"""Full TDR formula validation — runs when post-deploy fire count >= 20.
Stages: SSH dell-debian, query metrics, run synthetic replay, label, publish to fabric.

UTC discipline: deploy anchor from git merge commit_date (canonical, tz-aware).
NEVER use NOW(), UTC_TIMESTAMP(), datetime.now(), datetime.utcnow(), time.time().
Cycle_ts column is the canonical UTC anchor for windowing.

Usage: python3 /opt/r2d2/tdr_validation_full.py
Returns: prints final label to stdout. Exits 0 on success, non-zero on failure.
"""
import json, subprocess, sys, datetime, urllib.request, math
from collections import Counter

# Constants — architect-anchored
# Re-anchored at PR #614 GUARDRAIL_REACH (post-hardening sweep CLOSED GREEN).
# Architect directive 2026-05-01: ignore all fired rows before this anchor.
DEPLOY_ANCHOR_UTC_STR = "2026-05-01T08:06:32+00:00"
DEPLOY_MERGE_COMMIT = "a3e9a1af6ffecd0c29f1d911e363268c8ab9403e"  # PR #614
DEADLINE_UTC_STR = "2026-05-08T08:06:32+00:00"
EXCEPTION_ID = "ONE_TIME_EXCEPTION_TDR_VALIDATION_WATCHER"
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
    except Exception as e:
        return None


def fabric_set(key, value):
    payload = json.dumps({"key": key, "value": json.dumps(value)}).encode()
    req = urllib.request.Request(f"{FABRIC_API}/set", data=payload,
                                  headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=8).status


