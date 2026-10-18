"""WO-1.22: the dial-history chart under the two dials — the store's door, the geometry, the panel.

Offline and clock-free: every instant is a constant derived from
``tests/test_machine_state_history.py``'s ``AS_OF``, the store is pytest's ``tmp_path``, and
the two row builders (``_resolved`` / ``_unknown``) are IMPORTED from that file rather than
retyped — a second copy of "what a valid row looks like" would drift from the schema the
CHECK constraints actually enforce.

THE GEOMETRY IS PINNED AT EXACT COORDINATES, following ``_gauge_svg``'s own tests in
``tests/test_gui.py``: "contains a polyline" would pass against a chart that plotted every
point on top of itself. The y-axis assertions exist for the specific failure the module
docstring refuses — a range fitted to the data, which turns four days of noise into a
dramatic swing — so they check that a near-flat pair stays near-flat on the 0-1 axis.
"""

from __future__ import annotations

import html
import json
import re
import threading
from datetime import timedelta
from http.server import ThreadingHTTPServer

import pytest

from crash_detector.dials.dialset import DIAL_IDS
from evaluator.history_store import MachineStateHistoryStore
from evaluator.resolve import BREADTH_LOOKBACK_ROWS
from gui import server as gui_server
from gui.history import (HISTORY_CAPTION, PLOT_BOTTOM, PLOT_LEFT, PLOT_RIGHT, PLOT_TOP,
                         _MARKER_LIMIT, _PENS, _x, _y, dial_series, history_chart_svg,
                         history_panel_html)
from gui.state import DIAL_TITLES, build_state
from ingestion.store import SqliteStore

from test_gui import _get
from test_machine_state_history import AS_OF, _resolved, _unknown

EQUITY, MONETARY = DIAL_IDS


@pytest.fixture()
def store(tmp_path):
    with MachineStateHistoryStore(str(tmp_path / "machine-state.sqlite")) as s:
        yield s


def _day(offset: int):
    """A ``written_utc`` ``offset`` days after ``AS_OF`` — the evaluator's daily cadence."""
    return AS_OF + timedelta(days=offset)


def _append(store, dial_id: str, *, day: int, breadth):
    """One real row for ``dial_id``, resolved with ``breadth`` or UNKNOWN when it is ``None``."""
    row = _unknown(dial_id=dial_id) if breadth is None else _resolved(dial_id=dial_id, breadth=breadth)
    store.append(row, written_utc=_day(day))


def _entry(dial_id: str, points):
    """One ``dial_series`` entry, shaped exactly as the real one, over a known set of points."""
    colour, dash = _PENS[DIAL_IDS.index(dial_id)]
    return {
        "dial_id": dial_id, "title": DIAL_TITLES[dial_id], "colour": colour, "dash": dash,
        "points": list(points), "rows_read": len(points), "without_breadth": 0,
    }


def _polylines(svg: str) -> list:
    """Every polyline's ``points`` attribute, parsed back into ``(x, y)`` pairs."""
    return [
        [tuple(float(n) for n in pair.split(",")) for pair in attr.split()]
        for attr in re.findall(r'<polyline[^>]*points="([^"]+)"', svg)
    ]


# --- breadth_series: the store's door onto the series ------------------------------------ #


def test_breadth_series_returns_written_utc_and_breadth_oldest_first_in_append_order(store):
    for day, breadth in ((0, 0.11), (1, 0.22), (2, 0.33)):
        _append(store, EQUITY, day=day, breadth=breadth)

    assert store.breadth_series(EQUITY) == (
        (_day(0), 0.11), (_day(1), 0.22), (_day(2), 0.33),
    )
    # recent() answers the same rows in the OPPOSITE order and without written_utc at all,
    # which is why this method exists rather than reusing it.
    assert [row.breadth for row in store.recent(EQUITY, limit=3)] == [0.33, 0.22, 0.11]


def test_breadth_series_includes_an_unknown_rows_none_breadth_rather_than_filtering_it(store):
    _append(store, EQUITY, day=0, breadth=0.11)
    _append(store, EQUITY, day=1, breadth=None)   # UNKNOWN: the dial did not resolve
    _append(store, EQUITY, day=2, breadth=0.33)

    # "could not be resolved" must stay distinguishable from "no row was written" at this
    # layer; dropping it is dial_series's judgement to make, not the store's.
    assert store.breadth_series(EQUITY) == (
        (_day(0), 0.11), (_day(1), None), (_day(2), 0.33),
    )


