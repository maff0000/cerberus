"""Source adapters for the public feeds the ratified mapping declares.

Each adapter implements :class:`crash_detector.collectors.adapter.SourceAdapter`: one
bounded ``fetch``, a declared closed ``response_schema``, and ``is_empty``. Parsing is done
by pure functions (``parse_*``) so it is tested offline against recorded fixtures.

NOTHING HERE COMPUTES AN INDICATOR. A payload carries what the source said — a date, a
number, a unit — and, for the one source whose declared calculation needs a price history
(the 200-day average), the raw closes. Ratios, spreads, percentiles and scores belong to
the engine's executor behind the raw/dial boundary.

WO-1.14 adds ONE adapter that asks a different question of the same kind of source:
:class:`AlfredVintageAdapter` fetches one observation AS FIRST PUBLISHED, by searching
ALFRED's vintages for the earliest one that served it. It still only fetches and reports;
the ``vintage`` label on the stored reading is the caller's to write.

WO-1.15 teaches :class:`FredAdapter` the other half of that question — ONE observation at a
NAMED date out of FRED's CURRENT body, for the pairs ``ingestion.vintage`` measured stable —
behind an opt-in ``observation_date`` that no live call site has an argument to set. Left at
its default ``None`` it is byte-for-byte the adapter the live loop has always had: same URL,
same parser, same failure handling.

Failure discipline: a transport failure raises :class:`AdapterFetchError` with a stable
class and NO message, URL or exception text (PBG-SEC-002). A response that arrives but is
unparseable is NOT converted into a fetch failure and is NOT defaulted: the raw token is
passed through and the declared schema rejects it, so it is recorded ``MALFORMED``.
"""

from __future__ import annotations

import calendar
import html
import json
import math
import re
import socket
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Mapping, Union

import redis

from crash_detector.collectors.adapter import AdapterFetchError, FetchedResponse

__all__ = [
    "RESPONSE_SCHEMA",
    "VINTAGE_RESPONSE_SCHEMA",
    "FredAdapter",
    "AlfredVintageAdapter",
    "CboeAdapter",
    "YahooChartAdapter",
    "MultplShillerAdapter",
    "LbmaGoldAdapter",
    "HermesCandleAdapter",
    "ManualEntryAdapter",
    "LBMA_USER_AGENT",
    "ALFRED_HOST",
    "ALFRED_BASE",
    "MAX_VINTAGE_PROBES",
    "HERMES_PEER",
    "HERMES_CANDLE_CONTRACT",
    "HERMES_CANDLE_CONTRACT_VERSION",
    "hermes_latest_key",
    "parse_hermes_candle",
    "parse_lbma_gold",
    "parse_fred_csv",
    "parse_fred_csv_for_date",
    "parse_alfred_csv",
    "parse_cboe_csv",
    "parse_cboe_csv_for_date",
    "parse_yahoo_chart",
    "parse_multpl_table",
    "as_of_for",
]

#: Hard ceiling on a response body. A hostile or broken source cannot make us buffer
#: without bound. Multpl's full monthly table is the largest legitimate body (~150 KB).
MAX_BODY_BYTES = 4_000_000

#: Ceiling on the optional raw history a payload may carry: ~260 closes for the 200-day average,
#: or multpl's full monthly CAPE table (~1,870 rows since 1871) for the engine's percentile.
MAX_HISTORY = 2700

RESPONSE_SCHEMA: Mapping[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["unit"],
    "properties": {
        "unit": {"type": "string", "minLength": 1, "maxLength": 64},
        "observation_date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
        "value": {"type": "number"},
        "history": {
            "type": "array",
            "maxItems": MAX_HISTORY,
            "items": {
                "type": "array",
                "minItems": 2,
                "maxItems": 2,
                "prefixItems": [
                    {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                    {"type": "number"},
                ],
            },
        },
    },
    # observation_date and value travel together or not at all: a date with no value, or a
    # value with no date, is a half-observation and is not accepted as one.
    "dependentRequired": {"observation_date": ["value"], "value": ["observation_date"]},
}

#: WO-1.14. The schema for a payload read out of ONE NAMED VINTAGE of a source, i.e. the
#: value as the source FIRST published it rather than as it stands today.
#:
#: It is :data:`RESPONSE_SCHEMA` with ONE addition and ONE removal, DERIVED from it rather
#: than retyped so the two cannot drift:
#:
#: * ``vintage_date`` is added, and the ``dependentRequired`` below makes it travel WITH the
#:   value, never optionally. A point-in-time value that does not state which vintage
#:   produced it is indistinguishable from today's value for the same period, which is the
#:   exact confusion this whole work order exists to prevent. The field is the vintage the
#:   SERVER's own column header named (see :func:`parse_alfred_csv`), not the one we asked
#:   for, so it is a record of what was answered.
#: * ``history`` is removed. A vintage read is ONE observation at ONE vintage; a history
#:   carried alongside it would be a mixture of vintages under a single label.
#:
#: The ``vintage`` LABEL (``ingestion.vintage.VINTAGE_ORIGINAL``) is deliberately NOT in
#: here. That is a column on the stored reading and it is the caller's to write; this
#: adapter reports what the source said and writes nothing, like every other adapter in
#: this file.
VINTAGE_RESPONSE_SCHEMA: Mapping[str, Any] = {
    **RESPONSE_SCHEMA,
    "properties": {
        **{name: shape for name, shape in RESPONSE_SCHEMA["properties"].items() if name != "history"},
        "vintage_date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
    },
    "dependentRequired": {
        "observation_date": ["value", "vintage_date"],
        "value": ["observation_date", "vintage_date"],
        "vintage_date": ["observation_date", "value"],
    },
}


# --- as-of ---------------------------------------------------------------------------- #


def as_of_for(observation_date: str, rule: str, now_utc: datetime) -> datetime:
    """The instant the SOURCE says its data refers to, per the catalog's declared rule.

    ``obs_date``    the date as published, 00:00 UTC (daily/weekly series, the SLOOS survey).
    ``month_end``   FRED dates a monthly figure at the FIRST of the month. Taken literally
                    that makes every monthly figure already ~45 days old on release against
                    a 45-day relevance window, i.e. permanently stale. The window was
                    written for period-END ageing, so the last day of the month is used,
                    capped at today: a figure never claims to refer to a date later than
                    the day we asked.

    ``quarter_end`` (WO-1.6) the same idea for a QUARTERLY series FRED dates at the quarter START
                    (Z.1 and GDP): the last day of that quarter, capped at today.

    All are conservative in the direction that matters: none can make old data look
    newer than the period it covers.
    """
    day = date.fromisoformat(observation_date)
    if rule == "month_end":
        day = day.replace(day=calendar.monthrange(day.year, day.month)[1])
    elif rule == "quarter_end":
        month = (day.month - 1) // 3 * 3 + 3
        day = day.replace(month=month, day=calendar.monthrange(day.year, month)[1])
    elif rule != "obs_date":
        raise ValueError(f"unknown as-of rule {rule!r}")
    today = now_utc.date()
    if day > today:
        day = today
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc)


# --- pure parsers --------------------------------------------------------------------- #


