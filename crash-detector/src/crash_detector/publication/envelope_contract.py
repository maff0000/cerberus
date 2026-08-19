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
4. it conforms to the surface's closed schema.

Classification runs BEFORE schema validation so that a book-derived key is refused as a
book-derived key rather than as an anonymous unknown property. Both would refuse it; only
one tells the reader what they actually did. And the JSON-representability check runs
before both, because ``json.dumps`` renders ``float('nan')`` as the token ``NaN``, which
is not valid JSON — an envelope that passes a schema and then serialises to something no
consumer can parse has failed in the least useful order.

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
from collections.abc import Mapping as AbcMapping
from enum import Enum
from pathlib import Path
from typing import Any, Iterator, Mapping, Union

from crash_detector.collectors.validation import json_pointer, local_refs_only
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
    "contracts_dir",
    "schema_path_for",
    "load_envelope_schema",
    "refuse_unless_publishable",
]

#: The version both contracts pin with ``const``. Mirrored here so a Python caller and the
#: JSON allowlist cannot drift apart unnoticed; a test asserts they agree.
ENVELOPE_SCHEMA_VERSION = "1.0.0"

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
