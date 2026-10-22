#!/usr/bin/env python3
"""THE YAHOO DEPTH PROBE — how do you ask this endpoint for TWENTY-SIX YEARS of daily bars?

    PYTHONPATH=src:. python3 tools/probe/yahoo_range_probe.py --out evidence/<file>.json

WHY THIS EXISTS (WO-1.17). ``ingestion.backfill_calendar.yahoo_observation_dates`` must read
the whole list of dates a symbol printed a close on across a backfill span — WO-1.17's
episodes reach back to 2000 — and the live loop's request reaches nowhere near it:
``YahooChartAdapter._url`` asks ``range=10d`` (``2y`` with a history). So the DEPTH question
had to be settled before the date-list reader was written against an answer nobody had
measured. WO-1.16 (``evidence/wo116_yahoo_window_probe.json``) established that an absolute
``period1``/``period2`` window is applied exactly or refused with a clean ``400``; what it did
NOT ask is whether such a window stays at daily granularity when it is WIDE, nor what the
obvious one-word alternative — ``range=max`` — actually returns.

THE TRAP THIS FILE EXISTS TO CATCH, stated as the assumption it is. ``max`` is the first thing
a caller reaches for and it is in every symbol's own ``meta.validRanges``, so an implementation
built on "ask for max&interval=1d and read the dates off it" would compile, fetch ``200``, and
look right. If the server honours ``range`` but QUIETLY OVERRIDES ``interval``, that body is a
list of month- or quarter-START dates wearing the costume of a daily publication calendar —
and a date list is the one artefact in this module whose wrongness is invisible downstream: the
backfill would be told to recover 406 dates the symbol never printed on and never told about
the ~8,000 it did. A ``200`` nobody questions is the worst available failure here, which is why
the granularity is not taken from the parameter we sent but read off the response, and read
TWICE — once as the ``meta.dataGranularity`` the server declares, and once from the actual
spacing of the bars it sent (``step_days_histogram``), because a declared label is itself a
claim.

IT IS A PROBE, NOT A GATE, AND IT WRITES NO ADAPTER CODE. It opens sockets to a third party, so
its verdict is not reproducible offline and can never be a register check (CD-PL-F48). It
records what the server said; a human reads that and decides what the code does. The companion
to that rule is ``tests/test_wo117_calendar.py``, which re-derives this file's headline numbers
from this file and goes red if the prose in ``ingestion/`` ever stops matching the measurement.

SCOPE — PLAIN ``close`` SYMBOLS ONLY, for WO-1.16's reason unchanged: ``PID.md``'s WO-1.16 scope
correction (2026-10-15) rules the 51 ``adjclose`` rows out (an adjusted close has no
point-in-time value to recover), and this probe never asks for ``adjclose``.

WHAT IT ASKS, AND WHAT EACH CASE TELLS APART
--------------------------------------------
``R1`` — ``range=max&interval=1d``, the obvious deep ask. Is ``max`` honoured at all (does the
server echo ``meta.range == "max"``, is it in ``meta.validRanges``), and at WHAT granularity?
Asked of three symbols because "SPY came back monthly" alone cannot tell a symbol-specific
quirk from the endpoint's rule, and ``^GSPC``'s answer turns out to differ from SPY's.

``R2`` — the same ask with ``interval=1d`` LEFT OFF. If ``max`` without an interval returns the
same coarse body, then ``interval`` was never in play and the server simply has one granularity
per range; if it differs, ``interval=1d`` was sent, seen, and overridden. Two readings of the
same finding, and the difference between them is what "silently ignored" is allowed to mean.

``R3`` — a RELATIVE range at shorter depths (``1y``, ``5y``, ``10y``). This is the control that
stops R1 being over-read: if every ``range=`` answered coarse, the finding would be "range= is
not a daily mechanism"; if the short ones answer ``1d`` and only the long ones coarsen, the
finding is about DEPTH, and the boundary is visible in the record rather than guessed at.

``R4`` — the ABSOLUTE window at the depths the catalog actually needs: ``^GSPC`` from 1927
(the deepest ask any of the 7 plain-close rows can make), ``^GSPC`` from 2000 (the span
WO-1.17's episodes need), and ``SPY`` across its whole listed life from 1993. Does
``dataGranularity`` stay ``"1d"`` at 24,000 bars, does it arrive in ONE response, and how close
does the body come to :data:`ingestion.adapters.MAX_BODY_BYTES`? That last number decides
whether the reader needs a chunked walk or a single GET, and chunking a span means a seam to
get wrong, so it is worth a measurement rather than a precaution.

``R5`` — two SMALL windows recorded VERBATIM: a 2015 fortnight of SPY and the first fortnight
of ``^GSPC``'s recorded history in 1927/1928. These exist to be read as bodies rather than as
counts — the second is the oldest shape this endpoint serves anyone, and a reader that only
ever saw 2015 bars is a reader with an untested assumption about what a 1927 bar looks like.

``null`` CLOSES ARE COUNTED IN EVERY BODY, with their dates listed where there are few. Yahoo's
convention for "no print this session" is JSON ``null`` rather than a token, and
``yahoo_chart_dates`` makes its one deliberate SKIP on exactly that shape. Whether the real
deep bodies contain any is therefore a fact about how often that branch is reached in
production, and it is cheaper to count here than to wonder later.

BODIES are recorded verbatim under :data:`VERBATIM_CAP` and otherwise as their full ``meta``
block, their counts, their span, head and tail bars, and the step histogram — a 2.6 MB body is
not an evidence file's business, but every number drawn from it is.
"""

