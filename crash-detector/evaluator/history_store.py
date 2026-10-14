"""THE STATE MACHINE'S OWN HISTORY: one row per dial per EVALUATION RUN, append-only.

WO-1.3a round 4, built to ``governance/WO-1.3a-engine-spec.md`` §7 (the design), §8
(the Product Owner's sign-off on the round-3 investigation) and §9 item 1 (this round's
scope: the store, and only the store).

====================================================================================
WHY THIS IS A NEW STORE AND NOT A FOURTH TABLE IN ``ingestion/store.py``
====================================================================================

Settled by investigation and signed off in spec §8.1; the reasoning is not re-derived
here, only named, so a reader of this module knows what was decided:

* NOT a fourth table in :class:`ingestion.store.SqliteStore`. That file is the
  collector's — ``raw_*``, one row per fetch attempt and one per admitted source period,
  written by a container with outbound internet. A computed conclusion is a different
  kind of fact with a different writer, and an evaluator holding a WRITE handle on the
  raw store would be able to append raw rows it has no business appending. Its own file
  is what makes that unrepresentable rather than merely unintended.
* NOT a reuse of ``db/migrations/0004_dial_history.sql``. ``dial.history.state`` is the
  EXISTING ``Reading`` sum type — ``VALUE | DEGRADED | UNKNOWN``, how well the dial could
  be computed. :class:`~crash_detector.engine.statistics.State` is
  ``CALM | WATCH | ALARM | RECOVERY | UNKNOWN``, what the dial SAYS. Two vocabularies,
  one of them sharing the member name ``UNKNOWN``, which is exactly why they may not
  share a column. The table here is therefore named ``machine_state_history`` and its
  column ``machine_state``: neither name collides with ``dial.history`` or with
  ``state``, so a stored row cannot be read a year later against the wrong vocabulary.
  If the Postgres side ever needs this series it is a future migration (0008+), out of
  this work order's scope.
* SQLite, for the same reason ``ingestion/store.py`` is SQLite: the Postgres ``cd-store``
  is written-not-deployed (STATUS §4) and this seat has no authority to stand it up.

====================================================================================
WHAT A ROW CARRIES, AND WHY THE NUMBERS ARE STORED AND NOT ONLY THE STATE NAME
====================================================================================

Spec §7: "enough of the raw breadth/acute/count to re-derive persistence checks without
re-running the whole engine". The state machine reads its own history — persistence
counting over the current evaluation plus the 2 preceding rows, RECOVERY's per-master
exit check, the 20-row breadth lookback — so a row holding only ``machine_state`` would
force a re-computation from raw data that may since have been revised, and the re-run
would not be the reading that was published. Hence ``breadth``, ``acute`` (with the
master it came from, and every master's own score), and the ``count`` statistic as both
its number and the indicator ids that produced it. That is what "a reading is
explainable a year later" already means elsewhere in this codebase (BLUEPRINT §7).

APPEND-ONLY, mechanically, not by convention: ``BEFORE UPDATE`` / ``BEFORE DELETE``
triggers that ``RAISE(ABORT, ...)``, the same instrument ``raw_observation`` and
``raw_reading`` carry. A run's conclusion is a historical fact once written; a bug fix
produces a new, later row with the right number, exactly as every observation in this
product does.

====================================================================================
CD-RT-001, HELD IN THE SCHEMA
====================================================================================

An UNKNOWN row carries NO breadth, NO acute and NO count — enforced by
:data:`_STATE_FIELDS_COHERENT`, a CHECK constraint, so a row claiming UNKNOWN while
carrying numbers is unrepresentable rather than merely avoided by the writer. The shape
is ``dial.history``'s own ``dial_history_state_fields_coherent`` (migration 0004), one
vocabulary across: ``UNKNOWN`` requires every statistic NULL, and a resolvable state
requires every statistic present.

The second half of that constraint is not padding. Spec §2 propagates absence upward —
if any master is :class:`~crash_detector.engine.statistics.MasterUnknown` the dial's
acute statistic is :class:`~crash_detector.engine.statistics.AcuteUnknown` and spec §3
rule 1 makes the state UNKNOWN — so a CALM row with a missing number is not a partial
reading, it is a row that disagrees with the engine that wrote it.

====================================================================================
``candidate_state``, AND WHY THE OFFICIAL STATE ALONE MAKES THE CLOCK UNREADABLE
====================================================================================

Added by WO-1.3a's next round (the persistence resolver,
:func:`evaluator.resolve.official_state_for_dial`) and found to be NECESSARY by it rather
than wanted: spec §3's ``persistence = 3`` means the official state does NOT change until
the SAME candidate has been computed three readings running, so during a pending
transition ``machine_state`` is deliberately the OLD state and ``persistence_counter``
counts readings toward a new one. **A counter whose row does not say WHAT it is counting
cannot be continued by the next reading** — "does this reading's candidate match the one
accumulating?" is unanswerable from a state name that is, by construction, not it.

Re-deriving a preceding row's candidate from its stored statistics was considered first
(spec §7 asks for "enough of the raw breadth/acute/count to re-derive persistence checks")
and does not close: rule 5 needs ``trend_confirmed``, which is a caller-supplied input
this round does not compute and no column holds, so a re-derived candidate could not tell
``RECOVERY`` from ``CALM`` — the one distinction a recovery transition turns on. Recording
the candidate the engine actually computed is both smaller and honest, and it makes the
pending transition legible in the history instead of inferred from it.

``acute_rising`` is NULL on an UNKNOWN row for the same reason and not as a tidy-up: it
is a comparison BETWEEN acute readings, and the absence of an acute reading cannot be
rising. A ``0`` there would be a claim this evaluation did not make.

====================================================================================
HOW AN EXISTING FILE MOVES FORWARD
====================================================================================

Same habit as ``ingestion/store.py``, and no more than that habit: :data:`_SCHEMA` is
``CREATE TABLE IF NOT EXISTS`` throughout and is executed on every write-mode open, so a
second open of a live file is a no-op and never re-creates or re-shapes what is there. A
read-only handle creates nothing and migrates nothing — the GUI's door, once it reads
this series (spec §8.2). The table gained its second shape with
``candidate_state`` (above), and with it the ``ingestion.store``-style
:func:`_bring_forward` this docstring promised: additive, idempotent, guarded by ``PRAGMA
table_info`` and not by a migration ledger. There is no live file of this table anywhere
yet, so that step carries nothing forward today — it exists so that the next column does
not have to be the first one to need it.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Union

from crash_detector.dials.dialset import DIAL_IDS
from crash_detector.engine.statistics import State
from crash_detector.time_utc import format_utc, parse_utc

__all__ = ["MachineStateRow", "MachineStateHistoryStore", "TABLE"]

#: The table's name, in one place. NOT ``dial_history`` and NOT ``state``: see the module
#: docstring on the two vocabularies that must not share a column.
TABLE = "machine_state_history"

#: A vocabulary member admissible in DDL by string interpolation. The regex differs from
#: :func:`ingestion.store._as_sql_literals`'s ``[a-z][a-z0-9_]*`` in ONE way — one
#: optional dotted namespace segment — because every
#: :class:`~crash_detector.engine.statistics.State` value is namespaced (``state.calm``,
#: deliberately, so an engine state and a PID §4 detail level can never be confused).
#: Everything else the guard refuses, it still refuses.
_ADMISSIBLE_IN_DDL = re.compile(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)?")


def _as_sql_literals(values: tuple[str, ...]) -> str:
    """``'a', 'b'`` — the vocabulary as SQL literals, refusing anything that is not a word.

    :func:`ingestion.store._as_sql_literals`'s technique, reused rather than reinvented
    (spec §9 item 1 names it): a CHECK constraint cannot be parameterised, so the
    vocabulary reaches the DDL by string interpolation, and this guard is what makes that
    readable as safe rather than as a habit. Every value is a Python constant today, and a
    later one carrying a quote is refused here instead of silently producing a constraint
    that means something else.
    """
    for value in values:
        if not _ADMISSIBLE_IN_DDL.fullmatch(value):
            raise ValueError(f"not an admissible vocabulary member for DDL: {value!r}")
    return ", ".join(f"'{value}'" for value in values)


#: Built by walking :class:`~crash_detector.engine.statistics.State` so the SQL vocabulary
#: and the Python one cannot drift: a sixth member added to the enum reaches this CHECK
#: with no edit here, and a member removed from it stops being admissible in the table.
#: The enum is closed by the language, which is what makes that walk a complete list.
_MACHINE_STATE_VALUES = tuple(member.value for member in State)

#: ``machine_state`` is NOT NULL: there is no third thing a row may say. A dial that could
#: not be resolved says :attr:`~crash_detector.engine.statistics.State.UNKNOWN`, which is a
#: STATED absence and the whole of CD-AC-001 — not a missing value.
_MACHINE_STATE_COLUMN = (
    f"machine_state TEXT NOT NULL CHECK (machine_state IN ({_as_sql_literals(_MACHINE_STATE_VALUES)}))"
)

#: ``candidate_state`` — WHAT THIS READING'S OWN NUMBERS CALLED FOR, which is deliberately
#: NOT the same question ``machine_state`` answers. See the module docstring's section on
#: why the persistence clock is unreadable without it.
#:
#: NULLABLE, and the ``NULL`` is a THIRD STATE rather than a tidy-up (``raw_reading.vintage``
#: is the precedent, WO-1.14): it means THIS ROW PRE-DATES CANDIDATE RECORDING, which is
#: neither a recorded candidate nor an absent one. SQLite cannot ``ADD COLUMN ... NOT NULL``
#: without a DEFAULT, and a default here would be a state nobody computed, so the column is
#: nullable in BOTH the fresh DDL and the brought-forward one — the same DDL either way,
#: :func:`_bring_forward`'s own rule. :func:`evaluator.resolve.official_state_for_dial`
#: treats a ``NULL`` candidate on a preceding row as "cannot confirm a streak" and never as
#: "the streak held", so an unrecorded candidate can only ever DELAY a transition.
_CANDIDATE_STATE_COLUMN = (
    f"candidate_state TEXT CHECK (candidate_state IS NULL"
    f" OR candidate_state IN ({_as_sql_literals(_MACHINE_STATE_VALUES)}))"
)

#: ``crash_detector.dials.dialset.DIAL_IDS``. Two. A third is a PID amendment — the same
#: constraint ``dial.history`` carries as ``dial_history_dial_admitted``, read from the
#: declaring module rather than retyped.
_DIAL_ID_COLUMN = f"dial_id TEXT NOT NULL CHECK (dial_id IN ({_as_sql_literals(DIAL_IDS)}))"

#: The statistics an UNKNOWN row may not carry and a resolvable row may not omit.
_STATISTIC_COLUMNS = (
    "breadth",
    "acute",
    "acute_from_master_id",
    "master_scores",
    "indicator_count",
    "count_at_or_beyond",
    "acute_rising",
)

#: CD-RT-001, as ``dial.history``'s ``dial_history_state_fields_coherent`` shape. The
#: UNKNOWN branch is keyed off :attr:`~crash_detector.engine.statistics.State.UNKNOWN`'s
#: own value, never a retyped literal. There is no ``ELSE false`` arm because
#: :data:`_MACHINE_STATE_COLUMN` has already closed the vocabulary: the ``ELSE`` here IS
#: the four resolvable states, and an unlisted sixth state cannot reach this constraint.
_STATE_FIELDS_COHERENT = f"""CONSTRAINT {TABLE}_state_fields_coherent CHECK (
        CASE machine_state
            WHEN '{State.UNKNOWN.value}'
                THEN {' AND '.join(f'{column} IS NULL' for column in _STATISTIC_COLUMNS)}
            ELSE {' AND '.join(f'{column} IS NOT NULL' for column in _STATISTIC_COLUMNS)}
        END
    )"""

def _finite(column: str) -> str:
    """``column`` holds a real number or nothing — the SQLite spelling of ``dial.history``'s
    ``dial_history_score_is_finite``.

    SQLite stores a bound ``float('nan')`` AS NULL — verified against a real SQLite, not
    reasoned about — so NaN arrives as an absence and is refused by
    :data:`_STATE_FIELDS_COHERENT` on any resolvable row. ``inf`` is NOT converted: it
    survives as a REAL, sorts above every threshold this product has, and would render as
    a dial reading. That is what this guard is for.
    """
    return f"CHECK ({column} IS NULL OR ({column} > -9e307 AND {column} < 9e307))"


_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    {TABLE}_id INTEGER PRIMARY KEY AUTOINCREMENT,
    {_DIAL_ID_COLUMN},
    as_of TEXT NOT NULL,
    {_MACHINE_STATE_COLUMN},
    {_CANDIDATE_STATE_COLUMN},
    persistence_counter INTEGER NOT NULL CHECK (persistence_counter >= 0),
    acute_rising INTEGER CHECK (acute_rising IS NULL OR acute_rising IN (0, 1)),
    breadth REAL {_finite('breadth')},
    acute REAL {_finite('acute')},
    acute_from_master_id TEXT,
    master_scores TEXT CHECK (master_scores IS NULL OR json_type(master_scores) = 'object'),
    indicator_count INTEGER CHECK (indicator_count IS NULL OR indicator_count >= 0),
    count_at_or_beyond TEXT CHECK (count_at_or_beyond IS NULL OR json_type(count_at_or_beyond) = 'array'),
    written_utc TEXT NOT NULL,
    {_STATE_FIELDS_COHERENT}
);
CREATE INDEX IF NOT EXISTS {TABLE}_dial_recent_idx
    ON {TABLE} (dial_id, {TABLE}_id DESC);
CREATE TRIGGER IF NOT EXISTS {TABLE}_no_update BEFORE UPDATE ON {TABLE}
    BEGIN SELECT RAISE(ABORT, '{TABLE} is append-only'); END;
CREATE TRIGGER IF NOT EXISTS {TABLE}_no_delete BEFORE DELETE ON {TABLE}
    BEGIN SELECT RAISE(ABORT, '{TABLE} is append-only'); END;
"""

