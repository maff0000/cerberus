"""Base rate of PR #14's count rule on the CONTINUOUS control (2003-01..2026-10, where SKEW, DFII10, VIX3M all exist).
Inputs scored with the PR's own bands.  Missing vs the live engine: hy_oas, ig_oas, copper_gold (-> every ALARM count is a LOWER bound)."""
import sys, os, json, csv, datetime as dt, collections, statistics as st
SP = os.environ["R2_SCRATCH"]; REPO = os.path.join(SP, "repo_pr14", "crash-detector")
sys.path[:0] = [os.path.join(REPO, "src"), REPO, os.path.join(SP, "harness")]
from crash_detector.engine import statistics as S
from crash_detector.dials.scores import Contribution
import control as K
X = K.load()
B = json.load(open(os.path.join(REPO, "deploy/indicator-scaling.json")))["equity_crash"]
def sc(i, x):
    b = B[i]; s = (x - b["calm"]) / (b["stress"] - b["calm"]); return 0.0 if s < 0 else 1.0 if s > 1 else s
skew = {}
for r in csv.reader(open(os.path.join(SP, "control", "SKEW.csv"))):
    if r[0] == "DATE": continue
    m, d, y = r[0].split("/"); skew[dt.date(int(y), int(m), int(d))] = float(r[1])
tips = K.fred("DFII10") if False else {}
for r in csv.reader(open(os.path.join(SP, "control", "DFII10.csv"))):
    if r[0] == "observation_date" or r[1] in ("", "."): continue
    tips[dt.date.fromisoformat(r[0])] = float(r[1])
spx = X["spx"]; alld = sorted(spx); closes = [spx[d] for d in alld]; pos = {d: i for i, d in enumerate(alld)}
days = [d for d in alld if d >= dt.date(2003, 1, 2) and d in X["vix"] and d in X["vix3m"] and d in X["t10y3m"] and d in X["t10y2y"] and d in skew and d in tips]
yrs = (days[-1] - days[0]).days / 365.25
def inputs(d):
    i = pos[d]
    c = {"vix_level": sc("vix_level", X["vix"][d]), "vix_term_structure": sc("vix_term_structure", X["vix"][d] / X["vix3m"][d]),
         "yield_curve_10y3m": sc("yield_curve_10y3m", X["t10y3m"][d]), "yield_curve_10y2y": sc("yield_curve_10y2y", X["t10y2y"][d]),
         "cboe_skew": sc("cboe_skew", skew[d]), "real_rate_10y_tips": sc("real_rate_10y_tips", tips[d])}
    if i >= 199: c["spx_vs_200dma"] = sc("spx_vs_200dma", (closes[i] / (sum(closes[i - 199:i + 1]) / 200) - 1) * 100)
    return c
idx = {d: i for i, d in enumerate(days)}
def fwdmin(d, h=63):
    i = idx[d]; p0 = spx[d]
    fut = [spx[days[j]] / p0 - 1 for j in range(i + 1, min(i + 1 + h, len(days)))]
    return min(fut) if len(fut) == h else None
def runs(ds):
    out = []; cur = None
    for d in ds:
        if cur and idx[d] - idx[cur[1]] <= 5: cur[1] = d
        else:
            if cur: out.append(tuple(cur))
            cur = [d, d]
    if cur: out.append(tuple(cur))
    return out
combo = collections.defaultdict(list); n_cnt = 0
cands = []
for d in days:
    c = inputs(d)
    cn = S.count_for_one_dial(tuple(Contribution(source_id=k, category="x", weight=1.0, contribution=v) for k, v in sorted(c.items())))
    vol = max(c["vix_level"], c["vix_term_structure"])
    if cn.count >= S.PROVISIONAL_COUNT_K and vol < S.VOLATILITY_MASTER_STRESS:      # count-only: vol master (the only eligible master available here) below stress
        combo[tuple(cn.at_or_beyond)].append(d); cands.append(d)
unc = [fwdmin(d) for d in days if fwdmin(d) is not None]
base10 = sum(1 for v in unc if v <= -.10) / len(unc)
print(f"control {days[0]}..{days[-1]} ({yrs:.1f}y, {len(days)} days). Unconditional P(63d fwd-min <= -10%) = {base10:.1%}")
print(f"count>=2 with the vol master BELOW its 0.70 stress (count-only candidate days): {len(cands)} = {len(cands)/len(days):.1%} of days, {len(runs(cands))} separate runs = {len(runs(cands))/yrs:.2f}/yr\n")
print("by indicator combination at/beyond 0.80 (days; runs; P(63d fwd-min<=-10%) ; median S&P dd from 252d high):")
def dd252(d):
    i = pos[d]; hi = max(closes[max(0, i - 251):i + 1]); return spx[d] / hi - 1
for k, ds in sorted(combo.items(), key=lambda kv: -len(kv[1])):
    f = [fwdmin(d) for d in ds if fwdmin(d) is not None]
    p = sum(1 for v in f if v <= -.10) / len(f) if f else float("nan")
    print(f"  {len(ds):4d}d {len(runs(ds)):3d} runs  P(hit)={p:5.0%}  dd-med {st.median(dd252(d) for d in ds):+5.1%}  {list(k)}")
curve = [d for k, ds in combo.items() if set(k) >= {"yield_curve_10y2y", "yield_curve_10y3m"} for d in ds]
tipsk = [d for k, ds in combo.items() if set(k) >= {"cboe_skew", "real_rate_10y_tips"} for d in ds]
print(f"\ncount-only days containing BOTH curve indicators: {len(curve)} ({len(runs(sorted(curve)))} runs); containing BOTH cboe_skew and real_rate_10y_tips: {len(tipsk)} ({len(runs(sorted(tipsk)))} runs)")
for nm, ds in (("curve pair", curve), ("skew+tips", tipsk)):
    f = [fwdmin(d) for d in ds if fwdmin(d) is not None]
    print(f"   {nm}: P(63d fwd-min<=-10%) = {sum(1 for v in f if v<=-.10)/len(f):.0%} over {len(f)} observable days  (unconditional {base10:.0%})")
    byyr = collections.Counter(d.year for d in ds)
    print("   by year:", dict(sorted(byyr.items())))
