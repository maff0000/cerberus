"""WO-1.17 the date-list readers: they READ a calendar they do not model, and refuse bodies.

``ingestion.backfill_calendar`` closes the FRED half (13 rows) and the CBOE half (3 rows) of
the gap
``WO-1.17-COST-ESTIMATE.md`` §3 names — 13 ``obs_date`` ingredient rows with no date source in
the tree. The thing worth testing is not that it can filter a list; it is that the list comes
off the BODY. So every test here hands it a crafted body through a fake transport, and the
bodies carry the shapes a modelled calendar gets wrong: a Good Friday the exchange closes for
and FRED does not, a Columbus Day FRED skips and the exchange trades, a holiday row present
with FRED's ``.`` for no figure, and a series whose span starts well inside the window asked
for.

THE WINDOW IS TESTED AGAINST A BODY THAT IGNORES IT, which is not a contrivance: FRED ignores a
``cosd``/``coed`` window lying before a series' first observation and returns everything
(``evidence/wo115_fred_window_probe.json``). The request this module issues is UNDATED, so the
whole body is always what arrives and the bound is arithmetic here — these tests pin that the
arithmetic, not the server, is what excludes a date.

THE CBOE SECTION AT THE FOOT OF THIS FILE tests the same discipline against a body with a
DIFFERENT shape — ``MM/DD/YYYY`` dates, a header width that varies by index, and no
missing-data marker at all — using rows copied verbatim out of
``evidence/wo116_cboe_probe.json``. There the server ignoring the window is not a quirk but
the only behaviour available: ``cdn-api.cboe.com`` honours no windowing parameter whatsoever,
so the arithmetic bound is the entire mechanism.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from crash_detector.collectors.adapter import AdapterFetchError
from ingestion.adapters import (CboeAdapter, FredAdapter, cboe_history_url, fred_column,
                                fred_graph_url)
from ingestion.backfill_calendar import (cboe_body_dates, cboe_observation_dates,
                                         fred_body_dates, fred_observation_dates)
from ingestion.backfill_dates import observation_dates
from ingestion.catalog import INGREDIENTS

NOW = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)

#: The 13 rows §3 counts as having no date source. Named here rather than filtered silently so
#: the population this round claims to cover is visible in the test file.
FRED_OBS_DATE_ROWS = tuple(i.source_id for i in INGREDIENTS
                           if i.kind == "fred" and i.as_of_rule == "obs_date")


def _ing(source_id: str):
    return next(i for i in INGREDIENTS if i.source_id == source_id)


def _body(column: str, rows) -> str:
    """A ``fredgraph.csv`` body: the real header shape, then ``date,value`` lines."""
    return "\n".join([f"observation_date,{column}"] + [f"{d},{v}" for d, v in rows]) + "\n"


def _serves(body: str):
    """A fake transport with the adapters' three-positional-argument signature."""
    calls = []

    def getter(url, timeout_seconds, headers=None):
        calls.append((url, timeout_seconds, headers))
        return body

    getter.calls = calls
    return getter


# --- the population, and that it is the one §3 named ------------------------------------ #


def test_the_thirteen_fred_obs_date_rows_are_the_rows_with_no_other_date_source():
    """§3's arithmetic, re-derived from the catalog: 13 rows no formula can answer for."""
    assert len(FRED_OBS_DATE_ROWS) == 13
    for source_id in FRED_OBS_DATE_ROWS:
        with pytest.raises(ValueError):
            observation_dates(_ing(source_id), "2020-01-01", "2020-12-31")


def test_one_series_can_carry_two_ingredient_rows_so_the_calendar_is_per_pair():
    """``fred.DFII10`` and ``fred.DFII10.history`` are one FRED series. The URL is the same for
    both — which is WHY the module says caching is the caller's business and keeps no state."""
    plain, history = _ing("fred.DFII10"), _ing("fred.DFII10.history")
    assert plain.ref == history.ref and plain.history != history.history
    assert (fred_graph_url(plain.ref, plain.transformation)
            == fred_graph_url(history.ref, history.transformation))


# --- the URL: one builder, and the live loop's destination is unmoved -------------------- #


