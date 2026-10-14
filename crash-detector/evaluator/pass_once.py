"""ONE EVALUATOR PASS: the raw store in, one ``machine_state_history`` row per dial out.

WO-1.3a round 6, spec §9 item 2 — the function the three preceding rounds were parts of.
Everything it needs already exists and NOTHING IS COMPUTED HERE: ``breadth`` is the
existing banded weighted mean read out of the existing per-dial evaluation (spec §1,
"read out of the existing per-dial evaluation exactly as it is today"), ``acute`` and
``count`` are :mod:`crash_detector.engine.statistics`, the state is
:func:`evaluator.resolve.official_state_for_dial`, and the row is
:class:`evaluator.history_store.MachineStateRow`. This module is the WIRING between them,
and the only new judgements in it are the four stated below.

====================================================================================
1. THE RAW STORE IS OPENED READ-ONLY, BY PATH, AND THERE IS NO OTHER DOOR
====================================================================================

This process must never write to the collector's raw store — the same discipline the GUI
observes (``ingestion/store.py``'s ``read_only=True``, WO-1.4). That discipline is
STRUCTURAL here rather than observed: the raw store arrives as a **path**, not as a
handle, so there is no parameter through which a writable connection could be passed, and
:func:`_raw_reader` is the one expression in this module that opens it. A caller who wants
this pass to write to the raw store has no argument to do it with.

The history store is the opposite and arrives as an OPEN handle, because this process DOES
write there and the caller owns the file's lifetime across the two dials. The asymmetry is
the point: the one we may write to is handed to us open, and the one we may not write to we
open ourselves, closed.

====================================================================================
2. THE TWO DIALS ARE READ INDEPENDENTLY, AND THE SECOND READ IS NOT A BUG
====================================================================================

:func:`one_pass_for_both_dials` calls :func:`one_pass_for_dial` twice, and each call opens
the raw store and runs ``evaluate`` for itself. ``evaluate`` computes the PAIR, so each
call discards the other dial's reading.

That is deliberate (CD-AC-002). Carrying the other dial's reading out of a per-dial
function — or evaluating once and passing a ``DialSet`` down — would be the one thing this
product refuses: a place where both dials' numbers are in one caller's hands at once. Each
row is dated by its OWN inputs (``as_of``), so two reads a few milliseconds apart are two
honest readings and not one inconsistent one. The cost is one extra ``build_wiring()`` and
one extra banded mean per pass, on a cadence measured in minutes.

====================================================================================
3. ``trend_confirmed`` IS NOT COMPUTED. IT IS :data:`TREND_NOT_COMPUTED`, WHICH IS FALSE
====================================================================================

See the constant. It is a stated scope cut (spec §7), not a signal, and it is passed as a
NAMED constant rather than a literal ``False`` precisely so that the call site cannot be
read as "the trend was checked and did not confirm".

====================================================================================
4. A DIAL WITH NO READING AT ALL GETS AN UNKNOWN ROW, BUILT HERE
====================================================================================

If ``evaluate`` cannot produce a reading for a dial — a missing REQUIRED input, an empty
store — there is no magnitude, so there is no ``breadth``. :func:`_unknown_row` writes the
UNKNOWN row directly instead of routing through ``official_state_for_dial``; the reason is
in that function's own docstring and it is a missing number, not a shortcut.

Import route: ``PYTHONPATH=src:.`` from ``crash-detector/``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from crash_detector.dials.dialset import DIAL_IDS, EQUITY_DIAL_ID, MONETARY_DIAL_ID
from crash_detector.engine.evaluate import DIAL_SCORE_TYPES, evaluate
from crash_detector.engine.statistics import (
    State,
    count_for_one_dial,
    equity_crash_acute,
    monetary_debasement_acute,
)
from crash_detector.serving.dial_presentation import NotShown, present_dial
from evaluator.history_store import MachineStateHistoryStore, MachineStateRow
from evaluator.resolve import BREADTH_LOOKBACK_ROWS, official_state_for_dial
from ingestion.store import SqliteStore
from ingestion.wiring import build_wiring, observations_from_store

__all__ = [
    "TREND_NOT_COMPUTED",
    "PassWiringBroken",
    "one_pass_for_dial",
    "one_pass_for_both_dials",
]

#: **NOT A SIGNAL, NOT A MEASUREMENT, AND NOT A FINDING THAT THE TREND DID NOT CONFIRM.**
#:
#: Spec §7 cut the trend computation out of WO-1.3a explicitly: no 50/200-day structure, no
#: higher-low detection on the acute statistic, and nothing wired that could answer the
#: question. ``official_state_for_dial`` nonetheless takes ``trend_confirmed`` as a
#: parameter, so this pass has to supply something, and the only honest thing to supply is
#: the answer that CLAIMS LESS: ``False`` means "this pass asserts no confirmed trend",
#: which is conservative in the one direction that matters — spec §3's rule 5 needs
#: ``trend_confirmed`` to reach RECOVERY, so a hardcoded ``False`` can only ever KEEP a
#: dial in ALARM longer. It cannot manufacture a recovery.
#:
#: It is a named constant and not a literal at the call site so that reading
#: ``trend_confirmed=TREND_NOT_COMPUTED`` says what is true. When a real trend indicator is
#: wired (WO-1.3b or later), the change is to compute a value here and DELETE this
#: constant — a grep for its name finds every place that has to be revisited, which a
#: literal ``False`` would not.
TREND_NOT_COMPUTED = False


class PassWiringBroken(RuntimeError):
    """This module's own wiring is inconsistent — a defect here, not a data problem.

    Raised for the two things that cannot be true unless this file is wrong: a dial id
    :data:`_PER_DIAL` does not cover, and a reading whose score is not its dial's score
    type. Neither is "we have no data", so neither becomes an UNKNOWN row: swallowing a
    broken pass into a stated absence would publish "we do not know" when the truth is
    "our code is broken" (``engine/evaluate.py``'s own sentence about its executor).
    """


#: ``dial_id -> (the DialSet field carrying its reading, its acute statistic)``.
#:
#: WRITTEN OUT rather than derived from ``DIAL_IDS``/``DIAL_FIELDS`` by index: the pairing
#: of a dial with ITS acute function is the thing that must not be got wrong, and zipping
#: two tuples together would make it a consequence of their order rather than a statement.
#: The equity table and the monetary table are not interchangeable — spec §2 — and the two
#: dials' polarities fail in opposite directions (PID §3.1).
_PER_DIAL = {
    EQUITY_DIAL_ID: ("equity", equity_crash_acute),
    MONETARY_DIAL_ID: ("monetary", monetary_debasement_acute),
}

# ASSERTED AT IMPORT, by set equality, in this module's house style (see
# `statistics.COMBINES_WITH_AN_EXECUTOR_BRANCH`): a dial added to the product without a
# row here stops this module importing rather than being quietly skipped by a pass that
# iterates over the table it forgot to extend.
if set(_PER_DIAL) != set(DIAL_IDS):
    raise PassWiringBroken(
        f"_PER_DIAL covers {sorted(_PER_DIAL)} and the product declares {sorted(DIAL_IDS)}. "
        "A dial with no row here would be silently absent from every pass."
    )


def _raw_reader(raw_store_path: str) -> SqliteStore:
    """THE ONLY PLACE THIS PROCESS OPENS THE COLLECTOR'S RAW STORE. Read-only, always.

    ``read_only=True`` is written here once, as a keyword this module supplies and not one
    it accepts, so there is no call in this file — and no argument to any function in it —
    that can open the raw store for writing. The handle it returns raises
    :exc:`sqlite3.OperationalError` on any write, which is SQLite's refusal and not a flag
    this code checks; see ``ingestion/store.py``'s reader door for the same sentence.

    It also creates nothing: a path that does not exist is an error here rather than a new
    empty database that would read as "no indicators are live".
    """
    return SqliteStore(raw_store_path, read_only=True)


def _contributions_of(dial_id: str, reading: object) -> tuple:
    """ONE dial's contributions, off a reading that :func:`present_dial` has already shown.

    The magnitude comes through the presentation tier (``present_dial`` ->
    ``Shown.magnitude`` -> ``quantity_for``), which is the GUI's route and the one that
    answers absence with a type that has no number in it. The CONTRIBUTIONS do not travel
    that way — ``Shown`` carries a magnitude and nothing else, by design — so they are read
    off the reading's score directly, and the score's exact type is checked against
    :data:`~crash_detector.engine.evaluate.DIAL_SCORE_TYPES` for this dial before anything
    is read from it. ``present_dial`` having answered ``Shown`` already establishes that
    the reading carries a value and that the magnitude's provenance is this dial's; this
    check is the same claim made again at the one field that bypasses it.
    """
    score = reading.value
    expected = DIAL_SCORE_TYPES[dial_id]
    if type(score) is not expected:
        raise PassWiringBroken(
            f"the {dial_id!r} reading carries a {type(score).__name__} and this dial's "
            f"score type is {expected.__name__}. A dial's contributions are the inputs to "
            "its own masters and its own count; taking them off another dial's score "
            "would be the blend CD-AC-002 exists to refuse."
        )
    return score.contributions


def _unknown_row(dial_id: str, as_of: datetime) -> MachineStateRow:
    """The row for a dial that produced NO READING: UNKNOWN, no statistics, counter 0.

    **NOT ROUTED THROUGH** :func:`~evaluator.resolve.official_state_for_dial`, and the
    reason is a number that does not exist. That function takes ``breadth`` as a ``float``
    and its door establishes finiteness; a dial with no reading has no magnitude, so there
    is no breadth to pass, and passing ``0.0`` to satisfy a parameter that spec §3's rule 1
    never reads would be writing a CALM number into the one case that must not carry one
    (PID §3.2, CD-AC-001). ``None`` and ``nan`` are both refused at that door, correctly.

    What is duplicated is therefore one branch and not a judgement: rule 1 is
    unconditional, overrides every other rule and consults no history, so the row that
    function would have returned is exactly this one. ``candidate_state`` is UNKNOWN too —
    this reading's own numbers called for UNKNOWN, which is what that column records.

    ``as_of`` is the pass's own instant and not a reading's: there are no inputs to date
    this row by, which is the whole content of the row.
    """
    return MachineStateRow(
        dial_id=dial_id,
        as_of=as_of,
        machine_state=State.UNKNOWN,
        candidate_state=State.UNKNOWN,
        persistence_counter=0,
    )


def one_pass_for_dial(
    dial_id: str,
    *,
    raw_store_path: str,
    history: MachineStateHistoryStore,
    now_utc: datetime,
) -> MachineStateRow:
    """ONE DIAL, ONE PASS: read the raw store, score it, resolve the state, append one row.

    Returns the row that was appended, so a caller does not have to read back what it just
    wrote to know what the dial now says.

    ``now_utc`` is a PARAMETER and not a clock read, exactly as
    :func:`crash_detector.engine.evaluate.evaluate`'s is, so that a historical pass can be
    replayed: it decides which readings are fresh enough to be usable. The only clock this
    function reads is ``written_utc`` at the append — when the row was WRITTEN, which is a
    fact about this process and not about the reading, and which the store keeps separately
    for that reason.

    The five steps are spec §9 item 2's, in order:

    1. the raw store, through :func:`_raw_reader` and therefore read-only;
    2. ``breadth`` from the existing evaluation's magnitude (the GUI's route, unchanged),
       ``acute`` and ``count`` from this dial's own statistics over its contributions;
    3. this dial's recent rows, :data:`~evaluator.resolve.BREADTH_LOOKBACK_ROWS` of them,
       which is the window rule 4's lookback needs and the most any rule reads;
    4. :func:`~evaluator.resolve.official_state_for_dial`, with
       :data:`TREND_NOT_COMPUTED`;
    5. the append.
    """
    if dial_id not in _PER_DIAL:
        raise PassWiringBroken(
            f"{dial_id!r} is not a dial this pass knows. The dials are {sorted(_PER_DIAL)}."
        )
    dial_field, acute_for_this_dial = _PER_DIAL[dial_id]

    # 1. THE RAW STORE. Opened read-only, read, and closed before anything is computed:
    # the handle is held for exactly as long as the observations take to fetch.
    wiring = build_wiring()
    with _raw_reader(raw_store_path) as raw:
        observations = observations_from_store(raw, wiring, now_utc)

    # 2. THE THREE STATISTICS. `evaluate` computes the pair; this dial's reading is taken
    # and the other dial's is dropped, unexamined (module docstring item 2).
    reading = getattr(evaluate(observations, wiring.snapshot, now_utc), dial_field)
    shown = present_dial(dial_id, reading)
    if type(shown) is NotShown:
        # NO READING FOR THIS DIAL. `present_dial` answered absence with a type that has no
        # number in it, and the row says the same thing.
        row = _unknown_row(dial_id, now_utc)
        history.append(row, written_utc=datetime.now(timezone.utc))
        return row

    breadth = shown.magnitude.quantity_for(dial_id)
    contributions = _contributions_of(dial_id, reading)
    acute = acute_for_this_dial(contributions)
    count = count_for_one_dial(contributions)

    # 3. THE DIAL'S MEMORY. Most recent first, and `official_state_for_dial` refuses a
    # history carrying another dial's row — which is why the dial id is passed to `recent`
    # and not assumed from the handle.
    history_rows = history.recent(dial_id, limit=BREADTH_LOOKBACK_ROWS)

    # 4. THE STATE. `as_of` is the READING's instant — the oldest as_of among the inputs
    # this dial actually used — and not `now_utc`: a pass that runs at noon over a feed
    # that last published at 09:00 read its inputs as of 09:00, and the row says so.
    row = official_state_for_dial(
        history=history_rows,
        as_of=reading.as_of_utc,
        breadth=breadth,
        acute=acute,
        count=count,
        trend_confirmed=TREND_NOT_COMPUTED,
    )

    # 5. THE APPEND. The real clock, read once, here. An IntegrityError from the schema is
    # not caught: a row the table refuses is a defect in the resolver, not an outcome.
    history.append(row, written_utc=datetime.now(timezone.utc))
    return row


def one_pass_for_both_dials(
    *,
    raw_store_path: str,
    history: MachineStateHistoryStore,
    now_utc: datetime,
) -> dict:
    """``dial_id -> the row appended`` for BOTH dials, in :data:`DIAL_IDS` order.

    A loop over :data:`DIAL_IDS` and nothing else: the two dials are evaluated and resolved
    independently, no value crosses between the iterations, and the returned dict is two
    rows side by side rather than anything that combines them.

    **THIS IS NOT A SCHEDULER AND NOT AN ENTRY POINT.** There is no ``__main__`` in this
    module, no cadence, no container and no compose entry — spec §9 holds the deployment
    for its own round. One call is one pass; what calls it, and how often, is not decided
    here.
    """
    return {
        dial_id: one_pass_for_dial(
            dial_id,
            raw_store_path=raw_store_path,
            history=history,
            now_utc=now_utc,
        )
        for dial_id in DIAL_IDS
    }
