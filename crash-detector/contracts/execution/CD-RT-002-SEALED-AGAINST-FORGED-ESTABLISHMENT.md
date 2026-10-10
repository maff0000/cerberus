# Execution contract — CD-RT-002-SEALED-AGAINST-FORGED-ESTABLISHMENT

**CD-AC-002** and **CD-AC-005** · no governed class this tree declares can be constructed with
forged state by a route that executes no package code · obligation **MANDATORY** · scope **CLASS**
· delivered in **WO-2R3 increment 9**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every declared
test to name an execution contract that RESOLVES. It states how this test is run and what its exit
codes mean. **It states no result.** The register carries obligations; status is computed by the
validator from the register, the PID and append-only run records, and there is no field anywhere in
this chain in which an author could write a verdict.

## The proposition

> **A GOVERNED CLASS MUST NOT BE CONSTRUCTIBLE WITH FORGED STATE BY A ROUTE THAT EXECUTES NO
> PACKAGE CODE.**

Deliberately **not** *"cannot be forged"*. No in-process guard can say that, and this check does not
try. The proposition is about **WHO REFUSED**. If a route reaches an object of the exact governed
type, carrying attacker-supplied field values, and not one line under `src/crash_detector/` ran,
then this package decided nothing and its establishment boundary was not consulted — it was walked
around.

Ordered by the Product Owner at `PO-DECISIONS-0016` **ruling 2**:

> "THE CLASS OF 99 IS SEALED — INCREMENT 9, BEFORE THE SEVENTH SEAT (Q2/F-06-J). CD-PL-F104 and
> CD-D-166 are ADDED: the sealing property (no `__new__` + `__dict__.update` route around
> establishment) is required of the CLASS — instrument-enumerated over all 99 governed classes,
> exclusions MEASURED AND DECLARED never assumed, a plant in the established contrast form.
> **Fourth widening, same law: floors are not populations, and a remedy applied to 13 of 99 is a
> census with extra steps.**"

The measurement that produced the ruling is the sixth Assurance seat's `F-06-J`: *"THE REMEDY EXISTS
IN THIS TREE, IS APPLIED TO 13 TYPES, AND WAS NEVER ASKED OF THE OTHER 77. … A body edit cannot
[remove the boundary]. A caller declining to use the boundary can, for 77 of 99 governed types, and
that question was never in the closure's scope."*

## What this check is, and what it is not

**IT IS THE ACCEPTANCE TEST FOR THE CLASS. IT IS NOT THE CLOSURE.** The closure is the `__slots__`
declaration on each class plus an empty `__dictoffset__`, and the absence of any `__setstate__`
that is not this package's own. This check ENUMERATES the class from the artefact and fails on any
member the property is required of and does not hold for.

**IT IMPORTS THE SUBJECT, AND ITS SIBLING DELIBERATELY DOES NOT.**
`check_constructor_field_establishment.py` parses, so an auditor who trusts nothing in the
implementation can run it against a tree they extracted themselves. **THIS CHECK CANNOT DO THAT,
BECAUSE THE PROPERTY IS A RUNTIME PROPERTY.** `__dictoffset__` is a C-level slot on the type object;
`__setstate__` is installed by `dataclasses._add_slots` *after* the class body has been read; and
*"executes no package code"* is a statement about execution, measured with `sys.settrace`. **EVERY
ESCAPE ON THIS PROJECT'S RECORD PASSED A STATIC CHECKER.**

**IT REPORTS; IT IS NOT THE CARRIER.** `tests/test_sealed_against_forged_state.py` is what fails.

## How it is run

```bash
python3 -B tools/register/check_sealed_against_forged_establishment.py --root .
python3 -B tools/register/check_sealed_against_forged_establishment.py --root . --why
```

`--root` is the repository root of the tree under audit, not the package directory. `--why` prints
the full ledger: every class examined, its verdict, its measured exclusion clause where it has one,
and the outcome of every route.

**THE CHECK VERIFIES THAT IT IMPORTED THE SUBJECT TREE AND NOT SOME OTHER ONE.** Before measuring
anything it evicts every already-imported `crash_detector*` module, puts `<root>/src` and
`<root>/tools/register` at the front of `sys.path`, and then asserts that each imported module's
`__file__` resolves under `--root`. If it does not, the check REFUSES. A contrast run with the wrong
tree on `sys.path` is indistinguishable from a fix that does nothing (`CD-PL-F98`).

