# Execution contract — CD-RT-001-ABSENCE-RENDERS-UNKNOWN

**CD-AC-001** · Missing or stale input never renders as calm · obligation **MANDATORY** · scope **CLASS** ·
delivered in **WO-2**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

With no source registered and with a dead feed, both dials read Unknown or Degraded and the serving layer renders UNKNOWN — never a number, never the previous value.

## Command

```
PYTHONPATH=src python3 -m pytest tests/test_reading.py tests/test_evaluate.py tests/test_dial_presentation.py -q
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

`tests/test_dial_presentation.py` JOINED THIS DECLARED COMMAND AT WO-2R2 INCREMENT 1c, closing `CD-ASR-WO2R-F03`. The command GREW; **nothing was removed from it**, and `tests/test_reading.py` and `tests/test_evaluate.py` are unchanged in what they assert. It is here because the register may not claim a layer it declares no test for (`CD-RULE-004`): the criterion's words are about RENDERING, and until that increment this criterion's runtime arm evidenced only that absence could not be CONSTRUCTED as a number, never that a number a consumer CHOSE for an absence could not be presented as a dial. That is the half `ASR2-001-A` walked through. The new file executes the auditor's own shape and asserts both halves of the result: the number is still computed — that is the declared limit, boundary A, and it is asserted rather than hidden — and it cannot be presented.

`tests/test_reading.py` attacks the `Reading` sum type by asserting **set equality** between each constructor's attribute surface and a surface declared in the test file itself. `tests/test_evaluate.py` exercises the WO-2 shipped state: the source registry is EMPTY by PO ruling, so both dials must read Unknown, and that path is executed rather than assumed. It also exercises the **absence post-condition** directly, in both directions.

## Why it is asserted this way

The empty registry is not a temporary inconvenience — it is the doctrinally correct empty state the Product Owner ruled in PO-ACCEPT-BLUEPRINT-0001, and it is what makes this criterion demonstrable before a single source exists.

**This is the arm that carries CD-AC-001's "structurally incapable" half, and after CD-ASR-F02 it had to be rebuilt.** The original surface test asserted only that no name from `ARITHMETIC_DUNDERS` appeared in `vars(Unknown)` — a blacklist, which an auditor walked past with a plain `magnitude` property (`E03`). Absence yielded `0.0` while both declared guards stayed green. Four layers of structure now close it, each enforced by the interpreter at a different moment:

1. **definition time** — a declared member surface asserted by equality while the module is imported, so a member added in a class body makes `import crash_detector.dials.reading` raise `ReadingSurfaceViolated`;
2. **instance time** — `__slots__`, so `object.__setattr__(reading, "magnitude", 0.0)` raises `AttributeError` rather than sticking;
3. **subclass time** — subclassing a Reading constructor is refused, and `fold`/`is_value` dispatch on exact type identity rather than `isinstance`;
4. **consumption time** — `fold`, `is_value` and `DialSet` re-verify the surface of the reading's actual class on every call.

Separately, for CD-ASR-F03, the per-dial evaluator carries a **post-condition** that re-derives from its own arguments whether the dial got its required inputs and refuses a value-bearing reading if it did not — whatever the number is and wherever it came from.

**The declared surface is written out twice on purpose**: once in `reading.py`, because the runtime seal needs it, and once in `tests/test_reading.py`, which asserts the two agree. A test importing the module's table would pass a plant that edited the class and the table together.

## DECLARED LIMIT — the one residue, declared rather than denied

Required by `CD-RULE-004`. Stated identically in the header of `src/crash_detector/dials/reading.py` and in the comment above this test's entry in `required-tests.yaml`.

`type.__setattr__` installs a class attribute without going through a metaclass, and CPython offers no way to prevent that. Executable example:

```python
type.__setattr__(Unknown, "magnitude", property(lambda self: 0.0))
Unknown(reason="R", since_utc=t, missing_inputs=()).magnitude    # -> 0.0
```

What **is** closed is every route by which such a number reaches a consumer: `fold`, `is_value` and `DialSet` each raise `ReadingSurfaceViolated` on a reading of a mutated class, and the test suite proves both halves — that the mutation succeeds, and that every boundary refuses it.

So what this test evidences is: **absence cannot acquire a numeric member through construction, assignment, inheritance or definition, and a class mutated after import is refused wherever a reading of it would be used.** It does **not** evidence the stronger claim that a process which rewrites class objects at runtime cannot read a number back out of one it mutated. **Do not read a clean run as proof of the stronger claim.**

## Preconditions

* `python3` 3.11 or later with `pytest` available on the interpreter, and
  `jsonschema` for the modules that read the envelope contracts. Nothing else, and no
  install step.
* `PYTHONPATH=src` is part of the command line, not an environment the auditor is expected
  to have arranged. The package is importable from the source tree with no install.
* The working directory is the root of the subject tree the auditor extracted.

## Exit semantics

| exit | meaning |
|---|---|
| `0` | every test in the named modules passed. |
| `1` | at least one test failed — the failing assertion and its module are named in the output. |
| `2` · `3` · `4` | interrupted, internal error, or usage/collection error. None of these is a pass, and none may be read as one. |

No test in these modules may skip. A conditional skip is a hole with a comment in it, and
a suite that can skip its way to green is not evidence.

## Negative control

Absence made to yield a number at runtime, **by any route**, or a reading that carries a value produced by a dial that did not get its inputs. The class includes, and is not limited to:

* any member added to a Reading constructor's declared attribute surface — a property, a classvar, a method, a `__getattr__`, a slot, a dunder, numeric or not — added in the class body, by a decorator, by class assignment, or by a metaclass;
* an undeclared instance attribute set through `object.__setattr__`;
* a subclass of a Reading constructor carrying a numeric member;
* `evaluate()` returning `Value` or `Degraded` for a dial whose required inputs were absent, stale, future-dated, unregistered or lacking a contribution model — whether the number is a literal, a module-level constant, a configuration default, a previous magnitude carried across a gap, or a value read from the store.

With the WO-2 empty source registry both dials must read Unknown; a plant that makes either read a value must fail this test. Subject to the DECLARED LIMIT above.

Detection is a **contrast**, and the validator computes it as one: the same declared command
must exit `0` on the clean subject and non-zero on the subject with the violation planted.
A clean arm that fails cannot be told apart from a broken harness, and a broken harness
detects nothing — the validator returns `UNDECIDABLE`, never `PASS`.

The negative control for this test is declared as run record **`RTR-WO2-0001`**.
That record does not exist yet. It is the run the **independent Assurance
seat** will produce — a distinct actor from the one that wrote this test. Until it exists
the validator computes `UNDECIDABLE` for this test and the gate stays shut, which is
correct: this seat may declare which run must evidence its guard, and may not supply it.

## What this contract does not claim

It does not claim the test passes. It does not claim the criterion is satisfied. It does not
admit any evidence: `latest_admitted_run` is null in the register and this seat cannot fill
it in, because an implementation may not certify itself (`PBG-SOD-001`, non-waivable).

---

## DECLARED LIMITS 10 AND 11 — NEW AT WO-2R3 INCREMENT 8 (`PO-DECISIONS-0015` ruling 1)

This is the **third** of the three CD-RULE-004 places these two limits are declared in. The other
two are the header of `src/crash_detector/engine/evaluate.py` and the
`CD-RT-001-ABSENCE-RENDERS-UNKNOWN` entry of `required-tests.yaml`.

**THE NUMBERING RUNS AS ONE SEQUENCE ACROSS THREE HEADERS AND NOT THREE LISTS.** Limits 1–4 and
7–9 are the static check's (`tools/register/check_judgement_path_doors.py`); 5–6 are `admits`'s
(`src/crash_detector/admission.py`); **10 and 11 are the CD-ASR-F03 MECHANISM'S.** An auditor who
reads only one header has read part of what this row declares open — CD-PL-F81, ruled CD-D-111,
now applying to a third header.

### Why they exist at all

`PO-DECISIONS-0012` ruling 1 held that `_evaluate_dial` was *"reachable only through doors that
already establish"*. That half was **falsified by measurement twice independently** — a conforming,
declared-foreign `SourceAdapter` obtains the module from `sys.modules` on the second collection
cycle and reaches the **undecorated** evaluator through `__closure__`, passing no door. The
consequence the Product Owner had pre-committed to was taken in full: **`guarded` becomes a DOOR
and `CD-ASR-F03` is REDESIGNED, not repaired.** These are the residues the redesign leaves.

### 10 — THE BODY CAN BE RECONSTITUTED FROM ITS CODE OBJECT

Property (a) of the ruling is met **as the ruling states it**: after
`_absence_is_never_a_number` returns, **no undecorated evaluator object exists**. Every cell of
`_evaluate_dial.__closure__` holds data; `__wrapped__` is never created (`functools.wraps` is not
used at all, which is a strictly stronger answer to `PO-DECISIONS-0013` ruling 2 than the
`delattr` it replaces); and a walk across `__closure__`, `__wrapped__`, `__globals__` and the
module namespace finds **nothing callable**.

**THAT IS NOT THE SAME CLAIM AS "THE `__closure__` REACH IS CLOSED", AND THIS LIMIT EXISTS SO
NOBODY READS IT AS ONE.** Executable example:

```python
cells    = [c.cell_contents for c in evaluate._evaluate_dial.__closure__]
code     = next(c for c in cells if isinstance(c, types.CodeType))
globals_ = next(c for c in cells if isinstance(c, dict) and "Value" in c)
types.FunctionType(code, globals_)(starved_spec, {}, now, None)   # no door, no post-condition
```

**CARRIER MEASURED, AND IT ASSERTS THE RESIDUE *TRUE*:**
`tests/test_the_absence_door.py::test_the_reconstitution_residue_is_real_and_is_declared_limit_10`
performs exactly that reconstitution and **requires it to succeed**, so this paragraph cannot go
stale in the reassuring direction. The day the reconstitution stops working, that test goes red and
this limit is corrected in all three places rather than quietly enjoyed — the same discipline the
superseded closure assertion in `tests/test_evaluate.py` carried, and the reason anybody could tell
the closure route had closed.

**WHAT ACTUALLY CHANGED, WITHOUT DECORATION.** Before: the cell **held** the callable and one
attribute access reached it. Now: the cell holds materials and an attacker must **construct** a
callable from them. Same reach, one more line of interpreter-internals work.
**CARRIER FOR PREVENTING THE RECONSTITUTION: NOT PROVED TO BE CARRIED ANYWHERE**, and CPython
offers no way to prevent it — the sentence `admission.py`'s DECLARED LIMIT 6 (a) already carries
about the closure reach in general.

### 11 — THE DERIVATION DROPS A GENERIC'S SUBSCRIPT

`usable: dict[str, OK]` derives to *exactly a `dict`* and says nothing about its keys or its
values. Executable example: `_evaluate_dial(spec, {"src.a": object()}, now)` **passes this door**.

**CARRIER MEASURED, ONE LEVEL UP:** `_latest_usable_ok` builds the only `usable` any product
caller supplies and admits an outcome only when `type(outcome) is OK`.
**FOR A DIRECT CALLER SUPPLYING ITS OWN `dict`: NOT PROVED TO BE CARRIED ANYWHERE** — the
post-condition re-derives from `spec` and from the **keys** of `usable` only.

**AND THE ANNOTATION CHANGE THIS LIMIT SITS ON IS DECLARED RATHER THAN INHERITED (`CD-PL-F109`).**
`_evaluate_dial`'s `usable` moved `Mapping[str, OK]` → `dict[str, OK]`, because the establishment
is derived from that annotation and an abstract `Mapping` has no exact type to derive.
**IT IS NOT A NARROWING OF WHAT THE PRODUCT ACCEPTS, AND THAT IS MEASURED AND NOT ARGUED.** Two
arms, one axis, run in both trees:

| arm | base `314592c` | tip |
|---|---|---|
| a plain `dict` (control) | ADMITTED → `Unknown` | ADMITTED → `Unknown` |
| a `collections.abc.Mapping` that is not a `dict` | **REFUSED — `NotAdmitted`**, raised by `refuse_a_number_without_its_inputs` | **REFUSED — `NotAdmitted`**, raised by `_evaluate_dial` |

The accepted set is identical. **Only the point of refusal moves** — from after the body has run
to before it binds — because `refuse_a_number_without_its_inputs` has always declared
`usable=dict` and has always fired on every call through the net.

---

## DECLARED LIMIT 12 — NEW AT WO-3 INCREMENT `16B-FIX`, PLACED HERE AT `16B-FIX-2` (`FX8`)

*** **THIS COMMAND IS NAME-COUPLED TO THE CONTRACT'S `$defs`, BY DESIGN AND NOT BY ACCIDENT.**
Ruled by `PROJECT_LEAD_SEAT_02` on `CD-ASR-WO3-05` F6. ***

**WHY IT IS ONLY ARRIVING NOW, SAID PLAINLY.** `16B-FIX` declared this limit in **one** of the
three places `CD-RULE-004` requires, and **declared the shortfall rather than widening its own
scope to close it** — neither this file nor `tests/test_detail_level.py` was in `CD-ENG-WO3-06`'s
writable scope, and `tests/**` was protected by the very ruling the limit records. `CD-ASR-WO3-06`
(v) held that to be the right Engineer action and a wrong closure, and it was. The
`16B-FIX-2` dispatch **granted** both paths. This is the second of the three places; the third is
the module docstring of `tests/test_detail_level.py`, whose **assertions did not move and which
still reports `52 passed`** — the FX4 ruling protects that file's assertions, not its prose.

**WHAT WAS MEASURED, AND IT CUTS BOTH WAYS.** `CD-ASR-WO3-05` built a tree carrying a **pure
refactor with zero behavioural change**: `$defs/absent_data_detail_level` renamed to
`missing_data_render_level`, both branch `$ref`s repointed, its enum reordered to
`[acute, elevated]`, and the whole `$defs` mapping reversed. `calm` is still unrepresentable on
both missing-data branches on both surfaces. **The register-wired behavioural instrument
`CD-RT-001-MISSING-DATA-NEVER-CALM` PASSES it** — `67 assertions, 0 violations` — which is the
behavioural-not-structural design **vindicated by measurement**, and precisely what a
`$ref`-target-name checker would have failed. **BUT THIS COMMAND FAILS IT:** `6 failed / 46
passed` in `tests/test_detail_level.py`, all six reading schema keys **by name**. Before increment
`16B` no `execute:` line ran that file, so the brittleness was not the register's; growth made it
the register's.

**RULED: ACCEPT THE COUPLING AND DECLARE IT. DO NOT LOOSEN THE ASSERTIONS.** The reason is on the
record and is contestable: `absent_data_detail_level` is not an implementation detail on this
project — **both** contracts' own prose names it as the enforcement point for a **constitutional**
clause (PID §3.2). A rename that silently repoints it is exactly the change that *should* require
someone to open the register and think. Loosening these assertions to follow the `$ref` instead of
matching its target's name would buy refactor comfort with constitutional visibility, and that is
the wrong trade at this criterion.

*** **AND `CD-ASR-WO3-06` GAVE THAT RULING A SECOND, INDEPENDENT REASON NOBODY HAD NOTICED, WHICH
IS RECORDED HERE BECAUSE IT CHANGES HOW CONTESTABLE THE RULING IS.** *** `CD-ASR-WO3-05` F6's
named remedy was to *"move the name-coupled assertions behind a resolver that follows the `$ref`
instead of matching its target's name"*. **Measured on tree `X2` (this project's arm `C11`), that
remedy would have made the escape invisible to the entire register**: a resolver following
`#/$defs/absent_data_detail_level` finds the narrow enum, because on `X2` the narrow enum is still
there and still referenced — it is simply no longer the only path. **On that tree the five
name-coupled assertions in `tests/test_detail_level.py` were the ONLY thing in thirty `execute:`
lines that moved.** Two open items on this row therefore pointed in opposite directions. **`FX5`
resolves the tension the right way round** — the escape is now caught by the *behavioural*
instrument as `CD-CALM-BRANCHES-006`, so the guarantee no longer rests on the name coupling — and
the coupling is still not loosened, because nothing has yet made it safe to loosen.

**WHAT IT COSTS, STATED SO NOBODY REDISCOVERS IT AS A DEFECT:** a pure rename of that `$def`, with
behaviour provably unchanged, turns this row **RED** and requires a deliberate edit to
`tests/test_detail_level.py` plus a record of why. **THE COST IS PRICED AND NOT ACCIDENTAL.** And
the risk is named: a guard which fires on correct trees gets disabled, and then it guards nothing.
The mitigation is that the sibling row `CD-RT-001-MISSING-DATA-NEVER-CALM` is purely behavioural
and passes such a tree, so the constitutional guarantee is never carried by the name-coupled half
alone.

### Numbering — because `CD-ASR-WO3-06` could not verify it and said so

**DECLARED LIMIT NUMBERS ARE PER REGISTER ROW, NOT PER FILE.** Limits 1–12 above are
`CD-RT-001-ABSENCE-RENDERS-UNKNOWN`'s, one sequence across four headers and not four lists: 1–4
and 7–9 in `tools/register/check_judgement_path_doors.py`, 5–6 in
`src/crash_detector/admission.py`, 10–12 here and in `required-tests.yaml`. The **sibling** row
`CD-RT-001-MISSING-DATA-NEVER-CALM` has its **own** independent 1–12 sequence, in the header of
`tools/register/check_missing_data_never_calm.py`, in `required-tests.yaml`, and in
`contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md`. **Both rows live in
`required-tests.yaml`, so a bare "DECLARED LIMIT 12" is ambiguous there and always was — quote the
row id with the number.**
