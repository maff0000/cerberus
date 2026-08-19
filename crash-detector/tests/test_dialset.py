"""``DialSet`` is a container, never a combinator (CD-AC-002).

The property under test is an ABSENCE, so it is tested by enumerating the whole public
surface against an allowlist rather than by naming the one method somebody might add.
Adding *any* public member to ``DialSet`` fails these tests until it is declared
deliberately in ``DIAL_FIELDS``.
"""

from __future__ import annotations

import dataclasses
import numbers
import operator

import pytest

from crash_detector.dials.dialset import (
    DIAL_FIELDS,
    DIAL_IDS,
    EQUITY_DIAL_ID,
    MONETARY_DIAL_ID,
    DialSet,
)
from crash_detector.dials.magnitude import DialMagnitude
from crash_detector.dials.reading import Degraded, Unknown, Value
from crash_detector.dials.scores import (
    ARITHMETIC_DUNDERS,
    Contribution,
    EquityCrashScore,
    MonetaryDebasementScore,
)

from conftest import FIXED_NOW
from dial_magnitudes import magnitude_of

CONTRIB = Contribution(source_id="src.a", category="credit", weight=1.0, contribution=0.4)
# MECHANICS ONLY (CD-ASR-F01): a dial magnitude carries its dial as data, so building a
# score now names the dial the number came from. No assertion in this file was relaxed.
EQUITY = EquityCrashScore(
    score=magnitude_of(EQUITY_DIAL_ID, 0.4), contributions=(CONTRIB,)
)
MONETARY = MonetaryDebasementScore(
    score=magnitude_of(MONETARY_DIAL_ID, 0.6),
    contributions=(CONTRIB,),
)


def _unknown(reason="NO_REQUIRED_INPUTS_DECLARED"):
    return Unknown(reason=reason, since_utc=FIXED_NOW, missing_inputs=())


def _populated() -> DialSet:
    return DialSet(
        equity=Value(value=EQUITY, as_of_utc=FIXED_NOW, inputs_used=("src.a",)),
        monetary=Value(value=MONETARY, as_of_utc=FIXED_NOW, inputs_used=("src.a",)),
    )


def test_there_are_exactly_two_dials():
    assert DIAL_IDS == (EQUITY_DIAL_ID, MONETARY_DIAL_ID)
    assert DIAL_FIELDS == ("equity", "monetary")


def test_the_declared_fields_are_the_whole_of_the_type():
    assert tuple(f.name for f in dataclasses.fields(DialSet)) == DIAL_FIELDS


def test_dialset_exposes_no_public_member_beyond_the_two_readings():
    """The allowlist test. A `combined`, `overall`, `mean`, `worst`, `headline`, `blend`
    or anything else public fails here without the guard having to have predicted it."""
    # dir() of an INSTANCE, so that both class members and instance attributes are seen.
    public = {name for name in dir(_populated()) if not name.startswith("_")}
    assert public == set(DIAL_FIELDS), (
        f"unexpected public surface: {public ^ set(DIAL_FIELDS)}"
    )


def test_dialset_defines_no_arithmetic_or_numeric_coercion_dunder():
    for ancestor in DialSet.__mro__:
        if ancestor is object:
            continue
        defined = [name for name in ARITHMETIC_DUNDERS if name in vars(ancestor)]
        assert defined == [], f"{ancestor.__name__} defines {defined}"


def test_dialset_has_no_length_and_is_not_iterable():
    """`len(dials)`, `sum(dials)` and `a, b = dials` are all routes to treating the two
    dials as one aggregate. None of them exists."""
    dials = _populated()
    for coerce in (len, iter, list):
        with pytest.raises(TypeError):
            coerce(dials)


@pytest.mark.parametrize("coerce", [int, float, complex, round])
def test_dialset_cannot_be_coerced_to_a_number(coerce):
    with pytest.raises(TypeError):
        coerce(_populated())


def test_two_dialsets_cannot_be_combined_with_each_other():
    with pytest.raises(TypeError):
        operator.add(_populated(), _populated())


def test_a_dialset_is_not_a_number():
    assert not isinstance(_populated(), numbers.Number)


def test_dialset_is_frozen():
    dials = _populated()
    assert DialSet.__dataclass_params__.frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        dials.equity = _unknown()  # type: ignore[misc]


def test_dialset_fields_have_no_defaults():
    """No default. A DialSet cannot be built half-empty and then filled in."""
    for field in dataclasses.fields(DialSet):
        assert field.default is dataclasses.MISSING
        assert field.default_factory is dataclasses.MISSING
    with pytest.raises(TypeError):
        DialSet()  # type: ignore[call-arg]


# --- the two slots are not interchangeable --------------------------------------------- #

def test_a_slot_refuses_the_other_dials_score_type():
    """Two dials that can be swapped are one dial with two names."""
    with pytest.raises(TypeError):
        DialSet(
            equity=Value(value=MONETARY, as_of_utc=FIXED_NOW, inputs_used=("a",)),
            monetary=Value(value=MONETARY, as_of_utc=FIXED_NOW, inputs_used=("a",)),
        )
    with pytest.raises(TypeError):
        DialSet(
            equity=Value(value=EQUITY, as_of_utc=FIXED_NOW, inputs_used=("a",)),
            monetary=Value(value=EQUITY, as_of_utc=FIXED_NOW, inputs_used=("a",)),
        )


def test_the_cross_type_refusal_also_applies_to_degraded_not_only_value():
    """The variant: smuggle the wrong score type in through the other constructor."""
    with pytest.raises(TypeError):
        DialSet(
            equity=Degraded(
                value=MONETARY, as_of_utc=FIXED_NOW, missing_inputs=("a",), reason="R"
            ),
            monetary=_unknown(),
        )


def test_a_slot_refuses_a_bare_score_that_is_not_wrapped_in_a_reading():
    """A raw score is a number with no absence semantics attached."""
    with pytest.raises(TypeError):
        DialSet(equity=EQUITY, monetary=_unknown())  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [None, 0.0, "UNKNOWN", {"score": 0.0}])
def test_a_slot_refuses_anything_that_is_not_a_reading(bad):
    with pytest.raises(TypeError):
        DialSet(equity=bad, monetary=_unknown())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        DialSet(equity=_unknown(), monetary=bad)  # type: ignore[arg-type]


def test_both_dials_may_be_unknown_and_that_is_a_valid_dialset():
    """The WO-2 shipped state. It must be constructible, because it is the honest one."""
    dials = DialSet(equity=_unknown(), monetary=_unknown())
    assert isinstance(dials.equity, Unknown)
    assert isinstance(dials.monetary, Unknown)
