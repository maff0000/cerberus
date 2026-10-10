#!/usr/bin/env python3
"""PO-DECISIONS-0020 — VERIFY THE PID §6 AMENDMENT AND THE `F05` REMOVAL BY COMMAND.

Third sibling of `check_blueprint_carried_po_text_verbatim.py` (PO-0018 ruling 1, v0.3.0) and
`check_blueprint_carried_po_0019_verbatim.py` (PO-0019, v0.4.0). **A SEPARATE FILE AND NOT AN EDIT
OF EITHER, for the same reason those two are separate:** each is standing evidence for one
carriage, and mutating an older check to cover a newer one destroys the earlier evidence in the act
of producing the later.

`PID.md` is amendable **by the Product Owner only** (its own frontmatter: *"amendment: PO only"*),
and `BLUEPRINT.md` is protected from EVERY SEAT INCLUDING THE PROJECT LEAD (`CD-D-115`).
PO-DECISIONS-0020 authorises both acts in its own words — *"both are the Product Owner's alone
(PBG-PID-002, CD-D-115), authored here for verbatim carriage"*. **A Project Lead's ASSERTION that
it carried the Product Owner's bytes is precisely the self-vouching claim `F05` and `ASR3-F01`
caught. SO THIS IS A COMMAND AND NOT A SENTENCE.**

THIS CHECK HAS THREE ARMS, AND THE SECOND IS THE HARD ONE.

  ARM 1 — CARRIAGE. Every sentence this boundary quotes from PO-DECISIONS-0020 must resolve in the
  Product Owner's own file AND in the target that quotes it. A sentence present in the target but
  absent from the ruling is a seat inventing product meaning.

  ARM 2 — THE REMOVAL, AS USE-VERSUS-MENTION. `F05`'s repair is a DELETION, and a deletion cannot
  be proved by "the string is gone" — **because the Product Owner's own ruling QUOTES the sentence
  it removes, and this boundary carries that ruling verbatim.** The string therefore still occurs,
  and MUST still occur, or the carriage would be incomplete. What must be gone is the sentence
  functioning as THIS DOCUMENT'S OWN NORMATIVE VOICE. So the arm is split:
      2a. the original normative construction — the sentence welded to the owed-control statement
          in §16 — must be ABSENT outright;
      2b. every SURVIVING occurrence must be a MENTION and not a USE: it must sit inside double
          quotation marks. A single unquoted survival is the defect, and it is the exact defect
          `F05` raised.

  ARM 3 — 3/4 AND NEVER 4/4. PO-DECISIONS-0020 ruling 1 says *"Until the register rows exist they
  are 3/4 and MUST be carried as such, never rounded up."* This arm MEASURES that the register row
  really is absent, rather than trusting the boundary's own claim to have been honest about it.
  **If a register row for either criterion ever appears, THIS ARM STARTS FAILING** — deliberately.
  It is then telling the truth: the "3/4" prose has gone stale and must be re-derived, not that the
  register is wrong. **A check that silently kept passing across that transition would be useless.**

DECLARED LIMIT 1 — WORDS, NOT BYTES. Comparison runs under a normalisation that strips markdown
emphasis, backticks and blockquote markers and collapses whitespace, because carriage re-wraps to
each document's column width. A carriage that changed emphasis or line breaks passes here; one that
changed a WORD does not. `--counterfactual` proves that second half rather than asserting it.

DECLARED LIMIT 2 — NOT A COMPLETENESS CHECK. It proves what is quoted is genuine. It does NOT prove
nothing else was added. The Project Lead's own authored bytes at this boundary (the PID version bump
and §10 row, the BLUEPRINT version bump, status paragraph and §19 row, the §16/§17 label-discrepancy
disclosure, and the surrounding scaffolding prose) are OUT OF THIS CHECK'S REACH and are enumerated
in the Build Log. **An auditor wanting that half runs `git diff abafec2..HEAD -- PID.md BLUEPRINT.md`
and reads it.**

DECLARED LIMIT 3 — IT SAYS NOTHING ABOUT WHETHER ANY OF IT IS TRUE. It measures the provenance of
text and the absence of a string. Whether `CD-AC-017` is a sound requirement, and whether the
three-tier perimeter holds, is graded by an Assurance seat and by nothing in this file.

CD-RULE-004: this header and any register entry or execution contract must say the same thing.

Exit 0 = all three arms hold. Exit 1 = at least one does not.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

CHECK_ID = "PO-0020-PID-AMENDED-AND-F05-REMOVED-VERBATIM"

PO_SOURCE = "governance/decisions/PO-DECISIONS-0020.md"
PID_TARGET = "PID.md"
BP_TARGET = "BLUEPRINT.md"
LANE_REGISTER = "required-tests.yaml"

#: ARM 1. (label, sentence, target-file) — each MUST resolve in PO-DECISIONS-0020 *and* in target.
CARRIED = (
    (
        "ruling 1 — CD-AC-017's §6 row, the Product Owner's own row",
        "CD-AC-017 | Admission by declared-door provenance | plant: hand a judgement path a "
        "forged object of exact type that never left a declared door → admission refuses it; "
        "genuine article from the declared door → admitted. (RESISTED tier, §17 CD-BP-005.)",
        PID_TARGET,
    ),
    (
        "ruling 1 — CD-AC-018 is STRENGTHENS and NOT free-standing",
        "It enters as a STRENGTHENS relation on CD-AC-004, not as a free-standing requirement; "
        "the DETECTED tier is not new doctrine, it is CD-AC-004 named at the exit.",
        PID_TARGET,
    ),
    (
        "ruling 1 — the pid_relation resolved",
        "This resolves the pid_relation cleanly (DERIVES/STRENGTHENS/NEW — STRENGTHENS).",
        PID_TARGET,
    ),
    (
        "ruling 1 — 3/4 AND NEVER ROUNDED UP",
        "Until the register rows exist they are 3/4 and MUST be carried as such, never rounded up.",
        PID_TARGET,
    ),
    (
        "ruling 2 — the removal is the Product Owner's, at the PO layer",
        "I remove it now, at the PO layer, and replace it with the correct pointer",
        BP_TARGET,
    ),
    (
        "ruling 2 — no Engineer could remove it and none should have tried",
        "which CD-D-115 protects from every seat including me-via-a-seat — so no Engineer could "
        "remove it and none should have tried.",
        BP_TARGET,
    ),
    (
        "ruling 2 — where the requirement now LIVES",
        "the requirement that the forgery-detection obligation take a scheduled criterion form now "
        "LIVES as CD-AC-017/CD-AC-018 in the PID and the register (ruling 1), which is where a "
        "normative requirement belongs — not as loose prose in the Blueprint's risk section.",
        BP_TARGET,
    ),
    (
        "ruling 2 — §17 keeps its columns and cites the two criteria",
        "The Blueprint §17 row keeps its RISK/HANDLING columns and CITES the two criteria; it no "
        "longer carries the normative sentence about their form.",
        BP_TARGET,
    ),
    (
        "ruling 2 — F05 and F03 discharged by the same act",
        "F05 is discharged; F03 (the record carrying the obligation in a forbidden form) is "
        "discharged by the same act, because the obligation now has the required form.",
        BP_TARGET,
    ),
)

#: ARM 2. The bytes the Product Owner removed.
REMOVED = "not as a note, not as a residue paragraph, and not as a manual step"

#: ARM 2a. The original normative construction — the sentence welded to the owed-control statement.
#: THIS is what F05 raised, and this exact shape must be gone.
REMOVED_IN_ORIGINAL_POSITION = "FIRST-CLASS CRITERION — " + REMOVED

#: ARM 3. Where the register row would live if it existed. It does not exist on main; it is a
#: WO-3 artefact on the `wo-2r3` lane. Both criteria are therefore 3/4 of the CD-D-172 form.
REGISTER_ABSENT_FOR = ("CD-AC-017", "CD-AC-018")


def normalise(text: str) -> str:
    """Strip markdown emphasis, backticks and blockquote markers; collapse whitespace.

    Carriage re-wraps to each document's column width, so a raw substring test would fail for a
    PERFECTLY FAITHFUL carriage. See DECLARED LIMIT 1 for what this costs.

    NOTE: double quotes are DELIBERATELY PRESERVED — arm 2b decides use-versus-mention on them,
    so normalising them away would silently destroy that arm.
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


