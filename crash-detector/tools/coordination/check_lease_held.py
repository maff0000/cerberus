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
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lease as lease_mod  # noqa: E402
import registry  # noqa: E402
import scope as scope_mod  # noqa: E402
from common import Limit, git, repo_root, say_command, tree_banner  # noqa: E402

GOVERNED_PREFIXES = ("governance/", "tools/", "src/", "BLUEPRINT.md", "PID.md")

LIMITS = [
    "DECIDES: whether every governed path in the staged set (or in a commit range) is inside the "
    "write scope of a LIVE lease held by the named identity.",
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


def range_paths(root: str, rng: str) -> List[str]:
    out = git("diff", "--name-only", rng, cwd=root)
    return sorted({p for p in out.split("\n") if p.strip()})


def covering_lease(root: str, identity: str, path: str) -> Tuple[bool, str]:
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

        paths = staged_paths(root) if args.staged else range_paths(root, args.rng)
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
                    ("git diff --cached --name-only --diff-filter=ACMR" if args.staged
                     else "git diff --name-only %s" % args.rng))
        say_command("governed_paths", len(gov), "(filtered by governed_prefixes above)")
        say_command("uncovered_governed_paths", len(uncovered),
                    "python3 -B tools/coordination/check_lease_held.py %s"
                    % ("--staged" if args.staged else "--range " + args.rng))
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
