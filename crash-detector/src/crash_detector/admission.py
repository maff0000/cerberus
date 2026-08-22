"""``admits`` — ESTABLISHMENT DERIVED FROM THE SIGNATURE (BP-AMENDMENT-0001 §D.1, in force).

    @admits(row=one_of(PanelRow, None), now_utc=datetime, staleness_window_seconds=float)
    def resolve_panel(row, *, now_utc, staleness_window_seconds): ...

This module is a BLUEPRINT §1 INSTRUMENT and not a §7 local rule. Its subject is *every
public entry point on a judgement path*, and three of the doors §D.2 lists — ``resolve_panel``
(§6, the witness layer), ``present_dial`` (the serving path) and ``collect`` (§5, the
collector runner) — are not in §7 at all. It therefore lives at the top of the package,
beside :mod:`crash_detector.own_terms`, and not inside ``engine/``.

====================================================================================
WHY THE ESTABLISHMENT IS DERIVED FROM THE SIGNATURE AND NOT WRITTEN INTO THE BODY
====================================================================================

Both escapes this project has suffered at this altitude were EDITS TO A BODY:

* ``CD-ASR-F03`` replaced the ``missing_required`` branch of ``_evaluate_dial``'s body with
  a value-bearing reading, and every rule that lived in that body went with it;
* the fourth argument that ``_absence_is_never_a_number`` is deliberately written with
  ``*extra`` to survive is the same shape read from the other side — a guard whose arity is
  fixed stops guarding the moment somebody adds an argument.

A rule that lives in a function body is rewritten by editing the function body. So the rule
is applied HERE, at the boundary, and it is computed FROM ``inspect.signature`` — from the
door's own parameter list — rather than from anything a body says. A rewrite of the body
cannot remove it, because the body is not consulted.

====================================================================================
THE THREE THINGS THIS DOOR REFUSES, AND THE THIRD IS THE ONE THAT MATTERS
====================================================================================

**1. A VALUE OF THE WRONG EXACT TYPE** — ``type(value) is not declared``, never
``isinstance``. This is CD-AC-005 Class 2 and it is this codebase's standing doctrine: a
subclass may shadow any attribute with a property, and a property is the caller's code
running inside this system's judgement at the moment the judgement is made. The refusal is
:exc:`NotAdmitted`, a ``TypeError``, because what is wrong is the *kind of thing* offered.

**2. A PARAMETER THE DECLARATION WAS NOT TOLD ABOUT** — and this refusal fires **ON EVERY
CALL**, whether or not the caller passes the new argument. The parameter list is read from
the signature at decoration; if it and the declaration disagree in either direction the door
is FAULTED, and a faulted door raises :exc:`UndeclaredParameter` before it binds anything
and before the body runs. **A new argument added to a decorated door arrives REFUSED, never
unguarded** (planted violation P7 of BP-AMENDMENT-0001 §F.1, which the Product Owner
directed the fourth Assurance seat to run first).

It fires on every call rather than at import deliberately. An import-time refusal would be
one event in one process at one moment; a call-time refusal is re-derived and re-raised at
every single entry, so no amount of import ordering, lazy loading, reload or
``importlib`` cleverness gets a call past it. The fault itself is still computed once, from
the signature, at decoration — the check is derived statically and enforced dynamically.

**3. AN OPEN CHANNEL** — a ``*args`` or ``**kwargs`` parameter on a decorated door is itself
a fault. A variadic parameter is *the general case* of "a parameter it was not told about":
values arrive through it with no name to declare and no type to require. A door that needs
one is not a door this mechanism can close, and saying so loudly is the honest answer.

====================================================================================
WHAT THIS IS NOT
====================================================================================

**IT IS NOT "add ``type(row) is not PanelRow`` to ``resolve_panel``".** That is the instance
game the first gate caught, the auditor named it as the thing WO-2R3 must not be scoped to,
and §D.1 repeats the sentence. The unit of work here is *the class of doors*: the mechanism
is one function, it derives what it requires from each door's own signature, and the
acceptance test is ``tools/register/check_judgement_path_doors.py``, which enumerates the
judgement paths FROM THE ARTEFACT and fails on any public entry point that is not decorated.

====================================================================================
DECLARED LIMIT (CD-RULE-004), in the check header, the register entry and the execution
contract, each with an executable example. CD-RULE-006: each hand-off names a layer MEASURED
to carry it, or says NOT PROVED TO BE CARRIED ANYWHERE.
====================================================================================

 1  **``ESTABLISHED_HERE`` IS AN EXPLICIT WEAKENING AND IT IS COUNTED, NOT HIDDEN.** EIGHT
    parameters across FIVE callables declare it, and every one of them must state a reason
    in the artefact — a bare ``ESTABLISHED_HERE`` raises :exc:`AdmissionFault` at decoration
    and stops the module importing. Executable example::

        @admits(value=ESTABLISHED_HERE("this callable IS the establishment door"))
        def own_model_id(value): ...      # then own_model_id(object()) reaches the body

    **CARRIER MEASURED:** ``tools/register/check_judgement_path_doors.py`` prints every use
    with its file, line and parameter at every run, and
    ``tests/test_admission.py::test_the_established_here_exemptions_are_exactly_this_set``
    pins the exact set — module, callable and parameter. A ninth use fails that test. The
    check REPORTS the uses; it does not adjudicate them, and a reviewer must.

 5  **THE SIX ``ESTABLISHED_HERE`` USES ON §B.3's DOORS ARE A LIMIT AND NOT A CLOSURE, AND
    THE LIMIT IS §D.1's OWN CONCERN LEFT OPEN.** ``combine_within_one_dial(using)``,
    ``observed_for_dial(dial_id, quantity, inputs_used)`` and
    ``derived_within_one_dial(quantities, reduction)`` are BP-AMENDMENT-0001 §B.3's *"doors
    already closed, and they are the template"*. They establish their arguments by exact
    type **IN THEIR BODIES**, and each refuses with its OWN NAMED ERROR —
    ``UndeclaredReduction``, ``ScoreOutOfRange``, ``CrossDialCombination``,
    ``QuantityProvenanceMissing`` — which is the refusal identity nine auditor-derived tests
    assert and which CD-PL-F74 requires be recorded. Exact-typing them at the door would
    PREEMPT those named refusals with a generic :exc:`NotAdmitted` and replace this
    project's strongest closures with a coarser one, so they are decorated for the P7
    property ONLY: a new argument added to any of them arrives refused, and their type
    establishment stays where it is.

    **So §D.1's rule — "the establishment is derived from the signature rather than written
    into the body" — is NOT held at these three doors.** A rewrite of their bodies removes
    their type establishment, which is CD-ASR-F03's shape at the doors §B.3 calls the
    template. §D.2's table does not list them and this seat did not invent that scope.
    Executable example: delete the ``type(offered) is not DeclaredQuantity`` refusal from
    ``derived_within_one_dial``'s body and a bare ``float`` is admitted, with the decorator
    untouched — ``variants/WO-2R3/V19-b3-door-body-rewrite.patch``.
    **CARRIER MEASURED, and it is a body-level carrier:**
    ``tests/test_dial_provenance.py::test_the_derivation_door_refuses_a_value_whose_provenance_it_cannot_establish``
    and its siblings measure the bodies refusing TODAY. As a structure that survives an edit
    to those bodies: **NOT PROVED TO BE CARRIED ANYWHERE.** RAISED AS A FINDING to the
    Project Lead rather than closed here.

 6  **A DOOR IS BUILT OUT OF THINGS THE INTERPRETER LEAVES REACHABLE, AND ANYTHING THAT CAN
    EXECUTE CODE INSIDE THIS PACKAGE CAN REACH THEM.** This limit is a REACH, not a route,
    and its wording was three times narrower than what has since been measured through it.
    **THE ROUTES NAMED BELOW ARE KNOWN ROUTES AND ARE NOT AN EXHAUSTIVE SET.** Three
    distinct ones have now been found by three different parties on three different
    drivers, each time against a declaration that named one; anyone reading this should
    assume there is a fourth and should look for it rather than check this list.

    **(a) THE ``__closure__`` REACH — and it has TWO measured consequences, not one.**
    ``functools.wraps`` and this decorator both leave the door's working parts in the
    function's closure cells, and ``door.__closure__[i].cell_contents`` reaches every one
    of them. CPython offers no way to prevent it, so it is a property of the language and
    not of this design, and it is true of this codebase's own
    ``_absence_is_never_a_number``, which has passed three gates.

    *(a1) Reaching the WRAPPED FUNCTION and calling it, with the door bypassed.* Executable
    example: ``variants/WO-2R3/V24-wrapped-attribute-bypass.patch`` arm 3 —
    ASR3-F04's duck row returned ``Agrees`` and rendered ``WITNESS AGREES``. The door itself
    is untouched, so a second caller still meets a working door.

    *(a2) Reaching the LIVE DECLARATION DICT and rewriting it, so THE DOOR ITSELF STOPS
    REFUSING at its own front entrance.* Raised as ``CD-PL-F80`` by the Project Lead and
    MEASURED INDEPENDENTLY by this seat with the command recorded in the variant manifest:
    ``variants/WO-2R3/V33-closure-declaration-rewrite.patch``. ``resolve_panel.__closure__[0]``
    is the ``compiled`` dict this door consults on EVERY call; replacing its three entries
    with ``ESTABLISHED_HERE(...)`` makes the ORDINARY front-door call
    ``resolve_panel(DuckRow(), now_utc=..., staleness_window_seconds=600.0)`` return
    ``Agrees`` and render ``WITNESS AGREES``. This is a WIDER consequence than (a1): the
    mutation is to state the door SHARES, so every caller in the process is unguarded
    afterwards, including code that never went near a closure.

    **AND THE INTROSPECTION SURFACE DOES NOT SHOW IT, which is this seat's own finding
    (``CD-ENG-WO2R3-F13``) and is recorded here rather than repaired.** ``ADMITS_ATTRIBUTE``
    is set to ``dict(compiled)`` — A COPY TAKEN AT DECORATION — so after (a2):
    ``is_admitting_door(resolve_panel)`` is ``True``, ``declared_admissions(resolve_panel)``
    still reports ``['now_utc', 'row', 'staleness_window_seconds']``, and
    ``__admission_faults__`` is still ``()``. A reviewer asking the door what it requires is
    told the truth about what it WAS told and nothing about what it now DOES. Not repaired
    here: making the attribute the live object would hand a mutator a documented, supported
    handle instead of an interpreter-internal one, which is a WORSE trade, and choosing
    between them is a design decision outside a reconciliation increment.

    *(Note, measured: ``.clear()`` on that dict does NOT open the door — the body reads
    ``compiled[name]`` for every parameter the signature names, so an emptied dict raises
    ``KeyError`` and the door merely BREAKS. It has to be REWRITTEN, not emptied. Recorded
    because a seat that tries the obvious thing and sees a refusal may conclude the reach is
    closed. It is not.)*

    **(b) THE ``__wrapped__`` ATTRIBUTE — THIS HALF IS CLOSED HERE**, and the closure is
    measured (``tests/test_admission.py::test_a_door_publishes_no_way_round_itself``): the
    attribute is a documented one that ``inspect.unwrap`` follows and editors offer, so it
    was a bypass writable in ordinary-looking code with no cast and no import, and it is
    deleted. Executable example of what it used to do:
    ``variants/WO-2R3/V24-wrapped-attribute-bypass.patch`` arm 2.

    **(c) REBINDING THE ESTABLISHING FUNCTION IN ITS OWN MODULE NAMESPACE.** Raised as
    ``CD-PL-F83`` by the Project Lead on a driver that is in no corpus, and REPLICATED BY
    THIS SEAT rather than relayed: ``variants/WO-2R3/V34-establishing-function-rebound.patch``.
    ``crash_detector.collectors.runner.ensure_utc = lambda value: <1999>`` makes every
    recorded ``AttemptRecord.requested_utc`` read ``1999-01-01T00:00:00``, against a control
    on the unmodified module that records ``2026-08-22T12:00:00``. **THE DOOR IS SATISFIED
    IN BOTH ARMS** — ``started_utc`` is an exact ``datetime`` either way — because this
    module establishes a value's TYPE and never the IDENTITY OF THE FUNCTION THAT
    ESTABLISHED IT. It attacks the establishment layer, not the door.

    **WHAT IS AND IS NOT DEFEATED BY (c).** It is NOT a caller route: it needs the ability
    to execute code inside the package. BP-AMENDMENT-0001 §D.3 part 1's claim is about what
    a CALLER of ``collect`` can supply, and that claim SURVIVES — ``clock`` and ``sleep``
    are not parameters, and the interpreter refuses to pass them.

    **THE WHOLE REACH: NOT CLOSED, NOT CLAIMED, NOT PROVED TO BE CARRIED ANYWHERE.** Every
    route above requires the ability to execute code inside this package, which is the
    universal limit every in-process guard on this project lives inside; saying that is
    strictly weaker than "cannot happen", and it is said rather than implied.

 2  **THE RECEIVER OF A METHOD IS NOT ESTABLISHED.** The first parameter is skipped when,
    and only when, the callable was written inside a ``class`` body — read from
    ``__qualname__`` — AND that parameter is named ``self`` or ``cls``. The name is a
    vocabulary and this project's own CD-PL-F74 rule says so. Two things bound it:

    * the class-body test is asked FIRST, so a MODULE-LEVEL function whose parameter is
      named ``cls`` has no receiver to skip and is established like any other.
      ``assert_closed_presentation_surface(cls)`` on the serving path is exactly such a
      function, and this narrowing exists because the mechanism FAULTED that door the first
      time it was applied to it rather than quietly skipping its only argument;
    * the direction of the remaining dependence is the safe one. Renaming ``self`` does not
      open a hole, it FAULTS the door and every call raises :exc:`UndeclaredParameter`.

    Executable examples::

        class C:
            @admits()
            def m(myself): ...            # C().m() raises UndeclaredParameter

        @admits(cls=SealedPresentationType)
        def module_level(cls): ...        # `cls` IS established here

    **CARRIER MEASURED:** ``tests/test_admission.py::test_renaming_the_receiver_faults_the_door``
    and ``::test_a_module_level_parameter_named_cls_is_established_and_not_skipped``.
    A ``staticmethod`` written in a class body whose first parameter happens to be named
    ``self`` would have that parameter skipped; there are ZERO ``staticmethod``s and ZERO
    ``classmethod``s in the subject set, and ``check_judgement_path_doors.py`` PRINTS the
    counts it observed, so the premise is measured at every run rather than assumed.

 3  **THIS MODULE ESTABLISHES A VALUE'S TYPE, NEVER ITS TRUTH.** An exactly-typed
    ``ObservationRecord`` carrying a dishonest payload is admitted here and refused, if at
    all, somewhere else. Executable example: ``evaluate([ObservationRecord(source_id="x",
    observed_utc=NOW, outcome=OK(payload={"v": 1e18}, source_as_of_utc=NOW))], ...)`` is
    admitted by this door. **CARRIER MEASURED for the one case that decides a dial number:**
    the absence post-condition ``refuse_a_number_without_its_inputs`` and the staleness
    window; for source trust in general (CD-D-005, BLUEPRINT §5) **NOT PROVED TO BE CARRIED
    ANYWHERE.**

 4  **A CONTAINER'S ELEMENTS ARE ESTABLISHED WHEN THE DOOR IS CALLED, NOT AFTERWARDS.**
    :func:`each_of` walks the container once, at the door. A caller holding a reference to a
    mutable ``list`` can replace an element after the call has been admitted. Executable
    example is in ``tests/test_admission.py::test_a_list_mutated_after_admission_is_not_re_established``.
    **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE** for the general case; for ``evaluate``
    specifically the elements are read once, immediately, into ``_latest_usable_ok``, and
    that is a property of that function and not of this one.
"""

