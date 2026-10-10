-- migration: 1
-- name: schemas_roles_and_revoke_by_default
-- rollback: NONE. This migration creates cluster-level roles and database-level schemas.
--   Dropping a role that owns or is referenced by objects is not a safe automated
--   reversal, and dropping a schema destroys durable data. Recovery from a bad apply is
--   by restoring the store from its dump (BLUEPRINT §12), not by a down-migration.
--   Migrations in this project are append-only and forward-only (PBG-DATA-002).
--
-- BLUEPRINT §4. Six schemas, six roles, and REVOKE BY DEFAULT before any grant exists.
--
-- WHY THE REVOKES COME FIRST AND ARE STATED RATHER THAN ASSUMED.
--
-- PostgreSQL is not revoke-by-default out of the box. The pseudo-role PUBLIC begins with
-- USAGE on schema `public`, CONNECT and TEMP on the database, and EXECUTE on every
-- function created in any schema it can reach. Every one of those is a route by which a
-- role could hold a privilege nobody granted it by name. CD-AC-003 says `cd_engine` holds
-- NO grant of any kind on `witness.*`; a posture that only avoids writing
-- `GRANT ... TO cd_engine` does not establish that, because the privilege can arrive
-- through PUBLIC, through role membership, through a default privilege, or through
-- ownership.
--
-- The enumerated routes, each closed here or in 0007:
--   1. a direct grant on the schema or a table  -> never written; revoked explicitly (0007)
--   2. a grant to PUBLIC                        -> revoked here and in 0007
--   3. membership of a role that holds it       -> no role is granted membership of any
--                                                  other role, and every role is NOINHERIT
--   4. ownership of the schema or its objects   -> every object is owned by the migrator;
--                                                  no application role owns anything
--   5. ALTER DEFAULT PRIVILEGES                 -> none is created for cd_engine anywhere,
--                                                  and none at all in schema witness (0007)
--   6. the SUPERUSER / BYPASSRLS attributes     -> every role is NOSUPERUSER NOBYPASSRLS
--   7. a predefined role such as pg_read_all_data -> never granted (see 3)
--
-- Each of those is read back out of the live catalogue as implementation evidence, and
-- the independent Assurance seat is expected to attack every one of them again.

