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

import pytest

from ingestion.catalog import INGREDIENTS
from ingestion.vintage import (
    EVIDENCE_FILE,
    EVIDENCE_PROBED_UTC,
    MATERIAL_THRESHOLD,
    MIN_SHARED_OBSERVATIONS,
    REVISION_PRONE,
    REVISION_STABLE,
    REVISION_UNDETERMINED,
    VINTAGE_CURRENT_ONLY,
    VINTAGE_LABELS,
    VINTAGE_ORIGINAL,
    classify,
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


def test_the_vintage_vocabulary_is_closed_and_the_two_labels_are_distinct():
    assert VINTAGE_LABELS == (VINTAGE_ORIGINAL, VINTAGE_CURRENT_ONLY)
    assert len(set(VINTAGE_LABELS)) == 2