from __future__ import annotations

import functools
import inspect

__all__ = [
    "AdmissionFault",
    "UndeclaredParameter",
    "NotAdmitted",
    "ADMITS_ATTRIBUTE",
    "FAULTS_ATTRIBUTE",
    "ESTABLISHED_HERE",
    "one_of",
    "each_of",
    "admits",
    "declaration",
    "declared_admissions",
    "admission_faults",
    "is_admitting_door",
]

#: The attribute an admitting door carries, naming what it was told about. The static check
#: reads the SOURCE and never this attribute — an auditor who trusts nothing in the
#: implementation must be able to run the acceptance test without importing the product —
#: but the runtime tests read it, and so does anything that wants to ask a door what it
#: requires without calling it.
ADMITS_ATTRIBUTE = "__admits__"

#: The attribute carrying the door's declaration faults, computed from the signature at
#: decoration. Empty on a sound door. Non-empty means EVERY call raises.
FAULTS_ATTRIBUTE = "__admission_faults__"

#: The only parameter names skipped as a method receiver, and only in first position. See
#: DECLARED LIMIT 2: renaming these FAULTS the door rather than opening it.
_RECEIVER_NAMES = ("self", "cls")


class AdmissionFault(Exception):
    """A door's declaration and its signature disagree.

    **Deliberately NOT a** ``TypeError``. A ``TypeError`` is what a door raises about a
    VALUE, and product code catches ``TypeError`` in several places; a declaration fault is
    a defect in the door itself, and a caller's ``except TypeError`` must not be able to
    swallow the refusal of a door that is no longer guarding what it claims to guard.
    Collapsing *cannot determine* into *determined to be wrong* is how a check comes to
    report success it never established (Standards Baseline §8).
    """


