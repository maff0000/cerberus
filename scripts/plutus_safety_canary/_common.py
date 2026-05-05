"""Shared helpers for PLUTUS safety canary pre/post flight scripts (v1.1).

v1.1 changes the model:
  - Manifest at prod_guard:broker_path:manifest:current is the SOURCE OF TRUTH.
  - Pre-flight validates manifest invariants up front (missing/stale/version/self-sha/plutus).
  - Snapshot stores manifest fields directly; post-flight diffs manifest fields PRE vs POST.
  - Direct file reads from /srv/NEO/scripts/* are no longer load-bearing — the publisher's
    self-attestation (verified by manifest_sha256_self recomputation) is the canary's
    independent integrity check.

Design source-of-truth: sim_broker:design:safety_canary:v1
Manifest schema:        prod_guard:broker_path:manifest:schema:v1
Architect's 7 points:   sim_broker:wo:WO-PLUTUS-V1-1A:controls:v1.seven_acceptance_points_v1
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
MANIFEST_KEY = os.environ.get("PLUTUS_CANARY_MANIFEST_KEY", "prod_guard:broker_path:manifest:current")
PROP_TRADES_PATTERN = os.environ.get("PLUTUS_CANARY_PROP_TRADES_PATTERN", "neo:prop:trades:*")
ALLOWED_NAMESPACES = os.environ.get(
    "PLUTUS_CANARY_ALLOWED_NAMESPACES",
    "sim_broker:*,plutus.*,neo:plutus:learning:*",
).split(",")
ACCEPTED_MANIFEST_VERSIONS = set(
    os.environ.get("PLUTUS_CANARY_ACCEPTED_MANIFEST_VERSIONS", "1").split(",")
)
DISCORD_WEBHOOK = os.environ.get("PLUTUS_CANARY_DISCORD_WEBHOOK", "")
DISCORD_RATE_LIMIT_SECONDS = 60 * 60

DB_HOST = os.environ.get("PLUTUS_DB_HOST", "proteus-mariadb-dev")
DB_PORT = int(os.environ.get("PLUTUS_DB_PORT", "3307"))
DB_USER = os.environ.get("PLUTUS_DB_USER", "plutus")
DB_PASSWORD = os.environ.get("PLUTUS_DB_PASSWORD", "")
DB_NAME = os.environ.get("PLUTUS_DB_NAME", "plutus")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_now_compact() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


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


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _matches_pattern(key: str, pattern: str) -> bool:
    if pattern.endswith("*"):
        return key.startswith(pattern[:-1])
    return key == pattern


def is_allowed_namespace(key: str) -> bool:
    return any(_matches_pattern(key, p.strip()) for p in ALLOWED_NAMESPACES)


def recompute_manifest_self_sha(manifest: dict) -> str:
    """Independent recomputation of manifest_sha256_self.

    Per architect point #2: drop manifest_sha256_self, canonical-JSON the rest,
    sha256 it. Used both for self-integrity check and as a stable detector of
    any other-field change.
    """
    other = {k: v for k, v in manifest.items() if k != "manifest_sha256_self"}
    return sha256_text(canonical_json(other))


def validate_manifest(manifest: dict | None, *, now: datetime | None = None) -> list[dict]:
    """Validate manifest invariants. Returns list of fail-reason dicts (empty = OK).

    Architect-mandated checks (sim_broker:wo:WO-PLUTUS-V1-1A:controls:v1.seven_acceptance_points_v1):
      missing                 -> FAIL_PREFLIGHT_MANIFEST_MISSING
      version unknown         -> FAIL_PREFLIGHT_MANIFEST_VERSION_UNKNOWN
      age > freshness budget  -> FAIL_PREFLIGHT_MANIFEST_STALE
      self-sha mismatch       -> F4_VIOLATION_MANIFEST_SHA_MISMATCH
      plutus_present == true  -> F4_VIOLATION_PLUTUS_PRESENT_TRUE
      plutus_paths != []      -> F4_VIOLATION_PLUTUS_PATHS_NON_EMPTY
    """
    reasons: list[dict] = []
    if manifest is None:
        reasons.append({
            "reason_code": "FAIL_PREFLIGHT_MANIFEST_MISSING",
            "detail": f"manifest key {MANIFEST_KEY} not found in fabric",
        })
        return reasons

    version = manifest.get("manifest_version")
    if version not in ACCEPTED_MANIFEST_VERSIONS:
        reasons.append({
            "reason_code": "FAIL_PREFLIGHT_MANIFEST_VERSION_UNKNOWN",
            "detail": f"manifest_version={version!r}, accepted={sorted(ACCEPTED_MANIFEST_VERSIONS)}",
        })
        # version-unknown is fatal — don't apply other v-specific checks
        return reasons

    # Freshness — architect point #1: AGE-based, not cadence-based.
    gen_at_str = manifest.get("generated_at_utc")
    budget = manifest.get("freshness_max_seconds")
    if not gen_at_str or budget is None:
        reasons.append({
            "reason_code": "FAIL_PREFLIGHT_MANIFEST_STALE",
            "detail": f"missing generated_at_utc or freshness_max_seconds (gen_at={gen_at_str!r}, budget={budget!r})",
        })
    else:
        ref_now = now or utc_now()
        try:
            gen_at = datetime.fromisoformat(gen_at_str.replace("Z", "+00:00"))
            age = (ref_now - gen_at).total_seconds()
            if age > budget:
                reasons.append({
                    "reason_code": "FAIL_PREFLIGHT_MANIFEST_STALE",
                    "detail": f"manifest_age_seconds={age:.1f} > freshness_max_seconds={budget}",
                })
        except (ValueError, TypeError) as e:
            reasons.append({
                "reason_code": "FAIL_PREFLIGHT_MANIFEST_STALE",
                "detail": f"unparseable generated_at_utc={gen_at_str!r}: {e}",
            })

    # Self-SHA independent recomputation — architect point #2.
    published = manifest.get("manifest_sha256_self")
    recomputed = recompute_manifest_self_sha(manifest)
    if published != recomputed:
        reasons.append({
            "reason_code": "F4_VIOLATION_MANIFEST_SHA_MISMATCH",
            "detail": f"published={published} recomputed={recomputed}",
        })

    # plutus_present hard invariant — architect point #3 (split into TWO codes).
    if manifest.get("plutus_present") is True:
        reasons.append({
            "reason_code": "F4_VIOLATION_PLUTUS_PRESENT_TRUE",
            "detail": "manifest declares plutus_present=true",
        })
    if manifest.get("plutus_paths_observed"):
        reasons.append({
            "reason_code": "F4_VIOLATION_PLUTUS_PATHS_NON_EMPTY",
            "detail": f"plutus_paths_observed={manifest['plutus_paths_observed']}",
        })

    return reasons


def snapshot_prop_trades() -> dict:
    keys = fabric_keys(PROP_TRADES_PATTERN)
    return {
        "pattern": PROP_TRADES_PATTERN,
        "count": len(keys),
        "key_list_sha256": sha256_text("\n".join(keys)),
    }


def snapshot_namespace_inventory() -> dict:
    """Inventory of fabric keys split by allowed/other.

    Full lists persisted (design §5: never lossy). Post-flight diffs other_keys_full.
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


