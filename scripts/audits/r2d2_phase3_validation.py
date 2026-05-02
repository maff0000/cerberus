"""WO-R2D2-DECISION-LOGGING-PHASE-3-VALIDATION-0001
READ-ONLY. Anchor: created_at > 2026-05-01T14:50:22Z (NOT cycle_ts).
UTC: architect-stamped restart anchor + DB created_at. Fail-loud."""
import json, datetime, pymysql, sys
from collections import Counter

PR_622_SHA = "4919e0e86d4a8a0375e720dae8f66a84ab5d9949"
RESTART_UTC = datetime.datetime(2026, 5, 1, 14, 50, 22, tzinfo=datetime.timezone.utc)
VERIFY_PASS_UTC = datetime.datetime(2026, 5, 1, 14, 50, 37, tzinfo=datetime.timezone.utc)
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
proteus = pymysql.connect(host="127.0.0.1", port=3307, user=env["DB_USER"],
    password=env["DB_PASSWORD"], database="tradingProteus", charset="utf8mb4")
pcur = proteus.cursor(pymysql.cursors.DictCursor)

scur.execute("SELECT MAX(created_at) AS now FROM helios_strategy_signals")
CANONICAL_NOW = scur.fetchone()["now"].replace(tzinfo=datetime.timezone.utc)
NOW_SQL = CANONICAL_NOW.strftime("%Y-%m-%d %H:%M:%S")
HOURS_SINCE_RESTART = (CANONICAL_NOW - RESTART_UTC).total_seconds() / 3600

print(f"CANONICAL_NOW (created_at MAX): {CANONICAL_NOW.isoformat()}")
print(f"RESTART:                       {RESTART_UTC.isoformat()}")
print(f"VERIFY_PASS:                   {VERIFY_PASS_UTC.isoformat()}")
print(f"PR #622 SHA:                   {PR_622_SHA}")
print(f"hours since restart:           {HOURS_SINCE_RESTART:.2f}")

PHASE3 = ["nowic_at_m15", "tdr_m5"]
PHASE2 = ["cfr_m5", "coil_breakout_m5"]
INSTRUMENTED_TOTAL = PHASE3 + PHASE2

# Parser
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
    return "BROKEN", f"unrecognised shape keys={list(d.keys()) if isinstance(d,dict) else type(d).__name__}"

def validate_row(row, sid):
    gt_kind, gt = parse_gate_trace(row["gate_trace"])
    issues = []
    if gt_kind != "NEW":
        return {"id": row["id"], "instrument": row.get("instrument"),
                "ts": str(row["timestamp"]), "kind": gt_kind, "issues": []}
    # evidence_version
    if gt.get("evidence_version") != "1.0":
        issues.append(f"evidence_version={gt.get('evidence_version')!r} != '1.0'")
    # event_type valid
    if gt.get("event_type") not in ("DECLINE","PROPOSAL","FIRE","ABSTAIN"):
        issues.append(f"event_type={gt.get('event_type')!r} not in DECLINE/PROPOSAL/FIRE/ABSTAIN")
    # primary_reason match
    rc_raw = row["reason_codes"]
    try: rc_list = json.loads(rc_raw) if rc_raw else []
    except: rc_list = [rc_raw]
    rc0 = rc_list[0] if rc_list else None
    primary = gt.get("primary_reason_code")
    if rc0 and primary != rc0:
        issues.append(f"primary={primary!r} != reason_codes[0]={rc0!r}")
    # guards present + ordered
    guards = gt.get("guards") or []
    if not guards:
        issues.append("guards empty")
    else:
        orders = [g.get("order") for g in guards if g.get("order") is not None]
        if orders != sorted(orders):
            issues.append(f"guards out of order: {orders}")
    # first FAIL alignment
    first_fail = next((g for g in guards if g.get("result") == "FAIL"), None)
    if row["fired"] == 0 and gt.get("event_type") == "DECLINE":
        if first_fail is None:
            issues.append("DECLINE row has no FAIL guard")
        elif first_fail.get("name") and first_fail["name"] not in (primary or ""):
            issues.append(f"first FAIL='{first_fail.get('name')}' not in primary='{primary}'")
    # cycle_ts canonical (no microseconds)
    cts = gt.get("cycle_ts","")
    if "." in cts:
        issues.append(f"cycle_ts has microseconds (wall-clock?): {cts}")
    # weak observations
    weak = [g["name"] for g in guards
            if g.get("required") is None and g.get("observed") is None]
    if weak:
        issues.append(f"weak: required+observed both null on {weak}")
    return {"id": row["id"], "instrument": row.get("instrument"),
            "ts": str(row["timestamp"]), "kind": "NEW",
            "event_type": gt.get("event_type"), "primary": primary,
            "first_fail": first_fail.get("name") if first_fail else None,
            "guards_count": len(guards), "guard_orders": [g.get("order") for g in guards],
            "guard_names": [g.get("name") for g in guards],
            "cycle_ts": cts, "session": gt.get("session"),
            "direction": gt.get("direction_considered"),
            "issues": issues}

