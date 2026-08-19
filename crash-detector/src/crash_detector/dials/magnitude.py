"""``DialMagnitude`` — a dial's number, and which dial it is, as one inseparable thing.

    DialMagnitude := (provenance: exactly one dial id, quantity: a finite float)

PID §3.1 is CONSTITUTIONAL: "Two dials, never blended. Equity crash and monetary/
debasement fail in opposite directions; averaging cancels the signal."

====================================================================================
WHY THIS MODULE EXISTS — closing CD-ASR-F01 (HIGH)
====================================================================================

``EquityCrashScore.score`` and ``MonetaryDebasementScore.score`` used to be plain
``float``. The two score TYPES refused arithmetic with each other, and that refusal was
real; but the moment a caller had hold of two ``float`` values the type system had left
the conversation, and nothing in Python refuses ``(a + b) / 2`` between two floats.

An independent auditor proved it twice, and both blends passed all three of CD-AC-002's
declared layers simultaneously while returning ``0.5`` from equity ``0.9`` and monetary
``0.1`` (`CD-ASR-F01`, escaped variants `E01` and `E02`):

* `E01` put the arithmetic one call away, inside
  ``_fold(left: float, right: float) -> float``. The call expression held both dial
  markers but contained no arithmetic, so the AST check's RULE 1 did not fire; the
  arithmetic sat in a function whose parameters were annotated ``float`` and carried no
  dial flavour.
* `E02` needed no allowlisted path at all: ``_SLOTS = ("equity", "monetary")`` and
  ``[getattr(dials, slot).value.score for slot in _SLOTS]``. **No dial marker appeared in
  any expression**, so nothing was ever flavoured and no rule fired.

The auditor's root cause is decisive for the design: the AST check's flavour propagation
is INTRA-PROCEDURAL by design and purely STATIC, so ``getattr`` with a non-marker string
literal ERASES THE FLAVOUR ENTIRELY. **No amount of hardening a static intra-procedural
checker closes this class**, and this module does not try. The class is closed at the
TYPE and at the PUBLICATION BOUNDARY; the AST scan becomes a locator with a declared
limit (see ``tools/register/check_no_blend.py``).

====================================================================================
THE INVARIANT
====================================================================================

A dial magnitude is a **NOMINAL, PER-DIAL, NON-COERCIBLE** value:

1. **Provenance is carried, not inferred.** Every magnitude holds ``provenance``, a
   ``frozenset`` of dial ids that is **always exactly one element**, because the only
   constructor takes a single ``dial_id``. A magnitude whose provenance names both dials
   is not something this module refuses to build — it is something the signature cannot
   express. "Whose provenance includes both dials" is therefore not a state a
   ``DialMagnitude`` can be in.

2. **Nothing coerces it to a number.** This class defines none of
   :data:`~crash_detector.dials.scores.ARITHMETIC_DUNDERS` — no ``__add__`` family, no
   ``__float__``, ``__int__``, ``__index__``, ``__round__``, no ordering. So
   ``left + right``, ``sum([...])``, ``functools.reduce(operator.add, ...)``,
   ``statistics.mean``, ``math.fsum``, ``json.dumps`` and every other reduction raise
   ``TypeError`` **at runtime, from the interpreter**, regardless of how the two values
   were reached — through an attribute, a ``getattr`` over string slots, a dict, a tuple,
   a comprehension, a helper three calls away, or a route nobody has thought of. That is
   what makes this a CLASS closure rather than a longer list of banned spellings: the
   refusal is a property of the object, and the object does not know or care what
   expression is holding it.

3. **Combination compares provenance, at the point of combination.**
   :func:`combine_within_one_dial` is the declared way to compute a new magnitude from
   existing ones. It unions the provenances and refuses anything but a single dial with
   :exc:`CrossDialCombination`. So a helper written for one dial and then reused across
   both — the shape that arrives innocently — fails when it is reused, not when somebody
   reviews it. **Same-dial computation still works**, which matters: a closure that
   forbids the product is not a closure.

4. **Release names its dial.** :meth:`DialMagnitude.quantity_for` is the ONLY declared
   member that yields a bare ``float``, and it requires the caller to state which single
   dial it expects. A mismatch raises :exc:`CrossDialCombination`. There is no attribute
   on this type holding a bare number: the quantity lives in a private, name-mangled slot
   (``_DialMagnitude__quantity``) which no application module reads.

The attribute surface is **declared, asserted by set equality at import, slotted against
instance injection, and closed against subclassing** — the same four-layer pattern
``crash_detector.dials.reading`` uses for the Reading constructors, and for the same
reason: the question stops being "is this member numeric?" (undecidable in general) and
becomes "is this member DECLARED?" (decided by set equality). The pattern is written out
again here rather than imported from ``reading`` because ``reading``'s declaration is
keyed to the three Reading constructors and generalising it would be an edit to a closure
that has already been accepted (CD-ASR-F02, increment 1).

====================================================================================
WHAT REMAINS OPEN, STATED PLAINLY (CD-RULE-004)
====================================================================================

**A. THE RELEASE IS A REAL DOOR, AND IT IS THE ONLY ONE.** A number has to exist
eventually or nothing can be published. :meth:`quantity_for` is that point, and it can be
called once per dial:

    equity_number = equity_magnitude.quantity_for(EQUITY_DIAL_ID)
    monetary_number = monetary_magnitude.quantity_for(MONETARY_DIAL_ID)
    blended = (equity_number + monetary_number) / 2.0      # ordinary float arithmetic

That last line is not refused by this module and cannot be: they are two ``float``
objects and Python adds floats. What IS true is that (a) no expression reaches it without
naming BOTH dial ids explicitly, which is the thing the AST locator is left to find, and
(b) the result is **unpublishable** — ``crash_detector.publication.dial_scalar`` accepts
only a ``DialMagnitude`` whose provenance is exactly the dial slot it is being written
into, and the closed public envelope schema has no third key for it. Do not read this
module as claiming that no two numbers can ever be added in Python. Read it as claiming
that a dial magnitude cannot be combined with the other dial's magnitude, that reducing
one to a number requires naming its single dial, and that a number so obtained cannot be
published as anything but that dial.

**B. ``object.__setattr__`` REWRITES A SLOT.** As for every frozen dataclass in this
codebase, ``object.__setattr__(m, "provenance", frozenset({"a", "b"}))`` walks past
``__setattr__``. It is worth stating that this direction is SAFE: a forged multi-dial
provenance makes the magnitude LESS usable, not more —
:meth:`quantity_for` compares by set equality and refuses it, the score types refuse to
carry it, and the publication gate refuses to publish it. There is no forgery of
provenance that yields a number.

**C. REFLECTION REACHES THE PAYLOAD, AS IT DOES IN EVERY PYTHON OBJECT.**
``m.__getstate__()``, ``m.__reduce_ex__(2)`` and ``getattr(m, "_DialMagnitude__quantity")``
all return the number at runtime and nothing in Python can prevent them. Two things are
true about that and both are worth writing down. First, the state dict is **keyed by the
private slot names**, so reading it in source requires writing
``state["_DialMagnitude__quantity"]``, which the AST locator's RULE 3 reports — the keys
are part of the closure and are not cosmetic (``CD-ENG-WO2R-F06``, a finding this seat
raised against its own work, is the reason). Second, a revived magnitude goes through the
SAME validation as a constructed one, so reflection is a way of READING the payload and
never a way of forging a magnitude with no provenance, two dials' provenance, or a
non-finite number. This residue is boundary A reached by a different road, and the
publication gate answers it in the same way.

**D. ``repr`` SHOWS THE QUANTITY.** Deliberately. Hiding a value from a developer's own
debugger would be obfuscation, and obfuscation is not structure; CD-RULE-004 prefers a
boundary written down to a boundary made inconvenient. Parsing a number back out of a
repr is boundary A by a longer road.
"""

