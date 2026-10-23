"""THE DIAL'S OFFICIAL STATE OVER TIME: persistence, the second leg, rule 5's gate.

WO-1.3a round 5, extended by WO-1.3e round 1 (R2D2's finding B2 — ``ALARM``'s exit path,
under "ALARM's exit path" below) and round 3 (R2D2's UNKNOWN-exit floor, under "leaving
UNKNOWN"). :func:`evaluator.resolve.official_state_for_dial` is the half of spec §3's
state machine that HAS a memory — ``test_engine_candidate_state.py`` covers the half that
does not, and nothing in that file constructs a history. So everything under test here is a
property of a SEQUENCE: what the dial officially says given its preceding rows and one
reading's numbers.

====================================================================================
NO STORE IS OPENED. THE HISTORY IS CONSTRUCTED.
====================================================================================

The unit takes a tuple of :class:`evaluator.history_store.MachineStateRow` most-recent-first
and returns one more, unwritten — so these tests build the rows directly instead of
appending through :class:`~evaluator.history_store.MachineStateHistoryStore` and reading
them back. ``test_machine_state_history.py`` is where the file, the CHECK constraints and
``recent()``'s ordering are proven against a real SQLite; routing through it here would put
a store between the input and the assertion while removing the ability to place a preceding
row's ``persistence_counter`` exactly where a transition boundary is.

The rows are nonetheless rows that store WOULD accept: a resolvable row carries every
statistic and an UNKNOWN row carries none (CD-RT-001), because a history of rows the schema
refuses could not occur and a test built on one would prove nothing about production.

====================================================================================
THE READINGS ARE NAMED FOR THE CANDIDATE THEY COMPUTE, AND THAT NAMING IS ASSERTED
====================================================================================

Every test below feeds one of five readings — :func:`calm_reading`,
:func:`watch_reading`, :func:`alarm_reading`, :func:`recovering_reading`,
:func:`unknown_reading` — built in ``test_engine_candidate_state.py``'s "constructed, not
piped" style: :class:`~crash_detector.engine.statistics.Acute` and ``Count`` directly, so a
master's score sits exactly where a threshold is.

:func:`test_the_readings_in_this_file_compute_the_candidates_they_are_named_for` runs all
five through :func:`~crash_detector.engine.statistics.candidate_state_for_one_reading`
itself. That test exists so that every later assertion is about the RESOLVER: when a test
says "fed an ALARM candidate, the official state becomes ALARM immediately", the premise
that the reading really is an ALARM candidate has been established rather than assumed.

EVERY NUMBER HERE IS A FIXTURE CHOSEN AGAINST A PROVISIONAL THRESHOLD (PO-DECISIONS-0025
r3: ``PROVISIONAL_WARNING`` 0.6, ``PROVISIONAL_STRESS`` 0.85, ``PROVISIONAL_EXIT`` 0.5,
``PROVISIONAL_BREADTH_MID`` 0.35, ``PROVISIONAL_BREADTH_HIGH`` 0.55) and claims nothing
about any indicator's real distribution. The thresholds, ``PROVISIONAL_PERSISTENCE`` and
``BREADTH_LOOKBACK_ROWS`` are compared against the CONSTANTS wherever the comparison is the
point, so a recalibration in WO-1.3b moves the fixtures with them instead of silently
inverting what a test proves.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from crash_detector.dials.dialset import DIAL_IDS
from crash_detector.dials.scores import EQUITY_DIAL_ID
from crash_detector.engine import statistics as engine_statistics
from crash_detector.engine.statistics import (
    PROVISIONAL_ACUTE_RISE_DEADBAND,
    PROVISIONAL_BREADTH_RISE_DEADBAND,
    PROVISIONAL_EXIT,
    PROVISIONAL_STRESS,
    PROVISIONAL_WARNING,
    Acute,
    AcuteUnknown,
    Count,
    MasterScore,
    State,
    candidate_state_for_one_reading,
)
from evaluator.history_store import _STATISTIC_COLUMNS, MachineStateRow
from evaluator.resolve import (
    BREADTH_LOOKBACK_ROWS,
    PROVISIONAL_PERSISTENCE,
    _acute_rising,
    _breadth_rows_ago,
    official_state_for_dial,
)

#: The dial every reading and every row below belongs to, read from the declaring module.
DIAL = EQUITY_DIAL_ID

#: THE OTHER DECLARED DIAL, for the cross-dial refusal — derived from
#: :data:`crash_detector.dials.dialset.DIAL_IDS` rather than retyped, so a PID amendment
#: renaming it cannot leave this test asserting about a dial that no longer exists.
OTHER_DIAL = next(dial_id for dial_id in DIAL_IDS if dial_id != DIAL)

#: A fixed instant. Nothing here reads a clock: ``as_of`` is an argument and ``written_utc``
#: is the store's business at append time, not this function's.
AS_OF = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)

#: One evaluation cadence apart. A FIXTURE SPACING and not a product cadence: the resolver
#: counts ROWS and never reads ``as_of`` to decide anything (the persistence count is
#: defined over the append order, which is why ``recent()`` orders by row id).
A_CADENCE = timedelta(minutes=15)

#: A master score in the hysteresis gap — above :data:`PROVISIONAL_EXIT`, below
#: :data:`PROVISIONAL_WARNING`. The one band where rules 2, 4 and 5 are all false at once,
#: which is what makes a CALM candidate constructible.
QUIET = 0.55

#: At warning, under stress: rule 4's master limb and nothing above it.
AT_WARNING = 0.70

#: At or beyond stress: rule 2, on its own, with breadth and count held calm.
AT_STRESS = 0.90

#: Every master back under its exit threshold — rule 5's first condition.
UNDER_EXIT = (0.40, 0.20)


def _acute_of(*scores: float) -> Acute:
    """An :class:`Acute` whose masters carry exactly ``scores``, highest one named.

    ``master_1``, ``master_2``, ... are FIXTURE NAMES, for ``test_engine_masters.py``'s
    reason: no rule in spec §3 reads a master id, and naming these after real masters would
    suggest the scores were real readings of them.

    **EVERY MASTER HERE IS ``alarm_eligible=True``, AND THAT IS A CHOICE THIS FILE MAKES ON
    PURPOSE.** The subject of this file is the WRAPPER — persistence counting, the previous
    state, the second-leg rule — and a WATCH-only master would change which CANDIDATE comes
    out of :func:`candidate_state_for_one_reading` before the wrapper ever ran, so the
    readings below would no longer be the candidates they are named for. Spec §3 rule 2's
    eligibility restriction (WO-1.3e, R2D2's finding B3) is measured in
    ``test_engine_candidate_state.py``, where the candidate is the subject.
    """
    masters = tuple(
        MasterScore(
            master_id=f"master_{position}",
            dial_id=DIAL,
            score=score,
            warning_threshold=PROVISIONAL_WARNING,
            stress_threshold=PROVISIONAL_STRESS,
            exit_threshold=PROVISIONAL_EXIT,
            alarm_eligible=True,
        )
        for position, score in enumerate(scores, start=1)
    )
    highest = max(masters, key=lambda master: master.score)
    return Acute(
        dial_id=DIAL,
        score=highest.score,
        from_master_id=highest.master_id,
        masters=masters,
    )


def _count_of(at_or_beyond: int, considered: int = 6) -> Count:
    """A :class:`Count` of ``at_or_beyond`` indicators out of ``considered``."""
    names = tuple(f"indicator_{position}" for position in range(considered))
    return Count(at_or_beyond=names[:at_or_beyond], considered=names)


def _unknown_acute(dial_id: str = DIAL) -> AcuteUnknown:
    """A dial whose acute statistic could not be computed, with the absence explained."""
    return AcuteUnknown(
        dial_id=dial_id,
        unknown_master_ids=("master_1",),
        missing_component_ids=("some_indicator",),
    )


def _candidate(reading: dict) -> State:
    """The CANDIDATE a reading calls for. ``alarm_lock_armed`` is the wrapper's argument, not the candidate function's."""
    stats = {k: v for k, v in reading.items() if k != "alarm_lock_armed"}
    return candidate_state_for_one_reading(breadth_20_rows_ago=None, **stats)


def calm_reading(**overrides) -> dict:
    """RULE 6. Masters parked in the hysteresis gap, breadth low, nothing counted."""
    return {
        "breadth": 0.20,
        "acute": _acute_of(QUIET, QUIET),
        "count": _count_of(0),
        "trend_confirmed": False,
        "alarm_lock_armed": False,
        **overrides,
    }


def watch_reading(**overrides) -> dict:
    """RULE 4, MASTER LIMB. One master at warning; breadth and count plainly calm."""
    return {
        "breadth": 0.20,
        "acute": _acute_of(AT_WARNING, 0.10),
        "count": _count_of(0),
        "trend_confirmed": False,
        "alarm_lock_armed": False,
        **overrides,
    }


def alarm_reading(**overrides) -> dict:
    """RULE 2. One master at stress, with the calmest possible breadth and count."""
    return {
        "breadth": 0.0,
        "acute": _acute_of(AT_STRESS, 0.10),
        "count": _count_of(0),
        "trend_confirmed": False,
        "alarm_lock_armed": False,
        **overrides,
    }


def recovering_reading(**overrides) -> dict:
    """RULE 5, AS FAR AS ONE READING CAN SATISFY IT: every master under exit, trend confirmed.

    Whether this is a RECOVERY is the resolver's to decide and is the whole subject of
    :func:`test_rule_5s_previous_state_gate_corrects_the_candidate_before_persistence`.
    """
    return {
        "breadth": 0.10,
        "acute": _acute_of(*UNDER_EXIT),
        "count": _count_of(0),
        "trend_confirmed": True,
        "alarm_lock_armed": False,
        **overrides,
    }


def unknown_reading(**overrides) -> dict:
    """RULE 1. An acute statistic that does not exist, so there is no number to judge."""
    return {
        "breadth": 0.0,
        "acute": _unknown_acute(),
        "count": _count_of(0),
        "trend_confirmed": False,
        "alarm_lock_armed": False,
        **overrides,
    }


def _row(
    machine_state: State,
    *,
    candidate: State | None = None,
    counter: int = 0,
    dial_id: str = DIAL,
    as_of: datetime = AS_OF,
    breadth: float = 0.20,
    acute: float = 0.40,
) -> MachineStateRow:
    """ONE PRECEDING ROW, as the store would hold it.

    ``candidate`` defaults to ``machine_state`` — a SETTLED row, which is the invariant
    :mod:`evaluator.resolve` states: ``persistence_counter > 0`` exactly while a candidate
    the dial is not in is accumulating. Tests that need a row mid-count pass both.

    An UNKNOWN row carries NO statistic and a resolvable row carries every one of them,
    which is :data:`evaluator.history_store._STATE_FIELDS_COHERENT`'s CHECK — these rows
    are rows the real file would accept.
    """
    if machine_state is State.UNKNOWN:
        return MachineStateRow(
            dial_id=dial_id,
            as_of=as_of,
            machine_state=State.UNKNOWN,
            candidate_state=State.UNKNOWN if candidate is None else candidate,
            persistence_counter=counter,
        )
    return MachineStateRow(
        dial_id=dial_id,
        as_of=as_of,
        machine_state=machine_state,
        candidate_state=machine_state if candidate is None else candidate,
        persistence_counter=counter,
        acute_rising=False,
        breadth=breadth,
        acute=acute,
        acute_from_master_id="master_1",
        master_scores={"master_1": acute},
        indicator_count=0,
        count_at_or_beyond=(),
    )


def _history_of(length: int, *, breadth_at_the_lookback: float = 0.30) -> tuple:
    """``length`` settled CALM rows, most recent first, one of them carrying a breadth.

    The row :data:`BREADTH_LOOKBACK_ROWS` back — index 19 in a most-recent-first history —
    gets ``breadth_at_the_lookback``; every other row gets a breadth that is NOT it, so a
    test asserting on the lookback cannot be satisfied by the wrong row.
    """
    return tuple(
        _row(
            State.CALM,
            breadth=(
                breadth_at_the_lookback
                if position == BREADTH_LOOKBACK_ROWS - 1
                else 0.20
            ),
            as_of=AS_OF - A_CADENCE * (position + 1),
        )
        for position in range(length)
    )


# --- the premise every test below rests on ----------------------------------------------- #


def test_the_readings_in_this_file_compute_the_candidates_they_are_named_for():
    """The five readings really are the candidates their names claim, thresholds asserted.

    WITHOUT THIS TEST EVERY OTHER TEST IN THE FILE WOULD BE INFERRING ITS OWN PREMISE. The
    resolver's behaviour is stated in terms of the candidate it was handed, so "fed an ALARM
    candidate out of a RECOVERY, the dial alarms immediately" is only evidence about the
    resolver once ``alarm_reading()`` is known to BE an ALARM candidate. Here that is read
    off :func:`~crash_detector.engine.statistics.candidate_state_for_one_reading` directly,
    the same function the resolver calls.

    ``breadth_20_rows_ago=None`` matches what these readings meet in the tests below: every
    history there is shorter than :data:`BREADTH_LOOKBACK_ROWS`, so rule 4's breadth limb
    cannot fire and the candidate is the rule each reading was built for. The one test with
    a 20-row history supplies its own breadth deliberately.
    """
    assert PROVISIONAL_EXIT < QUIET < PROVISIONAL_WARNING
    assert PROVISIONAL_WARNING <= AT_WARNING < PROVISIONAL_STRESS
    assert AT_STRESS >= PROVISIONAL_STRESS
    assert all(score <= PROVISIONAL_EXIT for score in UNDER_EXIT)

    def candidate(reading: dict) -> State:
        # alarm_lock_armed is the WRAPPER's parameter, not the candidate function's.
        stats = {k: v for k, v in reading.items() if k != "alarm_lock_armed"}
        return candidate_state_for_one_reading(breadth_20_rows_ago=None, **stats)

    assert candidate(calm_reading()) is State.CALM
    assert candidate(watch_reading()) is State.WATCH
    assert candidate(alarm_reading()) is State.ALARM
    assert candidate(recovering_reading()) is State.RECOVERY
    assert candidate(unknown_reading()) is State.UNKNOWN


# --- the first reading, and normal persistence -------------------------------------------- #


def test_the_first_ever_reading_for_a_dial_becomes_official_immediately_with_the_clock_at_zero():
    """``history=()``: the candidate IS the official state, and ``persistence_counter`` is 0.

    ROGUE'S CALL, FLAGGED IN :mod:`evaluator.resolve` — the spec is silent on a dial's first
    evaluation. There is no previous state to transition FROM, so there is nothing to make
    the market wait ``PROVISIONAL_PERSISTENCE`` readings for, and with the candidate already official there is by
    definition nothing accumulating: ``0`` means "nothing pending", never "the dial is new".
    A ``1`` here would read as one reading toward a change on the only row that cannot
    possibly be mid-transition.

    The row's statistics are asserted too, because this is the one test where the whole row
    is new: a resolvable row must carry every statistic
    (:data:`evaluator.history_store._STATE_FIELDS_COHERENT`), and ``acute_rising`` is
    ``False`` because there is no earlier acute reading to have risen above (see
    :func:`test_acute_rising_reads_the_previous_rows_acute_and_claims_nothing_without_one`).
    """
    reading = watch_reading()

    row = official_state_for_dial(history=(), as_of=AS_OF, **reading)

    assert row.machine_state is State.WATCH
    assert row.candidate_state is State.WATCH
    assert row.persistence_counter == 0

    assert row.dial_id == DIAL
    assert row.as_of is AS_OF
    assert row.breadth == reading["breadth"]
    assert row.acute == reading["acute"].score
    assert row.acute_from_master_id == reading["acute"].from_master_id
    assert row.master_scores == {"master_1": AT_WARNING, "master_2": 0.10}
    assert row.indicator_count == 0
    assert row.count_at_or_beyond == ()
    assert row.acute_rising is False


def test_the_persistence_th_agreeing_reading_transitions_and_one_reading_short_does_not():
    """``persistence``: THIS reading plus the preceding rows, and one short is not enough.

    ONE HISTORY, READ AT TWO LENGTHS, which is what makes the pair evidence rather than two
    unrelated fixtures. The dial is officially CALM and a WATCH candidate has been
    accumulating: the oldest row recorded the first WATCH (counter 1) and each newer row the
    next, so the newest carries ``PROVISIONAL_PERSISTENCE - 1``. Every row carries
    ``candidate_state=WATCH`` with ``machine_state=CALM``, which is the pending-transition
    shape the ``candidate_state`` column exists to record.

    * Against the FULL history, the same WATCH reading is the ``PROVISIONAL_PERSISTENCE``-th
      in a row: the official state becomes WATCH and the clock reads 0 — spent, with the
      row's own ``machine_state`` as the record that it fired.
    * Against the history MINUS its newest row — the identical dial one evaluation earlier —
      that same reading is one short: the official state is STILL CALM and the clock reads
      ``PROVISIONAL_PERSISTENCE - 1``, counting toward a transition that has not happened.

    The second half is the one that matters. A resolver that transitioned one reading early
    would pass the first assertion and fail this one.

    **THE FIXTURE IS BUILT FROM THE CONSTANT AND NOT FROM A LITERAL**, which is WO-1.3e's
    doing: this test hardcoded a 2-row history and the number 3 while ``persistence`` read 3,
    so raising it to 5 broke the test rather than re-stating it. Derived from
    ``PROVISIONAL_PERSISTENCE``, what is under test is the RULE — "one short never
    transitions" — at whatever value the constant provisionally holds.
    """
    history = tuple(
        _row(
            State.CALM,
            candidate=State.WATCH,
            counter=counter,
            as_of=AS_OF - A_CADENCE * (PROVISIONAL_PERSISTENCE - counter),
        )
        for counter in range(PROVISIONAL_PERSISTENCE - 1, 0, -1)
    )
    assert len(history) == PROVISIONAL_PERSISTENCE - 1
    assert [row.persistence_counter for row in history] == list(
        range(PROVISIONAL_PERSISTENCE - 1, 0, -1)
    )

    on_time = official_state_for_dial(history=history, as_of=AS_OF, **watch_reading())
    one_short = official_state_for_dial(history=history[1:], as_of=AS_OF, **watch_reading())

    assert on_time.candidate_state is State.WATCH
    assert on_time.machine_state is State.WATCH
    assert on_time.persistence_counter == 0

    assert one_short.candidate_state is State.WATCH
    assert one_short.machine_state is State.CALM
    assert one_short.persistence_counter == PROVISIONAL_PERSISTENCE - 1


# --- breaking a streak: the revert, and the switch ---------------------------------------- #


def test_reverting_to_the_dials_own_state_mid_count_resets_the_clock_to_zero():
    """Spec §3's "reverting mid-count resets the counter to zero" — zero, not decremented.

    The dial is officially CALM with a WATCH candidate two readings into its three
    (``persistence_counter=2``), and this reading's candidate is CALM: the state the dial is
    already in. That IS the revert, and the clock does not step back to 1 — it clears,
    because nothing is accumulating any more and the invariant
    :mod:`evaluator.resolve` states is ``persistence_counter > 0`` exactly while a candidate
    the dial is NOT in is accumulating.

    The assertion is written against the preceding counter rather than the literal 0 alone,
    so a decrementing implementation is refused by name: at ``counter=2`` a decrement would
    also produce a number, and only the two assertions together separate them.
    """
    mid_count = _row(State.CALM, candidate=State.WATCH, counter=2, as_of=AS_OF - A_CADENCE)

    row = official_state_for_dial(history=(mid_count,), as_of=AS_OF, **calm_reading())

    assert row.candidate_state is State.CALM
    assert row.machine_state is State.CALM
    assert row.persistence_counter == 0
    assert row.persistence_counter != mid_count.persistence_counter - 1


def test_switching_to_a_different_candidate_mid_count_restarts_the_clock_at_one():
    """A NEW candidate mid-count counts 1, not 0 — ROGUE'S CALL, spec §3 addresses only the revert.

    The dial is officially CALM with a WATCH candidate at 2, and this reading calls for
    ALARM: neither the accumulating candidate nor the dial's current state, so neither spec
    §3's revert nor a continuation. The WATCH streak is destroyed — that is what breaking a
    streak means — but the ALARM candidate has genuinely been computed ONCE, and recording
    that as 0 would make its transition take four readings instead of the three spec §3
    asks for.

    The official state is unchanged in the same row, which is the other half of the claim:
    the switch starts a clock, it does not ring one.
    """
    mid_count = _row(State.CALM, candidate=State.WATCH, counter=2, as_of=AS_OF - A_CADENCE)

    row = official_state_for_dial(history=(mid_count,), as_of=AS_OF, **alarm_reading())

    assert row.candidate_state is State.ALARM
    assert row.machine_state is State.CALM
    assert row.persistence_counter == 1


# --- the second leg -----------------------------------------------------------------------  #


def test_the_second_leg_rule_alarms_out_of_recovery_with_no_persistence_wait():
    """Previous state RECOVERY + an ALARM candidate → ALARM NOW (spec §3, DECISION-RULE.md §6).

    THE SAME ALARM READING IS RUN TWICE, against two histories differing only in the
    previous official state, and that contrast is the evidence: out of RECOVERY the dial
    alarms on this reading with the clock cleared, while out of CALM the identical reading
    only starts the normal three-reading count. Without the second run, "ALARM with
    counter 0" could be any rule in the function.

    A relapse out of recovery is the one transition this product will not make the market
    wait for, and "the persistence/recovery clock resets to zero" is the spec's own phrase.
    """
    out_of_recovery = (_row(State.RECOVERY, as_of=AS_OF - A_CADENCE),)
    out_of_calm = (_row(State.CALM, as_of=AS_OF - A_CADENCE),)

    relapse = official_state_for_dial(history=out_of_recovery, as_of=AS_OF, **alarm_reading())
    ordinary = official_state_for_dial(history=out_of_calm, as_of=AS_OF, **alarm_reading())

    assert relapse.candidate_state is State.ALARM
    assert relapse.machine_state is State.ALARM
    assert relapse.persistence_counter == 0

    assert ordinary.candidate_state is State.ALARM
    assert ordinary.machine_state is State.CALM
    assert ordinary.persistence_counter == 1


# --- rule 5's previous-state gate ---------------------------------------------------------- #


def test_rule_5s_previous_state_gate_corrects_the_candidate_before_persistence():
    """A RECOVERY candidate whose dial was not in ALARM is not a recovery: the CANDIDATE becomes CALM.

    Rule 5 reads "Else if the dial's PREVIOUS state was ALARM AND ...", and
    :func:`~crash_detector.engine.statistics.candidate_state_for_one_reading` documents that
    it cannot apply that condition — it has no memory. The resolver applies it, and it
    applies it to the CANDIDATE, BEFORE any clock runs: spec §3's "Else" chain falls through
    past rule 5 to rule 6, so the candidate is CALM and it is CALM that gets counted.

    The premise is established on the spot rather than assumed: the identical reading is run
    through the engine function first, which returns RECOVERY. So the CALM on the row is the
    gate firing, not a reading that was never a recovery candidate.

    Three previous states, and the third is what makes this a GATE rather than a blanket
    suppression of RECOVERY:

    * previous CALM — candidate corrected to CALM, which is the state the dial is already
      in, so the clock reads 0 and nothing is pending.
    * previous WATCH — candidate corrected to CALM, and the row then counts 1 toward CALM
      with WATCH still official. **This is the test that the correction precedes
      persistence**: the clock is counting toward CALM, a state the engine never proposed,
      and an uncorrected candidate would have left ``candidate_state=RECOVERY`` on the row.
    * previous ALARM — the gate's condition is MET, the candidate stays RECOVERY, and it
      takes the ordinary ``PROVISIONAL_PERSISTENCE`` readings (counter 1 here). A recovery is
      late by design.

    A dial with NO history has no previous ALARM either, so its first reading can never be a
    RECOVERY — asserted last, because it is the same rule with the history empty.
    """
    reading = recovering_reading()
    assert _candidate(reading) is State.RECOVERY

    from_calm = official_state_for_dial(
        history=(_row(State.CALM, as_of=AS_OF - A_CADENCE),), as_of=AS_OF, **reading
    )
    from_watch = official_state_for_dial(
        history=(_row(State.WATCH, as_of=AS_OF - A_CADENCE),), as_of=AS_OF, **reading
    )
    from_alarm = official_state_for_dial(
        history=(_row(State.ALARM, as_of=AS_OF - A_CADENCE),), as_of=AS_OF, **reading
    )
    first_ever = official_state_for_dial(history=(), as_of=AS_OF, **reading)

    assert from_calm.candidate_state is State.CALM
    assert from_calm.machine_state is State.CALM
    assert from_calm.persistence_counter == 0

    assert from_watch.candidate_state is State.CALM
    assert from_watch.machine_state is State.WATCH
    assert from_watch.persistence_counter == 1

    assert from_alarm.candidate_state is State.RECOVERY
    assert from_alarm.machine_state is State.ALARM
    assert from_alarm.persistence_counter == 1

    assert first_ever.candidate_state is State.CALM
    assert first_ever.machine_state is State.CALM


# --- ALARM's exit path (WO-1.3e, R2D2's finding B2) ---------------------------------------- #


def _drive(readings: list, *, history: tuple) -> list:
    """Run ``readings`` in order, feeding each returned row back as the next one's history.

    THE SEQUENCE IS THE SUBJECT of every test below — "corrected to WATCH, then normal
    persistence applies" is a claim about four or six consecutive readings and cannot be
    made against one. Rows are PREPENDED because the history is most-recent-first, and
    ``as_of`` advances one fixture cadence per reading so the rows are rows the real store
    would hold; the resolver reads neither (it counts rows), which is why driving it this
    way proves the same thing the production evaluator pass would see.

    Returns every row produced, oldest first, so a test can assert on the whole path.
    """
    produced = []
    for position, reading in enumerate(readings):
        row = official_state_for_dial(
            history=history, as_of=AS_OF + A_CADENCE * position, **reading
        )
        produced.append(row)
        history = (row,) + history
    return produced


def test_alarm_never_exits_straight_to_calm_the_candidate_is_corrected_to_watch():
    """R2D2's observed live scenario: previous ALARM + a plainly calm reading → candidate WATCH.

    THE PREMISE IS ESTABLISHED ON THE SPOT, as rule 5's gate test does it: the identical
    reading goes through :func:`~crash_detector.engine.statistics.candidate_state_for_one_reading`
    first and returns CALM. So the WATCH on the row is the correction firing, not a reading
    that was never a CALM candidate — which is the whole of finding B2, since a CALM
    candidate out of ALARM is exactly what rule 6 produces while ``trend_confirmed`` is
    hard-wired False and rule 5 cannot fire.

    AND IT IS NOT AN INSTANT JUMP EITHER. The corrected candidate is counted, not applied:
    the official state is still ALARM on this reading with the clock at 1, and the contrast
    run — the same reading out of CALM — shows the correction is keyed on the previous state
    and not a blanket ban on CALM candidates.
    """
    reading = calm_reading()
    assert _candidate(reading) is State.CALM

    from_alarm = official_state_for_dial(
        history=(_row(State.ALARM, as_of=AS_OF - A_CADENCE),), as_of=AS_OF, **reading
    )
    from_calm = official_state_for_dial(
        history=(_row(State.CALM, as_of=AS_OF - A_CADENCE),), as_of=AS_OF, **reading
    )

    assert from_alarm.candidate_state is State.WATCH
    assert from_alarm.machine_state is State.ALARM
    assert from_alarm.persistence_counter == 1

    assert from_calm.candidate_state is State.CALM
    assert from_calm.machine_state is State.CALM
    assert from_calm.persistence_counter == 0


def test_the_correction_fires_on_every_reading_out_of_alarm_and_then_stops_by_itself():
    """ROGUE'S CALL UNDER TEST: every reading while ALARM is official, needing no clock of its own.

    ``PROVISIONAL_PERSISTENCE`` calm readings are driven out of an ALARM row and the
    candidate on EVERY one of them is asserted to be WATCH. That is what makes the
    correction a gate rather than a one-off: were it corrected only on the first reading,
    every row after the first would carry CALM, the WATCH streak would break on row 2 and the
    CALM streak would complete one reading later — the illegal ALARM → CALM jump, reinstated.

    THE LAST ASSERTION IS THE SELF-EXTINGUISHING HALF. The reading AFTER the transition sees
    a preceding row that says WATCH, so the correction's condition is false and the
    candidate is left as the CALM the engine computed. The correction needs no memory
    because the transition it causes removes its own trigger.
    """
    out_of_alarm = (_row(State.ALARM, as_of=AS_OF - A_CADENCE),)
    path = _drive([calm_reading() for _ in range(PROVISIONAL_PERSISTENCE + 1)], history=out_of_alarm)

    assert [row.candidate_state for row in path[:PROVISIONAL_PERSISTENCE]] == (
        [State.WATCH] * PROVISIONAL_PERSISTENCE
    )
    assert [row.machine_state for row in path[: PROVISIONAL_PERSISTENCE - 1]] == (
        [State.ALARM] * (PROVISIONAL_PERSISTENCE - 1)
    )
    assert [row.persistence_counter for row in path[: PROVISIONAL_PERSISTENCE - 1]] == (
        list(range(1, PROVISIONAL_PERSISTENCE))
    )

    transition = path[PROVISIONAL_PERSISTENCE - 1]
    assert transition.machine_state is State.WATCH
    assert transition.persistence_counter == 0

    after = path[PROVISIONAL_PERSISTENCE]
    assert after.candidate_state is State.CALM
    assert after.machine_state is State.WATCH
    assert after.persistence_counter == 1


def test_a_calm_count_already_running_out_of_alarm_is_restarted_toward_watch_not_completed():
    """THE LIVE ROW R2D2 FOUND: machine_state ALARM, candidate_state CALM, clock one short.

    This is not a hypothetical history. The defect was observed running, so the store holds
    rows mid-count toward the illegal transition — and the reading that lands on such a row
    is the one that would have completed it. The corrected candidate is WATCH, which is not
    the candidate the preceding row recorded, so the streak cannot be extended: the clock
    restarts at 1 and the official state is still ALARM.

    An already-accumulated count toward a transition the rule now forbids is therefore
    DISCARDED rather than honoured, which is the only safe reading of it — the readings that
    built it were readings nothing should have been counting.
    """
    one_short = PROVISIONAL_PERSISTENCE - 1
    mid_count = (
        _row(State.ALARM, candidate=State.CALM, counter=one_short, as_of=AS_OF - A_CADENCE),
    )

    row = official_state_for_dial(history=mid_count, as_of=AS_OF, **calm_reading())

    assert row.candidate_state is State.WATCH
    assert row.machine_state is State.ALARM
    assert row.persistence_counter == 1


def test_calm_is_still_reachable_from_alarm_by_way_of_a_watch_that_really_became_official():
    """THE CORRECTION REMOVES ONE TRANSITION'S WORTH OF SHORTCUT, NOT THE DESTINATION.

    Twice ``PROVISIONAL_PERSISTENCE`` identical calm readings are driven out of ALARM and
    the official path is asserted end to end: ALARM while the first count runs, WATCH when
    it completes, WATCH while the second runs, CALM when THAT completes. CALM out of ALARM
    now costs two transitions instead of one, which is DECISION-RULE.md §3's "the re-entry
    threshold is demanding" — and the last row proves it is a cost and not a prohibition.

    The intermediate WATCH is a state the dial GENUINELY OCCUPIED for the required readings,
    not a label passed through on the way: it is official on every row between the two
    transitions, which is what finding B2 says was missing.
    """
    out_of_alarm = (_row(State.ALARM, as_of=AS_OF - A_CADENCE),)
    path = _drive([calm_reading() for _ in range(2 * PROVISIONAL_PERSISTENCE)], history=out_of_alarm)

    assert [row.machine_state for row in path] == (
        [State.ALARM] * (PROVISIONAL_PERSISTENCE - 1)
        + [State.WATCH] * PROVISIONAL_PERSISTENCE
        + [State.CALM]
    )
    assert path[-1].candidate_state is State.CALM
    assert path[-1].persistence_counter == 0


def test_the_alarm_exit_correction_leaves_the_recovery_paths_exactly_as_they_were():
    """THE TWO PATHS OUT OF ALARM AND RECOVERY THAT ALREADY WORKED, RE-ASSERTED UNCHANGED.

    The correction's condition is "previous ALARM **and** candidate CALM", and each path
    below fails one half of it, so each must compute what it computed before WO-1.3e:

    * **Rule 5's gate, condition met** — previous ALARM, candidate RECOVERY. The candidate
      is NOT CALM, so this correction is inert and RECOVERY survives to be counted. The two
      corrections cannot fight: the gate only produces a CALM when the dial was NOT in
      ALARM, which is the one case this correction will not act on.
    * **The second-leg rule** — previous RECOVERY, candidate ALARM. Neither half holds, and
      the relapse is still immediate with the clock cleared.
    * **A genuine WATCH reading out of ALARM** — candidate already WATCH, nothing to
      correct, ordinary persistence. Run against ALARM and against CALM to show the
      correction has not quietly made ALARM a special case for readings it never touches.
    """
    recovery = official_state_for_dial(
        history=(_row(State.ALARM, as_of=AS_OF - A_CADENCE),),
        as_of=AS_OF,
        **recovering_reading(),
    )
    assert recovery.candidate_state is State.RECOVERY
    assert recovery.machine_state is State.ALARM
    assert recovery.persistence_counter == 1

    relapse = official_state_for_dial(
        history=(_row(State.RECOVERY, as_of=AS_OF - A_CADENCE),), as_of=AS_OF, **alarm_reading()
    )
    assert relapse.candidate_state is State.ALARM
    assert relapse.machine_state is State.ALARM
    assert relapse.persistence_counter == 0

    watch_from_alarm = official_state_for_dial(
        history=(_row(State.ALARM, as_of=AS_OF - A_CADENCE),), as_of=AS_OF, **watch_reading()
    )
    watch_from_calm = official_state_for_dial(
        history=(_row(State.CALM, as_of=AS_OF - A_CADENCE),), as_of=AS_OF, **watch_reading()
    )
    assert watch_from_alarm.candidate_state is State.WATCH
    assert watch_from_alarm.machine_state is State.ALARM
    assert watch_from_alarm.persistence_counter == 1
    assert watch_from_calm.candidate_state is State.WATCH
    assert watch_from_calm.machine_state is State.CALM
    assert watch_from_calm.persistence_counter == 1


# --- leaving UNKNOWN ----------------------------------------------------------------------- #


def test_leaving_unknown_is_immediate_and_not_held_behind_the_persistence_clock():
    """A resolvable reading after an UNKNOWN row resolves NOW — ROGUE'S CALL, and the schema's.

    THE SAME WATCH READING AGAINST TWO HISTORIES, differing only in the previous official
    state: after UNKNOWN it is official on this reading with the clock at 0, while after
    CALM the identical reading starts the ordinary count at 1. The contrast is what
    establishes that the UNKNOWN branch exists.

    The reason it is right rather than lenient is the schema:
    ``machine_state_history``'s ``state_fields_coherent`` CHECK makes an UNKNOWN row
    carrying numbers UNREPRESENTABLE (CD-RT-001), and this reading HAS a breadth, an acute
    and a count. Holding the old state for two more readings would mean writing a row that
    discards the numbers this evaluation really did observe. Spec §3 is silent; R2D2's
    WO-1.3b audit has since ACCEPTED the immediacy asserted here, and bounded what the
    exiting reading may report — the floor is the next test down, and the WATCH reading used
    here is one of the candidates it deliberately does not touch.
    """
    after_unknown = official_state_for_dial(
        history=(_row(State.UNKNOWN, as_of=AS_OF - A_CADENCE),), as_of=AS_OF, **watch_reading()
    )
    after_calm = official_state_for_dial(
        history=(_row(State.CALM, as_of=AS_OF - A_CADENCE),), as_of=AS_OF, **watch_reading()
    )

    assert after_unknown.candidate_state is State.WATCH
    assert after_unknown.machine_state is State.WATCH
    assert after_unknown.persistence_counter == 0

    assert after_calm.machine_state is State.CALM
    assert after_calm.persistence_counter == 1


def test_a_dial_leaving_unknown_is_floored_at_watch_and_never_resolves_straight_to_calm():
    """R2D2's SCENARIO: previous official UNKNOWN + one plainly calm reading → WATCH, not CALM.

    THE PREMISE IS ESTABLISHED ON THE SPOT, as the ALARM-exit tests do it: the identical
    reading goes through
    :func:`~crash_detector.engine.statistics.candidate_state_for_one_reading` first and
    returns CALM, so the WATCH on the row is the floor firing and not a reading that was
    never a CALM candidate. That is the whole of the finding — the data comes back after an
    outage, the first reading happens to resolve calm, and the dial would have said deploy on
    the strength of one unverified number.

    WATCH IS OFFICIAL ON THIS READING RATHER THAN ACCUMULATING, and that is the floor
    co-operating with item 1's accepted immediacy instead of fighting it: the UNKNOWN-exit
    branch applies the candidate with no clock, because a row carrying numbers cannot say
    UNKNOWN (CD-RT-001). "At least WATCH until persistence is satisfied" is therefore
    delivered as WATCH now, with persistence governing only the onward move to CALM.

    The invariant is asserted on the row as well — ``persistence_counter > 0`` exactly while
    a candidate the dial is not in is accumulating — because the floor corrects the CANDIDATE
    and a row that said WATCH while recording the raw CALM would have broken it.

    The contrast run is the same reading out of CALM: untouched, which shows the floor is
    keyed on the previous state and is not a blanket ban on CALM candidates.
    """
    reading = calm_reading()
    assert _candidate(reading) is State.CALM

    from_unknown = official_state_for_dial(
        history=(_row(State.UNKNOWN, as_of=AS_OF - A_CADENCE),), as_of=AS_OF, **reading
    )
    from_calm = official_state_for_dial(
        history=(_row(State.CALM, as_of=AS_OF - A_CADENCE),), as_of=AS_OF, **reading
    )

    assert from_unknown.candidate_state is State.WATCH
    assert from_unknown.machine_state is State.WATCH
    assert from_unknown.persistence_counter == 0
    assert (from_unknown.persistence_counter > 0) is (
        from_unknown.candidate_state is not from_unknown.machine_state
    )

    assert from_calm.candidate_state is State.CALM
    assert from_calm.machine_state is State.CALM
    assert from_calm.persistence_counter == 0


def test_the_unknown_floor_touches_no_candidate_except_calm():
    """ALARM and WATCH out of UNKNOWN resolve exactly as they did before the floor existed.

    The floor's condition is "previous UNKNOWN **and** candidate CALM", and CALM is the only
    candidate that is MORE PERMISSIVE than the UNKNOWN it replaces (DECISION-RULE.md §6 reads
    UNKNOWN itself as WATCH for permission purposes, never CALM). An ALARM out of an outage is
    not something to soften, and a WATCH is already at the floor — so both are immediate, with
    the clock at 0, which is what the test above's sibling asserted before WO-1.3e round 3 and
    what this re-asserts after it.

    An UNKNOWN candidate after an UNKNOWN row is in the same set and is covered where rule 1
    is: it is not an exit from UNKNOWN at all, and the floor never sees a CALM to act on.
    """
    out_of_unknown = (_row(State.UNKNOWN, as_of=AS_OF - A_CADENCE),)

    alarming = official_state_for_dial(history=out_of_unknown, as_of=AS_OF, **alarm_reading())
    watching = official_state_for_dial(history=out_of_unknown, as_of=AS_OF, **watch_reading())

    assert alarming.candidate_state is State.ALARM
    assert alarming.machine_state is State.ALARM
    assert alarming.persistence_counter == 0

    assert watching.candidate_state is State.WATCH
    assert watching.machine_state is State.WATCH
    assert watching.persistence_counter == 0


def test_a_recovery_reading_out_of_unknown_is_floored_because_rule_5s_gate_runs_first():
    """THE ONE COMPOSITION, AND IT IS DELIBERATE: the gate makes CALM, the floor makes WATCH.

    A RECOVERY candidate out of an UNKNOWN row is NOT a recovery — rule 5 requires the dial
    to have been in ALARM, and rule 5's gate therefore corrects the candidate to CALM (the
    "Else" chain's fall-through to rule 6, asserted in its own test above). Before WO-1.3e
    round 3 that CALM then became official immediately, which is R2D2's scenario reached by a
    second route: a dial that cannot even confirm a recovery saying deploy on one reading.

    So the ORDER OF THE TWO CORRECTIONS IS LOAD-BEARING and this test is what holds it in
    place. The gate runs first, above the floor, so its output is floored like any other CALM
    rather than escaping unfloored; swapping them would read the raw RECOVERY, find it is not
    CALM, and let the gate produce an unfloored CALM one line later.

    The engine's own candidate is asserted first so the chain is visible: RECOVERY in, and a
    row that says WATCH.
    """
    reading = recovering_reading()
    assert (
        _candidate(reading) is State.RECOVERY
    )

    row = official_state_for_dial(
        history=(_row(State.UNKNOWN, as_of=AS_OF - A_CADENCE),), as_of=AS_OF, **reading
    )

    assert row.candidate_state is State.WATCH
    assert row.machine_state is State.WATCH
    assert row.persistence_counter == 0


def test_the_unknown_floor_fires_once_and_calm_then_costs_an_ordinary_persistence_count():
    """THE SELF-EXTINGUISHING PROPERTY, AND IT IS NOT ITEM 3's — ONE READING, NOT FIVE.

    ``PROVISIONAL_PERSISTENCE + 1`` identical calm readings are driven out of an UNKNOWN row
    and the whole path is asserted:

    * Reading 1 — the floor fires, WATCH is OFFICIAL immediately, clock 0.
    * Readings 2 .. ``PROVISIONAL_PERSISTENCE`` — the preceding row says WATCH, so the floor's
      condition is ALREADY FALSE and every candidate from here on is the CALM the engine
      computed. Ordinary persistence counts 1, 2, ... from a dial genuinely in WATCH, and the
      count starts at 1 rather than extending anything because the WATCH row's recorded
      candidate was WATCH.
    * The last reading — the count completes and the dial officially says CALM.

    THE CONTRAST WITH THE ALARM EXIT IS THE POINT OF ASSERTING THE COUNT ITSELF. That
    correction fires on ``PROVISIONAL_PERSISTENCE`` consecutive readings, because the WATCH it
    produces is counted and ALARM stays official while the clock runs, which keeps its own
    trigger alive. This one is extinguished by a transition that happens on the reading it
    fired on, so it CANNOT fire twice — a sequence is the only way to show that, and the
    assertion that every candidate after the first is CALM is where it is shown.
    """
    out_of_unknown = (_row(State.UNKNOWN, as_of=AS_OF - A_CADENCE),)
    path = _drive(
        [calm_reading() for _ in range(PROVISIONAL_PERSISTENCE + 1)], history=out_of_unknown
    )

    assert path[0].candidate_state is State.WATCH
    assert path[0].machine_state is State.WATCH
    assert path[0].persistence_counter == 0

    assert [row.candidate_state for row in path[1:]] == (
        [State.CALM] * PROVISIONAL_PERSISTENCE
    )
    assert [row.machine_state for row in path] == (
        [State.WATCH] * PROVISIONAL_PERSISTENCE + [State.CALM]
    )
    assert [row.persistence_counter for row in path] == (
        [0] + list(range(1, PROVISIONAL_PERSISTENCE)) + [0]
    )


# --- the two refusals and the absence ------------------------------------------------------ #


def test_a_history_row_for_another_dial_is_refused():
    """One dial's persistence count may not be continued from another dial's readings.

    The dial is read OFF the reading (both :class:`~crash_detector.engine.statistics.Acute`
    and ``AcuteUnknown`` carry one) precisely so there is no parameter through which a
    caller could pair a history with the wrong reading — so the only cross-dial claim the
    function CAN check is this one, and it refuses rather than counting.

    The foreign row is SECOND in the history, not first: the check covers every row, and a
    version that only looked at ``history[0]`` — the row the persistence branch actually
    reads — would pass a test that put it at the front.

    The second half runs an UNRESOLVABLE reading for the other dial against this dial's
    history and gets the same refusal, which establishes that the check runs BEFORE rule 1's
    unconditional UNKNOWN. Rule 1 stops the rules; it does not excuse a mismatched history.
    """
    history = (
        _row(State.CALM, as_of=AS_OF - A_CADENCE),
        _row(State.CALM, dial_id=OTHER_DIAL, as_of=AS_OF - A_CADENCE * 2),
    )

    with pytest.raises(ValueError, match=OTHER_DIAL):
        official_state_for_dial(history=history, as_of=AS_OF, **watch_reading())

    with pytest.raises(ValueError, match=DIAL):
        official_state_for_dial(
            history=(_row(State.CALM, as_of=AS_OF - A_CADENCE),),
            as_of=AS_OF,
            **unknown_reading(acute=_unknown_acute(dial_id=OTHER_DIAL)),
        )


def test_an_unresolvable_reading_writes_unknown_and_carries_no_statistic_at_all():
    """Rule 1, unconditional: UNKNOWN, clock cleared, and every statistic absent (CD-RT-001).

    The history is deliberately mid-count — officially CALM with a WATCH candidate at 2 —
    because rule 1's "Stop; no other rule overrides this" has to be shown overriding
    something. The pending count does not survive the reading and is not carried forward: an
    evaluation that could not be resolved has not advanced any transition.

    The field list is :data:`evaluator.history_store._STATISTIC_COLUMNS` ITSELF, not a
    retyped list of names, so this test covers exactly the set the table's coherence CHECK
    governs — including ``acute_rising``, which is a comparison BETWEEN acute readings and
    cannot be rising when there is no acute reading to compare. A new statistic column added
    to the store without being nulled here makes this test fail, which is the point.
    """
    mid_count = _row(State.CALM, candidate=State.WATCH, counter=2, as_of=AS_OF - A_CADENCE)

    row = official_state_for_dial(history=(mid_count,), as_of=AS_OF, **unknown_reading())

    assert row.machine_state is State.UNKNOWN
    assert row.candidate_state is State.UNKNOWN
    assert row.persistence_counter == 0
    assert row.dial_id == DIAL
    assert row.as_of is AS_OF
    for field_name in _STATISTIC_COLUMNS:
        assert getattr(row, field_name) is None, field_name


# --- the two derived numbers ---------------------------------------------------------------- #


def test_acute_rising_reads_the_previous_rows_acute_and_claims_nothing_without_one():
    """``_acute_rising``: strictly above the last row's acute, and ``False`` when there is none.

    Four readings against one previous row at 0.40 — higher, lower, and EQUAL, since
    "rising" is a claim an unchanged number does not make — then the two ways there is
    nothing to compare against: no previous row at all, and a previous row that was UNKNOWN
    and carries no acute. Both answer ``False``, which is the answer that CLAIMS LESS rather
    than the true one; the column cannot hold "cannot confirm" (it is in the statistics set a
    resolvable row may not leave NULL) and :mod:`evaluator.resolve` flags that as an open
    question. ``False`` here must therefore never be read as "the acute statistic fell".

    The last two assertions carry it through the real function onto the row, so the helper is
    shown WIRED and not merely correct in isolation.
    """
    previous = _row(State.CALM, acute=0.40, as_of=AS_OF - A_CADENCE)

    assert _acute_rising(_acute_of(0.55, 0.10), previous) is True
    assert _acute_rising(_acute_of(0.30, 0.10), previous) is False
    assert _acute_rising(_acute_of(0.40, 0.10), previous) is False
    # WO-1.3b-II: THE DEADBAND. A rise has to clear PROVISIONAL_ACUTE_RISE_DEADBAND (0.02) over the previous row's
    # acute: a bare uptick is band arithmetic, and a move of exactly the deadband is not a rise either (strict).
    assert PROVISIONAL_ACUTE_RISE_DEADBAND == 0.02 == PROVISIONAL_BREADTH_RISE_DEADBAND
    assert _acute_rising(_acute_of(0.41, 0.10), previous) is False
    assert _acute_rising(_acute_of(0.40 + PROVISIONAL_ACUTE_RISE_DEADBAND, 0.10), previous) is False
    assert _acute_rising(_acute_of(0.43, 0.10), previous) is True
    assert _acute_rising(_acute_of(0.55), None) is False
    assert _acute_rising(_acute_of(0.55), _row(State.UNKNOWN)) is False

    rising = official_state_for_dial(history=(previous,), as_of=AS_OF, **watch_reading())
    falling = official_state_for_dial(
        history=(_row(State.ALARM, acute=AT_STRESS, as_of=AS_OF - A_CADENCE),),
        as_of=AS_OF,
        **watch_reading(),
    )

    assert rising.acute_rising is True
    assert falling.acute_rising is False


def test_the_breadth_lookback_needs_20_rows_and_reads_the_20th_one_specifically(monkeypatch):
    """``_breadth_rows_ago``: ``None`` under 20 rows, and the row 20 back once there are.

    Spec §7's provisional reading of "breadth rising over the last 20 readings" is a LOOKBACK
    COMPARISON, so one earlier number is the whole of it: index 19 of a most-recent-first
    history. :func:`_history_of` gives that row a breadth no other row has, so reading the
    oldest row, or ``history[20]``, cannot produce the expected number by accident — the
    25-row assertion is what separates "20 back" from "as far back as there is".

    ``None`` means CANNOT CONFIRM RISING and never DID NOT RISE, and it arises two ways:
    fewer than 20 rows exist, or the row 20 back is an UNKNOWN row that carries no breadth at
    all (CD-RT-001). Both are asserted, because a young or interrupted history must not read
    as a calm one.

    The last pair runs the number through the real function: ONE reading — breadth 0.40, past
    the mid band, every master quiet — against a 20-row history and a 19-row one. The
    candidate moves from WATCH to CALM, which establishes that the resolver DERIVES this
    number and hands it to rule 4's breadth limb rather than leaving it to a caller.
    """
    assert BREADTH_LOOKBACK_ROWS == 20

    assert _breadth_rows_ago(_history_of(BREADTH_LOOKBACK_ROWS - 1)) is None
    assert _breadth_rows_ago(_history_of(BREADTH_LOOKBACK_ROWS)) == 0.30
    assert _breadth_rows_ago(_history_of(BREADTH_LOOKBACK_ROWS + 5)) == 0.30
    assert _history_of(BREADTH_LOOKBACK_ROWS + 5)[-1].breadth == 0.20

    interrupted = list(_history_of(BREADTH_LOOKBACK_ROWS))
    interrupted[BREADTH_LOOKBACK_ROWS - 1] = _row(State.UNKNOWN)
    assert _breadth_rows_ago(tuple(interrupted)) is None

    here = 0.40
    # WO-1.3b-II: B_mid IS UNSET, so the breadth-rising limb is off and the lookback number is derived and handed to
    # rule 4 but read by NOTHING. The first pair below proves that; the second pair sets a B_mid (the day-one calibration
    # path, the only thing that has to change) and shows the same derivation is still wired through the resolver, which is
    # what this test was written to establish.
    assert engine_statistics.PROVISIONAL_BREADTH_MID is None
    assert engine_statistics.PROVISIONAL_BREADTH_HIGH is None
    # CLEAR OF THE DEADBAND, NOT MERELY ABOVE THE EARLIER NUMBER (WO-1.3e): rule 4's limb
    # wants a rise bigger than PROVISIONAL_BREADTH_RISE_DEADBAND, so a fixture that only
    # just cleared 0.30 would fail here for a reason that has nothing to do with the
    # lookback this test is about.
    assert here > 0.30 + PROVISIONAL_BREADTH_RISE_DEADBAND

    off_with_the_lookback = official_state_for_dial(
        history=_history_of(BREADTH_LOOKBACK_ROWS), as_of=AS_OF, **calm_reading(breadth=here))
    assert off_with_the_lookback.candidate_state is State.CALM  # breadth rose 0.30 -> 0.40 and nothing reads it

    monkeypatch.setattr(engine_statistics, "PROVISIONAL_BREADTH_MID", 0.35)
    with_the_lookback = official_state_for_dial(
        history=_history_of(BREADTH_LOOKBACK_ROWS),
        as_of=AS_OF,
        **calm_reading(breadth=here),
    )
    too_young = official_state_for_dial(
        history=_history_of(BREADTH_LOOKBACK_ROWS - 1),
        as_of=AS_OF,
        **calm_reading(breadth=here),
    )

    assert with_the_lookback.candidate_state is State.WATCH
    assert with_the_lookback.machine_state is State.CALM
    assert with_the_lookback.persistence_counter == 1

    assert too_young.candidate_state is State.CALM
    assert too_young.machine_state is State.CALM
    assert too_young.persistence_counter == 0
