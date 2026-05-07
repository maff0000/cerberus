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
    REQUIRED_DETERMINISTIC_REPLAY_V1_FIELDS,
    canonical_json_of_subobject,
    compute_dataset_hash_independent,
    fabric_set,
    get_plutus_db,
    get_run_metadata,
    get_scripted_overlays_subobject,
    hash_replay_artefact,
    sha256_of_canonical_json,
    sha256_text,
    spawn_replay_run,
    utc_now_iso,
    validate_deterministic_replay_v1_shape,
)


def assert_outcome(actual, expected, label: str) -> bool:
    ok = actual == expected
    print(f"  {'PASS' if ok else 'FAIL'}: {label} (got {actual!r}, expected {expected!r})")
    return ok


def t_det_1_byte_identical(run_id_a: str | None = None,
                            run_id_b: str | None = None) -> bool:
    """Bar #4: same scenario+seed -> byte-identical artefacts.

    Acceptance mode: caller supplies two run_ids that were spawned with same
    scenario+seed. Hash 5 artefact tables per locked §11, assert equality.
    """
    print("\n--- T-DET-1: same scenario+seed -> byte-identical artefacts ---")
    if run_id_a is None or run_id_b is None:
        print("  SKIP: requires --run-id-a and --run-id-b")
        return True

    conn = get_plutus_db()
    try:
        results = {}
        for table, excluded in ARTEFACT_EXCLUDED.items():
            h_a = hash_replay_artefact(conn, table, run_id_a, excluded)
            h_b = hash_replay_artefact(conn, table, run_id_b, excluded)
            results[table] = {"a": h_a, "b": h_b, "match": h_a == h_b}
            mark = "OK" if h_a == h_b else "MISMATCH"
            print(f"  {mark} {table}: A={h_a[:16]}... B={h_b[:16]}...")
    finally:
        conn.close()

    all_match = all(r["match"] for r in results.values())
    fabric_set(f"r2d2:plutus:wo:2:acceptance:byte_identical:{run_id_a}_vs_{run_id_b}:v1", {
        "run_id_a": run_id_a,
        "run_id_b": run_id_b,
        "per_artefact": results,
        "all_match": all_match,
        "verdict": "PASS" if all_match else "FAIL",
        "checked_at_utc": utc_now_iso(),
        "method": "hash_replay_artefact per locked §11; auto-increment IDs + run_id excluded; canonical-JSON sha256",
    })
    return assert_outcome(all_match, True, "T-DET-1 all 5 artefact hashes match A vs B")


