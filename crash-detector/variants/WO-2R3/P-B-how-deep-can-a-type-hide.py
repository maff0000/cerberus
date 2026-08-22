"""PROBE B — HOW DEEP CAN A JUDGEMENT-PATH TYPE HIDE FROM THE TWO GOVERNING INSTRUMENTS?

Run from the ROOT of a tree:  ``python3 -B variants/WO-2R3/P-B-how-deep-can-a-type-hide.py``

**NO VERDICT IS PRINTED.** Read the DATA lines (F-C1).

WHY IT EXISTS. `CD-ASR-WO2R3-01` found that `check_constructor_field_establishment.py` and
`check_judgement_path_doors.py` BOTH enumerated with `for node in tree.body` — top level only
— and that **NEITHER DECLARED IT**. One indentation level inside an already-governed file in
`engine/` escaped both. `PO-DECISIONS-0011` ruling 2 ordered the instruments fixed and **every
residual reach limit of the traversal DECLARED, never silent**.

**THIS PROBE IS WHERE THOSE DECLARED LIMITS COME FROM.** The dispatch is explicit that the
list of possible limits must not be copied: *"MEASURE WHICH OF THESE YOUR TRAVERSAL ACTUALLY
MISSES AND DECLARE EXACTLY THOSE — do not copy this list, and do not declare a limit you have
not demonstrated."* Every limit written into the three CD-RULE-004 places is a row below that
came back SEEN=no.

WHAT IT DOES. For each PLACEMENT it writes, into a throwaway copy of the tree, one public
frozen fielded dataclass with **no `@establishes`** and one public undecorated callable, both
inside `src/crash_detector/engine/` — a RULE A judgement-path package — and then runs both
instruments and reports, per placement:

  ctor  : the constructor instrument's exit code, and whether it NAMED the planted type
  doors : the doors instrument's exit code, and whether it NAMED the planted callable
  run   : whether the planted type ACCEPTS `(score=object(), breached='maybe')` at runtime

**A PLACEMENT WHERE `ctor exit=0` IS AN ESCAPE.** Placements that still escape after the fix
are the DECLARED LIMITS, and they are printed in the same table as the ones that are closed,
so this probe cannot be read as an advertisement for its author's fix.

**IT MUTATES NOTHING.** Everything happens in a temporary directory that is then removed.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
CTOR = "tools/register/check_constructor_field_establishment.py"
DOORS = "tools/register/check_judgement_path_doors.py"

#: The name every placement uses, so "did the instrument name it" is one string search.
TYPE_NAME = "HiddenVerdict"
DOOR_NAME = "hidden_decide"

#: The two things planted, at whatever indentation the placement needs.
BODY = '''@dataclass(frozen=True)
class {type_name}:
    score: float
    breached: bool


def {door_name}(reading):
    return reading
'''


def _indent(text: str, levels: int) -> str:
    pad = "    " * levels
    return "".join(pad + line if line.strip() else line for line in text.splitlines(True))


#: PLACEMENT -> the source appended to `engine/config.py`, and a note on what it varies.
#: `engine/config.py` already imports `dataclass`, so no placement needs a new import; a
#: placement that needed one would be varying TWO things at once.
PLACEMENTS: list = [
    (
        "module-level (CONTROL)",
        BODY.format(type_name=TYPE_NAME, door_name=DOOR_NAME),
        "the baseline. If this is not caught, nothing below means anything.",
    ),
    (
        "nested ONE class level",
        "class Outer1:\n" + _indent(BODY.format(type_name=TYPE_NAME, door_name=DOOR_NAME), 1),
        "THE AUDITOR'S ESCAPE. One indentation level, already-governed file, no rename.",
    ),
    (
        "nested TWO class levels",
        "class Outer1:\n    class Outer2:\n"
        + _indent(BODY.format(type_name=TYPE_NAME, door_name=DOOR_NAME), 2),
        "does the fix reach ARBITRARY depth or only the one depth that was measured?",
    ),
    (
        "inside a PUBLIC function body",
        "def outer_factory():\n"
        + _indent(BODY.format(type_name=TYPE_NAME, door_name=DOOR_NAME), 1)
        + "    return " + TYPE_NAME + ", " + DOOR_NAME + "\n",
        "a class defined where no import-time execution reaches it. The auditor's arm 4 "
        "shape: a function-local def that a module dict can then publish.",
    ),
    (
        "inside a PRIVATE function body",
        "def _outer_factory():\n"
        + _indent(BODY.format(type_name=TYPE_NAME, door_name=DOOR_NAME), 1)
        + "    return " + TYPE_NAME + ", " + DOOR_NAME + "\n",
        "the same, one character different. Isolates whether the enclosing scope's own "
        "visibility decides anything.",
    ),
    (
        "conditionally defined (`if True:`)",
        "if True:\n" + _indent(BODY.format(type_name=TYPE_NAME, door_name=DOOR_NAME), 1),
        "a static reader sees the source whether or not the branch is taken.",
    ),
    (
        "in a module OUTSIDE the scanned root",
        "",   # nothing is added to engine/config.py; see EXTRA_MODULE below
        "the instruments glob `src/crash_detector/**/*.py`. A file elsewhere is never parsed.",
    ),
    (
        "in a module that DOES NOT PARSE",
        "",   # see UNPARSEABLE below
        "a file the instrument cannot read. Is that a silence or a violation?",
    ),
    (
        "built by `type(...)` AT RUNTIME",
        "import dataclasses as _dc\n"
        f"{TYPE_NAME} = _dc.dataclass(frozen=True)(type('{TYPE_NAME}', (), "
        "{'__annotations__': {'score': float, 'breached': bool}}))\n"
        f"{DOOR_NAME} = lambda reading: reading\n",
        "NO `ClassDef` AND NO `FunctionDef` NODE EXISTS. There is nothing in the AST to walk.",
    ),
]


def _run(tree_root: pathlib.Path, script: str, *extra: str) -> tuple[int, str]:
    done = subprocess.run(
        [sys.executable, "-B", script, "--root", ".", *extra],
        cwd=tree_root,
        capture_output=True,
        text=True,
    )
    return done.returncode, done.stdout + done.stderr


_RUNTIME = f'''
import sys
sys.path.insert(0, "src")
import crash_detector.engine.config as config
target = getattr(config, "{TYPE_NAME}", None)
if target is None:
    for name in dir(config):
        holder = getattr(config, name)
        inner = getattr(holder, "{TYPE_NAME}", None)
        if inner is not None:
            target = inner
            break
if target is None:
    print("    run   : NOT REACHABLE from the module namespace at all")
else:
    try:
        target(score=object(), breached="maybe")
    except Exception as exc:
        print(f"    run   : REFUSED {{type(exc).__name__}}")
    else:
        print("    run   : ***ACCEPTED*** (score=object(), breached='maybe')")
'''


def main() -> int:
    print("PROBE B — HOW DEEP CAN A JUDGEMENT-PATH TYPE HIDE FROM THE TWO INSTRUMENTS?")
    print(f"tree: {ROOT}")
    print("NO VERDICT IS PRINTED. READ THE DATA LINES.")
    print(f"A PLACEMENT WITH `ctor exit=0` IS AN ESCAPE, wherever it appears in this table.")
    print()

    for name, addition, why in PLACEMENTS:
        with tempfile.TemporaryDirectory() as scratch:
            tree = pathlib.Path(scratch) / "t"
            shutil.copytree(
                ROOT, tree,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
                symlinks=True,
            )
            target = tree / "src" / "crash_detector" / "engine" / "config.py"
            if name == "in a module OUTSIDE the scanned root":
                outside = tree / "src" / "outside_the_root.py"
                outside.write_text(
                    "from dataclasses import dataclass\n\n\n"
                    + BODY.format(type_name=TYPE_NAME, door_name=DOOR_NAME)
                )
            elif name == "in a module that DOES NOT PARSE":
                broken = tree / "src" / "crash_detector" / "engine" / "unparseable.py"
                broken.write_text(
                    "from dataclasses import dataclass\n\n\n"
                    + BODY.format(type_name=TYPE_NAME, door_name=DOOR_NAME)
                    + "\nthis is (not( valid python\n"
                )
            else:
                target.write_text(target.read_text() + "\n\n" + addition)

            print(f"--- placement: {name}")
            print(f"    what it varies: {why}")

            code, out = _run(tree, CTOR)
            named = TYPE_NAME in out
            print(f"    ctor  : exit={code}  named `{TYPE_NAME}` in its output: {named}")
            code, out = _run(tree, CTOR, "--why")
            print(f"    ledger: `{TYPE_NAME}` appears under --why: {TYPE_NAME in out}")
            code, out = _run(tree, DOORS)
            print(f"    doors : exit={code}  named `{DOOR_NAME}` in its output: "
                  f"{DOOR_NAME in out}")

            done = subprocess.run(
                [sys.executable, "-B", "-c", _RUNTIME],
                cwd=tree, capture_output=True, text=True,
            )
            print((done.stdout + done.stderr).rstrip() or "    run   : <no output>")
            print()

    print("A PLACEMENT THIS TREE'S INSTRUMENTS CANNOT REACH IS A DECLARED LIMIT, NOT A SECRET.")
    print("The ones that are still escaping above are written into all three CD-RULE-004")
    print("places for this traversal, each with the row above as its executable example.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
