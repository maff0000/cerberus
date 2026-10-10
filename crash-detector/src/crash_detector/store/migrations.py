"""Discovering and validating the migration set (BLUEPRINT §4, Standards Baseline §10).

**Append-only and forward-only.** A migration that mutates a previous migration destroys
the ability to reason about any environment that already ran it, so this module treats an
edited migration file as a defect and refuses the whole run rather than applying the rest
of the set on top of a store whose history no longer matches its files.

Everything here is pure: it reads files and compares them with what a ledger says was
applied. It opens no connection and imports no driver. The half that talks to a database
is :mod:`crash_detector.store.migrate`, which takes the connection as an argument.

----

WHAT A MIGRATION FILE MUST DECLARE, AND WHY THE HEADER IS ENFORCED.

Each file begins with exactly three header lines::

    -- migration: 7
    -- name: grant_matrix
    -- rollback: NONE. <why, or what the rollback is>

``rollback`` is mandatory and may not be empty. "Every migration states its rollback, or
states plainly that it has none" (Standards Baseline §10) — and the value of the rule is
entirely in the *plainly*. A migration with no rollback field is not a migration whose
author decided it was irreversible; it is one where nobody decided anything, and the
person who finds that out is mid-incident.

The header is checked against the FILENAME as well as against itself. A file named
``0007_grant_matrix.sql`` declaring ``-- migration: 6`` is refused: two independent
statements of the same fact that disagree is the cheapest available signal that a file was
copied and half-edited.

----

WHY THE CHECKSUM IS OVER THE WHOLE FILE.

The ledger records the SHA-256 of the file's bytes, header and comments included. A
comment is not cosmetic here: these files carry the reasoning for a grant matrix, and an
edit to that reasoning after the migration has been applied leaves the store's own
explanation of itself out of step with the store. Superseding it with a new migration is
the supported route; editing the applied one is not (``PBG-CONT-003`` has the same shape
for the Build Log, and for the same reason).
"""

from __future__ import annotations

import hashlib
import pathlib
import re
from dataclasses import dataclass
from typing import Mapping

__all__ = [
    "Migration",
    "MigrationSetInvalid",
    "MigrationFileInvalid",
    "MigrationAltered",
    "MigrationMissing",
    "MIGRATION_FILENAME_PATTERN",
    "load_migrations",
    "pending_migrations",
]

#: ``NNNN_snake_case_name.sql``. Zero-padded so the lexical order of the directory listing
#: is the numeric order of application, which means a human reading ``ls`` and the runner
#: reading the set agree without either having to sort cleverly.
MIGRATION_FILENAME_PATTERN = re.compile(r"^(?P<version>\d{4})_(?P<name>[a-z0-9_]+)\.sql$")

_HEADER_VERSION = re.compile(r"^--\s*migration:\s*(?P<version>\d+)\s*$")
_HEADER_NAME = re.compile(r"^--\s*name:\s*(?P<name>[a-z0-9_]+)\s*$")
_HEADER_ROLLBACK = re.compile(r"^--\s*rollback:\s*(?P<rollback>\S.*)$")


class MigrationSetInvalid(Exception):
    """The migration set as a whole cannot be applied.

    The base class exists so a caller can catch the CLASS of refusal rather than the one
    member it happened to meet.
    """


class MigrationFileInvalid(MigrationSetInvalid):
    """One migration file is malformed, misnamed, or missing a required declaration."""


class MigrationAltered(MigrationSetInvalid):
    """A migration that was already applied no longer matches the file on disk.

    Forward-only means the applied history is immutable. Correct it by adding a new
    migration that supersedes it, never by editing the one that ran.
    """


class MigrationMissing(MigrationSetInvalid):
    """The ledger records a migration for which no file exists.

    Refused rather than ignored: the store contains changes this checkout cannot describe,
    so this checkout cannot say what applying the rest of the set would produce.
    """


