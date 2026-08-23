#!/usr/bin/env python3
"""PO-DECISIONS-0019 — VERIFY THAT THE CORRECTED PERIMETER IN `BLUEPRINT.md` IS THE PRODUCT
OWNER'S OWN BYTES.

Sibling of `check_blueprint_carried_po_text_verbatim.py`, which does the same job for
PO-DECISIONS-0018 ruling 1. **It is a SEPARATE file and not an edit of that one, deliberately:**
the 0018 check is standing evidence for v0.3.0 and mutating it to cover v0.4.0 would destroy the
evidence for the earlier carriage in the act of producing evidence for the later one.

`BLUEPRINT.md` is protected from EVERY SEAT INCLUDING THE PROJECT LEAD (`CD-D-115`).
PO-DECISIONS-0019 authorises the carriage in its own words — *"the corrections to BLUEPRINT.md are
mine to author (CD-D-115 / PBG-SOD-004), and are authored here for verbatim carriage"* — and a
Project Lead's ASSERTION that it carried text verbatim is exactly the self-vouching claim this
project has been burned by (`ASR3-F01`, and `F05` of the eighth seat's RED).

**SO IT IS A COMMAND AND NOT A SENTENCE.**

DECLARED LIMIT 1 — WHAT THIS CHECK DOES NOT SAY. It compares under a normalisation that strips
markdown emphasis, backticks, blockquote markers and collapses whitespace, because the carriage
re-wraps lines to the Blueprint's column width. **It therefore proves the WORDS are the Product
Owner's and NOT that the bytes are identical.** A carriage that changed emphasis or line breaks
passes here; a carriage that changed a WORD does not. `--counterfactual` proves that second half
rather than asserting it: it alters one word of every carried sentence and MUST fail.

DECLARED LIMIT 2 — IT IS NOT A COMPLETENESS CHECK. It verifies that what is quoted is genuine. It
does NOT verify that nothing else was added: the Project Lead's own authored bytes (the version
bump and status block, the two criterion IDs, the §14/§15 table scaffolding, the §14 disclosure
blockquote, the §19 row) are declared by enumeration at `BL-20260823T124508Z-0135` and are OUT OF
THIS CHECK'S REACH. **An auditor wanting that half runs `git diff 7794c15..HEAD -- BLUEPRINT.md`
and reads it.**

DECLARED LIMIT 3 — IT SAYS NOTHING ABOUT WHETHER THE CARRIED PERIMETER IS TRUE. It measures
provenance of text, not soundness of a claim. The three tiers are graded by an Assurance seat and
by nothing in this file.

CD-RULE-004: this header and any register entry or execution contract must say the same thing.

Exit 0 = every carried sentence resolves in both files. Exit 1 = at least one does not.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

CHECK_ID = "PO-0019-BLUEPRINT-CARRIED-PO-TEXT-VERBATIM"

PO_SOURCE = "governance/decisions/PO-DECISIONS-0019.md"
BP_TARGET = "BLUEPRINT.md"

#: Every sentence of PO-DECISIONS-0019 that BLUEPRINT.md v0.4.0 quotes. Each MUST resolve in the
#: Product Owner's own file AND in the Blueprint. A sentence appearing in the Blueprint but NOT in
#: the ruling is a seat inventing product meaning, which is what CD-D-115 exists to stop.
CARRIED = (
    (
        "ruling 1 — THREE TIERS, because two was the error",
        "The perimeter is restated as THREE TIERS, because two was the error",
    ),
    (
        "ruling 1 tier 1 — PREVENTED",
        "PREVENTED (accident + casual misuse): the declared-route refusals and the front door, "
        "exact-type admission — non-vacuous, proved by a refusing arm. Stops the forged SUBCLASS "
        "(F2) and every accident. Says exactly that and no more.",
    ),
    (
        "ruling 1 tier 2 — RESISTED, and the WeakSet obstacle OWNED",
        "RESISTED (deliberate in-process forgery, F1): a CONSTRUCTION-PROVENANCE door — \"did "
        "this object leave a declared door?\" — which the auditor measured separates genuine from "
        "F1 forgery in-process at admission time, defeatable only by locating and mutating a "
        "module-private structure (a difference IN KIND from F1's zero-knowledge, zero-package-line "
        "cost against exact type). Not absolute (its defeat is measured, FACT 3) — hence RESISTED, "
        "not prevented. The measured obstacle is owned in the text: the WeakSet form is "
        "unavailable because __slots__ omits __weakref__ and adding it widens the guarded "
        "surface, so the mechanism is specified as the discriminator, not the implementation.",
    ),
    (
        "ruling 1 tier 3 — DETECTED",
        "DETECTED (the residual, and the catastrophic-blast case): witness divergence + "
        "provenance, at the publication boundary — the backstop for what admission-time "
        "resistance does not hold, and the only defence where blast radius forbids relying on any "
        "in-process control (Layer 3 territory, D2 untouched).",
    ),
    (
        "ruling 2 — the RETRACTION and its reason",
        "\"the platform does not permit preventing it\" is RETRACTED, and the reason is that "
        "ADMISSION WAS NEVER TESTED.",
    ),
    (
        "ruling 2 — construction vs admission, the different predicate",
        "Construction cannot be prevented — measured three times, that stands. But admission is a "
        "different predicate, and a construction-provenance discriminator at admission is "
        "available and measured.",
    ),
    (
        "ruling 2 — the corrected text rests on a MEASUREMENT",
        "The corrected text rests on that measurement, not on an assertion.",
    ),
    (
        "ruling 3 — the criteria are MINTED by the Product Owner",
        "Two new acceptance criteria are minted",
    ),
    (
        "ruling 3 — CD-AC-017, the RESISTED tier",
        "admission on every judgement path admits only objects of provenance from a declared door "
        "(the RESISTED tier)",
    ),
    (
        "ruling 3 — CD-AC-018, the DETECTED tier",
        "the publication boundary raises DIVERGENCE between a released number and its "
        "corroborating witnesses (the DETECTED tier)",
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


def _break_one_word(needle: str) -> str:
    """Alter exactly ONE word of a carried sentence — the counterfactual arm."""
    words = needle.split(" ")
    for index, word in enumerate(words):
        if len(word) > 3:
            words[index] = word + "XQZ"
            break
    return " ".join(words)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--counterfactual", action="store_true",
        help="alter ONE word of every carried sentence; the run MUST fail, proving the check can",
    )
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    print(f"{CHECK_ID}")
    print(f"  tree: {root}")          # CD-PL-F98: every probe prints the tree it actually read.
    if args.counterfactual:
        print("  ARM: COUNTERFACTUAL — one word altered per sentence. A PASS HERE IS THE DEFECT.")

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
        if args.counterfactual:
            needle = _break_one_word(needle)
        in_po = needle in po
        in_bp = needle in bp
        if in_po and in_bp:
            carried_chars += len(needle)
        else:
            failures += 1
        status = "CARRIED" if (in_po and in_bp) else "**FAILED**"
        print(
            f"  [{status}] {label}\n"
            f"      in {PO_SOURCE}: {in_po}   in {BP_TARGET}: {in_bp}   ({len(needle)} chars)"
        )
        if not in_po and not args.counterfactual:
            print("      THE BLUEPRINT QUOTES A SENTENCE THE PRODUCT OWNER DID NOT WRITE, "
                  "or the ruling was edited after the carriage. EITHER IS A CD-D-115 BREACH.")
        if not in_bp and not args.counterfactual:
            print("      THE CARRIAGE IS INCOMPLETE OR WAS ALTERED. The perimeter in the "
                  "Blueprint is not the perimeter the Product Owner ruled.")

    print(
        f"\n  {len(CARRIED) - failures}/{len(CARRIED)} sentences resolve in BOTH files; "
        f"{carried_chars} normalised characters of Product Owner text carried."
    )
    print(
        "  DECLARED LIMIT: words, not bytes (emphasis and line breaks are normalised away); this "
        "check says NOTHING about what else the carriage added, and NOTHING about whether the\n"
        "  carried perimeter is true. For the first, read:  git diff 7794c15..HEAD -- BLUEPRINT.md"
    )
    if failures:
        print(f"\n{CHECK_ID}: FAIL — {failures} sentence(s) did not resolve in both files")
        return 1
    print(f"\n{CHECK_ID}: PASS — every quoted sentence is the Product Owner's own")
    return 0


if __name__ == "__main__":
    sys.exit(main())
