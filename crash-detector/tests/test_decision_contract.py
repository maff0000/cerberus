"""DECISION-RULE.md §7'S DOCUMENT, FIELD BY FIELD — ``evaluator/contract.py`` (WO-1.3a round 8).

Offline and clock-free: every instant is a constant, the only files read are the two config
files the product ships and pytest's own ``tmp_path``, and no test here reaches a network or
a database. ``contract_for_row`` is a pure function of its arguments by design (its
docstring says why ``live_identity`` is the separate impure half), so most of what follows
states a row and reads the document back.

WHAT THESE TESTS ARE FOR, in the order the module docstring makes the claims:

* **The document is asserted WHOLE**, not key by key. §7's field names are the schema Epic 2
  reads and a test that probes three of them would pass against a document missing the rest,
  so :func:`test_a_resolvable_row_is_section_7s_document` and
  :func:`test_an_unknown_row_is_the_same_document_with_its_numbers_stated_absent` compare
  the entire returned dict against a literal written out here. The literals are SPELLED,
  not imported from the module under test — ``"decision-rule/v1"`` rather than
  ``SCHEMA_VERSION`` — because the published strings are the document's and a test that
  reads them out of the code could not notice them changing.
* **The ``dial_value_min``/``dial_value_max`` identity is proven against a LONG-FORM
  RE-SCORE** (:func:`test_the_bracket_equals_a_real_re_score_with_every_missing_input_imputed`).
  The module computes the bracket in closed form, ``breadth · f`` and ``breadth · f + (1 − f)``,
  and the closed form is only worth having if it really is the re-score. So that test does
  the re-score the long way — the REAL banded-weighted-mean executor
  (:func:`crash_detector.engine.mapping.compute`), run three times over one declared weight
  set: once over the inputs that were scored, once with every missing input given its band's
  ``calm`` value (score 0) and once with every missing input given its ``stress`` value
  (score 1) — and compares those two magnitudes against what the contract published. The
  weight set is deliberately non-uniform and only partly scored, and the test also asserts
  that the two closest WRONG derivations give materially different answers, so it
  discriminates rather than merely restating the algebra.
* **The refusals are provoked**, not avoided: a coverage fraction outside ``0..1`` and a
  ``0.0`` coverage on a row that carries a breadth, a row of the wrong type (including a
  SUBCLASS, which is what exact-type admission is for), and a dial id outside ``DIAL_IDS``.
* **``content_version`` is hashed over BYTES**, and the test proves the distinction rather
  than asserting the docstring: the fixture file's bytes contain a ``\\r\\n`` and a BOM, so
  hashing ``read_text()`` re-encoded gives a DIFFERENT digest — a test written over plain
  ASCII could not tell the two implementations apart.
* **``scored_coverage`` is checked against MATH.md's own worked R-10 numbers** (§1.4 item 10
  and §2.4 item 8): 46/48 for the equity dial while ``coverage`` reads 1.0, and 14/21 =
  0.667 for the monetary dial while ``coverage`` reads 0.905. Those two figures are the
  whole of what R-10 says is missing, so the test asserts both the honest number AND its
  difference from the existing disclosure.

Import route: ``PYTHONPATH=src:.`` from ``crash-detector/`` — ``pythonpath = ["src", "."]``
in ``pyproject.toml`` does it for ``pytest``.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest

from crash_detector.dials.dialset import EQUITY_DIAL_ID, MONETARY_DIAL_ID
from crash_detector.dials.scores import Contribution
from crash_detector.engine.mapping import compute
from crash_detector.engine.model import (DeclaredParameter, MappingKind, ModelProvenance,
                                         ModelSpec)
from crash_detector.engine.statistics import State
from evaluator.contract import (BUILD_SHA_ENV, BUILD_SHA_UNKNOWN, content_version,
                                contract_for_row, live_identity)
from evaluator.history_store import MachineStateRow
from ingestion.wiring import (MAPPING_YAML, SCALING_JSON, TIER_WEIGHT, _polarities, _rows,
                              build_wiring, coverage, scored_coverage)

#: The instant the row is dated by — the OLDEST input's, which is what the engine dates a
#: reading by and what spec §14 ruled is published unchanged (DECISION-RULE.md §7's own
#: "newest" is a wording bug in that document, raised separately).
AS_OF = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)

#: ``state_since``: EARLIER than ``as_of`` and not derived from it, because it is the answer
#: to a different question (which reading first reached this state) that only
#: :meth:`evaluator.history_store.MachineStateHistoryStore.state_since` can give.
STATE_SINCE = datetime(2026, 10, 13, 6, 30, tzinfo=timezone.utc)

#: The three identity values, stated rather than arranged: ``contract_for_row`` is pure and
#: takes them as arguments precisely so a test need not build an image or read a file.
BUILD_SHA = "0f1e2d3c4b5a69788796a5b4c3d2e1f0deadbeef"
SCALING_VERSION = "1" * 64
MAPPING_VERSION = "2" * 64

IDENTITY_ARGUMENTS = dict(
    build_sha=BUILD_SHA, scaling_version=SCALING_VERSION, mapping_version=MAPPING_VERSION
)

TEST_PROVENANCE = ModelProvenance(
    stands_for="TEST DOUBLE; the weight set below is a test fixture, not a product model",
    account="TEST DOUBLE; it exists to re-score a bracket the long way, see this module",
    decided_by="TEST DOUBLE; no product decision registers this model",
)


def _resolvable_row(**overrides) -> MachineStateRow:
    """A row for a dial that RESOLVED: a state and every statistic present."""
    row = dict(
        dial_id=EQUITY_DIAL_ID,
        as_of=AS_OF,
        machine_state=State.WATCH,
        candidate_state=State.WATCH,
        persistence_counter=2,
        acute_rising=True,
        breadth=0.4,
        acute=0.67,
        acute_from_master_id="equity_volatility",
        master_scores={"equity_volatility": 0.67, "equity_credit": 0.2},
        indicator_count=3,
        count_at_or_beyond=("hy_oas", "vix_level", "cboe_skew"),
    )
    row.update(overrides)
    return MachineStateRow(**row)


def _unknown_row(**overrides) -> MachineStateRow:
    """A row for a dial that could NOT be resolved: a stated absence, carrying no number."""
    row = dict(
        dial_id=EQUITY_DIAL_ID,
        as_of=AS_OF,
        machine_state=State.UNKNOWN,
        candidate_state=State.UNKNOWN,
        persistence_counter=0,
    )
    row.update(overrides)
    return MachineStateRow(**row)


def _shape(document: object) -> object:
    """``document``'s key structure with every leaf replaced by its presence."""
    if isinstance(document, dict):
        return {key: _shape(value) for key, value in sorted(document.items())}
    return "<leaf>"


