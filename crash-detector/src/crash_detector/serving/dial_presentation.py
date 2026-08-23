"""``DialPresentation`` — what the surface shows for ONE dial, and absence is an ANSWER.

    DialPresentation := Shown(dial_id, magnitude) | NotShown(dial_id, reason, missing_inputs)

PID doctrine §3.2 is CONSTITUTIONAL: missing data must never render as calm. CD-AC-001's
words are about RENDERING — "missing or stale input never renders as calm".

====================================================================================
WHY THIS MODULE EXISTS — closing CD-ASR-WO2R-F03 (MEDIUM), CD-AC-001's AMBER
====================================================================================

An independent auditor wrote four lines that rendered absence as ``0.0`` with both declared
guards green (`ASR2-001-A`, measured again by this seat at ``50fc231``:
``CD-RT-001-AST-NO-NUMERIC-DEFAULT`` PASS 377 assertions, ``CD-RT-001-ABSENCE-RENDERS-UNKNOWN``
100 passed, whole suite 1325 passed, and ``SURFACE SHOWS: 0.0``):

    def surface_scalar(reading):
        return fold(reading,
                    on_value=lambda seen: seen.value,
                    on_degraded=lambda seen: seen.value,
                    on_unknown=lambda seen: 0.0)

It used none of the enumerated spellings — no ``float | None``, no ``or 0.0``, no
``.get(k, 0)``, no bare ``except``, no module-level constant, no numeric member on
``Unknown``. It went through :func:`~crash_detector.dials.reading.fold`, the exhaustive,
no-default-branch, surface-re-verifying consumer the design points every caller at.

**THE AUDITOR'S DIAGNOSIS IS EXACTLY RIGHT AND IS ADOPTED HERE.** ``fold``'s guarantee is
that a caller **cannot FORGET** ``Unknown``. It has never been a guarantee that a caller
cannot **ANSWER** ``Unknown`` with a number, and the criterion is about the second. The
present structure closed CONSTRUCTION of numeric defaults and left CONSUMPTION open.

====================================================================================
WHAT THIS MODULE DOES NOT DO, SAID FIRST SO IT CANNOT BE MISREAD
====================================================================================

**IT DOES NOT PUT A GUARD IN ``fold``, AND THAT IS A DECISION.** The tempting repair is to
make ``fold`` refuse a number returned from its ``on_unknown`` branch. This seat rejects it
and can say why:

* it is a ban on a RETURN TYPE, which is a spelling. ``on_unknown=lambda u: Box(0.0)`` walks
  straight past it, and so does returning the string ``"0.0"``. It would catch the
  auditor's four lines and not the class, which is the instance game a third time;
* ``fold`` is a general eliminator, not a dial surface. ``on_unknown=lambda u:
  len(u.missing_inputs)`` is a legitimate numeric answer about an absence, and a guard that
  forbade it would forbid the product to defend a proposition it does not defend.

So ``fold`` is left exactly as it is. **The honest answer was that ``fold`` is the wrong
SHAPE for the surface tier, not that ``fold`` needs another guard**, and what this module
adds is the right shape.

====================================================================================
THE INVARIANT
====================================================================================

**A NUMBER A CONSUMER CHOSE FOR AN ABSENCE CANNOT BE PRESENTED AS A DIAL.** It is the same
move the dial path already made twice, applied to the surface tier:

1. **THERE IS A TYPE FOR WHAT THE SURFACE SHOWS**, and it is a closed sum with no common
   ancestor, no shared base, sealed against subclassing, slotted against injection and
   asserted by set equality at import — the pattern
   :mod:`crash_detector.dials.reading` uses, for the reason it gives.

2. **``NotShown`` CARRIES NO NUMERIC FIELD OF ANY KIND.** There is nothing here to
   accidentally render as calm, because there is no number. Absence is ANSWERED — with the
   reason it is absent and the inputs that were missing — rather than merely left
   unconstructed.

3. **``Shown`` ADMITS ONLY A :class:`~crash_detector.dials.magnitude.DialMagnitude` OF ITS
   OWN DIAL**, by exact type identity and by set-equality on provenance. A bare ``float``
   is refused. So the auditor's ``0.0`` — and every other number a consumer might choose
   for an ``Unknown``, by any route, through any helper, computed any way — has nowhere to
   go: it is a ``float``, and a ``float`` cannot become a magnitude
   (:mod:`crash_detector.dials.provenance`) and cannot become a presentation (here).

4. **THE ELIMINATION IS PERFORMED BY THIS MODULE, NOT SUPPLIED BY THE CALLER.**
   :func:`present_dial` calls ``fold`` itself and writes all three branches itself. A
   surface that wants to show a dial does not get to write ``on_unknown``. This is the same
   structural move increment 1a made at the derivation door — the system performs the step
   rather than accepting the step's result — and it is why the closure is not a check on
   what a caller returned.

====================================================================================
WHAT REMAINS OPEN, STATED PLAINLY (CD-RULE-004, CD-RULE-006)
====================================================================================

**A. A MODULE MAY STILL COMPUTE ITS OWN NUMBER FROM AN ``Unknown`` AND HAND IT TO ITS OWN
CALLER. NOTHING HERE PREVENTS THAT, AND NOTHING IS CLAIMED TO.** `ASR2-001-A`'s
``surface_scalar`` still returns ``0.0`` if it is written, and still exits 0 under
``CD-RT-001-AST-NO-NUMERIC-DEFAULT``, because a static check cannot see a consumer's choice
and this module is not in that function's way.

What IS true, and is the whole of the change: that ``0.0`` cannot be PRESENTED as a dial.
MEASURED, not reasoned — ``Shown(dial_id=..., magnitude=0.0)`` raises
:exc:`DialPresentationRefused`, and so does every other non-magnitude.

**THE CARRIER FOR THE REMAINING ROUTE — a module that computes a number for an absence and
renders it ITSELF, without coming through here — IS: NOT PROVED TO BE CARRIED ANYWHERE.**
Said plainly rather than handed to a layer that does not hold, which is the CD-PL-F54 /
CD-PL-F59 defect and the reason CD-RULE-006 exists. There is no renderer in WO-2 to refuse
it: the rendering and publication LAYER is WO-3. What this module delivers is that when
WO-3 builds one, the type it must consume already exists and already refuses, so the
question is settled before the code that would get it wrong is written (BLUEPRINT §13: the
guard exists before the thing it guards).

**B. ``type.__setattr__`` INSTALLS A CLASS ATTRIBUTE WITHOUT GOING THROUGH A METACLASS**,
here as on the Reading constructors, and CPython offers no way to prevent it. The surface of
a presentation's class is therefore RE-VERIFIED at :func:`present_dial` and at
:func:`is_shown`, exactly as ``fold`` and ``is_value`` re-verify a reading's. A class
mutated after import is refused where a presentation of it would be used. This is boundary
A of :mod:`crash_detector.dials.reading` reached by the same road, and it is not a new
residue.

**C. ``object.__setattr__`` REWRITES A SLOT.** As for every frozen object in Python. The
direction that matters is safe: forging ``dial_id`` on a ``Shown`` makes it LESS usable,
because :func:`number_for_dial_slot` compares the magnitude's carried provenance to the
slot and not to anything this type says. Forging the magnitude slot with a bare float is the
already-declared private-slot residue and is reported statically by RULE 3 of
``tools/register/check_no_blend.py``; **no runtime layer carries it and none is claimed to**.
"""