def test_the_calendar_asks_the_same_undated_url_the_live_adapter_has_always_asked():
    """THE NON-REGRESSION, by EQUALITY rather than by substring. ``fred_graph_url`` was lifted
    out of ``FredAdapter._url`` this round; if the lift changed a character, the live collector
    is asking a different endpoint and this fails."""
    adapter = FredAdapter("DFF", None, source_id="fred.DFF", as_of_rule="obs_date",
                          unit="percent", clock=lambda: NOW)
    assert adapter._url() == fred_graph_url("DFF") == (
        "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF")
    # Every live FRED row, including the transformed ones, still builds what the adapter builds.
    for ing in (i for i in INGREDIENTS if i.kind == "fred"):
        live = FredAdapter(ing.ref, ing.transformation, ing.history, source_id=ing.source_id,
                           as_of_rule=ing.as_of_rule, unit=ing.unit, clock=lambda: NOW)
        assert live._url() == fred_graph_url(ing.ref, ing.transformation)
        # And the COLUMN the adapter insists on is the one the calendar reader expects, held by
        # feeding the adapter a body built from ``fred_column``: if the two drifted, one of the
        # two readers of this body would be calling it MALFORMED.
        column = fred_column(ing.ref, ing.transformation)
        assert live._parse(_body(column, [("2026-10-15", "1.5")]))["value"] == 1.5


def test_the_dated_mode_url_is_unmoved_too_and_the_calendar_never_asks_for_it():
    """The window belongs to the BACKFILL's per-date read. The calendar read must not carry one:
    a windowed request is a question about one date, and this is a question about all of them."""
    dated = FredAdapter("T5YIE", None, observation_date="2015-06-22", source_id="fred.T5YIE",
                        as_of_rule="obs_date", unit="percent", clock=lambda: NOW)
    assert dated._url() == fred_graph_url("T5YIE", observation_date="2015-06-22") == (
        "https://fred.stlouisfed.org/graph/fredgraph.csv?id=T5YIE"
        "&cosd=2015-06-22&coed=2015-06-22")
    assert "cosd" not in fred_graph_url("T5YIE")

    getter = _serves(_body("T5YIE", [("2015-06-22", "1.84")]))
    fred_observation_dates(_ing("fred.T5YIE"), "2015-06-01", "2015-06-30",
                           timeout_seconds=45.0, getter=getter)
    url, timeout, headers = getter.calls[0]
    assert len(getter.calls) == 1, "the calendar is ONE GET per series (§3 costs it as 13)"
    assert "cosd" not in url and "coed" not in url and url == fred_graph_url("T5YIE")
    assert (timeout, headers) == (45.0, None)


def test_a_transformed_row_reads_the_transformed_body_because_that_is_a_different_calendar():
    """``pc1`` has no row until a year after the series starts. Asking for the untransformed
    body would hand the backfill dates its own request cannot answer for."""
    ing = _ing("fred.CPIAUCSL.pc1")
    getter = _serves(_body(fred_column(ing.ref, ing.transformation),
                           [("1948-01-01", "10.2"), ("1948-02-01", "9.3")]))
    assert fred_observation_dates(ing, "1947-01-01", "1948-12-31",
                                  timeout_seconds=45.0, getter=getter) == (
        "1948-01-01", "1948-02-01")
    assert "transformation=pc1" in getter.calls[0][0]
    # And the header it insists on is the transformed one: the untransformed body is refused.
    with pytest.raises(ValueError, match="not 'CPIAUCSL_PC1'"):
        fred_observation_dates(ing, "1947-01-01", "1948-12-31", timeout_seconds=45.0,
                               getter=_serves(_body("CPIAUCSL", [("1948-01-01", "23.7")])))


# --- the calendar is READ, not modelled -------------------------------------------------- #


def test_the_dates_are_the_bodys_dates_including_the_ones_a_holiday_model_gets_wrong():
    """A real business-daily week straddling Good Friday and Columbus Day.

    2015-04-03 is Good Friday: the NYSE is shut and FRED, on the FEDERAL calendar, publishes.
    2015-10-12 is Columbus Day: FRED is shut and the NYSE trades. A single modelled calendar is
    wrong about both; the body is right about both, and that is the whole argument for reading
    it. 2015-04-06 is the Monday after, present and published."""
    rows = [("2015-04-01", "0.12"), ("2015-04-02", "0.13"), ("2015-04-03", "0.13"),
            ("2015-04-06", "0.12"),
            ("2015-10-09", "0.12"), ("2015-10-13", "0.11")]
    dates = fred_observation_dates(_ing("fred.DFF"), "2015-01-01", "2015-12-31",
                                   timeout_seconds=45.0, getter=_serves(_body("DFF", rows)))
    assert dates == ("2015-04-01", "2015-04-02", "2015-04-03", "2015-04-06",
                     "2015-10-09", "2015-10-13")
    assert "2015-04-03" in dates, "Good Friday: FRED publishes, an NYSE model would skip it"
    assert "2015-10-12" not in dates, "Columbus Day: FRED does not, an NYSE model would ask"


