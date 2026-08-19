"""The collection runner — bounded, and it always writes the row (BLUEPRINT §5).

Guarantees, in the order of how much they matter:

1. **Every fetch attempt writes exactly one attempt row**, whatever happens: success,
   timeout, malformed response, a broken declared schema, or an exception nobody
   anticipated. The write is in a ``finally``, so even a ``BaseException`` —
   ``KeyboardInterrupt``, ``SystemExit``, the container's ``SIGTERM`` handler — leaves the
   attempt recorded before it propagates.
2. **Bounded timeouts and bounded retries.** :class:`RetryPolicy` refuses an unbounded or
   unvalidated configuration at construction, and the runner independently measures the
   elapsed time so an adapter that ignores its budget cannot deliver a value.
3. **Validation once, at the boundary**, against the adapter's declared schema. A
   non-conforming response becomes ``MALFORMED`` with its error class and its location,
   and is never coerced. Nothing value-bearing from the response is retained.
4. **Idempotency on** ``(source_id, source_as_of_utc)`` for readings, while every attempt
   still appends an observation row.

**Retries apply to** ``FETCH_FAILED`` **only.** ``MALFORMED`` and ``EMPTY`` are answers.
Asking the same question again in two seconds is not a strategy, it is a way to multiply
rows without learning anything — and retrying a malformed response is how a source that
changed its shape becomes a source that is also hammered.

Nothing in this module computes a dial value, and nothing in it may. It imports neither
:mod:`crash_detector.dials` nor :mod:`crash_detector.engine`, and a test asserts that no
module in this package does. The collector containers additionally hold no grant on
``dial.*`` (deliverable A5), so the rule is enforced by permission as well as by
construction.

----

ON THE ELAPSED-TIME CHECK.

``fetch`` is synchronous, so the runner cannot interrupt an adapter that blocks past its
budget; it can only refuse to honour what that adapter eventually returns. It does. A
response whose round trip exceeded ``timeout_seconds`` is recorded as
``FETCH_FAILED(TIMEOUT_BUDGET_EXCEEDED)`` even when the payload is perfectly good.

That direction is deliberate. Under CD-AC-001 the cost of discarding a late-but-valid
response is a dial that reads ``Unknown`` for one cycle; the cost of accepting it is an
adapter whose declared timeout means nothing, which is an unbounded wait wearing a number.
The safe failure is the recorded absence.
"""

from __future__ import annotations

import math
from collections.abc import Mapping as AbcMapping
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Union

from crash_detector.collectors.adapter import (
    AdapterFetchError,
    FetchedResponse,
    SourceAdapter,
)
from crash_detector.collectors.attempt import (
    AttemptRecord,
    ObservationSink,
    ReadingKey,
    ReadingLedger,
)
from crash_detector.collectors.validation import (
    JsonSchemaValidator,
    PayloadValidator,
    SchemaDeclarationInvalid,
    SchemaRejection,
)
from crash_detector.observations import (
    OK,
    Empty,
    FetchFailed,
    FetchOutcome,
    Malformed,
    ObservationRecord,
)
from crash_detector.time_utc import ensure_utc

__all__ = [
    "RetryPolicy",
    "CollectionResult",
    "collect",
    "MAX_ATTEMPTS_CEILING",
    "MAX_TIMEOUT_SECONDS_CEILING",
    "MAX_BACKOFF_SECONDS_CEILING",
    "ERROR_ATTEMPT_DID_NOT_COMPLETE",
    "ERROR_TIMEOUT_BUDGET_EXCEEDED",
    "ERROR_TIMEOUT",
    "MALFORMED_ADAPTER_CONTRACT_BREACH",
    "MALFORMED_PAYLOAD_NOT_A_JSON_OBJECT",
    "MALFORMED_SCHEMA_DECLARATION_INVALID",
]

#: Hard ceilings, enforced at construction. A policy outside these is refused rather than
#: honoured: a retry loop nobody bounded is an outage generator, and a ten-minute
#: per-attempt timeout is an unbounded wait wearing a number (Standards Baseline §11).
MAX_ATTEMPTS_CEILING = 5
MAX_TIMEOUT_SECONDS_CEILING = 60.0
MAX_BACKOFF_SECONDS_CEILING = 30.0

# Stable failure classifications. Named constants rather than literals so a guard can
# assert on the class rather than on a string somebody retyped.
ERROR_ATTEMPT_DID_NOT_COMPLETE = "ATTEMPT_DID_NOT_COMPLETE"
ERROR_TIMEOUT_BUDGET_EXCEEDED = "TIMEOUT_BUDGET_EXCEEDED"
ERROR_TIMEOUT = "TIMEOUT"
_ERROR_UNCLASSIFIED_PREFIX = "UNCLASSIFIED_"

MALFORMED_ADAPTER_CONTRACT_BREACH = "ADAPTER_CONTRACT_BREACH"
MALFORMED_PAYLOAD_NOT_A_JSON_OBJECT = "PAYLOAD_NOT_A_JSON_OBJECT"
MALFORMED_SCHEMA_DECLARATION_INVALID = "SCHEMA_DECLARATION_INVALID"
_MALFORMED_EMPTINESS_UNDECIDABLE_PREFIX = "EMPTINESS_UNDECIDABLE_"
_MALFORMED_VALIDATOR_FAILED_PREFIX = "VALIDATOR_FAILED_"


