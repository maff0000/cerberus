"""Full NOWIC_AT formula validation — runs when post-deploy fire count >= 20.
SSH dell-debian, query metrics, compute Spearman, run cascade test, label, publish.

UTC discipline: deploy anchor architect-stamped from PR #605 / f164a43f.
Cycle_ts column is the canonical UTC anchor for windowing.
NEVER use NOW(), UTC_TIMESTAMP(), datetime.now(), datetime.utcnow(), time.time().
"""
import json, subprocess, sys, datetime, urllib.request, math
from collections import defaultdict, Counter

# Re-anchored at PR #614 GUARDRAIL_REACH (post-hardening sweep CLOSED GREEN).
# Architect directive 2026-05-01: ignore all fired rows before this anchor.
DEPLOY_ANCHOR_UTC_STR = "2026-05-01T08:06:32+00:00"
DEPLOY_MERGE_COMMIT = "a3e9a1af6ffecd0c29f1d911e363268c8ab9403e"  # PR #614
DEADLINE_UTC_STR = "2026-05-08T08:06:32+00:00"
EXCEPTION_ID = "ONE_TIME_EXCEPTION_NOWIC_AT_VALIDATION_WATCHER"
TRIGGER_THRESHOLD = 20
DELL = "root@192.168.11.10"
FABRIC_API = "http://localhost:8080/api/v1/redis"

DEPLOY_ANCHOR = datetime.datetime.fromisoformat(DEPLOY_ANCHOR_UTC_STR)
DEADLINE = datetime.datetime.fromisoformat(DEADLINE_UTC_STR)
DEPLOY_SQL = DEPLOY_ANCHOR.strftime("%Y-%m-%d %H:%M:%S")


def fabric_get(key):
    try:
        r = urllib.request.urlopen(f"{FABRIC_API}/get/{key}", timeout=5)
        d = json.loads(r.read())
        v = d.get("value")
        return json.loads(v) if v else None
    except Exception:
        return None


def fabric_set(key, value):
    payload = json.dumps({"key": key, "value": json.dumps(value)}).encode()
    req = urllib.request.Request(f"{FABRIC_API}/set", data=payload,
                                  headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=8).status


def remote_query(db, query):
    full = (
        f"mysql -h127.0.0.1 -P3307 -uroot -pPDAPass@R00t123 "
        f"{db} --batch --raw -e \"{query}\""
    )
    out = subprocess.run(["ssh", DELL, full], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"FAIL_LOUD: {db} query failed: {out.stderr}")
    lines = out.stdout.strip().split("\n")
    if len(lines) < 2:
        return []
    headers = lines[0].split("\t")
    return [{h: v for h, v in zip(headers, vals)} for vals in (line.split("\t") for line in lines[1:])]


def parse_dt(s):
    if not s or s == "NULL": return None
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    except Exception:
        return None


def entropy(d):
    t = sum(d.values())
    if t == 0: return 0.0
    return -sum((c/t)*math.log2(c/t) for c in d.values() if c>0)


def spearman(pairs):
    if len(pairs) < 3: return None
    xs = [p[0] for p in pairs]; ys = [p[1] for p in pairs]
    def rank(arr):
        sorted_arr = sorted(enumerate(arr), key=lambda t: t[1])
        ranks = [0.0]*len(arr); i = 0
        while i < len(sorted_arr):
            j = i
            while j+1 < len(sorted_arr) and sorted_arr[j+1][1] == sorted_arr[i][1]: j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j+1): ranks[sorted_arr[k][0]] = avg
            i = j+1
        return ranks
    rx = rank(xs); ry = rank(ys); n = len(xs)
    mx = sum(rx)/n; my = sum(ry)/n
    num = sum((rx[i]-mx)*(ry[i]-my) for i in range(n))
    dx = math.sqrt(sum((rx[i]-mx)**2 for i in range(n)))
    dy = math.sqrt(sum((ry[i]-my)**2 for i in range(n)))
    if dx == 0 or dy == 0: return None
    return num / (dx * dy)


def parse_evidence_body_ratio(ev_str):
    try: ev = json.loads(ev_str) if ev_str else {}
    except: return None
    nested = ev.get("nowic_at") or {}
    body = nested.get("body_ratio")
    if body is None: body = ev.get("body_ratio")
    return float(body) if body is not None else None