from __future__ import annotations

import math

__all__ = [
    "ScoreOutOfRange",
    "MagnitudeSurfaceViolated",
    "CrossDialCombination",
    "SealedMagnitudeType",
    "DialMagnitude",
    "DECLARED_MAGNITUDE_MEMBERS",
    "TOLERATED_INTERPRETER_MACHINERY",
    "combine_within_one_dial",
    "require_finite_float",
    "sole_dial_of",
]


class ScoreOutOfRange(ValueError):
    """A dial magnitude that is not a finite float.

    Refused at construction rather than clamped. A clamped score is a wrong number that
    looks like a right one.

    It lives in this module rather than in :mod:`crash_detector.dials.scores` because
    this is now the module that owns what a magnitude IS. ``scores`` re-exports it, so
    every existing import site is unchanged.
    """


class MagnitudeSurfaceViolated(TypeError):
    """:class:`DialMagnitude`'s attribute surface is not the declared one.

    A ``TypeError`` because what is wrong is the *type*, not a value someone passed.
    """


class CrossDialCombination(TypeError):
    """Two dials' magnitudes were combined, or a magnitude was read as the wrong dial.

    A ``TypeError`` on purpose. PID §3.1 says the two dials are different *kinds* of
    thing, and asking for a number out of one while naming the other is a category error
    rather than a bad value. It also means the refusal answers to the same
    ``pytest.raises(TypeError)`` as the interpreter's own refusal of ``equity + monetary``,
    so a caller cannot tell the two apart and cannot come to depend on the difference.
    """


