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

# 1. Update procedure to v2.5 with mt5_containers section
proc = mem_get("r2d2:healthcheck:procedure")
proc["version"] = "2.5"
proc["updated"] = "2026-04-28"
proc["updated_by"] = (proc.get("updated_by","") +
    " | v2.5: Matt directive 2026-04-28 — FundedNext + FTMO + Vantage MT5 containers ALWAYS probed and tested. Container up + RPYC handshake + MT5.initialize() + terminal_info.connected + account_info reachable.")

# Add scope entry
if "MT5 container fleet (FundedNext + FTMO + Vantage) — Matt directive 2026-04-28: ALWAYS PROBED" not in proc.get("scope",[]):
    proc.setdefault("scope",[]).append(
        "MT5 container fleet (FundedNext + FTMO + Vantage) — Matt directive 2026-04-28: ALWAYS PROBED. Container up + RPYC + MT5 init + terminal connected + account reachable."
    )

# New mandatory section
proc["commands"]["mt5_containers"] = {
  "_origin": "MANDATORY per Matt directive 2026-04-28. Always run as part of full healthcheck.",
  "_rationale": "All three MT5 containers carry execution risk. Vantage = live capital. FTMO Practice = NEO learning ground (zero risk but flip-readiness gate). FundedNext = funded account. Container being up is necessary but not sufficient — the RPYC layer + MT5 terminal connection + broker login are what actually let trades execute. A silently-disconnected container looks 'Up' to docker ps but rejects every order.",
  "containers": [
    {"name": "MT5_Vantage",       "host": "localhost", "rpyc_port": 18812, "purpose": "Vantage live"},
    {"name": "MT5_FTMO_Practice", "host": "localhost", "rpyc_port": 18813, "purpose": "FTMO practice / NEO learning"},
    {"name": "MT5_FundedNext",    "host": "localhost", "rpyc_port": 18815, "purpose": "FundedNext funded"}
  ],
  "_location_rule": "ALL three containers run on TRINITY (NOT dell-debian). ssh root@192.168.11.10 will not find them. R2D2's prior probe error 2026-04-22 (and Solo's apparent same trap 2026-04-28) is the anchor.",
  "probe_per_container": {
    "step_1_docker_status": "docker ps --format '{{.Names}}|{{.Status}}|{{.Ports}}' | grep '^<NAME>'",
    "step_2_port_open": "timeout 3 bash -c 'echo > /dev/tcp/localhost/<RPYC_PORT>'",
    "step_3_rpyc_handshake": "import rpyc; conn = rpyc.classic.connect('localhost', <RPYC_PORT>); conn.modules.sys.version  # remote python",
    "step_4_mt5_init": "mt5 = conn.modules.MetaTrader5; mt5.initialize()  # must return True",
    "step_5_terminal_info": "ti = mt5.terminal_info(); assert ti.connected == True AND ti.trade_allowed == True",
    "step_6_account_info": "ai = mt5.account_info(); assert ai.login is not None AND ai.server populated AND ai.balance / ai.equity numeric"
  },
  "healthy_signals": [
    "Container Status starts with 'Up'",
    "RPYC port reachable on localhost",
    "RPYC handshake succeeds (remote python responds)",
    "mt5.initialize() returns True",
    "terminal_info.connected == True",
    "terminal_info.trade_allowed == True (kill switch open)",
    "account_info.login matches expected from neo:prop:accounts (or trader:accounts:vantage)",
    "balance + equity numeric (not None, not stale at zero)"
  ],
  "fault_grading": {
    "container_not_up_or_missing": "RED — block all trading on that broker",
    "port_closed": "RED — RPYC service not listening, container alive but unreachable",
    "rpyc_handshake_fail": "RED — service running but communication broken (auth, version mismatch)",
    "mt5_initialize_false": "RED — MT5 module loaded but terminal init failed (broker connection lost)",
    "terminal_connected_false": "RED — broker connection dropped, orders will reject",
    "trade_allowed_false": "AMBER — kill switch closed (could be intentional). Cross-check with neo:prop:accounts.execution_mode and trader:flags:* before grading RED.",
    "account_login_mismatch": "RED — wrong account loaded into container, do not trade until restored"
  },
  "what_solos_2026_04_28_finding_actually_was": "Open question — the live container probe 2026-04-28 04:48Z showed all 3 MT5 containers GREEN with broker connections live and trade_allowed=True. Solo's 'FTMO container missing' from the morning either (a) was a probe-on-dell error like R2D2's 2026-04-22 lesson, (b) was a transient that resolved, or (c) is a deeper symptom abbreviated as 'missing'. Until clarified, do not assume the symptom is closed; do trust the live probe."
}

# Update output_shape
sect = proc["output_shape"].setdefault("sections_required_v24", proc["output_shape"].get("sections_required_v25", []))
proc["output_shape"]["sections_required_v25"] = sect + (["mt5_containers (NEW v2.5 — MANDATORY per Matt 2026-04-28)"] if "mt5_containers (NEW v2.5 — MANDATORY per Matt 2026-04-28)" not in sect else [])

# Update triggers
proc["triggers"]["v25_invocation_note"] = "On 'run the healthcheck': v2.5 adds mandatory mt5_containers section. Probes all 3 (FundedNext + FTMO + Vantage) with full RPYC + MT5 connection chain, not just docker ps."

