"""A scalar derived from BOTH dials is unrepresentable and unpublishable (CD-AC-002).

Closing CD-ASR-F01 (HIGH). The Product Owner's ruling is that "the closure must make any
scalar derived from both dial types unrepresentable/unpublishable **as a class**, not ban
known spellings", and "unrepresentable" is a RUNTIME property. So these tests do not read
source and do not inspect a checker's exit code. They EXECUTE the routes and watch the
interpreter or the constructor refuse.

The two escaped variants that produced the finding are reproduced here as
``test_variant_e01_*`` and ``test_variant_e02_*``, in the auditor's own shape, so that a
regression in the closure fails a DECLARED register test rather than only a variant patch
somebody has to remember to re-run.

WHAT IS DELIBERATELY NOT ASSERTED HERE, so that the boundary is visible rather than
discovered: that two numbers already released for their own single dials cannot be added.
They can — they are two ``float`` objects and Python adds floats. That residue is declared
in ``src/crash_detector/dials/magnitude.py`` (boundary A), in the header of
``tools/register/check_no_blend.py`` (boundary 6), in the register entry and in the
execution contract. What is asserted here is that the result cannot be published as a dial
(``test_a_released_number_cannot_be_published_as_a_dial``).
"""

from __future__ import annotations

import functools
import json
import math
import operator
import pickle
import statistics
from copy import deepcopy

import pytest

from crash_detector.dials.magnitude import (
    DECLARED_MAGNITUDE_MEMBERS,
    TOLERATED_INTERPRETER_MACHINERY,
    CrossDialCombination,
    DialMagnitude,
    MagnitudeSurfaceViolated,
    ScoreOutOfRange,
    combine_within_one_dial,
    sole_dial_of,
)
from crash_detector.dials.provenance import (
    DECLARED_QUANTITY_MEMBERS,
    SAME_DIAL_REDUCTIONS,
    TOLERATED_QUANTITY_MACHINERY,
    DeclaredQuantity,
    QuantityProvenanceMissing,
    SameDialReduction,
    UndeclaredReduction,
    derived_within_one_dial,
    observed_for_dial,
)
from crash_detector.dials.scores import (
    ARITHMETIC_DUNDERS,
    EQUITY_DIAL_ID,
    MONETARY_DIAL_ID,
)
from crash_detector.publication.dial_scalar import (
    PUBLISHABLE_DIAL_SLOTS,
    DialProvenanceRefused,
    number_for_dial_slot,
)

from dial_magnitudes import TEST_SOURCE_IDS, magnitude_of, quantity_of

EQUITY = magnitude_of(EQUITY_DIAL_ID, 0.9)
MONETARY = magnitude_of(MONETARY_DIAL_ID, 0.1)

#: An INDEPENDENT copy of the declared surface, as ``tests/test_reading.py`` keeps one for
#: the Reading constructors and for the same reason: editing the declaration in the module
#: to admit a new member must fail the declared test rather than widen the guard.
EXPECTED_MAGNITUDE_SURFACE = frozenset(
    {
        "__doc__",
        "__module__",
        "__slots__",
        "_DialMagnitude__quantity",
        "provenance",
        "__init__",
        "__setattr__",
        "__delattr__",
        "__eq__",
        "__ne__",
        "__hash__",
        "__repr__",
        "__getstate__",
        "__setstate__",
        "quantity_for",
    }
)


# --- the surface is DECLARED, not merely free of the members somebody listed ----------- #

def test_the_declared_surface_matches_this_files_independent_copy():
    assert DECLARED_MAGNITUDE_MEMBERS == EXPECTED_MAGNITUDE_SURFACE


def test_the_live_class_surface_is_exactly_the_declared_one():
    observed = frozenset(vars(DialMagnitude))
    assert observed - TOLERATED_INTERPRETER_MACHINERY == DECLARED_MAGNITUDE_MEMBERS


def test_the_magnitude_type_cannot_be_subclassed():
    with pytest.raises(MagnitudeSurfaceViolated):
        type("Sneaky", (DialMagnitude,), {"__float__": lambda self: 0.0})


def test_a_member_cannot_be_installed_on_the_sealed_class():
    with pytest.raises(MagnitudeSurfaceViolated):
        DialMagnitude.__float__ = lambda self: 0.0


def test_a_declared_member_cannot_be_deleted_from_the_sealed_class():
    with pytest.raises(MagnitudeSurfaceViolated):
        del DialMagnitude.quantity_for


def test_an_instance_carries_no_dict_so_nothing_can_be_injected():
    assert DialMagnitude.__dictoffset__ == 0
    with pytest.raises(MagnitudeSurfaceViolated):
        EQUITY.blended = 0.5


def test_a_magnitude_is_immutable():
    with pytest.raises(MagnitudeSurfaceViolated):
        EQUITY.provenance = frozenset({EQUITY_DIAL_ID, MONETARY_DIAL_ID})


# --- non-coercible: the interpreter refuses, whatever the route ------------------------ #

BINARY_OPERATORS = [
    operator.add, operator.sub, operator.mul, operator.truediv, operator.floordiv,
    operator.mod, operator.pow, operator.matmul,
    operator.and_, operator.or_, operator.xor, operator.lshift, operator.rshift,
    divmod,
]


