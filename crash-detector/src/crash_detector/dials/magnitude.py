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

4. **Release names its dial — AND RELEASE IS NOT THE CLOSURE.**
   :meth:`DialMagnitude.quantity_for` is the only DECLARED member that yields a bare
   ``float``, and it requires the caller to state which single dial it expects. It is not
   the only way a number leaves: ``repr``, ``str``, ``format``, an f-string, JSON over the
   state, the bytes of a pickle and ``getattr`` on the private slot all release it too,
   and this module now says so rather than claiming otherwise (see boundary A).

5. **A NUMBER THAT HAS LEFT CANNOT COME BACK — the CD-PL-F54 closure.** The constructor
   admits a :class:`~crash_detector.dials.provenance.DeclaredQuantity` and refuses a bare
   ``float``, comparing the quantity's declared dial set to ``dial_id`` by SET EQUALITY.
   Increment 2's structure was closed against being ASKED for a number and open to the
   number being READ OFF it: ``float(repr(m).split("quantity=")[1].rstrip(")"))`` names no
   dial, and two of those add and re-wrap. That route, and every other route to a bare
   ``float``, now ends nowhere. Read
   :mod:`crash_detector.dials.provenance` for why the closure is at the re-entry rather
   than at the exits, and for the residue at the admission door.

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

**A. THE EXITS ARE MANY, THEY ARE ALL DOORS, AND THIS MODULE NO LONGER CLAIMS OTHERWISE.**
The previous text of this boundary said "the release is a real door, AND IT IS THE ONLY
ONE", and said that reducing a magnitude to a number requires naming its single dial. **THE
SECOND HALF WAS FALSE AND IS WITHDRAWN** (`CD-PL-F54`). It was contradicted eight lines
below by this module's own disclosure that ``repr`` renders the quantity, and the Project
Lead measured the contradiction:

    float(repr(m).split("quantity=")[1].rstrip(")"))     # names no dial. Yields 0.4.

The honest statement is that a number leaves a magnitude by many routes and the list has no
end: :meth:`quantity_for`, ``repr``, ``str``, ``format``, an f-string, ``%``-formatting,
``pprint``, a log line, a traceback, ``json.dumps`` over ``__getstate__``, the bytes of a
``pickle``, ``getattr(m, "_DialMagnitude__quantity")`` and whatever protocol arrives in the
next Python release. **Closing one of them is the instance game.** Two released numbers can
be added, and this module cannot prevent it: they are two ``float`` objects and Python adds
floats.

**THE CLAIM THAT STOOD HERE — "THE SUM CANNOT COME BACK ... NO NUMBER SO OBTAINED CAN EVER BE
A DIAL MAGNITUDE AGAIN" — WAS MEASURED FALSE AND IS WITHDRAWN** (`CD-ASR-WO2R-F01`, HIGH).
It was refuted by execution at ``50fc231`` and replicated by the seat that wrote this
replacement before it changed anything. `ASR2-002-A` released both dials' numbers with
:meth:`quantity_for`, averaged them in an ordinary expression, and handed the average back
through :func:`combine_within_one_dial` — a PUBLIC function, re-exported in this package's
``__all__``, which computed an honest single-dial set from the magnitudes it was given and
then passed the caller's arbitrary closure's return value straight into the derivation door,
which validated the dial set and never the value. ``check_no_blend`` was PASS on 4873
assertions with it present. Equity 0.9 and monetary 0.1 published as an equity **0.5**. The
sum came back.

**WHAT IS CLAIMED NOW, STATED SO THAT IT CAN BE REFUTED BY EXECUTION** (`WO-2R2` increment
1a). A number that has left a magnitude cannot become a magnitude again **BY DERIVATION**:
the derivation door takes no number and no dial set at all — it takes
:class:`~crash_detector.dials.provenance.DeclaredQuantity` values whose provenance this
system established, refused by EXACT TYPE, and computes its own number from a closed set of
NAMED reductions. There is no argument anywhere on a derivation path through which a
caller's ``float`` or a caller's callable can arrive, so the closure does not depend on
recognising the caller, the module, the expression or the name of anything.