#: Names CPython's own ``type`` machinery may add to a class dictionary depending on
#: interpreter patch level. Enumerated with intent, and none of them can carry a number.
#: ``__dict__`` is deliberately NOT tolerated: a class that grows a ``__dict__``
#: descriptor has re-opened instance attribute injection.
#:
#: ``__getstate__`` and ``__setstate__`` are deliberately NOT tolerated here, unlike in
#: ``reading``: this type DEFINES both, so they are DECLARED members and are asserted by
#: equality like every other. A tolerated member is one the interpreter may or may not
#: add; a declared one is one this module is answerable for.
TOLERATED_INTERPRETER_MACHINERY: frozenset = frozenset(
    {
        "__replace__",
        "__weakref__",
        "__firstlineno__",
        "__static_attributes__",
    }
)

#: THE COMPLETE DECLARED ATTRIBUTE SURFACE of :class:`DialMagnitude`, asserted by set
#: EQUALITY at import — not by the absence of a blacklist, because a blacklist cannot see
#: a member nobody listed. That lesson is CD-ASR-F02's and it is applied here before
#: anybody has to learn it twice. ``tests/test_dial_provenance.py`` carries its own
#: independent copy and asserts the two agree, so widening this declaration fails the
#: declared test rather than widening the guard.
DECLARED_MAGNITUDE_MEMBERS: frozenset = frozenset(
    {
        "__doc__",
        "__module__",
        "__slots__",
        "_DialMagnitude__quantity",
        "provenance",
        "__init__",
        "__setattr__",
        "__delattr__",
        "__eq__",
        "__ne__",
        "__hash__",
        "__repr__",
        "__getstate__",
        "__setstate__",
        "quantity_for",
    }
)

_SEALED: set = set()


class SealedMagnitudeType(type):
    """The metaclass that closes :class:`DialMagnitude` against extension.

    A metaclass rather than a base class, for the reason
    :class:`~crash_detector.dials.reading.SealedReadingType` gives: a shared base is
    somewhere a coercion could be added once and inherited. A metaclass member is
    reachable on the class object and NOT on an instance, so ``magnitude.anything``
    cannot resolve through it.

    Subclassing is refused rather than policed because a subclass carrying ``__float__``
    would be accepted everywhere a magnitude is accepted while passing every check aimed
    at the declared class.
    """

    def __new__(mcls, name, bases, namespace, **kwargs):
        for base in bases:
            if isinstance(base, SealedMagnitudeType):
                raise MagnitudeSurfaceViolated(
                    f"{name} may not subclass {base.__name__}: a dial magnitude is a "
                    "CLOSED type. A subclass carrying an arithmetic or coercion dunder "
                    "would be accepted everywhere a magnitude is accepted, which is the "
                    "CD-ASR-F01 route from two dials to one number."
                )
        return super().__new__(mcls, name, bases, namespace, **kwargs)

    def __setattr__(cls, name: str, value: object) -> None:
        if cls in _SEALED:
            raise MagnitudeSurfaceViolated(
                f"cannot set {cls.__name__}.{name}: the dial magnitude type is SEALED. "
                "Its attribute surface is declared in DECLARED_MAGNITUDE_MEMBERS, and "
                "adding a member — an arithmetic dunder, a coercion, a property that "
                "returns the number, or anything else — is the CD-ASR-F01 route."
            )
        type.__setattr__(cls, name, value)

    def __delattr__(cls, name: str) -> None:
        if cls in _SEALED:
            raise MagnitudeSurfaceViolated(
                f"cannot delete {cls.__name__}.{name}: the dial magnitude type is "
                "SEALED. Removing the member that does the refusing changes the surface "
                "as much as adding one, and the surface is asserted by equality."
            )
        type.__delattr__(cls, name)


