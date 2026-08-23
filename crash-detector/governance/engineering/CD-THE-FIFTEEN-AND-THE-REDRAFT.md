# THE FIFTEEN DISPOSITIONS AND THE `UPSTREAM_OF_THE_PATH` REDRAFT

**status: THE PROJECT LEAD'S CONTENT FOR THE ONE ACT · authority PO-DECISIONS-0015 rulings 1, 4, 6**
prepared by: PROJECT_LEAD_SEAT_01 at BL-20260823T024708Z-0117 · executes CD-D-160, CD-D-161

> **THIS SUPERSEDES `CD-PROPOSAL-ELEVEN-DISPOSITIONS.md`. IT DOES NOT EDIT IT** (PBG-CONT-003).
> That draft stays readable exactly as written, including the six Category C dispositions this
> document reverses and the count this document corrects. **Corrections supersede, never edit.**
>
> **THIS FILE IS STILL NOT THE REGISTER.** The register is `tools/sweep/declared_dispositions.py`
> on branch `wo-2r3`, and **NOT ONE OF THESE FIFTEEN IS WRITTEN INTO IT.** This is the content;
> a dispatched Engineer writes it, because it is code on the lane and never this seat's own hand
> (`PBG-AUTH-006`, CD-D-160).

---

## 0. The count, measured and not transcribed

PL-MEASURED at `af2accb`, `python3 -B tools/sweep/delegated_judgement_sweep.py`, **EXIT 1**:

```
CD-CLASS-2-SWEEP: FAIL — 534 sites, 15 violations
```

**15 = 13 UNDECLARED ADMISSION SITES + 2 UNDECLARED MODULES.** Ten admission sites and one module
in `crash_detector.admission`; three admission sites and one module in
`crash_detector.establishment`.

**AND THE AUDITOR'S OWN ARITHMETIC IS CORRECTED HERE, IN ITS FAVOUR ON THE POINT AND AGAINST IT ON
THE NUMBER.** `F-06-I` is RIGHT that "the eleven" is a stale name and right to retire it. Its
recommendation reads *"fourteen sites and two modules need a disposition"* — **that is sixteen, and
the instrument prints fifteen.** Thirteen sites, not fourteen. The finding's substance stands
untouched; its closing count is one high. **This is the third time in this programme an instrument
has beaten a count carried in prose, and the third time the instrument won** (CD-RULE-009).

---

## 1. THE REDRAFT — `UPSTREAM_OF_THE_PATH`, bound to the SITE register

PO-DECISIONS-0014 ruling 1 rejected the drafted word **for exactly the reasons its own author
measured**: it bound the MODULE register where its siblings bind the SITE register, and its two
fields (`decides`, `route`) were prose no machine can check. It ordered it *"REDRAFTED to bind the
SITE register with machine-checkable fields."*

The name is kept. The Product Owner ordered it redrafted, not renamed.

### 1.1 The binding

`UPSTREAM_OF_THE_PATH` is **REMOVED** from the words `DECLARED_MODULE_DISPOSITIONS` may carry and
is admitted **only** in `DECLARED_ADMISSIONS`, whose site keys the sweep already emits for tier-2
deciding operations as well as tier-1 admissions.

### 1.2 The two mandatory fields, both machine-checked

| field | value | what the instrument CHECKS |
|---|---|---|
| `operand_origin` | one of `SOURCE_DECLARATION` · `MODULE_CONSTANT` · `OWN_CONSTRUCTION` · `CALLER_SUPPLIED` | **membership in a CLOSED set the instrument owns.** Any other string REFUSES the row. |
| `gates` | a SITE KEY 4-tuple `(module, qualname, category, expression)` naming the downstream **tier-1 admission** whose establishment this site's decision governs | **(a)** the key EXISTS in the sweep's own measured site set; **(b)** its module is **NOT** the declaring site's module. |

**AND ONE CONDITIONAL FIELD, WHICH IS THE WHOLE POINT OF THE WORD.** If `operand_origin` is
`CALLER_SUPPLIED`, the entry **MUST** also carry `finding`, and that finding **MUST** resolve to an
`OPEN` row in the findings register, **or the row REFUSES.**

