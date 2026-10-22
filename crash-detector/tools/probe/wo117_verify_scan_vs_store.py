"""Read-only: did the scan refactor preserve what the bisection admitted?

For every STORED reading of the three transformed rows, re-derive it LIVE through the new
FredVintageAdapter (the scan) and compare its payload - value and vintage_date - with the stored one.
Nothing is written to the store.
"""
import json, os, sqlite3, sys, time
from collections import Counter
from datetime import datetime, timezone

from crash_detector.collectors.adapter import AdapterFetchError
from ingestion import adapters as A
from ingestion.catalog import INGREDIENTS

KEY = os.environ["FRED_API_KEY"].strip()
DB, OUT = sys.argv[1], sys.argv[2]
clock = lambda: datetime.now(timezone.utc)


def paced(url, timeout, headers=None):
    time.sleep(0.5)
    for attempt in range(8):
        try:
            return A.http_get(url, timeout, headers)
        except AdapterFetchError as failure:
            print("RETRY", failure.error_class, failure.http_status, flush=True)
            time.sleep(min(30 * (attempt + 1), 120))
    raise RuntimeError("GET failed 8x")


db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
result, mismatches, probes = {}, [], Counter()
for sid in ("fred.CPIAUCSL.pc1", "fred.M2SL.pc1", "fred.PCEPILFE.pc1"):
    ing = next(i for i in INGREDIENTS if i.source_id == sid)
    floors = A.FredArchiveFloors(KEY, clock=clock)
    rows = sorted((json.loads(p) for (p,) in db.execute(
        "select payload from raw_reading where source_id=?", (sid,))), key=lambda d: d["observation_date"])
    same = 0
    for doc in rows:
        counted = []
        def tap(url, timeout, headers=None, _c=counted):
            _c.append(url)
            return paced(url, timeout, headers)
        adapter = A.FredVintageAdapter(ing.ref, ing.transformation, doc["observation_date"], api_key=KEY,
                                       source_id=sid, as_of_rule=ing.as_of_rule, unit=ing.unit,
                                       clock=clock, archive_floors=floors, getter=tap)
        got = adapter._acquire(600.0)
        probes[sid] += len([u for u in counted if "/observations" in u])
        ok = (got.get("vintage_date") == doc["vintage_date"]
              and got.get("value") is not None and abs(got["value"] - doc["value"]) < 1e-9)
        same += ok
        if not ok:
            mismatches.append([sid, doc["observation_date"], doc["vintage_date"], doc["value"], got])
    result[sid] = {"stored": len(rows), "scan_matches_stored": same, "mismatch": len(rows) - same,
                   "observation_GETs": probes[sid], "per_date": round(probes[sid] / max(len(rows), 1), 2)}
    print(sid, result[sid], flush=True)
    json.dump({"rows": result, "mismatches": mismatches}, open(OUT, "w"))
print("MISMATCHES", len(mismatches), mismatches[:5], flush=True)
