"""WO-1.14 THE BACKFILL DRIVER: what one range DOES, date by date, entirely offline.

``ingestion.backfill`` is the only module in the tree that fetches, paces, stores and labels
a historical reading, so these are the tests of the thing that MOVES. Everything here runs
against a throwaway ``SqliteStore`` in ``tmp_path`` and a transport that is a callable in this
file: no socket is opened, no name is resolved, and no wall clock is read — ``CLOCK`` is a
fixed instant, which is what makes "today" a value a test can reason about.

THE ADAPTERS ARE THE REAL ONES. ``_offline`` monkeypatches the driver's *reference* to
``build_backfill_adapter`` with a wrapper that calls the REAL constructor and then replaces
only its ``_getter``. So the routing is the real routing (``ingestion.vintage`` decides), the
URLs are the real URLs, the bisection is the real bisection and the parsers are the real
parsers — the only substitution is the wire. A test that faked the adapter instead would
prove the driver's bookkeeping against an object nothing in production builds.

WHAT EACH SECTION MEASURES

    ONE — the VINTAGE branch backfills a revision-prone series correctly across several
    dates: the figure stored is the one FIRST published (not a later revision), under the
    source period that date claims, labelled ``original``.

    TWO — the STABLE branch ANSWERS FOR THE DATE ASKED, which is what WO-1.15 changed.
    ``FredAdapter`` now windows the request on that one date (``cosd=D&coed=D``) and matches
    the row by EXACT date, so a historical date the body carries comes back under ITS OWN
    source period carrying ITS OWN value — not today's. Four dates spanning 1999 to today
    are all admitted, each under its own key. WO-1.14 measured the OPPOSITE here, because
    the branch then asked for the whole body and read its LATEST row: every historical date
    was reported ``FAILED_DATE_NOT_ANSWERED``, and the one date that admitted was the one
    that is literally today. That limit is closed, so the test that measured it asserts the
    new behaviour rather than being left standing against code that no longer behaves so.

    THREE — a date before ``STABILITY_MEASURED_FROM`` is refused UNFETCHED, the left edge
    itself is not refused, and the rest of the range proceeds.

    FOUR — a re-run of an admitted range issues NO requests. Counted, on the transport.

    FIVE — one date's failure is one date's failure: the range continues and the class is
    carried (the adapter's own ``error_class``, or the store's ``EMPTY`` discriminator).

    SIX — the PARTITION. ``_partitions`` asserts that every date given appears in exactly one
    of the four buckets and that ``counts`` agrees with the tuples, and it is called at the
    end of EVERY test in this file — so the claim is swept across every scenario here rather
    than demonstrated on one. One test additionally drives a single range that lands in all
    four buckets at once.

    SEVEN — a non-FRED kind raises before any date is touched. Measured by an exploding
    adapter builder: if the loop is entered at all, the test fails with its own message.

    EIGHT — the THIRD warrant, added by WO-1.16. ``cboe`` is neither revision-prone nor
    measured stable: it exposes no vintage mechanism AT ALL, so an admitted reading claims
    ``no_revision_mechanism``, and the driver derives that from the KIND without ever
    asking the FRED stability question. Its transport is a static body that ignores every
    parameter, so a date is answered by MATCHING A ROW and by nothing else.

    NINE — the same third warrant reached through a WINDOWED request. ``yahoo`` is the
    other no-revision-mechanism kind and the asymmetry is the point: its endpoint HONOURS an
    absolute window, so the date goes out on the wire and the body is already narrowed on
    arrival, where CBOE's date never leaves the parse. Its gap day is a successful
    ``200`` with the bar arrays absent — not CBOE's missing row and not FRED's 404 — and that
    is the mechanism this section exists to hold. It also holds the one Yahoo row the driver
    must REFUSE: ``adjclose``, a backfillable kind with an unbackfillable column, stopped at
    the label dispatch before a date is touched.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit

import pytest

from crash_detector.collectors import RetryPolicy
from crash_detector.collectors.adapter import AdapterFetchError
from ingestion import backfill as B
from ingestion.backfill import (BACKFILL_PACING_SECONDS, BACKFILL_POLICY,
                                REFUSED_STABILITY_UNMEASURED, backfill_range)
from ingestion.backfill_adapters import VINTAGE_BACKFILLABLE_KINDS
from ingestion.backfill_adapters import build_backfill_adapter as _real_build_backfill_adapter
from ingestion.catalog import INGREDIENTS
from ingestion.store import SqliteStore
from ingestion.vintage import (STABILITY_MEASURED_FROM, VINTAGE_CURRENT_ONLY,
                               VINTAGE_NO_REVISION_MECHANISM, VINTAGE_ORIGINAL)

#: A key-shaped string worth nothing; the real one is never in this tree.
_FAKE_KEY = "k" * 32

#: The instant every clock in this file reads. The ALFRED probe's own date, for no reason
#: other than that it is the date this work order's evidence was gathered on.
NOW = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
CLOCK = lambda: NOW  # noqa: E731
#: ``NOW``'s date as the source would write it. The stable branch's ONE admissible date
#: today, and that is the declared limit rather than a property of this constant.
TODAY = "2026-10-13"

#: The production retry policy with the RETRYING taken out, for the two tests that provoke a
#: transport failure. ``BACKFILL_POLICY`` waits 4 s between its two attempts, and sitting
#: through that would be paying for a property that belongs to
#: ``crash_detector.collectors.collect`` and is tested there. What is being measured here is
#: the driver's bookkeeping for a failed date. ``test_the_shipped_policy_and_pacing_are_the
#: _declared_ones`` asserts the real constant separately, so this substitution cannot hide a
#: change to it.
ONE_ATTEMPT = RetryPolicy(max_attempts=1, timeout_seconds=45.0, backoff_seconds=0.0)


@pytest.fixture
def store(tmp_path):
    with SqliteStore(str(tmp_path / "backfill.sqlite")) as s:
        yield s


def _ing(source_id: str):
    return next(i for i in INGREDIENTS if i.source_id == source_id)


def _offline(monkeypatch, getter):
    """Give the driver the REAL adapter for each date, with ``getter`` as its only transport."""

    def build(ing, observation_date, clock, api_key=None, archive_floors=None):
        adapter = _real_build_backfill_adapter(ing, observation_date, clock, api_key=api_key,
                                               archive_floors=archive_floors)
        adapter._getter = getter
        return adapter

    monkeypatch.setattr(B, "build_backfill_adapter", build)
    return getter


def _no_adapter_may_be_built(monkeypatch):
    """For the refusal test: any attempt to touch a date fails the test by name."""

    def explode(*args, **kwargs):
        raise AssertionError("an adapter was built: a date was touched before the kind check")

    monkeypatch.setattr(B, "build_backfill_adapter", explode)


def _readings(store) -> list:
    """Every admitted reading as ``(source_as_of_utc, payload, vintage)``, oldest period first."""
    return [(as_of, json.loads(payload), vintage) for as_of, payload, vintage in store._db.execute(
        "SELECT source_as_of_utc, payload, vintage FROM raw_reading ORDER BY source_as_of_utc")]


def _attempts(store) -> list:
    """Every attempt row as ``(outcome, source_as_of_utc, error_class)``, in the order written."""
    return list(store._db.execute(
        "SELECT outcome, source_as_of_utc, error_class FROM raw_observation ORDER BY observation_id"))


def _partitions(result, dates) -> None:
    """EVERY date given appears in EXACTLY ONE bucket, and ``counts`` says the same thing.

    Called by every test in this file, which is what makes the partition a swept property
    rather than one example's. The ``dates`` these tests pass carry no duplicates — a date
    asked twice in one range is a legitimate call whose second occurrence is ``skipped``, and
    "exactly one bucket" would then be a claim about occurrences rather than about dates.
    """
    buckets = {
        "admitted": tuple(result.admitted),
        "skipped": tuple(result.skipped),
        "refused": tuple(date for date, _ in result.refused),
        "failed": tuple(date for date, _ in result.failed),
    }
    assert len(set(dates)) == len(dates), "see this helper's docstring on duplicate dates"
    assert sorted(date for bucket in buckets.values() for date in bucket) == sorted(dates)
    for date in dates:
        landed = [name for name, bucket in buckets.items() if date in bucket]
        assert len(landed) == 1, (date, landed)
    expected = {name: len(bucket) for name, bucket in buckets.items()}
    expected["fetches"] = result.fetches
    assert result.counts == expected


# --- the transports, offline ------------------------------------------------------------ #
#
# FOUR fakes, because the four endpoints ask four DIFFERENT questions, and the whole point of
# this file is that the driver treats the answers differently. ``_Cboe`` and ``_Yahoo`` serve
# the same BRANCH and are still two fakes: one cannot be windowed and the other can, which is
# measured rather than chosen. Each fake's behaviour is a PROBED one, named against the evidence file that
# recorded it, rather than a guess at how an HTTP API ought to behave.


class _FredRest:
    """FRED's REST observations endpoint, offline, for the UNTRANSFORMED vintage rows.

    ``observations`` maps an observation date to its revision history as
    ``((vintage_date, value), ...)``, oldest first. A request asks for one observation over a
    ``realtime_start``..``realtime_end`` window and is answered the way the real API answers it
    (``/fred/series/observations``, probed 2026-10-20): one row per DISTINCT vintage, each with the
    validity span of that value clipped to the window, oldest first; an observation this fake has
    never heard of is ``count`` 0 at every vintage, which is "no vintage ever published this figure".
    Only the untransformed shape is modelled here — the transformed rows' single-day bisection is
    tested against its own model in ``tests/test_ingestion.py``.
    """

    def __init__(self, observations, *, fails=(), floor="1990-01-01"):
        self.observations = {obs: list(revisions) for obs, revisions in observations.items()}
        #: The series' ARCHIVE FLOOR as ``/fred/series/vintagedates`` would report it, and how
        #: often it was asked: the driver must ask once per range, not once per date.
        self.floor, self.floor_asked = floor, 0
        #: observation date -> the error class every request about it raises
        self.fails = dict(fails)
        self.asked: list[str] = []

    def observations_asked(self) -> list:
        return [parse_qs(urlsplit(url).query)["observation_start"][0] for url in self.asked]

    def __call__(self, url, timeout, headers=None):
        if urlsplit(url).path.endswith("/vintagedates"):
            self.floor_asked += 1
            asked = parse_qs(urlsplit(url).query)
            return json.dumps({
                "realtime_start": asked["realtime_start"][0], "realtime_end": asked["realtime_end"][0],
                "order_by": "vintage_date", "sort_order": "asc", "count": 1, "offset": 0,
                "limit": 1, "vintage_dates": [self.floor]})
        self.asked.append(url)
        query = parse_qs(urlsplit(url).query)
        observation = query["observation_start"][0]
        opens, closes = query["realtime_start"][0], query["realtime_end"][0]
        if observation in self.fails:
            raise AdapterFetchError(self.fails[observation])
        history = self.observations.get(observation, ())
        rows = []
        for position, (when, value) in enumerate(history):
            until = (date.fromisoformat(history[position + 1][0]) - timedelta(days=1)).isoformat() \
                if position + 1 < len(history) else closes
            start, end = max(when, opens), min(until, closes)
            if start <= end:
                rows.append({"realtime_start": start, "realtime_end": end,
                             "date": observation, "value": value})
        return json.dumps({
            "realtime_start": opens, "realtime_end": closes, "observation_start": observation,
            "observation_end": observation, "units": "lin", "output_type": 1, "file_type": "json",
            "order_by": "observation_date", "sort_order": "asc", "count": len(rows), "offset": 0,
            "limit": 100000, "observations": rows})


class _Fred:
    """``fredgraph.csv``, offline and WINDOW-AWARE — because since WO-1.15 the stable branch's
    request carries a one-day window (``cosd=D&coed=D``) and what the server does with it is
    the whole question.

    FOUR BEHAVIOURS, EVERY ONE OF THEM A PROBED CASE rather than a guess at an HTTP API. Each
    names its case in ``evidence/wo115_fred_window_probe.json`` (``tools/probe/fred_graph_
    window_probe.py``, run 2026-10-15 against the real endpoint):

    * **no window at all** — the WHOLE series, oldest row first and the latest row LAST. The
      live loop's request, unchanged by this work order (``baseline_no_window``).
    * **a window overlapping the series' span** — only the rows inside it, which for a
      one-day window on a date the series HAS is exactly one row (``q1_window_one_day``;
      ``q1_window_multi_day`` is the same rule over nine days, which is what proves the
      window is applied rather than the series answering one row whatever you ask).
    * **a window closing BEFORE ``registered_from``** — the window is IGNORED and the WHOLE
      UNFILTERED SERIES comes back, ``200 OK`` (``q2_window_before_series_start``: DFF asked
      for 1944-07-01 answered with all 26,403 rows, 424 KB). THIS IS THE DANGEROUS CASE. A
      parser reading such a body by POSITION — the last row, or "the only row in the window"
      — answers a 1944 backfill with this morning's rate, under a 1944 key.
    * **a window inside the span that matches no observation** — ``404`` with an HTML error
      page (``extra_window_on_gap_date``: T5YIE on 2015-06-20, a date inside its span and
      absent from its body). NOT ``200`` with a header and no rows, which is the shape a
      convenient fake would have invented; ``FredAdapter`` translates the real 404 into EMPTY
      for a dated request, and a fake sending the wrong shape would test nothing of that.

    ``registered_from`` defaults to the first row's date, so a fake's span IS its rows unless
    a test deliberately widens it to reach the third behaviour above.
    """

    def __init__(self, rows, *, column: str = "DFF", registered_from: str = None):
        self.rows, self.column = list(rows), column
        #: The series' first observation AS THE SERVER KNOWS IT. A window closing before this
        #: is the one the server ignores.
        self.registered_from = registered_from or self.rows[0][0]
        self.asked: list[str] = []

    def _csv(self, rows) -> str:
        lines = [f"observation_date,{self.column}"] + [f"{d},{v}" for d, v in rows]
        return "\n".join(lines) + "\n"

    @property
    def body(self) -> str:
        """The whole unwindowed series, exactly as the live loop's request is answered."""
        return self._csv(self.rows)

    def carries(self, observation_date: str) -> bool:
        return any(date == observation_date for date, _ in self.rows)

    def windows_asked(self) -> list:
        """``(cosd, coed)`` per request in order; ``(None, None)`` for an unwindowed one."""
        windows = []
        for url in self.asked:
            query = parse_qs(urlsplit(url).query)
            windows.append((query.get("cosd", [None])[0], query.get("coed", [None])[0]))
        return windows

    def __call__(self, url, timeout, headers=None):
        self.asked.append(url)
        query = parse_qs(urlsplit(url).query)
        if "cosd" not in query:
            return self.body  # no date in the request: the whole current series
        cosd, coed = query["cosd"][0], query["coed"][0]
        if coed < self.registered_from:
            return self.body  # the window is IGNORED, unfiltered and 200 OK: the dangerous case
        inside = [(date, value) for date, value in self.rows if cosd <= date <= coed]
        if not inside:
            raise AdapterFetchError("HTTP_ERROR", 404)  # no observation in the window
        return self._csv(inside)


