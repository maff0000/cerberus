"""CARRIER for the EXTENDED DISPOSITION VOCABULARY — the register CONTRACT.

WO-2R3 increment 7, ``PO-DECISIONS-0013`` ruling 3.

**THE SPLIT THIS FILE SITS ON.** The Project Lead DRAFTED three words. The Engineer
implements THE CONTRACT THAT ACCEPTS THEM. The Product Owner RATIFIES. The Project Lead then
writes the eleven dispositions in ``tools/sweep/declared_dispositions.py`` — **WHICH IS NOT
THE ENGINEER'S FILE AND IS NOT TOUCHED BY ANY TEST HERE.** Every test below builds a
THROWAWAY COPY of the tree and edits the register THERE, so the contract is exercised
without one word of the eleven being written by this seat (CD-D-130).

**WHAT A CONTRACT IS, AS OPPOSED TO A LABEL SET.** The dispatch's binding constraint:
*"NO NEW WORD MAY BE A SYNONYM FOR 'NOT LOOKED AT'. The instrument must REJECT a disposition
whose mandatory evidence fields are absent."* Each test below asserts that rejection by
CONSTRUCTING the entry that should be rejected.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SWEEP_REL = pathlib.Path("tools") / "sweep" / "delegated_judgement_sweep.py"
_REGISTER_REL = pathlib.Path("tools") / "sweep" / "declared_dispositions.py"


@pytest.fixture()
def a_tree():
    """A throwaway copy carrying `src/`, `tools/` and `governance/findings/`. **The
    repository's own registers are never written to** — only this copy's.

    ``governance/findings/`` joined the copy set at the WO-2R3 RECORD ACT: the sweep now
    resolves the MINIMAL FINDINGS REGISTER (``PO-DECISIONS-0014`` ruling 1) from its own
    location, and a copy without it reports ``FINDINGS_REGISTER_ABSENT`` — correctly, which is
    why the fixture supplies it rather than the check being softened to tolerate its absence.
    """
    root = pathlib.Path(tempfile.mkdtemp(prefix="cd-disp-"))
    for part in ("src", "tools"):
        shutil.copytree(_REPO_ROOT / part, root / part)
    shutil.copytree(
        _REPO_ROOT / "governance" / "findings", root / "governance" / "findings"
    )
    yield root
    shutil.rmtree(root, ignore_errors=True)


def _run(root) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-B", str(root / _SWEEP_REL), "--root", str(root)],
        capture_output=True,
        text=True,
    )


def _add_entry(root, key_literal: str, value_literal: str) -> None:
    """Append one entry to the throwaway copy's DECLARED_ADMISSIONS."""
    register = root / _REGISTER_REL
    register.write_text(
        register.read_text()
        + f"\n\nDECLARED_ADMISSIONS[{key_literal}] = {value_literal}\n"
    )


_A_SITE = (
    '("crash_detector.time_utc", "a_probe_site", "ISINSTANCE", "isinstance(x, int)")'
)


def test_a_word_outside_the_vocabulary_is_rejected(a_tree):
    """**THE HOLE THAT WAS ALREADY THERE, AND IT IS THE REASON THIS CONTRACT EXISTS.**

    Until WO-2R3 increment 7, ``DISPOSITIONS`` was used **only for printing**. A register
    entry carrying a word that was not in it was silently accepted, counted into nothing, and
    never printed — so the one thing the tuple existed to constrain, it did not constrain.
    """
    _add_entry(a_tree, _A_SITE, '("PROBABLY_FINE", "a word nobody agreed")')
    result = _run(a_tree)
    assert result.returncode == 1
    assert "UNKNOWN_DISPOSITION" in result.stdout, result.stdout[-3000:]
    assert "PROBABLY_FINE" in result.stdout


@pytest.mark.parametrize(
    "word, evidence",
    [
        ("DEFECT_OPEN", '{"finding": "F-1", "measured_reach": "one line"}'),
        ("DEFECT_OPEN", '{"finding": "F-1", "measured_reach": "", "counterfactual": "c"}'),
        ("CARRIER_ONLY", '{"callable": "admission_faults"}'),
        ("UPSTREAM_OF_THE_PATH", '{"decides": "whether a door establishes"}'),
    ],
)
def test_an_extended_word_missing_its_evidence_is_rejected(a_tree, word, evidence):
    """**NO NEW WORD MAY BE A SYNONYM FOR "NOT LOOKED AT".**

    Each case omits exactly one mandatory field, or supplies it empty. A word that could be
    used without its evidence would be a label, and a vocabulary of labels is the
    hand-maintained-summary defect ruling 3 exists to prevent.
    """
    _add_entry(a_tree, _A_SITE, f'("{word}", {evidence})')
    result = _run(a_tree)
    assert result.returncode == 1
    assert "DISPOSITION_EVIDENCE_MISSING" in result.stdout, result.stdout[-3000:]


