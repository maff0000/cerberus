#!/usr/bin/env python3
"""PLUTUS Safety Canary — PRE-FLIGHT.

Snapshot F4 SACRED invariants + namespace inventory. Persist to
plutus.safety_canary_runs (PRE) and mirror to sim_broker:reports:safety:<run_id>:v1.

Exit codes:
  0  PASS — engine may proceed
  1  FAIL — engine MUST refuse to start

Modes:
  --mode engine_start  (requires --run-id)
  --mode cron          (run_id auto-derived: cron-<utcstamp>)

Design source-of-truth: sim_broker:design:safety_canary:v1
WO: WO-PLUTUS-V1-1A
"""
from __future__ import annotations

import argparse
import json
import sys

from _common import (  # noqa: E402  (sibling import)
    collect_snapshot_errors,
    db_insert_canary_run,
    discord_alert,
    get_db_connection,
    mirror_to_fabric,
    snapshot_for_persistence,
    take_snapshot,
    utc_now_compact,
)

WO = "WO-PLUTUS-V1-1A"


def main() -> int:
    parser = argparse.ArgumentParser(description="PLUTUS safety canary pre-flight")
    parser.add_argument("--mode", choices=["engine_start", "cron"], required=True)
    parser.add_argument("--run-id", default=None,
                        help="Required when --mode engine_start")
    parser.add_argument("--no-db", action="store_true",
                        help="Skip DB write (useful for smoke-tests before migration lands)")
    parser.add_argument("--print-snapshot", action="store_true",
                        help="Print the snapshot JSON to stdout (debug)")
    args = parser.parse_args()

    if args.mode == "engine_start" and not args.run_id:
        sys.stderr.write("ERROR: --run-id required when --mode engine_start\n")
        return 1

    run_id = args.run_id or f"cron-{utc_now_compact()}"
    phase = "PRE" if args.mode == "engine_start" else "CRON"

    snapshot = take_snapshot()
    snapshot_persist = snapshot_for_persistence(snapshot)
    errors = collect_snapshot_errors(snapshot)

    outcome = "FAIL" if errors else "PASS"
    fail_reasons = [{"reason_code": e, "detail": ""} for e in errors] if errors else None

    # DB write (best-effort if --no-db)
    db_id = None
    db_skip_reason = None
    if not args.no_db:
        conn, err = get_db_connection()
        if conn is None:
            db_skip_reason = err
            sys.stderr.write(f"[pre_flight] DB write skipped: {err}\n")
        else:
            try:
                db_id = db_insert_canary_run(
                    conn,
                    run_id=run_id,
                    phase=phase,
                    snapshot_json=json.dumps(snapshot_persist),
                    diff_json=None,
                    outcome=outcome,
                    fail_reasons_json=json.dumps(fail_reasons) if fail_reasons else None,
                )
            finally:
                conn.close()

    mirror_key = mirror_to_fabric(
        run_id_or_cron_id=run_id,
        wo=WO,
        pre={"snapshot": snapshot_persist, "outcome": outcome, "phase": phase,
             "db_canary_id": db_id, "db_skip_reason": db_skip_reason},
        post=None,
        diff=None,
        outcome="PENDING" if outcome == "PASS" else "FAIL",
        fail_reasons=fail_reasons,
    )

    if args.print_snapshot:
        print(json.dumps(snapshot_persist, indent=2, default=str))

    if outcome == "FAIL":
        discord_alert(fail_reasons, wo=WO, run_id=run_id)
        sys.stderr.write(
            f"[pre_flight] FAIL run_id={run_id} reasons={errors} mirror={mirror_key}\n"
        )
        return 1

    sys.stdout.write(
        f"[pre_flight] PASS run_id={run_id} phase={phase} mirror={mirror_key}\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
