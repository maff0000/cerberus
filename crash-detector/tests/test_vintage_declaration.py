"""CARRIER for ``ingestion.vintage``: the frozen sets must still be what the evidence says.

``ingestion.vintage`` declares three frozen sets — REVISION_PRONE, REVISION_STABLE,
REVISION_UNDETERMINED — and claims they are the output of :func:`~ingestion.vintage.classify`
on ``evidence/wo114_alfred_probe.json``. A frozen set is a typed table, and a typed table
drifts from its evidence silently: someone adds a series to the catalog, re-runs the probe,
and forgets one line. This file is the thing that goes red when that happens.

It reads the REAL evidence file — not a fixture, not a sample — and re-derives. No network:
the probe is a probe and can never be a register check (CD-PL-F48), so what is pinned here
is the agreement between a RECORDED measurement and the declaration drawn from it.

The constants are checked against the probe's own header too. ``MATERIAL_THRESHOLD`` and
``EVIDENCE_PROBED_UTC`` are prose in the module docstring until something compares them with
the ``material_threshold`` and ``probed_utc`` the probe actually wrote; a declaration that
describes a 0.005 measurement while sitting on a 0.05 file is worse than one that says
nothing.
"""

from __future__ import annotations

import json
import pathlib
from datetime import datetime

import pytest

from ingestion import backfill as B
from ingestion.backfill import backfill_range
from ingestion.catalog import INGREDIENTS
from ingestion.vintage import (
    EVIDENCE_FILE,
    EVIDENCE_PROBED_UTC,
    MATERIAL_THRESHOLD,
    MIN_SHARED_OBSERVATIONS,
    NO_REVISION_MECHANISM_COLUMNS,
    NO_REVISION_MECHANISM_EVIDENCE,
    NO_REVISION_MECHANISM_KINDS,
    REVISION_PRONE,
    REVISION_STABLE,
    REVISION_UNDETERMINED,
    STABILITY_MEASURED_FROM,
    VINTAGE_CURRENT_ONLY,
    VINTAGE_LABELS,
    VINTAGE_NO_REVISION_MECHANISM,
    VINTAGE_ORIGINAL,
    classify,
    has_no_revision_mechanism,
    requires_original_vintage,
)

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
#: Resolved from :data:`ingestion.vintage.EVIDENCE_FILE`, never retyped: if the declaration
#: ever names a file that is not there, this file fails rather than quietly reading another.
_EVIDENCE_PATH = _REPO_ROOT / EVIDENCE_FILE


@pytest.fixture()
def probe() -> dict:
    assert _EVIDENCE_PATH.is_file(), f"the declared evidence file is missing: {EVIDENCE_FILE}"
    return json.loads(_EVIDENCE_PATH.read_text())


@pytest.fixture()
def derived(probe) -> dict:
    return classify(probe)


def test_the_declared_revision_prone_set_is_what_the_evidence_derives(derived):
    assert derived["prone"] == REVISION_PRONE


def test_the_declared_revision_stable_set_is_what_the_evidence_derives(derived):
    assert derived["stable"] == REVISION_STABLE


def test_the_declared_undetermined_set_is_what_the_evidence_derives(derived):
    assert derived["undetermined"] == REVISION_UNDETERMINED


def test_the_three_sets_partition_the_probe_exactly_once_each(probe, derived):
    """Every probed pair lands in exactly one set, and no declared pair was never probed."""
    probed = {(entry["series"], entry["transformation"]) for entry in probe["series"]}
    assert len(probed) == len(probe["series"]), "the probe records a pair twice"
    declared = [REVISION_PRONE, REVISION_STABLE, REVISION_UNDETERMINED]
    assert REVISION_PRONE | REVISION_STABLE | REVISION_UNDETERMINED == probed
    assert sum(len(one) for one in declared) == len(probed), "a pair is in two sets"
    assert len(derived["prone"]) + len(derived["stable"]) + len(derived["undetermined"]) == len(probed)


def test_the_probe_measured_with_the_threshold_the_declaration_describes(probe):
    assert probe["material_threshold"] == MATERIAL_THRESHOLD
    assert probe["probed_utc"] == EVIDENCE_PROBED_UTC


def test_the_stability_claim_begins_where_the_probe_actually_measured_from(probe):
    """``STABILITY_MEASURED_FROM`` is the probe's own left edge, not a date someone liked.

    It is the one constant a backfill consults to decide whether REVISION_STABLE says
    anything about an observation at all, so it has to BE the window the measurement was
    taken over. Two halves, because the header and the per-series figures could drift apart:
    the declared date is the probe's ``compare_from``, and ``compare_from`` is in fact the
    left edge every ``replay_window`` figure :func:`classify` reads was computed against.
    Move the probe's window back and leave the constant at 1999 and this goes red — which is
    the failure that would otherwise let a pre-1999 DFF reading be stored as current-only.
    """
    assert STABILITY_MEASURED_FROM == probe["compare_from"]
    edges = {entry["revision"]["replay_window"]["from"] for entry in probe["series"]}
    assert edges == {STABILITY_MEASURED_FROM}, f"replay windows disagree on their left edge: {sorted(edges)}"


