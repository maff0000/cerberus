"""The observation record and its four-way outcome (BLUEPRINT §5).

The three collapsed absences stay separate: *we could not ask*, *the answer did not
conform*, and *the source has nothing* are three different facts, and none of them is a
value.
"""

from __future__ import annotations

import dataclasses

import pytest

from crash_detector.observations import (
    OK,
    OUTCOME_CLASSES,
    Empty,
    FetchFailed,
    Malformed,
    ObservationRecord,
    outcome_class,
)
from crash_detector.time_utc import NaiveTimestampRejected

from conftest import FIXED_NOW, ago


def test_the_outcome_sum_type_has_exactly_four_discriminators():
    assert OUTCOME_CLASSES == ("OK", "FETCH_FAILED", "MALFORMED", "EMPTY")


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        (OK(payload={"a": 1}, source_as_of_utc=FIXED_NOW), "OK"),
        (FetchFailed(error_class="TIMEOUT"), "FETCH_FAILED"),
        (Malformed(schema_error_class="TYPE_MISMATCH"), "MALFORMED"),
        (Empty(), "EMPTY"),
    ],
)
def test_each_outcome_maps_to_its_own_discriminator(outcome, expected):
    assert outcome_class(outcome) == expected


def test_an_unrecognised_outcome_raises_rather_than_defaulting_to_ok():
    class LooksLikeOK:
        payload = {"a": 1}
        source_as_of_utc = FIXED_NOW

    with pytest.raises(TypeError):
        outcome_class(LooksLikeOK())  # type: ignore[arg-type]


def test_only_ok_carries_a_payload_and_a_source_timestamp():
    """The three failure outcomes have nowhere to put a value, so no value can hide."""
    for outcome in (FetchFailed(error_class="TIMEOUT"),
                    Malformed(schema_error_class="TYPE_MISMATCH"),
                    Empty()):
        assert not hasattr(outcome, "payload")
        assert not hasattr(outcome, "source_as_of_utc")


def test_empty_is_nullary_so_it_can_never_acquire_a_default_value():
    assert dataclasses.fields(Empty) == ()


def test_the_outcome_types_share_no_ancestor_but_object():
    """No common base is where a `.payload` accessor could be added for all four."""
    mros = [set(t.__mro__) for t in (OK, FetchFailed, Malformed, Empty)]
    assert set.intersection(*mros) == {object}


def test_ok_refuses_a_naive_source_timestamp():
    from datetime import datetime

    with pytest.raises(NaiveTimestampRejected):
        OK(payload={}, source_as_of_utc=datetime(2026, 8, 19, 12, 0, 0))


def test_ok_copies_its_payload_so_a_caller_cannot_mutate_a_stored_observation():
    payload = {"a": 1}
    outcome = OK(payload=payload, source_as_of_utc=FIXED_NOW)
    payload["a"] = 999
    assert outcome.payload == {"a": 1}


def test_fetch_failed_requires_a_stated_error_class():
    with pytest.raises(ValueError):
        FetchFailed(error_class="")


def test_fetch_failed_refuses_a_non_integer_http_status():
    with pytest.raises(TypeError):
        FetchFailed(error_class="HTTP", http_status="503")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        FetchFailed(error_class="HTTP", http_status=True)  # type: ignore[arg-type]


def test_malformed_requires_a_stated_schema_error_class():
    with pytest.raises(ValueError):
        Malformed(schema_error_class="")


def test_an_observation_record_requires_a_source_id():
    with pytest.raises(ValueError):
        ObservationRecord(source_id="", observed_utc=FIXED_NOW, outcome=Empty())


def test_an_observation_record_refuses_an_outcome_outside_the_sum_type():
    with pytest.raises(TypeError):
        ObservationRecord(source_id="s", observed_utc=FIXED_NOW, outcome="OK")  # type: ignore[arg-type]


def test_the_attempt_time_and_the_source_time_are_separate_facts():
    """"We asked recently" is not "the data is recent"."""
    record = ObservationRecord(
        source_id="src.a",
        observed_utc=FIXED_NOW,
        outcome=OK(payload={}, source_as_of_utc=ago(86400)),
    )
    assert record.observed_utc == FIXED_NOW
    assert record.outcome.source_as_of_utc == ago(86400)


def test_a_failed_attempt_is_still_a_record():
    """Every fetch attempt produces a record, including the failures (BLUEPRINT §5).
    A failure that records nothing is indistinguishable from a fetch never scheduled."""
    record = ObservationRecord(
        source_id="src.a",
        observed_utc=FIXED_NOW,
        outcome=FetchFailed(error_class="CONNECT_TIMEOUT"),
    )
    assert outcome_class(record.outcome) == "FETCH_FAILED"
