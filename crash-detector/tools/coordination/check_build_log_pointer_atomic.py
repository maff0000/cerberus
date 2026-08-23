#!/usr/bin/env python3
"""``CD-PL-F132``'S REAL FIX — increment 12 ITEM 2(e).

The discipline, stated as a property of a COMMIT rather than as a habit of a seat:

    **A commit that ADDS a `governance/engineering/build-log/BL-*.yaml` entry MUST move
    `last_build_log_entry` in `governance/engineering/ACTIVE_WORK.yaml` IN THAT SAME COMMIT, and the
    pointer's new value MUST name a Build Log entry that EXISTS IN THAT COMMIT'S TREE.**

WHY IT IS AN EXECUTABLE AND NOT A RULE
--------------------------------------
Because it has been a rule three times. ``CD-PL-F111`` -> ``CD-PL-F112`` -> ``CD-PL-F132`` is one
discipline that lived only in a seat's attention, was declared structurally fixed, held eight
boundaries, and failed at the ninth. The meta-auditor's phrase, adopted by the Product Owner at
``PO-DECISIONS-0021`` ruling 4: ***"A PREDICTION IS NOT A CARRIER."*** Five consecutive commits
booted ``RESUME_BLOCKED`` and **a cold agent could not start this project from its own tip.**

TWO VIOLATION CLASSES, NAMED SEPARATELY BECAUSE THEY FAIL DIFFERENTLY
---------------------------------------------------------------------
* ``POINTER_NOT_MOVED`` — the commit added an entry and did not touch the pointer. The tip then
  boots ``ACTIVE_WORK_STALE``.
* ``POINTER_DANGLING`` — the pointer names an entry that is not in that commit's tree. The tip then
  boots ``CONTINUITY_REFERENCE_INVALID / RESUME_BLOCKED``, which is strictly worse: it is broken for
  every actor who clones it, while the live worktree reads fine because the file is sitting on disk
  beside it (``CD-PL-F69``).

**IT IS RUN BACKWARD OVER THE PROJECT'S OWN HISTORY AND THE COUNT IS DERIVED, NOT COPIED.** The
record says 4 failures in 91 applications at positions 76, 85, 90 and 91. If this instrument
disagrees with the record, **the instrument's number is the finding and the record is what gets
corrected.**

*(The open question ``WHEN A RULE IS ADOPTED, IS THE RECORD SWEPT BACKWARD FOR THE INSTANCES THAT
MOTIVATED IT?`` has been on this project's docket since ``T23``. This instrument answers it by
example: it sweeps, it counts, it renumbers nothing and it repairs nothing.)*
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import Limit, git, repo_root, say_command, tree_banner  # noqa: E402

ACTIVE_WORK = "governance/engineering/ACTIVE_WORK.yaml"
BUILD_LOG_DIR = "governance/engineering/build-log"
ENTRY_NAME = re.compile(r"^governance/engineering/build-log/(BL-\d{8}T\d{6}Z-\d{4})\.yaml$")
POINTER_RE = re.compile(r"^last_build_log_entry:\s*([A-Za-z0-9T_-]+)", re.MULTILINE)

LIMITS = [
    "DECIDES: for each commit in the range, whether it ADDED a build-log entry without moving "
    "`last_build_log_entry` in ACTIVE_WORK.yaml in the SAME commit (POINTER_NOT_MOVED).",
    "DECIDES: for each commit in the range, whether the pointer's value names an entry ABSENT from "
    "that commit's own tree (POINTER_DANGLING). This is checked on EVERY commit, not only on "
    "commits that added an entry — a dangling pointer is a broken tip however it got there.",
    "DECIDES: whether the pointer names an entry that EXISTS but is not the HIGHEST-NUMBERED entry "
    "in that commit's tree (POINTER_STALE). This is the class that produced the five RESUME_BLOCKED "
    "commits; `pbg`'s own continuity.active_work_currency() calls it ACTIVE_WORK_STALE.",
    "DOES NOT DECIDE: staleness by any ordering other than the four-digit sequence number. If two "
    "lanes interleave one sequence — WHICH THIS PROJECT'S HISTORY DOES, see BLID-D02 — 'highest "
    "number in this tree' is a per-branch notion and the instrument says so rather than claiming a "
    "global order.",
    "DOES NOT DECIDE: whether the entry the pointer names is the RIGHT one. A commit that adds "
    "entry 0140 and points the pointer at an older, existing entry 0132 passes this instrument. "
    "It guards EXISTENCE and SIMULTANEITY, not CORRECTNESS OF CHOICE.",
    "DOES NOT DECIDE: the other continuity pointer fields. `last_completed_checkpoint_sha` and "
    "`continuity_record_commit` went stale in the same boundary as `last_build_log_entry` "
    "(CD-PL-F132's own note: THREE POINTER FIELDS WENT STALE IN ONE BOUNDARY AND ONLY ONE OF THEM "
    "IS CHECKED BY ANY INSTRUMENT). This instrument makes that two, not three.",
    "DOES NOT DECIDE: semantic validity of ACTIVE_WORK.yaml. `pbg boot` does that and does it well "
    "(CD-PL-F148 was a schema violation this instrument would have waved through).",
    "IT IS NOT INVOKED BY ANYTHING. See the CD-RULE-006 declaration in ITEM 4(ii) and Q11.",
]

RESIDUE = ("AUTOMATIC INVOCATION IS NOT PROVED TO BE CARRIED ANYWHERE. The only automatic pre-write "
           "carrier in this repository is `pbg/tools/hooks/pre-commit`, which greps "
           "`^governance/authority/` and nothing else, and `pbg/` is pinned read-only to every seat "
           "(PBG-FWK-013). The detector that would catch this — `continuity.active_work_currency()` "
           "— already exists inside `pbg/` and IS NOT CONNECTED TO THE GATE THAT RUNS ON EVERY "
           "COMMIT. That is Q11 and no seat this project dispatches may close it.")


def pointer_at(root: str, sha: str) -> Optional[str]:
    try:
        blob = git("show", "%s:%s" % (sha, ACTIVE_WORK), cwd=root)
    except RuntimeError:
        return None
    m = POINTER_RE.search(blob)
    return m.group(1) if m else None


def entry_exists_at(root: str, sha: str, entry_id: str) -> bool:
    path = "%s/%s.yaml" % (BUILD_LOG_DIR, entry_id)
    try:
        git("cat-file", "-e", "%s:%s" % (sha, path), cwd=root)
        return True
    except RuntimeError:
        return False


def entry_number(entry_id: Optional[str]) -> Optional[int]:
    if not entry_id:
        return None
    m = re.search(r"-(\d{4})$", entry_id)
    return int(m.group(1)) if m else None


def highest_entry_at(root: str, sha: str) -> Optional[str]:
    """The highest-numbered build-log entry present in this commit's OWN tree."""
    out = git("ls-tree", "--name-only", sha, BUILD_LOG_DIR + "/", cwd=root)
    best, best_n = None, -1
    for line in out.split("\n"):
        m = ENTRY_NAME.match(line.strip())
        if not m:
            continue
        n = entry_number(m.group(1))
        if n is not None and n > best_n:
            best, best_n = m.group(1), n
    return best


