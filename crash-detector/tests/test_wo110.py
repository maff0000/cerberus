"""WO-1.10: constituent_breadth_200dma = percent of a DEFINED 50-name large-cap sample above its own 200-day mean.

Ported from the legacy ARGUS ``equity_tells.fetch_breadth``. A new indicator beside ``breadth_rsp_spy``, never a
replacement. Fails loud below 30 of 50 resolving; the sample-defined disclosure travels with it."""

from __future__ import annotations

import json
import statistics
from datetime import date, timedelta
from pathlib import Path

import pytest

from crash_detector.engine.derivations import (
    BREADTH_MINIMUM_RESOLVED,
    BREADTH_SAMPLE,
    DERIVATIONS,
    DerivationUnavailable,
    derive,
)
from gui import server as gui_server
from gui.state import build_state
from ingestion.catalog import INGREDIENTS, PROVISIONAL_CONSTRUCTIONS, QUORUM, build_adapter
from ingestion.report import indicator_states
from ingestion.store import SqliteStore
from ingestion.wiring import DERIVED_FROM, build_wiring, observations_from_store

from test_wiring import CALM, NOW, SCALING_JSON, _breadth_components, _expected, _put, _seed, _rows

IND = "constituent_breadth_200dma"
DAY = "2026-10-09"


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "raw.sqlite")


def _dates(n, end=DAY):
    last = date.fromisoformat(end)
    return [(last - timedelta(days=n - 1 - i)).isoformat() for i in range(n)]


def _payload(closes, end=DAY):
    rows = [[d, c] for d, c in zip(_dates(len(closes), end), closes)]
    return {"unit": "usd", "observation_date": rows[-1][0], "value": rows[-1][1], "history": rows}


def _inputs(per_name):
    """{role: [payload]} for every sample name; a name absent from `per_name` has NO stored reading."""
    return {name: ([_payload(per_name[name])] if name in per_name else []) for name in BREADTH_SAMPLE}


def _above(n):
    return [100.0] * 209 + [110.0]


def _below(n=None):
    return [100.0] * 209 + [90.0]


def _mix(n_above, n_below, n_absent=0):
    names = list(BREADTH_SAMPLE)
    per = {}
    for i, name in enumerate(names[: n_above + n_below]):
        per[name] = _above(0) if i < n_above else _below()
    return _inputs(per)


# --- the sample ----------------------------------------------------------------------------------------- #


def test_the_sample_is_fifty_unique_names_and_matches_the_legacy_definition_when_it_is_reachable():
    assert len(BREADTH_SAMPLE) == 50 == len(set(BREADTH_SAMPLE))
    assert BREADTH_SAMPLE[0] == "AAPL" and BREADTH_SAMPLE[-1] == "UNP" and "BRK-B" in BREADTH_SAMPLE
    legacy = Path("/srv-argus-live/ARGUS/src/calc/tells/equity_tells.py")
    if not legacy.exists():
        pytest.skip("legacy ARGUS source not on this host")
    namespace: dict = {}
    text = legacy.read_text()
    block = text[text.index("BREADTH_SAMPLE = ["):]
    exec(block[: block.index("]") + 1], namespace)  # only the literal list assignment
    assert tuple(namespace["BREADTH_SAMPLE"]) == BREADTH_SAMPLE


def test_the_floor_is_thirty_of_fifty_as_in_the_legacy_tell():
    assert BREADTH_MINIMUM_RESOLVED == 30 and QUORUM[IND] == 30


# --- the derivation ------------------------------------------------------------------------------------- #


def test_the_figure_is_the_percent_above_over_those_resolved_matching_an_independent_computation():
    inputs = _mix(35, 15)
    got = derive(IND, inputs)
    independent = 100.0 * sum(
        1 for name in BREADTH_SAMPLE
        if inputs[name][0]["value"] > statistics.mean(c for _, c in inputs[name][0]["history"][-200:])
    ) / len(BREADTH_SAMPLE)
    assert got.value == pytest.approx(independent) == pytest.approx(70.0)
    assert got.observation_date == DAY and got.unit == "percent_of_sample_above_200dma"


def test_absent_names_leave_the_denominator_not_the_numerator():
    got = derive(IND, _mix(20, 15))  # 35 resolved, 15 with no reading
    assert got.value == pytest.approx(100.0 * 20 / 35)


def test_a_close_exactly_at_its_mean_is_not_above_it():
    flat = {name: [100.0] * 210 for name in BREADTH_SAMPLE}
    assert derive(IND, _inputs(flat)).value == 0.0


def test_only_the_last_two_hundred_closes_form_the_mean():
    # 1000-valued old closes would drag a longer mean far above the latest 110; the last 200 sit at 100.
    closes = [1000.0] * 10 + [100.0] * 199 + [110.0]
    assert derive(IND, _inputs({name: closes for name in BREADTH_SAMPLE})).value == 100.0
    assert statistics.mean(closes[-210:]) > 110.0  # the longer window would have said below


