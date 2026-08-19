"""The grant matrix: SQL and declaration must say the same thing — BLUEPRINT §4, A5.

THREE THINGS MUST AGREE, AND THIS FILE COMPARES TWO OF THEM.

    1. db/migrations/0007_grant_matrix.sql   what is written
    2. db/grant_matrix.json                  what is declared
    3. the live catalogue of a built store   what is TRUE

This module parses (1) and compares it with (2). The comparison with (3) is a register
check against a store built from the migrations, and an INDEPENDENT Assurance seat builds
its own store and reads the catalogue itself. Neither substitutes for the other: a live
catalogue cannot tell you whether the matrix matches the Blueprint, and a text comparison
cannot tell you whether PostgreSQL agreed with what it was told.

The parser here is STRICT. A ``GRANT`` line it cannot parse fails the test rather than
being skipped — a grant nobody could read is exactly the one worth reading.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest

from crash_detector.store.migrations import load_migrations

ROOT = pathlib.Path(__file__).resolve().parents[1]
DECLARATION_PATH = ROOT / "db" / "grant_matrix.json"

DECLARATION = json.loads(DECLARATION_PATH.read_text(encoding="utf-8"))
GRANT_SQL = next(
    migration.sql
    for migration in load_migrations(ROOT / "db" / "migrations")
    if migration.name == "grant_matrix"
)

_GRANT_SCHEMA = re.compile(
    r"^GRANT\s+(?P<privileges>[A-Z, ]+?)\s+ON\s+SCHEMA\s+(?P<schema>\w+)\s+TO\s+(?P<role>\w+);",
    re.MULTILINE,
)
_GRANT_TABLE = re.compile(
    r"^GRANT\s+(?P<privileges>[A-Z, ]+?)\s+ON\s+(?P<table>\w+\.\w+)\s+TO\s+(?P<role>\w+);",
    re.MULTILINE,
)
_ANY_GRANT = re.compile(r"^GRANT\b.*$", re.MULTILINE)
_DEFAULT_PRIVILEGES = re.compile(
    r"^ALTER DEFAULT PRIVILEGES\s+IN SCHEMA\s+(?P<schema>\w+)\s+"
    r"GRANT\s+(?P<privileges>[A-Z, ]+?)\s+ON\s+(?P<objects>\w+)\s+TO\s+(?P<role>\w+);",
    re.MULTILINE,
)


def _statements_only(sql: str) -> str:
    return "\n".join(
        line for line in sql.splitlines() if not line.strip().startswith("--")
    )


STATEMENTS = _statements_only(GRANT_SQL)


def _parsed_schema_usage() -> dict[str, set[str]]:
    usage: dict[str, set[str]] = {}
    for match in _GRANT_SCHEMA.finditer(STATEMENTS):
        privileges = {token.strip() for token in match.group("privileges").split(",")}
        assert privileges == {"USAGE"}, (
            f"a schema grant confers {privileges} rather than USAGE alone: "
            f"{match.group(0)}. CREATE on a schema lets a role add a table nobody "
            "reviewed, inside a boundary somebody drew."
        )
        usage.setdefault(match.group("role"), set()).add(match.group("schema"))
    return usage


def _parsed_table_privileges() -> dict[str, dict[str, set[str]]]:
    grants: dict[str, dict[str, set[str]]] = {}
    for match in _GRANT_TABLE.finditer(STATEMENTS):
        privileges = {token.strip() for token in match.group("privileges").split(",")}
        role = grants.setdefault(match.group("role"), {})
        role.setdefault(match.group("table"), set()).update(privileges)
    return grants


PARSED_SCHEMA_USAGE = _parsed_schema_usage()
PARSED_TABLE_PRIVILEGES = _parsed_table_privileges()


# --- THE PARSER MUST NOT SKIP ------------------------------------------------------------- #

def test_every_grant_statement_in_the_file_was_parsed():
    """PBG-CI-002: a precondition the check cannot meet is a failure, never a skip.

    A GRANT the parser did not understand is a privilege this test did not check, and a
    matrix test that silently ignores a grant is worse than no matrix test.
    """
    all_grants = {line.strip() for line in _ANY_GRANT.findall(STATEMENTS)}
    parsed = {
        match.group(0).strip()
        for match in list(_GRANT_SCHEMA.finditer(STATEMENTS))
        + list(_GRANT_TABLE.finditer(STATEMENTS))
    }
    # ALTER DEFAULT PRIVILEGES lines contain the word GRANT but are not GRANT statements.
    unparsed = {line for line in all_grants if line not in parsed}
    assert unparsed == set(), f"GRANT statements this test could not read: {unparsed}"


def test_the_parse_is_not_vacuous():
    assert len(PARSED_TABLE_PRIVILEGES) == 6
    assert sum(len(tables) for tables in PARSED_TABLE_PRIVILEGES.values()) >= 20


# --- SQL AND DECLARATION AGREE -------------------------------------------------------------- #

def test_the_declared_roles_are_the_six_in_the_blueprint():
    assert DECLARATION["roles"] == [
        "cd_collector",
        "cd_witness",
        "cd_engine",
        "cd_public",
        "cd_private",
        "cd_review",
    ]


def test_schema_usage_in_the_sql_matches_the_declaration():
    declared = {
        role: set(schemas) for role, schemas in DECLARATION["schema_usage"].items()
    }
    assert PARSED_SCHEMA_USAGE == declared


def test_table_privileges_in_the_sql_match_the_declaration():
    declared = {
        role: {table: set(privileges) for table, privileges in tables.items()}
        for role, tables in DECLARATION["table_privileges"].items()
    }
    assert PARSED_TABLE_PRIVILEGES == declared


def test_default_privileges_in_the_sql_match_the_declaration():
    parsed = [
        {
            "grantee": match.group("role"),
            "schema": match.group("schema"),
            "object_type": match.group("objects"),
            "privileges": sorted(
                token.strip() for token in match.group("privileges").split(",")
            ),
        }
        for match in _DEFAULT_PRIVILEGES.finditer(STATEMENTS)
    ]
    declared = [
        {
            "grantee": entry["grantee"],
            "schema": entry["schema"],
            "object_type": entry["object_type"],
            "privileges": sorted(entry["privileges"]),
        }
        for entry in DECLARATION["default_privileges"]
    ]
    assert parsed == declared


# --- ASYMMETRY 1: cd_engine HOLDS NOTHING ON witness (CD-AC-003) ---------------------------- #

def test_cd_engine_is_granted_nothing_at_all_in_schema_witness():
    """The load-bearing asymmetry, checked as a CLASS and not as one statement shape.

    Not "there is no GRANT SELECT ON witness.observation TO cd_engine" — that catches the
    instance. Every parsed grant to cd_engine is examined, and any whose object lies in
    schema witness fails, whatever the privilege and whatever the object.
    """
    for schema in PARSED_SCHEMA_USAGE.get("cd_engine", set()):
        assert schema != "witness", "cd_engine is granted USAGE on schema witness"
    for table in PARSED_TABLE_PRIVILEGES.get("cd_engine", {}):
        assert not table.startswith("witness."), (
            f"cd_engine is granted a privilege on {table}"
        )


def test_no_default_privilege_exists_that_would_reach_cd_engine():
    """ALTER DEFAULT PRIVILEGES is the route a direct-grant check does not look at.

    A default privilege grants nothing today and everything tomorrow, on the next table
    somebody adds. The only one in this store is cd_private in schema private.
    """
    for match in _DEFAULT_PRIVILEGES.finditer(STATEMENTS):
        assert match.group("role") != "cd_engine", match.group(0)
        assert match.group("schema") != "witness", match.group(0)


def test_no_default_privilege_exists_in_schema_witness_for_any_role():
    for match in _DEFAULT_PRIVILEGES.finditer(STATEMENTS):
        assert match.group("schema") != "witness"


def test_no_role_is_granted_membership_of_another_role():
    """Role membership is the route by which a privilege arrives without a grant.

    Every role is additionally NOINHERIT (migration 1), so even a membership granted by
    mistake is not exercised without an explicit SET ROLE. Two instruments, neither
    load-bearing alone.
    """
    membership = re.compile(
        r"^GRANT\s+(?!USAGE|SELECT|INSERT|UPDATE|DELETE|TRUNCATE|CONNECT|EXECUTE|ALL)"
        r"\w+\s+TO\s+\w+;",
        re.MULTILINE,
    )
    assert membership.search(STATEMENTS) is None
    # In STATEMENTS, not in the file: the header comment names the predefined roles in
    # order to say they are never granted, and a check that failed on the explanation of
    # a rule would be a check nobody can document around.
    assert "pg_read_all_data" not in STATEMENTS
    assert "pg_write_all_data" not in STATEMENTS


def test_the_refusal_is_written_explicitly_and_not_merely_omitted():
    """Stated so the posture converges rather than merely starting correct.

    A store migrated from a cluster where somebody had granted it by hand must end up in
    the right state, not preserve the defect because the file happened to say nothing.
    """
    assert "REVOKE ALL ON SCHEMA witness                FROM cd_engine;" in GRANT_SQL
    assert "REVOKE ALL ON ALL TABLES    IN SCHEMA witness FROM cd_engine;" in GRANT_SQL
    assert "REVOKE ALL ON ALL SEQUENCES IN SCHEMA witness FROM cd_engine;" in GRANT_SQL
    assert "REVOKE ALL ON ALL FUNCTIONS IN SCHEMA witness FROM cd_engine;" in GRANT_SQL


def test_the_class_guard_would_catch_a_variant_violation():
    """PBG-ASSURE-017, and the exact attack Assurance is instructed to try.

    The guard is proved against grants it has never seen: a column-level grant, a
    sequence grant, a schema USAGE, a privilege other than SELECT. Each is a DIFFERENT
    route to the same violation, and a guard that catches only the one planted instance
    has not been tested.
    """
    variants = [
        "GRANT USAGE ON SCHEMA witness TO cd_engine;",
        "GRANT SELECT ON witness.observation TO cd_engine;",
        "GRANT REFERENCES ON witness.reading TO cd_engine;",
        "GRANT TRIGGER ON witness.observation TO cd_engine;",
    ]
    for variant in variants:
        schema_hits = _GRANT_SCHEMA.finditer(variant)
        table_hits = _GRANT_TABLE.finditer(variant)
        caught = any(
            match.group("role") == "cd_engine" and match.group("schema") == "witness"
            for match in schema_hits
        ) or any(
            match.group("role") == "cd_engine"
            and match.group("table").startswith("witness.")
            for match in table_hits
        )
        assert caught, f"the guard did not catch {variant!r}"


# --- ASYMMETRY 2: THE ONE-WAY VALVE --------------------------------------------------------- #

def test_cd_witness_may_read_the_published_envelope():
    """Witnesses see the score AFTER it is published, because divergence detection needs
    both sides.
    """
    assert "SELECT" in PARSED_TABLE_PRIVILEGES["cd_witness"][
        "publication.public_envelope"
    ]


def test_cd_witness_holds_nothing_on_raw_or_dial():
    """It cannot influence a score."""
    assert "raw" not in PARSED_SCHEMA_USAGE["cd_witness"]
    assert "dial" not in PARSED_SCHEMA_USAGE["cd_witness"]
    for table in PARSED_TABLE_PRIVILEGES["cd_witness"]:
        assert not table.startswith(("raw.", "dial."))


def test_nothing_grants_the_engine_a_read_of_the_witness_pipeline_by_any_route():
    """The valve is one-way, stated from the other end as well."""
    for role, tables in PARSED_TABLE_PRIVILEGES.items():
        for table in tables:
            if table.startswith("witness."):
                assert role == "cd_witness", (
                    f"{role} is granted a privilege on {table}; schema witness is "
                    "cd_witness's alone (BLUEPRINT §4)"
                )


# --- THE PUBLIC SURFACE READS EXACTLY TWO TABLES (BLUEPRINT §3, separation 3) ---------------- #

def test_cd_public_reads_exactly_two_tables_and_holds_nothing_else():
    tables = PARSED_TABLE_PRIVILEGES["cd_public"]
    assert set(tables) == {
        "publication.public_envelope",
        "publication.witness_panel",
    }
    for privileges in tables.values():
        assert privileges == {"SELECT"}
    assert PARSED_SCHEMA_USAGE["cd_public"] == {"publication"}


def test_cd_public_cannot_reach_the_private_envelope():
    assert "publication.private_envelope" not in PARSED_TABLE_PRIVILEGES["cd_public"]
    for schema in ("dial", "raw", "private", "witness", "alert"):
        assert schema not in PARSED_SCHEMA_USAGE["cd_public"]


# --- THE REVIEW WRITES NO NUMBER (BLUEPRINT §9) --------------------------------------------- #

def test_cd_review_can_write_only_its_own_review_row():
    tables = PARSED_TABLE_PRIVILEGES["cd_review"]
    writable = {
        table for table, privileges in tables.items() if privileges - {"SELECT"}
    }
    assert writable == {"publication.review"}


def test_cd_review_holds_no_grant_on_a_dial_or_envelope_number():
    for table, privileges in PARSED_TABLE_PRIVILEGES["cd_review"].items():
        if table != "publication.review":
            assert privileges == {"SELECT"}, table
        assert not table.startswith("dial.")


# --- COLLECTORS FETCH AND RECORD; THEY NEVER COMPUTE ---------------------------------------- #

def test_no_collector_grant_would_let_it_write_a_conclusion():
    """BLUEPRINT §5. A collector holds nothing on dial.* or publication.*."""
    for table in PARSED_TABLE_PRIVILEGES["cd_collector"]:
        assert table.startswith("raw."), table
    assert PARSED_SCHEMA_USAGE["cd_collector"] == {"raw"}


def test_the_disclosed_deviation_is_recorded_rather_than_taken_quietly():
    """`INSERT on raw.*` read literally would include the two dial input-set tables.

    They are excluded, and the exclusion is disclosed in the declaration with its
    reasoning and the change that would reverse it. Implementation choices are this seat's;
    a conflict inside the Blueprint is the Project Lead's (PBG-AUTH-005).
    """
    deviations = {entry["id"] for entry in DECLARATION["disclosed_deviations"]}
    assert "CD-ENG-F17" in deviations
    excluded = next(
        entry for entry in DECLARATION["disclosed_deviations"]
        if entry["id"] == "CD-ENG-F17"
    )["excluded"]
    for table in excluded:
        assert table not in PARSED_TABLE_PRIVILEGES["cd_collector"]


def test_the_declaration_carries_no_status_like_key():
    """The matrix declares obligations, never results. Nothing in it may record a verdict."""
    forbidden = {
        "status",
        "result",
        "outcome",
        "verdict",
        "grade",
        "score",
        "disposition",
        "passed",
        "failed",
    }

    def walk(node: object, pointer: str = "") -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                assert key.lower() not in forbidden, f"{pointer}/{key}"
                walk(value, f"{pointer}/{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{pointer}/{index}")

    walk(DECLARATION)


@pytest.mark.parametrize(
    "invariant_id",
    ["CD-GM-001", "CD-GM-002", "CD-GM-003", "CD-GM-004", "CD-GM-005", "CD-GM-006", "CD-GM-007"],
)
def test_each_declared_invariant_is_present_for_the_live_check_to_read(invariant_id: str):
    """The live grant-matrix check (deliverable B1) reads these. They are declared here so
    the check has a specification rather than a habit, and so a route nobody thought of is
    a missing invariant rather than a silent gap.
    """
    assert invariant_id in {entry["id"] for entry in DECLARATION["invariants"]}


def test_the_cd_ac_003_invariant_enumerates_every_route_not_just_the_direct_grant():
    routes = next(
        entry for entry in DECLARATION["invariants"] if entry["id"] == "CD-GM-001"
    )["routes_that_must_all_be_checked"]
    joined = " ".join(routes).lower()
    for route in ("public", "membership", "default", "ownership", "superuser", "column"):
        assert route in joined, f"the CD-AC-003 invariant does not name the {route} route"
