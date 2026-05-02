"""CSDR PASS 3: combined-knob sweep around the PASS 2 winners.

PASS 2 surfaced compression_multiplier as the dominant lever (1.5→2.0 = 1→19 proposals).
quality_threshold (70→60) and displacement_atr_min (0.5→0.3) also unlock.

PASS 3 runs the combinatorial space of the 3 winners + max_bars_after_sweep
(per Matt's earlier interest) and reports per-session breakdown.

Output: /tmp/r2d2_csdr_sweep/pass3_combined.json
"""
import json, datetime, pymysql, sys, os, copy, itertools
from collections import defaultdict
sys.path.insert(0, "/tmp")
from csdr_engine import replay_csdr, session_bucket

BASELINE = {
    "compression_lookback": 10,
    "compression_multiplier": 1.5,
    "min_sweep_extension_atr": 0.05,
    "displacement_atr_min": 0.5,
    "max_bars_after_sweep": 6,
    "min_fvg_atr": 0.08,
    "max_retest_bars": 8,
    "entry_model": "midpoint",
    "sl_buffer_atr": 0.10,
    "tp_r_multiple": 1.5,
    "quality_threshold": 70,
    "base_confidence": 0.55,
    "weight_compression": 15,
    "weight_sweep": 20,
    "weight_displacement": 20,
    "weight_fvg": 15,
    "weight_session": 10,
    "weight_htf_bias": 10,
    "weight_structure": 10,
}

# PASS 3: focused multi-knob sweep
GRID = {
    "compression_multiplier": [1.5, 2.0, 2.5, 3.0],
    "quality_threshold":      [40, 50, 60, 70],
    "displacement_atr_min":   [0.2, 0.3, 0.5, 0.7],
    "max_bars_after_sweep":   [4, 6, 8, 12],
    "min_fvg_atr":            [0.05, 0.08, 0.15],
}
# 4 × 4 × 4 × 4 × 3 = 768 combinations

