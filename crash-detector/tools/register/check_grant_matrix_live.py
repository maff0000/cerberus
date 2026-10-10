#!/usr/bin/env python3
"""CD-RT-003-GRANT-MATRIX-LIVE — the grant matrix, read out of a LIVE catalogue.

    python3 tools/register/check_grant_matrix_live.py --root <subject tree>

with the connection target supplied in the environment BY NAME:

    CD_CHECK_STORE_HOST      e.g. 127.0.0.1
    CD_CHECK_STORE_PORT      e.g. 5432
    CD_CHECK_STORE_NAME      the database to migrate and probe
    CD_CHECK_STORE_USER      a role that may CREATE ROLE and CREATE SCHEMA, and may read
                             pg_authid — see PRIVILEGES below
    CD_CHECK_STORE_PASSWORD  read by NAME at the point of use. Its VALUE is never printed,
                             logged or written anywhere by this script, and any occurrence
                             of it in an error message from the driver is redacted before
                             the message is shown (PBG-SEC-002, PBG-EVID-003, PBG-CONT-009,
                             all non-waivable).

WHY THIS CHECK EXISTS (CD-OB-003)
----------------------------------
Increment 3 proved the grant matrix against a live PostgreSQL catalogue under RT-A and
recorded 150 assertions with 0 failures. But its probe lived in ``/tmp``. So the criterion
had EVIDENCE and NO STANDING GUARD: reproducible in principle, and not runnable by anyone
who was not that seat. CD-OB-003 required it be promoted to a durable check an auditor can
run against a tree they extracted themselves. This is that check.

WHY A LIVE CATALOGUE AND NOT THE SQL TEXT. ``tests/test_grant_matrix_declaration.py``
already compares ``db/grant_matrix.json`` against the SQL by parsing it. Neither can tell
you whether PostgreSQL agreed with what it was told. A GRANT that was written and a GRANT
that is held are different facts, and CD-AC-003 — the product's most consequential
separation — rests on the second. Where the live catalogue and the migration text
disagree, the catalogue wins and the migration is wrong.

WHAT IT DOES
-------------
 1  Reads the migrations from the SUBJECT TREE (``<root>/db/migrations/*.sql``) and applies
    them in filename order, itself, with plain SQL. It deliberately does NOT go through
    ``db/migrate.py``: a check must not depend on the correctness of the thing it is
    checking, and a migration runner that silently skipped a file would produce a store
    that agreed with a matrix nobody applied.
 2  Reads the declaration from the SUBJECT TREE (``<root>/db/grant_matrix.json``).
 3  Reads the grants OUT OF THE LIVE CATALOGUE and asserts CD-GM-001 through CD-GM-007.

CD-GM-001 IS CHECKED ALONG ALL SEVEN ROUTES the declaration names, because "a check that
only looks for a direct GRANT catches the instance and not the class, and Assurance is
instructed to attack the other six": the schema privilege, table and column privileges,
sequence and function privileges, a grant to the pseudo-role PUBLIC that cd_engine would
inherit, membership of another role that holds one, a default privilege that would grant it
on a FUTURE object, ownership of the schema or anything in it, and the SUPERUSER /
BYPASSRLS role attributes. Then, independently of every catalogue query, it opens a session
as ``cd_engine`` and makes PostgreSQL itself refuse.

UNREACHABLE STORE = NON-ZERO WITH A STATED REASON. Never a skip, for any reason
(PBG-CI-002). That applies to an unset environment variable, an absent driver, a refused
connection, a failed migration and a subject tree with no migrations in it. A check that
skips when the store is down is a check that reports success on every host where nobody
started a database — which is most of them.

PRIVILEGES. The connection reads ``pg_authid`` to establish that the six roles carry no
password. A connection that cannot read it is REFUSED rather than allowed to report an
absence it did not observe: a check whose own privileges hide part of the catalogue is
reporting on its blind spot. In practice that means the cluster superuser, which is also
what applying the migrations needs.

EXIT: 0 clean · 1 violation, each named with its route · 2 usage · 3 precondition not met.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, resolve_root  # noqa: E402

CHECK_ID = "CD-RT-003-GRANT-MATRIX-LIVE"

REQUIRED_ENVIRONMENT = (
    "CD_CHECK_STORE_HOST",
    "CD_CHECK_STORE_PORT",
    "CD_CHECK_STORE_NAME",
    "CD_CHECK_STORE_USER",
    "CD_CHECK_STORE_PASSWORD",
)

ROLES = (
    "cd_collector",
    "cd_witness",
    "cd_engine",
    "cd_public",
    "cd_private",
    "cd_review",
)
SCHEMAS = ("raw", "witness", "dial", "publication", "private", "alert")
APPEND_ONLY = ("dial.history", "raw.observation", "witness.observation", "alert.event")
TABLE_PRIVILEGES = (
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "TRUNCATE",
    "REFERENCES",
    "TRIGGER",
)


def _redact(text: str, secret: str) -> str:
    """Never let a driver message carry a credential into stdout or a record."""
    if secret and secret in text:
        return text.replace(secret, "<REDACTED>")
    return text


class LiveGrants:
    def __init__(self, check: Check, connection) -> None:
        self.check = check
        self.connection = connection

    def scalar(self, sql, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return row[0] if row is not None else None

    def rows(self, sql, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    def assert_that(self, invariant: str, route: str, holds: bool, observed: str) -> None:
        self.check.asserted()
        if not holds:
            self.check.violation(
                pathlib.Path("<live catalogue>"),
                0,
                f"{invariant} route={route}",
                f"the LIVE catalogue contradicts {invariant}. Observed: {observed}",
            )

    # -- CD-GM-001: cd_engine holds nothing on schema witness, along all seven routes -- #
    def gm_001(self) -> None:
        for privilege in ("USAGE", "CREATE"):
            held = self.scalar(
                "SELECT has_schema_privilege('cd_engine', 'witness', %s)", (privilege,)
            )
            self.assert_that(
                "CD-GM-001",
                f"schema-privilege {privilege}",
                held is False,
                f"has_schema_privilege('cd_engine','witness','{privilege}') -> {held}",
            )

        objects = self.rows(
            "SELECT c.oid, c.relname, c.relkind FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'witness'"
        )
        self.assert_that(
            "CD-GM-001",
            "precondition: schema witness carries objects to test",
            len(objects) > 0,
            f"{len(objects)} objects in schema witness — an assertion about privileges on "
            "nothing is not an assertion",
        )
        for oid, relname, relkind in objects:
            if relkind in ("r", "p", "v", "m", "f"):
                for privilege in TABLE_PRIVILEGES:
                    held = self.scalar(
                        "SELECT has_table_privilege('cd_engine', %s::oid, %s)",
                        (oid, privilege),
                    )
                    self.assert_that(
                        "CD-GM-001",
                        f"table-privilege {privilege} ON witness.{relname}",
                        held is False,
                        f"has_table_privilege -> {held}",
                    )
            if relkind == "S":
                for privilege in ("USAGE", "SELECT", "UPDATE"):
                    held = self.scalar(
                        "SELECT has_sequence_privilege('cd_engine', %s::oid, %s)",
                        (oid, privilege),
                    )
                    self.assert_that(
                        "CD-GM-001",
                        f"sequence-privilege {privilege} ON witness.{relname}",
                        held is False,
                        f"has_sequence_privilege -> {held}",
                    )

        columns = self.rows(
            "SELECT table_name, column_name, privilege_type "
            "FROM information_schema.column_privileges "
            "WHERE table_schema = 'witness' AND grantee = 'cd_engine'"
        )
        self.assert_that(
            "CD-GM-001",
            "column-privilege",
            columns == [],
            f"information_schema.column_privileges -> {columns}",
        )

        functions = self.rows(
            "SELECT p.oid, p.proname FROM pg_proc p JOIN pg_namespace n "
            "ON n.oid = p.pronamespace WHERE n.nspname = 'witness'"
        )
        for oid, proname in functions:
            held = self.scalar(
                "SELECT has_function_privilege('cd_engine', %s::oid, 'EXECUTE')", (oid,)
            )
            self.assert_that(
                "CD-GM-001",
                f"function-privilege EXECUTE ON witness.{proname}",
                held is False,
                f"has_function_privilege -> {held}",
            )

        acls = self.rows(
            "SELECT nspname, nspacl::text FROM pg_namespace WHERE nspname = ANY(%s)",
            (list(SCHEMAS),),
        )
        public_grants = [
            (name, acl)
            for name, acl in acls
            if acl and any(item.startswith("=") for item in acl.strip("{}").split(","))
        ]
        self.assert_that(
            "CD-GM-001",
            "PUBLIC pseudo-role on any of the six schemas",
            public_grants == [],
            f"pg_namespace.nspacl entries with a leading '=' -> {public_grants}. A grant "
            "to PUBLIC is a grant cd_engine holds without ever being named.",
        )
        public_tables = self.rows(
            "SELECT table_name, privilege_type FROM information_schema.table_privileges "
            "WHERE table_schema = 'witness' AND grantee = 'PUBLIC'"
        )
        self.assert_that(
            "CD-GM-001",
            "PUBLIC table grants in schema witness",
            public_tables == [],
            f"information_schema.table_privileges grantee=PUBLIC -> {public_tables}",
        )

        memberships = self.rows(
            "SELECT r.rolname, m.rolname FROM pg_auth_members am "
            "JOIN pg_roles r ON r.oid = am.member "
            "JOIN pg_roles m ON m.oid = am.roleid WHERE r.rolname = ANY(%s)",
            (list(ROLES),),
        )
        self.assert_that(
            "CD-GM-001",
            "role membership (inherited grants)",
            memberships == [],
            f"pg_auth_members -> {memberships}. A role that is a member of another role "
            "holds that role's grants without holding one of its own.",
        )

        defaults = self.rows(
            "SELECT n.nspname, pg_get_userbyid(d.defaclrole), d.defaclobjtype, "
            "       d.defaclacl::text "
            "FROM pg_default_acl d LEFT JOIN pg_namespace n ON n.oid = d.defaclnamespace"
        )
        self.assert_that(
            "CD-GM-001",
            "default privilege in schema witness",
            [row for row in defaults if row[0] == "witness"] == [],
            f"pg_default_acl in witness -> {[r for r in defaults if r[0] == 'witness']}. "
            "A default privilege grants nothing today and everything on the next object "
            "created.",
        )
        self.assert_that(
            "CD-GM-001",
            "default privilege naming cd_engine anywhere",
            [row for row in defaults if "cd_engine" in (row[3] or "")] == [],
            f"pg_default_acl naming cd_engine -> "
            f"{[r for r in defaults if 'cd_engine' in (r[3] or '')]}",
        )

        owned_schemas = self.rows(
            "SELECT nspname, pg_get_userbyid(nspowner) FROM pg_namespace "
            "WHERE pg_get_userbyid(nspowner) = ANY(%s)",
            (list(ROLES),),
        )
        self.assert_that(
            "CD-GM-001",
            "ownership of a schema",
            owned_schemas == [],
            f"pg_namespace.nspowner -> {owned_schemas}. An owner needs no grant.",
        )

        attributes = self.rows(
            "SELECT rolname, rolsuper, rolbypassrls FROM pg_roles "
            "WHERE rolname = 'cd_engine'"
        )
        self.assert_that(
            "CD-GM-001",
            "SUPERUSER / BYPASSRLS attributes",
            attributes != [] and not attributes[0][1] and not attributes[0][2],
            f"pg_roles -> {attributes}. A superuser holds every privilege in the cluster "
            "and appears in no grant table at all.",
        )

    def gm_001_behavioural(self) -> None:
        """The catalogue says no. This makes PostgreSQL say no, in a session."""
        import psycopg2

        for statement in (
            "SELECT 1 FROM witness.observation LIMIT 1",
            "SELECT 1 FROM witness.reading LIMIT 1",
            "INSERT INTO witness.observation (source_id) VALUES ('probe')",
        ):
            with self.connection.cursor() as cursor:
                cursor.execute("SET LOCAL ROLE cd_engine")
                try:
                    cursor.execute(statement)
                except psycopg2.Error as exc:
                    self.assert_that(
                        "CD-GM-001",
                        f"live refusal: cd_engine `{statement}`",
                        exc.pgcode in ("42501", "3F000", "42P01"),
                        f"SQLSTATE {exc.pgcode} ({type(exc).__name__})",
                    )
                else:
                    self.assert_that(
                        "CD-GM-001",
                        f"live refusal: cd_engine `{statement}`",
                        False,
                        "THE STATEMENT SUCCEEDED — cd_engine reached schema witness in a "
                        "real session, whatever the catalogue tables say",
                    )
            self.connection.rollback()

    # -- CD-GM-002: the one-way valve --------------------------------------------------- #
    def gm_002(self) -> None:
        import psycopg2

        held = self.scalar(
            "SELECT has_table_privilege('cd_witness', 'publication.public_envelope', "
            "'SELECT')"
        )
        self.assert_that(
            "CD-GM-002",
            "cd_witness SELECT ON publication.public_envelope",
            held is True,
            f"has_table_privilege -> {held}. The valve must be OPEN in this direction: a "
            "witness that cannot see what was published cannot corroborate it.",
        )
        usage = self.scalar(
            "SELECT has_schema_privilege('cd_witness', 'publication', 'USAGE')"
        )
        self.assert_that(
            "CD-GM-002",
            "cd_witness USAGE ON SCHEMA publication",
            usage is True,
            f"has_schema_privilege -> {usage}. A table grant is useless without it.",
        )

        with self.connection.cursor() as cursor:
            cursor.execute("SET LOCAL ROLE cd_witness")
            try:
                cursor.execute("SELECT count(*) FROM publication.public_envelope")
                count = cursor.fetchone()[0]
            except psycopg2.Error as exc:
                self.assert_that(
                    "CD-GM-002",
                    "live: cd_witness reads the published envelope",
                    False,
                    f"REFUSED with SQLSTATE {exc.pgcode}",
                )
            else:
                self.assert_that(
                    "CD-GM-002",
                    "live: cd_witness reads the published envelope",
                    True,
                    f"SELECT succeeded, {count} rows",
                )
        self.connection.rollback()

        for schema in ("raw", "dial"):
            held = self.scalar(
                "SELECT has_schema_privilege('cd_witness', %s, 'USAGE')", (schema,)
            )
            self.assert_that(
                "CD-GM-002",
                f"cd_witness holds NO USAGE on schema {schema}",
                held is False,
                f"has_schema_privilege -> {held}. The valve must be SHUT in this "
                "direction: a witness that can reach the ingredients is an ingredient.",
            )
        leaks = self.rows(
            "SELECT table_schema, table_name, privilege_type "
            "FROM information_schema.table_privileges "
            "WHERE grantee = 'cd_witness' AND table_schema IN ('raw', 'dial')"
        )
        self.assert_that(
            "CD-GM-002",
            "cd_witness holds no table grant in raw.* or dial.*",
            leaks == [],
            f"information_schema.table_privileges -> {leaks}",
        )
        others = self.rows(
            "SELECT grantee, table_name, privilege_type "
            "FROM information_schema.table_privileges "
            "WHERE table_schema = 'witness' AND grantee = ANY(%s) "
            "  AND grantee <> 'cd_witness'",
            (list(ROLES),),
        )
        self.assert_that(
            "CD-GM-002",
            "schema witness is cd_witness's alone",
            others == [],
            f"information_schema.table_privileges -> {others}",
        )

    # -- CD-GM-003: nothing is mutable after the fact ------------------------------------ #
    def gm_003(self) -> None:
        for table in APPEND_ONLY:
            for role in ROLES:
                for privilege in ("UPDATE", "DELETE", "TRUNCATE"):
                    held = self.scalar(
                        "SELECT has_table_privilege(%s, %s, %s)",
                        (role, table, privilege),
                    )
                    self.assert_that(
                        "CD-GM-003",
                        f"{role} {privilege} ON {table}",
                        held is False,
                        f"has_table_privilege -> {held}",
                    )
        everywhere = self.rows(
            "SELECT grantee, table_schema, table_name, privilege_type "
            "FROM information_schema.table_privileges "
            "WHERE table_schema = ANY(%s) "
            "  AND privilege_type IN ('UPDATE', 'DELETE', 'TRUNCATE') "
            "  AND grantee = ANY(%s)",
            (list(SCHEMAS), list(ROLES) + ["PUBLIC"]),
        )
        self.assert_that(
            "CD-GM-003",
            "whole-store sweep for UPDATE/DELETE/TRUNCATE",
            everywhere == [],
            f"information_schema.table_privileges -> {everywhere}. TRUNCATE is in this "
            "sweep deliberately: a matrix that forbids DELETE and permits TRUNCATE "
            "forbids nothing.",
        )

    # -- CD-GM-004: the public surface sees two tables ------------------------------------ #
    def gm_004(self) -> None:
        granted = self.rows(
            "SELECT table_schema || '.' || table_name, privilege_type "
            "FROM information_schema.table_privileges WHERE grantee = 'cd_public'"
        )
        names = sorted({row[0] for row in granted})
        self.assert_that(
            "CD-GM-004",
            "cd_public reaches exactly two tables",
            names == ["publication.public_envelope", "publication.witness_panel"],
            f"cd_public holds table grants on {names}",
        )
        privileges = sorted({row[1] for row in granted})
        self.assert_that(
            "CD-GM-004",
            "and holds only SELECT on them",
            privileges in ([], ["SELECT"]),
            f"privilege types held by cd_public -> {privileges}",
        )
        for schema in ("dial", "raw", "private"):
            held = self.scalar(
                "SELECT has_schema_privilege('cd_public', %s, 'USAGE')", (schema,)
            )
            self.assert_that(
                "CD-GM-004",
                f"cd_public holds nothing on schema {schema}",
                held is False,
                f"has_schema_privilege -> {held}",
            )
        held = self.scalar(
            "SELECT has_table_privilege('cd_public', 'publication.private_envelope', "
            "'SELECT')"
        )
        self.assert_that(
            "CD-GM-004",
            "cd_public cannot read the private envelope",
            held is False,
            f"has_table_privilege -> {held}",
        )

    # -- CD-GM-005: the reviewer writes no number ------------------------------------------ #
    def gm_005(self) -> None:
        writes = self.rows(
            "SELECT table_schema || '.' || table_name, privilege_type "
            "FROM information_schema.table_privileges "
            "WHERE grantee = 'cd_review' AND privilege_type IN ('INSERT','UPDATE')"
        )
        offending = [row for row in writes if not row[0].endswith("publication.review")]
        self.assert_that(
            "CD-GM-005",
            "cd_review holds no INSERT or UPDATE on a dial or envelope table",
            offending == [],
            f"cd_review write grants -> {writes}",
        )
        # CD-GM-005's words are "no numeric DIAL column for a headline to be written
        # into" — a magnitude, not an identifier. So the rule is stated in two halves
        # rather than as "no number anywhere", which would condemn a surrogate key:
        #
        #   * a REAL-VALUED type (double precision, real, numeric) is forbidden outright.
        #     Those are the types a magnitude wears, and there is no honest reason for the
        #     reviewer's table to carry one.
        #   * an INTEGER type is permitted ONLY as an identifier, judged by an `_id` name.
        #     A scaled score stored as an integer is still a headline number, and
        #     `combined_stress bigint` fails here exactly as `combined_stress numeric`
        #     does.
        #
        # This is the shape of the invariant, not an exemption for the two columns that
        # happen to exist: publication.review carries review_id (an identity key) and
        # public_envelope_id (a foreign key), and both are identifiers by construction.
        real_valued = self.rows(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'publication' AND table_name = 'review' "
            "  AND data_type IN ('double precision','real','numeric')"
        )
        self.assert_that(
            "CD-GM-005",
            "publication.review declares no real-valued column",
            real_valued == [],
            f"real-valued columns on publication.review -> {real_valued}. A place to "
            "write a magnitude is an invitation to write one.",
        )
        integer_columns = self.rows(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'publication' AND table_name = 'review' "
            "  AND data_type IN ('integer','bigint','smallint')"
        )
        not_identifiers = [
            row for row in integer_columns if not str(row[0]).endswith("_id")
        ]
        self.assert_that(
            "CD-GM-005",
            "publication.review's integer columns are identifiers only",
            not_identifiers == [],
            f"integer columns that are not identifiers -> {not_identifiers} (all integer "
            f"columns: {integer_columns}). A scaled score stored as an integer is still a "
            "headline number the AI review would have authored.",
        )

    # -- CD-GM-006: role attributes ---------------------------------------------------------- #
    def gm_006(self) -> None:
        attributes = self.rows(
            "SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolinherit, "
            "       rolreplication, rolbypassrls FROM pg_roles "
            "WHERE rolname = ANY(%s) ORDER BY rolname",
            (list(ROLES),),
        )
        self.assert_that(
            "CD-GM-006",
            "all six roles exist",
            len(attributes) == len(ROLES),
            f"pg_roles -> {[row[0] for row in attributes]}",
        )
        for row in attributes:
            name = row[0]
            self.assert_that(
                "CD-GM-006",
                f"{name} is NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT "
                "NOREPLICATION NOBYPASSRLS",
                not any(row[1:]),
                f"pg_roles -> {row}",
            )
        memberships = self.rows(
            "SELECT r.rolname FROM pg_auth_members am "
            "JOIN pg_roles r ON r.oid = am.member WHERE r.rolname = ANY(%s)",
            (list(ROLES),),
        )
        self.assert_that(
            "CD-GM-006",
            "no application role is a member of any role",
            memberships == [],
            f"pg_auth_members -> {memberships}",
        )
        passworded = self.rows(
            "SELECT rolname FROM pg_authid WHERE rolname = ANY(%s) "
            "  AND rolpassword IS NOT NULL",
            (list(ROLES),),
        )
        self.assert_that(
            "CD-GM-006",
            "roles were created WITHOUT passwords (PBG-SEC-002)",
            passworded == [],
            f"pg_authid.rolpassword IS NOT NULL -> {passworded}. Passwords arrive from "
            "the environment at deploy, never from a migration.",
        )

    # -- CD-GM-007: ownership ------------------------------------------------------------------ #
    def gm_007(self) -> None:
        owned = self.rows(
            "SELECT n.nspname, c.relname, pg_get_userbyid(c.relowner) FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = ANY(%s) AND pg_get_userbyid(c.relowner) = ANY(%s)",
            (list(SCHEMAS), list(ROLES)),
        )
        self.assert_that(
            "CD-GM-007",
            "no application role owns a table, sequence or view",
            owned == [],
            f"pg_class.relowner -> {owned}. An owner holds every privilege on the object "
            "and can grant more, without appearing in any grant table.",
        )
        owned_functions = self.rows(
            "SELECT n.nspname, p.proname, pg_get_userbyid(p.proowner) FROM pg_proc p "
            "JOIN pg_namespace n ON n.oid = p.pronamespace "
            "WHERE n.nspname = ANY(%s) AND pg_get_userbyid(p.proowner) = ANY(%s)",
            (list(SCHEMAS), list(ROLES)),
        )
        self.assert_that(
            "CD-GM-007",
            "no application role owns a function",
            owned_functions == [],
            f"pg_proc.proowner -> {owned_functions}",
        )
        owners = self.rows(
            "SELECT DISTINCT pg_get_userbyid(c.relowner) FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = ANY(%s)",
            (list(SCHEMAS),),
        )
        self.assert_that(
            "CD-GM-007",
            "every object in the six schemas has ONE owner, the migrator",
            len(owners) == 1,
            f"distinct owners -> {sorted(row[0] for row in owners)}. More than one owner "
            "means the migration ran as more than one identity, and ownership is a "
            "privilege route the grant matrix does not describe.",
        )

    # -- the whole matrix, live against the declaration ------------------------------------- #
    def whole_matrix(self, declared: dict) -> None:
        live_usage: dict = {}
        for role in ROLES:
            for schema in SCHEMAS:
                if self.scalar(
                    "SELECT has_schema_privilege(%s, %s, 'USAGE')", (role, schema)
                ):
                    live_usage.setdefault(role, set()).add(schema)
        expected_usage = {
            role: set(schemas) for role, schemas in declared["schema_usage"].items()
        }
        self.assert_that(
            "WHOLE-MATRIX",
            "schema USAGE, live vs db/grant_matrix.json",
            live_usage == expected_usage,
            "live="
            + repr({k: sorted(v) for k, v in sorted(live_usage.items())})
            + " expected="
            + repr({k: sorted(v) for k, v in sorted(expected_usage.items())}),
        )

        live_tables: dict = {}
        for grantee, schema, table, privilege in self.rows(
            "SELECT grantee, table_schema, table_name, privilege_type "
            "FROM information_schema.table_privileges "
            "WHERE table_schema = ANY(%s) AND grantee = ANY(%s)",
            (list(SCHEMAS), list(ROLES)),
        ):
            live_tables.setdefault(grantee, {}).setdefault(
                f"{schema}.{table}", set()
            ).add(privilege)
        expected_tables = {
            role: {table: set(privileges) for table, privileges in tables.items()}
            for role, tables in declared["table_privileges"].items()
        }
        self.assert_that(
            "WHOLE-MATRIX",
            "table privileges, live vs db/grant_matrix.json",
            live_tables == expected_tables,
            "live="
            + repr(
                {
                    k: {t: sorted(p) for t, p in sorted(v.items())}
                    for k, v in sorted(live_tables.items())
                }
            ),
        )

        declared_defaults = declared.get("default_privileges", [])
        live_defaults = self.rows(
            "SELECT n.nspname, d.defaclacl::text FROM pg_default_acl d "
            "LEFT JOIN pg_namespace n ON n.oid = d.defaclnamespace"
        )
        self.assert_that(
            "WHOLE-MATRIX",
            "default privileges, live vs declaration",
            len(live_defaults) == len(declared_defaults),
            f"live pg_default_acl -> {live_defaults}; declared -> "
            f"{[entry.get('grantee') for entry in declared_defaults]}",
        )


def main() -> int:
    args = parse_root(CHECK_ID, __doc__)
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code

    check = Check(CHECK_ID, root)

    migrations_dir = root / "db" / "migrations"
    declaration_path = root / "db" / "grant_matrix.json"
    if not migrations_dir.is_dir():
        return check.refuse(f"{migrations_dir} does not exist in this subject tree.")
    if not declaration_path.is_file():
        return check.refuse(f"{declaration_path} does not exist in this subject tree.")

    migrations = sorted(migrations_dir.glob("*.sql"))
    if not migrations:
        return check.refuse(
            f"{migrations_dir} contains no .sql migrations. There is nothing to build a "
            "store from, and an empty migration set must not read as a clean grant matrix."
        )

    try:
        declared = json.loads(declaration_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return check.refuse(f"db/grant_matrix.json could not be read: {exc}")

    missing = [name for name in REQUIRED_ENVIRONMENT if not os.environ.get(name)]
    if missing:
        return check.refuse(
            "the connection target is not set: "
            + ", ".join(missing)
            + ". Connection details are supplied in the environment BY NAME; no value is "
            "ever written in this file or in any record. Unset means this check cannot "
            "reach a store, which is a non-zero exit and never a skip."
        )

    try:
        import psycopg2
        from psycopg2 import errors as _pg_errors  # noqa: F401
    except ImportError as exc:
        return check.refuse(
            f"the PostgreSQL driver is not importable ({exc}). This check reads a LIVE "
            "catalogue and there is no substitute for one. psycopg2 is a declared "
            "dependency of this project (requirements.txt); a host without it cannot run "
            "this check, and must be told so rather than shown a pass."
        )

    secret = os.environ["CD_CHECK_STORE_PASSWORD"]
    target = (
        f"{os.environ['CD_CHECK_STORE_USER']}@{os.environ['CD_CHECK_STORE_HOST']}:"
        f"{os.environ['CD_CHECK_STORE_PORT']}/{os.environ['CD_CHECK_STORE_NAME']}"
    )

    try:
        connection = psycopg2.connect(
            host=os.environ["CD_CHECK_STORE_HOST"],
            port=os.environ["CD_CHECK_STORE_PORT"],
            dbname=os.environ["CD_CHECK_STORE_NAME"],
            user=os.environ["CD_CHECK_STORE_USER"],
            password=secret,
            connect_timeout=15,
        )
    except psycopg2.Error as exc:
        return check.refuse(
            f"the store at {target} is UNREACHABLE: "
            f"{_redact(str(exc).strip(), secret)} "
            "(the credential is redacted from this message by construction). A check that "
            "cannot reach its subject reports that it could not, and never that the "
            "subject was clean."
        )

    try:
        # -- pg_authid readability: a blind spot must not read as an absence ----------- #
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM pg_authid")
        except psycopg2.Error as exc:
            connection.rollback()
            return check.refuse(
                f"this connection cannot read pg_authid (SQLSTATE {exc.pgcode}), so it "
                "cannot establish that the six roles carry no password. A check whose own "
                "privileges hide part of the catalogue reports on its blind spot. Connect "
                "as a role that can read it — in practice the cluster superuser, which is "
                "also what applying the migrations needs."
            )
        connection.rollback()

        # -- apply the migrations from the SUBJECT TREE -------------------------------- #
        for path in migrations:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(path.read_text(encoding="utf-8"))
                connection.commit()
            except psycopg2.Error as exc:
                connection.rollback()
                return check.refuse(
                    f"migration {path.name} from the subject tree FAILED to apply "
                    f"(SQLSTATE {exc.pgcode}): {_redact(str(exc).strip(), secret)}. The "
                    "store could not be built, so nothing about its grants has been "
                    "established. Note the store must be EMPTY: this check applies every "
                    "migration itself, deliberately not through db/migrate.py, because a "
                    "check must not depend on the correctness of the thing it checks."
                )

        version = None
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
        check.note(f"authentic target: {version}")
        check.note(f"authentic target: {target} (credential by env-var name only)")
        check.note(
            f"{len(migrations)} migrations applied from the subject tree, in filename "
            f"order: {', '.join(path.name for path in migrations)}"
        )

        live = LiveGrants(check, connection)
        live.gm_001()
        live.gm_001_behavioural()
        live.gm_002()
        live.gm_003()
        live.gm_004()
        live.gm_005()
        live.gm_006()
        live.gm_007()
        live.whole_matrix(declared)
        connection.rollback()
    finally:
        connection.close()

    return check.done(
        f"the LIVE catalogue of a store built from {len(migrations)} subject-tree "
        "migrations; CD-GM-001..007 plus the whole-matrix comparison"
    )


if __name__ == "__main__":
    raise SystemExit(main())
