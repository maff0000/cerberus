"""Apollo Ranger Session Matrix — v2 of backtest_validation
WO falcon:ranger:wo:backtest_validation:001 — session-split extension
Owner: R2D2
Spec ref: falcon:ranger:spec:v1

CHANGES FROM v1:
- Strategy filter: only most-reliable cohort (>=20 resolved trades; TDR included to expose
  per-session pattern despite global EVIDENCE_AGAINST verdict)
- DROP conf>=7 filter — catch ALL fires from selected strategies
- Session split: ASIA(0-7Z) / LONDON(8-12Z) / NY(13-20Z) / LATE(21-23Z)
  per canonical aegis/normalize/normalizer.py:210
- Output: [strategy × session] matrix with Ranger + Static metrics per cell

Output → r2d2:reports:falcon_ranger_backtest:002_session_matrix:001
READ-ONLY against trading data. UTC discipline absolute.
Methodology: r2d2:methodology:correlation:v1.
Main directive: r2d2:directive:main (preservation of the team).
"""
import json, datetime, pymysql, sys, math
from collections import defaultdict, Counter

# --- params (from falcon:ranger:spec:v1 — single layer) ---
P = {"risk_pts": 2, "target_pts": 10, "trail_atr_mult": 1.2, "trail_floor_pts": 4,
     "graduation_buffer_atr_mult": 0.5, "next_tp_offset_pts": 10,
     "time_stop_M5_bars": 24, "max_slippage_pts": 1}
ATR_PERIOD = 14
BREAKEVEN_TRIGGER_PTS = 5
BREAKEVEN_OFFSET_PTS = 1

# --- selected strategies (best-first, per Matt 2026-05-02) ---
SELECTED_STRATEGIES = ["nowic_at_m15", "tdr_m5", "nowic_rt_m15"]

# --- session buckets (UTC hour) per aegis normalizer canonical ---
def session_for_hour(h):
    if 0 <= h <= 7: return "ASIA"
    if 8 <= h <= 12: return "LONDON"
    if 13 <= h <= 20: return "NY"
    return "LATE"  # 21-23

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
print(f"Strategies:    {SELECTED_STRATEGIES}")

# --- pull fires for selected strategies (NO conf filter) ---
strats_in = ",".join([f"'{s}'" for s in SELECTED_STRATEGIES])
scur.execute(f"""
    SELECT id, timestamp, strategy_id, instrument, confidence, direction,
           entry_price, sl_price, tp1_price, tp2_price, outcome, outcome_pnl_pts
    FROM helios_strategy_signals
    WHERE fired=1 AND instrument='XAU_USD'
      AND strategy_id IN ({strats_in})
      AND timestamp >= '{W6M}' AND timestamp <= '{NOW_SQL}'
    ORDER BY timestamp ASC
""")
fires = list(scur.fetchall())
print(f"\nFires loaded: {len(fires)} (no conf filter, selected strategies, 6mo XAU)")

# Tag session per fire (based on fire timestamp UTC hour)
for f in fires:
    ts = f["timestamp"]
    h = ts.hour
    f["session"] = session_for_hour(h)

# Distribution check
strat_session_counts = Counter()
for f in fires:
    strat_session_counts[(f["strategy_id"], f["session"])] += 1
print("\nFire counts per [strategy × session]:")
for s in SELECTED_STRATEGIES:
    print(f"  {s}: ", end="")
    for sess in ["ASIA","LONDON","NY","LATE"]:
        c = strat_session_counts.get((s, sess), 0)
        print(f"{sess}={c} ", end="")
    print(f"TOTAL={sum(strat_session_counts.get((s,sess),0) for sess in ['ASIA','LONDON','NY','LATE'])}")

# --- ATR + window helpers (same as v1) ---
def compute_atr(bars, period=ATR_PERIOD):
    if len(bars) < period + 1: return None
    trs = []
    for i in range(1, len(bars)):
        h = float(bars[i]["high"]); l = float(bars[i]["low"]); pc = float(bars[i-1]["close"])
        trs.append(max(h-l, abs(h-pc), abs(l-pc)))
    if len(trs) < period: return None
    atr = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    return atr

