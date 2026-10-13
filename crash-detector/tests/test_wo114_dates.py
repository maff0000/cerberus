"""WO-1.14 the observation-date helper: the two cadences it states, and everything it refuses.

``ingestion.backfill_dates`` is pure arithmetic over a declared ``as_of_rule`` — no clock, no
socket, no store. So these tests are about exactly two things: that the dates it produces are
the ones the SOURCE actually dates its observations at, and that every cadence it cannot
state as a formula is a loud refusal rather than a plausible-looking list.

THE CONVENTION IS CHECKED AGAINST THE CATALOG'S OWN AGEING RULE, not against a literal typed
twice. ``as_of_for(d, "quarter_end", now)`` is the function that ages a quarterly figure to
its quarter end, and it can only be correct if ``d`` is the quarter START — so asserting that
every generated date survives a round trip through it is asserting the convention itself. If
FRED ever moved to dating GDP at the quarter end, that assertion is what would fail.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from ingestion.adapters import as_of_for
from ingestion.backfill_dates import GENERABLE_AS_OF_RULES, last_periods, observation_dates
from ingestion.catalog import INGREDIENTS

NOW = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
TODAY = NOW.date()


def _ing(source_id: str):
    return next(i for i in INGREDIENTS if i.source_id == source_id)


# --- the two cadences it states --------------------------------------------------------- #


def test_a_quarterly_series_is_dated_at_the_quarter_starts():
    """GDP's eight most recent published quarters, as FRED dates them: 01/04/07/10-01."""
    assert observation_dates(_ing("fred.GDP"), "2024-07-01", "2026-04-01") == (
        "2024-07-01", "2024-10-01", "2025-01-01", "2025-04-01",
        "2025-07-01", "2025-10-01", "2026-01-01", "2026-04-01")


def test_a_monthly_series_is_dated_at_the_month_starts():
    assert observation_dates(_ing("fred.UMCSENT"), "2026-06-01", "2026-09-30") == (
        "2026-06-01", "2026-07-01", "2026-08-01", "2026-09-01")


def test_the_bounds_are_inclusive_bounds_and_not_anchors():
    """A start mid-quarter does not shift the grid; it just excludes the quarter it is inside."""
    assert observation_dates(_ing("fred.GDP"), "2024-08-15", "2025-05-01") == (
        "2024-10-01", "2025-01-01", "2025-04-01")


def test_a_range_containing_no_period_boundary_is_empty_and_not_an_error():
    assert observation_dates(_ing("fred.GDP"), "2025-02-01", "2025-03-31") == ()
    assert observation_dates(_ing("fred.GDP"), "2025-06-01", "2025-01-01") == ()


@pytest.mark.parametrize("source_id", ["fred.GDP", "fred.NCBEILQ027S", "fred.UMCSENT",
                                       "fred.CPIAUCSL.pc1", "fred.CPILFESL", "fred.M2SL.pc1",
                                       "fred.PCEPILFE.pc1", "fred.SAHMREALTIME"])
def test_every_generated_date_is_the_period_start_its_ageing_rule_assumes(source_id):
    """The round trip that IS the convention: ageing a generated date lands on the period end.

    ``as_of_for`` moves a ``month_end``/``quarter_end`` date to the last day of its month or
    quarter. That is only the right ageing if the date it was given was the period's FIRST
    day — so a generated date whose aged form is not the last day of its own period would
    mean this module and the catalog disagree about how the source dates its observations.
    """
    ing = _ing(source_id)
    generated = observation_dates(ing, "2024-01-01", "2026-04-01")
    assert generated, "the range must produce dates or this test measures nothing"
    for day in generated:
        start = date.fromisoformat(day)
        assert start.day == 1
        aged = as_of_for(day, ing.as_of_rule, NOW).date()
        assert (aged + timedelta(days=1)).day == 1   # the aged form is a MONTH END
        months = (aged.year - start.year) * 12 + aged.month - start.month
        assert months == (2 if ing.as_of_rule == "quarter_end" else 0)


