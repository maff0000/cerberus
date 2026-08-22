"""``establishes`` — ESTABLISHMENT DERIVED FROM THE DECLARED FIELD LIST.

    @establishes(dial_specs=each_of(DialSpec, within=(tuple,)), source_registry=SourceRegistry, ...)
    @dataclass(frozen=True)
    class ConfigSnapshot: ...

This is :mod:`crash_detector.admission`'s idea ONE LEVEL DOWN, and the sentence it
implements is transcribed rather than paraphrased (CD-D-110, PO-DECISIONS-0007 ruling 1):

    "the ``admits`` idea one level down — establishment derived from the DECLARED FIELD
     LIST, refusing what it was not told, applied at the boundary so a body edit cannot
     remove it."

====================================================================================
WHY THIS EXISTS: ``__post_init__`` IS A BODY
====================================================================================

BP-AMENDMENT-0001 §D.1's principle is *establishment derived from the declaration, never
written into an editable body*. ``admits`` applies it to the parameters of a CALLABLE.
Every frozen value type on this project's judgement path established its FIELDS in
``__post_init__``, which is a body, and §D.2's table lists no constructor — so increment 2
correctly did not close them and correctly DECLARED the gap instead. The Product Owner
ruled on that declaration:

    "``__post_init__`` IS A BODY."   — PO-DECISIONS-0007 ruling 1 (CD-D-105, answer (A))

and then ruled its own ruling beaten before the work started, because that ruling named
four types and a fifth was found within hours:

    "AN ENUMERATION CANNOT CLOSE A PROPERTY-DEFINED CLASS — this estate's most expensive
     lesson, and I applied it to the kernel while writing a list into my own ruling."
                                    — PO-DECISIONS-0008 ruling 2 (CD-D-114)

So the subject of this module is not five types. It is a CLASS defined by a property, the
class is enumerated from the artefact by
``tools/register/check_constructor_field_establishment.py``, and that instrument was
written and run BEFORE this module existed so its population could not be a photograph of
this module's diff.

THE ESCAPE THIS SHAPE EXISTS TO PREVENT, AND IT IS THE THIRD OF ITS KIND HERE. CD-ASR-F03
was an edit to ``_evaluate_dial``'s BODY. The fourth argument
``_absence_is_never_a_number`` is deliberately written with ``*extra`` to survive is the
same shape from the other side. ``variants/WO-2R3/V17-constructor-body-escape.patch`` is
the third: it deletes the ``type(spec) is not DialSpec`` loop from
``ConfigSnapshot.__post_init__``, and at WO-2R3 increment 4 the whole judgement-path doors
instrument STILL EXITED 0 with it applied. **A rule that lives in a body is removed by
editing the body.** So the rule is applied HERE, at the class boundary, and it is derived
from ``dataclasses.fields(cls)`` — the class's own DECLARED FIELD LIST — rather than from
anything a body says.

====================================================================================
THE THREE THINGS THIS BOUNDARY REFUSES, AND THE SECOND IS THE ONE THAT MATTERS
====================================================================================

**1. A FIELD WHOSE ESTABLISHED VALUE IS OF THE WRONG EXACT TYPE** — ``type(value) is not
declared``, never ``isinstance``, for the same reason ``admits`` gives: a subclass may
shadow any attribute with a property, and a property is the caller's code running inside
this system's judgement at the moment the judgement is made. The refusal is
:exc:`FieldNotEstablished`, a ``TypeError``.

**2. A FIELD THE DECLARATION WAS NOT TOLD ABOUT** — in BOTH directions, and this refusal
fires **ON EVERY CONSTRUCTION**, whether or not the caller passes the new field. The field
list is read from ``dataclasses.fields`` at decoration; if it and the declaration disagree
either way the TYPE is FAULTED, and every construction raises :exc:`UndeclaredField`.
**A NEW FIELD ADDED TO A GOVERNED TYPE ARRIVES REFUSED, NEVER UNGUARDED.** This is planted
violation P7 one level down, and it is what makes this a closure of a class rather than
thirty-two type checks.

It fires on every construction rather than at import for the reason ``admits`` states: an
import-time refusal is one event in one process at one moment, and a construction-time
refusal is re-derived at every single entry, so no amount of import ordering, lazy loading,
reload or ``importlib`` cleverness gets a construction past it. The fault itself is still
computed once, from the field list, at decoration — derived statically, enforced
dynamically.

**3. AN ``InitVar``** — a pseudo-field that reaches ``__init__`` and is never an attribute,
so its established value cannot be read back after construction and this mechanism cannot
establish it. A type that needs one is not a type this mechanism can close, and it FAULTS
rather than admitting it. **There are ZERO ``InitVar``s in the subject set today and the
static check PRINTS the count it observed**, so the premise is measured at every run rather
than assumed. This is the "report the conflict, do not weaken the rule" instruction of the
increment-5 dispatch, discharged in code.

====================================================================================
WHERE THE CHECK RUNS, AND WHY IT IS **AFTER** THE GENERATED ``__init__`` AND NOT BEFORE
====================================================================================

The wrapper calls the dataclass-generated ``__init__`` — which assigns the fields and then
calls ``__post_init__`` — and establishes the fields **from the object's own attributes
afterwards**. That ordering is a design decision with three measured reasons and one
disclosed cost.

*Reason 1 — what the object HOLDS is what must be established.* Almost every
``__post_init__`` in this codebase CANONICALISES: ``own_str``, ``ensure_utc``,
``tuple(...)``, ``dict(...)``, ``float(...)``. A check on the ARGUMENTS would establish a
value the object does not hold, and would refuse ``StalenessWindow(seconds=600)`` — an
``int`` the body legitimately turns into a ``float`` — which is a closure that forbids the
product.

*Reason 2 — it reaches fields no argument carries.* ``field(init=False)`` fields and
``field(default_factory=...)`` fields never appear as a bound argument in a form this
mechanism could read (the factory sentinel is not the value). Read as attributes, they are
established like every other field. There are zero of each in the subject set today; the
static check prints the counts, and the mechanism does not depend on their absence.

*Reason 3 — it catches the body rewriting a field to something else.* A ``__post_init__``
that assigns a wrong-typed value through ``object.__setattr__`` is refused, because what is
established is the final state and not the offered one.

**THE COST, STATED RATHER THAN LEFT TO BE FOUND: ``__post_init__`` RUNS FIRST.** If a body
raises before the boundary is reached, the refusal a caller sees is the BODY's and not this
one's — so a plant against this mechanism must be constructed to reach it, and a plant that
merely exits non-zero has proved nothing about which layer refused it
(``CD-ENG-WO2R3-F12``, this seat's own finding against its own increment-4 work). What the
ordering does NOT cost is the closure: no object escapes the constructor, because the
exception propagates out of ``__init__`` and the caller never receives a reference.

====================================================================================
WHY THE DECLARATION IS HELD IN A MODULE REGISTRY AND **NOT** AS A CLASS ATTRIBUTE
====================================================================================

``admits`` sets ``__admits__`` on the door. This mechanism sets NOTHING on the class, and
that is not a stylistic difference — it is forced by the artefact and it is an improvement
on ``admits``, and both halves are stated:

*Forced.* :data:`crash_detector.dials.reading.DECLARED_MEMBER_SURFACE` and
:data:`crash_detector.serving.dial_presentation.DECLARED_PRESENTATION_SURFACE` declare the
COMPLETE attribute surface of ``Value``, ``Degraded``, ``Unknown``, ``Shown`` and
``NotShown``, asserted by SET EQUALITY at import against ``frozenset(vars(cls))``, with an
independent copy of each table in the tests. **Adding any class attribute to those five
would break CD-ASR-F02's layer-1 closure.** Five of the thirty-two members of this class
are sealed that way. Replacing ``__init__`` does not disturb the surface, because
``__init__`` is already in it.

*An improvement.* ``CD-ENG-WO2R3-F13`` is this seat's own finding that ``admits``'s
introspection surface LIES after ``variants/WO-2R3/V33-closure-declaration-rewrite.patch``:
``__admits__`` is a copy taken at decoration, so a door whose live declaration has been
rewritten still reports the original. The note in ``admission.py`` says making the
attribute the live object would "hand a mutator a documented, supported handle instead of
an interpreter-internal one, which is a WORSE trade". **A module-level registry publishes
no handle on the class at all.** It is not a closure of V33's route — see DECLARED LIMIT 3
— and it is not claimed as one.

====================================================================================
DECLARED LIMIT (CD-RULE-004), in this header, the register entry and the execution
contract, each with an executable example. CD-RULE-006: each hand-off names a layer
MEASURED to carry it, or says NOT PROVED TO BE CARRIED ANYWHERE.
====================================================================================

 1  **THIS MECHANISM ESTABLISHES A FIELD'S TYPE AND NEVER A RELATION BETWEEN TWO FIELDS.**
    BP-AMENDMENT-0001 §C.5's invariants 2 and 3 — a resolved ``ModelSpec``'s ``dial_id``
    EQUALS the dial naming it; its input ids are a SUBSET of the naming ``DialSpec``'s
    declared inputs — are CROSS-FIELD invariants. **A cross-field invariant cannot be
    derived from a declared field list**: the field list says what each field IS, and says
    nothing about what any two of them must be to each other. The same is true of
    ``ConfigSnapshot``'s "exactly one spec per dial", ``AttemptRecord``'s
    ``requested_utc <= observation.observed_utc``, ``CollectionResult``'s
    ``rows_recorded == attempts_made``, ``Agrees``'s
    ``freshness.as_of_utc == self.as_of_utc``, and every uniqueness check in a registry.
    **THEY REMAIN BODY-BORNE AND THIS MECHANISM DOES NOT COVER THEM.** They are listed
    rather than left to be discovered because they shared a body with the fields.
    Executable example: ``variants/WO-2R3/V36-cross-field-invariant-body-rewrite.patch``
    deletes ``ConfigSnapshot.__post_init__``'s "exactly one spec per dial" check and
    constructs a snapshot carrying two equity specs and no monetary spec — **ACCEPTED**,
    with every field of it exactly typed and this boundary satisfied.
    **CARRIER MEASURED, AND IT IS A BODY-LEVEL CARRIER:**
    ``tests/test_engine_config.py`` and ``tests/test_engine_model_registry.py`` measure
    those bodies refusing TODAY, and V36's arm measures that they stop refusing when the
    body is edited. As a STRUCTURE that survives an edit to those bodies:
    **NOT PROVED TO BE CARRIED ANYWHERE.** RAISED AS A FINDING (``CD-ENG-WO2R3-F18``) to
    the Project Lead rather than closed here: closing it needs a way to derive a RELATION
    from a declaration, which is a design question and not a reconciliation.

 2  **``ESTABLISHED_HERE`` IS AN EXPLICIT WEAKENING AND IT IS COUNTED, NOT HIDDEN.** THREE
    fields across THREE types declare it, every one must state a reason in the artefact (a
    bare ``ESTABLISHED_HERE`` raises :exc:`EstablishmentFault` at decoration and stops the
    module importing), and they are ``Value.value``, ``Degraded.value`` and
    ``FetchedResponse.payload``. The first two are a GENERIC PARAMETER — ``T`` is the dial
    score type and is the caller's, and exact-typing it against a fixed pair of score
    classes would write product meaning this seat has no authority to write (CD-RULE-003).
    The third is a FOREIGN PAYLOAD arriving from an adapter, which is CD-BP-003's surface
    one type down. Executable example::

        @establishes(value=ESTABLISHED_HERE("generic parameter T"), ...)
        class Value: ...           # then Value(value=object(), ...) reaches the body

    **CARRIER MEASURED:** ``tools/register/check_constructor_field_establishment.py``
    prints every use with its class, field and line at every run, and
    ``tests/test_field_establishment.py::test_the_established_here_field_exemptions_are_exactly_this_set``
    pins the exact set. A fourth use is a test failure, not a quiet widening.
    **CARRIER for what those three fields actually hold: PARTIAL.** ``Value.value`` and
    ``Degraded.value`` are re-established one level up by ``DialSet.__post_init__``'s
    ``_reject_cross_typed``, which is measured by ``tests/test_dialset.py`` and IS ITSELF
    BODY-BORNE. For ``FetchedResponse.payload``: **NOT PROVED TO BE CARRIED ANYWHERE** —
    it is CD-BP-003, source trust is CD-D-005, and no guard was built over it.

 3  **A CLASS IS BUILT OUT OF THINGS THE INTERPRETER LEAVES REACHABLE.** This is the same
    REACH ``admission.py`` declares as its DECLARED LIMIT 6 and it is inherited rather than
    newly incurred: anything that can execute code inside this package can reach
    ``__init__.__closure__`` or rebind ``cls.__init__``. ``__wrapped__`` is deleted from the
    wrapper for the same reason ``admits`` deletes it — it is a documented attribute
    ``inspect.unwrap`` follows — and the deletion is measured by
    ``tests/test_field_establishment.py::test_a_governed_type_publishes_no_way_round_its_own_boundary``.

    **THE WORDING BELOW IS THE MEASURED REACH AND NOT THE ONE THIS SEAT FIRST WROTE.** The
    first draft of this limit named the ``_DECLARATIONS`` registry as a route. It was
    MEASURED and it is NOT one: the wrapper closes over its own local ``compiled`` dict, so
    rewriting the registry changes what the boundary SAYS about itself and nothing about
    what it DOES — ``variants/WO-2R3/V37-establishes-registry-rewrite.patch`` ARM 3 rewrites
    it and the construction is STILL REFUSED. That is
    :func:`crash_detector.admission.declared_admissions`'s CD-ENG-WO2R3-F13 defect INVERTED:
    the introspection surface can be made to lie in the SAFE direction. **It is recorded
    rather than removed, because a seat that tries the obvious thing, sees a refusal and
    concludes the reach is closed will be wrong.**

    **THE ROUTE THAT IS OPEN IS THE CLOSURE CELL, and it is V33's move one level down.**
    ``V37`` ARM 4 finds the live ``compiled`` dict in ``__init__.__closure__``, rewrites its
    entries to ``ESTABLISHED_HERE`` and constructs
    ``ScoreComputation(magnitude=0.5, contributions=(object(),))`` through the ORDINARY front
    door: **ESCAPED**, with a bare ``object`` stored in ``contributions``. The mutation is to
    state the boundary SHARES, so every caller in the process is unguarded afterwards.
    **NOT CLOSED, NOT CLAIMED, NOT PROVED TO BE CARRIED ANYWHERE.** Every route requires the
    ability to execute code inside this package, which is the universal limit every
    in-process guard on this project lives inside; saying that is strictly weaker than
    "cannot happen", and it is said rather than implied.

 4  **A SUBCLASS OF A GOVERNED TYPE IS NOT GOVERNED, AND FOR A ``@dataclass`` SUBCLASS THAT
    IS TRUE OF ITS INHERITED FIELDS TOO.** The decorator is applied per class and a subclass
    carries no declaration of its own.

    **THIS WORDING IS THE MEASURED REACH AND IT IS WIDER THAN THE ONE THIS SEAT FIRST
    WROTE.** The first draft said the subclass "INHERITS the wrapped ``__init__``, so its
    INHERITED fields are still established". Measured, that is true of ONE of the two cases
    and false of the other, and the false one is the likelier:

    * a subclass that is ITSELF a ``@dataclass`` **REGENERATES** ``__init__``, which
      OVERRIDES the wrapped one, so **NOT ONE of its fields is established — inherited or
      added.** ``V38`` (a): ``ScoreComputationPlus(magnitude=0.5, contributions=(object(),))``
      is **ACCEPTED**, with a bare ``object`` in ``contributions`` that the parent refuses;
    * a PLAIN subclass, not a dataclass, does inherit the wrapped ``__init__`` and its
      inherited fields ARE established. ``V38`` (c): the same construction on
      ``ScoreComputationPlain`` is **REFUSED**.

    Executable example: ``variants/WO-2R3/V38-subclass-adds-an-unestablished-field.patch``.
    **CARRIER MEASURED, AND ONLY AT THE DOORS:** ``Value``, ``Degraded``, ``Unknown``,
    ``Shown`` and ``NotShown`` refuse subclassing outright at their metaclass, and every
    ``@admits`` door on the judgement path requires an EXACT type — ``V38`` (d) measures
    ``resolve_panel`` refusing a ``PanelRow`` subclass instance with
    ``NotAdmitted: row=PanelRowPlus is not admitted; this door requires exactly PanelRow or
    None``. For a subclass used ENTIRELY INSIDE this package, reaching no door:
    **NOT PROVED TO BE CARRIED ANYWHERE.** RAISED AS A FINDING (``CD-ENG-WO2R3-F19``).
"""

