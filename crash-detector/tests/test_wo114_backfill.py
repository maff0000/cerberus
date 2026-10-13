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

    TWO — the STABLE branch's DECLARED LIMIT, tested as it ACTUALLY BEHAVES TODAY and not as
    it is eventually intended to. ``FredAdapter`` asks for the whole current body and reads
    its LATEST row; there is no date in its request at all. So for a historical date — even
    one the body carries a row for, and ``_Fred`` below carries rows for every date asked —
    the reading that comes back answers for TODAY's period, the driver's date gate catches
    the mismatch, NOTHING IS STORED, and the date is reported ``FAILED_DATE_NOT_ANSWERED``.
    The one date that admits is the one that is literally today in this module's clock. That
    is the limit ``ingestion.backfill`` declares in its own docstring, measured.

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
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

import pytest

from crash_detector.collectors import RetryPolicy
from crash_detector.collectors.adapter import AdapterFetchError
from ingestion import backfill as B
from ingestion.backfill import (BACKFILL_PACING_SECONDS, BACKFILL_POLICY,
                                FAILED_DATE_NOT_ANSWERED, REFUSED_STABILITY_UNMEASURED,
                                backfill_range)
from ingestion.backfill_adapters import build_backfill_adapter as _real_build_backfill_adapter
from ingestion.catalog import INGREDIENTS
from ingestion.store import SqliteStore
from ingestion.vintage import STABILITY_MEASURED_FROM, VINTAGE_CURRENT_ONLY, VINTAGE_ORIGINAL

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

    def build(ing, observation_date, clock):
        adapter = _real_build_backfill_adapter(ing, observation_date, clock)
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
# Two fakes because the two branches ask two DIFFERENT questions of two different endpoints,
# and the whole point of this round is that the driver treats the answers differently.


class _Alfred:
    """ALFRED's vintage endpoint, offline: a trail that begins somewhere, and per observation
    the vintages that served it.

    ``observations`` maps an observation date to its revision history as
    ``((vintage_date, value), ...)``, oldest first — so a vintage asked for serves the newest
    revision at or before it, and a vintage older than the first one serves the row not at
    all. Those are the three states the bisection in
    ``ingestion.adapters.AlfredVintageAdapter`` turns on: 404 beneath the trail, served-but-
    empty, and served. An observation this fake has never heard of is served-but-empty at
    every vintage, which is "no vintage ever published this figure".
    """

    def __init__(self, observations, *, column: str = "GDP", trail_from: str = "1991-07-15",
                 fails=()):
        self.observations = {obs: list(revisions) for obs, revisions in observations.items()}
        self.column, self.trail_from = column, trail_from
        #: observation date -> the error class every request about it raises
        self.fails = dict(fails)
        self.asked: list[str] = []

    def observations_asked(self) -> list:
        return [parse_qs(urlsplit(url).query)["cosd"][0] for url in self.asked]

    def __call__(self, url, timeout, headers=None):
        self.asked.append(url)
        query = parse_qs(urlsplit(url).query)
        vintage, observation = query["vintage_date"][0], query["cosd"][0]
        if observation in self.fails:
            raise AdapterFetchError(self.fails[observation])
        if vintage < self.trail_from:
            raise AdapterFetchError("HTTP_ERROR", 404)  # no such vintage of this series
        header = f"observation_date,{self.column}_{vintage.replace('-', '')}"
        served = [value for when, value in self.observations.get(observation, ()) if when <= vintage]
        if not served:
            return header + "\n"  # the vintage exists and had nothing to say about this date
        return f"{header}\n{observation},{served[-1]}\n"


class _Fred:
    """``fredgraph.csv``'s CURRENT body, offline: the WHOLE series, latest row LAST.

    That shape is the declared limit itself rather than a convenience: the request carries no
    date (``FredAdapter._url`` names the series and the transformation, nothing else), the
    body carries every observation, and ``parse_fred_csv`` reads the LAST non-missing row. So
    a body that answers perfectly for every date asked still answers with TODAY's period.
    """

    def __init__(self, rows, *, column: str = "DFF"):
        self.rows, self.column = list(rows), column
        self.asked: list[str] = []

    @property
    def body(self) -> str:
        lines = [f"observation_date,{self.column}"] + [f"{d},{v}" for d, v in self.rows]
        return "\n".join(lines) + "\n"

    def carries(self, observation_date: str) -> bool:
        return any(date == observation_date for date, _ in self.rows)

    def __call__(self, url, timeout, headers=None):
        self.asked.append(url)
        return self.body


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


