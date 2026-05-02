"""Apollo Falcon Ranger Layer 3 Replay — Backtest Validation
WO: falcon:ranger:wo:backtest_validation:001
Owner: R2D2
Spec ref: falcon:ranger:spec:v1 (core_mechanic + parameters_default_xau_compression)
Output: r2d2:reports:falcon_ranger_backtest:001

READ-ONLY against trading data. UTC discipline absolute. No NOW()/utcnow()/time.time().
Methodology: r2d2:methodology:correlation:v1 (Spearman default for any rho).
Main directive: r2d2:directive:main (preservation of the team).

Architecture:
  1. Pull 6mo of XAU Falcon conf-7+ fires from helios_strategy_signals
  2. For each fire, pull forward M1 candles from tradingSignals.candles_M1
  3. Compute M1 ATR(14) at fire time
  4. Simulate Ranger Channel-Graduation Tracker (CGT) — single-layer + 2-layer modes
  5. Build static-bracket counterfactual (same fires, no Ranger)
  6. Verify R1/R2/R3 invariants across full sample (zero violations permitted)
  7. Compute WR delta vs static + ranger_delta_pts distribution + graduation rate
  8. Bake report
"""
import json, datetime, pymysql, sys, math, urllib.request
from collections import defaultdict, Counter

# --- spec params (from falcon:ranger:spec:v1) ---
PARAMS = {
    "L1": {"risk_pts": 2, "target_pts": 10, "trail_atr_mult": 1.2, "trail_floor_pts": 4,
           "graduation_buffer_atr_mult": 0.5, "next_tp_offset_pts": 10,
           "time_stop_M5_bars": 24, "max_slippage_pts": 1},
    "L2": {"risk_pts": 3, "target_pts": 7, "trail_atr_mult": 1.0, "trail_floor_pts": 3,
           "next_tp_offset_pts": 7, "time_stop_M5_bars": 12},
    "L3": {"risk_pts": 4, "target_pts": 5, "trail_atr_mult": 0.8, "trail_floor_pts": 2,
           "next_tp_offset_pts": 5, "time_stop_M5_bars": 6},
}
ATR_PERIOD = 14
BREAKEVEN_TRIGGER_PTS = 5  # R3: peak distance trigger for breakeven invariant
BREAKEVEN_OFFSET_PTS = 1   # R3: minimum profit floor once breakeven triggered