## Exit codes

| code | meaning |
|---|---|
| `0` | PASS **AGAINST THE DECLARED ROUTES ONLY** — see LIMIT 7, which the check itself prints after this verdict on every run. Every class the property is required of holds it; every class it is not required of carries a MEASURED, PRINTED exclusion. The assertion count is printed and a run making zero assertions REFUSES rather than passing. **A `0` HERE IS NOT A CLAIM THAT ANY CLASS IS SEALED AGAINST DELIBERATE IN-PROCESS FORGERY, AND THE SAME RUN PRINTS THE MEASURED COUNT OF CLASSES THAT ARE NOT.** |
| `1` | FAIL. At least one of: a class open to a declared route with the seal available to it; a class whose seal availability could not be measured; the two population derivations disagreeing in either direction. |
| `3` | PRECONDITION_NOT_MET. `--root` is not a tree with `src/crash_detector` and the sibling instrument; the subject does not import; or an imported module resolved outside the subject tree. **Never a pass and never a skip** (`PBG-CI-002`). |

## The population, and why no count is written here

**IT IS OBTAINED BY IMPORTING THE SIBLING INSTRUMENT FROM THE SUBJECT TREE AND CALLING ITS OWN
`_classes()`** over the same file set — every `*.py` under `src/crash_detector` not in a
`__pycache__`. Reused, not reimplemented and not transcribed. **RUN THE CHECK AND READ ITS OWN
POPULATION LINE.** A count read from a run is a measurement; a count copied into a document is a
transcription that goes stale exactly as an unpointed-at copy does (`CD-RULE-009`, `CD-PL-F91`).

That is derivation ONE. Derivation TWO is a `vars()` descent over the **imported modules**, at any
nesting depth, recording every class whose `__module__` is that module. **THE TWO ARE DIFFED AS SETS
AT EVERY RUN AND DISAGREEMENT IN EITHER DIRECTION IS A VIOLATION, NOT A RECONCILIATION.** The check
does not adopt either reading, does not take the union and does not take the intersection for its
verdict. A class inside `if False:` is in the source and not live; a class built by `type(...)` is
live and in no source reading. Both are real and both are reported.

## The declared route set

| | |
|---|---|
| `R1` | `cls.__new__(cls)` then `__dict__.update(...)` — the route the record names |
| `R2` | `object.__new__(cls)` then `__dict__.update(...)` — the same, past an overridden `__new__` |
| `R3` | `copyreg._reconstructor(cls, object, None)` then `__dict__.update(...)` — what `pickle` protocols 0 and 1 do, reached from an untrusted byte string |
| `R4` | `cls.__new__(cls)` then `__setstate__(MAPPING state)` — the sibling the ruling names |
| `R5` | `cls.__new__(cls)` then `__setstate__(SEQUENCE state)` |

**R2, R3 AND R5 ARE IN THE SET BECAUSE MEASUREMENTS CONTRADICTED THE SET, WHICH IS THE ONLY REASON A
SET IS ALLOWED TO GROW ON THIS PROJECT.**

* with `R1` alone, five `enum.Enum` subclasses report *"the route does not reach an instance"* —
  `Enum.__new__()` demands a value — and **R2 forges every one of them**;
* with `R4` alone, `StalenessWindow` and `FreshnessEvidence` were scored **SEALED WHEN THEY ARE
  NOT**. CPython's `dataclasses._dataclass_setstate` *zips* `fields(self)` against the state, so a
  MAPPING writes field NAMES as values and the forged marker never lands. **A ROUTE THAT FAILS FOR
  THE WRONG REASON SCORES A CLASS CLOSED**, which is the `CD-ENG-WO2R3-F12` standard failing inside
  the instrument that cites it. Both shapes are offered because both exist here:
  `DialMagnitude.__setstate__` and `DeclaredQuantity.__setstate__` index by name and need the
  mapping; the stdlib one zips and needs the sequence.

## The exclusion — ONE clause, and it is measured by construction

`PO-DECISIONS-0012` ruling 2 removed vocabularies from this project's instruments. **THERE IS NO
LIST OF EXCLUDED CLASSES AND NO LIST OF EXCLUDED BASES ANYWHERE IN THIS CHECK.**

