"""CERBERUS WO-1.22 — the two dials' PUBLISHED HISTORY, as a plain SVG line chart.

Requested by the Product Owner directly: underneath the two dials, both dials' past values
over time on one pair of axes, so the relationship between them is visible.

====================================================================================
NO NEW PERSISTENCE. THIS MODULE ONLY READS.
====================================================================================

The series already exists and is already written once per evaluator pass:
``evaluator/pass_once.py`` computes ``breadth = shown.magnitude.quantity_for(dial_id)`` —
**the exact quantity the dial box above shows as its big number**, by the same expression
in ``gui/state.py``'s own ``_dial_entry`` — and
:meth:`evaluator.history_store.MachineStateHistoryStore.append` persists it in
``machine_state_history.breadth``, keyed by ``dial_id`` and ``written_utc``. So this chart
is a VIEW over a fact the evaluator has been recording since 2026-10-14, not a second
place where dial values are stored. Nothing here writes, and the handle is opened
``read_only=True`` (:meth:`~evaluator.history_store.MachineStateHistoryStore.breadth_series`
is available through that door and creates nothing).

That the two numbers are the SAME quantity was confirmed against the live store rather
than asserted: ``monetary_debasement``'s newest stored ``breadth`` was
``0.29494585808622015`` while the live dial showed ``0.295``. The equity figures agree to
four decimals rather than exactly, and THAT IS THE EXPECTED RESULT, not a discrepancy: the
GUI recomputes its dial from the raw store on every request (every 60s) while the evaluator
appends one row a day, so the two are the same quantity read at two different instants.
The chart therefore ends at the last EVALUATED reading, which may sit a little behind the
number in the box above it.

====================================================================================
A SEPARATE MODULE, AND A SEPARATE STORE
====================================================================================

``gui/state.py`` is the view-model over the COLLECTOR's raw store (``cd-live-data``). This
series comes from the EVALUATOR's store (``cd-live-state``) — a different file, a different
writer, a different volume, and the compose file's own "one volume per writer" rule. Fusing
them into one view-model would put two stores' lifetimes behind one name; keeping them
apart is also what lets a missing or unreadable history degrade to a STATED ABSENCE in this
one panel while the dials above it still render.

It is accordingly NOT added to ``/api/state``: that key set is pinned by a test whose
subject is that no key of the view-model combines the dials, and widening it here would buy
a JSON consumer nobody has asked for at the cost of blurring which store answers what.

====================================================================================
WHY THE TWO LINES SHARE ONE Y-AXIS, AND WHY THAT IS NOT THE USUAL MISTAKE
====================================================================================

Plotting two series against two y-scales is the standard way to manufacture a visual
correlation that is not in the data. There is exactly one y-axis here and it is the dials'
OWN fixed 0-1 scale — not a range fitted to the data, which would zoom four days of noise
up into a dramatic-looking swing. Both dials are already expressed on that scale, so this
is one axis honestly shared, and the vertical distance between the lines is a real
difference between two comparable numbers.

The two dials are still NEVER COMBINED (CD-AC-002): there is no sum, no ratio, no spread
and no blended line here. Two independent polylines on shared axes is a COMPARISON, which
is what was asked for; an arithmetic combination of them is what this product refuses.

====================================================================================
COLOUR ENCODES WHICH DIAL, NEVER HOW BAD
====================================================================================

The gauge above (``gui/server.py``'s ``_gauge_svg``) uses a green->amber->red ramp where
hue means MAGNITUDE. Here hue means IDENTITY, and the two meanings must not be confused by
a reader, so neither line is drawn in the gauge's green or red: a red line would read as
"this dial is in alarm" when it only ever means "this is the monetary dial".

:data:`_PENS` is a FIXED ORDER over :data:`~crash_detector.dials.dialset.DIAL_IDS`, never
cycled, so a dial keeps its colour across renders. The pair was validated rather than
eyeballed — worst-case colour-vision-deficient separation Delta E 24.7 (protan) and
normal-vision 33.6 against a white surface, both well clear of the >=8 and >=15 floors — and
identity is carried REDUNDANTLY by a dash pattern as well as hue, so the lines remain
tellable apart in greyscale, in print and for a colourblind reader.

====================================================================================
WHAT THIS CHART IS NOT, AND IT SAYS SO ON ITS FACE
====================================================================================

:data:`HISTORY_CAPTION`. The series begins 2026-10-14 and grows ONE POINT PER DAY
(``CD_EVALUATE_INTERVAL_SECONDS=86400`` since WO-1.3e; the earliest rows are at the old
5-minute cadence, which is why the left of the chart is dense and the right is sparse).
It is a few days of live recording — NOT a reconstructed history across past crash
episodes. That reconstruction is separate, future work tied to WO-1.17's backfill and
R2D2's replay, and a viewer must not mistake this for a long track record. The caption is
part of the chart for the same reason the dial box carries "placeholder bands": a number
whose provenance is only in a work order is a number that will be misread.
"""

