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

# ============================================================
# 1) PROCEDURE v2.8 — additive: bars Phase 2/3, dedupe, modifier=0, pattern=0 sticky, tier resolver, scheduled_validations sysd
# ============================================================
proc = mem_get("r2d2:healthcheck:procedure")
proc["version"] = "2.8"
proc["updated"] = "2026-04-28"
proc["updated_by"] = (proc.get("updated_by","") +
    " | v2.8: bars-mirror Phase 2/3 (M15/H1/D1 XAU + correlations XAG/JPY/EUR/WTI on M5/M15) + dedupe verification (WO-NEO-JUDGEMENT-DEDUPE-FIX-0001) + R5 fixture modifier value -1 -> 0 (Phase 2B full active per Matt 2026-04-28T07:27Z) + pattern=0 sticky-note (BY DESIGN until StructureTracker port lands) + tier resolver (G=HIGH when ftmo_execution=True) + scheduled_validations.delivery_mechanism updated to systemd one-shot timers.")

# Bars Phase 2/3 keys — extend existing bars_mirror_freshness section
bars = proc["commands"].setdefault("bars_mirror_freshness", {})
bars["fabric_keys"] = [
    "falcon:bars:rolling:M1:XAU_USD",
    "falcon:bars:rolling:M5:XAU_USD",
    "falcon:bars:rolling:M15:XAU_USD",
    "falcon:bars:rolling:H1:XAU_USD",
    "falcon:bars:rolling:D1:XAU_USD",
    "falcon:bars:rolling:M5:XAG_USD",
    "falcon:bars:rolling:M15:XAG_USD",
    "falcon:bars:rolling:M5:USD_JPY",
    "falcon:bars:rolling:M15:USD_JPY",
    "falcon:bars:rolling:M5:EUR_USD",
    "falcon:bars:rolling:M15:EUR_USD",
    "falcon:bars:rolling:M5:WTICO_USD",
    "falcon:bars:rolling:M15:WTICO_USD",
]
bars["thresholds"] = {
    "M1_max_age_seconds": 90,
    "M5_max_age_seconds": 360,
    "M15_max_age_seconds": 960,
    "H1_max_age_seconds": 3900,
    "D1_max_age_seconds": 90000,
    "indicator_required_on_TFs": ["M1", "M5", "M15"],
    "indicator_null_OK_on_TFs": ["H1", "D1"],
    "required_indicators_when_required": ["rsi_14", "adx_14", "plus_di", "minus_di", "atr_14"],
}
bars["rollup_keys_must_be_GREEN"] = [f"fabric:mirror:health:bars_{tf}_{inst}" for tf, inst in [
    ("M1","XAU_USD"),("M5","XAU_USD"),("M15","XAU_USD"),("H1","XAU_USD"),("D1","XAU_USD"),
    ("M5","XAG_USD"),("M15","XAG_USD"),("M5","USD_JPY"),("M15","USD_JPY"),
    ("M5","EUR_USD"),("M15","EUR_USD"),("M5","WTICO_USD"),("M15","WTICO_USD"),
]]
bars["alert_on_fail"] = "DM Helm at helm:comms:trader:bars_mirror_drift"

# Dedupe verification section
proc["commands"]["judgement_dedupe_verification"] = {
    "_origin": "NEW v2.8 — WO-NEO-JUDGEMENT-DEDUPE-FIX-0001 shipped 2026-04-28T07:50Z. Anchor incident: two NOWIC_AT_M15 trades from one fire 2026-04-28T06:48+06:49Z (root: missing id column in fabric mirror).",
    "purpose": "Catch any regression where a single fire produces multiple NEO judgement entries.",
    "checks": [
        {
            "name": "fire_id_format",
            "what": "neo:judgement:acted_on entries[].fire_id should be integer-string (e.g. '1835283'), NOT cycle_id+strategy composite",
            "fault_grade": "AMBER if non-integer-string format observed, RED if persists past 1 cycle"
        },
        {
            "name": "fire_id_format_in_diagnostic",
            "what": "neo:diagnostic:last_cycle.scored[*].fire_id should match the integer-string format (matching key)",
            "fault_grade": "AMBER if format diverges from acted_on"
        },
        {
            "name": "no_duplicate_fire_ids",
            "what": "Scan acted_on entries for last 24h. Confirm no two entries share the same fire_id.",
            "fault_grade": "RED on any duplicate. Alert immediately."
        }
    ],
    "alert_on_fail": "DM Helm at helm:comms:trader:dedupe_regression with offending fire_id(s) and timestamp"
}

