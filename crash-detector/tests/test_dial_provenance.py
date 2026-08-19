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

EQUITY = DialMagnitude(dial_id=EQUITY_DIAL_ID, quantity=0.9)
MONETARY = DialMagnitude(dial_id=MONETARY_DIAL_ID, quantity=0.1)

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
        combine_within_one_dial(
            [EQUITY, MONETARY], using=lambda numbers: sum(numbers) / len(numbers)
        )


def test_a_same_dial_helper_reused_across_dials_fails_when_it_is_reused():
    """The shape that arrives innocently. `mean_of` is legitimate for one dial and is
    refused the moment it is handed both — at runtime, by comparing data, not because
    anybody read the code."""

    def mean_of(magnitudes):
        return combine_within_one_dial(
            magnitudes, using=lambda numbers: sum(numbers) / len(numbers)
        )

    same_dial = mean_of([EQUITY, DialMagnitude(dial_id=EQUITY_DIAL_ID, quantity=0.5)])
    assert same_dial.quantity_for(EQUITY_DIAL_ID) == pytest.approx(0.7)
    with pytest.raises(CrossDialCombination):
        mean_of([EQUITY, MONETARY])


def test_same_dial_computation_still_works():
    """FALSE-POSITIVE CHECK. A closure that forbids the product is not a closure."""
    window = [
        DialMagnitude(dial_id=MONETARY_DIAL_ID, quantity=quantity)
        for quantity in (0.1, 0.2, 0.3, 0.4)
    ]
    rolling_mean = combine_within_one_dial(
        window, using=lambda numbers: sum(numbers) / len(numbers)
    )
    assert rolling_mean.provenance == frozenset({MONETARY_DIAL_ID})
    assert rolling_mean.quantity_for(MONETARY_DIAL_ID) == pytest.approx(0.25)
    widest = combine_within_one_dial(window, using=max)
    assert widest.quantity_for(MONETARY_DIAL_ID) == 0.4


def test_combining_nothing_is_refused():
    with pytest.raises(CrossDialCombination):
        combine_within_one_dial([], using=sum)


def test_a_forged_multi_dial_provenance_yields_no_number():
    """`object.__setattr__` rewrites a slot on any frozen object in Python, and that is
    stated as boundary B of the module's declared limit. The direction is SAFE: a forged
    provenance makes the magnitude LESS usable, never more."""
    forged = DialMagnitude(dial_id=EQUITY_DIAL_ID, quantity=0.5)
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
