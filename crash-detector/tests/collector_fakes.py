"""TEST DOUBLES for the collector framework. Not application code.

Everything in this module is a fake. It lives under ``tests/`` and never under ``src/``
because WO-2 delivers **no adapter for any real source**: the ingredient set is CD-D-005,
owed by the Product Owner before WO-3, and an adapter in the application tree would be an
ingredient registered by an Engineer seat, which is inventing product meaning
(``PBG-AUTH-005``).

:class:`FakeInMemoryAdapter` performs no I/O of any kind. It returns what it was
constructed to return, from memory, in order. It opens no socket, resolves no name and
reads no file, and there is a test asserting that no module under ``src/`` does either.

The sink and the ledger are in-memory stand-ins for ``raw.observation`` and the reading
uniqueness constraint that deliverable A5 will build in SQL. They implement the same
contract deliberately: if the property holds against these and not against the real store,
the difference is in the SQL and the SQL is where to look.
"""

from __future__ import annotations

from collections.abc import Mapping as AbcMapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Iterable, Mapping, Union

from crash_detector.collectors.adapter import AdapterFetchError, FetchedResponse
from crash_detector.collectors.attempt import AttemptRecord, ReadingKey

#: A schema a conforming fake response satisfies. Closed, like every schema in this
#: project, so a fake that drifts is caught rather than tolerated.
FAKE_RESPONSE_SCHEMA: Mapping[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["reading"],
    "properties": {"reading": {"type": "number"}},
}


class FakeInMemoryAdapter:
    """TEST DOUBLE. Replays a scripted sequence of outcomes, from memory.

    ``script`` is a sequence of items, one per attempt:

    * a :class:`~crash_detector.collectors.adapter.FetchedResponse` — returned as-is;
    * an ``Exception`` instance — raised;
    * anything else — returned as-is, so the runner's "the adapter broke its contract"
      path can be reached with, for example, a bare ``dict``.

    Running past the end of the script raises, loudly. A fake that quietly repeats its
    last item would make a test asserting "three attempts" pass against a runner that made
    thirty.
    """

    def __init__(
        self,
        *,
        script: Iterable[object],
        source_id: str = "fake.source",
        adapter_id: str = "fake.adapter.v0",
        response_schema: Union[Mapping[str, Any], None] = None,
        is_empty_fn: Union[Callable[[object], bool], None] = None,
    ) -> None:
        self._script = list(script)
        self._source_id = source_id
        self._adapter_id = adapter_id
        self._response_schema = (
            FAKE_RESPONSE_SCHEMA if response_schema is None else response_schema
        )
        self._is_empty_fn = is_empty_fn
        #: Every ``timeout_seconds`` the runner passed, in order. A test reads this to
        #: prove the bound actually reached the adapter rather than merely existing.
        self.timeouts_seen: list[float] = []
        self.calls = 0

    @property
    def source_id(self) -> str:
        return self._source_id

    @property
    def adapter_id(self) -> str:
        return self._adapter_id

    @property
    def response_schema(self) -> Mapping[str, Any]:
        return self._response_schema

    def fetch(self, *, timeout_seconds: float) -> FetchedResponse:
        self.timeouts_seen.append(timeout_seconds)
        if self.calls >= len(self._script):
            raise AssertionError(
                f"FakeInMemoryAdapter script exhausted after {self.calls} calls; the "
                "runner attempted more times than the test scripted"
            )
        item = self._script[self.calls]
        self.calls += 1
        if isinstance(item, BaseException):
            raise item
        return item  # type: ignore[return-value]

    def is_empty(self, payload: object) -> bool:
        if self._is_empty_fn is not None:
            return self._is_empty_fn(payload)
        if isinstance(payload, AbcMapping):
            return "reading" not in payload
        return False


@dataclass
class RecordingSink:
    """TEST DOUBLE for ``raw.observation``. Append-only, in memory.

    Append-only on purpose: the real table carries no ``UPDATE`` or ``DELETE`` grant for
    any role (BLUEPRINT §4), and a fake that allowed either would let a test pass against
    behaviour the store would refuse.
    """

    recorded: list[AttemptRecord] = field(default_factory=list)

    def record(self, attempt: AttemptRecord) -> None:
        self.recorded.append(attempt)

    @property
    def outcome_classes(self) -> tuple[str, ...]:
        return tuple(attempt.outcome_class for attempt in self.recorded)

    @property
    def attempt_numbers(self) -> tuple[int, ...]:
        return tuple(attempt.attempt_number for attempt in self.recorded)


@dataclass
class ExplodingSink:
    """TEST DOUBLE. A sink that cannot write, and says so instead of pretending."""

    def record(self, attempt: AttemptRecord) -> None:
        raise OSError("the store is unreachable")


@dataclass
class RecordingLedger:
    """TEST DOUBLE for ``UNIQUE (source_id, source_as_of_utc)``.

    Mirrors ``INSERT ... ON CONFLICT DO NOTHING``: the return value says whether THIS
    call claimed the key.
    """

    admitted: list[ReadingKey] = field(default_factory=list)
    rejected: list[ReadingKey] = field(default_factory=list)

    def admit_if_absent(self, key: ReadingKey) -> bool:
        if key in self.admitted:
            self.rejected.append(key)
            return False
        self.admitted.append(key)
        return True


class SteppingClock:
    """TEST DOUBLE. A monotonic clock that advances a fixed step per call.

    The runner takes its clock as an argument precisely so that no wall clock is consulted
    anywhere in the collector path. ``advance_by`` is set per test to make an attempt
    appear to have taken however long the test needs it to have taken — including longer
    than its timeout budget.
    """

    def __init__(self, start: datetime, *, advance_seconds: float = 0.0) -> None:
        self._now = start
        self._advance = timedelta(seconds=advance_seconds)
        self.calls = 0

    def __call__(self) -> datetime:
        self.calls += 1
        current = self._now
        self._now = self._now + self._advance
        return current


class RecordingSleep:
    """TEST DOUBLE. Records what it was asked to wait for, and waits for nothing."""

    def __init__(self) -> None:
        self.slept: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.slept.append(seconds)


def failing_fetch(error_class: str = "CONNECTION_REFUSED") -> AdapterFetchError:
    """A scripted transport failure the adapter classifies itself."""
    return AdapterFetchError(error_class)