def test_a_row_present_with_fred_s_dot_is_not_a_publication_date():
    """The holiday shape FRED actually serves for some daily series: the date is in the body
    carrying ``.``. Asking the backfill for it buys a recorded EMPTY, so it is not a date."""
    rows = [("2015-12-24", "0.24"), ("2015-12-25", "."), ("2015-12-28", "0.20"),
            ("2015-12-29", "")]
    assert fred_observation_dates(_ing("fred.DFF"), "2015-12-01", "2015-12-31",
                                  timeout_seconds=45.0,
                                  getter=_serves(_body("DFF", rows))) == (
        "2015-12-24", "2015-12-28")


def test_a_weekly_series_calendar_is_its_own_weekday_and_its_own_skips():
    """``IC4WSA`` is dated Saturdays. The model in §3 would assume a fixed weekday and never see
    the skip; the body carries both facts and this asserts neither is invented."""
    rows = [("2020-02-29", "216750"), ("2020-03-07", "212500"), ("2020-03-21", "998000")]
    dates = fred_observation_dates(_ing("fred.IC4WSA"), "2020-02-01", "2020-03-31",
                                   timeout_seconds=45.0, getter=_serves(_body("IC4WSA", rows)))
    assert dates == ("2020-02-29", "2020-03-07", "2020-03-21")
    assert all(date.fromisoformat(d).weekday() == 5 for d in dates)
    assert "2020-03-14" not in dates, "a week the body skips is not a week we may invent"


def test_a_value_that_is_not_a_number_is_still_a_publication_date():
    """The question is whether the series published, and it did. Judging the figure belongs to
    the backfill's read and to the closed response schema, not to a date list."""
    assert fred_observation_dates(_ing("fred.DFF"), "2015-01-01", "2015-12-31",
                                  timeout_seconds=45.0,
                                  getter=_serves(_body("DFF", [("2015-07-01", "NaN")]))) == (
        "2015-07-01",)


def test_the_body_order_is_not_relied_on():
    """FRED serves oldest row first. The result is sorted rather than trusting that."""
    rows = [("2015-07-02", "0.13"), ("2015-07-01", "0.12"), ("2015-07-06", "0.14")]
    assert fred_body_dates(_body("DFF", rows), "DFF") == (
        "2015-07-01", "2015-07-02", "2015-07-06")


# --- the window: an exact bound on the dates, applied HERE ------------------------------- #


def test_dates_outside_the_window_are_excluded_from_a_body_that_carries_the_whole_series():
    """The case §3 and the WO-1.15 probe both warn about: the server returned EVERYTHING. The
    bound has to be ours, and it is inclusive at both ends."""
    rows = [("2007-01-02", "5.25"), ("2007-04-02", "5.26"), ("2007-09-04", "5.02"),
            ("2008-01-02", "4.27"), ("2009-12-31", "0.12"), ("2010-01-04", "0.11"),
            ("2026-10-15", "4.08")]
    dates = fred_observation_dates(_ing("fred.DFF"), "2007-04-02", "2009-12-31",
                                   timeout_seconds=45.0, getter=_serves(_body("DFF", rows)))
    assert dates == ("2007-04-02", "2007-09-04", "2008-01-02", "2009-12-31")
    assert "2007-01-02" not in dates and "2010-01-04" not in dates
    assert "2026-10-15" not in dates, "today's row rode in on an undated body and is not in 2008"


def test_a_window_entirely_before_the_series_starts_is_empty_and_not_the_whole_body():
    """The exact failure the window probe found at the SERVER. Here it is arithmetic, so a 2000
    window against a series beginning in 2003 is empty rather than 'all of it'."""
    rows = [("2003-01-02", "98.1"), ("2003-01-03", "98.3")]
    assert fred_observation_dates(_ing("fred.DTWEXBGS"), "2000-01-01", "2002-12-31",
                                  timeout_seconds=45.0,
                                  getter=_serves(_body("DTWEXBGS", rows))) == ()


def test_an_empty_window_is_an_empty_tuple_and_not_an_error():
    """``backfill_range`` of no dates does nothing, which is a fine answer to 'did this series
    publish in this fortnight'. Reversed bounds are the same, as in ``observation_dates``."""
    getter = _serves(_body("DFF", [("2015-07-01", "0.12")]))
    assert fred_observation_dates(_ing("fred.DFF"), "2016-01-01", "2016-01-14",
                                  timeout_seconds=45.0, getter=getter) == ()
    assert fred_observation_dates(_ing("fred.DFF"), "2016-01-01", "2015-01-01",
                                  timeout_seconds=45.0, getter=getter) == ()


