"""The registry wired into ``ConfigSnapshot`` (deliverable A4, BLUEPRINT §5 and §7).

Two invariants join the snapshot's constructor with the registry, and they are
load-bearing together: every named input must be registered, and a source's declared
criticality must agree with the set it is named in. The equivalent DATABASE constraint is
deliverable A5 and is owed; both must exist, because this one refuses an incoherent
configuration before an evaluation runs and that one refuses an incoherent row whatever
wrote it.

**THIS FILE IS ABOUT THE SOURCE REGISTRY AND IS UNCHANGED IN WHAT IT ASSERTS.**
BP-AMENDMENT-0001 §C touched it in one mechanical way only: a dial that declares required
inputs must NAME a model, and the field it names one in is now ``model_ref`` — a name —
rather than ``contribution_model``, a field that held an object and does not exist any more.
The ``FakeModel`` double that used to satisfy that rule is deleted along with the type it
doubled; nothing here is an object with a ``compute`` method, because no field on the dial
path can hold one. Every assertion, every exception type and every node id below is as it
was. The model registry's own three invariants are tested where they belong, in
``tests/test_engine_model_registry.py``.
"""

from __future__ import annotations

import pytest

from crash_detector.dials.dialset import DIAL_IDS, EQUITY_DIAL_ID, MONETARY_DIAL_ID
from crash_detector.dials.reading import Unknown
from crash_detector.engine.config import ConfigSnapshot, DialSpec, empty_config_snapshot
from crash_detector.engine.evaluate import evaluate
from crash_detector.engine.model import (
    EMPTY_MODEL_REGISTRY,
    MappingKind,
    ModelProvenance,
    ModelRegistry,
    ModelSpec,
)
from crash_detector.source_registry import EMPTY_INDICATOR_MAPPING_REGISTRY
from crash_detector.source_registry import (
    EMPTY_SOURCE_REGISTRY,
    Criticality,
    CriticalityContractViolated,
    DisposableSourceIsLoadBearing,
    SourceNotRegistered,
    SourceRecord,
    SourceRegistry,
)

from conftest import FIXED_NOW, WINDOW_SECONDS


#: The model NAME a dial uses here. A name and nothing else — no object is involved, and no
#: mapping runs in this module. It exists only to satisfy ``DialSpec``'s own rule that a dial
#: declaring required inputs must name the model that maps them.
NAMES_A_MODEL = "model.test.v0"


def _model_registry_for(*specs: DialSpec) -> ModelRegistry:
    """One derived row per spec that names a model, MIRRORING that dial's declared inputs.

    Mechanical, for the reason ``_record`` is: these tests already declare the sources they
    mean, so deriving the model row from the same declaration means not one assertion had to
    move to accommodate the new field, and a test can never state one input set two ways.
    """
    return ModelRegistry(
        models=tuple(
            ModelSpec(
                model_id=spec.model_ref,
                dial_id=spec.dial_id,
                required_input_ids=spec.required_input_ids,
                contributing_input_ids=spec.contributing_input_ids,
                mapping=MappingKind.UNSPECIFIED,
                parameters=(),
                provenance=ModelProvenance(
                    stands_for="TEST DOUBLE; WO-2 registers no model",
                    account="TEST DOUBLE; the account of a real mapping is CD-D-005",
                    decided_by="TEST DOUBLE; no product decision registers a model here",
                ),
            )
            for spec in specs
            if spec.model_ref is not None
        )
    )


def _record(source_id: str, criticality: Criticality) -> SourceRecord:
    return SourceRecord(
        source_id=source_id,
        adapter_id="fake.adapter.v0",
        cadence_seconds=300,
        criticality=criticality,
        stands_for="TEST DOUBLE; WO-2 registers no ingredient source",
    )


def _snapshot(*, equity: DialSpec, monetary: DialSpec, registry: SourceRegistry):
    return ConfigSnapshot(
        config_snapshot_id="cfg-test",
        dial_specs=(equity, monetary),
        staleness_window_seconds=WINDOW_SECONDS,
        source_registry=registry,
        indicator_mapping_registry=EMPTY_INDICATOR_MAPPING_REGISTRY,
        model_registry=_model_registry_for(equity, monetary),
    )


def _bare(dial_id: str) -> DialSpec:
    return DialSpec(
        dial_id=dial_id,
        required_input_ids=(),
        contributing_input_ids=(),
        model_ref=None,
    )


# --- THE SHIPPED WO-2 STATE ------------------------------------------------------------- #

def test_the_shipped_snapshot_carries_an_empty_registry_and_both_dials_read_unknown():
    """The doctrinally correct empty state, end to end.

    Nothing is registered, therefore no dial may declare an input, therefore both dials
    read ``Unknown``. Each step is enforced rather than merely true today.
    """
    config = empty_config_snapshot("cfg-wo2", staleness_window_seconds=WINDOW_SECONDS)

    assert config.source_registry is EMPTY_SOURCE_REGISTRY
    assert config.source_registry.is_empty

    dials = evaluate([], config, FIXED_NOW)
    assert isinstance(dials.equity, Unknown)
    assert isinstance(dials.monetary, Unknown)


def test_the_registry_is_required_and_has_no_default():
    """A registry nobody chose is not evidence of anything.

    In particular, an empty registry that arrived by omission looks identical to the
    deliberate WO-2 empty state, and only one of the two is a decision.

    BOTH registries are asserted, separately, because "required with no default" is a
    property of each field and a test that omitted both at once could not tell which one
    the constructor was actually refusing.
    """
    with pytest.raises(TypeError):
        ConfigSnapshot(  # type: ignore[call-arg]
            config_snapshot_id="cfg-test",
            dial_specs=tuple(_bare(dial_id) for dial_id in DIAL_IDS),
            staleness_window_seconds=WINDOW_SECONDS,
            model_registry=EMPTY_MODEL_REGISTRY,
        )
    with pytest.raises(TypeError):
        ConfigSnapshot(  # type: ignore[call-arg]
            config_snapshot_id="cfg-test",
            dial_specs=tuple(_bare(dial_id) for dial_id in DIAL_IDS),
            staleness_window_seconds=WINDOW_SECONDS,
            source_registry=EMPTY_SOURCE_REGISTRY,
        )