def _number_or_token(token: str) -> Union[float, str]:
    """A finite float, else the raw token so the schema (not this function) rejects it."""
    try:
        number = float(token)
    except ValueError:
        return token
    return number if math.isfinite(number) else token


def parse_fred_csv(text: str, column: str, unit: str, history: int = 0) -> dict:
    """Latest non-missing row of a ``fredgraph.csv`` body. FRED writes ``.`` for no data.

    ``history``: when positive, also carry the last ``history`` non-missing rows as raw
    ``[date, number]`` pairs, oldest first (WO-1.6: the engine derives a year-on-year move and a
    3-month rate from the raw levels; nothing is computed here). A row whose value is not a
    finite number makes the payload MALFORMED, never skipped: a derivation over a silently
    thinned series would be a different quantity.

    ``column`` is the expected value-column header: the series id, or ``<ID>_<TRANSFORM>``
    (e.g. ``M2SL_PC1``) when a server-side transformation was requested. A body whose header
    is not exactly what was asked for is MALFORMED, never read.
    """
    lines = text.strip().splitlines()
    if not lines or lines[0].split(",")[0] != "observation_date" or len(lines[0].split(",")) != 2:
        return {"malformed": "header"}  # no "unit": fails the closed schema -> MALFORMED
    if lines[0].split(",")[1] != column:
        return {"malformed": "series"}
    rows = []
    for line in reversed(lines[1:]):
        cells = line.split(",")
        if len(cells) != 2 or cells[1] in ("", "."):
            continue
        rows.append((cells[0], _number_or_token(cells[1])))
        if len(rows) >= max(history, 1):
            break
    if not rows:
        return {"unit": unit}  # a conforming body with no observation: EMPTY
    out: dict = {"unit": unit, "observation_date": rows[0][0], "value": rows[0][1]}
    if history:
        out["history"] = [[d, v] for d, v in reversed(rows)]
    return out


#: ALFRED's keyless graph CSV — the SAME public, credential-free door as ``fredgraph.csv``
#: (see :class:`FredAdapter`) with one extra query parameter, ``vintage_date``. No API key
#: is involved: ``api.stlouisfed.org`` is never contacted. Confirmed by direct probe on
#: 2026-10-13 over all 23 FRED pairs the catalog collects
#: (``tools/probe/alfred_vintage_probe.py``, ``evidence/wo114_alfred_probe.json``).
#:
#: DELIBERATELY NOT IN ``ingestion.catalog.EGRESS_HOSTS`` NOR IN
#: ``deploy/egress-destinations.yaml``, and WO-1.14's wiring round settled that rather than
#: deferring it again. Both of those are the LIVE collector's egress declaration — the first
#: is asserted equal to the hostnames of ``build_adapter(i)._url()`` over the INGREDIENTS, the
#: second is registered per compose service — so an entry for this host would assert that
#: ``cd-collectors`` reaches ALFRED, which it structurally does not and must not. The host is
#: declared instead in ``ingestion.backfill_adapters.BACKFILL_EGRESS_HOSTS``, where the full
#: reasoning and the compose/registry work that is OWED to the backfill driver round are
#: recorded. This adapter still cannot be reached through ``ingestion.catalog.build_adapter``
#: at all: its only constructor is
#: ``ingestion.backfill_adapters.build_backfill_adapter``.
ALFRED_HOST = "alfred.stlouisfed.org"
ALFRED_BASE = f"https://{ALFRED_HOST}/graph/alfredgraph.csv"

#: Hard ceiling on the GETs ONE :meth:`AlfredVintageAdapter.fetch` may issue. The bisection
#: needs ``2 + ceil(log2(days))`` — 17 for an observation in 1960 asked today — so this is a
#: guard against a broken invariant looping, not a budget the search is expected to approach.
#: Reaching it is a recorded failure and never a partial answer.
MAX_VINTAGE_PROBES = 24

#: A series id and a transformation are interpolated into a URL, so what may appear there is
#: stated POSITIVELY and anything else is refused at construction. Not a leak control (that is
#: PBG-SEC-002, below) — a refusal to build a request out of a string nobody vouched for.
_SERIES_ID = re.compile(r"^[A-Za-z0-9_]{1,64}$")
_TRANSFORMATION = re.compile(r"^[a-z0-9]{1,16}$")


def parse_alfred_csv(text: str, column: str, unit: str, observation_date: str,
                     vintage_date: str) -> dict:
    """ONE named observation read out of ONE named vintage of an ``alfredgraph.csv`` body.

    Three outcomes, and they are kept apart because the vintage search in
    :class:`AlfredVintageAdapter` turns on exactly this distinction:

    * **a value** — this vintage carried a figure for ``observation_date``;
    * **``{"unit": ...}``** — this vintage is served and carried NO figure for that date
      (the row is absent, or present with FRED's ``.`` for no data). EMPTY, not zero;
    * **``{"malformed": ...}``** — a body we do not understand. Never read as either of the
      other two, because "I could not read the answer" and "the answer was no" would send
      the bisection in opposite directions.

    THE HEADER IS CHECKED AGAINST THE VINTAGE WE ASKED FOR. ALFRED labels its value column
    ``<ID>[_<TRANSFORM>]_<YYYYMMDD>``, so the response STATES which vintage it is. A body
    that answered a different vintage is MALFORMED and is not read as the one requested —
    otherwise a server-side substitution would be recorded as a point-in-time fact.

    THE OBSERVATION IS MATCHED BY EXACT DATE, never taken as "the only row". ALFRED does not
    REFUSE an out-of-range ``cosd``/``coed`` window, it silently CLAMPS it (verified
    2026-10-13; recorded in ``tools/probe/alfred_vintage_probe.py``), so a body may carry a
    span nobody asked for. An exact-key match cannot be fooled by that; "the only row" could.
    """
    lines = text.strip().splitlines()
    header = lines[0].split(",") if lines else []
    if len(header) != 2 or header[0] != "observation_date":
        return {"malformed": "header"}  # no "unit": fails the closed schema -> MALFORMED
    prefix = column + "_"
    if not header[1].startswith(prefix):
        return {"malformed": "series"}
    if header[1][len(prefix):] != vintage_date.replace("-", ""):
        return {"malformed": "vintage"}
    for line in lines[1:]:
        cells = line.split(",")
        if len(cells) != 2 or cells[0] != observation_date:
            continue
        if cells[1] in ("", "."):
            break  # served, and this vintage had nothing to say about this date
        return {"unit": unit, "observation_date": observation_date,
                "value": _number_or_token(cells[1]), "vintage_date": vintage_date}
    return {"unit": unit}


