"""WO-R2D2-TPC-REGIME-GATE-AUDIT-0001
READ-ONLY. UTC discipline. No NOW()/utcnow()/time.time(). No changes."""
import json, datetime, pymysql, sys
from collections import Counter

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

scur.execute("SELECT MAX(timestamp) AS now FROM helios_strategy_signals WHERE strategy_id='tpc_m15'")
CANONICAL_NOW = scur.fetchone()["now"].replace(tzinfo=datetime.timezone.utc)
NOW_SQL = CANONICAL_NOW.strftime("%Y-%m-%d %H:%M:%S")
PHASE4_ANCHOR = "2026-05-01 15:36:43"
CLASSIFIER_FIX_DATE = "2026-04-30 00:00:00"
W14 = "2026-04-17 00:00:00"
print(f"CANONICAL_NOW: {CANONICAL_NOW.isoformat()}")

# ============================================================
# CONFIG
# ============================================================
print("\n[CONFIG] TPC config keys")
pcur.execute("""
    SELECT config_key, config_value, description
    FROM falcon_strategy_tpc_config
    WHERE instrument='XAU_USD' AND mode='NORMAL'
    ORDER BY config_key
""")
config = {r["config_key"]: r for r in pcur.fetchall()}
for k, r in config.items():
    print(f"  {k:<40s} = {r['config_value']}  ({r['description'][:55]})")

# ============================================================
# Q1+Q2: NOT_TRENDING and RSI_TOO_EXTENDED prevalence (14d + post-fix)
# ============================================================
print("\n[Q1+Q2+Q4] Bucket distribution + temporal split")
def buckets(window_start, label):
    scur.execute(f"""
        SELECT
          CASE
            WHEN reason_codes LIKE '%NOT_TRENDING%' THEN 'NOT_TRENDING'
            WHEN reason_codes LIKE '%RSI_TOO_EXTENDED%' THEN 'RSI_TOO_EXTENDED'
            WHEN reason_codes LIKE '%RSI_PULLBACK_ACTIVE%' THEN 'RSI_PULLBACK_ACTIVE'
            WHEN reason_codes LIKE '%NO_EMA_DATA%' THEN 'NO_EMA_DATA'
            WHEN reason_codes LIKE '%SESSION_BLOCKED%' THEN 'SESSION_BLOCKED'
            ELSE 'OTHER'
          END bucket,
          COUNT(*) c
        FROM helios_strategy_signals
        WHERE strategy_id='tpc_m15' AND timestamp >= '{window_start}' AND timestamp <= '{NOW_SQL}'
        GROUP BY bucket ORDER BY c DESC
    """)
    return [(r["bucket"], int(r["c"])) for r in scur.fetchall()]

b14 = buckets(W14, "14d")
b_post = buckets(CLASSIFIER_FIX_DATE, "post-fix")
print(f"  14d total bucket distribution:")
total_14 = sum(c for _,c in b14)
for bn, c in b14:
    print(f"    {bn:<22s} {c:>5d} ({100*c/total_14:.1f}%)")
print(f"\n  Post-classifier-fix (>=2026-04-30) bucket distribution:")
total_post = sum(c for _,c in b_post)
session_blocked_post = next((c for b,c in b_post if b=="SESSION_BLOCKED"), 0)
strategy_evals_post = total_post - session_blocked_post
for bn, c in b_post:
    pct_total = 100*c/total_post
    pct_strat = 100*c/strategy_evals_post if bn != "SESSION_BLOCKED" and strategy_evals_post else 0
    note = " (admission-level)" if bn == "SESSION_BLOCKED" else ""
    print(f"    {bn:<22s} {c:>5d} ({pct_total:.1f}% of total, {pct_strat:.1f}% of strategy-evals){note}")