@pytest.mark.parametrize("op", BINARY_OPERATORS, ids=lambda o: o.__name__)
def test_no_binary_operator_combines_the_two_magnitudes(op):
    with pytest.raises(TypeError):
        op(EQUITY, MONETARY)
    with pytest.raises(TypeError):
        op(MONETARY, EQUITY)


@pytest.mark.parametrize("op", BINARY_OPERATORS, ids=lambda o: o.__name__)
def test_no_magnitude_combines_with_a_bare_number_either(op):
    """Weighting one dial before blending is still blending."""
    for magnitude in (EQUITY, MONETARY):
        with pytest.raises(TypeError):
            op(magnitude, 2.0)
        with pytest.raises(TypeError):
            op(2.0, magnitude)


@pytest.mark.parametrize("coerce", [int, float, complex, round, math.floor, math.ceil])
def test_a_magnitude_cannot_be_coerced_to_a_bare_number(coerce):
    with pytest.raises(TypeError):
        coerce(EQUITY)


def test_the_magnitude_type_defines_no_arithmetic_or_coercion_dunder():
    defined = [name for name in ARITHMETIC_DUNDERS if name in vars(DialMagnitude)]
    assert defined == [], f"DialMagnitude defines {defined}"


def test_no_ancestor_of_the_magnitude_type_defines_one_either():
    for ancestor in DialMagnitude.__mro__:
        if ancestor is object:
            continue
        defined = [name for name in ARITHMETIC_DUNDERS if name in vars(ancestor)]
        assert defined == [], f"{ancestor.__name__} defines {defined}"


@pytest.mark.parametrize(
    "reduce",
    [
        lambda pair: sum(pair),
        lambda pair: math.fsum(pair),
        lambda pair: statistics.mean(pair),
        lambda pair: statistics.median(pair),
        lambda pair: functools.reduce(operator.add, pair),
        lambda pair: max(pair),
        lambda pair: min(pair),
        lambda pair: sorted(pair),
    ],
    ids=["sum", "fsum", "mean", "median", "reduce", "max", "min", "sorted"],
)
def test_every_aggregation_over_the_two_magnitudes_is_a_type_error(reduce):
    """The CLASS, not the spelling. None of these needs an operator in the source, and
    `statistics` in particular reaches for `__float__` and `as_integer_ratio`, neither of
    which exists on a magnitude."""
    with pytest.raises(TypeError):
        reduce([EQUITY, MONETARY])


def test_a_magnitude_is_not_json_serialisable():
    """Serialising both to JSON and averaging downstream is a route too. It stops here."""
    with pytest.raises(TypeError):
        json.dumps({"e": EQUITY, "m": MONETARY})


def test_copying_and_pickling_do_not_strip_the_provenance():
    """A round trip that returned a bare number would be a laundering route."""
    copied = deepcopy(EQUITY)
    assert copied.provenance == frozenset({EQUITY_DIAL_ID})
    revived = pickle.loads(pickle.dumps(EQUITY))
    assert revived.provenance == frozenset({EQUITY_DIAL_ID})
    with pytest.raises(TypeError):
        revived + MONETARY


def test_the_pickle_state_is_keyed_by_the_private_slot_name():
    """CD-ENG-WO2R-F06, a finding this seat raised against its own increment-2 work.

    The first draft of `__getstate__` returned `{"dial_id": ..., "quantity": ...}`, and

        states = [m.__getstate__() for m in (equity, monetary)]
        blended = sum(s["quantity"] for s in states) / len(states)      # -> 0.5

    reached the number WITHOUT naming a dial and WITHOUT naming the private slot, so
    nothing refused it and the AST locator's RULE 3 had nothing to see. The state is now
    keyed by the slot names, so the same expression must be written
    `s["_DialMagnitude__quantity"]` — which RULE 3 reports as a string constant exactly as
    it reports the attribute. The runtime residue is unchanged and is declared.
    """
    state = EQUITY.__getstate__()
    assert set(state) == {"provenance", "_DialMagnitude__quantity"}
    assert "quantity" not in state
    assert "dial_id" not in state


def test_a_revived_magnitude_is_validated_exactly_as_a_constructed_one():
    """A pickle is untrusted input like any other. A hand-written state cannot forge a
    magnitude with two dials' provenance, none at all, or a non-finite number."""
    forged = EQUITY.__getstate__()
    forged["provenance"] = frozenset({EQUITY_DIAL_ID, MONETARY_DIAL_ID})
    revived = DialMagnitude.__new__(DialMagnitude)
    with pytest.raises(CrossDialCombination):
        revived.__setstate__(forged)

    not_a_set = EQUITY.__getstate__()
    not_a_set["provenance"] = EQUITY_DIAL_ID
    with pytest.raises(CrossDialCombination):
        DialMagnitude.__new__(DialMagnitude).__setstate__(not_a_set)

    non_finite = EQUITY.__getstate__()
    non_finite["_DialMagnitude__quantity"] = math.inf
    with pytest.raises(ScoreOutOfRange):
        DialMagnitude.__new__(DialMagnitude).__setstate__(non_finite)


def test_a_magnitude_is_not_equal_to_its_own_number():
    """Equality with a float would be coercion by another name."""
    assert EQUITY != 0.9
    assert not (EQUITY == 0.9)