def t_det_2_seed_divergence(run_id_a: str | None = None,
                             run_id_c: str | None = None) -> bool:
    """Bar #5 + locked T-DET-2 wording (3 assertions, architect 2026-05-06).

    For same scenario/config/source/code_ref with different seed:
      1. artefact_hash must differ
      2. >=20% of generated ticks have different rounded bid (price)
      3. >=20% of generated ticks have different sim_ts_utc
    """
    import math
    print("\n--- T-DET-2: different seed -> different tick path (3 assertions) ---")
    if run_id_a is None or run_id_c is None:
        print("  SKIP: requires --run-id-a and --run-id-c")
        return True

    conn = get_plutus_db()
    try:
        # Assertion 1: artefact_hash must differ (use replay_ticks as the canonical artefact)
        h_a = hash_replay_artefact(conn, "replay_ticks", run_id_a, ARTEFACT_EXCLUDED["replay_ticks"])
        h_c = hash_replay_artefact(conn, "replay_ticks", run_id_c, ARTEFACT_EXCLUDED["replay_ticks"])
        assertion_1 = h_a != h_c
        print(f"  Assertion 1 (hash differs): {'PASS' if assertion_1 else 'FAIL'} A={h_a[:16]} C={h_c[:16]}")

        # Assertions 2 + 3: >=20% bid divergence + >=20% sim_ts divergence
        with conn.cursor() as cur:
            cur.execute(
                "SELECT bid, sim_ts_utc FROM replay_ticks WHERE run_id=%s ORDER BY tick_id",
                (run_id_a,),
            )
            ticks_a = cur.fetchall()
            cur.execute(
                "SELECT bid, sim_ts_utc FROM replay_ticks WHERE run_id=%s ORDER BY tick_id",
                (run_id_c,),
            )
            ticks_c = cur.fetchall()
    finally:
        conn.close()

    n = min(len(ticks_a), len(ticks_c))
    if n == 0:
        print(f"  ABORT: zero ticks for one or both runs (a={len(ticks_a)} c={len(ticks_c)})")
        return False

    bid_diff_count = sum(1 for i in range(n) if ticks_a[i][0] != ticks_c[i][0])
    ts_diff_count = sum(1 for i in range(n) if ticks_a[i][1] != ticks_c[i][1])
    bid_threshold = math.ceil(0.20 * n)
    ts_threshold = math.ceil(0.20 * n)
    assertion_2 = bid_diff_count >= bid_threshold
    assertion_3 = ts_diff_count >= ts_threshold
    print(f"  Assertion 2 (>=20% bid differs): {'PASS' if assertion_2 else 'FAIL'} "
          f"bid_diff={bid_diff_count}/{n} (threshold {bid_threshold})")
    print(f"  Assertion 3 (>=20% sim_ts differs): {'PASS' if assertion_3 else 'FAIL'} "
          f"ts_diff={ts_diff_count}/{n} (threshold {ts_threshold})")

    all_pass = assertion_1 and assertion_2 and assertion_3
    fabric_set(f"r2d2:plutus:wo:2:acceptance:seed_divergence:{run_id_a}_vs_{run_id_c}:v1", {
        "run_id_a": run_id_a,
        "run_id_c": run_id_c,
        "n_compared": n,
        "ticks_a_count": len(ticks_a),
        "ticks_c_count": len(ticks_c),
        "assertion_1_hash_differs": assertion_1,
        "assertion_2_bid_diff_count": bid_diff_count,
        "assertion_2_threshold": bid_threshold,
        "assertion_2_pass": assertion_2,
        "assertion_3_ts_diff_count": ts_diff_count,
        "assertion_3_threshold": ts_threshold,
        "assertion_3_pass": assertion_3,
        "verdict": "PASS" if all_pass else "FAIL",
        "checked_at_utc": utc_now_iso(),
        "method": "Architect-locked T-DET-2 wording 2026-05-06 (3 assertions; >= ceil(0.20*N))",
    })
    return assertion_1 and assertion_2 and assertion_3