**WHAT IS NOT CLAIMED, AND MUST NOT BE READ IN.** Two released numbers can still be added:
they are two ``float`` objects and Python adds floats. And a blend can still be **declared**
back in at :func:`~crash_detector.dials.provenance.observed_for_dial`, the external base
case — see boundary E, which is NOT closed, and `CD-ENG-WO2R2-V05` in
``variants/WO-2R2/MANIFEST.md``, which reaches that door through the product's own
contribution-model interface, publishes a blend, and is **NOT REFUSED BY ANY LAYER**.

**B. ``object.__setattr__`` REWRITES A SLOT, AND IT HAS TWO DIRECTIONS — ONE SAFE, ONE NOT.**
As for every frozen object in Python, ``object.__setattr__`` walks past ``__setattr__``.

*Forging the PROVENANCE is safe.* ``object.__setattr__(m, "provenance", frozenset({"a",
"b"}))`` makes the magnitude LESS usable, not more: :meth:`quantity_for` compares by set
equality and refuses it, the score types refuse to carry it, and the publication gate
refuses to publish it. There is no forgery of provenance that yields a number.

*Forging the VALUE is NOT safe, and this seat found it against its own work while running
the eleven plants* (``CD-ENG-WO2R-F11``). ``object.__setattr__(q, "_DeclaredQuantity__value",
<a blend>)`` on the DeclaredQuantity a live magnitude already holds changes the number
IN PLACE, so nothing is ever constructed and the re-entry closure is never reached. MEASURED
as `V17`: it is NOT refused at runtime and the magnitude then reads 0.5. **NO RUNTIME LAYER
CARRIES THIS AND NONE IS CLAIMED TO** (CD-RULE-006). What does carry it, statically, is RULE
3 of ``tools/register/check_no_blend.py``: reaching either private slot on the scanned path
is a violation with no allowlist beyond each declaring module, and `V17` produces six of
them. No Python-level structure can prevent an in-place slot rewrite; a guard that claimed to
would be claiming something Python does not offer.

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

**D. ``repr`` SHOWS THE QUANTITY, AND IS NAMED A RELEASE DOOR.** Deliberately, and
unchanged: hiding a value from a developer's own debugger would be obfuscation, and
obfuscation is not structure. This is the direction chosen on the contradiction the Project
Lead raised — the disclosure stands, the CLAIM that stood beside it does not. ``repr`` is
listed in boundary A with the other exits, in the register entry and in
``contracts/execution/CD-RT-002-TYPE-NO-ARITHMETIC.md``, in the same words.

**E. THE ADMISSION DOOR IS A DECLARATION AND A DECLARATION CAN BE FALSE. THIS IS WHERE THE
CLASS IS STILL OPEN, AND IT IS THE MOST IMPORTANT PARAGRAPH IN THIS HEADER.** The residue of
the re-entry closure, stated in full in :mod:`crash_detector.dials.provenance`. A module that
calls ``observed_for_dial(dial_id=..., quantity=<a blend>, inputs_used=(...))`` obtains a
magnitude. **NOT CLAIMED TO BE CLOSED**, and measured both ways as `V12`/`V13`.

*What it costs a module OUTSIDE a declared admission site*: a RULE 4 violation from
``tools/register/check_no_blend.py``. **THAT CARRIER IS A NAME VOCABULARY AND DOES NOT
SURVIVE A RENAME** (`CD-PL-F74`, adopted project-wide at `CD-D-073`). It is a locator, it is
static and intra-procedural, and it is recorded as a vocabulary result rather than a class
one. It is not what closes anything.

*What it costs a module INSIDE a declared admission site: nothing at all, and this was
MEASURED.* `CD-ENG-WO2R2-V05` gives ONE stateful ``ContributionModel`` object to BOTH
``DialSpec``s. ``evaluate`` hands it each dial's payloads in turn — a separation that is real
and that the variant does not break — and the model keeps what it saw and returns the mean as
the second dial's magnitude. It launders nothing, names no door outside a declared site,
touches no private slot, performs no arithmetic on a magnitude and never holds both dials in
one expression. Every field of its admission claim is TRUE except the number.
``check_no_blend`` PASS 5002, ``check_no_numeric_default`` PASS 397, whole suite 1333 passed,
and ``number_for_dial_slot('monetary_debasement', ...)`` **returned 0.5**.