class _Cboe:
    """``cdn-api.cboe.com``'s ``{index}_History.csv``, offline — and DELIBERATELY NOT
    window-aware, which is the one way it differs from :class:`_Fred` and the reason it is
    four lines long.

    THE SIMPLICITY IS THE PROBED FINDING, NOT A SHORTCUT. ``tools/probe/cboe_history_probe
    .py`` (run 2026-10-15, ``evidence/wo116_cboe_probe.json``) asked this endpoint with eight
    date-windowing spellings — FRED's ``cosd``/``coed`` among them — plus two negative
    controls, and every single response was BYTE-IDENTICAL to the bare URL's, same SHA-256.
    There is no window to honour and no parameter to branch on, so this fake answers one
    fixed body to every URL it is ever handed. A fake that varied by URL would be asserting
    a behaviour the real server does not have, and would hide the fact that on this branch
    the observation date NEVER REACHES THE WIRE: it is a property of the adapter's parse
    alone (:class:`ingestion.adapters.CboeAdapter`, WO-1.16).

    That also makes the body's LAST ROW the standing hazard, on every request, for every
    date: a parse that read by position would answer each backfilled date with this week's
    close under that date's key. ``_VIX_LATEST_CLOSE`` names that wrong answer so the tests
    below can assert it was available and not taken.
    """

    def __init__(self, body: str):
        self.body = body
        self.asked: list[str] = []

    def rows(self) -> list:
        """``(MM/DD/YYYY, CLOSE)`` per row of the body, as the endpoint serves them."""
        lines = self.body.strip().split("\n")
        header = lines[0].split(",")
        return [(cells[0], cells[header.index("CLOSE")])
                for cells in (line.split(",") for line in lines[1:])]

    def carries(self, mm_dd_yyyy: str) -> bool:
        return any(date == mm_dd_yyyy for date, _ in self.rows())

    def __call__(self, url, timeout, headers=None):
        self.asked.append(url)
        return self.body  # every parameter ignored, every time: the probed behaviour


