"""MODELS ARE DATA — the BASELINE arms of P1, P2, P3, P4 and P8 (BP-AMENDMENT-0001 §F.1).

Every test in this file is the BASELINE arm of a planted violation: the structure is
present, and the plant is refused. **A BASELINE ARM ALONE IS HALF THE EVIDENCE.** A guard
nobody has seen refuse anything is a rumour, and a guard nobody has seen FAIL to refuse is
an untested one — so each plant also has a VIOLATED arm, run in a pristine throwaway
extraction with the structure removed, showing the escape returning. The violated arms
cannot live here (they need a differently-shaped tree) and are recorded with their exact
command lines and observed output in this increment's Build Log entry and commit message.

====================================================================================
"ALL OVER EMPTY_MODEL_REGISTRY" — WHAT THAT MEANS HERE, PRECISELY
====================================================================================

The Product Owner's standing condition is that every plant runs over
:data:`~crash_detector.engine.model.EMPTY_MODEL_REGISTRY`, and it is worth being exact
about what is and is not claimed, because the two halves are different:

1. **THE PRODUCT REGISTERS ZERO MODELS AND ZERO SOURCES, AND NO PLANT CHANGES THAT.**
   Nothing in this file registers a row in the application. ``EMPTY_MODEL_REGISTRY`` is
   what ships, ``empty_config_snapshot`` is what the product builds, and every route below
   is shown to die against exactly that shipped configuration — at RESOLUTION, with
   :exc:`~crash_detector.engine.model.ModelNotRegistered`, before any plant-specific
   refusal is even reached. That is the arm named ``…_over_the_shipped_empty_registry`` on
   each plant, and it is the one the standing condition is about.

2. **P3, P4 AND P8 ALSO CONSTRUCT A ``ModelSpec`` LOCALLY, AND MUST.** They plant against
   ``ConfigSnapshot``'s second and third invariants and against the executor, and those
   cannot be reached at all without a spec to reach them with. This is exactly why
   PO-DECISIONS-0005 ruling 2 made ``MappingKind`` ship non-empty: *"P3 and P4 must
   construct a ModelSpec to plant against ConfigSnapshot invariants 2 and 3, and over an
   empty enum they die at ModelSpec construction for a reason that is not under test. A
   criterion that cannot be demonstrated is a rumour."* A spec built inside a test is not a
   registered product model, and no such spec escapes this file.

Both halves are shown for every plant, separately, so neither can be read as the other.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from crash_detector.dials.dialset import EQUITY_DIAL_ID, MONETARY_DIAL_ID
from crash_detector.engine.config import ConfigSnapshot, DialSpec, empty_config_snapshot
from crash_detector.engine.evaluate import evaluate
from crash_detector.engine.mapping import (
    MAPPINGS_WITH_AN_EXECUTOR_BRANCH,
    UnspecifiedMapping,
    compute,
)
from crash_detector.engine.model import (
    EMPTY_MODEL_REGISTRY,
    DeclaredParameter,
    MappingKind,
    ModelBoundToAnotherDial,
    ModelNotRegistered,
    ModelProvenance,
    ModelReadsUndeclaredInput,
    ModelRegistry,
    ModelSpec,
)
from crash_detector.observations import OK, ObservationRecord
from crash_detector.own_terms import NotEstablishedOnOwnTerms
from crash_detector.source_registry import EMPTY_INDICATOR_MAPPING_REGISTRY
from crash_detector.source_registry import (
    Criticality,
    SourceRecord,
    SourceRegistry,
)

from conftest import FIXED_NOW, WINDOW_SECONDS


# ========================================================================================= #
# THE PLANT ITSELF — the auditor's ASR3-F02 object, transcribed rather than paraphrased
# ========================================================================================= #

class CarryingModel:
    """THE AUDITOR'S PLANT, VERBATIM IN BEHAVIOUR.

    Transcribed from ``variants/WO-2R2/CLASS-1/CD-ENG-WO2R2-V05-stateful-model-shared-by-
    both-dials.patch`` — the object CD-ASR-WO2R2-01 wrote and the Project Lead replicated
    (BL-…-0047). "Pure by contract, stateful in fact": one instance given to BOTH dial specs
    saw the equity dial's payloads on the first call and the monetary dial's on the second,
    averaged them in its own memory, and returned the mean as the SECOND dial's magnitude —
    publishing **monetary 0.5** out of an equity 0.9 and a monetary 0.1, through
    ``number_for_dial_slot``, the one declared publication gate, with every static layer
    green.

    It is reproduced here rather than referenced because a plant an auditor has to go and
    find is a plant that does not get run. **IT IS ORDINARY PYTHON AND THIS AMENDMENT DOES
    NOT TRY TO STOP ANYONE WRITING IT** — §C's claim is that there is nowhere to PUT it, not
    that the class cannot be defined. Every test below hands this exact object to the dial
    path and watches the interpreter or a constructor refuse it.
    """

    def __init__(self) -> None:
        self.seen: list = []

    @property
    def model_id(self) -> str:
        return "carrying.model.v0"

    def compute(self, payloads):
        figure = float(list(payloads.values())[0]["figure"])
        self.seen.append(figure)
        carried = sum(self.seen) / len(self.seen)
        return type("_", (), {"magnitude": carried, "contributions": ()})()


NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)

TEST_PROVENANCE = ModelProvenance(
    stands_for="TEST DOUBLE; WO-2 registers no model",
    account="TEST DOUBLE; the account of a real mapping is CD-D-005 and is owed",
    decided_by="TEST DOUBLE; no product decision registers a model in WO-2",
)


def _model(
    model_id: str,
    dial_id: str,
    required=(),
    contributing=(),
    mapping=MappingKind.UNSPECIFIED,
) -> ModelSpec:
    return ModelSpec(
        model_id=model_id,
        dial_id=dial_id,
        required_input_ids=tuple(required),
        contributing_input_ids=tuple(contributing),
        mapping=mapping,
        parameters=(),
        provenance=TEST_PROVENANCE,
    )


def _sources(*source_ids: str) -> SourceRegistry:
    return SourceRegistry(
        sources=tuple(
            SourceRecord(
                source_id=source_id,
                adapter_id="fake.adapter.v0",
                cadence_seconds=60,
                criticality=Criticality.REQUIRED,
                stands_for="TEST DOUBLE source; WO-2 registers no ingredient source",
            )
            for source_id in source_ids
        )
    )


def _ok(source_id: str, figure: float) -> ObservationRecord:
    return ObservationRecord(
        source_id=source_id,
        observed_utc=NOW,
        outcome=OK(
            payload={"figure": figure},
            source_as_of_utc=NOW - timedelta(seconds=5),
        ),
    )


# ========================================================================================= #
# P1 — THE AUDITOR'S ASR3-F02 MODEL OBJECT INTO DialSpec.
#      MUST FAIL AT: DialSpec construction.
# ========================================================================================= #

def test_p1_the_auditors_model_object_cannot_be_given_to_a_dialspec_at_all():
    """P1, BASELINE. The plant dies at the constructor of the FIRST ``DialSpec``.

    THE REFUSING LAYER IS THE PYTHON DATACLASS CONSTRUCTOR ITSELF, and its scope is every
    construction of a ``DialSpec`` by any caller anywhere, including ones that go on to be
    ignored. There is no field named ``contribution_model``, so the keyword is not a bad
    value — it is not a parameter.

    RENAME TEST: SURVIVES. Nothing here compares a name. Rename every identifier in
    ``engine/config.py`` and a keyword the dataclass does not declare is still a TypeError,
    because the refusal is the interpreter's own argument binding.
    """
    plant = CarryingModel()
    with pytest.raises(TypeError) as raised:
        DialSpec(  # type: ignore[call-arg]
            dial_id=EQUITY_DIAL_ID,
            required_input_ids=("src.e",),
            contributing_input_ids=(),
            contribution_model=plant,
        )
    assert "contribution_model" in str(raised.value)


def test_p1_the_field_that_held_an_object_does_not_exist_on_the_type_or_the_instance():
    """P1, BASELINE. The field is DELETED, not emptied — asserted three ways.

    A field narrowed to ``None`` would still be an attribute to write to with
    ``object.__setattr__``. This asserts the stronger thing: the name is absent from the
    dataclass's declared fields, absent from the constructor's signature, and absent from
    an instance.
    """
    import dataclasses
    import inspect

    spec = DialSpec(
        dial_id=EQUITY_DIAL_ID,
        required_input_ids=(),
        contributing_input_ids=(),
        model_ref=None,
    )
    names = {field.name for field in dataclasses.fields(DialSpec)}
    assert "contribution_model" not in names
    assert "model_ref" in names
    assert "contribution_model" not in inspect.signature(DialSpec).parameters
    assert not hasattr(spec, "contribution_model")


def test_p1_the_plant_adapted_to_the_new_field_is_refused_because_an_object_is_not_a_name():
    """P1, BASELINE. The obvious next move, and it is refused too.

    An auditor who reads the diff will not stop at the deleted keyword; they will put the
    object in ``model_ref``. THE REFUSING LAYER IS ``own_model_id`` — that is,
    ``own_str``'s ``isinstance(value, str)`` — and its scope is every ``model_ref`` on
    every ``DialSpec``, plus every ``model_id`` on every ``ModelSpec`` and every lookup
    through ``ModelRegistry.get``.

    RENAME TEST: SURVIVES. The refusal is a type test against ``str``, not a comparison
    against any name this codebase chose.
    """
    plant = CarryingModel()
    with pytest.raises(NotEstablishedOnOwnTerms) as raised:
        DialSpec(
            dial_id=EQUITY_DIAL_ID,
            required_input_ids=("src.e",),
            contributing_input_ids=(),
            model_ref=plant,  # type: ignore[arg-type]
        )
    assert "CarryingModel" in str(raised.value)


def test_p1_a_callable_str_subclass_is_rebuilt_as_a_str_that_cannot_be_called():
    """P1, BASELINE. The subtle version, which a type check on ``str`` would have admitted.

    A ``str`` subclass that is also callable passes ``isinstance(x, str)``. It does not
    survive ``own_str``, which rebuilds an exact ``str`` from the value's own code points —
    so what is STORED has no ``__call__`` at all. This is the difference between "we do not
    accept your type" and "we do not run your code", and only the second one closes it.
    """

    class CallableName(str):
        def __call__(self, payloads):  # pragma: no cover - never reached
            raise AssertionError("a stored model_ref must not be callable")

    spec = DialSpec(
        dial_id=EQUITY_DIAL_ID,
        required_input_ids=(),
        contributing_input_ids=(),
        model_ref=CallableName("model.smuggled.v0"),
    )
    assert type(spec.model_ref) is str
    assert not callable(spec.model_ref)


def test_p1_over_the_shipped_empty_registry():
    """P1, over EMPTY_MODEL_REGISTRY. The shipped configuration refuses it independently.

    Even supposing every refusal above were removed, the name the plant would have to be
    registered under resolves to nothing: the product ships zero rows. THE REFUSING LAYER
    IS ``ModelRegistry.get`` and its scope is every resolution of every ``model_ref``.
    """
    config = empty_config_snapshot("cfg-wo2", staleness_window_seconds=WINDOW_SECONDS)
    assert config.model_registry is EMPTY_MODEL_REGISTRY
    assert config.model_registry.is_empty
    with pytest.raises(ModelNotRegistered):
        config.model_registry.get("carrying.model.v0")
    # And the shipped snapshot still evaluates, to Unknown on both dials, with the plant
    # having nowhere to be. A closure that forbade the product would not be a closure.
    dials = evaluate([_ok("src.e", 0.9)], config, NOW)
    assert not hasattr(dials.equity, "value")
    assert not hasattr(dials.monetary, "value")


# ========================================================================================= #
# P2 — A CALLABLE INTO ANY ModelSpec FIELD.
#      MUST FAIL AT: ModelSpec construction.
# ========================================================================================= #

@pytest.mark.parametrize(
    "field_name",
    [
        "model_id",
        "dial_id",
        "required_input_ids",
        "contributing_input_ids",
        "mapping",
        "parameters",
        "provenance",
    ],
)
def test_p2_a_callable_is_refused_by_every_single_field_of_a_modelspec(field_name):
    """P2, BASELINE. **EVERY** field, enumerated from the dataclass, not from a list I chose.

    The parametrisation is asserted complete against ``dataclasses.fields`` in
    ``test_p2_the_parametrisation_covers_every_declared_field`` below, so a field ADDED to
    ``ModelSpec`` later without being planted against fails that test rather than quietly
    becoming an unplanted door.

    THE REFUSING LAYERS, per field, each with its scope:
      * ``model_id`` / ``dial_id`` — ``own_str``: every id on every ``ModelSpec``;
      * both id tuples — ``own_str`` elementwise: every source id a model declares;
      * ``mapping`` — ``type(x) is not MappingKind``: an ``Enum`` with members cannot be
        subclassed by the interpreter, so there is no subclass this could admit;
      * ``parameters`` — ``type(x) is not DeclaredParameter``, elementwise;
      * ``provenance`` — ``type(x) is not ModelProvenance``.

    RENAME TEST: SURVIVES, for all seven. Not one refusal compares a name: they are a type
    rebuild from primitives, an enum's closed membership, and exact-type identity.
    """
    plant = CarryingModel()
    kwargs = dict(
        model_id="model.p2.v0",
        dial_id=EQUITY_DIAL_ID,
        required_input_ids=(),
        contributing_input_ids=(),
        mapping=MappingKind.UNSPECIFIED,
        parameters=(),
        provenance=TEST_PROVENANCE,
    )
    # For the tuple-valued fields the interesting plant is a callable INSIDE the tuple, not
    # a callable instead of it: a bare object fails on iteration for a reason that is not
    # under test, and a plant that dies for the wrong reason proves nothing.
    if field_name in ("required_input_ids", "contributing_input_ids", "parameters"):
        kwargs[field_name] = (plant,)
    else:
        kwargs[field_name] = plant

    with pytest.raises((TypeError, ValueError)) as raised:
        ModelSpec(**kwargs)  # type: ignore[arg-type]
    assert not isinstance(raised.value, AssertionError)


def test_p2_the_parametrisation_covers_every_declared_field():
    """P2, BASELINE. The plant enumerates its subject FROM THE ARTEFACT.

    A plant over a hand-written list of fields goes silently out of date the moment a field
    is added. This asserts by SET EQUALITY, in both directions, that the seven fields
    planted above are exactly the fields ``ModelSpec`` declares — so a new field arrives
    with a failing test rather than as an unplanted door.
    """
    import dataclasses

    planted = {
        "model_id",
        "dial_id",
        "required_input_ids",
        "contributing_input_ids",
        "mapping",
        "parameters",
        "provenance",
    }
    declared = {field.name for field in dataclasses.fields(ModelSpec)}
    assert planted == declared, (
        "ModelSpec's fields and P2's planted fields disagree. A field this plant does not "
        "cover is a field nobody has watched refuse a callable."
    )


def test_p2_no_field_on_a_constructed_modelspec_holds_anything_callable():
    """P2, BASELINE. The property stated positively, over a real spec.

    The parametrised test shows each field REFUSING. This shows the complementary thing:
    for a spec that was accepted, nothing reachable through its declared fields is
    callable. It walks the fields from ``dataclasses.fields`` rather than naming them.
    """
    import dataclasses

    spec = _model("model.p2.ok.v0", EQUITY_DIAL_ID, required=("src.e",))
    for field in dataclasses.fields(spec):
        value = getattr(spec, field.name)
        assert not callable(value), f"{field.name} holds a callable"
        if isinstance(value, tuple):
            for element in value:
                assert not callable(element)


# ========================================================================================= #
# P3 — AN EQUITY-BOUND ModelSpec NAMED BY THE MONETARY DialSpec.
#      MUST FAIL AT: ConfigSnapshot construction.
# ========================================================================================= #

def test_p3_a_model_bound_to_one_dial_cannot_be_named_by_the_other():
    """P3, BASELINE. ``ASR3-F02``'s cross-dial mechanism, met by the shape of the data.

    THE REFUSING LAYER IS ``establish_model_for_dial``'s invariant 2, called from
    ``ConfigSnapshot.__post_init__``. ITS SCOPE is every ``ConfigSnapshot`` construction and
    every resolution, for every dial — it is one function, called at both, so the two
    cannot come apart.

    RENAME TEST: SURVIVES. The refusal is ``model.dial_id != dial_id`` between two strings
    this package rebuilt through ``own_str``; it names no identifier and depends on no
    vocabulary. It would still fire if both dials were renamed, because both sides of the
    comparison come from the same rename.
    """
    equity_bound = _model("model.shared.v0", EQUITY_DIAL_ID, required=("src.e",))
    with pytest.raises(ModelBoundToAnotherDial) as raised:
        ConfigSnapshot(
            config_snapshot_id="cfg-p3",
            dial_specs=(
                DialSpec(
                    dial_id=EQUITY_DIAL_ID,
                    required_input_ids=("src.e",),
                    contributing_input_ids=(),
                    model_ref="model.shared.v0",
                ),
                DialSpec(
                    dial_id=MONETARY_DIAL_ID,
                    required_input_ids=("src.e",),
                    contributing_input_ids=(),
                    model_ref="model.shared.v0",
                ),
            ),
            staleness_window_seconds=WINDOW_SECONDS,
            source_registry=_sources("src.e"),
            indicator_mapping_registry=EMPTY_INDICATOR_MAPPING_REGISTRY,
            model_registry=ModelRegistry(models=(equity_bound,)),
        )
    assert MONETARY_DIAL_ID in str(raised.value)


def test_p3_there_is_no_object_to_place_in_both_specs_in_the_first_place():
    """P3, BASELINE. The deeper half of §C.4, and the reason P3 is not merely a check.

    ``ASR3-F02`` worked because ONE OBJECT was in both specs and carried state between the
    two calls. Two dials may legitimately name two rows that declare the same MAPPING — and
    that blends nothing, because a ``ModelSpec`` is frozen data with no memory, and the
    executor is a function of one dial's spec and one dial's payloads with no reference to
    the other dial's payloads to close over.

    So this constructs the legitimate case and asserts it is ACCEPTED — a false-positive
    control — and that the two rows are distinct data carrying no shared mutable state.
    """
    config = ConfigSnapshot(
        config_snapshot_id="cfg-p3-ok",
        dial_specs=(
            DialSpec(
                dial_id=EQUITY_DIAL_ID,
                required_input_ids=("src.e",),
                contributing_input_ids=(),
                model_ref="model.equity.v0",
            ),
            DialSpec(
                dial_id=MONETARY_DIAL_ID,
                required_input_ids=("src.m",),
                contributing_input_ids=(),
                model_ref="model.monetary.v0",
            ),
        ),
        staleness_window_seconds=WINDOW_SECONDS,
        source_registry=_sources("src.e", "src.m"),
        indicator_mapping_registry=EMPTY_INDICATOR_MAPPING_REGISTRY,
        model_registry=ModelRegistry(
            models=(
                _model("model.equity.v0", EQUITY_DIAL_ID, required=("src.e",)),
                _model("model.monetary.v0", MONETARY_DIAL_ID, required=("src.m",)),
            )
        ),
    )
    equity_model = config.model_for(EQUITY_DIAL_ID)
    monetary_model = config.model_for(MONETARY_DIAL_ID)
    assert equity_model is not monetary_model
    assert equity_model.mapping is monetary_model.mapping, (
        "two rows naming the SAME mapping is legitimate and blends nothing"
    )
    assert equity_model.dial_id == EQUITY_DIAL_ID
    assert monetary_model.dial_id == MONETARY_DIAL_ID


def test_p3_a_dial_id_rewritten_after_snapshot_construction_is_refused_at_resolution():
    """P3, BASELINE. ``object.__setattr__`` walks past frozen — and is caught at the second
    reading.

    This is the DECLARED LIMIT of :mod:`crash_detector.engine.model` boundary 1, and the
    measurement that shows what carries it. The snapshot is built coherently, then the
    resolved row's ``dial_id`` is rewritten to the other dial. Because
    ``establish_model_for_dial`` runs AGAIN at every resolution — the same function, not a
    second copy — the rewrite is refused when the model is next resolved rather than
    silently applied.
    """
    model = _model("model.equity.v0", EQUITY_DIAL_ID, required=("src.e",))
    config = ConfigSnapshot(
        config_snapshot_id="cfg-p3-rewrite",
        dial_specs=(
            DialSpec(
                dial_id=EQUITY_DIAL_ID,
                required_input_ids=("src.e",),
                contributing_input_ids=(),
                model_ref="model.equity.v0",
            ),
            DialSpec(
                dial_id=MONETARY_DIAL_ID,
                required_input_ids=(),
                contributing_input_ids=(),
                model_ref=None,
            ),
        ),
        staleness_window_seconds=WINDOW_SECONDS,
        source_registry=_sources("src.e"),
        indicator_mapping_registry=EMPTY_INDICATOR_MAPPING_REGISTRY,
        model_registry=ModelRegistry(models=(model,)),
    )
    assert config.model_for(EQUITY_DIAL_ID) is model

    object.__setattr__(model, "dial_id", MONETARY_DIAL_ID)
    with pytest.raises(ModelBoundToAnotherDial):
        config.model_for(EQUITY_DIAL_ID)
    with pytest.raises(ModelBoundToAnotherDial):
        evaluate([_ok("src.e", 0.9)], config, NOW)


def test_p3_over_the_shipped_empty_registry():
    """P3, over EMPTY_MODEL_REGISTRY. No row exists to be bound to either dial.

    THE REFUSING LAYER IS ``ModelRegistry.get``, at RESOLUTION, and it fires before
    invariant 2 is reached at all — which is the point of §E's step 7: with zero rows the
    cross-dial route is not merely refused, it is unreachable.
    """
    with pytest.raises(ModelNotRegistered):
        ConfigSnapshot(
            config_snapshot_id="cfg-p3-empty",
            dial_specs=(
                DialSpec(
                    dial_id=EQUITY_DIAL_ID,
                    required_input_ids=("src.e",),
                    contributing_input_ids=(),
                    model_ref="model.shared.v0",
                ),
                DialSpec(
                    dial_id=MONETARY_DIAL_ID,
                    required_input_ids=(),
                    contributing_input_ids=(),
                    model_ref=None,
                ),
            ),
            staleness_window_seconds=WINDOW_SECONDS,
            source_registry=_sources("src.e"),
            indicator_mapping_registry=EMPTY_INDICATOR_MAPPING_REGISTRY,
            model_registry=EMPTY_MODEL_REGISTRY,
        )


# ========================================================================================= #
# P4 — A ModelSpec READING AN UNDECLARED INPUT.
#      MUST FAIL AT: ConfigSnapshot construction.
# ========================================================================================= #

def test_p4_a_model_may_not_read_an_input_its_dial_did_not_declare():
    """P4, BASELINE. The source registry's own evasion, one level up.

    THE REFUSING LAYER IS ``establish_model_for_dial``'s invariant 3, called from
    ``ConfigSnapshot.__post_init__`` and again at every resolution. ITS SCOPE is every
    (dial, model) pair in every snapshot.

    RENAME TEST: SURVIVES. The refusal is a set difference between two tuples of strings
    this package rebuilt; it names nothing.
    """
    reads_more = _model(
        "model.greedy.v0", EQUITY_DIAL_ID, required=("src.e", "src.undeclared")
    )
    with pytest.raises(ModelReadsUndeclaredInput) as raised:
        ConfigSnapshot(
            config_snapshot_id="cfg-p4",
            dial_specs=(
                DialSpec(
                    dial_id=EQUITY_DIAL_ID,
                    required_input_ids=("src.e",),
                    contributing_input_ids=(),
                    model_ref="model.greedy.v0",
                ),
                DialSpec(
                    dial_id=MONETARY_DIAL_ID,
                    required_input_ids=(),
                    contributing_input_ids=(),
                    model_ref=None,
                ),
            ),
            staleness_window_seconds=WINDOW_SECONDS,
            source_registry=_sources("src.e", "src.undeclared"),
            indicator_mapping_registry=EMPTY_INDICATOR_MAPPING_REGISTRY,
            model_registry=ModelRegistry(models=(reads_more,)),
        )
    assert "src.undeclared" in str(raised.value)


def test_p4_a_model_may_not_promote_a_contributing_input_to_required():
    """P4, BASELINE. The same invariant reached by MOVING an id rather than adding one.

    The dial declares ``src.c`` as CONTRIBUTING; the model declares the same id as
    REQUIRED. The union is a subset of the union, so a naive "is every model input one of
    the dial's inputs?" test would admit it — and it would change what absence means, since
    a required input's absence forces ``Unknown`` and a contributing one's forces
    ``Degraded`` (BLUEPRINT §5). The invariant is a subset test PER SET for exactly this
    reason, and this is the plant that proves the per-set half is load-bearing.
    """
    promotes = _model("model.promoting.v0", EQUITY_DIAL_ID, required=("src.c",))
    registry = SourceRegistry(
        sources=(
            SourceRecord(
                source_id="src.c",
                adapter_id="fake.adapter.v0",
                cadence_seconds=60,
                criticality=Criticality.CONTRIBUTING,
                stands_for="TEST DOUBLE source",
            ),
        )
    )
    with pytest.raises(ModelReadsUndeclaredInput):
        ConfigSnapshot(
            config_snapshot_id="cfg-p4-promote",
            dial_specs=(
                DialSpec(
                    dial_id=EQUITY_DIAL_ID,
                    required_input_ids=(),
                    contributing_input_ids=("src.c",),
                    model_ref="model.promoting.v0",
                ),
                DialSpec(
                    dial_id=MONETARY_DIAL_ID,
                    required_input_ids=(),
                    contributing_input_ids=(),
                    model_ref=None,
                ),
            ),
            staleness_window_seconds=WINDOW_SECONDS,
            source_registry=registry,
            indicator_mapping_registry=EMPTY_INDICATOR_MAPPING_REGISTRY,
            model_registry=ModelRegistry(models=(promotes,)),
        )


def test_p4_a_model_reading_exactly_what_its_dial_declares_is_accepted():
    """P4, BASELINE. FALSE-POSITIVE CONTROL. A closure that forbids the product is not one.

    Both sets, both non-empty, both matching the dial exactly, with the criticalities
    agreeing in the source registry. It must construct.
    """
    registry = SourceRegistry(
        sources=(
            SourceRecord(
                source_id="src.r",
                adapter_id="a",
                cadence_seconds=60,
                criticality=Criticality.REQUIRED,
                stands_for="TEST DOUBLE source",
            ),
            SourceRecord(
                source_id="src.c",
                adapter_id="a",
                cadence_seconds=60,
                criticality=Criticality.CONTRIBUTING,
                stands_for="TEST DOUBLE source",
            ),
        )
    )
    config = ConfigSnapshot(
        config_snapshot_id="cfg-p4-ok",
        dial_specs=(
            DialSpec(
                dial_id=EQUITY_DIAL_ID,
                required_input_ids=("src.r",),
                contributing_input_ids=("src.c",),
                model_ref="model.exact.v0",
            ),
            DialSpec(
                dial_id=MONETARY_DIAL_ID,
                required_input_ids=(),
                contributing_input_ids=(),
                model_ref=None,
            ),
        ),
        staleness_window_seconds=WINDOW_SECONDS,
        source_registry=registry,
        indicator_mapping_registry=EMPTY_INDICATOR_MAPPING_REGISTRY,
        model_registry=ModelRegistry(
            models=(
                _model(
                    "model.exact.v0",
                    EQUITY_DIAL_ID,
                    required=("src.r",),
                    contributing=("src.c",),
                ),
            )
        ),
    )
    assert config.model_for(EQUITY_DIAL_ID).required_input_ids == ("src.r",)
    assert config.model_for(MONETARY_DIAL_ID) is None


def test_p4_a_model_reading_a_subset_of_its_dials_inputs_is_accepted():
    """P4, BASELINE. FALSE-POSITIVE CONTROL. It is a SUBSET rule, not an equality rule.

    A dial may declare an input its model does not read — the dial's declaration is what
    the collector fetches and what the absence post-condition measures against, and a model
    that reads fewer of them is not an incoherent configuration. Asserting this stops a
    later seat tightening the invariant to equality without noticing it changes the rule.
    """
    config = ConfigSnapshot(
        config_snapshot_id="cfg-p4-subset",
        dial_specs=(
            DialSpec(
                dial_id=EQUITY_DIAL_ID,
                required_input_ids=("src.e", "src.f"),
                contributing_input_ids=(),
                model_ref="model.subset.v0",
            ),
            DialSpec(
                dial_id=MONETARY_DIAL_ID,
                required_input_ids=(),
                contributing_input_ids=(),
                model_ref=None,
            ),
        ),
        staleness_window_seconds=WINDOW_SECONDS,
        source_registry=_sources("src.e", "src.f"),
        indicator_mapping_registry=EMPTY_INDICATOR_MAPPING_REGISTRY,
        model_registry=ModelRegistry(
            models=(_model("model.subset.v0", EQUITY_DIAL_ID, required=("src.e",)),)
        ),
    )
    assert config.model_for(EQUITY_DIAL_ID).required_input_ids == ("src.e",)


def test_p4_over_the_shipped_empty_registry():
    """P4, over EMPTY_MODEL_REGISTRY. There is no row to read anything, declared or not.

    THE REFUSING LAYER IS the SOURCE registry, first: with zero sources registered no dial
    may declare an input at all, so the configuration the plant needs cannot be built
    before the model registry is even consulted. Two independent empty registries, and
    either one alone stops it.
    """
    from crash_detector.source_registry import SourceNotRegistered

    with pytest.raises(SourceNotRegistered):
        ConfigSnapshot(
            config_snapshot_id="cfg-p4-empty",
            dial_specs=(
                DialSpec(
                    dial_id=EQUITY_DIAL_ID,
                    required_input_ids=("src.e",),
                    contributing_input_ids=(),
                    model_ref="model.greedy.v0",
                ),
                DialSpec(
                    dial_id=MONETARY_DIAL_ID,
                    required_input_ids=(),
                    contributing_input_ids=(),
                    model_ref=None,
                ),
            ),
            staleness_window_seconds=WINDOW_SECONDS,
            source_registry=EMPTY_SOURCE_REGISTRY_FOR_THE_PLANT,
            indicator_mapping_registry=EMPTY_INDICATOR_MAPPING_REGISTRY,
            model_registry=EMPTY_MODEL_REGISTRY,
        )


#: Named rather than imported inline so the plant above reads as what it is: the SHIPPED
#: empty source registry, not a registry this test emptied.
from crash_detector.source_registry import (  # noqa: E402
    EMPTY_SOURCE_REGISTRY as EMPTY_SOURCE_REGISTRY_FOR_THE_PLANT,
)


# ========================================================================================= #
# P8 — A ModelSpec WHOSE mapping IS MappingKind.UNSPECIFIED, RESOLVED AND EXECUTED.
#      MUST FAIL AT: the executor, with UnspecifiedMapping — AND NO MAGNITUDE RETURNED.
# ========================================================================================= #

def test_p8_the_executor_refuses_the_unspecified_mapping_and_returns_nothing():
    """P8, BASELINE. The one member computes nothing, and is watched refusing.

    PO-DECISIONS-0005 ruling 2 ships this member so P3 and P4 can be planted at all. *A
    refusing member nobody has watched refuse is a rumour one level down* — this is the
    watching.

    THE REFUSING LAYER IS ``engine.mapping.compute``'s ``UNSPECIFIED`` branch, and ITS
    SCOPE is every execution of every mapping, because it is the only branch there is.

    RENAME TEST: SURVIVES. The dispatch is ``spec.mapping is MappingKind.UNSPECIFIED`` — an
    identity comparison against an enum member object, not against its ``value`` string and
    not against its ``name``. Rename the member and the identity still holds.
    """
    spec = _model("model.p8.v0", EQUITY_DIAL_ID, required=("src.e",))
    with pytest.raises(UnspecifiedMapping) as raised:
        compute(spec, {"src.e": {"figure": 0.9}})

    # NOTHING IS RETURNED, asserted rather than assumed: the refusal carries no magnitude,
    # no numeric attribute and is not itself a number. CD-AC-001's failure mode is a number
    # standing in for an absence, and an exception with a number on it is that with an
    # extra step.
    assert not hasattr(raised.value, "magnitude")
    assert not isinstance(raised.value, (int, float))
    assert raised.value.args and isinstance(raised.value.args[0], str)


def test_p8_the_refusal_travels_out_of_evaluate_rather_than_becoming_a_reading():
    """P8, BASELINE. Reached through the real dial path, not by calling the executor.

    A refusal that only fires when the executor is called directly would be a refusal the
    product routes around. This drives a fully-supplied dial through ``evaluate`` and shows
    the refusal leaving it — not caught and turned into a number, and not caught and turned
    into ``Unknown``, which would publish "we have no data" when the truth is "there is no
    declared mapping".
    """
    config = ConfigSnapshot(
        config_snapshot_id="cfg-p8",
        dial_specs=(
            DialSpec(
                dial_id=EQUITY_DIAL_ID,
                required_input_ids=("src.e",),
                contributing_input_ids=(),
                model_ref="model.p8.v0",
            ),
            DialSpec(
                dial_id=MONETARY_DIAL_ID,
                required_input_ids=(),
                contributing_input_ids=(),
                model_ref=None,
            ),
        ),
        staleness_window_seconds=WINDOW_SECONDS,
        source_registry=_sources("src.e"),
        indicator_mapping_registry=EMPTY_INDICATOR_MAPPING_REGISTRY,
        model_registry=ModelRegistry(
            models=(_model("model.p8.v0", EQUITY_DIAL_ID, required=("src.e",)),)
        ),
    )
    with pytest.raises(UnspecifiedMapping):
        evaluate([_ok("src.e", 0.9)], config, NOW)


def test_p8_the_enum_ships_exactly_one_member_and_it_is_the_refusing_one():
    """P8, BASELINE. The ruling itself, asserted as a property of the artefact.

    PO-DECISIONS-0005 ruling 2: exactly one member, and it computes nothing. A second
    member is a PRODUCT decision that arrives only with the CD-D-005 register — a seat
    adding one is inventing product meaning (``PBG-AUTH-005``, CD-RULE-003) — so this test
    is the tripwire that makes such an addition visible instead of quiet.
    """
    assert list(MappingKind) == [MappingKind.UNSPECIFIED]
    assert MAPPINGS_WITH_AN_EXECUTOR_BRANCH == frozenset(MappingKind), (
        "every declared mapping must have a branch in the executor and vice versa; the "
        "module asserts this at import, and this asserts that the assertion is live"
    )


def test_p8_no_code_path_in_the_executor_module_returns_a_number():
    """P8, BASELINE. Stated as a property of the SOURCE, not of the runs I happened to try.

    A runtime plant shows one path refusing. This reads the module's AST and asserts that
    ``compute`` contains no ``return`` with a value at all — so there is no branch, reached
    or unreached, that hands back a magnitude. That is what "no else, no fallthrough, no
    numeric return anywhere on that path" means, checked rather than promised.
    """
    import ast
    import inspect

    import crash_detector.engine.mapping as mapping_module

    tree = ast.parse(inspect.getsource(mapping_module))
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "compute"
    ]
    assert len(functions) == 1, "expected exactly one compute() in the executor module"
    returns = [
        node
        for node in ast.walk(functions[0])
        if isinstance(node, ast.Return) and node.value is not None
    ]
    assert returns == [], (
        "compute() returns a value on some path. The one shipped mapping member REFUSES "
        "and returns nothing (PO-DECISIONS-0005 ruling 2); a return here would be a "
        "magnitude manufactured where a mapping is absent."
    )


def test_p8_the_executor_refuses_a_spec_whose_mapping_slot_was_rewritten():
    """P8, BASELINE. ``object.__setattr__`` past frozen, at the executor's own door.

    The declared limit of :mod:`crash_detector.engine.model` boundary 1, measured. The spec
    is built correctly and then its ``mapping`` slot is overwritten with something that is
    not a member. Because ``compute`` reads the SLOT rather than trusting the constructor
    that filled it, the rewrite is refused at the moment it would have selected a branch.

    The plant is a callable, deliberately: this is the last place an object could
    conceivably reach the computation, and it does not.
    """
    spec = _model("model.p8.rewrite.v0", EQUITY_DIAL_ID, required=("src.e",))
    object.__setattr__(spec, "mapping", CarryingModel())
    with pytest.raises(TypeError) as raised:
        compute(spec, {"src.e": {"figure": 0.9}})
    assert "MappingKind" in str(raised.value)


def test_p8_over_the_shipped_empty_registry():
    """P8, over EMPTY_MODEL_REGISTRY. The executor is UNREACHABLE in the shipped product.

    §C.2.1 in terms: *"Under EMPTY_MODEL_REGISTRY the executor is unreachable in the
    shipped configuration anyway: no model is registered, so no model_ref resolves, so no
    ModelSpec reaches engine.mapping.compute at all."* This is that sentence measured — the
    shipped snapshot evaluates to ``Unknown`` on both dials and no refusal is needed,
    because nothing gets far enough to need refusing.
    """
    config = empty_config_snapshot("cfg-wo2", staleness_window_seconds=WINDOW_SECONDS)
    assert config.model_for(EQUITY_DIAL_ID) is None
    assert config.model_for(MONETARY_DIAL_ID) is None
    dials = evaluate([_ok("src.e", 0.9), _ok("src.m", 0.1)], config, NOW)
    assert not hasattr(dials.equity, "value")
    assert not hasattr(dials.monetary, "value")


# ========================================================================================= #
# THE REGISTRY AND THE EXECUTOR'S OWN DOORS — not plants, but the structure they rest on
# ========================================================================================= #

def test_the_model_registry_refuses_a_row_that_is_not_exactly_a_modelspec():
    """EXACT TYPE, not ``isinstance`` — and the SUBCLASS is the plant that shows why.

    A ``ModelSpec`` subclass may shadow ``dial_id``, ``mapping`` or either input tuple, and
    every one of those is read inside an invariant that decides what a dial may compute. An
    ``isinstance`` check would admit it. Both arms are planted: a foreign object, and a
    genuine subclass carrying no override at all — because if the subclass is refused when
    it is harmless, no override is needed to make it dangerous.
    """
    class Subclassed(ModelSpec):
        pass

    row = Subclassed(
        model_id="model.subclassed.v0",
        dial_id=EQUITY_DIAL_ID,
        required_input_ids=(),
        contributing_input_ids=(),
        mapping=MappingKind.UNSPECIFIED,
        parameters=(),
        provenance=TEST_PROVENANCE,
    )
    assert isinstance(row, ModelSpec), "the plant IS a ModelSpec by isinstance"
    with pytest.raises(TypeError):
        ModelRegistry(models=(row,))
    with pytest.raises(TypeError):
        ModelRegistry(models=(CarryingModel(),))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        compute(row, {})


def test_the_model_registry_refuses_two_rows_with_one_name():
    """Two rows for one name is two mappings for one name, and which one a dial resolved to
    would depend on iteration order."""
    with pytest.raises(ValueError):
        ModelRegistry(
            models=(
                _model("model.same.v0", EQUITY_DIAL_ID),
                _model("model.same.v0", MONETARY_DIAL_ID),
            )
        )


def test_the_registry_is_not_a_caller_supplied_mapping_whose_lookup_it_would_run():
    """A ``Mapping`` supplied by a caller decides its own lookups.

    Holding one would mean resolution runs that object's ``__getitem__`` — the caller's
    code choosing which spec a dial resolved to, which is this amendment's own defect one
    storey down. The registry holds a TUPLE of exact-typed rows and does its own lookup.
    """
    class LyingMapping(dict):
        def __getitem__(self, key):  # pragma: no cover - never reached
            raise AssertionError("a supplied mapping must never decide a resolution")

        def get(self, key, default=None):  # pragma: no cover - never reached
            raise AssertionError("a supplied mapping must never decide a resolution")

    with pytest.raises(TypeError):
        ModelRegistry(models=LyingMapping({"a": 1}))  # type: ignore[arg-type]


def test_the_executor_refuses_a_spec_that_is_not_exactly_a_modelspec():
    """The plant handed straight to the executor, bypassing every constructor above it."""
    with pytest.raises(TypeError) as raised:
        compute(CarryingModel(), {"src.e": {"figure": 0.9}})  # type: ignore[arg-type]
    assert "ModelSpec" in str(raised.value)


def test_the_executor_refuses_payloads_it_did_not_receive_as_plain_dicts():
    """Which payload a source id maps to is not a supplied object's judgement to make."""

    class LyingPayloads(dict):
        def items(self):  # pragma: no cover - never reached
            raise AssertionError("a supplied mapping must never be iterated here")

    spec = _model("model.payload.v0", EQUITY_DIAL_ID, required=("src.e",))
    with pytest.raises(TypeError):
        compute(spec, LyingPayloads({"src.e": {"figure": 0.9}}))
    with pytest.raises(TypeError):
        compute(spec, {"src.e": ("not", "a", "payload")})  # type: ignore[dict-item]


