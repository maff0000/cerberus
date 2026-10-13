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

import redis

from crash_detector.collectors.adapter import AdapterFetchError, FetchedResponse

__all__ = [
    "RESPONSE_SCHEMA",
    "FredAdapter",
    "CboeAdapter",
    "YahooChartAdapter",
    "MultplShillerAdapter",
    "LbmaGoldAdapter",
    "HermesCandleAdapter",
    "ManualEntryAdapter",
    "LBMA_USER_AGENT",
    "HERMES_PEER",
    "HERMES_CANDLE_CONTRACT",
    "HERMES_CANDLE_CONTRACT_VERSION",
    "hermes_latest_key",
    "parse_hermes_candle",
    "parse_lbma_gold",
    "parse_fred_csv",
    "parse_cboe_csv",
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
    """

    __slots__ = ("_series", "_transformation", "_history")
    adapter_id = "cd.ingest.fred_csv.v1"

    def __init__(self, series: str, transformation: Union[str, None], history: int = 0, **kw: Any) -> None:
        super().__init__(**kw)
        self._series = series
        self._transformation = transformation
        self._history = history

    def _url(self) -> str:
        suffix = f"&transformation={self._transformation}" if self._transformation else ""
        return f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={self._series}{suffix}"

    def _parse(self, body: str) -> dict:
        column = self._series + (f"_{self._transformation.upper()}" if self._transformation else "")
        return parse_fred_csv(body, column, self._unit, self._history)


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
