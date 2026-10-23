#!/usr/bin/env python3
"""THE REAL BACKFILL RUN — the 36 backfillable catalog rows over WO-1.17's 8 episode windows.

    PYTHONPATH=src:. python3 tools/backfill/wo117_run.py --db <store.sqlite> [--out record.json]

    The 18 revision-prone FRED rows (route 4.1) read their first-published figures through FRED's
    keyed REST API, so a run that includes any of them needs the key in the ENVIRONMENT, supplied by
    the caller (never on the command line, never written anywhere by this script):

        FRED_API_KEY="$(cat /srv/cerberus-secrets/fred_api_key.secret)" PYTHONPATH=src:. python3 ...

    It is required only when such a row is selected and the run is not ``--dates-only``.

WHAT THIS IS AND WHAT IT IS NOT. It is the ORCHESTRATION driver the execution of
``WO-1.17-COST-ESTIMATE.md`` needs: it enumerates the population, obtains each row's real date
list, and calls ``ingestion.backfill.backfill_range`` once per row. It is NOT a new backfill. It
contains no pacing, no resumability mechanism, no per-date error handling and no adapter choice,
because every one of those already exists one layer down and a second copy here would be a
second thing to get wrong. Everything this module adds is the answer to one question —
**which rows, over which dates** — and the honest answer to that is 95% arithmetic over §2's
windows plus 23 GETs of published calendars.

WHY IT LIVES IN ``tools/backfill/`` AND NOT IN ``tools/probe/``, whose three
``woNNN_backfill_proof.py`` scripts this follows line for line on CLI shape, store ownership and
the JSON record. Those say of themselves "IT IS A PROBE, NOT A GATE... it writes a JSON record a
human reads", and each exists to settle one claim about one endpoint. This is the opposite end:
a production RUN whose output is data in a store, measured at ~190,391 GETs and ~36.25 hours
(§6). Filing a 36-hour execution driver among the probes would mislabel the one tool in this
tree that spends real money, so it goes in the directory already named for what it does.

THE FIVE THINGS IT DOES, IN ORDER
    1.  **Enumerates the 36 rows by RE-DERIVING them** (:func:`backfillable_population`) from
        ``ingestion.catalog.INGREDIENTS`` and the same three routing predicates §5 asks —
        ``VINTAGE_BACKFILLABLE_KINDS``, ``has_no_revision_mechanism`` for the yahoo column tier.
        Not a transcribed list of 36 source ids: a list would let the driver and the cost
        estimate diverge silently the next time the catalog grows a row, which is exactly what
        happened to §5's own FRED sub-count when ``DRTSCIS`` arrived (24 → 25). Re-derived, the
        driver cannot be wrong about the population without the document being wrong too.
    2.  **Obtains each row's real date list** (:func:`row_dates`) from the ONE date source its
        routing names — §3's four calendars, and the dispatch is :func:`date_source`.
    3.  **Calls ``backfill_range`` once per row** with that row's full filtered date list, in
        §5's route grouping, printing each row's ``BackfillResult.counts`` the moment it finishes.
        This is the ONLY place network cost is spent on READINGS, and it is already paced
        (``BACKFILL_PACING_SECONDS``) and already resumable (``sink.is_admitted`` before the
        fetch) by the function itself.
    4.  **Takes ``--db`` as a required argument and defaults it to nothing**, the convention
        ``tools/probe/wo114_backfill_proof.py`` set and its two siblings kept. The caller owns
        the path. Nothing here creates, migrates, discovers or guesses at a store, and in
        particular nothing here knows the name of the live DEV store: a driver that could
        default into ``cd-live-data`` is a driver that can write 190,391 rows of backfill into
        production because somebody forgot a flag.
    5.  **Reports, and does not grade a date.** Exit 1 means THE RUN was incomplete — a row
        whose calendar could not be read, or a selection that matched no rows. A date in
        ``failed`` is NOT an error exit, and that is deliberate: §7.1 measures that 11 of the 18
        bisected rows will meet ALFRED's per-series archive floor during this very run and
        return EMPTY for their oldest episode. A run that exited non-zero on an expected gap
        would be a 36-hour job that always reports failure, and nobody reads the output of a
        tool that always reports failure.

ONE WIDE SPAN PER ROW, NOT EIGHT WINDOWED CALLS — AND THE WINDOW IS APPLIED HERE
    The output handed to ``backfill_range`` must be the union of all eight windows' dates for
    that row, sorted and deduplicated. There are two ways to get it and they are NOT equivalent:

    * **Eight calls per row, concatenated.** 8 × 24 = 192 calendar GETs, of which 168 are
      redundant — ``fred_observation_dates`` and ``cboe_observation_dates`` ask UNDATED and
      filter in arithmetic, so eight calls fetch the same body eight times and differ only in
      the bound they then apply. Worse than wasteful, it is WRONG for Yahoo: a window lying
      entirely before a symbol's first trade is a measured clean ``400``
      (``evidence/wo116_yahoo_window_probe.json``), which this module would have to either
      swallow — indistinguishable from "the symbol printed nothing in those years" — or let kill
      the row. ``yahoo.HYG`` first trades 2007-04, ``LQD`` 2002-07 and ``RSP`` 2003-04, so the
      1999-11-02 episode would do exactly that on three of the seven rows.
    * **One call per row over the ENCLOSING span, then filtered to the eight windows here.**
      23 GETs, no redundancy, and no impossible window to ask for: the enclosing span
      1999-11-02..2025-05-31 intersects every one of these 36 rows' real lifetime, so every
      request is answerable. The three readers return the same dates either way — each one's
      bound is already an exact arithmetic comparison over whatever body arrived, by their own
      design, *because* a server's windowing courtesy is not what any of them lean on.

    So the span is one, the filter is :func:`assemble_dates`, and it is PURE: a list of published
    dates and the eight windows in, the union out. Nothing about it needs a network to test,
    which is why ``tests/test_wo117_run.py`` tests it with no network at all.

    **23 GETs AND NOT §3.1'S 24**, because the two ``DFII10`` rows are one FRED calendar.
    ``fred_observation_dates``' docstring says caching that is "the CALLER's business — this
    function has no state and keeps none", so the caller does it: :func:`calendar_identity`
    keys a per-run cache on exactly the arguments each reader actually reads, which for FRED is
    ``(ref, transformation)`` and not the ingredient row. Within one invocation only. There is
    no cache file and that is the next round's question, not this one's — §3.1 names the
    *persistence* of these lists as what remains owed.

RESUMABLE ACROSS AN INTERRUPTION, BY CONSTRUCTION, WITH NO CHECKPOINT OF ITS OWN
    Run the identical command twice and the second run stores nothing new and issues NO READING
    FETCH AT ALL. That is not a property this driver implements; it is ``backfill_range``'s,
    stated in its own docstring ("a re-run of a completed range issues NO requests at all") and
    held by ``sink.is_admitted(key)`` being asked BEFORE the fetch rather than discovered after
    it. This module is resumable because it is *stateless between runs*: the date list it
    assembles is a pure function of §2's windows and the published calendars, so run N+1 hands
    ``backfill_range`` the same list run N did and every date already stored comes back
    ``skipped`` with ``fetches == 0``. A checkpoint file here would be a second, weaker answer to
    a question the store already answers authoritatively — and it could be WRONG in the one
    direction that matters, by recording a row as done whose last few dates never committed.

    **BUT IT IS NOT LITERALLY FREE, AND THE DIFFERENCE IS REPORTED RATHER THAN ROUNDED AWAY.**
    A re-run re-reads the published calendars, because they are not persisted — so it costs the
    23 calendar GETs again and 0 reading GETs. The two are counted separately everywhere in this
    module's output (``calendar_fetches`` against each row's ``fetches``) precisely so that
    "the re-run was free" can be read as the exact claim it is: free of the 190,391, not free of
    everything. Measured on the real tiny subset rather than asserted — see
    ``evidence/wo117_run_proof.json``.

WHAT IT STILL DOES NOT DO, SO THAT NOBODY READS THE ABSENCE AS A CLAIM
    The ``history`` array gap of §8 is NOT closed here: a dated backfill stores a scalar, and the
    7 rows whose live readings carry a trailing array get no array from this run. §8.2 identifies
    a buildable fix and §8.3 says it is necessary and, on two indicators, not sufficient. It is a
    separate round. Likewise the 54 rows §9 excludes are excluded here by the same two structural
    mechanisms and not by a list kept in this file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Dict, Sequence, Tuple, Union

from ingestion.adapters import http_get
from ingestion.backfill import backfill_range
from ingestion.backfill_adapters import VINTAGE_BACKFILLABLE_KINDS
from ingestion.backfill_calendar import (cboe_observation_dates, fred_observation_dates,
                                         yahoo_observation_dates)
from ingestion.backfill_dates import GENERABLE_AS_OF_RULES, observation_dates
from ingestion.catalog import INGREDIENTS, Ingredient
from ingestion.store import SqliteStore
from ingestion.vintage import has_no_revision_mechanism, requires_original_vintage

__all__ = [
    "CALENDAR_TIMEOUT_SECONDS",
    "EPISODES",
    "LEAD_IN_CALENDAR_DAYS",
    "OAS_FRED_FLOOR",
    "OAS_WIDENED_ROWS",
    "Episode",
    "assemble_dates",
    "backfillable_population",
    "calendar_identity",
    "date_source",
    "enclosing_span",
    "read_calendar",
    "row_dates",
]

#: §2's lead-in, in calendar days, applied before EVERY episode start — and the reason
#: :class:`Episode` carries a SPAN and derives its window rather than carrying both. 40 trading
#: days is ``max(BREADTH_LOOKBACK_ROWS, PROVISIONAL_PERSISTENCE) = 20`` rows doubled, because
#: ``_breadth_rows_ago`` answers "cannot confirm rising" if the row exactly 20 back is an
#: ``UNKNOWN`` carrying no breadth (CD-RT-001) and a backfilled lead-in will contain such rows
#: wherever a date was refused or came back EMPTY. 40 × 365.25/252 = 57.98 → 58, rounded up to
#: 60 for a clean boundary. Derived here rather than transcribed so that §2's table and this
#: tuple cannot disagree about a single episode's left edge: ``tests/test_wo117_run.py`` checks
#: the derived windows against §2 verbatim, which a pair of hardcoded columns could not be.
LEAD_IN_CALENDAR_DAYS = 60


@dataclass(frozen=True)
class Episode:
    """One of §2's eight episodes: a judged span, and the window that span implies.

    ``span_start``/``span_end`` are the run-up-through-recovery judgement §2 records; the WINDOW
    is the span with :data:`LEAD_IN_CALENDAR_DAYS` prepended, and it is the window that bounds
    the date list. The two are kept apart because only one of them is a judgement — moving a
    lead-in is an arithmetic consequence of the engine's row windows and moving a span is a call
    about what an episode covered.
    """

    __slots__ = ("key", "title", "span_start", "span_end")

    key: str
    title: str
    span_start: str
    span_end: str

    @property
    def window_start(self) -> str:
        """The span start with the lead-in prepended. §2's "Window (incl. 60d lead-in)" column."""
        return (date.fromisoformat(self.span_start)
                - timedelta(days=LEAD_IN_CALENDAR_DAYS)).isoformat()

    @property
    def window_end(self) -> str:
        """The window's right edge, which is the span's: nothing is appended after an episode."""
        return self.span_end

    @property
    def calendar_days(self) -> int:
        """Inclusive day count of the window. §2's last column, and what a test holds it to."""
        return (date.fromisoformat(self.window_end)
                - date.fromisoformat(self.window_start)).days + 1


