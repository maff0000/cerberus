"""CSDR State Machine — pure-Python port for Apollo replay.
Mirrors /srv-dev/falcon/strategies/csdr/{worker,sweep,fvg,scoring,state}.py
plus /srv-dev/falcon/core/displacement_detector.py logic.

Used by csdr_session_sweep harness to replay 6mo XAU history under varied params.
READ-ONLY — no DB writes from here.
"""
from typing import Optional, List, Dict, Tuple

# =====================================================================
# Sweep detection (mirrors falcon/strategies/csdr/sweep.py)
# =====================================================================
def detect_sweep(candle: dict, comp_high: float, comp_low: float,
                 atr: float, min_ext_atr: float) -> Optional[dict]:
    if atr <= 0: return None
    h = float(candle["high"]); l = float(candle["low"]); c = float(candle["close"])
    min_ext = min_ext_atr * atr
    if h > comp_high + min_ext and c <= comp_high:
        return {"sweep_side":"HIGH","sweep_extreme":h,"direction":"SHORT",
                "extension_atr":(h - comp_high)/atr}
    if l < comp_low - min_ext and c >= comp_low:
        return {"sweep_side":"LOW","sweep_extreme":l,"direction":"LONG",
                "extension_atr":(comp_low - l)/atr}
    return None

# =====================================================================
# Displacement detection (mirrors falcon/core/displacement_detector.py)
# =====================================================================
def detect_displacement(candles: list, atr: float, min_disp_atr: float) -> Optional[dict]:
    if not candles or len(candles) < 3 or atr <= 0: return None
    latest = candles[-1]; prev = candles[-2]
    move = float(latest["close"]) - float(prev["close"])
    move_atr = abs(move) / atr
    if move_atr < min_disp_atr: return None
    direction = "UP" if move > 0 else "DOWN"
    lbl = min(float(latest["open"]), float(latest["close"]))
    lbh = max(float(latest["open"]), float(latest["close"]))
    pbl = min(float(prev["open"]), float(prev["close"]))
    pbh = max(float(prev["open"]), float(prev["close"]))
    overlap = max(0, pbh - lbl) if direction == "UP" else max(0, lbh - pbl)
    body = lbh - lbl
    if body > 0 and overlap / body > 0.5: return None
    return {"direction": direction, "displacement_size_atr": move_atr,
            "extreme_price": float(latest["high"]) if direction == "UP" else float(latest["low"])}

# =====================================================================
# FVG detection (mirrors falcon/strategies/csdr/fvg.py)
# =====================================================================
def detect_fvg(candles: list, direction: str, atr: float, min_fvg_atr: float) -> Optional[dict]:
    if len(candles) < 3 or atr <= 0: return None
    c1 = candles[-3]; c3 = candles[-1]
    if direction == "LONG":
        bot = float(c1["high"]); top = float(c3["low"])
        if top <= bot: return None
    elif direction == "SHORT":
        top = float(c1["low"]); bot = float(c3["high"])
        if top <= bot: return None
    else: return None
    sz = top - bot
    sz_atr = sz / atr
    if sz_atr < min_fvg_atr: return None
    return {"fvg_top": top, "fvg_bottom": bot, "fvg_mid": (top+bot)/2,
            "fvg_size": sz, "fvg_size_atr": sz_atr}

def check_retest(candle: dict, fvg_top: float, fvg_bottom: float, fvg_mid: float,
                 entry_model: str) -> Optional[dict]:
    h = float(candle["high"]); l = float(candle["low"]); c = float(candle["close"])
    if entry_model == "touch":
        if l <= fvg_top and h >= fvg_bottom:
            entry = fvg_top if c < fvg_mid else fvg_bottom
            return {"entry_price": entry}
    elif entry_model == "midpoint":
        if l <= fvg_mid and h >= fvg_mid:
            return {"entry_price": fvg_mid}
    elif entry_model == "confirmation":
        if l <= fvg_top and h >= fvg_bottom:
            return {"entry_price": c}
    return None

def fvg_invalidated(candle: dict, fvg_top: float, fvg_bottom: float, direction: str) -> bool:
    c = float(candle["close"])
    if direction == "LONG":  return c < fvg_bottom
    if direction == "SHORT": return c > fvg_top
    return False

