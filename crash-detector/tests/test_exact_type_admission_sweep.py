"""THE F01 EXACT-TYPE SWEEP — the carrier for WO-2R3 increment 10, ITEM_1.

``PO-DECISIONS-0018`` ruling 2, verbatim: *"EXACT TYPE, everywhere on a judgement path where
an `isinstance` still survives — sites enumerated BY INSTRUMENT, the forged-subclass probe as
the plant, both arms."*

**WHAT THIS FILE DOES AND DOES NOT ASSERT.**

It asserts, for each of the TWELVE tier-1 admission sites converted from ``isinstance`` to
exact type at increment 10, that **an object which satisfied the old predicate is REFUSED by
the new one** — and, beside it, that the honest value the product actually uses is still
admitted. A refusal with no contrast is indistinguishable from a probe that never ran
(``CD-D-079``), so every refusal here has its control on the next line.

It does **NOT** assert that ``CD-ASR-F01`` is closed, that the forged type is prevented, or
that any class is sealed. The forged subclass is STILL CONSTRUCTIBLE — the platform permits
it and this increment does not claim otherwise. What it claims is that the judgement paths
enumerated by ``tools/sweep/delegated_judgement_sweep.py`` refuse the instance, because
admission is by exact type.

**THE DENOMINATOR IS THE INSTRUMENT'S AND NOT THIS FILE'S.** ``ISINSTANCE 30`` at
``686a374``; ``ISINSTANCE 18`` after this increment; twelve converted, and the twelve are
enumerated in ``test_the_converted_sites_are_exactly_these_twelve`` from the RUNTIME
behaviour rather than from a source grep.
"""

from __future__ import annotations

import datetime as dt

import pytest

from crash_detector.admission import (
    AdmissionFault,
    ESTABLISHED_HERE,
    NotAdmitted,
    admits,
    each_of,
    _Exactly,
    declared_admissions,
)
from crash_detector.dials.magnitude import DialMagnitude
from crash_detector.dials.provenance import (
    CrossDialCombination,
    DeclaredQuantity,
    observed_for_dial,
)
from crash_detector.dials.reading import (
    READING_CONSTRUCTORS,
    ReadingSurfaceViolated,
    SealedReadingType,
    seal_reading_type,
)
from crash_detector.observations import FetchFailed, Malformed
from crash_detector.source_registry import Criticality, SourceRecord, SourceRegistry


# --------------------------------------------------------------------------------------- #
# THE PROBES. Each is the OLD predicate's counterexample: something `isinstance` admits and
# `type(x) is T` refuses. Two shapes, because `isinstance` has TWO routes and this project's
# record only ever named one of them.
#
#   (1) A SUBCLASS.        The route the register's dispositions name.
#   (2) `__class__`.       CPython's `object_isinstance` falls back to the instance's
#                          `__class__` attribute, which is an ordinary property a caller can
#                          define. **A CLASS THAT CANNOT BE SUBCLASSED CAN STILL BE WORN.**
# --------------------------------------------------------------------------------------- #


def wearing(cls):
    """An object of an UNRELATED type whose ``__class__`` property answers ``cls``."""

    class Forged:
        @property
        def __class__(self):
            return cls

    return Forged()


class LyingStr(str):
    def strip(self, *a):
        return "x"

    def startswith(self, *a):
        return True

    def __len__(self):
        return 1


class LyingInt(int):
    def __le__(self, other):
        return False


class LyingFrozenset(frozenset):
    def __iter__(self):
        return iter(("forged-dial",))


class LyingTuple(tuple):
    def __iter__(self):
        return iter((float,))


class LyingAdmission(_Exactly):
    """Admits everything and reports that it does not."""

    __slots__ = ()

    def refusal(self, parameter, value):
        return None

    def describe(self):
        return "exactly PanelRow"


def test_isinstance_has_two_routes_and_the_second_needs_no_subclass():
    """**THE PREMISE THE WHOLE SWEEP RESTS ON, ASSERTED AND NOT ASSUMED.**

    Several of this project's declared dispositions read *"CPython refuses to subclass it, so
    isinstance and exact type coincide here"*. They do not coincide. ``isinstance`` consults
    ``__class__`` as well as ``type()``, so a class that cannot be SUBCLASSED can still be
    WORN by an object of an entirely unrelated type.
    """
    with pytest.raises(TypeError, match="cannot extend"):
        exec("class EvilCrit(Criticality): pass", {"Criticality": Criticality})
    with pytest.raises(TypeError, match="not an acceptable base type"):
        exec("class EvilBool(bool): pass", {})

    for victim in (Criticality, bool, str, int, float, frozenset, dt.datetime):
        forged = wearing(victim)
        assert isinstance(forged, victim), victim
        assert type(forged) is not victim, victim


