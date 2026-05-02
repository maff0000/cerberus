"""WO-R2D2-FALCON-STRATEGY-READINESS-MATRIX-0001
READ-ONLY. UTC discipline. Methodology: r2d2:methodology:correlation:v1 (Spearman default)."""
import json, datetime, pymysql, sys, math
from collections import Counter, defaultdict

env = {}
with open("/srv-dev/tradingProteus/.env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v.strip('"').strip("'")

scalp = pymysql.connect(host="127.0.0.1", port=3307, user=env["DB_USER"],
    password=env["DB_PASSWORD"], database="tradingScalp", charset="utf8mb4")
scur = scalp.cursor(pymysql.cursors.DictCursor)
proteus = pymysql.connect(host="127.0.0.1", port=3307, user=env["DB_USER"],
    password=env["DB_PASSWORD"], database="tradingProteus", charset="utf8mb4")
pcur = proteus.cursor(pymysql.cursors.DictCursor)

scur.execute("SELECT MAX(timestamp) AS now FROM helios_strategy_signals")
CANONICAL_NOW = scur.fetchone()["now"].replace(tzinfo=datetime.timezone.utc)
NOW_SQL = CANONICAL_NOW.strftime("%Y-%m-%d %H:%M:%S")
W90 = (CANONICAL_NOW - datetime.timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
print(f"CANONICAL_NOW: {CANONICAL_NOW.isoformat()}")
print(f"90d window:    {W90} -> {NOW_SQL}")

# Methodology (loaded for the record)
METHODOLOGY = "r2d2:methodology:correlation:v1 (Spearman default, n>=20 min, strength: <0.1 NEGLIGIBLE / 0.1-0.3 WEAK / 0.3-0.5 MODERATE / 0.5+ STRONG)"
print(f"\nMETHODOLOGY: {METHODOLOGY}")

# ============================================================
# Spearman correlation (no scipy dependency)
# ============================================================
def rank(values):
    """Average-rank for ties."""
    sorted_pairs = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(sorted_pairs):
        j = i
        while j+1 < len(sorted_pairs) and sorted_pairs[j+1][1] == sorted_pairs[i][1]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j+1):
            ranks[sorted_pairs[k][0]] = avg_rank
        i = j+1
    return ranks

def spearman(x, y):
    """Returns (rho, n) for paired numeric vectors. None if n < 2."""
    pairs = [(a,b) for a,b in zip(x,y) if a is not None and b is not None]
    n = len(pairs)
    if n < 2: return None, n
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    rx = rank(xs); ry = rank(ys)
    mean_rx = sum(rx)/n; mean_ry = sum(ry)/n
    num = sum((rx[i]-mean_rx)*(ry[i]-mean_ry) for i in range(n))
    den_x = math.sqrt(sum((rx[i]-mean_rx)**2 for i in range(n)))
    den_y = math.sqrt(sum((ry[i]-mean_ry)**2 for i in range(n)))
    if den_x == 0 or den_y == 0: return None, n
    return (num / (den_x * den_y), n)

def label_strength(rho):
    if rho is None: return "INSUFFICIENT"
    abs_r = abs(rho)
    if abs_r < 0.1: return "NEGLIGIBLE"
    if abs_r < 0.3: return "WEAK"
    if abs_r < 0.5: return "MODERATE"
    return "STRONG"

# ============================================================
# Pull 90d fires for every strategy
# ============================================================
scur.execute(f"""
    SELECT id, timestamp, strategy_id, instrument, confidence, adjusted_confidence,
           outcome, outcome_pnl_pts, outcome_mfe_pts, outcome_mae_pts,
           outcome_duration_minutes, fired, evidence, gate_trace
    FROM helios_strategy_signals
    WHERE fired=1 AND timestamp >= '{W90}'
""")
fires = list(scur.fetchall())
print(f"\nTotal 90d fires: {len(fires)}")

by_strategy = defaultdict(list)
for f in fires:
    by_strategy[f["strategy_id"]].append(f)

# ============================================================
# Per-strategy analysis
# ============================================================
matrix = {}

for sid, rows in by_strategy.items():
    n = len(rows)
    confidences = [int(r["confidence"]) for r in rows if r["confidence"] is not None]
    adjusted = [int(r["adjusted_confidence"]) for r in rows if r["adjusted_confidence"] is not None]
    conf_dist = dict(Counter(confidences))
    distinct_conf = len(set(confidences))

    resolved = [r for r in rows if r["outcome"] and r["outcome"] != "PENDING"]
    n_resolved = len(resolved)
    wins = sum(1 for r in resolved if r["outcome"] in ("TP1_HIT", "TP2_HIT"))
    losses = sum(1 for r in resolved if r["outcome"] == "SL_HIT")
    expired = sum(1 for r in resolved if r["outcome"] == "EXPIRED")
    invalidated = sum(1 for r in resolved if r["outcome"] == "INVALIDATED")
    pnls = [float(r["outcome_pnl_pts"]) for r in resolved if r["outcome_pnl_pts"] is not None]
    avg_pnl = sum(pnls)/len(pnls) if pnls else None
    win_pnls = [p for p in pnls if p > 0]
    loss_pnls = [p for p in pnls if p < 0]
    expectancy = avg_pnl  # average P&L per trade

    # gate_trace richness
    instrumented_fires = sum(1 for r in rows if r["gate_trace"] and "evidence_version" in r["gate_trace"])
    gate_trace_status = ("FULL" if instrumented_fires == n else
                         "PARTIAL" if instrumented_fires > 0 else "LEGACY")

    # Confidence-vs-outcome correlation (only meaningful if confidence varies)
    conf_outcome_corr = None
    if distinct_conf >= 2 and pnls:
        # Pair each resolved row's confidence with its pnl
        pairs = [(int(r["confidence"]), float(r["outcome_pnl_pts"]))
                 for r in resolved if r["confidence"] is not None and r["outcome_pnl_pts"] is not None]
        if len(pairs) >= 2:
            rho, np_n = spearman([p[0] for p in pairs], [p[1] for p in pairs])
            conf_outcome_corr = {"rho": rho, "n": np_n, "strength": label_strength(rho)}

    # Dimension correlations: extract candidate features from evidence
    # Strategy-specific feature extraction
    feature_corrs = []
    if n_resolved >= 20:
        # Build feature vectors from evidence
        feature_data = defaultdict(list)  # feature_name -> [(value, pnl)]
        for r in resolved:
            if r["outcome_pnl_pts"] is None: continue
            try: ev = json.loads(r["evidence"]) if r["evidence"] else {}
            except: ev = {}
            try: gt = json.loads(r["gate_trace"]) if r["gate_trace"] else {}
            except: gt = {}
            # Extract numeric features from evidence
            for k, v in ev.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    feature_data[f"ev.{k}"].append((v, float(r["outcome_pnl_pts"])))
                elif isinstance(v, dict):
                    for kk, vv in v.items():
                        if isinstance(vv, (int, float)) and not isinstance(vv, bool):
                            feature_data[f"ev.{k}.{kk}"].append((vv, float(r["outcome_pnl_pts"])))
            # Extract numeric features from gate_trace observed
            if isinstance(gt, dict) and gt.get("guards"):
                for g in gt["guards"]:
                    obs = g.get("observed") or {}
                    for k, v in obs.items():
                        if isinstance(v, (int, float)) and not isinstance(v, bool):
                            feature_data[f"gt.{g.get('name','?')}.{k}"].append((v, float(r["outcome_pnl_pts"])))

        # Compute spearman per feature with sample size guard
        for feat, pairs in feature_data.items():
            if len(pairs) >= 20:  # methodology min sample
                rho, np_n = spearman([p[0] for p in pairs], [p[1] for p in pairs])
                if rho is not None and abs(rho) >= 0.1:  # filter NEGLIGIBLE
                    feature_corrs.append({"feature": feat, "rho": round(rho, 3), "n": np_n,
                                          "strength": label_strength(rho)})
        feature_corrs.sort(key=lambda x: -abs(x["rho"]))

    # ========================================================
    # APPLY LABELS
    # ========================================================
    # readiness_label (Helm's axis)
    readiness_label = None
    readiness_reason = ""
    if n_resolved < 20 and distinct_conf <= 1:
        readiness_label = "INSUFFICIENT_SAMPLE"
        readiness_reason = f"only {n_resolved} resolved trades; cannot build or test formula"
    elif sid == "nowic_rt_m15":
        readiness_label = "BLOCKED_UPSTREAM"
        readiness_reason = "NOWIC_RT enablement is BLOCKED by architect standing rule"
    elif n_resolved == 0 and distinct_conf >= 2:
        readiness_label = "BLOCKED_UPSTREAM"
        readiness_reason = f"variable confidence emitted ({distinct_conf} distinct values) BUT zero resolved trades — outcome tracking gap"
    elif distinct_conf >= 3 and n_resolved >= 20:
        readiness_label = "VARIABLE_CONFIDENCE_READY"
        readiness_reason = f"emits {distinct_conf} distinct confidence values across {n_resolved} resolved trades"
    elif n_resolved >= 20:
        readiness_label = "NEEDS_FORMULA"
        readiness_reason = f"constant/near-constant confidence ({distinct_conf} value(s)) but enough resolved samples ({n_resolved}) to build a variable-confidence formula"
    elif n_resolved < 20 and distinct_conf >= 2:
        readiness_label = "INSUFFICIENT_SAMPLE"
        readiness_reason = f"emits variation but only {n_resolved} resolved trades — need n>=20 to validate"

    # evidence_label (Solo's axis)
    evidence_label = None
    evidence_reason = ""
    if n_resolved < 20:
        evidence_label = "INCONCLUSIVE"
        evidence_reason = f"only {n_resolved} resolved trades — insufficient evidence either way"
    elif expectancy is not None and expectancy > 0.5:
        evidence_label = "EVIDENCE_SUPPORTED"
        evidence_reason = f"positive expectancy +{expectancy:.2f} pts/trade across {n_resolved} resolved"
    elif expectancy is not None and expectancy < -0.5:
        evidence_label = "EVIDENCE_AGAINST"
        evidence_reason = f"negative expectancy {expectancy:.2f} pts/trade across {n_resolved} resolved"
    else:
        evidence_label = "WEAK_EVIDENCE"
        exp_str = f"{expectancy:.2f}" if expectancy is not None else "N/A"
        evidence_reason = f"near-neutral expectancy {exp_str} pts/trade across {n_resolved} resolved"

    # trust_weight_suggested (for Solo's Stage 1)
    weight = 1.0
    if evidence_label == "EVIDENCE_SUPPORTED": weight = 1.5
    elif evidence_label == "EVIDENCE_AGAINST": weight = 0.0
    elif evidence_label == "WEAK_EVIDENCE": weight = 1.0
    elif evidence_label == "INCONCLUSIVE": weight = 0.5
    if readiness_label == "BLOCKED_UPSTREAM": weight = 0.0
    if readiness_label == "VARIABLE_CONFIDENCE_READY" and evidence_label == "EVIDENCE_SUPPORTED":
        weight = 2.0  # promote: variable conf + positive evidence

    matrix[sid] = {
        "fires_90d": n,
        "confidence_distribution": conf_dist,
        "confidence_distinct_values": distinct_conf,
        "confidence_min": min(confidences) if confidences else None,
        "confidence_max": max(confidences) if confidences else None,
        "resolved_count": n_resolved,
        "wins": wins, "losses": losses, "expired": expired, "invalidated": invalidated,
        "win_rate_pct": round(100*wins/(wins+losses), 1) if (wins+losses) else None,
        "avg_pnl_pts": round(avg_pnl, 3) if avg_pnl else None,
        "win_avg_pnl_pts": round(sum(win_pnls)/len(win_pnls), 3) if win_pnls else None,
        "loss_avg_pnl_pts": round(sum(loss_pnls)/len(loss_pnls), 3) if loss_pnls else None,
        "gate_trace_status": gate_trace_status,
        "instrumented_fires": instrumented_fires,
        "confidence_vs_outcome_correlation": conf_outcome_corr,
        "dimension_correlations_top5": feature_corrs[:5],
        "readiness_label": readiness_label,
        "readiness_reason": readiness_reason,
        "evidence_label": evidence_label,
        "evidence_reason": evidence_reason,
        "trust_weight_suggested": weight
    }

# ============================================================
# Print summary
# ============================================================
print("\n=== STRATEGY READINESS MATRIX ===")
for sid in sorted(matrix.keys(), key=lambda s: -matrix[s]["fires_90d"]):
    m = matrix[sid]
    print(f"\n{sid}")
    print(f"  fires_90d={m['fires_90d']} conf_distinct={m['confidence_distinct_values']} ({m['confidence_min']}-{m['confidence_max']}) gate_trace={m['gate_trace_status']}")
    print(f"  resolved={m['resolved_count']} W/L={m['wins']}/{m['losses']} WR={m['win_rate_pct']}% avg_pnl={m['avg_pnl_pts']}")
    if m['confidence_vs_outcome_correlation']:
        c = m['confidence_vs_outcome_correlation']
        print(f"  conf-outcome correlation: rho={c['rho']:.3f} n={c['n']} ({c['strength']})")
    if m['dimension_correlations_top5']:
        print(f"  top-5 dimension correlations:")
        for d in m['dimension_correlations_top5']:
            print(f"    {d['feature']}: rho={d['rho']} n={d['n']} ({d['strength']})")
    print(f"  readiness_label: {m['readiness_label']} — {m['readiness_reason']}")
    print(f"  evidence_label:  {m['evidence_label']} — {m['evidence_reason']}")
    print(f"  trust_weight_suggested: {m['trust_weight_suggested']}")

# ============================================================
# Dormants — listed for completeness but NOT full Matrix rows
# ============================================================
pcur.execute("SELECT plugin_id FROM falcon_select_enablement WHERE enabled=1")
enabled = [r["plugin_id"] for r in pcur.fetchall()]
firing = list(matrix.keys())
dormants = [s for s in enabled if s not in firing]
print(f"\n=== DORMANT (enabled but no 90d fires): {len(dormants)} ===")
for d in dormants: print(f"  {d}")

# ============================================================
# Save
# ============================================================
report = {
    "wo": "WO-R2D2-FALCON-STRATEGY-READINESS-MATRIX-0001",
    "wo_status": "CLOSED",
    "executed_by": "R2D2",
    "anchors": {
        "canonical_now_utc": CANONICAL_NOW.isoformat(),
        "window_90d_start_sql": W90,
        "window_end_sql": NOW_SQL
    },
    "ut_discipline": "READ-ONLY. timestamp + journal-anchored. No NOW()/utcnow()/time.time().",
    "methodology_reference": METHODOLOGY,
    "methodology_key": "r2d2:methodology:correlation:v1",
    "matrix": matrix,
    "dormants_enabled_no_90d_fires": dormants,
    "label_definitions": {
        "readiness_label": {
            "VARIABLE_CONFIDENCE_READY": ">=3 distinct confidence values + >=20 resolved trades — currently emitting variable confidence and has outcome data to validate",
            "NEEDS_FORMULA": "constant/near-constant confidence (1-2 values) but >=20 resolved trades — formula can be built from evidence features",
            "INSUFFICIENT_SAMPLE": "<20 resolved trades — cannot reliably build or test a formula",
            "BLOCKED_UPSTREAM": "structural blocker (architect rule, missing outcome tracking, etc.) — formula work cannot proceed yet"
        },
        "evidence_label": {
            "EVIDENCE_SUPPORTED": "expectancy > +0.5 pts/trade across >=20 resolved",
            "WEAK_EVIDENCE": "near-neutral expectancy (-0.5 to +0.5 pts/trade) across >=20 resolved",
            "EVIDENCE_AGAINST": "expectancy < -0.5 pts/trade across >=20 resolved",
            "INCONCLUSIVE": "<20 resolved trades — insufficient evidence either way"
        },
        "trust_weight_suggested_for_solo_stage_1": {
            "VARIABLE_CONFIDENCE_READY + EVIDENCE_SUPPORTED": 2.0,
            "EVIDENCE_SUPPORTED": 1.5,
            "WEAK_EVIDENCE": 1.0,
            "INCONCLUSIVE": 0.5,
            "EVIDENCE_AGAINST or BLOCKED_UPSTREAM": 0.0
        }
    },
    "downstream_handoff_notes": {
        "for_helm_variable_confidence_queue": (
            "Strategies labelled NEEDS_FORMULA with strongest dimension correlations should be queued first. "
            "TDR_M5 and SF-002 already emit variation — TDR has outcomes (validate), SF-002 lacks outcome tracking (fix that first)."
        ),
        "for_solo_stage_1_weighting": (
            "trust_weight_suggested column is direct multiplier for Section 11 vote weighting. "
            "Refresh after each Helm formula deployment + R2D2 revalidation."
        )
    }
}

import os
os.makedirs("/tmp/r2d2_tuning", exist_ok=True)
with open("/tmp/r2d2_tuning/strategy_readiness_matrix.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\nLOCAL: /tmp/r2d2_tuning/strategy_readiness_matrix.json")

scur.close(); scalp.close(); pcur.close(); proteus.close()
print("DONE.")