from __future__ import annotations

from dataclasses import dataclass

from crash_detector.admission import ESTABLISHED_HERE, admits, is_exactly, one_of
from crash_detector.own_terms import NotEstablishedOnOwnTerms, own_str
from crash_detector.dials.magnitude import (
    CrossDialCombination,
    DialMagnitude,
    sole_dial_of,
)
from crash_detector.dials.reading import (
    READING_CONSTRUCTORS,
    Degraded,
    Reading,
    Unknown,
    Value,
    fold,
)
from crash_detector.dials.scores import SCORE_TYPES
from crash_detector.establishment import each_of, establishes

__all__ = [
    "DialPresentationRefused",
    "SealedPresentationType",
    "Shown",
    "NotShown",
    "DialPresentation",
    "PRESENTATION_CONSTRUCTORS",
    "DECLARED_PRESENTATION_SURFACE",
    "TOLERATED_INTERPRETER_MACHINERY",
    "assert_closed_presentation_surface",
    "present_dial",
    "is_shown",
]


class DialPresentationRefused(TypeError):
    """Something that is not this dial's magnitude was offered for presentation.

    A ``TypeError`` because what is wrong is the *type*, not a value someone passed — and
    the same choice, for the same reason, that
    :exc:`~crash_detector.dials.magnitude.CrossDialCombination` makes one package over.
    """


