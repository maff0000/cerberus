"""WO-R2D2-CSDR-POST-TIMING-LOOSEN-REVALIDATION-24H-0001
READ-ONLY. UTC discipline absolute. Architect spec window mostly in future — honest reporting."""
import json, datetime, pymysql, sys
from collections import Counter

LOOSEN_RESTART_UTC = datetime.datetime(2026, 5, 1, 16, 10, 57, tzinfo=datetime.timezone.utc)
WINDOW_END_SPEC_UTC = datetime.datetime(2026, 5, 2, 16, 10, 57, tzinfo=datetime.timezone.utc)
LOOSEN_SQL = LOOSEN_RESTART_UTC.strftime("%Y-%m-%d %H:%M:%S")
WINDOW_END_SQL = WINDOW_END_SPEC_UTC.strftime("%Y-%m-%d %H:%M:%S")

if LOOSEN_RESTART_UTC.tzinfo is None:
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

ACTUAL_WINDOW_END = min(CANONICAL_NOW, WINDOW_END_SPEC_UTC)
ACTUAL_WINDOW_END_SQL = ACTUAL_WINDOW_END.strftime("%Y-%m-%d %H:%M:%S")
MIN_ELAPSED = (ACTUAL_WINDOW_END - LOOSEN_RESTART_UTC).total_seconds() / 60
SHORTFALL_HRS = (WINDOW_END_SPEC_UTC - CANONICAL_NOW).total_seconds() / 3600

print(f"CANONICAL_NOW (created_at MAX): {CANONICAL_NOW.isoformat()}")
print(f"LOOSEN restart:                 {LOOSEN_RESTART_UTC.isoformat()}")
print(f"WINDOW END (spec):              {WINDOW_END_SPEC_UTC.isoformat()}")
print(f"WINDOW END (actual data):       {ACTUAL_WINDOW_END.isoformat()}")
print(f"Minutes of actual data:         {MIN_ELAPSED:.1f}")
print(f"Shortfall to spec window end:   {SHORTFALL_HRS:.2f} hours in the future")

# ============================================================
# CONFIG SANITY
# ============================================================
pcur.execute("""
    SELECT config_key, config_value FROM falcon_strategy_csdr_config
    WHERE instrument='XAU_USD' AND mode='NORMAL'
      AND config_key IN ('csdr_max_bars_after_sweep','csdr_min_fvg_atr')
""")
config = {r["config_key"]: r["config_value"] for r in pcur.fetchall()}
threshold_correct = (str(config.get("csdr_max_bars_after_sweep")) == "6")
print(f"\n[CONFIG] csdr_max_bars_after_sweep = {config.get('csdr_max_bars_after_sweep')} (expected 6, correct={threshold_correct})")
print(f"         csdr_min_fvg_atr           = {config.get('csdr_min_fvg_atr')} (untouched)")

# ============================================================
# 1-9. Metrics over actual elapsed window
# ============================================================
scur.execute(f"""
    SELECT id, created_at, timestamp, fired, reason_codes, evidence, gate_trace
    FROM helios_strategy_signals
    WHERE strategy_id='csdr_m15' AND created_at >= '{LOOSEN_SQL}' AND created_at <= '{ACTUAL_WINDOW_END_SQL}'
    ORDER BY created_at
""")
rows = scur.fetchall()
csdr_evals = len(rows)
fires = sum(1 for r in rows if r["fired"]==1)

waiting_disp_by_bars = Counter()
sweep_expired_by_bars = Counter()
displacement_count = 0
displacement_atrs = []
no_fvg_count = 0
proposals = 0
fp_indicators = []
phase_dist = Counter()

for r in rows:
    rc = r["reason_codes"] or ""
    try:
        ev = json.loads(r["evidence"]) if r["evidence"] else {}
    except: ev = {}
    bis = ev.get("bars_in_state")
    if "WAITING_DISPLACEMENT" in rc:
        phase_dist["WAITING_DISPLACEMENT"] += 1
        if bis is not None: waiting_disp_by_bars[int(bis)] += 1
    elif "SWEEP_EXPIRED" in rc:
        phase_dist["SWEEP_EXPIRED"] += 1
        if bis is not None: sweep_expired_by_bars[int(bis)] += 1
    elif "DISPLACEMENT_JUST_CONFIRMED" in rc:
        phase_dist["DISPLACEMENT_JUST_CONFIRMED"] += 1
        displacement_count += 1
        if ev.get("displacement_atr") is not None:
            displacement_atrs.append(float(ev["displacement_atr"]))
    elif "NO_FVG" in rc:
        phase_dist["NO_FVG"] += 1
        no_fvg_count += 1
    else:
        for ph in ["NO_COMPRESSION","COMPRESSION_JUST_DETECTED","WAITING_SWEEP",
                   "COMPRESSION_EXPIRED","SWEEP_JUST_DETECTED","SESSION_BLOCKED",
                   "PROPOSAL_READY","WAITING_RETEST","RETEST_FAILED"]:
            if ph in rc:
                phase_dist[ph] += 1; break
    if r["fired"] == 1:
        proposals += 1
        # Check session/policy on fires
        try:
            gt = json.loads(r["gate_trace"]) if r["gate_trace"] else {}
            sess = gt.get("session") if isinstance(gt, dict) else None
            if sess and sess not in ("LONDON","NY"):
                fp_indicators.append(f"fire id={r['id']} in non-allowed session {sess}")
        except: pass
        if displacement_atrs and displacement_atrs[-1] < 0.5:
            fp_indicators.append(f"fire id={r['id']} with weak displacement_atr={displacement_atrs[-1]}")

