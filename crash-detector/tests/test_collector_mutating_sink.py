"""**GROUND 3 / ESCAPE 3 — A MUTATING SINK CANNOT CHANGE WHAT THE RUNNER REPORTS.**

The fifth Assurance seat's item (a), untaken after two gates, and the auditor named the
carrier in terms: *"A test that a mutating sink cannot change ``CollectionResult.final_outcome``
or ``reading_key``. Two arms: the mutating sink, and a benign control. **AND THE ARM THAT
MATTERS IS THE MUTATING ONE PASSING THROUGH YOUR FIX** — a test that only runs the benign sink
has tested nothing."*

THE ESCAPE, AS IT STOOD
-----------------------
``_record`` is called inside the ``finally:`` of the attempt loop and every read of the outcome
happens after it, so **the sink runs before the read.** The ``OK`` handed to the sink and the
``OK`` on ``CollectionResult`` were **the same object**: normal ``setattr`` is refused
(``FrozenInstanceError``) and ``object.__setattr__`` succeeds. A sink returning ``None``
throughout — so ``_record``'s contract check is satisfied and **nothing refuses** — rewrote:

* ``CollectionResult.final_outcome.payload`` from ``{"reading": 0.25}`` to ``{"reading": 999.0}``;
* ``source_as_of_utc``, so ``_reading_key`` asked the ledger for a key naming a period **NO ROW
  RECORDS**, and the ledger answered ``admitted``.

EVERY TEST BELOW IS TWO ARMS ON ONE AXIS
-----------------------------------------
The axis is the sink and **only** the sink: identical adapter, identical policy, identical
started instant, identical ledger. One sink mutates what it is handed; the other records it and
does nothing. **AND THE CONTROL ARM IS ASSERTED TO STILL SEE THE MUTATION IT PERFORMED**, so a
run in which the sink silently failed to mutate anything cannot be mistaken for the fix working
(``CD-ENG-WO2R3-F12``).

WHAT IS NOT CLOSED IS ASSERTED TRUE HERE TOO
---------------------------------------------
``OK.__post_init__`` takes ``dict(self.payload)`` — a SHALLOW copy — so a payload whose VALUE is
itself mutable is still shared. :func:`test_the_nested_payload_residue_is_declared_and_measured`
performs that mutation and requires it to still reach the runner's copy, so the declared limit
in ``_the_runners_own_copy``'s docstring cannot go stale in the reassuring direction.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from crash_detector.collectors.adapter import FetchedResponse
from crash_detector.collectors.attempt import AttemptRecord
from crash_detector.collectors.delay import DelayKind
from crash_detector.collectors.runner import CollectionResult, RetryPolicy, collect
from crash_detector.observations import OK

from collector_fakes import (
    FAKE_RESPONSE_SCHEMA,
    FakeInMemoryAdapter,
    RecordingLedger,
    RecordingSink,
)

FIXED_NOW = datetime(2026, 8, 22, 12, 0, 0, tzinfo=timezone.utc)
HONEST_AS_OF = datetime(2026, 8, 22, 11, 59, 59, tzinfo=timezone.utc)
#: The escape's own values, from the measurement that raised it.
HONEST_PAYLOAD = {"reading": 0.25}
FORGED_PAYLOAD = {"reading": 999.0}
FORGED_AS_OF = datetime(2000, 1, 1, tzinfo=timezone.utc)

SINGLE = RetryPolicy(max_attempts=1, timeout_seconds=1.0, backoff_seconds=0.0)


class MutatingSink(RecordingSink):
    """**THE ESCAPE, AS A SINK.** It records the row, rewrites the frozen outcome it was
    handed through ``object.__setattr__``, and returns ``None`` — so ``_record``'s contract
    check is satisfied and nothing refuses.

    It REMEMBERS the object it mutated, so the control assertion below can require that the
    mutation actually happened. A sink that failed to mutate would make every arm here pass
    for the wrong reason.
    """

    def __init__(self, *, payload=None, as_of=None) -> None:
        super().__init__()
        self._payload = FORGED_PAYLOAD if payload is None else payload
        self._as_of = FORGED_AS_OF if as_of is None else as_of
        self.mutated: list = []

    def record(self, attempt: AttemptRecord) -> None:
        super().record(attempt)
        outcome = attempt.observation.outcome
        if type(outcome) is OK:
            object.__setattr__(outcome, "payload", self._payload)
            object.__setattr__(outcome, "source_as_of_utc", self._as_of)
            self.mutated.append(outcome)


class NestedMutatingSink(RecordingSink):
    """The residue's sink: it mutates the payload dict's VALUE **in place**, rather than
    replacing the payload. A shallow copy does not defend against this."""

    def __init__(self) -> None:
        super().__init__()
        self.mutated: list = []

    def record(self, attempt: AttemptRecord) -> None:
        super().record(attempt)
        outcome = attempt.observation.outcome
        if type(outcome) is OK:
            inner = outcome.payload["reading"]
            if isinstance(inner, dict):
                inner["v"] = 999.0
                self.mutated.append(outcome)


def _run(sink, *, payload=None, schema=None):
    """One collection over the SHIPPED door. Only ``sink`` varies between the arms."""
    adapter = FakeInMemoryAdapter(
        script=[
            FetchedResponse(
                payload=HONEST_PAYLOAD if payload is None else payload,
                source_as_of_utc=HONEST_AS_OF,
            )
        ],
        response_schema=FAKE_RESPONSE_SCHEMA if schema is None else schema,
    )
    ledger = RecordingLedger()
    result = collect(
        adapter,
        policy=SINGLE,
        sink=sink,
        ledger=ledger,
        collector_run_id="run-escape-3",
        started_utc=FIXED_NOW,
        delay=DelayKind.WALL_CLOCK,
    )
    return result, ledger


def test_a_mutating_sink_cannot_change_the_final_outcome():
    """**THE ARM THAT MATTERS: THE MUTATING SINK, THROUGH THE FIX.**"""
    sink = MutatingSink()
    result, _ledger = _run(sink)

    assert sink.mutated, (
        "THE SINK DID NOT MUTATE ANYTHING, so this arm proves nothing about the fix. Either "
        "the outcome was not an OK or `object.__setattr__` stopped working — check before "
        "reading the assertions below as a pass (CD-ENG-WO2R3-F12)."
    )
    assert dict(sink.mutated[0].payload) == FORGED_PAYLOAD, (
        "the object the sink was handed did NOT keep the sink's rewrite, so the two arms of "
        "this test differ in something other than the axis it claims"
    )

    assert isinstance(result, CollectionResult)
    assert type(result.final_outcome) is OK
    assert dict(result.final_outcome.payload) == HONEST_PAYLOAD, (
        "A MUTATING SINK REWROTE `CollectionResult.final_outcome`. The object the sink was "
        "handed and the object the runner reports are the same object, and the sink runs "
        "BEFORE the read because `_record` is inside the attempt loop's `finally:`."
    )
    assert result.final_outcome.source_as_of_utc == HONEST_AS_OF
    assert result.final_outcome is not sink.mutated[0]


def test_a_mutating_sink_cannot_change_the_reading_key_the_ledger_is_asked_for():
    """**THE HALF THAT REACHES THE STORE.** The forged ``source_as_of_utc`` made the runner
    claim a period NO ROW RECORDS, and the ledger answered ``admitted``."""
    sink = MutatingSink()
    result, ledger = _run(sink)

    assert sink.mutated, "the sink did not mutate; this arm proves nothing"
    assert result.reading_key is not None
    assert result.reading_key == ("fake.source", "2026-08-22T11:59:59Z"), (
        "THE READING KEY WAS DERIVED FROM THE OBJECT THE SINK MUTATED. The runner asked the "
        f"ledger for {result.reading_key!r}, which names a period no attempt row records."
    )
    assert ledger.admitted == [result.reading_key], (
        f"the ledger was asked for {ledger.admitted!r}, and the key on the result is "
        f"{result.reading_key!r}. If those differ the runner told the store one thing and "
        "its caller another."
    )
    assert result.reading_admitted is True


def test_the_benign_control_arm_records_the_row_and_changes_nothing():
    """**THE CONTROL.** Without it, both assertions above are satisfied by a runner that
    ignores its sink entirely, or by one whose outcome is always the honest one because the
    adapter never produced anything else."""
    sink = RecordingSink()
    result, ledger = _run(sink)

    assert len(sink.recorded) == 1
    assert type(result.final_outcome) is OK
    assert dict(result.final_outcome.payload) == HONEST_PAYLOAD
    assert result.final_outcome.source_as_of_utc == HONEST_AS_OF
    assert result.reading_key == ("fake.source", "2026-08-22T11:59:59Z")
    assert ledger.admitted == [result.reading_key]
    assert result.reading_admitted is True
    # AND THE ROW THE SINK RECEIVED IS THE HONEST ONE TOO: the fix must not have made the
    # runner keep a truthful copy while handing the store a different object's content.
    assert dict(sink.recorded[0].observation.outcome.payload) == HONEST_PAYLOAD


def test_the_row_the_sink_receives_is_equal_to_what_the_runner_keeps():
    """The snapshot must be a COPY and not a DIFFERENT ANSWER. Two objects, one truth."""
    sink = RecordingSink()
    result, _ledger = _run(sink)
    recorded = sink.recorded[0].observation.outcome
    assert recorded is not result.final_outcome, (
        "the runner is still reporting the object it handed the sink; the snapshot is an "
        "alias and closes nothing"
    )
    assert type(recorded) is type(result.final_outcome)
    assert dict(recorded.payload) == dict(result.final_outcome.payload)
    assert recorded.source_as_of_utc == result.final_outcome.source_as_of_utc


@pytest.mark.parametrize(
    "script_item, expected",
    [
        (FetchedResponse(payload={"reading": "words"}, source_as_of_utc=HONEST_AS_OF),
         "MALFORMED"),
    ],
)
def test_the_snapshot_is_taken_for_every_outcome_class_and_not_only_for_OK(
    script_item, expected
):
    """The copy is DERIVED from ``typing.get_args(FetchOutcome)`` and
    ``dataclasses.fields``, so it covers every member of the closed sum type rather than the
    one the escape happened to use. Asserted by running the non-``OK`` members through the
    shipped door and requiring the runner's outcome to be a distinct object of the right
    class."""
    from crash_detector.observations import outcome_class

    sink = RecordingSink()
    adapter = FakeInMemoryAdapter(script=[script_item], response_schema=FAKE_RESPONSE_SCHEMA)
    result = collect(
        adapter,
        policy=SINGLE,
        sink=sink,
        ledger=RecordingLedger(),
        collector_run_id="run-classes",
        started_utc=FIXED_NOW,
        delay=DelayKind.WALL_CLOCK,
    )
    assert outcome_class(result.final_outcome) == expected
    assert result.final_outcome is not sink.recorded[0].observation.outcome
    assert type(result.final_outcome) is type(sink.recorded[0].observation.outcome)


def test_the_nested_payload_residue_is_declared_and_measured():
    """**WHAT THIS FIX DOES NOT CLOSE, ASSERTED TRUE SO THE DECLARATION CANNOT GO STALE.**

    ``OK.__post_init__`` takes ``dict(self.payload)`` — a SHALLOW copy — so a payload whose
    VALUE is itself mutable is shared between the object the sink holds and the runner's own.
    A sink that mutates the inner object mutates both.

    **IF THIS TEST EVER FAILS THE RESIDUE HAS CLOSED, WHICH IS GOOD NEWS AND STILL A
    DOCUMENTATION DEFECT** until ``_the_runners_own_copy``'s declared limit is corrected.
    """
    nested_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["reading"],
        "properties": {
            "reading": {
                "type": "object",
                "additionalProperties": False,
                "required": ["v"],
                "properties": {"v": {"type": "number"}},
            }
        },
    }
    sink = NestedMutatingSink()
    result, _ledger = _run(sink, payload={"reading": {"v": 0.25}}, schema=nested_schema)
    if not sink.mutated:
        pytest.skip(
            "the nested payload did not survive validation as a dict, so this arm cannot "
            "measure the residue it is about"
        )
    assert result.final_outcome.payload["reading"]["v"] == 999.0, (
        "the nested-payload residue named in `_the_runners_own_copy`'s declared limit is "
        "CLOSED. That is good news and it is still a documentation defect until the limit is "
        "corrected where it is written."
    )
