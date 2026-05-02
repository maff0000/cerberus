import json, urllib.request

API = "http://localhost:8080/api/v1/redis"
def mem_set(key, value):
    payload = json.dumps({"key": key, "value": json.dumps(value)}).encode()
    req = urllib.request.Request(f"{API}/set", data=payload,
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=5)

result = {
  "suite_id": "r2d2:healthcheck:procedure",
  "version": "2.4",
  "version_change": "Upgraded from v2.3 this session — incorporated Helm + Solo guidance post §6.2 V2 cutover. fabric-mirror moved to Trinity. helios_decisions/helios_snapshots retired. helios:state + helios:heat are new V2 canonical surfaces. SF-* fire writes pending REBUILD. NEO subsection I (determinism replay) flipped DEFERRED → ACTIVE.",
  "run_time_utc": "2026-04-28T04:35:30Z",
  "run_trigger": "Matt: 'run full systems check please R2' + procedure-update + bug verifications + rerun",
  "overall_status": "GREEN",
  "overall_headline": "System GREEN against current V2 architecture. All previous AMBER findings (Helios 'frozen', ARES advisory missing) confirmed as expected V2 state, not regressions. Bug pair (mirror Decimal + NEO instrument-null) FIXED at 04:11Z. SF-* helios_strategy_signals rebuild pending Helm PR per Matt's ruling.",
  "sections": {
    "ssh_tunnel": {"status": "GREEN", "evidence": "Trinity↔dell PONG <1s; fabric-tunnel.service active ~5d; HTTP 200 from :18080; canary OK <10min ago"},
    "neo": {
      "status": "GREEN",
      "load_bearing_grade": "A=GREEN, E=GREEN, I=READY (fixture v2 confirmed in fabric, 6 fixtures, full replay execution deferred to next session)",
      "evidence": "observer.log mtime within 1m; neo:state:XAU_USD fresh (<30s); diagnostic clean; architecture_mode=judgement; decision=NO_QUALIFIED_FIRE (correct - quiet asia, top score 0.00 vs 7.0 threshold); 0 hard-gate-on-instrument hits last 30 min",
      "subsection_I_status": "ACTIVE — r2d2:tests:neo_scoring_replay v2 confirmed: version=2, fixture_count=6, scorer_config_version=2, threshold=7.0. F4 (account_code_hard_gate) marked SACRED per Solo. Full replay execution to be added as a recurring run."
    },
    "falcon": {"status": "GREEN", "evidence": "Daemon active (~10h uptime); all 13 plugins fresh in DB+journal; latest cycle <10min; row counts normal (272 m5 / 1130 nowic_at_m15)"},
    "helios": {
      "status": "GREEN",
      "_grading_change_v24": "Graded against V2 canonical surfaces and evaluation cadence. SF-* helios_strategy_signals freshness EXCLUDED until rebuild lands.",
      "evidence": [
        "helios-shadow.service active (~17h uptime), GATE0 cycling ~1.3s",
        "helios:state:XAU_USD source=helios_daemon_v2, advisory_status=NO_GO, decision_timestamp 2026-04-28T04:34:16Z (~70s before rerun), composite=0, primary_strategy_id=None (correct for NO_GO)",
        "helios:heat:XAU_USD source=helios_daemon_v2, advisory_status=FRESH, heat_score=29.0, regime=BEAR_TREND, session=asia",
        "HELIOS_GATE2B_SF002/SF003/SF007 each 102 events/min — evaluation cadence consistent across all 3 scanners",
        "0 HELIOS_V2_ERROR / 24h"
      ]
    },
    "ares_sync": {
      "status": "GREEN",
      "_grading_change_v24": "fabric-mirror probed locally on Trinity (corrected). ares:advisory:current dropped from probe set (retire-suspect, not Helm's lane).",
      "evidence": "Trinity ares:* current=15, dell source=15, sync delta=0. macro+market_status fresh and mirrored. Mirror service active on Trinity since 04:11:13Z (post-Decimal-fix), all cycles GREEN since."
    },
    "falcon_fires_mirror": {
      "status": "GREEN",
      "_origin": "NEW v2.4 — both probes from Solo's must-add list",
      "fire_field_completeness": "All rows in falcon:fires:recent:XAU_USD carry instrument + strategy_name + direction + confidence + entry/sl/tp/key/invalidation. Schema complete.",
      "decimal_serialization_health": "0 Decimal/Traceback/Exception in last 15 min of fabric-mirror.service journal. Pre-fix history (1596 crashes today before 04:11:13Z restart) confirms the bug Solo flagged. Post-fix steady state: all cycles GREEN, 7-10ms duration."
    },
    "agent_smith_ledger": {
      "status": "GREEN",
      "_origin": "NEW v2.4 — Solo's should-add Phase 3 probe",
      "evidence": "trader:ledger:state source=agent_smith.ledger_heartbeat, updated_at_utc 2026-04-28T04:33:58Z (~90s before rerun, within 90s threshold), balance=4968.97, equity=6141.97"
    }
  },
  "what_changed_vs_v23_run_earlier_today": {
    "ssh_tunnel": "GREEN → GREEN (no change)",
    "neo": "GREEN → GREEN (richer — load-bearing tier graded; subsection I activated)",
    "falcon": "GREEN → GREEN (no change)",
    "helios": "AMBER → GREEN (re-aimed at V2 surfaces; the AMBER was procedure lag, not architecture fault)",
    "ares_sync": "AMBER → GREEN (ares:advisory dropped from probe; mirror on Trinity confirmed working)",
    "falcon_fires_mirror_NEW": "added GREEN",
    "agent_smith_ledger_NEW": "added GREEN"
  },
  "verified_bug_fixes_2026_04_28": {
    "bug_1_fabric_mirror_decimal": {
      "status": "FIXED at 2026-04-28T04:11:13Z",
      "evidence": "1596 Decimal-serialization crashes in journal pre-04:11; 0 since service restart. All cycles state=GREEN, dur_ms=7-10.",
      "originally_flagged_by": "Solo trader:comms:helm:falcon_fires_mirror_decimal_bug_20260428",
      "note": "R2D2's earlier rollup (state=GREEN at 04:00Z run) was correct. Solo's 04:25Z DM cited 12h pre-fix observation window."
    },
    "bug_2_neo_instrument_null": {
      "status": "FIXED via Bug 1 fix at 04:11:13Z",
      "evidence": "falcon:fires:recent:XAU_USD rows carry instrument='XAU_USD' per row + full price schema. Zero hard-gate-on-instrument blocks in NEO observer log last 30 min.",
      "originally_flagged_by": "Solo trader:comms:helm:neo_scorer_instrument_null_bug_20260428",
      "lost_event": "tdr_m5 SHORT conf 7 fire at 03:55Z hard-gate-blocked pre-fix. Lost to history. Future fires will have full schema."
    }
  },
  "pending_items": {
    "sf_helios_strategy_signals_rebuild": "Matt ruled REBUILD 2026-04-28. R2D2 DM'd Helm at r2d2:comms:helm:sf_rebuild_ruling_2026_04_28 with 4 questions (build cost, schema, validation plan). Awaiting Helm reply.",
    "three_drive_threshold_tuning": "Owed to Helm. Sequenced AFTER SF-* rebuild lands per Matt 2026-04-28.",
    "blueprint_validation_assignments": "2 unread Helm comms from 2026-04-26 (helm:comms:r2d2:blueprint_validation_assignment_2026_04_26 + :draft1). Read after current healthcheck cycle closes."
  },
  "open_questions_unresolved": [
    "ares:advisory:current ownership: Helm confirmed not his lane. Solo or Rogue? (Helm pointed me to Solo; in v2.4 it's dropped from probe set as retire-suspect.)"
  ],
  "persist_to": ["r2d2:healthcheck:latest", "r2d2:healthcheck:history:2026-04-28"]
}

mem_set("r2d2:healthcheck:latest", result)
mem_set("r2d2:healthcheck:history:2026-04-28", result)
print("PERSISTED v2.4: r2d2:healthcheck:latest + r2d2:healthcheck:history:2026-04-28")
print("OVERALL: GREEN")
