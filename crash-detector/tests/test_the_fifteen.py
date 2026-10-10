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
    # Category C — six sites, REVERSED from the draft's OUT_OF_BOUND. **FOUR OF THE SIX WERE
    # FIXED AT WO-2R3 INCREMENT 10 ITEM 1 (`5a37301`) AND ARE NO LONGER SITES AT ALL**; they
    # moved to `_THE_FOUR_THAT_WERE_FIXED` below, which asserts strictly MORE about them than
    # this map did. THE TWO THAT ARE STILL OPEN ARE STILL HERE, WITH THE SAME WORD.
    ("crash_detector.admission", "_compile", "ISINSTANCE",
     "isinstance(declaration, type)"): "DEFECT_OPEN",
    ("crash_detector.admission", "_type_tuple", "ISINSTANCE",
     "isinstance(value, type)"): "DEFECT_OPEN",
    # The three establishment sites, read for the first time at the issuing boundary.
    ("crash_detector.establishment", "_declared_field_list", "DUCK",
     "getattr(cls, '__dataclass_fields__', {})"): "DEFECT_OPEN",
    ("crash_detector.establishment", "_declared_field_list", "DUCK",
     "getattr(field._field_type, 'name', '')"): "DEFECT_OPEN",
    ("crash_detector.establishment", "establishes.apply_at_the_boundary.__init__", "DUCK",
     "getattr(self, name, _ABSENT)"): "DEFECT_OPEN",
}


