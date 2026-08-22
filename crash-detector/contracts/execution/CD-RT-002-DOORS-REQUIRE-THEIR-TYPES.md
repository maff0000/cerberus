# Execution contract — CD-RT-002-DOORS-REQUIRE-THEIR-TYPES

**CD-AC-005** (and CD-AC-002, and CD-AC-001 through `ASR3-F05`) · every public entry point on a
judgement path establishes each of its arguments by exact type at the door · obligation
**MANDATORY** · scope **CLASS** · delivered in **WO-2R3 increment 2**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every declared
test to name an execution contract that RESOLVES. It states how this test is run and what its exit
codes mean. **It states no result.** The register carries obligations; status is computed by the
validator from the register, the PID and append-only run records, and there is no field anywhere in
this chain in which an author could write a verdict.

## The proposition

> **Every public entry point on a judgement path establishes each of its arguments by EXACT TYPE at
> the door, and the establishment is DERIVED FROM THE SIGNATURE rather than written into the body.**
> — BP-AMENDMENT-0001 §D.1, in force.

§D.1 names its own acceptance test in the same paragraph, and this is it: *"a static check that
enumerates the judgement paths and fails on any public entry point that is not decorated — not a
list of three fixes."*

## Command

```
python3 -B tools/register/check_judgement_path_doors.py --root .
```

