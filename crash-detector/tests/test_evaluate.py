"""``evaluate`` — the pure core, and the empty-registry UNKNOWN path (CD-AC-001).

The headline test of this file is
:func:`test_with_no_sources_declared_both_dials_read_unknown` — the WO-2 shipped state,
which must be ``Unknown`` and must never be a number.

====================================================================================
WHAT BP-AMENDMENT-0001 §C CHANGED IN THIS FILE, AND WHAT IT COST
====================================================================================

There used to be two test doubles here — ``FakeModel``, which returned a fixed magnitude,
and ``ExplodingModel``, which raised. **BOTH ARE DELETED, BECAUSE THE THING THEY WERE
DOUBLES OF IS DELETED.** ``ContributionModel`` was a caller-supplied object and §C removes
the field that held one; a double for a type that cannot exist is not a test, it is a
fossil.

In their place a dial that names a model names it BY ID, and the model registry the
snapshot carries is derived from what the dials declare — the same mechanical derivation
``_registry_for`` already does for the source registry, and for the same reason: not one
assertion should have to move to accommodate a new field, because a test edited to
accommodate new code is how a guard quietly stops guarding.

**THE HONEST CONSEQUENCE, STATED RATHER THAN LEFT TO BE NOTICED.**
:class:`~crash_detector.engine.model.MappingKind` ships with exactly one member and that
member COMPUTES NOTHING (PO-DECISIONS-0005 ruling 2). So under every configuration this
product can currently construct, a fully-supplied dial reaches
:func:`~crash_detector.engine.mapping.compute` and is REFUSED with
:exc:`~crash_detector.engine.mapping.UnspecifiedMapping`. No dial number exists anywhere,
by design, until CD-D-005 lands.

That means the value-bearing tail of ``_evaluate_dial`` — score-type selection, provenance
stamping, ``_oldest_as_of`` — is **no longer reachable end to end**, and the tests that
reached it that way could not survive unchanged. Each has been REPLACED, not dropped: the
replacement asserts the same proposition against the structure that now carries it, either
at the executor boundary or against the helper that owns the rule. Every old node id, its
successor and the reason are named in the commit that lands this file (the deleted-subject
rule of the WO-2R3 dispatch). Where a proposition genuinely lost coverage, the test that
replaced it says so in its own docstring rather than in a report nobody reads next to the
code.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
# IMPORTED AT MODULE LEVEL SINCE WO-2R3 INCREMENT 8 AND NOT ONLY INSIDE ONE TEST: the
# redesigned CD-ASR-F03 mechanism RESOLVES the annotations of the body it is applied to
# (`typing.get_type_hints`), and a test body annotated with a name this module cannot resolve
# would fail at decoration for a reason that has nothing to do with what it is testing.
from datetime import datetime

import pytest

from crash_detector.dials.dialset import EQUITY_DIAL_ID, MONETARY_DIAL_ID, DialSet
from crash_detector.dials.reading import (
    AbsenceYieldedAValue,
    Degraded,
    Reading,
    Unknown,
    Value,
)
from crash_detector.dials.magnitude import DialMagnitude
from crash_detector.dials.scores import (
    Contribution,
    EquityCrashScore,
    MonetaryDebasementScore,
)
from crash_detector.engine.config import ConfigSnapshot, DialSpec, empty_config_snapshot
from crash_detector.engine.evaluate import (
    REASON_CONTRIBUTING_INPUTS_UNAVAILABLE,
    REASON_NO_REQUIRED_INPUTS,
    REASON_REQUIRED_INPUTS_UNAVAILABLE,
    evaluate,
    refuse_a_number_without_its_inputs,
    required_inputs_are_all_present,
)
from crash_detector.engine.mapping import UnspecifiedMapping
from crash_detector.engine.model import (
    EMPTY_MODEL_REGISTRY,
    MappingKind,
    ModelProvenance,
    ModelRegistry,
    ModelSpec,
)
from crash_detector.observations import (
    OK,
    Empty,
    FetchFailed,
    Malformed,
    ObservationRecord,
)
from crash_detector.source_registry import EMPTY_INDICATOR_MAPPING_REGISTRY
from crash_detector.source_registry import Criticality, SourceRecord, SourceRegistry

from conftest import FIXED_NOW, WINDOW_SECONDS, ago
from dial_magnitudes import magnitude_of


# --- test doubles, clearly named as such ---------------------------------------------- #
#
# THERE IS NO MODEL DOUBLE HERE ANY MORE, AND THAT IS THE POINT. A model is DATA now, so a
# test that wants a dial to name one registers a ROW, exactly as the application would.
# Nothing below is an object with a `compute` method, because no field on the dial path can
# hold one.

#: Passed as `model=` to :func:`_spec` to say "this dial names a model". The model itself is
#: DERIVED by :func:`_model_registry_for` from what the dial declares, so a test never states
#: the same input set twice and can never state it two ways.
DECLARES_A_MODEL = object()

#: The provenance every derived test row carries. Text, and obviously test text: WO-2
#: registers zero models and CD-D-005 is the Product Owner's (BLUEPRINT §16).
TEST_PROVENANCE = ModelProvenance(
    stands_for="TEST DOUBLE; WO-2 registers no model",
    account="TEST DOUBLE; the account of a real mapping is CD-D-005 and is owed",
    decided_by="TEST DOUBLE; no product decision registers a model in WO-2",
)


def _model_id_for(dial_id: str) -> str:
    return f"model.{dial_id}.test"


def _model_registry_for(*specs: DialSpec) -> ModelRegistry:
    """A model registry carrying exactly one row per spec that names a model.

    Each derived row MIRRORS its dial's declared inputs, so ``ConfigSnapshot``'s third
    invariant — a model may not read an input its dial did not declare — is satisfied by
    construction rather than by a second list a test could get wrong. Its ``mapping`` is
    ``UNSPECIFIED``, because that is the only member there is and shipping a second one
    would be inventing product meaning (CD-RULE-003, ``PBG-AUTH-005``).
    """
    return ModelRegistry(
        models=tuple(
            ModelSpec(
                model_id=spec.model_ref,
                dial_id=spec.dial_id,
                required_input_ids=spec.required_input_ids,
                contributing_input_ids=spec.contributing_input_ids,
                mapping=MappingKind.UNSPECIFIED,
                parameters=(),
                provenance=TEST_PROVENANCE,
            )
            for spec in specs
            if spec.model_ref is not None
        )
    )


def _registry_for(*specs: DialSpec) -> SourceRegistry:
    """A registry that registers exactly the sources ``specs`` name, at the criticality
    the set they appear in implies.

    ADDED IN WO-2 INCREMENT 2, and deliberately mechanical. ``ConfigSnapshot`` gained a
    required ``source_registry`` field with deliverable A4, plus the invariants that every
    named input is registered and that its criticality agrees with the set it is named in.
    These tests already declare the sources they mean; this derives the registry rows that
    say the same thing, so that not one assertion below had to move to accommodate the new
    field. A test edited to accommodate new code is how a guard quietly stops guarding.
    """
    implied: dict[str, Criticality] = {}
    for spec in specs:
        for source_id in spec.required_input_ids:
            _imply(implied, source_id, Criticality.REQUIRED)
        for source_id in spec.contributing_input_ids:
            _imply(implied, source_id, Criticality.CONTRIBUTING)
    return SourceRegistry(
        sources=tuple(
            SourceRecord(
                source_id=source_id,
                adapter_id="fake.adapter.v0",
                cadence_seconds=60,
                criticality=criticality,
                stands_for="TEST DOUBLE source; no ingredient is registered in WO-2",
            )
            for source_id, criticality in implied.items()
        )
    )


def _imply(
    implied: dict[str, Criticality], source_id: str, criticality: Criticality
) -> None:
    """One registry ROW per source, because that is what ``raw.source_registry`` is.

    A source feeding both dials gets one row, not two. A source that two dials would want
    at DIFFERENT criticalities is a conflict this helper refuses rather than silently
    picks a winner for — see finding CD-ENG-F08, raised because BLUEPRINT §5 models
    criticality as a property of the SOURCE and not of the (source, dial) pair.
    """
    existing = implied.get(source_id)
    if existing is not None and existing is not criticality:
        raise AssertionError(
            f"test declares {source_id!r} as both {existing.value} and "
            f"{criticality.value}; BLUEPRINT §5 gives a source one criticality"
        )
    implied[source_id] = criticality


def _snapshot(*, equity_spec: DialSpec, monetary_spec: DialSpec) -> ConfigSnapshot:
    return ConfigSnapshot(
        config_snapshot_id="cfg-test",
        dial_specs=(equity_spec, monetary_spec),
        staleness_window_seconds=WINDOW_SECONDS,
        source_registry=_registry_for(equity_spec, monetary_spec),
        indicator_mapping_registry=EMPTY_INDICATOR_MAPPING_REGISTRY,
        model_registry=_model_registry_for(equity_spec, monetary_spec),
    )


def _spec(dial_id, required=(), contributing=(), model=None) -> DialSpec:
    return DialSpec(
        dial_id=dial_id,
        required_input_ids=tuple(required),
        contributing_input_ids=tuple(contributing),
        model_ref=_model_id_for(dial_id) if model is not None else None,
    )


def _ok(source_id, seconds_ago) -> ObservationRecord:
    return ObservationRecord(
        source_id=source_id,
        observed_utc=FIXED_NOW,
        outcome=OK(payload={"v": 1}, source_as_of_utc=ago(seconds_ago)),
    )


# --- THE SHIPPED WO-2 STATE ------------------------------------------------------------ #

def test_the_application_registers_no_model():
    """CD-D-005 is the Product Owner's and is owed before WO-3 (BLUEPRINT §16).

    REPLACES ``test_the_application_registers_no_contribution_model``, whose subject
    (``CONTRIBUTION_MODELS``) BP-AMENDMENT-0001 §C deletes. Same proposition — the
    application registers no model — asserted against the structure that now carries it,
    and asserted three ways because ``is_empty`` is a property a future row could make
    lie about while ``models`` said otherwise.
    """
    assert EMPTY_MODEL_REGISTRY.is_empty
    assert EMPTY_MODEL_REGISTRY.models == ()
    assert EMPTY_MODEL_REGISTRY.model_ids == ()
    config = empty_config_snapshot("cfg-wo2", staleness_window_seconds=WINDOW_SECONDS)
    assert config.model_registry is EMPTY_MODEL_REGISTRY


def test_with_no_sources_declared_both_dials_read_unknown():
    """The doctrinally correct empty state.

    Zero satisfied requirements is NOT "all requirements satisfied". An engine that
    answered anything else here would violate CD-AC-001 on its first commit.
    """
    config = empty_config_snapshot("cfg-wo2", staleness_window_seconds=WINDOW_SECONDS)
    dials = evaluate([], config, FIXED_NOW)

    assert isinstance(dials, DialSet)
    for reading in (dials.equity, dials.monetary):
        assert isinstance(reading, Unknown)
        assert reading.reason == REASON_NO_REQUIRED_INPUTS
        assert not hasattr(reading, "value")


def test_the_empty_state_is_unknown_even_when_observations_happen_to_be_present():
    """Observations from sources no dial declares must not conjure a reading."""
    config = empty_config_snapshot("cfg-wo2", staleness_window_seconds=WINDOW_SECONDS)
    dials = evaluate([_ok("src.unregistered", 10)], config, FIXED_NOW)
    assert isinstance(dials.equity, Unknown)
    assert isinstance(dials.monetary, Unknown)


# --- purity ----------------------------------------------------------------------------- #

def test_evaluate_has_the_blueprint_signature():
    parameters = list(inspect.signature(evaluate).parameters)
    assert parameters == ["observations", "config_snapshot", "now_utc"]


def test_evaluate_is_deterministic_for_the_same_arguments():
    config = empty_config_snapshot("cfg-wo2", staleness_window_seconds=WINDOW_SECONDS)
    first = evaluate([], config, FIXED_NOW)
    second = evaluate([], config, FIXED_NOW)
    assert first == second


def test_evaluate_does_not_consult_the_clock():
    """`now_utc` is an argument so a historical evaluation replays exactly. If evaluate
    read the wall clock, the reading's timestamp would not track the argument."""
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    earlier = evaluate([], config, ago(86400))
    assert earlier.equity.since_utc == ago(86400)


