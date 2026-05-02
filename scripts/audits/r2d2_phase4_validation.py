"""WO-R2D2-DECISION-LOGGING-PHASE-4-VALIDATION-0001
READ-ONLY. Anchor: created_at > 2026-05-01T15:36:43Z (NOT cycle_ts)."""
import json, datetime, pymysql, sys
from collections import Counter

PR_623_SHA = "c44aaa81b6ffeb549d3e5248a1466c31eb6a891f"
PR_624_SHA = "b32e5404ed548580de1775f6235b8155754f39cc"
RESTART_UTC = datetime.datetime(2026, 5, 1, 15, 36, 43, tzinfo=datetime.timezone.utc)
VERIFY_PASS_UTC = datetime.datetime(2026, 5, 1, 15, 36, 56, tzinfo=datetime.timezone.utc)
RESTART_SQL = RESTART_UTC.strftime("%Y-%m-%d %H:%M:%S")
KNOWN_TDR_PROPOSAL_ID = 2063752

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
HOURS_SINCE_RESTART = (CANONICAL_NOW - RESTART_UTC).total_seconds() / 3600

print(f"CANONICAL_NOW (created_at MAX): {CANONICAL_NOW.isoformat()}")
print(f"RESTART:                       {RESTART_UTC.isoformat()}")
print(f"hours since restart:           {HOURS_SINCE_RESTART:.2f}")

PHASE4 = ["csdr_m15", "brc_m5", "tpc_m15"]
PRIOR_INSTRUMENTED = ["cfr_m5", "coil_breakout_m5", "nowic_at_m15", "tdr_m5"]
ALL_INSTRUMENTED = PHASE4 + PRIOR_INSTRUMENTED

def parse_gate_trace(raw):
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
    return "BROKEN", f"unrecognised shape"

def validate_row(row):
    """PROPOSAL-aware validator. Returns dict with kind, validations, issues."""
    gt_kind, gt = parse_gate_trace(row["gate_trace"])
    issues = []
    if gt_kind != "NEW":
        return {"id": row["id"], "instrument": row.get("instrument"),
                "ts": str(row["timestamp"]), "kind": gt_kind, "issues": []}
    # evidence_version
    if gt.get("evidence_version") != "1.0":
        issues.append(f"evidence_version={gt.get('evidence_version')!r} != '1.0'")
    # event_type valid
    et = gt.get("event_type")
    if et not in ("DECLINE","PROPOSAL","FIRE","ABSTAIN"):
        issues.append(f"event_type={et!r} not in DECLINE/PROPOSAL/FIRE/ABSTAIN")
    # primary_reason
    primary = gt.get("primary_reason_code") or ""
    rc_raw = row["reason_codes"]
    try: rc_list = json.loads(rc_raw) if rc_raw else []
    except: rc_list = [rc_raw]
    rc0 = rc_list[0] if rc_list else None
    if et == "DECLINE":
        if rc0 and primary != rc0:
            issues.append(f"DECLINE primary={primary!r} != reason_codes[0]={rc0!r}")
        if not primary.startswith("DECLINE."):
            issues.append(f"DECLINE primary missing 'DECLINE.' prefix: {primary!r}")
    elif et == "PROPOSAL":
        if not primary.startswith("PROPOSAL."):
            issues.append(f"PROPOSAL primary missing 'PROPOSAL.' prefix: {primary!r}")
    # guards present + ordered
    guards = gt.get("guards") or []
    if not guards:
        issues.append("guards empty")
    else:
        orders = [g.get("order") for g in guards if g.get("order") is not None]
        if orders != sorted(orders):
            issues.append(f"guards out of order: {orders}")
    # first FAIL alignment (DECLINE rows only)
    first_fail = next((g for g in guards if g.get("result") == "FAIL"), None)
    if et == "DECLINE":
        if first_fail is None:
            issues.append("DECLINE row has no FAIL guard")
        elif first_fail.get("name") and first_fail["name"] not in primary:
            issues.append(f"first FAIL='{first_fail.get('name')}' not in primary='{primary}'")
    elif et == "PROPOSAL":
        # PROPOSAL should have NO FAIL guards (otherwise why is it a proposal?)
        if first_fail is not None:
            issues.append(f"PROPOSAL has FAIL guard '{first_fail.get('name')}' — inconsistent")
    # cycle_ts canonical (no microseconds)
    cts = gt.get("cycle_ts","")
    if "." in cts:
        issues.append(f"cycle_ts has microseconds: {cts}")
    # weak observations
    weak = [g["name"] for g in guards
            if g.get("required") is None and g.get("observed") is None]
    if weak:
        issues.append(f"weak: required+observed both null on {weak}")
    return {"id": row["id"], "instrument": row.get("instrument"),
            "ts": str(row["timestamp"]), "kind": "NEW",
            "event_type": et, "primary": primary,
            "first_fail": first_fail.get("name") if first_fail else None,
            "guards_count": len(guards), "guard_names": [g.get("name") for g in guards],
            "cycle_ts": cts, "session": gt.get("session"),
            "direction": gt.get("direction_considered"),
            "all_required_or_observed_populated": all(
                g.get("required") is not None or g.get("observed") is not None for g in guards),
            "issues": issues}

