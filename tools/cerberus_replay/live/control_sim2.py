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


def run(k, drop_curve, lock):
    saved_ids, saved_k = S.COUNT_INDICATOR_IDS, S.PROVISIONAL_COUNT_K
    S.PROVISIONAL_COUNT_K = k
    if drop_curve:
        S.COUNT_INDICATOR_IDS = tuple(x for x in saved_ids if not x.startswith("yield_curve"))
    try:
        h = MachineStateHistoryStore(":memory:"); out = {}
        for d in days:
            c = day_inputs(d)
            contribs = tuple(Contribution(source_id=kk, category="x", weight=1.0, contribution=v) for kk, v in sorted(c.items()))
            ms = []
            for mid, comps in (("volatility_master", ("vix_level", "vix_term_structure")), ("curve_master", ("yield_curve_10y3m", "yield_curve_10y2y"))):
                m = MASTERS[mid]
                avail = [c[x] for x in comps if x in c]
                ms.append(S.MasterScore(master_id=mid, dial_id=EQ, score=max(avail), warning_threshold=m.warning_threshold,
                                        stress_threshold=m.stress_threshold, exit_threshold=m.exit_threshold, alarm_eligible=m.alarm_eligible))
            top = max(ms, key=lambda m: m.score)
            ac = S.Acute(dial_id=EQ, score=top.score, from_master_id=top.master_id, masters=tuple(ms))
            cnt = S.count_for_one_dial(contribs)
            i = pos[d]
            tr = trend_confirmed_from_closes(closes[max(0, i - 259):i + 1]) if lock else False
            armed = h.alarm_lock_armed(EQ) if lock else False
            row = R.official_state_for_dial(history=h.recent(EQ, limit=20), as_of=dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc),
                                            breadth=.3, acute=ac, count=cnt, trend_confirmed=tr, alarm_lock_armed=armed)
            h.append(row, written_utc=dt.datetime.now(dt.timezone.utc))
            out[d] = dict(state=row.machine_state.name, count=cnt.count)
        return out
    finally:
        S.COUNT_INDICATOR_IDS, S.PROVISIONAL_COUNT_K = saved_ids, saved_k

import eval_master as EM
epis = [(p, t) for p, t in EM.EPIS if p >= days[0]]
yrs = (days[-1] - days[0]).days / 365.25
def longest(o, which=("ALARM", "WATCH")):
    best = 0; cur = 0; bs = None; st_ = None
    for d in days:
        if o[d]["state"] in which:
            if cur == 0: st_ = d
            cur += 1
            if cur > best: best, bs = cur, (st_, d)
        else: cur = 0
    return best, bs
def reopen_and_reentry(o):
    reo = []; late = []
    for p, t in epis:
        for a, b in zip(days, days[1:]):
            if p <= b <= t and o[a]["state"] in ("WATCH", "ALARM") and o[b]["state"] in ("CALM", "RECOVERY") and any(o[x]["state"] == "ALARM" for x in days if b - dt.timedelta(days=30) <= x < b):
                reo.append(spx[t] / spx[b] - 1)
        perm = [d for d in days if d >= t and o[d]["state"] in ("CALM", "RECOVERY")]
        if perm: late.append(((perm[0] - t).days, spx[perm[0]] / spx[t] - 1))
    return len(reo), (st.mean(reo) if reo else 0), st.median(l[0] for l in late), st.median(l[1] for l in late), max(l[0] for l in late)
CONF = [
 ("C0 vol.70, no count, no lock   (pre-PR + vol fix)", 99, False, False),
 ("C1 + count k=2 (curves in)     (no lock)", 2, False, False),
 ("C2 + lock/trend, no count", 99, False, True),
 ("C3 PR AS WRITTEN: lock + count k=2 (curves in)", 2, False, True),
 ("C4 lock + count k=2, curves OUT of count", 2, True, True),
]
print(f"{len(days)} days {days[0]}..{days[-1]} ({yrs:.1f}y); {len(epis)} declines >=15% (EM.EPIS)")
print("config | ALARM% DENY% | FA spans/yr (n) | declines with ALARM at/before trough | longest continuous deny | premature re-opens (mean further fall) | re-entry median d / off-low (max d)")
store = {}
for name, k, dc, lk in CONF:
    o = run(k, dc, lk); store[name] = o
    r = EM.evaluate(days, {d: {"state": o[d]["state"]} for d in days}, epis=epis)
    caught = sum(1 for e in r["res"] if e["alarm"] is not None and e["alarm"] <= e["t"])
    n_re, mean_re, med_d, med_off, max_d = reopen_and_reentry(o)
    lg, ls = longest(o)
    print(f"{name}\n    ALARM {r['alarm_days']:.1%}  DENY {r['deny_days']:.1%} | FA {r['fa_per_yr']:.2f}/yr ({r['fa_spans']}) | caught {caught}/{len(r['res'])} | longest deny {lg}d {ls[0]}..{ls[1]} | reopens {n_re} ({mean_re:+.0%}) | re-entry {med_d:.0f}d / {med_off:+.0%} (max {max_d}d)")
import pickle; pickle.dump({n: {str(d): v for d, v in o.items()} for n, o in store.items()}, open(os.path.join(SP, "live", "control_sim2.pkl"), "wb"))
