"""``alert.event`` — **the durable row IS the alert** (BLUEPRINT §10, ``Q26`` ruled).

    raise_alert(connection, event_class=ALERT_CADENCE_BREACH, severity=ALERT_CRITICAL,
                raised_by=RAISED_BY_ENGINE, subject_ref="heartbeat:open_interval")

===========================================================================================
*** WHAT ``Q26`` RULED, AND WHAT THIS MODULE THEREFORE DOES NOT CONTAIN ***
===========================================================================================
``PO-DECISIONS-0024`` ruling 3: the detector is advisory, so **alerts surface on the
publication surface and on a machine-readable state endpoint, with NO EXTERNAL PUSH CHANNEL
until the Product Authority names one.**

    *** THERE IS NO EMAIL, WEBHOOK, DISCORD, SLACK, SMS OR OUTBOUND HTTP IN THIS PACKAGE.
        NOT BEHIND A FEATURE FLAG, NOT DISABLED BY DEFAULT, AND NOT "READY TO ENABLE". ***

A disabled-by-default push channel is not the absence of a channel; it is a channel plus a
boolean, and the boolean is what somebody flips at 2am. The ruling says the channel is *"a
one-line addition when he says so"*. **This module is built so that it is one line — a new
reader of :func:`recent_alerts` — and that line is not written here.**

**IT IS ALSO STRUCTURAL, NOT A PROMISE.** Nothing under ``src/`` may import a socket, an
HTTP client or a name resolver, and ``tests/test_collector_boundaries.py`` asserts it over
the whole package by walking the source — including function-local imports, because *"a
deferred import reaches the network exactly as well as a module-level one"*. So the absence
of a push channel here is carried by an existing instrument that fails, not by this
paragraph. ``tests/test_no_external_push.py`` adds the arm specific to this ruling.

Egress is separately constrained: ``deploy/egress-destinations.yaml`` is a deny-by-default
registry and ``cd-engine``'s ``x-egress`` policy is ``NONE`` with an empty host list. **THIS
SEAT DID NOT WIDEN IT AND HAD NO OCCASION TO** — see the Build Log.

===========================================================================================
THE ROW CARRIES A CLASSIFICATION AND A REFERENCE, NEVER A VALUE (``PBG-SEC-002``)
===========================================================================================
Migration 6 states the reason and it is the same one ``raw.observation`` has no detail
column: *"the natural content of an alert message is the thing that went wrong, and the
thing that went wrong is routinely a request, a response or a key that failed validation —
exactly the places a credential travels."*

So there is **no free-text body parameter on this function**, and ``subject_ref`` is checked
here before it reaches the store: bounded at 200, and refused outright if
:func:`~crash_detector.publication.classification.classify_key` says any token in it is
secret-bearing. That reuses the existing door rather than building a second one beside it.

===========================================================================================
THE CLOSED SETS ARE THE STORE'S OWN, RESTATED SO A REFUSAL CAN NAME THE REASON
===========================================================================================
``alert.event`` carries CHECK constraints on ``event_class``, ``severity`` and ``raised_by``.
Those are the boundary of record and they hold whatever process writes the row, including a
direct ``INSERT``. The sets below mirror them so that a violation is refused **before** a
statement is issued, with a message that names which vocabulary was breached — a driver's
constraint-violation error names the constraint, and this project does not carry a driver's
error text into a governed record because a driver error can quote the failing statement.

A test asserts the sets here and the SQL in ``db/migrations/0006_private_and_alert.sql``
agree, by reading both files, so drift is a failing test rather than a discovery in
production. **The store is the authority; this is the second statement of it, and neither is
sole.**
"""

from __future__ import annotations

from typing import Any, Tuple

from crash_detector.publication.classification import (
    CLASSIFICATION_SECRET_BEARING,
    classify_key,
)

__all__ = [
    "ALERT_CADENCE_BREACH",
    "ALERT_WITNESS_DIVERGENCE",
    "ALERT_PUBLICATION_REFUSAL",
    "ALERT_COLLECTION_DEGRADED",
    "ALERT_EVENT_CLASSES",
    "ALERT_INFO",
    "ALERT_WARNING",
    "ALERT_CRITICAL",
    "ALERT_SEVERITIES",
    "RAISED_BY_ENGINE",
    "RAISED_BY_WITNESS",
    "ALERT_RAISERS",
    "SUBJECT_REF_MAX_LENGTH",
    "ALERT_EVENT_INSERT",
    "AlertRefused",
    "raise_alert",
    "recent_alerts",
]

#: BLUEPRINT §10's three routes plus the store-side refusal CD-AC-006 turns into an alert.
#: A fifth class is a deliberate migration, not a free string: an alert class nobody declared
#: is an alert nobody has a response for.
ALERT_CADENCE_BREACH = "CADENCE_BREACH"
ALERT_WITNESS_DIVERGENCE = "WITNESS_DIVERGENCE"
ALERT_PUBLICATION_REFUSAL = "PUBLICATION_REFUSAL"
ALERT_COLLECTION_DEGRADED = "COLLECTION_DEGRADED"

ALERT_EVENT_CLASSES: Tuple[str, ...] = (
    ALERT_CADENCE_BREACH,
    ALERT_WITNESS_DIVERGENCE,
    ALERT_PUBLICATION_REFUSAL,
    ALERT_COLLECTION_DEGRADED,
)

ALERT_INFO = "INFO"
ALERT_WARNING = "WARNING"
ALERT_CRITICAL = "CRITICAL"
ALERT_SEVERITIES: Tuple[str, ...] = (ALERT_INFO, ALERT_WARNING, ALERT_CRITICAL)

