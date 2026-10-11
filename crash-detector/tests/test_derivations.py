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