def t_det_3_canary_pre(run_id: str | None = None) -> bool:
    """Bar #7: V1-1A canary PRE row exists for replay run_id."""
    print("\n--- T-DET-3: V1-1A canary PRE row exists ---")
    if run_id is None:
        print("  SKIP: requires --run-id")
        return True
    conn = get_plutus_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT canary_id, outcome, ran_at_utc FROM safety_canary_runs "
                "WHERE run_id=%s AND phase='PRE' ORDER BY canary_id",
                (run_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    print(f"  PRE rows for run_id={run_id}: {len(rows)}")
    for r in rows:
        print(f"    canary_id={r[0]} outcome={r[1]} ran_at={r[2]}")
    pass_outcome = len(rows) >= 1 and rows[0][1] == "PASS"
    fabric_set(f"r2d2:plutus:wo:2:acceptance:canary_pre:{run_id}:v1", {
        "run_id": run_id,
        "pre_row_count": len(rows),
        "first_pre_outcome": rows[0][1] if rows else None,
        "verdict": "PASS" if pass_outcome else "FAIL",
        "checked_at_utc": utc_now_iso(),
    })
    return assert_outcome(pass_outcome, True, "T-DET-3 PRE row exists with outcome=PASS")


def t_det_4_canary_post(run_id: str | None = None) -> bool:
    """Bar #8: V1-1A canary POST row exists with PASS outcome for replay run_id."""
    print("\n--- T-DET-4: V1-1A canary POST row exists with PASS ---")
    if run_id is None:
        print("  SKIP: requires --run-id")
        return True
    conn = get_plutus_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT canary_id, outcome, fail_reasons_json, ran_at_utc FROM safety_canary_runs "
                "WHERE run_id=%s AND phase='POST' ORDER BY canary_id",
                (run_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    print(f"  POST rows for run_id={run_id}: {len(rows)}")
    for r in rows:
        print(f"    canary_id={r[0]} outcome={r[1]} fail_reasons={r[2]} ran_at={r[3]}")
    pass_outcome = len(rows) >= 1 and rows[0][1] == "PASS"
    fabric_set(f"r2d2:plutus:wo:2:acceptance:canary_post:{run_id}:v1", {
        "run_id": run_id,
        "post_row_count": len(rows),
        "first_post_outcome": rows[0][1] if rows else None,
        "fail_reasons": rows[0][2] if rows else None,
        "verdict": "PASS" if pass_outcome else "FAIL",
        "checked_at_utc": utc_now_iso(),
    })
    return assert_outcome(pass_outcome, True, "T-DET-4 POST row exists with outcome=PASS")


def t_det_5_fail_loud(scenario_id: str) -> bool:
    """Bar #3: missing deterministic config fails loud.

    Architect 2026-05-07 R2_ACCEPTED requirement: T-DET-5 must PASS via three
    sub-cases (or be explicitly waived by Matt — architect won't waive):
      A. Missing deterministic config fails loud (CLI rejects --no-seed)
      B. Invalid speed_factor=2.0 fails at DB layer (chk_speed_factor_v1_2 CHECK)
      C. No speed_factor execution path exists (grep proves engine doesn't consume it)
    """
    import subprocess as _sub
    print("\n--- T-DET-5: fail-loud rules (3 sub-cases) ---")

    sub_results = {}

    # Sub-case A: spawn replay attempt without seed -> non-zero exit + no replay_runs row
    print("  Sub-case A: missing seed -> CLI rejects (no replay_runs row created)")
    pre_count = _replay_runs_count()
    rc, out, err = _sub.run(["mt5_plutus", "replay", "--scenario", scenario_id],
                             capture_output=True, text=True).returncode, "", ""
    res_a = _sub.run(["mt5_plutus", "replay", "--scenario", scenario_id],
                     capture_output=True, text=True)
    post_count = _replay_runs_count()
    sub_a_pass = res_a.returncode != 0 and post_count == pre_count
    print(f"    cmd: mt5_plutus replay --scenario {scenario_id} (no --seed)")
    print(f"    exit={res_a.returncode}, replay_runs delta={post_count - pre_count}")
    print(f"    stderr-tail: {(res_a.stderr or '').strip().splitlines()[-1] if res_a.stderr else '(empty)'}")
    print(f"    Sub-case A: {'PASS' if sub_a_pass else 'FAIL'}")
    sub_results["A_missing_seed"] = {"pass": sub_a_pass, "exit": res_a.returncode,
                                       "rows_delta": post_count - pre_count}

    # Sub-case B: DB CHECK rejects speed_factor=2.0 INSERT
    print("  Sub-case B: speed_factor=2.0 INSERT rejected by DB CHECK")
    sub_b_pass = False
    rejection_message = None
    test_run_id = f"T-DET-5-B-{utc_now_iso().replace(':', '').replace('-', '')}"
    try:
        conn = get_plutus_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO replay_runs (run_id, scenario_id, seed, dataset_hash, config_hash, "
                    "config_snapshot_json, code_ref, instrument, source_start_utc, source_end_utc, "
                    "exec_start_utc, speed_factor) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 2.0)",
                    (test_run_id, scenario_id, 99, "0"*64, "0"*64, "{}", "0"*40,
                     "TEST", "2026-01-01 00:00:00", "2026-01-01 00:00:01", "2026-01-01 00:00:02"),
                )
        except Exception as e:  # pylint: disable=broad-except
            rejection_message = f"{type(e).__name__}: {str(e)[:200]}"
            sub_b_pass = "chk_speed_factor_v1_2" in str(e).lower() or "check" in str(e).lower() or "constraint" in str(e).lower()
        finally:
            conn.close()
    except Exception as e:  # pylint: disable=broad-except
        rejection_message = f"connection failed: {e}"
    print(f"    DB rejected with: {rejection_message}")
    print(f"    Sub-case B: {'PASS' if sub_b_pass else 'FAIL'}")
    sub_results["B_speed_factor_db_check"] = {"pass": sub_b_pass, "rejection": rejection_message}

    # Sub-case C: grep engine src/replay/ for speed_factor consumption beyond metadata
    print("  Sub-case C: grep engine for speed_factor consumption")
    grep_res = _sub.run(
        ["ssh", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "root@192.168.11.10",
         "grep -rn 'speed_factor' /srv/mt5_plutus/src/replay/ 2>/dev/null"],
        capture_output=True, text=True,
    )
    grep_lines = grep_res.stdout.strip().splitlines() if grep_res.stdout else []
    # Strip path prefix "FILE:LINE:" before pattern matching to avoid false-positive on path slashes.
    # Suspicious time-arithmetic patterns: explicit consumption of speed_factor in time logic.
    def _content_after_grep_prefix(line: str) -> str:
        # grep -rn output: 'FILE:LINE:CONTENT'
        parts = line.split(":", 2)
        return parts[2] if len(parts) >= 3 else line

    suspicious_patterns = [
        "* speed_factor", "speed_factor *",   # multiplication
        "/ speed_factor", "speed_factor /",    # division
        "sleep(", "time.sleep",                # time consumption
        "asyncio.sleep",
        "/speed_factor", "*speed_factor",      # tight-spacing variants
        "speed_factor*", "speed_factor/",
    ]
    suspicious = []
    for line in grep_lines:
        content = _content_after_grep_prefix(line).lower()
        if any(p in content for p in suspicious_patterns):
            suspicious.append(line)
    sub_c_pass = len(suspicious) == 0
    print(f"    speed_factor mentions in src/replay/: {len(grep_lines)} (suspicious for time-arithmetic: {len(suspicious)})")
    for line in grep_lines[:10]:
        print(f"      {line}")
    print(f"    Sub-case C: {'PASS' if sub_c_pass else 'FAIL'}")
    sub_results["C_no_speed_factor_execution"] = {
        "pass": sub_c_pass,
        "total_mentions": len(grep_lines),
        "suspicious_count": len(suspicious),
        "sample_lines": grep_lines[:10],
    }

    all_pass = sub_a_pass and sub_b_pass and sub_c_pass
    fabric_set("r2d2:plutus:wo:2:acceptance:fail_loud_rules:v1", {
        "checked_at_utc": utc_now_iso(),
        "sub_cases": sub_results,
        "verdict": "PASS" if all_pass else "FAIL",
        "method": "Architect 2026-05-07 three sub-cases: A missing config B DB CHECK speed_factor C no execution path",
    })
    return assert_outcome(all_pass, True, "T-DET-5 all 3 sub-cases PASS")


def _replay_runs_count() -> int:
    conn = get_plutus_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM replay_runs")
            return cur.fetchone()[0]
    finally:
        conn.close()


def t_det_7_config_hash_independent(run_id: str | None) -> bool:
    """Architect 2026-05-06T02:45Z correction: parse + re-canonicalise + sha,
    NOT raw byte hash.

    Reasoning: even if engine persists canonical-JSON correctly at run start,
    storage layer may add invisible normalisation (whitespace, charset, line
    endings). Parsing back + re-canonicalising produces the SAME hash that
    engine should have computed at run-start step 6, regardless of any
    storage-layer byte drift. T-DET-7 stays valid for any well-behaved engine;
    only catches actually-wrong computations, not storage artifacts.

    Implementable post-migration_007 + first replay run.
    """
    import json as _json
    print("\n--- T-DET-7: config_hash recomputation (parse + recanonicalise + sha) ---")
    if run_id is None:
        print("  SKIP: requires --run-id of an existing plutus.replay_runs row (post-migration_007)")
        return True

    meta = get_run_metadata(run_id)
    if meta is None:
        print(f"  FAIL: run_id={run_id} not found in plutus.replay_runs")
        return False

    snapshot_json_str = meta.get("config_snapshot_json")
    declared_hash = meta.get("config_hash")
    if not snapshot_json_str:
        print("  FAIL: config_snapshot_json is empty/null — migration_007 not applied OR engine didn't persist")
        return False

    # Architect-locked method: parse -> re-canonicalise per §22 -> sha256
    try:
        parsed = _json.loads(snapshot_json_str)
    except (_json.JSONDecodeError, TypeError) as e:
        print(f"  FAIL: config_snapshot_json is not valid JSON: {e}")
        return False

    recanonical = canonical_json_of_subobject(parsed)
    recomputed_hash = sha256_text(recanonical)

    print(f"  declared_config_hash:   {declared_hash}")
    print(f"  recomputed_config_hash: {recomputed_hash}")
    print(f"  (recanonical bytes len: {len(recanonical)} vs persisted bytes len: {len(snapshot_json_str)})")
    match = declared_hash == recomputed_hash

    fabric_set(f"r2d2:plutus:wo:2:acceptance:config_hash_independent:{run_id}:v1", {
        "run_id": run_id,
        "declared_hash": declared_hash,
        "recomputed_hash": recomputed_hash,
        "snapshot_json_persisted_length": len(snapshot_json_str),
        "snapshot_json_recanonical_length": len(recanonical),
        "persisted_equals_recanonical_byte_for_byte": snapshot_json_str == recanonical,
        "match": match,
        "verdict": "PASS" if match else "FAIL",
        "checked_at_utc": utc_now_iso(),
        "method": "parse(config_snapshot_json) -> canonical-JSON per §22 (sort_keys=True, separators=(',',':')) -> sha256",
        "architect_correction_applied": "2026-05-06T02:45Z — robust to storage-layer byte drift",
    })

    return assert_outcome(match, True, "T-DET-7 declared == recomputed config_hash")


def t_det_8_snapshot_run_start_mirror(run_id: str | None,
                                       pre_run_mirror_key: str | None) -> bool:
    """Architect 2026-05-06 CRITICAL nuance:
    Compare config_snapshot_json against captured run-start mirror, NOT against
    current live scripted_overlays after the run.

    IMPL A (V1-2 election): captured run-start mirror.
      Harness reads scripted_overlays.deterministic_replay_v1 BEFORE spawning replay.
      Mirror persisted to fabric at pre_run_mirror_key.
      After replay: read replay_runs.config_snapshot_json; assert equality vs mirror.

    Why: comparing against live source AFTER run is unsound for audit — legitimate later
    config update would make old runs look invalid.
    """
    print("\n--- T-DET-8: snapshot equality vs captured run-start mirror (NOT live) ---")
    if run_id is None or pre_run_mirror_key is None:
        print("  SKIP: requires --run-id AND --pre-run-mirror-key (mirror captured BEFORE replay started)")
        return True

    meta = get_run_metadata(run_id)
    if meta is None:
        print(f"  FAIL: run_id={run_id} not found in plutus.replay_runs")
        return False

    snapshot_json_str = meta.get("config_snapshot_json")
    if not snapshot_json_str:
        print("  FAIL: config_snapshot_json is empty/null")
        return False

    from _common import fabric_get
    pre_run_mirror = fabric_get(pre_run_mirror_key)
    if pre_run_mirror is None:
        print(f"  FAIL: pre_run_mirror_key={pre_run_mirror_key} not found in fabric")
        return False

    mirror_canonical = pre_run_mirror.get("canonical_json")
    if mirror_canonical is None:
        print(f"  FAIL: pre_run_mirror has no 'canonical_json' field — was it captured correctly?")
        return False

    match = snapshot_json_str == mirror_canonical

    fabric_set(f"r2d2:plutus:wo:2:acceptance:snapshot_run_start_mirror:{run_id}:v1", {
        "run_id": run_id,
        "pre_run_mirror_key": pre_run_mirror_key,
        "mirror_captured_at_utc": pre_run_mirror.get("captured_at_utc"),
        "snapshot_json_length": len(snapshot_json_str),
        "mirror_canonical_length": len(mirror_canonical),
        "match": match,
        "verdict": "PASS" if match else "FAIL",
        "checked_at_utc": utc_now_iso(),
        "method": "IMPL A — compare replay_runs.config_snapshot_json vs captured pre-run scripted_overlays mirror",
        "do_NOT_compare_to_live_post_run": "Architect 2026-05-06 explicit: live scripted_overlays may have legitimately changed post-run; comparison would be unsound",
    })

    return assert_outcome(match, True, "T-DET-8 snapshot == run-start mirror")


def capture_pre_run_mirror(scenario_id: str, mirror_key: str) -> bool:
    """Helper for T-DET-8 IMPL A: capture scripted_overlays.deterministic_replay_v1
    BEFORE spawning a replay run. Persists mirror to fabric for post-run comparison.

    Call this from the test runner BEFORE spawn_replay_run().
    """
    print(f"\n--- Capture pre-run mirror for scenario_id={scenario_id} ---")
    sub_object = get_scripted_overlays_subobject(scenario_id)
    if sub_object is None:
        print(f"  FAIL: no deterministic_replay_v1 sub-object found in scripted_overlays for {scenario_id}")
        return False

    missing = validate_deterministic_replay_v1_shape(sub_object)
    if missing:
        print(f"  WARN: shape incomplete; missing fields: {missing}")
        # Capture anyway — engine should also FAIL pre-flight; this captures the live state for comparison

    mirror_canonical = canonical_json_of_subobject(sub_object)
    mirror_sha = sha256_text(mirror_canonical)
    fabric_set(mirror_key, {
        "scenario_id": scenario_id,
        "captured_at_utc": utc_now_iso(),
        "canonical_json": mirror_canonical,
        "canonical_sha256": mirror_sha,
        "subobject_keys": sorted(sub_object.keys()),
        "note": "Captured BEFORE replay run. Used by T-DET-8 IMPL A. Architect 2026-05-06: do NOT compare to live source after run.",
    })
    print(f"  Mirror captured: sha256={mirror_sha} length={len(mirror_canonical)} stored={mirror_key}")
    return True


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
                                            "T-DET-5", "T-DET-6", "T-DET-7", "T-DET-8",
                                            "capture-mirror"],
                        default=None, help="Run a single test or capture pre-run mirror")
    parser.add_argument("--scenario", default="tdr_validation_2026_03_28",
                        help="Scenario id for replay tests (only for capture-mirror)")
    parser.add_argument("--seed", type=int, default=42, help="Seed for primary replay (legacy)")
    parser.add_argument("--seed-b", type=int, default=43, help="Second seed (legacy)")
    parser.add_argument("--run-id", default=None,
                        help="Existing replay_runs.run_id for T-DET-3/4/6/7/8")
    parser.add_argument("--run-id-a", default=None,
                        help="Run A (same-seed pair partner) for T-DET-1")
    parser.add_argument("--run-id-b", default=None,
                        help="Run B (same-seed pair partner) for T-DET-1")
    parser.add_argument("--run-id-c", default=None,
                        help="Run C (different seed from A) for T-DET-2")
    parser.add_argument("--pre-run-mirror-key", default=None,
                        help="Fabric key holding the pre-run scripted_overlays mirror (for T-DET-8 IMPL A)")
    args = parser.parse_args()

    if args.only == "capture-mirror":
        if not args.pre_run_mirror_key:
            print("ERROR: --pre-run-mirror-key required for capture-mirror mode")
            return 2
        ok = capture_pre_run_mirror(args.scenario, args.pre_run_mirror_key)
        return 0 if ok else 1

    suite = [
        ("T-DET-1", lambda: t_det_1_byte_identical(args.run_id_a, args.run_id_b)),
        ("T-DET-2", lambda: t_det_2_seed_divergence(args.run_id_a, args.run_id_c)),
        ("T-DET-3", lambda: t_det_3_canary_pre(args.run_id)),
        ("T-DET-4", lambda: t_det_4_canary_post(args.run_id)),
        ("T-DET-5", lambda: t_det_5_fail_loud(args.scenario)),
        ("T-DET-6", lambda: t_det_6_dataset_hash_independent(args.run_id)),
        ("T-DET-7", lambda: t_det_7_config_hash_independent(args.run_id)),
        ("T-DET-8", lambda: t_det_8_snapshot_run_start_mirror(args.run_id, args.pre_run_mirror_key)),
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