def test_breadth_series_keeps_the_two_dials_series_independent(store):
    _append(store, EQUITY, day=0, breadth=0.11)
    _append(store, MONETARY, day=0, breadth=0.91)
    _append(store, MONETARY, day=1, breadth=0.92)

    assert store.breadth_series(EQUITY) == ((_day(0), 0.11),)
    assert store.breadth_series(MONETARY) == ((_day(0), 0.91), (_day(1), 0.92))


def test_breadth_series_returns_every_row_not_just_the_breadth_lookback_window(store):
    total = BREADTH_LOOKBACK_ROWS + 5
    for day in range(total):
        _append(store, EQUITY, day=day, breadth=0.01 * day)

    series = store.breadth_series(EQUITY)
    assert len(series) == total, "the history was silently truncated to a state-machine window"
    assert len(store.recent(EQUITY, limit=BREADTH_LOOKBACK_ROWS)) == BREADTH_LOOKBACK_ROWS
    assert series[0] == (_day(0), 0.0)  # the oldest row is still there


# --- dial_series: the plottable view over both dials ------------------------------------- #


def test_dial_series_drops_none_breadth_points_but_counts_them_in_without_breadth(store):
    _append(store, EQUITY, day=0, breadth=0.11)
    _append(store, EQUITY, day=1, breadth=None)
    _append(store, EQUITY, day=2, breadth=0.33)
    _append(store, MONETARY, day=0, breadth=0.91)

    equity, monetary = dial_series(store)
    assert equity["points"] == [(_day(0), 0.11), (_day(2), 0.33)]
    assert equity["rows_read"] == 3 and equity["without_breadth"] == 1
    assert all(breadth is not None for _, breadth in equity["points"])
    assert monetary["points"] == [(_day(0), 0.91)] and monetary["without_breadth"] == 0


def test_dial_series_follows_dial_ids_sequence_and_carries_each_dials_own_colour_dash_and_title(store):
    _append(store, EQUITY, day=0, breadth=0.11)
    _append(store, MONETARY, day=0, breadth=0.91)

    series = dial_series(store)
    assert [entry["dial_id"] for entry in series] == list(DIAL_IDS)
    assert [entry["title"] for entry in series] == [DIAL_TITLES[d] for d in DIAL_IDS]
    assert [(entry["colour"], entry["dash"]) for entry in series] == list(_PENS)
    # Identity is carried redundantly: neither hue nor dash is shared by the two lines.
    assert series[0]["colour"] != series[1]["colour"] and series[0]["dash"] != series[1]["dash"]


# --- the SVG geometry -------------------------------------------------------------------- #


def test_known_points_map_to_exact_plot_coordinates_in_the_polyline():
    # Four days wide and the full 0-1 height: x spans PLOT_LEFT..PLOT_RIGHT (50..690) and y
    # spans PLOT_BOTTOM..PLOT_TOP (194..34), so the midpoint of both is exactly 370.0,114.0.
    points = [(_day(0), 0.0), (_day(2), 0.5), (_day(4), 1.0)]
    svg = history_chart_svg([_entry(EQUITY, points), _entry(MONETARY, [])])

    assert 'points="50.0,194.0 370.0,114.0 690.0,34.0"' in svg
    assert _polylines(svg) == [[(50.0, 194.0), (370.0, 114.0), (690.0, 34.0)]]
    # The same three coordinates, computed by the functions themselves rather than retyped.
    for (moment, breadth), expected in zip(points, ((50.0, 194.0), (370.0, 114.0), (690.0, 34.0))):
        assert (_x(moment, _day(0), _day(4)), _y(breadth)) == expected
        assert f'<circle cx="{expected[0]:.1f}" cy="{expected[1]:.1f}" r="4"' in svg


def test_a_series_with_one_or_no_points_draws_no_polyline_and_no_markers():
    drawable = _entry(EQUITY, [(_day(0), 0.25), (_day(4), 0.75)])
    lone = _entry(MONETARY, [(_day(2), 0.5)])
    svg = history_chart_svg([drawable, lone])

    assert len(_polylines(svg)) == 1, "a one-point series was drawn as a trend"
    assert _polylines(svg) == [[(50.0, 154.0), (690.0, 74.0)]]
    assert svg.count("<circle") == 2  # the drawable series' two markers, and not the lone point
    assert "370.0,114.0" not in svg and 'cx="370.0"' not in svg
    # The legend still names the dial that has no line, rather than omitting it.
    assert f"{DIAL_TITLES[MONETARY]} — no history yet" in svg

    assert _polylines(history_chart_svg([_entry(EQUITY, []), _entry(MONETARY, [])])) == []


