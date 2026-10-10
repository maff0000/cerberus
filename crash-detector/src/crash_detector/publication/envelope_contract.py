"""Publication REFUSES. It does not filter (BLUEPRINT §3.5, §8; CD-AC-002, CD-AC-006).

    "Publication refuses, rather than filters — the engine validates the public envelope
    against the closed schema BEFORE writing it, and on any unknown or private-classified
    key it writes nothing and raises. Fail closed. A filter that strips private fields is
    the wrong shape: it succeeds quietly on input it should have rejected loudly."

That paragraph is the whole design of this module, and the shape of the API is the part
that enforces it. :func:`refuse_unless_publishable` returns ``None``. It has no cleaned
copy to return, no ``strict=False``, no ``drop_unknown`` and no ``allow`` list, because
every one of those is a lever someone reaches for at 2am when publication is failing —
and the sanitised envelope that comes out of a filter looks exactly like a correct one.

There is no ``is_publishable() -> bool`` either. A predicate invites
``if not ok: envelope = clean(envelope)``; a procedure that raises does not.

----

WHAT THIS DELIVERS IN WO-2, AND WHAT IT DOES NOT.

The publication LAYER — building envelopes, writing ``publication.public_envelope``,
raising the ``alert.event`` row on a refusal, and serving any of it — is WO-3. What lands
here is the validator and the refusal path, written and tested now because the guard is
the part that has to exist before the thing it guards (BLUEPRINT §13: the doctrine-bearing
criteria are structural from the first commit).

Nothing here writes, serves, binds a port or opens a socket. It reads two JSON files and
raises.

----

THE ORDER OF THE CHECKS IS PART OF THE CONTRACT.

1. the candidate is a JSON object at all;
2. it contains only JSON-representable values, and no non-finite number;
3. no key anywhere is classified for this surface;
4. it conforms to the surface's closed schema;
5. **every node in it that claims ``detail_level: "calm"`` can PROVE it is fresh.**

Classification runs BEFORE schema validation so that a book-derived key is refused as a
book-derived key rather than as an anonymous unknown property. Both would refuse it; only
one tells the reader what they actually did. And the JSON-representability check runs
before both, because ``json.dumps`` renders ``float('nan')`` as the token ``NaN``, which
is not valid JSON — an envelope that passes a schema and then serialises to something no
consumer can parse has failed in the least useful order.

**AND THE FRESHNESS STAGE RUNS LAST, WHICH IS ALSO PART OF THE CONTRACT.** A document that
is not shaped like an envelope has no meaningful stamps to compare, and the schema stage is
what establishes the shape. Running freshness first would mean reporting a missing
``published_utc`` on a document that was never an envelope in the first place.

----

WHY THERE IS A FRESHNESS STAGE AT ALL, AND WHY IT COULD NOT HAVE BEEN A SCHEMA KEYWORD.

``CD-AC-001`` reads *"Missing OR STALE input never renders as calm."* Sixteen increments
guarded the MISSING half and every one of them put the guard in the closed contract, which
is the right place for it: an ``UNKNOWN`` reading declares no ``score`` at all, and since
16A-FIX the ``DEGRADED`` and ``UNKNOWN`` branches type their ``detail_level`` as
``$defs/absent_data_detail_level`` — the vocabulary MINUS ``calm``. Missing data carrying
``calm`` is unrepresentable rather than merely discouraged.

**NOTHING HAD EVER COMPUTED THE STALE HALF, AND THE REASON IS A PROPERTY OF SCHEMAS RATHER
THAN AN OVERSIGHT: A SCHEMA CAN REQUIRE A STAMP BUT IT CANNOT COMPARE ONE.** ``required``
and a ``pattern`` prove a document CARRIES a timestamp; no keyword in 2020-12 subtracts one
instance value from another. So at ``295bdbe`` a ``VALUE`` dial stamped ``1970-01-01`` and
rendering ``calm`` was ADMITTED ON BOTH SURFACES with ``staleness_window_seconds: 1``, on a
tree where ``UNKNOWN + calm`` was correctly REFUSED (``CD-ASR-WO3-11``, ``A311-F2``, RED).
The contracts asserted in prose that a required stamp was *"the FRESHNESS half"*; it is the
AUDITABILITY half. This stage is the freshness half, and it lives here because the
comparison has to live somewhere a schema cannot reach.

``PO-DECISIONS-0029`` ruled ``Q34`` (a): the comparison is made AT THIS GATE and is computed
**PURELY FROM THE DOCUMENT** — ``published_utc`` MINUS the calm-bearing node's own oldest
stamp, against the root's declared ``staleness_window_seconds``. Both instants come out of
the candidate. **NO CLOCK IS CALLED AND NO CLOCK CAN BE PASSED IN**, which is what keeps
this stage inside ``BP-AMENDMENT-0001`` §D.3's NO-CALLER-CLOCK rule: that amendment says in
terms that no parameter exists through which a caller clock, caller sleep or caller span can
arrive, and :func:`refuse_unless_publishable` still takes exactly ``candidate`` and
``surface``.

----

ON WHAT A REFUSAL IS ALLOWED TO SAY.

``jsonschema``'s error messages embed the offending instance: a ``oneOf`` failure
renders the entire dial object into the message text. A refusal message is a log line and
a log line is a governed artefact, so this module builds its own messages from the failing
KEYWORD, the JSON POINTER and, for an unknown key, the KEY NAME. Never from a value.
"""