# --------------------------------------------------------------------------------------- #
# crash_detector.admission — the six DEFECT_OPEN sites, four of which are converted.
# --------------------------------------------------------------------------------------- #


def test_established_here_refuses_a_str_subclass_that_lies_about_being_blank():
    """``_EstablishedHere.__call__`` — was ``isinstance(because, str)``.

    The old predicate admitted a ``str`` subclass whose ``strip`` says it is not blank while
    the object IS the empty string, and the artefact then carried an exemption with NO stated
    reason — through the one guard that exists to stop exactly that.
    """
    blank_but_says_otherwise = LyingStr("")
    assert isinstance(blank_but_says_otherwise, str)
    assert blank_but_says_otherwise.strip() == "x"      # the old predicate's whole basis

    with pytest.raises(AdmissionFault) as refused:
        ESTABLISHED_HERE(blank_but_says_otherwise)
    assert "requires a stated reason" in str(refused.value)

    # CONTROL — an honest exact `str` is still the way to state a reason.
    assert ESTABLISHED_HERE("a real reason").describe().endswith("(a real reason)")


def test_compile_refuses_an_admission_subclass_that_admits_everything():
    """``_compile`` — was ``isinstance(declaration, _Admission)``.

    MEASURED at ``686a374``: this declaration was ACCEPTED, the door reported
    ``faults: ()``, ``describe()`` said ``'exactly PanelRow'``, and the body ran on an
    ``object()``. The module header has said *"Three forms, and no fourth"* since it was
    written; the code now enforces the set instead of the docstring claiming it.
    """
    liar = LyingAdmission((int,))
    assert isinstance(liar, _Exactly)                   # the old predicate is satisfied

    with pytest.raises(AdmissionFault) as refused:
        @admits(value=liar)
        def a_door(value):  # pragma: no cover - never decorated
            return value
    assert "no fourth form" in str(refused.value)

    # CONTROL — the three declared forms still compile.
    @admits(value=int)
    def by_type(value):
        return value

    assert by_type(1) == 1
    assert declared_admissions(by_type)["value"].describe() == "int"


def test_compile_refuses_a_tuple_subclass_whose_iteration_disagrees_with_itself():
    """``_compile`` — was ``isinstance(declaration, tuple)``.

    MEASURED at ``686a374``: ``repr`` said ``(<class 'int'>,)``, ``len`` said ``1``, and the
    door ENFORCED ``float``. The source read one type and the door required another.
    """
    liar = LyingTuple((int,))
    assert isinstance(liar, tuple)
    assert repr(liar) == "(<class 'int'>,)" and len(liar) == 1
    assert [t.__name__ for t in liar] == ["float"]      # what it actually yields

    with pytest.raises(AdmissionFault):
        @admits(value=liar)
        def a_door(value):  # pragma: no cover - never decorated
            return value

    # CONTROL — an exact tuple of types is still a declaration.
    @admits(value=(int, float))
    def honest(value):
        return value

    assert honest(1.5) == 1.5
    with pytest.raises(NotAdmitted):
        honest("no")


def test_each_of_refuses_a_tuple_subclass_as_its_container_set():
    """``each_of`` — was ``isinstance(within, tuple)``."""
    with pytest.raises(AdmissionFault):
        each_of(int, within=LyingTuple((list,)))

    # CONTROL — the declared default and an explicit exact tuple both still work.
    assert each_of(int).describe().startswith("tuple or list")
    assert each_of(int, within=(tuple,)).describe().startswith("tuple")


# --------------------------------------------------------------------------------------- #
# crash_detector.observations
# --------------------------------------------------------------------------------------- #


def test_fetch_failed_refuses_an_int_subclass_status():
    """``FetchFailed.__post_init__`` — was ``isinstance(status, int)``."""
    with pytest.raises(TypeError) as refused:
        FetchFailed(error_class="Timeout", http_status=LyingInt(404))
    assert "must be an int or absent" in str(refused.value)

    with pytest.raises(TypeError):
        FetchFailed(error_class="Timeout", http_status=wearing(int))

    # CONTROL — an exact int and an absent status.
    assert FetchFailed(error_class="Timeout", http_status=404).http_status == 404
    assert FetchFailed(error_class="Timeout").http_status is None


