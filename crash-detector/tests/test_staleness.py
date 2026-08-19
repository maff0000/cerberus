"""The staleness window has a ceiling, and agreement requires evidence (CD-AC-005).

CD-ASR-F06, escaped variant E07: `staleness_window_seconds=1e18` with a panel row **ten
years old** and marked AGREES rendered `WITNESS AGREES`. No source edit — configuration
alone. `_require_usable_window` refused non-finite and non-positive windows and accepted
any finite positive number.

These tests are about the CLASS, not about `1e18`. Two propositions:

1. **No window above the ceiling can be constructed at all**, and the ceiling is DERIVED
   from PID.md §5's ratified detectability budget rather than chosen. A window above it is
   REFUSED, never clamped.
2. **Agreement cannot be constructed without positive evidence of freshness**, and the
   evidence cannot be constructed for a stale or future-dated observation. So there is no
   route to agreement that skips the age comparison, because the comparison lives inside
   the value agreement is made of.

The second is the one that matters more. A ceiling alone would still leave every code path
that never reaches a comparison free to produce agreement.
"""

from __future__ import annotations

import dataclasses
import math

import pytest

from crash_detector.staleness import (
    STALENESS_WINDOW_CEILING_SECONDS,
    STALENESS_WINDOW_CEILING_SOURCE,
    FreshnessEvidence,
    FreshnessNotEstablished,
    StalenessWindow,
    StalenessWindowOutOfRange,
)
from crash_detector.time_utc import NaiveTimestampRejected

from conftest import FIXED_NOW, ago

TEN_YEARS_SECONDS = 3650 * 24 * 3600.0


# --- the ceiling is derived, and it says so --------------------------------------------- #

def test_the_ceiling_is_the_ratified_fifteen_minute_budget_in_seconds():
    """15 minutes, from PID.md §5. Not a number this codebase chose (CD-RULE-003)."""
    assert STALENESS_WINDOW_CEILING_SECONDS == 15 * 60.0


def test_the_ceiling_carries_the_clause_it_derives_from():
    """A bound whose provenance is not written down is a bound nobody can check."""
    assert "PID.md" in STALENESS_WINDOW_CEILING_SOURCE
    assert "15 minutes" in STALENESS_WINDOW_CEILING_SOURCE
    assert "RATIFIED" in STALENESS_WINDOW_CEILING_SOURCE
    assert "CD-D-003" in STALENESS_WINDOW_CEILING_SOURCE


def test_the_ceiling_is_a_ceiling_and_not_an_operating_window():
    """It must say so, because a ceiling used as a setting is the whole budget spent."""
    assert "ceiling" in STALENESS_WINDOW_CEILING_SOURCE
    assert "window_for(regime)" in STALENESS_WINDOW_CEILING_SOURCE
    assert "WO-3" in STALENESS_WINDOW_CEILING_SOURCE


# --- the window itself ------------------------------------------------------------------ #

@pytest.mark.parametrize(
    "window",
    [
        1e18,                       # E07, verbatim
        STALENESS_WINDOW_CEILING_SECONDS + 1e-9,
        901.0,
        3600.0,                     # one hour — the OLD test constant, now inadmissible
        86400.0,                    # a day
        TEN_YEARS_SECONDS,          # a decade
        1e308,                      # the largest finite float region
    ],
)
def test_a_window_above_the_ceiling_is_refused(window):
    """The class: ANY finite positive number above the ceiling, not the one E07 used."""
    with pytest.raises(StalenessWindowOutOfRange):
        StalenessWindow(seconds=window)


def test_the_refusal_names_the_ceiling_and_says_it_is_not_clamped():
    """A refusal that does not say why teaches the next author nothing."""
    with pytest.raises(StalenessWindowOutOfRange) as raised:
        StalenessWindow(seconds=1e18)
    message = str(raised.value)
    assert "900.0" in message
    assert "REFUSED, not clamped" in message
    assert "PID.md" in message


def test_the_window_is_refused_and_not_clamped():
    """A clamped window is a wrong window that looks like a right one.

    Asserted as a PROPERTY, not as a message: no object comes back at all, so there is
    nothing that could be carrying a silently reduced value.
    """
    with pytest.raises(StalenessWindowOutOfRange):
        StalenessWindow(seconds=1e18)
    # and the value that would have been clamped to is itself perfectly constructible,
    # so the refusal is about the ARGUMENT and not about the ceiling being unusable.
    assert StalenessWindow(seconds=STALENESS_WINDOW_CEILING_SECONDS).seconds == 900.0


@pytest.mark.parametrize("window", [math.inf, math.nan, -math.inf])
def test_a_non_finite_window_is_still_refused(window):
    """The half of the door that was already closed. It stays closed."""
    with pytest.raises(StalenessWindowOutOfRange):
        StalenessWindow(seconds=window)


