-- migration: 7
-- name: grant_matrix
-- rollback: NONE as a migration. The grant matrix is nevertheless the one part of this
--   store that CAN be reversed safely by hand, because revoking a privilege destroys no
--   data: `REVOKE ALL ON ALL TABLES IN SCHEMA <s> FROM <role>` returns any role to the
--   revoke-by-default state established in migration 1. That is stated as an operational
--   fact, not offered as a down-migration; migrations here remain forward-only
--   (PBG-DATA-002).
--
-- BLUEPRINT §4, the grant matrix, implemented ROW BY ROW.
--
--   | Role         | Grants                                                          |
--   |--------------|-----------------------------------------------------------------|
--   | cd_collector | INSERT on raw.*; SELECT on raw.source_registry                   |
--   | cd_witness   | INSERT on witness.*, publication.witness_panel, alert.event;     |
--   |              | SELECT on witness.*, publication.public_envelope                 |
--   | cd_engine    | SELECT on raw.*; INSERT on dial.*, publication.public_envelope,  |
--   |              | publication.private_envelope, publication.heartbeat, alert.event |
--   | cd_public    | SELECT on publication.public_envelope, publication.witness_panel |
--   | cd_private   | SELECT on dial.*, publication.private_envelope, private.*,       |
--   |              | alert.event; INSERT on private.*                                 |
--   | cd_review    | SELECT on publication.public_envelope;                           |
--   |              | INSERT on publication.review                                     |
--
-- The same matrix is carried machine-readably in db/grant_matrix.json, and a test asserts
-- that this file and that file say the same thing by parsing the statements below. Three
-- things must agree: this SQL, that declaration, and the live catalogue. Assurance reads
-- the third independently.
--
-- ============================================================================
-- THE TWO LOAD-BEARING ASYMMETRIES. NOT SOFTENED, AND NOT PARAPHRASED.
-- ============================================================================
--
-- 1. cd_engine holds NO GRANT OF ANY KIND on witness.* — not USAGE on the schema, not
--    SELECT on a table, nothing. This is what makes CD-AC-003 true by construction rather
--    than by test. Without USAGE on the schema, cd_engine cannot so much as name an
--    object in it, whatever privileges might later be granted on a table by accident.
--
-- 2. cd_witness MAY SELECT publication.public_envelope — the one-way valve. Witnesses see
--    the score after it is published, because divergence detection needs both sides; the
--    score never sees the witnesses.
--
-- Asymmetry 1 is defended against a CLASS of routes, not against the single instance of
-- somebody typing `GRANT SELECT ON witness.observation TO cd_engine`. The routes and
-- their closures:
--
--   direct grant on a table/column  REVOKEd explicitly below, after the schema revoke
--   grant on the schema             never granted; REVOKEd explicitly below
--   a grant to PUBLIC               REVOKEd in migration 1 and again below, for tables,
--                                   sequences and functions
--   role membership                 no role is a member of any other; every role is
--                                   NOINHERIT (migration 1). No predefined role such as
--                                   pg_read_all_data is granted to anything.
--   ALTER DEFAULT PRIVILEGES        the ONLY default privileges in this store are for
--                                   cd_private in schema private (see the note below).
--                                   None exists in schema witness, for any role.
--   ownership                       every object is owned by the migrator. No application
--                                   role owns a schema, table, sequence or function.
--   role attributes                 every role is NOSUPERUSER NOBYPASSRLS (migration 1).
--
-- ============================================================================
-- ON `.*`, AND WHY THIS FILE PREFERS EXPLICIT PER-TABLE GRANTS
-- ============================================================================
--
-- `INSERT on raw.*` could be implemented with ALTER DEFAULT PRIVILEGES, so that a table
-- added by a future migration is automatically granted. That is the FAIL-OPEN direction:
-- a table nobody has thought about yet becomes writable by a role nobody re-examined.
-- For a matrix whose whole purpose is least privilege, the fail-closed direction is
-- right, so `.*` is implemented as explicit per-table grants and extending it is a
-- deliberate line in a future migration.
--
-- The single exception is schema `private`, which carries no table at all in WO-2 (see
-- migration 6). Its matrix row would otherwise be unimplemented, and a boundary that is
-- only implemented once there is something inside it is a boundary that gets retrofitted.
-- The default privilege there is confined to a schema on which cd_private holds the only
-- USAGE, so the fail-open surface is one role reaching tables in its own schema.
--
-- STATED LIMIT: ALTER DEFAULT PRIVILEGES applies to objects created by the role that ran
-- it — here, the migrator. Every migration must therefore be applied by the SAME role.
-- That is recorded as a deployment constraint in README.md and as finding CD-ENG-F16.
--
-- ============================================================================
-- DISCLOSED DEVIATION — cd_collector AND THE DIAL INPUT-SET TABLES
-- ============================================================================
--
-- Read literally, `INSERT on raw.*` includes raw.dial_required_input and
-- raw.dial_contributing_input, the two tables migration 2 adds to hold BLUEPRINT §5's
-- declarative "a DISPOSABLE source can never be named in a dial's required-input set"
-- constraint. Those tables did not exist when the matrix was written.
--
-- They are NOT granted to cd_collector, and the deviation is disclosed rather than taken
-- quietly, because granting them would contradict the same section's explicit doctrine:
-- "A collector fetches and records. It never computes... No collector holds a grant that
-- would let it write a conclusion." A collector able to insert into a dial's
-- required-input set can decide what a dial requires, which is a conclusion.
--
-- This is an implementation reading of a conflict inside §5, not a product decision, and
-- it is raised to the Project Lead as CD-ENG-F17. If the Project Lead rules the literal
-- reading, the change is two GRANT lines in a new migration.

