"""The two dial score types — unrelated by construction (BLUEPRINT §7, CD-AC-002).

PID §3.1 is CONSTITUTIONAL: "Two dials, never blended. Equity crash and
monetary/debasement fail in opposite directions; averaging cancels the signal."

Built, that means:

* :class:`EquityCrashScore` and :class:`MonetaryDebasementScore` share no ancestor except
  ``object``, so there is no common numeric base through which one could be substituted
  for, or combined with, the other.
* Neither defines **any** arithmetic or numeric-coercion dunder. ``equity + monetary`` is
  a ``TypeError`` raised by the interpreter, not a check someone has to remember to run.
* Neither subclasses ``float`` or ``int``, and neither is registered with
  ``numbers.Number``, so neither is silently coercible into an arithmetic expression.
* Neither is ordered against the other: no ``__lt__`` family, so they cannot even be
  compared, let alone combined.

This is one of CD-AC-002's refusals. The others are the magnitude type in
:mod:`crash_detector.dials.magnitude`, the provenance gate at the publication boundary in
:mod:`crash_detector.publication.dial_scalar`, the AST no-blend check over the dial path,
and the closed public envelope schema. None of them is load-bearing alone (BLUEPRINT §13,
BLUEPRINT §17 risk CD-BP-001).

====================================================================================
ON THE ``score`` FIELD — REWRITTEN closing CD-ASR-F01 (HIGH)
====================================================================================

``score`` used to be a plain ``float``, on the reasoning that "what is forbidden is
arithmetic *between the two dial types*, not the existence of a magnitude", with the AST
no-blend check named as the instrument that would catch a caller unwrapping both dials to
floats first.

**That reasoning was refuted by execution.** An independent auditor produced two working
blends that passed all three declared layers simultaneously and each returned ``0.5`` from
equity ``0.9`` and monetary ``0.1`` (`CD-ASR-F01`, escaped variants `E01` and `E02`). The
defect was exactly where the old paragraph put its trust: the moment a caller held two
``float`` values, the type system had left the conversation, and the static check that was
supposed to see it is intra-procedural and cannot follow a value into a helper or through
a ``getattr`` over string slots.

So ``score`` is now a :class:`~crash_detector.dials.magnitude.DialMagnitude`: a NOMINAL,
PER-DIAL, NON-COERCIBLE value that carries which dial it came from as DATA. It defines
none of :data:`ARITHMETIC_DUNDERS`, so ``left + right``, ``sum([...])``,
``functools.reduce``, ``statistics.mean`` and every other reduction raise ``TypeError``
from the interpreter regardless of how the two values were reached. Each score type
refuses a magnitude that does not carry ITS dial, so the two slots are not interchangeable
and a magnitude cannot be laundered from one dial into the other by re-wrapping it.

Read :mod:`crash_detector.dials.magnitude` for the invariant in full, including the one
boundary that is declared rather than closed: a number released for ONE named dial is an
ordinary ``float``, and what stops two such numbers being published as a blend is the
publication gate and the closed envelope schema, not this type.

----

ON WHAT IS DELIBERATELY NOT VALIDATED HERE.

**No range constraint is imposed on the magnitude, and that is a refusal, not an
omission.** A declared range is a declared scale, and the scale of a dial is what the dial
*means*. BLUEPRINT §16 records the ingredient set and the meaning of each dial as CD-D-005
— owed by the Product Owner before WO-3 — and PID §3.6 forbids unexplained mappings. An
Engineer seat picking ``[0.0, 1.0]`` here would be inventing product meaning
(``PBG-AUTH-005``, CD-RULE-003), and an invented bound that later turns out to be wrong is
worse than no bound: it rejects legitimate readings and it does so quietly, inside a
constructor.

That refusal survives the CD-ASR-F01 rework unchanged and deliberately so. This increment
changed the TYPE of a magnitude and how it composes. It decided nothing about what a
magnitude means, and it introduced no range, no unit and no threshold.

What IS validated is the class of thing, not its meaning: a finite ``float`` inside a
magnitude carrying exactly one dial's provenance, with ``bool`` refused explicitly because
``isinstance(True, int)`` is true in Python and a boolean arriving as a magnitude is
precisely the coercion this product cannot afford.

Raised to the Project Lead as an open product question, not resolved here.
"""