def test_evaluate_does_not_mutate_its_inputs():
    observations = [_ok("src.a", 10)]
    snapshot = list(observations)
    config = empty_config_snapshot("cfg-wo2", staleness_window_seconds=WINDOW_SECONDS)
    evaluate(observations, config, FIXED_NOW)
    assert observations == snapshot


def test_importing_the_engine_does_not_pull_in_the_witness_package():
    """CD-AC-003 held in the import graph; the store holds the same separation again.

    Run in a clean subprocess rather than against this process's ``sys.modules``, which
    the rest of the suite has already polluted by importing the witness package directly.
    Checking the transitive closure catches the variant where the edge is added two or
    three modules down, not only a direct `from crash_detector.witness import ...`.
    """
    import pathlib
    import subprocess
    import sys

    src = str(pathlib.Path(__file__).resolve().parent.parent / "src")
    probe = (
        "import sys; import crash_detector.engine; "
        "leaked=[m for m in sys.modules if m.startswith('crash_detector.witness')]; "
        "print(','.join(sorted(leaked)))"
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", probe],
        capture_output=True,
        text=True,
        timeout=60,
        env={"PYTHONPATH": src, "PATH": "/usr/bin:/bin"},
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "", (
        f"crash_detector.engine reaches the witness package: {completed.stdout.strip()}"
    )


# --- absence never becomes a number ------------------------------------------------------ #

@pytest.mark.parametrize(
    "outcome",
    [
        FetchFailed(error_class="CONNECT_TIMEOUT"),
        FetchFailed(error_class="HTTP", http_status=503),
        Malformed(schema_error_class="TYPE_MISMATCH"),
        Empty(),
    ],
    ids=["fetch_failed", "http_error", "malformed", "empty"],
)
def test_a_non_ok_outcome_never_produces_a_dial_contribution(outcome):
    """Each of the three collapsed absences, separately. None is a value."""
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=DECLARES_A_MODEL),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    record = ObservationRecord(
        source_id="src.a", observed_utc=FIXED_NOW, outcome=outcome
    )
    reading = evaluate([record], config, FIXED_NOW).equity
    assert isinstance(reading, Unknown)
    assert reading.reason == REASON_REQUIRED_INPUTS_UNAVAILABLE
    assert reading.missing_inputs == ("src.a",)


