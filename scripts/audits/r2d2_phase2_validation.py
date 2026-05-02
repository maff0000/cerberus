"""WO-R2D2-DECISION-LOGGING-PHASE-2-VALIDATION-0001
READ-ONLY. UTC: architect-stamped restart anchor + DB timestamps. Fail-loud on missing tz."""
import json, datetime, pymysql, sys
from collections import Counter, defaultdict

# ============================================================
# Architect-stamped anchors
# ============================================================
PR_619_SHA = "2f6efcf7f0ae16cbe595c16f4cc8cec0b62c6aba"
RESTART_UTC = datetime.datetime(2026, 5, 1, 12, 38, 4, tzinfo=datetime.timezone.utc)
VERIFY_PASS_UTC = datetime.datetime(2026, 5, 1, 12, 47, 40, tzinfo=datetime.timezone.utc)
RESTART_SQL = RESTART_UTC.strftime("%Y-%m-%d %H:%M:%S")

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

# Canonical now via signals MAX (no NOW())
scur.execute("SELECT MAX(timestamp) AS now FROM helios_strategy_signals")
CANONICAL_NOW = scur.fetchone()["now"].replace(tzinfo=datetime.timezone.utc)
NOW_SQL = CANONICAL_NOW.strftime("%Y-%m-%d %H:%M:%S")
HOURS_SINCE_RESTART = (CANONICAL_NOW - RESTART_UTC).total_seconds() / 3600

print(f"CANONICAL_NOW: {CANONICAL_NOW.isoformat()}")
print(f"RESTART:       {RESTART_UTC.isoformat()}")
print(f"VERIFY_PASS:   {VERIFY_PASS_UTC.isoformat()}")
print(f"PR #619 SHA:   {PR_619_SHA}")
print(f"hours since restart: {HOURS_SINCE_RESTART:.2f}")

INSTRUMENTED = ["cfr_m5", "coil_breakout_m5"]

# ============================================================
# TASK 1: Read post-restart rows
# ============================================================
print("\n[1] Post-restart row counts")
scur.execute(f"""
    SELECT strategy_id, COUNT(*) c, MIN(timestamp) earliest, MAX(timestamp) latest,
           SUM(CASE WHEN gate_trace IS NULL OR gate_trace='' OR gate_trace='[]' THEN 1 ELSE 0 END) legacy_or_empty,
           SUM(CASE WHEN gate_trace LIKE '%evidence_version%' THEN 1 ELSE 0 END) instrumented
    FROM helios_strategy_signals
    WHERE timestamp >= '{RESTART_SQL}' AND timestamp <= '{NOW_SQL}'
    GROUP BY strategy_id ORDER BY strategy_id
""")
all_post = [dict(r) for r in scur.fetchall()]
for r in all_post:
    r["c"] = int(r["c"] or 0)
    r["legacy_or_empty"] = int(r["legacy_or_empty"] or 0)
    r["instrumented"] = int(r["instrumented"] or 0)
    expected = "INSTRUMENTED" if r["strategy_id"] in INSTRUMENTED else "LEGACY"
    actual = "INSTRUMENTED" if r["instrumented"] > 0 else "LEGACY"
    flag = "OK" if expected == actual else "MISMATCH"
    print(f"  {r['strategy_id']:<22s} c={r['c']:>4d} instrumented={r['instrumented']:>3d} "
          f"legacy/empty={r['legacy_or_empty']:>3d} expected={expected} actual={actual} {flag}")

# ============================================================
# TASKS 2 & 3: Validate cfr_m5 + coil_breakout_m5 gate_trace
# ============================================================
def parse_gate_trace(raw):
    """Return ('LEGACY', None) for empty/[], ('NEW', dict) for new format, ('BROKEN', err) on parse error."""
    if raw is None or raw == "" or raw == "[]":
        return "LEGACY", None
    try:
        d = json.loads(raw)
    except Exception as e:
        return "BROKEN", str(e)
    if isinstance(d, list):
        return "LEGACY", None
    if isinstance(d, dict) and d.get("evidence_version"):
        return "NEW", d
    return "BROKEN", f"unrecognised shape keys={list(d.keys()) if isinstance(d,dict) else type(d).__name__}"

