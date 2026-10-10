"""``WitnessPanel`` — ``Unavailable`` is a distinct constructor (CD-AC-005).

PID §6: ``WITNESS UNAVAILABLE`` is not ``WITNESS AGREES``. These tests check the type
cannot express the confusion, and that there is no field on ``Unavailable`` a later edit
could default into a measurement.
"""

from __future__ import annotations

import dataclasses
import math

import pytest

from crash_detector.witness.panel import (
    PANEL_CONSTRUCTORS,
    PANEL_STATES,
    UNAVAILABLE_REASONS,
    Agrees,
    AgreementWithoutFreshnessEvidence,
    Diverges,
    Unavailable,
    panel_state,
)

from conftest import FIXED_NOW, freshness_for

AGREES = Agrees(
    divergence_measure=0.02, as_of_utc=FIXED_NOW, freshness=freshness_for()
)
DIVERGES = Diverges(divergence_measure=0.9, threshold=0.5, as_of_utc=FIXED_NOW)
UNAVAILABLE = Unavailable(reason="PANEL_ROW_ABSENT", since_utc=FIXED_NOW)


def test_the_sum_type_has_exactly_three_constructors():
    assert PANEL_CONSTRUCTORS == (Agrees, Diverges, Unavailable)
    assert PANEL_STATES == ("AGREES", "DIVERGES", "UNAVAILABLE")


def test_the_three_constructors_share_no_ancestor_but_object():
    """A shared base is where a `.divergence_measure` could be added for all three."""
    mros = [set(c.__mro__) for c in PANEL_CONSTRUCTORS]
    assert set.intersection(*mros) == {object}


def test_unavailable_is_not_agrees_and_cannot_be_mistaken_for_it():
    assert type(UNAVAILABLE) is not type(AGREES)
    assert not isinstance(UNAVAILABLE, Agrees)
    assert UNAVAILABLE != AGREES


def test_unavailable_carries_no_measurement_of_any_kind():
    """There is nothing on this type a rendering layer could read as agreement."""
    names = {f.name for f in dataclasses.fields(Unavailable)}
    assert names == {"reason", "since_utc"}
    assert not hasattr(UNAVAILABLE, "divergence_measure")
    assert not hasattr(UNAVAILABLE, "threshold")


def test_no_panel_constructor_has_a_default_for_any_field():
    """No default. A default is where absence acquires a value nobody chose."""
    for constructor in PANEL_CONSTRUCTORS:
        for field in dataclasses.fields(constructor):
            assert field.default is dataclasses.MISSING, (constructor, field.name)
            assert field.default_factory is dataclasses.MISSING, (constructor, field.name)


def test_agrees_cannot_be_constructed_without_a_measurement():
    """Reaching AGREES requires a measurement, and there is no way round that."""
    with pytest.raises(TypeError):
        Agrees(as_of_utc=FIXED_NOW)  # type: ignore[call-arg]


@pytest.mark.parametrize("bad", [None, "0.0", 0, True, math.nan, math.inf])
def test_agrees_refuses_a_measurement_that_is_not_a_finite_float(bad):
    """Refused, not coerced. `float("0.0")` and `float(True)` both produce a divergence
    measure that reads as agreement, manufactured out of a type error."""
    with pytest.raises((TypeError, ValueError)):
        Agrees(
            divergence_measure=bad, as_of_utc=FIXED_NOW, freshness=freshness_for()
        )


@pytest.mark.parametrize("bad", [None, "0.5", 1, True, math.nan, math.inf])
def test_diverges_refuses_a_threshold_that_is_not_a_finite_float(bad):
    with pytest.raises((TypeError, ValueError)):
        Diverges(divergence_measure=0.9, threshold=bad, as_of_utc=FIXED_NOW)


def test_all_three_constructors_are_frozen():
    for constructor in PANEL_CONSTRUCTORS:
        assert constructor.__dataclass_params__.frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        UNAVAILABLE.reason = "PANEL_ROW_STALE"  # type: ignore[misc]


def test_unavailable_requires_a_stated_reason():
    with pytest.raises(ValueError):
        Unavailable(reason="", since_utc=FIXED_NOW)


def test_unavailable_requires_a_reason_from_the_declared_set():
    """Every route to unavailability is named, so a new route cannot be added without
    declaring it — which is what stops "we do not know why" being a silent reason."""
    with pytest.raises(ValueError):
        Unavailable(reason="BECAUSE", since_utc=FIXED_NOW)


@pytest.mark.parametrize("reason", UNAVAILABLE_REASONS)
def test_every_declared_reason_is_constructible(reason):
    assert Unavailable(reason=reason, since_utc=FIXED_NOW).reason == reason


def test_no_declared_reason_resembles_agreement():
    for reason in UNAVAILABLE_REASONS:
        assert "AGREE" not in reason.upper()


