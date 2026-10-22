"""WO-1.17 the run driver: the population it walks and the date list it assembles.

``tools/backfill/wo117_run.py`` adds exactly two things to machinery that already existed —
WHICH ROWS, and OVER WHICH DATES. Everything else it does is a call into
``ingestion.backfill.backfill_range``, whose own behaviour is measured by
``tests/test_wo114_backfill.py`` and proven against the real wire by the three
``tools/probe/woNNN_backfill_proof.py`` scripts. So this file tests the two things, and it tests
them where they live: the population is a re-derivation from the catalog and the predicates, and
the date list is ``assemble_dates``, which is pure.

NO REAL NETWORK, AND NOT BY CONVENTION ALONE. Every test that reaches a date source hands it a
fake ``getter`` with the adapters' own three-positional-argument signature, the standing pattern
``tests/test_wo117_calendar.py`` set for the readers themselves. The reason is sharper here than
for the readers: the thing this driver drives is measured at 190,391 GETs and ~36.25 hours
(``WO-1.17-COST-ESTIMATE.md`` §6), so a test suite that could reach the wire is a test suite that
could spend a day of somebody's budget by being run. The real-network confirmation for this round
is a TINY named subset, run once by hand, recorded in ``evidence/wo117_run_proof.json`` — it is
not in here and must not be.

WHAT THE WINDOW TESTS ARE FOR. §2's eight windows are a transcription risk: eight pairs of dates
carried from a markdown table into a tuple, where a single wrong digit silently moves an episode's
left edge and quietly drops or invents a few hundred dates. So the driver stores the SPANS and
derives every window from ``LEAD_IN_CALENDAR_DAYS``, and the tests below check the derived windows
against §2's own "Window" and "Calendar days" columns written out verbatim. Two hardcoded columns
could not check each other; a derivation and one column can.
"""

from __future__ import annotations

import pytest

from ingestion.backfill_adapters import VINTAGE_BACKFILLABLE_KINDS
from ingestion.backfill_dates import GENERABLE_AS_OF_RULES, observation_dates
from ingestion.catalog import INGREDIENTS
from ingestion.vintage import has_no_revision_mechanism, requires_original_vintage

from tools.backfill.wo117_run import (CALENDAR_TIMEOUT_SECONDS, EPISODES, LEAD_IN_CALENDAR_DAYS,
                                      Episode, assemble_dates, backfillable_population,
                                      calendar_identity, date_source, enclosing_span,
                                      read_calendar, route, row_dates, select_episodes,
                                      select_rows)

#: §2's table, columns 3 and 4, written out verbatim. The expectation side of the derivation —
#: if these and ``EPISODES``' spans ever disagree, one of the two was typed wrong and the test
#: says which episode.
SECTION_2_WINDOWS = {
    "dotcom": ("1999-11-02", "2002-12-31", 1156),
    "gfc": ("2007-04-02", "2009-12-31", 1005),
    "downgrade": ("2011-03-02", "2011-12-31", 305),
    "china": ("2015-06-02", "2016-03-31", 304),
    "q4-2018": ("2018-08-02", "2018-12-31", 152),
    "covid": ("2019-12-03", "2020-04-30", 150),
    "2022": ("2021-11-02", "2022-12-31", 425),
    "apr-2025": ("2024-12-31", "2025-05-31", 152),
}


def _ing(source_id: str):
    return next(i for i in INGREDIENTS if i.source_id == source_id)


def _fred_body(column: str, dates) -> str:
    """A ``fredgraph.csv`` body carrying one row per date. The real header shape."""
    return "\n".join([f"observation_date,{column}"]
                     + [f"{d},1.5" for d in dates]) + "\n"


def _serves(body: str):
    """A fake transport with the adapters' three-positional-argument signature."""
    calls = []

    def getter(url, timeout_seconds, headers=None):
        calls.append((url, timeout_seconds, headers))
        return body

    getter.calls = calls
    return getter


def _refuses(error):
    def getter(url, timeout_seconds, headers=None):
        raise error
    return getter


# --- §2: the eight windows, derived and checked against the table ----------------------- #


