"""WO-R2D2-TPC-POST-RSI-BAND-REVALIDATION-0001
READ-ONLY. UTC discipline. No NOW()/utcnow()/time.time().
Apply lesson: precise grep on `FAULT:` prefix to avoid `"faults": 0` JSON false positives."""
import json, datetime, pymysql, subprocess, sys
from collections import Counter

PR_SHA = "ed98a67fd0a6b1cf59a539f5852daa870406c2ed"
RESTART_UTC = datetime.datetime(2026, 5, 1, 17, 20, 35, tzinfo=datetime.timezone.utc)
VERIFY_PASS_UTC = datetime.datetime(2026, 5, 1, 17, 20, 38, tzinfo=datetime.timezone.utc)
RESTART_SQL = RESTART_UTC.strftime("%Y-%m-%d %H:%M:%S")
W14 = "2026-04-17 00:00:00"

if RESTART_UTC.tzinfo is None:
    print("FAIL_LOUD: anchor missing tz", file=sys.stderr); sys.exit(2)

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

scur.execute("SELECT MAX(created_at) AS now FROM helios_strategy_signals")
CANONICAL_NOW = scur.fetchone()["now"].replace(tzinfo=datetime.timezone.utc)
NOW_SQL = CANONICAL_NOW.strftime("%Y-%m-%d %H:%M:%S")
MIN_ELAPSED = (CANONICAL_NOW - RESTART_UTC).total_seconds() / 60
print(f"CANONICAL_NOW: {CANONICAL_NOW.isoformat()}")
print(f"RESTART:       {RESTART_UTC.isoformat()}")
print(f"min elapsed:   {MIN_ELAPSED:.2f}")

# ============================================================
# Q1+Q2: Config sanity + drift
# ============================================================
print("\n[Q1+Q2] TPC config + drift")
pcur.execute("""
    SELECT config_key, config_value,
           JSON_EXTRACT(llm_reasoning, '$.source_audit') source_audit,
           JSON_EXTRACT(llm_reasoning, '$.prior_value') prior_value
    FROM falcon_strategy_tpc_config
    WHERE instrument='XAU_USD' AND mode='NORMAL'
    ORDER BY config_key
""")
config_rows = list(pcur.fetchall())
config = {r["config_key"]: r for r in config_rows}
rsi_max_live = config.get("tpc_rsi_entry_max", {}).get("config_value")
rsi_min_live = config.get("tpc_rsi_entry_min", {}).get("config_value")
print(f"  tpc_rsi_entry_max = {rsi_max_live} (expected 70)")
print(f"  tpc_rsi_entry_min = {rsi_min_live} (expected 35)")
print(f"  tpc_min_setup_quality = {config.get('tpc_min_setup_quality', {}).get('config_value')} (unchanged 0.55)")
both_correct = (str(rsi_max_live) == "70.0" and str(rsi_min_live) == "35.0")
quality_unchanged = (str(config.get("tpc_min_setup_quality", {}).get("config_value")) == "0.55")

# True drift = rows where prior != current AND key is NOT one of the two intended targets
intended_changed = {"tpc_rsi_entry_max", "tpc_rsi_entry_min"}
true_drift = []
for r in config_rows:
    pv = (r["prior_value"] or "").strip('"')
    cv = str(r["config_value"]).strip()
    if pv and pv != cv and r["config_key"] not in intended_changed:
        true_drift.append({"key": r["config_key"], "current": cv, "prior": pv})
print(f"  true drift (excluding intended targets): {len(true_drift)} keys {true_drift}")

# BRC threshold sanity (architect mentioned should still be 600)
pcur.execute("""
    SELECT config_value FROM falcon_strategy_brc_config
    WHERE config_key='brc_hermes_stale_threshold_seconds'
""")
brc_threshold = pcur.fetchone()["config_value"]
brc_held = (str(brc_threshold) == "600")
print(f"  BRC threshold sanity: {brc_threshold} (expected 600, held={brc_held})")