def test_an_outcome_that_merely_looks_like_ok_is_not_accepted_as_one():
    """Usability must be decided by TYPE IDENTITY, not by duck typing.

    Found by mutation: replacing ``isinstance(outcome, OK)`` with
    ``hasattr(outcome, "source_as_of_utc")`` passed the rest of this file, because none of
    today's three failure outcomes carries a source timestamp. It is an equivalent mutant
    *today* and a live hole *tomorrow* — the moment A4 or A5 adds a constructor that
    carries a period (an ``EMPTY`` with a source_as_of_utc, say), a non-``OK`` outcome
    would start contributing to a dial. This test fixes the property now, while it is
    cheap.

    The record is built through the real constructor and then re-pointed, because
    ``ObservationRecord`` correctly refuses a non-member of the sum type at construction;
    the look-alike stands in for a future member.
    """
    look_alike = type(
        "FutureEmptyWithPeriod",
        (),
        {"payload": {"v": 1}, "source_as_of_utc": ago(10)},
    )()
    record = ObservationRecord(
        source_id="src.a", observed_utc=FIXED_NOW, outcome=Empty()
    )
    object.__setattr__(record, "outcome", look_alike)

    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=DECLARES_A_MODEL),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    reading = evaluate([record], config, FIXED_NOW).equity
    assert isinstance(reading, Unknown), (
        "an outcome that is not OK must not contribute, however OK-shaped it looks"
    )


def test_a_missing_required_input_forces_unknown():
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=DECLARES_A_MODEL),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    reading = evaluate([], config, FIXED_NOW).equity
    assert isinstance(reading, Unknown)
    assert reading.missing_inputs == ("src.a",)


def test_a_stale_required_input_forces_unknown_and_never_the_previous_value():
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=DECLARES_A_MODEL),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    # THE CONTRAST ARM. It used to read `assert isinstance(fresh, Value)`; §C's one
    # non-computing mapping means a fully-supplied dial now REACHES the executor and is
    # refused there instead of returning a number. What the arm is FOR is unchanged: it
    # shows the stale arm's Unknown is caused by the staleness and not by the dial being
    # incapable of getting that far.
    with pytest.raises(UnspecifiedMapping):
        evaluate([_ok("src.a", 10)], config, FIXED_NOW)

    stale = evaluate([_ok("src.a", WINDOW_SECONDS + 1)], config, FIXED_NOW).equity
    assert isinstance(stale, Unknown), "a stale input must not carry the last reading"


