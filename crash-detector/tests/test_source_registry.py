"""The source registry and its criticality contract (BLUEPRINT §5, deliverable A4).

The headline tests are the two that WO-2 actually ships against:
:func:`test_wo2_registers_no_ingredient_source` and the criticality-contract group, which
is the code-side half of the rule that a ``DISPOSABLE`` source can never become
load-bearing. The database-side half is deliverable A5 and is owed.
"""

from __future__ import annotations

import pytest

from crash_detector.source_registry import (
    CRITICALITY_NAMES,
    EMPTY_SOURCE_REGISTRY,
    Criticality,
    CriticalityContractViolated,
    DisposableSourceIsLoadBearing,
    SourceNotRegistered,
    SourceRecord,
    SourceRegistry,
)


def _record(source_id: str, criticality: Criticality) -> SourceRecord:
    return SourceRecord(
        source_id=source_id,
        adapter_id="fake.adapter.v0",
        cadence_seconds=300,
        criticality=criticality,
        stands_for="TEST DOUBLE; WO-2 registers no ingredient source",
    )


# --- THE SHIPPED WO-2 STATE ------------------------------------------------------------ #

def test_wo2_registers_no_ingredient_source():
    """CD-D-005 is the Product Owner's and is owed before WO-3 (BLUEPRINT §16).

    An Engineer seat populating this would be choosing what a dial MEANS.
    """
    assert EMPTY_SOURCE_REGISTRY.is_empty
    assert EMPTY_SOURCE_REGISTRY.sources == ()
    assert EMPTY_SOURCE_REGISTRY.source_ids == ()


def test_the_empty_registry_admits_no_input_at_any_criticality():
    """The empty state is not merely empty; it actively refuses every named input."""
    for asserter in (
        EMPTY_SOURCE_REGISTRY.assert_may_be_required,
        EMPTY_SOURCE_REGISTRY.assert_may_be_contributing,
        EMPTY_SOURCE_REGISTRY.assert_registered,
    ):
        with pytest.raises(SourceNotRegistered):
            asserter(("src.anything",))


# --- THE CRITICALITY CONTRACT ----------------------------------------------------------- #

def test_criticality_has_exactly_three_members_matching_the_blueprint_table():
    assert CRITICALITY_NAMES == ("REQUIRED", "CONTRIBUTING", "DISPOSABLE")
    assert tuple(member.value for member in Criticality) == CRITICALITY_NAMES


def test_a_disposable_source_may_never_be_required():
    """BLUEPRINT §5, named explicitly in the dispatch. The A5 SQL must mirror this."""
    registry = SourceRegistry(sources=(_record("src.d", Criticality.DISPOSABLE),))
    with pytest.raises(DisposableSourceIsLoadBearing):
        registry.assert_may_be_required(("src.d",))


def test_a_disposable_source_may_never_be_contributing_either():
    """"Its absence changes nothing" and "its absence forces Degraded" cannot both hold.

    The dispatch names the required-input case. This is the same proposition through the
    other set: a guard that caught only the named instance would be caught out by an
    author who moved the source one field to the left.
    """
    registry = SourceRegistry(sources=(_record("src.d", Criticality.DISPOSABLE),))
    with pytest.raises(DisposableSourceIsLoadBearing):
        registry.assert_may_be_contributing(("src.d",))


def test_disposable_violations_are_catchable_as_the_general_contract_class():
    registry = SourceRegistry(sources=(_record("src.d", Criticality.DISPOSABLE),))
    with pytest.raises(CriticalityContractViolated):
        registry.assert_may_be_required(("src.d",))
    assert issubclass(DisposableSourceIsLoadBearing, CriticalityContractViolated)


@pytest.mark.parametrize(
    "criticality,asserter_name",
    [
        (Criticality.CONTRIBUTING, "assert_may_be_required"),
        (Criticality.REQUIRED, "assert_may_be_contributing"),
    ],
)
def test_a_criticality_that_disagrees_with_its_set_is_refused(criticality, asserter_name):
    """The whole Blueprint table, not just the DISPOSABLE row.

    Promoting a CONTRIBUTING source into a required set changes its absence from
    ``Degraded`` to ``Unknown`` without changing the registry row that declares what its
    absence does — a silent disagreement between two places that must agree.
    """
    registry = SourceRegistry(sources=(_record("src.x", criticality),))
    with pytest.raises(CriticalityContractViolated):
        getattr(registry, asserter_name)(("src.x",))