Run with the working directory set to **the root of a subject tree the auditor extracted itself** —
`git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line above is verbatim:
no path fixing, no editing, no wrapper. There is no run-everything harness in this repository and
there may not be one, because an auditor verifying through a harness the project wrote is verifying
the harness (`PBG-ASSURE-001`).

`python3 -B` so no `__pycache__` is written into the subject tree (`PBG-RT-001` — mutation by
EFFECT, not by label).

## Exit codes

| code | meaning |
|---|---|
| 0 | assertions were made and all of them held |
| 1 | VIOLATION — at least one judgement-path door is undecorated, or its declaration and its signature disagree, or it carries an open channel |
| 2 | USAGE — the command line was wrong |
| 3 | PRECONDITION NOT MET — the check could not do its job, with the reason stated. **This includes a run that made ZERO assertions**: `exit 0` must never be able to mean "I looked at nothing" |

## Subject, and how it is DERIVED FROM THE ARTEFACT

The check does not import the product. It parses, so an auditor who trusts nothing in the
implementation can run it. **It prints its subject count**, so a vacuous pass is visible.

A callable is a SUBJECT if EITHER rule reaches it. The two are unioned, not intersected, because
each covers the other's blind spot and neither is trusted alone.

* **RULE 1 — judgement-path packages, DENY-BY-DEFAULT WITHIN THEM.** Every `*.py` under
  `src/crash_detector/engine/` and `src/crash_detector/serving/` is read, and every public
  module-level `def` and every public method of a public class in it is a subject. Nothing inside
  those packages is opted out by name, so a NEW MODULE is a subject with no edit to the check.
* **RULE 2 — return-type reach, anywhere under `src/`.** Any public callable whose return
  annotation names one of the judgement value types is a subject wherever it lives, including under
  a package RULE 1 has never heard of.

**WHY IT IS NOT A LIST (CD-D-098).** §B measured 44 public callables with an unestablished
parameter at `f30e63c`. That measurement is already stale: WO-2R3 increment 1 created
`engine/mapping.py` and with it `compute(spec, payloads)` — the one place in the product a dial
magnitude is computed — which post-dates the inventory entirely. A check enumerating 44 names would
not have looked at it. The Project Lead graded this higher than the seat that raised it did, and it
is the reason the subject is walked rather than listed.

Exemptions are derived from the artefact and **each one's count is printed**: non-public names,
`@property` accessors (a property getter takes only its receiver and no argument can be added to
one), and methods of a class whose bases include `Protocol` (stubs describing a boundary to a
foreign system, closed by a different mechanism at §D.3).

## What it asserts about each subject — two things

1. it carries `@admits(...)`;
2. the parameter names `admits` was told about are EXACTLY the parameter names in its signature,
   minus the method receiver — **planted violation P7 caught statically as well as at runtime.**

## The negative control, both arms, MEASURED

All arms run over `EMPTY_MODEL_REGISTRY` and `EMPTY_SOURCE_REGISTRY` — zero model rows, zero source
rows — because that is the shipped WO-2 state and a plant demonstrated against a configuration
nobody ships demonstrates nothing about what ships.

**P7 — the one the Product Owner directed the fourth Assurance seat to run first.**

```
git archive <sha> | tar -x -C /tmp/p7 && cd /tmp/p7
git apply -p1 variants/WO-2R3/V20-p7-added-parameter.patch
python3 -B tools/register/check_judgement_path_doors.py --root .
```
→ exit **1**, `PARAMETER_NOT_DECLARED_TO_ADMITS`, `resolve_panel has parameter(s)
['tolerate_stale'] in its signature that @admits() was not told about`. `PYTHONPATH=src python3 -B
-m pytest tests -q` on the same tree goes from **1518 passed** to **59 failed, 1460 passed** (re-measured at WO-2R3 increment 3), and an ORDINARY
call that does not pass the new argument at all raises `UndeclaredParameter`.

The VIOLATED arm — `variants/WO-2R3/V23-p7-violated.patch`, the same added parameter with the
`@admits` decorator removed — ADMITS both calls and renders `WITNESS AGREES`.

**P5** — `variants/WO-2R3/V21-p5-violated.patch` removes the door from `evaluate`; `ASR3-F05`'s duck
`ConfigSnapshot` is then ADMITTED and its own `covers()` decides freshness for a 315 360 000-second-old
observation against a 600-second window. BASELINE: `NotAdmitted: evaluate: config_snapshot=Duck is
not admitted; this door requires exactly ConfigSnapshot`.

**P6** — `variants/WO-2R3/V22-p6-violated.patch` removes the door from `resolve_panel`; `ASR3-F04`'s
row then resolves to `Agrees` and RENDERS `WITNESS AGREES`. BASELINE: `NotAdmitted: resolve_panel:
row=DuckRow is not admitted; this door requires exactly PanelRow or None`.

## The rename test (CD-PL-F74)

Every refusal this check and this mechanism produce is a property of `type(value)` identity, of
`inspect.signature`, or of a set difference between two name sets. **They survive any rename**, and
that is the point of this architecture. TWO name dependences exist and both are disclosed:

* the method receiver is skipped by the name `self`/`cls`, and only inside a class body. Renaming it
  does not open a hole — it FAULTS the door and refuses every call. That is a vocabulary result in
  the SAFE direction and it is measured
  (`tests/test_admission.py::test_renaming_the_receiver_faults_the_door`);
* this check recognises `admits` **by its name in the source**. See DECLARED LIMIT 4.

## DECLARED LIMIT (CD-RULE-004)

Stated identically here, in the header of `tools/register/check_judgement_path_doors.py`, and in the
register entry, each with a patch an auditor can apply to their own extraction. Under CD-RULE-006
each hand-off names a layer **MEASURED** to carry it, or says **NOT PROVED TO BE CARRIED ANYWHERE**.

**THIS ROW HAS SIX DECLARED LIMITS.** 1–4 are the STATIC CHECK'S and are below. **5 and 6 are the
MECHANISM'S** — they live in the header of `src/crash_detector/admission.py` and, since WO-2R3
increment 4, in full in the register entry as well (CD-PL-F81, ruled CD-D-111: until then this
contract POINTED AT them and the register did not carry them at all — `grep -c "__closure__"
required-tests.yaml` returned **0**, measured). They are reproduced below as **5** and **6** so that
this contract, the check header and the register say the same six things. Numbering runs 1..6 across
the two headers on purpose: they are one row's limits, not two lists.

**1 — CONSTRUCTORS ARE STILL NOT SUBJECTS *OF THIS CHECK*, AND AS OF WO-2R3 INCREMENT 5 THAT IS NO
LONGER AN UNCARRIED GAP. THE WORDING BELOW IS NARROWED TO ITS MEASURED REACH; THE SUPERSEDED WORDING
IS QUOTED RATHER THAN DELETED.**

It read: *"CONSTRUCTORS ARE NOT SUBJECTS, AND THAT IS A REAL GAP IN §D AS SCOPED. … §D.2's table
lists no constructor and this check does not invent that scope. … as a structure that survives an
edit to those bodies, NOT PROVED TO BE CARRIED ANYWHERE."* That was true when it was written and the
Product Owner ruled on it at PO-DECISIONS-0007 ruling 1 — *"`__post_init__` IS A BODY"* — creating
increment 5 to close it, and re-based it at PO-DECISIONS-0008 ruling 2 from four named types to THE
CLASS.

**WHAT IS STILL TRUE.** This check reads CALLABLES and a constructor is not one of its subjects.
`variants/WO-2R3/V17-constructor-body-escape.patch` deletes the `type(spec) is not DialSpec` loop
from `ConfigSnapshot.__post_init__` and **this command still exits 0 with 54 assertions**, measured
at increment 5 on a pristine extraction. Nothing about that has changed and no reader should infer
otherwise from a clean run of THIS check.

**WHAT IS NO LONGER TRUE IS THE HAND-OFF.** The residue now has a carrier and the carrier is
MEASURED (CD-RULE-006):

* the STRUCTURE is `crash_detector.establishment.establishes` — establishment derived from the
  DECLARED FIELD LIST, applied at the class boundary, where a body rewrite cannot reach it;
* the ENUMERATION is `python3 -B tools/register/check_constructor_field_establishment.py --root .`,
  which enumerates that class and asserts every **fielded** member carries the declaration. **RUN IT
  AND READ ITS OWN `POPULATION` LINE — NO COUNT AND NO DEFINITION OF THE SIBLING'S CLASS IS
  TRANSCRIBED HERE, AND UNTIL `PO-DECISIONS-0010` RULING 1 BOTH WERE.** This line read *"which
  measures the class at **32 members** and asserts every one of them carries the declaration"*. That
  was a copy of a SIBLING limit's definition and count living where no rule pointed at it
  (`CD-PL-F91`) — `CD-RULE-004`'s three places are each limit's OWN — and the ruling widened that
  class to **BODY-BORNE OR ABSENT** and moved the count, so the copy went stale exactly as an
  unpointed-at copy does. A count read from the sibling's run is a MEASUREMENT; a count copied here
  is a TRANSCRIPTION (`CD-RULE-009`);
* the MEASUREMENT is V17 itself, run: with V17 applied and the mechanism present, constructing a
  duck `DialSpec` into `ConfigSnapshot` is **REFUSED** —
  `crash_detector.establishment.FieldNotEstablished: ConfigSnapshot.dial_specs[0]=DuckDialSpec is
  not admitted; every element must be exactly DialSpec` — and with the mechanism removed
  (`V40-v17-violated-arm-establishes-removed.patch`) the same construction **ESCAPES**, storing
  `['DuckDialSpec', 'DuckDialSpec']` and answering `spec_for('equity_crash') -> DuckDialSpec`.
  Commands and both arms are in `variants/WO-2R3/MANIFEST.md`.

**AND WHAT IS STILL NOT CARRIED, so this correction does not overstate itself.** The new mechanism
establishes a field's TYPE and never a RELATION BETWEEN TWO FIELDS: §C.5's invariants 2 and 3,
`ConfigSnapshot`'s one-spec-per-dial, and every registry uniqueness check REMAIN BODY-BORNE, with
`variants/WO-2R3/V36-cross-field-invariant-body-rewrite.patch` as the executable example — it
deletes the one-spec-per-dial check and a snapshot with two equity specs and no monetary spec is
**ACCEPTED**. For that residue, as a structure surviving a body edit: **NOT PROVED TO BE CARRIED
ANYWHERE.** See `CD-RT-002-CONSTRUCTORS-ESTABLISH-FROM-THE-DECLARED-FIELD-LIST`'s own DECLARED
LIMIT 1, which is where it now lives.

**2 — RULE 1's PACKAGE LIST IS A VOCABULARY.** `engine` and `serving` are spelled in the check. A
judgement-path door written under a package name the check has never heard of is reached only by
RULE 2, and only if it annotates its return type. MEASURED:
`variants/WO-2R3/V16-new-package-undecorated-door.patch` adds
`src/crash_detector/judging/decide.py` with a public, undecorated, unannotated `decide(reading)` and
this command still exits 0 with **54 assertions**. **NOT PROVED TO BE CARRIED ANYWHERE** — no other
layer enumerates judgement-path packages. It is stated here so the fourth Assurance seat can hit it
without having to find it first.

**3 — `collectors/` IS NOW A JUDGEMENT-PATH PACKAGE, AND WHAT REMAINS OPEN THERE IS CD-BP-003.**

*What this slot said at WO-2R3 increment 2, recorded rather than deleted so a reader of the diff
sees the transition rather than inferring it:* "`collectors/` is not yet a judgement-path package
here, by scope and not by oversight." **THAT LIMIT IS DISCHARGED.** BP-AMENDMENT-0001 §D.3 was
implemented at WO-2R3 increment 3 and `collectors` is in `JUDGEMENT_PATH_PACKAGES`, deny-by-default
within: every public callable in the package is a subject, and a new module there is a subject the
day it is written.

**MEASURED — AND RE-TAKEN AT WO-2R3 INCREMENT 4 BY RUNNING THE INSTRUMENT, NOT BY TRANSCRIBING IT**
(CD-PL-F82, ruled CD-D-120). This paragraph read *"the subject count went from **19 to 24**"*, which
compared **a TOTAL against a SUBSET**. The check reaches subjects by two unioned rules; at BOTH SHAs
rule 2 reaches 3 doors rule 1 does not, so **24 was the rule-1 part of a total of 27** and 19 was a
total. Both figures below are re-derived, each on its own pristine extraction:

```
git archive 995ec3e | tar -x -C /tmp/cd-995        # increment-2 head, the base
cd /tmp/cd-995   && python3 -B tools/register/check_judgement_path_doors.py --root .
    SUBJECTS ENUMERATED: 19. DECORATED: 19.   |  by rule 2 only: 3  |  PASS — 38 assertions

