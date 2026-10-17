"""Per-row relevance windows DERIVED from real measured release lag, not from round numbers.

This closes the OPEN ITEM both ``buffett_indicator`` and ``sloos_bank_lending`` carry in
``governance/mapping/indicator_mapping.yaml``: that their ratified windows are flat numbers
over a rhythm that is not flat. It closes it by DERIVING each window from the measured
calendar instead of by making the window vary across the cycle — and the reason is worth
stating, because a reader who expects an expected-next-release model will otherwise wonder
what is missing here.

WHY ONE NUMBER PER ROW AND NOT A CURVE ACROSS THE CYCLE
-------------------------------------------------------
``ingestion.report.indicator_states`` reads ``store.latest_reading(...)`` — the NEWEST
admitted reading, always. So "is this indicator LIVE or STALE" is a genuinely BINARY
question, and the engine holds NO state between the two for a reading to pass through:

* either a newer reading has arrived, in which case the age is measured from THAT reading's
  own ``as_of`` and the clock has already reset — the old reading is not consulted at all;
* or it has not, and the only thing that can be asked is whether too much time has passed
  since the current reading's ``as_of`` with nothing newer having shown up.

A release-calendar model therefore cannot be SHARPER than a correctly-computed threshold the
way it could for a continuously-varying signal. There is no "approaching stale" the engine
could act on differently, no intermediate state a phase-aware window would populate. What
such a model CAN do — the whole of what it can do — is compute that ONE threshold HONESTLY,
from real measured evidence rather than from a round number chosen to be safely large. That
is what this module does, and emitting different thresholds at different points in the cycle
would add complexity corresponding to nothing the engine can act on.

THE DERIVATION
--------------
A reading's ``as_of`` sits at its own period's anchor — ``quarter_end`` for
``buffett_indicator``'s legs, ``obs_date`` (the quarter start) for ``sloos_bank_lending``'s,
per ``ingestion.adapters``. That reading stays the latest admitted one until the NEXT
period's print supersedes it, which happens one full cycle later PLUS that next print's own
release lag. So the peak age a HEALTHY feed reaches is ``cycle + worst measured lag``, and
the window must clear it by some margin for releases that slip:

    window = (cycle_days + worst_lag_days + tolerance_days) * 86400

``worst_lag_days`` MUST be measured from the same anchor the row's ``as_of_rule`` ages from,
since that is the anchor the age is computed against. The probe records both framings per
leg for exactly this reason.

WHAT THIS MODULE IS AND IS NOT
------------------------------
It is a TRACEABLE DERIVATION of figures the Owner ALREADY RATIFIED on 2026-10-16 (210 days
and 150 days) — the same arithmetic those mapping notes work out in prose, written as code
so it can be re-derived from the evidence rather than re-read from a comment. It is NOT a
new number and NOT an authority: the ratified mapping remains the declaration, and
``crash_detector.staleness`` remains the only enforcer. Both figures below reproduce their
ratified counterparts EXACTLY; ``buffett_indicator``'s is also, to the second,
``RELEVANCE_WINDOW_CEILING_SECONDS``, because that ceiling is derived from this very row as
the widest window the mapping declares.

A pure function over its three inputs, deliberately: it reads neither the catalog nor the
probe file, so a caller cannot mistake it for the source of the measurements.
"""

from __future__ import annotations

__all__ = [
    "peak_relevance_seconds",
    "BUFFETT_INDICATOR_RELEVANCE_SECONDS",
    "SLOOS_BANK_LENDING_RELEVANCE_SECONDS",
]

SECONDS_PER_DAY = 86_400


def peak_relevance_seconds(cycle_days: float, worst_lag_days: float, tolerance_days: float) -> float:
    """Seconds a HEALTHY feed on this release calendar must be allowed to go unrefreshed.

    :param cycle_days: the publication cycle — how long one reading stays the current one
        before the next period's print can supersede it (~91 for a quarterly series).
    :param worst_lag_days: the WORST MEASURED lag from the row's own ``as_of`` anchor to the
        date our feed could first have seen the print. Measured, not estimated, and from the
        same anchor the row's ``as_of_rule`` ages from.
    :param tolerance_days: headroom for a release that slips, sized against the release
        variance already on record rather than as a token cushion.

    ``cycle_days + worst_lag_days`` is the peak age a healthy feed reaches between releases;
    the tolerance is what keeps a slipped release from reading STALE anyway.
    """
    return (cycle_days + worst_lag_days + tolerance_days) * SECONDS_PER_DAY


#: ``buffett_indicator``: quarterly, both legs aged from the QUARTER END (``as_of_rule
#: quarter_end``). ``worst_lag_days`` is the SLOWER leg, ``NCBEILQ027S``, measured 67-101 days
#: from quarter end over 14 real ALFRED-vintage quarters (2023-Q1..2026-Q2) in
#: ``evidence/wo119_release_lag_probe.json``; the 101 is 2025-Q3, a 27-day outlier against that
#: leg's 67-74 norm, and taking the outlier as the worst case is the point. The faster leg,
#: ``GDP``, measured 25-84 and cannot set the window. 91 + 101 = the ~192-day measured peak; the
#: 18-day tolerance is the margin the ratified mapping note reasons out, chosen because a
#: thinner cushion than the 27-day variance already on record would re-open the false STALE
#: this window exists to close. Reproduces the ratified 18,144,000 s (210 days) EXACTLY, which
#: is also ``crash_detector.staleness.RELEVANCE_WINDOW_CEILING_SECONDS`` — this is the row that
#: ceiling is derived from.
BUFFETT_INDICATOR_RELEVANCE_SECONDS = peak_relevance_seconds(
    cycle_days=91, worst_lag_days=101, tolerance_days=18
)

#: ``sloos_bank_lending``: quarterly, both legs aged from the QUARTER START (``as_of_rule
#: obs_date``). Both legs — ``DRTSCILM`` and ``DRTSCIS``, which print together as one SLOOS
#: release — measured IDENTICALLY 30-42 days from quarter start over 15 real ALFRED-vintage
#: quarters (2023-Q1..2026-Q3) in ``evidence/wo119_release_lag_probe.json``, so either leg sets
#: the same window. 91 + 42 = the ~133-day measured peak; the 17-day tolerance is the margin the
#: ratified mapping note reasons out, sized against the 12-day spread across those quarters
#: (the 42 being 2024-Q4) and the fact that 2026-Q3 was not yet carried by any vintage inside
#: the probe's 400-day horizon. Reproduces the ratified 12,960,000 s (150 days) EXACTLY. Not the
#: widest window the mapping declares, so the engine's ceiling is not derived from this row.
SLOOS_BANK_LENDING_RELEVANCE_SECONDS = peak_relevance_seconds(
    cycle_days=91, worst_lag_days=42, tolerance_days=17
)