def test_the_generated_dates_cover_every_catalog_series_the_rules_admit():
    """No FRED series declaring a generable rule is left unanswerable, and none is invented."""
    generable = {i.source_id for i in INGREDIENTS
                 if i.kind == "fred" and i.as_of_rule in GENERABLE_AS_OF_RULES}
    for source_id in generable:
        assert observation_dates(_ing(source_id), "2025-01-01", "2025-12-31")
    for ing in INGREDIENTS:
        if ing.kind == "fred" and ing.source_id not in generable:
            with pytest.raises(ValueError):
                observation_dates(ing, "2025-01-01", "2025-12-31")


# --- what it refuses -------------------------------------------------------------------- #


def test_a_daily_or_weekly_series_is_refused_because_its_dates_are_a_calendar():
    for source_id in ("fred.DFF", "fred.T10Y3M", "fred.WALCL", "fred.IC4WSA"):
        with pytest.raises(ValueError, match="publisher's calendar"):
            observation_dates(_ing(source_id), "2024-01-01", "2025-01-01")


def test_the_quarterly_sloos_survey_is_refused_too_because_it_is_dated_at_its_release():
    """DRTSCILM is quarterly and declares ``obs_date``: cadence is not the question, dating is."""
    with pytest.raises(ValueError, match="publisher's calendar"):
        observation_dates(_ing("fred.DRTSCILM"), "2024-01-01", "2025-01-01")


def test_a_non_fred_kind_is_refused_on_the_same_grounds_the_backfill_refuses_it():
    for ing in INGREDIENTS:
        if ing.kind != "fred":
            with pytest.raises(ValueError, match="kind"):
                observation_dates(ing, "2024-01-01", "2025-01-01")


def test_a_bound_that_cannot_be_read_is_not_a_bound_that_is_guessed_at():
    with pytest.raises(ValueError):
        observation_dates(_ing("fred.GDP"), "2024-13-01", "2025-01-01")
    with pytest.raises(ValueError):
        observation_dates(_ing("fred.GDP"), "last tuesday", "2025-01-01")


# --- last_periods: one implementation of the convention, not two ------------------------ #


def test_last_periods_counts_back_from_the_day_it_is_given():
    assert last_periods(_ing("fred.GDP"), date(2026, 6, 30), 8) == (
        "2024-07-01", "2024-10-01", "2025-01-01", "2025-04-01",
        "2025-07-01", "2025-10-01", "2026-01-01", "2026-04-01")
    assert last_periods(_ing("fred.UMCSENT"), TODAY, 3) == (
        "2026-08-01", "2026-09-01", "2026-10-01")


def test_last_periods_returns_exactly_the_tail_of_the_same_generated_grid():
    """It computes a start and defers; a second implementation of the convention would drift."""
    for source_id, count in (("fred.GDP", 8), ("fred.NCBEILQ027S", 13), ("fred.CPILFESL", 30)):
        ing = _ing(source_id)
        tail = last_periods(ing, TODAY, count)
        whole = observation_dates(ing, "2000-01-01", TODAY.isoformat())
        assert tail == whole[-count:] and len(tail) == count


def test_last_periods_includes_the_current_unfinished_period_and_says_so():
    """2026-10-01 is a quarter that has not ended. Generable, unpublished — the driver's call.

    Recorded as a test because it is the one surprising thing about this function, and the
    docstring's advice (bound ``today`` yourself if you want only published periods) is only
    worth anything if the behaviour it warns about is pinned.
    """
    assert last_periods(_ing("fred.GDP"), TODAY, 1) == ("2026-10-01",)
    assert last_periods(_ing("fred.GDP"), date(2026, 6, 30), 1) == ("2026-04-01",)


def test_a_count_below_one_is_a_callers_error():
    with pytest.raises(ValueError):
        last_periods(_ing("fred.GDP"), TODAY, 0)