#: Names CPython's own ``dataclasses``/``type`` machinery may add depending on interpreter
#: patch level. Enumerated with intent; none of them can carry a number. ``__dict__`` is
#: deliberately NOT tolerated: a class that grows one has re-opened instance injection.
TOLERATED_INTERPRETER_MACHINERY: frozenset = frozenset(
    {
        "__getstate__",
        "__setstate__",
        "__replace__",
        "__weakref__",
        "__firstlineno__",
        "__static_attributes__",
    }
)

#: Members every frozen dataclass here carries. Written out rather than computed, because a
#: surface derived from observation would declare whatever it found — including whatever an
#: attacker added. That lesson is CD-ASR-F02's and it is applied here before anybody has to
#: learn it a fourth time.
_DATACLASS_MEMBERS: frozenset = frozenset(
    {
        "__annotations__",
        "__dataclass_fields__",
        "__dataclass_params__",
        "__delattr__",
        "__doc__",
        "__eq__",
        "__hash__",
        "__init__",
        "__match_args__",
        "__module__",
        "__post_init__",
        "__repr__",
        "__setattr__",
        "__slots__",
    }
)

#: THE COMPLETE DECLARED ATTRIBUTE SURFACE, per constructor, asserted by set EQUALITY at
#: import. ``tests/test_dial_presentation.py`` carries its own independent copy and asserts
#: the two agree, so widening this declaration fails a declared test rather than widening
#: the guard.
DECLARED_PRESENTATION_SURFACE = {
    "Shown": _DATACLASS_MEMBERS | frozenset({"dial_id", "magnitude"}),
    "NotShown": _DATACLASS_MEMBERS
    | frozenset({"dial_id", "reason", "missing_inputs"}),
}

_SEALED: set = set()


