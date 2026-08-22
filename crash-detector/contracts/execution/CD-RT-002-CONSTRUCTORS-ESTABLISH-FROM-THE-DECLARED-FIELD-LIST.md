# Execution contract — CD-RT-002-CONSTRUCTORS-ESTABLISH-FROM-THE-DECLARED-FIELD-LIST

**CD-AC-002** and **CD-AC-005** · every public type in the frozen subject, on a judgement path,
whose field establishment is BODY-BORNE derives that establishment from its DECLARED FIELD LIST at
the class boundary · obligation **MANDATORY** · scope **CLASS** · delivered in
**WO-2R3 increment 5**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every declared
test to name an execution contract that RESOLVES. It states how this test is run and what its exit
codes mean. **It states no result.** The register carries obligations; status is computed by the
validator from the register, the PID and append-only run records, and there is no field anywhere in
this chain in which an author could write a verdict.

## The proposition

> **Every public type in the frozen subject, on a judgement path, whose field establishment is
> BODY-BORNE establishes each of its DECLARED FIELDS by EXACT TYPE at the class boundary, derived
> from the DECLARED FIELD LIST rather than written into `__post_init__`.**

BP-AMENDMENT-0001 §D.1's principle is *establishment derived from the declaration, never written
into an editable body*. `admits` applies it to a CALLABLE's signature. The Product Owner applied the
same principle one level down at `PO-DECISIONS-0007` ruling 1 (CD-D-105, answer (A)):

> "The principle that decides it is §D.1's own: establishment derived from the declaration, never
> written into an editable body. **`__post_init__` IS A BODY.**"

and then re-based its own ruling at `PO-DECISIONS-0008` ruling 2 (CD-D-114), from a list of four
named types to A CLASS:

> "AN ENUMERATION CANNOT CLOSE A PROPERTY-DEFINED CLASS — this estate's most expensive lesson, and I
> applied it to the kernel while writing a list into my own ruling. … the four named types plus
> `AttemptRecord` are the FLOOR, NOT THE POPULATION."

## What this check is, and what it is not

**IT IS THE ACCEPTANCE TEST FOR THE CLASS. IT IS NOT THE CLOSURE.** The closure is
`crash_detector.establishment.establishes`, and its declared limits are in that module's header and
are reproduced below. This check ENUMERATES the class from the artefact and fails on any member that
does not carry the declaration.

**IT PARSES; IT DOES NOT IMPORT THE PRODUCT**, so an auditor who trusts nothing in the
implementation can run it against a tree they extracted themselves. That also means **it proves
nothing about runtime behaviour** — every escape on this project's record passed a static checker.
The runtime claim is made by `tests/test_field_establishment.py` and by the variants named below.

**IT WAS BUILT AND RUN BEFORE THE MECHANISM IT CHECKS FOR EXISTED.** That ordering is durable in the
git graph rather than asserted here: the check landed ALONE at `4a5098d`, printing
`POPULATION — THE BODY-BORNE FIELD-ESTABLISHMENT CLASS: 32. DECLARED TO @establishes: 0.`, one
commit before the mechanism. `CD-D-119` required exactly that, on the reasoning that an instrument
written after a mechanism enumerates what the mechanism already covers.

## Command

```
python3 -B tools/register/check_constructor_field_establishment.py --root .
```

and, for the verdict and the reason on every one of the classes examined including the ones ruled
OUT:

```
python3 -B tools/register/check_constructor_field_establishment.py --root . --why
```