def test_a_future_dated_observation_is_not_treated_as_fresh():
    """Without this, one bad upstream clock makes a reading permanently current — a
    stale value rendering as calm, reached by the back door rather than by a default."""
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=DECLARES_A_MODEL),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    reading = evaluate([_ok("src.a", -86400)], config, FIXED_NOW).equity
    assert isinstance(reading, Unknown)
    assert reading.missing_inputs == ("src.a",)


def test_a_missing_contributing_input_does_not_force_unknown_the_way_a_required_one_does():
    """REPLACES ``test_a_missing_contributing_input_degrades_rather_than_hiding_the_damage``.

    PROPOSITION PRESERVED: a missing CONTRIBUTING input is a different thing from a missing
    REQUIRED one — the required one stops the dial dead, the contributing one does not. That
    is asserted here by contrast, in both directions, against the same configuration.

    **PROPOSITION LOST, AND SAID PLAINLY:** that the resulting reading is specifically
    ``Degraded``, carrying ``REASON_CONTRIBUTING_INPUTS_UNAVAILABLE`` and naming the missing
    source. That branch sits BELOW the executor call, and with one non-computing
    ``MappingKind`` member no configuration reaches it. It is not dead code — it becomes
    reachable the moment CD-D-005 registers a computing mapping — but nothing here can drive
    it today. ``Degraded``'s own construction and fields remain covered by
    ``tests/test_reading.py`` and by the post-condition tests below, which build one
    directly; what is NOT covered until a computing member exists is ``_evaluate_dial``
    CHOOSING it. Raised as a coverage residue in this increment's Build Log rather than
    papered over.
    """
    config = _snapshot(
        equity_spec=_spec(
            EQUITY_DIAL_ID, required=("src.a",), contributing=("src.b",),
            model=DECLARES_A_MODEL,
        ),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    # The contributing input is absent — and the dial still gets as far as the executor.
    with pytest.raises(UnspecifiedMapping):
        evaluate([_ok("src.a", 10)], config, FIXED_NOW)

    # The REQUIRED input absent instead: the dial stops before the executor, with the
    # missing source named. The two arms differ in exactly the way BLUEPRINT §5's
    # criticality table says they must.
    reading = evaluate([_ok("src.b", 10)], config, FIXED_NOW).equity
    assert isinstance(reading, Unknown)
    assert reading.reason == REASON_REQUIRED_INPUTS_UNAVAILABLE
    assert reading.missing_inputs == ("src.a",)


def test_an_executor_that_cannot_compute_raises_rather_than_returning_a_number():
    """REPLACES ``test_a_model_that_cannot_compute_raises_rather_than_returning_a_number``,
    whose subject was a caller-supplied model object that raised — a thing §C makes
    unconstructible.

    PROPOSITION PRESERVED EXACTLY, and it is the one that matters: **a refusal from the
    mapping travels.** It is not caught in ``_evaluate_dial`` and turned into a number, and
    it is not caught and turned into ``Unknown`` either. Swallowing it would publish "we
    have no data" when the truth is "there is no declared mapping"; returning zero would
    publish calm. Neither is honest, so it travels out of ``evaluate`` to the caller.

    The exception is now raised by the ENGINE'S OWN executor rather than by a double, which
    makes the proposition stronger rather than weaker: there is no longer any caller code in
    the call stack at all.
    """
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=DECLARES_A_MODEL),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    with pytest.raises(UnspecifiedMapping) as raised:
        evaluate([_ok("src.a", 10)], config, FIXED_NOW)
    assert not isinstance(raised.value, (int, float))
    assert not hasattr(raised.value, "magnitude"), (
        "a refusal must not carry a magnitude; a caught exception with a number on it is a "
        "number standing in for an absence with an extra step"
    )


# --- the supplied path, so the absence paths are not passing by accident ------------------ #
#
# THIS SECTION USED TO BE HEADED "the happy path". There is no happy path any more: with one
# non-computing MappingKind member, a dial that gets EVERYTHING still ends at a refusal. The
# tests below are the successors of the four that asserted a number, and each names its
# predecessor and says what survived and what did not. The contrast they exist to provide —
# that the Unknown branches above are caused by absence rather than by the dial being unable
# to get that far — is preserved in full, because reaching the executor is as far as any
# configuration can go.

def test_a_satisfied_dial_reaches_the_executor_with_its_inputs_named():
    """REPLACES ``test_a_satisfied_dial_reads_value_with_its_inputs_named``.

    PROPOSITION PRESERVED: a dial whose required inputs are all present gets all the way to
    the mapping, carrying exactly the inputs it declared and no others. That is asserted
    from the refusal itself, which names the model, the dial and the input set the executor
    was handed.

    PROPOSITION LOST: that the result is a ``Value`` carrying an ``EquityCrashScore``. No
    mapping computes, so no dial number exists. The score types are asserted as a table in
    ``test_each_dial_has_its_own_unrelated_score_type`` below.
    """
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a", "src.b"),
                          model=DECLARES_A_MODEL),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    with pytest.raises(UnspecifiedMapping) as raised:
        evaluate([_ok("src.a", 10), _ok("src.b", 20)], config, FIXED_NOW)
    message = str(raised.value)
    assert "'src.a', 'src.b'" in message, message
    assert _model_id_for(EQUITY_DIAL_ID) in message, message
    assert EQUITY_DIAL_ID in message, message


