import json, urllib.request

API = "http://localhost:8080/api/v1/redis"
def mem_get(key):
    resp = urllib.request.urlopen(f"{API}/get/{key}", timeout=5)
    data = json.loads(resp.read())
    return json.loads(data["value"]) if data.get("value") else None
def mem_set(key, value):
    payload = json.dumps({"key": key, "value": json.dumps(value)}).encode()
    req = urllib.request.Request(f"{API}/set", data=payload,
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=5)

old = mem_get("r2d2:healthcheck:procedure")

# Build v2.4 from v2.3 base — preserving structure, applying targeted updates
new = dict(old)
new["version"] = "2.4"
new["updated"] = "2026-04-28"
new["updated_by"] = "R2D2 — incorporated Helm + Solo guidance post §6.2 V2 cutover (helios_decisions retired 04-24, helios_snapshots retired 04-27, fabric-mirror moved to Trinity, helios:state + helios:heat are new V2 canonical surfaces, replay fixture v2 landed)"

# Update scope to reflect V2 surfaces
new["scope"] = [
  "SSH tunnel availability (bidirectional): Trinity→dell-debian command channel + dell-debian→Trinity fabric-tunnel (port 18080). Infra baseline.",
  "NEO observer + judgement-layer suite. Subsection I (determinism replay) now ACTIVE post fixture v2 landing.",
  "Falcon daemon + 13 strategies + signal output (per-strategy fires unchanged from V1)",
  "Helios (helios-shadow) daemon + V2 canonical surfaces (helios:state, helios:heat). Grade evaluation cadence, NOT fire frequency for SF-*.",
  "ARES fabric-sync integrity (Trinity-side fabric-mirror.service, NOT dell-debian)",
  "fabric-mirror service health (Trinity local) — Decimal serialization, falcon_fires schema completeness",
  "Agent Smith ledger heartbeat freshness (Phase 3 shipped 2026-04-27)"
]

# Update environment notes
env = new.setdefault("environment", {})
env["fabric_mirror_location"] = "TRINITY (/srv/fabric-mirror/), systemctl probes use local systemctl, NOT ssh dell. Helm's helm:comms:r2d2:healthcheck_reply_2026_04_28 corrected R2D2's prior assumption."

# REWRITE Helios section — grade evaluation cadence, drop fire-frequency probe for SF-*
new["commands"]["helios"] = {
  "_v24_change": "Per Solo + Helm: helios_strategy_signals SF-* writes pending Matt REBUILD ruling. Until restored, grade evaluation cadence (HELIOS_GATE2B_SF*/cycle) and V2 canonical surfaces (helios:state, helios:heat).",
  "daemon_status": "ssh root@192.168.11.10 'systemctl is-active helios-shadow && systemctl show helios-shadow -p ActiveEnterTimestamp -p ActiveEnterTimestamp --value'",
  "last_cycle_log": "ssh root@192.168.11.10 'journalctl -u helios-shadow.service --since \"5 minutes ago\" --no-pager | grep HELIOS_GATE0 | tail -3'",
  "evaluation_cadence_per_scanner": "ssh root@192.168.11.10 'journalctl -u helios-shadow.service --since \"5 minutes ago\" --no-pager' | grep -oE 'HELIOS_GATE2B_SF00[237]' | sort | uniq -c",
  "v2_canonical_state": {
    "helios_state": "curl -s http://localhost:8080/api/v1/redis/get/helios:state:XAU_USD",
    "expected": "advisory_status not DATA_STALE, source=helios_daemon_v2, age <10s, decision_timestamp advancing every cycle",
    "reject_legacy": "If advisory_status == SETUP_ACTIVE seen, FAIL — V1 bridge would have re-emerged"
  },
  "v2_canonical_heat": {
    "helios_heat": "curl -s http://localhost:8080/api/v1/redis/get/helios:heat:XAU_USD",
    "expected": "advisory_status=FRESH, source=helios_daemon_v2, age <10s, heat_score>0",
    "tolerance": "advisory_status=NO_SIGNAL is transient AMBER, not RED. Pattern dim 0 by design until StructureTracker port lands."
  },
  "fires_persistence_status": "FROZEN PROVISIONAL — helios_strategy_signals SF-* writes paused at V2 cutover. Matt ruled REBUILD 2026-04-28; awaiting Helm sf_rebuild PR. When rebuild lands, restore freshness probe and validate cycle_id round-trip.",
  "error_watch": "CUTOFF=\"$(date -u -d '24 hours ago' +'%Y-%m-%d %H:%M:%S')\"; ssh root@192.168.11.10 \"journalctl -u helios-shadow.service --since '${CUTOFF} UTC' --no-pager\" | grep -c HELIOS_V2_ERROR",
  "healthy_signals": [
    "Daemon Active: active (running)",
    "HELIOS_GATE0 cycle log fresh within 30s",
    "HELIOS_GATE2B_SF002/SF003/SF007 each appearing >=1x per cycle (~1.3s cycle = ~46/min)",
    "helios:state:<instrument> advisory_status fresh + source=helios_daemon_v2 + age <10s",
    "helios:heat:<instrument> advisory_status=FRESH or NO_SIGNAL (transient) + age <10s",
    "Zero HELIOS_V2_ERROR / 24h"
  ],
  "do_NOT_grade_as_fault": [
    "Absence of new SF-* fires (last fires: SF-002 04-23 15:25Z, SF-003 04-17, SF-007 never — no qualifying setups in current market)",
    "helios_strategy_signals SF-* row count unchanged from 04-24 08:00Z baseline (post-cutover, pending rebuild)"
  ]
}