class UndeclaredParameter(AdmissionFault):
    """The signature carries a parameter the declaration was not told about — or vice versa.

    Raised **on every call** to the faulted door, before the arguments are bound and before
    the body runs. This is planted violation P7: *a new parameter added to a decorated door
    without being declared to* ``admits`` *is refused on every call*.
    """


class NotAdmitted(TypeError):
    """A value of the wrong exact type arrived at a door.

    A ``TypeError`` because what is wrong is the *kind of thing* offered, which is the same
    reading :exc:`~crash_detector.own_terms.NotEstablishedOnOwnTerms` and
    :exc:`~crash_detector.serving.dial_presentation.DialPresentationRefused` already take.
    """


# ---------------------------------------------------------------------------------------- #
# THE DECLARATION VOCABULARY. Three forms, and no fourth: a declaration this module cannot
# recognise is a FAULT and not a value it guesses at.
# ---------------------------------------------------------------------------------------- #


class _Admission:
    """One parameter's requirement. ``refusal`` returns a message, or ``None`` to admit."""

    __slots__ = ()

    def refusal(self, parameter: str, value: object) -> "str | None":
        raise NotImplementedError

    def describe(self) -> str:
        raise NotImplementedError


class _Exactly(_Admission):
    """``type(value)`` must BE one of these types. Never ``isinstance``.

    Exact identity of the type object, so a subclass is refused rather than admitted and
    silently trusted. A subclass may shadow any attribute with a property, and a property is
    the caller's code running inside this system's judgement — which is the whole of
    CD-AC-005 Class 2 and of ``ASR3-F04``, where a row whose ``state`` property answered
    ``AGREES`` while its stored state was ``UNAVAILABLE`` rendered ``WITNESS AGREES``.
    """

    __slots__ = ("types",)

    def __init__(self, types: tuple) -> None:
        self.types = types

    def refusal(self, parameter: str, value: object) -> "str | None":
        if type(value) in self.types:
            return None
        return (
            f"{parameter}={type(value).__name__} is not admitted; this door requires "
            f"exactly {self.describe()}. Exact type and never isinstance: a subclass may "
            f"shadow any attribute with a property, and a property is the caller's code "
            f"running inside this system's judgement (CD-AC-005 Class 2)."
        )

    def describe(self) -> str:
        return " or ".join(
            "None" if t is type(None) else t.__name__ for t in self.types
        )