# ========================================================================================= #
# 1 — THE WHOLE DOCUMENT, FOR A ROW THAT RESOLVED.
# ========================================================================================= #


def test_a_resolvable_row_is_section_7s_document():
    """Every §7 field, by the name §7 gives it, carrying what the row concluded.

    Asserted as ONE dict comparison. The two bracket arms go through ``pytest.approx``
    because they are the products of binary floats and nothing else here is: the point of
    the comparison is the field names and the values, not the last bit of 0.3.
    """
    document = contract_for_row(
        _resolvable_row(),
        state_since=STATE_SINCE,
        scored_weight_fraction=0.75,
        **IDENTITY_ARGUMENTS,
    )

    assert document == {
        "schema_version": "decision-rule/v1",
        "dial": "equity_crash",
        "as_of": "2026-10-14T12:00:00Z",
        # The bare state word, `State.name`, NOT the namespaced `state.watch` member value.
        "state": "WATCH",
        "state_since": "2026-10-13T06:30:00Z",
        "persistence_counter": 2,
        # SPEC §12: not emitted as 0.0 in any state, and the flag is true in every state so
        # that "not computed" can never be read as "computed as zero".
        "sizing_multiplier": None,
        "sizing_not_computed": True,
        "acute_rising": True,
        "statistics": {"breadth": 0.4, "acute": 0.67, "count": 3},
        "coverage_bracket": {
            "scored_weight_fraction": 0.75,
            "dial_value_min": pytest.approx(0.3),
            "dial_value_max": pytest.approx(0.55),
            "coverage_not_computed": False,
        },
        # SPEC §14 ruling: the gap stands as built, disclosed in band. WO-1.3d fills it.
        "inputs": None,
        "inputs_not_computed": True,
        "identity": {
            "build_sha": BUILD_SHA,
            "scaling_version": SCALING_VERSION,
            "mapping_version": MAPPING_VERSION,
            "decision_rule_version": "v1",
        },
    }


