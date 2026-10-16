"""WO-1.4: the GUI view-model and server. Absence never renders as calm; the dials are never combined."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from datetime import timedelta
from http.server import ThreadingHTTPServer

import pytest

from gui import server as gui_server
from gui.state import build_state
from ingestion.store import SqliteStore
from ingestion.wiring import build_wiring

from test_wiring import CALM, NOW, _seed


@pytest.fixture
def wiring():
    return build_wiring()


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "raw.sqlite")


def _state(db_path):
    with SqliteStore(db_path, read_only=True) as ro:
        return build_state(ro, NOW)


def _dial(state, dial_id):
    return next(d for d in state["dials"] if d["dial_id"] == dial_id)


def test_empty_store_shows_no_reading_on_both_dials_and_pending_reasons(db_path):
    with SqliteStore(db_path):
        pass
    state = _state(db_path)
    for d in state["dials"]:
        assert d["status"] == "NO READING" and d["value"] is None and d["reason"]
    page = gui_server.render_page(state)
    assert page.count("NO READING") >= 2
    pending = [i for i in state["indicators"] if i["state"] == "PENDING"]
    assert not pending  # WO-1.8: nothing is PENDING any more; an unfed indicator reads MISSING, never calm
    assert all(i["state"] != "LIVE" for i in state["indicators"])


def test_full_store_shows_two_separate_values_and_live_indicators(db_path, wiring):
    with SqliteStore(db_path) as w:
        _seed(w, wiring, CALM)
    state = _state(db_path)
    eq, mo = _dial(state, "equity_crash"), _dial(state, "monetary_debasement")
    assert eq["status"] == "VALUE" and mo["status"] == "VALUE"
    assert 0.0 <= eq["value"] <= 1.0 and 0.0 <= mo["value"] <= 1.0
    assert state["counts"] == {"LIVE": 31}  # WO-1.10: + constituent_breadth_200dma
    # No key anywhere in the view-model combines the dials.
    assert set(state) == {"generated_utc", "provisional", "dials", "indicators", "counts"}
    live = {i["id"]: i for i in state["indicators"] if i["state"] == "LIVE"}
    assert live["hy_oas"]["value"] == CALM["hy_oas"] and live["hy_oas"]["dials"] == ["equity_crash"]
    assert "PROVISIONAL" in gui_server.render_page(state)
    for d in state["dials"]:
        assert (d["coverage"]["fraction"] == 1.0) == (not d["coverage"]["pending"]) and d["coverage"]["fraction"] > 0.0
    assert "gold_real_rate_cross" in gui_server.render_page(state)
    # WO-1.6: the two substituted feeds are LIVE but say, on the page, that they are not the ratified row's.
    for substituted in ("buffett_indicator", "fiscal_dominance", "ism_manufacturing", "gold_real_rate_cross",
                        "private_credit_stress"):
        assert live[substituted]["substitute"] and "SUBSTITUTE FEED" in live[substituted]["why"]
    assert live["buffett_indicator"]["window_days"] == 120.0  # the recorded override, not the ratified 45
    assert live["fiscal_dominance"]["value"] == 0.0 and live["fiscal_dominance"]["dials"] == ["monetary_debasement"]
    assert live["buffett_indicator"]["dials"] == ["equity_crash"]
    assert live["gold_spot"]["dials"] == ["monetary_debasement"]


def test_a_missing_required_input_blanks_that_dial_only(db_path, wiring):
    with SqliteStore(db_path) as w:
        _seed(w, wiring, CALM, skip=("hy_oas",))
    state = _state(db_path)
    eq, mo = _dial(state, "equity_crash"), _dial(state, "monetary_debasement")
    assert eq["status"] == "NO READING" and eq["value"] is None and "hy_oas" in eq["missing_inputs"]
    assert mo["status"] == "VALUE"


def test_a_stale_indicator_is_not_shown_as_a_value(db_path, wiring):
    with SqliteStore(db_path) as w:
        _seed(w, wiring, {"hy_oas": 3.0}, age=timedelta(days=30))
    row = next(i for i in _state(db_path)["indicators"] if i["id"] == "hy_oas")
    assert row["state"] == "STALE" and row["value"] is None and row["age_days"] == 30.0


def test_read_only_store_cannot_write_or_create(db_path, tmp_path):
    with pytest.raises(Exception):
        SqliteStore(str(tmp_path / "does-not-exist.sqlite"), read_only=True)
    with SqliteStore(db_path):
        pass
    with SqliteStore(db_path, read_only=True) as ro:
        with pytest.raises(Exception):
            ro._db.execute("DELETE FROM raw_reading")


def test_text_from_the_store_is_html_escaped():
    state = {
        "generated_utc": "x", "provisional": "<script>alert(1)</script>", "counts": {"<b>": 1},
        "dials": [{"dial_id": "d", "title": "<i>t</i>", "status": "NO READING", "value": None, "as_of_utc": None,
                   "coverage": {"fraction": 0.5, "pending": ["<p>"]}, "missing_inputs": ["<img>"], "reason": "<u>why</u>", "inputs_used": []}],
        "indicators": [],
    }
    page = gui_server.render_page(state)
    for raw in ("<script>alert", "<i>t</i>", "<img>", "<u>why", "<b>: 1", "<p>"):
        assert raw not in page


def _get(url):
    """(status, headers, body); an HTTP error status is returned, not raised, and every socket is closed."""
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.status, resp.headers, resp.read()
    except urllib.error.HTTPError as err:
        with err:
            return err.code, err.headers, err.read()


@pytest.fixture
def running(db_path):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), gui_server.Handler)
    srv.db_path = db_path
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


# --- WO-1.21: the top-right gauge, one per dial ----------------------------------------- #
#
# Three claims, each pinned separately: the needle's angle is the REAL geometry of a
# semicircular 0-1 gauge (0 -> left, 1 -> right, 0.5 -> straight up), a dial with NO READING
# gets the track and NO needle at all (a needle has to point somewhere, and this GUI's whole
# discipline is that an absent dial never shows a number that looks like one), and the gauge
# is actually present in the rendered page for both dials.


def test_the_gauge_needle_points_left_at_zero_right_at_one_and_straight_up_at_half():
    from gui.server import _gauge_svg

    # A semicircular gauge's pivot is the arc's centre; "left" and "right" are the horizontal
    # bounds of the SAME y as the pivot, and "straight up" is the same x, well above it.
    assert '<line x1="60.0" y1="65.0" x2="18.0" y2="65.0"' in _gauge_svg(0.0)
    assert '<line x1="60.0" y1="65.0" x2="102.0" y2="65.0"' in _gauge_svg(1.0)
    assert '<line x1="60.0" y1="65.0" x2="60.0" y2="23.0"' in _gauge_svg(0.5)


def test_the_gauge_has_no_needle_at_all_when_there_is_no_reading():
    from gui.server import _gauge_svg

    svg = _gauge_svg(None)
    assert "<line " not in svg and "<circle" not in svg  # "<line" alone is a prefix of "<linearGradient"
    assert "<svg" in svg and "gaugeGrad" in svg  # the track itself still renders


def test_the_gauge_clamps_an_out_of_range_value_on_the_drawing_only():
    # The dial's own number is never clamped anywhere in this file; this is a defensive bound
    # on the NEEDLE's drawing alone, so a provisional figure outside [0,1] still SHOWS as the
    # number it is while the needle does not fly off the semicircle.
    from gui.server import _gauge_svg

    assert _gauge_svg(0.0) == _gauge_svg(-0.4)
    assert _gauge_svg(1.0) == _gauge_svg(1.7)


def test_the_gauge_renders_in_the_page_for_both_dials_and_tracks_their_reading(running, db_path, wiring):
    with SqliteStore(db_path) as w:
        _seed(w, wiring, CALM, age=timedelta(hours=1))
    page = _get(running + "/")[2].decode()
    assert page.count('<svg class="gauge"') == 2  # one per dial, never fewer, never combined
    assert page.count('id="gaugeGrad"') == 2  # one definition per gauge; "gaugeGrad" alone also counts each url(#...) reference


def test_a_no_reading_dial_gets_a_gauge_track_with_no_needle_on_the_live_page(db_path):
    with SqliteStore(db_path):
        pass
    page = gui_server.render_page(_state(db_path))
    assert page.count('<svg class="gauge"') == 2
    # Both dials are NO READING on an empty store: neither gauge may show a needle.
    dials_html = page.split('<div class="dials">')[1].split("</main>")[0]
    assert dials_html.count("<line ") == 0 and dials_html.count("<circle") == 0  # "<line" alone also matches "<linearGradient"


def test_server_refuses_to_render_when_the_store_is_unreadable(running):
    for path in ("/", "/api/state", "/healthz"):
        assert _get(running + path)[0] == 503


def test_server_serves_page_json_and_health(running, db_path, wiring):
    with SqliteStore(db_path) as w:
        _seed(w, wiring, CALM, age=timedelta(hours=1))
    status, headers, body = _get(running + "/")
    assert status == 200 and headers["X-CD-Build"] == gui_server.BUILD_SHA
    assert b"Equity crash" in body and b"Monetary debasement" in body
    state = json.loads(_get(running + "/api/state")[2])
    assert [d["dial_id"] for d in state["dials"]] == ["equity_crash", "monetary_debasement"]
    assert json.loads(_get(running + "/healthz")[2])["ok"] is True
    assert _get(running + "/nope")[0] == 404
