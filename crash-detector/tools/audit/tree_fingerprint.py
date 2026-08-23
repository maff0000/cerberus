#!/usr/bin/env python3
"""CD-PL-F100 — THE TREE FINGERPRINT, AS A GOVERNED INSTRUMENT INSTEAD OF A PASTED SHELL LINE.

    python3 -B tools/audit/tree_fingerprint.py --root <subject tree>

THE DEFECT THIS REPLACES, VERBATIM FROM THE FINDING
---------------------------------------------------
    **"THE FINGERPRINT RECIPE THIS SEAT PUT IN THE DISPATCH INCLUDES GITIGNORED FILES."**

The shipped recipe was ``find . -path ./.git -prune -o -type f -print | ... | sha256sum``. It
sweeps ``.pytest_cache/``, which is created by running ``pytest`` — **which the dispatch
orders the seat to do.** The dispatch then tells the seat that a moved fingerprint means
*"something mutated under you and your verdict is about a tree that no longer exists"*. **SO
THE INSTRUMENT FIRES ITS MAXIMUM-SEVERITY ALARM AT AN AUDITOR FOR OBEYING THE DISPATCH.**

REPRODUCED BY THIS SEAT rather than quoted (CD-RULE-009), in this worktree, one arm apart —
add ONE empty file under ``.pytest_cache/`` and take both recipes again::

    shipped recipe   ef33427d91538500…  ->  80b3dfa6eada2152…   **MOVED. THE FALSE ALARM.**
    this instrument  f659601e65534304…  ->  f659601e65534304…   unmoved
    …and ONE BYTE of TRACKED content    ->  b1bdb3a3838e981c…   **MOVED, as it must.**

**BOTH ARMS, WHICH IS THE WHOLE ACCEPTANCE TEST: a tree carrying an ignored artefact
fingerprints IDENTICALLY to the same tree without it, and a tree with one byte of TRACKED
content changed does not.**

WHY NOT SIMPLY PRUNE ``.pytest_cache``
---------------------------------------
Because that is a NAME, and this project has a test for those. The fifth Assurance seat's
ad-hoc arm added ``-path ./.pytest_cache -prune``; **run pytest with ``-o cache_dir=.other``
and it stops pruning.** MEASURED — see ``THE RENAME TEST`` below. This instrument asks git
what is ignorable, so it does not carry a list of directory names at all.

**AND THE NAME DEPENDENCE THAT REPLACES IT, STATED PLAINLY RATHER THAN CLAIMED AWAY: IT
DEPENDS ON ``.gitignore`` BEING CORRECT.** A wrongly-ignored PRODUCT file is invisible to this
fingerprint. **THAT IS A REAL WEAKENING AND IT IS NOT DRESSED UP.** What this instrument does
about it is the one thing it can: **IT PRINTS EVERY PATH IT EXCLUDED.** An exclusion a reader
can see is an exclusion a reader can challenge; the shipped recipe's inclusion of cache files
was invisible for exactly as long as nobody printed it.

WHAT THIS FIXES THAT THE SHELL ONE-LINER COULD NOT, EACH MEASURED
------------------------------------------------------------------
1. **OUTSIDE A GIT WORKTREE IT PRODUCED A CONFIDENT HASH OF NOTHING.** Measured in ``/tmp``:
   ``git ls-files`` writes ``fatal: not a git repository`` to stderr, the pipeline continues,
   and ``sha256sum`` of empty input yields ``abcfa6a9d4df344d…`` — **a fingerprint that means
   "I looked at nothing", indistinguishable from one that means "the tree is this".** This
   instrument REFUSES (exit 3), which is the same rule ``tools/register/_support.py``'s
   ``Check.done`` already applies: *``exit 0`` must never be able to mean "I looked at
   nothing"*.
2. **A TRACKED FILE DELETED FROM THE WORKTREE WAS SWALLOWED.** Measured: ``xargs`` exits
   **123**, but the pipeline's exit status is the LAST command's, so the one-liner returns 0
   and prints a fingerprint for an inconsistent tree. This instrument REFUSES and names the
   missing paths.
3. **A VACUOUS RUN.** Zero files is a refusal here, not a hash.

WHAT IT DOES **NOT** SEE — DECLARED, MEASURED, AND NOT CLAIMED CLOSED
----------------------------------------------------------------------
* **FILE MODE.** Measured: ``chmod +x PID.md`` leaves the fingerprint **IDENTICAL**
  (``f659601e…`` both sides). A file becoming executable is a real change to a tree and this
  does not see it. **NOT PROVED TO BE CARRIED ANYWHERE.**
* **``.gitignore`` CORRECTNESS**, above. The exclusions are PRINTED, not verified.
* **SYMLINK TARGETS.** Content is read through the link, so a link retargeted outside the tree
  changes the fingerprint while the tree's own bytes did not, and a broken link is refused as
  a missing path. Declared rather than resolved.
* **EMPTY DIRECTORIES**, which git does not track and this therefore cannot see.
* **IT IS A FINGERPRINT OF A WORKING TREE, NOT A GIT IDENTITY.** It says nothing about branch,
  HEAD, staged state or history. ``git rev-parse HEAD`` and ``git status --porcelain`` answer
  those and this does not replace either.

CARRIER (``CD-RULE-006`` — a check reports, a carrier fails)
-------------------------------------------------------------
``tests/test_tree_fingerprint.py``, which asserts BOTH arms of the acceptance test by
constructing them, and asserts each of the three refusals above by triggering it.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import subprocess
import sys

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_PRECONDITION = 3

INSTRUMENT_ID = "CD-TREE-FINGERPRINT"


def _refuse(reason: str) -> int:
    print(f"{INSTRUMENT_ID}: PRECONDITION NOT MET — {reason}", file=sys.stderr)
    return EXIT_PRECONDITION


def _git(root: pathlib.Path, *arguments: str):
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=False,
    )


def tracked_and_untracked(root: pathlib.Path):
    """Every path git considers part of this tree, EXCLUDING what ``.gitignore`` excludes.

    ``--cached`` (tracked) plus ``--others --exclude-standard`` (untracked and NOT ignored).
    **THE EXCLUSION DECISION IS DELEGATED TO GIT AND NOT RE-IMPLEMENTED HERE** — a second
    implementation of ignore semantics would be a second thing to get wrong, and the one that
    matters is the one the repository already declares.
    """
    result = _git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if result.returncode != 0:
        return None, result.stderr.decode("utf-8", "replace").strip()
    names = [part for part in result.stdout.split(b"\0") if part]
    return names, None


def ignored(root: pathlib.Path):
    """What git EXCLUDED. Printed so the ``.gitignore`` dependence is visible, not invisible."""
    result = _git(root, "ls-files", "-z", "--others", "--ignored", "--exclude-standard")
    if result.returncode != 0:
        return []
    return [part for part in result.stdout.split(b"\0") if part]


def fingerprint(root: pathlib.Path, names) -> "tuple[str, list]":
    """The digest, and the paths that could not be read.

    **THE SPELLING IS THE HISTORIC ONE ON PURPOSE.** Each line is
    ``<sha256 of the file's bytes>  ./<path>\\n`` and the digest is the sha256 of those lines
    concatenated, in ``LC_ALL=C`` byte order — byte-for-byte what
    ``… | sed -z 's|^|./|' | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum`` produces, so
    values taken before this instrument existed remain comparable. **A FINGERPRINT INSTRUMENT
    THAT SILENTLY CHANGED THE VALUE WOULD INVALIDATE EVERY RECORDED FIGURE IT WAS BUILT TO
    PROTECT.**
    """
    lines = []
    missing = []
    for name in sorted(names):
        path = root / name.decode("utf-8", "surrogateescape")
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            missing.append(path)
            continue
        lines.append(digest.encode() + b"  ./" + name + b"\n")
    return hashlib.sha256(b"".join(lines)).hexdigest(), missing


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="tree_fingerprint.py",
        description=(
            "The tree fingerprint, git-aware. Replaces the shipped `find`-based recipe, "
            "which included gitignored files and fired a maximum-severity alarm at an "
            "auditor for running pytest (CD-PL-F100)."
        ),
    )
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--show-excluded",
        action="store_true",
        help="print every path .gitignore excluded. ON BY DEFAULT when there are few enough "
        "to read; this forces it.",
    )
    try:
        arguments = parser.parse_args(argv)
    except SystemExit:
        return EXIT_USAGE

    root = pathlib.Path(arguments.root).resolve()
    if not root.is_dir():
        return _refuse(f"{root} is not a directory")

    inside = _git(root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != b"true":
        # **THE FIRST OF THE THREE THINGS THE SHELL ONE-LINER GOT WRONG.** Outside a git
        # worktree it printed sha256 of empty input and exited 0.
        return _refuse(
            f"{root} is not inside a git worktree, so there is no ignore declaration to "
            "delegate to. The shipped shell recipe printed a confident-looking hash of "
            "NOTHING here (abcfa6a9d4df344d…, the sha256 of empty input) and exited 0. "
            "`exit 0` must never be able to mean 'I looked at nothing'."
        )

    names, error = tracked_and_untracked(root)
    if names is None:
        return _refuse(f"git ls-files failed: {error}")
    if not names:
        return _refuse(
            "git listed ZERO files. A fingerprint over an empty set is a valid-looking "
            "digest of nothing, which is the failure mode this instrument exists to refuse."
        )

    digest, missing = fingerprint(root, names)
    if missing:
        # **THE SECOND.** `xargs` exits 123 on a missing file but the pipeline's status is the
        # LAST command's, so the one-liner returned 0 and printed a fingerprint for a tree
        # that does not hold together.
        print(f"{INSTRUMENT_ID}", file=sys.stderr)
        for path in missing:
            print(f"    UNREADABLE: {path}", file=sys.stderr)
        return _refuse(
            f"{len(missing)} path(s) git listed could not be read — most commonly a TRACKED "
            "file deleted from the worktree, or a broken symlink. The tree does not hold "
            "together and a fingerprint of it would describe a state that never existed. "
            "The shipped shell recipe swallowed this and exited 0."
        )

    excluded = ignored(root)
    print(f"{INSTRUMENT_ID}")
    print(f"    subject: {root}")
    print(f"    files fingerprinted: {len(names)}")
    print(f"    EXCLUDED by .gitignore: {len(excluded)}")
    # **THE EXCLUSIONS ARE PRINTED, AND THAT IS THIS INSTRUMENT'S ANSWER TO ITS OWN KNOWN
    # WEAKNESS.** It cannot verify that .gitignore is correct. It can make the consequence of
    # .gitignore being wrong VISIBLE instead of invisible — which is exactly what nobody did
    # for the shipped recipe's inclusion of cache files.
    if excluded and (arguments.show_excluded or len(excluded) <= 40):
        for path in sorted(excluded):
            print(f"      excluded: {path.decode('utf-8', 'replace')}")
    elif excluded:
        print(f"      ({len(excluded)} paths — re-run with --show-excluded to list them)")
    print(
        "    NOTE: this does NOT see file MODE (measured: `chmod +x` leaves it identical), "
        "does not verify that .gitignore is correct, and is a fingerprint of a WORKING TREE "
        "and not a git identity. See this file's header."
    )
    print(f"    FINGERPRINT: {digest}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
