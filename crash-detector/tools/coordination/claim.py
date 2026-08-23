#!/usr/bin/env python3
"""THE WORK-CLAIM REGISTRY — increment 12 ITEM 1, ``PO-DECISIONS-0021`` ruling 3(a).

The ruling: *"A task is atomically claimed before it is worked; a launch refuses to start on an
already-claimed task. Two seats can never take the same work."*

    claim.py claim   --task T --seat S --write-scope G [--read-scope G] [--dispatch D] [--block B]
    claim.py release --task T --seat S [--reason R]
    claim.py list    [--all]
    claim.py status  --task T
    claim.py reap    --task T --reason R          # EXPLICIT. NEVER a side effect of `claim`.

**THE REGISTRY IS A DIRECTORY, ONE FILE PER CLAIM, AND THE FILESYSTEM IS THE LOCK.** See
``registry.py`` for why a shared list file re-creates the exact contention this increment removes,
and for the measurement that ``O_EXCL`` is atomic on this filesystem.

**AND ``O_EXCL`` IS ONLY HALF OF THE RULING.** ``PO-DECISIONS-0021`` ruling 3 says *"no two live
seats share a TASK **or a WRITE SCOPE**"*. ``O_EXCL`` excludes on the FILENAME, and the filename is
the TASK ID; two seats with different task ids and identical write scopes take different filenames
and it never fires. Increment 12 checked the scope half with a directory read and took the claim
fifty lines later, and ``CD-ASR-WO2R3-06-F04`` raced that window: **193 of 200 rounds put two seats
on ONE write scope, both ``VERDICT: CLAIMED``, both ``rc=0``.** The scope check and the take now run
inside ONE :func:`registry.critical_section` — a mutex around the DECISION, released before this
command returns, so DISJOINT claims are still taken concurrently and still proceed in parallel.

WHAT ``claim`` REFUSES
----------------------
* the task is already claimed — ``FileExistsError`` from ``O_EXCL``, and the refusal NAMES the
  holder, its PID and its claim time;
* the declared ``write_scope`` reaches a shared record file and the seat is not the accountable
  seat (ITEM 2(d) prospective arm, imported not re-implemented);
* the declared ``write_scope`` overlaps the WRITE or READ scope of any LIVE claim
  (``CD-PL-F134``: a live reader's material must not move under it);
* a scope entry the algebra cannot parse, or a literal that names an existing DIRECTORY without
  ``/**`` — the second is a real trap, because ``tools/coordination`` and ``tools/coordination/**``
  mean different things and only one of them is what the seat meant.

**WHAT IT DOES NOT DO IS REAP.** A claim whose PID is dead is STALE, and ``claim`` refuses against
it exactly as if it were live. **REAPING SILENTLY IS THE BUG THAT MAKES THE WHOLE REGISTRY
WORTHLESS**: a wrapper hard-kill has happened on this project — an entire Assurance audit ceased to
exist — and if the next launch reaps the corpse without trace, nobody learns a seat died. ``reap``
is a separate command, it writes the reaping INTO the claim file with its reason and the evidence
of death, and it sets ``state: ABANDONED`` rather than deleting anything.

WHAT ``release`` REFUSES
------------------------
**A seat releasing another seat's claim.** This matters far more than it looks: releasing someone
else's claim is precisely how a launch script papers over a collision, and it turns a refusal into
a silent hand-off.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_no_shared_record_write as shared_rec  # noqa: E402
import liveness  # noqa: E402
import registry  # noqa: E402
import scope as scope_mod  # noqa: E402
from common import Limit, current_branch, repo_root, resolve_sha, say_command, tree_banner  # noqa: E402

LIMITS = [
    "DECIDES: mutual exclusion on a TASK ID, by O_EXCL create in a directory registry. Two "
    "processes racing the same task id: exactly one wins. MEASURED at 6400 concurrent attempts "
    "over 200 rounds, exactly 200 wins (governance/coordination/evidence/EV-ATOMICITY-MEASUREMENT.md). "
    "**O_EXCL EXCLUDES ON THE FILENAME, WHICH IS THE TASK ID. IT IS NOT AND NEVER WAS EXCLUSION ON "
    "A WRITE SCOPE** — that is the next limit, and increment 12 stated it without the distinction.",
    "DECIDES: refusal of a claim whose write_scope overlaps a live claim's write OR read scope, "
    "using tools/coordination/scope.py, which fails closed on forms it cannot decide. **AND IT "
    "DECIDES IT UNDER CONCURRENCY**: the check and the take run inside ONE registry-directory "
    "critical section (registry.critical_section, fcntl.flock), so the read that finds a colliding "
    "claim and the write that takes this one are a single atomic act. Increment 12 stated this "
    "limit FLATLY, with no concurrency qualifier, in an instrument whose entire purpose is "
    "concurrency — it was TRUE single-threaded and FALSE under load, and CD-ASR-WO2R3-06-F04 "
    "measured 193 double-takes in 200 raced rounds. MEASURED AGAIN AFTER THE FIX by the ninth "
    "Assurance seat's own harness at 200 rounds (governance/coordination/evidence/"
    "EV-SCOPE-RACE-MEASUREMENT.md) and by PLANT-COORD-06.",
    "DELIBERATELY DOES NOT SERIALISE WORK: the critical section is held across check-then-take "
    "ONLY, and is released before this command returns. Two seats taking DISJOINT scopes both "
    "succeed and proceed in parallel — an EQUAL requirement (PO-DECISIONS-0021 ruling 3, preserved "
    "by PO-DECISIONS-0022 ruling 1). PLANT-COORD-06 arm 3 measures it.",
    "DOES NOT DECIDE: a claim taken by a process that does not run this code. flock is ADVISORY. "
    "It binds every route through these instruments and NOTHING ELSE; a hand-written claim file "
    "defeats it exactly as it always defeated the registry.",
    "REFUSES rather than proceeds if the critical section cannot be entered within 30s. Proceeding "
    "unlocked would be F04 with a log line attached.",
    "DOES NOT DECIDE: whether two DIFFERENT task ids are the same work. `WO-2R3-INC-12` and "
    "`increment-12` are two tasks to this registry. Task identity is a naming discipline, and it is "
    "NOT PROVED TO BE CARRIED ANYWHERE.",
    "DOES NOT DECIDE: work done with no claim at all. Nothing in this repository forces a seat to "
    "claim before it writes; that binding is ITEM 4 and ITEM 4(ii) declares its own gap.",
    "DOES NOT DECIDE: atomicity on a network filesystem. The filesystem is re-measured on every "
    "run and a refused type aborts rather than proceeding on an assumption.",
    "DOES NOT DECIDE: a claim file edited by hand. The registry trusts its own records; a seat that "
    "rewrites another seat's claim file with an editor defeats it, and `git` is the only witness.",
]

RESIDUE = ("TASK-ID SYNONYMY (two names for one piece of work) is NOT PROVED TO BE CARRIED "
           "ANYWHERE. The scope-overlap refusal is a partial carrier — two seats naming one job "
           "differently will usually still collide on write_scope and be refused there — and that "
           "is a MEASURED behaviour (PLANT-COORD-02 arm 1), not a design intention. It is partial "
           "because two seats can do the same work in two different files.")


def claim_record(root: str, task: str) -> str:
    return registry.record_path(root, registry.CLAIMS_DIR, task, registry.CLAIM_SUFFIX)


def _validate_scope(root: str, entries: List[str], label: str) -> List[str]:
    pats = scope_mod.parse_scope(entries)
    problems = []
    for p in pats:
        if not p.recursive and not any(ch in "".join(p.segments) for ch in "*?[]{}"):
            candidate = os.path.join(root, *p.segments)
            if os.path.isdir(candidate):
                problems.append(
                    "%s entry %r names an EXISTING DIRECTORY but is written as a literal path. A "
                    "literal covers that path and nothing under it. Write %r if you mean the "
                    "subtree." % (label, p.raw, p.raw.rstrip("/") + "/**"))
        links = scope_mod.symlinked_components(root, p)
        if links:
            problems.append("%s entry %r traverses a symlink at %s; the algebra is textual and "
                            "cannot see through it — refusing rather than deciding wrongly"
                            % (label, p.raw, ", ".join(links)))
    if problems:
        raise ValueError("SCOPE_REFUSED:\n    " + "\n    ".join(problems))
    return [p.raw for p in pats]


def live_claims(root: str) -> List[Dict[str, Any]]:
    recs = registry.list_records(root, registry.CLAIMS_DIR, registry.CLAIM_SUFFIX)
    return [r for r in recs if r.get("state") == registry.STATE_CLAIMED]


def describe_holder(rec: Dict[str, Any]) -> str:
    live = liveness.is_live(rec.get("pid"), rec.get("pid_cmdline_fingerprint"),
                            rec.get("pid_start_time_ticks"))
    return ("held by seat=%s pid=%s host=%s claimed_utc=%s state=%s liveness=%s (%s)"
            % (rec.get("seat_actor_id"), rec.get("pid"), rec.get("hostname"),
               rec.get("claimed_utc"), rec.get("state"),
               "LIVE" if live.live else "DEAD/" + live.reason, live.evidence))


def cmd_claim(root: str, args: argparse.Namespace) -> int:
    registry.assert_atomic_or_refuse(os.path.join(root, registry.CLAIMS_DIR))

    write_scope = _validate_scope(root, args.write_scope, "write_scope")
    read_scope = _validate_scope(root, args.read_scope, "read_scope") if args.read_scope else []

    # ITEM 2(d) PROSPECTIVE ARM — imported, not re-implemented.
    bad = shared_rec.prospective_violation(root, write_scope, args.seat)
    if bad:
        print("VERDICT: CLAIM REFUSED")
        print(bad)
        return 1

    # ------------------------------------------------------------------------------------------
    # **THE PAYLOAD IS BUILT BEFORE THE CRITICAL SECTION IS ENTERED, DELIBERATELY.**
    # `resolve_sha` shells out to git twice. Holding the registry mutex across a subprocess would
    # turn a microsecond decision into a multi-millisecond one and make the section look like the
    # serialisation this increment must not ship. Nothing below the `with` runs a subprocess.
    # ------------------------------------------------------------------------------------------
    pid, fp, ticks = liveness.self_identity()
    payload = {
        "record_type": "WORK_CLAIM",
        "task_id": args.task,
        "seat_actor_id": args.seat,
        "pid": pid,
        "pid_cmdline_fingerprint": fp,
        "pid_start_time_ticks": ticks,
        "hostname": registry.hostname(),
        "claimed_utc": registry.now(),
        "base_sha": resolve_sha(args.base or "HEAD", cwd=root),
        "branch": args.branch or current_branch(root),
        "worktree": args.worktree or root,
        "write_scope": write_scope,
        "read_scope": read_scope,
        "build_log_id_block": args.block,
        "dispatch_id": args.dispatch,
        "state": registry.STATE_CLAIMED,
        "provenance": {
            "claimed_utc_command": "date -u +%FT%TZ",
            "base_sha_command": "git rev-parse %s && git cat-file -t <sha>" % (args.base or "HEAD"),
            "atomicity": "os.open(path, O_CREAT|O_EXCL|O_WRONLY) — FileExistsError is the refusal",
        },
    }

    path = claim_record(root, args.task)

    # ==========================================================================================
    # **CD-ASR-WO2R3-06-F04 — THE CHECK AND THE TAKE ARE ONE ATOMIC ACT, OR THEY ARE NOTHING.**
    #
    # Increment 12 read the live claims here and wrote the record 50 lines later, and 193 of 200
    # raced rounds put TWO SEATS ON ONE WRITE SCOPE, both printing `VERDICT: CLAIMED`, both rc=0.
    # `O_EXCL` did not fire and could not: it excludes on the FILENAME, which is the TASK ID, and
    # the two racers had different task ids by construction. **O_EXCL IS THE TASK CONJUNCT OF
    # `PO-DECISIONS-0021` RULING 3. THIS SECTION IS THE WRITE-SCOPE CONJUNCT.**
    #
    # WHAT IS INSIDE: a directory read, a pure-python scope decision, one `O_EXCL` create.
    # WHAT IS NOT: anything that blocks. NO subprocess, NO git, NO network. The payload above is
    # already built. **THE MUTEX IS AROUND THE DECISION, NEVER AROUND THE WORK** — the moment the
    # record is on disk the section is left, and two seats holding DISJOINT claims proceed in
    # parallel with no lock between them. A lease that serialises is a failed item, and so is a
    # registry that serialises.
    # ==========================================================================================
    with registry.critical_section(root, registry.CLAIMS_DIR):
        # ITEM 2(b), applied INSIDE the section: write-vs-write AND write-vs-READ against every
        # live claim. **Identity is not consulted here and never was** — claim.py has always
        # refused a same-seat overlap, and F08 was check_scope_disjoint.py disagreeing with it.
        for other in live_claims(root):
            if other.get("task_id") == args.task:
                continue
            other_write = other.get("write_scope") or []
            other_read = other.get("read_scope") or []
            ow, hits = scope_mod.overlaps(write_scope, other_write) if other_write else (False, [])
            if ow:
                print("VERDICT: CLAIM REFUSED — WRITE/WRITE SCOPE OVERLAP")
                print("   this seat : %s  task=%s" % (args.seat, args.task))
                print("   other seat: %s  task=%s  (%s)"
                      % (other.get("seat_actor_id"), other.get("task_id"), other.get("__path__")))
                for h in hits:
                    print("   %s" % h)
                print("   DECIDED INSIDE THE CHECK-THEN-TAKE SECTION (%s) — the read that found "
                      "this claim and the write that would have taken mine are ONE atomic act."
                      % registry.lock_path(root, registry.CLAIMS_DIR))
                return 1
            orr, hits = scope_mod.overlaps(write_scope, other_read) if other_read else (False, [])
            if orr:
                print("VERDICT: CLAIM REFUSED — WRITE/READ SCOPE OVERLAP (CD-PL-F134)")
                print("   this seat would WRITE what seat %s declared it would READ."
                      % other.get("seat_actor_id"))
                print("   other seat: %s  task=%s  (%s)"
                      % (other.get("seat_actor_id"), other.get("task_id"), other.get("__path__")))
                for h in hits:
                    print("   %s" % h)
                return 1

        try:
            registry.write_exclusive(path, payload)
        except FileExistsError:
            existing = registry.load(path)
            print("VERDICT: CLAIM REFUSED — TASK ALREADY CLAIMED")
            print("   task_id : %s" % args.task)
            print("   record  : %s" % os.path.relpath(path, root))
            print("   %s" % describe_holder(existing))
            print("   requested by seat=%s pid=%d" % (args.seat, pid))
            print("   NOTE: a DEAD holder is still a refusal here. Run `claim.py reap --task %s "
                  "--reason ...` explicitly; `claim` never reaps." % args.task)
            return 1

    print("VERDICT: CLAIMED")
    print("   task_id  : %s" % args.task)
    print("   seat     : %s" % args.seat)
    print("   record   : %s" % os.path.relpath(path, root))
    say_command("live_claims_after", len(live_claims(root)),
                "python3 -B tools/coordination/claim.py list")
    return 0


def cmd_release(root: str, args: argparse.Namespace) -> int:
    path = claim_record(root, args.task)
    if not os.path.exists(path):
        print("VERDICT: RELEASE REFUSED — no claim record for task %r" % args.task)
        return 1
    rec = registry.load(path)
    if rec.get("seat_actor_id") != args.seat:
        print("VERDICT: RELEASE REFUSED — NOT THE HOLDING SEAT")
        print("   task_id      : %s" % args.task)
        print("   holder       : %s" % rec.get("seat_actor_id"))
        print("   requested by : %s" % args.seat)
        print("   Releasing another seat's claim is how a launch script papers over a collision. "
              "Refused.")
        return 1
    if rec.get("state") != registry.STATE_CLAIMED:
        print("VERDICT: RELEASE REFUSED — claim state is %r, not %s"
              % (rec.get("state"), registry.STATE_CLAIMED))
        return 1
    rec["state"] = registry.STATE_RELEASED
    rec["released_utc"] = registry.now()
    rec["released_by_seat"] = args.seat
    rec["release_reason"] = args.reason or "completed"
    rec.pop("__path__", None)
    registry.rewrite(path, rec)
    print("VERDICT: RELEASED — task=%s seat=%s" % (args.task, args.seat))
    return 0


def cmd_reap(root: str, args: argparse.Namespace) -> int:
    """EXPLICIT reaping. It writes WHY and the EVIDENCE OF DEATH into the record."""
    path = claim_record(root, args.task)
    if not os.path.exists(path):
        print("VERDICT: REAP REFUSED — no claim record for task %r" % args.task)
        return 1
    rec = registry.load(path)
    if rec.get("state") != registry.STATE_CLAIMED:
        print("VERDICT: REAP REFUSED — claim state is %r, nothing to reap" % rec.get("state"))
        return 1
    live = liveness.is_live(rec.get("pid"), rec.get("pid_cmdline_fingerprint"),
                            rec.get("pid_start_time_ticks"))
    if live.live and not args.force:
        print("VERDICT: REAP REFUSED — THE HOLDER IS ALIVE")
        print("   %s" % describe_holder(rec))
        print("   CD-PL-F143 on this project is a seat DECLARED DEAD WHILE IT WAS ALIVE AND READING. "
              "Refusing.")
        return 1
    rec["state"] = registry.STATE_ABANDONED
    rec["reaped_utc"] = registry.now()
    rec["reaped_by"] = args.by or "unknown"
    rec["reap_reason"] = args.reason
    rec["reap_evidence_of_death"] = {
        "liveness_verdict": live.reason,
        "evidence": live.evidence,
        "degraded_measurement": live.degraded,
        "command": "python3 -B tools/coordination/claim.py status --task %s" % args.task,
    }
    rec["reap_disclosure"] = (
        "THIS CLAIM WAS NOT COMPLETED. It was abandoned by an explicit reap. A seat died holding it "
        "and the work it named is UNDONE unless someone says otherwise. This record is retained, "
        "not deleted, so that the death is visible.")
    if args.force and live.live:
        rec["reap_forced_over_a_live_holder"] = True
    rec.pop("__path__", None)
    registry.rewrite(path, rec)
    print("VERDICT: REAPED — task=%s state=ABANDONED" % args.task)
    print("   evidence: %s / %s" % (live.reason, live.evidence))
    return 0


def cmd_list(root: str, args: argparse.Namespace) -> int:
    recs = registry.list_records(root, registry.CLAIMS_DIR, registry.CLAIM_SUFFIX)
    shown = recs if args.all else [r for r in recs if r.get("state") == registry.STATE_CLAIMED]
    for r in shown:
        print("   %-38s %s" % (r.get("task_id"), describe_holder(r)))
        print("        write_scope: %s" % (r.get("write_scope") or []))
        print("        read_scope : %s" % (r.get("read_scope") or []))
    say_command("claims_shown", len(shown),
                "python3 -B tools/coordination/claim.py list%s" % (" --all" if args.all else ""))
    say_command("claims_total", len(recs), "ls governance/coordination/claims/*.claim.yaml | wc -l")
    print("VERDICT: LISTED")
    return 0


def cmd_status(root: str, args: argparse.Namespace) -> int:
    path = claim_record(root, args.task)
    if not os.path.exists(path):
        print("VERDICT: UNCLAIMED — %s" % args.task)
        return 0
    rec = registry.load(path)
    print("VERDICT: %s" % rec.get("state"))
    print("   %s" % describe_holder(rec))
    for k in ("write_scope", "read_scope", "base_sha", "branch", "worktree",
              "build_log_id_block", "dispatch_id"):
        print("   %-20s %s" % (k, rec.get(k)))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Work-claim registry (PO-DECISIONS-0021 ruling 3(a)).")
    ap.add_argument("--root", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("claim")
    p.add_argument("--task", required=True)
    p.add_argument("--seat", required=True)
    p.add_argument("--write-scope", action="append", required=True)
    p.add_argument("--read-scope", action="append", default=[])
    p.add_argument("--dispatch", default=None)
    p.add_argument("--block", default=None)
    p.add_argument("--base", default=None)
    p.add_argument("--branch", default=None)
    p.add_argument("--worktree", default=None)

    p = sub.add_parser("release")
    p.add_argument("--task", required=True)
    p.add_argument("--seat", required=True)
    p.add_argument("--reason", default=None)

    p = sub.add_parser("reap")
    p.add_argument("--task", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--by", default=None)
    p.add_argument("--force", action="store_true",
                   help="reap a holder measured ALIVE. Recorded in the file as a forced reap.")

    p = sub.add_parser("list")
    p.add_argument("--all", action="store_true")

    p = sub.add_parser("status")
    p.add_argument("--task", required=True)

    args = ap.parse_args(argv)
    root = args.root or repo_root()

    with Limit("tools/coordination/claim.py", LIMITS, RESIDUE):
        tree_banner(root)
        print("filesystem = %s   (command: stat -f -c %%T %s)"
              % (registry.fs_type(root), registry.CLAIMS_DIR))
        try:
            handler = {"claim": cmd_claim, "release": cmd_release, "reap": cmd_reap,
                       "list": cmd_list, "status": cmd_status}[args.cmd]
            return handler(root, args)
        except (ValueError, RuntimeError, scope_mod.ScopeInvalid) as exc:
            print("VERDICT: REFUSED — %s" % exc)
            return 2


if __name__ == "__main__":
    sys.exit(main())
