"""C1 — ``detail_level`` proportionality, and the two things it must never do.

BLUEPRINT §8, PID §4 (the three levels) and PID §3.2 (the constitutional refusal).

The two propositions this file exists for:

1. *** **MISSING DATA NEVER RENDERS AS CALM.** *** PID §3.2, and it needs no dial scale, so
   it is enforced NOW rather than owed with ``Q25``. Both arms.
2. *** **THE RULE LIVES IN ONE PLACE.** *** Asserted over the whole package by walking the
   source, not by reading the module that was supposed to be the only one.

**NO SOURCE IS REGISTERED BY ANYTHING IN THIS FILE** (``Q25``). Magnitudes are built with
the project's existing ``tests/dial_magnitudes.py`` helper, whose stand-in id never reaches
``raw.source_registry``.
"""

from __future__ import annotations

import ast
import pathlib
from datetime import datetime, timezone

import pytest

from crash_detector.dials.dialset import DIAL_IDS
from crash_detector.dials.reading import Degraded, Unknown, Value
from crash_detector.publication.detail_level import (
    DETAIL_ACUTE,
    DETAIL_CALM,
    DETAIL_CONTENT,
    DETAIL_ELEVATED,
    DETAIL_ORDER,
    DetailPolicy,
    DetailPolicyIncoherent,
    content_for,
    detail_level_for,
)

from dial_magnitudes import magnitude_of

EQUITY, MONETARY = DIAL_IDS
NOW = datetime(2026, 8, 23, 12, 0, 0, tzinfo=timezone.utc)

#: SYNTHETIC. The dial has no ratified scale (Q25 holds it), so these numbers mean nothing
#: outside this file and the module declares no policy of its own.
POLICY = DetailPolicy(elevated_at=0.4, acute_at=0.8, absent_data_level=DETAIL_ELEVATED)


def _value(dial_id: str, score: float) -> Value:
    return Value(
        value=magnitude_of(dial_id, score), as_of_utc=NOW, inputs_used=("test-source",)
    )


# ========================================================================================= #
# *** PID §3.2 — MISSING DATA MUST NEVER RENDER AS CALM. BOTH ARMS. ***
# ========================================================================================= #

def test_a_policy_that_renders_absent_data_as_calm_is_REFUSED():
    """THE REFUSING ARM. The prohibited rendering is unrepresentable, not discouraged."""
    with pytest.raises(DetailPolicyIncoherent) as refusal:
        DetailPolicy(elevated_at=0.4, acute_at=0.8, absent_data_level=DETAIL_CALM)
    message = str(refusal.value)
    assert "MISSING DATA MUST NEVER RENDER AS CALM" in message
    assert "PROHIBITED BEHAVIOUR" in message


def test_a_policy_that_renders_absent_data_above_calm_is_admitted():
    """THE ADMITTING ARM. A constructor refusing every policy would be vacuous."""
    for level in (DETAIL_ELEVATED, DETAIL_ACUTE):
        policy = DetailPolicy(elevated_at=0.4, acute_at=0.8, absent_data_level=level)
        assert policy.absent_data_level == level


def test_an_unknown_reading_never_renders_as_calm():
    reading = Unknown(
        reason="NO_SOURCE_REGISTERED", since_utc=NOW, missing_inputs=()
    )
    level = detail_level_for(reading, dial_slot=EQUITY, policy=POLICY)
    assert level != DETAIL_CALM
    assert level == DETAIL_ELEVATED


def test_a_degraded_reading_never_renders_as_calm_even_with_a_tiny_score():
    """*** THE CASE THAT MATTERS. ***

    The magnitude is 0.01 — far below the calm threshold — so a naive implementation that
    read the number and ignored the constructor would return ``calm`` for a reading whose
    inputs were missing. That is precisely *"rendering stale or missing data as calm"*.
    """
    reading = Degraded(
        value=magnitude_of(EQUITY, 0.01),
        as_of_utc=NOW,
        missing_inputs=("absent-input",),
        reason="INPUT_MISSING",
    )
    assert detail_level_for(reading, dial_slot=EQUITY, policy=POLICY) != DETAIL_CALM


def test_the_SAME_score_on_a_VALUE_reading_does_render_as_calm():
    """THE CONTRAST THAT MAKES THE TEST ABOVE MEAN SOMETHING.

    Same number, same dial, same policy. **Only the constructor moved**, and the answer
    changed — so the refusal above is caused by the damage and not by the threshold.
    """
    assert detail_level_for(_value(EQUITY, 0.01), dial_slot=EQUITY, policy=POLICY) == (
        DETAIL_CALM
    )


# ========================================================================================= #
# THE THREE LEVELS AND WHAT EACH EMITS ARE PID §4, VERBATIM
# ========================================================================================= #