class _Yahoo:
    """``query1.finance.yahoo.com``'s v8 chart endpoint, offline and WINDOW-AWARE — the one
    way this branch differs from :class:`_Cboe`, and the reason the two WO-1.16 fakes do not
    share a line.

    CBOE CANNOT BE WINDOWED AND YAHOO CAN, both measured. ``_Cboe`` answers one fixed body to
    every URL because the probe found every windowing spelling byte-identical to the bare
    one; here ``period1``/``period2`` are HONOURED, so a one-day window on a real session is
    answered with THAT session's bar and nothing else (``evidence/wo116_yahoo_window_probe
    .json``, ``q1_window_multi_day`` and ``q2_window_one_day_utc_day``, probed 2026-10-15).
    The date therefore reaches the WIRE on this branch and the body is already narrowed when
    it arrives — the opposite of CBOE, where the date lives only in the parse.

    THREE BEHAVIOURS, EACH A PROBED CASE:

    * **a window containing bars** — ``200``, exactly the bars whose session-open stamps lie
      inside it, in stamp order (``q1_window_multi_day``: a wider window really does answer
      wider, which is what proves the window is applied rather than ignored).
    * **a window containing no bar** — ``200`` and ``error: null``, ``meta`` complete, and the
      bar arrays simply ABSENT: no ``timestamp`` key at all and ``"quote":[{}]``
      (``q3_window_on_non_trading_day``, SPY on Saturday 2015-06-13). NOT a 404, NOT a 400,
      and not a neighbouring bar. THIS IS THE SHAPE THE WEEKEND TEST BELOW TURNS ON, and it is
      why :class:`~ingestion.adapters.YahooChartAdapter` needs none of ``FredAdapter``'s
      404-to-EMPTY translation: Yahoo's gap day is representable as a successful answer.
    * **an IMPOSSIBLE window** — ``400``. Reversed (``period2`` before ``period1``,
      ``q5_window_reversed``) or closing entirely before the symbol's first trade
      (``q4_window_before_first_trade_one_day``/``_one_year``). The bound is read out of the
      template's own ``meta.firstTradeDate`` rather than typed. This fake IS capable of a 400
      and the weekend case asserts it issued none — otherwise "a miss, not a transport
      failure" would be a claim about a fake that could not fail in the first place.

    THE BODY IS THE REAL ONE, REBUILT. ``template`` is a verbatim probed response (see
    :data:`_YAHOO_SPY_ONE_UTC_DAY`); every answer is that body with ``timestamp`` and
    ``indicators`` replaced for the window asked about, so ``meta`` — forty-odd keys, a
    ``currentTradingPeriod`` tree, a ``regularMarketPrice`` that is TODAY's — is the real
    thing the parser has to reach past on every single request.

    ``indicators`` carries ``quote`` ONLY, where the served body carries an ``adjclose``
    block beside it. Deliberate, and narrow: the probe records a CLOSE per bar and nothing
    else, so filling an ``adjclose`` array for 2015-06-11 would be making data up, and no
    dated Yahoo fetch may ask for that column anyway — the third test in this section is that
    refusal. A real body's ``adjclose`` block sitting beside the ``quote`` one is exercised
    verbatim by ``tests/test_ingestion.py``'s parser tests, which is where that belongs.

    A request carrying NO window is answered with EVERY bar this fake holds, which is not a
    convenience: it is the shape of the defect ``q6_range_and_period_together`` measured —
    given ``range`` AND a window, range wins and the whole relative body comes back. The
    first test below calls it directly to show the wrong answer was available.
    """

    def __init__(self, bars, template: str):
        #: observation date -> ``(session_open_stamp, close)``, the probe's own figures
        self.bars = dict(bars)
        self.template = template
        #: the symbol's first trade, READ OUT OF the template's meta rather than typed
        self.first_trade = json.loads(template)["chart"]["result"][0]["meta"]["firstTradeDate"]
        self.asked: list[str] = []
        #: the URLs this fake answered 400 to. Asserted EMPTY by the weekend test.
        self.refused: list[str] = []

    def windows_asked(self) -> list:
        """``(period1, period2)`` per request in order, as ints; ``(None, None)`` unwindowed."""
        windows = []
        for url in self.asked:
            query = parse_qs(urlsplit(url).query)
            windows.append(tuple(int(query[p][0]) if p in query else None
                                 for p in ("period1", "period2")))
        return windows

    def carries(self, observation_date: str) -> bool:
        return observation_date in self.bars

    def _body(self, inside) -> str:
        body = json.loads(self.template)
        result = body["chart"]["result"][0]
        result.pop("timestamp", None)
        if not inside:
            # The probed EMPTY shape: no timestamp key anywhere, an empty quote dict.
            result["indicators"] = {"quote": [{}]}
            return json.dumps(body)
        result["timestamp"] = [stamp for stamp, _ in inside]
        result["indicators"] = {"quote": [{"close": [close for _, close in inside]}]}
        return json.dumps(body)

    def __call__(self, url, timeout, headers=None):
        self.asked.append(url)
        query = parse_qs(urlsplit(url).query)
        bars = sorted(self.bars.values())
        if "period1" not in query:
            return self._body(bars)  # the window was dropped: the whole body, q6's hazard
        period1, period2 = int(query["period1"][0]), int(query["period2"][0])
        if period2 < period1 or period2 < self.first_trade:
            self.refused.append(url)
            raise AdapterFetchError("HTTP_ERROR", 400)  # an impossible window, q4/q5
        return self._body([bar for bar in bars if period1 <= bar[0] <= period2])


#: A quarter of GDP, its first publication, and a later revision of the same quarter. The
#: revisions are what make "first published" a claim with a wrong answer available.
_GDP = {
    "2008-09-01": (("2008-10-30", "14412.8"), ("2009-07-31", "14200.2")),
    "2008-12-01": (("2009-01-30", "14200.2"), ("2009-07-31", "14093.0")),
    "2009-03-01": (("2009-04-29", "14075.5"),),
}
_GDP_DATES = ("2008-09-01", "2008-12-01", "2009-03-01")
#: The quarter ENDS those three quarter-START dates claim, by ``as_of_for``'s ``quarter_end``.
_GDP_PERIODS = ["2008-09-30T00:00:00Z", "2008-12-31T00:00:00Z", "2009-03-31T00:00:00Z"]

#: A plausible current DFF body: a row for every date these tests ask for, latest last.
_DFF_ROWS = (("1998-12-31", "4.68"), ("1999-01-01", "4.63"), ("2005-06-15", "3.04"),
             ("2020-03-16", "0.65"), (TODAY, "3.88"))

#: ``VIX_History.csv``, REAL: header and every row copied verbatim out of
#: ``evidence/wo116_cboe_probe.json`` (``rows_for_month_verbatim`` for 2015-06, then
#: ``rows_tail``), so the body under test is the body the endpoint actually serves —
#: ``MM/DD/YYYY`` dates, six-decimal figures, and four columns of which one is asked for.
#: ``tests/test_ingestion.py`` holds the same rows for the PARSER's unit tests; this copy is
#: the driver's, kept local because every transport in this file is (see the module
#: docstring), and both name the same evidence file as their source.
#:
#: 2015-06-13 and 06-14 were a WEEKEND and are simply ABSENT — CBOE publishes no
#: missing-data marker, so "no figure for this date" arrives as a missing row. That gap is
#: what the miss test below drives, and it is the probe's finding rather than a hole
#: punched to make a test convenient.
_VIX_BODY = (
    "DATE,OPEN,HIGH,LOW,CLOSE\n"
    "06/11/2015,13.040000,13.220000,12.560000,12.850000\n"
    "06/12/2015,13.310000,14.020000,13.300000,13.780000\n"
    "06/15/2015,15.480000,15.570000,14.910000,15.390000\n"
    "06/16/2015,15.620000,15.620000,14.810000,14.810000\n"
    "10/13/2026,15.610000,15.610000,15.170000,15.270000\n"
    "10/14/2026,15.170000,17.450000,14.980000,16.870000\n"
)
#: The CLOSE on the body's LAST row — the figure a read-by-position would put under every
#: backfilled date's key. The wrong answer, named, so it can be asserted absent.
_VIX_LATEST_CLOSE = 16.87


#: A Yahoo v8 chart response, REAL: copied verbatim out of ``evidence/wo116_yahoo_window_
#: probe.json`` (``q2_window_one_day_utc_day``, SPY asked for the whole UTC day of
#: 2015-06-08). :class:`_Yahoo` uses it as the TEMPLATE every answer is rebuilt from, so the
#: ``meta`` block every request in this section is answered with is the served one, down to
#: the ``regularMarketPrice`` of 770.01 that is this morning's figure sitting inside a 2015
#: body. ``tests/test_ingestion.py`` holds the same body for the PARSER's unit tests; this
#: copy is the driver's, kept local because every transport in this file is (see the module
#: docstring), and both name the same evidence file as their source.
_YAHOO_SPY_ONE_UTC_DAY = (
    '{"chart":{"result":[{"meta":{"currency":"USD","symbol":"SPY","exchangeName":"PCX","fullExcha'
    'ngeName":"NYSEArca","instrumentType":"ETF","firstTradeDate":728317800,"regularMarketTime":17'
    '92089976,"hasPrePostMarketData":true,"gmtoffset":-14400,"timezone":"EDT","exchangeTimezoneNa'
    'me":"America/New_York","regularMarketPrice":770.01,"regularMarketChangePercent":0.053,"fulld'
    'ayPrice":770.01,"fulldayChange":0.41,"fulldayChangePercent":0.053,"fiftyTwoWeekHigh":781.62,'
    '"fiftyTwoWeekLow":629.28,"regularMarketDayHigh":771.91,"regularMarketDayLow":764.44,"regular'
    'MarketVolume":26568391,"longName":"State Street SPDR S&P 500 ETF Trust","shortName":"State S'
    'treet SPDR S&P 500 ETF T","chartPreviousClose":209.77,"priceHint":2,"currentTradingPeriod":{'
    '"pre":{"timezone":"EDT","start":1792051200,"end":1792071000,"gmtoffset":-14400},"regular":{"'
    'timezone":"EDT","start":1792071000,"end":1792094400,"gmtoffset":-14400},"post":{"timezone":"'
    'EDT","start":1792094400,"end":1792108800,"gmtoffset":-14400}},"dataGranularity":"1d","range"'
    ':"","validRanges":["1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"]},"timestamp'
    '":[1433770200],"indicators":{"quote":[{"close":[208.47999572753906],"high":[209.820007324218'
    '75],"low":[208.38999938964844],"volume":[89063300],"open":[209.63999938964844]}],"adjclose":'
    '[{"adjclose":[172.54739379882812]}]}}],"error":null}}'
)