from __future__ import annotations

import html
from datetime import datetime
from typing import Union

from crash_detector.dials.dialset import DIAL_IDS
from evaluator.history_store import MachineStateHistoryStore
from gui.state import DIAL_TITLES

__all__ = [
    "HISTORY_CAPTION",
    "HISTORY_BEGAN",
    "dial_series",
    "read_dial_series",
    "history_chart_svg",
    "history_panel_html",
]

#: The first ``written_utc`` in the live store, confirmed by reading it and not from memory.
HISTORY_BEGAN = "2026-10-14"

HISTORY_CAPTION = (
    f"This is the evaluator's own recording of each dial's published number, one row per pass, "
    f"beginning {HISTORY_BEGAN} and growing by one point a day. It is NOT a reconstructed history "
    f"across past crash episodes and it is not a track record: there are only a few days of real "
    f"readings here, and the earliest ones are closer together because the evaluator ran every "
    f"5 minutes before WO-1.3e made it daily."
)

#: ``(colour, dash)`` per dial, in :data:`~crash_detector.dials.dialset.DIAL_IDS` ORDER and
#: never cycled. ``dash`` is the redundant, non-colour half of the encoding; ``""`` is a
#: solid line. See the module docstring on why no line is green or red.
_PENS = (
    ("#2a78d6", ""),       # equity_crash — blue
    ("#eb6834", "7 4"),    # monetary_debasement — orange, dashed
)

#: The one scale both lines are drawn on: the dials' own fixed 0-1 span, NOT a range fitted
#: to the data. See the module docstring.
Y_MIN, Y_MAX = 0.0, 1.0

#: Below this many points a series gets a visible marker per point, because a handful of
#: readings a day apart IS the data and a bare line between them hides how few there are.
#: A dense series gets no markers: 300 overlapping dots are a smear, not information.
_MARKER_LIMIT = 12

VIEW_WIDTH, VIEW_HEIGHT = 720, 220
PLOT_LEFT, PLOT_RIGHT = 50.0, 690.0
PLOT_TOP, PLOT_BOTTOM = 34.0, 194.0

#: The horizontal gridlines. Labelled at the ends and the middle only — a label on every
#: line is the noise this chart does not need.
_Y_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
_Y_LABELLED = (0.0, 0.5, 1.0)


def _y(value: float) -> float:
    """A 0-1 dial value to a plot y. Clamped FOR THE DRAWING ONLY.

    ``_gauge_svg``'s rule, for its reason: the clamp keeps a provisional figure outside
    [0,1] from being drawn off the axes, and no number is ever clamped where it is shown.
    """
    clamped = max(Y_MIN, min(Y_MAX, float(value)))
    return PLOT_BOTTOM - (clamped - Y_MIN) / (Y_MAX - Y_MIN) * (PLOT_BOTTOM - PLOT_TOP)


def _x(moment: datetime, first: datetime, last: datetime) -> float:
    """A timestamp to a plot x, across the REAL date range found in the data.

    A zero span — every point at one instant, or a single shared timestamp — puts them at
    the left edge rather than dividing by zero. Nothing is plotted off it: a series with
    one point draws no line at all (see :func:`history_chart_svg`).
    """
    span = (last - first).total_seconds()
    if span <= 0:
        return PLOT_LEFT
    return PLOT_LEFT + (moment - first).total_seconds() / span * (PLOT_RIGHT - PLOT_LEFT)