# --- provenance is carried as DATA, and compared at the point of combination ------------ #

def test_provenance_is_always_exactly_one_dial():
    assert EQUITY.provenance == frozenset({EQUITY_DIAL_ID})
    assert len(MONETARY.provenance) == 1


def test_a_magnitude_cannot_be_constructed_without_naming_its_dial():
    for bad in ("", None, 0, ["equity_crash"], frozenset({EQUITY_DIAL_ID})):
        with pytest.raises(CrossDialCombination):
            DialMagnitude(dial_id=bad, quantity=0.5)


@pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan, 1, True, "0.5", None])
def test_a_magnitude_refuses_anything_that_is_not_a_finite_float(bad):
    with pytest.raises(ScoreOutOfRange):
        DialMagnitude(dial_id=EQUITY_DIAL_ID, quantity=bad)


def test_releasing_a_number_requires_naming_the_right_dial():
    assert EQUITY.quantity_for(EQUITY_DIAL_ID) == 0.9
    with pytest.raises(CrossDialCombination):
        EQUITY.quantity_for(MONETARY_DIAL_ID)


def test_combining_across_the_dials_is_refused_by_comparing_provenance():
    with pytest.raises(CrossDialCombination):
        combine_within_one_dial([EQUITY, MONETARY], using=SameDialReduction.MEAN)


def test_a_same_dial_helper_reused_across_dials_fails_when_it_is_reused():
    """The shape that arrives innocently. `mean_of` is legitimate for one dial and is
    refused the moment it is handed both — at runtime, by comparing data, not because
    anybody read the code."""

    def mean_of(magnitudes):
        return combine_within_one_dial(magnitudes, using=SameDialReduction.MEAN)

    same_dial = mean_of([EQUITY, magnitude_of(EQUITY_DIAL_ID, 0.5)])
    assert same_dial.quantity_for(EQUITY_DIAL_ID) == pytest.approx(0.7)
    with pytest.raises(CrossDialCombination):
        mean_of([EQUITY, MONETARY])


def test_same_dial_computation_still_works():
    """FALSE-POSITIVE CHECK. A closure that forbids the product is not a closure."""
    window = [
        magnitude_of(MONETARY_DIAL_ID, quantity)
        for quantity in (0.1, 0.2, 0.3, 0.4)
    ]
    rolling_mean = combine_within_one_dial(window, using=SameDialReduction.MEAN)
    assert rolling_mean.provenance == frozenset({MONETARY_DIAL_ID})
    assert rolling_mean.quantity_for(MONETARY_DIAL_ID) == pytest.approx(0.25)
    widest = combine_within_one_dial(window, using=SameDialReduction.MAX)
    assert widest.quantity_for(MONETARY_DIAL_ID) == 0.4
    narrowest = combine_within_one_dial(window, using=SameDialReduction.MIN)
    assert narrowest.quantity_for(MONETARY_DIAL_ID) == 0.1
    total = combine_within_one_dial(window, using=SameDialReduction.SUM)
    assert total.quantity_for(MONETARY_DIAL_ID) == pytest.approx(1.0)


def test_combining_nothing_is_refused():
    with pytest.raises(CrossDialCombination):
        combine_within_one_dial([], using=SameDialReduction.SUM)


def test_a_forged_multi_dial_provenance_yields_no_number():
    """`object.__setattr__` rewrites a slot on any frozen object in Python, and that is
    stated as boundary B of the module's declared limit. The direction is SAFE: a forged
    provenance makes the magnitude LESS usable, never more."""
    forged = magnitude_of(EQUITY_DIAL_ID, 0.5)
    object.__setattr__(forged, "provenance", frozenset({EQUITY_DIAL_ID, MONETARY_DIAL_ID}))
    with pytest.raises(CrossDialCombination):
        forged.quantity_for(EQUITY_DIAL_ID)
    with pytest.raises(CrossDialCombination):
        sole_dial_of(forged)
    with pytest.raises(DialProvenanceRefused):
        number_for_dial_slot(EQUITY_DIAL_ID, forged)


def test_sole_dial_of_refuses_a_bare_number_and_a_look_alike():
    class LooksLikeOne:
        provenance = frozenset({EQUITY_DIAL_ID})

    for impostor in (0.9, "0.9", LooksLikeOne()):
        with pytest.raises(CrossDialCombination):
            sole_dial_of(impostor)


# --- unpublishable: the publication boundary compares provenance ------------------------ #

def test_the_publishable_slots_are_the_two_dials():
    assert PUBLISHABLE_DIAL_SLOTS == (EQUITY_DIAL_ID, MONETARY_DIAL_ID)


def test_a_dial_magnitude_publishes_into_its_own_slot():
    """FALSE-POSITIVE CHECK: the product still works."""
    assert number_for_dial_slot(EQUITY_DIAL_ID, EQUITY) == 0.9
    assert number_for_dial_slot(MONETARY_DIAL_ID, MONETARY) == 0.1


def test_a_magnitude_cannot_be_published_into_the_other_dials_slot():
    with pytest.raises(DialProvenanceRefused):
        number_for_dial_slot(MONETARY_DIAL_ID, EQUITY)
    with pytest.raises(DialProvenanceRefused):
        number_for_dial_slot(EQUITY_DIAL_ID, MONETARY)


