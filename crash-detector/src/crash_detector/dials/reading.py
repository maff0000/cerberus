"""``Reading[T]`` — absence has a name, and it is not a number (BLUEPRINT §7, CD-AC-001).

    Reading[T] := Value(T, as_of_utc, inputs_used)
                | Degraded(T, as_of_utc, missing_inputs, reason)
                | Unknown(reason, since_utc, missing_inputs)

Three constructors, **no common ancestor**, **no default value anywhere**. ``Degraded``
still carries a value, but it is a *different constructor*, so a rendering layer must
decide what to do with it and cannot accidentally paint it as a clean reading.

There is deliberately no ``Optional[T]``, no ``float | None`` and no zero default in this
module or anywhere else on the dial path. PID doctrine §3.2 — "missing data must never
render as calm" — is enforced here by making the calm rendering of absence
*inexpressible*, not by asking callers to remember (BLUEPRINT §1).

Why no shared base class: a base class is somewhere a numeric accessor could later be
added that all three constructors would inherit, which is exactly the route from absence
to a number that this type exists to close. Exhaustive handling is provided by
:func:`fold`, which has no default branch, and by ``match`` on the concrete types.

====================================================================================
THE CLOSED ATTRIBUTE SURFACE — added closing CD-ASR-F02 (HIGH)
====================================================================================

The paragraph above was true and was not enough. An independent auditor added a plain
property to ``Unknown`` — ``magnitude -> 0.0``, no dunder, no annotation, no default —
and **absence yielded the number 0.0** while both declared guards for CD-AC-001 stayed
green (`CD-ASR-F02`, escaped variant `E03`). The declared test asserted only that no name
from ``ARITHMETIC_DUNDERS`` appeared in ``vars(Unknown)``. That is a **blacklist**, and a
blacklist cannot see a member nobody thought to list.

This module now closes the **CLASS** — *absence yielding a number* — rather than the two
routes that were reported. The class is closed by making the attribute surface of all
three constructors **declared, verified and sealed**, so the question stops being "is this
member numeric?" (undecidable in general) and becomes "is this member DECLARED?" (decided
by set equality). Four layers, each enforced by the interpreter at a different moment:

1. **DEFINITION TIME.** :data:`DECLARED_MEMBER_SURFACE` states, per constructor, the
   complete set of names its class dictionary may hold. :func:`seal_reading_type` asserts
   **set equality** against it while this module is being imported. A member added in the
   class body — property, classvar, method, slot, dunder, numeric or not — makes
   ``import crash_detector.dials.reading`` raise :exc:`ReadingSurfaceViolated`. There is
   nothing to be quietly invisible to, because nothing is being looked *for*: anything not
   in the declared set is a breach by construction.

2. **INSTANCE TIME.** Each class declares ``__slots__`` and therefore has no instance
   ``__dict__``. ``unknown.magnitude = 0.0`` raises ``FrozenInstanceError``, and
   ``object.__setattr__(unknown, "magnitude", 0.0)`` — which walks *past* the frozen
   dataclass's ``__setattr__`` — raises ``AttributeError``. Frozen alone never closed this:
   frozen refuses assignment to a *declared field* and says nothing about adding an
   undeclared one to a non-slotted instance.

3. **SUBCLASS TIME.** :class:`SealedReadingType` refuses to create any subclass of a sealed
   constructor. This matters more than it looks: :func:`fold` and :func:`is_value` used to
   dispatch on ``isinstance``, so a subclass of ``Unknown`` carrying a numeric member would
   have been accepted *everywhere a Reading is accepted* while passing every check aimed at
   the three declared classes. Both functions now dispatch on **exact type identity**, and
   the subclass they would have to be given cannot be created at all.

4. **CONSUMPTION TIME.** ``type.__setattr__(Unknown, "magnitude", property(...))`` walks
   past the metaclass's ``__setattr__`` — CPython offers no way to stop it — so
   :func:`fold`, :func:`is_value` and ``DialSet`` **re-verify the surface of the reading's
   actual class on every call**. A class mutated after import is refused at every boundary
   through which a reading reaches a consumer, so the number has nowhere to go.

**WHAT REMAINS OPEN, STATED PLAINLY (CD-RULE-004).** Layer 4 is a refusal at the boundary,
not a prohibition on the mutation itself. After
``type.__setattr__(Unknown, "magnitude", property(lambda self: 0.0))`` the expression
``Unknown(reason="R", since_utc=t, missing_inputs=()).magnitude`` **does** evaluate to
``0.0`` for code that reads it directly without passing the reading to any consumer. What
is closed is every route by which such a number reaches a consumer, a fold, a dial set or a
rendering. Do not read this module as claiming that a numeric attribute is unattainable by
a process that rewrites class objects at runtime; read it as claiming that absence cannot
acquire one through construction, assignment, inheritance or definition, and that a mutated
class is refused where it would be used.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Generic, Mapping, TypeVar, Union

from crash_detector.own_terms import NotEstablishedOnOwnTerms, own_str
from crash_detector.time_utc import ensure_utc
from crash_detector.establishment import ESTABLISHED_HERE, each_of, establishes

__all__ = [
    "Value",
    "Degraded",
    "Unknown",
    "Reading",
    "READING_CONSTRUCTORS",
    "DECLARED_MEMBER_SURFACE",
    "TOLERATED_INTERPRETER_MACHINERY",
    "ReadingSurfaceViolated",
    "AbsenceYieldedAValue",
    "SealedReadingType",
    "member_surface_breaches",
    "assert_closed_surface",
    "seal_reading_type",
    "fold",
    "is_value",
]

T = TypeVar("T")
R = TypeVar("R")


def _own_reason(type_name: str, offered: object) -> str:
    """Re-establish a reading's ``reason`` as a plain ``str``, or refuse.

    A module function rather than a member, so it does not widen the declared attribute
    surface these three constructors assert by set equality at import.

    The reason carried no type check at all, so ``not self.reason`` — the refusal that makes
    "we do not know why" impossible to state silently — was decided by whatever ``__bool__``
    or ``__len__`` the supplied object defined (CD-AC-005, Class 2).
    """
    try:
        return own_str(offered)
    except NotEstablishedOnOwnTerms as refusal:
        raise TypeError(f"{type_name}.reason must be a str: {refusal}") from None


class ReadingSurfaceViolated(TypeError):
    """A Reading constructor's attribute surface is not the declared one.

    Raised at import if a member was added or removed in a class body, and raised at a
    consumer boundary if a class was mutated after import. It is a ``TypeError`` because
    what is wrong is the *type*, not the value someone passed.
    """


class AbsenceYieldedAValue(RuntimeError):
    """A code path that did not get its inputs produced a reading that carries a value.

    The vocabulary lives here, with the sum type, rather than in the engine, because the
    proposition belongs to the type: a reading that carries a value is a claim that inputs
    were present, and a claim without its evidence is the CD-AC-001 failure. The engine
    raises it (see :mod:`crash_detector.engine.evaluate`); this module names it.
    """


#: Names CPython's own ``dataclasses``/``type`` machinery may add to a class dictionary
#: depending on interpreter patch level, and which therefore may not be *required* by the
#: declared surface without pinning the interpreter. Each is enumerated with intent: a
#: pickle hook, a weak-reference slot, a copy helper, and 3.13's source-position members.
#: None of them can carry a dial magnitude.
#:
#: ``__dict__`` is deliberately NOT tolerated. A class dictionary that grows a ``__dict__``
#: descriptor has re-opened instance attribute injection, which is layer 2 above, so it is
#: a breach and not machinery.
TOLERATED_INTERPRETER_MACHINERY: frozenset = frozenset(
    {
        "__getstate__",
        "__setstate__",
        "__replace__",
        "__weakref__",
        "__firstlineno__",
        "__static_attributes__",
    }
)

#: Members every frozen dataclass in this module carries, written out rather than computed,
#: because a surface derived from observation would declare whatever it found — including
#: whatever an attacker added.
_DATACLASS_MEMBERS: frozenset = frozenset(
    {
        "__annotations__",
        "__dataclass_fields__",
        "__dataclass_params__",
        "__delattr__",
        "__doc__",
        "__eq__",
        "__hash__",
        "__init__",
        "__match_args__",
        "__module__",
        "__post_init__",
        "__repr__",
        "__setattr__",
        "__slots__",
    }
)

#: Members ``typing.Generic`` adds to a parameterised class.
_GENERIC_MEMBERS: frozenset = frozenset({"__orig_bases__", "__parameters__"})

#: THE COMPLETE DECLARED ATTRIBUTE SURFACE, per constructor, keyed by class name.
#:
#: This is the whole of CD-ASR-F02's closure at layer 1, and it is asserted by EQUALITY —
#: not by the absence of anything. ``tests/test_reading.py`` carries its own independent
#: copy of this table and asserts that the two agree, so editing this declaration to admit
#: a new member fails the declared test rather than widening the guard.
DECLARED_MEMBER_SURFACE: Mapping[str, frozenset] = {
    "Value": _DATACLASS_MEMBERS
    | _GENERIC_MEMBERS
    | frozenset({"value", "as_of_utc", "inputs_used"}),
    "Degraded": _DATACLASS_MEMBERS
    | _GENERIC_MEMBERS
    | frozenset({"value", "as_of_utc", "missing_inputs", "reason"}),
    "Unknown": _DATACLASS_MEMBERS
    | frozenset({"reason", "since_utc", "missing_inputs"}),
}

#: Classes that have passed :func:`seal_reading_type`. Identity, not name: a re-created
#: class wearing the same name is a different object and is not sealed.
_SEALED: set = set()


class SealedReadingType(type):
    """The metaclass that closes the Reading constructors against extension.

    It is a metaclass and not a base class on purpose. A shared *base* would be a place a
    numeric accessor could be added once and inherited by all three constructors, which is
    the hazard this module's original docstring named and refused. A metaclass member is
    reachable on the class object and **not** on an instance, so ``Unknown(...).anything``
    cannot resolve through it: the sum type still has no common ancestor but ``object``.
    """

    def __new__(mcls, name, bases, namespace, **kwargs):
        for base in bases:
            if isinstance(base, SealedReadingType):
                raise ReadingSurfaceViolated(
                    f"{name} may not subclass {base.__name__}: the Reading sum type is "
                    "CLOSED. A subclass carrying a numeric member would be accepted "
                    "everywhere a Reading is accepted, so subclassing is refused rather "
                    "than policed (CD-ASR-F02). A new kind of reading is a change to "
                    "Reading and to fold, reviewed as one."
                )
        return super().__new__(mcls, name, bases, namespace, **kwargs)

    def __setattr__(cls, name: str, value: object) -> None:
        """Refuse class-attribute assignment once the class is sealed.

        Assignment before sealing is permitted because ``dataclasses`` itself assigns
        ``__init__``, ``__repr__`` and the rest onto the class after the class body has
        run. Sealing happens at the bottom of this module, after all decoration.
        """
        if cls in _SEALED:
            raise ReadingSurfaceViolated(
                f"cannot set {cls.__name__}.{name}: this Reading constructor is SEALED. "
                "Its attribute surface is declared in DECLARED_MEMBER_SURFACE and adding "
                "a member — numeric or not — is the CD-ASR-F02 route from absence to a "
                "number."
            )
        type.__setattr__(cls, name, value)

    def __delattr__(cls, name: str) -> None:
        if cls in _SEALED:
            raise ReadingSurfaceViolated(
                f"cannot delete {cls.__name__}.{name}: this Reading constructor is "
                "SEALED. Removing a declared member is as much a change to the surface "
                "as adding one, and the surface is asserted by equality."
            )
        type.__delattr__(cls, name)


@establishes(
    value=ESTABLISHED_HERE(
        "the generic parameter T. Which score types a Reading may carry is product "
        "meaning this seat has no authority to fix (CD-RULE-003); DialSet re-establishes "
        "it one level up, in a body, and DECLARED LIMIT 2 says so"
    ),
    as_of_utc=datetime,
    inputs_used=each_of(str, within=(tuple,)),
)
@dataclass(frozen=True)
class Value(Generic[T], metaclass=SealedReadingType):
    """A reading computed from inputs that were all present and fresh."""

    __slots__ = ("value", "as_of_utc", "inputs_used")

    value: T
    as_of_utc: datetime
    inputs_used: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_utc", ensure_utc(self.as_of_utc))
        object.__setattr__(self, "inputs_used", tuple(self.inputs_used))
        if not self.inputs_used:
            raise ValueError(
                "Value requires at least one named input; a reading computed from "
                "nothing is Unknown, not a value"
            )


@establishes(
    value=ESTABLISHED_HERE(
        "the generic parameter T; the reason given for Value.value applies unchanged"
    ),
    as_of_utc=datetime,
    missing_inputs=each_of(str, within=(tuple,)),
    reason=str,
)
@dataclass(frozen=True)
class Degraded(Generic[T], metaclass=SealedReadingType):
    """A reading computed while named inputs were missing or stale.

    It carries a value AND its damage. A consumer must branch on the constructor, and
    the constructor is not :class:`Value`.
    """

    __slots__ = ("value", "as_of_utc", "missing_inputs", "reason")

    value: T
    as_of_utc: datetime
    missing_inputs: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_utc", ensure_utc(self.as_of_utc))
        object.__setattr__(self, "missing_inputs", tuple(self.missing_inputs))
        if not self.missing_inputs:
            raise ValueError(
                "Degraded requires at least one named missing input; a reading with "
                "nothing missing is a Value, not a degradation"
            )
        object.__setattr__(self, "reason", _own_reason("Degraded", self.reason))
        if not self.reason:
            raise ValueError("Degraded requires a stated reason")


@establishes(
    reason=str,
    since_utc=datetime,
    missing_inputs=each_of(str, within=(tuple,)),
)
@dataclass(frozen=True)
class Unknown(metaclass=SealedReadingType):
    """No honest reading could be produced.

    Carries **no value field of any kind**. There is nothing here to accidentally render
    as a number, because there is no number. It is deliberately not generic: it carries
    no value, so there is no ``T`` for it to be parameterised by, and that asymmetry is
    the point rather than an oversight.

    The promise in the paragraph above is no longer only a promise. ``Unknown``'s whole
    attribute surface is declared in :data:`DECLARED_MEMBER_SURFACE`, asserted by equality
    at import, slotted against instance injection, closed against subclassing and
    re-verified at every consumer boundary. See this module's header for the four layers
    and for the one residue that is declared rather than closed.
    """

    __slots__ = ("reason", "since_utc", "missing_inputs")

    reason: str
    since_utc: datetime
    missing_inputs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "since_utc", ensure_utc(self.since_utc))
        object.__setattr__(self, "missing_inputs", tuple(self.missing_inputs))
        object.__setattr__(self, "reason", _own_reason("Unknown", self.reason))
        if not self.reason:
            raise ValueError("Unknown requires a stated reason")


#: The sum type. Closed.
Reading = Union[Value[T], Degraded[T], Unknown]

#: The complete set of constructors, for guards that must enumerate them.
READING_CONSTRUCTORS: tuple[type, ...] = (Value, Degraded, Unknown)

#: The same set as a frozenset of class objects, for exact-identity dispatch. Membership
#: here is IDENTITY: a look-alike, a re-created class of the same name and (were one
#: constructible) a subclass are all absent from it.
_CONSTRUCTOR_IDENTITIES: frozenset = frozenset(READING_CONSTRUCTORS)


def member_surface_breaches(cls: type) -> tuple[str, ...]:
    """Every way ``cls``'s class dictionary departs from its declared surface.

    Returns an empty tuple when the surface is exactly as declared. The comparison is set
    EQUALITY in both directions — an unexpected member and a missing one are both breaches
    — because a guard that only looked for additions could be defeated by deleting the
    member that does the refusing.
    """
    declared = DECLARED_MEMBER_SURFACE.get(cls.__name__)
    if declared is None:
        return (
            f"{cls.__name__} declares no member surface in DECLARED_MEMBER_SURFACE, so "
            "there is nothing to verify it against. An undeclared Reading constructor is "
            "a defect, not a case to be tolerated.",
        )
    observed = frozenset(vars(cls))
    unexpected = observed - declared - TOLERATED_INTERPRETER_MACHINERY
    missing = declared - observed
    breaches = []
    if unexpected:
        breaches.append(
            f"{cls.__name__} carries undeclared member(s) {sorted(unexpected)}. The "
            "surface is declared and asserted by equality, so this is a breach whether or "
            "not the member is numeric (CD-ASR-F02)."
        )
    if missing:
        breaches.append(
            f"{cls.__name__} is missing declared member(s) {sorted(missing)}. A removed "
            "member changes the surface as much as an added one."
        )
    return tuple(breaches)


def assert_closed_surface(cls: type) -> None:
    """Raise :exc:`ReadingSurfaceViolated` unless ``cls``'s surface is the declared one.

    Called at import by :func:`seal_reading_type`, and again at every consumer boundary,
    because ``type.__setattr__`` can install a member on a class object without going
    through the metaclass and no Python-level structure can prevent that.
    """
    breaches = member_surface_breaches(cls)
    if breaches:
        raise ReadingSurfaceViolated(" ".join(breaches))


def seal_reading_type(cls: type) -> type:
    """Verify ``cls``'s declared surface and its slotting, then seal it.

    Verification is at IMPORT time, so a member added to a class body is a failure to
    import the dial path rather than a member somebody has to notice.
    """
    if not isinstance(cls, SealedReadingType):
        raise ReadingSurfaceViolated(
            f"{cls.__name__} is not built by SealedReadingType, so it is closed against "
            "neither subclassing nor class-attribute assignment."
        )
    if "__slots__" not in vars(cls):
        raise ReadingSurfaceViolated(
            f"{cls.__name__} declares no __slots__. Without slots an instance carries a "
            "__dict__, and `object.__setattr__(reading, 'magnitude', 0.0)` sticks: frozen "
            "refuses assignment to a declared field and says nothing about adding an "
            "undeclared one."
        )
    # Read directly rather than through a defaulted lookup: every type carries
    # ``__dictoffset__``, and a numeric default here would itself be a class-B violation of
    # CD-RT-001-AST-NO-NUMERIC-DEFAULT. The guard reported this seat's first draft, which is
    # the check earning its keep on the module it guards.
    if cls.__dictoffset__:
        raise ReadingSurfaceViolated(
            f"{cls.__name__} instances carry a __dict__ despite __slots__, so instance "
            "attribute injection is open."
        )
    assert_closed_surface(cls)
    _SEALED.add(cls)
    return cls


for _constructor in READING_CONSTRUCTORS:
    seal_reading_type(_constructor)
del _constructor

if set(READING_CONSTRUCTORS) != _SEALED or len(_SEALED) != 3:
    raise ReadingSurfaceViolated(
        "not every Reading constructor was sealed at import. The seal is the whole of "
        "CD-ASR-F02's layer-1 closure, so a constructor that reaches use unsealed is a "
        "failure to import and never a warning."
    )


def fold(
    reading: "Reading[T]",
    *,
    on_value: Callable[["Value[T]"], R],
    on_degraded: Callable[["Degraded[T]"], R],
    on_unknown: Callable[[Unknown], R],
) -> R:
    """Exhaustive handling of a ``Reading``.

    All three branches are **required keyword arguments**. There is no default branch, so
    a caller cannot forget ``Unknown`` and silently fall through to the value branch —
    the failure mode this whole type exists to prevent.

    Dispatch is on **exact type identity**, not ``isinstance``. Subclassing is refused by
    :class:`SealedReadingType`, so this is belt and braces rather than the only stop; but
    an ``isinstance`` dispatch would mean that any subclass which did come into existence
    was accepted here, and this is the boundary through which every reading reaches a
    consumer. The surface of the reading's class is re-verified on the way through for the
    same reason: it is the last place a class mutated after import can be refused.
    """
    kind = type(reading)
    if kind not in _CONSTRUCTOR_IDENTITIES:
        raise TypeError(
            f"not a Reading: {kind.__name__}. The sum type is closed; an "
            "unrecognised member is a defect, not a case to be defaulted."
        )
    assert_closed_surface(kind)
    if kind is Value:
        return on_value(reading)
    if kind is Degraded:
        return on_degraded(reading)
    return on_unknown(reading)


def is_value(reading: "Reading[T]") -> bool:
    """True only for :class:`Value`.

    ``Degraded`` is deliberately not "present": it is a reading that must be rendered
    with its damage attached, and a helper that lumped it in with ``Value`` would be the
    first step back towards rendering damage as calm.

    Exact type identity, and the surface is re-verified for a member of the sum type, for
    the reasons given on :func:`fold`. A non-member is still simply not a value, as
    before — this predicate answers a question and does not police its argument.
    """
    kind = type(reading)
    if kind not in _CONSTRUCTOR_IDENTITIES:
        return False
    assert_closed_surface(kind)
    return kind is Value
