"""``DeclaredQuantity`` — a number that carries where it came from, or it is not admitted.

    DeclaredQuantity := (dials: exactly one dial id, value: a finite float)

PID §3.1 is CONSTITUTIONAL: "Two dials, never blended. Equity crash and monetary/
debasement fail in opposite directions; averaging cancels the signal."

====================================================================================
WHY THIS MODULE EXISTS — closing CD-PL-F54, re-opening and closing CD-ASR-F01 (HIGH)
====================================================================================

Increment 2 made a dial magnitude NOMINAL and NON-COERCIBLE. That worked, and it is kept:
the Project Lead re-ran eleven probes against it and nine were refused, including every
alternate coercion protocol it tried — ``math.fsum``, ``round``, ``operator.index``,
``Decimal``, ``int``, ``complex``, ``__format__`` and ``str``-then-``float``. **The type is
closed against being ASKED for a number.**

It was not closed against THE NUMBER BEING READ OFF IT:

    float(repr(m).split("quantity=")[1].rstrip(")"))

That names no dial, asks the type for nothing, and yields the bare quantity. Two of those
add. Re-wrapped as ``DialMagnitude(dial_id="equity_crash", quantity=<the blend>)`` the
result's provenance IS exactly one dial, so every provenance comparison increment 2 built
passes it — and it publishes. The Project Lead measured it three ways (`PL-Q4`, `PL-Q5`,
`PL-Q6`) and then wrote one plausible module (`PL-Q9`) that defeated the static arm and the
runtime arm together: ``check_no_blend`` PASS on 3919 assertions with zero violations, and
at runtime ``EquityCrashScore(score=DialMagnitude(dial_id='equity_crash', quantity=0.5))``
out of a 0.4 equity reading and a 0.6 monetary one.

====================================================================================
WHY THE EXITS ARE NOT THE PLACE TO FIX IT
====================================================================================

The tempting repair is to stop ``repr`` rendering a parseable float. **That is the
instance game again**, and this seat rejects it for a reason it can state:

``repr`` is one spelling of an exit class that has no last member. ``str``, ``format``,
an f-string, ``%``-formatting, ``pprint``, a log line, a traceback, ``json.dumps`` over
``__getstate__``, the bytes of a ``pickle``, ``vars()``, ``gc.get_referents`` — every one
of them renders or reaches the payload, and Python cannot be made to stop. Closing
``repr`` would move the same attack one line sideways and would cost a developer their
debugger, which is a real cost paid for nothing. **Any float that has left a magnitude has
lost its dial, and no downstream layer can recover it.**

So the closure is at the RE-ENTRY, not at the exit. The question stops being
"is this number blended?", which is undecidable, and becomes

    "is this number's provenance DECLARED?"

which is decided by SET EQUALITY — the same move increment 1 made for absence and
increment 2 made for combination, applied to the one step both of them left open.

====================================================================================
THE INVARIANT
====================================================================================

1. **A BARE ``float`` CANNOT BECOME A DIAL MAGNITUDE.** ``DialMagnitude``'s constructor
   admits a :class:`DeclaredQuantity` and nothing else. Every laundering route — ``repr``,
   ``str``, ``format``, JSON, a pickle's bytes, ``getattr`` on the private slot,
   ``__getstate__``, a number recovered from a log — ends holding a ``float``, and a
   ``float`` has no provenance. It is therefore not a value the constructor can accept,
   whatever it is worth and however it was obtained.

2. **A DECLARED QUANTITY CANNOT BE MADE BY ARITHMETIC.** This type defines none of
   :data:`~crash_detector.dials.scores.ARITHMETIC_DUNDERS` either, so two declared
   quantities cannot be added, averaged, summed or reduced into a third. There is no
   expression that produces a ``DeclaredQuantity`` from two of them.

3. **THERE ARE EXACTLY TWO DOORS INTO THE TYPE, AND BOTH DECLARE A DIAL AS DATA.**

   * :func:`observed_for_dial` — a number entering from OUTSIDE the system, admitted for
     ONE named dial, citing the non-empty set of ingredient sources it was computed from.
     This is the base case: something has to be the first number or the product cannot
     exist. It is a DECLARATION, and its residue is declared in full below.
   * :func:`~crash_detector.dials.magnitude.combine_within_one_dial` — a number DERIVED
     from magnitudes already in hand. Its dial set is the UNION of theirs, computed by the
     machinery from data the caller had to be holding, never asserted by the caller; a
     union of size other than one is refused.

4. **CONSTRUCTION COMPARES THE DECLARATION TO THE TARGET BY SET EQUALITY.**
   ``DialMagnitude(dial_id=D, quantity=q)`` requires ``q.dials == frozenset({D})``. Not a
   subset, not an intersection, not "contains". A quantity declared for the other dial, for
   both dials, or for a dial that does not exist is refused identically, by comparing
   values.

**WHY THAT IS A CLASS CLOSURE.** It does not enumerate laundering routes and it does not
need to know one existed. It removes the destination they all share. A route this seat has
not thought of, arriving through a protocol this seat has not heard of, still ends with a
``float`` in somebody's hand — and the ``float`` is the thing that cannot get in.

====================================================================================
WHAT REMAINS OPEN, STATED PLAINLY (CD-RULE-004, CD-RULE-006)
====================================================================================

**THE ADMISSION DOOR IS A DECLARATION, AND A DECLARATION CAN BE FALSE.** A module holding a
blended float may call

    observed_for_dial(dial_id="equity_crash", quantity=blended, inputs_used=("banner",))

and obtain a quantity declared for one dial. Nothing at runtime can distinguish that from a
genuine first measurement, because at the bottom of any provenance chain there is an
assertion that a number came from outside; a base case that had to prove itself would need
a base case of its own. **This seat does not claim to have closed it and does not hand it to
a layer without measuring that layer.**

What is true, and is the difference between this and the state the Project Lead measured:

* it is no longer a COMPOSITION ACCIDENT. `PL-Q9` was one ordinary-looking helper that read
  numbers and re-wrapped them; the same module must now write an explicit false statement
  about where its number came from, naming a dial and naming sources it did not use;
* the flavour `PL-Q9` removed is FORCED BACK INTO THE SOURCE. Its whole strength was that
  no dial name appeared anywhere. A caller of this door must name one;
* it is caught STATICALLY by deny-by-default. ``tools/register/check_no_blend.py`` RULE 4
  admits a reference to this door only from the declared admission sites listed there, and
  reports every other reference on the scanned path as a violation — without needing to
  recognise arithmetic, a dial marker, or anything about how the number was obtained.
  MEASURED: `V12` and `V13` in ``variants/WO-2R/CD-ASR-F01/``.

The residue of THAT is the residue of any registry: an edit to the declared admission list
itself, and a module outside the scanned set. Both are boundaries 4 and 7 of the check's
own declared limit, and neither is claimed to be carried anywhere else.

**``object.__setattr__`` REWRITES A SLOT**, here as on every frozen object in Python, and the
two directions differ.

Forging ``dials`` is SAFE for the same reason it is safe on a magnitude: it makes the
quantity LESS usable. :meth:`DeclaredQuantity.value_for` compares by set equality and refuses
it, and so does the magnitude constructor.

Forging ``_DeclaredQuantity__value`` IS NOT SAFE, and this seat raised it against its own
work (``CD-ENG-WO2R-F11``). Rewriting the number IN PLACE on the quantity a live magnitude
already holds never constructs anything, so the re-entry closure is never reached. MEASURED
as `V17`: NOT refused at runtime; the magnitude then reads the blend. **NO RUNTIME LAYER
CARRIES THIS AND NONE IS CLAIMED TO** (CD-RULE-006). RULE 3 of
``tools/register/check_no_blend.py`` carries it statically — reaching either private slot on
the scanned path is a violation with no allowlist beyond each declaring module, and `V17`
produces six of them — and no Python-level structure can prevent an in-place slot rewrite.
"""

