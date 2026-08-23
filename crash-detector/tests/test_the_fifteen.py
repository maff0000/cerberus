"""CARRIER for THE FIFTEEN — ``PO-DECISIONS-0015`` ruling 4, the WO-2R3 record act.

    *"THE ONE ACT DISPOSITIONS FIFTEEN, NOT ELEVEN … the instrument's count beats the ruling's
     prose … Category C's six sites are RE-DISPOSITIONED: their stated ground is falsified by
     CD-PL-F103, and a disposition whose reason has died does not survive on habit."*

**THE SWEEP GOES FROM EXIT 1 TO EXIT 0 IN THIS ACT AND THAT IS ARITHMETIC.** Every one of its
fifteen violations is now DECLARED. Nothing is fixed, no line under ``src/`` moved, and ten of
the thirteen site rows say `DEFECT_OPEN` — a register honestly describing a system with ten
open defects. **The tests below are written so that not one of them can be satisfied by the
exit code**, and one of them exists purely to assert that the instrument prints what its own
zero does not mean.

**AND THE DERIVATION IS EXERCISED HERE ON THE REAL SUBJECT, NOT ON A CONVENIENT ONE.**
``tests/test_upstream_of_the_path.py`` proves the derivation mechanism on the smallest module
in the closure. That is the mechanism, not the act. Below, ONE ROW is removed from each of the
two modules this act actually derives — 33 keys and 17 keys — and each must go UNDECLARED.
"""

from __future__ import annotations

import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SWEEP_REL = pathlib.Path("tools") / "sweep" / "delegated_judgement_sweep.py"
_REGISTER_REL = pathlib.Path("tools") / "sweep" / "declared_dispositions.py"

_DERIVED_MODULES = ("crash_detector.admission", "crash_detector.establishment")

#: The thirteen tier-1 sites of the fifteen, and the word each one must carry. Written out
#: rather than computed, because a test that derives its expectation from the thing it is
#: testing asserts nothing.
_THE_THIRTEEN = {
    # Category A — one site.
    ("crash_detector.admission", "_is_defined_in_a_class_body", "DUCK",
     "getattr(entry_point, '__qualname__', '')"): "DEFECT_OPEN",
    # Category B — three sites, ratified as drafted.
    ("crash_detector.admission", "admission_faults", "DUCK",
     "getattr(door, FAULTS_ATTRIBUTE, ())"): "CARRIER_ONLY",
    ("crash_detector.admission", "declared_admissions", "DUCK",
     "getattr(door, ADMITS_ATTRIBUTE, {})"): "CARRIER_ONLY",
    ("crash_detector.admission", "is_admitting_door", "DUCK",
     "hasattr(door, ADMITS_ATTRIBUTE)"): "CARRIER_ONLY",
    # Category C — six sites, REVERSED from the draft's OUT_OF_BOUND.
    ("crash_detector.admission", "_EstablishedHere.__call__", "ISINSTANCE",
     "isinstance(because, str)"): "DEFECT_OPEN",
    ("crash_detector.admission", "_compile", "ISINSTANCE",
     "isinstance(declaration, _Admission)"): "DEFECT_OPEN",
    ("crash_detector.admission", "_compile", "ISINSTANCE",
     "isinstance(declaration, tuple)"): "DEFECT_OPEN",
    ("crash_detector.admission", "_compile", "ISINSTANCE",
     "isinstance(declaration, type)"): "DEFECT_OPEN",
    ("crash_detector.admission", "_type_tuple", "ISINSTANCE",
     "isinstance(value, type)"): "DEFECT_OPEN",
    ("crash_detector.admission", "each_of", "ISINSTANCE",
     "isinstance(within, tuple)"): "DEFECT_OPEN",
    # The three establishment sites, read for the first time at the issuing boundary.
    ("crash_detector.establishment", "_declared_field_list", "DUCK",
     "getattr(cls, '__dataclass_fields__', {})"): "DEFECT_OPEN",
    ("crash_detector.establishment", "_declared_field_list", "DUCK",
     "getattr(field._field_type, 'name', '')"): "DEFECT_OPEN",
    ("crash_detector.establishment", "establishes.apply_at_the_boundary.__init__", "DUCK",
     "getattr(self, name, _ABSENT)"): "DEFECT_OPEN",
}