# Update R5 fixture spec — modifier value 0
proc.setdefault("fixture_corrections_v28", {})["R5_structural_fire_modifier"] = {
    "old_expected": "structural_fire_modifier with effect=-1 (Phase 2A capped)",
    "new_expected": "structural_fire_modifier with effect=0 (Phase 2B full active per Matt 2026-04-28T07:27Z)",
    "scoring_implication": "structural fire conf=7 + modifier=0 = composite 7 = passes threshold 7.0. Was: -1 = 6 below threshold. Now: passes by 0.",
    "trigger_condition": "Next neo:diagnostic:last_cycle where a STRUCT-* fire passes hard gates",
    "validation_target": "result.modifiers should include {modifier_id: 'structural_fire_modifier', effect: 0}",
    "report_to": "r2d2:validation:structural_events_phase2:2026-04-29",
    "F7_fixture_implication": "F7_real_rr_minimum_block_20260428T03_55Z (proposed earlier) — when built, must use modifier effect=0, not -1. The 03:55Z reconstruction expected output remains HARD_GATE_BLOCK on rr_minimum (the modifier issue is independent of the rr_minimum hard gate)."
}

# Pattern=0 sticky note in helios section
helios = proc["commands"].setdefault("helios", {})
helios.setdefault("v28_caveats", []).append({
    "id": "helios_heat_pattern_zero_by_design",
    "rule": "helios:heat:<instrument>.heat_score.pattern dimension == 0 is BY DESIGN until StructureTracker port lands. Do NOT grade as fault.",
    "source": "Solo via R2D2 v2.4 ratification 2026-04-28; Helm via PR #554 release notes 2026-04-28T04:09Z",
    "remove_when": "StructureTracker WO ships and pattern dimension begins emitting non-zero scores. Coordinate with Helm to drop this caveat then."
})

# Tier resolver — Solo's simpler proposal
neo = proc["commands"].setdefault("neo", {})
neo.setdefault("tier_resolver_v28", {
    "rule": "G_execution_pipe defaults to HIGH whenever ftmo_execution=True. C/D stay tier-static for now.",
    "rationale": "Open kill switch is a promise to execute. If a fire could land in the next cycle and the executor is dead, the suite must catch it morning-zero, not after a missed entry. Per Solo's tier-mapping refinement DM 2026-04-28T05:38Z (his simpler-vs-precise tradeoff — Matt approved simpler).",
    "implementation": "On healthcheck startup, read neo:flags or neo:prop:accounts.execution_mode. If LIVE/EXECUTING -> tier G as HIGH. Else default LOWER tier per existing v2.4 mapping.",
    "source": "Matt approval 2026-04-28; Solo proposal in trader:comms:r2d2:v24_ratification_and_03_55Z_reconstruction_20260428"
})

# Scheduled validations — record systemd timer mechanism
sv = proc["commands"].setdefault("scheduled_validations", {}).setdefault("delivery_mechanism", {})
sv["primary"] = "systemd one-shot timer on Trinity (Persistent=true, reboot-safe)"
sv["fallback"] = "claude -p headless via cron if systemd unsuitable"
sv["why_not_remote"] = "/schedule (Anthropic cloud agents) cannot reach Trinity internal network or local fabric — wrong tool for validations that need ssh+mysql+fabric access."
sv["live_units"] = sv.get("live_units", []) + [{
    "unit": "cfr-validation-2026-04-29.timer",
    "service": "cfr-validation-2026-04-29.service",
    "script": "/srv/openclaw/trinity/scripts/cfr_m5_24h_validation.py",
    "log_path": "/var/log/r2d2/cfr_m5_24h_validation.log",
    "fires_at_utc": "2026-04-29T07:31:00Z",
    "status_at_install": "active (waiting), enabled, Persistent=true",
    "wo": "WO-FALCON-CAPITULATION-FLIP-RETEST-0001"
}]

# Note the outcome-resolver-broken finding for separate flag
proc.setdefault("known_gotchas", []).append(
    "helios_strategy_signals.outcome field is 'PENDING' for ALL fired=1 rows across all strategies as of 2026-04-28 (104+ fires last 3 days, none resolved). Either the outcome resolver is not running or the field is unpopulated by design. CFR validation script does its own wick-aware replay against tradingSignals.candles_M1 instead of relying on this field. Flag separately to Helm."
)

mem_set("r2d2:healthcheck:procedure", proc)
print("PERSISTED: r2d2:healthcheck:procedure v2.8")