def test_the_published_document_recomputes_nothing_from_the_row():
    """The numbers published are the ROW's, including a row whose statistics are unusual.

    A second evaluation is not what §7 asks for: the document says what the evaluation that
    produced the row concluded. So a breadth of 0.0 — a real reading in which nothing scored
    above its calm band — is published AS 0.0 and not treated as an absence, and a
    ``persistence_counter`` of 0 is published as 0.
    """
    document = contract_for_row(
        _resolvable_row(breadth=0.0, acute=0.0, indicator_count=0, persistence_counter=0,
                        machine_state=State.CALM, candidate_state=State.CALM,
                        acute_rising=False),
        state_since=STATE_SINCE,
        scored_weight_fraction=0.5,
        **IDENTITY_ARGUMENTS,
    )

    assert document["state"] == "CALM"
    assert document["persistence_counter"] == 0
    assert document["acute_rising"] is False
    assert document["statistics"] == {"breadth": 0.0, "acute": 0.0, "count": 0}
    # breadth 0.0 still brackets: with half the weight unscored the dial value lies in
    # [0.0, 0.5], and that is a statement about this reading rather than an absence.
    assert document["coverage_bracket"]["dial_value_min"] == pytest.approx(0.0)
    assert document["coverage_bracket"]["dial_value_max"] == pytest.approx(0.5)
    assert document["coverage_bracket"]["coverage_not_computed"] is False


# ========================================================================================= #
# 2 — THE SAME DOCUMENT FOR AN UNKNOWN ROW: NO NUMBERS, NO MISSING KEYS.
# ========================================================================================= #


def test_an_unknown_row_is_the_same_document_with_its_numbers_stated_absent():
    """CD-RT-001 at the exit: an UNKNOWN dial has no statistics, and the document says so.

    ``statistics`` is three nulls — not zeros, which would read as a measured calm — and the
    coverage block is null THROUGHOUT with its one disclosure flag true, because there is no
    dial value to bracket.
    """
    document = contract_for_row(
        _unknown_row(), state_since=STATE_SINCE, **IDENTITY_ARGUMENTS
    )

    assert document == {
        "schema_version": "decision-rule/v1",
        "dial": "equity_crash",
        "as_of": "2026-10-14T12:00:00Z",
        "state": "UNKNOWN",
        "state_since": "2026-10-13T06:30:00Z",
        "persistence_counter": 0,
        "sizing_multiplier": None,
        "sizing_not_computed": True,
        "acute_rising": None,
        "statistics": {"breadth": None, "acute": None, "count": None},
        "coverage_bracket": {
            "scored_weight_fraction": None,
            "dial_value_min": None,
            "dial_value_max": None,
            "coverage_not_computed": True,
        },
        "inputs": None,
        "inputs_not_computed": True,
        "identity": {
            "build_sha": BUILD_SHA,
            "scaling_version": SCALING_VERSION,
            "mapping_version": MAPPING_VERSION,
            "decision_rule_version": "v1",
        },
    }


def test_an_unknown_row_brackets_nothing_even_when_a_real_fraction_is_supplied():
    """``bracketed`` requires RESOLVABLE, not merely a fraction.

    A caller that holds this reading's contributions can compute a perfectly good coverage
    fraction for a dial that came out UNKNOWN. The fraction is then published, because it is
    a true fact about the reading, and the bracket is still null: there is no dial value for
    the imputation to move.
    """
    document = contract_for_row(
        _unknown_row(),
        state_since=STATE_SINCE,
        scored_weight_fraction=0.8,
        **IDENTITY_ARGUMENTS,
    )

    assert document["coverage_bracket"] == {
        "scored_weight_fraction": 0.8,
        "dial_value_min": None,
        "dial_value_max": None,
        "coverage_not_computed": True,
    }