mem_set("r2d2:healthcheck:procedure", proc)
print("PERSISTED: r2d2:healthcheck:procedure v2.5")

# 2. Add rule to identity:current absolute_rules
ic = mem_get("r2d2:identity:current")
new_rule = "MT5 CONTAINER FLEET ALWAYS PROBED. FundedNext + FTMO + Vantage. Always on Trinity (never dell). Probe stack: container Up → RPYC port → RPYC handshake → mt5.initialize() → terminal_info.connected + trade_allowed → account_info.login + balance + equity. Matt directive 2026-04-28."
if new_rule not in ic.get("absolute_rules",[]):
    ic.setdefault("absolute_rules",[]).append(new_rule)
ic["updated"] = "2026-04-28"
mem_set("r2d2:identity:current", ic)
print("PERSISTED: r2d2:identity:current — added MT5 fleet rule to absolute_rules")

# 3. Prepend to identity:depth (PREPEND-ONLY)
depth = mem_get("r2d2:identity:depth")
new_entry = {
  "date": "2026-04-28",
  "insight": "MT5 CONTAINER FLEET ALWAYS PROBED. Matt directive 2026-04-28 — FundedNext + FTMO + Vantage MT5 containers must ALWAYS be probed and tested as part of full healthcheck. All three live on Trinity (not dell). Probing only docker ps is insufficient — a silently-disconnected MT5 reads 'Up' to docker but rejects every order. Probe stack: container Up → RPYC port reachable → RPYC handshake → mt5.initialize() → terminal_info.connected + trade_allowed → account_info.login matches expected + balance + equity numeric. Solo flagged 'FTMO container missing' this morning; live probe found ALL 3 GREEN with brokers connected and trade_allowed=True. Solo likely tripped on the same dell-vs-Trinity location trap I hit on 2026-04-22. The lesson compounds: location lessons are foundational, and execution-path probes must walk the full chain to broker connectivity, not just to the systemd unit. v2.5 procedure carries this as a mandatory section and identity:current carries it as an absolute_rule.",
  "source": "Matt — direct directive 2026-04-28 ('FundedNext and FTMO and Vantage containers should always be probed and tested')",
  "weight": "FOUNDATIONAL — fleet probe rule + container-up-is-not-enough doctrine"
}
if not any(e.get("date") == new_entry["date"] and "MT5 CONTAINER FLEET" in e.get("insight","") for e in depth.get("entries",[])):
    depth["entries"].insert(0, new_entry)
mem_set("r2d2:identity:depth", depth)
print("PERSISTED: r2d2:identity:depth — prepended MT5 fleet lesson")

# 4. Re-persist healthcheck:latest with the new section
hc = mem_get("r2d2:healthcheck:latest")
hc["version"] = "2.5"
hc["run_time_utc"] = "2026-04-28T04:55:00Z"
hc["sections"]["mt5_containers"] = {
  "status": "GREEN",
  "_origin": "NEW v2.5 — MANDATORY per Matt directive 2026-04-28",
  "containers_probed": [
    {
      "name": "MT5_Vantage", "rpyc_port": 18812, "uptime": "Up 2 weeks",
      "rpyc_handshake": "OK (remote python 3.9.13)",
      "mt5_initialize": True,
      "terminal_connected": True, "trade_allowed": True, "build": 5700,
      "account_login": 26582979, "server": "VantageInternational-Live 10",
      "balance": 4968.97, "equity": 6141.97,
      "verdict": "GREEN — fully operational, live broker connection, trades enabled"
    },
    {
      "name": "MT5_FTMO_Practice", "rpyc_port": 18813, "uptime": "Up 7 days",
      "rpyc_handshake": "OK (remote python 3.9.13)",
      "mt5_initialize": True,
      "terminal_connected": True, "trade_allowed": True, "build": 5800,
      "account_login": 1513159824, "server": "FTMO-Demo",
      "balance": 99989.29, "equity": 99989.29,
      "verdict": "GREEN — fully operational, FTMO-Demo live, trades enabled. Solo's 'FTMO container missing' morning finding does NOT match current state."
    },
    {
      "name": "MT5_FundedNext", "rpyc_port": 18815, "uptime": "Up 7 days",
      "rpyc_handshake": "OK (remote python 3.9.13)",
      "mt5_initialize": True,
      "terminal_connected": True, "trade_allowed": True, "build": 5800,
      "account_login": 13945833, "server": "FundedNext-Server 2",
      "balance": 5999.96, "equity": 5999.96,
      "verdict": "GREEN — fully operational, funded account live, trades enabled"
    }
  ],
  "section_grade": "GREEN",
  "note": "Solo's morning P1 'FTMO container missing' is unverified by live probe. All 3 containers Up, RPYC reachable, MT5 connected to broker, trade_allowed=True. Likely Solo tripped on dell-vs-Trinity location trap. R2D2 will brief Solo and request specifics."
}
hc["overall_status"] = "GREEN"
mem_set("r2d2:healthcheck:latest", hc)
mem_set("r2d2:healthcheck:history:2026-04-28", hc)
print("PERSISTED: r2d2:healthcheck:latest + history v2.5 with mt5_containers section")