# --- ONE: the vintage branch, across several dates -------------------------------------- #


def test_a_revision_prone_series_backfills_the_figure_as_first_published_across_several_dates(
        store, monkeypatch):
    """GDP is measured revision-prone, so each date is fetched from ALFRED vintage by vintage.

    The assertion that matters is the VALUE: 14412.8 is what the 2008 Q3 figure said when it
    was first published and 14200.2 is what it says now, and a backfill that stored the
    second has committed the forgery this work order exists to prevent.
    """
    alfred = _offline(monkeypatch, _Alfred(_GDP))
    result = backfill_range(_ing("fred.GDP"), _GDP_DATES, store, CLOCK, pace=0)

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
    assert sorted(set(alfred.observations_asked())) == sorted(_GDP_DATES)
    _partitions(result, _GDP_DATES)


def test_the_later_revision_is_present_in_the_fake_and_is_the_answer_nobody_stored(
        store, monkeypatch):
    """The negative half of the test above: the wrong answer was AVAILABLE and was not taken."""
    alfred = _offline(monkeypatch, _Alfred(_GDP))
    backfill_range(_ing("fred.GDP"), ("2008-09-01",), store, CLOCK, pace=0)
    today_s_body = alfred("https://x/?id=GDP&vintage_date=2026-10-13&cosd=2008-09-01", 1.0)
    assert "14200.2" in today_s_body  # what GDP says about 2008 Q3 NOW
    assert _readings(store)[0][1]["value"] == 14412.8  # what it said THEN


# --- TWO: the stable branch, as it actually behaves today -------------------------------- #


def test_a_stable_series_reports_not_answered_for_every_date_but_today_even_when_the_body_has_it(
        store, monkeypatch):
    """THE DECLARED LIMIT, MEASURED. Dates all at or after ``STABILITY_MEASURED_FROM``, a body
    that carries a row for every one of them — and only the date that is literally today in
    this module's clock is admitted. The others are ``FAILED_DATE_NOT_ANSWERED``.

    This is the current behaviour and not the intended one: closing it is a per-date FRED
    request (``cosd``/``coed``) or a deepened ``history``, which ``ingestion.backfill`` says
    it OWES and does not attempt. What is tested here is that until then the driver reports a
    miss instead of admitting today's rate under a historical key.
    """
    dates = ("1999-01-01", "2005-06-15", "2020-03-16", TODAY)
    assert all(date >= STABILITY_MEASURED_FROM for date in dates)
    fred = _offline(monkeypatch, _Fred(_DFF_ROWS))
    result = backfill_range(_ing("fred.DFF"), dates, store, CLOCK, pace=0)

    assert result.vintage == VINTAGE_CURRENT_ONLY
    assert result.admitted == (TODAY,)
    assert result.failed == (("1999-01-01", FAILED_DATE_NOT_ANSWERED),
                             ("2005-06-15", FAILED_DATE_NOT_ANSWERED),
                             ("2020-03-16", FAILED_DATE_NOT_ANSWERED))
    assert result.fetches == 4  # each was really asked for; none was refused unfetched
    # The transport answered for every date asked. The miss is the ADAPTER's reading of the
    # body, which is why this is a declared limit of the stable branch and not a bad fake.
    assert all(fred.carries(date) for date in dates)
    # ...and here is why it cannot do better yet: there is no date in the request at all.
    assert {url for url in fred.asked} == {
        "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF"}

    # NOTHING SILENTLY WRONG WAS STORED: one reading, under TODAY's period, carrying today's
    # value, labelled current_only. No 1999, 2005 or 2020 key exists in the store.
    assert _readings(store) == [
        (f"{TODAY}T00:00:00Z", {"unit": "percent", "observation_date": TODAY, "value": 3.88},
         VINTAGE_CURRENT_ONLY)]
    # The three unadmitted fetches are still in the record as the OK attempts they were: the
    # reading is absent, the attempt is not hidden.
    assert _attempts(store) == [("OK", f"{TODAY}T00:00:00Z", None)] * 4
    _partitions(result, dates)


