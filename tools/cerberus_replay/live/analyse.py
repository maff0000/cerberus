import sys, os, json, collections, datetime as dt
SP = os.environ["R2_SCRATCH"]
sys.path.insert(0, os.path.join(SP, "harness"))
import cerberus_replay as C          # harness Panel: store S&P path + episode windows (pinned dfd127e engine for its own scoring)
import protect as PR
D = dt.date.fromisoformat
EPS = [e[0] for e in C.EPISODES]
CFG = ["A_strict_asis", "B_strict_liveshaped", "C_avail_liveshaped", "D_avail_asis"]

def load(cfg):
    out = {}
    for ep in EPS:
        p = os.path.join(SP, "live", "runs", cfg, f"{ep}.jsonl")
        for l in open(p):
            r = json.loads(l); out[D(r["date"])] = r
    return out
R = {c: load(c) for c in CFG}
P = C.Panel()
st = lambda r, dial: (r.get(dial) or {}).get("state", "state.unknown").split(".")[1].upper()
def states(cfg, dial="equity_crash"):
    return {d: {"state": st(r, dial)} for d, r in R[cfg].items()}
errs = {c: sum(1 for r in R[c].values() if r["err"]) for c in CFG}
print("rows per config:", {c: len(R[c]) for c in CFG}, "pass errors:", errs)

print("\n=== T1 COVERAGE MAP: share of days per official state, equity dial, config A (store as-is) and B (live-shaped S&P) ===")
for cfg in ("A_strict_asis", "B_strict_liveshaped"):
    print(cfg)
    for dial in ("equity_crash", "monetary_debasement"):
        for ep in EPS:
            ds = [d for d in P.days if P.win[d] == ep]
            c = collections.Counter(st(R[cfg][d], dial) for d in ds)
            n = len(ds)
            print(f"  {dial[:8]:8s} {ep:9s} n={n:4d} " + "  ".join(f"{k} {v/n:5.1%}" for k, v in sorted(c.items())))

print("\n=== T1b: which equity masters SCORE per episode (config C: real contributions, hy_oas requirement relaxed) ===")
mids = ["credit_master", "curve_master", "volatility_master", "financial_conditions_master"]
for ep in EPS:
    ds = [d for d in P.days if P.win[d] == ep]; n = len(ds)
    cnt = collections.Counter()
    for d in ds:
        ms = (R["C_avail_liveshaped"][d].get("equity_crash") or {}).get("masters") or {}
        for m in ms: cnt[m] += 1
        if not ms: cnt["NO MASTER"] += 1
    print(f"  {ep:9s} n={n:4d} " + "  ".join(f"{m.replace('_master','')} {cnt[m]/n:4.0%}" for m in mids) + f"  none {cnt['NO MASTER']/n:4.0%}")

print("\n=== T2 PROTECTION (config C, equity): share of the peak->trough decline still ahead at the FIRST signal ===")
sC = states("C_avail_liveshaped")
PR.show("ALARM", PR.protection(P, sC))
PR.show("DENY (WATCH|ALARM)", PR.protection(P, sC, ("WATCH", "ALARM")))
sD = states("D_avail_asis")
PR.show("D (store as-is, no S&P history) ALARM", PR.protection(P, sD))

print("\n=== T3 state shares, equity, config C, per episode ===")
for ep in EPS:
    ds = [d for d in P.days if P.win[d] == ep]; n = len(ds)
    c = collections.Counter(sC[d]["state"] for d in ds)
    print(f"  {ep:9s} " + "  ".join(f"{k} {c[k]/n:5.1%}" for k in ("ALARM", "WATCH", "RECOVERY", "CALM", "UNKNOWN")))

print("\n=== T4 what drove ALARM (config C): masters >= stress vs count-only ===")
STRESS = {"credit_master": .85, "volatility_master": .70, "financial_conditions_master": .85}
for ep in EPS:
    ds = [d for d in P.days if P.win[d] == ep]
    cand_alarm = [d for d in ds if (R["C_avail_liveshaped"][d].get("equity_crash") or {}).get("cand") == "state.alarm"]
    cnt_only = [d for d in cand_alarm if not any(v >= STRESS.get(m, 9) for m, v in (R["C_avail_liveshaped"][d]["equity_crash"].get("masters") or {}).items())]
    print(f"  {ep:9s} ALARM-candidate days {len(cand_alarm):4d}; of which count-only (no eligible master at stress): {len(cnt_only)}"
          + (f"  e.g. {cnt_only[0]}..{cnt_only[-1]}" if cnt_only else ""))
    if cnt_only:
        ex = R["C_avail_liveshaped"][cnt_only[len(cnt_only) // 2]]["equity_crash"]
        print("       sample:", ex["at_or_beyond"], {k: round(v, 2) for k, v in (ex["masters"] or {}).items()})

print("\n=== T5 the lock in the replay: trend flag availability & lock behaviour ===")
for cfg in CFG:
    print(f"  {cfg}: trend True on {sum(1 for r in R[cfg].values() if r['trend'])} of {len(R[cfg])} days; "
          f"days armed {sum(1 for r in R[cfg].values() if r['armed_before'])}")
for ep in EPS:
    ds = [d for d in P.days if P.win[d] == ep]
    for cfg in ("C_avail_liveshaped", "D_avail_asis"):
        s = {d: st(R[cfg][d], "equity_crash") for d in ds}
        firstA = next((d for d in ds if s[d] == "ALARM"), None)
        if firstA is None: continue
        rec = [d for d in ds if d > firstA and s[d] == "RECOVERY"]
        calm = [d for d in ds if d > firstA and s[d] == "CALM"]
        print(f"  {ep:9s} {cfg[:1]}: first ALARM {firstA}; later RECOVERY days {len(rec)} (first {rec[0] if rec else '-'}); CALM days after ALARM {len(calm)} (first {calm[0] if calm else '-'}); last day state {s[ds[-1]]}")

print("\n=== T6 monetary dial (real pass, config A strict, store as-is) ===")
for ep in EPS:
    ds = [d for d in P.days if P.win[d] == ep]
    s = [st(R["A_strict_asis"][d], "monetary_debasement") for d in ds]
    seq = []
    for k in s:
        if not seq or seq[-1][0] != k: seq.append([k, 0])
        seq[-1][1] += 1
    print(f"  {ep:9s} " + " ".join(f"{k}x{n}" for k, n in seq))
json.dump({c: {str(d): {"eq": st(r, "equity_crash"), "mo": st(r, "monetary_debasement"), "trend": r["trend"], "armed": r["armed_before"]} for d, r in R[c].items()} for c in CFG},
          open(os.path.join(SP, "live", "runs_summary.json"), "w"))
