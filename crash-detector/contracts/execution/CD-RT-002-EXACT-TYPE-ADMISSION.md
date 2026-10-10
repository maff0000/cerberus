# Execution contract — CD-RT-002-EXACT-TYPE-ADMISSION

**CD-AC-002** · a forged metatype subclass is refused at the judgement-path door, because
admission is by exact type · obligation **MANDATORY** · scope **CLASS** · delivered in
**WO-2R3 increment 10, ITEM_1**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every declared
test to name an execution contract that RESOLVES. It states how this test is run and what its exit
codes mean. **It states no result.** The register carries obligations; status is computed by the
validator from the register, the PID and append-only run records, and there is no field anywhere in
this chain in which an author could write a verdict.

## The proposition

> **THE FORGED SUBCLASS IS STILL CONSTRUCTIBLE — THE PLATFORM PERMITS IT AND THIS CHECK DOES NOT
> CLAIM OTHERWISE. IT IS REFUSED AT THE JUDGEMENT-PATH DOOR, BECAUSE ADMISSION IS BY EXACT TYPE.**

Deliberately **not** *"the forged type is prevented"*, **not** *"the class is sealed"*, and **not**
*"CD-ASR-F01 is closed"*. **THREE SEATS HAVE BEEN SUPERSEDED ON THIS PROJECT FOR CLAIMING A CLASS
CLOSED THAT WAS NOT**, and `PO-DECISIONS-0018` ruling 1 has now settled the question in terms:

> "Appending R6/R7 is the census game; 'deriving from the attribute model' is the census game
> wearing a derivation, because CPython's attribute model is OPEN BY DESIGN: `object.__setattr__`
> and `type.__new__` are the platform working as documented. Seven gates and two programmes have
> now taught the same sentence — **an enumeration cannot close a property-defined class** — and
> this class is defined by a platform property we do not control."

So the proposition is about **WHAT THE FORGERY IS WORTH**. The forged instance passes `isinstance`
BY CONSTRUCTION and can never be made to fail it; it fails exact type BY CONSTRUCTION and can never
be made to pass it. **THAT ASYMMETRY IS THE WHOLE REMEDY**, and this check asserts the half of it
this project controls.

Ordered by the Product Owner at `PO-DECISIONS-0018` **ruling 2**:

> "**F01 GETS ITS OWN ENGINEER, FIRST** — the Project Lead's reading is adopted. The forged-type
> walk (metatype subclass passing `isinstance` with zero package lines) crosses the boundary the
> sealing defect only festers inside. The fix is this project's own existing standard applied where
> it is missing: EXACT TYPE, everywhere on a judgement path where an `isinstance` still survives —
> sites enumerated BY INSTRUMENT, the forged-subclass probe as the plant, both arms. Bounded, real,
> and it kills the resurrection of CD-ASR-F01 at the sites that matter."

The measurement that produced the ruling is the seventh Assurance seat's `CD-ASR-WO2R3-04-F01`
(HIGH, a live control bypass), and its own diagnosis:

> "`type.__new__(metaclass, ...)` does not call `metaclass.__new__`. The guard is written in
> `SealedMagnitudeType.__new__` and is therefore only on the path that the `class` statement takes.
> **It guards the syntax, not the type.**"

## What this check is, and what it is not

**IT BUILDS THE FORGED CLASS ITSELF, IN EVERY RUN, AND PRINTS THAT IT SUCCEEDED.** That is not a
concession buried in a footnote; it is `CD-EXACT-ARM2-002`, an ASSERTED premise. If the forged class
ever stops being constructible, or stops passing `issubclass`/`isinstance`, or stops coercing to the
forged number, **this check goes RED** — because a guard whose hazard has silently evaporated is
measuring nothing, and its clean exit would then be the sixth false green on this project.

**IT IS NOT A CENSUS AND DOES NOT CLAIM TO BE ONE.** Four sealed metatypes, one judgement-path door
each. The instrument that enumerates the whole judgement-path population is
`tools/sweep/delegated_judgement_sweep.py`; the per-site carriers for increment 10's twelve
exact-type conversions are `tests/test_exact_type_admission_sweep.py`.

**IT IS A REGRESSION TEST ON A PRODUCT RULING, AND THAT IS ARM 1.** `PO-DECISIONS-0018` ruling 1(a)
keeps the declared-route refusals — *"they are real, they refuse the front door and the named
routes, and they proof the product against ACCIDENT and against casual misuse"*. Arm 1 asserts that
`class Evil(V): ...` still raises each module's own surface violation. **A CHANGE THAT MAKES ARM 1
STOP REFUSING HAS BROKEN ACCIDENT-PROOFING THE PRODUCT OWNER EXPLICITLY KEPT**, and this check is
where that shows up.

**IT REPORTS; IT IS NOT THE CARRIER FOR THE SWEEP.** The twelve site conversions fail in
`tests/test_exact_type_admission_sweep.py`, not here. This check carries the four metatypes.

## How it is run

```bash
python3 -B tools/register/check_exact_type_admission.py --root .
```

