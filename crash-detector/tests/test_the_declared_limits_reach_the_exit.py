"""CARRIER — **THE DECLARED LIMITS REACH THE EXIT, ON EVERY PATH, AND CAN BE MADE TO VANISH.**

``PO-DECISIONS-0018`` ruling 1(b), the Product Owner's own bytes:

    *"The instrument's exit carries its declared limit ... A green board that says exactly that
    is honest; a green board that says more is the sixth false green."*

**A DOCSTRING IS NOT AN EXIT, AND AN EXIT NOTHING WATCHES IS A DOCSTRING WITH EXTRA STEPS.**
WO-2R3 increment 10 moved two declared limits out of module docstrings and into stdout:

* ``CD-RT-002-SEALED-AGAINST-FORGED-ESTABLISHMENT`` DECLARED LIMIT 7 — what ``SEALED`` means and
  what it does not, with that run's own measured forgery counts;
* ``CD-CLASS-2-SWEEP`` DECLARED LIMIT 5 — ``CD-D-166``, the ``gates`` field, unsound in BOTH
  directions, with the measured numbers for each.

Both are printed from a ``finally``, which is a claim about EVERY exit path and not just the
happy one. **THAT CLAIM IS WHAT THIS FILE MEASURES**, and it measures it the only way that
means anything: by asserting the text is there on four exit codes AND by DELETING the print
from a throwaway copy and watching the same assertions fail.

Without that last arm this file would be a test that cannot fail — the rumour the Standards
Baseline §7 names. **THE COUNTERFACTUAL IS THE TEST; THE REST IS BOOKKEEPING.**

**IT ALSO PINS THE ORDER.** The limit must come AFTER the verdict line, because the failure it
exists to prevent is a reader who runs the check and reads its LAST line. A limit printed
before the verdict is a limit the verdict scrolls off the screen.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SEALING_REL = pathlib.Path("tools") / "register" / "check_sealed_against_forged_establishment.py"
_SWEEP_REL = pathlib.Path("tools") / "sweep" / "delegated_judgement_sweep.py"

#: The exact `finally` line each instrument prints its limit from. Deleting it is the
#: counterfactual, and naming it here means the arm breaks loudly if either file is
#: restructured rather than silently deleting nothing and still "passing".
_THE_PRINT = {
    _SEALING_REL: "        print(_declared_limit_text())",
    _SWEEP_REL: "        print(_declared_limit_5_text())",
}


@pytest.fixture()
def a_tree():
    """A throwaway copy of the tree. **NEVER the repository itself** (`CD-PL-F98`)."""
    root = pathlib.Path(tempfile.mkdtemp(prefix="cd-limits-"))
    for part in ("src", "tools"):
        shutil.copytree(_REPO_ROOT / part, root / part)
    shutil.copytree(
        _REPO_ROOT / "governance" / "findings", root / "governance" / "findings"
    )
    yield root
    shutil.rmtree(root, ignore_errors=True)


def _run(tree: pathlib.Path, relative: pathlib.Path, *arguments):
    return subprocess.run(
        [sys.executable, "-B", str(tree / relative), *arguments],
        capture_output=True,
        text=True,
        cwd=str(tree),
    )


def _remove_the_print(tree: pathlib.Path, relative: pathlib.Path) -> None:
    """Delete the one line that prints the limit. The tree keeps working; only the limit goes."""
    path = tree / relative
    line = _THE_PRINT[relative]
    text = path.read_text(encoding="utf-8")
    assert text.count(line + "\n") == 1, (
        f"{relative} no longer contains exactly one `{line.strip()}` — this counterfactual "
        "cannot prove anything about a file it did not modify, so it REFUSES rather than "
        "deleting nothing and reporting a pass."
    )
    path.write_text(text.replace(line + "\n", "        pass\n"), encoding="utf-8")


# ======================================================================================= #
# THE SEALING INSTRUMENT — DECLARED LIMIT 7, ON FOUR EXIT CODES.
# ======================================================================================= #

#: **EVERY MARKER MUST BE UNIQUE TO THE EXIT BLOCK.** The bare string "DECLARED LIMIT 7" also
#: appears in the check's own `scanned:` summary line, which is printed by `Check.done` and NOT
#: by the `finally` — so a counterfactual keyed on it would find the summary, conclude the limit
#: survived deletion, and report a failure that is really its own sloppiness.
_SEALED_MARKERS = (
    "DECLARED LIMIT 7 — PRINTED AFTER THE VERDICT",
    "SEALED AGAINST DECLARED ROUTES",
    "NOT** SEALED AGAINST DELIBERATE IN-PROCESS",
    "WHICH THE PLATFORM DOES NOT PERMIT PREVENTING",
)


def test_the_sealing_exit_carries_the_limit_on_a_PASS_and_AFTER_the_verdict(a_tree):
    """Exit 0. **AND THE LIMIT COMES AFTER THE VERDICT LINE**, which is the whole point."""
    result = _run(a_tree, _SEALING_REL, "--root", ".")
    assert result.returncode == 0, result.stdout[-3000:]
    for marker in _SEALED_MARKERS:
        assert marker in result.stdout, f"{marker}\n{result.stdout[-3000:]}"
    verdict = result.stdout.index("SEALED-AGAINST-FORGED-ESTABLISHMENT: PASS —")
    assert result.stdout.index("DECLARED LIMIT 7 — PRINTED AFTER THE VERDICT") > verdict, (
        "the limit was printed BEFORE the verdict. A reader runs the check and reads its "
        "LAST line; a limit the verdict scrolls past is a limit nobody reads."
    )


def test_the_sealing_exit_carries_the_limit_on_a_PRECONDITION_REFUSAL_with_no_invented_number(
    a_tree,
):
    """Exit 3. **AND IT PRINTS NO MEASUREMENT, BECAUSE NO MEASUREMENT WAS TAKEN** (`CD-RULE-003`)."""
    empty = a_tree / "not-a-repository"
    empty.mkdir()
    result = _run(a_tree, _SEALING_REL, "--root", str(empty))
    assert result.returncode == 3, result.stdout[-3000:]
    assert "DECLARED LIMIT 7 — PRINTED AFTER THE VERDICT" in result.stdout
    assert "**NO PERIMETER" in result.stdout
    assert "MEASUREMENT WAS TAKEN ON THIS RUN**" in result.stdout
    assert "classes examined were forged by" not in result.stdout, (
        "a run that measured nothing printed a forgery count. A number this run did not "
        "derive is a number this run invented."
    )


def test_the_sealing_exit_carries_the_limit_on_a_USAGE_error(a_tree):
    """Exit 2, from argparse's own ``SystemExit``. The ``finally`` survives it."""
    result = _run(a_tree, _SEALING_REL)
    assert result.returncode == 2, (result.stdout + result.stderr)[-3000:]
    assert "DECLARED LIMIT 7 — PRINTED AFTER THE VERDICT" in result.stdout