def _occurrences(haystack: str, needle: str):
    start = 0
    while True:
        found = haystack.find(needle, start)
        if found < 0:
            return
        yield found
        start = found + 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--counterfactual", action="store_true",
        help="alter ONE word of every carried sentence and re-insert the removed sentence as a "
             "USE; the run MUST fail, proving the check can",
    )
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    print(f"{CHECK_ID}")
    print(f"  tree: {root}")          # CD-PL-F98: every probe prints the tree it actually read.
    if args.counterfactual:
        print("  ARM: COUNTERFACTUAL — one word altered per sentence, and the removed sentence")
        print("       re-introduced as an UNQUOTED USE. A PASS HERE IS THE DEFECT.")

    po_path = root / PO_SOURCE
    pid_path = root / PID_TARGET
    bp_path = root / BP_TARGET
    for path in (po_path, pid_path, bp_path):
        if not path.is_file():
            print(f"  FAIL — required file absent: {path}")
            return 1

    po = normalise(po_path.read_text(encoding="utf-8"))
    targets = {
        PID_TARGET: normalise(pid_path.read_text(encoding="utf-8")),
        BP_TARGET: normalise(bp_path.read_text(encoding="utf-8")),
    }

    failures = 0
    carried_chars = 0

    # ---------------------------------------------------------------- ARM 1: carriage
    print("\n  ARM 1 — CARRIAGE: every quoted sentence is the Product Owner's own")
    for label, sentence, target_name in CARRIED:
        needle = normalise(sentence)
        if args.counterfactual:
            needle = _break_one_word(needle)
        in_po = needle in po
        in_target = needle in targets[target_name]
        if in_po and in_target:
            carried_chars += len(needle)
        else:
            failures += 1
        status = "CARRIED" if (in_po and in_target) else "**FAILED**"
        print(
            f"    [{status}] {label}\n"
            f"        in {PO_SOURCE}: {in_po}   in {target_name}: {in_target}   "
            f"({len(needle)} chars)"
        )
        if not in_po and not args.counterfactual:
            print("        THE TARGET QUOTES A SENTENCE THE PRODUCT OWNER DID NOT WRITE, or the "
                  "ruling was edited after the carriage. EITHER IS A BREACH.")
        if not in_target and not args.counterfactual:
            print("        THE CARRIAGE IS INCOMPLETE OR WAS ALTERED.")

    # ------------------------------------------- ARM 2: the removal, as use-versus-mention
    print("\n  ARM 2 — THE REMOVAL: F05's sentence survives only as a MENTION, never as a USE")
    bp = targets[BP_TARGET]
    if args.counterfactual:
        bp = bp + " and it is verified as a FIRST-CLASS CRITERION — " + REMOVED + " forever."

    original = normalise(REMOVED_IN_ORIGINAL_POSITION)
    if original in bp:
        failures += 1
        print(f"    [**FAILED**] 2a — the original normative construction is STILL PRESENT")
        print(f"        F05 IS NOT REPAIRED. Found: {original[:70]}...")
    else:
        print("    [REMOVED ] 2a — the original normative construction is ABSENT")

    needle = normalise(REMOVED)
    sites = list(_occurrences(bp, needle))
    unquoted = []
    for site in sites:
        before = bp[max(0, site - 2):site]
        after = bp[site + len(needle):site + len(needle) + 2]
        # A MENTION is bounded by double quotes on both sides. A USE is not.
        if '"' not in before or '"' not in after:
            unquoted.append(site)
    if unquoted:
        failures += 1
        print(f"    [**FAILED**] 2b — {len(unquoted)} of {len(sites)} survival(s) are UNQUOTED USES")
        for site in unquoted:
            print(f'        ...{bp[max(0, site - 60):site + len(needle) + 20]}...')
        print("        AN UNQUOTED SURVIVAL IS THE SENTENCE STILL SPEAKING IN THIS DOCUMENT'S "
              "OWN NORMATIVE VOICE, WHICH IS EXACTLY WHAT F05 RAISED.")
    else:
        print(f"    [MENTIONS] 2b — all {len(sites)} survival(s) are quoted mentions, not uses")
        print("        (survivals are REQUIRED: the Product Owner's ruling quotes the sentence it "
              "removes, and that ruling is carried verbatim.)")

    # ------------------------------------------------------- ARM 3: 3/4 and never 4/4
    print("\n  ARM 3 — 3/4 AND NEVER ROUNDED UP: the register row is MEASURED absent")
    register = root / LANE_REGISTER
    if register.is_file():
        text = register.read_text(encoding="utf-8")
        present = [cid for cid in REGISTER_ABSENT_FOR if cid in text]
        if present:
            failures += 1
            print(f"    [**FAILED**] {LANE_REGISTER} now carries {', '.join(present)}")
            print("        THIS IS NOT NECESSARILY A DEFECT IN THE REGISTER — IT IS A DEFECT IN "
                  "THE PROSE. The record still says 3/4 and the register says otherwise; "
                  "re-derive the fraction and update this check.")
        else:
            print(f"    [3/4     ] {LANE_REGISTER} present and carries neither criterion")
    else:
        print(f"    [3/4     ] {LANE_REGISTER} is ABSENT from this tree — the register is a WO-3")
        print("               artefact on the wo-2r3 lane, so 3/4 is the honest fraction:")
        print("               §14 row + §15 work order + PID §6 lineage = 3; register row = 0.")

    # ------------------------------------------------------------------------ verdict
    print(
        f"\n  {len(CARRIED) - min(failures, len(CARRIED))}/{len(CARRIED)} sentences resolve in "
        f"both files; {carried_chars} normalised characters of Product Owner text carried."
    )
    print(
        "  DECLARED LIMIT: words, not bytes. This check says NOTHING about what else the carriage\n"
        "  added, and NOTHING about whether any of it is TRUE. For the first, read:\n"
        "      git diff abafec2..HEAD -- PID.md BLUEPRINT.md"
    )
    if failures:
        print(f"\n{CHECK_ID}: FAIL — {failures} arm/sentence check(s) did not hold")
        return 1
    print(f"\n{CHECK_ID}: PASS — the PID amendment and the F05 removal are the Product Owner's own")
    return 0


if __name__ == "__main__":
    sys.exit(main())