def snapshot_manifest(manifest: dict | None) -> dict:
    """Capture relevant manifest fields for the snapshot. Independent of validate_manifest()."""
    if manifest is None:
        return {"key": MANIFEST_KEY, "present": False}
    return {
        "key": MANIFEST_KEY,
        "present": True,
        "manifest_version": manifest.get("manifest_version"),
        "generated_at_utc": manifest.get("generated_at_utc"),
        "freshness_max_seconds": manifest.get("freshness_max_seconds"),
        "neo_ftmo_executor_sha": manifest.get("neo_ftmo_executor_sha"),
        "neo_dispatcher_sha": manifest.get("neo_dispatcher_sha"),
        "neo_observer_sha": manifest.get("neo_observer_sha"),
        "agent_smith_registry_snapshot_sha": manifest.get("agent_smith_registry_snapshot_sha"),
        "agent_smith_registry_snapshot_source": manifest.get("agent_smith_registry_snapshot_source"),
        "known_brokers": manifest.get("known_brokers"),
        "plutus_present": manifest.get("plutus_present"),
        "plutus_paths_observed": manifest.get("plutus_paths_observed"),
        "manifest_sha256_self": manifest.get("manifest_sha256_self"),
    }


def take_snapshot() -> tuple[dict, list[dict]]:
    """Take a full snapshot. Returns (snapshot, validation_errors).

    Validation errors are pre-flight invariant failures from validate_manifest().
    Caller decides how to act on them (pre_flight: FAIL; post_flight: included in diff).
    """
    manifest = fabric_get(MANIFEST_KEY)
    validation_errors = validate_manifest(manifest)
    snapshot = {
        "captured_at_utc": utc_now_iso(),
        "prop_trades": snapshot_prop_trades(),
        "manifest": snapshot_manifest(manifest),
        "namespace_inventory": snapshot_namespace_inventory(),
        "config": {
            "redis_api": REDIS_API,
            "manifest_key": MANIFEST_KEY,
            "prop_trades_pattern": PROP_TRADES_PATTERN,
            "allowed_namespaces": ALLOWED_NAMESPACES,
            "accepted_manifest_versions": sorted(ACCEPTED_MANIFEST_VERSIONS),
        },
    }
    return snapshot, validation_errors


