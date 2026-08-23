"""The health surface — **detector health, never market information** (CD-AC-014, §10).

    document = health_document(live=True, last_publication_utc=..., regime="CALM",
                               degraded_classes=(DEGRADED_CADENCE_BREACH,))
    refuse_unless_health_safe(document)      # raises; returns nothing to publish

===========================================================================================
*** THE MISTAKE THIS MODULE EXISTS TO MAKE UNREPRESENTABLE ***
===========================================================================================
A health endpoint that leaks a dial value, a witness reading, a source name or a
private-envelope key is a ``CD-AC-006`` breach wearing an ops hat. **And it is a genuinely
easy mistake, because "degraded" is tempting to explain with the number that degraded:**

    {"degraded": true, "equity_crash_score": 0.87}          <- the temptation
    {"degraded": true, "degraded_classes": ["DIAL_STALE"]}  <- the rule

    *** EXPLAIN IT WITH A CLASS. NEVER WITH A VALUE. ***

An operator needs to know *that* a dial is stale and *which kind* of thing is wrong, so they
can act. They do not need the number, and the endpoint is **unauthenticated** — BLUEPRINT
§10 requires that, because a health surface you have to hold a credential to read is a
health surface an outside party cannot use to detect that you are down, which is the whole
of ``CD-AC-014``.

So the unauthenticated surface is exactly the reason the content rule has to be absolute.

===========================================================================================
TWO INDEPENDENT REFUSALS, AS THE ENVELOPE HAS
===========================================================================================
``BLUEPRINT`` §3 holds the public/private boundary in five independent places and says why:
either alone is a single point of failure for the product's most consequential criterion.
This surface is held in two, and **the first needs no vocabulary to work**:

1. **THE CLOSED ALLOWLIST.** :data:`HEALTH_KEYS` is total. ``equity_crash``,
   ``monetary_debasement``, ``score``, ``divergence_measure``, ``inputs_used`` and every
   other name are refused not because anything was recognised about them but because they
   are **not on the list**. A key nobody declared cannot be served even if something
   computed it, and renaming it does not get it past.

2. **THE CLASSIFICATION REGISTER**, reused rather than rebuilt:
   :func:`~crash_detector.publication.classification.classify_key` and its recursive
   :func:`~crash_detector.publication.classification.iter_keys` scan. It names the REASON —
   *"``portfolio_value`` is a private-classified key"* is actionable where *"not on the
   allowlist"* sends an engineer to add it to the allowlist, which is the wrong repair —
   and it fires at every depth, because a key nested inside an object is exactly as served
   as one at the root.

**AND A THIRD, SPECIFIC TO THIS SURFACE:** :data:`DEGRADED_CLASSES` is a closed vocabulary,
so ``degraded_classes`` cannot become a free-text field that an engineer eventually writes a
number into. That is the same argument ``alert.event`` makes for having no free-text body.

===========================================================================================
THE SAME SAFETY PROPERTY HOLDS ON THE MACHINE-READABLE STATE ENDPOINT (``Q26``)
===========================================================================================
``PO-DECISIONS-0024`` ruling 3 puts alerts on the publication surface **and** on a
machine-readable state endpoint. :func:`state_document` builds that one, and it goes through
**the same** :func:`refuse_unless_health_safe`, against the same allowlist discipline.

**IT SURFACES ``event_class``, ``severity`` AND ``raised_utc``, AND DELIBERATELY NOT
``subject_ref``.** A subject reference is a key NAME or an identifier — safe in an
operator's view, and ``alert.event`` is careful that it is never a value — but a
``source_id`` is exactly the kind of identifier that legitimately appears there, and a
**source name is market information** that ``Q25`` has not even decided yet. On an
unauthenticated surface the reference is dropped. An operator who needs it reads the row
under their own authority, which is the one extra step migration 6 already requires for the
same reason.

===========================================================================================
WHAT THIS MODULE IS NOT
===========================================================================================
**IT BINDS NO PORT AND OPENS NO SOCKET.** Nothing under ``src/`` may import a socket, an HTTP
client or a name resolver — ``tests/test_collector_boundaries.py`` asserts it over the whole
package, including function-local imports. This module builds a document and refuses a
document. **Serving it is transport and lives outside the package**; the thing that reads it
from outside is ``tools/probe/external_probe.py``, which is not in the container set at all.

That split is not an inconvenience worked around. It is why the proportionality rule and the
safety rule are *"testable without a browser"* (BLUEPRINT §8's phrase for the same split on
the envelope).

===========================================================================================
DECLARED LIMIT (CD-RULE-004).
===========================================================================================
 1  **THE ALLOWLIST IS TOTAL FOR KEYS AND SAYS NOTHING ABOUT VALUES.** ``regime`` is a
    declared string field, so a caller that writes a dial score into it as text —
    ``regime="0.87"`` — publishes a number through a key that is legitimately a string.
    This is the identical residue the public envelope schema declares about
    ``equity_crash.score``, and the identical answer: the closed vocabulary
    :data:`DEGRADED_CLASSES` closes it for the degradation fields, and ``regime`` is
    constrained to a declared regime name by
    :data:`~crash_detector.regime.REGIME_ORDER` — MEASURED, both arms, in
    ``tests/test_health_surface.py``. **For a value smuggled through a field whose type it
    matches and whose vocabulary it satisfies: NOT PROVED TO BE CARRIED ANYWHERE.**

 2  **THIS MODULE JUDGES A DOCUMENT AND SERVES NOTHING.** Whether the served bytes are the
    document that was judged depends on the transport, and there is no transport: the
    container set is not built (``CONTAINER_READY_DESIGN``). **NOT PROVED TO BE CARRIED
    ANYWHERE** for any deployed surface.

 3  **LIVENESS IS REPORTED BY THE THING WHOSE LIVENESS IT IS**, and that is
    self-certification if it is the only reading taken (``PBG-EVID-001``). It is not: the
    external probe reaches its verdict from OUTSIDE, and a probe that cannot connect at all
    reports ``DOWN`` **without needing any process inside the system to agree**. The
    document is the system's own account; the probe's exit code is the independent one.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Tuple

from crash_detector.publication.classification import (
    CLASSIFICATION_SECRET_BEARING,
    classify_key,
    iter_keys,
)
from crash_detector.regime import REGIME_ORDER

__all__ = [
    "HEALTH_SCHEMA_VERSION",
    "HEALTH_KEYS",
    "STATE_KEYS",
    "DEGRADED_NONE",
    "DEGRADED_PUBLICATION_HALTED",
    "DEGRADED_CADENCE_BREACH",
    "DEGRADED_EVALUATION_HALTED",
    "DEGRADED_INPUTS_INCOMPLETE",
    "DEGRADED_WITNESS_UNAVAILABLE",
    "DEGRADED_CLASSES",
    "HealthSurfaceRefused",
    "health_document",
    "state_document",
    "refuse_unless_health_safe",
]

HEALTH_SCHEMA_VERSION = "1.0.0"

#: CLOSED. BLUEPRINT §10's five observables plus the version that identifies the shape.
#: A key outside this set is refused because nobody declared it — the allowlist needs no
#: vocabulary and catches the obfuscated name just as flatly as the obvious one.
HEALTH_KEYS: Tuple[str, ...] = (
    "schema_version",
    "live",
    "last_publication_utc",
    "last_evaluation_utc",
    "regime",
    "degraded",
    "degraded_classes",
)

#: CLOSED. The machine-readable state endpoint of ``Q26``. Health, plus the alert classes
#: currently standing. **No ``subject_ref``** — see the module docstring.
STATE_KEYS: Tuple[str, ...] = HEALTH_KEYS + ("alerts",)

#: A CLOSED vocabulary of WHY, so "degraded" is never explained with a number.
#: Each names a KIND of detector failure an operator has a different response to.
DEGRADED_NONE = "NONE"
DEGRADED_PUBLICATION_HALTED = "PUBLICATION_HALTED"
DEGRADED_CADENCE_BREACH = "CADENCE_BREACH"
DEGRADED_EVALUATION_HALTED = "EVALUATION_HALTED"
DEGRADED_INPUTS_INCOMPLETE = "INPUTS_INCOMPLETE"
DEGRADED_WITNESS_UNAVAILABLE = "WITNESS_UNAVAILABLE"

DEGRADED_CLASSES: Tuple[str, ...] = (
    DEGRADED_NONE,
    DEGRADED_PUBLICATION_HALTED,
    DEGRADED_CADENCE_BREACH,
    DEGRADED_EVALUATION_HALTED,
    DEGRADED_INPUTS_INCOMPLETE,
    DEGRADED_WITNESS_UNAVAILABLE,
)

#: The alert fields the unauthenticated surface may carry. ``subject_ref`` is ABSENT and
#: that absence is the safety decision, not an oversight.
_PUBLISHABLE_ALERT_FIELDS: Tuple[str, ...] = ("event_class", "severity", "raised_utc")


class HealthSurfaceRefused(Exception):
    """A candidate health document was refused, and nothing is served.

    Modelled on :exc:`~crash_detector.publication.envelope_contract.PublicationRefused` and
    for the identical reason: it names a ``reason_class``, a JSON pointer and, where there
    is one, the offending KEY NAME. **No value from the candidate appears on this exception
    or in its message** — a refusal message is a log line and a log line is a governed
    artefact.

    There is no ``sanitise()``, no ``strict=False`` and no ``drop_unknown``. A filter that
    strips the offending field succeeds quietly on input it should have rejected loudly, and
    the sanitised document looks exactly like a correct one.
    """

    def __init__(
        self, reason_class: str, *, pointer: str = "", key: "str | None" = None,
        detail: str = "",
    ) -> None:
        location = pointer or "<root>"
        named = f" key {key!r}" if key else ""
        suffix = f": {detail}" if detail else ""
        super().__init__(
            f"health surface REFUSED [{reason_class}] at {location}{named}{suffix}. "
            "Nothing was served."
        )
        self.reason_class = reason_class
        self.pointer = pointer
        self.key = key
        self.detail = detail


REFUSAL_UNKNOWN_KEY = "UNKNOWN_KEY"
REFUSAL_PRIVATE_CLASSIFIED_KEY = "PRIVATE_CLASSIFIED_KEY"
REFUSAL_SECRET_BEARING_KEY = "SECRET_BEARING_KEY"
REFUSAL_UNDECLARED_DEGRADED_CLASS = "UNDECLARED_DEGRADED_CLASS"
REFUSAL_UNDECLARED_REGIME = "UNDECLARED_REGIME"
REFUSAL_NOT_A_DOCUMENT = "NOT_A_DOCUMENT"


def refuse_unless_health_safe(
    candidate: object, *, allowed_keys: Iterable[str] = HEALTH_KEYS
) -> None:
    """Refuse ``candidate`` unless every key on it is declared and public-safe.

    Returns ``None`` on success. There is nothing to assign from this call, and that is the
    point: it cannot be mistaken for a sanitiser and a caller cannot accidentally serve its
    return value. That is
    :func:`~crash_detector.publication.envelope_contract.refuse_unless_publishable`'s design
    and this surface takes it unchanged.
    """
    if not isinstance(candidate, Mapping):
        raise HealthSurfaceRefused(
            REFUSAL_NOT_A_DOCUMENT, detail=f"got {type(candidate).__name__}"
        )

    allowlist = tuple(allowed_keys)

    # (1) THE CLOSED ALLOWLIST. Total, and it recognises nothing.
    for key, pointer in iter_keys(candidate):
        # Keys nested inside `alerts` entries are judged against the alert field allowlist,
        # which is its own closed set; everything else is judged against the top-level one.
        expected = (
            _PUBLISHABLE_ALERT_FIELDS if pointer.startswith("/alerts/") else allowlist
        )
        if key not in expected:
            raise HealthSurfaceRefused(
                REFUSAL_UNKNOWN_KEY,
                pointer=pointer,
                key=key,
                detail=(
                    "the health surface's keys are an allowlist and this key is not on it. "
                    "It is refused because nobody declared it, not because anything was "
                    "recognised about it — so a dial value, a witness reading or a source "
                    "name is refused under any name at all. The repair is to remove the "
                    "key, NEVER to add it to the allowlist: this surface is "
                    "unauthenticated and carries detector health, not market information "
                    "(CD-AC-006, CD-AC-014)"
                ),
            )

    # (2) THE CLASSIFICATION REGISTER, reused. It names the REASON.
    for key, pointer in iter_keys(candidate):
        classified = classify_key(key)
        if classified is None:
            continue
        classification, token = classified
        reason = (
            REFUSAL_SECRET_BEARING_KEY
            if classification == CLASSIFICATION_SECRET_BEARING
            else REFUSAL_PRIVATE_CLASSIFIED_KEY
        )
        raise HealthSurfaceRefused(
            reason,
            pointer=pointer,
            key=key,
            detail=(
                f"the token {token!r} classifies this key as {classification.lower()}. "
                "An unauthenticated ops surface is not a lesser surface for this purpose: "
                "it is the MOST exposed one"
            ),
        )

    # (3) THE CLOSED VOCABULARIES. Without these, `degraded_classes` becomes free text and
    #     free text is where a number eventually gets written.
    classes = candidate.get("degraded_classes")
    if classes is not None:
        if not isinstance(classes, (list, tuple)):
            raise HealthSurfaceRefused(
                REFUSAL_UNDECLARED_DEGRADED_CLASS,
                pointer="/degraded_classes",
                detail=f"expected a list of declared classes, got {type(classes).__name__}",
            )
        for index, member in enumerate(classes):
            if member not in DEGRADED_CLASSES:
                raise HealthSurfaceRefused(
                    REFUSAL_UNDECLARED_DEGRADED_CLASS,
                    pointer=f"/degraded_classes/{index}",
                    detail=(
                        "not a declared degradation class. The vocabulary is "
                        f"{list(DEGRADED_CLASSES)} and it is CLOSED, because 'degraded' "
                        "must be explained with a CLASS and never with a VALUE — and a "
                        "free-text field is where the value eventually goes. The offending "
                        "entry is NOT reproduced in this message"
                    ),
                )

    regime = candidate.get("regime")
    if regime is not None and regime not in REGIME_ORDER:
        raise HealthSurfaceRefused(
            REFUSAL_UNDECLARED_REGIME,
            pointer="/regime",
            detail=(
                f"not a declared regime. The vocabulary is {list(REGIME_ORDER)} and it is "
                "CLOSED here so that a dial score cannot be smuggled out through a field "
                "whose declared type is a string. The offending value is NOT reproduced"
            ),
        )


def health_document(
    *,
    live: bool,
    last_publication_utc: "str | None",
    last_evaluation_utc: "str | None",
    regime: "str | None",
    degraded_classes: Iterable[str] = (),
) -> dict:
    """Build the health document, then **refuse it unless it is safe**.

    Every field is a named keyword. There is no ``**extra``, no ``detail`` and no
    ``metadata``: a builder with an open bag is a builder through which anything reaches the
    surface, and the closed signature is the first of the three refusals.

    ``degraded`` is DERIVED from ``degraded_classes`` rather than passed alongside it, so
    the flag and the reasons cannot disagree — two copies of one fact is one fact with a bug
    scheduled (migration 5 makes the identical argument about its projected columns).
    """
    classes = tuple(degraded_classes)
    substantive = tuple(name for name in classes if name != DEGRADED_NONE)

    document = {
        "schema_version": HEALTH_SCHEMA_VERSION,
        "live": bool(live),
        "last_publication_utc": last_publication_utc,
        "last_evaluation_utc": last_evaluation_utc,
        "regime": regime,
        "degraded": bool(substantive),
        "degraded_classes": list(substantive) if substantive else [DEGRADED_NONE],
    }
    refuse_unless_health_safe(document)
    return document


def state_document(
    *,
    live: bool,
    last_publication_utc: "str | None",
    last_evaluation_utc: "str | None",
    regime: "str | None",
    degraded_classes: Iterable[str] = (),
    alerts: Iterable[Mapping] = (),
) -> dict:
    """The machine-readable state endpoint of ``Q26`` — health plus standing alerts.

    **The alert entries are projected down to class, severity and instant.** ``subject_ref``
    is dropped, because it may legitimately carry a ``source_id`` and a source name is
    market information on an unauthenticated surface. Projected here rather than filtered at
    the reader, so there is exactly one place the decision lives.

    ``alerts`` are the rows :func:`~crash_detector.publication.alerting.recent_alerts`
    returns. **Nothing in this function pushes them anywhere.** It builds a document; a
    reader serves it. That is the whole of the surfacing ``Q26`` ruled for, and adding a
    channel later is a new reader of ``recent_alerts``, not a change here.
    """
    document = health_document(
        live=live,
        last_publication_utc=last_publication_utc,
        last_evaluation_utc=last_evaluation_utc,
        regime=regime,
        degraded_classes=degraded_classes,
    )
    document["alerts"] = [_projected_alert(row) for row in alerts]
    refuse_unless_health_safe(document, allowed_keys=STATE_KEYS)
    return document


def _projected_alert(row: Any) -> dict:
    """``(event_class, severity, raised_utc, ...)`` -> the three publishable fields.

    Positional, because that is the column order
    :func:`~crash_detector.publication.alerting.recent_alerts` selects. Anything beyond the
    third column is dropped by not being read, which is stronger than dropping it by name:
    a column added to that ``SELECT`` cannot arrive here by default.
    """
    event_class, severity, raised_utc = row[0], row[1], row[2]
    return {
        "event_class": str(event_class),
        "severity": str(severity),
        "raised_utc": str(raised_utc),
    }
