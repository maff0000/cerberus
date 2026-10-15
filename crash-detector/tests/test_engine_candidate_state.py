"""RULES 1-6 OF SPEC §3, ONE READING AT A TIME (WO-1.3a round 4).

:func:`crash_detector.engine.statistics.candidate_state_for_one_reading` is HALF of the
state machine: it answers "ignoring how long anything has held, what does THIS reading's
data call for?" and it has no memory at all. Persistence counting, the second-leg rule and
rule 5's "the PREVIOUS state was ALARM" condition are the next round's wrapper and are NOT
under test here — nothing in this file constructs a history, opens a store or asserts a
transition.

====================================================================================
EVERY TEST BELOW ISOLATES ONE RULE, AND "ISOLATES" IS MEANT LITERALLY
====================================================================================

Each reading is built so that the rule under test is the ONLY rule whose condition holds —
not so that the expected answer happens to come out. A test that asserts ``ALARM`` from a
reading where rules 2 AND 3 both fire has not established which rule the code ran.

**THE ONE OVERLAP THAT IS THE SPEC'S AND NOT THIS FILE'S**: a master at or beyond STRESS
(0.85) is necessarily also at or beyond WARNING (0.6), so rule 2's condition can never hold
while rule 4's master limb does not. That overlap is inherent to a precedence of thresholds
and it is why rule 2 comes FIRST; ``test_rule_2...`` is therefore built so that rule 3 is
plainly false, and what it establishes is that rule 2 beats rule 4 rather than that rule 2
fires alone. Every other test holds its non-subject rules genuinely false.

**TWO RULES CHANGED IN WO-1.3e AND THE TESTS BELOW ARE WRITTEN AGAINST THE NEW ONES**
(R2D2's WO-1.3b finding B3). Rule 2 now fires only for an ``alarm_eligible`` master — a
WATCH-only row at any score does not ALARM — and rule 3 now reads BREADTH ALONE, its
``count`` conjunct dropped as an interim measure. ``count`` is still computed, still passed
in and still published; ``PROVISIONAL_COUNT_K`` is no longer a gate. The tests that pin
those two sentences name ``alarm_eligible`` and ``count`` in their own names.

**CONSTRUCTED, NOT PIPED**, following ``test_engine_masters.py``'s own rule: these tests
build :class:`~crash_detector.engine.statistics.Acute`, ``AcuteUnknown`` and ``Count``
directly rather than running contributions through the masters tables. The unit under test
takes the three statistics and returns a state; routing real indicator ids and a banded mean
in front of it would put the masters tables between the input and the assertion while
removing the ability to place a master's score exactly where a threshold boundary is.

EVERY NUMBER IN THIS FILE IS A TEST FIXTURE CHOSEN AGAINST A PROVISIONAL THRESHOLD. The
thresholds themselves (``PROVISIONAL_WARNING`` 0.6, ``PROVISIONAL_STRESS`` 0.85,
``PROVISIONAL_EXIT`` 0.5, ``COUNT_THRESHOLD`` 0.9, ``PROVISIONAL_BREADTH_MID`` 0.35,
``PROVISIONAL_BREADTH_HIGH`` 0.55, ``PROVISIONAL_BREADTH_RISE_DEADBAND`` 0.02,
``PROVISIONAL_COUNT_K`` 3, which no rule reads any more) are the Product Owner's
uncalibrated placeholders per PO-DECISIONS-0025 r3, so no score, breadth or count below
claims anything about any indicator's real distribution. They are compared against the
CONSTANTS rather than against literals wherever the comparison is the point, so a
recalibration in WO-1.3b moves the fixtures with the thresholds instead of silently
inverting what a test proves.
"""

from __future__ import annotations

