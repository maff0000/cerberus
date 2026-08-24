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

----

*** **THIS FILE IS NOW NAMED BY THE REGISTER, AND UNTIL WO-3 INCREMENT 16B IT WAS NOT.** ***

MEASURED at ``CD-DISPATCH-INC16B-ENGINEER`` §2, on a tree with the whole of 16A-FIX's
constitutional narrowing reverted: **every one of the fourteen register instruments exited
exactly as it does on the clean tree**, and the only failures anywhere in ``pytest tests/ -q``
were **nine assertions in this file** — which no ``execute:`` line in ``required-tests.yaml``
ran. The register declared 29 ``execute:`` lines, 14 of them naming pytest files, and this was
not one of the 14. *A memorial, not a guard.* At increment 16B this file was added to
``CD-RT-001-ABSENCE-RENDERS-UNKNOWN``'s declared command — **additively; nothing was removed
from it and nothing was reordered** — which is the same growth that entry took at WO-2R2
increment 1c and for the same reason: that entry carries the RENDERING half of ``CD-AC-001``,
and *"renders as calm"* is *"renders as a number"* one level up.

**DO NOT READ THAT AS THE DISCHARGE OF ``PO-DECISIONS-0026`` RULING 9.** The ruling requires
the guarantee to be carried by *"a live instrument, not a memorial in tests"*, and a pytest
file the gate happens to name is still a pytest file. **The live instrument is
``tools/register/check_missing_data_never_calm.py`` (``CD-RT-001-MISSING-DATA-NEVER-CALM``)**,
which drives ``refuse_unless_publishable`` itself on both surfaces at every dial slot. This
file remains what it has always been: the propositions, asserted close to the code.
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
from crash_detector.publication.envelope_contract import (
    CONTRACTS_DIR_ENV_VAR,
    EnvelopeSurface,
    PublicationRefused,
    refuse_unless_publishable,
)

from dial_magnitudes import magnitude_of
from publication_fakes import (
    degraded_dial,
    private_envelope,
    public_envelope,
    unknown_dial,
)

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


def _two_reading_offenders(tree) -> list:
    """Functions taking more than one reading, or more than one dial slot.

    *** CORRECTED AT WO-3 INCREMENT 16A-FIX. THE PREVIOUS COUNTER WAS NAMED FOR A CLAUSE IT
    DID NOT ENFORCE — THE FOURTH RECORDED INSTANCE OF THAT PATTERN ON THIS PROJECT. ***

    What it was, verbatim::

        reading_like = [n for n in names if "reading" in n or "dial_slot" in n]
        assert len(reading_like) <= 2, (node.name, names)

    **ONE bucket for both concepts, and a ceiling of two.** The ceiling was two because the
    module's own ``detail_level_for(reading, *, dial_slot, policy)`` puts one of each into
    that single bucket. The consequence, PROVED against a planted function rather than
    argued: ``def level_for_both(reading_a, reading_b, *, policy)`` yields
    ``reading_like == ['reading_a', 'reading_b']``, length 2, **and PASSES** — so the guard
    named *"no function in the module takes two readings"* admitted precisely a function
    taking two readings, which is the ``CD-AC-002`` shape it exists to forbid.

    Counting the two concepts SEPARATELY, at most one each, enforces the name. The real
    module is unchanged by the correction and the planted function is caught; both arms are
    asserted below.
    """
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        names = [argument.arg for argument in node.args.args + node.args.kwonlyargs]
        readings = [n for n in names if "reading" in n]
        slots = [n for n in names if "dial_slot" in n]
        if len(readings) > 1 or len(slots) > 1:
            offenders.append((node.name, names))
        if any(n in ("readings", "dial_slots", "both", "dialset") for n in names):
            offenders.append((node.name, names))
    return offenders