git archive 04cdd34 | tar -x -C /tmp/cd-clean      # increment-3 head, this lane
cd /tmp/cd-clean && python3 -B tools/register/check_judgement_path_doors.py --root .
    SUBJECTS ENUMERATED: 27. DECORATED: 27.   |  by rule 2 only: 3  |  PASS — 54 assertions
```

**LIKE-FOR-LIKE: TOTAL 19 → 27. RULE-1 SUBSET 16 → 24. ASSERTIONS 38 → 54.** The subset figures are
the printed total minus the printed rule-2-only count — arithmetic on the check's own output, not a
second measurement. **Never pair 19 with 24.**

**What it does not mean.** The coverage is **WIDER** than was claimed, not narrower: **27 of 27**
subjects are decorated, the check exits 0, and nothing was unguarded because of the error. Eight
subjects were added, not five. **Why nothing caught it:**
`tests/test_judgement_path_doors.py` asserts `subjects >= 24` — **A FLOOR**, which passes at 27 and
would pass at 270. **Raising that floor to an equality is NOT ruled, NOT authorised and NOT done**
(CD-D-120): it would be a code change answering a documentary finding. It is named here and left
alone.

`tests/test_judgement_path_doors.py::test_the_collector_doors_are_really_subjects_and_not_merely_counted`
removes `@admits` from `collect` in a scratch copy and asserts this command FAILS on it — so the
package being in RULE 1 is a measured property of the check and not a string in a file.

**WHAT IS OPEN IS NARROWER AND IT IS THE SOFTEST SURFACE IN THE PRODUCT.** BLUEPRINT §17's
**CD-BP-003**: `collect`'s `adapter`, `sink`, `ledger` and `validator` are `Protocol` boundaries to
genuinely foreign things — a market data source, the store — so exact-typing them against a concrete
class is not available and §D.3 part 2 says it would be wrong. They are declared `ESTABLISHED_HERE`,
and this command PRINTS all four with file, line and parameter at every run, derived from the
artefact. **IT IS A DOOR THAT ADMITS, NOT AN ABSENCE OF A DOOR.** The Product Owner named it the
fourth Assurance seat's first target.

What IS closed at that door and is **not** a limit — **REWRITTEN TO ITS MEASURED REACH AT WO-2R3
INCREMENT 6 BY PRODUCT AUTHORITY (`PO-DECISIONS-0011` ruling 3). ONE OF THE FOUR CLAIMS IS WITHDRAWN
RATHER THAN RESTATED.** The wording this replaces is quoted in full and is not deleted
(`PBG-CONT-003` — corrections supersede, never edit away):

> *"`policy` exact `RetryPolicy` (`isinstance` admitted a subclass shadowing `max_attempts` with a
> property until this increment), `started_utc` exact `datetime` and then rebuilt by `ensure_utc`,
> `delay` exact `DelayKind` from a closed enum, and every value the four Protocols RETURN
> exact-typed at its point of return."*

**IT IS WRONG IN A STATED DIRECTION.** The fourth claim is *literally true* and was *offered as
closure*, and it **closes the TYPE and not the VALUE**. `CD-ASR-WO2R3-01` reproduced ESCAPE 1
against it and moved the WO-2R3 gate to RED: `type(OK.payload) is exactly dict` while the value held
`inf`, a key outside the schema, and a live module object. *"A claim filed under 'not a limit' that
turns out to be a limit is worse than an undeclared gap, because the declaration is what a reader
stops reading at."*

**RE-MEASURED CLAIM BY CLAIM BY `CD-ENG-WO2R3-02`** — the whole list, not only the quoted sentence.
Command, run at a pristine `git archive 531c95c` extraction and at the increment-6 tree:
`python3 -B variants/WO-2R3/P-E1-what-is-closed-at-that-door.py`.

| claim | measured | observed line |
|---|---|---|
| `policy` exact `RetryPolicy` | **HOLDS, AND HARDER THAN CLAIMED** | with `runner.RetryPolicy` rebound to an unrelated class, a genuine one is still `ADMITTED final_outcome=OK` and `_NotAPolicy` is still `NotAdmitted` — `@admits` compiles at DECORATION time |
| `started_utc` exact `datetime` | **TYPE ONLY — a LIMIT, not a closure** | subclass `NotAdmitted`; naive `NaiveTimestampRejected`; `datetime(2016,1,1)` **`ADMITTED`** |
| `delay` exact `DelayKind` | **HOLDS** | a look-alike with the same `.value`, and the bare `.value`, both `NotAdmitted` |
| every returned value exact-typed | **WITHDRAWN** | see DECLARED LIMIT 5 below; may no longer be cited toward CD-AC-002 |

**AND THE DOOR THIS LIST CARRIES BY IMPLICATION.** `type(response) is not FetchedResponse` in
`runner.py` resolves its name **at CALL time** from module globals, so it is *not* of the same
strength as `policy`. Measured, arm (iv), from an adapter that **imports nothing from
`crash_detector`** and reaches the runner's globals through the frame it is called in:

```
reached module globals of : crash_detector.collectors.runner
runner.FetchedResponse rebound: True
at the door               : ADMITTED final_outcome=OK {'reading': 0.25}
```

**AN EXACT-TYPE DOOR IS ONLY AS STRONG AS WHEN IT RESOLVES ITS TYPE, AND THIS ONE MODULE CONTAINS
ONE OF EACH.** For the global-rebind route: **NOT PROVED TO BE CARRIED ANYWHERE.** Closing it is not
among increment 6's items and is not claimed.

**DECLARED LIMIT 5 — THE PAYLOAD SNAPSHOT** (`CD-RULE-004`, stated identically in `collect`'s header
in `src/crash_detector/collectors/runner.py`, in `required-tests.yaml`, and here). Since increment 6
the object stored on `OK.payload` is a rebuild taken **after** the validation verdict and **before**
`adapter.is_empty` is called, and `is_empty` is handed a **second, independent** rebuild — so the
object foreign code can mutate is neither the judged one nor the stored one. `_payload_snapshot`
rebuilds `dict`, `list` and `tuple` **by exact type** to `PAYLOAD_SNAPSHOT_MAX_DEPTH` (32) levels.
Exact type on purpose: walking a foreign mapping means calling *its* `keys` and `__getitem__`, which
is the adapter's code running again inside the rebuild that exists to stop the adapter's code
mattering. It is deliberately **not** `copy.deepcopy`, which dispatches to
`__deepcopy__`/`__reduce_ex__` and would hand the adapter one more execution point.

**WHAT IT DOES NOT REACH — each an arm of `variants/WO-2R3/P-A-escape1-stored-is-not-validated.py`,
run at BOTH SHAs:**

1. **A container that is not exactly `dict`/`list`/`tuple` is carried BY REFERENCE.** Arm
   `nested-dict-subclass`: `class Sub(dict)` nested in the payload, `is_empty` sets
   `payload["nested"]["reading"] = inf`; stored reads `{"nested": {"reading": Infinity}, "reading":
   0.25}` and **fails the schema it was judged by** (`JSONSCHEMA_MAXIMUM at /nested/reading`) — at
   `531c95c` **and** at the increment-6 tree.
2. **Anything below the declared depth is carried BY REFERENCE.** Arm `beyond-depth-cap`: two
   hundred levels, innermost `reading` rewritten to `inf` after validation — open at both SHAs.
3. **The VALIDATOR is not covered at all.** It is the other declared-foreign protocol at this door
   and is handed the adapter's live object before any snapshot exists. The probe prints
   `validator's argument IS the adapter's live object : True` at every arm after the fix, **on
   purpose**. That route travels to the fifth Assurance seat with the sink/ledger/validator table.
4. **If the `FetchedResponse` door has itself been defeated, `payload` is a property.** It is now
   read **once** and bound to a local where it was read **four** times — `times the payload PROPERTY
   was read by package code: 4` at `531c95c`, `1` now. **A NARROWING, NOT A CLOSURE.**

**CARRIER MEASURED:** `tests/test_collector_runner.py::test_a_hostile_is_empty_cannot_change_the_stored_payload`,
`::test_the_object_is_empty_is_handed_is_not_the_adapters_own_object`,
`::test_a_hostile_is_empty_cannot_change_a_nested_plain_dict_either` and
`::test_the_snapshot_depth_is_a_declared_number_and_the_residue_below_it_is_real` — measured **RED**
(`4 failed, 59 passed`) against a tree with the snapshot reverted, green with it. **FOR RESIDUES 1–4:
NOT PROVED TO BE CARRIED ANYWHERE.** Residues 1 and 3 are **pinned** by
`::test_the_snapshot_does_not_reach_a_container_that_is_not_exactly_a_dict` and
`::test_the_validator_is_still_handed_the_adapters_live_object`, which pass in **both** arms by
design: they assert the limit is still exactly that wide. They are pins, not carriers, and they say
so in their own docstrings.

**EXECUTABLE EXAMPLE, AND IT IS A POSITIVE ONE — AN OBJECT THAT IS ADMITTED.**
`variants/WO-2R3/V26-conforming-hostile-adapter.patch` adds a probe carrying an adapter that
supplies all five protocol members, returns an exact `FetchedResponse` whose payload conforms to the
schema it declared itself, and answers `False` to `is_empty`. MEASURED at this seat's own work:
`missing protocol members: ()`, `ADMITTED: OK`, `payload recorded: {'reading': 0.0}`,
`source_id recorded: src.does.not.exist`, `rows written: 1`, `reading admitted: True`. Nothing in
this tree refuses it.

**CARRIER, PARTIAL AND MEASURED:** it cannot compute a dial value — nothing under `collectors/` may
import `crash_detector.dials` or `crash_detector.engine`, asserted over the whole package by
`tests/test_collector_boundaries.py::test_no_collector_module_imports_the_dial_types_or_the_engine`
— and its observation still faces the staleness window and the required-input rules in
`engine.evaluate`, over a SHIPPED EMPTY source registry it contributes to no dial at all.
**CARRIER FOR WHETHER A CONFORMING ADAPTER IS TELLING THE TRUTH: NOT PROVED TO BE CARRIED
ANYWHERE.** Source trust is CD-D-005 and BLUEPRINT §5 and it is OWED, not held. No guard was built
over it.

**THE PROTOCOL CONFORMANCE CHECK ITSELF FAILS THE RENAME TEST** (CD-PL-F74): `missing_adapter_members`
asks `hasattr` for five SPELLED names, so it measures a VOCABULARY and not a class. That is
unavoidable at a boundary to a foreign system — structural conformance IS nominal — and it is
recorded rather than presented as a closure. It is the ONLY refusal this increment relies on that
fails the rename test; every other one is a type identity comparison or an identity comparison
against `None`.

**CARRIER MEASURED FOR THE EXTENT OF THE LIMIT ITSELF:**
`tests/test_admission.py::test_cd_bp_003_is_exactly_four_parameters_and_every_one_names_its_residue`
pins CD-BP-003 at FOUR parameters of ONE door and requires each to name the risk in the artefact and
to write CD-RULE-006's words. A fifth is a test failure, not a quiet widening.

**4 — A DECORATOR NAMED `admits` IS RECOGNISED BY ITS NAME IN THE SOURCE.** This check reads TEXT;
it cannot know that the `admits` a module imported is `crash_detector.admission.admits`. MEASURED:
`variants/WO-2R3/V18-counterfeit-admits.patch` defines a do-nothing `admits` in
`crash_detector/own_terms.py` and imports it into `serving/witness_resolver.py` — this command exits
0 with **54 assertions** and PASS, and `ASR3-F04`'s duck row then renders `WITNESS AGREES`. **CARRIER
MEASURED: THE RUNTIME.** The same patched tree runs **3 failed, 1516 passed** under `PYTHONPATH=src python3 -B -m
pytest tests -q` (re-measured at WO-2R3 increment 3), because the plants call the real doors and observe the real refusals. A static
reader alone cannot carry this and does not claim to.

**5 — §D.1's OWN RULE IS NOT HELD AT THE THREE §B.3 DOORS.** *(The MECHANISM's limit, from
`src/crash_detector/admission.py`. Reproduced here in full at WO-2R3 increment 4 rather than pointed
at — CD-PL-F81.)* `combine_within_one_dial(using)`, `observed_for_dial(dial_id, quantity,
inputs_used)` and `derived_within_one_dial(quantities, reduction)` are BP-AMENDMENT-0001 §B.3's
*"doors already closed, and they are the template"*. They establish their arguments by exact type
**IN THEIR BODIES**, and each refuses with its OWN NAMED ERROR — `UndeclaredReduction`,
`ScoreOutOfRange`, `CrossDialCombination`, `QuantityProvenanceMissing` — which is the refusal
identity nine auditor-derived tests assert and which CD-PL-F74 requires be recorded. Exact-typing
them at the door would PREEMPT those named refusals with a generic `NotAdmitted` and replace this
project's strongest closures with a coarser one, so they are decorated for the **P7 property only**
and their six `ESTABLISHED_HERE` declarations say so.

**THE CONSEQUENCE, STATED AND NOT SOFTENED:** a rewrite of those three bodies removes their type
establishment, which is CD-ASR-F03's shape at the doors §B.3 calls the template. §D.2's table does
not list them and no seat invented that scope. **MEASURED:**
`variants/WO-2R3/V19-b3-door-body-rewrite.patch` deletes the `type(offered) is not DeclaredQuantity`
refusal from `derived_within_one_dial`'s body and a bare `float` is admitted with the decorator
untouched; at `04cdd34` this command still exits 0 with **54 assertions** and
`PYTHONPATH=src python3 -B -m pytest tests -q` reports **1 failed, 1518 passed**.
**CARRIER, AND IT IS A BODY-LEVEL CARRIER:**
`tests/test_dial_provenance.py::test_the_derivation_door_refuses_a_value_whose_provenance_it_cannot_establish`
and its siblings measure those bodies refusing TODAY. As a structure that survives an edit to those
bodies: **NOT PROVED TO BE CARRIED ANYWHERE.**

**6 — A DOOR IS BUILT OUT OF THINGS THE INTERPRETER LEAVES REACHABLE.** *(The MECHANISM's limit.)*
This is a **REACH, not a route**, and **THE ROUTES NAMED HERE ARE KNOWN ROUTES AND ARE NOT AN
EXHAUSTIVE SET** (CD-D-121). Three have now been found by three different parties on three different
drivers, and each time the declaration named one. **Assume there is a fourth and look for it rather
than checking this list.**

**6a1 — the `__closure__` reach to the WRAPPED FUNCTION.** `door.__closure__[i].cell_contents`
reaches the undecorated function and calls it with the door bypassed. True of every decorator ever
written in Python, including this codebase's own `_absence_is_never_a_number`, which has passed three
gates; CPython offers no way to prevent it, so it is a property of the language and not of this
design. **EXECUTABLE EXAMPLE:** `variants/WO-2R3/V24-wrapped-attribute-bypass.patch` arm 3 —
ASR3-F04's duck row returned `Agrees` and rendered `WITNESS AGREES`. The door itself is untouched, so
a second caller still meets a working door.

**6a2 — the SAME reach rewrites the door's LIVE DECLARATION, and then THE DOOR ITSELF STOPS REFUSING
AT ITS OWN FRONT ENTRANCE.** *(CD-PL-F80's second route: the limit's wording covered it, its named
example did not.)* **EXECUTABLE EXAMPLE, MEASURED BY THE IMPLEMENTING SEAT AND NOT RELAYED:**
`variants/WO-2R3/V33-closure-declaration-rewrite.patch`, run with
`PYTHONPATH=src python3 -B probe_v33_closure_declaration_rewrite.py`.

```
CONTROL — the front door before anything is touched:
    REFUSED: NotAdmitted: resolve_panel: row=DuckRow is not admitted; this door requires
             exactly PanelRow or None. Exact type and never isinstance