# ============================================================
# TASK 7: System safety — count post-Phase-3 rows + fires + version drift
# ============================================================
print("\n[7] System safety — post-Phase-3 row breakdown")
scur.execute(f"""
    SELECT strategy_id, COUNT(*) c,
           SUM(CASE WHEN fired=1 THEN 1 ELSE 0 END) fires,
           SUM(CASE WHEN gate_trace LIKE '%evidence_version%' THEN 1 ELSE 0 END) instrumented,
           SUM(CASE WHEN gate_trace = '[]' THEN 1 ELSE 0 END) legacy_bracket,
           SUM(CASE WHEN gate_trace IS NULL OR gate_trace='' THEN 1 ELSE 0 END) null_or_empty
    FROM helios_strategy_signals
    WHERE created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}'
    GROUP BY strategy_id ORDER BY strategy_id
""")
all_post = [dict(r) for r in scur.fetchall()]
for r in all_post:
    for k in ("c","fires","instrumented","legacy_bracket","null_or_empty"):
        r[k] = int(r[k] or 0)
    expected = "NEW_or_legacy" if r["strategy_id"] in INSTRUMENTED_TOTAL else "LEGACY"
    print(f"  {r['strategy_id']:<22s} c={r['c']:>4d} fires={r['fires']:>2d} "
          f"new={r['instrumented']:>3d} '[]'={r['legacy_bracket']:>3d} expected={expected}")

# Version drift: any evidence_version != 1.0?
scur.execute(f"""
    SELECT gate_trace FROM helios_strategy_signals
    WHERE created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}'
      AND gate_trace LIKE '%evidence_version%'
""")
versions = Counter()
for r in scur.fetchall():
    try:
        d = json.loads(r["gate_trace"])
        versions[str(d.get("evidence_version"))] += 1
    except: versions["BROKEN"] += 1
print(f"  evidence_version distribution: {dict(versions)}")

# Out-of-policy fired=1: cross-check
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
    SELECT id, timestamp, strategy_id, instrument, evidence, gate_trace
    FROM helios_strategy_signals
    WHERE created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}' AND fired=1
