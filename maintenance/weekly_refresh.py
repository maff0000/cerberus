"""R2D2 maintenance — weekly refresh.
Re-runs the Strategy Readiness Matrix, dormant analysis, and drift sweep.
Bakes a weekly summary at r2d2:weekly:<date>.

Re-uses the canonical Matrix script via subprocess on dell-debian to keep one
source of truth for Matrix logic. Same pattern for dormant.

UTC discipline. Methodology: r2d2:methodology:maintenance:v1
Main directive: r2d2:directive:main (preservation of the team).
"""
import sys, json, subprocess
sys.path.insert(0, "/opt/r2d2/maintenance")
from _common import (canonical_now_utc, fabric_get, fabric_set, discord_post, log_run)

SCRIPT = "weekly_refresh"
MATRIX_SCRIPT = "/tmp/r2d2_strategy_readiness_matrix.py"
SSH = "root@192.168.11.10"


def main():
    try:
        anchor = canonical_now_utc()
    except SystemExit:
        log_run(SCRIPT, "FAIL", "could not derive canonical_now_utc")
        return 2

    # Snapshot prior Matrix labels for change detection
    prior_matrix = fabric_get("r2d2:audit:falcon_strategy_readiness_matrix:latest")
    prior_labels = {}
    if prior_matrix and isinstance(prior_matrix.get("matrix"), dict):
        prior_labels = {sid: m.get("readiness_label")
                        for sid, m in prior_matrix["matrix"].items()}

    # Re-run the Matrix script on dell-debian (where the data is)
    print(f"[{SCRIPT}] anchor={anchor.isoformat()} — re-running Matrix on dell-debian")
    result = subprocess.run(
        ["ssh", SSH, "cd /srv-dev && python3 /tmp/r2d2_strategy_readiness_matrix.py"],
        capture_output=True, text=True, timeout=120)
    matrix_status = "OK" if result.returncode == 0 else "FAIL"

    # Re-pull fresh Matrix from fabric
    new_matrix = fabric_get("r2d2:audit:falcon_strategy_readiness_matrix:latest")
    new_labels = {}
    if new_matrix and isinstance(new_matrix.get("matrix"), dict):
        new_labels = {sid: m.get("readiness_label")
                      for sid, m in new_matrix["matrix"].items()}

    # Detect label changes
    label_changes = []
    for sid in set(prior_labels.keys()) | set(new_labels.keys()):
        old = prior_labels.get(sid)
        new = new_labels.get(sid)
        if old != new:
            label_changes.append({"strategy_id": sid, "old": old, "new": new})

    # Run drift sweep + sample growth as part of weekly
    drift_result = subprocess.run(
        ["python3", "/opt/r2d2/maintenance/drift_sweep.py"],
        capture_output=True, text=True, timeout=120)
    growth_result = subprocess.run(
        ["python3", "/opt/r2d2/maintenance/sample_growth_check.py"],
        capture_output=True, text=True, timeout=120)

    drift_doc = fabric_get("r2d2:audit:drift_sweep:latest") or {}
    growth_doc = fabric_get("r2d2:audit:sample_growth_check:latest") or {}

    week_summary = {
        "ran_utc": anchor.isoformat(),
        "matrix_status": matrix_status,
        "label_changes": label_changes,
        "drift_count": (drift_doc.get("summary") or {}).get("drift_count", 0),
        "upgrades_eligible": (growth_doc.get("summary") or {}).get("upgrades_eligible", []),
        "components_run": ["matrix", "drift_sweep", "sample_growth_check"]
    }
    print(f"[{SCRIPT}] matrix={matrix_status} label_changes={len(label_changes)} "
          f"drift={week_summary['drift_count']} upgrades_eligible={len(week_summary['upgrades_eligible'])}")

    week_key = f"r2d2:weekly:{anchor.strftime('%Y%m%d')}"
    fabric_set(week_key, {
        "ran_utc": anchor.isoformat(),
        "summary": week_summary,
        "methodology": "r2d2:methodology:maintenance:v1",
        "main_directive": "r2d2:directive:main"
    })
    fabric_set("r2d2:weekly:latest", {
        "ran_utc": anchor.isoformat(),
        "summary": week_summary,
        "snapshot_key": week_key
    })

    # Discord post only if anything material changed
    if label_changes or week_summary["drift_count"] or week_summary["upgrades_eligible"]:
        parts = ["**[R2D2 MAINTENANCE]** Weekly refresh complete."]
        if label_changes:
            parts.append(f"\n**Strategy label changes** ({len(label_changes)}):")
            for c in label_changes[:5]:
                parts.append(f"  - {c['strategy_id']}: {c['old']} → {c['new']}")
        if week_summary["drift_count"]:
            parts.append(f"\n**Drift detected:** {week_summary['drift_count']} config row(s) — see `r2d2:audit:drift_sweep:latest`")
        if week_summary["upgrades_eligible"]:
            parts.append(f"\n**Sample-growth eligible:** {', '.join(week_summary['upgrades_eligible'])}")
        parts.append(f"\n\nWeek snapshot: `{week_key}`")
        discord_post("\n".join(parts), priority="normal", topic="weekly_refresh")
        log_run(SCRIPT, "MATERIAL_CHANGES", week_summary)
    else:
        log_run(SCRIPT, "OK_NO_CHANGES", week_summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
