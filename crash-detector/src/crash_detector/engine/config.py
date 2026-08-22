"""The run-level configuration snapshot (BLUEPRINT §7, Standards Baseline §10).

"Configuration that affects a result belongs in a run-level snapshot, so the result can be
explained later." Every ``dial.history`` row will reference the ``config_snapshot_id`` that
produced it. Thresholds, weights and windows are configuration, external to the logic
(``PBG-SEC-001``) — never literals in the computation.

The snapshot validates itself at construction, so an incoherent configuration is refused
before an evaluation runs rather than producing a reading nobody can explain:

  * both dials must have a spec, and only the two dials may;
  * a dial declaring required inputs must NAME the model that maps them, because a
    dial with inputs and no declared mapping cannot produce an explicable number
    (doctrine §3.6). It names it; it does not carry it — see below;
  * the staleness window must be ADMISSIBLE — a positive finite number of seconds that is
    also at or below :data:`~crash_detector.staleness.STALENESS_WINDOW_CEILING_SECONDS`.
    An infinite window is not a lenient window, it is no window at all, and it is the
    cheapest way to make a stale reading render as current; ``1e18`` is the same thing
    written so as not to look like it, which is CD-ASR-F06. Admission happens in exactly
    one place, :class:`~crash_detector.staleness.StalenessWindow`, shared with the serving
    resolver — two guarded comparison sites would be an enumeration, and enumerations come
    apart;
  * **every source a dial names must be registered**, and **its declared criticality must
    agree with the set it is named in** — see below.

----

THE SOURCE REGISTRY IS PART OF THE SNAPSHOT (WO-2, increment 2, deliverable A4).

Which sources exist and how critical each one is are configuration that affects a result,
so they belong in the run-level snapshot alongside the thresholds and the window
(Standards Baseline §10). A ``dial.history`` row referencing a ``config_snapshot_id`` can
then be explained a year later without archaeology — including the part of the explanation
that says which inputs were even eligible.

Two invariants join the constructor with it, and they are load-bearing together:

1. **Every source named in a dial's input sets must be registered.** Without this the
   criticality contract is vacuous: you evade the ``DISPOSABLE`` prohibition simply by not
   registering the source you are about to make load-bearing.
2. **A source's declared criticality must match the set it is named in.** That subsumes
   the dispatch's specific rule that a ``DISPOSABLE`` source may NEVER appear in a dial's
   required-input set, which raises
   :exc:`~crash_detector.source_registry.DisposableSourceIsLoadBearing` by name. The
   reasoning for enforcing the Blueprint's whole criticality table rather than that single
   row is in :mod:`crash_detector.source_registry`.

The equivalent DATABASE constraint is deliverable A5 and is owed. Both must exist: this
one refuses an incoherent configuration before an evaluation runs, and that one refuses an
incoherent row whatever wrote it.

WO-2 ships :data:`~crash_detector.source_registry.EMPTY_SOURCE_REGISTRY` — zero sources —
because CD-D-005 is owed by the Product Owner (BLUEPRINT §16). The consequence is exact
and intended: nothing is registered, so no dial may name an input, so every dial reads
``Unknown``. See :func:`empty_config_snapshot`.

The registry is a REQUIRED field with no default. A default registry would be a registry
nobody chose, and the one thing worse than an empty registry is an empty registry that
arrived by omission and is therefore not evidence of anything.

----

THE MODEL REGISTRY IS PART OF THE SNAPSHOT TOO (BP-AMENDMENT-0001 §C.5, in force).

**``DialSpec`` CARRIES A REFERENCE AND NOT AN OBJECT.** The field that held one —
``contribution_model: ContributionModel | None`` — **does not exist**. It was not emptied,
deprecated or type-narrowed: the attribute is gone, so ``DialSpec(…, contribution_model=x)``
is a ``TypeError`` from the dataclass constructor itself and ``spec.contribution_model`` is
an ``AttributeError``. In its place ``model_ref: ModelId | None`` holds a NAME, established
through :func:`~crash_detector.engine.model.own_model_id`, and an object is not a name.

That is the closure of ``ASR3-F02``, and it is a deletion rather than a check: a ``Protocol``
annotation asserts nothing at runtime, so there was never a check to strengthen — there was
a door that should not have existed. The whole reasoning is in
:mod:`crash_detector.engine.model`.

:class:`~crash_detector.engine.model.ModelRegistry` joins
:class:`~crash_detector.source_registry.SourceRegistry` on this snapshot, on the same terms
and for the same stated reason: it is configuration that affects a result, so it belongs in
the run-level snapshot (Standards Baseline §10), and it is **required with no default**,
because a registry nobody chose is not evidence of anything.

Three further invariants join the constructor with it, and the first two mirror the source
registry exactly:

1. every ``model_ref`` a dial names **must resolve** in the model registry;
2. a resolved spec's ``dial_id`` **must equal** the dial naming it — one model serves one
   dial, which is the structural answer to ``ASR3-F02``'s cross-dial mechanism;
3. a resolved spec's input ids **must be a subset of** the naming ``DialSpec``'s declared
   inputs, per set, and every one of them must be registered in the ``SourceRegistry`` with
   an agreeing criticality.

All three live in :func:`~crash_detector.engine.model.establish_model_for_dial`, which this
constructor calls and which :meth:`ConfigSnapshot.model_for` calls again at every
resolution. **One function, two call sites** — two independently written checks would be an
enumeration, and enumerations come apart.

WO-2 ships :data:`~crash_detector.engine.model.EMPTY_MODEL_REGISTRY` — zero rows — beside
the empty source registry, because CD-D-005 is owed. With no model registered no dial may
name one; with no source registered no dial may declare an input; both dials read
``Unknown``.

Regime-aware staleness (``window_for(regime)``, CD-AC-009) is WO-3. WO-2 carries the
declared constant window and names it as such.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from crash_detector.own_terms import NotEstablishedOnOwnTerms, own_str
from crash_detector.dials.dialset import DIAL_IDS
from crash_detector.engine.model import (
    EMPTY_MODEL_REGISTRY,
    ModelId,
    ModelRegistry,
    ModelSpec,
    establish_model_for_dial,
    own_model_id,
)
from crash_detector.source_registry import EMPTY_SOURCE_REGISTRY, SourceRegistry
from crash_detector.staleness import StalenessWindow

__all__ = ["DialSpec", "ConfigSnapshot", "empty_config_snapshot"]


@dataclass(frozen=True)
class DialSpec:
    """One dial's declared inputs and the NAME of the model that maps them.

    **THERE IS NO FIELD HERE THAT HOLDS A MODEL OBJECT OR A CALLABLE**, and that absence is
    the whole of ``ASR3-F02``'s closure (BP-AMENDMENT-0001 §C). ``model_ref`` is a name
    resolved by the engine against
    :class:`~crash_detector.engine.model.ModelRegistry`; there is no expression a caller can
    write that places code where a dial's magnitude is computed.
    """

    dial_id: str
    required_input_ids: tuple[str, ...]
    contributing_input_ids: tuple[str, ...]
    model_ref: Union[ModelId, None]

    def __post_init__(self) -> None:
        # EVERY ID RE-ESTABLISHED BEFORE ANY OF THEM DECIDES ANYTHING (CD-AC-005, Class 2).
        # `dial_id not in DIAL_IDS` selects the dial; `source_id in usable` in the engine
        # decides whether a required input was present, which decides whether the dial is a
        # number at all; and the duplicate and overlap tests below are set membership. All
        # of those are the supplied strings' `__eq__` and `__hash__` to answer, and
        # `isinstance(source_id, str)` admitted a subclass that could answer them.
        try:
            object.__setattr__(self, "dial_id", own_str(self.dial_id))
        except NotEstablishedOnOwnTerms:
            raise ValueError(
                f"unknown dial_id {self.dial_id!r}; the dials are {DIAL_IDS}. "
                "A third dial is a PID amendment, not a configuration edit."
            ) from None
        if self.dial_id not in DIAL_IDS:
            raise ValueError(
                f"unknown dial_id {self.dial_id!r}; the dials are {DIAL_IDS}. "
                "A third dial is a PID amendment, not a configuration edit."
            )
        for field_name in ("required_input_ids", "contributing_input_ids"):
            try:
                established = tuple(
                    own_str(source_id) for source_id in getattr(self, field_name)
                )
            except NotEstablishedOnOwnTerms:
                raise ValueError(
                    f"DialSpec.{field_name} must be non-empty strings"
                ) from None
            object.__setattr__(self, field_name, established)
        for field_name in ("required_input_ids", "contributing_input_ids"):
            ids = getattr(self, field_name)
            if any(not source_id for source_id in ids):
                raise ValueError(f"DialSpec.{field_name} must be non-empty strings")
            if len(set(ids)) != len(ids):
                raise ValueError(f"DialSpec.{field_name} contains duplicates")
        overlap = set(self.required_input_ids) & set(self.contributing_input_ids)
        if overlap:
            raise ValueError(
                f"sources declared both required and contributing for {self.dial_id}: "
                f"{sorted(overlap)}"
            )
        # THE MODEL REFERENCE IS A NAME, ESTABLISHED ON THIS SYSTEM'S OWN TERMS.
        # `own_model_id` raises NotEstablishedOnOwnTerms — a TypeError — for anything that
        # is not a str, which is where the ASR3-F02 plant dies if it is adapted to this
        # field rather than to the deleted one. It is deliberately NOT caught and reworded
        # into a ValueError: the refusal names the type that was offered, and that is the
        # single most useful thing an auditor reading the failure can be told.
        if self.model_ref is not None:
            object.__setattr__(self, "model_ref", own_model_id(self.model_ref))

        if self.required_input_ids and self.model_ref is None:
            raise ValueError(
                f"dial {self.dial_id!r} declares required inputs but names no model; a "
                "dial with inputs and no declared mapping cannot produce an explicable "
                "number (doctrine §3.6)"
            )


@dataclass(frozen=True)
class ConfigSnapshot:
    """Everything outside the observations that affects an evaluation."""

    config_snapshot_id: str
    dial_specs: tuple[DialSpec, ...]
    staleness_window_seconds: float
    source_registry: SourceRegistry
    model_registry: ModelRegistry

    def __post_init__(self) -> None:
        if not self.config_snapshot_id:
            raise ValueError("ConfigSnapshot requires a config_snapshot_id")
        object.__setattr__(self, "dial_specs", tuple(self.dial_specs))

        # EXACT TYPE, not isinstance (CD-AC-005, Class 2). A DialSpec subclass may shadow
        # `required_input_ids` or `model_ref` with a property, so the values the absence
        # post-condition re-derives its answer from would be computed by the caller's code
        # at the moment it re-derived them — and a `model_ref` property could answer with a
        # different name at construction than at resolution.
        if any(type(spec) is not DialSpec for spec in self.dial_specs):
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
        # ONE ADMISSION DOOR, shared with the serving resolver (CD-ASR-F06). The snapshot
        # keeps a float field because the envelope publishes the window that was applied
        # as a number, but the value only becomes USABLE by passing through
        # StalenessWindow — and `window()` below is the only way the evaluation gets one.
        StalenessWindow(seconds=window)

        registry = self.source_registry
        # EXACT TYPE, for the reason above: a SourceRegistry subclass may redefine
        # `assert_may_be_required`, which is the criticality contract itself.
        if type(registry) is not SourceRegistry:
            raise TypeError(
                "ConfigSnapshot.source_registry must be a SourceRegistry, got "
                f"{type(registry).__name__}. Pass EMPTY_SOURCE_REGISTRY explicitly for "
                "the WO-2 state; there is no default, because a registry nobody chose "
                "is not evidence of anything."
            )
        # Both invariants, per dial. `assert_may_be_*` calls `get` first, so an
        # unregistered source raises SourceNotRegistered before any criticality is read
        # — the two checks are one pass and cannot come apart.
        for spec in self.dial_specs:
            registry.assert_may_be_required(spec.required_input_ids)
            registry.assert_may_be_contributing(spec.contributing_input_ids)

        # THE MODEL REGISTRY, AND §C.5's THREE INVARIANTS OVER IT.
        # Exact type, for the reason above and one more: a ModelRegistry subclass may
        # redefine `get`, and `get` IS the resolution — a subclass could answer with a
        # different spec than the one it holds, which is the caller choosing what a dial
        # computes without any field ever having held a model. `establish_model_for_dial`
        # refuses a non-ModelRegistry first of all, so this is that same refusal reached at
        # the earliest point rather than a second copy of it.
        for spec in self.dial_specs:
            establish_model_for_dial(
                self.model_registry,
                dial_id=spec.dial_id,
                model_ref=spec.model_ref,
                required_input_ids=spec.required_input_ids,
                contributing_input_ids=spec.contributing_input_ids,
            )
        # INVARIANT 3's second half, using the source registry's OWN criticality contract
        # rather than a second copy of it. The subset test above has already established
        # that the model names nothing the dial did not, so these ids are the dial's ids and
        # the registry has already admitted them — this asserts the model's own declaration
        # against the same contract, so a row promoting a contributing input to required is
        # refused even though the dial named both.
        for spec in self.dial_specs:
            model = self.model_for(spec.dial_id)
            if model is None:
                continue
            registry.assert_may_be_required(model.required_input_ids)
            registry.assert_may_be_contributing(model.contributing_input_ids)

    def model_for(self, dial_id: str) -> "Union[ModelSpec, None]":
        """The resolved :class:`~crash_detector.engine.model.ModelSpec` for ``dial_id``.

        ``None`` when the dial names no model, which is the WO-2 shipped state of both
        dials and is not an error.

        **THE ONE RESOLUTION DOOR.** The evaluation takes its model from HERE and never by
        indexing the registry itself, for the same reason it takes its staleness window from
        :meth:`window` and never from the raw float: the field is the record of what was
        configured, and this is the thing that may be applied. Every §C.5 invariant is
        re-asserted at this call by the same function the constructor used, so a ``dial_id``
        or an input tuple rewritten past ``frozen`` between construction and evaluation is
        refused here rather than resolved.
        """
        spec = self.spec_for(dial_id)
        return establish_model_for_dial(
            self.model_registry,
            dial_id=spec.dial_id,
            model_ref=spec.model_ref,
            required_input_ids=spec.required_input_ids,
            contributing_input_ids=spec.contributing_input_ids,
        )

    def window(self) -> StalenessWindow:
        """The admitted staleness window for this snapshot.

        The evaluation takes its window from HERE and never from the raw float, so the
        ceiling cannot be evaded by reading the field directly: the field is the record of
        what was configured, and this is the thing that may be applied.
        """
        return StalenessWindow(seconds=self.staleness_window_seconds)

    def spec_for(self, dial_id: str) -> DialSpec:
        """The spec for ``dial_id``. Raises rather than returning a default spec."""
        for spec in self.dial_specs:
            if spec.dial_id == dial_id:
                return spec
        raise KeyError(f"no spec for dial {dial_id!r}")


def empty_config_snapshot(
    config_snapshot_id: str, *, staleness_window_seconds: float
) -> ConfigSnapshot:
    """The WO-2 configuration: both dials declared, zero inputs, no model, no sources.

    This is the shipped state while CD-D-005 is owed (BLUEPRINT §16). Evaluating against
    it yields ``Unknown`` for both dials, which is the honest answer and not a
    placeholder.

    **BOTH registries are empty here rather than absent**, and the facts reinforce each
    other: with nothing registered, the source registry's first invariant means no dial
    COULD declare an input even if someone added one to a spec without touching the
    registry, and the model registry's first invariant means no ``model_ref`` resolves —
    so no ``ModelSpec`` reaches the executor by any route whatever.
    """
    return ConfigSnapshot(
        config_snapshot_id=config_snapshot_id,
        dial_specs=tuple(
            DialSpec(
                dial_id=dial_id,
                required_input_ids=(),
                contributing_input_ids=(),
                model_ref=None,
            )
            for dial_id in DIAL_IDS
        ),
        staleness_window_seconds=staleness_window_seconds,
        source_registry=EMPTY_SOURCE_REGISTRY,
        model_registry=EMPTY_MODEL_REGISTRY,
    )
