-- migration: 5
-- name: publication
-- rollback: NONE. Published envelopes are the artefact consumers have already seen;
--   dropping them rewrites what was published. Forward-only (PBG-DATA-002).
--
-- BLUEPRINT §3, §4, §8 and §9. What the two surfaces serve, and nothing else.
--
-- THE CLOSED ENVELOPE, HELD A SECOND TIME.
--
-- BLUEPRINT §3 lists five independent separations between public and private, of which
-- any one failing still leaves four. Separation 4 is the closed JSON Schema in
-- contracts/public_envelope.schema.json, and separation 5 is that publication REFUSES on
-- an unknown or private-classified key rather than filtering it out.
--
-- This migration adds the same closure IN THE STORE, as a CHECK constraint whose
-- allowlist is the schema's top-level `properties` list, verbatim. It is not a
-- replacement for the schema and it is not a duplicate of it: the schema validates the
-- whole document to arbitrary depth in the process that builds it, and this constraint
-- refuses a top-level key at the point of writing, whatever process wrote it and whether
-- or not that process remembered to validate. A boundary held in two independent places,
-- because either alone is a single point of failure for the product's most consequential
-- criterion.
--
-- It is an ALLOWLIST and not a denylist, deliberately. `combined_stress` is refused not
-- because it is named anywhere but because it is not among the ten keys that are. A key
-- nobody declared cannot be published even if something computed it, and renaming the
-- blend does not get it past.
--
-- The two lists below must stay in step with contracts/*.schema.json. A test asserts
-- exactly that, by reading both files, so drift between them is a failing test rather
-- than a discovery in production.

SET timezone TO 'UTC';

-- --------------------------------------------------------------------------------------
-- publication.public_envelope — read by cd_public, and by cd_witness (the one-way valve).
-- --------------------------------------------------------------------------------------
CREATE TABLE publication.public_envelope (
    public_envelope_id bigint      GENERATED ALWAYS AS IDENTITY,
    schema_version     text        NOT NULL,
    as_of_utc          timestamptz NOT NULL,
    published_utc      timestamptz NOT NULL DEFAULT now(),
    config_snapshot_id text        NOT NULL,
    envelope           jsonb       NOT NULL,

    CONSTRAINT public_envelope_pk PRIMARY KEY (public_envelope_id),

    CONSTRAINT public_envelope_is_an_object
        CHECK (jsonb_typeof(envelope) = 'object'),

    -- CLOSED. Subtracting the allowlist must leave the empty object: any key outside it
    -- survives the subtraction and the constraint fails.
    CONSTRAINT public_envelope_keys_are_an_allowlist CHECK (
        (envelope - ARRAY[
            'schema_version',
            'as_of_utc',
            'published_utc',
            'regime',
            'staleness_window_seconds',
            'inputs_used',
            'degraded_inputs',
            'config_snapshot_id',
            'equity_crash',
            'monetary_debasement'
        ]) = '{}'::jsonb
    ),

    -- The honesty fields BLUEPRINT §8 marks required. An envelope cannot be published
    -- without them, so a consumer never has to distinguish "no degradation" from "the
    -- field was omitted".
    CONSTRAINT public_envelope_honesty_fields_present CHECK (
        envelope ?& ARRAY[
            'schema_version',
            'as_of_utc',
            'published_utc',
            'regime',
            'staleness_window_seconds',
            'inputs_used',
            'degraded_inputs',
            'config_snapshot_id',
            'equity_crash',
            'monetary_debasement'
        ]
    ),

    -- The indexed columns are a projection of the document, so they must agree with it.
    -- Two copies of a fact that can disagree is one fact with a bug scheduled.
    CONSTRAINT public_envelope_columns_agree_with_document CHECK (
            envelope ->> 'schema_version'     = schema_version
        AND envelope ->> 'config_snapshot_id' = config_snapshot_id
    )
);

COMMENT ON TABLE publication.public_envelope IS
    'The published public envelope. Top-level keys are an allowlist matching contracts/public_envelope.schema.json — there is no place here for a third, combined number (CD-AC-002, CD-AC-006). Readable by cd_public and, one-way, by cd_witness.';

CREATE INDEX public_envelope_published_idx
    ON publication.public_envelope (published_utc DESC);

-- --------------------------------------------------------------------------------------
-- publication.private_envelope — cd_public holds no grant on this table.
-- --------------------------------------------------------------------------------------
CREATE TABLE publication.private_envelope (
    private_envelope_id bigint      GENERATED ALWAYS AS IDENTITY,
    schema_version      text        NOT NULL,
    classification      text        NOT NULL,
    as_of_utc           timestamptz NOT NULL,
    published_utc       timestamptz NOT NULL DEFAULT now(),
    config_snapshot_id  text        NOT NULL,
    envelope            jsonb       NOT NULL,

    CONSTRAINT private_envelope_pk PRIMARY KEY (private_envelope_id),

    CONSTRAINT private_envelope_is_an_object
        CHECK (jsonb_typeof(envelope) = 'object'),

    CONSTRAINT private_envelope_keys_are_an_allowlist CHECK (
        (envelope - ARRAY[
            'schema_version',
            'classification',
            'as_of_utc',
            'published_utc',
            'regime',
            'staleness_window_seconds',
            'inputs_used',
            'degraded_inputs',
            'config_snapshot_id',
            'equity_crash',
            'monetary_debasement'
        ]) = '{}'::jsonb
    ),

    CONSTRAINT private_envelope_honesty_fields_present CHECK (
        envelope ?& ARRAY[
            'schema_version',
            'classification',
            'as_of_utc',
            'published_utc',
            'regime',
            'staleness_window_seconds',
            'inputs_used',
            'degraded_inputs',
            'config_snapshot_id',
            'equity_crash',
            'monetary_debasement'
        ]
    ),

    -- The private envelope declares its own classification, and it is PRIVATE. A row that
    -- says otherwise is a private envelope claiming it may be served publicly.
    CONSTRAINT private_envelope_is_classified_private
        CHECK (classification = 'PRIVATE'),

    CONSTRAINT private_envelope_columns_agree_with_document CHECK (
            envelope ->> 'schema_version'     = schema_version
        AND envelope ->> 'classification'     = classification
        AND envelope ->> 'config_snapshot_id' = config_snapshot_id
    )
);

COMMENT ON TABLE publication.private_envelope IS
    'The published private envelope. cd_public holds NO grant on this table — separation 3 of BLUEPRINT §3.';

CREATE INDEX private_envelope_published_idx
    ON publication.private_envelope (published_utc DESC);

-- --------------------------------------------------------------------------------------
-- publication.witness_panel — CD-AC-005. Unavailable is not agreement.
-- --------------------------------------------------------------------------------------
-- Written by cd_witness, read by cd_public. The engine writes nothing here and reads
-- nothing from it: the panel and the score meet only where they are displayed next to
-- each other.
--
-- The coherence CHECK is the store-side form of crash_detector.witness.panel: reaching
-- AGREES requires a MEASUREMENT. There is no row shape in which panel_state = 'AGREES'
-- and divergence_measure IS NULL, so absence cannot be written as agreement even by a
-- direct INSERT that bypasses the application entirely.
CREATE TABLE publication.witness_panel (
    witness_panel_id   bigint      GENERATED ALWAYS AS IDENTITY,
    panel_state        text        NOT NULL,
    divergence_measure double precision,
    threshold          double precision,
    as_of_utc          timestamptz,
    since_utc          timestamptz,
    reason             text,
    published_utc      timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT witness_panel_pk PRIMARY KEY (witness_panel_id),

    -- crash_detector.witness.panel.PANEL_STATES.
    CONSTRAINT witness_panel_state_admitted
        CHECK (panel_state IN ('AGREES', 'DIVERGES', 'UNAVAILABLE')),

    -- crash_detector.witness.panel.UNAVAILABLE_REASONS. Every route to unavailability is
    -- named, so "we do not know why" is never itself silently a reason.
    CONSTRAINT witness_panel_unavailable_reason_admitted CHECK (
        panel_state <> 'UNAVAILABLE'
        OR reason IN (
            'PANEL_ROW_ABSENT',
            'PANEL_ROW_STALE',
            'PANEL_ROW_FUTURE_DATED',
            'PANEL_ROW_INCOHERENT',
            'PANEL_STATE_UNRECOGNISED',
            'WITNESS_FEED_UNREACHABLE'
        )
    ),

    CONSTRAINT witness_panel_state_fields_coherent CHECK (
        CASE panel_state
            WHEN 'AGREES' THEN
                -- `<> 'NaN'` and not `x = x`: PostgreSQL departs from IEEE 754 and holds
                -- NaN = NaN TRUE, so the idiomatic self-comparison ADMITS NaN. A NaN
                -- divergence measure would be a measurement that is not one, on the row
                -- whose whole purpose is that agreement requires a measurement.
                    divergence_measure IS NOT NULL
                AND divergence_measure <> 'NaN'::float8
                AND as_of_utc IS NOT NULL
                AND since_utc IS NULL
                AND threshold IS NULL
                AND reason    IS NULL
            WHEN 'DIVERGES' THEN
                    divergence_measure IS NOT NULL
                AND divergence_measure <> 'NaN'::float8
                AND threshold IS NOT NULL
                AND threshold <> 'NaN'::float8
                AND as_of_utc IS NOT NULL
                AND since_utc IS NULL
                AND reason    IS NULL
            WHEN 'UNAVAILABLE' THEN
                -- Carries NO divergence measure, because there is none. There is nothing
                -- on this row a rendering layer could mistake for a measurement.
                    divergence_measure IS NULL
                AND threshold IS NULL
                AND as_of_utc IS NULL
                AND since_utc IS NOT NULL
                AND reason    IS NOT NULL
            ELSE false
        END
    )
);

COMMENT ON TABLE publication.witness_panel IS
    'The witness panel. AGREES requires a measurement: there is no row shape in which agreement is reachable from absence (CD-AC-005).';

CREATE INDEX witness_panel_published_idx
    ON publication.witness_panel (published_utc DESC);

-- --------------------------------------------------------------------------------------
-- publication.review — the AI review, with zero authority over a number.
-- --------------------------------------------------------------------------------------
-- BLUEPRINT §9. cd_review holds no INSERT or UPDATE on any dial or envelope number, so
-- the authority limit is a grant rather than an instruction. This table reinforces it:
-- IT DECLARES NO NUMERIC COLUMN AT ALL other than its own identity and the foreign key
-- naming the envelope it reviewed. There is no float, no numeric, no score — nothing for
-- a headline to be written into, so a model that tried would have nowhere to put it.
--
-- `rejected_by_validator` records a review that FAILED a validator. A rejected review is
-- recorded as rejected, not silently trimmed: a trimmed output hides the fact that the
-- model tried.
CREATE TABLE publication.review (
    review_id             bigint      GENERATED ALWAYS AS IDENTITY,
    public_envelope_id    bigint      NOT NULL,
    model_id              text        NOT NULL,
    review_text           text        NOT NULL,
    admitted              boolean     NOT NULL,
    validators_passed     text[]      NOT NULL,
    rejected_by_validator text,
    created_utc           timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT review_pk PRIMARY KEY (review_id),

    CONSTRAINT review_of_a_published_envelope
        FOREIGN KEY (public_envelope_id)
        REFERENCES publication.public_envelope (public_envelope_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,

    -- BLUEPRINT §9's four validators. Named, so a fifth is a deliberate migration.
    CONSTRAINT review_rejecting_validator_admitted CHECK (
        rejected_by_validator IS NULL
        OR rejected_by_validator IN (
            'no_headline_authorship',
            'no_crash_certainty',
            'no_market_is_safe',
            'no_missing_data_as_safety'
        )
    ),

    -- Admitted and rejected are mutually exclusive facts, and neither may be silent.
    CONSTRAINT review_admission_is_coherent CHECK (
        (admitted AND rejected_by_validator IS NULL)
        OR ((NOT admitted) AND rejected_by_validator IS NOT NULL)
    ),

    CONSTRAINT review_model_named CHECK (length(btrim(model_id)) > 0)
);

COMMENT ON TABLE publication.review IS
    'The one AI review. Declares no numeric dial column: there is nothing here for a headline number to be written into (BLUEPRINT §9, doctrine §3.3).';

-- --------------------------------------------------------------------------------------
-- publication.heartbeat — cadence is monitored on the PUBLICATION layer (CD-AC-008).
-- --------------------------------------------------------------------------------------
-- Each successful publish writes a row. A cadence breach is an excessive INTERVAL BETWEEN
-- HEARTBEATS, not the age of a number — which is why this table exists separately from
-- public_envelope.published_utc: an envelope that was never written leaves no timestamp
-- to be old, and the absence of a heartbeat is what must be detected.
--
-- The check that reads it runs OUTSIDE the container set (BLUEPRINT §8, PBG-EVID-001): a
-- process inside the system reporting that the system is publishing is self-certification.
CREATE TABLE publication.heartbeat (
    heartbeat_id       bigint      GENERATED ALWAYS AS IDENTITY,
    published_utc      timestamptz NOT NULL DEFAULT now(),
    public_envelope_id bigint      NOT NULL,

    CONSTRAINT heartbeat_pk PRIMARY KEY (heartbeat_id),
    CONSTRAINT heartbeat_of_a_published_envelope
        FOREIGN KEY (public_envelope_id)
        REFERENCES publication.public_envelope (public_envelope_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

COMMENT ON TABLE publication.heartbeat IS
    'One row per successful publish. A cadence breach is an excessive interval between these rows, detected by a probe outside the container set (CD-AC-008).';

CREATE INDEX heartbeat_published_idx
    ON publication.heartbeat (published_utc DESC);