from __future__ import annotations

import enum
import math
from types import MappingProxyType

__all__ = [
    "ScoreOutOfRange",
    "CrossDialCombination",
    "QuantityProvenanceMissing",
    "QuantitySurfaceViolated",
    "UndeclaredReduction",
    "SealedQuantityType",
    "DeclaredQuantity",
    "DECLARED_QUANTITY_MEMBERS",
    "TOLERATED_QUANTITY_MACHINERY",
    "SameDialReduction",
    "SAME_DIAL_REDUCTIONS",
    "observed_for_dial",
    "derived_within_one_dial",
    "require_finite_float",
]


class ScoreOutOfRange(ValueError):
    """A dial magnitude that is not a finite float.

    Refused at construction rather than clamped. A clamped score is a wrong number that
    looks like a right one.

    It lives in THIS module, and is re-exported by
    :mod:`crash_detector.dials.magnitude` and :mod:`crash_detector.dials.scores` so that
    every existing import site is unchanged, because this is now the module that owns what
    an admissible NUMBER is. ``magnitude`` owns what a magnitude is; this owns what may be
    inside one.
    """


class CrossDialCombination(TypeError):
    """Two dials' numbers met, or a number was read as the wrong dial.

    A ``TypeError`` on purpose. PID §3.1 says the two dials are different *kinds* of thing,
    so asking for one while naming the other is a category error rather than a bad value.
    It also means the refusal answers to the same ``pytest.raises(TypeError)`` as the
    interpreter's own refusal of ``equity + monetary``, so a caller cannot tell the two
    apart and cannot come to depend on the difference.
    """


