#!/usr/bin/env python3
"""LIVENESS, MEASURED — not assumed, and not from a bare PID.

``PO-DECISIONS-0021`` ruling 3(d) turns on whether another session is *live*. Every wrong answer
here is expensive in one of two directions:

* **Wrongly ALIVE** — a dead seat's claim blocks the project forever and the next actor learns to
  delete claim files by hand, which is the control being trained out of existence.
* **Wrongly DEAD** — the ruling-2 incident, reproduced. ``CD-PL-F143`` on this project's record is
  exactly this: a HIGH finding raised against a seat that was *declared dead while it was alive and
  reading*, and then WITHDRAWN.

So liveness is ``/proc/<pid>`` **plus a cmdline match**. A bare PID check is wrong the moment the
operating system recycles the number, and PID recycling is not exotic — it is guaranteed on any
long-running host.

The recorded ``pid_cmdline_fingerprint`` is the process's ``/proc/<pid>/cmdline`` with NULs turned
into spaces, TRUNCATED to :data:`CMDLINE_FINGERPRINT_CHARS` characters. Liveness requires the
current cmdline to start with the recorded fingerprint.

**THE DECLARED LIMIT, AND IT IS REAL:** a recycled PID that happens to be running a command line
with the same prefix reads as ALIVE. On this host the seats are launched by wrappers whose command
lines differ in their prompt-file argument, so the prefix distinguishes them — but the class is not
closed and this module does not claim it is. The residue is carried by
:func:`start_time_ticks`: the claim/lease also records ``/proc/<pid>/stat`` field 22 (process start
time in clock ticks since boot), and liveness requires THAT to match too. A recycled PID cannot
reproduce the original process's start time, so with the start-time field present the class IS
closed for PID recycling. Records written WITHOUT that field (there are none produced by this
increment, but a hand-written one is possible) fall back to the cmdline prefix only, and
:func:`is_live` reports ``degraded=True`` so the caller can print it.
"""

from __future__ import annotations

import os
from typing import NamedTuple, Optional, Tuple

CMDLINE_FINGERPRINT_CHARS = 160


def read_cmdline(pid: int) -> Optional[str]:
    try:
        with open("/proc/%d/cmdline" % pid, "rb") as fh:
            raw = fh.read()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None
    return raw.replace(b"\x00", b" ").decode("utf-8", "replace").strip()


def cmdline_fingerprint(pid: int) -> Optional[str]:
    cl = read_cmdline(pid)
    if cl is None:
        return None
    return cl[:CMDLINE_FINGERPRINT_CHARS]


def start_time_ticks(pid: int) -> Optional[int]:
    """Field 22 of ``/proc/<pid>/stat`` — start time in clock ticks since boot.

    Parsed by splitting AFTER the final ``)`` because the process name in field 2 may contain
    spaces and parentheses. This is the standard, and the naive ``split()[21]`` is the standard bug.
    """
    try:
        with open("/proc/%d/stat" % pid, "r") as fh:
            data = fh.read()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None
    close = data.rfind(")")
    if close < 0:
        return None
    fields = data[close + 2:].split()
    # after "(comm)" the next field is state == field 3, so field 22 is index 19 here
    try:
        return int(fields[19])
    except (IndexError, ValueError):
        return None


class Liveness(NamedTuple):
    live: bool
    reason: str
    degraded: bool
    evidence: str


def is_live(pid: Optional[int], recorded_fingerprint: Optional[str],
            recorded_start_ticks: Optional[int] = None) -> Liveness:
    """MEASURE whether the recorded process is still the process that is running."""
    if pid is None:
        return Liveness(False, "NO_PID_RECORDED", True,
                        "the record names no pid; liveness is unmeasurable, treated as DEAD")
    proc = "/proc/%d" % pid
    if not os.path.isdir(proc):
        return Liveness(False, "NO_SUCH_PROCESS", False,
                        "os.path.isdir('%s') is False" % proc)

    now_ticks = start_time_ticks(pid)
    now_fp = cmdline_fingerprint(pid)

    if recorded_start_ticks is not None:
        if now_ticks is None:
            return Liveness(False, "START_TIME_UNREADABLE", True,
                            "/proc/%d/stat unreadable while /proc/%d exists" % (pid, pid))
        if now_ticks != recorded_start_ticks:
            return Liveness(False, "PID_RECYCLED", False,
                            "/proc/%d/stat field 22 = %d, record says %d — the number was reused"
                            % (pid, now_ticks, recorded_start_ticks))

    if recorded_fingerprint:
        if now_fp is None:
            return Liveness(False, "CMDLINE_UNREADABLE", True,
                            "/proc/%d/cmdline unreadable" % pid)
        if not now_fp.startswith(recorded_fingerprint[:CMDLINE_FINGERPRINT_CHARS]):
            return Liveness(False, "CMDLINE_MISMATCH", False,
                            "/proc/%d/cmdline = %r, record says %r"
                            % (pid, now_fp, recorded_fingerprint))
    else:
        return Liveness(True, "ALIVE_PID_ONLY", True,
                        "/proc/%d exists; NO cmdline fingerprint recorded, so PID RECYCLING IS NOT "
                        "EXCLUDED — this record is DEGRADED evidence" % pid)

    degraded = recorded_start_ticks is None
    return Liveness(True, "ALIVE", degraded,
                    "/proc/%d exists; cmdline prefix matches%s"
                    % (pid, "" if not degraded else "; NO start-time recorded, PID recycling not excluded"))


def self_identity() -> Tuple[int, str, Optional[int]]:
    pid = os.getpid()
    return pid, cmdline_fingerprint(pid) or "", start_time_ticks(pid)