from __future__ import annotations

import copy
import json
import math
import os
import re
from collections.abc import Mapping as AbcMapping
from enum import Enum
from pathlib import Path
from typing import Any, Iterator, Mapping, Union

from crash_detector.collectors.validation import json_pointer, local_refs_only

#: *** THE TOKEN IS IMPORTED FROM THE ONE MODULE THAT OWNS THE VOCABULARY, NOT RETYPED. ***
#: ``tests/test_detail_level.py::test_only_one_module_decides_a_detail_level`` walks the whole
#: package with ``ast`` and fails on a bare level literal anywhere but
#: :mod:`crash_detector.publication.detail_level` — **and it caught this stage's first draft,
#: which had written ``"calm"`` out by hand.** The control is right and the import is the fix:
#: the gate must refuse over the SAME token the producer emits, and a second spelling of the
#: word is a second place for it to drift. ``tests/test_detail_level.py`` separately asserts
#: that token and the contracts' ``$defs/detail_level`` enum cannot drift apart either, so the
#: chain from schema to producer to gate is pinned end to end.
from crash_detector.publication.detail_level import DETAIL_CALM
from crash_detector.publication.classification import (
    CLASSIFICATION_BOOK_ADJACENT,
    CLASSIFICATION_SECRET_BEARING,
    classify_key,
    iter_keys,
)

__all__ = [
    "EnvelopeSurface",
    "PublicationRefused",
    "ContractUnavailable",
    "ENVELOPE_SCHEMA_VERSION",
    "CONTRACTS_DIR_ENV_VAR",
    "REFUSAL_NOT_A_JSON_OBJECT",
    "REFUSAL_NON_JSON_VALUE",
    "REFUSAL_NON_FINITE_NUMBER",
    "REFUSAL_PRIVATE_CLASSIFIED_KEY",
    "REFUSAL_SECRET_BEARING_KEY",
    "REFUSAL_UNKNOWN_KEY",
    "REFUSAL_SCHEMA_VIOLATION",
    "REFUSAL_STALE_CALM",
    "UTC_STAMP_PATTERN",
    "contracts_dir",
    "schema_path_for",
    "load_envelope_schema",
    "refuse_unless_publishable",
]

#: The version both contracts pin with ``const``. Mirrored here so a Python caller and the
#: JSON allowlist cannot drift apart unnoticed; a test asserts they agree.
#:
#: **BUMPED 1.0.0 -> 1.1.0 AT WO-3 INCREMENT 16A**, for one allowlist edit and no other:
#: ``detail_level`` now attaches PER DIAL inside ``$defs/dial_reading`` in both contracts,
#: under ``PO-DECISIONS-0025`` ruling 5 (which ruled ``Q29``). Two modules' docstrings called
#: that bump *"exactly the friction intended"*; it was paid once, deliberately, and is
#: recorded here rather than left to be inferred from a diff. The field is NOT at envelope
#: top level and a test asserts it stays out — that placement is the ``CD-AC-002`` question.
ENVELOPE_SCHEMA_VERSION = "1.1.0"

#: Override for where the contracts live. Configuration from the environment, so the code
#: runs unchanged in a container that mounts them elsewhere (Standards Baseline §12) and
#: without a host-specific absolute path anywhere in the source.
CONTRACTS_DIR_ENV_VAR = "CD_CONTRACTS_DIR"

REFUSAL_NOT_A_JSON_OBJECT = "NOT_A_JSON_OBJECT"
REFUSAL_NON_JSON_VALUE = "NON_JSON_VALUE"
REFUSAL_NON_FINITE_NUMBER = "NON_FINITE_NUMBER"
REFUSAL_PRIVATE_CLASSIFIED_KEY = "PRIVATE_CLASSIFIED_KEY"
REFUSAL_SECRET_BEARING_KEY = "SECRET_BEARING_KEY"
REFUSAL_UNKNOWN_KEY = "UNKNOWN_KEY"
REFUSAL_SCHEMA_VIOLATION = "SCHEMA_VIOLATION"

#: *** THE FOURTH STAGE'S TOKEN. NEW AT WO-3 INCREMENT 16D (`PO-DECISIONS-0029` ruling 1). ***
#: A node claimed ``calm`` and could not prove it had earned it. Like every token beside it,
#: it is carried with a POINTER and a KEY NAME and **never with a value from the candidate** —
#: not the stamp, not the age, not the window (``PBG-SEC-002``).
REFUSAL_STALE_CALM = "STALE_CALM"

_JSON_SCALARS = (str, int, float, bool, type(None))