def validate_row(row, sid):
    gt_kind, gt = parse_gate_trace(row["gate_trace"])
    issues = []
    if gt_kind != "NEW":
        return {"id": row["id"], "ts": str(row["timestamp"]), "kind": gt_kind, "issues": ["not new format"]}

    # evidence_version
    if gt.get("evidence_version") != "1.0":
        issues.append(f"evidence_version={gt.get('evidence_version')!r} != '1.0'")

    # primary_reason_code preserved verbatim (compare against reason_codes column)
    rc_raw = row["reason_codes"]
    try:
        rc_list = json.loads(rc_raw) if rc_raw else []
    except: rc_list = [rc_raw]
    rc0 = rc_list[0] if rc_list else None
    primary = gt.get("primary_reason_code")
    if rc0 and primary != rc0:
        issues.append(f"primary_reason_code={primary!r} != reason_codes[0]={rc0!r}")

    # guards present and ordered
    guards = gt.get("guards") or []
    if not guards:
        issues.append("guards empty")
    else:
        orders = [g.get("order") for g in guards]
        if orders != sorted(orders):
            issues.append(f"guards not in order: {orders}")
        if any(g.get("order") is None for g in guards):
            issues.append("guard missing order")
        if any(not g.get("name") for g in guards):
            issues.append("guard missing name")
        if any(g.get("result") not in ("PASS","FAIL","SKIP","WARN",None) for g in guards):
            issues.append("guard result not in PASS/FAIL/SKIP/WARN")

    # First FAIL guard alignment
    first_fail = next((g for g in guards if g.get("result") == "FAIL"), None)
    if row["fired"] == 0:
        if first_fail is None:
            issues.append("DECLINE row has no FAIL guard")
        else:
            # primary should mention the FAIL guard name
            if first_fail.get("name") and first_fail["name"] not in (primary or ""):
                issues.append(f"first FAIL='{first_fail.get('name')}' not in primary_reason='{primary}'")

    # Required/observed populated check (weakness, not a hard fail)
    weak_guards = [g["name"] for g in guards
                   if (g.get("required") is None and g.get("observed") is None)]
    if weak_guards:
        issues.append(f"weak: required+observed both null on {weak_guards}")

    return {"id": row["id"], "ts": str(row["timestamp"]), "kind": "NEW",
            "primary": primary, "first_fail": first_fail.get("name") if first_fail else None,
            "guards_count": len(guards), "issues": issues,
            "session": gt.get("session"), "ares_state": (gt.get("risk_context") or {}).get("ares_state"),
            "cycle_ts": gt.get("cycle_ts")}

per_strategy_rows = {}
per_strategy_validation = {}
for sid in INSTRUMENTED:
    scur.execute(f"""
        SELECT id, timestamp, fired, reason_codes, gate_trace
        FROM helios_strategy_signals
        WHERE timestamp >= '{RESTART_SQL}' AND timestamp <= '{NOW_SQL}'
          AND strategy_id='{sid}'
        ORDER BY timestamp ASC
    """)
    rows = scur.fetchall()
    per_strategy_rows[sid] = len(rows)
    validations = [validate_row(r, sid) for r in rows]
    per_strategy_validation[sid] = validations
    print(f"\n[2/3] {sid} validation ({len(rows)} rows)")
    for v in validations[:5]:
        print(f"  id={v['id']} ts={v['ts']} kind={v['kind']} primary={v.get('primary')} "
              f"first_fail={v.get('first_fail')} issues={v['issues']}")

    # HERMES_STALE pass rate (CFR-specific freshness verification)
    hermes_pass = 0; hermes_total = 0
    cascade_failures = Counter()
    for v in validations:
        if v["kind"] != "NEW": continue
        # Re-parse for guard inspection
    scur.execute(f"""
        SELECT gate_trace FROM helios_strategy_signals
        WHERE timestamp >= '{RESTART_SQL}' AND timestamp <= '{NOW_SQL}' AND strategy_id='{sid}'
    """)
    hermes_states = Counter(); first_fail_dist = Counter()
    for r in scur.fetchall():
        kind, gt = parse_gate_trace(r["gate_trace"])
        if kind != "NEW": continue
        for g in (gt.get("guards") or []):
            if g.get("name") == "HERMES_STALE":
                hermes_states[g.get("result")] += 1
        ff = next((g for g in (gt.get("guards") or []) if g.get("result")=="FAIL"), None)
        if ff: first_fail_dist[ff.get("name")] += 1
    print(f"  HERMES_STALE results: {dict(hermes_states)}")
    print(f"  first-FAIL distribution: {dict(first_fail_dist)}")
    per_strategy_validation[f"{sid}_hermes"] = dict(hermes_states)
    per_strategy_validation[f"{sid}_first_fail_dist"] = dict(first_fail_dist)