from __future__ import annotations

from dataclasses import dataclass

from crash_detector.own_terms import NotEstablishedOnOwnTerms, own_str
from crash_detector.dials.magnitude import (
    CrossDialCombination,
    DialMagnitude,
    ScoreOutOfRange,
    require_finite_float,
)
from crash_detector.establishment import each_of, establishes

__all__ = [
    "ScoreOutOfRange",
    "CrossDialCombination",
    "DialMagnitude",
    "Contribution",
    "EquityCrashScore",
    "MonetaryDebasementScore",
    "SCORE_TYPES",
    "ARITHMETIC_DUNDERS",
    "EQUITY_DIAL_ID",
    "MONETARY_DIAL_ID",
]

#: The identity of the equity-crash dial. It lives HERE, beside the type whose magnitudes
#: carry it, because after CD-ASR-F01 a dial id is not a label on a container — it is the
#: PROVENANCE a magnitude carries as data, and provenance belongs with the thing that
#: has it. ``crash_detector.dials.dialset`` re-exports both ids, so every existing import
#: site is unchanged.
EQUITY_DIAL_ID = "equity_crash"

#: The identity of the monetary-debasement dial. Declared in its own statement rather than
#: alongside the other, so that no single expression in this module names both dials
#: except the one that deliberately enumerates the two types as data.
MONETARY_DIAL_ID = "monetary_debasement"

#: Every arithmetic, comparison-ordering and numeric-coercion dunder. **Neither score
#: type, no container of them, and — since CD-ASR-F01 — no dial MAGNITUDE may define any
#: of these.** Enumerated as data so the guard that asserts their absence tests the CLASS
#: of violation and not the one instance somebody happened to plant. The magnitude type is
#: the one that now matters most: it is what a caller reaches when it unwraps a dial, and
#: the whole of E01 and E02 was that what it reached used to be a bare ``float``.
ARITHMETIC_DUNDERS: tuple[str, ...] = (
    # binary arithmetic, and their reflected and in-place forms
    "__add__", "__radd__", "__iadd__",
    "__sub__", "__rsub__", "__isub__",
    "__mul__", "__rmul__", "__imul__",
    "__truediv__", "__rtruediv__", "__itruediv__",
    "__floordiv__", "__rfloordiv__", "__ifloordiv__",
    "__mod__", "__rmod__", "__imod__",
    "__divmod__", "__rdivmod__",
    "__pow__", "__rpow__", "__ipow__",
    "__matmul__", "__rmatmul__", "__imatmul__",
    # bitwise, because `equity | monetary` and `equity & monetary` are combinations too
    "__and__", "__rand__", "__iand__",
    "__or__", "__ror__", "__ior__",
    "__xor__", "__rxor__", "__ixor__",
    "__lshift__", "__rlshift__", "__ilshift__",
    "__rshift__", "__rrshift__", "__irshift__",
    "__invert__",
    # unary arithmetic
    "__neg__", "__pos__", "__abs__",
    # numeric coercion: every route by which a caller could get a bare number out
    "__int__", "__float__", "__complex__", "__index__", "__round__",
    "__trunc__", "__floor__", "__ceil__",
    # ordering across the two dials: they are not comparable, because comparing them
    # presumes a shared scale, which is the premise CD-AC-002 denies
    "__lt__", "__le__", "__gt__", "__ge__",
)


