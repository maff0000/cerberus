"""The two dial score types are unrelated, and cannot be combined (CD-AC-002).

PID §3.1 is CONSTITUTIONAL. These tests are built for the CLASS of violation: they
enumerate every arithmetic, bitwise, ordering and numeric-coercion dunder rather than
checking that ``__add__`` in particular is absent, and they attempt each operator against
the live objects rather than trusting the class dictionary alone.
"""

from __future__ import annotations

import dataclasses
import math
import numbers
import operator

import pytest

from crash_detector.dials.magnitude import CrossDialCombination, DialMagnitude
from crash_detector.dials.scores import (
    ARITHMETIC_DUNDERS,
    EQUITY_DIAL_ID,
    MONETARY_DIAL_ID,
    SCORE_TYPES,
    Contribution,
    EquityCrashScore,
    MonetaryDebasementScore,
    ScoreOutOfRange,
)

from dial_magnitudes import magnitude_of

CONTRIB = Contribution(source_id="src.a", category="credit", weight=1.0, contribution=0.4)

#: Which dial each score type belongs to. Written out rather than derived, so the mapping
#: this file asserts against is not the mapping under test.
DIAL_ID_OF = {
    EquityCrashScore: EQUITY_DIAL_ID,
    MonetaryDebasementScore: MONETARY_DIAL_ID,
}


def magnitude_for(score_type, quantity):
    """A magnitude carrying ``score_type``'s own dial.

    Test MECHANICS, not a relaxed expectation. After CD-ASR-F01 a dial magnitude is a
    per-dial nominal value rather than a bare float, so a test that builds a score has to
    say which dial its number came from; after CD-PL-F54 the NUMBER inside it carries a
    declared provenance too, because a bare float that has left a magnitude may not
    re-enter one. Nothing this file asserts became weaker; the constructions became
    explicit, and ``test_a_bare_number_cannot_be_a_dial_score`` below now has a second
    layer beneath it.
    """
    return magnitude_of(DIAL_ID_OF[score_type], quantity)


EQUITY = EquityCrashScore(
    score=magnitude_for(EquityCrashScore, 0.4), contributions=(CONTRIB,)
)
MONETARY = MonetaryDebasementScore(
    score=magnitude_for(MonetaryDebasementScore, 0.6), contributions=(CONTRIB,)
)

BINARY_OPERATORS = [
    operator.add, operator.sub, operator.mul, operator.truediv, operator.floordiv,
    operator.mod, operator.pow, operator.matmul,
    operator.and_, operator.or_, operator.xor, operator.lshift, operator.rshift,
    divmod,
]
ORDERING_OPERATORS = [operator.lt, operator.le, operator.gt, operator.ge]
UNARY_OPERATORS = [operator.neg, operator.pos, operator.abs, operator.invert]


# --- structurally unrelated ----------------------------------------------------------- #

def test_there_are_exactly_two_score_types():
    assert SCORE_TYPES == (EquityCrashScore, MonetaryDebasementScore)


def test_the_two_score_types_share_no_ancestor_but_object():
    shared = set(EquityCrashScore.__mro__) & set(MonetaryDebasementScore.__mro__)
    assert shared == {object}, f"unexpected shared base: {shared - {object}}"


def test_neither_score_type_subclasses_a_numeric_type():
    for score_type in SCORE_TYPES:
        assert not issubclass(score_type, (int, float, complex))
        assert not issubclass(score_type, numbers.Number)


def test_neither_score_instance_registers_as_a_number():
    for score in (EQUITY, MONETARY):
        assert not isinstance(score, numbers.Number)


def test_both_score_types_are_frozen():
    for score_type in SCORE_TYPES:
        assert score_type.__dataclass_params__.frozen


def test_scores_refuse_mutation():
    with pytest.raises(dataclasses.FrozenInstanceError):
        EQUITY.score = 0.9  # type: ignore[misc]


# --- no arithmetic, and the whole class of it ------------------------------------------ #

def test_neither_score_type_defines_any_arithmetic_or_coercion_dunder():
    for score_type in SCORE_TYPES:
        defined = [name for name in ARITHMETIC_DUNDERS if name in vars(score_type)]
        assert defined == [], f"{score_type.__name__} defines {defined}"