class QuantityProvenanceMissing(CrossDialCombination):
    """A bare number was offered where a number with a declared provenance is required.

    A subclass of :exc:`CrossDialCombination` — and therefore of ``TypeError`` — because
    it is the same category error one step earlier. A ``float`` with no dial is not a
    number belonging to the wrong dial; it is a number belonging to no dial, which is
    exactly what a blend becomes the moment it is computed. A caller catching the
    cross-dial refusal catches this too and cannot come to treat re-entry as the lenient
    boundary.
    """


class QuantitySurfaceViolated(TypeError):
    """:class:`DeclaredQuantity`'s attribute surface is not the declared one."""


class UndeclaredReduction(CrossDialCombination):
    """A derivation was asked for by something that is not a declared reduction.

    A subclass of :exc:`CrossDialCombination` — and therefore of ``TypeError`` — because it
    is the same category error a third time: a caller's own callable is not a reduction
    this system can account for, and a number it returns is a number this system did not
    compute. Everything this module refuses answers to one name, so a caller cannot come to
    treat any one of these boundaries as the lenient one.

    Added at CD-ASR-WO2R-F01. `ASR2-002-A` handed :func:`derived_within_one_dial` the return
    value of ``lambda _released: carried`` and the door took it, because the door validated
    the DIAL SET it was given and never the VALUE. A callable is refused here BY EXACT TYPE,
    which is a comparison of what the door was handed and not of what it was called.
    """


#: Names CPython's own ``type`` machinery may add to a class dictionary depending on
#: interpreter patch level. Enumerated with intent, and none of them can carry a number.
#: ``__dict__`` is deliberately NOT tolerated: a class that grows a ``__dict__`` descriptor
#: has re-opened instance attribute injection.
TOLERATED_QUANTITY_MACHINERY: frozenset = frozenset(
    {
        "__replace__",
        "__weakref__",
        "__firstlineno__",
        "__static_attributes__",
    }
)

#: THE COMPLETE DECLARED ATTRIBUTE SURFACE of :class:`DeclaredQuantity`, asserted by set
#: EQUALITY at import — not by the absence of a blacklist, because a blacklist cannot see a
#: member nobody listed (CD-ASR-F02's lesson, applied here before anybody has to learn it a
#: third time). ``tests/test_dial_provenance.py`` carries its own independent copy and
#: asserts the two agree, so widening this declaration fails a declared register test
#: rather than widening the guard.
DECLARED_QUANTITY_MEMBERS: frozenset = frozenset(
    {
        "__doc__",
        "__module__",
        "__slots__",
        "_DeclaredQuantity__value",
        "dials",
        "__init__",
        "__setattr__",
        "__delattr__",
        "__eq__",
        "__ne__",
        "__hash__",
        "__repr__",
        "__getstate__",
        "__setstate__",
        "value_for",
    }
)

_SEALED: set = set()


class SealedQuantityType(type):
    """The metaclass that closes :class:`DeclaredQuantity` against extension.

    A metaclass rather than a base class, for the reason
    :class:`~crash_detector.dials.magnitude.SealedMagnitudeType` gives: a shared base is
    somewhere a coercion could be added once and inherited, and a metaclass member is
    reachable on the class object and NOT on an instance, so ``quantity.anything`` cannot
    resolve through it.

    Subclassing is refused rather than policed. A subclass declaring two dials, or
    carrying an ``__add__`` that unions provenance quietly, would be accepted everywhere a
    declared quantity is accepted — except that the magnitude constructor tests EXACT type
    identity, which is the second instrument over the same route.
    """

    def __new__(mcls, name, bases, namespace, **kwargs):
        for base in bases:
            if isinstance(base, SealedQuantityType):
                raise QuantitySurfaceViolated(
                    f"{name} may not subclass {base.__name__}: a declared quantity is a "
                    "CLOSED type. The whole of its value is that its provenance was "
                    "established by one of two declared doors, and a subclass is a third "
                    "door nobody declared (CD-ASR-F01, CD-PL-F54)."
                )
        return super().__new__(mcls, name, bases, namespace, **kwargs)

    def __setattr__(cls, name: str, value: object) -> None:
        if cls in _SEALED:
            raise QuantitySurfaceViolated(
                f"cannot set {cls.__name__}.{name}: the declared quantity type is SEALED. "
                "Its attribute surface is declared in DECLARED_QUANTITY_MEMBERS, and "
                "adding a member — an arithmetic dunder that unions two provenances, a "
                "coercion, a constructor that takes a dial set — is the CD-ASR-F01 route."
            )
        type.__setattr__(cls, name, value)

    def __delattr__(cls, name: str) -> None:
        if cls in _SEALED:
            raise QuantitySurfaceViolated(
                f"cannot delete {cls.__name__}.{name}: the declared quantity type is "
                "SEALED. Removing the member that does the refusing changes the surface "
                "as much as adding one, and the surface is asserted by equality."
            )
        type.__delattr__(cls, name)