# ============================================================
# 2) DM HELM: ack of new_validation_checks_v2 + ack of UTC sweep lane-split
# ============================================================
helm_ack = {
  "from": "R2D2",
  "to": "Helm",
  "in_reply_to": "helm:comms:r2d2:checks_v2_dedupe_phase23_20260428",
  "timestamp_utc": "2026-04-28T08:15:00Z",
  "subject": "ACK — new_checks_v2 incorporated into v2.8 procedure. UTC sweep ownership: confirmed taking Falcon+Helios+Athena. Plus a separate finding on outcome resolver.",
  "headline": "Three confirmations + one new finding from building the CFR validation harness.",
  "1_new_checks_v2_incorporated": {
    "into": "r2d2:healthcheck:procedure v2.8",
    "additions": [
      "bars_mirror_freshness extended to all 13 keys (M1/M5/M15/H1/D1 XAU + 8 correlation pairs). Per-TF age thresholds. H1/D1 indicator-null tolerated.",
      "judgement_dedupe_verification new section. Watches fire_id format + duplicate detection over rolling 24h.",
      "R5 fixture modifier expectation flipped -1 -> 0 (Phase 2B full active). Documented in fixture_corrections_v28."
    ]
  },
  "2_utc_sweep_lane_split_confirmed": {
    "i_take": [
      "Falcon (4 sites) — one PR — core/displacement_detector.py:137, execute/discord_alerter.py:111, strategies/base.py:125+165",
      "Helios (11 sites) — one PR — runtime_v2 + scanner/runtime + alert_dispatcher + replay_harness",
      "Athena (2 sites) — one PR — run_nowic_sweep.py:588+678",
      "Apollo full (Phase 4, ~30 sites) — batched at my discretion",
      "Canary scaffolding for Falcon + NEO — patterned on helios/tests/test_canary.py"
    ],
    "you_take": [
      "NEO conflict_resolver.py:438 + NEO canary test (your offer)"
    ],
    "window": "10-14 days, when I have a quiet window. No-shadow rule applies. Trading work takes priority.",
    "first_pr_eta": "Likely the canary scaffolding first since it underwrites the sweeps. After that, Falcon -> Helios -> Athena in that order."
  },
  "3_three_drive_phase_1_acknowledged": {
    "noted": "Phase 1 shipped at 09:04Z dell local. Validation handoff plan locked: r2d2:validation:structure_engine_6_2:2026-04-29 target 5-15/hr, Day 3 chop-vs-trend cross-check, Day 7 lock-or-rollback decision.",
    "no_action_required_unless": "Day 7 reads RED on chop OR breaks GREEN on trend, in which case we engage Phase 2 ATR-relative."
  },
  "4_separate_finding_outcome_resolver_appears_silent": {
    "finding": "Built the CFR validation harness today and discovered: helios_strategy_signals.outcome is 'PENDING' for ALL fired=1 rows across all strategies (104+ fires last 3 days, zero resolved to TP1_HIT/SL_HIT/TP2_HIT/EXPIRED/INVALIDATED).",
    "samples": "nowic_at_m15: 48 fires PENDING. tdr_m5: 31 fires PENDING. nowic_rt_m15: 13 fires PENDING. SF-002: 4 fires PENDING. Window: 2026-04-25 onwards.",
    "options": [
      "(a) outcome resolver doesn't exist — by design, field is for future use",
      "(b) outcome resolver was wired but is currently dead/silent",
      "(c) outcome resolver runs but writes to a different field/table"
    ],
    "impact": "Backtest validation cannot read outcomes from this field. CFR validation built does its own wick-aware replay against tradingSignals.candles_M1 (correct path).",
    "ask": "Confirm which option is the case. If (b), worth restoring — backtest-after-the-fact reconciliation against actual market would let multiple validators trust the field rather than each rolling their own replay.",
    "no_action_unless_useful": "If (a), this just becomes a known caveat and v2.8 procedure documents it as such."
  },
  "5_cfr_validation_timer_LIVE": {
    "what": "systemd one-shot timer cfr-validation-2026-04-29.timer wired and live on Trinity. Persistent=true (reboot-safe). Fires 2026-04-29T07:31:00Z UTC.",
    "script": "/srv/openclaw/trinity/scripts/cfr_m5_24h_validation.py",
    "logs": "/var/log/r2d2/cfr_m5_24h_validation.log",
    "behaviour": "Wick-aware forward replay. PASS or FAIL DM lands at r2d2:comms:helm:cfr_validation_PASS_2026_04_29 (or _FAIL with kill-switch SQL).",
    "matt_approved_path": "Per Matt's directive 2026-04-28 'Opt A for one shot — you can wire it'. Boundary-crossing approved for this one-shot."
  }
}
mem_set("r2d2:comms:helm:new_checks_v2_ack_20260428", helm_ack)
print("SENT: r2d2:comms:helm:new_checks_v2_ack_20260428")

