"""Dial types — part of "the dial path" (BLUEPRINT §7).

This package and :mod:`crash_detector.engine` together are the **dial path** that the
Required Test Register's AST check (CD-RT-001-AST-NO-NUMERIC-DEFAULT, deliverable B1)
scans. Nothing here may introduce a numeric default, an ``Optional[float]``, a
``float | None`` annotation, an ``or 0`` fallback, a ``.get(key, <number>)`` or a bare
``except`` returning a number.
"""

from crash_detector.dials.dialset import (
    DIAL_FIELDS,
    DIAL_IDS,
    EQUITY_DIAL_ID,
    MONETARY_DIAL_ID,
    DialSet,
)
from crash_detector.dials.reading import (
    READING_CONSTRUCTORS,
    Degraded,
    Reading,
    Unknown,
    Value,
    fold,
    is_value,
)
from crash_detector.dials.scores import (
    ARITHMETIC_DUNDERS,
    SCORE_TYPES,
    Contribution,
    EquityCrashScore,
    MonetaryDebasementScore,
    ScoreOutOfRange,
)

__all__ = [
    "ARITHMETIC_DUNDERS",
    "Contribution",
    "DIAL_FIELDS",
    "DIAL_IDS",
    "Degraded",
    "DialSet",
    "EQUITY_DIAL_ID",
    "EquityCrashScore",
    "MONETARY_DIAL_ID",
    "MonetaryDebasementScore",
    "READING_CONSTRUCTORS",
    "Reading",
    "SCORE_TYPES",
    "ScoreOutOfRange",
    "Unknown",
    "Value",
    "fold",
    "is_value",
]
