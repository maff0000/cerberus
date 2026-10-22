import sys, os, json, datetime as dt, sqlite3, tempfile, collections
SP = os.environ["R2_SCRATCH"]
sys.path.insert(0, os.path.join(SP, "live")); sys.path.insert(0, os.path.join(SP, "harness"))
import live_replay as L
from ingestion.store import SqliteStore
from ingestion.wiring import build_wiring, derive_from_store
from evaluator.trend import trend_confirmed_from_closes
import control as K, numpy as np

print("--- (a) item 7: the two defective ratios are out of the live wiring")
w = build_wiring()
print("   breadth_rsp_spy live:", "breadth_rsp_spy" in w.live_ids, "| credit_stress_hyg_lqd live:", "credit_stress_hyg_lqd" in w.live_ids)

print("--- (b) trend: PR evaluator.trend vs MY eval_lock.trend on the control S&P (every day with >=220 closes)")
spx = K.yahoo("gspc"); alld = sorted(spx); cl = [spx[d] for d in alld]
cs = np.cumsum([0] + cl); ma = {}
for i, d in enumerate(alld):
    if i >= 199: ma[d] = (cs[i + 1] - cs[i - 199]) / 200
mism = n = 0
for i, d in enumerate(alld):
    if i < 219: continue
    mine = d in ma and alld[i - 20] in ma and spx[d] > ma[d] and ma[d] / ma[alld[i - 20]] - 1 >= -0.0025
    theirs = trend_confirmed_from_closes(cl[max(0, i - 259):i + 1])
    n += 1; mism += (mine != theirs)
print(f"   {n} days, {mism} disagreements")

print("--- (c) why the monetary dial is UNKNOWN under the real pass on the store: derived indicators that cannot be computed")
rows = L.load_rows()
wd = tempfile.mkdtemp(dir=SP); raw = os.path.join(wd, "r.sqlite"); SqliteStore(raw).close()
c = sqlite3.connect(raw, isolation_level=None)
c.execute("INSERT INTO raw_observation (source_id,adapter_id,collector_run_id,attempt_number,requested_utc,observed_utc,outcome) VALUES ('r','r','r',1,'x','x','OK')")
d = dt.date(2022, 9, 30)
for av, sid, asof, payload, adm, vint in rows:
    if av <= d: c.execute("INSERT OR IGNORE INTO raw_reading (source_id,source_as_of_utc,payload,observation_id,admitted_utc,vintage) VALUES (?,?,?,1,?,?)", (sid, asof, payload, adm, vint))
with SqliteStore(raw, read_only=True) as rs:
    for k, v in sorted(derive_from_store(rs, w).items()):
        print("   ", k, "->", v if isinstance(v, str) else f"OK {v.value:.4g}")