def parse_fred_csv_for_date(text: str, column: str, unit: str, observation_date: str) -> dict:
    """ONE named observation read out of a ``fredgraph.csv`` body, matched by EXACT DATE.

    WO-1.15, and it exists because :func:`parse_fred_csv`'s discipline — the LATEST
    non-missing row — is the right answer to a different question. "What is this series'
    current value?" is answered by the last row; "what was the value for 2005-06-15?" is
    not, and cannot be, by ANY row read by position.

    THE WINDOWED REQUEST IS NOT A GUARANTEE ABOUT THE BODY, AND THIS IS MEASURED, NOT
    ASSUMED. ``cosd``/``coed`` narrow the body when the window overlaps the series' real
    span, but a window lying ENTIRELY BEFORE the series' first observation is neither
    clamped nor refused nor answered empty: the server IGNORES it and returns the WHOLE
    unfiltered series, oldest row first and TODAY's row last (probed 2026-10-15 against
    ``fred.stlouisfed.org``: ``tools/probe/fred_graph_window_probe.py``,
    ``evidence/wo115_fred_window_probe.json``, case ``q2_window_before_series_start`` — DFF
    asked for 1944-07-01 answered with all 26,403 rows). "The last row" against that body
    would answer a 1944 backfill with this morning's rate, under a 1944 key. "The only row"
    would be no safer: it is only ever the only row when the server chose to honour the
    window, which is precisely the case this function does not get to assume it is in.

    So the match is on the KEY and never on the position, the same discipline
    :func:`parse_alfred_csv` already follows against ALFRED's clamping for the same reason.
    A body nobody asked for cannot fool an exact-key match: it either carries a row dated
    ``observation_date`` or it does not.

    Three outcomes, kept apart:

    * **a value** — a row dated exactly ``observation_date`` carrying a figure;
    * **``{"unit": ...}``** — no such row, or the row is present with FRED's ``.`` (or an
      empty cell) for no data. EMPTY, not zero, and not someone else's number;
    * **``{"malformed": ...}``** — a header that is not ``observation_date,<column>``. The
      check is :func:`parse_fred_csv`'s, character for character, because it is the same
      endpoint answering the same series; plain FRED's header carries no vintage to verify,
      which is the one check :func:`parse_alfred_csv` has and this does not.

    NO ``history``. A windowed request asks for one day, so there is no history in the body
    to carry, and a payload that mixed one day's window with a history read out of some
    other body would be two different questions under one key. A backfilled reading for an
    ingredient whose LIVE row carries ``history`` (``fred.DFII10.history``) therefore
    carries none: the history exists for a derivation the live loop runs, and recovering it
    per past date is not what this answers.
    """
    lines = text.strip().splitlines()
    if not lines or lines[0].split(",")[0] != "observation_date" or len(lines[0].split(",")) != 2:
        return {"malformed": "header"}  # no "unit": fails the closed schema -> MALFORMED
    if lines[0].split(",")[1] != column:
        return {"malformed": "series"}
    for line in lines[1:]:
        cells = line.split(",")
        if len(cells) != 2 or cells[0] != observation_date:
            continue
        if cells[1] in ("", "."):
            break  # the series has this date and published no figure for it
        return {"unit": unit, "observation_date": observation_date,
                "value": _number_or_token(cells[1])}
    return {"unit": unit}


#: What one probed vintage said about the observation. Three states, named rather than
#: inferred from the shape at each of the four places the search branches on them.
_SERVED, _ABSENT, _UNREADABLE = "SERVED", "ABSENT", "UNREADABLE"


def _vintage_state(payload: Mapping[str, Any]) -> str:
    """Which of the three :func:`parse_alfred_csv` outcomes this payload is.

    A value that is not a finite number is ``_UNREADABLE``, NOT ``_SERVED``. The token is
    still carried out of the search untouched so the closed schema is the thing that rejects
    it (the convention :func:`parse_fred_csv` follows), but the search stops on it: a
    bisection cannot step over an answer it could not read without guessing which way to go.
    """
    if "malformed" in payload:
        return _UNREADABLE
    if "value" not in payload:
        return _ABSENT
    return _SERVED if type(payload["value"]) is float else _UNREADABLE


def parse_cboe_csv(text: str, column: str, unit: str) -> dict:
    """Latest row of a CBOE ``*_History.csv`` (``DATE`` is MM/DD/YYYY)."""
    lines = text.strip().splitlines()
    header = lines[0].split(",") if lines else []
    if not header or header[0] != "DATE" or column not in header:
        return {"malformed": "header"}
    index = header.index(column)
    for line in reversed(lines[1:]):
        cells = line.split(",")
        if len(cells) != len(header):
            continue
        try:
            observed = datetime.strptime(cells[0], "%m/%d/%Y").date().isoformat()
        except ValueError:
            return {"unit": unit, "observation_date": cells[0], "value": _number_or_token(cells[index])}
        return {"unit": unit, "observation_date": observed, "value": _number_or_token(cells[index])}
    return {"unit": unit}



def parse_cboe_csv_for_date(text: str, column: str, unit: str, observation_date: str) -> dict:
    """ONE named observation read out of a CBOE ``*_History.csv`` body, matched by EXACT DATE.

    WO-1.16, and the reason it sits beside :func:`parse_cboe_csv` rather than replacing it is
    the same reason :func:`parse_fred_csv_for_date` sits beside :func:`parse_fred_csv`: the
    last row is the right answer to "what is this index at now?" and cannot be the answer to
    "what was it on 2015-06-15?".

    HERE THERE IS NO WINDOW TO ASK FOR, WHICH IS MEASURED, NOT ASSUMED. ``cdn-api.cboe.com``
    honours NO date-windowing parameter at all: eight spellings (``dt``, ``date``,
    ``startDate``/``endDate``, ``start``/``end``, ``from``/``to``, ``start_date``/``end_date``,
    FRED's own ``cosd``/``coed``, and a nonsense control) each came back ``200`` with a body
    BYTE-IDENTICAL to the bare URL's and the same row count — probed 2026-10-15,
    ``tools/probe/cboe_history_probe.py``, ``evidence/wo116_cboe_probe.json``. So the
    body is always the WHOLE static history, oldest row first and the latest session last
    (VIX: 9,294 rows, 1990-01-02..2026-10-14). That makes the position read strictly worse
    than FRED's was: FRED at least sometimes filtered, while here EVERY per-date request is
    answered with a body whose last row is today. Reading it by position would answer a 2015
    backfill with this week's close under a 2015 key, every time.

    So the match is on the KEY and never on the position. The one thing that differs from
    :func:`parse_fred_csv_for_date` is that CBOE's ``DATE`` is ``MM/DD/YYYY``, so
    ``observation_date`` (ISO) is compared against the CONVERTED date, never against the raw
    cell — the conversion :func:`parse_cboe_csv` already does. A row whose date cell will not
    parse is SKIPPED, not returned: a date we cannot read is a date we cannot prove is the one
    that was asked for. (:func:`parse_cboe_csv` carries such a cell through verbatim, which is
    defensible for "the latest row" and is not available to an exact match.)

    Three outcomes, kept apart:

    * **a value** — a row whose converted date is exactly ``observation_date``, carrying a
      figure. The raw token is passed through by :func:`_number_or_token`, never defaulted;
    * **``{"unit": ...}``** — no such row. CBOE publishes no missing-data marker: every row of
      every probed body carries a figure in every column and non-sessions are simply ABSENT
      (``rows_for_month_verbatim`` for 2015-06 has no 06/06 or 06/07 weekend rows). A weekend,
      a holiday or a date before the index existed is therefore this case, not the next one.
      The empty-cell guard below is kept anyway, so a body that one day does carry a blank is
      EMPTY rather than a reading with no value;
    * **``{"malformed": ...}``** — a header that does not start with ``DATE`` (``header``), or
      one that lacks ``column`` (``column``). Split out, where :func:`parse_cboe_csv` folds
      both into ``header``, because an unreadable body and a body that is simply not carrying
      the asked-for series are different failures to read in a backfill log.
    """
    lines = text.strip().splitlines()
    header = lines[0].split(",") if lines else []
    if not header or header[0] != "DATE":
        return {"malformed": "header"}  # no "unit": fails the closed schema -> MALFORMED
    if column not in header:
        return {"malformed": "column"}
    index = header.index(column)
    for line in lines[1:]:
        cells = line.split(",")
        if len(cells) != len(header):
            continue
        try:
            observed = datetime.strptime(cells[0], "%m/%d/%Y").date().isoformat()
        except ValueError:
            continue  # unreadable date: cannot be proven to be the one asked for
        if observed != observation_date:
            continue
        if cells[index] == "":
            break  # the body carries this session and no figure for it
        return {"unit": unit, "observation_date": observation_date,
                "value": _number_or_token(cells[index])}
    return {"unit": unit}

