"""The dates a FRED series ACTUALLY published on, read off a body FRED served.

WO-1.17. ``ingestion.backfill.backfill_range`` takes an EXPLICIT list of observation dates and
derives nothing — its docstring says a driver that guessed at a publication calendar "would be
inventing the very dates whose values it then claims to have recovered". So somebody has to
supply the list, and for 23 of the 34 backfillable ingredient rows nothing in the tree could:
``ingestion.backfill_dates.observation_dates`` answers for the 11 rows whose dating is
arithmetic (``quarter_end``, ``month_end``) and refuses the rest out loud. This module closes
the FRED half of that gap — the 13 ``obs_date`` rows — and it is the "separate, later piece of
work" that module's docstring forecast rather than an extension of it.

THE METHOD IS THE POINT: NO CALENDAR IS MODELLED HERE, AND THAT IS NOT FASTIDIOUSNESS
    The tempting shape is "weekdays, minus US federal holidays". ``WO-1.17-COST-ESTIMATE.md``
    §3 uses exactly that and says in the same breath that it is an ESTIMATION APPROXIMATION and
    not ground truth, because the model is wrong in both directions at once and the errors do
    not cancel:

    * FRED business days are not NYSE trading days. Good Friday closes the exchange and is not
      a federal holiday; Columbus Day and Veterans Day are federal holidays and the exchange
      trades. One modelled calendar serving both sources asks FRED for ~2 dates a year it has
      no row for and SKIPS ~1 a year it does.
    * Juneteenth became a federal holiday in 2021 and an NYSE closure in 2022, so the model has
      to be correct about history as well as about rules.
    * Series disagree with their own cadence. A weekly series skips weeks; a daily series has
      gaps nobody legislated; ``DRTSCILM`` is a quarterly SURVEY dated at its own release and
      not at any period boundary.

    Every one of those is a question about one publisher's history, and a wrong answer is
    silent: a date the model invents costs a GET and comes back EMPTY (noisy, survivable), but a
    date the model MISSES is a hole in the backfill that nothing downstream ever reports. So the
    list is READ, not computed. FRED's undated body for a series IS its calendar — one row per
    date the series has an observation for — and reading it is one GET per series.

WHAT THIS ASKS FOR, AND WHY IT IS THE SAME QUESTION THE BACKFILL WILL ASK
    :func:`~ingestion.adapters.fred_graph_url`, undated: the identical URL
    :class:`~ingestion.adapters.FredAdapter` issues for this ingredient in the live loop, built
    by the same function so there is ONE way to ask FRED for a series body and not two that
    agree today. The transformation is carried for the same reason — a transformed body is a
    DIFFERENT calendar (``pc1`` has no row until a year after the series starts, because there
    is no year-ago base to compare against), and the honest date list is the calendar of the
    body the backfill will actually read.

    ``ing.history`` is deliberately NOT passed, and it is the obvious wrong move so it is named:
    that field is how many TRAILING rows the live loop carries for a derivation (70 for WALCL,
    2600 for ``fred.DFII10.history``, 0 for the rest). Handing it to a calendar read would
    truncate the body to its last N rows and silently return a date list that stops short — the
    exact failure this module exists to prevent, wearing the costume of a parameter.

    THE CALENDAR BELONGS TO THE (ref, transformation) PAIR, NOT TO THE INGREDIENT ROW.
    ``fred.DFII10`` and ``fred.DFII10.history`` are two catalog rows over one FRED series, so a
    caller walking the 13 rows one at a time pays 13 GETs for 12 distinct calendars. Caching
    that is the CALLER's business — this function has no state and keeps none.

A BODY WE CANNOT READ IS A RAISE AND NEVER AN EMPTY TUPLE
    This is the one place this module parts company with its siblings in
    ``ingestion.adapters``, and the divergence is deliberate. Those parsers answer for ONE
    reading and hand a ``{"malformed": ...}`` payload to the closed response schema, which
    records the failure against that one date; a skipped junk row there costs one observation.
    Here a dropped row is a date that is never asked for at all, in a run whose whole output is
    "which dates were recovered" — a hole with nothing to compare it against. So a header that
    is not this series', a row that is not two cells, a date cell that is not a date, and a date
    carried twice are all :class:`ValueError`. An empty tuple means one thing only: FRED served
    a body we fully understood and it has no observation in the window asked for.
"""

from __future__ import annotations

from datetime import date
from typing import Callable, Tuple, Union

from ingestion.adapters import fred_column, fred_graph_url, http_get
from ingestion.catalog import Ingredient

__all__ = ["MISSING_VALUE_TOKENS", "fred_body_dates", "fred_observation_dates"]

#: FRED's OWN tokens for "this date exists in the series and carries no figure". A row bearing
#: one is NOT a publication date and must not enter a date list: asking the backfill for it buys
#: a recorded EMPTY, which ``ingestion.adapters.parse_fred_csv_for_date`` already names as the
#: answer for exactly this case ("the series has this date and published no figure for it").
#:
#: ANY OTHER TOKEN IS A PUBLICATION, including one that is not a readable number. The question
#: this module answers is "did the series publish on this date", and it did; whether the figure
#: is usable is the backfill's reading to take and the closed response schema's to reject. A
#: date list that pre-judged values would be two modules deciding one thing.
MISSING_VALUE_TOKENS = ("", ".")