def _bring_forward(db: sqlite3.Connection) -> None:
    """Add the columns an older file is missing. Additive, idempotent, no table rewrite.

    ``ingestion.store._bring_forward``'s habit, and no more than that habit: ``CREATE TABLE
    IF NOT EXISTS`` is a no-op on a table that already exists, so a file created before a
    column was declared needs the ``ALTER TABLE`` as well. Each step is guarded by what the
    file ACTUALLY HAS — ``PRAGMA table_info`` — rather than by a recorded version number,
    because there is no migration ledger in this store to be trusted.

    ``ADD COLUMN`` rewrites SQLite's schema record only: no row is touched, no table is
    copied, and the append-only triggers are not dropped and re-created. Existing rows take
    ``NULL``, which :data:`_CANDIDATE_STATE_COLUMN` documents as a third state and which the
    resolver reads as "cannot confirm", never as "confirmed".

    NO FILE OF THIS TABLE EXISTS ANYWHERE YET — nothing in spec §9 is deployed — so this
    function has no live file to carry forward today. It is written anyway, and tested
    against a file created without the column, because the alternative is a store whose
    "one shape" assumption is true only until the first evaluator runs.
    """
    columns = {row[1] for row in db.execute(f"PRAGMA table_info({TABLE})")}
    if "candidate_state" not in columns:  # WO-1.3a, the persistence resolver
        db.execute(f"ALTER TABLE {TABLE} ADD COLUMN {_CANDIDATE_STATE_COLUMN}")


