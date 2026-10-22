"""Differential: the REAL pass (config C) vs MY harness state machine configured as the PR's intent, same days, same trend flags.
Where they differ the REAL code is the truth; the difference is what my WO-1.3b-II harness did not model."""
import sys, os, json, collections, datetime as dt
SP = os.environ["R2_SCRATCH"]
sys.path.insert(0, os.path.join(SP, "harness"))
import cerberus_replay as C, engine_run as E, eval_count as EC
D = dt.date.fromisoformat
P = C.Panel(); rows = E.build_rows(P)
S = json.load(open(os.path.join(SP, "live", "runs_summary.json")))["C_avail_liveshaped"]
trend = {D(d): v["trend"] for d, v in S.items()}
cc = EC.with_count(rows, .8, 2)           # count v2 (FAST2, T=.8, k=2) as a master-like 0/1 signal, harness idiom
# harness: count_v2 enters as an ALARM-eligible master at 1.0 -> reproduces rule 3 (count>=2 -> ALARM)
p = E.Params(stress={"volatility_master": .70, "count_v2": .99}, warn={"count_v2": 9}, b_mid=9, b_high=9, trend=trend, lock=True)
hs = E.run_machine(cc, P.days, p)
real = {D(d): v["eq"] for d, v in S.items()}
mismatch = collections.Counter(); byep = collections.defaultdict(list)
for d in P.days:
    h = hs[d]["state"]; r = real[d]
    if h != r:
        mismatch[(h, r)] += 1; byep[P.win[d]].append(d)
print("days compared:", len(P.days), " exact agreement:", sum(1 for d in P.days if hs[d]['state'] == real[d]))
print("harness -> real mismatches:", dict(mismatch))
for ep, ds in byep.items(): print(" ", ep, len(ds), "days, first", ds[0], "last", ds[-1])