def test_one_hundred_ninety_nine_closes_does_not_resolve_and_two_hundred_does():
    short = [100.0] * 198 + [110.0]  # 199 closes
    exact = [100.0] * 199 + [110.0]  # 200 closes
    per = {name: exact for name in BREADTH_SAMPLE[:30]} | {name: short for name in BREADTH_SAMPLE[30:]}
    assert derive(IND, _inputs(per)).value == 100.0  # exactly the 30 with 200 closes resolve
    per = {name: exact for name in BREADTH_SAMPLE[:29]} | {name: short for name in BREADTH_SAMPLE[29:]}
    with pytest.raises(DerivationUnavailable, match=r"only 29 of 50"):
        derive(IND, _inputs(per))


def test_thirty_resolved_is_enough_and_twenty_nine_returns_no_figure_naming_the_unresolved():
    assert derive(IND, _mix(15, 15)).value == 50.0
    with pytest.raises(DerivationUnavailable) as why:
        derive(IND, _mix(15, 14))
    text = str(why.value)
    assert "only 29 of 50" in text and "<30" in text and BREADTH_SAMPLE[-1] in text and "thinned sample" in text


def test_an_empty_store_for_every_name_is_unavailable_not_zero_and_not_a_crash():
    with pytest.raises(DerivationUnavailable, match=r"only 0 of 50"):
        derive(IND, _inputs({}))


def test_a_name_whose_latest_close_is_older_than_the_newest_is_unresolved_not_carried_forward():
    per = {name: _above(0) for name in BREADTH_SAMPLE}
    inputs = _inputs(per)
    stale = {name: [_payload(per[name], end="2026-10-02")] for name in BREADTH_SAMPLE[:20]}
    inputs.update(stale)  # 20 names end a week earlier: 30 resolve on DAY
    got = derive(IND, inputs)
    assert got.observation_date == DAY and got.value == 100.0
    inputs.update({name: [_payload(per[name], end="2026-10-02")] for name in BREADTH_SAMPLE[:21]})
    with pytest.raises(DerivationUnavailable, match=r"only 29 of 50"):
        derive(IND, inputs)


def test_malformed_names_are_unresolved_individually_and_never_corrupt_the_rest():
    inputs = _mix(20, 20)  # 40 resolved
    good = BREADTH_SAMPLE[0]
    inputs[BREADTH_SAMPLE[45]] = [{"unit": "usd", "value": 1.0}]  # no date, no history
    inputs[BREADTH_SAMPLE[46]] = [{"unit": "usd", "observation_date": DAY, "value": float("nan"), "history": []}]
    lie = _payload(_above(0))
    lie["value"] = 999.0  # the reading is not the last close of its own history
    inputs[BREADTH_SAMPLE[47]] = [lie]
    zero = _payload([0.0] * 210)
    inputs[BREADTH_SAMPLE[48]] = [zero]
    assert derive(IND, inputs).value == pytest.approx(100.0 * 20 / 40)
    assert inputs[good][0]["value"] == 110.0


def test_the_derivation_is_registered_with_the_sample_as_its_roles():
    spec = DERIVATIONS[IND]
    assert spec.roles == BREADTH_SAMPLE and spec.window == 200 and spec.unit == "percent_of_sample_above_200dma"


# --- the catalog and the wiring --------------------------------------------------------------------------- #


def test_fifty_dividend_adjusted_components_with_enough_history_serve_only_this_indicator():
    ings = [i for i in INGREDIENTS if IND in i.serves]
    assert [i.ref for i in ings] == list(BREADTH_SAMPLE)
    for ing in ings:
        assert ing.serves == (IND,) and ing.kind == "yahoo" and ing.completes == "COMPONENT" and ing.column == "adjclose"
        assert ing.history >= 200
        adapter = build_adapter(ing, lambda: NOW)
        assert adapter._field == "adjclose" and "range=2y" in adapter._url()
    assert len({i.source_id for i in ings}) == 50
    assert "BRK-B" in build_adapter(next(i for i in ings if i.ref == "BRK-B"), lambda: NOW)._url()
    assert DERIVED_FROM[IND] == tuple(i.source_id for i in ings)


def test_breadth_rsp_spy_is_untouched_and_both_are_live_and_distinct():
    wiring = build_wiring()
    assert DERIVED_FROM["breadth_rsp_spy"] == ("yahoo.RSP", "yahoo.SPY")
    assert "breadth_rsp_spy" in wiring.derived_for and IND in wiring.derived_for
    scaling = json.loads(SCALING_JSON.read_text())["equity_crash"]
    assert scaling["breadth_rsp_spy"] == {"calm": 0.29, "stress": 0.25, "required": False}
    assert scaling[IND] == {"calm": 70.0, "stress": 30.0, "required": False}


def test_the_row_is_equity_only_lowest_tier_low_is_worse_and_the_band_agrees_with_the_polarity():
    row = next(r for r in _rows() if r["id"] == IND)
    assert row["dial"] == "equity_crash" and row["tier"] == 3 and row["polarity"] == "low_is_worse"
    assert row["staleness_window_seconds"] == 604800 and row["cadence"] == "daily"
    scaling = json.loads(SCALING_JSON.read_text())
    assert IND not in scaling["monetary_debasement"]
    assert scaling["equity_crash"][IND]["calm"] > scaling["equity_crash"][IND]["stress"]  # low_is_worse
    assert not scaling["equity_crash"][IND]["required"]


