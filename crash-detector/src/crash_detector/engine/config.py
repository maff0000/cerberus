"""The run-level configuration snapshot (BLUEPRINT §7, Standards Baseline §10).

"Configuration that affects a result belongs in a run-level snapshot, so the result can be
explained later." Every ``dial.history`` row will reference the ``config_snapshot_id`` that
produced it. Thresholds, weights and windows are configuration, external to the logic
(``PBG-SEC-001``) — never literals in the computation.

The snapshot validates itself at construction, so an incoherent configuration is refused
before an evaluation runs rather than producing a reading nobody can explain:

  * both dials must have a spec, and only the two dials may;
  * a dial declaring required inputs must declare the model that maps them, because a
    dial with inputs and no declared mapping cannot produce an explicable number
    (doctrine §3.6);
  * the staleness window must be a positive finite number of seconds. An infinite window
    is not a lenient window, it is no window at all, and it is the cheapest way to make a
    stale reading render as current.

----

SCOPE NOTE (WO-2, increment 1 of 7). :class:`ConfigSnapshot` carries no source registry in
this increment. ``raw.source_registry`` with its ``REQUIRED | CONTRIBUTING | DISPOSABLE``
criticality, and the rule that a ``DISPOSABLE`` source may never appear in a dial's
required-input set, are deliverable A4/A5 and are owed. The A2 property that depends on
them — "with an empty source registry both dials read ``Unknown``" — is expressed here
exactly and testably as :func:`empty_config_snapshot`: zero declared inputs on either
dial. When A4 lands, the registry becomes a field on this type and the "every named input
must be registered" and "no ``DISPOSABLE`` input may be required" checks join the
constructor.

Regime-aware staleness (``window_for(regime)``, CD-AC-009) is WO-3. WO-2 carries the
declared constant window and names it as such.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Union

from crash_detector.dials.dialset import DIAL_IDS
from crash_detector.engine.model import ContributionModel

__all__ = ["DialSpec", "ConfigSnapshot", "empty_config_snapshot"]


@dataclass(frozen=True)
class DialSpec:
    """One dial's declared inputs and its contribution model."""

    dial_id: str
    required_input_ids: tuple[str, ...]
    contributing_input_ids: tuple[str, ...]
    contribution_model: Union[ContributionModel, None]

    def __post_init__(self) -> None:
        if self.dial_id not in DIAL_IDS:
            raise ValueError(
                f"unknown dial_id {self.dial_id!r}; the dials are {DIAL_IDS}. "
                "A third dial is a PID amendment, not a configuration edit."
            )
        object.__setattr__(self, "required_input_ids", tuple(self.required_input_ids))
        object.__setattr__(
            self, "contributing_input_ids", tuple(self.contributing_input_ids)
        )
        for field_name in ("required_input_ids", "contributing_input_ids"):
            ids = getattr(self, field_name)
            if any(not isinstance(source_id, str) or not source_id for source_id in ids):
                raise ValueError(f"DialSpec.{field_name} must be non-empty strings")
            if len(set(ids)) != len(ids):
                raise ValueError(f"DialSpec.{field_name} contains duplicates")
        overlap = set(self.required_input_ids) & set(self.contributing_input_ids)
        if overlap:
            raise ValueError(
                f"sources declared both required and contributing for {self.dial_id}: "
                f"{sorted(overlap)}"
            )
        if self.required_input_ids and self.contribution_model is None:
            raise ValueError(
                f"dial {self.dial_id!r} declares required inputs but no contribution "
                "model; a dial with inputs and no declared mapping cannot produce an "
                "explicable number (doctrine §3.6)"
            )


@dataclass(frozen=True)
class ConfigSnapshot:
    """Everything outside the observations that affects an evaluation."""

    config_snapshot_id: str
    dial_specs: tuple[DialSpec, ...]
    staleness_window_seconds: float

    def __post_init__(self) -> None:
        if not self.config_snapshot_id:
            raise ValueError("ConfigSnapshot requires a config_snapshot_id")
        object.__setattr__(self, "dial_specs", tuple(self.dial_specs))

        if any(not isinstance(spec, DialSpec) for spec in self.dial_specs):
            raise TypeError("ConfigSnapshot.dial_specs must all be DialSpec")
        declared = [spec.dial_id for spec in self.dial_specs]
        if sorted(declared) != sorted(DIAL_IDS):
            raise ValueError(
                f"ConfigSnapshot must carry exactly one spec per dial {DIAL_IDS}, got "
                f"{declared}"
            )

        window = self.staleness_window_seconds
        if isinstance(window, bool) or not isinstance(window, float):
            raise TypeError(
                "ConfigSnapshot.staleness_window_seconds must be a float, got "
                f"{type(window).__name__}"
            )
        if not math.isfinite(window) or window <= 0.0:
            raise ValueError(
                "staleness_window_seconds must be a positive finite number of seconds; "
                "an unbounded staleness window is no staleness window"
            )

    def spec_for(self, dial_id: str) -> DialSpec:
        """The spec for ``dial_id``. Raises rather than returning a default spec."""
        for spec in self.dial_specs:
            if spec.dial_id == dial_id:
                return spec
        raise KeyError(f"no spec for dial {dial_id!r}")


def empty_config_snapshot(
    config_snapshot_id: str, *, staleness_window_seconds: float
) -> ConfigSnapshot:
    """The WO-2 configuration: both dials declared, zero inputs, no model.

    This is the shipped state while CD-D-005 is owed (BLUEPRINT §16). Evaluating against
    it yields ``Unknown`` for both dials, which is the honest answer and not a
    placeholder.
    """
    return ConfigSnapshot(
        config_snapshot_id=config_snapshot_id,
        dial_specs=tuple(
            DialSpec(
                dial_id=dial_id,
                required_input_ids=(),
                contributing_input_ids=(),
                contribution_model=None,
            )
            for dial_id in DIAL_IDS
        ),
        staleness_window_seconds=staleness_window_seconds,
    )
