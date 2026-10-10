#!/usr/bin/env python3
"""Shared primitives for the increment-12 coordination discipline.

Nothing in this module makes a coordination decision. It carries the four house obligations that
every instrument in ``tools/coordination/`` owes, in one place, so that no instrument can satisfy
them by remembering to:

* ``CD-RULE-005`` — every governed timestamp comes from ``date -u +%FT%TZ`` **and from nothing
  else**. :func:`utc_now` shells out to that exact command. It does not read the Python clock.
  If ``date`` is unavailable the call RAISES; it does not fall back, because a fallback would be
  the silent substitution the rule exists to forbid.
* ``CD-PL-F36`` — SHAs are RESOLVED, never transcribed. :func:`resolve_sha` runs ``git rev-parse``
  and then ``git cat-file -t`` and refuses anything that is not a commit object.
* ``CD-PL-F98`` — every probe prints the tree it ran in. :func:`tree_banner`.
* ``CD-RULE-004`` / ``CD-D-166`` — every instrument prints its DECLARED LIMIT **after** its
  verdict, **on every exit path**. :class:`Limit` is a context manager whose ``finally`` prints.
  A limit printed before the verdict is a limit nobody reads; a limit printed only on success is
  a limit that vanishes exactly when it matters.

``CD-RULE-009`` — every count or fingerprint records the exact command beside it — is discharged by
the instruments themselves via :func:`say_command`, which prints a paste-able command line next to
the number it produced.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Iterable, List, Optional, Sequence


# ------------------------------------------------------------------------------------------------
# CD-RULE-005 — the only timestamp source on this project
# ------------------------------------------------------------------------------------------------

UTC_COMMAND = ["date", "-u", "+%FT%TZ"]


def utc_now() -> str:
    """Return the governed UTC timestamp, from ``date -u +%FT%TZ`` and from nothing else.

    RAISES rather than falls back. ``CD-RULE-005`` names one source; a second source that only
    appears when the first is missing is a second source.
    """
    out = subprocess.run(UTC_COMMAND, capture_output=True, text=True, check=True)
    stamp = out.stdout.strip()
    if not stamp:
        raise RuntimeError("CD-RULE-005: `date -u +%FT%TZ` produced no output; refusing to invent one")
    return stamp


# ------------------------------------------------------------------------------------------------
# git
# ------------------------------------------------------------------------------------------------

def git(*args: str, cwd: Optional[str] = None, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError("git %s failed rc=%d: %s" % (" ".join(args), proc.returncode, proc.stderr.strip()))
    return proc.stdout


def repo_root(start: Optional[str] = None) -> str:
    return git("rev-parse", "--show-toplevel", cwd=start or os.getcwd()).strip()


def resolve_sha(rev: str, cwd: Optional[str] = None) -> str:
    """``CD-PL-F36``: resolve, then PROVE the object is a commit. Never transcribe."""
    sha = git("rev-parse", rev, cwd=cwd).strip()
    kind = git("cat-file", "-t", sha, cwd=cwd).strip()
    if kind != "commit":
        raise RuntimeError("CD-PL-F36: %s resolved to %s which is a %s, not a commit" % (rev, sha, kind))
    return sha


def current_branch(cwd: Optional[str] = None) -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd).strip()


# ------------------------------------------------------------------------------------------------
# CD-PL-F98 — every probe prints the tree it ran in
# ------------------------------------------------------------------------------------------------

def tree_banner(cwd: Optional[str] = None, stream=sys.stdout) -> None:
    cwd = cwd or os.getcwd()
    try:
        root = repo_root(cwd)
        sha = git("rev-parse", "HEAD", cwd=cwd).strip()
        branch = current_branch(cwd)
    except Exception as exc:  # not in a repository at all — say so rather than print nothing
        print("[TREE] not a git worktree (%s): cwd=%s" % (exc, cwd), file=stream)
        return
    print("[TREE] worktree=%s branch=%s head=%s cwd=%s" % (root, branch, sha, cwd), file=stream)
    print("[TREE]   command: git rev-parse --show-toplevel; git rev-parse --abbrev-ref HEAD; git rev-parse HEAD",
          file=stream)


# ------------------------------------------------------------------------------------------------
# CD-RULE-009 — a number without its producing command is not evidence
# ------------------------------------------------------------------------------------------------

def say_command(label: str, value, command: str, stream=sys.stdout) -> None:
    print("%s = %s" % (label, value), file=stream)
    print("    produced by: %s" % command, file=stream)


# ------------------------------------------------------------------------------------------------
# CD-RULE-004 / CD-D-166 — the declared limit, AFTER the verdict, on EVERY exit path
# ------------------------------------------------------------------------------------------------

class Limit:
    """Print an instrument's DECLARED LIMIT from a ``finally``, after the verdict, always.

    Usage::

        with Limit("check_x.py", ["what it does not decide", ...]):
            ... compute and PRINT THE VERDICT ...

    The limit text is printed on normal return, on ``SystemExit`` (including ``sys.exit(1)``) and
    on an uncaught exception. That is the whole point: ``CD-D-166`` is on this project's record
    because a limit printed before a verdict is a limit nobody reads, and a limit printed only on
    success is a limit that vanishes exactly when it matters.
    """

    def __init__(self, instrument: str, limits: Sequence[str], residue: Optional[str] = None,
                 stream=sys.stdout):
        self.instrument = instrument
        self.limits = list(limits)
        self.residue = residue
        self.stream = stream

    def __enter__(self) -> "Limit":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        s = self.stream
        print("", file=s)
        print("-- DECLARED LIMIT (CD-RULE-004 option 2) -- %s" % self.instrument, file=s)
        print("   This instrument does NOT close its class. It decides exactly what is listed", file=s)
        print("   below and REFUSES (fails closed) or DECLINES anything else. DO NOT READ A CLEAN", file=s)
        print("   RUN AS PROOF OF THE PROPOSITION BEYOND THESE BOUNDS.", file=s)
        for i, item in enumerate(self.limits, 1):
            print("   L%d. %s" % (i, item), file=s)
        if self.residue:
            print("   RESIDUE (CD-RULE-006): %s" % self.residue, file=s)
        print("-- end declared limit --", file=s)
        s.flush()
        return False


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def lines_of(text: str) -> List[str]:
    return text.splitlines()


def uniq(seq: Iterable[str]) -> List[str]:
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out
