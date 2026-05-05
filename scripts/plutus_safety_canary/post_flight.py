#!/usr/bin/env python3
"""PLUTUS Safety Canary — POST-FLIGHT.

Re-snapshot, diff against PRE for same run_id. FAIL loud on ANY divergence.

Exit codes:
  0  PASS — run valid
  1  FAIL — run marked invalid; Discord critical alert fires (rate-limited)

Design source-of-truth: sim_broker:design:safety_canary:v1
WO: WO-PLUTUS-V1-1A
"""
from __future__ import annotations

import argparse
import json
import sys

from _common import (  # noqa: E402
    db_get_pre_snapshot,
    db_insert_canary_run,
    discord_alert,
    fabric_get,
    get_db_connection,
    is_allowed_namespace,
    mirror_to_fabric,
    snapshot_for_persistence,
    take_snapshot,
)

WO = "WO-PLUTUS-V1-1A"


def diff_snapshots(pre: dict, post: dict) -> tuple[list[dict], dict]:
    """Return (fail_reasons, diff_summary).

    Reasons (per design §2):
      F4_VIOLATION_PROP_TRADES_COUNT_CHANGED
      F4_VIOLATION_PROP_TRADES_KEYS_CHANGED
      F4_VIOLATION_AGENT_SMITH_REGISTRY_CHANGED
      F4_VIOLATION_EXECUTOR_BINARY_CHANGED
      NAMESPACE_ISOLATION_VIOLATION (per offending key)
    """
    reasons: list[dict] = []
    diff: dict = {}

    # F4: prop_trades count
    pre_pt = pre.get("prop_trades", {})
    post_pt = post.get("prop_trades", {})
    if pre_pt.get("count") != post_pt.get("count"):
        diff["prop_trades_count"] = {"pre": pre_pt.get("count"), "post": post_pt.get("count")}
        reasons.append({
            "reason_code": "F4_VIOLATION_PROP_TRADES_COUNT_CHANGED",
            "detail": f"pre={pre_pt.get('count')} post={post_pt.get('count')}",
        })

    # F4: prop_trades key list (catches additions/deletions/renames even at same count)
    if pre_pt.get("key_list_sha256") != post_pt.get("key_list_sha256"):
        diff["prop_trades_key_list_sha256"] = {
            "pre": pre_pt.get("key_list_sha256"),
            "post": post_pt.get("key_list_sha256"),
        }
        reasons.append({
            "reason_code": "F4_VIOLATION_PROP_TRADES_KEYS_CHANGED",
            "detail": "key list SHA differs (additions/deletions/renames)",
        })

    # F4: agent_smith registry
    pre_as = pre.get("agent_smith_registry", {})
    post_as = post.get("agent_smith_registry", {})
    if pre_as.get("sha256") != post_as.get("sha256"):
        diff["agent_smith_registry_sha256"] = {
            "pre": pre_as.get("sha256"),
            "post": post_as.get("sha256"),
        }
        reasons.append({
            "reason_code": "F4_VIOLATION_AGENT_SMITH_REGISTRY_CHANGED",
            "detail": f"key={pre_as.get('key')}",
        })

    # F4: executor binary SHA (mtime ignored — only content matters)
    pre_ex = pre.get("executor", {})
    post_ex = post.get("executor", {})
    if pre_ex.get("sha256") != post_ex.get("sha256"):
        diff["executor_sha256"] = {"pre": pre_ex.get("sha256"), "post": post_ex.get("sha256")}
        reasons.append({
            "reason_code": "F4_VIOLATION_EXECUTOR_BINARY_CHANGED",
            "detail": f"path={pre_ex.get('path')}",
        })

    # Namespace isolation: new keys in POST that weren't in PRE, outside allowed namespaces
    pre_other = set(pre.get("namespace_inventory", {}).get("other_keys_full", []))
    post_other = set(post.get("namespace_inventory", {}).get("other_keys_full", []))
    new_keys_outside_allowed = sorted(post_other - pre_other)
    if new_keys_outside_allowed:
        diff["new_keys_outside_allowed"] = new_keys_outside_allowed[:100]
        for k in new_keys_outside_allowed:
            if not is_allowed_namespace(k):
                reasons.append({
                    "reason_code": "NAMESPACE_ISOLATION_VIOLATION",
                    "detail": k,
                })

    return reasons, diff