SET timezone TO 'UTC';

-- ========================================================================================
-- STEP 1 — REVOKE BY DEFAULT, AGAIN, NOW THAT OBJECTS EXIST.
-- ========================================================================================
-- Migration 1 revoked what PUBLIC held before the tables existed. PUBLIC acquires EXECUTE
-- on every function created since, so the revoke is repeated here over the objects
-- themselves. Repetition is cheap; an inherited privilege is not.
DO $$
DECLARE
    schema_name text;
    role_name   text;
BEGIN
    FOREACH schema_name IN ARRAY ARRAY[
        'raw', 'witness', 'dial', 'publication', 'private', 'alert'
    ]
    LOOP
        EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA %I FROM PUBLIC', schema_name);
        EXECUTE format('REVOKE ALL ON ALL SEQUENCES IN SCHEMA %I FROM PUBLIC', schema_name);
        EXECUTE format('REVOKE ALL ON ALL FUNCTIONS IN SCHEMA %I FROM PUBLIC', schema_name);
        EXECUTE format('REVOKE ALL ON ALL ROUTINES IN SCHEMA %I FROM PUBLIC', schema_name);

        -- And from every application role, before any is granted anything. An
        -- unstated permission is absent, not implied (Standards Baseline §2).
        FOREACH role_name IN ARRAY ARRAY[
            'cd_collector', 'cd_witness', 'cd_engine', 'cd_public', 'cd_private', 'cd_review'
        ]
        LOOP
            EXECUTE format('REVOKE ALL ON SCHEMA %I FROM %I', schema_name, role_name);
            EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA %I FROM %I', schema_name, role_name);
            EXECUTE format('REVOKE ALL ON ALL SEQUENCES IN SCHEMA %I FROM %I', schema_name, role_name);
            EXECUTE format('REVOKE ALL ON ALL FUNCTIONS IN SCHEMA %I FROM %I', schema_name, role_name);
            EXECUTE format('REVOKE ALL ON ALL ROUTINES IN SCHEMA %I FROM %I', schema_name, role_name);
        END LOOP;
    END LOOP;
END
$$;

-- ========================================================================================
-- STEP 2 — GRANT BY EXCEPTION, ROW BY ROW.
-- ========================================================================================

-- ---------------------------------------------------------------------------------------
-- cd_collector: INSERT on raw.*; SELECT on raw.source_registry
-- ---------------------------------------------------------------------------------------
GRANT USAGE ON SCHEMA raw TO cd_collector;

