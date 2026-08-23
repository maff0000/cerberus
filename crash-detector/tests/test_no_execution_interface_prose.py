"""**THE PAIRED CONTRAST `PO-DECISIONS-0015` RULING 3 MADE THE CONDITION OF THE CORRECTION.**

The ruling, verbatim:

    *"CD-RT-012: CORRECT THE FALSE POSITIVE — IF AND ONLY IF the correction carries its own
    contrast. The L3 prose reading is corrected together with a paired demonstration that a
    TRUE violation of the same clause is still caught (baseline/violated arms — the axis
    discipline of IMP-024). If that contrast cannot be produced, the violation is DECLARED the
    way the Class-2 sweep's is."*

THE FALSE POSITIVE
------------------
``tests/test_tree_fingerprint.py:61`` carries a sentence in which a governance record tells a
person to run a test. ``dispatch`` is a ``TRANSMISSION_VERB`` and ``orders`` is a
``TRADEABLE_NOUN``, so L3's pattern A — verb, filler, tradeable noun — read the two words as a
claim about what the code does, and ``CD-RT-012-NO-EXECUTION-INTERFACE`` shipped **EXIT 1**. It
went ``EXIT 0`` -> ``EXIT 1`` inside increment 7 and no document said so until an auditor ran
one command (``F-06-A``).

THE AXIS, AND IT IS ONE VARIABLE
--------------------------------
In that sentence the first word is a NOUN and the second is a VERB — the two roles pattern A
assigned are exactly swapped. A determiner introduces a NOUN PHRASE, so the word immediately
after it is that phrase's head noun and not the sentence's finite verb. **INSERTING A SUBJECT
NOUN BETWEEN THE DETERMINER AND THE TRANSMISSION VERB RESTORES THE VIOLATION**, and that is
the one variable every arm below moves.

THREE NARROWINGS, EACH WITH ITS OWN ARM, BECAUSE A CORRECTION MUST NOT BE A WORD BAN
-------------------------------------------------------------------------------------
1. the determiner set EXCLUDES every determiner that can also be a subject pronoun — ``this``,
   ``that``, ``these``, ``those``, ``each``, ``one``, ``some``;
2. the suppression does not apply to a participial or gerund form, so a noun phrase ABOUT
   instructions being moved is untouched;
3. **the suppression does not apply at all to a sentence that NAMES A PARTY THAT ACTS ON
   INSTRUCTIONS.** This one exists because the residue was MEASURED and not reasoned about:
   without it, the suppressed shape with a party named in it went clean.

**WHAT THE CORRECTION STILL DOES NOT CATCH IS ASSERTED HERE TOO**, in
:func:`test_the_residue_of_this_correction_is_declared_and_measured`, so the declared limit
cannot go stale in the reassuring direction.

WHY EVERY ARM IS ASSEMBLED FROM WORDS AT RUNTIME AND NOT WRITTEN AS A SENTENCE
------------------------------------------------------------------------------
**THIS FILE IS INSIDE THE SCANNED SET.** A carrier for L3 that spelled its arms as literal
sentences would put nine true execution-interface declarations into ``tests/`` and take the
register RED on its own evidence — **MEASURED: 11 violations, EXIT 1**, on the first draft of
this file. The two ways out are to EXCLUDE this file from the check, which widens the guard's
blind spot in order to test the guard, or to assemble the arms from single words, which L3
cannot read because ``_judge_sentence`` refuses a fragment of fewer than two words. **THE
SECOND COSTS THE GUARD NOTHING AND IS TAKEN.** No arm below is weaker for it: the string handed
to ``judge_prose`` is byte-for-byte the sentence, built one word earlier.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

sys.path.insert(
    0, str(pathlib.Path(__file__).resolve().parent.parent / "tools" / "register")
)

from _broker_vocabulary import judge_prose  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _sentence(*words: str) -> str:
    """Join single words into the arm. See this module's docstring for why."""
    return " ".join(words)


#: THE SENTENCE THE REGISTER ACTUALLY SHIPPED RED ON, rebuilt word by word from the artefact.
THE_FALSE_POSITIVE = _sentence(
    "which", "is", "created", "by", "running", "pytest", "which", "the",
    "dispatch", "ORDERS", "the", "auditor", "to", "do",
)

#: THE PAIRED ARM, ON THE EXACT AXIS. The same determiner, the same transmission verb and the
#: same tradeable noun as the false positive, with a SUBJECT NOUN inserted between the first
#: two. If this reads clean, the correction is not a grammatical narrowing — it is a hole.
THE_PAIRED_TRUE_VIOLATION = _sentence(
    "which", "the", "client", "dispatches", "orders", "to", "the", "broker",
)


def test_the_baseline_arm_the_corrected_reading_lets_the_false_positive_through():
    """**BASELINE ARM.** The sentence the register shipped RED on now reads CLEAN."""
    assert judge_prose(THE_FALSE_POSITIVE) is None, judge_prose(THE_FALSE_POSITIVE)


def test_the_violated_arm_the_same_shape_with_a_subject_is_still_caught():
    """**THE ARM THE RULING REQUIRES.** One variable, both directions.

    A correction that could not survive this would be an exemption for a shape rather than a
    reading of a grammar, and `PO-DECISIONS-0012` ruling 3 forbids exemptions as a route to
    green — a prohibition `PO-DECISIONS-0015` did not touch.
    """
    verdict = judge_prose(THE_PAIRED_TRUE_VIOLATION)
    assert verdict is not None, (
        "THE PAIRED TRUE VIOLATION WENT CLEAN. The two arms differ in exactly one word — a "
        "subject noun between the determiner and the transmission verb — so if both read "
        "clean the correction has removed the clause rather than corrected it."
    )
    assert "active voice" in verdict[0]