def test_malformed_refuses_a_str_subclass_before_it_can_answer_startswith():
    """``Malformed.__post_init__`` — was ``isinstance(self.instance_path, str)``.

    The old predicate admitted the subclass, and the RFC 6901 shape check and the length
    ceiling immediately below were then ITS ``startswith`` and ITS ``__len__`` to answer. The
    type refusal now fires first, so neither is ever asked.
    """
    liar = LyingStr("this is not a json pointer")
    assert isinstance(liar, str) and liar.startswith("/")   # it lies, and convincingly

    with pytest.raises(TypeError) as refused:
        Malformed(schema_error_class="required", instance_path=liar)
    assert "must be a str" in str(refused.value)

    # CONTROL — the document root and an honest pointer.
    assert Malformed(schema_error_class="required").instance_path == ""
    assert Malformed(schema_error_class="required", instance_path="/a").instance_path == "/a"


# --------------------------------------------------------------------------------------- #
# crash_detector.source_registry — including the site that was a LIVE admission.
# --------------------------------------------------------------------------------------- #


def _record(**overrides):
    fields = dict(
        source_id="s1",
        adapter_id="a1",
        stands_for="a thing",
        criticality=Criticality.REQUIRED,
        cadence_seconds=60,
    )
    fields.update(overrides)
    return SourceRecord(**fields)


def test_source_record_refuses_a_worn_criticality():
    """``SourceRecord.__post_init__`` — was ``isinstance(self.criticality, Criticality)``.

    **THE REFUSAL IDENTITY IS PINNED AND THE FIRST DRAFT OF THIS TEST DID NOT PIN IT.**
    Raised against this seat's own work as ``CD-ENG-WO2R3-08-F04``: written as
    ``pytest.raises((TypeError, Exception))`` with ``"criticality" in str(...)``, it PASSED
    AT THE BASE SHA ``686a374`` — where this site still admitted the forgery and it was
    ``@establishes``' ``FieldNotEstablished`` one layer down that refused it, with the word
    ``criticality`` in its message too. **A TEST THAT PASSES ON BOTH ARMS IS NOT A CONTRAST,
    AND IT WAS FOUND BY RUNNING THIS FILE AGAINST THE BASE TREE RATHER THAN BY READING IT.**
    ``FieldNotEstablished`` IS a ``TypeError`` subclass, so only the message distinguishes
    them, and now it does.
    """
    with pytest.raises(TypeError, match="must be a Criticality member") as refused:
        _record(criticality=wearing(Criticality))
    # and it is THIS door's refusal, not the field boundary's one layer down.
    assert type(refused.value) is TypeError, (
        "the forgery was refused, but by "
        f"{type(refused.value).__name__} — a layer below the site this test is about."
    )

    # CONTROL — a real member.
    assert _record().criticality is Criticality.REQUIRED


def test_ids_with_refuses_a_worn_criticality_and_this_site_was_a_live_admission():
    """``SourceRegistry.ids_with`` — was ``isinstance(criticality, Criticality)``.

    **MEASURED AT ``686a374``: THIS SITE ADMITTED THE FORGERY AND ANSWERED ``()``** — "no
    sources at this criticality" — with no refusal anywhere. A caller asking which sources
    are REQUIRED was told none, and a required-inputs check over an empty tuple passes
    vacuously. The declared disposition for the site was ``EXACT`` on the ground that
    ``Criticality`` cannot be subclassed. It cannot; it did not need to be.
    """
    registry = SourceRegistry(sources=(_record(),))

    with pytest.raises(TypeError) as refused:
        registry.ids_with(wearing(Criticality))
    assert "Criticality member" in str(refused.value)

    # CONTROLS — the real member answers, and an obviously wrong type still refuses.
    assert registry.ids_with(Criticality.REQUIRED) == ("s1",)
    assert registry.ids_with(Criticality.DISPOSABLE) == ()
    with pytest.raises(TypeError):
        registry.ids_with("REQUIRED")


