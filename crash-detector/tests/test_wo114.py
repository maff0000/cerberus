"""WO-1.14 ROUTING: which constructor a FRED ingredient gets, and which one it can never get.

Two claims, and the second is the load-bearing one.

ONE — the ROUTE IS THE EVIDENCE'S. A FRED ingredient whose (series, transformation) pair
``ingestion.vintage.requires_original_vintage`` answers YES for is backfilled through
``FredVintageAdapter`` (the figure as FIRST published); a pair measured stable is
backfilled from FRED's current body through the ordinary ``FredAdapter``. Nothing in
``ingestion.backfill_adapters`` decides that — the declaration does, and these tests sweep
every FRED ingredient in the catalog so the two cannot drift apart for 16 of 24 series while
looking right for the one a hand-written test happened to name.

TWO — the LIVE LOOP CANNOT REACH THE VINTAGE ADAPTER, STRUCTURALLY. ``FredVintageAdapter``
spends one GET (or, for a transformed series, ``2 + ceil(log2(days))``) per ``fetch`` under a total deadline and answers for one
named observation date. In ``ingestion.run``'s loop — a few seconds per attempt, "the latest
value", every ingredient every pass — it would be wrong twice over. So the tests below hold
the SHAPE that makes it unreachable rather than the habit of not reaching it:
``build_adapter`` has no argument that could select it, ``ingestion.catalog`` does not import
or expose it, ``ingestion.run`` does not import the module that does, and the dependency runs
one way only (backfill -> catalog), so the reverse is an import cycle rather than an edit.

THREE — THE HOST IS DECLARED WHERE IT IS TRUE. ``api.stlouisfed.org`` is reached by the
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
#: Key-shaped and worth nothing; the real credential is never in this tree.
KEY = "k" * 32
FRED = tuple(i for i in INGREDIENTS if i.kind == "fred")


def _ing(source_id: str):
    return next(i for i in INGREDIENTS if i.source_id == source_id)


def _imported_names(module_path: str) -> set:
    """Every module and name a file IMPORTS, read from its AST rather than from its text.

    AST and not ``in source``: a prose mention of ``FredVintageAdapter`` in a comment that
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
    adapter = build_backfill_adapter(_ing("fred.GDP"), OBS, CLOCK, api_key=KEY)
    assert type(adapter) is A.FredVintageAdapter
    assert adapter.adapter_id == "cd.ingest.fred_vintage_rest.v1"
    assert adapter.source_id == "fred.GDP"
    parts = urlsplit(adapter._url())
    assert parts.hostname == A.FRED_API_HOST and "series_id=GDP" in parts.query and OBS in parts.query
    assert "api_key" not in parts.query  # the host-declaring URL never carries the credential


def test_a_revision_prone_transformed_pair_carries_its_transformation_into_the_vintage_fetch():
    """The pair is (series, transformation): M2SL's pc1 is what was declared revision-prone."""
    adapter = build_backfill_adapter(_ing("fred.M2SL.pc1"), OBS, CLOCK, api_key=KEY)
    assert type(adapter) is A.FredVintageAdapter
    assert "units=pc1" in urlsplit(adapter._url()).query


def test_a_measured_stable_fred_ingredient_backfills_from_freds_current_body():
    """DFF differs in ZERO of 2,369 shared observations over the replay window (ingestion.vintage)."""
    adapter = build_backfill_adapter(_ing("fred.DFF"), OBS, CLOCK, api_key=KEY)
    assert type(adapter) is A.FredAdapter
    assert urlsplit(adapter._url()).hostname == "fred.stlouisfed.org"