@pytest.mark.parametrize("window", [0.0, -1.0, -1e18])
def test_a_non_positive_window_is_still_refused(window):
    with pytest.raises(StalenessWindowOutOfRange):
        StalenessWindow(seconds=window)


@pytest.mark.parametrize("window", ["600", None, True, False, [600], {"seconds": 600}])
def test_a_window_that_is_not_a_number_is_refused(window):
    """`bool` explicitly: `isinstance(True, int)` is true in Python, and `True` seconds is
    a type error wearing a value."""
    with pytest.raises(TypeError):
        StalenessWindow(seconds=window)


@pytest.mark.parametrize("window", [0.001, 1.0, 60.0, 899.0, 900.0])
def test_every_admissible_window_is_constructible(window):
    """A closure that forbids the product is not a closure."""
    assert StalenessWindow(seconds=window).seconds == float(window)


def test_the_window_is_frozen():
    window = StalenessWindow(seconds=60.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        window.seconds = 1e18  # type: ignore[misc]


def test_the_window_has_exactly_one_declared_field():
    """A declared member set, asserted by EQUALITY. A second field is where a later edit
    would put an override, and it would not be caught by a blacklist."""
    assert {f.name for f in dataclasses.fields(StalenessWindow)} == {"seconds"}


@pytest.mark.parametrize(
    ("age", "covered"),
    [
        (0.0, True),
        (1.0, True),
        (600.0, True),
        (600.0000001, False),
        (-0.001, False),
        (-86400.0, False),
        (math.nan, False),
        (math.inf, False),
        (-math.inf, False),
        (TEN_YEARS_SECONDS, False),
    ],
)
def test_covers_answers_the_freshness_question_including_at_its_edges(age, covered):
    assert StalenessWindow(seconds=600.0).covers(age) is covered


# --- freshness evidence ------------------------------------------------------------------ #

def test_freshness_evidence_can_be_made_for_a_current_observation():
    evidence = FreshnessEvidence(
        as_of_utc=ago(10), observed_at_utc=FIXED_NOW, window=StalenessWindow(seconds=600.0)
    )
    assert evidence.age_seconds == 10.0


def test_a_decade_old_observation_cannot_evidence_freshness_under_any_window():
    """E07's row, against EVERY window that can exist. There is no window it survives,
    because the widest window that can be constructed is the ceiling."""
    for window_seconds in (0.001, 1.0, 60.0, 899.0, STALENESS_WINDOW_CEILING_SECONDS):
        with pytest.raises(FreshnessNotEstablished):
            FreshnessEvidence(
                as_of_utc=ago(TEN_YEARS_SECONDS),
                observed_at_utc=FIXED_NOW,
                window=StalenessWindow(seconds=window_seconds),
            )


def test_a_stale_observation_one_second_past_the_window_cannot_evidence_freshness():
    with pytest.raises(FreshnessNotEstablished):
        FreshnessEvidence(
            as_of_utc=ago(601),
            observed_at_utc=FIXED_NOW,
            window=StalenessWindow(seconds=600.0),
        )


def test_a_future_dated_observation_cannot_evidence_freshness():
    """It would otherwise never age out of any window."""
    with pytest.raises(FreshnessNotEstablished):
        FreshnessEvidence(
            as_of_utc=ago(-1),
            observed_at_utc=FIXED_NOW,
            window=StalenessWindow(seconds=600.0),
        )


@pytest.mark.parametrize("bad", [600.0, 1e18, "600", None, True])
def test_freshness_cannot_be_evidenced_against_a_bare_number(bad):
    """A number that never passed the admission door is not a window.

    This is the route that would otherwise reopen the whole finding: evidence against
    `1e18` as a plain float would make any age look current.
    """
    with pytest.raises(TypeError):
        FreshnessEvidence(
            as_of_utc=ago(10), observed_at_utc=FIXED_NOW, window=bad
        )


def test_the_age_is_not_a_field_so_it_cannot_be_asserted_by_a_caller():
    """The comparison is DONE here, not accepted here.

    If `age_seconds` were a field, a caller could declare a decade-old observation to be
    ten seconds old and the constructor would believe it. It is a derived property over a
    declared field set asserted by equality.
    """
    assert {f.name for f in dataclasses.fields(FreshnessEvidence)} == {
        "as_of_utc",
        "observed_at_utc",
        "window",
    }
    with pytest.raises(TypeError):
        FreshnessEvidence(  # type: ignore[call-arg]
            as_of_utc=ago(TEN_YEARS_SECONDS),
            observed_at_utc=FIXED_NOW,
            window=StalenessWindow(seconds=600.0),
            age_seconds=10.0,
        )


def test_freshness_evidence_refuses_a_naive_timestamp():
    from datetime import datetime

    naive = datetime(2026, 8, 19, 12, 0, 0)
    with pytest.raises(NaiveTimestampRejected):
        FreshnessEvidence(
            as_of_utc=naive,
            observed_at_utc=FIXED_NOW,
            window=StalenessWindow(seconds=600.0),
        )


def test_freshness_evidence_is_frozen():
    evidence = FreshnessEvidence(
        as_of_utc=ago(10), observed_at_utc=FIXED_NOW, window=StalenessWindow(seconds=600.0)
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        evidence.as_of_utc = FIXED_NOW  # type: ignore[misc]


# --- the proposition, swept --------------------------------------------------------------- #

def test_no_window_and_no_age_combination_evidences_freshness_for_a_stale_observation():
    """The class, swept: every constructible window against a range of ages.

    Evidence exists if and only if the observation is inside the window and not in the
    future. Nothing outside that is reachable, at any window a caller can construct.
    """
    windows = [0.001, 1.0, 60.0, 600.0, 899.0, 900.0]
    ages = [
        -TEN_YEARS_SECONDS, -1.0, -0.001, 0.0, 0.5, 60.0, 600.0, 900.0,
        901.0, 3600.0, 86400.0, TEN_YEARS_SECONDS,
    ]
    established = []
    for window_seconds in windows:
        window = StalenessWindow(seconds=window_seconds)
        for age in ages:
            try:
                FreshnessEvidence(
                    as_of_utc=ago(age), observed_at_utc=FIXED_NOW, window=window
                )
            except FreshnessNotEstablished:
                continue
            established.append((window_seconds, age))

    expected = [
        (window_seconds, age)
        for window_seconds in windows
        for age in ages
        if 0.0 <= age <= window_seconds
    ]
    assert established == expected


def test_no_window_above_the_ceiling_exists_to_be_swept():
    """The other half of the sweep: the wide windows are not merely unhelpful, they are
    unconstructible, so they are absent from every combination above."""
    for window_seconds in (900.000001, 901.0, 3600.0, 1e18, TEN_YEARS_SECONDS):
        with pytest.raises(StalenessWindowOutOfRange):
            StalenessWindow(seconds=window_seconds)


# --- two routes this seat found against its OWN first cut, and closed --------------------- #

def test_a_float_subclass_that_redefines_comparison_is_not_a_window():
    """The route: Python tries the REFLECTED operation first when the right operand is a
    subclass of the left operand's type. So `age > window` calls `window.__lt__(age)`,
    and a subclass that answers `False` there makes every age look fresh.

    The first cut of this module used `isinstance(window, (int, float))` and then compared
    with `>`, which this defeats completely. The check is now on the EXACT type.
    """

    class NeverGreater(float):
        def __lt__(self, other):  # noqa: D105
            return False

        def __le__(self, other):  # noqa: D105
            return True

        def __gt__(self, other):  # noqa: D105
            return False

    with pytest.raises(TypeError):
        StalenessWindow(seconds=NeverGreater(1e18))


def test_an_int_subclass_is_refused_for_the_same_reason():
    class SneakyInt(int):
        def __lt__(self, other):  # noqa: D105
            return False

    with pytest.raises(TypeError):
        StalenessWindow(seconds=SneakyInt(10**18))


def test_the_window_cannot_be_subclassed_to_raise_its_own_ceiling():
    """The route: inherit, override `__post_init__`, keep passing every isinstance check.

    Refused at class-CREATION time, so the subclass does not exist to be instantiated —
    the same posture `SealedReadingType` takes for the Reading sum type.
    """
    with pytest.raises(TypeError):
        class WideWindow(StalenessWindow):
            def __post_init__(self):  # noqa: D105
                object.__setattr__(self, "seconds", 1e18)


def test_freshness_evidence_cannot_be_subclassed_to_skip_the_comparison():
    with pytest.raises(TypeError):
        class AlwaysFresh(FreshnessEvidence):
            def __post_init__(self):  # noqa: D105
                return None


def test_an_undeclared_attribute_cannot_be_injected_onto_either_value():
    """`__slots__`, so there is no instance dict for an override to live in."""
    window = StalenessWindow(seconds=600.0)
    with pytest.raises(AttributeError):
        object.__setattr__(window, "ceiling", 1e18)
    evidence = FreshnessEvidence(
        as_of_utc=ago(10), observed_at_utc=FIXED_NOW, window=window
    )
    with pytest.raises(AttributeError):
        object.__setattr__(evidence, "age_seconds", 0.0)