@pytest.mark.parametrize(
    ("panel", "expected"),
    [(AGREES, "AGREES"), (DIVERGES, "DIVERGES"), (UNAVAILABLE, "UNAVAILABLE")],
)
def test_panel_state_maps_each_constructor_to_its_own_discriminator(panel, expected):
    assert panel_state(panel) == expected


def test_panel_state_refuses_a_look_alike_rather_than_defaulting_it_to_agrees():
    """The variant an attacker reaches for: something that quacks like agreement."""

    class LooksLikeAgrees:
        divergence_measure = 0.0
        as_of_utc = FIXED_NOW

    with pytest.raises(TypeError):
        panel_state(LooksLikeAgrees())  # type: ignore[arg-type]


def test_a_subclass_of_unavailable_is_still_not_agrees():
    """Subclassing is the other way a look-alike arrives. It must not become AGREES."""

    class SneakyUnavailable(Unavailable):
        pass

    sneaky = SneakyUnavailable(reason="PANEL_ROW_ABSENT", since_utc=FIXED_NOW)
    with pytest.raises(TypeError):
        panel_state(sneaky)


def test_every_constructor_refuses_a_naive_timestamp():
    from datetime import datetime

    from crash_detector.time_utc import NaiveTimestampRejected

    naive = datetime(2026, 8, 19, 12, 0, 0)
    with pytest.raises(NaiveTimestampRejected):
        Agrees(
            divergence_measure=0.1, as_of_utc=naive, freshness=freshness_for()
        )
    with pytest.raises(NaiveTimestampRejected):
        Diverges(divergence_measure=0.9, threshold=0.5, as_of_utc=naive)
    with pytest.raises(NaiveTimestampRejected):
        Unavailable(reason="PANEL_ROW_ABSENT", since_utc=naive)


# --- CD-ASR-F06: agreement requires positive evidence of freshness ------------------------- #

def test_agrees_cannot_be_constructed_without_freshness_evidence():
    """The field is required and has no default. Absence is a TypeError from Python."""
    with pytest.raises(TypeError):
        Agrees(divergence_measure=0.02, as_of_utc=FIXED_NOW)  # type: ignore[call-arg]


def test_no_panel_constructor_gained_a_default_when_freshness_was_added():
    """A default on `freshness` would have re-opened the whole finding in one line."""
    for field in dataclasses.fields(Agrees):
        assert field.default is dataclasses.MISSING, field.name
        assert field.default_factory is dataclasses.MISSING, field.name


def test_agrees_declares_exactly_three_fields():
    """Asserted by EQUALITY. A fourth field is where an override would go."""
    assert {f.name for f in dataclasses.fields(Agrees)} == {
        "divergence_measure",
        "as_of_utc",
        "freshness",
    }


def test_agrees_refuses_a_look_alike_that_is_not_freshness_evidence():
    """The variant an author reaches for: something that quacks like evidence.

    Duck typing here would be the whole defect back again — anyone could declare an
    observation fresh by writing an object with the right attribute names.
    """

    class LooksLikeFreshness:
        as_of_utc = FIXED_NOW
        observed_at_utc = FIXED_NOW
        age_seconds = 0.0

    with pytest.raises(AgreementWithoutFreshnessEvidence):
        Agrees(
            divergence_measure=0.02,
            as_of_utc=FIXED_NOW,
            freshness=LooksLikeFreshness(),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("bad", [None, 0.0, "fresh", True, {}])
def test_agrees_refuses_anything_that_is_not_freshness_evidence(bad):
    with pytest.raises(AgreementWithoutFreshnessEvidence):
        Agrees(divergence_measure=0.02, as_of_utc=FIXED_NOW, freshness=bad)


def test_agrees_refuses_evidence_about_a_different_observation():
    """Borrowing a fresh observation's evidence for a stale one is the obvious evasion of
    a freshness requirement, and it is closed by binding the two instants together."""
    from conftest import ago

    with pytest.raises(AgreementWithoutFreshnessEvidence):
        Agrees(
            divergence_measure=0.02,
            as_of_utc=ago(300),
            freshness=freshness_for(),  # evidence about FIXED_NOW, not about ago(300)
        )


def test_a_decade_old_observation_cannot_produce_agrees_by_direct_construction():
    """CD-ASR-F06's row, attacked at the TYPE rather than through the resolver.

    There is no window under which the evidence can be made, so there is no argument list
    that constructs this value. That is what "structurally incapable" means.
    """
    from crash_detector.staleness import FreshnessNotEstablished, StalenessWindow
    from conftest import ago

    ten_years = 3650 * 24 * 3600.0
    for window_seconds in (1.0, 60.0, 600.0, 900.0):
        with pytest.raises(FreshnessNotEstablished):
            Agrees(
                divergence_measure=0.02,
                as_of_utc=ago(ten_years),
                freshness=freshness_for(
                    ago(ten_years), window_seconds=window_seconds
                ),
            )
        # and the window that would have made it fresh cannot be built either
        with pytest.raises(ValueError):
            StalenessWindow(seconds=ten_years)
