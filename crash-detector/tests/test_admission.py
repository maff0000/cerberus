"""``admits`` — establishment derived from the signature (BP-AMENDMENT-0001 §D.1).

These are the MECHANISM's own tests. The doors it is applied to are tested where they live
(``test_evaluate.py``, ``test_witness_resolver.py``, ``test_dial_presentation.py``,
``test_engine_model_registry.py``), and the class as a class is tested by
``tools/register/check_judgement_path_doors.py``, whose own contrast arms live in
``test_judgement_path_doors.py``.

The tests named as CARRIERS by the DECLARED LIMITs in ``src/crash_detector/admission.py``
are here and are named after the limit they carry, so that CD-RULE-006's "measure the layer
you claim carries the residue" is a grep away:

* limit 1 -> :func:`test_the_established_here_exemptions_are_exactly_this_set` and
  :func:`test_every_established_here_states_a_reason_in_the_artefact`
* limit 2 -> :func:`test_renaming_the_receiver_faults_the_door` and
  :func:`test_a_module_level_parameter_named_cls_is_established_and_not_skipped`
* limit 4 -> :func:`test_a_list_mutated_after_admission_is_not_re_established`

Limit 5 — the six ``ESTABLISHED_HERE`` uses on BP-AMENDMENT-0001 §B.3's already-closed
doors — is carried by ``tests/test_dial_provenance.py``, which is where those doors' own
named refusals are measured, and it is NOT carried here.
"""

from datetime import datetime, timezone

import pytest

from crash_detector.admission import (
    ADMITS_ATTRIBUTE,
    AdmissionFault,
    ESTABLISHED_HERE,
    NotAdmitted,
    UndeclaredParameter,
    admission_faults,
    admits,
    declared_admissions,
    each_of,
    is_admitting_door,
    one_of,
)

WHEN = datetime(2026, 8, 22, 12, 0, 0, tzinfo=timezone.utc)


# --- P7: A NEW PARAMETER ARRIVES REFUSED, NEVER UNGUARDED --------------------------------- #

def test_a_parameter_the_declaration_was_not_told_about_refuses_every_call():
    """PLANT P7's mechanism, in miniature. This is the property that distinguishes
    "establishment derived from the signature" from "four type checks on four named
    functions", and the Product Owner directed the fourth Assurance seat to run it first."""

    @admits(a=int)
    def door(a, added_later=False):
        return a

    # EVERY call, including the one that does not pass the new argument at all.
    with pytest.raises(UndeclaredParameter):
        door(1)
    with pytest.raises(UndeclaredParameter):
        door(1, added_later=True)
    with pytest.raises(UndeclaredParameter):
        door(a=1)


def test_the_refusal_names_the_undeclared_parameter_rather_than_the_door_only():
    @admits(a=int)
    def door(a, added_later=False):
        return a

    with pytest.raises(UndeclaredParameter) as refusal:
        door(1)
    assert "added_later" in str(refusal.value)


def test_an_undeclared_parameter_is_a_fault_computed_at_decoration_from_the_signature():
    """The fault is DERIVED, once, from ``inspect.signature`` — not discovered by watching
    what a caller passes. Nothing about the call is consulted to find it."""

    @admits(a=int)
    def door(a, added_later=False):
        return a

    assert len(admission_faults(door)) == 1
    assert "added_later" in admission_faults(door)[0]


def test_a_declaration_that_names_a_parameter_the_door_does_not_have_also_faults():
    """The other direction. A declaration adrift from its signature is guarding a door that
    is not there, and reading only one direction is how a guard comes to look present."""

    @admits(a=int, gone=str)
    def door(a):
        return a

    with pytest.raises(UndeclaredParameter):
        door(1)


def test_a_variadic_parameter_is_an_open_channel_and_faults_the_door():
    """``*extra`` is the general case of "a parameter it was not told about". This is
    exactly the shape ``_absence_is_never_a_number`` uses deliberately to keep guarding
    across an arity change — which is the right answer for a POST-condition over two fixed
    arguments and the wrong one for a door that must establish everything that arrives."""

    @admits(a=int)
    def positional(a, *extra):
        return a

    @admits(a=int)
    def by_name(a, **extra):
        return a

    with pytest.raises(UndeclaredParameter):
        positional(1)
    with pytest.raises(UndeclaredParameter):
        by_name(1)


def test_a_door_with_no_parameters_still_declares_that_it_has_none():
    """``@admits()`` is not a no-op. It is the statement "I was told about no parameters",
    and it is what makes a door with nothing to establish today still refuse an argument
    added tomorrow."""

    @admits()
    def door():
        return 1

    assert door() == 1
    assert is_admitting_door(door)
    assert admission_faults(door) == ()


# --- EXACT TYPE, NEVER ISINSTANCE --------------------------------------------------------- #

def test_a_subclass_is_refused_and_not_admitted_for_what_it_can_do():
    class SneakyStr(str):
        def __eq__(self, other):
            return True

        def __hash__(self):
            return hash("")

    @admits(name=str)
    def door(name):
        return name

    assert door("plain") == "plain"
    with pytest.raises(NotAdmitted):
        door(SneakyStr("plain"))


