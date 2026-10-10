"""Applying migrations, against a recording double — A5, PBG-DATA-002/003.

:func:`crash_detector.store.migrate.apply` takes a PEP 249 connection as an argument, so
what it does with one can be observed exactly rather than inferred from a database's
after-state. That is the point of the injection: this file asserts the SEQUENCE — one
transaction per migration, the ledger row inside it, a rollback and a stop on failure —
which a live store cannot show you, and a live store separately asserts the RESULT, which
this cannot.

Neither is the other's evidence. Both are the Engineer's implementation testing and
neither is assurance (``PBG-SOD-001``, non-waivable).
"""

from __future__ import annotations

import pathlib

import pytest

from crash_detector.store.migrate import (
    LEDGER_TABLE,
    AppliedMigration,
    MigrationApplyFailed,
    apply,
    ensure_ledger,
    plan,
    read_ledger,
)
from crash_detector.store.migrations import MigrationAltered, load_migrations

ROOT = pathlib.Path(__file__).resolve().parents[1]
DELIVERED = ROOT / "db" / "migrations"


class RecordingCursor:
    """A PEP 249 cursor that records what it was asked to do.

    A test double, named as one, living under ``tests/``. It executes nothing.
    """

    def __init__(self, connection: "RecordingConnection") -> None:
        self._connection = connection

    def __enter__(self) -> "RecordingCursor":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def execute(self, sql: str, parameters: object = None) -> None:
        if self._connection.fail_on and self._connection.fail_on in sql:
            self._connection.journal.append(("execute-raised", sql[:60]))
            raise RuntimeError("the double was configured to fail here")
        self._connection.journal.append(("execute", sql, parameters))

    def fetchall(self) -> list[tuple[int, str]]:
        return list(self._connection.ledger_rows)


class RecordingConnection:
    """A PEP 249 connection that records commits and rollbacks."""

    def __init__(
        self,
        *,
        ledger_rows: list[tuple[int, str]] | None = None,
        fail_on: str | None = None,
    ) -> None:
        self.ledger_rows = ledger_rows or []
        self.fail_on = fail_on
        self.journal: list[tuple] = []

    def cursor(self) -> RecordingCursor:
        return RecordingCursor(self)

    def commit(self) -> None:
        self.journal.append(("commit",))

    def rollback(self) -> None:
        self.journal.append(("rollback",))

    # -- readers used by the assertions ------------------------------------------------- #

    @property
    def executed(self) -> list[str]:
        return [entry[1] for entry in self.journal if entry[0] == "execute"]

    @property
    def shape(self) -> list[str]:
        return [entry[0] for entry in self.journal]


@pytest.fixture()
def migrations():
    return load_migrations(DELIVERED)


# --- THE LEDGER ------------------------------------------------------------------------- #

def test_the_ledger_is_created_by_the_runner_and_not_by_a_migration(migrations):
    """It must exist before migration 1 can record itself, so it cannot be a migration."""
    connection = RecordingConnection()
    ensure_ledger(connection)
    assert any("CREATE TABLE IF NOT EXISTS public.schema_migration" in sql
               for sql in connection.executed)
    for migration in migrations:
        # In the STATEMENTS. Migration 1's comments explain where the ledger lives and
        # why; a check that failed on the explanation of a rule is a check nobody can
        # document around.
        statements = "\n".join(
            line
            for line in migration.sql.splitlines()
            if not line.strip().startswith("--")
        )
        assert "schema_migration" not in statements, migration.filename


def test_the_ledger_lives_outside_the_six_application_schemas():
    """BLUEPRINT §4 says six schemas, and it stays literally true of this store."""
    assert LEDGER_TABLE == "public.schema_migration"
    for schema in ("raw", "witness", "dial", "publication", "private", "alert"):
        assert not LEDGER_TABLE.startswith(f"{schema}.")


def test_the_ledger_read_returns_version_to_checksum():
    connection = RecordingConnection(ledger_rows=[(1, "a" * 64), (2, "b" * 64)])
    assert read_ledger(connection) == {1: "a" * 64, 2: "b" * 64}


def test_the_ledger_ddl_constrains_the_checksum_to_a_sha256():
    """A ledger that accepts any string records a checksum nobody can compare."""
    from crash_detector.store.migrate import LEDGER_DDL

    assert "checksum_sha256 ~ '^[0-9a-f]{64}$'" in LEDGER_DDL
    assert "timestamptz" in LEDGER_DDL


# --- PLANNING IS A REAL CHECK, NOT A PREVIEW ---------------------------------------------- #

def test_plan_reports_every_migration_against_an_empty_store(migrations):
    connection = RecordingConnection()
    assert [m.version for m in plan(connection, migrations)] == [1, 2, 3, 4, 5, 6, 7]


def test_plan_writes_nothing_but_the_ledger_ddl(migrations):
    connection = RecordingConnection()
    plan(connection, migrations)
    inserts = [sql for sql in connection.executed if sql.strip().upper().startswith("INSERT")]
    assert inserts == []