#: §2's eight episodes, in chronological order. The SPANS are read off §2's "Episode span"
#: column; every window is derived. Ordered and disjoint, which a test holds — overlapping
#: windows would still produce a correct union (:func:`assemble_dates` deduplicates) but would
#: mean §2's 3,649-day total double-counted.
EPISODES: Tuple[Episode, ...] = (
    Episode("dotcom", "2000-02 dot-com", "2000-01-01", "2002-12-31"),
    Episode("gfc", "2007-09 GFC", "2007-06-01", "2009-12-31"),
    Episode("downgrade", "2011 downgrade/euro", "2011-05-01", "2011-12-31"),
    Episode("china", "2015-16 China/Feb low", "2015-08-01", "2016-03-31"),
    Episode("q4-2018", "Q4 2018", "2018-10-01", "2018-12-31"),
    Episode("covid", "March 2020 COVID", "2020-02-01", "2020-04-30"),
    Episode("2022", "2022 (incl. gilt)", "2022-01-01", "2022-12-31"),
    Episode("apr-2025", "April 2025", "2025-03-01", "2025-05-31"),
)

#: WO-1.3b-II item 8. FRED keeps only three years of the ICE BofA OAS series (since April 2026), so the earliest
#: observation it will serve is 2023-10-23. The April-2025 window opens 2024-12-31; for these two rows the request
#: window is widened back to that floor, contiguously. Every other row, and every other episode, is unchanged.
OAS_FRED_FLOOR = "2023-10-23"
OAS_WIDENED_ROWS = ("fred.BAMLH0A0HYM2", "fred.BAMLC0A0CM")

