"""Absence is ANSWERED, and a number chosen for an absence is unpresentable (CD-AC-001).

Closing CD-ASR-WO2R-F03 (MEDIUM), CD-AC-001's AMBER, which rides with CLASS 1 by CD-D-073.

The criterion's words are about RENDERING — "missing or stale input never renders as calm"
— and "unpresentable" is a RUNTIME property. So these tests do not read source and do not
inspect a checker's exit code. They EXECUTE the routes and watch the constructor refuse.

`ASR2-001-A` is reproduced here in the auditor's own shape
(``test_asr2_001_a_*``) so that a regression fails a DECLARED register test rather than
only a variant patch somebody has to remember to re-run.

WHAT IS DELIBERATELY NOT ASSERTED HERE, so that the boundary is visible rather than
discovered: that a module cannot compute its own number from an ``Unknown`` and hand it to
its own caller. It can — `ASR2-001-A`'s ``surface_scalar`` still returns ``0.0`` if anybody
writes it, and ``test_asr2_001_a_still_computes_its_number_and_that_is_declared`` asserts
exactly that rather than hiding it. What is asserted is that the number cannot be PRESENTED
as a dial. That residue, and its carrier, are declared in
``src/crash_detector/serving/dial_presentation.py`` (boundary A), in the header of
``tools/register/check_no_numeric_default.py``, in the register entry and in the execution
contract, in the same words.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from crash_detector.dials.reading import Degraded, Unknown, Value, fold
from crash_detector.dials.scores import (
    EQUITY_DIAL_ID,
    MONETARY_DIAL_ID,
    EquityCrashScore,
    MonetaryDebasementScore,
)
from crash_detector.serving.dial_presentation import (
    DECLARED_PRESENTATION_SURFACE,
    PRESENTATION_CONSTRUCTORS,
    TOLERATED_INTERPRETER_MACHINERY,
    DialPresentationRefused,
    NotShown,
    Shown,
    is_shown,
    present_dial,
)

from dial_magnitudes import magnitude_of

WHEN = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)

#: An INDEPENDENT copy of the declared surface, as ``tests/test_reading.py`` keeps one for
#: the Reading constructors and for the same reason: editing the declaration in the module
#: to admit a new member must fail the declared test rather than widen the guard.
EXPECTED_SURFACE = {
    "Shown": frozenset(
        {
            "__annotations__", "__dataclass_fields__", "__dataclass_params__",
            "__delattr__", "__doc__", "__eq__", "__hash__", "__init__",
            "__match_args__", "__module__", "__post_init__", "__repr__",
            "__setattr__", "__slots__", "dial_id", "magnitude",
        }
    ),
    "NotShown": frozenset(
        {
            "__annotations__", "__dataclass_fields__", "__dataclass_params__",
            "__delattr__", "__doc__", "__eq__", "__hash__", "__init__",
            "__match_args__", "__module__", "__post_init__", "__repr__",
            "__setattr__", "__slots__", "dial_id", "reason", "missing_inputs",
        }
    ),
}


def _unknown(missing=("vix", "move")):
    return Unknown(
        reason="REQUIRED_INPUT_MISSING", since_utc=WHEN, missing_inputs=missing
    )


def _value(dial_id=EQUITY_DIAL_ID, quantity=0.9):
    score_type = EquityCrashScore if dial_id == EQUITY_DIAL_ID else MonetaryDebasementScore
    return Value(
        value=score_type(score=magnitude_of(dial_id, quantity), contributions=()),
        as_of_utc=WHEN,
        inputs_used=("src.a",),
    )


def _degraded(dial_id=EQUITY_DIAL_ID, quantity=0.9):
    score_type = EquityCrashScore if dial_id == EQUITY_DIAL_ID else MonetaryDebasementScore
    return Degraded(
        value=score_type(score=magnitude_of(dial_id, quantity), contributions=()),
        as_of_utc=WHEN,
        missing_inputs=("src.b",),
        reason="CONTRIBUTING_INPUTS_UNAVAILABLE",
    )


# --- ABSENCE IS ANSWERED ------------------------------------------------------------------ #

def test_an_unknown_reading_is_answered_and_the_answer_carries_no_number():
    """The whole of the CD-ASR-WO2R-F03 closure in one assertion pair: the answer exists,
    and there is no field in it for a number to hide in."""
    answered = present_dial(EQUITY_DIAL_ID, _unknown())
    assert type(answered) is NotShown
    assert answered.reason == "REQUIRED_INPUT_MISSING"
    assert answered.missing_inputs == ("vix", "move")
    assert not is_shown(answered)
    for member in vars(NotShown):
        assert not isinstance(getattr(NotShown, member, None), (int, float)), member


def test_a_number_chosen_for_an_absence_cannot_be_presented_as_a_dial():
    """`ASR2-001-A`'s 0.0, and every other number a consumer might choose, offered directly
    to the type that renders a dial. The refusal is by EXACT TYPE of what it was handed."""
    for chosen in (0.0, 0, -1.0, 0.5, float("nan"), "0.0", None, [0.0], object()):
        with pytest.raises(DialPresentationRefused):
            Shown(dial_id=EQUITY_DIAL_ID, magnitude=chosen)


def test_asr2_001_a_the_auditors_own_shape_cannot_reach_the_surface():
    """`ASR2-001-A` VERBATIM IN SHAPE. `fold` still lets the caller answer Unknown with a
    number — deliberately, and it is untouched — and the number still has nowhere to go."""
    reading = _unknown()
    surface_scalar = fold(
        reading,
        on_value=lambda seen: seen.value,
        on_degraded=lambda seen: seen.value,
        on_unknown=lambda seen: 0.0,
    )
    assert surface_scalar == 0.0  # the number EXISTS. It is a float.
    with pytest.raises(DialPresentationRefused):
        Shown(dial_id=EQUITY_DIAL_ID, magnitude=surface_scalar)


def test_asr2_001_a_still_computes_its_number_and_that_is_declared():
    """THE DECLARED LIMIT, ASSERTED RATHER THAN HIDDEN (CD-RULE-004, boundary A).

    Nothing stops a module computing a number for an absence and handing it to its own
    caller, and this test fails the day somebody quietly claims otherwise."""
    assert (
        fold(
            _unknown(),
            on_value=lambda seen: seen.value,
            on_degraded=lambda seen: seen.value,
            on_unknown=lambda seen: 0.0,
        )
        == 0.0
    )


def test_fold_was_not_given_a_guard_and_a_numeric_unknown_branch_still_works():
    """DELIBERATE. A numeric answer ABOUT an absence is legitimate — a count of missing
    inputs is a number and is not a dial reading — so `fold` is left exactly as it is and
    the closure is at the type that presents a dial."""
    assert (
        fold(
            _unknown(missing=("a", "b", "c")),
            on_value=lambda seen: 0,
            on_degraded=lambda seen: 0,
            on_unknown=lambda seen: len(seen.missing_inputs),
        )
        == 3
    )


# --- the surface is DECLARED, not merely free of the members somebody listed ------------- #

def test_the_declared_surface_matches_this_files_independent_copy():
    assert DECLARED_PRESENTATION_SURFACE == EXPECTED_SURFACE


def test_the_live_class_surfaces_are_exactly_the_declared_ones():
    for constructor in PRESENTATION_CONSTRUCTORS:
        observed = frozenset(vars(constructor))
        assert (
            observed - TOLERATED_INTERPRETER_MACHINERY
            == DECLARED_PRESENTATION_SURFACE[constructor.__name__]
        )


@pytest.mark.parametrize("constructor", PRESENTATION_CONSTRUCTORS, ids=lambda c: c.__name__)
def test_a_presentation_constructor_cannot_be_subclassed(constructor):
    with pytest.raises(DialPresentationRefused):
        type("Sneaky", (constructor,), {"magnitude": property(lambda self: 0.0)})


@pytest.mark.parametrize("constructor", PRESENTATION_CONSTRUCTORS, ids=lambda c: c.__name__)
def test_a_member_cannot_be_installed_on_a_sealed_presentation(constructor):
    with pytest.raises(DialPresentationRefused):
        constructor.magnitude_for_the_surface = property(lambda self: 0.0)


@pytest.mark.parametrize("constructor", PRESENTATION_CONSTRUCTORS, ids=lambda c: c.__name__)
def test_a_presentation_instance_carries_no_dict(constructor):
    assert constructor.__dictoffset__ == 0


def test_an_undeclared_attribute_cannot_be_injected_into_an_absence():
    answered = present_dial(EQUITY_DIAL_ID, _unknown())
    with pytest.raises(AttributeError):
        object.__setattr__(answered, "magnitude", 0.0)


def test_a_class_mutated_after_import_is_refused_at_the_consumer_boundary():
    """`type.__setattr__` walks past the metaclass and CPython offers no way to stop it, so
    the surface is re-verified where a presentation would be used (boundary B)."""
    type.__setattr__(NotShown, "magnitude", property(lambda self: 0.0))
    try:
        assert NotShown(dial_id=EQUITY_DIAL_ID, reason="R", missing_inputs=()).magnitude == 0.0
        with pytest.raises(DialPresentationRefused):
            present_dial(EQUITY_DIAL_ID, _unknown())
        with pytest.raises(DialPresentationRefused):
            is_shown(NotShown(dial_id=EQUITY_DIAL_ID, reason="R", missing_inputs=()))
    finally:
        type.__delattr__(NotShown, "magnitude")
    assert type(present_dial(EQUITY_DIAL_ID, _unknown())) is NotShown


# --- the elimination is performed here, not supplied by the caller ------------------------ #

def test_present_dial_takes_no_branch_from_its_caller():
    """There is no `on_unknown` for a caller to write. Checked on the signature, because a
    parameter that does not exist is the closure — not a value that is refused."""
    import inspect

    parameters = set(inspect.signature(present_dial).parameters)
    assert parameters == {"dial_id", "reading"}


def test_a_look_alike_score_is_refused_by_exact_type():
    """The CLASS 2 doctrine applied here before an auditor has to apply it for us: a value
    is admitted for what it IS, never for what it can do."""

    class LooksLikeAScore:
        score = magnitude_of(EQUITY_DIAL_ID, 0.9)
        contributions = ()

    reading = Value(value=LooksLikeAScore(), as_of_utc=WHEN, inputs_used=("src.a",))
    with pytest.raises(DialPresentationRefused):
        present_dial(EQUITY_DIAL_ID, reading)


def test_presenting_a_magnitude_under_the_other_dials_name_is_refused():
    with pytest.raises(DialPresentationRefused):
        Shown(dial_id=MONETARY_DIAL_ID, magnitude=magnitude_of(EQUITY_DIAL_ID, 0.9))


def test_a_forged_multi_dial_provenance_cannot_be_presented():
    forged = magnitude_of(EQUITY_DIAL_ID, 0.5)
    object.__setattr__(
        forged, "provenance", frozenset({EQUITY_DIAL_ID, MONETARY_DIAL_ID})
    )
    with pytest.raises(DialPresentationRefused):
        Shown(dial_id=EQUITY_DIAL_ID, magnitude=forged)


def test_a_presentation_requires_a_named_dial_and_a_stated_reason():
    with pytest.raises(DialPresentationRefused):
        Shown(dial_id="", magnitude=magnitude_of(EQUITY_DIAL_ID, 0.9))
    with pytest.raises(DialPresentationRefused):
        NotShown(dial_id=EQUITY_DIAL_ID, reason="", missing_inputs=())
    with pytest.raises(DialPresentationRefused):
        present_dial("", _unknown())


# --- FALSE POSITIVES: the product must still work ----------------------------------------- #

def test_a_dial_with_a_reading_is_still_shown():
    """FALSE-POSITIVE CHECK. A closure that forbids the product is not a closure."""
    presented = present_dial(EQUITY_DIAL_ID, _value())
    assert type(presented) is Shown
    assert is_shown(presented)
    assert presented.magnitude.quantity_for(EQUITY_DIAL_ID) == 0.9


def test_a_degraded_reading_is_shown_with_its_damage_and_is_not_suppressed():
    """Degraded HAS a value. Rendering it as absent would be the opposite error and just as
    wrong: it would render damage as absence."""
    presented = present_dial(MONETARY_DIAL_ID, _degraded(MONETARY_DIAL_ID, 0.4))
    assert type(presented) is Shown
    assert presented.magnitude.quantity_for(MONETARY_DIAL_ID) == 0.4


def test_both_dials_present_side_by_side_without_ever_meeting_in_an_expression():
    """BLUEPRINT §13: composition happens at the serving layer. Holding the two dials side
    by side never requires arithmetic between them, and none happens here."""
    presented = {
        EQUITY_DIAL_ID: present_dial(EQUITY_DIAL_ID, _value(EQUITY_DIAL_ID, 0.9)),
        MONETARY_DIAL_ID: present_dial(MONETARY_DIAL_ID, _unknown()),
    }
    assert is_shown(presented[EQUITY_DIAL_ID])
    assert not is_shown(presented[MONETARY_DIAL_ID])
    assert presented[MONETARY_DIAL_ID].reason == "REQUIRED_INPUT_MISSING"


def test_a_presentation_is_not_a_reading_and_carries_no_arithmetic():
    """It must not become the next laundering vehicle. It defines no arithmetic dunder and
    no coercion, so two presentations cannot be combined into a third figure."""
    from crash_detector.dials.scores import ARITHMETIC_DUNDERS

    for constructor in PRESENTATION_CONSTRUCTORS:
        defined = [name for name in ARITHMETIC_DUNDERS if name in vars(constructor)]
        assert defined == [], f"{constructor.__name__} defines {defined}"
    left = present_dial(EQUITY_DIAL_ID, _value(EQUITY_DIAL_ID, 0.9))
    right = present_dial(MONETARY_DIAL_ID, _value(MONETARY_DIAL_ID, 0.1))
    with pytest.raises(TypeError):
        left + right
    with pytest.raises(TypeError):
        float(left)
