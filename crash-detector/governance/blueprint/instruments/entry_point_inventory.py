"""ENTRY-POINT INVENTORY — a Project Lead DESIGN INSTRUMENT, not application code.

It ships under `governance/blueprint/instruments/` and never under `src/`, because it is
evidence for a Blueprint amendment rather than a part of the product. It imports nothing
from the product, executes nothing from it, and only parses.

WHAT IT MEASURES
    Every public callable in a source tree that has at least one parameter whose type the
    callable does not establish anywhere in its own body — where "establish" means the
    parameter is named inside a call to one of the establishment functions this project
    already uses (`own_str`, `own_float`, `own_instant`, `own_utc_offset`, `ensure_utc`,
    `parse_utc`, `isinstance`, `type`, `sole_dial_of`, `observed_for_dial`).

WHAT IT DOES NOT MEASURE, STATED SO THE NUMBER IS NOT OVERREAD
    * It is syntactic. A parameter established by a helper one call away reads here as
      unestablished, and a parameter named inside a `type(...)` call that compares
      something else reads here as established. Both directions of error are present.
    * It does not know which callables are on a judgement path. That classification is
      done by hand in the amendment and is the Project Lead's reading, not a measurement.
    * A `Protocol` parameter is structurally typed by construction, so an annotation is
      never establishment. The instrument does not read annotations at all.

    So the count is a FLOOR ON WHERE TO LOOK, not a defect count. It exists to answer the
    auditor's open denominator question — "the three I found are a denominator of three,
    not a proof that a fourth does not exist" (CD-ASR-WO2R2-01, NEXT SAFE GATE) — with a
    measurement instead of an assertion.

PRODUCING COMMAND, recorded here because CD-PL-F78 / PO-DECISIONS-0004 ruling 5 makes an
integrity artefact that does not record its producing command not an integrity control:

    python3 -B governance/blueprint/instruments/entry_point_inventory.py \
        /srv/crash-detector-wo2r2-audit/src/crash_detector

Target of the run recorded in BP-AMENDMENT-0001: worktree /srv/crash-detector-wo2r2-audit
at f30e63cbac6782ec5d7789071ee26be0ba7fe2e5, tree object
01da44b51e07dfb2e71170f4f19b6db09814b981.
"""

from __future__ import annotations

import ast
import pathlib
import sys

#: The functions this project uses to establish that a value is what it claims to be.
#: `isinstance` and `type` are included even though the project's own standard is exact
#: type, because the instrument is looking for the ABSENCE of any establishment at all.
ESTABLISHERS = {
    "own_str",
    "own_float",
    "own_instant",
    "own_utc_offset",
    "ensure_utc",
    "parse_utc",
    "isinstance",
    "type",
    "sole_dial_of",
    "observed_for_dial",
}


def is_public(name: str) -> bool:
    return not name.startswith("_")


def inventory(root: pathlib.Path) -> list[tuple[str, int, str, list[str]]]:
    rows: list[tuple[str, int, str, list[str]]] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        rel = path.relative_to(root.parent)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not is_public(node.name):
                continue
            args = (
                node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            )
            names = [a.arg for a in args if a.arg not in ("self", "cls")]
            if not names:
                continue
            established: set[str] = set()
            for sub in ast.walk(node):
                if not isinstance(sub, ast.Call):
                    continue
                fn = sub.func
                fname = getattr(fn, "id", None) or getattr(fn, "attr", None)
                if fname not in ESTABLISHERS:
                    continue
                for inner in ast.walk(sub):
                    if isinstance(inner, ast.Name) and inner.id in names:
                        established.add(inner.id)
            unestablished = [n for n in names if n not in established]
            if unestablished:
                rows.append((str(rel), node.lineno, node.name, unestablished))
    return rows


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    rows = inventory(pathlib.Path(sys.argv[1]))
    for rel, lineno, name, params in rows:
        print(f"{rel}:{lineno}\t{name}({', '.join(params)})")
    print(
        "\nTOTAL public callables with at least one unestablished parameter: "
        f"{len(rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
