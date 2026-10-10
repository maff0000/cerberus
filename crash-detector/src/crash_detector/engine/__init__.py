"""The dial engine (BLUEPRINT §7).

**Nothing in this package, and nothing reachable from it, imports
:mod:`crash_detector.witness`.** That is CD-AC-003 held in the import graph. It is held a
second, independent time in the store, where ``cd_engine`` has no privilege of any kind on
schema ``witness`` — not even ``USAGE``. Either alone would be a single point of failure
for the product's most consequential separation.

This package and :mod:`crash_detector.dials` are "the dial path" that the Required Test
Register's AST check scans (CD-RT-001-AST-NO-NUMERIC-DEFAULT, deliverable B1).

**``ContributionModel`` AND ``CONTRIBUTION_MODELS`` ARE DELETED AND ARE NOT RE-EXPORTED**
(BP-AMENDMENT-0001 §C, in force). There is no deprecation shim and no alias: a name that
still resolved would be a door still standing. Models are DATA now — see
:mod:`crash_detector.engine.model` for the types and
:mod:`crash_detector.engine.mapping` for the one engine-owned executor.
"""

from crash_detector.engine.config import ConfigSnapshot, DialSpec, empty_config_snapshot
from crash_detector.engine.evaluate import (
    DIAL_SCORE_TYPES,
    REASON_CONTRIBUTING_INPUTS_UNAVAILABLE,
    REASON_NO_MODEL_DECLARED,
    REASON_NO_REQUIRED_INPUTS,
    REASON_REQUIRED_INPUTS_UNAVAILABLE,
    evaluate,
)
from crash_detector.engine.mapping import UnspecifiedMapping, compute
from crash_detector.engine.model import (
    EMPTY_MODEL_REGISTRY,
    DeclaredParameter,
    MappingKind,
    ModelBoundToAnotherDial,
    ModelId,
    ModelNotRegistered,
    ModelProvenance,
    ModelReadsUndeclaredInput,
    ModelRegistry,
    ModelSpec,
    ScoreComputation,
)

__all__ = [
    "ConfigSnapshot",
    "DIAL_SCORE_TYPES",
    "DeclaredParameter",
    "DialSpec",
    "EMPTY_MODEL_REGISTRY",
    "MappingKind",
    "ModelBoundToAnotherDial",
    "ModelId",
    "ModelNotRegistered",
    "ModelProvenance",
    "ModelReadsUndeclaredInput",
    "ModelRegistry",
    "ModelSpec",
    "REASON_CONTRIBUTING_INPUTS_UNAVAILABLE",
    "REASON_NO_MODEL_DECLARED",
    "REASON_NO_REQUIRED_INPUTS",
    "REASON_REQUIRED_INPUTS_UNAVAILABLE",
    "ScoreComputation",
    "UnspecifiedMapping",
    "compute",
    "empty_config_snapshot",
    "evaluate",
]
