"""``WitnessPanel`` — unavailable is not agreement (BLUEPRINT §6, CD-AC-005).

    WitnessPanel := Agrees(divergence_measure, as_of_utc)
                  | Diverges(divergence_measure, threshold, as_of_utc)
                  | Unavailable(reason, since_utc)

``Unavailable`` is a **distinct constructor**, so it cannot be rendered by the same branch
as ``Agrees``. There is no default, and there is no route from absence to agreement
anywhere in this module or in the resolver that produces these values.

``Agrees`` additionally carries :class:`~crash_detector.staleness.FreshnessEvidence`, so it
cannot be constructed at all for an observation that was not current when it was read
(CD-ASR-F06). Read :mod:`crash_detector.staleness` for that invariant and for the derivation
of the window ceiling.

PID doctrine §3.4: "External sources are witnesses, never ingredients. A witness that is
also an ingredient cannot corroborate anything." A witness panel that quietly reads AGREES
when the witness feed is dead corroborates nothing while looking like corroboration —
which is worse than no panel at all, because it manufactures confidence.

Reaching :class:`Agrees` requires a **measurement**. It cannot be reached by absence, by
staleness, by a half-written row, or by a stored state the resolver does not recognise.

Divergence *computation* is WO-4 (CD-AC-004). WO-2 delivers the type and the
absence/staleness mapping, which is what CD-AC-005 needs and no more. Nothing here feeds a
dial, and ``cd_witness`` will hold no grant on ``dial.*``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Union

from crash_detector.staleness import FreshnessEvidence
from crash_detector.time_utc import ensure_utc

__all__ = [
    "Agrees",
    "AgreementWithoutFreshnessEvidence",
    "Diverges",
    "Unavailable",
    "WitnessPanel",
    "PANEL_CONSTRUCTORS",
    "PANEL_STATES",
    "UNAVAILABLE_REASONS",
    "panel_state",
]


def _require_finite_float(type_name: str, field_name: str, observed: object) -> None:
    """A measurement must be a finite float. ``bool`` is refused ahead of the float test.

    Refused, not coerced: ``float("0.0")`` and ``float(True)`` both succeed and both would
    produce a divergence measure of zero, which reads as perfect agreement.
    """
    if isinstance(observed, bool) or not isinstance(observed, float):
        raise TypeError(
            f"{type_name}.{field_name} must be a float, got {type(observed).__name__}"
        )
    if not math.isfinite(observed):
        raise ValueError(f"{type_name}.{field_name} must be finite, got {observed!r}")


class AgreementWithoutFreshnessEvidence(ValueError):
    """Agreement was claimed without positive, coherent evidence of freshness."""


@dataclass(frozen=True)
class Agrees:
    """The witnesses were reachable, current, and within the divergence threshold.

    **CURRENT is a field, not a hope (CD-ASR-F06).** ``freshness`` is a
    :class:`~crash_detector.staleness.FreshnessEvidence`, which cannot itself be
    constructed for an observation outside its window — and no window above
    :data:`~crash_detector.staleness.STALENESS_WINDOW_CEILING_SECONDS` can be constructed
    at all. So a decade-old row cannot produce an ``Agrees`` by ANY route into any
    resolver, including a route that skips the age comparison entirely: there is no such
    route, because the comparison lives inside the evidence and the evidence is required.

    The evidence must be about THIS reading's instant. Binding ``freshness.as_of_utc`` to
    ``as_of_utc`` is what stops the obvious evasion — attaching evidence about some other,
    fresher observation to an agreement about a stale one.
    """

    divergence_measure: float
    as_of_utc: datetime
    freshness: FreshnessEvidence

    def __post_init__(self) -> None:
        _require_finite_float("Agrees", "divergence_measure", self.divergence_measure)
        object.__setattr__(self, "as_of_utc", ensure_utc(self.as_of_utc))
        if type(self.freshness) is not FreshnessEvidence:
            raise AgreementWithoutFreshnessEvidence(
                "Agrees requires FreshnessEvidence, got "
                f"{type(self.freshness).__name__}. Reaching agreement requires a "
                "MEASUREMENT that the witnesses were current; an object that merely "
                "resembles one is not that measurement, and neither is a subclass that "
                "may have redefined how the measurement is made. The EXACT type is "
                "required — FreshnessEvidence refuses subclassing for the same reason."
            )
        if self.freshness.as_of_utc != self.as_of_utc:
            raise AgreementWithoutFreshnessEvidence(
                f"the freshness evidence is for {self.freshness.as_of_utc!r} but this "
                f"agreement is for {self.as_of_utc!r}. Evidence about a different "
                "observation is not evidence about this one."
            )


@dataclass(frozen=True)
class Diverges:
    """The witnesses were reachable and current, and disagreed beyond threshold.

    Divergence is an alarm, never an adjustment (BLUEPRINT §6, CD-AC-004).
    """

    divergence_measure: float
    threshold: float
    as_of_utc: datetime

    def __post_init__(self) -> None:
        _require_finite_float("Diverges", "divergence_measure", self.divergence_measure)
        _require_finite_float("Diverges", "threshold", self.threshold)
        object.__setattr__(self, "as_of_utc", ensure_utc(self.as_of_utc))


@dataclass(frozen=True)
class Unavailable:
    """No honest statement about witness agreement could be made.

    Carries **no divergence measure**, because there is none. There is nothing on this
    type that a rendering layer could mistake for a measurement, and no field a later
    edit could default to zero.
    """

    reason: str
    since_utc: datetime

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError("Unavailable requires a stated reason")
        if self.reason not in UNAVAILABLE_REASONS:
            raise ValueError(
                f"unknown Unavailable reason {self.reason!r}; the declared reasons are "
                f"{UNAVAILABLE_REASONS}. Every route to unavailability is named, so "
                '"we do not know why" is never itself silently a reason.'
            )
        object.__setattr__(self, "since_utc", ensure_utc(self.since_utc))


#: The sum type. Closed.
WitnessPanel = Union[Agrees, Diverges, Unavailable]

#: The complete set of constructors, for guards that must enumerate them.
PANEL_CONSTRUCTORS: tuple[type, ...] = (Agrees, Diverges, Unavailable)

#: The persisted discriminator values for ``publication.witness_panel``.
PANEL_STATES: tuple[str, ...] = ("AGREES", "DIVERGES", "UNAVAILABLE")

#: Stable reason classes for :class:`Unavailable`. Every route to unavailability is
#: named, so a new route cannot be added without naming it here first.
UNAVAILABLE_REASONS: tuple[str, ...] = (
    "PANEL_ROW_ABSENT",
    "PANEL_ROW_STALE",
    "PANEL_ROW_FUTURE_DATED",
    "PANEL_ROW_INCOHERENT",
    "PANEL_STATE_UNRECOGNISED",
    "WITNESS_FEED_UNREACHABLE",
)

_STATE_BY_TYPE = {Agrees: "AGREES", Diverges: "DIVERGES", Unavailable: "UNAVAILABLE"}


def panel_state(panel: "WitnessPanel") -> str:
    """The persisted discriminator for a panel value.

    An unrecognised member raises. It is not defaulted, and in particular it is never
    defaulted to ``AGREES``.
    """
    try:
        return _STATE_BY_TYPE[type(panel)]
    except KeyError:
        raise TypeError(
            f"not a WitnessPanel: {type(panel).__name__}. The sum type is closed; "
            "there is no fall-through, least of all to agreement."
        ) from None