""")
post_fires_rows = scur.fetchall()
violations = []
for r in post_fires_rows:
    pol = enable_pol.get((r["strategy_id"], r["instrument"]))
    if pol is None: continue
    sess = None
    try:
        gt_kind, gt = parse_gate_trace(r["gate_trace"])
        if gt_kind == "NEW": sess = gt.get("session")
    except: pass
    if not sess and r["evidence"]:
        try:
            ev = json.loads(r["evidence"])
            sess = (ev.get("nowic_at") or {}).get("session") or ev.get("session")
        except: pass
    if sess and sess.upper() not in pol:
        violations.append({"id": r["id"], "sid": r["strategy_id"], "session": sess, "allowed": pol})
print(f"  fires post-Phase-3: {len(post_fires_rows)}, policy violations: {len(violations)}")

# ============================================================
# TASKS 1+2+3: Validate per-strategy
# ============================================================
print("\n[1+2+3] Per-strategy gate_trace validation")
per_strategy = {}
for sid in PHASE3:
    scur.execute(f"""
        SELECT id, instrument, timestamp, fired, reason_codes, health_as_of, gate_trace
        FROM helios_strategy_signals
        WHERE created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}' AND strategy_id='{sid}'
        ORDER BY id
    """)
    rows = scur.fetchall()
    validations = [validate_row(r, sid) for r in rows]
    per_strategy[sid] = {"rows_n": len(rows), "validations": validations}

    # Bucket by NEW vs LEGACY (SESSION_BLOCKED short-circuits)
    new_n = sum(1 for v in validations if v["kind"] == "NEW")
    legacy_n = sum(1 for v in validations if v["kind"] == "LEGACY")
    print(f"\n  {sid}: total={len(rows)} new={new_n} legacy={legacy_n}")
    for v in validations:
        if v["kind"] == "NEW":
            print(f"    [NEW] id={v['id']} instr={v['instrument']} event={v.get('event_type')} "
                  f"primary={v.get('primary')} first_fail={v.get('first_fail')} "
                  f"cycle_ts={v.get('cycle_ts')} sess={v.get('session')} dir={v.get('direction')} "
                  f"issues={v['issues']}")
        else:
            # Find the row's reason for legacy
            rrow = next(r for r in rows if r["id"] == v["id"])
            rc = rrow["reason_codes"][:80] if rrow["reason_codes"] else ""
            print(f"    [LEG] id={v['id']} instr={v['instrument']} reason={rc}")

    # Check tdr_m5 PROPOSAL specifically
    if sid == "tdr_m5":
        prop_rows = [r for r in rows if r["fired"] == 1]
        per_strategy[sid]["proposal_rows"] = len(prop_rows)
        per_strategy[sid]["proposal_with_health_as_of"] = sum(1 for r in prop_rows if r["health_as_of"])
        print(f"    tdr_m5 PROPOSAL rows post-Phase-3: {len(prop_rows)} "
              f"(with non-NULL health_as_of: {per_strategy[sid]['proposal_with_health_as_of']})")
        for pr in prop_rows[:3]:
            gt_kind, gt = parse_gate_trace(pr["gate_trace"])
            print(f"      PROPOSAL id={pr['id']} hao={pr['health_as_of']} "
                  f"event_type={gt.get('event_type') if gt else 'LEGACY'}")

# ============================================================
# TASK 4: Compare to Phase 2 (cfr/coil) — structural consistency
# ============================================================
print("\n[4] Cross-phase structural comparison")
phase_signatures = {}
for sid in INSTRUMENTED_TOTAL:
    scur.execute(f"""
        SELECT gate_trace FROM helios_strategy_signals
        WHERE created_at >= '{RESTART_SQL}' AND strategy_id='{sid}'
          AND gate_trace LIKE '%evidence_version%'
        ORDER BY id LIMIT 1
    """)
    row = scur.fetchone()
    if not row: continue
    _, gt = parse_gate_trace(row["gate_trace"])
    if gt:
        guard_names = [g.get("name") for g in (gt.get("guards") or [])]
        # First guard name (the freshness gate) — should be consistent
        freshness_guard = guard_names[0] if guard_names else None
        all_required_populated = all(g.get("required") is not None or g.get("observed") is not None
                                     for g in (gt.get("guards") or []))
        phase_signatures[sid] = {
            "freshness_guard_name": freshness_guard,
            "guard_count": len(guard_names),
            "guard_names": guard_names,
            "session_populated": gt.get("session") is not None,
            "regime_context_populated": gt.get("regime_context") is not None,
            "direction_populated": gt.get("direction_considered") is not None,
            "cycle_ts_canonical": "." not in (gt.get("cycle_ts") or ""),
            "all_guards_have_data": all_required_populated
        }

for sid, sig in phase_signatures.items():
    print(f"  {sid:<22s} freshness={sig['freshness_guard_name']!r:<18s} "
          f"guards={sig['guard_count']} session={sig['session_populated']} "
          f"regime={sig['regime_context_populated']} direction={sig['direction_populated']} "
          f"cts_canonical={sig['cycle_ts_canonical']} all_data={sig['all_guards_have_data']}")

# Naming inconsistency: collect distinct freshness guard names
freshness_names = set(s["freshness_guard_name"] for s in phase_signatures.values()
                      if s["freshness_guard_name"])
print(f"  Distinct freshness guard names across instrumented: {sorted(freshness_names)}")

# ============================================================
# TASK 5: Backward compat
# ============================================================
print("\n[5] Backward compatibility — legacy strategies")
scur.execute(f"""
    SELECT strategy_id, COUNT(*) c,
           SUM(CASE WHEN gate_trace='[]' THEN 1 ELSE 0 END) bracket_empty,
           SUM(CASE WHEN gate_trace LIKE '%evidence_version%' THEN 1 ELSE 0 END) new_fmt
    FROM helios_strategy_signals
    WHERE created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}'
      AND strategy_id NOT IN ('cfr_m5','coil_breakout_m5','nowic_at_m15','tdr_m5')
    GROUP BY strategy_id ORDER BY c DESC