def test_the_document_has_one_shape_in_every_state():
    """A consumer never probes for a key: the states differ in VALUES, never in shape."""
    resolvable = contract_for_row(
        _resolvable_row(),
        state_since=STATE_SINCE,
        scored_weight_fraction=0.75,
        **IDENTITY_ARGUMENTS,
    )
    unknown = contract_for_row(
        _unknown_row(), state_since=STATE_SINCE, **IDENTITY_ARGUMENTS
    )

    assert _shape(resolvable) == _shape(unknown)
    # Spelled out as well as compared, so that a key dropped from BOTH branches by one edit
    # is a failure here rather than a silently narrower document.
    assert sorted(resolvable) == [
        "acute_rising", "as_of", "coverage_bracket", "dial", "identity", "inputs",
        "inputs_not_computed", "persistence_counter", "schema_version", "sizing_multiplier",
        "sizing_not_computed", "state", "state_since", "statistics",
    ]


# ========================================================================================= #
# 3 — THE BRACKET IS THE RE-SCORE. PROVEN THE LONG WAY.
# ========================================================================================= #

#: ONE DECLARED WEIGHT SET: ``(input id, calm, stress, weight)``. Three inputs are scored by
#: the reading below and two are not, so ``f`` is a real fraction; the weights are NON-UNIFORM
#: (3, 2, 1 scored against 3, 2 missing) so that a derivation which averaged scores without
#: their weights, or which imputed the missing weight at a uniform share, gives a different
#: answer here and fails; and one scored value is beyond its stress band so that the clamp is
#: exercised inside the mean the bracket is taken around.
WEIGHT_SET = (
    ("alpha", 0.0, 10.0, 3.0),
    ("bravo", 100.0, 50.0, 2.0),   # inverted band: the polarity-aware case
    ("charlie", 2.0, 3.0, 1.0),
    ("delta", 0.0, 1.0, 3.0),      # MISSING from the reading
    ("echo", -1.0, 1.0, 2.0),      # MISSING from the reading
)

#: What the reading actually had a value for. ``alpha`` scores 0.7, ``bravo`` 0.5 down its
#: inverted band, ``charlie`` clamps to 1.0.
SCORED_VALUES = {"alpha": 7.0, "bravo": 75.0, "charlie": 5.0}

MISSING_IDS = ("delta", "echo")


def _weight_set_spec() -> ModelSpec:
    """:data:`WEIGHT_SET` as a real ``ModelSpec`` the real executor will accept."""
    parameters = []
    for source_id, calm, stress, weight in WEIGHT_SET:
        parameters.append(DeclaredParameter(name=f"calm::{source_id}", value=calm))
        parameters.append(DeclaredParameter(name=f"stress::{source_id}", value=stress))
        parameters.append(DeclaredParameter(name=f"weight::{source_id}", value=weight))
    return ModelSpec(
        model_id="test.banded-weighted-mean.bracket.v0",
        dial_id=EQUITY_DIAL_ID,
        required_input_ids=("alpha",),
        contributing_input_ids=tuple(
            source_id for source_id, *_ in WEIGHT_SET if source_id != "alpha"
        ),
        mapping=MappingKind.BANDED_WEIGHTED_MEAN,
        parameters=tuple(parameters),
        provenance=TEST_PROVENANCE,
    )


def _band(source_id: str) -> tuple:
    calm, stress = next((c, s) for i, c, s, _ in WEIGHT_SET if i == source_id)
    return calm, stress


def _re_score(values: dict) -> float:
    """The REAL banded weighted mean over ``values`` — the product's own executor, no copy."""
    return compute(
        _weight_set_spec(), {source_id: {"value": v} for source_id, v in values.items()}
    ).magnitude


