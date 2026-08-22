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
-m pytest tests -q` on the same tree goes from **1478 passed** to **57 failed**, and an ORDINARY
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
with 38 assertions. **CARRIER, IN PART:** the frozen dataclasses re-establish every field and the
suite measures them refusing a look-alike TODAY; as a structure that survives an edit to those
bodies, **NOT PROVED TO BE CARRIED ANYWHERE.** RAISED AS A FINDING to the Project Lead rather than
closed by the seat that found it.

**2 — RULE 1's PACKAGE LIST IS A VOCABULARY.** `engine` and `serving` are spelled in the check. A
judgement-path door written under a package name the check has never heard of is reached only by
RULE 2, and only if it annotates its return type. MEASURED:
`variants/WO-2R3/V16-new-package-undecorated-door.patch` adds
`src/crash_detector/judging/decide.py` with a public, undecorated, unannotated `decide(reading)` and
this command still exits 0 with 38 assertions. **NOT PROVED TO BE CARRIED ANYWHERE** — no other
layer enumerates judgement-path packages. It is stated here so the fourth Assurance seat can hit it
without having to find it first.

**3 — `collectors/` IS NOT YET A JUDGEMENT-PATH PACKAGE HERE, BY SCOPE AND NOT BY OVERSIGHT.**
A6 — `collect(adapter, policy, sink, ledger, collector_run_id, clock, sleep, validator)` — is
BP-AMENDMENT-0001 §D.3 and WO-2R3 increment 3, and §D.3's closure is a DIFFERENT mechanism: `clock`
and `sleep` stop being caller callables, and the protocol returns are established at the point of
return. Adding `collectors` to RULE 1 today would fail this check on work that has not been
dispatched. The check PRINTS the gap at every run. **CARRIER MEASURED:**
`tests/test_judgement_path_doors.py` asserts the gap is still declared, so it cannot close silently.

**4 — A DECORATOR NAMED `admits` IS RECOGNISED BY ITS NAME IN THE SOURCE.** This check reads TEXT;
it cannot know that the `admits` a module imported is `crash_detector.admission.admits`. MEASURED:
`variants/WO-2R3/V18-counterfeit-admits.patch` defines a do-nothing `admits` in
`crash_detector/own_terms.py` and imports it into `serving/witness_resolver.py` — this command exits
0 with 38 assertions and PASS, and `ASR3-F04`'s duck row then renders `WITNESS AGREES`. **CARRIER
MEASURED: THE RUNTIME.** The same patched tree runs **3 FAILED** under `PYTHONPATH=src python3 -B -m
pytest tests -q`, because the plants call the real doors and observe the real refusals. A static
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
