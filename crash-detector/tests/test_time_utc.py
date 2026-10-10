"""UTC handling: naive is refused, never assumed (Standards Baseline §9)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from crash_detector.time_utc import (
    NaiveTimestampRejected,
    age_seconds,
    ensure_utc,
    format_utc,
    now_utc,
    parse_utc,
)

AWARE = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
NAIVE = datetime(2026, 8, 19, 12, 0, 0)


def test_ensure_utc_refuses_naive_rather_than_assuming_utc():
    with pytest.raises(NaiveTimestampRejected):
        ensure_utc(NAIVE)


def test_ensure_utc_converts_a_non_utc_offset_rather_than_refusing_it():
    plus_two = datetime(2026, 8, 19, 14, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    assert ensure_utc(plus_two) == AWARE


def test_ensure_utc_refuses_a_non_datetime():
    with pytest.raises(TypeError):
        ensure_utc("2026-08-19T12:00:00Z")


@pytest.mark.parametrize(
    "text",
    [
        "2026-08-19T12:00:00Z",
        "2026-08-19T12:00:00+00:00",
        "2026-08-19T14:00:00+02:00",
    ],
)
def test_parse_utc_accepts_every_form_that_states_its_offset(text):
    assert parse_utc(text) == AWARE


@pytest.mark.parametrize(
    "text",
    [
        "2026-08-19T12:00:00",  # no offset at all
        "2026-08-19",  # date only, therefore no offset
    ],
)
def test_parse_utc_refuses_a_timestamp_with_no_declared_offset(text):
    with pytest.raises(NaiveTimestampRejected):
        parse_utc(text)


def test_format_utc_emits_an_explicit_z():
    assert format_utc(AWARE) == "2026-08-19T12:00:00Z"


def test_format_utc_keeps_microseconds_and_still_emits_z():
    stamped = AWARE.replace(microsecond=123456)
    assert format_utc(stamped) == "2026-08-19T12:00:00.123456Z"


def test_format_utc_round_trips_through_parse_utc():
    assert parse_utc(format_utc(AWARE)) == AWARE


def test_format_utc_refuses_naive():
    with pytest.raises(NaiveTimestampRejected):
        format_utc(NAIVE)


def test_now_utc_is_aware():
    observed = now_utc()
    assert observed.tzinfo is not None
    assert observed.utcoffset() == timedelta(0)


def test_age_seconds_is_positive_for_the_past():
    assert age_seconds(as_of_utc=AWARE - timedelta(seconds=90), now_utc=AWARE) == 90.0


def test_age_seconds_is_negative_for_the_future_and_is_not_clamped():
    """A future-dated observation must be visible as such to the caller.

    Clamping a negative age to zero is how a future-dated row becomes permanently fresh.
    """
    assert age_seconds(as_of_utc=AWARE + timedelta(seconds=90), now_utc=AWARE) == -90.0