def test_a_bool_is_not_a_float_and_is_not_an_int_where_a_float_is_required():
    @admits(seconds=float)
    def door(seconds):
        return seconds

    assert door(600.0) == 600.0
    for offered in (True, 600, "600.0", None):
        with pytest.raises(NotAdmitted):
            door(offered)


def test_one_of_admits_exactly_the_named_types_and_none_is_spelled_none():
    class A:
        pass

    class B:
        pass

    class SubA(A):
        pass

    @admits(v=one_of(A, B, None))
    def door(v):
        return type(v).__name__

    assert door(A()) == "A"
    assert door(B()) == "B"
    assert door(None) == "NoneType"
    with pytest.raises(NotAdmitted):
        door(SubA())


def test_each_of_establishes_the_container_and_every_element():
    class Record:
        pass

    class LooksLikeOne:
        pass

    @admits(rows=each_of(Record))
    def door(rows):
        return len(rows)

    assert door([Record(), Record()]) == 2
    assert door((Record(),)) == 1
    with pytest.raises(NotAdmitted):
        door([Record(), LooksLikeOne()])
    with pytest.raises(NotAdmitted):
        door({Record()})
    with pytest.raises(NotAdmitted):
        door(iter([Record()]))


def test_the_refusal_is_a_typeerror_and_the_fault_is_deliberately_not_one():
    """A caller's ``except TypeError`` must not be able to swallow the refusal of a door
    that has stopped guarding what it claims to guard. *Cannot determine* and *determined
    to be wrong* lead to different actions (Standards Baseline §8)."""

    @admits(a=int)
    def value_refusal(a):
        return a

    @admits(a=int)
    def faulted(a, b=None):
        return a

    assert issubclass(NotAdmitted, TypeError)
    assert not issubclass(UndeclaredParameter, TypeError)
    with pytest.raises(TypeError):
        value_refusal("x")
    try:
        faulted(1)
    except TypeError:  # pragma: no cover - the assertion below is the point
        pytest.fail("a declaration fault must not be catchable as a TypeError")
    except UndeclaredParameter:
        pass


# --- DECLARED LIMIT 2's CARRIER ----------------------------------------------------------- #

def test_renaming_the_receiver_faults_the_door():
    """CD-PL-F74 answered honestly. The receiver is skipped by NAME — ``self`` or ``cls`` —
    and that is a vocabulary. The DIRECTION of the dependence is what makes it safe:
    renaming ``self`` does not open a hole, it faults the door and refuses every call."""

    class Renamed:
        @admits()
        def m(myself):
            return 1

    with pytest.raises(UndeclaredParameter):
        Renamed().m()


def test_the_receiver_is_skipped_only_in_first_position():
    """A parameter named ``self`` anywhere else is an ordinary parameter and must be
    declared, so the skip cannot be used to smuggle one past the declaration."""

    @admits(a=int)
    def door(a, self=None):
        return a

    with pytest.raises(UndeclaredParameter):
        door(1)


def test_a_method_receiver_is_not_established_and_the_rest_of_the_method_is():
    class Door:
        @admits(x=int)
        def m(self, x):
            return x

    assert Door().m(3) == 3
    with pytest.raises(NotAdmitted):
        Door().m("3")


# --- DECLARED LIMIT 4's CARRIER ----------------------------------------------------------- #

def test_a_list_mutated_after_admission_is_not_re_established():
    """Stated as a limit rather than hidden. ``each_of`` walks the container ONCE, at the
    door. A caller holding the same list can replace an element afterwards, and this door
    does not look again."""

    class Record:
        pass

    seen = []

    @admits(rows=each_of(Record))
    def door(rows):
        seen.append(rows)
        return rows

    supplied = [Record()]
    admitted = door(supplied)
    supplied[0] = "not a record at all"
    assert admitted[0] == "not a record at all"
    assert seen[0] is supplied


# --- DECLARATION FAULTS ARE RAISED AT DECORATION, NOT GUESSED AT -------------------------- #

def test_a_declaration_that_is_not_a_type_stops_the_module_importing():
    with pytest.raises(AdmissionFault):

        @admits(a="int")
        def door(a):
            return a


def test_established_here_requires_a_stated_reason():
    with pytest.raises(AdmissionFault):

        @admits(a=ESTABLISHED_HERE)
        def door(a):
            return a

    @admits(a=ESTABLISHED_HERE("this callable IS the establishment door for a"))
    def stated(a):
        return a

    assert stated(object()) is not None


# --- THE DOOR REMAINS THE FUNCTION IT WRAPPED --------------------------------------------- #

def test_an_admitting_door_keeps_its_identity_and_publishes_what_it_requires():
    @admits(a=int, when=datetime)
    def door(a, *, when):
        """A door."""
        return a

    assert door.__name__ == "door"
    assert door.__doc__ == "A door."
    assert sorted(declared_admissions(door)) == ["a", "when"]
    assert hasattr(door, ADMITS_ATTRIBUTE)
    assert door(1, when=WHEN) == 1


