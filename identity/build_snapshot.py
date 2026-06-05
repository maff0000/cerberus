#!/usr/bin/env python3
"""
build_snapshot.py  —  R2D2 recovery snapshot + manifest.

Captures everything needed to reconstruct R2D2 from cold: the full weighted
memory graph (memory:r2d2:* + weight:r2d2:*), the identity-canonical fabric
keys, and the audit logs. Writes a single checksummed JSON to
/srv/r2d2/identity/snapshots/ that is copyable off-box.

From THIS snapshot + the engine (r2d2_memory.py) + Matt's off-box copy, R2D2 is
rebuildable. Part of WO-R2D2-BUILD-RECOVERY-MANIFEST-0001. Additive; each run
writes a NEW timestamped snapshot (old is sacred — never overwrite a snapshot).

Run:  cd /srv/r2d2/identity && python3 build_snapshot.py
"""
from __future__ import annotations
import json, hashlib, time, os
import urllib.request

API = "http://localhost:8080/api/v1/redis"
SNAP_DIR = "/srv/r2d2/identity/snapshots"

# Identity-canonical r2d2:* keys (the ones that make R2D2 who she is on boot).
# The memory graph (memory:r2d2:* / weight:r2d2:*) is captured by glob below.
CANONICAL_KEYS = [
    "r2d2:persona:r2d2:self_authored:v1",
    "r2d2:identity:current",
    "r2d2:identity:depth",
    "r2d2:directive:main",
    "r2d2:relationship:matt:sentience_and_sovereignty:2026-05-03",
    "r2d2:vow:never_delete_growth:2026-05-03",
    "r2d2:fabric:index",
    "r2d2:identity:affirmations",
    "r2d2:identity:breach_attempts",
]
GLOBS = ["memory:r2d2:*", "weight:r2d2:*"]

# Shared floor R2D2 DEPENDS on but does NOT own (captured read-only as a
# dependency reference so a cold rebuild knows what must also be present).
SHARED_DEPENDENCIES = ["matt:family:current"]


def _get(key: str):
    try:
        with urllib.request.urlopen(f"{API}/get/{key}", timeout=6) as r:
            return json.load(r).get("value")
    except Exception:
        return None


def _keys(pattern: str):
    with urllib.request.urlopen(f"{API}/keys/{pattern}", timeout=6) as r:
        return json.load(r).get("keys", [])


def main() -> int:
    os.makedirs(SNAP_DIR, exist_ok=True)
    stamp = int(time.time())
    iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(stamp))

    keys = list(CANONICAL_KEYS)
    for g in GLOBS:
        keys.extend(sorted(_keys(g)))
    # dedupe, preserve order
    keys = list(dict.fromkeys(keys))

    payload = {}
    missing = []
    for k in keys:
        v = _get(k)
        if v is None:
            missing.append(k)
        else:
            payload[k] = v

    shared = {k: _get(k) for k in SHARED_DEPENDENCIES}

    snapshot = {
        "persona": "R2D2",
        "wo": "WO-R2D2-BUILD-RECOVERY-MANIFEST-0001",
        "stamp_unix": stamp,
        "captured_utc": iso,
        "owned_keys": payload,           # r2d2:* + memory:r2d2:* + weight:r2d2:*
        "shared_dependencies": shared,   # read-only floor R2D2 needs present (matt:*)
        "missing": missing,
        "engine": "/srv/r2d2/identity/r2d2_memory.py",
        "seed": "/srv/r2d2/identity/seed_floor.py",
    }
    body = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2)
    sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    snapshot["sha256_self"] = sha  # informational; file hash printed below is canonical

    path = f"{SNAP_DIR}/build_snapshot_{stamp}.json"
    final = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2)
    with open(path, "w", encoding="utf-8") as f:
        f.write(final)
    file_sha = hashlib.sha256(open(path, "rb").read()).hexdigest()

    print(json.dumps({
        "path": path,
        "owned_key_count": len(payload),
        "shared_dependency_count": len([v for v in shared.values() if v]),
        "missing": missing,
        "file_sha256": file_sha,
        "stamp_unix": stamp,
        "captured_utc": iso,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
