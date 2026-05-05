#!/usr/bin/env python3
"""PLUTUS Safety Canary — POST-FLIGHT (v1.1, manifest-primary).

Diffs PRE manifest fields vs current manifest. FAIL loud on any divergence.

Failure reasons (per prod_guard:broker_path:manifest:schema:v1.consumer_failure_reasons):
  F4_VIOLATION_EXECUTOR_BINARY_CHANGED
  F4_VIOLATION_DISPATCHER_CHANGED
  F4_VIOLATION_OBSERVER_CHANGED
  F4_VIOLATION_AGENT_SMITH_REGISTRY_CHANGED
  F4_VIOLATION_PLUTUS_PRESENT_TRUE
  F4_VIOLATION_PLUTUS_PATHS_NON_EMPTY
  F4_VIOLATION_KNOWN_BROKERS_CHANGED
  F4_VIOLATION_MANIFEST_SHA_MISMATCH (re-validated each run)
  F4_VIOLATION_PROP_TRADES_COUNT_CHANGED
  F4_VIOLATION_PROP_TRADES_KEYS_CHANGED
  NAMESPACE_ISOLATION_VIOLATION
  FAIL_PREFLIGHT_MANIFEST_* (re-checked at POST)

Modes:
  --mode manual          (V1-1A canonical operator-callable post-flight)
  V1-2 will add: replay_complete

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
    validate_manifest,
)

WO = "WO-PLUTUS-V1-1A"

# (PRE-field, POST-field, reason_code) — both fields read from snapshot.manifest
MANIFEST_FIELD_DIFFS = [
    ("neo_ftmo_executor_sha", "F4_VIOLATION_EXECUTOR_BINARY_CHANGED"),
    ("neo_dispatcher_sha", "F4_VIOLATION_DISPATCHER_CHANGED"),
    ("neo_observer_sha", "F4_VIOLATION_OBSERVER_CHANGED"),
    ("agent_smith_registry_snapshot_sha", "F4_VIOLATION_AGENT_SMITH_REGISTRY_CHANGED"),
    ("known_brokers", "F4_VIOLATION_KNOWN_BROKERS_CHANGED"),
]


def diff_snapshots(pre: dict, post: dict, post_validation_errors: list[dict]) -> tuple[list[dict], dict]:
    """Return (fail_reasons, diff_summary)."""
    reasons: list[dict] = []
    diff: dict = {}

    # Manifest field diffs (PRE vs POST)
    pre_m = pre.get("manifest", {}) or {}
    post_m = post.get("manifest", {}) or {}
    for field, code in MANIFEST_FIELD_DIFFS:
        pv = pre_m.get(field)
        qv = post_m.get(field)
        if pv != qv:
            diff[f"manifest.{field}"] = {"pre": pv, "post": qv}
            reasons.append({
                "reason_code": code,
                "detail": f"pre={pv} post={qv}",
            })

    # plutus_present transition (false -> true)
    if pre_m.get("plutus_present") is False and post_m.get("plutus_present") is True:
        reasons.append({
            "reason_code": "F4_VIOLATION_PLUTUS_PRESENT_TRUE",
            "detail": "plutus_present transitioned false -> true during run",
        })

    # plutus_paths_observed transition ([] -> non-empty)
    pre_paths = pre_m.get("plutus_paths_observed") or []
    post_paths = post_m.get("plutus_paths_observed") or []
    if not pre_paths and post_paths:
        reasons.append({
            "reason_code": "F4_VIOLATION_PLUTUS_PATHS_NON_EMPTY",
            "detail": f"plutus_paths_observed transitioned []->{post_paths} during run",
        })

    # POST-side manifest invariants — if manifest went stale/missing/etc during run, surface
    # (avoid double-reporting MANIFEST_SHA_MISMATCH if already in field diffs above)
    seen_codes = {r["reason_code"] for r in reasons}
    for ve in post_validation_errors:
        if ve["reason_code"] not in seen_codes:
            reasons.append(ve)
            seen_codes.add(ve["reason_code"])

    # F4: prop_trades count
    pre_pt = pre.get("prop_trades", {})
    post_pt = post.get("prop_trades", {})
    if pre_pt.get("count") != post_pt.get("count"):
        diff["prop_trades_count"] = {"pre": pre_pt.get("count"), "post": post_pt.get("count")}
        reasons.append({
            "reason_code": "F4_VIOLATION_PROP_TRADES_COUNT_CHANGED",
            "detail": f"pre={pre_pt.get('count')} post={post_pt.get('count')}",
        })
    if pre_pt.get("key_list_sha256") != post_pt.get("key_list_sha256"):
        diff["prop_trades_key_list_sha256"] = {
            "pre": pre_pt.get("key_list_sha256"),
            "post": post_pt.get("key_list_sha256"),
        }
        reasons.append({
            "reason_code": "F4_VIOLATION_PROP_TRADES_KEYS_CHANGED",
            "detail": "key list SHA differs (additions/deletions/renames)",
        })

    # Namespace isolation: NEW keys in POST that weren't in PRE, outside allowed namespaces
    pre_other = set(pre.get("namespace_inventory", {}).get("other_keys_full", []))
    post_other = set(post.get("namespace_inventory", {}).get("other_keys_full", []))
    new_keys = sorted(post_other - pre_other)
    if new_keys:
        diff["new_keys_outside_allowed"] = new_keys[:100]
        for k in new_keys:
            if not is_allowed_namespace(k):
                reasons.append({
                    "reason_code": "NAMESPACE_ISOLATION_VIOLATION",
                    "detail": k,
                })

    return reasons, diff


def main() -> int:
    parser = argparse.ArgumentParser(description="PLUTUS safety canary post-flight (v1.1)")
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--mode",
        choices=["manual"],
        default="manual",
        help=("Post-flight mode. V1-1A: 'manual' (canonical operator-callable; "
              "ExecStopPost reuses this). V1-2 adds 'replay_complete'."),
    )
    parser.add_argument("--no-db", action="store_true",
                        help="Skip DB read/write — fall back to fabric mirror for PRE")
    parser.add_argument("--print-diff", action="store_true")
    args = parser.parse_args()

    run_id = args.run_id

    post_snapshot, post_validation_errors = take_snapshot()

    pre_snapshot = None
    pre_source = None
    db_skip_reason = None

    if not args.no_db:
        conn, err = get_db_connection()
        if conn is None:
            db_skip_reason = err
            sys.stderr.write(
                f"[post_flight] DB read failed: {err} — falling back to fabric mirror\n"
            )
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

    fail_reasons, diff = diff_snapshots(pre_snapshot, post_snapshot, post_validation_errors)
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
        pre=None,
        post={"snapshot": post_persist, "outcome": outcome, "db_canary_id": db_id,
              "pre_loaded_from": pre_source, "mode": args.mode,
              "post_validation_errors": post_validation_errors},
        diff=diff,
        outcome=outcome,
        fail_reasons=fail_reasons or None,
    )

    if args.print_diff:
        print(json.dumps(diff, indent=2, default=str))

    if outcome == "FAIL":
        discord_alert(fail_reasons, wo=WO, run_id=run_id)
        codes = [r["reason_code"] for r in fail_reasons]
        sys.stderr.write(
            f"[post_flight] FAIL run_id={run_id} reasons={codes} mirror={mirror_key}\n"
        )
        return 1

    sys.stdout.write(f"[post_flight] PASS run_id={run_id} mirror={mirror_key}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