#: Ten real SPY sessions as ``date -> (session_open_stamp, close)``, lifted bar for bar out of
#: the probe's ``q1_window_multi_day`` answer for 2015-06-08..2015-06-19. The stamps are the
#: endpoint's own: 1433770200 is 2015-06-08T13:30Z, the session OPEN on summer time, which is
#: the whole reason the adapter's window is the UTC DAY and not a zero-width point at
#: midnight.
#:
#: 2015-06-13 and 06-14 were a WEEKEND and are ABSENT, exactly as they are absent from
#: ``_VIX_BODY`` — the same two days, so the two WO-1.16 branches are measured against the
#: same real gap arriving in their two different shapes: a missing ROW from CBOE, and from
#: Yahoo a successful response with the bar arrays gone.
_SPY_BARS = {
    "2015-06-08": (1433770200, 208.47999572753906),
    "2015-06-09": (1433856600, 208.4499969482422),
    "2015-06-10": (1433943000, 210.9499969482422),
    "2015-06-11": (1434029400, 211.6300048828125),
    "2015-06-12": (1434115800, 210.00999450683594),
    "2015-06-15": (1434375000, 209.11000061035156),
    "2015-06-16": (1434461400, 210.25),
    "2015-06-17": (1434547800, 210.58999633789062),
    "2015-06-18": (1434634200, 212.77999877929688),
    "2015-06-19": (1434720600, 210.80999755859375),
}
#: The close on the LAST bar the fake holds — the figure every date would be answered with if
#: the window were dropped and the body read by position (``q6_range_and_period_together``:
#: emit ``range`` beside a window and range wins). ``_VIX_LATEST_CLOSE``'s counterpart: the
#: wrong answer, named, so it can be asserted absent.
_SPY_CLOSE_IF_THE_WINDOW_WERE_DROPPED = 210.80999755859375
#: The probed window for Saturday 2015-06-13, verbatim from ``q3_window_on_non_trading_day``'s
#: URL. The weekend test asserts the adapter emitted exactly this.
_SATURDAY_WINDOW = (1434153600, 1434239999)


# --- ONE: the vintage branch, across several dates -------------------------------------- #


def test_a_revision_prone_series_backfills_the_figure_as_first_published_across_several_dates(
        store, monkeypatch):
    """GDP is measured revision-prone, so each date's first-published figure is read from FRED's REST vintage history.

    The assertion that matters is the VALUE: 14412.8 is what the 2008 Q3 figure said when it
    was first published and 14200.2 is what it says now, and a backfill that stored the
    second has committed the forgery this work order exists to prevent.
    """
    rest = _offline(monkeypatch, _FredRest(_GDP))
    result = backfill_range(_ing("fred.GDP"), _GDP_DATES, store, CLOCK, pace=0, api_key=_FAKE_KEY)

    assert result.source_id == "fred.GDP" and result.vintage == VINTAGE_ORIGINAL
    assert result.admitted == _GDP_DATES
    assert result.counts == {"admitted": 3, "skipped": 0, "refused": 0, "failed": 0, "fetches": 3}
    readings = _readings(store)
    assert [as_of for as_of, _, _ in readings] == _GDP_PERIODS
    assert [payload["value"] for _, payload, _ in readings] == [14412.8, 14200.2, 14075.5]
    assert [payload["vintage_date"] for _, payload, _ in readings] == [
        "2008-10-30", "2009-01-30", "2009-04-29"]
    assert [payload["observation_date"] for _, payload, _ in readings] == list(_GDP_DATES)
    # The label is on the row, written at INSERT, and it is `original` because a vintage was
    # really read: these are the figures the source itself first published.
    assert {vintage for _, _, vintage in readings} == {VINTAGE_ORIGINAL}
    # One fetch per date, each a bisection; every date this fake was asked about was asked for.
    assert sorted(set(rest.observations_asked())) == sorted(_GDP_DATES)
    _partitions(result, _GDP_DATES)


def test_a_range_asks_the_archive_floor_once_and_the_date_first_kept_at_it_is_not_admitted(
        store, monkeypatch):
    """WO-1.17 follow-up. 2008-09-01's first vintage (2008-10-30) is declared the series' archive
    floor: that figure was first KEPT there, not first published there. The other two dates are
    admitted untouched, and the floor is ONE request for the range, not one per date."""
    rest = _offline(monkeypatch, _FredRest(_GDP, floor="2008-10-30"))
    result = backfill_range(_ing("fred.GDP"), _GDP_DATES, store, CLOCK, pace=0, api_key=_FAKE_KEY)
    assert result.admitted == ("2008-12-01", "2009-03-01")
    assert result.failed == (("2008-09-01", "MALFORMED"),)
    assert [payload["value"] for _, payload, _ in _readings(store)] == [14200.2, 14075.5]
    assert rest.floor_asked == 1, "the floor is a property of the series: asked once per range"
    assert sorted(set(rest.observations_asked())) == sorted(_GDP_DATES)


def test_the_later_revision_is_present_in_the_fake_and_is_the_answer_nobody_stored(
        store, monkeypatch):
    """The negative half of the test above: the wrong answer was AVAILABLE and was not taken."""
    rest = _offline(monkeypatch, _FredRest(_GDP))
    backfill_range(_ing("fred.GDP"), ("2008-09-01",), store, CLOCK, pace=0, api_key=_FAKE_KEY)
    today_s_body = rest("https://x/?series_id=GDP&realtime_start=2026-10-13&realtime_end=2026-10-13"
                        "&observation_start=2008-09-01", 1.0)
    assert "14200.2" in today_s_body  # what GDP says about 2008 Q3 NOW
    assert _readings(store)[0][1]["value"] == 14412.8  # what it said THEN


def test_a_vintage_range_handed_no_key_raises_before_any_date_is_touched(store, monkeypatch):
    """A missing credential is a fact about the WHOLE range: one raise, not a thousand identical
    failed dates. No adapter is built, nothing is fetched, nothing is written."""
    _no_adapter_may_be_built(monkeypatch)
    with pytest.raises(ValueError) as refused:
        backfill_range(_ing("fred.GDP"), _GDP_DATES, store, CLOCK, pace=0)
    assert "api_key" in str(refused.value)
    assert _readings(store) == [] and _attempts(store) == []


def test_the_key_reaches_the_request_and_is_recorded_nowhere_in_the_store(store, monkeypatch):
    """The credential travels in the URL the transport is handed and in NOTHING the run writes:
    not a payload, not an attempt row, not a failure class (PBG-SEC-002)."""
    monkeypatch.setattr(B, "BACKFILL_POLICY", ONE_ATTEMPT)
    rest = _offline(monkeypatch, _FredRest(_GDP, fails={"2008-12-01": "CONNECTION_FAILED"}))
    result = backfill_range(_ing("fred.GDP"), _GDP_DATES, store, CLOCK, pace=0, api_key=_FAKE_KEY)
    assert all(parse_qs(urlsplit(url).query)["api_key"] == [_FAKE_KEY] for url in rest.asked)
    dump = json.dumps([list(row) for row in store._db.execute(
        "SELECT * FROM raw_observation")] + [list(row) for row in store._db.execute(
            "SELECT * FROM raw_reading")]) + repr(result)
    assert _FAKE_KEY not in dump and "api_key" not in dump


def test_a_stable_or_keyless_range_needs_no_key_and_is_not_asked_for_one(store, monkeypatch):
    """Only the revision-prone FRED rows read the keyed endpoint; DFF (measured stable) runs
    exactly as before with ``api_key`` left at its default."""
    fred = _Fred([(TODAY, "3.64")], column="DFF")
    _offline(monkeypatch, fred)
    result = backfill_range(_ing("fred.DFF"), (TODAY,), store, CLOCK, pace=0)
    assert result.vintage == VINTAGE_CURRENT_ONLY and result.admitted == (TODAY,)


# --- TWO: the stable branch, answering for the date asked -------------------------------- #


def test_a_stable_series_answers_each_historical_date_under_its_own_period(
        store, monkeypatch):
    """WO-1.15, MEASURED. Dates all at or after ``STABILITY_MEASURED_FROM``, a body that
    carries a row for every one of them — and EVERY ONE is admitted, each under the source
    period ITS date claims, each carrying the figure the body holds for THAT date.

    This is the test WO-1.14's declared limit used to own, and the limit is gone. Then, the
    stable branch asked for the whole current body and read its LATEST row, so all three
    historical dates came back answering for TODAY's period and were reported
    ``FAILED_DATE_NOT_ANSWERED``; only the date that is literally today admitted. Now the
    request carries a one-day window and the row is matched by EXACT date, so the 1999 key
    holds the 1999 rate.

    THE VALUES ARE THE ASSERTION THAT MATTERS, not the bucket counts. 4.63 is what
    ``_DFF_ROWS`` says for 1999-01-01 and 3.88 is what it says for today; a branch that
    still read the body by position would put 3.88 under all four keys — the exact forgery
    this work order closes — and it would sail through a test that only counted admissions.
    """
    dates = ("1999-01-01", "2005-06-15", "2020-03-16", TODAY)
    assert all(date >= STABILITY_MEASURED_FROM for date in dates)
    fred = _offline(monkeypatch, _Fred(_DFF_ROWS))
    result = backfill_range(_ing("fred.DFF"), dates, store, CLOCK, pace=0)

    # ``current_only`` is still the right label: the RIGHT period, but today's revision of
    # it. Windowing the request changed which period is answered, not which vintage.
    assert result.vintage == VINTAGE_CURRENT_ONLY
    assert result.admitted == dates
    assert result.failed == () and result.refused == () and result.skipped == ()
    assert result.fetches == 4  # one windowed GET per date; none was refused or skipped
    assert all(fred.carries(date) for date in dates)
    # EVERY REQUEST CARRIED ITS DATE, as a window on that single day. The old limit was that
    # none of them did — the URL was bare, and a bare URL cannot ask about a particular day.
    assert fred.windows_asked() == [(date, date) for date in dates]

    # FOUR readings, each under the period its date claims (``obs_date`` for DFF), each with
    # its own value out of the body, all labelled current_only.
    assert _readings(store) == [
        ("1999-01-01T00:00:00Z",
         {"unit": "percent", "observation_date": "1999-01-01", "value": 4.63},
         VINTAGE_CURRENT_ONLY),
        ("2005-06-15T00:00:00Z",
         {"unit": "percent", "observation_date": "2005-06-15", "value": 3.04},
         VINTAGE_CURRENT_ONLY),
        ("2020-03-16T00:00:00Z",
         {"unit": "percent", "observation_date": "2020-03-16", "value": 0.65},
         VINTAGE_CURRENT_ONLY),
        (f"{TODAY}T00:00:00Z",
         {"unit": "percent", "observation_date": TODAY, "value": 3.88},
         VINTAGE_CURRENT_ONLY)]
    # The forgery, named and measured: today's rate appears under TODAY's key and nowhere
    # else. This is the assertion that would have failed before WO-1.15, four times over.
    assert [as_of for as_of, payload, _ in _readings(store)
            if payload["value"] == 3.88] == [f"{TODAY}T00:00:00Z"]
    # Four OK attempts, each recorded against the period it answered for.
    assert _attempts(store) == [("OK", f"{date}T00:00:00Z", None) for date in dates]
    _partitions(result, dates)


