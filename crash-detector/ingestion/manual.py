"""Hand-entry of the one input that has no feed: the SLOOS NDFI leg (CERBERUS WO-1.7).

    python3 -m ingestion.manual sloos-ndfi --survey-date 2026-07-01 --value 12.5            # preview only
    python3 -m ingestion.manual sloos-ndfi --survey-date 2026-07-01 --value 12.5 --confirm  # record it
    python3 -m ingestion.manual list

In the live stack:
    docker exec cerberus-live-cd-live-collector-1 python3 -B -m ingestion.manual sloos-ndfi ...

WHAT THIS IS. ``sloos_bank_lending`` has two legs. The C&I leg is fetched (FRED DRTSCILM). The other, the Fed's SLOOS
Table 2 Q14 (the NDFI question), averaged over its 5 sub-categories, is published only as a PDF/HTML table: there is no
machine-readable feed and there will not be one. This is a structural acceptance of a manual process, not a gap to
engineer around: nothing here fetches, scrapes or guesses a figure.

HOW IT IS TREATED. The entered value goes through the SAME boundary as a fetched one (``ManualEntryAdapter`` ->
``collect()`` -> closed response schema -> observation row -> append-only reading ledger), so downstream it IS a reading:
it is aged by the indicator's 120-day relevance window from its SURVEY date, and once that passes the indicator reads
STALE and drops out of the dial exactly as a dead feed would. Nobody has to remember to expire it. Until the first entry
the indicator reads MISSING ("awaiting manual entry").

WHAT YOU ENTER.
* ``--survey-date``: the survey's quarter start, using FRED's convention for DRTSCILM: 01-01, 04-01, 07-01 or 10-01
  (the July 2026 survey is 2026-07-01). Anything else is refused: it is the date the value is aged from.
* ``--value``: net percent of banks tightening, in [-100, 100]: the average of the 5 sub-categories, worked out by you.
* Nothing is recorded without ``--confirm``; the default is a preview.
* A survey date that already has a value is refused. The ledger is append-only (a first print is never replaced), so
  CHECK THE NUMBER BEFORE --confirm: there is no edit. A genuine correction is an operator act on the store.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sqlite3
import sys
import uuid
from datetime import date, datetime, timezone

from crash_detector.collectors import DelayKind, RetryPolicy, collect
from crash_detector.observations import OK

from ingestion.adapters import ManualEntryAdapter
from ingestion.catalog import INGREDIENTS, MANUAL_SLOOS_NDFI
from ingestion.store import SqliteStore

POLICY = RetryPolicy(max_attempts=1, timeout_seconds=5.0, backoff_seconds=0.0)
QUARTER_START_MONTHS = (1, 4, 7, 10)
EARLIEST_SURVEY = date(1990, 1, 1)  # FRED DRTSCILM begins 1990; earlier is a typo and the ledger has no edit
ISO_EXTENDED = re.compile(r"\d{4}-\d{2}-\d{2}")


class EntryRefused(Exception):
    """The entry is not acceptable. The message says why and nothing was recorded."""


def validate(survey_date: str, value: float, today: date) -> tuple:
    try:
        if not ISO_EXTENDED.fullmatch(survey_date):
            raise ValueError(survey_date)
        day = date.fromisoformat(survey_date)
    except ValueError:
        raise EntryRefused(f"--survey-date {survey_date!r} is not an ISO date (YYYY-MM-DD)") from None
    if day.day != 1 or day.month not in QUARTER_START_MONTHS:
        raise EntryRefused(f"--survey-date {survey_date} is not a quarter start (YYYY-01-01, -04-01, -07-01, -10-01)")
    if day < EARLIEST_SURVEY:
        raise EntryRefused(f"--survey-date {survey_date} is before {EARLIEST_SURVEY} (the series starts there)")
    if day > today:
        raise EntryRefused(f"--survey-date {survey_date} is in the future")
    if type(value) is not float or not math.isfinite(value) or not -100.0 <= value <= 100.0:
        raise EntryRefused(f"--value {value!r} is not a finite net percentage in [-100, 100]")
    return day.isoformat(), value


def record(store: SqliteStore, survey_date: str, value: float, now: datetime) -> dict:
    """Validate and record one entry. Returns a summary; raises :class:`EntryRefused` if it is not acceptable."""
    survey_date, value = validate(survey_date, value, now.date())
    ing = next(i for i in INGREDIENTS if i.source_id == MANUAL_SLOOS_NDFI)
    for row in store._db.execute("SELECT payload FROM raw_reading WHERE source_id=?", (ing.source_id,)):
        if json.loads(row[0]).get("observation_date") == survey_date:
            raise EntryRefused(f"{survey_date} already has a recorded value; the ledger is append-only, nothing changed")
    clock = lambda: now  # noqa: E731
    adapter = ManualEntryAdapter(survey_date, value, source_id=ing.source_id, as_of_rule=ing.as_of_rule,
                                 unit=ing.unit, clock=clock)
    store.register(ing.source_id, adapter.adapter_id, ing.poll_seconds, ing.stands_for, ing.declared_feed,
                   ing.serves, now)
    result = collect(adapter, policy=POLICY, sink=store, ledger=store, collector_run_id="manual-" + uuid.uuid4().hex[:12],
                     started_utc=now, delay=DelayKind.WALL_CLOCK)
    outcome = result.final_outcome
    if not isinstance(outcome, OK) or not result.reading_admitted:
        raise EntryRefused(f"the boundary did not admit the entry ({type(outcome).__name__})")
    return {"survey_date": survey_date, "value": value, "as_of": outcome.source_as_of_utc.isoformat()}


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                     allow_abbrev=False)
    parser.add_argument("--db", default=os.environ.get("CD_DB_PATH"), help="ingestion store (default $CD_DB_PATH)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    entry = sub.add_parser("sloos-ndfi", help="enter the SLOOS Table 2 Q14 NDFI figure for one survey",
                          allow_abbrev=False)
    entry.add_argument("--survey-date", required=True)
    entry.add_argument("--value", required=True, type=float)
    entry.add_argument("--confirm", action="store_true", help="actually record it (default: preview)")
    sub.add_parser("list", help="show the hand-entered values on record")
    args = parser.parse_args(argv)
    if not args.db:
        print("REFUSED: no --db and CD_DB_PATH is unset.", file=sys.stderr)
        return 2
    now = datetime.now(timezone.utc)
    if args.cmd == "list":
        try:
            with SqliteStore(args.db, read_only=True) as store:
                rows = store.recent_readings(MANUAL_SLOOS_NDFI, 100)
        except sqlite3.Error as why:
            print(f"REFUSED: cannot read {args.db}: {why}", file=sys.stderr)
            return 2
        for payload in rows:
            print(f"{payload['observation_date']}  {payload['value']}  ({payload['unit']})")
        print(f"-- {len(rows)} hand-entered SLOOS NDFI value(s)")
        return 0
    try:
        survey_date, value = validate(args.survey_date, args.value, now.date())
        if not args.confirm:
            # The preview must not promise what --confirm will refuse: open the store read-only and look for the date.
            # A store that does not exist yet cannot hold a duplicate; --confirm will create it.
            if os.path.exists(args.db):
                with SqliteStore(args.db, read_only=True) as store:
                    if any(p.get("observation_date") == survey_date for p in store.recent_readings(MANUAL_SLOOS_NDFI, 1000)):
                        raise EntryRefused(f"{survey_date} already has a recorded value; --confirm would be refused")
            print(f"PREVIEW ONLY, nothing recorded: SLOOS NDFI survey {survey_date} = {value} net % tightening.\n"
                  "Re-run with --confirm to record it. There is no edit afterwards.")
            return 0
        with SqliteStore(args.db) as store:
            done = record(store, survey_date, value, now)
    except sqlite3.Error as why:
        print(f"REFUSED: cannot write {args.db}: {why}", file=sys.stderr)
        return 2
    except EntryRefused as why:
        print(f"REFUSED: {why}", file=sys.stderr)
        return 2
    print(f"RECORDED: SLOOS NDFI survey {done['survey_date']} = {done['value']} (ages from {done['as_of'][:10]}; "
          "120-day relevance window)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
