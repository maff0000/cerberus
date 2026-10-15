"""THE OTHER HALF OF SPEC §3's STATE MACHINE: what the dial OFFICIALLY says, over time.

WO-1.3a round 5, built to ``governance/WO-1.3a-engine-spec.md`` §3 (the second-leg rule,
rule 5's previous-state condition, ``persistence``) and §7 (how persistence is counted, and
the 20-row breadth lookback).

AMENDED BY WO-1.3e ROUND 1 for R2D2's WO-1.3b finding B2: ``ALARM`` may no longer exit
directly to ``CALM``. One candidate correction, its own section below.

AMENDED AGAIN BY WO-1.3e ROUND 2 for R2D2's finding B1, the cadence/unit mismatch:
:data:`PROVISIONAL_PERSISTENCE` reads 5 rather than 3, and the constant's own comment carries
both the reason and the transition rates behind the number. The mismatch itself was never
this module's — persistence here has always been counted in READINGS and still is; what
WO-1.3e changes outside this file is what a reading IS (one pass a day, not one every 300
seconds), which is what makes "5 readings" mean the 5 trading days DECISION-RULE.md §4
describes. :data:`BREADTH_LOOKBACK_ROWS` is unchanged for the same reason, written out on it.

Nothing else in R2D2's RED verdict is addressed here — rule 3's breadth-only fix (B3), the
``curve_master``/``fiscal_master`` demotion and the UNKNOWN-exit floor are later rounds of
the same WO and this module is deliberately unchanged for them.

====================================================================================
WHY THIS IS HERE AND NOT IN ``engine/statistics.py`` BESIDE THE CANDIDATE FUNCTION
====================================================================================

:func:`~crash_detector.engine.statistics.candidate_state_for_one_reading` is one reading's
numbers in, one :class:`~crash_detector.engine.statistics.State` out — no memory, no store,
and spec §9 item 1 placed it in ``engine/`` for that reason. **THIS function's input and
output are both :class:`evaluator.history_store.MachineStateRow`**: it reads the dial's
preceding rows and it returns the row to append. That type lives in this package, OUTSIDE
``src/crash_detector``, because the application tree in ``src/`` owns no durable store (the
reason :mod:`ingestion` is outside it too, stated in this package's own ``__init__``).

So the choice is not a matter of taste: putting this function in ``engine/statistics.py``
would make ``src/crash_detector`` import ``evaluator``, inverting the one-way dependency
``history_store`` already establishes (``evaluator`` → ``crash_detector``, never back). The
candidate function stays where the PO put it; the wrapper lives with the row shape it is
built out of, and imports the engine the same way everything else in this package does.

====================================================================================
WHAT THIS FUNCTION DECIDES, IN THE ORDER SPEC §3 DECIDES IT
====================================================================================

1. **Rule 1 is not persistence-gated, in EITHER direction.** An unresolvable reading is
   ``UNKNOWN`` on the reading it happens (spec §3 rule 1: *"Stop; no other rule overrides
   this"*), and a resolvable reading is NOT held at ``UNKNOWN`` while a clock runs. The
   second half is forced rather than chosen: ``machine_state_history``'s own
   ``state_fields_coherent`` CHECK makes an ``UNKNOWN`` row carrying numbers
   UNREPRESENTABLE (CD-RT-001), so a reading that HAS a breadth, an acute and a count
   cannot be written as ``UNKNOWN`` — the only way to hold the old state for two more
   readings would be to drop the numbers this evaluation really did observe. The schema
   settles the question the spec is silent on, and this is **ROGUE'S CALL, FLAGGED**: spec
   §3 says nothing about leaving ``UNKNOWN`` and R2D2 may rule otherwise in WO-1.3b.
2. **Rule 5's previous-state condition**, which the candidate function documents that it
   cannot apply: a ``RECOVERY`` candidate whose dial was NOT in ``ALARM`` on its last row
   is not a recovery at all. Spec §3's own "Else" chain falls through past rule 5 to rule
   6, so the candidate becomes ``CALM`` — and it is the CANDIDATE that is corrected here,
   before persistence, not the official state after it.
3. **``ALARM``'s exit is corrected to ``WATCH``** (R2D2's WO-1.3b finding B2, remediated
   in WO-1.3e): the dial's last official state ``ALARM`` and this reading's candidate
   ``CALM`` → the candidate is corrected to ``WATCH``. ``ALARM`` leaves only toward
   ``WATCH`` or toward ``RECOVERY``, never to ``CALM`` in one step. The same shape, the
   same place and the same reason as item 2 — a previous-state condition the memoryless
   candidate function cannot apply, applied to the CANDIDATE before any clock runs. It has
   its own section below, because whether it fires once or on every reading is a judgement
   call and the reasoning is load-bearing.
4. **The second-leg rule** (spec §3, DECISION-RULE.md §6): previous official state
   ``RECOVERY`` and this reading's candidate ``ALARM`` (rule 2 or rule 3 fired again) →
   ``ALARM`` NOW, no persistence, counter cleared. A relapse out of recovery is the one
   transition this product will not make the market wait :data:`PROVISIONAL_PERSISTENCE`
   readings for.
5. **Normal persistence** (spec §3, §7's reading of it): the official state changes to a new
   candidate only once THIS reading and the immediately preceding rows have all produced
   that same candidate — :data:`PROVISIONAL_PERSISTENCE` rows in total, Trinity's provisional
   reading of WHICH rows count and WO-1.3e's of how many, neither settled doctrine.

====================================================================================
``ALARM`` NEVER EXITS DIRECTLY TO ``CALM`` — AND WHY THE CORRECTION NEEDS NO CLOCK
====================================================================================

**THE DEFECT THIS CORRECTS WAS LIVE.** R2D2's WO-1.3b audit (verdict RED, finding B2) found
this state machine stepping a dial from ``ALARM`` to ``CALM`` with no intermediate ``WATCH``.
The route is item 2's mirror image and round 5 closed only item 2's direction: with
``trend_confirmed`` hard-wired ``False`` (spec §7's disclosed scope cut) rule 5 cannot fire,
so a dial sitting in ``ALARM`` whose masters and breadth have genuinely quietened falls
through spec §3's "Else" chain past rules 2, 3, 4 and 5 to rule 6 — ``CALM``.
:data:`PROVISIONAL_PERSISTENCE` such readings and the dial officially says deploy. DECISION-RULE.md §3 asks for exactly the
opposite ("the halt/exit threshold is hair-trigger; the re-entry threshold is demanding")
and §6's hysteresis is the mechanism it names for it; a one-step ``ALARM`` → ``CALM`` is not
hysteresis, it is the absence of it.

So: **previous official state ``ALARM`` and a ``CALM`` candidate → the candidate is
``WATCH``.** ``ALARM`` may exit toward ``WATCH`` or toward ``RECOVERY``, and nowhere else.
``WATCH`` is the right floor rather than some new state because DECISION-RULE.md §6 already
assigns it exactly the permission this case needs — "halt new tranches; hold existing" — and
already uses it as the conservative read of a state that must not be mistaken for ``CALM``
(``UNKNOWN`` is "treated as WATCH for permission purposes, never as CALM").

**EVERY READING, OR ONLY THE FIRST ONE? EVERY READING — AND THE CORRECTION THEREFORE NEEDS
NO PERSISTENCE-LIKE GATE OF ITS OWN. ROGUE'S CALL, AND THE REASONING IS THE POINT.** The
condition is read fresh off the preceding row on every reading (``previous.machine_state is
ALARM`` and ``candidate is CALM``); there is no "have I corrected already" memory, no new
column and no second clock. The reason that is sufficient rather than lazy is that **the
correction's own trigger is extinguished by the transition it causes**:

* Reading 1 out of ``ALARM``: candidate ``CALM`` → corrected ``WATCH``. Normal persistence
  starts a fresh count toward ``WATCH`` — the preceding row's candidate was not ``WATCH``,
  so there is no streak to extend — and the official state stays ``ALARM``.
* Readings 2 .. :data:`PROVISIONAL_PERSISTENCE`: the same correction fires again on the same
  condition, the count reaches :data:`PROVISIONAL_PERSISTENCE`, and the official state
  becomes ``WATCH``.
* The reading after that: the preceding row now says ``WATCH``, not ``ALARM``. **The correction's
  condition is false and it stops applying by itself** — the candidate stays ``CALM`` and
  ordinary persistence counts toward ``CALM`` from a dial that is genuinely in ``WATCH``.

``CALM`` is still reachable from ``ALARM``; it now costs two transitions instead of one,
which is what "the re-entry threshold is demanding" means. Nothing is suppressed, and no
state is made unreachable.

**THE FIRST-READING-ONLY ALTERNATIVE IS NOT MERELY MORE MACHINERY — IT REINSTATES THE
DEFECT**, and that is what settles the question rather than a preference for less code.
Correct only the first reading and the candidate stream out of ``ALARM`` reads ``WATCH``,
``CALM``, ``CALM``, ...: reading 2's switch to a different pending candidate destroys the
``WATCH`` streak (this module's own rule, above — the new candidate writes 1), the ``CALM``
streak then completes one reading later than it otherwise would, and the official state steps
``ALARM`` → ``CALM`` with no ``WATCH`` ever having become official. The illegal jump returns
one reading late, now wearing a correction that fired once. A gate that holds for one reading
in :data:`PROVISIONAL_PERSISTENCE` is not a gate.

**IT CANNOT COLLIDE WITH ITEM 2, AND THE CONDITIONS PROVE THAT RATHER THAN THE ORDERING.**
Item 2 corrects a ``RECOVERY`` candidate to ``CALM`` only when the dial was NOT in ``ALARM``;
this correction requires that it WAS. The two previous-state conditions are mutually
exclusive, so item 2 can never hand this one the ``CALM`` it would act on, and writing the
two in the opposite order would compute the same candidate. Nor can it disturb the second-leg
rule or rule 1: each of those needs a candidate this correction does not produce (``ALARM``
out of ``RECOVERY``, and ``UNKNOWN`` respectively). A dial with no history at all has no
previous ``ALARM`` to leave, so its first reading is untouched.

====================================================================================
``persistence_counter`` IS A TRANSITION CLOCK, NOT AN AGE — THE INVARIANT, STATED
====================================================================================

**``persistence_counter > 0`` EXACTLY WHILE A CANDIDATE THE DIAL IS NOT IN IS
ACCUMULATING.** Equivalently, on every row this function returns::

    persistence_counter > 0  ⟺  candidate_state is not machine_state

Readings counted are "this one and the ones before it that agreed", so the first reading at
a new candidate writes 1, the second 2, and the :data:`PROVISIONAL_PERSISTENCE`-th
TRANSITIONS — at which point the
clock has been spent and the row's own ``machine_state`` is the record that it fired, so the
counter reads 0 again. ``0`` therefore means "nothing pending", never "the dial is new".

Two consequences worth naming, both deliberate:

* **The first-ever reading for a dial writes ``persistence_counter = 0``** (spec is silent;
  ROGUE'S CALL). There is no previous state to transition FROM, so the candidate becomes
  official immediately — and with the candidate official there is by definition nothing
  accumulating. Writing ``1`` would read as "one reading toward a change" on a row where no
  change is pending, and would break the invariant above on the only row that cannot
  possibly be mid-transition.
* **A reading whose candidate equals the official state writes 0**, which is spec §3's
  *"reverting mid-count resets the counter to zero"* — the revert IS the candidate coming
  back to the state the dial is already in.
* **A reading that switches from one pending candidate to a DIFFERENT pending candidate
  writes 1, not 0** (ROGUE'S CALL; spec §3 addresses only the revert). The new candidate
  has genuinely been computed once, and calling that 0 would make its transition take four
  readings instead of the three spec §3 asks for. The OLD candidate's streak is destroyed
  either way, which is what "breaking the streak" means here.

====================================================================================
DECLARED LIMITS
====================================================================================

**THE HISTORY'S ORDER IS THE CALLER'S CLAIM AND IS NOT CHECKED HERE.** ``history`` must be
most-recent-first, which is exactly what :meth:`evaluator.history_store.
MachineStateHistoryStore.recent` returns. It cannot be verified from the rows: ``recent()``
orders by the file's own row id and NOT by ``as_of`` — deliberately, because a clock that
moved must not be able to reorder the persistence count — and ``MachineStateRow`` does not
carry its row id. Sorting by ``as_of`` here would therefore be a different order than the
one the count is defined over, so nothing is sorted and nothing is asserted.

**WHAT IS CHECKED** is the one cross-dial claim that CAN be: every history row's ``dial_id``
must equal the dial the reading's ``acute`` carries, or this function refuses. The dial is
read OFF the reading (both :class:`~crash_detector.engine.statistics.Acute` and
``AcuteUnknown`` carry it) rather than taken as a parameter, so there is no argument through
which one dial's history could be handed another dial's reading.

**``trend_confirmed`` IS STILL A CALLER-SUPPLIED PARAMETER** (spec §7's explicit scope cut),
passed straight through to the candidate function, and this round does not compute it from
``spx_vs_200dma`` or anything else. It is NOT stored on the row either, which means a
``RECOVERY`` candidate's second condition is not recoverable from the history a year later
— named here as an OWED COLUMN for the round that computes it, not as a gap nobody noticed.

**THE 0.5 EXIT THRESHOLD IS STILL NOT AN INDEPENDENT GATE, AND THIS ROUND DOES NOT MAKE IT
ONE.** R2D2's recommended fix (1) has two halves; WO-1.3e round 1 delivers the first —
``ALARM`` exits only toward ``WATCH`` — and leaves the second standing.
``PROVISIONAL_EXIT`` is read in exactly one place, rule 5 inside the candidate function,
which ``trend_confirmed=False`` still makes unreachable; so leaving ``ALARM`` for ``WATCH``
is NOT today conditioned on every master having fallen back under its exit threshold, and a
dial can reach ``WATCH`` out of ``ALARM`` on rule 6's calm reading alone. Named here as the
remainder of finding B2, owed by the round that computes ``trend_confirmed`` or lifts the
exit check out of rule 5 — not as a gap nobody noticed.

**NOTHING HERE WRITES.** The row comes back ready to append; the append, its ``written_utc``
and the store handle belong to the evaluator pass (spec §9 item 2), which is the next step
and is not this function.
"""

