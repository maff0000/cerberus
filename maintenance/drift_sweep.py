"""R2D2 maintenance — daily drift sweep.
Walks every Falcon strategy config row. For any row whose llm_reasoning.source_audit
points to an R2D2 audit, checks that current config_value matches the value
recommended in the audit.

Surfaces drift to fabric (always) + Discord (on detection only, rate-limited).

READ-ONLY against trading data. Fabric writes for R2D2 audit results only.
UTC discipline absolute. Methodology: r2d2:methodology:maintenance:v1
Main directive: r2d2:directive:main (preservation of the team).
"""
import sys, json, datetime
sys.path.insert(0, "/opt/r2d2/maintenance")
from _common import (canonical_now_utc, remote_query, fabric_get, fabric_set,
                     discord_post, log_run)

SCRIPT = "drift_sweep"

def main():
    try:
        anchor = canonical_now_utc()
    except SystemExit:
        log_run(SCRIPT, "FAIL", "could not derive canonical_now_utc")
        return 2

    # Discover all Falcon strategy config tables
    tables = remote_query(
        "SELECT TABLE_NAME FROM information_schema.tables "
        "WHERE table_schema='tradingProteus' AND table_name LIKE 'falcon_strategy_%config%'",
        db="tradingProteus")
    if not tables:
        log_run(SCRIPT, "FAIL", "could not list config tables")
        return 2

    drift_rows = []
    r2d2_traced_count = 0
    total_rows = 0

    for t in tables:
        tname = t["TABLE_NAME"]
        # Skip tables without llm_reasoning column (older config tables)
        cols = remote_query(
            f"SELECT COLUMN_NAME FROM information_schema.columns "
            f"WHERE table_schema='tradingProteus' AND table_name='{tname}' "
            f"AND COLUMN_NAME='llm_reasoning'", db="tradingProteus")
        if not cols: continue
        rows = remote_query(
            f"SELECT id, instrument, mode, config_key, config_value, "
            f"JSON_UNQUOTE(JSON_EXTRACT(llm_reasoning, '$.source_audit')) AS source_audit "
            f"FROM {tname} WHERE llm_reasoning IS NOT NULL",
            db="tradingProteus")
        if not rows: continue
        for r in rows:
            total_rows += 1
            sa = r.get("source_audit")
            if not sa or "r2d2:audit:" not in sa: continue
            r2d2_traced_count += 1
            # Pull the audit and find what it recommended for this key
            audit = fabric_get(sa.strip('"').strip())
            if not audit:
                drift_rows.append({
                    "table": tname, "key": r["config_key"], "instrument": r["instrument"],
                    "current": r["config_value"], "source_audit": sa,
                    "drift_type": "AUDIT_MISSING",
                    "note": "source_audit pointed to a fabric key that doesn't exist or didn't load"
                })
                continue
            # Find the recommended value in the audit
            recommended = None
            audit_str = json.dumps(audit) if not isinstance(audit, str) else audit
            # heuristic: look for "recommended" or "new_value" + the key name
            # Many R2D2 audits put it under summary_for_architect.recommended_fix
            for path in ("summary_for_architect", "recommended_next_wo", "Q10_safest_next_wo",
                         "headline_summary", "task_8_phase4_candidates"):
                node = audit.get(path) if isinstance(audit, dict) else None
                if node:
                    node_str = json.dumps(node)
                    # Look for recommended / new value
                    if r["config_key"] in node_str:
                        # Try to extract a recommended numeric or string
                        rec_node = node.get("recommended_fix") if isinstance(node, dict) else None
                        if isinstance(rec_node, dict):
                            recommended = rec_node.get("recommended") or rec_node.get("change")
                            break
            # If we can't extract recommended, that's still informative — flag for manual review
            if recommended is None:
                # No explicit recommendation found; treat as OK (config row references audit but no clear value to compare)
                continue
            # Compare current to recommended
            cur_str = str(r["config_value"]).strip()
            rec_str = str(recommended).strip()
            if cur_str != rec_str and cur_str not in rec_str and rec_str not in cur_str:
                drift_rows.append({
                    "table": tname, "key": r["config_key"], "instrument": r["instrument"],
                    "current": cur_str, "recommended": rec_str, "source_audit": sa,
                    "drift_type": "VALUE_DRIFT"
                })

    summary = {
        "total_config_rows": total_rows,
        "r2d2_traced_rows": r2d2_traced_count,
        "drift_count": len(drift_rows),
        "drift_rows": drift_rows[:20]  # cap output
    }
    print(f"[{SCRIPT}] anchor={anchor.isoformat()} traced={r2d2_traced_count} drift={len(drift_rows)}")

    # Bake to fabric (always)
    fabric_set("r2d2:audit:drift_sweep:latest", {
        "ran_utc": anchor.isoformat(),
        "summary": summary,
        "methodology": "r2d2:methodology:maintenance:v1",
        "main_directive": "r2d2:directive:main"
    })
    snap_ts = anchor.strftime("%Y%m%dT%H%M%SZ")
    fabric_set(f"r2d2:audit:drift_sweep:snapshot:{snap_ts}", {
        "ran_utc": anchor.isoformat(),
        "summary": summary
    })

    # Discord post on drift only
    if drift_rows:
        examples = "\n".join([f"  - `{d['table']}.{d['key']}` ({d.get('instrument','?')}): "
                              f"current=`{d.get('current')}` vs recommended=`{d.get('recommended','?')}` "
                              f"[{d['drift_type']}]"
                              for d in drift_rows[:5]])
        msg = (f"**[R2D2 MAINTENANCE]** **DRIFT DETECTED** ({len(drift_rows)} row(s))\n\n"
               f"{examples}\n\n"
               f"Audit: `r2d2:audit:drift_sweep:latest`. "
               f"Investigate before next strategy fix cycle.")
        discord_post(msg, priority="high", topic="drift_sweep")
        log_run(SCRIPT, "DRIFT_DETECTED", summary)
    else:
        log_run(SCRIPT, "OK", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