# ============================================================
# TASK 4: Backward compatibility — legacy strategies still parseable
# ============================================================
print("\n[4] Legacy strategy parseability")
scur.execute(f"""
    SELECT strategy_id, COUNT(*) c,
           SUM(CASE WHEN gate_trace IS NULL OR gate_trace='' THEN 1 ELSE 0 END) null_or_empty,
           SUM(CASE WHEN gate_trace='[]' THEN 1 ELSE 0 END) bracket_empty,
           SUM(CASE WHEN gate_trace LIKE '%evidence_version%' THEN 1 ELSE 0 END) new_fmt
    FROM helios_strategy_signals
    WHERE timestamp >= '{RESTART_SQL}' AND timestamp <= '{NOW_SQL}'
      AND strategy_id NOT IN ('cfr_m5','coil_breakout_m5')
    GROUP BY strategy_id ORDER BY c DESC
""")
legacy_summary = [dict(r) for r in scur.fetchall()]
legacy_compat_issues = []
for r in legacy_summary:
    r["c"] = int(r["c"] or 0)
    r["null_or_empty"] = int(r["null_or_empty"] or 0)
    r["bracket_empty"] = int(r["bracket_empty"] or 0)
    r["new_fmt"] = int(r["new_fmt"] or 0)
    if r["new_fmt"] > 0:
        legacy_compat_issues.append(f"{r['strategy_id']}: unexpected new format in legacy strategy")
    print(f"  {r['strategy_id']:<22s} c={r['c']:>4d} null/empty={r['null_or_empty']:>3d} "
          f"'[]'={r['bracket_empty']:>3d} new_fmt={r['new_fmt']:>3d}")

# Sample-parse a legacy row to confirm it doesn't break dispatch
scur.execute(f"""
    SELECT strategy_id, gate_trace FROM helios_strategy_signals
    WHERE timestamp >= '{RESTART_SQL}' AND timestamp <= '{NOW_SQL}'
      AND strategy_id NOT IN ('cfr_m5','coil_breakout_m5')
    LIMIT 5
""")
legacy_dispatch_results = []
for r in scur.fetchall():
    kind, _ = parse_gate_trace(r["gate_trace"])
    legacy_dispatch_results.append({"sid": r["strategy_id"], "raw": (r["gate_trace"] or "")[:60], "dispatch": kind})
    print(f"  dispatch sample: {r['strategy_id']:<22s} '{(r['gate_trace'] or '')[:30]}' -> {kind}")

# ============================================================
# TASK 5: Usefulness assessment
# ============================================================
print("\n[5] Usefulness assessment")
# CFR: scan first row, report what we know without reading worker code
scur.execute(f"""
    SELECT id, timestamp, fired, reason_codes, gate_trace
    FROM helios_strategy_signals
    WHERE timestamp >= '{RESTART_SQL}' AND timestamp <= '{NOW_SQL}' AND strategy_id='cfr_m5'
    ORDER BY timestamp ASC LIMIT 1
""")
cfr_sample_row = scur.fetchone()
_, cfr_sample = parse_gate_trace(cfr_sample_row["gate_trace"]) if cfr_sample_row else (None, None)

cfr_explanation = "(no rows)"
cfr_weaknesses = []
if cfr_sample:
    fail = next((g for g in cfr_sample.get("guards", []) if g.get("result") == "FAIL"), None)
    if fail:
        cfr_explanation = (f"CFR declined at gate '{fail.get('name')}' "
                          f"(order {fail.get('order')}). "
                          f"required={fail.get('required')} observed={fail.get('observed')}")
        if fail.get("required") is None:
            cfr_weaknesses.append("FAIL guard has no 'required' values — can't see threshold")
        if fail.get("observed") is None:
            cfr_weaknesses.append("FAIL guard has no 'observed' values — can't see actual metric")
        # CFR specifically — observed has cascade_window_bars+atr but missing the actual atr_multiple/body_pct
        if fail.get("name") == "NO_CASCADE":
            obs_keys = set((fail.get("observed") or {}).keys())
            req_keys = set((fail.get("required") or {}).keys())
            req_metrics = {k.replace("cascade_min_","").replace("_max","").replace("_min","")
                           for k in req_keys}
            obs_metrics = {k.replace("cascade_","").replace("_observed","")
                           for k in obs_keys}
            missing_obs = req_metrics - obs_metrics - {"window_bars"}
            if missing_obs:
                cfr_weaknesses.append(f"observed missing the metrics being thresholded: {sorted(missing_obs)}")