def require_finite_float(type_name: str, field_name: str, observed: object) -> None:
    """Refuse anything that is not a finite float.

    ``bool`` is refused explicitly, ahead of the ``float`` test, because ``True`` would
    otherwise slip through any ``int``-tolerant path and become ``1.0``.

    **No range is imposed, and that is a refusal rather than an omission.** A declared
    range is a declared scale, and the scale of a dial is what the dial *means* —
    CD-D-005, owed by the Product Owner (BLUEPRINT §16), and inventing one here would be
    inventing product meaning (``PBG-AUTH-005``, CD-RULE-003). What is validated is the
    class of thing, never its meaning. This increment changed the TYPE of a magnitude and
    how it composes; it decided nothing about what a magnitude means.
    """
    if isinstance(observed, bool) or not isinstance(observed, float):
        raise ScoreOutOfRange(
            f"{type_name}.{field_name} must be a float, got {type(observed).__name__}"
        )
    if not math.isfinite(observed):
        raise ScoreOutOfRange(
            f"{type_name}.{field_name} must be finite, got {observed!r}"
        )


def _install(instance: object, dial_id: object, quantity: object) -> None:
    """Validate and write a magnitude's two slots. THE ONLY place either is written.

    A module function rather than a method, for two reasons. It is the shared path for
    construction and for revival from a pickle or a copy, so neither can be validated more
    loosely than the other; and it is not a member of :class:`DialMagnitude`, so it does
    not widen the declared attribute surface.
    """
    if not isinstance(dial_id, str) or not dial_id:
        raise CrossDialCombination(
            "a dial magnitude requires the id of the ONE dial it came from, as a "
            f"non-empty string; got {dial_id!r}. Provenance is carried as data rather "
            "than inferred from the code around the number, so that a cross-dial "
            "combination is refused by comparing values and not by anybody having read "
            "the expression (CD-ASR-F01)."
        )
    require_finite_float("DialMagnitude", "quantity", quantity)
    object.__setattr__(instance, "provenance", frozenset({dial_id}))
    object.__setattr__(instance, "_DialMagnitude__quantity", quantity)