# =====================================================================
# Scoring (mirrors falcon/strategies/csdr/scoring.py)
# =====================================================================
def score_setup(comp_q, sweep_q, disp_q, fvg_q, sess_q, htf_q, struct_q,
                w_comp, w_sweep, w_disp, w_fvg, w_sess, w_htf, w_struct):
    total = w_comp + w_sweep + w_disp + w_fvg + w_sess + w_htf + w_struct
    if total <= 0: return 0
    weighted = (comp_q*w_comp + sweep_q*w_sweep + disp_q*w_disp + fvg_q*w_fvg
                + sess_q*w_sess + htf_q*w_htf + struct_q*w_struct)
    return round((weighted / total) * 100)

# =====================================================================
# CSDR Replay Engine — walks M15 candles + M1 candles forward
# Tracks 8-state machine. Emits a "proposal" event when an entry
# would have fired. Caller simulates trade outcome from forward bars.
# =====================================================================
SESSION_QUALITY = {"LONDON": 1.0, "NY": 0.9, "LONDON_NY_OVERLAP": 1.0,
                   "ASIA": 0.3, "LATE_NY": 0.1, "DEAD": 0.0}

def session_for_hour(h: int) -> str:
    """Match worker.py session classification."""
    if 8 <= h < 12: return "LONDON"
    if 12 <= h < 13: return "LONDON_NY_OVERLAP"  # London/NY overlap window
    if 13 <= h <= 16: return "NY"
    if 0 <= h < 7: return "ASIA"
    if 17 <= h <= 20: return "NY"   # extended NY
    return "LATE_NY" if 17 <= h <= 23 else "DEAD"

def session_bucket(h: int) -> str:
    """Coarse-grained R2D2 session bucket for reporting (4 buckets)."""
    if 0 <= h <= 7: return "ASIA"
    if 8 <= h <= 12: return "LONDON"
    if 13 <= h <= 20: return "NY"
    return "LATE"