**WHY THAT CLAUSE AND NOT A LONGER WORD LIST.** The binding constraint the Project Lead wrote
against itself was *"no new word may be a synonym for 'not looked at'"*. Under this redraft, using
the word forces you to say **where the operand came from**; and saying it came from the caller
forces you to **name the open defect**. There is no spelling of `UPSTREAM_OF_THE_PATH` that records
a caller-controlled operand and claims nothing is wrong. The old draft's `route` field could have
been satisfied by a sentence. This one cannot be satisfied at all without a fact the instrument
independently holds.

**AND `gates` IS THE 'UPSTREAM' HALF MADE FALSIFIABLE.** The claim the word exists to make is *"what
this decides is whether judgement-path doors establish at all"* — previously prose. It now names a
concrete downstream point in another module, and **the day that point moves, is renamed, or dies,
the row refuses.** A claim about a route that survives the route disappearing is not a claim.

### 1.3 The two module entries are DERIVED, never written

A module in the closure is DECLARED when **either** it carries a `DECLARED_MODULE_DISPOSITIONS`
entry in one of the original five words, **or** every one of its tier-2 sites carries a site entry.
`crash_detector.admission` and `crash_detector.establishment` take the second route and **get no
module-level prose claim at all.** The instrument derives the module answer from the site register;
it does not accept a sentence about it.

**THE PRICE, PL-MEASURED, STATED UP FRONT RATHER THAN DISCOVERED BY THE SEAT PAYING IT.** The two
modules carry **33** and **17** tier-2 occurrences respectively — 50 — which collapse to some
smaller number of distinct site keys, because the register declares the EXPRESSION and not each
occurrence of it. **The Engineer measures the true key count; this seat has not, and does not quote
50 as the number of rows.**

This is the register's own declared weakness — *"a module-level claim is WEAKER than a per-site one
… THE WEAKNESS IS THE LIMIT"* — closed for exactly the two modules where the strongest claim in the
register was resting on the weakest instrument.

### 1.4 ⚠ THIS IS A READING, AND IT IS THE EXPENSIVE ONE

The Product Owner ordered the word bound to the SITE register with machine-checkable fields. It did
**not** say the module entries decompose into site entries. **THE CHEAPER READING EXISTS AND IS
NAMED HERE SO IT CAN BE TAKEN IN ONE SENTENCE:** keep a MODULE-level entry whose fields *reference*
site keys — machine-checkable, far fewer rows, and it leaves the word bound where the ruling said
it must not be bound.

**THIS SEAT TAKES THE LITERAL READING** because "binds the SITE register" is not ambiguous and
because the cheap reading preserves precisely the module/site asymmetry the ruling gave as its first
reason for rejection. **IF THAT IS WRONG IT IS WRONG EXPENSIVELY, IN AN ENGINEER'S BUDGET**, and
that is stated here rather than left in the diff.

---

## 2. THE FINDINGS REGISTER — minimal, and its rows

PO-DECISIONS-0014 ruling 1: *"id, raised_at (boundary SHA), status (OPEN / CLOSED / SUPERSEDED),
nothing else … An index, not a system."* `DEFECT_OPEN.finding` and the redrafted
`UPSTREAM_OF_THE_PATH.finding` resolve against it **or the row refuses**.

**NOTHING ELSE. NOT a title, NOT a severity, NOT a description.** A findings register that carries
prose becomes the hand-maintained summary it was created to stop, and this project has met that
defect twice already. The finding's *substance* lives in the document that raised it; this is an
index that answers one question — *does this id exist, and is it open?*

| id | raised_at | status | where the substance lives (NOT a register field) |
|---|---|---|---|
| `CD-F-0001` | `af2accb` | `OPEN` | fifth seat, T8 Category A — `VERDICT-FIFTH-SEAT.md` §M6 |
| `CD-F-0002` | `af2accb` | `OPEN` | sixth seat, **`F-06-R`** — `VERDICT-SIXTH-SEAT.md` |
| `CD-F-0003` | `af2accb` | `OPEN` | sixth seat **`F-06-D`**, understated, corrected in the worse direction by **`CD-PL-F103`** |
| `CD-F-0004` | `af2accb` | `OPEN` | **`CD-PL-F104`** — this boundary, `governance/reconciliation/WO-2R3/README.md` and `PL-AB0` |

**THE `raised_at` VALUES ARE THIS SEAT'S CLAIM AND THE ENGINEER RESOLVES THEM WITH `git rev-parse`,
NEVER BY TRANSCRIPTION** (CD-PL-F36).

---

## 3. THE FIFTEEN

### Category A — one site. UNCHANGED from the draft, and it was right.