def added_entries(root: str, sha: str) -> List[str]:
    out = git("show", "--pretty=format:", "--diff-filter=A", "--name-only", sha, cwd=root)
    ids = []
    for line in out.split("\n"):
        m = ENTRY_NAME.match(line.strip())
        if m:
            ids.append(m.group(1))
    return ids


def touched(root: str, sha: str, path: str) -> bool:
    out = git("show", "--pretty=format:", "--name-only", sha, cwd=root)
    return path in [ln.strip() for ln in out.split("\n")]


def sweep(root: str, rev: str) -> Tuple[int, int, int, List[Dict], str]:
    """Walk history OLDEST-FIRST. Returns (applications, violations, examined, records, command)."""
    cmd = "git rev-list --reverse --first-parent %s" % rev
    shas = [s for s in git("rev-list", "--reverse", "--first-parent", rev, cwd=root).split() if s]
    records: List[Dict] = []
    applications = 0          # commits that ADDED at least one build-log entry
    violations = 0

    for sha in shas:
        adds = added_entries(root, sha)
        ptr = pointer_at(root, sha)
        classes: List[str] = []

        if adds:
            applications += 1
            if not touched(root, sha, ACTIVE_WORK):
                classes.append("POINTER_NOT_MOVED")

        if ptr is not None and not entry_exists_at(root, sha, ptr):
            classes.append("POINTER_DANGLING")
        elif ptr is not None:
            # POINTER_STALE — the pointer names an entry that EXISTS but is not the highest-numbered
            # entry in this commit's own tree. THIS IS THE CLASS THAT ACTUALLY PRODUCED THE FIVE
            # RESUME_BLOCKED COMMITS. `pbg`'s own `continuity.active_work_currency()` returns
            # ACTIVE_WORK_STALE for it. An earlier draft of this instrument checked only
            # POINTER_NOT_MOVED and POINTER_DANGLING and MISSED a31c799, c6ee53e and 5f09627 — three
            # of the five commits the record names — because each of them moved the pointer to a
            # real entry that was no longer the latest. A near-miss that passes is the exact shape
            # of every escape on this project's record.
            top = highest_entry_at(root, sha)
            if top is not None and entry_number(ptr) is not None and entry_number(top) is not None:
                if entry_number(ptr) < entry_number(top):
                    classes.append("POINTER_STALE")

        if classes:
            violations += 1
            records.append({
                "position": applications if adds else None,
                "sha": sha,
                "short": sha[:12],
                "author": git("show", "-s", "--format=%an", sha, cwd=root).strip(),
                "added": adds,
                "pointer": ptr,
                "classes": classes,
            })
    return applications, violations, len(shas), records, cmd


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None)
    ap.add_argument("--rev", default="HEAD", help="tip to sweep backward from (default HEAD)")
    ap.add_argument("--range", dest="rng", default=None,
                    help="a commit range instead of a full backward sweep, e.g. A..B")
    args = ap.parse_args(argv)
    root = args.root or repo_root()
    rev = args.rng or args.rev

    with Limit("tools/coordination/check_build_log_pointer_atomic.py", LIMITS, RESIDUE):
        tree_banner(root)
        try:
            applications, violations, examined, records, cmd = sweep(root, rev)
        except Exception as exc:
            print("VERDICT: PRECONDITION_NOT_MET — %s" % exc)
            return 2

        for r in records:
            print("   VIOLATION %s  author=%-24s classes=%s"
                  % (r["short"], r["author"], ",".join(r["classes"])))
            if r["added"]:
                print("                 added   : %s" % ", ".join(r["added"]))
            print("                 pointer : %s" % r["pointer"])
            if r["position"]:
                print("                 position: %d of the applications counted so far" % r["position"])

        say_command("commits_examined", examined, cmd)
        say_command("applications_of_the_discipline", applications,
                    "python3 -B tools/coordination/check_build_log_pointer_atomic.py --rev %s   "
                    "# a commit that ADDED at least one BL-*.yaml" % rev)
        say_command("violations", violations,
                    "python3 -B tools/coordination/check_build_log_pointer_atomic.py --rev %s" % rev)
        by_class: Dict[str, int] = {}
        for r in records:
            for c in r["classes"]:
                by_class[c] = by_class.get(c, 0) + 1
        for c, n in sorted(by_class.items()):
            say_command("violations[%s]" % c, n,
                        "python3 -B tools/coordination/check_build_log_pointer_atomic.py --rev %s"
                        " | grep -c %s" % (rev, c))
        positions = [r["position"] for r in records if r["position"]]
        if positions:
            say_command("failing_positions", positions,
                        "python3 -B tools/coordination/check_build_log_pointer_atomic.py --rev %s" % rev)

        if violations:
            print("VERDICT: REFUSED — %d violating commit(s) in %d application(s) over %d commit(s)"
                  % (violations, applications, examined))
            return 1
        print("VERDICT: ADMITTED — %d application(s) over %d commit(s), no violation"
              % (applications, examined))
        return 0


if __name__ == "__main__":
    sys.exit(main())
