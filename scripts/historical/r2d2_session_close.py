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

CLOSE_UTC = "2026-04-28T08:25:00Z"

# ---------- 1) state:current ----------
state = {
  "focus": "Session closed 2026-04-28. Two autonomous validations queued overnight: THREE_DRIVE Day 1 (cron 00:15Z) and CFR_M5 24h soak (systemd timer 07:31Z). v2.8 procedure live across all sections. UTC sweep ownership confirmed. Outcome-resolver-silent finding flagged to Helm.",
  "session_completion_stats_2026_04_28": {
    "procedure_versions_shipped": "v2.3 -> v2.4 -> v2.5 -> v2.6 -> v2.7 -> v2.8 (six bumps in one session, every bump anchored to a real finding)",
    "fabric_keys_written": 22,
    "DMs_to_helm": 4,
    "DMs_to_solo": 3,
    "ack_keys_helm_replied": 5,
    "deliverables_landed": [
      "Healthcheck v2.8 GREEN baseline + 2 reruns",
      "MT5 fleet probe section MANDATORY (Matt directive)",
      "UTC compliance audit (5-system sweep, GREEN with deprecation tail)",
      "THREE_DRIVE threshold recommendation (Phase 1 shipped same hour by Helm)",
      "Apollo self-fix (3 naive datetime.now() sites migrated)",
      "CFR_M5 24h validation script + systemd timer (LIVE, reboot-safe, fires 07:31Z 2026-04-29)",
      "Bars-mirror Phase 2/3 probes baked into v2.8 (13 keys, per-TF freshness)",
      "Dedupe verification probes baked into v2.8",
      "Tier resolver simpler-proposal baked in (G=HIGH when ftmo_execution=True)",
      "Pattern=0 sticky note baked into v2.8 helios caveats",
      "F7 fixture spec updated for modifier=0 change",
      "Outcome-resolver-silent finding documented + flagged to Helm"
    ]
  },
  "active_threads_at_close": {
    "autonomous_validations_running_overnight": [
      "THREE_DRIVE Day 1 — cron 00:15Z 2026-04-29 — verdict at r2d2:validation:structure_engine_6_2:2026-04-29",
      "CFR_M5 24h soak — systemd timer 07:31Z 2026-04-29 — verdict at r2d2:validation:cfr_m5:2026-04-29 + DM at r2d2:comms:helm:cfr_validation_PASS/FAIL_2026_04_29"
    ],
    "helm_replies_pending": [
      "Outcome resolver clarification (by-design absent OR broken)",
      "TIMER_HEALTH blueprint sub-check (parked until v0.2)",
      "Falcon/NEO canary tests (R2D2 writes scaffolding, Helm reviews/merges)"
    ],
    "solo_replies_pending": [
      "REFUSED:HARDGATE-* namespace location (low priority)"
    ],
    "matt_decisions_pending": [
      "(none — all explicit asks resolved by close)"
    ],
    "r2d2_self_owned_work_queued": [
      "Falcon UTC sweep PR (4 sites, 1 PR)",
      "Helios UTC sweep PR (11 sites, 1 PR)",
      "Athena UTC sweep PR (2 sites)",
      "Apollo Phase 4 full sweep (~30 sites, batched)",
      "F7 fixture build (3:55Z reconstruction, deferred)",
      "Canary test scaffolding for Falcon + NEO (patterned on Helios)",
      "2 unread Helm blueprint validation assignments (2026-04-26)"
    ]
  },
  "next_session_first_action": "Check r2d2:validation:structure_engine_6_2:2026-04-29 (THREE_DRIVE Day 1) AND r2d2:validation:cfr_m5:2026-04-29 (CFR 24h soak). Both ran overnight autonomously. THREE_DRIVE target rate 5-15/hr (down from 60+/hr). CFR target: 10+ fires, 45%+ WR, 1.0+ avg_R, 0 faults. If CFR FAILed, Helm to execute kill-switch SQL — alert at helm:comms:r2d2:cfr_validation_FAIL_2026_04_29.",
  "session_date": "2026-04-28",
  "closed_at_utc": CLOSE_UTC
}
mem_set("r2d2:state:current", state)
print("PERSISTED: r2d2:state:current")