def test_the_sealing_exit_says_the_HONEST_COUNT_and_names_what_it_does_not_claim(a_tree):
    """**THE NUMBER IS THE POINT.** A limit without one is an adjective."""
    result = _run(a_tree, _SEALING_REL, "--root", ".")
    assert "classes examined were forged by" in result.stdout
    assert "THIS CHECK CALLS SEALED" in result.stdout
    assert "VACUOUSLY TRUE OF A STATELESS OBJECT" in result.stdout
    assert "THE HONEST COUNT OF THOSE IS ZERO" in result.stdout, result.stdout[-3000:]
    assert "NOT that CD-ASR-WO2R3-04-F01 is closed" in result.stdout
    assert "IT IS NOT BUILT YET" in result.stdout, "the WO-3 detection obligation is owed, not done"


def test_DELETING_THE_PRINT_MAKES_EVERY_SEALING_ASSERTION_ABOVE_FAIL(a_tree):
    """**THE COUNTERFACTUAL.** Without this arm the four tests above cannot fail (`CD-D-079`)."""
    _remove_the_print(a_tree, _SEALING_REL)
    result = _run(a_tree, _SEALING_REL, "--root", ".")
    assert result.returncode == 0, "the tree must still WORK; only the limit is gone"
    assert "PASS — 99 assertions" in result.stdout or "PASS —" in result.stdout
    for marker in _SEALED_MARKERS:
        assert marker not in result.stdout, (
            f"{marker} survived deleting the only line that prints it, so the tests above "
            "were passing on some other text and prove nothing."
        )


# ======================================================================================= #
# THE CLASS-2 SWEEP — DECLARED LIMIT 5, ON THE **FAIL** PATH.
#
# **THIS IS THE ARM THAT MATTERS MOST HERE.** Before increment 10 the sweep's only declared-
# limit text was on its `return 0` path: a limit that appeared when the board was green and
# vanished when it was not — the wrong way round, because a reader looking at a FAIL is
# exactly the reader about to decide what the failure means.
# ======================================================================================= #