def test_source_record_refuses_an_int_subclass_cadence():
    """``SourceRecord.__post_init__`` — was ``isinstance(self.cadence_seconds, int)``.

    The disposition was ``DELEGATED``: *"An int SUBCLASS passes, and ``self.cadence_seconds
    <= 0`` immediately below is then its ``__le__`` to answer, so a subclass could register a
    non-positive cadence."* Here is that subclass, and here is it refused.
    """
    sneaky = LyingInt(-5)
    assert isinstance(sneaky, int) and not (sneaky <= 0)    # its own `__le__` lies

    with pytest.raises(TypeError) as refused:
        _record(cadence_seconds=sneaky)
    assert "must be an int" in str(refused.value)

    # CONTROLS — an honest positive cadence is admitted; an honest negative one is refused
    # by the check the subclass was steering.
    assert _record(cadence_seconds=60).cadence_seconds == 60
    with pytest.raises(ValueError):
        _record(cadence_seconds=-5)
    # AND the bool limb is UNCHANGED and still `isinstance` — the stricter operator here.
    with pytest.raises(TypeError):
        _record(cadence_seconds=True)


# --------------------------------------------------------------------------------------- #
# crash_detector.dials — the two frozenset sites and the sealing admission.
# --------------------------------------------------------------------------------------- #


def _quantity():
    return observed_for_dial(dial_id="d1", quantity=1.0, inputs_used=("i1",))


def test_declared_quantity_refuses_a_frozenset_subclass_provenance():
    """``dials.provenance::_install`` — was ``isinstance(dials, frozenset)``.

    `_install` is reached through `__setstate__`, which is the revival path a hand-written
    pickle takes; the public doors refuse a direct construction for a different and older
    reason (`QuantityProvenanceMissing`) that would mask this one.
    """
    liar = LyingFrozenset({"d1"})
    assert isinstance(liar, frozenset)

    honest = _quantity()
    state = honest.__getstate__()
    assert type(state["dials"]) is frozenset

    forged = DeclaredQuantity.__new__(DeclaredQuantity)
    with pytest.raises(CrossDialCombination) as refused:
        forged.__setstate__({**state, "dials": liar})
    assert "LyingFrozenset" in str(refused.value)

    # CONTROL — the real state revives.
    revived = DeclaredQuantity.__new__(DeclaredQuantity)
    revived.__setstate__(state)
    assert revived == honest


def test_magnitude_setstate_refuses_a_frozenset_subclass_provenance():
    """``dials.magnitude::DialMagnitude.__setstate__`` — was ``isinstance(provenance,
    frozenset)``.

    MEASURED at ``686a374``: the subclass reached ``_install`` and was refused THERE, by a
    message about DIALS, for a fault that is about TYPES. Right outcome, wrong layer.
    """
    honest = DialMagnitude(dial_id="d1", quantity=_quantity())
    state = honest.__getstate__()
    assert type(state["provenance"]) is frozenset

    forged = DialMagnitude.__new__(DialMagnitude)
    with pytest.raises(CrossDialCombination) as refused:
        forged.__setstate__({**state, "provenance": LyingFrozenset({"d1"})})
    assert "cannot be revived" in str(refused.value)

    # CONTROL — the real state round-trips.
    revived = DialMagnitude.__new__(DialMagnitude)
    revived.__setstate__(state)
    assert revived == honest


def test_seal_reading_type_refuses_a_metatype_subclass():
    """``dials.reading::seal_reading_type`` — was ``isinstance(cls, SealedReadingType)``.

    An ADMISSION predicate: pass it and the class is RECORDED AS SEALED. A metatype SUBCLASS
    supplies its own ``__setattr__`` and ``__delattr__`` — the two members sealing is made of
    — so under ``isinstance`` a class closed by SOMEBODY ELSE'S code was recorded as sealed
    by this one.
    """
    sub = type("SealedReadingTypeSub", (SealedReadingType,), {})
    impostor = type.__new__(sub, "Impostor", (), {"__slots__": ()})
    assert isinstance(impostor, SealedReadingType)
    assert type(impostor) is not SealedReadingType

    with pytest.raises(ReadingSurfaceViolated) as refused:
        seal_reading_type(impostor)
    assert "not built by SealedReadingType" in str(refused.value)

    # CONTROL — the three real constructors pass it, which is what import does.
    for constructor in READING_CONSTRUCTORS:
        assert seal_reading_type(constructor) is constructor


# --------------------------------------------------------------------------------------- #
# THE DENOMINATOR ITSELF.
# --------------------------------------------------------------------------------------- #