@pytest.mark.parametrize(
    "slot", ["combined_stress", "overall", "blended_score", "headline", ""]
)
def test_no_third_slot_accepts_a_dial_magnitude(slot):
    with pytest.raises(DialProvenanceRefused):
        number_for_dial_slot(slot, EQUITY)


def test_a_released_number_cannot_be_published_as_a_dial():
    """THE DECLARED RESIDUE, and the layer that carries it.

    Two numbers released for their own dials CAN be added — that is boundary A of the
    magnitude module's declared limit and boundary 6 of the AST check's. What cannot
    happen is publishing the result: it is a bare float with no provenance, and the gate
    takes only a magnitude.
    """
    blended = (
        EQUITY.quantity_for(EQUITY_DIAL_ID) + MONETARY.quantity_for(MONETARY_DIAL_ID)
    ) / 2.0
    assert blended == pytest.approx(0.5)
    for slot in PUBLISHABLE_DIAL_SLOTS:
        with pytest.raises(CrossDialCombination):
            number_for_dial_slot(slot, blended)


# --- the two escaped variants, executed --------------------------------------------------- #

class _Dials:
    """The shape both auditor variants reached through: two dial slots, each holding a
    reading with a magnitude. Reproduced in the test suite so a regression fails a
    DECLARED arm and not only a variant patch."""

    def __init__(self):
        self.equity = _Reading(EQUITY)
        self.monetary = _Reading(MONETARY)


class _Reading:
    def __init__(self, magnitude):
        self.value = _Score(magnitude)


class _Score:
    def __init__(self, magnitude):
        self.score = magnitude


def test_variant_e01_inter_procedural_fold_raises_when_executed():
    """`E01`: the arithmetic one call away, in a helper whose parameters are annotated
    `float` so no dial flavour reaches it. The AST check exits 0 on this and always
    will — that is boundary 1 of its declared limit. The TYPE refuses it."""

    def _fold(left: float, right: float) -> float:
        return (left + right) / 2.0

    dials = _Dials()
    with pytest.raises(TypeError):
        _fold(dials.equity.value.score, dials.monetary.value.score)


def test_variant_e02_getattr_over_string_slots_raises_when_executed():
    """`E02`, the stronger of the two: no dial marker appears in any expression, so
    nothing is ever flavoured and no static rule can fire. The TYPE refuses it."""
    slots = ("equity", "monetary")
    dials = _Dials()
    magnitudes = [getattr(dials, slot).value.score for slot in slots]
    with pytest.raises(TypeError):
        sum(magnitudes) / len(magnitudes)


# ======================================================================================= #
# THE RE-ENTRY CLOSURE — CD-PL-F54, re-opening and closing CD-ASR-F01
#
# Increment 2's structure was closed against the type being ASKED for a number and open to
# the number being READ OFF it. Nine of the Project Lead's eleven probes were refused; two
# were not, and one plausible module (`PL-Q9`) defeated the static arm and the runtime arm
# together while naming no dial and performing no arithmetic on a magnitude.
#
# These tests execute the routes and watch the constructor refuse. They do not read source
# and they do not inspect a checker's exit code: "unrepresentable" is a RUNTIME property.
#
# WHAT IS DELIBERATELY ASSERTED TO BE OPEN, so the boundary is visible rather than
# discovered: the EXITS. `test_the_exits_are_open_and_that_is_declared` asserts that a
# number can still be read out of `repr`, and
# `test_two_released_numbers_still_add_and_that_is_declared` asserts that two released
# floats still add. Both are true, both are declared, and a test that pretended otherwise
# would be the kind of false evidence this whole rework exists to correct.
# ======================================================================================= #

EXPECTED_QUANTITY_SURFACE = frozenset(
    {
        "__doc__",
        "__module__",
        "__slots__",
        "_DeclaredQuantity__value",
        "dials",
        "__init__",
        "__setattr__",
        "__delattr__",
        "__eq__",
        "__ne__",
        "__hash__",
        "__repr__",
        "__getstate__",
        "__setstate__",
        "value_for",
    }
)


def _leak(magnitude):
    """The `PL-Q4` laundering step, verbatim: a number off the repr, naming no dial."""
    return float(repr(magnitude).split("quantity=")[1].rstrip(")"))


def test_the_exits_are_open_and_that_is_declared():
    """DECLARED LIMIT, asserted so it cannot quietly stop being true or be forgotten.

    `repr` renders the quantity deliberately — hiding a value from a developer's own
    debugger is obfuscation, not structure — and it is one member of an exit class with no
    last member. This test exists so the next auditor reads the boundary here rather than
    discovering it, and so that anybody tempted to "fix" `repr` sees that the closure does
    not depend on it."""
    assert _leak(EQUITY) == 0.9
    assert _leak(MONETARY) == 0.1
    assert float(f"{EQUITY!r}".split("quantity=")[1].rstrip(")")) == 0.9


