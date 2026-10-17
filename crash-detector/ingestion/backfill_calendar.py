"""The dates a source ACTUALLY published on, read off a body that source served.

WO-1.17. ``ingestion.backfill.backfill_range`` takes an EXPLICIT list of observation dates and
derives nothing — its docstring says a driver that guessed at a publication calendar "would be
inventing the very dates whose values it then claims to have recovered". So somebody has to
supply the list, and for 24 of the 35 backfillable ingredient rows nothing in the tree could:
``ingestion.backfill_dates.observation_dates`` answers for the 11 rows whose dating is
arithmetic (``quarter_end``, ``month_end``) and refuses the rest out loud. This module is the
"separate, later piece of work" that module's docstring forecast rather than an extension of
it, and it closes that gap one SOURCE at a time: the 14 FRED ``obs_date`` rows
(:func:`fred_observation_dates`), the 3 CBOE rows (:func:`cboe_observation_dates`) and the 7
Yahoo PLAIN-CLOSE rows (:func:`yahoo_observation_dates`) — the third and last source, which
completes the 24.

THE 51 ``adjclose`` YAHOO ROWS ARE NOT PART OF THAT COUNT AND ARE REFUSED BY NAME.
    ``ingestion/catalog.py`` carries 58 ``yahoo`` rows, of which 51 ask for ``column
    == "adjclose"``. A backfilled adjusted close has NO point-in-time meaning at all: it drifts
    retroactively with every dividend and split, for every date before the event, forever
    (PID.md, WO-1.16 scope correction, and the reason
    ``ingestion.vintage.NO_REVISION_MECHANISM_COLUMNS`` admits ``close`` and ``""`` for this
    kind and NOT ``adjclose``). So :func:`yahoo_observation_dates` refuses those rows out loud
    rather than handing back a plausible-looking calendar for a quantity nobody can recover,
    the same refusal :class:`~ingestion.adapters.YahooChartAdapter` makes at construction.

ONE ARGUMENT, THREE ENDPOINTS, AND THE DIFFERENCES BETWEEN THEM ARE MEASURED AND NOT ASSUMED
    The warrant below is written about FRED because that is the source that came first, and
    every word of it holds for CBOE and for Yahoo unchanged: the list is READ, a modelled
    calendar is wrong in both directions, and a missed date is a silent hole. What differs is
    only what each endpoint does with a window, and not one of the three was guessed at:

    * FRED *sometimes* honours ``cosd``/``coed`` and ignores it when the window lies before
      the series' first observation (``evidence/wo115_fred_window_probe.json``), so
      :func:`fred_observation_dates` must ask UNDATED on purpose.
    * ``cdn-api.cboe.com`` honours NO windowing parameter AT ALL — eight spellings plus two
      controls each returned a byte-identical body (``evidence/wo116_cboe_probe.json``), so
      for CBOE there is no dated request to avoid asking for; there is only the one URL
      :func:`~ingestion.adapters.cboe_history_url` builds.
    * ``query1.finance.yahoo.com`` GENUINELY windows, and is the one source of the three whose
      window can be trusted to mean what it says: an absolute ``period1``/``period2`` span is
      either applied exactly or the request is refused with a clean ``400``, never answered
      with somebody else's bars (``evidence/wo116_yahoo_window_probe.json``). So
      :func:`yahoo_observation_dates` is the one that ASKS DATED — and the arithmetic filter is
      kept anyway, because the body is matched on the date KEY here as everywhere else.

    Either way the window is applied HERE, in arithmetic, over whatever body arrives.

THE DEPTH OF A REQUEST IS ALSO MEASURED, AND FOR YAHOO THE OBVIOUS DEEP ASK IS A TRAP
    FRED and CBOE each serve their whole past in one body, so "ask undated" is the whole of
    their depth question. Yahoo's is not: the live loop asks ``range=10d`` (``2y`` with a
    history), neither of which reaches a backfill episode in 2000, and the obvious widening —
    ``range=max`` — is an honoured value that answers a DIFFERENT QUESTION than the one asked.
    It is served COARSENED, with ``interval=1d`` silently ignored: SPY came back 406 bars at
    ``dataGranularity == "1mo"``, ``^GSPC`` 169 bars at ``"3mo"`` beginning 1984-12-01, where
    that same symbol's absolute window reaches its real 1927-12-30 first bar (measured
    2026-10-16, ``evidence/wo117_yahoo_range_probe.json``). A date list read off such a body
    would be MONTH-START dates presented as a daily publication calendar — the silent-hole
    failure this module exists to prevent, arriving as a ``200`` nobody would question. The
    absolute window keeps ``1d`` at every depth measured, so ONE wide windowed GET is the
    mechanism and no chunking is needed; :func:`yahoo_observation_dates` argues the sizes.

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
    caller walking the 14 rows one at a time pays 14 GETs for 13 distinct calendars. Caching
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

    THE ONE PRINCIPLED EXCEPTION IS YAHOO'S ``null`` CLOSE, and it is an exception to the
    "never skip" rule rather than a crack in it: a ``null`` is not a row we failed to read, it
    is the SOURCE ITSELF naming that session as having no print. Skipping it is reading the
    body, not dropping part of it — argued at :func:`yahoo_chart_dates`, where the three
    missing-value conventions of the three sources sit side by side (FRED's ``.``, CBOE's
    empty cell, Yahoo's ``null``) and are each the publisher's own word for the same thing.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Callable, Tuple, Union

from ingestion.adapters import (YAHOO_USER_AGENT, cboe_history_url, fred_column, fred_graph_url,
                                http_get, yahoo_chart_url)
from ingestion.catalog import Ingredient

__all__ = ["MISSING_VALUE_TOKENS", "CBOE_MISSING_VALUE_TOKENS",
           "fred_body_dates", "fred_observation_dates",
           "cboe_body_dates", "cboe_observation_dates",
           "yahoo_chart_dates", "yahoo_observation_dates"]

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
    with no (ref, transformation) pairing to deduplicate the way FRED's 14 rows have.

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


def yahoo_chart_dates(text: str) -> Tuple[str, ...]:
    """Every date a Yahoo v8 chart body carries a PRINTED close for, ascending. Pure.

    The third sibling of :func:`fred_body_dates` and :func:`cboe_body_dates`, reading the same
    body :func:`~ingestion.adapters.parse_yahoo_chart` reads — ``chart.result[0].timestamp``
    beside ``chart.result[0].indicators.quote[0].close`` — and deriving each bar's date from its
    ``timestamp`` exactly as that function derives it: a ``1d`` bar is stamped at the session
    OPEN (1433770200 is 2015-06-08T13:30Z for a US listing on summer time, 14:30Z the same
    session in winter), so the UTC date of the stamp is the session's date.

    A ``null`` CLOSE IS SKIPPED, AND IT IS THE ONE SKIP THIS MODULE ALLOWS ITSELF.
    Everything else in this module refuses a body rather than dropping a row from it, because a
    dropped row is a date the backfill is never told to ask for and a hole nothing downstream
    reports. A ``null`` close is not that. It is the SOURCE's own word for "no print this
    session" — the same signal FRED spells ``.`` and CBOE spells as an empty cell, and the same
    skip :func:`~ingestion.adapters.parse_yahoo_chart` and
    :func:`~ingestion.adapters.parse_yahoo_chart_for_date` already make ("Yahoo nulls a session
    it has no print for; skip, never fill"). So this is not a row we failed to read and quietly
    abandoned; it is a row we read correctly, whose content is "nothing happened". Keeping it
    would be the error: it would enter the date list as a recoverable publication, buy the
    backfill a GET, and come back EMPTY — and worse, it would assert that the symbol printed on
    a date the source has just said it did not.

    THE DISTINCTION IS "A BODY WE CANNOT READ" vs "A BODY SAYING NOTHING HAPPENED", and the
    raise list is drawn exactly along it. Not JSON, no ``chart.result[0]``, no
    ``indicators.quote[0]``, ``timestamp`` and ``close`` of different lengths, a ``timestamp``
    that is not a readable epoch second, and a date carried twice are each a
    :class:`ValueError` — in every one of those the body has stopped telling us what it
    contains, and guessing is how a date goes missing. :func:`parse_yahoo_chart_for_date`
    answers the same shapes with a ``{"malformed": ...}`` payload recorded against ONE date;
    the divergence is this module's, stated in its docstring, and it is the same divergence
    :func:`fred_body_dates` and :func:`cboe_body_dates` make from their own siblings.

    THERE IS NO ``YAHOO_MISSING_VALUE_TOKENS`` BESIDE ITS TWO SIBLINGS, deliberately: Yahoo's
    missing-value convention is not a token at all but JSON ``null``, i.e. a TYPE rather than a
    string, and a one-element tuple holding ``None`` would be a list of string tokens
    pretending to hold one. The check is ``close is None`` and nothing else — a close of ``0``
    is a print, and a ``"."`` would be FRED's convention imported into a body that has never
    used it.

    ABSENT BAR ARRAYS ARE NO BARS, NOT A BROKEN BODY, and that shape is measured rather than
    inferred: a window matching no session — a weekend, a market holiday, a zero-width window —
    comes back ``200`` with ``meta`` intact, ``"indicators":{"quote":[{}]}`` and NO
    ``timestamp`` key at all (``evidence/wo116_yahoo_window_probe.json``,
    ``q3_window_on_non_trading_day``, SPY on 2015-06-13). That is this function's empty tuple,
    which is the one thing an empty tuple may mean here: a body we fully understood, carrying
    no session in the window asked for. (:func:`~ingestion.adapters.parse_yahoo_chart` reads
    the same shape as ``{"malformed": "shape"}``, correctly for ITS question — a ten-day live
    range with no bars in it is a body that cannot be read — and wrongly for this one.)

    The result is SORTED rather than taken in body order, for :func:`fred_body_dates`' reason:
    Yahoo serves oldest bar first and every reader of this body matches on the date KEY rather
    than on position, so this one does not rely on the order either.
    """
    try:
        result = json.loads(text)["chart"]["result"][0]
        quote = result["indicators"]["quote"][0]
        # ABSENT arrays are the probed shape of "no session in this window", so they are read
        # as no bars — NOT, as parse_yahoo_chart reads them, as a body we cannot read.
        stamps = result.get("timestamp") or []
        closes = quote.get("close") or []
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        raise ValueError(
            f"not a Yahoo v8 chart body: {text[:120]!r}. A chart.result[0] carrying an "
            f"indicators.quote[0] is the shape every reader of this endpoint expects, and a "
            f"body we cannot read is not one whose dates we may guess at") from None
    if len(stamps) != len(closes):
        raise ValueError(
            f"this body carries {len(stamps)} timestamps and {len(closes)} closes: the bar "
            f"arrays contradict each other and no pairing of them is this function's to pick")
    seen: set = set()
    for position, (stamp, close) in enumerate(zip(stamps, closes), start=1):
        if close is None:  # the source's own "no print this session"; argued above.
            continue
        try:
            observed = datetime.fromtimestamp(stamp, tz=timezone.utc).date()
        except (OSError, OverflowError, TypeError, ValueError):
            raise ValueError(
                f"bar {position} of this body is stamped {stamp!r}, which is not a readable "
                f"epoch second; a date we cannot read is not one we may guess at") from None
        if observed in seen:
            raise ValueError(
                f"this body carries {observed.isoformat()} twice: the body contradicts itself "
                f"and this function will not pick one of the two bars for the caller")
        seen.add(observed)
    return tuple(day.isoformat() for day in sorted(seen))


def yahoo_observation_dates(ing: Ingredient, start: str, end: str, *,
                            timeout_seconds: float,
                            getter: Callable[..., str] = http_get) -> Tuple[str, ...]:
    """The dates ``ing``'s Yahoo symbol PRINTED a close on within ``[start, end]``, ascending.

    ONE GET, and that it can be one is a MEASUREMENT rather than a convenience — see below.
    Interchangeable at a call site with :func:`fred_observation_dates`,
    :func:`cboe_observation_dates` and ``ingestion.backfill_dates.observation_dates``: same
    argument shape, same inclusive-bound convention, same ascending tuple of ISO strings, ready
    to hand straight to ``ingestion.backfill.backfill_range``. For the 7 plain-close rows the
    formula sibling can answer for NONE of them — all 7 are ``obs_date``, which it refuses out
    loud — so this is the only honest source of their date lists.

    THE 7 ROWS, AND THE 51 THIS REFUSES. ``ing.column != ""`` is a :class:`ValueError` and not
    a silent fall back to ``close``: 51 of the catalog's 58 ``yahoo`` rows ask for ``adjclose``,
    whose value for a past date drifts retroactively with every later dividend and split,
    forever, so there is no point-in-time quantity for a backfill to recover and therefore no
    honest publication calendar to hand it (PID.md, WO-1.16 scope correction;
    ``ingestion.vintage.NO_REVISION_MECHANISM_COLUMNS`` admits ``close`` and ``""`` for this
    kind and not ``adjclose``). Answering such a caller with the unadjusted close's calendar
    would be the :class:`~ingestion.adapters.YahooChartAdapter` defect it refuses at
    construction, one layer earlier: a date list for a DIFFERENT quantity than the one asked
    about. The refusal names the column so the caller can read why.

    ``range=max`` IS HONOURED AND IS STILL THE WRONG REQUEST, WHICH IS WHY IT WAS MEASURED.
    The live loop's ``range=10d`` (``2y`` with a history) reaches nowhere near a backfill
    episode in 2000, so the deep ask had to be settled rather than assumed. ``max`` is a real
    value — every symbol's own ``meta.validRanges`` lists it and the server echoes
    ``meta.range == "max"`` — but the body it returns is COARSENED, with ``interval=1d``
    silently ignored (measured 2026-10-16, ``evidence/wo117_yahoo_range_probe.json``):

    * ``SPY?range=max&interval=1d`` -> 406 bars at ``dataGranularity == "1mo"``, oldest
      1993-02-01 (its real first trade is 1993-01-29, so even the depth is off by the stub of
      a month);
    * ``^GSPC?range=max&interval=1d`` -> 169 bars at ``"3mo"``, oldest 1984-12-01 — SHALLOWER
      than the same symbol's absolute window, which reaches its real 1927-12-30 first bar.

    A date list read off that body would be month- or quarter-START dates presented as a daily
    publication calendar: a ``200``, plausible, and wrong in the one way this module exists to
    prevent. So the request is an ABSOLUTE ``period1``/``period2`` window over the asked-for
    span, built by :func:`~ingestion.adapters.yahoo_chart_url` — the same builder the live loop
    and the per-date backfill use, so there is ONE way to ask Yahoo for bars and not three.

    AND IT IS ONE GET, NOT A CHUNKED WALK, BECAUSE THE WINDOW KEEPS ``1d`` AT EVERY DEPTH
    MEASURED. The deepest ask any of these 7 rows can make came back whole: ``^GSPC`` over
    1927-01-01..2026-10-15 is 24,815 daily bars in 2,654,167 bytes, ``dataGranularity == "1d"``,
    one response; its 2000-01-01 span (the one WO-1.17's episodes need) is 6,737 bars in
    725,517 bytes, and SPY's whole life 8,486 bars in 851,702. So chunking the span into
    several windows would buy nothing and cost a seam to get wrong. The ceiling is
    :data:`~ingestion.adapters.MAX_BODY_BYTES` (4,000,000) and the widest measured body sits at
    66% of it — at ~107 bytes per bar that ceiling is ~37,000 daily bars, about 148 trading
    years, which no symbol in this catalog approaches. If one ever did,
    :func:`~ingestion.adapters.http_get` raises ``BODY_TOO_LARGE`` and the calendar read FAILS
    rather than returning a truncated list, which is the correct direction for this module.

    THE DATED ASK IS THE DIVERGENCE FROM ITS TWO SIBLINGS, AND IT IS THE ENDPOINT'S DOING.
    :func:`fred_observation_dates` must ask UNDATED because FRED ignores a window lying before
    a series' start and serves the whole body anyway; CBOE has no window to ask for at all.
    Yahoo's window is neither: it is applied exactly or the request is refused outright with a
    clean ``400``, never answered with somebody else's bars
    (``evidence/wo116_yahoo_window_probe.json``, ``q2_window_one_day_utc_day`` and ``q4_*``).
    The arithmetic filter below is kept anyway and is not ceremony: it is the same
    match-on-the-KEY discipline every reader of this body holds, and it is what makes this
    function's answer independent of a server's courtesy — if a future body ever carried a bar
    outside the span asked for (``range=`` silently WINS over a period window in one URL, which
    is why :func:`~ingestion.adapters.yahoo_chart_url` refuses to build both), the bound here
    still holds.

    ``end`` BEFORE ``start`` RETURNS ``()`` WITHOUT A GET, because an empty interval contains no
    dates — arithmetic, not a model of a calendar — and because the alternative is worse: a
    reversed window is a measured ``400`` (``q5_window_reversed``), so the sibling-compatible
    empty answer would otherwise arrive as a fetch failure for a question that answers itself.
    Both bounds are parsed BEFORE the GET, so a bound we cannot read costs no bytes.

    ``ing.history`` is deliberately NOT passed, for this module's stated reason — here it would
    pick ``range=2y`` over the window and silently return a date list that stops at two years
    old. ``today`` is deliberately not applied either, though
    :func:`~ingestion.adapters.parse_yahoo_chart` applies one: that guard exists so a live poll
    cannot store a partial intraday bar as a close, and whether a date too recent to have
    closed may be backfilled is the DRIVER's floor to hold (the same answer
    :func:`~ingestion.adapters.parse_yahoo_chart_for_date` gives), not a date list's to
    second-guess. ``timeout_seconds`` is required and has no default, as for both siblings: a
    26-year window is ~700 KB where a live poll is 2 KB, and the budget belongs to the caller
    that knows which it is asking for.

    ``getter`` is called with the same three positional arguments
    :meth:`~ingestion.adapters._BaseAdapter._acquire` calls it with, and the third is NOT
    ``None`` here as it is for the FRED and CBOE readers: this endpoint answers ``429`` to
    urllib's default agent, so the header is
    :data:`~ingestion.adapters.YAHOO_USER_AGENT` — the identical string
    :meth:`~ingestion.adapters.YahooChartAdapter._headers` sends, from one constant.

    Raises :class:`ValueError` for a kind that is not ``yahoo``, for a column that is not
    ``""``, and for a bound it cannot parse. An
    :class:`~crash_detector.collectors.adapter.AdapterFetchError` from the GET propagates
    UNTOUCHED, including the ``400`` of an impossible window — a window entirely before the
    symbol's first trade, or entirely in the future. That asymmetry is
    :class:`~ingestion.adapters.YahooChartAdapter`'s own and is argued there at length: none of
    those is the source saying anything about a date, each is the REQUEST being wrong, and
    translated into an empty list it would read as "the symbol printed nothing in those years",
    indistinguishable from a quiet stretch of weekends. A symbol whose calendar could not be
    fetched has no date list, and a caller must not be able to mistake that for a symbol that
    never traded.
    """
    if ing.kind != "yahoo":
        raise ValueError(
            f"{ing.source_id} is kind {ing.kind!r}; this reads a Yahoo v8 chart body. The FRED "
            f"and Cboe calendars are read off different bodies by different functions")
    if ing.column != "":
        raise ValueError(
            f"{ing.source_id} asks for column {ing.column!r}, and only the 7 plain-close yahoo "
            f"rows are in scope: an adjusted close drifts retroactively with every later "
            f"dividend and split, so it has no point-in-time value to recover and no honest "
            f"publication calendar to hand a backfill (PID.md, WO-1.16 scope correction)")
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if last < first:
        # An empty interval carries no dates, and asking for it is a measured 400. Argued above.
        return ()
    body = getter(yahoo_chart_url(ing.ref, start=start, end=end), timeout_seconds,
                  {"User-Agent": YAHOO_USER_AGENT})
    published = yahoo_chart_dates(body)
    return tuple(d for d in published if first <= date.fromisoformat(d) <= last)