class _EachOf(_Admission):
    """The container is exactly one of ``within``, and EVERY element exactly ``element``.

    A3's requirement, and it is written *the record, not only the outcome*: exact-typing the
    element one level in is not the same claim as exact-typing what arrived, and the
    difference is a sequence of look-alikes each of which happens to carry an honest
    ``outcome``.
    """

    __slots__ = ("element", "within")

    def __init__(self, element: tuple, within: tuple) -> None:
        self.element = element
        self.within = within

    def refusal(self, parameter: str, value: object) -> "str | None":
        if type(value) not in self.within:
            return (
                f"{parameter}={type(value).__name__} is not admitted; this door requires "
                f"exactly {' or '.join(t.__name__ for t in self.within)} whose every "
                f"element is exactly {_names(self.element)}. A supplied container decides "
                f"its own iteration, and what this door iterates is not the caller's "
                f"judgement to make."
            )
        for index, element in enumerate(value):
            if type(element) not in self.element:
                return (
                    f"{parameter}[{index}]={type(element).__name__} is not admitted; every "
                    f"element must be exactly {_names(self.element)}. The RECORD is "
                    f"established here and not only what it carries: an element that is "
                    f"merely shaped like one decides which observations are usable "
                    f"(BP-AMENDMENT-0001 §D.2, A3)."
                )
        return None

    def describe(self) -> str:
        return (
            f"{' or '.join(t.__name__ for t in self.within)} of {_names(self.element)}"
        )