class EnvelopeSurface(Enum):
    """Which contract a candidate is being judged against.

    Two members, and a candidate is judged against exactly one. There is deliberately no
    "both" and no "either": an envelope that would satisfy both contracts is an envelope
    whose surface nobody decided, and deciding it later is deciding it at the point of
    least attention.
    """

    PUBLIC = "public"
    PRIVATE = "private"

    @property
    def schema_filename(self) -> str:
        return f"{self.value}_envelope.schema.json"


class ContractUnavailable(RuntimeError):
    """The declared contract could not be read or is not usable.

    A separate class from :exc:`PublicationRefused` because it is a different fact about
    a different thing: the candidate was never judged. It is emphatically NOT a pass —
    where a check cannot reach its authentic target it must fail, never wave through
    (Standards Baseline §16, ``PBG-CI-002``).
    """


class PublicationRefused(Exception):
    """A candidate envelope was refused, and nothing was published.

    ``reason_class`` is a stable token; ``pointer`` is an RFC 6901 JSON Pointer to the
    offending location; ``key`` names the offending property where there is one. No value
    from the candidate appears on this exception or in its message.
    """

    def __init__(
        self,
        reason_class: str,
        *,
        surface: "EnvelopeSurface",
        pointer: str = "",
        key: Union[str, None] = None,
        detail: str = "",
    ) -> None:
        location = pointer or "<root>"
        named = f" key {key!r}" if key else ""
        suffix = f": {detail}" if detail else ""
        super().__init__(
            f"{surface.value} envelope REFUSED [{reason_class}] at {location}"
            f"{named}{suffix}. Nothing was published."
        )
        self.reason_class = reason_class
        self.surface = surface
        self.pointer = pointer
        self.key = key
        self.detail = detail


def contracts_dir() -> Path:
    """Where the product JSON Schemas live.

    ``$CD_CONTRACTS_DIR`` when set, otherwise ``contracts/`` resolved relative to this
    source file. Never an absolute host path written into the source.

    ``schemas/`` at the project root is RESERVED by the governance framework and holds no
    product schema (CD-AUTH-0001, CD-FWK-001).
    """
    override = os.environ.get(CONTRACTS_DIR_ENV_VAR)
    if override:
        return Path(override)
    # .../src/crash_detector/publication/envelope_contract.py -> project root is parents[3]
    return Path(__file__).resolve().parents[3] / "contracts"


def schema_path_for(surface: "EnvelopeSurface") -> Path:
    if not isinstance(surface, EnvelopeSurface):
        raise TypeError("surface must be an EnvelopeSurface member")
    return contracts_dir() / surface.schema_filename


def load_envelope_schema(surface: "EnvelopeSurface") -> dict:
    """Read and sanity-check a contract, returning a fresh copy each call.

    A fresh copy because a shared mutable schema is a schema a caller can widen at
    runtime, and a closed schema that can be opened by whoever holds a reference to it is
    not closed.

    Refuses a contract carrying a non-local ``$ref``: resolving one would make validation
    perform an outbound fetch, which is an undeclared egress path inside a check.
    """
    path = schema_path_for(surface)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractUnavailable(
            f"cannot read the {surface.value} envelope contract at {path}: "
            f"{type(exc).__name__}. The candidate was NOT judged and nothing may be "
            "published on the strength of this call."
        ) from exc
    try:
        schema = json.loads(text)
    except ValueError as exc:
        raise ContractUnavailable(
            f"the {surface.value} envelope contract at {path} is not valid JSON: "
            f"{type(exc).__name__}"
        ) from exc
    if not isinstance(schema, dict):
        raise ContractUnavailable(
            f"the {surface.value} envelope contract at {path} is not a JSON object"
        )
    if not local_refs_only(schema):
        raise ContractUnavailable(
            f"the {surface.value} envelope contract at {path} carries a non-local $ref; "
            "resolving one is an outbound fetch performed inside a validation step"
        )
    return copy.deepcopy(schema)


def refuse_unless_publishable(
    candidate: object, *, surface: "EnvelopeSurface"
) -> None:
    """Refuse ``candidate`` unless it conforms exactly to ``surface``'s closed contract.

    Returns ``None`` on success and raises :exc:`PublicationRefused` otherwise. There is
    nothing to assign from this call, and that is the point: it cannot be mistaken for a
    sanitiser, and a caller cannot accidentally publish its return value.

    ``candidate`` is never mutated, never copied-and-repaired, and never partially
    accepted.
    """
    if not isinstance(surface, EnvelopeSurface):
        raise TypeError("surface must be an EnvelopeSurface member")

    if not isinstance(candidate, AbcMapping):
        raise PublicationRefused(
            REFUSAL_NOT_A_JSON_OBJECT,
            surface=surface,
            detail=f"got {type(candidate).__name__}",
        )

    _refuse_non_json(candidate, surface)
    _refuse_classified_keys(candidate, surface)
    _refuse_schema_violation(candidate, surface)
    _refuse_stale_calm(candidate, surface)