def main() -> int:
    parser = argparse.ArgumentParser(description="PLUTUS safety canary post-flight")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--no-db", action="store_true",
                        help="Skip DB read/write — fetch PRE from fabric mirror instead")
    parser.add_argument("--print-diff", action="store_true",
                        help="Print the diff JSON to stdout (debug)")
    args = parser.parse_args()

    run_id = args.run_id

    # POST snapshot
    post_snapshot = take_snapshot()

    # Load PRE snapshot — DB first, fabric mirror as fallback
    pre_snapshot = None
    pre_source = None
    db_skip_reason = None

    if not args.no_db:
        conn, err = get_db_connection()
        if conn is None:
            db_skip_reason = err
            sys.stderr.write(f"[post_flight] DB read failed: {err} — falling back to fabric mirror\n")
        else:
            try:
                pre_snapshot = db_get_pre_snapshot(conn, run_id)
                if pre_snapshot:
                    pre_source = "db"
            finally:
                conn.close()

    if pre_snapshot is None:
        mirror_key = f"sim_broker:reports:safety:{run_id}:v1"
        mirror = fabric_get(mirror_key)
        if mirror and isinstance(mirror.get("pre"), dict):
            pre_snapshot = mirror["pre"].get("snapshot")
            pre_source = "fabric_mirror"

    if pre_snapshot is None:
        reason = {
            "reason_code": "POST_FLIGHT_PRE_SNAPSHOT_NOT_FOUND",
            "detail": f"run_id={run_id} not found in DB or fabric mirror",
        }
        discord_alert([reason], wo=WO, run_id=run_id)
        sys.stderr.write(f"[post_flight] FAIL run_id={run_id} — PRE snapshot not found\n")
        mirror_to_fabric(run_id, WO, pre=None,
                         post={"snapshot": snapshot_for_persistence(post_snapshot)},
                         diff=None, outcome="FAIL", fail_reasons=[reason])
        return 1

    fail_reasons, diff = diff_snapshots(pre_snapshot, post_snapshot)
    outcome = "FAIL" if fail_reasons else "PASS"

    post_persist = snapshot_for_persistence(post_snapshot)

    db_id = None
    if not args.no_db and db_skip_reason is None:
        conn, err = get_db_connection()
        if conn is not None:
            try:
                db_id = db_insert_canary_run(
                    conn,
                    run_id=run_id,
                    phase="POST",
                    snapshot_json=json.dumps(post_persist),
                    diff_json=json.dumps(diff) if diff else None,
                    outcome=outcome,
                    fail_reasons_json=json.dumps(fail_reasons) if fail_reasons else None,
                )
            finally:
                conn.close()

    mirror_key = mirror_to_fabric(
        run_id_or_cron_id=run_id,
        wo=WO,
        pre=None,  # don't overwrite existing PRE
        post={"snapshot": post_persist, "outcome": outcome, "db_canary_id": db_id,
              "pre_loaded_from": pre_source},
        diff=diff,
        outcome=outcome,
        fail_reasons=fail_reasons or None,
    )

    if args.print_diff:
        print(json.dumps(diff, indent=2, default=str))

    if outcome == "FAIL":
        discord_alert(fail_reasons, wo=WO, run_id=run_id)
        sys.stderr.write(
            f"[post_flight] FAIL run_id={run_id} reasons={[r['reason_code'] for r in fail_reasons]} mirror={mirror_key}\n"
        )
        return 1

    sys.stdout.write(f"[post_flight] PASS run_id={run_id} mirror={mirror_key}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