For each class the check walks `__mro__` to find the base that imposes an instance `__dict__`, then
**BUILDS A THROWAWAY SUBCLASS OF THAT BASE AT RUN TIME** — through the base's own metaclass
protocol, so a metaclass declaring `__prepare__` is given what it asked for — declaring
`__slots__ = ()`, and **READS THE RESULTING `__dictoffset__`**. The class is excluded only if that
number is non-zero **AND** the base is OUTSIDE this package, because a base we own carrying a
`__dict__` is our defect to fix and never our exclusion to claim.

*"It is `AdmissionFault`"* is a list entry. *"A probe subclass of `builtins.BaseException` declaring
`__slots__ = ()` still reports `__dictoffset__ == 16` on this interpreter"* is a measurement, taken
on this run. **IF A FUTURE INTERPRETER MAKES SUCH A BASE SEALABLE, THIS CHECK REQUIRES THE SEAL OF
THOSE CLASSES ON THE VERY NEXT RUN, WITH NO EDIT TO ANY FILE.**

**AN EXCLUSION THE CHECK CANNOT MEASURE IS NOT AN EXCLUSION.** If the probe subclass cannot be
built, the class is reported `UNMEASURABLE` and is a **violation**, not an exemption. The first
draft of the probe called `type(base)(name, (base,), {...})` with an ordinary dict and five
`enum.Enum` subclasses came back `AttributeError: 'dict' object has no attribute '_member_names'` —
**an instrument reporting its own defect as a property of the subject.** Recorded rather than
quietly fixed.

## Declared limits (`CD-RULE-004`)

Stated identically here, in the header of
`tools/register/check_sealed_against_forged_establishment.py`, and in the register entry.

**LIMIT 1 — IT IMPORTS THE SUBJECT.** Importing executes the subject's module-level code. An auditor
who will not import an untrusted tree should run this in a container, and should not read the
parse-only sibling as proving the same proposition.

**LIMIT 2 — THE ROUTE SET IS DECLARED, NOT PROVED COMPLETE.** A route nobody has thought of is
invisible to this check exactly as it is to every other guard here. A green run means *"none of
these five reached an object"* and it means nothing wider.

**LIMIT 3 — THE EXCLUDED CLASSES ARE NOT SAFE, THEY ARE UNSEALABLE.** Every one of them can still be
reached by at least one route in the set. **THAT RESIDUE IS NOT PROVED TO BE CARRIED ANYWHERE**
(`CD-RULE-006`), and a green run of this check is not evidence about it. The counts and the per-base
probe measurements are printed unconditionally, so that *"not required"* can never mean *"not looked
at"*.