def dial_series(store: MachineStateHistoryStore) -> list:
    """Both dials' plottable history, in fixed dial order: a list of two independent entries.

    ``points`` is ``[(written_utc, breadth), ...]`` oldest first, with every row whose
    ``breadth is None`` REMOVED. Such a row is an UNKNOWN reading — the evaluator could not
    resolve the dial, so there is no number (``MachineStateRow``'s documented invariant and
    the schema's CHECK). Charting it as ``0`` would invent a calm reading out of a stated
    absence, which is the one thing this GUI refuses everywhere else; the count is kept in
    ``without_breadth`` so the absence can be reported instead of merely dropped.

    The two dials' series routinely differ in length and in timestamps, and that is normal
    rather than a fault to repair: ``pass_once.one_pass_for_both_dials`` reads and appends
    each dial INDEPENDENTLY (its docstring item 2, CD-AC-002), so the rows are written
    seconds apart and either dial may have rows the other does not. Each line is plotted on
    its own points; nothing here aligns, pads, resamples or interpolates them onto shared
    x-coordinates, all of which would be inventing readings that were never taken.
    """
    series = []
    for dial_id, (colour, dash) in zip(DIAL_IDS, _PENS):
        rows = store.breadth_series(dial_id)
        points = [(written_utc, breadth) for written_utc, breadth in rows if breadth is not None]
        series.append({
            "dial_id": dial_id,
            "title": DIAL_TITLES[dial_id],
            "colour": colour,
            "dash": dash,
            "points": points,
            "rows_read": len(rows),
            "without_breadth": len(rows) - len(points),
        })
    return series


def read_dial_series(path: str) -> list:
    """Open the evaluator's history store READ-ONLY at ``path`` and read both dials.

    Raises if the file is absent or unreadable — ``mode=ro`` creates nothing — and the
    caller decides what that means. ``gui/server.py`` turns it into a stated absence in this
    panel alone rather than a 503 for the whole page: the dials above do not depend on this
    file, and failing the page over a missing chart would hide working data.
    """
    with MachineStateHistoryStore(path, read_only=True) as store:
        return dial_series(store)


def _frame_svg(first: Union[datetime, None], last: Union[datetime, None]) -> str:
    """The axes: four gridlines, three y-labels, and the real date range on the x-axis."""
    parts = []
    for level in _Y_GRID:
        y = _y(level)
        parts.append(
            f'<line x1="{PLOT_LEFT}" y1="{y:.1f}" x2="{PLOT_RIGHT}" y2="{y:.1f}" '
            'stroke="#e4e8ef" stroke-width="1"/>'
        )
        if level in _Y_LABELLED:
            parts.append(
                f'<text x="{PLOT_LEFT - 8}" y="{y + 4:.1f}" text-anchor="end" '
                f'font-size="11" fill="#6a7488">{level:.1f}</text>'
            )
    parts.append(
        f'<line x1="{PLOT_LEFT}" y1="{PLOT_BOTTOM}" x2="{PLOT_RIGHT}" y2="{PLOT_BOTTOM}" '
        'stroke="#cfd5df" stroke-width="1"/>'
    )
    if first is not None and last is not None:
        parts.append(
            f'<text x="{PLOT_LEFT}" y="{PLOT_BOTTOM + 16:.0f}" font-size="11" fill="#6a7488">'
            f"{html.escape(first.date().isoformat())}</text>"
        )
        if last.date() != first.date():
            parts.append(
                f'<text x="{PLOT_RIGHT}" y="{PLOT_BOTTOM + 16:.0f}" text-anchor="end" '
                f'font-size="11" fill="#6a7488">{html.escape(last.date().isoformat())}</text>'
            )
    return "".join(parts)


def _legend_svg(series: list) -> str:
    """A swatch and the dial's own title per line, from ``DIAL_TITLES``.

    Present whenever there are two series, so identity is never carried by colour alone
    (the dash pattern in the swatch is the other half of that). A dial with no line says so
    here, beside its own name, rather than quietly missing from the key.
    """
    parts = []
    x = PLOT_LEFT
    for entry in series:
        drawable = len(entry["points"]) >= 2
        dash = f' stroke-dasharray="{entry["dash"]}"' if entry["dash"] else ""
        parts.append(
            f'<line x1="{x:.0f}" y1="14" x2="{x + 26:.0f}" y2="14" stroke="{entry["colour"]}" '
            f'stroke-width="2" stroke-linecap="round"{dash}/>'
        )
        label = entry["title"] if drawable else f"{entry['title']} — no history yet"
        parts.append(
            f'<text x="{x + 32:.0f}" y="18" font-size="12" fill="#46506a">{html.escape(label)}</text>'
        )
        x += 42 + 7.2 * len(label)
    return "".join(parts)