def test_a_registry_of_the_wrong_type_is_refused():
    with pytest.raises(TypeError):
        _snapshot(
            equity=_bare(EQUITY_DIAL_ID),
            monetary=_bare(MONETARY_DIAL_ID),
            registry=("src.a",),  # type: ignore[arg-type]
        )


# --- INVARIANT 1: EVERY NAMED INPUT IS REGISTERED ---------------------------------------- #

@pytest.mark.parametrize("field_name", ["required_input_ids", "contributing_input_ids"])
def test_a_dial_may_not_name_an_unregistered_source(field_name):
    """Without this the criticality contract is vacuous.

    The cheapest way to make a DISPOSABLE source load-bearing is not to register it.
    """
    kwargs = dict(
        dial_id=EQUITY_DIAL_ID,
        required_input_ids=(),
        contributing_input_ids=(),
        model_ref=NAMES_A_MODEL,
    )
    kwargs[field_name] = ("src.ghost",)
    with pytest.raises(SourceNotRegistered):
        _snapshot(
            equity=DialSpec(**kwargs),
            monetary=_bare(MONETARY_DIAL_ID),
            registry=EMPTY_SOURCE_REGISTRY,
        )


# --- INVARIANT 2: CRITICALITY AGREES WITH THE SET ---------------------------------------- #

def test_a_disposable_source_cannot_be_a_dials_required_input():
    """The rule the dispatch names explicitly, at the config level. A5 owes the SQL."""
    registry = SourceRegistry(sources=(_record("src.d", Criticality.DISPOSABLE),))
    with pytest.raises(DisposableSourceIsLoadBearing):
        _snapshot(
            equity=DialSpec(
                dial_id=EQUITY_DIAL_ID,
                required_input_ids=("src.d",),
                contributing_input_ids=(),
                model_ref=NAMES_A_MODEL,
            ),
            monetary=_bare(MONETARY_DIAL_ID),
            registry=registry,
        )


def test_the_disposable_rule_holds_on_the_second_dial_too():
    """A guard that watches one dial is a guard an author walks around.

    The registry check runs per spec, so this is the same proposition reached through the
    other slot rather than a second, independently-written rule.
    """
    registry = SourceRegistry(sources=(_record("src.d", Criticality.DISPOSABLE),))
    with pytest.raises(DisposableSourceIsLoadBearing):
        _snapshot(
            equity=_bare(EQUITY_DIAL_ID),
            monetary=DialSpec(
                dial_id=MONETARY_DIAL_ID,
                required_input_ids=("src.d",),
                contributing_input_ids=(),
                model_ref=NAMES_A_MODEL,
            ),
            registry=registry,
        )


def test_a_disposable_source_cannot_be_a_dials_contributing_input():
    registry = SourceRegistry(sources=(_record("src.d", Criticality.DISPOSABLE),))
    with pytest.raises(DisposableSourceIsLoadBearing):
        _snapshot(
            equity=DialSpec(
                dial_id=EQUITY_DIAL_ID,
                required_input_ids=(),
                contributing_input_ids=("src.d",),
                model_ref=None,
            ),
            monetary=_bare(MONETARY_DIAL_ID),
            registry=registry,
        )


def test_a_contributing_source_cannot_be_promoted_into_the_required_set():
    registry = SourceRegistry(sources=(_record("src.c", Criticality.CONTRIBUTING),))
    with pytest.raises(CriticalityContractViolated):
        _snapshot(
            equity=DialSpec(
                dial_id=EQUITY_DIAL_ID,
                required_input_ids=("src.c",),
                contributing_input_ids=(),
                model_ref=NAMES_A_MODEL,
            ),
            monetary=_bare(MONETARY_DIAL_ID),
            registry=registry,
        )


def test_a_coherent_configuration_is_accepted():
    """The invariants refuse disagreement. They do not refuse configuration."""
    registry = SourceRegistry(
        sources=(
            _record("src.r", Criticality.REQUIRED),
            _record("src.c", Criticality.CONTRIBUTING),
            _record("src.d", Criticality.DISPOSABLE),
        )
    )
    config = _snapshot(
        equity=DialSpec(
            dial_id=EQUITY_DIAL_ID,
            required_input_ids=("src.r",),
            contributing_input_ids=("src.c",),
            model_ref=NAMES_A_MODEL,
        ),
        monetary=_bare(MONETARY_DIAL_ID),
        registry=registry,
    )
    assert config.source_registry.ids_with(Criticality.DISPOSABLE) == ("src.d",)
    assert config.spec_for(EQUITY_DIAL_ID).required_input_ids == ("src.r",)


def test_the_snapshot_is_frozen_so_the_registry_cannot_be_swapped_after_validation():
    """Otherwise the constructor's invariants are a formality.

    A caller who could reassign the registry after construction could pass a coherent one
    to the constructor and then substitute the one they wanted.
    """
    config = empty_config_snapshot("cfg-wo2", staleness_window_seconds=WINDOW_SECONDS)
    with pytest.raises(Exception):
        config.source_registry = SourceRegistry(  # type: ignore[misc]
            sources=(_record("src.d", Criticality.DISPOSABLE),)
        )