def test_every_fred_ingredient_routes_exactly_as_the_vintage_declaration_says():
    """The sweep. Not one named series each way — all 24, against the declaration itself."""
    prone, stable = [], []
    for ing in FRED:
        adapter = build_backfill_adapter(ing, OBS, CLOCK, api_key=KEY)
        if requires_original_vintage(ing.ref, ing.transformation):
            assert type(adapter) is A.FredVintageAdapter, ing.source_id
            prone.append(ing.source_id)
        else:
            assert type(adapter) is A.FredAdapter, ing.source_id
            stable.append(ing.source_id)
    # 25 FRED ingredient rows over 24 distinct (series, transformation) pairs: DFII10 is
    # ingested twice, once plain and once with history for the gold_real_rate_cross
    # derivation. Both rows route the same way, because the route is a property of the PAIR
    # the evidence judged and not of the catalog row — which is why this is a sweep.
    #
    # WO-1.19 MOVED THIS FROM 24/23 BY ADDING ONE ROW AND ONE PAIR: DRTSCIS, the small-firm
    # leg of sloos_bank_lending, which took over from a manual table-scrape that was never
    # automatable. The gap between the two numbers is still exactly one and still DFII10's —
    # a second series ingested twice would show up here as the gap widening, not as a pair
    # quietly routing on someone else's evidence.
    assert len(FRED) == 25 and len({(i.ref, i.transformation) for i in FRED}) == 24
    # 16 measured revision-prone + 2 UNDETERMINED (fail-safe: fetched point-in-time) = 18
    # pairs, and 6 measured-stable pairs over 7 rows. DRTSCIS is the 16th, and it is MEASURED
    # — probed on its own against ALFRED, 18 of the 81 observations its first vintage shares
    # with today's differing materially — not inherited from its DRTSCILM sibling.
    assert (len(prone), len(stable)) == (18, 7)
    assert [s for s in stable if s.startswith("fred.DFII10")] == [
        "fred.DFII10", "fred.DFII10.history"]
    assert {"fred.BAMLC0A0CM", "fred.BAMLH0A0HYM2"} <= set(prone), (
        "an unprobed or undetermined pair must be fetched vintage-by-vintage, never trusted"
    )


def test_a_kind_nobody_has_reasoned_about_is_refused_rather_than_backfilled():
    """multpl and the HERMES peer: today's value wearing a past date is the forgery
    this WO exists to prevent, so the answer is a refusal.

    ``manual`` WAS A FOURTH KIND HERE AND IS NOT ONE ANY MORE (WO-1.19) — not admitted, but
    retired: its only row, ``sloos_bank_lending``'s hand-entered second leg, became the
    ``DRTSCIS`` FRED feed. A kind with no rows cannot be refused, so naming it in the set
    below would be asserting a boundary nothing stands on.

    ``lbma`` HAS NOW LEFT THIS SET THE SAME WAY (WO-1.20), and for the same reason rather than
    a new one: its only row, ``gold_real_rate_cross``'s gold leg, became ``yahoo.GC=F.history``,
    and the kind, its adapter and its egress host are gone from the tree. RETIRED, NOT ADMITTED
    — it is absent here because there is nothing of that kind left to refuse, not because a
    point-in-time backfill of it was ever reasoned about. ``ingestion.backfill_adapters``'
    declaration carries the same note.

    WO-1.16 MOVED ``cboe`` AND THEN ``yahoo`` OUT OF THIS SET, and the test says so by
    deriving the set from :data:`VINTAGE_BACKFILLABLE_KINDS` rather than by listing non-FRED
    kinds — a listed set would have had to be rewritten twice to keep asserting a boundary
    that had moved underneath it. Neither is an exception carved into a refusal; each has its
    own probed warrant (:data:`~ingestion.vintage.VINTAGE_NO_REVISION_MECHANISM`), so each
    routes.

    ``yahoo`` LEAVING THIS SET IS NOT THE SAME AS EVERY YAHOO ROW ROUTING, and that is the
    one thing a reader of this test must not conclude from it. The kind is admitted for the
    PRINTED close; the 51 ``adjclose`` rows are still refused, by the adapter rather than by
    the tuple, and the two tests below hold both halves.
    """
    assert VINTAGE_BACKFILLABLE_KINDS == ("fred", "cboe", "yahoo")
    others = [i for i in INGREDIENTS if i.kind not in VINTAGE_BACKFILLABLE_KINDS]
    assert {i.kind for i in others} == {"multpl", "hermes"}
    for ing in others:
        with pytest.raises(ValueError):
            build_backfill_adapter(ing, OBS, CLOCK, api_key=KEY)


