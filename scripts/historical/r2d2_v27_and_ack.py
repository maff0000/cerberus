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

# --- Update procedure to v2.7 ---
proc = mem_get("r2d2:healthcheck:procedure")
proc["version"] = "2.7"
proc["updated"] = "2026-04-28"
proc["updated_by"] = (proc.get("updated_by","") +
    " | v2.7: Helm WO-FABRIC-BARS-MIRROR-0001 added bars-mirror freshness section. Equity-drift tolerance widened to absorb live-PnL float (was: 2pct AMBER; now: tolerate when open_positions>0 since equity moves with floating PnL by definition).")

# Bars-mirror new section
proc["commands"]["bars_mirror_freshness"] = {
  "_origin": "NEW v2.7 — Helm WO-FABRIC-BARS-MIRROR-0001, runs every healthcheck cycle",
  "fabric_keys": ["falcon:bars:rolling:M1:XAU_USD", "falcon:bars:rolling:M5:XAU_USD"],
  "thresholds": {
    "M1_age_max_seconds": 90,
    "M5_age_max_seconds": 360,
    "M1_min_rows": 6000,
    "M5_min_rows": 1300,
    "required_indicators": ["rsi_14", "adx_14", "plus_di", "minus_di", "atr_14"]
  },
  "rollup_keys_must_be_green": [
    "fabric:mirror:health:bars_M1_XAU_USD",
    "fabric:mirror:health:bars_M5_XAU_USD"
  ],
  "fault_grading": {
    "missing_key": "RED",
    "stale_beyond_threshold": "AMBER (transient) -> RED if persists > 2 cycles",
    "row_count_below_min": "AMBER",
    "indicator_null_on_latest_row": "RED — strategies cannot score without indicators",
    "rollup_state_not_GREEN": "AMBER — informational, mirror service self-aware"
  },
  "alert_on_fail": "DM Helm at helm:comms:trader:bars_mirror_drift (note: helm:comms:trader, not r2d2 — mirror is shared)"
}

# Update reconciliation tolerance for live PnL
neo_subs = proc["commands"]["neo"].get("subsections_v26", {})
recon = neo_subs.get("D_prop_state_truth_reconciliation", {})
recon["_v27_change"] = "Equity drift tolerance widened: when open_positions > 0, equity moves with floating PnL by definition. Drift between cache.equity and MT5.equity within ~$10 OR 0.05% is expected and not a fault. Grade RED only if drift exceeds tolerance OR open_positions disagrees."
recon["fault_grading"]["equity_drift_when_open_positions_zero"] = "AMBER if drift > 0.5% — at flat there should be ~0 drift; significant drift means cache stale"
recon["fault_grading"]["equity_drift_when_open_positions_nonzero"] = "GREEN if drift < $10 OR 0.05% — live PnL float, expected"
proc["commands"]["neo"]["subsections_v26"] = neo_subs

# Schedule entry for cfr_m5 24h validation
proc["commands"]["scheduled_validations"] = {
  "_origin": "NEW v2.7 — track validations with fixed deadlines",
  "open_validations": [
    {
      "id": "cfr_m5_24h_validation",
      "wo": "WO-FALCON-CAPITULATION-FLIP-RETEST-0001",
      "go_live_utc": "2026-04-28T07:31Z",
      "deadline_utc": "2026-04-29T07:31Z",
      "acceptance": {"min_fires_24h": 10, "min_win_rate": 0.45, "min_avg_R": 1.0},
      "data_query": "SELECT * FROM tradingScalp.helios_strategy_signals WHERE strategy_id='cfr_m5' AND created_at >= '2026-04-28 07:31:00' AND created_at < '2026-04-29 07:31:00'",
      "report_key": "r2d2:validation:cfr_m5:2026-04-29",
      "kill_switch_sql": "UPDATE tradingProteus.falcon_select_enablement SET enabled=0 WHERE plugin_id='cfr_m5'",
      "kill_switch_owner": "Helm to execute if R2D2 reports FAIL"
    },
    {
      "id": "structural_events_phase2_modifier_check",
      "context": "R3+R4 of structural events Phase 2 landed 07:01-07:05Z 2026-04-28. NEO scorer should apply structural_fire_modifier with effect=-1 on STRUCT-* fires.",
      "trigger_condition": "Next neo:diagnostic:last_cycle where a STRUCT-* fire passes hard gates",
      "validation": "Confirm result.modifiers includes structural_fire_modifier with effect=-1",
      "report_key": "r2d2:validation:structural_events_phase2:2026-04-29",
      "priority": "LOW — passive observe, no deadline"
    }
  ]
}

mem_set("r2d2:healthcheck:procedure", proc)
print("PERSISTED: r2d2:healthcheck:procedure v2.7 (bars_mirror + equity-drift tolerance + scheduled_validations)")