def test_each_criticality_is_accepted_in_its_own_set():
    """The contract refuses disagreement; it does not refuse everything."""
    registry = SourceRegistry(
        sources=(
            _record("src.r", Criticality.REQUIRED),
            _record("src.c", Criticality.CONTRIBUTING),
            _record("src.d", Criticality.DISPOSABLE),
        )
    )
    registry.assert_may_be_required(("src.r",))
    registry.assert_may_be_contributing(("src.c",))
    assert registry.ids_with(Criticality.DISPOSABLE) == ("src.d",)


def test_an_unregistered_source_is_refused_before_any_criticality_is_read():
    """Otherwise the DISPOSABLE prohibition is vacuous.

    You would evade it by simply not registering the source you are about to make
    load-bearing, which is less work than registering it wrongly.
    """
    registry = SourceRegistry(sources=(_record("src.r", Criticality.REQUIRED),))
    with pytest.raises(SourceNotRegistered):
        registry.assert_may_be_required(("src.never.registered",))


# --- SourceRecord ------------------------------------------------------------------------ #

@pytest.mark.parametrize("field_name", ["source_id", "adapter_id", "stands_for"])
def test_a_record_refuses_an_empty_required_string(field_name):
    kwargs = dict(
        source_id="src.a",
        adapter_id="a.v0",
        cadence_seconds=60,
        criticality=Criticality.REQUIRED,
        stands_for="what it stands for",
    )
    kwargs[field_name] = ""
    with pytest.raises(ValueError):
        SourceRecord(**kwargs)


def test_criticality_must_be_the_enum_and_not_its_string():
    """A string is not a criticality; it is a criticality that has not been checked."""
    with pytest.raises(TypeError):
        SourceRecord(
            source_id="src.a",
            adapter_id="a.v0",
            cadence_seconds=60,
            criticality="DISPOSABLE",  # type: ignore[arg-type]
            stands_for="x",
        )


@pytest.mark.parametrize("cadence", [0, -1])
def test_a_non_positive_cadence_is_not_a_schedule(cadence):
    with pytest.raises(ValueError):
        _replace_cadence(cadence)


def test_a_boolean_cadence_is_refused_because_bools_are_ints_in_python():
    with pytest.raises(TypeError):
        _replace_cadence(True)


def _replace_cadence(cadence):
    return SourceRecord(
        source_id="src.a",
        adapter_id="a.v0",
        cadence_seconds=cadence,
        criticality=Criticality.REQUIRED,
        stands_for="x",
    )


# --- SourceRegistry ----------------------------------------------------------------------- #

def test_two_rows_for_one_source_is_two_criticalities_for_one_source():
    with pytest.raises(ValueError):
        SourceRegistry(
            sources=(
                _record("src.a", Criticality.REQUIRED),
                _record("src.a", Criticality.DISPOSABLE),
            )
        )


def test_the_registry_holds_only_source_records():
    with pytest.raises(TypeError):
        SourceRegistry(sources=("src.a",))  # type: ignore[arg-type]


def test_get_has_no_default_and_raises_for_an_unregistered_source():
    registry = SourceRegistry(sources=(_record("src.a", Criticality.REQUIRED),))
    assert registry.get("src.a").criticality is Criticality.REQUIRED
    with pytest.raises(SourceNotRegistered):
        registry.get("src.b")


def test_the_registry_is_frozen_so_a_snapshot_cannot_be_edited_after_the_fact():
    registry = SourceRegistry(sources=(_record("src.a", Criticality.REQUIRED),))
    with pytest.raises(Exception):
        registry.sources = ()  # type: ignore[misc]


def test_an_iterable_of_records_is_normalised_to_a_tuple():
    registry = SourceRegistry(sources=[_record("src.a", Criticality.REQUIRED)])
    assert isinstance(registry.sources, tuple)