def test_no_function_in_the_module_takes_two_readings():
    """A level derived from BOTH dials is the CD-AC-002 shape reached one step across."""
    import crash_detector.publication.detail_level as module

    path = pathlib.Path(module.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assert _two_reading_offenders(tree) == []


def test_that_two_reading_scan_would_CATCH_a_function_taking_two_readings():
    """*** THE VACUITY GUARD THE COUNTER DID NOT HAVE, AND WHY IT NOW EXISTS. ***

    Run the exact scan against a planted two-reading function. Under the superseded
    ``len(reading_like) <= 2`` counter this planted function PASSED.
    """
    planted = ast.parse(
        "def level_for_both(reading_a, reading_b, *, policy):\n    return 'acute'\n"
    )
    assert _two_reading_offenders(planted) == [
        ("level_for_both", ["reading_a", "reading_b", "policy"])
    ]

    # ...and the shape the module legitimately has is still admitted.
    permitted = ast.parse(
        "def detail_level_for(reading, *, dial_slot, policy):\n    return 'calm'\n"
    )
    assert _two_reading_offenders(permitted) == []


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

#: The two branches PID §3.2 is ABOUT. ``VALUE`` is deliberately not here: a genuinely calm
#: reading backed by a real number is the whole reason ``calm`` exists.
#:
#: ``DEGRADED`` is in this tuple as a DECISION, not an assumption, and the evidence is
#: :func:`detail_level_for` itself — its ``on_degraded`` branch returns
#: ``policy.absent_data_level``, IDENTICALLY to ``on_unknown``, and never reaches
#: ``_level_for_score``. The module already treats a degraded reading as missing data; before
#: 16A-FIX the CONTRACT did not agree, and a contract that admits what the code cannot
#: produce is the gap that let this defect through. ``ABSENT_DATA_BRANCHES`` is asserted
#: against the module's actual behaviour below, so this comment cannot quietly become false.
ABSENT_DATA_BRANCHES = ("dial_reading_degraded", "dial_reading_unknown")

ABSENT_DATA_LEVEL_TYPE = "absent_data_detail_level"

ADMITTED = "ADMITTED"
REFUSED = "REFUSED"

#: The two missing-data dial shapes, as the fakes build them. Keyed by the state they carry
#: so a failure message names the branch rather than a lambda.
MISSING_DATA_DIALS = {"UNKNOWN": unknown_dial, "DEGRADED": degraded_dial}


def _contracts_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[1] / "contracts"


# --- THE LIVE GATE, NOT THE SCHEMA KEYS -------------------------------------------------- #

def _dial_with_level(builder, level: "str | None") -> dict:
    """A dial from ``builder`` carrying ``level`` — or carrying none when ``level`` is None."""
    dial = builder()
    if level is None:
        del dial["detail_level"]
    else:
        dial["detail_level"] = level
    return dial


def _verdict(surface: EnvelopeSurface, dial: dict) -> str:
    """*** WHAT THE PRODUCT'S OWN REFUSAL FUNCTION SAYS ABOUT A REAL ENVELOPE. ***

    Returns :data:`ADMITTED` or :data:`REFUSED` rather than raising, so a caller can assert
    on the ADMITTING arm with the same expression it uses for the refusing one. A helper
    that only knew how to assert refusals could not have caught a contract that refuses
    everything.
    """
    build = public_envelope if surface is EnvelopeSurface.PUBLIC else private_envelope
    try:
        refuse_unless_publishable(build(equity_crash=dial), surface=surface)
        return ADMITTED
    except PublicationRefused:
        return REFUSED


def _assert_missing_data_never_renders_as_calm() -> None:
    """*** PID §3.2 AS ONE EXECUTABLE PROPERTY, OVER BOTH SURFACES AND BOTH BRANCHES. ***

    The whole property in ONE function, so the real arm and every mutated arm run EXACTLY
    the same assertions. A contrast arm running a different check would prove nothing about
    the check that guards the real contracts.

    Reads the contracts through ``$CD_CONTRACTS_DIR``, which is how the mutated arms point
    it at a copy — **the real files are never written to** (``CD-PL-F154``).
    """
    for surface in EnvelopeSurface:
        for state, builder in MISSING_DATA_DIALS.items():
            where = (surface.value, state)

            # 1. *** THE CLAUSE. *** Missing data must never render as calm.
            assert _verdict(surface, _dial_with_level(builder, DETAIL_CALM)) == REFUSED, where

            # 2. NON-VACUITY. The branch must still be publishable, or §3.2 is satisfied by
            #    breaking the only state this product can currently emit.
            for admissible in (DETAIL_ELEVATED, DETAIL_ACUTE):
                assert _verdict(surface, _dial_with_level(builder, admissible)) == (
                    ADMITTED
                ), (where, admissible)

            # 3. THE PROBE IS LIVE, and presence is still required.
            assert _verdict(surface, _dial_with_level(builder, "banana")) == REFUSED, where
            assert _verdict(surface, _dial_with_level(builder, None)) == REFUSED, where


def _contracts_copy_with_calm_restored(tmp_path: pathlib.Path, *branches: str) -> pathlib.Path:
    """A COPY of both closed contracts with 16A-FIX **REVERTED** on ``branches``.

    The mutation is the exact inverse of the fix: the branch's ``detail_level`` goes back to
    referencing the full ``#/$defs/detail_level``, which is what it referenced at ``53f639a``
    when ``calm`` was ADMITTED. **NEVER THE REAL FILES** (``CD-PL-F154``).

    The anchor is asserted before it is replaced. A mutation that silently matched nothing
    would produce a correct subject dressed as a broken one, and the arm would pass by not
    testing anything — the same trap ``tests/test_deploy_portability.py::_subject`` guards.
    """
    import json

    target = tmp_path / "contracts"
    target.mkdir()
    for name in SCHEMA_NAMES:
        schema = _schema(name)
        for branch in branches:
            anchor = schema["$defs"][branch]["properties"]["detail_level"]
            assert anchor == {"$ref": f"#/$defs/{ABSENT_DATA_LEVEL_TYPE}"}, (
                f"the mutation anchor for {name}:{branch} is {anchor!r}, not the narrowed "
                "type this arm exists to revert; the arm would be vacuous"
            )
            schema["$defs"][branch]["properties"]["detail_level"] = {
                "$ref": "#/$defs/detail_level"
            }
        (target / name).write_text(json.dumps(schema, indent=2), encoding="utf-8")
    return target


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


@pytest.mark.parametrize("surface", list(EnvelopeSurface))
def test_the_UNKNOWN_branch_carries_a_level_and_that_is_the_constitutional_half(surface):
    """*** PID §3.2 — 'Missing data must never render as calm.' MEASURED, NOT INSPECTED. ***

    ===================================================================================
    RE-POINTED AT ITS OWN CLAUSE AT WO-3 INCREMENT 16A-FIX. WHAT IT USED TO ASSERT, AND
    WHY THAT WAS NOT ENOUGH — RECORDED, NOT ERASED (CD-ASR-WO3-03, RED).
    ===================================================================================
    This test was headed *"PID §3.2"* and its whole body was two STRUCTURAL assertions::

        unknown = _schema(name)["$defs"]["dial_reading_unknown"]
        assert "score" not in unknown["properties"], name       # CD-AC-001, not §3.2
        assert "detail_level" in unknown["required"], name      # PRESENCE, not VALUE

    **NAMED FOR THE CLAUSE; DID NOT TEST THE CLAUSE.** §3.2 is about a VALUE — that the
    level is never ``calm``. Both assertions above are satisfied by an UNKNOWN dial
    carrying ``detail_level: "calm"``, and at ``53f639a`` such an envelope was in fact
    ADMITTED by :func:`refuse_unless_publishable` on BOTH surfaces. The guard passed
    while the constitution was breached, which is the third recorded instance of this
    pattern on this project (``CD-PL-F169``, ``CD-ASR-WO3-02`` F06/F07, this one).

    Neither assertion is lost: ``score`` absent on ``UNKNOWN`` is CD-AC-001 and is guarded
    at ``tests/test_envelope_contracts.py::test_the_unknown_branch_declares_no_score_
    property_at_all``; ``detail_level`` required in every branch is guarded above by
    :func:`_assert_detail_level_attaches_per_dial`.

    **IT IS NOW AN END-TO-END BEHAVIOURAL ASSERTION THROUGH THE LIVE GATE.** A structural
    assertion about schema keys is what let this through twice; this one builds a real
    envelope and asks the real refusal function, so it fails if the CONTRACT is widened,
    if the ``$defs`` are re-plumbed, or if the gate stops consulting the contract at all.
    """
    assert _verdict(surface, _dial_with_level(unknown_dial, DETAIL_CALM)) == REFUSED
    # *** THE NON-VACUITY ARM. A contract that refused every UNKNOWN dial would satisfy
    # PID §3.2 by making the only state this product can currently publish unpublishable.
    assert _verdict(surface, _dial_with_level(unknown_dial, DETAIL_ELEVATED)) == ADMITTED


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


# ========================================================================================= #
# *** PID §3.2 HELD IN THE SCHEMA — AND THE ARMS THAT FAIL WHEN IT IS NOT. ***
#
# WO-3 INCREMENT 16A-FIX, ANSWERING CD-ASR-WO3-03's RED.
#
# The Project Lead applied this very fix on a copy at 53f639a and measured that `calm`
# became REFUSED on both surfaces AND ALL 43 detail_level TESTS STILL PASSED. *** A GUARD
# THAT WOULD NEITHER REQUIRE NOR FORBID ITS OWN REMEDY IS NOT GUARDING THE THING IT IS
# NAMED FOR. *** Everything below exists so that stops being true: revert the fix and these
# arms go red.
# ========================================================================================= #

def test_the_two_narrowed_branches_are_the_two_the_MODULE_treats_as_missing_data():
    """*** THE PRODUCT DECISION, CHECKED AGAINST THE CODE RATHER THAN ASSUMED. ***

    Narrowing ``DEGRADED`` was a judgement (dispatch §3: *"if you conclude DEGRADED should
    keep calm, say so"*), and this is the evidence it rests on: ``detail_level_for`` returns
    ``policy.absent_data_level`` for a ``Degraded`` reading **exactly as it does for an
    ``Unknown`` one**, whatever the score. The score used here is 0.01 — far below
    ``elevated_at`` — so a naive implementation reading the number would say ``calm``.

    If a future change makes ``DEGRADED`` score-derived, this test fails and the contract
    narrowing must be revisited. **The comment on ABSENT_DATA_BRANCHES cannot quietly rot.**
    """
    unknown = Unknown(reason="NO_SOURCE_REGISTERED", since_utc=NOW, missing_inputs=())
    degraded = Degraded(
        value=magnitude_of(EQUITY, 0.01),
        as_of_utc=NOW,
        missing_inputs=("absent-input",),
        reason="INPUT_MISSING",
    )
    for reading in (unknown, degraded):
        assert detail_level_for(reading, dial_slot=EQUITY, policy=POLICY) == (
            POLICY.absent_data_level
        )
    # ...and the policy that supplies it can never say calm.
    with pytest.raises(DetailPolicyIncoherent):
        DetailPolicy(elevated_at=0.4, acute_at=0.8, absent_data_level=DETAIL_CALM)


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_the_absent_data_branches_declare_a_vocabulary_that_EXCLUDES_calm(name):
    """The structural half — kept, but no longer the ONLY half (see the behavioural arms)."""
    schema = _schema(name)
    assert schema["$defs"][ABSENT_DATA_LEVEL_TYPE]["enum"] == [DETAIL_ELEVATED, DETAIL_ACUTE]
    assert DETAIL_CALM not in schema["$defs"][ABSENT_DATA_LEVEL_TYPE]["enum"], name
    for branch in ABSENT_DATA_BRANCHES:
        assert schema["$defs"][branch]["properties"]["detail_level"] == {
            "$ref": f"#/$defs/{ABSENT_DATA_LEVEL_TYPE}"
        }, (name, branch)
    # *** VALUE KEEPS calm. Narrowing it would satisfy PID §3.2 vacuously. ***
    assert schema["$defs"]["dial_reading_value"]["properties"]["detail_level"] == {
        "$ref": "#/$defs/detail_level"
    }, name
    assert DETAIL_CALM in schema["$defs"]["detail_level"]["enum"], name


def test_missing_data_never_renders_as_calm_THROUGH_THE_LIVE_GATE():
    """*** THE ACCEPTANCE PROPERTY. Both surfaces, both missing-data branches, four rows. ***

    This is the dispatch's §5 probe as a standing test rather than a one-off measurement.
    """
    _assert_missing_data_never_renders_as_calm()


# --- THE FAILING ARMS. F1 WITHOUT THESE IS A FIX THE NEXT REFACTOR SILENTLY UNDOES. ------- #

@pytest.mark.parametrize("branch", ABSENT_DATA_BRANCHES)
def test_the_guard_FAILS_when_calm_is_restored_to_a_missing_data_branch(
    branch, tmp_path, monkeypatch
):
    """*** THE ARM 16A DID NOT HAVE, AND THE REASON ITS RED WAS INVISIBLE. ***

    Revert 16A-FIX on ONE branch, on a COPY, and the property above must go RED. Run this
    against the pre-fix contracts and it is exactly the state CD-ASR-WO3-03 found.

    Parametrised per branch so that re-widening ``DEGRADED`` alone is caught too — a
    mutation that only ``UNKNOWN`` guarded would leave half the fix unprotected.
    """
    mutated = _contracts_copy_with_calm_restored(tmp_path, branch)
    monkeypatch.setenv(CONTRACTS_DIR_ENV_VAR, str(mutated))

    with pytest.raises(AssertionError):
        _assert_missing_data_never_renders_as_calm()


def test_the_guard_FAILS_when_calm_is_restored_to_BOTH_missing_data_branches(
    tmp_path, monkeypatch
):
    """The full revert of F1 — the exact contract shape at ``53f639a``."""
    mutated = _contracts_copy_with_calm_restored(tmp_path, *ABSENT_DATA_BRANCHES)
    monkeypatch.setenv(CONTRACTS_DIR_ENV_VAR, str(mutated))

    with pytest.raises(AssertionError):
        _assert_missing_data_never_renders_as_calm()


def test_the_mutated_copy_reproduces_the_RED_and_leaves_the_real_contracts_untouched(
    tmp_path, monkeypatch
):
    """*** CD-ASR-WO3-03's RED, REPRODUCED AS AN EXECUTABLE FACT RATHER THAN A CLAIM. ***

    Against the reverted copy an UNKNOWN dial carrying ``calm`` is ADMITTED on BOTH
    surfaces — the defect verbatim. Against the REAL contracts, in the same test, it is
    REFUSED. **The real files are read and never written** (``CD-PL-F154``).
    """
    before = {name: (_contracts_dir() / name).read_bytes() for name in SCHEMA_NAMES}

    mutated = _contracts_copy_with_calm_restored(tmp_path, *ABSENT_DATA_BRANCHES)
    monkeypatch.setenv(CONTRACTS_DIR_ENV_VAR, str(mutated))
    for surface in EnvelopeSurface:
        assert _verdict(surface, _dial_with_level(unknown_dial, DETAIL_CALM)) == (
            ADMITTED
        ), f"the mutation did not reproduce the RED on {surface.value}"

    monkeypatch.delenv(CONTRACTS_DIR_ENV_VAR)
    for surface in EnvelopeSurface:
        assert _verdict(surface, _dial_with_level(unknown_dial, DETAIL_CALM)) == REFUSED

    assert {name: (_contracts_dir() / name).read_bytes() for name in SCHEMA_NAMES} == before


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