def test_the_bracket_equals_a_real_re_score_with_every_missing_input_imputed():
    """``dial_value_min``/``dial_value_max`` ARE the re-score, done the long way and compared.

    Three runs of :func:`crash_detector.engine.mapping.compute` over one weight set:

    1. the inputs the reading scored — this is ``breadth``, the number the row carries;
    2. the same, PLUS every missing input at its band's ``calm`` value, which scores exactly
       0 — "if every missing input scored 0", §7's ``dial_value_min``, computed by actually
       putting the inputs in and re-running the mean rather than by algebra;
    3. the same, plus every missing input at its ``stress`` value, which scores exactly 1 —
       §7's ``dial_value_max``.

    What the contract published in closed form must equal runs 2 and 3. The last two
    assertions are what make this a test rather than a restatement: the two derivations one
    would most plausibly write instead — publishing the breadth itself as the minimum (it is
    the mean of what WAS scored, so it "looks" like a floor) and adding the whole missing
    share to the un-rescaled breadth — are shown to give materially different numbers, so
    this test fails if the derivation is wrong in either of those directions.
    """
    breadth = _re_score(SCORED_VALUES)
    scored_weight = sum(w for i, _, _, w in WEIGHT_SET if i in SCORED_VALUES)
    nominal_weight = sum(w for *_, w in WEIGHT_SET)
    fraction = scored_weight / nominal_weight

    # The fixture is non-vacuous: real missing weight, and not a uniform weight set.
    assert 0.0 < fraction < 1.0
    assert len({w for *_, w in WEIGHT_SET}) > 1

    imputed_at_zero = dict(SCORED_VALUES)
    imputed_at_one = dict(SCORED_VALUES)
    for source_id in MISSING_IDS:
        calm, stress = _band(source_id)
        imputed_at_zero[source_id] = calm    # (calm - calm) / span == 0
        imputed_at_one[source_id] = stress   # (stress - calm) / span == 1
    long_form_min = _re_score(imputed_at_zero)
    long_form_max = _re_score(imputed_at_one)

    # Every missing input really was imputed, in both directions.
    assert set(imputed_at_zero) == set(imputed_at_one) == {i for i, *_ in WEIGHT_SET}

    document = contract_for_row(
        _resolvable_row(breadth=breadth),
        state_since=STATE_SINCE,
        scored_weight_fraction=fraction,
        **IDENTITY_ARGUMENTS,
    )
    bracket = document["coverage_bracket"]

    assert bracket["dial_value_min"] == pytest.approx(long_form_min)
    assert bracket["dial_value_max"] == pytest.approx(long_form_max)
    # ... and the closed form the module derives is that same pair of numbers.
    assert long_form_min == pytest.approx(breadth * fraction)
    assert long_form_max == pytest.approx(breadth * fraction + (1.0 - fraction))
    # The bracket contains the reading it brackets, which the algebra guarantees and which a
    # consumer would be entitled to assume even if it did not.
    assert bracket["dial_value_min"] <= breadth <= bracket["dial_value_max"]

    # THE DISCRIMINATION. Neither plausible-but-wrong derivation survives this weight set.
    assert long_form_min != pytest.approx(breadth)
    assert long_form_max != pytest.approx(breadth + (1.0 - fraction))


def test_the_bracket_collapses_onto_the_reading_when_nothing_is_missing():
    """``f == 1`` is the degenerate case and it had better be degenerate.

    With every nominal input scored there is nothing to impute, so both arms are the breadth
    itself: ``breadth · 1`` and ``breadth · 1 + 0``. The long-form re-score is the same run
    as the breadth's own, which is exactly the claim.
    """
    values = {source_id: calm for source_id, calm, _, _ in WEIGHT_SET}
    values["alpha"] = 7.0
    breadth = _re_score(values)

    document = contract_for_row(
        _resolvable_row(breadth=breadth),
        state_since=STATE_SINCE,
        scored_weight_fraction=1.0,
        **IDENTITY_ARGUMENTS,
    )

    assert document["coverage_bracket"]["dial_value_min"] == pytest.approx(breadth)
    assert document["coverage_bracket"]["dial_value_max"] == pytest.approx(breadth)


# ========================================================================================= #
# 4 — THE COVERAGE FRACTION'S REFUSALS (``_fraction``, through its only caller).
# ========================================================================================= #


@pytest.mark.parametrize(
    "fraction", [1.5, -0.1, 2.0, float("nan"), float("inf"), float("-inf")]
)
def test_a_coverage_fraction_outside_zero_to_one_is_refused(fraction):
    """Not a conservative or an optimistic coverage — a defect in whatever computed it.

    Published, it would put a ``dial_value_max`` below ``dial_value_min`` into the one
    document Epic 2 trusts, which is worse than no bracket at all.
    """
    with pytest.raises(ValueError, match="finite fraction in 0..1"):
        contract_for_row(
            _resolvable_row(),
            state_since=STATE_SINCE,
            scored_weight_fraction=fraction,
            **IDENTITY_ARGUMENTS,
        )