# REWRITE ARES section — drop ares:advisory:current, fabric-mirror is on Trinity
new["commands"]["ares_sync"]["_v24_change"] = "fabric-mirror.service runs on TRINITY (corrected from prior dell-debian assumption). ares:advisory:current dropped from probe set (retire-suspect; on Solo or Rogue's lane per Helm)."
new["commands"]["ares_sync"]["mirror_service_check"] = "systemctl is-active fabric-mirror.service && systemctl show fabric-mirror.service -p ActiveEnterTimestamp --value (RUN ON TRINITY, NOT DELL)"
new["commands"]["ares_sync"]["mirror_decimal_health"] = "journalctl -u fabric-mirror.service --since '15 minutes ago' --no-pager | grep -ciE 'decimal|traceback|exception' (must be 0 — Decimal serialization bug fixed 2026-04-28T04:11Z)"
new["commands"]["ares_sync"]["per_entry_rollups"] = [
  "fabric:mirror:health:ares (state=GREEN, last_cycle_ms<5000, entries_mirrored=15)",
  "fabric:mirror:health:falcon_fires (state=GREEN, entries_mirrored>=1)"
]
new["commands"]["ares_sync"]["dropped"] = ["ares:advisory:current — retire-suspect post §6.2 V2 cutover. Helm not the owner. Pending Solo or Rogue confirmation."]

# NEW SECTION — falcon_fires_mirror (Solo's two mandatory probes)
new["commands"]["falcon_fires_mirror"] = {
  "_origin": "Added 2026-04-28 v2.4 per Solo's two-must-add probes — both surfaced real bugs today (fabric-mirror Decimal crash + NEO instrument-null hard-gate). Catch them during morning healthcheck before market.",
  "fire_field_completeness_per_row": {
    "command": "curl -s http://localhost:8080/api/v1/redis/get/falcon:fires:recent:XAU_USD",
    "validate": "For each row in .rows[]: assert presence and non-null of: instrument, strategy_name, direction, confidence. Assert presence of: entry_price, sl_price, tp1_price, key_level, invalidation_level (allow null only for the still-rolling-out workers per Helm's enabled-strategies manifest).",
    "fault_meaning": "If any required field null: NEO will hard-gate-block qualifying fires. RED grade. Block trading.",
    "_real_incident_2026_04_28": "TDR_M5 SHORT conf 7 fire at 03:55Z hard-gate-blocked because mirror dropped instrument per row. Fixed 04:11Z by manifest patch."
  },
  "mirror_decimal_serialization": {
    "command": "journalctl -u fabric-mirror.service --since '15 minutes ago' --no-pager | grep -ciE 'decimal|traceback|exception'",
    "validate": "Count must be 0. Mirror cycle log must show 'cycle name=falcon_fires state=GREEN' within last 60s.",
    "fault_meaning": "Mirror crashing silently on Decimal (was 1596 crashes pre-fix today). falcon_fires path silently dead while rollup may show stale GREEN.",
    "_real_incident_2026_04_28": "Fix landed 04:11:13Z service restart. R2D2 healthcheck rollup was correct (post-fix), Solo's 04:25Z DM cited 12h-old pre-fix observation."
  }
}

