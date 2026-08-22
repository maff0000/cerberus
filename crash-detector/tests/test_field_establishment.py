"""The RUNTIME evidence for ``crash_detector.establishment``.

``tools/register/check_constructor_field_establishment.py`` PARSES. It proves nothing about
runtime behaviour, and every escape on this project's record passed a static checker. These
tests import the product and CONSTRUCT the real types, which is the only way a claim like
"a new field arrives refused" can be evidence rather than a rumour.

They are the Engineer's tests and they are part of the implementation. **They are not
assurance and they do not become assurance by being thorough** (``PBG-SOD-001``,
non-waivable).

Two of them are named in ``DECLARED LIMIT`` clauses as the MEASURED CARRIER of a residue,
and one diffs the STATIC population against the RUNTIME population so the two independent
readings of the same class have to agree.
"""

from __future__ import annotations

import dataclasses
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

import pytest

from crash_detector.admission import AdmissionFault
from crash_detector.establishment import (
    ESTABLISHED_HERE,
    EstablishmentFault,
    FieldNotEstablished,
    UndeclaredField,
    declared_establishment,
    establishes,
    establishment_faults,
    establishment_field_list,
    governed_types,
    is_establishing_type,
    one_of,
)
from crash_detector.engine.config import ConfigSnapshot, DialSpec
from crash_detector.engine.model import EMPTY_MODEL_REGISTRY
from crash_detector.serving.witness_resolver import PanelRow
from crash_detector.source_registry import EMPTY_SOURCE_REGISTRY

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_CHECK = _REPO_ROOT / "tools" / "register" / "check_constructor_field_establishment.py"

NOW = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)


def _import_the_whole_product():
    """Import EVERY module under ``crash_detector``, derived by walking the package.

    The registry only knows about types whose module has been imported, so a runtime
    reading taken from a partial import would be a partial reading that LOOKS complete.
    The walk is derived from the package, never a list of module names: a module written
    tomorrow is imported here the day it is written.
    """
    import importlib
    import pkgutil

    import crash_detector

    for module in pkgutil.walk_packages(
        crash_detector.__path__, prefix="crash_detector."
    ):
        importlib.import_module(module.name)


def _product_types():
    """The governed types that are PRODUCT types.

    ``governed_types()`` is a process-global registry, and the throwaway classes these
    tests build to exercise the mechanism land in it too. They are filtered out HERE, in
    the test, and never inside the mechanism: a registry that decided for itself which of
    its entries counted would be deciding what it is evidence about.
    """
    _import_the_whole_product()
    return tuple(
        cls
        for cls in governed_types()
        if cls.__module__.startswith("crash_detector.")
        and "<locals>" not in cls.__qualname__
    )


# ---------------------------------------------------------------------------------------- #
# THE MECHANISM ITSELF
# ---------------------------------------------------------------------------------------- #


def _governed(**declared):
    """Build a throwaway governed dataclass, exactly as the product declares one."""

    def build(cls):
        return establishes(**declared)(dataclasses.dataclass(frozen=True)(cls))

    return build


def test_a_declared_field_of_the_wrong_exact_type_is_refused_at_the_boundary():
    @_governed(name=str)
    class Governed:
        name: str

    assert Governed(name="ok").name == "ok"
    with pytest.raises(FieldNotEstablished) as refusal:
        Governed(name=1)
    assert "Governed.name" in str(refusal.value)


def test_a_subclass_of_the_declared_type_is_refused_because_exact_and_never_isinstance():
    class Sneaky(str):
        def __eq__(self, other):  # the caller's code, inside this system's judgement
            return True

        def __hash__(self):
            return hash("")

    @_governed(name=str)
    class Governed:
        name: str

    with pytest.raises(FieldNotEstablished):
        Governed(name=Sneaky("anything"))


def test_a_new_field_the_declaration_was_not_told_about_refuses_EVERY_construction():
    """P7 at the constructor. The construction below does not mention the new field."""

    @_governed(name=str)
    class Governed:
        name: str
        added_later: int = 0

    assert establishment_faults(Governed)
    with pytest.raises(UndeclaredField) as refusal:
        Governed(name="ok")
    assert "added_later" in str(refusal.value)
    assert "arrives REFUSED, never unguarded" in str(refusal.value)


