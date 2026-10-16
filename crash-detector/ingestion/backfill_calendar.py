"""The dates a source ACTUALLY published on, read off a body that source served.

WO-1.17. ``ingestion.backfill.backfill_range`` takes an EXPLICIT list of observation dates and
derives nothing — its docstring says a driver that guessed at a publication calendar "would be
inventing the very dates whose values it then claims to have recovered". So somebody has to
supply the list, and for 23 of the 34 backfillable ingredient rows nothing in the tree could:
``ingestion.backfill_dates.observation_dates`` answers for the 11 rows whose dating is
arithmetic (``quarter_end``, ``month_end``) and refuses the rest out loud. This module is the
"separate, later piece of work" that module's docstring forecast rather than an extension of
it, and it closes that gap one SOURCE at a time: the 13 FRED ``obs_date`` rows
(:func:`fred_observation_dates`) and the 3 CBOE rows (:func:`cboe_observation_dates`). Yahoo's
chart JSON is a third calendar in a third body and is a later round still.

ONE ARGUMENT, TWO ENDPOINTS, AND THE DIFFERENCE BETWEEN THEM IS MEASURED AND NOT ASSUMED
    The warrant below is written about FRED because that is the half that came first, and
    every word of it holds for CBOE unchanged: the list is READ, a modelled calendar is wrong
    in both directions, and a missed date is a silent hole. What differs is only what the
    endpoint does with a window, and neither was guessed at:

    * FRED *sometimes* honours ``cosd``/``coed`` and ignores it when the window lies before
      the series' first observation (``evidence/wo115_fred_window_probe.json``), so
      :func:`fred_observation_dates` must ask UNDATED on purpose.
    * ``cdn-api.cboe.com`` honours NO windowing parameter AT ALL — eight spellings plus two
      controls each returned a byte-identical body (``evidence/wo116_cboe_probe.json``), so
      for CBOE there is no dated request to avoid asking for; there is only the one URL
      :func:`~ingestion.adapters.cboe_history_url` builds.

    Either way the window is applied HERE, in arithmetic, over the whole body that arrives.

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
    is not this series', a row that is not its header's width, a date cell that is not a date, and a date
    carried twice are all :class:`ValueError`. An empty tuple means one thing only: the source
    served a body we fully understood and it has no observation in the window asked for.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Callable, Tuple, Union

from ingestion.adapters import cboe_history_url, fred_column, fred_graph_url, http_get
from ingestion.catalog import Ingredient

__all__ = ["MISSING_VALUE_TOKENS", "CBOE_MISSING_VALUE_TOKENS",
           "fred_body_dates", "fred_observation_dates",
           "cboe_body_dates", "cboe_observation_dates"]

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


#: CBOE's token for "this session is in the body and carries no figure" — the EMPTY CELL, and
#: the list is deliberately one token long because CBOE publishes no missing-data marker of its
#: own the way FRED publishes ``.``. This is MEASURED, not inherited from the adapter
#: docstrings that assert it: all three catalog bodies were fetched whole on 2026-10-16 and
#: 22,839 rows across them (SKEW 9,249, VIX 9,295, VIX3M 4,295) carry a figure in EVERY column
#: — zero empty cells, zero unreadable dates, zero duplicate dates, zero short rows. Non-
#: sessions are simply ABSENT rows: a weekend, a holiday, or a date before the index existed
#: has no line at all, which is why a read calendar is the only way to know CBOE's trading days.
#:
#: So this guard has nothing to exclude TODAY and is kept anyway, for the reason
#: ``ingestion.adapters.parse_cboe_csv_for_date`` keeps its own identical one: if a body one day
#: does carry a blank, that date must be EMPTY rather than a publication date this function
#: hands to the backfill as recoverable. FRED's ``.`` is NOT in this list — adding it would be
#: inventing a CBOE convention the endpoint has never used.
CBOE_MISSING_VALUE_TOKENS = ("",)


def cboe_body_dates(text: str, column: str) -> Tuple[str, ...]:
    """Every date a CBOE ``*_History.csv`` body carries a ``column`` figure for, ascending. Pure.

    The sibling of :func:`fred_body_dates`, and the differences are the body's, not a change of
    mind:

    * **``DATE`` is ``MM/DD/YYYY``,** so the cell is CONVERTED and the result is ISO — the same
      conversion :func:`~ingestion.adapters.parse_cboe_csv` does, so one body does not have two
      date readings;
    * **the row width is the HEADER's, not two.** ``SKEW_History.csv`` is ``DATE,SKEW`` and
      ``VIX_History.csv`` is ``DATE,OPEN,HIGH,LOW,CLOSE``, so ``column`` is located by
      :meth:`list.index` and the width is whatever that header declares. A hard-coded 2 would
      refuse every VIX body ever served;
    * **the header check is split in two,** matching
      :func:`~ingestion.adapters.parse_cboe_csv_for_date`'s ``header`` / ``column`` split rather
      than folding both into one message: a body that is not a CBOE history file and a body
      that is one but does not carry the asked-for column are different things to read in a
      backfill log.

    Everything else is :func:`fred_body_dates`'s discipline unchanged, including the order of
    the two checks: a row bearing a :data:`CBOE_MISSING_VALUE_TOKENS` token is skipped before
    its date is parsed, because it is not a publication date whatever its date cell says. A
    short row, an unreadable date and a date carried twice are each a :class:`ValueError` — a
    calendar read that skipped one would drop a date from the list silently, which this module's
    docstring calls a hole nothing downstream ever reports. The result is SORTED rather than
    trusted from the body, even though CBOE serves oldest row first and was measured strictly
    ascending in all three bodies: every other reader of this body matches on the date KEY
    rather than on position, and so does this one.
    """
    lines = text.strip().splitlines()
    header = lines[0].split(",") if lines else []
    if not header or header[0] != "DATE":
        raise ValueError(
            f"not a Cboe *_History.csv body: header is "
            f"{lines[0] if lines else '<empty body>'!r}, expected a 'DATE,...' header")
    if column not in header:
        raise ValueError(
            f"this body carries columns {header!r}, which do not include {column!r}: a date list "
            f"read off the wrong column would be backfilled under this one's key")
    position = header.index(column)
    seen: set = set()
    for number, line in enumerate(lines[1:], start=2):
        cells = line.split(",")
        if len(cells) != len(header):
            raise ValueError(
                f"line {number} of the {column} body has {len(cells)} cells, not "
                f"{len(header)}: {line!r}. A row skipped here is a date never asked for, so the "
                f"body is refused whole")
        if cells[position] in CBOE_MISSING_VALUE_TOKENS:
            continue
        try:
            observed = datetime.strptime(cells[0], "%m/%d/%Y").date()
        except ValueError:
            raise ValueError(
                f"line {number} of the {column} body is dated {cells[0]!r}, which is not an "
                f"MM/DD/YYYY date; a date we cannot read is not one we may guess at") from None
        if observed in seen:
            raise ValueError(
                f"the {column} body carries {observed.isoformat()} twice: the body contradicts "
                f"itself and this function will not pick one of the two rows for the caller")
        seen.add(observed)
    return tuple(day.isoformat() for day in sorted(seen))


def cboe_observation_dates(ing: Ingredient, start: str, end: str, *,
                           timeout_seconds: float,
                           getter: Callable[..., str] = http_get) -> Tuple[str, ...]:
    """The dates ``ing``'s CBOE index had a session on within ``[start, end]``, ascending. ONE GET.

    Interchangeable at a call site with :func:`fred_observation_dates` and with
    ``ingestion.backfill_dates.observation_dates``: same argument shape, same inclusive-bound
    convention, same ascending tuple of ISO strings, ready to hand straight to
    ``ingestion.backfill.backfill_range``. For these three rows the formula sibling can answer
    for NONE of them — all three are ``obs_date``, which it refuses out loud — so this is the
    only honest source of their date lists.

    THE REQUEST IS THE ADAPTER'S, UNCHANGED AND UNDATED, BECAUSE THERE IS NO OTHER REQUEST TO
    MAKE. :func:`~ingestion.adapters.cboe_history_url` builds the identical URL
    :class:`~ingestion.adapters.CboeAdapter` issues for this ingredient in the live loop, and
    here that is not a discipline this function imposes on itself the way
    :func:`fred_observation_dates` does — it is the only URL that exists.
    ``cdn-api.cboe.com`` honours no windowing parameter at all (eight spellings plus two
    controls, byte-identical bodies, ``evidence/wo116_cboe_probe.json``), so every reader of
    this index — live poll, per-date backfill, and this calendar read — gets the SAME whole
    static history and differs only in what it does with it. That makes the filter below the
    entire windowing mechanism, and the ONE GET is the whole cost: 3 GETs for all three rows,
    with no (ref, transformation) pairing to deduplicate the way FRED's 13 rows have.

    ``ing.column`` is carried and ``ing.history`` deliberately is not, for this module's stated
    reason. ``column`` matters more here than it does for FRED: the three rows read two
    different headers (``SKEW`` out of ``DATE,SKEW``; ``CLOSE`` out of
    ``DATE,OPEN,HIGH,LOW,CLOSE``), and it is the catalog's declared column rather than a
    position, so the date list is the calendar of the column the backfill will actually read.

    ``start`` and ``end`` are inclusive BOUNDS and are not themselves expected to be session
    dates; both are parsed BEFORE the GET, so a bound we cannot read costs no bytes. Raises
    :class:`ValueError` for a kind that is not ``cboe`` (this reads a CBOE history CSV and
    nothing else — FRED's ``fredgraph.csv`` is :func:`fred_observation_dates`' and Yahoo's
    chart JSON is its own later round) and for a bound it cannot parse. An
    :class:`~crash_detector.collectors.adapter.AdapterFetchError` from the GET propagates
    UNTOUCHED, and the asymmetry it preserves is :class:`~ingestion.adapters.CboeAdapter`'s own:
    a 404 on this URL is "no history file for this index" in EVERY mode, never "no session on
    that date", so there is nothing here to translate into an empty list. An index whose
    calendar could not be fetched has no date list, and a caller must not be able to mistake
    that for an index that never traded.
    """
    if ing.kind != "cboe":
        raise ValueError(
            f"{ing.source_id} is kind {ing.kind!r}; this reads a Cboe *_History.csv body. The "
            f"FRED and Yahoo calendars are read off different bodies by different functions")
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    body = getter(cboe_history_url(ing.ref), timeout_seconds, None)
    published = cboe_body_dates(body, ing.column)
    return tuple(d for d in published if first <= date.fromisoformat(d) <= last)
