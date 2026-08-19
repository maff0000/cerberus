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
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Generic, TypeVar, Union

from crash_detector.time_utc import ensure_utc

__all__ = [
    "Value",
    "Degraded",
    "Unknown",
    "Reading",
    "READING_CONSTRUCTORS",
    "fold",
    "is_value",
]

T = TypeVar("T")
R = TypeVar("R")


@dataclass(frozen=True)
class Value(Generic[T]):
    """A reading computed from inputs that were all present and fresh."""

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


@dataclass(frozen=True)
class Degraded(Generic[T]):
    """A reading computed while named inputs were missing or stale.

    It carries a value AND its damage. A consumer must branch on the constructor, and
    the constructor is not :class:`Value`.
    """

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
        if not self.reason:
            raise ValueError("Degraded requires a stated reason")


@dataclass(frozen=True)
class Unknown:
    """No honest reading could be produced.

    Carries **no value field of any kind**. There is nothing here to accidentally render
    as a number, because there is no number. It is deliberately not generic: it carries
    no value, so there is no ``T`` for it to be parameterised by, and that asymmetry is
    the point rather than an oversight.
    """

    reason: str
    since_utc: datetime
    missing_inputs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "since_utc", ensure_utc(self.since_utc))
        object.__setattr__(self, "missing_inputs", tuple(self.missing_inputs))
        if not self.reason:
            raise ValueError("Unknown requires a stated reason")


#: The sum type. Closed.
Reading = Union[Value[T], Degraded[T], Unknown]

#: The complete set of constructors, for guards that must enumerate them.
READING_CONSTRUCTORS: tuple[type, ...] = (Value, Degraded, Unknown)


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
    """
    if isinstance(reading, Value):
        return on_value(reading)
    if isinstance(reading, Degraded):
        return on_degraded(reading)
    if isinstance(reading, Unknown):
        return on_unknown(reading)
    raise TypeError(
        f"not a Reading: {type(reading).__name__}. The sum type is closed; an "
        "unrecognised member is a defect, not a case to be defaulted."
    )


def is_value(reading: "Reading[T]") -> bool:
    """True only for :class:`Value`.

    ``Degraded`` is deliberately not "present": it is a reading that must be rendered
    with its damage attached, and a helper that lumped it in with ``Value`` would be the
    first step back towards rendering damage as calm.
    """
    return isinstance(reading, Value)