def test_a_cboe_ingredient_routes_to_a_dated_cboe_adapter_and_is_asked_no_vintage_question(
        monkeypatch):
    """The other half of the boundary above: the kind that was added actually goes somewhere.

    ``requires_original_vintage`` must not be CONSULTED — it answers about a FRED pair, and
    its fail-safe ``True`` would point a Cboe index id at the vintage adapter. Asserting the
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
        adapter = build_backfill_adapter(ing, OBS, CLOCK, api_key=KEY)
        assert type(adapter) is A.CboeAdapter, ing.source_id
        # The date reached it, and reaching it is the whole difference between a backfill
        # and a re-read of this week's close.
        assert adapter._observation_date == OBS
        assert adapter._url() == build_adapter(ing, CLOCK)._url(), (
            "the URL is static: a dated Cboe request asks for the same body the live one does"
        )


def test_a_plain_close_yahoo_ingredient_routes_to_a_dated_yahoo_adapter_and_is_asked_no_vintage_question(
        monkeypatch):
    """The Cboe test above, for the kind WO-1.16 wired second — and one assertion inverted.

    ``requires_original_vintage`` must not be CONSULTED, for the reason it must not be for
    Cboe: it answers about a FRED (series, transformation) pair, a Yahoo symbol is not in
    :data:`~ingestion.vintage.REVISION_STABLE` and never could be, and its fail-safe ``True``
    would point ``yahoo.SPY`` at the vintage adapter. Asserting the returned TYPE would not
    catch a dispatch that asked the question and ignored the answer, so the function is
    replaced with one that fails this test by name if it is reached at all.

    WHERE THIS DIVERGES FROM THE CBOE TEST, AND WHY THE DIVERGENCE IS THE POINT. A dated Cboe
    request addresses the SAME URL as the live one — the body is static and only the row read
    changes — so that test asserts URL EQUALITY. Yahoo is the opposite: the dated request
    REPLACES ``range`` with an absolute ``period1``/``period2`` window, because given both in
    one URL ``range`` silently WINS and the whole relative body comes back
    (``evidence/wo116_yahoo_window_probe.json``, ``q6_range_and_period_together``). So the
    assertion here is URL INEQUALITY in a NAMED direction: no ``range=`` at all, and a window
    whose bounds are the UTC day of the date asked for rather than merely some window.

    THE FIELD IS ASSERTED AGAINST THE LIVE CONSTRUCTOR'S RESOLUTION, not against the literal
    ``"close"``. The catalog leaves ``column`` empty for the default and
    ``ingestion.catalog.build_adapter`` resolves it with ``field=ing.column or "close"``; a
    backfill that resolved it any other way would store a different QUANTITY under the same
    ingredient than the live collector does, which is the WO-1.14 defect class by field
    instead of by date. Asserting equality with ``build_adapter``'s own choice is what keeps
    the two from drifting apart.
    """
    def explode(*args, **kwargs):
        raise AssertionError("a FRED vintage question was asked about a non-FRED ingredient")

    monkeypatch.setattr("ingestion.backfill_adapters.requires_original_vintage", explode)
    plain = [i for i in INGREDIENTS if i.kind == "yahoo" and i.column == ""]
    # EIGHT SINCE WO-1.20: ``yahoo.GC=F.history`` reads the printed close like the other seven,
    # so it routes here on exactly the same warrant. Spelled out rather than derived from the
    # same predicate the loop below filters on, which would assert nothing.
    assert {i.source_id for i in plain} == {"yahoo.HYG", "yahoo.LQD", "yahoo.RSP", "yahoo.SPY",
                                            "yahoo.^GSPC", "yahoo.HG=F", "yahoo.GC=F",
                                            "yahoo.GC=F.history"}
    for ing in plain:
        adapter = build_backfill_adapter(ing, OBS, CLOCK, api_key=KEY)
        assert type(adapter) is A.YahooChartAdapter, ing.source_id
        # The date reached it, and reaching it is the whole difference between a backfill and
        # a re-read of this week's close.
        assert adapter._observation_date == OBS
        assert adapter._field == build_adapter(ing, CLOCK)._field == "close", ing.source_id
        query = urlsplit(adapter._url()).query
        assert "range=" not in query, (
            f"{ing.source_id}: range= silently wins over a period window, so a dated request "
            f"that kept it would be handed a relative body ending at this morning's bar"
        )
        assert "period1=" in query and "period2=" in query, ing.source_id
        assert "range=" in urlsplit(build_adapter(ing, CLOCK)._url()).query, (
            f"{ing.source_id}: the LIVE request is the relative one and must stay that way"
        )
    # The window is the UTC day of OBS and not merely a window: 2008-09-01T00:00:00Z and the
    # last second of that day, which is the bound the probe measured (a zero-width window at
    # midnight returns no bars for a real trading session).
    spy = urlsplit(build_backfill_adapter(_ing("yahoo.SPY"), OBS, CLOCK, api_key=KEY)._url()).query
    assert "period1=1220227200" in spy and "period2=1220313599" in spy, spy


def test_an_adjclose_yahoo_ingredient_is_refused_rather_than_handed_a_working_adapter():
    """THE ROW THE WIRING MUST NOT ADMIT, asked of the real catalog ingredients.

    ``private_credit_stress``'s ``yahoo.BIZD.adj`` and all 50 rows of
    ``constituent_breadth_200dma``'s sample ask for ``adjclose`` deliberately and with
    measured cause, and a dated read of that field has no point-in-time meaning at all: it is
    restated backwards by every dividend and split, forever (PID.md WO-1.16 scope
    correction). ``yahoo`` being in :data:`VINTAGE_BACKFILLABLE_KINDS` is therefore NOT a
    statement about these rows, and this test is what keeps the distance between those two
    sentences from closing by accident.

    THE REFUSAL IS THE ADAPTER'S AND THERE IS DELIBERATELY NO SECOND COPY OF IT HERE, which
    is the other half of what is asserted. ``build_backfill_adapter`` has no ``adjclose``
    check of its own; it resolves ``ing.column`` to ``field=`` and the constructor raises
    before a URL is built or a byte is fetched, so the refusal propagates out of the
    constructor this function is REQUIRED to call. That is asserted twice over: once by the
    raise arriving at this call site with the adapter's own words, and once structurally —
    the function's code contains no ``"adjclose"`` literal, read from its AST so the comment
    that explains the absence does not read as the check itself. A third copy of the rule
    would add no defence and one more place for it to drift; the genuinely independent second
    door is a DIFFERENT question at a different dispatch
    (``tests/test_vintage_declaration.py``: ``ingestion.backfill`` can derive no label for
    these rows and stops the range).

    THE LIVE PATH IS ASSERTED STILL TO WORK, because "refuse closed" must not quietly become
    "refuse". These are live COMPONENTs polled every pass; the refusal is scoped to the DATED
    question and the undated one is unaffected.
    """
    adj = [i for i in INGREDIENTS if i.kind == "yahoo" and i.column == "adjclose"]
    assert len(adj) == 51 and "yahoo.BIZD.adj" in {i.source_id for i in adj}, (
        "the adjclose ingredients have changed shape — re-reason this guard"
    )
    for ing in adj:
        with pytest.raises(ValueError, match="adjclose has no"):
            build_backfill_adapter(ing, OBS, CLOCK, api_key=KEY)
        live = build_adapter(ing, CLOCK)
        assert type(live) is A.YahooChartAdapter and live._field == "adjclose", ing.source_id
        assert live._observation_date is None, ing.source_id

    source = inspect.getsource(build_backfill_adapter)
    literals = {node.value for node in ast.walk(ast.parse(source.strip()))
                if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    assert "adjclose" not in literals, (
        "build_backfill_adapter has acquired its own adjclose check; the rule lives in "
        "YahooChartAdapter.__init__ and a second copy is a second thing to keep in step"
    )


# --- TWO: the live loop cannot reach the vintage adapter ------------------------------- #


def test_the_live_path_never_returns_the_vintage_adapter_for_anything():
    """Including the revision-prone series: the LIVE question is "the latest value", and the
    answer to it is a FredAdapter whether or not the series gets revised."""
    live = [build_adapter(i, CLOCK) for i in INGREDIENTS if i.kind != "manual"]
    assert not any(isinstance(a, A.FredVintageAdapter) for a in live)
    prone = [i for i in FRED if requires_original_vintage(i.ref, i.transformation)]
    assert len(prone) == 18 and all(type(build_adapter(i, CLOCK)) is A.FredAdapter for i in prone)


def test_the_live_constructor_has_no_argument_that_could_select_a_vintage_adapter():
    """Unchanged signature, and that is the point: not a flag a future caller passes wrong."""
    assert list(inspect.signature(build_adapter).parameters) == ["ing", "clock"]
    assert list(inspect.signature(build_backfill_adapter).parameters) == [
        "ing", "observation_date", "clock", "api_key", "archive_floors"]


def test_the_live_catalog_module_neither_imports_nor_exposes_the_vintage_adapter():
    assert not hasattr(C, "FredVintageAdapter")
    assert "FredVintageAdapter" not in C.__all__
    imported = _imported_names("ingestion/catalog.py")
    assert not any("Vintage" in name or "backfill" in name for name in imported), imported


def test_the_live_collector_loop_does_not_import_the_backfill_module():
    """``ingestion.run`` is the loop. It reaches build_adapter and nothing else."""
    assert not hasattr(live_run, "build_backfill_adapter")
    imported = _imported_names("ingestion/run.py")
    assert "ingestion.catalog.build_adapter" in imported
    assert not any("Vintage" in name or "backfill" in name for name in imported), imported


def test_the_dependency_runs_one_way_so_the_reverse_would_be_an_import_cycle():
    """The structural half: backfill -> catalog, never catalog -> backfill."""
    assert "ingestion.catalog" in _imported_names("ingestion/backfill_adapters.py")
    assert "ingestion.backfill_adapters" not in _imported_names("ingestion/catalog.py")


# --- THREE: the host is declared where it is true -------------------------------------- #


def test_the_vintage_host_is_declared_for_the_backfill_path_and_only_there():
    assert set(BACKFILL_EGRESS_HOSTS) == {A.FRED_API_HOST}
    assert BACKFILL_EGRESS_HOSTS[A.FRED_API_HOST].startswith("Federal Reserve Bank of St. Louis")
    # The three declarations of what the LIVE collector reaches, each asserted ABSENT.
    assert A.FRED_API_HOST not in EGRESS_HOSTS and A.FRED_API_HOST not in NON_HTTP_PEERS
    registry = load_compose(ROOT / "deploy/egress-destinations.yaml")["destinations"]
    assert A.FRED_API_HOST not in {d["host"] for d in registry}
    collectors = load_compose(ROOT / "deploy/compose.yaml")["services"]["cd-collectors"]
    assert A.FRED_API_HOST not in collectors["x-egress"]["hosts"]
    assert set(collectors["x-egress"]["hosts"]) == {d["host"] for d in registry}
    # ...and the two Python declarations are disjoint, so neither can be read as the other.
    assert not set(EGRESS_HOSTS) & set(BACKFILL_EGRESS_HOSTS)


def test_the_live_egress_declaration_is_still_exactly_what_the_live_adapters_reach():
    """The invariant this round had to not break: EGRESS_HOSTS == the live URLs' hostnames."""
    hosts = {urlsplit(build_adapter(i, CLOCK)._url()).hostname
             for i in INGREDIENTS if i.kind not in ("manual", "hermes")}
    assert hosts == set(EGRESS_HOSTS)