def test_no_ancestor_of_either_score_type_defines_one_either():
    """Checking the class dictionary alone would miss the base-class variant of the
    plant: define ``__add__`` on a mixin and inherit it. ``object`` is excluded because
    its default rich-comparison slots return ``NotImplemented``, which is a refusal."""
    for score_type in SCORE_TYPES:
        for ancestor in score_type.__mro__:
            if ancestor is object:
                continue
            defined = [name for name in ARITHMETIC_DUNDERS if name in vars(ancestor)]
            assert defined == [], f"{ancestor.__name__} defines {defined}"


@pytest.mark.parametrize("op", BINARY_OPERATORS, ids=lambda o: o.__name__)
def test_every_binary_operator_between_the_two_dials_is_a_type_error(op):
    """`(equity + monetary) / 2` and every sibling of it, refused by the interpreter."""
    with pytest.raises(TypeError):
        op(EQUITY, MONETARY)
    with pytest.raises(TypeError):
        op(MONETARY, EQUITY)


@pytest.mark.parametrize("op", BINARY_OPERATORS, ids=lambda o: o.__name__)
def test_no_score_can_be_combined_with_a_bare_number_either(op):
    """Weighting one dial before blending is still blending. Both directions refused."""
    for score in (EQUITY, MONETARY):
        with pytest.raises(TypeError):
            op(score, 2.0)
        with pytest.raises(TypeError):
            op(2.0, score)


@pytest.mark.parametrize("op", ORDERING_OPERATORS, ids=lambda o: o.__name__)
def test_the_two_dials_cannot_even_be_ordered_against_each_other(op):
    """Comparing them presumes a shared scale, which is the premise CD-AC-002 denies."""
    with pytest.raises(TypeError):
        op(EQUITY, MONETARY)


@pytest.mark.parametrize("op", UNARY_OPERATORS, ids=lambda o: o.__name__)
def test_no_unary_arithmetic_on_a_score(op):
    with pytest.raises(TypeError):
        op(EQUITY)


@pytest.mark.parametrize("coerce", [int, float, complex, round])
def test_a_score_cannot_be_coerced_to_a_bare_number(coerce):
    with pytest.raises(TypeError):
        coerce(EQUITY)


def test_a_score_cannot_be_summed_which_is_how_a_blend_usually_arrives():
    with pytest.raises(TypeError):
        sum([EQUITY, MONETARY])


def test_the_two_types_are_never_equal_even_with_identical_contents():
    """Dataclass equality is type-sensitive. Equality across the dials would imply
    substitutability, and two substitutable dials are one dial with two names."""
    equity = EquityCrashScore(
        score=magnitude_for(EquityCrashScore, 0.5), contributions=(CONTRIB,)
    )
    monetary = MonetaryDebasementScore(
        score=magnitude_for(MonetaryDebasementScore, 0.5), contributions=(CONTRIB,)
    )
    assert equity != monetary


# --- magnitude validation: the class of thing, not its meaning ------------------------- #

@pytest.mark.parametrize("bad", [0, 1, "0.5", None, True, False, [], object()])
def test_a_magnitude_that_is_not_a_float_is_refused(bad):
    """`True` in particular: isinstance(True, int) is true, and a boolean magnitude
    silently becoming 1.0 is exactly the coercion this product cannot afford.

    Since CD-ASR-F01 a BARE FLOAT is refused here too, and is covered by
    ``test_a_bare_number_cannot_be_a_dial_score`` below: a number without provenance is
    what a blend IS, so there is no route from ``float`` into a dial reading."""
    for score_type in SCORE_TYPES:
        with pytest.raises(ScoreOutOfRange):
            score_type(score=bad, contributions=())
        with pytest.raises(ScoreOutOfRange):
            DialMagnitude(dial_id=DIAL_ID_OF[score_type], quantity=bad)


@pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
def test_a_non_finite_magnitude_is_refused(bad):
    for score_type in SCORE_TYPES:
        with pytest.raises(ScoreOutOfRange):
            magnitude_for(score_type, bad)


@pytest.mark.parametrize("magnitude", [-5.0, 0.0, 0.5, 1.0, 42.0])
def test_no_range_is_imposed_on_the_magnitude(magnitude):
    """Deliberate. A declared range is a declared scale, and the scale of a dial is what
    the dial MEANS — CD-D-005, owed by the Product Owner (BLUEPRINT §16). An Engineer
    seat inventing [0.0, 1.0] here would be inventing product meaning (PBG-AUTH-005).

    This test exists so that adding a range later is a visible, deliberate change with a
    product decision behind it, rather than a quiet tightening inside a constructor.

    CD-ASR-F01 changed how a magnitude is CARRIED and left this refusal exactly where it
    was: the assertion still spans -5.0 to 42.0 and still admits every finite float.
    """
    for score_type in SCORE_TYPES:
        carried = score_type(
            score=magnitude_for(score_type, magnitude), contributions=()
        ).score
        assert carried.quantity_for(DIAL_ID_OF[score_type]) == magnitude