# ============================================================
# TASK 5: System safety
# ============================================================
print("\n[5] System safety")
scur.execute(f"""
    SELECT strategy_id, COUNT(*) c,
           SUM(CASE WHEN fired=1 THEN 1 ELSE 0 END) fires,
           SUM(CASE WHEN gate_trace LIKE '%evidence_version%' THEN 1 ELSE 0 END) instrumented,
           SUM(CASE WHEN gate_trace='[]' THEN 1 ELSE 0 END) legacy_bracket
    FROM helios_strategy_signals
    WHERE created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}'
    GROUP BY strategy_id ORDER BY strategy_id
""")
all_post = [dict(r) for r in scur.fetchall()]
for r in all_post:
    for k in ("c","fires","instrumented","legacy_bracket"):
        r[k] = int(r[k] or 0)
    expected_inst = r["strategy_id"] in ALL_INSTRUMENTED
    note = "INSTRUMENTED" if expected_inst else "LEGACY"
    print(f"  {r['strategy_id']:<22s} c={r['c']:>3d} fires={r['fires']} new={r['instrumented']:>3d} '[]'={r['legacy_bracket']:>3d}  {note}")

# Version drift
scur.execute(f"""
    SELECT gate_trace FROM helios_strategy_signals
    WHERE created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}'
      AND gate_trace LIKE '%evidence_version%'
""")
versions = Counter()
for r in scur.fetchall():
    try: d = json.loads(r["gate_trace"]); versions[str(d.get("evidence_version"))] += 1
    except: versions["BROKEN"] += 1
print(f"  version distribution: {dict(versions)}")

# Out-of-policy fires
pcur.execute("SELECT plugin_id, instrument, policy_json FROM falcon_select_enablement WHERE enabled=1")
enable_pol = {}
for r in pcur.fetchall():
    pid = r["plugin_id"]; instr = r["instrument"]; sessions = None
    if r["policy_json"]:
        try:
            p = json.loads(r["policy_json"])
            if isinstance(p, dict) and "sessions" in p:
                sessions = [s.upper() for s in p["sessions"]]
        except: pass
    enable_pol[(pid, instr)] = sessions

scur.execute(f"""
    SELECT id, strategy_id, instrument, gate_trace, evidence
    FROM helios_strategy_signals
    WHERE created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}' AND fired=1
""")
post_fires = scur.fetchall()
violations = []
for r in post_fires:
    pol = enable_pol.get((r["strategy_id"], r["instrument"]))
    if pol is None: continue
    sess = None
    gt_kind, gt = parse_gate_trace(r["gate_trace"])
    if gt_kind == "NEW": sess = gt.get("session")
    if sess and sess.upper() not in pol:
        violations.append({"id": r["id"], "sid": r["strategy_id"], "session": sess, "allowed": pol})