def test_a_date_before_the_stability_measurement_is_refused_unfetched_and_the_range_goes_on(
        store, monkeypatch):
    """The left edge is INCLUSIVE, so the refusal is the day before it and that day costs no GET.

    ``STABILITY_MEASURED_FROM`` is where the measurement that authorises the stable branch
    begins; before it, today's body is not evidence about the date and there is no vintage to
    fall back on here. 1998-12-31 is therefore refused rather than failed — a date nobody
    fetched is not a date that failed — and 1999-01-01, the edge itself, is fetched AND
    ADMITTED, under its own period.

    THE REFUSAL IS WHAT THIS TEST OWNS AND WO-1.15 DID NOT TOUCH IT. The floor is a property
    of ``ingestion.vintage``'s measurement window, not of how the branch asks its question —
    so closing ``FredAdapter``'s limit moved the edge date from ``failed`` to ``admitted``
    and left the day before it refused, unfetched, exactly as it was. The body carries a row
    for 1998-12-31 too, which is what makes the refusal the FLOOR's doing and not the fake's.
    """
    assert STABILITY_MEASURED_FROM == "1999-01-01"
    dates = ("1998-12-31", "1999-01-01", TODAY)
    fred = _offline(monkeypatch, _Fred(_DFF_ROWS))
    result = backfill_range(_ing("fred.DFF"), dates, store, CLOCK, pace=0)

    assert result.refused == (("1998-12-31", REFUSED_STABILITY_UNMEASURED),)
    assert result.fetches == 2 and len(fred.asked) == 2  # UNFETCHED, counted on the transport
    assert len(_attempts(store)) == 2  # and no attempt row names the refused date either
    # The refused date is in the body and was still never asked about: the two windows are
    # the two dates that passed the floor, and neither of them is 1998-12-31.
    assert fred.carries("1998-12-31")
    assert fred.windows_asked() == [("1999-01-01", "1999-01-01"), (TODAY, TODAY)]
    # The rest of the range proceeded, and since WO-1.15 the edge gets a real answer for its
    # OWN period rather than a reported miss: nothing failed here at all.
    assert result.failed == ()
    assert result.admitted == ("1999-01-01", TODAY)
    assert [as_of for as_of, _, _ in _readings(store)] == [
        "1999-01-01T00:00:00Z", f"{TODAY}T00:00:00Z"]
    _partitions(result, dates)


# --- FOUR: a re-run of a finished range is free ------------------------------------------ #


def test_re_running_an_admitted_range_skips_every_date_and_issues_no_request_at_all(
        store, monkeypatch):
    """``fetches == 0``, counted on the transport as well as reported. This is the property
    that makes a 6,000-date backfill resumable: a range already half-done costs GETs only for
    the half that is missing."""
    rest = _offline(monkeypatch, _FredRest(_GDP))
    first = backfill_range(_ing("fred.GDP"), _GDP_DATES, store, CLOCK, pace=0, api_key=_FAKE_KEY)
    assert first.admitted == _GDP_DATES
    probes, attempts = len(rest.asked), len(_attempts(store))

    again = backfill_range(_ing("fred.GDP"), _GDP_DATES, store, CLOCK, pace=0, api_key=_FAKE_KEY)

    assert again.skipped == _GDP_DATES
    assert again.counts == {"admitted": 0, "skipped": 3, "refused": 0, "failed": 0, "fetches": 0}
    assert len(rest.asked) == probes      # not one more GET
    assert len(_attempts(store)) == attempts  # and not one more attempt row
    assert [as_of for as_of, _, _ in _readings(store)] == _GDP_PERIODS  # still three readings
    _partitions(again, _GDP_DATES)


# --- FIVE: one date's failure is one date's failure --------------------------------------- #


def test_a_transport_failure_on_one_date_carries_its_class_and_stops_nothing(store, monkeypatch):
    """The middle date's fetch fails; the first and last are admitted, and the class recorded
    is the adapter's own ``error_class`` — no message, no URL, no exception text."""
    monkeypatch.setattr(B, "BACKFILL_POLICY", ONE_ATTEMPT)
    rest = _offline(monkeypatch, _FredRest(_GDP, fails={"2008-12-01": "CONNECTION_FAILED"}))
    result = backfill_range(_ing("fred.GDP"), _GDP_DATES, store, CLOCK, pace=0, api_key=_FAKE_KEY)

    assert result.admitted == ("2008-09-01", "2009-03-01")
    assert result.failed == (("2008-12-01", "CONNECTION_FAILED"),)
    assert result.fetches == 3  # the failure was a fetch, and the range continued past it
    assert [as_of for as_of, _, _ in _readings(store)] == [_GDP_PERIODS[0], _GDP_PERIODS[2]]
    assert ("FETCH_FAILED", None, "CONNECTION_FAILED") in _attempts(store)
    assert "2009-03-01" in rest.observations_asked()  # the date AFTER the failure was asked
    _partitions(result, _GDP_DATES)


def test_an_answer_that_is_not_a_reading_is_a_failed_date_with_the_stores_own_class(
        store, monkeypatch):
    """Neither EMPTY nor MALFORMED is a date this backfill HAS, which is what ``failed`` records
    — and the class carried is the store's own discriminator, not a vocabulary invented here.

    * ``2009-06-01`` — ALFRED served every vintage and none carried this figure. EMPTY is a
      real ANSWER (the observation was never published), and it still leaves a gap.
    * ``2030-06-01`` — an observation that HAS NOT HAPPENED. ``FredVintageAdapter`` refuses
      it as MALFORMED without probing anything, rather than searching an empty window; the
      driver reports the refusal under that date and carries on.
    """
    dates = ("2008-09-01", "2009-06-01", "2030-06-01")
    rest = _offline(monkeypatch, _FredRest(_GDP))
    result = backfill_range(_ing("fred.GDP"), dates, store, CLOCK, pace=0, api_key=_FAKE_KEY)

    assert result.admitted == ("2008-09-01",)
    assert result.failed == (("2009-06-01", "EMPTY"), ("2030-06-01", "MALFORMED"))
    outcomes = [outcome for outcome, _, _ in _attempts(store)]
    assert outcomes == ["OK", "EMPTY", "MALFORMED"]
    assert len(_readings(store)) == 1
    assert "2009-06-01" in rest.observations_asked()        # really searched for
    assert "2030-06-01" not in rest.observations_asked()    # and this one never asked at all
    _partitions(result, dates)


# --- SIX: the partition, over a range that lands in all four buckets ---------------------- #


