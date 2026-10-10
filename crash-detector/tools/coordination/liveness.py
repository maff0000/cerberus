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

HOW IT ACTUALLY DECIDES, AND WHY IT IS NOT THE ORDER THE DISPATCH PRESCRIBED
---------------------------------------------------------------------------
1. ``/proc/<pid>`` must exist. No directory, no process.
2. **If the record carries ``pid_start_time_ticks``, THAT IS AUTHORITATIVE.** ``/proc/<pid>/stat``
   field 22 is the process start time in clock ticks since boot. **A recycled PID cannot reproduce
   the original process's start time**, so this closes the PID-recycling class outright.
3. The cmdline fingerprint is recorded and compared, but a MISMATCH IS NOT DEATH when the start
   time matches — it is reported as ``cmdline DRIFTED``.

**THE THIRD POINT IS A CORRECTION TO THE DISPATCH AND IT WAS FORCED BY A MEASUREMENT.** The
dispatch specifies "``/proc/<pid>`` **plus a cmdline match**". Built literally, ``PLANT-COORD-04``
arms 1 and 3 both failed: ``launch.sh`` acquires the lease and then ``exec``s the seat, and
``exec`` keeps the process while REPLACING ITS COMMAND LINE — so every successfully launched seat
read as **dead one moment after starting**. That is not a conservative lease, it is an inoperative
one, and it is precisely the defect ``CD-PL-F143`` names: a seat declared dead while it was alive
and reading. The dispatch's *intent* — "a bare PID check is wrong the moment the OS recycles the
number" — is honoured by a strictly stronger test.

**THE DECLARED LIMIT THAT REMAINS:** a record written WITHOUT a start time (none is produced by
this increment; a hand-written one is possible) falls back to the cmdline prefix alone, and
:func:`is_live` returns ``degraded=True`` so every caller can print it. In that degraded mode a
recycled PID running a similar command line reads as ALIVE, and the class is NOT closed.
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

    # ------------------------------------------------------------------------------------------
    # START TIME IS AUTHORITATIVE WHEN IT IS RECORDED. CMDLINE IS SECONDARY AND ADVISORY.
    #
    # THIS ORDERING IS A CORRECTION TO WHAT THE DISPATCH PRESCRIBED, AND THE REASON IS MEASURED,
    # NOT ARGUED. `CD-DISPATCH-INC12-COORDINATION-ENGINEER` ITEM 4 says liveness is
    # "`/proc/<pid>` **plus a cmdline match**". Built exactly that way, PLANT-COORD-04 arms 1 and 3
    # BOTH FAILED, and the cause was structural rather than incidental:
    #
    #   `launch.sh` acquires the lease and THEN `exec`s the seat. `exec` keeps the process and
    #   REPLACES ITS COMMAND LINE. So the fingerprint recorded at acquire time ("sh launch.sh ...")
    #   never matches the cmdline a moment later ("the seat"), and EVERY SUCCESSFULLY LAUNCHED SEAT
    #   READ AS DEAD IMMEDIATELY. A lease that declares its own holder dead the instant the launch
    #   succeeds is not a conservative lease; it is an inoperative one, and it would have shipped
    #   the exact defect `CD-PL-F143` names — A SEAT DECLARED DEAD WHILE IT WAS ALIVE AND READING.
    #
    # The dispatch's INTENT is unambiguous and it is honoured: "a bare PID check is wrong the moment
    # the OS recycles the number". `/proc/<pid>/stat` field 22 answers that STRICTLY BETTER than a
    # cmdline match — a recycled PID cannot reproduce the original process's start time, whereas a
    # recycled PID running a similar wrapper CAN reproduce a cmdline prefix. So the stronger check
    # is used where it is available, the weaker one is retained where it is not, and cmdline drift
    # is RECORDED rather than treated as death.
    # ------------------------------------------------------------------------------------------
    if recorded_start_ticks is not None:
        if now_ticks is None:
            return Liveness(False, "START_TIME_UNREADABLE", True,
                            "/proc/%d/stat unreadable while /proc/%d exists" % (pid, pid))
        if now_ticks != recorded_start_ticks:
            return Liveness(False, "PID_RECYCLED", False,
                            "/proc/%d/stat field 22 = %d, record says %d — the number was reused"
                            % (pid, now_ticks, recorded_start_ticks))
        drift = ""
        if recorded_fingerprint and now_fp is not None and \
                not now_fp.startswith(recorded_fingerprint[:CMDLINE_FINGERPRINT_CHARS]):
            drift = ("; cmdline DRIFTED from %r to %r — expected after exec(), NOT treated as death"
                     % (recorded_fingerprint[:60], now_fp[:60]))
        return Liveness(True, "ALIVE", False,
                        "/proc/%d exists and /proc/%d/stat field 22 == %d, so PID recycling is "
                        "EXCLUDED%s" % (pid, pid, recorded_start_ticks, drift))

    # No start time recorded. Fall back to the cmdline prefix, and say the evidence is DEGRADED.
    if recorded_fingerprint:
        if now_fp is None:
            return Liveness(False, "CMDLINE_UNREADABLE", True,
                            "/proc/%d/cmdline unreadable" % pid)
        if not now_fp.startswith(recorded_fingerprint[:CMDLINE_FINGERPRINT_CHARS]):
            return Liveness(False, "CMDLINE_MISMATCH", True,
                            "/proc/%d/cmdline = %r, record says %r. NO START TIME WAS RECORDED, so "
                            "this cannot distinguish a recycled PID from an exec()'d one — DEGRADED."
                            % (pid, now_fp, recorded_fingerprint))
        return Liveness(True, "ALIVE_CMDLINE_ONLY", True,
                        "/proc/%d exists and the cmdline prefix matches; NO start time recorded, so "
                        "PID RECYCLING IS NOT EXCLUDED — DEGRADED evidence" % pid)

    return Liveness(True, "ALIVE_PID_ONLY", True,
                    "/proc/%d exists; NO cmdline fingerprint and NO start time recorded, so PID "
                    "RECYCLING IS NOT EXCLUDED — DEGRADED evidence" % pid)


def self_identity() -> Tuple[int, str, Optional[int]]:
    pid = os.getpid()
    return pid, cmdline_fingerprint(pid) or "", start_time_ticks(pid)
