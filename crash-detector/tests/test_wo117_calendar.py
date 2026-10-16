"""WO-1.17 the FRED date-list reader: it READS a calendar it does not model, and refuses bodies.

``ingestion.backfill_calendar`` closes the FRED half of the gap
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
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from crash_detector.collectors.adapter import AdapterFetchError
from ingestion.adapters import FredAdapter, fred_column, fred_graph_url
from ingestion.backfill_calendar import fred_body_dates, fred_observation_dates
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
    """CBOE's ``*_History.csv`` and Yahoo's chart JSON are their own calendars, in their own
    later rounds. Handing one to this reader must not produce a plausible-looking list."""
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