def test_the_levels_are_exactly_the_three_the_pid_names_in_its_order():
    assert DETAIL_ORDER == ("calm", "elevated", "acute")


def test_what_each_level_emits_is_the_ratified_clause():
    assert content_for(DETAIL_CALM) == ("dial", "one_line")
    assert content_for(DETAIL_ELEVATED) == (
        "dial", "one_line", "contributing_categories",
    )
    assert content_for(DETAIL_ACUTE) == (
        "dial", "one_line", "contributing_categories", "contributions_ranked",
    )


def test_detail_is_monotone_in_risk():
    """'Proportional to risk' means each level emits everything the one below it does."""
    for lower, higher in zip(DETAIL_ORDER[:-1], DETAIL_ORDER[1:]):
        assert set(DETAIL_CONTENT[lower]) < set(DETAIL_CONTENT[higher])


def test_an_undeclared_level_emits_nothing_and_raises():
    with pytest.raises(DetailPolicyIncoherent):
        content_for("catastrophic")


@pytest.mark.parametrize(
    "score,expected",
    [(0.0, DETAIL_CALM), (0.39, DETAIL_CALM), (0.4, DETAIL_ELEVATED),
     (0.79, DETAIL_ELEVATED), (0.8, DETAIL_ACUTE), (1.0, DETAIL_ACUTE)],
)
def test_the_bands_do_not_overlap_and_the_boundaries_are_where_declared(score, expected):
    assert detail_level_for(_value(EQUITY, score), dial_slot=EQUITY, policy=POLICY) == (
        expected
    )


# ========================================================================================= #
# *** PER DIAL. THERE IS NO CROSS-DIAL ROUTE. (CD-AC-002) ***
# ========================================================================================= #

def test_the_level_is_decided_for_one_reading_and_one_slot():
    import inspect

    signature = inspect.signature(detail_level_for)
    assert list(signature.parameters) == ["reading", "dial_slot", "policy"]


def test_a_magnitude_from_the_OTHER_dial_cannot_be_scored_into_this_slot():
    """The existing provenance gate is what carries this, not a check repeated here."""
    from crash_detector.publication.dial_scalar import DialProvenanceRefused

    wrong_dial = Value(
        value=magnitude_of(MONETARY, 0.9), as_of_utc=NOW, inputs_used=("test-source",)
    )
    with pytest.raises(DialProvenanceRefused):
        detail_level_for(wrong_dial, dial_slot=EQUITY, policy=POLICY)


def test_each_dial_gets_its_own_level_and_they_may_differ():
    """Two dials, two answers, computed separately. **Nothing combines them.**"""
    equity = detail_level_for(_value(EQUITY, 0.9), dial_slot=EQUITY, policy=POLICY)
    monetary = detail_level_for(_value(MONETARY, 0.1), dial_slot=MONETARY, policy=POLICY)
    assert equity == DETAIL_ACUTE
    assert monetary == DETAIL_CALM


def test_no_function_in_the_module_takes_two_readings():
    """A level derived from BOTH dials is the CD-AC-002 shape reached one step across."""
    import crash_detector.publication.detail_level as module

    path = pathlib.Path(module.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names = [argument.arg for argument in node.args.args + node.args.kwonlyargs]
            reading_like = [n for n in names if "reading" in n or "dial_slot" in n]
            assert len(reading_like) <= 2, (node.name, names)
            assert not any(
                n in ("readings", "dial_slots", "both", "dialset") for n in names
            ), (node.name, names)


# ========================================================================================= #
# *** THE RULE LIVES IN ONE PLACE ***
# ========================================================================================= #

def test_only_one_module_decides_a_detail_level():
    """Two call sites that each decide how much detail to emit IS the defect.

    Walked over the whole package: the level vocabulary and the content mapping may be
    NAMED anywhere (a renderer must be able to compare against them) but the DECISION —
    a literal level string being produced by a comparison — belongs to one module.
    """
    src_root = pathlib.Path(__file__).resolve().parents[1] / "src" / "crash_detector"
    owner = src_root / "publication" / "detail_level.py"
    paths = sorted(src_root.rglob("*.py"))
    assert owner in paths

    offenders = []
    for path in paths:
        if path == owner:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                body = getattr(node, "body", None) or []
                if (
                    body
                    and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)
                ):
                    docstrings.add(id(body[0].value))

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in docstrings
                and node.value in DETAIL_ORDER
            ):
                offenders.append(f"{path.relative_to(src_root)}:{node.lineno}")

    assert offenders == [], (
        "a detail level literal is produced outside the one module that owns the rule: "
        f"{offenders}. The surfaces render what they are given; they do not decide."
    )


