"""Publication REFUSES; it does not filter (deliverable A7, BLUEPRINT §3.5, §8).

BLUEPRINT §3, separation 5: "the engine validates the public envelope against the closed
schema *before* writing it, and on any unknown or private-classified key it writes nothing
and raises. Fail closed. A filter that strips private fields is the wrong shape: it
succeeds quietly on input it should have rejected loudly."

Two things are tested here and they are not the same thing:

* the refusal FIRES, against a wide class of violations rather than the one instance a
  plant will use; and
* the refusal is a REFUSAL — nothing is returned, nothing is repaired, and the candidate
  is not mutated. A guard that quietly sanitises has failed even when it "caught" the
  problem.

CD-AC-002 is the criterion with three independent instruments, and this module holds the
third. The dispatch warns that Assurance will try to sneak a blended number past the
closed schema "via a helper, a comprehension, a ``getattr``, a dict round-trip, and a
module the later AST allowlist does not cover". Every one of those is a way of COMPUTING
the number; none of them changes the DOCUMENT that arrives here. So the tests below
exercise exactly that: the same blend arriving by five different construction routes, all
refused identically, because the contract judges the shape and has no opinion about the
provenance.
"""

from __future__ import annotations

import copy
import json

import pytest

from crash_detector.dials.dialset import DIAL_IDS, EQUITY_DIAL_ID, MONETARY_DIAL_ID
from crash_detector.publication.classification import (
    BOOK_ADJACENT_TOKENS,
    SECRET_BEARING_TOKENS,
    classify_key,
    key_tokens,
)
from crash_detector.publication.envelope_contract import (
    ENVELOPE_SCHEMA_VERSION,
    REFUSAL_NON_FINITE_NUMBER,
    REFUSAL_NON_JSON_VALUE,
    REFUSAL_NOT_A_JSON_OBJECT,
    REFUSAL_PRIVATE_CLASSIFIED_KEY,
    REFUSAL_SCHEMA_VIOLATION,
    REFUSAL_SECRET_BEARING_KEY,
    REFUSAL_UNKNOWN_KEY,
    EnvelopeSurface,
    PublicationRefused,
    refuse_unless_publishable,
)

SURFACES = (EnvelopeSurface.PUBLIC, EnvelopeSurface.PRIVATE)

UNKNOWN_DIAL = {
    "state": "UNKNOWN",
    "reason": "NO_REQUIRED_INPUTS_DECLARED",
    "since_utc": "2026-08-19T12:00:00Z",
    "missing_inputs": [],
    "detail_level": "elevated",
}

VALUE_DIAL = {
    "state": "VALUE",
    "score": 0.42,
    "as_of_utc": "2026-08-19T12:00:00Z",
    "inputs_used": ["src.a"],
    "contributions": [
        {"source_id": "src.a", "category": "volatility", "weight": 1.0,
         "contribution": 0.42}
    ],
    "detail_level": "elevated",
}

DEGRADED_DIAL = {
    "state": "DEGRADED",
    "score": 0.42,
    "as_of_utc": "2026-08-19T12:00:00Z",
    "missing_inputs": ["src.b"],
    "reason": "CONTRIBUTING_INPUTS_UNAVAILABLE",
    "contributions": [
        {"source_id": "src.a", "category": "volatility", "weight": 1.0,
         "contribution": 0.42}
    ],
    "detail_level": "elevated",
}


def _envelope(surface: EnvelopeSurface, **overrides) -> dict:
    """A minimal conforming envelope — the WO-2 shipped state: both dials UNKNOWN."""
    envelope = {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "as_of_utc": "2026-08-19T12:00:00Z",
        "published_utc": "2026-08-19T12:00:05Z",
        "regime": "UNKNOWN",
        "staleness_window_seconds": 3600.0,
        "inputs_used": [],
        "degraded_inputs": [],
        "config_snapshot_id": "cfg-wo2",
        EQUITY_DIAL_ID: copy.deepcopy(UNKNOWN_DIAL),
        MONETARY_DIAL_ID: copy.deepcopy(UNKNOWN_DIAL),
    }
    if surface is EnvelopeSurface.PRIVATE:
        envelope["classification"] = "PRIVATE"
    envelope.update(overrides)
    return envelope