def test_two_released_numbers_still_add_and_that_is_declared():
    """DECLARED LIMIT. They are two floats and Python adds floats. `PL-Q1a` returns 1.0."""
    assert _leak(EQUITY) + _leak(MONETARY) == pytest.approx(1.0)
    released = EQUITY.quantity_for(EQUITY_DIAL_ID) + MONETARY.quantity_for(MONETARY_DIAL_ID)
    assert released == pytest.approx(1.0)


def test_a_bare_float_cannot_become_a_dial_magnitude():
    """THE CLOSURE, in one line. A number with no provenance is not a magnitude's number."""
    with pytest.raises(QuantityProvenanceMissing):
        DialMagnitude(dial_id=EQUITY_DIAL_ID, quantity=0.5)


def test_variant_pl_q4_repr_launder_and_rewrap_is_refused():
    """`PL-Q4`: launder both through repr, re-wrap the mean as the equity dial, publish.
    NOT REFUSED at a94ef97 — it constructed an EquityCrashScore of 0.5 from 0.4 and 0.6."""
    blended = (_leak(EQUITY) + _leak(MONETARY)) / 2
    with pytest.raises(QuantityProvenanceMissing):
        DialMagnitude(dial_id=EQUITY_DIAL_ID, quantity=blended)


def test_variant_pl_q5_launder_through_the_declared_door_is_refused():
    """`PL-Q5`: the same, through `quantity_for` — the DECLARED release. NOT REFUSED before.

    This one matters most of the three, because it uses nothing irregular: both numbers
    were released by naming their own single dial, exactly as the design intends."""
    blended = (
        EQUITY.quantity_for(EQUITY_DIAL_ID) + MONETARY.quantity_for(MONETARY_DIAL_ID)
    ) / 2
    with pytest.raises(QuantityProvenanceMissing):
        DialMagnitude(dial_id=EQUITY_DIAL_ID, quantity=blended)


def test_variant_pl_q6_the_publication_gate_never_sees_the_rewrapped_blend():
    """`PL-Q6`: at a94ef97 `number_for_dial_slot` RETURNED 0.5 for the re-wrapped blend,
    which is what refuted boundary 6's claim that the publication boundary carried this.

    The gate is unchanged and is not what refuses this. The blend cannot be built into the
    magnitude the gate requires, so the gate is never reached — which is why boundary 6 now
    names the RE-ENTRY and carries this refusal as its evidence (CD-RULE-006)."""
    blended = (_leak(EQUITY) + _leak(MONETARY)) / 2
    with pytest.raises(QuantityProvenanceMissing):
        number_for_dial_slot(EQUITY_DIAL_ID, DialMagnitude(
            dial_id=EQUITY_DIAL_ID, quantity=blended
        ))


def test_variant_pl_q9_the_flavour_free_launderer_is_refused():
    """`PL-Q9` in its own shape: no dial named in any expression, no arithmetic on any
    magnitude, the slot passed in as a parameter. It defeated the static arm AND the
    runtime arm together at a94ef97. The static arm still exits 0 on it and always will —
    nothing about such a module is recognisable — and the RE-ENTRY refuses it."""

    def as_number(reading):
        return float(repr(reading).split("quantity=")[1].rstrip(")"))

    def aggregate(readings, slot):
        figures = [as_number(r) for r in readings]
        total = 0.0
        for figure in figures:
            total = total + figure
        return DialMagnitude(dial_id=slot, quantity=total / len(figures))

    with pytest.raises(QuantityProvenanceMissing):
        aggregate([EQUITY, MONETARY], EQUITY_DIAL_ID)


def test_laundering_that_never_touches_repr_is_refused_too():
    """The evidence that this is a CLASS closure and not a `repr` fix.

    Two routes that render or reach the payload without `repr` anywhere: an f-string over
    the private slot, and a JSON round trip of the pickle state. Both yield a real float,
    and neither float can re-enter."""
    quantity = object.__getattribute__(EQUITY, "_DialMagnitude__quantity")
    from_fstring = float(f"{quantity}".split("value=")[1].rstrip(")"))
    assert from_fstring == 0.9
    from_json = json.loads(
        json.dumps(EQUITY.__getstate__()["_DialMagnitude__quantity"].__getstate__()[
            "_DeclaredQuantity__value"
        ])
    )
    assert from_json == 0.9
    for laundered in (from_fstring, from_json):
        with pytest.raises(QuantityProvenanceMissing):
            DialMagnitude(dial_id=EQUITY_DIAL_ID, quantity=laundered)


def test_reflection_now_reaches_a_declared_quantity_rather_than_a_float():
    """Boundary C strengthened as a consequence rather than by a rule.

    The private slot holds a `DeclaredQuantity`, so the escape this seat raised against its
    own increment-2 work (`CD-ENG-WO2R-F06`) fails at the `sum` instead of merely being
    visible to a locator."""
    reached = [
        getattr(EQUITY, "_DialMagnitude__quantity"),
        getattr(MONETARY, "_DialMagnitude__quantity"),
    ]
    assert all(type(q) is DeclaredQuantity for q in reached)
    with pytest.raises(TypeError):
        reached[0] + reached[1]
    with pytest.raises(TypeError):
        sum(m.__getstate__()["_DialMagnitude__quantity"] for m in (EQUITY, MONETARY))


