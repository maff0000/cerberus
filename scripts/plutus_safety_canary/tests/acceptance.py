#!/usr/bin/env python3
"""WO-PLUTUS-V1-1A acceptance harness — T1, T2, T3, T4.

Runs each test, asserts expected outcome, cleans up. Exit 0 = all PASS.

Tests (per design tests_canaries_for_acceptance):
  T1  synthetic violation: prop_trades count change → post_flight FAIL
  T2  synthetic violation: namespace isolation (trader:* fake key) → FAIL
  T3  pre_flight blocking: executor missing → pre_flight FAIL
  T4  SHA-not-mtime: touch then content change → only content triggers FAIL

Default --no-db so the harness can run before Rogue's migration lands.
Once plutus.safety_canary_runs exists, drop --no-db.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CANARY_DIR = os.path.dirname(HERE)
PRE = os.path.join(CANARY_DIR, "pre_flight.py")
POST = os.path.join(CANARY_DIR, "post_flight.py")
REDIS_API = os.environ.get("REDIS_FABRIC_API", "http://localhost:8080/api/v1/redis")
EXECUTOR_PATH = os.environ.get("PLUTUS_CANARY_EXECUTOR_PATH", "/srv/NEO/scripts/neo_ftmo_executor.py")


def utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


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


def run(cmd: list[str], expect_exit: int) -> tuple[int, str, str]:
    res = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ})
    ok = "OK " if res.returncode == expect_exit else "MISMATCH "
    print(f"  {ok}exit={res.returncode} (expected {expect_exit}) cmd={' '.join(cmd)}")
    if res.stdout.strip():
        for line in res.stdout.strip().splitlines():
            print(f"    stdout: {line}")
    if res.stderr.strip():
        for line in res.stderr.strip().splitlines():
            print(f"    stderr: {line}")
    return res.returncode, res.stdout, res.stderr


def assert_outcome(actual: int, expected: int, label: str) -> bool:
    ok = actual == expected
    print(f"  {'PASS' if ok else 'FAIL'}: {label} (got exit={actual}, expected {expected})")
    return ok


def t1_prop_trades_violation(no_db: bool) -> bool:
    print("\n--- T1: synthetic prop_trades violation ---")
    run_id = f"TEST-T1-{utc_compact()}"
    fake_key = "neo:prop:trades:CANARY-TEST-T1"
    flags = ["--no-db"] if no_db else []

    pre_rc, _, _ = run(["python3", PRE, "--mode", "engine_start", "--run-id", run_id, *flags],
                       expect_exit=0)
    if pre_rc != 0:
        print("  ABORT: pre_flight unexpectedly failed (env not clean?)")
        return False
    fabric_set(fake_key, {"test": "T1"})
    try:
        post_rc, _, _ = run(["python3", POST, "--run-id", run_id, *flags], expect_exit=1)
    finally:
        fabric_delete(fake_key)

    mirror = fabric_get(f"sim_broker:reports:safety:{run_id}:v1")
    has_count_violation = False
    has_keys_violation = False
    if mirror and mirror.get("fail_reasons"):
        codes = [r["reason_code"] for r in mirror["fail_reasons"]]
        has_count_violation = "F4_VIOLATION_PROP_TRADES_COUNT_CHANGED" in codes
        has_keys_violation = "F4_VIOLATION_PROP_TRADES_KEYS_CHANGED" in codes

    # Verify cleanup with a fresh run_id passes
    verify_run_id = f"TEST-T1-VERIFY-{utc_compact()}"
    pre2_rc, _, _ = run(["python3", PRE, "--mode", "engine_start", "--run-id", verify_run_id, *flags],
                        expect_exit=0)
    post2_rc, _, _ = run(["python3", POST, "--run-id", verify_run_id, *flags], expect_exit=0)

    return all([
        assert_outcome(post_rc, 1, "T1 post_flight FAIL on prop_trades violation"),
        assert_outcome(int(has_count_violation), 1, "T1 fail_reasons contains F4_VIOLATION_PROP_TRADES_COUNT_CHANGED"),
        assert_outcome(int(has_keys_violation), 1, "T1 fail_reasons contains F4_VIOLATION_PROP_TRADES_KEYS_CHANGED"),
        assert_outcome(pre2_rc, 0, "T1 cleanup verification pre_flight PASS"),
        assert_outcome(post2_rc, 0, "T1 cleanup verification post_flight PASS"),
    ])


def t2_namespace_isolation(no_db: bool) -> bool:
    print("\n--- T2: synthetic namespace isolation violation ---")
    run_id = f"TEST-T2-{utc_compact()}"
    fake_key = f"trader:CANARY-TEST-T2-{utc_compact()}"
    flags = ["--no-db"] if no_db else []

    pre_rc, _, _ = run(["python3", PRE, "--mode", "engine_start", "--run-id", run_id, *flags],
                       expect_exit=0)
    if pre_rc != 0:
        return False
    fabric_set(fake_key, {"test": "T2"})
    try:
        post_rc, _, _ = run(["python3", POST, "--run-id", run_id, *flags], expect_exit=1)
    finally:
        fabric_delete(fake_key)

    mirror = fabric_get(f"sim_broker:reports:safety:{run_id}:v1")
    has_iso_violation = False
    detail_includes_key = False
    if mirror and mirror.get("fail_reasons"):
        for r in mirror["fail_reasons"]:
            if r["reason_code"] == "NAMESPACE_ISOLATION_VIOLATION":
                has_iso_violation = True
                if r.get("detail") == fake_key:
                    detail_includes_key = True

    return all([
        assert_outcome(post_rc, 1, "T2 post_flight FAIL on namespace violation"),
        assert_outcome(int(has_iso_violation), 1, "T2 fail_reasons contains NAMESPACE_ISOLATION_VIOLATION"),
        assert_outcome(int(detail_includes_key), 1, f"T2 detail includes offending key {fake_key}"),
    ])


def t3_pre_flight_blocking(no_db: bool) -> bool:
    print("\n--- T3: pre_flight blocks when executor missing ---")
    run_id = f"TEST-T3-{utc_compact()}"
    flags = ["--no-db"] if no_db else []
    bak = EXECUTOR_PATH + ".canary_test_bak"
    if not os.path.exists(EXECUTOR_PATH):
        print(f"  SKIP: executor not present at {EXECUTOR_PATH}")
        return True

    shutil.move(EXECUTOR_PATH, bak)
    try:
        pre_rc, _, stderr = run(
            ["python3", PRE, "--mode", "engine_start", "--run-id", run_id, *flags], expect_exit=1
        )
    finally:
        shutil.move(bak, EXECUTOR_PATH)

    mirror = fabric_get(f"sim_broker:reports:safety:{run_id}:v1")
    has_executor_missing = False
    if mirror and mirror.get("fail_reasons"):
        codes = [r["reason_code"] for r in mirror["fail_reasons"]]
        has_executor_missing = "FAIL_PREFLIGHT_EXECUTOR_MISSING" in codes

    # Re-run with executor restored — must PASS
    verify_run_id = f"TEST-T3-VERIFY-{utc_compact()}"
    pre2_rc, _, _ = run(["python3", PRE, "--mode", "engine_start", "--run-id", verify_run_id, *flags],
                        expect_exit=0)

    return all([
        assert_outcome(pre_rc, 1, "T3 pre_flight FAIL when executor missing"),
        assert_outcome(int(has_executor_missing), 1, "T3 fail_reasons contains FAIL_PREFLIGHT_EXECUTOR_MISSING"),
        assert_outcome(pre2_rc, 0, "T3 pre_flight PASS after executor restored"),
    ])


def t4_sha_not_mtime(no_db: bool) -> bool:
    print("\n--- T4: SHA-not-mtime detection ---")
    flags = ["--no-db"] if no_db else []
    if not os.path.exists(EXECUTOR_PATH):
        print(f"  SKIP: executor not present at {EXECUTOR_PATH}")
        return True

    # Step 1-3: touch only (mtime change, content same) — should PASS
    run_id_a = f"TEST-T4A-{utc_compact()}"
    pre_a, _, _ = run(["python3", PRE, "--mode", "engine_start", "--run-id", run_id_a, *flags],
                      expect_exit=0)
    if pre_a != 0:
        return False
    os.utime(EXECUTOR_PATH, None)  # touch
    time.sleep(0.5)
    post_a, _, _ = run(["python3", POST, "--run-id", run_id_a, *flags], expect_exit=0)

    # Step 4-7: append a comment line (content change) — should FAIL
    run_id_b = f"TEST-T4B-{utc_compact()}"
    pre_b, _, _ = run(["python3", PRE, "--mode", "engine_start", "--run-id", run_id_b, *flags],
                      expect_exit=0)
    if pre_b != 0:
        return False

    canary_marker = b"\n# canary test comment - DO NOT COMMIT\n"
    with open(EXECUTOR_PATH, "rb") as f:
        original = f.read()
    try:
        with open(EXECUTOR_PATH, "ab") as f:
            f.write(canary_marker)
        post_b, _, _ = run(["python3", POST, "--run-id", run_id_b, *flags], expect_exit=1)
    finally:
        with open(EXECUTOR_PATH, "wb") as f:
            f.write(original)

    mirror_b = fabric_get(f"sim_broker:reports:safety:{run_id_b}:v1")
    has_executor_change = False
    if mirror_b and mirror_b.get("fail_reasons"):
        codes = [r["reason_code"] for r in mirror_b["fail_reasons"]]
        has_executor_change = "F4_VIOLATION_EXECUTOR_BINARY_CHANGED" in codes

    return all([
        assert_outcome(post_a, 0, "T4a post_flight PASS on mtime-only change"),
        assert_outcome(post_b, 1, "T4b post_flight FAIL on content change"),
        assert_outcome(int(has_executor_change), 1, "T4b fail_reasons contains F4_VIOLATION_EXECUTOR_BINARY_CHANGED"),
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-db", action="store_true", default=True,
                        help="Skip DB writes (default; flip off once migration is live)")
    parser.add_argument("--with-db", action="store_true",
                        help="Force DB writes — overrides --no-db default")
    parser.add_argument("--only", choices=["T1", "T2", "T3", "T4"], default=None,
                        help="Run a single test")
    args = parser.parse_args()
    no_db = not args.with_db

    suite = [("T1", t1_prop_trades_violation),
             ("T2", t2_namespace_isolation),
             ("T3", t3_pre_flight_blocking),
             ("T4", t4_sha_not_mtime)]
    if args.only:
        suite = [(n, fn) for n, fn in suite if n == args.only]

    results = []
    for name, fn in suite:
        try:
            ok = fn(no_db)
        except Exception as e:  # pylint: disable=broad-except
            print(f"\n  EXCEPTION in {name}: {type(e).__name__}: {e}")
            ok = False
        results.append((name, ok))

    print("\n=== ACCEPTANCE SUMMARY ===")
    for name, ok in results:
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")
    all_pass = all(ok for _, ok in results)
    print(f"\nOVERALL: {'GREEN' if all_pass else 'RED'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
