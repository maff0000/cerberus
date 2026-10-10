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

=====================================================================================================
IDENTITY IS NOT THE DISCRIMINATOR. **`CD-ASR-WO2R3-06-F08`, AND IT WAS THE CENTRE OF THIS FILE.**
=====================================================================================================

Increment 12 shipped this instrument with a same-seat skip:

    sa, sb = a.get("seat_actor_id"), b.get("seat_actor_id")
    if sa == sb:
        lines.append("note ... not a cross-seat pair, not examined")
        continue

**SO THE INSTRUMENT BUILT TO DETECT THE FOUNDING INCIDENT PRINTED ``CONCURRENT WORK PROCEEDS`` FOR
THE FOUNDING INCIDENT, AND EXITED 0.** ``VERDICT-META-ASSURANCE-01-SECOND-SEAT`` §1.1 describes that
incident in its own words: *"TWO PROJECT LEAD SESSIONS ALIVE SIMULTANEOUSLY ON `main`, BOTH WITH
COMMIT AUTHORITY, **BOTH COMMITTING AS `PROJECT_LEAD_SEAT_01`**, NEITHER AWARE OF THE OTHER"*. One
identity. Two live claims. One shared record file. **THE SAME-IDENTITY PAIR IS THE INCIDENT; IT IS
NOT AN EXCEPTION TO THE CLASS.**

``PO-DECISIONS-0022`` ruling 5 orders the correction in the Product Owner's own words: *"the control
must FLAG two live claims on one scope regardless of identity"*, and ruling 3 places the Product
Authority's own hand inside ``CD-RULE-002`` with no exemption, because the incident was the Product
Owner's own breach of it.

**THE REGISTRY CANNOT TELL YOU WHETHER TWO LIVE CLAIMS ARE ONE SESSION OR TWO, AND THAT IS PRECISELY
WHY IDENTITY MUST NOT BE THE DISCRIMINATOR.** Two live claims are two live claims.

THE FOUR PAIRINGS, AND THE TWO EXEMPTIONS THAT SURVIVE — DELIBERATELY, AND NOT BY OMISSION
------------------------------------------------------------------------------------------
The unit of comparison is **a pair of DISTINCT live claim RECORDS**, at ANY identity.

* ``A.write x B.write``  — **EXAMINED.** Overlap is a violation at any identity.
* ``A.write x B.read``   — **EXAMINED, BOTH DIRECTIONS.** ``CD-PL-F134``. Any identity.
* ``A.read  x B.read``   — **NOT EXAMINED, AND THAT IS DELIBERATE.** Two seats reading one file is
  the normal case; refusing it would ban every parallel audit, which is precisely the vacuity
  ``PO-DECISIONS-0021`` ruling 3 rejects. **This exemption is about the PAIRING, not the identity,
  and the F08 correction does not touch it.**
* **ONE claim record's OWN write scope against its OWN read scope — NOT EXAMINED, AND THAT IS
  DELIBERATE.** A seat reading what it is about to write is what work IS. **This exemption is about
  a SINGLE RECORD, not about two records sharing an identity**, and the F08 correction does not
  touch it either: the pair loop never compares a record with itself.

**A SEAT MAY HOLD TWO CLAIMS AND BOTH ARE ADMITTED — PROVIDED THEY ARE DISJOINT.** That is a
deliberate design call and it is declared: only the OVERLAPPING same-identity pair is the violation.
A blanket refusal of same-identity multi-claim would have been defensible and would have narrowed
what the machinery permits, so it was not taken. ``PLANT-COORD-05`` arm 3 measures the disjoint
same-identity pair still being ADMITTED, because a control that refuses the disjoint case has not
fixed ``F08`` — it has banned concurrency.
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
    "DECIDES: pairwise WRITE x WRITE disjointness over EVERY pair of DISTINCT live claim records, "
    "**AT ANY IDENTITY, INCLUDING TWO CLAIMS HELD BY ONE SEAT ID**. Identity is NOT a "
    "discriminator here and MUST NOT BE: the founding incident was two sessions under ONE identity "
    "(CD-ASR-WO2R3-06-F08, PO-DECISIONS-0022 ruling 5).",
    "DECIDES: pairwise WRITE x READ disjointness over EVERY pair of DISTINCT live claim records, in "
    "both directions (A.write vs B.read AND B.write vs A.read), **AT ANY IDENTITY**. This is "
    "CD-PL-F134 with the F08 correction applied.",
    "DELIBERATELY DOES NOT REFUSE: READ x READ, at any identity. Two seats reading one file is the "
    "normal case, and refusing it would ban parallel audits — the vacuity PO-DECISIONS-0021 ruling "
    "3 rejects. This exemption is about the PAIRING and not about the identity.",
    "DELIBERATELY DOES NOT REFUSE: ONE claim record's own write scope against its OWN read scope. A "
    "seat reading what it is about to write is what work IS. This exemption is about a SINGLE "
    "RECORD; the pair loop never compares a record with itself. It is NOT an identity exemption, "
    "and two DISTINCT records sharing one seat id ARE compared.",
    "DELIBERATELY ADMITS: one seat holding two or more DISJOINT live claims. A blanket refusal of "
    "same-identity multi-claim was available and was NOT taken, because it narrows what the "
    "machinery permits; only the OVERLAPPING same-identity pair is the violation. Measured by "
    "PLANT-COORD-05 arm 3.",
    "DECIDES: symlink aliasing in the LITERAL leading segments of a scope — a scope whose prefix "
    "traverses a symlink is REFUSED, not decided, because the algebra is textual.",
    "DOES NOT DECIDE: a seat that writes outside its declared scope. This instrument reads "
    "DECLARATIONS. What actually got touched is merge_reconcile.py assertion (1), CONTAINMENT, and "
    "that runs after the fact rather than before it.",
    "DOES NOT DECIDE: a live actor that never took a claim. It is blind to unclaimed work by "
    "construction — there is nothing in the registry to compare.",
    "DOES NOT DECIDE: whether two live claim records are two SESSIONS or one. It cannot, and after "
    "the F08 correction it does not need to — it grades the pair, not the process.",
    "*** IT IS NOT INVOKED BY ANYTHING. *** Nothing in this repository runs this file "
    "automatically. That is Q11, it is routed to the framework with its priority INVERTED — "
    "correctness before carriage (PO-DECISIONS-0022 ruling 4) — and it is NOT closed here.",
]