def test_the_eight_windows_are_section_2s_eight_windows_derived_from_the_lead_in():
    """The transcription check. Each window is a SPAN plus the lead-in, and the result must be
    §2's own column — including the one window whose arithmetic crosses a year boundary."""
    assert LEAD_IN_CALENDAR_DAYS == 60
    assert len(EPISODES) == 8
    assert [e.key for e in EPISODES] == list(SECTION_2_WINDOWS)
    for episode in EPISODES:
        start, end, days = SECTION_2_WINDOWS[episode.key]
        assert (episode.window_start, episode.window_end) == (start, end), episode.key
        assert episode.calendar_days == days, episode.key
    assert sum(e.calendar_days for e in EPISODES) == 3649


def test_the_lead_in_is_the_only_thing_between_a_span_and_its_window():
    """Stated as the inverse, so a changed ``LEAD_IN_CALENDAR_DAYS`` cannot pass by coincidence:
    the window's right edge is the span's untouched, and its left edge moves with the constant."""
    moved = Episode("x", "x", "2020-02-01", "2020-04-30")
    assert moved.window_end == moved.span_end == "2020-04-30"
    assert moved.window_start == "2019-12-03"


def test_the_windows_are_ascending_and_do_not_overlap():
    """§2 totals 3,649 calendar days by ADDING the eight, which only holds if they are disjoint.
    ``assemble_dates`` deduplicates regardless, so an overlap would not corrupt a date list — it
    would mean that total double-counted."""
    windows = [(e.window_start, e.window_end) for e in EPISODES]
    assert windows == sorted(windows)
    for earlier, later in zip(windows, windows[1:]):
        assert earlier[1] < later[0], f"{earlier} overlaps {later}"


def test_the_enclosing_span_covers_every_window_and_is_one_span():
    assert enclosing_span(EPISODES) == ("1999-11-02", "2025-05-31")
    start, end = enclosing_span(EPISODES)
    for episode in EPISODES:
        assert start <= episode.window_start and episode.window_end <= end
    assert enclosing_span([EPISODES[5]]) == ("2019-12-03", "2020-04-30")
    with pytest.raises(ValueError):
        enclosing_span([])


def test_no_date_in_this_plan_falls_before_the_stability_measurement_window():
    """§1's claim, re-derived: every ``STABILITY_MEASURED_FROM`` refusal is moot for this run, so
    the 7 measured-stable rows' ``refused`` bucket should be empty for every real date."""
    from ingestion.vintage import STABILITY_MEASURED_FROM
    assert enclosing_span(EPISODES)[0] >= STABILITY_MEASURED_FROM


# --- §5: the population, re-derived rather than listed ---------------------------------- #


def test_the_population_is_the_thirty_six_rows_section_5_counts():
    population = backfillable_population()
    assert len(population) == 36
    # And it is the SAME set the two filters describe, computed here a second way.
    expected = {i.source_id for i in INGREDIENTS
                if i.kind in VINTAGE_BACKFILLABLE_KINDS
                and not (i.kind == "yahoo" and not has_no_revision_mechanism("yahoo", i.column))}
    assert {i.source_id for i in population} == expected


def test_the_four_routes_are_section_5s_eighteen_seven_three_eight():
    counts = {}
    for ing in backfillable_population():
        counts[route(ing)] = counts.get(route(ing), 0) + 1
    assert counts == {"4.1-fred-bisected": 18, "4.2-fred-stable": 7,
                      "4.3-cboe": 3, "4.4-yahoo-close": 8}
    # §5.2 by name: six REVISION_STABLE pairs spending seven catalog rows, DFII10 twice.
    stable = {i.source_id for i in backfillable_population()
              if i.kind == "fred" and not requires_original_vintage(i.ref, i.transformation)}
    assert stable == {"fred.DFF", "fred.DFII10", "fred.DFII10.history", "fred.SAHMREALTIME",
                      "fred.T10Y2Y", "fred.T10Y3M", "fred.T5YIE"}


