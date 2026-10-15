"""WO-1.14 ROUTING: which constructor a FRED ingredient gets, and which one it can never get.

Two claims, and the second is the load-bearing one.

ONE — the ROUTE IS THE EVIDENCE'S. A FRED ingredient whose (series, transformation) pair
``ingestion.vintage.requires_original_vintage`` answers YES for is backfilled through
``AlfredVintageAdapter`` (the figure as FIRST published); a pair measured stable is
backfilled from FRED's current body through the ordinary ``FredAdapter``. Nothing in
``ingestion.backfill_adapters`` decides that — the declaration does, and these tests sweep
every FRED ingredient in the catalog so the two cannot drift apart for 15 of 23 series while
looking right for the one a hand-written test happened to name.

TWO — the LIVE LOOP CANNOT REACH THE VINTAGE ADAPTER, STRUCTURALLY. ``AlfredVintageAdapter``
spends ``2 + ceil(log2(days))`` GETs per ``fetch`` under a total deadline and answers for one
named observation date. In ``ingestion.run``'s loop — a few seconds per attempt, "the latest
value", every ingredient every pass — it would be wrong twice over. So the tests below hold
the SHAPE that makes it unreachable rather than the habit of not reaching it:
``build_adapter`` has no argument that could select it, ``ingestion.catalog`` does not import
or expose it, ``ingestion.run`` does not import the module that does, and the dependency runs
one way only (backfill -> catalog), so the reverse is an import cycle rather than an edit.

THREE — THE HOST IS DECLARED WHERE IT IS TRUE. ``alfred.stlouisfed.org`` is reached by the
backfill path and by nothing else, so it is declared in ``BACKFILL_EGRESS_HOSTS`` and is
absent from ``EGRESS_HOSTS``, from ``deploy/egress-destinations.yaml`` and from
``cd-collectors``' compose allowlist — all three of which are claims about what the LIVE
collector service reaches. The tests assert the absence as well as the presence: a host that
leaked into the live declaration would be a false egress claim in the exact files that exist
because a false egress claim once went green (CD-ASR-F04).

NOTHING HERE FETCHES. No adapter is given a getter and ``fetch`` is never called: this module
is about which object is constructed and what URL it would address, which is the whole of
what this round changed.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
from datetime import datetime, timezone
from urllib.parse import urlsplit

import pytest

from compose_reader import load_compose
from ingestion import adapters as A
from ingestion import catalog as C
from ingestion import run as live_run
from ingestion.backfill_adapters import (BACKFILL_EGRESS_HOSTS, VINTAGE_BACKFILLABLE_KINDS,
                                         build_backfill_adapter)
from ingestion.catalog import EGRESS_HOSTS, INGREDIENTS, NON_HTTP_PEERS, build_adapter
from ingestion.vintage import requires_original_vintage

NOW = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
CLOCK = lambda: NOW  # noqa: E731
#: An observation date in the replay window, old enough that a vintage search over it is the
#: real case. Never fetched — only interpolated into a URL.
OBS = "2008-09-01"

ROOT = pathlib.Path(__file__).resolve().parents[1]
FRED = tuple(i for i in INGREDIENTS if i.kind == "fred")


def _ing(source_id: str):
    return next(i for i in INGREDIENTS if i.source_id == source_id)


def _imported_names(module_path: str) -> set:
    """Every module and name a file IMPORTS, read from its AST rather than from its text.

    AST and not ``in source``: a prose mention of ``AlfredVintageAdapter`` in a comment that
    explains why the module does not import it must not read as the import itself.
    """
    tree = ast.parse((ROOT / module_path).read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


# --- ONE: the route is the evidence's -------------------------------------------------- #


def test_a_revision_prone_fred_ingredient_backfills_through_the_vintage_adapter():
    """GDP is revised; the figure a 2008 collector saw is not the figure GDP carries now."""
    adapter = build_backfill_adapter(_ing("fred.GDP"), OBS, CLOCK)
    assert type(adapter) is A.AlfredVintageAdapter
    assert adapter.adapter_id == "cd.ingest.alfred_vintage_csv.v1"
    assert adapter.source_id == "fred.GDP"
    parts = urlsplit(adapter._url())
    assert parts.hostname == A.ALFRED_HOST and f"id=GDP" in parts.query and OBS in parts.query


def test_a_revision_prone_transformed_pair_carries_its_transformation_into_the_vintage_fetch():
    """The pair is (series, transformation): M2SL's pc1 is what was declared revision-prone."""
    adapter = build_backfill_adapter(_ing("fred.M2SL.pc1"), OBS, CLOCK)
    assert type(adapter) is A.AlfredVintageAdapter
    assert "transformation=pc1" in urlsplit(adapter._url()).query


