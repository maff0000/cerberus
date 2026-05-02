"""WO-R2D2-FALCON-DORMANT-GUARD-SENSITIVITY-0001 — 8 dormant strategies, 9 questions.
READ-ONLY. UTC: cycle_ts canonical + git commit_date. No NOW()/utcnow()/time.time()."""

import json, datetime, pymysql, subprocess
from collections import defaultdict, Counter

env = {}
with open("/srv-dev/tradingProteus/.env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v.strip('"').strip("'")

# Anchor on canonical UTC
scalp = pymysql.connect(host="127.0.0.1", port=3307, user=env["DB_USER"],
    password=env["DB_PASSWORD"], database="tradingScalp", charset="utf8mb4")
scur = scalp.cursor(pymysql.cursors.DictCursor)
proteus = pymysql.connect(host="127.0.0.1", port=3307, user=env["DB_USER"],
    password=env["DB_PASSWORD"], database="tradingProteus", charset="utf8mb4")
pcur = proteus.cursor(pymysql.cursors.DictCursor)
sig = pymysql.connect(host="127.0.0.1", port=3307, user=env["DB_USER"],
    password=env["DB_PASSWORD"], database="tradingSignals", charset="utf8mb4")
sgcur = sig.cursor(pymysql.cursors.DictCursor)

scur.execute("SELECT MAX(cycle_ts) AS now FROM helios_v3_decisions")
CANONICAL_NOW = scur.fetchone()["now"].replace(tzinfo=datetime.timezone.utc)
W90_SQL = (CANONICAL_NOW - datetime.timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
NOW_SQL = CANONICAL_NOW.strftime("%Y-%m-%d %H:%M:%S")
print(f"CANONICAL_NOW: {CANONICAL_NOW.isoformat()}")

DORMANTS = ["asia_orb", "brc_m5", "cfr_m5", "crf_m5", "csdr_m15", "fdr_m5",
            "meanrev_edges_m5", "tpc_m15"]

# ============================================================
# Per-strategy: top decline reasons + near-miss patterns + counts
# ============================================================
print("\n=== Per-strategy 90d decline analysis ===")
per_strategy = {}
for sid in DORMANTS:
    scur.execute(f"""
        SELECT instrument, fired, reason_codes, COUNT(*) c
        FROM helios_strategy_signals
        WHERE strategy_id=%s AND timestamp >= '{W90_SQL}' AND timestamp <= '{NOW_SQL}'
        GROUP BY instrument, fired, reason_codes
        ORDER BY c DESC LIMIT 30
    """, (sid,))
    rows = scur.fetchall()

    # Aggregate
    by_instrument = Counter()
    by_reason = Counter()
    total = 0; fired_count = 0; sb_count = 0
    near_miss = []
    other_decline = []
    for r in rows:
        c = int(r["c"]); rc = r["reason_codes"] or ""
        total += c
        by_instrument[r["instrument"]] += c
        if r["fired"] == 1: fired_count += c
        if "SESSION_BLOCKED" in rc: sb_count += c
        # Categorise reasons
        if any(p in rc for p in ["WAITING", "ANCHOR_ARMED", "NO_TRIGGER", "DETECTED",
                                   "AWAITING", "ARMED", "PARTIAL"]):
            near_miss.append({"reason": rc[:100], "count": c, "instrument": r["instrument"]})
        elif r["fired"] == 0 and "SESSION_BLOCKED" not in rc:
            other_decline.append({"reason": rc[:100], "count": c, "instrument": r["instrument"]})
        by_reason[rc[:100]] += c

    per_strategy[sid] = {
        "total_evals_90d": total,
        "fires_90d": fired_count,
        "session_blocked": sb_count,
        "instruments": dict(by_instrument),
        "top_reasons": [(k, v) for k, v in by_reason.most_common(10)],
        "near_miss_patterns": sorted(near_miss, key=lambda x: -x["count"])[:5],
        "other_decline_patterns": sorted(other_decline, key=lambda x: -x["count"])[:5]
    }

    print(f"\n--- {sid} ---")
    print(f"  total_evals: {total}, fires: {fired_count}, SB: {sb_count}")
    print(f"  top reasons:")
    for k, v in by_reason.most_common(5):
        print(f"    {v:>5d} | {k[:90]}")
    if per_strategy[sid]["near_miss_patterns"]:
        print(f"  near-miss:")
        for nm in per_strategy[sid]["near_miss_patterns"][:3]:
            print(f"    {nm['count']:>5d} | {nm['reason']}")

# ============================================================
# Strategy code inspection — what guard does each top reason map to?
# Read worker.py for each dormant
# ============================================================
print("\n=== Code inspection — guard hit rate ===")
strategy_code_paths = {
    "asia_orb": "/srv-dev/falcon/strategies/asia_orb/worker.py",
    "brc_m5": "/srv-dev/falcon/strategies/brc/worker.py",
    "cfr_m5": "/srv-dev/falcon/strategies/capitulation_flip_retest/worker.py",
    "crf_m5": "/srv-dev/falcon/strategies/climax_reversal/worker.py",
    "csdr_m15": "/srv-dev/falcon/strategies/csdr/worker.py",
    "fdr_m5": "/srv-dev/falcon/strategies/fdr/worker.py",
    "meanrev_edges_m5": "/srv-dev/falcon/strategies/meanrev_edges/worker.py",
    "tpc_m15": "/srv-dev/falcon/strategies/tpc/worker.py"
}
code_facts = {}
for sid, path in strategy_code_paths.items():
    out = subprocess.run(["ssh", "root@192.168.11.10", f"ls {path} 2>/dev/null && wc -l {path} 2>/dev/null"],
                          capture_output=True, text=True, timeout=10)
    code_facts[sid] = {"path": path, "exists": bool(out.stdout.strip()),
                        "info": out.stdout.strip()}

# ============================================================
# HERMES freshness for relevant timeframes
# ============================================================
print("\n=== HERMES freshness ===")
hermes_freshness = {}
for tf in ("M1", "M5", "M15", "H1"):
    sgcur.execute(f"SELECT MAX(timestamp) AS latest FROM candles_{tf} WHERE instrument='XAU_USD'")
    row = sgcur.fetchone()
    if row and row["latest"]:
        ts = row["latest"].replace(tzinfo=datetime.timezone.utc)
        age_min = (CANONICAL_NOW - ts).total_seconds() / 60
        hermes_freshness[tf] = {"latest": str(row["latest"]), "age_min": round(age_min, 2)}
        print(f"  {tf}: latest={row['latest']} age={age_min:.2f}min")
    else:
        hermes_freshness[tf] = {"latest": None}

# ============================================================
# Apply labels per strategy
# ============================================================
def label_strategy(sid, info):
    fires = info["fires_90d"]
    total = info["total_evals_90d"]
    near_miss_count = sum(nm["count"] for nm in info["near_miss_patterns"])
    other_decline_count = sum(d["count"] for d in info["other_decline_patterns"])

    # Top non-SB reason
    top_other = [(k, v) for k, v in info["top_reasons"] if "SESSION_BLOCKED" not in k]
    top_other_text = top_other[0][0] if top_other else ""
    top_other_count = top_other[0][1] if top_other else 0

    # Flag-based heuristics
    if total == 0:
        return "INCONCLUSIVE", "No evaluations recorded — strategy may not be loaded into worker pool"
    if fires == 0 and near_miss_count == 0 and other_decline_count > 0:
        # Strategy evaluating but no near-misses → guards rejecting at first stage
        if "INVALID_REGIME" in top_other_text or "NOT_TRENDING" in top_other_text or "BLOCKED_REGIME" in top_other_text:
            return "OVER_CONSTRAINED", f"Top reason '{top_other_text}' suggests regime gate rejecting all setups"
        if "OUTSIDE_WINDOW" in top_other_text:
            return "TRULY_RARE", f"Time-window strategy: '{top_other_text}' is by-design"
        if "NO_DISPLACEMENT" in top_other_text or "NO_COIL" in top_other_text:
            return "TRULY_RARE", f"Pattern strategy: '{top_other_text}' is normal market silence"
        if "RANGE_TOO_NARROW" in top_other_text or "NOT_AT_EDGE" in top_other_text:
            return "OVER_CONSTRAINED", f"Range strategy may have narrow guard"
        return "NEEDS_BETTER_LOGGING", f"Decline pattern '{top_other_text}' but no near-miss visibility"
    if near_miss_count > 0 and fires == 0:
        return "OVER_CONSTRAINED", f"Near-miss patterns observed ({near_miss_count}) but strategy never completes setup"
    if fires > 0:
        return "INCONCLUSIVE", f"Has fires ({fires}) — not truly dormant in 90d"
    return "INCONCLUSIVE", "Pattern unclear"

labels = {}
for sid in DORMANTS:
    label, rationale = label_strategy(sid, per_strategy[sid])
    labels[sid] = {"label": label, "rationale": rationale}
    print(f"  {sid:<22s} {label:<25s} {rationale[:80]}")

# ============================================================
# Save
# ============================================================
import os
os.makedirs("/tmp/r2d2_tuning", exist_ok=True)
out = {
    "canonical_now_utc": CANONICAL_NOW.isoformat(),
    "window_90d_start": W90_SQL,
    "window_end": NOW_SQL,
    "dormants_analysed": DORMANTS,
    "per_strategy_analysis": per_strategy,
    "code_existence": code_facts,
    "hermes_freshness": hermes_freshness,
    "labels": labels
}
with open("/tmp/r2d2_tuning/dormant_analysis.json", "w") as f:
    json.dump(out, f, indent=2, default=str)
print(f"\nSaved /tmp/r2d2_tuning/dormant_analysis.json")

scur.close(); scalp.close(); pcur.close(); proteus.close(); sgcur.close(); sig.close()