class DialMagnitude(metaclass=SealedMagnitudeType):
    """One dial's magnitude, inseparable from which dial it is.

    Written by hand rather than as a ``dataclass`` for one reason: the number must not be
    a public field. A dataclass would put it in ``__init__``'s signature, in ``repr``'s
    field list and — decisively — in an attribute any caller can read without saying
    which dial they think they are reading. Here the quantity lives in a name-mangled
    slot and the only declared way out is :meth:`quantity_for`, which takes the dial id
    the caller expects and refuses a mismatch.
    """

    __slots__ = ("provenance", "__quantity")

    def __init__(self, *, dial_id: str, quantity: float) -> None:
        """Build a magnitude for ONE dial.

        Keyword-only, so a call site always reads ``dial_id=...``; and there is no
        constructor that takes a set of dials, which is why a multi-dial provenance is
        not a state this type can be in.
        """
        _install(self, dial_id, quantity)

    # -- immutability -------------------------------------------------------------- #

    def __setattr__(self, name: str, value: object) -> None:
        raise MagnitudeSurfaceViolated(
            f"cannot set {type(self).__name__}.{name}: a dial magnitude is immutable, "
            "and its provenance in particular is the evidence that it belongs to one "
            "dial. Build a new magnitude, or combine within one dial with "
            "combine_within_one_dial()."
        )

    def __delattr__(self, name: str) -> None:
        raise MagnitudeSurfaceViolated(
            f"cannot delete {type(self).__name__}.{name}: a magnitude without its "
            "provenance is a bare number, which is the thing this type exists to "
            "prevent."
        )

    # -- copying and pickling -------------------------------------------------------- #

    def __getstate__(self) -> dict:
        """The state a copy or a pickle carries, KEYED BY THE PRIVATE SLOT NAMES.

        Defined because ``copy.deepcopy`` and ``pickle`` restore a slotted object by
        calling ``setattr``, which this type refuses. Without these two the round trip
        would raise, and refusing to copy a reading is an accidental restriction on the
        product rather than a property CD-AC-002 asks for.

        **THE KEY NAMES ARE PART OF THE CLOSURE AND ARE NOT COSMETIC.** This seat's first
        draft returned ``{"dial_id": ..., "quantity": ...}``, and this seat then found the
        escape that follows and recorded it as a finding against its own work
        (`CD-ENG-WO2R-F06`):

            states = [m.__getstate__() for m in (equity_magnitude, monetary_magnitude)]
            blended = sum(s["quantity"] for s in states) / len(states)   # -> 0.5

        That reached the number **without naming a dial and without naming the private
        slot**, so nothing refused it and RULE 3 of the AST locator had nothing to see.
        Keying the state by the slot names means the same expression must now be written
        ``s["_DialMagnitude__quantity"]``, which RULE 3 reports as a string constant
        exactly as it reports the attribute. The runtime residue is unchanged and is
        declared: reflection reaches the payload, as it does in every Python object.
        """
        return {
            "provenance": self.provenance,
            "_DialMagnitude__quantity": self._DialMagnitude__quantity,
        }

    def __setstate__(self, state) -> None:
        """Rebuild from state, through THE SAME validation the constructor uses.

        A revived magnitude is validated exactly as a constructed one, so a hand-written
        pickle cannot forge a magnitude with no provenance, with two dials' provenance, or
        with a non-finite number. A round trip through ``copy`` or ``pickle`` is therefore
        not a laundering route: what comes back is a magnitude of one dial, still refusing
        arithmetic with the other.
        """
        provenance = state["provenance"]
        if not isinstance(provenance, frozenset) or len(provenance) != 1:
            raise CrossDialCombination(
                f"a magnitude cannot be revived with provenance {provenance!r}: it must "
                "be exactly one dial. A pickle is untrusted input like any other, and a "
                "revived magnitude is validated exactly as a constructed one."
            )
        _install(self, sorted(provenance)[0], state["_DialMagnitude__quantity"])

    # -- identity ------------------------------------------------------------------- #

    def __eq__(self, other: object) -> bool:
        """Equal only to a magnitude of the SAME dial with the same quantity.

        Deliberately NOT equal to a bare ``float``. Equality with a number would be a
        coercion by another name, and it would make ``0.5 in (equity, monetary)`` answer
        a question about arithmetic.
        """
        if type(other) is not DialMagnitude:
            return NotImplemented
        return (
            self.provenance == other.provenance
            and self._DialMagnitude__quantity == other._DialMagnitude__quantity
        )

    def __ne__(self, other: object) -> bool:
        answer = self.__eq__(other)
        if answer is NotImplemented:
            return NotImplemented
        return not answer

    def __hash__(self) -> int:
        return hash((frozenset(self.provenance), self._DialMagnitude__quantity))

    def __repr__(self) -> str:
        return (
            f"DialMagnitude(dial_id={sorted(self.provenance)[0]!r}, "
            f"quantity={self._DialMagnitude__quantity!r})"
        )

    # -- the one declared release ---------------------------------------------------- #

    def quantity_for(self, dial_id: str) -> float:
        """The bare number, for a caller that names the single dial it expects.

        The ONLY declared member of this type that yields a ``float``. It compares
        provenance by SET EQUALITY, so a magnitude of the other dial, a magnitude whose
        provenance was forged to name two dials, and a magnitude of a dial that does not
        exist are all refused identically — the refusal is a comparison of data and does
        not depend on anyone having read the surrounding code.

        This is boundary A of this module's declared limit. Two numbers released this way
        can be added by ordinary Python arithmetic; what closes that is the publication
        gate and the closed envelope schema, not this method.
        """
        if self.provenance != frozenset({dial_id}):
            raise CrossDialCombination(
                f"this magnitude's provenance is {sorted(self.provenance)}, and the "
                f"caller asked for it as {dial_id!r}. A dial magnitude is released as a "
                "number only to a caller that names its ONE dial: PID §3.1 says the two "
                "dials fail in opposite directions and averaging cancels the signal, so "
                "a number whose dial is in doubt has already lost the property that "
                "makes it worth publishing (CD-AC-002, CD-ASR-F01)."
            )
        return self._DialMagnitude__quantity


