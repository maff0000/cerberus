"""The backfill DRIVER: one named observation date at a time, into the store, labelled.

WO-1.14. Everything upstream of here decides; this module is the only thing that MOVES.
``ingestion.vintage`` declares which (series, transformation) pairs were measured to be
revised and from which date that measurement begins; ``ingestion.backfill_adapters``
constructs the adapter that declaration implies. Neither fetches, paces, stores or labels —
this does, and nothing else in the tree does any of it.

ONE FUNCTION, AND THE DATES ARE THE CALLER'S
    :func:`backfill_range` takes an EXPLICIT list of observation dates. There is no cadence
    logic here and there must not be: "which dates does a business-daily FRED series have
    between 1999 and today" is a question about a publication calendar, it differs per
    series, and a driver that guessed at it would be inventing the very dates whose values
    it then claims to have recovered. The caller computes the dates — from the catalog, from
    a body it already holds, or by hand — and this function answers for exactly those.

WHAT HAPPENS TO ONE DATE, IN ORDER, AND WHY THE FIRST TWO ANSWERS COST NO GET
    1.  **Refused, unfetched** — the pair was measured STABLE and the date is before
        :data:`~ingestion.vintage.STABILITY_MEASURED_FROM`. The stable branch's whole
        authority is a measurement over the replay window; before the left edge of that
        window the measurement says NOTHING, so today's body is not evidence about that date
        and there is no vintage read to fall back on here. DFF is the case that makes it
        concrete rather than theoretical — stable in zero of 2,369 shared observations from
        1999 on, materially different in 93 of its 18,624 before that — so a 1985 DFF
        reading taken from today's body would be exactly the forgery this work order exists
        to prevent. Refused, and recorded as refused: a date nobody fetched is not a date
        that failed, and it is certainly not a date we have.
    2.  **Skipped, unfetched** — the source period this date maps to is already admitted.
        Asked of the store BEFORE the fetch (``SqliteStore.is_admitted``) rather than
        discovered after it by ``admit_if_absent``, because the point of a re-runnable range
        is that a range already half-done costs GETs only for the half that is missing. A
        re-run of a completed range issues NO requests at all, which is the property
        ``tests/test_wo114_backfill.py`` measures by counting them.
    3.  **Fetched** — through ``crash_detector.collectors.collect``, so a backfilled reading
        passes the same door a live one does: every attempt recorded including the failures,
        the payload validated against the adapter's declared schema, the period claimed
        exactly once. This driver does not re-implement any of that and may not.

THE VINTAGE LABEL IS DERIVED, NOT CONSTANT — AND THIS IS THE ONE PLACE IT IS WRITTEN
    ``VINTAGE_ORIGINAL`` for the vintage branch, ``VINTAGE_CURRENT_ONLY`` for the
    measured-stable one, read off the same ``requires_original_vintage`` call that chose the
    adapter. Both labels are their own stated meanings word for word: a reading out of
    ``AlfredVintageAdapter`` carries the figure the source FIRST published and the vintage
    date the server itself named; a reading out of ``FredAdapter`` carries the figure TODAY's
    body holds for that past period — the right period, since WO-1.15, but today's revision
    of it — which is exactly what ``current_only`` says, admitted on the authority of
    :data:`~ingestion.vintage.REVISION_STABLE` plus the date test in step 1 above.

    Labelling the stable branch ``original`` would have a DFF reading from today's body
    claim to be the figure first published — the one claim ``ingestion.vintage`` exists to
    stop, and the correction recorded on :data:`~ingestion.vintage.VINTAGE_ORIGINAL` itself.
    The label reaches the row at INSERT, through ``admit_if_absent(key, vintage=...)``,
    because ``raw_reading`` is append-only and no later UPDATE could add it.

THE DATE GATE IS A CHECK ON THE ANSWER, NOT A DESCRIPTION OF ONE ADAPTER'S LIMIT
    WO-1.14 declared a limit here: the stable branch asked FRED for the whole current body
    and read its LATEST observation, so a date years back came back as a perfectly good
    reading of the WRONG period, and per-date selection out of that body was OWED. WO-1.15
    did it — the stable branch now windows the request on the date asked for and matches the
    row by EXACT date (``ingestion.adapters.parse_fred_csv_for_date``) — so the stable branch
    answers for an arbitrary past date within the measurement window, and the paragraph that
    said otherwise is gone rather than quietly left standing.

    **THE GATE BELOW IS UNCHANGED, AND THAT IS THE POINT.** It computes the source period it
    ASKED for and refuses to admit a reading that answered for a different one, reporting
    :data:`FAILED_DATE_NOT_ANSWERED`, and it does that for WHICHEVER adapter answered — it was
    never a statement about ``FredAdapter``, so closing ``FredAdapter``'s limit does not
    retire it. What it guards now is that no later change on either branch — a source that
    ignores a window (plain FRED demonstrably does, for a window before a series' first
    observation: ``evidence/wo115_fred_window_probe.json``), a parser that read a row by
    position, a transformation that shifts a period — can put a number under a key nobody
    asked for without this driver catching it and storing nothing.

    A date the source simply has no observation for is a different answer and is reported as
    one: EMPTY, carried into ``failed`` with the store's own discriminator (FRED answers a
    gap date with a 404, which ``FredAdapter`` translates for a dated request — see that
    class). Nothing is stored in either case, which is what a gap IS.

    **NO EGRESS ALLOWLIST PERMITS ALFRED YET.** ``BACKFILL_EGRESS_HOSTS`` records the host
    and records what is owed — a compose service of its own with its own ``x-egress``
    ALLOWLIST and a registered destination. Until that lands, this driver runs where egress
    is unrestricted (a seat's own shell) and is fail-closed inside the deployed stack, which
    is the accurate description of a backfill that is not yet deployed.

THE LOOP NEVER ABORTS, AND EVERY DATE IS ACCOUNTED FOR
    One date's failure is one date's failure. A transport error, a body we cannot read, an
    observation no vintage ever published, an unreadable date string, even a defect in this
    driver — recorded against that date and the range continues, because a 6,000-date
    backfill that stops at the first 503 has turned a recoverable gap into a lost afternoon.
    The failure is carried as a CLASS and nothing else — ``AdapterFetchError.error_class``
    where the adapter named one, the store's own ``OK``/``EMPTY``/``MALFORMED`` discriminator
    where it did not, an exception type name where the defect is ours. No message, no URL, no
    exception text (PBG-SEC-002), and no new failure shape invented here.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Sequence, Union

from crash_detector.collectors import DelayKind, ReadingKey, RetryPolicy, collect
from crash_detector.observations import OK, FetchFailed, outcome_class
from crash_detector.time_utc import format_utc

from ingestion.adapters import as_of_for
from ingestion.backfill_adapters import VINTAGE_BACKFILLABLE_KINDS, build_backfill_adapter
from ingestion.catalog import Ingredient
from ingestion.store import SqliteStore
from ingestion.vintage import (STABILITY_MEASURED_FROM, VINTAGE_CURRENT_ONLY, VINTAGE_ORIGINAL,
                               requires_original_vintage)

__all__ = [
    "BACKFILL_PACING_SECONDS",
    "BACKFILL_POLICY",
    "FAILED_DATE_NOT_ANSWERED",
    "REFUSED_STABILITY_UNMEASURED",
    "BackfillResult",
    "backfill_range",
]

#: Courtesy gap between FETCHES — never before the first one, and never around a date that
#: was skipped or refused, because neither of those touched the network. The live loop's
#: :data:`ingestion.run.PACING_SECONDS` is 1.5 s across ~25 sources once per pass; a backfill
#: issues thousands of requests in a row against one host, and 0.7 s is the gap this seat
#: chose for that. It is a courtesy and not a published rate limit: FRED documents none for
#: the keyless graph CSV, so this is deliberately slower than necessary rather than tuned to
#: an edge nobody stated. A real 429 is a recorded ``HTTP_ERROR`` for that date, not a
#: surprise this constant is pretending to prevent.
BACKFILL_PACING_SECONDS = 0.7

#: ``timeout_seconds`` is a TOTAL deadline per attempt, and for
#: :class:`~ingestion.adapters.AlfredVintageAdapter` ONE attempt is a bisection of up to
#: ``2 + ceil(log2(days))`` GETs — 17 for a 1960 observation asked today. 45 s is that search
#: with room, and it is under the framework's 60 s ceiling. ``max_attempts=2`` because a
#: backfill has no next pass to retry on the way the live loop does: it is this run or a
#: reported gap.
BACKFILL_POLICY = RetryPolicy(max_attempts=2, timeout_seconds=45.0, backoff_seconds=4.0)

#: Refusal reason: measured stable, but the date is before the measurement's own left edge
#: (:data:`~ingestion.vintage.STABILITY_MEASURED_FROM`). Nothing was fetched.
REFUSED_STABILITY_UNMEASURED = "STABILITY_UNMEASURED_BEFORE_WINDOW"

#: Failure class: the fetch succeeded and answered for a DIFFERENT source period than the one
#: asked for, so nothing was stored. Today's body answering for today when a 2005 date was
#: asked — the declared limit of the stable branch, reported as a miss rather than admitted.
FAILED_DATE_NOT_ANSWERED = "OBSERVATION_DATE_NOT_ANSWERED"


@dataclass(frozen=True)
class BackfillResult:
    """What one range did, date by date. Every date given appears in exactly one bucket.

    ``refused`` and ``failed`` carry ``(date, class)`` pairs rather than counts because a
    count cannot be acted on: an operator re-running a range needs to know WHICH dates are
    missing and which class of thing happened to them. ``fetches`` is the number of requests
    this run actually issued, which is how "a re-run of a finished range is free" is stated
    as a measurable fact rather than as an intention.
    """

    __slots__ = ("source_id", "vintage", "admitted", "skipped", "refused", "failed", "fetches")

    source_id: str
    #: The label every reading this run admitted carries. One per range, because the pair's
    #: measured-stability — and therefore the branch and the label — is a property of the
    #: pair and not of the date.
    vintage: str
    admitted: tuple[str, ...]
    #: Dates whose source period was already in the store. No request was issued for these.
    skipped: tuple[str, ...]
    refused: tuple[tuple[str, str], ...]
    failed: tuple[tuple[str, str], ...]
    fetches: int

    @property
    def counts(self) -> dict:
        """The four buckets as counts, plus the request count. For a one-line report."""
        return {
            "admitted": len(self.admitted),
            "skipped": len(self.skipped),
            "refused": len(self.refused),
            "failed": len(self.failed),
            "fetches": self.fetches,
        }


class _VintageLedger:
    """A ``ReadingLedger`` that supplies the vintage label, and the gate on WHICH period.

    ``collect`` admits through the ``ReadingLedger`` protocol, whose ``admit_if_absent`` takes
    a key and nothing else — correctly, since the live loop has no vintage to state. So the
    label arrives by wrapping the store for this one date rather than by widening that
    protocol or by a second write afterwards, which the append-only trigger forbids anyway.

    IT IS ALSO THE DATE GATE, and that is not an extra job bolted on — it is the same job. The
    only moment at which "is this the period we asked for" can be answered is the moment the
    key is in hand and the row is not yet written. ``False`` is returned for a key we did not
    ask for, which is the protocol's own "this call did not claim it" and is exactly true: the
    reading is not stored. The caller reads :attr:`answered_for` to tell that apart from an
    ordinary duplicate, so no fact is lost in the narrowing.

    The unclaimed payload stays pending in the store and is dropped when it closes — which is
    what an unadmitted reading IS. The attempt row for it was written, so the fetch is still
    in the record; only the reading is absent.
    """

    __slots__ = ("_store", "_expected", "_vintage", "answered_for")

    def __init__(self, store: SqliteStore, expected: ReadingKey, vintage: str) -> None:
        self._store = store
        self._expected = expected
        self._vintage = vintage
        #: The key ``collect`` offered when it was NOT the one asked for; ``None`` otherwise.
        self.answered_for: Union[ReadingKey, None] = None

    def admit_if_absent(self, key: ReadingKey) -> bool:
        if tuple(key) != tuple(self._expected):
            self.answered_for = key
            return False
        return self._store.admit_if_absent(key, vintage=self._vintage)


def backfill_range(ing: Ingredient, dates: Sequence[str], sink: SqliteStore,
                   clock: Callable[[], datetime], *,
                   pace: float = BACKFILL_PACING_SECONDS,
                   run_id: Union[str, None] = None) -> BackfillResult:
    """Backfill ``ing`` over exactly ``dates``, in the order given. Returns what happened.

    ``dates`` are observation dates as the SOURCE dates them (``YYYY-MM-DD``), pre-computed
    by the caller — see this module's docstring on why no cadence is derived here. ``sink``
    is the store, which is the ``ObservationSink``, the ``ReadingLedger`` and the thing asked
    whether a period is already admitted; ``clock`` is read fresh per date, as the live loop
    reads it fresh per ingredient.

    ``pace`` exists for the same reason ``ingestion.run.run_once``'s does: so a test can
    measure this function's behaviour without waiting for its courtesy gaps. Production
    callers leave it alone.

    A kind outside :data:`~ingestion.backfill_adapters.VINTAGE_BACKFILLABLE_KINDS` RAISES,
    before any date is touched. That is a caller's error about the whole range rather than a
    property of a date, and reporting it once per date would bury one defect under a thousand
    identical failures.
    """
    if ing.kind not in VINTAGE_BACKFILLABLE_KINDS:
        raise ValueError(
            f"{ing.source_id} is kind {ing.kind!r}; a point-in-time backfill is declared only for "
            f"{VINTAGE_BACKFILLABLE_KINDS} (see ingestion.backfill_adapters)"
        )
    run_id = run_id or "backfill-" + uuid.uuid4().hex[:12]
    # ONE call, for the whole range: the measured-stability of a pair decides both which
    # adapter every date gets and which label every admitted reading carries.
    original = requires_original_vintage(ing.ref, ing.transformation)
    vintage = VINTAGE_ORIGINAL if original else VINTAGE_CURRENT_ONLY

    admitted: list = []
    skipped: list = []
    refused: list = []
    failed: list = []
    fetches = 0

    for observation_date in dates:
        if not original and observation_date < STABILITY_MEASURED_FROM:
            # Measured stable says nothing about a date the measurement does not cover, and
            # the stable branch has no vintage to fall back on. Unfetched, and reported.
            refused.append((observation_date, REFUSED_STABILITY_UNMEASURED))
            continue
        ledger = None
        try:
            # The period THIS date claims, by the catalog's own rule and the same pure
            # function the adapters use — so the key asked about here is the key a reading
            # for this date would be admitted under.
            key = (ing.source_id, format_utc(as_of_for(observation_date, ing.as_of_rule, clock())))
            if sink.is_admitted(key):
                skipped.append(observation_date)
                continue
            if fetches and pace > 0:
                time.sleep(pace)  # between fetches only; a skip or a refusal paces nothing
            fetches += 1
            ledger = _VintageLedger(sink, key, vintage)
            result = collect(
                build_backfill_adapter(ing, observation_date, clock),
                policy=BACKFILL_POLICY, sink=sink, ledger=ledger, collector_run_id=run_id,
                started_utc=clock(), delay=DelayKind.WALL_CLOCK,
            )
        except Exception as failure:  # one date's defect, never the range's end
            failed.append((observation_date, type(failure).__name__))
            continue
        if result.reading_admitted:
            admitted.append(observation_date)
        elif ledger.answered_for is not None:
            failed.append((observation_date, FAILED_DATE_NOT_ANSWERED))
        elif isinstance(result.final_outcome, OK):
            # The period was claimed between the question and the answer. Rare, and the
            # UNIQUE constraint is what decided it, exactly as it is meant to.
            skipped.append(observation_date)
        elif isinstance(result.final_outcome, FetchFailed):
            failed.append((observation_date, result.final_outcome.error_class))
        else:
            # EMPTY or MALFORMED: the store's own discriminator, not a new vocabulary. EMPTY
            # is a real answer — no vintage ever published this observation — and it is still
            # a date this backfill does not have, which is what ``failed`` records.
            failed.append((observation_date, outcome_class(result.final_outcome)))

    return BackfillResult(
        source_id=ing.source_id,
        vintage=vintage,
        admitted=tuple(admitted),
        skipped=tuple(skipped),
        refused=tuple(refused),
        failed=tuple(failed),
        fetches=fetches,
    )