def parse_yahoo_chart(text: str, unit: str, history: int = 0, today: Union[date, None] = None,
                      field: str = "close") -> dict:
    """Latest daily close of a Yahoo v8 chart body; optionally the last ``history`` closes.

    ``field`` is ``close`` (the printed price, the default) or ``adjclose`` (split- and DIVIDEND-adjusted, i.e. a
    total-return series). A body that lacks the requested field is MALFORMED, never silently read as ``close``.

    ``today``: when given, any bar dated on or after it is DROPPED. During a session the last
    bar is the live price, not a close, and the store keeps the first value admitted for a
    period (Auditor finding 2, WO-1.2b), so a partial bar would be locked in as the close.
    """
    try:
        result = json.loads(text)["chart"]["result"][0]
        stamps = result["timestamp"]
        closes = (result["indicators"]["quote"][0]["close"] if field == "close"
                  else result["indicators"][field][0][field])
    except (ValueError, KeyError, IndexError, TypeError):
        return {"malformed": "shape"}
    if len(stamps) != len(closes):
        return {"malformed": "shape"}
    rows = []
    for stamp, close in zip(stamps, closes):
        if close is None:  # Yahoo nulls a session it has no print for; skip, never fill.
            continue
        bar_date = datetime.fromtimestamp(stamp, tz=timezone.utc).date()
        if today is not None and bar_date >= today:
            continue  # not yet a close
        rows.append((bar_date.isoformat(), close))
    if not rows:
        return {"unit": unit}
    out: dict = {"unit": unit, "observation_date": rows[-1][0], "value": _number_or_token(str(rows[-1][1]))}
    if history:
        out["history"] = [[d, c] for d, c in rows[-history:]]
    return out


_MULTPL_ROW = re.compile(
    r"<td>([A-Z][a-z]{2} \d{1,2}, \d{4})</td>\s*<td>\s*(?:&#x2002;|&\w+;)?\s*([^<\s]+)\s*</td>"
)


def parse_multpl_table(text: str, unit: str, with_history: bool = False) -> dict:
    """First (= most recent) row of multpl's ``/table/by-month`` page; optionally the whole table.

    ``with_history`` carries every row of the page, oldest first, as raw ``[date, value]`` pairs
    so the ENGINE can percentile the latest figure within it. Nothing is computed here. A row
    whose date or value cannot be read makes the whole payload MALFORMED rather than being
    skipped: a percentile over a silently thinned table would be a different quantity.
    """
    matches = list(_MULTPL_ROW.finditer(text))
    if not matches:
        return {"malformed": "shape"}  # no row found is a page we do not understand, not "empty"
    rows = []
    for match in matches if with_history else matches[:1]:
        try:
            observed = datetime.strptime(html.unescape(match.group(1)), "%b %d, %Y").date().isoformat()
        except ValueError:
            return {"malformed": "date"}
        rows.append((observed, _number_or_token(match.group(2))))
    out: dict = {"unit": unit, "observation_date": rows[0][0], "value": rows[0][1]}
    if with_history:
        out["history"] = [[d, v] for d, v in reversed(rows)]
    return out


#: The browser-prefixed agent legacy ARGUS ``gold_tells.py`` used. It no longer gets past LBMA's
#: Cloudflare edge from the build host (HTTP 403), so it is not a working credential.
LBMA_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) argus-crash-engine/monetary-tells"
LBMA_PM_URL = "https://prices.lbma.org.uk/json/gold_pm.json"
LBMA_AM_URL = "https://prices.lbma.org.uk/json/gold_am.json"


def _lbma_usd_by_date(text: str) -> Union[dict, None]:
    """date -> USD fix of an LBMA ``gold_*.json`` body, or None if the body is not that shape.

    The body is a list of ``{"d": "YYYY-MM-DD", "v": [USD, GBP, EUR], ...}``. A row with no USD
    figure (a day with no fix, or a cancelled one) is skipped: that is the source saying there is
    no fix, not a number we are discarding. A figure that is present but not a finite number is
    passed through as a token so the closed schema rejects it (MALFORMED).
    """
    try:
        rows = json.loads(text)
    except ValueError:
        return None
    if type(rows) is not list:
        return None
    out: dict = {}
    for row in rows:
        if type(row) is not dict or type(row.get("d")) is not str:
            return None
        values = row.get("v")
        if values is None or row.get("is_cancelled") is True:
            continue
        if type(values) is not list:
            return None
        if not values or values[0] is None:
            continue
        out[row["d"]] = values[0] if type(values[0]) in (int, float) and math.isfinite(values[0]) else str(values[0])
    return out


def parse_lbma_gold(pm_text: str, am_text: str, unit: str, history: int = 0) -> dict:
    """The newest LBMA gold fix in USD per troy ounce: the PM fix of a date, else that date's AM fix.

    Same selection as the legacy ARGUS gold tell: take the union of dates, prefer PM for a date
    that has one, fall back to AM only for a date with no PM (today, before the PM fix is made).

    ``history`` (WO-1.7): when positive, also carry the last ``history`` dates' fixes as raw
    ``[date, usd]`` pairs, oldest first, chosen by the same PM-else-AM rule. Nothing is computed.
    """
    pm, am = _lbma_usd_by_date(pm_text), _lbma_usd_by_date(am_text)
    if pm is None or am is None:
        return {"malformed": "shape"}
    dates = sorted(set(pm) | set(am))
    if not dates:
        return {"unit": unit}  # a conforming body with no fix: EMPTY
    day = dates[-1]
    out: dict = {"unit": unit, "observation_date": day, "value": pm[day] if day in pm else am[day]}
    if history:
        out["history"] = [[d, pm[d] if d in pm else am[d]] for d in dates[-history:]]
    return out