Run with the working directory set to **the root of a subject tree the auditor extracted itself** —
`git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The lines above are
verbatim: no path fixing, no editing, no wrapper. There is no run-everything harness in this
repository and there may not be one, because an auditor verifying through a harness the project
wrote is verifying the harness (`PBG-ASSURE-001`).

`python3 -B` so no `__pycache__` is written into the subject tree (`PBG-RT-001` — mutation by
EFFECT, not by label).

## Exit codes

| code | meaning |
|---|---|
| 0 | assertions were made and all of them held |
| 1 | VIOLATION — at least one member of the class does not derive its establishment from its declared field list, or its declaration and its field list disagree, or `@establishes` is applied inside `@dataclass` |
| 2 | USAGE — the command line was wrong |
| 3 | PRECONDITION NOT MET — the check could not do its job, with the reason stated. **This includes a run that made ZERO assertions**: `exit 0` must never be able to mean "I looked at nothing" |

## THE DEFINITION, printed at every run so a reader can disagree with it without reading the source

A class is **IN** the **BODY-BORNE-OR-ABSENT** field-establishment class when **ALL THREE** hold
(widened at `PO-DECISIONS-0010` ruling 1, `CD-D-134`; see CHECK LIMIT 1 for the superseded wording):

1. **PUBLIC** — its name does not begin with `_`.
2. **FROZEN SUBJECT** — it is declared `@dataclass(frozen=True, ...)`.
3. **ON A JUDGEMENT PATH**, by any of three unioned rules, all derived from the tree and none
   trusted alone:
   * **RULE A — judgement-path packages.** Defined under `src/crash_detector/engine/`,
     `.../serving/` or `.../collectors/`. Same package set as the doors check's RULE 1, same limit.
   * **RULE B — door reach.** Its name appears in the `@admits(...)` declaration, a parameter
     annotation or the return annotation of any callable carrying `@admits(...)`. **No list of
     judgement types is written into the check** — the set is read out of the decorations.
   * **RULE C — field reach, transitive.** It is named in the declared field annotation of a type
     already reached, run to a **FIXPOINT**. A type the judgement path carries INSIDE a type it
     already carries is on the judgement path.
   **RULES B AND C RESOLVE MODULE-LEVEL NAMES TO A FIXPOINT**, because both reach types through a
   NAME: `one_of(*READING_CONSTRUCTORS)` spells no constructor and `outcome: 'FetchOutcome'` spells
   no outcome. **The first draft of the check did not resolve them and measured the population at
   18; resolving them measured it at 32.** That defect is recorded in the check's header rather than
   quietly fixed — an instrument that stops at the spelling measures a VOCABULARY, which is the
   error this whole increment is about.
**THERE IS NO FOURTH MEMBERSHIP CLAUSE, AND UNTIL `PO-DECISIONS-0010` RULING 1 THERE WAS.** The
superseded clause read: *"(4) **BODY-BORNE** — it defines `__post_init__` or `__init__` in its own
class body, and that body either names at least one DECLARED FIELD of the class, or reaches the
field list reflectively (`dataclasses.fields`, `__dataclass_fields__`, `__dict__`, `vars`)."*

**WHERE ESTABLISHMENT LIVES NO LONGER DECIDES WHETHER THE RULE REACHES A TYPE. IT IS WHAT THE RULE
REQUIRES OF IT.** The old clause survives as a **REPORTED PROPERTY** — printed on every member's
line as `BODY-BORNE` or `ABSENT`, by exactly the same reading — and it decides nothing.

**THAT READING IS A HEURISTIC AND IS DECLARED AS ONE.** No static reader can tell *establishment*
from *derivation*: a `__post_init__` that merely reads a field to build a message reads as
BODY-BORNE exactly as one that refuses a bad value does. It therefore OVER-REPORTS body-borneness.
**That used to be the safe direction and since the widening it is not a direction at all**, because
a member is required to declare whether its establishment is body-borne, absent or anywhere else.

## What it requires of each member, and the one case that satisfies vacuously

**A FIELDED MEMBER — one declaring at least one field — is asserted three things:**

1. the class carries `@establishes(...)`. **Establishment being ABSENT is no longer an excuse; it is
   the failure.** A fielded public frozen judgement-path type that establishes NOWHERE is a
   **VIOLATION and not an exemption** (`PO-DECISIONS-0010` ruling 1);
2. the field names `establishes` was told about are **EXACTLY** the class's declared field list, in
   **BOTH** directions — **this is P7 at the constructor level, caught statically**;
3. `@establishes` is applied **OUTSIDE** `@dataclass`. Inside it, the field list does not exist yet.

**A ZERO-FIELD MEMBER SATISFIES VACUOUSLY, AND IS ENUMERATED, COUNTED, ASSERTED OVER AND PRINTED
WITH ITS REASON.** It is not dropped and not silently excluded — the ruling says the instrument
asserts over the **WHOLE** enumerated population. Exactly **ONE** assertion is made of it, and the
honest description of that assertion is that it is a **MEASUREMENT OF THE FIELD LIST and not a proof
about establishment**: *this class declares no field whose establishment could be underived.* It is
**REFUTABLE BY EXECUTION** — add one field and the member routes to the fielded branch and fails on
assertion 1 the same run. If a vacuous member *does* carry `@establishes(...)`, assertions 2 and 3
run against it too, so an empty type with an adrift declaration is still caught.

**HOW A READER TELLS "SATISFIED VACUOUSLY" FROM "NOT LOOKED AT", WITHOUT TRUSTING ANYONE.** The
vacuous members are inside `POPULATION`, counted again on their own line, printed one per line with
their reach rule, their zero-length field list, their establishment locus and the words `SATISFIED
VACUOUSLY`, and their assertions are inside the assertion total. A class that was **not** looked at
appears under `--why` as `OUT` with the clause that excluded it, or is not among the classes
examined at all — and `CLASSES EXAMINED` is printed so the two totals reconcile.

## The measurement at WO-2R3 increment 5, and the re-measurement after the widening

**AT INCREMENT 5, BEFORE THE WIDENING (lane `46adf33`).** Population **32**, of **35** public frozen
dataclasses under `src/crash_detector/` and **96** classes examined. **14** by RULE A, **10** by
RULE B only, **9** by RULE C only. **ADJACENT 1** (`observations.py` `Empty`). **OUT 2**
(`store/migrations.py` `Migration`, `store/migrate.py` `AppliedMigration` — BP-AMENDMENT-0001 §B.4
Class C, which §H places out of WO-2R3's scope; the property-based enumeration and the amendment's
scoping agree here, which is a check on both). `32 + 1 + 2 = 35`; every one is named in the output.

**AFTER THE `PO-DECISIONS-0010` RULING 1 WIDENING**, measured by running this row's own `execute`
command in the lane worktree: **POPULATION 33** — **FIELDED 32**, **ZERO-FIELD SATISFYING VACUOUSLY
1** — of **99** classes examined across **39** modules. **14** by RULE A, **10** by RULE B only,
**9** by RULE C only. **ASSERTIONS 96 → 97**, the one added being the vacuous member's.
`ESTABLISHED_HERE` **3**, unchanged. **THE ADJACENT SET READS 0 BECAUSE IT NO LONGER EXISTS AS AN
EXEMPTION**: its single former member, `Empty`, is now IN the population and satisfies vacuously.

**THE WIDENING CHANGED NOT ONE VERDICT.** Every pre-existing assertion held with the same verdict;
this check was GREEN before and is GREEN after. **A green run of this row is therefore not evidence
that the widening was performed** — the unwidened check is green too. The evidence is the contrast
in the negative-controls table below.

**THE FLOOR THE PRODUCT OWNER NAMED IS FIVE** — `ConfigSnapshot`, `DialSpec`, `ModelSpec`,
`PanelRow`, `AttemptRecord` — and all five are IN. **THE FLOOR IS 5/33 AND IT IS NOT THE
POPULATION.**

## The negative controls, both arms, run

| | patches | observed |
|---|---|---|
| **V17 BASELINE** | `V17-constructor-body-escape.patch` + `V35-v17-companion-probe.patch` | `REFUSED: crash_detector.establishment.FieldNotEstablished: ConfigSnapshot.dial_specs[0]=DuckDialSpec is not admitted; every element must be exactly DialSpec` |
| **V17 VIOLATED** | the same, plus `V40-v17-violated-arm-establishes-removed.patch` | `ESCAPED -> ConfigSnapshot CONSTRUCTED with duck dial_specs`; `stored element types: ['DuckDialSpec','DuckDialSpec']`; `spec_for('equity_crash') -> DuckDialSpec` |
| **P7-at-the-constructor BASELINE** | `V39-new-field-on-a-governed-type.patch` | this command exits **1**, `FIELD_NOT_DECLARED_TO_ESTABLISHES`; an ordinary construction that never mentions the new field raises `establishment.UndeclaredField: PanelRow is a FAULTED type and every construction of it is refused`; the suite goes 1537 passed -> **57 failed, 1480 passed** |
| **P7-at-the-constructor VIOLATED** | the same, plus `V41-v39-violated-arm-establishes-removed.patch` | faults **0**; `ADMITTED -> the new field arrived UNGUARDED` |
| **THE SAME MOVE, DIFFERENT TYPE, BASELINE** | `V42-panelrow-canonicalisation-body-deleted.patch` | `REFUSED: establishment.FieldNotEstablished: PanelRow.state=DuckStr` |
| **… VIOLATED** | the same, plus `V41` | `ESCAPED`; stored state type `DuckStr`, stored value `'UNAVAILABLE'`, and `row.state == 'AGREES'` answers **True** — `ASR3-F04`'s sentence reached through a constructor. **Stated without overclaim:** `resolve_panel` still returned `Unavailable` in that arm, so the escape reaches the VALUE TYPE and the resolver's own re-establishment still held |
| **THE WIDENING — OLD ARM** (`46adf33`, pristine `git archive` extraction) | `V43-fielded-judgement-path-type-with-no-establishment.patch` | this command **exits 0**, `PASS — 96 assertions, 0 violations`, and prints `  ADJACENT (not required, and this is a real hole): engine/verdict.py:40 Verdict [RULE A] fields=['score']`. **ADJACENT SET 2** in that arm. The hole, measured, not asserted from one side |
| **THE WIDENING — NEW ARM** (`c18aeb4`, pristine `git archive` extraction) | the same single patch, unchanged | this command **exits 1**, `FAIL — 1 violation(s)`, `VIOLATION src/crash_detector/engine/verdict.py:40 — Verdict is a PUBLIC FROZEN type ON A JUDGEMENT PATH declaring 1 field(s) ['score'], and it carries no @establishes(...). Its establishment is ABSENT ...`. **POPULATION 34, FIELDED 33, DECLARED TO @establishes 32.** The type is IN and it is NAMED |

**THAT LAST PAIR IS THE ONLY PROOF THIS WIDENING HAS**, and it is stated that way on purpose. The
widening altered **no** verdict on the real tree — `Empty`, its one new member, has zero fields and
satisfies vacuously — so a green run of this row cannot distinguish a widening written into the
code path from one written only into this document. **The same patch, exit 0 at `46adf33` and exit 1
at `c18aeb4`, can.**


The command for every probe is `PYTHONPATH=src python3 -B <the probe the patch adds>`, in a separate
pristine extraction per arm. Every row is in `variants/WO-2R3/MANIFEST.md` with its command.

**AND THE THING NOBODY SHOULD MISS.** With V17 applied, **BOTH STATIC CHECKS STILL EXIT 0** — the
doors check `PASS — 54 assertions` and this check `PASS — 96 assertions` — because V17 removes a
BODY and neither check reads bodies. **The closure is a RUNTIME closure and it is proved by running
it.** A clean run of this check is not proof of the proposition.

## DECLARED LIMIT (CD-RULE-004)

Stated identically here, in `tools/register/check_constructor_field_establishment.py`'s header, in
`src/crash_detector/establishment.py`'s header and in the register entry. Numbering runs 1..4 for
the **MECHANISM's** limits and 1..4 for the **CHECK's**; each says which it is. CD-RULE-006 is
applied to every one: a named carrier is MEASURED, or the words **NOT PROVED TO BE CARRIED
ANYWHERE** are written.

### MECHANISM LIMIT 1 — a field's TYPE, never a RELATION BETWEEN TWO FIELDS

§C.5's invariants 2 and 3 (a resolved spec's `dial_id` EQUALS the dial naming it; its input ids are
a SUBSET of the naming `DialSpec`'s declared inputs), `ConfigSnapshot`'s one-spec-per-dial,
`AttemptRecord`'s `requested_utc <= observation.observed_utc`, `CollectionResult`'s
`rows_recorded == attempts_made`, `Agrees`'s `freshness.as_of_utc == as_of_utc` and every registry
uniqueness check **REMAIN BODY-BORNE**. A declared field list says what each field IS and nothing
about what any two of them must be TO EACH OTHER.

**EXECUTABLE EXAMPLE:** `variants/WO-2R3/V36-cross-field-invariant-body-rewrite.patch` deletes the
one-spec-per-dial check and `PYTHONPATH=src python3 -B probe_v36_cross_field_invariant.py` reports
**ACCEPTED** — two equity specs, no monetary spec, every element exactly a `DialSpec`, the boundary
fully satisfied and the object wrong.

**CARRIER MEASURED, AND IT IS BODY-LEVEL:** `tests/test_engine_config.py` and
`tests/test_engine_model_registry.py` measure those bodies refusing today, and V36 measures them
stopping when the body is edited. As a STRUCTURE that survives an edit to those bodies: **NOT PROVED
TO BE CARRIED ANYWHERE.** Raised as `CD-ENG-WO2R3-F18` rather than closed by the seat that found it:
closing it needs a way to derive a RELATION from a declaration, which is a design question.

### MECHANISM LIMIT 2 — `ESTABLISHED_HERE` is an explicit weakening, counted not hidden

**THREE** fields across **THREE** types: `Value.value` and `Degraded.value` (the generic parameter
`T` — which score types a `Reading` may carry is product meaning and fixing it here would be
inventing one, `CD-RULE-003`) and `FetchedResponse.payload` (a foreign payload, CD-BP-003 one type
down). Every use must state a reason in the artefact; a bare `ESTABLISHED_HERE` raises at decoration
and stops the module importing.

**CARRIER MEASURED:** this check PRINTS all three with class, field and line at every run, and
`tests/test_field_establishment.py::test_the_established_here_field_exemptions_are_exactly_this_set`
pins the set, so a FOURTH is a test failure and not a quiet widening. **CARRIER FOR WHAT THOSE THREE
FIELDS HOLD, PARTIAL:** `Value.value` and `Degraded.value` are re-established one level up by
`DialSet.__post_init__`'s `_reject_cross_typed`, **which is itself body-borne**; for
`FetchedResponse.payload`, **NOT PROVED TO BE CARRIED ANYWHERE**.

### MECHANISM LIMIT 3 — the interpreter reach

Inherited from `admission.py`'s DECLARED LIMIT 6 rather than newly incurred. `__wrapped__` is
deleted from the wrapper and the deletion is MEASURED
(`tests/test_field_establishment.py::test_a_governed_type_publishes_no_way_round_its_own_boundary`).

**THE REGISTRY IS NOT A ROUTE, AND THE SEAT THAT WROTE THIS EXPECTED IT TO BE.**
`variants/WO-2R3/V37-establishes-registry-rewrite.patch` ARM 3 rewrites
`establishment._DECLARATIONS` and the construction is **STILL REFUSED**, because the wrapper closes
over its own local `compiled` dict. Rewriting the registry therefore makes the INTROSPECTION SURFACE
LIE in the **safe** direction — `CD-ENG-WO2R3-F13`'s defect inverted. It is recorded rather than
removed, because a seat that tries the obvious thing, sees a refusal and concludes the reach is
closed will be wrong.

**THE ROUTE THAT IS OPEN IS THE CLOSURE CELL**, and it is `V33`'s move one level down. V37 ARM 4
finds the live `compiled` dict in `__init__.__closure__`, rewrites its entries and constructs
`ScoreComputation(magnitude=0.5, contributions=(object(),))` through the ORDINARY front door:
**ESCAPED**, a bare `object` stored. The mutation is to state the boundary SHARES, so every caller in
the process is unguarded afterwards. **NOT CLOSED, NOT CLAIMED, NOT PROVED TO BE CARRIED ANYWHERE.**

### MECHANISM LIMIT 4 — a subclass is not governed, and for a `@dataclass` subclass that reaches its inherited fields too

**THIS SEAT'S FIRST WORDING SAID THE OPPOSITE AND THE MEASUREMENT REFUTED IT.** A `@dataclass`
subclass **REGENERATES** `__init__`, which OVERRIDES the wrapped one, so **not one** of its fields is
established — `variants/WO-2R3/V38-subclass-adds-an-unestablished-field.patch` (a):
`ScoreComputationPlus(magnitude=0.5, contributions=(object(),))` is **ACCEPTED**. A PLAIN subclass,
not itself a dataclass, DOES inherit the wrapped `__init__` and the same construction is
**REFUSED** — V38 (c).

**CARRIER MEASURED, AND ONLY AT THE DOORS:** `Value`, `Degraded`, `Unknown`, `Shown` and `NotShown`
refuse subclassing outright at their metaclass, and every `@admits` door requires an EXACT type —
V38 (d) measures `resolve_panel` refusing a `PanelRow` subclass instance with
`admission.NotAdmitted: row=PanelRowPlus is not admitted; this door requires exactly PanelRow or
None`. For a subclass used ENTIRELY INSIDE this package, reaching no door: **NOT PROVED TO BE CARRIED
ANYWHERE.** Raised as `CD-ENG-WO2R3-F19`.

### CHECK LIMIT 1 — what the widened class still does not reach

**SUPERSEDED AT `PO-DECISIONS-0010` RULING 1, QUOTED RATHER THAN DELETED (`CD-RULE-004`).**

**THE SUPERSEDED WORDING, IN FULL.** It read: *"**CHECK LIMIT 1 — THE ADJACENT SET.** A frozen
public judgement-path type with **NO** establishing body fails clause (4): its establishment is
ABSENT, not body-borne, so it is outside the class the Product Owner ruled and this check does not
require `@establishes` of it. **There is exactly one today** — `observations.py` `Empty`, which has
no `__post_init__` and no declared fields — and it is PRINTED with its file and line at every run.
**THIS IS A REAL HOLE.** A NEW frozen judgement-path type written with no `__post_init__` at all is
outside the ruled class and this check will name it ADJACENT rather than fail. **EXECUTABLE
EXAMPLE:** add `@dataclass(frozen=True)` / `class Verdict: score: float` to
`src/crash_detector/engine/` with no `__post_init__` — this check exits 0 and names it in the
ADJACENT SET. **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.** Raised as `CD-ENG-WO2R3-F17` and
referred to the Project Lead and the Product Owner, because **widening the ruled class is a scope
decision and not this seat's to take** — the increment-5 dispatch's objective says "AND NOTHING
ELSE".*

**`CD-ENG-WO2R3-F17` IS CLOSED BY RULING, NOT BY THE SEAT THAT RAISED IT.** The Product Owner
widened the class at `PO-DECISIONS-0010` ruling 1. **THE ADJACENT SET IS DEAD AS AN EXEMPTION** —
that same executable example is now
`variants/WO-2R3/V43-fielded-judgement-path-type-with-no-establishment.patch`, and it is the row
marked **THE WIDENING** in the negative-controls table above: **exit 0 and ADJACENT at `46adf33`,
exit 1 naming `Verdict` after the widening.**

**TWO RESIDUES REMAIN, AND NEITHER IS CLOSED BY THE WIDENING.**

**RESIDUE (i) — a ZERO-FIELD member satisfies vacuously, and the whole of what is asserted of it is
that it has no fields.** `Empty` is that member today and the only one. It carries no boundary of
any kind; the rule is satisfied there because there is nothing to satisfy it about, which is a
different fact from a guarded type. **EXECUTABLE EXAMPLE:** V43 is this residue **one field down** —
the moment a field arrives on a type with no establishment, the check fails. **CARRIER MEASURED:**
`tests/test_field_establishment.py::test_the_vacuously_satisfying_members_are_exactly_this_set`
pins the vacuous set BY NAME and re-measures each member's emptiness at RUNTIME from
`dataclasses.fields`, so a SECOND zero-field judgement-path type is a test failure rather than a
quiet widening of the vacuous branch, and a field arriving on `Empty` fails there too.

**RESIDUE (ii) — the CROSS-FIELD invariant is not reached, and the widening did not touch it.** A
declared field list says what each field IS and **nothing** about what any two of them must be TO
EACH OTHER. §C.5's invariants 2 and 3, `ConfigSnapshot`'s one-spec-per-dial, `AttemptRecord`'s
`requested_utc <= observation.observed_utc`, `CollectionResult`'s `rows_recorded == attempts_made`
and `Agrees`'s `freshness.as_of_utc == as_of_utc` **REMAIN BODY-BORNE**. **The widened wording must
not be read to imply otherwise:** widening the class from *body-borne* to *body-borne or absent*
widened **WHO MUST DECLARE**, not **WHAT A DECLARATION CAN SAY**. **EXECUTABLE EXAMPLE:**
`variants/WO-2R3/V36-cross-field-invariant-body-rewrite.patch`, as at MECHANISM LIMIT 1. **CARRIER
MEASURED AND IT IS BODY-LEVEL:** `tests/test_engine_config.py` and
`tests/test_engine_model_registry.py`. **As a STRUCTURE that survives an edit to those bodies: NOT
PROVED TO BE CARRIED ANYWHERE.** Standing as `CD-ENG-WO2R3-F18`.

**AND WHAT A READER MUST NOT INFER FROM A GREEN RUN.** The widening changed **no** verdict on the
population it was applied to. This check was GREEN before it and is GREEN after it. What the
widening buys is **prospective**, and it is proved by the contrast, never by the run.

### CHECK LIMIT 2 — RULE A's package list is a VOCABULARY

`engine`, `serving` and `collectors` are spelled in the check. A frozen judgement-path type written
under a package name this file has never heard of is reached only by RULE B or RULE C. This is the
**same** limit `CD-RT-002-DOORS-REQUIRE-THEIR-TYPES` declares as its DECLARED LIMIT 2, reached from
the TYPE side instead of the CALLABLE side. **EXECUTABLE EXAMPLE:**
`variants/WO-2R3/V16-new-package-undecorated-door.patch` adds `src/crash_detector/judging/`; a frozen
type placed there, named by no door and by no reached type's fields, is reached by none of the three
rules. **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.**

### CHECK LIMIT 3 — `establishes` and `admits` are recognised BY NAME in the source

This check reads TEXT; it cannot know that the `establishes` a module imported is
`crash_detector.establishment.establishes`. **Inherited** from the doors check's DECLARED LIMIT 4
rather than newly incurred. **EXECUTABLE EXAMPLE:** the counterfeit pattern of
`variants/WO-2R3/V18-counterfeit-admits.patch`, applied to `establishes`. **CARRIER MEASURED: THE
RUNTIME.** `tests/test_field_establishment.py` imports the product and constructs the real types, and
`::test_the_static_enumeration_and_the_runtime_population_are_the_same_class` diffs the STATIC
population against the RUNTIME population **as SETS**, so a counterfeit decorator leaves the two
readings disagreeing. A static reader alone cannot carry this and does not claim to.

### CHECK LIMIT 4 — it checks that a declaration EXISTS and MATCHES; it does not adjudicate what was declared

`@establishes(payload=ESTABLISHED_HERE("..."))` satisfies every assertion this check makes. Every
`ESTABLISHED_HERE` use is therefore PRINTED with its class, field and line at every run — exactly as
the doors check does for doors — so an exemption that starts absorbing the population is visible in
the output rather than discovered later. **CARRIER MEASURED:**
`tests/test_field_establishment.py::test_the_established_here_field_exemptions_are_exactly_this_set`.

## What a clean run of this check does and does not license

It licenses one sentence: *at this SHA, every member of the enumerated class carries a declaration
that matches its declared field list, and the enumeration is printed in full.*

It does **not** license "constructors are closed". Read the eight declared limits above, and read
`CD-RT-002-DOORS-REQUIRE-THEIR-TYPES`'s DECLARED LIMIT 1, which now hands its residue to this row
and names what it still does not carry. **A clean run of a static check is not proof of a runtime
property** — every escape on this project's record passed a static checker.


---

## DECLARED LIMIT 5 — THE TRAVERSAL'S RESIDUAL REACH

**NEW AT WO-2R3 INCREMENT 6, AND IT REPLACES A LIMIT THAT WAS NEVER DECLARED AT ALL**
(`PO-DECISIONS-0011` ruling 2). Stated identically here, in the check's header, and in
`required-tests.yaml` (`CD-RULE-004`).

**THE UNDECLARED LIMIT THAT WAS HERE UNTIL THIS INCREMENT, SAID PLAINLY BECAUSE NOBODY EVER WROTE IT
DOWN:** this check enumerated classes with `for node in tree.body` — **TOP LEVEL ONLY** — at three
separate sites, and `check_judgement_path_doors.py` did the same for callables. **BOTH GOVERNING
INSTRUMENTS SHARED ONE BLIND SPOT AND NEITHER DECLARED IT.**

`CD-ASR-WO2R3-01` escaped it with **ONE INDENTATION LEVEL** inside an already-governed file in
`engine/`, a RULE A judgement-path package:

```
POPULATION unchanged at 33      ctor EXIT=0      doors EXIT=0
--why ledger mentions it: 0  — NOT EVEN EXAMINED
runtime: Judgement.Verdict(score=object(), breached='maybe') ACCEPTED
```

The ledger printed `OUT engine/config.py:379 Judgement — clause (2): not declared
@dataclass(frozen=True).` — a correct-sounding line about the **container** — and **nothing whatever
about the fielded frozen type inside it** (`CD-PL-F96`). **AN ABSENCE WOULD HAVE BEEN MORE HONEST
THAN THE LINE THAT WAS THERE.**

Enumeration is now `_classes`, which uses `ast.walk` and reaches **any nesting depth**, prints
**qualified names**, and the count of classes examined is **ASSERTED against a second independent
derivation** rather than printed.

### The two derivations, and why they are independent

| | derivation 1 | derivation 2 |
|---|---|---|
| input | the shared `parsed` list | the file's **bytes re-read from disk**, re-parsed |
| traversal | `ast.walk` — breadth-first deque over `iter_child_nodes` | `ast.NodeVisitor` — **visitor dispatch**, depth-first via `iter_fields` |
| qualified names | a parent map built once | its own **descent stack** |

The **sets** are diffed, not the counts compared — this project's own doctrine, learned at
`CD-D-119`: identical counts have hidden a swap here before. A class in the independent reading that
never reached adjudication is `CLASS_NEVER_ADJUDICATED`, **a violation**.

**MEASURED, BOTH ARMS.** Regressing *only* the adjudication loop back to `tree.body` in a scratch
copy, with the nested plant applied, gives `IN THE INDEPENDENT READING AND NEVER ADJUDICATED: 1` and
**EXIT 1** naming `Judgement.Verdict`. **CARRIER MEASURED:**
`tests/test_field_establishment.py::test_the_count_of_classes_examined_is_asserted_against_a_second_derivation`
performs exactly that regression and requires the failure.

### What is now closed — measured, not assumed

`variants/WO-2R3/P-B-how-deep-can-a-type-hide.py` plants the same public frozen fielded undeclared
type at **nine placements** and runs both instruments at each, at a pristine `531c95c` extraction and
at the increment-6 tree. These rows go `ctor exit=0` at `531c95c` and `ctor exit=1`, **named in the
ledger**, now:

* nested **one** class level — the auditor's escape
* nested **two** class levels
* inside a **public** function body
* inside a **private** function body
* **conditionally defined** under `if True:`

**THE CONDITIONAL ONE WAS FOUND BY `CD-ENG-WO2R3-02` AND IS IN NO AUDITOR'S DOCUMENT.** It is not
nested at all — a module-level `if` block is simply not in `tree.body` — and the type it hides is
**fully reachable and ACCEPTED at runtime**.

### A row that turned out NOT to be a limit

**A module that does not parse.** Measured `ctor exit=1`. It is already an `UNPARSEABLE` violation
and always was — a failure, not a silence. **It is not declared as a limit because it is not one.**

### The residual reach limits are exactly two

**(i) A CLASS WITH NO `ClassDef` NODE IS INVISIBLE, AND NO AST TRAVERSAL CAN FIX THAT.** Executable
example — the probe's `built by type(...) AT RUNTIME` placement, appended to `engine/config.py`:

```python
import dataclasses as _dc
HiddenVerdict = _dc.dataclass(frozen=True)(type('HiddenVerdict', (), {
    '__annotations__': {'score': float, 'breached': bool}}))
