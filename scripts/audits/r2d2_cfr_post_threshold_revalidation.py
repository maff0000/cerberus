"""WO-R2D2-CFR-POST-THRESHOLD-REVALIDATION-0001
READ-ONLY. UTC: cycle_ts canonical + architect-stamped restart anchor + git commit ts.
No NOW()/utcnow()/time.time(). Missing time fails loud.
"""
import json, datetime, pymysql, urllib.request, sys
from collections import Counter

# ============================================================
# Architect-stamped anchors (canonical, tz-aware, fail loud)
# ============================================================
PR_616_MERGE_SHA = "910c19470eb5ceb66aadf906dba64e29411eb4dd"
RESTART_UTC = datetime.datetime(2026, 5, 1, 10, 47, 36, tzinfo=datetime.timezone.utc)
VERIFY_PASS_UTC = datetime.datetime(2026, 5, 1, 10, 47, 48, tzinfo=datetime.timezone.utc)
RESTART_SQL = RESTART_UTC.strftime("%Y-%m-%d %H:%M:%S")

if RESTART_UTC.tzinfo is None:
    print("FAIL_LOUD: restart anchor missing tz", file=sys.stderr); sys.exit(2)

# Load DB creds (read-only)
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

# Canonical now via cycle_ts MAX (no NOW())
scur.execute("SELECT MAX(cycle_ts) AS now FROM helios_v3_decisions")
CANONICAL_NOW = scur.fetchone()["now"].replace(tzinfo=datetime.timezone.utc)
NOW_SQL = CANONICAL_NOW.strftime("%Y-%m-%d %H:%M:%S")
WINDOW_90D_START = CANONICAL_NOW - datetime.timedelta(days=90)
W90_SQL = WINDOW_90D_START.strftime("%Y-%m-%d %H:%M:%S")
PRE_FIX_END = RESTART_UTC.strftime("%Y-%m-%d %H:%M:%S")
HOURS_SINCE_RESTART = (CANONICAL_NOW - RESTART_UTC).total_seconds() / 3600

print(f"CANONICAL_NOW (cycle_ts MAX): {CANONICAL_NOW.isoformat()}")
print(f"RESTART anchor:               {RESTART_UTC.isoformat()}")
print(f"VERIFY_PASS:                  {VERIFY_PASS_UTC.isoformat()}")
print(f"PR #616 SHA:                  {PR_616_MERGE_SHA}")
print(f"hours since restart:          {HOURS_SINCE_RESTART:.2f}")
print(f"90d window:                   {W90_SQL}  -->  {NOW_SQL}")

# ============================================================
# TASK 1: Confirm live CFR threshold = 600
# ============================================================
print("\n[1] Live CFR threshold confirmation")
pcur.execute("""
    SELECT * FROM falcon_strategy_capitulation_flip_retest_config
    WHERE config_key='cfr_hermes_stale_threshold_seconds'
      AND instrument='XAU_USD' AND mode='NORMAL'
""")
threshold_row = pcur.fetchone()
print(f"  row: {threshold_row}")
if not threshold_row:
    print("FAIL_LOUD: threshold row missing"); sys.exit(2)
live_threshold = threshold_row.get("config_value") or threshold_row.get("value")
# Try to coerce
try:
    live_threshold_int = int(float(str(live_threshold)))
except Exception:
    live_threshold_int = None
print(f"  live_threshold (raw): {live_threshold!r}")
print(f"  live_threshold (int): {live_threshold_int}")
threshold_correct = (live_threshold_int == 600)

# ============================================================
# TASK 2: No unrelated CFR config changed
# ============================================================
print("\n[2] Full CFR config snapshot")
pcur.execute("""
    SELECT config_key, instrument, mode, config_value, updated_at
    FROM falcon_strategy_capitulation_flip_retest_config
    ORDER BY config_key, instrument, mode
""")
cfr_full_config = [dict(r) for r in pcur.fetchall()]
recently_changed = []
for r in cfr_full_config:
    ua = r.get("updated_at")
    if ua and ua.replace(tzinfo=datetime.timezone.utc) >= RESTART_UTC - datetime.timedelta(hours=24):
        recently_changed.append({
            "key": r["config_key"], "instr": r["instrument"], "mode": r["mode"],
            "value": str(r["config_value"]), "updated": str(ua)
        })