def test_a_date_before_the_stability_measurement_is_refused_unfetched_and_the_range_goes_on(
        store, monkeypatch):
    """The left edge is INCLUSIVE, so the refusal is the day before it and that day costs no GET.

    ``STABILITY_MEASURED_FROM`` is where the measurement that authorises the stable branch
    begins; before it, today's body is not evidence about the date and there is no vintage to
    fall back on here. 1998-12-31 is therefore refused rather than failed — a date nobody
    fetched is not a date that failed — and 1999-01-01, the edge itself, is fetched.
    """
    assert STABILITY_MEASURED_FROM == "1999-01-01"
    dates = ("1998-12-31", "1999-01-01", TODAY)
    fred = _offline(monkeypatch, _Fred(_DFF_ROWS))
    result = backfill_range(_ing("fred.DFF"), dates, store, CLOCK, pace=0)

    assert result.refused == (("1998-12-31", REFUSED_STABILITY_UNMEASURED),)
    assert result.fetches == 2 and len(fred.asked) == 2  # UNFETCHED, counted on the transport
    assert len(_attempts(store)) == 2  # and no attempt row names the refused date either
    # The rest of the range proceeded: the edge itself was asked (and hit the limit above),
    # and today was admitted.
    assert result.failed == (("1999-01-01", FAILED_DATE_NOT_ANSWERED),)
    assert result.admitted == (TODAY,)
    assert [as_of for as_of, _, _ in _readings(store)] == [f"{TODAY}T00:00:00Z"]
    _partitions(result, dates)


# --- FOUR: a re-run of a finished range is free ------------------------------------------ #


def test_re_running_an_admitted_range_skips_every_date_and_issues_no_request_at_all(
        store, monkeypatch):
    """``fetches == 0``, counted on the transport as well as reported. This is the property
    that makes a 6,000-date backfill resumable: a range already half-done costs GETs only for
    the half that is missing."""
    alfred = _offline(monkeypatch, _Alfred(_GDP))
    first = backfill_range(_ing("fred.GDP"), _GDP_DATES, store, CLOCK, pace=0)
    assert first.admitted == _GDP_DATES
    probes, attempts = len(alfred.asked), len(_attempts(store))

    again = backfill_range(_ing("fred.GDP"), _GDP_DATES, store, CLOCK, pace=0)

    assert again.skipped == _GDP_DATES
    assert again.counts == {"admitted": 0, "skipped": 3, "refused": 0, "failed": 0, "fetches": 0}
    assert len(alfred.asked) == probes      # not one more GET
    assert len(_attempts(store)) == attempts  # and not one more attempt row
    assert [as_of for as_of, _, _ in _readings(store)] == _GDP_PERIODS  # still three readings
    _partitions(again, _GDP_DATES)


# --- FIVE: one date's failure is one date's failure --------------------------------------- #


def test_a_transport_failure_on_one_date_carries_its_class_and_stops_nothing(store, monkeypatch):
    """The middle date's fetch fails; the first and last are admitted, and the class recorded
    is the adapter's own ``error_class`` — no message, no URL, no exception text."""
    monkeypatch.setattr(B, "BACKFILL_POLICY", ONE_ATTEMPT)
    alfred = _offline(monkeypatch, _Alfred(_GDP, fails={"2008-12-01": "CONNECTION_FAILED"}))
    result = backfill_range(_ing("fred.GDP"), _GDP_DATES, store, CLOCK, pace=0)

    assert result.admitted == ("2008-09-01", "2009-03-01")
    assert result.failed == (("2008-12-01", "CONNECTION_FAILED"),)
    assert result.fetches == 3  # the failure was a fetch, and the range continued past it
    assert [as_of for as_of, _, _ in _readings(store)] == [_GDP_PERIODS[0], _GDP_PERIODS[2]]
    assert ("FETCH_FAILED", None, "CONNECTION_FAILED") in _attempts(store)
    assert "2009-03-01" in alfred.observations_asked()  # the date AFTER the failure was asked
    _partitions(result, _GDP_DATES)


