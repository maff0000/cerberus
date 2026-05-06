#!/usr/bin/env python3
"""V1-2 Deterministic Replay Acceptance Harness — T-DET-1 through T-DET-6.

Source of truth: locked design at sim_broker:design:deterministic_replay_core:v1
(locked 2026-05-06T01:40Z; pre-lock snapshot at :snapshot:20260506T013500Z_pre_lock).

Mapping to V1-2 R2_ACCEPTED bar (architect-locked):
  T-DET-1 -> bar #4 same scenario+seed -> byte-identical artefacts
  T-DET-2 -> bar #5 different seed -> different tick path (3 assertions: hash != + >=20% price + >=20% sim_ts)
  T-DET-3 -> bar #7 V1-1A canary BEFORE replay (PRE row in safety_canary_runs)
  T-DET-4 -> bar #8 V1-1A canary PASSES AFTER replay (POST row PASS)
  T-DET-5 -> bar #3 missing deterministic config fails loud (multiple sub-cases per §12)
  T-DET-6 -> architect watch-out 9: dataset_hash hashes actual rows (independent recomputation)

Stage status:
  T-DET-6 IMPLEMENTABLE NOW (independent of Rogue's CLI; only needs HERMES read + a row in plutus.replay_runs)
  T-DET-1/2/3/4/5 STUB UNTIL Rogue's mt5_plutus replay CLI is BUILT

Usage:
  python3 det_acceptance.py --only T-DET-6 --scenario tdr_validation_2026_03_28 --seed 42
  python3 det_acceptance.py            # full suite (after BUILT)
"""
from __future__ import annotations

import argparse
import json
import sys

from _common import (  # noqa: E402
    ARTEFACT_EXCLUDED,
    compute_dataset_hash_independent,
    fabric_set,
    get_plutus_db,
    get_run_metadata,
    hash_replay_artefact,
    spawn_replay_run,
    utc_now_iso,
)


def assert_outcome(actual, expected, label: str) -> bool:
    ok = actual == expected
    print(f"  {'PASS' if ok else 'FAIL'}: {label} (got {actual!r}, expected {expected!r})")
    return ok


def t_det_1_byte_identical(scenario_id: str, seed: int) -> bool:
    """Bar #4: same scenario+seed -> byte-identical artefacts.

    STUB UNTIL Rogue's CLI is BUILT. Spawns 2 replay runs, hashes 5 artefact tables
    per locked §11, asserts equality.
    """
    print("\n--- T-DET-1: same scenario+seed -> byte-identical artefacts ---")
    print("  STUB: requires Rogue's mt5_plutus replay CLI (BUILT phase)")
    rc_a, _, err_a = spawn_replay_run(scenario_id, seed)
    if rc_a != 0:
        print(f"  ABORT: replay A failed: {err_a[:200]}")
        return False
    rc_b, _, err_b = spawn_replay_run(scenario_id, seed)
    if rc_b != 0:
        print(f"  ABORT: replay B failed: {err_b[:200]}")
        return False
    # TODO post-BUILT: extract run_ids from CLI stdout/return; hash 5 artefacts; assert equal.
    print("  TODO: extract run_ids, hash artefacts, assert equal across 5 tables")
    return False  # STUB returns False until implemented


def t_det_2_seed_divergence(scenario_id: str, seed_a: int, seed_b: int) -> bool:
    """Bar #5 + locked T-DET-2 wording (3 assertions).

    For same scenario/config/source/code_ref with different seed:
      1. artefact_hash must differ
      2. >=20% of generated ticks have different rounded price output (bid)
      3. >=20% of generated ticks have different sim_ts output

    STUB UNTIL Rogue's CLI is BUILT.
    """
    print("\n--- T-DET-2: different seed -> different tick path (3 assertions) ---")
    print("  STUB: requires Rogue's mt5_plutus replay CLI (BUILT phase)")
    return False  # STUB


def t_det_3_canary_pre(scenario_id: str, seed: int) -> bool:
    """Bar #7: V1-1A canary runs BEFORE replay test.

    Verify plutus.safety_canary_runs has phase=PRE row for replay run_id with
    ran_at_utc earlier than first tick in plutus.replay_ticks for that run_id.

    STUB UNTIL Rogue's CLI is BUILT.
    """
    print("\n--- T-DET-3: V1-1A canary fires BEFORE replay ---")
    print("  STUB: requires Rogue's mt5_plutus replay CLI (BUILT phase)")
    return False  # STUB


def t_det_4_canary_post(scenario_id: str, seed: int) -> bool:
    """Bar #8: V1-1A canary PASSES AFTER replay test.

    Verify plutus.safety_canary_runs has phase=POST row for replay run_id with
    outcome=PASS, fail_reasons_json IS NULL, ran_at_utc later than last tick.

    STUB UNTIL Rogue's CLI is BUILT.
    """
    print("\n--- T-DET-4: V1-1A canary PASSES AFTER replay ---")
    print("  STUB: requires Rogue's mt5_plutus replay CLI (BUILT phase)")
    return False  # STUB