def test_a_reading_is_only_as_fresh_as_its_oldest_input():
    """Taking the newest would make a reading look fresher than the data behind it.

    NODE ID UNCHANGED, SUBJECT MOVED. It used to assert ``reading.as_of_utc`` off a ``Value``
    that ``evaluate`` returned; that branch is below the executor and is unreachable while
    no mapping computes. The RULE it was testing lives in ``_oldest_as_of``, which is
    unchanged by this amendment, so the test now exercises the rule where the rule is rather
    than through a return value that no longer occurs.
    """
    from crash_detector.engine.evaluate import _oldest_as_of

    usable = {
        "src.a": OK(payload={"v": 1}, source_as_of_utc=ago(10)),
        "src.b": OK(payload={"v": 1}, source_as_of_utc=ago(500)),
    }
    assert _oldest_as_of(usable, ("src.a", "src.b")) == ago(500)
    assert _oldest_as_of(usable, ("src.b", "src.a")) == ago(500), (
        "the oldest input wins whatever order the used ids arrive in"
    )


def test_the_latest_observation_per_source_wins():
    """NODE ID UNCHANGED, SUBJECT MOVED, for the same reason as the test above.

    ``_latest_usable_ok`` is the function that decides this and it is untouched by
    BP-AMENDMENT-0001; the assertion used to reach it through a ``Value``'s ``as_of_utc``
    and now reaches it directly. The window is taken from a real snapshot rather than
    constructed here, so the admission door is still the only way to get one.
    """
    from crash_detector.engine.evaluate import _latest_usable_ok

    config = empty_config_snapshot("cfg-wo2", staleness_window_seconds=WINDOW_SECONDS)
    usable = _latest_usable_ok(
        [_ok("src.a", 500), _ok("src.a", 10), _ok("src.a", 400)],
        now_utc=FIXED_NOW,
        window=config.window(),
    )
    assert sorted(usable) == ["src.a"]
    assert usable["src.a"].source_as_of_utc == ago(10)


def test_each_dial_has_its_own_unrelated_score_type():
    """REPLACES ``test_each_dial_carries_its_own_score_type``.

    PROPOSITION PRESERVED: the two dials are different KINDS of thing (PID §3.1) and the
    engine's own table says so — two dials, two unrelated types, neither a subclass of the
    other, so no arithmetic between them is expressible.

    PROPOSITION LOST: that a live evaluation stamps each dial's reading with its own type.
    No evaluation produces a value while no mapping computes. What replaces the end-to-end
    half is stronger in one respect and weaker in another, and both are stated: **a model
    row is bound to ONE dial** (§C.4), so the cross-dial route the old test's contrast
    guarded against is now refused at construction — see
    ``tests/test_engine_model_registry.py``'s P3.
    """
    from crash_detector.engine.evaluate import DIAL_SCORE_TYPES

    assert DIAL_SCORE_TYPES[EQUITY_DIAL_ID] is EquityCrashScore
    assert DIAL_SCORE_TYPES[MONETARY_DIAL_ID] is MonetaryDebasementScore
    assert not issubclass(EquityCrashScore, MonetaryDebasementScore)
    assert not issubclass(MonetaryDebasementScore, EquityCrashScore)


def test_one_dial_being_unknown_does_not_disturb_the_other():
    """Two dials, two evaluators, no aggregation stage. NODE ID UNCHANGED.

    It used to assert ``equity is Value`` and ``monetary is Unknown``. The equity half is
    now a refusal rather than a number, so the contrast is made the other way round and in
    both directions: whichever dial is the SATISFIED one, the refusal that comes out names
    THAT dial's own model, which is only possible if the two evaluations are independent
    and neither consulted the other's inputs.
    """
    equity_satisfied = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=DECLARES_A_MODEL),
        monetary_spec=_spec(MONETARY_DIAL_ID, required=("src.missing",),
                            model=DECLARES_A_MODEL),
    )
    with pytest.raises(UnspecifiedMapping) as raised:
        evaluate([_ok("src.a", 10)], equity_satisfied, FIXED_NOW)
    assert _model_id_for(EQUITY_DIAL_ID) in str(raised.value)

    monetary_satisfied = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.missing",),
                          model=DECLARES_A_MODEL),
        monetary_spec=_spec(MONETARY_DIAL_ID, required=("src.a",),
                            model=DECLARES_A_MODEL),
    )
    with pytest.raises(UnspecifiedMapping) as raised:
        evaluate([_ok("src.a", 10)], monetary_satisfied, FIXED_NOW)
    assert _model_id_for(MONETARY_DIAL_ID) in str(raised.value)

    # And the dial that did NOT get its input is still Unknown when the other one does not
    # raise at all — both dials absent, no aggregation, two independent Unknowns.
    neither = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.missing",),
                          model=DECLARES_A_MODEL),
        monetary_spec=_spec(MONETARY_DIAL_ID, required=("src.other",),
                            model=DECLARES_A_MODEL),
    )
    dials = evaluate([], neither, FIXED_NOW)
    assert isinstance(dials.equity, Unknown)
    assert isinstance(dials.monetary, Unknown)
    assert dials.equity.missing_inputs == ("src.missing",)
    assert dials.monetary.missing_inputs == ("src.other",)


def test_evaluate_refuses_a_naive_now():
    from datetime import datetime

    from crash_detector.time_utc import NaiveTimestampRejected

    config = empty_config_snapshot("cfg-wo2", staleness_window_seconds=WINDOW_SECONDS)
    with pytest.raises(NaiveTimestampRejected):
        evaluate([], config, datetime(2026, 8, 19, 12, 0, 0))


# ======================================================================================= #
# THE ABSENCE POST-CONDITION — CD-ASR-F03 (MEDIUM), escaped variant E04
#
# E04 replaced the missing-required branch with a Value whose magnitude came from a
# module-level constant. The AST guard enumerated four spellings of a numeric default and
# this was a fifth. These tests assert the post-condition that makes the SPELLING
# irrelevant: a reading that carries a value is a CLAIM that inputs were present, and the
# claim is checked against the inputs the dial was given.
# ======================================================================================= #

