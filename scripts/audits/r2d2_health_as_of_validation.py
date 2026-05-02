"""WO-R2D2-HEALTH-AS-OF-WRITER-FIX-VALIDATION-0001
READ-ONLY. Anchor: created_at > 2026-05-01T14:12:19Z (NOT cycle_ts/timestamp).
UTC: architect-stamped restart anchor + DB created_at + DB timestamps. Fail-loud on missing tz.
"""
import json, datetime, pymysql, sys
from collections import Counter, defaultdict

PR_621_SHA = "786ce3ca17cf970a42e9d61c5e994af9776b4808"
RESTART_UTC = datetime.datetime(2026, 5, 1, 14, 12, 19, tzinfo=datetime.timezone.utc)
VERIFY_PASS_UTC = datetime.datetime(2026, 5, 1, 14, 14, 34, tzinfo=datetime.timezone.utc)
RESTART_SQL = RESTART_UTC.strftime("%Y-%m-%d %H:%M:%S")
VERIFY_SQL = VERIFY_PASS_UTC.strftime("%Y-%m-%d %H:%M:%S")

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

scur.execute("SELECT MAX(created_at) AS now FROM helios_strategy_signals")
CANONICAL_NOW = scur.fetchone()["now"].replace(tzinfo=datetime.timezone.utc)
NOW_SQL = CANONICAL_NOW.strftime("%Y-%m-%d %H:%M:%S")
HOURS_SINCE_RESTART = (CANONICAL_NOW - RESTART_UTC).total_seconds() / 3600

print(f"CANONICAL_NOW (created_at MAX): {CANONICAL_NOW.isoformat()}")
print(f"RESTART:                       {RESTART_UTC.isoformat()}")
print(f"VERIFY_PASS:                   {VERIFY_PASS_UTC.isoformat()}")
print(f"PR #621 SHA:                   {PR_621_SHA}")
print(f"hours since restart:           {HOURS_SINCE_RESTART:.2f}")

AFFECTED = ["nowic_at_m15", "tdr_m5", "nowic_rt_m15", "whipsaw_fade_m5"]

# ============================================================
# TASK 2 + 3 + 4: post-restart rows for affected strategies
#                 (anchored by created_at, NOT timestamp/cycle_ts)
# ============================================================
print("\n[2-4] Per-strategy post-restart row analysis (anchored by created_at)")
per_strategy = {}
for sid in AFFECTED:
    scur.execute(f"""
        SELECT
          COUNT(*) total,
          SUM(CASE WHEN fired=1 THEN 1 ELSE 0 END) fires,
          SUM(CASE WHEN fired=0 THEN 1 ELSE 0 END) declines,
          SUM(CASE WHEN health_as_of IS NULL THEN 1 ELSE 0 END) hao_null,
          SUM(CASE WHEN health_as_of IS NOT NULL THEN 1 ELSE 0 END) hao_non_null,
          SUM(CASE WHEN fired=1 AND health_as_of IS NOT NULL THEN 1 ELSE 0 END) fire_hao_non_null,
          SUM(CASE WHEN fired=1 AND health_as_of IS NULL THEN 1 ELSE 0 END) fire_hao_null,
          MIN(created_at) earliest_write,
          MAX(created_at) latest_write
        FROM helios_strategy_signals
        WHERE strategy_id='{sid}' AND created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}'
    """)
    r = dict(scur.fetchone())
    for k in ("total","fires","declines","hao_null","hao_non_null","fire_hao_non_null","fire_hao_null"):
        r[k] = int(r[k] or 0)
    per_strategy[sid] = r
    print(f"\n  {sid}:")
    print(f"    total post-restart rows: {r['total']}")
    print(f"    fires: {r['fires']}  declines: {r['declines']}")
    print(f"    health_as_of NULL: {r['hao_null']}  non-NULL: {r['hao_non_null']}")
    print(f"    fires with non-NULL health_as_of: {r['fire_hao_non_null']}")
    print(f"    earliest write: {r['earliest_write']}  latest: {r['latest_write']}")

    # Sample non-NULL health_as_of values to prove DATETIME format is valid
    if r["hao_non_null"] > 0:
        scur.execute(f"""
            SELECT id, fired, created_at, timestamp, health_as_of, health_status, health_source
            FROM helios_strategy_signals
            WHERE strategy_id='{sid}' AND created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}'
              AND health_as_of IS NOT NULL
            ORDER BY created_at DESC LIMIT 3
        """)
        samples = [dict(s) for s in scur.fetchall()]
        per_strategy[sid]["non_null_samples"] = [
            {k:str(v) for k,v in s.items()} for s in samples]
        print(f"    non-NULL samples (post-fix proof):")
        for s in samples:
            print(f"      id={s['id']} fired={s['fired']} hao={s['health_as_of']} "
                  f"hstatus={s['health_status']} hsource={s['health_source']}")
    if r["fires"] > 0:
        scur.execute(f"""
            SELECT id, created_at, timestamp, health_as_of, health_status, health_source, reason_codes
            FROM helios_strategy_signals
            WHERE strategy_id='{sid}' AND created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}'
              AND fired=1 ORDER BY created_at ASC LIMIT 5
        """)
        fires = [dict(s) for s in scur.fetchall()]
        per_strategy[sid]["fire_samples"] = [
            {k:str(v) for k,v in s.items()} for s in fires]
        print(f"    fire samples:")
        for s in fires:
            print(f"      id={s['id']} hao={s['health_as_of']} hstatus={s['health_status']} "
                  f"reason={s['reason_codes'][:80]}")

