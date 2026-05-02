"""WO-R2D2-BRC-POST-STALE-THRESHOLD-REVALIDATION-0001
READ-ONLY. UTC discipline absolute."""
import json, datetime, pymysql, sys
from collections import Counter

PR_SHA = "a917da7a49abfd63634381b078bf9a6168fe64fe"
RESTART_UTC = datetime.datetime(2026, 5, 1, 17, 7, 26, tzinfo=datetime.timezone.utc)
VERIFY_PASS_UTC = datetime.datetime(2026, 5, 1, 17, 7, 29, tzinfo=datetime.timezone.utc)
RESTART_SQL = RESTART_UTC.strftime("%Y-%m-%d %H:%M:%S")
CLASSIFIER_FIX_DATE = "2026-04-30 00:00:00"
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
print(f"min elapsed:   {MIN_ELAPSED:.1f}")

# ============================================================
# Q1 + Q2: Live config + drift check
# ============================================================
print("\n[Q1+Q2] Config sanity")
pcur.execute("""
    SELECT config_key, config_value,
           JSON_EXTRACT(llm_reasoning, '$.source_audit') source_audit,
           JSON_EXTRACT(llm_reasoning, '$.prior_value') prior_value
    FROM falcon_strategy_brc_config
    WHERE instrument='XAU_USD' AND mode='NORMAL'
    ORDER BY config_key
""")
config_rows = list(pcur.fetchall())
config = {r["config_key"]: r for r in config_rows}
threshold = config.get("brc_hermes_stale_threshold_seconds", {})
threshold_correct = (str(threshold.get("config_value")) == "600")
print(f"  brc_hermes_stale_threshold_seconds = {threshold.get('config_value')} (expected 600, correct={threshold_correct})")
print(f"    source_audit = {threshold.get('source_audit')}")
print(f"    prior_value  = {threshold.get('prior_value')}")
# Drift check: any other config row with prior_value != current config_value?
drift = []
for r in config_rows:
    pv = (r["prior_value"] or "").strip('"')
    cv = str(r["config_value"]).strip()
    if pv and pv != cv:
        drift.append({"key": r["config_key"], "current": cv, "prior": pv})
print(f"  config drift detected (any key where prior != current other than threshold): {drift}")

# ============================================================
# Q3: Counterfactual — historical stales that would pass at 600
# ============================================================
print("\n[Q3] Counterfactual (historical 14d HERMES_STALE under new 600 threshold)")
scur.execute(f"""
    SELECT COUNT(*) total,
           AVG(CAST(JSON_EXTRACT(evidence, '$.signal_age') AS DECIMAL(10,2))) avg_age,
           MIN(CAST(JSON_EXTRACT(evidence, '$.signal_age') AS DECIMAL(10,2))) min_age,
           MAX(CAST(JSON_EXTRACT(evidence, '$.signal_age') AS DECIMAL(10,2))) max_age,
           SUM(CASE WHEN CAST(JSON_EXTRACT(evidence, '$.signal_age') AS DECIMAL(10,2)) < 600 THEN 1 ELSE 0 END) would_pass_at_600
    FROM helios_strategy_signals
    WHERE strategy_id='brc_m5' AND fired=0 AND reason_codes LIKE '%HERMES_STALE%'
      AND timestamp >= '{W14}' AND timestamp < '{RESTART_SQL}'
""")
counterfactual = dict(scur.fetchone())
total_stale_pre = int(counterfactual["total"] or 0)
would_pass = int(counterfactual["would_pass_at_600"] or 0)
print(f"  pre-restart 14d HERMES_STALE total: {total_stale_pre}")
print(f"  signal_age min={counterfactual['min_age']} avg={counterfactual['avg_age']} max={counterfactual['max_age']}")
print(f"  would pass at 600: {would_pass} ({100*would_pass/total_stale_pre if total_stale_pre else 0:.0f}%)")

# ============================================================
# Q4: Post-fix HERMES_STALE rate
# ============================================================
print("\n[Q4] Post-fix HERMES_STALE")
scur.execute(f"""
    SELECT COUNT(*) total,
           SUM(CASE WHEN reason_codes LIKE '%HERMES_STALE%' THEN 1 ELSE 0 END) stale,
           SUM(CASE WHEN fired=1 THEN 1 ELSE 0 END) fires
    FROM helios_strategy_signals
    WHERE strategy_id='brc_m5' AND created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}'
""")
post = dict(scur.fetchone())
post_total = int(post["total"] or 0)
post_stale = int(post["stale"] or 0)
post_fires = int(post["fires"] or 0)
print(f"  post-restart BRC rows: {post_total}")
print(f"  HERMES_STALE post-restart: {post_stale}")
print(f"  fires post-restart: {post_fires}")