def test_an_answer_that_is_not_a_reading_is_a_failed_date_with_the_stores_own_class(
        store, monkeypatch):
    """Neither EMPTY nor MALFORMED is a date this backfill HAS, which is what ``failed`` records
    — and the class carried is the store's own discriminator, not a vocabulary invented here.

    * ``2009-06-01`` — ALFRED served every vintage and none carried this figure. EMPTY is a
      real ANSWER (the observation was never published), and it still leaves a gap.
    * ``2030-06-01`` — an observation that HAS NOT HAPPENED. ``AlfredVintageAdapter`` refuses
      it as MALFORMED without probing anything, rather than searching an empty window; the
      driver reports the refusal under that date and carries on.
    """
    dates = ("2008-09-01", "2009-06-01", "2030-06-01")
    alfred = _offline(monkeypatch, _Alfred(_GDP))
    result = backfill_range(_ing("fred.GDP"), dates, store, CLOCK, pace=0)

    assert result.admitted == ("2008-09-01",)
    assert result.failed == (("2009-06-01", "EMPTY"), ("2030-06-01", "MALFORMED"))
    outcomes = [outcome for outcome, _, _ in _attempts(store)]
    assert outcomes == ["OK", "EMPTY", "MALFORMED"]
    assert len(_readings(store)) == 1
    assert "2009-06-01" in alfred.observations_asked()        # really searched for
    assert "2030-06-01" not in alfred.observations_asked()    # and this one never asked at all
    _partitions(result, dates)


# --- SIX: the partition, over a range that lands in all four buckets ---------------------- #


def test_one_range_lands_in_all_four_buckets_and_they_partition_the_dates_given(
        store, monkeypatch):
    """SAHMREALTIME is measured stable and FRED dates it ``month_end``, which is what lets one
    range reach all four answers:

    * ``1998-01-01`` — before the measurement's left edge: REFUSED, unfetched;
    * ``2005-06-01`` — fetched, and the body answers for today: FAILED, nothing stored;
    * ``2026-10-01`` — the current month, whose period is today: ADMITTED;
    * ``2026-10-05`` — the SAME source period (``month_end``, capped at today), already
      admitted by the line above: SKIPPED, unfetched.

    The last pair is not a contrivance — two dates in one month ARE one source period, and
    that is exactly what ``skipped`` means.
    """
    dates = ("1998-01-01", "2005-06-01", "2026-10-01", "2026-10-05")
    rows = (("1998-01-01", "0.03"), ("2005-06-01", "-0.13"), ("2026-10-01", "0.27"))
    sahm = _offline(monkeypatch, _Fred(rows, column="SAHMREALTIME"))
    result = backfill_range(_ing("fred.SAHMREALTIME"), dates, store, CLOCK, pace=0)

    assert result.refused == (("1998-01-01", REFUSED_STABILITY_UNMEASURED),)
    assert result.failed == (("2005-06-01", FAILED_DATE_NOT_ANSWERED),)
    assert result.admitted == ("2026-10-01",)
    assert result.skipped == ("2026-10-05",)
    assert result.counts == {"admitted": 1, "skipped": 1, "refused": 1, "failed": 1, "fetches": 2}
    assert len(sahm.asked) == 2  # the refusal and the skip each cost nothing
    assert [as_of for as_of, _, _ in _readings(store)] == [f"{TODAY}T00:00:00Z"]
    _partitions(result, dates)


def test_the_pace_falls_between_fetches_only_and_never_around_a_refusal_or_a_skip(
        store, monkeypatch):
    """The courtesy gap is a gap between REQUESTS. The range above issues two, so there is one
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


def test_a_non_fred_kind_raises_before_a_single_date_is_touched(store, monkeypatch):
    """One defect about the whole range, reported once — not buried under a thousand identical
    per-date failures. Measured by an adapter builder that fails the test if it is reached at
    all, so the refusal is proved to come BEFORE the loop and not from inside it."""
    _no_adapter_may_be_built(monkeypatch)
    others = [ing for ing in INGREDIENTS if ing.kind != "fred"]
    assert {ing.kind for ing in others} == {"cboe", "yahoo", "multpl", "lbma", "hermes", "manual"}

    for ing in others:
        with pytest.raises(ValueError, match="point-in-time backfill is declared only for"):
            backfill_range(ing, ("1998-01-01", "2005-06-01", TODAY), store, CLOCK, pace=0)

    assert _attempts(store) == [] and _readings(store) == []