def require_finite_float(type_name: str, field_name: str, observed: object) -> None:
    """Refuse anything that is not a finite float.

    ``bool`` is refused explicitly, ahead of the ``float`` test, because ``True`` would
    otherwise slip through any ``int``-tolerant path and become ``1.0``.

    **No range is imposed, and that is a refusal rather than an omission.** A declared
    range is a declared scale, and the scale of a dial is what the dial *means* — CD-D-005,
    owed by the Product Owner (BLUEPRINT §16), and inventing one here would be inventing
    product meaning (``PBG-AUTH-005``, CD-RULE-003). What is validated is the class of
    thing, never its meaning.
    """
    if isinstance(observed, bool) or not isinstance(observed, float):
        raise ScoreOutOfRange(
            f"{type_name}.{field_name} must be a float, got {type(observed).__name__}"
        )
    if not math.isfinite(observed):
        raise ScoreOutOfRange(
            f"{type_name}.{field_name} must be finite, got {observed!r}"
        )


class SameDialReduction(enum.Enum):
    """THE CLOSED SET OF WAYS SEVERAL NUMBERS OF ONE DIAL BECOME ONE NUMBER OF THAT DIAL.

    A caller of :func:`derived_within_one_dial` names a reduction; it does not supply one.
    That is the whole of the CD-ASR-WO2R-F01 closure at this door, and the difference is
    structural rather than stylistic:

    * a caller-supplied callable returns a number **this system did not compute**, and no
      layer downstream can tell such a number from a derivation. `ASR2-002-A` closed over
      the other dial's released figure and returned it from a one-line ``lambda``; the door
      stamped this dial's provenance onto it and it published as an equity 0.5 out of an
      equity 0.9 and a monetary 0.1;
    * a NAMED reduction is executed by this module over numbers this module released from
      quantities whose provenance this module established. There is no argument through
      which a caller's number can arrive, so there is nothing for a door to fail to
      validate.

    An :class:`enum.Enum` because an enum with members is closed against subclassing by the
    interpreter and its members cannot be added to after class creation, so the set is
    closed by the language rather than by a check. A reduction this product later needs is
    added HERE, deliberately and visibly, and it still cannot take a caller's number.

    **NO WEIGHTED REDUCTION IS SHIPPED, AND THAT IS A REFUSAL RATHER THAN AN OMISSION.**
    Weights are product meaning — the relative worth of one observation against another —
    and CD-D-005 is owed by the Product Owner. Inventing them here would be inventing a
    product quantity (CD-RULE-003, ``PBG-AUTH-005``). A weighted derivation fails closed.
    """

    MEAN = "mean"
    SUM = "sum"
    MAX = "max"
    MIN = "min"


def _mean(values: tuple) -> float:
    return math.fsum(values) / len(values)


def _sum(values: tuple) -> float:
    return math.fsum(values)


def _max(values: tuple) -> float:
    return max(values)


def _min(values: tuple) -> float:
    return min(values)


#: Each declared reduction and the implementation THIS MODULE runs for it. Asserted by set
#: EQUALITY against the enum at import, in both directions, for the reason every other
#: declaration in this package is: a member with no implementation would raise at the worst
#: possible moment, and an implementation with no member would be a fifth reduction nobody
#: declared.
#:
#: **A ``MappingProxyType`` OVER A DICT WITH NO OTHER REFERENCE, and this seat found the
#: reason against its own work** (`CD-ENG-WO2R2-V03`). A plain dict here would have been a
#: door of exactly the kind this increment exists to close, one storey up: the door refuses
#: a caller's callable, and the caller then writes its callable INTO the table the door
#: trusts — ``SAME_DIAL_REDUCTIONS[SameDialReduction.MEAN] = lambda values: <a blend>`` —
#: and every refusal below then runs the attacker's code with the door's own blessing. The
#: dict literal is consumed by ``MappingProxyType`` at module level and is never bound to a
#: name, so there is no reference to the underlying mapping to reach by name at all.
#: MEASURED both ways as `CD-ENG-WO2R2-V03`.
SAME_DIAL_REDUCTIONS = MappingProxyType(
    {
        SameDialReduction.MEAN: _mean,
        SameDialReduction.SUM: _sum,
        SameDialReduction.MAX: _max,
        SameDialReduction.MIN: _min,
    }
)

