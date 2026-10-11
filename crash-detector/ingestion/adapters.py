"""Source adapters for the public feeds the ratified mapping declares.

Each adapter implements :class:`crash_detector.collectors.adapter.SourceAdapter`: one
bounded ``fetch``, a declared closed ``response_schema``, and ``is_empty``. Parsing is done
by pure functions (``parse_*``) so it is tested offline against recorded fixtures.

NOTHING HERE COMPUTES AN INDICATOR. A payload carries what the source said — a date, a
number, a unit — and, for the one source whose declared calculation needs a price history
(the 200-day average), the raw closes. Ratios, spreads, percentiles and scores belong to
the engine's executor behind the raw/dial boundary.

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
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from typing import Any, Callable, Mapping, Union

from crash_detector.collectors.adapter import AdapterFetchError, FetchedResponse

__all__ = [
    "RESPONSE_SCHEMA",
    "FredAdapter",
    "CboeAdapter",
    "YahooChartAdapter",
    "MultplShillerAdapter",
    "parse_fred_csv",
    "parse_cboe_csv",
    "parse_yahoo_chart",
    "parse_multpl_table",
    "as_of_for",
]

#: Hard ceiling on a response body. A hostile or broken source cannot make us buffer
#: without bound. Multpl's full monthly table is the largest legitimate body (~150 KB).
MAX_BODY_BYTES = 4_000_000

#: Ceiling on the optional raw close history carried for the 200-day average.
MAX_HISTORY = 400

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

    Both are conservative in the direction that matters: neither can make old data look
    newer than the period it covers.
    """
    day = date.fromisoformat(observation_date)
    if rule == "month_end":
        day = day.replace(day=calendar.monthrange(day.year, day.month)[1])
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


def parse_fred_csv(text: str, column: str, unit: str) -> dict:
    """Latest non-missing row of a ``fredgraph.csv`` body. FRED writes ``.`` for no data.

    ``column`` is the expected value-column header: the series id, or ``<ID>_<TRANSFORM>``
    (e.g. ``M2SL_PC1``) when a server-side transformation was requested. A body whose header
    is not exactly what was asked for is MALFORMED, never read.
    """
    lines = text.strip().splitlines()
    if not lines or lines[0].split(",")[0] != "observation_date" or len(lines[0].split(",")) != 2:
        return {"malformed": "header"}  # no "unit": fails the closed schema -> MALFORMED
    if lines[0].split(",")[1] != column:
        return {"malformed": "series"}
    for line in reversed(lines[1:]):
        cells = line.split(",")
        if len(cells) != 2 or cells[1] in ("", "."):
            continue
        return {"unit": unit, "observation_date": cells[0], "value": _number_or_token(cells[1])}
    return {"unit": unit}  # a conforming body with no observation: EMPTY


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


def parse_yahoo_chart(text: str, unit: str, history: int = 0, today: Union[date, None] = None) -> dict:
    """Latest daily close of a Yahoo v8 chart body; optionally the last ``history`` closes.

    ``today``: when given, any bar dated on or after it is DROPPED. During a session the last
    bar is the live price, not a close, and the store keeps the first value admitted for a
    period (Auditor finding 2, WO-1.2b), so a partial bar would be locked in as the close.
    """
    try:
        result = json.loads(text)["chart"]["result"][0]
        stamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
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


def parse_multpl_table(text: str, unit: str) -> dict:
    """First (= most recent) row of multpl's ``/table/by-month`` page."""
    match = _MULTPL_ROW.search(text)
    if match is None:
        return {"malformed": "shape"}  # no row found is a page we do not understand, not "empty"
    try:
        observed = datetime.strptime(html.unescape(match.group(1)), "%b %d, %Y").date().isoformat()
    except ValueError:
        return {"malformed": "date"}
    return {"unit": unit, "observation_date": observed, "value": _number_or_token(match.group(2))}


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

    def fetch(self, *, timeout_seconds: float) -> FetchedResponse:
        body = self._getter(self._url(), timeout_seconds, self._headers())
        payload = self._parse(body)
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
    """

    __slots__ = ("_series", "_transformation")
    adapter_id = "cd.ingest.fred_csv.v1"

    def __init__(self, series: str, transformation: Union[str, None], **kw: Any) -> None:
        super().__init__(**kw)
        self._series = series
        self._transformation = transformation

    def _url(self) -> str:
        suffix = f"&transformation={self._transformation}" if self._transformation else ""
        return f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={self._series}{suffix}"

    def _parse(self, body: str) -> dict:
        column = self._series + (f"_{self._transformation.upper()}" if self._transformation else "")
        return parse_fred_csv(body, column, self._unit)


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

    __slots__ = ("_symbol", "_history")
    adapter_id = "cd.ingest.yahoo_chart.v1"

    def __init__(self, symbol: str, history: int = 0, **kw: Any) -> None:
        super().__init__(**kw)
        self._symbol = symbol
        self._history = history

    def _headers(self) -> Mapping[str, str]:
        # Yahoo answers 429 to urllib's default agent and 200 to an identified browser-style
        # one; FRED does the opposite (see http_get). Per-adapter, declared, not global.
        return {"User-Agent": "Mozilla/5.0 (compatible; cerberus-ingest/1.0)"}

    def _url(self) -> str:
        quoted = self._symbol.replace("^", "%5E").replace("=", "%3D")
        rng = "2y" if self._history else "10d"
        return f"https://query1.finance.yahoo.com/v8/finance/chart/{quoted}?range={rng}&interval=1d"

    def _parse(self, body: str) -> dict:
        return parse_yahoo_chart(body, self._unit, self._history, today=self._clock().date())


class MultplShillerAdapter(_BaseAdapter):
    """multpl.com's Shiller P/E monthly table (declared source: ``multpl/Shiller``)."""

    __slots__ = ()
    adapter_id = "cd.ingest.multpl_shiller_pe.v1"

    def _url(self) -> str:
        return "https://www.multpl.com/shiller-pe/table/by-month"

    def _parse(self, body: str) -> dict:
        return parse_multpl_table(body, self._unit)