_SWEEP_MARKERS = (
    "DECLARED LIMIT 5",
    "THIS FIELD IS UNSOUND IN BOTH DIRECTIONS AT ONCE",
    "IT REFUSES WHEN NOTHING IS WRONG",
    "IT PASSES WHEN THE CLAIM IS FALSE",
    "IT IS A POINTER THAT ROTS LOUDLY",
)


def test_the_sweep_exit_carries_CD_D_166s_limit_AFTER_the_verdict_whatever_the_verdict_is(a_tree):
    result = _run(a_tree, _SWEEP_REL, "--root", ".")
    for marker in _SWEEP_MARKERS:
        assert marker in result.stdout, f"{marker}\n{result.stdout[-3000:]}"
    verdict = max(
        result.stdout.rfind("CD-CLASS-2-SWEEP: FAIL"),
        result.stdout.rfind("CD-CLASS-2-SWEEP: PASS"),
    )
    assert verdict != -1, result.stdout[-3000:]
    assert result.stdout.index("DECLARED LIMIT 5") > verdict, (
        "the limit was printed BEFORE the verdict line."
    )


def test_the_sweep_limit_states_BOTH_directions_with_their_numbers(a_tree):
    """**A DECLARED LIMIT THAT ONLY ADMITS THE FLATTERING HALF IS NOT A DECLARATION.**"""
    result = _run(a_tree, _SWEEP_REL, "--root", ".")
    assert "31\n    GATES-SITE-DOES-NOT-EXIST refusals" in result.stdout, result.stdout[-3000:]
    assert "ZERO refusals and a bit-for-bit unmoved verdict" in result.stdout
    assert "183\n    product tests still passing" in result.stdout
    assert "NOT PROVED TO BE CARRIED\n  ANYWHERE" in result.stdout


def test_the_sweep_limit_DERIVES_its_live_numbers_rather_than_transcribing_them(a_tree):
    """The rejected clause's kill-number is re-derived at every run, not written down."""
    result = _run(a_tree, _SWEEP_REL, "--root", ".")
    assert "LIVE IN THIS RUN, DERIVED NOW AND NOT TRANSCRIBED" in result.stdout
    assert "`UPSTREAM_OF_THE_PATH`\n    row(s) in the site register" in result.stdout
    assert "THE NUMBER THAT KILLED THE CANDIDATE CLAUSE" in result.stdout


def test_the_sweep_limit_DOES_NOT_REPRODUCE_a_rule_token_that_could_be_grepped_for(a_tree):
    """**CD-ENG-WO2R3-09-F03, kept as a test rather than as a memory.**

    The first draft of this block spelled the refusal rule with underscores, and four tests in
    ``tests/test_upstream_of_the_path.py`` — which assert those rule names are ABSENT from a
    clean run's stdout — went red. A paragraph EXPLAINING a rule must not answer a grep for a
    rule that FIRED. The text was changed; the tests were not.
    """
    result = _run(a_tree, _SWEEP_REL, "--root", ".")
    limit = result.stdout[result.stdout.index("DECLARED LIMIT 5"):]
    for token in (
        "GATES_SITE_DOES_NOT_EXIST",
        "GATES_SITE_IS_IN_THE_DECLARING_MODULE",
        "OPERAND_ORIGIN_NOT_IN_THE_CLOSED_SET",
        "CALLER_SUPPLIED_WITHOUT_A_FINDING",
        "DISPOSITION_EVIDENCE_MISSING",
        "FINDING_DOES_NOT_RESOLVE",
        "FINDING_IS_NOT_OPEN",
    ):
        assert token not in limit, f"the limit block reproduces the rule token {token}"


def test_DELETING_THE_PRINT_MAKES_EVERY_SWEEP_ASSERTION_ABOVE_FAIL(a_tree):
    """**THE COUNTERFACTUAL**, again, and it is the same argument."""
    _remove_the_print(a_tree, _SWEEP_REL)
    result = _run(a_tree, _SWEEP_REL, "--root", ".")
    assert "CD-CLASS-2-SWEEP:" in result.stdout, "the tool must still WORK"
    for marker in _SWEEP_MARKERS:
        assert marker not in result.stdout, (
            f"{marker} survived deleting the only line that prints it."
        )