class SealedPresentationType(type):
    """The metaclass that closes the presentation constructors against extension.

    A metaclass rather than a base class, for the reason
    :class:`~crash_detector.dials.reading.SealedReadingType` gives: a shared base is
    somewhere a numeric accessor could be added once and inherited by both constructors,
    which is the route from absence to a number this module exists to close. A metaclass
    member is reachable on the class object and NOT on an instance, so
    ``not_shown.anything`` cannot resolve through it.
    """

    def __new__(mcls, name, bases, namespace, **kwargs):
        # ``isinstance`` AND NOT EXACT TYPE, DELIBERATELY (WO-2R3 increment 10, ITEM_1).
        # This is a REFUSAL predicate — satisfy it and the class statement is REFUSED — so
        # the WIDER operator is the STRICTER one and converting it would refuse LESS.
        # MEASURED at `686a374`, with `Sub = type('SealedPresentationTypeSub', (SealedPresentationType,), {})`
        # and `Forged = type.__new__(Sub, 'Forged', (NotShown,), ...)`:
        #     isinstance(Forged, SealedPresentationType) True   type(Forged) is ... False
        #     class Child(Forged): ...  -> REFUSED DialPresentationRefused   <- TODAY
        #     the exact-type predicate over the same bases -> ADMITS
        # **CONVERTING THIS LINE WOULD LET AN ORDINARY `class` STATEMENT SUBCLASS A SEALED
        # PRESENTATION THROUGH ONE FORGED INTERMEDIATE**, which is a WEAKENING of the
        # accident-proofing PO-DECISIONS-0018 ruling 1(a) explicitly keeps. Executed against
        # all four sealed metatypes; not one of them was inferred from another.
        for base in bases:
            if isinstance(base, SealedPresentationType):
                raise DialPresentationRefused(
                    f"{name} may not subclass {base.__name__}: the presentation sum type "
                    "is CLOSED. A subclass of NotShown carrying a numeric member would be "
                    "accepted everywhere a presentation is accepted, which is CD-ASR-F02's "
                    "route from absence to a number arriving one tier later."
                )
        return super().__new__(mcls, name, bases, namespace, **kwargs)

    def __setattr__(cls, name: str, value: object) -> None:
        if cls in _SEALED:
            raise DialPresentationRefused(
                f"cannot set {cls.__name__}.{name}: this presentation constructor is "
                "SEALED. Its attribute surface is declared in "
                "DECLARED_PRESENTATION_SURFACE and adding a member — numeric or not — is "
                "the route absence takes to become a number."
            )
        type.__setattr__(cls, name, value)

    def __delattr__(cls, name: str) -> None:
        if cls in _SEALED:
            raise DialPresentationRefused(
                f"cannot delete {cls.__name__}.{name}: this presentation constructor is "
                "SEALED. Removing the member that does the refusing changes the surface as "
                "much as adding one, and the surface is asserted by equality."
            )
        type.__delattr__(cls, name)


def _establish_dial_id(presentation: object) -> None:
    """Re-establish a presentation's ``dial_id`` as a plain ``str``, or refuse.

    Shared by both constructors so neither can validate it more loosely than the other, and
    a module function rather than a member so it does not widen the declared attribute
    surface asserted at import (the same reasoning
    :func:`crash_detector.dials.magnitude._install` gives).

    The id is not merely type-checked, it is REBUILT (CD-AC-005, Class 2). ``Shown``
    decides whether a magnitude may be shown under this name with ``carried !=
    self.dial_id``, and ``!=`` is the left operand's to define. ``isinstance(dial_id, str)``
    admitted a subclass, which could then answer that comparison itself and be presented as
    the other dial.
    """
    offered = getattr(presentation, "dial_id")
    try:
        established = own_str(offered)
    except NotEstablishedOnOwnTerms:
        established = ""
    if not established:
        raise DialPresentationRefused(
            f"a presentation names the ONE dial it is for, as a non-empty string; got "
            f"{offered!r}."
        )
    object.__setattr__(presentation, "dial_id", established)


@establishes(
    dial_id=str,
    magnitude=DialMagnitude,
)
@dataclass(frozen=True)
class Shown(metaclass=SealedPresentationType):
    """This dial has a reading, and here is the magnitude it is.

    ``magnitude`` is a :class:`~crash_detector.dials.magnitude.DialMagnitude` and **never a
    bare number**. That is the whole of CD-ASR-WO2R-F03's closure at this type: a number a
    consumer chose for an ``Unknown`` is a ``float``, a ``float`` cannot become a magnitude
    since CD-PL-F54, and it cannot become a presentation here — so there is no expression
    that presents it as a dial, whatever route produced it.
    """

    __slots__ = ("dial_id", "magnitude")

    dial_id: str
    magnitude: DialMagnitude

    def __post_init__(self) -> None:
        # RE-ESTABLISHED BEFORE `carried != self.dial_id` DECIDES ANYTHING (CD-AC-005,
        # Class 2). That comparison is the whole of this constructor's cross-dial refusal
        # and `!=` is the left operand's to define, so a `str` subclass admitted by
        # `isinstance` could answer it and be shown under the other dial's name.
        _establish_dial_id(self)
        if type(self.magnitude) is not DialMagnitude:
            raise DialPresentationRefused(
                f"a {type(self.magnitude).__name__} was offered as dial {self.dial_id!r}'s "
                "presented magnitude. A dial is SHOWN only from a value carrying the "
                "provenance that says which dial it is: a bare number has none, and a "
                "number a consumer chose because a reading was Unknown has less than none "
                "— it is not a measurement at all. PID doctrine §3.2: missing data must "
                "never render as calm (CD-AC-001, CD-ASR-WO2R-F03)."
            )
        try:
            carried = sole_dial_of(self.magnitude)
        except CrossDialCombination as refusal:
            raise DialPresentationRefused(
                f"nothing may be shown as dial {self.dial_id!r} without the provenance "
                f"that says it belongs there: {refusal}"
            ) from refusal
        if carried != self.dial_id:
            raise DialPresentationRefused(
                f"a magnitude whose provenance is {carried!r} was offered as dial "
                f"{self.dial_id!r}'s presentation. The two dials fail in opposite "
                "directions, so showing one dial's number under the other's name is the "
                "same defect as blending them, reached by a shorter road (CD-AC-002)."
            )