from __future__ import annotations

import dataclasses
import functools
import inspect

from .admission import (
    ESTABLISHED_HERE,
    declaration,
    each_of,
    one_of,
)

__all__ = [
    "EstablishmentFault",
    "UndeclaredField",
    "FieldNotEstablished",
    "ESTABLISHED_HERE",
    "one_of",
    "each_of",
    "establishes",
    "declared_establishment",
    "establishment_faults",
    "establishment_field_list",
    "is_establishing_type",
    "governed_types",
]


class EstablishmentFault(Exception):
    """A type's declaration and its DECLARED FIELD LIST disagree.

    **Deliberately NOT a** ``TypeError``, for the reason
    :exc:`crash_detector.admission.AdmissionFault` gives: a ``TypeError`` is what a
    boundary raises about a VALUE, product code catches ``TypeError`` in several places,
    and a caller's ``except TypeError`` must not be able to swallow the refusal of a
    boundary that is no longer guarding what it claims to guard.
    """


class UndeclaredField(EstablishmentFault):
    """The field list carries a field the declaration was not told about — or vice versa.

    Raised **on every construction** of the faulted type, before the generated ``__init__``
    assigns anything and before ``__post_init__`` runs. This is planted violation P7 one
    level down: *a new field added to a governed judgement-path type is refused on every
    construction*.
    """