def replay_csdr(m15_bars: list, m1_lookup: dict, atr_lookup: dict, params: dict) -> List[dict]:
    """Walk M15 bars forward, run CSDR state machine. Return list of PROPOSAL events.
    Each event = dict with: ts, direction, entry_price, stop_price, target_price, quality, session, atr.

    m15_bars: chronological list of M15 candles [{ts, open, high, low, close}, ...]
    m1_lookup: dict {m15_ts: list of preceding M1 candles for that bar}
    atr_lookup: dict {m15_ts: ATR(14) at that bar}
    params: dict with all CSDR config knobs
    """
    proposals = []
    state = {"mode": "IDLE", "bars_in_state": 0}

    for bar in m15_bars:
        ts = bar["ts"]
        atr = atr_lookup.get(ts)
        m1 = m1_lookup.get(ts, [])
        if atr is None or atr <= 0 or len(m1) < 3:
            continue

        h = bar["ts"].hour
        active_session = session_for_hour(h)

        cur_m15 = {"open": bar["open"], "high": bar["high"], "low": bar["low"], "close": bar["close"]}
        mode = state["mode"]

        # IDLE: detect compression
        if mode == "IDLE":
            lookback = min(params["compression_lookback"], len(m1))
            recent = m1[-lookback:]
            r_high = max(float(c["high"]) for c in recent)
            r_low = min(float(c["low"]) for c in recent)
            r_size = r_high - r_low
            if 0 < r_size <= params["compression_multiplier"] * atr:
                state = {"mode": "COMPRESSION_DETECTED",
                         "compression_high": r_high, "compression_low": r_low,
                         "compression_size": r_size, "bars_in_state": 0}
            continue

        # COMPRESSION_DETECTED: look for sweep
        if mode == "COMPRESSION_DETECTED":
            state["bars_in_state"] += 1
            sweep = detect_sweep(cur_m15, state["compression_high"], state["compression_low"],
                                 atr, params["min_sweep_extension_atr"])
            if sweep:
                state.update({
                    "mode": "SWEEP_DETECTED",
                    "sweep_side": sweep["sweep_side"], "sweep_extreme": sweep["sweep_extreme"],
                    "direction": sweep["direction"], "bars_in_state": 0,
                })
                continue
            if state["bars_in_state"] > params["max_bars_after_sweep"]:
                state = {"mode": "IDLE", "bars_in_state": 0}
            continue

        # SWEEP_DETECTED: look for displacement
        if mode == "SWEEP_DETECTED":
            state["bars_in_state"] += 1
            disp = detect_displacement(m1, atr, params["displacement_atr_min"])
            if disp:
                expected = "UP" if state["direction"] == "LONG" else "DOWN"
                if disp["direction"] == expected and disp["displacement_size_atr"] >= params["displacement_atr_min"]:
                    state["mode"] = "DISPLACEMENT_CONFIRMED"
                    state["displacement_size_atr"] = disp["displacement_size_atr"]
                    state["bars_in_state"] = 0
                    # Fall through to FVG check below
            if state["mode"] == "SWEEP_DETECTED":
                if state["bars_in_state"] > params["max_bars_after_sweep"]:
                    state = {"mode": "IDLE", "bars_in_state": 0}
                continue

        # DISPLACEMENT_CONFIRMED: look for FVG (immediate same-bar attempt)
        if state["mode"] == "DISPLACEMENT_CONFIRMED":
            fvg = detect_fvg(m1, state["direction"], atr, params["min_fvg_atr"])
            if fvg:
                state.update({
                    "mode": "FVG_CONFIRMED",
                    "fvg_top": fvg["fvg_top"], "fvg_bottom": fvg["fvg_bottom"],
                    "fvg_mid": fvg["fvg_mid"], "fvg_size": fvg["fvg_size"],
                    "bars_in_state": 0,
                })
                # Worker.py auto-transitions FVG_CONFIRMED -> RETEST_ARMED in same cycle
                state["mode"] = "RETEST_ARMED"
            else:
                state = {"mode": "IDLE", "bars_in_state": 0}
                continue

        # RETEST_ARMED: wait for retest (could be same bar after FVG_CONFIRMED transition)
        if state["mode"] == "RETEST_ARMED":
            state["bars_in_state"] += 1
            direction = state["direction"]

            # Check FVG invalidation
            if fvg_invalidated(cur_m15, state["fvg_top"], state["fvg_bottom"], direction):
                state = {"mode": "IDLE", "bars_in_state": 0}
                continue

            # Check max retest bars
            if state["bars_in_state"] > params["max_retest_bars"]:
                state = {"mode": "IDLE", "bars_in_state": 0}
                continue

            # Check for retest
            retest = check_retest(cur_m15, state["fvg_top"], state["fvg_bottom"],
                                  state["fvg_mid"], params["entry_model"])
            if retest:
                # Quality gate
                comp_range_atr = state["compression_size"] / atr
                comp_q = max(0.0, min(1.0, 1.0 - comp_range_atr / params["compression_multiplier"]))

                sweep_ext = abs(state["sweep_extreme"] - (state["compression_high"] if state["sweep_side"] == "HIGH" else state["compression_low"])) / atr
                sweep_q = max(0.0, min(1.0, sweep_ext / (params["min_sweep_extension_atr"] * 2)))

                disp_q = max(0.0, min(1.0, state["displacement_size_atr"] / (params["displacement_atr_min"] * 2)))

                fvg_size_atr = state["fvg_size"] / atr
                fvg_q = max(0.0, min(1.0, fvg_size_atr / (params["min_fvg_atr"] * 2)))

                sess_q = SESSION_QUALITY.get(active_session, 0.1)
                htf_q = 0.5
                struct_q = 0.5

                quality = score_setup(
                    comp_q, sweep_q, disp_q, fvg_q, sess_q, htf_q, struct_q,
                    params["weight_compression"], params["weight_sweep"],
                    params["weight_displacement"], params["weight_fvg"],
                    params["weight_session"], params["weight_htf_bias"],
                    params["weight_structure"],
                )

                if quality < params["quality_threshold"]:
                    state = {"mode": "IDLE", "bars_in_state": 0}
                    continue

                # PROPOSAL!
                entry = retest["entry_price"]
                trade_dir = "BUY" if direction == "LONG" else "SELL"
                if trade_dir == "BUY":
                    stop = state["sweep_extreme"] - params["sl_buffer_atr"] * atr
                    sl_dist = entry - stop
                    target = entry + sl_dist * params["tp_r_multiple"]
                else:
                    stop = state["sweep_extreme"] + params["sl_buffer_atr"] * atr
                    sl_dist = stop - entry
                    target = entry - sl_dist * params["tp_r_multiple"]

                proposals.append({
                    "ts": ts,
                    "direction": trade_dir,
                    "entry_price": entry,
                    "stop_price": stop,
                    "target_price": target,
                    "sl_distance_pts": sl_dist,
                    "tp_distance_pts": sl_dist * params["tp_r_multiple"],
                    "quality": quality,
                    "session": session_bucket(h),
                    "atr": atr,
                    "compression_size": state["compression_size"],
                    "sweep_side": state["sweep_side"],
                    "displacement_atr": state["displacement_size_atr"],
                    "fvg_size_atr": state["fvg_size"] / atr,
                })

                # Reset state after proposal
                state = {"mode": "IDLE", "bars_in_state": 0}

    return proposals