def test_one_range_lands_in_all_four_buckets_and_they_partition_the_dates_given(
        store, monkeypatch):
    """SAHMREALTIME is measured stable and FRED dates it ``month_end``, which is what lets one
    range reach all four answers:

    * ``1998-01-01`` — before the measurement's left edge: REFUSED, unfetched;
    * ``2005-06-01`` — windowed on itself and matched by exact date: ADMITTED, under the
      JUNE period (``month_end``) rather than under the date asked;
    * ``2005-07-01`` — a date INSIDE the series' span that the body has no row for. FRED
      answers such a window with ``404`` and an HTML error page rather than ``200`` and an
      empty body (probed: ``evidence/wo115_fred_window_probe.json``, case
      ``extra_window_on_gap_date``), and ``FredAdapter`` translates that into EMPTY for a
      dated request. A gap is a real ANSWER and it is still a date this backfill does not
      have: FAILED, carrying the store's own ``EMPTY`` discriminator, nothing stored;
    * ``2026-10-01`` — the current month, whose period is capped at today: ADMITTED;
    * ``2026-10-05`` — the SAME source period (``month_end``, capped at today), already
      admitted by the line above: SKIPPED, unfetched.

    The last pair is not a contrivance — two dates in one month ARE one source period, and
    that is exactly what ``skipped`` means.

    WHY THE ``failed`` CASE IS A GAP DATE NOW AND NOT A PERIOD MISMATCH. WO-1.14 manufactured
    this bucket out of its own limitation: ``2005-06-01`` was fetched, the body answered for
    TODAY, and the driver's date gate reported ``FAILED_DATE_NOT_ANSWERED``. WO-1.15 closed
    that, and closed it thoroughly enough that the gate can no longer be reached through the
    stable branch BY ANY BODY THE SERVER MIGHT SEND — ``ingestion.backfill`` and
    ``_BaseAdapter.fetch`` derive the key from the same ``as_of_for(D, rule, clock())``, and
    ``parse_fred_csv_for_date`` guarantees the payload's date IS ``D``, so only a clock that
    moved between those two calls could separate the two keys. The gate is still live code
    and is still right to keep (``ingestion.backfill`` says why: it guards WHICHEVER adapter
    answered, against a later parser or transformation that shifts a period), but exercising
    it now needs a deliberately period-shifting ADAPTER, which this file does not build — see
    its own docstring on why it substitutes only the transport. So the ``failed`` bucket here
    is the gap date, which is the stable branch's REAL failure mode, and
    ``FAILED_DATE_NOT_ANSWERED`` is left OWED a test rather than reached by a contrivance
    that would prove nothing about anything production builds.
    """
    dates = ("1998-01-01", "2005-06-01", "2005-07-01", "2026-10-01", "2026-10-05")
    rows = (("1998-01-01", "0.03"), ("2005-06-01", "-0.13"), ("2026-10-01", "0.27"))
    sahm = _offline(monkeypatch, _Fred(rows, column="SAHMREALTIME"))
    result = backfill_range(_ing("fred.SAHMREALTIME"), dates, store, CLOCK, pace=0)

    assert result.refused == (("1998-01-01", REFUSED_STABILITY_UNMEASURED),)
    assert result.failed == (("2005-07-01", "EMPTY"),)
    assert result.admitted == ("2005-06-01", "2026-10-01")
    assert result.skipped == ("2026-10-05",)
    assert result.counts == {"admitted": 2, "skipped": 1, "refused": 1, "failed": 1, "fetches": 3}
    assert len(sahm.asked) == 3  # the refusal and the skip each cost nothing
    # The gap date really was asked for, and asked for as a window on itself: the EMPTY is
    # the server's 404 translated, not this fake quietly declining to carry a row.
    assert not sahm.carries("2005-07-01")
    assert ("2005-07-01", "2005-07-01") in sahm.windows_asked()
    # 2005-06-01's reading is under the JUNE period — the window is what makes a historical
    # month answerable at all, and ``month_end`` is what decides the key it lands under.
    assert [as_of for as_of, _, _ in _readings(store)] == [
        "2005-06-30T00:00:00Z", f"{TODAY}T00:00:00Z"]
    # The gap is in the record as the EMPTY attempt it was; only the reading is absent.
    assert [outcome for outcome, _, _ in _attempts(store)] == ["OK", "EMPTY", "OK"]
    _partitions(result, dates)


def test_the_pace_falls_between_fetches_only_and_never_around_a_refusal_or_a_skip(
        store, monkeypatch):
    """The courtesy gap is a gap between REQUESTS. This range issues two, so there is one
    gap: not one before the first fetch, and none for the two dates that touched no network."""
    slept: list = []
    monkeypatch.setattr(B.time, "sleep", slept.append)
    dates = ("1998-01-01", "2005-06-01", "2026-10-01", "2026-10-05")
    rows = (("1998-01-01", "0.03"), ("2005-06-01", "-0.13"), ("2026-10-01", "0.27"))
    _offline(monkeypatch, _Fred(rows, column="SAHMREALTIME"))

    result = backfill_range(_ing("fred.SAHMREALTIME"), dates, store, CLOCK, pace=0.01)

    assert result.fetches == 2 and slept == [0.01]
    _partitions(result, dates)


def test_the_shipped_policy_and_pacing_are_the_declared_ones(store):
    """So that ``ONE_ATTEMPT`` above cannot quietly become the thing production uses."""
    assert (BACKFILL_POLICY.max_attempts, BACKFILL_POLICY.timeout_seconds,
            BACKFILL_POLICY.backoff_seconds) == (2, 45.0, 4.0)
    assert BACKFILL_PACING_SECONDS == 0.7


# --- SEVEN: a kind that cannot be backfilled is refused before any date ------------------- #


def test_an_undeclared_kind_raises_before_a_single_date_is_touched(store, monkeypatch):
    """One defect about the whole range, reported once — not buried under a thousand identical
    per-date failures. Measured by an adapter builder that fails the test if it is reached at
    all, so the refusal is proved to come BEFORE the loop and not from inside it.

    The set is DERIVED from ``VINTAGE_BACKFILLABLE_KINDS``, not typed: WO-1.16 declared
    ``cboe`` and then ``yahoo`` backfillable, and a test that listed "every kind except fred"
    would have had to be edited twice to keep asserting a boundary that had moved underneath
    it.

    ``manual`` HAS ALSO LEFT THIS SET, for an unrelated reason and in the other direction
    (WO-1.19): no ingredient has that kind any more. Its one row was ``sloos_bank_lending``'s
    second leg, a SLOOS table scrape nobody could automate, and it was retired when ``DRTSCIS``
    made the same figure a FRED feed. The kind is gone from the catalog, not moved into
    ``VINTAGE_BACKFILLABLE_KINDS``, so there is nothing left here to refuse.

    ``lbma`` LEFT IT THE SAME WAY AT WO-1.20. Its one row was ``gold_real_rate_cross``'s gold
    leg — an endpoint that answered HTTP 403 to this host for the whole of its life — and it was
    retired when the futures close ``yahoo.GC=F.history`` took the role the ratified row had
    named all along. Catalog row, adapter and egress host are all gone, so again there is
    nothing of that kind left to refuse; it was not moved into ``VINTAGE_BACKFILLABLE_KINDS``.

    WHAT THIS TEST NO LONGER COVERS, SO THE GAP IS NOT SILENT. ``yahoo`` has left this set,
    and its 51 ``adjclose`` rows are refused by a DIFFERENT mechanism at a different place —
    they are a backfillable KIND with an unbackfillable COLUMN, so they reach the label
    dispatch and stop the range there rather than failing this kind check. That refusal is
    held by ``tests/test_vintage_declaration.py``
    (``test_no_adjclose_ingredient_can_be_labelled_no_revision_mechanism``, door 4) and by
    ``tests/test_wo114.py`` at the adapter constructor. Widening this assertion to cover them
    would be asserting the wrong boundary.
    """
    _no_adapter_may_be_built(monkeypatch)
    others = [ing for ing in INGREDIENTS if ing.kind not in VINTAGE_BACKFILLABLE_KINDS]
    assert {ing.kind for ing in others} == {"multpl", "hermes"}

    for ing in others:
        with pytest.raises(ValueError, match="point-in-time backfill is declared only for"):
            backfill_range(ing, ("1998-01-01", "2005-06-01", TODAY), store, CLOCK, pace=0)

    assert _attempts(store) == [] and _readings(store) == []


# --- EIGHT: the no-revision-mechanism branch, end to end --------------------------------- #


def test_a_source_with_no_revision_mechanism_backfills_each_date_under_its_own_label(
        store, monkeypatch):
    """WO-1.16, MEASURED THROUGH THE DRIVER. Four real 2015 VIX sessions, each admitted under
    the period ITS date claims, each carrying the close the body holds for THAT date — and
    every stored row labelled ``no_revision_mechanism``.

    THE LABEL IS THE ASSERTION THAT MATTERS, and it is read back OFF THE ROW rather than off
    the in-memory result, because the label is written at INSERT and the row is what any
    later reader of this store will see. ``no_revision_mechanism`` is a THIRD warrant, and
    neither of the other two would be true here: ``original`` is mechanism-earned and no
    vintage was read (CBOE serves none); ``current_only`` rests on a positive stability
    MEASUREMENT and none was made for this source. Both of those are available labels that a
    careless branch could reach, which is why both are asserted against by name.

    THE SECOND ASSERTION IS THE FORGERY, as it is on the FRED branch: the body's last row is
    this week's close and it is present in every single response, so a parse that read by
    position would put 16.87 under all four 2015 keys. It appears under none of them.
    """
    dates = ("2015-06-11", "2015-06-12", "2015-06-15", "2015-06-16")
    cboe = _offline(monkeypatch, _Cboe(_VIX_BODY))
    result = backfill_range(_ing("cboe.VIX"), dates, store, CLOCK, pace=0)

    assert result.source_id == "cboe.VIX"
    assert result.vintage == VINTAGE_NO_REVISION_MECHANISM
    assert result.vintage not in (VINTAGE_ORIGINAL, VINTAGE_CURRENT_ONLY)
    assert result.admitted == dates
    assert result.counts == {"admitted": 4, "skipped": 0, "refused": 0, "failed": 0, "fetches": 4}

    # Four rows, one per date, each under its own period (``obs_date``), each with its own
    # close — and THE LABEL ON THE ROW, which is the thing WO-1.16 adds.
    assert _readings(store) == [
        ("2015-06-11T00:00:00Z",
         {"unit": "index", "observation_date": "2015-06-11", "value": 12.85},
         VINTAGE_NO_REVISION_MECHANISM),
        ("2015-06-12T00:00:00Z",
         {"unit": "index", "observation_date": "2015-06-12", "value": 13.78},
         VINTAGE_NO_REVISION_MECHANISM),
        ("2015-06-15T00:00:00Z",
         {"unit": "index", "observation_date": "2015-06-15", "value": 15.39},
         VINTAGE_NO_REVISION_MECHANISM),
        ("2015-06-16T00:00:00Z",
         {"unit": "index", "observation_date": "2015-06-16", "value": 14.81},
         VINTAGE_NO_REVISION_MECHANISM)]
    assert {vintage for _, _, vintage in _readings(store)} == {VINTAGE_NO_REVISION_MECHANISM}

    # THE WRONG ANSWER WAS AVAILABLE ON EVERY RESPONSE AND WAS TAKEN NONE OF THE FOUR TIMES.
    assert cboe.rows()[-1] == ("10/14/2026", "16.870000")  # it really is in the body served
    assert _VIX_LATEST_CLOSE not in [payload["value"] for _, payload, _ in _readings(store)]

    # THE DATE NEVER REACHED THE WIRE, and could not have: the URL is bare and identical on
    # all four requests. This is the branch's defining difference from WO-1.15's FRED one,
    # where the date goes out as ``cosd``/``coed`` — here it lives only in the parse.
    assert len(cboe.asked) == 4 and len(set(cboe.asked)) == 1
    assert urlsplit(cboe.asked[0]).query == ""
    assert cboe.asked[0].endswith("/VIX_History.csv")

    assert _attempts(store) == [("OK", f"{date}T00:00:00Z", None) for date in dates]
    _partitions(result, dates)