**NO LAYER CARRIES THAT, AND NONE IS CLAIMED TO — NOT PROVED TO BE CARRIED ANYWHERE**
(CD-RULE-006). No guard was built for it, deliberately: an identity check refusing one model
object shared between two specs is defeated by two instances sharing a class attribute, and
whether a caller-supplied model is pure is not decidable at this altitude. Closing it is an
architectural change — the system computing dial magnitudes from source payloads itself
rather than delegating to a caller-supplied model — which is BLUEPRINT §7 / CD-D-005
territory and is owed to the Product Owner. The variant, its measurement and the reasoning
are in ``variants/WO-2R2/MANIFEST.md``.
"""

from __future__ import annotations

from crash_detector.own_terms import NotEstablishedOnOwnTerms, own_str
from crash_detector.dials.provenance import (
    CrossDialCombination,
    DeclaredQuantity,
    QuantityProvenanceMissing,
    SameDialReduction,
    ScoreOutOfRange,
    UndeclaredReduction,
    derived_within_one_dial,
    observed_for_dial,
    require_finite_float,
)

__all__ = [
    "ScoreOutOfRange",
    "MagnitudeSurfaceViolated",
    "CrossDialCombination",
    "QuantityProvenanceMissing",
    "UndeclaredReduction",
    "DeclaredQuantity",
    "SameDialReduction",
    "SealedMagnitudeType",
    "DialMagnitude",
    "DECLARED_MAGNITUDE_MEMBERS",
    "TOLERATED_INTERPRETER_MACHINERY",
    "combine_within_one_dial",
    "observed_for_dial",
    "require_finite_float",
    "sole_dial_of",
]


class MagnitudeSurfaceViolated(TypeError):
    """:class:`DialMagnitude`'s attribute surface is not the declared one.

    A ``TypeError`` because what is wrong is the *type*, not a value someone passed.
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