if frozenset(SAME_DIAL_REDUCTIONS) != frozenset(SameDialReduction):
    raise UndeclaredReduction(
        "SAME_DIAL_REDUCTIONS and SameDialReduction disagree about which reductions this "
        "module implements. The two are asserted by set equality because a declared "
        "reduction with no implementation and an implementation with no declaration are "
        "the same defect seen from opposite sides."
    )


def _install(instance: object, dials: object, value: object) -> None:
    """Validate and write a declared quantity's two slots. THE ONLY place either is written.

    A module function rather than a method, for two reasons. It is the shared path for
    construction and for revival from a pickle or a copy, so neither can be validated more
    loosely than the other; and it is not a member of :class:`DeclaredQuantity`, so it does
    not widen the declared attribute surface.
    """
    if not isinstance(dials, frozenset) or len(dials) != 1:
        raise CrossDialCombination(
            f"a declared quantity carries the provenance of EXACTLY ONE dial; got "
            f"{dials!r}. A number derived from both dials has no single dial to be "
            "published as, and PID §3.1 admits no third figure derived from the two."
        )
    only = next(iter(dials))
    if not isinstance(only, str) or not only:
        raise CrossDialCombination(
            f"a dial id must be a non-empty string; got {only!r}."
        )
    require_finite_float("DeclaredQuantity", "value", value)
    object.__setattr__(instance, "dials", frozenset(dials))
    object.__setattr__(instance, "_DeclaredQuantity__value", value)


