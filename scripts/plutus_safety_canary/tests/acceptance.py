#!/usr/bin/env python3
"""WO-PLUTUS-V1-1A acceptance harness — T1-T11 + T12 bonus (canary v1.1).

Architect's seven acceptance points (sim_broker:wo:WO-PLUTUS-V1-1A:controls:v1
.seven_acceptance_points_v1):
  - T6 enforces AGE-based staleness (NOT cadence)
  - T10 fails separately for plutus_present=true AND plutus_paths_observed != []
  - manifest_sha256_self recomputed independently
  - All T1-T11 must produce queryable evidence in fabric mirror (negative-evidence)

Default --no-db so harness runs before Rogue's migration_005 lands.
Once plutus.safety_canary_runs exists on dell-debian, drop --no-db.

Tests:
  T1   prop_trades count + key-list violation        F4_VIOLATION_PROP_TRADES_*
  T2   namespace isolation                           NAMESPACE_ISOLATION_VIOLATION
  T3   executor SHA changed (manifest mode)          F4_VIOLATION_EXECUTOR_BINARY_CHANGED
  T4   agent_smith registry SHA changed              F4_VIOLATION_AGENT_SMITH_REGISTRY_CHANGED
  T5   manifest missing                              FAIL_PREFLIGHT_MANIFEST_MISSING
  T6   manifest stale (age-based)                    FAIL_PREFLIGHT_MANIFEST_STALE
  T7   manifest version unknown                      FAIL_PREFLIGHT_MANIFEST_VERSION_UNKNOWN
  T8   dispatcher SHA changed                        F4_VIOLATION_DISPATCHER_CHANGED
  T9   observer SHA changed                          F4_VIOLATION_OBSERVER_CHANGED
  T10a plutus_present=true                           F4_VIOLATION_PLUTUS_PRESENT_TRUE
  T10b plutus_paths_observed non-empty               F4_VIOLATION_PLUTUS_PATHS_NON_EMPTY
  T11  manifest_sha256_self mismatch                 F4_VIOLATION_MANIFEST_SHA_MISMATCH
  T12  known_brokers changed (bonus)                 F4_VIOLATION_KNOWN_BROKERS_CHANGED
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CANARY_DIR = os.path.dirname(HERE)
PRE = os.path.join(CANARY_DIR, "pre_flight.py")
POST = os.path.join(CANARY_DIR, "post_flight.py")
REDIS_API = os.environ.get("REDIS_FABRIC_API", "http://localhost:8080/api/v1/redis")
LIVE_MANIFEST_KEY = "prod_guard:broker_path:manifest:current"


def utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def utc_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def fabric_set(key: str, value) -> None:
    payload = json.dumps({"key": key, "value": json.dumps(value)}).encode()
    req = urllib.request.Request(
        f"{REDIS_API}/set", data=payload, headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req, timeout=5)


def fabric_delete(key: str) -> None:
    req = urllib.request.Request(f"{REDIS_API}/delete/{key}", method="DELETE")
    try:
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise


def fabric_get(key: str):
    try:
        with urllib.request.urlopen(f"{REDIS_API}/get/{key}", timeout=5) as resp:
            data = json.loads(resp.read())
        raw = data.get("value")
        return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def make_synthetic_manifest(*, generated_at: datetime | None = None,
                            overrides: dict | None = None) -> dict:
    """Build a valid synthetic manifest based on the live one. Recomputes self-sha
    so the manifest is internally consistent unless overrides break it intentionally."""
    base = fabric_get(LIVE_MANIFEST_KEY)
    if base is None:
        raise RuntimeError("Live manifest not present — cannot derive synthetic")
    m = copy.deepcopy(base)
    if generated_at is not None:
        m["generated_at_utc"] = utc_iso(generated_at)
    if overrides:
        m.update(overrides)
    # Recompute self-sha unless caller is intentionally testing self-sha mismatch
    if "manifest_sha256_self" not in (overrides or {}):
        m_no_self = {k: v for k, v in m.items() if k != "manifest_sha256_self"}
        m["manifest_sha256_self"] = sha256_text(canonical_json(m_no_self))
    return m


def run(cmd: list[str], expect_exit: int, env_extra: dict | None = None) -> tuple[int, str, str]:
    env = {**os.environ, **(env_extra or {})}
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    ok = "OK " if res.returncode == expect_exit else "MISMATCH "
    print(f"  {ok}exit={res.returncode} (expected {expect_exit}) cmd={' '.join(cmd[:6])}...")
    if res.stdout.strip():
        for line in res.stdout.strip().splitlines()[:5]:
            print(f"    stdout: {line}")
    if res.stderr.strip():
        for line in res.stderr.strip().splitlines()[:8]:
            print(f"    stderr: {line}")
    return res.returncode, res.stdout, res.stderr


def assert_outcome(actual, expected, label: str) -> bool:
    ok = actual == expected
    print(f"  {'PASS' if ok else 'FAIL'}: {label} (got {actual!r}, expected {expected!r})")
    return ok


def fail_codes_in_mirror(run_id: str) -> list[str]:
    mirror = fabric_get(f"sim_broker:reports:safety:{run_id}:v1")
    if not mirror or not mirror.get("fail_reasons"):
        return []
    return [r["reason_code"] for r in mirror["fail_reasons"]]


def fail_details_in_mirror(run_id: str) -> list[tuple[str, str]]:
    mirror = fabric_get(f"sim_broker:reports:safety:{run_id}:v1")
    if not mirror or not mirror.get("fail_reasons"):
        return []
    return [(r["reason_code"], r.get("detail", "")) for r in mirror["fail_reasons"]]


# ------------------------ TESTS ------------------------

def t1_prop_trades_violation(no_db: bool) -> bool:
    print("\n--- T1: prop_trades count + keys violation ---")
    run_id = f"TEST-T1-{utc_compact()}"
    fake_key = "neo:prop:trades:CANARY-TEST-T1"
    flags = ["--no-db"] if no_db else []

    pre_rc, _, _ = run(["python3", PRE, "--mode", "engine_start", "--run-id", run_id, *flags],
                       expect_exit=0)
    if pre_rc != 0:
        return False
    fabric_set(fake_key, {"test": "T1"})
    try:
        post_rc, _, _ = run(["python3", POST, "--mode", "manual", "--run-id", run_id, *flags],
                            expect_exit=1)
    finally:
        fabric_delete(fake_key)

    codes = fail_codes_in_mirror(run_id)
    return all([
        assert_outcome(post_rc, 1, "T1 post_flight FAIL"),
        assert_outcome("F4_VIOLATION_PROP_TRADES_COUNT_CHANGED" in codes, True, "T1 count code present"),
        assert_outcome("F4_VIOLATION_PROP_TRADES_KEYS_CHANGED" in codes, True, "T1 keys code present"),
    ])


def t2_namespace_isolation(no_db: bool) -> bool:
    print("\n--- T2: namespace isolation violation ---")
    run_id = f"TEST-T2-{utc_compact()}"
    fake_key = f"trader:CANARY-TEST-T2-{utc_compact()}"
    flags = ["--no-db"] if no_db else []

    pre_rc, _, _ = run(["python3", PRE, "--mode", "engine_start", "--run-id", run_id, *flags],
                       expect_exit=0)
    if pre_rc != 0:
        return False
    fabric_set(fake_key, {"test": "T2"})
    try:
        post_rc, _, _ = run(["python3", POST, "--mode", "manual", "--run-id", run_id, *flags],
                            expect_exit=1)
    finally:
        fabric_delete(fake_key)

    details = fail_details_in_mirror(run_id)
    has_iso = any(c == "NAMESPACE_ISOLATION_VIOLATION" and d == fake_key for c, d in details)
    return all([
        assert_outcome(post_rc, 1, "T2 post_flight FAIL"),
        assert_outcome(has_iso, True, f"T2 NAMESPACE_ISOLATION_VIOLATION with detail={fake_key}"),
    ])


def _t_manifest_field_change_pre_post(test_id: str, mutation_field: str, expected_code: str,
                                      no_db: bool, mutator) -> bool:
    """Generic pre/post test where manifest M_A is published, pre_flight runs, manifest is
    overwritten with M_B (mutation applied), post_flight runs, expected diff fires."""
    run_id = f"TEST-{test_id}-{utc_compact()}"
    test_key = f"test:plutus_canary:{test_id}:{utc_compact()}"
    flags = ["--no-db"] if no_db else []
    env = {"PLUTUS_CANARY_MANIFEST_KEY": test_key}

    base = make_synthetic_manifest()
    fabric_set(test_key, base)
    try:
        pre_rc, _, _ = run(
            ["python3", PRE, "--mode", "engine_start", "--run-id", run_id, *flags],
            expect_exit=0, env_extra=env,
        )
        if pre_rc != 0:
            print(f"  ABORT: {test_id} pre_flight unexpectedly failed against synthetic baseline")
            return False
        # Mutate
        m_b = mutator(copy.deepcopy(base))
        fabric_set(test_key, m_b)
        post_rc, _, _ = run(
            ["python3", POST, "--mode", "manual", "--run-id", run_id, *flags],
            expect_exit=1, env_extra=env,
        )
    finally:
        fabric_delete(test_key)

    codes = fail_codes_in_mirror(run_id)
    return all([
        assert_outcome(post_rc, 1, f"{test_id} post_flight FAIL"),
        assert_outcome(expected_code in codes, True, f"{test_id} code {expected_code} present"),
    ])


def t3_executor_sha_change(no_db: bool) -> bool:
    print("\n--- T3: executor SHA changed (manifest mode) ---")
    def mutator(m):
        m["neo_ftmo_executor_sha"] = "0" * 64
        m_no_self = {k: v for k, v in m.items() if k != "manifest_sha256_self"}
        m["manifest_sha256_self"] = sha256_text(canonical_json(m_no_self))
        return m
    return _t_manifest_field_change_pre_post(
        "T3", "neo_ftmo_executor_sha", "F4_VIOLATION_EXECUTOR_BINARY_CHANGED", no_db, mutator
    )


def t4_agent_smith_change(no_db: bool) -> bool:
    print("\n--- T4: agent_smith registry SHA changed ---")
    def mutator(m):
        m["agent_smith_registry_snapshot_sha"] = "1" * 64
        m_no_self = {k: v for k, v in m.items() if k != "manifest_sha256_self"}
        m["manifest_sha256_self"] = sha256_text(canonical_json(m_no_self))
        return m
    return _t_manifest_field_change_pre_post(
        "T4", "agent_smith_registry_snapshot_sha", "F4_VIOLATION_AGENT_SMITH_REGISTRY_CHANGED",
        no_db, mutator,
    )


def t5_manifest_missing(no_db: bool) -> bool:
    print("\n--- T5: manifest missing ---")
    run_id = f"TEST-T5-{utc_compact()}"
    nonexistent_key = f"test:plutus_canary:T5:nonexistent:{utc_compact()}"
    flags = ["--no-db"] if no_db else []
    env = {"PLUTUS_CANARY_MANIFEST_KEY": nonexistent_key}

    pre_rc, _, _ = run(
        ["python3", PRE, "--mode", "engine_start", "--run-id", run_id, *flags],
        expect_exit=1, env_extra=env,
    )

    codes = fail_codes_in_mirror(run_id)
    return all([
        assert_outcome(pre_rc, 1, "T5 pre_flight FAIL"),
        assert_outcome("FAIL_PREFLIGHT_MANIFEST_MISSING" in codes, True,
                       "T5 FAIL_PREFLIGHT_MANIFEST_MISSING present"),
    ])


def t6_manifest_stale(no_db: bool) -> bool:
    print("\n--- T6: manifest stale (AGE-based, not cadence) ---")
    run_id = f"TEST-T6-{utc_compact()}"
    test_key = f"test:plutus_canary:T6:{utc_compact()}"
    flags = ["--no-db"] if no_db else []
    env = {"PLUTUS_CANARY_MANIFEST_KEY": test_key}

    # Manifest aged 1 hour past now — well past 300s budget
    stale_dt = datetime.now(timezone.utc) - timedelta(seconds=3600)
    stale_manifest = make_synthetic_manifest(generated_at=stale_dt)
    fabric_set(test_key, stale_manifest)

    try:
        pre_rc, _, _ = run(
            ["python3", PRE, "--mode", "engine_start", "--run-id", run_id, *flags],
            expect_exit=1, env_extra=env,
        )
    finally:
        fabric_delete(test_key)

    details = fail_details_in_mirror(run_id)
    stale_present = any(c == "FAIL_PREFLIGHT_MANIFEST_STALE" for c, _ in details)
    age_in_detail = any(c == "FAIL_PREFLIGHT_MANIFEST_STALE" and "manifest_age_seconds=" in d
                        for c, d in details)
    return all([
        assert_outcome(pre_rc, 1, "T6 pre_flight FAIL"),
        assert_outcome(stale_present, True, "T6 FAIL_PREFLIGHT_MANIFEST_STALE present"),
        assert_outcome(age_in_detail, True, "T6 detail contains manifest_age_seconds (proves AGE invariant)"),
    ])


def t7_manifest_version_unknown(no_db: bool) -> bool:
    print("\n--- T7: manifest version unknown ---")
    run_id = f"TEST-T7-{utc_compact()}"
    test_key = f"test:plutus_canary:T7:{utc_compact()}"
    flags = ["--no-db"] if no_db else []
    env = {"PLUTUS_CANARY_MANIFEST_KEY": test_key}

    bad_version = make_synthetic_manifest(overrides={"manifest_version": "99-future"})
    fabric_set(test_key, bad_version)

    try:
        pre_rc, _, _ = run(
            ["python3", PRE, "--mode", "engine_start", "--run-id", run_id, *flags],
            expect_exit=1, env_extra=env,
        )
    finally:
        fabric_delete(test_key)

    codes = fail_codes_in_mirror(run_id)
    return all([
        assert_outcome(pre_rc, 1, "T7 pre_flight FAIL"),
        assert_outcome("FAIL_PREFLIGHT_MANIFEST_VERSION_UNKNOWN" in codes, True,
                       "T7 FAIL_PREFLIGHT_MANIFEST_VERSION_UNKNOWN present"),
    ])


def t8_dispatcher_change(no_db: bool) -> bool:
    print("\n--- T8: dispatcher SHA changed ---")
    def mutator(m):
        m["neo_dispatcher_sha"] = "2" * 64
        m_no_self = {k: v for k, v in m.items() if k != "manifest_sha256_self"}
        m["manifest_sha256_self"] = sha256_text(canonical_json(m_no_self))
        return m
    return _t_manifest_field_change_pre_post(
        "T8", "neo_dispatcher_sha", "F4_VIOLATION_DISPATCHER_CHANGED", no_db, mutator,
    )


def t9_observer_change(no_db: bool) -> bool:
    print("\n--- T9: observer SHA changed ---")
    def mutator(m):
        m["neo_observer_sha"] = "3" * 64
        m_no_self = {k: v for k, v in m.items() if k != "manifest_sha256_self"}
        m["manifest_sha256_self"] = sha256_text(canonical_json(m_no_self))
        return m
    return _t_manifest_field_change_pre_post(
        "T9", "neo_observer_sha", "F4_VIOLATION_OBSERVER_CHANGED", no_db, mutator,
    )


def t10a_plutus_present_true(no_db: bool) -> bool:
    print("\n--- T10a: plutus_present=true ---")
    run_id = f"TEST-T10a-{utc_compact()}"
    test_key = f"test:plutus_canary:T10a:{utc_compact()}"
    flags = ["--no-db"] if no_db else []
    env = {"PLUTUS_CANARY_MANIFEST_KEY": test_key}

    bad = make_synthetic_manifest(overrides={"plutus_present": True})
    fabric_set(test_key, bad)

    try:
        pre_rc, _, _ = run(
            ["python3", PRE, "--mode", "engine_start", "--run-id", run_id, *flags],
            expect_exit=1, env_extra=env,
        )
    finally:
        fabric_delete(test_key)

    codes = fail_codes_in_mirror(run_id)
    return all([
        assert_outcome(pre_rc, 1, "T10a pre_flight FAIL"),
        assert_outcome("F4_VIOLATION_PLUTUS_PRESENT_TRUE" in codes, True,
                       "T10a F4_VIOLATION_PLUTUS_PRESENT_TRUE present"),
    ])


def t10b_plutus_paths_non_empty(no_db: bool) -> bool:
    print("\n--- T10b: plutus_paths_observed non-empty ---")
    run_id = f"TEST-T10b-{utc_compact()}"
    test_key = f"test:plutus_canary:T10b:{utc_compact()}"
    flags = ["--no-db"] if no_db else []
    env = {"PLUTUS_CANARY_MANIFEST_KEY": test_key}

    bad = make_synthetic_manifest(
        overrides={"plutus_paths_observed": ["/srv/NEO/scripts/plutus_smuggled.py"]}
    )
    fabric_set(test_key, bad)

    try:
        pre_rc, _, _ = run(
            ["python3", PRE, "--mode", "engine_start", "--run-id", run_id, *flags],
            expect_exit=1, env_extra=env,
        )
    finally:
        fabric_delete(test_key)

    details = fail_details_in_mirror(run_id)
    has_code = any(c == "F4_VIOLATION_PLUTUS_PATHS_NON_EMPTY" for c, _ in details)
    has_path = any(c == "F4_VIOLATION_PLUTUS_PATHS_NON_EMPTY" and "plutus_smuggled" in d
                   for c, d in details)
    return all([
        assert_outcome(pre_rc, 1, "T10b pre_flight FAIL"),
        assert_outcome(has_code, True, "T10b F4_VIOLATION_PLUTUS_PATHS_NON_EMPTY present"),
        assert_outcome(has_path, True, "T10b detail names offending path"),
    ])


def t11_manifest_sha_mismatch(no_db: bool) -> bool:
    print("\n--- T11: manifest_sha256_self mismatch ---")
    run_id = f"TEST-T11-{utc_compact()}"
    test_key = f"test:plutus_canary:T11:{utc_compact()}"
    flags = ["--no-db"] if no_db else []
    env = {"PLUTUS_CANARY_MANIFEST_KEY": test_key}

    # Override self-sha to bogus value; the helper won't re-derive when self-sha override is provided
    bad = make_synthetic_manifest(overrides={"manifest_sha256_self": "f" * 64})
    fabric_set(test_key, bad)

    try:
        pre_rc, _, _ = run(
            ["python3", PRE, "--mode", "engine_start", "--run-id", run_id, *flags],
            expect_exit=1, env_extra=env,
        )
    finally:
        fabric_delete(test_key)

    codes = fail_codes_in_mirror(run_id)
    return all([
        assert_outcome(pre_rc, 1, "T11 pre_flight FAIL"),
        assert_outcome("F4_VIOLATION_MANIFEST_SHA_MISMATCH" in codes, True,
                       "T11 F4_VIOLATION_MANIFEST_SHA_MISMATCH present"),
    ])


def t12_known_brokers_change(no_db: bool) -> bool:
    print("\n--- T12 (bonus): known_brokers changed ---")
    def mutator(m):
        m["known_brokers"] = m["known_brokers"] + ["MT5_SIM_PLUTUS"]
        m_no_self = {k: v for k, v in m.items() if k != "manifest_sha256_self"}
        m["manifest_sha256_self"] = sha256_text(canonical_json(m_no_self))
        return m
    return _t_manifest_field_change_pre_post(
        "T12", "known_brokers", "F4_VIOLATION_KNOWN_BROKERS_CHANGED", no_db, mutator,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-db", action="store_true",
                        help="Force DB writes — drops --no-db default (use after migration_005 lands)")
    parser.add_argument("--only", default=None,
                        help="Run only the named test (e.g. T6)")
    args = parser.parse_args()
    no_db = not args.with_db

    suite = [
        ("T1", t1_prop_trades_violation),
        ("T2", t2_namespace_isolation),
        ("T3", t3_executor_sha_change),
        ("T4", t4_agent_smith_change),
        ("T5", t5_manifest_missing),
        ("T6", t6_manifest_stale),
        ("T7", t7_manifest_version_unknown),
        ("T8", t8_dispatcher_change),
        ("T9", t9_observer_change),
        ("T10a", t10a_plutus_present_true),
        ("T10b", t10b_plutus_paths_non_empty),
        ("T11", t11_manifest_sha_mismatch),
        ("T12", t12_known_brokers_change),
    ]
    if args.only:
        suite = [(n, fn) for n, fn in suite if n == args.only]
        if not suite:
            print(f"No test named {args.only}")
            return 2

    results = []
    for name, fn in suite:
        try:
            ok = fn(no_db)
        except Exception as e:  # pylint: disable=broad-except
            import traceback
            print(f"\n  EXCEPTION in {name}: {type(e).__name__}: {e}")
            traceback.print_exc()
            ok = False
        results.append((name, ok))

    print("\n=== ACCEPTANCE SUMMARY ===")
    for name, ok in results:
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")
    bar_tests = {n for n, _ in results if not n.startswith("T12")}
    bar_pass = all(ok for n, ok in results if n in bar_tests)
    bonus_pass = all(ok for n, ok in results)
    print(f"\nT1-T11 BAR: {'GREEN' if bar_pass else 'RED'}")
    print(f"WITH BONUS T12: {'GREEN' if bonus_pass else 'RED'}")
    return 0 if bar_pass else 1


if __name__ == "__main__":
    sys.exit(main())