def test_dff_is_why_the_window_is_load_bearing_and_the_evidence_still_says_so(probe):
    """The concrete case the constant exists for: DFF is stable ONLY inside the window.

    The declaration argues from DFF — clean across the replay window, materially revised 93
    times over its full history, every one of those before the window opens. That argument
    is a reading of this file, so it is pinned here. The pre-1999 part is derived, not
    assumed: the replay window differs in ZERO observations at all (not merely zero
    MATERIALLY), so every differing observation in the full overlap lies outside it.
    """
    dff = [
        entry for entry in probe["series"]
        if (entry["series"], entry["transformation"]) == ("DFF", None)
    ]
    assert len(dff) == 1, "the probe no longer measures DFF exactly once"
    revision = dff[0]["revision"]
    window = revision["replay_window"]

    assert ("DFF", None) in REVISION_STABLE
    # Inside the window: not one print moved, over a window far above the floor.
    assert (window["differing"], window["differing_materially"]) == (0, 0)
    assert window["shared_observations"] == 2369 >= MIN_SHARED_OBSERVATIONS
    # Outside it: the 93 the prose cites, in an overlap that starts decades before 1999.
    assert revision["differing_materially"] == 93
    assert revision["shared_observations"] == 18624
    assert revision["shared_span"][0] < STABILITY_MEASURED_FROM <= window["shared_span"][0]


def test_every_fred_pair_the_catalog_collects_was_probed(probe):
    """The declaration covers the catalog as it stands; a new FRED row needs a new probe."""
    probed = {(entry["series"], entry["transformation"]) for entry in probe["series"]}
    catalog = {
        (ingredient.ref, ingredient.transformation)
        for ingredient in INGREDIENTS
        if ingredient.kind == "fred"
    }
    assert catalog, "no FRED ingredient was recognised — this guard has stopped measuring"
    assert catalog <= probed, f"collected but never probed: {sorted(catalog - probed)}"


def test_requires_original_vintage_answers_from_the_measured_stable_set():
    """Fail-safe: only POSITIVELY measured stability may skip point-in-time fetching."""
    for series, transformation in REVISION_PRONE | REVISION_UNDETERMINED:
        assert requires_original_vintage(series, transformation) is True
    for series, transformation in REVISION_STABLE:
        assert requires_original_vintage(series, transformation) is False
    # A series nobody has probed is fetched vintage-by-vintage, not silently trusted.
    assert requires_original_vintage("NEVER_PROBED_SERIES") is True
    # The transformation is part of the identity: the raw index is not the YoY figure.
    assert requires_original_vintage("DFF", "pc1") is True


def test_a_stable_verdict_is_never_returned_on_a_window_below_the_floor():
    """The floor is the whole difference between STABLE and UNDETERMINED — hold it down."""
    thin = {"series": [{
        "series": "THIN", "transformation": None,
        "revision": {
            "differing_materially": 0, "shared_observations": MIN_SHARED_OBSERVATIONS - 1,
            "replay_window": {"differing_materially": 0, "shared_observations": 1},
        },
    }]}
    assert classify(thin) == {
        "prone": frozenset(), "stable": frozenset(),
        "undetermined": frozenset({("THIN", None)}),
    }


def test_the_vintage_vocabulary_is_closed_and_the_three_labels_are_distinct():
    """WO-1.16 widened this from two to three, which is the only way it may ever change.

    The assertion is on the EXACT tuple rather than on membership, so a label added anywhere
    in the tree lands here first: the vocabulary is the ``raw_reading.vintage`` CHECK
    (``ingestion.store``) and widening it is a schema change, not an import.
    """
    assert VINTAGE_LABELS == (VINTAGE_ORIGINAL, VINTAGE_CURRENT_ONLY,
                              VINTAGE_NO_REVISION_MECHANISM)
    assert len(set(VINTAGE_LABELS)) == 3


# ---------------------------------------------------------------------------------------
# WO-1.16: the gate on VINTAGE_NO_REVISION_MECHANISM is a (kind, column) question
#
# ``kind == "yahoo"`` is NINE catalog rows reading TWO quantities out of one endpoint: the
# printed ``close``, which nothing restates, and ``adjclose``, which is restated for every
# past date by every future dividend and split. The label is true of the first and FALSE of
# the second, so the tests below are not one happy path and one edge case — they are the two
# halves of the only reason this gate takes a column at all.
# ---------------------------------------------------------------------------------------