class DeclaredQuantity(metaclass=SealedQuantityType):
    """A number and the dial its derivation touched, inseparable.

    **NOT CONSTRUCTED DIRECTLY BY APPLICATION CODE.** The constructor is private by
    convention and by the register check that guards it; the two declared doors are
    :func:`observed_for_dial` and
    :func:`~crash_detector.dials.magnitude.combine_within_one_dial`. It is written by hand
    rather than as a ``dataclass`` for the reason
    :class:`~crash_detector.dials.magnitude.DialMagnitude` gives: a dataclass would put the
    number in an attribute any caller can read without saying which dial it thinks it is
    reading.

    It defines no arithmetic and no coercion, so no expression in Python produces a third
    declared quantity from two of them. That is what stops the type becoming a laundering
    vehicle of its own.
    """

    __slots__ = ("dials", "__value")

    def __init__(self, *arguments, **keywords) -> None:
        """REFUSES, ALWAYS. Direct construction is not a door (CD-ASR-WO2R-F01).

        Until this commit the signature was ``(*, dials: frozenset, value: float)``, and
        that was the deepest hole in the re-entry closure: **both arguments were things a
        caller could simply write.** ``frozenset({"equity_crash"})`` is a literal, and a
        blended ``float`` is a number. A type whose constructor accepts an ASSERTED
        provenance and an arbitrary number establishes nothing at all; it only records what
        it was told, and the whole value of this type is that its provenance was
        ESTABLISHED rather than asserted.

        So this constructor fails closed and states what it could not establish, exactly as
        the Product Owner's Class 1 invariant requires of any door that cannot establish its
        guarantee from what it was handed. The two doors build an instance through
        ``object.__new__`` and :func:`_install`, which is not a signature anybody reaches by
        writing the type's name.

        **WHAT THIS DOES NOT CLOSE, AND IT IS NOT CLAIMED TO.** Python has no private state.
        ``object.__setattr__`` on the two slots of an instance obtained by
        ``object.__new__`` forges a quantity without calling anything here, and
        ``provenance._install`` is reachable as a module attribute. Both routes must write
        ``_DeclaredQuantity__value`` or name a module-private helper, and both are the
        residue already declared in this module's header — the residue does not grow, it is
        simply now the ONLY route rather than one of three.
        """
        raise QuantityProvenanceMissing(
            "DeclaredQuantity(...) is not a door and cannot be constructed directly. Its "
            "two fields are exactly the two things a caller must not be able to assert: a "
            "dial set is EVIDENCE about where a number came from, and a number with no "
            "evidence is what a blend becomes the moment it is computed. WHAT THIS "
            "CONSTRUCTOR COULD NOT ESTABLISH: that the provenance offered was carried by "
            "the value rather than written beside it. Obtain one from observed_for_dial(), "
            "which admits a measurement from OUTSIDE for ONE named dial and cites the "
            "inputs it came from, or from derived_within_one_dial(), which reduces "
            "quantities already established and computes the number itself "
            "(CD-AC-002, CD-ASR-WO2R-F01, PID §3.1)."
        )

    # -- immutability -------------------------------------------------------------- #

    def __setattr__(self, name: str, value: object) -> None:
        raise QuantitySurfaceViolated(
            f"cannot set {type(self).__name__}.{name}: a declared quantity is immutable, "
            "and its dial set in particular is the evidence that makes the number "
            "admissible at all."
        )

    def __delattr__(self, name: str) -> None:
        raise QuantitySurfaceViolated(
            f"cannot delete {type(self).__name__}.{name}: a declared quantity without its "
            "provenance is a bare number, which is the thing this type exists to refuse."
        )

    # -- copying and pickling -------------------------------------------------------- #

    def __getstate__(self) -> dict:
        """The state a copy or a pickle carries, KEYED BY THE PRIVATE SLOT NAME.

        Defined because ``copy.deepcopy`` and ``pickle`` restore a slotted object by
        calling ``setattr``, which this type refuses. The key naming follows
        ``DialMagnitude.__getstate__``'s and for the same measured reason
        (``CD-ENG-WO2R-F06``): a state dict keyed ``{"value": ...}`` would put the number
        one ordinary word away from anybody, and RULE 3 of the AST locator would have
        nothing to see.
        """
        return {
            "dials": self.dials,
            "_DeclaredQuantity__value": self._DeclaredQuantity__value,
        }

    def __setstate__(self, state) -> None:
        """Rebuild from state, through THE SAME validation the constructor uses.

        A pickle is untrusted input like any other. A hand-written one cannot revive a
        quantity with no dial, with two dials, or with a non-finite number.
        """
        _install(self, state["dials"], state["_DeclaredQuantity__value"])

    # -- identity ------------------------------------------------------------------- #

    def __eq__(self, other: object) -> bool:
        """Equal only to a declared quantity of the same dial with the same value.

        Deliberately NOT equal to a bare ``float``: equality with a number would be a
        coercion by another name.
        """
        if type(other) is not DeclaredQuantity:
            return NotImplemented
        return (
            self.dials == other.dials
            and self._DeclaredQuantity__value == other._DeclaredQuantity__value
        )

    def __ne__(self, other: object) -> bool:
        answer = self.__eq__(other)
        if answer is NotImplemented:
            return NotImplemented
        return not answer

    def __hash__(self) -> int:
        return hash((frozenset(self.dials), self._DeclaredQuantity__value))

    def __repr__(self) -> str:
        """Shows the value. DELIBERATELY, and it is DECLARED as a release door.

        Hiding a number from a developer's own debugger is obfuscation, not structure, and
        this seat resolved the contradiction the Project Lead identified in favour of
        keeping it (see the module docstring, and ``CD-RT-002-TYPE-NO-ARITHMETIC``'s
        contract). It is safe to render because reading a number out of this text yields a
        ``float``, and a ``float`` cannot get back in.
        """
        return (
            f"DeclaredQuantity(dials={sorted(self.dials)!r}, "
            f"value={self._DeclaredQuantity__value!r})"
        )

    # -- the one release ------------------------------------------------------------- #

    def value_for(self, dial_id: str) -> float:
        """The bare number, for a caller that names the single dial it expects.

        Compares by SET EQUALITY, so a quantity of the other dial, one whose ``dials`` was
        forged to name two, and one naming a dial that does not exist are all refused
        identically — a comparison of data that does not depend on anyone having read the
        surrounding code.
        """
        if self.dials != frozenset({dial_id}):
            raise CrossDialCombination(
                f"this quantity's declared provenance is {sorted(self.dials)}, and the "
                f"caller asked for it as {dial_id!r}. PID §3.1 says the two dials fail in "
                "opposite directions, so a number whose dial is in doubt has already lost "
                "the property that makes it worth publishing (CD-AC-002, CD-ASR-F01)."
            )
        return self._DeclaredQuantity__value


def _assert_declared_surface(cls: type) -> None:
    """Raise unless ``cls``'s class dictionary is exactly the declared surface."""
    observed = frozenset(vars(cls))
    unexpected = observed - DECLARED_QUANTITY_MEMBERS - TOLERATED_QUANTITY_MACHINERY
    missing = DECLARED_QUANTITY_MEMBERS - observed
    breaches = []
    if unexpected:
        breaches.append(
            f"{cls.__name__} carries undeclared member(s) {sorted(unexpected)}. The "
            "surface is declared and asserted by equality, so this is a breach whether or "
            "not the member looks numeric (CD-ASR-F01)."
        )
    if missing:
        breaches.append(
            f"{cls.__name__} is missing declared member(s) {sorted(missing)}. Removing "
            "the member that does the refusing changes the surface as much as adding one."
        )
    if breaches:
        raise QuantitySurfaceViolated(" ".join(breaches))


