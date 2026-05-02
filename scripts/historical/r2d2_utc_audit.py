import json, urllib.request

API = "http://localhost:8080/api/v1/redis"
def mem_set(key, value):
    payload = json.dumps({"key": key, "value": json.dumps(value)}).encode()
    req = urllib.request.Request(f"{API}/set", data=payload,
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=5)

audit = {
  "audit_id": "utc_compliance_2026_04_28",
  "version": "1.0",
  "run_time_utc": "2026-04-28T05:55:00Z",
  "trigger": "Matt 2026-04-28: 'run test on strategy code to make sure only UTC timestamps used... extend to NEO Falcon and Helios'",
  "scope": ["Falcon strategies + util", "Helios scanner V1+V2 + canary tests", "NEO scripts", "Apollo V4 (R2D2 self-audit)", "Athena (R2D2 self-audit)"],
  "audit_patterns": [
    "SQL NOW() / INTERVAL with NOW()",
    "datetime.utcnow() (deprecated Python 3.12+)",
    "naive datetime.now() (no timezone arg)",
    "datetime.now(timezone.X) where X != utc",
    "region-specific TZ strings (BST/Europe/London/EST/PST/etc)",
    "time.localtime / time.mktime / time.timezone",
    "shell: date -d without -u",
    "shell: journalctl --since 'X ago' (uses local time)"
  ],
  "headline": "ZERO production functional UTC bugs found. ZERO NOW() in production SQL. ZERO naive datetime.now() in production code. ZERO region TZ strings. ~50 sites use deprecated datetime.utcnow() (functionally returns UTC, but Python 3.13+ may remove). Helios has explicit canary regression tests for the BST class — model for Falcon and NEO to adopt.",
  "overall_grade": "GREEN with deprecation tail",
  "findings_by_system": {
    "falcon": {
      "grade": "GREEN",
      "production_bugs": 0,
      "deprecated_utcnow_sites": [
        {"file": "/srv-dev/falcon/core/displacement_detector.py", "line": 137, "code": "detected_at=datetime.utcnow()", "severity": "LOW (deprecated, functional)"},
        {"file": "/srv-dev/falcon/execute/discord_alerter.py", "line": 111, "code": "datetime.utcnow() - timedelta(minutes=30)", "severity": "LOW"},
        {"file": "/srv-dev/falcon/strategies/base.py", "line": 125, "code": "datetime.utcnow().isoformat() + 'Z'", "severity": "LOW"},
        {"file": "/srv-dev/falcon/strategies/base.py", "line": 165, "code": "datetime.utcnow().isoformat() + 'Z'", "severity": "LOW"}
      ],
      "sql_now_in_prod": 0,
      "naive_datetime_now": 0,
      "region_tz_strings": 0,
      "note": "All 4 utcnow sites correctly produce UTC. base.py emits ISO+Z which is UTC-canonical. Migration to datetime.now(timezone.utc) is mechanical and low-risk."
    },
    "helios": {
      "grade": "GREEN",
      "production_bugs": 0,
      "deprecated_utcnow_sites": [
        {"file": "/srv-dev/tradingProteus/helios/src/runtime_v2.py", "lines": [100, 111, 112, 187], "context": "candle_age + current_utc + timestamp fallback", "severity": "LOW"},
        {"file": "/srv-dev/tradingProteus/helios/src/scanner/runtime.py", "lines": [156, 180, 181, 353], "context": "candle_age + current_utc", "severity": "LOW"},
        {"file": "/srv-dev/tradingProteus/helios/src/scanner/alert_dispatcher.py", "lines": [174], "context": "cooldown cutoff", "severity": "LOW"},
        {"file": "/srv-dev/tradingProteus/helios/src/scanner/replay_harness.py", "lines": [251, 394, 577], "context": "replay_start/end timestamps", "severity": "LOW"}
      ],
      "sql_now_in_prod": 0,
      "naive_datetime_now": 0,
      "region_tz_strings": 0,
      "positive_signal": "tests/test_canary.py:165 explicitly regress-tests that production SQL uses UTC_TIMESTAMP() not NOW(). tests/test_canary.py:161 has BST-leak regression coverage. THIS IS THE MODEL — Falcon and NEO should add equivalent canary tests."
    },
    "neo": {
      "grade": "GREEN",
      "production_bugs": 0,
      "deprecated_utcnow_sites": [
        {"file": "/srv/NEO/scripts/neo_conflict_resolver.py", "line": 438, "code": "(datetime.utcnow() - row['latest']).days", "severity": "LOW"}
      ],
      "sql_clean_explicit": [
        {"file": "/srv/NEO/scripts/neo_observer.py", "line": 293, "code": "WHERE timestamp >= UTC_TIMESTAMP() - INTERVAL %s MINUTE", "verdict": "CLEAN — explicitly uses UTC_TIMESTAMP, not NOW"},
        {"file": "/srv/NEO/scripts/neo_auditor.py", "line": 152, "code": "AND timestamp <= %s + INTERVAL %s MINUTE", "verdict": "CLEAN — uses parameterized %s for the timestamp (passed as close_time UTC value), no NOW"}
      ],
      "naive_datetime_now": 0,
      "region_tz_strings": 0
    },
    "apollo_v4_self_audit": {
      "grade": "AMBER (R2D2's own house)",
      "deprecated_utcnow_sites": "~30 across engine.py, models.py, audit/, regression/, tools/, scalp_sweep.py, diagnostic_reporter.py, orb_regression.py, preflight.py — all functionally produce UTC, but deprecated",
      "naive_datetime_now_sites": [
        {"file": "/srv-dev/tradingProteus/apollov4/tests/test_reliability.py", "line": 277, "code": "entry_time=datetime.now()", "severity": "MEDIUM — test fixture uses naive now(), would produce inconsistent results in BST"},
        {"file": "/srv-dev/tradingProteus/apollov4/tests/day_test_report.py", "line": 583, "code": "datetime.now().strftime('%Y-%m-%d')", "severity": "LOW — report-header date string, not load-bearing for backtest correctness"},
        {"file": "/srv-dev/tradingProteus/apollov4/tests/day_test_report.py", "line": 956, "code": "datetime.now().strftime('%Y-%m-%d %H:%M:%S')", "severity": "LOW — report-header timestamp string"}
      ],
      "self_audit_lesson": "Per identity:depth 2026-04-23: audit yourself before you audit others. Found 3 naive datetime.now() in my own Apollo test/report code. 0 in production engine path. Will fix on next Apollo touch."
    },
    "athena_self_audit": {
      "grade": "GREEN",
      "deprecated_utcnow_sites": [
        {"file": "/srv-dev/tradingProteus/athena/run_nowic_sweep.py", "lines": [588, 678], "code": "datetime.utcnow().strftime('%Y%m%d%H%M%S')", "severity": "LOW — used in sweep tmpdir + run_id naming"}
      ],
      "production_bugs": 0
    }
  },
  "summary_table": {
    "system": ["Falcon", "Helios", "NEO", "Apollo (R2D2)", "Athena (R2D2)"],
    "production_functional_bugs": [0, 0, 0, 0, 0],
    "deprecated_utcnow_sites": [4, 11, 1, 30, 2],
    "naive_datetime_now_in_tests": [0, 0, 0, 3, 0],
    "sql_NOW_in_prod": [0, 0, 0, 0, 0],
    "region_tz_strings": [0, 0, 0, 0, 0],
    "grade": ["GREEN", "GREEN", "GREEN", "AMBER (test code)", "GREEN"]
  },
  "what_did_NOT_break": [
    "No NOW() in production SQL — every cross-system query uses UTC_TIMESTAMP() or parameterized UTC strings",
    "No naive datetime.now() in production code path — every now() call is either utcnow() (deprecated but UTC) or now(timezone.utc) (correct)",
    "No region-specific TZ strings (BST, Europe/London, etc) anywhere",
    "No time.localtime / time.mktime / time.timezone usage",
    "Helios canary tests explicitly regress against the BST/UTC class — proven defense"
  ],
  "what_could_break_in_future": [
    "Python 3.12 emits DeprecationWarning on datetime.utcnow() — log noise",
    "Python 3.13+ may REMOVE datetime.utcnow() — would break ~50 sites across the stack at once",
    "Apollo test_reliability.py:277 entry_time=datetime.now() naive — when run in BST timezone, would produce off-by-1h fixture values inconsistent with UTC engine output"
  ],
  "recommendations": {
    "P1_now": [
      "R2D2 fixes own 3 naive datetime.now() in Apollo tests/reports (self-discipline first)",
      "Add canary-style UTC regression test to Falcon (model after helios/tests/test_canary.py:test_utc_timestamp_used_in_query) — Helm's lane to ship",
      "Add equivalent canary to NEO scripts — Helm's lane to ship"
    ],
    "P2_planned": [
      "Sweep migration: datetime.utcnow() → datetime.now(timezone.utc) across Falcon (4 sites), Helios (11 sites), NEO (1 site), Apollo (30 sites), Athena (2 sites). Mechanical change, low-risk. Coordinate with Helm to schedule when no live work is mid-flight."
    ],
    "P3_optional": [
      "Add a CI lint rule: grep -rE 'datetime\\.utcnow|datetime\\.now\\(\\)$' --include='*.py' ; fail build on hit. Forces forward-only compliance for new code."
    ]
  },
  "no_block_on_trading": "Audit findings do not change trading state. Live execution path uses correct UTC throughout. The deprecation tail is a future-Python-version risk, not a current trading risk.",
  "persist_to": "r2d2:audit:utc_compliance:2026-04-28"
}

mem_set("r2d2:audit:utc_compliance:2026-04-28", audit)
print("PERSISTED: r2d2:audit:utc_compliance:2026-04-28")
print("OVERALL: GREEN with deprecation tail. Zero production bugs.")