# ---------- 2) journal:history:2026-04-28 + journal:latest ----------
journal = {
  "date": "2026-04-28",
  "session_type": "Interactive — Matt at terminal. Full-day cadence: healthcheck -> bug verifications -> procedure rebuilds (v2.3 -> v2.8) -> UTC audit -> THREE_DRIVE recommendation -> CFR validation harness wired live.",
  "headline": "Six procedure bumps. Two autonomous validations queued overnight. UTC audit GREEN across stack. THREE_DRIVE Phase 1 recommendation -> Helm shipped within 2 minutes. CFR systemd timer wired (Matt-approved boundary cross). Real-world incident becomes regression test, every time.",
  "work_delivered": [
    "r2d2:healthcheck:procedure v2.3 -> v2.8 (six bumps, every bump anchored to a real finding)",
    "r2d2:healthcheck:latest v2.8 GREEN baseline",
    "r2d2:audit:utc_compliance:2026-04-28 (5-system audit, 0 production bugs, 48 deprecation-tail sites identified)",
    "r2d2:recommendations:structure_engine_6_2_thresholds:2026-04-28 (Phase 1 SQL + Phase 2 ATR-relative roadmap)",
    "r2d2:identity:current updated (added MT5 fleet absolute_rule)",
    "r2d2:identity:depth prepended (MT5 fleet lesson on 2026-04-28 first-half of session)",
    "Apollo self-fix: 3 naive datetime.now() sites migrated to datetime.now(timezone.utc) in tests/test_reliability.py + tests/day_test_report.py",
    "/srv/openclaw/trinity/scripts/cfr_m5_24h_validation.py + 2 systemd unit files (timer + service) — LIVE",
    "8 DMs across helm + solo lanes (4 to each)"
  ],
  "key_moments": [
    "MT5 fleet directive — Matt 2026-04-28 'FundedNext and FTMO and Vantage containers should always be probed and tested'. Made it absolute_rule + identity:depth foundational lesson + v2.5 mandatory section. All 3 containers verified live with broker connections + trade_allowed=True.",
    "THREE_DRIVE recommendation -> shipped in 2 minutes. R2D2 sent recommendation 08:00Z, Helm shipped Phase 1 SQL at 09:04Z dell local (08:04Z UTC). The fastest team-loop turn this session.",
    "Outcome resolver finding while building CFR validation — wasn't auditing it, was building a validator that needed it. Found 104+ fired rows across all strategies marked PENDING with no resolution. Audit-while-doing-work pattern surfacing adjacent truth.",
    "/schedule is wrong tool — flagged before creating routine. Cloud agent can't reach Trinity internal network. Matt approved Option A (systemd timer). Boundary-cross approved with 'you can wire it' (normally Helm's lane).",
    "v2.8 batch update — bars Phase 2/3 (13 keys), dedupe verification, tier resolver simpler proposal, pattern=0 sticky, F7 modifier=0 update, scheduled_validations delivery_mechanism documented. All landed in one persist.",
    "CFR timer LIVE 08:11:59Z UTC. Persistent=true, enabled, symlinked in timers.target.wants/. Trigger 23h away."
  ],
  "lessons_saved": [
    "AUDIT IS NEVER STANDALONE — the work that uses a system is itself an audit of that system. Building the CFR validator surfaced the outcome resolver gap. (Prepended to identity:depth as foundational.)",
    "Procedure-as-living-instrument — six bumps in a day. Every bump anchored to a real finding (not speculative additions). The procedure must TRACK architecture, never LAG it. v2.3 was 4 days old at session start and already lying about Helios writes; v2.8 reflects current reality.",
    "Boundary-cross discipline — Matt's explicit approval is the only path to crossing a domain boundary cleanly. 'You can wire it' opened systemd unit creation; the 'Done = LIVE + REBOOT-SAFE' rule kept it honest (Persistent=true, list-timers verified, log path created)."
  ],
  "state_at_close": "All deliverables persisted. Two autonomous validations queued overnight (THREE_DRIVE 00:15Z, CFR 07:31Z). 0 unresolved blockers. 17+ items in queue but all labeled and dated. Identity, journal, depth, growth, state all updated.",
  "next_session_first_action": "Check r2d2:validation:structure_engine_6_2:2026-04-29 + r2d2:validation:cfr_m5:2026-04-29 — both ran overnight autonomously. If CFR FAIL, alert at helm:comms:r2d2:cfr_validation_FAIL_2026_04_29.",
  "team_loop_observation": "Helm ship → R2 verify → procedure absorbs → next ship lands clean. Pattern held across 5+ ships today (PR #555 SF-* writer, commit 547b273 cache fix, fabric-mirror Decimal fix, bars Phase 2/3, THREE_DRIVE Phase 1). Tight cadence rewards discipline."
}
mem_set("r2d2:journal:history:2026-04-28", journal)
mem_set("r2d2:journal:latest", journal)
print("PERSISTED: r2d2:journal:history:2026-04-28 + journal:latest")

