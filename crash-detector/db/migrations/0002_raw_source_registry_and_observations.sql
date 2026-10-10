-- migration: 2
-- name: raw_source_registry_and_observations
-- rollback: NONE. Dropping these tables destroys the append-only observation record,
--   which is the evidence that a fetch was attempted at all. Recovery from a bad apply is
--   by restoring the store from its dump (BLUEPRINT §12). Forward-only (PBG-DATA-002).
--
-- BLUEPRINT §4 and §5. The ingredient side of the store.
--
-- THREE TABLES, AND THE REASON THEY ARE THREE AND NOT ONE.
--
--   raw.source_registry  which sources exist, and how load-bearing each one is
--   raw.observation      one row per FETCH ATTEMPT, whatever came of it. No payload.
--   raw.reading          one row per SOURCE PERIOD actually observed. Unique. Carries the
--                        validated payload.
--
-- The observation/reading split is the same split
-- crash_detector.collectors.attempt makes in code, and it exists because the two have
-- OPPOSITE uniqueness rules:
--
--   * the attempt log is append-only and UNCONSTRAINED. Every attempt appends, always. A
--     unique constraint here would deduplicate failures out of the record, and the count
--     of failed attempts is exactly what tells an operator a source is dying.
--   * the reading is UNIQUE on (source_id, source_as_of_utc). Re-fetching the same period
--     must not produce a second reading of it. `INSERT ... ON CONFLICT DO NOTHING` plus
--     the reported row count is the whole contract of
--     crash_detector.collectors.attempt.ReadingLedger.admit_if_absent.
--
-- WO-2 SEEDS NO SOURCE ROW. Registering an ingredient source is choosing what a dial
-- MEANS, which is the Product Owner's (CD-D-005, owed before WO-3; BLUEPRINT §16). The
-- empty registry is the deliverable, not a gap: with nothing registered every dial
-- correctly reads UNKNOWN.

SET timezone TO 'UTC';

-- --------------------------------------------------------------------------------------
-- raw.source_registry — the registry is DATA, not code (BLUEPRINT §5).
-- --------------------------------------------------------------------------------------
CREATE TABLE raw.source_registry (
    source_id       text        NOT NULL,
    adapter_id      text        NOT NULL,
    cadence_seconds integer     NOT NULL,
    criticality     text        NOT NULL,
    stands_for      text        NOT NULL,
    registered_utc  timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT source_registry_pk PRIMARY KEY (source_id),

    -- The criticality CHECK admits exactly crash_detector.source_registry.CRITICALITY_NAMES.
    -- Three members. A fourth is a Blueprint amendment, not an edit here, because each
    -- member carries a declared engine consequence (BLUEPRINT §5) and a criticality with
    -- no declared consequence is one nobody can act on.
    CONSTRAINT source_registry_criticality_admitted
        CHECK (criticality IN ('REQUIRED', 'CONTRIBUTING', 'DISPOSABLE')),

    -- The FK target that makes the DISPOSABLE prohibition declarative rather than a
    -- trigger. See raw.dial_required_input below. Redundant with the primary key as a
    -- uniqueness statement; present because a composite foreign key needs a composite
    -- unique constraint to point at.
    CONSTRAINT source_registry_id_criticality_unique UNIQUE (source_id, criticality),

    CONSTRAINT source_registry_ids_not_blank
        CHECK (length(btrim(source_id)) > 0
           AND length(btrim(adapter_id)) > 0
           AND length(btrim(stands_for)) > 0),

    -- Mirrors SourceRecord.__post_init__: a zero or negative cadence is not a schedule.
    CONSTRAINT source_registry_cadence_positive CHECK (cadence_seconds > 0)
);

COMMENT ON TABLE raw.source_registry IS
    'Registered ingredient sources. EMPTY in WO-2 by decision (CD-D-005 owed to the Product Owner). Mirrors crash_detector.source_registry.SourceRecord.';
COMMENT ON COLUMN raw.source_registry.criticality IS
    'REQUIRED | CONTRIBUTING | DISPOSABLE. Declares the ENGINE consequence of the source being absent (BLUEPRINT §5).';
COMMENT ON COLUMN raw.source_registry.stands_for IS
    'What this source stands for in the dial. Doctrine §3.6 forbids an unexplained mapping, so a source cannot be registered without one.';

