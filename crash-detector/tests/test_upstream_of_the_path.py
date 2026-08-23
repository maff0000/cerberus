"""CARRIER for the REDRAFTED ``UPSTREAM_OF_THE_PATH`` — ``PO-DECISIONS-0014`` ruling 1.

    *"REJECTED AS DRAFTED, for exactly the reasons its own author measured: it binds the
     module register where its siblings bind the site register, and its fields are prose no
     machine can check. It is REDRAFTED to bind the SITE register with machine-checkable
     fields."*

**FIVE MACHINE CHECKS, AND EVERY ONE OF THEM HAS AN ARM THAT REFUSES AND AN ARM THAT PASSES.**
The drafted word had two prose fields; presence and non-emptiness were enforced and nothing
else, so any sentence satisfied it. The redraft replaces them with a CLOSED SET and a SITE KEY
— two facts this instrument independently holds — and this file is where that difference is
made to bite. A closed-set check that has only ever seen members has not been shown to close a
set; a `gates` check that has only ever seen sites that exist has not been shown to resolve
anything.

**AND THE DERIVATION IS TESTED THE SAME WAY.** A module answer that is DERIVED from per-site
entries must be able to go back to UNDECLARED when one entry is removed. A derivation that
cannot be made to fail has not been shown to derive anything.

Every test builds a THROWAWAY COPY of the tree and edits the registers THERE.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SWEEP_REL = pathlib.Path("tools") / "sweep" / "delegated_judgement_sweep.py"
_REGISTER_REL = pathlib.Path("tools") / "sweep" / "declared_dispositions.py"
_FINDINGS_REL = pathlib.Path("governance") / "findings" / "findings-register.json"

#: A real tier-1 admission site in a module that is NOT `crash_detector.time_utc`. Used as the
#: `gates` target for the arms that are about something other than `gates`.
_A_REAL_GATED_SITE = (
    "crash_detector.engine.config",
    "ConfigSnapshot.__post_init__",
    "ISINSTANCE",
    "isinstance(window, float)",
)

#: The declaring site for the probe rows. A site key that does not exist, so every arm below
#: also raises STALE DECLARATION — deliberately, so that no assertion here can be satisfied by
#: the exit code alone. Every assertion names a RULE.
_A_SITE = ("crash_detector.time_utc", "a_probe_site", "ISINSTANCE", "isinstance(x, int)")


@pytest.fixture()
def a_tree():
    root = pathlib.Path(tempfile.mkdtemp(prefix="cd-upstream-"))
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


def _sites(root):
    """This run's own measured site set, taken from the COPY's own sweep (CD-PL-F98: read the
    tree you actually measured, never assume two arms read the same one)."""
    spec = importlib.util.spec_from_file_location("_probe_sweep", root / _SWEEP_REL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sites, subject, _outside, _sources = module.sweep(root)
    tier_2 = {site for site in sites if site[2] not in module.TIER_1_ADMISSION}
    return tier_2, subject


def _append(root, python_source: str) -> None:
    register = root / _REGISTER_REL
    register.write_text(register.read_text() + "\n\n" + python_source + "\n")


def _site_entry(root, key, value_literal: str) -> None:
    _append(root, f"DECLARED_ADMISSIONS[{key!r}] = {value_literal}")


def _upstream(origin: str, gates=_A_REAL_GATED_SITE, finding: str | None = None) -> str:
    evidence = {"operand_origin": origin, "gates": gates}
    if finding is not None:
        evidence["finding"] = finding
    return f"(\"UPSTREAM_OF_THE_PATH\", {evidence!r})"


# ------------------------------------------------------------------------------------- #
# `gates` — A SITE KEY, NOT A ROUTE DESCRIPTION. THREE ARMS.
# ------------------------------------------------------------------------------------- #


def test_a_gates_key_that_does_not_exist_REFUSES(a_tree):
    """**"A CLAIM ABOUT A ROUTE THAT SURVIVES THE ROUTE DISAPPEARING IS NOT A CLAIM."**

    The drafted `route` field was a sentence, and a sentence about a route stays true-looking
    forever. This one names a point that either is in the measured site set or is not.
    """
    _site_entry(
        a_tree,
        _A_SITE,
        _upstream(
            "SOURCE_DECLARATION",
            gates=("crash_detector.engine.config", "NoSuchThing", "ISINSTANCE", "isinstance(a, b)"),
        ),
    )
    result = _run(a_tree)
    assert result.returncode == 1
    assert "GATES_SITE_DOES_NOT_EXIST" in result.stdout, result.stdout[-3000:]


def test_a_gates_key_in_the_SAME_module_REFUSES(a_tree):
    """The word asserts that this site is UPSTREAM OF a judgement path. A site that only gates
    its own module has not been shown to be upstream of anything, and the ruling's first
    stated reason for rejecting the draft was that it *"binds the module register where its
    siblings bind the site register"* — the module/site asymmetry this check is the other half
    of.
    """
    _site_entry(
        a_tree,
        _A_SITE,
        _upstream(
            "SOURCE_DECLARATION",
            gates=("crash_detector.time_utc", "ensure_utc", "ISINSTANCE", "isinstance(value, datetime)"),
        ),
    )
    result = _run(a_tree)
    assert result.returncode == 1
    assert "GATES_SITE_IS_IN_THE_DECLARING_MODULE" in result.stdout, result.stdout[-3000:]


def test_a_gates_key_that_is_not_a_four_tuple_REFUSES(a_tree):
    """The shape a reader would most naturally reach for: a sentence, or a `module::qualname`
    string. Both are the drafted field wearing the new field's name."""
    _site_entry(
        a_tree,
        _A_SITE,
        '("UPSTREAM_OF_THE_PATH", {"operand_origin": "SOURCE_DECLARATION", '
        '"gates": "crash_detector.engine.config::ConfigSnapshot"})',
    )
    result = _run(a_tree)
    assert result.returncode == 1
    assert "GATES_SITE_DOES_NOT_EXIST" in result.stdout, result.stdout[-3000:]