@pytest.mark.parametrize(
    "words, narrowing",
    [
        (
            ("This", "module", "routes", "orders", "to", "the", "broker", "for", "execution"),
            "the ordinary active-voice violation, untouched",
        ),
        (
            ("Route", "an", "order", "to", "the", "broker", "for", "execution"),
            "the archetype CD-PL-F32 was raised about, and the sentence CD-ENG-F36's "
            "correction restored",
        ),
        (
            ("This", "dispatches", "orders", "to", "the", "venue"),
            "NARROWING 1: `this` is a determiner AND a subject pronoun, so it is deliberately "
            "absent from the suppression set",
        ),
        (
            ("Each", "forwards", "orders", "to", "the", "desk"),
            "NARROWING 1 again, with `each` — the other determiner that can stand as a subject",
        ),
        (
            ("The", "dispatch", "orders", "to", "the", "broker"),
            "NARROWING 3, AND IT WAS MEASURED RATHER THAN REASONED ABOUT: this arm went CLEAN "
            "before the party condition was added. A sentence naming a party that acts on "
            "instructions is never given the benefit of a grammatical doubt",
        ),
        (
            ("the", "routed", "orders", "reached", "the", "broker"),
            "NARROWING 2: a participial form after a determiner names a phrase ABOUT "
            "instructions being moved, and the suppression does not reach it",
        ),
        (
            ("Each", "bargain", "was", "routed", "to", "the", "desk"),
            "the PASSIVE pattern, which this correction does not go near",
        ),
        (
            ("order", "routing", "to", "the", "exchange"),
            "the NOMINALISED pattern, which this correction does not go near",
        ),
        (
            ("the", "bargain", "clears", "through", "the", "exchange"),
            "the TRADE-LIFECYCLE pattern, which this correction does not go near",
        ),
    ],
)
def test_the_violated_arm_a_true_declaration_in_prose_is_still_caught(words, narrowing):
    """**VIOLATED ARM, NINE MORE.** Every true declaration still caught, and each names which
    narrowing keeps it caught, so a reader can see that the correction is bounded rather than
    take it on the word "narrow"."""
    built = _sentence(*words)
    assert judge_prose(built) is not None, f"{built!r} went CLEAN. {narrowing}"


def test_the_residue_of_this_correction_is_declared_and_measured():
    """**WHAT THE CORRECTION STILL DOES NOT CATCH, ASSERTED TRUE SO IT CANNOT GO STALE.**

    The suppressed shape, with NO party named anywhere in the sentence, reads clean. It is a
    strained sentence and it is a real residue, and this project's most-found defect is a
    declaration that is wrong in the reassuring direction.

    **IF THIS TEST EVER FAILS, THE CORRECTION HAS BECOME NARROWER THAN ITS DECLARATION AND THE
    DECLARED LIMIT MUST BE CORRECTED IN ALL THREE CD-RULE-004 PLACES RATHER THAN QUIETLY
    ENJOYED.**
    """
    residue = _sentence("The", "dispatch", "orders", "the", "childorder")
    assert judge_prose(residue) is None, (
        "the residue named in this correction's declared limit is closed. That is good news "
        "and it is still a documentation defect until the limit is corrected in all three "
        "CD-RULE-004 places."
    )


def _run_the_check_over(tree: pathlib.Path):
    return subprocess.run(
        [sys.executable, "-B", str(tree / "tools" / "register" /
                                   "check_no_execution_interface.py"), "--root", str(tree)],
        capture_output=True,
        text=True,
    )


def test_the_register_row_is_green_and_a_planted_true_declaration_takes_it_red():
    """**CD-RULE-006: A CHECK REPORTS, A CARRIER FAILS — SO THE CARRIER RUNS THE CHECK.**

    A reading is not a register row. Two arms over the same throwaway tree, reading THAT
    tree's own copy of the instrument (CD-PL-F98):

    * the shipped tree: **EXIT 0**;
    * the same tree with ONE comment added, assembled word by word and written into a product
      module, saying in the active voice that the code moves instructions to a party that acts
      on them: **EXIT 1**.

    Without the second arm the first is satisfied by a check that reads nothing.
    """
    tree = pathlib.Path(tempfile.mkdtemp(prefix="cd-rt012-"))
    try:
        for part in ("src", "tools", "tests", "db", "deploy"):
            source = _REPO_ROOT / part
            if source.is_dir():
                shutil.copytree(
                    source, tree / part, ignore=shutil.ignore_patterns("__pycache__")
                )
        clean = _run_the_check_over(tree)
        assert clean.returncode == 0, (
            "THE SHIPPED TREE IS STILL RED. Either the correction did not reach the code "
            "path, or this increment introduced prose of its own that the guard reads.\n"
            + clean.stdout[-4000:]
        )

        planted = tree / "src" / "crash_detector" / "time_utc.py"
        planted.write_text(
            planted.read_text()
            + "\n# "
            + _sentence("The", "gateway", "dispatches", "orders", "to", "the", "broker")
            + "\n"
        )
        red = _run_the_check_over(tree)
        assert red.returncode == 1, (
            "A TRUE EXECUTION-INTERFACE DECLARATION IN PROSE WAS PLANTED AND THE CHECK "
            "PASSED. The correction is a hole, not a narrowing.\n" + red.stdout[-4000:]
        )
        assert "execution interface declared in prose" in red.stdout, red.stdout[-4000:]
    finally:
        shutil.rmtree(tree, ignore_errors=True)