def test_a_zero_coverage_fraction_on_a_row_that_carries_a_breadth_is_refused():
    """A breadth is the weighted mean of the inputs that WERE scored.

    So "no weight was scored" cannot be true of a row that has one: the two statements are
    about the same reading and they disagree. Refused rather than bracketed to ``[0, 1]``,
    which would look like a measured and maximally uncertain reading.
    """
    with pytest.raises(ValueError, match="weighted mean of the inputs that WERE scored"):
        contract_for_row(
            _resolvable_row(),
            state_since=STATE_SINCE,
            scored_weight_fraction=0.0,
            **IDENTITY_ARGUMENTS,
        )


def test_a_zero_coverage_fraction_is_admitted_on_an_unknown_row():
    """The same 0.0 is a TRUE statement about a dial that resolved to nothing, and is kept.

    This is the other half of the refusal above: it is tied to the row carrying a breadth and
    is not a blanket rule that zero coverage cannot be reported.
    """
    document = contract_for_row(
        _unknown_row(),
        state_since=STATE_SINCE,
        scored_weight_fraction=0.0,
        **IDENTITY_ARGUMENTS,
    )

    assert document["coverage_bracket"]["scored_weight_fraction"] == 0.0
    assert document["coverage_bracket"]["coverage_not_computed"] is True


# ========================================================================================= #
# 5 — WHAT MAY BE PUBLISHED AT ALL: THE ROW'S TYPE, AND THE DIAL ENUM.
# ========================================================================================= #


class _LooksLikeARow(MachineStateRow):
    """A SUBCLASS, which is the whole reason the admission is exact-type (CD-AC-005)."""


def test_only_an_exact_machine_state_row_is_published():
    """A subclass may shadow any field with a property, and a property is a caller's code.

    Running where the engine's conclusion is read — so the subclass is refused by type
    identity, as is anything else offered in the row's place.
    """
    forged = _LooksLikeARow(
        dial_id=EQUITY_DIAL_ID,
        as_of=AS_OF,
        machine_state=State.CALM,
        persistence_counter=0,
    )

    with pytest.raises(TypeError, match="publishes a MachineStateRow, got _LooksLikeARow"):
        contract_for_row(forged, state_since=STATE_SINCE, **IDENTITY_ARGUMENTS)

    with pytest.raises(TypeError, match="publishes a MachineStateRow, got dict"):
        contract_for_row(
            {"dial_id": EQUITY_DIAL_ID}, state_since=STATE_SINCE, **IDENTITY_ARGUMENTS
        )


def test_a_dial_this_product_does_not_declare_is_refused():
    """§7's enum is the two dials that exist; a third is a PID amendment, not a row."""
    with pytest.raises(ValueError, match="is not a dial this product declares"):
        contract_for_row(
            _resolvable_row(dial_id="monetary_debasement_gbp"),
            state_since=STATE_SINCE,
            **IDENTITY_ARGUMENTS,
        )


# ========================================================================================= #
# 6 — ``content_version``: THE SHA256 OF A FILE'S BYTES.
# ========================================================================================= #


def test_content_version_is_the_sha256_of_the_files_bytes_and_not_of_its_text(tmp_path):
    """BYTES, as the migrations' ``checksum_sha256`` and the tree fingerprint both do it.

    The fixture's bytes carry a UTF-8 BOM and a CRLF, so ``read_text()`` — which decodes the
    BOM and translates the line ending — re-encodes to something else entirely. A digest over
    decoded text would make the published version depend on this process's decoding, and the
    artefact being identified is a file somebody shipped.
    """
    path = tmp_path / "indicator-scaling.json"
    raw = b'\xef\xbb\xbf{"schema_version": "v1"}\r\n'
    path.write_bytes(raw)

    digest = content_version(path)

    assert digest == hashlib.sha256(raw).hexdigest()
    assert len(digest) == 64 and digest == digest.lower()
    assert digest != hashlib.sha256(path.read_text().encode("utf-8")).hexdigest()