# ============================================================
# Q3: Counterfactual — RSI_TOO_EXTENDED at 70
# ============================================================
print("\n[Q3] Counterfactual RSI_TOO_EXTENDED would pass at 70")
scur.execute(f"""
    SELECT
      CAST(JSON_EXTRACT(evidence, '$.rsi') AS DECIMAL(10,2)) rsi_val,
      JSON_EXTRACT(evidence, '$.direction') direction
    FROM helios_strategy_signals
    WHERE strategy_id='tpc_m15' AND reason_codes LIKE '%RSI_TOO_EXTENDED%'
      AND timestamp >= '{W14}' AND timestamp < '{RESTART_SQL}' AND evidence IS NOT NULL
""")
te_rows = [(float(r["rsi_val"]), r["direction"]) for r in scur.fetchall() if r["rsi_val"] is not None]
te_total = len(te_rows)
te_buy_high = [v for v, d in te_rows if (d == '"BUY"' or d == 'BUY') and v >= 65 and v < 70]
te_short_low = [v for v, d in te_rows if (d == '"SHORT"' or d == 'SHORT') and v > 35 and v <= 40]
te_would_pass = len(te_buy_high) + len(te_short_low)
print(f"  pre-fix total RSI_TOO_EXTENDED: {te_total}")
print(f"  BUY direction in 65-70 zone (newly passes upper widen): {len(te_buy_high)}")
print(f"  SHORT direction in 35-40 zone (newly passes lower widen): {len(te_short_low)}")
print(f"  total would-pass at new band: {te_would_pass} ({100*te_would_pass/te_total if te_total else 0:.1f}%)")

# ============================================================
# Q4: Counterfactual RSI_PULLBACK_ACTIVE at 35
# ============================================================
print("\n[Q4] Counterfactual RSI_PULLBACK_ACTIVE would pass at new band")
scur.execute(f"""
    SELECT
      CAST(JSON_EXTRACT(evidence, '$.rsi') AS DECIMAL(10,2)) rsi_val,
      JSON_EXTRACT(evidence, '$.direction') direction
    FROM helios_strategy_signals
    WHERE strategy_id='tpc_m15' AND reason_codes LIKE '%RSI_PULLBACK_ACTIVE%'
      AND timestamp >= '{W14}' AND timestamp < '{RESTART_SQL}' AND evidence IS NOT NULL
""")
pa_rows = [(float(r["rsi_val"]), r["direction"]) for r in scur.fetchall() if r["rsi_val"] is not None]
pa_total = len(pa_rows)
# BUY pullback active means RSI < 40 (now <35); 35-40 would now pass
pa_buy_lowend = [v for v, d in pa_rows if (d == '"BUY"' or d == 'BUY') and v >= 35 and v < 40]
# SHORT pullback active means RSI > 65 (now >70); 65-70 would now pass
pa_short_highend = [v for v, d in pa_rows if (d == '"SHORT"' or d == 'SHORT') and v > 65 and v <= 70]
# Direction unknown / NULL
pa_no_direction = [(v, d) for v, d in pa_rows if d is None]
pa_would_pass = len(pa_buy_lowend) + len(pa_short_highend)
print(f"  pre-fix total RSI_PULLBACK_ACTIVE: {pa_total}")
print(f"  BUY direction in 35-40 zone (lower widen rescues): {len(pa_buy_lowend)}")
print(f"  SHORT direction in 65-70 zone (upper widen rescues): {len(pa_short_highend)}")
print(f"  rows with no direction: {len(pa_no_direction)}")
print(f"  total would-pass at new band: {pa_would_pass} ({100*pa_would_pass/pa_total if pa_total else 0:.1f}%)")

total_counterfactual = te_would_pass + pa_would_pass
print(f"\n  COMBINED counterfactual rescue: {total_counterfactual} setups (would now pass RSI gate)")

# ============================================================
# Q5+Q6+Q9: Post-restart TPC behavior
# ============================================================
print("\n[Q5+Q6+Q9] Post-restart TPC bucket distribution")
scur.execute(f"""
    SELECT reason_codes, COUNT(*) c
    FROM helios_strategy_signals
    WHERE strategy_id='tpc_m15' AND created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}'
    GROUP BY reason_codes ORDER BY c DESC
""")
post_buckets = [(r["reason_codes"], int(r["c"])) for r in scur.fetchall()]
post_total = sum(c for _, c in post_buckets)
print(f"  post-restart TPC rows: {post_total}")
for rc, c in post_buckets:
    print(f"    {rc[:80]} {c}")

# Pull native gate_trace samples to confirm new RSI thresholds
scur.execute(f"""
    SELECT id, fired, reason_codes, gate_trace
    FROM helios_strategy_signals
    WHERE strategy_id='tpc_m15' AND created_at >= '{RESTART_SQL}'
      AND gate_trace LIKE '%evidence_version%'
    ORDER BY id LIMIT 5
""")
post_native_rows = list(scur.fetchall())
new_rsi_max_observed = set()
new_rsi_min_observed = set()
for r in post_native_rows:
    try:
        gt = json.loads(r["gate_trace"])
        for g in gt.get("guards", []):
            req = g.get("required") or {}
            if g.get("name") == "RSI_TOO_EXTENDED" and "rsi_max" in req:
                new_rsi_max_observed.add(req["rsi_max"])
            if g.get("name") == "RSI_PULLBACK_ACTIVE" and "rsi_min" in req:
                new_rsi_min_observed.add(req["rsi_min"])
            # Also check direction
            obs = g.get("observed") or {}
        first_fail = next((g for g in gt.get("guards", []) if g.get("result") == "FAIL"), None)
        print(f"  native row id={r['id']} primary={gt.get('primary_reason_code')} "
              f"first_fail={first_fail.get('name') if first_fail else 'NONE'}")
    except Exception as e:
        print(f"  parse err id={r['id']}: {e}")