#: **THE FOUR CATEGORY-C DEFECTS THAT WERE FIXED, dead key -> successor key.** Written out
#: rather than derived, for the same reason `_THE_THIRTEEN` is: a test that derives its
#: expectation from the thing it is testing asserts nothing.
#:
#: **THESE FOUR ROWS SAID "NOT FIXED BY THIS ACT AND NOT SCHEDULED TO BE BY IT". A LATER ACT
#: FIXED THEM**, and the assertions below are STRONGER than the ones they replace: the old map
#: asserted a word on a live key; this one asserts the old key is GONE, that the successor
#: EXISTS as a live site, and that it carries `EXACT`. A test that only counted `DEFECT_OPEN`
#: would have gone green again the moment somebody re-added a defect.
_THE_FOUR_THAT_WERE_FIXED = {
    ("crash_detector.admission", "_EstablishedHere.__call__", "ISINSTANCE",
     "isinstance(because, str)"):
        ("crash_detector.admission", "_EstablishedHere.__call__", "IDENTITY",
         "type(because) is not str"),
    ("crash_detector.admission", "_compile", "ISINSTANCE",
     "isinstance(declaration, tuple)"):
        ("crash_detector.admission", "_compile", "IDENTITY",
         "type(declaration) is tuple"),
    ("crash_detector.admission", "each_of", "ISINSTANCE",
     "isinstance(within, tuple)"):
        ("crash_detector.admission", "each_of", "IDENTITY",
         "type(within) is not tuple"),
    # **THE ONE THAT IS NOT A 1:1 CONVERSION.** The comparison did not change spelling in
    # place; it MOVED into the new `is_exactly` helper, whose one site decides by `is`.
    ("crash_detector.admission", "_compile", "ISINSTANCE",
     "isinstance(declaration, _Admission)"):
        ("crash_detector.admission", "is_exactly", "IDENTITY", "kind is candidate"),
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


def test_the_TWO_Category_C_sites_that_remain_are_still_DEFECT_OPEN(a_tree):
    """**THE REVERSAL, ASSERTED AS A REVERSAL — AND NOW ALSO AS A PARTIAL REPAIR.**

    The superseded draft dispositioned all six Category C sites `OUT_OF_BOUND` on the ground
    *"no caller-controlled route"*. `PO-DECISIONS-0015` ruling 4: *"a disposition whose reason
    has died does not survive on habit."*

    **FOUR OF THE SIX WERE THEN ACTUALLY FIXED** at WO-2R3 increment 10 item 1 — see
    :data:`_THE_FOUR_THAT_WERE_FIXED` and the two tests below it. **TWO REMAIN OPEN AND MUST
    STAY OPEN**: `_compile isinstance(declaration, type)` and `_type_tuple
    isinstance(value, type)`, both kept deliberately with a measured reason (exact type there
    would refuse this package's own metaclass-sealed declarations). Six minus four is two, and
    this test asserts the two rather than the arithmetic.
    """
    _module, admissions, _modules = _load(a_tree)
    category_c = [key for key in _THE_THIRTEEN
                  if key[1] in ("_EstablishedHere.__call__", "_compile", "_type_tuple", "each_of")]
    assert len(category_c) == 2, category_c
    for key in category_c:
        assert admissions[key][0] == "DEFECT_OPEN"
        assert admissions[key][1]["finding"], key
    assert len(_THE_FOUR_THAT_WERE_FIXED) == 4
    assert not set(category_c) & set(_THE_FOUR_THAT_WERE_FIXED)


@pytest.mark.parametrize("dead, successor", sorted(_THE_FOUR_THAT_WERE_FIXED.items()))
def test_a_FIXED_Category_C_site_is_GONE_and_its_successor_is_EXACT(a_tree, dead, successor):
    """**THE FOUR THAT WERE FIXED, ASSERTED AS FIXES AND NOT AS ABSENCES.**

    A row disappearing from a register proves nothing on its own — deleting the entry that
    complains is precisely the move the sweep's both-directions set equality exists to catch.
    So this asserts three things at once: the DEAD key is not a site any more, the SUCCESSOR
    key IS a site, and the successor carries `EXACT`. **Only the middle one distinguishes a
    repair from a deletion.**
    """
    sweep_module, admissions, _modules = _load(a_tree)
    sites, _subject, _outside, _sources = sweep_module.sweep(a_tree)
    assert dead not in set(sites), f"{dead} is still a live site; it was supposed to be fixed"
    assert dead not in admissions, f"{dead} still has a register row for a site that is gone"
    assert successor in set(sites), (
        f"{successor} is NOT a live site. The dead key vanishing without its successor "
        "appearing is a DELETION, not a repair, and this test refuses to read it as one."
    )
    assert successor in admissions, f"{successor} is a live site with no disposition"
    assert admissions[successor][0] == "EXACT", admissions[successor][0]


def test_the_four_repairs_CLOSED_NO_FINDING(a_tree):
    """**A SEAT THAT FIXES A SITE DOES NOT GET TO CLOSE A FINDING** — `governance/findings/`
    is nobody's to mark closed, and the four repaired sites cited CD-F-0002 and CD-F-0003,
    which are still cited by the sites that are still open.
    """
    sweep_module, admissions, _modules = _load(a_tree)
    findings, problems = sweep_module._load_findings_register(
        a_tree / "governance" / "findings" / "findings-register.json"
    )
    assert not problems, problems
    for name in ("CD-F-0002", "CD-F-0003"):
        assert findings[name]["status"] == "OPEN", (
            f"{name} is {findings[name]!r} and must be OPEN"
        )
    still_citing = [
        key for key, value in admissions.items()
        if isinstance(value[1], dict) and "CD-F-0003" in str(value[1].get("finding", ""))
    ]
    assert still_citing, "nothing cites CD-F-0003 any more, which would make it unfalsifiable"


def test_the_tier_1_tally_is_SIX_DEFECT_OPEN_and_three_CARRIER_ONLY(a_tree):
    """**SUPERSEDES `test_the_tier_1_tally_is_ten_DEFECT_OPEN_and_three_CARRIER_ONLY`, AND THE
    REASON THE NUMBER MOVED IS THE ONLY REASON A NUMBER IS EVER ALLOWED TO MOVE HERE.**

    `PO-DECISIONS-0015` ruling 4 and §4 of the content document made it TEN, and ten open
    defects was the point of that act rather than a side effect of it. **FOUR OF THE TEN WERE
    REPAIRED AT WO-2R3 INCREMENT 10 ITEM 1 (`5a37301`)** — see
    :data:`_THE_FOUR_THAT_WERE_FIXED`, whose own tests assert each dead key is gone AND each
    successor exists AND each successor is `EXACT`, which is what makes this a repair rather
    than four deleted rows. Ten minus four is six.

    **THE TALLY IS NOT WHAT IS BEING ASSERTED HERE AND IT NEVER WAS.** It is a cross-check on
    the per-site tests above, which name their sites. If this number is right and those are
    wrong, those are what fail.
    """
    result = _run(a_tree)
    assert "DEFECT_OPEN               6 |" in result.stdout, result.stdout[:6000]
    assert "CARRIER_ONLY              3 |" in result.stdout, result.stdout[:6000]


def test_the_OUT_OF_BOUND_count_is_NOW_zero_and_it_got_there_by_REPAIR_not_by_a_tally(a_tree):
    """**SUPERSEDES `test_the_register_still_carries_TWO_OUT_OF_BOUND_rows_and_they_are_NOT_the
    _fifteen`, AND THE SUPERSEDING IS THE INTERESTING PART.**

    That test existed to pin a MEASURED CONTRADICTION so it could not be lost:
    `CD-THE-FIFTEEN-AND-THE-REDRAFT.md` §4 tallied `OUT_OF_BOUND` at **0** — *"was 6. Every one
    of them is gone"* — and the Engineer dispatch wrote `**OUT_OF_BOUND COUNT AFTER THIS ACT:
    ZERO.**` **MEASURED, IT WAS TWO**, on `crash_detector.observations`, predating the whole
    proposal and outside every seat's authority on that act.

    **IT IS NOW ZERO — AND NOT BECAUSE ANYBODY EDITED A TALLY.** WO-2R3 increment 10 item 1
    converted both sites to exact type, and item 5 re-pointed both rows to their successors
    with the predecessors' `OUT_OF_BOUND` text recorded verbatim in each. A declared residue
    was discharged by a code change, which is the one way a residue is allowed to disappear.

    **SO THIS TEST NOW ASSERTS THE ROUTE AND NOT THE NUMBER.** Zero alone would also be the
    reading if somebody had simply deleted two inconvenient rows, and that is the failure this
    file has been guarding against since it was written.
    """
    sweep_module, admissions, _modules = _load(a_tree)
    sites, _subject, _outside, _sources = sweep_module.sweep(a_tree)

    out_of_bound = sorted(key for key, value in admissions.items() if value[0] == "OUT_OF_BOUND")
    assert out_of_bound == [], out_of_bound

    # THE TWO THAT WERE `OUT_OF_BOUND`, and where each of them went.
    for dead, successor in (
        (("crash_detector.observations", "FetchFailed.__post_init__", "ISINSTANCE",
          "isinstance(status, int)"),
         ("crash_detector.observations", "FetchFailed.__post_init__", "IDENTITY",
          "type(status) is not int")),
        (("crash_detector.observations", "Malformed.__post_init__", "ISINSTANCE",
          "isinstance(self.instance_path, str)"),
         ("crash_detector.observations", "Malformed.__post_init__", "IDENTITY",
          "type(self.instance_path) is not str")),
    ):
        assert dead not in set(sites), f"{dead} is still a live site"
        assert successor in set(sites), (
            f"{successor} is NOT a live site — the OUT_OF_BOUND row went to zero without a "
            "successor appearing, which is a deletion and not a repair."
        )
        assert admissions[successor][0] == "EXACT"
        assert "OUT_OF_BOUND" in admissions[successor][1], (
            f"{successor}'s row does not record that its predecessor was OUT_OF_BOUND. A "
            "residue that disappears quietly is indistinguishable from one that was papered."
        )
        assert "NOT PROVED TO BE CARRIED ANYWHERE" in admissions[successor][1], (
            "the predecessor's residue sentence is not carried into the successor's row."
        )

    # AND THE `DELEGATED` ROW, WHICH WENT THE SAME WAY AND FOR THE SAME REASON.
    assert not [key for key, value in admissions.items() if value[0] == "DELEGATED"]
    cadence = ("crash_detector.source_registry", "SourceRecord.__post_init__", "IDENTITY",
               "type(self.cadence_seconds) is not int")
    assert cadence in set(sites)
    assert admissions[cadence][0] == "EXACT"
    assert "DELEGATED" in admissions[cadence][1]


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

    Before that act the sweep exited 1 with fifteen violations. After it, every violation was
    DECLARED and it exited 0. **Nothing was fixed. Ten sites were declared OPEN DEFECTS. No
    line under `src/` changed.**

    **WO-2R3 INCREMENT 10 CHANGED THE NUMBER AND NOT THE ARGUMENT.** Item 1 converted twelve
    tier-1 sites to exact type, which RE-KEYED them and pushed this tool from 15 violations to
    18 — *the violation count went up because the code got better* — and item 5 re-pointed
    every orphaned row to its measured successor. So it exits 0 again, **six** sites are
    declared OPEN DEFECTS rather than ten, and the four that left did so because they were
    REPAIRED, which `_THE_FOUR_THAT_WERE_FIXED` asserts site by site rather than by counting.
    The sentence this test guards is unchanged: a zero here is arithmetic over the declaration
    set and is not evidence about the code. A clean run being read as evidence of a proposition it says nothing
    about is the failure this project keeps meeting, so the instrument is required to say so in
    its own output, every time, without an auditor having to know to ask.
    """
    result = _run(a_tree)
    assert result.returncode == 0, result.stdout[-4000:]
    assert "A PASS here is a statement about the SURFACE and never about the class" in result.stdout
    assert "A REGISTER FULL OF `DEFECT_OPEN` BUYS NOTHING" in result.stdout
    assert "ARITHMETIC over the declaration set, not evidence about the code" in result.stdout
    assert "6 sites DECLARED AS OPEN DEFECTS" in result.stdout, result.stdout[-4000:]
    # **AND THE SWEEP'S OTHER DECLARED LIMIT NOW REACHES THE EXIT TOO**, on this PASS path and
    # on the FAIL path alike — WO-2R3 increment 10 item 4, CD-D-166. Asserted here as well as
    # in tests/test_the_declared_limits_reach_the_exit.py because THIS is the test that exists
    # to stop a zero exit being read as a proposition it says nothing about, and `gates` being
    # unsound in both directions is the sharpest thing this tool's zero does not mean.
    assert "THIS FIELD IS UNSOUND IN BOTH DIRECTIONS AT ONCE" in result.stdout
    assert result.stdout.index("DECLARED LIMIT 5") > result.stdout.rindex(
        "CD-CLASS-2-SWEEP: PASS"
    ), "the CD-D-166 limit was printed before the verdict line"
