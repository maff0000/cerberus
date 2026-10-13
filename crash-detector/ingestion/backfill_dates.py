"""The observation dates a FRED series is DATED at, for the two cadences a formula can state.

WO-1.14. ``ingestion.backfill.backfill_range`` takes an EXPLICIT list of observation dates
and derives nothing, deliberately — its own docstring says a driver that guessed at a
publication calendar "would be inventing the very dates whose values it then claims to have
recovered". That is still true. This module is what a CALLER uses to produce such a list for
the cases where the dates are not a calendar at all but an arithmetic fact about the month,
and it refuses every other case rather than guessing.

IT IS NOT A CADENCE ENGINE, AND THE DIFFERENCE IS THE WHOLE POINT
    "The observation dates of all 23 FRED pairs across 25 years" is a question about
    publication calendars: which Wednesdays WALCL was dated at, which business days the
    Treasury curve printed on, which weeks IC4WSA skipped. None of that is derivable from a
    date and a rule; it is a property of each publisher's history, and the only honest way to
    get it is to read it off a body the source itself served. That generator is a separate,
    later piece of work and :func:`observation_dates` is not a down payment on it — it is the
    small part that CAN be stated as a formula, stated as one, with the rest refused out
    loud (:data:`GENERABLE_AS_OF_RULES`).

WHERE THE CONVENTION COMES FROM: ``ing.as_of_rule``, AND WHY THAT IS NOT A COINCIDENCE
    The cadence is NOT inferred from the series id, from the poll interval, or from a table
    kept here that would have to be maintained alongside the catalog. It is read off the
    ingredient's declared ``as_of_rule``, because that field exists precisely BECAUSE of the
    dating convention this module needs:

    * ``quarter_end`` is declared (``ingestion.catalog``: GDP, NCBEILQ027S) for a QUARTERLY
      series *FRED dates at the quarter START* — the rule ages the figure to the quarter's
      last day because the source dates it at the first. So the observation dates are the
      quarter starts: 01-01, 04-01, 07-01, 10-01.
    * ``month_end`` is declared for a MONTHLY series *FRED dates at the FIRST of the month*,
      for the same reason. So the observation dates are the month starts.
    * ``obs_date`` means "the date as published" — daily, weekly, and the quarterly SLOOS
      survey, which is dated at its own release and not at a period boundary. There is no
      formula, so there is a :class:`ValueError`.

    Verified against the live DEV store rather than taken from the docstring (2026-10-13):
    ``fred.GDP`` carries ``observation_date`` 2026-04-01 under source period 2026-06-30, and
    ``fred.UMCSENT`` carries 2026-08-01 under 2026-08-31.

    So a monthly series added to the catalog tomorrow is covered by the same declaration that
    makes its ageing right, and a series whose dating this module cannot state is refused by
    the same declaration rather than by a list somebody forgot to update.

NOTHING HERE FETCHES, AND NOTHING HERE DECIDES WHETHER A DATE MAY BE STORED
    It returns strings. Whether a date is REFUSED for being before
    ``ingestion.vintage.STABILITY_MEASURED_FROM``, whether it is already admitted, and which
    adapter answers for it are all the driver's, and this module knows none of them: handing
    it those judgements would put two modules in charge of the same rule. A range that
    reaches back past a stability measurement is therefore generable here and refused there,
    which is the right order — the caller gets to ASK for the honest range and gets told,
    date by date, what happened to each.
"""

from __future__ import annotations

import calendar
from datetime import date
from typing import Tuple

from ingestion.catalog import Ingredient

__all__ = ["GENERABLE_AS_OF_RULES", "observation_dates"]

#: The declared as-of rules whose SOURCE dating convention is an arithmetic fact about the
#: month, and therefore the only ones this module will answer for. Stated positively so
#: every other rule — present or added later — is a refusal rather than a quiet default.
GENERABLE_AS_OF_RULES = ("quarter_end", "month_end")