def _unknown_reading():
    return Unknown(reason="R", since_utc=FIXED_NOW, missing_inputs=("src.a",))


def _value_reading():
    return Value(
        value=EquityCrashScore(
            # MECHANICS ONLY (CD-ASR-F01, CD-PL-F54): the magnitude carries its dial
            # as data, and its NUMBER carries a declared provenance of its own.
            score=magnitude_of(EQUITY_DIAL_ID, 0.0),
            contributions=(),
        ),
        as_of_utc=FIXED_NOW,
        inputs_used=("src.a",),
    )


def _degraded_reading():
    return Degraded(
        value=EquityCrashScore(
            # MECHANICS ONLY (CD-ASR-F01, CD-PL-F54): the magnitude carries its dial
            # as data, and its NUMBER carries a declared provenance of its own.
            score=magnitude_of(EQUITY_DIAL_ID, 0.0),
            contributions=(),
        ),
        as_of_utc=FIXED_NOW,
        missing_inputs=("src.a",),
        reason="R",
    )


def test_the_per_dial_evaluator_carries_the_post_condition():
    """The guard is applied AT the function boundary, not written into its body, because
    the escape that produced CD-ASR-F03 was an edit to the body.

    **THE INTENT OF THIS TEST IS UNCHANGED. ITS INSTRUMENT IS REPLACED, AND THAT IS
    ``PO-DECISIONS-0013`` RULING 2** — *"a test that requires a bypass to exist pins the
    bypass open, and a test that asserts a vulnerability is a defect in the test."*

    **THE SUPERSEDED ASSERTION, QUOTED RATHER THAN DELETED** (CD-RULE-004, PBG-CONT-003)::

        assert hasattr(evaluate_module._evaluate_dial, "__wrapped__"), (
            "the per-dial evaluator must be wrapped in refuse_a_number_without_its_inputs; "
            "without it, any rewritten branch may return a number (CD-ASR-F03)")

    **THE ONLY SHIPPED ASSERTION THAT THE CD-ASR-F03 GUARD WAS APPLIED WAS THE PRESENCE OF
    THE ATTRIBUTE THAT REMOVES IT.** The fifth Assurance seat demonstrated the bypass live —
    through the wrapper a rewritten branch is REFUSED, through ``__wrapped__`` the same
    branch is ACCEPTED and returns a ``Value`` carrying inputs that were never present — and
    the test and the defect were the same line. That is why three parties looked at this
    wrapper across WO-2R, WO-2R2 and WO-2R3 and saw a guard.

    Four assertions replace it, each testing the property the docstring actually claims, and
    none of them a way through the guard.
    """
    import importlib

    evaluate_module = importlib.import_module("crash_detector.engine.evaluate")

    # -------------------------------------------------------------- 1. THE NEGATIVE.
    # The same practice as this project's two other delattr sites, whose carriers are
    # tests/test_admission.py:334 and tests/test_field_establishment.py:215.
    # THREE SITES, ONE PRACTICE, THREE CARRIERS.
    assert not hasattr(evaluate_module._evaluate_dial, "__wrapped__"), (
        "the CD-ASR-F03 guard must not publish a documented way round itself; `admits` "
        "and `establishes` both delete this attribute and call it a bypass"
    )
    assert inspect.unwrap(evaluate_module._evaluate_dial) is evaluate_module._evaluate_dial

    # -------------------------------------------------------------- 2. THE GUARD FIRES ON
    # THE REAL OBJECT. Not "an attribute is present" — the post-condition is OBSERVED being
    # called, with the real arguments, at the real boundary.
    seen = []
    real_post_condition = evaluate_module.refuse_a_number_without_its_inputs
    try:
        evaluate_module.refuse_a_number_without_its_inputs = (
            lambda spec, usable, reading: seen.append((spec, usable, reading))
        )
        evaluate_module._evaluate_dial(_spec(EQUITY_DIAL_ID), {}, FIXED_NOW)
    finally:
        evaluate_module.refuse_a_number_without_its_inputs = real_post_condition
    assert len(seen) == 1, "the post-condition was not called at the evaluator's boundary"
    observed_spec, observed_usable, observed_reading = seen[0]
    assert observed_spec.dial_id == EQUITY_DIAL_ID
    assert observed_usable == {}
    assert isinstance(observed_reading, Unknown)

    # -------------------------------------------------------------- 3. THE GUARD IS AT THE
    # BOUNDARY AND SURVIVES ANY BODY — the docstring's actual claim, with the counterfactual
    # arm CD-D-079 requires. The decorator is applied to a body that returns a value-bearing
    # reading having received no inputs at all: CD-ASR-F03's own shape.
    # **THE BODY CARRIES ANNOTATIONS AND NO OPEN CHANNEL SINCE WO-2R3 INCREMENT 8, AND THAT
    # IS NOT COSMETIC.** *Superseded (PBG-CONT-003 — corrections supersede, never edit):*
    # ``def rewritten_body(spec, usable, now_utc, *extra, **extra_by_name):``
    # The mechanism DERIVES its establishment from the signature now, so an unannotated
    # parameter and an open channel are BOTH REFUSED AT DECORATION — property (b) of
    # `PO-DECISIONS-0015` ruling 1. Both refusals are asserted, with their own arms, in
    # ``tests/test_the_absence_door.py``, which is where the full attack lives.
    def rewritten_body(spec: "DialSpec", usable: dict, now_utc: "datetime") -> "Reading":
        return _value_reading()

    starved = _spec(EQUITY_DIAL_ID, required=("src.a",), model=DECLARES_A_MODEL)
    guarded = evaluate_module._absence_is_never_a_number(rewritten_body)
    with pytest.raises(AbsenceYieldedAValue):
        guarded(starved, {}, FIXED_NOW)
    # THE COUNTERFACTUAL: the identical body WITHOUT the decorator does not refuse. Two arms
    # differing in exactly the structure the proposition credits.
    assert isinstance(rewritten_body(starved, {}, FIXED_NOW), Value)

    # -------------------------------------------------------------- 4. THE HALF THAT WAS
    # DECLARED OPEN IS CLOSED — AND THE OLD ASSERTION FIRED ON THE FIX, WHICH IS THE ONLY
    # REASON ANYBODY COULD TELL.
    #
    # **SUPERSEDED AT WO-2R3 INCREMENT 8** (`PBG-CONT-003` — corrections supersede, never
    # edit). The old text, verbatim:
    #
    #     reachable = [cell.cell_contents
    #                  for cell in (evaluate_module._evaluate_dial.__closure__ or ())
    #                  if callable(getattr(cell, "cell_contents", None))]
    #     assert reachable, (
    #         "the closure route is DECLARED OPEN; if it has closed, the declared limit in "
    #         "engine/evaluate.py, admission.py and establishment.py is now wrong and must be "
    #         "corrected in all three CD-RULE-004 places rather than quietly enjoyed")
    #
    # **THAT ASSERTION DID EXACTLY WHAT IT SAID IT WOULD DO.** `PO-DECISIONS-0015` ruling 1
    # (a) made *"no undecorated evaluator object exists at runtime"* the acceptance property;
    # the redesign carries the body as a CODE OBJECT and no callable form of it survives; and
    # this assertion WENT RED on the increment that closed the route it pinned open. The limit
    # it named is corrected in all three CD-RULE-004 places rather than quietly enjoyed, and
    # the residue that replaces it — `types.FunctionType(code, globals)` RECONSTITUTES a
    # callable body from the materials still in the cells — is DECLARED LIMIT 10 and is
    # CARRIED, asserted TRUE, by
    # `tests/test_the_absence_door.py::test_the_reconstitution_residue_is_real_and_is_declared_limit_10`.
    #
    # **THE FULL ATTACK IS `tests/test_the_absence_door.py`, WHICH WALKS `__closure__`,
    # `__wrapped__`, `__globals__` AND THE MODULE NAMESPACE WITH A COUNTERFACTUAL ARM, AND IT
    # IS NOT DUPLICATED HERE.** This is the one line of it that belongs beside the
    # post-condition's own carrier.
    reachable = [
        cell.cell_contents
        for cell in (evaluate_module._evaluate_dial.__closure__ or ())
        if callable(getattr(cell, "cell_contents", None))
    ]
    assert not reachable, (
        "A CALLABLE IS REACHABLE THROUGH THE GUARD'S OWN CLOSURE. `PO-DECISIONS-0015` "
        "ruling 1 (a) calls a wrapper that keeps the naked callable alive in a cell THE "
        "DEFECT CLASS, not an implementation choice. Found: "
        + repr([getattr(c, "__qualname__", c) for c in reachable])
    )