GRANT INSERT ON raw.source_registry TO cd_collector;
GRANT INSERT ON raw.observation     TO cd_collector;
GRANT INSERT ON raw.reading         TO cd_collector;
-- raw.dial_required_input and raw.dial_contributing_input: deliberately NOT granted.
-- See "DISCLOSED DEVIATION" in the header (CD-ENG-F17).

GRANT SELECT ON raw.source_registry TO cd_collector;

-- ---------------------------------------------------------------------------------------
-- cd_witness: INSERT on witness.*, publication.witness_panel, alert.event
--             SELECT on witness.*, publication.public_envelope
-- ---------------------------------------------------------------------------------------
GRANT USAGE ON SCHEMA witness     TO cd_witness;
GRANT USAGE ON SCHEMA publication TO cd_witness;
GRANT USAGE ON SCHEMA alert       TO cd_witness;

GRANT INSERT ON witness.observation           TO cd_witness;
GRANT INSERT ON witness.reading               TO cd_witness;
GRANT INSERT ON publication.witness_panel     TO cd_witness;
GRANT INSERT ON alert.event                   TO cd_witness;

GRANT SELECT ON witness.observation           TO cd_witness;
GRANT SELECT ON witness.reading               TO cd_witness;

-- THE ONE-WAY VALVE. The witness layer reads the PUBLISHED score, because divergence
-- detection needs both sides. Nothing in the reverse direction exists.
GRANT SELECT ON publication.public_envelope   TO cd_witness;

-- cd_witness holds no grant on raw.* or dial.* — IT CANNOT INFLUENCE A SCORE. Stated as
-- a refusal so a reader does not have to infer it from an absence.
REVOKE ALL ON SCHEMA raw  FROM cd_witness;
REVOKE ALL ON SCHEMA dial FROM cd_witness;
REVOKE ALL ON ALL TABLES IN SCHEMA raw  FROM cd_witness;
REVOKE ALL ON ALL TABLES IN SCHEMA dial FROM cd_witness;

-- ---------------------------------------------------------------------------------------
-- cd_engine: SELECT on raw.*
--            INSERT on dial.*, publication.public_envelope,
--                      publication.private_envelope, publication.heartbeat, alert.event
-- ---------------------------------------------------------------------------------------
GRANT USAGE ON SCHEMA raw         TO cd_engine;
GRANT USAGE ON SCHEMA dial        TO cd_engine;
GRANT USAGE ON SCHEMA publication TO cd_engine;
GRANT USAGE ON SCHEMA alert       TO cd_engine;
-- NO `GRANT USAGE ON SCHEMA witness TO cd_engine`. There is no such line in this file and
-- there must never be one. See STEP 3.
-- NO grant on schema private either — the matrix marks it explicitly absent.

GRANT SELECT ON raw.source_registry          TO cd_engine;
GRANT SELECT ON raw.dial_required_input      TO cd_engine;
GRANT SELECT ON raw.dial_contributing_input  TO cd_engine;
GRANT SELECT ON raw.observation              TO cd_engine;
GRANT SELECT ON raw.reading                  TO cd_engine;

GRANT INSERT ON dial.history                 TO cd_engine;
GRANT INSERT ON publication.public_envelope  TO cd_engine;
GRANT INSERT ON publication.private_envelope TO cd_engine;
GRANT INSERT ON publication.heartbeat        TO cd_engine;
GRANT INSERT ON alert.event                  TO cd_engine;

-- ---------------------------------------------------------------------------------------
-- cd_public: SELECT on publication.public_envelope, publication.witness_panel
-- ---------------------------------------------------------------------------------------
-- Separation 3 of BLUEPRINT §3: the public surface authenticates as a role that can read
-- exactly two tables. No grant on dial, raw, private, or publication.private_envelope.
GRANT USAGE ON SCHEMA publication TO cd_public;

GRANT SELECT ON publication.public_envelope TO cd_public;
GRANT SELECT ON publication.witness_panel   TO cd_public;

-- ---------------------------------------------------------------------------------------
-- cd_private: SELECT on dial.*, publication.private_envelope, private.*, alert.event
--             INSERT on private.*
-- ---------------------------------------------------------------------------------------
GRANT USAGE ON SCHEMA dial        TO cd_private;
GRANT USAGE ON SCHEMA publication TO cd_private;
GRANT USAGE ON SCHEMA private     TO cd_private;
GRANT USAGE ON SCHEMA alert       TO cd_private;

