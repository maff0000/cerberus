"""P-K — `CD-PL-F104` RE-MEASURED BY `CD-ENG-WO2R3-04`, INDEPENDENTLY, ARM BY ARM.

**THIS IS NOT A COPY OF `PL-AB0`.** The Project Lead handed its probe over as EVIDENCE the
dispatched Engineer was *"required to re-measure and free to contradict"*. A re-measurement
that re-runs the original seat's driver measures the driver. This one is written from the
FINDING TEXT — `governance/reconciliation/WO-2R3/README.md`, the five-arm table — and it asks
each arm's question in its own way. Where it agrees with `PL-AB0` it agrees independently;
where it does not, it says so on the line.

**IT IS AN INSTRUMENT THAT REPORTS AND IT IS NOT A CARRIER** (CD-RULE-006). It exits 0
whatever it measures. The carriers for the three `establishment` dispositions are the
`DEFECT_OPEN` rows in `tools/sweep/declared_dispositions.py` and `tests/test_the_fifteen.py`.

    PYTHONPATH=src python3 -B variants/WO-2R3/P-K-the-establishment-forged-governed-type-re-measured.py

**IT PRINTS THE TREE IT IMPORTED ON THE FIRST LINE** (CD-PL-F98: two arms of a probe once
resolved their import root from `__file__` and BOTH ARMS IMPORTED THE SAME TREE, printing
identical output). Point PYTHONPATH at a different extraction and the line changes; if it does
not change, the two runs are one run.

TWO DIFFERENCES FROM `PL-AB0`, BOTH RECORDED BECAUSE ONE CUTS EACH WAY:

  * **ARM 5 IS RUN UNDER A FULL PACKAGE IMPORT, NOT A BARE ONE.** `PL-AB0` measured
    `governed_types()` going 0 -> 1 with only `crash_detector.establishment` imported, and
    stated that limit rather than leaving it to be found. Under a full import the baseline is
    not zero and the delta is still exactly one, so **the consequence does not depend on the
    bare-import condition.** The finding is stronger without its own stated limit.
  * **ARM 6 IS THIS SEAT'S AND IS NOT IN `PL-AB0`.** It asks whether the shipped docstring
    actually makes the claim arm 2 falsifies, instead of taking the finding's word for it.
"""

import dataclasses
import pathlib
import sys

import crash_detector.establishment as E
import crash_detector.observations as O

print(f"tree: {pathlib.Path(E.__file__).resolve()}")
print(f"python: {sys.version.split()[0]}")
print(f"`establishes` in __all__: {'establishes' in getattr(E, '__all__', [])!r}")
print()

print("ARM 1 — is `establishes` reachable from ORDINARY in-process caller code?")
try:
    @E.establishes(x=int)
    @dataclasses.dataclass(frozen=True)
    class CallerType:
        x: int

    print(f"  YES. decoration SUCCEEDED on a caller-authored class; instance {CallerType(x=1)!r}")
    print("  => `cls` at BOTH _declared_field_list duck sites is a CALLER-SUPPLIED operand")
except Exception as exc:  # noqa: BLE001
    print(f"  NO. REFUSED: {type(exc).__name__}: {exc}")
print()

print("ARM 2 — does the `dataclasses.is_dataclass` gate admit a NON-dataclass?")


class Hostile:
    __dataclass_fields__ = {}


print(f"  dataclasses.is_dataclass(Hostile) -> {dataclasses.is_dataclass(Hostile)!r}"
      "   <- it is itself a hasattr probe")
try:
    E.establishes()(Hostile)
    print("  YES. establishes()(Hostile) SUCCEEDED on a plain class carrying the attribute.")
except Exception as exc:  # noqa: BLE001
    print(f"  NO. REFUSED: {type(exc).__name__}: {str(exc)[:140]}")
print()

print("ARM 3 — can caller-written data STEER the InitVar refusal?")


class ForgedField:
    name = "x"

    class _field_type:      # noqa: N801
        name = "_FIELD_INITVAR"


class ForgedCls:
    __dataclass_fields__ = {"x": ForgedField}


try:
    names, initvars = E._declared_field_list(ForgedCls)
    print(f"  names={names!r} initvars={initvars!r}")
    print(f"  STEERED: {bool(initvars)!r}  <- an InitVar fault refuses EVERY construction")
except Exception as exc:  # noqa: BLE001
    print(f"  raised: {type(exc).__name__}: {exc}")