def test_a_series_at_the_marker_limit_gets_a_marker_per_point_and_one_over_it_gets_none():
    at_limit = [(_day(day), 0.5) for day in range(_MARKER_LIMIT)]
    svg = history_chart_svg([_entry(EQUITY, at_limit), _entry(MONETARY, [])])
    assert len(_polylines(svg)[0]) == _MARKER_LIMIT
    assert svg.count("<circle") == _MARKER_LIMIT

    over_limit = [(_day(day), 0.5) for day in range(_MARKER_LIMIT + 1)]
    dense = history_chart_svg([_entry(EQUITY, over_limit), _entry(MONETARY, [])])
    assert len(_polylines(dense)[0]) == _MARKER_LIMIT + 1, "the line itself lost points"
    assert dense.count("<circle") == 0


def test_no_dial_with_two_points_says_no_history_yet_instead_of_drawing_empty_axes():
    svg = history_chart_svg([_entry(EQUITY, [(_day(0), 0.4)]), _entry(MONETARY, [])])

    assert "NO HISTORY YET" in svg
    assert "<polyline" not in svg and "<circle" not in svg
    # An empty set of axes reads as "both lines are flat at zero"; the words are the point.
    assert "<svg" in svg and "fewer than two evaluated readings" in svg


def test_the_y_axis_is_always_zero_to_one_and_never_fitted_to_the_datas_own_range():
    # Near both ends of the dials' scale: inside the plot box, and NOT on its edges.
    wide = history_chart_svg([_entry(EQUITY, [(_day(0), 0.99), (_day(4), 0.01)]), _entry(MONETARY, [])])
    assert _polylines(wide) == [[(50.0, 35.6), (690.0, 192.4)]]
    for _, y in _polylines(wide)[0]:
        assert PLOT_TOP < y < PLOT_BOTTOM, "a value inside 0-1 was drawn outside the plot box"

    # A near-flat pair STAYS near-flat: a fitted y-range would stretch 0.02 of difference
    # across the whole 160px box. 0.40 -> 130.0 and 0.42 -> 126.8 on the fixed 0-1 axis.
    flat = history_chart_svg([_entry(EQUITY, [(_day(0), 0.40), (_day(4), 0.42)]), _entry(MONETARY, [])])
    assert _polylines(flat) == [[(50.0, 130.0), (690.0, 126.8)]]
    assert _y(0.0) == PLOT_BOTTOM and _y(1.0) == PLOT_TOP
    assert _x(_day(0), _day(0), _day(4)) == PLOT_LEFT and _x(_day(4), _day(0), _day(4)) == PLOT_RIGHT


# --- history_panel_html ------------------------------------------------------------------ #


def test_the_unavailable_panel_states_the_absence_and_draws_no_chart():
    panel = history_panel_html(None, unavailable="CD_STATE_PATH is unset: no history is mounted.")

    assert "NO HISTORY AVAILABLE" in panel
    assert "CD_STATE_PATH is unset: no history is mounted." in panel  # the reason travels with it
    assert "<svg" not in panel and "<polyline" not in panel
    assert "Points plotted" not in panel


def test_the_panel_reports_the_points_plotted_and_notes_unresolved_readings_only_when_there_are_some(store):
    _append(store, EQUITY, day=0, breadth=0.11)
    _append(store, EQUITY, day=1, breadth=None)
    _append(store, EQUITY, day=2, breadth=0.33)
    _append(store, MONETARY, day=0, breadth=0.91)
    _append(store, MONETARY, day=1, breadth=0.92)

    panel = history_panel_html(dial_series(store))
    assert "Points plotted: Equity crash 2, Monetary debasement 2." in panel
    assert "Equity crash: 1 reading(s) could not be resolved" in panel
    assert "Monetary debasement: 0 reading(s)" not in panel, "a zero count was reported as a note"
    assert '<svg class="histchart"' in panel and "NO HISTORY AVAILABLE" not in panel


def test_the_history_caption_is_rendered_verbatim_on_the_panel(store):
    _append(store, EQUITY, day=0, breadth=0.11)

    panel = history_panel_html(dial_series(store))
    # Escaped, not reworded: the apostrophes in the caption become &#x27; in the source and
    # read back as the caption's own text in the browser.
    assert html.escape(HISTORY_CAPTION) in panel
    assert "NOT a reconstructed history across past crash episodes" in panel


# --- gui/server.py's integration --------------------------------------------------------- #


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "raw.sqlite")
    with SqliteStore(path):
        pass
    return path


