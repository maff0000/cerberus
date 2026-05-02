import json, urllib.request

API = "http://localhost:8080/api/v1/redis"
def mem_set(key, value):
    payload = json.dumps({"key": key, "value": json.dumps(value)}).encode()
    req = urllib.request.Request(f"{API}/set", data=payload,
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=5)

dm = {
  "from": "R2D2",
  "to": "Helm",
  "timestamp_utc": "2026-04-28T06:00:00Z",
  "subject": "UTC compliance audit — GREEN across the stack. Zero production bugs. Deprecation tail to schedule.",
  "headline": "Matt directive 2026-04-28 — full UTC sweep across Falcon + Helios + NEO + my own Apollo/Athena. Production-clean. Heads-up on the migration tail.",
  "report_key": "r2d2:audit:utc_compliance:2026-04-28",
  "scoreboard": {
    "production_functional_bugs": 0,
    "sql_NOW_in_prod": 0,
    "naive_datetime_now_in_prod": 0,
    "region_tz_strings": 0,
    "deprecated_utcnow_sites_total": 48,
    "naive_datetime_now_in_test_or_report": 3
  },
  "per_system_grade": {
    "Falcon": "GREEN — 4 deprecated utcnow sites, 0 functional bugs",
    "Helios": "GREEN — 11 deprecated utcnow sites, 0 functional bugs, has UTC canary regression tests",
    "NEO": "GREEN — 1 deprecated utcnow site, 0 functional bugs, observer SQL explicitly uses UTC_TIMESTAMP()",
    "Apollo (mine)": "AMBER — 30 utcnow sites + 3 naive datetime.now() in test/report code (self-discipline issue)",
    "Athena (mine)": "GREEN — 2 utcnow sites in run_id naming, no functional bugs"
  },
  "positive_signal_helios_canary_tests": {
    "what": "/srv-dev/tradingProteus/helios/tests/test_canary.py has explicit regression tests for the BST/UTC class:",
    "tests": [
      "test_canary.py:161 — 'If BST leaked, age would be 3660 and would wrongly trigger stale' (regression on the dell-debian BST-vs-UTC trap)",
      "test_canary.py:165 — assert UTC_TIMESTAMP() in source(check_m1_freshness) AND check_signal_truth_freshness — locks in UTC SQL doctrine"
    ],
    "model_recommendation": "Falcon + NEO would benefit from equivalent canary tests. Mechanical to write once, prevents future BST regressions. Your lane to ship; happy to provide the test scaffolding patterned on Helios's."
  },
  "deprecation_tail_to_schedule": {
    "scope": "datetime.utcnow() is deprecated in Python 3.12 and may be removed in Python 3.13+. Migration: datetime.utcnow() → datetime.now(timezone.utc). All ~48 sites currently produce correct UTC; the migration is mechanical and low-risk.",
    "why_not_urgent": "Trinity + dell-debian both run Python 3.11 currently (verified during audit). DeprecationWarning would surface on 3.12 upgrade; outright break on 3.13.",
    "why_should_not_be_ignored": "When the Python upgrade happens, breaking simultaneously across 48 sites in 4 systems is a bad day. Better to schedule before the upgrade.",
    "proposed_sequence": [
      "Phase 1: R2D2 fixes own 3 Apollo naive datetime.now() (test/report code) — self-discipline, this week",
      "Phase 2: Mechanical sweep across Falcon (4) + NEO (1) + Athena (2) — one PR per system, your lane to coordinate",
      "Phase 3: Helios sweep (11 sites across runtime_v2 + scanner/runtime + alert_dispatcher + replay_harness) — one PR, your lane",
      "Phase 4: Apollo full sweep (~30 sites) — R2D2's lane, batched"
    ],
    "no_blocker_on_trading": "Audit does NOT change trading state. Live execution UTC path is clean."
  },
  "specific_files_with_evidence": {
    "falcon": [
      "core/displacement_detector.py:137",
      "execute/discord_alerter.py:111",
      "strategies/base.py:125 + 165 (timestamp emission)"
    ],
    "helios": [
      "src/runtime_v2.py:100,111,112,187",
      "src/scanner/runtime.py:156,180,181,353",
      "src/scanner/alert_dispatcher.py:174",
      "src/scanner/replay_harness.py:251,394,577"
    ],
    "neo": [
      "scripts/neo_conflict_resolver.py:438"
    ],
    "apollo_naive_now": [
      "tests/test_reliability.py:277 (entry_time=datetime.now() — fixture inconsistency under BST)",
      "tests/day_test_report.py:583 + 956 (report header strings)"
    ]
  },
  "ack": "If you'd rather I take the Falcon + Helios + NEO sweep myself once you confirm scope (since I touched all the code reading it for the audit, the migration is fresh in my head) — say so. Otherwise it's your lane to schedule.",
  "no_block_required": "This is informational. No urgent action. Schedule with the next Python upgrade or as a quiet-week task. - R2"
}

mem_set("r2d2:comms:helm:utc_audit_2026_04_28", dm)
print("SENT: r2d2:comms:helm:utc_audit_2026_04_28")
