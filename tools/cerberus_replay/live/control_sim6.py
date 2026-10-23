"""PR #14's REAL resolver + REAL lock query + REAL trend test, driven day by day over the CONTINUOUS control series (1990-2026,
NOT the store).  Inputs available on the control: vix_level, vix_term_structure, yield_curve_10y3m, yield_curve_10y2y, spx_vs_200dma.
No hy_oas / nfci / skew / copper_gold, so every ALARM/WATCH number here is a LOWER BOUND (missing inputs can only add stress).
Config PR = the PR as written.  Config NOCURVE = identical except the two curve indicators are removed from the count."""
import sys, os, json, datetime as dt, collections, statistics as st
SP = os.environ["R2_SCRATCH"]
REPO = os.path.join(SP, "repo_pr14b", "crash-detector")
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
import csv
spx = X["spx"]
skew = {}
for r in csv.reader(open(os.path.join(SP, "control", "SKEW.csv"))):
    if r[0] == "DATE": continue
    m_, d_, y_ = r[0].split("/"); skew[dt.date(int(y_), int(m_), int(d_))] = float(r[1])
tips = {}
for r in csv.reader(open(os.path.join(SP, "control", "DFII10.csv"))):
    if r[0] == "observation_date" or r[1] in ("", "."): continue
    tips[dt.date.fromisoformat(r[0])] = float(r[1])
days = [d for d in sorted(spx) if d >= dt.date(2006, 7, 17) and d in X["vix"] and d in X["vix3m"] and d in X["t10y3m"] and d in X["t10y2y"] and d in skew and d in tips]
alld = sorted(spx); closes = [spx[d] for d in alld]; pos = {d: i for i, d in enumerate(alld)}
EQ = "equity_crash"
MASTERS = {m.master_id: m for m in S.EQUITY_CRASH_MASTERS}

def day_inputs(d):
    i = pos[d]
    c = {"vix_level": sc("vix_level", X["vix"][d]),
         "yield_curve_10y3m": sc("yield_curve_10y3m", X["t10y3m"][d]), "yield_curve_10y2y": sc("yield_curve_10y2y", X["t10y2y"][d])}
    c["vix_term_structure"] = sc("vix_term_structure", X["vix"][d] / X["vix3m"][d])
    c["cboe_skew"] = sc("cboe_skew", skew[d]); c["real_rate_10y_tips"] = sc("real_rate_10y_tips", tips[d])
    if i >= 199: c["spx_vs_200dma"] = sc("spx_vs_200dma", (closes[i] / (sum(closes[i - 199:i + 1]) / 200) - 1) * 100)
    return c


def run(k, ids, lock):
    saved_ids, saved_k = S.COUNT_INDICATOR_IDS, S.PROVISIONAL_COUNT_K
    S.PROVISIONAL_COUNT_K = k
    S.COUNT_INDICATOR_IDS = tuple(ids)
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

import eval_master as EM, bisect
class _Near(dict):
    def __missing__(self, d):
        ks = self._keys
        i = bisect.bisect_right(ks, d) - 1
        return dict.__getitem__(self, ks[max(i, 0)])
EM.spx = _Near(EM.spx); EM.spx._keys = sorted(dict.keys(EM.spx))
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

ALL = tuple(S.COUNT_INDICATOR_IDS)
NOCURVE = tuple(x for x in ALL if not x.startswith("yield_curve"))
MKT = ("vix_level", "vix_term_structure", "spx_vs_200dma", "cboe_skew")                 # market-priced, none a slow level/structural quantity
MKT_NOSKEW = ("vix_level", "vix_term_structure", "spx_vs_200dma")
CONF = [
 ("SHIPPED f290583: K=None (rule 3 off), lock+trend", None, ALL, True),
 ("SHIPPED f290583, lock OFF (no RECOVERY lock)", None, ALL, False),
]
print(f"{len(days)} days {days[0]}..{days[-1]} ({yrs:.1f}y); {len(epis)} declines >=15%.  (control lacks hy_oas, ig_oas, copper_gold: ALARM/FA are LOWER bounds)")
for name, k, ids, lk in CONF:
    o = run(k, ids, lk)
    r = EM.evaluate(days, {d: {"state": o[d]["state"]} for d in days}, epis=epis)
    caught = sum(1 for e in r["res"] if e["alarm"] is not None and e["alarm"] <= e["t"])
    lg, ls = longest(o)
    print(f"{name:55s} ALARM {r['alarm_days']:5.1%} DENY {r['deny_days']:5.1%} | FA {r['fa_per_yr']:.2f}/yr ({r['fa_spans']:2d}) | caught {caught}/{len(r['res'])} | longest deny {lg}d")

print("--- per-episode, shipped (lock on) ---")
o = run(None, ALL, True)
r = EM.evaluate(days, {d: {"state": o[d]["state"]} for d in days}, epis=epis)
shares = []
for e in r["res"]:
    p, t = e["p"], e["t"] if "p" in e else (None, e["t"])
    a = e["alarm"]
    if a is None: print(e); continue
    dd = spx[t] / spx[epis[r["res"].index(e)][0]] - 1
    pk = epis[r["res"].index(e)][0]; ahead = min(1.0, (spx[a] - spx[t]) / (spx[pk] - spx[t])) if a <= t else 0
    shares.append(ahead)
    print(f"  peak {epis[r['res'].index(e)][0]} trough {t} first ALARM {a} share of fall ahead {ahead:.0%}")
print("mean share ahead", f"{st.mean(shares):.0%}")
print("reopen/reentry (n_reopen, mean fwd ret, median reentry days, median reentry ret, max days):", reopen_and_reentry(o))