#: The two roles BLUEPRINT §4 names as writers of the ``alert`` schema. Note that the
#: EXTERNAL PROBE IS NOT ONE OF THEM and cannot be: it holds no database credential at all,
#: which is the property that makes it external (``PBG-EVID-001``).
RAISED_BY_ENGINE = "cd_engine"
RAISED_BY_WITNESS = "cd_witness"
ALERT_RAISERS: Tuple[str, ...] = (RAISED_BY_ENGINE, RAISED_BY_WITNESS)

#: Migration 6: ``CHECK (subject_ref IS NULL OR length(subject_ref) <= 200)``.
SUBJECT_REF_MAX_LENGTH = 200

ALERT_EVENT_INSERT = (
    "INSERT INTO alert.event (event_class, severity, raised_by, subject_ref) "
    "VALUES (%s, %s, %s, %s)"
)

_RECENT_ALERTS_SELECT = (
    "SELECT event_class, severity, raised_utc, raised_by, subject_ref "
    "FROM alert.event ORDER BY raised_utc DESC LIMIT %s"
)


class AlertRefused(ValueError):
    """An alert was offered in a shape ``alert.event`` does not admit.

    **This is not a way to lose an alert.** It refuses the DESCRIPTION, not the event: every
    caller in this package builds its description from closed vocabulary and a reference it
    constructed, so reaching this exception means a programming error at the raising site
    rather than an alert that had nowhere to go.
    """


def raise_alert(
    connection: Any,
    *,
    event_class: str,
    severity: str,
    raised_by: str,
    subject_ref: "str | None" = None,
) -> None:
    """Append one durable ``alert.event`` row. **The row IS the alert.**

    Takes an already-open PEP 249 connection, which is what keeps the whole of ``src/`` free
    of a database driver import and lets this be tested against a recording double that
    captures the exact statement issued (the store's migration module takes the same approach
    and says why; its dotted path is deliberately not written out here — see the note in
    :mod:`crash_detector.publication.publish`).

    **There is no ``message`` or ``detail`` parameter, deliberately.** See the module
    docstring: a free-text body is where a credential travels.

    Commits, because an alert that is lost when the caller's later work fails is an alert
    that was raised about a failure and then destroyed by it. Append-only: no role holds
    ``UPDATE`` or ``DELETE`` on this table, so a row can be superseded but never marked away.
    """
    if event_class not in ALERT_EVENT_CLASSES:
        raise AlertRefused(
            f"{event_class!r} is not a declared alert class. The closed set is "
            f"{list(ALERT_EVENT_CLASSES)} and it is an allowlist held here and in the "
            "alert.event CHECK constraint. A fifth class is a deliberate migration: an "
            "alert class nobody declared is an alert nobody has a response for."
        )
    if severity not in ALERT_SEVERITIES:
        raise AlertRefused(
            f"{severity!r} is not a declared severity. The closed set is "
            f"{list(ALERT_SEVERITIES)}."
        )
    if raised_by not in ALERT_RAISERS:
        raise AlertRefused(
            f"{raised_by!r} may not raise an alert. The closed set is "
            f"{list(ALERT_RAISERS)} — the two roles BLUEPRINT §4 names as writers of the "
            "alert schema. A process outside the container set is not among them and "
            "cannot be: it holds no database credential, which is the property that makes "
            "it external evidence (PBG-EVID-001)."
        )

    if subject_ref is not None:
        if type(subject_ref) is not str:
            raise AlertRefused(
                "subject_ref is an identifier or a KEY NAME and must be a plain str, got "
                f"{type(subject_ref).__name__}."
            )
        if len(subject_ref) > SUBJECT_REF_MAX_LENGTH:
            raise AlertRefused(
                f"subject_ref is {len(subject_ref)} characters and the bound is "
                f"{SUBJECT_REF_MAX_LENGTH}. REFUSED rather than truncated: a truncated "
                "reference is a reference to something else, and it would be silently "
                "wrong at exactly the moment somebody was following it."
            )
        # The existing door. A reference is a NAME; if the vocabulary says the name itself
        # is secret-bearing then whatever is behind it is a credential, and a credential is
        # never carried in a record (PBG-SEC-002, non-waivable).
        classified = classify_key(subject_ref)
        if classified is not None and classified[0] == CLASSIFICATION_SECRET_BEARING:
            raise AlertRefused(
                f"the token {classified[1]!r} classifies this subject_ref as "
                "secret-bearing. alert.event is APPEND-ONLY and no role holds a DELETE "
                "grant, so a secret written here cannot be removed. The reference is "
                "refused; the VALUE is not reproduced in this message either."
            )

    with connection.cursor() as cursor:
        cursor.execute(
            ALERT_EVENT_INSERT, (event_class, severity, raised_by, subject_ref)
        )
    connection.commit()


def recent_alerts(connection: Any, *, limit: int = 20) -> tuple:
    """The most recent alert rows, newest first — **a READ, and the only kind there is.**

    This is the whole of the surfacing mechanism ``Q26`` ruled for. The publication surface
    and the machine-readable state endpoint both render what this returns; **nothing pushes
    it anywhere.** When the Product Authority names a channel, the addition is a new reader
    of this function, and that is what "a one-line addition" means.
    """
    if type(limit) is not int or limit < 1:
        raise AlertRefused(
            f"limit must be a positive plain int, got {limit!r}."
        )
    with connection.cursor() as cursor:
        cursor.execute(_RECENT_ALERTS_SELECT, (limit,))
        return tuple(cursor.fetchall())