def _refuse_non_json(candidate: Mapping, surface: "EnvelopeSurface") -> None:
    """Refuse anything JSON cannot carry, and any number JSON cannot represent."""
    for node, pointer in _iter_nodes(candidate):
        if isinstance(node, AbcMapping):
            for key in node:
                if not isinstance(key, str):
                    raise PublicationRefused(
                        REFUSAL_NON_JSON_VALUE,
                        surface=surface,
                        pointer=pointer,
                        detail=(
                            f"object key of type {type(key).__name__}; JSON object keys "
                            "are strings, and json.dumps would silently coerce this one"
                        ),
                    )
            continue
        if isinstance(node, (list, tuple)):
            continue
        if isinstance(node, bool) or node is None:
            continue
        if isinstance(node, float):
            if not math.isfinite(node):
                raise PublicationRefused(
                    REFUSAL_NON_FINITE_NUMBER,
                    surface=surface,
                    pointer=pointer,
                    detail=(
                        "json.dumps renders this as the bare token NaN or Infinity, "
                        "which is not valid JSON and which no consumer can parse"
                    ),
                )
            continue
        if isinstance(node, _JSON_SCALARS):
            continue
        raise PublicationRefused(
            REFUSAL_NON_JSON_VALUE,
            surface=surface,
            pointer=pointer,
            detail=(
                f"value of type {type(node).__name__} is not JSON-representable; a "
                "datetime, Decimal or dataclass here would be str()'d by a later "
                "serialiser into a shape no schema ever checked"
            ),
        )


def _iter_nodes(node: object, pointer: str = "") -> Iterator[tuple]:
    """``(node, pointer)`` for every node in the tree, root first."""
    yield (node, pointer)
    if isinstance(node, AbcMapping):
        for key, value in node.items():
            token = str(key).replace("~", "~0").replace("/", "~1")
            yield from _iter_nodes(value, f"{pointer}/{token}")
    elif isinstance(node, (list, tuple)):
        for index, value in enumerate(node):
            yield from _iter_nodes(value, f"{pointer}/{index}")


def _refuse_classified_keys(candidate: Mapping, surface: "EnvelopeSurface") -> None:
    """Refuse a key whose vocabulary says it may not appear on this surface."""
    for key, pointer in iter_keys(candidate):
        classified = classify_key(key)
        if classified is None:
            continue
        classification, token = classified
        if classification == CLASSIFICATION_SECRET_BEARING:
            # Both surfaces. A secret is referenced by environment-variable NAME at the
            # point of use and is never carried in a record (PBG-SEC-002, non-waivable).
            # The MATCHED TOKEN is reported, never the value under the key.
            raise PublicationRefused(
                REFUSAL_SECRET_BEARING_KEY,
                surface=surface,
                pointer=pointer,
                key=key,
                detail=(
                    f"the token {token!r} classifies this key as secret-bearing; no "
                    "envelope of any classification may carry one"
                ),
            )
        if (
            classification == CLASSIFICATION_BOOK_ADJACENT
            and surface is EnvelopeSurface.PUBLIC
        ):
            raise PublicationRefused(
                REFUSAL_PRIVATE_CLASSIFIED_KEY,
                surface=surface,
                pointer=pointer,
                key=key,
                detail=(
                    f"the token {token!r} classifies this key as book-adjacent; PID "
                    "doctrine §3.5 keeps anything touching the book private. The repair "
                    "is to remove the key, never to add it to the public allowlist"
                ),
            )


def _refuse_schema_violation(candidate: Mapping, surface: "EnvelopeSurface") -> None:
    """Refuse anything the closed contract does not admit."""
    import jsonschema

    schema = load_envelope_schema(surface)
    try:
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)
        validator = validator_cls(schema)
        errors = list(validator.iter_errors(candidate))
    except Exception as exc:
        raise ContractUnavailable(
            f"the {surface.value} envelope contract is not a usable JSON Schema: "
            f"{type(exc).__name__}. The candidate was NOT judged."
        ) from exc

    if not errors:
        return

    chosen = _preferred_error(errors)
    pointer = json_pointer(list(chosen.absolute_path))

    if chosen.validator == "additionalProperties":
        for key in _unexpected_keys(chosen):
            raise PublicationRefused(
                REFUSAL_UNKNOWN_KEY,
                surface=surface,
                pointer=pointer,
                key=key,
                detail=(
                    "the contract's properties are an allowlist and this key is not on "
                    "it. Publication fails closed; it does not strip the key and "
                    "continue"
                ),
            )

    detail = f"failed the {str(chosen.validator)!r} constraint"
    if chosen.validator == "oneOf":
        detail = (
            "matches none of the declared reading states. VALUE, DEGRADED and UNKNOWN "
            "are three closed shapes, so a field that is legitimate on one of them is "
            "refused on the others — an UNKNOWN reading carrying a score has no state "
            "to be published as, which is CD-AC-001 held in the contract"
        )
    raise PublicationRefused(
        REFUSAL_SCHEMA_VIOLATION,
        surface=surface,
        pointer=pointer,
        detail=detail,
    )