def test_contributions_are_normalised_to_a_tuple():
    score = EquityCrashScore(
        score=magnitude_for(EquityCrashScore, 0.1), contributions=[CONTRIB]
    )
    assert isinstance(score.contributions, tuple)


# --- the magnitude is per-dial and non-coercible (CD-ASR-F01) --------------------------- #

def test_a_bare_number_cannot_be_a_dial_score():
    """THE DEFECT CD-ASR-F01 REPORTED, refused at its root.

    `.score` used to be a plain float, so the moment a caller held two of them the type
    system had left the conversation. There is now no route from a bare number into a
    dial reading, so a blend computed anywhere cannot be re-wrapped and published as a
    dial's magnitude.
    """
    for score_type in SCORE_TYPES:
        with pytest.raises(ScoreOutOfRange):
            score_type(score=0.5, contributions=())


def test_a_magnitude_of_the_other_dial_is_refused():
    """Two slots that can be swapped are one dial with two names."""
    with pytest.raises(CrossDialCombination):
        EquityCrashScore(
            score=magnitude_for(MonetaryDebasementScore, 0.5), contributions=()
        )
    with pytest.raises(CrossDialCombination):
        MonetaryDebasementScore(
            score=magnitude_for(EquityCrashScore, 0.5), contributions=()
        )


@pytest.mark.parametrize("op", BINARY_OPERATORS, ids=lambda o: o.__name__)
def test_every_binary_operator_between_the_two_magnitudes_is_a_type_error(op):
    """The heart of the CD-ASR-F01 closure, at the level a caller actually reaches.

    Both escaped variants unwrapped the dials to `.score` and combined the results. This
    is that expression, for every binary operator, in both directions.
    """
    with pytest.raises(TypeError):
        op(EQUITY.score, MONETARY.score)
    with pytest.raises(TypeError):
        op(MONETARY.score, EQUITY.score)


@pytest.mark.parametrize("op", ORDERING_OPERATORS, ids=lambda o: o.__name__)
def test_the_two_magnitudes_cannot_be_ordered_against_each_other(op):
    with pytest.raises(TypeError):
        op(EQUITY.score, MONETARY.score)


@pytest.mark.parametrize("coerce", [int, float, complex, round])
def test_a_magnitude_cannot_be_coerced_to_a_bare_number(coerce):
    with pytest.raises(TypeError):
        coerce(EQUITY.score)


def test_neither_magnitude_defines_any_arithmetic_or_coercion_dunder():
    for magnitude in (EQUITY.score, MONETARY.score):
        defined = [
            name for name in ARITHMETIC_DUNDERS if name in vars(type(magnitude))
        ]
        assert defined == [], f"{type(magnitude).__name__} defines {defined}"


def test_no_ancestor_of_the_magnitude_type_defines_one_either():
    for ancestor in type(EQUITY.score).__mro__:
        if ancestor is object:
            continue
        defined = [name for name in ARITHMETIC_DUNDERS if name in vars(ancestor)]
        assert defined == [], f"{ancestor.__name__} defines {defined}"


# --- Contribution --------------------------------------------------------------------- #

def test_a_contribution_requires_a_named_source_and_category():
    with pytest.raises(ValueError):
        Contribution(source_id="", category="c", weight=1.0, contribution=0.1)
    with pytest.raises(ValueError):
        Contribution(source_id="s", category="", weight=1.0, contribution=0.1)


@pytest.mark.parametrize("bad", [1, "1.0", None, True, math.nan, math.inf])
def test_a_contribution_weight_must_be_a_finite_float(bad):
    with pytest.raises(ScoreOutOfRange):
        Contribution(source_id="s", category="c", weight=bad, contribution=0.1)


def test_no_score_type_field_has_a_default():
    for score_type in SCORE_TYPES:
        for field in dataclasses.fields(score_type):
            assert field.default is dataclasses.MISSING, (score_type, field.name)
            assert field.default_factory is dataclasses.MISSING, (score_type, field.name)
