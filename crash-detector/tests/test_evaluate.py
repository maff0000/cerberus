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
from crash_detector.dials.reading import Degraded, Unknown, Value
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
)
from crash_detector.engine.model import CONTRIBUTION_MODELS, ScoreComputation
from crash_detector.observations import (
    OK,
    Empty,
    FetchFailed,
    Malformed,
    ObservationRecord,
)

from conftest import FIXED_NOW, WINDOW_SECONDS, ago


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


def _snapshot(*, equity_spec: DialSpec, monetary_spec: DialSpec) -> ConfigSnapshot:
    return ConfigSnapshot(
        config_snapshot_id="cfg-test",
        dial_specs=(equity_spec, monetary_spec),
        staleness_window_seconds=WINDOW_SECONDS,
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
        [_ok("src.a", 10), _ok("src.b", 900)], config, FIXED_NOW
    ).equity
    assert reading.as_of_utc == ago(900)


def test_the_latest_observation_per_source_wins():
    config = _snapshot(
        equity_spec=_spec(EQUITY_DIAL_ID, required=("src.a",), model=FakeModel()),
        monetary_spec=_spec(MONETARY_DIAL_ID),
    )
    reading = evaluate(
        [_ok("src.a", 900), _ok("src.a", 10), _ok("src.a", 400)], config, FIXED_NOW
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