def t_det_5_fail_loud(scenario_id: str) -> bool:
    """Bar #3: missing deterministic config fails loud.

    Sub-cases (per locked §12):
      - missing seed -> FAIL_PREFLIGHT_DETERMINISTIC_SEED_MISSING
      - missing scenario_id -> FAIL_PREFLIGHT_DETERMINISTIC_SCENARIO_MISSING
      - naive datetime in source range without governed convention -> FAIL_TZ_AMBIGUOUS
      - future source_end -> FAIL_PREFLIGHT_DETERMINISTIC_SOURCE_RANGE_FUTURE
      - speed_factor != 1.0 -> FAIL_SPEED_FACTOR_FORBIDDEN OR DB CHECK violation

    STUB UNTIL Rogue's CLI is BUILT.
    """
    print("\n--- T-DET-5: fail-loud rules (multiple sub-cases) ---")
    print("  STUB: requires Rogue's mt5_plutus replay CLI (BUILT phase)")
    return False  # STUB


def t_det_6_dataset_hash_independent(run_id: str | None = None) -> bool:
    """Architect watch-out 9: dataset_hash hashes ACTUAL rows, not metadata.

    R2 reads HERMES candles independently for the run's source range, applies
    locked design §3 row_serialization_strict, sha256s, compares to declared
    dataset_hash in plutus.replay_runs.

    Implementable NOW (independent of Rogue's CLI) once a replay_runs row exists.
    """
    print("\n--- T-DET-6: dataset_hash independent recomputation ---")
    if run_id is None:
        print("  SKIP: requires --run-id of an existing plutus.replay_runs row")
        print("  (Rogue spawns first replay; pass that run_id back here for verification)")
        return True

    meta = get_run_metadata(run_id)
    if meta is None:
        print(f"  FAIL: run_id={run_id} not found in plutus.replay_runs")
        return False

    declared_hash = meta.get("dataset_hash")
    instrument = meta.get("instrument")
    source_start_utc = meta.get("source_start_utc")
    source_end_utc = meta.get("source_end_utc")

    print(f"  run_id={run_id}")
    print(f"  instrument={instrument}")
    print(f"  source_range={source_start_utc} -> {source_end_utc}")
    print(f"  declared_hash={declared_hash}")

    try:
        recomputed_hash, row_count = compute_dataset_hash_independent(
            instrument, str(source_start_utc), str(source_end_utc)
        )
    except Exception as e:  # pylint: disable=broad-except
        print(f"  FAIL: independent recomputation raised {type(e).__name__}: {e}")
        return False

    print(f"  recomputed_hash={recomputed_hash} (over {row_count} HERMES rows)")

    match = declared_hash == recomputed_hash
    fabric_set(f"r2d2:plutus:wo:2:acceptance:dataset_hash_independent:{run_id}:v1", {
        "run_id": run_id,
        "declared_hash": declared_hash,
        "recomputed_hash": recomputed_hash,
        "row_count": row_count,
        "match": match,
        "verdict": "PASS" if match else "FAIL",
        "checked_at_utc": utc_now_iso(),
        "source_table": "tradingSignals.candles_M1",
        "row_serialization_rule_applied": "locked design §3 row_serialization_strict",
    })

    return assert_outcome(match, True, "T-DET-6 declared == recomputed dataset_hash")


def main() -> int:
    parser = argparse.ArgumentParser(description="V1-2 deterministic replay acceptance harness")
    parser.add_argument("--only", choices=["T-DET-1", "T-DET-2", "T-DET-3", "T-DET-4",
                                            "T-DET-5", "T-DET-6"],
                        default=None, help="Run a single test")
    parser.add_argument("--scenario", default="tdr_validation_2026_03_28",
                        help="Scenario id for replay tests")
    parser.add_argument("--seed", type=int, default=42, help="Seed for primary replay")
    parser.add_argument("--seed-b", type=int, default=43, help="Second seed for T-DET-2")
    parser.add_argument("--run-id", default=None,
                        help="Existing replay_runs.run_id for T-DET-6 (skip if absent)")
    args = parser.parse_args()

    suite = [
        ("T-DET-1", lambda: t_det_1_byte_identical(args.scenario, args.seed)),
        ("T-DET-2", lambda: t_det_2_seed_divergence(args.scenario, args.seed, args.seed_b)),
        ("T-DET-3", lambda: t_det_3_canary_pre(args.scenario, args.seed)),
        ("T-DET-4", lambda: t_det_4_canary_post(args.scenario, args.seed)),
        ("T-DET-5", lambda: t_det_5_fail_loud(args.scenario)),
        ("T-DET-6", lambda: t_det_6_dataset_hash_independent(args.run_id)),
    ]
    if args.only:
        suite = [(n, fn) for n, fn in suite if n == args.only]

    results = []
    for name, fn in suite:
        try:
            ok = fn()
        except Exception as e:  # pylint: disable=broad-except
            import traceback
            print(f"\n  EXCEPTION in {name}: {type(e).__name__}: {e}")
            traceback.print_exc()
            ok = False
        results.append((name, ok))

    print("\n=== ACCEPTANCE SUMMARY ===")
    for name, ok in results:
        print(f"  {name}: {'PASS' if ok else 'FAIL/STUB'}")
    all_pass = all(ok for _, ok in results)
    print(f"\nOVERALL: {'GREEN' if all_pass else 'RED/STUB-PENDING'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