**1.** `crash_detector.admission::_is_defined_in_a_class_body` · `DUCK` ·
`getattr(entry_point, '__qualname__', '')` → **`DEFECT_OPEN`**

| field | value |
|---|---|
| `finding` | `CD-F-0001` |
| `measured_reach` | one writable attribute, in-process, before decoration; bounded to parameters named in `_RECEIVER_NAMES` (`self`/`cls`), which is one identifier wide and not zero — `assert_closed_presentation_surface(cls)` on the serving path is a real module-level function with a parameter named `cls` |
| `counterfactual` | without the assignment: `UndeclaredParameter: free_function2 is a FAULTED door and every call to it is refused` |

The site falsifies its own shipped docstring, which says the property *"is not something a caller can
influence"*. **IT CLOSES NOTHING AND IS NOT AN EXEMPTION.** CD-D-153 prohibited increment 7 from
fixing it; its remediation is a separate ruling and is still owed.

### Category B — three sites. UNCHANGED. `CARRIER_ONLY` was ratified as drafted.

**2.** `admission_faults` · `DUCK` · `getattr(door, FAULTS_ATTRIBUTE, ())`
**3.** `declared_admissions` · `DUCK` · `getattr(door, ADMITS_ATTRIBUTE, {})`
**4.** `is_admitting_door` · `DUCK` · `hasattr(door, ADMITS_ATTRIBUTE)`
— all three `crash_detector.admission`, all three → **`CARRIER_ONLY`**

| field | value |
|---|---|
| `callable` | the enumerated carrier callers — `tests/test_admission.py`, `tests/test_judgement_path_doors.py`, `tests/test_collector_runner.py`. **MACHINE-CHECKED by `_carrier_only_violations`: callers under `src/` are ENUMERATED, not claimed, and the build breaks the day somebody adds an import.** |
| `why_it_is_not_product_judgement` | each believes any object carrying the attribute — `is_admitting_door(Liar()) = True`, `declared_admissions(Liar()) = {'x': 'whatever'}`, `admission_faults(Liar()) = ()`. The blast radius is a carrier believing a claim an object makes about itself. |

### Category C — six sites. **RE-DISPOSITIONED. THE DRAFT WAS WRONG AND ITS GROUND IS DEAD.**

The draft dispositioned all six `OUT_OF_BOUND` on the ground *"no caller-controlled route"*. **That
ground is falsified twice independently** — by the sixth seat's `F-06-R` and by the Project Lead's
own `CD-PL-F103`, which measured the metaclass admission bypass **end to end on an ordinary,
source-honest `@admits(value=int)` door reporting ZERO faults.** PO-DECISIONS-0015 ruling 4:
*"a disposition whose reason has died does not survive on habit."*

All six → **`DEFECT_OPEN`**:

| # | site (all `crash_detector.admission`) |
|---|---|
| **5** | `_EstablishedHere.__call__` · `ISINSTANCE` · `isinstance(because, str)` |
| **6** | `_compile` · `ISINSTANCE` · `isinstance(declaration, _Admission)` |
| **7** | `_compile` · `ISINSTANCE` · `isinstance(declaration, tuple)` |
| **8** | `_compile` · `ISINSTANCE` · `isinstance(declaration, type)` |
| **9** | `_type_tuple` · `ISINSTANCE` · `isinstance(value, type)` |
| **10** | `each_of` · `ISINSTANCE` · `isinstance(within, tuple)` |

| field | value |
|---|---|
| `finding` | `CD-F-0002`, with `CD-F-0003` as the lever |
| `measured_reach` | a **subclass** satisfies the `isinstance` and then supplies the behaviour. C4 verified by the sixth seat personally; the other five measured on the same lever — a `str` subclass whose `strip` lies gets an **unexplained exemption** through the one guard that exists to stop exactly that; an `_Admission` subclass whose `refusal` returns `None` **and whose `describe()` reports `"exactly PanelRow"`**; a `tuple` subclass whose `__iter__` yields something other than what `repr` and `len` show |
| `counterfactual` | exact-type identity at the same site refuses the subclass — the discipline the module already applies to VALUES and does not apply to DECLARATIONS |