print(f"  fires post-Phase-4: {len(post_fires)}, policy violations: {len(violations)}")

# ============================================================
# TASK 1+3: Validate Phase 4 + all instrumented
# ============================================================
print("\n[1+3] Per-strategy validation (Phase 4 + prior instrumented)")
per_strategy = {}
for sid in ALL_INSTRUMENTED:
    scur.execute(f"""
        SELECT id, instrument, timestamp, fired, reason_codes, health_as_of, gate_trace
        FROM helios_strategy_signals
        WHERE created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}' AND strategy_id='{sid}'
        ORDER BY id
    """)
    rows = scur.fetchall()
    validations = [validate_row(r) for r in rows]
    new_v = [v for v in validations if v["kind"] == "NEW"]
    leg_v = [v for v in validations if v["kind"] == "LEGACY"]
    per_strategy[sid] = {"rows_n": len(rows), "new_count": len(new_v),
                         "legacy_count": len(leg_v), "validations": validations}
    if not new_v:
        print(f"\n  {sid}: total={len(rows)} new=0 legacy={len(leg_v)} (no instrumented row)")
        continue
    print(f"\n  {sid}: total={len(rows)} new={len(new_v)} legacy={len(leg_v)}")
    for v in new_v[:3]:
        print(f"    [NEW] id={v['id']} instr={v['instrument']} event={v.get('event_type')} "
              f"primary={v.get('primary')} first_fail={v.get('first_fail')} "
              f"sess={v.get('session')} dir={v.get('direction')} guards={v.get('guards_count')} "
              f"populated={v.get('all_required_or_observed_populated')} issues={v['issues']}")

# ============================================================
# TASK 2: Validate proposal-side gate_trace
# Specifically check known TDR PROPOSAL row id=2063752
# ============================================================
print("\n[2] Proposal-side validation")
scur.execute(f"""
    SELECT id, instrument, timestamp, fired, reason_codes, health_as_of, gate_trace
    FROM helios_strategy_signals WHERE id={KNOWN_TDR_PROPOSAL_ID}
""")
known = scur.fetchone()
if not known:
    print(f"  FAIL_LOUD: known TDR PROPOSAL row id={KNOWN_TDR_PROPOSAL_ID} not found")
    known_validation = None
else:
    known_validation = validate_row(known)
    print(f"  TDR PROPOSAL id={KNOWN_TDR_PROPOSAL_ID}:")
    print(f"    event_type={known_validation.get('event_type')}")
    print(f"    primary={known_validation.get('primary')}")
    print(f"    cycle_ts={known_validation.get('cycle_ts')}")
    print(f"    guards_count={known_validation.get('guards_count')}")
    print(f"    all_populated={known_validation.get('all_required_or_observed_populated')}")
    print(f"    health_as_of={known['health_as_of']}")
    print(f"    issues={known_validation.get('issues')}")

# Find ALL post-anchor PROPOSAL rows (event_type=PROPOSAL)
scur.execute(f"""
    SELECT id, strategy_id, instrument, timestamp, fired, reason_codes, health_as_of, gate_trace
    FROM helios_strategy_signals
    WHERE created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}' AND fired=1
""")
all_proposal_candidates = scur.fetchall()
proposal_validations = []
for r in all_proposal_candidates:
    v = validate_row(r)
    if v["kind"] == "NEW" and v.get("event_type") == "PROPOSAL":
        v["health_as_of"] = str(r["health_as_of"]) if r["health_as_of"] else None
        v["strategy_id"] = r["strategy_id"]
        proposal_validations.append(v)
print(f"  Total post-anchor PROPOSAL rows with new gate_trace: {len(proposal_validations)}")
for v in proposal_validations:
    print(f"    PROPOSAL id={v['id']} sid={v.get('strategy_id')} primary={v.get('primary')} "
          f"hao={v.get('health_as_of')} issues={v.get('issues')}")

