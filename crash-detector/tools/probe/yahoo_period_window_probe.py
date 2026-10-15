#!/usr/bin/env python3
"""THE YAHOO CHART WINDOW PROBE — does ``period1``/``period2`` WINDOW, CLAMP, REFUSE, or get IGNORED?

    PYTHONPATH=src:. python3 tools/probe/yahoo_period_window_probe.py --out evidence/<file>.json

WHY THIS EXISTS (WO-1.16). ``ingestion.adapters.YahooChartAdapter._url`` asks for
``range=2y&interval=1d`` (or ``10d`` with no history) — a RELATIVE range anchored on now —
and ``parse_yahoo_chart`` then reads the LAST bar of whatever came back. For a backfill of a
date years ago that is the same defect WO-1.15 found in plain FRED: a perfectly good reading
of the WRONG period. The candidate fix is an ABSOLUTE window — the v8 chart endpoint is
widely described outside this repo as accepting ``period1``/``period2`` as Unix timestamps in
place of ``range`` — and this file measures whether that is true of the real endpoint, and
what it does at the edges, BEFORE any adapter is written against it.

THE THING THAT MUST NOT BE ASSUMED, stated as the published claim it is. Public write-ups of
this endpoint (e.g. the ``yahoo-finance-api2`` package's notes, read 2026-10-15) say outright:
"values below the initial trading date will be rounded up to the initial trading date, and
values greater than the last trading date will be rounded down to the most recent timestamp
available." If that is so, Yahoo CLAMPS exactly the way ``alfred.stlouisfed.org`` was measured
to (``evidence/wo114_alfred_probe.json``) — and a window placed before a symbol's listing
would answer with the symbol's FIRST REAL BAR while the caller believes it asked about 1983.
Reading "the last bar" out of that is how a backfill forges a historical print. The same
write-ups also say ``range`` and ``period1``/``period2`` are mutually exclusive, which matters
because the adapter builds ``range`` today and an implementation that merely APPENDS the
window would be relying on an untested precedence. A remembered doc is not evidence. So this
file asks the real endpoint and writes down the answer.

IT IS A PROBE, NOT A GATE, AND IT WRITES NO ADAPTER CODE. It opens sockets to a third party,
so its verdict is not reproducible offline and can never be a register check (CD-PL-F48). It
records what the server said; a human reads that and decides what the adapter does. This
round deliberately changes nothing under ``ingestion/``.

SCOPE — PLAIN ``close`` SYMBOLS ONLY. ``PID.md``'s WO-1.16 scope correction (2026-10-15) rules
``yahoo.BIZD.adj`` and the breadth sample OUT: those are wired ``column="adjclose"`` on
purpose, ``adjclose`` has no vintage mechanism at all, and a point-in-time backfill of them is
not a windowing question. The symbols here are the plain-``close`` ones from
``ingestion/catalog.py`` and the probe never asks for ``adjclose``.

HOW THE EPOCH BOUNDS ARE DERIVED, since this is the step a caller gets wrong. Yahoo's daily
bars are NOT stamped at midnight: a ``1d`` bar carries the epoch second of the regular
session's OPEN in the exchange's own timezone (09:30 America/New_York for a US listing =
13:30Z under EDT, 14:30Z under EST). A window for "calendar day D" is therefore asked as
``period1`` = 00:00:00Z of D and ``period2`` = 23:59:59Z of D — the whole UTC day — which
contains that open for any US exchange under either offset. The record does not take that on
faith: every returned stamp is written down three ways (raw epoch, its UTC date, and its date
under the ``meta.gmtoffset`` the SAME response declares), so the convention is visible rather
than argued, and ``parse_yahoo_chart``'s own ``datetime.fromtimestamp(stamp, tz=utc).date()``
is the UTC column.

WHAT IT ASKS, PER SYMBOL
------------------------
``baseline`` — the UNWINDOWED request, byte-for-byte the URL ``YahooChartAdapter._url`` builds
today. Establishes the response's real shape and ``meta.firstTradeDate``, so the "impossible"
window below is DERIVED from what the server says the symbol holds rather than typed in from
memory.

``Q1`` — does ``period1``/``period2`` work AT ALL, and is the shape the one
``parse_yahoo_chart`` already requires (``chart.result[0].timestamp`` and
``.indicators.quote[0].close``)? Asked with a multi-day window, because a window is only
demonstrably APPLIED if a wider one returns wider; and answered twice over — structurally
(which keys are present) and by CALLING the repo's real ``parse_yahoo_chart`` on the body and
recording its verdict dict. The parser is imported read-only; nothing under ``ingestion/`` is
touched.

``Q2`` — a ONE-DAY window on a real trading day: exactly one bar, more, or none? Plus the
zero-width variant (``period1 == period2``, the bound a caller derives when they forget the
session offset), because "one day" has two plausible encodings and only one of them can be
the recommendation.

``Q3`` — a one-day window on a NON-TRADING day, both kinds: a weekend DERIVED from the
multi-day body above (not assumed — which calendar days a symbol trades is the server's to
say) and a market holiday derived the same way from a body spanning the first week of July.
Empty, an error, or a NEIGHBOURING bar? This is the case that decides whether a future parser
may trust "the only bar in the window" or whether exact-date matching is mandatory.

``Q4`` — a window wholly BEFORE the symbol's first trade, one day and one year of it, placed
``IMPOSSIBLE_YEARS`` before ``meta.firstTradeDate``. Clamp (the published claim), refusal,
empty, or the whole unrelated series? This is FRED's dangerous case from WO-1.15 asked of a
different endpoint. Then the two cases that single case CANNOT tell apart on its own: a window
SPANNING the first trade from outside it (clamp-to-start answers with the real first bars, a
flat refusal answers with neither) and a window a year in the FUTURE (the published claim's
mirror half — "rounded down to the most recent timestamp available" — which, if true, would
hand a clock-skewed caller today's bar wearing next year's date).

``Q5`` — ``period2`` before ``period1``: a malformed window's failure shape, measured rather
than guessed, because a caller computing bounds wrong should fail loudly and not quietly.

``Q6`` — ``range`` AND ``period1``/``period2`` in the same URL. Which wins? The adapter emits
``range`` today, so an implementation that appends rather than REPLACES depends on this
answer, and the published claim that the two are mutually exclusive is not a measurement.

BODIES ARE RECORDED VERBATIM where they fit under :data:`VERBATIM_CAP`, which is every
windowed case of interest. The unwindowed baseline is a 500-bar page, so it is recorded as its
full ``meta`` block, its bar count, its span, its first and last bars and a head/tail of its
dates, with ``truncated`` set.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from typing import Union

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
# ``src`` AND the repo root, in pyproject's own order (``pythonpath = ["src", "."]``): the
# supported import route is PYTHONPATH=src:., and this file is runnable without it.
sys.path[:0] = [os.path.join(_ROOT, "src"), _ROOT]

try:  # read-only: the probe asks the REAL parser whether it can read what the server sent
    from ingestion.adapters import parse_yahoo_chart
except ImportError:  # pragma: no cover - the structural checks below still stand alone
    parse_yahoo_chart = None  # type: ignore[assignment]

HOST = "query1.finance.yahoo.com"
#: The EXACT door ``ingestion.adapters.YahooChartAdapter`` uses: same host, same v8 chart
#: path, no credential of any kind (this endpoint takes none and none exists in this file).
BASE = f"https://{HOST}/v8/finance/chart/"
#: Byte-for-byte ``YahooChartAdapter._headers``: Yahoo answers 429 to urllib's default agent
#: and 200 to an identified browser-style one, so probing with a different agent would be
#: probing a different door.
USER_AGENT = "Mozilla/5.0 (compatible; cerberus-ingest/1.0)"
#: Courtesy gap between requests to an unofficial, unpaid, rate-limiting endpoint.
PACE = 1.2
#: Bodies at or under this are stored verbatim.
VERBATIM_CAP = 20_000
#: Bars/dates kept at each end of a truncated body.
HEAD_TAIL = 4
#: How far before a symbol's first trade the "impossible" window is placed. Ten years is not a
#: boundary-adjacent off-by-one; it is unambiguously outside.
IMPOSSIBLE_YEARS = 10
#: The 5+-years-back week the one-day windows are placed in, and the week whose body the
#: holiday case is derived from. Both are spans, not assertions about which days trade.
TARGET_WEEK = ("2015-06-08", "2015-06-19")
HOLIDAY_WEEK = ("2015-07-01", "2015-07-07")


def _quoted(symbol: str) -> str:
    """The symbol, escaped the way ``YahooChartAdapter._url`` escapes it."""
    return symbol.replace("^", "%5E").replace("=", "%3D")


def _url(symbol: str, rng: Union[str, None] = None,
         period1: Union[int, None] = None, period2: Union[int, None] = None) -> str:
    """The request, built the way the adapter builds it plus/minus the window under test."""
    parts = []
    if rng is not None:
        parts.append(f"range={rng}")
    if period1 is not None:
        parts.append(f"period1={period1}")
    if period2 is not None:
        parts.append(f"period2={period2}")
    parts.append("interval=1d")
    return BASE + _quoted(symbol) + "?" + "&".join(parts)


def _utc_day(day: str) -> tuple[int, int]:
    """``[00:00:00Z, 23:59:59Z]`` of one calendar day, as epoch seconds.

    See the module docstring: a ``1d`` bar is stamped at the exchange's session OPEN, never at
    midnight, so the bounds for "calendar day D" are the whole UTC day — which contains
    13:30Z/14:30Z for a US listing under either DST offset.
    """
    midnight = datetime(*(int(p) for p in day.split("-")), tzinfo=timezone.utc)
    start = int(midnight.timestamp())
    return start, start + 86_399


def _fetch(url: str, timeout: float = 30.0) -> dict:
    """status, content type and the literal body. An HTTP error is an ANSWER, not a failure.

    A 400/404/422 here is one of the outcomes the probe is looking for — "Yahoo refuses this
    window" — so it is recorded with its body rather than raised. Only a transport failure,
    which is an absence of an answer, is reported as an error.
    """
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"http_status": response.status,
                    "content_type": response.headers.get("Content-Type"),
                    "body": response.read(32_000_000).decode("utf-8", "replace")}
    except urllib.error.HTTPError as failure:
        return {"http_status": failure.code,
                "content_type": failure.headers.get("Content-Type") if failure.headers else None,
                "http_error": True,
                "body": failure.read(400_000).decode("utf-8", "replace")}


def _bar_rows(stamps: list, closes: list, gmtoffset: Union[int, None]) -> list:
    """Every bar as ``[epoch, utc_date, exchange_local_date, close]``.

    The UTC column is literally what ``parse_yahoo_chart`` computes. The local column is the
    same stamp shifted by the ``gmtoffset`` THIS RESPONSE declares. Writing both down is how
    the record shows whether the two derivations agree for a given instrument type instead of
    asserting that they do.
    """
    rows = []
    for stamp, close in zip(stamps, closes):
        try:
            moment = datetime.fromtimestamp(stamp, tz=timezone.utc)
        except (OSError, OverflowError, ValueError, TypeError):
            rows.append([stamp, None, None, close])
            continue
        local = (moment + timedelta(seconds=gmtoffset)).date().isoformat() if gmtoffset is not None else None
        rows.append([stamp, moment.date().isoformat(), local, close])
    return rows


def _shape(body: str, unit: str = "usd") -> dict:
    """What the body IS, measured. Nothing here interprets; it records.

    ``parse_yahoo_chart_says`` is the repo's own parser run on this exact body, so Q1's
    "does the shape match what the parser expects" is answered by the parser and not by this
    file's opinion of it. ``last_bar_is`` is recorded separately because the parser reads the
    LAST bar, and on a clamped or ignored window that single value is the forgery.
    """
    out: dict = {"body_bytes": len(body)}
    try:
        document = json.loads(body)
    except ValueError:
        out["json"] = False
        out["body_head"] = body[:1_000]
        return out
    out["json"] = True
    out["top_level_keys"] = sorted(document.keys())
    chart = document.get("chart")
    if not isinstance(chart, dict):
        out["body_verbatim"] = body if len(body) <= VERBATIM_CAP else body[:VERBATIM_CAP]
        return out
    out["chart_keys"] = sorted(chart.keys())
    out["chart_error"] = chart.get("error")  # verbatim: null on success, an object on refusal
    results = chart.get("result")
    if not results:
        out["result_is"] = "null" if results is None else "empty-list"
        out["body_verbatim"] = body if len(body) <= VERBATIM_CAP else body[:VERBATIM_CAP]
        return out
    result = results[0]
    out["result_keys"] = sorted(result.keys())
    meta = result.get("meta") or {}
    out["meta"] = meta  # verbatim, including firstTradeDate/gmtoffset the derivations use
    indicators = result.get("indicators") or {}
    out["indicator_keys"] = sorted(indicators.keys())
    quote = (indicators.get("quote") or [{}])[0]
    out["quote_keys"] = sorted(quote.keys()) if isinstance(quote, dict) else None
    # The two paths parse_yahoo_chart requires, asked as separate presence questions.
    out["has_timestamp_key"] = "timestamp" in result
    out["has_quote_close_key"] = isinstance(quote, dict) and "close" in quote
    stamps = result.get("timestamp") or []
    closes = (quote.get("close") if isinstance(quote, dict) else None) or []
    out["timestamp_count"] = len(stamps)
    out["close_count"] = len(closes)
    bars = _bar_rows(list(stamps), list(closes), meta.get("gmtoffset"))
    out["bar_count"] = len(bars)
    utc_dates = [row[1] for row in bars]
    out["utc_dates_span"] = [utc_dates[0], utc_dates[-1]] if utc_dates else None
    if len(body) <= VERBATIM_CAP:
        out["bars"] = bars
        out["utc_dates"] = utc_dates
        out["body_verbatim"] = body
        out["truncated"] = False
    else:
        out["bars_head"] = bars[:HEAD_TAIL]
        out["bars_tail"] = bars[-HEAD_TAIL:]
        out["utc_dates_head"] = utc_dates[:HEAD_TAIL]
        out["utc_dates_tail"] = utc_dates[-HEAD_TAIL:]
        out["truncated"] = True
    out["last_bar_is"] = bars[-1] if bars else None
    if parse_yahoo_chart is not None:
        # today=None so NOTHING is dropped: the probe wants the server's bars, not the live
        # loop's partial-bar guard, which is a separate behaviour with its own tests.
        out["parse_yahoo_chart_says"] = parse_yahoo_chart(body, unit, 0, today=None, field="close")
    return out


def _case(name: str, question: str, asks: str, symbol: str, unit: str,
          rng: Union[str, None], window: Union[tuple, None],
          derivation: Union[str, None] = None) -> dict:
    """One request, one record. ``asks`` states in words what this case tells apart."""
    period1, period2 = window if window else (None, None)
    url = _url(symbol, rng, period1, period2)
    record: dict = {"case": name, "question": question, "asks": asks, "range_param": rng,
                    "period1": period1, "period2": period2, "url": url}
    if period1 is not None:
        record["period_bounds_utc"] = [
            datetime.fromtimestamp(period1, tz=timezone.utc).isoformat(),
            datetime.fromtimestamp(period2, tz=timezone.utc).isoformat() if period2 is not None else None,
        ]
    if derivation:
        record["bounds_derivation"] = derivation
    try:
        answer = _fetch(url)
    except (urllib.error.URLError, OSError) as failure:
        record["transport_error"] = f"{type(failure).__name__}: {failure}"
        return record
    record.update({k: v for k, v in answer.items() if k != "body"})
    record["observed"] = _shape(answer["body"], unit)
    return record


def _gap_run(case: dict, start: str, end: str) -> Union[tuple, None]:
    """The first RUN of consecutive calendar dates in ``[start, end]`` with no bar.

    DERIVED from the body this run actually received, never assumed: which calendar days a
    given symbol prints on is the exchange's business and not this file's to declare. Both
    ends are returned so a window can be placed on one non-trading day and across a whole run
    of them — two different questions, the second being the general "window matches nothing".
    """
    observed = case.get("observed", {})
    if "utc_dates" not in observed:
        return None  # body truncated or absent: no derivation available
    present = set(observed["utc_dates"])
    cursor, stop = date.fromisoformat(start), date.fromisoformat(end)
    while cursor <= stop and cursor.isoformat() in present:
        cursor += timedelta(days=1)
    if cursor > stop:
        return None
    first = cursor
    while cursor + timedelta(days=1) <= stop and (cursor + timedelta(days=1)).isoformat() not in present:
        cursor += timedelta(days=1)
    return first.isoformat(), cursor.isoformat()


def _first_trading_day(case: dict, start: str, end: str) -> Union[str, None]:
    """The first calendar date in the span that the server DID return a bar for."""
    dates = case.get("observed", {}).get("utc_dates") or []
    for day in dates:
        if start <= day <= end:
            return day
    return None


def probe_one(symbol: str, unit: str, history: int, full: bool) -> dict:
    """Every case for one symbol, in order, each pacing itself.

    ``full`` runs the whole question set. A non-``full`` symbol runs the subset that answers
    the convention question only (does a window work, and do its stamps land on the dates
    expected for THIS instrument type) — an index and a futures contract are stamped by
    different venues than an ETF and that is exactly what the subset is for.
    """
    record: dict = {"symbol": symbol, "unit": unit, "catalog_history": history,
                    "adapter_url_today": _url(symbol, "2y" if history else "10d"),
                    "cases": []}

    def add(*args, **kw) -> dict:
        case = _case(*args, **kw)
        record["cases"].append(case)
        observed = case.get("observed", {})
        print(f"    {case['case']:<34} status={case.get('http_status')} "
              f"bars={observed.get('bar_count')} span={observed.get('utc_dates_span')} "
              f"err={json.dumps(observed.get('chart_error'))[:90]}", flush=True)
        time.sleep(PACE)
        return case

    baseline = add("baseline_range_as_adapter_builds_it", "baseline",
                   "the URL YahooChartAdapter._url builds TODAY, unchanged; establishes the "
                   "response shape and meta.firstTradeDate so the impossible window below is "
                   "derived rather than typed from memory",
                   symbol, unit, "2y" if history else "10d", None)
    meta = baseline.get("observed", {}).get("meta") or {}
    first_trade = meta.get("firstTradeDate")
    if isinstance(first_trade, (int, float)):
        first_trade_date = datetime.fromtimestamp(first_trade, tz=timezone.utc).date()
        record["first_trade_per_server"] = {"epoch": first_trade,
                                            "utc_date": first_trade_date.isoformat()}
    else:
        first_trade_date = None
        record["first_trade_per_server"] = None

    week_start, week_end = TARGET_WEEK
    multi = add("q1_window_multi_day", "Q1",
                f"period1/period2 over {week_start}..{week_end}: does an absolute window work "
                "at all, is the shape the one parse_yahoo_chart already requires, and does a "
                "WIDER window return wider (which is the only thing that proves the window is "
                "applied rather than ignored)",
                symbol, unit, None, (_utc_day(week_start)[0], _utc_day(week_end)[1]),
                derivation=f"00:00:00Z of {week_start} .. 23:59:59Z of {week_end}")

    target = _first_trading_day(multi, week_start, week_end)
    if target is None:
        record["one_day_note"] = ("the multi-day body carried no bar inside the target week, so "
                                  "no trading day could be derived for the one-day cases")
    else:
        record["one_day_derivation"] = (
            f"{target} is the first date in {week_start}..{week_end} the server itself returned "
            "a bar for; it is not asserted to be a trading day, it is observed to be one")
        day_start, day_end = _utc_day(target)
        add("q2_window_one_day_utc_day", "Q2",
            "a ONE-DAY window as the whole UTC day: exactly one bar, more, or none?",
            symbol, unit, None, (day_start, day_end),
            derivation=f"00:00:00Z .. 23:59:59Z of {target} (a 1d bar is stamped at the "
                       "exchange session OPEN, 13:30Z/14:30Z for a US listing, which this "
                       "span contains under either DST offset)")
        add("q2_window_one_day_zero_width", "Q2",
            "period1 == period2 == midnight UTC: the bound a caller derives when they forget "
            "the bar is stamped at the session open. Does it answer with the day's bar anyway, "
            "or with nothing? Only one of the two encodings can be the recommendation",
            symbol, unit, None, (day_start, day_start),
            derivation=f"00:00:00Z of {target}, twice — a zero-width window")

    if full:
        run = _gap_run(multi, week_start, week_end)
        if run is None:
            record["weekend_note"] = ("every calendar day in the target week came back with a "
                                      "bar, or the body was truncated: no non-trading day "
                                      "could be derived from it")
        else:
            gap_first, gap_last = run
            record["weekend_derivation"] = (
                f"{gap_first}..{gap_last} lies inside the window above but the server returned "
                "no bar for it")
            add("q3_window_on_non_trading_day", "Q3",
                "a one-day window on a date the symbol does NOT print on: empty, an error, or "
                "a NEIGHBOURING bar? This decides whether a parser may ever trust 'the only "
                "bar in the window' or whether exact-date matching is mandatory",
                symbol, unit, None, _utc_day(gap_first),
                derivation=f"00:00:00Z .. 23:59:59Z of {gap_first}")
            if gap_last != gap_first:
                add("q3_window_wholly_inside_non_trading_run", "Q3",
                    "the same question generalised: a MULTI-day window that matches no bar at "
                    "all. Confirms whether the single-day answer is the endpoint's shape for "
                    "an empty window or a one-off",
                    symbol, unit, None, (_utc_day(gap_first)[0], _utc_day(gap_last)[1]),
                    derivation=f"00:00:00Z of {gap_first} .. 23:59:59Z of {gap_last}")

        holiday_start, holiday_end = HOLIDAY_WEEK
        holiday_week = add("q3_holiday_week_span", "Q3",
                           f"the body for {holiday_start}..{holiday_end}, fetched only so the "
                           "holiday below is DERIVED from which dates the server returned "
                           "rather than from a remembered exchange calendar",
                           symbol, unit, None,
                           (_utc_day(holiday_start)[0], _utc_day(holiday_end)[1]),
                           derivation=f"00:00:00Z of {holiday_start} .. 23:59:59Z of {holiday_end}")
        holiday_dates = holiday_week.get("observed", {}).get("utc_dates")
        if holiday_dates is None:
            record["holiday_note"] = ("the holiday-week body carried no readable date list, so "
                                      "no holiday case was derivable from it")
        else:
            # A WEEKDAY with no bar is a holiday by observation. The weekend days of that week
            # are excluded here because the weekend case above already asks about them, and the
            # mid-week absence is the one that looks like a business day to a caller.
            present = set(holiday_dates)
            absent_weekdays = []
            cursor, stop = date.fromisoformat(holiday_start), date.fromisoformat(holiday_end)
            while cursor <= stop:
                if cursor.weekday() < 5 and cursor.isoformat() not in present:
                    absent_weekdays.append(cursor.isoformat())
                cursor += timedelta(days=1)
            record["holiday_derivation"] = (
                f"weekday dates in {holiday_start}..{holiday_end} the server returned no bar "
                f"for: {absent_weekdays} — a weekday the market did not trade is a holiday by "
                "observation, not by consulting a calendar this file does not have")
            if absent_weekdays:
                add("q3_window_on_market_holiday", "Q3",
                    "a one-day window on a WEEKDAY the market was shut: same question as the "
                    "weekend case, asked of the case that is easier to get wrong because the "
                    "date looks like a business day",
                    symbol, unit, None, _utc_day(absent_weekdays[0]),
                    derivation=f"00:00:00Z .. 23:59:59Z of {absent_weekdays[0]}")

        if first_trade_date is not None:
            impossible = first_trade_date - timedelta(days=round(IMPOSSIBLE_YEARS * 365.25))
            record["impossible_window_derivation"] = (
                f"meta.firstTradeDate {first_trade_date.isoformat()} per the baseline response, "
                f"minus {IMPOSSIBLE_YEARS} years = {impossible.isoformat()}")
            add("q4_window_before_first_trade_one_day", "Q4",
                "a one-day window a DECADE before the symbol's first trade: refusal, empty, a "
                "CLAMP to the first real bar (what public write-ups claim, and what ALFRED was "
                "measured to do), or the whole unrelated series? This is WO-1.15's dangerous "
                "FRED case asked of Yahoo",
                symbol, unit, None, _utc_day(impossible.isoformat()),
                derivation=f"00:00:00Z .. 23:59:59Z of {impossible.isoformat()}")
            year_start = f"{impossible.year}-01-01"
            year_end = f"{impossible.year}-12-31"
            add("q4_window_before_first_trade_one_year", "Q4",
                "the same impossible span widened to a whole year, which separates clamping "
                "(one bar, the first real one) from ignoring the window (hundreds of bars from "
                "a period nobody asked about)",
                symbol, unit, None, (_utc_day(year_start)[0], _utc_day(year_end)[1]),
                derivation=f"00:00:00Z of {year_start} .. 23:59:59Z of {year_end}")
            spanning_end = first_trade_date + timedelta(days=5)
            add("q4_window_spanning_first_trade", "Q4",
                "a window opening a decade before the first trade and closing just after it: "
                "clamp-to-start answers with the real first bars, a flat refusal answers with "
                "neither — and the cases above cannot tell those two apart from one side",
                symbol, unit, None,
                (_utc_day(impossible.isoformat())[0], _utc_day(spanning_end.isoformat())[1]),
                derivation=f"00:00:00Z of {impossible.isoformat()} .. 23:59:59Z of "
                           f"{spanning_end.isoformat()} (firstTradeDate + 5 days)")
        future = date.today() + timedelta(days=365)
        add("q4_window_after_last_bar", "Q4",
            "a one-day window a YEAR FROM NOW: the mirror of the impossible case. Public "
            "write-ups claim out-of-range highs are 'rounded down to the most recent timestamp "
            "available'; if that were true here, a caller whose clock or date arithmetic ran "
            "ahead would be handed TODAY's bar labelled with a date that has not happened",
            symbol, unit, None, _utc_day(future.isoformat()),
            derivation=f"00:00:00Z .. 23:59:59Z of {future.isoformat()} (today + 365 days)")

        if target is not None:
            day_start, day_end = _utc_day(target)
            add("q5_window_reversed", "Q5",
                "period2 BEFORE period1: a malformed window's failure shape, measured rather "
                "than guessed, because a caller that computes bounds wrong must fail loudly",
                symbol, unit, None, (day_end, day_start - 86_400 * 5),
                derivation=f"23:59:59Z of {target} as period1, five days EARLIER as period2")
            add("q6_range_and_period_together", "Q6",
                "range=2y AND a one-day period window in the same URL. Which wins? The adapter "
                "emits range today, so an implementation that APPENDS a window rather than "
                "replacing range depends entirely on this answer",
                symbol, unit, "2y", (day_start, day_end),
                derivation=f"range=2y plus 00:00:00Z .. 23:59:59Z of {target}")
    return record


#: The in-scope plain-``close`` symbols. ``full`` marks the one that carries the whole question
#: set; the others carry the convention subset, because an index and a COMEX future are stamped
#: by different venues than a US-listed ETF and the dates must be seen to land for each.
SYMBOLS = [
    {"symbol": "SPY", "unit": "usd", "history": 0, "full": True},
    {"symbol": "^GSPC", "unit": "index", "history": 260, "full": False},
    {"symbol": "HG=F", "unit": "usd_per_lb", "history": 0, "full": False},
]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="where to write the JSON record")
    parser.add_argument("--only", nargs="*", default=None,
                        help="restrict to these symbols (default: all three in SYMBOLS)")
    args = parser.parse_args(argv)

    wanted = [s for s in SYMBOLS if args.only is None or s["symbol"] in args.only]
    records = []
    for index, spec in enumerate(wanted, 1):
        print(f"[{index}/{len(wanted)}] {spec['symbol']}"
              f"{' (full question set)' if spec['full'] else ' (convention subset)'}", flush=True)
        records.append(probe_one(spec["symbol"], spec["unit"], spec["history"], spec["full"]))

    document = {
        "probed_utc": date.today().isoformat(),
        "endpoint": BASE,
        "credential": "none (this endpoint takes none)",
        "user_agent": USER_AGENT,
        "parser_imported": parse_yahoo_chart is not None,
        "scope_note": ("plain close symbols only; PID.md's WO-1.16 correction (2026-10-15) "
                       "rules the adjclose ingredients out of this round and the probe never "
                       "asks for adjclose"),
        "why": ("WO-1.16: whether query1.finance.yahoo.com's v8 chart endpoint accepts an "
                "ABSOLUTE period1/period2 window in place of the relative range= the adapter "
                "builds today, and what it does on a one-day window, a non-trading day, and a "
                "window before the symbol existed — the last being the case where a CLAMP "
                "(claimed by public write-ups, measured of ALFRED in "
                "evidence/wo114_alfred_probe.json) would let a backfill forge a historical "
                "print out of the first real bar"),
        "symbols": records,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"-- {len(records)} symbols written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