@dataclass(frozen=True)
class RetryPolicy:
    """A bounded attempt policy. Every field is required; there are no defaults.

    No defaults on purpose. A default retry policy is a policy nobody chose, and the
    first time it matters is the first time a source is down.
    """

    max_attempts: int
    timeout_seconds: float
    backoff_seconds: float

    def __post_init__(self) -> None:
        if isinstance(self.max_attempts, bool) or not isinstance(self.max_attempts, int):
            raise TypeError("RetryPolicy.max_attempts must be an int")
        if not 1 <= self.max_attempts <= MAX_ATTEMPTS_CEILING:
            raise ValueError(
                f"max_attempts must lie in [1, {MAX_ATTEMPTS_CEILING}], got "
                f"{self.max_attempts}"
            )
        for name, ceiling in (
            ("timeout_seconds", MAX_TIMEOUT_SECONDS_CEILING),
            ("backoff_seconds", MAX_BACKOFF_SECONDS_CEILING),
        ):
            observed = getattr(self, name)
            if isinstance(observed, bool) or not isinstance(observed, float):
                raise TypeError(
                    f"RetryPolicy.{name} must be a float, got "
                    f"{type(observed).__name__}"
                )
            if not math.isfinite(observed):
                raise ValueError(
                    f"RetryPolicy.{name} must be finite, got {observed!r}. "
                    "An infinite timeout is not a lenient timeout, it is no timeout."
                )
            if observed < 0.0 or observed > ceiling:
                raise ValueError(
                    f"RetryPolicy.{name} must lie in [0.0, {ceiling}], got {observed!r}"
                )
        if self.timeout_seconds <= 0.0:
            raise ValueError("RetryPolicy.timeout_seconds must be positive")

    @property
    def worst_case_seconds(self) -> float:
        """The longest this policy can take, stated rather than left to arithmetic."""
        return (
            self.max_attempts * self.timeout_seconds
            + (self.max_attempts - 1) * self.backoff_seconds
        )


@dataclass(frozen=True)
class CollectionResult:
    """What one collection run for one source produced.

    ``reading_admitted`` is ``False`` for a re-fetch of a period already claimed, and
    also ``False`` for every non-``OK`` outcome. Read it with ``reading_key``: a key with
    ``reading_admitted=False`` is a duplicate period; no key at all is an attempt that
    reported no period.
    """

    source_id: str
    adapter_id: str
    collector_run_id: str
    attempts_made: int
    rows_recorded: int
    final_outcome: FetchOutcome
    reading_key: Union[ReadingKey, None]
    reading_admitted: bool

    def __post_init__(self) -> None:
        if self.rows_recorded != self.attempts_made:
            raise AssertionError(
                f"{self.rows_recorded} rows recorded for {self.attempts_made} attempts. "
                "Every fetch attempt writes exactly one row (BLUEPRINT §5); a result "
                "that says otherwise is a defect in the runner, not a tolerance."
            )


def collect(
    adapter: SourceAdapter,
    *,
    policy: RetryPolicy,
    sink: ObservationSink,
    ledger: ReadingLedger,
    collector_run_id: str,
    clock: Callable[[], datetime],
    sleep: Callable[[float], None],
    validator: Union[PayloadValidator, None] = None,
) -> CollectionResult:
    """Run one bounded collection for one source, recording EVERY attempt.

    ``clock`` and ``sleep`` are required injections. There is no default wall clock and
    no default sleep, so no module-level ``now()`` and no real delay can hide inside this
    function, and a test exercises the retry path without waiting for it.

    Raises :exc:`~crash_detector.collectors.validation.SchemaDeclarationInvalid` if the
    adapter's declared schema is unusable — after the attempt row has been written. That
    is our defect, not the source's, and it is not retried and not silently recorded as
    the source misbehaving.
    """
    if not isinstance(collector_run_id, str) or not collector_run_id:
        raise ValueError("collect requires a non-empty collector_run_id")
    if not isinstance(policy, RetryPolicy):
        raise TypeError("collect requires a RetryPolicy")
    if not callable(clock) or not callable(sleep):
        raise TypeError("collect requires callable clock and sleep")

    active_validator: PayloadValidator = (
        JsonSchemaValidator() if validator is None else validator
    )
    source_id = adapter.source_id
    adapter_id = adapter.adapter_id

    rows_recorded = 0
    attempts_made = 0
    final_outcome: FetchOutcome = FetchFailed(
        error_class=ERROR_ATTEMPT_DID_NOT_COMPLETE
    )

    for attempt_number in range(1, policy.max_attempts + 1):
        attempts_made = attempt_number
        requested_utc = ensure_utc(clock())

        # Pre-set so that a BaseException escaping _attempt still leaves a TRUTHFUL row
        # behind rather than no row. "The attempt terminated before it could be
        # classified" is a fact; silence is not.
        outcome: FetchOutcome = FetchFailed(error_class=ERROR_ATTEMPT_DID_NOT_COMPLETE)
        try:
            outcome = _attempt(
                adapter,
                policy=policy,
                validator=active_validator,
                requested_utc=requested_utc,
                clock=clock,
            )
        except SchemaDeclarationInvalid as exc:
            # Recorded, then re-raised. The row must exist (guarantee 1) and the defect
            # must be loud (Standards Baseline §8) — those are not in tension.
            outcome = Malformed(
                schema_error_class=MALFORMED_SCHEMA_DECLARATION_INVALID,
                instance_path="",
            )
            raise exc
        finally:
            sink.record(
                AttemptRecord(
                    observation=ObservationRecord(
                        source_id=source_id,
                        observed_utc=ensure_utc(clock()),
                        outcome=outcome,
                    ),
                    adapter_id=adapter_id,
                    collector_run_id=collector_run_id,
                    attempt_number=attempt_number,
                    requested_utc=requested_utc,
                )
            )
            rows_recorded += 1

        final_outcome = outcome
        if not isinstance(outcome, FetchFailed):
            break
        if attempt_number < policy.max_attempts and policy.backoff_seconds > 0.0:
            sleep(policy.backoff_seconds)

    reading_key: Union[ReadingKey, None] = None
    reading_admitted = False
    if isinstance(final_outcome, OK):
        reading_key = _reading_key(source_id, final_outcome)
        reading_admitted = bool(ledger.admit_if_absent(reading_key))

    return CollectionResult(
        source_id=source_id,
        adapter_id=adapter_id,
        collector_run_id=collector_run_id,
        attempts_made=attempts_made,
        rows_recorded=rows_recorded,
        final_outcome=final_outcome,
        reading_key=reading_key,
        reading_admitted=reading_admitted,
    )