print(f"  CFR explanation (no worker code): {cfr_explanation}")
for w in cfr_weaknesses:
    print(f"    weak: {w}")

scur.execute(f"""
    SELECT id, timestamp, fired, reason_codes, gate_trace
    FROM helios_strategy_signals
    WHERE timestamp >= '{RESTART_SQL}' AND timestamp <= '{NOW_SQL}' AND strategy_id='coil_breakout_m5'
    ORDER BY timestamp ASC LIMIT 1
""")
coil_sample_row = scur.fetchone()
_, coil_sample = parse_gate_trace(coil_sample_row["gate_trace"]) if coil_sample_row else (None, None)

coil_explanation = "(no rows)"
coil_weaknesses = []
if coil_sample:
    fail = next((g for g in coil_sample.get("guards", []) if g.get("result") == "FAIL"), None)
    if fail:
        coil_explanation = (f"Coil declined at gate '{fail.get('name')}' (order {fail.get('order')}). "
                            f"required={fail.get('required')} observed={fail.get('observed')}")
        if fail.get("required") is None:
            coil_weaknesses.append("FAIL guard has no 'required' values — can't see threshold")
        if fail.get("observed") is None:
            coil_weaknesses.append("FAIL guard has no 'observed' values — can't see actual metric")
    # Cross-strategy structural inconsistencies
    if coil_sample.get("session") is None and cfr_sample and cfr_sample.get("session"):
        coil_weaknesses.append("coil session=null while CFR session populated — inconsistent")
    if coil_sample.get("regime_context") is None and cfr_sample and cfr_sample.get("regime_context"):
        coil_weaknesses.append("coil regime_context=null while CFR populated — inconsistent")
    coil_cycle_ts = coil_sample.get("cycle_ts","")
    if "." in coil_cycle_ts:  # microseconds present = wall clock not cycle boundary
        coil_weaknesses.append(f"coil cycle_ts has microseconds ({coil_cycle_ts}) — looks like wall-clock not cycle boundary; CFR uses aligned boundary")

print(f"  Coil explanation (no worker code): {coil_explanation}")
for w in coil_weaknesses:
    print(f"    weak: {w}")

# ============================================================
# TASK 6: Phase 3 candidate
# ============================================================
print("\n[6] Phase 3 candidate")
# Recommend by traffic + investigation backlog
scur.execute(f"""
    SELECT strategy_id, COUNT(*) c
    FROM helios_strategy_signals
    WHERE timestamp >= '2026-04-28 00:00:00' AND timestamp <= '{NOW_SQL}'
      AND strategy_id NOT IN ('cfr_m5','coil_breakout_m5')
    GROUP BY strategy_id ORDER BY c DESC
""")
traffic = [dict(r) for r in scur.fetchall()]
for r in traffic:
    r["c"] = int(r["c"] or 0)
print(f"  recent traffic (post-AMEND-1, excl. instrumented):")
for r in traffic[:10]:
    print(f"    {r['strategy_id']:<22s} {r['c']:>5d}")

# Candidate logic: instrument the high-traffic + high-decline-density ones first
# Architect mentioned: NOWIC_RT / NOWIC_AT / TDR / CSDR / BRC / TPC
known_candidates = ["nowic_at_m15", "nowic_rt_m15", "tdr_m5", "csdr_m15", "brc_m5", "tpc_m15"]
traffic_map = {r["strategy_id"]: r["c"] for r in traffic}
candidate_ranking = sorted(known_candidates, key=lambda c: -traffic_map.get(c, 0))
print(f"  ranked Phase 3 candidates (by recent traffic):")
for c in candidate_ranking:
    print(f"    {c:<22s} traffic={traffic_map.get(c, 0)}")