@establishes(
    dial_id=str,
    reason=str,
    missing_inputs=each_of(str, within=(tuple,)),
)
@dataclass(frozen=True)
class NotShown(metaclass=SealedPresentationType):
    """This dial has no reading, and here is why.

    **Carries no numeric field of any kind**, exactly as
    :class:`~crash_detector.dials.reading.Unknown` does not, and for the same reason: there
    is nothing here to accidentally render as calm, because there is no number. It is
    deliberately not parameterised by anything — it carries no value, so there is no type
    for it to be parameterised by, and that asymmetry is the point rather than an oversight.
    """

    __slots__ = ("dial_id", "reason", "missing_inputs")

    dial_id: str
    reason: str
    missing_inputs: tuple

    def __post_init__(self) -> None:
        _establish_dial_id(self)
        # `reason` carried no type check at all, so the refusal below was decided by the
        # supplied object's own __bool__ or __len__ (CD-AC-005, Class 2).
        try:
            object.__setattr__(self, "reason", own_str(self.reason))
            object.__setattr__(
                self,
                "missing_inputs",
                tuple(own_str(one) for one in self.missing_inputs),
            )
        except NotEstablishedOnOwnTerms as refusal:
            raise DialPresentationRefused(
                f"a presentation's reason and missing inputs are stated as strings: "
                f"{refusal}"
            ) from None
        if not self.reason:
            raise DialPresentationRefused(
                "NotShown requires a stated reason. 'We are not showing this' without a "
                "reason is an absence that has not been answered, which is the state this "
                "type exists to remove."
            )


#: The sum type. Closed.
DialPresentation = "Shown | NotShown"

#: The complete set of constructors, for guards that must enumerate them.
PRESENTATION_CONSTRUCTORS: tuple = (Shown, NotShown)

#: The same set as a frozenset of class objects, for exact-identity dispatch. Membership
#: here is IDENTITY: a look-alike and a re-created class of the same name are both absent.
_CONSTRUCTOR_IDENTITIES: frozenset = frozenset(PRESENTATION_CONSTRUCTORS)


@admits(cls=SealedPresentationType)
def assert_closed_presentation_surface(cls: type) -> None:
    """Raise unless ``cls``'s class dictionary is exactly the declared surface.

    Called at import and again at every consumer boundary, because ``type.__setattr__`` can
    install a member on a class object without going through the metaclass and no
    Python-level structure can prevent that (boundary B).
    """
    declared = DECLARED_PRESENTATION_SURFACE.get(cls.__name__)
    if declared is None:
        raise DialPresentationRefused(
            f"{cls.__name__} declares no surface in DECLARED_PRESENTATION_SURFACE, so "
            "there is nothing to verify it against. An undeclared presentation constructor "
            "is a defect, not a case to be tolerated."
        )
    observed = frozenset(vars(cls))
    unexpected = observed - declared - TOLERATED_INTERPRETER_MACHINERY
    missing = declared - observed
    breaches = []
    if unexpected:
        breaches.append(
            f"{cls.__name__} carries undeclared member(s) {sorted(unexpected)}. The surface "
            "is declared and asserted by equality, so this is a breach whether or not the "
            "member is numeric (CD-ASR-F02)."
        )
    if missing:
        breaches.append(
            f"{cls.__name__} is missing declared member(s) {sorted(missing)}. A removed "
            "member changes the surface as much as an added one."
        )
    if breaches:
        raise DialPresentationRefused(" ".join(breaches))