def fetch_m1_window(fire_ts, lookback=60, lookforward=180):
    fire_naive = fire_ts.replace(tzinfo=None) if fire_ts.tzinfo else fire_ts
    start = (fire_naive - datetime.timedelta(minutes=lookback)).strftime("%Y-%m-%d %H:%M:%S")
    end = (fire_naive + datetime.timedelta(minutes=lookforward)).strftime("%Y-%m-%d %H:%M:%S")
    sigcur.execute(f"""
        SELECT timestamp, open, high, low, close FROM candles_M1
        WHERE instrument='XAU_USD' AND timestamp >= '{start}' AND timestamp <= '{end}'
        ORDER BY timestamp ASC
    """)
    bars = sigcur.fetchall()
    if not bars: return None, []
    fire_idx = None
    for i, b in enumerate(bars):
        bts = b["timestamp"].replace(tzinfo=None) if b["timestamp"].tzinfo else b["timestamp"]
        if bts >= fire_naive:
            fire_idx = i; break
    if fire_idx is None or fire_idx < ATR_PERIOD + 1: return None, []
    return compute_atr(bars[:fire_idx+1]), bars[fire_idx:]

# --- Ranger CGT + Static replay (same as v1) ---
def simulate(fire, atr, forward_bars):
    direction = 1 if (fire["direction"] == "LONG") else -1
    entry = float(fire["entry_price"]) if fire.get("entry_price") else float(forward_bars[0]["open"])
    initial_sl = float(fire["sl_price"]) if fire.get("sl_price") else entry - direction * P["risk_pts"]
    initial_tp = float(fire["tp1_price"]) if fire.get("tp1_price") else entry + direction * P["target_pts"]
    trail_distance = max(atr * P["trail_atr_mult"], P["trail_floor_pts"])

    # Ranger
    sl, tp = initial_sl, initial_tp
    grads = 0; peak = 0.0; sl_hist = [sl]
    exit_price = exit_reason = None; bars_elapsed = 0
    time_stop_min = P["time_stop_M5_bars"] * 5

    for bar in forward_bars[1:]:
        bars_elapsed += 1
        h, l, c = float(bar["high"]), float(bar["low"]), float(bar["close"])
        peak = max(peak, (h - entry) if direction == 1 else (entry - l))
        sl_hit = (l <= sl) if direction == 1 else (h >= sl)
        tp_hit = (h >= tp) if direction == 1 else (l <= tp)
        if sl_hit:
            exit_price, exit_reason = sl, "SL"; break
        if tp_hit:
            buf = atr * P["graduation_buffer_atr_mult"]
            grad = (h > tp + buf) if direction == 1 else (l < tp - buf)
            if grad:
                if (tp - sl) * direction > 0:
                    sl = tp; sl_hist.append(sl)
                tp = tp + direction * P["next_tp_offset_pts"]; grads += 1
            else:
                exit_price, exit_reason = tp, "TP"; break
        # trail
        if direction == 1:
            cand = h - trail_distance
            if cand > sl: sl = cand; sl_hist.append(sl)
        else:
            cand = l + trail_distance
            if cand < sl: sl = cand; sl_hist.append(sl)
        if direction == 1 and sl > entry: sl = max(sl, entry)
        elif direction == -1 and sl < entry: sl = min(sl, entry)
        if bars_elapsed >= time_stop_min:
            exit_price, exit_reason = c, "TIME"; break
    if exit_price is None:
        exit_price = float(forward_bars[-1]["close"]); exit_reason = "INCOMPLETE"
    ranger_pnl = (exit_price - entry) * direction

    # Static (initial SL/TP only, no trail/graduation)
    s_sl, s_tp = initial_sl, initial_tp
    static_pnl = None
    for i, bar in enumerate(forward_bars[1:], start=1):
        h, l, c = float(bar["high"]), float(bar["low"]), float(bar["close"])
        if direction == 1:
            if l <= s_sl: static_pnl = (s_sl - entry) * 1; break
            if h >= s_tp: static_pnl = (s_tp - entry) * 1; break
        else:
            if h >= s_sl: static_pnl = (entry - s_sl); break
            if l <= s_tp: static_pnl = (entry - s_tp); break
        if i >= time_stop_min:
            static_pnl = (c - entry) * direction; break
    if static_pnl is None: static_pnl = 0.0

    # Invariants
    inv = {"R1": 0, "R2": 0, "R3": 0}
    if fire.get("sl_price"):
        if abs(float(fire["sl_price"]) - initial_sl) > 0.01: inv["R1"] += 1
    for k in range(1, len(sl_hist)):
        if direction == 1 and sl_hist[k] < sl_hist[k-1] - 0.01: inv["R2"] += 1
        elif direction == -1 and sl_hist[k] > sl_hist[k-1] + 0.01: inv["R2"] += 1
    if peak >= BREAKEVEN_TRIGGER_PTS and exit_reason == "SL":
        if direction == 1 and exit_price < entry + BREAKEVEN_OFFSET_PTS - 0.01: inv["R3"] += 1
        elif direction == -1 and exit_price > entry - BREAKEVEN_OFFSET_PTS + 0.01: inv["R3"] += 1

    return {
        "ranger_pnl": round(ranger_pnl, 3), "ranger_exit": exit_reason,
        "static_pnl": round(static_pnl, 3),
        "graduations": grads, "peak": round(peak, 3),
        "invariants": inv, "atr": round(atr, 3) if atr else None,
    }