from __future__ import annotations

import argparse
import collections
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

try:  # read-only: the probe asks the REAL parser whether it can read what the server sent,
    # and the REAL builder whether the URL probed is the one the code would have asked for.
    from ingestion.adapters import MAX_BODY_BYTES, parse_yahoo_chart, yahoo_chart_url
except ImportError:  # pragma: no cover - the structural record below still stands alone
    parse_yahoo_chart = None  # type: ignore[assignment]
    yahoo_chart_url = None  # type: ignore[assignment]
    MAX_BODY_BYTES = None  # type: ignore[assignment]

HOST = "query1.finance.yahoo.com"
#: The EXACT door ``ingestion.adapters.YahooChartAdapter`` uses: same host, same v8 chart
#: path, no credential of any kind (this endpoint takes none and none exists in this file).
BASE = f"https://{HOST}/v8/finance/chart/"
#: Byte-for-byte ``ingestion.adapters.YAHOO_USER_AGENT``: Yahoo answers 429 to urllib's default
#: agent and 200 to an identified browser-style one, so probing with a different agent would be
#: probing a different door. Typed here rather than imported for the reason WO-1.16's probe
#: typed it: a probe that borrows the value under test cannot show the two agree.
USER_AGENT = "Mozilla/5.0 (compatible; cerberus-ingest/1.0)"
#: Courtesy gap between requests to an unofficial, unpaid, rate-limiting endpoint. Longer than
#: WO-1.16's 1.2s because several of these responses are megabytes.
PACE = 2.0
#: Bodies at or under this are stored verbatim. Small by design: R5's two windows are meant to
#: be read, and a 725 KB body stored verbatim would bury them.
VERBATIM_CAP = 12_000
#: Bars/dates kept at each end of a body too large to store whole.
HEAD_TAIL = 5
#: Null closes listed by date rather than merely counted, up to this many.
NULL_DATE_CAP = 40
#: The near bound of every absolute window below. FIXED at WO-1.16's probe date rather than
#: ``date.today()``, deliberately: the bar counts and byte sizes the ``ingestion/`` docstrings
#: cite were measured against this bound, so a re-run of this file reproduces those numbers
#: instead of drifting one bar per day and leaving a reader to wonder which of the two is
#: wrong. The far bounds are the catalog's own depths.
WINDOW_END = "2026-10-15"
#: ``^GSPC``'s deep ask, a year before any S&P print exists, so the first bar returned is the
#: SERVER's answer to "what is the oldest you have" rather than a date this file asserts.
DEEP_START = "1927-01-01"
#: The span WO-1.17's backfill episodes need, and SPY's whole listed life (its real first trade
#: is 1993-01-29 per ``meta.firstTradeDate``; 01-01 is again asked from outside it on purpose).
EPISODE_START = "2000-01-01"
SPY_LIFE_START = "1993-01-01"
#: R5's two verbatim windows: a 2015 fortnight, and the first fortnight of recorded history.
SMALL_WINDOW = ("2015-06-08", "2015-06-19")
ANCIENT_WINDOW = ("1927-12-25", "1928-01-10")