def test_the_converted_sites_are_exactly_these_twelve():
    """**THE SET, NOT THE NUMBER** — the lesson DECLARED LIMIT 1 of ``admission`` records.

    Each entry is a callable that MUST refuse its probe. If a conversion is reverted, the
    entry stops raising and this test names which one. It reads runtime behaviour, never
    source text, so a re-spelling cannot satisfy it.
    """
    registry = SourceRegistry(sources=(_record(),))
    honest_state = DialMagnitude(dial_id="d1", quantity=_quantity()).__getstate__()
    sub = type("SealedReadingTypeSub", (SealedReadingType,), {})

    def _decorate_with(declaration):
        @admits(value=declaration)
        def a_door(value):  # pragma: no cover - never decorated
            return value

    converted = {
        "admission::_EstablishedHere.__call__": lambda: ESTABLISHED_HERE(LyingStr("")),
        "admission::_compile _Admission": lambda: _decorate_with(LyingAdmission((int,))),
        "admission::_compile tuple": lambda: _decorate_with(LyingTuple((int,))),
        "admission::each_of within": lambda: each_of(int, within=LyingTuple((list,))),
        "observations::FetchFailed.http_status": lambda: FetchFailed(
            error_class="x", http_status=LyingInt(404)
        ),
        "observations::Malformed.instance_path": lambda: Malformed(
            schema_error_class="x", instance_path=LyingStr("nope")
        ),
        "source_registry::SourceRecord.criticality": lambda: _record(
            criticality=wearing(Criticality)
        ),
        "source_registry::SourceRecord.cadence_seconds": lambda: _record(
            cadence_seconds=LyingInt(-5)
        ),
        "source_registry::SourceRegistry.ids_with": lambda: registry.ids_with(
            wearing(Criticality)
        ),
        "dials.provenance::_install": lambda: DeclaredQuantity.__new__(
            DeclaredQuantity
        ).__setstate__(
            {**_quantity().__getstate__(), "dials": LyingFrozenset({"d1"})}
        ),
        "dials.magnitude::__setstate__": lambda: DialMagnitude.__new__(
            DialMagnitude
        ).__setstate__({**honest_state, "provenance": LyingFrozenset({"d1"})}),
        "dials.reading::seal_reading_type": lambda: seal_reading_type(
            type.__new__(sub, "Impostor", (), {"__slots__": ()})
        ),
    }

    assert len(converted) == 12

    admitted = []
    for name, probe in converted.items():
        try:
            probe()
        except Exception:
            continue
        admitted.append(name)

    assert admitted == [], (
        "these converted sites ADMITTED an object that only `isinstance` accepts, which "
        "means the exact-type conversion was reverted or bypassed at: " + ", ".join(admitted)
    )


# --------------------------------------------------------------------------------------- #
# THE EIGHTEEN THAT WERE **NOT** CONVERTED. A DECLARED REASON WITH NO CARRIER IS A SENTENCE
# (CD-RULE-006), AND THESE TWO TESTS ARE THE CARRIERS FOR THE TWO REASONS THAT DO THE WORK.
# --------------------------------------------------------------------------------------- #


def test_the_four_metatype_guards_keep_isinstance_because_exact_type_would_ADMIT():
    """**THE MECHANICAL READING OF "EXACT TYPE EVERYWHERE" IS WRONG AT FOUR SITES.**

    ``SealedMagnitudeType.__new__`` and its three siblings are **REFUSAL** predicates —
    ``if isinstance(base, M): raise`` — and at a refusal predicate the WIDER operator is the
    STRICTER one. Converting them to ``type(base) is M`` would refuse STRICTLY LESS.

    This test builds the thing that separates the two predicates: a class whose METATYPE is a
    SUBCLASS of the sealed metatype, forged over the sealed victim. Today an ordinary ``class``
    statement over it is REFUSED. Under exact type it would be ADMITTED, and that is asserted
    here as a property of the predicate rather than argued in a comment.

    **PO-DECISIONS-0018 ruling 1(a) keeps these refusals as accident-proofing. Converting them
    would have been the regression the ruling was written to forbid.**
    """
    from crash_detector.dials.magnitude import (
        DialMagnitude, MagnitudeSurfaceViolated, SealedMagnitudeType,
    )
    from crash_detector.dials.provenance import (
        DeclaredQuantity, QuantitySurfaceViolated, SealedQuantityType,
    )
    from crash_detector.dials.reading import Degraded  # noqa: F811
    from crash_detector.dials.reading import ReadingSurfaceViolated  # noqa: F811
    from crash_detector.serving.dial_presentation import (
        DialPresentationRefused, NotShown, SealedPresentationType,
    )

    cases = (
        (SealedMagnitudeType, DialMagnitude, MagnitudeSurfaceViolated),
        (SealedQuantityType, DeclaredQuantity, QuantitySurfaceViolated),
        (SealedReadingType, Degraded, ReadingSurfaceViolated),
        (SealedPresentationType, NotShown, DialPresentationRefused),
    )
    assert len(cases) == 4

    for metatype, victim, surface_error in cases:
        sub = type(f"{metatype.__name__}Sub", (metatype,), {})
        forged = type.__new__(sub, "Forged", (victim,), {"__slots__": ()})

        # THE TWO PREDICATES DISAGREE AT THIS BASE. That is the whole of the argument.
        assert isinstance(forged, metatype) is True, metatype
        assert (type(forged) is metatype) is False, metatype

        # TODAY, with `isinstance`: an ordinary class statement over the forged base REFUSES.
        with pytest.raises(surface_error):
            exec("class Child(B):\n    __slots__ = ()\n", {"B": forged})

        # AND THE PREDICATE THE CONVERSION WOULD INSTALL, EVALUATED OVER THE SAME BASES:
        # it does not fire, so the class statement would SUCCEED.
        assert any(type(b) is metatype for b in (forged,)) is False, (
            f"{metatype.__name__}: the exact-type predicate would REFUSE this base, so the "
            "reason recorded at that site for keeping `isinstance` no longer holds and the "
            "site should be re-examined."
        )


