#!/usr/bin/env python3
"""PO-DECISIONS-0022 ruling 2 — VERIFY THE `RESISTED` TIER CORRECTION BY COMMAND.

Fourth sibling of `check_blueprint_carried_po_text_verbatim.py` (PO-0018, v0.3.0),
`check_blueprint_carried_po_0019_verbatim.py` (PO-0019, v0.4.0) and
`check_pid_carried_po_0020_verbatim.py` (PO-0020, v0.4.1). **A SEPARATE FILE AND NOT AN EDIT OF
ANY OF THEM**, for the reason those three are separate: each is standing evidence for ONE carriage,
and mutating an older check so a newer carriage passes destroys the earlier evidence in the act of
producing the later. **That is especially load-bearing here, because this carriage SUPERSEDES a
sentence the 0019 check certifies — and the honest record of that is the 0019 check going RED on
exactly one sentence, not the 0019 check being quietly rewritten.**

`BLUEPRINT.md` is protected from EVERY SEAT INCLUDING THE PROJECT LEAD (`CD-D-115`).
PO-DECISIONS-0022 ruling 2 authorises this carriage in its own words — *"PO-authored correction,
carried verbatim by the remediation increment as its first act"*. A Project Lead's ASSERTION that
it carried the Product Owner's bytes is precisely the self-vouching claim `ASR3-F01`, the eighth
seat's `F05` and the ninth seat's findings were built to catch. **SO THIS IS A COMMAND AND NOT A
SENTENCE.**

THIS CHECK HAS THREE ARMS, AND THE THIRD IS THE ONE THAT MATTERS.

  ARM 1 — CARRIAGE. Every sentence of ruling 2's blockquote must resolve in the Product Owner's own
  file AND in `BLUEPRINT.md`. A sentence present in the Blueprint but absent from the ruling is a
  seat inventing product meaning inside a protected file.

  ARM 2 — SUPERSESSION, AS USE-VERSUS-MENTION. The v0.4.0 `RESISTED` prose is REPLACED, and a
  replacement cannot be proved by "the old string is gone" — the §19 amendment log QUOTES the old
  reading as history and MUST keep doing so (`PBG-CONT-003`: corrections supersede, they never
  edit). So the arm is split:
      2a. the distinctive superseded fragment — *"defeatable only by locating and mutating a
          module-private structure"* — must be ABSENT from §17's `CD-BP-005` row, which is the
          document's own normative voice;
      2b. any SURVIVING occurrence elsewhere in the file must sit in §19, the amendment log, where
          it is a MENTION of what was corrected and not a USE. A survival in §17 is the defect.

  ARM 3 — THE SUPERSESSION IS EXACTLY ONE SENTENCE WIDE. This arm imports the 0019 check's OWN
  `CARRIED` table — not a copy of it — and measures each of its ten sentences against
  `BLUEPRINT.md` today. **EXACTLY ONE must have stopped resolving: `ruling 1 tier 2 — RESISTED, and
  the WeakSet obstacle OWNED`. The other NINE must still resolve.** This is the arm that stops this
  boundary from using a PO-authorised correction as cover for dropping other Product Owner bytes
  from a protected file while nobody is counting. If a tenth sentence goes missing, or if the
  RESISTED sentence is still there, this arm FAILS and says which.

DECLARED LIMIT 1 — WORDS, NOT BYTES. Comparison runs under a normalisation that strips markdown
emphasis, backticks and blockquote markers and collapses whitespace, because carriage re-wraps to
each document's column width. A carriage that changed emphasis or line breaks passes here; one that
changed a WORD does not. `--counterfactual` proves that second half rather than asserting it.

DECLARED LIMIT 2 — AND IT IS NEW HERE, DECLARED RATHER THAN DISCOVERED. A hyphen at a line break is
REJOINED on both sides before comparison, because PO-DECISIONS-0022 hard-wraps `construction-
provenance` across lines 28/29 of its own file and a raw comparison would fail a PERFECTLY FAITHFUL
carriage. The rejoin is applied identically to source and target, so it cannot make a changed word
match; it can only stop a line break from counting as a change. The three sibling checks do not do
this because none of their carried sentences is hyphen-split.

DECLARED LIMIT 3 — NOT A COMPLETENESS CHECK. It proves what is quoted is genuine and that exactly
one sentence was superseded. It does NOT prove nothing else was added. The Project Lead's own
authored bytes at this boundary (the version bump, the status paragraph, the §19 row, and the
retained `**Scheduled as CD-AC-017** (§14, §15 WO-3)` scaffolding clause) are OUT OF THIS CHECK'S
REACH and are enumerated in the Build Log. **An auditor wanting that half runs
`git diff d60b8b9..HEAD -- BLUEPRINT.md` and reads it.**

DECLARED LIMIT 4 — IT SAYS NOTHING ABOUT WHETHER ANY OF IT IS TRUE. It measures the provenance of
text and the width of a supersession. Whether `CD-AC-017` is a sound requirement, whether the
DETECTED tier can in fact bear the load moved onto it, and whether the corrected perimeter holds,
is graded by an Assurance seat and by nothing in this file.

CD-RULE-004: this header and any register entry or execution contract must say the same thing.

Exit 0 = all three arms hold. Exit 1 = at least one does not.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CHECK_ID = "PO-0022-BLUEPRINT-RESISTED-CORRECTED-VERBATIM"

PO_SOURCE = "governance/decisions/PO-DECISIONS-0022.md"
BP_TARGET = "BLUEPRINT.md"

#: ARM 1. (label, sentence) — each MUST resolve in PO-DECISIONS-0022 *and* in BLUEPRINT.md.
#: A sentence here that is absent from the ruling is a seat inventing product meaning.
CARRIED = (
    (
        "ruling 2 — the tier label, corrected to OWED, NOT BUILT",
        "RESISTED (deliberate in-process forgery, F1) — OWED, NOT BUILT.",
    ),
    (
        "ruling 2 — the mechanism is specified, unbuilt, and insufficient alone",
        "A construction-provenance discriminator at admission is the specified mechanism "
        "(CD-AC-017), and it is not yet built and, as first measured, insufficient alone: a value "
        "forged AFTER admission defeats it at zero cost.",
    ),
    (
        "ruling 2 — THE LOAD MOVES TO DETECTION until admission is built AND proven",
        "Until CD-AC-017 is built AND shown to bind post-admission mutation, the F1 route is "
        "carried by the DETECTED tier (CD-AC-018, witness divergence at publication) as the "
        "load-bearing defence, with admission-provenance as defence-in-depth, not the primary.",
    ),
    (
        "ruling 2 — when it is verified",
        "Verified at WO-3 when real sources land.",
    ),
)

#: ARM 2. The distinctive fragment of the SUPERSEDED v0.4.0 RESISTED prose. Chosen because it
#: occurs in the removed text and in NO paraphrase of it: §19's v0.4.0 row summarises the tier
#: without reproducing this clause.
SUPERSEDED_FRAGMENT = "defeatable only by locating and mutating a module-private structure"

#: ARM 3. The one 0019 sentence this correction supersedes, by the sibling check's OWN label.
SUPERSEDED_0019_LABEL = "ruling 1 tier 2 — RESISTED, and the WeakSet obstacle OWNED"


def normalise(text: str) -> str:
    """Rejoin hyphen-linebreaks, strip markdown emphasis and blockquote markers, collapse space.

    See DECLARED LIMIT 1 and DECLARED LIMIT 2 in the module docstring for what this costs. The
    rejoin runs BEFORE the whitespace collapse, and identically on both sides of every comparison.
    """
    text = re.sub(r"-[ \t]*\r?\n[ \t]*>?[ \t]*", "-", text)
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


def _section(blueprint_raw: str, heading: str, next_heading: str) -> str:
    """Return the raw text between two `## ` headings. Fails loudly if either is missing."""
    start = blueprint_raw.index(heading)
    end = blueprint_raw.index(next_heading, start)
    return blueprint_raw[start:end]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--counterfactual",
        action="store_true",
        help="alter ONE word of every carried sentence and of the ARM 2 fragment; the check MUST "
             "then fail. This proves the check can fail rather than asserting that it can.",
    )
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    po_raw = (root / PO_SOURCE).read_text(encoding="utf-8")
    bp_raw = (root / BP_TARGET).read_text(encoding="utf-8")
    po = normalise(po_raw)
    bp = normalise(bp_raw)

    print(CHECK_ID)
    print("  tree: %s" % root)
    if args.counterfactual:
        print("  *** COUNTERFACTUAL ARM: one word altered in every sentence. MUST FAIL. ***")

    failures = []

    # ---- ARM 1 -----------------------------------------------------------------------------
    print("\n  ARM 1 — CARRIAGE: ruling 2's blockquote, in the PO's file AND in the Blueprint")
    carried_chars = 0
    for label, sentence in CARRIED:
        needle = normalise(sentence)
        if args.counterfactual:
            needle = _break_one_word(needle)
        in_po = needle in po
        in_bp = needle in bp
        ok = in_po and in_bp
        if ok:
            carried_chars += len(needle)
        print("    [%s] %s" % ("CARRIED" if ok else "MISSING", label))
        print("        in %s: %s   in %s: %s   (%d chars)"
              % (PO_SOURCE, in_po, BP_TARGET, in_bp, len(needle)))
        if not ok:
            failures.append("ARM 1: %s (in_po=%s in_bp=%s)" % (label, in_po, in_bp))
    print("    %d/%d sentences resolve in BOTH files; %d normalised characters carried."
          % (len(CARRIED) - len([f for f in failures if f.startswith("ARM 1")]),
             len(CARRIED), carried_chars))

    # ---- ARM 2 -----------------------------------------------------------------------------
    print("\n  ARM 2 — SUPERSESSION, use-versus-mention")
    fragment = normalise(SUPERSEDED_FRAGMENT)
    if args.counterfactual:
        fragment = _break_one_word(fragment)
    sec17 = normalise(_section(bp_raw, "## 17. Risks carried into WO-2", "## 18."))
    sec19 = normalise(_section(bp_raw, "## 19. Amendment log", "\n---\n")) if "\n---\n" in \
        bp_raw[bp_raw.index("## 19. Amendment log"):] else normalise(
            bp_raw[bp_raw.index("## 19. Amendment log"):])
    total = bp.count(fragment)
    in_17 = fragment in sec17
    in_19 = fragment in sec19
    print("    2a. superseded fragment ABSENT from §17 (the normative voice) : %s" % (not in_17))
    print("        fragment: %r" % SUPERSEDED_FRAGMENT)
    print("    2b. occurrences in the whole file: %d ; in §19 (a MENTION): %s" % (total, in_19))
    if in_17:
        failures.append("ARM 2a: the superseded v0.4.0 RESISTED prose is STILL IN §17")
    if total and not in_19:
        failures.append("ARM 2b: the fragment survives OUTSIDE §17 and OUTSIDE §19 — neither a "
                        "use this boundary removed nor a mention the amendment log keeps")
    if args.counterfactual and not in_17:
        failures.append("ARM 2: counterfactual — an ALTERED fragment must not be findable, and "
                        "its absence must not be read as the removal succeeding")

    # ---- ARM 3 -----------------------------------------------------------------------------
    print("\n  ARM 3 — THE SUPERSESSION IS EXACTLY ONE SENTENCE WIDE (measured against the 0019 "
          "check's OWN table)")
    try:
        import check_blueprint_carried_po_0019_verbatim as sibling
    except ImportError as exc:                                      # pragma: no cover
        print("    UNAVAILABLE: cannot import the 0019 sibling check (%s)" % exc)
        failures.append("ARM 3: the 0019 sibling check could not be imported")
        sibling = None

    if sibling is not None:
        still, gone = [], []
        for label, sentence in sibling.CARRIED:
            (still if normalise(sentence) in bp else gone).append(label)
        print("    0019 sentences still resolving in BLUEPRINT.md : %d/%d"
              % (len(still), len(sibling.CARRIED)))
        for label in gone:
            print("      [SUPERSEDED] %s" % label)
        if gone != [SUPERSEDED_0019_LABEL]:
            failures.append(
                "ARM 3: the supersession is not exactly one sentence wide. Expected exactly "
                "%r to have stopped resolving; got %r" % ([SUPERSEDED_0019_LABEL], gone))
        else:
            print("    EXACTLY ONE, and it is the one PO-DECISIONS-0022 ruling 2 corrects.")
        print("    CONSEQUENCE, DISCLOSED AND NOT HIDDEN: "
              "check_blueprint_carried_po_0019_verbatim.py now exits 1 at %d/%d BY DESIGN. "
              "It is not broken and it must not be edited — it is the standing evidence that the "
              "v0.4.0 text existed and was superseded by the Product Owner and not by a seat."
              % (len(still), len(sibling.CARRIED)))

    # ---- verdict ---------------------------------------------------------------------------
    print()
    if args.counterfactual:
        if failures:
            print("%s: COUNTERFACTUAL PASS — the check FAILED as it must (%d failure(s))"
                  % (CHECK_ID, len(failures)))
            for line in failures:
                print("    %s" % line)
            return 1
        print("%s: COUNTERFACTUAL FAILED — an altered carriage PASSED. THE CHECK IS VACUOUS."
              % CHECK_ID)
        return 1

    if failures:
        print("%s: FAIL" % CHECK_ID)
        for line in failures:
            print("    %s" % line)
        return 1
    print("%s: PASS — ruling 2's correction is the Product Owner's own words, the superseded "
          "prose is out of §17, and exactly one 0019 sentence moved." % CHECK_ID)
    return 0


if __name__ == "__main__":
    sys.exit(main())