def _assert_declared_surface(cls: type) -> None:
    """Raise unless ``cls``'s class dictionary is exactly the declared surface."""
    observed = frozenset(vars(cls))
    unexpected = observed - DECLARED_MAGNITUDE_MEMBERS - TOLERATED_INTERPRETER_MACHINERY
    missing = DECLARED_MAGNITUDE_MEMBERS - observed
    breaches = []
    if unexpected:
        breaches.append(
            f"{cls.__name__} carries undeclared member(s) {sorted(unexpected)}. The "
            "surface is declared and asserted by equality, so this is a breach whether "
            "or not the member looks numeric (CD-ASR-F01)."
        )
    if missing:
        breaches.append(
            f"{cls.__name__} is missing declared member(s) {sorted(missing)}. Removing "
            "the member that does the refusing changes the surface as much as adding "
            "one."
        )
    if breaches:
        raise MagnitudeSurfaceViolated(" ".join(breaches))


_assert_declared_surface(DialMagnitude)
if DialMagnitude.__dictoffset__:
    raise MagnitudeSurfaceViolated(
        "DialMagnitude instances carry a __dict__ despite __slots__, so instance "
        "attribute injection is open and a coercion could be attached to one instance."
    )
_SEALED.add(DialMagnitude)


def sole_dial_of(magnitude: "DialMagnitude") -> str:
    """The one dial a magnitude came from.

    Refuses anything that is not exactly a :class:`DialMagnitude` — exact type identity,
    not ``isinstance``, for the reason :func:`~crash_detector.dials.reading.fold` gives:
    this is a boundary through which a magnitude reaches a consumer, and a look-alike
    should not be accepted at it. It also re-verifies the class surface, because
    ``type.__setattr__`` can install a member on a class object without going through the
    metaclass and no Python-level structure can prevent that.
    """
    if type(magnitude) is not DialMagnitude:
        raise CrossDialCombination(
            f"not a dial magnitude: {type(magnitude).__name__}. A bare number has no "
            "provenance, and a number without provenance is exactly what CD-AC-002 "
            "forbids being published."
        )
    _assert_declared_surface(DialMagnitude)
    if len(magnitude.provenance) != 1:
        raise CrossDialCombination(
            f"this magnitude's provenance is {sorted(magnitude.provenance)}, which is "
            "not exactly one dial. A scalar derived from both dials is what PID §3.1 "
            "forbids; it has no single dial to be published as."
        )
    return sorted(magnitude.provenance)[0]


def combine_within_one_dial(magnitudes, *, using) -> "DialMagnitude":
    """Compute a new magnitude from magnitudes that all came from the SAME dial.

    THE POINT OF COMBINATION, and therefore the place provenance is compared. ``using``
    receives a tuple of the released numbers, in the order given, and returns one float.

    Legitimate same-dial work still works — a rolling mean of one dial over time, a
    weighted recomputation, a maximum over a window — and that matters as much as the
    refusal: a closure that forbids the product is not a closure.

    What is refused is the shape that arrives innocently: a helper written for one dial
    and later reused across both. It fails when it is REUSED, at runtime, by comparing
    the provenance data it was handed — not when somebody reviews the code, and not
    because the expression happened to name a dial.
    """
    ordered = tuple(magnitudes)
    if not ordered:
        raise CrossDialCombination(
            "combine_within_one_dial() requires at least one magnitude. A magnitude "
            "computed from nothing is a number nobody computed, which CD-AC-001 refuses "
            "as surely as CD-AC-002 refuses a blend."
        )
    dials = frozenset(sole_dial_of(magnitude) for magnitude in ordered)
    if len(dials) != 1:
        raise CrossDialCombination(
            f"refusing to combine magnitudes from {sorted(dials)}. PID §3.1 is "
            "CONSTITUTIONAL: the two dials fail in opposite directions and averaging "
            "cancels the signal. This refusal compares the provenance the magnitudes "
            "CARRY, so it holds however the values were reached — through an attribute, "
            "a getattr over string slots, a dict, a comprehension, or a helper several "
            "calls away (CD-ASR-F01)."
        )
    dial_id = sorted(dials)[0]
    numbers = tuple(magnitude.quantity_for(dial_id) for magnitude in ordered)
    return DialMagnitude(dial_id=dial_id, quantity=using(numbers))