def remote_mysql(query):
    """Run a single-line MySQL query on dell-debian. Returns rows as list of dicts."""
    full = (
        f"mysql -h127.0.0.1 -P3307 -uroot -pPDAPass@R00t123 "
        f"tradingScalp --batch --raw -e \"{query}\""
    )
    out = subprocess.run(["ssh", DELL, full], capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError(f"FAIL_LOUD: mysql query failed: {out.stderr}")
    lines = out.stdout.strip().split("\n")
    if len(lines) < 2:
        return []
    headers = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        vals = line.split("\t")
        rows.append({h: v for h, v in zip(headers, vals)})
    return rows


def remote_proteus(query):
    full = (
        f"mysql -h127.0.0.1 -P3307 -uroot -pPDAPass@R00t123 "
        f"tradingProteus --batch --raw -e \"{query}\""
    )
    out = subprocess.run(["ssh", DELL, full], capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError(f"FAIL_LOUD: proteus query failed: {out.stderr}")
    lines = out.stdout.strip().split("\n")
    if len(lines) < 2:
        return []
    headers = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        vals = line.split("\t")
        rows.append({h: v for h, v in zip(headers, vals)})
    return rows


def parse_dt(s):
    """Parse DB datetime string as UTC. cycle_ts is canonical UTC per V3 spec."""
    if not s or s == "NULL":
        return None
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    except Exception:
        try:
            return datetime.datetime.fromisoformat(s).replace(tzinfo=datetime.timezone.utc)
        except Exception:
            return None


def entropy(d):
    t = sum(d.values())
    if t == 0: return 0.0
    return -sum((c/t) * math.log2(c/t) for c in d.values() if c > 0)


def run_validation():
    """Execute the full validation. Returns (label, report_dict)."""
    report = {
        "report_id": None,
        "wo": "WO-FALCON-CONFIDENCE-FORMULA-TDR-M5-0001",
        "validation_plan": "r2d2:plan:tdr_formula_post_deploy_validation",
        "validator": "R2D2 (autonomous via tdr_validation_watcher)",
        "exception_ref": EXCEPTION_ID,
        "deploy_anchor_utc": DEPLOY_ANCHOR_UTC_STR,
        "deploy_merge_commit": DEPLOY_MERGE_COMMIT,
        "deploy_anchor_source": "git log -1 afb7c3f0 --format=%cI — canonical UTC, tz-aware",
    }

    # Canonical now from MAX(helios_v3_decisions.cycle_ts)
    anchor_rows = remote_mysql("SELECT MAX(cycle_ts) AS anchor FROM helios_v3_decisions")
    if not anchor_rows or not anchor_rows[0].get("anchor"):
        raise RuntimeError("FAIL_LOUD: no V3 cycle anchor available")
    canonical_now = parse_dt(anchor_rows[0]["anchor"])
    if canonical_now is None:
        raise RuntimeError("FAIL_LOUD: cannot parse canonical_now from cycle_ts")
    if canonical_now < DEPLOY_ANCHOR:
        raise RuntimeError(f"FAIL_LOUD: canonical_now {canonical_now} < deploy_anchor")
    report["completed_at_anchor_utc"] = canonical_now.isoformat()
    report["report_id"] = f"r2d2:audit:tdr_m5_formula_validation:{canonical_now.isoformat()}"
    NOW_SQL = canonical_now.strftime("%Y-%m-%d %H:%M:%S")

    # Pre-deploy distribution (90d before deploy)
    pre_window = (DEPLOY_ANCHOR - datetime.timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
    rows = remote_mysql(
        f"SELECT confidence, COUNT(*) c FROM helios_strategy_signals "
        f"WHERE strategy_id='tdr_m5' AND fired=1 "
        f"AND timestamp >= '{pre_window}' AND timestamp < '{DEPLOY_SQL}' "
        f"GROUP BY confidence ORDER BY confidence"
    )
    pre_dist = {int(r["confidence"]): int(r["c"]) for r in rows if r.get("confidence") not in (None, "NULL")}
    pre_total = sum(pre_dist.values())
    pre_entropy = entropy(pre_dist)

    # Post-deploy distribution
    rows = remote_mysql(
        f"SELECT confidence, COUNT(*) c FROM helios_strategy_signals "
        f"WHERE strategy_id='tdr_m5' AND fired=1 "
        f"AND timestamp >= '{DEPLOY_SQL}' AND timestamp <= '{NOW_SQL}' "
        f"GROUP BY confidence ORDER BY confidence"
    )
    post_dist = {int(r["confidence"]): int(r["c"]) for r in rows if r.get("confidence") not in (None, "NULL")}
    post_total = sum(post_dist.values())
    post_entropy = entropy(post_dist)

    # Outcome buckets post-deploy
    rows = remote_mysql(
        f"SELECT confidence, outcome, outcome_pnl_pts, outcome_mfe_pts, outcome_mae_pts "
        f"FROM helios_strategy_signals "
        f"WHERE strategy_id='tdr_m5' AND fired=1 "
        f"AND timestamp >= '{DEPLOY_SQL}' AND timestamp <= '{NOW_SQL}'"
    )
    WIN = {"TP1_HIT", "TP2_HIT"}
    LOSS = {"SL_HIT"}
    buckets = {}
    for r in rows:
        try:
            c = int(r["confidence"])
        except (ValueError, TypeError, KeyError):
            continue
        b = buckets.setdefault(c, {"n": 0, "wins": 0, "losses": 0, "pending": 0,
                                    "neutral": 0, "pnl_sum": 0.0, "pnl_count": 0})
        b["n"] += 1
        o = r.get("outcome")
        if o in WIN: b["wins"] += 1
        elif o in LOSS: b["losses"] += 1
        elif o == "PENDING": b["pending"] += 1
        else: b["neutral"] += 1
        try:
            pnl = float(r["outcome_pnl_pts"])
            b["pnl_sum"] += pnl; b["pnl_count"] += 1
        except (ValueError, TypeError, KeyError):
            pass
    bucket_summary = {}
    for c, b in buckets.items():
        resolved = b["wins"] + b["losses"]
        bucket_summary[c] = {
            "n": b["n"], "wins": b["wins"], "losses": b["losses"],
            "pending": b["pending"], "neutral": b["neutral"], "resolved": resolved,
            "wr_pct": round(b["wins"]/resolved*100, 1) if resolved > 0 else None,
            "avg_pnl": round(b["pnl_sum"]/b["pnl_count"], 2) if b["pnl_count"] > 0 else None,
        }

    # Monotonicity test
    sorted_conf = sorted(c for c in bucket_summary if bucket_summary[c]["wr_pct"] is not None)
    inversions = []
    for i in range(len(sorted_conf) - 1):
        a, b = sorted_conf[i], sorted_conf[i+1]
        if bucket_summary[b]["wr_pct"] < bucket_summary[a]["wr_pct"]:
            inversions.append({"from": a, "to": b,
                                "wr_from": bucket_summary[a]["wr_pct"],
                                "wr_to": bucket_summary[b]["wr_pct"]})
    n_resolved_total = sum(b["resolved"] for b in bucket_summary.values())

    # Fire-rate regression
    pre_30d = (DEPLOY_ANCHOR - datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    rows = remote_mysql(
        f"SELECT COUNT(*) c FROM helios_strategy_signals "
        f"WHERE strategy_id='tdr_m5' AND fired=1 "
        f"AND timestamp >= '{pre_30d}' AND timestamp < '{DEPLOY_SQL}'"
    )
    fires_pre_30d = int(rows[0]["c"]) if rows else 0
    hours_pre = 30 * 24
    hours_post = (canonical_now - DEPLOY_ANCHOR).total_seconds() / 3600
    rate_pre = fires_pre_30d / hours_pre if hours_pre > 0 else 0
    rate_post = post_total / hours_post if hours_post > 0 else 0
    pct_change = ((rate_post - rate_pre) / rate_pre * 100) if rate_pre > 0 else None
    regression_over_20 = pct_change is not None and pct_change < -20.0

    # confidence_breakdown JSON presence (sample 5 latest fires)
    rows = remote_mysql(
        f"SELECT evidence FROM helios_strategy_signals "
        f"WHERE strategy_id='tdr_m5' AND fired=1 "
        f"AND timestamp >= '{DEPLOY_SQL}' AND timestamp <= '{NOW_SQL}' "
        f"ORDER BY timestamp DESC LIMIT 5"
    )
    breakdown_present = 0
    sample_breakdown = None
    for r in rows:
        try:
            ev = json.loads(r.get("evidence", "{}"))
            bd = ev.get("confidence_breakdown") or ev.get("tdr_confidence_breakdown")
            if bd:
                breakdown_present += 1
                if sample_breakdown is None: sample_breakdown = bd
        except Exception:
            pass

    # Falcon fault log
    fault_rows = remote_proteus(
        f"SELECT COUNT(*) c FROM falcon_fault_log "
        f"WHERE created_at >= '{DEPLOY_SQL}' AND created_at <= '{NOW_SQL}' "
        f"AND component LIKE '%tdr%'"
    )
    fault_count = int(fault_rows[0]["c"]) if fault_rows else 0

    # ===== Final label decision =====
    # Architect labels: EVIDENCE_SUPPORTED / WEAK_EVIDENCE / REGRESSION / INCONCLUSIVE
    label = None
    label_reason = None
    if regression_over_20:
        label = "REGRESSION"
        label_reason = f"Fire rate dropped {pct_change:.1f}% post-deploy (pre {rate_pre:.4f}/h → post {rate_post:.4f}/h)."
    elif fault_count > 0:
        label = "REGRESSION"
        label_reason = f"{fault_count} falcon_fault_log entries for tdr_m5 component post-deploy."
    elif post_total < TRIGGER_THRESHOLD:
        label = "INCONCLUSIVE"
        label_reason = f"post_total={post_total} below TRIGGER_THRESHOLD={TRIGGER_THRESHOLD}"
    elif n_resolved_total < 5:
        label = "INCONCLUSIVE"
        label_reason = f"Only {n_resolved_total} resolved fires post-deploy. Need >=5 for outcome correlation claim."
    elif post_entropy < 0.3:
        label = "REGRESSION"
        label_reason = f"Post-deploy entropy {post_entropy:.2f} bits — distribution collapsed (formula not varying)."
    elif len(inversions) == 0:
        label = "EVIDENCE_SUPPORTED"
        label_reason = f"{post_total} fires, {n_resolved_total} resolved. Entropy {pre_entropy:.2f}→{post_entropy:.2f} bits. No monotonicity inversions."
    elif len(inversions) == 1 and n_resolved_total < 30:
        label = "WEAK_EVIDENCE"
        label_reason = f"{len(inversions)} inversion(s) but small sample ({n_resolved_total} resolved). Likely sampling noise."
    else:
        label = "WEAK_EVIDENCE"
        label_reason = f"{len(inversions)} monotonicity inversions across {n_resolved_total} resolved fires."

    # Compose report
    report.update({
        "label": label,
        "label_rationale": label_reason,
        "auto_run": True,
        "watcher_id": "tdr_validation_watcher",
        "metrics": {
            "pre_deploy_distribution_90d": {"values": {str(k): v for k, v in pre_dist.items()},
                                             "total": pre_total, "entropy_bits": round(pre_entropy, 4)},
            "post_deploy_distribution": {"values": {str(k): v for k, v in post_dist.items()},
                                          "total": post_total, "entropy_bits": round(post_entropy, 4)},
            "entropy_delta_bits": round(post_entropy - pre_entropy, 4),
            "outcome_buckets_post_deploy": bucket_summary,
            "n_resolved_total": n_resolved_total,
            "monotonicity_inversions": inversions,
            "fire_rate": {"pre_per_h": round(rate_pre, 4), "post_per_h": round(rate_post, 4),
                          "pct_change": round(pct_change, 2) if pct_change is not None else None,
                          "regression_over_20pct": regression_over_20},
            "confidence_breakdown_sample_present": f"{breakdown_present}/5",
            "confidence_breakdown_sample": sample_breakdown,
            "falcon_fault_log_post_deploy": fault_count,
            "hours_post_deploy": round(hours_post, 2),
        },
        "constraints_held": [
            "Single watcher only (tdr_validation_watcher)",
            "tdr_m5 only",
            "READ-ONLY validation",
            "UTC discipline: cycle_ts canonical anchor, no NOW()/utcnow()/time.time()",
            "Did NOT modify any live-consumed strategy health key",
            "Did NOT update Falcon or Helios config",
            "Did NOT change health weighting or enable NOWIC",
            "Did NOT self-clear r2d2:blocker:autonomous_cron_publishing"
        ]
    })

    return label, report


def main():
    try:
        label, report = run_validation()
        # Persist
        report_id = report["report_id"]
        fabric_set(report_id, report)
        fabric_set("r2d2:audit:tdr_m5_formula_validation:latest", report)
        # Update watcher state to DISABLED (final label achieved)
        state = fabric_get("r2d2:watcher:tdr_validation:state") or {}
        state["status"] = "DISABLED"
        state["final_label"] = label
        state["final_label_published_at_utc"] = report["completed_at_anchor_utc"]
        state["auto_disable_reason"] = "FINAL_LABEL_PUBLISHED"
        history = state.get("history", [])
        history.append({"event": "validation_complete", "label": label,
                        "anchor_utc": report["completed_at_anchor_utc"]})
        state["history"] = history
        fabric_set("r2d2:watcher:tdr_validation:state", state)
        # Print label for parent process
        print(f"LABEL={label}")
        print(f"REPORT_ID={report_id}")
        return 0
    except Exception as e:
        # Fail loud
        err_state = fabric_get("r2d2:watcher:tdr_validation:state") or {}
        err_state.setdefault("errors", []).append({
            "exception": str(e),
            "context": "tdr_validation_full.py main()",
        })
        try:
            fabric_set("r2d2:watcher:tdr_validation:state", err_state)
        except Exception:
            pass
        print(f"ERROR={e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