def test_the_disclosure_says_what_it_is_and_what_it_is_not():
    text = PROVISIONAL_CONSTRUCTIONS[IND]
    for needle in ("FIXED 50-name", "NOT the S&P 500", "30 of the 50", "placeholder", "x1", "breadth_rsp_spy"):
        assert needle in text


# --- the live path: store -> dial -> page ----------------------------------------------------------------- #


def _state(db_path, now=NOW):
    with SqliteStore(db_path, read_only=True) as ro:
        return build_state(ro, now)


def _row(db_path, now=NOW):
    return next(i for i in _state(db_path, now)["indicators"] if i["id"] == IND)


def test_unfed_it_reads_missing_and_yields_no_observation_never_calm(db_path):
    with SqliteStore(db_path) as w:
        assert not [o for o in observations_from_store(w, build_wiring(), NOW) if o.source_id == IND]
    row = _row(db_path)
    assert row["state"] == "MISSING" and row["value"] is None


def test_fed_it_is_live_with_the_real_percentage_and_the_disclosure(db_path):
    wiring = build_wiring()
    with SqliteStore(db_path) as w:
        _seed(w, wiring, {IND: 64.0})
    row = _row(db_path)
    assert row["state"] == "LIVE" and row["value"] == pytest.approx(64.0) and row["dials"] == ["equity_crash"]
    assert row["window_days"] == 7.0 and row["unit"] == "percent_of_sample_above_200dma"
    assert "PROVISIONAL, SAMPLE-DEFINED" in row["why"] and "NOT the S&P 500" in row["why"] and "50/50 components fresh" in row["why"]


def test_the_figure_moves_the_equity_dial_through_the_placeholder_band_and_not_the_monetary_dial(db_path, tmp_path):
    wiring = build_wiring()
    dials = {}
    for figure in (70.0, 50.0, 30.0, 10.0):
        path = str(tmp_path / f"{figure}.sqlite")
        values = CALM | {IND: figure}
        with SqliteStore(path) as w:
            _seed(w, wiring, values)
        dials[figure] = {d["dial_id"]: d for d in _state(path)["dials"]}
        eq = dials[figure]["equity_crash"]
        assert IND in eq["inputs_used"]
        assert eq["value"] == pytest.approx(_expected("equity_crash", values))  # independent re-derivation
    eq = [dials[f]["equity_crash"]["value"] for f in (70.0, 50.0, 30.0, 10.0)]
    assert eq[0] < eq[1] < eq[2] and eq[2] == pytest.approx(eq[3])  # linear between calm and stress, clamped beyond
    assert len({dials[f]["monetary_debasement"]["value"] for f in dials}) == 1
    assert IND not in dials[70.0]["monetary_debasement"]["inputs_used"]


def test_thirty_fresh_names_is_live_and_twenty_nine_shows_no_number_and_is_out_of_the_dial(db_path, tmp_path):
    wiring = build_wiring()
    parts = wiring.derived_for[IND]
    for fresh, expect in ((30, "LIVE"), (29, "UNAVAILABLE")):
        path = str(tmp_path / f"{fresh}.sqlite")
        with SqliteStore(path) as w:
            _seed(w, wiring, CALM, skip=(IND,))
            for sid, payload in _breadth_components(parts, 70.0, "2026-10-10", absent=set(range(fresh, 50))).items():
                _put(w, sid, payload, "2026-10-10T00:00:00Z")
        row = _row(path)
        if expect == "LIVE":
            assert row["state"] == "LIVE" and row["value"] is not None and "30/50 components fresh" in row["why"]
        else:
            assert row["state"] == "MISSING" and row["value"] is None and "only 29/50" in row["why"]
            eq = next(d for d in _state(path)["dials"] if d["dial_id"] == "equity_crash")
            assert IND not in eq["inputs_used"]  # absence is absence, never a calm default


def test_a_week_old_sample_is_stale_not_live(db_path):
    with SqliteStore(db_path) as w:
        _seed(w, build_wiring(), {IND: 64.0}, age=timedelta(days=8))
    row = _row(db_path)
    assert row["state"] == "STALE" and row["value"] is None


def test_report_counts_only_fresh_components_toward_the_floor(db_path):
    parts = build_wiring().derived_for[IND]
    with SqliteStore(db_path) as w:
        for sid, payload in _breadth_components(parts, 70.0, "2026-10-10", absent=set(range(30, 50))).items():
            _put(w, sid, payload, "2026-10-10T00:00:00Z")
        state = next(s for s in indicator_states(w, NOW) if s["id"] == IND)
    assert state["state"] == "DERIVED" and "30/50" in state["detail"]


def test_the_page_renders_the_disclosure_and_the_number(db_path):
    with SqliteStore(db_path) as w:
        _seed(w, build_wiring(), CALM)
    page = gui_server.render_page(_state(db_path))
    assert IND in page and "SAMPLE-DEFINED" in page
