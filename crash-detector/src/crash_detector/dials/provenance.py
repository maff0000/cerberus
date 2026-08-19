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

import math

__all__ = [
    "ScoreOutOfRange",
    "CrossDialCombination",
    "QuantityProvenanceMissing",
    "QuantitySurfaceViolated",
    "SealedQuantityType",
    "DeclaredQuantity",
    "DECLARED_QUANTITY_MEMBERS",
    "TOLERATED_QUANTITY_MACHINERY",
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

    def __init__(self, *, dials: frozenset, value: float) -> None:
        _install(self, dials, value)

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
    return DeclaredQuantity(dials=frozenset({dial_id}), value=quantity)


def derived_within_one_dial(*, dials: frozenset, value: float) -> DeclaredQuantity:
    """A quantity whose dial set was COMPUTED from magnitudes the caller already held.

    Called only by :func:`~crash_detector.dials.magnitude.combine_within_one_dial`, which
    unions the provenance of the magnitudes it was given and refuses a union of any size
    but one. The dial set arriving here is therefore evidence rather than an assertion —
    the caller could not have produced it without holding magnitudes that carried it.

    It is a separate door from :func:`observed_for_dial` so that the two are separately
    visible to the register check: an admission is a CLAIM about the outside world, a
    derivation is an inference from data already in hand, and collapsing them would hide
    the one that needs watching behind the one that does not.
    """
    return DeclaredQuantity(dials=dials, value=value)