-- --------------------------------------------------------------------------------------
-- raw.dial_required_input — "a DISPOSABLE source can never be named in a dial's
-- required-input set" (BLUEPRINT §5), enforced DECLARATIVELY.
-- --------------------------------------------------------------------------------------
-- A trigger would work and is rejected in favour of a constraint the planner and the
-- catalogue both understand: a composite foreign key to (source_id, criticality) with the
-- referencing criticality column pinned by CHECK. The only rows that can exist are rows
-- whose source is registered REQUIRED. There is no window in which the pair is
-- inconsistent, no ordering dependence, and nothing to disable.
--
-- Its class-level strength: changing a source's criticality away from REQUIRED while it
-- is named here is refused by the foreign key, not merely the insert. So a source cannot
-- become load-bearing by an edit six months from now, AND a load-bearing source cannot be
-- quietly demoted to DISPOSABLE while a dial still requires it. Both directions are the
-- same defect, and ON UPDATE RESTRICT closes the second one.
CREATE TABLE raw.dial_required_input (
    dial_id     text NOT NULL,
    source_id   text NOT NULL,
    criticality text NOT NULL,

    CONSTRAINT dial_required_input_pk PRIMARY KEY (dial_id, source_id),

    -- Two dials. A third is a PID amendment, not a configuration edit
    -- (crash_detector.dials.dialset.DIAL_IDS).
    CONSTRAINT dial_required_input_dial_admitted
        CHECK (dial_id IN ('equity_crash', 'monetary_debasement')),

    -- The pin. This column cannot hold 'CONTRIBUTING' or 'DISPOSABLE' at all, so the
    -- foreign key below can only ever resolve against a REQUIRED registry row.
    CONSTRAINT dial_required_input_criticality_pinned
        CHECK (criticality = 'REQUIRED'),

    CONSTRAINT dial_required_input_source_is_required
        FOREIGN KEY (source_id, criticality)
        REFERENCES raw.source_registry (source_id, criticality)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

COMMENT ON TABLE raw.dial_required_input IS
    'Which registered sources a dial REQUIRES. A DISPOSABLE or CONTRIBUTING source cannot appear here: the criticality column is pinned to REQUIRED by CHECK and the composite FK resolves against (source_id, criticality) in the registry (BLUEPRINT §5, CD-AC-001). Empty in WO-2 — nothing is registered, so nothing can be required.';

CREATE TABLE raw.dial_contributing_input (
    dial_id     text NOT NULL,
    source_id   text NOT NULL,
    criticality text NOT NULL,

    CONSTRAINT dial_contributing_input_pk PRIMARY KEY (dial_id, source_id),
    CONSTRAINT dial_contributing_input_dial_admitted
        CHECK (dial_id IN ('equity_crash', 'monetary_debasement')),
    -- Same instrument, other set. A DISPOSABLE source's absence must change NOTHING, and
    -- a contributing input's absence forces Degraded; those cannot both be true of one
    -- source. Mirrors SourceRegistry.assert_may_be_contributing.
    CONSTRAINT dial_contributing_input_criticality_pinned
        CHECK (criticality = 'CONTRIBUTING'),
    CONSTRAINT dial_contributing_input_source_is_contributing
        FOREIGN KEY (source_id, criticality)
        REFERENCES raw.source_registry (source_id, criticality)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

COMMENT ON TABLE raw.dial_contributing_input IS
    'Which registered sources CONTRIBUTE to a dial. Same declarative instrument as raw.dial_required_input, pinned to CONTRIBUTING.';

-- --------------------------------------------------------------------------------------
-- raw.observation — ONE ROW PER FETCH ATTEMPT, INCLUDING THE FAILURES.
-- --------------------------------------------------------------------------------------
-- The single most important property in the collector component (BLUEPRINT §5). A failed
-- fetch that writes nothing is indistinguishable from a fetch that was never scheduled,
-- and both are indistinguishable from a source that had nothing to report — three states
-- that demand different responses, collapsed into one absence (Standards Baseline §8).
--
-- DELIBERATELY ABSENT, AND NOT TO BE REINTRODUCED: any free-text detail column and any
-- payload-excerpt column. Both were removed from the increment-2 design because they are
-- a secret-exfiltration path into an append-only store that carries no DELETE grant: a
-- hostile or merely careless source echoes a credential back inside the value that failed
-- validation, and jsonschema's own error messages embed the offending instance value
-- (PBG-SEC-002, non-waivable). What is stored instead is CLASSIFICATION — error_class,
-- schema_error_class — and LOCATION — instance_path, an RFC 6901 pointer built from
-- property names and array indices only.
--
-- NO source_id FOREIGN KEY, DELIBERATELY. An FK here would let registry state veto the
-- recording of an attempt: deregister a source mid-run and the attempt row that proves we
-- tried becomes unwritable. That is precisely the failure the append-only attempt log
-- exists to prevent, so referential tidiness loses to it.
--
-- NO UNIQUE CONSTRAINT beyond the surrogate identity. See the header. The identity column
-- is a row address, not a deduplication key.
CREATE TABLE raw.observation (
    observation_id     bigint      GENERATED ALWAYS AS IDENTITY,
    source_id          text        NOT NULL,
    adapter_id         text        NOT NULL,
    collector_run_id   text        NOT NULL,
    attempt_number     integer     NOT NULL,
    requested_utc      timestamptz NOT NULL,
    observed_utc       timestamptz NOT NULL,
    outcome            text        NOT NULL,
    source_as_of_utc   timestamptz,
    error_class        text,
    http_status        integer,
    schema_error_class text,
    instance_path      text,

    CONSTRAINT observation_pk PRIMARY KEY (observation_id),

    -- Exactly crash_detector.observations.OUTCOME_CLASSES. FOUR, not three: MALFORMED and
    -- EMPTY are different facts and neither is FETCH_FAILED.
    CONSTRAINT observation_outcome_admitted
        CHECK (outcome IN ('OK', 'FETCH_FAILED', 'MALFORMED', 'EMPTY')),

    CONSTRAINT observation_ids_not_blank
        CHECK (length(btrim(source_id)) > 0
           AND length(btrim(adapter_id)) > 0
           AND length(btrim(collector_run_id)) > 0),

    CONSTRAINT observation_attempt_numbering_starts_at_one
        CHECK (attempt_number >= 1),

    -- Mirrors AttemptRecord.__post_init__: a fetch cannot finish before it started, and a
    -- row that says otherwise makes every latency figure derived from it wrong.
    CONSTRAINT observation_completed_after_requested
        CHECK (observed_utc >= requested_utc),

    -- http_status is NULLABLE and NEVER DEFAULTS TO 0. A zero status would sort, compare
    -- and aggregate alongside real statuses, and "we never got a status" would become a
    -- status. 0 is excluded by the range, not merely undefaulted.
    CONSTRAINT observation_http_status_is_a_real_status
        CHECK (http_status IS NULL OR (http_status BETWEEN 100 AND 599)),

    -- crash_detector.observations.MAX_INSTANCE_PATH_LENGTH. Unbounded external input on a
    -- path into an append-only store with no DELETE grant is an unbounded row.
    CONSTRAINT observation_instance_path_bounded
        CHECK (instance_path IS NULL OR length(instance_path) <= 200),

    -- RFC 6901: the empty string is the pointer to the document ROOT — a real location,
    -- not a placeholder — and any other pointer begins with '/'.
    CONSTRAINT observation_instance_path_is_a_json_pointer
        CHECK (instance_path IS NULL OR instance_path = '' OR instance_path LIKE '/%'),

    -- THE DISCRIMINATED UNION, HELD IN THE STORE.
    --
    -- The outcome sum type has four constructors carrying different fields, and this
    -- CHECK is what stops the table degenerating into "one row shape with a label". Every
    -- non-OK outcome has source_as_of_utc NULL, because a failed, malformed or empty
    -- answer reports no source period; inventing one for it — the fetch instant, say —
    -- would make every failure a distinct observation OF something.
    CONSTRAINT observation_outcome_fields_coherent CHECK (
        CASE outcome
            WHEN 'OK' THEN
                    source_as_of_utc   IS NOT NULL
                AND error_class        IS NULL
                AND http_status        IS NULL
                AND schema_error_class IS NULL
                AND instance_path      IS NULL
            WHEN 'FETCH_FAILED' THEN
                    source_as_of_utc   IS NULL
                AND error_class        IS NOT NULL
                AND length(btrim(error_class)) > 0
                AND schema_error_class IS NULL
                AND instance_path      IS NULL
            WHEN 'MALFORMED' THEN
                    source_as_of_utc   IS NULL
                AND error_class        IS NULL
                AND http_status        IS NULL
                AND schema_error_class IS NOT NULL
                AND length(btrim(schema_error_class)) > 0
                AND instance_path      IS NOT NULL
            WHEN 'EMPTY' THEN
                    source_as_of_utc   IS NULL
                AND error_class        IS NULL
                AND http_status        IS NULL
                AND schema_error_class IS NULL
                AND instance_path      IS NULL
            ELSE false
        END
    )
);

COMMENT ON TABLE raw.observation IS
    'One row per fetch ATTEMPT, including failures (BLUEPRINT §5). Append-only: no UPDATE or DELETE grant for any role. No unique constraint — deduplicating here would erase the failure count. No payload and no free-text detail column, deliberately (PBG-SEC-002).';
COMMENT ON COLUMN raw.observation.observed_utc IS
    'When WE completed the attempt. Distinct from source_as_of_utc so that "we asked recently" is never mistaken for "the data is recent".';
COMMENT ON COLUMN raw.observation.source_as_of_utc IS
    'The instant the SOURCE says its data is for. NULL for every non-OK outcome, enforced by observation_outcome_fields_coherent.';
COMMENT ON COLUMN raw.observation.http_status IS
    'NULLABLE. Never defaults to 0: "we never got a status" is not a status.';
COMMENT ON COLUMN raw.observation.instance_path IS
    'RFC 6901 JSON Pointer naming WHERE a MALFORMED response failed. Property names and array indices only — never a value. Bounded at 200 characters.';

-- Reading paths the engine and the operator actually use. Not unique — see the header.
CREATE INDEX observation_source_observed_idx
    ON raw.observation (source_id, observed_utc DESC);
CREATE INDEX observation_run_idx
    ON raw.observation (collector_run_id);

-- --------------------------------------------------------------------------------------
-- raw.reading — the source period, claimed exactly once.
-- --------------------------------------------------------------------------------------
-- UNIQUE (source_id, source_as_of_utc) is the store half of BLUEPRINT §5's idempotency
-- rule and the exact contract of ReadingLedger.admit_if_absent: the collector issues
-- `INSERT ... ON CONFLICT DO NOTHING` and reads the row count to learn whether THIS call
-- claimed the period, with no prior SELECT and no race between the two.
--
-- The source_id FK is present here and absent on raw.observation, and the asymmetry is
-- deliberate: an attempt must always be recordable, but a READING of an unregistered
-- source is a reading nobody can explain — it has no declared criticality, so the engine
-- could not say what its absence would have meant. With the WO-2 registry empty, this FK
-- means no reading can be admitted at all, which is the correct consequence of having
-- registered nothing rather than an obstacle to be worked around.
CREATE TABLE raw.reading (
    reading_id       bigint      GENERATED ALWAYS AS IDENTITY,
    source_id        text        NOT NULL,
    source_as_of_utc timestamptz NOT NULL,
    payload          jsonb       NOT NULL,
    observation_id   bigint      NOT NULL,
    admitted_utc     timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT reading_pk PRIMARY KEY (reading_id),

    CONSTRAINT reading_source_period_unique UNIQUE (source_id, source_as_of_utc),

    CONSTRAINT reading_source_registered
        FOREIGN KEY (source_id) REFERENCES raw.source_registry (source_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,

    -- The reading names the attempt that produced it, so a published number can be traced
    -- back to the fetch that observed it.
    CONSTRAINT reading_from_an_observation
        FOREIGN KEY (observation_id) REFERENCES raw.observation (observation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,

    -- A validated response is a JSON object; crash_detector.observations.OK.payload is a
    -- mapping. A bare scalar or array admitted by a slack declared schema is refused here
    -- rather than wrapped, because wrapping would invent a key name.
    CONSTRAINT reading_payload_is_an_object
        CHECK (jsonb_typeof(payload) = 'object')
);

COMMENT ON TABLE raw.reading IS
    'One validated observation of one source period. UNIQUE (source_id, source_as_of_utc) — the store half of the idempotency rule in BLUEPRINT §5.';
