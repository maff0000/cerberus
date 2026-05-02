"""WO-R2D2-POST-HARDENING-BACKTEST-REVALIDATION-0001 — short post-ARES confirmation pass.
READ-ONLY. UTC: cycle_ts canonical + git commit_date. No NOW()/utcnow()/time.time()."""

import json, datetime, pymysql, urllib.request
from collections import Counter

env = {}
with open("/srv-dev/tradingProteus/.env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v.strip('"').strip("'")

# Anchors
PR_614_GUARDRAIL = datetime.datetime(2026, 5, 1, 8, 6, 32, tzinfo=datetime.timezone.utc)
PR_615_ARES_WHALE = datetime.datetime(2026, 5, 1, 10, 2, 40, tzinfo=datetime.timezone.utc)
PR_615_SQL = PR_615_ARES_WHALE.strftime("%Y-%m-%d %H:%M:%S")

scalp = pymysql.connect(host="127.0.0.1", port=3307, user=env["DB_USER"],
    password=env["DB_PASSWORD"], database="tradingScalp", charset="utf8mb4")
scur = scalp.cursor(pymysql.cursors.DictCursor)
proteus = pymysql.connect(host="127.0.0.1", port=3307, user=env["DB_USER"],
    password=env["DB_PASSWORD"], database="tradingProteus", charset="utf8mb4")
pcur = proteus.cursor(pymysql.cursors.DictCursor)

scur.execute("SELECT MAX(cycle_ts) AS now FROM helios_v3_decisions")
CANONICAL_NOW = scur.fetchone()["now"].replace(tzinfo=datetime.timezone.utc)
NOW_SQL = CANONICAL_NOW.strftime("%Y-%m-%d %H:%M:%S")
print(f"CANONICAL_NOW: {CANONICAL_NOW.isoformat()}")
print(f"PR #615 ARES_WHALE: {PR_615_ARES_WHALE.isoformat()}")
print(f"hours since PR #615: {(CANONICAL_NOW - PR_615_ARES_WHALE).total_seconds()/3600:.2f}")

# ============================================================
# TASK 1: Confirm ARES clean state visible in fabric
# ============================================================
def get_fab(k):
    try:
        r = urllib.request.urlopen(f"http://localhost:8080/api/v1/redis/get/{k}", timeout=5)
        d = json.loads(r.read())
        return json.loads(d["value"]) if d.get("value") else None
    except: return None

print("\n[1] ARES clean state check (fabric)")
ares_keys = ["ares:risk_score:global", "ares:macro:snapshot", "ares:market:status",
             "ares:risk:XAU_USD:SCALP:NORMAL", "ares:risk:XAU_USD:SWING:NORMAL"]
ares_summary = {}
for k in ares_keys:
    v = get_fab(k)
    if not isinstance(v, dict):
        ares_summary[k] = "MISSING"; continue
    fields = v.get("fields", {})
    payload = fields.get("payload_json", {}) if isinstance(fields, dict) else {}
    health = payload.get("health", {}) if isinstance(payload, dict) else {}
    ares_summary[k] = {
        "level": v.get("level"),
        "degradation_state": fields.get("degradation_state") if isinstance(fields, dict) else None,
        "posture": fields.get("posture") if isinstance(fields, dict) else None,
        "fault_codes": fields.get("fault_codes") if isinstance(fields, dict) else None,
        "snapshot_state": payload.get("snapshot_state") if isinstance(payload, dict) else None,
        "missing_modules": payload.get("missing_modules") if isinstance(payload, dict) else None,
        "degraded": health.get("degraded") if isinstance(health, dict) else None,
        "fail_reason": health.get("fail_reason") if isinstance(health, dict) else None,
    }
    print(f"  {k}: deg={ares_summary[k]['degradation_state']} posture={ares_summary[k]['posture']} "
          f"snap={ares_summary[k]['snapshot_state']} missing={ares_summary[k]['missing_modules']} "
          f"faults={ares_summary[k]['fault_codes']}")

# Determine ARES verdict
any_degraded = any(isinstance(s, dict) and (s.get("degradation_state") == "ERROR" or s.get("degraded"))
                    for s in ares_summary.values())
defensive_posture = any(isinstance(s, dict) and s.get("posture") == "DEFENSIVE" for s in ares_summary.values())
ares_verdict = "DEGRADED" if any_degraded else ("DEFENSIVE" if defensive_posture else "CLEAN")
print(f"\n  ARES verdict (fabric snapshot): {ares_verdict}")

# Also check ares_whale state explicitly per architect's mention
whale_state = get_fab("ares:whale:state") or get_fab("ares:whale:XAU_USD") or get_fab("ares_whale:state")
print(f"  ares_whale state: {whale_state if whale_state else 'KEY_NOT_FOUND'}")

# ============================================================
# TASK 2+3+4: post-PR-#615 policy/guardrail/family regressions
# ============================================================
print(f"\n[2-4] Post-PR-#615 regression check ({(CANONICAL_NOW - PR_615_ARES_WHALE).total_seconds()/3600:.2f}h elapsed)")

# Q4: out-of-policy fired=1 rows post-PR-#615
scur.execute(f"""
    SELECT id, timestamp, strategy_id, instrument, evidence
    FROM helios_strategy_signals
    WHERE fired=1 AND timestamp >= '{PR_615_SQL}' AND timestamp <= '{NOW_SQL}'
""")
post_fires = scur.fetchall()
print(f"  post-PR-#615 fired=1 rows: {len(post_fires)}")

# Read enablement for cross-check
pcur.execute("SELECT plugin_id, instrument, enabled, policy_json FROM falcon_select_enablement WHERE enabled=1")
enable_pol = {}
for r in pcur.fetchall():
    pid = r["plugin_id"]; instr = r["instrument"]
    sessions = None
    if r["policy_json"]:
        try:
            p = json.loads(r["policy_json"])
            if isinstance(p, dict) and "sessions" in p:
                sessions = [s.upper() for s in p["sessions"]]
        except: pass
    enable_pol[(pid, instr)] = sessions

violations = []
for r in post_fires:
    sid = r["strategy_id"]; instr = r["instrument"]
    pol = enable_pol.get((sid, instr))
    if pol is None: continue  # no policy or disabled = different audit
    try: ev = json.loads(r["evidence"]) if r["evidence"] else {}
    except: ev = {}
    nat = ev.get("nowic_at") or ev.get("nowic_rt") or {}
    sess = (nat.get("session") if nat else None) or ev.get("session")
    if sess and sess.upper() not in pol:
        violations.append({"id":r["id"],"ts":str(r["timestamp"]),"sid":sid,"instr":instr,
                           "session":sess,"allowed":pol})
print(f"  post-PR-#615 policy violations: {len(violations)}")

# Q3: SESSION_BLOCKED rows persisting
scur.execute(f"""
    SELECT COUNT(*) c FROM helios_strategy_signals
    WHERE timestamp >= '{PR_615_SQL}' AND timestamp <= '{NOW_SQL}'
      AND fired=0 AND reason_codes LIKE '%SESSION_BLOCKED%'
""")
sb_post615 = int(scur.fetchone()["c"])
print(f"  post-PR-#615 SESSION_BLOCKED audit rows: {sb_post615}")

# Q3: FALCON_PROPOSAL_INVALID_FAMILY post-PR-#615
pcur.execute(f"""
    SELECT COUNT(*) c FROM falcon_fault_log
    WHERE created_at >= '{PR_615_SQL}' AND created_at <= '{NOW_SQL}'
      AND fault_code LIKE '%INVALID_FAMILY%'
""")
invalid_family = int(pcur.fetchone()["c"])

# Any other faults
pcur.execute(f"""
    SELECT fault_code, COUNT(*) c FROM falcon_fault_log
    WHERE created_at >= '{PR_615_SQL}' AND created_at <= '{NOW_SQL}'
    GROUP BY fault_code ORDER BY c DESC
""")
all_faults = [dict(r) for r in pcur.fetchall()]
print(f"  post-PR-#615 INVALID_FAMILY faults: {invalid_family}")
print(f"  post-PR-#615 all falcon_fault_log: {len(all_faults)} categories, total: {sum(f['c'] for f in all_faults)}")
for f in all_faults[:5]: print(f"    {f}")

# Guardrail rejections post-PR-#615
scur.execute(f"""
    SELECT COUNT(*) c FROM helios_strategy_signals
    WHERE timestamp >= '{PR_615_SQL}' AND timestamp <= '{NOW_SQL}'
      AND fired=0 AND reason_codes LIKE '%GUARDRAIL%'
""")
guardrail_post615 = int(scur.fetchone()["c"])
print(f"  post-PR-#615 GUARDRAIL rejections: {guardrail_post615}")

# Q5: watchers state confirmation (read fabric)
state_tdr = get_fab("r2d2:watcher:tdr_validation:state")
state_nat = get_fab("r2d2:watcher:nowic_at_validation:state")
print(f"\n[5] Watcher states:")
print(f"  TDR:     {state_tdr.get('status') if state_tdr else 'MISSING'} anchor={state_tdr.get('anchor_utc_canonical') if state_tdr else None}")
print(f"  NOWIC_AT: {state_nat.get('status') if state_nat else 'MISSING'} anchor={state_nat.get('anchor_utc_canonical') if state_nat else None}")

# Q6: Re-state clean strategy evidence (delta from previous)
# Read prior backtest revalidation + check for any new clean fires
prior_report = get_fab("r2d2:audit:post_hardening_backtest_revalidation:latest")

# Count post-PR-#615 clean fires per strategy
scur.execute(f"""
    SELECT strategy_id, instrument, COUNT(*) c
    FROM helios_strategy_signals
    WHERE fired=1 AND timestamp >= '{PR_615_SQL}' AND timestamp <= '{NOW_SQL}'
    GROUP BY strategy_id, instrument ORDER BY c DESC
""")
post_615_fires_by_strategy = [dict(r) for r in scur.fetchall()]
print(f"\n[6] Post-PR-#615 fires by strategy: {len(post_615_fires_by_strategy)}")
for r in post_615_fires_by_strategy: print(f"    {r}")

# Verdict
sanity_clean = (len(violations) == 0 and invalid_family == 0 and guardrail_post615 == 0 and ares_verdict == "CLEAN")
print(f"\nSanity post-ARES: {'PASS' if sanity_clean else 'CHECK_NEEDED'}")

# Save
import os
os.makedirs("/tmp/r2d2_tuning", exist_ok=True)
out = {
    "canonical_now_utc": CANONICAL_NOW.isoformat(),
    "anchors": {
        "PR_614_GUARDRAIL": PR_614_GUARDRAIL.isoformat(),
        "PR_615_ARES_WHALE": PR_615_ARES_WHALE.isoformat()
    },
    "hours_since_pr_615": (CANONICAL_NOW - PR_615_ARES_WHALE).total_seconds()/3600,
    "ares_state": ares_summary,
    "ares_verdict": ares_verdict,
    "ares_whale_state": whale_state,
    "post_pr_615_violations": violations,
    "post_pr_615_session_blocked_count": sb_post615,
    "post_pr_615_invalid_family_faults": invalid_family,
    "post_pr_615_all_faults": all_faults,
    "post_pr_615_guardrail_rejections": guardrail_post615,
    "post_pr_615_fires_by_strategy": post_615_fires_by_strategy,
    "watcher_states": {
        "tdr": {"status": state_tdr.get("status") if state_tdr else None,
                "anchor": state_tdr.get("anchor_utc_canonical") if state_tdr else None},
        "nowic_at": {"status": state_nat.get("status") if state_nat else None,
                     "anchor": state_nat.get("anchor_utc_canonical") if state_nat else None}
    },
    "sanity_pass": sanity_clean,
    "prior_backtest_label": prior_report.get("overall_verdict") if prior_report else None
}
with open("/tmp/r2d2_tuning/post_ares.json", "w") as f:
    json.dump(out, f, indent=2, default=str)
print(f"\nSaved /tmp/r2d2_tuning/post_ares.json")

scur.close(); scalp.close(); pcur.close(); proteus.close()
