"""``Reading`` — absence has a name and no numeric fallback (CD-AC-001).

These tests attack the CLASS of violation, not one instance of it: they enumerate the
whole attribute surface of ``Unknown`` looking for any route to a number, and they check
``fold`` has no default branch rather than checking one particular caller.

CD-ASR-F02 SHOWED THAT THE PARAGRAPH ABOVE WAS NOT YET TRUE, and the second half of this
file is the correction. The original surface test asserted only that no name from
``ARITHMETIC_DUNDERS`` appeared in ``vars(Unknown)`` — a BLACKLIST, which an auditor
walked past with a plain ``magnitude`` property. The tests under "the attribute surface is
CLOSED" assert **set equality** with a surface declared here, in this file, so that a
member nobody anticipated fails for not being declared rather than passing for not being
listed.

THE DECLARED SURFACE IS WRITTEN OUT TWICE ON PURPOSE. ``reading.py`` declares it because
the runtime seal needs it; this file declares its own copy and asserts the two agree. If it
imported the module's table instead, a plant that added ``magnitude`` to the class AND to
the table would pass, which is a test that verifies self-consistency and nothing else.
"""

from __future__ import annotations

import dataclasses
import inspect
import numbers
import typing

import pytest

from crash_detector.dials.dialset import DialSet
from crash_detector.dials.reading import (
    DECLARED_MEMBER_SURFACE,
    READING_CONSTRUCTORS,
    TOLERATED_INTERPRETER_MACHINERY,
    Degraded,
    Reading,
    ReadingSurfaceViolated,
    SealedReadingType,
    Unknown,
    Value,
    fold,
    is_value,
    member_surface_breaches,
)
from crash_detector.dials.magnitude import DialMagnitude
from crash_detector.dials.scores import (
    ARITHMETIC_DUNDERS,
    EQUITY_DIAL_ID,
    EquityCrashScore,
)

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


# ===================================================================================== #
# THE ATTRIBUTE SURFACE IS CLOSED — CD-ASR-F02 (HIGH), escaped variant E03
#
# The class of violation is ABSENCE YIELDING A NUMBER, by any route. These tests assert
# the surface by EQUALITY with the declaration below, so the question is never "is this
# member numeric?" — which no test can decide in general — but "is this member declared?",
# which is decided by set difference.
# ===================================================================================== #

#: THIS FILE'S OWN COPY of the declared surface. Deliberately not imported from the module
#: under test. Compare with ``crash_detector.dials.reading.DECLARED_MEMBER_SURFACE``.
_DATACLASS_MEMBERS = frozenset({
    "__annotations__", "__dataclass_fields__", "__dataclass_params__", "__delattr__",
    "__doc__", "__eq__", "__hash__", "__init__", "__match_args__", "__module__",
    "__post_init__", "__repr__", "__setattr__", "__slots__",
})
_GENERIC_MEMBERS = frozenset({"__orig_bases__", "__parameters__"})

DECLARED_SURFACE_PER_CONSTRUCTOR = {
    "Value": _DATACLASS_MEMBERS | _GENERIC_MEMBERS
    | frozenset({"value", "as_of_utc", "inputs_used"}),
    "Degraded": _DATACLASS_MEMBERS | _GENERIC_MEMBERS
    | frozenset({"value", "as_of_utc", "missing_inputs", "reason"}),
    "Unknown": _DATACLASS_MEMBERS
    | frozenset({"reason", "since_utc", "missing_inputs"}),
}


def test_the_module_declares_the_same_surface_this_test_declares():
    """Editing the module's declaration to admit a new member must fail HERE.

    Without this the surface assertion would be circular: a plant adding `magnitude` to
    both the class and the module's table would agree with itself.
    """
    assert dict(DECLARED_MEMBER_SURFACE) == DECLARED_SURFACE_PER_CONSTRUCTOR


@pytest.mark.parametrize("constructor", READING_CONSTRUCTORS, ids=lambda c: c.__name__)
def test_the_attribute_surface_is_exactly_the_declared_set(constructor):
    """SET EQUALITY, not the absence of a blacklisted name (CD-ASR-F02).

    Any addition fails: a property, a classvar, a method, a slot, a dunder, numeric or
    not. So does any removal — a guard that only looked for additions could be defeated
    by deleting the member that does the refusing.
    """
    declared = DECLARED_SURFACE_PER_CONSTRUCTOR[constructor.__name__]
    observed = frozenset(vars(constructor))
    unexpected = observed - declared - TOLERATED_INTERPRETER_MACHINERY
    missing = declared - observed
    assert not unexpected, (
        f"{constructor.__name__} carries undeclared member(s) {sorted(unexpected)}; the "
        "surface is closed, so an undeclared member is a failure whether or not it is a "
        "number (CD-ASR-F02 / E03)"
    )
    assert not missing, (
        f"{constructor.__name__} is missing declared member(s) {sorted(missing)}"
    )


