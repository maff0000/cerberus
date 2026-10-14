"""THE OTHER HALF OF SPEC §3's STATE MACHINE: what the dial OFFICIALLY says, over time.

WO-1.3a round 5, built to ``governance/WO-1.3a-engine-spec.md`` §3 (the second-leg rule,
rule 5's previous-state condition, ``persistence = 3``) and §7 (how persistence is counted,
and the 20-row breadth lookback).

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
3. **The second-leg rule** (spec §3, DECISION-RULE.md §6): previous official state
   ``RECOVERY`` and this reading's candidate ``ALARM`` (rule 2 or rule 3 fired again) →
   ``ALARM`` NOW, no persistence, counter cleared. A relapse out of recovery is the one
   transition this product will not make the market wait three readings for.
4. **Normal persistence** (spec §3, §7's reading of it): the official state changes to a new
   candidate only once THIS reading and the 2 immediately preceding rows have all produced
   that same candidate — 3 rows total, Trinity's provisional reading of "3 consecutive
   readings", flagged as such in the spec and not settled doctrine.

====================================================================================
``persistence_counter`` IS A TRANSITION CLOCK, NOT AN AGE — THE INVARIANT, STATED
====================================================================================

**``persistence_counter > 0`` EXACTLY WHILE A CANDIDATE THE DIAL IS NOT IN IS
ACCUMULATING.** Equivalently, on every row this function returns::

    persistence_counter > 0  ⟺  candidate_state is not machine_state

Readings counted are "this one and the ones before it that agreed", so the first reading at
a new candidate writes 1, the second 2, and the third TRANSITIONS — at which point the
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
#: the official state changes to it: THIS reading plus the 2 immediately preceding rows
#: (spec §7's disambiguation, Trinity's provisional reading, flagged there as such).
#:
#: Declared HERE rather than beside the engine's other provisional numbers because this is
#: the only module that reads it — ``engine/statistics.py`` holds the thresholds its own
#: rules compare against and says in its docstring that it does no persistence counting, so
#: a persistence constant sitting there would be a number nothing in that module uses.
#: Not calibrated, not backtested, and nothing here may be read as a tuned value.
PROVISIONAL_PERSISTENCE = 3

#: PROVISIONAL (spec §3 rule 4 / §7). How far back "breadth rising over the last 20
#: readings" looks. Spec §7's provisional reading is a LOOKBACK COMPARISON and not a
#: monotonicity requirement, so one earlier number is the whole of it: the row 20 back,
#: which in a most-recent-first history is index 19.
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
            # THE TRANSITION. This reading plus the 2 before it all called for the same
            # state (spec §7's 3 rows), so the dial now says it. The clock is spent and
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