class _EstablishedHere(_Admission):
    """This parameter is NOT exact-typed at the door, and the reason is recorded.

    For the three callables whose contract IS establishment — they accept any object and
    refuse it themselves. See DECLARED LIMIT 1: every use is printed by the static check and
    the exact set is pinned by a test, so a fourth use is a test failure and not a quiet
    widening.
    """

    __slots__ = ("because",)

    def __init__(self, because: str) -> None:
        self.because = because

    def refusal(self, parameter: str, value: object) -> "str | None":
        return None

    def describe(self) -> str:
        return f"ANY VALUE — established in the body ({self.because})"

    def __call__(self, because: str) -> "_EstablishedHere":
        """``ESTABLISHED_HERE("reason")`` — the reason is required, not optional."""
        if not isinstance(because, str) or not because.strip():
            raise AdmissionFault(
                "ESTABLISHED_HERE requires a stated reason. An unexplained exemption is "
                "the escape hatch this mechanism exists to make impossible to write "
                "quietly (CD-RULE-004)."
            )
        return _EstablishedHere(because)


#: The one exemption, and it must be CALLED with its reason: ``ESTABLISHED_HERE("...")``.
ESTABLISHED_HERE = _EstablishedHere("no reason stated")


def _names(types: tuple) -> str:
    return " or ".join("None" if t is type(None) else t.__name__ for t in types)


