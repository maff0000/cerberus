"""Shared plumbing for the register checks. STDLIB ONLY.

Every check in this directory is a STANDALONE script with a stable command line, and every
one of them takes ``--root <subject tree>``. The auditor runs them against a throwaway copy
they extracted themselves — never against the Engineer's worktree — so a check that
hardcoded a path would be a check nobody but its author could run.

THE ONE RULE THIS MODULE EXISTS TO ENFORCE (``PBG-CI-002``)
-----------------------------------------------------------
**No check may skip. For any reason. Ever.**

A precondition that cannot be met is a NON-ZERO exit with a stated reason — never a pass,
and never a skip. A check that skips is a check that detects nothing while reporting
success, which is worse than no check at all, because the register then carries a row
somebody believes.

That rule has a second, less obvious half, and :func:`Check.done` enforces it: a check that
made **no assertions** — because it found no files, or the subject tree was empty, or a
glob matched nothing — must also refuse. Otherwise `exit 0` means "clean" and "I looked at
nothing" indistinguishably, and pointing the check at the wrong directory reads as a pass.

EXIT CODES, stable across every check here:

    0   the subject is clean: assertions were made, and all of them held
    1   VIOLATION: at least one finding, each printed with its file and line
    2   USAGE: the command line was wrong
    3   PRECONDITION NOT MET: the check could not do its job, with the reason stated

Anything other than 0 is a failure. An auditor reading only stdout must be able to tell a
real violation from a broken check, so 1 and 3 are printed differently and say so.
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import sys
from dataclasses import dataclass, field

__all__ = [
    "EXIT_CLEAN",
    "EXIT_VIOLATION",
    "EXIT_USAGE",
    "EXIT_PRECONDITION",
    "Finding",
    "Check",
    "module_level_statements",
    "parse_root",
]


#: The three node types that END module scope. Everything else is descended through.
#: **THIS IS THE ONLY ENUMERATION IN :func:`module_level_statements` AND IT IS THE
#: CLOSED ONE.** See that function's docstring for why it is not a vocabulary.
_SCOPE_ENDING_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def module_level_statements(tree):
    """Every statement at MODULE SCOPE, including inside a module-level block.

    ``for node in tree.body`` — which every enumerator in this directory used to write —
    is **not** "module level". It is "module level and not indented", and the difference
    is a live escape: a name bound inside ``if TYPE_CHECKING:``, ``try:``/``except
    ImportError:``, ``with``, ``for`` or ``while`` at module level is bound in the module
    namespace exactly as a top-level one is, and is invisible to ``tree.body``.

    **MEASURED, NOT ASSUMED (WO-2R3 increment 8, `F-06-K`).** Wrapping
    ``FetchOutcome = Union[OK, FetchFailed, Malformed, Empty]`` in ``if True:`` in
    ``observations.py`` dropped ``FetchFailed``, ``Malformed`` and ``Empty`` out of
    ``check_constructor_field_establishment.py``'s governed class and **converted a real
    FAIL into a PASS** — with ``@establishes`` stripped from ``FetchFailed`` the control
    arm is ``FAIL — 1 violation, EXIT 1`` and the same tree with the ``if True:`` added is
    ``PASS — 91 assertions, EXIT 0``. Both arms run from
    ``tests/test_module_level_traversal.py``.

    **WHY THIS PRUNES RATHER THAN ENUMERATING BLOCK TYPES, WHICH IS THE WHOLE POINT.**
    The obvious repair is ``ast.walk`` (too wide — it descends into function bodies and
    class bodies, which are *not* module scope) or a list of block statements to descend
    into (``if``/``try``/``with``/``for``/``while``) — and that list **is a vocabulary**,
    which is the defect class this project has spent six gates on. A ``match`` statement,
    or whatever the next Python grammar adds, defeats it silently.

    So the rule is inverted and closed: **descend into EVERY node except the three that
    create a new scope.** A statement is at module scope if no ``def``, ``async def`` or
    ``class`` stands between it and the module. That is derived from the language's own
    scoping rule rather than from a list of spellings, and a new block statement type is
    handled on the day it is added with no edit here.

    The scope-ending nodes are THEMSELVES yielded — a ``def`` inside ``if TYPE_CHECKING:``
    binds a module-level name — but their bodies are not descended into.

    Returns statements only (``ast.stmt``), in source order per branch, so every existing
    caller's ``isinstance(node, (ast.Assign, ast.FunctionDef, ...))`` filter keeps its
    exact meaning and only its INPUT widens.
    """
    out: list = []

    def descend(node) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _SCOPE_ENDING_NODES):
                out.append(child)
                continue
            if isinstance(child, ast.stmt):
                out.append(child)
            descend(child)

    descend(tree)
    return out

EXIT_CLEAN = 0
EXIT_VIOLATION = 1
EXIT_USAGE = 2
EXIT_PRECONDITION = 3


@dataclass(frozen=True)
class Finding:
    """One violation, located. ``line`` is 1-indexed; 0 means the whole file."""

    path: pathlib.Path
    line: int
    rule: str
    what: str

    def render(self, root: pathlib.Path) -> str:
        try:
            shown = self.path.relative_to(root)
        except ValueError:
            shown = self.path
        where = f"{shown}:{self.line}" if self.line else f"{shown}"
        return f"VIOLATION  {where}\n    rule: {self.rule}\n    what: {self.what}"


@dataclass
class Check:
    """A register check in progress.

    ``assertions`` counts the propositions actually tested. It is not decoration: it is
    what makes a vacuous run impossible to mistake for a clean one.
    """

    check_id: str
    root: pathlib.Path
    findings: list[Finding] = field(default_factory=list)
    assertions: int = 0
    notes: list[str] = field(default_factory=list)

    # -- reporting -------------------------------------------------------------------- #
    def asserted(self, count: int = 1) -> None:
        self.assertions += count

    def note(self, text: str) -> None:
        """Something the reader should know that is not a violation."""
        self.notes.append(text)

    def violation(self, path: pathlib.Path, line: int, rule: str, what: str) -> None:
        self.findings.append(Finding(pathlib.Path(path), int(line), rule, what))

    def refuse(self, reason: str) -> "int":
        """A precondition could not be met. NON-ZERO, with the reason. Never a skip."""
        print(f"{self.check_id}: PRECONDITION_NOT_MET", file=sys.stderr)
        print(f"    {reason}", file=sys.stderr)
        print(
            "    This is a non-zero exit with a stated reason, never a pass and never a "
            "skip (PBG-CI-002).",
            file=sys.stderr,
        )
        return EXIT_PRECONDITION

    def done(self, subject_summary: str) -> int:
        """Print the verdict and return the exit code."""
        print(f"{self.check_id}")
        print(f"    subject: {self.root}")
        print(f"    scanned: {subject_summary}")
        print(f"    assertions: {self.assertions}")
        for note in self.notes:
            print(f"    note: {note}")

        if self.assertions == 0:
            return self.refuse(
                "the check made ZERO assertions. Nothing was examined, so `clean` would "
                "mean `I looked at nothing`. Check --root points at the subject tree."
            )

        if self.findings:
            print("")
            for finding in self.findings:
                print(finding.render(self.root))
            print("")
            print(f"{self.check_id}: FAIL — {len(self.findings)} violation(s)")
            return EXIT_VIOLATION

        print(f"{self.check_id}: PASS — {self.assertions} assertions, 0 violations")
        return EXIT_CLEAN


def parse_root(check_id: str, description: str, extra=None) -> argparse.Namespace:
    """The stable command line every check shares: ``--root <subject tree>``.

    ``extra`` is a callable taking the parser, for a check that needs one more argument.
    """
    parser = argparse.ArgumentParser(
        prog=check_id,
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--root",
        required=True,
        help=(
            "the SUBJECT TREE to check: the repository root of the tree under audit. "
            "Required, and never defaulted — an auditor runs this against a copy they "
            "extracted themselves."
        ),
    )
    if extra is not None:
        extra(parser)
    return parser.parse_args()


def resolve_root(check: str, raw: str) -> "tuple[pathlib.Path | None, int]":
    """Resolve and validate ``--root``. Returns (path, exit_code); path is None on failure."""
    root = pathlib.Path(raw).expanduser()
    if not root.is_absolute():
        root = (pathlib.Path.cwd() / root).resolve()
    else:
        root = root.resolve()
    if not root.is_dir():
        print(f"{check}: PRECONDITION_NOT_MET", file=sys.stderr)
        print(f"    --root {raw} is not a directory.", file=sys.stderr)
        print(
            "    This is a non-zero exit with a stated reason, never a skip (PBG-CI-002).",
            file=sys.stderr,
        )
        return None, EXIT_PRECONDITION
    return root, EXIT_CLEAN


def read_text(check: Check, path: pathlib.Path) -> "str | None":
    """Read a file, or record the unreadability as a violation rather than passing over it."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        check.violation(
            path,
            0,
            "UNREADABLE",
            f"the check could not read this file ({type(exc).__name__}: {exc}). An "
            "unreadable file inside the scanned set is a failure, not a file to pass over.",
        )
        return None


def python_files(root: pathlib.Path, relative_dirs, relative_files=()) -> list[pathlib.Path]:
    """Every ``*.py`` under the named directories, plus the named files, sorted.

    ``__pycache__`` is excluded because it holds compiled copies of files already scanned,
    not source. Nothing else is excluded: a directory a check declines to look at is a
    directory a violation can be parked in.
    """
    found: list[pathlib.Path] = []
    for relative in relative_dirs:
        base = root / relative
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            found.append(path)
    for relative in relative_files:
        path = root / relative
        if path.is_file():
            found.append(path)
    return sorted(set(found))