def test_that_scan_would_catch_a_second_decision_site():
    """**THE VACUITY GUARD.**"""
    planted = ast.parse('def render(score):\n    return "acute" if score > 9 else "calm"\n')
    found = [
        node.value
        for node in ast.walk(planted)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value in DETAIL_ORDER
    ]
    assert sorted(found) == ["acute", "calm"]


def test_the_module_declares_no_ready_made_policy():
    """The thresholds need a dial SCALE, and the dial has none (Q25). No default exists."""
    import crash_detector.publication.detail_level as module

    constructed = [
        name for name, value in vars(module).items() if isinstance(value, DetailPolicy)
    ]
    assert constructed == []


# ========================================================================================= #
# *** detail_level ATTACHES PER DIAL. PO-DECISIONS-0025 RULING 5, WHICH RULED Q29. ***
#
# THIS BLOCK REPLACES ``test_detail_level_is_NOT_on_either_closed_envelope_schema``, AND THE
# REPLACEMENT IS AN ASSURANCE FINDING AGAINST THE PROJECT LEAD'S OWN RECORD (``CD-PL-F169``).
# The superseded guard asserted exactly two things:
#
#     assert "detail_level" not in schema["properties"]
#     assert "detail_level" not in schema["required"]
#
# — TOP LEVEL ONLY. **A PER-DIAL ATTACHMENT PASSED IT UNTOUCHED**, so the guard was, in the
# auditor's words, *"enforced against the rejected option and unenforced against the proposed
# one"*. It was cited as evidence that the field was absent; it could not have detected the
# arrival of the field in the form the seat itself recommended.
#
# The three propositions below are the replacement, and each has a FAILING ARM observed
# against a MUTATED COPY — never against the real contract (``CD-PL-F154`` is what planting
# in the real file costs).
# ========================================================================================= #

SCHEMA_NAMES = ("public_envelope.schema.json", "private_envelope.schema.json")
UNION_BRANCHES = ("dial_reading_value", "dial_reading_degraded", "dial_reading_unknown")


def _contracts_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[1] / "contracts"


def _schema(name: str) -> dict:
    import json

    return json.loads((_contracts_dir() / name).read_text(encoding="utf-8"))


def _assert_detail_level_attaches_per_dial(schema: dict, name: str) -> None:
    """The whole property, in one function, so the real arm and the mutated arms run
    EXACTLY the same assertions. A contrast arm that ran a different check would prove
    nothing about the check that guards the real file."""
    # 1. ABSENT AT ENVELOPE TOP LEVEL — the CD-AC-002 hazard, still live, still guarded.
    assert "detail_level" not in schema["properties"], name
    assert "detail_level" not in schema["required"], name

    # 2. PRESENT IN $defs.dial_reading — the parent closes with additionalProperties:false,
    #    and a sibling of oneOf sees the whole instance, so an undeclared key dies here.
    assert schema["$defs"]["dial_reading"]["additionalProperties"] is False, name
    assert "detail_level" in schema["$defs"]["dial_reading"]["properties"], name

    # 3. ADMITTED IN EVERY BRANCH OF THE UNION, ``UNKNOWN`` INCLUDED. Each branch closes
    #    independently, so a key admitted at the parent and not in a branch is refused by
    #    that branch — the key must be named in each branch it is to appear in.
    for branch in UNION_BRANCHES:
        subschema = schema["$defs"][branch]
        assert subschema["additionalProperties"] is False, (name, branch)
        assert "detail_level" in subschema["properties"], (name, branch)
        assert "detail_level" in subschema["required"], (name, branch)


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_detail_level_attaches_PER_DIAL_and_not_at_envelope_top_level(name):
    """*** THE RULED PLACEMENT, ASSERTED IN ALL THREE OF ITS PARTS. ***"""
    _assert_detail_level_attaches_per_dial(_schema(name), name)


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_the_UNKNOWN_branch_carries_a_level_and_that_is_the_constitutional_half(name):
    """*** PID §3.2 — 'Missing data must never render as calm.' ***

    Called out separately from the sweep above because it is the branch that matters. With
    zero registered sources every dial reads ``UNKNOWN``, so until 16B lands this is the
    ONLY branch production will exercise — and it is the one carrying the guarantee. It
    declares no ``score`` (CD-AC-001) and it MUST still declare a level, or a renderer
    meeting a level-less unknown dial decides for itself how loud to be.
    """
    unknown = _schema(name)["$defs"]["dial_reading_unknown"]
    assert "score" not in unknown["properties"], name
    assert "detail_level" in unknown["required"], name


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_the_schema_vocabulary_cannot_drift_from_the_module_that_owns_the_rule(name):
    """The enum is a SECOND place the three levels are written down. It is allowed to
    exist — a JSON contract cannot import Python — but it is not allowed to disagree."""
    declared = _schema(name)["$defs"]["detail_level"]["enum"]
    assert tuple(declared) == DETAIL_ORDER, name


