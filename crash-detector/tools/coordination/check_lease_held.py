#!/usr/bin/env python3
"""THE HAND BINDING — increment 12 ITEM 4(ii), ``PO-DECISIONS-0021`` ruling 3(d).

    check_lease_held.py --staged            # is the currently STAGED write covered by a lease?
    check_lease_held.py --range A..B        # was every governed write in this range covered?
    check_lease_held.py --identity NAME     # the committing identity to test (default: git config)

The ruling requires the launch lease to bind *"the driver AND **the PO's own hand**"*. This file is
the hand half: a standalone, invocable check that a governed write is covered by a live lease held
by the committing identity.

======================================================================================================
THE ``CD-RULE-006`` DECLARATION, IN ITS REQUIRED WORDS. READ IT BEFORE CREDITING THIS FILE.
======================================================================================================

**THIS CHECK IS NOT PROVED TO BE CARRIED ANYWHERE.**

Not "carried by the pre-commit hook". Not "carried by the Project Lead's boundary discipline". Not
"carried by the dispatch". **NOWHERE.** Nothing in this repository invokes it automatically. It runs
when a human or a seat types its name, and at no other time.

THE MEASUREMENT BEHIND THAT SENTENCE, so it is a finding and not a modesty:

    git config core.hooksPath          ->  pbg/tools/hooks
    cat pbg/tools/hooks/pre-commit     ->  STAGED=$(git diff --cached --name-only ... |
                                                    grep '^governance/authority/' || true)
                                           [ -n "$STAGED" ] || exit 0

The one automatic pre-write carrier in this repository greps ``^governance/authority/`` and waves
everything else through. **IT LIVES INSIDE ``pbg/``, WHICH IS PINNED AND READ-ONLY TO EVERY SEAT ON
THIS PROJECT (``PBG-FWK-013``).** Extending it to call this check would be editing the framework to
make a control pass, which is a bypass and not a fix, and the Project Lead would reject it. **THIS
SEAT DID NOT TRY, AND THE DISPATCH TOLD IT ABOUT THE TRAP IN ADVANCE.**

That gap is ``Q11``/``Q12``. It needs a bounded framework dispatch against PBG itself, from the
human. **IT IS NOT THIS SEAT'S TO CLOSE AND THIS FILE DOES NOT PRETEND OTHERWISE.**

**SO DELIVERABLE 3(d) LANDS HALF-CARRIED BY CONSTRUCTION.** The driver half
(``tools/coordination/launch.sh``) is real machinery that refuses to ``exec``; it binds every launch
that goes through it and nothing else, and the operator's wrapper does not go through it today. The
hand half is this file, and it is **NOT PROVED TO BE CARRIED ANYWHERE.**

**DO NOT DRESS AN UNINVOKED CHECK AS A BINDING.** An uninvoked check that is *described* as a
binding is worse than no check, because it spends the reader's attention on a door that is not shut.
That is the ``CD-PL-F132`` shape exactly — a discipline that lives in a seat's attention and gets
called structural.

=====================================================================================================
``--range`` USED TO BE FLIPPABLE FROM RED TO GREEN IN ONE COMMAND, BY THE PARTY IT GRADES.
**``CD-ASR-WO2R3-06-F09``.**
=====================================================================================================

The ninth Assurance seat measured it::

    check_lease_held.py --range HEAD~2..HEAD --identity PROJECT_LEAD_SEAT_01
      -> VERDICT: REFUSED — 6 governed path(s) not covered by a live lease          rc=1

    lease.py acquire --lease RETRO --seat PROJECT_LEAD_SEAT_01 --task ANY \
             --write-scope 'governance/**' --write-scope 'tools/**' --pid 1
      -> VERDICT: LEASE ACQUIRED                                                    rc=0

    check_lease_held.py --range HEAD~2..HEAD --identity PROJECT_LEAD_SEAT_01
      -> VERDICT: ADMITTED — every governed path is covered by a live lease         rc=0

**SAME COMMITS. SAME HISTORY. NOTHING REWRITTEN. RED TO GREEN IN ONE COMMAND.** Two separable root
causes, and both are addressed:

**(a) ``--range`` GRADED HISTORICAL WRITES AGAINST LEASES LIVE *NOW*.** The contract this file
delivers is named ``CD-CT-009-LEASE-HELD-AT-WRITE`` and the old ``--range`` **did not measure
time-of-write at all** — it asked "is there a lease live at this instant", which a lease acquired
one second ago satisfies. It now grades **each commit against the lease's own RECORDED LIVE
INTERVAL** — ``acquired_utc`` to ``released_utc``/``reaped_utc`` — and compares it against that
commit's committer timestamp. A lease acquired *after* a commit does not cover it, so the retro
acquisition no longer moves the verdict. **AND ``--range`` NO LONGER CONSULTS PID LIVENESS AT ALL**,
which was itself wrong in the other direction: the seat that made a historical write is normally
dead by the time anyone audits it, and requiring its process to still be running would have refused
every honest history.

**(b) ``--pid`` WAS UNAUTHENTICATED AND ``--pid 1`` IS ``init``, WHICH IS ALWAYS ALIVE.** That half
lives in ``lease.py``, which now DERIVES a session bound rather than trusting the number. **It is a
BOUND AND NOT AN AUTHENTICATION, and the residue is returned as ``CONTROL_NOT_SATISFIABLE`` rather
than papered over** — see ``lease._authenticate_pid``.

**WHAT (a) DOES NOT CLOSE, AND IT MUST BE READ BEFORE THIS MODE IS CREDITED:** *both* inputs are
SELF-REPORTED. ``GIT_COMMITTER_DATE`` is settable by the committer, and a lease record is a YAML
file the holder can edit. **THIS MODE DEFEATS THE ONE-COMMAND RETRO FLIP. IT DOES NOT WITHSTAND A
PARTY WILLING TO FORGE A TIMESTAMP, AND NOTHING IN THIS REPOSITORY DOES.** That residue is declared,
not carried.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lease as lease_mod  # noqa: E402
import registry  # noqa: E402
import scope as scope_mod  # noqa: E402
from common import Limit, git, repo_root, say_command, tree_banner  # noqa: E402

GOVERNED_PREFIXES = ("governance/", "tools/", "src/", "BLUEPRINT.md", "PID.md")

LIMITS = [
    "DECIDES (--staged): whether every governed path in the STAGED set is inside the write scope of "
    "a lease held by the named identity and LIVE NOW. The write is happening now, so now is the "
    "right instant to ask about.",
    "DECIDES (--range): whether every governed path of EVERY COMMIT in the range was inside the "
    "write scope of a lease held by the named identity **AND LIVE AT THE TIME OF THAT COMMIT** — "
    "the lease's own recorded interval (acquired_utc .. released_utc/reaped_utc) against that "
    "commit's committer timestamp. **INCREMENT 12 GRADED HISTORICAL WRITES AGAINST LEASES LIVE NOW, "
    "SO THE PARTY BEING GRADED COULD FLIP IT RED-TO-GREEN IN ONE COMMAND (CD-ASR-WO2R3-06-F09) — "
    "the contract is named CD-CT-009-LEASE-HELD-AT-WRITE and the mode did not measure time of "
    "write at all.** A lease acquired after a commit no longer covers that commit.",
    "DOES NOT CONSULT PID LIVENESS IN --range, DELIBERATELY. The seat that made a historical write "
    "is normally dead by the time anyone audits it; requiring its process to still be running "
    "would refuse every honest history. The record's declared interval is what is read.",
    "*** DOES NOT DECIDE WHETHER EITHER TIMESTAMP IS TRUE. BOTH ARE SELF-REPORTED: "
    "GIT_COMMITTER_DATE is settable by the committer and a lease record is a YAML file its holder "
    "can edit. THIS MODE DEFEATS THE ONE-COMMAND RETRO FLIP; IT DOES NOT WITHSTAND A PARTY WILLING "
    "TO FORGE A TIMESTAMP, AND NOTHING IN THIS REPOSITORY DOES. *** NOT PROVED TO BE CARRIED "
    "ANYWHERE (CD-RULE-006).",
    "BOTH INTERVAL EDGES ARE STRICT. CD-RULE-005's one timestamp source (`date -u +%FT%TZ`) is "
    "SECOND-GRANULAR, so a lease acquired in the SAME SECOND as a commit cannot be distinguished "
    "from one acquired retroactively — MEASURED: with an inclusive edge the retro-flip still "
    "captured 1 of 11 governed writes. The ambiguous instant is decided AGAINST the party being "
    "graded. **THE COST IS DECLARED: an honest launch that commits inside the same second as its "
    "own lease acquisition is REFUSED**, and the refusal says so in those words.",
    "REFUSES TO ANSWER rather than answering wrongly: a lease record with an unreadable or absent "
    "acquired_utc is reported UNUSABLE and counted as covering NOTHING, and an unparseable commit "
    "timestamp aborts the run with PRECONDITION_NOT_MET (rc=2).",
    "DOES NOT DECIDE: whether the `--pid` a lease names is the pid it claims. That is lease.py's "
    "half of F09; it DERIVES a session bound (os.getsid) which refuses `--pid 1`, and it declares "
    "full pid authentication CONTROL_NOT_SATISFIABLE on this platform.",
    "*** IT IS NOT INVOKED BY ANYTHING. `git config core.hooksPath` is `pbg/tools/hooks`; that "
    "hook greps '^governance/authority/' and nothing else; `pbg/` is pinned read-only "
    "(PBG-FWK-013). NOTHING AUTOMATICALLY RUNS THIS FILE. ***",
    "DOES NOT DECIDE: a write made with `git commit --no-verify`, or with plumbing, or outside git.",
    "DOES NOT DECIDE: whether the lease SHOULD have been granted. It reads the lease, it does not "
    "grade it.",
    "'GOVERNED' here means a path under governance/, tools/, src/, or BLUEPRINT.md / PID.md. That "
    "enumeration is a CHOICE and it is printed on every run so a reader can disagree with it.",
]

RESIDUE = ("AUTOMATIC INVOCATION IS **NOT PROVED TO BE CARRIED ANYWHERE**. Those are the required "
           "words of CD-RULE-006 and they are the honest answer. The layer that would carry it "
           "(`pbg/tools/hooks/pre-commit`) EXISTS, RUNS ON EVERY COMMIT, AND IS OUT OF REACH OF "
           "EVERY SEAT THIS PROJECT DISPATCHES. Q11 / Q12.")


def governed(path: str) -> bool:
    return any(path == p or path.startswith(p) for p in GOVERNED_PREFIXES)


def staged_paths(root: str) -> List[str]:
    out = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", cwd=root)
    return sorted({p for p in out.split("\n") if p.strip()})


def covering_lease(root: str, identity: str, path: str) -> Tuple[bool, str]:
    """``--staged`` only: the write is happening NOW, so NOW is the right instant to ask about."""
    for lease in lease_mod.live_leases(root):
        if lease.get("seat_actor_id") != identity:
            continue
        ws = list(lease.get("write_scope") or [])
        if not ws:
            continue
        ov, hits = scope_mod.overlaps([path], ws)
        if ov and not any("UNDECIDABLE" in h for h in hits):
            return True, "covered by lease %r (%s)" % (lease.get("lease_id"), hits[0])
    return False, "no LIVE lease held by %r covers it" % identity


# ------------------------------------------------------------------------------------------------
# CD-ASR-WO2R3-06-F09(a) — TIME-OF-WRITE GRADING FOR `--range`.
# The contract is named CD-CT-009-LEASE-HELD-AT-WRITE. `AT WRITE` is now a measured quantity.
# ------------------------------------------------------------------------------------------------

def parse_utc(stamp: Optional[str], what: str) -> datetime:
    """Parse a governed timestamp. **RAISES rather than guessing** — CD-RULE-003, fail closed."""
    if not stamp:
        raise ValueError("%s is missing" % what)
    s = str(stamp).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        raise ValueError("%s = %r is not an ISO-8601 timestamp this instrument can read" % (what, stamp))
    if dt.tzinfo is None:
        raise ValueError("%s = %r carries no timezone; refusing to assume one" % (what, stamp))
    return dt.astimezone(timezone.utc)


def commits_in_range(root: str, rng: str) -> List[str]:
    out = git("rev-list", rng, cwd=root)
    return [c for c in out.split("\n") if c.strip()]


def commit_facts(root: str, sha: str) -> Tuple[datetime, List[str], List[str], str]:
    """Return ``(committed_at, parents, changed_paths, method)`` for one commit.

    **THE PATH ENUMERATION IS DELIBERATELY NOT ``git show --pretty=format: --name-only``.** That
    idiom PRINTS NOTHING FOR A MERGE COMMIT — measured on this repository at `6c58725`, which
    produced zero lines from `git show` and 40+ from the idiom used here. `CD-ASR-WO2R3-06-F12`
    raises exactly that defect against two SIBLING instruments (`check_no_shared_record_write.py`
    and `check_build_log_pointer_atomic.py`), where it makes a refusal STRUCTURALLY UNREACHABLE on
    any merge. **F12 IS OUT OF SCOPE FOR THIS INCREMENT AND IS NOT FIXED HERE. IT IS NOT REPRODUCED
    HERE EITHER** — importing a known blind spot into a newly written mode would be building the
    finding a second time on purpose.
    """
    out = git("show", "-s", "--format=%cI%n%P", sha, cwd=root).split("\n")
    when = parse_utc(out[0].strip(), "commit %s committer date (git show -s --format=%%cI)" % sha[:8])
    parents = out[1].split() if len(out) > 1 else []
    method = "git diff-tree -r -m --no-commit-id --name-only %s" % sha
    paths = git("diff-tree", "-r", "-m", "--no-commit-id", "--name-only", sha, cwd=root)
    return when, parents, sorted({p for p in paths.split("\n") if p.strip()}), method


def lease_interval(rec: Dict[str, Any]) -> Tuple[Optional[datetime], Optional[datetime], Optional[str]]:
    """``(start, end, problem)``. ``end`` of ``None`` means the record says it is still open."""
    try:
        start = parse_utc(rec.get("acquired_utc"), "acquired_utc")
    except ValueError as exc:
        return None, None, str(exc)
    end = None
    for key in ("released_utc", "reaped_utc"):
        if rec.get(key):
            try:
                cand = parse_utc(rec.get(key), key)
            except ValueError as exc:
                return start, None, str(exc)
            if end is None or cand < end:
                end = cand
    return start, end, None


def covering_lease_at(root: str, identity: str, path: str, when: datetime
                      ) -> Tuple[bool, str, List[str]]:
    """Was a lease held by ``identity`` covering ``path`` **LIVE AT** ``when``?

    **PID LIVENESS IS NOT CONSULTED.** The seat that made a historical write is normally dead by the
    time anyone audits it; grading a past write on whether a process is running today answers a
    different question and answers it wrongly in both directions. What is read is the record's own
    declared interval.
    """
    notes: List[str] = []
    for lease in lease_mod.all_leases(root):
        if lease.get("seat_actor_id") != identity:
            continue
        ws = list(lease.get("write_scope") or [])
        if not ws:
            continue
        start, end, problem = lease_interval(lease)
        if problem:
            notes.append("lease %r UNUSABLE FOR TIME-OF-WRITE GRADING: %s — it is NOT counted as "
                         "covering anything, because a lease with no readable interval cannot say "
                         "when it was live" % (lease.get("lease_id"), problem))
            continue
        ov, hits = scope_mod.overlaps([path], ws)
        if not ov or any("UNDECIDABLE" in h for h in hits):
            continue
        # ------------------------------------------------------------------------------------
        # **BOTH EDGES ARE STRICT, AND THAT IS A DELIBERATE FAIL-CLOSED CHOICE, NOT AN OFF-BY-ONE.**
        #
        # `CD-RULE-005` mandates ONE timestamp source on this project — `date -u +%FT%TZ` — and it
        # is SECOND-GRANULAR. So a lease acquired in the SAME SECOND as a commit is a pair of
        # timestamps that CANNOT distinguish "acquired, then wrote" from "wrote, then acquired
        # retroactively". **THE SECOND OF THOSE IS EXACTLY `CD-ASR-WO2R3-06-F09`**, and it was
        # MEASURED here: with an inclusive edge, the retro-flip attack still captured 1 of 11
        # governed writes — the one committed in the same second as the retro acquisition.
        #
        # An ambiguous instant is DECIDED AGAINST THE PARTY BEING GRADED (`CD-RULE-003`: derive or
        # fail closed). THE COST IS DECLARED: an honest launch that commits inside the same second
        # as its own lease acquisition is REFUSED, and the refusal says exactly why below.
        # ------------------------------------------------------------------------------------
        if when <= start:
            notes.append("lease %r covers the SCOPE but NOT THE TIME: the write is at %s and the "
                         "lease was acquired at %s — **A LEASE ACQUIRED AFTER (OR IN THE SAME "
                         "SECOND AS) A WRITE DOES NOT COVER THAT WRITE (CD-ASR-WO2R3-06-F09).** "
                         "The edge is STRICT because CD-RULE-005's timestamp source is "
                         "second-granular and an ambiguous instant is decided against the party "
                         "being graded."
                         % (lease.get("lease_id"), when.isoformat(), start.isoformat()))
            continue
        if end is not None and when >= end:
            notes.append("lease %r covers the SCOPE but NOT THE TIME: the write is at %s and the "
                         "lease ended at %s (edge STRICT, same reason)"
                         % (lease.get("lease_id"), when.isoformat(), end.isoformat()))
            continue
        return True, ("covered by lease %r live [%s .. %s] at write time %s (%s)"
                      % (lease.get("lease_id"), start.isoformat(),
                         end.isoformat() if end else "still open", when.isoformat(), hits[0])), notes
    return False, ("no lease held by %r was LIVE AT %s with a write scope covering it"
                   % (identity, when.isoformat())), notes


def check_range(root: str, rng: str, identity: str) -> Tuple[int, int, int, List[Tuple[str, str, str]]]:
    """Grade every governed path of every commit in ``rng`` at ITS OWN commit time."""
    commits = commits_in_range(root, rng)
    total_paths = 0
    governed_paths = 0
    uncovered: List[Tuple[str, str, str]] = []
    for sha in commits:
        when, parents, paths, method = commit_facts(root, sha)
        gov = [p for p in paths if governed(p)]
        total_paths += len(paths)
        governed_paths += len(gov)
        print("   commit %s  committed_utc=%s  parents=%d%s  paths=%d governed=%d"
              % (sha[:12], when.isoformat(), len(parents),
                 "  *** MERGE COMMIT — paths enumerated with -m, NOT with `git show --pretty=format:"
                 " --name-only`, which prints NOTHING here (see commit_facts) ***"
                 if len(parents) > 1 else "", len(paths), len(gov)))
        print("        produced by: %s" % method)
        for p in gov:
            ok, why, notes = covering_lease_at(root, identity, p, when)
            for n in notes:
                print("        note      %s" % n)
            if ok:
                print("        covered   %s — %s" % (p, why))
            else:
                print("        UNCOVERED %s — %s" % (p, why))
                uncovered.append((sha, p, why))
    return len(commits), total_paths, governed_paths, uncovered


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None)
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--range", dest="rng", default=None)
    ap.add_argument("--identity", default=None,
                    help="the committing identity (default: GIT_AUTHOR_NAME, else git config user.name)")
    args = ap.parse_args(argv)
    root = args.root or repo_root()

    identity = args.identity or os.environ.get("GIT_AUTHOR_NAME") or \
        git("config", "user.name", cwd=root, check=False).strip() or "UNKNOWN"

    with Limit("tools/coordination/check_lease_held.py", LIMITS, RESIDUE):
        tree_banner(root)
        print("*** CD-RULE-006: THIS CHECK IS **NOT PROVED TO BE CARRIED ANYWHERE**. Nothing in this")
        print("*** repository invokes it automatically. core.hooksPath = %s"
              % git("config", "core.hooksPath", cwd=root, check=False).strip())
        print("*** and that hook greps '^governance/authority/' only. pbg/ is read-only (PBG-FWK-013).")
        print("governed_prefixes = %s   (this enumeration is a CHOICE — disagree with it out loud)"
              % (GOVERNED_PREFIXES,))
        print("identity = %r" % identity)

        if not args.staged and not args.rng:
            print("VERDICT: NOTHING CHECKED — pass --staged or --range")
            return 2

        if args.rng:
            # ------------------------------------------------------------------------------
            # TIME-OF-WRITE MODE. CD-ASR-WO2R3-06-F09(a).
            # ------------------------------------------------------------------------------
            print("MODE = --range, GRADED AT TIME OF WRITE. Each commit is graded against the")
            print("       RECORDED LIVE INTERVAL of each lease (acquired_utc .. released/reaped),")
            print("       against THAT COMMIT'S committer timestamp. A lease acquired after a")
            print("       commit does not cover that commit. PID liveness is NOT consulted here.")
            print("       *** BOTH INPUTS ARE SELF-REPORTED: GIT_COMMITTER_DATE is settable and a")
            print("       *** lease record is editable. This defeats the ONE-COMMAND RETRO FLIP.")
            print("       *** IT DOES NOT WITHSTAND A FORGED TIMESTAMP AND DOES NOT CLAIM TO.")
            for rec in lease_mod.all_leases(root):
                start, end, problem = lease_interval(rec)
                print("   lease %-24s seat=%-24s interval=[%s .. %s] state=%s%s"
                      % (rec.get("lease_id"), rec.get("seat_actor_id"),
                         start.isoformat() if start else "UNREADABLE",
                         end.isoformat() if end else ("still open" if start else "UNREADABLE"),
                         rec.get("state"), "  UNUSABLE: %s" % problem if problem else ""))
            try:
                ncommits, npaths, ngov, uncovered = check_range(root, args.rng, identity)
            except (ValueError, RuntimeError) as exc:
                print("VERDICT: PRECONDITION_NOT_MET — %s" % exc)
                print("   THE MODE REFUSES TO ANSWER RATHER THAN ANSWERING WRONGLY (CD-RULE-003).")
                return 2
            say_command("commits_in_range", ncommits, "git rev-list %s" % args.rng)
            say_command("paths_in_range", npaths,
                        "git diff-tree -r -m --no-commit-id --name-only <each commit>")
            say_command("governed_paths", ngov, "(filtered by governed_prefixes above)")
            say_command("uncovered_governed_writes", len(uncovered),
                        "python3 -B tools/coordination/check_lease_held.py --range %s" % args.rng)
            say_command("lease_records_total", len(lease_mod.all_leases(root)),
                        "python3 -B tools/coordination/lease.py list --all")
            if uncovered:
                print("VERDICT: REFUSED — %d governed write(s) in %s were NOT covered by a lease "
                      "held by %r AND LIVE AT THE TIME OF THAT WRITE"
                      % (len(uncovered), args.rng, identity))
                return 1
            print("VERDICT: ADMITTED — every governed write in %s was covered by a lease held by "
                  "%r and LIVE AT THE TIME OF THAT WRITE" % (args.rng, identity))
            return 0

        # ----------------------------------------------------------------------------------
        # --staged: the write is happening NOW, so NOW is the right instant to ask about.
        # ----------------------------------------------------------------------------------
        paths = staged_paths(root)
        gov = [p for p in paths if governed(p)]
        uncovered = []
        for p in gov:
            ok, why = covering_lease(root, identity, p)
            if not ok:
                uncovered.append((p, why))
                print("   UNCOVERED %s — %s" % (p, why))
            else:
                print("   covered   %s — %s" % (p, why))

        say_command("paths_in_write", len(paths),
                    "git diff --cached --name-only --diff-filter=ACMR")
        say_command("governed_paths", len(gov), "(filtered by governed_prefixes above)")
        say_command("uncovered_governed_paths", len(uncovered),
                    "python3 -B tools/coordination/check_lease_held.py --staged")
        say_command("live_leases", len(lease_mod.live_leases(root)),
                    "python3 -B tools/coordination/lease.py list")

        if uncovered:
            print("VERDICT: REFUSED — %d governed path(s) not covered by a live lease held by %r"
                  % (len(uncovered), identity))
            return 1
        print("VERDICT: ADMITTED — every governed path is covered by a live lease held by %r" % identity)
        return 0


if __name__ == "__main__":
    sys.exit(main())