def test_every_backfill_url_reaches_a_declared_host_and_only_the_prone_ones_reach_the_rest_api():
    reached = {}
    for ing in FRED:
        host = urlsplit(build_backfill_adapter(ing, OBS, CLOCK, api_key=KEY)._url()).hostname
        reached.setdefault(host, []).append(ing.source_id)
    assert set(reached) <= set(EGRESS_HOSTS) | set(BACKFILL_EGRESS_HOSTS)
    assert set(reached) == {A.FRED_API_HOST, "fred.stlouisfed.org"}
    assert all(requires_original_vintage(_ing(s).ref, _ing(s).transformation)
               for s in reached[A.FRED_API_HOST])


def test_the_backfill_module_records_what_the_driver_round_still_owes():
    """WO-1.17: no registration is owed while the driver is a host-level script, and the module
    says so, naming the obligation that returns (DEST-FRED-API-001) if it is ever containerised. The old text: a
    backfill that cannot be permitted anywhere is fail-closed, and saying so is the deal."""
    import ingestion.backfill_adapters as B

    doc = B.__doc__ + inspect.getsource(B)
    assert "DEST-FRED-API-001" in doc and "host-level" in doc
    assert "cd-collectors" in doc


# --- FOUR: the credential ------------------------------------------------------------------ #


def test_a_revision_prone_row_is_refused_at_construction_without_a_key_and_a_stable_one_is_not():
    """Only the rows that read the keyed endpoint need a key; nothing is built around a missing one."""
    with pytest.raises(ValueError) as refused:
        build_backfill_adapter(_ing("fred.GDP"), OBS, CLOCK)
    assert "api_key" in str(refused.value)
    assert type(build_backfill_adapter(_ing("fred.DFF"), OBS, CLOCK)) is A.FredAdapter
    assert type(build_backfill_adapter(_ing("cboe.VIX"), OBS, CLOCK)) is A.CboeAdapter


def test_the_key_is_handed_to_the_vintage_adapter_and_to_no_other_adapter():
    """The keyless branches never receive it — they take no such argument — so it cannot be
    appended to a Cboe, Yahoo or plain-FRED request by accident."""
    for ing in FRED:
        adapter = build_backfill_adapter(ing, OBS, CLOCK, api_key=KEY)
        if type(adapter) is A.FredVintageAdapter:
            assert adapter._api_key == KEY and KEY not in adapter._url()
        else:
            assert not hasattr(adapter, "_api_key") and KEY not in adapter._url()