print(f"  total CFR config rows: {len(cfr_full_config)}")
print(f"  rows updated within 24h before restart: {len(recently_changed)}")
for r in recently_changed:
    print(f"    {r}")

# ============================================================
# TASK 3: Post-restart HERMES_STALE rate (if any, signal_age >600?)
# ============================================================
print("\n[3] Post-restart HERMES_STALE analysis")
scur.execute(f"""
    SELECT COUNT(*) AS n,
           AVG(CAST(JSON_EXTRACT(evidence, '$.signal_age') AS DECIMAL(10,2))) avg_age,
           MIN(CAST(JSON_EXTRACT(evidence, '$.signal_age') AS DECIMAL(10,2))) min_age,
           MAX(CAST(JSON_EXTRACT(evidence, '$.signal_age') AS DECIMAL(10,2))) max_age
    FROM helios_strategy_signals
    WHERE strategy_id='cfr_m5'
      AND timestamp >= '{RESTART_SQL}' AND timestamp <= '{NOW_SQL}'
      AND fired=0 AND reason_codes LIKE '%HERMES_STALE%'
""")
post_stale = scur.fetchone()
print(f"  post-restart HERMES_STALE: count={post_stale['n']} avg={post_stale['avg_age']} "
      f"min={post_stale['min_age']} max={post_stale['max_age']}")

# Of any post-restart stale, are they legitimately >600?
scur.execute(f"""
    SELECT id, timestamp, evidence
    FROM helios_strategy_signals
    WHERE strategy_id='cfr_m5'
      AND timestamp >= '{RESTART_SQL}' AND timestamp <= '{NOW_SQL}'
      AND fired=0 AND reason_codes LIKE '%HERMES_STALE%'
      AND CAST(JSON_EXTRACT(evidence, '$.signal_age') AS DECIMAL(10,2)) <= 600
    LIMIT 10
""")
post_stale_below_600 = [dict(r) for r in scur.fetchall()]
print(f"  post-restart HERMES_STALE with age<=600 (illegitimate): {len(post_stale_below_600)}")

# ============================================================
# TASK 4: 90d counterfactual re-confirm (independent of HELM)
# ============================================================
print("\n[4] 90d counterfactual re-confirm")
scur.execute(f"""
    SELECT
      COUNT(*) total_stale_pre,
      SUM(CASE WHEN CAST(JSON_EXTRACT(evidence, '$.signal_age') AS DECIMAL(10,2)) < 600 THEN 1 ELSE 0 END) would_pass_at_600,
      SUM(CASE WHEN CAST(JSON_EXTRACT(evidence, '$.signal_age') AS DECIMAL(10,2)) >= 600 THEN 1 ELSE 0 END) would_still_stale_at_600,
      MAX(CAST(JSON_EXTRACT(evidence, '$.signal_age') AS DECIMAL(10,2))) max_age_observed
    FROM helios_strategy_signals
    WHERE strategy_id='cfr_m5'
      AND timestamp >= '{W90_SQL}' AND timestamp < '{PRE_FIX_END}'
      AND fired=0 AND reason_codes LIKE '%HERMES_STALE%'
""")
counterfactual = dict(scur.fetchone())
print(f"  pre-fix stale rejections (90d): {counterfactual['total_stale_pre']}")
print(f"  would pass at 600s threshold: {counterfactual['would_pass_at_600']}")
print(f"  would remain stale at 600s:   {counterfactual['would_still_stale_at_600']}")
print(f"  max age observed:             {counterfactual['max_age_observed']}")
counterfactual_ok = (counterfactual['would_still_stale_at_600'] == 0 and
                     int(counterfactual['would_pass_at_600']) == int(counterfactual['total_stale_pre']))

# ============================================================
# TASK 5: Post-restart decline categorisation (what is CFR doing now?)
# ============================================================
print("\n[5] Post-restart CFR decision distribution")
scur.execute(f"""
    SELECT fired, reason_codes, COUNT(*) c
    FROM helios_strategy_signals
    WHERE strategy_id='cfr_m5'
      AND timestamp >= '{RESTART_SQL}' AND timestamp <= '{NOW_SQL}'
    GROUP BY fired, reason_codes
    ORDER BY c DESC
""")
post_distribution = [dict(r) for r in scur.fetchall()]
total_post = sum(int(r['c']) for r in post_distribution)
post_fires = sum(int(r['c']) for r in post_distribution if r['fired']==1)

