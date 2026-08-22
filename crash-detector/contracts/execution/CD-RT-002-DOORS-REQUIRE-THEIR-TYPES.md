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
day it is written. MEASURED: the subject count went from **19 to 24** and the assertion count from
**38 to 54**, and `tests/test_judgement_path_doors.py::test_the_collector_doors_are_really_subjects_and_not_merely_counted`
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

## What this check is NOT

**IT IS NOT PROOF OF A RUNTIME PROPERTY.** A static checker exiting non-zero is not proof that
anything is unconstructible, because every escape on this project's record passed a static checker.
The runtime claims are made by the plants (`tests/test_judgement_path_doors.py`) and by
`tests/test_admission.py`, and the mechanism's own residues — including a bypass the implementing
seat found in its own doors and closed, and the `__closure__` half it could not close — are DECLARED
LIMIT 6 in `src/crash_detector/admission.py`.

**IT IS NOT A LIST OF THREE FIXES.** The instance game — *"add `type(row) is not PanelRow` to
`resolve_panel`"* — is what the first gate caught, what the auditor named, and what §D.1 repeats. The
unit of work is the class of doors: one mechanism, deriving what it requires from each door's own
signature, and one check enumerating them from the tree.