def test_a_date_the_static_body_has_no_row_for_is_a_clean_miss_and_the_range_goes_on(
        store, monkeypatch):
    """The CBOE shape of "the source has no figure for this date": an ABSENT ROW.

    2015-06-13 and 06-14 were a weekend. CBOE publishes no missing-data marker — no
    FRED-style ``.``, no blank cell — so a non-session is not a row with nothing in it, it is
    no row at all, and the two of them are consecutive, which is the ordinary case a real
    range walks into roughly two days in seven.

    IT IS A MISS, NOT A TRANSPORT FAILURE, and the distinction is the whole reason
    ``CboeAdapter`` does NOT translate 404 the way ``FredAdapter`` does. The body for a gap
    date ARRIVES, intact and complete — it simply has no row for that date. So the fetch
    happens (``fetches == 4``, four requests on the transport), the attempt is recorded under
    the store's own EMPTY discriminator, nothing is stored, and the next date is admitted
    normally. A gap costs the range one request and nothing else.
    """
    dates = ("2015-06-12", "2015-06-13", "2015-06-14", "2015-06-15")
    cboe = _offline(monkeypatch, _Cboe(_VIX_BODY))
    result = backfill_range(_ing("cboe.VIX"), dates, store, CLOCK, pace=0)

    assert result.vintage == VINTAGE_NO_REVISION_MECHANISM
    assert result.admitted == ("2015-06-12", "2015-06-15")
    assert result.failed == (("2015-06-13", "EMPTY"), ("2015-06-14", "EMPTY"))
    assert result.refused == () and result.skipped == ()

    # The gap dates were really ASKED FOR — fetched, answered, and found to have no row.
    assert result.fetches == 4 and len(cboe.asked) == 4
    assert not cboe.carries("06/13/2015") and not cboe.carries("06/14/2015")
    assert [outcome for outcome, _, _ in _attempts(store)] == ["OK", "EMPTY", "EMPTY", "OK"]

    # NOTHING STORED FOR THE GAP, and the date after it is admitted under its own period with
    # its own value — the range walked straight through two consecutive misses.
    assert _readings(store) == [
        ("2015-06-12T00:00:00Z",
         {"unit": "index", "observation_date": "2015-06-12", "value": 13.78},
         VINTAGE_NO_REVISION_MECHANISM),
        ("2015-06-15T00:00:00Z",
         {"unit": "index", "observation_date": "2015-06-15", "value": 15.39},
         VINTAGE_NO_REVISION_MECHANISM)]
    _partitions(result, dates)


def test_the_driver_derives_the_label_from_the_kind_and_never_asks_the_fred_question(
        store, monkeypatch):
    """``requires_original_vintage`` IS NOT CONSULTED for a no-revision-mechanism kind, and
    this measures the DRIVER's reference to it specifically.

    It is a separate site from the one ``test_wo114.py`` already covers. That test explodes
    the function under ``ingestion.backfill_adapters`` and proves the ROUTING never asks it;
    ``ingestion.backfill`` imports its OWN reference to decide the LABEL, and the three-way
    branch added by WO-1.16 dispatches on the kind BEFORE reaching it. So this explodes
    ``backfill``'s reference and nothing else, and names the claim narrowly for that reason.

    WHY IT MUST NOT BE ASKED RATHER THAN MERELY NEED NOT BE: the function answers from
    ``REVISION_STABLE``, a table of FRED series, and ``("VIX", None)`` is not in it — so it
    would return ``True`` and the range would claim ``original``, the label reserved for a
    figure read from a real vintage. A confident wrong answer, not an error, which is the
    failure mode ``VINTAGE_NO_REVISION_MECHANISM`` exists to make impossible.
    """
    def explode(*args, **kwargs):
        raise AssertionError("the driver asked the FRED stability question about a cboe kind")

    monkeypatch.setattr(B, "requires_original_vintage", explode)
    _offline(monkeypatch, _Cboe(_VIX_BODY))
    result = backfill_range(_ing("cboe.VIX"), ("2015-06-15",), store, CLOCK, pace=0)

    assert result.admitted == ("2015-06-15",)
    assert result.vintage == VINTAGE_NO_REVISION_MECHANISM
    assert _readings(store) == [
        ("2015-06-15T00:00:00Z",
         {"unit": "index", "observation_date": "2015-06-15", "value": 15.39},
         VINTAGE_NO_REVISION_MECHANISM)]
    _partitions(result, ("2015-06-15",))


# --- NINE: the same warrant, reached through a WINDOWED request --------------------------- #


