#!/usr/bin/env python3
"""THE MERGE / RECONCILIATION STEP — increment 12 ITEM 3, ``PO-DECISIONS-0021`` ruling 3(c).

The ruling: *"A MERGE / RECONCILIATION step at the accountable seat that integrates disjoint results
and asserts no two seats touched the same artefact."*

    merge_reconcile.py --base <sha> --claim <task-id> [--claim <task-id> ...] [--emit]

THREE ASSERTIONS, ALL REQUIRED, ANY ONE FAILING IS A REFUSAL
------------------------------------------------------------
1. **CONTAINMENT** — for each claim, every path in ``git diff --name-only <base>..<seat-tip>`` is
   INSIDE that seat's declared ``write_scope``. A seat that exceeded its lane is NAMED with the
   path. This is the arm that closes the gap ``check_scope_disjoint.py`` declares: that instrument
   reads DECLARATIONS, this one reads what was actually TOUCHED.
2. **NON-OVERLAP** — the one the ruling names. The pairwise INTERSECTION of the seats'
   touched-path sets is EMPTY. Non-zero exit names the ARTEFACT and BOTH seats.
3. **IDENTITY** — every commit in each seat's range carries that seat's ``actor_id`` as the git
   author (``CD-RULE-002``). **TWO IDENTITIES INTERLEAVED IN ONE HISTORY IS `CD-RULE-002`'S EXACT
   FAILURE MODE**, and "two Project Leads commit as one identity and nothing detects it" is what it
   means in practice.

IT EMITS A RECORD, AND THE RECORD IS THE POINT
-----------------------------------------------
``governance/coordination/merges/<utc>-<merge-id>.yaml``. ``PBG-CONT-007``: a result that exists
only in conversation is not project state. **A merge that happened but was not recorded is
indistinguishable from one that did not.**

THE HONEST LIMIT, DECLARED HERE AND PRINTED ON EVERY RUN (``CD-RULE-004``)
--------------------------------------------------------------------------
``git diff --name-only`` measures **PATHS, NOT BYTES.**

* Two seats editing **disjoint REGIONS of one file** are REFUSED by this instrument. That is a
  deliberate over-refusal: the tool cannot prove region-disjointness and will not guess.
* Two seats writing the same bytes **THROUGH a path neither declared** — a symlink, a generated
  file, a `.gitignore`d artefact, a database — are **NOT CAUGHT AT ALL.** Nothing here looks
  outside the git index.
* This instrument reads history. **It does not perform the merge and it cannot prevent one.**
  It is a gate the accountable seat must choose to walk through.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import registry  # noqa: E402
import scope as scope_mod  # noqa: E402
from common import Limit, git, repo_root, resolve_sha, say_command, tree_banner, utc_now  # noqa: E402

LIMITS = [
    "MEASURES PATHS, NOT BYTES. `git diff --name-only` is the whole input.",
    "OVER-REFUSES: two seats editing DISJOINT REGIONS of ONE file are refused. Region-disjointness "
    "is not proved by this instrument and it will not guess.",
    "DOES NOT CATCH: two seats writing the same bytes THROUGH a path neither declared — a symlink, "
    "a generated file, a .gitignore'd artefact, a database, a file outside the repository.",
    "DOES NOT CATCH: a seat whose commits are not in the range it declared. The range comes from "
    "the claim record's base_sha and the named tip; a seat that committed elsewhere is invisible.",
    "DOES NOT PERFORM THE MERGE AND CANNOT PREVENT ONE. It is a gate the accountable seat must "
    "choose to walk through, and nothing in this repository forces that choice — see ITEM 4(ii).",
    "IDENTITY assertion reads the git AUTHOR name only. CD-RULE-002 gives one identity to a ROLE, "
    "so two concurrent sessions of one role pass this assertion. That is the second meta-assurance "
    "seat's §7.2 and it is not closed here.",
]

RESIDUE = ("BYTE-LEVEL and OUT-OF-INDEX collision is NOT PROVED TO BE CARRIED ANYWHERE. No "
           "instrument on this project reads two seats' edits for region overlap, and nothing "
           "watches paths git does not track. The over-refusal on same-path edits is the only "
           "thing standing where that control would be, and it is a blunt instrument by design.")


def claim_of(root: str, task: str) -> Dict[str, Any]:
    p = registry.record_path(root, registry.CLAIMS_DIR, task, registry.CLAIM_SUFFIX)
    if not os.path.exists(p):
        raise RuntimeError("PRECONDITION_NOT_MET: no claim record for task %r at %s"
                           % (task, os.path.relpath(p, root)))
    rec = registry.load(p)
    rec["__path__"] = os.path.relpath(p, root)
    return rec


def touched_paths(root: str, base: str, tip: str) -> List[str]:
    out = git("diff", "--name-only", "%s..%s" % (base, tip), cwd=root)
    return sorted({p for p in out.split("\n") if p.strip()})


def commits_in(root: str, base: str, tip: str) -> List[Tuple[str, str, str]]:
    out = git("log", "--format=%H%x1f%an%x1f%ae", "%s..%s" % (base, tip), cwd=root)
    rows = []
    for line in out.split("\n"):
        if not line.strip():
            continue
        sha, an, ae = line.split("\x1f")
        rows.append((sha, an, ae))
    return rows


def path_in_scope(path: str, write_scope: List[str]) -> Tuple[bool, str]:
    """Is a concrete touched path inside the declared write scope?

    A concrete path is a LITERAL pattern, so this reduces to pattern-vs-pattern overlap, which the
    algebra decides exactly for the forms it decides and fails closed on the rest. Failing closed
    here means REPORTING IT AS IN-SCOPE, which would be the wrong direction — so for containment the
    UNDECIDABLE case is reported as OUT of scope and named as undecidable.
    """
    if not write_scope:
        return False, "the seat declared no write scope"
    lit = scope_mod.parse_pattern(path)
    for raw in write_scope:
        pat = scope_mod.parse_pattern(raw)
        if pat.undecidable_reason:
            continue
        ov, why = scope_mod.patterns_overlap(lit, pat)
        if ov and "UNDECIDABLE" not in why and "CASE_COLLISION" not in why:
            return True, "covered by %r (%s)" % (raw, why)
    return False, "no DECIDABLE entry in %s covers it" % (write_scope,)


def reconcile(root: str, base: str, tasks: List[str], tips: Dict[str, str]) -> Dict[str, Any]:
    base_sha = resolve_sha(base, cwd=root)
    seats: List[Dict[str, Any]] = []
    findings: List[str] = []

    for task in tasks:
        rec = claim_of(root, task)
        seat = rec.get("seat_actor_id")
        tip = tips.get(task) or rec.get("tip") or rec.get("branch")
        if not tip:
            raise RuntimeError("PRECONDITION_NOT_MET: no tip for task %r — pass --tip %s=<rev>"
                               % (task, task))
        tip_sha = resolve_sha(tip, cwd=root)
        paths = touched_paths(root, base_sha, tip_sha)
        commits = commits_in(root, base_sha, tip_sha)
        seats.append({
            "task_id": task,
            "seat_actor_id": seat,
            "claim_record": rec["__path__"],
            "write_scope": list(rec.get("write_scope") or []),
            "tip_rev": tip,
            "tip_sha": tip_sha,
            "commits": [{"sha": c[0], "author_name": c[1], "author_email": c[2]} for c in commits],
            "touched_paths": paths,
        })

    # ---- ASSERTION 1: CONTAINMENT -------------------------------------------------------------
    containment = []
    for s in seats:
        breaches = []
        for p in s["touched_paths"]:
            inside, why = path_in_scope(p, s["write_scope"])
            if not inside:
                breaches.append({"path": p, "why": why})
        containment.append({"seat_actor_id": s["seat_actor_id"], "task_id": s["task_id"],
                            "breaches": breaches})
        for b in breaches:
            findings.append("CONTAINMENT seat %s (task %s) touched %s which is OUTSIDE its declared "
                            "write_scope %s — %s"
                            % (s["seat_actor_id"], s["task_id"], b["path"], s["write_scope"], b["why"]))

    # ---- ASSERTION 2: NON-OVERLAP -------------------------------------------------------------
    intersections = []
    for i in range(len(seats)):
        for j in range(i + 1, len(seats)):
            a, b = seats[i], seats[j]
            inter = sorted(set(a["touched_paths"]) & set(b["touched_paths"]))
            intersections.append({
                "seat_a": a["seat_actor_id"], "task_a": a["task_id"],
                "seat_b": b["seat_actor_id"], "task_b": b["task_id"],
                "intersection": inter, "empty": len(inter) == 0,
            })
            for p in inter:
                findings.append("NON_OVERLAP artefact %s was touched by BOTH seat %s (task %s) and "
                                "seat %s (task %s)"
                                % (p, a["seat_actor_id"], a["task_id"], b["seat_actor_id"], b["task_id"]))

    # ---- ASSERTION 3: IDENTITY ----------------------------------------------------------------
    identity = []
    for s in seats:
        bad = [c for c in s["commits"] if c["author_name"] != s["seat_actor_id"]]
        identity.append({"seat_actor_id": s["seat_actor_id"], "task_id": s["task_id"],
                         "commits": len(s["commits"]), "foreign": bad})
        for c in bad:
            findings.append("IDENTITY commit %s in seat %s's range is authored %r <%s>, not %r "
                            "(CD-RULE-002)"
                            % (c["sha"][:12], s["seat_actor_id"], c["author_name"],
                               c["author_email"], s["seat_actor_id"]))

    return {
        "record_type": "MERGE_RECONCILIATION",
        "base_sha": base_sha,
        "seats": seats,
        "assertion_1_containment": containment,
        "assertion_2_non_overlap": intersections,
        "assertion_3_identity": identity,
        "findings": findings,
        "verdict": "REFUSED" if findings else "ADMITTED",
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None)
    ap.add_argument("--base", required=True)
    ap.add_argument("--claim", action="append", required=True, dest="claims")
    ap.add_argument("--tip", action="append", default=[],
                    help="TASK=REV, the seat's tip. Repeatable. Defaults to the claim's branch.")
    ap.add_argument("--emit", action="store_true",
                    help="write the record under governance/coordination/merges/")
    ap.add_argument("--merge-id", default=None)
    args = ap.parse_args(argv)
    root = args.root or repo_root()

    tips: Dict[str, str] = {}
    for spec in args.tip:
        if "=" not in spec:
            print("--tip must be TASK=REV, got %r" % spec, file=sys.stderr)
            return 2
        k, v = spec.split("=", 1)
        tips[k] = v

    with Limit("tools/coordination/merge_reconcile.py", LIMITS, RESIDUE):
        tree_banner(root)
        try:
            result = reconcile(root, args.base, args.claims, tips)
        except Exception as exc:
            print("VERDICT: PRECONDITION_NOT_MET — %s" % exc)
            return 2

        print("base_sha = %s   (git rev-parse %s ; git cat-file -t -> commit)" % (result["base_sha"], args.base))
        for s in result["seats"]:
            print("   seat %-22s task=%-22s tip=%s" % (s["seat_actor_id"], s["task_id"], s["tip_sha"][:12]))
            say_command("     touched_paths", len(s["touched_paths"]),
                        "git diff --name-only %s..%s" % (result["base_sha"][:12], s["tip_sha"][:12]))
            for p in s["touched_paths"]:
                print("        %s" % p)
            say_command("     commits", len(s["commits"]),
                        "git log --format=%%H %s..%s" % (result["base_sha"][:12], s["tip_sha"][:12]))

        print("")
        print("   ASSERTION 1 CONTAINMENT : %s"
              % ("PASS" if not any(c["breaches"] for c in result["assertion_1_containment"]) else "FAIL"))
        print("   ASSERTION 2 NON-OVERLAP : %s"
              % ("PASS" if all(x["empty"] for x in result["assertion_2_non_overlap"]) else "FAIL"))
        print("   ASSERTION 3 IDENTITY    : %s"
              % ("PASS" if not any(i["foreign"] for i in result["assertion_3_identity"]) else "FAIL"))
        for x in result["assertion_2_non_overlap"]:
            print("      %s x %s intersection=%s"
                  % (x["seat_a"], x["seat_b"], x["intersection"] if x["intersection"] else "EMPTY"))
        for f in result["findings"]:
            print("   FINDING %s" % f)

        stamp = utc_now()
        result["reconciled_utc"] = stamp
        merge_id = args.merge_id or ("MERGE-" + "-".join(args.claims))
        result["merge_id"] = merge_id

        if args.emit:
            d = registry.registry_dir(root, registry.MERGES_DIR)
            safe = registry.safe_identifier(stamp.replace(":", "") + "-" + merge_id)
            out = os.path.join(d, safe + ".yaml")
            registry.rewrite(out, result)
            print("   RECORD EMITTED: %s   (PBG-CONT-007)" % os.path.relpath(out, root))
        else:
            print("   RECORD NOT EMITTED — pass --emit. A merge that happened but was not recorded "
                  "is indistinguishable from one that did not (PBG-CONT-007).")

        say_command("findings", len(result["findings"]),
                    "python3 -B tools/coordination/merge_reconcile.py --base %s %s"
                    % (args.base, " ".join("--claim " + c for c in args.claims)))
        if result["findings"]:
            print("VERDICT: REFUSED — the merge is NOT reconciled")
            return 1
        print("VERDICT: ADMITTED — containment, non-overlap and identity all hold")
        return 0


if __name__ == "__main__":
    sys.exit(main())