def _flatten(error: Any, depth: int = 0) -> Iterator[tuple]:
    """``(error, context_depth)`` for an error and every sub-error inside its ``context``.

    ``oneOf`` reports one error at the parent and puts the per-branch detail in
    ``context``. Both levels are collected, but the depth is kept, because the two say
    different things and only one of them is reliable.
    """
    yield (error, depth)
    for sub in getattr(error, "context", None) or ():
        yield from _flatten(sub, depth + 1)


def _preferred_error(errors: Any) -> Any:
    """The error to report, chosen deterministically and honestly.

    Ordered by CONTEXT DEPTH first, then by whether it is an ``additionalProperties``
    failure, then by pointer.

    Depth first is the load-bearing part. A ``oneOf`` branch's own
    ``additionalProperties`` error is an artefact of the branch that did not match — for
    an UNKNOWN reading that wrongly carries a ``score``, the VALUE branch reports
    ``missing_inputs`` as unexpected, which is a true statement about a branch nobody
    intended and a misleading one about the document. Preferring depth 0 means the
    refusal says "no declared reading state admits this object", which is what actually
    happened.

    Sorted on the RENDERED pointer, never on ``error.path``: that is a deque mixing
    ``str`` property names with ``int`` array indices, and comparing those raises
    ``TypeError`` — a crash that only appears when a candidate is malformed in two places
    of different kinds.
    """
    flattened = [pair for error in errors for pair in _flatten(error)]

    def sort_key(pair: tuple) -> tuple:
        error, depth = pair
        return (
            depth,
            0 if error.validator == "additionalProperties" else 1,
            len(error.absolute_path),
            json_pointer(list(error.absolute_path)),
            str(error.validator),
        )

    return min(flattened, key=sort_key)[0]


def _unexpected_keys(error: Any) -> tuple:
    """The keys that tripped an ``additionalProperties`` error, computed not parsed.

    Derived by comparing the instance's keys against the failing subschema's declared
    allowlist rather than by reading ``error.message``. The message would do for this one
    keyword, but building the habit of parsing validator prose is how a value-bearing
    message eventually reaches a log.
    """
    instance = error.instance
    if not isinstance(instance, AbcMapping):
        return ()
    subschema = error.schema if isinstance(error.schema, AbcMapping) else {}
    declared = subschema.get("properties", {})
    allowed = set(declared) if isinstance(declared, AbcMapping) else set()
    return tuple(sorted(str(key) for key in instance if str(key) not in allowed))


# =========================================================================================== #
# STAGE 4 — FRESHNESS. *** A NODE THAT CLAIMS `calm` MUST PROVE IT EARNED IT. ***
# WO-3 increment 16D, PO-DECISIONS-0029 ruling 1 (Q34 (a)), answering CD-ASR-WO3-11 A311-F2.
# =========================================================================================== #

#: The property that carries a rendering decision, and the one value of it this stage guards.
#: ``calm`` is the only level ``CD-AC-001`` is about: *"missing or stale input never renders as
#: calm."* ``elevated`` and ``acute`` are what a stale dial is SUPPOSED to render as, so a stale
#: node carrying one of those is correct behaviour and this stage says nothing about it.
DETAIL_LEVEL_KEY = "detail_level"

#: Re-exported under this module's own name so a reader of the stage sees what it guards
#: without leaving the file. **IT IS A BINDING, NOT A LITERAL** — see the import.
CALM_DETAIL_LEVEL = DETAIL_CALM

#: The root properties this stage reads, and it reads them ONLY at the root. Both contracts
#: REQUIRE both of them at the root today; this stage nevertheless checks and fails closed,
#: because a stage whose correctness depends on another stage having run is a stage that breaks
#: silently the day the order changes.
PUBLISHED_UTC_KEY = "published_utc"
STALENESS_WINDOW_KEY = "staleness_window_seconds"

#: *** MIRRORED FROM `#/$defs/utc_timestamp` IN BOTH CONTRACTS, CHARACTER FOR CHARACTER. ***
#: Kept here as a string rather than compiled inline so ``tests/test_envelope_freshness.py`` can
#: assert the mirror against the contracts themselves and the two cannot drift apart unnoticed —
#: the same device ``ENVELOPE_SCHEMA_VERSION`` uses for the pinned version. **THE PARSER BELOW IS
#: NO LOOSER THAN THIS PATTERN AND THE TEST PROVES THAT DIRECTION**: every string the parser
#: accepts, the contract accepts. The reverse does NOT hold and is deliberate — this pattern
#: admits ``2026-13-45T99:99:99Z``, which is not an instant, and an unparsable stamp FAILS CLOSED.
UTC_STAMP_PATTERN = (
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?Z$"
)

_UTC_STAMP_RE = re.compile(
    r"^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})"
    r"T(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?:\.(?P<fraction>[0-9]{1,6}))?Z$"
)