@pytest.mark.parametrize(
    "reading", [_value_reading(), _degraded_reading()], ids=["value", "degraded"]
)
def test_a_value_bearing_reading_from_a_dial_with_no_required_inputs_is_refused(reading):
    """The WO-2 shipped state. Zero requirements satisfied is not all satisfied."""
    with pytest.raises(AbsenceYieldedAValue):
        refuse_a_number_without_its_inputs(_spec(EQUITY_DIAL_ID), {}, reading)


@pytest.mark.parametrize(
    "reading", [_value_reading(), _degraded_reading()], ids=["value", "degraded"]
)
def test_a_value_bearing_reading_with_a_required_input_missing_is_refused(reading):
    """E04's proposition, refused at runtime and without asking where the number came
    from: a literal, a module constant, a config default and a carried previous value all
    fail here identically, because what is refused is the claim and not the arithmetic."""
    spec = _spec(EQUITY_DIAL_ID, required=("src.a",), model=DECLARES_A_MODEL)
    with pytest.raises(AbsenceYieldedAValue):
        refuse_a_number_without_its_inputs(spec, {}, reading)


def test_a_value_bearing_reading_from_a_dial_naming_no_model_is_refused():
    """A dial with inputs and no declared mapping cannot produce an explicable number.

    REPLACES ``test_a_value_bearing_reading_with_no_contribution_model_is_refused``. Same
    proposition, same mechanism, same one-line body — only the field it re-points is
    renamed, because ``contribution_model`` no longer exists and ``model_ref`` is what a
    dial now carries.

    ``DialSpec`` refuses this combination at construction, so the spec is built and then
    re-pointed: the post-condition must not depend on another constructor's vigilance.
    """
    spec = _spec(EQUITY_DIAL_ID, required=("src.a",), model=DECLARES_A_MODEL)
    object.__setattr__(spec, "model_ref", None)
    usable = {"src.a": OK(payload={"v": 1}, source_as_of_utc=ago(10))}
    with pytest.raises(AbsenceYieldedAValue):
        refuse_a_number_without_its_inputs(spec, usable, _value_reading())


def test_the_post_condition_permits_a_value_when_every_required_input_was_present():
    """FALSE-POSITIVE CHECK. A guard that forbids the product is not a guard."""
    spec = _spec(EQUITY_DIAL_ID, required=("src.a",), model=DECLARES_A_MODEL)
    usable = {"src.a": OK(payload={"v": 1}, source_as_of_utc=ago(10))}
    refuse_a_number_without_its_inputs(spec, usable, _value_reading())
    refuse_a_number_without_its_inputs(spec, usable, _degraded_reading())