#: WO-1.12. HERMES is a SEPARATE SYSTEM in another seat's domain (Helm's), and this project is one
#: READ-ONLY CONSUMER of a contract it publishes — the same relationship it has to FRED, Cboe, Yahoo
#: and multpl.com, differing only in that the transport is a Redis GET on the LAN rather than HTTPS.
#: Nothing in this module writes, expires, renames or otherwise touches a ``hermes:*`` key, and
#: nothing here may be pointed at HERMES' own container, compose project or files.
#:
#: HERMES' CURRENT CLASSIFICATION, recorded because a reader of a gold price is owed it rather than
#: having to go and find it: the publishing service is labelled ``NON_PROMOTED_ENGINEERING_CANDIDATE``
#: with ``ENVIRONMENT=DEV`` and ``RUN_ENV=STAGING``, i.e. it is NOT a promoted production service.
#: Its price data is nevertheless REAL: it runs with ``OANDA_ENVIRONMENT=live``, so these are live
#: OANDA quotes and not a demo/practice feed. Matt has accepted that maturity caveat explicitly
#: ("good enough, will be maintained"); it is disclosed here, in the mapping row and in STATUS.md
#: rather than smoothed over, and it is not re-argued in code.
HERMES_PEER = ("192.168.11.10", 6379, 0)
#: The published contract this adapter reads, by name and version. A body claiming anything else is
#: NOT read as if it were this one: it is MALFORMED. The contract may change under us, and the only
#: safe response to a contract we were not written against is to refuse it loudly.
HERMES_CANDLE_CONTRACT = "hermes.candles.latest"
HERMES_CANDLE_CONTRACT_VERSION = "v1"


def hermes_latest_key(instrument: str, timeframe: str) -> str:
    """The key HERMES publishes its newest closed candle for one instrument/timeframe under."""
    return f"hermes:candles:{instrument}:{timeframe}:latest:{HERMES_CANDLE_CONTRACT_VERSION}"


def parse_hermes_candle(text: Union[str, None], instrument: str, timeframe: str, unit: str) -> dict:
    """The CLOSE of HERMES' newest closed candle for ``instrument``/``timeframe``.

    ``text`` is the raw key body, or ``None`` for a key that is not there. An absent key is the
    publisher saying it has nothing (its own TTL is 4h, so a stopped HERMES empties it rather than
    leaving a stale body behind): that is EMPTY, which reads MISSING downstream and never calm.

    REFUSED, NOT INTERPRETED. The envelope must name the contract and version this function was
    written against, and the candle must be for the instrument and timeframe that were ASKED FOR —
    the key says one thing and the body must agree, or we are reading a different series under a
    familiar name. Any of those is MALFORMED.

    EMPTY, NOT A NUMBER. ``status`` other than ``OK`` is the publisher declining to vouch for the
    candle, and ``is_closed`` false is a bar still forming. Either yields no value: the store keeps
    the FIRST payload admitted for a source period (Auditor finding 2, WO-1.2b), so admitting a
    partial bar would lock it in as the close for the whole period.

    THE DATE IS THE CANDLE'S OWN UTC DAY, and that is a deliberate, disclosed coarsening. The
    payload schema carries a DATE, the row's cadence is daily and its staleness window is 7 days, so
    the figure is "the close of the FIRST H4 candle HERMES publishes on each UTC day" — a defined,
    reproducible once-a-day reference in the same spirit as the LBMA daily fix it replaces, not an
    intraday tick. Later candles the same UTC day are not admitted, because the period is already
    filled; nothing is averaged, carried forward or overwritten.

    NOTHING IS COMPUTED. ``open``, ``high``, ``low``, the body/wick geometry and the derivation
    metadata HERMES also publishes are READ PAST, not combined: a close is what the mapping row's
    ``market:XAUUSD`` spot asks for (collector-never-computes, BLUEPRINT §5).
    """
    if text is None:
        return {"unit": unit}  # the key is absent or expired: EMPTY, never a defaulted price
    try:
        envelope = json.loads(text)
    except ValueError:
        return {"malformed": "shape"}  # no "unit": fails the closed schema -> MALFORMED
    if type(envelope) is not dict:
        return {"malformed": "shape"}
    if (envelope.get("contract") != HERMES_CANDLE_CONTRACT
            or envelope.get("contract_version") != HERMES_CANDLE_CONTRACT_VERSION):
        return {"malformed": "contract"}
    candle = envelope.get("data")
    if type(candle) is not dict:
        return {"malformed": "shape"}
    if candle.get("instrument") != instrument or candle.get("timeframe") != timeframe:
        return {"malformed": "series"}
    if envelope.get("status") != "OK" or candle.get("is_closed") is not True:
        return {"unit": unit}  # the publisher does not vouch for it, or it is still forming: EMPTY
    stamp = candle.get("timestamp_utc")
    if type(stamp) is not str:
        return {"malformed": "date"}
    try:
        day = date.fromisoformat(stamp[:10]).isoformat()
    except ValueError:
        return {"malformed": "date"}
    close = candle.get("close")
    numeric = type(close) in (int, float) and not isinstance(close, bool) and math.isfinite(close)
    return {"unit": unit, "observation_date": day, "value": close if numeric else str(close)}


# --- transport ------------------------------------------------------------------------ #


def http_get(url: str, timeout_seconds: float, headers: Union[Mapping[str, str], None] = None) -> str:
    """One bounded GET. Raises :class:`AdapterFetchError` with a stable class only.

    Redirects are NOT followed: the egress registry names exactly the hosts we may reach,
    and an automatic redirect would reach one nobody declared. (The CBOE legacy host answers
    307; the registered host is the redirect target.) The default urllib User-Agent is kept
    deliberately — FRED's edge resets connections from unfamiliar agent strings.
    """

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args: Any, **kwargs: Any):  # noqa: D401
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(url, headers=dict(headers or {}))
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            body = response.read(MAX_BODY_BYTES + 1)
    except urllib.error.HTTPError as failure:
        raise AdapterFetchError("HTTP_ERROR", failure.code) from None
    except (socket.timeout, TimeoutError):
        raise AdapterFetchError("TIMEOUT") from None
    except urllib.error.URLError as failure:
        reason = failure.reason
        if isinstance(reason, (socket.timeout, TimeoutError)):
            raise AdapterFetchError("TIMEOUT") from None
        raise AdapterFetchError("CONNECTION_FAILED") from None
    except OSError:
        raise AdapterFetchError("CONNECTION_FAILED") from None
    if len(body) > MAX_BODY_BYTES:
        raise AdapterFetchError("BODY_TOO_LARGE")
    return body.decode("utf-8", errors="replace")


