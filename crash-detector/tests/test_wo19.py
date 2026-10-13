"""WO-1.9: daily-cadence staleness windows survive a routine holiday weekend, and still mean something.

The windows are DERIVED from a calendar model below, not tuned until today's blank went away. The model walks every
start date over several years and finds the longest stretch a healthy feed can leave its newest observation unpublished.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from crash_detector.dials.reading import Unknown
from ingestion.catalog import window_seconds
from ingestion.store import SqliteStore
from ingestion.wiring import _rows, build_wiring, evaluate_from_store
from test_wiring import CALM, NOW, _seed

DAY = 86400
FRED_DAILY_WINDOW = 8 * DAY      # business-day series published by FRED with a one-business-day lag
MARKET_DAILY_WINDOW = 7 * DAY    # market-day series dated on the trading day itself
FRED_CALENDAR_DAY_SERIES = {"fed_funds_rate"}   # DFF has a print for every calendar day; its 7-day window predates WO-1.9
FRED_BUSINESS_DAY = {"hy_oas", "ig_oas", "yield_curve_10y3m", "yield_curve_10y2y", "real_rate_10y_tips", "breakeven_5y"}
MARKET_DAILY = {"credit_stress_hyg_lqd", "breadth_rsp_spy", "cboe_skew", "vix_term_structure", "vix_level",
                "spx_vs_200dma", "copper_gold", "gold_spot", "private_credit_stress",
                "constituent_breadth_200dma"}


def _worst_gap_seconds(closed_days: set, publish_lag_business_days: int) -> float:
    """Longest age, in seconds, the NEWEST available observation reaches, observation dated 00:00 UTC (the as_of_for
    rule), while a healthy feed has simply not published the next one yet. Checked up to the end (23:59:59) of the day
    the next print lands. ``closed_days`` are non-trading dates; weekends are always closed."""
    def open_(d): return d.weekday() < 5 and d not in closed_days
    worst, start = 0.0, date(2026, 1, 1)
    for k in range(2 * 365):
        d = start + timedelta(days=k)
        if not open_(d):
            continue
        nxt = d + timedelta(days=1)
        while not open_(nxt):
            nxt += timedelta(days=1)
        landing, lag = nxt, publish_lag_business_days
        while lag:
            landing += timedelta(days=1)
            while not open_(landing):
                landing += timedelta(days=1)
            lag -= 1
        worst = max(worst, (datetime.combine(landing, datetime.max.time()) - datetime.combine(d, datetime.min.time())).total_seconds())
    return worst


# Fri holiday + weekend + Mon holiday is the pattern the WO calls real; add it explicitly to a plain year of holidays.
HOLIDAY_WEEKEND = {date(2026, 10, 9), date(2026, 10, 12)}


def test_the_realistic_worst_case_for_a_fred_business_day_series_is_just_under_seven_days():
    # last obs Thu 00:00; Fri + Mon closed; next obs Tue, published Wed; checked to Wed 23:59:59.
    gap = _worst_gap_seconds(HOLIDAY_WEEKEND, publish_lag_business_days=1)
    assert 6 * DAY < gap < 7 * DAY
    assert gap < FRED_DAILY_WINDOW and FRED_DAILY_WINDOW - gap > DAY - 1   # >= one full day of grace left over


def test_the_old_four_day_window_could_not_survive_even_an_ordinary_three_day_weekend():
    # Plain Friday obs, Monday holiday: Friday 00:00 -> Wednesday: 4 days is exceeded by Monday midnight already.
    assert _worst_gap_seconds({date(2026, 10, 12)}, publish_lag_business_days=1) > 4 * DAY
    assert _worst_gap_seconds(set(), publish_lag_business_days=1) > 4 * DAY - 1   # even a plain weekend sits on the line


def test_the_worst_case_for_a_market_series_dated_on_its_own_trading_day_is_under_six_days():
    gap = _worst_gap_seconds(HOLIDAY_WEEKEND, publish_lag_business_days=0)
    assert 5 * DAY < gap < 6 * DAY
    assert gap < MARKET_DAILY_WINDOW and MARKET_DAILY_WINDOW - gap > DAY - 1


def test_every_daily_cadence_row_declares_exactly_the_calibrated_window_and_none_is_unclassified():
    daily = {r["id"]: r for r in _rows() if r["cadence"] == "daily"}
    assert set(daily) == FRED_BUSINESS_DAY | MARKET_DAILY - {"private_credit_stress"} | FRED_CALENDAR_DAY_SERIES
    for ident in FRED_BUSINESS_DAY:
        assert daily[ident]["staleness_window_seconds"] == FRED_DAILY_WINDOW, ident
    for ident in MARKET_DAILY - {"private_credit_stress"}:
        assert daily[ident]["staleness_window_seconds"] == MARKET_DAILY_WINDOW, ident
    assert daily["fed_funds_rate"]["staleness_window_seconds"] == 7 * DAY


def test_private_credit_stress_a_daily_etf_price_follows_the_market_window():
    assert window_seconds("private_credit_stress", 10368000) == MARKET_DAILY_WINDOW


def test_the_windows_are_still_a_meaningful_freshness_check():
    # tighter than the 14-day weekly rows, and nowhere near the monthly ones
    weekly = {r["staleness_window_seconds"] for r in _rows() if r["cadence"] == "weekly"}
    for r in _rows():
        if r["cadence"] == "daily":
            w = window_seconds(r["id"], r["staleness_window_seconds"])
            assert w <= 8 * DAY < min(weekly)


def test_classification_is_untouched_by_the_calibration():
    # WO-1.9 changes windows only. The required set per dial is exactly what WO-1.3 wired, pinned here so a quiet
    # change to it (a separate design question, not this WO) fails loudly.
    w = build_wiring()
    equity, monetary = w.snapshot.spec_for("equity_crash"), w.snapshot.spec_for("monetary_debasement")
    assert sorted(equity.required_input_ids) == ["hy_oas", "yield_curve_10y2y", "yield_curve_10y3m"]
    assert sorted(monetary.required_input_ids) == ["breakeven_5y", "broad_dollar"]
    assert len(equity.contributing_input_ids) == 21 and len(monetary.contributing_input_ids) == 8


@pytest.fixture
def wiring():
    return build_wiring()


def _equity_with_hy_oas_aged(wiring, tmp_path, age):
    with SqliteStore(str(tmp_path / "x.sqlite")) as s:
        _seed(s, wiring, {k: v for k, v in CALM.items() if k != "hy_oas"})
        _seed(s, wiring, {"hy_oas": 3.0}, age=age)
        return evaluate_from_store(s, NOW, wiring).equity


def test_todays_case_hy_oas_dated_2026_10_08_is_fresh_at_columbus_day_noon(wiring, tmp_path):
    age = datetime(2026, 10, 12, 12, tzinfo=timezone.utc) - datetime(2026, 10, 8, tzinfo=timezone.utc)
    assert age == timedelta(days=4, hours=12) > timedelta(days=4)   # STALE under the old 4-day window
    assert type(_equity_with_hy_oas_aged(wiring, tmp_path, age)) is not Unknown


@pytest.mark.parametrize("ident", sorted(FRED_BUSINESS_DAY))
def test_a_fred_business_day_reading_is_fresh_just_inside_eight_days_and_stale_just_outside(wiring, ident):
    assert _is_usable(wiring, ident, FRED_DAILY_WINDOW - 1) is True
    assert _is_usable(wiring, ident, FRED_DAILY_WINDOW + 1) is False
    assert _is_usable(wiring, ident, 4 * DAY + 1) is True       # the old window's casualty


@pytest.mark.parametrize("ident", ["cboe_skew", "vix_level", "gold_spot"])
def test_a_direct_market_reading_is_fresh_just_inside_seven_days_and_stale_just_outside(wiring, ident):
    assert _is_usable(wiring, ident, MARKET_DAILY_WINDOW - 1) is True
    assert _is_usable(wiring, ident, MARKET_DAILY_WINDOW + 1) is False
    assert _is_usable(wiring, ident, 4 * DAY + 1) is True


def _is_usable(wiring, ident, age_seconds):
    """True when the indicator's reading survives the engine's relevance window at that age.

    A fresh dial with every other input current, and this one input aged: a required input that is stale blanks the
    dial (Unknown); a contributing one drops out of the dial's contributions. Both are observed, not assumed."""
    import tempfile
    with tempfile.TemporaryDirectory() as d, SqliteStore(d + "/x.sqlite") as s:
        _seed(s, wiring, {k: v for k, v in CALM.items() if k != ident})
        _seed(s, wiring, {ident: CALM[ident]}, age=timedelta(seconds=age_seconds))
        dials = evaluate_from_store(s, NOW, wiring)
    dial = dials.monetary if ident in ("gold_spot", "breakeven_5y") else dials.equity
    return ident not in (getattr(dial, "missing_inputs", ()) or ())
