"""R2D2 maintenance — daily correlation tracker.

Codifies direction-correctness checks: Spearman rho(confidence, outcome_pnl_pts)
per strategy with n_WL>=20 over 90d rolling window. Detects drift, flags
inversions, surfaces TRUSTED-threshold candidates as INFORMATIONAL ONLY.

READ-ONLY against trading data. Fabric writes only to r2d2:correlation_tracker:*.
NO strategy promotion. NO trader-layer consumption. NO V3-H3 closure.
NO HEALTH_ALLOWED_STATUSES change. NO HeliosV3 multiplier ramp.

UTC discipline absolute. Methodology: r2d2:methodology:correlation:v1
WO: WO-R2D2-CORRELATION-TRACKER-0001 (architect-ratified 2026-05-06)
Main directive: r2d2:directive:main (preservation of the team).
"""
import sys, json, datetime
from statistics import mean

sys.path.insert(0, "/opt/r2d2/maintenance")
from _common import (canonical_now_utc, remote_query, fabric_get, fabric_set,
                     discord_post, log_run)

SCRIPT = "correlation_tracker"

# Architect-approved minimum strategy set
STRATEGIES = [
    "nowic_at_m15",
    "nowic_rt_m15",
    "coil_breakout_m5",
    "whipsaw_fade_m5",
    "tdr_m5",
    "SF-002",
]

# Architect-approved direction label thresholds
N_WL_MIN = 20

# Architect-approved TRUSTED criteria (informational only)
TRUSTED_N_WL = 100
TRUSTED_RHO_MIN = 0.0  # strictly positive
TRUSTED_EXP_MIN = 0.5
TRUSTED_STABLE_RUNS = 3

# Architect-approved Discord severity gates (Q4)
DISCORD_RHO_DELTA_D7_THRESHOLD = -0.25
DISCORD_EXP_DELTA_D7_THRESHOLD = -1.0

# Architect-locked inverse quarantine — never auto-lifted
QUARANTINED_STRATEGIES = {"tdr_m5", "SF-002"}

# Snapshot trigger — write iff label changed OR rho_delta_d1 abs >= 0.10
SNAPSHOT_RHO_DELTA_THRESHOLD = 0.10

# Backfill window per architect Q2 amendment
BACKFILL_DAYS_PREFERRED = 30

# Rolling window for current run
ROLLING_WINDOW_DAYS = 90


def spearman_rho(xs, ys):
    """Spearman rank-correlation coefficient. Returns None if insufficient sample."""
    if len(xs) < 2 or len(xs) != len(ys):
        return None

    def ranks(values):
        # Average rank for ties (standard Spearman behaviour)
        n = len(values)
        sorted_idx = sorted(range(n), key=lambda i: values[i])
        rank_arr = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and values[sorted_idx[j + 1]] == values[sorted_idx[i]]:
                j += 1
            avg_rank = (i + j) / 2 + 1
            for k in range(i, j + 1):
                rank_arr[sorted_idx[k]] = avg_rank
            i = j + 1
        return rank_arr

    rx, ry = ranks(xs), ranks(ys)
    mx, my = mean(rx), mean(ry)
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(len(xs)))
    dx = sum((r - mx) ** 2 for r in rx) ** 0.5
    dy = sum((r - my) ** 2 for r in ry) ** 0.5
    if dx == 0 or dy == 0:
        return 0.0  # constant variable; no correlation
    return num / (dx * dy)


def fetch_strategy_data(strategy_id, window_end_utc, window_days=ROLLING_WINDOW_DAYS):
    """Fetch W/L sample for a strategy over the rolling window ending at window_end_utc.

    Returns list of dicts: [{confidence, outcome, outcome_pnl_pts}, ...]
    Read-only — no DB writes.
    """
    end_str = window_end_utc.strftime("%Y-%m-%d %H:%M:%S")
    start_str = (window_end_utc - datetime.timedelta(days=window_days)).strftime("%Y-%m-%d %H:%M:%S")
    sql = (
        f"SELECT confidence, outcome, outcome_pnl_pts "
        f"FROM helios_strategy_signals "
        f"WHERE strategy_id='{strategy_id}' "
        f"AND fired=1 "
        f"AND outcome IN ('TP1_HIT','SL_HIT') "
        f"AND timestamp >= '{start_str}' "
        f"AND timestamp <= '{end_str}' "
        f"AND outcome_pnl_pts IS NOT NULL "
        f"AND confidence IS NOT NULL"
    )
    rows = remote_query(sql)
    if rows is None:
        return None
    parsed = []
    for r in rows:
        try:
            parsed.append({
                "confidence": float(r["confidence"]),
                "outcome": r["outcome"],
                "outcome_pnl_pts": float(r["outcome_pnl_pts"]),
            })
        except (TypeError, ValueError):
            continue
    return parsed


