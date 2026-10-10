#!/usr/bin/env python3
"""THE BOUNDARY GOVERNANCE-CITATION MEASUREMENT — ordered by ``PO-DECISIONS-0016`` ruling 1(b).

The ruling, verbatim:

    *"(b) the boundary reconciliation gains a MEASUREMENT: every governance document cited by
    lane files exists on main at the boundary SHA — counted and asserted; the 29-vs-34 file
    count discrepancy resolved by instrument, not smoothed."*

WHY THIS FILE EXISTS AT ALL
---------------------------
``F-06-B`` (sixth Assurance seat, HIGH) measured that **the audit target does not contain its own
governing authority**: main's ``BLUEPRINT.md`` commit is not an ancestor of the lane, and the lane
cites design constraints — ``CD-BP-003`` most of all — from shipped product source, from the doors
instrument whose green row was that audit's subject, and from ``required-tests.yaml``.

``PO-DECISIONS-0016`` ruling 1(a) answered the *reader* half of that finding with a header on the
lane's ``BLUEPRINT.md``. **A HEADER IS A SENTENCE AND A SENTENCE IS NOT A CONTROL.** Ruling 1(b) is
the other half: the sentence *"every governance citation in this lane resolves against `main` at
the reconciliation boundary"* is a CLAIM, and this file is the thing that makes it a MEASUREMENT.
Without it, the header is exactly what this project's whole record is about — a declaration
standing in for a guard.

WHAT IT ASSERTS
---------------
For a lane SHA and a main SHA, **every governance citation appearing in a lane file RESOLVES
against main at that SHA.** Two citation forms, both extracted mechanically:

* **PATH form** — a repository path naming a governance document (``governance/...``,
  ``BLUEPRINT.md``, ``PID.md``, ``pbg/...``). It RESOLVES when that exact path exists in main's
  tree at the main SHA, proved with ``git cat-file -e <sha>:<path>``.
* **IDENTIFIER form** — a governed identifier (``CD-BP-003``, ``BP-AMENDMENT-0001``,
  ``PO-DECISIONS-0016``, ``CD-D-166``, ``CD-RULE-007``, ``PBG-SOD-001`` and their families). It
  RESOLVES when the identifier occurs at least once inside main's **authority surface** at the
  main SHA — ``governance/``, ``BLUEPRINT.md``, ``PID.md``, ``pbg/`` — proved with ``git grep``.

An unresolved citation is a violation and the instrument exits 1, naming the citing file, the line
and the citation. **A LANE FILE MAY NOT CITE AN AUTHORITY THAT MAIN DOES NOT CARRY.**

WHAT "RESOLVES" DELIBERATELY DOES **NOT** MEAN — READ THIS BEFORE CREDITING A GREEN RUN
---------------------------------------------------------------------------------------
Resolution here is **EXISTENCE, NOT AGREEMENT.** It proves main carries a document, or a document
that mentions the identifier. **IT DOES NOT PROVE THE LANE'S USE OF THE CITATION MATCHES WHAT MAIN
SAYS.** A lane file citing ``CD-BP-003`` for a proposition ``CD-BP-003`` does not contain passes
this instrument. That residue is **NOT PROVED TO BE CARRIED ANYWHERE** (``CD-RULE-006``): no
instrument on this project reads a citation for meaning, and this one does not become the first by
being read hopefully. It closes the *absence* class and declares the *semantics* class open.

THE 29-vs-34 DISCREPANCY, AND HOW IT IS RESOLVED
------------------------------------------------
``F-06-B`` reported ``BP-AMENDMENT-0001 : 96 times across 34 files`` and ``CD-BP-003 : 86 times
across 23 files``, "excluding BLUEPRINT.md and governance/". The Project Lead measured 29 files on
its own exclusion set and the two numbers have sat beside each other in the record ever since.

**THIS INSTRUMENT DOES NOT PICK A WINNER. IT PRINTS THE ARITHMETIC** — see ``--discrepancy``. For
each named identifier it reports the count under THIS instrument's exclusion set, the count under
NO exclusion, and the delta to the figure ``F-06-B`` published, with the producing command beside
every number (``CD-RULE-009``). Where the published figure cannot be reproduced under any
exclusion set this instrument can construct, **IT SAYS SO IN THOSE WORDS RATHER THAN CONSTRUCTING
A METHOD THAT ARRIVES AT IT.** A count that cannot be recomputed is exactly what ``CD-RULE-009``
exists to stop being cited as evidence, and that rule binds Assurance seats too.

DECLARED LIMITS — ``CD-RULE-004`` OPTION 2, MEASURED AND NOT ESTIMATED
----------------------------------------------------------------------
1. **IT SEES TRACKED FILES ONLY.** ``git ls-tree`` at the lane SHA. An untracked file in a lane
   worktree citing a dead authority is invisible here. Measured: at ``05ddaa3`` the lane worktree's
   ``git status --porcelain`` is ZERO lines, so at that SHA the limit costs nothing — **and it is
   a limit anyway, because the next boundary's porcelain is not this one's.**
2. **IT MATCHES TEXT, NOT SYNTAX.** A citation inside a comment, a docstring, a string literal and
   a filename are indistinguishable to it. This is deliberate — ``F-06-B``'s subject is prose
   citations in product source — but it means a citation constructed at runtime
   (``"CD-BP-" + "003"``) is invisible. Concrete, executable: put ``"CD-D-" + "999"`` in a lane
   file and this instrument reports nothing.
3. **IDENTIFIER RESOLUTION IS OCCURRENCE, NOT DEFINITION.** ``CD-D-166`` resolves if any governed
   file on main contains that string — including a file that merely mentions it in passing. There
   is no register of defined identifiers on this project to check against. **A REGISTER WOULD BE
   THE STRONGER CONTROL AND IT DOES NOT EXIST; THIS IS THE WEAKER ONE, NAMED.**
4. **THE PATTERN SET IS ENUMERATED AND IS NOT CLAIMED EXHAUSTIVE.** It is printed at every run.
   An identifier family nobody has coined yet is not matched. **DO NOT READ A CLEAN RUN AS PROOF
   THAT THE LANE CITES NOTHING ELSE.**
5. **IT CANNOT SEE A CITATION THAT IS CORRECT AND STALE.** See "existence, not agreement" above.

TO SEE IT FAIL — the counterfactual arm (``CD-D-079``), executable in one command::

    d=$(mktemp -d) && git archive <lane-sha> | tar -x -C "$d" \\
      && echo 'see governance/decisions/PO-DECISIONS-9999.md and CD-D-999' > "$d/DEAD.md" \\
      && python3 -B tools/reconciliation/check_lane_governance_citations.py \\
           --lane-tree "$d" --main-sha <main-sha>

It exits 1 and names ``DEAD.md``, the line, and both unresolved citations.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict

# --------------------------------------------------------------------------------------------- #
# THE EXCLUSION SET. PRINTED AT EVERY RUN, BECAUSE AN UNPRINTED EXCLUSION SET IS THE WHOLE REASON
# THE 29-vs-34 DISCREPANCY EXISTS.
# --------------------------------------------------------------------------------------------- #
EXCLUDED_PREFIXES = (
    "governance/",   # the lane's OWN governance record. Its build-log block (0060-0099) is the
                     # Engineer seats' and is not what F-06-B is about.
    "pbg/",          # the pinned framework. Read-only to every seat; not lane-authored text.
)
EXCLUDED_EXACT = (
    "BLUEPRINT.md",  # the lane's historical baseline. It is the SUBJECT of ruling 1, not evidence
                     # for it. (At the lane tip it carries the PO-authored header of ruling 1(a).)
)

# --------------------------------------------------------------------------------------------- #
# THE CITATION PATTERNS. ENUMERATED, PRINTED, AND NOT CLAIMED EXHAUSTIVE (DECLARED LIMIT 4).
# --------------------------------------------------------------------------------------------- #
PATH_PATTERNS = (
    ("governance path", re.compile(r"governance/[A-Za-z0-9._/-]+\.(?:md|yaml|yml)")),
    ("pbg path", re.compile(r"pbg/[A-Za-z0-9._/-]+\.(?:md|yaml|yml)")),
    ("root document", re.compile(r"\b(?:BLUEPRINT|PID)\.md\b")),
)
IDENT_PATTERNS = (
    ("blueprint amendment", re.compile(r"\bBP-AMENDMENT-\d{4}\b")),
    ("product owner decision", re.compile(r"\bPO-[A-Z]+(?:-[A-Z0-9]+)*-\d{4}\b")),
    ("blueprint criterion", re.compile(r"\bCD-BP-\d{3}\b")),
    ("acceptance criterion", re.compile(r"\bCD-AC-\d{3}\b")),
    ("project decision", re.compile(r"\bCD-D-\d{3}\b")),
    ("project rule", re.compile(r"\bCD-RULE-\d{3}\b")),
    ("authority record", re.compile(r"\bCD-AUTH-\d{4}\b")),
    ("framework control", re.compile(r"\bPBG-[A-Z]+-\d{3}\b")),
)

# main's AUTHORITY SURFACE — where an identifier must occur for the citation to resolve.
AUTHORITY_SURFACE = ("governance", "BLUEPRINT.md", "PID.md", "pbg")

# --------------------------------------------------------------------------------------------- #
# THE SECOND RESOLUTION CLASS — CD-D-132, AND IT IS NOT AN EXCLUSION.
#
# CD-D-132 SPLITS THE BUILD-LOG SEQUENCE BLOCKS ON PURPOSE: main holds 0100-0199, the WO-2R3 lane
# holds 0060-0099, and 0001-0059 is shared history closed to both parties. A lane file citing a
# lane build-log entry is therefore citing something main CORRECTLY does not carry, and reporting
# that as a violation would train a reader to ignore this instrument's output — which is worse than
# not having it.
#
# **SO THE ENTRY IS STILL ASSERTED, JUST AGAINST THE LANE, AND THE CLASS IS COUNTED SEPARATELY AND
# PRINTED SEPARATELY. IT IS NEVER FOLDED INTO THE MAIN COUNT.** An entry in the lane's block that
# does not exist ON THE LANE either is a violation exactly as before. This is a second assertion,
# not a hole: the one thing it must not become is a place to put a citation that is failing.
# --------------------------------------------------------------------------------------------- #
LANE_SEQUENCE_BLOCK = (60, 99)
BUILD_LOG_PREFIX = "governance/engineering/build-log/"
BUILD_LOG_SEQ = re.compile(r"^governance/engineering/build-log/BL-\d{8}T\d{6}Z-(\d{4})\.yaml$")


def in_lane_sequence_block(path):
    m = BUILD_LOG_SEQ.match(path)
    if not m:
        return False
    lo, hi = LANE_SEQUENCE_BLOCK
    return lo <= int(m.group(1)) <= hi

# The figures F-06-B published, carried here so the delta is arithmetic and not memory.
# Source: governance/assurance/WO-2R3/VERDICT-SIXTH-SEAT.md, F-06-B, measured by that seat at
# af2accb and published WITHOUT its producing command.
F_06_B_PUBLISHED = {
    "BP-AMENDMENT-0001": (34, 96),
    "CD-BP-003": (23, 86),
}


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", repo, *args], capture_output=True, text=True, check=False
    )


def resolve_sha(repo, rev):
    r = git(repo, "rev-parse", rev)
    if r.returncode != 0:
        sys.exit(f"FATAL: cannot resolve {rev!r} in {repo}: {r.stderr.strip()}")
    sha = r.stdout.strip()
    t = git(repo, "cat-file", "-t", sha)
    if t.stdout.strip() != "commit":
        sys.exit(f"FATAL: {rev!r} -> {sha} is a {t.stdout.strip()!r}, not a commit")
    return sha


def is_excluded(path):
    return path.startswith(EXCLUDED_PREFIXES) or path in EXCLUDED_EXACT


def lane_files(repo, sha, tree_dir):
    """The lane's population. From git at a SHA, or from a directory for the counterfactual arm."""
    if tree_dir:
        out = []
        for root, dirs, names in os.walk(tree_dir):
            dirs[:] = [d for d in dirs if d != ".git"]
            for n in names:
                rel = os.path.relpath(os.path.join(root, n), tree_dir)
                out.append(rel.replace(os.sep, "/"))
        return sorted(out)
    r = git(repo, "ls-tree", "-r", "--name-only", sha)
    return sorted(p for p in r.stdout.splitlines() if p)