for _constructor in PRESENTATION_CONSTRUCTORS:
    if "__slots__" not in vars(_constructor):
        raise DialPresentationRefused(
            f"{_constructor.__name__} declares no __slots__. Without slots an instance "
            "carries a __dict__ and `object.__setattr__(presentation, 'magnitude', 0.0)` "
            "sticks: frozen refuses assignment to a declared field and says nothing about "
            "adding an undeclared one."
        )
    if _constructor.__dictoffset__:
        raise DialPresentationRefused(
            f"{_constructor.__name__} instances carry a __dict__ despite __slots__, so "
            "instance attribute injection is open."
        )
    assert_closed_presentation_surface(_constructor)
    _SEALED.add(_constructor)
del _constructor

if set(PRESENTATION_CONSTRUCTORS) != _SEALED or len(_SEALED) != 2:
    raise DialPresentationRefused(
        "not every presentation constructor was sealed at import. The seal is the whole of "
        "this module's layer-1 closure, so a constructor that reaches use unsealed is a "
        "failure to import and never a warning."
    )

#: The reason a dial is not shown when its reading is ``Unknown``. It restates the
#: reading's own reason rather than inventing one — this module decides nothing about WHY a
#: dial has no reading, only that "no reading" is answered rather than numbered.
REASON_NO_READING = "NO_READING"


@admits(dial_id=str, reading=one_of(*READING_CONSTRUCTORS))
def present_dial(dial_id: str, reading: "Reading") -> "Shown | NotShown":
    """What the surface shows for ONE dial. **THE ELIMINATION IS PERFORMED HERE.**

    A surface that wants to show a dial calls this. It does not call ``fold`` and write its
    own ``on_unknown``, which is precisely the shape `ASR2-001-A` used: ``fold`` guarantees
    a caller cannot FORGET ``Unknown`` and has never guaranteed that a caller cannot ANSWER
    ``Unknown`` with a number. Here there is no branch for a caller to supply.

    All three branches are written by this module:

    * ``Value``    -> :class:`Shown`, carrying the magnitude the reading's score carries;
    * ``Degraded`` -> :class:`Shown` too — a degraded reading HAS a value and must be
      rendered WITH its damage, and the damage travels as the reading's own
      ``missing_inputs``. It is deliberately not silently promoted to a clean reading and
      deliberately not suppressed: suppressing it would render damage as absence, which is
      the opposite error and just as wrong;
    * ``Unknown``  -> :class:`NotShown`, carrying the reading's stated reason and the
      inputs it was missing. **ABSENCE IS ANSWERED**, with a type that has no numeric field
      for an answer to hide in.

    The score is admitted by EXACT TYPE membership in
    :data:`~crash_detector.dials.scores.SCORE_TYPES`, never by ``isinstance`` and never by
    asking whether it has a ``score`` attribute. A look-alike carrying a plausible number is
    refused, which is the same doctrine
    :class:`~crash_detector.dials.magnitude.DialMagnitude` applies to its own operands.
    """
    # Re-established at the public entry point too, so the id that selects the reading and
    # the id that is stamped on the presentation are the same plain string (CD-AC-005).
    try:
        dial_id = own_str(dial_id)
    except NotEstablishedOnOwnTerms:
        dial_id = ""
    if not dial_id:
        raise DialPresentationRefused(
            f"presenting a dial requires the id of the ONE dial, as a non-empty string; "
            f"got {dial_id!r}."
        )
    for constructor in PRESENTATION_CONSTRUCTORS:
        assert_closed_presentation_surface(constructor)
    return fold(
        reading,
        on_value=lambda seen: _shown_from(dial_id, seen.value),
        on_degraded=lambda seen: _shown_from(dial_id, seen.value),
        on_unknown=lambda seen: NotShown(
            dial_id=dial_id,
            reason=seen.reason,
            missing_inputs=seen.missing_inputs,
        ),
    )


