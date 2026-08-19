-- migration: 4
-- name: dial_history
-- rollback: NONE. dial.history is the honest series (CD-AC-010); dropping it destroys the
--   claim it exists to support. Forward-only (PBG-DATA-002); recover by restore from dump.
--
-- BLUEPRINT §4, §7 and §8. The computed readings and their history.
--
-- ONE ROW PER DIAL PER EVALUATION, AND DELIBERATELY NOT ONE ROW PER EVALUATION.
--
-- There is no table here with a column for each dial, and no column anywhere in this
-- store named combined, overall, blended, composite or aggregate. A row shape carrying
-- both dials side by side is one `+` away from a headline number, and CD-AC-002 says the
-- two dials are never blended. The two readings meet at the serving layer, in a container
-- that computes nothing, and nowhere else. `DialSet` in code is a container with no
-- method returning a scalar; this table is its store-side equivalent — a series keyed by
-- dial_id, from which a caller who wants both must ask twice.
--
-- CD-AC-010, AND WHY first_published_utc IS DEFENDED TWICE.
--
-- "first_published_utc is set on insert and cannot be moved afterwards, which is the whole
-- of CD-AC-010's mechanism" (BLUEPRINT §4). Two independent instruments:
--
--   1. NO UPDATE OR DELETE GRANT on dial.history for any role (0007). An application role
--      cannot move it because an application role cannot issue UPDATE at all.
--   2. A BEFORE UPDATE trigger that refuses any statement changing the column. This one
--      also binds the table's OWNER and the migrator, who are not constrained by grants.
--
-- Instrument 1 alone would leave the owner able to rewrite history; instrument 2 alone
-- could be dropped by the owner. Neither is load-bearing by itself and that is the point
-- (BLUEPRINT §1). Assurance is invited to attack both.

SET timezone TO 'UTC';

CREATE TABLE dial.history (
    dial_history_id     bigint      GENERATED ALWAYS AS IDENTITY,
    dial_id             text        NOT NULL,
    state               text        NOT NULL,
    score               double precision,
    as_of_utc           timestamptz,
    since_utc           timestamptz,
    reason              text,
    inputs_used         text[]      NOT NULL,
    missing_inputs      text[]      NOT NULL,
    contributions       jsonb       NOT NULL,
    config_snapshot_id  text        NOT NULL,
    provenance          text        NOT NULL,
    evaluated_utc       timestamptz NOT NULL,
    first_published_utc timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT dial_history_pk PRIMARY KEY (dial_history_id),

    -- crash_detector.dials.dialset.DIAL_IDS. Two. A third is a PID amendment.
    CONSTRAINT dial_history_dial_admitted
        CHECK (dial_id IN ('equity_crash', 'monetary_debasement')),

    -- Reading := Value | Degraded | Unknown (crash_detector.dials.reading).
    CONSTRAINT dial_history_state_admitted
        CHECK (state IN ('VALUE', 'DEGRADED', 'UNKNOWN')),

    -- BLUEPRINT §8: LIVE rows are the live series; a backfilled point is available only
    -- through a separately named, separately labelled series. Because provenance is
    -- required on the row, a backfilled point cannot lose its label on the way to a chart.
    CONSTRAINT dial_history_provenance_admitted
        CHECK (provenance IN ('LIVE', 'BACKFILL')),

    CONSTRAINT dial_history_config_snapshot_named
        CHECK (length(btrim(config_snapshot_id)) > 0),

    CONSTRAINT dial_history_contributions_is_an_array
        CHECK (jsonb_typeof(contributions) = 'array'),

    -- Mirrors crash_detector.serving/engine freshness handling: a reading cannot be as-of
    -- a future instant relative to the evaluation that produced it. A future-dated row is
    -- permanently fresh, which is the cheapest way to make a stale dial read current.
    CONSTRAINT dial_history_not_future_dated
        CHECK (as_of_utc IS NULL OR as_of_utc <= evaluated_utc),

    -- THE DISCRIMINATED UNION, HELD IN THE STORE. CD-AC-001.
    --
    -- UNKNOWN declares NO SCORE — score IS NULL is a constraint, not a convention, so an
    -- unknown dial carrying a number is unrepresentable rather than merely discouraged.
    -- This mirrors contracts/public_envelope.schema.json, where the UNKNOWN branch
    -- declares no `score` property at all. Two independent refusals of the same shape.
    --
    -- VALUE requires at least one named input: a reading computed from nothing is
    -- Unknown, not a value. DEGRADED requires at least one named missing input and a
    -- reason: a reading with nothing missing is a Value, not a degradation.
    CONSTRAINT dial_history_state_fields_coherent CHECK (
        CASE state
            WHEN 'VALUE' THEN
                    score          IS NOT NULL
                AND as_of_utc      IS NOT NULL
                AND since_utc      IS NULL
                AND reason         IS NULL
                AND cardinality(inputs_used)    > 0
                AND cardinality(missing_inputs) = 0
            WHEN 'DEGRADED' THEN
                    score          IS NOT NULL
                AND as_of_utc      IS NOT NULL
                AND since_utc      IS NULL
                AND reason         IS NOT NULL
                AND length(btrim(reason)) > 0
                AND cardinality(missing_inputs) > 0
            WHEN 'UNKNOWN' THEN
                    score          IS NULL
                AND as_of_utc      IS NULL
                AND since_utc      IS NOT NULL
                AND reason         IS NOT NULL
                AND length(btrim(reason)) > 0
                AND cardinality(inputs_used) = 0
                AND contributions = '[]'::jsonb
            ELSE false
        END
    ),

    -- A score must be a real number. NaN is a double precision VALUE in PostgreSQL: it
    -- sorts greater than everything else, aggregates, and would render as a dial reading.
    --
    -- NOTE, AND IT IS THE REASON THIS IS WRITTEN THE WAY IT IS. PostgreSQL deliberately
    -- departs from IEEE 754 here: `'NaN'::float8 = 'NaN'::float8` is TRUE, so the
    -- idiomatic Python guard `score = score` admits NaN rather than refusing it. That
    -- version was written first, and it was a live PostgreSQL that refused to refuse the
    -- row — which is exactly why the migrations are applied against a real catalogue
    -- rather than reasoned about. The working form compares against the literal.
    CONSTRAINT dial_history_score_is_finite
        CHECK (score IS NULL OR (score <> 'NaN'::float8
                             AND score <> 'Infinity'::float8
                             AND score <> '-Infinity'::float8))
);

