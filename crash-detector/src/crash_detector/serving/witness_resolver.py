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
* **A non-finite staleness window.** ``float("inf")`` seconds is not a lenient window, it
  is the abolition of staleness. It is refused rather than honoured.
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

from crash_detector.time_utc import age_seconds, ensure_utc
from crash_detector.witness.panel import (
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
        if not isinstance(self.state, str):
            raise TypeError("PanelRow.state must be a str")
        object.__setattr__(self, "as_of_utc", ensure_utc(self.as_of_utc))
        object.__setattr__(self, "published_utc", ensure_utc(self.published_utc))
        object.__setattr__(self, "measures", dict(self.measures))


def resolve_panel(
    row: Union[PanelRow, None],
    *,
    now_utc: datetime,
    staleness_window_seconds: float,
) -> "WitnessPanel":
    """Resolve a stored panel row to a :class:`WitnessPanel`.

    ``row is None`` means ``cd-witness`` wrote nothing. It resolves to ``Unavailable``,
    never to ``Agrees``.
    """
    instant = ensure_utc(now_utc)
    _require_usable_window(staleness_window_seconds)

    if row is None:
        return Unavailable(reason="PANEL_ROW_ABSENT", since_utc=instant)

    age = age_seconds(as_of_utc=row.as_of_utc, now_utc=instant)
    if age < 0.0:
        return Unavailable(reason="PANEL_ROW_FUTURE_DATED", since_utc=instant)
    if age > staleness_window_seconds:
        return Unavailable(reason="PANEL_ROW_STALE", since_utc=row.as_of_utc)

    if row.state == _STATE_UNAVAILABLE:
        return Unavailable(
            reason="WITNESS_FEED_UNREACHABLE", since_utc=row.as_of_utc
        )

    if row.state == _STATE_AGREES:
        measure = _finite_measure(row, _DIVERGENCE_MEASURE)
        if measure is None:
            return Unavailable(reason="PANEL_ROW_INCOHERENT", since_utc=row.as_of_utc)
        return Agrees(divergence_measure=measure, as_of_utc=row.as_of_utc)

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


def _require_usable_window(staleness_window_seconds: float) -> None:
    """A staleness window must be a positive finite number of seconds.

    Refused rather than defaulted. A caller that cannot state a window does not get a
    lenient one — it gets an error, because "no window" and "a very large window" both
    mean nothing is ever stale.
    """
    window = staleness_window_seconds
    if isinstance(window, bool) or not isinstance(window, (int, float)):
        raise TypeError(
            f"staleness_window_seconds must be a number, got {type(window).__name__}"
        )
    if not math.isfinite(window) or window <= 0.0:
        raise ValueError(
            "staleness_window_seconds must be positive and finite; an unbounded "
            "staleness window is no staleness window"
        )


def _finite_measure(row: PanelRow, key: str) -> Union[float, None]:
    """The measurement stored under ``key``, or ``None`` if there is not an honest one.

    ``None`` here means "this row cannot be read", and every caller turns it into
    ``PANEL_ROW_INCOHERENT``. It is never turned into a measurement.

    Returning ``Union[float, None]`` is confined to this private helper on the serving
    path and never crosses into the dial path, where ``float | None`` is banned outright
    (CD-AC-001). Here the two callers both branch on ``is None`` immediately, and the type
    that leaves this module is the :class:`WitnessPanel` sum type.
    """
    if key not in row.measures:
        return None
    observed = row.measures[key]
    if isinstance(observed, bool) or not isinstance(observed, float):
        return None
    if not math.isfinite(observed):
        return None
    return observed


#: Rendering, as data: exactly one text per constructor, and no entry for anything else.
PANEL_TEXT = {
    Agrees: WITNESS_AGREES_TEXT,
    Diverges: WITNESS_DIVERGES_TEXT,
    Unavailable: WITNESS_UNAVAILABLE_TEXT,
}


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
