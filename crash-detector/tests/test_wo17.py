"""WO-1.7: gold_real_rate_cross (provisional correlation percentile), ism_manufacturing (regional z composite),
sloos_bank_lending (hand-entered NDFI leg). Absence stays absence; a blocked gold feed is never shown live."""

from __future__ import annotations

import json
import random
import statistics
from datetime import date, datetime, timedelta, timezone

import pytest

from crash_detector.engine.derivations import DerivationUnavailable, derive
from ingestion import adapters as A
from ingestion import manual
from ingestion.catalog import INGREDIENTS, MANUAL_SLOOS_NDFI
from ingestion.report import indicator_states
from ingestion.store import SqliteStore
from ingestion.wiring import build_wiring, observations_from_store
from gui.state import build_state

from test_wiring import NOW, _gold_rates_series, _independent_gold_figure, _put

DAY = "2026-10-10"


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "raw.sqlite")


def _payload(rows):
    return {"unit": "x", "observation_date": rows[-1][0], "value": rows[-1][1], "history": rows}


# --- gold_real_rate_cross ----------------------------------------------------------------- #


def test_correlation_percentile_matches_an_independent_stdlib_derivation():
    gold, real = _gold_rates_series(DAY)
    got = derive("gold_real_rate_cross", {"gold": [_payload(gold)], "real_rate": [_payload(real)]})
    assert got.value == pytest.approx(_independent_gold_figure(gold, real))
    assert 0.0 < got.value <= 100.0 and got.observation_date == DAY and got.unit == "percentile_of_rolling_corr"


def test_a_flip_toward_positive_correlation_reads_high_and_the_normal_negative_regime_reads_low():
    rng = random.Random(3)
    end = date.fromisoformat(DAY)
    dates = [(end - timedelta(days=799 - i)).isoformat() for i in range(800)]
    shocks = [rng.gauss(0, 1) for _ in dates]
    sign = [-1.0] * 700 + [1.0] * 100  # the last 100 days gold moves WITH real yields
    gold, real, g, r = [], [], 2000.0, 1.0
    for d, sh, sg in zip(dates, shocks, sign):
        g *= 1.0 + 0.005 * sg * sh
        r += 0.03 * sh
        gold.append([d, g]); real.append([d, r])
    flipped = derive("gold_real_rate_cross", {"gold": [_payload(gold)], "real_rate": [_payload(real)]})
    assert flipped.value > 95.0
    normal = derive("gold_real_rate_cross", {"gold": [_payload(gold[:700])], "real_rate": [_payload(real[:700])]})
    assert normal.value < 90.0 and normal.value < flipped.value  # -1 regime throughout: nowhere near the top


def test_correlation_refuses_short_history_misaligned_dates_and_bad_prices_without_a_number():
    gold, real = _gold_rates_series(DAY)
    with pytest.raises(DerivationUnavailable, match="shared dates"):
        derive("gold_real_rate_cross", {"gold": [_payload(gold[:30])], "real_rate": [_payload(real[:30])]})
    with pytest.raises(DerivationUnavailable, match="earlier correlations"):
        derive("gold_real_rate_cross", {"gold": [_payload(gold[-200:])], "real_rate": [_payload(real[-200:])]})
    shifted = [[(date.fromisoformat(d) + timedelta(days=1000)).isoformat(), v] for d, v in real]
    with pytest.raises(DerivationUnavailable, match="shared dates"):
        derive("gold_real_rate_cross", {"gold": [_payload(gold)], "real_rate": [_payload(shifted)]})
    bad = [list(r) for r in gold]; bad[400][1] = 0.0
    with pytest.raises(DerivationUnavailable, match="non-positive"):
        derive("gold_real_rate_cross", {"gold": [_payload(bad)], "real_rate": [_payload(real)]})
    flat = [[d, 1.0] for d, _ in real]
    with pytest.raises(DerivationUnavailable, match="zero variance"):
        derive("gold_real_rate_cross", {"gold": [_payload(gold)], "real_rate": [_payload(flat)]})
    with pytest.raises(DerivationUnavailable, match="no raw history"):
        derive("gold_real_rate_cross", {"gold": [{"unit": "x", "observation_date": DAY, "value": 1.0}], "real_rate": [_payload(real)]})


def test_lbma_history_is_raw_pm_else_am_pairs_and_off_by_default():
    pm = '[{"d":"2026-10-08","v":[4000.0,1,1]},{"d":"2026-10-09","v":[4010.0,1,1]}]'
    am = '[{"d":"2026-10-09","v":[4005.0,1,1]},{"d":"2026-10-10","v":[4020.0,1,1]}]'
    out = A.parse_lbma_gold(pm, am, "usd_per_oz", history=2)
    assert out["value"] == 4020.0 and out["history"] == [["2026-10-09", 4010.0], ["2026-10-10", 4020.0]]
    assert "history" not in A.parse_lbma_gold(pm, am, "usd_per_oz")


