"""The two closed envelope contracts, as DOCUMENTS (deliverable A7, BLUEPRINT §3, §8).

This module tests the schema files themselves — their closure, their allowlists and their
agreement with the Python types they mirror. The refusal BEHAVIOUR is in
``test_publication_refusal.py``.

The closure tests here are deliberately STRUCTURAL: they walk the whole document and
assert the property of every subschema, rather than checking the handful of places
somebody remembered. An allowlist is only total if it is total everywhere, and the way a
closed schema stops being closed is that a new nested object is added without
``additionalProperties: false`` — a change that no test naming today's objects would
notice.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from crash_detector.dials.dialset import DIAL_IDS, EQUITY_DIAL_ID, MONETARY_DIAL_ID
from crash_detector.publication.classification import classify_key
from crash_detector.publication.envelope_contract import (
    CONTRACTS_DIR_ENV_VAR,
    ENVELOPE_SCHEMA_VERSION,
    ContractUnavailable,
    EnvelopeSurface,
    contracts_dir,
    load_envelope_schema,
    schema_path_for,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

#: The eight honesty fields BLUEPRINT §8 marks required, verbatim. An envelope cannot be
#: published without them.
HONESTY_FIELDS = (
    "schema_version",
    "as_of_utc",
    "published_utc",
    "regime",
    "staleness_window_seconds",
    "inputs_used",
    "degraded_inputs",
    "config_snapshot_id",
)

SURFACES = (EnvelopeSurface.PUBLIC, EnvelopeSurface.PRIVATE)


def _walk(node, pointer=""):
    """Every ``(node, pointer)`` in a JSON document."""
    yield (node, pointer)
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk(value, f"{pointer}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, f"{pointer}/{index}")


# --- THE FILES EXIST WHERE THE DISPATCH SAYS ---------------------------------------------- #

def test_both_contracts_live_in_contracts_and_not_in_the_reserved_schemas_directory():
    """``schemas/`` at the project root is RESERVED by the framework (CD-FWK-001)."""
    assert contracts_dir() == REPO_ROOT / "contracts"
    for surface in SURFACES:
        assert schema_path_for(surface).is_file()
    assert not (REPO_ROOT / "schemas").exists() or not list(
        (REPO_ROOT / "schemas").glob("*envelope*")
    )


def test_the_contracts_directory_is_configurable_from_the_environment(monkeypatch):
    """Configuration from the environment; no host-specific absolute path in the source."""
    monkeypatch.setenv(CONTRACTS_DIR_ENV_VAR, "/somewhere/else")
    assert contracts_dir() == pathlib.Path("/somewhere/else")


def test_an_unreachable_contract_fails_and_is_never_treated_as_a_pass(monkeypatch, tmp_path):
    """Where a check cannot reach its authentic target it fails (Standards Baseline §16)."""
    monkeypatch.setenv(CONTRACTS_DIR_ENV_VAR, str(tmp_path))
    with pytest.raises(ContractUnavailable):
        load_envelope_schema(EnvelopeSurface.PUBLIC)


def test_a_contract_that_is_not_valid_json_fails_loudly(monkeypatch, tmp_path):
    monkeypatch.setenv(CONTRACTS_DIR_ENV_VAR, str(tmp_path))
    (tmp_path / "public_envelope.schema.json").write_text("{ not json", encoding="utf-8")
    with pytest.raises(ContractUnavailable):
        load_envelope_schema(EnvelopeSurface.PUBLIC)


def test_a_contract_with_a_remote_ref_is_refused(monkeypatch, tmp_path):
    """Resolving one would make publication validation perform an outbound fetch."""
    monkeypatch.setenv(CONTRACTS_DIR_ENV_VAR, str(tmp_path))
    (tmp_path / "public_envelope.schema.json").write_text(
        json.dumps({"$ref": "https://example.invalid/s.json"}), encoding="utf-8"
    )
    with pytest.raises(ContractUnavailable):
        load_envelope_schema(EnvelopeSurface.PUBLIC)


def test_each_load_returns_a_fresh_copy_so_a_caller_cannot_open_the_closed_schema():
    """A closed schema that whoever holds a reference can open is not closed."""
    first = load_envelope_schema(EnvelopeSurface.PUBLIC)
    first["additionalProperties"] = True
    second = load_envelope_schema(EnvelopeSurface.PUBLIC)
    assert second["additionalProperties"] is False


# --- CLOSURE, STRUCTURALLY, EVERYWHERE ----------------------------------------------------- #

@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_every_object_subschema_is_closed(surface):
    """``additionalProperties: false`` at EVERY level, not at the levels we remembered."""
    schema = load_envelope_schema(surface)
    open_nodes = []
    for node, pointer in _walk(schema):
        if not isinstance(node, dict):
            continue
        describes_object = node.get("type") == "object" or "properties" in node
        if not describes_object:
            continue
        if node.get("additionalProperties") is not False:
            open_nodes.append(pointer or "<root>")
    assert open_nodes == [], (
        f"{surface.value} envelope has object subschemas that are not closed: "
        f"{open_nodes}"
    )


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_no_subschema_reopens_the_allowlist_by_another_route(surface):
    """``patternProperties``, ``unevaluatedProperties`` and a truthy
    ``additionalProperties`` are three ways to have an allowlist that is not one."""
    schema = load_envelope_schema(surface)
    offenders = []
    for node, pointer in _walk(schema):
        if not isinstance(node, dict):
            continue
        for keyword in ("patternProperties", "unevaluatedProperties"):
            if keyword in node:
                offenders.append(f"{pointer}:{keyword}")
        if "additionalProperties" in node and node["additionalProperties"] is not False:
            offenders.append(f"{pointer}:additionalProperties")
    assert offenders == []


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_the_closure_scan_would_notice_a_newly_added_open_object(surface):
    """Prove the guard fails when the thing it guards is broken, at its own seam.

    A future nested object added without closure is the realistic way this schema stops
    being closed, so the scan is proved against exactly that mutation.
    """
    schema = load_envelope_schema(surface)
    schema["$defs"]["planted_open_object"] = {
        "type": "object",
        "properties": {"anything": {"type": "string"}},
    }
    open_nodes = [
        pointer
        for node, pointer in _walk(schema)
        if isinstance(node, dict)
        and (node.get("type") == "object" or "properties" in node)
        and node.get("additionalProperties") is not False
    ]
    assert "/$defs/planted_open_object" in open_nodes


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_every_ref_is_a_local_fragment(surface):
    schema = load_envelope_schema(surface)
    refs = [
        node["$ref"]
        for node, _ in _walk(schema)
        if isinstance(node, dict) and "$ref" in node
    ]
    assert refs, "no $ref found; the check would pass vacuously"
    assert all(isinstance(ref, str) and ref.startswith("#") for ref in refs)


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_the_contract_is_itself_a_valid_json_schema(surface):
    import jsonschema

    schema = load_envelope_schema(surface)
    jsonschema.validators.validator_for(schema).check_schema(schema)


# --- THE ALLOWLIST IS EXACTLY WHAT §8 REQUIRES ---------------------------------------------- #

def test_the_public_allowlist_is_the_two_dials_and_the_eight_honesty_fields_and_nothing_else():
    """"Exactly", per the dispatch. Anything more is a field nobody ratified."""
    schema = load_envelope_schema(EnvelopeSurface.PUBLIC)
    assert set(schema["properties"]) == set(HONESTY_FIELDS) | set(DIAL_IDS)


def test_the_public_schema_declares_no_classification_field():
    """So a private envelope validated against the public contract is rejected on its
    own label before anything else about it is considered."""
    schema = load_envelope_schema(EnvelopeSurface.PUBLIC)
    assert "classification" not in schema["properties"]


def test_the_private_allowlist_is_the_public_one_plus_its_classification():
    schema = load_envelope_schema(EnvelopeSurface.PRIVATE)
    assert set(schema["properties"]) == set(HONESTY_FIELDS) | set(DIAL_IDS) | {
        "classification"
    }
    assert schema["properties"]["classification"]["const"] == "PRIVATE"


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_every_honesty_field_is_required(surface):
    """§8: the schema marks them required, so an envelope cannot be published without them."""
    schema = load_envelope_schema(surface)
    assert set(HONESTY_FIELDS) <= set(schema["required"])


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_both_dials_are_required(surface):
    schema = load_envelope_schema(surface)
    assert set(DIAL_IDS) <= set(schema["required"])


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_every_declared_property_is_required(surface):
    """No optional field on the allowlist.

    An optional field is a field a consumer must handle the absence of, and "sometimes
    present" is where a reader learns to guess (Standards Baseline §8).
    """
    schema = load_envelope_schema(surface)
    assert set(schema["properties"]) == set(schema["required"])


# --- THERE IS NOWHERE FOR A THIRD NUMBER --------------------------------------------------- #

@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
@pytest.mark.parametrize(
    "blend_key",
    [
        "combined_stress",
        "combined",
        "overall",
        "overall_stress",
        "blended_score",
        "composite",
        "aggregate",
        "mean_stress",
        "total_stress",
        "headline",
        "headline_number",
        "stress_index",
        "combinedStress",
    ],
)
def test_no_blend_key_appears_anywhere_in_either_contract(surface, blend_key):
    """The schema has no PLACE for a third, combined number.

    Thirteen spellings rather than the one the plant will use: the proposition is that
    there is nowhere to put a blend, not that one particular name is absent.
    """
    schema = load_envelope_schema(surface)
    for node, _ in _walk(schema):
        if isinstance(node, dict) and "properties" in node:
            assert blend_key not in node["properties"]


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_the_two_dials_are_the_only_dial_slots(surface):
    schema = load_envelope_schema(surface)
    dial_slots = [
        key
        for key, value in schema["properties"].items()
        if isinstance(value, dict) and value.get("$ref") == "#/$defs/dial_reading"
    ]
    assert sorted(dial_slots) == sorted([EQUITY_DIAL_ID, MONETARY_DIAL_ID])


# --- THE CONTRACT MIRRORS THE PYTHON TYPES --------------------------------------------------- #

@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_the_dial_keys_are_the_declared_dial_ids(surface):
    """One name for a dial, not two that must be kept in step by hand."""
    schema = load_envelope_schema(surface)
    assert set(DIAL_IDS) <= set(schema["properties"])


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_the_declared_states_are_the_three_reading_constructors(surface):
    from crash_detector.dials.reading import READING_CONSTRUCTORS

    schema = load_envelope_schema(surface)
    declared = set(schema["$defs"]["dial_reading"]["properties"]["state"]["enum"])
    assert declared == {
        constructor.__name__.upper() for constructor in READING_CONSTRUCTORS
    }


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_the_unknown_branch_declares_no_score_property_at_all(surface):
    """CD-AC-001 held in the contract.

    Not "score must be null" and not "score is optional": there is no score property, so
    an unknown reading carrying a number is unrepresentable rather than discouraged.
    """
    schema = load_envelope_schema(surface)
    unknown = schema["$defs"]["dial_reading_unknown"]
    assert "score" not in unknown["properties"]
    assert unknown["additionalProperties"] is False


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_the_declared_schema_version_matches_the_python_constant(surface):
    """Two constants that must agree is one constant with a bug scheduled."""
    schema = load_envelope_schema(surface)
    assert schema["properties"]["schema_version"]["const"] == ENVELOPE_SCHEMA_VERSION


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_no_score_carries_a_declared_range(surface):
    """A declared range is a declared scale, and the scale of a dial is product meaning.

    CD-D-005 is owed by the Product Owner and PID §3.6 forbids unexplained mappings; an
    invented bound would reject legitimate readings, quietly, inside a validator. See
    finding CD-ENG-F06.
    """
    schema = load_envelope_schema(surface)
    for node, pointer in _walk(schema):
        if not isinstance(node, dict) or "properties" not in node:
            continue
        score = node["properties"].get("score")
        if not isinstance(score, dict):
            continue
        for bound in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"):
            assert bound not in score, f"a scale was invented at {pointer}"


# --- NO CLASSIFIED KEY IS ON EITHER ALLOWLIST ------------------------------------------------- #

@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_no_declared_key_anywhere_is_itself_classified(surface):
    """The two instruments must not contradict each other.

    A key that the allowlist declares and the classification register forbids is a field
    that can never be published — an outage waiting for the first envelope that carries
    it, and the first response to an outage is to weaken the check.
    """
    schema = load_envelope_schema(surface)
    conflicts = []
    for node, pointer in _walk(schema):
        if not isinstance(node, dict) or "properties" not in node:
            continue
        for key in node["properties"]:
            if classify_key(key) is not None:
                conflicts.append(f"{pointer}/{key}")
    assert conflicts == []


# --- TIMESTAMPS ------------------------------------------------------------------------------- #

@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_utc_is_enforced_by_pattern_and_not_by_format(surface):
    """``format`` is an annotation by default, and an annotation is not a refusal."""
    schema = load_envelope_schema(surface)
    timestamp = schema["$defs"]["utc_timestamp"]
    assert "pattern" in timestamp
    assert timestamp["pattern"].endswith("Z$")
    for node, _ in _walk(schema):
        if isinstance(node, dict):
            assert "format" not in node