def test_THE_RENAME_TEST_a_gates_key_does_NOT_survive_renaming_one_identifier(a_tree):
    """**THE PROOF STANDARD ASKS THIS EXPLICITLY, AND THE ANSWER IS REPORTED WHICHEVER WAY IT
    FALLS: IT DOES NOT SURVIVE.**

    Rename the parameter `window` in `crash_detector.engine.config` and the gated site key's
    expression text changes, so the row REFUSES. That is DECLARED LIMIT 4 of this tool applied
    to the new field — *"a disposition is keyed by the expression's text, so renaming a local
    variable makes the site UNDECLARED and this tool FAILS. That is the safe direction and it
    is deliberate."*

    **THE HONEST COST, STATED HERE AND NOT LEFT TO BE FOUND:** the refusal is credited to
    TEXT, not to STRUCTURE. An auditor must read it as *"somebody moved the thing this row
    points at, go and look"* and never as *"the gating relationship has been broken"*. The two
    are different facts and this check cannot tell them apart.
    """
    source = a_tree / "src" / "crash_detector" / "engine" / "config.py"
    before = source.read_text()
    assert "isinstance(window, float)" in before
    source.write_text(before.replace("window", "staleness_window_seconds"))
    _site_entry(a_tree, _A_SITE, _upstream("SOURCE_DECLARATION"))
    result = _run(a_tree)
    assert result.returncode == 1
    assert "GATES_SITE_DOES_NOT_EXIST" in result.stdout, result.stdout[-4000:]


# ------------------------------------------------------------------------------------- #
# `operand_origin` — MEMBERSHIP IN A CLOSED SET. BOTH ARMS.
# ------------------------------------------------------------------------------------- #


def test_an_operand_origin_outside_the_closed_set_REFUSES(a_tree):
    _site_entry(a_tree, _A_SITE, _upstream("PROBABLY_INTERNAL"))
    result = _run(a_tree)
    assert result.returncode == 1
    assert "OPERAND_ORIGIN_NOT_IN_THE_CLOSED_SET" in result.stdout, result.stdout[-3000:]
    assert "PROBABLY_INTERNAL" in result.stdout


def test_an_operand_origin_that_is_a_SENTENCE_REFUSES(a_tree):
    """**THE MOST LIKELY WAY THE REDRAFT WOULD BE DEFEATED IN PRACTICE**, and it is the exact
    defect the ruling rejected the draft for: put a sentence where the fact goes and let it
    read as compliance. Under the draft that worked. It does not work now.
    """
    _site_entry(
        a_tree,
        _A_SITE,
        _upstream("the operand comes from the module's own declaration, which is source-written"),
    )
    result = _run(a_tree)
    assert result.returncode == 1
    assert "OPERAND_ORIGIN_NOT_IN_THE_CLOSED_SET" in result.stdout, result.stdout[-3000:]