def test_gold_history_ingredients_are_new_ids_and_the_futures_close_does_not_feed_the_cross():
    by_id = {i.source_id: i for i in INGREDIENTS}
    for sid in ("lbma.gold_fix_usd.history", "fred.DFII10.history"):
        assert by_id[sid].serves == ("gold_real_rate_cross",) and by_id[sid].completes == "COMPONENT" and by_id[sid].history >= 2000
    assert "gold_real_rate_cross" not in by_id["yahoo.GC=F"].serves
    assert by_id["fred.DFII10"].serves == ("real_rate_10y_tips",) and by_id["fred.DFII10"].history == 0


def _fail_attempt(store, source_id, when):
    store._db.execute(
        "INSERT INTO raw_observation (source_id, adapter_id, collector_run_id, attempt_number, requested_utc, observed_utc,"
        " outcome, http_status, error_class) VALUES (?,?,?,?,?,?,?,?,?)",
        (source_id, "cd.ingest.lbma_gold_fix.v1", "r", 1, when, when, "FETCH_FAILED", 403, "HTTP_ERROR"))


def test_with_lbma_blocked_gold_real_rate_cross_is_feed_failing_with_no_value_and_no_futures_substitute(db_path):
    """The honest-inheritance case: LBMA answers 403, TIPS history is fine, Yahoo gold futures are fine."""
    _, real = _gold_rates_series(DAY)
    with SqliteStore(db_path) as w:
        _put(w, "fred.DFII10.history", _payload(real), DAY + "T00:00:00Z")
        _put(w, "yahoo.GC=F", {"unit": "usd_per_oz", "observation_date": DAY, "value": 4216.0}, DAY + "T00:00:00Z")
        _fail_attempt(w, "lbma.gold_fix_usd.history", DAY + "T06:00:00Z")
    with SqliteStore(db_path, read_only=True) as ro:
        row = next(i for i in build_state(ro, NOW)["indicators"] if i["id"] == "gold_real_rate_cross")
        wiring = build_wiring()
        assert "gold_real_rate_cross" not in {o.source_id for o in observations_from_store(ro, wiring, NOW)}
    assert row["state"] == "FEED_FAILING" and row["value"] is None
    assert "lbma.gold_fix_usd.history" in row["why"] and "LBMA" in row["why"]
    assert "PROVISIONAL" in row["why"] and "NOT-OWNER-RATIFIED" in row["why"]


# --- ism_manufacturing --------------------------------------------------------------------- #


def _survey(values, last_day):
    """Monthly rows ending at `last_day`, one calendar month apart going back."""
    year, month = int(last_day[:4]), int(last_day[5:7])
    dates = []
    for back in range(len(values) - 1, -1, -1):
        index = year * 12 + month - 1 - back
        dates.append(f"{index // 12}-{index % 12 + 1:02d}-01")
    return [[d, v] for d, v in zip(dates, values)]


def _three(values_each, last_day="2026-09-01"):
    return {role: [_payload(_survey(v, last_day))] for role, v in zip(("philadelphia", "new_york", "dallas"), values_each)}


def test_ism_composite_is_the_equal_weighted_mean_of_each_regions_own_z_score():
    rng = random.Random(11)
    series = [[rng.gauss(10 * k, 5 + k) for _ in range(300)] for k in range(3)]
    got = derive("ism_manufacturing", _three(series))
    expected = statistics.mean((s[-1] - statistics.fmean(s)) / statistics.pstdev(s) for s in series)
    assert got.value == pytest.approx(expected) and got.observation_date == "2026-09-01"
    assert got.unit == "regional_survey_z_composite"


def test_ism_uses_the_newest_month_all_regions_share_and_refuses_thin_or_flat_histories():
    rng = random.Random(5)
    a, b = [rng.gauss(0, 1) for _ in range(200)], [rng.gauss(0, 1) for _ in range(200)]
    inputs = _three([a, b, [rng.gauss(0, 1) for _ in range(200)]])
    inputs["dallas"] = [_payload(_survey([rng.gauss(0, 1) for _ in range(199)], "2026-08-01"))]  # Dallas has not reported Sep
    assert derive("ism_manufacturing", inputs).observation_date == "2026-08-01"
    with pytest.raises(DerivationUnavailable, match="at least 120"):
        derive("ism_manufacturing", _three([a[:50], b, b]))
    with pytest.raises(DerivationUnavailable, match="zero variance"):
        derive("ism_manufacturing", _three([[3.0] * 200, b, b]))
    no_overlap = _three([a, b, b])
    no_overlap["new_york"] = [_payload(_survey(b, "2000-01-01"))]  # ends 200 months before the others begin to overlap
    with pytest.raises(DerivationUnavailable, match="every regional survey"):
        derive("ism_manufacturing", no_overlap)


def test_ism_ingredients_are_the_three_verified_fred_series_and_none_of_richmond_or_kansas_city():
    refs = {i.ref for i in INGREDIENTS if "ism_manufacturing" in i.serves}
    assert refs == {"GACDFSA066MSFRBPHI", "GACDISA066MSFRBNY", "BACTSAMFRBDAL"}


# --- sloos_bank_lending / manual entry ------------------------------------------------------ #