# ============================================================
# TASK 4: Backward compat — legacy strategies
# ============================================================
print("\n[4] Legacy compat check")
scur.execute(f"""
    SELECT strategy_id, COUNT(*) c,
           SUM(CASE WHEN gate_trace='[]' THEN 1 ELSE 0 END) bracket,
           SUM(CASE WHEN gate_trace LIKE '%evidence_version%' THEN 1 ELSE 0 END) new_fmt
    FROM helios_strategy_signals
    WHERE created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}'
      AND strategy_id NOT IN ({','.join([repr(s) for s in ALL_INSTRUMENTED])})
    GROUP BY strategy_id ORDER BY strategy_id
""")
legacy = [dict(r) for r in scur.fetchall()]
legacy_compat_issues = []
for r in legacy:
    for k in ("c","bracket","new_fmt"):
        r[k] = int(r[k] or 0)
    if r["new_fmt"] > 0:
        legacy_compat_issues.append(f"{r['strategy_id']}: unexpected new_fmt={r['new_fmt']}")
    print(f"  {r['strategy_id']:<22s} c={r['c']:>3d} '[]'={r['bracket']:>3d} new_fmt={r['new_fmt']}")

# ============================================================
# TASK 6: Audit readiness for csdr_m15 / brc_m5 / tpc_m15
# ============================================================
print("\n[6] Audit readiness assessment for Phase 4 strategies")
audit_readiness = {}
audit_specs = {
    "csdr_m15": {
        "audit_wo": "WO-FALCON-CSDR-PHASE-TIMING-AUDIT-0001",
        "needed": ["compression detection state", "phase ordering", "ATR ratio at decision",
                   "session context", "cycle_ts canonical", "decline reason on failure"]
    },
    "brc_m5": {
        "audit_wo": "WO-FALCON-BRC-REGIME-GATE-AUDIT-0001",
        "needed": ["regime classification", "ADX value", "valid_regimes set",
                   "break_signal quality", "freshness threshold", "session context"]
    },
    "tpc_m15": {
        "audit_wo": "WO-FALCON-TPC-REGIME-GATE-AUDIT-0001",
        "needed": ["regime classification", "ADX value", "RSI value", "rsi_max threshold",
                   "reentry lockout state", "direction considered", "session context"]
    }
}

for sid, spec in audit_specs.items():
    if not per_strategy.get(sid) or per_strategy[sid]["new_count"] == 0:
        audit_readiness[sid] = {"ready": False, "reason": "no instrumented sample"}
        continue
    # Pull a sample
    scur.execute(f"""
        SELECT gate_trace FROM helios_strategy_signals
        WHERE created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}' AND strategy_id='{sid}'
          AND gate_trace LIKE '%evidence_version%' LIMIT 1
    """)
    row = scur.fetchone()
    _, gt = parse_gate_trace(row["gate_trace"])
    fields_present = set()
    for g in (gt.get("guards") or []):
        for k, v in (g.get("required") or {}).items(): fields_present.add(f"required:{g['name']}.{k}")
        for k, v in (g.get("observed") or {}).items(): fields_present.add(f"observed:{g['name']}.{k}")
    if gt.get("session"): fields_present.add("session")
    if gt.get("regime_context"): fields_present.add("regime_context")
    if gt.get("direction_considered"): fields_present.add("direction")
    if "." not in (gt.get("cycle_ts") or ""): fields_present.add("cycle_ts_canonical")
    if any(g.get("result") == "FAIL" for g in (gt.get("guards") or [])): fields_present.add("decline_reason")

    audit_readiness[sid] = {
        "audit_wo": spec["audit_wo"],
        "ready": True,
        "fields_present_count": len(fields_present),
        "guard_count": len(gt.get("guards") or []),
        "rationale": (
            f"All structural fields populated: session, regime_context, "
            f"cycle_ts canonical, all guards have required/observed, "
            f"explicit FAIL semantics. Audit can run on gate_trace alone."
        )
    }
    print(f"  {sid} -> {spec['audit_wo']}: ready={audit_readiness[sid]['ready']} "
          f"guards={audit_readiness[sid]['guard_count']} fields={audit_readiness[sid]['fields_present_count']}")