def test_the_fifty_one_adjclose_rows_are_excluded_and_cannot_be_asked_for_by_name():
    """§9's mechanism 2, held at the driver's door rather than left to the two refusals
    downstream. An adjusted close drifts retroactively forever, so there is no point-in-time
    value to recover — naming one is a STOP, not a run of one row."""
    adjclose = [i for i in INGREDIENTS if i.kind == "yahoo" and i.column == "adjclose"]
    assert len(adjclose) == 51
    assert not ({i.source_id for i in adjclose}
                & {i.source_id for i in backfillable_population()})
    with pytest.raises(ValueError):
        select_rows(["yahoo.BIZD.adj"])


def test_the_four_date_sources_split_the_population_eleven_fourteen_three_eight():
    """§3.1's arithmetic: 11 rows a formula answers for, 25 that need a published calendar."""
    counts = {}
    for ing in backfillable_population():
        counts[date_source(ing)] = counts.get(date_source(ing), 0) + 1
    assert counts == {"formula": 11, "fred": 14, "cboe": 3, "yahoo": 8}


def test_the_formula_is_preferred_exactly_where_it_can_answer_and_nowhere_else():
    """The preference ``date_source`` documents, held in both directions against the one module
    that decides it: a row routed to ``formula`` must be answerable by ``observation_dates``, and
    a row routed to a published calendar must be REFUSED by it."""
    for ing in backfillable_population():
        if date_source(ing) == "formula":
            assert ing.kind == "fred" and ing.as_of_rule in GENERABLE_AS_OF_RULES
            assert observation_dates(ing, "2020-01-01", "2020-12-31")  # answers, no network
        else:
            with pytest.raises(ValueError):
                observation_dates(ing, "2020-01-01", "2020-12-31")


# --- the calendar cache key: 23 GETs, not 24 -------------------------------------------- #


def test_the_two_dfii10_rows_share_one_calendar_so_the_run_pays_twenty_three_gets():
    """§3.1 counts 24 GETs for 24 rows and §5.2 says why that is 13 distinct FRED calendars and
    not 14. The caller's cache is what collects the difference, and the key is what makes it
    safe: ``history`` is the only field those two rows differ in and it is deliberately absent."""
    plain, history = _ing("fred.DFII10"), _ing("fred.DFII10.history")
    assert plain.history != history.history
    assert calendar_identity(plain) == calendar_identity(history) == ("fred", "DFII10", None)

    fetching = {calendar_identity(i) for i in backfillable_population()
                if date_source(i) != "formula"}
    assert len(fetching) == 23
    assert len({calendar_identity(i) for i in backfillable_population()
                if date_source(i) == "fred"}) == 13


def test_the_cboe_key_carries_the_column_because_the_three_rows_read_two_headers():
    assert calendar_identity(_ing("cboe.VIX")) == ("cboe", "VIX", "CLOSE")
    assert calendar_identity(_ing("cboe.SKEW")) == ("cboe", "SKEW", "SKEW")
    assert calendar_identity(_ing("yahoo.SPY")) == ("yahoo", "SPY")


# --- assemble_dates: the union of the windows, sorted, deduplicated --------------------- #


def test_the_union_keeps_a_date_in_any_window_and_drops_every_date_in_the_gaps():
    """The economy of an episode-windowed backfill, stated as arithmetic: dates between episodes
    are not asked for, which is the whole 3,649-vs-9,800 difference §2 reports."""
    published = (
        "1999-11-01",  # one day before the dot-com window opens
        "1999-11-02",  # its left edge, inclusive
        "2002-12-31",  # its right edge, inclusive
        "2003-01-01",  # one day after
        "2005-06-15",  # deep in the gap between dot-com and the GFC
        "2007-04-02",  # the GFC window's left edge
        "2025-05-31",  # the last window's right edge
        "2025-06-01",  # one day after the last window closes
    )
    assert assemble_dates(published, EPISODES) == (
        "1999-11-02", "2002-12-31", "2007-04-02", "2025-05-31")