def test_a_measured_stable_fred_ingredient_backfills_from_freds_current_body():
    """DFF differs in ZERO of 2,369 shared observations over the replay window (ingestion.vintage)."""
    adapter = build_backfill_adapter(_ing("fred.DFF"), OBS, CLOCK)
    assert type(adapter) is A.FredAdapter
    assert urlsplit(adapter._url()).hostname == "fred.stlouisfed.org"


def test_every_fred_ingredient_routes_exactly_as_the_vintage_declaration_says():
    """The sweep. Not one named series each way — all 23, against the declaration itself."""
    prone, stable = [], []
    for ing in FRED:
        adapter = build_backfill_adapter(ing, OBS, CLOCK)
        if requires_original_vintage(ing.ref, ing.transformation):
            assert type(adapter) is A.AlfredVintageAdapter, ing.source_id
            prone.append(ing.source_id)
        else:
            assert type(adapter) is A.FredAdapter, ing.source_id
            stable.append(ing.source_id)
    # 24 FRED ingredient rows over 23 distinct (series, transformation) pairs: DFII10 is
    # ingested twice, once plain and once with history for the gold_real_rate_cross
    # derivation. Both rows route the same way, because the route is a property of the PAIR
    # the evidence judged and not of the catalog row — which is why this is a sweep.
    assert len(FRED) == 24 and len({(i.ref, i.transformation) for i in FRED}) == 23
    # 15 measured revision-prone + 2 UNDETERMINED (fail-safe: fetched point-in-time) = 17
    # pairs, and 6 measured-stable pairs over 7 rows.
    assert (len(prone), len(stable)) == (17, 7)
    assert [s for s in stable if s.startswith("fred.DFII10")] == [
        "fred.DFII10", "fred.DFII10.history"]
    assert {"fred.BAMLC0A0CM", "fred.BAMLH0A0HYM2"} <= set(prone), (
        "an unprobed or undetermined pair must be fetched vintage-by-vintage, never trusted"
    )


def test_a_kind_nobody_has_reasoned_about_is_refused_rather_than_backfilled():
    """Yahoo, multpl, LBMA, the HERMES peer and manual entry: today's value wearing a past date
    is the forgery this WO exists to prevent, so the answer is a refusal.

    WO-1.16 MOVED ``cboe`` OUT OF THIS SET and the test says so by deriving the set from
    :data:`VINTAGE_BACKFILLABLE_KINDS` rather than by listing non-FRED kinds. Cboe is not an
    exception carved into a refusal — it is a kind with its own probed warrant
    (:data:`~ingestion.vintage.VINTAGE_NO_REVISION_MECHANISM`), so it routes. ``yahoo`` is the
    one that stayed, and it is the interesting one: it has no vintage endpoint either, but its
    ``adjclose`` is retroactively restated by every dividend and split.
    """
    assert VINTAGE_BACKFILLABLE_KINDS == ("fred", "cboe")
    others = [i for i in INGREDIENTS if i.kind not in VINTAGE_BACKFILLABLE_KINDS]
    assert {i.kind for i in others} == {"yahoo", "multpl", "lbma", "hermes", "manual"}
    for ing in others:
        with pytest.raises(ValueError):
            build_backfill_adapter(ing, OBS, CLOCK)


def test_a_cboe_ingredient_routes_to_a_dated_cboe_adapter_and_is_asked_no_vintage_question(
        monkeypatch):
    """The other half of the boundary above: the kind that was added actually goes somewhere.

    ``requires_original_vintage`` must not be CONSULTED — it answers about a FRED pair, and
    its fail-safe ``True`` would point a Cboe index id at the ALFRED adapter. Asserting the
    returned type alone would not catch that: a dispatch that asked the question and then
    ignored the answer would still hand back a ``CboeAdapter``. So the function is replaced
    with one that fails the test by name if it is reached at all.
    """
    def explode(*args, **kwargs):
        raise AssertionError("a FRED vintage question was asked about a non-FRED ingredient")

    monkeypatch.setattr("ingestion.backfill_adapters.requires_original_vintage", explode)
    cboe = [i for i in INGREDIENTS if i.kind == "cboe"]
    assert {i.source_id for i in cboe} == {"cboe.VIX", "cboe.VIX3M", "cboe.SKEW"}
    for ing in cboe:
        adapter = build_backfill_adapter(ing, OBS, CLOCK)
        assert type(adapter) is A.CboeAdapter, ing.source_id
        # The date reached it, and reaching it is the whole difference between a backfill
        # and a re-read of this week's close.
        assert adapter._observation_date == OBS
        assert adapter._url() == build_adapter(ing, CLOCK)._url(), (
            "the URL is static: a dated Cboe request asks for the same body the live one does"
        )


# --- TWO: the live loop cannot reach the vintage adapter ------------------------------- #