@admits(
    dial_id=str,
    score=ESTABLISHED_HERE(
        "the body below refuses a score whose exact type is not in SCORE_TYPES with the "
        "NAMED error DialPresentationRefused, whose message is the one a consumer reads when "
        "a look-alike carrying a plausible number is offered for presentation (CD-AC-001, "
        "CD-AC-002). An exact-type door here would PREEMPT that named refusal with a generic "
        "NotAdmitted and replace this boundary's own closure with a coarser one — the same "
        "trade admission.py's DECLARED LIMIT 5 records at the three §B.3 doors. CARRIER "
        "MEASURED, by name: tests/test_dial_presentation.py asserts DialPresentationRefused "
        "through present_dial for a look-alike score. This door is decorated for the P7 "
        "property ONLY: a new argument added to it arrives REFUSED, and its type "
        "establishment stays in its body."
    ),
)
def _shown_from(dial_id: str, score: object) -> "Shown":
    """The magnitude a dial score carries, presented for ONE dial.

    **IT IS A DOOR AS OF WO-2R3 INCREMENT 8, BECAUSE THE CRITERION STOPPED MOVING ON AN
    UNDERSCORE** (``PO-DECISIONS-0015`` ruling 1). It returns a ``Shown`` — a judgement value
    — so it is a judgement-path entry point whatever it is spelled, and
    ``from crash_detector.serving.dial_presentation import _shown_from`` is a line anybody can
    write.

    Exact type membership, not ``isinstance`` and not a ``hasattr``: this is a boundary
    through which a value reaches the surface, and a look-alike should not be accepted at
    it.
    """
    # `is_exactly` AND NOT `type(score) not in SCORE_TYPES` (`F-06-D`, WO-2R3 increment 8).
    # **THIS BODY REFUSAL IS WHAT THIS DOOR'S OWN `ESTABLISHED_HERE` REASON NAMES AS THE
    # THING AN EXACT-TYPE DOOR WOULD PREEMPT**, so a declaration citing it had to be a
    # refusal that a caller's metaclass cannot answer. `in` over a tuple is `==` and `==`
    # puts `type(score)` on the LEFT; `is` between two type objects has nothing to
    # delegate. SCORE_TYPES is a TUPLE, which is the container kind that falls to `__eq__`
    # ALONE — a frozenset would also have needed a forged `__hash__`. Both measured.
    if not is_exactly(score, SCORE_TYPES):
        raise DialPresentationRefused(
            f"a {type(score).__name__} was carried by a reading offered for presentation. "
            "A dial is shown from one of the declared dial score types and from nothing "
            "else — a look-alike carrying a plausible number is exactly what a consumer "
            "would build to render an absence as calm (CD-AC-001, CD-AC-002)."
        )
    return Shown(dial_id=dial_id, magnitude=score.score)


@admits(presentation=one_of(*PRESENTATION_CONSTRUCTORS))
def is_shown(presentation: "DialPresentation") -> bool:
    """True only for :class:`Shown`.

    Exact type identity, and the surface is re-verified for a member of the sum type, for
    the reasons :func:`~crash_detector.dials.reading.is_value` gives. A non-member is simply
    not shown; this predicate answers a question and does not police its argument.
    """
    kind = type(presentation)
    if kind not in _CONSTRUCTOR_IDENTITIES:
        return False
    assert_closed_presentation_surface(kind)
    return kind is Shown