def fred_body_dates(text: str, column: str) -> Tuple[str, ...]:
    """Every date a ``fredgraph.csv`` body carries an observation for, ascending. Pure.

    The header check is :func:`~ingestion.adapters.parse_fred_csv`'s, character for character,
    because it is the same endpoint answering the same series — but it RAISES where that one
    returns a ``{"malformed": ...}`` payload, for the reason this module's docstring gives.

    Rows bearing one of :data:`MISSING_VALUE_TOKENS` are excluded; anything else is a
    publication date. The result is SORTED rather than taken in body order: FRED serves oldest
    row first and this does not need to rely on that, the same way every reader of this body
    matches on the date KEY rather than on position.
    """
    lines = text.strip().splitlines()
    header = lines[0].split(",") if lines else []
    if len(header) != 2 or header[0] != "observation_date":
        raise ValueError(
            f"not a fredgraph.csv body: header is {lines[0] if lines else '<empty body>'!r}, "
            f"expected 'observation_date,{column}'")
    if header[1] != column:
        raise ValueError(
            f"this body is series {header[1]!r}, not {column!r}: a date list read off the wrong "
            f"series would be backfilled under this one's key")
    seen: set = set()
    for number, line in enumerate(lines[1:], start=2):
        cells = line.split(",")
        if len(cells) != 2:
            raise ValueError(
                f"line {number} of the {column} body has {len(cells)} cells, not 2: {line!r}. A "
                f"row skipped here is a date never asked for, so the body is refused whole")
        if cells[1] in MISSING_VALUE_TOKENS:
            continue
        try:
            observed = date.fromisoformat(cells[0])
        except ValueError:
            raise ValueError(
                f"line {number} of the {column} body is dated {cells[0]!r}, which is not a date; "
                f"a date we cannot read is not one we may guess at") from None
        if observed in seen:
            raise ValueError(
                f"the {column} body carries {cells[0]} twice: the body contradicts itself and "
                f"this function will not pick one of the two rows for the caller")
        seen.add(observed)
    return tuple(day.isoformat() for day in sorted(seen))


def fred_observation_dates(ing: Ingredient, start: str, end: str, *,
                           timeout_seconds: float,
                           getter: Callable[..., str] = http_get) -> Tuple[str, ...]:
    """The dates ``ing``'s FRED series published on within ``[start, end]``, ascending. ONE GET.

    Interchangeable at a call site with ``ingestion.backfill_dates.observation_dates``: same
    argument shape, same inclusive-bound convention, same ascending tuple of ISO strings, ready
    to hand straight to ``ingestion.backfill.backfill_range``. The difference is the WARRANT —
    that one states a dating convention a formula can express and refuses everything else, this
    one asks the publisher. Where both answer (a monthly or quarterly FRED row) they must agree,
    and ``tests/test_wo117_calendar.py`` holds that they do; where they disagree the body is
    right, because the body is what the backfill will be reading.

    ``start`` and ``end`` are inclusive BOUNDS on the dates returned and are not themselves
    expected to be publication dates. The filter is an exact comparison against the dates the
    body carries — FRED's own windowing is NOT used and could not be trusted for this: a
    ``cosd``/``coed`` window lying entirely before a series' first observation is ignored and the
    WHOLE body comes back (``evidence/wo115_fred_window_probe.json``, case
    ``q2_window_before_series_start``). So the request is undated on purpose and the window is
    applied here, where it is arithmetic rather than a server's courtesy.

    ``timeout_seconds`` is required and has no default: a FRED body is tens of thousands of rows
    where a live poll is one, so the budget belongs to the caller that knows which it is asking
    for, and this module invents no deadline of its own. ``getter`` is the same transport
    ``ingestion.adapters``' adapters take and is called with the same three positional arguments
    :meth:`~ingestion.adapters._BaseAdapter._acquire` calls it with.

    Raises :class:`ValueError` for a kind that is not ``fred`` (this reads a ``fredgraph.csv``
    body and nothing else — CBOE's ``*_History.csv`` and Yahoo's chart JSON are their own
    calendars and their own later rounds) and for a bound it cannot parse. An
    :class:`~crash_detector.collectors.adapter.AdapterFetchError` from the GET propagates
    UNTOUCHED: an undated request carries no claim about a particular date, so there is no 404
    here to translate into EMPTY the way :meth:`~ingestion.adapters.FredAdapter._acquire` does
    for a dated one. A series whose calendar could not be fetched has no date list, and a caller
    must not be able to mistake that for a series that published nothing.
    """
    if ing.kind != "fred":
        raise ValueError(
            f"{ing.source_id} is kind {ing.kind!r}; this reads a fredgraph.csv body. The CBOE and "
            f"Yahoo calendars are read off different bodies by different functions")
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    body = getter(fred_graph_url(ing.ref, ing.transformation), timeout_seconds, None)
    published = fred_body_dates(body, fred_column(ing.ref, ing.transformation))
    return tuple(d for d in published if first <= date.fromisoformat(d) <= last)