def test_the_executor_holds_no_module_level_mutable_state():
    """``ASR3-F02``'s mechanism was MEMORY. This module has nowhere to put any.

    Enumerated from the module rather than asserted: every module-level binding that is not
    a function, a class, a module or an immutable is reported by name, so a mutable added
    later arrives with a failing test.
    """
    import __future__
    import types

    import crash_detector.engine.mapping as mapping_module

    immutable = (str, int, float, bool, tuple, frozenset, bytes, type(None))
    # `__future__._Feature` is the compiler directive left behind by
    # `from __future__ import annotations`. It is a frozen marker the interpreter reads at
    # compile time, not state this module can write to, and it is named here rather than
    # swept up by a broader exclusion so the exclusion cannot quietly cover anything else.
    offenders = [
        name
        for name, value in vars(mapping_module).items()
        if not name.startswith("__")
        and not isinstance(value, (types.FunctionType, types.ModuleType, type))
        and not isinstance(value, immutable)
        and not isinstance(value, __future__._Feature)
    ]
    assert offenders == [], (
        f"engine.mapping holds mutable module-level state: {offenders}. The executor must "
        "hold nothing between dials or between runs."
    )


def test_a_declared_parameter_refuses_a_non_finite_value():
    """A NaN compares false against everything including itself; an infinity abolishes
    whatever it bounds. Neither is a configured quantity, and refusing them invents no
    product number (CD-RULE-003)."""
    import math

    for value in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError):
            DeclaredParameter(name="threshold", value=value)
    with pytest.raises(NotEstablishedOnOwnTerms):
        DeclaredParameter(name="threshold", value=1)  # int is not a float


def test_the_shipped_product_registers_no_model_and_no_source():
    """The deliverable, asserted as one statement. CD-D-005 is owed (BLUEPRINT §16)."""
    from crash_detector.source_registry import EMPTY_SOURCE_REGISTRY

    config = empty_config_snapshot("cfg-wo2", staleness_window_seconds=WINDOW_SECONDS)
    assert config.model_registry.models == ()
    assert config.source_registry.sources == ()
    assert config.model_registry is EMPTY_MODEL_REGISTRY
    assert config.source_registry is EMPTY_SOURCE_REGISTRY
    assert all(spec.model_ref is None for spec in config.dial_specs)