env = {}
with open("/srv-dev/tradingProteus/.env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v.strip('"').strip("'")

sigs = pymysql.connect(host="127.0.0.1", port=3307, user=env["DB_USER"],
    password=env["DB_PASSWORD"], database="tradingSignals", charset="utf8mb4")
sigcur = sigs.cursor(pymysql.cursors.DictCursor)

print("Loading data...")
sigcur.execute("""
    SELECT timestamp, open, high, low, close FROM candles_M1
    WHERE instrument='XAU_USD'
      AND timestamp >= DATE_SUB((SELECT MAX(timestamp) FROM candles_M1 WHERE instrument='XAU_USD'), INTERVAL 180 DAY)
    ORDER BY timestamp ASC
""")
m1_all = sigcur.fetchall()
print(f"  M1 candles: {len(m1_all)}")

m15_bars = []
buckets = defaultdict(list)
for c in m1_all:
    ts = c["timestamp"]
    bk = ts.replace(minute=(ts.minute // 15) * 15, second=0, microsecond=0)
    buckets[bk].append(c)
for bts in sorted(buckets.keys()):
    bs = buckets[bts]
    if not bs: continue
    m15_bars.append({"ts": bts, "open": float(bs[0]["open"]),
                     "high": max(float(c["high"]) for c in bs),
                     "low": min(float(c["low"]) for c in bs),
                     "close": float(bs[-1]["close"])})
print(f"  M15 bars: {len(m15_bars)}")

m1_lookup = {}
m1_by_ts = sorted(m1_all, key=lambda c: c["timestamp"])
m1_idx = 0
for bar in m15_bars:
    while m1_idx < len(m1_by_ts) and m1_by_ts[m1_idx]["timestamp"] < bar["ts"]:
        m1_idx += 1
    start = max(0, m1_idx - 30)
    m1_lookup[bar["ts"]] = m1_by_ts[start:m1_idx]

def wilder_atr(bars, period=14):
    if len(bars) < period+1: return None
    trs=[]
    for i in range(1,len(bars)):
        h=float(bars[i]["high"]); l=float(bars[i]["low"]); pc=float(bars[i-1]["close"])
        trs.append(max(h-l, abs(h-pc), abs(l-pc)))
    if len(trs)<period: return None
    a=sum(trs[:period])/period
    for tr in trs[period:]: a=(a*(period-1)+tr)/period
    return a

atr_lookup = {bar["ts"]: wilder_atr(m1_lookup.get(bar["ts"], []), 14) for bar in m15_bars}
m1_sorted = sorted(m1_all, key=lambda c: c["timestamp"])

def simulate_trade(prop, max_minutes=480):
    direction = 1 if prop["direction"] == "BUY" else -1
    entry, stop, target = prop["entry_price"], prop["stop_price"], prop["target_price"]
    end_ts = prop["ts"] + datetime.timedelta(minutes=max_minutes)
    bh = 0
    for c in m1_sorted:
        if c["timestamp"] < prop["ts"]: continue
        if c["timestamp"] > end_ts: break
        bh += 1
        h, l = float(c["high"]), float(c["low"])
        if direction == 1:
            if l <= stop: return {"outcome":"SL","pnl_pts":stop-entry,"bars_held":bh}
            if h >= target: return {"outcome":"TP","pnl_pts":target-entry,"bars_held":bh}
        else:
            if h >= stop: return {"outcome":"SL","pnl_pts":entry-stop,"bars_held":bh}
            if l <= target: return {"outcome":"TP","pnl_pts":entry-target,"bars_held":bh}
    return {"outcome":"TIMEOUT","pnl_pts":0.0,"bars_held":bh}

def run_combo(params):
    proposals = replay_csdr(m15_bars, m1_lookup, atr_lookup, params)
    by_sess = defaultdict(list)
    for p in proposals:
        out = simulate_trade(p)
        by_sess[p["session"]].append({"outcome": out["outcome"], "pnl_pts": out["pnl_pts"]})
    res = {"_total_proposals": len(proposals)}
    for sess in ["ASIA", "LONDON", "NY", "LATE"]:
        items = by_sess.get(sess, [])
        if not items:
            res[sess] = {"n": 0}; continue
        n = len(items)
        wins = sum(1 for it in items if it["outcome"] == "TP")
        res[sess] = {"n": n, "wins": wins, "wr_pct": round(100*wins/n,2),
                     "expectancy_pts": round(sum(it["pnl_pts"] for it in items)/n, 3)}
    all_items = [it for items in by_sess.values() for it in items]
    if all_items:
        n = len(all_items); wins = sum(1 for it in all_items if it["outcome"]=="TP")
        res["TOTAL"] = {"n": n, "wins": wins, "wr_pct": round(100*wins/n, 2),
                        "expectancy_pts": round(sum(it["pnl_pts"] for it in all_items)/n, 3)}
    return res

print(f"\n=== PASS 3: combined sweep ({4*4*4*4*3} combinations) ===")
results = []
combo_count = 0
for cm in GRID["compression_multiplier"]:
    for qt in GRID["quality_threshold"]:
        for da in GRID["displacement_atr_min"]:
            for mb in GRID["max_bars_after_sweep"]:
                for mf in GRID["min_fvg_atr"]:
                    combo_count += 1
                    if combo_count % 50 == 0:
                        print(f"  combo {combo_count}/768...")
                    p = copy.deepcopy(BASELINE)
                    p.update({"compression_multiplier": cm, "quality_threshold": qt,
                              "displacement_atr_min": da, "max_bars_after_sweep": mb,
                              "min_fvg_atr": mf})
                    r = run_combo(p)
                    r["_params"] = {"cm": cm, "qt": qt, "da": da, "mb": mb, "mf": mf}
                    results.append(r)

# ---- Find best per session ----
print("\n=== BEST PER SESSION (by WR with n>=10 minimum) ===")
best = {}
for sess in ["ASIA", "LONDON", "NY", "LATE"]:
    candidates = [r for r in results if r.get(sess, {}).get("n", 0) >= 10]
    if not candidates:
        # Lower bar to 5
        candidates = [r for r in results if r.get(sess, {}).get("n", 0) >= 5]
    if not candidates:
        # Lower to 3
        candidates = [r for r in results if r.get(sess, {}).get("n", 0) >= 3]
    if not candidates:
        best[sess] = None
        print(f"  {sess}: NO COMBOS WITH n>=3")
        continue
    # Sort by WR descending, then expectancy descending, then n
    candidates.sort(key=lambda r: (-r[sess]["wr_pct"], -r[sess]["expectancy_pts"], -r[sess]["n"]))
    top = candidates[0]
    best[sess] = {
        "params": top["_params"],
        "n": top[sess]["n"],
        "wins": top[sess]["wins"],
        "wr_pct": top[sess]["wr_pct"],
        "expectancy_pts": top[sess]["expectancy_pts"],
        "total_proposals_in_combo": top["_total_proposals"],
    }
    p = top["_params"]
    print(f"  {sess}: cm={p['cm']} qt={p['qt']} da={p['da']} mb={p['mb']} mf={p['mf']} → "
          f"n={top[sess]['n']} WR={top[sess]['wr_pct']}% exp={top[sess]['expectancy_pts']}")

# ---- Best aggregate (TOTAL) ----
print("\n=== BEST OVERALL (TOTAL row, n>=20) ===")
agg_candidates = [r for r in results if r.get("TOTAL", {}).get("n", 0) >= 20]
if agg_candidates:
    agg_candidates.sort(key=lambda r: (-r["TOTAL"]["wr_pct"], -r["TOTAL"]["expectancy_pts"]))
    top10 = agg_candidates[:10]
    for i, r in enumerate(top10, 1):
        p = r["_params"]; t = r["TOTAL"]
        print(f"  #{i}: cm={p['cm']} qt={p['qt']} da={p['da']} mb={p['mb']} mf={p['mf']} → "
              f"n={t['n']} WR={t['wr_pct']}% exp={t['expectancy_pts']}")

# ---- Save ----
out = {
    "wo": "WO-R2D2-CSDR-PARAM-SWEEP-001 PASS 3",
    "executed_by": "R2D2",
    "method": "Combinatorial sweep of 5 knobs around PASS 2 winners (768 combos × per-session aggregation)",
    "baseline_for_reference": BASELINE,
    "grid": GRID,
    "best_per_session": best,
    "top10_overall_n_ge_20": [
        {"params": r["_params"], "TOTAL": r["TOTAL"]} for r in agg_candidates[:10]
    ] if agg_candidates else [],
    "all_combos_with_proposals_ge_5": [
        r for r in results if r.get("_total_proposals", 0) >= 5
    ],
}

import os
os.makedirs("/tmp/r2d2_csdr_sweep", exist_ok=True)
with open("/tmp/r2d2_csdr_sweep/pass3_combined.json", "w") as f:
    json.dump(out, f, indent=2, default=str)
print(f"\nSaved /tmp/r2d2_csdr_sweep/pass3_combined.json")
sigcur.close(); sigs.close()