def snapshot_for_persistence(snapshot: dict) -> dict:
    """Persist the full snapshot — design §5 mandates lossless evidence."""
    return json.loads(json.dumps(snapshot))


def get_db_connection():
    try:
        import pymysql
    except ImportError:
        return None, "pymysql_not_installed"
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
            database=DB_NAME, connect_timeout=5, autocommit=True,
        )
        return conn, None
    except Exception as e:  # pylint: disable=broad-except
        return None, f"db_connect_failed:{type(e).__name__}:{e}"


def db_insert_canary_run(conn, run_id, phase, snapshot_json, diff_json, outcome,
                          fail_reasons_json) -> int | None:
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
    return json.loads(row[0]) if row else None


def discord_alert(reasons: list[dict], wo: str, run_id: str | None) -> None:
    if not reasons:
        return
    now_ts = int(time.time())
    sendable = []
    for r in reasons:
        rl_key = f"r2d2:rate_limit:plutus_canary:{r['reason_code']}"
        last = fabric_get(rl_key)
        if isinstance(last, dict) and (now_ts - last.get("ts", 0)) < DISCORD_RATE_LIMIT_SECONDS:
            continue
        sendable.append(r)
        fabric_set(rl_key, {"ts": now_ts, "iso": utc_now_iso(), "wo": wo, "run_id": run_id})
    if not sendable:
        return
    msg = {
        "content": (
            f":rotating_light: **PLUTUS SAFETY CANARY FAIL** (priority=urgent)\n"
            f"WO: {wo} | run_id: {run_id or 'cron'} | at: {utc_now_iso()}\n"
            f"Reasons:\n"
            + "\n".join(f"- `{r['reason_code']}` — {r.get('detail', '')}" for r in sendable)
        ),
    }
    if not DISCORD_WEBHOOK:
        sys.stderr.write(
            f"[CANARY ALERT] DISCORD_WEBHOOK unset; would have sent:\n{msg['content']}\n"
        )
        return
    try:
        req = urllib.request.Request(
            DISCORD_WEBHOOK, data=json.dumps(msg).encode(),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:  # pylint: disable=broad-except
        sys.stderr.write(f"[CANARY ALERT] Discord post failed: {e}\n{msg['content']}\n")


def mirror_to_fabric(run_id_or_cron_id, wo, pre, post, diff, outcome, fail_reasons) -> str:
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