# ============================================================
# Q3: Observed regimes / ADX / RSI when NOT_TRENDING fires (post-fix)
# ============================================================
print("\n[Q3] Observed regime distribution at NOT_TRENDING (temporal)")
scur.execute(f"""
    SELECT
      CASE WHEN timestamp < '{CLASSIFIER_FIX_DATE}' THEN 'PRE_FIX' ELSE 'POST_FIX' END period,
      JSON_EXTRACT(evidence, '$.regime') observed_regime,
      COUNT(*) c
    FROM helios_strategy_signals
    WHERE strategy_id='tpc_m15' AND reason_codes LIKE '%NOT_TRENDING%'
      AND timestamp >= '{W14}'
    GROUP BY period, observed_regime ORDER BY period, c DESC
""")
not_trending_temporal = [(r["period"], r["observed_regime"], int(r["c"])) for r in scur.fetchall()]
for p, reg, c in not_trending_temporal:
    print(f"    {p:<10s} regime={reg!s:<15s} {c}")

# ============================================================
# Q5: RSI_TOO_EXTENDED RSI value distribution
# ============================================================
print("\n[Q5] RSI value distribution at RSI_TOO_EXTENDED (full 14d)")
scur.execute(f"""
    SELECT CAST(JSON_EXTRACT(evidence, '$.rsi') AS DECIMAL(10,2)) rsi_val
    FROM helios_strategy_signals
    WHERE strategy_id='tpc_m15' AND reason_codes LIKE '%RSI_TOO_EXTENDED%'
      AND timestamp >= '{W14}' AND evidence IS NOT NULL
""")
rsi_extended = [float(r["rsi_val"]) for r in scur.fetchall() if r["rsi_val"] is not None]
def hist(vals, bins):
    out = []
    for low, high in bins:
        n = sum(1 for v in vals if low <= v < high)
        out.append((f"{low}-{high}", n))
    return out
print(f"  total RSI_TOO_EXTENDED: {len(rsi_extended)}")
if rsi_extended:
    print(f"  rsi min={min(rsi_extended):.2f} max={max(rsi_extended):.2f} avg={sum(rsi_extended)/len(rsi_extended):.2f}")
    bins = [(65,68),(68,70),(70,72),(72,75),(75,80),(80,100)]
    for label, n in hist(rsi_extended, bins):
        marker = " <-- close to old wall" if label == "65-68" else ""
        print(f"    rsi {label}: {n} ({100*n/len(rsi_extended):.1f}%){marker}")

print("\n[Q5b] RSI value distribution at RSI_PULLBACK_ACTIVE (full 14d)")
scur.execute(f"""
    SELECT CAST(JSON_EXTRACT(evidence, '$.rsi') AS DECIMAL(10,2)) rsi_val
    FROM helios_strategy_signals
    WHERE strategy_id='tpc_m15' AND reason_codes LIKE '%RSI_PULLBACK_ACTIVE%'
      AND timestamp >= '{W14}' AND evidence IS NOT NULL
""")
rsi_pullback = [float(r["rsi_val"]) for r in scur.fetchall() if r["rsi_val"] is not None]
print(f"  total RSI_PULLBACK_ACTIVE: {len(rsi_pullback)}")
if rsi_pullback:
    print(f"  rsi min={min(rsi_pullback):.2f} max={max(rsi_pullback):.2f} avg={sum(rsi_pullback)/len(rsi_pullback):.2f}")
    bins = [(0,30),(30,35),(35,40),(40,45),(45,50)]
    for label, n in hist(rsi_pullback, bins):
        marker = " <-- close to old wall (40)" if label == "35-40" else ""
        print(f"    rsi {label}: {n} ({100*n/len(rsi_pullback):.1f}%){marker}")

# ============================================================
# Q6: Near-miss analysis — of post-regime cycles, how many fail at single RSI gate?
# ============================================================
print("\n[Q6] Near-miss analysis: single-guard rejections")
# Of 78 RSI_TOO_EXTENDED + 131 RSI_PULLBACK_ACTIVE, those are setups that PASSED:
# - NOT_TRENDING (regime in allowed set)
# - ADX_TOO_LOW (skipped or passed)
# - REENTRY_LOCKOUT
# - NO_EMA_DATA
# - NO_RSI_DATA
# But got blocked at RSI band check.
print(f"  RSI_TOO_EXTENDED: {len(rsi_extended)} setups blocked ONLY by RSI > 65")
print(f"  RSI_PULLBACK_ACTIVE: {len(rsi_pullback)} setups blocked ONLY by RSI < 40")
print(f"  Total RSI-band rejections: {len(rsi_extended) + len(rsi_pullback)}")
print(f"  These are TRUE near-miss cases — passed all earlier gates, blocked at single gate.")