def _state(db_path):
    with SqliteStore(db_path, read_only=True) as ro:
        return build_state(ro, AS_OF)


@pytest.fixture
def history_path(tmp_path):
    """A real evaluator history store with two days of readings on both dials."""
    path = str(tmp_path / "machine-state.sqlite")
    with MachineStateHistoryStore(path) as writer:
        for day, (equity, monetary) in enumerate(((0.11, 0.91), (0.33, 0.92))):
            _append(writer, EQUITY, day=day, breadth=equity)
            _append(writer, MONETARY, day=day, breadth=monetary)
    return path


@pytest.fixture
def serve(db_path):
    """Start real servers on loopback ports, as ``test_gui.py``'s ``running`` fixture does.

    A factory rather than one fixture because ``CD_STATE_PATH`` set and unset are two
    separate cases of the same handler and both are driven over real HTTP.
    """
    started = []

    def start(state_path=None):
        srv = ThreadingHTTPServer(("127.0.0.1", 0), gui_server.Handler)
        srv.db_path = db_path
        if state_path is not None:
            srv.state_path = state_path
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        started.append(srv)
        return f"http://127.0.0.1:{srv.server_address[1]}"

    yield start
    for srv in started:
        srv.shutdown()
        srv.server_close()


def test_render_page_places_the_history_panel_between_the_dials_and_the_indicators_table(db_path, store):
    _append(store, EQUITY, day=0, breadth=0.11)
    _append(store, EQUITY, day=1, breadth=0.33)
    page = gui_server.render_page(_state(db_path), history_panel_html(dial_series(store)))

    assert page.index('<div class="dials">') < page.index('<section class="histpanel">')
    assert page.index('<section class="histpanel">') < page.index("<h3>Indicators (")
    # The chart lives in the panel between them, not inside the dials block.
    dials_html = page.split('<div class="dials">')[1].split('<section class="histpanel">')[0]
    assert "histchart" not in dials_html


def test_render_page_renders_the_raw_store_view_unchanged_when_no_history_is_passed(db_path):
    page = gui_server.render_page(_state(db_path))

    # The panel's CSS is always in the <style> block; what must be absent is the panel.
    assert '<section class="histpanel">' not in page and '<svg class="histchart"' not in page
    assert page.count("NO READING") >= 2 and "<h3>Indicators (" in page


def test_the_live_page_states_the_absence_when_cd_state_path_is_unset(serve):
    status, _, body = _get(serve() + "/")
    page = body.decode()

    assert status == 200
    assert "NO HISTORY AVAILABLE" in page and "CD_STATE_PATH is unset" in page
    assert "<polyline" not in page  # no chart at all, and no empty axes standing in for one
    assert "Equity crash" in page, "a missing history took the dials down with it"


def test_the_live_page_draws_both_dials_lines_from_a_real_history_store(serve, history_path):
    status, _, body = _get(serve(history_path) + "/")
    page = body.decode()

    assert status == 200 and "NO HISTORY AVAILABLE" not in page
    assert page.count('<svg class="histchart"') == 1
    assert len(_polylines(page)) == 2, "one line per dial, from the evaluator's own store"
    assert _polylines(page) == [[(50.0, 176.4), (690.0, 141.2)], [(50.0, 48.4), (690.0, 46.8)]]
    assert "Points plotted: Equity crash 2, Monetary debasement 2." in page


def test_api_state_json_is_unchanged_by_this_work_order(serve, history_path):
    for url in (serve(), serve(history_path)):
        status, _, body = _get(url + "/api/state")
        state = json.loads(body)

        assert status == 200
        # The pinned key set, re-asserted here rather than assumed from test_gui.py: no key
        # of the view-model combines the dials and none of them is the history.
        assert set(state) == {"generated_utc", "provisional", "dials", "indicators", "counts"}
        assert [d["dial_id"] for d in state["dials"]] == list(DIAL_IDS)
        assert b"histchart" not in body and b"histpanel" not in body
        # Nor was a key added inside a dial or an indicator: the chart is not in this JSON
        # at any depth, and the series it draws is read from the other store entirely.
        assert set(state["dials"][0]) == {"dial_id", "title", "status", "value", "as_of_utc",
                                         "coverage", "missing_inputs", "reason", "inputs_used"}
        assert set(state["indicators"][0]) == {"id", "name", "tier", "dials", "state", "value",
                                               "unit", "as_of_utc", "age_days", "window_days",
                                               "why", "wired"}