def _install(instance: object, dial_id: object, quantity: object) -> None:
    """Validate and write a magnitude's two slots. THE ONLY place either is written.

    A module function rather than a method, for two reasons. It is the shared path for
    construction and for revival from a pickle or a copy, so neither can be validated more
    loosely than the other; and it is not a member of :class:`DialMagnitude`, so it does
    not widen the declared attribute surface.
    """
    # RE-ESTABLISHED BEFORE THE SET-EQUALITY COMPARISON BELOW (CD-AC-005, Class 2).
    # `quantity.dials != frozenset({dial_id})` is the cross-dial refusal, and it hashes and
    # compares this string. `isinstance(dial_id, str)` admitted a subclass whose __hash__
    # and __eq__ answered that comparison, so the refusal was the caller's to make.
    offered_dial_id = dial_id
    try:
        dial_id = own_str(dial_id)
    except NotEstablishedOnOwnTerms:
        dial_id = ""  # falls into the refusal below, with the offered value reported
    if not dial_id:
        raise CrossDialCombination(
            "a dial magnitude requires the id of the ONE dial it came from, as a "
            f"non-empty string; got {offered_dial_id!r}. Provenance is carried as data rather "
            "than inferred from the code around the number, so that a cross-dial "
            "combination is refused by comparing values and not by anybody having read "
            "the expression (CD-ASR-F01)."
        )
    if type(quantity) is not DeclaredQuantity:
        # THE RE-ENTRY REFUSAL, and the whole of the CD-PL-F54 closure (CD-ASR-F01).
        #
        # A bare number cannot become a magnitude. Every laundering route out of a
        # magnitude — repr, str, format, an f-string, JSON, the bytes of a pickle,
        # getattr on the private slot, __getstate__, a figure recovered from a log line,
        # or a protocol nobody here has heard of — ends with a `float` in somebody's
        # hand, and a `float` has no dial. Chasing the exits is the instance game: there
        # is no last exit. Removing the destination they share is the class closure.
        #
        # A value that is not even a finite float is reported in the familiar terms
        # first, so that "you passed a string" does not arrive dressed as a provenance
        # argument. Everything that survives that is a real number with no provenance.
        require_finite_float("DialMagnitude", "quantity", quantity)
        raise QuantityProvenanceMissing(
            f"a bare number ({quantity!r}) was offered as dial {dial_id!r}'s magnitude. A "
            "magnitude is built from a DeclaredQuantity — a number whose provenance was "
            "established at one of two declared doors: observed_for_dial(), which admits "
            "a measurement from outside for ONE named dial and cites the inputs it came "
            "from, or combine_within_one_dial(), which derives one from magnitudes "
            "already in hand and unions their provenance. A float that has left a "
            "magnitude has lost its dial and no layer downstream can recover it, so it "
            "may not come back in (PID §3.1, CD-AC-002, CD-ASR-F01, CD-PL-F54)."
        )
    if quantity.dials != frozenset({dial_id}):
        raise CrossDialCombination(
            f"a quantity declared for {sorted(quantity.dials)} was offered as dial "
            f"{dial_id!r}'s magnitude. The comparison is SET EQUALITY in both directions "
            "— not a subset, not an intersection — so a quantity of the other dial, of "
            "both dials, or of a dial that does not exist is refused identically, by "
            "comparing data (CD-AC-002, CD-ASR-F01)."
        )
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

    def __init__(self, *, dial_id: str, quantity: "DeclaredQuantity") -> None:
        """Build a magnitude for ONE dial, from a number that already has a provenance.

        Keyword-only, so a call site always reads ``dial_id=...``; and there is no
        constructor that takes a set of dials, which is why a multi-dial provenance is
        not a state this type can be in.

        ``quantity`` is a
        :class:`~crash_detector.dials.provenance.DeclaredQuantity` and **never a bare
        ``float``** (CD-PL-F54). Its dial set is compared to ``dial_id`` by set equality,
        so the two cannot disagree and neither can be inferred from the other.
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
        exactly as it reports the attribute.

        **AND SINCE CD-PL-F54 THE PAYLOAD IS NOT A ``float``.** The slot holds a
        :class:`~crash_detector.dials.provenance.DeclaredQuantity`, so what reflection
        reaches is another provenance-carrying value that defines no arithmetic and no
        coercion. The escape above now fails at the ``sum`` rather than being merely
        visible to a locator. Reflection remains a way of READING the payload and is
        declared as such; it is not a way of obtaining a number that can re-enter.
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
        if not isinstance(provenance, frozenset):
            raise CrossDialCombination(
                f"a magnitude cannot be revived with provenance {provenance!r}: it must "
                "be exactly one dial. A pickle is untrusted input like any other, and a "
                "revived magnitude is validated exactly as a constructed one."
            )
        # Counted and indexed on a container this method built (CD-AC-005, Class 2). The
        # supplied object's own __len__ and its elements' own __lt__ decided both the count
        # and which id was installed when this read `len(provenance) != 1` and
        # `sorted(provenance)[0]`, and a pickle is untrusted input like any other.
        members = tuple(provenance)
        if len(members) != 1:
            raise CrossDialCombination(
                f"a magnitude cannot be revived with provenance {provenance!r}: it must "
                "be exactly one dial. A pickle is untrusted input like any other, and a "
                "revived magnitude is validated exactly as a constructed one."
            )
        _install(self, members[0], state["_DialMagnitude__quantity"])

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
        """Renders the quantity, UNCHANGED and deliberately (boundary D, and CD-PL-F54).

        The Project Lead identified a contradiction: this codebase disclosed that ``repr``
        contains the quantity while also claiming that reducing a magnitude to a number
        requires naming its single dial. Both could not be true. This seat resolved it by
        WITHDRAWING THE CLAIM and keeping ``repr``, because hiding a value from a
        developer's own debugger is obfuscation rather than structure, and because
        ``repr`` is one member of an exit class with no last member. ``repr`` is now NAMED
        as a release door alongside ``quantity_for`` and reflection, and what closes the
        class is that a number which came out of one cannot go back into a magnitude.
        """
        dial_id = sorted(self.provenance)[0]
        return (
            f"DialMagnitude(dial_id={dial_id!r}, "
            f"quantity={self._DialMagnitude__quantity.value_for(dial_id)!r})"
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
        can be added by ordinary Python arithmetic and this method does not pretend
        otherwise. What closes THAT is not the publication gate — the Project Lead
        measured the gate accepting the blend once it was re-wrapped, and boundary 6 of
        ``check_no_blend`` has been corrected accordingly. What closes it is that the
        blend cannot be re-wrapped at all: it is a bare ``float`` and
        :class:`DialMagnitude` admits only a
        :class:`~crash_detector.dials.provenance.DeclaredQuantity` (CD-PL-F54).
        """
        # The caller's `dial_id` is hashed into the set this provenance is compared with,
        # so its own __hash__ and __eq__ would otherwise decide the release (CD-AC-005,
        # Class 2). Re-established first; anything that is not a string is simply not this
        # magnitude's dial and is refused by the same sentence as the wrong dial.
        try:
            dial_id = own_str(dial_id)
        except NotEstablishedOnOwnTerms:
            raise CrossDialCombination(
                f"this magnitude's provenance is {sorted(self.provenance)}, and the "
                f"caller asked for it as {dial_id!r}, which is not a dial id at all."
            ) from None
        if self.provenance != frozenset({dial_id}):
            raise CrossDialCombination(
                f"this magnitude's provenance is {sorted(self.provenance)}, and the "
                f"caller asked for it as {dial_id!r}. A dial magnitude is released as a "
                "number only to a caller that names its ONE dial: PID §3.1 says the two "
                "dials fail in opposite directions and averaging cancels the signal, so "
                "a number whose dial is in doubt has already lost the property that "
                "makes it worth publishing (CD-AC-002, CD-ASR-F01)."
            )
        return self._DialMagnitude__quantity.value_for(dial_id)


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


