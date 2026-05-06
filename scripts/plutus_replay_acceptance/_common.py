"""Shared helpers for the V1-2 deterministic replay acceptance harness.

Acceptance suite: T-DET-1 through T-DET-6 per locked design at
sim_broker:design:deterministic_replay_core:v1 (locked 2026-05-06T01:40Z).

Bar items mapped:
  T-DET-1 -> bar #4 (same scenario+seed -> byte-identical artefacts)
  T-DET-2 -> bar #5 (different seed -> different tick path)
  T-DET-3 -> bar #7 (V1-1A canary BEFORE replay)
  T-DET-4 -> bar #8 (V1-1A canary PASSES AFTER replay)
  T-DET-5 -> bar #3 (missing deterministic config fails loud)
  T-DET-6 -> architect watch-out 9 (dataset_hash hashes actual rows, not metadata)

T-DET-1/2/3/4/5 require Rogue's mt5_plutus replay CLI (BUILT phase).
T-DET-6 can run as soon as tradingSignals.candles_M1 is reachable + a
declared dataset_hash is recorded in plutus.replay_runs.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

REDIS_API = os.environ.get("REDIS_FABRIC_API", "http://localhost:8080/api/v1/redis")

DB_HOST = os.environ.get("PLUTUS_DB_HOST", "proteus-mariadb-dev")
DB_PORT = int(os.environ.get("PLUTUS_DB_PORT", "3307"))
DB_USER = os.environ.get("PLUTUS_DB_USER", "plutus")
DB_PASSWORD = os.environ.get("PLUTUS_DB_PASSWORD", "")
DB_NAME = os.environ.get("PLUTUS_DB_NAME", "plutus")

HERMES_DB_HOST = os.environ.get("HERMES_DB_HOST", DB_HOST)
HERMES_DB_PORT = int(os.environ.get("HERMES_DB_PORT", str(DB_PORT)))
HERMES_DB_USER = os.environ.get("HERMES_DB_USER", DB_USER)
HERMES_DB_PASSWORD = os.environ.get("HERMES_DB_PASSWORD", DB_PASSWORD)
HERMES_DB_NAME = os.environ.get("HERMES_DB_NAME", "tradingSignals")
HERMES_TABLE = os.environ.get("HERMES_TABLE", "candles_M1")

REPLAY_CLI = os.environ.get("PLUTUS_REPLAY_CLI", "mt5_plutus")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def fabric_get(key: str):
    try:
        with urllib.request.urlopen(f"{REDIS_API}/get/{key}", timeout=5) as resp:
            data = json.loads(resp.read())
        raw = data.get("value")
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def fabric_set(key: str, value) -> None:
    payload = json.dumps({"key": key, "value": json.dumps(value)}).encode()
    req = urllib.request.Request(
        f"{REDIS_API}/set", data=payload, headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req, timeout=5)


def get_plutus_db():
    """Connect to plutus DB (replay_* tables). Caller closes."""
    import pymysql
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME, connect_timeout=5, autocommit=True,
    )


def get_hermes_db():
    """Connect to HERMES (tradingSignals) DB. Caller closes."""
    import pymysql
    return pymysql.connect(
        host=HERMES_DB_HOST, port=HERMES_DB_PORT, user=HERMES_DB_USER,
        password=HERMES_DB_PASSWORD, database=HERMES_DB_NAME,
        connect_timeout=5, autocommit=True,
    )


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def serialize_candle_row_strict(ts_utc: str, o: float, h: float, l: float,
                                c: float, v: int) -> str:
    """Per locked design §3 row_serialization_strict:
      f'{ts_iso}:{o:%.6f}:{h:%.6f}:{l:%.6f}:{c:%.6f}:{v:%d}'
    where ts_iso is 'YYYY-MM-DDTHH:MM:SSZ' literal.
    """
    return f"{ts_utc}:{o:.6f}:{h:.6f}:{l:.6f}:{c:.6f}:{v:d}"


def normalize_naive_dt_to_utc_iso(dt) -> str:
    """Convert naive DATETIME from tradingSignals.candles_M1 to UTC ISO 8601 with Z.
    Per locked design §3 governed-source-convention PATH B:
    naive value treated as already-UTC clock face; format with explicit 'Z'.
    """
    if dt.tzinfo is None:
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_dataset_hash_independent(instrument: str, source_start_utc: str,
                                     source_end_utc: str) -> tuple[str, int]:
    """T-DET-6 core: independently recompute dataset_hash from raw HERMES rows.

    Returns (sha256_hex, row_count). Mismatch with declared in plutus.replay_runs
    means engine hashed metadata or used different algorithm — FAIL.
    """
    sql = (
        f"SELECT timestamp, open, high, low, close, volume "
        f"FROM {HERMES_TABLE} "
        f"WHERE instrument = %s AND timestamp BETWEEN %s AND %s "
        f"ORDER BY instrument, timestamp"
    )
    conn = get_hermes_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (instrument, source_start_utc, source_end_utc))
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        raise RuntimeError(
            f"Empty HERMES range: instrument={instrument} {source_start_utc} -> {source_end_utc}"
        )

    serialized = [
        serialize_candle_row_strict(
            normalize_naive_dt_to_utc_iso(ts),
            float(o), float(h), float(l), float(c), int(v),
        )
        for (ts, o, h, l, c, v) in rows
    ]
    return sha256_text("\n".join(serialized)), len(rows)


def hash_replay_artefact(conn, table: str, run_id: str,
                          excluded_columns: list[str]) -> str:
    """Per locked design §11: hash artefact rows for a run_id, excluding
    auto-increment IDs + run_id (deliberately differs across runs)."""
    with conn.cursor(cursor=__import__("pymysql").cursors.DictCursor) as cur:
        cur.execute(f"SELECT * FROM {table} WHERE run_id = %s ORDER BY 1", (run_id,))
        rows = cur.fetchall()
    payload_rows = []
    for row in rows:
        clean = {k: v for k, v in row.items() if k not in excluded_columns}
        # Decimal serialization per locked §11 — quote DB values as strings
        clean = {k: str(v) if v is not None else None for k, v in sorted(clean.items())}
        payload_rows.append(canonical_json(clean))
    return sha256_text("\n".join(payload_rows))


# Excluded columns per locked design §11.explicit_excluded_columns_per_artefact
ARTEFACT_EXCLUDED = {
    "replay_ticks": ["tick_id", "run_id"],
    "replay_orders": ["order_id", "run_id"],
    "replay_fills": ["fill_id", "order_id", "run_id"],
    "replay_positions": ["position_id", "run_id"],
    "replay_equity": ["equity_id", "run_id"],
    "replay_sessions": ["session_id", "run_id"],
}


def spawn_replay_run(scenario_id: str, seed: int, code_ref: str | None = None,
                     extra_args: list[str] | None = None) -> tuple[int, str, str]:
    """Spawn Rogue's replay CLI and return (returncode, stdout, stderr).

    Architect-locked invocation pattern (per locked design Q4):
      mt5_plutus replay --scenario <id> --seed <uint64> [--code-ref <sha>]
    """
    cmd = [REPLAY_CLI, "replay", "--scenario", scenario_id, "--seed", str(seed)]
    if code_ref:
        cmd.extend(["--code-ref", code_ref])
    if extra_args:
        cmd.extend(extra_args)
    res = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())
    return res.returncode, res.stdout, res.stderr


def get_run_metadata(run_id: str) -> dict | None:
    """Read plutus.replay_runs row for run_id."""
    conn = get_plutus_db()
    try:
        import pymysql
        with conn.cursor(cursor=pymysql.cursors.DictCursor) as cur:
            cur.execute("SELECT * FROM replay_runs WHERE run_id = %s", (run_id,))
            return cur.fetchone()
    finally:
        conn.close()


def get_scripted_overlays_subobject(scenario_id: str, namespace_key: str = "deterministic_replay_v1") -> dict | None:
    """Read plutus.scenarios.scripted_overlays for scenario_id, parse JSON,
    extract the namespaced sub-object.

    Returns:
        dict — the deterministic_replay_v1 sub-object (V1-2 canonical config)
        None — scenario row missing OR scripted_overlays NULL OR namespace key absent

    Per locked design §22 (post-lock 2026-05-06):
      Canonical V1-2 config source = plutus.scenarios.scripted_overlays.deterministic_replay_v1
    """
    conn = get_plutus_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT scripted_overlays FROM scenarios WHERE scenario_id = %s",
                (scenario_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    if not row or row[0] is None:
        return None
    try:
        overlays = json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return None
    return overlays.get(namespace_key)


def canonical_json_of_subobject(sub_object: dict) -> str:
    """Per locked §22 at-run-start atomic protocol: canonicalise via
    json.dumps(sub_object, sort_keys=True, separators=(',', ':'))."""
    return json.dumps(sub_object, sort_keys=True, separators=(",", ":"), default=str)


def sha256_of_canonical_json(sub_object: dict) -> str:
    """Per locked §22 config_hash methodology: sha256 of canonical-JSON of the sub-object."""
    return sha256_text(canonical_json_of_subobject(sub_object))


REQUIRED_DETERMINISTIC_REPLAY_V1_FIELDS = [
    "synthetic_ticks_per_m1",
    "instrument_decimal_precision",
    "spread_points",
    "source_timezone_policy",
    "source_timezone",
    "source_table",
    "ohlc_path_rule",
    "dataset_hash_rule",
    "price_precision_rule",
    "seed_streams",
    "description",
    "llm_reasoning",
]


def validate_deterministic_replay_v1_shape(sub_object: dict) -> list[str]:
    """Per locked §22.preferred_implementation.required_fields_no_skip:
    every field is REQUIRED, no skip. Returns list of missing-field names."""
    missing = []
    for field in REQUIRED_DETERMINISTIC_REPLAY_V1_FIELDS:
        if field not in sub_object:
            missing.append(field)
    return missing