def test_an_extended_word_carrying_only_prose_is_rejected(a_tree):
    """The most likely way the contract would be defeated in practice: use the new word, put
    a sentence where the evidence goes, and let it read as compliance."""
    _add_entry(
        a_tree,
        _A_SITE,
        '("DEFECT_OPEN", "there is a route and it is bad, we measured it, honestly")',
    )
    result = _run(a_tree)
    assert result.returncode == 1
    assert "DISPOSITION_EVIDENCE_MISSING" in result.stdout
    assert "not prose" in result.stdout or "not\nprose" in result.stdout.replace("  ", " ")


def test_a_complete_extended_entry_is_accepted(a_tree):
    """**AND THE OTHER DIRECTION, WITHOUT WHICH THE ABOVE IS SATISFIED BY A CONTRACT THAT
    REJECTS EVERYTHING.** A well-formed entry must not be reported as a contract failure.

    It still leaves the sweep RED, because the site it declares does not exist — which is the
    register's set-equality assertion doing its own job, and a different violation entirely.
    """
    _add_entry(
        a_tree,
        _A_SITE,
        '("DEFECT_OPEN", {"finding": "CD-ASR-WO2R3-05-T8A", '
        '"measured_reach": "one __qualname__ assignment converts a FAULTED door into a '
        'silently-passing one", "counterfactual": "the same code without the assignment '
        'raises UndeclaredParameter"})',
    )
    result = _run(a_tree)
    assert "DISPOSITION_EVIDENCE_MISSING" not in result.stdout, result.stdout[-3000:]
    assert "UNKNOWN_DISPOSITION" not in result.stdout


def test_CARRIER_ONLY_is_an_enumeration_and_fails_when_a_product_caller_appears(a_tree):
    """**THE STRONGEST OF THE THREE WORDS, AND THE ONLY ONE THAT IS MACHINE-CHECKED.**

    The draft: *"AN ENUMERATION, NOT A CLAIM: the register must be able to show that no
    caller exists under ``src/``, by instrument, and FAIL when one appears. A ``CARRIER_ONLY``
    that becomes false when somebody adds an import must break the build the day they add
    it."*

    So: declare `ensure_utc` CARRIER_ONLY — a callable that demonstrably IS called from
    product modules — and require the sweep to say so.
    """
    _add_entry(
        a_tree,
        _A_SITE,
        '("CARRIER_ONLY", {"callable": "ensure_utc", '
        '"why_it_is_not_product_judgement": "asserted, wrongly, for this test"})',
    )
    result = _run(a_tree)
    assert result.returncode == 1
    assert "CARRIER_ONLY_HAS_A_PRODUCT_CALLER" in result.stdout, result.stdout[-3000:]
    assert "ensure_utc" in result.stdout


def test_CARRIER_ONLY_holds_for_a_callable_no_product_module_calls(a_tree):
    """The counterfactual arm. Without it the test above is satisfied by a check that
    reports a caller for everything."""
    _add_entry(
        a_tree,
        _A_SITE,
        '("CARRIER_ONLY", {"callable": "a_name_no_module_under_src_ever_calls", '
        '"why_it_is_not_product_judgement": "its only callers are carriers"})',
    )
    result = _run(a_tree)
    assert "CARRIER_ONLY_HAS_A_PRODUCT_CALLER" not in result.stdout, result.stdout[-3000:]