#: The deadline for ONE published-calendar GET. The three readers require ``timeout_seconds`` and
#: supply no default on purpose — "a FRED body is tens of thousands of rows where a live poll is
#: one, so the budget belongs to the caller that knows which it is asking for". This caller is
#: asking for the widest bodies any of them serve, and the widest was measured: ``^GSPC`` over
#: its whole life is 24,815 bars in 2,654,167 bytes in one response
#: (``evidence/wo117_yahoo_range_probe.json``), and the enclosing span here is a quarter of that
#: depth. 120 s is that with generous room. It is deliberately NOT ``BACKFILL_POLICY``'s 45 s:
#: that budget is sized for a vintage BISECTION of up to 17 small GETs, a different shape of
#: request, and borrowing it here would be reusing a number rather than choosing one.
CALENDAR_TIMEOUT_SECONDS = 120.0

#: The four date sources of §3, as :func:`date_source` names them. ``formula`` is the only one
#: that costs no GET.
DATE_SOURCES = ("formula", "fred", "cboe", "yahoo")


def backfillable_population() -> Tuple[Ingredient, ...]:
    """The 36 backfillable catalog rows, re-derived. §5's population, from §5's own predicates.

    Two filters and no list:

    * ``ing.kind in VINTAGE_BACKFILLABLE_KINDS`` — the kinds ``build_backfill_adapter`` can
      construct an adapter for at all, which is where the ``multpl``/``lbma``/``hermes``/
      ``manual`` rows leave (§9's mechanism 1).
    * for ``yahoo`` only, ``has_no_revision_mechanism("yahoo", ing.column)`` — the column tier,
      which is where the 51 ``adjclose`` rows leave (§9's mechanism 2). An adjusted close drifts
      retroactively with every later dividend and split, so there is no point-in-time quantity
      to recover; ``backfill_range`` would reach its ``ValueError`` for these rows and
      ``yahoo_observation_dates`` refuses them by name one layer earlier. Excluded HERE so the
      run never asks, rather than counting on either refusal to catch it.

    Catalog order is preserved, which is why :func:`run` sorts by route rather than relying on it.
    """
    population = []
    for ing in INGREDIENTS:
        if ing.kind not in VINTAGE_BACKFILLABLE_KINDS:
            continue
        if ing.kind == "yahoo" and not has_no_revision_mechanism("yahoo", ing.column):
            continue
        population.append(ing)
    return tuple(population)


