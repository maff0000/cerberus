"""The publication layer — **validate BOTH, then write** (BLUEPRINT §8, CD-AC-006, CD-AC-008).

    outcome = publish_cycle(connection,
                            public_envelope=public, private_envelope=private)
    outcome.heartbeat_written   # True on every successful publish (CD-AC-008)

===========================================================================================
*** THE ORDER IS THE CRITERION, AND IT IS ENFORCED BY THE SHAPE OF THIS FUNCTION ***
===========================================================================================
BLUEPRINT §8: *"The engine builds two envelopes per cycle and validates each against its own
closed schema before writing."*

**BOTH validations happen before EITHER write.** That is stronger than "each is validated
before it is written", and the difference is a real failure:

    validate(public) -> write(public) -> validate(private) -> REFUSE

leaves a published public envelope for a cycle whose private counterpart was never written.
The two surfaces then disagree about what happened in that cycle, permanently, and the
public one is the one consumers have already seen. So this function does all judging first
and all writing second, and **a refusal of either envelope means NEITHER is written and no
heartbeat is written.**

The two validations use **the two separate closed contracts** —
``contracts/public_envelope.schema.json`` and ``contracts/private_envelope.schema.json`` —
through the existing :func:`~crash_detector.publication.envelope_contract.refuse_unless_publishable`
door with its own ``EnvelopeSurface``. There is deliberately no "both" and no "either"
surface, and this module does not add one.

===========================================================================================
THE HEARTBEAT — ``CD-AC-008``, AND IT IS THE THING THAT DID NOT EXIST
===========================================================================================
``publication.heartbeat`` landed with migration 5 at WO-2 and **nothing has ever written to
it**, measured at this increment's base::

    grep -rn "heartbeat" src/ --include=*.py   ->  no matches, exit 1

**THIS FUNCTION IS THAT WRITER.** One row per successful publish, inside the same
transaction as the envelopes, with a foreign key to the public envelope it attests. Inside
the transaction on purpose: a heartbeat that commits when the envelope did not is a
heartbeat claiming a publish that did not happen, and that is the one lie this table exists
to make impossible.

Whether an interval between those rows is EXCESSIVE is
:mod:`crash_detector.publication.cadence`'s, and that module cannot see the age of a number.

===========================================================================================
A REFUSAL IS AN ALERT, AND THE ALERT IS WRITTEN EVEN THOUGH NOTHING IS PUBLISHED
===========================================================================================
BLUEPRINT §10 lists publication refusal as one of the three routes to ``alert.event``, and
migration 6 calls it *"the store-side refusal that CD-AC-006 turns into an alert"*.

**SO ON A REFUSAL EXACTLY ONE ROW IS WRITTEN, AND IT IS AN ALERT, NOT AN ENVELOPE.** Stated
plainly because ``PublicationRefused``'s own message ends *"Nothing was published"*, which is
true of the envelope tables and would be misread as "nothing was written at all". The
outcome is:

* ``publication.public_envelope``  — **nothing**
* ``publication.private_envelope`` — **nothing**
* ``publication.heartbeat``        — **nothing**
* ``alert.event``                  — **one row**, class ``PUBLICATION_REFUSAL``

The alert's ``subject_ref`` is built from the refusal's ``reason_class``, JSON POINTER and
KEY NAME. **Never from a value** — that is exactly what
:class:`~crash_detector.publication.envelope_contract.PublicationRefused` was designed to
carry, and it is why this module can reference the failure at all (``PBG-SEC-002``).

**AND THE ALERT IS WRITTEN AND COMMITTED BEFORE THE REFUSAL IS RE-RAISED**, because *"durable
rows first, so no alert is lost while the channel is decided"* (``Q26``,
``PO-DECISIONS-0024`` ruling 3). If writing the alert itself fails, the original refusal is
still raised — a failure to record a failure must not replace it with a different one.

===========================================================================================
NO DRIVER IMPORT, NO SOCKET, NO SOURCE
===========================================================================================
Takes an already-open PEP 249 connection, the approach the store's migration module takes
and states the reason for: it keeps ``src/`` free of a database driver import and lets this
be tested against a recording double that captures the exact statements and their ORDER —
which is how "validated before written" is measured rather than asserted.

(That module is named in prose here without its dotted path on purpose.
``tests/test_store_schema_sql.py::test_the_migration_step_is_not_the_application_startup_path``
scans the source as TEXT for the package path, so writing it out would report this module as
reaching the migration step on the strength of a sentence saying it does not. The control is
correct about the thing it guards and is left exactly as it stands; the imprecision is raised
as a finding rather than repaired under this dispatch — see ``CD-ENG-WO3-02-F02``.)

**NOTHING HERE REGISTERS A SOURCE.** The ingredient set is held with the Product Authority
(``CD-D-005`` / ``Q25``); this module never touches ``raw.source_registry``, constructs no
``SourceRecord``, and reads ``inputs_used`` only as opaque strings the caller's envelope
already carried past its own closed schema.

===========================================================================================
DECLARED LIMIT (CD-RULE-004).
===========================================================================================
 1  **THIS IS THE PUBLICATION LAYER, NOT THE ENVELOPE BUILDER.** It judges and writes two
    candidate documents; it does not compute them. Building an envelope from readings needs
    readings, readings need registered sources, and there are none (``Q25``). **NOT PROVED TO
    BE CARRIED ANYWHERE** — the builder is owed with the source set, and until it exists no
    envelope in this system has a provenance this module could check.

 2  **SUPERSEDED AT WO-3 INCREMENTS 16A AND 16A-FIX. THE CORRECTION IS STATED, NOT EDITED
    AWAY** (``PBG-CONT-003``: corrections supersede, never delete).

    **WHAT THIS LIMIT SAID, VERBATIM:**

        *"``detail_level`` IS NOT ON EITHER SURFACE AND IS NOT WRITTEN BY THIS MODULE. Both
        closed schemas record it as 'DELIBERATELY ABSENT AND OWED', and adding it is an
        allowlist edit with a ``schema_version`` bump. The proportionality RULE is
        implemented in exactly one place — :mod:`crash_detector.publication.detail_level` —
        and is not wired into the envelope, because where it attaches is a question with a
        ``CD-AC-002`` consequence that this seat raised rather than answered. See that
        module and the Build Log finding ``CD-ENG-WO3-02-F03``."*

    **THAT WAS TRUE WHEN WRITTEN AT INCREMENT 15. ITS FIRST CLAUSE IS NOW FALSE.**
    ``CD-ENG-WO3-02-F03`` was RULED by ``PO-DECISIONS-0025`` ruling 5 (``Q29``):
    *"detail_level attaches PER-DIAL."* Increment 16A paid the wiring — the key is declared
    inside ``$defs/dial_reading`` in **both** closed contracts and required in every branch
    of the ``VALUE | DEGRADED | UNKNOWN`` union — and bumped ``schema_version``
    ``1.0.0 -> 1.1.0`` in both. **``detail_level`` IS THEREFORE ON BOTH SURFACES'
    CONTRACTS.** Increment 16A-FIX then narrowed ``DEGRADED`` and ``UNKNOWN`` to
    ``$defs/absent_data_detail_level`` (``elevated | acute``), because 16A had left ``calm``
    admissible on exactly the two branches PID §3.2 forbids it on (``CD-ASR-WO3-03``,
    ``RED``).

    *** **WHAT REMAINS TRUE IS THE HALF THAT CONCERNS THIS MODULE: IT STILL DOES NOT WRITE
    THE FIELD, AND NO SURFACE RECEIVES IT.** *** :func:`publish_cycle` does not compute a
    ``detail_level``. It judges and writes whatever candidate mapping it is handed — and it
    is handed nothing, because **``publish_cycle`` HAS ZERO CALLERS and ``src/`` HAS NO
    ENTRYPOINT** (``CD-PL-F167``; ``CD-ASR-WO3-02`` F01: *"a writer with no caller"*).

    **AND THE ZERO-CALLER CLAIM IS MEASURED OVER THE WHOLE REPOSITORY, NOT JUST ``src/``,
    BECAUSE ``src/`` IS NOT WHERE THE ENTRYPOINTS ARE.** ``deploy/entrypoints/`` holds six
    service entrypoints (``cd_engine.py``, ``cd_public.py``, ``cd_private.py``,
    ``cd_collectors.py``, ``cd_witness.py``, ``cd_review.py``) and the Dockerfiles name
    them, so *"``src/`` has no entrypoint"* — true, and the project's standing phrasing —
    can mislead a reader into thinking no entrypoint exists anywhere. Each of those six is
    a thin shim calling ``_service.boot``; **not one of them reaches this module.** Outside
    ``tests/`` the only occurrences of ``publish_cycle`` in the repository are this file's
    own docstring example, ``__all__``, the ``def``, prose in
    :mod:`~crash_detector.publication.detail_level`, a quarantined ``plants/`` patch and
    Build Log prose. **THE IMAGES ARE WRITTEN AND NOT BUILT**
    (``CONTAINER_READY_DESIGN`` / ``CONTAINER_BUILD_NOT_YET_AUTHORISED``).

    *** **A SCHEMA IS NOT A SURFACE**, and that distinction is the whole of this
    correction: the field is in the CONTRACT, so a candidate carrying it is now JUDGED —
    including the ``calm``-on-missing-data refusal 16A-FIX added — and the field still
    reaches no reader, because nothing publishes. ***

    **NOT PROVED TO BE CARRIED ANYWHERE**, and the caller is deliberately NOT written here.
    The health surface's value axis is still open (``CD-AC-006`` wearing an ops hat) and it
    blocks the moment any transport exists, so that residual and ``CD-PL-F167`` must land
    together and neither may land alone.

 3  **ONE TRANSACTION, AND THE COMMIT IS THE CALLER'S ONLY ATOMICITY GUARANTEE.** The three
    inserts are issued without an intervening commit and committed together, so PostgreSQL
    gives them atomically. Against a connection in autocommit mode they are three separate
    transactions and a crash between them leaves an envelope with no heartbeat.
    **NOT PROVED TO BE CARRIED ANYWHERE** — no live PostgreSQL exists on this lane and the
    container set is not built (``CONTAINER_READY_DESIGN``). Measured only against a
    recording double, which records the statement ORDER faithfully and knows nothing about
    isolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from crash_detector.publication.alerting import (
    ALERT_CRITICAL,
    ALERT_PUBLICATION_REFUSAL,
    RAISED_BY_ENGINE,
    SUBJECT_REF_MAX_LENGTH,
    raise_alert,
)
from crash_detector.publication.envelope_contract import (
    EnvelopeSurface,
    PublicationRefused,
    refuse_unless_publishable,
)

__all__ = [
    "PUBLIC_ENVELOPE_INSERT",
    "PRIVATE_ENVELOPE_INSERT",
    "HEARTBEAT_INSERT",
    "PublishOutcome",
    "publish_cycle",
    "refusal_subject_ref",
]

#: ``RETURNING`` the identity, because the heartbeat's foreign key needs it and reading it
#: back with a second ``SELECT max(...)`` would be a race with any concurrent publisher.
PUBLIC_ENVELOPE_INSERT = (
    "INSERT INTO publication.public_envelope "
    "(schema_version, as_of_utc, published_utc, config_snapshot_id, envelope) "
    "VALUES (%s, %s, %s, %s, %s) RETURNING public_envelope_id"
)

PRIVATE_ENVELOPE_INSERT = (
    "INSERT INTO publication.private_envelope "
    "(schema_version, classification, as_of_utc, published_utc, config_snapshot_id, "
    "envelope) VALUES (%s, %s, %s, %s, %s, %s)"
)

#: CD-AC-008. One row per successful publish, attesting the envelope it was written for.
HEARTBEAT_INSERT = (
    "INSERT INTO publication.heartbeat (published_utc, public_envelope_id) "
    "VALUES (%s, %s)"
)


@dataclass(frozen=True)
class PublishOutcome:
    """What one publication cycle actually wrote."""

    #: SEALED (PO-DECISIONS-0016 ruling 2).
    __slots__ = (
        "public_envelope_id",
        "public_written",
        "private_written",
        "heartbeat_written",
    )

    public_envelope_id: object
    public_written: bool
    private_written: bool
    heartbeat_written: bool

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(f"{cls.__name__} may not subclass PublishOutcome.")


def refusal_subject_ref(refusal: PublicationRefused) -> str:
    """A bounded reference to a refusal, built from CLASSIFICATION and LOCATION only.

    ``reason_class``, the RFC 6901 JSON pointer and the offending KEY NAME. **No value from
    the candidate envelope appears in it** — ``PublicationRefused`` is built so that none is
    available to appear, which is what makes this reference safe to put in an append-only
    table nobody holds a ``DELETE`` grant on.

    Truncated to the store's 200-character bound at the POINTER end rather than refused,
    because a refusal-to-alert-about-a-refusal loses the alert; the reason class and surface
    are kept whole so the truncated form still says what happened.
    """
    parts = [refusal.surface.value, refusal.reason_class]
    if refusal.key:
        parts.append(f"key={refusal.key}")
    if refusal.pointer:
        parts.append(f"at={refusal.pointer}")
    reference = "|".join(parts)
    return reference[:SUBJECT_REF_MAX_LENGTH]


def publish_cycle(
    connection: Any,
    *,
    public_envelope: Mapping,
    private_envelope: Mapping,
) -> PublishOutcome:
    """Publish one cycle: judge both envelopes, then write both plus the heartbeat.

    Raises :exc:`~crash_detector.publication.envelope_contract.PublicationRefused` if either
    candidate fails its own closed contract, having written **no envelope and no heartbeat**
    and **one** ``alert.event`` row.

    The inserted columns are read OUT OF the envelope documents rather than taken as
    separate parameters. That is deliberate: ``public_envelope_columns_agree_with_document``
    is a CHECK constraint in migration 5, and a signature that let a caller pass a
    ``schema_version`` differing from the document's would let them build the row the
    constraint exists to refuse. Here the two cannot disagree because there is only one
    source for both.
    """
    # ------------------------------------------------------------------ JUDGE. BOTH. FIRST.
    try:
        refuse_unless_publishable(public_envelope, surface=EnvelopeSurface.PUBLIC)
        refuse_unless_publishable(private_envelope, surface=EnvelopeSurface.PRIVATE)
    except PublicationRefused as refusal:
        # Durable row first (Q26). A failure to RECORD the failure must not replace it: the
        # original refusal is raised either way, and the alerting failure is chained onto it
        # rather than substituted for it.
        try:
            raise_alert(
                connection,
                event_class=ALERT_PUBLICATION_REFUSAL,
                severity=ALERT_CRITICAL,
                raised_by=RAISED_BY_ENGINE,
                subject_ref=refusal_subject_ref(refusal),
            )
        except Exception as alerting_failure:
            raise refusal from alerting_failure
        raise

    # --------------------------------------------------------- ONLY NOW DOES ANYTHING WRITE.
    with connection.cursor() as cursor:
        cursor.execute(
            PUBLIC_ENVELOPE_INSERT,
            (
                public_envelope["schema_version"],
                public_envelope["as_of_utc"],
                public_envelope["published_utc"],
                public_envelope["config_snapshot_id"],
                _document(public_envelope),
            ),
        )
        returned = cursor.fetchone()
        public_envelope_id = returned[0] if returned is not None else None

        cursor.execute(
            PRIVATE_ENVELOPE_INSERT,
            (
                private_envelope["schema_version"],
                private_envelope["classification"],
                private_envelope["as_of_utc"],
                private_envelope["published_utc"],
                private_envelope["config_snapshot_id"],
                _document(private_envelope),
            ),
        )

        # *** CD-AC-008. THE ROW NOTHING HAS EVER WRITTEN. ***
        cursor.execute(
            HEARTBEAT_INSERT,
            (public_envelope["published_utc"], public_envelope_id),
        )

    connection.commit()

    return PublishOutcome(
        public_envelope_id=public_envelope_id,
        public_written=True,
        private_written=True,
        heartbeat_written=True,
    )


def _document(envelope: Mapping) -> dict:
    """A plain ``dict`` copy of the validated candidate, for the ``jsonb`` column.

    A copy because the caller keeps a reference to what they passed in, and a mapping that
    is mutated between validation and serialisation is a document that was judged in one
    shape and stored in another. ``dict(...)`` and not ``copy.deepcopy``: the candidate has
    already passed ``_refuse_non_json``, so every nested value is a JSON primitive,
    ``list`` or ``Mapping`` and none of them carries behaviour that a deep copy would need
    to preserve.
    """
    return dict(envelope)