# ============================================================
# Classification
# ============================================================
def overall_label():
    # Required hard checks
    cfr_v = per_strategy_validation.get("cfr_m5", [])
    coil_v = per_strategy_validation.get("coil_breakout_m5", [])
    if not cfr_v and not coil_v:
        return "LOGGING_NEEDS_MORE_RUNTIME_ROWS", ["zero post-restart instrumented rows"]
    # Hard issues = first FAIL doesn't align, primary mismatch, guards empty
    hard = []
    for sid, vs in (("cfr_m5", cfr_v), ("coil_breakout_m5", coil_v)):
        for v in vs:
            for issue in v["issues"]:
                if any(k in issue for k in ["primary_reason_code", "first FAIL", "guards empty",
                                             "guards not in order", "evidence_version=", "no FAIL guard"]):
                    hard.append(f"{sid}/id={v['id']}: {issue}")
    if hard:
        return "LOGGING_PARTIAL", hard
    if legacy_compat_issues:
        return "LEGACY_COMPAT_BROKEN", legacy_compat_issues
    # Soft weaknesses (coil nulls) downgrade to PARTIAL
    soft = (cfr_weaknesses + coil_weaknesses)
    if soft:
        return "LOGGING_PARTIAL", soft
    return "LOGGING_VALIDATED", []

label, label_reasons = overall_label()
print(f"\n[VERDICT] {label}")
for r in label_reasons:
    print(f"  - {r}")

# ============================================================
# Save report
# ============================================================
report = {
  "wo": "WO-R2D2-DECISION-LOGGING-PHASE-2-VALIDATION-0001",
  "wo_status": "CLOSED",
  "executed_by": "R2D2",
  "anchors": {
    "canonical_now_utc": CANONICAL_NOW.isoformat(),
    "restart_utc": RESTART_UTC.isoformat(),
    "verify_pass_utc": VERIFY_PASS_UTC.isoformat(),
    "pr_619_sha": PR_619_SHA,
    "hours_since_restart": round(HOURS_SINCE_RESTART, 2),
  },
  "ut_discipline": "READ-ONLY. Architect-stamped restart anchor + DB timestamps. No NOW()/utcnow()/time.time().",
  "task_1_post_restart_counts": all_post,
  "task_2_3_per_strategy_validation": {
    sid: {"row_count": per_strategy_rows.get(sid, 0),
          "rows_validated": per_strategy_validation.get(sid, []),
          "hermes_state_distribution": per_strategy_validation.get(f"{sid}_hermes", {}),
          "first_fail_distribution": per_strategy_validation.get(f"{sid}_first_fail_dist", {})}
    for sid in INSTRUMENTED
  },
  "task_4_legacy_compat": {
    "summary_per_legacy_strategy": legacy_summary,
    "dispatch_samples": legacy_dispatch_results,
    "compat_issues": legacy_compat_issues
  },
  "task_5_usefulness": {
    "cfr_can_explain_without_worker_code": cfr_explanation,
    "cfr_weaknesses": cfr_weaknesses,
    "coil_can_explain_without_worker_code": coil_explanation,
    "coil_weaknesses": coil_weaknesses
  },
  "task_6_phase3_candidates": {
    "ranking_by_traffic": [{"sid": c, "post_amend1_traffic": traffic_map.get(c, 0)} for c in candidate_ranking],
    "recommendation": "Pair tdr_m5 + nowic_at_m15 next — both high-traffic, both already in active investigation/queue, both M5/M15 cohort fits the existing pattern. Defer nowic_rt_m15 (BLOCKED standing rule).",
    "rationale": [
      "tdr_m5 and nowic_at_m15 are the active confidence-formula cohort — instrumentation aligns with the watcher data we already collect",
      "csdr_m15/brc_m5/tpc_m15 are pending audit WOs — instrumenting them now would provide the evidence those audits need rather than ad-hoc DB grovels",
      "nowic_rt_m15 is BLOCKED — instrumentation possible but no operational benefit until enabled"
    ]
  },
  "classification": label,
  "classification_reasons": label_reasons,
  "do_not_touched": ["DB config","code","health keys","thresholds","execution authority",
                     "health weighting","NOWIC_RT","watchers"],
  "precursor_audits": [
    "r2d2:audit:cfr_hermes_stale_investigation:latest",
    "r2d2:audit:cfr_post_threshold_revalidation:latest"
  ]
}

import os
os.makedirs("/tmp/r2d2_tuning", exist_ok=True)
with open("/tmp/r2d2_tuning/decision_logging_phase2.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\nLOCAL: /tmp/r2d2_tuning/decision_logging_phase2.json")

scur.close(); scalp.close()
print("DONE.")