def test_the_result_is_sorted_even_though_the_windows_are_walked_one_at_a_time():
    """Per-window concatenation does not preserve ascending order on its own, and
    ``backfill_range`` honours the order given — so an unsorted list would make a half-finished
    run's progress unreadable."""
    published = ("2020-03-02", "2000-06-01", "2022-07-01", "2008-09-15")
    assembled = assemble_dates(published, EPISODES)
    assert assembled == tuple(sorted(assembled))
    assert assembled == ("2000-06-01", "2008-09-15", "2020-03-02", "2022-07-01")


def test_the_order_the_episodes_are_given_in_does_not_change_the_answer():
    published = ("2000-06-01", "2008-09-15", "2022-07-01")
    assert (assemble_dates(published, list(reversed(EPISODES)))
            == assemble_dates(published, EPISODES))


def test_overlapping_windows_offer_a_date_twice_and_it_is_asked_for_once():
    """§2's eight do not overlap, so this guards a ``--episode`` selection and any future re-cut
    of the spans. A duplicate would cost a wasted GET and a confusing ``skipped`` count, which is
    why it is deduplicated here rather than absorbed by ``backfill_range``'s own idempotence."""
    overlapping = (Episode("a", "a", "2020-03-01", "2020-06-30"),
                   Episode("b", "b", "2020-05-01", "2020-08-31"))
    assert overlapping[0].window_end > overlapping[1].window_start
    published = ("2019-12-01",   # before BOTH windows open (a's lead-in reaches 2020-01-01)
                 "2020-05-15",   # inside both — offered twice, asked for once
                 "2020-07-15")   # inside b only
    assembled = assemble_dates(published, overlapping)
    assert assembled == ("2020-05-15", "2020-07-15")
    assert len(assembled) == len(set(assembled))


def test_a_published_list_with_nothing_in_any_window_is_empty_and_not_an_error():
    """``backfill_range`` of no dates does nothing, which is the right answer for a symbol that
    did not exist during any selected episode — not a failure to be reported as one."""
    assert assemble_dates(("2005-06-15", "2013-01-01"), EPISODES) == ()
    assert assemble_dates((), EPISODES) == ()


def test_the_cap_takes_the_first_n_of_each_window_and_is_refused_below_one():
    """The proof-run cap, and per-window is the only useful spelling: a cap on the TOTAL would
    collapse a two-episode proof into the first episode and prove nothing about the union."""
    published = ("2000-01-03", "2000-01-04", "2000-01-05",
                 "2020-02-03", "2020-02-04", "2020-02-05")
    two = [e for e in EPISODES if e.key in ("dotcom", "covid")]
    assert assemble_dates(published, two, cap=2) == (
        "2000-01-03", "2000-01-04", "2020-02-03", "2020-02-04")
    assert assemble_dates(published, two, cap=1) == ("2000-01-03", "2020-02-03")
    assert assemble_dates(published, two, cap=None) == tuple(sorted(published))
    with pytest.raises(ValueError):
        assemble_dates(published, two, cap=0)


# --- row_dates: ONE calendar read over the enclosing span, then the union --------------- #


def test_one_row_costs_one_get_over_the_enclosing_span_and_not_one_per_episode():
    """The decision this driver's docstring argues: eight windowed calls would be 8x the GETs for
    the same answer, and for Yahoo would be an impossible window on three of seven rows. Held by
    counting the calls and reading the bound off the URL — the FRED request carries NO window."""
    getter = _serves(_fred_body("DFF", ["2000-06-01", "2005-06-15", "2020-03-02"]))
    dates, fetched = row_dates(_ing("fred.DFF"), EPISODES, getter=getter)
    assert len(getter.calls) == 1
    url, timeout, headers = getter.calls[0]
    assert "cosd" not in url and "coed" not in url
    assert (timeout, headers) == (CALENDAR_TIMEOUT_SECONDS, None)
    # The gap date was served and is NOT asked for: the window is applied here.
    assert dates == ("2000-06-01", "2020-03-02")
    assert fetched is True