ROUTE   — rewrite resolve_panel.__closure__[0] (the live `compiled` dict, keys
          ['now_utc', 'row', 'staleness_window_seconds']) to ESTABLISHED_HERE(...)
ARM     — the SAME front door call, nothing else changed:
    ESCAPED -> Agrees; RENDERS: WITNESS AGREES
```

This is **WIDER than 6a1**: the mutation is to state the door SHARES, so every caller in the process
is unguarded afterwards, including code that never went near a closure.

**AND THE INTROSPECTION SURFACE DOES NOT SHOW IT** — `CD-ENG-WO2R3-F13`, raised by the seat against
its own increment-2 work. `__admits__` is `dict(compiled)`, **A COPY TAKEN AT DECORATION**, so after
6a2: `is_admitting_door(resolve_panel)` is `True`, `declared_admissions(resolve_panel)` still reports
`['now_utc', 'row', 'staleness_window_seconds']`, and `__admission_faults__` is still `()`. A
reviewer asking the door what it requires is told the truth about what it WAS told and nothing about
what it now DOES. **NOT REPAIRED:** making that attribute the live object would hand a mutator a
documented, supported handle instead of an interpreter-internal one, which is a worse trade, and
choosing between them is a design decision and not a reconciliation item.

*MEASURED side-note, so a seat does not mistake a break for a closure:* `.clear()` on that dict does
**NOT** open the door — the body reads `compiled[name]` for every parameter the signature names, so
an emptied dict raises `KeyError` and the door merely **BREAKS**. It has to be **REWRITTEN**, not
emptied.

**6b — `__wrapped__`: THIS HALF IS CLOSED**, and the closure is measured
(`tests/test_admission.py::test_a_door_publishes_no_way_round_itself`). `functools.wraps` sets it,
`inspect.unwrap` follows it and editors offer it, so it was a bypass writable in ordinary-looking
code with no cast and no import; it is deleted. What it used to do is
`variants/WO-2R3/V24-wrapped-attribute-bypass.patch` arm 2.

**6c — REBINDING THE ESTABLISHING FUNCTION IN ITS OWN MODULE NAMESPACE.** *(CD-PL-F83, a Project Lead
route that is in no corpus, **replicated by the implementing seat** rather than relayed.)*
**EXECUTABLE EXAMPLE:** `variants/WO-2R3/V34-establishing-function-rebound.patch`, run with
`PYTHONPATH=src python3 -B probe_v34_establishing_function_rebound.py`.

```
CONTROL — the unmodified module:
    started_utc handed in : 2026-08-22T12:00:00+00:00   (exact datetime, both arms)
    AttemptRecord.requested_utc recorded: ['2026-08-22T12:00:00.000010+00:00', ...]
