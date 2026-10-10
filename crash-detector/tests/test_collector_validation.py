"""Boundary validation, and what may not leave it (deliverable A4, Standards Baseline §4).

The property that matters most here is not "invalid payloads are rejected" — that is
``jsonschema``'s job and it does it. It is that **nothing value-bearing escapes**.
``jsonschema``'s own messages embed the offending instance, and a hostile response's
values may include a secret the source echoed back (``PBG-SEC-002``, ``PBG-EVID-003``,
both non-waivable). What leaves this module is a sanitised classification and a JSON
Pointer built from property names and array indices.
"""

from __future__ import annotations

import pytest

from crash_detector.collectors.validation import (
    MAX_INSTANCE_PATH_LENGTH,
    JsonSchemaValidator,
    SchemaDeclarationInvalid,
    SchemaRejection,
    json_pointer,
    local_refs_only,
)
from crash_detector.observations import Malformed

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["reading"],
    "properties": {
        "reading": {"type": "number"},
        "series": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"v": {"type": "number"}},
            },
        },
    },
}

#: A SYNTHETIC marker, not a secret and not shaped like a real credential either.
#: It stands in for "a value the source echoed back that must never be recorded". A
#: realistic-looking token here would be a value that a later secret scanner flags and
#: that a reader has to decide about — and the point of the test survives intact
#: without it (PBG-SEC-002, Standards Baseline §5).
SECRET_SHAPED = "SYNTHETIC-MARKER-THAT-MUST-NOT-BE-RECORDED-0000"


def _validator() -> JsonSchemaValidator:
    return JsonSchemaValidator()


# --- CONFORMANCE ------------------------------------------------------------------------ #

def test_a_conforming_payload_validates_silently():
    assert _validator().validate({"reading": 1.0}, SCHEMA) is None


@pytest.mark.parametrize(
    "payload,expected_class,expected_path",
    [
        ({"reading": "words"}, "JSONSCHEMA_TYPE", "/reading"),
        ({}, "JSONSCHEMA_REQUIRED", ""),
        ({"reading": 1.0, "extra": 2}, "JSONSCHEMA_ADDITIONALPROPERTIES", ""),
        ({"reading": 1.0, "series": [{"v": 1.0}, {"v": "words"}]},
         "JSONSCHEMA_TYPE", "/series/1/v"),
        ({"reading": 1.0, "series": [{"nope": 1.0}]},
         "JSONSCHEMA_ADDITIONALPROPERTIES", "/series/0"),
    ],
)
def test_a_non_conforming_payload_is_rejected_with_its_class_and_location(
    payload, expected_class, expected_path
):
    with pytest.raises(SchemaRejection) as caught:
        _validator().validate(payload, SCHEMA)
    assert caught.value.error_class == expected_class
    assert caught.value.instance_path == expected_path


# --- NOTHING VALUE-BEARING ESCAPES -------------------------------------------------------- #

def test_a_rejection_carries_no_value_from_the_payload():
    """The single most important property of this module.

    ``jsonschema``'s message for this payload quotes the offending value verbatim —
    ``'<the value>' is not of type 'number'``. None of that may reach the exception, its
    message, or the row built from it.
    """
    with pytest.raises(SchemaRejection) as caught:
        _validator().validate({"reading": SECRET_SHAPED}, SCHEMA)

    rejection = caught.value
    rendered = " ".join([rejection.error_class, rejection.instance_path, str(rejection)])
    assert SECRET_SHAPED not in rendered

    stored = Malformed(
        schema_error_class=rejection.error_class,
        instance_path=rejection.instance_path,
    )
    assert SECRET_SHAPED not in repr(stored)


def test_a_rejection_carries_no_value_even_when_the_key_name_is_the_value():
    """A hostile response can put the secret in a KEY, so the key is reported and the
    row is bounded — but the additionalProperties error's LOCATION is the parent, not
    the key, so the value never becomes the classification either."""
    with pytest.raises(SchemaRejection) as caught:
        _validator().validate({"reading": 1.0, SECRET_SHAPED: 1}, SCHEMA)
    assert caught.value.error_class == "JSONSCHEMA_ADDITIONALPROPERTIES"
    assert SECRET_SHAPED not in caught.value.error_class