def redis_read(key: str, timeout_seconds: float) -> Union[str, None]:
    """One bounded READ of ONE key on the HERMES publication peer. Returns ``None`` for no key.

    READ-ONLY BY CONSTRUCTION, not by intention: the only command this function can issue is
    ``GET`` of the key it was handed. There is no write path here to misuse, and the connection is
    closed again immediately rather than pooled.

    Failure discipline is the same as :func:`http_get`: a stable class and NO message, URL or
    exception text (PBG-SEC-002). The body is bounded by the same ceiling, so a key somebody grew
    without bound cannot make us buffer without bound.
    """
    host, port, database = HERMES_PEER
    client = redis.Redis(
        host=host, port=port, db=database,
        socket_connect_timeout=timeout_seconds, socket_timeout=timeout_seconds,
        single_connection_client=True, decode_responses=False,
    )
    try:
        body = client.get(key)
    except redis.exceptions.TimeoutError:
        raise AdapterFetchError("TIMEOUT") from None
    except (redis.exceptions.RedisError, OSError):
        raise AdapterFetchError("CONNECTION_FAILED") from None
    finally:
        client.close()
    if body is None:
        return None
    if len(body) > MAX_BODY_BYTES:
        raise AdapterFetchError("BODY_TOO_LARGE")
    return body.decode("utf-8", errors="replace")


# --- adapters ------------------------------------------------------------------------- #


class _BaseAdapter:
    """Shared shell. Subclasses supply ``_url``, ``_parse`` and their identity."""

    __slots__ = ("_source_id", "_as_of_rule", "_unit", "_clock", "_getter")

    adapter_id = "overridden"
    response_schema = RESPONSE_SCHEMA

    def __init__(
        self,
        source_id: str,
        as_of_rule: str,
        unit: str,
        clock: Callable[[], datetime],
        getter: Callable[..., str] = http_get,
    ) -> None:
        self._source_id = source_id
        self._as_of_rule = as_of_rule
        self._unit = unit
        self._clock = clock
        self._getter = getter

    @property
    def source_id(self) -> str:
        return self._source_id

    def _headers(self) -> Union[Mapping[str, str], None]:
        return None

    def _url(self) -> str:  # pragma: no cover - abstract
        raise NotImplementedError

    def _parse(self, body: str) -> dict:  # pragma: no cover - abstract
        raise NotImplementedError

    def _acquire(self, timeout_seconds: float) -> dict:
        """One bounded read of the source, parsed. A source needing more than one GET overrides this."""
        return self._parse(self._getter(self._url(), timeout_seconds, self._headers()))

    def fetch(self, *, timeout_seconds: float) -> FetchedResponse:
        payload = self._acquire(timeout_seconds)
        now = self._clock()
        date_text = payload.get("observation_date")
        if isinstance(date_text, str):
            try:
                as_of = as_of_for(date_text, self._as_of_rule, now)
            except ValueError:
                # An unreadable source date: refuse to invent one; the closed schema
                # rejects the payload, so it is recorded MALFORMED.
                payload = {"malformed": "date"}
                as_of = now
        else:
            as_of = now  # EMPTY / MALFORMED carry no source period; the runner ignores it.
        return FetchedResponse(payload=payload, source_as_of_utc=as_of)

    def is_empty(self, payload: object) -> bool:
        return isinstance(payload, dict) and "value" not in payload


class FredAdapter(_BaseAdapter):
    """``fred.stlouisfed.org/graph/fredgraph.csv`` — public, keyless, no credential exists.

    ``transformation`` is FRED's OWN server-side unit transform (``pc1`` = percent change
    from a year ago), so a YoY indicator is still a number the source computed and we
    merely recorded.

    TWO QUESTIONS, ONE ENDPOINT, AND THE SECOND ONE IS OPT-IN (WO-1.15). With
    ``observation_date`` left at ``None`` — which is every live call, since
    ``ingestion.catalog.build_adapter`` has no argument that could set it — this asks
    "what is this series' latest value?" and behaves EXACTLY as it always has: the same
    URL, :func:`parse_fred_csv`, and a 404 is a fetch FAILURE. With ``observation_date``
    set, which only ``ingestion.backfill_adapters.build_backfill_adapter`` does, it asks
    "what does this series say for the observation dated D?", and all three of those change
    together:

    * the request carries ``cosd=D&coed=D``, the same windowing
      :meth:`AlfredVintageAdapter._url_for` uses against ALFRED;
    * the body is read by :func:`parse_fred_csv_for_date`, which matches D EXACTLY and never
      by position — see that function on WHY the window is a courtesy and not a promise;
    * an ``HTTP_ERROR``/404 becomes EMPTY rather than a failure (:meth:`_acquire`).

    WHY THE 404 IS AN ANSWER HERE AND A FAILURE THERE. A window landing on a date inside the
    series' span that the series does not have — a Saturday for a business-daily series — is
    answered ``404`` with an HTML error page, not ``200`` with a header and no rows (probed
    2026-10-15: ``evidence/wo115_fred_window_probe.json``, case ``extra_window_on_gap_date``,
    T5YIE on 2015-06-20). That 404 is FRED saying "no observation on this date", which is
    the EMPTY this adapter must report, and it is the same carve-out
    :meth:`AlfredVintageAdapter.probe` makes with ``absent_on_404`` for "no such vintage".
    Unwindowed, nothing is being asked about a particular date and a 404 means the SERIES
    could not be fetched — a real failure, and the live loop's handling of it is untouched
    because the translation is gated on ``observation_date`` being set.

    ``observation_date`` is KEYWORD-ONLY. ``history`` is the third positional parameter at
    every existing call site, and a date arriving where a row count belongs — or a count
    where a date belongs — would be a silent change of question. The date is also parsed at
    construction: a string we cannot read as a date is not one we may interpolate into a URL.
    """

    __slots__ = ("_series", "_transformation", "_history", "_observation_date")
    adapter_id = "cd.ingest.fred_csv.v1"

    def __init__(self, series: str, transformation: Union[str, None], history: int = 0, *,
                 observation_date: Union[str, None] = None, **kw: Any) -> None:
        super().__init__(**kw)
        if observation_date is not None:
            date.fromisoformat(observation_date)
        self._series = series
        self._transformation = transformation
        self._history = history
        self._observation_date = observation_date

    def _url(self) -> str:
        suffix = f"&transformation={self._transformation}" if self._transformation else ""
        window = ("" if self._observation_date is None else
                  f"&cosd={self._observation_date}&coed={self._observation_date}")
        return f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={self._series}{suffix}{window}"

    def _parse(self, body: str) -> dict:
        column = self._series + (f"_{self._transformation.upper()}" if self._transformation else "")
        if self._observation_date is None:
            return parse_fred_csv(body, column, self._unit, self._history)
        return parse_fred_csv_for_date(body, column, self._unit, self._observation_date)

    def _acquire(self, timeout_seconds: float) -> dict:
        """The shared one GET, plus the 404-as-EMPTY translation a DATED request needs.

        Unwindowed, this is the base method and nothing else: one call, one ``except``-free
        path, identical to the live loop's today.
        """
        if self._observation_date is None:
            return super()._acquire(timeout_seconds)
        try:
            return super()._acquire(timeout_seconds)
        except AdapterFetchError as failure:
            if failure.error_class == "HTTP_ERROR" and failure.http_status == 404:
                return {"unit": self._unit}  # FRED has no observation on this date: an ANSWER
            raise


