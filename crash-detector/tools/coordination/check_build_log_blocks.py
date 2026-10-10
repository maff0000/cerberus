#!/usr/bin/env python3
"""PER-SEAT BUILD LOG ID BLOCKS — increment 12 ITEM 2(c), ``PO-DECISIONS-0021`` ruling 3(b).

Three refusals, and the third is not in the dispatch but is required by the ruling's own words
*"no shared sequence"*:

1. ``--table`` — **TWO ALLOCATED BLOCKS THAT OVERLAP.** Read from
   ``governance/coordination/BUILD-LOG-ID-BLOCKS.yaml``.
2. ``--entries`` — **AN ENTRY WHOSE ID FALLS OUTSIDE ITS AUTHOR'S ALLOCATED BLOCK.** The author is
   the git author of the commit that ADDED the file (``CD-RULE-002``), resolved with
   ``git log --diff-filter=A``, not guessed from the file's contents.
3. ``--entries`` — **TWO ENTRIES SHARING ONE ID NUMBER.** The duplicate ``0136`` on ``main`` is the
   worked instance; the second meta-assurance seat (§7.3) named this as something a uniqueness
   check would have caught in under a second, and nothing was checking.

WHAT THIS INSTRUMENT REFUSES TO DO, AND WHY IT IS A REFUSAL AND NOT AN OMISSION
------------------------------------------------------------------------------
**IT DOES NOT RENUMBER ANYTHING AND IT HAS NO WRITE PATH AT ALL.** Rewriting Build Log history is
non-waivable (``PBG-CONT-003``); corrections supersede, never edit. The dispatch carries
"if closing this requires renumbering an existing entry, STOP" as a declared stop. **THE STOP IS
NOT TRIGGERED**: closing the blocks forward needs no renumbering. The historical collisions are
counted, printed, and left standing.

**AND IT DOES NOT QUIETLY EXCLUDE HISTORY TO OBTAIN A GREEN.** ``--entries --all`` runs over every
entry in the tree and exits non-zero on the historical violations, because a control that starts
counting at the moment it was written is a control that has never been tested. ``--entries --since
<rev>`` restricts to entries added after a named commit, and the restriction is PRINTED with the
count so nobody mistakes a narrowed run for a clean project.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml  # noqa: E402

from common import Limit, git, repo_root, say_command, tree_banner  # noqa: E402

BLOCKS_FILE = "governance/coordination/BUILD-LOG-ID-BLOCKS.yaml"
BUILD_LOG_DIR = "governance/engineering/build-log"
ENTRY_RE = re.compile(r"^BL-\d{8}T\d{6}Z-(\d{4})\.yaml$")

LIMITS = [
    "DECIDES: whether any two ALLOCATED blocks in the table overlap numerically.",
    "DECIDES: whether an entry's id falls inside the block allocated to the git author of the "
    "commit that ADDED it (git log --diff-filter=A --format=%an -- <path>).",
    "DECIDES: whether two entries in the examined set share one id number.",
    "DOES NOT DECIDE: an entry added by a seat with NO allocated block. It is reported as "
    "UNALLOCATED_AUTHOR and counted as a violation — it cannot be inside a block that does not exist.",
    "DOES NOT DECIDE: cross-BRANCH id collisions unless both branches are passed with --ref. A "
    "single-ref run sees one sequence and cannot know about the other. THE PROJECT HAS 18 SUCH "
    "COLLISIONS TODAY (BLID-D02) and a default run would not show them.",
    "DOES NOT RENUMBER, MOVE OR EDIT ANY ENTRY. It has no write path. PBG-CONT-003 is non-waivable.",
    "DOES NOT DECIDE: whether an entry's CONTENT belongs to its author. It reads the filename and "
    "the git author of the adding commit, and nothing inside the file.",
]

RESIDUE = ("cross-branch id collision is carried by this instrument ONLY when the caller passes "
           "two --ref values. For a single-ref run it is NOT PROVED TO BE CARRIED ANYWHERE, and "
           "nothing on this project automatically runs the two-ref form — see Q11/Q12 and ITEM "
           "4(ii)'s CD-RULE-006 declaration.")


def load_blocks(root: str) -> List[Dict]:
    p = os.path.join(root, BLOCKS_FILE)
    if not os.path.exists(p):
        raise RuntimeError("PRECONDITION_NOT_MET: %s does not exist" % BLOCKS_FILE)
    with open(p, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    blocks = data.get("blocks")
    if not blocks:
        raise RuntimeError("PRECONDITION_NOT_MET: %s has no `blocks`" % BLOCKS_FILE)
    return blocks


def check_table(blocks: List[Dict]) -> Tuple[int, List[str]]:
    lines, violations = [], 0
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            a, b = blocks[i], blocks[j]
            lo = max(int(a["first"]), int(b["first"]))
            hi = min(int(a["last"]), int(b["last"]))
            if lo <= hi:
                violations += 1
                lines.append("VIOLATION BLOCK OVERLAP  %s [%04d-%04d] holder=%s  x  %s [%04d-%04d] holder=%s "
                             "-> shared ids %04d-%04d"
                             % (a["id"], a["first"], a["last"], a.get("holder"),
                                b["id"], b["first"], b["last"], b.get("holder"), lo, hi))
            else:
                lines.append("ok        %s [%04d-%04d] x %s [%04d-%04d] disjoint"
                             % (a["id"], a["first"], a["last"], b["id"], b["first"], b["last"]))
    return violations, lines


def entries_of(root: str, ref: str) -> List[str]:
    out = git("ls-tree", "--name-only", ref, BUILD_LOG_DIR + "/", cwd=root)
    return [p for p in out.split("\n") if p.strip()]


def adding_author(root: str, ref: str, path: str) -> Optional[str]:
    out = git("log", "--diff-filter=A", "--format=%an", ref, "--", path, cwd=root).strip()
    if not out:
        return None
    return out.split("\n")[-1].strip()


def block_for(blocks: List[Dict], author: str) -> Optional[Dict]:
    for b in blocks:
        if b.get("holder") == author or b.get("holder_git_author_name") == author:
            return b
    return None


def check_entries(root: str, blocks: List[Dict], refs: List[str], since: Optional[str]) -> Tuple[int, int, List[str], Dict[str, List[str]]]:
    lines: List[str] = []
    violations = 0
    examined = 0
    by_id: Dict[str, List[str]] = {}

    limit_paths: Optional[set] = None
    if since:
        rng = "%s..%s" % (since, refs[0])
        added = git("log", "--diff-filter=A", "--format=", "--name-only", rng, "--",
                    BUILD_LOG_DIR + "/", cwd=root)
        limit_paths = {p for p in added.split("\n") if p.strip()}

    for ref in refs:
        for path in entries_of(root, ref):
            name = os.path.basename(path)
            m = ENTRY_RE.match(name)
            if not m:
                if name.startswith("."):
                    continue
                violations += 1
                lines.append("VIOLATION MALFORMED NAME  %s@%s does not match BL-<utc>-NNNN.yaml" % (path, ref))
                continue
            if limit_paths is not None and path not in limit_paths:
                continue
            examined += 1
            num = int(m.group(1))
            # KEY BY FILENAME, NOT BY (filename, ref). The SAME entry present on two branches is
            # ONE entry — shared ancestry, not a duplicate. Counting it as a collision would report
            # a violation for every commit two branches have in common, which is a false positive
            # of exactly the kind CD-RULE-004 forbids a guard from claiming as its class.
            if name not in by_id.setdefault(m.group(1), []):
                by_id[m.group(1)].append(name)
            author = adding_author(root, ref, path)
            if author is None:
                violations += 1
                lines.append("VIOLATION NO ADDING COMMIT  %s@%s — cannot resolve the git author that added it" % (name, ref))
                continue
            blk = block_for(blocks, author)
            if blk is None:
                violations += 1
                lines.append("VIOLATION UNALLOCATED_AUTHOR  %s@%s added by %r who holds no block"
                             % (name, ref, author))
                continue
            if not (int(blk["first"]) <= num <= int(blk["last"])):
                violations += 1
                lines.append("VIOLATION OUT OF BLOCK  %s@%s id=%04d added by %r whose block is %s [%04d-%04d]"
                             % (name, ref, num, author, blk["id"], blk["first"], blk["last"]))

    for ident, holders in sorted(by_id.items()):
        if len(holders) > 1:
            violations += 1
            lines.append("VIOLATION DUPLICATE ID  %s is used by %d DISTINCT entries: %s"
                         % (ident, len(holders), ", ".join(sorted(holders))))
    return examined, violations, lines, by_id


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None)
    ap.add_argument("--table", action="store_true", help="refuse overlapping ALLOCATIONS")
    ap.add_argument("--entries", action="store_true", help="refuse out-of-block and duplicate ids")
    ap.add_argument("--ref", action="append", default=[], help="git ref to examine (repeatable)")
    ap.add_argument("--since", default=None,
                    help="restrict --entries to entries ADDED after this rev. THE RESTRICTION IS PRINTED.")
    ap.add_argument("--all", action="store_true", help="explicit: examine every entry in the ref(s)")
    args = ap.parse_args(argv)
    root = args.root or repo_root()
    refs = args.ref or ["HEAD"]

    with Limit("tools/coordination/check_build_log_blocks.py", LIMITS, RESIDUE):
        tree_banner(root)
        if not args.table and not args.entries:
            print("VERDICT: NOTHING CHECKED — pass --table and/or --entries")
            return 2
        try:
            blocks = load_blocks(root)
        except RuntimeError as exc:
            print("VERDICT: %s" % exc)
            return 2

        rc = 0
        total_violations = 0

        if args.table:
            v, lines = check_table(blocks)
            for ln in lines:
                print("   %s" % ln)
            say_command("allocated_blocks", len(blocks),
                        "python3 -c \"import yaml;print(len(yaml.safe_load(open('%s'))['blocks']))\"" % BLOCKS_FILE)
            say_command("block_overlap_violations", v,
                        "python3 -B tools/coordination/check_build_log_blocks.py --table")
            total_violations += v

        if args.entries:
            if args.since:
                print("   SCOPE RESTRICTED: only entries ADDED after %r are examined. A clean run "
                      "here says NOTHING about the entries before it." % args.since)
            else:
                print("   SCOPE: EVERY entry in ref(s) %s, including the project's whole history."
                      % refs)
            examined, v, lines, by_id = check_entries(root, blocks, refs, args.since)
            for ln in lines:
                print("   %s" % ln)
            say_command("entries_examined", examined,
                        "git ls-tree --name-only %s governance/engineering/build-log/ | wc -l" % refs[0])
            say_command("distinct_ids", len(by_id),
                        "git ls-tree --name-only %s governance/engineering/build-log/ | "
                        "grep -oE '[0-9]{4}\\.yaml$' | sort -u | wc -l" % refs[0])
            say_command("entry_violations", v,
                        "python3 -B tools/coordination/check_build_log_blocks.py --entries %s"
                        % " ".join("--ref " + r for r in refs))
            total_violations += v

        if total_violations:
            print("VERDICT: REFUSED — %d violation(s)" % total_violations)
            rc = 1
        else:
            print("VERDICT: ADMITTED — no block overlap, no out-of-block entry, no duplicate id")
        return rc


if __name__ == "__main__":
    sys.exit(main())
