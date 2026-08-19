"""The dial engine (BLUEPRINT §7).

**Nothing in this package, and nothing reachable from it, imports
:mod:`crash_detector.witness`.** That is CD-AC-003 held in the import graph. It is held a
second, independent time in the store, where ``cd_engine`` has no privilege of any kind on
schema ``witness`` — not even ``USAGE``. Either alone would be a single point of failure
for the product's most consequential separation.

This package and :mod:`crash_detector.dials` are "the dial path" that the Required Test
Register's AST check scans (CD-RT-001-AST-NO-NUMERIC-DEFAULT, deliverable B1).
"""

from crash_detector.engine.config import ConfigSnapshot, DialSpec, empty_config_snapshot
from crash_detector.engine.evaluate import (
    DIAL_SCORE_TYPES,
    REASON_CONTRIBUTING_INPUTS_UNAVAILABLE,
    REASON_NO_CONTRIBUTION_MODEL,
    REASON_NO_REQUIRED_INPUTS,
    REASON_REQUIRED_INPUTS_UNAVAILABLE,
    evaluate,
)
from crash_detector.engine.model import (
    CONTRIBUTION_MODELS,
    ContributionModel,
    ScoreComputation,
)

__all__ = [
    "CONTRIBUTION_MODELS",
    "ConfigSnapshot",
    "ContributionModel",
    "DIAL_SCORE_TYPES",
    "DialSpec",
    "REASON_CONTRIBUTING_INPUTS_UNAVAILABLE",
    "REASON_NO_CONTRIBUTION_MODEL",
    "REASON_NO_REQUIRED_INPUTS",
    "REASON_REQUIRED_INPUTS_UNAVAILABLE",
    "ScoreComputation",
    "empty_config_snapshot",
    "evaluate",
]