#: A property whose NAME declares it is a stamp. **THIS SUFFIX CAN ONLY EVER TIGHTEN THE ANSWER
#: AND CAN NEVER PRODUCE AN ADMISSION** — see :func:`_node_stamps`. Freshness is proved from
#: VALUES that parse, never from names; the name is consulted only to catch a property that
#: ANNOUNCES itself as a stamp and then does not parse, which is a refusal rather than a shrug.
_DECLARED_STAMP_SUFFIX = "_utc"

_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

#: Whole seconds in a day, and microseconds in a second. The arithmetic below is in INTEGER
#: MICROSECONDS end to end so that the boundary case ``age == window`` is decided exactly rather
#: than by a float that is one ULP the wrong side of it.
_SECONDS_PER_DAY = 86400
_MICROSECONDS_PER_SECOND = 1000000


def _is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_from_civil(year: int, month: int, day: int) -> int:
    """Days from 1970-01-01 to ``year-month-day``, by arithmetic and by nothing else.

    *** THIS FUNCTION IS WHY THIS MODULE STILL IMPORTS NEITHER ``datetime`` NOR ``time``. ***
    Either would do the arithmetic, and either would also put a reader-of-the-system-clock one
    attribute lookup away from a stage whose entire guarantee is that it cannot reach one. The
    guarantee is worth more than the six lines below: there is no name in this module that a
    later edit could turn into a clock call without ADDING AN IMPORT, which is a diff a reviewer
    sees. ``tests/test_envelope_freshness.py`` asserts that absence mechanically, over the
    module's own AST, so it is a control and not a comment.

    The algorithm is the standard proleptic-Gregorian days-from-civil computation (era-based,
    exact for every year this pattern can express). It is pure integer arithmetic on three
    integers the CANDIDATE supplied.

    LEAP SECONDS ARE NOT REPRESENTED, which is the same choice POSIX time makes and the same
    one ``datetime`` makes — a ``:60`` second is rejected by :func:`_parse_utc_stamp` as
    unparsable and therefore FAILS CLOSED. See DECLARED LIMIT F-3 in the contract note.
    """
    shifted = year - (1 if month <= 2 else 0)
    era = (shifted if shifted >= 0 else shifted - 399) // 400
    year_of_era = shifted - era * 400
    day_of_year = (153 * (month + (-3 if month > 2 else 9)) + 2) // 5 + day - 1
    day_of_era = (
        year_of_era * 365 + year_of_era // 4 - year_of_era // 100 + day_of_year
    )
    return era * 146097 + day_of_era - 719468


def _parse_utc_stamp(value: object) -> Union[int, None]:
    """``value`` as INTEGER MICROSECONDS since the epoch, or ``None`` if it is not an instant.

    ``None`` is *"this is not a stamp I can read"* and every caller treats it as a REFUSAL,
    never as a skip. There is no third answer and there is deliberately no ``default``.

    Stricter than :data:`UTC_STAMP_PATTERN` on purpose: the contract pattern is a shape check
    and admits ``2026-13-45T99:99:99Z``, which names no instant. A stamp that names no instant
    cannot prove a node fresh.
    """
    if not isinstance(value, str):
        return None
    matched = _UTC_STAMP_RE.match(value)
    if matched is None:
        return None
    year = int(matched.group("year"))
    month = int(matched.group("month"))
    day = int(matched.group("day"))
    hour = int(matched.group("hour"))
    minute = int(matched.group("minute"))
    second = int(matched.group("second"))
    if not 1 <= month <= 12:
        return None
    days_in_month = _DAYS_IN_MONTH[month - 1]
    if month == 2 and _is_leap_year(year):
        days_in_month = 29
    if not 1 <= day <= days_in_month:
        return None
    if hour > 23 or minute > 59 or second > 59:
        return None
    fraction = matched.group("fraction") or ""
    microseconds = int(fraction.ljust(6, "0")) if fraction else 0
    whole_seconds = (
        _days_from_civil(year, month, day) * _SECONDS_PER_DAY
        + hour * 3600
        + minute * 60
        + second
    )
    return whole_seconds * _MICROSECONDS_PER_SECOND + microseconds


