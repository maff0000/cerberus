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

=====================================================================================================
``O_EXCL`` IS EXCLUSION ON A **FILENAME**, AND THE FILENAME IS THE **TASK ID**. IT IS NOT EXCLUSION
ON A **WRITE SCOPE**. **`CD-ASR-WO2R3-06-F04`.**
=====================================================================================================

That distinction cost 193 of 200 raced rounds. Two seats with DIFFERENT task ids and IDENTICAL write
scopes take DIFFERENT filenames, so ``O_EXCL`` **never fires**, and the only thing standing between
them was a directory read (the scope check) followed later by a write (the take) — a textbook TOCTOU
window. The ninth Assurance seat raced exactly that window and measured **193 double-takes on one
write scope, both seats printing ``VERDICT: CLAIMED``, both ``rc=0``**, in a registry whose own
sibling detector calls the resulting state a violation.

``PO-DECISIONS-0021`` ruling 3 states the invariant as *"no two live seats share a TASK **or a WRITE
SCOPE**"*. ``O_EXCL`` delivers the first conjunct only. :func:`critical_section` delivers the second.

**WHAT IT IS: A MUTEX AROUND THE DECISION, NOT AROUND THE WORK.** It is held across
*check-then-take* and released the instant the record is on disk — microseconds. It does **NOT**
serialise seats, it does **NOT** make the registry one-writer-at-a-time, and two seats taking
DISJOINT scopes concurrently both still succeed and both still proceed in parallel. **A DESIGN THAT
SERIALISED ALL CLAIMS WOULD PASS THE RACE HARNESS AND FAIL THE INCREMENT** — the invariant is
NON-OVERLAP, not one-writer-at-a-time (``PO-DECISIONS-0021`` ruling 3, preserved as the goal by
``PO-DECISIONS-0022`` ruling 1). ``PLANT-COORD-06`` arm 3 measures two disjoint claims taken
CONCURRENTLY, both ``CLAIMED``, both live at once.

**WHY ``flock`` AND NOT A LOCK FILE TAKEN WITH ``O_EXCL``:** a lock *file* leaks. A seat killed by
the operator's wrapper — which has happened on this project, and an entire Assurance audit ceased to
exist — leaves an ``O_EXCL`` lock file behind and every later claim deadlocks against a corpse, so
somebody adds a stale-lock timeout, and the timeout is the hole. ``flock`` is released by the KERNEL
when the holding descriptor closes, including on ``SIGKILL``. There is no stale state to reap and
therefore no reaping policy to get wrong.

**ITS DECLARED LIMITS, WHICH ARE REAL:**

* ``flock`` is advisory and process-local to this machine. **It binds every process that goes
  through these instruments and NOTHING ELSE.** A seat that hand-writes a claim file with an editor
  defeats it exactly as it always defeated the registry, and ``git`` is still the only witness.
* ``flock`` over NFS has the same reliability caveat as ``O_EXCL``. It is covered by the same
  refusal: :func:`assert_atomic_or_refuse` runs before the section is entered.
* It is bounded by :data:`LOCK_TIMEOUT_S`. **On timeout it RAISES and the caller REFUSES.** It does
  not proceed unlocked, because proceeding unlocked is the defect with a log line attached.
"""

from __future__ import annotations

import contextlib
import errno
import fcntl
import os
import socket
import subprocess
import sys
import time
from typing import Any, Dict, Iterator, List, Optional

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


# ------------------------------------------------------------------------------------------------
# CD-ASR-WO2R3-06-F04 — THE CHECK-THEN-TAKE CRITICAL SECTION.
# A mutex around the DECISION. Never around the WORK. See the module docstring.
# ------------------------------------------------------------------------------------------------

LOCK_NAME = ".registry.lock"
LOCK_TIMEOUT_S = 30.0
LOCK_POLL_S = 0.002


class RegistryLockUnavailable(RuntimeError):
    """The check-then-take section could not be entered. The caller REFUSES; it does not proceed."""


def lock_path(root: str, which: str) -> str:
    return os.path.join(registry_dir(root, which), LOCK_NAME)


@contextlib.contextmanager
def critical_section(root: str, which: str, timeout: float = LOCK_TIMEOUT_S) -> Iterator[str]:
    """Serialise **check-then-take** on one registry directory. NOT the work that follows it.

    Enter it around *"read every live record, decide, write the record"* and around nothing else.
    The section must contain no git call, no subprocess and no network wait — build the payload
    BEFORE entering, so that what is serialised is microseconds of decision and not seconds of
    setup. Every caller in this tree does exactly that, deliberately.
    """
    p = lock_path(root, which)
    fd = os.open(p, os.O_CREAT | os.O_RDWR, 0o644)
    deadline = time.monotonic() + timeout
    waited = 0.0
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK):
                    raise
                now = time.monotonic()
                if now >= deadline:
                    raise RegistryLockUnavailable(
                        "REGISTRY_LOCK_TIMEOUT: could not enter the check-then-take section on %s "
                        "within %.1fs (waited %.3fs). ANOTHER PROCESS IS INSIDE IT. This instrument "
                        "REFUSES rather than proceeding unlocked, because proceeding unlocked is "
                        "CD-ASR-WO2R3-06-F04 with a log line attached. (lock: %s, mechanism: "
                        "fcntl.flock LOCK_EX|LOCK_NB)" % (which, timeout, waited, p))
                time.sleep(LOCK_POLL_S)
                waited += LOCK_POLL_S
        yield p
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


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
