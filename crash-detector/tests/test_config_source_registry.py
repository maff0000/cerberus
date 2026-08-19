"""The registry wired into ``ConfigSnapshot`` (deliverable A4, BLUEPRINT §5 and §7).

Two invariants join the snapshot's constructor with the registry, and they are
load-bearing together: every named input must be registered, and a source's declared
criticality must agree with the set it is named in. The equivalent DATABASE constraint is
deliverable A5 and is owed; both must exist, because this one refuses an incoherent
configuration before an evaluation runs and that one refuses an incoherent row whatever
wrote it.
"""

from __future__ import annotations

import pytest

from crash_detector.dials.dialset import DIAL_IDS, EQUITY_DIAL_ID, MONETARY_DIAL_ID
from crash_detector.dials.reading import Unknown
from crash_detector.engine.config import ConfigSnapshot, DialSpec, empty_config_snapshot
from crash_detector.engine.evaluate import evaluate
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


class FakeModel:
    """TEST DOUBLE. Never called here; present only to satisfy DialSpec's own rule that
    a dial declaring required inputs must declare the model that maps them."""

    @property
    def model_id(self) -> str:
        return "fake.model.v0"

    def compute(self, payloads):  # pragma: no cover - never invoked in this module
        raise AssertionError("no model runs in these tests")


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
    )


def _bare(dial_id: str) -> DialSpec:
    return DialSpec(
        dial_id=dial_id,
        required_input_ids=(),
        contributing_input_ids=(),
        contribution_model=None,
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
    """
    with pytest.raises(TypeError):
        ConfigSnapshot(  # type: ignore[call-arg]
            config_snapshot_id="cfg-test",
            dial_specs=tuple(_bare(dial_id) for dial_id in DIAL_IDS),
            staleness_window_seconds=WINDOW_SECONDS,
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
        contribution_model=FakeModel(),
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
                contribution_model=FakeModel(),
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
                contribution_model=FakeModel(),
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
                contribution_model=None,
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
                contribution_model=FakeModel(),
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
            contribution_model=FakeModel(),
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