def _line_svg(entry: dict, first: datetime, last: datetime) -> str:
    """One dial's polyline, plus a marker per point while the series is still short.

    Fewer than two points draws NOTHING: a polyline needs two, and a lone dot presented as
    a trend would be a line this data cannot support. The caller says so in words instead.
    """
    points = entry["points"]
    if len(points) < 2:
        return ""
    coords = " ".join(f"{_x(w, first, last):.1f},{_y(b):.1f}" for w, b in points)
    dash = f' stroke-dasharray="{entry["dash"]}"' if entry["dash"] else ""
    span = f"{points[0][0].date().isoformat()} to {points[-1][0].date().isoformat()}"
    # <title> is the stdlib-only, no-JS hover: the browser shows it natively on the mark.
    out = [
        f'<polyline class="histline" fill="none" stroke="{entry["colour"]}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round"{dash} points="{coords}">'
        f'<title>{html.escape(entry["title"])}: {len(points)} readings, {html.escape(span)}</title>'
        "</polyline>"
    ]
    if len(points) <= _MARKER_LIMIT:
        for w, b in points:
            out.append(
                f'<circle cx="{_x(w, first, last):.1f}" cy="{_y(b):.1f}" r="4" '
                f'fill="{entry["colour"]}"/>'
            )
    return "".join(out)


def history_chart_svg(series: list) -> str:
    """Both dials' history as one inline SVG. Never an empty box that reads as "no stress".

    When NO dial has enough history to draw, the plot area says so in words. That is this
    GUI's standing discipline — an absence must never look like data — and an empty set of
    axes is exactly the picture a reader would take for "the lines are flat at zero".
    """
    plotted = [entry for entry in series if len(entry["points"]) >= 2]
    moments = [w for entry in plotted for w, _ in entry["points"]]
    first, last = (min(moments), max(moments)) if moments else (None, None)
    body = [_frame_svg(first, last), _legend_svg(series)]
    if plotted:
        body.extend(_line_svg(entry, first, last) for entry in plotted)
    else:
        body.append(
            f'<text x="{(PLOT_LEFT + PLOT_RIGHT) / 2:.0f}" y="{(PLOT_TOP + PLOT_BOTTOM) / 2:.0f}" '
            'text-anchor="middle" font-size="14" fill="#8a1c1c" font-weight="700">'
            "NO HISTORY YET — fewer than two evaluated readings per dial</text>"
        )
    return (
        f'<svg class="histchart" viewBox="0 0 {VIEW_WIDTH} {VIEW_HEIGHT}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img">' + "".join(body) + "</svg>"
    )


def history_panel_html(series: Union[list, None], *, unavailable: str = "") -> str:
    """The whole panel: a heading, the chart or a stated absence, and the caption.

    ``unavailable`` is a reason the history could not be read at all (no ``CD_STATE_PATH``,
    an unmounted volume, an unreadable file). It renders as a REFUSAL TO CHART carrying its
    own reason, never as a blank chart and never as silence — the same shape the dial box
    above uses for NO READING.
    """
    if unavailable:
        return (
            '<section class="histpanel"><h3>Dial history</h3>'
            f'<div class="num none">NO HISTORY AVAILABLE</div>'
            f'<div class="why"><b>Why:</b> {html.escape(unavailable)}</div></section>'
        )
    notes = [
        f"{entry['title']}: {entry['without_breadth']} reading(s) could not be resolved "
        f"(UNKNOWN, no number) and are not plotted."
        for entry in (series or [])
        if entry["without_breadth"]
    ]
    counts = ", ".join(
        f"{html.escape(entry['title'])} {len(entry['points'])}" for entry in (series or [])
    )
    return (
        '<section class="histpanel"><h3>Dial history</h3>'
        + history_chart_svg(series or [])
        + f'<div class="why">Points plotted: {counts}. Both lines are on the dials\' own 0–1 scale; '
        "the two dials are shown together for comparison and are never combined.</div>"
        + "".join(f'<div class="why">{html.escape(note)}</div>' for note in notes)
        + f'<div class="why">{html.escape(HISTORY_CAPTION)}</div></section>'
    )