def test_content_version_changes_when_the_files_bytes_change(tmp_path):
    """The identity is the content: one byte different is a different version.

    And a file whose DECLARED version is edited without its bytes changing is impossible,
    which is the reason this is not ``provenance.mapping_version``.
    """
    path = tmp_path / "ratified.yaml"
    path.write_bytes(b"indicators: []\n")
    before = content_version(path)

    path.write_bytes(b"indicators: []\n\n")

    assert content_version(path) != before


def test_content_version_of_the_two_shipped_config_files():
    """Run against the REAL files, so the function is proven on what it is actually asked for."""
    for path in (SCALING_JSON, MAPPING_YAML):
        assert content_version(path) == hashlib.sha256(path.read_bytes()).hexdigest()


# ========================================================================================= #
# 7 — ``live_identity``: WHAT A RUNNING BUILD HAS TO GO OUTSIDE ITSELF TO LEARN.
# ========================================================================================= #


def test_live_identity_reads_the_build_sha_from_the_environment(monkeypatch):
    """``CD_BUILD_SHA``, the same env var ``gui/server.py`` publishes from — reused, not re-decided."""
    monkeypatch.setenv(BUILD_SHA_ENV, "cafebabe")

    identity = live_identity()

    assert identity["build_sha"] == "cafebabe"
    assert identity["scaling_version"] == content_version(SCALING_JSON)
    assert identity["mapping_version"] == content_version(MAPPING_YAML)
    assert sorted(identity) == ["build_sha", "mapping_version", "scaling_version"]


def test_live_identity_falls_back_to_unknown_when_the_build_sha_is_unset(monkeypatch):
    """An image built without a sha says ``unknown`` — a stated absence, not an empty string."""
    monkeypatch.delenv(BUILD_SHA_ENV, raising=False)

    assert live_identity()["build_sha"] == BUILD_SHA_UNKNOWN == "unknown"


def test_an_explicit_build_sha_wins_over_the_environment(monkeypatch):
    """For a caller that already knows it: the argument is the answer, the env var is the default."""
    monkeypatch.setenv(BUILD_SHA_ENV, "from-the-environment")

    assert live_identity(build_sha="from-the-caller")["build_sha"] == "from-the-caller"


# ========================================================================================= #
# 8 — ``scored_coverage``: MATH.md R-10's OWN NUMBERS.
# ========================================================================================= #


@pytest.fixture()
def wiring():
    return build_wiring()


def _bound_weights(dial_id: str) -> dict:
    """Every ratified indicator bound to ``dial_id`` -> the tier weight the wiring gives it."""
    return {
        row["id"]: TIER_WEIGHT[row["tier"]]
        for row in _rows()
        if dial_id in _polarities(row)
    }


def _contributions(dial_id: str, scored_ids) -> tuple:
    """``scored_ids`` as the engine's own ``Contribution`` values, carrying the real weights.

    The weight is read from the ratified mapping's tier, which is where the model spec's
    ``weight::<id>`` parameter comes from, so these carry the weight production would.
    """
    weights = _bound_weights(dial_id)
    return tuple(
        Contribution(
            source_id=source_id,
            category="banded_indicator",
            weight=weights[source_id],
            contribution=0.5,
        )
        for source_id in scored_ids
    )


def test_scored_coverage_is_math_mds_worked_monetary_figure(wiring):
    """MATH.md §2.4 item 8, verbatim: the monetary dial reads 14/21 = 0.667 by scored weight.

    The dial's two gold legs are FEED_FAILING (R-9) and ``copper_gold`` is HELD, so the eight
    indicators below are what the reading actually scored. ``coverage`` reports 0.905 for the
    same dial and the same reading, because it counts WIRED rows; the difference between the
    two numbers IS R-10, and both are asserted here so the gap cannot close by accident.
    """
    scored = ("broad_dollar", "breakeven_5y", "cpi_yoy", "core_pce_yoy", "real_rate_10y_tips",
              "fed_funds_rate", "m2_yoy", "monetisation_flag")

    answer = scored_coverage(
        wiring, MONETARY_DIAL_ID, _contributions(MONETARY_DIAL_ID, scored)
    )

    assert answer["scored_weight"] == 14.0
    assert answer["nominal_weight"] == 21.0
    assert answer["fraction"] == pytest.approx(14.0 / 21.0)
    assert round(answer["fraction"], 3) == 0.667
    assert answer["not_scored"] == ["copper_gold", "gold_real_rate_cross", "gold_spot"]
    # The figure R-10 names as wrong for this purpose, and it is still disclosed where it is
    # right: these are two different questions about the same dial.
    assert coverage(wiring)[MONETARY_DIAL_ID]["fraction"] == pytest.approx(0.9047619047619048)