def test_a_bound_we_cannot_read_is_refused_before_a_byte_is_fetched():
    getter = _serves(_body("DFF", [("2015-07-01", "0.12")]))
    for start, end in (("not-a-date", "2015-12-31"), ("2015-01-01", "2015-13-01")):
        with pytest.raises(ValueError):
            fred_observation_dates(_ing("fred.DFF"), start, end,
                                   timeout_seconds=45.0, getter=getter)
    assert getter.calls == [], "a bound we cannot parse must not cost a GET"


# --- where it agrees with the formula, and where it refuses ------------------------------ #


def test_it_agrees_with_the_formula_on_a_row_both_can_answer_for():
    """``observation_dates`` states that FRED dates a MONTHLY series at the first of the month.
    A body read here must reproduce that, because it is the same convention seen from the other
    side — if the two ever disagree, one of them is wrong about FRED and that is worth a
    failing test rather than a quiet divergence."""
    ing = _ing("fred.UMCSENT")
    rows = [(d, "61.3") for d in ("2026-05-01", "2026-06-01", "2026-07-01", "2026-08-01")]
    read = fred_observation_dates(ing, "2026-05-01", "2026-08-31", timeout_seconds=45.0,
                                  getter=_serves(_body("UMCSENT", rows)))
    assert read == observation_dates(ing, "2026-05-01", "2026-08-31")


def test_a_non_fred_ingredient_is_refused_and_costs_no_get():
    """CBOE's ``*_History.csv`` and Yahoo's chart JSON are their own calendars read by their own
    functions — ``cboe_observation_dates`` below, and Yahoo in a later round. Handing either
    body to the FRED reader must not produce a plausible-looking list."""
    getter = _serves("anything")
    others = [i for i in INGREDIENTS if i.kind != "fred"]
    assert {i.kind for i in others} >= {"cboe", "yahoo"}, "the later rounds' kinds are absent"
    for ing in others:
        with pytest.raises(ValueError, match="fredgraph.csv body"):
            fred_observation_dates(ing, "2020-01-01", "2020-12-31",
                                   timeout_seconds=45.0, getter=getter)
    assert getter.calls == []


def test_a_fetch_failure_propagates_and_is_never_an_empty_date_list():
    """The deliberate asymmetry with ``FredAdapter``'s DATED mode, which turns a 404 into EMPTY.
    An undated request makes no claim about a particular date, so there is nothing here for a
    404 to mean except 'no calendar' — and a caller must not read that as 'published nothing'."""
    def refused(url, timeout_seconds, headers=None):
        raise AdapterFetchError("HTTP_ERROR", 404)

    with pytest.raises(AdapterFetchError) as raised:
        fred_observation_dates(_ing("fred.DFF"), "2015-01-01", "2015-12-31",
                               timeout_seconds=45.0, getter=refused)
    assert raised.value.error_class == "HTTP_ERROR" and raised.value.http_status == 404


# --- a body we cannot read stops the run --------------------------------------------------#


def test_a_body_that_is_not_this_series_is_refused_rather_than_read():
    with pytest.raises(ValueError, match="not 'DFF'"):
        fred_body_dates(_body("T10Y2Y", [("2015-07-01", "1.5")]), "DFF")


@pytest.mark.parametrize("body", [
    "",
    "<!DOCTYPE html><html>FRED error page</html>",
    "observation_date\n2015-07-01\n",
    "observation_date,DFF,extra\n2015-07-01,0.12,x\n",
])
def test_a_body_that_is_not_a_fredgraph_csv_at_all_is_refused(body):
    with pytest.raises(ValueError, match="not a fredgraph.csv body"):
        fred_body_dates(body, "DFF")


def test_a_malformed_row_raises_where_the_sibling_parsers_would_skip_it():
    """``parse_fred_csv`` skips a row it cannot read because it is hunting the LATEST good one.
    Here a skipped row is a date never asked for, in a run whose output is which dates were
    recovered — a hole with nothing to compare it against. So the body is refused whole."""
    with pytest.raises(ValueError, match="line 3 .* 3 cells"):
        fred_body_dates("observation_date,DFF\n2015-07-01,0.12\n2015-07-02,0.13,0.14\n", "DFF")
    with pytest.raises(ValueError, match="which is not a date"):
        fred_body_dates("observation_date,DFF\n2015-07-01,0.12\n07/02/2015,0.13\n", "DFF")