def test_the_error_class_is_sanitised_so_a_schema_cannot_smuggle_content_through_it():
    """The failing keyword comes from a schema, and a schema is data."""
    hostile = {"type": "object", "properties": {"a": {"type": "number"}},
               "additionalProperties": False}
    with pytest.raises(SchemaRejection) as caught:
        _validator().validate({"b": 1}, hostile)
    assert caught.value.error_class.replace("_", "").isalnum()
    assert caught.value.error_class.upper() == caught.value.error_class


# --- JSON POINTERS ------------------------------------------------------------------------ #

def test_the_root_pointer_is_the_empty_string_as_rfc_6901_defines_it():
    assert json_pointer([]) == ""


def test_a_pointer_escapes_slash_and_tilde():
    """Otherwise a property name containing a slash forges a deeper path than it occupies."""
    assert json_pointer(["a/b", "c~d"]) == "/a~1b/c~0d"


def test_a_pointer_mixes_property_names_and_array_indices():
    assert json_pointer(["series", 3, "v"]) == "/series/3/v"


def test_a_pointer_is_bounded_and_stays_within_what_the_row_will_accept():
    """The truncation marker must fit INSIDE the ceiling.

    Getting this wrong produces a pointer the ``Malformed`` constructor then refuses — a
    collector that crashes only on deeply nested malformed responses, which is to say
    only when a source is behaving badly.
    """
    pointer = json_pointer(["x" * 40] * 20)
    assert len(pointer) <= MAX_INSTANCE_PATH_LENGTH
    assert pointer.endswith("[truncated]")
    Malformed(schema_error_class="JSONSCHEMA_TYPE", instance_path=pointer)


def test_a_malformation_nested_past_the_pointer_ceiling_still_produces_a_storable_row():
    """The seam between the pointer producer and the row constructor, end to end.

    Nested deeply enough that the pointer must be truncated, with long property names so
    the ceiling is genuinely crossed. If the truncated pointer did not fit the row, the
    collector would raise here instead of recording a MALFORMED outcome — and it would do
    so only against a source producing deeply nested rubbish.
    """
    depth = 15
    name = "n" * 20
    leaf_schema: dict = {"type": "number"}
    schema: dict = leaf_schema
    for _ in range(depth):
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {name: schema},
        }
    payload: object = "words"
    for _ in range(depth):
        payload = {name: payload}

    with pytest.raises(SchemaRejection) as caught:
        _validator().validate(payload, schema)

    assert len(caught.value.instance_path) <= MAX_INSTANCE_PATH_LENGTH
    assert caught.value.instance_path.endswith("[truncated]")
    stored = Malformed(
        schema_error_class=caught.value.error_class,
        instance_path=caught.value.instance_path,
    )
    assert stored.instance_path == caught.value.instance_path


# --- OUR SCHEMA VERSUS THEIR PAYLOAD ------------------------------------------------------ #

@pytest.mark.parametrize(
    "schema,expected_prefix",
    [
        ("not a mapping", "SCHEMA_NOT_A_MAPPING"),
        (None, "SCHEMA_NOT_A_MAPPING"),
        ({"type": "not-a-json-schema-type"}, "SCHEMA_UNUSABLE_"),
        ({"required": "reading"}, "SCHEMA_UNUSABLE_"),
    ],
)
def test_our_broken_schema_raises_a_different_class_from_their_broken_payload(
    schema, expected_prefix
):
    """Recording our defect as MALFORMED would blame the source for our bug."""
    with pytest.raises(SchemaDeclarationInvalid) as caught:
        _validator().validate({"reading": 1.0}, schema)
    assert caught.value.error_class.startswith(expected_prefix)