# Bucket by category
buckets = Counter()
for r in post_distribution:
    rc = (r['reason_codes'] or '').upper()
    c = int(r['c'])
    if r['fired'] == 1:
        buckets["PROPOSAL/FIRED"] += c
    elif "HERMES_STALE" in rc:
        buckets["HERMES_STALE"] += c
    elif "NO_CASCADE" in rc:
        buckets["NO_CASCADE"] += c
    elif "NO_RETEST" in rc:
        buckets["NO_RETEST"] += c
    elif "NO_CONFIRMATION" in rc or "AWAITING_CONFIRMATION" in rc:
        buckets["NO_CONFIRMATION"] += c
    elif "SESSION_BLOCKED" in rc:
        buckets["SESSION_BLOCKED"] += c
    elif "REGIME" in rc or "INVALID_REGIME" in rc:
        buckets["REGIME_BLOCKED"] += c
    elif "GUARDRAIL" in rc:
        buckets["GUARDRAIL"] += c
    else:
        buckets["OTHER"] += c

print(f"  total post-restart evals: {total_post}")
print(f"  post-restart fires:       {post_fires}")
print(f"  bucket breakdown:")
for k, v in buckets.most_common():
    pct = 100.0*v/total_post if total_post else 0.0
    print(f"    {k:<22s} {v:>6d}  ({pct:.1f}%)")

print(f"\n  raw top 10 reason_codes post-restart:")
for r in post_distribution[:10]:
    print(f"    fired={r['fired']} c={r['c']:>5d}  {(r['reason_codes'] or '')[:90]}")

# ============================================================
# TASK 6: Pre-fix vs post-fix decline distribution
# ============================================================
print("\n[6] Pre-fix (90d) vs post-fix decline distribution")
scur.execute(f"""
    SELECT fired, reason_codes, COUNT(*) c
    FROM helios_strategy_signals
    WHERE strategy_id='cfr_m5'
      AND timestamp >= '{W90_SQL}' AND timestamp < '{PRE_FIX_END}'
    GROUP BY fired, reason_codes
    ORDER BY c DESC LIMIT 30
""")
pre_distribution = [dict(r) for r in scur.fetchall()]
total_pre = sum(int(r['c']) for r in pre_distribution)
pre_buckets = Counter()
for r in pre_distribution:
    rc = (r['reason_codes'] or '').upper(); c = int(r['c'])
    if r['fired'] == 1: pre_buckets["PROPOSAL/FIRED"] += c
    elif "HERMES_STALE" in rc: pre_buckets["HERMES_STALE"] += c
    elif "NO_CASCADE" in rc: pre_buckets["NO_CASCADE"] += c
    elif "NO_RETEST" in rc: pre_buckets["NO_RETEST"] += c
    elif "NO_CONFIRMATION" in rc or "AWAITING_CONFIRMATION" in rc: pre_buckets["NO_CONFIRMATION"] += c
    elif "SESSION_BLOCKED" in rc: pre_buckets["SESSION_BLOCKED"] += c
    elif "REGIME" in rc: pre_buckets["REGIME_BLOCKED"] += c
    elif "GUARDRAIL" in rc: pre_buckets["GUARDRAIL"] += c
    else: pre_buckets["OTHER"] += c

print(f"  PRE-FIX total: {total_pre} | POST-FIX total: {total_post}")
all_keys = set(pre_buckets) | set(buckets)
print(f"  {'Bucket':<22s} {'PRE_n':>8s} {'PRE_%':>7s} {'POST_n':>8s} {'POST_%':>7s}")
for k in sorted(all_keys, key=lambda x: -(pre_buckets.get(x,0)+buckets.get(x,0))):
    pn = pre_buckets.get(k,0); ppc = 100.0*pn/total_pre if total_pre else 0.0
    qn = buckets.get(k,0); qpc = 100.0*qn/total_post if total_post else 0.0
    print(f"  {k:<22s} {pn:>8d} {ppc:>6.1f}% {qn:>8d} {qpc:>6.1f}%")