def test_a_date_carried_twice_is_refused_rather_than_silently_halved():
    with pytest.raises(ValueError, match="carries 2015-07-01 twice"):
        fred_body_dates(_body("DFF", [("2015-07-01", "0.12"), ("2015-07-01", "0.13")]), "DFF")


def test_a_conforming_body_with_no_observations_is_empty_and_not_an_error():
    """The one thing an empty tuple is allowed to mean: a body we fully understood, with
    nothing in it. Distinct from every refusal above, which is why those all raise."""
    assert fred_body_dates("observation_date,DFF\n", "DFF") == ()
    assert fred_body_dates(_body("DFF", [("2015-07-01", ".")]), "DFF") == ()


# =========================================================================================== #
# CBOE: the same discipline, a different body                                                 #
# =========================================================================================== #

#: The 3 CBOE rows. Named here rather than filtered silently, for the reason
#: :data:`FRED_OBS_DATE_ROWS` is.
CBOE_ROWS = tuple(i.source_id for i in INGREDIENTS if i.kind == "cboe")

#: ``VIX_History.csv``, REAL: the header and every row of 2015-06 copied verbatim out of
#: ``evidence/wo116_cboe_probe.json`` (``rows_for_month_verbatim``), then two rows from
#: ``rows_tail``. So the body under test is the body the endpoint actually serves —
#: ``MM/DD/YYYY`` dates, six-decimal figures, FIVE columns of which ``CLOSE`` is asked for.
#:
#: June 2015 had NO market holiday, so these 22 rows are June's 22 weekdays exactly and every
#: absent date in the month is a WEEKEND: 06/06, 06/07, 06/13, 06/14, 06/20, 06/21, 06/27,
#: 06/28. That is the finding the calendar read exists for — CBOE publishes no missing-data
#: marker, so a non-session is an ABSENT ROW and the only way to know the trading days is to
#: read which rows are there.
#:
#: The two 2026 rows at the foot are the probe's real tail. They ride in on EVERY request,
#: windowed or not, which is why a window test below has something to exclude.
_VIX_BODY = (
    "DATE,OPEN,HIGH,LOW,CLOSE\n"
    "06/01/2015,13.920000,14.860000,13.470000,13.970000\n"
    "06/02/2015,14.720000,15.050000,13.590000,14.240000\n"
    "06/03/2015,13.730000,14.200000,13.400000,13.660000\n"
    "06/04/2015,14.570000,15.490000,13.990000,14.710000\n"
    "06/05/2015,15.010000,15.650000,14.210000,14.210000\n"
    "06/08/2015,14.840000,15.500000,14.670000,15.290000\n"
    "06/09/2015,15.180000,15.740000,14.470000,14.470000\n"
    "06/10/2015,14.240000,14.370000,12.960000,13.220000\n"
    "06/11/2015,13.040000,13.220000,12.560000,12.850000\n"
    "06/12/2015,13.310000,14.020000,13.300000,13.780000\n"
    "06/15/2015,15.480000,15.570000,14.910000,15.390000\n"
    "06/16/2015,15.620000,15.620000,14.810000,14.810000\n"
    "06/17/2015,14.660000,15.490000,14.070000,14.500000\n"
    "06/18/2015,14.030000,14.030000,12.540000,13.190000\n"
    "06/19/2015,13.350000,14.000000,12.960000,13.960000\n"
    "06/22/2015,13.420000,13.460000,12.430000,12.740000\n"
    "06/23/2015,12.500000,12.680000,11.930000,12.110000\n"
    "06/24/2015,12.570000,13.330000,12.010000,13.260000\n"
    "06/25/2015,12.960000,14.160000,12.920000,14.010000\n"
    "06/26/2015,14.130000,14.910000,13.640000,14.020000\n"
    "06/29/2015,16.700000,19.500000,15.820000,18.850000\n"
    "06/30/2015,17.600000,19.800000,17.490000,18.230000\n"
    "10/13/2026,15.610000,15.610000,15.170000,15.270000\n"
    "10/14/2026,15.170000,17.450000,14.980000,16.870000\n"
)

#: Every trading day of June 2015, which is what ``_VIX_BODY`` carries and therefore what the
#: reader must return for a June window. Written out rather than generated: a generated
#: expectation would be a MODEL of the calendar, and this file's whole argument is that the
#: model is the thing not to trust.
_JUNE_2015_SESSIONS = (
    "2015-06-01", "2015-06-02", "2015-06-03", "2015-06-04", "2015-06-05",
    "2015-06-08", "2015-06-09", "2015-06-10", "2015-06-11", "2015-06-12",
    "2015-06-15", "2015-06-16", "2015-06-17", "2015-06-18", "2015-06-19",
    "2015-06-22", "2015-06-23", "2015-06-24", "2015-06-25", "2015-06-26",
    "2015-06-29", "2015-06-30",
)