def test_a_windowed_no_revision_mechanism_source_backfills_each_session_under_its_own_label(
        store, monkeypatch):
    """WO-1.16's OTHER branch, measured through the driver. The same four 2015 dates the CBOE
    test asks for, asked of ``yahoo.SPY`` instead — each admitted under the period ITS date
    claims, each carrying the close the probe recorded for THAT session, every stored row
    labelled ``no_revision_mechanism``.

    THE LABEL IS STILL THE ASSERTION THAT MATTERS and it is still read back OFF THE ROW, for
    the reasons the CBOE test gives. Both of the other two warrants are available to a
    careless branch and neither would be true: ``original`` is mechanism-earned and Yahoo
    serves no vintage at all, ``current_only`` rests on a positive stability MEASUREMENT and
    none was made for this symbol. Both are asserted against by name.

    WHAT IS NEW HERE AND IS NOT A RESTATEMENT OF THE CBOE TEST: **the date reaches the wire.**
    CBOE's four requests were one identical bare URL and the date lived only in the parse;
    here each request carries its own absolute ``period1``/``period2`` window — four
    DISTINCT URLs, no ``range`` parameter on any of them — so the body is already narrowed
    when it arrives and the parse's exact-date match is the second line of defence rather
    than the only one. ``range`` being absent is itself load-bearing and measured: given both,
    range WINS and the window is silently ignored (``q6_range_and_period_together``).

    THE FORGERY, AS ON BOTH OTHER BRANCHES. The fake holds ten sessions through 2015-06-19,
    and a request that dropped the window is answered with all ten — which is exactly what a
    body built with ``range`` beside the window looks like. The test CALLS the transport that
    way to show the wrong answer was there to be taken: 210.80999755859375 under all four
    2015 keys. It appears under none of them.
    """
    dates = ("2015-06-11", "2015-06-12", "2015-06-15", "2015-06-16")
    yahoo = _offline(monkeypatch, _Yahoo(_SPY_BARS, _YAHOO_SPY_ONE_UTC_DAY))
    result = backfill_range(_ing("yahoo.SPY"), dates, store, CLOCK, pace=0)

    assert result.source_id == "yahoo.SPY"
    assert result.vintage == VINTAGE_NO_REVISION_MECHANISM
    assert result.vintage not in (VINTAGE_ORIGINAL, VINTAGE_CURRENT_ONLY)
    assert result.admitted == dates
    assert result.counts == {"admitted": 4, "skipped": 0, "refused": 0, "failed": 0, "fetches": 4}

    # Four rows, one per date, each under its own period (``obs_date``), each with its own
    # close — and THE LABEL ON THE ROW. ``history`` is not carried: a one-day window has one
    # bar in it, which ingestion.backfill_adapters records as the declared limit.
    assert _readings(store) == [
        ("2015-06-11T00:00:00Z",
         {"unit": "usd", "observation_date": "2015-06-11", "value": 211.6300048828125},
         VINTAGE_NO_REVISION_MECHANISM),
        ("2015-06-12T00:00:00Z",
         {"unit": "usd", "observation_date": "2015-06-12", "value": 210.00999450683594},
         VINTAGE_NO_REVISION_MECHANISM),
        ("2015-06-15T00:00:00Z",
         {"unit": "usd", "observation_date": "2015-06-15", "value": 209.11000061035156},
         VINTAGE_NO_REVISION_MECHANISM),
        ("2015-06-16T00:00:00Z",
         {"unit": "usd", "observation_date": "2015-06-16", "value": 210.25},
         VINTAGE_NO_REVISION_MECHANISM)]
    assert {vintage for _, _, vintage in _readings(store)} == {VINTAGE_NO_REVISION_MECHANISM}

    # THE DATE WENT OUT ON THE WIRE, one window per date, and no ``range`` beside it.
    assert len(yahoo.asked) == 4 and len(set(yahoo.asked)) == 4
    assert yahoo.windows_asked() == [(1433980800, 1434067199),   # 2015-06-11, whole UTC day
                                     (1434067200, 1434153599),   # 2015-06-12
                                     (1434326400, 1434412799),   # 2015-06-15
                                     (1434412800, 1434499199)]   # 2015-06-16
    for url in yahoo.asked:
        assert "range=" not in url, url
        assert "interval=1d" in url and "/chart/SPY?" in url

    # THE WRONG ANSWER WAS AVAILABLE AND WAS TAKEN NONE OF THE FOUR TIMES. Asked WITHOUT a
    # window — the q6 shape — this very transport answers with all ten bars, ending here.
    unwindowed = json.loads(yahoo("https://query1.finance.yahoo.com/v8/finance/chart/SPY", 1.0))
    bars = unwindowed["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    assert len(bars) == 10 and bars[-1] == _SPY_CLOSE_IF_THE_WINDOW_WERE_DROPPED
    assert _SPY_CLOSE_IF_THE_WINDOW_WERE_DROPPED not in [
        payload["value"] for _, payload, _ in _readings(store)]

    assert _attempts(store) == [("OK", f"{date}T00:00:00Z", None) for date in dates]
    _partitions(result, dates)


def test_a_non_trading_day_is_a_clean_miss_through_the_two_hundred_and_empty_path(
        store, monkeypatch):
    """THE YAHOO SHAPE of "the source has no figure for this date", and it is the THIRD such
    shape in this file — which is the reason this test is the one that matters most here.

    THREE SOURCES, THREE MECHANISMS, ONE OUTCOME:

    * FRED answers a one-day window on a gap date with ``404`` and an HTML error page, so
      :class:`~ingestion.adapters.FredAdapter` TRANSLATES that 404 into EMPTY;
    * CBOE serves a body with no ROW for the date and no missing-data marker, so
      :class:`~ingestion.adapters.CboeAdapter` finds no key to match;
    * Yahoo answers ``200``, ``error: null``, a complete ``meta`` — and the bar arrays simply
      ABSENT: no ``timestamp`` key, ``"quote":[{}]``
      (``evidence/wo116_yahoo_window_probe.json``, ``q3_window_on_non_trading_day``).

    So this is a SUCCESSFUL FETCH that answered "nothing printed that day", and
    :class:`~ingestion.adapters.YahooChartAdapter` translates nothing to reach that — it needs
    no carve-out of FRED's kind because the shape is already a clean one.

    THAT IT IS NOT A 400 IS ASSERTED, NOT ASSUMED, AND IT IS THE POINT OF THE TEST. A 400 on
    this endpoint is reachable only by an IMPOSSIBLE window — reversed, or wholly before the
    symbol's first trade — and translating one to EMPTY would make a date that HAS NOT
    HAPPENED indistinguishable from a quiet Saturday, which is the asymmetry
    ``YahooChartAdapter``'s docstring argues at length. The fake is capable of issuing that
    400 (:class:`_Yahoo` raises it for both probed cases), so ``yahoo.refused == []`` is a
    real measurement rather than a property of a transport that could not fail. The recorded
    outcome is the store's own EMPTY discriminator, and no attempt carries ``HTTP_ERROR``.

    2015-06-13 and 06-14 are the SAME weekend the CBOE test walks, deliberately: one real gap,
    arriving at the driver in two different shapes, costing the range one request each and
    nothing else.
    """
    dates = ("2015-06-12", "2015-06-13", "2015-06-14", "2015-06-15")
    yahoo = _offline(monkeypatch, _Yahoo(_SPY_BARS, _YAHOO_SPY_ONE_UTC_DAY))
    result = backfill_range(_ing("yahoo.SPY"), dates, store, CLOCK, pace=0)

    assert result.vintage == VINTAGE_NO_REVISION_MECHANISM
    assert result.admitted == ("2015-06-12", "2015-06-15")
    assert result.failed == (("2015-06-13", "EMPTY"), ("2015-06-14", "EMPTY"))
    assert result.refused == () and result.skipped == ()

    # The gap dates were really ASKED FOR — fetched, answered, and found to hold no bar.
    assert result.fetches == 4 and len(yahoo.asked) == 4
    assert not yahoo.carries("2015-06-13") and not yahoo.carries("2015-06-14")
    assert yahoo.windows_asked()[1] == _SATURDAY_WINDOW  # the probed window, to the second

    # A SUCCESSFUL FETCH, NOT A TRANSPORT FAILURE. No 400 was issued, none of the four
    # attempts carries a transport class, and the Saturday's body really is the probed EMPTY
    # shape: 200-worth of JSON with error null, meta intact, and the bar arrays gone.
    assert yahoo.refused == []
    assert [outcome for outcome, _, _ in _attempts(store)] == ["OK", "EMPTY", "EMPTY", "OK"]
    assert {error_class for _, _, error_class in _attempts(store)} == {None}
    saturday = json.loads(yahoo(
        f"https://query1.finance.yahoo.com/v8/finance/chart/SPY?period1={_SATURDAY_WINDOW[0]}"
        f"&period2={_SATURDAY_WINDOW[1]}&interval=1d", 1.0))
    result_block = saturday["chart"]["result"][0]
    assert saturday["chart"]["error"] is None
    assert "timestamp" not in result_block and result_block["indicators"] == {"quote": [{}]}
    assert result_block["meta"]["symbol"] == "SPY"  # the body ARRIVED, whole

    # NOTHING STORED FOR THE GAP, and the date after it is admitted under its own period with
    # its own value — the range walked straight through two consecutive misses. Neither
    # neighbour's close was borrowed for the Saturday, which a window read by position would
    # have done.
    assert _readings(store) == [
        ("2015-06-12T00:00:00Z",
         {"unit": "usd", "observation_date": "2015-06-12", "value": 210.00999450683594},
         VINTAGE_NO_REVISION_MECHANISM),
        ("2015-06-15T00:00:00Z",
         {"unit": "usd", "observation_date": "2015-06-15", "value": 209.11000061035156},
         VINTAGE_NO_REVISION_MECHANISM)]
    _partitions(result, dates)


def test_an_adjclose_ingredient_is_refused_by_the_driver_before_a_single_date_is_touched(
        store, monkeypatch):
    """THE ROW THIS BRANCH MUST NOT ADMIT, refused at ``backfill_range``'s OWN ENTRY POINT.

    ``private_credit_stress``'s ``yahoo.BIZD.adj`` and all 50 rows of
    ``constituent_breadth_200dma``'s sample ask for ``adjclose`` deliberately, and a dated
    read of that field has no point-in-time meaning at all: it is restated backwards by every
    dividend and split, forever (PID.md WO-1.16 scope correction). ``yahoo`` being in
    :data:`~ingestion.backfill_adapters.VINTAGE_BACKFILLABLE_KINDS` is not a statement about
    these rows, and the two tests above are what that tuple DOES say.

    WHY THIS EXISTS WHEN TWO OTHER TESTS ALREADY HOLD THE SAME RULE — it is reached through a
    different door, and WHICH door fires is the finding. ``tests/test_wo114.py``
    (``test_an_adjclose_yahoo_ingredient_is_refused_rather_than_handed_a_working_adapter``)
    calls ``build_backfill_adapter`` directly and measures the ADAPTER CONSTRUCTOR's raise.
    ``tests/test_vintage_declaration.py`` (door 4) measures the LABEL DISPATCH with no store
    at all. This one goes in the way a real caller does — the real driver function, a real
    ``SqliteStore``, real catalog rows — and what it finds is that the label dispatch gets
    there FIRST: the range stops before the loop, so no adapter is ever constructed and the
    constructor's refusal is never reached. Hence the message asserted is the dispatch's
    (``no vintage label is derived``) and the adapter's own words are asserted ABSENT. Two
    independent doors, and from this entrance the outer one is the one that shuts.

    MEASURED THE WAY SECTION SEVEN MEASURES ITS REFUSAL: an adapter builder that fails the
    test by name if it is reached at all, which proves "before a single date is touched"
    rather than describing it — and the store is then asserted untouched, which proves no row
    was written on the way out.

    AND IT IS NOT THE KIND CHECK. ``yahoo`` really is in that tuple, asserted here, so this
    refusal cannot be section SEVEN's wearing a different name; if the kind ever leaves the
    tuple this test is measuring the wrong door and says so.
    """
    _no_adapter_may_be_built(monkeypatch)
    assert "yahoo" in VINTAGE_BACKFILLABLE_KINDS, (
        "yahoo has left VINTAGE_BACKFILLABLE_KINDS: this test would now be measuring the "
        "kind-level refusal of section SEVEN, not the label dispatch"
    )
    adj = [ing for ing in INGREDIENTS if ing.kind == "yahoo" and ing.column == "adjclose"]
    assert len(adj) == 51 and "yahoo.BIZD.adj" in {ing.source_id for ing in adj}, (
        "the adjclose ingredients have changed shape — re-reason this guard"
    )

    for ing in adj:
        with pytest.raises(ValueError) as caught:
            backfill_range(ing, ("2015-06-11", "2015-06-12", "2015-06-15"), store, CLOCK, pace=0)
        assert "no vintage label is derived" in str(caught.value), ing.source_id
        # NOT the adapter constructor's refusal: no adapter was built to raise it.
        assert "adjclose has no" not in str(caught.value), ing.source_id

    assert _attempts(store) == [] and _readings(store) == []