# ============================================================
# TASK 7: Peer M5 stale rate comparison
# ============================================================
print("\n[7] Peer M5 stale rate (post-restart window)")
peers = ["cfr_m5", "sweep_fvg_m5", "crf_m5", "whipsaw_fade_m5",
         "coil_breakout_m5", "fdr_m5", "tdr_m5", "brc_m5"]
peer_stale = {}
for p in peers:
    scur.execute(f"""
        SELECT
          COUNT(*) total,
          SUM(CASE WHEN fired=0 AND reason_codes LIKE '%HERMES_STALE%' THEN 1 ELSE 0 END) stale,
          SUM(CASE WHEN fired=1 THEN 1 ELSE 0 END) fires
        FROM helios_strategy_signals
        WHERE strategy_id='{p}'
          AND timestamp >= '{RESTART_SQL}' AND timestamp <= '{NOW_SQL}'
    """)
    r = dict(scur.fetchone())
    total = int(r['total'] or 0); stale = int(r['stale'] or 0); fires = int(r['fires'] or 0)
    rate = 100.0*stale/total if total else None
    peer_stale[p] = {"total": total, "stale": stale, "fires": fires,
                     "stale_rate_pct": rate}
    print(f"  {p:<22s} evals={total:>5d} stale={stale:>3d} ({rate if rate is not None else 'N/A'}%) fires={fires}")

# ============================================================
# TASK 8: Classify CFR post-fix
# ============================================================
print("\n[8] Classification")
cfr = peer_stale["cfr_m5"]
post_stale_count = int(post_stale['n'] or 0)

# Decision rules
classification = None
rationale = []

if post_stale_below_600:
    classification = "CFR_DATA_DEFECT_REMAINS"
    rationale.append(f"{len(post_stale_below_600)} post-restart HERMES_STALE rows have signal_age<=600 (threshold should reject these)")
elif not threshold_correct:
    classification = "CFR_STILL_STALE"
    rationale.append(f"live threshold not 600 (got {live_threshold_int})")
elif cfr["total"] == 0:
    classification = "INCONCLUSIVE_PENDING_SAMPLE"
    rationale.append("zero post-restart evaluations — too few hours since restart")
elif post_stale_count > 0 and (cfr["stale_rate_pct"] or 0) > 5:
    classification = "CFR_STILL_STALE"
    rationale.append(f"post-fix stale rate still elevated ({cfr['stale_rate_pct']:.1f}%)")
elif buckets["NO_CASCADE"]/total_post > 0.7 if total_post else False:
    classification = "CFR_OVER_CONSTRAINED_AFTER_STALE_FIX"
    rationale.append(f"NO_CASCADE dominates ({buckets['NO_CASCADE']}/{total_post} = "
                     f"{100*buckets['NO_CASCADE']/total_post:.1f}%) — next guard is rejecting almost everything")
elif post_fires > 0:
    classification = "CFR_RESTORED_TO_COHORT"
    rationale.append(f"CFR producing {post_fires} fire(s) post-restart — back in cohort")
elif post_stale_count == 0 and total_post > 0:
    # No stale, but no fires either — reaching real strategy guards
    other_decline_pct = 100.0 - (buckets["HERMES_STALE"]/total_post*100 if total_post else 0)
    # Check NO_CASCADE pct
    nc_pct = (buckets["NO_CASCADE"]/total_post*100) if total_post else 0
    if nc_pct > 50:
        classification = "CFR_OVER_CONSTRAINED_AFTER_STALE_FIX"
        rationale.append(f"freshness fixed; cascade guard now dominant ({nc_pct:.1f}%)")
    else:
        classification = "INCONCLUSIVE_PENDING_SAMPLE"
        rationale.append(f"freshness fixed; sample too small to label cascade rate ({total_post} evals, {HOURS_SINCE_RESTART:.1f}h)")
else:
    classification = "INCONCLUSIVE_PENDING_SAMPLE"
    rationale.append("decision rules ambiguous")

print(f"  CLASSIFICATION: {classification}")
for r in rationale:
    print(f"    - {r}")

# ============================================================
# TASK 9: Recommendation
# ============================================================
print("\n[9] Recommendation")
if classification == "CFR_RESTORED_TO_COHORT":
    recommendation = "leave active and observe for 24-72h to gather full session coverage"