def test_scored_coverage_is_math_mds_worked_equity_figure(wiring):
    """MATH.md §1.4 item 10: ``coverage.fraction`` is 1.0 for the equity dial while
    ``sloos_bank_lending`` is MISSING. By scored weight the dial is a mean over 46 of 48."""
    scored = tuple(
        source_id for source_id in _bound_weights(EQUITY_DIAL_ID)
        if source_id != "sloos_bank_lending"
    )

    answer = scored_coverage(wiring, EQUITY_DIAL_ID, _contributions(EQUITY_DIAL_ID, scored))

    assert answer["scored_weight"] == 46.0
    assert answer["nominal_weight"] == 48.0
    assert answer["fraction"] == pytest.approx(46.0 / 48.0)
    assert answer["not_scored"] == ["sloos_bank_lending"]
    assert coverage(wiring)[EQUITY_DIAL_ID]["fraction"] == 1.0


def test_scored_coverage_refuses_another_dials_contribution(wiring):
    """A weight scored on the equity dial is not coverage of the monetary one (CD-AC-002).

    ``hy_oas`` is bound to the equity dial only. A caller holding both dials' contributions
    could otherwise pair the wrong tuple with the wrong dial and get a plausible number.
    """
    assert MONETARY_DIAL_ID not in _polarities(
        next(row for row in _rows() if row["id"] == "hy_oas")
    )
    contributions = _contributions(EQUITY_DIAL_ID, ("hy_oas",))

    with pytest.raises(ValueError, match="is not bound to 'monetary_debasement'"):
        scored_coverage(wiring, MONETARY_DIAL_ID, contributions)


def test_scored_coverage_refuses_a_repeated_indicator(wiring):
    """The second entry would silently double-count its weight, and could push the fraction
    above 1.0 — which ``_fraction`` would then refuse one storey later, naming the wrong
    thing. Refused here, where the duplicate is."""
    doubled = _contributions(MONETARY_DIAL_ID, ("broad_dollar",)) * 2

    with pytest.raises(ValueError, match="appears twice in one dial's contributions"):
        scored_coverage(wiring, MONETARY_DIAL_ID, doubled)


def test_scored_coverage_feeds_the_contract_the_fraction_it_asks_for(wiring):
    """The two functions meet: R-10's fraction is what §7's bracket is computed over.

    Asserted end to end rather than left to prose, because the contract's docstring names
    ``scored_coverage`` as the source and the GUI's ``coverage`` figure as the wrong one.
    """
    scored = ("broad_dollar", "breakeven_5y", "cpi_yoy", "core_pce_yoy", "real_rate_10y_tips",
              "fed_funds_rate", "m2_yoy", "monetisation_flag")
    fraction = scored_coverage(
        wiring, MONETARY_DIAL_ID, _contributions(MONETARY_DIAL_ID, scored)
    )["fraction"]

    document = contract_for_row(
        _resolvable_row(dial_id=MONETARY_DIAL_ID, breadth=0.14),
        state_since=STATE_SINCE,
        scored_weight_fraction=fraction,
        **IDENTITY_ARGUMENTS,
    )

    assert document["dial"] == "monetary_debasement"
    assert document["coverage_bracket"]["scored_weight_fraction"] == pytest.approx(14 / 21)
    assert document["coverage_bracket"]["dial_value_min"] == pytest.approx(0.14 * 14 / 21)
    assert document["coverage_bracket"]["dial_value_max"] == pytest.approx(
        0.14 * 14 / 21 + 7 / 21
    )