#: The two indicators whose Yahoo rows are wired ``column="adjclose"`` deliberately (PID.md,
#: WO-1.16 scope correction). Named by INDICATOR and not by source id so the guard below
#: covers the ``constituent_breadth_200dma`` sample as it is, however many names it holds.
_ADJCLOSE_INDICATORS = ("private_credit_stress", "constituent_breadth_200dma")


def _yahoo_rows(*, column_in):
    return [i for i in INGREDIENTS if i.kind == "yahoo" and i.column in column_in]


def _adjclose_rows():
    return [i for i in INGREDIENTS
            if any(ind in i.serves for ind in _ADJCLOSE_INDICATORS)]


def test_the_two_tiers_are_disjoint_and_each_names_evidence_that_is_on_disk():
    """A kind declares its no-revision claim at ONE granularity, and names where it came from.

    A kind in both tiers would be a contradiction with a silent winner: the whole-body tier
    is answered first, so it would override its own column list. And either tier without an
    entry in :data:`~ingestion.vintage.NO_REVISION_MECHANISM_EVIDENCE` is the thing this
    module's first docstring line refuses — a declaration held as a belief.
    """
    assert not (NO_REVISION_MECHANISM_KINDS & set(NO_REVISION_MECHANISM_COLUMNS)), (
        "a kind cannot claim both whole-body and per-column scope"
    )
    declared = NO_REVISION_MECHANISM_KINDS | set(NO_REVISION_MECHANISM_COLUMNS)
    assert declared == set(NO_REVISION_MECHANISM_EVIDENCE), (
        f"declared without evidence, or evidence without a declaration: "
        f"{sorted(declared ^ set(NO_REVISION_MECHANISM_EVIDENCE))}"
    )
    for kind, named in NO_REVISION_MECHANISM_EVIDENCE.items():
        assert (_REPO_ROOT / named).is_file(), f"{kind} names a probe that is not there: {named}"


def test_cboe_is_the_whole_body_tier_and_answers_true_whatever_column_is_passed():
    """The Cboe claim is about the BYTES OF ONE FILE, so it holds for every column in it.

    Asserted on columns Cboe does not even have, because the point is not that the gate
    tolerates junk — it is that this tier deliberately does not consult the argument, and a
    future refactor that started filtering Cboe by column would be narrowing a claim the
    probe made at file scope. ``"adjclose"`` is in the list as the sharpest version of that:
    it is a Yahoo field, it means nothing to Cboe, and it must not drag Cboe's answer down
    with it.
    """
    assert NO_REVISION_MECHANISM_KINDS == frozenset({"cboe"})
    cboe = [i for i in INGREDIENTS if i.kind == "cboe"]
    assert len(cboe) == 3, "the Cboe rows this was reasoned about have changed"
    for ing in cboe:
        assert has_no_revision_mechanism(ing.kind, ing.column) is True
    for column in ("CLOSE", "SKEW", "close", "adjclose", "", "not-a-column"):
        assert has_no_revision_mechanism("cboe", column) is True


def test_every_plain_close_yahoo_row_the_catalog_collects_answers_true():
    """The eight rows WO-1.16 made backfillable, derived from the catalog and not retyped.

    SEVEN UNTIL WO-1.20, when ``yahoo.GC=F.history`` — ``gold_real_rate_cross``'s new gold leg,
    replacing the retired LBMA fix — joined this population. It is here because it declares
    ``column == ""`` like the other seven, i.e. it reads the PRINTED close, which is the one
    property this gate turns on; its history depth is irrelevant to the question. The roster
    stays spelled out because it is the INDEPENDENT half of the assertion: deriving it from the
    same predicate the gate uses would make this test agree with itself.
    """
    plain = _yahoo_rows(column_in=("", "close"))
    assert {i.source_id for i in plain} == {
        "yahoo.HYG", "yahoo.LQD", "yahoo.RSP", "yahoo.SPY",
        "yahoo.^GSPC", "yahoo.HG=F", "yahoo.GC=F", "yahoo.GC=F.history",
    }
    for ing in plain:
        assert has_no_revision_mechanism(ing.kind, ing.column) is True, ing.source_id
    # Both spellings of the one field, because the catalog uses "" and build_adapter
    # resolves it with ``ing.column or "close"``. Admitting only one would refuse all eight.
    assert has_no_revision_mechanism("yahoo", "") is True
    assert has_no_revision_mechanism("yahoo", "close") is True


