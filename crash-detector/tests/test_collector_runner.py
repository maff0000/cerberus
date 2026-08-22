"""The collection runner (BLUEPRINT §5, deliverable A4).

The headline property, and the one tested hardest, is
**EVERY FETCH ATTEMPT WRITES A ROW, INCLUDING THE FAILURES.** A failed fetch that writes
nothing is indistinguishable from a fetch that was never scheduled, and both are
indistinguishable from a source that had nothing to report — three states that demand
different responses, collapsed into one absence.

So the first group below does not test it once with a timeout. It tests it against every
way an attempt can end that the runner knows about, and then against two it does not: an
exception class nobody anticipated, and a ``BaseException`` that is not an ``Exception``
at all.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from crash_detector.collectors.adapter import AdapterFetchError, FetchedResponse
from crash_detector.collectors.attempt import AttemptRecord
from crash_detector.collectors.delay import DelayKind
from crash_detector.collectors.runner import (
    ERROR_ATTEMPT_DID_NOT_COMPLETE,
    ERROR_TIMEOUT,
    ERROR_TIMEOUT_BUDGET_EXCEEDED,
    MALFORMED_ADAPTER_CONTRACT_BREACH,
    MALFORMED_PAYLOAD_NOT_A_JSON_OBJECT,
    MALFORMED_SCHEMA_DECLARATION_INVALID,
    MAX_ATTEMPTS_CEILING,
    MAX_BACKOFF_SECONDS_CEILING,
    MAX_TIMEOUT_SECONDS_CEILING,
    PAYLOAD_SNAPSHOT_MAX_DEPTH,
    CollectionResult,
    RetryPolicy,
    collect,
)
from crash_detector.collectors.validation import SchemaDeclarationInvalid
from crash_detector.observations import OK, Empty, FetchFailed, Malformed

from collector_fakes import (
    ExplodingSink,
    FakeInMemoryAdapter,
    RecordingLedger,
    RecordingSink,
    failing_fetch,
)
from conftest import FIXED_NOW

POLICY = RetryPolicy(max_attempts=3, timeout_seconds=5.0, backoff_seconds=1.0)
SINGLE = RetryPolicy(max_attempts=1, timeout_seconds=5.0, backoff_seconds=0.0)

#: A policy whose per-attempt budget is one millisecond, and an adapter latency an order of
#: magnitude above it. Since §D.3 part 1 the elapsed span is measured by the RUNNER from
#: ``time.monotonic`` — there is no ``clock`` argument to advance — so "this response
#: arrived after its budget" is now demonstrated by an adapter that really is late. The
#: direction is deterministic and not a race: ``time.sleep(s)`` guarantees AT LEAST ``s``,
#: so the observed elapsed span is always above the budget, on any host, under any load.
TINY_BUDGET = RetryPolicy(max_attempts=1, timeout_seconds=0.001, backoff_seconds=0.0)
OVER_BUDGET_LATENCY_SECONDS = 0.05

#: A closed schema that also admits ``{}``, so "the source conformed and had nothing to
#: report" is reachable. Without it EMPTY would be unreachable through the default fake
#: and a test claiming to cover all four outcomes would be covering three.
EMPTY_TOLERANT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {"reading": {"type": "number"}},
}


def _ok_response(seconds_ago: float = 0.0) -> FetchedResponse:
    return FetchedResponse(
        payload={"reading": 1.5},
        source_as_of_utc=FIXED_NOW - timedelta(seconds=seconds_ago),
    )


def _adapter(script, **kwargs):
    """A fake whose schema tolerates ``{}`` unless the test overrides it."""
    kwargs.setdefault("response_schema", EMPTY_TOLERANT_SCHEMA)
    return FakeInMemoryAdapter(script=script, **kwargs)


def _run(adapter, *, policy=SINGLE, sink=None, ledger=None, run_id="run-1"):
    """One collection over the SHIPPED door.

    ``clock`` and ``sleep`` are gone: BP-AMENDMENT-0001 §D.3 part 1 deleted both parameters.
    The run's instant is a VALUE and the waiting is a NAMED KIND, so this helper supplies
    data where it used to supply two callables. Nothing here can decide how long an attempt
    took any more — the runner measures that itself.
    """
    sink = RecordingSink() if sink is None else sink
    ledger = RecordingLedger() if ledger is None else ledger
    result = collect(
        adapter,
        policy=policy,
        sink=sink,
        ledger=ledger,
        collector_run_id=run_id,
        started_utc=FIXED_NOW,
        delay=DelayKind.WALL_CLOCK,
    )
    return result, sink, ledger


# --- EVERY ATTEMPT WRITES A ROW --------------------------------------------------------- #

@pytest.mark.parametrize(
    "script_item,expected_class",
    [
        (_ok_response(), "OK"),
        (AdapterFetchError("CONNECTION_REFUSED"), "FETCH_FAILED"),
        (AdapterFetchError("HTTP_ERROR", 503), "FETCH_FAILED"),
        (TimeoutError("slow"), "FETCH_FAILED"),
        (FetchedResponse(payload={"reading": "words"}, source_as_of_utc=FIXED_NOW),
         "MALFORMED"),
        (FetchedResponse(payload={}, source_as_of_utc=FIXED_NOW), "EMPTY"),
        ({"not": "a FetchedResponse"}, "MALFORMED"),
    ],
)
def test_every_way_an_attempt_can_end_writes_exactly_one_row(script_item, expected_class):
    """Seven endings, one row each, and four DISTINCT outcome classes across them.

    The four outcomes are not three spellings of absence: OK, FETCH_FAILED, MALFORMED and
    EMPTY are recorded as themselves.
    """
    adapter = _adapter([script_item])
    result, sink, _ = _run(adapter)

    assert len(sink.recorded) == 1
    assert sink.outcome_classes == (expected_class,)
    assert result.rows_recorded == 1
    assert result.attempts_made == 1


def test_the_four_outcome_classes_are_all_reachable_and_all_distinct():
    """Guarding the CLASS: the parametrised cases above must not all land on one bucket."""
    seen = set()
    for item in (
        _ok_response(),
        AdapterFetchError("CONNECTION_REFUSED"),
        FetchedResponse(payload={"reading": "words"}, source_as_of_utc=FIXED_NOW),
        FetchedResponse(payload={}, source_as_of_utc=FIXED_NOW),
    ):
        _, sink, _ = _run(_adapter([item]))
        seen.add(sink.outcome_classes[0])
    assert seen == {"OK", "FETCH_FAILED", "MALFORMED", "EMPTY"}


def test_an_unanticipated_exception_still_writes_a_row_and_is_classified_by_type():
    """No bare except, no swallow, and no silence.

    The class carries the exception TYPE and never its message: an exception raised
    inside an HTTP client habitually stringifies the request, and the request carries the
    source credential (PBG-SEC-002).
    """
    class UnanticipatedError(RuntimeError):
        pass

    adapter = FakeInMemoryAdapter(
        script=[UnanticipatedError("SYNTHETIC-MARKER-THAT-MUST-NOT-BE-RECORDED-0000")]
    )
    result, sink, _ = _run(adapter)

    assert sink.outcome_classes == ("FETCH_FAILED",)
    outcome = sink.recorded[0].outcome
    assert isinstance(outcome, FetchFailed)
    assert outcome.error_class == "UNCLASSIFIED_UnanticipatedError"
    assert "SYNTHETIC-MARKER" not in outcome.error_class


def test_a_base_exception_that_is_not_an_exception_still_leaves_the_attempt_recorded():
    """A SIGTERM handler raising SystemExit mid-fetch must not erase the attempt.

    This is the case the pre-set outcome and the ``finally`` exist for. The row says
    ATTEMPT_DID_NOT_COMPLETE, which is a fact; no row at all would have been silence.
    """
    adapter = FakeInMemoryAdapter(script=[KeyboardInterrupt()])
    sink = RecordingSink()
    with pytest.raises(KeyboardInterrupt):
        collect(
            adapter,
            policy=SINGLE,
            sink=sink,
            ledger=RecordingLedger(),
            collector_run_id="run-sigterm",
            started_utc=FIXED_NOW,
            delay=DelayKind.WALL_CLOCK,
        )
    assert len(sink.recorded) == 1
    outcome = sink.recorded[0].outcome
    assert isinstance(outcome, FetchFailed)
    assert outcome.error_class == ERROR_ATTEMPT_DID_NOT_COMPLETE


def test_a_sink_that_cannot_write_raises_rather_than_losing_the_attempt_quietly():
    """"We did not record it" must never become "it did not happen"."""
    with pytest.raises(OSError):
        collect(
            FakeInMemoryAdapter(script=[_ok_response()]),
            policy=SINGLE,
            sink=ExplodingSink(),
            ledger=RecordingLedger(),
            collector_run_id="run-nosink",
            started_utc=FIXED_NOW,
            delay=DelayKind.WALL_CLOCK,
        )


def test_every_retry_appends_its_own_row():
    """A retry adds an observation row. Three attempts, three rows, numbered 1..3."""
    adapter = FakeInMemoryAdapter(
        script=[failing_fetch(), failing_fetch(), failing_fetch()]
    )
    result, sink, _ = _run(adapter, policy=POLICY)

    assert result.attempts_made == 3
    assert result.rows_recorded == 3
    assert sink.attempt_numbers == (1, 2, 3)
    assert sink.outcome_classes == ("FETCH_FAILED",) * 3


def test_the_result_refuses_to_report_fewer_rows_than_attempts():
    """A defensive invariant on the result type itself, not a tolerance.

    If a future edit drops a record call, this is what says so rather than a test that
    happened to count rows.
    """
    with pytest.raises(AssertionError):
        CollectionResult(
            source_id="src.a",
            adapter_id="a.v0",
            collector_run_id="run",
            attempts_made=3,
            rows_recorded=2,
            final_outcome=Empty(),
            reading_key=None,
            reading_admitted=False,
            delays_applied=(),
        )


# --- BOUNDED RETRIES -------------------------------------------------------------------- #

def test_retries_stop_at_max_attempts():
    """The same proposition as before §D.3, read off the RUNNER instead of off a double.

    ``sleep`` was a caller-supplied callable and this test asserted on ITS log — the
    system's behaviour attested by the caller's own object. ``delays_applied`` is the
    runner's own record of what it waited for. The backoff is a real ``time.sleep`` on the
    wall clock, 1 ms four times, because the delay that ships is the delay measured: there
    is deliberately no ``DelayKind`` member meaning "do not actually wait".
    """
    adapter = FakeInMemoryAdapter(script=[failing_fetch()] * MAX_ATTEMPTS_CEILING)
    policy = RetryPolicy(
        max_attempts=MAX_ATTEMPTS_CEILING, timeout_seconds=1.0, backoff_seconds=0.001
    )
    result, sink, _ = _run(adapter, policy=policy)

    assert result.attempts_made == MAX_ATTEMPTS_CEILING
    assert adapter.calls == MAX_ATTEMPTS_CEILING
    # Backoff between attempts, never after the last one.
    assert result.delays_applied == (0.001,) * (MAX_ATTEMPTS_CEILING - 1)


@pytest.mark.parametrize(
    "item",
    [
        FetchedResponse(payload={"reading": "words"}, source_as_of_utc=FIXED_NOW),
        FetchedResponse(payload={}, source_as_of_utc=FIXED_NOW),
        _ok_response(),
    ],
)
def test_only_fetch_failed_is_retried(item):
    """MALFORMED and EMPTY are ANSWERS.

    Asking the same question again in two seconds is not a strategy; retrying a source
    that changed its shape is a source that is also hammered.
    """
    adapter = _adapter([item, item, item])
    result, sink, _ = _run(adapter, policy=POLICY)

    assert result.attempts_made == 1
    assert adapter.calls == 1
    assert result.delays_applied == ()


def test_a_recovered_fetch_stops_retrying_and_keeps_the_failure_rows():
    adapter = FakeInMemoryAdapter(script=[failing_fetch(), _ok_response()])
    result, sink, ledger = _run(adapter, policy=POLICY)

    assert result.attempts_made == 2
    assert sink.outcome_classes == ("FETCH_FAILED", "OK")
    assert isinstance(result.final_outcome, OK)
    assert ledger.admitted == [result.reading_key]


# --- BOUNDED TIMEOUTS ------------------------------------------------------------------- #

def test_the_declared_timeout_reaches_the_adapter():
    adapter = FakeInMemoryAdapter(script=[_ok_response()])
    _run(adapter)
    assert adapter.timeouts_seen == [SINGLE.timeout_seconds]


def test_a_response_that_arrives_after_its_budget_is_refused_even_when_it_is_good():
    """An adapter that ignores its timeout cannot deliver a value, only a recorded failure.

    ``fetch`` is synchronous, so the runner cannot interrupt it; it can only refuse to
    honour what eventually comes back. Under CD-AC-001 the safe direction is the recorded
    absence: a dial that reads UNKNOWN for one cycle costs less than an adapter whose
    declared timeout means nothing.
    """
    adapter = FakeInMemoryAdapter(
        script=[_ok_response()], latency_seconds=OVER_BUDGET_LATENCY_SECONDS
    )
    result, sink, ledger = _run(adapter, policy=TINY_BUDGET)

    assert sink.outcome_classes == ("FETCH_FAILED",)
    assert result.final_outcome.error_class == ERROR_TIMEOUT_BUDGET_EXCEEDED
    assert ledger.admitted == []


def test_a_timeout_error_from_the_adapter_is_classified_as_a_timeout():
    adapter = FakeInMemoryAdapter(script=[TimeoutError("slow")])
    result, _, _ = _run(adapter)
    assert result.final_outcome.error_class == ERROR_TIMEOUT


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_attempts": 0, "timeout_seconds": 1.0, "backoff_seconds": 0.0},
        {"max_attempts": MAX_ATTEMPTS_CEILING + 1, "timeout_seconds": 1.0,
         "backoff_seconds": 0.0},
        {"max_attempts": 1, "timeout_seconds": 0.0, "backoff_seconds": 0.0},
        {"max_attempts": 1, "timeout_seconds": -1.0, "backoff_seconds": 0.0},
        {"max_attempts": 1, "timeout_seconds": float("inf"), "backoff_seconds": 0.0},
        {"max_attempts": 1, "timeout_seconds": float("nan"), "backoff_seconds": 0.0},
        {"max_attempts": 1, "timeout_seconds": MAX_TIMEOUT_SECONDS_CEILING + 1.0,
         "backoff_seconds": 0.0},
        {"max_attempts": 1, "timeout_seconds": 1.0,
         "backoff_seconds": MAX_BACKOFF_SECONDS_CEILING + 1.0},
        {"max_attempts": 1, "timeout_seconds": 1.0, "backoff_seconds": float("inf")},
        {"max_attempts": 1, "timeout_seconds": 1.0, "backoff_seconds": -1.0},
    ],
)
def test_an_unbounded_or_absurd_policy_is_refused_at_construction(kwargs):
    """An unbounded wait is an outage with extra steps (Standards Baseline §11)."""
    with pytest.raises((ValueError, TypeError)):
        RetryPolicy(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_attempts": True, "timeout_seconds": 1.0, "backoff_seconds": 0.0},
        {"max_attempts": 1, "timeout_seconds": 1, "backoff_seconds": 0.0},
        {"max_attempts": 1, "timeout_seconds": 1.0, "backoff_seconds": True},
    ],
)
def test_a_policy_field_of_the_wrong_type_is_refused(kwargs):
    with pytest.raises(TypeError):
        RetryPolicy(**kwargs)


def test_the_policy_states_its_own_worst_case():
    policy = RetryPolicy(max_attempts=3, timeout_seconds=5.0, backoff_seconds=1.0)
    assert policy.worst_case_seconds == 3 * 5.0 + 2 * 1.0


# --- VALIDATION AT THE BOUNDARY --------------------------------------------------------- #

def test_a_non_conforming_response_is_malformed_with_its_class_and_location():
    adapter = FakeInMemoryAdapter(
        script=[FetchedResponse(payload={"reading": "words"},
                                source_as_of_utc=FIXED_NOW)]
    )
    result, sink, _ = _run(adapter)
    outcome = result.final_outcome
    assert isinstance(outcome, Malformed)
    assert outcome.schema_error_class == "JSONSCHEMA_TYPE"
    assert outcome.instance_path == "/reading"


def test_a_malformed_response_is_never_coerced_into_a_reading():
    """Not coerced, not partially accepted, and not admitted to the ledger."""
    adapter = FakeInMemoryAdapter(
        script=[FetchedResponse(payload={"reading": "1.5"}, source_as_of_utc=FIXED_NOW)]
    )
    result, _, ledger = _run(adapter)
    assert isinstance(result.final_outcome, Malformed)
    assert result.reading_key is None
    assert ledger.admitted == []


def test_an_unknown_key_in_a_response_is_malformed_because_the_schema_is_closed():
    adapter = FakeInMemoryAdapter(
        script=[
            FetchedResponse(
                payload={"reading": 1.0, "surprise": 2.0}, source_as_of_utc=FIXED_NOW
            )
        ]
    )
    result, _, _ = _run(adapter)
    assert isinstance(result.final_outcome, Malformed)
    assert result.final_outcome.schema_error_class == "JSONSCHEMA_ADDITIONALPROPERTIES"


def test_our_broken_schema_is_recorded_and_then_raised_rather_than_blamed_on_the_source():
    """Two obligations that are not in tension: the row exists, and the defect is loud.

    Recording it as MALFORMED and saying nothing else would blame the source for our bug,
    and *cannot determine* is not *determined to be absent* (Standards Baseline §8).
    """
    adapter = FakeInMemoryAdapter(
        script=[_ok_response()], response_schema={"type": "not-a-json-schema-type"}
    )
    sink = RecordingSink()
    with pytest.raises(SchemaDeclarationInvalid):
        collect(
            adapter,
            policy=POLICY,
            sink=sink,
            ledger=RecordingLedger(),
            collector_run_id="run-badschema",
            started_utc=FIXED_NOW,
            delay=DelayKind.WALL_CLOCK,
        )
    assert len(sink.recorded) == 1
    outcome = sink.recorded[0].outcome
    assert isinstance(outcome, Malformed)
    assert outcome.schema_error_class == MALFORMED_SCHEMA_DECLARATION_INVALID


def test_a_declared_schema_with_a_remote_ref_is_refused_without_fetching_it():
    """Resolving a remote $ref is an outbound network request inside a validation step.

    Nothing in this increment may reach the network. The refusal is a schema-declaration
    defect, so it is raised rather than recorded against the source.
    """
    adapter = FakeInMemoryAdapter(
        script=[_ok_response()],
        response_schema={"$ref": "https://example.invalid/schema.json"},
    )
    with pytest.raises(SchemaDeclarationInvalid) as caught:
        collect(
            adapter,
            policy=SINGLE,
            sink=RecordingSink(),
            ledger=RecordingLedger(),
            collector_run_id="run-remoteref",
            started_utc=FIXED_NOW,
            delay=DelayKind.WALL_CLOCK,
        )
    assert caught.value.error_class == "SCHEMA_REMOTE_REF_FORBIDDEN"


def test_an_adapter_returning_the_wrong_type_breaches_its_contract():
    adapter = FakeInMemoryAdapter(script=[{"reading": 1.0}])
    result, _, _ = _run(adapter)
    assert isinstance(result.final_outcome, Malformed)
    assert result.final_outcome.schema_error_class == MALFORMED_ADAPTER_CONTRACT_BREACH


def test_a_conforming_payload_that_is_not_a_json_object_is_refused_not_wrapped():
    """Wrapping would invent a key name, and an invented key is a shape nobody agreed to."""
    adapter = FakeInMemoryAdapter(
        script=[FetchedResponse(payload=[1, 2, 3], source_as_of_utc=FIXED_NOW)],
        response_schema={"type": "array"},
        is_empty_fn=lambda payload: False,
    )
    result, _, _ = _run(adapter)
    assert isinstance(result.final_outcome, Malformed)
    assert (
        result.final_outcome.schema_error_class == MALFORMED_PAYLOAD_NOT_A_JSON_OBJECT
    )


def test_a_non_boolean_answer_to_is_empty_is_a_contract_breach():
    """A truthy string would make "is it empty" answer yes by accident."""
    adapter = FakeInMemoryAdapter(
        script=[_ok_response()], is_empty_fn=lambda payload: "yes"  # type: ignore[return-value]
    )
    result, _, _ = _run(adapter)
    assert isinstance(result.final_outcome, Malformed)
    assert result.final_outcome.schema_error_class == MALFORMED_ADAPTER_CONTRACT_BREACH


def test_an_exploding_is_empty_does_not_become_a_reading():
    adapter = FakeInMemoryAdapter(
        script=[_ok_response()],
        is_empty_fn=lambda payload: (_ for _ in ()).throw(ValueError("boom")),
    )
    result, _, ledger = _run(adapter)
    assert isinstance(result.final_outcome, Malformed)
    assert result.final_outcome.schema_error_class.startswith("EMPTINESS_UNDECIDABLE_")
    assert ledger.admitted == []


# --- IDEMPOTENCY ------------------------------------------------------------------------ #

def test_a_refetch_of_the_same_period_adds_a_row_but_not_a_second_reading():
    """BLUEPRINT §5, exactly: "a retry adds an observation row, never a duplicate reading".

    The A5 SQL must mirror both halves: raw.observation append-only with NO unique
    constraint, and the reading UNIQUE on (source_id, source_as_of_utc).
    """
    ledger = RecordingLedger()
    sink = RecordingSink()
    period = FIXED_NOW - timedelta(minutes=5)
    results = []

    for run_id in ("run-a", "run-b"):
        results.append(
            collect(
                FakeInMemoryAdapter(
                    script=[FetchedResponse(payload={"reading": 1.5},
                                            source_as_of_utc=period)]
                ),
                policy=SINGLE,
                sink=sink,
                ledger=ledger,
                collector_run_id=run_id,
                started_utc=FIXED_NOW,
                delay=DelayKind.WALL_CLOCK,
            )
        )

    assert len(sink.recorded) == 2
    assert len(ledger.admitted) == 1
    assert len(ledger.rejected) == 1
    assert ledger.admitted[0] == ("fake.source", "2026-08-19T11:55:00Z")

    # The RUNNER's own answer, not only the fake's bookkeeping. Asserting on the ledger
    # alone would leave a runner that ignores the ledger's verdict entirely and reports
    # every re-fetch as a fresh reading — which is what this pair of assertions caught
    # when the idempotency branch was mutated away.
    assert [result.reading_key for result in results] == [
        ("fake.source", "2026-08-19T11:55:00Z")
    ] * 2
    assert [result.reading_admitted for result in results] == [True, False]


def test_the_idempotency_key_is_the_source_period_not_the_fetch_instant():
    period = FIXED_NOW - timedelta(hours=2)
    adapter = FakeInMemoryAdapter(
        script=[FetchedResponse(payload={"reading": 1.5}, source_as_of_utc=period)]
    )
    result, _, _ = _run(adapter)
    assert result.reading_key == ("fake.source", "2026-08-19T10:00:00Z")


def test_two_different_periods_are_two_readings():
    ledger = RecordingLedger()
    admitted = []
    for minutes in (5, 10):
        admitted.append(collect(
            FakeInMemoryAdapter(
                script=[
                    FetchedResponse(
                        payload={"reading": 1.5},
                        source_as_of_utc=FIXED_NOW - timedelta(minutes=minutes),
                    )
                ]
            ),
            policy=SINGLE,
            sink=RecordingSink(),
            ledger=ledger,
            collector_run_id=f"run-{minutes}",
            started_utc=FIXED_NOW,
            delay=DelayKind.WALL_CLOCK,
        ).reading_admitted)
    assert len(ledger.admitted) == 2
    assert ledger.rejected == []
    assert admitted == [True, True]


def test_the_same_instant_in_a_different_offset_is_the_same_reading():
    """The key is normalised to canonical UTC before it becomes a dictionary key.

    Two datetimes that denote the same instant in different offsets are equal in Python
    and are the same row in the store, but are not the same dict key. Normalising once
    means the in-memory ledger and the UNIQUE constraint agree about "the same".
    """
    plus_two = timezone(timedelta(hours=2))
    ledger = RecordingLedger()
    results = []
    for as_of in (
        datetime(2026, 8, 19, 10, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 8, 19, 12, 0, 0, tzinfo=plus_two),
    ):
        results.append(
            collect(
                FakeInMemoryAdapter(
                    script=[
                        FetchedResponse(payload={"reading": 1.5}, source_as_of_utc=as_of)
                    ]
                ),
                policy=SINGLE,
                sink=RecordingSink(),
                ledger=ledger,
                collector_run_id="run-offset",
                started_utc=FIXED_NOW,
                delay=DelayKind.WALL_CLOCK,
            )
        )
    assert len(ledger.admitted) == 1
    assert len(ledger.rejected) == 1
    assert len({result.reading_key for result in results}) == 1
    assert [result.reading_admitted for result in results] == [True, False]


@pytest.mark.parametrize(
    "item",
    [
        AdapterFetchError("CONNECTION_REFUSED"),
        FetchedResponse(payload={"reading": "words"}, source_as_of_utc=FIXED_NOW),
        FetchedResponse(payload={}, source_as_of_utc=FIXED_NOW),
    ],
)
def test_a_failure_has_no_source_period_and_claims_no_reading(item):
    """Inventing a period for a failure would make every failure a reading of nothing."""
    adapter = _adapter([item])
    result, _, ledger = _run(adapter)
    assert result.reading_key is None
    assert result.reading_admitted is False
    assert ledger.admitted == []


# --- THE ATTEMPT ROW ---------------------------------------------------------------------- #

def test_the_attempt_row_carries_the_collector_provenance_the_engine_does_not_read():
    adapter = FakeInMemoryAdapter(script=[_ok_response()])
    _, sink, _ = _run(adapter, run_id="run-provenance")
    attempt = sink.recorded[0]

    assert attempt.adapter_id == "fake.adapter.v0"
    assert attempt.collector_run_id == "run-provenance"
    assert attempt.attempt_number == 1
    assert attempt.source_id == "fake.source"
    assert attempt.outcome_class == "OK"
    assert attempt.elapsed_seconds >= 0.0
    assert attempt.completed_utc >= attempt.requested_utc


def test_an_attempt_that_finished_before_it_started_is_refused():
    """A row that says otherwise makes every latency figure derived from it wrong."""
    from crash_detector.observations import ObservationRecord

    with pytest.raises(ValueError):
        AttemptRecord(
            observation=ObservationRecord(
                source_id="src.a",
                observed_utc=FIXED_NOW - timedelta(seconds=1),
                outcome=Empty(),
            ),
            adapter_id="a.v0",
            collector_run_id="run",
            attempt_number=1,
            requested_utc=FIXED_NOW,
        )


@pytest.mark.parametrize("attempt_number", [0, -1])
def test_attempt_numbering_starts_at_one(attempt_number):
    from crash_detector.observations import ObservationRecord

    with pytest.raises(ValueError):
        AttemptRecord(
            observation=ObservationRecord(
                source_id="src.a", observed_utc=FIXED_NOW, outcome=Empty()
            ),
            adapter_id="a.v0",
            collector_run_id="run",
            attempt_number=attempt_number,
            requested_utc=FIXED_NOW,
        )


def test_collect_refuses_an_unnamed_run():
    with pytest.raises(ValueError):
        collect(
            FakeInMemoryAdapter(script=[_ok_response()]),
            policy=SINGLE,
            sink=RecordingSink(),
            ledger=RecordingLedger(),
            collector_run_id="",
            started_utc=FIXED_NOW,
            delay=DelayKind.WALL_CLOCK,
        )


def test_collect_takes_no_clock_and_no_sleep_and_defaults_neither_instant_nor_delay():
    """REPLACES ``test_collect_has_no_default_clock_and_no_default_sleep`` (deleted subject).

    THE OLD PROPOSITION: ``clock`` and ``sleep`` are required injections, so no module-level
    ``now()`` and no real delay can hide inside ``collect``.

    THE SAME PROPOSITION AGAINST THE NEW STRUCTURE, AND IT IS STRICTLY STRONGER. The old
    test asked whether two CALLABLE parameters had defaults; the parameters are gone. What
    is asserted now is that there is **no parameter of ``collect`` through which a callable
    can arrive at all** — not that the two named ones are mandatory — and that the two
    values which replaced them are themselves mandatory. CHECKED ON THE SIGNATURE, so a
    rewrite of the body cannot restore either.
    """
    import inspect

    signature = inspect.signature(collect)
    assert "clock" not in signature.parameters
    assert "sleep" not in signature.parameters
    for name in ("started_utc", "delay"):
        assert signature.parameters[name].default is inspect.Parameter.empty
    # THE CLASS, not the two names: no parameter of this door may be supplied a callable
    # and be believed about it. `admits` refuses anything but the declared exact type, and
    # the four that are NOT exact-typed are the declared CD-BP-003 protocol boundary.
    from crash_detector.admission import declared_admissions

    declared = declared_admissions(collect)
    assert set(declared) == set(signature.parameters)
    exempt = {
        name
        for name, admission in declared.items()
        if "ANY VALUE" in admission.describe()
    }
    assert exempt == {"adapter", "sink", "ledger", "validator"}, (
        "the set of parameters this door does NOT exact-type is CD-BP-003 and it is "
        "pinned here: a fifth one is a widening of the declared limit, not a detail"
    )


# --- ESCAPE 1: THE STORED PAYLOAD IS THE VALIDATED PAYLOAD (WO-2R3 increment 6) ---------- #
#
# THE DEFECT THESE CARRY. `validator.validate(p)` judged an object, `adapter.is_empty(p)`
# was handed THE SAME object, and `OK(payload=p)` stored THE SAME object. `is_empty` is
# DECLARED-FOREIGN CODE under CD-BP-003. An adapter that rewrote the mapping it was handed
# and then honestly answered `False` had the rewritten mapping stored under a verdict earned
# by the original — `CD-ASR-WO2R3-01`, ESCAPE 1, the correctness defect that moved the
# WO-2R3 gate to RED.
#
# WHY `OK.__post_init__`'s EXISTING `dict(self.payload)` DID NOT CARRY THIS, which is why
# six increments of readers were satisfied: it copies AFTER the foreign call, so it copies
# the mutation faithfully.
#
# THE LIMIT THESE DO **NOT** CARRY IS TESTED TOO, in
# `test_the_snapshot_does_not_reach_a_container_that_is_not_exactly_a_dict`. A residue that
# only appears in prose is a residue nobody re-measures.

def _hostile_is_empty(mutation):
    """An `is_empty` that mutates the object it is handed and answers honestly.

    It answers `False`, so the runner proceeds to `OK` — the mutation is the whole attack
    and a truthful emptiness verdict is what makes it reach storage.
    """

    def is_empty(payload):
        mutation(payload)
        return False

    return is_empty


def test_a_hostile_is_empty_cannot_change_the_stored_payload():
    """ESCAPE 1, the auditor's own reproduction, as a carrier.

    At `531c95c` this stored `{'reading': inf, 'not_in_schema': ...}` — a payload that fails
    the schema it was judged by, under an `OK` whose verdict was earned by `{'reading': 1.5}`.
    """
    def mutate(payload):
        payload["reading"] = float("inf")
        payload["not_in_schema"] = "\x00\x00\x00"

    adapter = _adapter([_ok_response()], is_empty_fn=_hostile_is_empty(mutate))
    result, _, _ = _run(adapter)

    assert isinstance(result.final_outcome, OK)
    assert result.final_outcome.payload == {"reading": 1.5}, (
        "the stored payload must be the payload the validator judged; an adapter's "
        "is_empty must not be able to reach it"
    )
    assert "not_in_schema" not in result.final_outcome.payload


def test_the_object_is_empty_is_handed_is_not_the_adapters_own_object():
    """THE STRUCTURAL PROPERTY, not one mutation of it.

    The previous test names one attack. This names the property that defeats every attack of
    that class: the foreign call is not handed a live reference to the object the adapter
    still holds.

    **IT IS ASSERTED AGAINST THE ADAPTER'S OBJECT AND NOT AGAINST THE STORED ONE, AND THAT
    IS THE POINT.** `OK.__post_init__` has always done `dict(self.payload)`, so
    `id(is_empty's argument) != id(OK.payload)` was ALREADY TRUE at `531c95c` with the defect
    fully present. A test asserting THAT would pass in both arms and carry nothing. This seat
    wrote it that way first, ran it against a tree with the snapshot reverted, found it
    GREEN, and rewrote it — recorded here because a carrier nobody tried to break is a
    carrier nobody has measured.
    """
    payload = {"reading": 1.5}
    seen: list[int] = []
    adapter = FakeInMemoryAdapter(
        script=[FetchedResponse(payload=payload, source_as_of_utc=FIXED_NOW)],
        response_schema=EMPTY_TOLERANT_SCHEMA,
        is_empty_fn=_hostile_is_empty(lambda handed: seen.append(id(handed))),
    )
    result, _, _ = _run(adapter)

    assert isinstance(result.final_outcome, OK)
    assert len(seen) == 1
    assert seen[0] != id(payload), (
        "is_empty must not be handed the object the adapter still holds a reference to"
    )
    assert id(result.final_outcome.payload) != id(payload)


def test_a_hostile_is_empty_cannot_change_a_nested_plain_dict_either():
    """THE REACH AXIS THE FIX DOES CLOSE — nesting, for exactly-typed containers.

    A shallow copy would pass the two tests above and fail this one. That is the whole
    reason this one exists: `dict(payload)` is not a snapshot, it is a snapshot of the top
    row.
    """
    nested_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["reading", "nested"],
        "properties": {
            "reading": {"type": "number"},
            "nested": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"reading": {"type": "number"}},
            },
        },
    }
    response = FetchedResponse(
        payload={"reading": 1.5, "nested": {"reading": 1.5}},
        source_as_of_utc=FIXED_NOW,
    )
    adapter = FakeInMemoryAdapter(
        script=[response],
        response_schema=nested_schema,
        is_empty_fn=_hostile_is_empty(
            lambda payload: payload["nested"].__setitem__("reading", float("inf"))
        ),
    )
    result, _, _ = _run(adapter)

    assert isinstance(result.final_outcome, OK)
    assert result.final_outcome.payload["nested"]["reading"] == 1.5


def test_the_snapshot_does_not_reach_a_container_that_is_not_exactly_a_dict():
    """**THE DECLARED LIMIT, ASSERTED RATHER THAN WRITTEN DOWN.**

    `_payload_snapshot` rebuilds `dict`, `list` and `tuple` BY EXACT TYPE. A `dict`
    SUBCLASS is carried BY REFERENCE and an adapter can still rewrite its interior. That is
    DECLARED LIMIT 5 in `collect`'s header and it is stated in `required-tests.yaml` and in
    `contracts/execution/CD-RT-002-DOORS-REQUIRE-THEIR-TYPES.md`.

    **THIS TEST ASSERTS THE LIMIT IS STILL EXACTLY THAT WIDE.** It passes today because the
    escape works. If a later increment widens the snapshot, this test FAILS — and that
    failure is the signal to go and correct the three declarations, not to delete the test.
    A limit whose wording is the only thing holding it is a limit that goes stale, and this
    project has now been bitten by that three times (`CD-PL-F91`, item C's stale count, and
    the sentence DECLARED LIMIT 5 supersedes).
    """
    class _Sub(dict):
        pass

    nested_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["reading", "nested"],
        "properties": {
            "reading": {"type": "number"},
            "nested": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"reading": {"type": "number"}},
            },
        },
    }
    response = FetchedResponse(
        payload={"reading": 1.5, "nested": _Sub({"reading": 1.5})},
        source_as_of_utc=FIXED_NOW,
    )
    adapter = FakeInMemoryAdapter(
        script=[response],
        response_schema=nested_schema,
        is_empty_fn=_hostile_is_empty(
            lambda payload: payload["nested"].__setitem__("reading", float("inf"))
        ),
    )
    result, _, _ = _run(adapter)

    assert isinstance(result.final_outcome, OK)
    assert result.final_outcome.payload["nested"]["reading"] == float("inf"), (
        "DECLARED LIMIT 5 says a dict SUBCLASS is carried by reference. If this assertion "
        "fails the limit is now NARROWER than declared: correct all three CD-RULE-004 "
        "places, and do not delete this test"
    )


def test_the_snapshot_depth_is_a_declared_number_and_the_residue_below_it_is_real():
    """The second half of DECLARED LIMIT 5, and the number that decides it.

    Nesting is rebuilt to `PAYLOAD_SNAPSHOT_MAX_DEPTH` levels and carried by reference
    below that. Asserted from BOTH sides of the boundary in ONE test, so neither the number
    nor the behaviour can drift without the other being noticed.
    """
    def _nest(levels: int) -> dict:
        deep: dict = {"reading": 1.5}
        for _ in range(levels):
            deep = {"nested": deep}
        return deep

    def _innermost(value):
        while isinstance(value, dict) and "nested" in value:
            value = value["nested"]
        return value

    def _mutate(payload):
        _innermost(payload)["reading"] = float("inf")

    schema = {"type": "object", "properties": {"reading": {"type": "number"}}}

    within = FetchedResponse(payload=_nest(PAYLOAD_SNAPSHOT_MAX_DEPTH - 2),
                             source_as_of_utc=FIXED_NOW)
    result, _, _ = _run(
        FakeInMemoryAdapter(script=[within], response_schema=schema,
                            is_empty_fn=_hostile_is_empty(_mutate))
    )
    assert isinstance(result.final_outcome, OK)
    assert _innermost(result.final_outcome.payload)["reading"] == 1.5, (
        "within the declared depth the rebuild must hold"
    )

    beyond = FetchedResponse(payload=_nest(PAYLOAD_SNAPSHOT_MAX_DEPTH + 5),
                             source_as_of_utc=FIXED_NOW)
    result, _, _ = _run(
        FakeInMemoryAdapter(script=[beyond], response_schema=schema,
                            is_empty_fn=_hostile_is_empty(_mutate))
    )
    assert isinstance(result.final_outcome, OK)
    assert _innermost(result.final_outcome.payload)["reading"] == float("inf"), (
        "below the declared depth the payload is carried by reference; if this fails the "
        "declared limit is now wrong in the SAFE direction and must still be corrected"
    )


def test_the_validator_is_still_handed_the_adapters_live_object():
    """**WHAT ITEM A DOES NOT CLOSE, ASSERTED SO IT CANNOT BE QUIETLY BELIEVED CLOSED.**

    The snapshot is taken AFTER validation, so the OTHER declared-foreign protocol at this
    door — `validator` — still receives the adapter's live object. A hostile validator that
    mutates while judging defeats the escape-1 closure completely. That route is NOT this
    increment's (the sink/ledger/validator behaviour table is unverified by anyone and
    travels to the fifth Assurance seat), and it is asserted here rather than merely
    admitted in a docstring.
    """
    seen: list[int] = []

    class _RecordingValidator:
        def validate(self, payload, schema):
            seen.append(id(payload))
            return None

    payload = {"reading": 1.5}
    response = FetchedResponse(payload=payload, source_as_of_utc=FIXED_NOW)
    sink = RecordingSink()
    ledger = RecordingLedger()
    collect(
        FakeInMemoryAdapter(script=[response], response_schema=EMPTY_TOLERANT_SCHEMA),
        policy=SINGLE,
        sink=sink,
        ledger=ledger,
        collector_run_id="run-1",
        started_utc=FIXED_NOW,
        delay=DelayKind.WALL_CLOCK,
        validator=_RecordingValidator(),
    )

    assert seen == [id(payload)], (
        "the validator receives the adapter's live payload: this is DECLARED LIMIT 5's "
        "third residue and it is NOT closed by the snapshot"
    )