def _quoted(symbol: str) -> str:
    """The symbol, escaped the way ``yahoo_chart_url`` escapes it."""
    return symbol.replace("^", "%5E").replace("=", "%3D")


def _url(symbol: str, rng: Union[str, None] = None,
         period1: Union[int, None] = None, period2: Union[int, None] = None,
         interval: Union[str, None] = "1d") -> str:
    """The request under test, built here rather than borrowed from the code it measures."""
    parts = []
    if rng is not None:
        parts.append(f"range={rng}")
    if period1 is not None:
        parts.append(f"period1={period1}")
    if period2 is not None:
        parts.append(f"period2={period2}")
    if interval is not None:
        parts.append(f"interval={interval}")
    return BASE + _quoted(symbol) + "?" + "&".join(parts)


def _utc_day_span(start: str, end: str) -> tuple[int, int]:
    """``[00:00:00Z of start, 23:59:59Z of end]`` as epoch seconds.

    The same arithmetic WO-1.16 measured to be the correct encoding and
    ``ingestion.adapters.yahoo_chart_url`` now performs: a ``1d`` bar is stamped at the
    exchange's session OPEN (13:30Z/14:30Z for a US listing), never at midnight, so the window
    must CONTAIN that instant. A zero-width window at midnight returns nothing at all.
    """
    first = datetime(*(int(p) for p in start.split("-")), tzinfo=timezone.utc)
    last = datetime(*(int(p) for p in end.split("-")), tzinfo=timezone.utc)
    return int(first.timestamp()), int((last + timedelta(days=1)).timestamp()) - 1


def _fetch(url: str, timeout: float = 120.0) -> dict:
    """status, content type and the literal body. An HTTP error is an ANSWER, not a failure.

    A 400/404/422 here is one of the outcomes the probe is looking for, so it is recorded with
    its body rather than raised. Only a transport failure — an ABSENCE of an answer — is
    reported as an error. The timeout is generous because a 26-year window is megabytes.
    """
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"http_status": response.status,
                    "content_type": response.headers.get("Content-Type"),
                    "body": response.read(64_000_000).decode("utf-8", "replace")}
    except urllib.error.HTTPError as failure:
        return {"http_status": failure.code,
                "content_type": failure.headers.get("Content-Type") if failure.headers else None,
                "http_error": True,
                "body": failure.read(400_000).decode("utf-8", "replace")}


def _bar_rows(stamps: list, closes: list, gmtoffset: Union[int, None]) -> list:
    """Every bar as ``[epoch, utc_date, exchange_local_date, close]``, as WO-1.16 recorded them.

    The UTC column is literally what ``parse_yahoo_chart`` and ``yahoo_chart_dates`` compute.
    The local column is the same stamp shifted by the ``gmtoffset`` THIS RESPONSE declares.
    Both are written down so the convention is visible rather than asserted — and at 1927 depth
    that matters more than usual, since the offset a 1927 bar carries is nobody's assumption.
    """
    rows = []
    for stamp, close in zip(stamps, closes):
        try:
            moment = datetime.fromtimestamp(stamp, tz=timezone.utc)
        except (OSError, OverflowError, ValueError, TypeError):
            rows.append([stamp, None, None, close])
            continue
        local = ((moment + timedelta(seconds=gmtoffset)).date().isoformat()
                 if gmtoffset is not None else None)
        rows.append([stamp, moment.date().isoformat(), local, close])
    return rows


