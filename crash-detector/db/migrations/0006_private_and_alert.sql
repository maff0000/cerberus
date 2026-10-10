-- migration: 6
-- name: private_and_alert
-- rollback: NONE. alert.event is append-only durable evidence that an alert was raised;
--   dropping it loses alerts that were never actioned. Forward-only (PBG-DATA-002).
--
-- BLUEPRINT §4 and §10.
--
-- SCHEMA `private` CARRIES NO TABLE IN WO-2, AND THAT IS A REFUSAL RATHER THAN AN
-- OMISSION.
--
-- BLUEPRINT §4 describes the schema as "anything book-adjacent" and names nothing
-- concrete. Deciding WHAT is book-adjacent — which positions, which exposures, which
-- account facts — is product meaning, and product meaning is the Product Owner's
-- (PBG-AUTH-005). An Engineer seat inventing a `private.position` table would be
-- inventing the very category the public/private boundary exists to protect, and would
-- then have built a boundary around a guess.
--
-- The schema, its revoke-by-default posture and cd_private's grants are all created now,
-- because the BOUNDARY is structural from the first commit (BLUEPRINT §13: retrofitting a
-- trust boundary is how trust boundaries end up leaky). What is owed is the content.
-- 0007's ALTER DEFAULT PRIVILEGES is what makes "SELECT and INSERT on private.*" true of
-- tables that do not exist yet, so the first book-adjacent table added in a later work
-- order arrives already inside the boundary rather than needing to be remembered into it.

SET timezone TO 'UTC';

-- --------------------------------------------------------------------------------------
-- alert.event — alerts are durable rows FIRST.
-- --------------------------------------------------------------------------------------
-- BLUEPRINT §10. Notification transport is deliberately not fixed yet; the durable row
-- means no alert is lost while that is decided. Append-only: no UPDATE or DELETE grant
-- for any role, so an alert cannot be marked away, only superseded by a later row.
--
-- NO FREE-TEXT BODY, FOR THE SAME REASON raw.observation HAS NO DETAIL COLUMN.
--
-- The natural content of an alert message is the thing that went wrong, and the thing
-- that went wrong is routinely a request, a response or a key that failed validation —
-- exactly the places a credential travels (PBG-SEC-002, non-waivable). This table
-- therefore carries CLASSIFICATION and a REFERENCE, never a value:
--
--   event_class   a named member of a closed set
--   subject_ref   an identifier or a KEY NAME — the name of the refused envelope key, a
--                 source_id, an envelope id. Never the value behind it. Bounded at 200.
--
-- An operator who needs the value looks it up under their own authority, from the row the
-- reference names. That is one extra step, and it is the step that keeps a secret out of
-- an append-only store that nobody holds a DELETE grant on.
CREATE TABLE alert.event (
    alert_event_id bigint      GENERATED ALWAYS AS IDENTITY,
    event_class    text        NOT NULL,
    severity       text        NOT NULL,
    raised_utc     timestamptz NOT NULL DEFAULT now(),
    raised_by      text        NOT NULL,
    subject_ref    text,

    CONSTRAINT alert_event_pk PRIMARY KEY (alert_event_id),

    -- The three routes BLUEPRINT §10 names, plus the store-side refusal that CD-AC-006
    -- turns into an alert. A fourth class is a deliberate migration, not a free string:
    -- an alert class nobody declared is an alert nobody has a response for.
    CONSTRAINT alert_event_class_admitted CHECK (
        event_class IN (
            'CADENCE_BREACH',
            'WITNESS_DIVERGENCE',
            'PUBLICATION_REFUSAL',
            'COLLECTION_DEGRADED'
        )
    ),

    CONSTRAINT alert_event_severity_admitted
        CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),

    -- Only the two roles BLUEPRINT §4 names as writers of this schema. Recorded on the
    -- row as well as enforced by grant, so the row is self-describing in a dump.
    CONSTRAINT alert_event_raised_by_admitted
        CHECK (raised_by IN ('cd_engine', 'cd_witness')),

    CONSTRAINT alert_event_subject_ref_bounded
        CHECK (subject_ref IS NULL OR length(subject_ref) <= 200)
);

COMMENT ON TABLE alert.event IS
    'Append-only alert events (BLUEPRINT §10). No UPDATE or DELETE grant for any role. Carries classification and a reference, never a value (PBG-SEC-002).';
COMMENT ON COLUMN alert.event.subject_ref IS
    'An identifier or key NAME — never the value behind it. Bounded at 200 characters.';

CREATE INDEX alert_event_raised_idx
    ON alert.event (raised_utc DESC);
CREATE INDEX alert_event_class_raised_idx
    ON alert.event (event_class, raised_utc DESC);