def test_the_five_original_words_are_unchanged_in_shape(a_tree):
    """**A CONTRACT CHANGE THAT BROKE THE EXISTING REGISTER WOULD HAVE FAILED THE ONE THING
    IT WAS FOR.** The five original words keep `(word, note)` and the population is unmoved.

    **SUPERSEDED IN TWO ASSERTIONS AT THE WO-2R3 RECORD ACT** (`PBG-CONT-003` — corrections
    supersede, never edit). The old text, verbatim:

        assert result.returncode == 1
        assert "534 sites, 15 violations" in result.stdout, (
            "the sweep's own population or violation count moved. The contract change must "
            "not move either — the eleven dispositions are the PROJECT LEAD's and are not "
            "written yet (CD-D-130).")

    It was written at increment 7, when the dispositions were NOT YET WRITTEN and any movement
    in the count meant the contract change had broken something. **THE RECORD ACT WRITES THEM,
    SO THE COUNT MOVES BY CONSTRUCTION** — every one of the fifteen violations is now
    DECLARED. `PO-DECISIONS-0015` ruling 4 ordered exactly that.

    **AND THE ASSERTION THAT REPLACES IT IS NOT "THE SWEEP IS GREEN".** A green exit here is
    ARITHMETIC over the declaration set and this project has been burned four times by a clean
    run being read as evidence of a proposition it says nothing about. So the replacement
    asserts the thing that could actually go wrong: that the POPULATION is what it was last
    MEASURED to be, that the five original words are still accepted, and that **the instrument
    itself prints, on every clean run, what its own zero exit code does and does not mean.**

    **SUPERSEDED AGAIN AT WO-2R3 INCREMENT 8, ITEM 1** (`PBG-CONT-003` — corrections
    supersede, never edit). The text it replaces, verbatim:

        assert "534 sites" in result.stdout, (
            "the sweep's own POPULATION moved. The record act declares sites; it does not
            create or destroy them, and it changed no line under src/.")

    **THAT REASON WAS TRUE OF A RECORD ACT AND IS FALSE OF THIS INCREMENT.** The
    `PO-DECISIONS-0015` ruling 1 redesign of the CD-ASR-F03 control CHANGES LINES UNDER
    ``src/`` by construction — it replaces one wrapper with a derivation — so the population
    moves by construction too. **534 -> 555, MEASURED by running the instrument and not by
    arithmetic on a diff**, and every one of the twenty-one new occurrences is TIER 2 (the
    deciding operation) in ``crash_detector.engine.evaluate``, a module the register already
    derives. **THE ASSERTION THAT ACTUALLY MATTERS IS BESIDE IT AND IS NEW**: not one of them
    is a TIER 1 admission, so this increment added ZERO sites needing a written disposition —
    which is the property that would have been quietly lost if the number alone were bumped.
    ``tools/sweep/declared_dispositions.py`` is untouched by this seat and is outside its
    scope; had a tier-1 site been added, this test would be RED and would have to stay RED.

    ====================================================================================
    **SUPERSEDED A THIRD TIME AT WO-2R3 INCREMENT 10, ITEM_1** (`PBG-CONT-003` —
    corrections supersede, never edit). The two assertions it replaces, verbatim:

        assert "555 sites" in result.stdout, (
            "the sweep's own POPULATION moved. If that was a deliberate product change,
            supersede this number with the MEASURED one and say what moved it; if it was
            not, something changed under src/ that nobody intended.")

        assert "TIER 1 — admission: 45 distinct sites" in result.stdout, (
            "THE TIER 1 ADMISSION POPULATION MOVED. ...")

    **IT WAS A DELIBERATE PRODUCT CHANGE AND THIS IS WHAT MOVED IT.**
    `PO-DECISIONS-0018` ruling 2 ordered the F01 exact-type sweep: *"EXACT TYPE, everywhere
    on a judgement path where an `isinstance` still survives — sites enumerated BY
    INSTRUMENT"*. **TWELVE tier-1 `ISINSTANCE` admissions became exact-type identity tests**,
    which are TIER 2 (`IDENTITY`) and not tier-1 admissions at all. MEASURED by running the
    instrument, not by arithmetic on a diff:

        555 -> 548 sites
        TIER 1 — admission: 45 -> 33 distinct sites (52 -> 40 occurrences)
            ISINSTANCE 30 -> 18      ISSUBCLASS 0 -> 0      DUCK 22 -> 22

    **THE DIRECTION IS THE ONE THAT MATTERS AND IT IS ASSERTED SEPARATELY BELOW: TIER 1
    ONLY EVER GOES DOWN IN THIS INCREMENT.** A tier-1 site carries an obligation — a written
    disposition in a register no Engineer seat owns. Removing one discharges an obligation;
    adding one creates a debt this seat cannot pay. The bound below is an INEQUALITY and not
    a new fingerprint, so a future increment that ADDS an admission is RED here even if it
    also removes one, which a bumped equality would have hidden.

    **AND TWELVE STALE DECLARATIONS ARE THE PRICE, DECLARED AND NOT PAPERED OVER.** Each
    converted site's disposition key names its old SOURCE TEXT, so all twelve are now
    `STALE DECLARATION` in `tools/sweep/declared_dispositions.py` — a file
    `PO-DECISIONS-0018` ruling 3 holds until the remedy clears it IN THE SAME ACT, and which
    this seat has no write access to and took none. The sweep reads
    `FAIL — 548 sites, 18 violations`. **THAT IS THE REGISTER WORKING**: a disposition whose
    reason has died does not survive on habit.
    ====================================================================================
    """
    result = _run(a_tree)
    assert "UNKNOWN_DISPOSITION" not in result.stdout
    assert "DISPOSITION_EVIDENCE_MISSING" not in result.stdout
    assert "MALFORMED_DISPOSITION" not in result.stdout
    # **SUPERSEDED A FOURTH TIME AT WO-3 INCREMENT 16A** (`PBG-CONT-003` — corrections
    # supersede, never edit). The assertion it replaces, verbatim:
    #
    #     assert "548 sites" in result.stdout, (
    #         "the sweep's own POPULATION moved. If that was a deliberate product change,
    #         supersede this number with the MEASURED one and say what moved it; if it was
    #         not, something changed under src/ that nobody intended.")
    #
    # **IT WAS A DELIBERATE PRODUCT CHANGE, AND THIS SUPERSESSION IS DONE THE WAY THAT
    # ASSERTION'S OWN TEXT INSTRUCTS.** `PO-DECISIONS-0025` r1/r2/r6 requires the
    # indicator->dial mapping to exist as REGISTRY DATA, and WO-3 increment 16A added the
    # carrier — the three enums, the record, the registry, the refusals and the loader — to
    # `crash_detector.source_registry`. **SIXTY-TWO NEW TIER-2 SITES AND NOT ONE NEW TIER-1
    # ADMISSION.** MEASURED by running the instrument on both trees, never by arithmetic on
    # a diff:
    #
    #     baseline 116c01f   PASS — 548 sites over 19 modules   TIER 1: 33 (ISINSTANCE 18)
    #     this SHA           PASS — 610 sites over 19 modules   TIER 1: 33 (ISINSTANCE 18)
    #
    # **THE MODULE COUNT IS UNCHANGED AT 19, AND THAT IS THE LOAD-BEARING HALF.** The carrier
    # was FIRST written as a companion module `crash_detector/indicator_mapping.py`, and this
    # instrument caught it: a new module enters the judgement closure UNDECLARED and takes
    # this control from PASS to FAIL — measured, `FAIL — 610 sites, 1 violations`. The only
    # remedy, a `DECLARED_MODULE_DISPOSITIONS` entry or a complete per-site declaration,
    # lives in `tools/sweep/declared_dispositions.py`: the Project Lead's register, held by
    # `PO-DECISIONS-0018` ruling 3 and outside any Engineer seat's scope. **THE CODE WAS
    # MOVED INTO A MODULE THAT ALREADY CARRIES AN ESTABLISHED DISPOSITION RATHER THAN THE
    # REGISTER BEING EDITED TO ACCEPT IT.** The control did its job and the code moved.
    assert "610 sites" in result.stdout, (
        "the sweep's own POPULATION moved. If that was a deliberate product change, "
        "supersede this number with the MEASURED one and say what moved it; if it was not, "
        "something changed under src/ that nobody intended.\n" + result.stdout[-3000:]
    )
    # **THE MODULE POPULATION IS PINNED FROM THIS INCREMENT, BECAUSE THE TOTAL CANNOT SEE
    # IT.** A new module carries an obligation payable only in a register no Engineer seat
    # owns — exactly as a tier-1 site does — so it is asserted separately for the same
    # reason, and as an INEQUALITY so that removing one and adding another cannot go green.
    assert "over 19 modules" in result.stdout, (
        "THE SUBJECT MODULE POPULATION MOVED. A module entering the judgement closure needs "
        "a DECLARED_MODULE_DISPOSITIONS entry or a complete per-site declaration in "
        "tools/sweep/declared_dispositions.py — the Project Lead's register, held by "
        "PO-DECISIONS-0018 ruling 3. AN ENGINEER SEAT THAT ADDS A MODULE CANNOT DISCHARGE "
        "THE OBLIGATION IT CREATES, so this is not a number an Engineer may bump: it is a "
        "stop-and-report. 19 was measured at WO-3 increment 16A.\n" + result.stdout[-3000:]
    )
    # **THE TIER-1 POPULATION IS THE ONE THAT CARRIES AN OBLIGATION, AND IT IS PINNED
    # SEPARATELY SO THAT A BUMP TO THE TOTAL CANNOT HIDE A NEW UNDECLARED ADMISSION.**
    # A tier-1 site needs a written disposition in a register no Engineer seat owns; a tier-2
    # occurrence derives from its module. Bumping only the total would let the first hide
    # inside the second.
    #
    # **AS AN INEQUALITY, NOT AN EQUALITY, AS OF INCREMENT 10.** An equality here would go
    # green for a change that removes one admission and adds another, which is precisely the
    # move it exists to catch. Parsed from the instrument's own line, never counted by eye.
    import re as _re

    tier_1 = _re.search(r"TIER 1 — admission: (\d+) distinct sites", result.stdout)
    assert tier_1, "the instrument stopped printing its tier-1 population\n" + result.stdout[-3000:]
    assert int(tier_1.group(1)) <= 33, (
        "THE TIER 1 ADMISSION POPULATION GREW. Every tier-1 site needs its own written "
        "disposition in tools/sweep/declared_dispositions.py, which is the Project Lead's "
        "register. A change that adds one is not a change that may bump a number here — "
        f"33 was the measured ceiling at WO-2R3 increment 10, and this run reports "
        f"{tier_1.group(1)}.\n" + result.stdout[-3000:]
    )
    isinstance_line = _re.search(r"ISINSTANCE\s+(\d+)", result.stdout)
    assert isinstance_line and int(isinstance_line.group(1)) <= 18, (
        "THE SURVIVING `isinstance` POPULATION GREW. PO-DECISIONS-0018 ruling 2 requires "
        "EXACT TYPE at every judgement-path admission where one can be taken; 18 is the "
        "measured residue at WO-2R3 increment 10, each with a written reason.\n"
        + result.stdout[-3000:]
    )
    if result.returncode == 0:
        assert "A REGISTER FULL OF `DEFECT_OPEN` BUYS NOTHING" in result.stdout, (
            "the sweep exited 0 WITHOUT saying what that does not mean. **THIS IS THE "
            "ASSERTION THAT MATTERS.** A zero here is arithmetic over the declaration set: "
            "ten sites are declared OPEN DEFECTS and not one of them is fixed.\n"
            + result.stdout[-3000:]
        )
        assert "ARITHMETIC over the declaration set" in result.stdout