def test_sloos_is_the_mean_of_both_legs_dated_by_the_older_and_needs_both():
    leg = lambda day, v: [{"unit": "x", "observation_date": day, "value": v}]  # noqa: E731
    got = derive("sloos_bank_lending", {"commercial_industrial": leg("2026-07-01", 10.0), "ndfi": leg("2026-04-01", 30.0)})
    assert got.value == 20.0 and got.observation_date == "2026-04-01"
    with pytest.raises(DerivationUnavailable):
        derive("sloos_bank_lending", {"commercial_industrial": leg("2026-07-01", 10.0), "ndfi": []})
    with pytest.raises(DerivationUnavailable, match="not a net percentage"):
        derive("sloos_bank_lending", {"commercial_industrial": leg("2026-07-01", 10.0), "ndfi": leg("2026-07-01", 250.0)})


@pytest.mark.parametrize("survey_date,value", [("2026-07-02", 5.0), ("2026-08-01", 5.0), ("2026-13-01", 5.0), ("junk", 5.0),
                                                ("2027-01-01", 5.0), ("2026-07-01", 100.5), ("2026-07-01", float("nan")),
                                                ("2026-07-01", float("inf"))])
def test_manual_entry_refuses_bad_dates_future_dates_and_non_percentages(survey_date, value, db_path):
    with SqliteStore(db_path) as store, pytest.raises(manual.EntryRefused):
        manual.record(store, survey_date, value, NOW)
    with SqliteStore(db_path, read_only=True) as ro:
        assert ro.latest_reading(MANUAL_SLOOS_NDFI) is None  # nothing recorded


def test_manual_cli_previews_by_default_records_with_confirm_and_refuses_a_second_value_for_a_survey(db_path, capsys):
    base = ["--db", db_path, "sloos-ndfi", "--survey-date", "2026-07-01", "--value", "12.5"]
    assert manual.main(base) == 0 and "PREVIEW ONLY" in capsys.readouterr().out
    with SqliteStore(db_path) as s:
        assert s.latest_reading(MANUAL_SLOOS_NDFI) is None
    assert manual.main(base + ["--confirm"]) == 0 and "RECORDED" in capsys.readouterr().out
    with SqliteStore(db_path) as s:
        reading = s.latest_reading(MANUAL_SLOOS_NDFI)
        assert reading["payload"] == {"unit": "net_percent_tightening", "observation_date": "2026-07-01", "value": 12.5}
        assert reading["source_as_of_utc"].startswith("2026-07-01")
        assert s.last_attempt(MANUAL_SLOOS_NDFI)[1] == "OK"
    again = ["--db", db_path, "sloos-ndfi", "--survey-date", "2026-07-01", "--value", "99", "--confirm"]
    assert manual.main(again) == 2 and "already has a recorded value" in capsys.readouterr().err
    assert manual.main(["--db", db_path, "list"]) == 0 and "2026-07-01  12.5" in capsys.readouterr().out


def _sloos_state(db_path, now):
    with SqliteStore(db_path, read_only=True) as ro:
        return next(i for i in build_state(ro, now)["indicators"] if i["id"] == "sloos_bank_lending")


def test_a_hand_entered_value_is_treated_like_a_fetched_one_missing_then_live_then_ages_out(db_path):
    with SqliteStore(db_path) as w:  # the automatic C&I leg, fetched (here: seeded) for the same survey
        _put(w, "fred.DRTSCILM", {"unit": "net_percent_tightening", "observation_date": "2026-07-01", "value": 6.0},
             "2026-07-01T00:00:00Z")
    row = _sloos_state(db_path, NOW)
    assert row["state"] == "MISSING" and row["value"] is None and "AWAITING MANUAL ENTRY" in row["why"]
    with SqliteStore(db_path) as w:
        manual.record(w, "2026-07-01", 18.0, NOW)
    live = _sloos_state(db_path, NOW)  # 2026-10-11: 102 days after the survey
    assert live["state"] == "LIVE" and live["value"] == 12.0 and live["dials"] == ["equity_crash"]
    assert live["window_days"] == 120.0 and live["as_of_utc"].startswith("2026-07-01")
    later = NOW + timedelta(days=19)  # 121 days: past the 120-day window
    gone = _sloos_state(db_path, later)
    assert gone["state"] == "STALE" and gone["value"] is None
    with SqliteStore(db_path, read_only=True) as ro:
        states = {s["id"]: s["state"] for s in indicator_states(ro, later)}
    assert states["sloos_bank_lending"] == "STALE"


def test_the_collector_loop_never_tries_to_poll_the_manual_source(db_path):
    from ingestion.run import run_once

    with SqliteStore(db_path) as store:
        summary = run_once(store, only=(MANUAL_SLOOS_NDFI,))
    assert summary == []  # skipped, not fetched, not a failure
    with SqliteStore(db_path, read_only=True) as ro:
        assert ro.latest_reading(MANUAL_SLOOS_NDFI) is None and ro.last_attempt(MANUAL_SLOOS_NDFI) is None