def _new_quantity(dials: frozenset, value: float) -> DeclaredQuantity:
    """Build a declared quantity. THE ONLY route to one, and it is module-private.

    It goes around :meth:`DeclaredQuantity.__init__`, which refuses always, rather than
    passing it a flag: a flag is an argument, and an argument is something a caller can
    write. What a caller cannot write is a call to a name in another module's private
    namespace without naming it, and naming it is the declared residue.

    Every instance in existence is validated by :func:`_install`, whichever door built it,
    because this is the only place ``object.__new__`` is called on the type.
    """
    quantity = object.__new__(DeclaredQuantity)
    _install(quantity, dials, value)
    return quantity


_assert_declared_surface(DeclaredQuantity)
if DeclaredQuantity.__dictoffset__:
    raise QuantitySurfaceViolated(
        "DeclaredQuantity instances carry a __dict__ despite __slots__, so instance "
        "attribute injection is open and a coercion could be attached to one instance."
    )
_SEALED.add(DeclaredQuantity)


def observed_for_dial(*, dial_id: str, quantity: float, inputs_used) -> DeclaredQuantity:
    """ADMIT a number from outside the system as ONE dial's, citing what produced it.

    **THIS IS THE BASE CASE AND IT IS A DECLARATION.** Something has to be the first number
    or the product cannot exist, and at the bottom of any provenance chain sits an
    assertion that a value came from outside. The module docstring states the residue in
    full rather than dressing this function up as a proof: what this door delivers is that
    a laundered float cannot enter *silently*, and that a module which wants it to enter
    must say, in source, which dial it is claiming and what it claims to have measured.

    Three refusals, each closing a different way of arriving here with nothing:

    * a ``dial_id`` that is not a non-empty string. A number admitted for no dial is a
      number with no provenance, which is what this whole type exists to refuse;
    * ``inputs_used`` empty, or carrying anything that is not a non-empty string. The same
      shape :class:`~crash_detector.dials.reading.Value` already requires of a reading, for
      the same reason: a magnitude computed from nothing is a number nobody computed
      (CD-AC-001, CD-ASR-F03);
    * ``dial_id`` appearing IN ``inputs_used``. **A dial is not an ingredient of a dial.**
      This closes the most natural honest-looking spelling of the forgery — declaring the
      two dials as the inputs of a third figure — by comparing data rather than by reading
      the expression. PID §3.1 admits no figure derived from the dials themselves.

    It imposes no range, no unit and no threshold. Those are product meaning and this seat
    does not invent one (CD-RULE-003, ``PBG-AUTH-005``).
    """
    if not isinstance(dial_id, str) or not dial_id:
        raise CrossDialCombination(
            "admitting a measured number requires the id of the ONE dial it was measured "
            f"for, as a non-empty string; got {dial_id!r}. Provenance is carried as data "
            "rather than inferred from the code around the number, so that a cross-dial "
            "combination is refused by comparing values and not by anybody having read "
            "the expression (CD-ASR-F01)."
        )
    ordered = tuple(inputs_used)
    if not ordered:
        raise CrossDialCombination(
            f"refusing to admit a number for dial {dial_id!r} with no inputs. A number "
            "admitted from nowhere is a number nobody measured, and the whole of this "
            "door's value is that it makes a claim about where a number came from "
            "(CD-AC-001, CD-AC-002)."
        )
    for source_id in ordered:
        if not isinstance(source_id, str) or not source_id:
            raise CrossDialCombination(
                f"every input cited for dial {dial_id!r} must be a non-empty source id; "
                f"got {source_id!r}."
            )
    if dial_id in ordered:
        raise CrossDialCombination(
            f"dial {dial_id!r} is cited as its own input. A DIAL IS NOT AN INGREDIENT OF "
            "A DIAL: PID §3.1 is constitutional that the two dials are never blended, and "
            "a figure whose inputs are dials is the blend it forbids, whichever dial's "
            "name is on the outside (CD-AC-002, CD-ASR-F01, CD-PL-F54)."
        )
    return _new_quantity(frozenset({dial_id}), quantity)