from __future__ import annotations

from datetime import datetime
from typing import Union

from crash_detector.engine.statistics import (
    Acute,
    AcuteUnknown,
    Count,
    State,
    candidate_state_for_one_reading,
)

from evaluator.history_store import MachineStateRow

__all__ = ["PROVISIONAL_PERSISTENCE", "BREADTH_LOOKBACK_ROWS", "official_state_for_dial"]

#: PROVISIONAL (spec §3, ``persistence``, itself reading DECISION-RULE.md §10's "unset —
#: calibration" row). How many consecutive readings must produce the same candidate before
#: the official state changes to it: THIS reading plus the 4 immediately preceding rows
#: (spec §7's disambiguation of WHICH rows count — Trinity's provisional reading, flagged
#: there as such — with this constant setting HOW MANY).
#:
#: **5 SINCE WO-1.3e, WAS 3 (R2D2's WO-1.3b finding B1), AND THE UNIT IS WHY.** Spec §3 and
#: DECISION-RULE.md §4 both say "3", and §4 says it as "3 consecutive DAILY readings" — but
#: the deployed evaluator was passing every 300 seconds, so 3 readings was ~15 minutes and
#: the number was never the one the doctrine had chosen. WO-1.3e sets the cadence to one
#: pass a day (``CD_EVALUATE_INTERVAL_SECONDS`` 86400, ``deploy/live-dev/compose.yaml``), so
#: a reading is a day again, and at that cadence R2D2 measured the transition rates this
#: product would actually run at: **~5.9 transitions/year at 3 readings, ~3.6 at 5, ~1.4 at
#: 10.** 5 is R2D2's recommendation and the number is quoted here because it is the ONLY
#: evidence behind the choice — this is a judgement about how often a regime instrument at a
#: 3-12 month horizon should be allowed to change its mind, not a calibration.
#:
#: **THE PO'S DOCUMENTS STILL READ 3 AND THIS IS A DISCLOSED DIVERGENCE, NOT AN AMENDMENT.**
#: DECISION-RULE.md §4 and ``governance/WO-1.3a-engine-spec.md`` §3 are the Product Owner's
#: and Trinity's to change; both mark the number *provisional*, which is the licence this
#: round acts on, but neither has been rewritten here. A reader who needs doctrine should
#: read them and treat the gap as open until the PO closes it.
#:
#: Declared HERE rather than beside the engine's other provisional numbers because this is
#: the only module that reads it — ``engine/statistics.py`` holds the thresholds its own
#: rules compare against and says in its docstring that it does no persistence counting, so
#: a persistence constant sitting there would be a number nothing in that module uses.
#: Not calibrated, not backtested, and nothing here may be read as a tuned value.
PROVISIONAL_PERSISTENCE = 5

