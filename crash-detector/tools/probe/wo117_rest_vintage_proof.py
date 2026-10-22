#!/usr/bin/env python3
"""WO-1.17: prove ``FredVintageAdapter`` against the REAL FRED REST API, with the real key.

    FRED_API_KEY="$(cat /srv/cerberus-secrets/fred_api_key.secret)" \\
        PYTHONPATH=src:. python3 tools/probe/wo117_rest_vintage_proof.py \\
        --store /srv/cerberus/wo117-data/wo117_historical.sqlite \\
        --out evidence/wo117_rest_vintage_proof.json

IT IS A PROBE, NOT A GATE — the same standing as ``wo114_backfill_proof.py``. It opens ``--store``
READ-ONLY (``mode=ro``) and never writes it; it writes only the JSON record a human reads.

WHAT IT SETTLES, in six cases, each run through the production adapter and the production
``http_get`` and nothing else:

1. an UNTRANSFORMED row at a date the real backfill FAILED on (the CSV fault), resolved by one GET;
2. an UNTRANSFORMED row at dates the real backfill ALREADY ADMITTED under the old mechanism, so the
   new path is checked for being CORRECT and not merely different — value AND vintage date compared
   to what the store holds;
3. the TRANSFORMED path (the single-day bisection) at real in-scope dates, again compared to the store;
4. the first-publication CEILING, on dates older than their series' archive;
5. EMPTY, on dates the series never carried;
6. the ARCHIVE FLOOR: the figures a series' archive start restates, refused, and their neighbours past it admitted.

THE KEY. Read from ``FRED_API_KEY`` once, in ``main``, and passed to the adapter as an argument. It is
never printed, never written to the record, and never placed on a command line. The record does carry
the NAMES of response headers and the rate-limit-looking ones' values, which are the server's and
carry no credential.

COURTESY. Every GET is preceded by ``--pause`` seconds, because the transformed bisection otherwise
issues 14-17 requests back to back.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime, timezone

from crash_detector.collectors.adapter import AdapterFetchError
from ingestion.adapters import (FRED_API_BASE, FredAdapter, FredArchiveFloors, FredVintageAdapter,
                                http_get)
from ingestion.catalog import INGREDIENTS


def _clock() -> datetime:
    return datetime.now(timezone.utc)


def _ing(source_id: str):
    return next(i for i in INGREDIENTS if i.source_id == source_id)


class _CountingGetter:
    """``http_get`` with a courtesy pause, a count and a wall-clock total. Logs no URL."""

    def __init__(self, pause: float):
        self.pause, self.gets, self.seconds = pause, 0, 0.0

    def __call__(self, url, timeout, headers=None):
        time.sleep(self.pause)
        started = time.monotonic()
        try:
            return http_get(url, timeout, headers)
        finally:
            self.gets += 1
            self.seconds += time.monotonic() - started


#: One archive-floor cache for the whole probe, as the real driver keeps one per range: every case on
#: a series after the first reuses its floor. Set once in ``main``, where the key is read.
_FLOORS: list = []


def _adapter(source_id: str, observation: str, key: str, getter):
    ing = _ing(source_id)
    return FredVintageAdapter(
        ing.ref, ing.transformation, observation, api_key=key, archive_floors=_FLOORS[0],
        source_id=ing.source_id,
        as_of_rule=ing.as_of_rule, unit=ing.unit, clock=_clock, getter=getter)


def run_case(source_id: str, observation: str, key: str, pause: float) -> dict:
    getter = _CountingGetter(pause)
    adapter = _adapter(source_id, observation, key, getter)
    outcome: dict = {"source_id": source_id, "observation_date": observation,
                     "path": "bisection" if adapter._transformation else "one_get"}
    try:
        outcome["payload"] = adapter.fetch(timeout_seconds=120.0).payload
    except AdapterFetchError as failure:
        outcome["fetch_failed"] = {"error_class": failure.error_class,
                                   "http_status": failure.http_status}
    outcome["gets"] = getter.gets
    outcome["bisection_budget"] = (2 + math.ceil(math.log2(max(
        (_clock().date() - datetime.fromisoformat(observation).date()).days, 2)))
        if adapter._transformation else 1)
    outcome["seconds"] = round(getter.seconds, 2)
    return outcome


def stored(store_path: str, source_id: str) -> dict:
    """``observation_date -> (value, vintage_date)`` for every reading the real run admitted."""
    db = sqlite3.connect(f"file:{store_path}?mode=ro", uri=True)
    try:
        rows = db.execute("SELECT payload FROM raw_reading WHERE source_id = ?",
                          (source_id,)).fetchall()
    finally:
        db.close()
    out = {}
    for (payload,) in rows:
        document = json.loads(payload)
        out[document["observation_date"]] = (document["value"], document.get("vintage_date"))
    return out


def compare_with_store(source_id: str, dates: list, store_path: str, key: str, pause: float) -> list:
    held = stored(store_path, source_id)
    results = []
    for observation in dates:
        case = run_case(source_id, observation, key, pause)
        payload = case.get("payload", {})
        old_value, old_vintage = held[observation]
        case["store_value"], case["store_vintage_date"] = old_value, old_vintage
        case["value_matches_store"] = payload.get("value") == old_value
        case["vintage_matches_store"] = payload.get("vintage_date") == old_vintage
        results.append(case)
    return results


def spread(items: list, count: int) -> list:
    """``count`` items spread evenly across a sorted list, always including the first and last."""
    if len(items) <= count:
        return list(items)
    return [items[round(i * (len(items) - 1) / (count - 1))] for i in range(count)]


def csv_cross_check(source_id: str, observation: str) -> dict:
    """The SAME observation read from a DIFFERENT endpoint: ``fredgraph.csv`` (keyless, current body)."""
    ing = _ing(source_id)
    adapter = FredAdapter(ing.ref, ing.transformation, 0, observation_date=observation,
                          source_id=ing.source_id, as_of_rule=ing.as_of_rule, unit=ing.unit,
                          clock=_clock)
    return adapter.fetch(timeout_seconds=60.0).payload


def rate_limit_probe(key: str) -> dict:
    """Header NAMES of a real response, and the value of anything that looks like a limit."""
    out: dict = {}
    for label, query in (
        ("wide_window", "series_id=WALCL&observation_start=2015-06-10&observation_end=2015-06-10"
                        "&realtime_start=1900-01-01&realtime_end=2026-10-20&file_type=json"),
        ("single_day", "series_id=CPIAUCSL&units=pc1&observation_start=2015-06-01"
                       "&observation_end=2015-06-01&realtime_start=2015-07-20"
                       "&realtime_end=2015-07-20&file_type=json"),
    ):
        request = urllib.request.Request(f"{FRED_API_BASE}?{query}&api_key={key}")
        with urllib.request.urlopen(request, timeout=30) as response:
            names = sorted({name.lower() for name, _ in response.getheaders()})
            ratey = {name.lower(): value for name, value in response.getheaders()
                     if any(word in name.lower() for word in ("rate", "limit", "retry", "quota"))}
            out[label] = {"status": response.status, "header_names": names,
                          "rate_limit_like_headers": ratey}
    return out


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description="WO-1.17: prove FredVintageAdapter on the real API")
    parser.add_argument("--store", required=True, help="the real backfill store; opened READ-ONLY")
    parser.add_argument("--out", required=True, help="where to write the JSON record")
    parser.add_argument("--pause", type=float, default=0.5, help="courtesy seconds before each GET")
    args = parser.parse_args(argv)

    key = (os.environ.get("FRED_API_KEY") or "").strip()
    if not key:
        print("-- STOP: REFUSED: FRED_API_KEY is unset.")
        return 1

    _FLOORS.append(FredArchiveFloors(key, clock=_clock))
    record: dict = {"probed_utc": _clock().isoformat(), "purpose": __doc__.split("\n\n")[0],
                    "endpoint": FRED_API_BASE, "credential": "read from FRED_API_KEY; never recorded"}

    print("-- 1. failed-in-the-real-run date (WALCL 2015-06-10)", flush=True)
    walcl = run_case("fred.WALCL", "2015-06-10", key, args.pause)
    walcl["independent_csv_read"] = csv_cross_check("fred.WALCL", "2015-06-10")
    walcl["expected_from_manual_probe"] = 4468005.0
    walcl["unit"] = _ing("fred.WALCL").unit
    walcl["store_holds_any_walcl"] = len(stored(args.store, "fred.WALCL"))
    record["case_1_failed_date_untransformed"] = walcl

    print("-- 2. dates the old mechanism already admitted (BAMLH0A0HYM2)", flush=True)
    held = stored(args.store, "fred.BAMLH0A0HYM2")
    record["case_2_cross_check_untransformed"] = compare_with_store(
        "fred.BAMLH0A0HYM2", spread(sorted(held), 8), args.store, key, args.pause)

    print("-- 3. transformed bisection at real in-scope dates (CPIAUCSL.pc1)", flush=True)
    held = stored(args.store, "fred.CPIAUCSL.pc1")
    record["case_3_bisection_transformed"] = compare_with_store(
        "fred.CPIAUCSL.pc1", spread(sorted(held), 4), args.store, key, args.pause)
    # The other two transformed rows hold nothing in the store (the fault hit them), so they are
    # proven to RESOLVE, not compared.
    record["case_3_other_transformed_rows"] = [
        run_case("fred.M2SL.pc1", "2020-02-01", key, args.pause),
        run_case("fred.PCEPILFE.pc1", "2020-02-01", key, args.pause),
    ]

    print("-- 4. ceiling refusals", flush=True)
    record["case_4_ceiling"] = [
        run_case("fred.WALCL", "2002-12-18", key, args.pause),
        run_case("fred.WALCL", "2000-01-05", key, args.pause),
        run_case("fred.NCBEILQ027S", "1999-10-01", key, args.pause),
    ]
    record["case_4_non_ceiling_controls"] = [
        # WALCL's first observation is 2002-12-18, so a 2000-era date is EMPTY and not a ceiling case.
        # 1999-12-01 is not a quarter-start date, so NCBEILQ027S has no such observation: EMPTY too.
        run_case("fred.NCBEILQ027S", "1999-12-01", key, args.pause),
        # Inside the archive: a genuine first publication, admitted.
        run_case("fred.GDP", "2000-01-01", key, args.pause),
        run_case("fred.NCBEILQ027S", "2013-04-01", key, args.pause),
    ]

    print("-- 5. EMPTY", flush=True)
    record["case_5_empty"] = [
        run_case("fred.WALCL", "2015-06-13", key, args.pause),
        run_case("fred.CPIAUCSL.pc1", "2015-06-15", key, args.pause),
        run_case("fred.WALCL", "2099-01-01", key, args.pause),
    ]

    print("-- 6. archive floor (the 83 contaminated figures' fingerprint)", flush=True)
    record["case_6_archive_floor_refusals"] = [
        run_case("fred.IC4WSA", "2008-05-31", key, args.pause),    # admitted by the real re-run
        run_case("fred.WALCL", "2011-03-02", key, args.pause),     # admitted by the real re-run
        run_case("fred.NFCI", "2011-03-04", key, args.pause),      # admitted by the real re-run
        run_case("fred.PCEPILFE.pc1", "1999-12-01", key, args.pause),  # was HTTP 400, now classified
        run_case("fred.WALCL", "2011-07-06", key, args.pause),     # genuine release ON the floor: refused (declared)
    ]
    record["case_6_controls_admitted_after_the_floor"] = [
        run_case("fred.IC4WSA", "2009-05-30", key, args.pause),
        run_case("fred.WALCL", "2011-07-13", key, args.pause),
        run_case("fred.NFCI", "2011-05-27", key, args.pause),
        run_case("fred.PCEPILFE.pc1", "2000-09-01", key, args.pause),
    ]
    record["archive_floors_read"] = {
        series: _FLOORS[0].floor(series, 60.0, http_get).isoformat()
        for series in ("IC4WSA", "WALCL", "NFCI", "PCEPILFE")}

    print("-- rate-limit headers", flush=True)
    record["rate_limit_probe"] = rate_limit_probe(key)

    document = json.dumps(record, indent=2, sort_keys=True)
    assert key not in document, "the key would have leaked into the record; nothing written"
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(document + "\n")
    print(f"-- written to {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