class FieldNotEstablished(TypeError):
    """A declared field's established value is not of the exact type declared for it.

    A ``TypeError`` because what is wrong is the *kind of thing* the field holds, which is
    the same reading :exc:`crash_detector.admission.NotAdmitted` and
    :exc:`crash_detector.own_terms.NotEstablishedOnOwnTerms` already take.
    """


#: The declarations, held OFF the class. See the header: five of the thirty-two governed
#: types declare their COMPLETE attribute surface and assert it by set equality at import,
#: so a class attribute here would break CD-ASR-F02's layer-1 closure. Keyed by class
#: IDENTITY, never by name: a re-created class wearing the same name is a different object
#: and is not in it.
_DECLARATIONS: dict = {}

#: A field whose attribute does not exist after construction. Distinguished from ``None``,
#: which is a legitimate established value.
_ABSENT = object()


def _declared_field_list(cls) -> "tuple[tuple, tuple]":
    """``cls``'s DECLARED FIELD LIST, and its ``InitVar`` pseudo-fields, from the artefact.

    ``dataclasses.fields`` is the declaration itself — it is what the ``@dataclass``
    machinery built from the class body's annotations, including inherited fields, and it
    excludes ``ClassVar`` and ``InitVar``. The ``InitVar``s are read separately out of
    ``__dataclass_fields__`` so they can be REFUSED rather than silently ignored.
    """
    names = tuple(field.name for field in dataclasses.fields(cls))
    initvars = tuple(
        name
        for name, field in getattr(cls, "__dataclass_fields__", {}).items()
        if getattr(field._field_type, "name", "") == "_FIELD_INITVAR"
    )
    return names, initvars