def compute_per_strategy(strategy_id, sample):
    """Compute per-strategy metrics from W/L sample.

    Returns dict with all metric fields. n_WL < 20 returns INSUFFICIENT_SAMPLE.
    """
    n_WL = len(sample)
    out = {
        "strategy_id": strategy_id,
        "n_WL": n_WL,
        "wins": sum(1 for r in sample if r["outcome"] == "TP1_HIT"),
        "losses": sum(1 for r in sample if r["outcome"] == "SL_HIT"),
    }

    if n_WL < N_WL_MIN:
        out.update({
            "win_rate": None, "expectancy_pts": None, "rho": None,
            "monotonicity": None, "confidence_cohort_table": [],
            "direction_label": "INSUFFICIENT_SAMPLE",
        })
        return out

    out["win_rate"] = round(out["wins"] / n_WL, 4)
    out["expectancy_pts"] = round(mean(r["outcome_pnl_pts"] for r in sample), 4)

    confs = [r["confidence"] for r in sample]
    pnls = [r["outcome_pnl_pts"] for r in sample]
    rho = spearman_rho(confs, pnls)
    out["rho"] = round(rho, 4) if rho is not None else None

    # Confidence cohort table
    cohorts = {}
    for r in sample:
        c = r["confidence"]
        cohorts.setdefault(c, []).append(r)
    cohort_rows = []
    for c, rows in sorted(cohorts.items()):
        n = len(rows)
        wins = sum(1 for r in rows if r["outcome"] == "TP1_HIT")
        losses = sum(1 for r in rows if r["outcome"] == "SL_HIT")
        avg_pnl = round(mean(r["outcome_pnl_pts"] for r in rows), 4)
        cohort_rows.append({
            "confidence": c, "n": n, "wins": wins, "losses": losses,
            "win_rate": round(wins / n, 4) if n else None,
            "avg_pnl_pts": avg_pnl,
        })
    out["confidence_cohort_table"] = cohort_rows

    # Monotonicity (only meaningful with >=2 distinct confidence levels)
    if len(cohort_rows) >= 2:
        exps = [r["avg_pnl_pts"] for r in cohort_rows]
        if all(exps[i] < exps[i + 1] for i in range(len(exps) - 1)):
            out["monotonicity"] = "monotonic_positive"
        elif all(exps[i] > exps[i + 1] for i in range(len(exps) - 1)):
            out["monotonicity"] = "monotonic_negative"
        else:
            out["monotonicity"] = "non_monotonic"
    else:
        out["monotonicity"] = "single_confidence_only"

    # Inverse high-conf cohort check (TRUSTED gate)
    median_conf = sorted([r["confidence"] for r in cohort_rows])[len(cohort_rows) // 2] if cohort_rows else None
    high_conf_cohorts = [r for r in cohort_rows if r["confidence"] >= median_conf]
    inverse_high_conf = any(
        r.get("avg_pnl_pts", 0) < 0 or (r.get("win_rate") or 1) < 0.45
        for r in high_conf_cohorts
        if r["n"] >= 5  # ignore tiny cohorts
    ) if len(cohort_rows) >= 2 else False
    out["inverse_high_conf_cohort"] = inverse_high_conf

    return out


def assign_direction_label(metrics, prior_metrics=None):
    """Apply architect-approved direction label thresholds.

    Returns one of: POSITIVE, WEAK_POSITIVE, NEUTRAL, FADING, INVERSE_LEANING,
    INVERSE_CONFIRMED, INSUFFICIENT_SAMPLE.

    For QUARANTINED_STRATEGIES, INVERSE_CONFIRMED is sticky — only architect lifts.
    """
    if metrics["n_WL"] < N_WL_MIN:
        return "INSUFFICIENT_SAMPLE"

    rho = metrics["rho"]
    exp = metrics["expectancy_pts"]
    if rho is None or exp is None:
        return "INSUFFICIENT_SAMPLE"

    # Quarantine override (sticky per architect rule)
    if metrics["strategy_id"] in QUARANTINED_STRATEGIES:
        if rho <= -0.1 or exp < 0 or metrics.get("inverse_high_conf_cohort"):
            return "INVERSE_CONFIRMED"
        # Even if surface metrics improve, quarantine remains until architect lifts
        # We surface as INVERSE_LEANING to flag the persistent concern
        if rho <= 0.1:
            return "INVERSE_LEANING"

    # FADING check requires prior_metrics (drift signal)
    if prior_metrics:
        rho_delta_d7 = (rho - (prior_metrics.get("rho_d7") or rho)) if prior_metrics.get("rho_d7") is not None else 0
        exp_delta_d7 = (exp - (prior_metrics.get("expectancy_d7") or exp)) if prior_metrics.get("expectancy_d7") is not None else 0
        if rho_delta_d7 <= -0.15 or exp_delta_d7 <= -0.5:
            return "FADING"

    # Standard label thresholds (architect-approved)
    if rho >= 0.3 and exp > 0.5 and not metrics.get("inverse_high_conf_cohort"):
        return "POSITIVE"
    if 0.1 <= rho < 0.3 and exp > 0:
        return "WEAK_POSITIVE"
    if abs(rho) < 0.1 and abs(exp) < 0.5:
        return "NEUTRAL"
    if -0.3 < rho <= -0.1 and exp < 0:
        return "INVERSE_LEANING"
    if rho <= -0.3:
        return "INVERSE_CONFIRMED"

    # Default — fall through case (e.g. rho between -0.1 and 0 but exp positive)
    return "WEAK_POSITIVE" if exp > 0 else "NEUTRAL"


def check_trusted_threshold(metrics, history):
    """Check architect-approved TRUSTED criteria.

    ALL of: n>=100, rho>0, exp>0.5, no_inverse_high_conf_cohort, stable_3_runs.
    Returns True/False and a reason. INFORMATIONAL ONLY — does NOT promote.
    """
    if metrics["n_WL"] < TRUSTED_N_WL:
        return False, f"n_WL={metrics['n_WL']} < {TRUSTED_N_WL}"
    if (metrics["rho"] or -1) <= TRUSTED_RHO_MIN:
        return False, f"rho={metrics['rho']} not strictly positive"
    if (metrics["expectancy_pts"] or -99) <= TRUSTED_EXP_MIN:
        return False, f"expectancy={metrics['expectancy_pts']} <= {TRUSTED_EXP_MIN}"
    if metrics.get("inverse_high_conf_cohort"):
        return False, "inverse_high_conf_cohort detected"
    if metrics["strategy_id"] in QUARANTINED_STRATEGIES:
        return False, f"strategy is in QUARANTINED_STRATEGIES (architect-locked)"
    # stable_3_runs: rho_delta_d1 abs < 0.15 for last 3 runs
    if not history or len(history) < TRUSTED_STABLE_RUNS:
        return False, f"need {TRUSTED_STABLE_RUNS} prior runs for stability check; have {len(history) if history else 0}"
    recent_rhos = [h.get("rho") for h in history[-TRUSTED_STABLE_RUNS:] if h.get("rho") is not None]
    recent_rhos.append(metrics["rho"])
    if len(recent_rhos) < TRUSTED_STABLE_RUNS:
        return False, "insufficient rho history"
    deltas = [abs(recent_rhos[i + 1] - recent_rhos[i]) for i in range(len(recent_rhos) - 1)]
    if any(d >= 0.15 for d in deltas):
        return False, f"unstable: rho_delta abs {max(deltas):.3f} >= 0.15"
    return True, "ALL CRITERIA PASS — INFORMATIONAL ONLY (architect approval required to promote)"


def get_history(strategy_id, days_back=14):
    """Fetch last N days of history entries from fabric for drift computation."""
    history = []
    today = canonical_now_utc().date()
    for d in range(1, days_back + 1):
        date_str = (today - datetime.timedelta(days=d)).isoformat()
        entry = fabric_get(f"r2d2:correlation_tracker:{strategy_id}:history:{date_str}")
        if entry:
            history.append(entry)
    return history


def attach_drift(metrics, history):
    """Compute drift_d1 and drift_d7 deltas if history exists."""
    rho = metrics.get("rho")
    exp = metrics.get("expectancy_pts")
    out = {"rho_delta_d1": None, "rho_delta_d7": None,
           "expectancy_delta_d1": None, "expectancy_delta_d7": None,
           "rho_d1": None, "rho_d7": None,
           "expectancy_d1": None, "expectancy_d7": None}
    if rho is None or not history:
        return out

    # history[0] is most recent (d-1)
    if len(history) >= 1:
        h1 = history[0]
        if h1.get("rho") is not None:
            out["rho_d1"] = h1["rho"]
            out["rho_delta_d1"] = round(rho - h1["rho"], 4)
        if h1.get("expectancy_pts") is not None and exp is not None:
            out["expectancy_d1"] = h1["expectancy_pts"]
            out["expectancy_delta_d1"] = round(exp - h1["expectancy_pts"], 4)
    if len(history) >= 7:
        h7 = history[6]
        if h7.get("rho") is not None:
            out["rho_d7"] = h7["rho"]
            out["rho_delta_d7"] = round(rho - h7["rho"], 4)
        if h7.get("expectancy_pts") is not None and exp is not None:
            out["expectancy_d7"] = h7["expectancy_pts"]
            out["expectancy_delta_d7"] = round(exp - h7["expectancy_pts"], 4)
    return out


def should_snapshot(metrics_today, prior_today_in_fabric):
    """Snapshot trigger per design: label changed OR rho_delta_d1 abs >= 0.10."""
    if not prior_today_in_fabric:
        return True
    if prior_today_in_fabric.get("direction_label") != metrics_today.get("direction_label"):
        return True
    rho_d = metrics_today.get("rho_delta_d1") or 0
    return abs(rho_d) >= SNAPSHOT_RHO_DELTA_THRESHOLD


def should_discord(metrics_today, prior_label):
    """Discord severity gate per architect Q4."""
    label = metrics_today.get("direction_label")
    rho_d7 = metrics_today.get("rho_delta_d7") or 0
    exp_d7 = metrics_today.get("expectancy_delta_d7") or 0

    # New INVERSE_CONFIRMED on previously WATCH/positive strategy
    if label == "INVERSE_CONFIRMED" and prior_label not in ("INVERSE_CONFIRMED", "INVERSE_LEANING"):
        return True, f"NEW INVERSE_CONFIRMED on {metrics_today['strategy_id']} (was {prior_label})"

    # TRUSTED_THRESHOLD_REACHED
    if metrics_today.get("trusted_threshold_reached"):
        return True, f"TRUSTED_THRESHOLD_REACHED on {metrics_today['strategy_id']} (informational; architect approval required)"

    # Sharp degradation
    if rho_d7 <= DISCORD_RHO_DELTA_D7_THRESHOLD:
        return True, f"sharp rho degradation on {metrics_today['strategy_id']}: rho_delta_d7={rho_d7}"
    if exp_d7 <= DISCORD_EXP_DELTA_D7_THRESHOLD:
        return True, f"sharp expectancy degradation on {metrics_today['strategy_id']}: expectancy_delta_d7={exp_d7}"

    return False, None


def run_for_anchor(anchor_utc, write_history_for_date=None, force_no_history=False):
    """Run tracker for a specific anchor (current or backfill historical day).

    write_history_for_date: if set, also write to history:<date> key.
    force_no_history: if True, skip drift computation (used for first-day backfill).
    """
    results = []
    for sid in STRATEGIES:
        sample = fetch_strategy_data(sid, anchor_utc)
        if sample is None:
            results.append({"strategy_id": sid, "error": "DB query failed"})
            continue

        metrics = compute_per_strategy(sid, sample)

        # Drift (skip on backfill first-day where no history exists)
        if force_no_history:
            metrics.update({"rho_delta_d1": None, "rho_delta_d7": None,
                           "expectancy_delta_d1": None, "expectancy_delta_d7": None})
            history = []
        else:
            history = get_history(sid, days_back=14)
            metrics.update(attach_drift(metrics, history))

        # Direction label
        prior_label = (history[0].get("direction_label") if history else None)
        prior_for_fading = {
            "rho_d7": metrics.get("rho_d7"),
            "expectancy_d7": metrics.get("expectancy_d7"),
        }
        metrics["direction_label"] = assign_direction_label(metrics, prior_metrics=prior_for_fading)

        # TRUSTED check (informational)
        trusted_ok, reason = check_trusted_threshold(metrics, history)
        metrics["trusted_threshold_reached"] = trusted_ok
        metrics["trusted_check_reason"] = reason

        metrics["computed_at_utc"] = anchor_utc.isoformat()
        metrics["window_start_utc"] = (anchor_utc - datetime.timedelta(days=ROLLING_WINDOW_DAYS)).isoformat()
        metrics["window_end_utc"] = anchor_utc.isoformat()
        metrics["evidence_pointer"] = "ops/evidence/WO-R2D2-CORRELATION-TRACKER-0001/"
        metrics["wo"] = "WO-R2D2-CORRELATION-TRACKER-0001"
        metrics["methodology"] = "r2d2:methodology:correlation:v1"
        metrics["main_directive"] = "r2d2:directive:main"

        # Persist
        latest_key = f"r2d2:correlation_tracker:{sid}:latest"
        prior_today = fabric_get(latest_key)
        fabric_set(latest_key, metrics)

        if write_history_for_date:
            history_key = f"r2d2:correlation_tracker:{sid}:history:{write_history_for_date}"
            fabric_set(history_key, metrics)

        # Snapshot trigger
        if should_snapshot(metrics, prior_today):
            snap_key = f"r2d2:correlation_tracker:{sid}:snapshot:{anchor_utc.strftime('%Y%m%dT%H%M%SZ')}"
            fabric_set(snap_key, metrics)
            metrics["snapshot_written"] = snap_key

        # Discord check (only on live runs, not backfill)
        if not force_no_history:
            should_post, reason_msg = should_discord(metrics, prior_label)
            if should_post:
                topic = f"correlation_tracker_{sid}_{metrics['direction_label']}"
                msg = (
                    f"**[R2D2 EVIDENCE ALERT]** Correlation tracker — {reason_msg}\n\n"
                    f"Strategy: `{sid}`\n"
                    f"n_WL={metrics['n_WL']}, WR={metrics['win_rate']}, "
                    f"expectancy={metrics['expectancy_pts']} pts, rho={metrics['rho']}\n"
                    f"Direction: `{metrics['direction_label']}` (was `{prior_label}`)\n\n"
                    f"Audit: `{latest_key}`\n"
                    f"_R2D2 evidence; not trade advice._"
                )
                priority = "high" if metrics["direction_label"] in ("INVERSE_CONFIRMED", "FADING") else "normal"
                discord_post(msg, priority=priority, topic=topic)
                metrics["discord_alert_sent"] = True

        results.append(metrics)
    return results


def main():
    try:
        anchor = canonical_now_utc()
    except SystemExit:
        log_run(SCRIPT, "FAIL", "could not derive canonical_now_utc")
        return 2

    today_str = anchor.date().isoformat()

    # Detect first run via summary key
    summary_key = "r2d2:correlation_tracker:summary:latest"
    is_first_run = fabric_get(summary_key) is None

    # First-run backfill: write history for last 30 days
    backfill_summary = None
    if is_first_run:
        print(f"[{SCRIPT}] FIRST RUN — backfilling 30 days of history baseline")
        backfilled = 0
        for d in range(BACKFILL_DAYS_PREFERRED, 0, -1):
            backfill_anchor = anchor - datetime.timedelta(days=d)
            backfill_date_str = backfill_anchor.date().isoformat()
            try:
                run_for_anchor(backfill_anchor, write_history_for_date=backfill_date_str, force_no_history=True)
                backfilled += 1
            except Exception as e:
                print(f"[{SCRIPT}] backfill day {backfill_date_str} failed: {e}", file=sys.stderr)
        backfill_summary = {"backfilled_days": backfilled, "preferred": BACKFILL_DAYS_PREFERRED}
        print(f"[{SCRIPT}] backfill complete: {backfilled}/{BACKFILL_DAYS_PREFERRED} days")

    # Main run for today
    results = run_for_anchor(anchor, write_history_for_date=today_str)

    # Summary
    distribution = {}
    alerts_count = 0
    for r in results:
        lbl = r.get("direction_label", "ERROR")
        distribution[lbl] = distribution.get(lbl, 0) + 1
        if r.get("discord_alert_sent"):
            alerts_count += 1

    summary = {
        "ran_utc": anchor.isoformat(),
        "strategies_tracked": len(STRATEGIES),
        "distribution_by_direction_label": distribution,
        "alerts_generated": alerts_count,
        "is_first_run": is_first_run,
        "backfill_summary": backfill_summary,
        "wo": "WO-R2D2-CORRELATION-TRACKER-0001",
        "methodology": "r2d2:methodology:correlation:v1",
        "main_directive": "r2d2:directive:main",
        "constraints_honoured": {
            "no_strategy_promotion": True,
            "no_trader_layer_consumption": True,
            "v3_h3_open": True,
            "tdr_inverse_quarantine_preserved": True,
            "sf_002_inverse_quarantine_preserved": True,
            "read_only_DB": True,
        },
    }
    fabric_set(summary_key, summary)
    snap_ts = anchor.strftime("%Y%m%dT%H%M%SZ")
    fabric_set(f"r2d2:correlation_tracker:summary:snapshot:{snap_ts}", summary)

    print(f"[{SCRIPT}] anchor={anchor.isoformat()} dist={distribution} alerts={alerts_count}")
    log_run(SCRIPT, "OK", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