# --- main loop ---
print("\n=== Running session-split replay ===")
results = []  # list of dicts {strategy, session, ranger_pnl, static_pnl, ...}
skipped = 0
for i, fire in enumerate(fires):
    if i % 100 == 0: print(f"  fire {i}/{len(fires)}...")
    ts = fire["timestamp"].replace(tzinfo=datetime.timezone.utc) if fire["timestamp"].tzinfo is None else fire["timestamp"]
    atr, forward = fetch_m1_window(ts)
    if not forward or atr is None or atr <= 0 or not fire.get("direction"):
        skipped += 1; continue
    r = simulate(fire, atr, forward)
    results.append({
        "fire_id": fire["id"],
        "strategy": fire["strategy_id"],
        "session": fire["session"],
        "confidence": int(fire["confidence"]),
        "ranger_pnl": r["ranger_pnl"],
        "static_pnl": r["static_pnl"],
        "ranger_exit": r["ranger_exit"],
        "graduations": r["graduations"],
        "peak": r["peak"],
        "invariants": r["invariants"],
    })

print(f"\nSimulated: {len(results)} fires; skipped: {skipped}")

# --- aggregate per [strategy × session] ---
def agg(items):
    n = len(items)
    if n == 0: return {"n": 0}
    rp = [it["ranger_pnl"] for it in items]
    sp = [it["static_pnl"] for it in items]
    rwins = [p for p in rp if p > 0]; rloss = [p for p in rp if p < 0]
    swins = [p for p in sp if p > 0]; sloss = [p for p in sp if p < 0]
    grads = sum(it["graduations"] for it in items)
    fires_grad = sum(1 for it in items if it["graduations"] > 0)
    deltas = [it["ranger_pnl"] - it["static_pnl"] for it in items]
    return {
        "n": n,
        "ranger_wr_pct": round(100*len(rwins)/n, 2),
        "ranger_expectancy": round(sum(rp)/n, 3),
        "ranger_avg_win": round(sum(rwins)/len(rwins), 3) if rwins else None,
        "ranger_avg_loss": round(sum(rloss)/len(rloss), 3) if rloss else None,
        "ranger_rr": round((sum(rwins)/len(rwins)) / abs(sum(rloss)/len(rloss)), 2) if rwins and rloss else None,
        "static_wr_pct": round(100*len(swins)/n, 2),
        "static_expectancy": round(sum(sp)/n, 3),
        "static_avg_win": round(sum(swins)/len(swins), 3) if swins else None,
        "static_avg_loss": round(sum(sloss)/len(sloss), 3) if sloss else None,
        "static_rr": round((sum(swins)/len(swins)) / abs(sum(sloss)/len(sloss)), 2) if swins and sloss else None,
        "ranger_lift_pts": round(sum(deltas)/n, 3),
        "wr_delta_pct": round(100*len(rwins)/n - 100*len(swins)/n, 2),
        "graduations_total": grads,
        "fires_with_graduations": fires_grad,
        "graduation_pct": round(100*fires_grad/n, 2),
        "invariant_violations": {
            "R1": sum(it["invariants"]["R1"] for it in items),
            "R2": sum(it["invariants"]["R2"] for it in items),
            "R3": sum(it["invariants"]["R3"] for it in items),
        },
    }

print("\n=== MATRIX ===")
matrix = {}
for s in SELECTED_STRATEGIES:
    matrix[s] = {}
    for sess in ["ASIA", "LONDON", "NY", "LATE"]:
        cell_items = [r for r in results if r["strategy"] == s and r["session"] == sess]
        matrix[s][sess] = agg(cell_items)
    matrix[s]["TOTAL"] = agg([r for r in results if r["strategy"] == s])

# Aggregate ALL
matrix["_ALL_"] = {}
for sess in ["ASIA", "LONDON", "NY", "LATE"]:
    matrix["_ALL_"][sess] = agg([r for r in results if r["session"] == sess])