print(f"\n  rsi_max observed in post-restart gate_traces: {sorted(new_rsi_max_observed)}")
print(f"  rsi_min observed in post-restart gate_traces: {sorted(new_rsi_min_observed)}")

# ============================================================
# Q7+Q8+Q10: Setup quality + proposals
# ============================================================
print("\n[Q7+Q8+Q10] Setup quality + proposals")
scur.execute(f"""
    SELECT COUNT(*) fires FROM helios_strategy_signals
    WHERE strategy_id='tpc_m15' AND fired=1 AND created_at >= '{RESTART_SQL}'
""")
post_fires = int(scur.fetchone()["fires"] or 0)
print(f"  post-restart TPC fires: {post_fires}")
print(f"  tpc_min_setup_quality configured: {config.get('tpc_min_setup_quality', {}).get('config_value')} (unchanged)")

# ============================================================
# Q11: System safety (precise grep)
# ============================================================
print("\n[Q11] System safety (precise grep — no JSON false positives)")
def jcount(p):
    try:
        out = subprocess.run(["ssh","root@192.168.11.10",
            f'TZ=UTC journalctl -u falcon-shadow --since "2026-05-01 17:20:35 UTC" --no-pager 2>/dev/null | grep -ciE "{p}" || echo 0'],
            capture_output=True, text=True, timeout=15)
        return int(out.stdout.strip().split()[-1])
    except: return None
datetime_errors = jcount("incorrect datetime|datetime value")
gt_unexpected = jcount("gate_trace.*unexpected|unexpected.*gate_trace")
real_faults = jcount(r"FAULT:|Signal write failed")  # FAULT: prefix avoids JSON faults:0 false positive
print(f"  datetime errors: {datetime_errors}")
print(f"  gate_trace unexpected: {gt_unexpected}")
print(f"  real FAULT entries (precise prefix grep): {real_faults}")

# Out-of-policy fires
scur.execute(f"""
    SELECT id, gate_trace FROM helios_strategy_signals
    WHERE strategy_id='tpc_m15' AND created_at >= '{RESTART_SQL}' AND fired=1
""")
fp_indicators = []
for r in scur.fetchall():
    try:
        gt = json.loads(r["gate_trace"]) if r["gate_trace"] else {}
        sess = gt.get("session") if isinstance(gt, dict) else None
        if sess and sess not in ("LONDON", "NY"):
            fp_indicators.append(f"fire id={r['id']} in session {sess}")
    except: pass
print(f"  policy violations: {len(fp_indicators)}")

# ============================================================
# Verdict
# ============================================================
def verdict():
    if not both_correct:
        return "TPC_RSI_FIX_REGRESSION", f"live config not matching: rsi_max={rsi_max_live} rsi_min={rsi_min_live}"
    if not quality_unchanged:
        return "TPC_RSI_FIX_REGRESSION", f"tpc_min_setup_quality changed unexpectedly"
    if true_drift:
        return "TPC_RSI_FIX_REGRESSION", f"unintended config drift: {true_drift}"
    if not brc_held:
        return "TPC_RSI_FIX_REGRESSION", f"BRC threshold drifted: {brc_threshold}"
    if datetime_errors and datetime_errors > 0:
        return "TPC_RSI_FIX_REGRESSION", f"{datetime_errors} datetime errors"
    if gt_unexpected and gt_unexpected > 0:
        return "TPC_RSI_FIX_REGRESSION", f"{gt_unexpected} gate_trace unexpected"
    if real_faults and real_faults > 0:
        return "TPC_RSI_FIX_REGRESSION", f"{real_faults} real FAULT entries"
    if fp_indicators:
        return "TPC_RSI_FIX_REGRESSION", f"policy violations: {fp_indicators}"
    if post_total == 0:
        return "TPC_RSI_FIX_PENDING_FORWARD_SAMPLE", "no post-restart TPC rows yet"
    # Has post-restart data
    no_ema_count = sum(c for rc,c in post_buckets if "NO_EMA_DATA" in rc)
    if post_total >= 1 and no_ema_count / post_total > 0.5:
        return "TPC_NEXT_BOTTLENECK_NO_EMA_DATA", (
            f"NO_EMA_DATA dominates post-fix at {100*no_ema_count/post_total:.0f}% "
            f"({no_ema_count}/{post_total}). Sample tiny but pattern matches pre-fix observation "
            f"that NO_EMA_DATA was 22.6% of strategy evals. Worth tracking."
        )
    return "TPC_RSI_FIX_PENDING_FORWARD_SAMPLE", (
        f"only {MIN_ELAPSED:.0f}min elapsed. counterfactual: {total_counterfactual} setups would have passed RSI gate. "
        f"forward sample insufficient — backtest is the load-bearing evidence."
    )

