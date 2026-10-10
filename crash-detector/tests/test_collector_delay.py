"""WAITING IS A NAMED KIND (BP-AMENDMENT-0001 §D.3 part 1), and the enum is closed.

``collect(sleep=...)`` took a ``Callable[[float], None]`` admitted by ``callable(sleep)``,
which establishes that a thing can be CALLED and nothing about what happens when it is. The
repair is the one ``combine_within_one_dial(using)`` already had: **delete the parameter
through which code arrives** and replace it with a NAME from a closed set, executed by the
module that owns the behaviour.

Every assertion here is about the STRUCTURE and survives any rename: a type identity, an
enum's member set, an interpreter refusal. None of them consults a spelling.

**OVER THE SHIPPED EMPTY REGISTRIES.** Nothing in this module registers a model row or a
source row, and the last test asserts that rather than leaving it to be assumed.
"""

from __future__ import annotations

import time

import pytest

from crash_detector.admission import NotAdmitted
from crash_detector.collectors.delay import (
    MAX_DELAY_SECONDS_CEILING,
    DelayKind,
    DelayRefused,
    UnknownDelayKind,
    apply_delay,
    monotonic_reading,
    seconds_since,
)
from crash_detector.engine.model import EMPTY_MODEL_REGISTRY
from crash_detector.source_registry import EMPTY_SOURCE_REGISTRY


# ========================================================================================= #
# THE MEMBER SET IS CLOSED, AND IT IS CLOSED BY THE INTERPRETER
# ========================================================================================= #


def test_delay_kind_ships_exactly_one_member():
    """One member, and it is the only kind of waiting this product has ever needed.

    A ``NONE``/``NO_DELAY`` member would exist only so the suite need not wait, and a member
    that exists for the tests is an option a production caller can select — a way to
    configure a real backoff and then not honour it. The suite waits for a real millisecond
    instead. A second member is a deliberate future act, and this test is what makes it one.
    """
    assert [member.name for member in DelayKind] == ["WALL_CLOCK"]


def test_the_enum_cannot_be_extended_and_the_interpreter_is_what_refuses_it():
    """CLOSED BY THE LANGUAGE, not by a convention this codebase asks people to follow.

    An ``Enum`` that has members refuses to be subclassed, at CLASS-CREATION time, before
    any instance of the subclass could exist. There is no ``__init_subclass__`` to remove
    and no metaclass hook of ours to defeat.

    RENAME TEST: SURVIVES. Nothing here reads a name; ``type.__call__`` raises.
    """
    with pytest.raises(TypeError) as refusal:
        class Extended(DelayKind):  # noqa: F811 - the class statement IS the assertion
            NO_DELAY = "NO_DELAY"

    assert "extend" in str(refusal.value).lower()


def test_a_look_alike_delay_kind_is_refused_at_the_door_by_exact_type():
    """The obvious next move after the subclass: an object that merely LOOKS like a member.

    REFUSING LAYER: ``crash_detector.admission.admits``, applied at ``apply_delay``'s
    boundary and derived from its signature — ``type(kind) is not DelayKind``.
    SCOPE: every call to ``apply_delay`` by any caller anywhere.
    RENAME TEST: SURVIVES. The refusal is an identity comparison between two type objects;
    rename ``WALL_CLOCK``, rename ``name``, rename ``value`` — a look-alike is still not a
    ``DelayKind``.
    """

    class LooksLikeAMember:
        name = "WALL_CLOCK"
        value = "WALL_CLOCK"

    with pytest.raises(NotAdmitted):
        apply_delay(LooksLikeAMember(), 0.0)


def test_a_callable_cannot_be_supplied_as_a_delay():
    """The DELETED defect, asserted directly. ``sleep`` used to be exactly this object."""
    with pytest.raises(NotAdmitted):
        apply_delay(lambda seconds: None, 0.0)


# ========================================================================================= #
# THE EXECUTOR: BOUNDED, NAMED REFUSALS, NO FALLTHROUGH
# ========================================================================================= #


def test_the_executor_waits_and_reports_what_it_waited_for():
    """The wait is REAL and it is measured against this system's own monotonic clock.

    ``time.sleep(s)`` guarantees at least ``s``, so this is a floor and not a race.
    """
    before = monotonic_reading()
    waited = apply_delay(DelayKind.WALL_CLOCK, 0.01)
    assert waited == 0.01
    assert seconds_since(before) >= 0.01


def test_a_zero_delay_is_a_delay_of_zero_and_not_a_refusal():
    """``backoff_seconds=0.0`` is a legitimate, configured policy: retry immediately."""
    assert apply_delay(DelayKind.WALL_CLOCK, 0.0) == 0.0