def test_the_cache_collapses_the_second_dfii10_row_to_zero_gets():
    getter = _serves(_fred_body("DFII10", ["2008-09-15", "2022-07-01"]))
    cache: dict = {}
    first, first_fetched = row_dates(_ing("fred.DFII10"), EPISODES, getter=getter, cache=cache)
    second, second_fetched = row_dates(_ing("fred.DFII10.history"), EPISODES,
                                       getter=getter, cache=cache)
    assert first == second == ("2008-09-15", "2022-07-01")
    assert (first_fetched, second_fetched) == (True, False)
    assert len(getter.calls) == 1 and len(cache) == 1


def test_a_formula_row_reads_no_body_at_all_and_reports_no_fetch():
    """11 of the 36 rows cost nothing to date, and the driver must not report a GET it never
    issued — the per-row ``calendar_fetched`` flag is what the run's GET count is summed from."""
    getter = _serves("this body must never be read")
    dates, fetched = row_dates(_ing("fred.GDP"), EPISODES, getter=getter)
    assert getter.calls == [] and fetched is False
    # Quarter starts inside the windows, and nothing from the gaps between them.
    assert dates[:4] == ("2000-01-01", "2000-04-01", "2000-07-01", "2000-10-01")
    assert "2005-01-01" not in dates and "2003-01-01" not in dates
    assert all(any(e.window_start <= d <= e.window_end for e in EPISODES) for d in dates)


def test_a_cboe_row_reads_a_differently_shaped_body_through_the_same_dispatch():
    """One date source per row, chosen by routing — the driver holds no second opinion about
    which body a row's calendar comes off. ``MM/DD/YYYY``, a five-column header, and the same
    ascending ISO tuple out."""
    body = ("DATE,OPEN,HIGH,LOW,CLOSE\n"
            "06/01/2015,13.92,14.86,13.47,13.97\n"      # ONE DAY before the china window opens
            "06/02/2015,14.72,15.05,13.59,14.24\n"      # its left edge, inclusive
            "06/15/2015,15.48,15.57,14.91,15.39\n"      # inside it
            "05/03/2004,15.00,15.00,15.00,15.00\n")     # in the gap after dot-com
    getter = _serves(body)
    dates, fetched = row_dates(_ing("cboe.VIX"), EPISODES, getter=getter)
    assert dates == ("2015-06-02", "2015-06-15") and fetched is True
    assert len(getter.calls) == 1


def test_a_calendar_that_could_not_be_read_raises_and_is_never_an_empty_date_list():
    """All three readers refuse to let a caller confuse "could not fetch" with "published
    nothing", and the driver must not undo that: an empty list here would silently skip a row's
    whole backfill. ``run`` catches this per row and reports the CLASS; it does not translate it."""
    from crash_detector.collectors.adapter import AdapterFetchError
    with pytest.raises(AdapterFetchError):
        row_dates(_ing("fred.DFF"), EPISODES,
                  getter=_refuses(AdapterFetchError("HTTP_ERROR")))
    with pytest.raises(ValueError):
        # A body we cannot read is a raise too, for the same reason.
        read_calendar(_ing("fred.DFF"), "2000-01-01", "2000-12-31",
                      getter=_serves("not,a,fredgraph,body\n1,2,3,4\n"))


# --- the selections, and that a typo cannot quietly run nothing ------------------------- #


def test_an_unknown_row_or_episode_is_a_refusal_and_not_an_empty_run():
    """On a resumable driver, "did nothing" and "found nothing to do" are the one pair of
    outcomes that must never look alike."""
    with pytest.raises(ValueError):
        select_rows(["fred.NOT_A_SERIES"])
    with pytest.raises(ValueError):
        select_episodes(["2008"])
    assert len(select_rows([])) == 36
    assert select_episodes([]) == EPISODES


def test_a_selection_is_deduplicated_and_returned_in_population_order():
    rows = select_rows(["cboe.VIX", "fred.GDP", "cboe.VIX"])
    assert [i.source_id for i in rows] == [
        i.source_id for i in backfillable_population() if i.source_id in ("cboe.VIX", "fred.GDP")]
    assert [e.key for e in select_episodes(["covid", "dotcom"])] == ["dotcom", "covid"]