def _step_histogram(utc_dates: list) -> dict:
    """How many calendar days apart consecutive bars are, counted.

    THE GRANULARITY, READ OFF THE BARS THEMSELVES rather than off the label the server attached
    to them. ``meta.dataGranularity`` is a claim; this is the body. Daily bars step 1 day
    (3 across a weekend, 4 over a holiday); monthly bars step 28-31; quarterly 89-92. So this
    histogram is what makes "``interval=1d`` was ignored" a measurement instead of a reading of
    one field, and it is the number ``tests/test_wo117_calendar.py`` re-derives.
    """
    steps: collections.Counter = collections.Counter()
    readable = [d for d in utc_dates if d]
    for earlier, later in zip(readable, readable[1:]):
        try:
            steps[(date.fromisoformat(later) - date.fromisoformat(earlier)).days] += 1
        except ValueError:
            steps["unreadable"] += 1  # type: ignore[index]
    return {str(k): v for k, v in sorted(steps.items(), key=lambda kv: str(kv[0]))}


def _shape(body: str, unit: str = "usd") -> dict:
    """What the body IS, measured. Nothing here interprets; it records.

    ``parse_yahoo_chart_says`` is the repo's own parser run on this exact body: whether a
    coarse ``range=max`` body is READABLE is a separate question from whether it answers the
    question asked, and the dangerous answer is "yes, perfectly" — which is what makes the
    coarsening silent. ``null_close_count`` is recorded for every body because
    ``ingestion.backfill_calendar.yahoo_chart_dates`` makes its one deliberate skip on that
    shape and how often it occurs in real deep history is a fact worth having.
    """
    out: dict = {"body_bytes": len(body)}
    if MAX_BODY_BYTES:
        out["pct_of_max_body_bytes"] = round(100.0 * len(body) / MAX_BODY_BYTES, 2)
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
    out["meta"] = meta  # verbatim, including the range/dataGranularity/validRanges echo
    # THE THREE FIELDS THIS WHOLE FILE TURNS ON, lifted out of meta so a reader does not have
    # to hunt them: what we asked for, what the server says it served, and what it admits is
    # askable. ``max in validRanges`` is why "max is simply not supported" is NOT the finding.
    out["meta_range_echo"] = meta.get("range")
    out["meta_data_granularity"] = meta.get("dataGranularity")
    out["meta_valid_ranges"] = meta.get("validRanges")
    out["meta_first_trade_date_utc"] = (
        datetime.fromtimestamp(meta["firstTradeDate"], tz=timezone.utc).date().isoformat()
        if isinstance(meta.get("firstTradeDate"), (int, float)) else None)
    indicators = result.get("indicators") or {}
    out["indicator_keys"] = sorted(indicators.keys())
    quote = (indicators.get("quote") or [{}])[0]
    out["quote_keys"] = sorted(quote.keys()) if isinstance(quote, dict) else None
    # The two paths every reader of this body requires, asked as separate presence questions.
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
    out["step_days_histogram"] = _step_histogram(utc_dates)
    null_dates = [row[1] for row in bars if row[3] is None]
    out["null_close_count"] = len(null_dates)
    out["null_close_dates"] = (null_dates if len(null_dates) <= NULL_DATE_CAP
                               else null_dates[:NULL_DATE_CAP])
    out["null_close_dates_truncated"] = len(null_dates) > NULL_DATE_CAP
    out["first_bar_is"] = bars[0] if bars else None
    out["last_bar_is"] = bars[-1] if bars else None
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
    if parse_yahoo_chart is not None:
        # today=None so NOTHING is dropped: the probe wants the server's bars, not the live
        # loop's partial-bar guard, which is a separate behaviour with its own tests.
        out["parse_yahoo_chart_says"] = parse_yahoo_chart(body, unit, 0, today=None,
                                                          field="close")
    return out