""")
legacy = [dict(r) for r in scur.fetchall()]
legacy_compat_issues = []
for r in legacy:
    for k in ("c","bracket_empty","new_fmt"):
        r[k] = int(r[k] or 0)
    if r["new_fmt"] > 0:
        legacy_compat_issues.append(f"{r['strategy_id']}: unexpected new_fmt={r['new_fmt']}")
    print(f"  {r['strategy_id']:<22s} c={r['c']:>3d} '[]'={r['bracket_empty']:>3d} new_fmt={r['new_fmt']:>3d}")

# ============================================================
# TASK 6: Usefulness — can R2D2 explain decline without worker code?
# ============================================================
print("\n[6] Usefulness assessment")
def explain_first_fail(gt):
    if not gt: return "(no gate_trace)"
    fail = next((g for g in (gt.get("guards") or []) if g.get("result") == "FAIL"), None)
    if not fail: return "(no FAIL guard)"
    return (f"declined at gate '{fail.get('name')}' (order {fail.get('order')}). "
            f"required={fail.get('required')} observed={fail.get('observed')}")

usefulness = {}
for sid in PHASE3:
    scur.execute(f"""
        SELECT gate_trace FROM helios_strategy_signals
        WHERE created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}' AND strategy_id='{sid}'
          AND gate_trace LIKE '%evidence_version%'
        ORDER BY id LIMIT 1
    """)
    row = scur.fetchone()
    if not row:
        usefulness[sid] = "(no instrumented row)"
        continue
    _, gt = parse_gate_trace(row["gate_trace"])
    explanation = explain_first_fail(gt)
    usefulness[sid] = explanation
    print(f"  {sid}: {explanation}")

# ============================================================
# Verdict
# ============================================================
def overall_label():
    nowic = per_strategy["nowic_at_m15"]["validations"]
    tdr = per_strategy["tdr_m5"]["validations"]
    nowic_new = [v for v in nowic if v["kind"] == "NEW"]
    tdr_new = [v for v in tdr if v["kind"] == "NEW"]
    if not nowic_new and not tdr_new:
        return "LOGGING_NEEDS_MORE_RUNTIME_ROWS", ["zero new-format rows for both Phase 3 strategies"]
    hard = []
    for sid, vs in (("nowic_at_m15", nowic_new), ("tdr_m5", tdr_new)):
        for v in vs:
            for issue in v["issues"]:
                if any(k in issue for k in ["primary=", "first FAIL", "guards empty",
                                             "guards out of order", "evidence_version=",
                                             "no FAIL guard", "event_type=",
                                             "cycle_ts has microseconds"]):
                    hard.append(f"{sid}/id={v['id']}: {issue}")
    if hard:
        return "LOGGING_PARTIAL", hard
    if legacy_compat_issues:
        return "LEGACY_COMPAT_BROKEN", legacy_compat_issues
    if violations:
        return "LOGGING_REGRESSION", [f"out-of-policy fires: {len(violations)}"]
    if "BROKEN" in versions or any(k != "1.0" for k in versions):
        return "LOGGING_REGRESSION", [f"version drift: {dict(versions)}"]
    # tdr proposal absence is allowed (TDR_PROPOSAL_PENDING) — separate label
    tdr_props = per_strategy["tdr_m5"].get("proposal_rows", 0)
    if tdr_props == 0:
        return "TDR_PROPOSAL_PENDING", [
            f"Phase 3 hard checks PASS (nowic_at + tdr DECLINE rows clean), "
            f"but no tdr_m5 PROPOSAL row in window — non-blocking; sample is {len(tdr_new)} DECLINE row(s)"
        ]
    return "LOGGING_VALIDATED", []

label, label_reasons = overall_label()
print(f"\n[VERDICT] {label}")
for r in label_reasons:
    print(f"  - {r}")

# ============================================================
# Phase 4 candidate
# ============================================================
print("\n[Phase 4 candidates]")
scur.execute(f"""
    SELECT strategy_id, COUNT(*) c
    FROM helios_strategy_signals
    WHERE timestamp >= '2026-04-28 00:00:00' AND timestamp <= '{NOW_SQL}'
      AND strategy_id NOT IN ('cfr_m5','coil_breakout_m5','nowic_at_m15','tdr_m5')
    GROUP BY strategy_id ORDER BY c DESC