RESIDUE = ("the gap between a DECLARED scope and a TOUCHED path is carried by "
           "`tools/coordination/merge_reconcile.py` assertion (1) CONTAINMENT, which is MEASURED by "
           "PLANT-COORD-03 and is not asserted here. The gap between a live actor and a claim is "
           "carried by `tools/coordination/launch.sh` for launches that go through it, and for "
           "every other route it is NOT PROVED TO BE CARRIED ANYWHERE. AUTOMATIC INVOCATION OF THIS "
           "FILE IS **NOT PROVED TO BE CARRIED ANYWHERE** (Q11).")


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

    # ------------------------------------------------------------------------------------------
    # THE PAIR LOOP. **THE UNIT IS A PAIR OF DISTINCT LIVE CLAIM RECORDS, AT ANY IDENTITY.**
    #
    # `range(i + 1, ...)` is the ONLY exemption that operates here, and it is a RECORD exemption,
    # not an identity one: a record is never compared with itself, so a claim's own write scope is
    # never tested against its own read scope. THAT is the exemption the increment-12 docstring
    # meant, and it survives the F08 correction untouched.
    #
    # WHAT DOES NOT SURVIVE is `if sa == sb: continue`. Two live claim records under ONE seat id
    # are two live claims, and they are the founding incident. See the module docstring.
    # ------------------------------------------------------------------------------------------
    for i in range(len(recs)):
        for j in range(i + 1, len(recs)):
            a, b = recs[i], recs[j]
            sa, sb = a.get("seat_actor_id"), b.get("seat_actor_id")
            same_identity = (sa == sb)
            # NOT a skip. A LABEL. The pair is examined either way; the label exists so that a
            # reader sees the founding-incident shape called by its name when it occurs.
            kind = "SAME-IDENTITY" if same_identity else "cross-seat"
            incident = ("  *** ONE IDENTITY, TWO LIVE CLAIMS, OVERLAPPING SCOPE — THIS IS THE "
                        "FOUNDING INCIDENT SHAPE (CD-ASR-WO2R3-06-F08). The registry cannot tell "
                        "you whether these are one session or two, and PO-DECISIONS-0022 ruling 5 "
                        "is that it must not need to. ***") if same_identity else ""

            pair_violations = 0
            aw, bw = _scope_of(a, "write_scope"), _scope_of(b, "write_scope")
            if aw and bw:
                ov, hits = scope_mod.overlaps(aw, bw)
                if ov:
                    violations += 1
                    pair_violations += 1
                    lines.append("VIOLATION WRITE/WRITE [%s]  seat %s (task %s)  x  seat %s (task %s)"
                                 % (kind, sa, a.get("task_id"), sb, b.get("task_id")))
                    for h in hits:
                        lines.append("            %s" % h)
                    if incident:
                        lines.append("          %s" % incident)

            for (wr, wseat, wtask), (rd, rseat, rtask) in (
                ((aw, sa, a.get("task_id")), (_scope_of(b, "read_scope"), sb, b.get("task_id"))),
                ((bw, sb, b.get("task_id")), (_scope_of(a, "read_scope"), sa, a.get("task_id"))),
            ):
                # READ x READ is never constructed here: the left side of every pairing is a WRITE
                # scope. That is the deliberate exemption, and it is a PAIRING exemption.
                if not wr or not rd:
                    continue
                ov, hits = scope_mod.overlaps(wr, rd)
                if ov:
                    violations += 1
                    pair_violations += 1
                    lines.append("VIOLATION WRITE/READ (CD-PL-F134) [%s]  seat %s (task %s) WRITES "
                                 "what seat %s (task %s) declared it would READ"
                                 % (kind, wseat, wtask, rseat, rtask))
                    for h in hits:
                        lines.append("            %s" % h)
                    if incident:
                        lines.append("          %s" % incident)

            if pair_violations == 0:
                lines.append("ok        %s (task %s) x %s (task %s) [%s] — disjoint on WRITE/WRITE "
                             "and on both WRITE/READ directions; BOTH MAY PROCEED IN PARALLEL"
                             % (sa, a.get("task_id"), sb, b.get("task_id"), kind))
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
