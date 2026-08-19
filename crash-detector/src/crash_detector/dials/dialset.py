"""``DialSet`` — a container, never a combinator (BLUEPRINT §7, CD-AC-002).

    DialSet := { equity:   Reading[EquityCrashScore],
                 monetary: Reading[MonetaryDebasementScore] }

It holds the two readings side by side and offers **no method that returns a scalar**.
There is deliberately no ``combined``, no ``overall``, no ``mean``, no ``worst``, no
``__float__``, no ``__int__`` and no ``__len__``: nothing on this type through which a
blended headline number could be obtained.

The absence is the design, so the absence is what the test asserts — by enumerating the
type's whole public surface against an allowlist of exactly the two declared fields,
rather than by checking for the one method somebody thought of.
"""

from __future__ import annotations

from dataclasses import dataclass

from crash_detector.dials.reading import (
    READING_CONSTRUCTORS,
    Degraded,
    Reading,
    Value,
)
from crash_detector.dials.scores import EquityCrashScore, MonetaryDebasementScore

__all__ = ["DialSet", "DIAL_IDS", "EQUITY_DIAL_ID", "MONETARY_DIAL_ID", "DIAL_FIELDS"]

EQUITY_DIAL_ID = "equity_crash"
MONETARY_DIAL_ID = "monetary_debasement"

#: The complete set of dials. Two. A third is a PID amendment, not an edit here.
DIAL_IDS: tuple[str, ...] = (EQUITY_DIAL_ID, MONETARY_DIAL_ID)

#: The complete public surface of :class:`DialSet`. The guard for "no scalar method"
#: compares against this, so adding ANY public member — not just an arithmetic one —
#: fails until it is declared here deliberately.
DIAL_FIELDS: tuple[str, ...] = ("equity", "monetary")


@dataclass(frozen=True)
class DialSet:
    """The two dial readings of one evaluation cycle, held apart."""

    equity: "Reading[EquityCrashScore]"
    monetary: "Reading[MonetaryDebasementScore]"

    def __post_init__(self) -> None:
        for field_name in DIAL_FIELDS:
            reading = getattr(self, field_name)
            if not isinstance(reading, READING_CONSTRUCTORS):
                raise TypeError(
                    f"DialSet.{field_name} must be a Reading "
                    f"(Value | Degraded | Unknown), got {type(reading).__name__}"
                )
        _reject_cross_typed(self.equity, EquityCrashScore, "equity")
        _reject_cross_typed(self.monetary, MonetaryDebasementScore, "monetary")


def _reject_cross_typed(reading: object, expected: type, field_name: str) -> None:
    """Refuse a reading whose payload is the *other* dial's score type.

    Without this the two slots would be structurally interchangeable, and two dials that
    can be swapped are one dial with two names.
    """
    if isinstance(reading, (Value, Degraded)):
        if not isinstance(reading.value, expected):
            raise TypeError(
                f"DialSet.{field_name} must carry {expected.__name__}, got "
                f"{type(reading.value).__name__}"
            )