class AlfredVintageAdapter(_BaseAdapter):
    """``alfred.stlouisfed.org/graph/alfredgraph.csv`` — ONE observation as it was FIRST published.

    WO-1.14. :class:`FredAdapter` asks "what is this series' latest value?" and gets today's
    revised history. This adapter asks a different question: "for the observation dated D,
    what number would a collector running back then actually have SEEN?" For a revised series
    those are different numbers, and storing the first as though it were the second is
    lookahead bias wearing a backfill's clothes.

    THE VINTAGE-SELECTION RULE, STATED ONCE AND IMPLEMENTED EXACTLY ONCE (:meth:`_acquire`):

        **The EARLIEST vintage date, within ``[observation_date, today]``, at which ALFRED
        serves a non-empty value for this observation date.**

    That is the first vintage that could have published the figure, so its value is the
    figure as first published — what was knowable then, which is the only thing a replay is
    entitled to use. Found by bisection on ``_SERVED`` vs ``_ABSENT``, the same instrument
    ``tools/probe/alfred_vintage_probe.py::vintage_depth`` used to find a SERIES' earliest
    vintage, anchored to one observation instead of to the series.

    WHY THE SEARCH FLOOR IS THE OBSERVATION DATE AND NOT THE PROBE'S 1990. A vintage dated
    before the observation date could not have known about the observation: the period had
    not happened. Making that the floor is both the tighter window (the bisection costs
    ``2 + ceil(log2(days))`` GETs instead of searching back to 1990) and the property the
    whole exercise is about — the returned vintage is NEVER one that could not have known.
    It is not left as an assumption: the day BEFORE the observation is probed, and if it
    already serves a value the premise is wrong for this series (a projection series, say),
    so the fetch is refused as MALFORMED rather than answered with a vintage that is not in
    fact the earliest.

    THE TWO ENDS ARE MEASURED, THE MIDDLE IS ASSUMED MONOTONE — a DECLARED limit. Bisection
    is only sound if "serves a value at D" never goes true-then-false as the vintage
    advances. Publishers overwhelmingly do not WITHDRAW a published observation, but if one
    ever did, this would return the earliest vintage of the LATER served run, not the true
    first publication. Detecting that needs a linear scan of every vintage, which this
    endpoint cannot be asked for at backfill scale. The limit is recorded here rather than
    left for a reader to discover.

    WHAT IT RETURNS, AND WHAT IT DOES NOT DO WITH IT. A payload conforming to
    :data:`VINTAGE_RESPONSE_SCHEMA`: the value, the observation date, and the vintage the
    SERVER named in its own column header. The caller is the one that decides this pair
    needed point-in-time treatment at all (``ingestion.vintage.requires_original_vintage``)
    and the one that stores the reading with ``vintage=ingestion.vintage.VINTAGE_ORIGINAL``.
    This adapter fetches what it is told to fetch and writes nothing, exactly like every
    other adapter in this file.

    BOUNDED, AND HOW. ``timeout_seconds`` is honoured as a TOTAL deadline across the whole
    bisection, not per request: each GET is given only the time left, and a budget that runs
    out mid-search is ``TIMEOUT``, never a partial answer. The number of GETs is capped by
    :data:`MAX_VINTAGE_PROBES`. Both ceilings are the reason this adapter does NOT belong in
    the live polling loop, whose per-attempt budget is a few seconds: it is for the backfill
    driver, which is a later round's work. Courtesy pacing between observations is that
    driver's call and is deliberately not done here — an adapter that slept would be
    deciding a policy nobody asked it to hold.

    Failure discipline is the shared one: a stable class and NO message, URL or exception
    text (PBG-SEC-002). ONE exception is carved out and it is an ANSWER rather than a
    failure: below the ceiling, an ``HTTP_ERROR``/404 is ALFRED saying "no such vintage of
    this series", which is precisely the ``_ABSENT`` the search is looking for. At the
    CEILING, where we asked for today's vintage and today's vintage must exist, a 404 is a
    real failure and is raised as one — swallowing it there would turn a mistyped series id
    into a tidy "this observation was never published".
    """

    __slots__ = ("_series", "_transformation", "_observation_date")
    adapter_id = "cd.ingest.alfred_vintage_csv.v1"
    response_schema = VINTAGE_RESPONSE_SCHEMA

    def __init__(self, series: str, transformation: Union[str, None], observation_date: str,
                 **kw: Any) -> None:
        super().__init__(**kw)
        if not isinstance(series, str) or not _SERIES_ID.match(series):
            raise ValueError("series id is not in the permitted shape")
        if transformation is not None and (
            not isinstance(transformation, str) or not _TRANSFORMATION.match(transformation)
        ):
            raise ValueError("transformation is not in the permitted shape")
        date.fromisoformat(observation_date)  # a date we cannot read is not one we may ask for
        self._series = series
        self._transformation = transformation
        self._observation_date = observation_date

    def _column(self) -> str:
        return self._series + (f"_{self._transformation.upper()}" if self._transformation else "")

    def _url_for(self, vintage: Union[str, None]) -> str:
        """The request for ONE vintage. ``None`` asks for the current one (see :meth:`_url`)."""
        parts = [f"id={self._series}"]
        if self._transformation:
            parts.append(f"transformation={self._transformation}")
        if vintage:
            parts.append(f"vintage_date={vintage}")
        # A COURTESY bound on the body, never a guarantee: ALFRED clamps an out-of-range
        # window instead of refusing it, so the parser matches the date exactly as well.
        parts += [f"cosd={self._observation_date}", f"coed={self._observation_date}"]
        return ALFRED_BASE + "?" + "&".join(parts)

    def _url(self) -> str:
        """The host-declaring URL (current vintage). The fetch asks :meth:`_url_for` instead.

        It exists so this adapter's egress host can be read off it the way every other
        adapter's is, by whatever registers it when it is wired up. ``fetch`` never uses it.
        """
        return self._url_for(None)

    def _acquire(self, timeout_seconds: float) -> dict:
        observed = date.fromisoformat(self._observation_date)
        today = self._clock().date()
        if observed > today:
            # Nothing can have published an observation that has not happened. Refused
            # rather than searched for in an empty window.
            return {"malformed": "observation_date"}

        deadline = time.monotonic() + timeout_seconds
        spent = [0]

        def probe(vintage: date, *, absent_on_404: bool = True) -> dict:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AdapterFetchError("TIMEOUT")
            spent[0] += 1
            if spent[0] > MAX_VINTAGE_PROBES:
                raise AdapterFetchError("VINTAGE_SEARCH_EXHAUSTED")
            asked = vintage.isoformat()
            try:
                body = self._getter(self._url_for(asked), remaining, self._headers())
            except AdapterFetchError as failure:
                if absent_on_404 and failure.error_class == "HTTP_ERROR" and failure.http_status == 404:
                    return {"unit": self._unit}  # ALFRED serves no such vintage: an ANSWER
                raise
            return parse_alfred_csv(body, self._column(), self._unit, self._observation_date, asked)

        # The ceiling. If TODAY's vintage has no value for this date, no vintage does: the
        # observation was never published and there is nothing here to backfill. EMPTY.
        high, found = today, probe(today, absent_on_404=False)
        state = _vintage_state(found)
        if state == _UNREADABLE:
            return found
        if state == _ABSENT:
            return {"unit": self._unit}

        # The floor, VERIFIED rather than assumed: the day before the observation existed.
        low = observed - timedelta(days=1)
        beneath = probe(low)
        state = _vintage_state(beneath)
        if state == _UNREADABLE:
            return beneath
        if state == _SERVED:
            # A vintage published before the observation date already carries the figure, so
            # the earliest-serving vintage is OUTSIDE the window this rule searches and the
            # answer would not be the earliest. Refused, never approximated.
            return {"malformed": "vintage_floor"}

        # Invariant: ``low`` is ABSENT, ``high`` is SERVED. Narrow to adjacent days.
        while (high - low).days > 1:
            middle = low + timedelta(days=(high - low).days // 2)
            payload = probe(middle)
            state = _vintage_state(payload)
            if state == _UNREADABLE:
                return payload
            if state == _SERVED:
                high, found = middle, payload
            else:
                low = middle
        return found


class CboeAdapter(_BaseAdapter):
    __slots__ = ("_index", "_column")
    adapter_id = "cd.ingest.cboe_history_csv.v1"

    def __init__(self, index: str, column: str, **kw: Any) -> None:
        super().__init__(**kw)
        self._index = index
        self._column = column

    def _url(self) -> str:
        return f"https://cdn-api.cboe.com/api/global/us_indices/daily_prices/{self._index}_History.csv"

    def _parse(self, body: str) -> dict:
        return parse_cboe_csv(body, self._column, self._unit)


class YahooChartAdapter(_BaseAdapter):
    """Yahoo Finance public chart endpoint (the provider OpenBB's equity path wraps).

    UNOFFICIAL: no SLA, no licence, rate-limited (HTTP 429 under bursts). Its failures are
    recorded like any other; none is defaulted.
    """

    __slots__ = ("_symbol", "_history", "_field")
    adapter_id = "cd.ingest.yahoo_chart.v1"

    def __init__(self, symbol: str, history: int = 0, field: str = "close", **kw: Any) -> None:
        super().__init__(**kw)
        self._symbol = symbol
        self._history = history
        self._field = field

    def _headers(self) -> Mapping[str, str]:
        # Yahoo answers 429 to urllib's default agent and 200 to an identified browser-style
        # one; FRED does the opposite (see http_get). Per-adapter, declared, not global.
        return {"User-Agent": "Mozilla/5.0 (compatible; cerberus-ingest/1.0)"}

    def _url(self) -> str:
        quoted = self._symbol.replace("^", "%5E").replace("=", "%3D")
        rng = "2y" if self._history else "10d"
        return f"https://query1.finance.yahoo.com/v8/finance/chart/{quoted}?range={rng}&interval=1d"

    def _parse(self, body: str) -> dict:
        return parse_yahoo_chart(body, self._unit, self._history, today=self._clock().date(), field=self._field)


class MultplShillerAdapter(_BaseAdapter):
    """multpl.com's Shiller P/E monthly table (declared source: ``multpl/Shiller``)."""

    __slots__ = ("_history",)
    adapter_id = "cd.ingest.multpl_shiller_pe.v1"

    def __init__(self, history: int = 0, **kw: Any) -> None:
        super().__init__(**kw)
        self._history = bool(history)

    def _url(self) -> str:
        return "https://www.multpl.com/shiller-pe/table/by-month"

    def _parse(self, body: str) -> dict:
        return parse_multpl_table(body, self._unit, self._history)


class LbmaGoldAdapter(_BaseAdapter):
    """LBMA daily gold fix (USD/oz), PM with AM fallback — the genuine spot-gold reference.

    Two bounded GETs (``gold_pm.json`` and ``gold_am.json``); BOTH must succeed, so a half-fetched
    answer is a recorded failure and never a silent choice. The legacy browser-prefixed User-Agent is
    sent. If the edge refuses us (HTTP 403 from its bot protection; observed from the build host
    with this and a plain curl agent), that is
    recorded as ``HTTP_ERROR``/403 like any failure: this adapter does not try to get around it.
    """

    __slots__ = ("_history",)
    adapter_id = "cd.ingest.lbma_gold_fix.v1"

    def __init__(self, history: int = 0, **kw: Any) -> None:
        super().__init__(**kw)
        self._history = history

    def _headers(self) -> Mapping[str, str]:
        return {"User-Agent": LBMA_USER_AGENT}

    def _url(self) -> str:
        return LBMA_PM_URL

    def _acquire(self, timeout_seconds: float) -> dict:
        pm_body = self._getter(LBMA_PM_URL, timeout_seconds, self._headers())
        am_body = self._getter(LBMA_AM_URL, timeout_seconds, self._headers())
        return parse_lbma_gold(pm_body, am_body, self._unit, self._history)


class HermesCandleAdapter(_BaseAdapter):
    """HERMES' published latest-closed-candle contract, read over its Redis publication (WO-1.12).

    ONE bounded ``GET`` of ONE key, and the key is derived from the instrument and timeframe this
    adapter was constructed with — it is not taken from anything a response says, so a body cannot
    redirect the next read. See :data:`HERMES_PEER` for what HERMES is, what its build labels say
    and why its data is live despite them, and :func:`parse_hermes_candle` for what is refused.

    It has no ``_url``: the transport is not HTTP, so this adapter is NOT part of the HTTP egress
    allowlist and does not appear in ``ingestion.catalog.EGRESS_HOSTS``. The peer it reaches is
    declared in ``ingestion.catalog.NON_HTTP_PEERS`` instead, and why it cannot be registered in
    ``deploy/egress-destinations.yaml`` is recorded there.
    """

    __slots__ = ("_instrument", "_timeframe")
    adapter_id = "cd.ingest.hermes_candle_latest.v1"

    def __init__(self, instrument: str, timeframe: str, **kw: Any) -> None:
        # The default getter on the shared shell is http_get, which is the WRONG transport here;
        # it is replaced rather than inherited, and a test still injects its own in its place.
        kw.setdefault("getter", redis_read)
        super().__init__(**kw)
        self._instrument = instrument
        self._timeframe = timeframe

    def _acquire(self, timeout_seconds: float) -> dict:
        body = self._getter(hermes_latest_key(self._instrument, self._timeframe), timeout_seconds)
        return parse_hermes_candle(body, self._instrument, self._timeframe, self._unit)


class ManualEntryAdapter(_BaseAdapter):
    """A value a human typed in (WO-1.7), carried through the SAME boundary as a fetched one.

    There is no feed: ``fetch`` returns the one payload it was constructed with and touches no
    network. It exists so a hand-entered figure is validated by the closed ``RESPONSE_SCHEMA``,
    recorded as an observation attempt, admitted to the append-only reading ledger and aged by the
    same relevance window as any fetched reading. Nothing about it is special downstream.
    """

    __slots__ = ("_entry",)
    adapter_id = "cd.ingest.manual_entry.v1"

    def __init__(self, observation_date: str, value: float, **kw: Any) -> None:
        super().__init__(**kw)
        self._entry = {"unit": self._unit, "observation_date": observation_date, "value": value}

    def _acquire(self, timeout_seconds: float) -> dict:
        return dict(self._entry)