-- --------------------------------------------------------------------------------------
-- Timestamps. BLUEPRINT §4, PBG-DATA-001: every timestamp is UTC.
-- --------------------------------------------------------------------------------------
-- Every timestamp column in this store is `timestamptz`. A bare `timestamp` would record
-- an instant whose meaning depends on whoever reads it, which is the same defect as a
-- naive datetime in the application (see crash_detector.time_utc, which refuses one).
--
-- The database timezone is pinned to UTC so that a session which does not set its own
-- renders UTC rather than the server's locale. The canonical ISO-8601 string with an
-- explicit `Z` is produced by `crash_detector.time_utc.format_utc` on the application
-- side, and in SQL by
--     to_char(ts AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
-- PostgreSQL's own default rendering of a timestamptz is `+00`, not `Z`; the explicit `Z`
-- is a property of the wire format this project emits, and the column type is what makes
-- that rendering unambiguous.
DO $$
BEGIN
    EXECUTE format('ALTER DATABASE %I SET timezone TO %L', current_database(), 'UTC');
END
$$;

SET timezone TO 'UTC';

-- --------------------------------------------------------------------------------------
-- The six schemas. BLUEPRINT §4.
-- --------------------------------------------------------------------------------------
-- Owned by the role running this migration — the migrator, which is NOT any of the six
-- application roles. Ownership is route 4 above: an application role that owned a schema
-- would hold every privilege on it regardless of the grant matrix.
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS witness;
CREATE SCHEMA IF NOT EXISTS dial;
CREATE SCHEMA IF NOT EXISTS publication;
CREATE SCHEMA IF NOT EXISTS private;
CREATE SCHEMA IF NOT EXISTS alert;

COMMENT ON SCHEMA raw IS
    'Ingredient observations, one row per fetch attempt including failures. Written by cd_collector, read by cd_engine (BLUEPRINT §4, §5).';
COMMENT ON SCHEMA witness IS
    'Witness observations. Written and read by cd_witness ONLY. cd_engine holds no grant of any kind here — CD-AC-003 (BLUEPRINT §4, §6).';
COMMENT ON SCHEMA dial IS
    'Computed dial readings and their history. Written by cd_engine, read by cd_engine and cd_private (BLUEPRINT §4, §7).';
COMMENT ON SCHEMA publication IS
    'The published artefacts: public_envelope, private_envelope, witness_panel, review, heartbeat (BLUEPRINT §4, §8).';
COMMENT ON SCHEMA private IS
    'Anything book-adjacent. Written and read by cd_private only (BLUEPRINT §4).';
COMMENT ON SCHEMA alert IS
    'Append-only alert events (BLUEPRINT §4, §10).';

-- --------------------------------------------------------------------------------------
-- REVOKE BY DEFAULT — the pseudo-role PUBLIC, before anything is granted by exception.
-- --------------------------------------------------------------------------------------
REVOKE ALL ON SCHEMA raw         FROM PUBLIC;
REVOKE ALL ON SCHEMA witness     FROM PUBLIC;
REVOKE ALL ON SCHEMA dial        FROM PUBLIC;
REVOKE ALL ON SCHEMA publication FROM PUBLIC;
REVOKE ALL ON SCHEMA private     FROM PUBLIC;
REVOKE ALL ON SCHEMA alert       FROM PUBLIC;

-- Schema `public` is NOT one of the six. It carries the migration ledger
-- (public.schema_migration, created by the migration runner, not by a migration — it must
-- exist before migration 1 can record itself) and nothing else. PUBLIC's inherited USAGE
-- on it is removed: this store addresses every object by qualified name, so nothing needs
-- an unqualified search path, and an unrevoked `public` is the classic place a table
-- appears that nobody meant to share.
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- CONNECT and TEMP on the database are PUBLIC by default. Removed, then granted by
-- exception to the six roles below. A role that cannot connect cannot reach anything,
-- which makes CONNECT the outermost ring of the same least-privilege argument.
DO $$
BEGIN
    EXECUTE format('REVOKE ALL ON DATABASE %I FROM PUBLIC', current_database());
END
$$;

-- --------------------------------------------------------------------------------------
-- The six roles. BLUEPRINT §4.
-- --------------------------------------------------------------------------------------
-- CREATED WITHOUT PASSWORDS, DELIBERATELY AND NON-NEGOTIABLY.
--
-- A password in a migration is a secret in Git, and a secret that was ever committed is
-- compromised regardless of any later deletion (PBG-SEC-002, PBG-EVID-003, non-waivable;
-- Standards Baseline §5). No governed record in this project carries a secret value.
--
-- A role created LOGIN with no password cannot authenticate under md5 or scram-sha-256:
-- authentication fails closed. The deploy step sets each password from the environment,
-- by env-var NAME, immediately after migration and outside version control:
--
--     ALTER ROLE cd_engine PASSWORD :'password';      -- value from $CD_STORE_ENGINE_PASSWORD
--
-- The env-var NAMES, and only the names, are:
--     CD_STORE_COLLECTOR_PASSWORD  CD_STORE_WITNESS_PASSWORD  CD_STORE_ENGINE_PASSWORD
--     CD_STORE_PUBLIC_PASSWORD     CD_STORE_PRIVATE_PASSWORD  CD_STORE_REVIEW_PASSWORD
--
-- Every role is NOINHERIT (route 3): even if a membership were granted by mistake, the
-- privileges of the granted role are not exercised without an explicit SET ROLE, so a
-- silent accumulation of privilege is not possible.
DO $$
DECLARE
    role_name text;
BEGIN
    FOREACH role_name IN ARRAY ARRAY[
        'cd_collector', 'cd_witness', 'cd_engine', 'cd_public', 'cd_private', 'cd_review'
    ]
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name) THEN
            EXECUTE format(
                'CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT '
                'NOREPLICATION NOBYPASSRLS',
                role_name
            );
        ELSE
            -- Idempotent, and it re-asserts the attributes rather than trusting whatever
            -- the role happens to carry. A role that acquired SUPERUSER between applies
            -- is exactly the drift this migration must not step over.
            EXECUTE format(
                'ALTER ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT '
                'NOREPLICATION NOBYPASSRLS',
                role_name
            );
        END IF;
        EXECUTE format(
            'GRANT CONNECT ON DATABASE %I TO %I', current_database(), role_name
        );
    END LOOP;
END
$$;

COMMENT ON ROLE cd_collector IS 'Fetches and records ingredient observations. Never computes (BLUEPRINT §5).';
COMMENT ON ROLE cd_witness   IS 'Fetches witness observations and builds the witness panel. No grant on raw.* or dial.* — it cannot influence a score (BLUEPRINT §4, §6).';
COMMENT ON ROLE cd_engine    IS 'The only writer of dial numbers. NO GRANT OF ANY KIND on schema witness — CD-AC-003 (BLUEPRINT §4).';
COMMENT ON ROLE cd_public    IS 'Serves the public market read. SELECT on exactly two publication tables (BLUEPRINT §3.3).';
COMMENT ON ROLE cd_private   IS 'Serves the private drill-down and anything book-adjacent (BLUEPRINT §3, §4).';
COMMENT ON ROLE cd_review    IS 'Runs the one AI review. No INSERT or UPDATE on any dial or envelope number (BLUEPRINT §9).';
