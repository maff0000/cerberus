"""The store schema, asserted against the code it must match — BLUEPRINT §4, A5.

These tests read the migration SQL as text. They are not a substitute for building a store
and reading its catalogue — that is done separately and independently, and an Assurance
seat does it again from scratch. What they establish is the property a live store cannot:
that the SQL and the PYTHON agree about the vocabularies they both encode.

A store built from these migrations could pass every catalogue query and still admit an
outcome the application never produces, or refuse one it does. Those two vocabularies live
in two files and there is nothing about a working database that makes them agree; only a
test that reads both does.

Each vocabulary is imported from its declaring module rather than retyped here. A constant
retyped in a test is a second copy with a bug scheduled for whoever edits the first.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest

from crash_detector.dials.dialset import DIAL_IDS
from crash_detector.observations import MAX_INSTANCE_PATH_LENGTH, OUTCOME_CLASSES
from crash_detector.source_registry import CRITICALITY_NAMES
from crash_detector.store.migrations import load_migrations
from crash_detector.witness.panel import PANEL_STATES, UNAVAILABLE_REASONS

ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "db" / "migrations"
CONTRACTS_DIR = ROOT / "contracts"

MIGRATIONS = load_migrations(MIGRATIONS_DIR)
SQL_BY_NAME = {migration.name: migration.sql for migration in MIGRATIONS}
ALL_SQL = "\n".join(migration.sql for migration in MIGRATIONS)

#: BLUEPRINT §4. Six, and the register check must count these rather than "how many
#: schemas exist" — the migration ledger lives in `public`, which is not one of them.
EXPECTED_SCHEMAS = ("raw", "witness", "dial", "publication", "private", "alert")

EXPECTED_ROLES = (
    "cd_collector",
    "cd_witness",
    "cd_engine",
    "cd_public",
    "cd_private",
    "cd_review",
)

#: The four tables BLUEPRINT §4 names as append-only.
APPEND_ONLY_TABLES = (
    "dial.history",
    "raw.observation",
    "witness.observation",
    "alert.event",
)


def _statements_only(sql: str) -> str:
    """``sql`` with ``--`` comment lines and ``COMMENT ON`` statements removed.

    A check that reads the prose in a migration is a check an author satisfies by editing
    the prose. These tests must judge STATEMENTS.
    """
    lines = [
        line for line in sql.splitlines() if not line.strip().startswith("--")
    ]
    text = "\n".join(lines)
    return re.sub(r"COMMENT ON [^;]*;", "", text, flags=re.DOTALL)


def _quoted_list(sql: str, marker: str) -> list[str]:
    """The single-quoted literals inside the parenthesised group following ``marker``."""
    index = sql.index(marker)
    depth = 0
    end = index
    for position in range(index, len(sql)):
        if sql[position] == "(":
            depth += 1
        elif sql[position] == ")":
            depth -= 1
            if depth == 0:
                end = position
                break
    return re.findall(r"'([^']*)'", sql[index:end])


# --- THE SET ITSELF ---------------------------------------------------------------------- #

def test_the_migration_set_loads_and_is_not_empty():
    assert len(MIGRATIONS) == 7
    assert [migration.version for migration in MIGRATIONS] == list(range(1, 8))


def test_every_migration_states_its_rollback():
    """Standards Baseline §10. The value of the rule is entirely in the *plainly*."""
    for migration in MIGRATIONS:
        assert migration.rollback, migration.filename
        assert len(migration.rollback) > 40, (
            f"{migration.filename}: the rollback declaration is a token rather than a "
            "statement"
        )


def test_the_migration_step_is_not_the_application_startup_path():
    """PBG-DATA-002, PBG-DATA-003.

    The command lives at db/migrate.py, OUTSIDE the importable application package, so no
    service can reach it by an import even by accident. Asserted structurally.
    """
    assert (ROOT / "db" / "migrate.py").is_file()
    package = ROOT / "src" / "crash_detector"
    offenders = []
    for path in sorted(package.rglob("*.py")):
        if path.parent.name == "store":
            continue
        text = path.read_text(encoding="utf-8")
        if "crash_detector.store" in text:
            offenders.append(str(path.relative_to(package)))
    assert offenders == [], (
        f"application modules reach the migration step: {offenders}. Migrating on boot "
        "means migrating once per replica, racing the others, with the service's own "
        "privileges."
    )


def test_no_application_module_imports_a_database_driver():
    """The one driver import in this repository is at its point of use in db/migrate.py."""
    package = ROOT / "src" / "crash_detector"
    offenders = [
        str(path.relative_to(package))
        for path in sorted(package.rglob("*.py"))
        if re.search(r"^\s*(import|from)\s+psycopg2", path.read_text(encoding="utf-8"), re.M)
    ]
    assert offenders == []


# --- SIX SCHEMAS, SIX ROLES, NO PASSWORD ------------------------------------------------- #

@pytest.mark.parametrize("schema", EXPECTED_SCHEMAS)
def test_each_of_the_six_schemas_is_created(schema: str):
    assert f"CREATE SCHEMA IF NOT EXISTS {schema};" in ALL_SQL


def test_no_seventh_application_schema_is_created():
    created = set(re.findall(r"CREATE SCHEMA IF NOT EXISTS (\w+);", ALL_SQL))
    assert created == set(EXPECTED_SCHEMAS)


@pytest.mark.parametrize("role", EXPECTED_ROLES)
def test_each_of_the_six_roles_is_created(role: str):
    assert f"'{role}'" in SQL_BY_NAME["schemas_roles_and_revoke_by_default"]


def test_the_roles_are_created_without_passwords():
    """PBG-SEC-002, non-waivable. A password in a migration is a secret in Git, and a
    secret that was ever committed is compromised regardless of any later deletion.
    """
    forbidden = re.compile(
        r"(CREATE|ALTER)\s+ROLE[^;]*\bPASSWORD\b", re.IGNORECASE | re.DOTALL
    )
    for migration in MIGRATIONS:
        # Comments explain that the deploy step sets passwords; the check must look at
        # STATEMENTS, so comment lines are removed before it runs.
        statements = "\n".join(
            line for line in migration.sql.splitlines() if not line.strip().startswith("--")
        )
        assert forbidden.search(statements) is None, migration.filename


def test_the_roles_are_created_with_no_privilege_escalating_attribute():
    sql = SQL_BY_NAME["schemas_roles_and_revoke_by_default"]
    for attribute in (
        "NOSUPERUSER",
        "NOCREATEDB",
        "NOCREATEROLE",
        "NOINHERIT",
        "NOREPLICATION",
        "NOBYPASSRLS",
    ):
        assert attribute in sql, attribute
    assert not re.search(r"\bWITH\s+SUPERUSER\b", sql, re.IGNORECASE)


def test_public_is_revoked_before_anything_is_granted():
    """PostgreSQL is not revoke-by-default out of the box.

    PUBLIC begins with USAGE on `public`, CONNECT and TEMP on the database, and EXECUTE on
    every function. Each is a route by which a role holds a privilege nobody granted by
    name — and the one that matters is cd_engine on schema witness.
    """
    sql = SQL_BY_NAME["schemas_roles_and_revoke_by_default"]
    for schema in EXPECTED_SCHEMAS:
        assert f"REVOKE ALL ON SCHEMA {schema}" in sql and "FROM PUBLIC" in sql, schema
    assert "REVOKE ALL ON SCHEMA public FROM PUBLIC;" in sql
    assert "REVOKE ALL ON DATABASE" in sql


# --- EVERY TIMESTAMP IS timestamptz (PBG-DATA-001) --------------------------------------- #

def test_no_column_is_declared_as_a_naive_timestamp():
    """A bare `timestamp` records an instant whose meaning depends on who reads it — the
    same defect crash_detector.time_utc refuses in the application.
    """
    offenders = []
    for migration in MIGRATIONS:
        for number, line in enumerate(migration.sql.splitlines(), start=1):
            if line.strip().startswith("--"):
                continue
            if re.search(r"\btimestamp\b(?!tz)", line) and "timestamptz" not in line:
                offenders.append(f"{migration.filename}:{number}: {line.strip()}")
    assert offenders == [], f"naive timestamp columns: {offenders}"


def test_every_time_bearing_column_uses_timestamptz():
    utc_columns = re.findall(
        r"^\s+(\w*_utc)\s+([a-z]\w*)", _statements_only(ALL_SQL), re.MULTILINE
    )
    assert utc_columns, "the scan found no timestamp columns and would pass vacuously"
    for name, declared_type in utc_columns:
        assert declared_type.strip() == "timestamptz", f"{name} is {declared_type!r}"


def test_the_database_timezone_is_pinned_to_utc():
    assert "ALTER DATABASE %I SET timezone TO %L" in ALL_SQL
    assert "'UTC'" in SQL_BY_NAME["schemas_roles_and_revoke_by_default"]


# --- raw.observation: THE FOUR OUTCOMES, AND WHAT MUST NOT BE STORED --------------------- #

@pytest.mark.parametrize(
    "table_sql_name",
    ["raw_source_registry_and_observations", "witness_observations"],
)
def test_the_outcome_check_admits_exactly_the_four_declared_classes(table_sql_name: str):
    """crash_detector.observations.OUTCOME_CLASSES. FOUR, not three.

    MALFORMED and EMPTY are different facts and neither is FETCH_FAILED; collapsing them
    is the failure BLUEPRINT §5 exists to prevent.
    """
    sql = SQL_BY_NAME[table_sql_name]
    admitted = _quoted_list(sql, "CHECK (outcome IN")
    assert tuple(admitted) == OUTCOME_CLASSES


def test_the_criticality_check_admits_exactly_the_declared_names():
    """crash_detector.source_registry.CRITICALITY_NAMES."""
    sql = SQL_BY_NAME["raw_source_registry_and_observations"]
    admitted = _quoted_list(sql, "CHECK (criticality IN")
    assert tuple(admitted) == CRITICALITY_NAMES


def test_the_instance_path_bound_is_the_one_the_type_enforces():
    """MAX_INSTANCE_PATH_LENGTH. Two constants that must agree is one constant with a bug."""
    sql = SQL_BY_NAME["raw_source_registry_and_observations"]
    assert f"length(instance_path) <= {MAX_INSTANCE_PATH_LENGTH}" in sql
    assert f"length(instance_path) <= {MAX_INSTANCE_PATH_LENGTH}" in (
        SQL_BY_NAME["witness_observations"]
    )


def test_http_status_is_nullable_and_never_defaults_to_zero():
    """A zero status would sort, compare and aggregate alongside real statuses."""
    for name in ("raw_source_registry_and_observations", "witness_observations"):
        sql = SQL_BY_NAME[name]
        assert re.search(r"http_status\s+integer,", sql), name
        assert "http_status IS NULL OR (http_status BETWEEN 100 AND 599)" in sql, name
        assert not re.search(r"http_status\s+integer[^,]*DEFAULT", sql), name


def test_source_as_of_utc_is_null_for_every_non_ok_outcome():
    for name in ("raw_source_registry_and_observations", "witness_observations"):
        coherence = SQL_BY_NAME[name]
        for outcome in ("FETCH_FAILED", "MALFORMED", "EMPTY"):
            branch = coherence.split(f"WHEN '{outcome}' THEN")[1].split("WHEN")[0]
            assert "source_as_of_utc   IS NULL" in branch, f"{name}/{outcome}"
        ok_branch = coherence.split("WHEN 'OK' THEN")[1].split("WHEN")[0]
        assert "source_as_of_utc   IS NOT NULL" in ok_branch, name


def test_the_outcome_coherence_check_has_no_fall_through():
    """An unrecognised outcome is refused, and in particular is never treated as OK."""
    for name in ("raw_source_registry_and_observations", "witness_observations"):
        assert "ELSE false" in SQL_BY_NAME[name], name


#: Columns whose ABSENCE is the deliverable. Increment 2 removed free-text detail and
#: payload-excerpt fields from the observation record because they are a secret
#: exfiltration path into an append-only store that carries no DELETE grant: a source
#: echoes a credential back inside the value that failed validation, and jsonschema's own
#: messages embed the offending instance value.
FORBIDDEN_OBSERVATION_COLUMNS = (
    "detail",
    "message",
    "error_message",
    "payload_excerpt",
    "excerpt",
    "response_body",
    "raw_response",
    "body",
    "sample",
)


@pytest.mark.parametrize("column", FORBIDDEN_OBSERVATION_COLUMNS)
def test_no_observation_table_carries_a_free_text_detail_or_payload_excerpt(column: str):
    for name in ("raw_source_registry_and_observations", "witness_observations"):
        sql = SQL_BY_NAME[name]
        table = sql.split("CREATE TABLE")[
            2 if name == "raw_source_registry_and_observations" else 1
        ]
        table = table.split(");")[0]
        assert not re.search(rf"^\s+{column}\s+\w", table, re.MULTILINE), (
            f"{name} declares a {column!r} column on an observation table"
        )


# --- APPEND-ONLY, AND THE TWO DIFFERENT UNIQUENESS RULES --------------------------------- #

def test_the_attempt_log_carries_no_unique_constraint_on_the_source_period():
    """Deduplicating attempts would erase the failure count, and the count of failed
    attempts is exactly what tells an operator a source is dying.
    """
    for name, table in (
        ("raw_source_registry_and_observations", "raw.observation"),
        ("witness_observations", "witness.observation"),
    ):
        sql = _statements_only(SQL_BY_NAME[name])
        observation = sql.split(f"CREATE TABLE {table}")[1].split("CREATE TABLE")[0]
        assert "UNIQUE" not in observation, (
            f"{name}: a unique constraint on the attempt log deduplicates failures out "
            "of the record"
        )


def test_the_reading_table_is_unique_on_the_source_period():
    """`INSERT ... ON CONFLICT DO NOTHING` plus the row count is exactly the contract of
    crash_detector.collectors.attempt.ReadingLedger.admit_if_absent.
    """
    assert "UNIQUE (source_id, source_as_of_utc)" in (
        SQL_BY_NAME["raw_source_registry_and_observations"]
    )
    assert "UNIQUE (source_id, source_as_of_utc)" in SQL_BY_NAME["witness_observations"]


def test_the_attempt_log_has_no_foreign_key_to_the_registry():
    """An FK there would let registry state veto the recording of an attempt, which is
    precisely the failure the append-only attempt log exists to prevent.
    """
    sql = _statements_only(SQL_BY_NAME["raw_source_registry_and_observations"])
    observation = sql.split("CREATE TABLE raw.observation")[1].split("CREATE TABLE")[0]
    assert "REFERENCES" not in observation


@pytest.mark.parametrize("table", APPEND_ONLY_TABLES)
def test_no_role_is_granted_update_or_delete_on_an_append_only_table(table: str):
    """BLUEPRINT §4, and the grant file must REVOKE them rather than merely omit them."""
    grants = SQL_BY_NAME["grant_matrix"]
    assert table in grants
    assert "REVOKE UPDATE, DELETE, TRUNCATE ON %s FROM %I" in grants
    for statement in re.findall(r"^GRANT\s+([A-Z, ]+)\s+ON\s+(\S+)", grants, re.MULTILINE):
        privileges, target = statement
        if target == table:
            assert "UPDATE" not in privileges and "DELETE" not in privileges, statement


def test_no_grant_anywhere_confers_update_delete_or_truncate():
    """Stated over the WHOLE grant file, so a fifth append-only table added later is
    covered by the same line rather than needing a new one.
    """
    for privileges, target in re.findall(
        r"^GRANT\s+([A-Z, ]+?)\s+ON\s+(\S+)", SQL_BY_NAME["grant_matrix"], re.MULTILINE
    ):
        forbidden = {"UPDATE", "DELETE", "TRUNCATE", "ALL"} & {
            token.strip() for token in privileges.split(",")
        }
        assert not forbidden, f"GRANT {privileges} ON {target} confers {forbidden}"


def test_first_published_utc_cannot_be_moved():
    """CD-AC-010. Defended twice: by the absence of any UPDATE grant, and by a trigger
    that also binds the table owner, whom grants do not constrain.
    """
    sql = SQL_BY_NAME["dial_history"]
    assert "first_published_utc timestamptz NOT NULL DEFAULT now()" in sql
    assert "CREATE FUNCTION dial.refuse_moving_first_published_utc()" in sql
    assert "BEFORE UPDATE ON dial.history" in sql
    assert "NEW.first_published_utc IS DISTINCT FROM OLD.first_published_utc" in sql


def test_the_immutability_trigger_catches_the_class_and_not_one_statement_shape():
    """`IS DISTINCT FROM` rather than `<>`, so a NULL on either side is still a change;
    FOR EACH ROW on any UPDATE, so a whole-row rewrite is caught as well as a targeted set.
    """
    sql = SQL_BY_NAME["dial_history"]
    assert "FOR EACH ROW" in sql
    assert "<> OLD.first_published_utc" not in sql


# --- THE DISPOSABLE PROHIBITION, DECLARATIVELY ------------------------------------------- #

def test_a_disposable_source_can_never_be_named_in_a_required_input_set():
    """BLUEPRINT §5, enforced by a composite FK rather than a trigger.

    The referencing criticality column is pinned to 'REQUIRED' by CHECK, and the FK
    resolves against (source_id, criticality) in the registry. The only rows that can
    exist are rows whose source is registered REQUIRED — there is no window in which the
    pair is inconsistent and nothing to disable.
    """
    sql = SQL_BY_NAME["raw_source_registry_and_observations"]
    assert "UNIQUE (source_id, criticality)" in sql
    assert "CHECK (criticality = 'REQUIRED')" in sql
    assert "CHECK (criticality = 'CONTRIBUTING')" in sql
    assert "FOREIGN KEY (source_id, criticality)" in sql
    assert "REFERENCES raw.source_registry (source_id, criticality)" in sql


def test_the_criticality_foreign_key_also_refuses_a_demotion():
    """ON UPDATE RESTRICT closes the other direction: a load-bearing source cannot be
    quietly re-registered DISPOSABLE while a dial still requires it.
    """
    sql = SQL_BY_NAME["raw_source_registry_and_observations"]
    assert sql.count("ON UPDATE RESTRICT") >= 2


def test_no_source_row_is_seeded():
    """WO-2 registers ZERO sources. CD-D-005 is the Product Owner's and is owed.

    With nothing registered every dial correctly reads UNKNOWN, which is the doctrinally
    right empty state and the thing that makes CD-AC-001's first plant demonstrable.
    """
    inserts = re.findall(r"^\s*INSERT\s+INTO\s+(\S+)", ALL_SQL, re.MULTILINE | re.IGNORECASE)
    assert inserts == [], f"the migrations seed rows: {inserts}"


# --- THE STORE HOLDS THE CLOSED ENVELOPE A SECOND TIME ----------------------------------- #

@pytest.mark.parametrize(
    "contract,table",
    [
        ("public_envelope.schema.json", "public_envelope"),
        ("private_envelope.schema.json", "private_envelope"),
    ],
)
def test_the_envelope_key_allowlist_matches_its_closed_schema(contract: str, table: str):
    """Two independent statements of the same allowlist must agree.

    The JSON Schema validates the whole document in the process that builds it; the CHECK
    refuses a top-level key at the point of writing, whatever wrote it and whether or not
    it remembered to validate. Drift between them is a failing test here rather than a
    discovery in production.
    """
    schema = json.loads((CONTRACTS_DIR / contract).read_text(encoding="utf-8"))
    declared = sorted(schema["properties"])

    sql = SQL_BY_NAME["publication"]
    block = sql.split(f"CONSTRAINT {table}_keys_are_an_allowlist")[1].split("),")[0]
    allowlisted = sorted(re.findall(r"'([a-z_]+)'", block))
    assert allowlisted == declared


@pytest.mark.parametrize(
    "contract,table",
    [
        ("public_envelope.schema.json", "public_envelope"),
        ("private_envelope.schema.json", "private_envelope"),
    ],
)
def test_the_required_honesty_fields_match_the_schema(contract: str, table: str):
    schema = json.loads((CONTRACTS_DIR / contract).read_text(encoding="utf-8"))
    sql = SQL_BY_NAME["publication"]
    block = sql.split(f"CONSTRAINT {table}_honesty_fields_present")[1].split("),")[0]
    required = sorted(re.findall(r"'([a-z_]+)'", block))
    assert required == sorted(schema["required"])


def test_no_table_in_the_store_can_hold_a_combined_dial_number():
    """CD-AC-002. There is no column named for a blend, and no table with a column per
    dial: a row shape carrying both dials side by side is one `+` away from a headline.
    """
    statements = _statements_only(ALL_SQL)
    for forbidden in ("combined", "overall", "blended", "composite", "aggregate_score"):
        for number, line in enumerate(statements.splitlines(), start=1):
            assert forbidden not in line.lower(), f"line {number}: {line.strip()}"


def test_the_dial_history_is_keyed_by_dial_and_not_shaped_with_one_column_per_dial():
    sql = SQL_BY_NAME["dial_history"]
    admitted = _quoted_list(sql, "CHECK (dial_id IN")
    assert tuple(admitted) == DIAL_IDS
    for dial_id in DIAL_IDS:
        assert f"{dial_id} " not in sql.split("CREATE TABLE dial.history")[1].split(");")[0]


def test_an_unknown_dial_reading_cannot_carry_a_score():
    """CD-AC-001, held in the store as it is held in the closed schema: UNKNOWN declares
    no score, so an unknown dial carrying a number is unrepresentable.
    """
    sql = SQL_BY_NAME["dial_history"]
    unknown = sql.split("WHEN 'UNKNOWN' THEN")[1].split("ELSE")[0]
    assert "score          IS NULL" in unknown
    assert "reason         IS NOT NULL" in unknown


def test_a_score_cannot_be_nan_or_infinite():
    """NaN is a double precision value, sorts above everything, and would render.

    Written as `<> 'NaN'::float8`, NOT as `score = score`. PostgreSQL departs from IEEE
    754 and holds NaN = NaN TRUE, so the idiomatic self-comparison ADMITS NaN. The first
    version of this constraint used it, and a live catalogue accepted the row — recorded
    as CD-ENG-F20 and corrected here.
    """
    sql = _statements_only(SQL_BY_NAME["dial_history"])
    assert "score <> 'NaN'::float8" in sql
    assert "'Infinity'::float8" in sql
    assert "score = score" not in sql


def test_no_constraint_anywhere_uses_the_self_comparison_that_admits_nan():
    """The CLASS of the defect, not the one instance the live run happened to find.

    A `x = x` guard is a NaN check that does not check, everywhere in this store, and it
    reads as correct to anyone who knows IEEE 754 and not PostgreSQL.
    """
    import re as _re

    statements = _statements_only(ALL_SQL)
    for match in _re.finditer(r"(?<![\w'])(\w+)\s*=\s*(\w+)(?![\w'])", statements):
        assert match.group(1) != match.group(2), (
            f"self-comparison {match.group(0)!r}: in PostgreSQL this is TRUE for NaN and "
            "therefore admits it"
        )


# --- THE WITNESS PANEL: UNAVAILABLE IS NOT AGREEMENT ------------------------------------- #

def test_the_panel_states_match_the_declared_sum_type():
    admitted = _quoted_list(SQL_BY_NAME["publication"], "CHECK (panel_state IN")
    assert tuple(admitted) == PANEL_STATES


def test_the_unavailable_reasons_match_the_declared_ones():
    """Every route to unavailability is named, so a new route cannot be added without
    naming it first.
    """
    sql = SQL_BY_NAME["publication"]
    block = sql.split("witness_panel_unavailable_reason_admitted")[1].split(
        "CONSTRAINT witness_panel_state_fields_coherent"
    )[0]
    reasons = set(re.findall(r"'([A-Z_]+)'", block))
    assert reasons - {"UNAVAILABLE"} == set(UNAVAILABLE_REASONS)


def test_agreement_requires_a_measurement():
    """CD-AC-005. There is no row shape in which AGREES has no divergence measure, so
    absence cannot be written as agreement even by an INSERT that bypasses the application.
    """
    sql = SQL_BY_NAME["publication"]
    agrees = sql.split("WHEN 'AGREES' THEN")[1].split("WHEN")[0]
    assert "divergence_measure IS NOT NULL" in agrees
    unavailable = sql.split("WHEN 'UNAVAILABLE' THEN")[1].split("ELSE")[0]
    assert "divergence_measure IS NULL" in unavailable


def test_the_review_table_declares_no_numeric_dial_column():
    """BLUEPRINT §9: there is nothing here for a headline number to be written into."""
    sql = SQL_BY_NAME["publication"]
    review = sql.split("CREATE TABLE publication.review")[1].split(");")[0]
    for numeric in ("double precision", "numeric", "real", "float"):
        assert numeric not in review, f"publication.review declares a {numeric} column"


# --- NO SECRET VALUE ANYWHERE IN THE MIGRATIONS (PBG-SEC-002) ---------------------------- #

def test_no_migration_contains_anything_shaped_like_a_credential():
    suspicious = re.compile(
        r"(password|passwd|secret|api[_-]?key|token)\s*(=|:=|=>)\s*'[^']+'",
        re.IGNORECASE,
    )
    for migration in MIGRATIONS:
        statements = "\n".join(
            line
            for line in migration.sql.splitlines()
            if not line.strip().startswith("--")
        )
        assert suspicious.search(statements) is None, migration.filename


def test_the_secret_scan_would_catch_one():
    """PBG-ASSURE-017. The planted string is obviously not a credential."""
    suspicious = re.compile(
        r"(password|passwd|secret|api[_-]?key|token)\s*(=|:=|=>)\s*'[^']+'",
        re.IGNORECASE,
    )
    assert suspicious.search("ALTER ROLE cd_engine PASSWORD = 'PLANTED-NOT-A-CREDENTIAL';")