_COLUMNS = (
    "dial_id",
    "as_of",
    "machine_state",
    "candidate_state",
    "persistence_counter",
    "acute_rising",
    "breadth",
    "acute",
    "acute_from_master_id",
    "master_scores",
    "indicator_count",
    "count_at_or_beyond",
)


@dataclass(frozen=True)
class MachineStateRow:
    """ONE EVALUATION'S CONCLUSION FOR ONE DIAL, as it was written and as it is read back.

    ``machine_state`` is a :class:`~crash_detector.engine.statistics.State` member on both
    sides of the file: :meth:`MachineStateHistoryStore.append` stores its value and
    :meth:`MachineStateHistoryStore.recent` resolves the stored text back through the enum,
    so a text no longer in the vocabulary fails loudly at the read rather than travelling
    on as a string nobody checks.

    Every statistic is ``None`` exactly when the state is UNKNOWN. That is the schema's
    guarantee (see the module docstring on CD-RT-001), not this type's: a row read back
    with the coherence broken would mean the CHECK had been removed from the file.
    """

    dial_id: str
    as_of: datetime
    machine_state: State
    persistence_counter: int
    #: WHAT THIS READING'S OWN NUMBERS CALLED FOR, before persistence was applied —
    #: :func:`crash_detector.engine.statistics.candidate_state_for_one_reading`'s answer.
    #: It is EQUAL to ``machine_state`` on a settled row and DIFFERENT on a row whose
    #: transition is still accumulating, which is the whole reason it is stored: see the
    #: module docstring. ``None`` only on a row written before the column existed.
    candidate_state: Union[State, None] = None
    acute_rising: Union[bool, None] = None
    breadth: Union[float, None] = None
    acute: Union[float, None] = None
    acute_from_master_id: Union[str, None] = None
    #: ``{master_id: score}`` for every master this evaluation scored — what spec §3's
    #: rules 2, 4 and 5 read PER MASTER, and what RECOVERY's exit check reads from the
    #: preceding rows rather than off the maximum.
    master_scores: Union[dict, None] = None
    #: The ``count`` statistic's number, derived by
    #: :class:`~crash_detector.engine.statistics.Count` from the ids below and stored
    #: beside them because the table is read by SQL that cannot re-derive it.
    indicator_count: Union[int, None] = None
    #: The indicator ids at or beyond ``COUNT_THRESHOLD`` — the explanation of the number.
    count_at_or_beyond: Union[tuple, None] = None