def test_a_declared_quantity_of_the_other_dial_is_refused_by_set_equality():
    """No laundering at all: take the OTHER dial's declared quantity and re-wrap it."""
    other = MONETARY.__getstate__()["_DialMagnitude__quantity"]
    with pytest.raises(CrossDialCombination):
        DialMagnitude(dial_id=EQUITY_DIAL_ID, quantity=other)


def test_a_forged_dial_set_on_a_declared_quantity_yields_no_magnitude():
    """`object.__setattr__` rewrites a slot on any frozen object. The direction is SAFE:
    a forged dial set makes the quantity LESS usable, never more."""
    quantity = quantity_of(EQUITY_DIAL_ID, 0.5)
    object.__setattr__(quantity, "dials", frozenset({EQUITY_DIAL_ID, MONETARY_DIAL_ID}))
    with pytest.raises(CrossDialCombination):
        DialMagnitude(dial_id=EQUITY_DIAL_ID, quantity=quantity)
    with pytest.raises(CrossDialCombination):
        quantity.value_for(EQUITY_DIAL_ID)


# --- the admission door: what it refuses, and what it admits ---------------------------- #

def test_the_admission_door_refuses_a_dial_as_its_own_input():
    """A DIAL IS NOT AN INGREDIENT OF A DIAL. This closes the most natural honest-looking
    spelling of the forgery — declaring the two dials as the inputs of a third figure —
    by comparing data rather than by recognising an expression."""
    with pytest.raises(CrossDialCombination):
        observed_for_dial(
            dial_id=EQUITY_DIAL_ID, quantity=0.5,
            inputs_used=(EQUITY_DIAL_ID, MONETARY_DIAL_ID),
        )


def test_the_admission_door_refuses_a_number_admitted_from_nowhere():
    """The same shape `Value` already requires of a reading: a magnitude computed from
    nothing is a number nobody computed (CD-AC-001, CD-ASR-F03)."""
    for bad in ((), [], ("",), (None,), (0,)):
        with pytest.raises(CrossDialCombination):
            observed_for_dial(dial_id=EQUITY_DIAL_ID, quantity=0.5, inputs_used=bad)


@pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan, 1, True, "0.5", None])
def test_the_admission_door_refuses_anything_that_is_not_a_finite_float(bad):
    with pytest.raises(ScoreOutOfRange):
        observed_for_dial(
            dial_id=EQUITY_DIAL_ID, quantity=bad, inputs_used=TEST_SOURCE_IDS
        )


def test_the_admission_door_refuses_a_number_admitted_for_no_dial():
    for bad in ("", None, 0, [EQUITY_DIAL_ID], frozenset({EQUITY_DIAL_ID})):
        with pytest.raises(CrossDialCombination):
            observed_for_dial(
                dial_id=bad, quantity=0.5, inputs_used=TEST_SOURCE_IDS
            )


# --- the declared quantity's own surface, on the pattern already accepted ---------------- #

def test_the_declared_quantity_surface_is_exactly_the_declaration():
    """Set EQUALITY in both directions, against an INDEPENDENT copy of the declaration.

    Widening the module's declaration to admit a new member fails this test rather than
    widening the guard — the lesson of CD-ASR-F02, applied here before it had to be
    learned a third time."""
    assert DECLARED_QUANTITY_MEMBERS == EXPECTED_QUANTITY_SURFACE
    observed = frozenset(vars(DeclaredQuantity))
    assert observed - DECLARED_QUANTITY_MEMBERS - TOLERATED_QUANTITY_MACHINERY == frozenset()
    assert DECLARED_QUANTITY_MEMBERS - observed == frozenset()


@pytest.mark.parametrize("dunder", ARITHMETIC_DUNDERS)
def test_a_declared_quantity_defines_no_arithmetic_or_coercion_dunder(dunder):
    """So no expression in Python produces a third declared quantity from two of them.
    Without this the type would be a laundering vehicle of its own.

    Asserted over the whole MRO rather than over ``vars`` alone, so an inherited coercion
    would fail too — but skipping the four ordering slots and ``__or__``, which every
    Python object and every Python CLASS carries from ``object`` and ``type``. Those are
    covered by the behavioural assertion below instead: the operation itself must raise."""
    inherited_from_the_interpreter = {"__lt__", "__le__", "__gt__", "__ge__", "__or__",
                                      "__ror__"}
    assert dunder not in vars(DeclaredQuantity)
    if dunder not in inherited_from_the_interpreter:
        assert not hasattr(DeclaredQuantity, dunder)


@pytest.mark.parametrize(
    "operation",
    [
        operator.add, operator.sub, operator.mul, operator.truediv, operator.floordiv,
        operator.mod, operator.pow, operator.or_, operator.and_, operator.xor,
        operator.lt, operator.le, operator.gt, operator.ge,
    ],
)
def test_two_declared_quantities_refuse_every_binary_operation(operation):
    """The behavioural half, which is what actually matters: whatever ``object`` and
    ``type`` provide, the OPERATION on two instances raises."""
    left = quantity_of(EQUITY_DIAL_ID, 0.4)
    right = quantity_of(MONETARY_DIAL_ID, 0.6)
    with pytest.raises(TypeError):
        operation(left, right)