def _refusal(envelope, surface) -> PublicationRefused:
    with pytest.raises(PublicationRefused) as caught:
        refuse_unless_publishable(envelope, surface=surface)
    return caught.value


# --- THE HAPPY PATH, SO THE REFUSALS MEAN SOMETHING ---------------------------------------- #

@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_the_wo2_shipped_envelope_is_publishable(surface):
    """Both dials UNKNOWN, no source registered. The doctrinally correct empty state.

    Without this the whole module could be passing because everything is refused.
    """
    assert refuse_unless_publishable(_envelope(surface), surface=surface) is None


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
@pytest.mark.parametrize("dial", [VALUE_DIAL, DEGRADED_DIAL, UNKNOWN_DIAL])
def test_each_reading_state_is_publishable_in_its_own_shape(surface, dial):
    envelope = _envelope(surface, **{EQUITY_DIAL_ID: copy.deepcopy(dial)})
    assert refuse_unless_publishable(envelope, surface=surface) is None


# --- THE FUNCTION IS A REFUSAL, NOT A FILTER ------------------------------------------------ #

def test_the_function_returns_nothing_so_it_cannot_be_mistaken_for_a_sanitiser():
    """There is nothing to assign from this call, and that is the design.

    ``envelope = refuse_unless_publishable(envelope, ...)`` yields ``None`` and fails at
    the next step, loudly, rather than publishing a quietly cleaned document.
    """
    assert refuse_unless_publishable(
        _envelope(EnvelopeSurface.PUBLIC), surface=EnvelopeSurface.PUBLIC
    ) is None


def test_the_api_offers_no_lever_to_soften_it():
    """No ``strict=False``, no ``drop_unknown``, no ``allow`` — every one of those is a
    lever somebody reaches for at 2am when publication is failing."""
    import inspect

    parameters = inspect.signature(refuse_unless_publishable).parameters
    assert set(parameters) == {"candidate", "surface"}
    assert parameters["surface"].default is inspect.Parameter.empty


def test_there_is_no_boolean_predicate_that_would_invite_a_filter_branch():
    """A predicate invites ``if not ok: envelope = clean(envelope)``."""
    import crash_detector.publication as publication

    for name in dir(publication):
        assert not name.startswith("is_publishable")
        assert "filter" not in name.lower()
        assert "sanitis" not in name.lower()
        assert "sanitiz" not in name.lower()


def test_a_refused_candidate_is_not_mutated():
    envelope = _envelope(EnvelopeSurface.PUBLIC, combined_stress=0.5)
    before = json.dumps(envelope, sort_keys=True)
    _refusal(envelope, EnvelopeSurface.PUBLIC)
    assert json.dumps(envelope, sort_keys=True) == before
    assert "combined_stress" in envelope


def test_an_accepted_candidate_is_not_mutated_either():
    envelope = _envelope(EnvelopeSurface.PUBLIC)
    before = json.dumps(envelope, sort_keys=True)
    refuse_unless_publishable(envelope, surface=EnvelopeSurface.PUBLIC)
    assert json.dumps(envelope, sort_keys=True) == before


# --- CD-AC-002: THE BLEND HAS NOWHERE TO GO -------------------------------------------------- #