COMMENT ON TABLE dial.history IS
    'Computed dial readings, one row per dial per evaluation. Append-only: no UPDATE or DELETE grant for any role. There is no column here, and no table in this store, holding a combined or blended dial number (CD-AC-002).';
COMMENT ON COLUMN dial.history.state IS
    'VALUE | DEGRADED | UNKNOWN. UNKNOWN carries no score, enforced by dial_history_state_fields_coherent (CD-AC-001).';
COMMENT ON COLUMN dial.history.first_published_utc IS
    'Set on insert; cannot be moved afterwards. Defended by the absence of any UPDATE grant AND by dial_history_first_published_utc_is_immutable (CD-AC-010).';
COMMENT ON COLUMN dial.history.provenance IS
    'LIVE | BACKFILL. Required on the row so a backfilled point cannot lose its label on the way to a chart (BLUEPRINT §8).';
COMMENT ON COLUMN dial.history.config_snapshot_id IS
    'The run-level configuration that produced this reading, so it can be explained a year later without archaeology (Standards Baseline §10).';

CREATE INDEX dial_history_dial_asof_idx
    ON dial.history (dial_id, first_published_utc DESC);
CREATE INDEX dial_history_live_series_idx
    ON dial.history (dial_id, first_published_utc DESC)
    WHERE provenance = 'LIVE';

-- --------------------------------------------------------------------------------------
-- first_published_utc is immutable. Instrument 2.
-- --------------------------------------------------------------------------------------
-- Written to refuse the CLASS rather than the instance: it fires on ANY update of the
-- table and compares the column, so it catches a targeted `SET first_published_utc = ...`,
-- a whole-row rewrite, an UPDATE that touches other columns and happens to carry a
-- different value, and a rewrite performed by the owner. `IS DISTINCT FROM` rather than
-- `<>` so that a NULL on either side is still detected as a change.
--
-- It deliberately does NOT block updates to other columns. Blocking those is the grant
-- matrix's job, and a trigger that silently duplicated it would make the grant look
-- optional.
CREATE FUNCTION dial.refuse_moving_first_published_utc()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.first_published_utc IS DISTINCT FROM OLD.first_published_utc THEN
        RAISE EXCEPTION
            'dial.history.first_published_utc is immutable (CD-AC-010): attempted to '
            'move row % from % to %',
            OLD.dial_history_id, OLD.first_published_utc, NEW.first_published_utc
            USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END
$$;

REVOKE ALL ON FUNCTION dial.refuse_moving_first_published_utc() FROM PUBLIC;

CREATE TRIGGER dial_history_first_published_utc_is_immutable
    BEFORE UPDATE ON dial.history
    FOR EACH ROW
    EXECUTE FUNCTION dial.refuse_moving_first_published_utc();