def test_the_two_failure_classes_share_no_ancestor_but_exception():
    """A shared base is somewhere a handler comes to treat them as one thing."""
    assert not issubclass(SchemaRejection, SchemaDeclarationInvalid)
    assert not issubclass(SchemaDeclarationInvalid, SchemaRejection)
    assert set(SchemaRejection.__mro__) & set(SchemaDeclarationInvalid.__mro__) == {
        Exception,
        BaseException,
        object,
    }


# --- NO REMOTE $ref ------------------------------------------------------------------------ #

@pytest.mark.parametrize(
    "schema",
    [
        {"$ref": "https://example.invalid/s.json"},
        {"properties": {"a": {"$ref": "http://example.invalid/s.json"}}},
        {"$defs": {"x": {"items": {"$ref": "file:///etc/passwd"}}}},
        {"allOf": [{"$ref": "//example.invalid/s.json"}]},
        {"properties": {"a": {"$ref": 7}}},
    ],
)
def test_a_non_local_ref_anywhere_in_a_declared_schema_is_refused(schema):
    """Resolving one is an outbound network fetch performed inside a validation step.

    Checked over the WHOLE document: a remote reference three levels down fetches just as
    eagerly as one at the root, and nested is where somebody would put it.
    """
    assert local_refs_only(schema) is False
    with pytest.raises(SchemaDeclarationInvalid) as caught:
        _validator().validate({"reading": 1.0}, schema)
    assert caught.value.error_class == "SCHEMA_REMOTE_REF_FORBIDDEN"


def test_a_local_fragment_ref_is_permitted():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "properties": {"reading": {"$ref": "#/$defs/number"}},
        "$defs": {"number": {"type": "number"}},
    }
    assert local_refs_only(schema) is True
    assert _validator().validate({"reading": 1.0}, schema) is None
    with pytest.raises(SchemaRejection):
        _validator().validate({"reading": "words"}, schema)


# --- DETERMINISM ---------------------------------------------------------------------------- #

def test_a_payload_malformed_in_two_places_of_different_kinds_does_not_crash_the_sort():
    """The salvage's ``sorted(..., key=lambda e: list(e.path))`` raises TypeError here.

    ``error.path`` is a deque mixing ``str`` property names with ``int`` array indices,
    and comparing ``['series']`` against ``[0]`` is unorderable — a latent crash that
    only fires when a source is malformed in two different ways at once, which is
    exactly when nobody wants the collector to crash.
    """
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "reading": {"type": "number"},
            "series": {"type": "array", "items": {"type": "number"}},
        },
    }
    with pytest.raises(SchemaRejection) as caught:
        _validator().validate({"reading": "words", "series": ["words"]}, schema)
    assert caught.value.error_class == "JSONSCHEMA_TYPE"


def test_the_same_payload_always_reports_the_same_rejection():
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
    }
    seen = set()
    for _ in range(5):
        with pytest.raises(SchemaRejection) as caught:
            _validator().validate({"a": "x", "b": "y"}, schema)
        seen.add((caught.value.error_class, caught.value.instance_path))
    assert len(seen) == 1


# --- THE STORED ROW -------------------------------------------------------------------------- #

def test_malformed_defaults_to_the_root_pointer_which_is_a_real_location():
    assert Malformed(schema_error_class="X").instance_path == ""


@pytest.mark.parametrize("bad", ["reading", "reading/x", " /reading"])
def test_malformed_refuses_a_path_that_is_not_a_json_pointer(bad):
    with pytest.raises(ValueError):
        Malformed(schema_error_class="X", instance_path=bad)


def test_malformed_refuses_an_unbounded_path():
    with pytest.raises(ValueError):
        Malformed(
            schema_error_class="X",
            instance_path="/" + "x" * (MAX_INSTANCE_PATH_LENGTH + 1),
        )


def test_malformed_refuses_a_non_string_path():
    with pytest.raises(TypeError):
        Malformed(schema_error_class="X", instance_path=7)  # type: ignore[arg-type]