def parse_evidence_breakdown(ev_str):
    try: ev = json.loads(ev_str) if ev_str else {}
    except: return None
    nested = ev.get("nowic_at") or {}
    return ev.get("confidence_breakdown") or nested.get("confidence_breakdown")


def run_validation():
    """Execute full NOWIC_AT validation. Returns (label, report_dict)."""
    # Canonical now from MAX(helios_v3_decisions.cycle_ts)
    anchor_rows = remote_query("tradingScalp", "SELECT MAX(cycle_ts) AS anchor FROM helios_v3_decisions")
    if not anchor_rows or not anchor_rows[0].get("anchor"):
        raise RuntimeError("FAIL_LOUD: no V3 cycle anchor")
    canonical_now = parse_dt(anchor_rows[0]["anchor"])
    if canonical_now is None or canonical_now < DEPLOY_ANCHOR:
        raise RuntimeError("FAIL_LOUD: canonical_now invalid or pre-deploy")
    NOW_SQL = canonical_now.strftime("%Y-%m-%d %H:%M:%S")

    # Pre / post distributions
    W90_SQL = (DEPLOY_ANCHOR - datetime.timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
    pre_rows = remote_query("tradingScalp",
        f"SELECT confidence, COUNT(*) c FROM helios_strategy_signals "
        f"WHERE strategy_id='nowic_at_m15' AND fired=1 "
        f"AND timestamp >= '{W90_SQL}' AND timestamp < '{DEPLOY_SQL}' "
        f"GROUP BY confidence")
    pre_dist = {int(r["confidence"]): int(r["c"]) for r in pre_rows if r.get("confidence") and r["confidence"] != "NULL"}
    post_rows = remote_query("tradingScalp",
        f"SELECT confidence, COUNT(*) c FROM helios_strategy_signals "
        f"WHERE strategy_id='nowic_at_m15' AND fired=1 "
        f"AND timestamp >= '{DEPLOY_SQL}' AND timestamp <= '{NOW_SQL}' "
        f"GROUP BY confidence")
    post_dist = {int(r["confidence"]): int(r["c"]) for r in post_rows if r.get("confidence") and r["confidence"] != "NULL"}

    # Fetch each post-deploy fire row (for Spearman + outcomes + breakdown)
    fire_rows = remote_query("tradingScalp",
        f"SELECT id, timestamp, confidence, evidence, outcome, outcome_pnl_pts "
        f"FROM helios_strategy_signals "
        f"WHERE strategy_id='nowic_at_m15' AND fired=1 "
        f"AND timestamp >= '{DEPLOY_SQL}' AND timestamp <= '{NOW_SQL}'")

    pairs_body_conf = []; breakdown_present = 0; sample_breakdown = None
    WIN, LOSS = {"TP1_HIT", "TP2_HIT"}, {"SL_HIT"}
    buckets = defaultdict(lambda: {"n":0,"wins":0,"losses":0,"pending":0,"invalid":0,
                                     "pnl_sum":0.0,"pnl_count":0})
    for r in fire_rows:
        try: c = int(r["confidence"]) if r.get("confidence") and r["confidence"] != "NULL" else None
        except: c = None
        body = parse_evidence_body_ratio(r.get("evidence", ""))
        bd = parse_evidence_breakdown(r.get("evidence", ""))
        if bd:
            breakdown_present += 1
            if sample_breakdown is None: sample_breakdown = bd
        if c is not None and body is not None:
            pairs_body_conf.append((body, c))
        if c is None: continue
        b = buckets[c]; b["n"] += 1
        o = r.get("outcome")
        if o in WIN: b["wins"] += 1
        elif o in LOSS: b["losses"] += 1
        elif o == "PENDING": b["pending"] += 1
        elif o == "INVALIDATED": b["invalid"] += 1
        try:
            if r.get("outcome_pnl_pts") and r["outcome_pnl_pts"] != "NULL":
                b["pnl_sum"] += float(r["outcome_pnl_pts"]); b["pnl_count"] += 1
        except: pass

    rho = spearman(pairs_body_conf)
    bucket_summary = {}
    for c in sorted(buckets):
        b = buckets[c]; res = b["wins"] + b["losses"]
        bucket_summary[c] = {"n":b["n"],"wins":b["wins"],"losses":b["losses"],"pending":b["pending"],
                              "invalid":b["invalid"],"resolved":res,
                              "wr_pct":round(b["wins"]/res*100,1) if res>0 else None,
                              "expectancy":round(b["pnl_sum"]/b["pnl_count"],2) if b["pnl_count"]>0 else None}

    # Fire rate regression
    pre_30d = (DEPLOY_ANCHOR - datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    pre30_rows = remote_query("tradingScalp",
        f"SELECT COUNT(*) c FROM helios_strategy_signals "
        f"WHERE strategy_id='nowic_at_m15' AND fired=1 "
        f"AND timestamp >= '{pre_30d}' AND timestamp < '{DEPLOY_SQL}'")
    fires_pre_30d = int(pre30_rows[0]["c"]) if pre30_rows else 0
    post_total = sum(post_dist.values())
    hours_pre, hours_post = 30*24, (canonical_now - DEPLOY_ANCHOR).total_seconds()/3600
    rate_pre = fires_pre_30d / hours_pre
    rate_post = post_total / hours_post if hours_post > 0 else 0
    pct_change = ((rate_post - rate_pre)/rate_pre * 100) if rate_pre > 0 else None
    regression = pct_change is not None and pct_change < -20.0

    # Safety: guardrail + fault log
    guardrail_rows = remote_query("tradingScalp",
        f"SELECT COUNT(*) c FROM helios_strategy_signals "
        f"WHERE strategy_id='nowic_at_m15' "
        f"AND timestamp >= '{DEPLOY_SQL}' AND timestamp <= '{NOW_SQL}' "
        f"AND (reason_codes LIKE '%FUTURE_TS%' OR reason_codes LIKE '%GUARDRAIL%')")
    guardrail_hits = int(guardrail_rows[0]["c"]) if guardrail_rows else 0
    fault_rows = remote_query("tradingProteus",
        f"SELECT COUNT(*) c FROM falcon_fault_log "
        f"WHERE created_at >= '{DEPLOY_SQL}' AND created_at <= '{NOW_SQL}' "
        f"AND component LIKE '%nowic%'")
    fault_count = int(fault_rows[0]["c"]) if fault_rows else 0

    n_resolved_total = sum(bucket_summary[c]["resolved"] for c in bucket_summary)

    # Label decision (architect's 4 options + INCONCLUSIVE_PENDING_FORWARD_FIRES)
    label = None; rationale = None
    if regression:
        label = "REGRESSION"
        rationale = f"Fire rate dropped {pct_change:.1f}% (pre {rate_pre:.4f}/h -> post {rate_post:.4f}/h)"
    elif fault_count > 0 or guardrail_hits > 0:
        label = "REGRESSION"
        rationale = f"Safety hits: {guardrail_hits} guardrail, {fault_count} fault"
    elif post_total < TRIGGER_THRESHOLD:
        label = "INCONCLUSIVE"
        rationale = f"post_total={post_total} < threshold={TRIGGER_THRESHOLD}"
    elif n_resolved_total < 5:
        label = "INCONCLUSIVE"
        rationale = f"Only {n_resolved_total} resolved fires; need >=5 for outcome correlation"
    elif rho is None:
        label = "INCONCLUSIVE"
        rationale = "Insufficient body_ratio coverage in evidence for Spearman"
    elif rho < -0.4:
        # Check if HIGH band outperforms LOW band
        sorted_c = sorted(c for c in bucket_summary if bucket_summary[c]["wr_pct"] is not None)
        if len(sorted_c) >= 2 and bucket_summary[sorted_c[-1]]["wr_pct"] > bucket_summary[sorted_c[0]]["wr_pct"]:
            label = "EVIDENCE_SUPPORTED"
            rationale = (f"Spearman rho={rho:.3f} < -0.4. HIGH-band WR={bucket_summary[sorted_c[-1]]['wr_pct']}% > "
                         f"LOW-band WR={bucket_summary[sorted_c[0]]['wr_pct']}%. {n_resolved_total} resolved.")
        else:
            label = "WEAK_EVIDENCE"
            rationale = f"Strong correlation rho={rho:.3f} but HIGH-band WR not greater than LOW-band"
    elif rho < -0.2:
        label = "WEAK_EVIDENCE"
        rationale = f"Marginal separation rho={rho:.3f} (target < -0.4). {n_resolved_total} resolved."
    else:
        label = "REGRESSION"
        rationale = f"Confidence INDEPENDENT of body_ratio (rho={rho:.3f}, expected < -0.4)"

    # confidence_breakdown JSON presence
    breakdown_rate = (breakdown_present / len(fire_rows)) if fire_rows else None

    report = {
        "report_id": f"r2d2:audit:nowic_at_m15_formula_validation:{canonical_now.isoformat()}",
        "wo": "WO-FALCON-CONFIDENCE-FORMULA-NOWIC-AT-M15-0001",
        "validator": "R2D2 (autonomous via nowic_at_validation_watcher)",
        "exception_ref": EXCEPTION_ID,
        "deploy_anchor_utc": DEPLOY_ANCHOR_UTC_STR,
        "deploy_merge_commit": DEPLOY_MERGE_COMMIT,
        "deploy_anchor_source": "git log -1 f164a43f --format=%cI (PR #605 merge commit)",
        "completed_at_anchor_utc": canonical_now.isoformat(),
        "auto_run": True,
        "watcher_id": "nowic_at_validation_watcher",

        "label": label,
        "label_rationale": rationale,

        "metrics": {
            "pre_deploy_distribution_90d": {"values": {str(k):v for k,v in pre_dist.items()},
                                             "total": sum(pre_dist.values()), "entropy_bits": round(entropy(pre_dist),4)},
            "post_deploy_distribution": {"values": {str(k):v for k,v in post_dist.items()},
                                          "total": post_total, "entropy_bits": round(entropy(post_dist),4)},
            "spearman_body_vs_conf": rho,
            "n_pairs_for_spearman": len(pairs_body_conf),
            "outcome_buckets_post_deploy": bucket_summary,
            "n_resolved_total": n_resolved_total,
            "fire_rate": {"pre_per_h": round(rate_pre,4), "post_per_h": round(rate_post,4),
                          "pct_change": round(pct_change,2) if pct_change is not None else None,
                          "regression_over_20pct": regression},
            "confidence_breakdown_present": f"{breakdown_present}/{len(fire_rows)}",
            "confidence_breakdown_rate": breakdown_rate,
            "confidence_breakdown_sample": sample_breakdown,
            "guardrail_hits": guardrail_hits,
            "fault_count": fault_count,
            "hours_post_deploy": round(hours_post, 2),
        },
        "constraints_held": [
            "Single watcher only (nowic_at_validation_watcher)",
            "nowic_at_m15 only",
            "READ-ONLY validation",
            "UTC discipline: cycle_ts canonical anchor",
            "Did NOT modify live-consumed strategy health key",
            "Did NOT update Falcon or Helios config",
            "Did NOT enable NOWIC_RT, whipsaw, Phase 3",
            "Did NOT change health weighting or execution authority",
            "Did NOT self-clear r2d2:blocker:autonomous_cron_publishing"
        ]
    }
    return label, report


def main():
    try:
        label, report = run_validation()
        report_id = report["report_id"]
        fabric_set(report_id, report)
        fabric_set("r2d2:audit:nowic_at_m15_formula_validation:latest", report)
        state = fabric_get("r2d2:watcher:nowic_at_validation:state") or {}
        state["status"] = "DISABLED"
        state["final_label"] = label
        state["final_label_published_at_utc"] = report["completed_at_anchor_utc"]
        state["auto_disable_reason"] = "FINAL_LABEL_PUBLISHED"
        history = state.get("history", [])
        history.append({"event": "validation_complete", "label": label,
                        "anchor_utc": report["completed_at_anchor_utc"]})
        state["history"] = history
        fabric_set("r2d2:watcher:nowic_at_validation:state", state)
        print(f"LABEL={label}")
        print(f"REPORT_ID={report_id}")
        return 0
    except Exception as e:
        err_state = fabric_get("r2d2:watcher:nowic_at_validation:state") or {}
        err_state.setdefault("errors", []).append({"exception": str(e),
                                                    "context": "nowic_at_validation_full.py main()"})
        try: fabric_set("r2d2:watcher:nowic_at_validation:state", err_state)
        except Exception: pass
        print(f"ERROR={e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