#: PROVISIONAL (spec §3 rule 4 / §7). How far back "breadth rising over the last 20
#: readings" looks. Spec §7's provisional reading is a LOOKBACK COMPARISON and not a
#: monotonicity requirement, so one earlier number is the whole of it: the row 20 back,
#: which in a most-recent-first history is index 19.
#:
#: **UNCHANGED BY WO-1.3e, AND DELIBERATELY SO.** The number is "20 READINGS" under any
#: cadence and that is what spec §3 rule 4 asks for; what R2D2's finding B1 broke was the
#: UNIT, not the count — at the deployed 300-second pass this lookback reached back about
#: 100 minutes while rule 4's own sentence says 20 readings of a daily instrument. With the
#: cadence now one pass a day, 20 rows is genuinely ~20 readings ≈ ~4 calendar weeks of
#: them, so the row count needed no compensating change and did not get one.
BREADTH_LOOKBACK_ROWS = 20


def _breadth_rows_ago(history: tuple) -> Union[float, None]:
    """The breadth from :data:`BREADTH_LOOKBACK_ROWS` evaluation-rows ago, or ``None``.

    **DERIVING THIS IS THIS FUNCTION'S JOB AND NOT THE CALLER'S.** The candidate function
    takes it as a raw parameter because it performs no query; by the time a caller has the
    dial's history in hand there is nothing left for them to decide, so leaving it to them
    would be leaving an off-by-one to be made twice.

    ``None`` means **"CANNOT CONFIRM RISING", NEVER "DID NOT RISE"** — the candidate
    function's own sentence, and the consequence is that rule 4's breadth limb cannot fire
    while its per-master limb is unaffected. Two ways it arises, and they mean the same
    thing here: fewer than 20 rows exist, or the row 20 back is an ``UNKNOWN`` row and
    carries no breadth at all (CD-RT-001 — an unresolvable reading has no number to
    compare against, and a young or interrupted history must not read as a calm one).
    """
    if len(history) < BREADTH_LOOKBACK_ROWS:
        return None
    return history[BREADTH_LOOKBACK_ROWS - 1].breadth