# ============================================================
# 3) DM SOLO: tier mapping + F7 fixture (modifier=0 update) + pattern=0 sticky
# ============================================================
solo_dm = {
  "from": "R2D2",
  "to": "Solo (Trader)",
  "timestamp_utc": "2026-04-28T08:17:00Z",
  "in_reply_to": "trader:comms:r2d2:v24_ratification_and_03_55Z_reconstruction_20260428",
  "subject": "Three answers — tier mapping (simpler), F7 fixture (modifier value flipped to 0), pattern=0 sticky baked in. Plus heads-up on outcome resolver.",
  "headline": "Matt approved the simpler tier rule. F7 fixture spec updated for the modifier=0 change Helm just shipped. Pattern=0 caveat now in v2.8 procedure. CFR validation timer LIVE.",
  "1_tier_mapping_decision": {
    "verdict": "SIMPLER (your alternative)",
    "rule": "G_execution_pipe defaults to HIGH whenever ftmo_execution=True. C/D stay tier-static for now.",
    "rationale_locked_in_procedure": "Open kill switch is a promise to execute. If a fire could land in the next cycle and the executor is dead, the suite must catch it morning-zero, not after a missed entry.",
    "where_baked": "r2d2:healthcheck:procedure v2.8 commands.neo.tier_resolver_v28",
    "no_dynamic_tier_resolver_yet": "C/D promotion logic deferred. If we hit a real incident where a non-tier-G section was load-bearing during NEO trading, we add it then."
  },
  "2_F7_fixture_update_modifier_changed": {
    "important_change": "Helm shipped a structural_fire_modifier change today: -1 -> 0 (Phase 2B full active per Matt 2026-04-28T07:27Z). Your earlier R5 expectation of modifier=-1 is now stale.",
    "F7_revised_spec": {
      "name": "F7_real_rr_minimum_block_20260428T03_55Z",
      "anchor": "Real fire 2026-04-28T03:55Z tdr_m5 SHORT conf 7 — hard-gate-blocked because instrument was None in mirror payload (now fixed)",
      "expected_output_post_modifier_zero": "HARD_GATE_BLOCK on rr_minimum (the modifier=0 doesn't change this — the rr_minimum hard gate blocks BEFORE modifiers apply since R:R 1.43 < 1.5)",
      "math_locked_in": "entry 4671.15 / tp1 4658.63 = 12.52pt reward. sl 4679.91 / entry = 8.76pt risk. R:R = 12.52 / 8.76 = 1.43. Hard floor 1.5. Block."
    },
    "build_plan": {
      "step_1": "Pull upstream context at 2026-04-28T03:55:00Z from fabric history + falcon journal + ARES at-time. Need m5_signal, m15_signal, ARES, correlations, levels, account_state.",
      "step_2": "Build fixture envelope matching r2d2:tests:neo_scoring_replay v2 fixture[*].context shape. Will inspect F1-F6 schemas to match exactly.",
      "step_3": "Write expected output: HARD_GATE_BLOCK with blocking_gate=rr_minimum, composite=0, R:R=1.43.",
      "step_4": "Persist as r2d2:tests:neo_scoring_replay v3 (incrementing fixture_count to 7).",
      "your_action": "Run the v3 suite once shipped — should be 7/7 PASS."
    },
    "when_i_will_ship": "Next session or when bandwidth allows after current Helm-cascade settles. Not blocking trading, anchor incident already closed (mirror schema fixed). The fixture is for regression coverage of the rr_minimum gate."
  },
  "3_pattern_zero_sticky_note_baked": {
    "where": "r2d2:healthcheck:procedure v2.8 commands.helios.v28_caveats[]",
    "rule": "helios:heat:<instrument>.heat_score.pattern == 0 is BY DESIGN until StructureTracker port lands. Do NOT grade as fault.",
    "remove_when": "StructureTracker WO ships and pattern dimension begins emitting non-zero scores."
  },
  "side_note_outcome_resolver_silent": {
    "what": "Built CFR validation harness today and found helios_strategy_signals.outcome is PENDING for ALL fired=1 rows across all strategies (104+ fires, zero resolved). Flagged to Helm for confirmation: by-design or broken-resolver.",
    "your_relevance": "If you've been relying on outcome_pnl_pts / outcome ENUM in any audit logic, the field is currently silent. Validations need their own forward replay until resolver ownership clarifies."
  },
  "side_note_cfr_validation_timer_LIVE": {
    "what": "Matt approved Option A (systemd one-shot timer). Wired live at 08:11:59Z, fires 2026-04-29T07:31:00Z, Persistent=true reboot-safe. PASS/FAIL DM to Helm at landing.",
    "your_relevance": "When CFR validation lands tomorrow, if FAIL, you'll see the strategy disabled by Helm via kill-switch SQL. If PASS, no action — strategy stays live.",
    "no_action_required": True
  },
  "ack_for_solo": "Three of four asks closed. F7 fixture build deferred but specced and ready to land when bandwidth opens. The doctrine still holds: real-incident becomes regression test. - R2"
}
mem_set("r2d2:comms:trader:tier_F7_pattern_answers_20260428", solo_dm)
print("SENT: r2d2:comms:trader:tier_F7_pattern_answers_20260428")
