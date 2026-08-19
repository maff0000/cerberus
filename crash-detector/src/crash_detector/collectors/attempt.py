"""One row per fetch attempt, and the idempotency key (BLUEPRINT §5, CD-AC-001).

**Every fetch attempt writes a row, including the failures.** This is the single most
important property in the collector component. A failed fetch that writes nothing is
indistinguishable from a fetch that was never scheduled, and both are indistinguishable
from a source that had nothing to report — three states that demand different responses,
collapsed into one absence (Standards Baseline §8).

----

WHY :class:`AttemptRecord` COMPOSES :class:`~crash_detector.observations.ObservationRecord`
RATHER THAN REPLACING OR EXTENDING IT.

:mod:`crash_detector.observations` is the collector/engine contract and the Project Lead
has ruled it KEEP (CD-D-008). Its :class:`~crash_detector.observations.ObservationRecord`
carries exactly what the ENGINE needs to read: ``source_id``, ``observed_utc``, and the
four-way outcome. That is deliberately the whole of the engine's diet, and adding
collector bookkeeping to it would push retry counts and adapter identities across the
§5/§7 boundary into a type the engine consumes.

The collector needs more than the engine reads — which attempt this was, which adapter ran
it, which run it belonged to, and when it was requested as distinct from when it
completed. Those are properties of the ATTEMPT, not of the observation. So this type holds
an ``ObservationRecord`` and adds them around it. One database row in ``raw.observation``
carries the union of both; the engine selects a projection.

The alternative — adding four required fields to ``ObservationRecord`` — was rejected
because it would have forced a change to increment 1's delivered tests, and a test changed
to accommodate new code is how a guard quietly stops guarding.

----

IDEMPOTENCY, AND THE TWO THINGS IT IS NOT THE SAME FOR.

BLUEPRINT §5: "Re-fetching the same source-period is idempotent on
``(source_id, source_as_of_utc)`` — a retry adds an observation row, never a duplicate
reading." Those are two different tables with two different rules, and conflating them
loses one of the properties:

* the ATTEMPT log is append-only and unconstrained. Every attempt appends, always. A
  unique constraint here would deduplicate failures out of the record, and the count of
  failed attempts is exactly what tells an operator a source is dying.
* the READING is unique on ``(source_id, source_as_of_utc)``. Re-fetching the same period
  must not produce a second reading of it.

:data:`ReadingKey` exists **only for** :class:`~crash_detector.observations.OK`. A failed
fetch has no source period to be idempotent about, and inventing one for it — the fetch
instant, say — would make every failure a distinct "reading" of nothing.

Deliverable A5's SQL must mirror both halves: ``raw.observation`` append-only with no
unique constraint and no ``UPDATE``/``DELETE`` grant, and the reading identified by a
``UNIQUE (source_id, source_as_of_utc)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Union

from crash_detector.observations import OK, ObservationRecord, outcome_class
from crash_detector.time_utc import ensure_utc, format_utc

__all__ = [
    "ReadingKey",
    "AttemptRecord",
    "ObservationSink",
    "ReadingLedger",
]

#: ``(source_id, source_as_of_utc)`` rendered as ISO-8601 with an explicit ``Z``.
#:
#: The timestamp is carried as its canonical STRING rather than as a ``datetime`` because
#: this key is a database identity: two ``datetime`` values that denote the same instant
#: in different offsets are equal in Python and are the same row in the store, but they
#: are not the same dictionary key. Normalising once, here, means the in-memory ledger and
#: the ``UNIQUE`` constraint agree about what "the same" means.
ReadingKey = tuple[str, str]


@dataclass(frozen=True)
class AttemptRecord:
    """One fetch attempt — one row of ``raw.observation`` — whatever came of it."""

    observation: ObservationRecord
    adapter_id: str
    collector_run_id: str
    attempt_number: int
    requested_utc: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.observation, ObservationRecord):
            raise TypeError(
                "AttemptRecord.observation must be an ObservationRecord, got "
                f"{type(self.observation).__name__}"
            )
        for name in ("adapter_id", "collector_run_id"):
            observed = getattr(self, name)
            if not isinstance(observed, str) or not observed:
                raise ValueError(f"AttemptRecord requires a non-empty {name}")
        if isinstance(self.attempt_number, bool) or not isinstance(
            self.attempt_number, int
        ):
            raise TypeError("AttemptRecord.attempt_number must be an int")
        if self.attempt_number < 1:
            raise ValueError("attempt numbering starts at 1")
        object.__setattr__(self, "requested_utc", ensure_utc(self.requested_utc))
        if self.requested_utc > self.observation.observed_utc:
            raise ValueError(
                "AttemptRecord.requested_utc is after the attempt completed; a fetch "
                "cannot finish before it started, and a row that says otherwise makes "
                "every latency figure derived from it wrong"
            )

    @property
    def source_id(self) -> str:
        return self.observation.source_id

    @property
    def outcome(self) -> object:
        return self.observation.outcome

    @property
    def completed_utc(self) -> datetime:
        """When the attempt finished. The observation's own ``observed_utc``."""
        return self.observation.observed_utc

    @property
    def outcome_class(self) -> str:
        """The persisted discriminator: ``OK`` | ``FETCH_FAILED`` | ``MALFORMED`` | ``EMPTY``."""
        return outcome_class(self.observation.outcome)

    @property
    def elapsed_seconds(self) -> float:
        """How long the attempt took, from request to completion."""
        return (self.completed_utc - self.requested_utc).total_seconds()

    @property
    def reading_key(self) -> Union[ReadingKey, None]:
        """``(source_id, source_as_of_utc)`` for an ``OK`` attempt, else ``None``.

        ``None`` means "this attempt reported no source period", which is a different
        fact from "the source period was midnight" and from "the period is now". It is
        not a default and nothing downstream may substitute one for it.
        """
        outcome = self.observation.outcome
        if isinstance(outcome, OK):
            return (self.source_id, format_utc(outcome.source_as_of_utc))
        return None


class ObservationSink(Protocol):
    """Where attempt rows go. Every attempt, without exception.

    An implementation must persist the row DURABLY before returning, and must **raise**
    if it cannot. A sink that buffers and loses attempts on a crash defeats the one
    property this whole component rests on, and a sink that swallows its own write
    failure converts "we did not record it" into "it did not happen".
    """

    def record(self, attempt: "AttemptRecord") -> None:
        """Persist one attempt row. Raise on failure; never swallow."""


class ReadingLedger(Protocol):
    """Where a source period is claimed exactly once.

    Mirrors ``INSERT ... ON CONFLICT DO NOTHING`` against a ``UNIQUE (source_id,
    source_as_of_utc)``: the return value is whether THIS call was the one that claimed
    the key, so a caller can tell a first reading from a re-fetch without a prior
    ``SELECT`` and without a race between the two.
    """

    def admit_if_absent(self, key: "ReadingKey") -> bool:
        """``True`` if this call claimed ``key``; ``False`` if it was already claimed.

        Must never raise merely because the key is present — that is the ordinary case
        on a retry, not an error. Raise only if the claim could not be attempted.
        """
