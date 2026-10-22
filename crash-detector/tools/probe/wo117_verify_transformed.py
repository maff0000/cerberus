"""Read-only: verify every ADMITTED reading of the three transformed (pc1) rows against FRED, by a
sequential scan that does not assume the bisection's monotonicity.

For each stored reading (observation_date, vintage_date, value):
  scan FRED's vintage dates from the observation date upward, probing units=pc1 at ONE vintage at a time
  (single-vintage windows are accepted for pc1), and take the FIRST vintage that serves a value.
  Compare vintage and value with what the store holds.
"""
import json, os, sqlite3, sys, time, urllib.request, urllib.parse, urllib.error
from datetime import date

KEY = os.environ["FRED_API_KEY"].strip()
DB, OUT = sys.argv[1], sys.argv[2]
B = "https://api.stlouisfed.org/fred/series/"
TODAY = date.today().isoformat()


def get(path, **p):
    q = urllib.parse.urlencode(list(p.items()) + [("file_type", "json"), ("api_key", KEY)])
    for attempt in range(14):
        time.sleep(0.6)
        try:
            return json.loads(urllib.request.urlopen(B + path + "?" + q, timeout=90).read())
        except Exception as failure:
            print("RETRY", path, attempt, type(failure).__name__, getattr(failure, "code", ""), flush=True)
            time.sleep(min(30 * (attempt + 1), 120))
    raise RuntimeError("GET failed 14x")


db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
result, mismatches = {}, []
for sid in ("fred.CPIAUCSL.pc1", "fred.M2SL.pc1", "fred.PCEPILFE.pc1"):
    series = sid[5:].split(".")[0]
    vd = get("vintagedates", series_id=series, realtime_start="1776-07-04", realtime_end=TODAY,
             sort_order="asc", limit="10000")["vintage_dates"]
    rows = [json.loads(p) for (p,) in db.execute("select payload from raw_reading where source_id=?", (sid,))]
    ok = bad = 0
    for doc in sorted(rows, key=lambda d: d["observation_date"]):
        obs = doc["observation_date"]
        found = None
        for v in (x for x in vd if x >= obs):
            r = get("observations", series_id=series, units="pc1", observation_start=obs,
                    observation_end=obs, realtime_start=v, realtime_end=v)
            hit = [o["value"] for o in r.get("observations", []) if o["date"] == obs and o["value"] != "."]
            if hit:
                found = (v, hit[0])
                break
        same = (found is not None and found[0] == doc["vintage_date"]
                and abs(float(found[1]) - float(doc["value"])) < 1e-9)
        ok += same
        bad += not same
        if not same:
            mismatches.append([sid, obs, doc["vintage_date"], doc["value"], list(found) if found else None])
    result[sid] = {"stored": len(rows), "match": ok, "mismatch": bad}
    print(sid, result[sid], flush=True)
    json.dump({"rows": result, "mismatches": mismatches}, open(OUT, "w"))
print("MISMATCHES", len(mismatches), mismatches[:10], flush=True)
