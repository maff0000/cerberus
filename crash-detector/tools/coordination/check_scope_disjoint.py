#!/usr/bin/env python3
"""THE LIVE DISJOINTNESS CHECK — increment 12 ITEM 2(b), ``PO-DECISIONS-0021`` ruling 3(b).

Over **all live claims**, assert that the write scopes are pairwise disjoint. Non-zero exit names
the two seats and the overlapping path.

**AND THE ASYMMETRIC CASE, WHICH IS THE ONE EVERYBODY FORGETS — INCLUDING THE SEAT THAT RAISED IT.**
One seat's WRITE scope against another seat's READ scope. That is ``CD-PL-F134``:

    *"`main` ADVANCED `d0d13f8` -> `baede05` WHILE `CD-ASR-WO2R3-05` WAS LIVE ... BUT `governance/`
    ON `main` IS THE SEAT'S OWN READING MATERIAL, AND IT CHANGED UNDER IT. ... THE HARM WAS ZERO
    AND THE DISCIPLINE WAS STILL BROKEN. The remedy is not "remember"."*

Write-vs-write disjointness alone would have passed that incident cleanly: the Project Lead and the
Assurance seat were not writing the same file. The auditor was *reading* what the Project Lead was
*writing*, and no symmetric check sees it.

WHY THE ASYMMETRY IS NOT SYMMETRIC
----------------------------------
``A.write x B.read`` is a violation. ``A.read x B.read`` is **NOT** — two seats reading the same
file is the normal case and refusing it would ban every parallel audit, which is precisely the
vacuity ruling 3 rejects. This instrument checks exactly three of the four pairings and says so.

**A SEAT'S OWN WRITE SCOPE OVERLAPPING ITS OWN READ SCOPE IS ALSO NOT A VIOLATION** — a seat reading
what it is about to write is what work is. Only *cross-seat* pairs are examined.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import registry  # noqa: E402
import scope as scope_mod  # noqa: E402
from common import Limit, repo_root, say_command, tree_banner  # noqa: E402

LIMITS = [
    "DECIDES: pairwise WRITE x WRITE disjointness over all live claims.",
    "DECIDES: pairwise WRITE x READ disjointness across DIFFERENT seats, in both directions "
    "(A.write vs B.read AND B.write vs A.read). This is CD-PL-F134.",
    "DELIBERATELY DOES NOT REFUSE: READ x READ. Two seats reading one file is the normal case, and "
    "refusing it would ban parallel audits — the vacuity PO-DECISIONS-0021 ruling 3 rejects.",
    "DELIBERATELY DOES NOT REFUSE: a seat's own write scope overlapping its own read scope.",
    "DECIDES: symlink aliasing in the LITERAL leading segments of a scope — a scope whose prefix "
    "traverses a symlink is REFUSED, not decided, because the algebra is textual.",
    "DOES NOT DECIDE: a seat that writes outside its declared scope. This instrument reads "
    "DECLARATIONS. What actually got touched is merge_reconcile.py assertion (1), CONTAINMENT, and "
    "that runs after the fact rather than before it.",
    "DOES NOT DECIDE: a live actor that never took a claim. It is blind to unclaimed work by "
    "construction — there is nothing in the registry to compare.",
]

RESIDUE = ("the gap between a DECLARED scope and a TOUCHED path is carried by "
           "`tools/coordination/merge_reconcile.py` assertion (1) CONTAINMENT, which is MEASURED by "
           "PLANT-COORD-03 and is not asserted here. The gap between a live actor and a claim is "
           "carried by `tools/coordination/launch.sh` for launches that go through it, and for "
           "every other route it is NOT PROVED TO BE CARRIED ANYWHERE.")


def _scope_of(rec: Dict[str, Any], key: str) -> List[str]:
    return list(rec.get(key) or [])


def check(root: str) -> Tuple[int, int, List[str]]:
    """Return ``(live_claim_count, violation_count, lines)``."""
    recs = [r for r in registry.list_records(root, registry.CLAIMS_DIR, registry.CLAIM_SUFFIX)
            if r.get("state") == registry.STATE_CLAIMED]
    lines: List[str] = []
    violations = 0

    # 0. symlink refusal — a textual algebra must not be handed an aliased path
    for r in recs:
        for key in ("write_scope", "read_scope"):
            for raw in _scope_of(r, key):
                try:
                    pat = scope_mod.parse_pattern(raw)
                except scope_mod.ScopeInvalid as exc:
                    violations += 1
                    lines.append("REFUSED  seat=%s %s entry %r is INVALID: %s"
                                 % (r.get("seat_actor_id"), key, raw, exc))
                    continue
                links = scope_mod.symlinked_components(root, pat)
                if links:
                    violations += 1
                    lines.append("REFUSED  seat=%s %s entry %r traverses a symlink at %s — the "
                                 "algebra is textual and cannot see through it"
                                 % (r.get("seat_actor_id"), key, raw, ", ".join(links)))

    for i in range(len(recs)):
        for j in range(i + 1, len(recs)):
            a, b = recs[i], recs[j]
            sa, sb = a.get("seat_actor_id"), b.get("seat_actor_id")
            if sa == sb:
                lines.append("note     seat=%s holds two claims (%s, %s) — not a cross-seat pair, "
                             "not examined" % (sa, a.get("task_id"), b.get("task_id")))
                continue

            pair_violations = 0
            aw, bw = _scope_of(a, "write_scope"), _scope_of(b, "write_scope")
            if aw and bw:
                ov, hits = scope_mod.overlaps(aw, bw)
                if ov:
                    violations += 1
                    pair_violations += 1
                    lines.append("VIOLATION WRITE/WRITE  seat %s (task %s)  x  seat %s (task %s)"
                                 % (sa, a.get("task_id"), sb, b.get("task_id")))
                    for h in hits:
                        lines.append("            %s" % h)

            for (wr, wseat, wtask), (rd, rseat, rtask) in (
                ((aw, sa, a.get("task_id")), (_scope_of(b, "read_scope"), sb, b.get("task_id"))),
                ((bw, sb, b.get("task_id")), (_scope_of(a, "read_scope"), sa, a.get("task_id"))),
            ):
                if not wr or not rd:
                    continue
                ov, hits = scope_mod.overlaps(wr, rd)
                if ov:
                    violations += 1
                    pair_violations += 1
                    lines.append("VIOLATION WRITE/READ (CD-PL-F134)  seat %s (task %s) WRITES what "
                                 "seat %s (task %s) declared it would READ"
                                 % (wseat, wtask, rseat, rtask))
                    for h in hits:
                        lines.append("            %s" % h)

            if pair_violations == 0:
                lines.append("ok        %s x %s — disjoint on WRITE/WRITE and on both WRITE/READ "
                             "directions; BOTH MAY PROCEED IN PARALLEL" % (sa, sb))
    return len(recs), violations, lines


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None)
    args = ap.parse_args(argv)
    root = args.root or repo_root()

    with Limit("tools/coordination/check_scope_disjoint.py", LIMITS, RESIDUE):
        tree_banner(root)
        ins, cmd = scope_mod.filesystem_is_case_insensitive(root)
        print("filesystem_case_insensitive = %s" % ins)
        print("    produced by: %s" % cmd)
        try:
            live, violations, lines = check(root)
        except Exception as exc:
            print("VERDICT: PRECONDITION_NOT_MET — %s" % exc)
            return 2
        for ln in lines:
            print("   %s" % ln)
        say_command("live_claims", live,
                    "python3 -B tools/coordination/claim.py list")
        say_command("scope_violations", violations,
                    "python3 -B tools/coordination/check_scope_disjoint.py")
        if violations:
            print("VERDICT: REFUSED — %d scope violation(s) among %d live claim(s)" % (violations, live))
            return 1
        print("VERDICT: ADMITTED — %d live claim(s), pairwise disjoint. CONCURRENT WORK PROCEEDS."
              % live)
        return 0


if __name__ == "__main__":
    sys.exit(main())