#: ``SKEW_History.csv``, REAL, same source and month. TWO columns where VIX has five — the
#: reason ``cboe_body_dates`` takes the row width from the HEADER and never from a constant.
_SKEW_BODY = (
    "DATE,SKEW\n"
    "06/11/2015,125.320000\n"
    "06/12/2015,119.260000\n"
    "06/15/2015,119.250000\n"
    "06/16/2015,120.230000\n"
)


# --- the population, and the URL the live loop has always asked ------------------------- #


def test_the_three_cboe_rows_have_no_other_date_source_either():
    """All three are ``obs_date``, so the formula sibling refuses every one of them. These are
    the rows this round claims to cover, re-derived from the catalog rather than asserted."""
    assert CBOE_ROWS == ("cboe.SKEW", "cboe.VIX", "cboe.VIX3M")
    for source_id in CBOE_ROWS:
        assert _ing(source_id).as_of_rule == "obs_date"
        with pytest.raises(ValueError):
            observation_dates(_ing(source_id), "2015-06-01", "2015-06-30")


def test_the_cboe_calendar_asks_the_same_url_the_live_adapter_has_always_asked():
    """THE NON-REGRESSION, by EQUALITY. ``cboe_history_url`` was lifted out of
    ``CboeAdapter._url`` this round; if the lift changed a character, the live collector is
    asking a different endpoint and this fails."""
    for ing in (i for i in INGREDIENTS if i.kind == "cboe"):
        live = CboeAdapter(ing.ref, ing.column, source_id=ing.source_id,
                           as_of_rule=ing.as_of_rule, unit=ing.unit, clock=lambda: NOW)
        assert live._url() == cboe_history_url(ing.ref)
    assert cboe_history_url("VIX") == (
        "https://cdn-api.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv")


def test_the_cboe_request_is_one_get_and_carries_no_window_because_none_exists():
    """There is no dated CBOE URL to avoid asking for — the endpoint honours no windowing
    parameter at all (``evidence/wo116_cboe_probe.json``: eight spellings, byte-identical
    bodies). So the URL is the bare one and the whole history is what arrives."""
    getter = _serves(_VIX_BODY)
    cboe_observation_dates(_ing("cboe.VIX"), "2015-06-01", "2015-06-30",
                           timeout_seconds=45.0, getter=getter)
    url, timeout, headers = getter.calls[0]
    assert len(getter.calls) == 1, "the calendar is ONE GET per index (3 for all three rows)"
    assert url == cboe_history_url("VIX") and "?" not in url
    assert (timeout, headers) == (45.0, None)


# --- the calendar is READ, not modelled -------------------------------------------------- #


def test_the_dates_are_every_session_the_body_carries_and_the_weekends_are_simply_absent():
    """The whole month, off the real body. A modelled calendar would have to be right about
    which days CBOE traded; this is right by construction because it READ them."""
    dates = cboe_observation_dates(_ing("cboe.VIX"), "2015-06-01", "2015-06-30",
                                   timeout_seconds=45.0, getter=_serves(_VIX_BODY))
    assert dates == _JUNE_2015_SESSIONS
    assert len(dates) == 22
    for weekend in ("2015-06-06", "2015-06-07", "2015-06-13", "2015-06-14",
                    "2015-06-20", "2015-06-21", "2015-06-27", "2015-06-28"):
        assert weekend not in dates, "an absent row is not a session we may invent"
        assert date.fromisoformat(weekend).weekday() >= 5


def test_a_two_column_body_is_read_by_its_own_header_width():
    """``SKEW`` is ``DATE,SKEW``; ``VIX`` is ``DATE,OPEN,HIGH,LOW,CLOSE``. A hard-coded width
    would refuse one of the two, and the catalog carries both."""
    assert cboe_observation_dates(_ing("cboe.SKEW"), "2015-06-01", "2015-06-30",
                                  timeout_seconds=45.0, getter=_serves(_SKEW_BODY)) == (
        "2015-06-11", "2015-06-12", "2015-06-15", "2015-06-16")
    assert cboe_body_dates(_SKEW_BODY, "SKEW") == cboe_body_dates(_SKEW_BODY, "SKEW")