ROUTE   — crash_detector.collectors.runner.ensure_utc = lambda value: <1999-01-01T00:00:00Z>
    AttemptRecord.requested_utc recorded: ['1999-01-01T00:00:00.000007+00:00', ...]
```

**THE DOOR IS SATISFIED IN BOTH ARMS** — `started_utc` is an exact `datetime` either way — because
`admits` establishes a value's **TYPE** and never the **IDENTITY OF THE FUNCTION THAT ESTABLISHED
IT**. It attacks the establishment layer, not the door.

**WHAT 6c DOES NOT DEFEAT — REWRITTEN AT WO-2R3 INCREMENT 6 BY PRODUCT AUTHORITY**
(`PO-DECISIONS-0011` ruling 3). **THE SUPERSEDED WORDING, QUOTED AND NOT DELETED**
(`PBG-CONT-003`, `CD-RULE-004`):

> *"It is **NOT a caller route**: it needs the ability to execute code inside the package."*

**IT IS A CALLER ROUTE, AND THE REASON IS THAT PASSING AN OBJECT TO THIS DOOR *IS* THE ABILITY TO
EXECUTE CODE INSIDE THE PACKAGE.** `collect` calls methods on caller-supplied objects, interleaved
with its own establishment sequence, and every one of those calls runs caller code in a frame whose
`f_back` chain reaches this package's module globals. MEASURED by `CD-ENG-WO2R3-02` with
`variants/WO-2R3/P-E23-what-the-in-package-execution-sentence-gets-wrong.py` arm 2, from a caller
importing nothing from `crash_detector` for its leverage:

```
members of the ADAPTER `collect` touched : 13
... of which are CALLS into caller code  : ['fetch', 'is_empty']
members of the SINK touched              : ['record']
members of the LEDGER touched            : ['admit_if_absent']
reached module globals of                : crash_detector.collectors.runner
could read runner.ensure_utc from there  : True
```

and independently by `variants/WO-2R3/P-E1-what-is-closed-at-that-door.py` arm (iv), which does not
merely **read** that global but **rebinds** it and walks a property-backed look-alike through the
`type(response) is not FetchedResponse` door: `runner.FetchedResponse rebound: True`,
`at the door: ADMITTED final_outcome=OK`.

**WHAT SURVIVES, AND IT IS NARROWER THAN IT SOUNDED.** BP-AMENDMENT-0001 §D.3 part 1's claim is about
what a caller can supply **AS A PARAMETER**, and that claim stands: `clock` and `sleep` are not
parameters and the interpreter refuses to pass them. **THAT IS A STATEMENT ABOUT THE SIGNATURE, NOT
ABOUT WHAT A CALLER CAN REACH ONCE IT IS INSIDE.** The two ran together in one sentence and the
second was read off the first.

**CARRIER FOR THE WHOLE OF LIMIT 6 — ALSO REWRITTEN, AND IT IS THE SAME SENTENCE THAT APPEARS IN
`establishment.py` DECLARED LIMIT 3 AND IN `admission.py`. ONE SENTENCE, TWO MODULES, LOAD-BEARING IN
BOTH.** Superseded wording, quoted and not deleted:

> *"Every route above needs the ability to execute code inside this package, which is the universal
> limit every in-process guard on this project lives inside."*

**IT IS WRONG IN BOTH DIRECTIONS AT ONCE, AND BOTH WERE RE-MEASURED RATHER THAN ADOPTED.**

**TOO NARROW — MEASURED AT ZERO.** `Agrees.__new__(Agrees)` then `__dict__.update(...)` executes **no
package code at all**. Arm 1 counts every line executed under `src/crash_detector/` with
`sys.settrace`:

```
LINES OF PACKAGE CODE EXECUTED BY THAT  : 0
package files touched                   : []
type(smuggled) is exactly Agrees        : True
smuggled.as_of_utc                      : 'not a datetime'
CONTROL — the same values through Agrees(...): REFUSED TypeError
LINES OF PACKAGE CODE EXECUTED BY THE CONTROL: 36
```

**36 LINES THROUGH THE FRONT DOOR AND A REFUSAL; 0 LINES AROUND IT AND AN OBJECT.**

**TOO WIDE** — the CD-BP-003 door **hands** in-package execution to any caller, as measured above, so
it is not a bar anyone has to clear.

**THE MEASURED REACH, WHICH IS WHAT REPLACES THE SENTENCE.** These routes are open to anything that
can either run in this process at all, or be passed to the CD-BP-003 door. **"IN-PACKAGE EXECUTION"
IS NEITHER NECESSARY NOR SCARCE, AND IT WAS OFFERED AS BOTH.** **NOT CLOSED, NOT CLAIMED, AND NOT
PROVED TO BE CARRIED ANYWHERE** — that much of the old sentence stands, and it is the only part that
did.

**WHAT THIS CORRECTION IS NOT.** It does not close the `__new__`/`__dict__` route. Doing so is
**F-A4**, it is a design change nobody has ruled, and it is **explicitly not this increment's**. The
asymmetry the auditor names is measured — arm 3: **2 of 33** governed types define `__setstate__`
(`FreshnessEvidence`, `StalenessWindow`) — and **raised as `CD-ENG-WO2R3-02-F09`, not acted on**. A
seat that corrects a sentence about a route and then closes the route has decided a design question
on its own authority.

## What this check is NOT

**IT IS NOT PROOF OF A RUNTIME PROPERTY.** A static checker exiting non-zero is not proof that
anything is unconstructible, because every escape on this project's record passed a static checker.
The runtime claims are made by the plants (`tests/test_judgement_path_doors.py`) and by
`tests/test_admission.py`, and the mechanism's own residues — including a bypass the implementing
seat found in its own doors and closed, and the `__closure__` reach it could not close — are DECLARED
LIMIT 6, in `src/crash_detector/admission.py`, **in the register entry, and reproduced in full above
since WO-2R3 increment 4**. It now names **three** known routes and says in terms that they are not
an exhaustive set.

**IT IS NOT A LIST OF THREE FIXES.** The instance game — *"add `type(row) is not PanelRow` to
`resolve_panel`"* — is what the first gate caught, what the auditor named, and what §D.1 repeats. The
unit of work is the class of doors: one mechanism, deriving what it requires from each door's own
signature, and one check enumerating them from the tree.


---

## DECLARED LIMIT 7 — THE TRAVERSAL'S RESIDUAL REACH

**NEW AT WO-2R3 INCREMENT 6, AND IT REPLACES A LIMIT THAT WAS NEVER DECLARED AT ALL**
(`PO-DECISIONS-0011` ruling 2). Numbered 7 because 1–4 are this check's and 5–6 are the mechanism's,
and this row's limits run as **one** sequence across the two headers.

**THE UNDECLARED LIMIT UNTIL THIS INCREMENT.** `_callables` read `tree.body` — top-level `def`s plus
the **direct** members of top-level **public** classes — and its sibling
`check_constructor_field_establishment.py` did the same for classes. **BOTH GOVERNING INSTRUMENTS
SHARED THIS BLIND SPOT AND NEITHER DECLARED IT.**

`CD-ASR-WO2R3-01`'s four arms, same undecorated public door in `collectors/runner.py`:

| where defined | doors check, `531c95c` | doors check, now |
|---|---|---|
| module-level `def` | exit 1 | exit 1 |
| method of a top-level class | exit 1 | exit 1 |
| method nested one level (`Outer.Inner`) | **exit 0** | **exit 1** |
| function-local `def` bound in a module dict | **exit 0** — and live, `POLICY["decide"]` accepted unestablished arguments | **exit 1** |

`_callables` now descends to **any depth**. **Both zeros are ones.**

**NO NEW EXEMPTION WAS INTRODUCED.** The three this check declares — non-public name, `@property`,
`Protocol` stub — are untouched, are still the only ones, and each is still counted in the output.
The old code skipped members of a **non-public** top-level class; that is preserved and now applied
to the **whole chain**, which is the same judgement — *"nothing outside can name this"* — asked of
every level rather than only the first.

### What is now closed — measured

`variants/WO-2R3/P-B-how-deep-can-a-type-hide.py` plants one public undecorated callable at nine
placements. Now **named** by this check: nested one class level · nested two class levels · inside a
public function body · inside a private function body · conditionally defined under `if True:`.

### The residual reach limits are exactly two

They are the **same two** the sibling instrument declares as its DECLARED LIMIT 5, because they are
properties of reading source rather than of either check.

**(i) A CALLABLE WITH NO `FunctionDef` NODE IS INVISIBLE.** A `lambda` bound to a name, or a function
built by `exec`/`type`, leaves nothing to walk. Executable example: the probe's `built by type(...)
AT RUNTIME` placement writes `hidden_decide = lambda reading: reading` into `engine/config.py`;
**measured at both SHAs, this check does not name it. CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.**

**(ii) A MODULE OUTSIDE `src/crash_detector/` IS NEVER PARSED.** Measured: the probe's `in a module
OUTSIDE the scanned root` placement is not named at either SHA. **CARRIER: NOT PROVED TO BE CARRIED
ANYWHERE.**

**A LIMIT THAT TURNED OUT NOT TO BE ONE:** a module that does not parse is an `UNPARSEABLE`
violation, not a silence. Measured, and therefore **not declared as a limit**.

### WHAT THE WIDENING FOUND IN EXISTING CODE — A FINDING, NOT A LIMIT

**THIS ROW'S DECLARED COMMAND EXITS 1 AT THIS SHA, AND THAT IS DELIBERATE AND DISCLOSED.**

`engine/evaluate.py`'s `guarded` — the closure inside the **private** decorator
`_absence_is_never_a_number` that carries the CD-ASR-F03 post-condition — is a **public-named**
callable in a RULE 1 package, with `*extra, **extra_by_name`, and no `@admits`:

```
VIOLATION  src/crash_detector/engine/evaluate.py:341
    rule: UNDECORATED_JUDGEMENT_PATH_DOOR
    what: guarded is a public entry point on a judgement path and it carries no @admits(...).
