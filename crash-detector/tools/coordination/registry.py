#!/usr/bin/env python3
"""Registry paths and record I/O shared by the claim registry (ITEM 1) and the lease (ITEM 4).

**THE REGISTRY IS A DIRECTORY. THE FILESYSTEM IS THE LOCK.**

``PO-DECISIONS-0021`` ruling 3(a) requires that *"a task is atomically claimed before it is
worked"*. A shared YAML list file cannot deliver that: two seats read it, both append, one write
wins, and the loser's claim vanishes with no error anywhere — which is the *same* class of defect
the increment exists to remove, re-created inside its own remedy. So one file per record, and the
record is taken with

    os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)

``O_EXCL`` is the control. ``if os.path.exists(p): refuse`` followed by a write is **the defect,
not the control** — the window between the test and the write is a TOCTOU window, and two seats
interleaved inside it both succeed. ``PLANT-COORD-01`` arm 2 is that exact mutation and it
demonstrates two holders of one task.

MEASURED ON THIS FILESYSTEM, NOT ASSUMED
----------------------------------------
``stat -f -c %T /srv/crash-detector-inc12`` -> ``ext2/ext3``. 200 rounds of 32 concurrent
processes racing ``O_EXCL`` on one path produced **exactly 200 successes out of 6400 attempts**
(``governance/coordination/evidence/EV-ATOMICITY-MEASUREMENT.md``). ``O_EXCL`` is atomic here.

**THE DECLARED LIMIT:** ``O_EXCL`` is documented as NOT atomic over NFS before NFSv3, and this
measurement is of THIS filesystem at THIS moment. :func:`assert_atomic_or_refuse` re-measures the
filesystem type at runtime and REFUSES on a network filesystem rather than assuming the property
travels.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml  # noqa: E402

from common import repo_root, utc_now  # noqa: E402

CLAIMS_DIR = "governance/coordination/claims"
LEASES_DIR = "governance/coordination/leases"
MERGES_DIR = "governance/coordination/merges"
ACCOUNTABLE_SEAT_FILE = "governance/coordination/ACCOUNTABLE-SEAT.yaml"
BLOCKS_FILE = "governance/coordination/BUILD-LOG-ID-BLOCKS.yaml"

CLAIM_SUFFIX = ".claim.yaml"
LEASE_SUFFIX = ".lease.yaml"

STATE_CLAIMED = "CLAIMED"
STATE_RELEASED = "RELEASED"
STATE_ABANDONED = "ABANDONED"

# Filesystem magic names (from `stat -f -c %T`) on which O_EXCL create is NOT relied upon.
REFUSED_FILESYSTEMS = {"nfs", "nfs4", "smb2", "cifs", "fuseblk", "9p", "afs", "ceph", "gfs2"}


def fs_type(path: str) -> str:
    out = subprocess.run(["stat", "-f", "-c", "%T", path], capture_output=True, text=True)
    return out.stdout.strip() or "UNKNOWN"


def assert_atomic_or_refuse(path: str) -> str:
    """Re-measure the filesystem. REFUSE rather than assume the atomicity property travels."""
    t = fs_type(path)
    if t.lower() in REFUSED_FILESYSTEMS:
        raise RuntimeError(
            "ATOMICITY_NOT_ESTABLISHED: %s is on filesystem %r. O_EXCL create is not relied upon "
            "here. A registry whose atomicity is assumed is worse than none — refusing. "
            "(command: stat -f -c %%T %s)" % (path, t, path))
    return t


def registry_dir(root: str, which: str) -> str:
    d = os.path.join(root, which)
    os.makedirs(d, exist_ok=True)
    return d


def record_path(root: str, which: str, ident: str, suffix: str) -> str:
    safe = safe_identifier(ident)
    return os.path.join(registry_dir(root, which), safe + suffix)


_ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")


def safe_identifier(ident: str) -> str:
    """A task or lease id must be a filename. REFUSE anything that is not, rather than sanitising.

    Sanitising would silently map two distinct task ids onto one file, which is the collision this
    registry exists to prevent, arriving through the door of the fix.
    """
    if not ident:
        raise ValueError("identifier is empty")
    if ident in (".", ".."):
        raise ValueError("identifier %r is a path component, not an id" % ident)
    bad = sorted({c for c in ident if c not in _ALLOWED})
    if bad:
        raise ValueError("identifier %r contains characters this registry refuses: %r. "
                         "Ids must match [A-Za-z0-9._-]+ so that one id is one file and two ids are "
                         "never one file." % (ident, "".join(bad)))
    return ident


def write_exclusive(path: str, payload: Dict[str, Any]) -> None:
    """THE ATOMIC TAKE. ``FileExistsError`` propagates to the caller and IS the refusal."""
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            yaml.safe_dump(payload, fh, sort_keys=False, default_flow_style=False, allow_unicode=True)
            fh.flush()
            os.fsync(fh.fileno())
    except Exception:
        os.unlink(path)
        raise


def rewrite(path: str, payload: Dict[str, Any]) -> None:
    """Update an EXISTING record in place. Not a take; the holder already owns the file."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False, default_flow_style=False, allow_unicode=True)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def load(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError("%s does not contain a mapping" % path)
    return data


def list_records(root: str, which: str, suffix: str) -> List[Dict[str, Any]]:
    d = registry_dir(root, which)
    out = []
    for name in sorted(os.listdir(d)):
        if not name.endswith(suffix):
            continue
        p = os.path.join(d, name)
        try:
            rec = load(p)
        except Exception as exc:
            rec = {"__unparseable__": str(exc)}
        rec["__path__"] = os.path.relpath(p, root)
        out.append(rec)
    return out


def live_records(records: List[Dict[str, Any]], state_key: str = "state") -> List[Dict[str, Any]]:
    return [r for r in records if r.get(state_key) == STATE_CLAIMED]


def accountable_seat(root: str) -> Dict[str, Any]:
    """FAIL CLOSED if the derivation record is missing. Never default to 'everyone may write'."""
    p = os.path.join(root, ACCOUNTABLE_SEAT_FILE)
    if not os.path.exists(p):
        raise RuntimeError("PRECONDITION_NOT_MET: %s does not exist. The accountable seat is a "
                           "DERIVED product fact (CD-RULE-003) and this instrument will not invent "
                           "one." % ACCOUNTABLE_SEAT_FILE)
    data = load(p)
    for key in ("accountable_seat", "shared_record_files"):
        if not data.get(key):
            raise RuntimeError("PRECONDITION_NOT_MET: %s is missing %r" % (ACCOUNTABLE_SEAT_FILE, key))
    return data


def hostname() -> str:
    return socket.gethostname()


def now() -> str:
    return utc_now()


def root_from(cwd: Optional[str] = None) -> str:
    return repo_root(cwd)