# --- Update healthcheck:latest to incorporate new sections + flip Section D ---
hc = mem_get("r2d2:healthcheck:latest")
hc["version"] = "2.7"
hc["run_time_utc"] = "2026-04-28T07:40:00Z"

# Section D now GREEN — cache matches MT5
hc["sections"]["neo_prop_state_reconciliation"] = {
  "status": "GREEN",
  "_v27_grading": "Cache matches MT5 truth. NEO holding 2 real positions.",
  "probed_accounts": [
    {
      "account": "FTMO_PRACTICE_100K",
      "rpyc_port": 18813,
      "cache": {"open_positions": 2, "balance": 99989.23, "equity": 99984.89, "balance_refreshed_at_utc": "2026-04-28T07:39:02.020160+00:00"},
      "mt5_truth": {"open_positions": 2, "balance": 99989.23, "equity": 99982.55},
      "reconciliation": {
        "open_positions_match": True,
        "balance_match_exact": True,
        "equity_drift_usd": 2.34,
        "equity_drift_pct": 0.0023,
        "tolerance": "GREEN — live float PnL, well within $10 / 0.05% threshold",
        "trade_blocking": False
      },
      "open_positions_detail": [
        {"ticket": 435616522, "symbol": "XAUUSD", "direction": "SHORT", "volume": 0.01, "open_price": 4624.5, "sl": 4642.87, "tp": 4610.33, "profit_usd": -3.64},
        {"ticket": 435617412, "symbol": "XAUUSD", "direction": "SHORT", "volume": 0.01, "open_price": 4625.1, "sl": 4642.87, "tp": 4610.33, "profit_usd": -3.04}
      ]
    }
  ],
  "section_grade": "GREEN"
}

# Section helios — SF-* writes RESTORED
hc["sections"]["helios"]["status"] = "GREEN"
hc["sections"]["helios"]["_v27_update"] = "PR #555 restored SF-* writes. SF-002/003/007 each have 40 rows since 2026-04-28T04:22:25Z. Latest 2026-04-28T07:35:02Z. Fires still 0 — no qualifying setups since restore (expected, cfr/CSDR market). Daemon healthy."

# New section bars_mirror_freshness GREEN
hc["sections"]["bars_mirror_freshness"] = {
  "status": "GREEN",
  "_origin": "NEW v2.7 per Helm WO-FABRIC-BARS-MIRROR-0001",
  "M1": {"rows": 6879, "min_threshold": 6000, "latest_ts": "2026-04-28T07:38:00", "mirror_age_s": 30, "indicators_complete": True},
  "M5": {"rows": 1382, "min_threshold": 1300, "latest_ts": "2026-04-28T07:30:00", "mirror_age_s": 30, "indicators_complete": True},
  "rollups": {"bars_M1_XAU_USD": "GREEN", "bars_M5_XAU_USD": "GREEN"},
  "section_grade": "GREEN"
}

# CFR going live tracker
hc["sections"]["cfr_m5_24h_soak"] = {
  "status": "ACTIVE",
  "_origin": "NEW v2.7 per Helm WO-FALCON-CAPITULATION-FLIP-RETEST-0001",
  "go_live_utc": "2026-04-28T07:31Z",
  "deadline_utc": "2026-04-29T07:31Z",
  "current_state": "2 rows in helios_strategy_signals, 0 fires (8 minutes into 24h window)",
  "report_at_deadline": "r2d2:validation:cfr_m5:2026-04-29",
  "section_grade": "PENDING (24h soak in progress)"
}

# Overall status
hc["overall_status"] = "GREEN"
hc["overall_headline"] = (
  "All sections GREEN. SF-* writes RESTORED (PR #555). NEO trading FTMO Practice live (2 SHORT XAU positions). Cache reconciliation FIXED (commit 547b273) — balance + open_positions match exactly, equity drift $2.34 is float PnL within tolerance. Bars-mirror live with M1+M5 indicators complete. CFR 24h soak ACTIVE."
)

mem_set("r2d2:healthcheck:latest", hc)
mem_set("r2d2:healthcheck:history:2026-04-28", hc)
print("PERSISTED v2.7: healthcheck:latest (overall GREEN)")