@pytest.mark.parametrize(
    "origin, finding",
    [
        ("SOURCE_DECLARATION", None),
        ("MODULE_CONSTANT", None),
        ("OWN_CONSTRUCTION", None),
        ("CALLER_SUPPLIED", "CD-F-0001"),
    ],
)
def test_every_MEMBER_of_the_closed_set_is_accepted(a_tree, origin, finding):
    """**THE PASSING ARM, AND IT IS PARAMETRIZED OVER THE WHOLE SET ON PURPOSE.** A closed-set
    check that accepted only one member would pass the refusing arms above while rejecting
    three quarters of the vocabulary, and nothing else here would notice.
    """
    _site_entry(a_tree, _A_SITE, _upstream(origin, finding=finding))
    result = _run(a_tree)
    for rule in (
        "OPERAND_ORIGIN_NOT_IN_THE_CLOSED_SET",
        "GATES_SITE_DOES_NOT_EXIST",
        "GATES_SITE_IS_IN_THE_DECLARING_MODULE",
        "CALLER_SUPPLIED_WITHOUT_A_FINDING",
        "DISPOSITION_EVIDENCE_MISSING",
        "FINDING_DOES_NOT_RESOLVE",
        "FINDING_IS_NOT_OPEN",
    ):
        assert rule not in result.stdout, f"{rule}\n{result.stdout[-4000:]}"


# ------------------------------------------------------------------------------------- #
# THE CONDITIONAL FIELD — "no spelling of this word records a caller-controlled operand and
# claims nothing is wrong". THREE ARMS.
# ------------------------------------------------------------------------------------- #


def test_CALLER_SUPPLIED_with_no_finding_REFUSES(a_tree):
    _site_entry(a_tree, _A_SITE, _upstream("CALLER_SUPPLIED"))
    result = _run(a_tree)
    assert result.returncode == 1
    assert "CALLER_SUPPLIED_WITHOUT_A_FINDING" in result.stdout, result.stdout[-3000:]


def test_CALLER_SUPPLIED_whose_finding_does_not_resolve_REFUSES(a_tree):
    """Naming *a* finding is not enough. The id has to be one somebody actually raised."""
    _site_entry(a_tree, _A_SITE, _upstream("CALLER_SUPPLIED", finding="CD-F-9999"))
    result = _run(a_tree)
    assert result.returncode == 1
    assert "FINDING_DOES_NOT_RESOLVE" in result.stdout, result.stdout[-3000:]


def test_CALLER_SUPPLIED_whose_finding_is_CLOSED_REFUSES(a_tree):
    rows = json.loads((a_tree / _FINDINGS_REL).read_text())
    rows.append({"id": "CD-F-0098", "raised_at": "0" * 40, "status": "SUPERSEDED"})
    (a_tree / _FINDINGS_REL).write_text(json.dumps(rows, indent=2) + "\n")
    _site_entry(a_tree, _A_SITE, _upstream("CALLER_SUPPLIED", finding="CD-F-0098"))
    result = _run(a_tree)
    assert result.returncode == 1
    assert "FINDING_IS_NOT_OPEN" in result.stdout, result.stdout[-3000:]


# ------------------------------------------------------------------------------------- #
# THE BINDING — the word is OUT of the module register. BOTH ARMS.
# ------------------------------------------------------------------------------------- #


def test_the_word_in_the_MODULE_register_REFUSES(a_tree):
    """*"it binds the module register where its siblings bind the site register"* was the
    ruling's FIRST stated reason for rejection, so the redraft has to make writing it there
    impossible rather than merely discouraged."""
    _append(
        a_tree,
        'DECLARED_MODULE_DISPOSITIONS["crash_detector.admission"] = '
        '("UPSTREAM_OF_THE_PATH", {"operand_origin": "SOURCE_DECLARATION", '
        f'"gates": {_A_REAL_GATED_SITE!r}}})',
    )
    result = _run(a_tree)
    assert result.returncode == 1
    assert "WORD_NOT_ADMITTED_IN_MODULE_REGISTER" in result.stdout, result.stdout[-3000:]