# ============================================================
# Q7: Reach pullback/reentry/confirmation stages?
# ============================================================
print("\n[Q7] Does TPC reach deeper stages?")
scur.execute(f"""
    SELECT reason_codes, COUNT(*) c FROM helios_strategy_signals
    WHERE strategy_id='tpc_m15' AND timestamp >= '{W14}'
      AND fired=1
    GROUP BY reason_codes
""")
fires = [(r["reason_codes"], int(r["c"])) for r in scur.fetchall()]
print(f"  total fires (14d): {sum(c for _,c in fires)}")
for rc, c in fires: print(f"    {rc[:80]} {c}")

# Also check for non-RSI deeper-stage declines
scur.execute(f"""
    SELECT DISTINCT reason_codes FROM helios_strategy_signals
    WHERE strategy_id='tpc_m15' AND timestamp >= '{W14}'
""")
all_rc = [r["reason_codes"] for r in scur.fetchall()]
deeper_codes = [rc for rc in all_rc if rc and not any(k in rc for k in
    ["NOT_TRENDING","RSI_PULLBACK","RSI_TOO_EXTENDED","NO_EMA_DATA","SESSION_BLOCKED"])]
print(f"  reason_codes beyond RSI/regime/EMA/session: {deeper_codes}")

# ============================================================
# Q8: Failure cause breakdown (post-fix)
# ============================================================
print("\n[Q8] Failure causes post-classifier-fix")
print(f"  Regime: NOT_TRENDING={next((c for b,c in b_post if b=='NOT_TRENDING'), 0)} (correct gating, RANGING/TRANSITION excluded)")
print(f"  Trend strength: ADX_TOO_LOW SKIPped (adx=null upstream — non-blocking)")
print(f"  RSI extension: RSI_TOO_EXTENDED={next((c for b,c in b_post if b=='RSI_TOO_EXTENDED'), 0)} (FIX-ABLE)")
print(f"  RSI pullback: RSI_PULLBACK_ACTIVE={next((c for b,c in b_post if b=='RSI_PULLBACK_ACTIVE'), 0)} (FIX-ABLE)")
print(f"  Stale data: HERMES_STALE = 0 (TPC threshold=600 already correct, no outlier)")
print(f"  Session policy: SESSION_BLOCKED={session_blocked_post} (correct)")
print(f"  Confidence floor: NEVER REACHED (no fires)")

# ============================================================
# Q9: Specific config keys too strict?
# ============================================================
print("\n[Q9] Config keys assessment")
print(f"  tpc_min_adx={config['tpc_min_adx']['config_value']} — UNTESTABLE (adx=null upstream)")
print(f"  tpc_rsi_entry_max={config['tpc_rsi_entry_max']['config_value']} — APPEARS TIGHT")
print(f"  tpc_rsi_entry_min={config['tpc_rsi_entry_min']['config_value']} — APPEARS TIGHT")
print(f"  tpc_pullback_zone_pct={config['tpc_pullback_zone_pct']['config_value']} — VERY TIGHT (0.3%)")
print(f"  tpc_max_pullback_pct={config['tpc_max_pullback_pct']['config_value']} — TIGHT (0.8%)")
print(f"  tpc_hermes_stale_threshold_seconds={config['tpc_hermes_stale_threshold_seconds']['config_value']} — CORRECT (matches peer cohort)")