@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
@pytest.mark.parametrize(
    "blend_key",
    [
        "combined_stress",
        "combined",
        "overall",
        "overall_stress",
        "blended_score",
        "composite_score",
        "aggregate",
        "mean_stress",
        "average",
        "total",
        "headline",
        "headline_number",
        "stress_index",
        "combinedStress",
        "COMBINED_STRESS",
        "x",
    ],
)
def test_a_third_combined_number_is_refused_whatever_it_is_called(surface, blend_key):
    """The allowlist is TOTAL, so this is not a list of forbidden names.

    Sixteen spellings including a single letter: the proposition is that there is nowhere
    for a third number, not that thirteen particular names are absent. A guard built
    against the one name the plant uses would pass the fourteenth.
    """
    refusal = _refusal(_envelope(surface, **{blend_key: 0.5}), surface)
    assert refusal.reason_class == REFUSAL_UNKNOWN_KEY
    assert refusal.key == blend_key


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_a_blend_nested_inside_a_dial_object_is_refused(surface):
    """Closure at EVERY level, not only at the root."""
    dial = copy.deepcopy(UNKNOWN_DIAL)
    dial["combined_stress"] = 0.5
    refusal = _refusal(_envelope(surface, **{EQUITY_DIAL_ID: dial}), surface)
    assert refusal.reason_class == REFUSAL_UNKNOWN_KEY
    assert refusal.pointer == f"/{EQUITY_DIAL_ID}"


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_a_blend_nested_inside_an_array_element_is_refused(surface):
    """Wrapping a field in a list is the cheapest way past a scan that stops at objects."""
    dial = copy.deepcopy(VALUE_DIAL)
    dial["contributions"][0]["combined_stress"] = 0.5
    refusal = _refusal(_envelope(surface, **{EQUITY_DIAL_ID: dial}), surface)
    assert refusal.reason_class == REFUSAL_UNKNOWN_KEY
    assert refusal.pointer == f"/{EQUITY_DIAL_ID}/contributions/0"


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_a_third_dial_slot_is_refused(surface):
    """Two dials. A third is a PID amendment, not an envelope edit."""
    refusal = _refusal(
        _envelope(surface, systemic_stress=copy.deepcopy(UNKNOWN_DIAL)), surface
    )
    assert refusal.reason_class == REFUSAL_UNKNOWN_KEY
    assert refusal.key == "systemic_stress"


@pytest.mark.parametrize(
    "construction",
    ["literal", "helper", "comprehension", "getattr", "dict_round_trip", "json_reparse"],
)
def test_the_same_blend_is_refused_by_every_construction_route(construction):
    """The contract judges the DOCUMENT, and has no opinion about how it was built.

    The dispatch warns that Assurance will try a helper, a comprehension, a ``getattr``, a
    dict round-trip and a module the AST allowlist does not cover. Each of those changes
    how the number is COMPUTED; none changes the key it lands under. That is precisely why
    the schema is the instrument that guards the class here, and why the AST check exists
    separately to guard the computation.
    """
    equity, monetary = 0.4, 0.6

    if construction == "literal":
        payload = {"combined_stress": 0.5}
    elif construction == "helper":
        payload = {"combined_stress": _blend(equity, monetary)}
    elif construction == "comprehension":
        payload = {
            key: (equity + monetary) / 2 for key in ("combined_stress",)
        }
    elif construction == "getattr":
        holder = _Holder(equity, monetary)
        payload = {
            "combined_stress": (getattr(holder, "equity") + getattr(holder, "monetary"))
            / 2
        }
    elif construction == "dict_round_trip":
        staging = dict(_envelope(EnvelopeSurface.PUBLIC))
        staging["combined_stress"] = (equity + monetary) / 2
        payload = {"combined_stress": staging.pop("combined_stress")}
    else:
        payload = json.loads(json.dumps({"combined_stress": (equity + monetary) / 2}))

    refusal = _refusal(
        _envelope(EnvelopeSurface.PUBLIC, **payload), EnvelopeSurface.PUBLIC
    )
    assert refusal.reason_class == REFUSAL_UNKNOWN_KEY
    assert refusal.key == "combined_stress"


def _blend(a: float, b: float) -> float:
    """A helper that computes a blend. The schema refuses its output all the same."""
    return (a + b) / 2


class _Holder:
    def __init__(self, equity: float, monetary: float) -> None:
        self.equity = equity
        self.monetary = monetary


# --- CD-AC-001: AN UNKNOWN READING CANNOT CARRY A NUMBER --------------------------------------- #