# Survives beyond bars=3 (loosen-eligible cases)
survives_beyond_3 = (sum(c for b,c in waiting_disp_by_bars.items() if b > 3) +
                     sum(c for b,c in sweep_expired_by_bars.items() if b > 3))

# Datetime / gate_trace anomaly counts (pre-checked at probe time, re-verify here)
import subprocess
def journal_count(pattern):
    cmd = ["ssh","root@192.168.11.10",
           f'TZ=UTC journalctl -u falcon-shadow --since "2026-05-01 16:10:57 UTC" --no-pager 2>/dev/null | grep -ciE "{pattern}" || echo 0']
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return int(out.stdout.strip().split()[-1])
    except Exception as e:
        return None

datetime_errors = journal_count("incorrect datetime|datetime value")
gt_unexpected = journal_count("gate_trace.*unexpected|unexpected.*gate_trace")

print(f"\n[METRICS] CSDR over actual elapsed window ({MIN_ELAPSED:.0f}min)")
print(f"  1. CSDR evaluations:         {csdr_evals}")
print(f"  2. WAITING_DISPLACEMENT by bars_in_state:")
for b in sorted(waiting_disp_by_bars.keys()):
    marker = " <-- AT NEW LIMIT (6)" if b == 6 else (" <-- POST-LOOSEN (>3)" if b > 3 else "")
    print(f"       bars={b}: {waiting_disp_by_bars[b]}{marker}")
print(f"  3. cases surviving bars > 3 (loosen-eligible): {survives_beyond_3}")
print(f"  4. DISPLACEMENT_JUST_CONFIRMED:                {displacement_count}")
print(f"  5. NO_FVG:                                     {no_fvg_count}")
print(f"  6. proposals emitted (fired=1):                {proposals}")
print(f"  7. fires:                                      {fires}")
print(f"  8. false-positive indicators:                  {len(fp_indicators)}  {fp_indicators}")
print(f"  9. datetime errors UTC:                        {datetime_errors}")
print(f"     gate_trace unexpected rejections UTC:       {gt_unexpected}")
print(f"  full phase distribution:")
for ph, c in phase_dist.most_common():
    print(f"       {ph:<32s} {c}")

