"""``Reading`` — absence has a name and no numeric fallback (CD-AC-001).

These tests attack the CLASS of violation, not one instance of it: they enumerate the
whole attribute surface of ``Unknown`` looking for any route to a number, and they check
``fold`` has no default branch rather than checking one particular caller.
"""

from __future__ import annotations

import dataclasses
import inspect
import numbers
import typing

import pytest

from crash_detector.dials.reading import (
    READING_CONSTRUCTORS,
    Degraded,
    Reading,
    Unknown,
    Value,
    fold,
    is_value,
)
from crash_detector.dials.scores import ARITHMETIC_DUNDERS

from conftest import FIXED_NOW, ago


def _value():
    return Value(value="v", as_of_utc=FIXED_NOW, inputs_used=("src.a",))


def _degraded():
    return Degraded(
        value="v", as_of_utc=FIXED_NOW, missing_inputs=("src.b",), reason="MISSING"
    )


def _unknown():
    return Unknown(reason="REQUIRED_INPUTS_UNAVAILABLE", since_utc=FIXED_NOW,
                   missing_inputs=("src.a",))


# --- the sum type is three constructors, related to nothing ------------------------- #

def test_the_sum_type_has_exactly_three_constructors():
    assert READING_CONSTRUCTORS == (Value, Degraded, Unknown)
    members = {typing.get_origin(arg) or arg for arg in typing.get_args(Reading)}
    assert members == {Value, Degraded, Unknown}


def test_the_three_constructors_share_no_ancestor_but_object():
    """A shared base is where a numeric accessor could later be added for all three."""
    bases = [set(c.__mro__) - {object} for c in READING_CONSTRUCTORS]
    common = set.intersection(*bases)
    # Generic is shared by the two generic constructors only, and carries no value.
    assert common == set(), f"unexpected shared ancestor: {common}"


def test_all_three_constructors_are_frozen():
    for constructor in READING_CONSTRUCTORS:
        assert dataclasses.fields(constructor) is not None
        assert constructor.__dataclass_params__.frozen, constructor


@pytest.mark.parametrize("reading", [_value(), _degraded(), _unknown()])
def test_readings_refuse_mutation(reading):
    field_name = dataclasses.fields(reading)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(reading, field_name, "mutated")


# --- Unknown carries no route to a number ------------------------------------------- #

def test_unknown_has_no_value_field():
    names = {f.name for f in dataclasses.fields(Unknown)}
    assert names == {"reason", "since_utc", "missing_inputs"}
    assert not hasattr(_unknown(), "value")


def test_unknown_defines_no_numeric_or_arithmetic_dunder():
    """The class of violation, not the instance: every dunder is checked, not `__add__`."""
    defined = [name for name in ARITHMETIC_DUNDERS if name in vars(Unknown)]
    assert defined == [], f"Unknown must define no numeric route, found {defined}"


def test_unknown_is_not_a_number_and_will_not_coerce():
    unknown = _unknown()
    assert not isinstance(unknown, numbers.Number)
    for coerce in (int, float, complex):
        with pytest.raises(TypeError):
            coerce(unknown)


def test_no_reading_constructor_has_a_default_for_any_field():
    """No default anywhere. A default is where a zero enters without anyone deciding."""
    for constructor in READING_CONSTRUCTORS:
        for field in dataclasses.fields(constructor):
            assert field.default is dataclasses.MISSING, (constructor, field.name)
            assert field.default_factory is dataclasses.MISSING, (constructor, field.name)


# --- the constructors refuse incoherent construction --------------------------------- #

def test_value_refuses_to_be_built_from_no_inputs():
    """A reading computed from nothing is Unknown, not a value."""
    with pytest.raises(ValueError):
        Value(value="v", as_of_utc=FIXED_NOW, inputs_used=())


def test_degraded_refuses_to_be_built_with_nothing_missing():
    with pytest.raises(ValueError):
        Degraded(value="v", as_of_utc=FIXED_NOW, missing_inputs=(), reason="R")


def test_degraded_refuses_an_unstated_reason():
    with pytest.raises(ValueError):
        Degraded(value="v", as_of_utc=FIXED_NOW, missing_inputs=("a",), reason="")


def test_unknown_refuses_an_unstated_reason():
    with pytest.raises(ValueError):
        Unknown(reason="", since_utc=FIXED_NOW, missing_inputs=())


@pytest.mark.parametrize("build", [
    lambda t: Value(value="v", as_of_utc=t, inputs_used=("a",)),
    lambda t: Degraded(value="v", as_of_utc=t, missing_inputs=("a",), reason="R"),
    lambda t: Unknown(reason="R", since_utc=t, missing_inputs=()),
])
def test_every_constructor_refuses_a_naive_timestamp(build):
    from crash_detector.time_utc import NaiveTimestampRejected
    from datetime import datetime

    with pytest.raises(NaiveTimestampRejected):
        build(datetime(2026, 8, 19, 12, 0, 0))


def test_iterable_inputs_are_normalised_to_tuples_so_a_reading_cannot_be_edited_later():
    reading = Value(value="v", as_of_utc=ago(1), inputs_used=["a", "b"])
    assert reading.inputs_used == ("a", "b")
    assert isinstance(reading.inputs_used, tuple)


# --- fold is exhaustive, with no default branch -------------------------------------- #

def test_fold_requires_all_three_branches_as_keyword_arguments():
    signature = inspect.signature(fold)
    branches = ["on_value", "on_degraded", "on_unknown"]
    for name in branches:
        parameter = signature.parameters[name]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is inspect.Parameter.empty, (
            f"{name} has a default; a default branch is how Unknown gets forgotten"
        )


def test_fold_cannot_be_called_without_the_unknown_branch():
    with pytest.raises(TypeError):
        fold(_unknown(), on_value=lambda r: 1, on_degraded=lambda r: 2)  # type: ignore[call-arg]


@pytest.mark.parametrize(
    ("reading", "expected"),
    [(_value(), "VALUE"), (_degraded(), "DEGRADED"), (_unknown(), "UNKNOWN")],
)
def test_fold_dispatches_each_constructor_to_its_own_branch(reading, expected):
    assert fold(
        reading,
        on_value=lambda r: "VALUE",
        on_degraded=lambda r: "DEGRADED",
        on_unknown=lambda r: "UNKNOWN",
    ) == expected


def test_fold_refuses_a_foreign_member_rather_than_defaulting_it():
    """A look-alike is not a member. This is the variant an attacker reaches for."""

    class LooksLikeAValue:
        value = 0.0
        as_of_utc = FIXED_NOW
        inputs_used = ("a",)

    with pytest.raises(TypeError):
        fold(
            LooksLikeAValue(),  # type: ignore[arg-type]
            on_value=lambda r: "VALUE",
            on_degraded=lambda r: "DEGRADED",
            on_unknown=lambda r: "UNKNOWN",
        )


# --- Degraded is not "present" -------------------------------------------------------- #

def test_only_value_counts_as_present():
    assert is_value(_value()) is True
    assert is_value(_degraded()) is False, (
        "Degraded must not be lumped in with Value; that is the first step back "
        "towards rendering damage as calm"
    )
    assert is_value(_unknown()) is False