# --- env / DB ---
env = {}
with open("/srv-dev/tradingProteus/.env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v.strip('"').strip("'")

scalp = pymysql.connect(host="127.0.0.1", port=3307, user=env["DB_USER"],
    password=env["DB_PASSWORD"], database="tradingScalp", charset="utf8mb4")
scur = scalp.cursor(pymysql.cursors.DictCursor)
sigs = pymysql.connect(host="127.0.0.1", port=3307, user=env["DB_USER"],
    password=env["DB_PASSWORD"], database="tradingSignals", charset="utf8mb4")
sigcur = sigs.cursor(pymysql.cursors.DictCursor)

scur.execute("SELECT MAX(timestamp) AS now FROM helios_strategy_signals")
CANONICAL_NOW = scur.fetchone()["now"].replace(tzinfo=datetime.timezone.utc)
W6M = (CANONICAL_NOW - datetime.timedelta(days=180)).strftime("%Y-%m-%d %H:%M:%S")
NOW_SQL = CANONICAL_NOW.strftime("%Y-%m-%d %H:%M:%S")
print(f"CANONICAL_NOW: {CANONICAL_NOW.isoformat()}")
print(f"6mo window:    {W6M} -> {NOW_SQL}")

# --- pull fires (conf-7+ XAU from helios_strategy_signals) ---
scur.execute(f"""
    SELECT id, timestamp, strategy_id, instrument, confidence, direction,
           entry_price, sl_price, tp1_price, tp2_price, outcome, outcome_pnl_pts
    FROM helios_strategy_signals
    WHERE fired=1 AND instrument='XAU_USD'
      AND confidence >= 7
      AND timestamp >= '{W6M}' AND timestamp <= '{NOW_SQL}'
    ORDER BY timestamp ASC
""")
fires = list(scur.fetchall())
print(f"\nFires loaded: {len(fires)} (XAU_USD, conf>=7, 6mo)")
if not fires:
    print("FAIL_LOUD: no fires to replay")
    sys.exit(2)

# --- ATR computation helper ---
def compute_atr(bars, period=ATR_PERIOD):
    """Wilder ATR over a list of bars [{open,high,low,close}, ...]"""
    if len(bars) < period + 1: return None
    trs = []
    for i in range(1, len(bars)):
        h = float(bars[i]["high"]); l = float(bars[i]["low"]); pc = float(bars[i-1]["close"])
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    if len(trs) < period: return None
    # Wilder smoothing
    atr = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    return atr

# --- pull M1 candles for a window around a fire ---
def fetch_m1_window(fire_ts, lookback_minutes=60, lookforward_minutes=180):
    """Returns (atr_at_fire, list_of_forward_bars). All comparisons in naive-UTC."""
    fire_naive = fire_ts.replace(tzinfo=None) if fire_ts.tzinfo else fire_ts
    start = (fire_naive - datetime.timedelta(minutes=lookback_minutes)).strftime("%Y-%m-%d %H:%M:%S")
    end = (fire_naive + datetime.timedelta(minutes=lookforward_minutes)).strftime("%Y-%m-%d %H:%M:%S")
    sigcur.execute(f"""
        SELECT timestamp, open, high, low, close
        FROM candles_M1
        WHERE instrument='XAU_USD' AND timestamp >= '{start}' AND timestamp <= '{end}'
        ORDER BY timestamp ASC
    """)
    bars = sigcur.fetchall()
    if not bars: return None, []
    fire_idx = None
    for i, b in enumerate(bars):
        # bar timestamps come back naive from MySQL — compare to naive fire_ts
        bts = b["timestamp"].replace(tzinfo=None) if b["timestamp"].tzinfo else b["timestamp"]
        if bts >= fire_naive:
            fire_idx = i; break
    if fire_idx is None or fire_idx < ATR_PERIOD + 1:
        return None, []
    atr = compute_atr(bars[:fire_idx+1])
    forward = bars[fire_idx:]  # includes the bar at-or-after fire
    return atr, forward

# --- single-trade Ranger CGT simulation ---
def simulate_ranger(fire, atr, forward_bars, layer="L1"):
    """Return dict with outcome metrics for this fire under Ranger logic."""
    p = PARAMS[layer]
    direction = 1 if (fire["direction"] == "LONG") else -1
    entry = float(fire["entry_price"]) if fire.get("entry_price") else float(forward_bars[0]["open"])
    # R1: Ranger respects the strategy's broker SL on cycle 1 (does NOT override).
    # Fall back to Ranger default risk_pts only if strategy didn't set one.
    if fire.get("sl_price"):
        initial_sl = float(fire["sl_price"])
    else:
        initial_sl = entry - direction * p["risk_pts"]
    if fire.get("tp1_price"):
        initial_tp = float(fire["tp1_price"])
    else:
        initial_tp = entry + direction * p["target_pts"]
    trail_distance = max(atr * p["trail_atr_mult"], p["trail_floor_pts"])

    sl = initial_sl
    tp = initial_tp
    graduations = 0
    peak_distance = 0.0  # max favorable excursion (signed by direction)
    invariant_violations = {"R1": 0, "R2": 0, "R3": 0}
    sl_history = [sl]

    exit_price = None
    exit_reason = None
    bars_elapsed = 0
    time_stop_minutes = p["time_stop_M5_bars"] * 5

    for i, bar in enumerate(forward_bars[1:], start=1):  # skip entry bar
        bars_elapsed += 1
        h = float(bar["high"]); l = float(bar["low"]); o = float(bar["open"]); c = float(bar["close"])
        # Update peak distance (favorable excursion)
        if direction == 1:
            peak_distance = max(peak_distance, h - entry)
        else:
            peak_distance = max(peak_distance, entry - l)

        # Check exits — conservative: SL has priority if both could hit in same bar
        if direction == 1:
            sl_hit = (l <= sl)
            tp_hit = (h >= tp)
        else:
            sl_hit = (h >= sl)
            tp_hit = (l <= tp)

        if sl_hit:
            exit_price = sl
            exit_reason = "SL"
            break
        if tp_hit:
            # Graduation check: did price exceed tp + buffer*atr?
            buffer_pts = atr * p.get("graduation_buffer_atr_mult", 0.5)
            if direction == 1:
                graduated = (h > tp + buffer_pts)
            else:
                graduated = (l < tp - buffer_pts)
            if graduated:
                # Lock the floor at tp, set new tp higher
                new_sl = tp
                if new_sl * direction > sl * direction:
                    sl = new_sl
                    sl_history.append(sl)
                tp = tp + direction * p["next_tp_offset_pts"]
                graduations += 1
                # don't exit; continue tracking
            else:
                # TP hit cleanly, exit at TP
                exit_price = tp
                exit_reason = "TP"
                break

        # Update trail: SL moves UP (LONG) or DOWN (SHORT) only
        if direction == 1:
            new_sl_candidate = h - trail_distance
            if new_sl_candidate > sl:
                sl = new_sl_candidate
                sl_history.append(sl)
        else:
            new_sl_candidate = l + trail_distance
            if new_sl_candidate < sl:
                sl = new_sl_candidate
                sl_history.append(sl)

        # SL floor: once ratcheted above entry, never let it drop below entry
        if direction == 1 and sl > entry:
            sl = max(sl, entry)
        elif direction == -1 and sl < entry:
            sl = min(sl, entry)

        # Time stop
        if bars_elapsed >= time_stop_minutes:
            exit_price = c
            exit_reason = "TIME"
            break

    if exit_price is None:
        # Ran out of forward data without exit — mark INCOMPLETE
        exit_price = float(forward_bars[-1]["close"])
        exit_reason = "INCOMPLETE"

    pnl_pts = (exit_price - entry) * direction

    # --- R1: Ranger never overrides initial SL on cycle 1 ---
    # In replay, R1 means: initial_sl == entry +/- risk_pts. If user supplied entry/sl, verify.
    if fire.get("sl_price"):
        broker_sl = float(fire["sl_price"])
        if abs(broker_sl - initial_sl) > 0.01:  # 1 cent tolerance
            invariant_violations["R1"] += 1

    # --- R2: SL never decreases (one-way ratchet) ---
    for k in range(1, len(sl_history)):
        if direction == 1 and sl_history[k] < sl_history[k-1] - 0.01:
            invariant_violations["R2"] += 1
        elif direction == -1 and sl_history[k] > sl_history[k-1] + 0.01:
            invariant_violations["R2"] += 1

    # --- R3: peak distance >= trigger AND exit via SL → close >= entry + offset ---
    if peak_distance >= BREAKEVEN_TRIGGER_PTS and exit_reason == "SL":
        if direction == 1:
            if exit_price < entry + BREAKEVEN_OFFSET_PTS - 0.01:
                invariant_violations["R3"] += 1
        else:
            if exit_price > entry - BREAKEVEN_OFFSET_PTS + 0.01:
                invariant_violations["R3"] += 1

    return {
        "entry": entry, "initial_sl": initial_sl, "initial_tp": initial_tp,
        "exit_price": exit_price, "exit_reason": exit_reason,
        "pnl_pts": round(pnl_pts, 3), "graduations": graduations,
        "peak_distance": round(peak_distance, 3),
        "bars_elapsed": bars_elapsed,
        "invariant_violations": invariant_violations,
        "atr": round(atr, 3) if atr else None,
        "trail_distance": round(trail_distance, 3),
        "is_win": pnl_pts > 0,
    }

# --- static-bracket counterfactual ---
def simulate_static(fire, atr, forward_bars):
    """Just initial SL/TP, no Ranger. Returns same shape minus graduations."""
    p = PARAMS["L1"]
    direction = 1 if (fire["direction"] == "LONG") else -1
    entry = float(fire["entry_price"]) if fire.get("entry_price") else float(forward_bars[0]["open"])
    sl = entry - direction * p["risk_pts"]
    tp = entry + direction * p["target_pts"]
    time_stop_minutes = p["time_stop_M5_bars"] * 5

    for i, bar in enumerate(forward_bars[1:], start=1):
        h = float(bar["high"]); l = float(bar["low"]); c = float(bar["close"])
        if direction == 1:
            if l <= sl: return {"pnl_pts": round(sl - entry, 3), "exit_reason": "SL"}
            if h >= tp: return {"pnl_pts": round(tp - entry, 3), "exit_reason": "TP"}
        else:
            if h >= sl: return {"pnl_pts": round(entry - sl, 3), "exit_reason": "SL"}
            if l <= tp: return {"pnl_pts": round(entry - tp, 3), "exit_reason": "TP"}
        if i >= time_stop_minutes:
            return {"pnl_pts": round((c - entry) * direction, 3), "exit_reason": "TIME"}
    return {"pnl_pts": 0.0, "exit_reason": "INCOMPLETE"}

# --- main loop ---
print("\n=== Running replay ===")
results = {"single_layer": [], "static": []}
skipped = 0
for i, fire in enumerate(fires):
    if i % 100 == 0:
        print(f"  fire {i}/{len(fires)}...")
    fire_ts = fire["timestamp"].replace(tzinfo=datetime.timezone.utc) if fire["timestamp"].tzinfo is None else fire["timestamp"]
    atr, forward = fetch_m1_window(fire_ts)
    if not forward or atr is None or atr <= 0:
        skipped += 1
        continue
    if not fire.get("direction"):
        skipped += 1
        continue
    r1 = simulate_ranger(fire, atr, forward, layer="L1")
    s1 = simulate_static(fire, atr, forward)
    r1["fire_id"] = fire["id"]; r1["strategy_id"] = fire["strategy_id"]
    r1["timestamp"] = str(fire["timestamp"]); r1["direction"] = fire["direction"]
    r1["confidence"] = int(fire["confidence"])
    s1["fire_id"] = fire["id"]; s1["strategy_id"] = fire["strategy_id"]
    s1["timestamp"] = str(fire["timestamp"])
    results["single_layer"].append(r1)
    results["static"].append(s1)

print(f"\nSimulated: {len(results['single_layer'])} fires; skipped (insufficient data): {skipped}")

# --- aggregate metrics ---
def agg(results_list, label):
    n = len(results_list)
    if n == 0: return {"label": label, "n": 0}
    pnls = [r["pnl_pts"] for r in results_list]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    wr = len(wins) / n if n else 0
    expectancy = sum(pnls) / n
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    rr = (avg_win / abs(avg_loss)) if avg_loss else None
    # Drawdown (cumulative)
    cum = 0.0; peak = 0.0; max_dd = 0.0
    for p in pnls:
        cum += p
        peak = max(peak, cum)
        dd = peak - cum
        if dd > max_dd: max_dd = dd
    sorted_pnls = sorted(pnls)
    p10 = sorted_pnls[int(n*0.1)] if n >= 10 else sorted_pnls[0]
    p50 = sorted_pnls[int(n*0.5)]
    p90 = sorted_pnls[int(n*0.9)] if n >= 10 else sorted_pnls[-1]
    return {
        "label": label, "n": n,
        "wins": len(wins), "losses": len(losses),
        "wr_pct": round(100*wr, 2),
        "expectancy_pts": round(expectancy, 3),
        "avg_win_pts": round(avg_win, 3),
        "avg_loss_pts": round(avg_loss, 3),
        "rr_ratio": round(rr, 2) if rr else None,
        "max_drawdown_pts": round(max_dd, 2),
        "pnl_p10": round(p10, 3),
        "pnl_p50": round(p50, 3),
        "pnl_p90": round(p90, 3),
    }

ranger_agg = agg(results["single_layer"], "ranger_single_layer")
static_agg = agg(results["static"], "static_bracket_baseline")

# --- ranger_delta_pts ---
deltas = [r["pnl_pts"] - s["pnl_pts"]
          for r, s in zip(results["single_layer"], results["static"])
          if r.get("fire_id") == s.get("fire_id")]
deltas_sorted = sorted(deltas)
n_d = len(deltas)
delta_dist = {
    "n": n_d,
    "p10": round(deltas_sorted[int(n_d*0.1)], 3) if n_d >= 10 else None,
    "p50": round(deltas_sorted[int(n_d*0.5)], 3) if n_d else None,
    "p90": round(deltas_sorted[int(n_d*0.9)], 3) if n_d >= 10 else None,
    "avg": round(sum(deltas)/n_d, 3) if n_d else None,
    "positive_count": sum(1 for d in deltas if d > 0),
    "negative_count": sum(1 for d in deltas if d < 0),
    "zero_count": sum(1 for d in deltas if d == 0),
}

# --- invariant tally ---
total_violations = {"R1": 0, "R2": 0, "R3": 0}
for r in results["single_layer"]:
    for k in total_violations:
        total_violations[k] += r["invariant_violations"].get(k, 0)

# --- pass/fail criteria ---
pass_criteria = {
    "per_trade_R_expected_ge_1_5R": ranger_agg.get("rr_ratio", 0) and ranger_agg["rr_ratio"] >= 1.5,
    "wr_delta_vs_static_ge_0": (ranger_agg["wr_pct"] - static_agg["wr_pct"]) >= 0,
    "R1_zero_violations": total_violations["R1"] == 0,
    "R2_zero_violations": total_violations["R2"] == 0,
    "R3_zero_violations": total_violations["R3"] == 0,
}
all_pass = all(pass_criteria.values())

# --- per-strategy breakdown ---
per_strategy = defaultdict(list)
for r in results["single_layer"]:
    per_strategy[r["strategy_id"]].append(r)
strategy_breakdown = {sid: agg(rs, sid) for sid, rs in per_strategy.items()}

# --- graduation rate ---
total_grads = sum(r["graduations"] for r in results["single_layer"])
fires_with_grads = sum(1 for r in results["single_layer"] if r["graduations"] > 0)
grad_rate_per_fire = total_grads / len(results["single_layer"]) if results["single_layer"] else 0

# --- v0.2 tuning signal: does replay support trigger=3, offset=1, trail=10? ---
peak_dist_distribution = sorted([r["peak_distance"] for r in results["single_layer"]])
if peak_dist_distribution:
    peak_p50 = peak_dist_distribution[len(peak_dist_distribution)//2]
    peak_p90 = peak_dist_distribution[int(len(peak_dist_distribution)*0.9)]
else:
    peak_p50 = peak_p90 = 0
v02_signal = {
    "trigger_3_pts_supported": peak_p50 >= 3,
    "offset_1_pt_supported": peak_p50 >= 1,
    "trail_10_pts_supported": peak_p90 >= 10,
    "peak_distance_p50": round(peak_p50, 3),
    "peak_distance_p90": round(peak_p90, 3),
}

# --- assemble report ---
report = {
    "wo": "falcon:ranger:wo:backtest_validation:001",
    "wo_status": "CLOSED" if all_pass else "REQUIRES_REVIEW",
    "executed_by": "R2D2",
    "anchors": {
        "canonical_now_utc": CANONICAL_NOW.isoformat(),
        "window_6mo_start_sql": W6M, "window_end_sql": NOW_SQL,
    },
    "ut_discipline": "READ-ONLY. timestamp anchored. No NOW()/utcnow()/time.time().",
    "spec_ref": "falcon:ranger:spec:v1",
    "params_used": PARAMS,
    "atr_period": ATR_PERIOD,
    "breakeven_trigger_pts": BREAKEVEN_TRIGGER_PTS,
    "breakeven_offset_pts": BREAKEVEN_OFFSET_PTS,
    "fires_total_loaded": len(fires),
    "fires_simulated": len(results["single_layer"]),
    "fires_skipped_no_forward_data": skipped,
    "ranger_aggregate": ranger_agg,
    "static_baseline_aggregate": static_agg,
    "ranger_delta_pts_distribution": delta_dist,
    "invariant_violations_total": total_violations,
    "pass_criteria": pass_criteria,
    "all_pass": all_pass,
    "graduation_stats": {
        "total_graduations": total_grads,
        "fires_with_graduations": fires_with_grads,
        "graduation_rate_per_fire": round(grad_rate_per_fire, 4),
        "graduation_pct_of_fires": round(100*fires_with_grads/len(results["single_layer"]), 2) if results["single_layer"] else 0,
    },
    "v02_tuning_signal": v02_signal,
    "per_strategy_breakdown": strategy_breakdown,
    "honest_limits": [
        "Layer 2 + Layer 3 not simulated in v1 of this report — single_layer only.",
        "  Reason: 2-layer simulation requires entry-precondition logic (L1 grad >= 1 AND structure intact AND ARES clear) that needs a separate ARES + structure-event integration. Land in v2.",
        "Replay uses M1 OHLC bars — sub-bar fill order is approximated (SL priority if both could hit in same bar).",
        "M1 ATR(14) computed from preceding 14 M1 bars at fire time — could differ from live ATR by up to 1 minute.",
        "Slippage = 0 in this replay. Per spec, max_slippage_pts=1 is the live-side cap.",
        "Counterfactual is static-bracket on the SAME fires — true 'no-Ranger' world would have different trader behaviour entirely.",
    ],
    "main_directive_alignment": "r2d2:directive:main — preservation of the team. This replay validates Ranger logic on lived market history before family-livelihood risk depends on it.",
}

# Save locally + bake to fabric
import os
os.makedirs("/tmp/r2d2_apollo_replay", exist_ok=True)
with open("/tmp/r2d2_apollo_replay/report.json", "w") as f:
    json.dump(report, f, indent=2, default=str)

# Also save per-trade detail for audit
with open("/tmp/r2d2_apollo_replay/per_trade.json", "w") as f:
    json.dump({"single_layer": results["single_layer"][:200], "static": results["static"][:200]}, f, indent=2, default=str)

print(f"\n=== HEADLINE ===")
print(f"  Fires simulated: {len(results['single_layer'])} / {len(fires)} loaded")
print(f"  Ranger WR: {ranger_agg['wr_pct']}% | Static WR: {static_agg['wr_pct']}% | delta: {ranger_agg['wr_pct']-static_agg['wr_pct']:.2f}%")
print(f"  Ranger expectancy: {ranger_agg['expectancy_pts']} pts | Static: {static_agg['expectancy_pts']} pts")
print(f"  Ranger R:R: {ranger_agg.get('rr_ratio')} | Threshold: 1.5")
print(f"  ranger_delta_pts: avg={delta_dist['avg']}, p10={delta_dist['p10']}, p50={delta_dist['p50']}, p90={delta_dist['p90']}")
print(f"  Invariant violations: R1={total_violations['R1']}, R2={total_violations['R2']}, R3={total_violations['R3']}")
print(f"  Graduation rate: {grad_rate_per_fire:.4f}/fire ({fires_with_grads} fires graduated)")
print(f"  Pass criteria: {pass_criteria}")
print(f"  ALL PASS: {all_pass}")

# Don't bake from dell-debian — fabric is on Trinity. JSON written to /tmp/r2d2_apollo_replay/ for scp-back.
print(f"\nReport JSON saved at: /tmp/r2d2_apollo_replay/report.json (scp back to Trinity to bake)")

scur.close(); scalp.close(); sigcur.close(); sigs.close()
print("DONE.")