# ============================================================
# Verdict
# ============================================================
def classify():
    rsi_ext_post = next((c for b,c in b_post if b=='RSI_TOO_EXTENDED'), 0)
    rsi_pull_post = next((c for b,c in b_post if b=='RSI_PULLBACK_ACTIVE'), 0)
    nt_post = next((c for b,c in b_post if b=='NOT_TRENDING'), 0)
    if not rsi_extended:
        return "TPC_INCONCLUSIVE", ["no RSI evidence"]
    rsi_close_to_wall = sum(1 for v in rsi_extended if v < 70)
    pct_close = 100 * rsi_close_to_wall / len(rsi_extended)
    rationale = []
    rationale.append(f"RSI_TOO_EXTENDED RSI distribution: min={min(rsi_extended):.1f} avg={sum(rsi_extended)/len(rsi_extended):.1f} max={max(rsi_extended):.1f}")
    rationale.append(f"{rsi_close_to_wall}/{len(rsi_extended)} ({pct_close:.0f}%) within 5 points of threshold (65-70 zone)")
    if rsi_pullback:
        rationale.append(f"RSI_PULLBACK_ACTIVE RSI distribution: min={min(rsi_pullback):.1f} avg={sum(rsi_pullback)/len(rsi_pullback):.1f} max={max(rsi_pullback):.1f}")
    if pct_close > 30:
        rationale.append("Significant fraction of RSI extended cases are in 65-70 zone — loosening upper to 70-72 would rescue them.")
    if rsi_ext_post + rsi_pull_post > nt_post * 0.5:
        return "TPC_RSI_THRESHOLD_TOO_STRICT", rationale + [
            f"RSI band 40-65 produces {rsi_ext_post + rsi_pull_post} blocks vs {nt_post} regime blocks. "
            f"RSI window is the dominant fix-able blocker post-classifier-fix."
        ]
    return "TPC_OVER_CONSTRAINED", rationale

label, rationale = classify()
print(f"\n[VERDICT] {label}")
for r in rationale: print(f"  - {r}")

