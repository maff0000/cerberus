"""Validation at the boundary, once, against an explicit schema (Standards Baseline §4).

A response that does not conform is stored as ``MALFORMED`` with its error class, and
**never coerced**. External input is hostile, including a source that has been reliable
for a year.

Two failures are kept apart here, because they belong to different people:

* :exc:`SchemaRejection` — *their* answer did not conform to *our* declared schema. This
  is an observation about the source and it becomes a ``MALFORMED`` row.
* :exc:`SchemaDeclarationInvalid` — *our* declared schema is unusable, so conformance
  could not be determined at all. This is our defect. Recording it as ``MALFORMED`` and
  saying nothing else would blame the source for our bug, and *cannot determine* is not
  *determined to be absent* (Standards Baseline §8). The runner records the attempt — the
  row is written, always — and then lets this exception travel, loudly.

----

WHAT IS DELIBERATELY NOT CARRIED OUT OF THIS MODULE.

``jsonschema``'s own error messages **embed the offending instance value**: a type error
on a credential field renders as ``'<the credential itself>' is not of type
``integer``. Carrying that
message onto an :class:`~crash_detector.observations.Malformed` outcome would write a
value from a hostile external response into a governed, append-only store, and any of
those values may be a secret the source echoed back (``PBG-SEC-002``,
``PBG-EVID-003``, both non-waivable; Standards Baseline §5 — "never print a matched value
when scanning; report class and location only").

So nothing value-bearing leaves this module. What leaves is:

* an ``error_class`` derived from the failing schema KEYWORD, uppercased and sanitised to
  ``[A-Z0-9_]`` so an adversarial schema cannot smuggle content through it; and
* an ``instance_path`` — an RFC 6901 JSON Pointer built from property NAMES and array
  INDICES only.

That is enough to count malformations, compare them across time and find the field that
broke. It is not enough to reconstruct the response, and that is the point.

----

REMOTE ``$ref`` IS REFUSED.

``jsonschema`` will resolve an ``http(s)`` ``$ref`` by fetching it. A declared schema
carrying one would turn every validation into an outbound network request from the
collector container — unbounded, unauthorised in this increment, and an egress path
nobody declared. Every ``$ref`` must therefore be a local ``#`` fragment, checked before
the validator is built.
"""

from __future__ import annotations

import re
from collections.abc import Mapping as AbcMapping
from typing import Any, Iterator, Mapping, Protocol, Sequence

from crash_detector.admission import ESTABLISHED_HERE, admits, one_of
from crash_detector.observations import MAX_INSTANCE_PATH_LENGTH

__all__ = [
    "SchemaRejection",
    "SchemaDeclarationInvalid",
    "VALIDATION_FAILURES",
    "PayloadValidator",
    "JsonSchemaValidator",
    "MAX_INSTANCE_PATH_LENGTH",
    "json_pointer",
    "local_refs_only",
]

#: A JSON Pointer longer than the ceiling is truncated with an explicit marker, and the
#: RESULT INCLUDING THE MARKER stays within the ceiling. Getting that wrong would produce
#: a pointer that the :class:`~crash_detector.observations.Malformed` constructor then
#: refuses — a collector that crashes only on deeply nested malformed responses, which is
#: to say only when a source is behaving badly.
_TRUNCATION_MARKER = "/...[truncated]"
_POINTER_BUDGET = MAX_INSTANCE_PATH_LENGTH - len(_TRUNCATION_MARKER)
_ERROR_CLASS_SANITISER = re.compile(r"[^A-Z0-9_]")


class SchemaRejection(Exception):
    """A payload did not conform to the adapter's declared schema.

    Carries a classification and a location. It carries no value, no message from the
    validator and no excerpt of the payload.
    """

    def __init__(self, error_class: str, instance_path: str) -> None:
        if not isinstance(error_class, str) or not error_class:
            raise ValueError("SchemaRejection requires a non-empty error_class")
        if not isinstance(instance_path, str):
            raise TypeError("SchemaRejection.instance_path must be a str")
        super().__init__(f"{error_class} at {instance_path or '<root>'}")
        self.error_class = error_class
        self.instance_path = instance_path