def read_file(repo, sha, path, tree_dir):
    if tree_dir:
        try:
            with open(os.path.join(tree_dir, path), "rb") as fh:
                return fh.read().decode("utf-8", "replace")
        except OSError:
            return None
    r = git(repo, "show", f"{sha}:{path}")
    if r.returncode != 0:
        return None
    return r.stdout


def path_exists_on_main(repo, main_sha, path, cache):
    if path not in cache:
        cache[path] = git(repo, "cat-file", "-e", f"{main_sha}:{path}").returncode == 0
    return cache[path]


def ident_on_main(repo, main_sha, ident, cache):
    if ident not in cache:
        r = git(repo, "grep", "-l", "-F", ident, main_sha, "--", *AUTHORITY_SURFACE)
        cache[ident] = bool(r.stdout.strip())
    return cache[ident]


def count_identifier(repo, sha, ident, excluded):
    """Files and occurrences for one identifier at one SHA. Returns (files, occurrences, paths)."""
    r = git(repo, "grep", "-o", "-F", ident, sha, "--", ".")
    paths, occ = defaultdict(int), 0
    for line in r.stdout.splitlines():
        if not line:
            continue
        rest = line[len(sha) + 1:] if line.startswith(sha + ":") else line
        p = rest.split(":", 1)[0]
        if excluded and is_excluded(p):
            continue
        paths[p] += 1
        occ += 1
    return len(paths), occ, sorted(paths)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".", help="repository root holding BOTH refs")
    ap.add_argument("--lane-sha", default="wo-2r3", help="lane ref or SHA")
    ap.add_argument("--main-sha", default="main", help="main ref or SHA — the BOUNDARY SHA")
    ap.add_argument("--lane-tree", default=None,
                    help="read the lane population from this DIRECTORY instead of git "
                         "(the counterfactual arm; see the module docstring)")
    ap.add_argument("--discrepancy", action="store_true",
                    help="print the 29-vs-34 arithmetic block")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    main_sha = resolve_sha(repo, args.main_sha)
    lane_sha = None if args.lane_tree else resolve_sha(repo, args.lane_sha)

    print("CD-LANE-CITATIONS — every governance citation in the lane resolves against main")
    print("=" * 96)
    print("  ORDERED BY : PO-DECISIONS-0016 ruling 1(b)")
    print(f"  REPO       : {repo}")
    print(f"  LANE       : {args.lane_tree or f'{args.lane_sha} -> {lane_sha}'}")
    print(f"  MAIN (BOUNDARY SHA) : {args.main_sha} -> {main_sha}")
    print()
    print("  EXCLUSION SET (printed because an unprinted one is what caused 29-vs-34):")
    for p in EXCLUDED_PREFIXES:
        print(f"    prefix : {p}")
    for p in EXCLUDED_EXACT:
        print(f"    exact  : {p}")
    print()
    print("  CITATION PATTERNS — enumerated, NOT claimed exhaustive (DECLARED LIMIT 4):")
    for label, rx in PATH_PATTERNS + IDENT_PATTERNS:
        print(f"    {label:24s} {rx.pattern}")
    print()
    print("  RESOLUTION means EXISTENCE ON MAIN, NEVER AGREEMENT WITH MAIN. See DECLARED LIMITS.")
    print("=" * 96)

    files = lane_files(repo, lane_sha, args.lane_tree)
    scanned, skipped = [], []
    for p in files:
        (skipped if is_excluded(p) else scanned).append(p)

    path_cache, ident_cache = {}, {}
    citations = defaultdict(list)      # citation -> [(file, lineno)]
    kinds = {}                         # citation -> "path" | "ident"
    unreadable = []

    for path in scanned:
        text = read_file(repo, lane_sha, path, args.lane_tree)
        if text is None:
            unreadable.append(path)
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for _, rx in PATH_PATTERNS:
                for m in rx.findall(line):
                    citations[m].append((path, lineno))
                    kinds[m] = "path"
            for _, rx in IDENT_PATTERNS:
                for m in rx.findall(line):
                    citations[m].append((path, lineno))
                    kinds[m] = "ident"

    resolved, on_lane, unresolved = [], [], []
    for cit in sorted(citations):
        if kinds[cit] == "path" and in_lane_sequence_block(cit):
            # CD-D-132's second resolution class. STILL ASSERTED — against the lane.
            if lane_sha is None:
                ok = args.lane_tree and os.path.exists(os.path.join(args.lane_tree, cit))
            else:
                ok = git(repo, "cat-file", "-e", f"{lane_sha}:{cit}").returncode == 0
            (on_lane if ok else unresolved).append(cit)
            continue
        if kinds[cit] == "path":
            ok = path_exists_on_main(repo, main_sha, cit, path_cache)
        else:
            ok = ident_on_main(repo, main_sha, cit, ident_cache)
        (resolved if ok else unresolved).append(cit)

    occurrences = sum(len(v) for v in citations.values())
    citing_files = {f for sites in citations.values() for f, _ in sites}

    print()
    print("POPULATION")
    print(f"  lane files at this SHA           : {len(files)}")
    print(f"  EXCLUDED by the set above        : {len(skipped)}")
    print(f"  SCANNED                          : {len(scanned)}")
    print(f"  of those, CITING at least once   : {len(citing_files)}")
    if unreadable:
        print(f"  UNREADABLE (reported, not skipped silently) : {len(unreadable)}")
        for p in unreadable:
            print(f"    ! {p}")
    print()
    print("CITATIONS")
    print(f"  DISTINCT citations               : {len(citations)}")
    print(f"    of which PATH form             : {sum(1 for c in citations if kinds[c] == 'path')}")
    print(f"    of which IDENTIFIER form       : {sum(1 for c in citations if kinds[c] == 'ident')}")
    print(f"  TOTAL OCCURRENCES                : {occurrences}")
    print(f"  RESOLVED against main@{main_sha[:7]}   : {len(resolved)}")
    print(f"  RESOLVED ON THE LANE (CD-D-132)  : {len(on_lane)}   "
          f"<- counted SEPARATELY, never folded into the line above")
    for cit in on_lane:
        print(f"      lane build-log block {LANE_SEQUENCE_BLOCK[0]:04d}-{LANE_SEQUENCE_BLOCK[1]:04d}"
              f" : {cit}")
    print(f"  UNRESOLVED                       : {len(unresolved)}")

    if args.discrepancy:
        print()
        print("THE 29-vs-34 DISCREPANCY — ARITHMETIC, NOT ADJUDICATION")
        print("-" * 96)
        print("  F-06-B published its counts WITHOUT a producing command. CD-RULE-009 says a")
        print("  fingerprint with no command is not evidence — AND THAT RULE BINDS ASSURANCE SEATS.")
        print("  Both readings below carry theirs.")
        print()
        for ident, (pub_files, pub_occ) in sorted(F_06_B_PUBLISHED.items()):
            if lane_sha is None:
                print(f"  {ident}: SKIPPED — --lane-tree has no SHA to count at.")
                continue
            ef, eo, _ = count_identifier(repo, lane_sha, ident, excluded=True)
            af, ao, _ = count_identifier(repo, lane_sha, ident, excluded=False)
            print(f"  {ident}")
            print(f"    THIS INSTRUMENT, exclusion set applied : {ef} files, {eo} occurrences")
            print(f"      git grep -o -F {ident} {lane_sha[:7]} -- .   (then the exclusion set)")
            print(f"    NO EXCLUSION AT ALL                    : {af} files, {ao} occurrences")
            print(f"      git grep -o -F {ident} {lane_sha[:7]} -- .")
            print(f"    F-06-B PUBLISHED                       : {pub_files} files, "
                  f"{pub_occ} occurrences   (no command published)")
            if pub_files in (ef, af):
                print("    -> REPRODUCED.")
            elif ef < pub_files < af:
                print(f"    -> NOT REPRODUCED. The published figure lies BETWEEN this")
                print(f"       instrument's two readings ({ef} < {pub_files} < {af}), so it was")
                print(f"       taken under a PARTIAL exclusion of {af - pub_files} file(s) that")
                print("       no exclusion set stated in that verdict describes.")
                print("       RECORDED AS UNRESOLVED-BY-RECONSTRUCTION AND NOT SMOOTHED.")
            else:
                print(f"    -> NOT REPRODUCED and NOT bracketed by this instrument's readings.")
                print("       RECORDED AS UNRESOLVED-BY-RECONSTRUCTION AND NOT SMOOTHED.")
            print()
        print("  WHAT IS RESOLVED: from this boundary forward there is ONE number per identifier,")
        print("  produced by ONE printed command, at a NAMED SHA. WHAT IS NOT: F-06-B's own two")
        print("  figures remain unreproducible, and that is a finding about the verdict, not a")
        print("  reason to prefer either number.")
        print("-" * 96)

    if unresolved:
        print()
        print("VIOLATIONS — a lane file cites an authority main does not carry at the boundary SHA")
        print("-" * 96)
        for cit in unresolved:
            sites = citations[cit]
            print(f"  UNRESOLVED {kinds[cit].upper():6s} {cit}   ({len(sites)} occurrence(s))")
            for f, ln in sites[:12]:
                print(f"      {f}:{ln}")
            if len(sites) > 12:
                print(f"      ... and {len(sites) - 12} more")
        print("-" * 96)
        print(f"CD-LANE-CITATIONS: FAIL — {len(citations)} citations, {len(unresolved)} unresolved")
        return 1

    print()
    print(f"CD-LANE-CITATIONS: PASS — {len(citations)} distinct citations, {occurrences} "
          f"occurrences, {len(unresolved)} unresolved")
    print("  READ THE DECLARED LIMITS BEFORE CREDITING THIS. It proves main CARRIES each cited")
    print("  authority. It does NOT prove the lane uses any of them the way main defines them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