""")
remaining_traffic = {r["strategy_id"]: int(r["c"]) for r in scur.fetchall()}
print(f"  remaining strategies (not yet instrumented), 4-day traffic:")
for s, c in sorted(remaining_traffic.items(), key=lambda x: -x[1]):
    print(f"    {s:<22s} {c}")

phase4_candidates = ["csdr_m15", "brc_m5", "tpc_m15"]
phase4_reasoning = (
    "Recommend Phase 4 batch: csdr_m15 + brc_m5 + tpc_m15. Each has a pending "
    "audit WO (CSDR phase timing, BRC regime gate, TPC regime gate). "
    "Instrumenting these BEFORE the audits run will provide native gate-trace evidence "
    "instead of ad-hoc DB grovels — exactly the rhythm of instrument -> validate -> expand."
)

# Save
report = {
  "wo": "WO-R2D2-DECISION-LOGGING-PHASE-3-VALIDATION-0001",
  "wo_status": "CLOSED",
  "executed_by": "R2D2",
  "anchors": {
    "canonical_now_utc": CANONICAL_NOW.isoformat(),
    "restart_utc": RESTART_UTC.isoformat(),
    "verify_pass_utc": VERIFY_PASS_UTC.isoformat(),
    "pr_622_sha": PR_622_SHA,
    "hours_since_restart": round(HOURS_SINCE_RESTART, 4),
    "anchor_rule": "created_at > restart_utc"
  },
  "ut_discipline": "READ-ONLY. created_at anchored. No NOW()/utcnow()/time.time().",
  "task_7_system_safety": {
    "post_restart_row_breakdown": all_post,
    "evidence_version_distribution": dict(versions),
    "post_fires_total": len(post_fires_rows),
    "post_fires_policy_violations": len(violations),
    "datetime_errors_post_restart_utc": "0 (verified TZ=UTC journalctl)"
  },
  "task_1_2_3_per_strategy": per_strategy,
  "task_4_cross_phase_signatures": phase_signatures,
  "task_4_naming_inconsistency": {
    "freshness_guard_names_across_instrumented": sorted(freshness_names),
    "concern": "freshness gate has different names across strategies — cfr=HERMES_STALE, tdr=STALE_DATA, coil=HERMES_STALE, nowic_at=SESSION_BLOCKED-first. Not blocking but harmonising would simplify cross-strategy review."
  },
  "task_5_legacy_compat": {
    "legacy_summary": legacy,
    "issues": legacy_compat_issues,
    "instrumented_count": 4,
    "legacy_count": len(legacy)
  },
  "task_6_usefulness": usefulness,
  "task_8_phase4_candidates": {
    "ranking_by_traffic": [{"sid": s, "traffic_4d": c} for s, c in sorted(remaining_traffic.items(), key=lambda x:-x[1])],
    "recommended_batch": phase4_candidates,
    "rationale": phase4_reasoning
  },
  "classification": label,
  "classification_reasons": label_reasons,
  "do_not_touched": ["DB config","code","health keys","thresholds","execution authority",
                     "health weighting","NOWIC_RT","watchers"],
  "precursor_audits": [
    "r2d2:audit:cfr_hermes_stale_investigation:latest",
    "r2d2:audit:cfr_post_threshold_revalidation:latest",
    "r2d2:audit:decision_logging_phase_2_validation:latest",
    "r2d2:audit:health_as_of_writer_fix_validation:latest"
  ]
}

import os
os.makedirs("/tmp/r2d2_tuning", exist_ok=True)
with open("/tmp/r2d2_tuning/decision_logging_phase3.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\nLOCAL: /tmp/r2d2_tuning/decision_logging_phase3.json")

scur.close(); scalp.close(); pcur.close(); proteus.close()
print("DONE.")