@dataclass(frozen=True)
class Migration:
    """One forward-only migration file."""

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `Migration.__new__(Migration)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("version", "name", "filename", "sql", "checksum_sha256", "rollback")

    version: int
    name: str
    filename: str
    sql: str
    checksum_sha256: str
    rollback: str

    def __post_init__(self) -> None:
        if self.version < 1:
            raise MigrationFileInvalid(
                f"{self.filename}: migration versions start at 1, got {self.version}"
            )
        if not self.rollback:
            raise MigrationFileInvalid(
                f"{self.filename}: a migration must state its rollback or state plainly "
                "that it has none (Standards Baseline §10)"
            )
        statements = "\n".join(
            line
            for line in self.sql.splitlines()
            if line.strip() and not line.strip().startswith("--")
        )
        if not statements.strip():
            raise MigrationFileInvalid(
                f"{self.filename}: contains no SQL, only comments. An empty migration "
                "applies cleanly and proves nothing, so it is refused rather than "
                "recorded as applied."
            )


def _parse_header(filename: str, text: str) -> tuple[int, str, str]:
    """The three declared header fields, or :exc:`MigrationFileInvalid`.

    The rollback declaration continues across following comment lines, so an author can
    explain an irreversible migration properly instead of compressing the reason onto one
    line and thereby not giving one.
    """
    lines = text.splitlines()
    if len(lines) < 3:
        raise MigrationFileInvalid(f"{filename}: too short to carry a migration header")

    version_match = _HEADER_VERSION.match(lines[0])
    if version_match is None:
        raise MigrationFileInvalid(
            f"{filename}: line 1 must be '-- migration: <n>', got {lines[0]!r}"
        )
    name_match = _HEADER_NAME.match(lines[1])
    if name_match is None:
        raise MigrationFileInvalid(
            f"{filename}: line 2 must be '-- name: <snake_case>', got {lines[1]!r}"
        )
    rollback_match = _HEADER_ROLLBACK.match(lines[2])
    if rollback_match is None:
        raise MigrationFileInvalid(
            f"{filename}: line 3 must be '-- rollback: <statement>' and must not be "
            f"empty, got {lines[2]!r}"
        )

    rollback_parts = [rollback_match.group("rollback").strip()]
    for line in lines[3:]:
        if not line.startswith("--"):
            break
        continuation = line[2:].strip()
        if not continuation:
            break
        if _HEADER_VERSION.match(line) or _HEADER_NAME.match(line):
            break
        rollback_parts.append(continuation)

    return (
        int(version_match.group("version")),
        name_match.group("name"),
        " ".join(rollback_parts),
    )


def load_migrations(directory: pathlib.Path) -> tuple[Migration, ...]:
    """Every migration in ``directory``, ordered, validated as a set.

    Refuses — rather than warns, skips or sorts around — a directory that is not a
    coherent forward-only set:

      * a filename that does not match ``NNNN_name.sql``. A stray ``.sql`` in the
        migrations directory is either a migration nobody named properly or a scratch file
        somebody left, and applying either would be guessing which;
      * a header that disagrees with the filename;
      * two files claiming the same version;
      * a gap in the version sequence. Versions must run 1..N with nothing missing,
        because a gap means either a migration was deleted — which forward-only forbids —
        or two branches numbered independently and one of them is about to be applied out
        of the order it was written in.
    """
    directory = pathlib.Path(directory)
    if not directory.is_dir():
        raise MigrationFileInvalid(f"not a migrations directory: {directory}")

    found: dict[int, Migration] = {}
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        if path.suffix != ".sql":
            continue
        match = MIGRATION_FILENAME_PATTERN.match(path.name)
        if match is None:
            raise MigrationFileInvalid(
                f"{path.name}: filename must match NNNN_snake_case_name.sql. A .sql file "
                "in the migrations directory that is not a migration is refused rather "
                "than skipped — skipping it would make a mis-named migration invisible."
            )

        raw = path.read_bytes()
        text = raw.decode("utf-8")
        header_version, header_name, rollback = _parse_header(path.name, text)

        filename_version = int(match.group("version"))
        filename_name = match.group("name")
        if header_version != filename_version:
            raise MigrationFileInvalid(
                f"{path.name}: declares '-- migration: {header_version}' but is named for "
                f"version {filename_version}"
            )
        if header_name != filename_name:
            raise MigrationFileInvalid(
                f"{path.name}: declares '-- name: {header_name}' but is named "
                f"{filename_name!r}"
            )
        if header_version in found:
            raise MigrationFileInvalid(
                f"{path.name}: version {header_version} is already claimed by "
                f"{found[header_version].filename}"
            )

        found[header_version] = Migration(
            version=header_version,
            name=header_name,
            filename=path.name,
            sql=text,
            checksum_sha256=hashlib.sha256(raw).hexdigest(),
            rollback=rollback,
        )

    if not found:
        raise MigrationFileInvalid(
            f"no migrations found in {directory}. An empty migration set would apply "
            "cleanly and prove nothing, so it is refused rather than reported as success."
        )

    expected = list(range(1, max(found) + 1))
    missing = [version for version in expected if version not in found]
    if missing:
        raise MigrationFileInvalid(
            f"gap in the migration sequence: {missing} absent from {sorted(found)}"
        )

    return tuple(found[version] for version in expected)


def pending_migrations(
    migrations: tuple[Migration, ...], applied: Mapping[int, str]
) -> tuple[Migration, ...]:
    """Those in ``migrations`` not yet in ``applied``, in ascending order.

    ``applied`` maps a version to the SHA-256 the ledger recorded for it.

    Refuses if an applied migration's file has changed (:exc:`MigrationAltered`) or has
    disappeared (:exc:`MigrationMissing`). Both are checked BEFORE anything is reported as
    pending, so a run that would apply new migrations on top of a history it cannot
    account for never starts.
    """
    by_version = {migration.version: migration for migration in migrations}

    for version in sorted(applied):
        migration = by_version.get(version)
        if migration is None:
            raise MigrationMissing(
                f"the ledger records migration {version} as applied, but no file for it "
                "exists in this checkout. The store carries a change this checkout "
                "cannot describe."
            )
        if migration.checksum_sha256 != applied[version]:
            raise MigrationAltered(
                f"{migration.filename} has changed since it was applied "
                f"(ledger {applied[version][:12]}…, file "
                f"{migration.checksum_sha256[:12]}…). Migrations are append-only and "
                "forward-only: supersede it with a new migration, never edit the one "
                "that ran."
            )

    return tuple(
        migration for migration in migrations if migration.version not in applied
    )