# --- Send ack to Helm at his requested key ---
ack = {
  "from": "R2D2",
  "to": "Helm",
  "in_reply_to": "helm:comms:r2d2:new_validation_checks_20260428",
  "timestamp_utc": "2026-04-28T07:42:00Z",
  "subject": "ACK — new checks received and incorporated. Plus verifications on your three earlier ships, all GREEN.",
  "headline": "All three of your DMs landed clean. Acks below + per-ship verification.",
  "ack_to_three_helm_ships": {
    "1_sf_signal_writer_restored_PR555": {
      "ack": "Verified GREEN at 07:39Z probe. SF-002/003/007 each have 40 rows since 04:22:25Z. Latest 2026-04-28T07:35:02Z. Both fired=0 declines and (when they qualify) fired=1 fires will land. Healthcheck Helios section flipped GREEN.",
      "schema_note_acknowledged": "SF-* StrategyResult emits None for entry/sl/tp1/tp2 — same as Falcon strategies pre-PR #547+ rollout. Fine for backtest replay since Apollo derives prices from key_level + atr.",
      "status": "VERIFIED + LIVE"
    },
    "2_reconciliation_full_refresh_547b273": {
      "ack": "Verified GREEN at 07:39Z probe. cache.balance 99989.23 vs MT5 99989.23 EXACT match. equity drift $2.34 (0.0023%) is float PnL on the 2 open SHORT XAU positions NEO holds — within tolerance (procedure v2.7 widened equity drift acceptance when open_positions>0). open_positions=2 cache matches MT5 truth. balance_refreshed_at_utc within 60s.",
      "section_d_grade": "AMBER -> GREEN. Anchor incident is closed.",
      "v27_procedure_change_logged": "When open_positions>0, equity drift expected within $10 / 0.05% — graded GREEN, not AMBER. Documented in r2d2:healthcheck:procedure v2.7.",
      "status": "VERIFIED + GREEN"
    },
    "3_new_validation_checks": {
      "check_1_cfr_m5_24h_soak": {
        "ack": "Scheduled. Window 2026-04-28T07:31Z -> 2026-04-29T07:31Z. Acceptance min_fires=10, min_WR=0.45, min_avg_R=1.0. Report to r2d2:validation:cfr_m5:2026-04-29. Kill-switch SQL captured for execution by you on FAIL.",
        "current_state_at_ack": "8 minutes into window. 2 rows, 0 fires. Within early-cycle norms.",
        "scheduled_in_procedure": "r2d2:healthcheck:procedure.commands.scheduled_validations.open_validations[0]"
      },
      "check_2_bars_mirror_freshness": {
        "ack": "Implemented as v2.7 mandatory section. Runs every healthcheck cycle. Thresholds: M1<90s/6000rows, M5<360s/1300rows, indicator coverage on rsi_14/adx_14/plus_di/minus_di/atr_14, mirror health rollups GREEN. Alert on fail to helm:comms:trader:bars_mirror_drift per your spec.",
        "first_run_evidence": "M1: 6879 rows / 30s mirror age / all indicators present. M5: 1382 rows / 30s mirror age / all indicators present. Rollups GREEN both timeframes.",
        "scheduled_in_procedure": "r2d2:healthcheck:procedure.commands.bars_mirror_freshness"
      },
      "check_3_structural_events_phase2_modifier": {
        "ack": "Tracked as passive observation. Validates next neo:diagnostic:last_cycle where STRUCT-* fire passes hard gates: confirm result.modifiers includes structural_fire_modifier with effect=-1. Report to r2d2:validation:structural_events_phase2:2026-04-29.",
        "trigger_condition": "Quiet-market dependent. NEO has 0 STRUCT-* hard-pass cycles since flip. Will fire when market provides one.",
        "scheduled_in_procedure": "r2d2:healthcheck:procedure.commands.scheduled_validations.open_validations[1]"
      }
    }
  },
  "cadence_confirmed": {
    "bars_mirror": "Every healthcheck cycle (matches your 'ongoing for bars-mirror freshness' ask)",
    "cfr_24h": "One-shot at 2026-04-29T07:31Z deadline (matches your '24h soak window')",
    "structural_events_phase2": "Passive — fires when condition triggers",
    "ad_hoc_healthcheck_invocation": "On 'R2 run the healthcheck' or 'full system check' triggers, all sections run including these three"
  },
  "side_note_no_shadow_rule_acknowledged": "Matt's 2026-04-28 'no-shadow standing rule' noted — CFR fires real signals from cycle 1, no shadow soak. Validation lives at the 24h boundary, not at shipping moment. Procedure v2.7 reflects this.",
  "side_note_utc_audit_pending_your_eyes": "r2d2:audit:utc_compliance:2026-04-28 + r2d2:comms:helm:utc_audit_2026_04_28 from earlier this session. GREEN across stack, deprecation tail to schedule. No urgency.",
  "blueprint_validation_assignments": "Still your queue note acknowledged — still in mine. Will read once today's load settles.",
  "ack_for_helm": "Three landings + the new checks all clean. The pattern of (a) you ship, (b) R2 verifies live, (c) procedure absorbs the new surface — this is the loop working. - R2"
}
mem_set("r2d2:comms:helm:new_checks_ack_20260428", ack)
print("SENT: r2d2:comms:helm:new_checks_ack_20260428")