def test_a_declared_quantity_refuses_every_numeric_coercion():
    quantity = quantity_of(EQUITY_DIAL_ID, 0.4)
    for coerce in (float, int, complex, round, operator.index, math.trunc, math.floor):
        with pytest.raises(TypeError):
            coerce(quantity)
    with pytest.raises(TypeError):
        math.fsum([quantity, quantity])
    with pytest.raises(TypeError):
        statistics.mean([quantity, quantity])


def test_a_declared_quantity_cannot_be_subclassed():
    with pytest.raises(TypeError):
        class Wider(DeclaredQuantity):
            def __float__(self):
                return 0.0


def test_the_declared_quantity_type_is_sealed_against_member_addition():
    with pytest.raises(TypeError):
        DeclaredQuantity.__add__ = lambda self, other: 0.0
    with pytest.raises(TypeError):
        del DeclaredQuantity.value_for


def test_a_declared_quantity_is_not_equal_to_a_bare_number():
    assert quantity_of(EQUITY_DIAL_ID, 0.5) != 0.5
    assert quantity_of(EQUITY_DIAL_ID, 0.5) == quantity_of(EQUITY_DIAL_ID, 0.5)
    assert quantity_of(EQUITY_DIAL_ID, 0.5) != quantity_of(MONETARY_DIAL_ID, 0.5)


def test_a_revived_declared_quantity_is_validated_exactly_as_a_constructed_one():
    quantity = quantity_of(EQUITY_DIAL_ID, 0.5)
    assert deepcopy(quantity) == quantity
    assert pickle.loads(pickle.dumps(quantity)) == quantity
    revived = DeclaredQuantity.__new__(DeclaredQuantity)
    with pytest.raises(CrossDialCombination):
        revived.__setstate__(
            {"dials": frozenset({EQUITY_DIAL_ID, MONETARY_DIAL_ID}),
             "_DeclaredQuantity__value": 0.5}
        )


# --- FALSE POSITIVES: the product must still work ---------------------------------------- #

def test_a_magnitude_still_publishes_into_its_own_slot_after_the_re_entry_closure():
    """FALSE-POSITIVE CHECK. A closure that forbids the product is not a closure."""
    assert number_for_dial_slot(EQUITY_DIAL_ID, EQUITY) == 0.9
    assert number_for_dial_slot(MONETARY_DIAL_ID, MONETARY) == 0.1


def test_a_derived_same_dial_magnitude_still_publishes():
    """The DERIVATION door end to end: combine within one dial, then publish the result.
    Its dial set AND its number are both computed by the door, so a caller supplies
    neither (CD-ASR-WO2R-F01)."""
    window = [magnitude_of(EQUITY_DIAL_ID, q) for q in (0.1, 0.2, 0.3)]
    mean = combine_within_one_dial(window, using=SameDialReduction.MEAN)
    assert number_for_dial_slot(EQUITY_DIAL_ID, mean) == pytest.approx(0.2)


def test_the_debugger_still_shows_a_developer_the_number():
    """FALSE-POSITIVE CHECK, and the reason the `repr` contradiction was resolved by
    withdrawing the CLAIM rather than by narrowing the exit. `repr` is byte-identical to
    what it was at a94ef97."""
    assert repr(EQUITY) == "DialMagnitude(dial_id='equity_crash', quantity=0.9)"
    assert repr(quantity_of(EQUITY_DIAL_ID, 0.9)) == (
        "DeclaredQuantity(dials=['equity_crash'], value=0.9)"
    )


# --- CD-ASR-WO2R-F01: THE DERIVATION DOOR VALIDATES THE VALUE ----------------------------- #
#
# The auditor's finding was not that a name was missing from a list. It was that a door
# which validated its DIAL SET and never its VALUE could be reached by a public function
# that did not look like a door. These tests execute the routes and watch the door refuse;
# none of them reads source and none of them inspects a checker's exit code.


def test_asr2_002_a_the_derivation_door_no_longer_launders_a_blend():
    """`ASR2-002-A` VERBATIM IN SHAPE, and it is refused by the derivation door.

    The auditor's module released both dials' numbers with `quantity_for`, averaged them
    in an ordinary expression, and handed the average back through
    `combine_within_one_dial(..., using=<a closure>)`. It named no dial, named no door,
    touched no private slot, and published an equity 0.5 out of an equity 0.9 and a
    monetary 0.1.

    The refusal is by EXACT TYPE of what the door was HANDED — a `function` is not a
    `SameDialReduction` — and not by anything about the module, its name, or its imports.
    """
    held = (EQUITY, MONETARY)
    numbers = [reading.quantity_for(sole_dial_of(reading)) for reading in held]
    carried = sum(numbers) / len(numbers)
    assert carried == pytest.approx(0.5)  # the blend still EXISTS; it is a float
    with pytest.raises(UndeclaredReduction):
        combine_within_one_dial([held[0]], using=lambda _released: carried)


def test_the_derivation_door_refuses_every_callable_shape():
    """A lambda, a def, a builtin, a bound method, a callable object, a partial.

    The class is "a number this system did not compute", not "a lambda". Each of these is
    refused for what it IS, so renaming any of them changes nothing."""

    class Callable:
        def __call__(self, _released):
            return 0.5

    def named(_released):
        return 0.5

    for supplied in (
        lambda _released: 0.5,
        named,
        max,
        statistics.mean,
        Callable(),
        functools.partial(named),
        [0.5],
        "MEAN",
        0.5,
        None,
    ):
        with pytest.raises(UndeclaredReduction):
            combine_within_one_dial([EQUITY], using=supplied)