# --- THE FAILING ARMS. A GUARD WHOSE FAILING ARM WAS NEVER OBSERVED IS UNTESTED. --------- #

@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_the_guard_FAILS_when_detail_level_is_moved_to_envelope_top_level(name):
    """*** THE ARM THE SUPERSEDED GUARD COULD NOT HAVE HAD. ***

    This mutation is the ``CD-AC-002`` hazard itself: one envelope-level level, which would
    have to be derived from BOTH readings. The old guard DID catch this one — it is the
    'rejected option' it was enforced against — and the replacement must keep catching it.
    """
    import copy

    mutated = copy.deepcopy(_schema(name))
    mutated["properties"]["detail_level"] = {"type": "string"}
    with pytest.raises(AssertionError):
        _assert_detail_level_attaches_per_dial(mutated, name)


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_the_guard_FAILS_when_detail_level_is_removed_from_dial_reading(name):
    """*** THE ARM THE SUPERSEDED GUARD DEMONSTRABLY DID NOT HAVE. ***

    Remove the field from the dial object entirely and the old two-line guard PASSES — it
    only ever looked at the top level, where the field is absent in both the correct and
    the broken state. This one fails, which is the whole of ``CD-PL-F169``'s remedy.
    """
    import copy

    mutated = copy.deepcopy(_schema(name))
    del mutated["$defs"]["dial_reading"]["properties"]["detail_level"]
    for branch in UNION_BRANCHES:
        mutated["$defs"][branch]["properties"].pop("detail_level", None)
        mutated["$defs"][branch]["required"] = [
            key for key in mutated["$defs"][branch]["required"] if key != "detail_level"
        ]
    with pytest.raises(AssertionError):
        _assert_detail_level_attaches_per_dial(mutated, name)


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_the_guard_FAILS_when_only_the_UNKNOWN_branch_loses_its_level(name):
    """THE NARROWEST MUTATION, AND THE ONE MOST LIKELY TO HAPPEN BY ACCIDENT.

    An editor who thinks 'an unknown dial has no data, so it needs no level' removes
    exactly this. The schema still LOOKS wired — two branches carry it — and the branch
    that is 100% of production traffic today has quietly stopped requiring it.
    """
    import copy

    mutated = copy.deepcopy(_schema(name))
    mutated["$defs"]["dial_reading_unknown"]["required"] = [
        key
        for key in mutated["$defs"]["dial_reading_unknown"]["required"]
        if key != "detail_level"
    ]
    with pytest.raises(AssertionError):
        _assert_detail_level_attaches_per_dial(mutated, name)


def test_the_superseded_guard_would_have_PASSED_the_per_dial_attachment():
    """*** ``CD-PL-F169`` REPRODUCED AS AN EXECUTABLE FACT, NOT AS A CLAIM IN A LOG. ***

    The exact two assertions the old test made, run against the CURRENT contracts — the
    ones that DO carry ``detail_level`` per dial. They pass. That is the defect: the guard
    was cited as evidence of absence and is satisfied by presence.
    """
    for name in SCHEMA_NAMES:
        schema = _schema(name)
        assert "detail_level" not in schema["properties"], name
        assert "detail_level" not in schema["required"], name
        # ...and yet:
        assert "detail_level" in schema["$defs"]["dial_reading"]["properties"], name


# --- POLICY COHERENCE --------------------------------------------------------------------- #

def test_thresholds_that_do_not_ascend_are_refused():
    with pytest.raises(DetailPolicyIncoherent) as refusal:
        DetailPolicy(elevated_at=0.8, acute_at=0.4, absent_data_level=DETAIL_ELEVATED)
    assert "unreachable" in str(refusal.value)


def test_equal_thresholds_are_refused():
    with pytest.raises(DetailPolicyIncoherent):
        DetailPolicy(elevated_at=0.5, acute_at=0.5, absent_data_level=DETAIL_ELEVATED)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), "0.4", True])
def test_an_unusable_threshold_is_refused(bad):
    with pytest.raises(DetailPolicyIncoherent):
        DetailPolicy(elevated_at=bad, acute_at=0.8, absent_data_level=DETAIL_ELEVATED)


def test_a_bare_pair_of_numbers_is_not_a_policy():
    with pytest.raises(TypeError):
        detail_level_for(_value(EQUITY, 0.5), dial_slot=EQUITY, policy=(0.4, 0.8))


def test_the_policy_may_not_be_subclassed():
    with pytest.raises(TypeError):
        class Lenient(DetailPolicy):  # pragma: no cover - class body never runs
            pass