print()

print("ARM 4 — is `self` at `getattr(self, name, _ABSENT)` caller-controlled?")
subject = None
for candidate in vars(O).values():
    if (isinstance(candidate, type) and dataclasses.is_dataclass(candidate)
            and candidate in getattr(E, "_DECLARATIONS", {})):
        subject = candidate
        break
print(f"  subject chosen from the LIVE package at run time (not named here): {subject!r}")
if subject is not None:
    try:
        class Sub(subject):     # noqa: N801
            pass

        print(f"  YES. SUBCLASSING SUCCEEDED -> {Sub!r}; the probed instance can be a caller's")
    except Exception as exc:  # noqa: BLE001
        print(f"  NO. subclassing REFUSED: {type(exc).__name__}: {str(exc)[:160]}")
print()

print("ARM 5 — THE CONSEQUENCE ARM, under a FULL package import and not a bare one.")
before = set(E.governed_types())
print(f"  governed_types() BEFORE = {len(before)}   <- PL-AB0 measured this as 0 under a BARE")
print("                                            import of `establishment` alone, and said so")


class Hostile2:
    __dataclass_fields__ = {}


try:
    E.establishes()(Hostile2)
except Exception as exc:  # noqa: BLE001
    print(f"  establishes()(Hostile2) REFUSED: {type(exc).__name__}")
after = set(E.governed_types())
print(f"  governed_types() AFTER  = {len(after)}   delta {len(after) - len(before)}")
print(f"  is_establishing_type(Hostile2)   -> {E.is_establishing_type(Hostile2)!r}")
print(f"  establishment_faults(Hostile2)   -> {E.establishment_faults(Hostile2)!r}")
print(f"  establishment_field_list(Hostile2) -> {E.establishment_field_list(Hostile2)!r}")
print(f"  Hostile2 in (after - before)     -> {Hostile2 in (after - before)!r}")
print()

print("  THE COUNTERFACTUAL — the same arm WITHOUT the forged attribute:")


class Honest:
    pass


try:
    E.establishes()(Honest)
    print("    Honest ADMITTED — THE COUNTERFACTUAL FAILS AND THE ARM ABOVE PROVES NOTHING")
except Exception as exc:  # noqa: BLE001
    print(f"    Honest REFUSED: {type(exc).__name__}: {str(exc)[:110]}")
print(f"    is_establishing_type(Honest) -> {E.is_establishing_type(Honest)!r}")
print()

print("ARM 6 — THIS SEAT'S OWN, NOT IN PL-AB0: does the shipped docstring make the claim")
print("        arm 2 falsifies, or is the finding quoting something that is not there?")
doc = E.establishes.__doc__ or ""
print(f"  ':raises EstablishmentFault:' present in establishes.__doc__: "
      f"{':raises EstablishmentFault:' in doc!r}")
for line in doc.splitlines():
    stripped = line.strip()
    if "raises EstablishmentFault" in stripped or "not a dataclass" in stripped:
        print(f"    | {stripped[:118]}")
print()

print("ARM 7 — THIS SEAT'S OWN: WHO READS THE SURFACES ARM 5 MOVED?")
print("        The consequence arm's evidence is four introspection functions. If no module")
print("        under src/ calls them, the FORGED GOVERNED TYPE is minted into a surface only")
print("        carriers read — which does not touch arms 1-4 and does bound arm 5.")
import ast  # noqa: E402

package_root = pathlib.Path(E.__file__).resolve().parent
watched = (
    "governed_types", "is_establishing_type", "establishment_faults",
    "establishment_field_list", "declared_establishment",
)
callers: dict = {name: [] for name in watched}
for path in sorted(package_root.rglob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            called = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if called in callers:
                callers[called].append(f"{path.relative_to(package_root)}:{node.lineno}")
for name in watched:
    print(f"  {name:26s} callers under src/: {callers[name] or 'NONE'}")
print()
print("  DECLARED LIMIT OF ARM 7, and it is the same limit `_carrier_only_violations` declares:")
print("  it reads CALL EXPRESSIONS BY NAME. An aliased call, a getattr on the module, or a call")
print("  through a container is invisible to it. IT IS A FLOOR ON THE CALLER SET AND NOT A PROOF")
print("  OF ITS EMPTINESS. NOT PROVED TO BE CARRIED ANYWHERE.")