**WHY THE FIFTH SEAT WAS NOT WRONG, WHICH MATTERS.** Its narrow claim — *these are consumed at
decoration from a source-written declaration and there is no caller route* — is **correct**, and the
sixth seat says so in terms. **The defect is that "no caller-controlled route" was the wrong test.**
The module's own doctrine is that a subclass is never trusted; **the declaration vocabulary is
admitted by `isinstance` at all six sites while the value vocabulary is not.** `OUT_OF_BOUND`
recorded the weaker half of the fact, **and `OUT_OF_BOUND` is a scope claim no instrument can
falsify** — which is why replacing it with a word that carries a resolvable finding is not a
relabelling.

### The three `crash_detector.establishment` sites — READ FOR THE FIRST TIME AT THIS BOUNDARY

No seat had read these one at a time. The sixth seat listed the governing question in its own §4 as
something **it could not establish**. The Project Lead measured it rather than hand an Engineer an
invented disposition — `PL-AB0`, five arms, pristine extraction, tree line on every arm.

All three → **`DEFECT_OPEN`**:

**11.** `_declared_field_list` · `DUCK` · `getattr(cls, '__dataclass_fields__', {})`
**12.** `_declared_field_list` · `DUCK` · `getattr(field._field_type, 'name', '')`
**13.** `establishes.apply_at_the_boundary.__init__` · `DUCK` · `getattr(self, name, _ABSENT)`

| field | value |
|---|---|
| `finding` | `CD-F-0004` |
| `measured_reach` | **`establishes` is PUBLIC and in `__all__`.** Ordinary in-process caller code decorates its own class, so `cls` at sites 11 and 12 is **CALLER-SUPPLIED**. The `dataclasses.is_dataclass` gate above them is itself a `hasattr` probe: a plain class carrying `__dataclass_fields__ = {}` passes it and `establishes()(Hostile)` **SUCCEEDS**, where the shipped docstring says it `:raises EstablishmentFault:`. The caller then holds a **FORGED GOVERNED TYPE** — `is_establishing_type` → `True`, `establishment_faults` → `()`, and it **ENTERS `governed_types()`** (measured 0 → 1 under a bare import of `establishment` alone, and that limit is stated). At site 13, `crash_detector.observations.OK` **subclasses successfully**, so the probed instance can be the caller's. |
| `counterfactual` | the same arm without the forged `__dataclass_fields__` attribute: `EstablishmentFault` at decoration, and the class never enters `governed_types()` |

**THIS IS `F-06-R`'s SENTENCE, ONE MODULE ACROSS, IN A PUBLIC EXPORTED ENTRY POINT, AND NO DOCUMENT
SAID SO.** `CD-PL-F104`, HIGH, raised at this boundary, against a module this seat has reconciled
three times without reading these three lines.

### The two modules — the redrafted word, DERIVED from the sites above

**14.** `crash_detector.admission` — 33 tier-2 occurrences
**15.** `crash_detector.establishment` — 17 tier-2 occurrences

No module-level prose claim. Each clears when every one of its tier-2 sites carries a site entry
under §1.

---

## 4. Tally

| disposition | count | change from the draft |
|---|---|---|
| `DEFECT_OPEN` | **10** | was 1 — Category C's six and the three `establishment` sites join it |
| `CARRIER_ONLY` | 3 | unchanged |
| `OUT_OF_BOUND` | **0** | **was 6. Every one of them is gone and its ground is on the record as dead.** |
| `UPSTREAM_OF_THE_PATH` *(redrafted, site-bound, derived at module level)* | 2 modules | was 1 module, in a word the PO rejected |
| **total** | **13 sites + 2 modules = 15** | was "the eleven" |

**THE REGISTER GETS MEASURABLY REDDER AND THAT IS THE CORRECT DIRECTION.** Ten `DEFECT_OPEN` rows
is a register honestly describing a system with ten open defects in its admission and establishment
mechanisms. **A register full of `DEFECT_OPEN` buys nothing — not a pass, not an exemption, and it
does not make the sweep green.** The sweep will still exit non-zero on other grounds and the WO-2
gate stays SHUT.

## 5. What this document does not claim

That the fifteen are correct. They are one seat's reading of two auditors' measurements plus one
probe of its own, and **the three `establishment` sites are a FIRST-AND-ONLY reading exactly as the
fifth seat's T8 was** — the reading that Category C has just been reversed for trusting. **THE
SEVENTH ASSURANCE SEAT IS TOLD, IN ITS DISPATCH, THAT THESE FIFTEEN ARE A TARGET AND NOT A SETTLED
RECORD.** The fourth seat's best result, and the sixth seat's, both came from disbelieving a
disposition the record had already settled.
