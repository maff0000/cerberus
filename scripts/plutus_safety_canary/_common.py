"""Shared helpers for PLUTUS safety canary pre/post flight scripts.

Design source-of-truth: sim_broker:design:safety_canary:v1
WO: WO-PLUTUS-V1-1A
"""
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

REDIS_API = os.environ.get("REDIS_FABRIC_API", "http://localhost:8080/api/v1/redis")
EXECUTOR_PATH = os.environ.get("PLUTUS_CANARY_EXECUTOR_PATH", "/srv/NEO/scripts/neo_ftmo_executor.py")
REGISTRY_KEY = os.environ.get("PLUTUS_CANARY_REGISTRY_KEY", "agent_smith:registry:dump")
PROP_TRADES_PATTERN = os.environ.get("PLUTUS_CANARY_PROP_TRADES_PATTERN", "neo:prop:trades:*")
ALLOWED_NAMESPACES = os.environ.get(
    "PLUTUS_CANARY_ALLOWED_NAMESPACES",
    "sim_broker:*,plutus.*,neo:plutus:learning:*",
).split(",")
DISCORD_WEBHOOK = os.environ.get("PLUTUS_CANARY_DISCORD_WEBHOOK", "")
DISCORD_RATE_LIMIT_SECONDS = 60 * 60

DB_HOST = os.environ.get("PLUTUS_DB_HOST", "proteus-mariadb-dev")
DB_PORT = int(os.environ.get("PLUTUS_DB_PORT", "3307"))
DB_USER = os.environ.get("PLUTUS_DB_USER", "plutus")
DB_PASSWORD = os.environ.get("PLUTUS_DB_PASSWORD", "")
DB_NAME = os.environ.get("PLUTUS_DB_NAME", "plutus")


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
        f"{REDIS_API}/set",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=5)


def fabric_keys(pattern: str) -> list[str]:
    with urllib.request.urlopen(f"{REDIS_API}/keys/{pattern}", timeout=10) as resp:
        data = json.loads(resp.read())
    return sorted(data.get("keys", []))


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_text(s: str) -> str:
    return sha256_bytes(s.encode("utf-8"))


def sha256_canonical_json(obj) -> str:
    return sha256_text(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str))


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _matches_pattern(key: str, pattern: str) -> bool:
    """Glob-ish: only trailing * supported (matches design allowed-namespaces shape).
    sim_broker:* -> startswith('sim_broker:')
    plutus.*     -> startswith('plutus.')
    """
    if pattern.endswith("*"):
        return key.startswith(pattern[:-1])
    return key == pattern


def is_allowed_namespace(key: str) -> bool:
    return any(_matches_pattern(key, p.strip()) for p in ALLOWED_NAMESPACES)


def snapshot_prop_trades() -> dict:
    keys = fabric_keys(PROP_TRADES_PATTERN)
    return {
        "pattern": PROP_TRADES_PATTERN,
        "count": len(keys),
        "key_list_sha256": sha256_text("\n".join(keys)),
    }


def snapshot_executor() -> dict:
    if not os.path.exists(EXECUTOR_PATH):
        return {
            "path": EXECUTOR_PATH,
            "exists": False,
            "size_bytes": None,
            "sha256": None,
            "error": "FAIL_PREFLIGHT_EXECUTOR_MISSING",
        }
    return {
        "path": EXECUTOR_PATH,
        "exists": True,
        "size_bytes": os.path.getsize(EXECUTOR_PATH),
        "sha256": sha256_file(EXECUTOR_PATH),
    }


def snapshot_agent_smith_registry() -> dict:
    """Hash the canonical agent_smith:registry:dump value.

    Per design edge case: missing key = FAIL LOUD with reason
    FAIL_PREFLIGHT_AGENT_SMITH_REGISTRY_MISSING (no silent skip).
    """
    val = fabric_get(REGISTRY_KEY)
    if val is None:
        return {
            "key": REGISTRY_KEY,
            "exists": False,
            "sha256": None,
            "error": "FAIL_PREFLIGHT_AGENT_SMITH_REGISTRY_MISSING",
        }
    if isinstance(val, (dict, list)):
        sha = sha256_canonical_json(val)
    else:
        sha = sha256_text(str(val))
    return {"key": REGISTRY_KEY, "exists": True, "sha256": sha}


def snapshot_namespace_inventory() -> dict:
    """Inventory of fabric keys split by allowed/other.

    For pre/post diff: post-flight detects new keys outside allowed namespaces.
    Full lists are persisted (design §5: snapshot_json is never lossy).
    """
    all_keys = fabric_keys("*")
    allowed = sorted(k for k in all_keys if is_allowed_namespace(k))
    other = sorted(k for k in all_keys if not is_allowed_namespace(k))
    return {
        "allowed_count": len(allowed),
        "other_count": len(other),
        "allowed_keys_sha256": sha256_text("\n".join(allowed)),
        "other_keys_sha256": sha256_text("\n".join(other)),
        "other_keys_full": other,
        "allowed_keys_full": allowed,
    }