def test_defaults_are_established_too_because_a_default_is_a_value_that_arrives():
    """``apply_defaults`` is called before the check. A default that is not of the declared
    type is a value entering the door without a caller — which is exactly the shape of a
    numeric default, and CD-AC-001's oldest failure mode."""

    @admits(a=int)
    def door(a=None):
        return a

    with pytest.raises(NotAdmitted):
        door()


# --- DECLARED LIMIT 2's SECOND CARRIER ---------------------------------------------------- #

def test_a_module_level_parameter_named_cls_is_established_and_not_skipped():
    """The class-body test is asked BEFORE the name. This narrowing exists because the
    mechanism FAULTED `assert_closed_presentation_surface(cls)` — a module-level function
    on the serving path whose only parameter is named `cls` — the first time it was applied
    to it, rather than quietly skipping the only argument that door has."""

    @admits(cls=int)
    def module_shaped(cls):
        return cls

    assert admission_faults(module_shaped) == ()
    assert module_shaped(1) == 1
    with pytest.raises(NotAdmitted):
        module_shaped("1")


def test_a_method_of_a_locally_defined_class_still_skips_its_receiver():
    """`__qualname__` reads `test_....<locals>.Local.m` — the segment before the method is
    the CLASS, not `<locals>`, so the receiver rule applies."""

    class Local:
        @admits(x=int)
        def m(self, x):
            return x

    assert Local().m(1) == 1


# --- DECLARED LIMIT 1's CARRIER: THE EXEMPTION SET IS PINNED ------------------------------ #

#: Every ESTABLISHED_HERE in the product, as (module, callable, parameter). A NINTH use
#: fails this test, which is what makes DECLARED LIMIT 1's "counted, not hidden" a measured
#: claim rather than an intention. `check_judgement_path_doors.py` prints the same set from
#: the SOURCE; this reads it from the RUNTIME, so the two are independent readings of it.
EXPECTED_ESTABLISHED_HERE = frozenset(
    {
        ("crash_detector.engine.model", "own_model_id", "value"),
        ("crash_detector.engine.model", "ModelRegistry.get", "model_id"),
        ("crash_detector.dials.magnitude", "combine_within_one_dial", "using"),
        ("crash_detector.dials.provenance", "observed_for_dial", "dial_id"),
        ("crash_detector.dials.provenance", "observed_for_dial", "quantity"),
        ("crash_detector.dials.provenance", "observed_for_dial", "inputs_used"),
        ("crash_detector.dials.provenance", "derived_within_one_dial", "quantities"),
        ("crash_detector.dials.provenance", "derived_within_one_dial", "reduction"),
    }
)


def _established_here_in_the_product() -> dict:
    """Every ESTABLISHED_HERE reachable in the product, keyed by (module, callable, param).

    Read from the RUNTIME — the compiled declaration objects on the doors themselves.
    ``check_judgement_path_doors.py`` prints the same set read from the SOURCE, so the two
    are independent readings and a disagreement between them is itself informative.
    """
    import importlib
    import pkgutil

    import crash_detector
    from crash_detector.admission import _EstablishedHere

    found: dict = {}
    for info in pkgutil.walk_packages(
        crash_detector.__path__, prefix="crash_detector."
    ):
        module = importlib.import_module(info.name)
        for attribute in list(vars(module).values()):
            candidates = [(attribute, "")]
            if isinstance(attribute, type):
                candidates = [
                    (member, f"{attribute.__name__}.")
                    for member in list(vars(attribute).values())
                ]
            for candidate, prefix in candidates:
                for parameter, admission in declared_admissions(candidate).items():
                    if isinstance(admission, _EstablishedHere):
                        found[
                            (
                                candidate.__module__,
                                prefix + candidate.__name__,
                                parameter,
                            )
                        ] = admission
    return found


def test_the_established_here_exemptions_are_exactly_this_set():
    observed = frozenset(_established_here_in_the_product())
    assert observed == EXPECTED_ESTABLISHED_HERE, (
        "the ESTABLISHED_HERE exemption set moved. Every use is an explicit weakening of "
        "the admission mechanism and must be reviewed, not absorbed. Added: "
        f"{sorted(observed - EXPECTED_ESTABLISHED_HERE)}; removed: "
        f"{sorted(EXPECTED_ESTABLISHED_HERE - observed)}."
    )


def test_every_established_here_states_a_reason_in_the_artefact():
    """A bare ESTABLISHED_HERE cannot reach the product: it raises at decoration. This
    asserts the other half — that every reason actually says something, names the error the
    body raises, and names the test measuring it (CD-RULE-006)."""
    found = _established_here_in_the_product()
    assert len(found) == len(EXPECTED_ESTABLISHED_HERE)
    for where, admission in found.items():
        assert len(admission.because) > 80, f"{where} states no real reason"
        assert "CARRIER MEASURED" in admission.because or "own_terms" in admission.because, (
            f"{where} names no carrier for the residue it leaves (CD-RULE-006)"
        )
