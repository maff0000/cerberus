"""One collection pass over every due ingredient, through the core's own ``collect()``.

    PYTHONPATH=src:. python3 -m ingestion.run --db /path/to/raw.sqlite [--force] [--only ID ...]

Exit status is non-zero if ANY ingredient did not end ``OK`` — a half-fed detector must not
look like a healthy cron job. Nothing here computes or scores; it fetches, validates at the
boundary and records.
"""

from __future__ import annotations

import argparse
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone

from crash_detector.collectors import DelayKind, RetryPolicy, collect
from crash_detector.observations import OK

from ingestion.adapters import ManualEntryAdapter
from ingestion.catalog import INGREDIENTS, Ingredient, build_adapter
from ingestion.store import SqliteStore

#: A failed or malformed last attempt is retried on the next pass after this long,
#: regardless of the poll interval, so an outage is not stretched into a 6-24h silence.
RETRY_AFTER = timedelta(minutes=15)
#: Courtesy gap between sources: Yahoo rate-limits bursts (HTTP 429) and FRED resets them.
PACING_SECONDS = 1.5
POLICY = RetryPolicy(max_attempts=2, timeout_seconds=20.0, backoff_seconds=4.0)


def is_due(store: SqliteStore, ing: Ingredient, now: datetime) -> bool:
    last = store.last_attempt(ing.source_id)
    if last is None:
        return True
    when, outcome = last
    return now - when >= (timedelta(seconds=ing.poll_seconds) if outcome == "OK" else RETRY_AFTER)


def run_once(store: SqliteStore, *, force: bool = False, only: tuple = (), pace: float = PACING_SECONDS) -> list[dict]:
    summary: list[dict] = []
    run_id = "ingest-" + uuid.uuid4().hex[:12]
    clock = lambda: datetime.now(timezone.utc)  # noqa: E731
    first = True
    for ing in INGREDIENTS:
        if only and ing.source_id not in only:
            continue
        now = clock()
        if ing.kind == "manual":
            # Hand-entered (WO-1.7): there is nothing to poll. Registered so the store knows the source; its
            # readings arrive only through ``ingestion.manual`` and it ages like any other.
            store.register(ing.source_id, ManualEntryAdapter.adapter_id, ing.poll_seconds, ing.stands_for,
                           ing.declared_feed, ing.serves, now)
            continue
        adapter = build_adapter(ing, clock)
        store.register(ing.source_id, adapter.adapter_id, ing.poll_seconds, ing.stands_for,
                       ing.declared_feed, ing.serves, now)
        if not force and not is_due(store, ing, now):
            summary.append({"source_id": ing.source_id, "state": "NOT_DUE"})
            continue
        if not first:
            time.sleep(pace)
        first = False
        try:
            result = collect(adapter, policy=POLICY, sink=store, ledger=store, collector_run_id=run_id,
                             started_utc=clock(), delay=DelayKind.WALL_CLOCK)
        except Exception as failure:  # recorded in the summary and the exit code, never swallowed
            summary.append({"source_id": ing.source_id, "state": "RUNNER_ERROR", "error": type(failure).__name__})
            continue
        outcome = result.final_outcome
        summary.append({
            "source_id": ing.source_id,
            "state": type(outcome).__name__.upper(),
            "attempts": result.attempts_made,
            "new_reading": bool(result.reading_admitted),
            **({"as_of": outcome.source_as_of_utc.isoformat(), "value": outcome.payload.get("value")}
               if isinstance(outcome, OK) else {}),
        })
    return summary


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--force", action="store_true", help="ignore poll intervals")
    parser.add_argument("--only", nargs="*", default=[])
    args = parser.parse_args(argv)
    with SqliteStore(args.db) as store:
        summary = run_once(store, force=args.force, only=tuple(args.only))
    bad = 0
    for row in summary:
        line = f"{row['source_id']:26} {row['state']:12}"
        if "value" in row:
            line += f" as_of={row['as_of'][:10]} value={row['value']} new={row['new_reading']}"
        print(line)
        bad += row["state"] not in ("OK", "NOT_DUE")
    print(f"-- {len(summary)} sources, {bad} not OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