`--root` is the subject tree. The check inserts `<root>/src` on `sys.path`, evicts any already
imported `crash_detector` modules, imports the subject, and **prints the resolved
`crash_detector.__file__` it actually imported** (`CD-PL-F98`: a contrast run with the wrong tree on
`sys.path` is indistinguishable from a fix that does nothing).

## Exit codes

| exit | meaning |
|---|---|
| 0 | clean — every arm held at all four metatypes and all four doors refused with the declared identity |
| 1 | violation, with the rule id, the door and the observed outcome |
| 2 | usage |
| 3 | precondition not met — `<root>/src/crash_detector/__init__.py` absent, or the subject tree did not import |

**Never a skip, for any reason** (`PBG-CI-002`). A tree that will not import is a tree this check
REFUSES on, never one it passes: *"refused" is a runtime claim, and every escape on this project's
record passed a static checker.*

## What is asserted

| rule | proposition |
|---|---|
| `CD-EXACT-ARM1-001` | the declared route `class Evil(V)` still raises that module's own surface violation — at all four sealed types |
| `CD-EXACT-ARM2-002` | the forged route STILL WORKS: class created, `issubclass` True, instance built, `float(inst)` the forged number, `isinstance` True, package lines within the per-site measured ceiling |
| `CD-EXACT-ARM2-003` | `type(instance) is V` is **False** — the asymmetry, asserted about the object and not assumed about the design |
| `CD-EXACT-DOOR-004` | the judgement-path door REFUSES the forged instance, **with the declared refusal identity for that door** |

The doors and their declared refusal identities:

| sealed metatype | victim | judgement-path door | declared refusal |
|---|---|---|---|
| `SealedMagnitudeType` | `DialMagnitude` | `dials.magnitude::_established_quantity` | `NotAdmitted` |
| `SealedQuantityType` | `DeclaredQuantity` | `dials.provenance::derived_within_one_dial` | `QuantityProvenanceMissing` |
| `SealedReadingType` | `Degraded` | `serving.dial_presentation::present_dial` | `NotAdmitted` |
| `SealedPresentationType` | `NotShown` | `serving.dial_presentation::is_shown` | `NotAdmitted` |

**A REFUSAL OF A DIFFERENT IDENTITY IS A VIOLATION, NOT A DETAIL** (`CD-PL-F74`). A body that
admitted the object and then tripped over a missing attribute has not refused it — *"the right
outcome from the wrong layer"* is this project's most-repeated defect and this check will not score
it as a pass.

## Declared limits (CD-RULE-004)

**Stated identically here, in the header of `tools/register/check_exact_type_admission.py`, and in
this test's `negative_control.violation` in `required-tests.yaml`. A register entry may not claim
more than its guard delivers.**

1. **FOUR DOORS, NOT EVERY DOOR.** Not a census. See above.
2. **IT PROVES NOTHING ABOUT ROUTES IT DOES NOT WALK.** `object.__setattr__`, `cls.__new__(cls)`
   state forgery, `__reduce__`, `__class__` reassignment on a live object and `ctypes` are not
   exercised. `CD-RT-002-SEALED-AGAINST-FORGED-ESTABLISHMENT` is a different instrument on a
   different property and **is not cited as support for anything here.**
3. **IT IMPORTS THE SUBJECT TREE.** Importing executes the subject's module-level code. An auditor
   who will not import an untrusted tree should run this in a container.
4. **EIGHTEEN `isinstance` ADMISSIONS SURVIVE IN THE PACKAGE AND THIS CHECK LOOKS AT NONE OF THEM.**
   Each carries a written, measured reason at its own site. Four of them are the metatype `__new__`
   guards themselves, where `isinstance` is the **stricter** operator because the predicate REFUSES:
   converting them would ADMIT an ordinary `class` statement through one forged intermediate, which
   was MEASURED on all four at WO-2R3 increment 10. **THAT RESIDUE IS CARRIED BY THE WRITTEN
   DECLARATIONS AND BY `tests/test_exact_type_admission_sweep.py`, AND BY NOTHING IN THIS CHECK.**
5. **THE PACKAGE-LINE CEILING IS PER SITE AND IS NOT ZERO EVERYWHERE.** Zero at three metatypes,
   FOUR at `SealedReadingType` — all four being `SealedReadingType.__setattr__` invoked by
   `typing.Generic` machinery on a class that is not in `_SEALED`, traced line by line, and **not
   one of them a refusal**. A uniform ceiling of zero would have been false on the day it was
   written.

## The planted violation

`plants/CD-AC-002/CD-RT-002-EXACT-TYPE-ADMISSION.patch` replaces `is_exactly(value, self.types)`
with `isinstance(value, self.types)` in `_Exactly.refusal` — **one line, at the single point where
every `@admits` parameter and every `@establishes` field decides what it accepts.** It is the exact
regression `F-06-D` corrected at increment 8, and it is the shape this project has now made four
times and called a simplification. Under it the door still reports `faults: ()`, `is_admitting_door`
is still `True`, and the refusal message still reads *"this door requires exactly X"*.

**A CHECK THAT CANNOT FAIL IS NOT A CHECK.** The three-column contrast — clean arm, `git apply`'s
own exit code, violated arm — is recorded in the WO-2R3 build log for increment 10 and is not
transcribed here (`CD-RULE-009`: a count copied is a transcription).
