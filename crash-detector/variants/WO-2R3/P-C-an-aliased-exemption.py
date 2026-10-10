"""PROBE C — WHO SEES A DOOR-PARAMETER `ESTABLISHED_HERE` ADDED UNDER A ONE-WORD ALIAS?

Run from the ROOT of a tree:  ``python3 -B variants/WO-2R3/P-C-an-aliased-exemption.py``

**NO VERDICT IS PRINTED.** Read the DATA lines (F-C1).

THE CLAIM UNDER TEST, `src/crash_detector/admission.py` DECLARED LIMIT 1, verbatim:

    **`ESTABLISHED_HERE` IS AN EXPLICIT WEAKENING AND IT IS COUNTED, NOT HIDDEN.**

`CD-ASR-WO2R3-01` §2.4 measured that as FALSE under a one-word alias. It added one door in
`collectors/validation.py` importing `ESTABLISHED_HERE as _EH` and observed::

    doors check: still reports 16 exemptions,  EXIT=0     <- invisible
    tests/test_judgement_path_doors.py: 22 passed        <- invisible to the door-side carrier

and then narrowed its own claim, carefully: *"For a door parameter exemption I found no carrier
that sees it. (The addendum reports pytest catching the alias; that is the FIELD-exemption
carrier in `test_field_establishment.py`, a different mechanism. I am narrowing the claim to
what I measured, not widening it.)"*

**THE QUESTION THE AUDITOR LEFT OPEN IS THE ONE THE INCREMENT-6 DISPATCH ORDERS ANSWERED:**
*"IS THERE A CARRIER THAT SEES A DOOR-PARAMETER EXEMPTION ADDED UNDER AN ALIAS? ... Name a
carrier MEASURED — a test that goes RED when a seventeenth aliased use arrives — or write the
words NOT PROVED TO BE CARRIED ANYWHERE."*

So this probe adds the aliased use for real and runs **FOUR** readers, not one:

  1 the doors check                      — a STATIC reader of the source
  2 tests/test_judgement_path_doors.py   — the door-side carrier the auditor ran
  3 tests/test_admission.py              — **THE ONE THE AUDITOR DID NOT RUN.** It enumerates
                                            exemptions from the RUNTIME compiled declaration
                                            objects, not from the source text, so an alias
                                            cannot change what it sees
  4 the whole suite                      — so no reader is missed by this probe's own choice
                                            of readers, which is the mistake being corrected

**IT MUTATES NOTHING.** The tree is copied to a temporary directory and removed after.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]

#: The aliased door, appended to `collectors/validation.py` — the auditor's own file and its
#: own one-word alias. `local_refs_only` already lives there with an unaliased exemption, so
#: this varies EXACTLY ONE THING: the spelling of the name.
ALIASED_DOOR = '''

from crash_detector.admission import ESTABLISHED_HERE as _EH


@admits(candidate=_EH("a seventeenth exemption, spelled through a one-word import alias"))
def aliased_probe_door(candidate):
    """A door whose exemption is spelled `_EH` and not `ESTABLISHED_HERE`."""
    return candidate
'''


def _run(tree: pathlib.Path, *argv: str) -> tuple[int, str]:
    done = subprocess.run(
        [sys.executable, "-B", *argv],
        cwd=tree,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin", "HOME": str(tree)},
    )
    return done.returncode, done.stdout + done.stderr


def _uses_line(output: str) -> str:
    for line in output.splitlines():
        if "ESTABLISHED_HERE uses:" in line:
            return line.strip()
    return "<no ESTABLISHED_HERE uses line found>"


def _tail(output: str, keep: int = 1) -> str:
    lines = [line for line in output.splitlines() if line.strip()]
    return " | ".join(lines[-keep:]) if lines else "<no output>"


def main() -> int:
    print("PROBE C — WHO SEES A DOOR-PARAMETER EXEMPTION ADDED UNDER A ONE-WORD ALIAS?")
    print(f"tree: {ROOT}")
    print("NO VERDICT IS PRINTED. READ THE DATA LINES.")
    print()

    doors_check = "tools/register/check_judgement_path_doors.py"

    for arm in ("BASELINE (no alias added)", "ALIASED DOOR ADDED"):
        with tempfile.TemporaryDirectory() as scratch:
            tree = pathlib.Path(scratch) / "t"
            shutil.copytree(
                ROOT, tree,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
                symlinks=True,
            )
            if arm.startswith("ALIASED"):
                target = tree / "src" / "crash_detector" / "collectors" / "validation.py"
                target.write_text(target.read_text() + ALIASED_DOOR)

            print(f"--- arm: {arm}")

            code, out = _run(tree, doors_check, "--root", ".")
            print(f"    1 doors check                     : exit={code}  {_uses_line(out)}")
            print(f"      does it NAME the aliased door?  : {'aliased_probe_door' in out}")

            code, out = _run(tree, "-m", "pytest", "-q", "tests/test_judgement_path_doors.py")
            print(f"    2 tests/test_judgement_path_doors.py : exit={code}  {_tail(out)}")

            code, out = _run(tree, "-m", "pytest", "-q", "tests/test_admission.py")
            print(f"    3 tests/test_admission.py            : exit={code}  {_tail(out)}")

            code, out = _run(tree, "-m", "pytest", "-q")
            print(f"    4 the whole suite                    : exit={code}  {_tail(out)}")
            print()

    print("A READER THAT DOES NOT GO RED IS NOT A CARRIER, WHATEVER IT PRINTS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
