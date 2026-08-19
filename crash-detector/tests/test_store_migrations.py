"""The migration set is validated before anything is applied — A5, PBG-DATA-002/003.

Append-only and forward-only means the applied history is IMMUTABLE. These tests prove
the loader refuses each way that stops being true, at the loader's own seam
(``PBG-ASSURE-017``): a set that is silently accepted when a file has been edited is a
store nobody can reason about, discovered at the worst possible moment.

Every refusal is exercised against a temporary directory built for the test. None of them
touches the delivered migrations.
"""

from __future__ import annotations

import hashlib
import pathlib

import pytest

from crash_detector.store.migrations import (
    MIGRATION_FILENAME_PATTERN,
    MigrationAltered,
    MigrationFileInvalid,
    MigrationMissing,
    MigrationSetInvalid,
    load_migrations,
    pending_migrations,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
DELIVERED = ROOT / "db" / "migrations"


def _write(directory: pathlib.Path, filename: str, body: str) -> pathlib.Path:
    path = directory / filename
    path.write_text(body, encoding="utf-8")
    return path


def _valid(version: int, name: str, statement: str = "SELECT 1;") -> str:
    return (
        f"-- migration: {version}\n"
        f"-- name: {name}\n"
        f"-- rollback: NONE. A test fixture.\n"
        f"\n{statement}\n"
    )


@pytest.fixture()
def migrations_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    directory = tmp_path / "migrations"
    directory.mkdir()
    return directory


# --- THE DELIVERED SET ---------------------------------------------------------------------- #

def test_the_delivered_set_loads():
    migrations = load_migrations(DELIVERED)
    assert [m.version for m in migrations] == [1, 2, 3, 4, 5, 6, 7]
    assert [m.name for m in migrations] == [
        "schemas_roles_and_revoke_by_default",
        "raw_source_registry_and_observations",
        "witness_observations",
        "dial_history",
        "publication",
        "private_and_alert",
        "grant_matrix",
    ]


def test_every_delivered_checksum_is_the_sha256_of_the_file_bytes():
    """The ledger records this value, so it must be the one an operator can reproduce."""
    for migration in load_migrations(DELIVERED):
        raw = (DELIVERED / migration.filename).read_bytes()
        assert migration.checksum_sha256 == hashlib.sha256(raw).hexdigest()


def test_the_filename_pattern_orders_lexically_and_numerically_the_same_way():
    names = sorted(path.name for path in DELIVERED.glob("*.sql"))
    versions = [
        int(MIGRATION_FILENAME_PATTERN.match(name).group("version")) for name in names
    ]
    assert versions == sorted(versions)


# --- THE HEADER IS ENFORCED ----------------------------------------------------------------- #

def test_a_migration_with_no_rollback_declaration_is_refused(
    migrations_dir: pathlib.Path,
):
    """Standards Baseline §10. A migration with no rollback field is not one whose author
    decided it was irreversible; it is one where nobody decided anything.
    """
    _write(migrations_dir, "0001_x.sql", "-- migration: 1\n-- name: x\nSELECT 1;\n")
    with pytest.raises(MigrationFileInvalid, match="rollback"):
        load_migrations(migrations_dir)


def test_an_empty_rollback_declaration_is_refused(migrations_dir: pathlib.Path):
    _write(
        migrations_dir,
        "0001_x.sql",
        "-- migration: 1\n-- name: x\n-- rollback:\nSELECT 1;\n",
    )
    with pytest.raises(MigrationFileInvalid):
        load_migrations(migrations_dir)


def test_a_header_that_disagrees_with_the_filename_is_refused(
    migrations_dir: pathlib.Path,
):
    """Two independent statements of the same fact that disagree is the cheapest available
    signal that a file was copied and half-edited.
    """
    _write(migrations_dir, "0002_x.sql", _valid(1, "x"))
    with pytest.raises(MigrationFileInvalid, match="named for version"):
        load_migrations(migrations_dir)


def test_a_name_that_disagrees_with_the_filename_is_refused(
    migrations_dir: pathlib.Path,
):
    _write(migrations_dir, "0001_x.sql", _valid(1, "y"))
    with pytest.raises(MigrationFileInvalid, match="declares"):
        load_migrations(migrations_dir)


def test_a_stray_sql_file_is_refused_rather_than_skipped(migrations_dir: pathlib.Path):
    """Skipping it would make a MIS-NAMED MIGRATION INVISIBLE, which is the failure mode
    that matters: the file most likely to be named wrongly is the one somebody added in a
    hurry.
    """
    _write(migrations_dir, "0001_x.sql", _valid(1, "x"))
    _write(migrations_dir, "scratch.sql", "SELECT 1;")
    with pytest.raises(MigrationFileInvalid, match="NNNN_snake_case_name"):
        load_migrations(migrations_dir)


def test_a_gap_in_the_sequence_is_refused(migrations_dir: pathlib.Path):
    """A gap means either a migration was deleted, which forward-only forbids, or two
    branches numbered independently and one is about to be applied out of order.
    """
    _write(migrations_dir, "0001_a.sql", _valid(1, "a"))
    _write(migrations_dir, "0003_c.sql", _valid(3, "c"))
    with pytest.raises(MigrationFileInvalid, match="gap"):
        load_migrations(migrations_dir)


def test_an_empty_migrations_directory_is_refused(migrations_dir: pathlib.Path):
    """An empty set would apply cleanly and prove nothing. Reported as a refusal, never as
    success (Standards Baseline §8).
    """
    with pytest.raises(MigrationFileInvalid, match="no migrations found"):
        load_migrations(migrations_dir)


def test_a_migration_with_no_sql_is_refused(migrations_dir: pathlib.Path):
    _write(migrations_dir, "0001_x.sql", "-- migration: 1\n-- name: x\n-- rollback: NONE.\n")
    with pytest.raises(MigrationFileInvalid, match="no SQL"):
        load_migrations(migrations_dir)


def test_a_multi_line_rollback_declaration_is_read_whole(migrations_dir: pathlib.Path):
    """An author must be able to explain an irreversible migration properly rather than
    compressing the reason onto one line and thereby not giving one.
    """
    _write(
        migrations_dir,
        "0001_x.sql",
        "-- migration: 1\n"
        "-- name: x\n"
        "-- rollback: NONE. Dropping this table destroys the append-only record,\n"
        "--   and recovery is by restore from dump.\n"
        "\nSELECT 1;\n",
    )
    (migration,) = load_migrations(migrations_dir)
    assert "recovery is by restore from dump" in migration.rollback


# --- FORWARD-ONLY, ENFORCED AGAINST THE LEDGER ---------------------------------------------- #

def test_nothing_is_pending_when_the_ledger_matches(migrations_dir: pathlib.Path):
    _write(migrations_dir, "0001_a.sql", _valid(1, "a"))
    migrations = load_migrations(migrations_dir)
    applied = {1: migrations[0].checksum_sha256}
    assert pending_migrations(migrations, applied) == ()


def test_only_the_unapplied_migrations_are_pending(migrations_dir: pathlib.Path):
    _write(migrations_dir, "0001_a.sql", _valid(1, "a"))
    _write(migrations_dir, "0002_b.sql", _valid(2, "b"))
    migrations = load_migrations(migrations_dir)
    pending = pending_migrations(migrations, {1: migrations[0].checksum_sha256})
    assert [m.version for m in pending] == [2]


def test_an_edited_applied_migration_is_refused(migrations_dir: pathlib.Path):
    """A migration that mutates a previous migration destroys the ability to reason about
    any environment that already ran it. Supersede it; never edit the one that ran.
    """
    _write(migrations_dir, "0001_a.sql", _valid(1, "a"))
    migrations = load_migrations(migrations_dir)
    with pytest.raises(MigrationAltered, match="append-only and forward-only"):
        pending_migrations(migrations, {1: "0" * 64})


def test_an_applied_migration_with_no_file_is_refused(migrations_dir: pathlib.Path):
    """The store carries a change this checkout cannot describe, so this checkout cannot
    say what applying the rest would produce.
    """
    _write(migrations_dir, "0001_a.sql", _valid(1, "a"))
    migrations = load_migrations(migrations_dir)
    with pytest.raises(MigrationMissing):
        pending_migrations(migrations, {1: migrations[0].checksum_sha256, 2: "x" * 64})


def test_the_whole_history_is_validated_before_anything_is_reported_pending(
    migrations_dir: pathlib.Path,
):
    """A run that would apply new migrations on top of a history it cannot account for
    must never start — not start and then discover.
    """
    _write(migrations_dir, "0001_a.sql", _valid(1, "a"))
    _write(migrations_dir, "0002_b.sql", _valid(2, "b"))
    migrations = load_migrations(migrations_dir)
    with pytest.raises(MigrationAltered):
        pending_migrations(migrations, {1: "f" * 64})


def test_every_refusal_shares_one_base_class(migrations_dir: pathlib.Path):
    """So a caller can catch the CLASS rather than the member it happened to meet."""
    for subclass in (MigrationFileInvalid, MigrationAltered, MigrationMissing):
        assert issubclass(subclass, MigrationSetInvalid)


def test_a_comment_only_edit_still_changes_the_checksum(migrations_dir: pathlib.Path):
    """The checksum is over the WHOLE file, comments included, and that is deliberate.

    These files carry the reasoning for a grant matrix. An edit to that reasoning after
    the migration has been applied leaves the store's own explanation of itself out of
    step with the store.
    """
    path = _write(migrations_dir, "0001_a.sql", _valid(1, "a"))
    before = load_migrations(migrations_dir)[0].checksum_sha256
    path.write_text(
        path.read_text(encoding="utf-8") + "-- an added explanation\n", encoding="utf-8"
    )
    after = load_migrations(migrations_dir)[0].checksum_sha256
    assert before != after