class SchemaDeclarationInvalid(Exception):
    """OUR declared schema is unusable, so conformance could not be determined.

    Never recorded as a property of the source. It is a configuration defect and it is
    raised so that it is seen as one.
    """

    def __init__(self, error_class: str) -> None:
        if not isinstance(error_class, str) or not error_class:
            raise ValueError("SchemaDeclarationInvalid requires a non-empty error_class")
        super().__init__(error_class)
        self.error_class = error_class


class PayloadValidator(Protocol):
    """Validates a payload against a declared schema, or raises."""

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `PayloadValidator.__new__(PayloadValidator)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ()

    def validate(self, payload: object, schema: Mapping[str, Any]) -> None:
        """Return ``None`` if conforming.

        Raise :exc:`SchemaRejection` if the payload does not conform, or
        :exc:`SchemaDeclarationInvalid` if the schema itself cannot be used. Never
        return a repaired, coerced or partially accepted payload — there is no such
        thing at this boundary.
        """


@admits(parts=one_of(list, tuple))
def json_pointer(parts: Sequence[object]) -> str:
    """An RFC 6901 JSON Pointer from a sequence of property names and array indices.

    ``~`` and ``/`` are escaped as the RFC requires, so a property name containing a
    slash cannot forge a deeper path than it occupies. The result is bounded by
    :data:`MAX_INSTANCE_PATH_LENGTH`; the root is the empty string, exactly as the RFC
    defines it, and not a placeholder for "we do not know".
    """
    rendered = ""
    for part in parts:
        token = str(part).replace("~", "~0").replace("/", "~1")
        rendered += "/" + token
        if len(rendered) > MAX_INSTANCE_PATH_LENGTH:
            return rendered[:_POINTER_BUDGET] + _TRUNCATION_MARKER
    return rendered


def _walk(node: object) -> Iterator[object]:
    """Every mapping and sequence node inside ``node``, including ``node`` itself."""
    yield node
    if isinstance(node, AbcMapping):
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, (list, tuple)):
        for value in node:
            yield from _walk(value)


@admits(
    schema=ESTABLISHED_HERE(
        "THIS CALLABLE IS THE ESTABLISHMENT DOOR for a declared schema document. Its "
        "contract is to answer a question about ANY object — a mapping, a list, a string, "
        "anything an adapter declared — and it walks whatever it is given, refusing nothing "
        "and coercing nothing. Exact-typing the argument would make it unable to answer for "
        "the very inputs it exists to be asked about. CARRIER MEASURED: the whole-document "
        "walk answers False for a remote $ref at any depth, and JsonSchemaValidator turns "
        "that into SchemaDeclarationInvalid before any validator is built — "
        "tests/test_collector_validation.py::test_a_non_local_ref_anywhere_in_a_declared_schema_is_refused, which is parametrised over a $ref at the root and one three levels down."
    )
)
def local_refs_only(schema: object) -> bool:
    """True when every ``$ref`` anywhere in ``schema`` is a local ``#`` fragment.

    Checked over the WHOLE document rather than its top level, because a remote
    reference three levels down fetches just as eagerly as one at the root.
    """
    for node in _walk(schema):
        if not isinstance(node, AbcMapping):
            continue
        if "$ref" not in node:
            continue
        ref = node["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#"):
            return False
    return True


class JsonSchemaValidator:
    """JSON Schema validation via ``jsonschema``.

    ``jsonschema`` is one of exactly two third-party runtime dependencies in this project
    and it is already present on the target interpreter (4.10.3), so every declared check
    runs with no install step.

    Stateless and side-effect free. It holds no cache keyed on a schema's identity: two
    different schema objects can be equal and one mapping can be mutated between calls,
    so a cache here would be a correctness risk in exchange for microseconds.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `JsonSchemaValidator.__new__(JsonSchemaValidator)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ()

    @admits(
        payload=ESTABLISHED_HERE(
            "UNVALIDATED EXTERNAL INPUT, and this call IS the establishment. Requiring a "
            "type here would claim the very property this boundary exists to determine, "
            "and it would also make the hostile inputs the validator must be asked about "
            "unaskable. CARRIER MEASURED: the payload is established against the adapter's "
            "DECLARED schema and a non-conforming one becomes SchemaRejection with a class "
            "and a location and is never coerced — "
            "tests/test_collector_validation.py, and the runner records it MALFORMED."
        ),
        schema=ESTABLISHED_HERE(
            "CD-BP-003. The declared schema arrives from a SourceAdapter's "
            "response_schema, a Protocol member returning Mapping[str, Any]; requiring "
            "exactly dict would forbid an adapter from declaring its schema through any "
            "other mapping, which is a constraint on foreign implementations this system "
            "has no business imposing. CARRIER MEASURED: the body establishes it — "
            "SCHEMA_NOT_A_MAPPING for a non-mapping, SCHEMA_REMOTE_REF_FORBIDDEN for a "
            "remote $ref, SCHEMA_UNUSABLE_* for anything jsonschema itself refuses, each a "
            "SchemaDeclarationInvalid raised as OUR defect and measured in "
            "tests/test_collector_validation.py."
        ),
    )
    def validate(self, payload: object, schema: Mapping[str, Any]) -> None:
        # Imported at point of use so this module imports cleanly for inspection even
        # where the dependency is absent, and so nothing is imported by a test that only
        # reads the protocol.
        import jsonschema

        if not isinstance(schema, AbcMapping):
            raise SchemaDeclarationInvalid("SCHEMA_NOT_A_MAPPING")
        if not local_refs_only(schema):
            raise SchemaDeclarationInvalid("SCHEMA_REMOTE_REF_FORBIDDEN")

        try:
            validator_cls = jsonschema.validators.validator_for(schema)
            validator_cls.check_schema(schema)
            validator = validator_cls(schema)
            errors = list(validator.iter_errors(payload))
        except SchemaDeclarationInvalid:
            raise
        except Exception as exc:
            # The schema itself, or the validator built from it, is unusable. Ours, not
            # theirs. The exception's text is deliberately not carried: a schema
            # compilation message can quote the schema, and a declared schema may name
            # an environment variable or an internal host.
            raise SchemaDeclarationInvalid(
                f"SCHEMA_UNUSABLE_{_sanitise(type(exc).__name__)}"
            ) from exc

        if not errors:
            return

        first = _first_error(errors)
        raise SchemaRejection(
            error_class=f"JSONSCHEMA_{_sanitise(str(first.validator))}",
            instance_path=json_pointer(list(first.absolute_path)),
        )


