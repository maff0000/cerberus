"""``evaluate`` — the pure core, and the empty-registry UNKNOWN path (CD-AC-001).

The headline test of this increment is
:func:`test_with_no_sources_declared_both_dials_read_unknown` — the WO-2 shipped state,
which must be ``Unknown`` and must never be a number.

``FakeModel`` below is a TEST DOUBLE. It exists only to reach the code paths that a real
contribution model will one day reach; no model is registered in the application
(``CONTRIBUTION_MODELS`` is empty, CD-D-005), and inventing one there would be inventing
product meaning.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass

import pytest

from crash_detector.dials.dialset import EQUITY_DIAL_ID, MONETARY_DIAL_ID, DialSet
from crash_detector.dials.reading import (
    AbsenceYieldedAValue,
    Degraded,
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
from crash_detector.engine.model import CONTRIBUTION_MODELS, ScoreComputation
from crash_detector.observations import (
    OK,
    Empty,
    FetchFailed,
    Malformed,
    ObservationRecord,
)
from crash_detector.source_registry import Criticality, SourceRecord, SourceRegistry

from conftest import FIXED_NOW, WINDOW_SECONDS, ago
from dial_magnitudes import magnitude_of


# --- test doubles, clearly named as such ---------------------------------------------- #

@dataclass(frozen=True)
class FakeModel:
    """TEST DOUBLE. Returns a fixed magnitude regardless of payload."""

    magnitude: float = 0.42

    @property
    def model_id(self) -> str:
        return "fake.model.v0"

    def compute(self, payloads) -> ScoreComputation:
        return ScoreComputation(
            magnitude=self.magnitude,
            contributions=tuple(
                Contribution(
                    source_id=source_id, category="fake", weight=1.0, contribution=0.1
                )
                for source_id in sorted(payloads)
            ),
        )


@dataclass(frozen=True)
class ExplodingModel:
    """TEST DOUBLE. A model that cannot compute honestly must raise, not return zero."""

    @property
    def model_id(self) -> str:
        return "fake.exploding.v0"

    def compute(self, payloads) -> ScoreComputation:
        raise ArithmeticError("model cannot compute")


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
    )


def _spec(dial_id, required=(), contributing=(), model=None) -> DialSpec:
    return DialSpec(
        dial_id=dial_id,
        required_input_ids=tuple(required),
        contributing_input_ids=tuple(contributing),
        contribution_model=model,
    )


def _ok(source_id, seconds_ago) -> ObservationRecord:
    return ObservationRecord(
        source_id=source_id,
        observed_utc=FIXED_NOW,
        outcome=OK(payload={"v": 1}, source_as_of_utc=ago(seconds_ago)),
    )


# --- THE SHIPPED WO-2 STATE ------------------------------------------------------------ #

def test_the_application_registers_no_contribution_model():
    """CD-D-005 is the Product Owner's and is owed before WO-3 (BLUEPRINT §16)."""
    assert dict(CONTRIBUTION_MODELS) == {}


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
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=FakeModel()),
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
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=FakeModel()),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    reading = evaluate([record], config, FIXED_NOW).equity
    assert isinstance(reading, Unknown), (
        "an outcome that is not OK must not contribute, however OK-shaped it looks"
    )


def test_a_missing_required_input_forces_unknown():
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=FakeModel()),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    reading = evaluate([], config, FIXED_NOW).equity
    assert isinstance(reading, Unknown)
    assert reading.missing_inputs == ("src.a",)


def test_a_stale_required_input_forces_unknown_and_never_the_previous_value():
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=FakeModel()),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    fresh = evaluate([_ok("src.a", 10)], config, FIXED_NOW).equity
    assert isinstance(fresh, Value)

    stale = evaluate([_ok("src.a", WINDOW_SECONDS + 1)], config, FIXED_NOW).equity
    assert isinstance(stale, Unknown), "a stale input must not carry the last reading"


def test_a_future_dated_observation_is_not_treated_as_fresh():
    """Without this, one bad upstream clock makes a reading permanently current — a
    stale value rendering as calm, reached by the back door rather than by a default."""
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=FakeModel()),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    reading = evaluate([_ok("src.a", -86400)], config, FIXED_NOW).equity
    assert isinstance(reading, Unknown)
    assert reading.missing_inputs == ("src.a",)


def test_a_missing_contributing_input_degrades_rather_than_hiding_the_damage():
    config = _snapshot(
        equity_spec=_spec(
            EQUITY_DIAL_ID, required=("src.a",), contributing=("src.b",),
            model=FakeModel(),
        ),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    reading = evaluate([_ok("src.a", 10)], config, FIXED_NOW).equity
    assert isinstance(reading, Degraded)
    assert reading.reason == REASON_CONTRIBUTING_INPUTS_UNAVAILABLE
    assert reading.missing_inputs == ("src.b",)


def test_a_model_that_cannot_compute_raises_rather_than_returning_a_number():
    """Swallowing it would publish "we have no data" when the truth is "our code is
    broken", and returning zero would publish calm. Neither is honest, so it travels."""
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=ExplodingModel()),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    with pytest.raises(ArithmeticError):
        evaluate([_ok("src.a", 10)], config, FIXED_NOW)