elif classification == "CFR_OVER_CONSTRAINED_AFTER_STALE_FIX":
    recommendation = "backtest CFR cascade guard logic — freshness fixed but next gate is the choke point"
elif classification == "CFR_STILL_STALE":
    recommendation = "investigate — threshold change may not have taken effect or HERMES delivery degraded"
elif classification == "CFR_DATA_DEFECT_REMAINS":
    recommendation = "investigate evidence/signal_age extraction — illegitimate stale rejects observed"
elif classification == "INCONCLUSIVE_PENDING_SAMPLE":
    recommendation = "re-evaluate after 24-72h — current sample insufficient"
else:
    recommendation = "consult architect"
print(f"  {recommendation}")

# ============================================================
# Save full report
# ============================================================
report = {
  "wo": "WO-R2D2-CFR-POST-THRESHOLD-REVALIDATION-0001",
  "wo_status": "CLOSED",
  "executed_by": "R2D2",
  "anchors": {
    "canonical_now_utc": CANONICAL_NOW.isoformat(),
    "restart_utc": RESTART_UTC.isoformat(),
    "verify_pass_utc": VERIFY_PASS_UTC.isoformat(),
    "pr_616_merge_sha": PR_616_MERGE_SHA,
    "hours_since_restart": round(HOURS_SINCE_RESTART, 2),
    "window_90d_pre_fix": [W90_SQL, PRE_FIX_END]
  },
  "ut_discipline": "READ-ONLY. cycle_ts canonical. Architect-stamped restart anchor. No NOW()/utcnow()/time.time(). Fail-loud on missing tz.",
  "task_1_threshold_confirmation": {
    "row": {k: str(v) for k,v in threshold_row.items()} if threshold_row else None,
    "live_threshold_int": live_threshold_int,
    "expected": 600,
    "match": threshold_correct
  },
  "task_2_full_cfr_config": {
    "total_rows": len(cfr_full_config),
    "rows_updated_24h_pre_restart": recently_changed,
    "all_config_keys": sorted(set(r["config_key"] for r in cfr_full_config))
  },
  "task_3_post_restart_stale": {
    "count": post_stale_count,
    "avg_age_s": str(post_stale['avg_age']) if post_stale['avg_age'] else None,
    "min_age_s": str(post_stale['min_age']) if post_stale['min_age'] else None,
    "max_age_s": str(post_stale['max_age']) if post_stale['max_age'] else None,
    "illegitimate_below_600": len(post_stale_below_600),
    "samples_below_600": post_stale_below_600
  },
  "task_4_counterfactual_reconfirm": {
    "pre_fix_stale_total_90d": int(counterfactual['total_stale_pre']),
    "would_pass_at_600": int(counterfactual['would_pass_at_600']),
    "would_remain_stale_at_600": int(counterfactual['would_still_stale_at_600']),
    "max_age_observed_s": str(counterfactual['max_age_observed']),
    "matches_helm_625": int(counterfactual['total_stale_pre']) == 625,
    "all_pass_at_600": counterfactual_ok
  },
  "task_5_post_restart_distribution": {
    "total_evaluations": total_post,
    "fires": post_fires,
    "buckets": dict(buckets),
    "top_reason_codes": [{"fired": r['fired'], "count": int(r['c']),
                          "reason_codes": (r['reason_codes'] or '')[:120]}
                         for r in post_distribution[:10]]
  },
  "task_6_pre_vs_post_distribution": {
    "pre_total": total_pre, "post_total": total_post,
    "pre_buckets": dict(pre_buckets), "post_buckets": dict(buckets)
  },
  "task_7_peer_comparison": peer_stale,
  "task_8_classification": classification,
  "task_8_rationale": rationale,
  "task_9_recommendation": recommendation,
  "do_not_touched": ["DB config", "code", "health keys", "thresholds",
                     "execution authority", "health weighting", "NOWIC_RT", "watchers"],
  "precursor_audit": "r2d2:audit:cfr_hermes_stale_investigation:latest"
}

import os
os.makedirs("/tmp/r2d2_tuning", exist_ok=True)
with open("/tmp/r2d2_tuning/cfr_post_threshold.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\nLOCAL: /tmp/r2d2_tuning/cfr_post_threshold.json")

scur.close(); scalp.close(); pcur.close(); proteus.close()
print("DONE.")
