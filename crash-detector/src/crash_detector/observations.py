"""The observation record and its fetch outcome — the collector/engine contract.

BLUEPRINT §5. **Every fetch attempt produces a record, including the failures**, and the
outcome of a fetch is a sum type with four constructors:

    outcome := OK(payload, source_as_of_utc)
             | FetchFailed(error_class, http_status?)   # we could not ask
             | Malformed(schema_error_class)            # we asked, the answer did not conform
             | Empty(source_as_of_utc?)                 # we asked, the source has nothing

A failed fetch that records nothing is indistinguishable from a fetch that was never
scheduled, and both are indistinguishable from a source that had nothing to report —
three states that demand different responses, collapsed into one absence. Standards
Baseline §8: *cannot determine* is not *determined to be absent*.

The engine reads outcomes, not values, and **the only outcome that can produce a dial
contribution is** :class:`OK`. The other three produce ``Unknown`` or ``Degraded`` — never
zero, never the previous value, never a default (BLUEPRINT §7).

----

SCOPE NOTE, disclosed rather than quietly taken (WO-2, increment 1 of 7).

This module exists in increment 1 because deliverable A2's own signature —
``evaluate(observations, config_snapshot, now_utc)`` — cannot be typed without it, and
because "only ``OK`` contributes" is an A2 property that has to be testable now. It is
therefore the minimum of the observation contract, and no more:

  * DELIVERED HERE: the four-constructor outcome sum type, and the observation record.
  * NOT DELIVERED HERE, and owed to deliverable A4: the adapter protocol, boundary schema
    validation, the collector runner and its bounded timeouts and retries, idempotency on
    ``(source_id, source_as_of_utc)``, the source registry with its
    ``REQUIRED | CONTRIBUTING | DISPOSABLE`` criticality, the persistence path that makes
    "every attempt writes a row" true of the store rather than only of the type, and the
    in-memory fake adapter used by tests.

It lives at the package root rather than under ``collectors/`` on purpose. It is the
*contract between* the collector layer and the engine, not a component of either, and
putting it under ``collectors/`` would make :mod:`crash_detector.engine` import the
collector package — an import-graph edge that CD-AC-003's checks should not have to
reason about.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Union

from crash_detector.time_utc import ensure_utc

__all__ = [
    "OK",
    "FetchFailed",
    "Malformed",
    "Empty",
    "FetchOutcome",
    "ObservationRecord",
    "OUTCOME_CLASSES",
    "outcome_class",
]


@dataclass(frozen=True)
class OK:
    """We asked, the source answered, and the answer conformed to its declared schema.

    The only outcome that can produce a dial contribution.

    ``payload`` is the validated response. ``source_as_of_utc`` is the instant the SOURCE
    says its data is for — not the instant we fetched it. Freshness is a property of the
    data, not of our diligence in asking for it.
    """

    payload: Mapping[str, object]
    source_as_of_utc: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(self.payload))
        object.__setattr__(self, "source_as_of_utc", ensure_utc(self.source_as_of_utc))


@dataclass(frozen=True)
class FetchFailed:
    """We could not ask. Network, timeout, transport, refusal, non-2xx.

    Carries no payload and no ``source_as_of_utc``, because there is no observation here
    — only a record that we tried.
    """

    error_class: str
    http_status: Union[int, None] = None

    def __post_init__(self) -> None:
        if not self.error_class:
            raise ValueError("FetchFailed requires a stated error_class")
        status = self.http_status
        if status is not None and (isinstance(status, bool) or not isinstance(status, int)):
            raise TypeError("FetchFailed.http_status must be an int or absent")


@dataclass(frozen=True)
class Malformed:
    """We asked, and the answer did not conform to the schema the adapter declares.

    Stored with its error class and **never coerced** (Standards Baseline §4). External
    input is hostile, including from a source that has been reliable for a year.
    """

    schema_error_class: str

    def __post_init__(self) -> None:
        if not self.schema_error_class:
            raise ValueError("Malformed requires a stated schema_error_class")


@dataclass(frozen=True)
class Empty:
    """We asked, the source conformed, and it has nothing to report for the period.

    Distinct from :class:`FetchFailed`: this is *determined to be absent*, which is a
    different fact from *cannot determine*, and it is not a value either.

    Nullary on purpose. It carries no ``source_as_of_utc``, because there is no
    observation to be as-of; the attempt's own time is on the
    :class:`ObservationRecord`. An optional timestamp here would be a field that is
    sometimes present, and "sometimes present" is where a reader learns to guess.
    """


#: The fetch outcome sum type. Closed: an unrecognised member is a defect, not a case to
#: be defaulted. There is deliberately no common base class — a base class is somewhere a
#: ``.value`` or ``.payload`` accessor could later be added that all four constructors
#: would inherit, which is exactly the route from a failure to a number that this type
#: exists to close.
FetchOutcome = Union[OK, FetchFailed, Malformed, Empty]

#: The persisted discriminator values for ``raw.observation.outcome``.
OUTCOME_CLASSES: tuple[str, ...] = ("OK", "FETCH_FAILED", "MALFORMED", "EMPTY")

_CLASS_BY_TYPE = {
    OK: "OK",
    FetchFailed: "FETCH_FAILED",
    Malformed: "MALFORMED",
    Empty: "EMPTY",
}


def outcome_class(outcome: "FetchOutcome") -> str:
    """The persisted discriminator for an outcome value.

    An unrecognised member raises. It is not defaulted, and in particular it is never
    defaulted to ``OK``.
    """
    try:
        return _CLASS_BY_TYPE[type(outcome)]
    except KeyError:
        raise TypeError(
            f"not a FetchOutcome: {type(outcome).__name__}. The sum type is closed; "
            "there is no fall-through, least of all to OK."
        ) from None


@dataclass(frozen=True)
class ObservationRecord:
    """One row of ``raw.observation`` — one fetch attempt, whatever came of it.

    ``observed_utc`` is when WE performed the attempt; the source's own timestamp, where
    one exists, lives on the outcome. Keeping the two apart is what stops "we asked
    recently" from being mistaken for "the data is recent".
    """

    source_id: str
    observed_utc: datetime
    outcome: "FetchOutcome"

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("ObservationRecord requires a source_id")
        object.__setattr__(self, "observed_utc", ensure_utc(self.observed_utc))
        # Validates membership of the closed sum type, and raises if it is not a member.
        outcome_class(self.outcome)