def _first_error(errors: Sequence[Any]) -> Any:
    """The error to report, chosen deterministically.

    Sorted by the RENDERED pointer rather than by ``error.path``. ``error.path`` is a
    deque of mixed ``str`` property names and ``int`` array indices, and sorting those
    against each other raises ``TypeError`` on this interpreter — a latent crash that
    only fires when one response happens to be malformed in two places of different
    kinds, which is precisely the moment nobody wants a crash in the collector.
    """
    return min(
        errors,
        key=lambda error: (
            len(error.absolute_path),
            json_pointer(list(error.absolute_path)),
            str(error.validator),
        ),
    )


def _sanitise(token: object) -> str:
    """Uppercase and reduce to ``[A-Z0-9_]``.

    The failing keyword comes from a schema, and a schema is data. Sanitising means an
    error class is always a safe, comparable token whatever the schema said.
    """
    cleaned = _ERROR_CLASS_SANITISER.sub("_", str(token).upper())
    return cleaned or "UNCLASSIFIED"


#: Convenience alias for the two failure classes, so a caller can catch the pair without
#: naming a common base class that does not exist. They deliberately share no ancestor
#: except ``Exception``: a shared base is somewhere a handler could come to treat our
#: defect and their malformation as one thing.
VALIDATION_FAILURES: tuple[type, ...] = (SchemaRejection, SchemaDeclarationInvalid)
