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

**1 — CONSTRUCTORS ARE NOT SUBJECTS, AND THAT IS A REAL GAP IN §D AS SCOPED.**
`ConfigSnapshot(...)`, `DialSpec(...)`, `ModelSpec(...)` and `PanelRow(...)` are public entry points
on the judgement path and they establish their fields in `__post_init__` — that is, in a BODY, which
is the thing §D.1 exists to stop relying on. §D.2's table lists no constructor and this check does
not invent that scope. MEASURED: `variants/WO-2R3/V17-constructor-body-escape.patch` deletes the
`type(spec) is not DialSpec` loop from `ConfigSnapshot.__post_init__` and this command still exits 0
with **54 assertions** (re-measured at WO-2R3 increment 3; it was 38 at increment 2, before
`collectors` joined RULE 1). **CARRIER, IN PART:** the frozen dataclasses re-establish every field and the
suite measures them refusing a look-alike TODAY; as a structure that survives an edit to those
bodies, **NOT PROVED TO BE CARRIED ANYWHERE.** RAISED AS A FINDING to the Project Lead rather than
closed by the seat that found it.

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

What IS closed at that door and is **not** a limit — stated so that seat does not waste the trip:
`policy` exact `RetryPolicy` (`isinstance` admitted a subclass shadowing `max_attempts` with a
property until this increment), `started_utc` exact `datetime` and then rebuilt by `ensure_utc`,
`delay` exact `DelayKind` from a closed enum, and every value the four Protocols RETURN exact-typed
at its point of return.

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

**WHAT 6c DOES NOT DEFEAT.** It is **NOT a caller route**: it needs the ability to execute code
inside the package. BP-AMENDMENT-0001 §D.3 part 1's claim is about what a **CALLER** of `collect` can
supply, and that claim **SURVIVES** — `clock` and `sleep` are not parameters and the interpreter
refuses to pass them.

**CARRIER FOR THE WHOLE OF LIMIT 6: NOT PROVED TO BE CARRIED ANYWHERE.** Every route above needs the
ability to execute code inside this package, which is the universal limit every in-process guard on
this project lives inside. Saying that is strictly weaker than "cannot happen", and it is said rather
than implied.

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
