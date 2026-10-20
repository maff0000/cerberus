#!/usr/bin/env python3
"""THE YAHOO RELATIVE-PAGE PROBE — how many dated closes does each ``range=`` actually answer?

    PYTHONPATH=src:. python3 tools/probe/yahoo_range_page_probe.py --out evidence/<file>.json

WHY THIS EXISTS (WO-1.20). ``gold_real_rate_cross``'s gold leg moves from the 403ing LBMA fix
to ``yahoo.GC=F.history``, and that row declares ``history=2600`` — ~10 years of trading days,
the depth ``fred.DFII10.history`` has carried since WO-1.7 and the depth the retiring LBMA row
declared. But ``YahooChartAdapter._url`` asked for a FLAT ``range=2y`` for every history read
from WO-1.2b until this WO, and a relative page has a size the caller does not get to choose.
So the question this file answers, BEFORE the catalog declares a number: what does each range
actually hand back, and can the page the adapter asks for carry the rows the row declares?

THE DEFECT IT IS LOOKING FOR IS QUIET, WHICH IS WHY IT IS MEASURED RATHER THAN REASONED.
``_correlation_percentile`` needs MINIMUM_PERCENTILE_HISTORY (360) earlier correlations over a
CORRELATION_WINDOW (60), i.e. 421 shared dates. A 2y page clears that. So a 2600-row
declaration served by a 2y page would NOT have failed loud: the dial would have gone on
printing a percentile whose history base was two years while the catalog row, SUBSTITUTED_FEEDS
and MATH.md all said ten. A number that is wrong by a factor of five and still renders is worth
a socket.

IT IS A PROBE, NOT A GATE. It opens sockets to a third party, so its verdict is not
reproducible offline and can never be a register check (CD-PL-F48). It records what the server
said; a human reads that and decides what the adapter asks for.

WHAT IT ASKS. Every relative range the response's own ``meta.validRanges`` offers that could
plausibly serve a deep history, for ``GC=F`` — the new ingredient's symbol. Then ``range=2y``
for each plain-``close`` symbol that ALREADY declares a history, so the record also says what
the page the existing rows ask for really holds: ``yahoo.BIZD.adj`` declares 520 rows and is
commented "the whole 2y page", a claim this probe either supports or contradicts. ``adjclose``
is never asked for (the WO-1.16 scope correction); BIZD is asked as plain ``close`` here purely
to size its PAGE, which is a property of the range and not of the column.

WHAT IS WRITTEN DOWN, per request: the URL byte-for-byte, the HTTP status, the raw bar count,
how many of those bars carry a non-null close, the first and last bar dates, and — read through
``parse_yahoo_chart`` itself rather than recounted here — how many dated pairs the adapter
would actually store, and whether that covers the rows the catalog declares.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone

sys.path.insert(0, "src")
sys.path.insert(0, ".")

from ingestion.adapters import parse_yahoo_chart  # noqa: E402
from ingestion.catalog import INGREDIENTS  # noqa: E402

BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
USER_AGENT = "Mozilla/5.0 (compatible; cerberus-ingest/1.0)"
TIMEOUT = 30.0

#: The row this WO is sizing the page for, and the depth it declares.
TARGET_SYMBOL, TARGET_HISTORY = "GC=F", 2600


def _get(url: str) -> tuple:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace")


def _quoted(symbol: str) -> str:
    return symbol.replace("^", "%5E").replace("=", "%3D")


def _observe(symbol: str, rng: str, declared_history: int) -> dict:
    url = f"{BASE}/{_quoted(symbol)}?range={rng}&interval=1d"
    status, body = _get(url)
    record = {"asks": f"how many dated closes does range={rng} answer for {symbol}",
              "url": url, "range": rng, "symbol": symbol, "http_status": status}
    try:
        result = json.loads(body)["chart"]["result"][0]
        stamps, closes = result["timestamp"], result["indicators"]["quote"][0]["close"]
    except (ValueError, KeyError, IndexError, TypeError):
        record["observed"] = {"readable": False, "body_head": body[:400]}
        return record
    as_date = lambda s: datetime.fromtimestamp(s, tz=timezone.utc).date().isoformat()  # noqa: E731
    # The adapter's own read, so the count is the one that would reach the store rather than a
    # recount here. ``today`` is passed exactly as the live loop passes it: the in-session last
    # bar is not a close and is dropped.
    parsed = parse_yahoo_chart(body, "probe", declared_history or 1, today=date.today())
    stored = parsed.get("history") or []
    record["observed"] = {
        "readable": True,
        "bars_returned": len(stamps),
        "bars_with_a_close": sum(1 for close in closes if close is not None),
        "first_bar_utc": as_date(stamps[0]),
        "last_bar_utc": as_date(stamps[-1]),
        "meta_valid_ranges": result.get("meta", {}).get("validRanges"),
        "dated_pairs_parse_yahoo_chart_would_store": len(stored),
        "declared_history_rows": declared_history,
        "page_covers_the_declared_rows": bool(declared_history) and len(stored) >= declared_history,
    }
    return record


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    cases = [_observe(TARGET_SYMBOL, rng, TARGET_HISTORY)
             for rng in ("10d", "2y", "5y", "10y", "max")]

    # What the page the EXISTING history rows ask for really holds. Plain-close rows only.
    existing = {ing.ref: ing.history for ing in INGREDIENTS
                if ing.kind == "yahoo" and ing.history and ing.column in ("", "close")}
    adjusted = sorted({ing.ref for ing in INGREDIENTS
                       if ing.kind == "yahoo" and ing.history and ing.column == "adjclose"})
    for symbol, history in sorted(existing.items()):
        if symbol == TARGET_SYMBOL:
            continue
        cases.append(_observe(symbol, "2y", history))
    # BIZD is the row whose 520 is commented "the whole 2y page"; its PAGE is a property of the
    # range, so it is sized here as plain ``close`` and its adjclose column is never requested.
    cases.append(_observe("BIZD", "2y", 520))

    document = {
        "probed_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": BASE,
        "credential": "none (this endpoint takes none)",
        "user_agent": USER_AGENT,
        "interval": "1d",
        "adjclose_rows_deliberately_not_asked": adjusted,
        "why": ("WO-1.20: yahoo.GC=F.history declares history=2600 (~10y of trading days, the "
                "depth fred.DFII10.history carries and the retiring lbma.gold_fix_usd.history "
                "declared), while YahooChartAdapter._url asked a flat range=2y for every "
                "history read. A 2y page still clears the 421 shared dates "
                "_correlation_percentile needs, so an undersized page would NOT have failed "
                "loud — the dial would have printed a percentile over a two-year base while "
                "every declaration said ten years. This measures each range's real size."),
        "cases": cases,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"-- {len(cases)} requests written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
