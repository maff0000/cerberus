import json, sqlite3, urllib.request, urllib.error, time
from datetime import datetime, timezone, timedelta
UA = "Mozilla/5.0 (compatible; cerberus-ingest/1.0)"
stored, plain = {}, {}
c = sqlite3.connect("file:/srv/cerberus/wo117-data/wo117_historical.sqlite?mode=ro", uri=True)
for (p,) in c.execute('select payload from raw_reading where source_id="yahoo.GC=F.history"'):
    d = json.loads(p); stored[d["observation_date"]] = d["value"]
for (p,) in c.execute('select payload from raw_reading where source_id="yahoo.GC=F"'):
    d = json.loads(p); plain[d["observation_date"]] = d["value"]
p1 = int(datetime(2000, 8, 25, tzinfo=timezone.utc).timestamp())
p2 = int(datetime(2025, 6, 3, tzinfo=timezone.utc).timestamp())
u = f"https://query1.finance.yahoo.com/v8/finance/chart/GC%3DF?period1={p1}&period2={p2}&interval=1d"
for attempt in range(8):
    try:
        raw = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=90).read()
        break
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, "retry in", 60 * (attempt + 1), flush=True); time.sleep(60 * (attempt + 1))
else:
    raise SystemExit("Yahoo kept refusing")
j = json.loads(raw)["chart"]["result"][0]
off = j["meta"].get("gmtoffset", 0)
live = {}
for ts, cl in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]):
    if cl is not None:
        live[(datetime.fromtimestamp(ts, timezone.utc) + timedelta(seconds=off)).date().isoformat()] = cl
common = sorted(set(stored) & set(live))
bad = [(d, stored[d], live[d]) for d in common if abs(stored[d] - live[d]) > 1e-6 * max(1, abs(live[d]))]
print("live rows", len(live), "| stored", len(stored), "| compared", len(common), "| mismatch", len(bad), bad[:5])
print("stored dates absent from the live pull:", len(set(stored) - set(live)), sorted(set(stored) - set(live))[:5])
both = sorted(set(stored) & set(plain))
print("vs the yahoo.GC=F rows already in the store: common", len(both),
      "| differ", sum(1 for d in both if stored[d] != plain[d]))
for d in ["2000-08-30", "2008-09-15", "2011-09-05", "2020-03-16", "2022-03-08", "2025-04-03", "2025-05-30"]:
    print(d, "stored", stored.get(d), "| live", live.get(d))