def test_the_derivation_door_refuses_a_value_whose_provenance_it_cannot_establish():
    """It takes established quantities, never numbers. A bare float, a float subclass and
    a look-alike carrying the right-looking `dials` attribute are all refused identically,
    by exact type — the door reads what it was handed, not what it was told."""

    class LooksLikeAQuantity:
        dials = frozenset({EQUITY_DIAL_ID})

        def value_for(self, _dial_id):
            return 0.5

    class NotQuiteAFloat(float):
        pass

    for offered in (0.5, NotQuiteAFloat(0.5), LooksLikeAQuantity(), None, "0.5"):
        with pytest.raises(QuantityProvenanceMissing):
            derived_within_one_dial(
                quantities=(offered,), reduction=SameDialReduction.MEAN
            )


def test_the_derivation_door_computes_the_union_and_refuses_two_dials():
    """The union is computed HERE from the quantities' own provenance, so a caller cannot
    state it, narrow it, or disagree with it."""
    with pytest.raises(CrossDialCombination):
        derived_within_one_dial(
            quantities=(
                quantity_of(EQUITY_DIAL_ID, 0.9),
                quantity_of(MONETARY_DIAL_ID, 0.1),
            ),
            reduction=SameDialReduction.MEAN,
        )


def test_the_derivation_door_refuses_deriving_from_nothing():
    with pytest.raises(CrossDialCombination):
        derived_within_one_dial(quantities=(), reduction=SameDialReduction.MEAN)


def test_a_declared_quantity_cannot_be_constructed_directly():
    """Its two fields are exactly the two things a caller must not be able to assert.

    `DeclaredQuantity(dials=frozenset({...}), value=<a blend>)` was a public, re-exported,
    one-expression forgery of provenance until CD-ASR-WO2R-F01. It now fails closed and
    says what it could not establish."""
    with pytest.raises(QuantityProvenanceMissing):
        DeclaredQuantity(dials=frozenset({EQUITY_DIAL_ID}), value=0.5)
    with pytest.raises(QuantityProvenanceMissing):
        DeclaredQuantity()


def test_the_declared_reductions_are_closed_and_implemented_by_this_system():
    """Set equality in both directions, and the enum is closed by the interpreter.

    A reduction with no implementation would raise at the worst possible moment; an
    implementation with no declaration would be a fifth reduction nobody declared."""
    assert frozenset(SAME_DIAL_REDUCTIONS) == frozenset(SameDialReduction)
    assert frozenset(member.name for member in SameDialReduction) == frozenset(
        {"MEAN", "SUM", "MAX", "MIN"}
    )
    with pytest.raises(TypeError):

        class Extended(SameDialReduction):
            MEDIAN = "median"


def test_no_public_callable_of_the_dial_package_admits_a_caller_supplied_number():
    """THE SWEEP, WITH ITS DENOMINATOR PRINTED.

    The auditor's question was not "is this door guarded?" but "CAN ANY PUBLIC FUNCTION
    REACH A DOOR?". `combine_within_one_dial` was public, re-exported in `__all__`, and
    reached the derivation door on its caller's behalf while being in no registry.

    So this sweeps EVERY public callable re-exported by `crash_detector.dials` and offers
    each of them a poisoned number in every way the call can be spelled, then asserts that
    no `DeclaredQuantity` and no `DialMagnitude` carrying that number came back. The one
    exception is `observed_for_dial`, which is the DECLARED BASE CASE: something has to be
    the first number, it names its dial and its inputs in source, and its residue is
    declared in this package's headers rather than closed here.

    It is not a proof that no such callable can ever be written — a sweep has a
    denominator, not a quantifier — and it is recorded as a sweep. What it does is make
    "a new public function became a door" a DECLARED TEST FAILURE rather than an audit
    finding two gates later.
    """
    import crash_detector.dials as package

    poison = 0.31415926535
    declared_base_case = {"observed_for_dial"}
    swept = 0
    admitted = []
    for name in package.__all__:
        member = getattr(package, name)
        if not callable(member) or name in declared_base_case:
            continue
        swept += 1
        attempts = (
            lambda m=member: m(poison),
            lambda m=member: m(dials=frozenset({EQUITY_DIAL_ID}), value=poison),
            lambda m=member: m(dial_id=EQUITY_DIAL_ID, quantity=poison),
            lambda m=member: m([poison], using=SameDialReduction.MEAN),
            lambda m=member: m(quantities=(poison,), reduction=SameDialReduction.MEAN),
            lambda m=member: m(EQUITY_DIAL_ID, poison),
        )
        for attempt in attempts:
            try:
                produced = attempt()
            except BaseException:
                continue
            if type(produced) is DeclaredQuantity:
                admitted.append((name, "DeclaredQuantity"))
            if type(produced) is DialMagnitude:
                admitted.append((name, "DialMagnitude"))
    assert swept >= 12, f"the sweep found only {swept} public callables to attack"
    assert admitted == [], f"a public callable admitted a caller-supplied number: {admitted}"