def one_of(*types: object) -> _Exactly:
    """Exactly one of these types. ``None`` stands for ``type(None)``.

    A4's ``PanelRow`` or ``None``, and A5's *exactly one of the sealed ``Reading`` members*,
    are both written with this. It is not a union in the typing sense and it does not admit
    a subclass of any member: it is a closed set of type identities.
    """
    return _Exactly(_type_tuple(types, "one_of"))


def each_of(*element: object, within: tuple = (tuple, list)) -> _EachOf:
    """A container of exactly ``within``, every element exactly one of ``element``."""
    if not isinstance(within, tuple) or not within:
        raise AdmissionFault("each_of(within=...) takes a non-empty tuple of types")
    return _EachOf(_type_tuple(element, "each_of"), _type_tuple(within, "each_of"))


def _type_tuple(values: tuple, where: str) -> tuple:
    resolved = []
    for value in values:
        if value is None:
            resolved.append(type(None))
        elif isinstance(value, type):
            resolved.append(value)
        else:
            raise AdmissionFault(
                f"{where}() takes types (or None), got {type(value).__name__}. A "
                "declaration this module cannot recognise is a fault, never a value it "
                "guesses at."
            )
    if not resolved:
        raise AdmissionFault(f"{where}() requires at least one type")
    return tuple(resolved)


def _compile(parameter: str, declaration: object) -> _Admission:
    """Turn one declaration into an :class:`_Admission`, or raise :exc:`AdmissionFault`."""
    if declaration is ESTABLISHED_HERE:
        raise AdmissionFault(
            f"admits({parameter}=ESTABLISHED_HERE) states no reason. The exemption must be "
            'CALLED with one — ESTABLISHED_HERE("...") — so that every weakening of this '
            "mechanism carries its justification in the artefact where the static check "
            "can print it and a test can pin it (CD-RULE-004)."
        )
    if isinstance(declaration, _Admission):
        return declaration
    if declaration is None:
        return _Exactly((type(None),))
    if isinstance(declaration, type):
        return _Exactly((declaration,))
    if isinstance(declaration, tuple):
        return _Exactly(_type_tuple(declaration, "admits"))
    raise AdmissionFault(
        f"admits({parameter}=...) was given a {type(declaration).__name__}, which is not a "
        "type, a tuple of types, one_of(...), each_of(...) or ESTABLISHED_HERE(...). There "
        "is no fourth form and nothing is inferred."
    )


# ---------------------------------------------------------------------------------------- #
# THE MECHANISM
# ---------------------------------------------------------------------------------------- #