def test_a_declaration_adrift_from_the_field_list_refuses_every_construction():
    @_governed(name=str, gone=int)
    class Governed:
        name: str

    with pytest.raises(UndeclaredField) as refusal:
        Governed(name="ok")
    assert "gone" in str(refusal.value)


def test_an_initvar_faults_the_type_rather_than_being_silently_ignored():
    """DECLARED LIMIT: an InitVar is never an attribute, so it cannot be established."""

    @establishes(name=str)
    @dataclasses.dataclass(frozen=True)
    class Governed:
        name: str
        seed: dataclasses.InitVar[int] = 0

        def __post_init__(self, seed):
            pass

    assert any("InitVar" in fault for fault in establishment_faults(Governed))
    with pytest.raises(UndeclaredField):
        Governed(name="ok")


def test_applying_the_decorator_to_a_non_dataclass_is_a_fault_at_decoration():
    with pytest.raises(EstablishmentFault) as refusal:
        @establishes(name=str)
        class NotADataclass:
            pass
    assert "not a dataclass" in str(refusal.value)


def test_a_bare_established_here_is_a_fault_at_decoration_and_must_state_its_reason():
    with pytest.raises(AdmissionFault):
        @_governed(name=ESTABLISHED_HERE)
        class Governed:
            name: str


def test_the_boundary_establishes_what_the_body_left_behind_and_not_what_was_offered():
    """The check runs AFTER __init__, so canonicalisation is what gets established."""

    @_governed(seconds=float)
    class Governed:
        seconds: float

        def __post_init__(self):
            object.__setattr__(self, "seconds", float(self.seconds))

    assert Governed(seconds=600).seconds == 600.0          # int canonicalised: ADMITTED

    @_governed(seconds=float)
    class Rewriting:
        seconds: float

        def __post_init__(self):
            object.__setattr__(self, "seconds", "not a number")

    with pytest.raises(FieldNotEstablished):
        Rewriting(seconds=1.0)                             # body rewrote it: REFUSED


def test_a_governed_type_publishes_no_way_round_its_own_boundary():
    """DECLARED LIMIT 3's measured half: ``__wrapped__`` is deleted, as ``admits`` does.

    What is NOT closed is the closure cells and the module registry, which is the rest of
    DECLARED LIMIT 3 and is stated there rather than tested away here.
    """
    assert not hasattr(PanelRow.__init__, "__wrapped__")
    assert not hasattr(ConfigSnapshot.__init__, "__wrapped__")


def test_the_declaration_is_held_off_the_class_so_no_declared_surface_is_widened():
    """CD-ASR-F02's layer-1 closure asserts ``frozenset(vars(cls))`` by set EQUALITY.

    Five members of this class seal themselves that way. A class attribute here would break
    them, which is why the registry is a module dict and not an ``__establishes__``.
    """
    from crash_detector.dials.reading import (
        DECLARED_MEMBER_SURFACE,
        Degraded,
        Unknown,
        Value,
        assert_closed_surface,
    )
    from crash_detector.serving.dial_presentation import (
        NotShown,
        Shown,
        assert_closed_presentation_surface,
    )

    for constructor in (Value, Degraded, Unknown):
        assert is_establishing_type(constructor)
        assert_closed_surface(constructor)
        assert frozenset(vars(constructor)) - DECLARED_MEMBER_SURFACE[
            constructor.__name__
        ] <= frozenset(
            {
                "__getstate__",
                "__setstate__",
                "__replace__",
                "__weakref__",
                "__firstlineno__",
                "__static_attributes__",
            }
        )
    for constructor in (Shown, NotShown):
        assert is_establishing_type(constructor)
        assert_closed_presentation_surface(constructor)


def test_the_refusal_survives_renaming_every_identifier_in_the_declaration():
    """CD-PL-F74's rename test, applied to this mechanism's own refusal.

    The refusal comes from ``type(value) is not declared`` over a list read from
    ``dataclasses.fields``. Nothing in it is a spelling, so renaming the class, the field
    and the declared type changes nothing about whether it bites.
    """

    @_governed(alpha=str)
    class First:
        alpha: str

    @_governed(zeta_omega=str)
    class SecondNamedNothingLikeTheFirst:
        zeta_omega: str

    with pytest.raises(FieldNotEstablished):
        First(alpha=1)
    with pytest.raises(FieldNotEstablished):
        SecondNamedNothingLikeTheFirst(zeta_omega=1)


