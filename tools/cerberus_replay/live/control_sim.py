"""PR #14's REAL resolver + REAL lock query + REAL trend test, driven day by day over the CONTINUOUS control series (1990-2026,
NOT the store).  Inputs available on the control: vix_level, vix_term_structure, yield_curve_10y3m, yield_curve_10y2y, spx_vs_200dma.
No hy_oas / nfci / skew / copper_gold, so every ALARM/WATCH number here is a LOWER BOUND (missing inputs can only add stress).
Config PR = the PR as written.  Config NOCURVE = identical except the two curve indicators are removed from the count."""
import sys, os, json, datetime as dt, collections, statistics as st
SP = os.environ["R2_SCRATCH"]
REPO = os.path.join(SP, "repo_pr14", "crash-detector")
sys.path[:0] = [os.path.join(REPO, "src"), REPO, os.path.join(SP, "harness")]
from crash_detector.engine import statistics as S
from crash_detector.engine.statistics import State
from crash_detector.dials.scores import Contribution
from evaluator.history_store import MachineStateHistoryStore
from evaluator import resolve as R
from evaluator.trend import trend_confirmed_from_closes
import control as K
import single_master as SM
X = K.load()
B = json.load(open(os.path.join(REPO, "deploy/indicator-scaling.json")))["equity_crash"]
def sc(i, x):
    b = B[i]; s = (x - b["calm"]) / (b["stress"] - b["calm"]); return 0.0 if s < 0 else 1.0 if s > 1 else s
spx = X["spx"]; days = [d for d in sorted(spx) if d >= dt.date(1990, 1, 2) and d in X["vix"] and d in X["t10y3m"] and d in X["t10y2y"]]
alld = sorted(spx); closes = [spx[d] for d in alld]; pos = {d: i for i, d in enumerate(alld)}
EQ = "equity_crash"
MASTERS = {m.master_id: m for m in S.EQUITY_CRASH_MASTERS}

def day_inputs(d):
    i = pos[d]
    c = {"vix_level": sc("vix_level", X["vix"][d]),
         "yield_curve_10y3m": sc("yield_curve_10y3m", X["t10y3m"][d]), "yield_curve_10y2y": sc("yield_curve_10y2y", X["t10y2y"][d])}
    if d in X["vix3m"]: c["vix_term_structure"] = sc("vix_term_structure", X["vix"][d] / X["vix3m"][d])
    if i >= 199: c["spx_vs_200dma"] = sc("spx_vs_200dma", (closes[i] / (sum(closes[i - 199:i + 1]) / 200) - 1) * 100)
    return c

def run(drop_curve_from_count):
    saved = S.COUNT_INDICATOR_IDS
    if drop_curve_from_count:
        S.COUNT_INDICATOR_IDS = tuple(x for x in saved if not x.startswith("yield_curve"))
    try:
        h = MachineStateHistoryStore(":memory:"); out = {}
        for d in days:
            c = day_inputs(d)
            contribs = tuple(Contribution(source_id=k, category="x", weight=1.0, contribution=v) for k, v in sorted(c.items()))
            scaled = c
            ms = []
            for mid, comps in (("volatility_master", ("vix_level", "vix_term_structure")), ("curve_master", ("yield_curve_10y3m", "yield_curve_10y2y"))):
                m = MASTERS[mid]
                avail = [scaled[x] for x in comps if x in scaled]
                if not avail: continue
                if mid == "volatility_master" and len(avail) < 2:   # pre-VIX3M: VIX level alone (calibration mode, as in WO-1.3b-II)
                    pass
                ms.append(S.MasterScore(master_id=mid, dial_id=EQ, score=max(avail), warning_threshold=m.warning_threshold,
                                        stress_threshold=m.stress_threshold, exit_threshold=m.exit_threshold, alarm_eligible=m.alarm_eligible))
            top = max(ms, key=lambda m: m.score)
            ac = S.Acute(dial_id=EQ, score=top.score, from_master_id=top.master_id, masters=tuple(ms))
            cnt = S.count_for_one_dial(contribs)
            i = pos[d]
            tr = trend_confirmed_from_closes(closes[max(0, i - 259):i + 1])
            armed = h.alarm_lock_armed(EQ)
            row = R.official_state_for_dial(history=h.recent(EQ, limit=20), as_of=dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc),
                                            breadth=.3, acute=ac, count=cnt, trend_confirmed=tr, alarm_lock_armed=armed)
            h.append(row, written_utc=dt.datetime.now(dt.timezone.utc))
            out[d] = dict(state=row.machine_state.name, cand=row.candidate_state.name, count=cnt.count, trend=tr, armed=armed,
                          vol=next((m.score for m in ms if m.master_id == "volatility_master"), None),
                          curve=next((m.score for m in ms if m.master_id == "curve_master"), None))
        return out
    finally:
        S.COUNT_INDICATOR_IDS = saved

def spans(out, which):
    res, cur = [], None
    for d in days:
        if out[d]["state"] in which:
            cur = [d, d] if cur is None else [cur[0], d]
        elif cur: res.append(tuple(cur)); cur = None
    if cur: res.append(tuple(cur))
    return res

decl = SM.clusters(SM.zigzag_declines(sorted(spx), spx, 0.15))
yrs = (days[-1] - days[0]).days / 365.25
res = {}
for name, drop in (("PR", False), ("NOCURVE", True)):
    o = run(drop); res[name] = o
    al = sum(1 for d in days if o[d]["state"] == "ALARM"); dn = sum(1 for d in days if o[d]["state"] in ("ALARM", "WATCH", "UNKNOWN"))
    print(f"\n== {name}: ALARM days {al} ({al/len(days):.1%}), DENY(ALARM|WATCH) days {dn} ({dn/len(days):.1%}) over {len(days)} days / {yrs:.1f}y")
    caught = 0
    for p, t in decl:
        fa = next((d for d in days if p - dt.timedelta(days=30) <= d <= t and o[d]["state"] == "ALARM"), None)
        ok = fa is not None; caught += ok
    print(f"   declines >=15% (clustered): {len(decl)}, ALARM at/before trough in {caught}")
    print("   ALARM spans >= 60 trading days:")
    for a, b in spans(o, ("ALARM",)):
        n = sum(1 for d in days if a <= d <= b)
        if n >= 60: print(f"     {a} -> {b}  {n}d  S&P {spx[b]/spx[a]-1:+.1%}")
    print("   DENY spans >= 250 trading days (ALARM|WATCH, contiguous):")
    for a, b in spans(o, ("ALARM", "WATCH")):
        n = sum(1 for d in days if a <= d <= b)
        if n >= 250: print(f"     {a} -> {b}  {n}d  ({(b-a).days/365.25:.1f}y)  S&P {spx[b]/spx[a]-1:+.1%}")
    rec = [d for d in days if o[d]["state"] == "RECOVERY"]
    print(f"   RECOVERY days {len(rec)}; first RECOVERY dates:", [str(r) for r in rec[:1]], "...")
import pickle; pickle.dump({k: {str(d): v for d, v in o.items()} for k, o in res.items()}, open(os.path.join(SP, "live", "control_sim.pkl"), "wb"))
# 2022-24 detail
o = res["PR"]
print("\nPR config around the 2022-2025 inversion (first date of each state change):")
prev = None
for d in days:
    if d < dt.date(2022, 6, 1): continue
    s = o[d]["state"]
    if s != prev: print("  ", d, s, f"count={o[d]['count']} curve={o[d]['curve']:.2f} vol={o[d]['vol']:.2f} trend={o[d]['trend']} armed={o[d]['armed']}"); prev = s