GRANT SELECT ON dial.history                 TO cd_private;
GRANT SELECT ON publication.private_envelope TO cd_private;
GRANT SELECT ON alert.event                  TO cd_private;

-- private.* — no table exists yet (migration 6). The default privilege is what makes the
-- matrix row true of the first book-adjacent table a later work order adds, so it arrives
-- inside the boundary rather than needing to be remembered into it.
ALTER DEFAULT PRIVILEGES IN SCHEMA private GRANT SELECT, INSERT ON TABLES TO cd_private;

-- ---------------------------------------------------------------------------------------
-- cd_review: SELECT on publication.public_envelope; INSERT on publication.review
-- ---------------------------------------------------------------------------------------
-- BLUEPRINT §9: no INSERT or UPDATE on any dial or envelope number, so the AI review's
-- authority limit is a grant and not an instruction.
GRANT USAGE ON SCHEMA publication TO cd_review;

GRANT SELECT ON publication.public_envelope TO cd_review;
GRANT INSERT ON publication.review          TO cd_review;

-- ========================================================================================
-- STEP 3 — CD-AC-003, STATED AS A REFUSAL RATHER THAN AN OMISSION.
-- ========================================================================================
-- Nothing above grants cd_engine anything in schema witness. These lines make that
-- explicit in the file and idempotent against any earlier state, so a store migrated from
-- a cluster where somebody had granted it by hand converges to the correct posture
-- instead of preserving the defect.
REVOKE ALL ON SCHEMA witness                FROM cd_engine;
REVOKE ALL ON ALL TABLES    IN SCHEMA witness FROM cd_engine;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA witness FROM cd_engine;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA witness FROM cd_engine;
REVOKE ALL ON ALL ROUTINES  IN SCHEMA witness FROM cd_engine;

-- And from every role except cd_witness. Schema `witness` is cd_witness's alone
-- (BLUEPRINT §4: "readable by cd_witness only").
REVOKE ALL ON SCHEMA witness FROM cd_collector, cd_public, cd_private, cd_review;
REVOKE ALL ON ALL TABLES IN SCHEMA witness FROM cd_collector, cd_public, cd_private, cd_review;

-- ========================================================================================
-- STEP 4 — APPEND-ONLY WHERE HISTORY IS A CLAIM.
-- ========================================================================================
-- BLUEPRINT §4: dial.history, raw.observation, witness.observation and alert.event carry
-- NO UPDATE OR DELETE GRANT FOR ANY ROLE. Nothing above grants either; these lines state
-- it, and make the posture converge rather than merely start correct.
--
-- TRUNCATE is revoked with them. A grant matrix that forbids DELETE and permits TRUNCATE
-- forbids nothing, and TRUNCATE is the version that leaves no rows to notice.
DO $$
DECLARE
    target text;
    role_name text;
BEGIN
    FOREACH target IN ARRAY ARRAY[
        'dial.history', 'raw.observation', 'witness.observation', 'alert.event',
        -- The same rule applied to the other tables that record a claim. Extending the
        -- rule beyond the four named is a tightening, not a paraphrase: no role in the
        -- matrix is granted UPDATE or DELETE anywhere at all.
        'raw.reading', 'raw.source_registry', 'raw.dial_required_input',
        'raw.dial_contributing_input', 'witness.reading',
        'publication.public_envelope', 'publication.private_envelope',
        'publication.witness_panel', 'publication.review', 'publication.heartbeat'
    ]
    LOOP
        FOREACH role_name IN ARRAY ARRAY[
            'cd_collector', 'cd_witness', 'cd_engine', 'cd_public', 'cd_private', 'cd_review'
        ]
        LOOP
            EXECUTE format('REVOKE UPDATE, DELETE, TRUNCATE ON %s FROM %I', target, role_name);
        END LOOP;
        EXECUTE format('REVOKE UPDATE, DELETE, TRUNCATE ON %s FROM PUBLIC', target);
    END LOOP;
END
$$;