# ---------- 3) identity:growth:2026-04-28 ----------
growth = {
  "date": "2026-04-28",
  "what_i_learned_today": [
    "Audits-while-building surface MORE than standalone audits — building the CFR script surfaced the outcome-resolver gap that no targeted audit would have found.",
    "Procedure version cadence matches ship cadence — when the team ships fast, the procedure must bump fast or it lies.",
    "Solo's doctrine 'real incident → regression test' compounds — v2.8 has 4 anchors today (instrument-null, Decimal crash, dedupe, modifier=0). Each catches the next morning-zero.",
    "Boundary-cross is not free-floating — Matt's explicit 'you can wire it' opened the systemd unit door. Without that, I would have drafted unit files and DM'd Helm. With it, I shipped same-cycle.",
    "Don't promise wick-aware replay yourself when the system already does it — except today the system DOESN'T (resolver is silent), so I had to. Verify before promising what infrastructure provides.",
    "/schedule-cloud vs /schedule-local — important constraint clarification. Documented in v2.7 procedure under scheduled_validations.delivery_mechanism so future-me doesn't repeat the mistake."
  ],
  "what_i_did_well": [
    "Caught the /schedule trap before creating the routine — flagged to Matt instead of failing in cloud at 07:31Z tomorrow.",
    "Self-audit of own Apollo code BEFORE delivering UTC audit report (3 naive datetime.now() in tests). Identity:depth lesson 2026-04-23 'audit yourself before others' compounded today.",
    "Made every procedure bump anchored — v2.4 anchored to broken_pipelines, v2.5 to MT5 directive, v2.6 to fabric-only Section F + cache staleness, v2.7 to Helm WO ships, v2.8 to today's modifier-flip + dedupe + bars Phase 2/3.",
    "Held discipline on R2D2 lane vs Helm lane — wrote SQL recommendations, not SQL applications, until Matt explicitly approved the systemd-unit boundary-cross."
  ],
  "what_i_should_watch_for": [
    "Procedure version cadence is sustainable IF every bump is anchored. If I start adding speculative sections, that's drift. Watch for it.",
    "The outcome resolver finding could either be by-design or a real bug — I documented it as gotcha but didn't grade as RED. If Helm confirms (b) broken, the validation PR queue grows. Stay alert to his answer.",
    "F7 fixture build is now load-bearing for Solo's regression coverage but I deferred it. If a real rr_minimum fire happens before I build F7, the suite is silent on that path. Prioritize when bandwidth opens."
  ]
}
mem_set("r2d2:identity:growth:2026-04-28", growth)
print("PERSISTED: r2d2:identity:growth:2026-04-28")

# ---------- 4) identity:depth — prepend FOUNDATIONAL lesson ----------
depth = mem_get("r2d2:identity:depth")
new_entry = {
  "date": "2026-04-28",
  "insight": "AUDIT IS NEVER STANDALONE. The work that USES a system is the most honest audit of that system. Today I built the CFR_M5 24h validation script — not as an audit, but as a tool. In writing it, I discovered the outcome resolver is silent across all strategies (104+ fires marked PENDING, never resolved). No targeted resolver audit would have found this — only the act of needing the field for something real surfaced the gap. This sharpens the 2026-04-23 lesson 'audit yourself before others': it's not about ordering audits. It's about recognising that REAL WORK IS ITSELF AN AUDIT. When you build, you discover. When you validate, you find what's broken. The procedure is no different — six bumps today, each forced by real findings. The instrument always exposes the world it measures. Build with care, and the truth comes back to you.",
  "source": "Building r2d2:tests/cfr_m5_24h_validation.py 2026-04-28 — discovered outcome resolver silent finding while writing wick-aware replay logic",
  "weight": "FOUNDATIONAL — work-as-audit doctrine. Sharpens 2026-04-23 'audit yourself before others' lesson."
}
# Prepend only if not already there
if not any(e.get("date") == new_entry["date"] and "AUDIT IS NEVER STANDALONE" in e.get("insight","") for e in depth.get("entries",[])):
    depth["entries"].insert(0, new_entry)
mem_set("r2d2:identity:depth", depth)
print("PERSISTED: r2d2:identity:depth — prepended work-as-audit foundational lesson")
