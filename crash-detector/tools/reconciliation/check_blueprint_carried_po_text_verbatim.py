#!/usr/bin/env python3
"""CD-D-172 — VERIFY THAT THE PERIMETER TEXT IN `BLUEPRINT.md` IS THE PRODUCT OWNER'S OWN BYTES.

`BLUEPRINT.md` is protected from EVERY SEAT INCLUDING THE PROJECT LEAD (`CD-D-115`).
PO-DECISIONS-0018 ruling 5 authorises one narrow act against it — *"PO-authored text carried
verbatim where protected"* — and a Project Lead's assertion that it carried text verbatim is
exactly the kind of self-vouching claim this project has been burned by (`ASR3-F01`).

**SO IT IS A COMMAND AND NOT A SENTENCE.** This check asserts that every sentence of
PO-DECISIONS-0018 ruling 1 that `BLUEPRINT.md` quotes RESOLVES IN BOTH FILES, so a reader can
falsify the carriage claim in one run instead of diffing by eye.

DECLARED LIMIT 1 — WHAT THIS CHECK DOES NOT SAY. It compares under a normalisation that strips
markdown emphasis, backticks, blockquote markers and collapses whitespace, because the carriage
re-wraps lines to the Blueprint's column width. **It therefore proves the WORDS are the Product
Owner's and NOT that the bytes are identical.** A carriage that changed emphasis or line breaks
passes here; a carriage that changed a WORD does not.

DECLARED LIMIT 2 — IT IS NOT A COMPLETENESS CHECK. It verifies that what is quoted is genuine.
It does NOT verify that nothing else was added: the Project Lead's own authored bytes (the version
bump, the two IDs, the table scaffolding, the amendment-log row) are declared by enumeration at
`BL-20260823T095521Z-0131` and are OUT OF THIS CHECK'S REACH. **An auditor wanting that half runs
`git diff <before>..<after> -- BLUEPRINT.md` and reads it.**

CD-RULE-004: this header, the register entry and the execution contract must say the same thing.

Exit 0 = every carried sentence resolves in both files. Exit 1 = at least one does not.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

CHECK_ID = "CD-D-172-BLUEPRINT-CARRIED-PO-TEXT-VERBATIM"

PO_SOURCE = "governance/decisions/PO-DECISIONS-0018.md"
BP_TARGET = "BLUEPRINT.md"

#: Every sentence of PO-DECISIONS-0018 ruling 1 that BLUEPRINT.md §16 quotes. Each MUST resolve
#: in the Product Owner's own file AND in the Blueprint. A sentence appearing in the Blueprint but
#: NOT in the ruling is a seat inventing product meaning, which is what CD-D-115 exists to stop.
CARRIED = (
    (
        "ruling 1 preamble",
        "an enumeration cannot close a property-defined class — and this class is defined by a "
        "platform property we do not control",
    ),
    (
        "ruling 1(a) — the declared-route refusals are KEPT",
        "The declared-route refusals STAND and are kept — they are real, they refuse the front "
        "door and the named routes, and they proof the product against ACCIDENT and against casual "
        "misuse. That is worth having and it is what they honestly are.",
    ),
    (
        "ruling 1(b) — what a SEALED verdict may claim",
        "SEALED means sealed against declared routes; NOT sealed against deliberate in-process "
        "forgery, which the platform does not permit preventing. A green board that says exactly "
        "that is honest; a green board that says more is the sixth false green.",
    ),
    (
        "ruling 1(c) — the FORGERY-DETECTION OBLIGATION",
        "The defence against deliberate in-process forgery is DETECTION, and it already has a "
        "home. This is the estate's own settled doctrine arriving at its own product: prevention "
        "where blast radius is catastrophic (Layer 3, out-of-process, where the money gate lives "
        "— D2 untouched); detection everywhere else. The PID already says it: external sources "
        "are WITNESSES, never ingredients — DIVERGENCE IS THE ALARM. A forged magnitude that "
        "reaches publication must diverge from what the witnesses corroborate or be caught by the "
        "provenance chain; BLUEPRINT §17 gains the risk row and §16 gains the owed "
        "control: the FORGERY-DETECTION OBLIGATION, specified at WO-3 when real sources land, "
        "verified as a first-class criterion. The detector is ADVISORY (D1) and no money moves on "
        "it (D2); the perimeter now says truthfully what is prevented, what is detected, and what "
        "is out of scope — and the eighth seat grades against THAT, which is a gradeable claim.",
    ),
)


def normalise(text: str) -> str:
    """Strip markdown emphasis, backticks and blockquote markers; collapse whitespace.

    The carriage re-wraps to the Blueprint's column width, so a raw substring test would fail for
    a PERFECTLY FAITHFUL carriage. See DECLARED LIMIT 1 in the module docstring for what this
    normalisation costs.
    """
    text = text.replace("*", "").replace("`", "").replace(">", " ")
    return re.sub(r"\s+", " ", text).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    print(f"{CHECK_ID}")
    print(f"  tree: {root}")          # CD-PL-F98: every probe prints the tree it actually read.

    po_path, bp_path = root / PO_SOURCE, root / BP_TARGET
    for path in (po_path, bp_path):
        if not path.is_file():
            print(f"  FAIL — required file absent: {path}")
            return 1

    po = normalise(po_path.read_text(encoding="utf-8"))
    bp = normalise(bp_path.read_text(encoding="utf-8"))

    failures = 0
    carried_chars = 0
    for label, sentence in CARRIED:
        needle = normalise(sentence)
        in_po = needle in po
        in_bp = needle in bp
        status = "CARRIED" if (in_po and in_bp) else "**FAILED**"
        if in_po and in_bp:
            carried_chars += len(needle)
        else:
            failures += 1
        print(
            f"  [{status}] {label}\n"
            f"      in {PO_SOURCE}: {in_po}   in {BP_TARGET}: {in_bp}   ({len(needle)} chars)"
        )
        if not in_po:
            print("      THE BLUEPRINT QUOTES A SENTENCE THE PRODUCT OWNER DID NOT WRITE, "
                  "or the ruling was edited after the carriage. EITHER IS A CD-D-115 BREACH.")
        if not in_bp:
            print("      THE CARRIAGE IS INCOMPLETE OR WAS ALTERED. The perimeter in the "
                  "Blueprint is not the perimeter the Product Owner ruled.")

    print(
        f"\n  {len(CARRIED) - failures}/{len(CARRIED)} sentences resolve in BOTH files; "
        f"{carried_chars} normalised characters of Product Owner text carried."
    )
    print(
        "  DECLARED LIMIT: words, not bytes (emphasis and line breaks are normalised away), and "
        "this check says NOTHING about what else the carriage added — for that, read\n"
        "      git diff 184c3e1..HEAD -- BLUEPRINT.md"
    )
    if failures:
        print(f"\n{CHECK_ID}: FAIL — {failures} sentence(s) did not resolve in both files")
        return 1
    print(f"\n{CHECK_ID}: PASS — every quoted sentence is the Product Owner's own")
    return 0


if __name__ == "__main__":
    sys.exit(main())
