"""CD-RT-008 — cadence breach alerting on the publication layer.

The declared command for ``CD-AC-008`` (``required-tests.yaml``,
``contracts/execution/CD-RT-008-CADENCE-BREACH-ALERTS.md``).

**THE PROPOSITION:** publication halted while ingestion continues raises an alert within one
publication cycle.

===========================================================================================
*** THE TWO CASES THAT COME APART, WHICH ARE THE WHOLE OF THIS FILE ***
===========================================================================================
    | scenario                                   | cadence  | data age |
    |--------------------------------------------|----------|----------|
    | a STALE number republished ON TIME         | HEALTHY  | STALE    |
    | a FRESH number published LATE              | BREACHED | FRESH    |

**An implementation that cannot tell these apart has not built CD-AC-008.** Both are
measured below, in ``test_a_stale_number_republished_on_time_...`` and
``test_a_fresh_number_published_late_...``, each asserting BOTH halves of its row — the
cadence verdict AND what the freshness instrument says about the same scenario — so the
divergence is demonstrated rather than described.

And the structural half: :func:`~crash_detector.publication.cadence.evaluate_cadence` has no
parameter through which the age of a number could reach it, asserted by introspecting the
signature, so the conflation is unrepresentable rather than merely absent.

**NO SOURCE IS REGISTERED BY ANYTHING IN THIS FILE** (``Q25``, ``CD-PL-F154``).
"""

from __future__ import annotations

import inspect
from datetime import datetime, timedelta, timezone

import pytest

from crash_detector.publication.alerting import (
    ALERT_CADENCE_BREACH,
    ALERT_CRITICAL,
    RAISED_BY_ENGINE,
    raise_alert,
)
from crash_detector.publication.cadence import (
    CADENCE_THRESHOLD_CEILING_SECONDS,
    CadenceBudget,
    CadenceBudgetIncoherent,
    CadenceVerdict,
    evaluate_cadence,
)
from crash_detector.publication.publish import publish_cycle
from crash_detector.staleness import (
    FreshnessEvidence,
    FreshnessNotEstablished,
    StalenessWindow,
)

from publication_fakes import RecordingConnection, private_envelope, public_envelope

NOW = datetime(2026, 8, 23, 12, 0, 0, tzinfo=timezone.utc)

#: 30 s cycle, one missed publish tolerated -> a 60 s breach threshold.
CYCLE_SECONDS = 30.0
BUDGET = CadenceBudget(publication_interval_seconds=CYCLE_SECONDS, missed_cycles_allowed=1)


def _heartbeats(*ages_seconds: float) -> list:
    """Heartbeat instants that many seconds before ``NOW``, oldest first."""
    return [NOW - timedelta(seconds=age) for age in sorted(ages_seconds, reverse=True)]


# --- THE CRITERION: PUBLICATION HALTS, AND IT IS DETECTED --------------------------------- #

def test_a_publisher_on_cadence_raises_nothing():
    """THE ADMITTING ARM. Normal cadence must be quiet, or the alarm is noise."""
    verdict = evaluate_cadence(_heartbeats(90, 60, 30, 0), now_utc=NOW, budget=BUDGET)
    assert verdict.breached is False
    assert verdict.worst_interval_seconds == 30.0


def test_publication_halted_is_a_breach():
    """THE REFUSING ARM. The last heartbeat is 5 cycles old and nothing has followed it."""
    verdict = evaluate_cadence(_heartbeats(210, 180, 150), now_utc=NOW, budget=BUDGET)
    assert verdict.breached is True
    assert verdict.open_interval_seconds == 150.0


def test_the_halt_is_detected_by_the_OPEN_interval_and_not_by_any_closed_one():
    """*** THE FAILURE MODE OF THE OBVIOUS IMPLEMENTATION. ***

    A publisher that has STOPPED writes no further heartbeat, so it creates no further gap.
    Every CLOSED interval here is a perfectly healthy 30 s; the only thing wrong is that
    nothing has happened since. A ``max(closed_intervals)`` implementation reports HEALTH
    about a dead detector, and this test is what fails if anyone writes one.
    """
    verdict = evaluate_cadence(_heartbeats(240, 210, 180), now_utc=NOW, budget=BUDGET)
    assert verdict.closed_intervals_seconds == (30.0, 30.0)
    assert max(verdict.closed_intervals_seconds) <= BUDGET.breach_threshold_seconds
    assert verdict.open_interval_seconds == 180.0
    assert verdict.breached is True


def test_a_detector_that_has_never_published_is_a_breach_and_not_an_unknown():
    verdict = evaluate_cadence([], now_utc=NOW, budget=BUDGET)
    assert verdict.breached is True
    assert verdict.heartbeat_count == 0
    # Not 0.0, which would read as "published just now".
    assert verdict.open_interval_seconds is None


