"""Applying the migration set to a store (BLUEPRINT §4, PBG-DATA-002, PBG-DATA-003).

**This is not the application's startup path.** Nothing under
:mod:`crash_detector.collectors`, :mod:`crash_detector.engine`,
:mod:`crash_detector.publication`, :mod:`crash_detector.serving` or
:mod:`crash_detector.witness` imports this module, and a test asserts it. Migration is a
separate, deliberate, once-per-deployment action run by ``db/migrate.py`` under the
migrator's credentials — not something six replicas race each other to do on boot with
whatever privileges their own service role happens to hold.

----

NO DRIVER IMPORT LIVES HERE.

:func:`apply` takes an already-open **PEP 249 connection**. That is what keeps the whole of
``src/`` free of a database driver import, and it is what lets these functions be tested
against a recording double that captures the exact statements issued, as well as against a
live PostgreSQL. Evidence from the double and evidence from the live catalogue answer
different questions and neither substitutes for the other.

----

THE LEDGER IS CREATED BY THE RUNNER, NOT BY A MIGRATION.

``public.schema_migration`` has to exist before migration 1 can record itself, so it
cannot be the product of a migration. :func:`ensure_ledger` creates it idempotently. It
lives in schema ``public`` rather than in a seventh application schema so that BLUEPRINT
§4's "six schemas" stays literally true of this store; migration 1 revokes PUBLIC's
inherited rights on ``public``, and no application role is granted anything there, so the
ledger is readable by the migrator alone.

----

ONE TRANSACTION PER MIGRATION, WITH ITS LEDGER ROW INSIDE IT.

The statements of a migration and the row that records the migration commit together or
not at all. The alternative — apply, then record — has a window in which a crash leaves a
store whose ledger under-reports it, and the next run then re-applies statements against
objects that already exist. PostgreSQL executes DDL transactionally, so this costs
nothing here and is worth having.

A failure aborts the whole run at the failing migration. Later migrations are NOT
attempted: they were written against the state the failed one was supposed to produce, and
running them anyway is how one clear failure becomes several confusing ones.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from crash_detector.store.migrations import Migration, pending_migrations

__all__ = [
    "LEDGER_TABLE",
    "LEDGER_DDL",
    "MigrationApplyFailed",
    "AppliedMigration",
    "ensure_ledger",
    "read_ledger",
    "plan",
    "apply",
]

#: Qualified name of the migration ledger. Not one of BLUEPRINT §4's six schemas.
LEDGER_TABLE = "public.schema_migration"

#: Idempotent. Every timestamp is ``timestamptz`` here too (``PBG-DATA-001``).
LEDGER_DDL = """
CREATE TABLE IF NOT EXISTS public.schema_migration (
    version         integer     NOT NULL,
    name            text        NOT NULL,
    filename        text        NOT NULL,
    checksum_sha256 text        NOT NULL,
    applied_utc     timestamptz NOT NULL DEFAULT now(),
    applied_by      text        NOT NULL DEFAULT current_user,
    CONSTRAINT schema_migration_pk PRIMARY KEY (version),
    CONSTRAINT schema_migration_checksum_is_sha256
        CHECK (checksum_sha256 ~ '^[0-9a-f]{64}$')
);
"""

_LEDGER_SELECT = (
    "SELECT version, checksum_sha256 FROM public.schema_migration ORDER BY version"
)

_LEDGER_INSERT = (
    "INSERT INTO public.schema_migration (version, name, filename, checksum_sha256) "
    "VALUES (%s, %s, %s, %s)"
)


class MigrationApplyFailed(Exception):
    """A migration raised while being applied. The run stops at it.

    Carries the version and filename by reference. It deliberately does not carry the
    database's own error text forward into any governed record: a driver error message can
    quote the failing statement, and a statement can carry a value (``PBG-SEC-002``). The
    original exception remains chained for an operator reading a terminal.
    """

    def __init__(self, version: int, filename: str) -> None:
        super().__init__(f"migration {version} ({filename}) failed to apply")
        self.version = version
        self.filename = filename


@dataclass(frozen=True)
class AppliedMigration:
    """One migration this run applied."""

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `AppliedMigration.__new__(AppliedMigration)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("version", "name", "filename", "checksum_sha256")

    version: int
    name: str
    filename: str
    checksum_sha256: str


def ensure_ledger(connection: Any) -> None:
    """Create the migration ledger if it is absent. Idempotent."""
    with connection.cursor() as cursor:
        cursor.execute(LEDGER_DDL)
    connection.commit()


def read_ledger(connection: Any) -> dict[int, str]:
    """``{version: checksum_sha256}`` for every migration the store records as applied."""
    with connection.cursor() as cursor:
        cursor.execute(_LEDGER_SELECT)
        rows = cursor.fetchall()
    return {int(version): str(checksum) for version, checksum in rows}


def plan(connection: Any, migrations: Sequence[Migration]) -> tuple[Migration, ...]:
    """What :func:`apply` would apply, without applying it.

    Performs the full forward-only validation — an edited or vanished applied migration
    raises here, before anything is written. So ``--plan`` is a real check and not a
    preview: a plan that succeeds and an apply that then refuses is not a state this can
    produce.
    """
    ensure_ledger(connection)
    return pending_migrations(tuple(migrations), read_ledger(connection))


def apply(
    connection: Any, migrations: Sequence[Migration]
) -> tuple[AppliedMigration, ...]:
    """Apply every pending migration in order, each with its ledger row, atomically.

    Returns what was applied — empty when the store was already current, which is a
    success and is reported as one rather than as "nothing happened".
    """
    outstanding = plan(connection, migrations)

    applied: list[AppliedMigration] = []
    for migration in outstanding:
        try:
            with connection.cursor() as cursor:
                # ONE ARGUMENT, DELIBERATELY. psycopg2 performs `%` interpolation only
                # when a parameter sequence is passed; the migration SQL contains `%I`
                # and `%L` inside plpgsql `format()` calls, and passing an empty
                # parameter sequence here would make the driver try to bind them.
                cursor.execute(migration.sql)
                cursor.execute(
                    _LEDGER_INSERT,
                    (
                        migration.version,
                        migration.name,
                        migration.filename,
                        migration.checksum_sha256,
                    ),
                )
            connection.commit()
        except Exception as exc:  # noqa: BLE001 — re-raised as a named failure below
            connection.rollback()
            raise MigrationApplyFailed(migration.version, migration.filename) from exc

        applied.append(
            AppliedMigration(
                version=migration.version,
                name=migration.name,
                filename=migration.filename,
                checksum_sha256=migration.checksum_sha256,
            )
        )

    return tuple(applied)
