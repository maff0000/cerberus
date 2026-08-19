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

This is the first of three independent refusals for CD-AC-002. The other two are the AST
no-blend check over the dial path and the closed public envelope schema. None of the three
is load-bearing alone (BLUEPRINT §13, BLUEPRINT §17 risk CD-BP-001).

----

ON THE ``score`` FIELD, and on what is deliberately NOT validated here.

``score`` is a plain ``float`` because a dial magnitude is a number. What is forbidden is
arithmetic *between the two dial types*, not the existence of a magnitude. Reading
``.score`` off both dials inside one expression is caught by the AST no-blend check
(CD-RT-002-AST-NO-BLEND), which is exactly why that check exists as well as this type.

**No range constraint is imposed on the magnitude, and that is a refusal, not an
omission.** A declared range is a declared scale, and the scale of a dial is what the dial
*means*. BLUEPRINT §16 records the ingredient set and the meaning of each dial as CD-D-005
— owed by the Product Owner before WO-3 — and PID §3.6 forbids unexplained mappings. An
Engineer seat picking ``[0.0, 1.0]`` here would be inventing product meaning
(``PBG-AUTH-005``), and an invented bound that later turns out to be wrong is worse than
no bound: it rejects legitimate readings and it does so quietly, inside a constructor.

What IS validated is the class of thing, not its meaning: a finite ``float``, with ``bool``
refused explicitly because ``isinstance(True, int)`` is true in Python and a boolean
arriving as a magnitude is precisely the coercion this product cannot afford.

Raised to the Project Lead as an open product question, not resolved here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "ScoreOutOfRange",
    "Contribution",
    "EquityCrashScore",
    "MonetaryDebasementScore",
    "SCORE_TYPES",
    "ARITHMETIC_DUNDERS",
]

#: Every arithmetic, comparison-ordering and numeric-coercion dunder. **Neither score
#: type, and no container of them, may define any of these.** Enumerated as data so the
#: guard that asserts their absence tests the CLASS of violation and not the one instance
#: somebody happened to plant.
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


class ScoreOutOfRange(ValueError):
    """A dial magnitude that is not a finite float.

    Refused at construction rather than clamped. A clamped score is a wrong number that
    looks like a right one.
    """


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
        if not self.source_id:
            raise ValueError("Contribution requires a source_id")
        if not self.category:
            raise ValueError("Contribution requires a category")
        for field_name in ("weight", "contribution"):
            _require_finite_float("Contribution", field_name, getattr(self, field_name))


@dataclass(frozen=True)
class EquityCrashScore:
    """Magnitude of building equity-crash conditions.

    Deliberately has no relationship of any kind to :class:`MonetaryDebasementScore`.
    """

    score: float
    contributions: tuple[Contribution, ...]

    def __post_init__(self) -> None:
        _require_finite_float(type(self).__name__, "score", self.score)
        object.__setattr__(self, "contributions", tuple(self.contributions))


@dataclass(frozen=True)
class MonetaryDebasementScore:
    """Magnitude of building monetary-debasement conditions.

    Deliberately has no relationship of any kind to :class:`EquityCrashScore`.
    """

    score: float
    contributions: tuple[Contribution, ...]

    def __post_init__(self) -> None:
        _require_finite_float(type(self).__name__, "score", self.score)
        object.__setattr__(self, "contributions", tuple(self.contributions))


#: The two dial score types. Two. A third is a PID amendment, not an edit here.
SCORE_TYPES: tuple[type, ...] = (EquityCrashScore, MonetaryDebasementScore)


def _require_finite_float(type_name: str, field_name: str, observed: object) -> None:
    """Refuse anything that is not a finite float.

    ``bool`` is refused explicitly, ahead of the ``float`` test, because ``True`` would
    otherwise slip through any ``int``-tolerant path and become ``1.0``.
    """
    if isinstance(observed, bool) or not isinstance(observed, float):
        raise ScoreOutOfRange(
            f"{type_name}.{field_name} must be a float, got {type(observed).__name__}"
        )
    if not math.isfinite(observed):
        raise ScoreOutOfRange(
            f"{type_name}.{field_name} must be finite, got {observed!r}"
        )