@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_an_unknown_reading_carrying_a_score_is_refused(surface):
    """CD-AC-001 held in the contract: absence has no shape that carries a number."""
    dial = copy.deepcopy(UNKNOWN_DIAL)
    dial["score"] = 0.0
    refusal = _refusal(_envelope(surface, **{EQUITY_DIAL_ID: dial}), surface)
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION
    assert refusal.pointer == f"/{EQUITY_DIAL_ID}"


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_a_value_reading_with_no_inputs_is_refused(surface):
    """A reading computed from nothing is Unknown, not a value."""
    dial = copy.deepcopy(VALUE_DIAL)
    dial["inputs_used"] = []
    refusal = _refusal(_envelope(surface, **{EQUITY_DIAL_ID: dial}), surface)
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_a_degraded_reading_with_nothing_missing_is_refused(surface):
    """A reading with nothing missing is a Value, not a degradation."""
    dial = copy.deepcopy(DEGRADED_DIAL)
    dial["missing_inputs"] = []
    refusal = _refusal(_envelope(surface, **{EQUITY_DIAL_ID: dial}), surface)
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_an_unrecognised_reading_state_is_refused(surface):
    """Three constructors. A fourth state has no branch and therefore no rendering."""
    dial = copy.deepcopy(UNKNOWN_DIAL)
    dial["state"] = "PROBABLY_FINE"
    refusal = _refusal(_envelope(surface, **{EQUITY_DIAL_ID: dial}), surface)
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_a_score_that_is_a_string_is_refused_rather_than_coerced(surface):
    dial = copy.deepcopy(VALUE_DIAL)
    dial["score"] = "0.42"
    refusal = _refusal(_envelope(surface, **{EQUITY_DIAL_ID: dial}), surface)
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_a_score_that_is_a_boolean_is_refused(surface):
    """``float(True)`` is ``1.0``. JSON Schema's ``number`` excludes booleans, and this
    asserts that it actually does rather than assuming it."""
    dial = copy.deepcopy(VALUE_DIAL)
    dial["score"] = True
    refusal = _refusal(_envelope(surface, **{EQUITY_DIAL_ID: dial}), surface)
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION


# --- CD-AC-006: BOOK-ADJACENT KEYS ------------------------------------------------------------- #

@pytest.mark.parametrize(
    "key",
    [
        "portfolio_value",
        "portfolioValue",
        "PORTFOLIO-VALUE",
        "holdings",
        "position_size",
        "book_value",
        "nav",
        "pnl",
        "p_n_l",
        "broker_account",
        "order_id",
        "isin",
        "exposure_gbp",
        "unrealised_gain",
    ],
)
def test_a_book_adjacent_key_is_refused_on_the_public_surface_as_what_it_is(key):
    """Named as book-adjacent rather than as an anonymous unknown property.

    Both refusals would fire; only one tells the reader that the repair is to remove the
    key rather than to add it to the allowlist.
    """
    refusal = _refusal(
        _envelope(EnvelopeSurface.PUBLIC, **{key: 1.0}), EnvelopeSurface.PUBLIC
    )
    assert refusal.reason_class == REFUSAL_PRIVATE_CLASSIFIED_KEY
    assert refusal.key == key


def test_a_book_adjacent_key_nested_deep_inside_an_array_is_still_found():
    dial = copy.deepcopy(VALUE_DIAL)
    dial["contributions"][0]["holdings"] = 12
    refusal = _refusal(
        _envelope(EnvelopeSurface.PUBLIC, **{EQUITY_DIAL_ID: dial}),
        EnvelopeSurface.PUBLIC,
    )
    assert refusal.reason_class == REFUSAL_PRIVATE_CLASSIFIED_KEY
    assert refusal.pointer == f"/{EQUITY_DIAL_ID}/contributions/0/holdings"


def test_a_book_adjacent_key_is_still_refused_on_the_private_surface_for_now():
    """Book content is legitimate on the private side and the ALLOWLIST is still closed.

    WO-2 ships the private envelope with no book fields declared, because which private
    fields exist is a product decision owed at WO-5 (CD-D-004). So the refusal here is
    UNKNOWN_KEY, not PRIVATE_CLASSIFIED_KEY, and that is the honest reason: the field is
    permitted in principle and undeclared in fact.
    """
    refusal = _refusal(
        _envelope(EnvelopeSurface.PRIVATE, portfolio_value=1.0), EnvelopeSurface.PRIVATE
    )
    assert refusal.reason_class == REFUSAL_UNKNOWN_KEY


def test_a_private_envelope_offered_to_the_public_surface_is_refused_on_its_own_label():
    refusal = _refusal(
        _envelope(EnvelopeSurface.PRIVATE), EnvelopeSurface.PUBLIC
    )
    assert refusal.reason_class == REFUSAL_UNKNOWN_KEY
    assert refusal.key == "classification"


def test_a_public_envelope_offered_to_the_private_surface_is_refused_for_its_missing_label():
    """A document cannot arrive at the private table having lost the one label that says
    where it may go."""
    refusal = _refusal(_envelope(EnvelopeSurface.PUBLIC), EnvelopeSurface.PRIVATE)
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION


def test_a_mislabelled_classification_is_refused():
    refusal = _refusal(
        _envelope(EnvelopeSurface.PRIVATE, classification="PUBLIC"),
        EnvelopeSurface.PRIVATE,
    )
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION


# --- SECRETS: REFUSED ON BOTH SURFACES ------------------------------------------------------------ #

@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
@pytest.mark.parametrize(
    "key",
    ["api_key", "apiKey", "auth_token", "bearer_token", "client_secret", "password",
     "session_id", "private_key", "signature"],
)
def test_a_secret_bearing_key_is_refused_on_both_surfaces(surface, key):
    """A secret is referenced by environment-variable NAME at the point of use and is
    never carried in a record (PBG-SEC-002, non-waivable). There is no surface it may
    appear on, which is why this one check applies to both."""
    refusal = _refusal(_envelope(surface, **{key: "value"}), surface)
    assert refusal.reason_class == REFUSAL_SECRET_BEARING_KEY
    assert refusal.key == key


def test_a_refusal_names_the_matched_token_and_never_the_value_under_the_key():
    """Standards Baseline §5: report class and location, never the matched value."""
    secret = "SYNTHETIC-MARKER-THAT-MUST-NOT-BE-RECORDED-0000"
    refusal = _refusal(
        _envelope(EnvelopeSurface.PUBLIC, api_key=secret), EnvelopeSurface.PUBLIC
    )
    rendered = " ".join(
        [str(refusal), refusal.reason_class, refusal.pointer, str(refusal.key),
         refusal.detail]
    )
    assert secret not in rendered
    assert "SYNTHETIC-MARKER" not in rendered


def test_no_refusal_message_ever_quotes_a_value_from_the_candidate():
    """``jsonschema``'s ``oneOf`` message renders the whole instance. This module builds
    its own messages from the keyword, the pointer and the key, never from the prose."""
    marker = "VALUE-THAT-MUST-NOT-APPEAR-IN-A-LOG"
    dial = copy.deepcopy(UNKNOWN_DIAL)
    dial["reason"] = marker
    dial["score"] = 0.0
    refusal = _refusal(
        _envelope(EnvelopeSurface.PUBLIC, **{EQUITY_DIAL_ID: dial}),
        EnvelopeSurface.PUBLIC,
    )
    assert marker not in str(refusal)
    assert marker not in refusal.detail


# --- THE HONESTY FIELDS ARE NOT OPTIONAL ------------------------------------------------------------ #

@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
@pytest.mark.parametrize(
    "field_name",
    [
        "schema_version",
        "as_of_utc",
        "published_utc",
        "regime",
        "staleness_window_seconds",
        "inputs_used",
        "degraded_inputs",
        "config_snapshot_id",
    ],
)
def test_an_envelope_missing_any_honesty_field_cannot_be_published(surface, field_name):
    """§8, every field, not a sample. An envelope without them cannot be published."""
    envelope = _envelope(surface)
    del envelope[field_name]
    refusal = _refusal(envelope, surface)
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
@pytest.mark.parametrize("dial_id", DIAL_IDS)
def test_an_envelope_missing_a_dial_cannot_be_published(surface, dial_id):
    envelope = _envelope(surface)
    del envelope[dial_id]
    refusal = _refusal(envelope, surface)
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_a_null_honesty_field_is_refused_rather_than_read_as_absent(surface):
    """``null`` is not a value and it is not an absence; it is a shape nobody declared."""
    refusal = _refusal(_envelope(surface, regime=None), surface)
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_an_empty_regime_is_refused(surface):
    refusal = _refusal(_envelope(surface, regime=""), surface)
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
@pytest.mark.parametrize("window", [0, -1, 0.0])
def test_a_non_positive_staleness_window_is_refused(surface, window):
    """An unbounded or absent window is no window, and it is the cheapest way to make a
    stale reading render as current."""
    refusal = _refusal(_envelope(surface, staleness_window_seconds=window), surface)
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_an_unbumped_schema_version_is_refused(surface):
    refusal = _refusal(_envelope(surface, schema_version="2.0.0"), surface)
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION


# --- UTC IS THE ONLY TIMESTAMP ---------------------------------------------------------------------- #

