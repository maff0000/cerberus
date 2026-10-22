"""Whole-population completeness of the WO-1.17 store, re-derived from the store and the live calendars.

For each of the 36 rows: the date list the driver itself asks for (row_dates over the 8 episodes), the
key each date would be admitted under (as_of_for), and whether that key is in raw_reading. Read-only.
"""
import json, sqlite3, sys
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, "tools/backfill")
import wo117_run as R
from ingestion.adapters import as_of_for
from ingestion.backfill import format_utc

DB, OUT = sys.argv[1], sys.argv[2]
db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
held = defaultdict(set)
for s, t in db.execute("select source_id, source_as_of_utc from raw_reading"):
    held[s].add(t)
now = datetime.now(timezone.utc)
cache, out = {}, []
for ing in sorted(R.backfillable_population(), key=lambda i: (R.route(i), i.source_id)):
    dates, _ = R.row_dates(ing, R.EPISODES, cache=cache)
    missing = [d for d in dates
               if format_utc(as_of_for(d, ing.as_of_rule, now)) not in held[ing.source_id]]
    out.append({"source_id": ing.source_id, "route": R.route(ing), "expected": len(dates),
                "present": len(dates) - len(missing), "missing": missing})
    print(f"{R.route(ing):18} {ing.source_id:24} expected {len(dates):5} present {len(dates)-len(missing):5} "
          f"missing {len(missing):4}", flush=True)
json.dump(out, open(OUT, "w"))
for route in sorted({r["route"] for r in out}):
    rs = [r for r in out if r["route"] == route]
    print(route, "rows", len(rs), "expected", sum(r["expected"] for r in rs),
          "present", sum(r["present"] for r in rs), "missing", sum(len(r["missing"]) for r in rs))
print("TOTAL rows", len(out), "expected", sum(r["expected"] for r in out),
      "present", sum(r["present"] for r in out), "missing", sum(len(r["missing"]) for r in out))