def test_the_five_ORIGINAL_words_are_still_admitted_in_the_module_register(a_tree):
    """The passing arm for the binding: the redraft removed ONE word from that register and
    must not have quietly removed the others. Exactly what the ruling named, and not one word
    more — being stricter than a ruling is still departing from it."""
    result = _run(a_tree)
    assert "WORD_NOT_ADMITTED_IN_MODULE_REGISTER" not in result.stdout, result.stdout[-4000:]


def test_the_DRAFTED_fields_no_longer_satisfy_the_word(a_tree):
    """`decides` and `route` were the drafted fields. **THE REDRAFT REPLACED THEM; IT DID NOT
    ADD TO THEM**, so an entry written against the draft must now fail rather than be silently
    tolerated alongside the new one."""
    _site_entry(
        a_tree,
        _A_SITE,
        '("UPSTREAM_OF_THE_PATH", {"decides": "whether judgement-path doors establish", '
        '"route": "every @admits door in the package"})',
    )
    result = _run(a_tree)
    assert result.returncode == 1
    assert "DISPOSITION_EVIDENCE_MISSING" in result.stdout, result.stdout[-3000:]
    assert "operand_origin" in result.stdout


# ------------------------------------------------------------------------------------- #
# THE DERIVATION — a module answer computed from the site register, never written. BOTH ARMS.
# ------------------------------------------------------------------------------------- #


def _derive_a_module(a_tree, module: str):
    """Delete `module`'s module-register entry and declare EVERY ONE of its tier-2 site keys.

    Returns the sorted tier-2 keys. **The module-register entry is removed in the COPY only**
    — this is how a module that has no module-level prose claim is reproduced without touching
    the repository's own register.
    """
    tier_2, subject = _sites(a_tree)
    assert module in subject
    keys = sorted(site for site in tier_2 if site[0] == module)
    assert keys, f"{module} has no tier-2 sites; the derivation would be VACUOUS"
    lines = [f'DECLARED_MODULE_DISPOSITIONS.pop("{module}", None)']
    for key in keys:
        lines.append(
            f"DECLARED_ADMISSIONS[{key!r}] = "
            f"(\"UPSTREAM_OF_THE_PATH\", {{'operand_origin': 'OWN_CONSTRUCTION', "
            f"'gates': {_A_REAL_GATED_SITE!r}}})"
        )
    _append(a_tree, "\n".join(lines))
    return keys


def test_a_module_with_EVERY_tier_2_site_declared_is_DERIVED_and_not_UNDECLARED(a_tree):
    """**THE PASSING ARM OF THE DERIVATION.** `crash_detector.dials.dialset` is used because it
    is the smallest module in the closure, so the arm is about the derivation and not about
    the volume of rows."""
    _derive_a_module(a_tree, "crash_detector.dials.dialset")
    result = _run(a_tree)
    assert "UNDECLARED MODULE: crash_detector.dials.dialset" not in result.stdout, (
        result.stdout[-4000:]
    )
    assert "[DERIVED     ] crash_detector.dials.dialset" in result.stdout, result.stdout[:4000]


def test_REMOVING_ONE_tier_2_entry_puts_the_module_back_to_UNDECLARED(a_tree):
    """**THE REFUSING ARM, AND IT IS THE WHOLE OF THE DERIVATION'S EVIDENCE.**

    One row out of the module's tier-2 set, and the DERIVED answer must disappear. A
    derivation that cannot be made to fail has not been shown to derive anything — it is a
    default wearing a computation's name.
    """
    keys = _derive_a_module(a_tree, "crash_detector.dials.dialset")
    _append(a_tree, f"del DECLARED_ADMISSIONS[{keys[0]!r}]")
    result = _run(a_tree)
    assert result.returncode == 1
    assert "UNDECLARED MODULE: crash_detector.dials.dialset" in result.stdout, (
        result.stdout[-4000:]
    )
    assert "tier-2 site keys still undeclared: 1 of" in result.stdout


def test_a_module_with_a_MODULE_entry_is_declared_without_any_site_entries(a_tree):
    """The other route stays open: the original five words at module granularity are unchanged
    by this act, and seventeen of the nineteen modules still take that route."""
    result = _run(a_tree)
    assert "[ESTABLISHED ] crash_detector.time_utc" in result.stdout
    assert "UNDECLARED MODULE: crash_detector.time_utc" not in result.stdout
