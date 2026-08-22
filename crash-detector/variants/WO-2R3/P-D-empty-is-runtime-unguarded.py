"""PROBE D — F-A1: IS `Empty` REFUSED AT RUNTIME WHEN IT GAINS A FIELD, OR ONLY IN PRINT?

Run from the ROOT of a tree:  ``python3 -B variants/WO-2R3/P-D-empty-is-runtime-unguarded.py``

**NO VERDICT IS PRINTED.** Read the DATA lines (F-C1).

WHAT IT ASKS. `PO-DECISIONS-0010` ruling 1 says a fielded public frozen judgement-path type
with no establishment **"FAILS ON ARRIVAL"**, and in this module's own vocabulary that means
**RAISES ON EVERY CONSTRUCTION**. `CD-ASR-WO2R3-01`'s F-A1 measured that for `Empty` — the ONE
member the CD-D-134 widening added to the population — it is **a static check line only**:
adding a field makes the instrument exit 1, and the interpreter accepts the type anyway.

WHY THIS IS A SCRIPT AND NOT A `.patch`. Every arm needs `Empty` to GAIN A FIELD, and
`observations.py` is edited by this very increment. A patch cut at `531c95c` would fail
`git apply` on context drift at the increment-6 tree — `T7` records four corpus patches that
did exactly that — and an arm that cannot be applied at both SHAs cannot be a contrast. This
script performs the same edit BY LOCATING THE CLASS IN THE AST, so it applies at any SHA where
`Empty` exists, and it prints the edited source line so a reader can see what it did.

**IT MUTATES NOTHING.** The tree is copied to a temporary directory; the edit and every run
happen there; the copy is removed.

THE FOUR ARMS:

  0 baseline, no edit   — is `Empty` an establishing type at all? does `Empty()` still work?
  1 static, no edit     — the constructor instrument on the unedited tree.
  2 static, +one field  — the instrument on the edited tree. F-A1 says this exits 1 at BOTH
                          SHAs, so **THIS ARM IS NOT THE PROOF AND IS PRINTED TO SHOW IT.**
  3 RUNTIME, +one field — **THE PROOF.** `Empty()` and `Empty(confidence=object())` in a fresh
                          interpreter against the edited tree.

WHAT IT DOES NOT REACH: it measures ONE type and ONE way of adding ONE field. It says nothing
about any other member of the population, and nothing about whether `@establishes()` is
applied everywhere it should be — that is the constructor instrument's job and this probe does
not duplicate it.
"""

from __future__ import annotations

import ast
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIELD_LINE = "    confidence: object = None"


def _copy_tree(destination: pathlib.Path) -> None:
    shutil.copytree(
        ROOT,
        destination,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        symlinks=True,
    )


def _give_empty_a_field(tree_root: pathlib.Path) -> str:
    """Insert one defaulted field into `Empty`, located by the AST and not by context.

    A DEFAULTED field on purpose: it leaves `Empty()` spellable, so arm 3 can ask about the
    construction that succeeds today as well as the new one. A required field would refuse
    `Empty()` with a plain `TypeError` from the generated `__init__` and tell us nothing
    about establishment.
    """
    source_path = tree_root / "src" / "crash_detector" / "observations.py"
    lines = source_path.read_text().splitlines()
    module = ast.parse("\n".join(lines))
    target = next(
        node
        for node in ast.walk(module)
        if isinstance(node, ast.ClassDef) and node.name == "Empty"
    )
    # `body[0]` is the docstring expression; insert after whatever the first statement is, so
    # the field lands inside the class body whether or not there is a docstring.
    insert_after = target.body[0].end_lineno
    lines.insert(insert_after, FIELD_LINE)
    source_path.write_text("\n".join(lines) + "\n")
    return f"{source_path.relative_to(tree_root)}:{insert_after + 1}: {FIELD_LINE.strip()}"


def _run(tree_root: pathlib.Path, *argv: str) -> tuple[int, str]:
    done = subprocess.run(
        [sys.executable, "-B", *argv],
        cwd=tree_root,
        capture_output=True,
        text=True,
    )
    return done.returncode, (done.stdout + done.stderr)


_RUNTIME_ARM = r"""
import sys
sys.path.insert(0, "src")
from crash_detector.observations import Empty
from crash_detector.establishment import is_establishing_type

print("    is_establishing_type(Empty) :", is_establishing_type(Empty))
for spelling, call in (
    ("Empty()", lambda: Empty()),
    ("Empty(confidence=object())", lambda: Empty(confidence=object())),
):
    try:
        call()
    except Exception as exc:
        print(f"    {spelling:<28}: REFUSED {type(exc).__name__}: {str(exc)[:180]}")
    else:
        print(f"    {spelling:<28}: ***ACCEPTED***")
"""


def main() -> int:
    print("PROBE D — F-A1: IS `Empty` REFUSED AT RUNTIME, OR ONLY IN PRINT?")
    print(f"tree: {ROOT}")
    print("NO VERDICT IS PRINTED. READ THE DATA LINES.")
    print()

    checker = "tools/register/check_constructor_field_establishment.py"

    with tempfile.TemporaryDirectory() as scratch:
        clean = pathlib.Path(scratch) / "clean"
        _copy_tree(clean)

        print("--- arm 0: BASELINE, no edit — is Empty an establishing type at all?")
        code, out = _run(clean, "-c", _RUNTIME_ARM)
        print(out.rstrip())
        print()

        print("--- arm 1: STATIC, no edit")
        code, out = _run(clean, checker, "--root", ".")
        headline = [line for line in out.splitlines() if "CD-RT-002-CONSTRUCTORS" in line]
        print(f"    exit={code}  {headline[-1].strip() if headline else out.strip()[:200]}")
        print()

        edited = pathlib.Path(scratch) / "edited"
        _copy_tree(edited)
        where = _give_empty_a_field(edited)
        print(f"--- the edit, applied for real: {where}")
        print()

        print("--- arm 2: STATIC, +one field on Empty "
              "(**NOT THE PROOF — F-A1 says this exits 1 at both SHAs**)")
        code, out = _run(edited, checker, "--root", ".")
        for line in out.splitlines():
            if "CD-RT-002-CONSTRUCTORS" in line or "VIOLATION" in line.upper():
                print(f"    {line.strip()[:220]}")
        print(f"    exit={code}")
        print()

        print("--- arm 3: RUNTIME, +one field on Empty  **THIS IS THE PROOF**")
        code, out = _run(edited, "-c", _RUNTIME_ARM)
        print(out.rstrip())
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