class MachineStateHistoryStore:
    """One SQLite file holding :data:`TABLE`. Open, append one row, read a dial's recent rows.

    THAT IS THE WHOLE OF THIS ROUND (spec §9). There is no six-rule precedence function
    here and no evaluator pass: the precedence belongs beside ``State``/``MasterCombine``
    in :mod:`crash_detector.engine.statistics` (spec §9 item 1) and the pass that reads the
    raw store, computes and appends is item 2. This class knows nothing about how a state
    was decided — it stores what it is given and refuses what the schema says cannot be.
    """

    __slots__ = ("_db",)

    def __init__(self, path: str, *, read_only: bool = False) -> None:
        if read_only:
            # The reader's door: the file must already exist, nothing is created, no write
            # of any kind can be issued through this handle, and no schema is brought
            # forward by a handle that only reads (``ingestion.store``'s GUI door, WO-1.4).
            self._db = sqlite3.connect(f"file:{path}?mode=ro", uri=True, isolation_level=None)
            return
        self._db = sqlite3.connect(path, isolation_level=None)  # autocommit: durable per row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.executescript(_SCHEMA)
        _bring_forward(self._db)

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> "MachineStateHistoryStore":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def append(self, row: MachineStateRow, *, written_utc: datetime) -> None:
        """Write one evaluation's conclusion. No UPDATE path exists, here or in the file.

        ``written_utc`` is when the row was written, separate from ``row.as_of``, which is
        the instant the evaluation read its inputs as of. Both are kept because a row
        written late is not a reading that happened late.

        Raises :class:`sqlite3.IntegrityError` for a row the schema refuses — an UNKNOWN
        carrying a number, a dial id nobody declared, a non-finite statistic. The refusal
        is the point and it is not caught here.
        """
        self._db.execute(
            f"INSERT INTO {TABLE} ({', '.join(_COLUMNS)}, written_utc)"
            f" VALUES ({', '.join('?' * (len(_COLUMNS) + 1))})",
            (
                row.dial_id,
                format_utc(row.as_of),
                row.machine_state.value,
                None if row.candidate_state is None else row.candidate_state.value,
                row.persistence_counter,
                None if row.acute_rising is None else int(row.acute_rising),
                row.breadth,
                row.acute,
                row.acute_from_master_id,
                None if row.master_scores is None else json.dumps(dict(row.master_scores), sort_keys=True),
                row.indicator_count,
                None if row.count_at_or_beyond is None else json.dumps(list(row.count_at_or_beyond)),
                format_utc(written_utc),
            ),
        )

    def recent(self, dial_id: str, *, limit: int) -> tuple:
        """This dial's ``limit`` most recent rows, MOST RECENT FIRST.

        Ordered by the row id — the order the evaluations were appended in — and not by
        ``as_of``: the id is assigned by the file and cannot be reordered by a clock that
        moved, which is what the persistence count and the breadth lookback (spec §7) are
        counting over. ``limit`` is the caller's window: 3 rows for a persistence check,
        20 for the breadth lookback, and asking for them is the caller's business.
        """
        rows = self._db.execute(
            f"SELECT {', '.join(_COLUMNS)} FROM {TABLE} WHERE dial_id = ?"
            f" ORDER BY {TABLE}_id DESC LIMIT ?",
            (dial_id, limit),
        ).fetchall()
        return tuple(_as_row(record) for record in rows)

    def state_since(self, dial_id: str):
        """The ``as_of`` OF THE ROW THAT STARTED this dial's current ``machine_state`` streak.

        DECISION-RULE.md §7's ``state_since``, and it is a QUERY rather than a column
        because the answer is a property of the whole series and the writer does not know
        it: :func:`evaluator.resolve.official_state_for_dial` sees
        :data:`~evaluator.resolve.BREADTH_LOOKBACK_ROWS` rows and a dial that has been CALM
        for six months at a five-minute cadence has fifty thousand. Deriving it from
        :meth:`recent` would therefore not be conservative-but-imprecise, it would be WRONG
        in the one direction that matters — a 20-row window answers "CALM for 100 minutes"
        about a state that has held since spring — so the window is not asked. No column was
        added either: a stored ``state_since`` would be a denormalised copy of what these
        two indexed reads already answer exactly, and the first row written with it stale
        would be a historical fact that is wrong forever (the table is append-only).

        The streak is run over ROW ID and not over ``as_of``, for :meth:`recent`'s reason:
        the id is the order the evaluations were appended in and cannot be reordered by a
        feed that republished an older vintage. What is returned is accordingly the as_of of
        the row that FIRST SAID SO and not ``MIN(as_of)`` across the streak — "the state has
        held since the reading that first reached it", which is the claim §7's consumer
        reads, and which stays true even where two readings' as_ofs are out of order.

        ``None`` only when this dial has NO rows at all. That is not a state that began at
        an unknown time, it is a dial with no history, and the caller holding the row it is
        about to append knows the answer for that case and this handle does not.

        A read, through both doors: it creates nothing, writes nothing and is available on a
        ``read_only=True`` handle.
        """
        latest = self._db.execute(
            f"SELECT machine_state FROM {TABLE} WHERE dial_id = ?"
            f" ORDER BY {TABLE}_id DESC LIMIT 1",
            (dial_id,),
        ).fetchone()
        if latest is None:
            return None
        # The newest row BELOW which this dial said something else. NULL (-> 0, and every
        # id is >= 1) means the whole of this dial's history is the one streak.
        broke_at = self._db.execute(
            f"SELECT MAX({TABLE}_id) FROM {TABLE}"
            f" WHERE dial_id = ? AND machine_state != ?",
            (dial_id, latest[0]),
        ).fetchone()[0]
        started = self._db.execute(
            f"SELECT as_of FROM {TABLE} WHERE dial_id = ? AND {TABLE}_id > ?"
            f" ORDER BY {TABLE}_id ASC LIMIT 1",
            (dial_id, broke_at or 0),
        ).fetchone()
        return parse_utc(started[0])


def _as_row(record: tuple) -> MachineStateRow:
    (dial_id, as_of, machine_state, candidate_state, persistence_counter, acute_rising,
     breadth, acute, acute_from_master_id, master_scores, indicator_count,
     count_at_or_beyond) = record
    return MachineStateRow(
        dial_id=dial_id,
        as_of=parse_utc(as_of),
        machine_state=State(machine_state),  # refuses a text the vocabulary no longer has
        candidate_state=None if candidate_state is None else State(candidate_state),
        persistence_counter=persistence_counter,
        acute_rising=None if acute_rising is None else bool(acute_rising),
        breadth=breadth,
        acute=acute,
        acute_from_master_id=acute_from_master_id,
        master_scores=None if master_scores is None else json.loads(master_scores),
        indicator_count=indicator_count,
        count_at_or_beyond=None if count_at_or_beyond is None else tuple(json.loads(count_at_or_beyond)),
    )
