"""Collector framework — fetch and record, never compute (BLUEPRINT §5, deliverable A4).

WO-2 delivers the framework, the adapter protocol, the boundary validator, the attempt
record and the runner. It delivers **no adapter for any real source**: the ingredient set
is CD-D-005, ruled by the Product Owner as theirs and owed before WO-3. The only
implementation of :class:`~crash_detector.collectors.adapter.SourceAdapter` anywhere in
this tree is an in-memory test double in ``tests/collector_fakes.py``, named as one.

**Nothing here computes a dial value.** This package imports neither
:mod:`crash_detector.dials` nor :mod:`crash_detector.engine`, and neither will it: the
boundary between "what we observed" and "what we concluded" is the boundary between the
``raw`` and ``dial`` schemas and between two containers, and an import edge across it
would be that boundary quietly ceasing to exist in the one place nobody looks.

**Nothing here opens a socket.** No module in this package imports ``socket``, ``ssl``,
``http``, ``urllib`` or any HTTP client. Tests assert both of these properties over the
whole package rather than over the modules somebody remembered.

The shared vocabulary lives one level up, at the package root, because it is a contract
BETWEEN this layer and the engine rather than a component of either (CD-D-008):

* :mod:`crash_detector.observations` — the four-way fetch outcome and the observation row
* :mod:`crash_detector.source_registry` — the registry, its criticality and its contract
"""

from crash_detector.collectors.adapter import (
    ADAPTER_PROTOCOL_MEMBERS,
    AdapterFetchError,
    FetchedResponse,
    SourceAdapter,
    missing_adapter_members,
)
from crash_detector.collectors.attempt import (
    AttemptRecord,
    ObservationSink,
    ReadingKey,
    ReadingLedger,
)
from crash_detector.collectors.runner import (
    MAX_ATTEMPTS_CEILING,
    MAX_BACKOFF_SECONDS_CEILING,
    MAX_TIMEOUT_SECONDS_CEILING,
    CollectionResult,
    RetryPolicy,
    collect,
)
from crash_detector.collectors.validation import (
    JsonSchemaValidator,
    PayloadValidator,
    SchemaDeclarationInvalid,
    SchemaRejection,
    VALIDATION_FAILURES,
)

__all__ = [
    "ADAPTER_PROTOCOL_MEMBERS",
    "AdapterFetchError",
    "AttemptRecord",
    "CollectionResult",
    "FetchedResponse",
    "JsonSchemaValidator",
    "MAX_ATTEMPTS_CEILING",
    "MAX_BACKOFF_SECONDS_CEILING",
    "MAX_TIMEOUT_SECONDS_CEILING",
    "ObservationSink",
    "PayloadValidator",
    "ReadingKey",
    "ReadingLedger",
    "RetryPolicy",
    "SchemaDeclarationInvalid",
    "SchemaRejection",
    "SourceAdapter",
    "VALIDATION_FAILURES",
    "collect",
    "missing_adapter_members",
]
