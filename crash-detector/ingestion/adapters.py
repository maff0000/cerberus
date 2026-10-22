"""Source adapters for the public feeds the ratified mapping declares.

Each adapter implements :class:`crash_detector.collectors.adapter.SourceAdapter`: one
bounded ``fetch``, a declared closed ``response_schema``, and ``is_empty``. Parsing is done
by pure functions (``parse_*``) so it is tested offline against recorded fixtures.

NOTHING HERE COMPUTES AN INDICATOR. A payload carries what the source said — a date, a
number, a unit — and, for the one source whose declared calculation needs a price history
(the 200-day average), the raw closes. Ratios, spreads, percentiles and scores belong to
the engine's executor behind the raw/dial boundary.

WO-1.14 adds ONE adapter that asks a different question of the same kind of source:
:class:`FredVintageAdapter` fetches one observation AS FIRST PUBLISHED, by reading FRED's
vintages for the earliest one that served it (WO-1.17: through FRED's documented REST API, which
replaced the ALFRED graph-CSV mechanism WO-1.14 first used). It still only fetches and reports;
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
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Mapping, Union

import redis

from crash_detector.collectors.adapter import AdapterFetchError, FetchedResponse

__all__ = [
    "RESPONSE_SCHEMA",
    "VINTAGE_RESPONSE_SCHEMA",
    "FredAdapter",
    "FredVintageAdapter",
    "CboeAdapter",
    "YahooChartAdapter",
    "MultplShillerAdapter",
    "HermesCandleAdapter",
    "ManualEntryAdapter",
    "YAHOO_SHORT_PAGE_MAX_ROWS",
    "FRED_API_HOST",
    "FRED_API_BASE",
    "FRED_REALTIME_FLOOR",
    "FRED_VINTAGEDATES_BASE",
    "FredArchiveFloors",
    "NON_DATA_RESPONSE",
    "require_json_body",
    "require_csv_body",
    "parse_fred_vintagedates_floor",
    "parse_fred_vintagedates_all",
    "MAX_VINTAGE_PROBES",
    "MAX_FIRST_PUBLICATION_LAG_DAYS",
    "HERMES_PEER",
    "HERMES_CANDLE_CONTRACT",
    "HERMES_CANDLE_CONTRACT_VERSION",
    "hermes_latest_key",
    "parse_hermes_candle",
    "fred_column",
    "fred_graph_url",
    "parse_fred_csv",
    "parse_fred_csv_for_date",
    "parse_fred_rest_first_publication",
    "parse_fred_rest_at_vintage",
    "cboe_history_url",
    "parse_cboe_csv",
    "parse_cboe_csv_for_date",
    "parse_yahoo_chart",
    "parse_yahoo_chart_for_date",
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
#:   SERVER's own response named (see :func:`parse_fred_rest_first_publication`), not the one we asked
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


# --- the fredgraph.csv request, built in ONE place ------------------------------------- #
#
# WO-1.17. These two were inline in :class:`FredAdapter` and are lifted out UNCHANGED because a
# SECOND caller now needs the same request: ``ingestion.backfill_calendar`` asks FRED for a
# series' whole undated body to read the dates it publishes on. A date list is only honest if it
# is the calendar of the body the backfill will actually READ, so that module must ask the
# identical question of the identical URL — and the only way to guarantee that over time is for
# there to be one builder rather than two that agree today.
#
# Not a general tidy-up: ``tools/probe/*`` carry their own copies of the column expression and are
# deliberately untouched here. The probes are frozen evidence scripts.


def fred_column(series: str, transformation: Union[str, None]) -> str:
    """The value-column header ``fredgraph.csv`` returns for this (series, transformation).

    FRED names the column after the series, suffixed with the UPPERCASED transform when one was
    requested server-side (``M2SL`` + ``pc1`` -> ``M2SL_PC1``). :func:`parse_fred_csv` and
    :func:`parse_fred_csv_for_date` both refuse a body whose header is not exactly this, so this
    is the expectation those refusals are measured against and not a cosmetic label.
    """
    return series + (f"_{transformation.upper()}" if transformation else "")


def fred_graph_url(series: str, transformation: Union[str, None] = None, *,
                   observation_date: Union[str, None] = None) -> str:
    """The ``fredgraph.csv`` URL. UNDATED by default, which is the whole-series body.

    With ``observation_date`` set the request carries ``cosd=D&coed=D`` — the window
    :class:`FredAdapter` uses in its dated mode, and a COURTESY rather than a promise: FRED
    ignores a window lying entirely before the series' first observation and returns the whole
    body anyway (``evidence/wo115_fred_window_probe.json``), which is why every reader of this
    body matches on the date KEY and never on position.

    Left undated, this is character-for-character the URL the live collector has always issued
    for a FRED ingredient, and ``tests/test_ingestion.py`` holds that by equality against the
    adapter so an edit here cannot quietly move the live loop's destination.
    """
    suffix = f"&transformation={transformation}" if transformation else ""
    window = ("" if observation_date is None else
              f"&cosd={observation_date}&coed={observation_date}")
    return f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}{suffix}{window}"


#: FRED's documented REST API — the ONE door the point-in-time (vintage) backfill reads through.
#: ``/fred/series/observations`` takes ``realtime_start``/``realtime_end``, and with a wide window it
#: returns every distinct vintage of an observation, each row stating the span it was valid for.
#:
#: WHY THIS REPLACED ``alfred.stlouisfed.org/graph/alfredgraph.csv`` (WO-1.17). The graph-CSV
#: vintage mechanism was found broken on 2026-10-18 and stayed broken through 2026-10-20, confirmed
#: across three unrelated series (GDP, WALCL, NFCI): it silently answered with the CURRENT value under
#: a label naming today's (or a frozen stale) date whatever ``vintage_dates`` asked for. That was an
#: EXTERNAL fault, and the header check in the old parser refused every corrupted body rather than
#: store it. The REST API is a documented, keyed interface and was unaffected.
#:
#: IT NEEDS A CREDENTIAL, AND THE CREDENTIAL IS NEVER READ HERE. :class:`FredVintageAdapter` takes
#: the key as an explicit constructor argument, the same discipline as ``clock``: this module
#: consults no process state for it. The host-level driver (``tools/backfill/wo117_run.py``) reads
#: ``FRED_API_KEY`` once and threads it down. The key is part of the REQUEST URL the getter is given
#: and of nothing else — it is not in :meth:`FredVintageAdapter._url`, not in any payload and not in
#: any failure (PBG-SEC-002).
#:
#: DELIBERATELY NOT IN ``ingestion.catalog.EGRESS_HOSTS`` NOR IN ``deploy/egress-destinations.yaml``,
#: for the reason the ALFRED host was not: both are the LIVE ``cd-collectors`` container's egress
#: declaration, and this host is reached only by the backfill driver, which runs directly on the host
#: (``python3 tools/backfill/wo117_run.py``) and not inside any compose service. The host is declared
#: in ``ingestion.backfill_adapters.BACKFILL_EGRESS_HOSTS``.
FRED_API_HOST = "api.stlouisfed.org"
FRED_API_BASE = f"https://{FRED_API_HOST}/fred/series/observations"

#: The left edge of the wide ``realtime_start`` an untransformed fetch asks for: comfortably before
#: any series' real archive floor, so the first row returned is the earliest vintage FRED holds.
FRED_REALTIME_FLOOR = "1900-01-01"

#: ``/fred/series/vintagedates``: every date on which a series' data changed, ascending. Its FIRST
#: entry is the series' ARCHIVE FLOOR — the earliest vintage FRED/ALFRED holds for it at all — which
#: is the one fact ``MAX_FIRST_PUBLICATION_LAG_DAYS`` could not supply (WO-1.17 §6, below). Same host
#: and key as :data:`FRED_API_BASE`, so no new egress. Asked ONCE per series by
#: :class:`FredArchiveFloors`, never once per date.
FRED_VINTAGEDATES_BASE = f"https://{FRED_API_HOST}/fred/series/vintagedates"

#: Hard ceiling on the observation GETs ONE :meth:`FredVintageAdapter.fetch` may issue. An
#: untransformed row costs ONE. A transformed row (the server refuses a wide ``realtime`` range for
#: any ``units`` other than ``lin``) is SCANNED: today's vintage, the vintage before the observation
#: (or the floor), then the real vintage dates inside the 365-day window in order until one serves a
#: value. A genuine first publication is found in a handful (PCEPILFE: 2-3; a weekly series
#: ~8-9), but the window can hold up to 53 weekly vintages, so the ceiling is 60: it guards a
#: broken invariant looping, not a budget the search approaches. Reaching it is a recorded failure
#: and never a partial answer.
MAX_VINTAGE_PROBES = 60

#: The widest gap, in CALENDAR DAYS, between an observation date and the vintage that first
#: serves it that may still be read as a FIRST PUBLICATION. Past it,
#: :class:`FredVintageAdapter` refuses the fetch instead of handing the caller a
#: restatement to label ``original``.
#:
#: WHY A CEILING IS NEEDED AT ALL (WO-1.17 cost estimate §7.1). The bisection's floor is the
#: observation date, which makes "a vintage that could not have known" impossible. NOTHING
#: bounds it from above, so the rule cannot tell the first vintage published AFTER the figure
#: was published from the first vintage ALFRED HAPPENS TO KEEP. ALFRED's archive starts on a
#: different date for every series (``tools/probe/alfred_vintage_probe.py::vintage_depth``
#: measures 17 of them, 1990 to 2023) and answers 404 beneath it; a 404 is the same
#: ``_ABSENT`` an unpublished vintage gives, so the search converges on the ARCHIVE's floor
#: and returns it as though it were a publication event. §7.1 measured that on 10 of the 17
#: bisected rows, at gaps of 8.6 to 15.4 YEARS.
#:
#: WHY 365 AND NOT LESS. The number has to clear the slowest GENUINE publication this adapter
#: serves, and FRED dates a quarterly observation at the quarter's START, so the gap already
#: contains the whole quarter before the release lag begins. ``evidence/wo114_backfill_proof.json``
#: measured ``fred.GDP``'s own bisection seven times: the advance estimate lands ~120 days
#: after the observation date — and observation 2025-07-01 was first served by vintage
#: 2025-12-23, **175 days**, a real first publication admitted as ``original`` with a value
#: that differs from today's. Quarterly Z.1 (``fred.NCBEILQ027S``) is structurally slower
#: still. 365 is 2.1x the longest gap measured here and leaves half a year of slack, because
#: a ceiling that holds only while the source keeps to its schedule would discard real
#: point-in-time data exactly when the source is disrupted — which is when a replay of a
#: crash most needs it.
#:
#: WHY 365 AND NOT MORE. Every restatement §7.1 measured is 3,123 to 5,615 days, so the band
#: between the two populations is empty for an order of magnitude either way and the exact
#: number inside it buys little: against §7.1's eight windows, 365 refuses 2,057 of 2,265
#: affected fetches where 180 would refuse 2,093 — 36 fetches, 1.6%, for a 5-day margin
#: against a publication this project has already seen.
#:
#: WHAT IT CANNOT CATCH, DECLARED — AND, SINCE WO-1.17, CAUGHT ELSEWHERE. The ~208 it misses are observations within a year of their
#: OWN series' archive floor, whose gaps (1 to 244 days) overlap genuine publication lags. No
#: threshold separates those at any value: a restatement served a month after the observation
#: is arithmetically identical to a first publication served a month after it. Closing that
#: needs a probe this adapter does not make — "does any vintage of this series exist on date
#: V", a different question from the one the bisection asks.
#:
#: THAT PROBE NOW EXISTS, and this constant alone was NOT sufficient: the real WO-1.17 re-run admitted
#: 83 near-floor restatements through it (IC4WSA 52 with lags to 362 days, WALCL 19, NFCI 12), found
#: by verifying the admissions rather than the exit code. :class:`FredArchiveFloors` answers the
#: question exactly and ``vintage_archive_floor`` refuses on it. This ceiling stays: it still refuses
#: a restatement served AFTER the floor (e.g. a late-added observation), which the floor test cannot.
MAX_FIRST_PUBLICATION_LAG_DAYS = 365

#: A series id and a transformation are interpolated into a URL, so what may appear there is
#: stated POSITIVELY and anything else is refused at construction. Not a leak control (that is
#: PBG-SEC-002, below) — a refusal to build a request out of a string nobody vouched for.
_SERIES_ID = re.compile(r"^[A-Za-z0-9_]{1,64}$")
_TRANSFORMATION = re.compile(r"^[a-z0-9]{1,16}$")
#: A FRED API key is 32 lowercase-hex characters today; what is permitted here is a looser, positive
#: alphanumeric shape, so a malformed value (a stray newline, a quote, an ``&``) is refused at
#: construction instead of being interpolated into a URL.
_API_KEY = re.compile(r"[A-Za-z0-9]{16,64}\Z")


def _rest_rows(text: str, observation_date: str, *, realtime_start: str, realtime_end: str,
               units: str) -> Union[list, dict]:
    """The vintage rows of ONE observation out of a ``/fred/series/observations`` JSON body.

    Returns a list of ``(realtime_start, realtime_end, token)`` sorted by ``realtime_start`` — one
    entry per distinct vintage FRED carries for ``observation_date`` — or ``{"malformed": reason}``
    for a body we do not understand. The reason is a stable token and never body text.

    THE ECHO IS CHECKED, FOR THE SAME REASON THE OLD CSV HEADER WAS. The REST body states the
    ``realtime_start``/``realtime_end``/``units`` and observation window it answered, so a body that
    answered a different question than the one asked is MALFORMED and is never read as the one
    requested. The graph-CSV fault this replaced was exactly a server-side substitution that said so
    in its header and nowhere else; that refusal is what kept the store incomplete rather than
    corrupt, and it is ported rather than dropped.

    THE OBSERVATION IS MATCHED BY EXACT DATE, never taken as "the only row", and every row's own
    validity span must lie inside the window that was asked for. A row that does not is MALFORMED
    rather than skipped, because a span we did not ask for is a source we do not understand.
    """
    try:
        document = json.loads(text)
    except ValueError:
        return {"malformed": "body"}
    if not isinstance(document, dict) or not isinstance(document.get("observations"), list):
        return {"malformed": "body"}
    if document.get("realtime_start") != realtime_start or document.get("realtime_end") != realtime_end:
        return {"malformed": "realtime"}
    if document.get("units") != units:
        return {"malformed": "units"}
    if (document.get("observation_start") != observation_date
            or document.get("observation_end") != observation_date):
        return {"malformed": "window"}
    rows = []
    for item in document["observations"]:
        if not isinstance(item, dict):
            return {"malformed": "row"}
        when, opens, closes, token = (item.get("date"), item.get("realtime_start"),
                                      item.get("realtime_end"), item.get("value"))
        if not all(isinstance(part, str) for part in (when, opens, closes, token)):
            return {"malformed": "row"}
        try:
            span = (date.fromisoformat(opens), date.fromisoformat(closes))
            window = (date.fromisoformat(realtime_start), date.fromisoformat(realtime_end))
        except ValueError:
            return {"malformed": "row"}
        if not window[0] <= span[0] <= span[1] <= window[1]:
            return {"malformed": "row"}
        if when != observation_date:
            continue
        rows.append((opens, closes, token))
    rows.sort()
    return rows


def parse_fred_rest_first_publication(text: str, unit: str, observation_date: str, *,
                                      realtime_end: str) -> dict:
    """The EARLIEST vintage of ONE observation, out of a WIDE-window untransformed body.

    Four outcomes, kept apart:

    * **a value** — the earliest vintage that carried a figure for ``observation_date``; the
      payload names that vintage's own ``realtime_start``;
    * **``{"unit": ...}``** — EMPTY. FRED has never, at any vintage, carried a figure for this date
      (no row, or only ``.`` rows), or the LATEST vintage no longer carries one. Not zero, not an
      error, and not someone else's number;
    * **``{"malformed": ...}``** — a body we do not understand (see :func:`_rest_rows`);
    * a value that is not a finite number is carried out untouched so the closed schema is what
      rejects it, the convention :func:`parse_fred_csv` follows.

    A vintage printing ``.`` has published no figure, so it is skipped when looking for the first
    one that did; the same rule the CSV reader applied to FRED's ``.``.

    THE LATEST VINTAGE MUST STILL CARRY IT. The CSV mechanism probed today's vintage first and
    answered EMPTY if it was absent ("no vintage serves it now, so there is nothing to backfill").
    This keeps that meaning on the new body: the final row must be valid through ``realtime_end`` and
    must not be ``.``.
    """
    rows = _rest_rows(text, observation_date, realtime_start=FRED_REALTIME_FLOOR,
                      realtime_end=realtime_end, units="lin")
    if isinstance(rows, dict):
        return rows
    if not rows or rows[-1][2] == "." or rows[-1][1] < realtime_end:
        return {"unit": unit}
    for opens, _closes, token in rows:
        if token != ".":
            return {"unit": unit, "observation_date": observation_date,
                    "value": _number_or_token(token), "vintage_date": opens}
    return {"unit": unit}


def parse_fred_rest_at_vintage(text: str, unit: str, observation_date: str, units: str,
                               vintage_date: str) -> dict:
    """ONE observation as ONE named vintage served it, out of a SINGLE-DAY-window body.

    The transformed-series reader (``units`` other than ``lin``), where the server refuses a wide
    window. Three outcomes, kept apart because the scan in :class:`FredVintageAdapter` turns on
    exactly this distinction: a value (``_SERVED``); ``{"unit": ...}`` (``_ABSENT`` — the vintage
    carried no figure for the date, which the REST API answers as ``200`` with ``count`` 0 and not
    as an HTTP error); ``{"malformed": ...}`` (never read as either of the other two, because
    "I could not read the answer" and "the answer was no" send the search opposite ways).
    """
    rows = _rest_rows(text, observation_date, realtime_start=vintage_date,
                      realtime_end=vintage_date, units=units)
    if isinstance(rows, dict):
        return rows
    if len(rows) > 1:
        return {"malformed": "row"}
    if not rows or rows[0][2] == ".":
        return {"unit": unit}
    return {"unit": unit, "observation_date": observation_date,
            "value": _number_or_token(rows[0][2]), "vintage_date": vintage_date}


def parse_fred_vintagedates_floor(text: str, *, realtime_end: str) -> Union[date, None]:
    """The EARLIEST vintage date out of a ``/fred/series/vintagedates`` body, or ``None``.

    ``None`` is "I could not read this" — never "the series has no floor". Every way a body can
    fail to be the answer to the question asked is ``None``, and no body text leaves this function:
    not JSON, not an object, a window or order other than the one requested (the echo is checked,
    as :func:`_rest_rows` checks its own), an empty or non-string list, an unparseable date. A
    series with NO vintage at all cannot have been asked about by a caller that already holds a
    figure for it, so empty is unreadable too and not a floor of "never".
    """
    try:
        document = json.loads(text)
    except ValueError:
        return None
    if not isinstance(document, dict):
        return None
    if (document.get("realtime_start") != FRED_REALTIME_FLOOR
            or document.get("realtime_end") != realtime_end or document.get("sort_order") != "asc"):
        return None
    listed = document.get("vintage_dates")
    if not isinstance(listed, list) or not listed or not isinstance(listed[0], str):
        return None
    try:
        return date.fromisoformat(listed[0])
    except ValueError:
        return None


class FredArchiveFloors:
    """One series' ARCHIVE FLOOR — the earliest vintage FRED holds for it — asked once and kept.

    WHY THIS EXISTS (WO-1.17, found by verifying the real re-run's 1,135 admissions). FRED's archive
    starts on a different date for every series, and every observation OLDER than that start is
    answered with the archive's own first vintage: a restatement, however recent the observation.
    ``MAX_FIRST_PUBLICATION_LAG_DAYS`` refuses such an answer only when it is more than a year late;
    WO-1.18 declared the remainder ("a near-floor restatement cannot be told from a lagged
    publication by arithmetic at any threshold") and said what closing it needed — "does any vintage
    of this series exist on date V". This is that probe, and it is exact where the ceiling was
    approximate: a figure whose first serving vintage IS the archive floor was not observed to be
    first published there, only first KEPT there. 83 such values were admitted before this class
    existed (IC4WSA 52 at 2009-05-28, WALCL 19 at 2011-07-07, NFCI 12 at 2011-05-25).

    ONE GET PER SERIES, NOT PER DATE. :meth:`floor` caches a success for the life of the object, so
    a backfill range that builds one adapter per date asks the endpoint once. The cache is
    per-instance and never module state, and a failure is never cached: an unreadable answer is
    returned as ``None`` and asked again next time. HTTP and network failures propagate as the
    getter's :class:`AdapterFetchError`, with no message (PBG-SEC-002).

    THE GETTER IS THE CALLER'S, passed per call, so the transport that answers the observation
    requests is the one that answers this — a test that substitutes the one cannot leave the other
    on the network. The key is a required constructor argument validated like the adapter's, and is
    held in no attribute but the request URL's.
    """

    __slots__ = ("_api_key", "_clock", "_floors", "_vintages")

    def __init__(self, api_key: str, *, clock: Callable[[], datetime]) -> None:
        if not isinstance(api_key, str) or not _API_KEY.match(api_key):
            raise ValueError("api key is not in the permitted shape")  # never echo what was given
        self._api_key = api_key
        self._clock = clock
        self._floors: dict = {}
        self._vintages: dict = {}

    def floor(self, series: str, timeout_seconds: float,
              getter: Callable[..., str]) -> Union[date, None]:
        if not isinstance(series, str) or not _SERIES_ID.match(series):
            raise ValueError("series id is not in the permitted shape")
        known = self._floors.get(series)
        if known is not None:
            return known
        today = self._clock().date().isoformat()
        query = urllib.parse.urlencode([
            ("series_id", series), ("realtime_start", FRED_REALTIME_FLOOR), ("realtime_end", today),
            ("sort_order", "asc"), ("limit", "1"), ("file_type", "json"),
            ("api_key", self._api_key)])
        found = parse_fred_vintagedates_floor(
            require_json_body(getter(FRED_VINTAGEDATES_BASE + "?" + query, timeout_seconds, None)),
            realtime_end=today)
        if found is not None:
            self._floors[series] = found
        return found

    def vintages(self, series: str, timeout_seconds: float,
                 getter: Callable[..., str]) -> Union[list, None]:
        """EVERY vintage date of ``series``, ascending, asked ONCE per series and kept.

        The transformed path SCANS these instead of bisecting (see :class:`FredVintageAdapter`):
        one GET per series buys the exact set of dates a probe can usefully be made at, where a
        bisection pays 13-15 probes per DATE and was unsound wherever the archive is not monotone.
        Same failure discipline as :meth:`floor`: a failure is never cached, an unreadable or
        truncated answer is ``None``, transport failures propagate as the getter's error.
        """
        if not isinstance(series, str) or not _SERIES_ID.match(series):
            raise ValueError("series id is not in the permitted shape")
        known = self._vintages.get(series)
        if known is not None:
            return known
        today = self._clock().date().isoformat()
        query = urllib.parse.urlencode([
            ("series_id", series), ("realtime_start", FRED_REALTIME_FLOOR), ("realtime_end", today),
            ("sort_order", "asc"), ("limit", "10000"), ("file_type", "json"),
            ("api_key", self._api_key)])
        found = parse_fred_vintagedates_all(
            require_json_body(getter(FRED_VINTAGEDATES_BASE + "?" + query, timeout_seconds, None)),
            realtime_end=today)
        if found is not None:
            self._vintages[series] = found
        return found


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
    :func:`_rest_rows` follows against a body that carries other rows for the same reason.
    A body nobody asked for cannot fool an exact-key match: it either carries a row dated
    ``observation_date`` or it does not.

    Three outcomes, kept apart:

    * **a value** — a row dated exactly ``observation_date`` carrying a figure;
    * **``{"unit": ...}``** — no such row, or the row is present with FRED's ``.`` (or an
      empty cell) for no data. EMPTY, not zero, and not someone else's number;
    * **``{"malformed": ...}``** — a header that is not ``observation_date,<column>``. The
      check is :func:`parse_fred_csv`'s, character for character, because it is the same
      endpoint answering the same series; plain FRED's header carries no vintage to verify,
      which is the one check :func:`_rest_rows` has (the response echoes its own vintage) and this does not.

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
    """Which of the three :func:`parse_fred_rest_at_vintage` outcomes this payload is.

    A value that is not a finite number is ``_UNREADABLE``, NOT ``_SERVED``. The token is
    still carried out of the search untouched so the closed schema is the thing that rejects
    it (the convention :func:`parse_fred_csv` follows), but the search stops on it: a
    scan cannot step over an answer it could not read without guessing what the vintage said.
    """
    if "malformed" in payload:
        return _UNREADABLE
    if "value" not in payload:
        return _ABSENT
    return _SERVED if type(payload["value"]) is float else _UNREADABLE


def cboe_history_url(index: str) -> str:
    """The ``{index}_History.csv`` URL. There is no dated variant, and that is MEASURED.

    ``cdn-api.cboe.com`` honours NO date-windowing parameter: eight spellings (``dt``,
    ``date``, ``startDate``/``endDate``, ``start``/``end``, ``from``/``to``,
    ``start_date``/``end_date``, FRED's own ``cosd``/``coed``) plus a nonsense control each
    came back ``200`` with a body BYTE-IDENTICAL to this bare URL's, same SHA-256 and same row
    count (probed 2026-10-15, ``tools/probe/cboe_history_probe.py``,
    ``evidence/wo116_cboe_probe.json``). So this takes no ``observation_date``, where
    :func:`fred_graph_url` does: there is nothing for a dated request to ask for, and a
    parameter that could not change the response would be a promise this endpoint never made.

    That one body serves both readers — :func:`parse_cboe_csv` for "what is this index at
    now?", :func:`parse_cboe_csv_for_date` for one named date, and
    ``ingestion.backfill_calendar.cboe_observation_dates`` for the whole date list — so there
    is ONE way to ask Cboe for an index's history and not three that agree today.
    ``tests/test_wo117_calendar.py`` holds this equal to :meth:`CboeAdapter._url` so an edit
    here cannot quietly move the live loop's destination.
    """
    return f"https://cdn-api.cboe.com/api/global/us_indices/daily_prices/{index}_History.csv"


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

#: The agent string Yahoo's edge requires, and it is not cosmetic: this endpoint answers 429 to
#: urllib's default agent and 200 to an identified browser-style one, where FRED's edge does the
#: opposite (see :func:`http_get`). It is a module constant rather than a literal inside
#: :meth:`YahooChartAdapter._headers` because there is now a SECOND caller that must send the
#: same header — ``ingestion.backfill_calendar.yahoo_observation_dates`` — and two copies of an
#: agent string that must match is the shape in which one of them quietly stops matching.
YAHOO_USER_AGENT = "Mozilla/5.0 (compatible; cerberus-ingest/1.0)"


def yahoo_chart_url(symbol: str, *, relative_range: Union[str, None] = None,
                    start: Union[str, None] = None, end: Union[str, None] = None) -> str:
    """The v8 chart URL, windowed ONE way or the OTHER and never both. Measured, not preferred.

    Lifted out of :meth:`YahooChartAdapter._url` in WO-1.17 for the reason
    :func:`cboe_history_url` was lifted out of :meth:`CboeAdapter._url` in WO-1.16: a third
    reader of this endpoint now exists (``ingestion.backfill_calendar.yahoo_observation_dates``,
    the whole date list) beside the live poll and the per-date backfill, and three places
    building the same URL is three conventions that agree today.
    ``tests/test_ingestion.py`` and ``tests/test_wo117_calendar.py`` hold this equal to the
    adapter's URL in BOTH of its modes, so the lift cannot have moved the live loop's
    destination by a character.

    TWO MECHANISMS, EXACTLY ONE PER REQUEST, AND THE EXCLUSIVITY IS A RAISE.
    ``relative_range`` is the ``range=`` the live loop has always sent (``10d``, or ``2y`` for a
    history read); ``start``/``end`` is an absolute ``period1``/``period2`` window over whole UTC
    days, inclusive at both ends. Given BOTH in one URL, ``range`` silently WINS and the period
    window is ignored — ``range=2y`` plus a one-day window for 2015-06-08 answered 502 bars
    ending at that morning's (probed 2026-10-15, ``evidence/wo116_yahoo_window_probe.json``,
    ``q6_range_and_period_together``). A builder that could emit both would therefore be a
    builder that can silently answer a historical question with today's bars, so it refuses.

    THE WINDOW IS WHOLE UTC DAYS BECAUSE A ``1d`` BAR IS STAMPED AT THE SESSION OPEN — 1433770200
    is 2015-06-08T13:30Z for a US listing on summer time, 14:30Z the same session in winter — so
    the window must CONTAIN that instant: ``period1`` = 00:00:00Z of ``start``, ``period2`` =
    00:00:00Z of ``end``+1 LESS ONE SECOND. The encoding a caller reaches for first (a zero-width
    point at midnight) returns ZERO BARS for a real trading day on three measured symbols
    (``q2_window_one_day_zero_width``), an off-by-one that looks exactly like a market holiday.
    ``start == end`` is the single-day window :class:`YahooChartAdapter` has always built for a
    dated fetch, character for character; a wider pair is the same arithmetic over more days.

    A REVERSED WINDOW IS A RAISE AND NOT A URL, because the server's answer to one is a clean
    ``400`` (``q5_window_reversed``) — a URL builder whose output can only be a fetch failure
    should not build it. ``start == end`` is not reversed and is the ordinary one-day case.

    AND ``range=max`` IS DELIBERATELY NOT HOW THE DEEP READS ARE ASKED FOR, measured 2026-10-16
    (``evidence/wo117_yahoo_range_probe.json``): ``max`` IS an honoured value — the server echoes
    ``meta.range == "max"`` and it is in every symbol's own ``meta.validRanges`` — but it is
    served at a COARSENED granularity with ``interval=1d`` ignored: SPY came back 406 bars at
    ``dataGranularity == "1mo"`` and ``^GSPC`` 169 bars at ``"3mo"``, starting 1984-12-01 where
    the same symbol's absolute window reaches 1927-12-30. So a date list read off a ``range=max``
    body would be a list of MONTH-START dates wearing the costume of a daily calendar. The
    absolute window keeps ``1d`` at every depth measured (``^GSPC`` 1927-12-30..2026-10-15 is
    24,815 daily bars, 2,654,167 bytes, ONE GET), which is why the deep reader uses it.
    """
    windowed = start is not None or end is not None
    if windowed and relative_range is not None:
        raise ValueError(
            f"range={relative_range!r} and an absolute {start}..{end} window in one URL: given "
            f"both, RANGE WINS and the window is ignored (evidence/wo116_yahoo_window_probe.json,"
            f" q6_range_and_period_together). One mechanism per request, never both")
    if windowed and (start is None or end is None):
        raise ValueError(
            f"an absolute window needs BOTH bounds; got start={start!r} end={end!r}. A half "
            f"window is not a window this endpoint can be asked for")
    if not windowed and relative_range is None:
        raise ValueError(
            "no window at all: pass relative_range (the live loop's range=) or both start and "
            "end (an absolute period1/period2 window)")
    quoted = symbol.replace("^", "%5E").replace("=", "%3D")
    chart = f"https://query1.finance.yahoo.com/v8/finance/chart/{quoted}"
    if relative_range is not None:
        return f"{chart}?range={relative_range}&interval=1d"
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if last < first:
        raise ValueError(
            f"{start}..{end} is reversed, and this endpoint answers a reversed window with a "
            f"clean 400 (q5_window_reversed): a URL that can only fail is not built")
    opened = datetime(first.year, first.month, first.day, tzinfo=timezone.utc)
    last_second = (datetime(last.year, last.month, last.day, tzinfo=timezone.utc)
                   + timedelta(days=1) - timedelta(seconds=1))
    return (f"{chart}?period1={int(opened.timestamp())}"
            f"&period2={int(last_second.timestamp())}&interval=1d")


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


def parse_yahoo_chart_for_date(text: str, unit: str, observation_date: str) -> dict:
    """ONE named daily close read out of a Yahoo v8 chart body, matched by EXACT DATE.

    WO-1.16, and it sits beside :func:`parse_yahoo_chart` for the reason
    :func:`parse_fred_csv_for_date` and :func:`parse_cboe_csv_for_date` sit beside their own
    latest-row parsers: "what is this symbol at now?" is answered by the LAST bar, and that
    cannot be the answer to "what did it close at on 2015-06-08?".

    THE WINDOW IS HONEST HERE, AND THE EXACT MATCH IS STILL THE DISCIPLINE. Unlike plain FRED
    — which IGNORES a window lying before a series' start and answers with the whole
    unfiltered series — Yahoo's ``period1``/``period2`` is either applied or the request is
    refused outright: a one-day window on a trading day returns exactly one correctly-dated
    bar, and an impossible window is a clean ``400``, never someone else's bars (probed
    2026-10-15, ``tools/probe/yahoo_period_window_probe.py``,
    ``evidence/wo116_yahoo_window_probe.json``, cases ``q2_window_one_day_utc_day`` and
    ``q4_*``). So there is no dangerous body to defend against the way there is for FRED.
    The match is on the KEY anyway, and not only for consistency with the two parsers above:
    a caller that windowed WRONGLY — or not at all, since ``range=`` silently WINS over a
    period window in the same URL (``q6_range_and_period_together``: 502 bars, this morning's
    last) — hands this function a body full of bars nobody asked about. A position read would
    answer that with today's close under a historical key. An exact match cannot: the body
    carries a bar dated ``observation_date`` or it does not.

    AN EMPTY WINDOW IS NOT A BROKEN BODY, and this is the ONE check that could not be
    :func:`parse_yahoo_chart`'s, reused though the rest of them are. A window matching no bar
    — a weekend, a market holiday, a zero-width window — is answered ``200`` with the envelope
    and ``meta`` intact and the bar arrays simply ABSENT: ``"indicators":{"quote":[{}]}`` and
    NO ``timestamp`` key at all (``q3_window_on_non_trading_day``, SPY on 2015-06-13).
    :func:`parse_yahoo_chart` reads that as ``{"malformed": "shape"}``, which is correct for
    ITS question — the live loop asks for a ten-day range, and a ten-day range with no bars in
    it is a body we cannot read — and wrong for this one, where it is the ordinary answer "the
    symbol did not print on this date". So here a MISSING bar array means "no bars"; every
    other shape check is :func:`parse_yahoo_chart`'s, unchanged.

    Three outcomes, kept apart:

    * **a value** — a bar whose UTC date is exactly ``observation_date``. The date is derived
      from the bar's ``timestamp`` exactly as :func:`parse_yahoo_chart` derives it (a ``1d``
      bar is stamped at the session OPEN, 1433770200 = 2015-06-08T13:30Z for a US listing, so
      the UTC date of the stamp is the session's date). The raw token is passed through by
      :func:`_number_or_token`, never defaulted;
    * **``{"unit": ...}``** — no bar for that date (the absent-array case above, and equally a
      body of bars for other dates), or a matched bar whose ``close`` is ``null``: Yahoo nulls
      a session it has no print for, and that skip is :func:`parse_yahoo_chart`'s, kept here.
      Under an exact-date match a skipped bar cannot be replaced by a neighbouring one, so a
      nulled session falls out as EMPTY rather than as some other day's close;
    * **``{"malformed": ...}``** — anything the shape checks reject: not JSON, no
      ``chart.result[0]``, no ``indicators.quote[0]``, ``timestamp`` and ``close`` of
      different lengths, or a ``timestamp`` that is not a readable epoch second.

    CLOSE ONLY, no ``field``. :func:`parse_yahoo_chart` can read ``adjclose`` and two live
    ingredients deliberately do, which is why :class:`YahooChartAdapter` REFUSES a dated
    request for that field outright rather than letting it be answered with the unadjusted
    close — argued there.

    NO ``history`` and no ``today``. No history for :func:`parse_fred_csv_for_date`'s reason:
    a one-day window has no history in it. No ``today`` because that guard exists for a range
    that ENDS at the live session — a dated request for a past date cannot reach a partial bar
    — and refusing a date that has not closed yet is the backfill driver's floor to hold, not
    this function's (``ingestion.backfill_adapters``, a later round).
    """
    try:
        result = json.loads(text)["chart"]["result"][0]
        quote = result["indicators"]["quote"][0]
        # ABSENT bar arrays are the probed shape of "no bar in this window", so they are read
        # as no bars and not, as parse_yahoo_chart reads them, as an unreadable body.
        stamps = result.get("timestamp") or []
        closes = quote.get("close") or []
        if len(stamps) != len(closes):
            return {"malformed": "shape"}
        for stamp, close in zip(stamps, closes):
            if close is None:  # Yahoo nulls a session it has no print for; skip, never fill.
                continue
            if datetime.fromtimestamp(stamp, tz=timezone.utc).date().isoformat() != observation_date:
                continue
            return {"unit": unit, "observation_date": observation_date,
                    "value": _number_or_token(str(close))}
    except (AttributeError, IndexError, KeyError, OSError, OverflowError, TypeError, ValueError):
        # The iteration is inside the guard, unlike parse_yahoo_chart's: a timestamp that is
        # not a readable epoch second is a body we cannot read, which is MALFORMED and must
        # not be an exception escaping into the collector.
        return {"malformed": "shape"}
    return {"unit": unit}

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


#: The ``error_class`` of a fetch that got an HTTP answer which is not DATA in the shape asked for.
#:
#: FOUND 2026-10-21, DURING WO-1.17's OWN VERIFICATION. FRED went into a site-wide maintenance
#: window and answered EVERY endpoint - ``fredgraph.csv``, ``/fred/series/observations``,
#: ``/fred/series/vintagedates`` - ``200`` with an HTML "Site Maintenance" page. A ``200`` is not
#: an ``HTTP_ERROR``, so ``http_get`` passed it through, every parser saw a body it could not read,
#: and the store recorded the attempts as ``MALFORMED``: the class that means "FRED gave a
#: well-formed answer and the answer itself failed validation". It was nothing of the kind, and
#: from the store alone an outage was indistinguishable from a refusal.
#:
#: THE RULE: ``MALFORMED`` means a WELL-FORMED answer failed validation. "We could not tell what
#: FRED gave us" - JSON asked for and not JSON, CSV asked for and not CSV - is a SERVICE failure
#: and is raised here, before any parser, so it is recorded ``FETCH_FAILED`` under this class,
#: which is not ``MALFORMED``, ``vintage_archive_floor`` or ``vintage_too_distant``. A body that
#: IS the right shape and says the wrong thing (a substituted header, a window or units echo that
#: differs, an unreadable value) is untouched and stays ``MALFORMED``.
NON_DATA_RESPONSE = "NON_DATA_RESPONSE"


def require_json_body(text: str) -> str:
    """``text`` unchanged if it parses as JSON; otherwise ``AdapterFetchError(NON_DATA_RESPONSE)``.

    Used where ``file_type=json`` was asked. It checks that the body IS JSON and nothing about what
    the JSON says: that is the parser's validation, and failing it is a ``MALFORMED``, not this.
    No body text is carried (PBG-SEC-002).
    """
    try:
        json.loads(text)
    except ValueError:
        raise AdapterFetchError(NON_DATA_RESPONSE) from None
    return text


def require_csv_body(text: str) -> str:
    """``text`` unchanged if it looks like CSV; otherwise ``AdapterFetchError(NON_DATA_RESPONSE)``.

    Used where ``fredgraph.csv`` was asked. "Looks like CSV" is deliberately minimal - a non-empty
    body that is not markup - because everything stricter (the header, its columns, the series
    asked for) is the parser's validation and a failure of it is ``MALFORMED``.
    """
    lines = text.strip().splitlines()
    if not lines or lines[0].lstrip().startswith("<"):
        raise AdapterFetchError(NON_DATA_RESPONSE)
    return text


def parse_fred_vintagedates_all(text: str, *, realtime_end: str) -> Union[list, None]:
    """EVERY vintage date out of a ``/fred/series/vintagedates`` body, ascending, or ``None``.

    Same discipline as :func:`parse_fred_vintagedates_floor`: ``None`` is "I could not read this" and
    never "the series has no vintages". The echo is checked (window and order), the dates must be
    strictly ascending, and a body whose ``count`` exceeds what it lists is TRUNCATED and therefore
    unreadable: a scan over a partial list would skip vintages and could call a served date absent.
    """
    try:
        document = json.loads(text)
    except ValueError:
        return None
    if not isinstance(document, dict):
        return None
    if (document.get("realtime_start") != FRED_REALTIME_FLOOR
            or document.get("realtime_end") != realtime_end or document.get("sort_order") != "asc"):
        return None
    listed = document.get("vintage_dates")
    if not isinstance(listed, list) or not listed or not all(isinstance(x, str) for x in listed):
        return None
    if document.get("count") != len(listed):
        return None
    try:
        parsed = [date.fromisoformat(x) for x in listed]
    except ValueError:
        return None
    if any(a >= b for a, b in zip(parsed, parsed[1:])):
        return None
    return parsed


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

    * the request carries ``cosd=D&coed=D``, windowing a
      single date on ``fredgraph.csv``;
    * the body is read by :func:`parse_fred_csv_for_date`, which matches D EXACTLY and never
      by position — see that function on WHY the window is a courtesy and not a promise;
    * an ``HTTP_ERROR``/404 becomes EMPTY rather than a failure (:meth:`_acquire`).

    WHY THE 404 IS AN ANSWER HERE AND A FAILURE THERE. A window landing on a date inside the
    series' span that the series does not have — a Saturday for a business-daily series — is
    answered ``404`` with an HTML error page, not ``200`` with a header and no rows (probed
    2026-10-15: ``evidence/wo115_fred_window_probe.json``, case ``extra_window_on_gap_date``,
    T5YIE on 2015-06-20). That 404 is FRED saying "no observation on this date", which is
    the EMPTY this adapter must report, and it is unrelated to the
    vintage adapter, whose REST endpoint answers an absent date ``200`` with ``count`` 0.
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
        return fred_graph_url(self._series, self._transformation,
                              observation_date=self._observation_date)

    def _parse(self, body: str) -> dict:
        require_csv_body(body)
        column = fred_column(self._series, self._transformation)
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


class FredVintageAdapter(_BaseAdapter):
    """``api.stlouisfed.org/fred/series/observations`` — ONE observation as it was FIRST published.

    WO-1.14 built this question against ALFRED's graph CSV; WO-1.17 moved it onto FRED's documented
    REST API when that CSV endpoint failed (see :data:`FRED_API_HOST` for the fault). The question is
    unchanged: :class:`FredAdapter` asks "what is this series' latest value?" and gets today's
    revised history; this asks "for the observation dated D, what number would a collector running
    back then actually have SEEN?" For a revised series those differ, and storing the first as
    though it were the second is lookahead bias wearing a backfill's clothes.

    THE VINTAGE-SELECTION RULE, UNCHANGED:

        **The EARLIEST vintage date, within ``[observation_date, today]``, at which FRED serves a
        non-empty value for this observation date.**

    TWO PATHS, CHOSEN ON ``transformation``, because the server forces the split. A request with
    ``units`` other than ``lin`` is REFUSED outright for a wide ``realtime`` range (HTTP 400, "then
    realtime_start must equal realtime_end"), measured 2026-10-20 for the three transformed rows.

    * **Untransformed — ONE GET.** ``realtime_start`` = :data:`FRED_REALTIME_FLOOR`,
      ``realtime_end`` = today (this adapter's own ``clock``). FRED answers with every distinct
      vintage of the observation, each row with its own validity span, so the earliest row IS the
      first publication — read, not searched for. That needs no monotonicity assumption (the whole
      history is in the body) and costs one GET where the CSV bisection cost ``2 + ceil(log2(days))``.
    * **Transformed — a SCAN over the series' real vintage dates, single-day windows.** Today's
      vintage first (absent there: EMPTY), then the vintage before the observation (or the floor),
      then the series' own vintage dates from the observation up to
      :data:`MAX_FIRST_PUBLICATION_LAG_DAYS` later, in order, until one serves a value. It replaced a
      bisection (WO-1.17 Fault 4): a bisection is sound only if "serves a value at D" never goes
      true-then-false as the vintage advances, and FRED's archive does not promise that
      (``PCEPILFE`` ``pc1`` 2000-10-01: served from 2000-11-30, ``.`` again at 2004-01-02/04). The
      vintage list is one GET per series (:meth:`FredArchiveFloors.vintages`).

    WHAT AN ABSENT VINTAGE LOOKS LIKE CHANGED. ALFRED answered ``404`` for a vintage beneath its
    archive. The REST API answers ``200`` with ``count`` 0 — for a vintage before publication AND for
    one before the series' archive alike — so there is no ``HTTP_ERROR``/404 carve-out any more: every
    HTTP failure is a genuine :class:`AdapterFetchError`, and the ceiling-probe special case ("a 404
    at today's vintage is a mistyped series id") is no longer a case at all, because a mistyped id is
    a ``400`` that propagates.

    THE FLOOR, VERIFIED AND NOT ASSUMED. A vintage dated before the observation date could not have
    known about it. On the untransformed path the first row's ``realtime_start`` IS the earliest
    serving vintage, so "does the day before already serve it?" is answered by the same body at no
    extra GET: a first vintage earlier than ``observation_date`` is refused as
    ``{"malformed": "vintage_floor"}``. On the transformed path the day before is probed.

    THE CEILING, ON BOTH PATHS (WO-1.17 §7.1, unchanged). FRED's archive starts on a different date
    for every series, and an observation OLDER than its series' archive is answered with the archive's
    own first vintage — a well-formed answer that is a RESTATEMENT, not a first publication. A gap
    wider than :data:`MAX_FIRST_PUBLICATION_LAG_DAYS` is refused as
    ``{"malformed": "vintage_too_distant"}``; that constant carries the derivation and the cases the
    arithmetic cannot reach. The two refusals are different facts (served too EARLY vs. too LATE to
    be a publication event) and keep different names. Neither name reaches the caller: both fail the
    closed ``response_schema`` identically and ``ingestion.backfill`` records the single class
    ``MALFORMED`` against the date (PBG-SEC-002).

    THE ARCHIVE FLOOR, ON BOTH PATHS (WO-1.17, added after the real re-run). The ceiling above is
    arithmetic and WO-1.18 declared where arithmetic stops: an observation within a year of its own
    series' archive start gets the archive's first vintage as a small, plausible-looking lag. The
    real re-run admitted 83 such figures as ``original`` (IC4WSA, WALCL, NFCI — each a run of
    consecutive weeks all stamped with ONE vintage date). The exact test is a fact, not a threshold:
    the series' earliest vintage, from :class:`FredArchiveFloors`, asked once per series. A figure
    whose first serving vintage EQUALS it is refused as ``{"malformed": "vintage_archive_floor"}``.
    A floor that cannot be read is ``{"malformed": "archive_floor_unreadable"}`` and the date is not
    answered on a guess. COST OF THE EXACT RULE, DECLARED: a figure genuinely first published ON the
    floor date (e.g. WALCL 2011-07-06, released 2011-07-07) is refused with the restatements, because
    the archive cannot distinguish them. One such date per series, refused rather than guessed.
    ON THE TRANSFORMED PATH the floor also removes a probe that cannot be asked: ALFRED answers HTTP
    400 ("the series does not exist in ALFRED") for any ``units`` request dated BEFORE the floor —
    measured 2026-10-21 for CPIAUCSL (1972-07-21), M2SL (1980-02-08) and PCEPILFE (2000-08-01); only
    PCEPILFE's floor is inside the backfill's range, which is why only it failed (9 dates as
    ``HTTP_ERROR``). Knowing the floor, no vintage beneath it is probed — it is absent by definition
    — so the 400 is never provoked and a pre-floor observation reaches its true classification,
    ``vintage_archive_floor``. A 400 that DOES arrive remains a genuine ``HTTP_ERROR``: telling this
    one from another would take reading the body's message, which the failure discipline forbids.

    EMPTY IS AN ANSWER. No row for the date at any vintage — a weekend, a holiday, a date the series
    never carried, or one that has not happened yet — is ``{"unit": ...}``.

    THE KEY. ``api_key`` is a required KEYWORD-ONLY constructor argument, never read from
    any process state. It appears in the request URL handed to the getter and nowhere else: not in
    :meth:`_url`, not in a payload, not in a failure. A failure carries a stable class and NO message,
    URL or exception text (PBG-SEC-002), so the key cannot leave through an error.

    BOUNDED. ``timeout_seconds`` is a TOTAL deadline across every GET one fetch makes, each GET is
    given only the time left, and a budget that runs out is ``TIMEOUT``, never a partial answer.
    Courtesy pacing between observations is the backfill driver's call and is not done here.
    """

    __slots__ = ("_series", "_transformation", "_observation_date", "_api_key", "_floors")
    adapter_id = "cd.ingest.fred_vintage_rest.v1"
    response_schema = VINTAGE_RESPONSE_SCHEMA

    def __init__(self, series: str, transformation: Union[str, None], observation_date: str, *,
                 api_key: str, archive_floors: Any, **kw: Any) -> None:
        super().__init__(**kw)
        if not isinstance(series, str) or not _SERIES_ID.match(series):
            raise ValueError("series id is not in the permitted shape")
        if transformation is not None and (
            not isinstance(transformation, str) or not _TRANSFORMATION.match(transformation)
        ):
            raise ValueError("transformation is not in the permitted shape")
        if not isinstance(api_key, str) or not _API_KEY.fullmatch(api_key):
            raise ValueError("api key is not in the permitted shape")  # never echo what was given
        if not (callable(getattr(archive_floors, "floor", None))
                and callable(getattr(archive_floors, "vintages", None))):
            # Required, with no default: an adapter that can be built without the archive-floor
            # test is the 83-values defect waiting to be rebuilt. See :class:`FredArchiveFloors`.
            raise ValueError("archive_floors must provide .floor and .vintages(series, timeout, getter)")
        date.fromisoformat(observation_date)  # a date we cannot read is not one we may ask for
        self._floors = archive_floors
        self._series = series
        self._transformation = transformation
        self._observation_date = observation_date
        self._api_key = api_key

    def _query(self, realtime_start: Union[str, None], realtime_end: Union[str, None]) -> list:
        parts = [("series_id", self._series), ("observation_start", self._observation_date),
                 ("observation_end", self._observation_date), ("file_type", "json")]
        if self._transformation:
            parts.append(("units", self._transformation))
        if realtime_start is not None:
            parts += [("realtime_start", realtime_start), ("realtime_end", realtime_end)]
        return parts

    def _url(self) -> str:
        """The host-declaring URL, WITHOUT the credential. The fetch asks :meth:`_request_url`.

        It exists so this adapter's egress host can be read off it the way every other adapter's is,
        by whatever registers it. Keeping the key out of it is what lets that reading be logged,
        compared and asserted on without a credential in the line.
        """
        return FRED_API_BASE + "?" + urllib.parse.urlencode(self._query(None, None))

    def _request_url(self, realtime_start: str, realtime_end: str) -> str:
        parts = self._query(realtime_start, realtime_end) + [("api_key", self._api_key)]
        return FRED_API_BASE + "?" + urllib.parse.urlencode(parts)

    def _acquire(self, timeout_seconds: float) -> dict:
        observed = date.fromisoformat(self._observation_date)
        today = self._clock().date()
        if observed > today:
            # Nothing can have published an observation that has not happened. Refused
            # rather than searched for in an empty window.
            return {"malformed": "observation_date"}

        deadline = time.monotonic() + timeout_seconds
        spent = [0]

        def get(realtime_start: date, realtime_end: date) -> str:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AdapterFetchError("TIMEOUT")
            spent[0] += 1
            if spent[0] > MAX_VINTAGE_PROBES:
                raise AdapterFetchError("VINTAGE_SEARCH_EXHAUSTED")
            url = self._request_url(realtime_start.isoformat(), realtime_end.isoformat())
            return require_json_body(self._getter(url, remaining, self._headers()))

        # The series' archive floor, asked BEFORE any observation GET: the transformed path needs it
        # to know which vintages it may not probe, and both paths need it to know which answer is a
        # restatement. One GET per series for the life of ``self._floors`` (see FredArchiveFloors).
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AdapterFetchError("TIMEOUT")
        floor = self._floors.floor(self._series, remaining, self._getter)
        if floor is None:
            return {"malformed": "archive_floor_unreadable"}

        if self._transformation is None:
            return self._first_publication_in_one_get(get, observed, today, floor)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AdapterFetchError("TIMEOUT")
        vintages = self._floors.vintages(self._series, remaining, self._getter)
        if vintages is None:
            return {"malformed": "vintage_list_unreadable"}
        return self._first_publication_by_scan(get, observed, today, floor, vintages)

    def _first_publication_in_one_get(self, get: Callable[..., str], observed: date,
                                      today: date, floor: date) -> dict:
        body = get(date.fromisoformat(FRED_REALTIME_FLOOR), today)
        found = parse_fred_rest_first_publication(
            body, self._unit, self._observation_date, realtime_end=today.isoformat())
        if "vintage_date" not in found:
            return found  # EMPTY, or MALFORMED / an unreadable value for the closed schema
        vintage = date.fromisoformat(found["vintage_date"])
        if vintage < observed:
            # The earliest vintage FRED holds for this observation predates the observation: the
            # premise of the search window is false for this series. Refused, never approximated.
            return {"malformed": "vintage_floor"}
        if vintage == floor:
            # First KEPT here, not first published here: see FredArchiveFloors. Named before the
            # ceiling because it is the cause; a restatement a decade late is both, and this is why.
            return {"malformed": "vintage_archive_floor"}
        if (vintage - observed).days > MAX_FIRST_PUBLICATION_LAG_DAYS:
            return {"malformed": "vintage_too_distant"}
        return found

    def _first_publication_by_scan(self, get: Callable[..., str], observed: date, today: date,
                                   floor: date, vintages: list) -> dict:
        """The transformed path: the EARLIEST vintage that serves a value, found by SCANNING.

        WO-1.17 Fault 4. This used to bisect, which is sound only if "serves a value" never goes
        true-then-false as the vintage advances. It does: ``PCEPILFE`` ``pc1`` for 2000-10-01 is
        served from vintage 2000-11-30 and is ``.`` again at 2004-01-02 and 2004-01-04, so the
        bisection landed in a gap, converged on 2004-01-05 and refused a genuine first publication
        as ``vintage_too_distant``. A scan walks the series' REAL vintage dates in order from the
        observation (asked once per series, :meth:`FredArchiveFloors.vintages`) and stops at the first
        that serves, so a later gap cannot be mistaken for the answer. It is also cheaper: a first
        publication is found in a few probes, where the bisection paid 13-15 per date.

        The window is the ceiling made literal: only vintages within
        :data:`MAX_FIRST_PUBLICATION_LAG_DAYS` of the observation are probed, so a value first served
        later is exactly the ``vintage_too_distant`` the arithmetic ceiling refused. Today's vintage is
        probed first, as before: absent there means no vintage ever served it (EMPTY), served there
        but nowhere in the window means served too late.
        """
        units = self._transformation
        memo: dict = {}

        def probe(vintage: date) -> dict:
            if vintage not in memo:
                memo[vintage] = parse_fred_rest_at_vintage(
                    get(vintage, vintage), self._unit, self._observation_date, units,
                    vintage.isoformat())
            return memo[vintage]

        state = _vintage_state(probe(today))
        if state == _UNREADABLE:
            return probe(today)
        if state == _ABSENT:
            return {"unit": self._unit}  # no vintage ever served it: EMPTY

        # The floor, VERIFIED rather than assumed: the day before the observation existed.
        # Archive start later than that: nothing before the archive can be asked (HTTP 400) and
        # nothing before it can have served the figure, so the scan begins after the floor.
        earliest = observed
        beneath = observed - timedelta(days=1)
        if beneath >= floor:
            state = _vintage_state(probe(beneath))
            if state == _UNREADABLE:
                return probe(beneath)
            if state == _SERVED:
                return {"malformed": "vintage_floor"}
        else:
            # Served AT the floor means the first serving vintage IS the floor (nothing earlier
            # exists): a restatement, decided in this one probe.
            state = _vintage_state(probe(floor))
            if state == _UNREADABLE:
                return probe(floor)
            if state == _SERVED:
                return {"malformed": "vintage_archive_floor"}
            earliest = floor + timedelta(days=1)

        ceiling = observed + timedelta(days=MAX_FIRST_PUBLICATION_LAG_DAYS)
        for vintage in vintages:
            if vintage < earliest or vintage == floor:
                continue
            if vintage > ceiling:
                break
            payload = probe(vintage)
            state = _vintage_state(payload)
            if state == _UNREADABLE:
                return payload
            if state == _SERVED:
                return payload
        # Served today, but at no vintage inside the window: first served too LATE to be a
        # publication event.
        return {"malformed": "vintage_too_distant"}


class CboeAdapter(_BaseAdapter):
    """``cdn-api.cboe.com`` ``{index}_History.csv`` — one static file, read two ways.

    TWO QUESTIONS, ONE URL, AND THE SECOND ONE IS OPT-IN (WO-1.16). With
    ``observation_date`` left at ``None`` — which is every live call, since
    ``ingestion.catalog.build_adapter`` has no argument that could set it — this asks "what
    is this index at now?" and behaves EXACTLY as it always has: :func:`parse_cboe_csv`, the
    last row. With ``observation_date`` set, which only
    ``ingestion.backfill_adapters.build_backfill_adapter`` does, it asks "what did this index
    close at on D?" and the body is read by :func:`parse_cboe_csv_for_date`, which matches D
    exactly and never by position.

    ONLY THE PARSE CHANGES, AND THAT IS THE WHOLE POINT OF THE SHAPE. :class:`FredAdapter`'s
    dated mode changes three things together — the URL gains ``cosd``/``coed``, the parser
    changes, and a 404 becomes EMPTY. Here exactly one of those three is available:

    * **the URL cannot change.** ``cdn-api.cboe.com`` honours NO date-windowing parameter:
      eight spellings plus two negative controls each returned a body BYTE-IDENTICAL to the
      bare URL's, same SHA-256 (probed 2026-10-15, ``evidence/wo116_cboe_probe.json``). So
      :meth:`_url` is untouched and there is nothing for a dated request to ask for;
    * **a 404 stays a FAILURE in both modes,** where ``FredAdapter`` translates it for a
      dated request. That carve-out exists because FRED answers "no observation on this date"
      with a 404 — a real answer to a windowed question. Nothing here is windowed: the only
      404 this URL can give is "no history file for this index", which is a fetch failure
      whichever question was asked. A date the index has no session for is an ABSENT ROW in a
      body that arrived fine, which :func:`parse_cboe_csv_for_date` returns as EMPTY;
    * **the parse must change,** and it is the one thing that can. Every dated request gets a
      body whose LAST row is this week's close, so reading by position would answer a 2015
      backfill with today's number under a 2015 key, every time.

    WHY THE KWARG EXISTS AT ALL, GIVEN THAT IT CANNOT REACH THE URL. The alternative
    considered was to leave this class alone and have the backfill driver call
    :func:`parse_cboe_csv_for_date` on the side — and it is the wrong shape, not merely the
    less tidy one: :meth:`_BaseAdapter.fetch` is the contract (``_acquire`` -> ``_parse`` ->
    ``as_of_for`` -> the closed schema), ``crash_detector.collectors.collect`` drives it, and
    a driver that parsed a body itself would be holding a payload that never passed the
    adapter's own ``response_schema``. It would also need the body, which only ``_acquire``
    has. So the kwarg: the question an adapter answers is the adapter's own state, and here
    it happens to be answerable without touching the request.

    ``observation_date`` is KEYWORD-ONLY, matching :class:`FredAdapter`, and is parsed at
    construction — not because it is interpolated anywhere, but because an unreadable date
    would match no row and report EMPTY, which would be this adapter saying "Cboe has no
    session on that date" about a string that was never a date.
    """

    __slots__ = ("_index", "_column", "_observation_date")
    adapter_id = "cd.ingest.cboe_history_csv.v1"

    def __init__(self, index: str, column: str, *,
                 observation_date: Union[str, None] = None, **kw: Any) -> None:
        super().__init__(**kw)
        if observation_date is not None:
            date.fromisoformat(observation_date)
        self._index = index
        self._column = column
        self._observation_date = observation_date

    def _url(self) -> str:
        return cboe_history_url(self._index)

    def _parse(self, body: str) -> dict:
        if self._observation_date is None:
            return parse_cboe_csv(body, self._column, self._unit)
        return parse_cboe_csv_for_date(body, self._column, self._unit, self._observation_date)


#: WO-1.20. The relative page a LIVE history read asks for, keyed on the rows the ingredient
#: declares. ``range=2y`` ANSWERS 503 DATED CLOSES AND ``range=10y`` ANSWERS 2515 (measured on
#: ``GC=F``, 2026-10-17, ``evidence/wo120_yahoo_range_probe.json``), so the flat ``2y`` this
#: adapter asked for from WO-1.2b until now CANNOT serve ``yahoo.GC=F.history``'s 2600 rows: it
#: would answer a fifth of them, and the catalog would be declaring a depth nothing could
#: deliver. ``gold_real_rate_cross`` would still have read a number — 503 shared dates clears the
#: 421 its percentile needs — which is exactly why this is a declaration and not an incident: the
#: dial would have gone on reporting a figure whose history base was two years while both its own
#: catalog row and ``SUBSTITUTED_FEEDS`` said ten.
#:
#: THE BOUNDARY IS THE LARGEST REQUEST ``2y`` IS ALREADY TRUSTED WITH, NOT THE PAGE'S MEASURED
#: SIZE, and the difference is deliberate. ``yahoo.BIZD.adj`` declares 520 rows against a page
#: that answers ~503, because its 520 MEANS "the whole 2y page" (its catalog comment says so).
#: Reading the boundary off the measurement instead would quietly escalate that row — and only
#: that row — to a 10y request, changing a live ingredient's question for no reason this WO has.
#: So every ingredient that existed before WO-1.20 keeps the page it has always asked for, and
#: only a request a 2y page cannot cover AT ALL escalates.
#:
#: ``10y`` AND NOT ``max``, AND THAT IS MEASURED RATHER THAN PREFERRED. ``max`` is in the
#: endpoint's own ``meta.validRanges`` and looks like the obvious way to ask for "everything",
#: but asked with ``interval=1d`` it answered 269 BARS SPANNING 2000-09-01 to 2026-10-16 — i.e.
#: it silently coarsened to MONTHLY and handed back FEWER rows than ``2y`` does, while reporting
#: a 26-year span (same probe, case ``range=max``). A caller trusting the span would have built a
#: ten-year correlation out of monthly prints. ``10y`` returns true daily bars, so it is what is
#: asked for.
YAHOO_SHORT_PAGE_MAX_ROWS = 520


class YahooChartAdapter(_BaseAdapter):
    """Yahoo Finance public chart endpoint (the provider OpenBB's equity path wraps).

    UNOFFICIAL: no SLA, no licence, rate-limited (HTTP 429 under bursts). Its failures are
    recorded like any other; none is defaulted.

    TWO QUESTIONS, ONE ENDPOINT, AND THE SECOND ONE IS OPT-IN (WO-1.16). With
    ``observation_date`` left at ``None`` — which is every live call, since
    ``ingestion.catalog.build_adapter`` has no argument that could set it — this asks "what is
    this symbol at now?" and is the adapter it has always been: ``range=10d`` (for a history read
    the page :data:`YAHOO_SHORT_PAGE_MAX_ROWS` selects, ``2y`` or ``10y``),
    :func:`parse_yahoo_chart`, the last bar, the same failure handling. With
    ``observation_date`` set it asks "what did this symbol close at on D?", and exactly two
    things change together:

    * the request REPLACES ``range`` with an absolute ``period1``/``period2`` window;
    * the body is read by :func:`parse_yahoo_chart_for_date`, which matches D exactly.

    REPLACES, NOT APPENDS, AND THAT IS MEASURED RATHER THAN PREFERRED. Given both in one URL,
    ``range`` WINS: the period window is silently ignored and the whole relative body comes
    back (probed 2026-10-15, ``evidence/wo116_yahoo_window_probe.json``,
    ``q6_range_and_period_together``: ``range=2y`` plus a one-day window for 2015-06-08
    answered 502 bars ending at this morning's). An implementation that appended the window
    would ask for a 2015 date and be handed two years of bars ending today — the body
    :func:`parse_yahoo_chart_for_date`'s exact-key match exists to make harmless, which is no
    reason to build the request that produces it.

    THE WINDOW IS THE WHOLE UTC DAY, AND THE OBVIOUS ENCODING IS THE WRONG ONE.
    ``period1``/``period2`` are Unix seconds bounding an absolute window, and a ``1d`` bar is
    stamped not at midnight but at the exchange's session OPEN — 1433770200 is
    2015-06-08T13:30Z, a US listing on summer time, 14:30Z the same session in winter. So the
    window has to CONTAIN that instant, and the whole UTC day of D contains it under either
    offset: ``period1`` = 00:00:00Z of D, ``period2`` = 00:00:00Z of D+1 LESS ONE SECOND =
    23:59:59Z of D. It is derived as "the next midnight, minus a second" rather than written
    as "plus 86399" because that is the bound being expressed — a UTC day is always 86400
    POSIX seconds so the two agree, but the arithmetic should say what it means. The encoding
    a caller reaches for first — ``period1 == period2 ==`` midnight of D, a zero-width point —
    returns ZERO BARS for a real trading day (``q2_window_one_day_zero_width``, measured on
    three symbols), which is an off-by-one that would look exactly like a market holiday. A
    half-open ``[00:00:00Z of D, 00:00:00Z of D+1)`` would do as well on the evidence; the
    inclusive 23:59:59Z bound is the one actually probed, so it is the one built.

    A 400 IS A FAILURE, NOT AN EMPTY — THE OPPOSITE OF WHAT ``FredAdapter`` DOES, DELIBERATELY.
    :class:`FredAdapter` translates an ``HTTP_ERROR``/404 into EMPTY for a dated request. This
    adapter translates nothing, and the asymmetry is the decision rather than an omission:

    * ``FredAdapter`` NEEDED that carve-out. FRED answers a one-day window on a real gap date
      — a Saturday inside a business-daily series' span — with ``404`` and an HTML error page,
      NOT with ``200`` and a header and no rows (``evidence/wo115_fred_window_probe.json``,
      ``extra_window_on_gap_date``). There, the 404 IS "no observation on this date", and
      without the translation every ordinary non-trading day would be a fetch failure.
    * Yahoo has no such need, because its gap day is already representable: a weekend, a
      holiday, or any date the symbol did not print on is ``200`` with the bar arrays absent,
      which :func:`parse_yahoo_chart_for_date` reports as EMPTY with no special-casing
      (``q3_window_on_non_trading_day``, ``q3_window_on_market_holiday``). Nothing about a real
      gap date is bought by translating a 400.
    * So a 400 here is reachable ONLY by an IMPOSSIBLE WINDOW — entirely before the symbol's
      first trade, entirely in the future, or reversed. All three were probed, all three are a
      clean 400 whose JSON body names the rejected bounds (``q4_*``, ``q5_window_reversed``).
      None of them is the source saying anything about the date asked for; each is the REQUEST
      being wrong, i.e. a caller defect. Translated to EMPTY it would be recorded as "the
      symbol did not print that day", indistinguishable from a weekend, and a driver whose date
      arithmetic ran ahead of the clock could walk a whole range logging quiet EMPTYs for dates
      that have not happened. Left as a failure it is loud, counted, retried under the retry
      policy and recorded as a fetch failure — which is also how a 404 behaves here in BOTH
      modes, the way :class:`CboeAdapter` keeps its 404 a failure in both of its own.
    * The before-first-trade case is the one arguable the other way: "the symbol did not exist,
      so there was nothing to print" does sound like EMPTY. It stays a failure on WO-1.14's
      reason — a date before an ingredient's history is a date a backfill must not be asking
      for, and the place to stop is the driver's floor, REFUSED unfetched (WO-1.15 does exactly
      that with ``STABILITY_MEASURED_FROM``), not a translation here that would make every
      out-of-range date look like a quiet weekend.

    Concretely that decision is the ABSENCE of an ``_acquire`` override: the base class's one
    bounded GET raises :class:`AdapterFetchError` and nothing here catches it, in either mode.

    A DATED REQUEST FOR ``adjclose`` IS REFUSED AT CONSTRUCTION, not answered with ``close``.
    ``field="adjclose"`` is deliberate for two live ingredients (``ingestion/catalog.py``:
    BIZD's printed-price drawdown counts every ex-dividend drop as stress, and the breadth
    sample uses the adjusted close like the legacy tell), while
    :func:`parse_yahoo_chart_for_date` reads ``close`` only — because a backfilled ``adjclose``
    has no point-in-time meaning at all: it drifts retroactively with every dividend and split,
    for every date before the event, forever (PID.md, WO-1.16 scope correction, and the
    reason ``ingestion.vintage.NO_REVISION_MECHANISM_COLUMNS`` admits ``close`` and ``""``
    for this kind and NOT ``adjclose``). THIS RAISE IS WHY THAT IS A REFUSAL RATHER THAN A
    PREFERENCE: ``ingestion.backfill_adapters.build_backfill_adapter`` routes the ``yahoo``
    kind with no column check of its own — deliberately, so the rule has one home — so an
    ``adjclose`` ingredient reaching it is refused HERE, before a URL exists.
    Answering such a request with the UNADJUSTED close would make this adapter report a
    different QUANTITY than the live collector stores under the same ingredient — the WO-1.14
    defect class, by field instead of by date. Whether ``adjclose`` may be backfilled at all is
    an open question with an owner; until it is settled, the combination raises rather than
    being resolved quietly in the wrong direction.

    ``observation_date`` is KEYWORD-ONLY, matching :class:`FredAdapter` and
    :class:`CboeAdapter`: ``history`` and ``field`` are positional at existing call sites, and
    a date arriving where a row count belongs would be a silent change of question. It is
    parsed at construction — a string we cannot read as a date is not one we may convert into a
    window.
    """

    __slots__ = ("_symbol", "_history", "_field", "_observation_date")
    adapter_id = "cd.ingest.yahoo_chart.v1"

    def __init__(self, symbol: str, history: int = 0, field: str = "close", *,
                 observation_date: Union[str, None] = None, **kw: Any) -> None:
        super().__init__(**kw)
        if observation_date is not None:
            date.fromisoformat(observation_date)
            if field != "close":
                raise ValueError("a dated Yahoo fetch reads close only; adjclose has no "
                                 "point-in-time meaning (PID.md WO-1.16 scope correction)")
        self._symbol = symbol
        self._history = history
        self._field = field
        self._observation_date = observation_date

    def _headers(self) -> Mapping[str, str]:
        # Yahoo answers 429 to urllib's default agent and 200 to an identified browser-style
        # one; FRED does the opposite (see http_get). Per-adapter, declared, not global — and
        # the string itself is YAHOO_USER_AGENT because the calendar reader must send the same.
        return {"User-Agent": YAHOO_USER_AGENT}

    def _url(self) -> str:
        # Both modes are yahoo_chart_url's (WO-1.17's lift), which is where the window
        # arithmetic and the one-mechanism-per-request refusal are argued. A dated fetch is the
        # single-day case of the absolute window: start == end == the date asked for.
        if self._observation_date is None:
            if not self._history:
                rng = "10d"
            else:
                rng = "2y" if self._history <= YAHOO_SHORT_PAGE_MAX_ROWS else "10y"
            return yahoo_chart_url(self._symbol, relative_range=rng)
        return yahoo_chart_url(self._symbol, start=self._observation_date,
                               end=self._observation_date)

    def _parse(self, body: str) -> dict:
        if self._observation_date is None:
            return parse_yahoo_chart(body, self._unit, self._history, today=self._clock().date(), field=self._field)
        return parse_yahoo_chart_for_date(body, self._unit, self._observation_date)


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