# NEW SECTION — agent_smith_ledger_heartbeat
new["commands"]["agent_smith_ledger"] = {
  "_origin": "Added 2026-04-28 v2.4 per Solo. Phase 3 ledger heartbeat shipped 2026-04-27 to close blind window where Matt's £3,700 deposit took 5h to land in fabric.",
  "ledger_heartbeat_freshness": {
    "command": "curl -s http://localhost:8080/api/v1/redis/get/trader:ledger:state",
    "validate": "updated_at_utc within last 90s, source=agent_smith.ledger_heartbeat, balance/equity not None",
    "fault_meaning": "Heartbeat dead — fabric blind to live broker state. Block live trading."
  }
}

# Update NEO section — load-bearing ranking + flip subsection I to ACTIVE
neo = new["commands"]["neo"]
neo["_v24_change"] = "Subsection I (determinism replay) flipped DEFERRED → ACTIVE (fixture v2 landed 2026-04-22, confirmed by Solo 2026-04-28). Subsection load-bearing ranking added per Solo's live-trader view."
neo["load_bearing_tier"] = {
  "HIGH": {
    "A_observer_liveness": "RED on this = stop trading. Solo reads neo:state and neo:diagnostic every cycle.",
    "E_diagnostic_emission": "Required to debug. RED = blind to why fires get rejected.",
    "I_determinism_signal": "Most load-bearing post-V2-cutover. Drift in scorer = silent edge loss across judgement layer. F4 (account_code_hard_gate) is SACRED — drift breaks Matt's NEO_TRADES_PRACTICE_ONLY rule. Refuse to flip ftmo_execution if F4 drifts."
  },
  "MEDIUM": {
    "B_scorer_config_integrity": "Run on demand and after any neo:config:scorer write.",
    "J_architecture_alignment": "Run weekly or after architecture-touching WO."
  },
  "LOWER_situational": {
    "C_guardrails_completeness": "Run after neo:prop:guardrails:* writes only.",
    "D_prop_state_integrity": "Daily when NEO trades. Currently dormant — no qualifying fires since flip.",
    "F_trade_audit": "Skip when zero trades.",
    "G_execution_pipe": "Pre-flip / pre-trade-day. Keep on daily list while MT5 container in flux.",
    "H_data_flow": "Background sanity. Live-trading flow surfaces failures faster."
  },
  "minimum_coverage_85_percent": "Running A + E + I + pre-flip-B-J catches 85% of what would actually hurt Solo. Rest are scheduled, not continuous."
}
neo["subsection_I_active"] = {
  "fixture_key": "r2d2:tests:neo_scoring_replay",
  "version": 2,
  "fixture_count": 6,
  "scorer_config_version_at_creation": 2,
  "scorer_threshold_at_creation": 7.0,
  "drift_alert_priority": "F4 hardgate_account_code_wrong is SACRED — Discord alert immediately on drift, refuse ftmo_execution flip until restored",
  "fixtures": [
    "F1 strong_long_multi_consensus (TRADE expected, composite=10, sum=7) — full positive",
    "F2 weak_long_below_threshold (TRADE at 7.0 boundary, sum=1) — minimal pass",
    "F3 hardgate_rsi_exhaustion_long (HARD_GATE_BLOCK, blocking=rsi_exhaustion) — gate-stop",
    "F4 hardgate_account_code_wrong (HARD_GATE_BLOCK, blocking=account_code_hard_gate) — SACRED",
    "F5 hardgate_rr_minimum_short (HARD_GATE_BLOCK, blocking=rr_minimum) — R:R floor",
    "F6 entry_cleanliness_chasing_long (TRADE at 7.0 with -2 chase penalty) — modifier interaction"
  ]
}