def take_snapshot() -> dict:
    return {
        "captured_at_utc": utc_now_iso(),
        "prop_trades": snapshot_prop_trades(),
        "executor": snapshot_executor(),
        "agent_smith_registry": snapshot_agent_smith_registry(),
        "namespace_inventory": snapshot_namespace_inventory(),
        "config": {
            "redis_api": REDIS_API,
            "executor_path": EXECUTOR_PATH,
            "registry_key": REGISTRY_KEY,
            "prop_trades_pattern": PROP_TRADES_PATTERN,
            "allowed_namespaces": ALLOWED_NAMESPACES,
        },
    }


def snapshot_for_persistence(snapshot: dict) -> dict:
    """Persist the full snapshot — design §5 mandates lossless evidence."""
    return json.loads(json.dumps(snapshot))


def collect_snapshot_errors(snapshot: dict) -> list[str]:
    errors = []
    if snapshot["executor"].get("error"):
        errors.append(snapshot["executor"]["error"])
    if snapshot["agent_smith_registry"].get("error"):
        errors.append(snapshot["agent_smith_registry"]["error"])
    return errors


def get_db_connection():
    """Best-effort plutus DB connection. Returns None if pymysql unavailable
    or DB unreachable — caller decides whether to FAIL or proceed in --no-db.
    """
    try:
        import pymysql
    except ImportError:
        return None, "pymysql_not_installed"
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=5,
            autocommit=True,
        )
        return conn, None
    except Exception as e:  # pylint: disable=broad-except
        return None, f"db_connect_failed:{type(e).__name__}:{e}"


def db_insert_canary_run(
    conn,
    run_id: str | None,
    phase: str,
    snapshot_json: str,
    diff_json: str | None,
    outcome: str,
    fail_reasons_json: str | None,
) -> int | None:
    """Insert a row into plutus.safety_canary_runs. Returns canary_id or None."""
    sql = (
        "INSERT INTO plutus.safety_canary_runs "
        "(run_id, phase, snapshot_json, diff_json, outcome, fail_reasons_json) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )
    with conn.cursor() as cur:
        cur.execute(sql, (run_id, phase, snapshot_json, diff_json, outcome, fail_reasons_json))
        return cur.lastrowid


def db_get_pre_snapshot(conn, run_id: str) -> dict | None:
    sql = (
        "SELECT snapshot_json FROM plutus.safety_canary_runs "
        "WHERE run_id = %s AND phase = 'PRE' "
        "ORDER BY ran_at_utc DESC LIMIT 1"
    )
    with conn.cursor() as cur:
        cur.execute(sql, (run_id,))
        row = cur.fetchone()
    if not row:
        return None
    return json.loads(row[0])


def discord_alert(reasons: list[dict], wo: str, run_id: str | None) -> None:
    """Best-effort Discord critical alert with per-reason rate limit.

    Rate limit: 1 alert per 60 minutes per failure_reason (design §4).
    Tracked via fabric key r2d2:rate_limit:plutus_canary:<reason>:<date_hour>.
    """
    if not reasons:
        return
    now_ts = int(time.time())
    sendable_reasons = []
    for r in reasons:
        rl_key = f"r2d2:rate_limit:plutus_canary:{r['reason_code']}"
        last = fabric_get(rl_key)
        if isinstance(last, dict) and (now_ts - last.get("ts", 0)) < DISCORD_RATE_LIMIT_SECONDS:
            continue
        sendable_reasons.append(r)
        fabric_set(rl_key, {"ts": now_ts, "iso": utc_now_iso(), "wo": wo, "run_id": run_id})
    if not sendable_reasons:
        return
    msg = {
        "content": (
            f":rotating_light: **PLUTUS SAFETY CANARY FAIL** (priority=urgent)\n"
            f"WO: {wo} | run_id: {run_id or 'cron'} | at: {utc_now_iso()}\n"
            f"Reasons:\n"
            + "\n".join(f"- `{r['reason_code']}` — {r.get('detail', '')}" for r in sendable_reasons)
        ),
    }
    if not DISCORD_WEBHOOK:
        sys.stderr.write(
            f"[CANARY ALERT] DISCORD_WEBHOOK unset; would have sent:\n{msg['content']}\n"
        )
        return
    try:
        req = urllib.request.Request(
            DISCORD_WEBHOOK,
            data=json.dumps(msg).encode(),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:  # pylint: disable=broad-except
        sys.stderr.write(f"[CANARY ALERT] Discord post failed: {e}\n{msg['content']}\n")


def mirror_to_fabric(run_id_or_cron_id: str, wo: str, pre: dict | None, post: dict | None,
                     diff: dict | None, outcome: str, fail_reasons: list[dict] | None) -> str:
    """Write/update sim_broker:reports:safety:<run_id>:v1."""
    key = f"sim_broker:reports:safety:{run_id_or_cron_id}:v1"
    existing = fabric_get(key) or {}
    payload = {
        "wo": wo,
        "run_id": run_id_or_cron_id,
        "pre": existing.get("pre") if pre is None else pre,
        "post": existing.get("post") if post is None else post,
        "diff": existing.get("diff") if diff is None else diff,
        "fail_reasons": existing.get("fail_reasons") if fail_reasons is None else fail_reasons,
        "final_outcome": outcome,
        "_mirror_updated_at_utc": utc_now_iso(),
    }
    fabric_set(key, payload)
    return key