def test_dict_is_not_a_tolerated_member_because_it_reopens_injection():
    assert "__dict__" not in TOLERATED_INTERPRETER_MACHINERY


@pytest.mark.parametrize("reading", [_value(), _degraded(), _unknown()])
def test_no_reading_instance_carries_a_dict(reading):
    """Slots, not just frozen. Frozen refuses assignment to a DECLARED field; it says
    nothing about adding an undeclared one to a non-slotted instance."""
    assert not hasattr(reading, "__dict__")
    assert "__slots__" in vars(type(reading))


@pytest.mark.parametrize("reading", [_value(), _degraded(), _unknown()])
def test_an_undeclared_instance_attribute_cannot_be_injected(reading):
    """Both routes: the ordinary one, and the one that walks past ``__setattr__``."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        reading.magnitude = 0.0
    with pytest.raises(AttributeError):
        object.__setattr__(reading, "magnitude", 0.0)
    assert not hasattr(reading, "magnitude")


@pytest.mark.parametrize("constructor", READING_CONSTRUCTORS, ids=lambda c: c.__name__)
def test_no_reading_constructor_may_be_subclassed(constructor):
    """`fold` and `is_value` dispatched on isinstance, so a subclass carrying a numeric
    member would have been accepted everywhere a Reading is accepted."""
    with pytest.raises(ReadingSurfaceViolated):
        type("Sneaky", (constructor,), {"magnitude": 0.0})


@pytest.mark.parametrize("constructor", READING_CONSTRUCTORS, ids=lambda c: c.__name__)
def test_a_sealed_constructor_refuses_class_attribute_assignment(constructor):
    """E03's exact route, one level up: a member added to the class after import."""
    with pytest.raises(ReadingSurfaceViolated):
        setattr(constructor, "magnitude", property(lambda self: 0.0))
    with pytest.raises(ReadingSurfaceViolated):
        delattr(constructor, "__init__")
    assert not hasattr(constructor, "magnitude")


@pytest.mark.parametrize("constructor", READING_CONSTRUCTORS, ids=lambda c: c.__name__)
def test_every_constructor_is_built_by_the_sealing_metaclass(constructor):
    assert isinstance(constructor, SealedReadingType)


def test_the_surface_check_reports_an_undeclared_member_that_is_not_a_number():
    """The equality semantics, exercised without touching the real classes.

    A member that is neither a dunder nor numeric — the class E03 belongs to — must be
    reported. Nothing here asks what the member IS.
    """
    look_alike = type("Unknown", (), {"__slots__": (), "explain": lambda self: "hello"})
    assert member_surface_breaches(look_alike), (
        "an undeclared non-numeric member must be reported; a check that only reported "
        "numeric ones is the blacklist CD-ASR-F02 walked past"
    )


def test_a_constructor_with_no_declared_surface_is_refused_rather_than_tolerated():
    undeclared = type("Provisional", (), {"__slots__": ()})
    breaches = member_surface_breaches(undeclared)
    assert breaches and "declares no member surface" in breaches[0]


# --- the consumer boundary re-verifies, and the residue is declared ------------------- #

def _breach(constructor, name="magnitude"):
    """Install an undeclared member by the ONE route no Python structure can refuse.

    ``type.__setattr__`` walks past the metaclass's ``__setattr__``. This is the residue
    declared in ``reading.py``'s header and in CD-RT-001-ABSENCE-RENDERS-UNKNOWN's entry:
    the mutation itself cannot be prevented, so every consumer boundary re-verifies.
    """
    type.__setattr__(constructor, name, property(lambda self: 0.0))


def _heal(constructor, name="magnitude"):
    type.__delattr__(constructor, name)


def test_the_residue_is_real_and_is_declared_not_denied():
    """Absence CAN be given a numeric member by rewriting the class object at runtime.

    This test exists so the limit is measured rather than asserted. What the closure
    claims is not that this mutation is impossible — it is that a reading of a mutated
    class is refused at every boundary through which it could reach a consumer, which the
    three tests below prove.
    """
    _breach(Unknown)
    try:
        assert _unknown().magnitude == 0.0
    finally:
        _heal(Unknown)
    assert not hasattr(_unknown(), "magnitude")


def test_fold_refuses_a_reading_whose_class_surface_was_breached():
    _breach(Unknown)
    try:
        with pytest.raises(ReadingSurfaceViolated):
            fold(
                _unknown(),
                on_value=lambda r: "VALUE",
                on_degraded=lambda r: "DEGRADED",
                on_unknown=lambda r: "UNKNOWN",
            )
    finally:
        _heal(Unknown)
    assert fold(
        _unknown(),
        on_value=lambda r: "VALUE",
        on_degraded=lambda r: "DEGRADED",
        on_unknown=lambda r: "UNKNOWN",
    ) == "UNKNOWN"