```

MEASURED **at both SHAs**: `ctor exit=0`, not named, absent from the `--why` ledger, and at runtime
`HiddenVerdict(score=object(), breached='maybe')` **ACCEPTED**. **CARRIER: NOT PROVED TO BE CARRIED
ANYWHERE** — nothing in this tree enumerates types at runtime and compares them against the static
population. **PINNED** (not carried) by
`tests/test_field_establishment.py::test_a_type_with_no_classdef_node_is_a_DECLARED_LIMIT_and_still_escapes`,
which **passes because the escape works**; if it ever fails, the limit is now wrong and all three
`CD-RULE-004` places must be corrected.

**(ii) A MODULE OUTSIDE `src/crash_detector/` IS NEVER PARSED.** Both instruments glob that one
directory. Executable example: the probe's `in a module OUTSIDE the scanned root` placement writes
the identical type to `src/outside_the_root.py`. MEASURED **at both SHAs**: `ctor exit=0`, not named,
absent from the ledger. **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE** — the package boundary is a
convention here, not an assertion.

### What the two derivations do NOT give independence from

**The `ast` module itself, and the set of files handed to both readings.** A defect in CPython's
parser, or a file neither reading is offered — which is limit (ii) — is invisible to both.
**TWO DERIVATIONS OF ONE INPUT ARE TWO DERIVATIONS, NOT TWO INPUTS.**

### The planted violation

`plants/CD-AC-005/CD-RT-002-CONSTRUCTORS-ESTABLISH-FROM-THE-DECLARED-FIELD-LIST.patch` — the twelfth
plant, and the first to vary the **reach** axis. **BITTEN** to `PO-DECISIONS-0011` ruling 4's
standard on the day it landed: clean arm established first (`exit 0`, `PASS — 101 assertions`),
`git apply` **for real**, violated arm `exit 1` reproducing the signature, and the instrument
**SHA-verified byte-identical** at `48679d2bc5b2ac8ceef427023e553d37f64e65716bbbe6c90ac1d80636479382`.
It escaped at `531c95c` **and** at `f495eef` — the post-item-A, post-item-D commit of this same
increment. Both measured, neither assumed.


---

## THE "IN-PACKAGE EXECUTION" SENTENCE — REWRITTEN AT WO-2R3 INCREMENT 6

**By product authority** (`PO-DECISIONS-0011` ruling 3). This is `establishment.py` DECLARED LIMIT
3's closing sentence, which is **the same sentence that appears in `admission.py` — one sentence, two
modules, load-bearing in both.** Superseded wording, quoted and not deleted (`PBG-CONT-003`,
`CD-RULE-004`):

> *"Every route requires the ability to execute code inside this package, which is the universal
> limit every in-process guard on this project lives inside; saying that is strictly weaker than
> 'cannot happen', and it is said rather than implied."*

**IT IS WRONG IN BOTH DIRECTIONS AT ONCE**, and `CD-ENG-WO2R3-02` re-measured both rather than
adopting the auditor's finding.

**TOO NARROW — MEASURED AT ZERO.** `Agrees.__new__(Agrees)` then `__dict__.update(...)` executes **no
package code at all**. `variants/WO-2R3/P-E23-what-the-in-package-execution-sentence-gets-wrong.py`
arm 1 counts every line executed under `src/crash_detector/` with `sys.settrace`:

```
LINES OF PACKAGE CODE EXECUTED BY THAT  : 0
package files touched                   : []
type(smuggled) is exactly Agrees        : True
smuggled.as_of_utc                      : 'not a datetime'
CONTROL — the same values through Agrees(...): REFUSED TypeError
LINES OF PACKAGE CODE EXECUTED BY THE CONTROL: 36
```

**36 LINES THROUGH THE FRONT DOOR AND A REFUSAL; 0 LINES AROUND IT AND AN OBJECT.**

**TOO WIDE** — the CD-BP-003 door **hands** in-package execution to any caller (arm 2:
`reached module globals of : crash_detector.collectors.runner`, `could read runner.ensure_utc from
there : True`), so it is not a bar anyone has to clear.

**THE MEASURED REACH.** These routes are open to anything that can either run in this process at all,
or be passed to the CD-BP-003 door. **"IN-PACKAGE EXECUTION" IS NEITHER NECESSARY NOR SCARCE, AND IT
WAS OFFERED AS BOTH.** **NOT CLOSED, NOT CLAIMED, AND NOT PROVED TO BE CARRIED ANYWHERE** — that much
of the old sentence stands, and it is the only part that did.

**THIS CORRECTION DOES NOT CLOSE THE ROUTE.** That is **F-A4**, a design change nobody has ruled, and
**explicitly not this increment's**. The asymmetry the auditor names is measured — arm 3: **2 of 33**
governed types define `__setstate__` (`FreshnessEvidence`, `StalenessWindow`) — and **raised as
`CD-ENG-WO2R3-02-F09`, not acted on.**