def _positive_finite_seconds(value: object) -> Union[float, None]:
    """``value`` as a real, finite, strictly-positive number of seconds, or ``None``.

    ``bool`` is excluded explicitly. ``True`` is an ``int`` in Python and would otherwise read
    as a one-second window — a window nobody declared, arrived at by a type confusion, and
    silently the tightest one in the product.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0:
        return None
    return numeric


def _node_stamps(node: Mapping) -> tuple:
    """``(parsed, unparsable)`` for the DIRECT properties of ``node`` that are stamps.

    ``parsed`` is a sorted list of ``(microseconds, key)`` for every direct property whose
    value is a string that :func:`_parse_utc_stamp` reads as an instant. ``unparsable`` is the
    sorted list of keys that ANNOUNCE themselves as stamps by name and are not readable as one.

    *** THE DETECTION IS BY VALUE, NOT BY NAME, AND THAT IS THE WHOLE POINT. *** The obvious
    implementation reads ``node["as_of_utc"]``. It must not, and neither must this: the two
    contracts today spell the stamp ``as_of_utc`` on the ``VALUE`` and ``DEGRADED`` branches and
    ``since_utc`` on ``UNKNOWN``, so a fixed property name would already be wrong, and a
    contract edit that spells it a third way tomorrow would make a name-reading stage silently
    stop finding stamps — which is *admitting*, not refusing. **A STAGE THAT LOOKS FOR NAMES IT
    KNOWS IS A RECOGNISER OVER AN OPEN SET, AND THIS ROW HAS LOST ELEVEN CONSECUTIVE AUDITS TO
    EXACTLY THAT.** A string that parses as a UTC instant IS a stamp, whatever it is called.

    **AND THE OLDEST OF THEM GOVERNS** (see :func:`_refuse_stale_calm`), which is what makes
    value-detection safe in the direction that matters: adding a fresh-looking string to a node
    can never rescue it, because the node is only as fresh as its oldest readable stamp. That
    is the envelope's own declared doctrine for ``as_of_utc`` — *"as fresh as its oldest input,
    never as fresh as the last time we asked"* — and this stage must not quietly adopt a laxer
    one.

    **THE NAME SUFFIX IS THE TIGHTENING HALF AND CAN NEVER ADMIT ANYTHING.** A property called
    ``as_of_utc`` whose value is ``"yesterday"``, or is a number, or is ``null``, is a stamp
    that will not parse; the caller REFUSES on it. It is never counted as proof of anything.
    """
    parsed = []
    unparsable = []
    for key, value in node.items():
        name = str(key)
        microseconds = _parse_utc_stamp(value)
        if microseconds is not None:
            parsed.append((microseconds, name))
        elif name.lower().endswith(_DECLARED_STAMP_SUFFIX):
            unparsable.append(name)
    return sorted(parsed), sorted(unparsable)


def _refuse_stale_calm(candidate: Mapping, surface: "EnvelopeSurface") -> None:
    """Refuse the envelope unless every node claiming ``calm`` can prove it is fresh.

    *** THE PREDICATE, STATED WHOLE: FOR EVERY NODE IN THE CANDIDATE DOCUMENT THAT CARRIES
    ``detail_level: "calm"``, THAT NODE MUST PROVE FRESHNESS, AND IF IT CANNOT, THE ENVELOPE IS
    REFUSED. ***

    Proving freshness is all five of these, and any one of them failing is a REFUSAL:

      (a) the document's ROOT carries a ``published_utc`` that reads as an instant;
      (b) the document's ROOT carries a ``staleness_window_seconds`` that is a real, finite,
          strictly-positive number;
      (c) the calm-bearing node ITSELF carries at least one readable stamp, and no property of
          it that announces itself as a stamp fails to read as one;
      (d) ``age = published_utc - <the node's OLDEST stamp>`` is **NOT NEGATIVE**; and
      (e) ``age <= staleness_window_seconds``.

    **(d) IS NOT DECORATION AND IT IS NOT THE OBVIOUS FORMULA.** The obvious formula is
    ``age > window -> refuse``, and it leaves a dial stamped ``2099-01-01`` — data from the
    future, whose age is NEGATIVE — comfortably inside every window there is. The Project Lead
    MEASURED that row at ``295bdbe`` before this increment was dispatched: ADMITTED on both
    surfaces. A stamp AFTER publication is INCOHERENT rather than fresh, and incoherent fails
    closed. The predicate is a CLOSED INTERVAL, not an upper bound.

    ---- IT QUANTIFIES OVER NODES, NEVER OVER DIAL SLOTS -----------------------------------

    This walks :func:`_iter_nodes` — the same walk stage 1 already trusts, which descends
    objects AND arrays at every depth and yields RFC 6901 pointers. **ANY MAPPING NODE WHOSE
    ``detail_level`` IS ``calm`` IS A CALM-BEARING NODE, WHEREVER IN THE DOCUMENT IT SITS, AT
    WHATEVER DEPTH, THROUGH HOWEVER MANY ARRAYS.**

    It does NOT read ``candidate["equity_crash"]["as_of_utc"]``. That would hard-code the
    document shape — it would know about the two dial slots that exist today and be silent on
    the third one a contract edit adds tomorrow, which is the defect class that lost eleven
    consecutive audit rounds on this row. Rule CC closed the MISSING half by CONSTRUCTION OVER
    A CLOSED SET rather than RECOGNITION OVER AN OPEN ONE; this is the same move applied to the
    STALE half. The question is not *"is this one of the dials I know about?"* but *"does this
    node claim calm, and can it prove it earned it?"*

    One consequence is worth naming because it is ``CD-ASR-WO3-11``'s ``A311-F1`` closed as a
    side effect: ``{"source_id": "SRC-A", "detail_level": "calm"}`` sitting inside a root
    ``degraded_inputs`` array is a mapping node carrying ``calm`` with no stamp of its own. It
    is refused HERE — **even on a tree whose contract has been widened to admit it.**

    ---- FAIL CLOSED AT EVERY BRANCH -------------------------------------------------------

    A stamp that will not parse, a window that is not a number, a missing ``published_utc``, a
    calm-bearing node with no stamp at all: every one of them is a REFUSAL and never a skip.
    Where a check cannot reach its authentic target it must fail, never wave through (Standards
    Baseline §16, ``PBG-CI-002``). **THERE IS NO "CANNOT TELL, SO ALLOW" BRANCH IN THIS STAGE.**

    ---- WHAT IT IS NOT ---------------------------------------------------------------------

    It is the SIMPLE WINDOW FLOOR and nothing more. The comparand is the document's own root
    ``staleness_window_seconds``, whose own description says it is *"the window that was
    applied, carried so every consumer judges freshness by the same declared rule rather than
    by its own guess"* — **this stage is that consumer.** The REGIME-AWARE window of
    ``CD-RT-009``/``CD-AC-009``, which TIGHTENS in stress, is a later detector-layer refinement
    that rides ON TOP and may only ever make the refusal MORE conservative. It is NOT
    implemented here, NOT scaffolded here, and there is deliberately NO HOOK for it
    (``PO-DECISIONS-0029`` ruling 2).
    """
    calm_nodes = [
        (node, pointer)
        for node, pointer in _iter_nodes(candidate)
        if isinstance(node, AbcMapping)
        and node.get(DETAIL_LEVEL_KEY) == CALM_DETAIL_LEVEL
    ]
    if not calm_nodes:
        # Nothing in this document claims to be calm, so there is nothing for this stage to
        # judge. That is NOT a weakening: the guarantee is about `calm` and about nothing else,
        # and a stage that refused documents making no claim would be refusing the product's
        # ordinary output to look strict.
        return

    published = _parse_utc_stamp(candidate.get(PUBLISHED_UTC_KEY))
    window = _positive_finite_seconds(candidate.get(STALENESS_WINDOW_KEY))

    for node, pointer in calm_nodes:
        if published is None:
            raise PublicationRefused(
                REFUSAL_STALE_CALM,
                surface=surface,
                pointer=pointer,
                key=PUBLISHED_UTC_KEY,
                detail=(
                    "this node renders as calm, and freshness is measured from the root's "
                    "publication instant, which is absent or does not read as a UTC instant. "
                    "A node whose age cannot be computed has not proved it is fresh, and an "
                    "unprovable freshness claim is refused rather than assumed"
                ),
            )
        if window is None:
            raise PublicationRefused(
                REFUSAL_STALE_CALM,
                surface=surface,
                pointer=pointer,
                key=STALENESS_WINDOW_KEY,
                detail=(
                    "this node renders as calm, and the root declares no usable staleness "
                    "window to judge it against — the window must be a real, finite, strictly "
                    "positive number of seconds, because an unbounded window is no window"
                ),
            )

        parsed, unparsable = _node_stamps(node)
        if unparsable:
            raise PublicationRefused(
                REFUSAL_STALE_CALM,
                surface=surface,
                pointer=pointer,
                key=unparsable[0],
                detail=(
                    "this node renders as calm and carries a property that announces itself "
                    "as a UTC stamp and does not read as one. A stamp that will not parse is "
                    "a refusal and never a skip"
                ),
            )
        if not parsed:
            raise PublicationRefused(
                REFUSAL_STALE_CALM,
                surface=surface,
                pointer=pointer,
                key=DETAIL_LEVEL_KEY,
                detail=(
                    "this node renders as calm and carries no UTC stamp of its own, so there "
                    "is nothing to measure its age from. Calm is a claim about the freshness "
                    "of data and a node that cannot date its data cannot make it"
                ),
            )

        # *** THE OLDEST STAMP GOVERNS. *** `parsed` is sorted, so `parsed[0]` is the oldest,
        # and the tie between two equally-old stamps is broken by key name so the refusal a
        # given document produces is the same one every time it is judged.
        oldest_microseconds, oldest_key = parsed[0]
        age = published - oldest_microseconds

        if age < 0:
            raise PublicationRefused(
                REFUSAL_STALE_CALM,
                surface=surface,
                pointer=pointer,
                key=oldest_key,
                detail=(
                    "this node renders as calm and is stamped AFTER the envelope was "
                    "published. Data from the future is incoherent rather than fresh, so it "
                    "fails closed: a negative age is not a small age"
                ),
            )
        if age > window * _MICROSECONDS_PER_SECOND:
            raise PublicationRefused(
                REFUSAL_STALE_CALM,
                surface=surface,
                pointer=pointer,
                key=oldest_key,
                detail=(
                    "this node renders as calm and its oldest stamp is older than the "
                    "staleness window the root declares. PID §3.2 is constitutional: missing "
                    "OR STALE input never renders as calm. The repair is to render this "
                    "reading at its true level, never to widen the window"
                ),
            )