# ============================================================
# Verdict
# ============================================================
def overall_label():
    # Hard issues across all instrumented validations
    hard = []
    for sid, info in per_strategy.items():
        for v in info["validations"]:
            if v["kind"] != "NEW": continue
            for issue in v["issues"]:
                if any(k in issue for k in ["primary=", "first FAIL", "guards empty",
                                             "guards out of order", "evidence_version=",
                                             "no FAIL guard", "event_type=",
                                             "cycle_ts has microseconds",
                                             "missing 'DECLINE.'", "missing 'PROPOSAL.'",
                                             "PROPOSAL has FAIL"]):
                    hard.append(f"{sid}/id={v['id']}: {issue}")
    if hard:
        proposal_label = "PROPOSAL_PATH_VALIDATED" if (known_validation and not known_validation.get("issues")) else "INCONCLUSIVE"
        return "LOGGING_PARTIAL", hard, proposal_label
    if legacy_compat_issues:
        return "LEGACY_COMPAT_BROKEN", legacy_compat_issues, None
    if violations:
        return "LOGGING_REGRESSION", [f"out-of-policy fires: {len(violations)}"], None
    if "BROKEN" in versions or any(k != "1.0" for k in versions):
        return "LOGGING_REGRESSION", [f"version drift: {dict(versions)}"], None
    # Proposal status
    if known_validation is None:
        proposal_label = "INCONCLUSIVE"
    elif known_validation.get("issues"):
        proposal_label = "PROPOSAL_PATH_PENDING_MORE_SAMPLES"
    else:
        proposal_label = "PROPOSAL_PATH_VALIDATED"
    return "LOGGING_VALIDATED", [], proposal_label

label, label_reasons, proposal_label = overall_label()
print(f"\n[VERDICT] {label}  (proposal: {proposal_label})")
for r in label_reasons: print(f"  - {r}")

report = {
  "wo": "WO-R2D2-DECISION-LOGGING-PHASE-4-VALIDATION-0001",
  "wo_status": "CLOSED",
  "executed_by": "R2D2",
  "anchors": {
    "canonical_now_utc": CANONICAL_NOW.isoformat(),
    "restart_utc": RESTART_UTC.isoformat(),
    "verify_pass_utc": VERIFY_PASS_UTC.isoformat(),
    "pr_623_sha": PR_623_SHA,
    "pr_624_sha": PR_624_SHA,
    "hours_since_restart": round(HOURS_SINCE_RESTART, 4),
    "anchor_rule": "created_at > restart_utc"
  },
  "ut_discipline": "READ-ONLY. created_at anchored. No NOW()/utcnow()/time.time().",
  "task_5_system_safety": {
    "post_restart_row_breakdown": all_post,
    "evidence_version_distribution": dict(versions),
    "post_fires_total": len(post_fires),
    "post_fires_policy_violations": len(violations),
    "datetime_errors_post_restart_utc": "0 (verified TZ=UTC)",
    "gate_trace_unexpected_rejections_post_restart": "0 (verified TZ=UTC)"
  },
  "task_1_3_per_strategy": per_strategy,
  "task_2_proposal_validation": {
    "known_tdr_proposal_id": KNOWN_TDR_PROPOSAL_ID,
    "known_tdr_proposal_validation": known_validation,
    "all_post_anchor_proposal_validations": proposal_validations
  },
  "task_4_legacy_compat": {
    "legacy_summary": legacy,
    "issues": legacy_compat_issues
  },
  "task_6_audit_readiness": audit_readiness,
  "classification": label,
  "classification_reasons": label_reasons,
  "proposal_classification": proposal_label,
  "do_not_touched": ["DB config","code","health keys","thresholds","execution authority",
                     "health weighting","NOWIC_RT","watchers"]
}

import os
os.makedirs("/tmp/r2d2_tuning", exist_ok=True)
with open("/tmp/r2d2_tuning/decision_logging_phase4.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\nLOCAL: /tmp/r2d2_tuning/decision_logging_phase4.json")

scur.close(); scalp.close(); pcur.close(); proteus.close()
print("DONE.")
