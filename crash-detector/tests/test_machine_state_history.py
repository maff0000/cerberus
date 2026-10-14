"""The state machine's own history store (WO-1.3a round 4, spec §9 item 1).

Offline, no clock dependence: every instant is a constant and the file is pytest's
``tmp_path``, the same throwaway-file pattern ``ingestion/store.py``'s own tests use.

WHAT THESE TESTS ARE FOR. The round-3 investigation's CD-RT-001 finding was that an
UNKNOWN row must not be able to carry a number — and "the writer does not write one" is
not that guarantee. So the refusals below are provoked against a REAL SQLite and the real
:class:`sqlite3.IntegrityError` is caught: a test that only avoided constructing the bad
row would pass against a table with no CHECK constraint at all.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from crash_detector.engine.statistics import State
from evaluator.history_store import (TABLE, MachineStateHistoryStore, MachineStateRow,
                                     _as_sql_literals)

AS_OF = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)
WRITTEN = AS_OF + timedelta(seconds=2)
DIAL = "equity_crash"


def _resolved(**overrides) -> MachineStateRow:
    """A row for a dial that RESOLVED: a state, and every statistic present."""
    row = dict(
        dial_id=DIAL,
        as_of=AS_OF,
        machine_state=State.WATCH,
        persistence_counter=2,
        acute_rising=True,
        breadth=0.41,
        acute=0.67,
        acute_from_master_id="equity_volatility",
        master_scores={"equity_volatility": 0.67, "equity_credit": 0.2},
        indicator_count=3,
        count_at_or_beyond=("vix_spot", "hy_oas", "move_index"),
    )
    row.update(overrides)
    return MachineStateRow(**row)


def _unknown(**overrides) -> MachineStateRow:
    """A row for a dial that could NOT be resolved: a stated absence, carrying no number."""
    row = dict(
        dial_id=DIAL,
        as_of=AS_OF,
        machine_state=State.UNKNOWN,
        persistence_counter=0,
    )
    row.update(overrides)
    return MachineStateRow(**row)


@pytest.fixture()
def store(tmp_path):
    with MachineStateHistoryStore(str(tmp_path / "machine-state.sqlite")) as s:
        yield s


def _ddl(path) -> list:
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return db.execute("SELECT type, name, sql FROM sqlite_master ORDER BY name").fetchall()
    finally:
        db.close()


# --- one row, written and read back ------------------------------------------------------ #


def test_a_row_is_written_and_read_back_as_the_same_reading(store):
    store.append(_resolved(), written_utc=WRITTEN)

    (read_back,) = store.recent(DIAL, limit=3)
    assert read_back == _resolved(), "a stored conclusion came back as a different one"
    assert read_back.machine_state is State.WATCH  # the enum member, not the stored text
    assert read_back.as_of == AS_OF
    assert read_back.master_scores == {"equity_volatility": 0.67, "equity_credit": 0.2}
    assert read_back.count_at_or_beyond == ("vix_spot", "hy_oas", "move_index")


def test_an_unknown_row_is_written_and_read_back_carrying_no_numbers(store):
    store.append(_unknown(), written_utc=WRITTEN)

    (read_back,) = store.recent(DIAL, limit=3)
    assert read_back.machine_state is State.UNKNOWN
    for absent in ("breadth", "acute", "acute_from_master_id", "master_scores",
                   "indicator_count", "count_at_or_beyond", "acute_rising"):
        assert getattr(read_back, absent) is None, f"an UNKNOWN reading carried {absent}"


def test_recent_returns_this_dials_rows_most_recent_first_and_no_other_dials(store):
    for counter in (1, 2, 3):
        store.append(_resolved(persistence_counter=counter), written_utc=WRITTEN)
    store.append(_resolved(dial_id="monetary_debasement"), written_utc=WRITTEN)

    assert [row.persistence_counter for row in store.recent(DIAL, limit=2)] == [3, 2]
    assert all(row.dial_id == DIAL for row in store.recent(DIAL, limit=20))
    assert len(store.recent(DIAL, limit=20)) == 3, "another dial's row reached this series"


# --- CD-RT-001: the schema refuses it, not the writer ------------------------------------ #


def test_an_unknown_row_carrying_a_breadth_is_refused_by_the_check_not_by_the_writer(store):
    """The row is CONSTRUCTED and OFFERED; SQLite is what refuses it."""
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        store.append(_unknown(breadth=0.41), written_utc=WRITTEN)
    assert store.recent(DIAL, limit=3) == ()


@pytest.mark.parametrize(
    "carried",
    [
        {"breadth": 0.41},
        {"acute": 0.67},
        {"acute_from_master_id": "equity_volatility"},
        {"master_scores": {"equity_volatility": 0.67}},
        {"indicator_count": 3},
        {"count_at_or_beyond": ("vix_spot",)},
        {"acute_rising": False},  # a comparison between acute readings there were none of
    ],
)
def test_no_statistic_whatsoever_may_accompany_an_unknown_state(store, carried):
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        store.append(_unknown(**carried), written_utc=WRITTEN)


@pytest.mark.parametrize(
    "missing",
    ["breadth", "acute", "acute_from_master_id", "master_scores", "indicator_count",
     "count_at_or_beyond", "acute_rising"],
)
def test_a_resolvable_state_may_not_omit_a_statistic_either(store, missing):
    """Spec §2 propagates absence upward: a CALM row with a hole disagrees with the engine."""
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        store.append(_resolved(machine_state=State.CALM, **{missing: None}), written_utc=WRITTEN)


def test_a_non_finite_statistic_is_refused_and_a_nan_cannot_pass_as_a_number(store):
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        store.append(_resolved(acute=float("inf")), written_utc=WRITTEN)
    # SQLite stores a bound NaN AS NULL, so it arrives as an absence — and an absence on a
    # resolvable row is refused by the coherence constraint. Two constraints, one refusal.
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        store.append(_resolved(breadth=float("nan")), written_utc=WRITTEN)


def test_a_dial_nobody_declared_is_refused(store):
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        store.append(_resolved(dial_id="combined"), written_utc=WRITTEN)


def test_the_state_vocabulary_in_the_ddl_is_built_from_the_enum_not_retyped(store):
    ddl = store._db.execute(
        "SELECT sql FROM sqlite_master WHERE name = ?", (TABLE,)
    ).fetchone()[0]
    for member in State:
        assert f"'{member.value}'" in ddl
    assert ddl.count("'state.") == len(State) + 1, "a state the enum does not declare"
    # ... and a state the enum does declare still has to be spelled exactly:
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        store._db.execute(
            f"INSERT INTO {TABLE} (dial_id, as_of, machine_state, persistence_counter,"
            " written_utc) VALUES (?,?,?,?,?)", (DIAL, "t", "UNKNOWN", 0, "t"))


def test_a_vocabulary_member_that_is_not_a_word_is_refused_rather_than_interpolated():
    """The CHECK cannot be parameterised; the refusal is what stands in for the placeholder."""
    assert _as_sql_literals(("state.calm", "equity_crash")) == "'state.calm', 'equity_crash'"
    for bad in ("o'brien", "DROP", "two words", "", "1st", "state.", ".calm", "a.b.c"):
        with pytest.raises(ValueError, match="not an admissible vocabulary member"):
            _as_sql_literals((bad,))


# --- append-only, and what a second open does -------------------------------------------- #


def test_the_table_is_append_only(store):
    store.append(_resolved(), written_utc=WRITTEN)
    for sql in (f"UPDATE {TABLE} SET breadth = 0.01",
                f"UPDATE {TABLE} SET machine_state = 'state.calm'",
                f"DELETE FROM {TABLE}"):
        with pytest.raises(sqlite3.IntegrityError, match=f"{TABLE} is append-only"):
            store._db.execute(sql)
    assert store.recent(DIAL, limit=3) == (_resolved(),), "a refused write still landed"


def test_opening_the_file_again_keeps_the_schema_and_every_row(tmp_path):
    """Every evaluator pass opens the file; only the first may create anything in it."""
    path = tmp_path / "live.sqlite"
    with MachineStateHistoryStore(str(path)) as first:
        first.append(_resolved(), written_utc=WRITTEN)
    after_first = _ddl(path)

    for _ in range(3):
        MachineStateHistoryStore(str(path)).close()

    assert _ddl(path) == after_first, "a re-open re-shaped a file that was already written"
    with MachineStateHistoryStore(str(path)) as reopened:
        assert reopened.recent(DIAL, limit=3) == (_resolved(),)
        reopened.append(_resolved(persistence_counter=3), written_utc=WRITTEN)
        assert len(reopened.recent(DIAL, limit=20)) == 2
    # the triggers survived the re-opens as triggers, not merely as text in the DDL
    with MachineStateHistoryStore(str(path)) as last:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            last._db.execute(f"DELETE FROM {TABLE}")


def test_the_readers_door_creates_nothing_and_writes_nothing(tmp_path):
    path = tmp_path / "live.sqlite"
    with MachineStateHistoryStore(str(path)) as writer:
        writer.append(_resolved(), written_utc=WRITTEN)

    with MachineStateHistoryStore(str(path), read_only=True) as reader:
        assert reader.recent(DIAL, limit=3) == (_resolved(),)
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            reader.append(_resolved(), written_utc=WRITTEN)

    with pytest.raises(sqlite3.OperationalError):
        MachineStateHistoryStore(str(tmp_path / "absent.sqlite"), read_only=True)