def route(ing: Ingredient) -> str:
    """§5's four cost routes, for ORDERING and reporting only — never for choosing an adapter.

    ``backfill_range`` makes the adapter and label decision itself, from the same predicates, and
    this must not become a second opinion about it: the string returned here is a label on a
    progress line and a sort key, and if it ever disagreed with ``build_backfill_adapter`` the
    run would still do the right thing and merely print the wrong word for it. Kept because a
    36-hour run whose rows arrive in an order a reader can follow against §5/§6's tables is a
    run a human can check halfway through.
    """
    if ing.kind == "fred":
        return "4.1-fred-bisected" if requires_original_vintage(
            ing.ref, ing.transformation) else "4.2-fred-stable"
    if ing.kind == "cboe":
        return "4.3-cboe"
    if ing.kind == "yahoo":
        return "4.4-yahoo-close"
    raise ValueError(f"{ing.source_id} is kind {ing.kind!r}: no §5 route")


def date_source(ing: Ingredient) -> str:
    """Which of §3's four calendars this row's dates come off. One of :data:`DATE_SOURCES`.

    THE FORMULA IS ASKED FIRST, AND THAT IS A COST DECISION WITH A CORRECTNESS CHECK BEHIND IT.
    A ``month_end`` or ``quarter_end`` FRED row could be answered either way — by
    ``observation_dates``, which states the dating convention ``as_of_rule`` was declared for, or
    by ``fred_observation_dates``, which reads the published body. The formula is preferred
    because it costs no GET for 11 of the 36 rows, and it is SAFE to prefer because the two must
    agree where both answer: ``tests/test_wo117_calendar.py`` holds that they do on the real
    catalog rows, and ``backfill_calendar``'s own docstring records the tie-break if they ever
    stop ("where they differ the body wins"). If that test ever fails, this preference is the
    line to revisit — not the other way round.

    Everything else is dispatched on KIND, because for those rows the formula does not merely
    cost more, it refuses: all 14 FRED ``obs_date`` rows, all 3 CBOE and all 7 Yahoo rows are
    outside :data:`~ingestion.backfill_dates.GENERABLE_AS_OF_RULES` and ``observation_dates``
    raises for every one of them. That refusal is the gap §3.1 counts at 24 rows and
    ``backfill_calendar`` closes.
    """
    if ing.kind == "fred" and ing.as_of_rule in GENERABLE_AS_OF_RULES:
        return "formula"
    if ing.kind in ("fred", "cboe", "yahoo"):
        return ing.kind
    raise ValueError(
        f"{ing.source_id} is kind {ing.kind!r} with as-of rule {ing.as_of_rule!r}: no date "
        f"source in the tree answers for it (see ingestion.backfill_calendar)")