def test_every_extended_word_is_printed_even_at_zero(a_tree):
    """A vocabulary a reader cannot see is a vocabulary nobody will use correctly. All eight
    words are printed with their counts.

    **SUPERSEDED IN ONE ASSERTION AT THE WO-2R3 RECORD ACT, AND THE OLD TEXT IS QUOTED HERE
    RATHER THAN DELETED** (`PBG-CONT-003` — corrections supersede, never edit). It read:

        assert "EXTENDED, PO RATIFICATION PENDING" in result.stdout

    written when the three words were the Project Lead's DRAFT and the marker existed *"so no
    reader mistakes drafted for ruled"*. `PO-DECISIONS-0014` ruling 1 RATIFIED `CARRIER_ONLY`
    as drafted, RATIFIED `DEFECT_OPEN` with the findings register attached, and REDRAFTED
    `UPSTREAM_OF_THE_PATH`. **The marker is now the false statement it was written to
    prevent**, so it is gone and the assertion follows it. The word EXTENDED is kept, because
    the shape difference it names — `(word, evidence mapping)` and not `(word, note)` — did
    not change.
    """
    result = _run(a_tree)
    for word in ("DEFECT_OPEN", "CARRIER_ONLY", "UPSTREAM_OF_THE_PATH"):
        assert word in result.stdout
    assert "(EXTENDED)" in result.stdout
    assert "PO RATIFICATION PENDING" not in result.stdout, (
        "the three words were ratified or redrafted by PO-DECISIONS-0014 ruling 1; a marker "
        "saying otherwise is a stale claim in the instrument's own output.\n"
        + result.stdout[:4000]
    )
    assert "words used that are NOT in the vocabulary: 0" in result.stdout