def test_detection_happens_within_one_publication_cycle_of_the_breach():
    """PID §5: *a cadence breach alerts within one publication cycle.*

    The threshold is crossed at 60 s of silence. Evaluated at every cycle boundary, the
    FIRST evaluation at which the breach is visible is 60 s -- 90 s, i.e. within one cycle
    of the threshold being crossed. Walked rather than asserted about.
    """
    first_seen_at = None
    for elapsed in (0.0, 30.0, 60.0, 90.0):
        verdict = evaluate_cadence(
            [NOW], now_utc=NOW + timedelta(seconds=elapsed), budget=BUDGET
        )
        if verdict.breached and first_seen_at is None:
            first_seen_at = elapsed
    assert first_seen_at == 90.0
    assert first_seen_at - BUDGET.breach_threshold_seconds <= CYCLE_SECONDS


def test_a_breach_writes_a_durable_alert_row_first():
    """``Q26``: the row IS the alert. Written, committed, and nothing pushed anywhere."""
    connection = RecordingConnection()
    verdict = evaluate_cadence(_heartbeats(300), now_utc=NOW, budget=BUDGET)
    assert verdict.breached is True

    raise_alert(
        connection,
        event_class=ALERT_CADENCE_BREACH,
        severity=ALERT_CRITICAL,
        raised_by=RAISED_BY_ENGINE,
        subject_ref="publication.heartbeat:open_interval",
    )
    inserts = connection.statements_touching("alert.event")
    assert len(inserts) == 1
    assert inserts[0].startswith("INSERT INTO alert.event")
    assert ("commit", None, None) in connection.journal
    # The reference names a table and a field. No value from anywhere appears in it.
    (parameters,) = connection.parameters_for("alert.event")
    assert parameters == (
        ALERT_CADENCE_BREACH,
        ALERT_CRITICAL,
        RAISED_BY_ENGINE,
        "publication.heartbeat:open_interval",
    )


# ================================================================================== #
# *** CADENCE IS NOT AGE. THE TWO CASES, EACH WITH BOTH HALVES MEASURED. ***
# ================================================================================== #

def test_a_stale_number_republished_on_time_has_HEALTHY_cadence_and_STALE_data():
    """Case 1. The publisher is fine. The data is not. Cadence must say so — and must NOT
    invent a complaint about the number, because the number is not its business."""
    # The publisher has published every 30 s, right up to now.
    verdict = evaluate_cadence(_heartbeats(90, 60, 30, 0), now_utc=NOW, budget=BUDGET)
    assert verdict.breached is False, "cadence is healthy: it published on time"

    # ...and the number it kept republishing is two hours old.
    stale_as_of = NOW - timedelta(hours=2)
    with pytest.raises(FreshnessNotEstablished):
        FreshnessEvidence(
            as_of_utc=stale_as_of,
            observed_at_utc=NOW,
            window=StalenessWindow(seconds=600.0),
        )


def test_a_fresh_number_published_late_has_BREACHED_cadence_and_FRESH_data():
    """Case 2. The number is current. The pipeline stopped for a while. **Only cadence can
    see it**, and freshness is right to say nothing is wrong with the number."""
    # One publish, 10 minutes after the previous one: an excessive INTERVAL.
    verdict = evaluate_cadence(_heartbeats(600, 0), now_utc=NOW, budget=BUDGET)
    assert verdict.breached is True, "cadence is broken: a 600 s gap on a 60 s threshold"
    assert verdict.closed_intervals_seconds == (600.0,)

    # ...and the number it eventually published is current.
    evidence = FreshnessEvidence(
        as_of_utc=NOW - timedelta(seconds=5),
        observed_at_utc=NOW,
        window=StalenessWindow(seconds=600.0),
    )
    assert evidence.age_seconds == 5.0


def test_the_two_cases_produce_OPPOSITE_verdicts_from_the_two_instruments():
    """The point of the pair, asserted as one fact instead of left to be inferred."""
    on_time_stale = evaluate_cadence(
        _heartbeats(90, 60, 30, 0), now_utc=NOW, budget=BUDGET
    )
    late_fresh = evaluate_cadence(_heartbeats(600, 0), now_utc=NOW, budget=BUDGET)
    assert on_time_stale.breached != late_fresh.breached


def test_evaluate_cadence_CANNOT_BE_GIVEN_the_age_of_a_number():
    """*** THE STRUCTURAL HALF. ***

    The conflation is not prevented by a rule somebody could relax; it is prevented because
    there is no parameter through which a reading, an envelope or an ``as_of_utc`` could
    reach this function. Widening the signature fails here.
    """
    signature = inspect.signature(evaluate_cadence)
    assert list(signature.parameters) == ["heartbeats_utc", "now_utc", "budget"]

    forbidden = ("as_of_utc", "reading", "envelope", "dial", "score", "staleness", "age")
    for name in signature.parameters:
        assert name not in forbidden


