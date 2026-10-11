"""WO-1.3: real ingestion-store data reaches the two dials; absence never becomes calm."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from crash_detector.dials.reading import Degraded, Unknown, Value
from ingestion.store import SqliteStore
from ingestion.wiring import (
    DIALS,
    SCALING_JSON,
    POLARITY,
    _rows,
    build_wiring,
    evaluate_from_store,
    observations_from_store,
)

NOW = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)

#: Mid-band, fresh values for every live indicator (value, per ingredient unit).
CALM = {
    "hy_oas": 3.0, "yield_curve_10y3m": 1.5, "yield_curve_10y2y": 1.0, "ig_oas": 0.9,
    "jobless_claims_4w": 200000.0, "sahm_rule": 0.0, "michigan_sentiment": 90.0,
    "cboe_skew": 120.0, "vix_level": 14.0, "chicago_fed_nfci": -0.5, "real_rate_10y_tips": 0.0,
    "fed_funds_rate": 2.0, "m2_yoy": 6.0, "broad_dollar": 125.0, "breakeven_5y": 2.0,
    "cpi_yoy": 2.0, "core_pce_yoy": 2.0,
    # WO-1.5 DERIVED: these are the FIGURES the engine must compute; _seed writes components that yield them.
    "breadth_rsp_spy": 0.29, "credit_stress_hyg_lqd": 0.80, "copper_gold": 2.0,
    "vix_term_structure": 0.85, "spx_vs_200dma": 5.0, "shiller_cape": 50.0,
    # WO-1.6: buffett_indicator and fiscal_dominance are DERIVED (figures the engine must compute); gold_spot is direct.
    "buffett_indicator": 100.0, "fiscal_dominance": 0.0, "gold_spot": 2000.0,
}


def _fiscal_components(parts, fired, date_text):
    """WALCL / core-CPI level histories whose discriminator is `fired` or not, built independently of the engine.

    Fired: the balance sheet is +25% on a year ago and core CPI is +10% in 3 months (~46% annualised).
    Not fired: both flat.
    """
    wal = [[f"2025-{1 + i // 4:02d}-{1 + 7 * (i % 4):02d}", 100.0] for i in range(48)]
    wal.append([date_text, 125.0 if fired else 100.0])
    month, year = int(date_text[5:7]), int(date_text[:4])
    earlier = month - 3 if month > 3 else month + 9
    core = [[f"{year if month > 3 else year - 1}-{earlier:02d}-01", 100.0],
            [date_text[:7] + "-01", 110.0 if fired else 100.0]]
    return {parts[0].source_id: {"unit": "x", "observation_date": date_text, "value": wal[-1][1], "history": wal},
            parts[1].source_id: {"unit": "x", "observation_date": core[-1][0], "value": core[-1][1], "history": core}}


def _derived_components(wiring, indicator, figure, date_text, vix=14.0):
    """{ingredient source_id: payload} whose engine derivation is `figure`, built independently of the engine."""
    parts = wiring.derived_for[indicator]
    unit = "x"
    if indicator == "fiscal_dominance":
        return _fiscal_components(parts, figure >= 0.5, date_text)
    if indicator == "spx_vs_200dma":
        r = 1.0 + figure / 100.0
        latest = 19900.0 * r / (200.0 - r)  # 199 closes of 100 + this one: latest / average - 1 == figure %
        history = [[f"2025-{1 + i // 28:02d}-{1 + i % 28:02d}", 100.0] for i in range(259)] + [[date_text, latest]]
        return {parts[0].source_id: {"unit": unit, "observation_date": date_text, "value": latest, "history": history}}
    if indicator == "shiller_cape":
        j = round(figure * 10) - 1  # history 1..999 => percentile of j+0.5 is 100*(1+j)/1000
        history = [[f"{1800 + i // 12:04d}-{1 + i % 12:02d}-01", float(i + 1)] for i in range(999)]
        return {parts[0].source_id: {"unit": unit, "observation_date": date_text, "value": j + 0.5, "history": history}}
    if indicator == "vix_term_structure":
        # cboe.VIX is SHARED with vix_level (its direct seed writes the numerator); only VIX3M is written here.
        return {parts[1].source_id: {"unit": unit, "observation_date": date_text, "value": vix / figure}}
    scale = {"copper_gold": 1000.0, "buffett_indicator": 0.1}.get(indicator, 1.0)
    return {parts[0].source_id: {"unit": unit, "observation_date": date_text, "value": figure / scale * 100.0},
            parts[1].source_id: {"unit": unit, "observation_date": date_text, "value": 100.0}}


def _put(store, source_id, payload, as_of):
    cur = store._db.execute(
        "INSERT INTO raw_observation (source_id, adapter_id, collector_run_id, attempt_number,"
        " requested_utc, observed_utc, outcome, source_as_of_utc) VALUES (?,?,?,?,?,?,?,?)",
        (source_id, "t", "r", 1, as_of, as_of, "OK", as_of))
    store._db.execute(
        "INSERT INTO raw_reading (source_id, source_as_of_utc, payload, observation_id, admitted_utc)"
        " VALUES (?,?,?,?,?)", (source_id, as_of, json.dumps(payload), cur.lastrowid, as_of))


def _seed(store, wiring, values, *, age=timedelta(days=1), skip=()):
    for indicator, value in values.items():
        if indicator in skip:
            continue
        if indicator in wiring.derived_for:
            day = (NOW - age).date().isoformat()
            for source_id, payload in _derived_components(wiring, indicator, value, day,
                                                              vix=values.get("vix_level", CALM["vix_level"])).items():
                _put(store, source_id, payload, day + "T00:00:00Z")
            continue
        ing = wiring.ingredient_for[indicator]
        as_of = (NOW - age).strftime("%Y-%m-%dT%H:%M:%SZ")
        cur = store._db.execute(
            "INSERT INTO raw_observation (source_id, adapter_id, collector_run_id, attempt_number,"
            " requested_utc, observed_utc, outcome, source_as_of_utc) VALUES (?,?,?,?,?,?,?,?)",
            (ing.source_id, "t", "r", 1, as_of, as_of, "OK", as_of),
        )
        store._db.execute(
            "INSERT INTO raw_reading (source_id, source_as_of_utc, payload, observation_id, admitted_utc)"
            " VALUES (?,?,?,?,?)",
            (ing.source_id, as_of, json.dumps({"unit": ing.unit, "observation_date": as_of[:10], "value": value}),
            cur.lastrowid, as_of),
        )


def _expected(dial, values):
    """Independent re-derivation: tier weight x clamped linear band, weighted mean."""
    scaling = json.loads(SCALING_JSON.read_text())[dial]
    tier = {r["id"]: r["tier"] for r in _rows()}
    num = den = 0.0
    for i, band in scaling.items():
        w = {1: 3.0, 2: 2.0, 3: 1.0}[tier[i]]
        x = (values[i] - band["calm"]) / (band["stress"] - band["calm"])
        num += w * min(1.0, max(0.0, x))
        den += w
    return num / den


@pytest.fixture
def wiring():
    return build_wiring()


@pytest.fixture
def store(tmp_path):
    with SqliteStore(str(tmp_path / "raw.sqlite")) as s:
        yield s


def _mag(reading):
    # The magnitude is sealed by design (CD-PL-F54); the explainable route is the named
    # contributions the dial carries, from which the weighted mean is recomputed.
    c = reading.value.contributions
    return sum(x.weight * x.contribution for x in c) / sum(x.weight for x in c)


def test_only_whole_quantity_ingredients_are_live_and_the_rest_is_pending_with_a_reason(wiring):
    assert len(wiring.ingredient_for) == 18  # + gold_spot (WO-1.6)
    assert len(wiring.derived_for) == 8  # + buffett_indicator, fiscal_dominance (WO-1.6)
    assert len(wiring.pending) == 4
    assert wiring.live_ids | set(wiring.pending) == {r["id"] for r in _rows()}
    assert not wiring.live_ids & set(wiring.pending)
    assert not set(wiring.ingredient_for) & set(wiring.derived_for)
    for blocked in ("gold_real_rate_cross", "sloos_bank_lending"):
        assert blocked in wiring.pending and wiring.pending[blocked]
    assert wiring.pending["gold_real_rate_cross"].startswith("BLOCKED on definition")


def test_scaling_band_order_agrees_with_the_ratified_polarity_for_every_dial(wiring):
    scaling = json.loads(SCALING_JSON.read_text())
    for row in _rows():
        if row["id"] not in wiring.live_ids:
            continue
        dials = row["dial"] if isinstance(row["dial"], list) else [row["dial"]]
        for dial in dials:
            if (row["id"], dial) in wiring.held:
                assert row["id"] not in scaling[dial], "a HELD binding must carry no band"
                continue
            pol = row["polarity"][dial] if isinstance(row["polarity"], dict) else row["polarity"]
            band = scaling[dial][row["id"]]
            rising_is_riskier = band["stress"] > band["calm"]
            assert rising_is_riskier == (POLARITY[pol].name == "RISING_MEANS_MORE_RISK"), (dial, row["id"])
    # and nothing is scaled that is not live, nor bound to a dial it does not serve
    for dial in DIALS:
        for indicator in scaling[dial]:
            assert indicator in wiring.live_ids and (indicator, dial) not in wiring.held


def test_every_input_present_gives_a_value_on_both_dials_never_blended(wiring, store):
    _seed(store, wiring, CALM)
    dials = evaluate_from_store(store, NOW, wiring)
    assert type(dials.equity) is Value and type(dials.monetary) is Value
    assert _mag(dials.equity) == pytest.approx(_expected("equity_crash", CALM))
    assert _mag(dials.monetary) == pytest.approx(_expected("monetary_debasement", CALM))
    assert _mag(dials.equity) != _mag(dials.monetary)  # two readings, not one blended number


def test_stress_in_one_dial_moves_only_that_dial(wiring, store):
    stressed = dict(CALM, hy_oas=6.0, yield_curve_10y3m=-1.0, yield_curve_10y2y=-0.75)
    _seed(store, wiring, stressed)
    dials = evaluate_from_store(store, NOW, wiring)
    assert _mag(dials.equity) == pytest.approx(_expected("equity_crash", stressed))
    # Margin derived from structure, not a hard-coded constant: three tier-1 inputs (weight 3
    # each) saturate at 1.0 against the dial's total weight, so each further calm input dilutes
    # the score (0.346 at 17 live inputs, 0.231 at 23). Require at least half that ceiling.
    tier = {r["id"]: r["tier"] for r in _rows()}
    total = sum({1: 3.0, 2: 2.0, 3: 1.0}[tier[i]]
                for i in json.loads(SCALING_JSON.read_text())["equity_crash"])
    assert _mag(dials.equity) > _expected("equity_crash", CALM) + 0.5 * 9.0 / total
    assert _mag(dials.monetary) == pytest.approx(_expected("monetary_debasement", CALM))


def test_a_missing_required_input_is_unknown_never_calm(wiring, store):
    _seed(store, wiring, CALM, skip=("hy_oas",))
    dials = evaluate_from_store(store, NOW, wiring)
    assert type(dials.equity) is Unknown and "hy_oas" in dials.equity.missing_inputs
    assert type(dials.monetary) is Value  # the other dial is untouched


def test_a_missing_contributing_input_is_degraded_and_names_it(wiring, store):
    _seed(store, wiring, CALM, skip=("cboe_skew",))
    dials = evaluate_from_store(store, NOW, wiring)
    assert type(dials.equity) is Degraded and dials.equity.missing_inputs == ("cboe_skew",)


def test_a_stale_required_input_is_unknown_on_its_own_cadence_window(wiring, store):
    # hy_oas is daily: window 4 days. Its only print is 10 days old; everything else is fresh.
    _seed(store, wiring, {k: v for k, v in CALM.items() if k != "hy_oas"})
    _seed(store, wiring, {"hy_oas": 3.0}, age=timedelta(days=10))
    dials = evaluate_from_store(store, NOW, wiring)
    assert type(dials.equity) is Unknown and "hy_oas" in dials.equity.missing_inputs


def test_a_slow_series_is_not_stale_at_the_liveness_ceiling(wiring):
    # a 20-day-old monthly print is current for a 45-day window (it would fail the 900 s ceiling)
    with SqliteStore(":memory:") as s:
        _seed(s, wiring, CALM)
        _seed(s, wiring, {"cpi_yoy": 3.0}, age=timedelta(days=20))
        obs = {o.source_id for o in observations_from_store(s, wiring, NOW)}
        assert "cpi_yoy" in obs


def test_an_empty_store_is_unknown_on_both_dials(wiring, store):
    dials = evaluate_from_store(store, NOW, wiring)
    assert type(dials.equity) is Unknown and type(dials.monetary) is Unknown


def test_a_non_numeric_stored_value_is_absence_not_zero(wiring, store):
    _seed(store, wiring, dict(CALM, hy_oas="."))
    assert "hy_oas" not in {o.source_id for o in observations_from_store(store, wiring, NOW)}
    assert type(evaluate_from_store(store, NOW, wiring).equity) is Unknown


def test_pending_indicators_never_produce_an_observation(wiring, store):
    _seed(store, wiring, CALM)
    produced = {o.source_id for o in observations_from_store(store, wiring, NOW)}
    assert not produced & set(wiring.pending)


def test_both_dial_indicators_use_each_dials_own_band(wiring, store):
    # real_rate_10y_tips = 2.5: max stress for equity (band 0..2.5), min for monetary (band 2..-1)
    _seed(store, wiring, dict(CALM, real_rate_10y_tips=2.5))
    dials = evaluate_from_store(store, NOW, wiring)
    values = dict(CALM, real_rate_10y_tips=2.5)
    assert _mag(dials.equity) == pytest.approx(_expected("equity_crash", values))
    assert _mag(dials.monetary) == pytest.approx(_expected("monetary_debasement", values))
    assert _mag(dials.equity) > _expected("equity_crash", CALM)
    assert _mag(dials.monetary) < _expected("monetary_debasement", CALM)


# --- WO-1.3 Auditor reconciliation (F1, F3) -------------------------------------------------- #

def test_coverage_discloses_that_a_fully_live_dial_is_built_from_part_of_the_ratified_weight(wiring):
    from ingestion.wiring import coverage
    cov = coverage(wiring)
    for dial in DIALS:
        c = cov[dial]
        assert 0.0 < c["fraction"] < 1.0, "pending rows exist, so no dial may claim full coverage"
        assert c["wired_weight"] < c["nominal_weight"] and c["pending"]
        assert not set(c["pending"]) & set(wiring.ingredient_for)
    assert "gold_real_rate_cross" in cov["monetary_debasement"]["pending"]


def test_relevance_window_is_inclusive_at_its_limit_and_refuses_beyond_and_the_future():
    from crash_detector.staleness import RelevanceWindow
    w = RelevanceWindow(seconds=345600.0)
    assert w.covers(345600.0) and w.covers(0.0)
    assert not w.covers(345600.001) and not w.covers(-1.0)
    assert not w.covers(float("nan")) and not w.covers(float("inf"))
    assert RelevanceWindow(seconds=10_368_000.0).covers(10_368_000.0)
    with pytest.raises(Exception):
        RelevanceWindow(seconds=10_368_001.0)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), True, "3.0", None])
def test_a_non_finite_or_non_number_stored_value_yields_no_observation(wiring, store, bad):
    _seed(store, wiring, {"hy_oas": 3.0})
    ing = wiring.ingredient_for["vix_level"]
    as_of = (NOW - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Simulates a corrupted stored payload. SQLite < 3.42 refuses NaN/Infinity literals through the
    # table's json_type CHECK, so the CHECK is bypassed for this one insert only.
    store._db.execute("PRAGMA ignore_check_constraints=ON")
    cur = store._db.execute(
        "INSERT INTO raw_observation (source_id, adapter_id, collector_run_id, attempt_number,"
        " requested_utc, observed_utc, outcome, source_as_of_utc) VALUES (?,?,?,?,?,?,?,?)",
        (ing.source_id, "t", "r", 1, as_of, as_of, "OK", as_of))
    store._db.execute(
        "INSERT INTO raw_reading (source_id, source_as_of_utc, payload, observation_id, admitted_utc)"
        " VALUES (?,?,?,?,?)",
        (ing.source_id, as_of, json.dumps({"unit": "x", "value": bad}, allow_nan=True), cur.lastrowid, as_of))
    store._db.execute("PRAGMA ignore_check_constraints=OFF")
    ids = {o.source_id for o in observations_from_store(store, wiring, NOW)}
    assert "hy_oas" in ids and "vix_level" not in ids