@establishes(
    source_id=str,
    category=str,
    weight=float,
    contribution=float,
)
@dataclass(frozen=True)
class Contribution:
    """One named input's contribution to a dial magnitude.

    ``source_id`` is the registry identifier of the ingredient that produced it, so a
    reading can be explained from its stored inputs a year later without archaeology
    (BLUEPRINT §7).
    """

    source_id: str
    category: str
    weight: float
    contribution: float

    def __post_init__(self) -> None:
        # RE-ESTABLISHED BEFORE THEY ARE JUDGED OR STORED (CD-AC-005, Class 2). Neither
        # label carried any type check at all, so `not self.source_id` was decided by
        # whatever __bool__ or __len__ the supplied object defined, and both labels are
        # then carried into the published envelope and compared there. The two numbers go
        # through require_finite_float, which now RETURNS the established float rather than
        # approving the caller's object, so what this frozen value stores is a plain float.
        for field_name in ("source_id", "category"):
            try:
                object.__setattr__(
                    self, field_name, own_str(getattr(self, field_name))
                )
            except NotEstablishedOnOwnTerms as refusal:
                raise TypeError(
                    f"Contribution.{field_name} must be a str: {refusal}"
                ) from None
        if not self.source_id:
            raise ValueError("Contribution requires a source_id")
        if not self.category:
            raise ValueError("Contribution requires a category")
        for field_name in ("weight", "contribution"):
            object.__setattr__(
                self,
                field_name,
                require_finite_float(
                    "Contribution", field_name, getattr(self, field_name)
                ),
            )


def _require_magnitude_of(type_name: str, dial_id: str, observed: object) -> None:
    """Refuse a magnitude that is not this dial's magnitude.

    THREE refusals in one, and each closes a different route (CD-ASR-F01):

    * a bare number is refused, because a number without provenance is precisely what a
      blend is. There is no path from ``float`` to a score type, so a blended float cannot
      be re-wrapped as a dial reading and published as one;
    * a look-alike is refused by EXACT TYPE IDENTITY rather than ``isinstance``, so a
      subclass carrying a coercion — were one constructible, and
      :class:`~crash_detector.dials.magnitude.SealedMagnitudeType` refuses to construct
      one — is not accepted where a magnitude is accepted;
    * the OTHER dial's magnitude is refused by comparing provenance, so the two slots are
      not interchangeable. Two dials that can be swapped are one dial with two names.
    """
    if type(observed) is not DialMagnitude:
        raise ScoreOutOfRange(
            f"{type_name}.score must be a DialMagnitude carrying dial {dial_id!r}, got "
            f"{type(observed).__name__}. A dial magnitude carries its provenance as data "
            "so that a cross-dial combination is refused by comparing values rather than "
            "by anybody having read the expression (CD-AC-002, CD-ASR-F01). Build one "
            f"with DialMagnitude(dial_id={dial_id!r}, quantity=<float>)."
        )
    if observed.provenance != frozenset({dial_id}):
        raise CrossDialCombination(
            f"{type_name}.score was given a magnitude whose provenance is "
            f"{sorted(observed.provenance)}, and this dial is {dial_id!r}. The two dials "
            "fail in opposite directions (PID §3.1), so a magnitude may not be laundered "
            "from one dial into the other by re-wrapping it."
        )


@establishes(
    score=DialMagnitude,
    contributions=each_of(Contribution, within=(tuple,)),
)
@dataclass(frozen=True)
class EquityCrashScore:
    """Magnitude of building equity-crash conditions.

    Deliberately has no relationship of any kind to :class:`MonetaryDebasementScore`.
    """

    score: DialMagnitude
    contributions: tuple[Contribution, ...]

    def __post_init__(self) -> None:
        _require_magnitude_of(type(self).__name__, EQUITY_DIAL_ID, self.score)
        object.__setattr__(self, "contributions", tuple(self.contributions))


@establishes(
    score=DialMagnitude,
    contributions=each_of(Contribution, within=(tuple,)),
)
@dataclass(frozen=True)
class MonetaryDebasementScore:
    """Magnitude of building monetary-debasement conditions.

    Deliberately has no relationship of any kind to :class:`EquityCrashScore`.
    """

    score: DialMagnitude
    contributions: tuple[Contribution, ...]

    def __post_init__(self) -> None:
        _require_magnitude_of(type(self).__name__, MONETARY_DIAL_ID, self.score)
        object.__setattr__(self, "contributions", tuple(self.contributions))


#: The two dial score types. Two. A third is a PID amendment, not an edit here.
SCORE_TYPES: tuple[type, ...] = (EquityCrashScore, MonetaryDebasementScore)