def test_the_own_terms_isinstance_doors_are_carried_by_the_base_type_descriptor():
    """**THE CARRIER FOR THE SIX SHAPE-ADMITTING DOORS, AND IT IS THE C LAYER.**

    ``own_float``, ``own_str``, ``own_instant``, ``own_utc_offset``, ``ensure_utc`` and
    ``parse_utc`` admit a SUBCLASS on purpose — ``numpy.float64`` IS a ``float`` and
    ``pandas.Timestamp`` IS a ``datetime``, and a measurement path that refused them would be
    broken rather than safe. So exact type is not available and the sites are DECLARED.

    What that leaves open is the route ``isinstance`` has and SUBCLASSING does not: an object
    of an unrelated type WEARING the class through ``__class__``. **IT DOES NOT SURVIVE THE
    NEXT LINE**, because every one of these doors immediately applies an UNBOUND BASE-TYPE
    DESCRIPTOR, and CPython refuses to apply a descriptor to anything that is not a genuine
    instance of its owning type. The refusing layer is named from its own failure text.
    """
    from crash_detector.own_terms import own_float, own_instant, own_str, own_utc_offset
    from crash_detector.time_utc import ensure_utc, parse_utc

    cases = (
        ("own_float", float, lambda v: own_float(v), "'float' object"),
        ("own_str", str, lambda v: own_str(v), "requires a 'str' object"),
        ("own_instant", dt.datetime,
         lambda v: own_instant(v, offset=dt.timedelta(0)), "doesn't apply to a 'Forged'"),
        ("own_utc_offset", dt.datetime, lambda v: own_utc_offset(v), "'datetime.datetime'"),
        ("ensure_utc", dt.datetime, lambda v: ensure_utc(v), "'datetime.datetime'"),
        ("parse_utc", str, lambda v: parse_utc(v), "requires a 'str' object"),
    )
    assert len(cases) == 6

    for name, victim, call, expected_in_text in cases:
        forged = wearing(victim)
        # THE PREMISE: `isinstance` is satisfied and no subclass was needed.
        assert isinstance(forged, victim) is True, name
        assert (type(forged) is victim) is False, name

        with pytest.raises(TypeError) as refused:
            call(forged)
        assert "descriptor" in str(refused.value), (
            f"{name}: the forgery was refused, but NOT by the base-type descriptor this "
            f"site's declared reason names — {str(refused.value)[:160]}"
        )
        assert expected_in_text in str(refused.value), (
            f"{name}: {str(refused.value)[:160]}"
        )

    # CONTROLS — a GENUINE subclass is the case these doors exist to serve, and it is
    # admitted, and what comes back is EXACT type built by this package.
    class RealFloat(float):
        def __float__(self):
            return 999.0

    class RealStr(str):
        def __eq__(self, other):
            return True

        def __hash__(self):
            return 0

    assert own_float(RealFloat(1.5)) == 1.5 and type(own_float(RealFloat(1.5))) is float
    assert type(own_str(RealStr("x"))) is str and str.__eq__(own_str(RealStr("x")), "x")