# --- the happy path, so the absence paths are not passing by accident --------------------- #

def test_a_satisfied_dial_reads_value_with_its_inputs_named():
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a", "src.b"),
                          model=FakeModel()),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    reading = evaluate(
        [_ok("src.a", 10), _ok("src.b", 20)], config, FIXED_NOW
    ).equity
    assert isinstance(reading, Value)
    assert isinstance(reading.value, EquityCrashScore)
    assert reading.inputs_used == ("src.a", "src.b")


def test_a_reading_is_only_as_fresh_as_its_oldest_input():
    """Taking the newest would make a reading look fresher than the data behind it."""
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a", "src.b"),
                          model=FakeModel()),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    reading = evaluate(
        [_ok("src.a", 10), _ok("src.b", 500)], config, FIXED_NOW
    ).equity
    assert reading.as_of_utc == ago(500)


def test_the_latest_observation_per_source_wins():
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=FakeModel()),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    reading = evaluate(
        [_ok("src.a", 500), _ok("src.a", 10), _ok("src.a", 400)], config, FIXED_NOW
    ).equity
    assert reading.as_of_utc == ago(10)


def test_each_dial_carries_its_own_score_type():
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=FakeModel()),
        monetary_spec=_spec(MONETARY_DIAL_ID, required=("src.a",), model=FakeModel()),
    )
    dials = evaluate([_ok("src.a", 10)], config, FIXED_NOW)
    assert isinstance(dials.equity.value, EquityCrashScore)
    assert isinstance(dials.monetary.value, MonetaryDebasementScore)


def test_one_dial_being_unknown_does_not_disturb_the_other():
    """Two dials, two evaluators, no aggregation stage."""
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=FakeModel()),
        monetary_spec=_spec(MONETARY_DIAL_ID, required=("src.missing",),
                            model=FakeModel()),
    )
    dials = evaluate([_ok("src.a", 10)], config, FIXED_NOW)
    assert isinstance(dials.equity, Value)
    assert isinstance(dials.monetary, Unknown)


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
    the escape that produced CD-ASR-F03 was an edit to the body."""
    import importlib

    evaluate_module = importlib.import_module("crash_detector.engine.evaluate")

    assert hasattr(evaluate_module._evaluate_dial, "__wrapped__"), (
        "the per-dial evaluator must be wrapped in refuse_a_number_without_its_inputs; "
        "without it, any rewritten branch may return a number (CD-ASR-F03)"
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
    spec = _spec(EQUITY_DIAL_ID, required=("src.a",), model=FakeModel())
    with pytest.raises(AbsenceYieldedAValue):
        refuse_a_number_without_its_inputs(spec, {}, reading)


def test_a_value_bearing_reading_with_no_contribution_model_is_refused():
    """A dial with inputs and no declared mapping cannot produce an explicable number.

    ``DialSpec`` refuses this combination at construction, so the spec is built and then
    re-pointed: the post-condition must not depend on another constructor's vigilance.
    """
    spec = _spec(EQUITY_DIAL_ID, required=("src.a",), model=FakeModel())
    object.__setattr__(spec, "contribution_model", None)
    usable = {"src.a": OK(payload={"v": 1}, source_as_of_utc=ago(10))}
    with pytest.raises(AbsenceYieldedAValue):
        refuse_a_number_without_its_inputs(spec, usable, _value_reading())


def test_the_post_condition_permits_a_value_when_every_required_input_was_present():
    """FALSE-POSITIVE CHECK. A guard that forbids the product is not a guard."""
    spec = _spec(EQUITY_DIAL_ID, required=("src.a",), model=FakeModel())
    usable = {"src.a": OK(payload={"v": 1}, source_as_of_utc=ago(10))}
    refuse_a_number_without_its_inputs(spec, usable, _value_reading())
    refuse_a_number_without_its_inputs(spec, usable, _degraded_reading())


@pytest.mark.parametrize(
    ("required", "model", "usable_ids"),
    [
        ((), None, ()),
        (("src.a",), FakeModel(), ()),
        (("src.a",), FakeModel(), ("src.a",)),
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
    spec = _spec(EQUITY_DIAL_ID, required=("src.a",), model=FakeModel())
    assert required_inputs_are_all_present(spec, {}) is False
    assert required_inputs_are_all_present(spec, present) is True
    object.__setattr__(spec, "contribution_model", None)
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
        equity_spec = _spec(EQUITY_DIAL_ID, required=("src.a",), model=FakeModel())
        monetary_spec = _spec(MONETARY_DIAL_ID)
        config = ConfigSnapshot(
            config_snapshot_id="cfg-old",
            dial_specs=(equity_spec, monetary_spec),
            staleness_window_seconds=window,
            source_registry=_registry_for(equity_spec, monetary_spec),
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