def test_plan_refuses_an_altered_history_before_anything_is_written(migrations):
    """So "the plan succeeded and the apply then refused" is not a state this can produce."""
    connection = RecordingConnection(ledger_rows=[(1, "0" * 64)])
    with pytest.raises(MigrationAltered):
        plan(connection, migrations)


# --- APPLY: ONE TRANSACTION PER MIGRATION, LEDGER ROW INSIDE IT --------------------------- #

def test_apply_runs_every_migration_in_ascending_order(migrations):
    connection = RecordingConnection()
    applied = apply(connection, migrations)
    assert [record.version for record in applied] == [1, 2, 3, 4, 5, 6, 7]
    assert all(isinstance(record, AppliedMigration) for record in applied)


def test_each_migration_commits_with_its_own_ledger_row(migrations):
    connection = RecordingConnection()
    apply(connection, migrations)

    # After the ledger DDL and its commit, the shape is exactly:
    #   execute(migration sql), execute(ledger insert), commit — seven times.
    tail = connection.journal[3:]
    assert len(tail) == len(migrations) * 3
    for index, migration in enumerate(migrations):
        statement, ledger, commit = tail[index * 3 : index * 3 + 3]
        assert statement[0] == "execute" and statement[1] == migration.sql
        assert ledger[0] == "execute" and "INSERT INTO public.schema_migration" in ledger[1]
        assert ledger[2] == (
            migration.version,
            migration.name,
            migration.filename,
            migration.checksum_sha256,
        )
        assert commit == ("commit",)


def test_the_migration_sql_is_executed_with_no_parameter_sequence(migrations):
    """psycopg2 performs `%` interpolation only when a parameter sequence is passed, and
    the migration SQL contains `%I` and `%L` inside plpgsql `format()` calls. Passing an
    empty sequence would make the driver try to bind them.
    """
    connection = RecordingConnection()
    apply(connection, migrations)
    for entry in connection.journal:
        if entry[0] != "execute":
            continue
        sql, parameters = entry[1], entry[2]
        if "INSERT INTO public.schema_migration" in sql:
            assert parameters is not None
        else:
            assert parameters is None, f"{sql[:40]!r} was executed with parameters"


def test_at_least_one_delivered_migration_contains_a_percent_placeholder(migrations):
    """The test above guards a real hazard, not a hypothetical one."""
    assert any("%I" in migration.sql for migration in migrations)


def test_applying_a_current_store_is_a_success_and_is_reported_as_one(migrations):
    connection = RecordingConnection(
        ledger_rows=[(m.version, m.checksum_sha256) for m in migrations]
    )
    assert apply(connection, migrations) == ()


def test_only_pending_migrations_are_applied(migrations):
    connection = RecordingConnection(
        ledger_rows=[(m.version, m.checksum_sha256) for m in migrations[:4]]
    )
    applied = apply(connection, migrations)
    assert [record.version for record in applied] == [5, 6, 7]


# --- FAILURE STOPS THE RUN AND ROLLS BACK -------------------------------------------------- #

def test_a_failing_migration_rolls_back_and_stops_the_run(migrations):
    """Later migrations were written against the state the failed one was to produce.
    Running them anyway turns one clear failure into several confusing ones.
    """
    connection = RecordingConnection(fail_on="CREATE TABLE dial.history")
    with pytest.raises(MigrationApplyFailed) as raised:
        apply(connection, migrations)
    assert raised.value.version == 4
    assert raised.value.filename == "0004_dial_history.sql"
    assert connection.shape[-1] == "rollback"
    # Three migrations committed before the failure; nothing after it ran.
    assert connection.shape.count("commit") == 4  # ledger DDL + migrations 1..3
    assert not any(
        "CREATE TABLE publication.public_envelope" in sql for sql in connection.executed
    )


def test_the_failure_carries_a_reference_and_not_the_databases_error_text(migrations):
    """A driver error message can quote the failing statement, and a statement can carry
    a value (PBG-SEC-002). The original exception stays chained for a terminal.
    """
    connection = RecordingConnection(fail_on="CREATE TABLE dial.history")
    with pytest.raises(MigrationApplyFailed) as raised:
        apply(connection, migrations)
    assert str(raised.value) == "migration 4 (0004_dial_history.sql) failed to apply"
    assert raised.value.__cause__ is not None


def test_a_failure_does_not_write_a_ledger_row_for_the_failed_migration(migrations):
    connection = RecordingConnection(fail_on="CREATE TABLE dial.history")
    with pytest.raises(MigrationApplyFailed):
        apply(connection, migrations)
    ledger_writes = [
        entry[2]
        for entry in connection.journal
        if entry[0] == "execute" and "INSERT INTO public.schema_migration" in entry[1]
    ]
    assert [row[0] for row in ledger_writes] == [1, 2, 3]