def test_the_column_asked_for_is_the_catalog_s_and_not_a_position():
    """``cboe.VIX`` declares ``CLOSE``, the FIFTH cell. Read by position it would be ``OPEN``.
    The dates happen to coincide here, which is exactly why the COLUMN is asserted instead:
    the body is refused outright if the declared column is not in the header."""
    assert _ing("cboe.VIX").column == "CLOSE" and _ing("cboe.SKEW").column == "SKEW"
    with pytest.raises(ValueError, match="do not include 'CLOSE'"):
        cboe_body_dates(_SKEW_BODY, "CLOSE")


def test_the_body_order_is_not_relied_on_for_cboe_either():
    """CBOE serves oldest row first and was measured strictly ascending in all three bodies.
    The result is sorted rather than trusting that."""
    jumbled = ("DATE,SKEW\n"
               "06/16/2015,120.230000\n"
               "06/11/2015,125.320000\n"
               "06/12/2015,119.260000\n")
    assert cboe_body_dates(jumbled, "SKEW") == ("2015-06-11", "2015-06-12", "2015-06-16")


def test_cboe_publishes_no_blank_cell_today_and_the_guard_is_kept_anyway():
    """MEASURED, not assumed: all three bodies were fetched whole on 2026-10-16 and 22,839 rows
    carry a figure in every column — zero empty cells. So the real bodies exercise this guard
    not at all, and it is kept for the reason ``parse_cboe_csv_for_date`` keeps its identical
    one: a body that one day DOES carry a blank must make that date absent from the list rather
    than a date the backfill is told it can recover."""
    for body in (_VIX_BODY, _SKEW_BODY):
        header = body.splitlines()[0].split(",")
        for line in body.strip().splitlines()[1:]:
            assert "" not in line.split(",")[1:], "the real bodies carry no blank cell"
            assert len(line.split(",")) == len(header)
    blanked = ("DATE,SKEW\n"
               "06/11/2015,125.320000\n"
               "06/12/2015,\n"
               "06/15/2015,119.250000\n")
    assert cboe_body_dates(blanked, "SKEW") == ("2015-06-11", "2015-06-15")


def test_fred_s_dot_is_not_a_cboe_missing_marker_and_is_a_publication():
    """``.`` is FRED's convention. Treating it as CBOE's would be inventing a convention this
    endpoint has never used — and the question here is only whether the index had a session."""
    dotted = "DATE,SKEW\n06/11/2015,.\n"
    assert cboe_body_dates(dotted, "SKEW") == ("2015-06-11",)


# --- the window: an exact bound on the dates, applied HERE ------------------------------- #


def test_dates_outside_the_window_are_excluded_at_both_ends():
    """The window excludes rows at BOTH ends of the body it was handed: June's first week falls
    before the bound and the 2026 tail falls after it. Inclusive at both ends."""
    dates = cboe_observation_dates(_ing("cboe.VIX"), "2015-06-10", "2015-06-19",
                                   timeout_seconds=45.0, getter=_serves(_VIX_BODY))
    assert dates == ("2015-06-10", "2015-06-11", "2015-06-12", "2015-06-15",
                     "2015-06-16", "2015-06-17", "2015-06-18", "2015-06-19")
    assert dates[0] == "2015-06-10" and dates[-1] == "2015-06-19", "bounds are inclusive"
    assert "2015-06-09" not in dates and "2015-06-22" not in dates
    assert "2026-10-14" not in dates, "today's row rode in on an unwindowable body"


def test_a_window_entirely_before_the_index_existed_is_empty_and_not_the_whole_body():
    """``VIX3M`` begins 2009-09-18 (probed). A 2005 window is empty rather than 'all of it',
    because the bound is arithmetic here and the server could not have applied one."""
    body = ("DATE,OPEN,HIGH,LOW,CLOSE\n"
            "09/18/2009,25.910000,26.660000,25.910000,26.540000\n"
            "09/21/2009,26.960000,27.240000,26.170000,26.230000\n")
    assert cboe_observation_dates(_ing("cboe.VIX3M"), "2005-01-01", "2008-12-31",
                                  timeout_seconds=45.0, getter=_serves(body)) == ()


def test_an_empty_cboe_window_is_an_empty_tuple_and_not_an_error():
    getter = _serves(_VIX_BODY)
    assert cboe_observation_dates(_ing("cboe.VIX"), "2016-01-01", "2016-01-14",
                                  timeout_seconds=45.0, getter=getter) == ()
    assert cboe_observation_dates(_ing("cboe.VIX"), "2016-01-01", "2015-01-01",
                                  timeout_seconds=45.0, getter=getter) == ()