def test_the_cadence_module_imports_no_staleness_judgement():
    """It borrows the CEILING constant from ``staleness`` and nothing that judges an age.

    Importing ``FreshnessEvidence`` here would be the first step of the conflation, so the
    import list is asserted rather than trusted.
    """
    import crash_detector.publication.cadence as module

    assert not hasattr(module, "FreshnessEvidence")
    assert not hasattr(module, "StalenessWindow")
    assert module.CADENCE_THRESHOLD_CEILING_SECONDS == 900.0


# --- THE BUDGET REFUSES WHAT IT MUST ------------------------------------------------------ #

def test_a_budget_that_alarms_on_correct_behaviour_is_refused():
    with pytest.raises(CadenceBudgetIncoherent) as refusal:
        CadenceBudget(publication_interval_seconds=30.0, missed_cycles_allowed=0)
    assert "PERFECTLY PUNCTUAL" in str(refusal.value)


def test_a_threshold_above_the_pid_detectability_budget_is_refused_not_clamped():
    with pytest.raises(CadenceBudgetIncoherent) as refusal:
        CadenceBudget(publication_interval_seconds=600.0, missed_cycles_allowed=1)
    assert "exceeds the ceiling" in str(refusal.value)
    assert "REFUSED, not" in str(refusal.value)


def test_a_budget_inside_the_ceiling_is_admitted():
    """THE ADMITTING ARM for the two refusals above."""
    budget = CadenceBudget(publication_interval_seconds=300.0, missed_cycles_allowed=1)
    assert budget.breach_threshold_seconds == 600.0
    assert budget.breach_threshold_seconds <= CADENCE_THRESHOLD_CEILING_SECONDS


@pytest.mark.parametrize("bad", [0.0, -1.0, float("inf"), float("nan"), True, "30"])
def test_an_unusable_publication_interval_is_refused(bad):
    with pytest.raises(CadenceBudgetIncoherent):
        CadenceBudget(publication_interval_seconds=bad, missed_cycles_allowed=1)


def test_missed_cycles_must_be_a_whole_number_of_cycles():
    with pytest.raises(CadenceBudgetIncoherent) as refusal:
        CadenceBudget(publication_interval_seconds=30.0, missed_cycles_allowed=1.5)
    assert "WHOLE NUMBER OF PUBLICATION CYCLES" in str(refusal.value)


def test_a_bare_number_is_not_a_budget():
    with pytest.raises(TypeError):
        evaluate_cadence([NOW], now_utc=NOW, budget=60.0)


def test_the_budget_may_not_be_subclassed():
    with pytest.raises(TypeError):
        class Lenient(CadenceBudget):  # pragma: no cover - class body never runs
            pass


def test_heartbeat_order_does_not_change_the_verdict():
    """A caller's ``ORDER BY`` must not be able to decide whether the detector is healthy."""
    ascending = _heartbeats(240, 210, 180)
    verdict_a = evaluate_cadence(ascending, now_utc=NOW, budget=BUDGET)
    verdict_b = evaluate_cadence(list(reversed(ascending)), now_utc=NOW, budget=BUDGET)
    assert verdict_a.breached == verdict_b.breached
    assert verdict_a.worst_interval_seconds == verdict_b.worst_interval_seconds


def test_the_verdict_carries_no_envelope_and_no_dial():
    """A verdict about cadence that carried a reading would be a place for one to leak."""
    verdict = evaluate_cadence([NOW], now_utc=NOW, budget=BUDGET)
    assert isinstance(verdict, CadenceVerdict)
    assert set(CadenceVerdict.__slots__) == {
        "breached",
        "worst_interval_seconds",
        "open_interval_seconds",
        "closed_intervals_seconds",
        "heartbeat_count",
        "budget",
    }


# --- THE HEARTBEAT IS WRITTEN, WHICH IS WHAT THE INTERVALS ARE MEASURED BETWEEN ----------- #

def test_a_successful_publish_writes_a_heartbeat():
    """CD-AC-008's other half: without this row there are no intervals to measure.

    ``grep -rn heartbeat src/ --include=*.py`` returned NO MATCHES at this increment's base.
    """
    connection = RecordingConnection()
    outcome = publish_cycle(
        connection,
        public_envelope=public_envelope(),
        private_envelope=private_envelope(),
    )
    assert outcome.heartbeat_written is True
    heartbeats = connection.statements_touching("publication.heartbeat")
    assert len(heartbeats) == 1
    assert heartbeats[0].startswith("INSERT INTO publication.heartbeat")


def test_a_refused_publish_writes_NO_heartbeat():
    """A heartbeat on a cycle that published nothing is the one lie this table forbids."""
    from crash_detector.publication.envelope_contract import PublicationRefused

    connection = RecordingConnection()
    with pytest.raises(PublicationRefused):
        publish_cycle(
            connection,
            public_envelope=public_envelope(combined_stress=0.9),
            private_envelope=private_envelope(),
        )
    assert connection.statements_touching("publication.heartbeat") == []