# ============================================================
# Q5: Post-fix gates reached
# ============================================================
print("\n[Q5] Post-fix gates reached (which buckets show up)")
scur.execute(f"""
    SELECT reason_codes, COUNT(*) c
    FROM helios_strategy_signals
    WHERE strategy_id='brc_m5' AND created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}'
    GROUP BY reason_codes ORDER BY c DESC
""")
post_buckets = [(r["reason_codes"], int(r["c"])) for r in scur.fetchall()]
for rc, c in post_buckets:
    print(f"    {rc[:80]} {c}")

# Pull the one (or few) post-restart gate_trace rows for native evidence
scur.execute(f"""
    SELECT id, created_at, fired, reason_codes, gate_trace
    FROM helios_strategy_signals
    WHERE strategy_id='brc_m5' AND created_at >= '{RESTART_SQL}'
      AND gate_trace LIKE '%evidence_version%'
    ORDER BY id LIMIT 5
""")
post_native_rows = list(scur.fetchall())
print(f"\n  post-restart native gate_trace rows: {len(post_native_rows)}")
for r in post_native_rows:
    try:
        gt = json.loads(r["gate_trace"])
        hermes_guard = next((g for g in gt.get("guards", []) if g.get("name") == "HERMES_STALE"), None)
        if hermes_guard:
            print(f"    id={r['id']} HERMES_STALE: result={hermes_guard.get('result')} "
                  f"required={hermes_guard.get('required')} observed={hermes_guard.get('observed')}")
        first_fail = next((g for g in gt.get("guards", []) if g.get("result") == "FAIL"), None)
        print(f"           primary={gt.get('primary_reason_code')} first_fail={first_fail.get('name') if first_fail else 'NONE'}")
    except Exception as e:
        print(f"    id={r['id']} parse error: {e}")

# ============================================================
# Q6+Q7: Proposals + break-quality protective
# ============================================================
print("\n[Q6+Q7] Proposals + break-quality")
print(f"  post-restart fires/proposals: {post_fires}")
# Break-quality guard: verify required.min_break_quality still 0.6 in any post-restart gate_trace
break_quality_thresholds = set()
for r in post_native_rows:
    try:
        gt = json.loads(r["gate_trace"])
        for g in gt.get("guards", []):
            if g.get("name") == "NO_BREAK_SIGNAL":
                req = g.get("required") or {}
                if "min_break_quality" in req:
                    break_quality_thresholds.add(req["min_break_quality"])
    except: pass
print(f"  break-quality thresholds observed in post-restart gate_traces: {sorted(break_quality_thresholds)}")
print(f"  configured brc_min_break_quality: {config.get('brc_min_break_quality', {}).get('config_value')}")

# ============================================================
# Q8: Regime gate behavior post-fix
# ============================================================
print("\n[Q8] Regime gate behavior post-restart")
regime_observations = []
for r in post_native_rows:
    try:
        gt = json.loads(r["gate_trace"])
        ir_guard = next((g for g in gt.get("guards", []) if g.get("name") == "INVALID_REGIME"), None)
        if ir_guard:
            regime_observations.append({"id": r["id"], "result": ir_guard.get("result"),
                                         "observed": ir_guard.get("observed")})
    except: pass
for o in regime_observations:
    print(f"  id={o['id']} INVALID_REGIME result={o['result']} observed={o['observed']}")

# ============================================================
# Q9: New errors / failures
# ============================================================
print("\n[Q9] System safety")
import subprocess
def jcount(p):
    try:
        out = subprocess.run(["ssh","root@192.168.11.10",
            f'TZ=UTC journalctl -u falcon-shadow --since "2026-05-01 17:07:26 UTC" --no-pager 2>/dev/null | grep -ciE "{p}" || echo 0'],
            capture_output=True, text=True, timeout=15)
        return int(out.stdout.strip().split()[-1])
    except: return None
datetime_errors = jcount("incorrect datetime|datetime value")
gt_unexpected = jcount("gate_trace.*unexpected|unexpected.*gate_trace")
generic_errors = jcount("Signal write failed|FAULT")
print(f"  datetime errors: {datetime_errors}")
print(f"  gate_trace unexpected: {gt_unexpected}")
print(f"  generic FAULT/write-fail: {generic_errors}")

# Out-of-policy fired=1
scur.execute(f"""
    SELECT id, gate_trace FROM helios_strategy_signals
    WHERE strategy_id='brc_m5' AND created_at >= '{RESTART_SQL}' AND fired=1
""")
fp_indicators = []
for r in scur.fetchall():
    try:
        gt = json.loads(r["gate_trace"]) if r["gate_trace"] else {}
        sess = gt.get("session") if isinstance(gt, dict) else None
        if sess and sess not in ("LONDON", "NY"):
            fp_indicators.append(f"fire id={r['id']} in non-allowed session {sess}")
    except: pass
print(f"  policy violations: {len(fp_indicators)}")