**LIMIT 4 — WHAT A SEALED VERDICT DOES NOT SAY.** It says the declared routes did not reach an
object carrying forged state. It says nothing about a **subclass** of that class, which carries no
seal of its own (the same shape as `establishment.py`'s DECLARED LIMIT 4); nothing about what a
caller does with a legitimately constructed instance; and nothing about the `CD-BP-003` door, which
HANDS in-package execution to any caller and is measured in `establishment.py`'s own declared limit.

**LIMIT 5 — THIS CHECK REPORTS; IT IS NOT THE CARRIER.** A check that both measures a property and
is the only thing that would notice its removal is one instrument wearing two hats. The runtime
contrast lives in `tests/test_sealed_against_forged_state.py`.

**LIMIT 6 — THERE IS NO IMPORT-TIME REFUSAL, AND THAT IS DELIBERATE AND DATED.** A class added
without `__slots__` imports cleanly; nothing in the package objects, and this boundary check is what
catches it. An import-time guard was BUILT (`src/crash_detector/sealing.py`) and REMOVED, because a
new package module enters the Class-2 sweep's import closure and can only be dispositioned in
`tools/sweep/declared_dispositions.py`, which `PO-DECISIONS-0017` ruling 2 protects until after the
seventh Assurance seat. **DEFERRED WITH A REASON, NOT DROPPED**, and it is the natural companion to
the act that clears the three stale keys.

**LIMIT 7 — WHAT `SEALED` MEANS IN THIS INSTRUMENT'S OWN EXIT, AND IT IS NOT THE ENGLISH WORD. THE
EXIT CARRIES THIS LIMIT ON EVERY RUN.** Ordered by the Product Owner at `PO-DECISIONS-0018`
**ruling 1(b)**, and the sentence is the Product Owner's own bytes, carried into `BLUEPRINT` §16
`CD-D-172` and §17 `CD-BP-005`:

> "**The instrument's exit carries its declared limit**: SEALED means *sealed against declared
> routes; NOT sealed against deliberate in-process forgery, which the platform does not permit
> preventing*. A green board that says exactly that is honest; a green board that says more is the
> sixth false green."

**A DOCSTRING IS NOT AN EXIT.** Limits 1–6 have been true and unread since this check was written,
because a reader runs it and reads its last line. So `main()` prints this limit to stdout **AFTER**
the `PASS`/`FAIL` line, in a `finally`, **on every exit path — 0, 1, 2 and 3, and an unhandled
exception** — with **THIS RUN'S OWN MEASURED NUMBERS IN IT**. `Check.done` in `tools/register/
_support.py` prints the verdict line and that module is not this check's to edit, which is why the
limit is printed after it rather than woven into it.

**AND THE LIMIT CARRIES A NUMBER, NOT AN ADJECTIVE (`CD-RULE-003`).** Two further routes are
EXECUTED against every class on every run and their outcomes are counted and printed:

| | |
|---|---|
| `F1` | `cls.__new__(cls)` then `object.__setattr__(instance, member, FORGED)` — the value forged on the instance, past `@dataclass(frozen=True)` and past a `__slots__` descriptor |
| `F2` | `type.__new__(<metatype>, name, bases, namespace)` — the TYPE forged rather than a value, attempted only where the governed class is itself a metatype |

**F1 AND F2 ARE NOT IN THE DECLARED ROUTE SET, ARE NOT COUNTED AS ASSERTIONS, AND DO NOT MOVE THE
VERDICT — DELIBERATELY, AND FOR TWO REASONS THAT ARE BOTH LOAD-BEARING.** First, appending them and
calling the class closed is what the Product Owner named *the census game* and ruled out in ruling 1:
*"an enumeration cannot close a property-defined class — and this class is defined by a platform
property we do not control."* Second, scoring them would make this check permanently RED for
`object.__setattr__` and `type.__new__`, **which are CPython working as documented** — a red no edit
to this package could ever clear, reported as though it were a defect somebody could fix. §17
`CD-BP-005` declares preventing them **OUT OF SCOPE: HIGH, ACCEPTED AND DECLARED**.

**THE RESIDUE OF THAT MEASUREMENT IS SPLIT BY REASON AND NEVER POOLED**, because a route that fails
for the wrong reason scores a class closed — the `CD-ENG-WO2R3-F12` standard that `R5` already exists
because of. Each class is reported `FORGED`, `NO STATE TO FORGE` (the object WAS reached, with exact
type and zero package lines, but the class declares no `__slots__` member and no dataclass field for
the probe to write, so *"not forged"* is **VACUOUSLY TRUE OF A STATELESS OBJECT AND IS NOT A SEAL**),
`NOT FORGED`, or `NOT REACHED` with the constructor's own exception type and message. **RUN IT AND
READ ITS NUMBERS**; none is transcribed here (`CD-RULE-009`, `CD-PL-F91`).

**WHAT THIS CHECK THEREFORE STILL DOES NOT CLAIM.** It does not claim any governed class is sealed
against deliberate in-process forgery — it claims the opposite, with a count, and the exit says so.
It does not claim `CD-ASR-WO2R3-04-F01`, `CD-AC-002` or `CD-AC-005` is closed, and it opens no gate.
The defence against deliberate in-process forgery is **DETECTION** — witness divergence and the
provenance chain, the FORGERY-DETECTION OBLIGATION owed at **WO-3** as a first-class criterion (§16
`CD-D-172`) — **and it is not built yet.** Meanwhile the blast radius is what §17 states: the
detector is ADVISORY (`D1`) and no money moves on it (`D2`).

## The plant

`plants/CD-AC-005/CD-RT-002-SEALED-AGAINST-FORGED-ESTABLISHMENT.patch`, applied with `git apply` to
a pristine `git archive` extraction, **with `git apply`'s own exit code recorded as a third
column** — a patch that does not apply produces a "violated" arm that is the clean tree and exits 0,
which is a dead plant reporting a pass behind a green board.

The measured arms are in the register entry. The one worth repeating here: **on the violated arm the
SIBLING constructor check still exits 0 with `PASS — 101 assertions, 0 violations`.** The planted
class is ruled out of the sibling's population by two of its three clauses at once. That contrast
IS the widening, measured rather than argued.
