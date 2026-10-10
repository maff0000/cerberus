#!/usr/bin/env python3
"""P-O — **`in` OVER A TUPLE OF TYPES IS `==`, AND `==` IS DELEGABLE TO A METACLASS.**

`F-06-D`, the sixth Assurance seat's item 3. `crash_detector.admission` states its doctrine
three times — *"a value of the wrong exact type — ``type(value) is not declared``, never
``isinstance``"*, and `_Exactly`'s own docstring *"``type(value)`` must BE one of these types.
Never ``isinstance``"* — **and implements it with `in`.** `x in (A, B)` is
`x == A or x == B`, `==` puts `type(value)` on the LEFT, and a metaclass that defines
`__eq__` therefore decides this system's admission for its own instances.

**THE PLANT IS AN ORDINARY, SOURCE-HONEST DOOR REPORTING ZERO FAULTS.** No decorator is
removed, no declaration is edited, nothing in `crash_detector` is patched. The only thing the
caller supplies is a class whose metaclass answers `__eq__`.

**IT REPORTS AND IT IS NOT A CARRIER** (CD-RULE-006). It exits 0 whatever it measures. Its
carrier is `tests/test_admission_operator.py`, whose arms FAIL at the base.

    PYTHONPATH=src python3 -B variants/WO-2R3/P-O-the-metaclass-decides-the-comparison.py

Run it in a `git archive` extraction of the base AND in the lane, and compare. **EACH RUN
PRINTS ITS OWN TREE** (CD-PL-F98) — two arms that resolved their import root the same way once
printed identical output on this project and proved nothing.
"""

from __future__ import annotations

import os
import sys

print("TREE PWD:", os.getcwd())
print("crash_detector from:", __import__("crash_detector").__file__)
print()

from crash_detector.admission import (  # noqa: E402
    NotAdmitted,
    admission_faults,
    admits,
    declared_admissions,
    each_of,
)


class Anything(type):
    """A metaclass that answers `__eq__` with True. Eight lines, no privilege at all."""

    def __eq__(cls, other):  # noqa: D105
        return True

    def __hash__(cls):  # noqa: D105 - required once __eq__ is defined
        return id(cls)


class NotAnInt(metaclass=Anything):
    """An instance of this is not an `int` by any honest reading."""


@admits(value=int)
def an_ordinary_door(value: int) -> str:
    """A source-honest door. `@admits(value=int)` and nothing else."""
    return f"BODY RAN and it was handed a {type(value).__name__}"


@admits(values=each_of(int))
def an_ordinary_container_door(values) -> str:
    """The same question one level in: `each_of` establishes a container's ELEMENTS."""
    return f"BODY RAN and element 0 was a {type(values[0]).__name__}"


def arm(label: str, call) -> None:
    try:
        print(f"  {label:<52} ADMITTED -> {call()}")
    except NotAdmitted as refusal:
        print(f"  {label:<52} REFUSED  -> NotAdmitted: {str(refusal)[:60]}")
    except Exception as other:  # pragma: no cover - a probe reports whatever it gets
        print(f"  {label:<52} RAISED   -> {type(other).__name__}: {str(other)[:60]}")


print("THE DOOR IS SOURCE-HONEST AND REPORTS ZERO FAULTS:")
print("  declared_admissions :", {k: v.describe() for k, v in
                                  declared_admissions(an_ordinary_door).items()})
print("  admission_faults    :", admission_faults(an_ordinary_door))
print()

print("ARM 1 — CONTROL. An ordinary wrong type at the same door.")
arm("an_ordinary_door(object())", lambda: an_ordinary_door(object()))
print()
print("ARM 2 — THE PLANT. The caller's METACLASS decides the comparison.")
arm("an_ordinary_door(NotAnInt())", lambda: an_ordinary_door(NotAnInt()))
print()
print("ARM 3 — THE SAME QUESTION ONE LEVEL IN, at `each_of`'s CONTAINER test.")
arm("an_ordinary_container_door(NotAnInt())",
    lambda: an_ordinary_container_door(NotAnInt()))
print()
print("ARM 4 — AND AT `each_of`'s ELEMENT test, in an honest tuple.")
arm("an_ordinary_container_door((NotAnInt(),))",
    lambda: an_ordinary_container_door((NotAnInt(),)))
print()
print("ARM 5 — THE CONTROL FOR ARM 4. An honest tuple of ordinary wrong elements.")
arm("an_ordinary_container_door((object(),))",
    lambda: an_ordinary_container_door((object(),)))
print()
print("THIS PROBE STATES NO CONCLUSION. What it measured is in the Build Log and in the")
print("seat's return, where it can be argued with.")
sys.exit(0)
