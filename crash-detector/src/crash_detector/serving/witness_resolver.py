"""Serving-layer witness resolution — absence lands on UNAVAILABLE (CD-AC-005).

BLUEPRINT §6: "if ``cd-witness`` writes no panel row at all, or writes one older than its
staleness window, ``cd-public`` renders ``WITNESS UNAVAILABLE``. Both the explicit and the
implicit failure path land on the same honest state, and neither has a route to
``AGREES``."

**Six routes reach** :class:`~crash_detector.witness.panel.Unavailable` **here, and there
is no seventh route to anything else:**

* the panel row is absent                            — ``PANEL_ROW_ABSENT``
* the panel row is older than its staleness window   — ``PANEL_ROW_STALE``
* the panel row is dated in the future               — ``PANEL_ROW_FUTURE_DATED``
* the stored state is recognised but its measurements are missing, or are not finite
  floats                                             — ``PANEL_ROW_INCOHERENT``
* the stored state is not one this resolver recognises — ``PANEL_STATE_UNRECOGNISED``
* the stored state says the feed was unreachable     — ``WITNESS_FEED_UNREACHABLE``

The ones after the first two matter as much as the first two. A resolver that defaulted an
unrecognised, half-written or future-dated row to agreement would satisfy CD-AC-005's
letter for the case somebody tested and violate its proposition for every case nobody
thought of. In particular:

* **Future-dated rows.** A row whose ``as_of_utc`` is ahead of ``now_utc`` would never age
  out of any staleness window. Without this branch, one bad clock upstream produces a
  panel that reads ``AGREES`` permanently, and reads it most confidently exactly when the
  witness pipeline is broken.
* **A staleness window wide enough to make staleness meaningless.** ``float("inf")``
  seconds is not a lenient window, it is the abolition of staleness — and so, in every way
  that matters, is ``1e18``. Refusing only the first was **CD-ASR-F06**: the auditor passed
  ``1e18`` with a row **ten years old** and marked ``AGREES`` and got ``WITNESS AGREES``,
  with **no source edit at all**. The window is now admitted through
  :class:`~crash_detector.staleness.StalenessWindow`, which refuses — never clamps —
  anything above a ceiling DERIVED from ``PID.md`` §5's ratified 15-minute detectability
  budget. Read that module for the derivation.
* **Agreement without evidence of freshness.** ``Agrees`` now requires
  :class:`~crash_detector.staleness.FreshnessEvidence`, whose construction *is* the age
  comparison. Bounding the window alone would have left every route that never reaches the
  comparison — an exception handler, a fallback branch, a caller of a private helper —
  free to produce agreement. There is no such route now, because the comparison is inside
  the value that agreement is made of.
* **Coercion.** ``float(row.measures[k])`` would happily turn ``"0.0"``, ``True`` or
  ``Decimal("0")`` into a divergence measure of zero — perfect agreement, manufactured
  from a type error. Measurements must already be finite floats; anything else is
  ``PANEL_ROW_INCOHERENT`` (Standards Baseline §4: reject, do not coerce).

Note the row model: measurements arrive in a mapping whose keys are **present or absent**,
never present-and-null. There is no ``float | None`` here, so there is no null that could
be read as a zero measure of divergence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Union

from crash_detector.admission import admits, one_of
from crash_detector.own_terms import NotEstablishedOnOwnTerms, own_float, own_str
from crash_detector.staleness import FreshnessEvidence, StalenessWindow
from crash_detector.time_utc import age_seconds, ensure_utc
from crash_detector.witness.panel import (
    PANEL_CONSTRUCTORS,
    PANEL_STATES,
    Agrees,
    Diverges,
    Unavailable,
    WitnessPanel,
)

__all__ = [
    "PanelRow",
    "resolve_panel",
    "render_panel",
    "PANEL_TEXT",
    "WITNESS_UNAVAILABLE_TEXT",
    "WITNESS_AGREES_TEXT",
    "WITNESS_DIVERGES_TEXT",
]

WITNESS_UNAVAILABLE_TEXT = "WITNESS UNAVAILABLE"
WITNESS_AGREES_TEXT = "WITNESS AGREES"
WITNESS_DIVERGES_TEXT = "WITNESS DIVERGES"

_DIVERGENCE_MEASURE = "divergence_measure"
_THRESHOLD = "threshold"

_STATE_AGREES, _STATE_DIVERGES, _STATE_UNAVAILABLE = PANEL_STATES


@dataclass(frozen=True)
class PanelRow:
    """One row as read from ``publication.witness_panel``.

    ``measures`` holds only the measurements the row actually carried. A missing key is a
    missing measurement; there is no null to misread.

    ``as_of_utc`` is what the witness data is for; ``published_utc`` is when the row was
    written. Freshness is judged on the former, because "we wrote a row recently" is not
    "the witnesses are current".
    """

    state: str
    as_of_utc: datetime
    published_utc: datetime
    measures: Mapping[str, float]

    def __post_init__(self) -> None:
        # EVERY FIELD RE-ESTABLISHED ON THIS SYSTEM'S OWN TERMS (CD-AC-005, Class 2).
        #
        # `state` decides which panel constructor is reached, and it decides it with `==`
        # against the three declared discriminators. `==` is the LEFT operand's to define,
        # so `isinstance(self.state, str)` admitted a subclass that then answered the
        # question itself: a row whose stored state is UNAVAILABLE — the witness feed is
        # DEAD — compares equal to "AGREES" and renders WITNESS AGREES. `own_str` copies
        # the code points out of the object, so what is compared is a plain `str`.
        #
        # The measure KEYS are the same shape one level down: `key not in row.measures` is
        # decided by the stored keys' `__hash__` and `__eq__`, so a key that is not
        # "divergence_measure" can answer to that name and supply the measurement. A
        # non-`str` key is refused rather than kept, because a key this system cannot
        # re-establish is a key whose hashing it does not control.
        try:
            object.__setattr__(self, "state", own_str(self.state))
        except NotEstablishedOnOwnTerms as refusal:
            raise TypeError(f"PanelRow.state must be a str: {refusal}") from None
        try:
            object.__setattr__(
                self,
                "measures",
                {own_str(key): value for key, value in dict(self.measures).items()},
            )
        except NotEstablishedOnOwnTerms as refusal:
            raise TypeError(
                f"every PanelRow.measures key must be a str: {refusal}"
            ) from None
        object.__setattr__(self, "as_of_utc", ensure_utc(self.as_of_utc))
        object.__setattr__(self, "published_utc", ensure_utc(self.published_utc))


@admits(
    row=one_of(PanelRow, None),
    now_utc=datetime,
    staleness_window_seconds=float,
)
def resolve_panel(
    row: Union[PanelRow, None],
    *,
    now_utc: datetime,
    staleness_window_seconds: float,
) -> "WitnessPanel":
    """Resolve a stored panel row to a :class:`WitnessPanel`.

    ``row is None`` means ``cd-witness`` wrote nothing. It resolves to ``Unavailable``,
    never to ``Agrees``.

    **A4 OF BP-AMENDMENT-0001 §D.2, ESTABLISHED AT THE DOOR AND DERIVED FROM THIS
    SIGNATURE.** ``row`` must be exactly a :class:`PanelRow` or exactly ``None`` —
    ``ASR3-F04`` supplied a duck row whose ``state`` PROPERTY answered ``"AGREES"`` while
    its stored state was ``UNAVAILABLE``, and it rendered ``WITNESS AGREES`` with the
    witness feed dead. A ``PanelRow`` SUBCLASS is refused for the same reason and not as a
    side effect: a subclass may shadow ``state``, ``as_of_utc`` or ``measures`` with a
    property, and a property is the caller's code answering the question at the moment this
    resolver asks it. The one door that survives the refusal is ``PanelRow`` construction
    itself, which re-establishes every field on this system's own terms.

    Neither requirement is written in this body. Both are read from the signature above.
    ``resolve_panel(row, now_utc=..., staleness_window_seconds=..., tolerate=True)`` — a
    fourth argument added here — refuses on EVERY call, including calls that do not pass
    it.
    """
    instant = ensure_utc(now_utc)
    window = StalenessWindow(seconds=staleness_window_seconds)

    if row is None:
        return Unavailable(reason="PANEL_ROW_ABSENT", since_utc=instant)

    age = age_seconds(as_of_utc=row.as_of_utc, now_utc=instant)
    if age < 0.0:
        return Unavailable(reason="PANEL_ROW_FUTURE_DATED", since_utc=instant)
    if not window.covers(age):
        return Unavailable(reason="PANEL_ROW_STALE", since_utc=row.as_of_utc)

    if row.state == _STATE_UNAVAILABLE:
        return Unavailable(
            reason="WITNESS_FEED_UNREACHABLE", since_utc=row.as_of_utc
        )

    if row.state == _STATE_AGREES:
        measure = _finite_measure(row, _DIVERGENCE_MEASURE)
        if measure is None:
            return Unavailable(reason="PANEL_ROW_INCOHERENT", since_utc=row.as_of_utc)
        return Agrees(
            divergence_measure=measure,
            as_of_utc=row.as_of_utc,
            freshness=FreshnessEvidence(
                as_of_utc=row.as_of_utc,
                observed_at_utc=instant,
                window=window,
            ),
        )

    if row.state == _STATE_DIVERGES:
        measure = _finite_measure(row, _DIVERGENCE_MEASURE)
        threshold = _finite_measure(row, _THRESHOLD)
        if measure is None or threshold is None:
            return Unavailable(reason="PANEL_ROW_INCOHERENT", since_utc=row.as_of_utc)
        return Diverges(
            divergence_measure=measure,
            threshold=threshold,
            as_of_utc=row.as_of_utc,
        )

    return Unavailable(reason="PANEL_STATE_UNRECOGNISED", since_utc=row.as_of_utc)


def _finite_measure(row: PanelRow, key: str) -> Union[float, None]:
    """The measurement stored under ``key``, or ``None`` if there is not an honest one.

    ``None`` here means "this row cannot be read", and every caller turns it into
    ``PANEL_ROW_INCOHERENT``. It is never turned into a measurement.

    Returning ``Union[float, None]`` is confined to this private helper on the serving
    path and never crosses into the dial path, where ``float | None`` is banned outright
    (CD-AC-001). Here the two callers both branch on ``is None`` immediately, and the type
    that leaves this module is the :class:`WitnessPanel` sum type.

    **THE NUMBER THAT LEAVES HERE IS THIS SYSTEM'S OWN (CD-AC-005, Class 2, the sibling
    CD-ASR-WO2-02 named in the same breath as F02).** This helper used to end
    ``return observed`` after ``isinstance(observed, float)``, and a ``float`` subclass
    passed that check — the very type :class:`~crash_detector.staleness.StalenessWindow`
    refuses by exact type four modules away, so the two modules disagreed about whether a
    subclass of a number is a number. It mattered because ``math.isfinite`` consults
    ``__float__`` and the stored measure's ``__eq__`` and ``__lt__`` then belong to the
    caller. :func:`crash_detector.own_terms.own_float` reads the stored double out of the
    object rather than asking it, so what is returned is a plain ``float`` and the
    finiteness test below is made on THAT.

    The two modules now agree on the DOCTRINE — no judgement is delegated to a supplied
    object — while applying different remedies, and the difference is argued in
    :func:`own_float`: a window is configuration and can afford outright refusal, a
    measurement is supplied data where ``numpy.float64`` is ordinary and refusal would
    break the one path that actually reads the outside world.
    """
    if key not in row.measures:
        return None
    observed = row.measures[key]
    try:
        established = own_float(observed)
    except NotEstablishedOnOwnTerms:
        return None
    if not math.isfinite(established):
        return None
    return established


#: Rendering, as data: exactly one text per constructor, and no entry for anything else.
PANEL_TEXT = {
    Agrees: WITNESS_AGREES_TEXT,
    Diverges: WITNESS_DIVERGES_TEXT,
    Unavailable: WITNESS_UNAVAILABLE_TEXT,
}


@admits(panel=one_of(*PANEL_CONSTRUCTORS))
def render_panel(panel: "WitnessPanel") -> str:
    """The text a surface shows for a panel value.

    Exhaustive by construction: an unrecognised member raises rather than falling through
    to the agreement string. There is no default argument to this lookup, deliberately —
    a default here is the whole of CD-AC-005's failure mode in one line.
    """
    try:
        return PANEL_TEXT[type(panel)]
    except KeyError:
        raise TypeError(
            f"not a WitnessPanel: {type(panel).__name__}. The sum type is closed; "
            "there is no fall-through, least of all to agreement."
        ) from None