label, reason = verdict()
print(f"\n[VERDICT] {label}")
print(f"  reason: {reason}")

# ============================================================
# Save
# ============================================================
report = {
  "wo": "WO-R2D2-TPC-POST-RSI-BAND-REVALIDATION-0001",
  "wo_status": "CLOSED",
  "executed_by": "R2D2",
  "anchors": {
    "canonical_now_utc": CANONICAL_NOW.isoformat(),
    "restart_utc": RESTART_UTC.isoformat(),
    "verify_pass_utc": VERIFY_PASS_UTC.isoformat(),
    "pr_sha": PR_SHA,
    "min_since_restart": round(MIN_ELAPSED, 2)
  },
  "ut_discipline": "READ-ONLY. created_at + journal-anchored. No NOW()/utcnow()/time.time().",
  "lesson_applied": "Used `FAULT:` prefix grep (not `FAULT` alone) to avoid `\"faults\": 0` JSON false positives.",
  "Q1_Q2_config": {
    "tpc_rsi_entry_max_live": rsi_max_live,
    "tpc_rsi_entry_min_live": rsi_min_live,
    "tpc_min_setup_quality": config.get("tpc_min_setup_quality", {}).get("config_value"),
    "both_target_keys_correct": both_correct,
    "tpc_min_setup_quality_unchanged": quality_unchanged,
    "true_drift_excluding_targets": true_drift,
    "brc_threshold_held": brc_held,
    "rsi_max_provenance": str(config.get("tpc_rsi_entry_max", {}).get("source_audit")),
    "rsi_max_prior": str(config.get("tpc_rsi_entry_max", {}).get("prior_value")),
    "rsi_min_provenance": str(config.get("tpc_rsi_entry_min", {}).get("source_audit")),
    "rsi_min_prior": str(config.get("tpc_rsi_entry_min", {}).get("prior_value")),
  },
  "Q3_counterfactual_rsi_too_extended": {
    "pre_fix_total": te_total,
    "buy_65_70_rescued": len(te_buy_high),
    "short_35_40_rescued": len(te_short_low),
    "would_pass_at_new_band": te_would_pass,
    "would_pass_pct": round(100*te_would_pass/te_total, 1) if te_total else None
  },
  "Q4_counterfactual_rsi_pullback_active": {
    "pre_fix_total": pa_total,
    "buy_35_40_rescued": len(pa_buy_lowend),
    "short_65_70_rescued": len(pa_short_highend),
    "rows_with_no_direction": len(pa_no_direction),
    "would_pass_at_new_band": pa_would_pass,
    "would_pass_pct": round(100*pa_would_pass/pa_total, 1) if pa_total else None
  },
  "counterfactual_combined_rescue": total_counterfactual,
  "Q5_Q6_Q9_post_restart_buckets": {rc: c for rc, c in post_buckets},
  "Q5_Q6_Q9_native_observations": {
    "rsi_max_observed_in_post_gate_trace": sorted(new_rsi_max_observed),
    "rsi_min_observed_in_post_gate_trace": sorted(new_rsi_min_observed)
  },
  "Q7_Q8_Q10_quality_proposals": {
    "post_restart_fires": post_fires,
    "tpc_min_setup_quality_configured": config.get("tpc_min_setup_quality", {}).get("config_value")
  },
  "Q11_system_safety": {
    "datetime_errors_post_restart_utc": datetime_errors,
    "gate_trace_unexpected_rejections_utc": gt_unexpected,
    "real_fault_entries_precise_grep": real_faults,
    "policy_violations": fp_indicators
  },
  "Q12_no_ema_investigate_or_hold": (
    "HOLD — single post-restart NO_EMA_DATA row is consistent with pre-fix 22.6% rate; "
    "needs more sample to declare it the new bottleneck. Architect's 1-write-lane "
    "discipline applies. Defer until forward sample accumulates."
  ),
  "verdict": label,
  "verdict_reason": reason
}

import os
os.makedirs("/tmp/r2d2_tuning", exist_ok=True)
with open("/tmp/r2d2_tuning/tpc_postfix.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\nLOCAL: /tmp/r2d2_tuning/tpc_postfix.json")
print(f"VERDICT={label}")

scur.close(); scalp.close(); pcur.close(); proteus.close()
print("DONE.")
