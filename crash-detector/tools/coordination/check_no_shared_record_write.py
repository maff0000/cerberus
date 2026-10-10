#!/usr/bin/env python3
"""NO SHARED RECORD WRITE — increment 12 ITEM 2(d), ``PO-DECISIONS-0021`` ruling 3(b).

The ruling: *"its OWN record files ... no shared ACTIVE_WORK.yaml edit, no shared sequence.
Parallel writers never touch the same bytes."*

**TWO DIRECTIONS. BOTH REQUIRED. THE SECOND IS THE ONE THAT MAKES IT A CONTROL.**

* **PROSPECTIVE** (``--prospective``) — refuse a CLAIM whose declared ``write_scope`` reaches a
  shared record file when the claiming seat is not the accountable seat. Called by ``claim.py``
  before the claim is taken, so a seat cannot even declare the intention.
* **RETROSPECTIVE** (``--range A..B``) — over a commit range, refuse when a commit that TOUCHES a
  shared record file carries a non-accountable seat's git author identity. Seat identity comes from
  the git author (``CD-RULE-002``).

**PROSPECTIVE-ONLY IS A PROMISE. THE RETROSPECTIVE ARM IS WHAT MAKES IT A CONTROL** — it reads what
actually happened rather than what a seat said it would do, and it does not depend on the seat
having run anything.

THE LIMIT, AND IT IS NOT SMALL — SEE ``governance/coordination/ACCOUNTABLE-SEAT.yaml``
--------------------------------------------------------------------------------------
``CD-RULE-002`` gives one git identity to the Project Lead ROLE, not one per SESSION. **This check
catches a NON-ACCOUNTABLE seat writing the shared file. IT CANNOT DISTINGUISH TWO CONCURRENT
ACCOUNTABLE SESSIONS FROM ONE**, which the second meta-assurance seat measured (§7.2) as the true
root cause of the day's breaches. That residue is declared here, on every run, and is NOT PROVED TO
BE CARRIED ANYWHERE by this increment.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import registry  # noqa: E402
import scope as scope_mod  # noqa: E402
from common import Limit, git, repo_root, say_command, tree_banner  # noqa: E402

LIMITS = [
    "DECIDES: whether a declared write_scope REACHES a shared record file, using the scope algebra "
    "in tools/coordination/scope.py — which fails closed on the forms it does not decide.",
    "DECIDES: whether a commit in a given range TOUCHES a shared record file while carrying a git "
    "author name that is not the accountable seat's.",
    "DOES NOT DECIDE: two concurrent sessions of the SAME accountable seat. CD-RULE-002 gives one "
    "identity to the ROLE, not one per session, so two live Project Leads are indistinguishable "
    "from one in `git log`. This is VERDICT-META-ASSURANCE-01-SECOND-SEAT.md §7.2.",
    "DOES NOT DECIDE: a write made and then reverted inside one commit, or a write made with "
    "`git commit --no-verify` in some future hook world — this instrument reads history, so it sees "
    "what landed and nothing about how.",
    "DOES NOT DECIDE: the accountable seat writing a shared record file it should not have. It "
    "guards WHO, not WHETHER.",
]

RESIDUE = ("two concurrent sessions of the accountable seat is NOT PROVED TO BE CARRIED ANYWHERE. "
           "The nearest carrier is the ITEM 4 launch lease, which refuses the second SESSION rather "
           "than the second COMMIT — and only where the lease is actually acquired, which ITEM 4(ii) "
           "declares is nowhere automatic.")


def prospective_violation(root: str, write_scope: List[str], seat: str) -> Optional[str]:
    """Return a refusal string, or ``None``. Used by ``claim.py`` before the claim is taken."""
    acc = registry.accountable_seat(root)
    if seat == acc["accountable_seat"]:
        return None
    shared = list(acc["shared_record_files"])
    ov, hits = scope_mod.overlaps(write_scope, shared)
    if not ov:
        return None
    return ("SHARED_RECORD_WRITE_REFUSED: seat %r is not the accountable seat (%r) and its declared "
            "write_scope reaches a shared record file.\n    %s"
            % (seat, acc["accountable_seat"], "\n    ".join(hits)))


def retrospective(root: str, rng: str) -> Tuple[int, int, List[str], str]:
    """Return ``(commits_examined, violations, lines)`` over ``rng`` (e.g. ``main~20..main``)."""
    acc = registry.accountable_seat(root)
    accountable = acc["accountable_seat"]
    shared = set(acc["shared_record_files"])

    log_cmd = "git log --format=%%H %s" % rng
    shas = [s for s in git("log", "--format=%H", rng, cwd=root).split() if s]
    lines: List[str] = []
    violations = 0
    for sha in shas:
        author = git("show", "-s", "--format=%an", sha, cwd=root).strip()
        touched = [p for p in git("show", "--pretty=format:", "--name-only", sha,
                                  cwd=root).split("\n") if p.strip()]
        hit = sorted(set(touched) & shared)
        if not hit:
            continue
        if author != accountable:
            violations += 1
            lines.append("VIOLATION %s author=%r is not the accountable seat %r; touched %s"
                         % (sha[:12], author, accountable, ", ".join(hit)))
        else:
            lines.append("ok        %s author=%r touched %s" % (sha[:12], author, ", ".join(hit)))
    return len(shas), violations, lines, log_cmd


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None)
    ap.add_argument("--prospective", action="store_true", help="check a proposed claim")
    ap.add_argument("--seat", default=None)
    ap.add_argument("--write-scope", action="append", default=[])
    ap.add_argument("--range", dest="rng", default=None, help="retrospective commit range, e.g. A..B")
    args = ap.parse_args(argv)

    root = args.root or repo_root()

    with Limit("tools/coordination/check_no_shared_record_write.py", LIMITS, RESIDUE):
        tree_banner(root)
        rc = 0
        did_something = False

        if args.prospective:
            did_something = True
            if not args.seat or not args.write_scope:
                print("VERDICT: PRECONDITION_NOT_MET — --prospective needs --seat and --write-scope")
                return 2
            try:
                bad = prospective_violation(root, args.write_scope, args.seat)
            except Exception as exc:
                print("VERDICT: PRECONDITION_NOT_MET — %s" % exc)
                return 2
            if bad:
                print("VERDICT: REFUSED (prospective)")
                print(bad)
                rc = 1
            else:
                print("VERDICT: ADMITTED (prospective) — seat %r declares no shared record file" % args.seat)

        if args.rng:
            did_something = True
            try:
                examined, violations, lines, log_cmd = retrospective(root, args.rng)
            except Exception as exc:
                print("VERDICT: PRECONDITION_NOT_MET — %s" % exc)
                return 2
            for ln in lines:
                print("   %s" % ln)
            say_command("commits_examined", examined, log_cmd)
            say_command("shared_record_violations", violations,
                        "python3 -B tools/coordination/check_no_shared_record_write.py --range %s" % args.rng)
            if violations:
                print("VERDICT: REFUSED (retrospective) — %d commit(s) wrote a shared record file "
                      "under a non-accountable identity" % violations)
                rc = 1
            else:
                print("VERDICT: ADMITTED (retrospective) — every shared-record write in %s carries the "
                      "accountable seat" % args.rng)

        if not did_something:
            print("VERDICT: NOTHING CHECKED — pass --prospective or --range")
            return 2
        return rc


if __name__ == "__main__":
    sys.exit(main())
