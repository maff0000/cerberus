import json, urllib.request

API = "http://localhost:8080/api/v1/redis"

def mem_set(key, value):
    payload = json.dumps({"key": key, "value": json.dumps(value)}).encode()
    req = urllib.request.Request(f"{API}/set", data=payload,
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=5)

result = {
  "suite_id": "r2d2:healthcheck:procedure",
  "version": "2.3",
  "run_time_utc": "2026-04-28T04:03:28Z",
  "run_trigger": "Matt: 'run full systems check please R2'",
  "overall_status": "AMBER",
  "overall_headline": "Materially improved since 2026-04-24. Helm fixed all 3 ARES broken pipelines. SSH/NEO/Falcon GREEN. Helios daemon GREEN but write-path frozen since 2026-04-24 08:00:01Z (V2 cutover steady state, dispatch DISABLED intentionally). ARES advisory:current key gone — needs Helm confirmation if retired or new break.",
  "sections": {
    "ssh_tunnel": {
      "status": "GREEN",
      "evidence": "Trinity->dell PONG <1s; fabric-tunnel.service active since 2026-04-23 21:52 BST (~5d uptime, stable); HTTP 200 from :18080; fabric-tunnel-canary fired 04:54:44 BST = 03:54:44Z (~9min ago at run, OK)",
      "note": None
    },
    "neo": {
      "status": "GREEN",
      "evidence": "Observer cron present (* * * *); observer.log mtime 2026-04-28T03:59:02Z (~4min ago, in-cycle); neo:state:XAU_USD ts=2026-04-28T03:59:01Z; diagnostic cycle_at_utc=2026-04-28T03:59:01Z; architecture_mode=judgement; decision=NO_QUALIFIED_FIRE (correct - quiet asia, top score 0.00 vs 7.0 threshold)",
      "note": "0 open paper trades, no daily ledger keys yet (expected - no qualified fires since flip 2026-04-22). Last cycle reported 1 STRUCTURAL would-fire in shadow + 19 rejections. Judgement layer healthy."
    },
    "falcon": {
      "status": "GREEN",
      "evidence": "falcon-shadow.service active since 2026-04-27 17:39 BST (~10h uptime, recent restart); last cycle 2026-04-28T03:54:58Z (~9min ago, within 6m boundary); cycle_number=136. All 13 plugins writing within 24h - DB row counts: 12 strategies @ 272 rows, nowic_at_m15 @ 1130 (M15 anchor cadence, expected). Latest rows 2026-04-28T03:54:58Z across all 13.",
      "note": "Journal counts (3503 nowic_at, 825-898 others) all healthy. Zero anomalies."
    },
    "helios": {
      "status": "AMBER",
      "evidence": "helios-shadow.service active since 2026-04-27 10:42 BST (~17h uptime); HELIOS_GATE0 cycling ~1.3s/cycle (3 cycles in 4s window); 0 HELIOS_V2_ERROR in 24h. helios_strategy_signals SF-* table FROZEN: SF-002/SF-003/SF-007 all latest=2026-04-24 08:00:01Z, total=2090 each (zero growth in 4 days). Dispatch state: 264 SKIPPED / 5min, ALL with suppression_reason=DISPATCH_DISABLED (vs ADVISORY_NOT_GO on 2026-04-24).",
      "note": "Reading: V2 cutover steady state. SF-* freeze at 08:00:01Z 2026-04-24 confirmed as pre-V1-retirement boundary, not regression. Dispatch flipped from cascade-suppressed (ADVISORY_NOT_GO) to explicitly-disabled (DISPATCH_DISABLED) - controlled, intentional. Daemon scanning healthy; write path retired by Solo's 2026-04-24 14:00Z helios_decisions retire notice. AMBER not RED because behavior is consistent with announced architecture, but 4 days zero-fires across all 3 scanners warrants Helm confirmation that the V2 fire-write path is correctly wired and we're not silently missing fires."
    },
    "ares_sync": {
      "status": "AMBER",
      "evidence": "Trinity ares:* current=15, history=1992. Dell source ares:* = 15. Sync delta = 0 (perfect parity, vs Trinity-only-15/dell-14 on 2026-04-24). Fresh values: ares:market:status published_at=2026-04-28T04:00:01Z (~3m ago, market_status=OPEN, source=tradingRisk.trading_calendar), ares:macro:snapshot generated_at=2026-04-28T03:10:01Z (~53m ago, regime=NEUTRAL, alignment_score=0). Mirror health rollups GREEN (fabric:mirror:health:ares last_cycle 04:02:01Z, 15/15 keys; fabric:mirror:health:falcon_fires last_cycle 04:02:31Z).",
      "note": "Critical state-change versus 2026-04-24: ares:advisory:current key NO LONGER EXISTS (was holding stale NO_GO from 10:00Z 04-24). This was the cascade root that gated Helios dispatch. Question for Helm: is the advisory publisher retired (intentional decommission) or broken (silent regression)? Answer determines whether Helios DISPATCH_DISABLED can be lifted.",
      "broken_pipelines_status_vs_20260424": [
        {"name": "trinity_market_status_bridge", "status_2026_04_24": "RED (script moved to retired/, cron still calling old path)", "status_2026_04_28": "FIXED - Trinity crontab no longer references market_status_bridge.py. ares:market:status now mirrored from dell via fabric-mirror service. Fresh payload OPEN/is_trading=true."},
        {"name": "dell_market_status_publisher", "status_2026_04_24": "RED (services/market_status_publisher.py never existed)", "status_2026_04_28": "FIXED - file now exists at /srv-dev/tradingProteus/ares/services/market_status_publisher.py, dell crontab still scheduling */15min, key publishing successfully."},
        {"name": "ares_macro_publisher", "status_2026_04_24": "RED (publisher.py source missing, only .pyc remained, systemd exit-code failures)", "status_2026_04_28": "FIXED - ares-macro.service ran at 04:10:02 BST today, exit 0/SUCCESS, snapshot published successfully (NEUTRAL regime, all 3 instruments populated)."}
      ],
      "new_finding_2026_04_28": "ares:advisory:current key absent. Was the only ares:* current key generating gating signal (NO_GO 04-24). Status of advisory publisher unknown - flag to Helm."
    }
  },
  "dependent_suites": {
    "structure_engine_6_2_validation": {"status": "NOT_RUN_THIS_SESSION", "reason": "Background context only - last verdict was RED 2026-04-24 (THREE_DRIVE 77/hr vs 10 cap). Re-run on Matt direction."},
    "struct_tick_persistence": {"status": "NOT_RUN_THIS_SESSION", "reason": "Last RED 2026-04-23 - 5d stale. Re-run on Matt direction."},
    "fabric_mirror": {"status": "GREEN", "reason": "Per-entry health rollups fresh (~1m ago) and GREEN. ares + falcon_fires both reporting 15/15 and 1 row mirrored."},
    "neo_health_suite": {"status": "NOT_RUN_THIS_SESSION", "reason": "Liveness GREEN via NEO probes. Full 10-section suite available on 'R2 run the NEO suite' trigger."}
  },
  "open_unread_helm_messages_at_run": [
    "helm:comms:r2d2:blueprint_validation_assignment_2026_04_26 (subject: 'New validation lane assignment - Helm Blueprint System Map. Pressure-test it.')",
    "helm:comms:r2d2:blueprint_validation_assignment_2026_04_26:draft1"
  ],
  "comparison_to_2026_04_24": {
    "ssh_tunnel": "Same GREEN. Tunnel uptime extended to ~5d.",
    "neo": "Same GREEN. Judgement layer holding post-flip.",
    "falcon": "Same GREEN. Daemon restarted Apr 27 17:39 BST, cycling normally.",
    "helios": "AMBER -> AMBER. Different reason: cascade-suppression -> explicit-disable. V2 cutover steady state confirmed.",
    "ares_sync": "RED -> AMBER. 3 broken pipelines all fixed. New question: advisory:current key gone."
  },
  "persist_to": ["r2d2:healthcheck:latest", "r2d2:healthcheck:history:2026-04-28"],
  "next_actions_for_matt": [
    "Confirm with Helm: is ares:advisory:current intentionally retired, or is the publisher broken? Determines whether Helios DISPATCH_DISABLED is the new normal or temporary.",
    "Confirm with Helm: V2 fire-write path for SF-002/003/007 - where do post-cutover fires write? 4 days zero rows across all 3 scanners should produce something in EITHER helios_strategy_signals (with V2 fired-only semantic) OR a different table.",
    "2 new Helm assignments unread (blueprint validation 2026-04-26)."
  ]
}

mem_set("r2d2:healthcheck:latest", result)
mem_set("r2d2:healthcheck:history:2026-04-28", result)
print("PERSISTED: r2d2:healthcheck:latest + r2d2:healthcheck:history:2026-04-28")
