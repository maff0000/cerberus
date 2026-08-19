#!/usr/bin/env python3
"""The dedicated migration step (BLUEPRINT §4, PBG-DATA-002, PBG-DATA-003).

    python3 db/migrate.py --plan     # what would be applied. Validates; writes nothing.
    python3 db/migrate.py --apply    # apply every pending migration, in order.

**This command is not part of any service's startup.** It lives here, outside ``src/``,
rather than inside the importable application package, so that no service can reach it by
an import even by accident: migrating is a deliberate deployment action taken once under
the migrator's credentials, not something six replicas race each other to do on boot with
whatever privileges their own role happens to hold.

It is also the only file in this repository that imports a database driver. Everything it
does with the connection is in :mod:`crash_detector.store.migrate`, which takes a PEP 249
connection as an argument and is therefore testable without one.

----

CONFIGURATION IS READ FROM THE ENVIRONMENT, AND THE SECRET IS READ BY NAME ONLY.

    CD_STORE_HOST                 host of the store
    CD_STORE_PORT                 port of the store
    CD_STORE_NAME                 database name
    CD_STORE_MIGRATOR_USER        the migrator role — NOT any of the six application roles
    CD_STORE_MIGRATOR_PASSWORD    read at the point of use; never logged, never echoed,
                                  never written to any record (PBG-SEC-002, non-waivable)
    CD_STORE_SSLMODE              optional; defaults to `prefer`

Every one of those is REQUIRED except the last, and a missing one is a refusal rather than
a default. A default host is a default that connects to the wrong store exactly once.

----

THE MIGRATOR IS NOT AN APPLICATION ROLE.

It needs CREATEROLE (migration 1 creates the six roles) and ownership of the database. No
application role has, or should be able to obtain, either. Every migration must be applied
by the SAME migrator role: migration 7's ``ALTER DEFAULT PRIVILEGES`` is recorded against
the role that ran it, so a second migrator would leave the default privilege attached to
the wrong grantor. That is a deployment constraint, recorded in README.md.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_MIGRATIONS_DIR = _HERE / "migrations"
_SRC = _HERE.parent / "src"

# The single supported import route for this project is PYTHONPATH=src with no install
# step (BLUEPRINT §11). Resolved relative to this file, so there is no host-specific
# absolute path anywhere and the command works from any working directory.
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from crash_detector.store.migrate import apply, plan  # noqa: E402
from crash_detector.store.migrations import (  # noqa: E402
    MigrationSetInvalid,
    load_migrations,
)

_REQUIRED_ENV = (
    "CD_STORE_HOST",
    "CD_STORE_PORT",
    "CD_STORE_NAME",
    "CD_STORE_MIGRATOR_USER",
    "CD_STORE_MIGRATOR_PASSWORD",
)

def _connection_settings() -> dict[str, str]:
    """Connection settings from the environment, or a refusal naming what is missing."""
    missing = [name for name in _REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        raise SystemExit(
            "REFUSED: the migration step is configured from the environment and these "
            f"variables are unset or empty: {', '.join(missing)}. They are named, never "
            "defaulted: a default host connects to the wrong store exactly once."
        )
    return {
        "host": os.environ["CD_STORE_HOST"],
        "port": os.environ["CD_STORE_PORT"],
        "dbname": os.environ["CD_STORE_NAME"],
        "user": os.environ["CD_STORE_MIGRATOR_USER"],
        "password": os.environ["CD_STORE_MIGRATOR_PASSWORD"],
        "sslmode": os.environ.get("CD_STORE_SSLMODE", "prefer"),
    }


def _describe(settings: dict[str, str]) -> str:
    """A printable description of the target. The password is not in it, by construction."""
    return (
        f"{settings['user']}@{settings['host']}:{settings['port']}/{settings['dbname']} "
        f"(sslmode={settings['sslmode']})"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="db/migrate.py",
        description="Apply the crash-detector store migrations. Forward-only.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--plan",
        action="store_true",
        help="validate the set and report what is pending. Writes nothing.",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="apply every pending migration, each with its ledger row, atomically.",
    )
    args = parser.parse_args(argv)

    try:
        migrations = load_migrations(_MIGRATIONS_DIR)
    except MigrationSetInvalid as exc:
        print(f"MIGRATION_SET_INVALID: {exc}", file=sys.stderr)
        return 2

    print(f"migrations discovered: {len(migrations)} in {_MIGRATIONS_DIR}")
    for migration in migrations:
        print(f"  {migration.version:04d} {migration.name} {migration.checksum_sha256}")

    settings = _connection_settings()
    print(f"target: {_describe(settings)}")

    # Imported here rather than at module scope so that `--help` and the migration-set
    # validation above work on a host without the driver, and so the one driver import in
    # this repository is at its point of use.
    import psycopg2

    connection = psycopg2.connect(**settings)
    try:
        if args.plan:
            outstanding = plan(connection, migrations)
            if not outstanding:
                print("PENDING: none — the store is current")
            for migration in outstanding:
                print(f"PENDING: {migration.version:04d} {migration.name}")
            return 0

        applied = apply(connection, migrations)
        if not applied:
            print("APPLIED: none — the store was already current")
        for record in applied:
            print(f"APPLIED: {record.version:04d} {record.name} {record.checksum_sha256}")
        return 0
    except MigrationSetInvalid as exc:
        print(f"MIGRATION_SET_INVALID: {exc}", file=sys.stderr)
        return 2
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