def test_a_cboe_bound_we_cannot_read_is_refused_before_a_byte_is_fetched():
    getter = _serves(_VIX_BODY)
    for start, end in (("not-a-date", "2015-06-30"), ("2015-06-01", "2015-13-01")):
        with pytest.raises(ValueError):
            cboe_observation_dates(_ing("cboe.VIX"), start, end,
                                   timeout_seconds=45.0, getter=getter)
    assert getter.calls == [], "a bound we cannot parse must not cost a GET"


# --- refusals: a body we cannot read stops the run ---------------------------------------- #


def test_a_non_cboe_ingredient_is_refused_and_costs_no_get():
    getter = _serves(_VIX_BODY)
    others = [i for i in INGREDIENTS if i.kind != "cboe"]
    assert {i.kind for i in others} >= {"fred", "yahoo"}
    for ing in others:
        with pytest.raises(ValueError, match=r"Cboe \*_History.csv body"):
            cboe_observation_dates(ing, "2015-06-01", "2015-06-30",
                                   timeout_seconds=45.0, getter=getter)
    assert getter.calls == []


@pytest.mark.parametrize("body", [
    "",
    "<!DOCTYPE html><html>Cboe error page</html>",
    "observation_date,CLOSE\n2015-06-15,15.39\n",
    "Date,OPEN,HIGH,LOW,CLOSE\n06/15/2015,1,2,3,4\n",
])
def test_a_body_that_is_not_a_cboe_history_csv_at_all_is_refused(body):
    """A header that is not ``DATE,...`` is a raise, where ``parse_cboe_csv_for_date`` returns
    a ``{"malformed": ...}`` payload — this module's stated divergence."""
    with pytest.raises(ValueError, match="not a Cboe"):
        cboe_body_dates(body, "CLOSE")


def test_a_cboe_row_of_the_wrong_width_raises_where_the_sibling_parsers_would_skip_it():
    """``parse_cboe_csv_for_date`` SKIPS a short row because it is hunting one named date. Here
    a skipped row is a date never asked for, so the body is refused whole."""
    with pytest.raises(ValueError, match="line 3 .* 4 cells, not 5"):
        cboe_body_dates("DATE,OPEN,HIGH,LOW,CLOSE\n"
                        "06/11/2015,13.040000,13.220000,12.560000,12.850000\n"
                        "06/12/2015,13.310000,14.020000,13.300000\n", "CLOSE")


def test_a_cboe_date_we_cannot_read_raises_rather_than_being_skipped():
    """The deliberate divergence from ``parse_cboe_csv_for_date``, which skips an unreadable
    date because it cannot be PROVEN to be the one asked for. A calendar read that skipped it
    would drop a date from the whole list silently. ISO is not CBOE's format and is refused
    too: this body is ``MM/DD/YYYY`` and a reader guessing between the two could not tell
    06/07 from 07/06."""
    with pytest.raises(ValueError, match="which is not an MM/DD/YYYY date"):
        cboe_body_dates("DATE,SKEW\n06/11/2015,125.320000\nnot-a-date,119.260000\n", "SKEW")
    with pytest.raises(ValueError, match="which is not an MM/DD/YYYY date"):
        cboe_body_dates("DATE,SKEW\n06/11/2015,125.320000\n2015-06-12,119.260000\n", "SKEW")


def test_a_cboe_date_carried_twice_is_refused_rather_than_silently_halved():
    """Reported in ISO, the form the caller would have received it in."""
    with pytest.raises(ValueError, match="carries 2015-06-15 twice"):
        cboe_body_dates("DATE,SKEW\n06/15/2015,119.250000\n06/15/2015,119.260000\n", "SKEW")


def test_a_cboe_fetch_failure_propagates_and_is_never_an_empty_date_list():
    """A 404 on this URL is "no history file for this index" in every mode — never "no session
    on that date", which is an ABSENT ROW in a body that arrived fine. So there is nothing here
    to translate into an empty list, and a caller must not read one as "never traded"."""
    def refused(url, timeout_seconds, headers=None):
        raise AdapterFetchError("HTTP_ERROR", 404)

    with pytest.raises(AdapterFetchError) as raised:
        cboe_observation_dates(_ing("cboe.VIX"), "2015-06-01", "2015-06-30",
                               timeout_seconds=45.0, getter=refused)
    assert raised.value.error_class == "HTTP_ERROR" and raised.value.http_status == 404


def test_a_conforming_cboe_body_with_no_rows_is_empty_and_not_an_error():
    """The one thing an empty tuple is allowed to mean, for CBOE as for FRED."""
    assert cboe_body_dates("DATE,SKEW\n", "SKEW") == ()
