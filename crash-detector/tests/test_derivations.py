"""Direct tests of the engine's derivations (WO-1.5): the figure is computed, and absence is never a number."""

import pytest

from crash_detector.engine.derivations import DerivationUnavailable, derive


def _p(date, value, **extra):
    return {"unit": "x", "observation_date": date, "value": value, **extra}


def test_ratio_uses_the_newest_date_both_components_share():
    out = derive("breadth_rsp_spy", {"numerator": [_p("2026-10-09", 3.0), _p("2026-10-08", 9.0)],
                                     "denominator": [_p("2026-10-08", 3.0)]})
    assert (out.value, out.observation_date) == (3.0, "2026-10-08")


def test_copper_gold_is_scaled_x1000():
    out = derive("copper_gold", {"numerator": [_p("2026-10-09", 5.0)], "denominator": [_p("2026-10-09", 2500.0)]})
    assert out.value == pytest.approx(2.0)


def test_ratio_with_no_shared_date_is_refused_not_defaulted():
    with pytest.raises(DerivationUnavailable):
        derive("vix_term_structure", {"numerator": [_p("2026-10-09", 1.0)], "denominator": [_p("2026-10-08", 1.0)]})


def test_a_short_200_day_history_is_refused_not_averaged_short():
    history = [[f"2026-01-{d:02d}", 100.0] for d in range(1, 29)]
    with pytest.raises(DerivationUnavailable, match="28 closes"):
        derive("spx_vs_200dma", {"series": [_p("2026-01-28", 100.0, history=history)]})


def test_a_truncated_percentile_history_is_refused():
    history = [[f"{1900 + i // 12}-{1 + i % 12:02d}-01", float(i)] for i in range(100)]
    with pytest.raises(DerivationUnavailable):
        derive("shiller_cape", {"series": [_p("1908-05-01", 99.0, history=history)]})


def test_a_non_derived_indicator_and_wrong_roles_are_errors():
    with pytest.raises(ValueError):
        derive("hy_oas", {"series": [_p("2026-10-09", 1.0)]})
    with pytest.raises(ValueError):
        derive("spx_vs_200dma", {"numerator": [_p("2026-10-09", 1.0)]})


# --- WO-1.6: buffett_indicator ------------------------------------------------------------------ #


def test_buffett_is_the_z1_ratio_in_percent_reproducing_the_legacy_figure():
    # FRED 2026-01-01: NCBEILQ027S 70,018,384 ($M), GDP 31,906.274 ($B) -> 219.4% (legacy engine printed ~218%).
    out = derive("buffett_indicator", {"numerator": [_p("2026-01-01", 70018384.0)],
                                       "denominator": [_p("2026-01-01", 31906.274)]})
    assert out.value == pytest.approx(70018384.0 / (31906.274 * 1000.0) * 100.0)
    assert 219.0 < out.value < 220.0 and out.unit == "percent_of_gdp"


def test_buffett_never_pairs_two_different_quarters():
    out = derive("buffett_indicator", {"numerator": [_p("2026-04-01", 83050847.0), _p("2026-01-01", 70018384.0)],
                                       "denominator": [_p("2026-01-01", 31906.274)]})
    assert out.observation_date == "2026-01-01"  # the newest quarter BOTH have; GDP has not printed 2026-04-01 here
    with pytest.raises(DerivationUnavailable):
        derive("buffett_indicator", {"numerator": [_p("2026-04-01", 1.0)], "denominator": [_p("2026-01-01", 1.0)]})


# --- WO-1.6: monetisation_flag ------------------------------------------------------------------- #


def _walcl(latest, year_ago, latest_date="2026-10-07"):
    return {"balance_sheet": [_p(latest_date, latest, history=[
        ["2025-09-24", 1.0], ["2025-10-01", year_ago], ["2025-10-08", 50.0], [latest_date, latest]])]}


def _core(factor, latest_date="2026-08-01"):
    return {"core_price_index": [_p(latest_date, 100.0 * factor, history=[
        ["2026-04-01", 99.0], ["2026-05-01", 99.5], ["2026-06-01", 99.8], ["2026-07-01", 100.0],
        [latest_date, 100.0 * factor]])]}


def _fiscal(walcl_growth, core_3m_ratio):
    # the 3-months-earlier level of the core series is 2026-05-01 (99.5) for a 2026-08-01 latest
    walcl = _walcl(100.0 * (1.0 + walcl_growth), 100.0)
    core = {"core_price_index": [_p("2026-08-01", 99.5 * core_3m_ratio, history=[
        ["2026-04-01", 99.0], ["2026-05-01", 99.5], ["2026-06-01", 99.8], ["2026-07-01", 100.0],
        ["2026-08-01", 99.5 * core_3m_ratio]])]}
    return derive("monetisation_flag", {**walcl, **core})


def test_fiscal_fires_only_when_both_legs_are_over_their_band():
    ratio_over = 1.0 + 0.0105  # (1.0105)**4 - 1 = 4.26% annualised
    assert _fiscal(0.12, ratio_over).value == 1.0
    assert _fiscal(0.12, 1.0).value == 0.0, "balance-sheet growth alone must never fire (2008)"
    assert _fiscal(0.0, ratio_over).value == 0.0, "inflation alone must never fire"
    assert _fiscal(-0.05, ratio_over).value == 0.0, "QT with high CPI must not fire (2022)"
    assert _fiscal(0.0, 1.0).value == 0.0


def test_fiscal_bands_are_inclusive_at_the_legacy_locked_values():
    just_over = (1.04) ** 0.25  # exactly 4.0% annualised; float rounding may land either side, so step off it
    assert _fiscal(0.10, just_over * 1.0001).value == 1.0
    assert _fiscal(0.0999, just_over * 1.0001).value == 0.0
    assert _fiscal(0.10, just_over * 0.9999).value == 0.0


def test_fiscal_reading_is_dated_by_its_older_leg():
    out = _fiscal(0.12, 1.0105)
    assert out.observation_date == "2026-08-01" and out.unit == "fired_flag"  # CPI (Aug) older than WALCL (Oct 7)


def test_fiscal_refuses_a_missing_month_instead_of_bridging_it():
    walcl = _walcl(120.0, 100.0)
    core = {"core_price_index": [_p("2026-08-01", 103.0, history=[
        ["2026-03-01", 99.0], ["2026-04-01", 99.5], ["2026-06-01", 99.8], ["2026-08-01", 103.0]])]}
    with pytest.raises(DerivationUnavailable, match="2026-05-01"):
        derive("monetisation_flag", {**walcl, **core})


def test_fiscal_refuses_a_balance_sheet_history_too_short_for_the_year():
    walcl = {"balance_sheet": [_p("2026-10-07", 120.0, history=[["2026-09-02", 100.0], ["2026-10-07", 120.0]])]}
    with pytest.raises(DerivationUnavailable, match="365 days"):
        derive("monetisation_flag", {**walcl, **_core(1.0105)})


@pytest.mark.parametrize("bad", [None, "x", float("nan"), True])
def test_fiscal_a_non_number_level_is_absence_not_zero(bad):
    walcl = {"balance_sheet": [_p("2026-10-07", 120.0, history=[["2025-10-01", bad], ["2026-10-07", 120.0]])]}
    with pytest.raises(DerivationUnavailable):
        derive("monetisation_flag", {**walcl, **_core(1.0105)})


def test_fiscal_a_payload_without_history_is_refused():
    with pytest.raises(DerivationUnavailable, match="history"):
        derive("monetisation_flag", {"balance_sheet": [_p("2026-10-07", 120.0)], **_core(1.0105)})