def calendar_identity(ing: Ingredient) -> tuple:
    """What this row's calendar is a calendar OF — the per-run cache key, and nothing more.

    Keyed on EXACTLY the arguments the reader for this row actually reads, so two rows share a
    key if and only if they would issue a byte-identical request:

    * ``fred`` — ``(ref, transformation)``. Not the ingredient row and not ``column``, because
      ``fred_observation_dates`` builds its URL from ``fred_graph_url(ing.ref,
      ing.transformation)`` and derives the column from the same pair. This is the one key that
      collapses: ``fred.DFII10`` and ``fred.DFII10.history`` are two catalog rows over one FRED
      series (§5.2), so the 14 ``obs_date`` rows cost 13 GETs, which is §3.1's own count.
      ``ing.history`` is NOT in the key and must not be — it is the only difference between
      those two rows and it is deliberately never passed to a calendar read, where it would
      truncate the body to its last N rows and return a date list that stops short.
    * ``cboe`` — ``(ref, column)``. ``column`` matters: the three rows read two different headers
      out of two differently-shaped bodies.
    * ``yahoo`` — ``(ref,)``. ``column`` is pinned to ``""`` for all 7 in-scope rows and anything
      else is refused by the reader, so it carries no information here.
    * ``formula`` — the pure rule, so ``(as_of_rule,)``. Cached for symmetry and not for cost;
      there is no body behind it.
    """
    source = date_source(ing)
    if source == "formula":
        return ("formula", ing.as_of_rule)
    if source == "fred":
        return ("fred", ing.ref, ing.transformation)
    if source == "cboe":
        return ("cboe", ing.ref, ing.column)
    return ("yahoo", ing.ref)


def enclosing_span(episodes: Sequence[Episode]) -> Tuple[str, str]:
    """The one span that contains every selected window: (earliest start, latest end).

    The span the calendars are read over, argued in this module's docstring. ISO dates compare
    correctly as strings — fixed width, zero padded, most significant field first — so ``min``
    and ``max`` over the strings are the chronological min and max, and nothing here has to
    parse a date to order one.
    """
    if not episodes:
        raise ValueError("no episodes selected; there is no span to read a calendar over")
    return (min(e.window_start for e in episodes), max(e.window_end for e in episodes))


def read_calendar(ing: Ingredient, start: str, end: str, *,
                  timeout_seconds: float = CALENDAR_TIMEOUT_SECONDS,
                  getter: Callable[..., str] = http_get) -> Tuple[str, ...]:
    """Every date ``ing``'s source published on within ``[start, end]``, from its OWN calendar.

    The dispatch :func:`date_source` names, and nothing else — the four functions behind it are
    interchangeable at a call site by their own design (same argument shape, same inclusive
    bounds, same ascending tuple of ISO strings), which is what makes this five lines instead of
    four code paths. ``getter`` is threaded through for the three that fetch and ignored by the
    formula, which has no body to read; ``tests/test_wo117_run.py`` uses it to assemble real date
    lists with no network.

    An ``AdapterFetchError`` propagates: a calendar that could not be read is not a calendar with
    no dates in it, and all three readers refuse to let a caller confuse the two. :func:`run`
    catches it PER ROW, which is a different thing from swallowing it — see there.
    """
    source = date_source(ing)
    if source == "formula":
        return observation_dates(ing, start, end)
    reader = {"fred": fred_observation_dates,
              "cboe": cboe_observation_dates,
              "yahoo": yahoo_observation_dates}[source]
    return reader(ing, start, end, timeout_seconds=timeout_seconds, getter=getter)


def assemble_dates(published: Sequence[str], episodes: Sequence[Episode],
                   *, cap: Union[int, None] = None) -> Tuple[str, ...]:
    """``published`` narrowed to the union of ``episodes``' windows: sorted, deduplicated. PURE.

    The whole of what this driver adds to a date list, and the reason it is a separate function
    with no I/O in it: the claim "the list handed to ``backfill_range`` is the union of the eight
    windows" is then a claim about arithmetic, testable against a handful of literal strings
    rather than against a 36-hour run.

    THE THREE PROPERTIES, AND WHY EACH IS CONSTRUCTED RATHER THAN HOPED FOR:

    * **UNION.** A date is kept if it falls inside ANY selected window, so a row's list is every
      date it published across all eight episodes and nothing from the gaps between them — which
      is the whole economy of an episode-windowed backfill (§2: 3,649 days against ~9,800 for a
      continuous one).
    * **DEDUPLICATED.** Two windows that overlapped would otherwise offer the same date twice,
      and ``backfill_range`` would fetch it, store it, then skip the second copy — a wasted GET
      and a confusing ``skipped`` count rather than a wrong answer. §2's eight windows do not
      overlap (a test holds it), so this guards a caller's ``--episode`` selection and any
      future re-cut of the spans, not today's table. ``set`` is also what makes the result
      independent of the order the windows are given in.
    * **SORTED.** ``backfill_range`` honours "the order given" and paces between fetches, so
      ascending order is what makes a half-finished run's progress legible: every date before the
      last one printed is done. The readers already return ascending, but the per-window
      concatenation below does not preserve that on its own, so it is re-established here rather
      than inherited.

    ``cap`` takes the first ``cap`` dates of EACH window rather than of the whole union, and it
    exists for one purpose: the tiny real-network proof this module's round is actually
    delivering. Per-window is the only useful spelling of it — ``--max-dates-per-episode 2``
    over two episodes proves the union across episodes, which a cap on the total would collapse
    into the first window. It must never be set for a real run and :func:`run` says so in the
    record it writes.

    The bounds are compared as STRINGS, which for fixed-width zero-padded ISO dates is the same
    comparison ``date.fromisoformat`` would give after two parses — and the dates arrive here
    already validated as dates by whichever reader produced them.
    """
    if cap is not None and cap < 1:
        raise ValueError(f"cap must be at least 1 if given, not {cap}")
    kept: list = []
    for episode in episodes:
        inside = [d for d in published if episode.window_start <= d <= episode.window_end]
        kept.extend(inside[:cap] if cap is not None else inside)
    return tuple(sorted(set(kept)))