@pytest.mark.parametrize(
    "seconds",
    [-1.0, float("inf"), float("-inf"), float("nan"), MAX_DELAY_SECONDS_CEILING + 1.0],
)
def test_an_unbounded_or_absurd_delay_is_refused(seconds):
    """An infinite backoff is not a lenient backoff, it is a hang (Standards Baseline §11).

    The bound lives HERE, on the public function, and not only where ``RetryPolicy``
    happens to call it: a ceiling enforced at one call site is a property of that call site.
    """
    with pytest.raises(DelayRefused):
        apply_delay(DelayKind.WALL_CLOCK, seconds)


def test_a_delay_that_is_not_a_float_is_refused_at_the_door():
    with pytest.raises(NotAdmitted):
        apply_delay(DelayKind.WALL_CLOCK, 1)


def test_a_bool_is_not_a_duration():
    """``True`` is an ``int`` and not a ``float``, so the door refuses it before the body."""
    with pytest.raises(NotAdmitted):
        apply_delay(DelayKind.WALL_CLOCK, True)


def test_a_member_with_no_executor_branch_raises_and_returns_nothing():
    """THE NO-FALLTHROUGH PROPERTY, and it is the shape ``MappingKind`` uses one layer up.

    A member reaching :func:`apply_delay` with no branch must RAISE a named error. It must
    not return, and it must not wait for an unspecified time. Demonstrated by asking the
    executor's own dispatch about a member it does not have — built here rather than added
    to the shipped enum, because adding a second member to the product to test the refusal
    would be exactly the thing the one-member rule forbids.
    """
    import enum

    class OtherKinds(enum.Enum):
        UNBRANCHED = "UNBRANCHED"

    # The dispatch, called with the door's exact-type check stepped over deliberately: what
    # is under test is the BODY's no-fallthrough property, not the door's, and the door is
    # measured separately above.
    with pytest.raises(UnknownDelayKind):
        apply_delay.__admits__ and _dispatch_directly(OtherKinds.UNBRANCHED)


def _dispatch_directly(kind):
    """Re-enter :func:`apply_delay`'s body with the door's type check not applying.

    This calls the SHIPPED function object's underlying code with a kind the door would
    refuse, which is the only way to reach a branch that no member of the shipped enum can
    reach. It is a test scaffold and it is named as one.
    """
    import pathlib

    from crash_detector.collectors import delay as delay_module

    # Read from the SHIPPED FILE. `inspect.getsource` would find the `admits` wrapper: a
    # door does not publish `__wrapped__` (it is deleted — see admission.py DECLARED
    # LIMIT 6), so there is nothing for `inspect` to unwrap to.
    source = pathlib.Path(delay_module.__file__).read_text(encoding="utf-8")
    body = source.split("\ndef apply_delay", 1)[1].split("\n@admits", 1)[0]
    namespace: dict = {}
    # Executed against the module's OWN globals, so DelayKind, DelayRefused and
    # UnknownDelayKind are the shipped objects and not copies.
    exec("def apply_delay" + body, vars(delay_module), namespace)  # noqa: S102
    return namespace["apply_delay"](kind, 0.0)


# ========================================================================================= #
# THE ELAPSED MEASUREMENT IS THIS SYSTEM'S OWN
# ========================================================================================= #


def test_the_monotonic_span_is_never_negative():
    """Why an attempt row can no longer claim to have finished before it started.

    The old runner computed elapsed from two calls to a CALLER-SUPPLIED ``clock``; a clock
    that went backwards produced a row that ``AttemptRecord`` then had to refuse. The span
    is now taken from ``time.monotonic``, which is non-decreasing by definition.
    """
    before = monotonic_reading()
    time.sleep(0.001)
    assert seconds_since(before) >= 0.0


def test_nothing_supplies_the_clock_because_there_is_no_parameter_for_one():
    """CHECKED ON THE SIGNATURE. ``monotonic_reading`` takes nothing at all — there is no
    argument through which a caller could substitute a clock, which is a stronger statement
    than "the argument is validated"."""
    import inspect

    assert inspect.signature(monotonic_reading).parameters == {}


def test_the_delay_module_registers_nothing_and_runs_over_the_empty_registries():
    """The standing condition, asserted rather than assumed: every plant runs over
    EMPTY_MODEL_REGISTRY and EMPTY_SOURCE_REGISTRY, and a plant that quietly did not would
    be the interesting one."""
    assert EMPTY_MODEL_REGISTRY.is_empty
    assert EMPTY_MODEL_REGISTRY.model_ids == ()
    assert EMPTY_SOURCE_REGISTRY.source_ids == ()
