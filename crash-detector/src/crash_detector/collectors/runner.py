"""The collection runner — bounded, and it always writes the row (BLUEPRINT §5).

Guarantees, in the order of how much they matter:

1. **Every fetch attempt writes exactly one attempt row**, whatever happens: success,
   timeout, malformed response, a broken declared schema, or an exception nobody
   anticipated. The write is in a ``finally``, so even a ``BaseException`` —
   ``KeyboardInterrupt``, ``SystemExit``, the container's ``SIGTERM`` handler — leaves the
   attempt recorded before it propagates.
2. **Bounded timeouts and bounded retries.** :class:`RetryPolicy` refuses an unbounded or
   unvalidated configuration at construction, and the runner independently measures the
   elapsed time so an adapter that ignores its budget cannot deliver a value. **That
   measurement is now this system's own** (BP-AMENDMENT-0001 §D.3 part 1): it is taken from
   :func:`~crash_detector.collectors.delay.monotonic_reading`, not from a ``clock`` callable
   the caller supplied, so an adapter's punctuality is no longer decided by an object
   the caller wrote. See :mod:`crash_detector.collectors.delay`.
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
import typing
from collections.abc import Mapping as AbcMapping
from dataclasses import dataclass, fields
from datetime import datetime, timedelta
from typing import Union

from crash_detector.admission import ESTABLISHED_HERE, admits, is_exactly
from crash_detector.collectors.adapter import (
    ADAPTER_PROTOCOL_MEMBERS,
    AdapterFetchError,
    FetchedResponse,
    SourceAdapter,
    missing_adapter_members,
)
from crash_detector.collectors.attempt import (
    AttemptRecord,
    ObservationSink,
    ReadingKey,
    ReadingLedger,
)
from crash_detector.collectors.delay import (
    MAX_DELAY_SECONDS_CEILING,
    DelayKind,
    apply_delay,
    monotonic_reading,
    seconds_since,
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
from crash_detector.own_terms import NotEstablishedOnOwnTerms, own_str
from crash_detector.time_utc import ensure_utc
from crash_detector.establishment import each_of, establishes, one_of

__all__ = [
    "RetryPolicy",
    "CollectionResult",
    "collect",
    "AdapterContractBreach",
    "SinkContractBreach",
    "LedgerContractBreach",
    "MAX_ATTEMPTS_CEILING",
    "MAX_TIMEOUT_SECONDS_CEILING",
    "MAX_BACKOFF_SECONDS_CEILING",
    "ERROR_ATTEMPT_DID_NOT_COMPLETE",
    "ERROR_TIMEOUT_BUDGET_EXCEEDED",
    "ERROR_TIMEOUT",
    "MALFORMED_ADAPTER_CONTRACT_BREACH",
    "MALFORMED_PAYLOAD_NOT_A_JSON_OBJECT",
    "MALFORMED_SCHEMA_DECLARATION_INVALID",
    "MALFORMED_VALIDATOR_CONTRACT_BREACH",
    "PAYLOAD_SNAPSHOT_MAX_DEPTH",
]


class AdapterContractBreach(TypeError):
    """The supplied adapter is not structurally an adapter, or its identity is not a str.

    OURS, not the source's — an adapter missing a member is a wiring defect in this system,
    and recording it as a MALFORMED observation would blame the source for our bug
    (Standards Baseline §8). Raised before any attempt is made, so no attempt row is owed.

    A ``TypeError`` because what is wrong is the KIND of thing supplied, which is the same
    reading :exc:`~crash_detector.admission.NotAdmitted` and
    :exc:`~crash_detector.own_terms.NotEstablishedOnOwnTerms` already take.
    """


class SinkContractBreach(TypeError):
    """``ObservationSink.record`` returned something. The contract is ``None``, or raise."""


class LedgerContractBreach(TypeError):
    """``ReadingLedger.admit_if_absent`` answered with something that is not a ``bool``.

    Never coerced. "Was this source period already claimed" is the question idempotency
    turns on, and answering it by truthiness is how a re-fetch becomes a second reading.
    """

#: Hard ceilings, enforced at construction. A policy outside these is refused rather than
#: honoured: a retry loop nobody bounded is an outage generator, and a ten-minute
#: per-attempt timeout is an unbounded wait wearing a number (Standards Baseline §11).
MAX_ATTEMPTS_CEILING = 5
MAX_TIMEOUT_SECONDS_CEILING = 60.0
#: THE SAME OBJECT the delay executor bounds itself by, imported rather than restated. Two
#: constants with the same value in two modules are one edit away from being two different
#: bounds, and the one that would then be wrong is the one nobody looked at.
MAX_BACKOFF_SECONDS_CEILING = MAX_DELAY_SECONDS_CEILING

# Stable failure classifications. Named constants rather than literals so a guard can
# assert on the class rather than on a string somebody retyped.
ERROR_ATTEMPT_DID_NOT_COMPLETE = "ATTEMPT_DID_NOT_COMPLETE"
ERROR_TIMEOUT_BUDGET_EXCEEDED = "TIMEOUT_BUDGET_EXCEEDED"
ERROR_TIMEOUT = "TIMEOUT"
_ERROR_UNCLASSIFIED_PREFIX = "UNCLASSIFIED_"

#: How far :func:`_payload_snapshot` rebuilds the exact-typed container spine of a validated
#: payload before it carries what it finds BY REFERENCE. Declared as a number rather than
#: left implicit in a recursion limit, because it IS the reach of the escape-1 closure and a
#: reach nobody can name is a reach nobody can test. Deeper than any JSON this system has a
#: use for, and far under the interpreter's recursion ceiling, so the rebuild cannot itself
#: become a way to raise inside the boundary. It also terminates on a payload that contains
#: a reference to itself, which an unbounded rebuild would not.
PAYLOAD_SNAPSHOT_MAX_DEPTH = 32

MALFORMED_ADAPTER_CONTRACT_BREACH = "ADAPTER_CONTRACT_BREACH"
MALFORMED_PAYLOAD_NOT_A_JSON_OBJECT = "PAYLOAD_NOT_A_JSON_OBJECT"
MALFORMED_SCHEMA_DECLARATION_INVALID = "SCHEMA_DECLARATION_INVALID"
#: §D.3 part 2. A validator that returns a value instead of raising or returning ``None``
#: has answered a question nobody asked; the response is recorded as MALFORMED rather than
#: read as conforming.
MALFORMED_VALIDATOR_CONTRACT_BREACH = "VALIDATOR_CONTRACT_BREACH"
_MALFORMED_EMPTINESS_UNDECIDABLE_PREFIX = "EMPTINESS_UNDECIDABLE_"
_MALFORMED_VALIDATOR_FAILED_PREFIX = "VALIDATOR_FAILED_"


@establishes(
    max_attempts=int,
    timeout_seconds=float,
    backoff_seconds=float,
)
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


@establishes(
    source_id=str,
    adapter_id=str,
    collector_run_id=str,
    attempts_made=int,
    rows_recorded=int,
    final_outcome=one_of(OK, FetchFailed, Malformed, Empty),
    reading_key=one_of(tuple, None),
    reading_admitted=bool,
    delays_applied=each_of(float, within=(tuple,)),
)
@dataclass(frozen=True)
class CollectionResult:
    """What one collection run for one source produced.

    ``reading_admitted`` is ``False`` for a re-fetch of a period already claimed, and
    also ``False`` for every non-``OK`` outcome. Read it with ``reading_key``: a key with
    ``reading_admitted=False`` is a duplicate period; no key at all is an attempt that
    reported no period.

    ``delays_applied`` is **what the runner actually waited for**, in order, one entry per
    backoff performed. It exists because §D.3 part 1 deleted the ``sleep`` callable: the
    property *"backoff between attempts, never after the last one"* used to be read off a
    caller-supplied double's log, which is the system's behaviour attested by the caller's
    own object. It is now the runner's own answer about its own run.
    """

    source_id: str
    adapter_id: str
    collector_run_id: str
    attempts_made: int
    rows_recorded: int
    final_outcome: FetchOutcome
    reading_key: Union[ReadingKey, None]
    reading_admitted: bool
    #: NO DEFAULT, like every other field here. A default ``()`` would be the claim "this
    #: run waited for nothing", and a claim nobody made is not a claim this record may
    #: manufacture.
    delays_applied: tuple

    def __post_init__(self) -> None:
        if type(self.delays_applied) is not tuple or any(
            type(entry) is not float for entry in self.delays_applied
        ):
            raise TypeError(
                "CollectionResult.delays_applied must be a tuple of exactly float; it is "
                "the record of what this run waited for and a value of another kind in it "
                "is a record of something else"
            )
        if self.rows_recorded != self.attempts_made:
            raise AssertionError(
                f"{self.rows_recorded} rows recorded for {self.attempts_made} attempts. "
                "Every fetch attempt writes exactly one row (BLUEPRINT §5); a result "
                "that says otherwise is a defect in the runner, not a tolerance."
            )


@admits(
    adapter=ESTABLISHED_HERE(
        "CD-BP-003, BLUEPRINT §17. SourceAdapter is a Protocol — a boundary to a market "
        "data source that does not exist in this tree and never will be a class this "
        "package can name, so there is no concrete type to require and requiring one would "
        "be wrong (BP-AMENDMENT-0001 §D.3 part 2). CARRIER MEASURED, AND IT IS THE RETURNS "
        "AND NOT THE IDENTITY: missing_adapter_members refuses a structurally "
        "non-conforming adapter with AdapterContractBreach before any attempt; source_id "
        "and adapter_id are rebuilt by own_terms.own_str; the fetch return is exact-typed "
        "FetchedResponse; the is_empty answer is exact-typed bool — all four measured in "
        "tests/test_collector_admission.py. FOR WHAT A CONFORMING ADAPTER SAYS: NOT PROVED "
        "TO BE CARRIED ANYWHERE (source trust is CD-D-005, owed)."
    ),
    policy=RetryPolicy,
    sink=ESTABLISHED_HERE(
        "CD-BP-003, BLUEPRINT §17. ObservationSink is a Protocol — a boundary to the store, "
        "whose implementation is deliverable A5's SQL and not a Python class this package "
        "may name. CARRIER MEASURED for what it hands back: _record refuses a non-None "
        "return with SinkContractBreach "
        "(tests/test_collector_admission.py::test_a_sink_that_answers_with_a_value_is_refused). "
        "For whether a sink that returned None actually persisted the row: NOT PROVED TO BE "
        "CARRIED ANYWHERE in process — the carrier is the store's own durability and the "
        "grant matrix, measured live by CD-RT-GRANT-MATRIX-LIVE."
    ),
    ledger=ESTABLISHED_HERE(
        "CD-BP-003, BLUEPRINT §17. ReadingLedger is a Protocol standing in for a UNIQUE "
        "(source_id, source_as_of_utc) constraint, which is a property of the store and not "
        "of any object here. CARRIER MEASURED for its verdict: _established_ledger_verdict "
        "requires exactly a bool and refuses with LedgerContractBreach, replacing a bool() "
        "coercion that read any truthy answer as a first claim "
        "(tests/test_collector_admission.py::test_a_ledger_verdict_that_is_not_a_bool_is_refused). "
        "For whether the verdict is TRUE: NOT PROVED TO BE CARRIED ANYWHERE here — the "
        "carrier is the SQL UNIQUE constraint, measured by tests/test_store_schema_sql.py."
    ),
    collector_run_id=str,
    started_utc=datetime,
    delay=DelayKind,
    validator=ESTABLISHED_HERE(
        "CD-BP-003, BLUEPRINT §17. PayloadValidator is a Protocol; None selects the shipped "
        "JsonSchemaValidator, so the default path is a concrete type this package owns and "
        "only a supplied one is foreign. CARRIER MEASURED for its verdict: a validator that "
        "returns anything but None is recorded MALFORMED with VALIDATOR_CONTRACT_BREACH "
        "rather than read as agreement "
        "(tests/test_collector_admission.py::test_a_validator_that_returns_a_repaired_payload_is_a_breach). "
        "For whether a supplied validator validated anything at all: NOT PROVED TO BE "
        "CARRIED ANYWHERE."
    ),
)
def collect(
    adapter: SourceAdapter,
    *,
    policy: RetryPolicy,
    sink: ObservationSink,
    ledger: ReadingLedger,
    collector_run_id: str,
    started_utc: datetime,
    delay: DelayKind,
    validator: Union[PayloadValidator, None] = None,
) -> CollectionResult:
    """Run one bounded collection for one source, recording EVERY attempt.

    **A6 OF BP-AMENDMENT-0001 §D.2, CLOSED BY §D.3, BOTH PARTS.** This door took SIX
    caller-supplied objects plus a policy and admitted exactly one of them — ``policy``, by
    ``isinstance``, which admits a subclass shadowing ``max_attempts`` with a property.
    Everything the dial path later evaluates was written by objects this function never
    established.

    **PART 1 — ``clock`` AND ``sleep`` ARE GONE, AS PARAMETERS.** They were
    ``Callable``\\ s, admitted by ``callable()``, which establishes that a thing can be
    called and nothing about what it does. They are replaced by:

    * ``started_utc`` — the run's instant, **a VALUE**, exact-typed at this door and then
      rebuilt by :func:`~crash_detector.time_utc.ensure_utc` from its own primitive fields,
      so no method of the supplied object is consulted. Every attempt timestamp is derived
      from it and from this system's OWN monotonic reading
      (:mod:`crash_detector.collectors.delay`), which is why an attempt row can no longer
      claim to have finished before it started;
    * ``delay`` — a member of the **closed** :class:`~crash_detector.collectors.delay.DelayKind`,
      executed by the module that owns waiting. A caller names a kind; it does not supply
      one. This is ``combine_within_one_dial(using)``'s repair applied again.

    There is no expression a caller can write that puts code on this path. Not a stronger
    check on a callable — no parameter through which a callable arrives.

    **PART 2 — THE FOUR PROTOCOLS STAY AND EVERYTHING THEY HAND BACK IS ESTABLISHED ON
    ARRIVAL.** ``adapter``, ``sink``, ``ledger`` and ``validator`` are boundaries to
    genuinely foreign things; exact-typing them against a concrete class is not available
    and would be wrong. So this system does not claim to establish what they ARE. It
    establishes everything they HAND IT, at each point of return — see the DECLARED LIMIT.

    Raises :exc:`~crash_detector.collectors.validation.SchemaDeclarationInvalid` if the
    adapter's declared schema is unusable — after the attempt row has been written. That
    is our defect, not the source's, and it is not retried and not silently recorded as
    the source misbehaving.

    ==================================================================================
    DECLARED LIMIT — **CD-BP-003** (CD-RULE-004, stated identically here, in
    ``required-tests.yaml`` and in
    ``contracts/execution/CD-RT-002-DOORS-REQUIRE-THEIR-TYPES.md``; CD-RULE-006 applied to
    every carrier named). **BLUEPRINT §17 names this the softest remaining surface and the
    Product Owner named it the fourth Assurance seat's first target. It is written for that
    reader.**
    ==================================================================================

    **THIS IS A DOOR THAT ADMITS, NOT AN ABSENCE OF A DOOR, AND IT IS WEAKER THAN §C's
    CLOSURE IN A WAY THAT MATTERS.** §C deleted the field through which a model object could
    arrive: there is no expression to write. Here the parameter remains, and four of the
    seven things passed through it are objects this system cannot name a type for.

    1. **THE PROTOCOL CONFORMANCE CHECK IS A VOCABULARY, AND IT FAILS THE RENAME TEST.**
       ``missing_adapter_members`` asks ``hasattr`` for five SPELLED names. An object
       supplying all five conforms, whatever it does. Executable example — and it is not
       hypothetical, it is the whole shape of the residue::

           class Hostile:                       # conforms; refused by nothing here
               source_id = "src.e"
               adapter_id = "a.v0"
               response_schema = {"type": "object"}
               def fetch(self, *, timeout_seconds): return FetchedResponse(...)
               def is_empty(self, payload): return False

       ``variants/WO-2R3/V26-conforming-hostile-adapter.patch`` is that object, and it is
       ADMITTED. What it can then do is bounded by what this runner establishes of its
       returns — a ``FetchedResponse`` of exact type, a ``bool`` of exact type, a payload
       that passes the declared schema — and by the fact that nothing under
       ``collectors/`` may import the dial path or the engine. What it CANNOT be prevented
       from doing is reporting an honest-shaped observation that is untrue.
       **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.** Source trust is CD-D-005 and
       BLUEPRINT §5, and it is owed, not held. Nothing in this tree establishes that a
       conforming adapter is telling the truth, and this seat does not claim otherwise.

    2. **``started_utc``'s TYPE IS ESTABLISHED; ITS TRUTH IS NOT.** A caller passing an
       instant from last year gets attempt rows dated last year. Executable example:
       ``collect(..., started_utc=datetime(2016, 1, 1, tzinfo=timezone.utc), ...)`` is
       admitted and every ``AttemptRecord.requested_utc`` reads 2016.
       **CARRIER MEASURED, AND ONLY FOR THE ONE ROUTE THAT DECIDES A DIAL:** a dishonest
       ``observed_utc`` does not make a stale reading fresh, because freshness is computed
       from the OUTCOME's ``source_as_of_utc`` against
       :class:`~crash_detector.staleness.StalenessWindow` in ``engine.evaluate``, not from
       the collector's clock — measured by
       ``tests/test_evaluate.py::test_a_future_dated_observation_is_not_treated_as_fresh``
       and its siblings. For attempt-row latency figures and for operator forensics:
       **NOT PROVED TO BE CARRIED ANYWHERE.**

    3. **THE SINK AND THE LEDGER ARE ESTABLISHED ONLY IN WHAT THEY RETURN.** A sink that
       returns ``None`` and writes nothing is indistinguishable here from one that
       persisted durably; a ledger that returns ``True`` twice claims two first-claims of
       one period. Executable example:
       ``variants/WO-2R3/V27-lying-ledger.patch`` — a ledger returning ``True`` for a key it
       has already admitted, which makes a re-fetch look like a fresh reading.
       **CARRIER MEASURED, AND IT IS NOT THIS LAYER:** deliverable A5's SQL —
       ``UNIQUE (source_id, source_as_of_utc)`` on the reading and no ``UPDATE``/``DELETE``
       grant on ``raw.observation`` — is the structural carrier, measured live against a
       digest-pinned Postgres by ``CD-RT-GRANT-MATRIX-LIVE`` and by
       ``tests/test_store_schema_sql.py``. In-process, against an in-memory ledger:
       **NOT PROVED TO BE CARRIED ANYWHERE**, and it cannot be — the property belongs to the
       store.

    4. **WHAT IS *NOT* A LIMIT, SO THE SEAT LOOKING FOR ONE DOES NOT WASTE THE TRIP.**
       ``policy`` is exact-typed at this door: a ``RetryPolicy`` subclass shadowing
       ``max_attempts`` with a property is REFUSED, which ``isinstance`` admitted until this
       increment. ``delay`` is exact-typed against a closed enum. ``started_utc`` is
       exact-typed and rebuilt. Those three are closures, not admissions — **AND THE
       RE-MEASUREMENT ORDERED BY PO-DECISIONS-0011 RULING 3 STRENGTHENS THEM RATHER THAN
       WEAKENING THEM, WHICH IS ALSO WORTH WRITING DOWN.** ``@admits`` compiles its declared
       types at DECORATION time, so rebinding ``runner.RetryPolicy`` in this module's globals
       — the leverage ESCAPE 2 uses — does NOT defeat them. Measured by
       ``variants/WO-2R3/P-E1-what-is-closed-at-that-door.py`` arm (i'): with
       ``runner.RetryPolicy`` rebound to an unrelated class, a GENUINE ``RetryPolicy`` is
       still ADMITTED and the unrelated class is still ``NotAdmitted``.
       **THE CONTRAST THAT MATTERS IS WITH THE LINE BELOW:** ``type(response) is not
       FetchedResponse`` at this module's own boundary resolves its name AT CALL TIME from
       these same globals, and arm (iv) rebinds it and walks a property-backed look-alike
       straight through. **AN EXACT-TYPE DOOR IS ONLY AS STRONG AS WHEN IT RESOLVES ITS
       TYPE**, and this file contains one of each.
       ``started_utc`` closes the TYPE and never the TRUTH — an instant from 2016 is ADMITTED
       and every attempt row reads 2016 (arm (ii), and DECLARED LIMIT 2 above).

       **THE FOURTH CLAIM THAT USED TO STAND HERE IS SUPERSEDED, AND IT IS SUPERSEDED
       BECAUSE IT WAS MEASURED FALSE — PBG-CONT-003, corrections supersede, never edit
       away.** The superseded wording, quoted so a reader who remembers it can see what
       replaced it:

           *"Every value the four protocols return is exact-typed on arrival."*

       **THAT SENTENCE IS LITERALLY TRUE AND WAS OFFERED AS CLOSURE, AND IT CLOSED THE TYPE
       AND NOT THE VALUE.** ``CD-ASR-WO2R3-01`` reproduced ESCAPE 1 against it: the type of
       ``OK.payload`` was exactly ``dict`` while the value it held was not the value the
       validator had judged. Filing that under "not a limit" is worse than declaring no
       limit at all, because the declaration is where a reader stops reading — and four
       parties stopped there. It is not restated in a corrected form here; the corrected
       statement of what IS closed about a returned value is DECLARED LIMIT 5, which is a
       LIMIT and is filed as one. **This claim may no longer be cited toward CD-AC-002**
       (PO-DECISIONS-0011 ruling 3, and the removal of the prop is the Product Owner's).

    5. **THE PAYLOAD SNAPSHOT CLOSES THE ADAPTER ROUTE TO A DECLARED DEPTH AND OF DECLARED
       TYPES, AND NOTHING WIDER.** Since WO-2R3 increment 6 the object stored on
       ``OK.payload`` is a rebuild taken after the validation verdict and before
       ``is_empty`` is called, and ``is_empty`` is handed a second, independent rebuild —
       so an adapter that mutates its argument mutates neither the judged value nor the
       stored one. :func:`_payload_snapshot` states the mechanism. **WHAT IT DOES NOT
       REACH, each demonstrated by an arm of
       ``variants/WO-2R3/P-A-escape1-stored-is-not-validated.py``:**

       * **A CONTAINER THAT IS NOT EXACTLY ``dict``, ``list`` OR ``tuple`` IS CARRIED BY
         REFERENCE**, and the adapter may still rewrite its interior after the snapshot.
         Executable example — probe arm ``nested-dict-subclass``::

             class Sub(dict): ...
             payload = {"reading": 0.25, "nested": Sub({"reading": 0.25})}
             def is_empty(self, payload):          # the adapter's own code
                 payload["nested"]["reading"] = float("inf")
                 return False
             # stored: {"nested": {"reading": Infinity}, "reading": 0.25}
             # and the stored payload FAILS the schema it was judged by

       * **ANYTHING BELOW :data:`PAYLOAD_SNAPSHOT_MAX_DEPTH` IS CARRIED BY REFERENCE.**
         Executable example — probe arm ``beyond-depth-cap``, which nests two hundred
         levels and rewrites the innermost ``reading`` to ``inf`` after validation.

       * **IF THE ``FetchedResponse`` DOOR HAS ITSELF BEEN DEFEATED, THIS CLOSURE GOES WITH
         IT.** ESCAPE 2 rebinds ``FetchedResponse`` in this module's globals, after which
         ``payload`` is a property and every read of it is the adapter's code. The payload is
         now read ONCE and bound to a local (it was read FOUR times), so the object judged is
         the object snapshotted even in that case — measured by
         ``P-E1-what-is-closed-at-that-door.py`` arm (iv), ``times the payload PROPERTY was
         read by package code: 4`` at ``531c95c`` and ``1`` now. **THAT IS A NARROWING, NOT A
         CLOSURE:** one read still lets the look-alike choose what it hands over, and closing
         the global-rebind route is NOT this increment's and is not claimed here.

       * **THE VALIDATOR IS NOT COVERED AT ALL.** ``validator`` is the OTHER declared-
         foreign protocol at this door, and it is handed the adapter's live object before
         any snapshot exists. A validator that mutates the payload while judging it defeats
         this closure completely, and CLOSING THAT ROUTE IS NOT WHAT THIS LIMIT CLAIMS. The
         probe reports ``validator's argument IS the adapter's live object: True`` at every
         arm, after the fix, on purpose.

       **CARRIER MEASURED:**
       ``tests/test_collector_runner.py::test_a_hostile_is_empty_cannot_change_the_stored_payload``
       and its siblings go RED if the snapshot is removed or if ``is_empty`` is handed the
       stored object. **For the three residues above: NOT PROVED TO BE CARRIED ANYWHERE** —
       no test in this tree fails when a dict subclass nested inside a payload is rewritten
       by an adapter, and this seat does not claim one does.
    """
    if not collector_run_id:
        raise ValueError("collect requires a non-empty collector_run_id")

    started_utc = ensure_utc(started_utc)
    source_id, adapter_id = _established_adapter_identity(adapter)

    active_validator: PayloadValidator = (
        JsonSchemaValidator() if validator is None else validator
    )

    rows_recorded = 0
    attempts_made = 0
    delays_applied: list = []
    final_outcome: FetchOutcome = FetchFailed(
        error_class=ERROR_ATTEMPT_DID_NOT_COMPLETE
    )

    # ONE reading of THIS SYSTEM'S monotonic clock, taken here and never supplied. Every
    # instant below is `started_utc` plus a span measured from it, so the row timestamps
    # are non-decreasing by construction rather than by a caller's good manners.
    run_started = monotonic_reading()

    for attempt_number in range(1, policy.max_attempts + 1):
        attempts_made = attempt_number
        requested_utc = started_utc + timedelta(seconds=seconds_since(run_started))

        # Pre-set so that a BaseException escaping _attempt still leaves a TRUTHFUL row
        # behind rather than no row. "The attempt terminated before it could be
        # classified" is a fact; silence is not.
        outcome: FetchOutcome = FetchFailed(error_class=ERROR_ATTEMPT_DID_NOT_COMPLETE)
        try:
            outcome = _attempt(
                adapter,
                policy=policy,
                validator=active_validator,
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
            # **GROUND 3 / ESCAPE 3. THE SNAPSHOT IS TAKEN BEFORE THE SINK IS CALLED AND THE
            # ORDER IS THE WHOLE FIX.** `_record` runs inside this `finally:` and every read
            # of the outcome below happens after it, so until this line the object the sink
            # was handed and the object the runner reported were THE SAME OBJECT, and
            # `object.__setattr__` on it rewrote `CollectionResult.final_outcome` and the
            # ledger key. `kept` is re-established through the outcome's own constructor and
            # no sink has ever held a reference to it.
            kept: FetchOutcome = _the_runners_own_copy(outcome)
            _record(
                sink,
                AttemptRecord(
                    observation=ObservationRecord(
                        source_id=source_id,
                        observed_utc=started_utc
                        + timedelta(seconds=seconds_since(run_started)),
                        outcome=outcome,
                    ),
                    adapter_id=adapter_id,
                    collector_run_id=collector_run_id,
                    attempt_number=attempt_number,
                    requested_utc=requested_utc,
                ),
            )
            rows_recorded += 1

        # EVERY READ BELOW IS OF `kept` AND NOT OF `outcome`. The loop-continuation test is
        # included deliberately: `object.__setattr__(x, "__class__", Y)` reassigns the class
        # of a heap type, so a sink could otherwise decide whether the runner retries.
        final_outcome = kept
        if not isinstance(kept, FetchFailed):
            break
        if attempt_number < policy.max_attempts and policy.backoff_seconds > 0.0:
            delays_applied.append(apply_delay(delay, policy.backoff_seconds))

    reading_key: Union[ReadingKey, None] = None
    reading_admitted = False
    if isinstance(final_outcome, OK):
        reading_key = _reading_key(source_id, final_outcome)
        reading_admitted = _established_ledger_verdict(ledger, reading_key)

    return CollectionResult(
        source_id=source_id,
        adapter_id=adapter_id,
        collector_run_id=collector_run_id,
        attempts_made=attempts_made,
        rows_recorded=rows_recorded,
        final_outcome=final_outcome,
        reading_key=reading_key,
        reading_admitted=reading_admitted,
        delays_applied=tuple(delays_applied),
    )


def _reading_key(source_id: str, outcome: OK) -> ReadingKey:
    from crash_detector.time_utc import format_utc

    return (source_id, format_utc(outcome.source_as_of_utc))


# ------------------------------------------------------------------------------------- #
# §D.3 PART 2 — EVERYTHING THE FOUR PROTOCOLS HAND BACK IS ESTABLISHED AT THE POINT OF
# RETURN. The system cannot establish what an adapter IS. It can establish everything the
# adapter HANDS IT, and these three helpers plus `_attempt` are where it does.
# ------------------------------------------------------------------------------------- #


def _established_adapter_identity(adapter: SourceAdapter) -> "tuple[str, str]":
    """The adapter's ``source_id`` and ``adapter_id``, ESTABLISHED, before any attempt.

    Two returns crossing the protocol boundary, and both decide something: ``source_id`` is
    the key the engine looks an observation up by — ``source_id in usable`` is decided by
    its ``__hash__`` and ``__eq__`` — and ``adapter_id`` is the provenance stamped on every
    row. Until §D.3 they were read straight off the supplied object and stored.

    They are rebuilt by :func:`~crash_detector.own_terms.own_str` from their own code
    points, so a ``str`` subclass answering to a source id it is not cannot survive the
    trip. The whole-protocol conformance check runs FIRST, because an adapter missing
    ``is_empty`` used to reach an ``AttributeError`` half way through an attempt and be
    recorded as the SOURCE misbehaving; it is our configuration defect and it is now named
    as one, before a single row is written and therefore before a single row is owed.
    """
    missing = missing_adapter_members(adapter)
    if missing:
        raise AdapterContractBreach(
            f"the supplied adapter does not supply {list(missing)}. Checked against the "
            f"whole of {list(ADAPTER_PROTOCOL_MEMBERS)} rather than the member this "
            "function happens to reach first. THIS IS A VOCABULARY CHECK and it is "
            "declared as one: see CD-BP-003 in collect's DECLARED LIMIT block."
        )
    established = []
    for member in ("source_id", "adapter_id"):
        try:
            value = own_str(getattr(adapter, member))
        except NotEstablishedOnOwnTerms as refusal:
            raise AdapterContractBreach(
                f"adapter.{member} must be a str: {refusal}"
            ) from None
        if not value:
            raise AdapterContractBreach(f"adapter.{member} is empty")
        established.append(value)
    return established[0], established[1]


#: THE CLOSED OUTCOME SET, DERIVED FROM ITS OWN DECLARATION AND NOT SPELLED HERE.
#: ``FetchOutcome = Union[OK, FetchFailed, Malformed, Empty]`` is the declaration; a fifth
#: member arrives in this tuple on the run it is added, with no edit to this module. A
#: hand-written list of four type names would be a VOCABULARY, which is the defect class this
#: project keeps removing.
_OUTCOME_TYPES: tuple = tuple(typing.get_args(FetchOutcome))


def _the_runners_own_copy(outcome: FetchOutcome) -> FetchOutcome:
    """A copy of ``outcome`` that **NO SINK HAS EVER HELD A REFERENCE TO**.

    ====================================================================================
    GROUND 3 / ESCAPE 3 — A MUTATING SINK REWROTE THE OUTCOME THE RUNNER THEN READ.
    ====================================================================================

    ``_record`` is called inside the ``finally:`` of the attempt loop and the runner reads
    ``final_outcome`` afterwards, so **the sink runs BEFORE the read.** The ``OK`` handed to
    the sink and the ``OK`` the runner went on to report were **THE SAME OBJECT**: normal
    ``setattr`` is refused (``FrozenInstanceError``) and ``object.__setattr__`` succeeds, so a
    sink doing::

        object.__setattr__(attempt.observation.outcome, "payload", {"reading": 999.0})
        object.__setattr__(attempt.observation.outcome, "source_as_of_utc", <2000-01-01>)

    changed ``CollectionResult.final_outcome`` and made ``_reading_key`` ask the ledger for a
    key naming a period **NO ROW RECORDS** — which the ledger answered ``admitted``. The sink
    returns ``None`` throughout, so ``_record``'s contract check is satisfied and **nothing
    refuses**.

    **THE SHAPE TAKEN, AND WHY IT IS THE FIRST OF THE TWO THE AUDITOR NAMED.** *"Snapshot the
    outcome before ``_record``, OR derive the reading key from the recorded row."* The second
    is worse than the problem: the recorded row IS the object the sink held, so deriving the
    key from it asks the mutator what it mutated. **THIS SNAPSHOTS**, and it snapshots by
    RE-ESTABLISHING rather than by aliasing — the object is rebuilt through its own
    constructor, so ``__post_init__`` runs again and the result is a different object with a
    different ``payload`` dict.

    **DERIVED, NOT SPELLED.** The member set comes from ``typing.get_args(FetchOutcome)`` and
    the field list from ``dataclasses.fields``, so a fifth outcome member or a new field is
    copied on the run it is added with no edit here. Exact-type membership is asked through
    ``crash_detector.admission.is_exactly``, so a metaclass cannot answer it (``F-06-D``).

    **WHAT THIS DOES NOT COPY, DECLARED RATHER THAN LEFT TO BE FOUND.** ``OK.__post_init__``
    takes ``dict(self.payload)`` — a SHALLOW copy. A payload whose VALUE is itself mutable —
    ``{"reading": {"v": 0.25}}`` — is still shared between the two objects, and a sink that
    mutates the inner object mutates both. **The measured escape is a top-level rewrite and
    this closes it; the nested case is NOT closed and is NOT claimed closed.** Carried, and
    asserted TRUE, by ``tests/test_collector_mutating_sink.py``.
    """
    if not is_exactly(outcome, _OUTCOME_TYPES):
        raise SinkContractBreach(
            f"the runner cannot take its own copy of a {type(outcome).__name__}: the "
            "FetchOutcome sum type is CLOSED and this is not one of its members. Refusing is "
            "the fail-closed direction — a copy this function could not make would leave the "
            "runner reading an object a sink has held."
        )
    return type(outcome)(
        **{field.name: getattr(outcome, field.name) for field in fields(outcome)}
    )


def _record(sink: ObservationSink, attempt: AttemptRecord) -> None:
    """Write one row, and establish what the sink handed back.

    ``ObservationSink.record`` returns ``None``. A sink that returns anything else is not
    the sink this contract describes, and the difference is not cosmetic: the one thing
    this component guarantees is that the row exists, and an object improvising its own
    return protocol here is an object improvising its own idea of what "recorded" means.
    """
    verdict = sink.record(attempt)
    if verdict is not None:
        raise SinkContractBreach(
            f"ObservationSink.record returned {type(verdict).__name__}; the contract is to "
            "persist the row durably and return None, or to RAISE. A sink that answers "
            "with a value of its own is not one this runner can read as having written."
        )


def _established_ledger_verdict(ledger: ReadingLedger, key: ReadingKey) -> bool:
    """Whether THIS call claimed ``key`` — established as an exact ``bool``.

    This used to be ``bool(ledger.admit_if_absent(key))``, and the ``bool(...)`` was the
    defect: it CO-ERCES. A ledger returning the string ``"already claimed"`` — or any
    non-empty object, or one with a ``__bool__`` of its own — reported a duplicate period as
    a fresh reading, decided by the supplied object's own truthiness. The verdict is now
    required to BE a ``bool`` and is never derived from one.
    """
    verdict = ledger.admit_if_absent(key)
    if type(verdict) is not bool:
        raise LedgerContractBreach(
            f"ReadingLedger.admit_if_absent returned {type(verdict).__name__}; exactly "
            "True or exactly False is the contract. 'Was this period already claimed' is "
            "not a question to answer by truthiness — coercing it is how a re-fetch becomes "
            "a second reading of one source period."
        )
    return verdict


def _payload_snapshot(payload: AbcMapping) -> dict:
    """A payload the adapter holds no live reference into — to the declared depth.

    **WHY THIS EXISTS.** ``validator.validate`` judged an object; ``adapter.is_empty`` is
    then handed an object; ``OK`` then stores an object. Until WO-2R3 increment 6 all three
    were THE SAME OBJECT, and the middle one is DECLARED-FOREIGN CODE (``CD-BP-003``). An
    adapter whose ``is_empty`` rewrote the mapping it was handed, and then honestly answered
    ``False``, had the rewritten mapping stored under a verdict earned by the original —
    ``CD-ASR-WO2R3-01``, ESCAPE 1, which moved the WO-2R3 gate to RED.

    ``OK.__post_init__`` has always done ``dict(self.payload)``, and that is why this defect
    survived six increments of reading: a top-level copy IS taken, but it is taken AFTER the
    foreign call, so it faithfully copies the mutation.

    **WHAT IS REBUILT.** ``dict``, ``list`` and ``tuple`` **BY EXACT TYPE**, to
    :data:`PAYLOAD_SNAPSHOT_MAX_DEPTH` levels. Exact type on purpose and not
    :func:`isinstance`: walking a foreign mapping means calling ITS ``keys`` and
    ``__getitem__``, which is the adapter's code running again inside the rebuild that
    exists to stop the adapter's code mattering.

    **WHAT IS CARRIED BY REFERENCE, AND IT IS A DECLARED LIMIT.** See DECLARED LIMIT 4 in
    this module's header. Everything that is not exactly ``dict``/``list``/``tuple`` — which
    includes a ``dict`` SUBCLASS and every mutable leaf — and everything below the depth
    ceiling. The single top-level ``dict(payload)`` is the one place a non-exact mapping is
    read, because the caller has already established that the payload IS a mapping and
    ``OK`` would call ``dict`` on it regardless.

    **THIS IS NOT A DEEP COPY AND MUST NOT BECOME ONE.** :func:`copy.deepcopy` dispatches to
    ``__deepcopy__``/``__reduce_ex__`` on whatever it meets, so deep-copying a hostile
    payload hands the adapter one more execution point — the opposite of the property this
    function is for.
    """
    return _snapshot_value(dict(payload), 0)


def _snapshot_value(value: object, depth: int) -> object:
    if depth >= PAYLOAD_SNAPSHOT_MAX_DEPTH:
        return value
    if type(value) is dict:
        return {key: _snapshot_value(item, depth + 1) for key, item in value.items()}
    if type(value) is list:
        return [_snapshot_value(item, depth + 1) for item in value]
    if type(value) is tuple:
        return tuple(_snapshot_value(item, depth + 1) for item in value)
    return value


def _attempt(
    adapter: SourceAdapter,
    *,
    policy: RetryPolicy,
    validator: PayloadValidator,
) -> FetchOutcome:
    """One classified attempt.

    Every ``except`` here maps to a NAMED outcome constructor. None of them returns a
    number, a previous value, or an empty success — the three shapes doctrine §3.2
    forbids. There is no bare ``except`` and no ``except Exception: pass``.

    **THE ROUND TRIP IS TIMED BY THIS SYSTEM** (§D.3 part 1). The span is taken from
    :func:`~crash_detector.collectors.delay.monotonic_reading` either side of ``fetch``, so
    the judgement *"this response arrived after its budget"* is computed from a clock no
    caller supplied and no adapter can influence. It used to be computed from two calls to
    a caller-supplied ``clock``, and a clock that never advances made every adapter
    punctual.
    """
    before = monotonic_reading()
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

    if seconds_since(before) > policy.timeout_seconds:
        return FetchFailed(error_class=ERROR_TIMEOUT_BUDGET_EXCEEDED)

    # ESTABLISHED AT THE POINT OF RETURN, BY EXACT TYPE (§D.3 part 2). `isinstance` stood
    # here until this increment, and it admitted a FetchedResponse SUBCLASS — which may
    # shadow `payload` with a property, and a property is the adapter's code running inside
    # this runner at the moment the runner reads it. A subclass whose `payload` answers a
    # conforming mapping when the validator asks and something else when `OK` stores it is
    # the same defect as ASR3-F04 one component to the left.
    if type(response) is not FetchedResponse:
        return Malformed(
            schema_error_class=MALFORMED_ADAPTER_CONTRACT_BREACH,
            instance_path="",
        )

    # READ ONCE (WO-2R3 increment 6, ESCAPE 1). `response.payload` was read FOUR separate
    # times on this path — by the validator, by the mapping check, by `is_empty` and by `OK`.
    # On an exact `FetchedResponse` that is four reads of one dataclass attribute and they
    # agree. The exactness door above is what makes that true, and `CD-ASR-WO2R3-01`'s
    # ESCAPE 2 defeats that door by rebinding `FetchedResponse` in this module's globals from
    # caller code — after which `payload` is a PROPERTY, every read is the adapter's code
    # running again, and each read may answer differently. Binding it once means the object
    # judged and the object snapshotted are the same object even in that case.
    raw_payload = response.payload

    try:
        verdict = validator.validate(raw_payload, adapter.response_schema)
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

    # THE VALIDATION VERDICT, ESTABLISHED AT THE POINT OF RETURN (§D.3 part 2). Until this
    # increment the return of `validate` was DISCARDED, so "conforming" meant only "did not
    # raise". A validator that returns a repaired or coerced payload instead of raising was
    # therefore read as agreement — silent coercion at the one boundary whose entire job is
    # to refuse it (Standards Baseline §4). `None` is the whole of the contract, and
    # anything else is the validator improvising one.
    if verdict is not None:
        return Malformed(
            schema_error_class=MALFORMED_VALIDATOR_CONTRACT_BREACH,
            instance_path="",
        )

    if not isinstance(raw_payload, AbcMapping):
        # The declared schema admitted something that is not a JSON object, and
        # `OK.payload` is a mapping. Refused rather than wrapped: wrapping would invent
        # a key name, and an invented key is a shape the engine never agreed to.
        return Malformed(
            schema_error_class=MALFORMED_PAYLOAD_NOT_A_JSON_OBJECT,
            instance_path="",
        )

    # THE SNAPSHOT (WO-2R3 increment 6, ESCAPE 1). Taken AFTER the validation verdict and
    # BEFORE any foreign code can reach the payload again; `is_empty` is handed a SECOND,
    # independent snapshot, so the object it can mutate is not the object that is stored and
    # not the object that was judged. What the rebuild does NOT reach is DECLARED LIMIT 4.
    payload = _payload_snapshot(raw_payload)

    try:
        empty = adapter.is_empty(_payload_snapshot(payload))
    except Exception as exc:
        return Malformed(
            schema_error_class=(
                f"{_MALFORMED_EMPTINESS_UNDECIDABLE_PREFIX}{type(exc).__name__}"
            ),
            instance_path="",
        )
    if type(empty) is not bool:
        # A truthy string or a non-empty list would make "is it empty" answer yes by
        # accident. Emptiness is a decision, and it must be stated as one. EXACT TYPE
        # (§D.3 part 2): the answer must BE a bool, not be convertible to one.
        return Malformed(
            schema_error_class=MALFORMED_ADAPTER_CONTRACT_BREACH,
            instance_path="",
        )
    if empty:
        return Empty()

    return OK(payload=payload, source_as_of_utc=response.source_as_of_utc)