def test_no_adjclose_ingredient_can_be_labelled_no_revision_mechanism():
    """THE LOAD-BEARING GUARD. ``private_credit_stress`` and ``constituent_breadth_200dma``
    must have NO path to :data:`~ingestion.vintage.VINTAGE_NO_REVISION_MECHANISM`.

    Their value for a past date is today's retroactive restatement of it, so that label on
    such a row would be a plain false statement with nothing able to detect it — the exact
    failure the label's own comment forbids, by field instead of by date.

    FOUR DOORS, CLOSED SEPARATELY, because it is not enough that the current answer is
    ``False``:

    1. the live rows answer ``False`` through the real gate, derived from the catalog;
    2. ``yahoo`` is not in the WHOLE-BODY tier — which is answered FIRST and would make the
       column list dead code, so this is the door that a one-word edit opens;
    3. ``adjclose`` is in no kind's column list, now or for any kind added later;
    4. and the label dispatch in ``ingestion.backfill`` refuses the range rather than
       falling through to a label. That is the second independent defence, the first being
       ``YahooChartAdapter`` refusing a dated ``adjclose`` fetch at construction.

    DOOR 4 USED TO BE A HYPOTHETICAL AND IS NOW THE REAL PATH. It was asserted by
    monkeypatching ``yahoo`` INTO ``VINTAGE_BACKFILLABLE_KINDS``, because the kind-level
    refusal was what blocked Yahoo entirely and the only way to learn whether the label
    dispatch worked was to force that door open. The wiring round put ``yahoo`` in that tuple
    for real — for its plain closes — so these rows now reach the label dispatch on the
    ORDINARY path, and the monkeypatch is gone rather than left in place simulating a state
    that has arrived. The assertion is unchanged and it is strictly stronger for it.
    """
    rows = _adjclose_rows()
    assert rows, "the two adjclose indicators are no longer in the catalog — this guard is dead"
    assert {i.column for i in rows} == {"adjclose"}, (
        "an adjclose indicator is now wired to another column; re-reason this guard"
    )
    assert {i.kind for i in rows} == {"yahoo"}

    # 1. the real rows, through the real gate.
    for ing in rows:
        assert has_no_revision_mechanism(ing.kind, ing.column) is False, ing.source_id

    # 2. the whole-body tier would override the column list; yahoo must never be in it.
    assert "yahoo" not in NO_REVISION_MECHANISM_KINDS

    # 3. no kind, present or future, may admit adjclose by column.
    for kind, columns in NO_REVISION_MECHANISM_COLUMNS.items():
        assert "adjclose" not in columns, f"{kind} admits adjclose by column"

    # 4. the kind check now PASSES for these rows, and the label dispatch refuses anyway.
    assert "yahoo" in B.VINTAGE_BACKFILLABLE_KINDS, (
        "yahoo has left VINTAGE_BACKFILLABLE_KINDS; this door is being asserted against a "
        "kind-level refusal that already blocks it, which is not what door 4 is for"
    )
    ing = rows[0]
    with pytest.raises(ValueError) as caught:
        backfill_range(ing, ["2015-06-08"], None, lambda: datetime(2026, 10, 15))
    assert "no vintage label is derived" in str(caught.value), (
        f"a forced-open yahoo backfill got past the label dispatch: {caught.value}"
    )


def test_the_gate_refuses_an_unprobed_kind_and_a_kind_asked_without_a_column():
    """Fail-safe both ways: nothing undeclared answers True, and nothing answers on one arg.

    The missing-argument half is the defect this signature exists to prevent, in its most
    likely form — a caller who means "is yahoo unrevised?", writes the kind alone and gets
    the plain-close answer applied to an ``adjclose`` row. With no default for ``column``
    that is a ``TypeError`` where it is written, not a wrong row in the store.
    """
    for kind in ("multpl", "lbma", "hermes", "manual", "fred", "never-heard-of-it"):
        for column in ("", "close", "adjclose", "CLOSE"):
            assert has_no_revision_mechanism(kind, column) is False, (kind, column)
    with pytest.raises(TypeError):
        has_no_revision_mechanism("yahoo")
    with pytest.raises(TypeError):
        has_no_revision_mechanism("cboe")


def test_the_yahoo_probe_still_records_that_it_never_asked_for_adjclose():
    """The column split is argued FROM that probe's scope, so pin the prose to the file.

    ``NO_REVISION_MECHANISM_COLUMNS`` says the Yahoo measurement on record covers plain
    close and deliberately not ``adjclose``. If the probe is ever re-run wider, or its scope
    note rewritten, this goes red and the argument gets re-read — the same reason
    ``MATERIAL_THRESHOLD`` is checked against the probe's own header above.
    """
    named = _REPO_ROOT / NO_REVISION_MECHANISM_EVIDENCE["yahoo"]
    probe = json.loads(named.read_text())
    assert probe["probed_utc"] == "2026-10-15"
    assert "adjclose" in probe["scope_note"], "the probe no longer states its field scope"
    assert "never asks for adjclose" in probe["scope_note"]