CD-RT-002-DOORS-REQUIRE-THEIR-TYPES: FAIL — 1 violation(s)
```

**IT IS NOT EXEMPTED AND IT IS NOT FIXED.** `engine/evaluate.py` is outside WO-2R3 increment 6's
writable scope; adding an exemption for it would be the quiet widening this project keeps finding;
and deciding whether it should be decorated, renamed `_guarded`, or declared exempt **is a design
question for the Product Owner**. Raised as `CD-ENG-WO2R3-02-F06` and left open for the fifth
Assurance seat.

Note also that `functools.wraps` gives it the **runtime** `__name__` `_evaluate_dial`, so the static
reading and the runtime name **disagree** about whether it is public at all — which is part of what
makes it a question rather than an oversight.


---

## DECLARED LIMIT 8 — `ESTABLISHED_HERE` IS RESOLVED THROUGH ALIASES, AND THE COUNT IS CORRECTED

**NEW AT WO-2R3 INCREMENT 6** (`PO-DECISIONS-0011` ruling 1 item (c)). This is `admission.py`'s
DECLARED LIMIT 1 reproduced here, plus the check's own alias-resolution limit.

**WHY THE COUNT IS ONLY NOW IN THIS FILE, WHICH IS ITSELF WHY THE DEFECT SURVIVED FIVE
INCREMENTS.** The limit's own header says it is stated *"in the check header, the register entry
and the execution contract"* — and the **count** was in `admission.py` **alone**.
`grep -rn "across FIVE" required-tests.yaml contracts/execution/` at `531c95c` returns **nothing**.
**THE THREE-PLACE DISCIPLINE THAT WOULD HAVE CAUGHT THE DRIFT NEVER APPLIED TO THE NUMBER, BECAUSE
THE NUMBER WAS ONLY IN ONE PLACE.** Raised as `CD-ENG-WO2R3-02-F07`.

**SUPERSEDED WORDING, QUOTED AND NOT DELETED** (`PBG-CONT-003`):

> *"EIGHT parameters across FIVE callables declare it … A ninth use fails that test."*

**THE MEASURED FIGURE IS 16 PARAMETERS ACROSS 9 CALLABLES**, from `CD-ENG-WO2R3-02`'s own run of
`python3 -B tools/register/check_judgement_path_doors.py --root .`, which prints
`ESTABLISHED_HERE uses: 16` and lists all sixteen with file, line and parameter. Not transcribed
(`CD-RULE-009`).

**WHAT KEEPS THE NUMBER TRUE** — because this project has now been bitten twice by a count written
into prose (this limit, and the copied *"32 members"* that `CD-PL-F91` caught): **the number is not
the thing guarded, the SET is.**
`tests/test_admission.py::test_the_established_here_exemptions_are_exactly_this_set` pins the exact
set by module, callable and parameter, enumerating from the **runtime compiled declaration
objects**. If the number goes stale again, the set assertion fails first and names what moved.

### Alias resolution — what is resolved, and what is not

**RESOLVED:** an import alias · the plain form · a module-level rebinding run to a **fixpoint** ·
any attribute spelled `.ESTABLISHED_HERE`, whatever the module is aliased to.

**NOT RESOLVED, DECLARED RATHER THAN SILENT:** a name bound **inside a function body** · a name
computed at runtime (`getattr(admission, "ESTABLISHED_" + "HERE")`) · an exemption reached through a
**container** (`ALIASES = {"eh": ESTABLISHED_HERE}`) · a **wrapper**
(`def eh(reason): return ESTABLISHED_HERE(reason)`), which is a call, not a reference.

**MEASURED, BOTH ARMS** — `variants/WO-2R3/P-C-an-aliased-exemption.py` adds the auditor's own
`ESTABLISHED_HERE as _EH` door: at `531c95c` the check reports `uses: 16` and does **not** name it;
here it reports `uses: 17` and **does**.

### A correction to the record this seat owes the fourth Assurance seat

`SUPPLEMENT-T2-GRADING` §2.4: *"For a door parameter exemption I found no carrier that sees it."*
**MEASURED** on a pristine `git archive 531c95c` extraction, with the auditor's aliased door added,
running the readers the auditor did not run:

```
doors check                        : exit=0, still reports 16   <- invisible
tests/test_judgement_path_doors.py : exit=0, 22 passed          <- invisible
tests/test_admission.py            : exit=1, 2 failed, 23 passed
the whole suite                    : exit=1, 2 failed, 1536 passed
```

Failing: `::test_the_established_here_exemptions_are_exactly_this_set` and
`::test_every_established_here_states_a_reason_in_the_artefact`. **A door-parameter exemption added
under an alias was ALREADY CARRIED at `531c95c`**, because that reader enumerates from the runtime
compiled objects where a spelling cannot matter. The auditor ran the door-side carrier, found it
blind, and **narrowed its claim to exactly what it had measured** — the right discipline, and why
this is a correction and not a rebuttal. What was genuinely broken, and is fixed here, is **the
check's REPORT**: it said 16 when there were 17.

**CARRIER MEASURED:** `tests/test_admission.py`, red on a seventeenth use whether or not it is
aliased, **at both SHAs**. It covers every route in the "not resolved" list — including the ones the
check cannot see — because it never reads a name at all, *provided* the module is imported by
`pkgutil.walk_packages` and the door object is reachable from a module or class namespace. **For an
exemption on a door not reachable from any module or class namespace: NOT PROVED TO BE CARRIED
ANYWHERE.**
