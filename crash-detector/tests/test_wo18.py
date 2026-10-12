"""WO-1.8: private_credit_stress v1 = percent BIZD (dividend-adjusted) sits below its 252-day high. A market-price
PROXY for the ratified filing-based composite; absence stays absence; the disclosure travels with the indicator."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from crash_detector.engine.derivations import DRAWDOWN_WINDOW, DerivationUnavailable, derive
from gui import server as gui_server
from gui.state import build_state
from ingestion import adapters as A
from ingestion.catalog import INGREDIENTS, SUBSTITUTED_FEEDS, build_adapter
from ingestion.store import SqliteStore
from ingestion.wiring import build_wiring, observations_from_store

from test_wiring import CALM, NOW, _expected, _seed

DAY = "2026-10-10"


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "raw.sqlite")


def _dates(n, end=DAY):
    last = date.fromisoformat(end)
    return [(last - timedelta(days=n - 1 - i)).isoformat() for i in range(n)]


def _payload(closes, end=DAY):
    rows = [[d, c] for d, c in zip(_dates(len(closes), end), closes)]
    return {"unit": "usd", "observation_date": rows[-1][0], "value": rows[-1][1], "history": rows}


def _drawdown(closes):
    return derive("private_credit_stress", {"series": [_payload(closes)]})


# --- the derivation ---------------------------------------------------------------------------------------- #


def test_drawdown_matches_a_hand_computed_figure_and_is_dated_by_the_last_close():
    closes = [10.0] * 100 + [12.0] + [11.0] * 200 + [9.0]  # 302 closes; the high of the last 252 is 12
    got = _drawdown(closes)
    assert got.value == pytest.approx((1.0 - 9.0 / 12.0) * 100.0) == pytest.approx(25.0)
    assert got.observation_date == DAY and got.unit == "percent_below_trailing_high"


def test_a_new_high_reads_exactly_zero_and_the_figure_is_never_negative():
    assert _drawdown([float(i + 100) for i in range(300)]).value == 0.0
    assert _drawdown([100.0] * 300).value == 0.0
    assert _drawdown([100.0 + (i % 7) for i in range(300)]).value >= 0.0


def test_a_high_older_than_the_window_is_forgotten_but_one_inside_it_is_not():
    closes = [20.0] + [10.0] * (DRAWDOWN_WINDOW - 1) + [8.0]  # 253 closes: the 20 is the 253rd back from the end
    assert _drawdown(closes).value == pytest.approx(20.0)       # vs the high of 10, not 20
    inside = [20.0] + [10.0] * (DRAWDOWN_WINDOW - 2) + [8.0]    # 252 closes: the 20 is the oldest IN the window
    assert _drawdown(inside).value == pytest.approx(60.0)       # vs the high of 20


def test_the_construction_responds_to_its_inputs_a_crash_reads_far_higher_than_calm():
    calm = _drawdown([100.0 + 0.01 * i for i in range(300)]).value
    crash = _drawdown([100.0] * 280 + [100.0 - 2 * i for i in range(1, 21)]).value
    assert calm < 1.0 and crash == pytest.approx(40.0) and crash > 30 * calm + 1


def test_a_short_history_is_refused_with_its_count_never_measured_over_a_shorter_window():
    with pytest.raises(DerivationUnavailable, match="holds 251 closes"):
        _drawdown([100.0] * (DRAWDOWN_WINDOW - 1))
    assert _drawdown([100.0] * DRAWDOWN_WINDOW).value == 0.0  # exactly enough is enough


@pytest.mark.parametrize("mutate,match", [
    (lambda p: p.update(history=None), "no raw history"),
    (lambda p: p.pop("history"), "no raw history"),
    (lambda p: p.update(observation_date="2026-10-09"), "must be the same close"),
    (lambda p: p.update(value=1.0), "not the last close"),
    (lambda p: p.update(value=float("nan")), "not finite"),
    (lambda p: p["history"].__setitem__(5, ["junk", 1.0]), "not an ISO date|strictly increasing"),
    (lambda p: p["history"].__setitem__(5, [p["history"][6][0], 100.0]), "strictly increasing"),
    (lambda p: p["history"].__setitem__(5, [p["history"][5][0], float("inf")]), "not finite"),
    (lambda p: p["history"].__setitem__(-5, [p["history"][-5][0], 0.0]), "non-positive"),  # inside the window
    (lambda p: p["history"].__setitem__(5, [p["history"][5][0], True]), "not a plain number"),
])
def test_a_malformed_stored_reading_is_unavailable_never_a_number(mutate, match):
    payload = _payload([100.0] * 300)
    mutate(payload)
    with pytest.raises(DerivationUnavailable, match=match):
        derive("private_credit_stress", {"series": [payload]})


def test_no_stored_reading_at_all_is_unavailable():
    with pytest.raises(DerivationUnavailable, match="no stored reading"):
        derive("private_credit_stress", {"series": []})


# --- the adjusted-close ingestion --------------------------------------------------------------------------- #

_BODY = ('{"chart":{"result":[{"timestamp":[1791244800,1791331200,1791417600],"indicators":{"quote":[{"close":[10.0,9.0,8.0]}],'
         '"adjclose":[{"adjclose":[9.5,null,8.5]}]}}]}}')


def test_the_adjclose_field_is_read_when_asked_and_the_printed_close_otherwise():
    adj = A.parse_yahoo_chart(_BODY, "usd", 5, field="adjclose")
    assert adj["history"] == [["2026-10-06", 9.5], ["2026-10-08", 8.5]]  # the null is skipped, never filled
    assert adj["value"] == 8.5
    assert A.parse_yahoo_chart(_BODY, "usd", 5)["history"][-1] == ["2026-10-08", 8.0]  # default unchanged


def test_a_body_without_the_adjusted_field_is_malformed_not_silently_the_printed_close():
    body = '{"chart":{"result":[{"timestamp":[1791244800],"indicators":{"quote":[{"close":[10.0]}]}}]}}'
    assert A.parse_yahoo_chart(body, "usd", 5, field="adjclose") == {"malformed": "shape"}


def test_the_bizd_ingredient_asks_for_the_adjusted_close_with_enough_history():
    ing = next(i for i in INGREDIENTS if i.serves == ("private_credit_stress",))
    assert ing.kind == "yahoo" and ing.ref == "BIZD" and ing.column == "adjclose" and ing.completes == "COMPONENT"
    assert ing.history >= DRAWDOWN_WINDOW
    adapter = build_adapter(ing, lambda: NOW)
    assert adapter._field == "adjclose" and "BIZD" in adapter._url() and "range=2y" in adapter._url()
    # every OTHER yahoo ingredient still reads the printed close
    for other in INGREDIENTS:
        if other.kind == "yahoo" and other is not ing:
            assert build_adapter(other, lambda: NOW)._field == "close"


# --- wiring, scoring and the page --------------------------------------------------------------------------- #


def _row(db_path, now=NOW):
    with SqliteStore(db_path, read_only=True) as ro:
        return next(i for i in build_state(ro, now)["indicators"] if i["id"] == "private_credit_stress")


def test_unfed_it_reads_missing_and_yields_no_observation_never_calm(db_path):
    with SqliteStore(db_path) as w:
        assert not [o for o in observations_from_store(w, build_wiring(), NOW) if o.source_id == "private_credit_stress"]
    row = _row(db_path)
    assert row["state"] == "MISSING" and row["value"] is None


def test_fed_it_is_live_on_the_equity_dial_only_and_carries_the_proxy_disclosure(db_path):
    wiring = build_wiring()
    with SqliteStore(db_path) as w:
        _seed(w, wiring, {"private_credit_stress": 18.0})
    row = _row(db_path)
    assert row["state"] == "LIVE" and row["value"] == pytest.approx(18.0) and row["dials"] == ["equity_crash"]
    assert row["window_days"] == 7.0   # WO-1.9: market-day daily window
    assert "SUBSTITUTE FEED" in row["why"] and "MARKET-PRICE" in row["why"] and "NOT the underlying loan" in row["why"]


def test_the_figure_is_scored_through_the_placeholder_band_and_moves_the_equity_dial_only(db_path, tmp_path):
    wiring = build_wiring()
    dials = {}
    for figure in (5.0, 17.5, 30.0):
        path = str(tmp_path / f"{figure}.sqlite")
        values = CALM | {"private_credit_stress": figure}
        with SqliteStore(path) as w:
            _seed(w, wiring, values)
        with SqliteStore(path, read_only=True) as ro:
            state = build_state(ro, NOW)
        dials[figure] = {d["dial_id"]: d for d in state["dials"]}
        eq = dials[figure]["equity_crash"]
        assert "private_credit_stress" in eq["inputs_used"]
        assert eq["value"] == pytest.approx(_expected("equity_crash", values))  # independent re-derivation
    assert dials[5.0]["equity_crash"]["value"] < dials[17.5]["equity_crash"]["value"] < dials[30.0]["equity_crash"]["value"]
    assert all(dials[f]["monetary_debasement"]["value"] == dials[5.0]["monetary_debasement"]["value"] for f in dials)
    assert "private_credit_stress" not in dials[5.0]["monetary_debasement"]["inputs_used"]


def test_an_eight_day_old_reading_is_stale_not_live(db_path):
    wiring = build_wiring()
    with SqliteStore(db_path) as w:
        _seed(w, wiring, {"private_credit_stress": 18.0}, age=timedelta(days=8))
    row = _row(db_path)
    assert row["state"] == "STALE" and row["value"] is None  # the ratified 120 days would have shown it live


def test_the_page_renders_the_disclosure(db_path):
    wiring = build_wiring()
    with SqliteStore(db_path) as w:
        _seed(w, wiring, CALM)
    with SqliteStore(db_path, read_only=True) as ro:
        page = gui_server.render_page(build_state(ro, NOW))
    assert "private_credit_stress" in page and "MARKET-PRICE" in page


def test_the_substitution_record_names_what_was_not_built_and_what_stays_open():
    text = SUBSTITUTED_FEEDS["private_credit_stress"]
    for needle in ("MARKET-PRICE", "BIZD", "DIVIDEND-ADJUSTED", "NAV", "non-accrual", "PIK", "v2", "v3", "not Owner-ratified"):
        assert needle in text