def _oas_widened_window(ing: Ingredient, episodes: Sequence[Episode]) -> Union[Tuple[str, str], None]:
    """``[OAS_FRED_FLOOR, April-2025 window start)`` for the two OAS rows when that episode is selected, else None."""
    if ing.source_id not in OAS_WIDENED_ROWS:
        return None
    apr = [e for e in episodes if e.key == "apr-2025"]
    if not apr or apr[0].window_start <= OAS_FRED_FLOOR:
        return None
    return (OAS_FRED_FLOOR, apr[0].window_start)


def row_dates(ing: Ingredient, episodes: Sequence[Episode], *,
              timeout_seconds: float = CALENDAR_TIMEOUT_SECONDS,
              getter: Callable[..., str] = http_get,
              cache: Union[Dict[tuple, Tuple[str, ...]], None] = None,
              cap: Union[int, None] = None) -> Tuple[Tuple[str, ...], bool]:
    """One row's full date list over the union of ``episodes``. Returns ``(dates, was_fetched)``.

    One calendar read over the enclosing span, then :func:`assemble_dates`. ``was_fetched`` is
    ``False`` when ``cache`` already held this row's calendar or when the source is the formula,
    and it is returned rather than inferred so :func:`run` can count the calendar GETs it
    actually issued and keep that number apart from the reading GETs ``backfill_range`` reports.
    """
    start, end = enclosing_span(episodes)
    key = calendar_identity(ing)
    fetched = False
    if cache is not None and key in cache:
        published = cache[key]
    else:
        published = read_calendar(ing, start, end, timeout_seconds=timeout_seconds, getter=getter)
        fetched = date_source(ing) != "formula"
        if cache is not None:
            cache[key] = published
    dates = assemble_dates(published, episodes, cap=cap)
    widened = _oas_widened_window(ing, episodes)
    if widened is not None:
        extra = [d for d in published if widened[0] <= d < widened[1]]
        dates = tuple(sorted(set(dates) | set(extra[:cap] if cap is not None else extra)))
    return dates, fetched


def _clock() -> datetime:
    return datetime.now(timezone.utc)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def select_rows(only: Sequence[str]) -> Tuple[Ingredient, ...]:
    """The population, or the named subset of it. An unknown name RAISES rather than runs nothing.

    A typo in ``--only`` that quietly selected zero rows would make a run that did nothing look
    exactly like a run that found nothing to do, which on a resumable driver is the one pair of
    outcomes that must never be confused.
    """
    population = backfillable_population()
    if not only:
        return population
    by_id = {ing.source_id: ing for ing in population}
    unknown = [name for name in only if name not in by_id]
    if unknown:
        raise ValueError(
            f"--only names {unknown} which are not in the {len(population)}-row backfillable "
            f"population; a row outside it is excluded by §9's two structural mechanisms "
            f"(wrong kind, or an adjclose column) and cannot be backfilled by naming it")
    # Deduplicated, and in population order rather than in the order typed: the caller's typing
    # order is unrelated to the route grouping `run` sorts by for its own report.
    return tuple(ing for ing in population if ing.source_id in set(only))


def select_episodes(keys: Sequence[str]) -> Tuple[Episode, ...]:
    """§2's eight episodes, or the named subset. An unknown key raises, for the same reason."""
    if not keys:
        return EPISODES
    by_key = {e.key: e for e in EPISODES}
    unknown = [key for key in keys if key not in by_key]
    if unknown:
        raise ValueError(f"--episode names {unknown}; §2 declares "
                         f"{[e.key for e in EPISODES]}")
    return tuple(e for e in EPISODES if e.key in set(keys))


