"""CSDR Apollo replay + parameter sweep — best WR per session.

Per Matt 2026-05-02: focus exclusively on CSDR. Iterate parameters until best
WR combination per session. Uses csdr_engine.replay_csdr() to walk 6mo XAU
M15+M1 history under each param combination, simulates trade outcomes, aggregates
per session.

READ-ONLY against trading data. UTC discipline. Methodology: r2d2:methodology:correlation:v1.
Main directive: r2d2:directive:main (preservation of the team).

Run on dell-debian (where data lives). Bake report from Trinity post-scp.
"""
import json, datetime, pymysql, sys, os, copy
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from csdr_engine import replay_csdr, session_bucket

# ---- CSDR baseline params (current live values) ----
BASELINE = {
    "compression_lookback": 10,
    "compression_multiplier": 1.5,
    "min_sweep_extension_atr": 0.05,
    "displacement_atr_min": 0.5,
    "max_bars_after_sweep": 6,  # POST-FIX value (was 3)
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

# ---- Sweep grid (focused on highest-leverage knobs) ----
SWEEP_GRID = {
    "max_bars_after_sweep": [3, 4, 5, 6, 7, 8, 10],
    "min_sweep_extension_atr": [0.03, 0.05, 0.08, 0.12],
    "displacement_atr_min": [0.3, 0.5, 0.7, 1.0],
    "min_fvg_atr": [0.05, 0.08, 0.12, 0.20],
    "compression_multiplier": [1.0, 1.5, 2.0],
    "quality_threshold": [50, 60, 70, 80],
    "tp_r_multiple": [1.0, 1.5, 2.0, 2.5],
}
# 7 × 4 × 4 × 4 × 3 × 4 × 4 = 21,504 combos. Too many for first pass.
# First pass: sweep one knob at a time around BASELINE — find sensitivity, then narrow.
# Second pass: 2D sweep of top-2 most-impactful knobs.
# Third pass: refine on best region.

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

# ---- Pull 6mo M1 XAU candles ----
print("Loading M1 XAU candles (6mo)...")
sigcur.execute("""
    SELECT timestamp, open, high, low, close FROM candles_M1
    WHERE instrument='XAU_USD'
      AND timestamp >= DATE_SUB((SELECT MAX(timestamp) FROM candles_M1 WHERE instrument='XAU_USD'), INTERVAL 180 DAY)
    ORDER BY timestamp ASC
""")
m1_all = sigcur.fetchall()
print(f"  M1 candles loaded: {len(m1_all)}")

# Aggregate to M15 (open of first M1 in 15min window, high=max, low=min, close of last)
print("Aggregating to M15...")
m15_bars = []
buckets = defaultdict(list)
for c in m1_all:
    ts = c["timestamp"]
    bucket_key = ts.replace(minute=(ts.minute // 15) * 15, second=0, microsecond=0)
    buckets[bucket_key].append(c)
for bucket_ts in sorted(buckets.keys()):
    bs = buckets[bucket_ts]
    if not bs: continue
    m15_bars.append({
        "ts": bucket_ts,
        "open": float(bs[0]["open"]),
        "high": max(float(c["high"]) for c in bs),
        "low": min(float(c["low"]) for c in bs),
        "close": float(bs[-1]["close"]),
    })
print(f"  M15 bars: {len(m15_bars)}")

# Build m1_lookup: for each M15 bar, the 30 preceding M1 candles
print("Building m1_lookup (30 M1 bars per M15)...")
m1_lookup = {}
m1_by_ts = sorted(m1_all, key=lambda c: c["timestamp"])
m1_idx = 0
for bar in m15_bars:
    while m1_idx < len(m1_by_ts) and m1_by_ts[m1_idx]["timestamp"] < bar["ts"]:
        m1_idx += 1
    start = max(0, m1_idx - 30)
    m1_lookup[bar["ts"]] = m1_by_ts[start:m1_idx]

# Compute M1 ATR per M15 bar (Wilder ATR over 14 M1 bars preceding)
print("Computing ATR(14)...")
def wilder_atr(bars, period=14):
    if len(bars) < period + 1: return None
    trs = []
    for i in range(1, len(bars)):
        h = float(bars[i]["high"]); l = float(bars[i]["low"]); pc = float(bars[i-1]["close"])
        trs.append(max(h-l, abs(h-pc), abs(l-pc)))
    if len(trs) < period: return None
    a = sum(trs[:period])/period
    for tr in trs[period:]:
        a = (a * (period-1) + tr) / period
    return a

atr_lookup = {}
for bar in m15_bars:
    pre_m1 = m1_lookup.get(bar["ts"], [])
    atr_lookup[bar["ts"]] = wilder_atr(pre_m1, 14)

valid_count = sum(1 for v in atr_lookup.values() if v is not None and v > 0)
print(f"  ATR computed; {valid_count}/{len(m15_bars)} M15 bars have valid ATR")

# ---- Trade outcome simulator (TP1 vs SL hit on M1 forward bars) ----
def simulate_trade(prop, m1_lookup_ts_ordered, max_minutes=480):
    """Simulate trade outcome. Returns {outcome: TP|SL|TIMEOUT, pnl_pts, bars_held}."""
    direction = 1 if prop["direction"] == "BUY" else -1
    entry = prop["entry_price"]
    stop = prop["stop_price"]
    target = prop["target_price"]
    start_ts = prop["ts"]
    end_ts = start_ts + datetime.timedelta(minutes=max_minutes)
    # Walk forward M1 bars from start_ts
    bars_held = 0
    for c in m1_lookup_ts_ordered:
        if c["timestamp"] < start_ts: continue
        if c["timestamp"] > end_ts: break
        bars_held += 1
        h = float(c["high"]); l = float(c["low"])
        # Conservative: SL priority if both could hit
        if direction == 1:
            if l <= stop: return {"outcome": "SL", "pnl_pts": stop - entry, "bars_held": bars_held}
            if h >= target: return {"outcome": "TP", "pnl_pts": target - entry, "bars_held": bars_held}
        else:
            if h >= stop: return {"outcome": "SL", "pnl_pts": entry - stop, "bars_held": bars_held}
            if l <= target: return {"outcome": "TP", "pnl_pts": entry - target, "bars_held": bars_held}
    return {"outcome": "TIMEOUT", "pnl_pts": 0.0, "bars_held": bars_held}

# Pre-sort all M1 for trade simulation (avoid re-sorting per trade)
m1_sorted = sorted(m1_all, key=lambda c: c["timestamp"])

# ---- Run a single param combination, return per-session stats ----
def run_combo(params):
    """Returns dict {session: {n, wr_pct, expectancy, ...}}"""
    proposals = replay_csdr(m15_bars, m1_lookup, atr_lookup, params)
    by_session = defaultdict(list)
    for prop in proposals:
        outcome = simulate_trade(prop, m1_sorted)
        by_session[prop["session"]].append({
            "ts": prop["ts"], "direction": prop["direction"],
            "outcome": outcome["outcome"], "pnl_pts": outcome["pnl_pts"],
            "quality": prop["quality"], "bars_held": outcome["bars_held"],
            "tp_r": params["tp_r_multiple"],
        })
    result = {"_total_proposals": len(proposals)}
    for sess in ["ASIA", "LONDON", "NY", "LATE"]:
        items = by_session.get(sess, [])
        if not items:
            result[sess] = {"n": 0, "wr_pct": None, "expectancy": None}
            continue
        wins = sum(1 for it in items if it["outcome"] == "TP")
        sls = sum(1 for it in items if it["outcome"] == "SL")
        timeouts = sum(1 for it in items if it["outcome"] == "TIMEOUT")
        n = len(items)
        wr = 100 * wins / n
        exp = sum(it["pnl_pts"] for it in items) / n
        result[sess] = {
            "n": n, "wins": wins, "losses": sls, "timeouts": timeouts,
            "wr_pct": round(wr, 2), "expectancy_pts": round(exp, 3),
            "avg_quality": round(sum(it["quality"] for it in items) / n, 1),
        }
    # Aggregate row
    all_items = [it for items in by_session.values() for it in items]
    if all_items:
        n = len(all_items)
        wins = sum(1 for it in all_items if it["outcome"] == "TP")
        result["TOTAL"] = {
            "n": n, "wins": wins,
            "wr_pct": round(100*wins/n, 2),
            "expectancy_pts": round(sum(it["pnl_pts"] for it in all_items)/n, 3),
        }
    return result

# ---- PASS 1: baseline ----
print("\n=== PASS 1: BASELINE ===")
baseline_result = run_combo(BASELINE)
print(f"  Total proposals: {baseline_result['_total_proposals']}")
for sess in ["ASIA", "LONDON", "NY", "LATE", "TOTAL"]:
    c = baseline_result.get(sess, {})
    if c.get("n"):
        print(f"  {sess}: n={c['n']} WR={c['wr_pct']}% exp={c['expectancy_pts']}")
    else:
        print(f"  {sess}: 0 proposals")

# ---- PASS 2: 1D sweeps around baseline ----
print("\n=== PASS 2: 1D SENSITIVITY SWEEPS ===")
sensitivity_results = {}
for knob, values in SWEEP_GRID.items():
    if knob == "tp_r_multiple": continue  # 1D sweep on tp_r is meaningless without re-running
    print(f"\n  Knob: {knob}")
    sensitivity_results[knob] = {}
    for v in values:
        params = copy.deepcopy(BASELINE)
        params[knob] = v
        r = run_combo(params)
        sensitivity_results[knob][str(v)] = r
        if r.get("TOTAL"):
            t = r["TOTAL"]
            print(f"    {knob}={v}: n={t['n']} WR={t['wr_pct']}% exp={t['expectancy_pts']}")
        else:
            print(f"    {knob}={v}: 0 proposals")

# ---- Save report ----
report = {
    "wo": "WO-R2D2-CSDR-PARAM-SWEEP-001 (Matt 2026-05-02 directive)",
    "executed_by": "R2D2",
    "anchors": {"window_6mo": "180d ending at MAX(candles_M1.timestamp)"},
    "ut_discipline": "READ-ONLY. timestamp anchored. No NOW()/utcnow()/time.time().",
    "baseline_params": BASELINE,
    "baseline_result": baseline_result,
    "pass2_sensitivity_1d": sensitivity_results,
    "method": "Pure-Python CSDR state machine port from /srv-dev/falcon/strategies/csdr/. Walks 6mo XAU M15+M1 history, simulates TP1/SL outcomes via M1 forward bars (480min max hold).",
    "load_bearing_metric": "WR per [strategy×session] cell. Plus expectancy_pts as cross-check.",
    "honest_caveats": [
        "M1 sub-bar fill order approximated (SL priority if both could hit).",
        "No ARES context — strategy's session_quality lookup uses default mapping.",
        "TIMEOUT trades counted as 0 P&L (could be more sophisticated — exit at last close).",
        "Static-bracket only — no Ranger overlay (separate from Ranger backtest).",
        "Single-pass sensitivity only in v1 — multi-knob optimization needs PASS 3 (run after PASS 2 surfaces top-impact knobs).",
    ],
}

import os
os.makedirs("/tmp/r2d2_csdr_sweep", exist_ok=True)
with open("/tmp/r2d2_csdr_sweep/pass1_pass2_report.json", "w") as f:
    json.dump(report, f, indent=2, default=str)

print("\n=== DONE ===")
print(f"Report: /tmp/r2d2_csdr_sweep/pass1_pass2_report.json")
sigcur.close(); sigs.close()
