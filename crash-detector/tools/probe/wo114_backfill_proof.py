#!/usr/bin/env python3
"""THE PROOF RUN — ``ingestion.backfill`` against the REAL network and a REAL store.

    PYTHONPATH=src:. python3 tools/probe/wo114_backfill_proof.py \
        --db <store.sqlite> --source fred.GDP --start 2024-07-01 --end 2026-04-01 \
        --out evidence/wo114_backfill_proof.json

WHY THIS EXISTS, GIVEN THAT ``tests/test_wo114_backfill.py`` ALREADY PASSES. Those tests
substitute the WIRE and nothing else — real adapters, real bisection, real parsers, real
store, a callable where the socket should be. That is the right shape for a test and it
cannot answer one question: does the thing work against the server that actually exists? A
transport fake answers what it was told to answer. ALFRED answers what ALFRED answers, which
on 2026-10-13 included the clamping behaviour a fake would only reproduce if somebody had
already thought to. So this runs the driver for real, and writes down what came back.

IT IS A PROBE, NOT A GATE — the same standing as ``alfred_vintage_probe.py``. It opens
sockets to a third party, so it is not reproducible offline and is not a register check
(CD-PL-F48). It writes a JSON record a human reads.

WHAT IT RECORDS, AND WHY THE CURRENT VALUES ARE FETCHED TOO
    The ``backfill`` section is the driver's own ``BackfillResult`` — every date in exactly
    one of four buckets. The ``stored`` section is read back OUT OF THE STORE, so what is
    reported is what the database holds and not what the driver believed it wrote.

    The ``revision`` section is the part that makes this a proof of POINT-IN-TIME rather than
    a proof of plumbing. It issues ONE extra GET — to ``fred.stlouisfed.org``, the live
    collector's own host, for the same observation window — and reports today's CURRENT value
    for each quarter beside the first-published value just stored. If those two columns were
    equal the run would have proved nothing: a backfill that stores today's number for a past
    quarter is exactly the forgery ``ingestion.vintage`` exists to prevent, and the only way
    to show it did NOT happen is to show both numbers and the gap between them.

    ``vintage_date`` in the stored payload is the third leg, and it is independently
    checkable against a calendar nobody here controls: BEA publishes the advance estimate of
    a quarter's GDP about a month after the quarter ends, so a first-serving vintage that
    lands on a BEA release day is the server corroborating the bisection's answer.

WHAT IT DOES NOT DO. It does not create a store, migrate one it was not pointed at, or pick
the file for you: ``--db`` is required and the caller owns the decision of which database a
real write lands in. It computes no cadence of its own — ``ingestion.backfill_dates`` states
the dating convention and this file asks it.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import date, datetime, timezone

from ingestion.adapters import http_get, parse_fred_csv
from ingestion.backfill import backfill_range
from ingestion.backfill_dates import observation_dates
from ingestion.catalog import INGREDIENTS
from ingestion.store import SqliteStore
from ingestion.vintage import requires_original_vintage

#: Today's whole series, for the current-value column. ``cosd``/``coed`` bound the body to
#: the window asked about; the rows are matched by exact date, never by position.
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def ingredient(source_id: str):
    for ing in INGREDIENTS:
        if ing.source_id == source_id:
            return ing
    raise SystemExit(f"no such ingredient: {source_id}")


def current_values(ing, start: str, end: str, timeout: float = 30.0) -> dict:
    """Today's FRED value for every observation date in ``[start, end]``. One GET.

    Parsed by ``parse_fred_csv`` with ``history`` wide enough to carry the whole window, so
    the current column is read by the SAME parser the live collector reads it with rather
    than by a second CSV reader written here.
    """
    suffix = f"&transformation={ing.transformation}" if ing.transformation else ""
    url = f"{FRED_CSV}?id={ing.ref}{suffix}&cosd={start}&coed={end}"
    column = ing.ref + (f"_{ing.transformation.upper()}" if ing.transformation else "")
    body = http_get(url, timeout)
    parsed = parse_fred_csv(body, column, ing.unit, history=400)
    if "malformed" in parsed:
        return {"error": parsed["malformed"]}
    return {row[0]: row[1] for row in parsed.get("history", [])} or {
        parsed["observation_date"]: parsed["value"]}


def stored_rows(db_path: str, source_id: str) -> list:
    """What the DATABASE holds for this source, vintage label included. Read-only handle."""
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = db.execute(
            "SELECT source_as_of_utc, payload, vintage, admitted_utc FROM raw_reading "
            "WHERE source_id=? ORDER BY source_as_of_utc", (source_id,)).fetchall()
    finally:
        db.close()
    return [{"source_as_of_utc": as_of, "payload": json.loads(payload), "vintage": vintage,
             "admitted_utc": admitted} for as_of, payload, vintage, admitted in rows]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="WO-1.14 real backfill proof run")
    parser.add_argument("--db", required=True, help="the SQLite store to write into")
    parser.add_argument("--source", default="fred.GDP", help="ingredient source_id")
    parser.add_argument("--start", required=True, help="inclusive lower bound (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="inclusive upper bound (YYYY-MM-DD)")
    parser.add_argument("--out", required=True, help="where to write the JSON record")
    parser.add_argument("--pace", type=float, default=None, help="override courtesy pacing")
    args = parser.parse_args(argv)

    ing = ingredient(args.source)
    dates = observation_dates(ing, args.start, args.end)
    if not dates:
        raise SystemExit(f"{args.start}..{args.end} contains no observation date for {ing.source_id}")
    print(f"-- {ing.source_id}: {len(dates)} observation dates {dates[0]}..{dates[-1]}", flush=True)
    print(f"-- point-in-time required: {requires_original_vintage(ing.ref, ing.transformation)}",
          flush=True)

    started = datetime.now(timezone.utc)
    kwargs = {} if args.pace is None else {"pace": args.pace}
    with SqliteStore(args.db) as store:
        result = backfill_range(ing, dates, store, lambda: datetime.now(timezone.utc), **kwargs)
    finished = datetime.now(timezone.utc)
    print(f"-- {result.counts}", flush=True)

    rows = stored_rows(args.db, ing.source_id)
    try:
        current = current_values(ing, args.start, args.end)
    except Exception as failure:                      # the proof stands without this column
        current = {"error": type(failure).__name__}

    comparison = []
    for row in rows:
        payload = row["payload"]
        observed = payload.get("observation_date")
        now_value = current.get(observed) if isinstance(current, dict) else None
        first = payload.get("value")
        entry = {
            "observation_date": observed,
            "source_as_of_utc": row["source_as_of_utc"],
            "first_published_value": first,
            "first_serving_vintage_date": payload.get("vintage_date"),
            "current_value": now_value,
            "vintage_label": row["vintage"],
        }
        if isinstance(first, (int, float)) and isinstance(now_value, (int, float)):
            entry["revised_by"] = round(now_value - first, 6)
            entry["revised_by_relative"] = round((now_value - first) / first, 8) if first else None
        comparison.append(entry)
        print(f"   {observed}  first={first} (vintage {payload.get('vintage_date')})  "
              f"current={now_value}  label={row['vintage']}", flush=True)

    document = {
        "ran_utc": started.isoformat().replace("+00:00", "Z"),
        "finished_utc": finished.isoformat().replace("+00:00", "Z"),
        "elapsed_seconds": round((finished - started).total_seconds(), 1),
        "database": args.db,
        "source_id": ing.source_id,
        "as_of_rule": ing.as_of_rule,
        "requires_original_vintage": requires_original_vintage(ing.ref, ing.transformation),
        "requested_dates": list(dates),
        "backfill": {
            "vintage": result.vintage,
            "admitted": list(result.admitted),
            "skipped": list(result.skipped),
            "refused": [list(pair) for pair in result.refused],
            "failed": [list(pair) for pair in result.failed],
            "fetches": result.fetches,
            "counts": result.counts,
        },
        "stored": rows,
        "revision": comparison,
        "current_values_endpoint": FRED_CSV,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"-- written to {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
