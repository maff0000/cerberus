"""Classify every not-admitted date of the 9-row re-run TWO independent ways.

 A. through the real fixed adapter (the token it records: vintage_archive_floor / vintage_too_distant ...)
 B. from raw FRED REST bodies with the rule re-derived here, sharing no code with the adapter:
      first_vintage = earliest realtime_start carrying a value for the observation
      floor         = earliest vintage date the series has at all (/vintagedates, asc, limit 1)
      first_vintage == floor                      -> vintage_archive_floor
      first_vintage <  observation_date           -> vintage_floor
      first_vintage - observation_date > 365 days -> vintage_too_distant
      no value in any vintage                     -> EMPTY
      otherwise                                   -> ADMISSIBLE   (the adapter should have admitted it)
"""
import json, os, sys, time, urllib.request, urllib.parse
from collections import Counter, defaultdict
from datetime import date, datetime, timezone

from crash_detector.collectors.adapter import AdapterFetchError
from ingestion import adapters as A
from ingestion.catalog import INGREDIENTS

KEY = os.environ["FRED_API_KEY"].strip()
RECORD = sys.argv[1]
OUT = sys.argv[2]
ONLY = set(sys.argv[3:])
TODAY = datetime.now(timezone.utc).date()
BASE = "https://api.stlouisfed.org/fred/series/"


def raw(path, **p):
    time.sleep(0.6)
    q = urllib.parse.urlencode(list(p.items()) + [("file_type", "json"), ("api_key", KEY)])
    for attempt in range(14):
        try:
            return json.loads(urllib.request.urlopen(BASE + path + "?" + q, timeout=90).read())
        except Exception as failure:
            print('RETRY', path, p.get('observation_start'), attempt, type(failure).__name__, getattr(failure, 'code', ''), flush=True)
            time.sleep(min(30 * (attempt + 1), 120))
    raise RuntimeError("raw GET failed 14x")


def ing(s):
    return next(i for i in INGREDIENTS if i.source_id == s)


floors_adapter = A.FredArchiveFloors(KEY, clock=lambda: datetime.now(timezone.utc))
record = json.load(open(RECORD))
result = {}
disagree = []
for row in record["rows"]:
    sid = row["source_id"]
    if not row["failed"] or (ONLY and sid not in ONLY):
        continue
    i = ing(sid)
    series, units = i.ref, (i.transformation or "lin")
    floor = date.fromisoformat(raw("vintagedates", series_id=series, realtime_start="1776-07-04",
                                   realtime_end=str(TODAY), sort_order="asc", limit="1")["vintage_dates"][0])
    tally_a, tally_b, per = Counter(), Counter(), []
    for d, klass in row["failed"]:
        # A. the adapter
        ad = A.FredVintageAdapter(i.ref, i.transformation, d, api_key=KEY, source_id=sid,
                                  as_of_rule=i.as_of_rule, unit=i.unit,
                                  clock=lambda: datetime.now(timezone.utc), archive_floors=floors_adapter)
        try:
            p = ad._acquire(300.0)
            tok = p["malformed"] if "malformed" in p else ("EMPTY" if "value" not in p else "ADMITTED")
        except AdapterFetchError as e:
            tok = "FETCH:" + e.error_class
        # B. raw, independent. A transformed series (pc1) is a function of this observation AND the
        #    one a year earlier, and the server refuses a single-day window for it (HTTP 400), so its
        #    first servable vintage is derived from the underlying levels: the LATER of the two
        #    observations' first publication.
        def first_pub(obs):
            body = raw("observations", series_id=series, units="lin", observation_start=obs,
                       observation_end=obs, realtime_start="1776-07-04", realtime_end=str(TODAY))
            got = sorted(o["realtime_start"] for o in body["observations"]
                         if o["date"] == obs and o["value"] != ".")
            return date.fromisoformat(got[0]) if got else None
        needed = [d] if units == "lin" else [d, str(date.fromisoformat(d).replace(year=date.fromisoformat(d).year - 1))]
        firsts = [first_pub(x) for x in needed]
        served = [str(max(firsts))] if all(f is not None for f in firsts) else []
        if not served:
            ind = "EMPTY"
        else:
            fv, od = date.fromisoformat(served[0]), date.fromisoformat(d)
            ind = ("vintage_archive_floor" if fv == floor else "vintage_floor" if fv < od
                   else "vintage_too_distant" if (fv - od).days > 365 else "ADMISSIBLE")
        tally_a[tok] += 1
        tally_b[ind] += 1
        per.append([d, klass, tok, ind, served[0] if served else None])
        if tok != ind:
            disagree.append([sid, d, tok, ind])
    result[sid] = {"archive_floor": str(floor), "adapter_tokens": dict(tally_a),
                   "independent_rule": dict(tally_b), "dates": per}
    json.dump(result, open(OUT, "w"))
    print(sid, "floor", floor, "adapter", dict(tally_a), "independent", dict(tally_b), flush=True)
result["_disagreements"] = disagree
json.dump(result, open(OUT, "w"))
print("DISAGREEMENTS:", len(disagree), disagree[:10], flush=True)