def derived_within_one_dial(*, quantities, reduction) -> DeclaredQuantity:
    """REDUCE quantities whose provenance is already established, to one of that dial.

    **IT TAKES NO NUMBER AND NO DIAL SET.** That is the change that closes
    CD-ASR-WO2R-F01, and both halves of it matter.

    Until this commit the signature was ``(*, dials: frozenset, value: float)`` and the
    docstring argued that the dial set "is therefore evidence rather than an assertion —
    the caller could not have produced it without holding magnitudes that carried it".
    **THAT ARGUMENT WAS ABOUT THE CALLER AND NOT ABOUT THE VALUE, AND IT WAS REFUTED BY
    EXECUTION.** `ASR2-002-A` reached this door through the public, re-exported
    ``combine_within_one_dial``, which computed a perfectly honest single-dial set from the
    magnitudes it was handed and then passed an arbitrary closure's return value straight
    in. The dial set was evidence. The number beside it was not evidence of anything, and
    this door never looked at it. Equity 0.9 and monetary 0.1 published as an equity 0.5.

    What arrives now is a tuple of :class:`DeclaredQuantity` values — the only kind of value
    in this system that CARRIES an established provenance — and the name of a reduction.
    Four refusals, each stating what it could not establish:

    * anything that is not EXACTLY a :class:`DeclaredQuantity`. A bare ``float``, a
      ``float`` subclass, a look-alike, a number returned by a caller's callable: none of
      them carries provenance for this door to read, so the door cannot establish which
      dial the number came from and refuses rather than deciding. **Exact type identity,
      not ``isinstance``**, for the reason :func:`~crash_detector.dials.reading.fold` gives;
    * an empty derivation. A number derived from nothing is a number nobody computed;
    * a union of provenance that is not exactly one dial. The union is COMPUTED here from
      the quantities themselves, so a caller cannot state it, mis-state it, or narrow it;
    * a ``reduction`` that is not a member of :class:`SameDialReduction`, refused BY EXACT
      TYPE. A callable is the shape `ASR2-002-A` used, and it is refused for what it IS
      rather than for what it is named.

    The number is then computed HERE, by :data:`SAME_DIAL_REDUCTIONS`, over values released
    from the quantities for the one dial the union established. **No expression written by a
    caller contributes the result**, which is why this is a property of the door rather than
    a property of who called it.

    It remains a separate door from :func:`observed_for_dial` so that the two are separately
    visible: an admission is a CLAIM about the outside world, a derivation is an inference
    from data already in hand, and collapsing them would hide the one that needs watching
    behind the one that does not. The difference is now structural as well as documentary —
    this door can no longer be used to make a claim at all.
    """
    ordered = tuple(quantities)
    if not ordered:
        raise CrossDialCombination(
            "derived_within_one_dial() requires at least one established quantity. A "
            "number derived from nothing is a number nobody computed, which CD-AC-001 "
            "refuses as surely as CD-AC-002 refuses a blend."
        )
    for offered in ordered:
        if type(offered) is not DeclaredQuantity:
            raise QuantityProvenanceMissing(
                f"a {type(offered).__name__} was offered for derivation. A derivation "
                "reduces values whose provenance this system ESTABLISHED; it does not "
                "accept a number and stamp a provenance onto it. WHAT THIS DOOR COULD NOT "
                "ESTABLISH: which dial, if any, this value came from. Until CD-ASR-WO2R-F01 "
                "this door took a bare float and a caller-supplied dial set, and "
                "`ASR2-002-A` used exactly that to publish an equity 0.5 out of an equity "
                "0.9 and a monetary 0.1 — the dial set it was handed was honest and the "
                "number beside it was a blend (CD-AC-002, PID §3.1)."
            )
    if type(reduction) is not SameDialReduction:
        raise UndeclaredReduction(
            f"a {type(reduction).__name__} was offered as a reduction. A derivation is "
            "named, never supplied: the declared reductions are "
            f"{[member.name for member in SameDialReduction]}, and this module executes "
            "them itself over numbers it released from quantities it established. WHAT "
            "THIS DOOR COULD NOT ESTABLISH: that a number returned by a caller's own code "
            "was derived from this dial at all. `ASR2-002-A` was a one-line `lambda` that "
            "closed over the other dial's figure and returned it, and no layer downstream "
            "can tell such a number from a derivation (CD-AC-002, CD-ASR-WO2R-F01)."
        )
    dials = frozenset().union(*(offered.dials for offered in ordered))
    if len(dials) != 1:
        raise CrossDialCombination(
            f"refusing to derive one number from quantities of {sorted(dials)}. PID §3.1 "
            "is CONSTITUTIONAL: the two dials fail in opposite directions and averaging "
            "cancels the signal. The union is computed HERE from the provenance the "
            "quantities CARRY, so it holds however they were reached and cannot be stated "
            "by a caller (CD-AC-002, CD-ASR-F01)."
        )
    dial_id = next(iter(dials))
    values = tuple(offered.value_for(dial_id) for offered in ordered)
    return _new_quantity(dials, SAME_DIAL_REDUCTIONS[reduction](values))