def _faults(cls, field_names: tuple, initvars: tuple, declared: dict) -> tuple:
    """Every disagreement between the DECLARED FIELD LIST and the declaration, both ways."""
    found: list = []
    for name in initvars:
        found.append(
            f"{name!r} is an InitVar of {cls.__qualname__}. An InitVar reaches __init__ and "
            "is never an attribute, so its established value cannot be read back and this "
            "mechanism cannot establish it. A type that needs one is not a type this "
            "mechanism can close, and it says so rather than admitting it."
        )
    for name in field_names:
        if name not in declared:
            found.append(
                f"field {name!r} is in the DECLARED FIELD LIST of {cls.__qualname__} and "
                "was NOT declared to establishes(). A new field on a judgement-path type "
                "arrives REFUSED, never unguarded (BP-AMENDMENT-0001 §D.1 one level down; "
                "PO-DECISIONS-0007 ruling 1; planted violation P7 at the constructor)."
            )
    for name in declared:
        if name not in field_names:
            found.append(
                f"establishes() was told about {name!r}, which is not a declared field of "
                f"{cls.__qualname__}. A declaration that has come adrift from its field "
                "list is establishing a field that is not there."
            )
    return tuple(found)


def establishes(**declared: object):
    """Establish each of a type's DECLARED FIELDS by EXACT TYPE, at the class boundary.

    Applied OUTSIDE ``@dataclass``, so that ``dataclasses.fields(cls)`` — the declaration
    the dataclass machinery built from the class body — exists to derive from. The field
    list is read at decoration; the declaration is checked against it in BOTH directions;
    and any disagreement FAULTS the type so that every construction raises
    :exc:`UndeclaredField` before anything is assigned and before the body runs.

    ``@establishes()`` with no declarations is a meaningful and deliberate statement, not a
    no-op: it says *this type declares no fields and I was told about none*, and adding one
    later refuses every construction.

    :raises EstablishmentFault: at decoration, if the subject is not a dataclass or a
        declaration is not a form :mod:`crash_detector.admission` recognises. A malformed
        declaration is a defect in the type and must stop the module importing rather than
        produce a type that establishes by accident.
    :raises UndeclaredField: on every construction, if the field list and the declaration
        disagree, or the type carries an ``InitVar``.
    :raises FieldNotEstablished: on a construction, if a field's established value is not
        of the declared exact type.
    """
    compiled = {
        name: declaration(name, declared_form)
        for name, declared_form in declared.items()
    }

    def apply_at_the_boundary(cls):
        if not dataclasses.is_dataclass(cls):
            raise EstablishmentFault(
                f"@establishes was applied to {cls!r}, which is not a dataclass. The "
                "establishment is DERIVED FROM THE DECLARED FIELD LIST, and a class with "
                "no field list has nothing to derive it from. Apply it OUTSIDE "
                "@dataclass, never inside."
            )
        field_names, initvars = _declared_field_list(cls)
        faults = _faults(cls, field_names, initvars, declared)
        original_init = cls.__init__

        @functools.wraps(original_init)
        def __init__(self, *args, **kwargs):
            # THE FAULT IS CHECKED FIRST, ON EVERY CONSTRUCTION, BEFORE ANYTHING IS BOUND.
            # A type whose declaration no longer matches its field list is not a type that
            # establishes most of itself — it is a type that has stopped establishing, and
            # it must say so at every construction rather than at one import.
            if faults:
                raise UndeclaredField(
                    f"{cls.__qualname__} is a FAULTED type and every construction of it is "
                    "refused. " + " ".join(faults)
                )
            original_init(self, *args, **kwargs)
            # AND THEN THE FIELDS, READ FROM THE OBJECT'S OWN ESTABLISHED STATE. See the
            # header for why this is AFTER the generated __init__ and not before it.
            for name in field_names:
                value = getattr(self, name, _ABSENT)
                if value is _ABSENT:
                    raise FieldNotEstablished(
                        f"{cls.__qualname__}.{name} is in the DECLARED FIELD LIST and no "
                        "attribute of that name exists after construction, so its value "
                        "cannot be established. A field this boundary cannot read is a "
                        "field this boundary has not established."
                    )
                refusal = compiled[name].refusal(name, value)
                if refusal is not None:
                    raise FieldNotEstablished(
                        f"{cls.__qualname__}.{refusal} (BP-AMENDMENT-0001 §D.1 one level "
                        "down, PO-DECISIONS-0007 ruling 1 — every public type in the "
                        "frozen subject on a judgement path establishes each of its "
                        "declared fields by exact type AT THE BOUNDARY, derived from the "
                        "DECLARED FIELD LIST and not written into __post_init__, which is "
                        "a body.)"
                    )

        # THE TYPE DOES NOT PUBLISH A WAY ROUND ITS OWN BOUNDARY.
        #
        # `functools.wraps` sets `__wrapped__` to the generated `__init__`. That attribute
        # is documented and `inspect.unwrap` follows it, so
        # `object.__new__(C); C.__init__.__wrapped__(obj, ...)` would be a bypass writable
        # in ordinary-looking code. It is removed, exactly as `admits` removes it, and for
        # the reason V24 arm 2 measured. What this does NOT close is the closure cells —
        # see DECLARED LIMIT 3; that is true of every decorator in Python.
        try:
            delattr(__init__, "__wrapped__")
        except AttributeError:  # pragma: no cover - wraps always sets it
            pass
        # The generated signature is kept as DATA, so `inspect.signature(C.__init__)` still
        # reports what the constructor takes. A `Signature` is a description; it is not a
        # callable and it is not a way through.
        __init__.__signature__ = inspect.signature(original_init)
        cls.__init__ = __init__
        _DECLARATIONS[cls] = (dict(compiled), faults, field_names)
        return cls

    return apply_at_the_boundary


def declared_establishment(cls: object) -> dict:
    """What ``cls`` was told about, or ``{}`` if it is not a governed type."""
    return dict(_DECLARATIONS.get(cls, ({}, (), ()))[0])


def establishment_faults(cls: object) -> tuple:
    """``cls``'s declaration faults. Non-empty means every construction of it raises."""
    return tuple(_DECLARATIONS.get(cls, ({}, (), ()))[1])


def establishment_field_list(cls: object) -> tuple:
    """The DECLARED FIELD LIST this boundary derived its establishment from."""
    return tuple(_DECLARATIONS.get(cls, ({}, (), ()))[2])


def is_establishing_type(cls: object) -> bool:
    """True if ``cls`` carries an ``establishes`` declaration."""
    return cls in _DECLARATIONS


def governed_types() -> tuple:
    """Every type this boundary governs, in decoration order.

    Read by ``tests/test_field_establishment.py`` so the RUNTIME population can be diffed
    against the STATIC population the register check enumerates. Two independent readings
    of the same class that must agree.
    """
    return tuple(_DECLARATIONS)