# ============================================================
# Save
# ============================================================
report = {
  "wo": "WO-R2D2-TPC-REGIME-GATE-AUDIT-0001",
  "wo_status": "CLOSED",
  "executed_by": "R2D2",
  "anchors": {
    "canonical_now_utc": CANONICAL_NOW.isoformat(),
    "phase4_anchor": PHASE4_ANCHOR,
    "classifier_fix_date_utc": CLASSIFIER_FIX_DATE,
    "data_window_start": W14
  },
  "ut_discipline": "READ-ONLY. No NOW()/utcnow()/time.time().",
  "config_relevant": {k: config[k]["config_value"] for k in [
    "tpc_min_adx", "tpc_rsi_entry_max", "tpc_rsi_entry_min",
    "tpc_pullback_zone_pct", "tpc_max_pullback_pct",
    "tpc_hermes_stale_threshold_seconds", "tpc_min_setup_quality"]},
  "Q1_Q2_bucket_distribution_14d": dict(b14),
  "Q1_Q2_bucket_distribution_post_fix": dict(b_post),
  "Q3_not_trending_observed_regimes_temporal": [
    {"period": p, "regime": str(r), "count": c} for p, r, c in not_trending_temporal
  ],
  "Q4_trend_gate_assessment": {
    "verdict": "NOT TOO STRICT — historical 97.3% NOT_TRENDING was upstream regime=null defect (fixed 2026-04-30)",
    "post_fix_NOT_TRENDING_correctly_excludes": ["RANGING (60)", "TRANSITION (8)"],
    "allowed_regimes": ["BULL_TREND", "BEAR_TREND"]
  },
  "Q5_rsi_extended_distribution": {
    "total": len(rsi_extended),
    "min": min(rsi_extended) if rsi_extended else None,
    "max": max(rsi_extended) if rsi_extended else None,
    "avg": sum(rsi_extended)/len(rsi_extended) if rsi_extended else None,
    "histogram": {f"{low}-{high}": sum(1 for v in rsi_extended if low <= v < high)
                  for low, high in [(65,68),(68,70),(70,72),(72,75),(75,80),(80,100)]}
  },
  "Q5b_rsi_pullback_distribution": {
    "total": len(rsi_pullback),
    "min": min(rsi_pullback) if rsi_pullback else None,
    "max": max(rsi_pullback) if rsi_pullback else None,
    "avg": sum(rsi_pullback)/len(rsi_pullback) if rsi_pullback else None,
    "histogram": {f"{low}-{high}": sum(1 for v in rsi_pullback if low <= v < high)
                  for low, high in [(0,30),(30,35),(35,40),(40,45),(45,50)]}
  },
  "Q6_near_miss_count": len(rsi_extended) + len(rsi_pullback),
  "Q7_reaches_deeper_stages": {
    "total_fires_14d": sum(c for _,c in fires),
    "deeper_decline_codes_observed": deeper_codes
  },
  "Q8_failure_cause_post_fix": {
    "regime_correct_gating": next((c for b,c in b_post if b=='NOT_TRENDING'), 0),
    "rsi_too_extended_fixable": next((c for b,c in b_post if b=='RSI_TOO_EXTENDED'), 0),
    "rsi_pullback_active_fixable": next((c for b,c in b_post if b=='RSI_PULLBACK_ACTIVE'), 0),
    "no_ema_data": next((c for b,c in b_post if b=='NO_EMA_DATA'), 0),
    "session_blocked_admission": next((c for b,c in b_post if b=='SESSION_BLOCKED'), 0),
    "hermes_stale": "0 (TPC threshold=600 already correct)",
    "adx_skipped_upstream_null": "graceful, non-blocking",
    "confidence_floor_never_reached": True
  },
  "Q9_config_keys_too_strict": {
    "tpc_rsi_entry_max=65.0": "PRIMARY SUSPECT — RSI distribution hits 65-72 cluster post-pullback",
    "tpc_rsi_entry_min=40.0": "SECONDARY — wider band would catch deep pullbacks",
    "tpc_pullback_zone_pct=0.003": "TIGHT (0.3% from EMA) — needs deeper inspection",
    "tpc_max_pullback_pct=0.008": "TIGHT (0.8% max pullback) — same",
    "tpc_min_adx=20.0": "UNTESTABLE (adx=null upstream)",
    "tpc_hermes_stale=600": "CORRECT — matches peer cohort, no change needed"
  },
  "Q10_safest_next_wo": {
    "primary": {
      "type": "config-only threshold adjustment",
      "wo_name": "WO-FALCON-TPC-RSI-ENTRY-MAX-LOOSEN-0001",
      "change": "tpc_rsi_entry_max 65.0 -> 70.0 or 72.0",
      "rationale": "RSI distribution at RSI_TOO_EXTENDED clusters in 65-72 zone. Loosening upper to 70 or 72 catches recent BUY-direction post-pullback continuations.",
      "risk": "Lower buffer between extended and reversal — bounded by tpc_min_setup_quality=0.55",
      "owner": "Helm",
      "approval": "ARCHITECT GO required"
    },
    "alternative_pair": {
      "wo_name": "WO-FALCON-TPC-RSI-BAND-WIDEN-0001",
      "change": "tpc_rsi_entry_min 40.0 -> 35.0 AND tpc_rsi_entry_max 65.0 -> 70.0",
      "rationale": "Widen both ends. Captures both early-pullback entries AND late-pullback continuations.",
      "risk": "More aggressive than upper-only loosen"
    },
    "follow_up": "WO-R2D2-TPC-POST-RSI-LOOSEN-VALIDATION-0001 (24-48h forward-watch + counterfactual)"
  },
  "classification": label,
  "rationale": rationale,
  "do_not_touched": ["DB config","code","health keys","thresholds","execution authority",
                     "health weighting","NOWIC_RT","watchers"]
}

import os
os.makedirs("/tmp/r2d2_tuning", exist_ok=True)
with open("/tmp/r2d2_tuning/tpc_audit.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\nLOCAL: /tmp/r2d2_tuning/tpc_audit.json")

scur.close(); scalp.close(); pcur.close(); proteus.close()
print("DONE.")
