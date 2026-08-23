#!/usr/bin/env python3
"""THE LAUNCH LEASE — increment 12 ITEM 4, ``PO-DECISIONS-0021`` ruling 3(d).

The ruling: *"A LAUNCH LEASE binding BOTH writers — the driver AND the PO's own hand — refusing a
launch whose task or write scope overlaps a live session's; **disjoint-scope launches proceed
freely and in parallel**."*

    lease.py acquire --lease ID --seat S --task T --write-scope G [--read-scope G] [--exec-check]
    lease.py release --lease ID --seat S
    lease.py list [--all]
    lease.py reap  --lease ID --reason R
    lease.py check --task T --write-scope G [--read-scope G]     # would this be admitted?

One file per lease under ``governance/coordination/leases/``, taken with **the same ``O_EXCL``
mechanism as ITEM 1** — see ``registry.py`` for the measurement that it is atomic here.

WHAT IT REFUSES
---------------
* the requested **TASK** overlaps a live lease's task;
* the requested **WRITE** scope overlaps a live lease's **WRITE** scope;
* the requested **WRITE** scope overlaps a live lease's **READ** scope — ``CD-PL-F134``, the auditor
  whose reading material moved under it.

WHAT IT MUST ADMIT, AND THIS IS AN EQUAL REQUIREMENT
-----------------------------------------------------
*** **A LAUNCH WHOSE TASK AND SCOPES ARE DISJOINT — CONCURRENTLY, WITH THE OTHER LEASE STILL LIVE
AND UNDISTURBED.** ***

**A LEASE THAT SERIALISES IS A FAILED ITEM.** ``PO-DECISIONS-0021`` ruling 3 carries Matt's own
direction: *"multiple PLs / engineers on non-overlapping fixed tasks is fine, and great if it is
faster."* A control that refuses every parallel launch satisfies "no two seats overlap" vacuously,
and this project has a long record of vacuous greens.

LIVENESS IS MEASURED, NEVER ASSUMED, AND ``acquire`` NEVER REAPS
-----------------------------------------------------------------
See ``liveness.py``: ``/proc/<pid>`` **plus a cmdline match plus the process start time**. A bare
PID check is wrong the moment the OS recycles the number, and this project has already declared a
seat dead while it was alive and reading (``CD-PL-F143``, a HIGH finding raised against a live seat
and then WITHDRAWN).

**A STALE LEASE IS REAPED BY AN EXPLICIT ``reap`` COMMAND THAT WRITES WHY. NEVER SILENTLY BY
``acquire``.** Silent reaping on acquire is exactly ``PLANT-COORD-04`` arm 2 — the mutation that
reproduces ``PO-DECISIONS-0021`` ruling 2 on demand.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import liveness  # noqa: E402
import registry  # noqa: E402
import scope as scope_mod  # noqa: E402
from common import Limit, current_branch, repo_root, resolve_sha, say_command, tree_banner  # noqa: E402

LIMITS = [
    "DECIDES: refusal of a lease whose TASK equals a live lease's task.",
    "DECIDES: refusal of a lease whose WRITE scope overlaps a live lease's WRITE scope.",
    "DECIDES: refusal of a lease whose WRITE scope overlaps a live lease's READ scope (CD-PL-F134).",
    "ADMITS — AND THIS IS AN EQUAL REQUIREMENT — a launch whose task and scopes are disjoint, "
    "concurrently, with the other lease still live and undisturbed. A LEASE THAT SERIALISES IS A "
    "FAILED ITEM (PO-DECISIONS-0021 ruling 3).",
    "MEASURES liveness by /proc/<pid> + cmdline prefix + process start time. PID recycling is "
    "EXCLUDED for records carrying the start-time field; records without it are reported DEGRADED.",
    "DOES NOT DECIDE: a launcher that never asks for a lease. THE OPERATOR'S WRAPPER IS NOT IN THIS "
    "REPOSITORY (VERDICT-META-ASSURANCE-01-SECOND-SEAT.md §7.2) and nothing here can reach it.",
    "DOES NOT DECIDE: a lease acquired and then a DIFFERENT scope written. The lease records an "
    "intention; merge_reconcile.py assertion (1) reads what was actually touched, afterwards.",
]

RESIDUE = ("BINDING THE LAUNCHER is NOT PROVED TO BE CARRIED ANYWHERE for any launch that does not "
           "go through `tools/coordination/launch.sh`. The operator's wrapper lives outside the "
           "repository; no seat and no framework in this tree can reach it. See ITEM 4(ii)'s "
           "CD-RULE-006 declaration and Q12.")


def lease_path(root: str, ident: str) -> str:
    return registry.record_path(root, registry.LEASES_DIR, ident, registry.LEASE_SUFFIX)


def all_leases(root: str) -> List[Dict[str, Any]]:
    return registry.list_records(root, registry.LEASES_DIR, registry.LEASE_SUFFIX)


def live_leases(root: str) -> List[Dict[str, Any]]:
    out = []
    for r in all_leases(root):
        if r.get("state") != registry.STATE_CLAIMED:
            continue
        lv = liveness.is_live(r.get("pid"), r.get("pid_cmdline_fingerprint"),
                              r.get("pid_start_time_ticks"))
        r["__liveness__"] = lv
        if lv.live:
            out.append(r)
    return out


def collision(root: str, task: str, write_scope: List[str], read_scope: List[str]
              ) -> Optional[Tuple[Dict[str, Any], str, List[str]]]:
    """Return ``(other_lease, reason, evidence)`` or ``None`` if the launch is ADMITTED."""
    for other in live_leases(root):
        if other.get("task_id") == task:
            return other, "TASK_OVERLAP", ["requested task %r is held by lease %r" % (task, other.get("lease_id"))]
        ow = list(other.get("write_scope") or [])
        orr = list(other.get("read_scope") or [])
        if write_scope and ow:
            ov, hits = scope_mod.overlaps(write_scope, ow)
            if ov:
                return other, "WRITE_WRITE_OVERLAP", hits
        if write_scope and orr:
            ov, hits = scope_mod.overlaps(write_scope, orr)
            if ov:
                return other, "WRITE_READ_OVERLAP_CD_PL_F134", hits
        if read_scope and ow:
            ov, hits = scope_mod.overlaps(ow, read_scope)
            if ov:
                return other, "READ_WRITE_OVERLAP_CD_PL_F134", hits
    return None


def describe(rec: Dict[str, Any]) -> str:
    lv = rec.get("__liveness__") or liveness.is_live(
        rec.get("pid"), rec.get("pid_cmdline_fingerprint"), rec.get("pid_start_time_ticks"))
    return ("lease=%s seat=%s task=%s pid=%s acquired=%s state=%s liveness=%s (%s)"
            % (rec.get("lease_id"), rec.get("seat_actor_id"), rec.get("task_id"), rec.get("pid"),
               rec.get("acquired_utc"), rec.get("state"),
               "LIVE" if lv.live else "DEAD/" + lv.reason, lv.evidence))


def cmd_acquire(root: str, args: argparse.Namespace) -> int:
    registry.assert_atomic_or_refuse(os.path.join(root, registry.LEASES_DIR))
    write_scope = [p.raw for p in scope_mod.parse_scope(args.write_scope)]
    read_scope = [p.raw for p in scope_mod.parse_scope(args.read_scope)] if args.read_scope else []

    coll = collision(root, args.task, write_scope, read_scope)
    if coll:
        other, reason, hits = coll
        print("VERDICT: LAUNCH REFUSED — %s" % reason)
        print("   requested: seat=%s task=%s write_scope=%s read_scope=%s"
              % (args.seat, args.task, write_scope, read_scope))
        print("   collided with LIVE lease:")
        print("      %s" % describe(other))
        print("      record: %s" % other.get("__path__"))
        for h in hits:
            print("      %s" % h)
        return 1

    pid, fp, ticks = liveness.self_identity()
    if args.pid:
        pid = int(args.pid)
        fp = liveness.cmdline_fingerprint(pid) or ""
        ticks = liveness.start_time_ticks(pid)

    payload = {
        "record_type": "LAUNCH_LEASE",
        "lease_id": args.lease,
        "seat_actor_id": args.seat,
        "task_id": args.task,
        "pid": pid,
        "pid_cmdline_fingerprint": fp,
        "pid_start_time_ticks": ticks,
        "hostname": registry.hostname(),
        "acquired_utc": registry.now(),
        "base_sha": resolve_sha(args.base or "HEAD", cwd=root),
        "branch": args.branch or current_branch(root),
        "worktree": args.worktree or root,
        "write_scope": write_scope,
        "read_scope": read_scope,
        "state": registry.STATE_CLAIMED,
        "provenance": {
            "acquired_utc_command": "date -u +%FT%TZ",
            "atomicity": "os.open(path, O_CREAT|O_EXCL|O_WRONLY) — FileExistsError is the refusal",
            "liveness_method": "/proc/<pid> + cmdline prefix + /proc/<pid>/stat field 22",
        },
    }
    path = lease_path(root, args.lease)
    try:
        registry.write_exclusive(path, payload)
    except FileExistsError:
        existing = registry.load(path)
        print("VERDICT: LAUNCH REFUSED — LEASE ID ALREADY EXISTS")
        print("   %s" % describe(existing))
        print("   NOTE: a DEAD holder is still a refusal. `lease.py reap --lease %s --reason ...` "
              "is explicit and `acquire` NEVER reaps." % args.lease)
        return 1

    print("VERDICT: LEASE ACQUIRED — THE LAUNCH MAY PROCEED")
    print("   lease=%s seat=%s task=%s pid=%d" % (args.lease, args.seat, args.task, pid))
    print("   record: %s" % os.path.relpath(path, root))
    say_command("live_leases_after", len(live_leases(root)),
                "python3 -B tools/coordination/lease.py list")
    return 0


def cmd_check(root: str, args: argparse.Namespace) -> int:
    write_scope = [p.raw for p in scope_mod.parse_scope(args.write_scope)]
    read_scope = [p.raw for p in scope_mod.parse_scope(args.read_scope)] if args.read_scope else []
    coll = collision(root, args.task, write_scope, read_scope)
    if coll:
        other, reason, hits = coll
        print("VERDICT: WOULD BE REFUSED — %s" % reason)
        print("   %s" % describe(other))
        for h in hits:
            print("   %s" % h)
        return 1
    print("VERDICT: WOULD BE ADMITTED — task and scopes are disjoint from every live lease")
    say_command("live_leases", len(live_leases(root)),
                "python3 -B tools/coordination/lease.py list")
    return 0


def cmd_release(root: str, args: argparse.Namespace) -> int:
    path = lease_path(root, args.lease)
    if not os.path.exists(path):
        print("VERDICT: RELEASE REFUSED — no lease %r" % args.lease)
        return 1
    rec = registry.load(path)
    if rec.get("seat_actor_id") != args.seat:
        print("VERDICT: RELEASE REFUSED — NOT THE HOLDING SEAT (holder=%s, requested by=%s)"
              % (rec.get("seat_actor_id"), args.seat))
        return 1
    rec["state"] = registry.STATE_RELEASED
    rec["released_utc"] = registry.now()
    rec.pop("__path__", None)
    registry.rewrite(path, rec)
    print("VERDICT: RELEASED — lease=%s" % args.lease)
    return 0


def cmd_reap(root: str, args: argparse.Namespace) -> int:
    path = lease_path(root, args.lease)
    if not os.path.exists(path):
        print("VERDICT: REAP REFUSED — no lease %r" % args.lease)
        return 1
    rec = registry.load(path)
    lv = liveness.is_live(rec.get("pid"), rec.get("pid_cmdline_fingerprint"),
                          rec.get("pid_start_time_ticks"))
    if lv.live and not args.force:
        print("VERDICT: REAP REFUSED — THE HOLDER IS ALIVE")
        print("   %s" % describe(rec))
        return 1
    rec["state"] = registry.STATE_ABANDONED
    rec["reaped_utc"] = registry.now()
    rec["reap_reason"] = args.reason
    rec["reap_evidence_of_death"] = {"liveness_verdict": lv.reason, "evidence": lv.evidence,
                                     "degraded_measurement": lv.degraded}
    rec["reap_disclosure"] = ("A SESSION DIED HOLDING THIS LEASE. The record is retained, not "
                              "deleted, so that the death is visible to the next actor.")
    rec.pop("__path__", None)
    registry.rewrite(path, rec)
    print("VERDICT: REAPED — lease=%s state=ABANDONED (%s)" % (args.lease, lv.reason))
    return 0


def cmd_list(root: str, args: argparse.Namespace) -> int:
    recs = all_leases(root)
    live = live_leases(root)
    for r in recs:
        if args.all or r.get("state") == registry.STATE_CLAIMED:
            print("   %s" % describe(r))
            print("        write_scope: %s" % (r.get("write_scope") or []))
            print("        read_scope : %s" % (r.get("read_scope") or []))
    say_command("live_leases", len(live), "python3 -B tools/coordination/lease.py list")
    say_command("lease_records_total", len(recs),
                "ls governance/coordination/leases/*.lease.yaml | wc -l")
    print("VERDICT: LISTED")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("acquire")
    p.add_argument("--lease", required=True)
    p.add_argument("--seat", required=True)
    p.add_argument("--task", required=True)
    p.add_argument("--write-scope", action="append", required=True)
    p.add_argument("--read-scope", action="append", default=[])
    p.add_argument("--pid", default=None, help="the PID the lease covers (default: this process)")
    p.add_argument("--base", default=None)
    p.add_argument("--branch", default=None)
    p.add_argument("--worktree", default=None)

    p = sub.add_parser("check")
    p.add_argument("--task", required=True)
    p.add_argument("--write-scope", action="append", required=True)
    p.add_argument("--read-scope", action="append", default=[])

    p = sub.add_parser("release")
    p.add_argument("--lease", required=True)
    p.add_argument("--seat", required=True)

    p = sub.add_parser("reap")
    p.add_argument("--lease", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("list")
    p.add_argument("--all", action="store_true")

    args = ap.parse_args(argv)
    root = args.root or repo_root()

    with Limit("tools/coordination/lease.py", LIMITS, RESIDUE):
        tree_banner(root)
        try:
            return {"acquire": cmd_acquire, "check": cmd_check, "release": cmd_release,
                    "reap": cmd_reap, "list": cmd_list}[args.cmd](root, args)
        except (ValueError, RuntimeError, scope_mod.ScopeInvalid) as exc:
            print("VERDICT: REFUSED — %s" % exc)
            return 2


if __name__ == "__main__":
    sys.exit(main())
