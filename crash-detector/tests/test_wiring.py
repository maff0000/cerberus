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
}


def _seed(store, wiring, values, *, age=timedelta(days=1), skip=()):
    for indicator, value in values.items():
        if indicator in skip:
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
            (ing.source_id, as_of, json.dumps({"unit": ing.unit, "value": value}), cur.lastrowid, as_of),
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
    assert len(wiring.ingredient_for) == 17
    assert len(wiring.pending) == 13
    assert set(wiring.ingredient_for) | set(wiring.pending) == {r["id"] for r in _rows()}
    assert not set(wiring.ingredient_for) & set(wiring.pending)
    for derived in ("vix_term_structure", "gold_real_rate_cross", "shiller_cape", "sloos_bank_lending"):
        assert derived in wiring.pending and wiring.pending[derived]


def test_scaling_band_order_agrees_with_the_ratified_polarity_for_every_dial(wiring):
    scaling = json.loads(SCALING_JSON.read_text())
    for row in _rows():
        if row["id"] not in wiring.ingredient_for:
            continue
        dials = row["dial"] if isinstance(row["dial"], list) else [row["dial"]]
        for dial in dials:
            pol = row["polarity"][dial] if isinstance(row["polarity"], dict) else row["polarity"]
            band = scaling[dial][row["id"]]
            rising_is_riskier = band["stress"] > band["calm"]
            assert rising_is_riskier == (POLARITY[pol].name == "RISING_MEANS_MORE_RISK"), (dial, row["id"])
    # and nothing is scaled that is not live, nor bound to a dial it does not serve
    for dial in DIALS:
        for indicator in scaling[dial]:
            assert indicator in wiring.ingredient_for


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
    assert _mag(dials.equity) > _expected("equity_crash", CALM) + 0.3
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
    assert "fiscal_dominance" in cov["monetary_debasement"]["pending"]


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
    cur = store._db.execute(
        "INSERT INTO raw_observation (source_id, adapter_id, collector_run_id, attempt_number,"
        " requested_utc, observed_utc, outcome, source_as_of_utc) VALUES (?,?,?,?,?,?,?,?)",
        (ing.source_id, "t", "r", 1, as_of, as_of, "OK", as_of))
    store._db.execute(
        "INSERT INTO raw_reading (source_id, source_as_of_utc, payload, observation_id, admitted_utc)"
        " VALUES (?,?,?,?,?)",
        (ing.source_id, as_of, json.dumps({"unit": "x", "value": bad}, allow_nan=True), cur.lastrowid, as_of))
    ids = {o.source_id for o in observations_from_store(store, wiring, NOW)}
    assert "hy_oas" in ids and "vix_level" not in ids