def run(rows: Sequence[Ingredient], episodes: Sequence[Episode], store: SqliteStore, *,
        run_id: str, dates_only: bool = False, cap: Union[int, None] = None,
        timeout_seconds: float = CALENDAR_TIMEOUT_SECONDS,
        getter: Callable[..., str] = http_get,
        api_key: Union[str, None] = None) -> dict:
    """Walk ``rows`` sorted by §5's route grouping: read each one's calendar, then hand it to ``backfill_range``.

    PROGRESS IS PRINTED AS EACH ROW FINISHES, NOT COLLECTED AND RETURNED AT THE END, and for a
    36-hour run that is the difference between an interruption costing nothing and costing the
    record of what was done. The returned document is a convenience for ``--out``; stdout is the
    durable log, and because the store is the only state that matters a resumed run re-derives
    everything else.

    A CALENDAR FAILURE IS ONE ROW'S, NOT THE RUN'S. This mirrors ``backfill_range``'s own rule
    that "one date's failure is one date's failure" at the layer above it, and it is not a
    duplicate of that handling: ``backfill_range`` cannot report a failure that happened before
    it was called, and a 503 on row 3's calendar GET must not cost rows 4 through 36. The row is
    recorded in ``calendar_failed`` with the error CLASS and nothing else (PBG-SEC-002: no
    message, no URL, no exception text) and the run continues. It is also the one thing that
    makes the exit code non-zero, because it is the one thing that makes the run INCOMPLETE as
    opposed to merely finding gaps.

    ``dates_only`` stops after the calendar reads. It is how the next round can see the REAL date
    counts — replacing §3/§6's holiday-deduction model, which is stated there as a model and not
    a fact — for the price of 23 GETs instead of 190,391, before deciding to spend the rest.
    """
    ordered = sorted(rows, key=lambda ing: (route(ing), ing.source_id))
    span = enclosing_span(episodes)
    cache: Dict[tuple, Tuple[str, ...]] = {}
    calendar_fetches = 0
    records: list = []
    calendar_failed: list = []

    print(f"-- wo117 run {run_id}: {len(ordered)} rows x {len(episodes)} episodes "
          f"({', '.join(e.key for e in episodes)}), calendars read over {span[0]}..{span[1]}"
          + (f", capped at {cap} dates per episode" if cap is not None else "")
          + (", DATES ONLY — no reading will be fetched or stored" if dates_only else ""),
          flush=True)

    for position, ing in enumerate(ordered, start=1):
        head = f"[{position}/{len(ordered)}] {ing.source_id} ({route(ing)}, {date_source(ing)})"
        try:
            dates, fetched = row_dates(ing, episodes, timeout_seconds=timeout_seconds,
                                       getter=getter, cache=cache, cap=cap)
        except Exception as failure:
            calendar_fetches += 1  # it reached the network and came back wrong; still a GET
            calendar_failed.append({"source_id": ing.source_id,
                                    "date_source": date_source(ing),
                                    "error_class": getattr(failure, "error_class",
                                                           type(failure).__name__)})
            print(f"{head} CALENDAR UNREADABLE "
                  f"{getattr(failure, 'error_class', type(failure).__name__)} — row skipped, run "
                  f"continues", flush=True)
            continue
        calendar_fetches += int(fetched)
        record = {"source_id": ing.source_id, "route": route(ing),
                  "date_source": date_source(ing), "dates": len(dates),
                  "first_date": dates[0] if dates else None,
                  "last_date": dates[-1] if dates else None,
                  "calendar_fetched": fetched}
        if dates_only:
            print(f"{head} {len(dates)} dates "
                  f"{record['first_date']}..{record['last_date']}", flush=True)
            records.append(record)
            continue
        result = backfill_range(ing, dates, store, _clock, run_id=run_id, api_key=api_key)
        record["vintage"] = result.vintage
        record["counts"] = result.counts
        record["admitted_dates"] = list(result.admitted)
        record["refused"] = [list(pair) for pair in result.refused]
        record["failed"] = [list(pair) for pair in result.failed]
        records.append(record)
        print(f"{head} {len(dates)} dates, {result.vintage}: {result.counts}", flush=True)

    spent = sum(r.get("counts", {}).get("fetches", 0) for r in records)
    return {
        "run_id": run_id,
        "work_order": "CERBERUS-WO-1.17",
        "estimate": "governance/engineering/WO-1.17-COST-ESTIMATE.md",
        "episodes": [{"key": e.key, "title": e.title,
                      "span": [e.span_start, e.span_end],
                      "window": [e.window_start, e.window_end],
                      "calendar_days": e.calendar_days} for e in episodes],
        "calendar_span": list(span),
        "lead_in_calendar_days": LEAD_IN_CALENDAR_DAYS,
        "population_rows": len(backfillable_population()),
        "selected_rows": len(ordered),
        "dates_only": dates_only,
        "max_dates_per_episode": cap,
        "is_full_run": cap is None and len(ordered) == len(backfillable_population())
                       and len(episodes) == len(EPISODES) and not dates_only,
        "calendar_fetches": calendar_fetches,
        "distinct_calendars": len(cache),
        "reading_fetches": spent,
        "dates_total": sum(r["dates"] for r in records),
        "admitted_total": sum(r.get("counts", {}).get("admitted", 0) for r in records),
        "skipped_total": sum(r.get("counts", {}).get("skipped", 0) for r in records),
        "refused_total": sum(r.get("counts", {}).get("refused", 0) for r in records),
        "failed_total": sum(r.get("counts", {}).get("failed", 0) for r in records),
        "calendar_failed": calendar_failed,
        "rows": records,
    }


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        description="WO-1.17: backfill the 36-row population over the 8 episode windows")
    parser.add_argument("--db", required=True,
                        help="the SQLite store to write into. REQUIRED and never defaulted — "
                             "the caller owns the path, and a default could reach cd-live-data")
    parser.add_argument("--out", help="where to write the JSON run record (optional; stdout is "
                                      "the durable progress log either way)")
    parser.add_argument("--only", action="append", default=[], metavar="SOURCE_ID",
                        help="restrict to this catalog row; repeatable")
    parser.add_argument("--episode", action="append", default=[], metavar="KEY",
                        help=f"restrict to this episode; repeatable. "
                             f"{', '.join(e.key for e in EPISODES)}")
    parser.add_argument("--max-dates-per-episode", type=int, default=None, metavar="N",
                        help="take only the first N dates of each window. FOR A PROOF RUN ONLY; "
                             "a real execution leaves this unset")
    parser.add_argument("--dates-only", action="store_true",
                        help="read the calendars and report the date counts; fetch and store no "
                             "reading at all")
    parser.add_argument("--calendar-timeout", type=float, default=CALENDAR_TIMEOUT_SECONDS,
                        help=f"deadline for one calendar GET (default {CALENDAR_TIMEOUT_SECONDS})")
    parser.add_argument("--run-id", default=None,
                        help="the collector run id recorded against every attempt. Defaults to a "
                             "fresh one; name it to tie a resumed run to the one it continues")
    args = parser.parse_args(argv)

    try:
        rows = select_rows(args.only)
        episodes = select_episodes(args.episode)
    except ValueError as refusal:
        print(f"-- STOP: {refusal}", flush=True)
        return 1

    # The FRED REST key is read HERE, once, and handed down as an argument; nothing below this
    # function consults the environment. It is required ONLY when the run will actually spend a
    # route-4.1 GET: a dates-only run, or a selection with no revision-prone FRED row, never
    # touches the vintage endpoint and must not be made to carry a credential it will not use.
    api_key = None
    if not args.dates_only and any(
            ing.kind == "fred" and requires_original_vintage(ing.ref, ing.transformation)
            for ing in rows):
        api_key = (os.environ.get("FRED_API_KEY") or "").strip() or None
        if api_key is None:
            print("-- STOP: REFUSED: FRED_API_KEY is unset. The selected rows include revision-prone "
                  "FRED series (route 4.1), whose first-published figures are read through FRED's "
                  "keyed REST API.", flush=True)
            return 1

    run_id = args.run_id or "wo117-" + uuid.uuid4().hex[:12]
    started = _now()
    with SqliteStore(args.db) as store:
        document = run(rows, episodes, store, run_id=run_id, dates_only=args.dates_only,
                       cap=args.max_dates_per_episode, timeout_seconds=args.calendar_timeout,
                       api_key=api_key)
    document["ran_utc"] = started
    document["finished_utc"] = _now()
    document["database"] = args.db

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write("\n")

    print(f"-- done: {document['selected_rows']} rows, {document['dates_total']} dates, "
          f"{document['calendar_fetches']} calendar GETs ({document['distinct_calendars']} "
          f"distinct), {document['reading_fetches']} reading GETs; "
          f"admitted={document['admitted_total']} skipped={document['skipped_total']} "
          f"refused={document['refused_total']} failed={document['failed_total']}"
          + (f"; written to {args.out}" if args.out else ""), flush=True)
    if document["calendar_failed"]:
        # The run is INCOMPLETE, which is not the same as a run that found gaps. Re-running is
        # safe and cheap for the rows that did land: every stored date comes back `skipped`.
        print(f"-- INCOMPLETE: {len(document['calendar_failed'])} row(s) had no readable "
              f"calendar and were never asked for; re-run to retry them", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