@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-08-19T12:00:00+01:00",
        "2026-08-19T12:00:00+00:00",
        "2026-08-19T12:00:00",
        "2026-08-19 12:00:00Z",
        "2026-08-19",
        "19/08/2026 12:00:00",
        1755604800,
    ],
)
def test_a_timestamp_that_is_not_utc_with_an_explicit_z_is_refused(surface, timestamp):
    """Standards Baseline §9, enforced by the contract itself.

    ``+00:00`` is refused alongside ``+01:00``: one canonical rendering, so two documents
    of the same instant compare equal as strings.
    """
    refusal = _refusal(_envelope(surface, as_of_utc=timestamp), surface)
    assert refusal.reason_class == REFUSAL_SCHEMA_VIOLATION


# --- WHAT JSON CANNOT CARRY ---------------------------------------------------------------------- #

@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
@pytest.mark.parametrize("number", [float("nan"), float("inf"), float("-inf")])
def test_a_non_finite_number_is_refused_before_it_reaches_a_serialiser(surface, number):
    """``json.dumps`` renders these as the bare tokens ``NaN`` and ``Infinity``, which are
    not valid JSON. An envelope that passes a schema and then serialises to something no
    consumer can parse has failed in the least useful order."""
    refusal = _refusal(_envelope(surface, staleness_window_seconds=number), surface)
    assert refusal.reason_class == REFUSAL_NON_FINITE_NUMBER


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_a_non_json_value_is_refused_rather_than_str_ed_by_a_later_serialiser(surface):
    from datetime import datetime, timezone

    refusal = _refusal(
        _envelope(surface, as_of_utc=datetime(2026, 8, 19, tzinfo=timezone.utc)), surface
    )
    assert refusal.reason_class == REFUSAL_NON_JSON_VALUE


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
def test_a_non_string_object_key_is_refused(surface):
    """``json.dumps`` would silently coerce ``{1: x}`` into ``{"1": x}``."""
    envelope = _envelope(surface)
    envelope[EQUITY_DIAL_ID] = {1: "one"}
    refusal = _refusal(envelope, surface)
    assert refusal.reason_class == REFUSAL_NON_JSON_VALUE


@pytest.mark.parametrize("surface", SURFACES, ids=lambda s: s.value)
@pytest.mark.parametrize("candidate", [None, [], "an envelope", 7, 0.5, True])
def test_something_that_is_not_a_json_object_is_refused(surface, candidate):
    refusal = _refusal(candidate, surface)
    assert refusal.reason_class == REFUSAL_NOT_A_JSON_OBJECT


def test_the_surface_must_be_declared_and_cannot_be_a_string():
    with pytest.raises(TypeError):
        refuse_unless_publishable(_envelope(EnvelopeSurface.PUBLIC), surface="public")


# --- THE CLASSIFICATION REGISTER ITSELF -------------------------------------------------------------- #

@pytest.mark.parametrize(
    "key,expected",
    [
        ("portfolio_value", ("portfolio", "value")),
        ("portfolioValue", ("portfolio", "value")),
        ("PORTFOLIO-VALUE", ("portfolio", "value")),
        ("p_n_l", ("p", "n", "l")),
        ("dial2score", ("dial", "2", "score")),
        ("", ()),
    ],
)
def test_a_key_is_tokenised_across_every_casing_convention(key, expected):
    assert key_tokens(key) == expected


def test_weight_is_deliberately_not_classified():
    """A contribution weight is a model coefficient and is on the public allowlist.

    A false positive in a fail-closed check is an outage, and the first response to an
    outage is to weaken the check — so the register is specific rather than sweeping.
    """
    assert "weight" not in BOOK_ADJACENT_TOKENS
    assert classify_key("weight") is None
    assert classify_key("contribution") is None


def test_the_two_registers_do_not_overlap():
    assert BOOK_ADJACENT_TOKENS & SECRET_BEARING_TOKENS == frozenset()


def test_secret_bearing_is_reported_ahead_of_book_adjacent_where_a_key_is_both():
    """It is the stricter refusal: a book-adjacent key has a surface it may legitimately
    appear on, and a secret-bearing key has none."""
    classification, _ = classify_key("broker_api_key")
    assert classification == "SECRET_BEARING"


def test_a_non_string_key_is_a_type_error_rather_than_a_silent_pass():
    with pytest.raises(TypeError):
        classify_key(7)  # type: ignore[arg-type]
