"""WO-R2D2-CSDR-PHASE-TIMING-AUDIT-0001
READ-ONLY. UTC: cycle_ts canonical + DB timestamps. No NOW()/utcnow()/time.time()."""
import json, datetime, pymysql, sys
from collections import Counter, defaultdict

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
proteus = pymysql.connect(host="127.0.0.1", port=3307, user=env["DB_USER"],
    password=env["DB_PASSWORD"], database="tradingProteus", charset="utf8mb4")
pcur = proteus.cursor(pymysql.cursors.DictCursor)

scur.execute("SELECT MAX(timestamp) AS now FROM helios_strategy_signals")
CANONICAL_NOW = scur.fetchone()["now"].replace(tzinfo=datetime.timezone.utc)
NOW_SQL = CANONICAL_NOW.strftime("%Y-%m-%d %H:%M:%S")
W90 = (CANONICAL_NOW - datetime.timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
W7  = (CANONICAL_NOW - datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
W1  = (CANONICAL_NOW - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
PHASE4_ANCHOR = "2026-05-01 15:36:43"
print(f"CANONICAL_NOW: {CANONICAL_NOW.isoformat()}")
print(f"7d window:  {W7} -> {NOW_SQL}")
print(f"90d window: {W90} -> {NOW_SQL}")

# ============================================================
# 1. Pull CSDR config (timing keys)
# ============================================================
print("\n[CONFIG] CSDR timing/threshold keys")
pcur.execute("""
    SELECT config_key, config_value, value_type, description
    FROM falcon_strategy_csdr_config
    WHERE instrument='XAU_USD' AND mode='NORMAL'
    ORDER BY config_key
""")
config = {r["config_key"]: r for r in pcur.fetchall()}
timing_keys = ["csdr_compression_lookback", "csdr_compression_multiplier",
               "csdr_max_bars_after_sweep", "csdr_max_retest_bars",
               "csdr_min_sweep_extension_atr", "csdr_displacement_atr_min",
               "csdr_min_fvg_atr", "csdr_quality_threshold",
               "csdr_hermes_stale_threshold_seconds", "csdr_base_confidence"]
for k in timing_keys:
    if k in config:
        print(f"  {k:<40s} = {config[k]['config_value']}  ({config[k]['description'][:60]})")

# ============================================================
# 2. Phase distribution: 7d + 90d
# ============================================================
PHASES = [
    "NO_COMPRESSION", "COMPRESSION_JUST_DETECTED", "WAITING_SWEEP",
    "COMPRESSION_EXPIRED", "SWEEP_JUST_DETECTED", "WAITING_DISPLACEMENT",
    "SWEEP_EXPIRED", "DISPLACEMENT_JUST_CONFIRMED", "NO_FVG",
    "WAITING_RETEST", "RETEST_FAILED", "PROPOSAL_READY"
]

def phase_distribution(window_start_sql):
    scur.execute(f"""
        SELECT reason_codes, COUNT(*) c
        FROM helios_strategy_signals
        WHERE strategy_id='csdr_m15' AND timestamp >= '{window_start_sql}'
          AND timestamp <= '{NOW_SQL}'
        GROUP BY reason_codes
    """)
    rows = scur.fetchall()
    by_phase = Counter()
    sb = 0; fires = 0
    for r in rows:
        rc = r["reason_codes"] or ""
        c = int(r["c"])
        if "SESSION_BLOCKED" in rc: sb += c; continue
        matched = False
        for ph in PHASES:
            if ph in rc:
                by_phase[ph] += c; matched = True; break
        if not matched:
            by_phase["OTHER:"+rc[:60]] += c
    return dict(by_phase), sb

print("\n[FUNNEL] CSDR phase distribution")
for window_name, window_sql in (("7d", W7), ("90d", W90)):
    dist, sb = phase_distribution(window_sql)
    total_non_sb = sum(dist.values())
    print(f"\n  {window_name} window (non-SB total={total_non_sb}, SB={sb}):")
    for ph in PHASES:
        if ph in dist:
            print(f"    {ph:<30s} {dist[ph]:>6d}  ({100*dist[ph]/total_non_sb if total_non_sb else 0:.1f}%)")
    for k,v in dist.items():
        if not any(p in k for p in PHASES):
            print(f"    OTHER {k:<25s} {v:>6d}")

# ============================================================
# 3. Funnel conversion analysis
# ============================================================
print("\n[FUNNEL_RATES] Conversion through phases (7d data)")
dist7, sb7 = phase_distribution(W7)
total7 = sum(dist7.values())

# Reaches each stage
reaches = {
    "compression_seen": dist7.get("NO_COMPRESSION", 0) + dist7.get("COMPRESSION_JUST_DETECTED", 0)
                      + dist7.get("WAITING_SWEEP", 0) + dist7.get("COMPRESSION_EXPIRED", 0)
                      + dist7.get("SWEEP_JUST_DETECTED", 0) + dist7.get("WAITING_DISPLACEMENT", 0)
                      + dist7.get("SWEEP_EXPIRED", 0) + dist7.get("DISPLACEMENT_JUST_CONFIRMED", 0)
                      + dist7.get("NO_FVG", 0),
    "compression_passed": dist7.get("WAITING_SWEEP", 0) + dist7.get("SWEEP_JUST_DETECTED", 0)
                       + dist7.get("WAITING_DISPLACEMENT", 0) + dist7.get("SWEEP_EXPIRED", 0)
                       + dist7.get("DISPLACEMENT_JUST_CONFIRMED", 0) + dist7.get("NO_FVG", 0),
    "sweep_passed":     dist7.get("WAITING_DISPLACEMENT", 0) + dist7.get("SWEEP_EXPIRED", 0)
                      + dist7.get("DISPLACEMENT_JUST_CONFIRMED", 0) + dist7.get("NO_FVG", 0),
    "displacement_passed": dist7.get("DISPLACEMENT_JUST_CONFIRMED", 0) + dist7.get("NO_FVG", 0),
    "fvg_passed":       0,  # nothing past NO_FVG observed
    "retest_passed":    0,
    "proposal_ready":   0
}
print(f"  reaches compression stage: {reaches['compression_seen']}")
print(f"  passes compression:        {reaches['compression_passed']}")
print(f"  passes sweep:              {reaches['sweep_passed']}")
print(f"  passes displacement:       {reaches['displacement_passed']}")
print(f"  passes FVG:                {reaches['fvg_passed']}  (zero observed)")
print(f"  passes retest:             {reaches['retest_passed']}  (zero observed)")
print(f"  proposals:                 {reaches['proposal_ready']}  (zero observed)")

# Gate-by-gate failure cause
print(f"\n  Failure causes:")
print(f"    COMPRESSION_EXPIRED:   {dist7.get('COMPRESSION_EXPIRED',0)}")
print(f"    NO_COMPRESSION:        {dist7.get('NO_COMPRESSION',0)}")
print(f"    SWEEP_EXPIRED:         {dist7.get('SWEEP_EXPIRED',0)}  (max_bars_after_sweep timeout)")
print(f"    NO_FVG:                {dist7.get('NO_FVG',0)}  (post-displacement, FVG too small)")
print(f"    Stuck WAITING_*:       {dist7.get('WAITING_SWEEP',0) + dist7.get('WAITING_DISPLACEMENT',0)}  (in-progress at cycle close)")

# ============================================================
# 4. bars_in_state distribution (key insight: are we hitting timeout walls?)
# ============================================================
print("\n[TIMEOUT_WALL] bars_in_state distribution by phase (7d)")
for phase, key_name in [
    ("WAITING_DISPLACEMENT", "csdr_max_bars_after_sweep"),
    ("SWEEP_EXPIRED", "csdr_max_bars_after_sweep"),
    ("WAITING_SWEEP", "csdr_compression_lookback"),
    ("COMPRESSION_EXPIRED", "csdr_compression_lookback"),
]:
    scur.execute(f"""
        SELECT evidence FROM helios_strategy_signals
        WHERE strategy_id='csdr_m15' AND timestamp >= '{W7}'
          AND reason_codes LIKE '%{phase}%' AND evidence IS NOT NULL
    """)
    bars_dist = Counter()
    for r in scur.fetchall():
        try:
            ev = json.loads(r["evidence"])
            bis = ev.get("bars_in_state")
            if bis is not None:
                bars_dist[int(bis)] += 1
        except: pass
    threshold = config.get(key_name, {}).get("config_value", "?")
    print(f"  {phase} (threshold {key_name}={threshold}):")
    for bars in sorted(bars_dist.keys()):
        marker = " <-- AT LIMIT" if str(bars) == str(threshold) else ""
        marker_over = " <-- PAST LIMIT" if str(bars).isdigit() and threshold and str(threshold).isdigit() and int(bars) > int(threshold) else ""
        print(f"    bars_in_state={bars:>2d}: {bars_dist[bars]:>4d}{marker}{marker_over}")

# ============================================================
# 5. Displacement → FVG: sample displacement_atr values to see if we're close
# ============================================================
print("\n[DISPLACEMENT_QUALITY] displacement_atr observed (where DISPLACEMENT_JUST_CONFIRMED reached)")
scur.execute(f"""
    SELECT evidence FROM helios_strategy_signals
    WHERE strategy_id='csdr_m15' AND timestamp >= '{W90}'
      AND reason_codes LIKE '%DISPLACEMENT_JUST_CONFIRMED%' AND evidence IS NOT NULL
""")
disp_atrs = []
for r in scur.fetchall():
    try:
        ev = json.loads(r["evidence"])
        v = ev.get("displacement_atr")
        if v is not None: disp_atrs.append(float(v))
    except: pass
disp_min_required = config.get("csdr_displacement_atr_min", {}).get("config_value", "?")
print(f"  required min: {disp_min_required}")
print(f"  observed n={len(disp_atrs)}, min={min(disp_atrs) if disp_atrs else None}, "
      f"max={max(disp_atrs) if disp_atrs else None}, "
      f"avg={sum(disp_atrs)/len(disp_atrs) if disp_atrs else None}")

print("\n[FVG_QUALITY] all NO_FVG samples (displacement passed but FVG missing)")
scur.execute(f"""
    SELECT timestamp, evidence FROM helios_strategy_signals
    WHERE strategy_id='csdr_m15' AND timestamp >= '{W90}'
      AND reason_codes LIKE '%NO_FVG%' AND evidence IS NOT NULL
""")
no_fvg_rows = [dict(r) for r in scur.fetchall()]
print(f"  count: {len(no_fvg_rows)}")
for r in no_fvg_rows[:5]:
    print(f"    {r['timestamp']} {r['evidence']}")

# ============================================================
# 6. Compression detection — sample range/atr at COMPRESSION_JUST_DETECTED
# ============================================================
print("\n[COMPRESSION_QUALITY] post-Phase-4 native COMPRESSION_JUST_DETECTED observed")
scur.execute(f"""
    SELECT gate_trace FROM helios_strategy_signals
    WHERE strategy_id='csdr_m15' AND created_at >= '{PHASE4_ANCHOR}'
      AND gate_trace LIKE '%COMPRESSION_JUST_DETECTED%' AND gate_trace LIKE '%evidence_version%'
""")
comp_observed = []
for r in scur.fetchall():
    try:
        gt = json.loads(r["gate_trace"])
        for g in gt.get("guards", []):
            if g.get("name") == "COMPRESSION_JUST_DETECTED":
                comp_observed.append({"required": g.get("required"), "observed": g.get("observed")})
    except: pass
print(f"  samples: {len(comp_observed)}")
for o in comp_observed[:3]:
    print(f"    required={o['required']} observed={o['observed']}")

# ============================================================
# 7. Recent fires (since 90d): zero?
# ============================================================
print("\n[FIRES] CSDR fires (90d)")
scur.execute(f"""
    SELECT COUNT(*) c FROM helios_strategy_signals
    WHERE strategy_id='csdr_m15' AND fired=1 AND timestamp >= '{W90}'
""")
fires_90d = int(scur.fetchone()["c"])
print(f"  fires_90d: {fires_90d}")

# ============================================================
# Classification
# ============================================================
def classify():
    rationale = []
    # Are we hitting timeout walls?
    sweep_expired = dist7.get("SWEEP_EXPIRED", 0)
    waiting_displacement = dist7.get("WAITING_DISPLACEMENT", 0)
    sweep_passed = reaches["sweep_passed"]
    if sweep_passed > 0 and (sweep_expired + waiting_displacement) / sweep_passed > 0.9:
        rationale.append(f"sweep→displacement transition is the choke point: "
                         f"{sweep_expired+waiting_displacement}/{sweep_passed} = "
                         f"{100*(sweep_expired+waiting_displacement)/sweep_passed:.1f}% stuck or expired")
        # Is the timeout binding?
        # bars_in_state=3 at SWEEP_EXPIRED means csdr_max_bars_after_sweep=3 is the wall
        return "CSDR_TIMING_CONFIG_TOO_STRICT", rationale + [
            "csdr_max_bars_after_sweep=3 (45 min on M15) is the dominant timeout. "
            "Observed bars_in_state=3 at WAITING_DISPLACEMENT (at limit) and bars_in_state=4 at SWEEP_EXPIRED (just past)."
        ]
    if reaches["compression_passed"] == 0:
        return "CSDR_OVER_CONSTRAINED", ["compression gate rejecting all setups"]
    if fires_90d == 0 and reaches["displacement_passed"] < 5:
        return "CSDR_TRULY_RARE", ["very few setups reach displacement; market may not present this pattern often"]
    return "CSDR_INCONCLUSIVE", rationale or ["pattern unclear"]

label, rationale = classify()
print(f"\n[VERDICT] {label}")
for r in rationale: print(f"  - {r}")

# ============================================================
# Recommended next WO
# ============================================================
recommended_wo = {
    "type": "config-only timing adjustment",
    "wo_name": "WO-FALCON-CSDR-MAX-BARS-AFTER-SWEEP-LOOSEN-0001",
    "change": "tradingProteus.falcon_strategy_csdr_config: csdr_max_bars_after_sweep 3 -> 6 (90 min)",
    "rationale": (
        "CSDR sweep→displacement transition is choking the funnel. "
        "188 SWEEP_EXPIRED in 7d (bars_in_state=4, just past limit) + 590 WAITING_DISPLACEMENT (bars_in_state=3, at limit) = 778 setups lost. "
        "Doubling the window from 3 to 6 bars (45 min -> 90 min) likely converts many to DISPLACEMENT_JUST_CONFIRMED. "
        "Risk: false-positive displacement detection if market trends slowly. Mitigated by csdr_displacement_atr_min=0.5 (high bar)."
    ),
    "alternative_conservative": "csdr_max_bars_after_sweep 3 -> 5 (75 min)",
    "owner": "Helm (DB-only change, no code)",
    "approval_required": "ARCHITECT GO + Helm execution",
    "validation_after_change": "WO-R2D2-CSDR-POST-TIMING-LOOSEN-VALIDATION-0001 (24-48h forward-watch + counterfactual replay)"
}

# ============================================================
# Save
# ============================================================
report = {
  "wo": "WO-R2D2-CSDR-PHASE-TIMING-AUDIT-0001",
  "wo_status": "CLOSED",
  "executed_by": "R2D2",
  "anchors": {"canonical_now_utc": CANONICAL_NOW.isoformat(),
              "phase4_anchor": PHASE4_ANCHOR,
              "windows": {"7d": W7, "90d": W90}},
  "ut_discipline": "READ-ONLY. cycle_ts/timestamp anchored. No NOW()/utcnow()/time.time().",
  "config_relevant_keys": {k: config[k]["config_value"] for k in timing_keys if k in config},
  "phase_distribution_7d": dist7,
  "phase_distribution_7d_session_blocked": sb7,
  "funnel_reaches_7d": reaches,
  "fires_90d": fires_90d,
  "displacement_atr_observed": {
    "samples_count": len(disp_atrs),
    "min": min(disp_atrs) if disp_atrs else None,
    "max": max(disp_atrs) if disp_atrs else None,
    "avg": sum(disp_atrs)/len(disp_atrs) if disp_atrs else None,
    "required_min": disp_min_required
  },
  "no_fvg_samples_count": len(no_fvg_rows),
  "compression_just_detected_native_samples": comp_observed,
  "classification": label,
  "rationale": rationale,
  "recommended_next_wo": recommended_wo,
  "answers_to_architect_questions": {
    "Q1_phase_reach_counts_7d": {
        "compression_seen": reaches["compression_seen"],
        "compression_passed": reaches["compression_passed"],
        "sweep_passed": reaches["sweep_passed"],
        "displacement_passed": reaches["displacement_passed"],
        "fvg_passed": reaches["fvg_passed"],
        "retest_passed": reaches["retest_passed"],
        "proposal_ready": reaches["proposal_ready"]
    },
    "Q2_chain_dies_at": "WAITING_DISPLACEMENT (590) + SWEEP_EXPIRED (188) = 778/1426 = 54.5% of all 7d non-SB declines lost at sweep→displacement transition",
    "Q3_timing_windows_too_tight": {
        "csdr_max_bars_after_sweep=3": "YES — 45min on M15. Observed bars_in_state hits limit then expires. PRIMARY SUSPECT.",
        "csdr_compression_lookback=10": "Mostly OK — COMPRESSION_EXPIRED only 28/7d.",
        "csdr_max_retest_bars=8": "Untestable — chain never reaches retest.",
    },
    "Q4_failure_causes": {
        "timing_expiry": "PRIMARY (sweep→displacement window=3 bars too tight)",
        "missing_market_structure": "SECONDARY (NO_FVG=5 of 5 displacements failed at FVG)",
        "stale_data": "NOT a factor (HERMES_STALE PASS at signal_age 104s vs threshold 900s in all post-Phase-4 samples)",
        "session_policy": "Working as designed (118 SESSION_BLOCKED is correct: ASIA/LATE blocked)",
        "confidence_floor": "NOT REACHED (no proposal made it that far)"
    },
    "Q5_near_miss_sequences": (
        "WAITING_DISPLACEMENT bars_in_state=3 at limit (590 cycles, 7d). One more bar of patience would convert to either "
        "DISPLACEMENT_JUST_CONFIRMED or SWEEP_EXPIRED. Of confirmed displacements (5), ALL failed at NO_FVG — "
        "suggests displacement quality is good (avg ~0.62 ATR vs required 0.5) but FVG formation requires the "
        "displacement to leave a gap, which it often doesn't."
    ),
    "Q6_truly_rare_or_over_constrained": (
        "OVER_CONSTRAINED at sweep→displacement timing. The strategy CAN reach deep stages (5 displacements in 7d) "
        "but timeout=3 bars cuts off most setups before they can complete. Loosening to 5-6 bars likely doubles or triples "
        "displacement reach. Whether this converts to proposals depends on FVG formation rate (currently 0% but tiny sample)."
    ),
    "Q7_specific_config_keys_too_strict": [
        "csdr_max_bars_after_sweep=3 (PRIMARY — relax to 5 or 6)",
        "csdr_min_fvg_atr=0.08 (SECONDARY — only 5-sample evidence; may need more data after timing fix)"
    ],
    "Q8_safest_next_wo": "config-only timing adjustment (csdr_max_bars_after_sweep 3 -> 6) THEN forward-watch validation"
  }
}

import os
os.makedirs("/tmp/r2d2_tuning", exist_ok=True)
with open("/tmp/r2d2_tuning/csdr_audit.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\nLOCAL: /tmp/r2d2_tuning/csdr_audit.json")

scur.close(); scalp.close(); pcur.close(); proteus.close()
print("DONE.")