def test_is_value_refuses_a_reading_whose_class_surface_was_breached():
    _breach(Value)
    try:
        with pytest.raises(ReadingSurfaceViolated):
            is_value(_value())
    finally:
        _heal(Value)
    assert is_value(_value()) is True


def test_a_dialset_refuses_a_reading_whose_class_surface_was_breached():
    """The dial set is the other boundary a reading passes through to be published."""
    def build():
        return DialSet(equity=_unknown(), monetary=_unknown())

    _breach(Unknown)
    try:
        with pytest.raises(ReadingSurfaceViolated):
            build()
    finally:
        _heal(Unknown)
    assert isinstance(build(), DialSet)


@pytest.mark.parametrize("function", [fold, is_value], ids=["fold", "is_value"])
def test_the_dispatchers_call_no_isinstance(function):
    """A look-alike that inherits nothing is not a member — and since subclassing is
    refused, exact-type dispatch has no legitimate case it excludes.

    Read as an AST rather than as text, so the word appearing in a docstring that explains
    why it is not used does not fail the test.
    """
    import ast
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "isinstance" not in called, (
        "isinstance dispatch accepts a subclass everywhere a Reading is accepted; the "
        "sum type is closed, so dispatch is on type identity (CD-ASR-F02)"
    )
    assert "type" in called


def test_no_application_module_leaves_a_reading_surface_breached():
    """Import EVERY module in the application package, then re-verify all three surfaces.

    This is the declared arm's answer to the residue above, and it is deliberately an
    assertion about the OUTCOME rather than about the route. It does not look for
    ``type.__setattr__``, or for any other spelling of a class mutation — it imports the
    whole application and then asks whether the surfaces are still exactly as declared. A
    module that breaches one is caught however it did it, including by a route nobody
    listed.

    What remains outside it is a mutation performed by code that is not in this package —
    an operator's script, a plugin, a debugger — which no test over this tree can reach and
    which is declared as such in ``reading.py``'s header.

    Run in a clean subprocess, following the pattern of
    ``test_importing_the_engine_does_not_pull_in_the_witness_package``: importing every
    module into THIS process would change what the rest of the suite sees.
    """
    import pathlib
    import subprocess
    import sys

    src = str(pathlib.Path(__file__).resolve().parent.parent / "src")
    probe = (
        "import pkgutil, importlib, sys\n"
        "import crash_detector\n"
        "from crash_detector.dials.reading import "
        "READING_CONSTRUCTORS, member_surface_breaches\n"
        "failed = []\n"
        "for info in pkgutil.walk_packages(crash_detector.__path__, 'crash_detector.'):\n"
        "    try:\n"
        "        importlib.import_module(info.name)\n"
        "    except Exception as exc:\n"
        "        failed.append(f'{info.name}: {type(exc).__name__}: {exc}')\n"
        "breaches = [b for c in READING_CONSTRUCTORS for b in member_surface_breaches(c)]\n"
        "print('UNIMPORTABLE=' + '; '.join(failed))\n"
        "print('BREACHES=' + ' | '.join(breaches))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", probe],
        capture_output=True,
        text=True,
        timeout=120,
        env={"PYTHONPATH": src, "PATH": "/usr/bin:/bin"},
    )
    assert completed.returncode == 0, completed.stderr
    lines = dict(
        line.split("=", 1) for line in completed.stdout.strip().splitlines()
        if "=" in line
    )
    assert lines.get("UNIMPORTABLE") == "", (
        "a module in the application package could not be imported, so this sweep did not "
        f"cover it: {lines.get('UNIMPORTABLE')}"
    )
    assert lines.get("BREACHES") == "", (
        "importing the application package left a Reading constructor's declared attribute "
        f"surface breached: {lines.get('BREACHES')}"
    )


def test_a_value_still_carries_a_real_score_after_the_surface_closure():
    """FALSE-POSITIVE CHECK. A closure that forbids the product is not a closure."""
    reading = Value(
        value=EquityCrashScore(
            # MECHANICS ONLY (CD-ASR-F01): the magnitude carries its dial as data.
            score=DialMagnitude(dial_id=EQUITY_DIAL_ID, quantity=0.42),
            contributions=(),
        ),
        as_of_utc=ago(30),
        inputs_used=("src.a",),
    )
    assert reading.value.score.quantity_for(EQUITY_DIAL_ID) == 0.42
    assert is_value(reading) is True
    assert fold(
        reading,
        on_value=lambda r: r.value.score.quantity_for(EQUITY_DIAL_ID),
        on_degraded=lambda r: "DEGRADED",
        on_unknown=lambda r: "UNKNOWN",
    ) == 0.42