# ============================================================
# TASK 7: Confirm no rows lost — count expected vs actual
# Expected: each strategy should have ~one row per cycle since restart
# tdr_m5/whipsaw/cfr/coil/etc are M5 (cycle every 5 min)
# nowic_at_m15/nowic_rt_m15 are M15 (cycle every 15 min)
# ============================================================
print("\n[7] Row-loss check — expected vs actual cycle counts post-restart")
elapsed_min = (CANONICAL_NOW - RESTART_UTC).total_seconds() / 60
expected = {
    "tdr_m5": int(elapsed_min // 5),
    "whipsaw_fade_m5": int(elapsed_min // 5),
    "nowic_at_m15": int(elapsed_min // 15),
    "nowic_rt_m15": int(elapsed_min // 15),
}
loss_table = {}
for sid in AFFECTED:
    actual = per_strategy[sid]["total"]
    exp = expected.get(sid, 0)
    delta = actual - exp
    loss_table[sid] = {"expected_approx": exp, "actual": actual, "delta": delta,
                       "loss_suspected": delta < 0}
    flag = "LOSS" if delta < -1 else ("OK" if abs(delta) <= 1 else "SURPLUS")
    print(f"  {sid:<22s} expected~{exp:>4d}  actual={actual:>4d}  delta={delta:>+4d}  {flag}")

# ============================================================
# TASK 5: For NULL health_as_of rows, examine adjacent fields to determine cause
# ============================================================
print("\n[5] Why is health_as_of NULL where it is NULL? (sample analysis)")
null_cause_analysis = {}
for sid in AFFECTED:
    if per_strategy[sid]["hao_null"] == 0:
        continue
    scur.execute(f"""
        SELECT id, fired, health_as_of, health_status, health_source, reason_codes
        FROM helios_strategy_signals
        WHERE strategy_id='{sid}' AND created_at >= '{RESTART_SQL}' AND created_at <= '{NOW_SQL}'
          AND health_as_of IS NULL ORDER BY created_at ASC LIMIT 5
    """)
    rows = [dict(s) for s in scur.fetchall()]
    pattern = {
        "all_health_status_null": all(r["health_status"] is None for r in rows),
        "all_health_source_null": all(r["health_source"] is None for r in rows),
        "any_health_present": any(r["health_status"] or r["health_source"] for r in rows),
        "samples": [{k:str(v) for k,v in r.items()} for r in rows]
    }
    null_cause_analysis[sid] = pattern
    print(f"\n  {sid} NULL-cause sample (n={len(rows)}):")
    print(f"    all health_status NULL: {pattern['all_health_status_null']}")
    print(f"    all health_source NULL: {pattern['all_health_source_null']}")
    for r in rows[:3]:
        print(f"      id={r['id']} hao={r['health_as_of']} hs={r['health_status']} hsrc={r['health_source']}")

# ============================================================
# TASK 6: Compare against pre-fix failure class
# What was failing pre-restart and is it the same class now?
# ============================================================
print("\n[6] Pre-fix failure class characterization")
PRE_RESTART_WINDOW_START = (RESTART_UTC - datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
scur.execute(f"""
    SELECT strategy_id, COUNT(*) total,
           SUM(CASE WHEN fired=1 THEN 1 ELSE 0 END) fires,
           SUM(CASE WHEN health_as_of IS NULL THEN 1 ELSE 0 END) hao_null,
           SUM(CASE WHEN health_as_of IS NOT NULL THEN 1 ELSE 0 END) hao_non_null
    FROM helios_strategy_signals
    WHERE strategy_id IN ('tdr_m5','nowic_at_m15','nowic_rt_m15','whipsaw_fade_m5')
      AND created_at >= '{PRE_RESTART_WINDOW_START}' AND created_at < '{RESTART_SQL}'
    GROUP BY strategy_id ORDER BY strategy_id
""")
pre_fix = [dict(r) for r in scur.fetchall()]
for r in pre_fix:
    for k in ("total","fires","hao_null","hao_non_null"):
        r[k] = int(r[k] or 0)
print(f"  Pre-restart 2h window ({PRE_RESTART_WINDOW_START} -> {RESTART_SQL}):")
for r in pre_fix:
    print(f"    {r['strategy_id']:<22s} total={r['total']} fires={r['fires']} "
          f"hao_null={r['hao_null']} hao_non_null={r['hao_non_null']}")

# ============================================================
# Save report
# ============================================================
report = {
  "wo": "WO-R2D2-HEALTH-AS-OF-WRITER-FIX-VALIDATION-0001",
  "executed_by": "R2D2",
  "anchors": {
    "canonical_now_utc": CANONICAL_NOW.isoformat(),
    "restart_utc": RESTART_UTC.isoformat(),
    "verify_pass_utc": VERIFY_PASS_UTC.isoformat(),
    "pr_621_sha": PR_621_SHA,
    "hours_since_restart": round(HOURS_SINCE_RESTART, 2),
    "anchor_rule": "created_at > restart_utc (NOT timestamp/cycle_ts)"
  },
  "ut_discipline": "READ-ONLY. Architect-stamped restart anchor + DB created_at. No NOW()/utcnow()/time.time().",
  "task_2_3_4_per_strategy": per_strategy,
  "task_5_null_cause_analysis": null_cause_analysis,
  "task_6_pre_fix_class": pre_fix,
  "task_7_row_loss_check": loss_table,
}

import os
os.makedirs("/tmp/r2d2_tuning", exist_ok=True)
with open("/tmp/r2d2_tuning/health_as_of.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\nLOCAL: /tmp/r2d2_tuning/health_as_of.json")

scur.close(); scalp.close()
print("DONE.")