from crash_detector.dials.scores import EQUITY_DIAL_ID
from crash_detector.engine.statistics import (
    PROVISIONAL_BREADTH_HIGH,
    PROVISIONAL_BREADTH_MID,
    PROVISIONAL_BREADTH_RISE_DEADBAND,
    PROVISIONAL_COUNT_K,
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


def acute_of_rows(*rows: tuple) -> Acute:
    """An :class:`Acute` whose masters carry exactly these ``(score, alarm_eligible)`` rows.

    The master ids are ``master_1``, ``master_2``, ... and they are FIXTURE NAMES: the unit
    under test reads ``master.score`` and ``master.alarm_eligible`` and never a master id,
    because per-master thresholds would be a dial-keyed table lookup this module does not
    have (see the import-time uniformity assertion in ``statistics.py``) and the eligibility
    is carried on the score for exactly that reason. Naming them after real masters would
    suggest these scores were real readings of them — the REAL demoted rows are exercised
    through the real tables in ``test_engine_masters.py``.

    ``score`` IS ALWAYS THE MAX OVER EVERY ROW, ELIGIBLE OR NOT, and ``from_master_id``
    names whichever row that was. That is not this helper being lax: it is what
    :func:`~crash_detector.engine.statistics.equity_crash_acute` does, because a WATCH-only
    master is excluded from rule 2 and from nothing else, and a fixture that hid an
    ineligible master from the maximum would be testing a product that does not exist.
    """
    masters = tuple(
        MasterScore(
            master_id=f"master_{position}",
            dial_id=EQUITY_DIAL_ID,
            score=score,
            alarm_eligible=alarm_eligible,
        )
        for position, (score, alarm_eligible) in enumerate(rows, start=1)
    )
    highest = max(masters, key=lambda master: master.score)
    return Acute(
        dial_id=EQUITY_DIAL_ID,
        score=highest.score,
        from_master_id=highest.master_id,
        masters=masters,
    )


def acute_of(*scores: float) -> Acute:
    """``acute_of_rows`` with every master ALARM-ELIGIBLE, which is the unremarkable case.

    The shorthand exists so that the tests of rules 1 and 3-6 — none of which is about the
    demotion — read as they did before WO-1.3e. **IT IS A FIXTURE DEFAULT AND NOT A
    PRODUCTION ONE**: :class:`~crash_detector.engine.statistics.MasterScore` refuses to be
    built without an explicit ``alarm_eligible`` precisely so that no construction site can
    silently arm a demoted master, and this file does not hand that property back — every
    test ABOUT eligibility calls ``acute_of_rows`` and states both values at the call site.
    """
    return acute_of_rows(*((score, True) for score in scores))


def count_of(at_or_beyond: int, considered: int = 6) -> Count:
    """A :class:`Count` of ``at_or_beyond`` indicators out of ``considered``.

    The ids are positional fixtures for the same reason ``acute_of``'s are: rule 3 reads
    :attr:`Count.count`, which is a LENGTH, and which indicator is at its band is not a
    thing any rule in spec §3 consults.
    """
    names = tuple(f"indicator_{position}" for position in range(considered))
    return Count(at_or_beyond=names[:at_or_beyond], considered=names)


def test_rule_1_an_unknown_acute_is_unknown_and_nothing_else_is_consulted():
    """Rule 1: ``AcuteUnknown`` in, ``UNKNOWN`` out, with every other rule held false.

    The reading is otherwise as quiet as it can be — no breadth, nothing counted, no
    lookback, no trend — so the only condition that holds is rule 1's. ``UNKNOWN`` here is
    the ABSENCE of a resolvable state and emphatically not ``CALM``, which is CD-AC-001.
    """
    state = candidate_state_for_one_reading(
        breadth=0.0,
        acute=AcuteUnknown(
            dial_id=EQUITY_DIAL_ID,
            unknown_master_ids=("master_1",),
            missing_component_ids=("some_indicator",),
        ),
        count=count_of(0),
        breadth_20_rows_ago=None,
        trend_confirmed=False,
    )

    assert state is State.UNKNOWN


def test_rule_1_beats_an_alarm_the_breadth_count_and_masters_would_otherwise_fire():
    """Rule 1's "Stop; no other rule overrides this", measured against rules 2 AND 3.

    ONE reading, built to fire ``ALARM`` twice over — an eligible master at 0.95 (rule 2)
    and breadth 0.90 (rule 3, which reads breadth alone since WO-1.3e; the four counted
    indicators are left in the reading and no longer gate anything) — is run TWICE with
    only the ``acute``
    argument swapped. With the masters resolvable it is ``ALARM``, which is what makes the
    second assertion mean something: the UNKNOWN answer is rule 1 winning, not a quiet
    reading failing to fire anything.

    This is the shape of CD-AC-001's failure mode. A state machine that resolved the
    numbers it HAD and ignored the master it could not score would publish ``ALARM`` or
    ``CALM`` off a thinned reading; one that answers ``UNKNOWN`` has not turned an absence
    into a state.
    """
    breadth = 0.90
    count = count_of(4)
    assert breadth >= PROVISIONAL_BREADTH_HIGH

    with_every_master_scored = candidate_state_for_one_reading(
        breadth=breadth,
        acute=acute_of(0.95, 0.10),
        count=count,
        breadth_20_rows_ago=None,
        trend_confirmed=False,
    )
    with_one_master_unscoreable = candidate_state_for_one_reading(
        breadth=breadth,
        acute=AcuteUnknown(
            dial_id=EQUITY_DIAL_ID,
            unknown_master_ids=("master_1",),
            missing_component_ids=("some_indicator",),
        ),
        count=count,
        breadth_20_rows_ago=None,
        trend_confirmed=False,
    )

    assert with_every_master_scored is State.ALARM
    assert with_one_master_unscoreable is State.UNKNOWN


def test_rule_2_one_eligible_master_at_stress_alarms_with_no_breadth_and_nothing_counted():
    """Rule 2: a firing ALARM-ELIGIBLE master is ``ALARM`` on its own.

    Rule 3 is held plainly false — breadth 0.0 is far under the high band and NOTHING is
    counted — so breadth and count cannot be what fired. Spec §3's parenthesis on this rule
    is "breadth/count can never pull the state below what a firing master dictates", and
    this is that sentence measured: the calmest possible breadth and count do not soften a
    master at 0.90.

    Rule 4's master limb is necessarily ALSO true here (0.90 ≥ WARNING as well as ≥ STRESS,
    and no threshold ordering can separate them) — see the module docstring. What this test
    establishes about that overlap is the PRECEDENCE: the answer is ``ALARM`` and not
    ``WATCH``.
    """
    scored_at = 0.90
    assert scored_at >= PROVISIONAL_STRESS

    state = candidate_state_for_one_reading(
        breadth=0.0,
        acute=acute_of_rows((scored_at, True), (0.10, True)),
        count=count_of(0),
        breadth_20_rows_ago=None,
        trend_confirmed=False,
    )

    assert state is State.ALARM


def test_rule_2_a_watch_only_master_at_stress_does_not_alarm_and_its_eligible_twin_does():
    """THE DEMOTION, AND THE PAIR IS THE WHOLE EVIDENCE (R2D2's finding B3, WO-1.3e).

    ONE reading is run TWICE with ONE BIT CHANGED: a master at 0.95 — past STRESS (0.85) —
    is ``alarm_eligible=False`` in the first call and ``True`` in the second. Nothing else
    differs. The eligible run is ``ALARM``; the WATCH-only run is ``WATCH``.

    **THE SECOND CALL IS WHAT MAKES THE FIRST ONE MEAN ANYTHING.** A ``WATCH`` out of a
    reading that could not fire ALARM for some other reason would prove nothing, so the
    twin establishes that this reading DOES fire rule 2 when the row is armed, and that the
    field is therefore what suppressed it.

    Everything other than the demoted master is as calm as the arguments allow, which is the
    condition the remediation was written against: breadth 0.0 (rules 3 and 4's breadth limb
    out), nothing counted, no lookback, ``trend_confirmed=False``, and the only other master
    at 0.10. So the WATCH-only run has ONE extreme number in it and the answer is still not
    ``ALARM`` — there is no combination of calm elsewhere that this test leaves available as
    an alternative explanation.

    ``WATCH`` and not ``CALM``, and that is rule 4 working as R2D2 asked: 0.95 is at or
    beyond WARNING too, the master limb of rule 4 does not read ``alarm_eligible``, and a
    demoted master is capped BELOW ALARM rather than silenced. ``test_a_watch_only_master_at
    _its_warning_threshold_still_watches`` pins that at the warning boundary itself.
    """
    scored_at = 0.95
    assert scored_at >= PROVISIONAL_STRESS

    demoted = acute_of_rows((scored_at, False), (0.10, True))
    armed = acute_of_rows((scored_at, True), (0.10, True))

    # THE DEMOTED MASTER IS STILL THE DIAL'S ACUTE READING. Excluded from rule 2 and from
    # nothing else: it sets the maximum and it is named as the master that set it, so the
    # reading still SAYS this signal is extreme while declining to call it a crash. (Here
    # that is the fixture's doing; the same claim against the REAL demoted rows and the real
    # tables is ``test_engine_masters.py``'s ``test_the_two_watch_only_masters...``.)
    assert demoted.score == scored_at
    assert demoted.from_master_id == "master_1"
    assert demoted.masters[0].alarm_eligible is False

    watch_only = candidate_state_for_one_reading(
        breadth=0.0,
        acute=demoted,
        count=count_of(0),
        breadth_20_rows_ago=None,
        trend_confirmed=False,
    )
    eligible = candidate_state_for_one_reading(
        breadth=0.0,
        acute=armed,
        count=count_of(0),
        breadth_20_rows_ago=None,
        trend_confirmed=False,
    )

    assert watch_only is State.WATCH
    assert watch_only is not State.ALARM
    assert eligible is State.ALARM


def test_a_watch_only_master_at_its_warning_threshold_still_watches():
    """Rule 4's master limb does NOT read ``alarm_eligible``, measured at the boundary.

    The demoted master sits at EXACTLY ``PROVISIONAL_WARNING`` — the first score the limb
    admits, "at or beyond" — and under STRESS, so rule 2 would not fire for this score even
    if the row were armed. What this test establishes is therefore not a precedence but a
    REACH: the limb still sees a master the Owner demoted, and the demotion removed one
    privilege rather than removing the master from the state machine.

    Held false elsewhere: breadth 0.0 with nothing counted (rule 3), no lookback (rule 4's
    breadth limb cannot be established), and 0.6 is above EXIT with ``trend_confirmed``
    ``False`` besides (rule 5).

    **WHY THIS MATTERS MORE THAN IT LOOKS.** If the eligibility term had been applied to the
    masters tuple once — filtering ``acute.masters`` at the top of the function instead of
    inside rule 2's generator — this reading would be ``CALM``, the dial would go quiet on a
    master at its warning level, and the demotion would have become a deletion. The filter
    belongs to one rule, and this is the test that says so.
    """
    at_warning = PROVISIONAL_WARNING
    assert PROVISIONAL_WARNING <= at_warning < PROVISIONAL_STRESS

    state = candidate_state_for_one_reading(
        breadth=0.0,
        acute=acute_of_rows((at_warning, False), (0.10, True)),
        count=count_of(0),
        breadth_20_rows_ago=None,
        trend_confirmed=False,
    )

    assert state is State.WATCH


def test_a_watch_only_master_is_still_required_back_under_exit_before_recovery():
    """Rule 5 reads EVERY master, eligible or not — the exit limb is not filtered either.

    Two readings, one bit of data apart. In both, the eligible master is at 0.20 (well under
    EXIT) and ``trend_confirmed`` is ``True``, so rule 5's whole single-reading condition
    rests on the DEMOTED master:

    * parked at 0.55 — in the hysteresis gap, ABOVE exit — the answer is ``CALM``. "Every
      master back under its exit threshold" is not satisfied, and a rule 5 that skipped
      ineligible masters would wrongly read ``RECOVERY`` here.
    * at 0.40, under exit, everything else identical — the answer is ``RECOVERY``.

    The second reading is what proves the first: without it, ``CALM`` could be any other
    unmet condition rather than the demoted master holding recovery back.

    **AND THIS IS THE DIRECTION THE DEMOTION MUST NOT BE SYMMETRIC IN.** A master that may
    not DECLARE a crash must still be able to DELAY the all-clear; R2D2 asked for the row to
    be capped below ALARM, not for it to be ignored, and "ignored" here would mean the
    product announcing a recovery while a demoted master was still elevated. Rule 5 is late
    by design (DECISION-RULE.md §6) and an eligibility filter would have made it early.

    ``RECOVERY`` here is a CANDIDATE and not a verdict, as everywhere in this file: the
    previous-state and consecutive-readings halves of rule 5 are the wrapper's.
    """
    still_elevated = 0.55
    back_under_exit = 0.40
    assert PROVISIONAL_EXIT < still_elevated < PROVISIONAL_WARNING
    assert back_under_exit <= PROVISIONAL_EXIT

    held_back = candidate_state_for_one_reading(
        breadth=0.0,
        acute=acute_of_rows((still_elevated, False), (0.20, True)),
        count=count_of(0),
        breadth_20_rows_ago=None,
        trend_confirmed=True,
    )
    recovering = candidate_state_for_one_reading(
        breadth=0.0,
        acute=acute_of_rows((back_under_exit, False), (0.20, True)),
        count=count_of(0),
        breadth_20_rows_ago=None,
        trend_confirmed=True,
    )

    assert held_back is State.CALM
    assert recovering is State.RECOVERY


def test_rule_3_breadth_alone_alarms_with_nothing_counted_and_every_master_quiet():
    """Rule 3 SINCE WO-1.3e: breadth at the high band is ``ALARM`` with NOTHING counted.

    **THIS READING DID NOT FIRE BEFORE WO-1.3e AND THAT IS THE POINT.** The rule read
    ``breadth >= B_high AND count >= k``; ``count_of(0)`` made the second term false, so the
    answer was ``CALM``. R2D2's WO-1.3b finding B3 recommends dropping the count conjunct as
    an interim measure, and the widening is deliberate: breadth is now the WHOLE of rule 3.

    Isolation, term by term:

    * Rule 2 false — both masters sit at 0.55, under STRESS (and both are eligible, so it
      is the SCORE that fails the rule here and not the demotion; the demotion tests below
      hold the score high instead).
    * Rule 4's master limb false — 0.55 is under WARNING (0.6) too.
    * Rule 4's breadth limb false — the lookback is ``None``, so "rising" cannot be
      established at all, which is what makes ``ALARM`` here unambiguously rule 3's.
    * Rule 5 false — 0.55 is ABOVE the exit threshold (0.5), so "every master under exit"
      does not hold. The masters are deliberately parked in the 0.5-0.6 gap, which is the
      hysteresis band :class:`Master` enforces and the one place where no rule fires.
    """
    breadth = 0.60
    count = count_of(0)
    quiet = 0.55
    assert breadth >= PROVISIONAL_BREADTH_HIGH
    assert count.count == 0
    assert PROVISIONAL_EXIT < quiet < PROVISIONAL_WARNING

    state = candidate_state_for_one_reading(
        breadth=breadth,
        acute=acute_of(quiet, quiet),
        count=count,
        breadth_20_rows_ago=None,
        trend_confirmed=False,
    )

    assert state is State.ALARM


def test_rule_3_a_high_count_without_the_breadth_does_not_alarm():
    """THE OTHER HALF OF THE DROP: ``count`` is not a rule 3 term in EITHER direction.

    Dropping a conjunct could be read two ways — "the count is no longer REQUIRED alongside
    breadth", or "the count is no longer part of the condition at all" — and only the second
    is what WO-1.3e did. This reading separates them: EVERY considered indicator is at or
    beyond ``COUNT_THRESHOLD`` (6 of 6, twice ``PROVISIONAL_COUNT_K``) while breadth sits
    well under the high band. If the count had become a sufficient term of rule 3 in its own
    right, this would be ``ALARM``.

    It is ``CALM``: the masters are in the 0.5-0.6 hysteresis gap (rules 2, 4's master limb
    and 5 all false), the lookback is ``None`` (rule 4's breadth limb cannot fire), and
    breadth 0.20 is under the mid band as well as the high one.

    The reading is INTERNALLY ODD — six indicators at 0.9+ would not yield a breadth of 0.20
    through the real banded mean — and it is constructed that way on purpose, which is this
    file's "CONSTRUCTED, NOT PIPED" rule doing its job: the function admits breadth and count
    as independent arguments and cannot check that they came from one reading (its own
    DECLARED LIMIT says so), so the only way to show that it ignores one of them is to hand
    it a pair no real reading would produce.
    """
    breadth = 0.20
    count = count_of(6)
    quiet = 0.55
    assert count.count >= PROVISIONAL_COUNT_K
    assert breadth < PROVISIONAL_BREADTH_MID < PROVISIONAL_BREADTH_HIGH
    assert PROVISIONAL_EXIT < quiet < PROVISIONAL_WARNING

    state = candidate_state_for_one_reading(
        breadth=breadth,
        acute=acute_of(quiet, quiet),
        count=count,
        breadth_20_rows_ago=None,
        trend_confirmed=False,
    )

    assert state is State.CALM


def test_rule_4_breadth_rising_past_the_mid_band_watches_with_every_master_quiet():
    """Rule 4, BREADTH LIMB ALONE: no master is at warning, and breadth genuinely rose.

    0.30 twenty rows ago, 0.40 now: higher by 0.10, which clears
    ``PROVISIONAL_BREADTH_RISE_DEADBAND`` (0.02) as well as being strictly higher, and at or
    past the mid band (0.35). Held false elsewhere:

    * Rule 2 and rule 4's master limb — both masters at 0.55, under WARNING.
    * Rule 3 — breadth 0.40 is under the high band (0.55) AND nothing is counted, so
      neither half of its conjunction holds.
    * Rule 5 — 0.55 is above exit, and ``trend_confirmed`` is ``False`` besides.

    So the ONLY condition true in the whole precedence is the one this test names.
    """
    earlier, here = 0.30, 0.40
    quiet = 0.55
    assert here > earlier + PROVISIONAL_BREADTH_RISE_DEADBAND
    assert PROVISIONAL_BREADTH_MID <= here < PROVISIONAL_BREADTH_HIGH
    assert quiet < PROVISIONAL_WARNING

    state = candidate_state_for_one_reading(
        breadth=here,
        acute=acute_of(quiet, quiet),
        count=count_of(0),
        breadth_20_rows_ago=earlier,
        trend_confirmed=False,
    )

    assert state is State.WATCH


def test_rule_4_a_master_at_warning_watches_even_though_breadth_fell():
    """Rule 4, MASTER LIMB ALONE: breadth did NOT rise, and one master is at warning.

    The companion to the test above, and the pair is the point: the two limbs of rule 4 are
    joined by OR, so each one has to be shown firing with the other plainly false. Here
    breadth FELL (0.45 twenty rows ago, 0.40 now), so no reading of "rising" admits it.

    * Rule 2 false — 0.70 is under STRESS (0.85).
    * Rule 3 false — breadth under the high band, nothing counted.
    * Rule 5 false — 0.70 is well above exit.
    """
    earlier, here = 0.45, 0.40
    at_warning = 0.70
    assert here < earlier
    assert PROVISIONAL_WARNING <= at_warning < PROVISIONAL_STRESS

    state = candidate_state_for_one_reading(
        breadth=here,
        acute=acute_of(at_warning, 0.10),
        count=count_of(0),
        breadth_20_rows_ago=earlier,
        trend_confirmed=False,
    )

    assert state is State.WATCH


def test_rule_4_cannot_confirm_rising_when_there_are_fewer_than_20_rows_of_history():
    """``breadth_20_rows_ago=None`` does not fire rule 4's breadth limb — and does not lie.

    THIS IS ``test_rule_4_breadth_rising...``'s READING WITH ONE ARGUMENT CHANGED. Breadth
    is the same 0.40, past the mid band, and the masters are the same two quiet 0.55s; only
    the earlier breadth is gone, as it is for the first 20 evaluation rows of a dial's life.
    The answer moves from ``WATCH`` to ``CALM``, which establishes that the lookback is a
    REQUIRED term of that limb and not an optimisation.

    **AND THE REASON THIS IS THE RIGHT ANSWER RATHER THAN A CONVENIENT ONE.** ``None`` means
    "cannot confirm rising", never "did not rise", and the two differ in what they would
    license. They agree HERE because rule 4's limb needs a confirmed rise to fire — a young
    history cannot manufacture a WATCH. They would NOT agree if the absence were allowed to
    satisfy a rule, which is why the per-master limb is untouched by it: a master at warning
    still fires rule 4 on a one-row-old history, as
    ``test_rule_4_a_master_at_warning...`` shows with a lookback that exists. No rule in
    spec §3 reads a missing lookback as evidence of calm.
    """
    here = 0.40
    quiet = 0.55
    assert here >= PROVISIONAL_BREADTH_MID

    state = candidate_state_for_one_reading(
        breadth=here,
        acute=acute_of(quiet, quiet),
        count=count_of(0),
        breadth_20_rows_ago=None,
        trend_confirmed=False,
    )

    assert state is State.CALM


def test_rule_4_a_rise_smaller_than_the_deadband_is_not_a_rise_and_does_not_watch():
    """THE DEADBAND, AND THE DEFECT IT CLOSES WAS LIVE (R2D2's finding B1, WO-1.3e).

    Breadth sits AT the mid band and ticks up by half the deadband. Before WO-1.3e rule 4's
    limb read a bare ``here > earlier``, so this reading — and an uptick of 0.0001, which is
    what R2D2 actually watched happen on the live dials — turned CALM into a WATCH candidate,
    and the next equally tiny downtick turned it back. Breadth is a banded weighted mean of
    scaled scores; its last decimals are the bands' arithmetic, not the market. The answer
    is CALM: nothing in this reading is evidence of a rise.

    THE SECOND READING IS THE BOUNDARY AND IT IS THE SAME CLAIM. A move of EXACTLY the
    deadband is not a rise either, because "rising" stayed a strict ``>`` — the same reason
    an unchanged number never counted. One tick past the deadband is the next test, and the
    three together say where the edge is rather than that there is one somewhere.

    Held false elsewhere, as every test in this file must: both masters at 0.55 (under
    WARNING, so rule 2 and rule 4's master limb are out, and above EXIT so rule 5 is too,
    ``trend_confirmed`` being ``False`` besides), breadth under the high band with nothing
    counted (rule 3).
    """
    earlier = PROVISIONAL_BREADTH_MID
    quiet = 0.55
    assert quiet < PROVISIONAL_WARNING

    for here in (earlier + PROVISIONAL_BREADTH_RISE_DEADBAND / 2,
                 earlier + PROVISIONAL_BREADTH_RISE_DEADBAND):
        assert here > earlier
        assert PROVISIONAL_BREADTH_MID <= here < PROVISIONAL_BREADTH_HIGH

        state = candidate_state_for_one_reading(
            breadth=here,
            acute=acute_of(quiet, quiet),
            count=count_of(0),
            breadth_20_rows_ago=earlier,
            trend_confirmed=False,
        )

        assert state is State.CALM


def test_rule_4_a_rise_bigger_than_the_deadband_is_still_a_rise_and_still_watches():
    """THE COMPANION, AND THE PAIR IS THE POINT: the deadband narrows the limb, not closes it.

    The identical reading as the test above with ONE number changed — breadth rises by twice
    the deadband instead of by half of it — and the answer moves from CALM back to WATCH. A
    deadband that suppressed rule 4's breadth limb outright would pass that test and fail
    this one, and suppressing the limb is not what finding B1 asked for: a genuine move in
    breadth must still be able to say WATCH on its own.
    """
    earlier = PROVISIONAL_BREADTH_MID
    here = earlier + PROVISIONAL_BREADTH_RISE_DEADBAND * 2
    quiet = 0.55
    assert PROVISIONAL_BREADTH_MID <= here < PROVISIONAL_BREADTH_HIGH
    assert quiet < PROVISIONAL_WARNING

    state = candidate_state_for_one_reading(
        breadth=here,
        acute=acute_of(quiet, quiet),
        count=count_of(0),
        breadth_20_rows_ago=earlier,
        trend_confirmed=False,
    )

    assert state is State.WATCH


def test_rule_5_every_master_under_exit_and_the_trend_confirmed_is_recovery():
    """Rule 5: both conditions, and the second assertion is that it really is BOTH.

    Every master back under the exit threshold (0.40 and 0.20, both ≤ 0.5) and
    ``trend_confirmed=True``. Held false elsewhere:

    * Rules 2 and 4's master limb — 0.40 is under WARNING, let alone STRESS.
    * Rule 3 — breadth 0.10 is under the high band, nothing counted.
    * Rule 4's breadth limb — and this one is chosen to be interesting rather than merely
      absent: breadth DID rise (0.05 to 0.10) and the limb still does not fire, because 0.10
      is under the mid band. The limb is a conjunction and this reading separates its terms.

    Then the same reading with ``trend_confirmed=False`` is run again: it falls through to
    ``CALM``. "Both conditions required, never either" is DECISION-RULE.md §6's "late by
    design" and a `RECOVERY` that could be reached on quiet masters alone would be this
    product announcing the end of a crash because the data went quiet.

    **THIS IS A CANDIDATE AND NOT A VERDICT.** Rule 5's real condition begins "the dial's
    PREVIOUS state was ``ALARM``", and this function is built not to know the previous
    state; the ``for persistence consecutive readings`` half is likewise outside it. Both are
    the next round's wrapper's to check, and nothing here asserts that this ``RECOVERY``
    would survive them.
    """
    under_exit = (0.40, 0.20)
    earlier, here = 0.05, 0.10
    assert all(score <= PROVISIONAL_EXIT for score in under_exit)
    assert here > earlier and here < PROVISIONAL_BREADTH_MID

    recovering = candidate_state_for_one_reading(
        breadth=here,
        acute=acute_of(*under_exit),
        count=count_of(0),
        breadth_20_rows_ago=earlier,
        trend_confirmed=True,
    )
    without_the_trend = candidate_state_for_one_reading(
        breadth=here,
        acute=acute_of(*under_exit),
        count=count_of(0),
        breadth_20_rows_ago=earlier,
        trend_confirmed=False,
    )

    assert recovering is State.RECOVERY
    assert without_the_trend is State.CALM


def test_rule_6_nothing_fired_is_calm_and_a_confirmed_trend_alone_does_not_recover():
    """Rule 6: the last branch of the precedence, reached with every rule above it false.

    The masters sit at 0.55 — in the hysteresis gap, above exit and below warning — so rules
    2, 4 and 5 are all false at once, which is the only place in the threshold ordering where
    that is true. Breadth 0.20 with nothing counted and no lookback closes rules 3 and 4.

    ``trend_confirmed`` is ``True`` on purpose. It is the one input that might tempt a
    reading toward ``RECOVERY``, and rule 5 needs the masters under EXIT as well; a
    confirmed trend over masters that have NOT come back down is exactly the "either
    condition" reading DECISION-RULE.md §6 refuses. The answer is ``CALM``.

    ``CALM`` here is an ANSWER and not a default — :data:`State.CALM`'s own docstring says
    so, and ``test_rule_1...`` is the other half of that sentence: a reading that could not
    be resolved gets ``UNKNOWN``, never this.
    """
    quiet = 0.55
    assert PROVISIONAL_EXIT < quiet < PROVISIONAL_WARNING

    state = candidate_state_for_one_reading(
        breadth=0.20,
        acute=acute_of(quiet, quiet),
        count=count_of(0),
        breadth_20_rows_ago=None,
        trend_confirmed=True,
    )

    assert state is State.CALM
