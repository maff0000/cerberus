"""A6 — THE COLLECTOR BOUNDARY (BP-AMENDMENT-0001 §D.3, both parts, in force).

``collect`` took SIX caller-supplied objects plus a policy and admitted exactly ONE of them
— ``policy``, by ``isinstance``, which is not this project's exact-type standard. Everything
the dial path later evaluates was written by objects the collector never established.

| # | plant | must fail at |
|---|-------|--------------|
| A6-1 | a ``RetryPolicy`` SUBCLASS whose ``max_attempts`` is a property | the ``admits`` door |
| A6-2 | a callable supplied where the run's instant belongs | the ``admits`` door |
| A6-3 | a callable supplied where the delay kind belongs | the ``admits`` door |
| A6-4 | a ``FetchedResponse`` SUBCLASS whose ``payload`` is a property | the point of return, MALFORMED |
| A6-5 | a ledger answering a truthy non-``bool`` | the point of return, ``LedgerContractBreach`` |
| A6-6 | a validator returning a repaired payload instead of raising | the point of return, MALFORMED |
| A6-7 | a sink answering with a value of its own | the point of return, ``SinkContractBreach`` |
| A6-8 | an adapter missing a protocol member | before any attempt, ``AdapterContractBreach`` |
| A6-9 | an adapter whose ``source_id`` is a ``str`` SUBCLASS answering to an id it is not | the point of return, ``own_str`` |

**THE BASELINE ARMS ARE HERE. THE VIOLATED ARMS ARE NOT AND CANNOT BE.** "Remove the guard
and show it passes" means editing ``src/``, and this suite runs against the tree as it
stands. Each violated arm is a patch under ``variants/WO-2R3/``, applied to a pristine
``git archive`` extraction, run there and discarded. The manifest carries the literal
command line for each.

**EVERY PLANT RUNS OVER ``EMPTY_MODEL_REGISTRY`` AND ``EMPTY_SOURCE_REGISTRY``** — zero
model rows, zero source rows — because that is the shipped WO-2 state and a plant
demonstrated against a configuration nobody ships demonstrates nothing about what ships.
The collector path reads no registry at all, so the premise is asserted directly at the
bottom of this module rather than narrated.

**READ CD-BP-003 BEFORE READING THE PASSES HERE.** The declared limit is in ``collect``'s
own docstring, in ``required-tests.yaml`` and in the execution contract. What these plants
show refused is what a Protocol implementation HANDS BACK. What no plant here shows refused
— because nothing refuses it — is a structurally conforming adapter that lies.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from crash_detector.admission import NotAdmitted
from crash_detector.collectors.adapter import FetchedResponse, missing_adapter_members
from crash_detector.collectors.delay import DelayKind
from crash_detector.collectors.runner import (
    MALFORMED_ADAPTER_CONTRACT_BREACH,
    MALFORMED_VALIDATOR_CONTRACT_BREACH,
    AdapterContractBreach,
    LedgerContractBreach,
    RetryPolicy,
    SinkContractBreach,
    collect,
)
from crash_detector.engine.model import EMPTY_MODEL_REGISTRY
from crash_detector.observations import OK, Malformed
from crash_detector.source_registry import EMPTY_SOURCE_REGISTRY

from collector_fakes import FakeInMemoryAdapter, RecordingLedger, RecordingSink
from conftest import FIXED_NOW

SINGLE = RetryPolicy(max_attempts=1, timeout_seconds=5.0, backoff_seconds=0.0)


def _ok_response() -> FetchedResponse:
    return FetchedResponse(payload={"reading": 1.5}, source_as_of_utc=FIXED_NOW)


def _collect(**overrides):
    """One collection over the SHIPPED door, with one argument swapped for the plant."""
    arguments = dict(
        adapter=FakeInMemoryAdapter(script=[_ok_response()]),
        policy=SINGLE,
        sink=RecordingSink(),
        ledger=RecordingLedger(),
        collector_run_id="run-plant",
        started_utc=FIXED_NOW,
        delay=DelayKind.WALL_CLOCK,
    )
    arguments.update(overrides)
    adapter = arguments.pop("adapter")
    return collect(adapter, **arguments)


# ========================================================================================= #
# A6-1 — THE POLICY. `isinstance` ADMITTED A SUBCLASS; EXACT TYPE DOES NOT.
# ========================================================================================= #


def test_a6_1_a_retry_policy_subclass_shadowing_max_attempts_is_refused():
    """A6-1, BASELINE. The defect §D.3 names in terms: *"a RetryPolicy subclass shadowing
    ``max_attempts`` with a property is admitted"*.

    The subclass is honestly constructed — ``__post_init__`` runs and establishes a bounded
    ``max_attempts=1`` — and then answers 5000 when the runner asks, because the property is
    installed after construction. Every ceiling in ``RetryPolicy`` is enforced on the FIELD;
    the loop reads the ATTRIBUTE; and between those two is where a subclass lives.

    REFUSING LAYER: ``crash_detector.admission.admits``, applied at ``collect``'s boundary
    and derived from its signature — ``type(policy) is not RetryPolicy``.
    SCOPE OF THAT LAYER: every call to ``collect`` by any caller anywhere. It is not the
    ``RetryPolicy`` constructor, which was already closed and which this subclass PASSED.

    RENAME TEST: SURVIVES. The refusal is an identity comparison between two type objects.
    Rename ``max_attempts``, rename ``Unbounded``, rename ``policy`` — a subclass is still
    not the class.

    COUNTERFACTUAL (CD-D-079): ``variants/WO-2R3/V28-policy-subclass-isinstance.patch``
    restores ``isinstance(policy, RetryPolicy)`` in place of the door; the same object is
    then ADMITTED and the runner makes 5000 attempts against one source.
    """

    class Unbounded(RetryPolicy):
        pass

    policy = Unbounded(max_attempts=1, timeout_seconds=5.0, backoff_seconds=0.0)
    type.__setattr__(Unbounded, "max_attempts", property(lambda self: 5000))
    assert policy.max_attempts == 5000  # honestly built, then it lies

    with pytest.raises(NotAdmitted) as refusal:
        _collect(policy=policy)
    assert "Unbounded" in str(refusal.value)
    assert "RetryPolicy" in str(refusal.value)


def test_a6_1_the_control_arm_an_ordinary_policy_still_works():
    """A closure that forbids the product is not a closure."""
    result = _collect()
    assert type(result.final_outcome) is OK
    assert result.attempts_made == 1


# ========================================================================================= #
# A6-2 / A6-3 — THE TWO DELETED CALLABLES. THERE IS NO PARAMETER FOR ONE TO ARRIVE THROUGH.
# ========================================================================================= #


def test_a6_2_a_callable_cannot_be_supplied_where_the_run_instant_belongs():
    """A6-2, BASELINE. ``clock`` was a ``Callable[[], datetime]`` admitted by ``callable()``.

    What replaced it is a VALUE, exact-typed at the door. A caller offering the old thing —
    a zero-argument callable returning a datetime — is refused, and so is anything else that
    is not exactly a ``datetime``.

    REFUSING LAYER: ``admits`` at ``collect``'s boundary — ``type(started_utc) is not
    datetime``. SCOPE: every call to ``collect``.
    RENAME TEST: SURVIVES — a type identity comparison consulting no name.
    """
    with pytest.raises(NotAdmitted):
        _collect(started_utc=lambda: FIXED_NOW)


def test_a6_2_a_datetime_subclass_is_refused_too_and_that_is_the_class():
    """The inheritance edge, which is the move an auditor reaches for second.

    ``ASR2-005-A`` was a ``datetime`` subclass overriding ``astimezone`` and ``__rsub__``,
    and it made a row dated 2016 render WITNESS AGREES in 2026. Exact type at the door, and
    then ``ensure_utc`` rebuilds the instant from its own primitive fields anyway — two
    independent refusals of the same class, and the second is measured in
    ``tests/test_own_terms.py``.
    """

    class Sneaky(datetime):
        pass

    with pytest.raises(NotAdmitted):
        _collect(started_utc=Sneaky(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc))


def test_a6_3_a_callable_cannot_be_supplied_where_the_delay_kind_belongs():
    """A6-3, BASELINE. ``sleep`` was a ``Callable[[float], None]`` admitted by ``callable()``.

    REFUSING LAYER: ``admits`` at ``collect``'s boundary — ``type(delay) is not DelayKind``.
    SCOPE: every call to ``collect``. RENAME TEST: SURVIVES.
    """
    with pytest.raises(NotAdmitted):
        _collect(delay=lambda seconds: None)


def test_a6_2_a6_3_the_deleted_parameters_are_deleted_and_not_merely_guarded():
    """THE POINT OF §D.3 PART 1, CHECKED ON THE SIGNATURE.

    This is not "``clock`` is validated more strictly". There is no ``clock`` parameter and
    no ``sleep`` parameter, so there is no expression a caller can write that puts code on
    the collection path. A guard can be weakened; an absent parameter has to be added back,
    and adding one to a decorated door makes ``admits`` refuse every call (P7).
    """
    import inspect

    parameters = inspect.signature(collect).parameters
    assert "clock" not in parameters
    assert "sleep" not in parameters


# ========================================================================================= #
# A6-4 .. A6-9 — §D.3 PART 2. EVERYTHING THE PROTOCOLS HAND BACK, ESTABLISHED ON ARRIVAL.
# ========================================================================================= #


def test_a6_4_a_fetched_response_subclass_whose_payload_is_a_property_is_a_contract_breach():
    """A6-4, BASELINE. ``isinstance(response, FetchedResponse)`` stood here until §D.3.

    The subclass is honestly constructed — ``__post_init__`` runs, ``source_as_of_utc`` is
    established — and then its ``payload`` PROPERTY answers a conforming mapping when the
    validator asks and a different one when ``OK`` stores it. That is ``ASR3-F04``'s shape
    one component to the left: the caller's code running inside this system's judgement at
    the moment the judgement is made.

    REFUSING LAYER: ``crash_detector.collectors.runner._attempt``, at the point of return
    from ``adapter.fetch`` — ``type(response) is not FetchedResponse``.
    SCOPE OF THAT LAYER: every response from every adapter on every attempt. It is NOT the
    ``FetchedResponse`` constructor, which this object PASSED.
    RENAME TEST: SURVIVES. A type identity comparison; rename ``payload`` and the subclass
    is still not the class.
    COUNTERFACTUAL (CD-D-079): ``variants/WO-2R3/V29-fetched-response-subclass.patch``
    restores ``isinstance`` and the same object is ADMITTED, with its property deciding what
    the reading contains.
    """
    calls = {"n": 0}

    class TwoFaced(FetchedResponse):
        pass

    response = TwoFaced(payload={"reading": 1.5}, source_as_of_utc=FIXED_NOW)

    def _two_faced_payload(self):
        calls["n"] += 1
        return {"reading": 1.5} if calls["n"] == 1 else {"reading": 999.0}

    # The property is installed AFTER __post_init__ has run and established the field, so
    # the response is honestly built and then lies when asked. `type.__setattr__` walks past
    # the frozen dataclass and CPython offers no way to stop it, which is exactly why this
    # is closed at the POINT OF RETURN and not on the type.
    type.__setattr__(TwoFaced, "payload", property(_two_faced_payload))
    assert response.payload == {"reading": 1.5}
    assert response.payload == {"reading": 999.0}
    calls["n"] = 0
    result = _collect(adapter=FakeInMemoryAdapter(script=[response]))

    assert type(result.final_outcome) is Malformed
    assert result.final_outcome.schema_error_class == MALFORMED_ADAPTER_CONTRACT_BREACH
    # The lying property was never consulted: the response was refused by its TYPE.
    assert calls["n"] == 0


def test_a6_5_a_ledger_verdict_that_is_not_a_bool_is_refused():
    """A6-5, BASELINE. ``bool(ledger.admit_if_absent(key))`` was the defect, and the
    ``bool(...)`` was the whole of it: it COERCES.

    A ledger answering the string ``"already claimed"`` — an honest-looking answer, and a
    truthy one — reported a DUPLICATE source period as a FIRST claim. Idempotency is the
    property this component exists to hold, and it was decided by a supplied object's own
    truthiness.

    REFUSING LAYER: ``crash_detector.collectors.runner._established_ledger_verdict``, at the
    point of return from ``ReadingLedger.admit_if_absent`` — ``type(verdict) is not bool``.
    SCOPE OF THAT LAYER: every ledger verdict on every OK outcome.
    RENAME TEST: SURVIVES. Type identity; nothing consults ``admit_if_absent``'s spelling
    beyond the Protocol call itself.
    COUNTERFACTUAL (CD-D-079): ``variants/WO-2R3/V27-lying-ledger.patch`` restores the
    ``bool(...)`` coercion, and the same ledger makes a re-fetch of a claimed period report
    ``reading_admitted=True``.
    """

    class TruthyLedger:
        def admit_if_absent(self, key):
            return "already claimed"

    with pytest.raises(LedgerContractBreach) as refusal:
        _collect(ledger=TruthyLedger())
    assert "str" in str(refusal.value)


def test_a6_5_the_control_arm_a_real_bool_verdict_is_believed_in_both_directions():
    ledger = RecordingLedger()
    first = _collect(ledger=ledger)
    second = _collect(ledger=ledger)
    assert first.reading_admitted is True
    assert second.reading_admitted is False


def test_a6_6_a_validator_that_returns_a_repaired_payload_is_a_breach():
    """A6-6, BASELINE. The validator's RETURN was DISCARDED, so "conforming" meant only
    "did not raise".

    A validator that returns a repaired or coerced payload instead of raising was read as
    agreement — silent coercion at the one boundary whose entire job is to refuse it
    (Standards Baseline §4). The response is now recorded ``MALFORMED`` with a stable class.

    REFUSING LAYER: ``crash_detector.collectors.runner._attempt``, at the point of return
    from ``PayloadValidator.validate`` — ``verdict is not None``.
    SCOPE OF THAT LAYER: every validation of every response, including the shipped
    ``JsonSchemaValidator``'s.
    RENAME TEST: SURVIVES. The refusal is an identity comparison against ``None``.
    COUNTERFACTUAL (CD-D-079): ``variants/WO-2R3/V30-validator-return-discarded.patch``
    discards the verdict again, and the repairing validator's response is admitted as OK.
    """

    class RepairingValidator:
        def validate(self, payload, schema):
            return {"reading": 0.0}  # "I fixed it for you"

    result = _collect(validator=RepairingValidator())
    assert type(result.final_outcome) is Malformed
    assert (
        result.final_outcome.schema_error_class == MALFORMED_VALIDATOR_CONTRACT_BREACH
    )


def test_a6_6_the_control_arm_a_validator_that_returns_none_is_agreement():
    class SilentValidator:
        def validate(self, payload, schema):
            return None

    result = _collect(validator=SilentValidator())
    assert type(result.final_outcome) is OK


def test_a6_7_a_sink_that_answers_with_a_value_is_refused():
    """A6-7, BASELINE. ``ObservationSink.record`` returns ``None``; the return was ignored.

    The one guarantee this component makes is that the row exists. A sink improvising its
    own return protocol is a sink improvising its own idea of what "recorded" means, and the
    runner has no way to read it.

    REFUSING LAYER: ``crash_detector.collectors.runner._record``, at the point of return
    from ``ObservationSink.record``. SCOPE: every row written on every attempt.
    RENAME TEST: SURVIVES — an identity comparison against ``None``.
    """

    class ChattySink:
        def record(self, attempt):
            return "written, probably"

    with pytest.raises(SinkContractBreach):
        _collect(sink=ChattySink())


def test_a6_8_an_adapter_missing_a_protocol_member_is_refused_before_any_attempt():
    """A6-8, BASELINE. ``adapter.source_id`` was read straight off the supplied object.

    An adapter missing ``is_empty`` used to reach an ``AttributeError`` half way through an
    attempt and be recorded as ``UNCLASSIFIED_AttributeError`` — that is, as the SOURCE
    misbehaving. It is OUR wiring defect and it is now named as one, before any attempt is
    made and therefore before any row is owed.

    REFUSING LAYER: ``crash_detector.collectors.runner._established_adapter_identity`` via
    ``missing_adapter_members``, over the WHOLE of ``ADAPTER_PROTOCOL_MEMBERS``.
    SCOPE OF THAT LAYER: every ``collect`` call.
    **RENAME TEST: FAILS, AND THIS IS CD-BP-003.** ``hasattr`` asks for five SPELLED names.
    This refusal is a VOCABULARY and not a class, it is declared as one in ``collect``'s
    DECLARED LIMIT block, in ``required-tests.yaml`` and in the execution contract, and it
    is the softest surface in the product.
    """

    class NearlyAnAdapter:
        source_id = "src.e"
        adapter_id = "a.v0"
        response_schema = {"type": "object"}

        def fetch(self, *, timeout_seconds):  # pragma: no cover - never reached
            raise AssertionError("no attempt may be made")

    sink = RecordingSink()
    with pytest.raises(AdapterContractBreach) as refusal:
        _collect(adapter=NearlyAnAdapter(), sink=sink)
    assert "is_empty" in str(refusal.value)
    # No attempt was made, so no row is owed and none was written.
    assert sink.recorded == []


def test_a6_9_an_adapter_source_id_that_is_a_str_subclass_is_rebuilt_not_believed():
    """A6-9, BASELINE. ``source_id`` is the key the ENGINE looks an observation up by.

    ``source_id in usable`` is decided by the value's ``__hash__`` and ``__eq__``, so a
    ``str`` subclass can answer to a source id it is not — and whether a REQUIRED input was
    present is what decides a dial's reading. The id is rebuilt from its own code points by
    ``own_terms.own_str``, so what is stored is exact-type ``str`` this system built.

    REFUSING LAYER: ``crash_detector.own_terms.own_str``, called at the point of return from
    the adapter's ``source_id`` property. SCOPE: every ``collect`` call.
    RENAME TEST: SURVIVES — ``str.__str__`` is invoked as the BASE implementation; no name
    is consulted.
    """

    class AnswersToAnything(str):
        def __eq__(self, other):
            return True

        def __hash__(self):
            return hash("src.anything")

    adapter = FakeInMemoryAdapter(
        script=[_ok_response()], source_id=AnswersToAnything("src.e")
    )
    result = _collect(adapter=adapter)
    assert type(result.source_id) is str
    assert result.source_id.__class__ is not AnswersToAnything


def test_a6_9_an_adapter_whose_identity_is_not_a_string_at_all_is_refused():
    adapter = FakeInMemoryAdapter(script=[_ok_response()], adapter_id=7)
    with pytest.raises(AdapterContractBreach):
        _collect(adapter=adapter)


# ========================================================================================= #
# WHAT THIS BOUNDARY DOES *NOT* CLOSE — CD-BP-003, DEMONSTRATED RATHER THAN DESCRIBED.
# ========================================================================================= #


def test_cd_bp_003_a_structurally_conforming_adapter_is_admitted_whatever_it_says():
    """**THE DECLARED LIMIT, MEASURED AT THIS SEAT'S OWN WORK, IN THE POSITIVE DIRECTION.**

    This test asserts that something IS ADMITTED. It is here because a limit stated only in
    prose is a limit an auditor has to take on trust, and because the Product Owner named
    this boundary the fourth Assurance seat's first target.

    The object below supplies all five protocol members, returns an exact ``FetchedResponse``
    carrying a payload that conforms to the schema it itself declared, and answers ``False``
    to ``is_empty``. Every establishment §D.3 part 2 adds is satisfied. It is ADMITTED, and
    the reading it invents is recorded as an honest observation of a source that does not
    exist.

    **WHAT BOUNDS IT, MEASURED:** it cannot compute a dial value here — nothing under
    ``collectors/`` may import ``crash_detector.dials`` or ``crash_detector.engine``, and
    ``tests/test_collector_boundaries.py::test_no_collector_module_imports_the_dial_types_or_the_engine``
    asserts that over the whole package. Its observation still has to pass the staleness
    window and the required-input rules in ``engine.evaluate``, and over the SHIPPED empty
    source registry it contributes to no dial at all.

    **WHAT DOES NOT BOUND IT: NOT PROVED TO BE CARRIED ANYWHERE.** Nothing in this tree
    establishes that a conforming adapter is telling the truth. Source trust is CD-D-005 and
    BLUEPRINT §5, and it is OWED, not held. This seat does not claim otherwise and has not
    built a guard over it.
    """

    class ConformingButFictional:
        source_id = "src.does.not.exist"
        adapter_id = "fiction.v0"
        response_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "properties": {"reading": {"type": "number"}},
        }

        def fetch(self, *, timeout_seconds):
            return FetchedResponse(
                payload={"reading": 0.0},
                source_as_of_utc=FIXED_NOW - timedelta(seconds=1),
            )

        def is_empty(self, payload):
            return False

    assert missing_adapter_members(ConformingButFictional()) == ()
    result = _collect(adapter=ConformingButFictional())
    assert type(result.final_outcome) is OK
    assert result.final_outcome.payload == {"reading": 0.0}


def test_cd_bp_003_the_started_instant_is_type_established_and_not_truth_established():
    """The second half of the declared limit, also in the positive direction.

    A caller passing an instant from 2016 gets attempt rows dated 2016. The TYPE is
    established and the datetime is rebuilt from its own fields, so no method of the
    supplied object is consulted; the TRUTH is not established and nothing claims it is.

    CARRIER, for the one route that decides a dial: freshness is computed in
    ``engine.evaluate`` from the OUTCOME's ``source_as_of_utc`` against
    ``StalenessWindow``, not from the collector's instant. For attempt-row latency figures
    and operator forensics: NOT PROVED TO BE CARRIED ANYWHERE.
    """
    long_ago = datetime(2016, 1, 1, tzinfo=timezone.utc)
    sink = RecordingSink()
    _collect(started_utc=long_ago, sink=sink)
    assert sink.recorded[0].requested_utc.year == 2016


# ========================================================================================= #
# THE PREMISE — EVERY PLANT ABOVE RAN OVER THE SHIPPED EMPTY REGISTRIES.
# ========================================================================================= #


def test_every_plant_here_ran_over_the_empty_registries():
    """The collector path reads no registry, so the standing condition is asserted directly:
    nothing in this module registered a model row or an ingredient source, and the shipped
    registries are still empty after every plant above has run."""
    assert EMPTY_MODEL_REGISTRY.is_empty
    assert EMPTY_MODEL_REGISTRY.model_ids == ()
    assert EMPTY_SOURCE_REGISTRY.source_ids == ()