def _reading_key(source_id: str, outcome: OK) -> ReadingKey:
    from crash_detector.time_utc import format_utc

    return (source_id, format_utc(outcome.source_as_of_utc))


def _attempt(
    adapter: SourceAdapter,
    *,
    policy: RetryPolicy,
    validator: PayloadValidator,
    requested_utc: datetime,
    clock: Callable[[], datetime],
) -> FetchOutcome:
    """One classified attempt.

    Every ``except`` here maps to a NAMED outcome constructor. None of them returns a
    number, a previous value, or an empty success — the three shapes doctrine §3.2
    forbids. There is no bare ``except`` and no ``except Exception: pass``.
    """
    try:
        response = adapter.fetch(timeout_seconds=policy.timeout_seconds)
    except AdapterFetchError as exc:
        return FetchFailed(error_class=exc.error_class, http_status=exc.http_status)
    except TimeoutError:
        return FetchFailed(error_class=ERROR_TIMEOUT)
    except Exception as exc:
        # Classified by exception TYPE, never by its message: an exception raised inside
        # an HTTP client habitually stringifies the request, and the request carries the
        # source credential (PBG-SEC-002).
        return FetchFailed(
            error_class=f"{_ERROR_UNCLASSIFIED_PREFIX}{type(exc).__name__}"
        )

    elapsed = (ensure_utc(clock()) - requested_utc).total_seconds()
    if elapsed > policy.timeout_seconds:
        return FetchFailed(error_class=ERROR_TIMEOUT_BUDGET_EXCEEDED)

    if not isinstance(response, FetchedResponse):
        return Malformed(
            schema_error_class=MALFORMED_ADAPTER_CONTRACT_BREACH,
            instance_path="",
        )

    try:
        validator.validate(response.payload, adapter.response_schema)
    except SchemaRejection as exc:
        return Malformed(
            schema_error_class=exc.error_class,
            instance_path=exc.instance_path,
        )
    except SchemaDeclarationInvalid:
        # OUR defect. Travels to `collect`, which records the row and re-raises.
        raise
    except Exception as exc:
        return Malformed(
            schema_error_class=(
                f"{_MALFORMED_VALIDATOR_FAILED_PREFIX}{type(exc).__name__}"
            ),
            instance_path="",
        )

    if not isinstance(response.payload, AbcMapping):
        # The declared schema admitted something that is not a JSON object, and
        # `OK.payload` is a mapping. Refused rather than wrapped: wrapping would invent
        # a key name, and an invented key is a shape the engine never agreed to.
        return Malformed(
            schema_error_class=MALFORMED_PAYLOAD_NOT_A_JSON_OBJECT,
            instance_path="",
        )

    try:
        empty = adapter.is_empty(response.payload)
    except Exception as exc:
        return Malformed(
            schema_error_class=(
                f"{_MALFORMED_EMPTINESS_UNDECIDABLE_PREFIX}{type(exc).__name__}"
            ),
            instance_path="",
        )
    if not isinstance(empty, bool):
        # A truthy string or a non-empty list would make "is it empty" answer yes by
        # accident. Emptiness is a decision, and it must be stated as one.
        return Malformed(
            schema_error_class=MALFORMED_ADAPTER_CONTRACT_BREACH,
            instance_path="",
        )
    if empty:
        return Empty()

    return OK(payload=response.payload, source_as_of_utc=response.source_as_of_utc)