def _signature_parameters(entry_point) -> tuple:
    """The door's own parameters, read from ITS signature — never from a wrapped one.

    ``follow_wrapped=False`` matters and is not a detail. ``functools.wraps`` sets
    ``__wrapped__``, and ``inspect.signature`` follows it by default — so a door already
    wrapped by another decorator would be guarded against the signature of something that is
    NOT what the call binds against. What must be established is what this call actually
    passes, so the signature read is the one the call uses.
    """
    signature = inspect.signature(entry_point, follow_wrapped=False)
    parameters = list(signature.parameters.values())
    skipped: list = []
    if (
        _is_defined_in_a_class_body(entry_point)
        and parameters
        and parameters[0].name in _RECEIVER_NAMES
        and parameters[0].kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ):
        skipped.append(parameters.pop(0).name)
    return signature, parameters, skipped


def _is_defined_in_a_class_body(entry_point) -> bool:
    """Was this callable written inside a ``class`` statement?

    Read from ``__qualname__``, which records the lexical nesting the interpreter saw —
    ``ConfigSnapshot.model_for`` for a method, ``f.<locals>.g`` for a nested function,
    ``f.<locals>.C.m`` for a method of a locally defined class. It is a property of where
    the ``def`` was written and it is not something a caller can influence.

    It is asked BEFORE the name ``self``/``cls`` is consulted, and that ordering is the
    whole point: a module-level function whose parameter happens to be named ``cls`` — and
    ``assert_closed_presentation_surface(cls)`` on the serving path is exactly one — has no
    receiver to skip, so its argument is ESTABLISHED like any other. Skipping by name alone
    would have left that door open, and it did: this narrowing was made because the
    mechanism refused that door as FAULTED the first time it was applied to it.
    """
    qualname = getattr(entry_point, "__qualname__", "")
    parent = qualname.rpartition(".")[0]
    return bool(parent) and not parent.endswith("<locals>")


def _faults(entry_point, parameters: list, declared: dict) -> tuple:
    """Every disagreement between the SIGNATURE and the DECLARATION, in both directions."""
    found: list = []
    named = [p.name for p in parameters]
    for parameter in parameters:
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            found.append(
                f"*{parameter.name} is an OPEN CHANNEL. Values arrive through it with no "
                "name to declare and no type to require, which is the general case of the "
                "very thing this mechanism refuses. A door that needs one is not a door "
                "this mechanism can close, and it says so rather than admitting it."
            )
        elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
            found.append(
                f"**{parameter.name} is an OPEN CHANNEL, for the reason above."
            )
        elif parameter.name not in declared:
            found.append(
                f"parameter {parameter.name!r} is in the signature of "
                f"{entry_point.__qualname__} and was NOT declared to admits(). A new "
                "argument on a judgement-path door arrives REFUSED, never unguarded "
                "(BP-AMENDMENT-0001 §D.1; planted violation P7)."
            )
    for name in declared:
        if name not in named:
            found.append(
                f"admits() was told about {name!r}, which is not a parameter of "
                f"{entry_point.__qualname__}. A declaration that has come adrift from its "
                "signature is guarding a door that is not there."
            )
    return tuple(found)