@pytest.mark.parametrize(
    ("required", "model", "usable_ids"),
    [
        ((), None, ()),
        (("src.a",), DECLARES_A_MODEL, ()),
        (("src.a",), DECLARES_A_MODEL, ("src.a",)),
    ],
    ids=["no_requirements", "requirement_missing", "requirement_present"],
)
def test_unknown_is_never_refused_because_the_guard_is_one_directional(
    required, model, usable_ids
):
    """A body returning Unknown where a number was available is the SAFE direction, and a
    guard that compelled a number would push against PID §3.2 rather than for it."""
    spec = _spec(EQUITY_DIAL_ID, required=required, model=model)
    usable = {
        source_id: OK(payload={"v": 1}, source_as_of_utc=ago(10))
        for source_id in usable_ids
    }
    refuse_a_number_without_its_inputs(spec, usable, _unknown_reading())


def test_the_presence_predicate_answers_for_each_of_the_three_ways_inputs_can_be_absent():
    present = {"src.a": OK(payload={"v": 1}, source_as_of_utc=ago(10))}
    assert required_inputs_are_all_present(_spec(EQUITY_DIAL_ID), present) is False
    spec = _spec(EQUITY_DIAL_ID, required=("src.a",), model=DECLARES_A_MODEL)
    assert required_inputs_are_all_present(spec, {}) is False
    assert required_inputs_are_all_present(spec, present) is True
    object.__setattr__(spec, "model_ref", None)
    assert required_inputs_are_all_present(spec, present) is False


# --- CD-ASR-F06 on the DIAL path: the same class, the other comparison site --------------- #
#
# CD-ASR-F06 was reported against the serving resolver. There are TWO implementations of the
# same age comparison in this tree, and bounding only the one the auditor happened to attack
# would have closed the instance and not the class: the engine takes its window from the
# config snapshot and performs its own comparison, so an unbounded configured window makes a
# decade-old observation feed a dial exactly as it made a decade-old row render agreement.
# The admission door is shared, so both sites are closed by the same structure.

TEN_YEARS_SECONDS = 3650 * 24 * 3600.0


@pytest.mark.parametrize(
    "window", [1e18, 901.0, 3600.0, 86400.0, TEN_YEARS_SECONDS, 1e308]
)
def test_a_config_snapshot_refuses_a_window_above_the_ceiling(window):
    """The configuration cannot even be constructed, so no evaluation can run against it."""
    from crash_detector.staleness import StalenessWindowOutOfRange

    with pytest.raises(StalenessWindowOutOfRange):
        empty_config_snapshot("cfg-wide", staleness_window_seconds=window)


def test_the_config_snapshot_still_refuses_the_windows_it_already_refused():
    """No regression of the half of the door that was already closed."""
    import math

    from crash_detector.staleness import StalenessWindowOutOfRange

    for window in (math.inf, math.nan, 0.0, -1.0):
        with pytest.raises(StalenessWindowOutOfRange):
            empty_config_snapshot("cfg-bad", staleness_window_seconds=window)
    with pytest.raises(TypeError):
        empty_config_snapshot("cfg-bad", staleness_window_seconds="600")


def test_the_admitted_window_is_a_type_and_not_the_raw_field():
    """`window()` is what the evaluation applies. The float field is the RECORD of what was
    configured; the type is the thing that may be used."""
    from crash_detector.staleness import StalenessWindow

    config = empty_config_snapshot("cfg-wo2", staleness_window_seconds=WINDOW_SECONDS)
    assert isinstance(config.window(), StalenessWindow)
    assert config.window().seconds == WINDOW_SECONDS


def test_a_decade_old_observation_is_not_usable_under_any_constructible_window():
    """The dial-path equivalent of E07's row.

    Whatever window a caller configures — and the widest it can configure is the ceiling —
    a ten-year-old observation is not carried forward as a value.
    """
    from crash_detector.staleness import STALENESS_WINDOW_CEILING_SECONDS

    for window in (1.0, 60.0, 600.0, STALENESS_WINDOW_CEILING_SECONDS):
        equity_spec = _spec(EQUITY_DIAL_ID, required=("src.a",), model=DECLARES_A_MODEL)
        monetary_spec = _spec(MONETARY_DIAL_ID)
        config = ConfigSnapshot(
            config_snapshot_id="cfg-old",
            dial_specs=(equity_spec, monetary_spec),
            staleness_window_seconds=window,
            source_registry=_registry_for(equity_spec, monetary_spec),
            indicator_mapping_registry=EMPTY_INDICATOR_MAPPING_REGISTRY,
            model_registry=_model_registry_for(equity_spec, monetary_spec),
        )
        reading = evaluate([_ok("src.a", TEN_YEARS_SECONDS)], config, FIXED_NOW).equity
        assert isinstance(reading, Unknown)
        assert reading.reason == "REQUIRED_INPUTS_UNAVAILABLE"


def test_the_private_usable_filter_cannot_be_called_with_an_unadmitted_window():
    """The route that would otherwise remain: call the helper directly with a bare number.

    It takes a StalenessWindow, so there is no bare number to pass — and the only way to
    obtain one is to construct it, which is the admission.
    """
    from crash_detector.engine.evaluate import _latest_usable_ok

    signature = inspect.signature(_latest_usable_ok)
    assert "staleness_window_seconds" not in signature.parameters
    assert "window" in signature.parameters
    with pytest.raises(AttributeError):
        _latest_usable_ok(
            [_ok("src.a", TEN_YEARS_SECONDS)],
            now_utc=FIXED_NOW,
            window=1e18,  # type: ignore[arg-type]
        )