#: The month each quarter is dated at, by the convention ``quarter_end`` is declared for.
_QUARTER_START_MONTHS = (1, 4, 7, 10)


def observation_dates(ing: Ingredient, start: str, end: str) -> Tuple[str, ...]:
    """The dates the SOURCE dates ``ing``'s observations at, within ``[start, end]``, ascending.

    ``start`` and ``end`` are ISO ``YYYY-MM-DD`` and are INCLUSIVE BOUNDS on the returned
    dates, not themselves observation dates: a start of 2024-08-15 for a quarterly series
    yields 2024-10-01 first, because 2024-07-01 is outside the range asked for. They are
    bounds rather than anchors so that a caller can say "the last two years" without first
    having to know where the period boundaries fall — which is the thing this function is
    for.

    An empty range (``end`` before ``start``, or no period boundary between them) is an empty
    tuple and not an error: asking for the quarter starts inside one month is a reasonable
    question with the answer "none", and ``backfill_range`` of no dates does nothing.

    Raises :class:`ValueError` for a kind that is not ``fred`` (ALFRED serves vintages of
    FRED series and nothing else — the same refusal, on the same grounds, as
    ``ingestion.backfill_adapters.VINTAGE_BACKFILLABLE_KINDS``) and for an as-of rule outside
    :data:`GENERABLE_AS_OF_RULES`, whose dates are a publication calendar this module
    declines to invent. Also for a date string it cannot read: a bound we cannot parse is not
    a bound we may guess at.
    """
    if ing.kind != "fred":
        raise ValueError(
            f"{ing.source_id} is kind {ing.kind!r}; this module states the dating convention of "
            f"FRED series only (see ingestion.backfill_adapters.VINTAGE_BACKFILLABLE_KINDS)"
        )
    if ing.as_of_rule not in GENERABLE_AS_OF_RULES:
        raise ValueError(
            f"{ing.source_id} declares as-of rule {ing.as_of_rule!r}; observation dates are "
            f"derivable only for {GENERABLE_AS_OF_RULES}. The dates of a daily or weekly series "
            f"are its publisher's calendar and must be read off a body, not computed here"
        )
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    months = _QUARTER_START_MONTHS if ing.as_of_rule == "quarter_end" else tuple(range(1, 13))

    dates = []
    for year in range(first.year, last.year + 1):
        for month in months:
            day = date(year, month, 1)
            if first <= day <= last:
                dates.append(day.isoformat())
    return tuple(dates)


def last_periods(ing: Ingredient, today: date, count: int) -> Tuple[str, ...]:
    """The ``count`` most recent observation dates at or before ``today``. A convenience.

    The same rules and the same refusals as :func:`observation_dates`, which it defers to —
    this computes a START and nothing else, so there is one implementation of the dating
    convention and not two. ``today`` is passed IN rather than read from a clock: a function
    that read the wall clock could not be tested against a fixed instant, and every other
    date-bearing thing in this tree takes its ``now`` from the caller for the same reason.

    What it does NOT do is promise those periods have been PUBLISHED. The quarter containing
    ``today`` is dated at a quarter start that has already passed, so for GDP on 2026-10-13
    the most recent date is 2026-10-01 — a quarter that has not ended and whose advance
    estimate does not exist. Asking ALFRED for it is a correct, recorded EMPTY (no vintage
    ever published it), not a defect: see ``ingestion.backfill``'s failure buckets. A caller
    who wants only published periods should bound ``today`` itself.
    """
    if count < 1:
        raise ValueError(f"count must be at least 1, not {count}")
    # Wide enough to contain `count` periods of the slowest cadence this module states, then
    # trimmed from the right: the arithmetic for "how many months back is N quarters" is the
    # convention itself, and it already exists in observation_dates.
    start = date(today.year - (count // 4 + 2), 1, 1)
    generated = observation_dates(ing, start.isoformat(), today.isoformat())
    return generated[-count:]
