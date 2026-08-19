"""Contribution models — the mapping from inputs to a dial magnitude.

**WO-2 registers none, deliberately.**

PID doctrine §3.6: "No unexplained mappings. We do not copy a score-to-probability curve
we cannot account for." Which inputs feed a dial, what each stands for, and how they weigh
is CD-D-005 — ruled by the Product Owner as theirs and owed before WO-3 (BLUEPRINT §16,
governance/decisions/PO-ACCEPT-BLUEPRINT-0001.md). An Engineer seat inventing one would be
inventing product meaning (``PBG-AUTH-005``).

So this module ships the *shape* of a model and an empty registry. The consequence is
exact and intended: with no sources registered and no model declared, both dials read
``Unknown`` — the doctrinally correct empty state, and the thing that makes CD-AC-001's
first plant demonstrable.

The model is injected into a :class:`~crash_detector.engine.config.DialSpec` rather than
looked up inside :func:`~crash_detector.engine.evaluate.evaluate`, which is what keeps
``evaluate`` a pure function of its arguments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from crash_detector.dials.scores import Contribution

__all__ = ["ScoreComputation", "ContributionModel", "CONTRIBUTION_MODELS"]


@dataclass(frozen=True)
class ScoreComputation:
    """A magnitude and the named contributions that produced it.

    The contributions are not decoration: BLUEPRINT §7 requires that every reading be
    explicable from its stored inputs a year later, without archaeology.
    """

    magnitude: float
    contributions: tuple[Contribution, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "contributions", tuple(self.contributions))


class ContributionModel(Protocol):
    """Maps schema-validated ``OK`` payloads to one dial's magnitude."""

    @property
    def model_id(self) -> str:
        """A stable identifier, recorded on every ``dial.history`` row."""

    def compute(self, payloads: Mapping[str, Mapping[str, object]]) -> ScoreComputation:
        """Compute the magnitude from payloads keyed by ``source_id``.

        Contract: **pure**. No I/O, no clock, no configuration read from the environment.
        ``evaluate`` is a pure function of its arguments, and a model that reaches outside
        itself would make that claim false without changing ``evaluate``'s own code —
        which is why the contract is stated here where an implementer will read it.

        A model that cannot compute honestly must **raise**. It must not return a
        placeholder magnitude: there is no such thing on this dial path.
        """


#: Registered production models, keyed by ``model_id``.
#:
#: EMPTY IN WO-2, and that emptiness is the CD-D-005 hold made visible in code. Adding an
#: entry here is a product decision, not an implementation one.
CONTRIBUTION_MODELS: Mapping[str, ContributionModel] = {}