def _case(name: str, question: str, asks: str, symbol: str, unit: str,
          rng: Union[str, None], window: Union[tuple, None],
          interval: Union[str, None] = "1d",
          derivation: Union[str, None] = None) -> dict:
    """One request, one record. ``asks`` states in words what this case tells apart."""
    period1, period2 = _utc_day_span(*window) if window else (None, None)
    url = _url(symbol, rng, period1, period2, interval)
    record: dict = {"case": name, "question": question, "asks": asks, "range_param": rng,
                    "interval_param": interval, "period1": period1, "period2": period2,
                    "url": url}
    if window:
        record["window_asked"] = list(window)
        record["period_bounds_utc"] = [
            datetime.fromtimestamp(period1, tz=timezone.utc).isoformat(),
            datetime.fromtimestamp(period2, tz=timezone.utc).isoformat()]
        if yahoo_chart_url is not None and interval == "1d" and rng is None:
            # THE URL PROBED IS THE URL THE CODE ASKS FOR, held by equality rather than by
            # eye: this file builds its own window arithmetic (so the two can be compared at
            # all) and then records whether ingestion.adapters.yahoo_chart_url agrees. If it
            # ever does not, every number below is about a different request than the one
            # production makes, and the record says so instead of implying otherwise.
            built = yahoo_chart_url(symbol, start=window[0], end=window[1])
            record["yahoo_chart_url_builds"] = built
            record["url_matches_yahoo_chart_url"] = (built == url)
    if rng is not None and yahoo_chart_url is not None and window is None and interval == "1d":
        built = yahoo_chart_url(symbol, relative_range=rng)
        record["yahoo_chart_url_builds"] = built
        record["url_matches_yahoo_chart_url"] = (built == url)
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


def probe_one(spec: dict) -> dict:
    """Every case this symbol carries, in order, each pacing itself.

    ``deep`` marks the symbol whose whole history is asked for (``^GSPC``, the deepest ask in
    the catalog); ``controls`` marks the one that also carries the short-range controls and the
    verbatim window. The others carry R1/R2 only — the point of a third symbol is that
    ``range=max``'s granularity is shown to vary by symbol, which one symbol cannot show.
    """
    symbol, unit = spec["symbol"], spec["unit"]
    record: dict = {"symbol": symbol, "unit": unit, "catalog_history": spec["history"],
                    "catalog_column": "", "adapter_url_today":
                        _url(symbol, "2y" if spec["history"] else "10d"),
                    "cases": []}

    def add(*args, **kw) -> dict:
        case = _case(*args, **kw)
        record["cases"].append(case)
        observed = case.get("observed", {})
        print(f"    {case['case']:<40} status={case.get('http_status')} "
              f"bars={observed.get('bar_count')} "
              f"granularity={observed.get('meta_data_granularity')} "
              f"span={observed.get('utc_dates_span')} "
              f"bytes={observed.get('body_bytes')}", flush=True)
        time.sleep(PACE)
        return case

    add("r1_range_max_interval_1d", "R1",
        "range=max&interval=1d — the obvious deep ask. Is max HONOURED (does the server echo "
        "meta.range=max, and does meta.validRanges list it), and at what granularity? A coarse "
        "200 here is the silent failure this probe exists to catch: a month-start date list "
        "presented as a daily publication calendar",
        symbol, unit, "max", None)
    add("r2_range_max_no_interval", "R2",
        "the same ask with interval LEFT OFF entirely. If the body is identical, interval was "
        "never in play and this range simply has one granularity; if it differs, interval=1d "
        "was sent, seen and OVERRIDDEN — and 'silently ignored' means the second of those",
        symbol, unit, "max", None, interval=None)

    if spec.get("controls"):
        for shorter in ("1y", "5y", "10y"):
            add(f"r3_range_{shorter}_interval_1d", "R3",
                f"range={shorter}&interval=1d — the CONTROL that stops R1 being over-read. If "
                "every range= answered coarse, the finding would be about range=; if the short "
                "ones answer 1d and only the long ones coarsen, the finding is about DEPTH and "
                "the boundary is visible here rather than guessed at",
                symbol, unit, shorter, None)

    for window_spec in spec.get("windows", []):
        add(window_spec["case"], "R4", window_spec["asks"], symbol, unit, None,
            (window_spec["start"], WINDOW_END),
            derivation=f"00:00:00Z of {window_spec['start']} .. 23:59:59Z of {WINDOW_END} "
                       f"(the near bound is fixed, not today — see WINDOW_END)")

    for window_spec in spec.get("verbatim_windows", []):
        add(window_spec["case"], "R5", window_spec["asks"], symbol, unit, None,
            (window_spec["start"], window_spec["end"]),
            derivation=f"00:00:00Z of {window_spec['start']} .. 23:59:59Z of "
                       f"{window_spec['end']}")
    return record


