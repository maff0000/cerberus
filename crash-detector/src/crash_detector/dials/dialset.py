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
    assert_closed_surface,
)
from crash_detector.dials.scores import (
    EQUITY_DIAL_ID,
    MONETARY_DIAL_ID,
    EquityCrashScore,
    MonetaryDebasementScore,
)
from crash_detector.establishment import establishes, one_of

__all__ = ["DialSet", "DIAL_IDS", "EQUITY_DIAL_ID", "MONETARY_DIAL_ID", "DIAL_FIELDS"]

# The two dial ids are DEFINED in `crash_detector.dials.scores`, beside the types whose
# magnitudes carry them as provenance (CD-ASR-F01), and re-exported here so that every
# existing import site — `from crash_detector.dials.dialset import EQUITY_DIAL_ID` — is
# unchanged. A dial id moved house; it did not change meaning.

#: The complete set of dials. Two. A third is a PID amendment, not an edit here.
DIAL_IDS: tuple[str, ...] = (EQUITY_DIAL_ID, MONETARY_DIAL_ID)

#: The complete public surface of :class:`DialSet`. The guard for "no scalar method"
#: compares against this, so adding ANY public member — not just an arithmetic one —
#: fails until it is declared here deliberately.
DIAL_FIELDS: tuple[str, ...] = ("equity", "monetary")


@establishes(
    equity=one_of(*READING_CONSTRUCTORS),
    monetary=one_of(*READING_CONSTRUCTORS),
)
@dataclass(frozen=True)
class DialSet:
    """The two dial readings of one evaluation cycle, held apart."""

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `DialSet.__new__(DialSet)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("equity", "monetary")

    equity: "Reading[EquityCrashScore]"
    monetary: "Reading[MonetaryDebasementScore]"

    def __post_init__(self) -> None:
        for field_name in DIAL_FIELDS:
            reading = getattr(self, field_name)
            # EXACT TYPE IDENTITY, not isinstance, and the class's declared attribute
            # surface is re-verified on the way in (CD-ASR-F02). This is a consumer
            # boundary: a subclass carrying a numeric member would otherwise be accepted
            # here exactly as a Reading is, and a class mutated after import would carry
            # its extra member into the dial set unremarked.
            if type(reading) not in READING_CONSTRUCTORS:
                raise TypeError(
                    f"DialSet.{field_name} must be a Reading "
                    f"(Value | Degraded | Unknown), got {type(reading).__name__}"
                )
            assert_closed_surface(type(reading))
        _reject_cross_typed(self.equity, EquityCrashScore, "equity")
        _reject_cross_typed(self.monetary, MonetaryDebasementScore, "monetary")


def _reject_cross_typed(reading: object, expected: type, field_name: str) -> None:
    """Refuse a reading whose payload is the *other* dial's score type.

    Without this the two slots would be structurally interchangeable, and two dials that
    can be swapped are one dial with two names.
    """
    if type(reading) in (Value, Degraded):
        # EXACT TYPE, not isinstance (CD-AC-005, Class 2). `isinstance` here asked
        # `type(expected).__instancecheck__` — a metaclass method — whether the payload
        # belonged in this slot, and a score subclass carrying a coercion would have
        # answered yes. The sibling boundary in `dial_presentation._shown_from` already
        # admits by exact-type membership in SCORE_TYPES; this is that same rule at the
        # other consumer boundary rather than a second, looser one. A new kind of score is
        # a change to SCORE_TYPES, reviewed as one.
        if type(reading.value) is not expected:
            raise TypeError(
                f"DialSet.{field_name} must carry {expected.__name__}, got "
                f"{type(reading.value).__name__}"
            )