def admits(**declared: object):
    """Require each of a door's arguments by EXACT TYPE, derived from its own signature.

    Applied at the boundary. The parameter list is read from ``inspect.signature`` at
    decoration; the declaration is checked against it in BOTH directions; and any
    disagreement FAULTS the door so that every call raises :exc:`UndeclaredParameter` before
    the arguments are bound and before the body runs.

    ``@admits()`` with no declarations is a meaningful and deliberate statement, not a
    no-op: it says *this door has no parameters and I was told about none*, and adding one
    later refuses every call.

    :raises AdmissionFault: at decoration, if a declaration is not a form this module
        recognises. A malformed declaration is a defect in the door and must stop the
        module importing rather than produce a door that admits by accident.
    :raises UndeclaredParameter: on every call, if the signature and the declaration
        disagree.
    :raises NotAdmitted: on a call, if an argument's exact type is not the declared one.
    """
    compiled = {
        parameter: _compile(parameter, declaration)
        for parameter, declaration in declared.items()
    }

    def apply_at_the_boundary(entry_point):
        signature, parameters, skipped = _signature_parameters(entry_point)
        faults = _faults(entry_point, parameters, declared)
        guarded_names = tuple(p.name for p in parameters)

        @functools.wraps(entry_point)
        def door(*args, **kwargs):
            # THE FAULT IS CHECKED FIRST, ON EVERY CALL, BEFORE ANYTHING IS BOUND.
            # A door whose declaration no longer matches its signature is not a door that
            # guards most of itself — it is a door that has stopped guarding, and it must
            # say so at every entry rather than at one import.
            if faults:
                raise UndeclaredParameter(
                    f"{entry_point.__qualname__} is a FAULTED door and every call to it is "
                    "refused. " + " ".join(faults)
                )
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            for name in guarded_names:
                if name not in bound.arguments:
                    continue
                refusal = compiled[name].refusal(name, bound.arguments[name])
                if refusal is not None:
                    raise NotAdmitted(
                        f"{entry_point.__qualname__}: {refusal} (BP-AMENDMENT-0001 §D.1 — "
                        "every public entry point on a judgement path establishes each of "
                        "its arguments by exact type at the door.)"
                    )
            return entry_point(*args, **kwargs)

        # THE DOOR DOES NOT PUBLISH A WAY ROUND ITSELF.
        #
        # `functools.wraps` sets `__wrapped__` to the function it wrapped. That attribute is
        # documented, `inspect.unwrap` and `inspect.signature` follow it automatically, and
        # editors offer it — so `resolve_panel.__wrapped__(duck_row, ...)` is a bypass a
        # caller can write in ordinary-looking code with no cast and no import. MEASURED at
        # this seat's own work before an auditor had to measure it: ASR3-F04's row went
        # through that attribute and rendered WITNESS AGREES with every door decorated
        # (variants/WO-2R3/V24-wrapped-attribute-bypass.patch).
        #
        # It is removed. Everything else `wraps` copies — the name, the qualname, the
        # docstring, the module — is kept, because those are what make a door readable and
        # none of them is a way through it.
        #
        # WHAT THIS DOES NOT CLOSE, STATED RATHER THAN LEFT: the wrapped function is still
        # in this closure's cells, and `door.__closure__[i].cell_contents` reaches it. That
        # is true of EVERY decorator ever written in Python, including
        # `_absence_is_never_a_number`, which has passed three gates; CPython offers no way
        # to prevent it. What changes is that a bypass now requires reaching into
        # interpreter internals rather than reading a documented attribute. See DECLARED
        # LIMIT 6.
        try:
            delattr(door, "__wrapped__")
        except AttributeError:  # pragma: no cover - wraps always sets it
            pass
        # The real signature is kept as DATA, so `inspect.signature(door)` still reports
        # what the door takes and the existing tests that read it — "there is no
        # `on_unknown` for a caller to write, CHECKED ON THE SIGNATURE" — keep working. A
        # `Signature` is a description; it is not a callable and it is not a way through.
        door.__signature__ = signature
        setattr(door, ADMITS_ATTRIBUTE, dict(compiled))
        setattr(door, FAULTS_ATTRIBUTE, faults)
        setattr(door, "__admission_receiver__", tuple(skipped))
        return door

    return apply_at_the_boundary


def declaration(name: str, declared: object) -> _Admission:
    """Compile ONE declaration into its :class:`_Admission`, or raise :exc:`AdmissionFault`.

    Public so that :mod:`crash_detector.establishment` — the same idea one level down, at a
    type's DECLARED FIELD LIST instead of a callable's signature — shares THIS EXACT
    vocabulary rather than growing a second one. Two declaration vocabularies that drift
    apart is how a reader comes to believe a field is established as strictly as a
    parameter when it is not; there is one, and it is here.
    """
    return _compile(name, declared)


def declared_admissions(door: object) -> dict:
    """What ``door`` was told about, or ``{}`` if it is not an admitting door."""
    return dict(getattr(door, ADMITS_ATTRIBUTE, {}))


def admission_faults(door: object) -> tuple:
    """``door``'s declaration faults. Non-empty means every call to it raises."""
    return tuple(getattr(door, FAULTS_ATTRIBUTE, ()))


def is_admitting_door(door: object) -> bool:
    """True if ``door`` carries an ``admits`` declaration."""
    return hasattr(door, ADMITS_ATTRIBUTE)