# Update output_shape to include new sections
new["output_shape"]["per_section"] = "status (GREEN|AMBER|RED), metric, evidence command, observed value, expected value"
new["output_shape"]["sections_required_v24"] = [
  "ssh_tunnel",
  "neo (with load-bearing tier + subsection I active)",
  "falcon",
  "helios (V2 surfaces, evaluation-cadence grading)",
  "ares_sync (mirror on Trinity, ares:advisory dropped)",
  "falcon_fires_mirror (NEW v2.4)",
  "agent_smith_ledger (NEW v2.4)"
]

# Update known_gotchas
new["known_gotchas"] = [
  "openclaw-mariadb backtest user ONLY sees tradingProteus — Falcon operational tables are NOT here; they live at dell-debian:3307",
  "Trinity mariadb root/root is wrong — backtest/bt_eng_2026 is the real creds (cached from /srv/backtesting_engine/.env)",
  "neo:observations:latest key pattern does NOT exist — NEO observations live in in-cycle state only; use neo:state:<instr> and observer.log for liveness",
  "fabric-mirror.service runs on TRINITY (NOT dell). systemctl probes use local systemctl. Health rollups update because the service runs locally.",
  "helios_strategy_signals records ALL 16 strategies (13 Falcon + 3 Helios scanners), but SF-* writes are FROZEN post 2026-04-24 V2 cutover. Pending Matt's REBUILD ruling. Do NOT grade SF-* row absence as fault until rebuild lands.",
  "helios:state:<instrument> + helios:heat:<instrument> are the V2 canonical surfaces — both should age <10s with source=helios_daemon_v2.",
  "helios_decisions table is RETIRED (Matt 2026-04-24). bridge.read_latest_decision is dormant. Do not probe.",
  "helios_snapshots table is RETIRED (Matt 2026-04-27). bridge.read_latest_snapshot returns None unconditionally. Do not probe.",
  "ares:advisory:current is RETIRE-SUSPECT — gone from fabric, not Helm's lane. Pending Solo/Rogue confirmation.",
  "ares:market:status is now mirrored from dell via fabric-mirror — sourced from tradingRisk.trading_calendar (NOT the old market_status_bridge.py, which is retired).",
  "helios-shadow.service IS the canonical Helios scanner daemon. zeusv4.service is DEAD ARCHITECTURE — out of audit scope.",
  "ALWAYS UTC. Never NOW(). Never local. dell-debian MariaDB returns NOW() in BST while timestamps store UTC."
]

# Update dead_architecture_exclusions
new["dead_architecture_exclusions"]["helios_decisions"] = "RETIRED 2026-04-24 by Matt ruling. Out of probe scope."
new["dead_architecture_exclusions"]["helios_snapshots"] = "RETIRED 2026-04-27 by Matt ruling. Out of probe scope."
new["dead_architecture_exclusions"]["ares_advisory_current"] = "RETIRE-SUSPECT 2026-04-28 — not Helm's lane, pending Solo/Rogue confirm. Out of probe scope until proven needed."

# Triggers — note the v2.4 invocation behavior
new["triggers"]["v24_invocation_note"] = "On 'run the healthcheck': run all sections in output_shape.sections_required_v24. Subsection I in NEO is now ACTIVE — invoke replay against r2d2:tests:neo_scoring_replay v2 fixtures. Grade Helios on evaluation cadence + V2 canonical surface freshness, NOT SF-* fire frequency."

mem_set("r2d2:healthcheck:procedure", new)
print("PERSISTED: r2d2:healthcheck:procedure v2.4")
print("  added sections: falcon_fires_mirror, agent_smith_ledger")
print("  rewrote: helios (V2 surfaces), ares_sync (Trinity mirror, ares:advisory dropped), neo (load-bearing tier + I active)")
print("  updated: known_gotchas, dead_architecture_exclusions")