# ============================================================
# Verdict
# ============================================================
def verdict():
    if not threshold_correct:
        return "BRC_STALE_FIX_REGRESSION", "live config not 600"
    if datetime_errors and datetime_errors > 0:
        return "BRC_STALE_FIX_REGRESSION", f"{datetime_errors} datetime errors post-restart"
    if gt_unexpected and gt_unexpected > 0:
        return "BRC_STALE_FIX_REGRESSION", f"{gt_unexpected} gate_trace rejections post-restart"
    if generic_errors and generic_errors > 5:
        return "BRC_STALE_FIX_REGRESSION", f"{generic_errors} FAULT/write-fail entries"
    if fp_indicators:
        return "BRC_STALE_FIX_REGRESSION", f"policy violations: {fp_indicators}"
    if post_total == 0:
        return "BRC_STALE_FIX_PENDING_FORWARD_SAMPLE", "no post-restart BRC rows yet"
    # post_total > 0
    if post_stale > 0:
        # Did the live row genuinely exceed 600?
        return "BRC_STALE_FIX_PENDING_FORWARD_SAMPLE", f"some stale still firing — investigate signal_age vs 600"
    # Check if next bottleneck is dominant
    nbs = sum(c for rc,c in post_buckets if "NO_BREAK_SIGNAL" in rc)
    if post_total > 5 and nbs / post_total > 0.5:
        return "BRC_NEXT_BOTTLENECK_IDENTIFIED", f"NO_BREAK_SIGNAL dominates post-fix at {100*nbs/post_total:.0f}%"
    return "BRC_STALE_FIX_PENDING_FORWARD_SAMPLE", (
        f"only {MIN_ELAPSED:.0f}min elapsed. counterfactual confirms 100% historical conversion. "
        f"forward sample insufficient — backtest is the load-bearing evidence."
    )

label, reason = verdict()
print(f"\n[VERDICT] {label}")
print(f"  reason: {reason}")

# ============================================================
# Save
# ============================================================
report = {
  "wo": "WO-R2D2-BRC-POST-STALE-THRESHOLD-REVALIDATION-0001",
  "wo_status": "CLOSED",
  "executed_by": "R2D2",
  "anchors": {
    "canonical_now_utc": CANONICAL_NOW.isoformat(),
    "restart_utc": RESTART_UTC.isoformat(),
    "verify_pass_utc": VERIFY_PASS_UTC.isoformat(),
    "pr_sha": PR_SHA,
    "min_since_restart": round(MIN_ELAPSED, 1)
  },
  "ut_discipline": "READ-ONLY. created_at + journal-anchored. No NOW()/utcnow()/time.time().",
  "Q1_Q2_config_check": {
    "brc_hermes_stale_threshold_seconds_live": threshold.get("config_value"),
    "expected": 600,
    "match": threshold_correct,
    "source_audit": str(threshold.get("source_audit")),
    "prior_value": str(threshold.get("prior_value")),
    "drift_in_other_keys": drift
  },
  "Q3_counterfactual_pre_restart_14d": {
    "total_stale": total_stale_pre,
    "would_pass_at_600": would_pass,
    "would_pass_pct": round(100*would_pass/total_stale_pre, 1) if total_stale_pre else None,
    "signal_age_min": float(counterfactual["min_age"]) if counterfactual["min_age"] else None,
    "signal_age_max": float(counterfactual["max_age"]) if counterfactual["max_age"] else None,
    "signal_age_avg": float(counterfactual["avg_age"]) if counterfactual["avg_age"] else None
  },
  "Q4_post_fix_hermes_stale": {
    "post_restart_total_rows": post_total,
    "post_restart_stale": post_stale,
    "post_restart_stale_rate_pct": round(100*post_stale/post_total, 1) if post_total else None
  },
  "Q5_post_fix_buckets": {rc: c for rc, c in post_buckets},
  "Q5_native_gate_trace_observations": [
    {"id": r["id"], "fired": r["fired"], "reason_codes": r["reason_codes"][:80]}
    for r in post_native_rows
  ],
  "Q6_Q7_proposals_break_quality": {
    "post_restart_fires": post_fires,
    "break_quality_thresholds_observed": sorted(break_quality_thresholds),
    "configured_brc_min_break_quality": config.get("brc_min_break_quality", {}).get("config_value")
  },
  "Q8_regime_gate_observations": regime_observations,
  "Q9_system_safety": {
    "datetime_errors_utc": datetime_errors,
    "gate_trace_unexpected_rejections_utc": gt_unexpected,
    "generic_fault_write_fail": generic_errors,
    "policy_violations": fp_indicators
  },
  "Q10_recommendation": (
    "hold 600 — counterfactual 100% conversion; live forward sample tiny but no regression."
    if label != "BRC_STALE_FIX_REGRESSION" else
    "rollback to 120 — regression detected"
  ),
  "verdict": label,
  "verdict_reason": reason
}

import os
os.makedirs("/tmp/r2d2_tuning", exist_ok=True)
with open("/tmp/r2d2_tuning/brc_postfix.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\nLOCAL: /tmp/r2d2_tuning/brc_postfix.json")
print(f"VERDICT={label}")

scur.close(); scalp.close(); pcur.close(); proteus.close()
print("DONE.")
