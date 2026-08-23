"""P-P — `CD-PL-F104`: THE `@establishes` GATE UNDER SIX FORGERIES, BOTH ARMS.

    PYTHONPATH=<tree>/src python3 -B variants/WO-2R3/P-P-the-establishes-gate-under-six-forgeries.py

**IT PRINTS THE TREE IT IMPORTED ON THE FIRST LINE** (`CD-PL-F98`: two arms of a probe once
resolved their import root from ``__file__`` and BOTH IMPORTED THE SAME TREE, printing
identical output). Point ``PYTHONPATH`` at a different extraction and the line changes; **if
it does not change, the two runs are one run.**

**IT IS AN INSTRUMENT THAT REPORTS AND IT IS NOT A CARRIER** (`CD-RULE-006`). It exits 0
whatever it measures.

WHAT IT IS FOR
--------------
``P-K`` re-measured the finding. **THIS ONE MEASURES THE PROPOSED CLOSURE**, arm by arm,
against BOTH the unpatched tree and the tree with
``variants/WO-2R3/V49-cd-pl-f104-establishes-admits-a-non-dataclass.patch`` applied — because
`CD-RULE-004` says a guard closes its class or declares its limit, and **A CLOSURE NOBODY RAN
BOTH ARMS OF IS A PARAGRAPH.**

Six arms, and the last two matter most:

  1. the finding's own route — one class attribute, ``__dataclass_fields__ = {}``;
  2. the same plus a decoy ``__dataclass_params__`` that is not the machinery's type;
  3. a PLAIN SUBCLASS of a real dataclass — ``is_dataclass`` answers True and the class
     carries no declaration of its own (``establishment.py`` DECLARED LIMIT 4 says a subclass
     is not governed, and until this closure the decorator did not agree);
  4. an INSTANCE of a real dataclass — ``is_dataclass`` answers True for instances too;
  5. a genuine params object STOLEN from a real dataclass, plus a hand-written Field;
  6. **THE RESIDUE ARM.** A caller who builds genuine ``dataclasses`` machinery — a real
     params object and real ``Field``s carrying real sentinels. **THIS ARM IS EXPECTED TO BE
     ADMITTED IN BOTH TREES AND THAT IS THE POINT.** It is what the closure does NOT close,
     it is what the declared limit says, and printing it beside the five that ARE closed is
     the difference between a measured limit and a silent one.
"""

import dataclasses
import pathlib
import sys

import crash_detector.establishment as E

print(f"tree: {pathlib.Path(E.__file__).resolve()}")
print(f"python: {sys.version.split()[0]}")
print()


def arm(number: int, what: str, build) -> None:
    try:
        result = build()
    except E.EstablishmentFault as error:
        text = str(error)
        measured = text.split("MEASURED: ", 1)[1] if "MEASURED: " in text else "(no MEASURED clause — this is the UNPATCHED gate's wording)"
        print(f"ARM {number}  {what}")
        print(f"         REFUSED  EstablishmentFault")
        print(f"         because: {measured[:150]}")
    except Exception as error:  # noqa: BLE001 — a refusal from another layer is a datum
        print(f"ARM {number}  {what}")
        print(f"         refused  {type(error).__name__} — NOT THIS GATE, read the layer: {str(error)[:110]}")
    else:
        governed = result in E.governed_types() if isinstance(result, type) else "n/a"
        print(f"ARM {number}  {what}")
        print(f"         ADMITTED  is_establishing_type={E.is_establishing_type(result)} "
              f"faults={E.establishment_faults(result)!r} in_governed_types={governed}")
    print()


# ARM 1 — the finding's own route, verbatim.
class _Forged:
    __dataclass_fields__ = {}


arm(1, "one class attribute: `__dataclass_fields__ = {}`", lambda: E.establishes()(_Forged))


# ARM 2 — plus a decoy params object.
class _ForgedWithDecoyParams:
    __dataclass_fields__ = {}
    __dataclass_params__ = object()


arm(2, "the same, plus a decoy __dataclass_params__", lambda: E.establishes()(_ForgedWithDecoyParams))


@dataclasses.dataclass
class _Real:
    a: int


# ARM 3 — a plain subclass of a real dataclass.
class _PlainSubclass(_Real):
    pass


arm(3, "a PLAIN SUBCLASS of a real dataclass", lambda: E.establishes(a=int)(_PlainSubclass))

# ARM 4 — an INSTANCE of a real dataclass.
arm(4, "an INSTANCE of a real dataclass", lambda: E.establishes(a=int)(_Real(a=1)))


# ARM 5 — a genuine params object, a hand-written Field.
class _HandWrittenField:
    name = "a"
    _field_type = object()


class _ForgedWithStolenParams:
    __dataclass_fields__ = {"a": _HandWrittenField()}


_ForgedWithStolenParams.__dataclass_params__ = vars(_Real)["__dataclass_params__"]

arm(5, "a STOLEN genuine params object + a hand-written Field",
    lambda: E.establishes(a=int)(_ForgedWithStolenParams))


# ARM 6 — THE RESIDUE. Genuine machinery, built the way this module builds its own probe.
@dataclasses.dataclass
class _GenuineButEmpty:
    pass


arm(6, "GENUINE machinery, no fields — THE DECLARED RESIDUE, expected ADMITTED in BOTH trees",
    lambda: E.establishes()(_GenuineButEmpty))

print("population of governed_types() at the end of this run:", len(E.governed_types()))
print("NOTE: that number is a function of IMPORT HISTORY, not of the artefact. Measured:")
print("  after `import crash_detector.establishment` alone .... 0")
print("  after `import crash_detector.witness.panel` .......... 5")
print("  after `import crash_detector.engine.config` ......... 26")
print("  after a wide import ................................. 31")
print("A CARRIER THAT READS IT MUST DERIVE THE IMPORT ITSELF. tests/test_field_establishment.py")
print("does exactly that in `_import_the_whole_product()`, by walking the package with pkgutil.")