@pytest.fixture()
def a_tree():
    root = pathlib.Path(tempfile.mkdtemp(prefix="cd-fifteen-"))
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


def _load(root):
    """The COPY's own sweep and the COPY's own register (CD-PL-F98 — never assume two arms
    read the same tree)."""
    spec = importlib.util.spec_from_file_location("_fifteen_sweep", root / _SWEEP_REL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    namespace: dict = {"__file__": str(root / _REGISTER_REL), "__name__": "declared_dispositions"}
    exec(compile((root / _REGISTER_REL).read_text(), str(root / _REGISTER_REL), "exec"), namespace)
    return module, namespace["DECLARED_ADMISSIONS"], namespace["DECLARED_MODULE_DISPOSITIONS"]


def _append(root, source: str) -> None:
    register = root / _REGISTER_REL
    register.write_text(register.read_text() + "\n\n" + source + "\n")


# ------------------------------------------------------------------------------------- #
# THE THIRTEEN SITES, BY NAME AND BY WORD.
# ------------------------------------------------------------------------------------- #


@pytest.mark.parametrize("key, word", sorted(_THE_THIRTEEN.items()))
def test_each_of_the_thirteen_sites_carries_the_word_the_ruling_gave_it(a_tree, key, word):
    """One test per site, so a failure names the site rather than a count."""
    _module, admissions, _modules = _load(a_tree)
    assert key in admissions, f"{key} is not in the register at all"
    assert admissions[key][0] == word, f"{key} carries {admissions[key][0]!r}, not {word!r}"


def test_the_six_Category_C_sites_are_no_longer_OUT_OF_BOUND(a_tree):
    """**THE REVERSAL, ASSERTED AS A REVERSAL.** The superseded draft dispositioned all six
    `OUT_OF_BOUND` on the ground *"no caller-controlled route"*. `PO-DECISIONS-0015` ruling 4:
    *"a disposition whose reason has died does not survive on habit."*"""
    _module, admissions, _modules = _load(a_tree)
    category_c = [key for key, word in _THE_THIRTEEN.items()
                  if key[1] in ("_EstablishedHere.__call__", "_compile", "_type_tuple", "each_of")]
    assert len(category_c) == 6
    for key in category_c:
        assert admissions[key][0] == "DEFECT_OPEN"
        assert admissions[key][1]["finding"], key


def test_the_tier_1_tally_is_ten_DEFECT_OPEN_and_three_CARRIER_ONLY(a_tree):
    """`PO-DECISIONS-0015` ruling 4 and §4 of the content document. **TEN OPEN DEFECTS IS THE
    POINT OF THIS ACT, NOT A SIDE EFFECT OF IT.**"""
    result = _run(a_tree)
    assert "DEFECT_OPEN              10 |" in result.stdout, result.stdout[:6000]
    assert "CARRIER_ONLY              3 |" in result.stdout, result.stdout[:6000]


def test_the_register_still_carries_TWO_OUT_OF_BOUND_rows_and_they_are_NOT_the_fifteen(a_tree):
    """**A MEASURED CONTRADICTION WITH THE ACT'S OWN CONTENT DOCUMENT, PINNED SO IT CANNOT BE
    LOST.**

    `CD-THE-FIFTEEN-AND-THE-REDRAFT.md` §4 tallies ``OUT_OF_BOUND`` at **0** *"was 6. Every one
    of them is gone"*, and the Engineer dispatch says ``**OUT_OF_BOUND COUNT AFTER THIS ACT:
    ZERO.**`` **MEASURED, IT IS TWO.** The draft's six Category C dispositions were a PROPOSAL
    and were never written into this register; the two rows that are here predate the whole
    proposal, sit on `crash_detector.observations`, and are **not among the fifteen** — so no
    seat on this act had authority to touch them and none did.

    This test exists so the next reader meets the fact rather than the tally.
    """
    _module, admissions, _modules = _load(a_tree)
    out_of_bound = sorted(key for key, value in admissions.items() if value[0] == "OUT_OF_BOUND")
    assert len(out_of_bound) == 2, out_of_bound
    assert all(key[0] == "crash_detector.observations" for key in out_of_bound), out_of_bound
    assert not set(out_of_bound) & set(_THE_THIRTEEN)


# ------------------------------------------------------------------------------------- #
# THE TWO DERIVED MODULES — ON THE REAL SUBJECT, BOTH ARMS.
# ------------------------------------------------------------------------------------- #


@pytest.mark.parametrize("module", _DERIVED_MODULES)
def test_the_module_gets_NO_module_level_prose_claim(a_tree, module):
    """*"and get no module-level prose claim at all. The instrument DERIVES the module answer
    from the site register; it does not accept a sentence about it."*"""
    _sweep, _admissions, modules = _load(a_tree)
    assert module not in modules, f"{module} has a written module-level disposition"


@pytest.mark.parametrize("module", _DERIVED_MODULES)
def test_the_module_is_DERIVED_and_the_run_is_clean_of_it(a_tree, module):
    """The passing arm, on the real subject."""
    result = _run(a_tree)
    assert f"[DERIVED     ] {module}" in result.stdout, result.stdout[:6000]
    assert f"UNDECLARED MODULE: {module}" not in result.stdout


@pytest.mark.parametrize("module", _DERIVED_MODULES)
def test_REMOVING_ONE_REAL_tier_2_ROW_puts_the_module_back_to_UNDECLARED(a_tree, module):
    """**THE REFUSING ARM ON THE THING THIS ACT ACTUALLY DID.**

    33 rows and 17 rows. Take away ONE and the DERIVED answer must disappear and the sweep must
    go red again. A derivation that cannot be made to fail has not been shown to derive
    anything — and one exercised only on a module chosen for being small has been shown to
    derive something else.
    """
    sweep_module, admissions, _modules = _load(a_tree)
    sites, _subject, _outside, _sources = sweep_module.sweep(a_tree)
    tier_2 = sorted(
        site for site in {s for s in sites if s[2] not in sweep_module.TIER_1_ADMISSION}
        if site[0] == module
    )
    assert tier_2, module
    assert all(site in admissions for site in tier_2), "the module was not derived to begin with"
    _append(a_tree, f"del DECLARED_ADMISSIONS[{tier_2[0]!r}]")
    result = _run(a_tree)
    assert result.returncode == 1
    assert f"UNDECLARED MODULE: {module}" in result.stdout, result.stdout[-4000:]
    assert f"tier-2 site keys still undeclared: 1 of {len(tier_2)}" in result.stdout


# ------------------------------------------------------------------------------------- #
# `CARRIER_ONLY.callable` — THE FIELD THE CONTENT DOCUMENT GOT WRONG. BOTH ARMS.
# ------------------------------------------------------------------------------------- #


def _plant_a_product_caller(root, name: str) -> None:
    """Add a real call to `name` inside a module that IS in the swept closure."""
    victim = root / "src" / "crash_detector" / "engine" / "evaluate.py"
    victim.write_text(
        victim.read_text() + f"\n\ndef _planted_product_caller(door):\n    return {name}(door)\n"
    )


def test_a_product_caller_of_a_CARRIER_ONLY_callable_BREAKS_THE_BUILD(a_tree):
    """*"`callable` IS MACHINE-CHECKED — this word is an ENUMERATION, NOT A CLAIM, and it fails
    the day a product module calls the thing."*"""
    _plant_a_product_caller(a_tree, "admission_faults")
    result = _run(a_tree)
    assert result.returncode == 1
    assert "CARRIER_ONLY_HAS_A_PRODUCT_CALLER" in result.stdout, result.stdout[-4000:]
    assert "admission_faults" in result.stdout


def test_the_content_documents_own_field_text_would_have_made_that_check_VACUOUS(a_tree):
    """**THE FINDING THIS ACT RAISED AGAINST ITS OWN SPECIFICATION, PINNED AS A REGRESSION.**

    `CD-THE-FIFTEEN-AND-THE-REDRAFT.md` §3 gives the Category B `callable` field as *"the
    enumerated carrier callers — `tests/test_admission.py`, `tests/test_judgement_path_doors.py`,
    `tests/test_collector_runner.py`"*, beside the claim that it is **MACHINE-CHECKED**.

    `_carrier_only_violations` matches that field against CALL EXPRESSIONS BY NAME. A list of
    file paths matches no call expression, ever. **MEASURED: with a real product caller planted,
    the check DOES NOT FIRE.** The field carries the callable's NAME in this register, and the
    carrier file list lives in `why_it_is_not_product_judgement`, which is where prose belongs.

    This test asserts the vacuity so that nobody re-introduces the document's wording believing
    it is checked. **It is the arm that proves the machine check is a machine check and not a
    place a sentence can sit.**
    """
    _plant_a_product_caller(a_tree, "admission_faults")
    # Rewrite `callable` on EVERY row naming `admission_faults` — the tier-1 row of Category B
    # and its tier-2 companion — into the content document's own field text. Rewriting only one
    # would leave the other one firing and the arm would prove nothing.
    _append(
        a_tree,
        "for _key, _value in list(DECLARED_ADMISSIONS.items()):\n"
        "    if _value[0] == 'CARRIER_ONLY' and _value[1].get('callable') == 'admission_faults':\n"
        "        DECLARED_ADMISSIONS[_key] = ('CARRIER_ONLY', {\n"
        "            'callable': 'the enumerated carrier callers - tests/test_admission.py, '\n"
        "                        'tests/test_judgement_path_doors.py, tests/test_collector_runner.py',\n"
        "            'why_it_is_not_product_judgement': 'asserted, and unchecked',\n"
        "        })",
    )
    result = _run(a_tree)
    assert "CARRIER_ONLY_HAS_A_PRODUCT_CALLER" not in result.stdout, (
        "the check fired on a file-path field, which would mean this finding is wrong — "
        "welcome, but it must then be recorded as wrong.\n" + result.stdout[-4000:]
    )


# ------------------------------------------------------------------------------------- #
# AND THE ONE THAT IS ABOUT THE EXIT CODE ITSELF.
# ------------------------------------------------------------------------------------- #


def test_the_sweep_SAYS_what_its_own_zero_exit_code_does_not_mean(a_tree):
    """**THE SINGLE MOST MISREADABLE NUMBER THIS PROJECT HAS PRODUCED, AND THIS IS THE GUARD ON
    IT.**

    Before this act the sweep exited 1 with fifteen violations. After it, every violation is
    DECLARED and it exits 0. **Nothing was fixed. Ten sites are declared OPEN DEFECTS. No line
    under `src/` changed.** A clean run being read as evidence of a proposition it says nothing
    about is the failure this project keeps meeting, so the instrument is required to say so in
    its own output, every time, without an auditor having to know to ask.
    """
    result = _run(a_tree)
    assert result.returncode == 0, result.stdout[-4000:]
    assert "A PASS here is a statement about the SURFACE and never about the class" in result.stdout
    assert "A REGISTER FULL OF `DEFECT_OPEN` BUYS NOTHING" in result.stdout
    assert "ARITHMETIC over the declaration set, not evidence about the code" in result.stdout
    assert "10 sites DECLARED AS OPEN DEFECTS" in result.stdout, result.stdout[-4000:]
