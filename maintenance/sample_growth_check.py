"""R2D2 maintenance — daily sample-growth check.
For each strategy in the latest Strategy Readiness Matrix labelled INSUFFICIENT_SAMPLE,
checks resolved-trade count delta since the matrix was baked. If any strategy crosses
n=20 resolved trades, flags it as eligible for label upgrade in the next refresh.

READ-ONLY against trading data. UTC discipline. Methodology: r2d2:methodology:maintenance:v1
Main directive: r2d2:directive:main (preservation of the team).
"""
import sys, json
sys.path.insert(0, "/opt/r2d2/maintenance")
from _common import (canonical_now_utc, remote_query, fabric_get, fabric_set,
                     discord_post, log_run)

SCRIPT = "sample_growth_check"
THRESHOLD = 20

def main():
    try:
        anchor = canonical_now_utc()
    except SystemExit:
        log_run(SCRIPT, "FAIL", "could not derive canonical_now_utc")
        return 2

    # Read the latest Matrix
    matrix_doc = fabric_get("r2d2:audit:falcon_strategy_readiness_matrix:latest")
    if not matrix_doc:
        log_run(SCRIPT, "FAIL", "no Matrix found at r2d2:audit:falcon_strategy_readiness_matrix:latest")
        return 2

    matrix = matrix_doc.get("matrix", {})
    insufficient = {sid: m for sid, m in matrix.items()
                    if m.get("readiness_label") == "INSUFFICIENT_SAMPLE"}

    if not insufficient:
        log_run(SCRIPT, "OK", "no INSUFFICIENT_SAMPLE strategies in current Matrix")
        return 0

    upgrades_eligible = []
    growth_rows = []
    for sid, m in insufficient.items():
        prior_resolved = m.get("resolved_count", 0)
        # Re-query current resolved count
        rows = remote_query(
            f"SELECT COUNT(*) AS n FROM helios_strategy_signals "
            f"WHERE strategy_id='{sid}' AND fired=1 AND outcome != 'PENDING'")
        if not rows: continue
        current_resolved = int(rows[0]["n"] or 0)
        delta = current_resolved - prior_resolved
        eligible = current_resolved >= THRESHOLD
        growth_rows.append({
            "strategy_id": sid,
            "prior_resolved": prior_resolved,
            "current_resolved": current_resolved,
            "delta": delta,
            "eligible_for_upgrade": eligible
        })
        if eligible:
            upgrades_eligible.append(sid)

    summary = {
        "anchor_utc": anchor.isoformat(),
        "matrix_baked_utc": matrix_doc.get("anchors", {}).get("canonical_now_utc"),
        "insufficient_strategies_checked": list(insufficient.keys()),
        "growth_rows": growth_rows,
        "upgrades_eligible": upgrades_eligible
    }
    print(f"[{SCRIPT}] checked={len(insufficient)} eligible_for_upgrade={len(upgrades_eligible)}")

    fabric_set("r2d2:audit:sample_growth_check:latest", {
        "ran_utc": anchor.isoformat(),
        "summary": summary,
        "methodology": "r2d2:methodology:maintenance:v1",
        "main_directive": "r2d2:directive:main"
    })

    # Discord post if any strategy crossed threshold
    if upgrades_eligible:
        msg = (f"**[R2D2 MAINTENANCE]** **Sample-growth threshold crossed** "
               f"({len(upgrades_eligible)} strategy/strategies)\n\n"
               f"Eligible for label upgrade: {', '.join(upgrades_eligible)}\n\n"
               f"Next Strategy Readiness Matrix refresh will re-evaluate. "
               f"Audit: `r2d2:audit:sample_growth_check:latest`")
        discord_post(msg, priority="normal", topic="sample_growth_check")
        log_run(SCRIPT, "UPGRADE_ELIGIBLE", summary)
    else:
        log_run(SCRIPT, "OK", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