#: The in-scope plain-``close`` symbols this file asks about. All 7 of the catalog's plain rows
#: share one endpoint and one mechanism; three are probed because R1's answer was measured to
#: DIFFER BY SYMBOL (an ETF, an index and a COMEX future are three venues' stamping), and a
#: finding that varies by symbol cannot be established from one.
SYMBOLS = [
    {"symbol": "SPY", "unit": "usd", "history": 0, "controls": True,
     "windows": [
         {"case": "r4_window_whole_listed_life", "start": SPY_LIFE_START,
          "asks": "an absolute window across SPY's WHOLE listed life, opened a month before "
                  "its real first trade (1993-01-29 per meta.firstTradeDate) so the first bar "
                  "returned is the server's answer rather than this file's assertion. Does "
                  "granularity stay 1d over 33 years, in ONE response? This is the "
                  "same-mechanism check that stops the ^GSPC result below being a one-symbol "
                  "fluke"}],
     "verbatim_windows": [
         {"case": "r5_small_window_verbatim", "start": SMALL_WINDOW[0], "end": SMALL_WINDOW[1],
          "asks": "a 2015 fortnight, recorded VERBATIM: the body a reader should be able to "
                  "hold in their head, and the one a test can carry as a literal"}]},
    {"symbol": "^GSPC", "unit": "index", "history": 260,
     "windows": [
         {"case": "r4_window_deep_1927", "start": DEEP_START,
          "asks": "the DEEPEST ask any plain-close row in this catalog can make: ^GSPC from a "
                  "year before any S&P print exists to WINDOW_END. Does dataGranularity stay "
                  "1d at tens of thousands of bars, does it arrive in ONE response, and how "
                  "close does the body come to MAX_BODY_BYTES? That last number is what "
                  "decides single-GET versus a chunked walk with a seam to get wrong"},
         {"case": "r4_window_episode_span_2000", "start": EPISODE_START,
          "asks": "the span WO-1.17's backfill episodes actually need (2000 onward), sized so "
                  "the real cost of a calendar read is a number in the record rather than an "
                  "extrapolation from the 1927 case"}],
     "verbatim_windows": [
         {"case": "r5_ancient_window_verbatim", "start": ANCIENT_WINDOW[0],
          "end": ANCIENT_WINDOW[1],
          "asks": "the FIRST FORTNIGHT of recorded history, VERBATIM: the oldest shape this "
                  "endpoint serves anyone. A reader who has only ever seen 2015 bars has an "
                  "untested assumption about what a 1927 bar carries — gmtoffset, null closes, "
                  "or a stamp that is not a session open at all"}]},
    {"symbol": "HG=F", "unit": "usd_per_lb", "history": 0},
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
        print(f"[{index}/{len(wanted)}] {spec['symbol']}", flush=True)
        records.append(probe_one(spec))

    document = {
        "probed_utc": date.today().isoformat(),
        "endpoint": BASE,
        "credential": "none (this endpoint takes none)",
        "user_agent": USER_AGENT,
        "parser_imported": parse_yahoo_chart is not None,
        "builder_imported": yahoo_chart_url is not None,
        "max_body_bytes": MAX_BODY_BYTES,
        "window_end": WINDOW_END,
        "window_end_note": ("every absolute window below ends at this FIXED date rather than "
                            "today, so a re-run reproduces the bar counts and byte sizes the "
                            "ingestion/ docstrings cite instead of drifting a bar per day"),
        "scope_note": ("the 7 plain-close yahoo rows only; PID.md's WO-1.16 correction "
                       "(2026-10-15) rules the 51 adjclose rows out of this work and the probe "
                       "never asks for adjclose"),
        "why": ("WO-1.17: HOW to ask query1.finance.yahoo.com's v8 chart endpoint for 26 years "
                "of DAILY bars, given that ingestion.backfill_calendar.yahoo_observation_dates "
                "needs the whole date list and the live loop's range=10d/2y reaches nowhere "
                "near a backfill episode in 2000. The specific thing measured here is whether "
                "range=max — honoured, listed in every symbol's validRanges, and the first "
                "thing a caller reaches for — serves interval=1d or SILENTLY COARSENS it, "
                "because a coarsened 200 would be read as a daily publication calendar and "
                "would tell the backfill to recover dates the symbol never printed on while "
                "never mentioning the ones it did"),
        "symbols": records,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"-- {len(records)} symbols written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
