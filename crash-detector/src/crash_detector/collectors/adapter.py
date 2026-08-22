"""The source adapter protocol — fetch and record, never compute (BLUEPRINT §5).

    A collector fetches and records. It never computes.

The boundary between "what we observed" and "what we concluded" is the boundary between
the ``raw`` schema and the ``dial`` schema, and between two containers. No collector holds
a grant that would let it write a conclusion (deliverable A5's grant matrix), so the rule
below is a permission as well as an instruction.

An adapter supplies five things and nothing else:

* ``source_id`` — its row in ``raw.source_registry``
* ``adapter_id`` — a stable identity for this implementation, recorded on every attempt
* ``response_schema`` — the JSON Schema it accepts, **declared up front**. Validation
  happens once, at the boundary, against this schema (Standards Baseline §4).
* ``fetch`` — ONE bounded attempt. Raises on failure; the runner classifies and records.
* ``is_empty`` — whether a conforming response carried anything. That is a fact about the
  response's shape, not a judgement about what the market is doing.

There is deliberately no ``parse``, no ``normalise``, no ``score`` and no ``value``. An
adapter that transformed its response would be computing, and the transformation would
happen on the wrong side of the raw/dial boundary where nothing can audit it.

**NO ADAPTER FOR ANY REAL SOURCE EXISTS IN WO-2.** The framework and the registry types
are the deliverable; the ingredient set is CD-D-005 and is the Product Owner's
(BLUEPRINT §16). The only implementation of this protocol anywhere in this tree is an
in-memory test double under ``tests/collector_fakes.py``, named as one. Nothing in this
package opens a socket, and a test asserts that no module in it imports one.

----

WHY NO FREE-TEXT DETAIL TRAVELS WITH A FAILURE.

:exc:`AdapterFetchError` carries a stable ``error_class`` and an optional HTTP status, and
carries **no message, no URL and no exception text**. That is a secret-hygiene decision,
not an oversight (``PBG-SEC-002``, Standards Baseline §5): a transport failure's natural
detail string is the request that failed, and the request that failed is the one carrying
the source's credential in a header or a query string. A stable classification can be
counted and compared across time, which is what an operator actually needs; a raw message
is a value-bearing string on a path that ends in a governed record.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Protocol, Union

from crash_detector.admission import ESTABLISHED_HERE, admits
from crash_detector.time_utc import ensure_utc

__all__ = [
    "AdapterFetchError",
    "FetchedResponse",
    "SourceAdapter",
    "ADAPTER_PROTOCOL_MEMBERS",
    "missing_adapter_members",
]


class AdapterFetchError(Exception):
    """An adapter could not complete a fetch.

    ``error_class`` is a stable classification the adapter chooses — ``TIMEOUT``,
    ``CONNECTION_REFUSED``, ``HTTP_ERROR``, ``TLS_FAILURE`` — never a raw message.

    ``http_status`` is absent where the failure happened before any HTTP status existed.
    That is an honest absence, and it is not a zero: a zero status would sort, compare and
    aggregate alongside real statuses.
    """

    def __init__(self, error_class: str, http_status: Union[int, None] = None) -> None:
        if not isinstance(error_class, str) or not error_class:
            raise ValueError("AdapterFetchError requires a non-empty error_class")
        if http_status is not None and (
            isinstance(http_status, bool) or not isinstance(http_status, int)
        ):
            raise TypeError("AdapterFetchError.http_status must be an int or absent")
        super().__init__(error_class)
        self.error_class = error_class
        self.http_status = http_status


@dataclass(frozen=True)
class FetchedResponse:
    """One completed fetch, **before** validation.

    ``source_as_of_utc`` is the instant the SOURCE says its data refers to — never the
    instant we fetched it. Confusing the two is how "we asked recently" becomes "the data
    is recent", which is the stale-reads-as-calm failure with an extra step.

    ``payload`` is typed ``object`` on purpose: at this point it is unvalidated external
    input and claiming a shape for it here would be claiming the very thing the boundary
    validation is about to establish. The runner narrows it after validation.
    """

    payload: object
    source_as_of_utc: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_as_of_utc", ensure_utc(self.source_as_of_utc))


class SourceAdapter(Protocol):
    """What every ingredient source adapter must provide."""

    @property
    def source_id(self) -> str:
        """The ``raw.source_registry`` identifier this adapter fetches for."""

    @property
    def adapter_id(self) -> str:
        """A stable identifier for this adapter implementation."""

    @property
    def response_schema(self) -> Mapping[str, Any]:
        """The JSON Schema a response must conform to. Declared, never inferred.

        Inferring a schema from a response that arrived is not validation: it accepts
        whatever came, which is exactly what the boundary exists to stop.

        The schema must be entirely self-contained. A ``$ref`` to anything other than a
        local ``#`` fragment is refused by the validator, because resolving a remote
        reference is a network fetch performed inside a validation step.
        """

    def fetch(self, *, timeout_seconds: float) -> FetchedResponse:
        """Perform ONE bounded attempt.

        Must honour ``timeout_seconds`` — an unbounded wait is an outage with extra steps
        (Standards Baseline §11). The runner independently measures the elapsed time and
        refuses a response that arrived after the budget, so an adapter that ignores its
        timeout cannot deliver a value; it can only produce a recorded failure.

        Raise :exc:`AdapterFetchError` to state the failure class yourself, or any other
        exception to have it classified by type name. The attempt is recorded either way.
        """

    def is_empty(self, payload: object) -> bool:
        """Whether a schema-conforming payload carried nothing to report.

        A fact about the response's shape. Not a judgement about what it means, and not
        a place to decide that a value is too small to matter.
        """


#: The complete member set of :class:`SourceAdapter`. Enumerated as data so a guard can
#: check conformance against the whole protocol rather than the one member somebody
#: remembered. ``typing.runtime_checkable`` is deliberately not used: on this interpreter
#: it checks only for the presence of members, so it would pass an object whose ``fetch``
#: is an integer.
ADAPTER_PROTOCOL_MEMBERS: tuple[str, ...] = (
    "source_id",
    "adapter_id",
    "response_schema",
    "fetch",
    "is_empty",
)

#: Members that must be callable. The rest are values.
_ADAPTER_CALLABLES: frozenset[str] = frozenset({"fetch", "is_empty"})


@admits(
    candidate=ESTABLISHED_HERE(
        "THIS CALLABLE IS THE ESTABLISHMENT DOOR. Its entire contract is to accept ANY "
        "object and report which SourceAdapter members it fails to supply, so exact-typing "
        "its argument would make it unable to answer the only question it exists to answer. "
        "CARRIER MEASURED: it establishes the argument itself, member by member, over the "
        "whole of ADAPTER_PROTOCOL_MEMBERS — "
        "tests/test_collector_boundaries.py::test_conformance_is_checked_against_every_member_not_the_ones_remembered "
        "and ::test_a_member_that_exists_but_is_not_callable_does_not_count_as_conformance. "
        "WHAT IT CANNOT ESTABLISH is that a conforming object BEHAVES as the protocol says: "
        "that is CD-BP-003 and it is NOT PROVED TO BE CARRIED ANYWHERE."
    )
)
def missing_adapter_members(candidate: object) -> tuple[str, ...]:
    """Which :class:`SourceAdapter` members ``candidate`` fails to supply.

    Empty means structurally conformant. Reported as a tuple rather than a bool so a
    failure names what is missing; a bare ``False`` sends the reader back to the protocol
    to guess.

    **THIS IS A VOCABULARY CHECK AND IT DOES NOT SURVIVE A RENAME.** It asks ``hasattr``
    for five SPELLED names. Rename ``fetch`` on both sides — the Protocol and the object —
    and this function reports a conformance that means something different from what it
    meant before. That is unavoidable at a boundary to a foreign system: structural
    conformance IS nominal. It is recorded here rather than left for an auditor to
    discover, and it is the reason CD-BP-003 exists as a declared limit rather than as a
    closure.
    """
    missing: list[str] = []
    for member in ADAPTER_PROTOCOL_MEMBERS:
        if not hasattr(candidate, member):
            missing.append(member)
            continue
        if member in _ADAPTER_CALLABLES and not callable(getattr(candidate, member)):
            missing.append(member)
    return tuple(missing)