# ---------------------------------------------------------------------------------------- #
# THE CLASS — the runtime population against the static one
# ---------------------------------------------------------------------------------------- #


def test_every_governed_type_declares_exactly_its_own_declared_field_list():
    """In BOTH directions, for every member, read from ``dataclasses.fields`` at runtime."""
    assert _product_types(), "no type is governed; the mechanism is not applied at all"
    for cls in _product_types():
        declared = set(declared_establishment(cls))
        fields = {field.name for field in dataclasses.fields(cls)}
        assert declared == fields, cls.__qualname__
        assert set(establishment_field_list(cls)) == fields, cls.__qualname__
        assert establishment_faults(cls) == (), cls.__qualname__


_VACUOUS_MARKER = "  IN — SATISFIED VACUOUSLY: "


def _static_population() -> tuple[set, set]:
    """The check's OWN two printed sets: FIELDED (required) and ZERO-FIELD (vacuous).

    Read out of the run rather than recomputed here, so this is a reading OF THE INSTRUMENT
    and not a second implementation of it.
    """
    completed = subprocess.run(
        [sys.executable, "-B", str(_CHECK), "--root", str(_REPO_ROOT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    fielded = set()
    vacuous = set()
    for line in completed.stdout.splitlines():
        if "  IN [" in line:
            fielded.add(line.rsplit(" — ", 2)[0].split()[-1])
        elif _VACUOUS_MARKER in line:
            vacuous.add(line.split(_VACUOUS_MARKER, 1)[1].split()[1])
    return fielded, vacuous


def test_the_static_enumeration_and_the_runtime_population_are_the_same_class():
    """Two INDEPENDENT readings of one class, diffed as SETS and never compared as counts.

    The check parses the source and never imports it; ``governed_types()`` is the decorator
    reporting what it actually decorated at import. Identical counts have hidden a swap on
    this project before, so the sets are diffed.

    **SINCE PO-DECISIONS-0010 RULING 1 THE STATIC POPULATION HAS TWO PARTS**, and only the
    FIELDED part is REQUIRED to carry ``@establishes``.

    **ONE CLAUSE OF THIS TEST IS REVERSED AT WO-2R3 INCREMENT 6, AND IT IS A REVERSAL AND NOT
    A RELAXATION. THE SUPERSEDED CLAUSE IS QUOTED RATHER THAN DELETED (PBG-CONT-003):**

        assert vacuous & runtime == set(), sorted(vacuous & runtime)

    with the reasoning that went with it: *"The ZERO-FIELD part satisfies VACUOUSLY, so it is
    diffed in the OTHER direction — it must be DISJOINT from the runtime governed set."*

    **THAT CLAUSE ASSERTED THE ABSENCE OF A GUARD.** It required the vacuous member to be
    runtime-UNGOVERNED, and `CD-ASR-WO2R3-01`'s F-A1 is the finding that it therefore WAS:
    add a field to `Empty` and the instrument exited 1 while `Empty(confidence=object())` was
    ACCEPTED at runtime. `PO-DECISIONS-0011` ruling 1 item (d) ordered `@establishes()`
    applied to `Empty`, which makes the old clause false BY DESIGN.

    The replacement requires MORE of the system, not less: **every member the static reading
    enumerates — fielded OR vacuous — is governed at runtime, and nothing is governed at
    runtime that the static reading does not enumerate.** Satisfying vacuously is still not
    the same as being fielded; it is no longer the same as being unguarded.
    """
    fielded, vacuous = _static_population()
    runtime = {cls.__name__ for cls in _product_types()}
    assert fielded, "the check printed no fielded population"
    assert vacuous, "the check printed no vacuous population"
    assert fielded <= runtime, {
        "fielded in the static reading only": sorted(fielded - runtime),
    }
    assert vacuous <= runtime, {
        "vacuous in the static reading only, i.e. RUNTIME-UNGOVERNED": sorted(vacuous - runtime),
    }
    assert fielded | vacuous == runtime, {
        "in the static reading only": sorted((fielded | vacuous) - runtime),
        "in the runtime reading only": sorted(runtime - (fielded | vacuous)),
    }


def test_the_vacuously_satisfying_members_are_exactly_this_set():
    """CHECK LIMIT 1 residue (i)'s MEASURED CARRIER (CD-RULE-006).

    A member declaring ZERO FIELDS satisfies the widened rule vacuously. The set is PINNED BY
    NAME — a SECOND zero-field judgement-path type is a test failure and not a quiet widening
    of the vacuous branch — and each member's emptiness is re-measured AT RUNTIME from
    ``dataclasses.fields``, so a field ARRIVING on one of them fails here as well as in the
    check.

    Written out rather than computed, for the reason
    ``test_the_established_here_field_exemptions_are_exactly_this_set`` gives: a set derived
    from observation declares whatever it finds, including whatever somebody added.

    **THE SECOND ASSERTION IS REVERSED AT WO-2R3 INCREMENT 6. THE SUPERSEDED WORDING IS QUOTED
    RATHER THAN DELETED (PBG-CONT-003):**

        assert not is_establishing_type(cls), (
            f"{cls.__qualname__} is governed at runtime but the check reads it as "
            "satisfying vacuously — the two readings disagree")

    together with the sentence that justified it: *"carries no boundary of any kind. That is a
    residue, not a closure."*

    **THAT ASSERTION PINNED THE DEFECT IN PLACE.** It made "this type has no runtime boundary"
    a REQUIREMENT, so applying the decorator the mechanism's own docstring prescribes would
    have failed the suite. `CD-ASR-WO2R3-01` F-A1 measured what it cost: `Empty` + one field
    gave static exit 1 and runtime ***ACCEPTED***. `PO-DECISIONS-0011` ruling 1 item (d)
    ordered the decorator applied, and the assertion is now its opposite: **a vacuously
    satisfying member IS governed at runtime, so that the day it gains a field, every
    construction of it raises rather than one instrument printing a line.**
    """
    from crash_detector.observations import Empty

    expected = {Empty}

    _fielded, vacuous = _static_population()
    assert vacuous == {cls.__name__ for cls in expected}, sorted(vacuous)

    for cls in expected:
        assert dataclasses.fields(cls) == (), cls.__qualname__
        assert is_establishing_type(cls), (
            f"{cls.__qualname__} satisfies the rule VACUOUSLY and must still be GOVERNED AT "
            "RUNTIME. Without @establishes() a field added to it is a static check line "
            "only, which is exactly CD-ASR-WO2R3-01's F-A1"
        )


def test_a_nullary_governed_type_refuses_every_construction_the_day_it_gains_a_field():
    """**THE MECHANISM PROPERTY `Empty` NOW RELIES ON, ASSERTED ON ITS OWN.**

    `test_a_new_field_the_declaration_was_not_told_about_refuses_EVERY_construction` covers
    the FIELDED case: a type that declared `name=str` and grew a second field. **THE NULLARY
    CASE WAS NEVER ASSERTED**, and it is the one `PO-DECISIONS-0011` ruling 1 item (d) turns
    on — `@establishes()` with NO declarations, on a type with NO fields, so that a field
    added later refuses every construction.

    Both halves are here, because only the pair is a property: the nullary governed type
    constructs exactly as it did before, AND the same type with one field added refuses
    `EVERY` construction — including the nullary spelling that worked a moment ago.

    This asserts the MECHANISM. That `Empty` itself is wired to it is asserted by
    `test_the_vacuously_satisfying_members_are_exactly_this_set`, and the end-to-end contrast
    against the real module at both SHAs is
    `variants/WO-2R3/P-D-empty-is-runtime-unguarded.py`. Three readings, deliberately not one.
    """

    @_governed()
    class NullaryAndStaysThatWay:
        pass

    assert not establishment_faults(NullaryAndStaysThatWay)
    assert is_establishing_type(NullaryAndStaysThatWay)
    assert dataclasses.fields(NullaryAndStaysThatWay) == ()
    NullaryAndStaysThatWay()  # unchanged, and this is half the property

    @_governed()
    class NullaryUntilSomebodyAddedAField:
        confidence: object = None

    assert establishment_faults(NullaryUntilSomebodyAddedAField)
    with pytest.raises(UndeclaredField) as refusal:
        NullaryUntilSomebodyAddedAField()
    assert "confidence" in str(refusal.value)
    with pytest.raises(UndeclaredField):
        NullaryUntilSomebodyAddedAField(confidence=object())


def test_the_established_here_field_exemptions_are_exactly_this_set():
    """DECLARED LIMIT 2's measured carrier. A FOURTH exemption is a test failure.

    Written out rather than computed, for the reason ``DECLARED_MEMBER_SURFACE`` gives: a
    set derived from observation declares whatever it finds, including whatever somebody
    added.
    """
    from crash_detector.collectors.adapter import FetchedResponse
    from crash_detector.dials.reading import Degraded, Value

    expected = {
        (FetchedResponse, "payload"),
        (Value, "value"),
        (Degraded, "value"),
    }
    observed = {
        (cls, field)
        for cls in _product_types()
        for field, admission in declared_establishment(cls).items()
        if type(admission).__name__ == "_EstablishedHere"
    }
    assert observed == expected


# ---------------------------------------------------------------------------------------- #
# THE FLOOR THE PRODUCT OWNER NAMED — five of the thirty-two, each constructed and refused
# ---------------------------------------------------------------------------------------- #


def test_the_five_types_the_product_owner_named_are_all_governed():
    from crash_detector.collectors.attempt import AttemptRecord
    from crash_detector.engine.model import ModelSpec

    for cls in (ConfigSnapshot, DialSpec, ModelSpec, PanelRow, AttemptRecord):
        assert is_establishing_type(cls), cls.__qualname__


def test_a_duck_dialspec_is_refused_and_the_BODY_is_what_refuses_it_while_it_exists():
    """READ THE FAILURE TEXT. THE LAYER THAT REFUSES HERE IS THE BODY, NOT THE BOUNDARY.

    This is recorded as a test rather than left implicit, because it is the ordering cost
    ``establishment.py``'s header declares: the boundary establishes AFTER the generated
    ``__init__``, so while ``ConfigSnapshot.__post_init__``'s own
    ``type(spec) is not DialSpec`` loop exists, THAT loop raises first and the boundary is
    never reached. Anyone reading an exit code alone would credit this refusal to the wrong
    layer, which is exactly ``CD-ENG-WO2R3-F12``, this seat's own finding against its own
    increment-4 work.

    The proposition increment 5 exists to prove is what happens when that body is DELETED,
    and it cannot be proved from inside this suite because the body is present here. It is
    proved by ``variants/WO-2R3/V17-constructor-body-escape.patch`` plus
    ``V35-v17-companion-probe.patch`` in a pristine extraction, and its violated arm by
    ``V40-v17-violated-arm-establishes-removed.patch``.
    """

    class DuckDialSpec:
        dial_id = "equity_crash"
        required_input_ids = ()
        contributing_input_ids = ()
        model_ref = None

    with pytest.raises(TypeError) as refusal:
        ConfigSnapshot(
            config_snapshot_id="probe",
            dial_specs=(DuckDialSpec(), DuckDialSpec()),
            staleness_window_seconds=600.0,
            source_registry=EMPTY_SOURCE_REGISTRY,
            model_registry=EMPTY_MODEL_REGISTRY,
        )
    assert str(refusal.value) == "ConfigSnapshot.dial_specs must all be DialSpec"
    assert not isinstance(refusal.value, FieldNotEstablished)


def test_the_boundary_refuses_a_duck_element_where_no_body_check_can_reach_it_first():
    """The same proposition on a governed type whose body checks NOTHING about the field.

    ``ScoreComputation.__post_init__`` only calls ``tuple()`` on ``contributions``; it
    establishes no element type at all. So a wrong-typed element here can only be refused
    by the BOUNDARY, and the refusal's identity says which layer refused it.
    """
    from crash_detector.engine.model import ScoreComputation

    with pytest.raises(FieldNotEstablished) as refusal:
        ScoreComputation(magnitude=0.5, contributions=(object(),))
    assert "ScoreComputation.contributions[0]=object" in str(refusal.value)


def test_one_of_and_each_of_are_the_same_vocabulary_the_doors_use():
    """One declaration vocabulary, not two. Two that drift apart is how a reader comes to
    believe a field is established as strictly as a parameter when it is not."""
    from crash_detector import admission

    assert one_of is admission.one_of
    assert ESTABLISHED_HERE is admission.ESTABLISHED_HERE
