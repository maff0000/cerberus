-- migration: 3
-- name: witness_observations
-- rollback: NONE. Append-only observation evidence; forward-only (PBG-DATA-002).
--   Recovery from a bad apply is by restore from dump (BLUEPRINT §12).
--
-- BLUEPRINT §4 and §6. The witness side of the store — "witness observations, same shape".
--
-- THE WHOLE POINT OF THIS SCHEMA IS WHO CANNOT SEE IT.
--
-- The witness layer is a parallel pipeline that shares no component with the score,
-- meeting it only where the two are displayed next to each other (BLUEPRINT §6). In the
-- store that is one asymmetry, granted in 0007 and stated here so the reason travels with
-- the tables:
--
--     cd_witness  MAY SELECT publication.public_envelope   -- witnesses see the published
--                                                          -- score, because divergence
--                                                          -- detection needs both sides
--     cd_engine   holds NO GRANT OF ANY KIND on schema witness
--
-- A one-way valve. Witnesses see the score after it is published; the score never sees
-- the witnesses. That single asymmetry is what makes CD-AC-003 true by construction
-- rather than by test.
--
-- OWED, STATED RATHER THAN LEFT TO BE DISCOVERED: there is no witness source registry
-- table. BLUEPRINT §2 names OFR and Quantical as the witnesses, but registering a source
-- row — any source row — is prohibited to this seat, and a registry table with a
-- criticality vocabulary for witnesses would be asserting an engine consequence for a
-- witness that the Blueprint does not declare (witnesses have no engine consequence: they
-- corroborate, they never contribute). The witness source_id is therefore an
-- unconstrained identifier in WO-2. If a witness registry is wanted, it is a Blueprint
-- question, not an implementation one (PBG-AUTH-005).

SET timezone TO 'UTC';

-- --------------------------------------------------------------------------------------
-- witness.observation — same shape as raw.observation, same guarantee.
-- --------------------------------------------------------------------------------------
-- Every witness fetch attempt writes a row too, for exactly the reason the ingredient
-- side does: a dead witness feed must be visibly dead. A witness panel that reads AGREES
-- because nothing was recorded corroborates nothing while looking like corroboration,
-- which is worse than no panel at all (CD-AC-005).
CREATE TABLE witness.observation (
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

    CONSTRAINT witness_observation_pk PRIMARY KEY (observation_id),

    CONSTRAINT witness_observation_outcome_admitted
        CHECK (outcome IN ('OK', 'FETCH_FAILED', 'MALFORMED', 'EMPTY')),

    CONSTRAINT witness_observation_ids_not_blank
        CHECK (length(btrim(source_id)) > 0
           AND length(btrim(adapter_id)) > 0
           AND length(btrim(collector_run_id)) > 0),

    CONSTRAINT witness_observation_attempt_numbering_starts_at_one
        CHECK (attempt_number >= 1),

    CONSTRAINT witness_observation_completed_after_requested
        CHECK (observed_utc >= requested_utc),

    CONSTRAINT witness_observation_http_status_is_a_real_status
        CHECK (http_status IS NULL OR (http_status BETWEEN 100 AND 599)),

    CONSTRAINT witness_observation_instance_path_bounded
        CHECK (instance_path IS NULL OR length(instance_path) <= 200),

    CONSTRAINT witness_observation_instance_path_is_a_json_pointer
        CHECK (instance_path IS NULL OR instance_path = '' OR instance_path LIKE '/%'),

    CONSTRAINT witness_observation_outcome_fields_coherent CHECK (
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

COMMENT ON TABLE witness.observation IS
    'One row per WITNESS fetch attempt, including failures. Append-only: no UPDATE or DELETE grant for any role. cd_engine holds no grant of any kind on this schema (CD-AC-003).';

CREATE INDEX witness_observation_source_observed_idx
    ON witness.observation (source_id, observed_utc DESC);

-- --------------------------------------------------------------------------------------
-- witness.reading — the witness period, claimed exactly once.
-- --------------------------------------------------------------------------------------
CREATE TABLE witness.reading (
    reading_id       bigint      GENERATED ALWAYS AS IDENTITY,
    source_id        text        NOT NULL,
    source_as_of_utc timestamptz NOT NULL,
    payload          jsonb       NOT NULL,
    observation_id   bigint      NOT NULL,
    admitted_utc     timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT witness_reading_pk PRIMARY KEY (reading_id),
    CONSTRAINT witness_reading_source_period_unique UNIQUE (source_id, source_as_of_utc),
    CONSTRAINT witness_reading_from_an_observation
        FOREIGN KEY (observation_id) REFERENCES witness.observation (observation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT witness_reading_payload_is_an_object
        CHECK (jsonb_typeof(payload) = 'object')
);

COMMENT ON TABLE witness.reading IS
    'One validated witness observation of one period. UNIQUE (source_id, source_as_of_utc), the same idempotency rule as the ingredient side.';