def _acute_rising(acute: Acute, previous: Union[MachineStateRow, None]) -> bool:
    """Is this reading's acute statistic above the one on the dial's last row?

    Strictly above: ``>``, because "rising" is a claim and an unchanged number does not
    make it.

    **A BOOL AND NOT A THIRD STATE, WHICH IS THE SCHEMA'S DOING AND IS FLAGGED.** With no
    earlier acute reading to compare against — the first ever row, or a preceding row that
    was ``UNKNOWN`` and carries no acute — "rising" cannot be confirmed, and the honest
    answer is the one ``breadth_20_rows_ago`` gets to give: *cannot confirm*. The column
    cannot hold it: ``acute_rising`` is in ``machine_state_history``'s own statistics set,
    which a resolvable row may not leave NULL. ``False`` is written, as the answer that
    claims less, and NOTHING IN THIS ROUND READS IT — rule 4 reads breadth, and rule 5's
    "higher low on the acute statistic" is inside the deferred ``trend_confirmed``. If a
    later round makes this value load-bearing it needs its third state in the column
    FIRST; recorded here as an open question, the same shape as ``count``'s known defect.
    """
    if previous is None or previous.acute is None:
        return False
    return acute.score > previous.acute


def official_state_for_dial(
    *,
    history: tuple,
    as_of: datetime,
    breadth: float,
    acute,
    count: Count,
    trend_confirmed: bool,
) -> MachineStateRow:
    """THE DIAL'S OFFICIAL STATE FOR THIS READING, as the row that is ready to be appended.

    ``history`` is this dial's recent rows, MOST RECENT FIRST, as
    :meth:`evaluator.history_store.MachineStateHistoryStore.recent` returns them — ask it
    for at least :data:`BREADTH_LOOKBACK_ROWS` so rule 4's lookback can be made at all;
    fewer rows than that is a history that is genuinely too young and is read as "cannot
    confirm rising", not as "did not rise". An EMPTY history is this dial's first ever
    evaluation and is handled explicitly (see the module docstring).

    ``breadth``, ``acute``, ``count`` and ``trend_confirmed`` are this reading's statistics,
    the same four values
    :func:`~crash_detector.engine.statistics.candidate_state_for_one_reading` takes, and
    their door is that function's: it admits the types and establishes the finiteness of
    ``breadth``, so nothing is re-checked here. ``as_of`` is the instant the evaluation read
    its inputs as of, and it is carried onto the row unexamined — ``written_utc`` is the
    store's argument at append time, not this function's business.

    Returns ONE :class:`~evaluator.history_store.MachineStateRow`, unwritten. It carries the
    official ``machine_state``, the ``candidate_state`` this reading computed (equal to the
    official state on a settled row, different while a transition accumulates), the
    ``persistence_counter`` and — unless the state is ``UNKNOWN``, which may carry no
    numbers at all — the breadth/acute/count detail the store's schema requires.
    """
    rows = tuple(history)
    dial_id = acute.dial_id
    for row in rows:
        if row.dial_id != dial_id:
            raise ValueError(
                f"this reading is the {dial_id!r} dial's and the history carries a "
                f"{row.dial_id!r} row. One dial's persistence count may not be continued "
                "from another dial's readings; the dial is read off the reading precisely "
                "so that a caller cannot pair the two."
            )
    previous = rows[0] if rows else None

    candidate = candidate_state_for_one_reading(
        breadth=breadth,
        acute=acute,
        count=count,
        breadth_20_rows_ago=_breadth_rows_ago(rows),
        trend_confirmed=trend_confirmed,
    )

    # RULE 5'S PREVIOUS-STATE CONDITION, applied to the CANDIDATE and before any clock
    # runs. The candidate function's own docstring says exactly this is the caller's: a
    # RECOVERY out of it means "everything about rule 5 that ONE reading can satisfy", and
    # with the dial's last row not ALARM, spec §3's "Else" chain falls past rule 5 to rule
    # 6. A dial with no history at all has no previous ALARM either, so its first reading
    # can never be a RECOVERY — which is the correct reading of "the dial was in ALARM".
    if candidate is State.RECOVERY and (
        previous is None or previous.machine_state is not State.ALARM
    ):
        candidate = State.CALM

    # ALARM MAY NOT EXIT STRAIGHT TO CALM (R2D2's WO-1.3b finding B2; module docstring has
    # the section). The candidate function cannot apply this either — it is a previous-state
    # condition and that function has no memory — so it is corrected HERE, in the same place
    # and the same style as rule 5's gate above, to the CANDIDATE and before any clock runs.
    #
    # ON EVERY READING WHILE THE DIAL IS STILL IN ALARM, not only the first: the condition is
    # read off the preceding row each time and is extinguished by the transition it causes
    # (once WATCH is official, `previous.machine_state` is no longer ALARM and this stops
    # firing by itself), so the normal persistence below is the only clock needed. Correcting
    # only the first reading would let the CALM streak complete on reading 4 and would put
    # the illegal jump straight back — reasoned out in full in the docstring.
    #
    # Disjoint from the gate above by construction: that one needs a dial NOT in ALARM, this
    # one needs a dial that WAS, so neither can feed the other.
    if previous is not None and (
        previous.machine_state is State.ALARM and candidate is State.CALM
    ):
        candidate = State.WATCH

    if candidate is State.UNKNOWN:
        # RULE 1, UNCONDITIONAL AND IMMEDIATE: "Stop; no other rule overrides this". No
        # clock, no previous state consulted, and the row carries no numbers because there
        # are none to carry (`AcuteUnknown` has no score field — the state and the absence
        # of statistics are the same fact, not two that have to be kept in agreement).
        official, counter = State.UNKNOWN, 0
    elif previous is None:
        # THE DIAL'S FIRST EVER EVALUATION. Nothing to persist against and nothing to
        # transition from: the candidate IS the official state, and the clock reads 0
        # because nothing is pending. (Module docstring: ROGUE'S CALL, spec is silent.)
        official, counter = candidate, 0
    elif previous.machine_state is State.RECOVERY and candidate is State.ALARM:
        # THE SECOND-LEG RULE (spec §3), BEFORE NORMAL PERSISTENCE AND OVERRIDING IT. The
        # relapse is immediate and "the persistence/recovery clock resets to zero" is the
        # spec's own phrase. It cannot collide with the rule-5 correction above: that one
        # needs a RECOVERY candidate and this one needs an ALARM.
        official, counter = State.ALARM, 0
    elif previous.machine_state is State.UNKNOWN:
        # LEAVING UNKNOWN IS IMMEDIATE TOO, and the schema is why (module docstring item 1):
        # this reading HAS a breadth, an acute and a count, and a row carrying numbers
        # cannot say UNKNOWN. Holding the old state would mean discarding the reading.
        official, counter = candidate, 0
    elif candidate is previous.machine_state:
        # THE DIAL IS WHERE IT SAYS IT IS. Nothing is accumulating, so the clock reads 0 —
        # spec §3's "reverting mid-count resets the counter to zero", which is this branch
        # whether the previous row's counter was running or not.
        official, counter = candidate, 0
    else:
        # NORMAL PERSISTENCE (spec §3, §7). The preceding row's counter is how many
        # readings have already produced the candidate IT recorded; this reading extends
        # that streak only if the candidate is the same one. `is` on the enum member, and
        # a preceding row with NO recorded candidate (NULL — a row older than the column)
        # cannot evidence a streak: it restarts the clock rather than completing it, so an
        # unrecorded candidate can only ever DELAY a transition.
        accumulated = (
            previous.persistence_counter
            if previous.candidate_state is candidate
            else 0
        )
        counter = accumulated + 1
        if counter >= PROVISIONAL_PERSISTENCE:
            # THE TRANSITION. This reading plus the ones before it all called for the same
            # state — PROVISIONAL_PERSISTENCE rows, spec §7's rule for which ones they are —
            # so the dial now says it. The clock is spent and
            # reads 0; the row's own machine_state is the record that it fired.
            official, counter = candidate, 0
        else:
            official = previous.machine_state

    if (official is State.UNKNOWN) != (type(acute) is AcuteUnknown):
        raise AssertionError(
            f"the resolver reached official state {official!r} from an "
            f"{type(acute).__name__} reading. The two are the same fact (spec §3 rule 1 is "
            "the only way to UNKNOWN and an unresolvable acute is the only way to rule 1), "
            "and a row that disagreed with its own statistics would be refused by "
            "machine_state_history's state_fields_coherent CHECK — loudly here is better "
            "than at the append."
        )

    if type(acute) is AcuteUnknown:
        return MachineStateRow(
            dial_id=dial_id,
            as_of=as_of,
            machine_state=official,
            candidate_state=candidate,
            persistence_counter=counter,
        )
    return MachineStateRow(
        dial_id=dial_id,
        as_of=as_of,
        machine_state=official,
        candidate_state=candidate,
        persistence_counter=counter,
        acute_rising=_acute_rising(acute, previous),
        breadth=breadth,
        acute=acute.score,
        acute_from_master_id=acute.from_master_id,
        # EVERY master's own score, not only the maximum: spec §3's rules 2, 4 and 5 read
        # per master, and RECOVERY's exit check reads the preceding rows' per-master detail.
        master_scores={master.master_id: master.score for master in acute.masters},
        indicator_count=count.count,
        count_at_or_beyond=count.at_or_beyond,
    )