def test_the_live_path_never_returns_the_vintage_adapter_for_anything():
    """Including the revision-prone series: the LIVE question is "the latest value", and the
    answer to it is a FredAdapter whether or not the series gets revised."""
    live = [build_adapter(i, CLOCK) for i in INGREDIENTS if i.kind != "manual"]
    assert not any(isinstance(a, A.AlfredVintageAdapter) for a in live)
    prone = [i for i in FRED if requires_original_vintage(i.ref, i.transformation)]
    assert len(prone) == 17 and all(type(build_adapter(i, CLOCK)) is A.FredAdapter for i in prone)


def test_the_live_constructor_has_no_argument_that_could_select_a_vintage_adapter():
    """Unchanged signature, and that is the point: not a flag a future caller passes wrong."""
    assert list(inspect.signature(build_adapter).parameters) == ["ing", "clock"]
    assert list(inspect.signature(build_backfill_adapter).parameters) == [
        "ing", "observation_date", "clock"]


def test_the_live_catalog_module_neither_imports_nor_exposes_the_vintage_adapter():
    assert not hasattr(C, "AlfredVintageAdapter")
    assert "AlfredVintageAdapter" not in C.__all__
    imported = _imported_names("ingestion/catalog.py")
    assert not any("Alfred" in name or "backfill" in name for name in imported), imported


def test_the_live_collector_loop_does_not_import_the_backfill_module():
    """``ingestion.run`` is the loop. It reaches build_adapter and nothing else."""
    assert not hasattr(live_run, "build_backfill_adapter")
    imported = _imported_names("ingestion/run.py")
    assert "ingestion.catalog.build_adapter" in imported
    assert not any("Alfred" in name or "backfill" in name for name in imported), imported


def test_the_dependency_runs_one_way_so_the_reverse_would_be_an_import_cycle():
    """The structural half: backfill -> catalog, never catalog -> backfill."""
    assert "ingestion.catalog" in _imported_names("ingestion/backfill_adapters.py")
    assert "ingestion.backfill_adapters" not in _imported_names("ingestion/catalog.py")


# --- THREE: the host is declared where it is true -------------------------------------- #


def test_the_vintage_host_is_declared_for_the_backfill_path_and_only_there():
    assert set(BACKFILL_EGRESS_HOSTS) == {A.ALFRED_HOST}
    assert BACKFILL_EGRESS_HOSTS[A.ALFRED_HOST].startswith("Federal Reserve Bank of St. Louis")
    # The three declarations of what the LIVE collector reaches, each asserted ABSENT.
    assert A.ALFRED_HOST not in EGRESS_HOSTS and A.ALFRED_HOST not in NON_HTTP_PEERS
    registry = load_compose(ROOT / "deploy/egress-destinations.yaml")["destinations"]
    assert A.ALFRED_HOST not in {d["host"] for d in registry}
    collectors = load_compose(ROOT / "deploy/compose.yaml")["services"]["cd-collectors"]
    assert A.ALFRED_HOST not in collectors["x-egress"]["hosts"]
    assert set(collectors["x-egress"]["hosts"]) == {d["host"] for d in registry}
    # ...and the two Python declarations are disjoint, so neither can be read as the other.
    assert not set(EGRESS_HOSTS) & set(BACKFILL_EGRESS_HOSTS)


def test_the_live_egress_declaration_is_still_exactly_what_the_live_adapters_reach():
    """The invariant this round had to not break: EGRESS_HOSTS == the live URLs' hostnames."""
    hosts = {urlsplit(build_adapter(i, CLOCK)._url()).hostname
             for i in INGREDIENTS if i.kind not in ("manual", "hermes")}
    assert hosts == set(EGRESS_HOSTS)


def test_every_backfill_url_reaches_a_declared_host_and_only_the_prone_ones_reach_alfred():
    reached = {}
    for ing in FRED:
        host = urlsplit(build_backfill_adapter(ing, OBS, CLOCK)._url()).hostname
        reached.setdefault(host, []).append(ing.source_id)
    assert set(reached) <= set(EGRESS_HOSTS) | set(BACKFILL_EGRESS_HOSTS)
    assert set(reached) == {A.ALFRED_HOST, "fred.stlouisfed.org"}
    assert all(requires_original_vintage(_ing(s).ref, _ing(s).transformation)
               for s in reached[A.ALFRED_HOST])


def test_the_backfill_module_records_what_the_driver_round_still_owes():
    """The compose service and the DEST-ALFRED-001 registration are OWED, not forgotten: a
    backfill that cannot be permitted anywhere is fail-closed, and saying so is the deal."""
    import ingestion.backfill_adapters as B

    doc = B.__doc__ + inspect.getsource(B)
    assert "DEST-ALFRED-001" in doc and "OWED" in doc
    assert "cd-collectors" in doc