def _established_quantity(magnitude: "DialMagnitude") -> "DeclaredQuantity":
    """The provenance-carrying value inside a magnitude, WITHOUT releasing a bare float.

    The one place this module hands a magnitude's payload onward, and it hands on the
    :class:`~crash_detector.dials.provenance.DeclaredQuantity` rather than the number
    inside it. That is the difference CD-ASR-WO2R-F01 turned on: a released ``float`` has
    lost its dial and can be substituted for any other ``float`` by anybody holding it,
    whereas a declared quantity carries the evidence with it and can be substituted for
    nothing.

    It names the private slot, which RULE 3 of ``tools/register/check_no_blend.py`` refuses
    everywhere except the module that DECLARES that slot. This is that module.
    """
    if type(magnitude) is not DialMagnitude:
        raise CrossDialCombination(
            f"not a dial magnitude: {type(magnitude).__name__}. A bare number has no "
            "provenance to carry into a derivation, and a number without provenance is "
            "exactly what CD-AC-002 forbids being published."
        )
    return magnitude._DialMagnitude__quantity


def combine_within_one_dial(magnitudes, *, using) -> "DialMagnitude":
    """Compute a new magnitude from magnitudes that all came from the SAME dial.

    THE POINT OF COMBINATION, and therefore the place provenance is compared.

    **``using`` IS A NAMED REDUCTION AND NOT A CALLABLE. THAT IS THE CD-ASR-WO2R-F01
    CLOSURE AT THIS FUNCTION AND IT IS THE WHOLE OF IT.** It is a member of
    :class:`~crash_detector.dials.provenance.SameDialReduction`; the reduction is executed
    by :mod:`crash_detector.dials.provenance` over numbers that module released from the
    quantities these magnitudes carry, and nothing a caller wrote contributes the result.

    Until this commit ``using`` received a tuple of released ``float`` values and returned
    one, and this function passed that return value straight into the derivation door. It
    computed the dial set honestly and it validated the VALUE not at all, which made this
    the public, re-exported proxy through which `ASR2-002-A` published an equity 0.5 out of
    an equity 0.9 and a monetary 0.1 with every declared static layer green. The function
    was never in ``ADMISSION_VOCABULARY`` and did not need to be: it was a door that did not
    look like one, and adding its name to a list would have left the next one open.

    Legitimate same-dial work still works — a rolling mean of one dial over time, a maximum
    over a window, a minimum, a total — and that matters as much as the refusal: a closure
    that forbids the product is not a closure. What it costs is that a derivation this
    product later needs is DECLARED in ``SameDialReduction``, visibly, rather than written
    inline at a call site. A weighted recomputation is not shipped because weights are
    product meaning and CD-D-005 is owed (CD-RULE-003); that derivation fails closed.

    What is still refused, unchanged: the shape that arrives innocently — a helper written
    for one dial and later reused across both. It fails when it is REUSED, at runtime, by
    comparing the provenance data it was handed, not when somebody reviews the code, and
    not because the expression happened to name a dial.
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
    # What travels to the derivation door is the ESTABLISHED QUANTITIES, never released
    # numbers and never a dial set stated by this function. The door re-computes the union
    # from the quantities themselves and computes the reduced number itself, so there is no
    # argument on this path through which a caller's number could arrive (CD-ASR-WO2R-F01).
    return DialMagnitude(
        dial_id=dial_id,
        quantity=derived_within_one_dial(
            quantities=tuple(_established_quantity(m) for m in ordered),
            reduction=using,
        ),
    )