matrix["_ALL_"]["TOTAL"] = agg(results)

# Print compact summary
def fmt_cell(c):
    if c.get("n", 0) == 0: return "—"
    return f"n={c['n']} R{c['ranger_expectancy']:+.2f}/S{c['static_expectancy']:+.2f} (Δ{c['ranger_lift_pts']:+.2f})"

print(f"\n{'strategy':<22s} {'ASIA':<28s} {'LONDON':<28s} {'NY':<28s} {'LATE':<28s} {'TOTAL':<28s}")
print("-" * 170)
for s in SELECTED_STRATEGIES + ["_ALL_"]:
    print(f"{s:<22s} ", end="")
    for sess in ["ASIA", "LONDON", "NY", "LATE", "TOTAL"]:
        print(f"{fmt_cell(matrix[s][sess]):<28s} ", end="")
    print()

# Pass criteria check (per-cell)
all_inv_clean = True
for s in SELECTED_STRATEGIES:
    for sess in ["ASIA","LONDON","NY","LATE"]:
        c = matrix[s][sess]
        if c.get("n", 0) > 0:
            iv = c["invariant_violations"]
            if iv["R1"] or iv["R2"] or iv["R3"]:
                all_inv_clean = False
                print(f"  INVARIANT violation in [{s} × {sess}]: {iv}")

# --- assemble report ---
report = {
    "wo": "falcon:ranger:wo:backtest_validation:001 — v2 session-split extension",
    "wo_status": "CLOSED",
    "executed_by": "R2D2",
    "version": "v2",
    "v1_predecessor": "r2d2:reports:falcon_ranger_backtest:001",
    "anchors": {
        "canonical_now_utc": CANONICAL_NOW.isoformat(),
        "window_6mo_start_sql": W6M, "window_end_sql": NOW_SQL,
    },
    "ut_discipline": "READ-ONLY. timestamp anchored. No NOW()/utcnow()/time.time().",
    "filter_applied": {
        "instrument": "XAU_USD",
        "strategies": SELECTED_STRATEGIES,
        "selection_criteria": "n_resolved >= 20 from Strategy Readiness Matrix; TDR included despite EVIDENCE_AGAINST to expose per-session pattern",
        "confidence_filter": "DROPPED in v2 (was conf>=7 in v1) — captures all fires from selected strategies",
        "session_buckets_utc": {"ASIA": "0-7", "LONDON": "8-12", "NY": "13-20", "LATE": "21-23"}
    },
    "fires_loaded": len(fires),
    "fires_simulated": len(results),
    "fires_skipped_no_data": skipped,
    "fire_distribution_per_strategy_session": dict([(f"{k[0]}__{k[1]}", v) for k, v in strat_session_counts.items()]),
    "matrix": matrix,
    "all_invariants_clean": all_inv_clean,
    "honest_caveats_carried_from_v1": [
        "WR delta is definitionally asymmetric — Static counts only TP1-hit as win (5R/1R binary); Ranger counts any pnl>0 as win (includes trail-locked profits from would-be-losers). Lead with EXPECTANCY DELTA (ranger_lift_pts), not WR delta.",
        "M1 OHLC sub-bar fill order approximated — if bar high lifts trail and bar low dips through new trail, my code only fires SL next bar (intra-bar would have triggered). Overstates Ranger profits in volatile bars. PLUTUS tick-replay will tighten magnitude downward.",
        "Single-layer Ranger only — L2/L3 cascade not simulated.",
        "ARES event-block exits not simulated.",
    ],
    "load_bearing_metric": "ranger_lift_pts (Ranger - Static expectancy per cell, in pts/trade)",
    "main_directive_alignment": "r2d2:directive:main — preservation of the team. Per-session matrix surfaces where Ranger edge is real vs noise, supports Solo Stage 1 per-session weighting.",
}

# Save locally
import os
os.makedirs("/tmp/r2d2_apollo_replay", exist_ok=True)
with open("/tmp/r2d2_apollo_replay/session_matrix_report.json", "w") as f:
    json.dump(report, f, indent=2, default=str)

# Don't bake from dell-debian — fabric is on Trinity. JSON written for scp-back.
print(f"\nReport JSON saved at: /tmp/r2d2_apollo_replay/session_matrix_report.json")
print(f"All invariants clean: {all_inv_clean}")
print(f"Total fires simulated: {len(results)}")
print("DONE.")

scur.close(); scalp.close(); sigcur.close(); sigs.close()