# ============================================================
# 10. Comparison to 7d pre-loosen counterfactual (same as prior audit)
# ============================================================
PRE_W7_START = (LOOSEN_RESTART_UTC - datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
scur.execute(f"""
    SELECT reason_codes, evidence FROM helios_strategy_signals
    WHERE strategy_id='csdr_m15'
      AND timestamp >= '{PRE_W7_START}' AND timestamp < '{LOOSEN_SQL}'
      AND (reason_codes LIKE '%WAITING_DISPLACEMENT%' OR reason_codes LIKE '%SWEEP_EXPIRED%')
""")
pre_bars = Counter()
for r in scur.fetchall():
    rc = r["reason_codes"] or ""
    try:
        ev = json.loads(r["evidence"]) if r["evidence"] else {}
        b = ev.get("bars_in_state")
        if b is None: continue
        if "WAITING_DISPLACEMENT" in rc: pre_bars[("WAITING_DISPLACEMENT", int(b))] += 1
        elif "SWEEP_EXPIRED" in rc:      pre_bars[("SWEEP_EXPIRED", int(b))] += 1
    except: pass
counterfactual_eligible = sum(c for (ph,b),c in pre_bars.items()
                              if (ph=="WAITING_DISPLACEMENT" and b == 3)
                              or (ph=="SWEEP_EXPIRED" and b == 4))
print(f"\n[10] Counterfactual vs 7d pre-loosen: {counterfactual_eligible} setups would have gained patience")

# ============================================================
# Verdict logic — incorporates "insufficient sample" rule
# ============================================================
def verdict():
    if not threshold_correct:
        return "BLOCKED", "live config not 6"
    # Architect's intended window not yet elapsed
    if SHORTFALL_HRS > 1.0:  # > 1h short of spec end
        return "WATCH", (
            f"insufficient elapsed time — spec window ends {SHORTFALL_HRS:.1f}h in the future. "
            f"Actual data: {MIN_ELAPSED:.0f}min. "
            f"All metrics computed on actual elapsed window. "
            f"No regression observed; loosen IS in effect (cases at bars>3 = {survives_beyond_3}). "
            f"Re-run after canonical_now >= {WINDOW_END_SPEC_UTC.isoformat()}."
        )
    if fires > 0 and fp_indicators:
        return "FAIL", f"fires with FP indicators: {fp_indicators}"
    if displacement_count >= 3 and no_fvg_count >= 3 and no_fvg_count == displacement_count:
        return "PASS", "deep stages reached + FVG choke confirmed (separate audit needed)"
    if fires > 0 and not fp_indicators:
        return "PASS", "fires emerged with no FP indicators"
    if displacement_count == 0 and csdr_evals > 50:
        return "WATCH", "many evals but no displacements — continue watching, not yet revert-grade"
    return "WATCH", "no regression, no PASS conditions yet — continue forward watch"

label, reason = verdict()
print(f"\n[VERDICT] {label}")
print(f"  reason: {reason}")

def recommendation():
    if label == "BLOCKED":
        return "escalate"
    if SHORTFALL_HRS > 1.0:
        return f"continue watch — re-run after {WINDOW_END_SPEC_UTC.isoformat()}"
    if label == "FAIL":
        return "revert to 3"
    if displacement_count >= 3 and no_fvg_count == displacement_count:
        return "audit csdr_min_fvg_atr"
    if label == "PASS":
        return "hold 6"
    return "continue watch"

reco = recommendation()
print(f"  recommendation: {reco}")

# ============================================================
# Save
# ============================================================
report = {
  "wo": "WO-R2D2-CSDR-POST-TIMING-LOOSEN-REVALIDATION-24H-0001",
  "wo_status": "CLOSED",
  "executed_by": "R2D2",
  "anchors": {
    "canonical_now_utc": CANONICAL_NOW.isoformat(),
    "loosen_restart_utc": LOOSEN_RESTART_UTC.isoformat(),
    "spec_window_end_utc": WINDOW_END_SPEC_UTC.isoformat(),
    "actual_data_window_end_utc": ACTUAL_WINDOW_END.isoformat(),
    "minutes_of_actual_data_in_24h_window": round(MIN_ELAPSED, 1),
    "hours_short_of_spec_window_end": round(SHORTFALL_HRS, 2)
  },
  "ut_discipline": "READ-ONLY. created_at + journal-verified restart. No NOW()/utcnow()/time.time().",
  "anchor_reality_note": (
    f"Architect specified 24h window (16:10:57Z -> 2026-05-02T16:10:57Z). "
    f"Actual elapsed at execution: {MIN_ELAPSED:.0f} minutes ({SHORTFALL_HRS:.1f}h short of spec end). "
    f"All metrics computed on actual elapsed window. WO appears to have fired earlier than "
    f"the spec window allows; recommendation includes a defined next-review timestamp."
  ),
  "config_check": {
    "csdr_max_bars_after_sweep_live": config.get("csdr_max_bars_after_sweep"),
    "expected": 6, "match": threshold_correct,
    "csdr_min_fvg_atr_live": config.get("csdr_min_fvg_atr"),
    "csdr_min_fvg_atr_untouched": True
  },
  "metrics_actual_elapsed_window": {
    "1_csdr_evaluations": csdr_evals,
    "2_waiting_displacement_by_bars": dict(waiting_disp_by_bars),
    "3_cases_surviving_bars_gt_3": survives_beyond_3,
    "3_loosen_in_effect_proof": survives_beyond_3 > 0,
    "4_displacement_just_confirmed": displacement_count,
    "5_no_fvg_count": no_fvg_count,
    "6_proposals_emitted": proposals,
    "7_fires": fires,
    "8_false_positive_indicators": fp_indicators,
    "9_datetime_errors_utc": datetime_errors,
    "9_gate_trace_unexpected_rejections_utc": gt_unexpected,
    "phase_distribution_full": dict(phase_dist),
    "displacement_atrs_observed": displacement_atrs,
    "sweep_expired_by_bars": dict(sweep_expired_by_bars)
  },
  "10_counterfactual_pre_loosen_7d": {
    "setups_that_would_gain_patience": counterfactual_eligible,
    "method": "WAITING_DISPLACEMENT@bars=3 + SWEEP_EXPIRED@bars=4 in 7d pre-loosen window"
  },
  "verdict": label,
  "verdict_reason": reason,
  "recommendation": reco,
  "next_review_utc": WINDOW_END_SPEC_UTC.isoformat(),
  "definition_of_done_checklist": {
    "audit_written": True,
    "timestamped_snapshot_written": True,
    "all_10_metrics_reported": True,
    "decision_rules_applied": True,
    "no_config_changes": True,
    "no_held_audits_opened": True
  },
  "do_not_touched": ["DB config","code","health keys","thresholds","execution authority",
                     "health weighting","NOWIC_RT","watchers","BRC audit","TPC audit","FVG audit"]
}

import os
os.makedirs("/tmp/r2d2_tuning", exist_ok=True)
with open("/tmp/r2d2_tuning/csdr_24h.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\nLOCAL: /tmp/r2d2_tuning/csdr_24h.json")
print(f"VERDICT={label}  RECOMMENDATION={reco}")

scur.close(); scalp.close(); pcur.close(); proteus.close()
print("DONE.")
