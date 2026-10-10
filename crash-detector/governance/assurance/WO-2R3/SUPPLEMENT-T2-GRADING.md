# SUPPLEMENT TO THE WO-2R3 ASSURANCE VERDICT — GRADING OF ADDENDUM-T2-ADAPTER-BOUNDARY

**Actor:** CD-ASR-WO2R3-01 · **Under:** CD-DISPATCH-WO2R3-ASSURANCE, role unchanged · **Banked beside VERDICT.md under CD-D-143, never inside it**

> **RECORDED VERBATIM BY THE PROJECT LEAD AND NOT EDITED.** This is the auditor's document, written
> after it was handed back its own late-returning delegated measurement
> (`ADDENDUM-T2-ADAPTER-BOUNDARY.md`) with no steer on the answer. **IT MOVES THE OVERALL VERDICT
> FROM AMBER TO RED, ON ITS OWN RE-MEASUREMENT, AGAINST A SENTENCE IT HAD WRITTEN ITSELF.**
> `VERDICT.md` IS NOT EDITED — it stands as written and this stands beside it (`PBG-CONT-003`:
> corrections supersede, never edit).
> A RED is not a failure of the project and is not an acceptance either (`PBG-AUTH-003`):
> disposition is the Product Owner's. The Project Lead's reconciliation of this document —
> including the two claims it re-measured itself and the findings it raises — is
> `governance/engineering/build-log/BL-20260822T205345Z-0107.yaml`.

**Target re-verified before and after this work:** SHA `531c95c2c42df51e24d4ce9cdb1f8a0d1818f5c0`, tree fingerprint `69b1fef83741d6d0ca14723a2df6ffeeb8efac3ab01195158ce65f22e2dcba5f`, porcelain **0**. Unchanged from both takes in VERDICT.md. All work in `/tmp` extractions; nothing under `pbg/`, the lane or the audit worktree was touched.

---

## 0. THE ANSWER, UP FRONT

**Yes. It changes two of the three things you asked about, and it changes my overall verdict.**

| | in VERDICT.md | now | why |
|---|---|---|---|
| **T2 — CD-BP-003** | AMBER | **RED** | four escapes, three verified by me; two refute claims the record lists as *closed and not a limit* |
| **CD-AC-002** | AMBER | **AMBER — unchanged** | no route reaches a dial score or the envelope; containment traced and real, though it is an unimplemented enum |
| **CD-AC-005** | AMBER | **AMBER — unchanged grade, materially weakened reasoning** | no route from foreign input to a forged `Agrees`; but the mitigation I leaned on is now measurably softer |
| **OVERALL** | AMBER | **RED** | the stated ground of my AMBER is falsified — see §1 |

**I did not grade this on the delegated seat's word.** I independently re-ran the load-bearing items. What I verified and what I did not is set out in §5, item by item.

---

## 1. WHY THE OVERALL VERDICT MOVES TO RED

My AMBER rested on one sentence, which I wrote and which the Product Owner would reasonably have relied on:

> *"This is not a RED: I found no mechanism defect. Every finding is about the scope of the class and the integrity of the evidence, not about whether the machinery works. It does."*

**That sentence is now false, and I am the party who has to say so.** ESCAPE 1 is not scoping and not evidence integrity. It is a correctness defect in the shipped ingestion path, it has a two-line counterfactual fix, and I reproduced it myself. Leaving an AMBER standing on a premise I have since disproved would be exactly the "control scoped narrower than the class it names" failure this project keeps finding — committed by its auditor.

**RED here means: one bounded, well-understood correctness fix is owed before the gate, not that WO-2R3 was misconceived.** Everything I credited in VERDICT.md §1 still stands — the runtime closure is real, the rename test passes, the counterfactual arm holds, CD-D-135 is verified in the git graph. None of that is withdrawn.

---

## 2. WHAT I VERIFIED MYSELF

### 2.1 ESCAPE 1 — the stored payload is not the validated payload (**VERIFIED**)

Read first at `runner.py:670 / 709 / 728`: `validator.validate(response.payload, …)` → `adapter.is_empty(response.payload)` → `OK(payload=response.payload, …)`. **The adapter's own code is handed a live reference to the payload between validation and storage, and nothing re-validates.**

Reproduced on a pristine extraction, shipped default `JsonSchemaValidator`, strictest declarable schema (`additionalProperties: false`, `required`, `minimum/maximum`), no source edit:

```
mode=none    validator saw {'reading': 0.25}   stored {'reading': 0.25}
mode=mutate  validator saw {'reading': 0.25}
             stored  {'reading': inf, 'not_in_schema': '\x00\x00\x00',
                      'type': <module 'builtins' (built-in)>}

does the STORED payload conform to the schema it was judged by?
   NO -> SchemaRejection: JSONSCHEMA_ADDITIONALPROPERTIES at <root>

type(OK.payload) is exactly dict : True    <- the TYPE is established
value holds a live module object : True    <- the VALUE is not the one that passed validation
```

**It refutes a written claim, quoted verbatim from `required-tests.yaml:1199-1203`, under the heading `WHAT IS CLOSED AT THAT DOOR AND IS NOT A LIMIT`:**

> *"…and every value the four Protocols RETURN exact-typed at its point of return."*

The sentence is *literally* true and *offered* as closure. It closes the type and not the value. **A claim filed under "not a limit" that turns out to be a limit is worse than an undeclared gap, because the declaration is what a reader stops reading at.**

### 2.2 ESCAPE 2 — "not a caller route" is false at this door (**VERIFIED**)

`admission.py:181-184`, verbatim:

> *"**WHAT IS AND IS NOT DEFEATED BY (c).** It is NOT a caller route: it needs the ability to execute code inside the package."*

`collect` calls six methods on caller-supplied objects, interleaved with its own establishment sequence. Passing an object to that door **is** the ability to execute code inside the package. Demonstrated from caller code, with a hostile class that imports nothing from `crash_detector`:

```
reached module globals of: crash_detector.collectors.runner
runner.FetchedResponse rebound: True
final_outcome: OK {'reading': 0.25}      # via a property-backed look-alike
```

The look-alike defeated `type(response) is not FetchedResponse` at `runner.py:663` — **also listed under "WHAT IS CLOSED AT THAT DOOR AND IS NOT A LIMIT."**

**This converges with my F-A4 and the convergence is the finding.** In VERDICT.md I showed `establishment.py:222-225`'s *"Every route requires the ability to execute code inside this package"* is **too narrow** — `Agrees.__new__` needs no such thing. ESCAPE 2 shows the same sentence treats in-package execution as a high bar that the CD-BP-003 door **hands to any caller**. **The sentence is wrong in both directions at once**: it overstates the precondition for the routes it names, and understates who already has it. It appears in two modules and is load-bearing in both.

### 2.3 ESCAPE 4 — and I extend it past where the delegated seat stopped (**VERIFIED, AND WIDENED**)

Doors check, four arms, same undecorated public door in `collectors/runner.py`:

| where defined | doors check |
|---|---|
| module-level `def` | **exit 1** |
| method of a top-level class | **exit 1** |
| method nested one level (`Outer.Inner`) | **exit 0** |
| function-local `def` bound in a module dict | **exit 0** (and live: `POLICY["decide"]` accepts unestablished arguments) |

**My extension, which is not in the addendum and not in my verdict:** I ran the same shape against the **constructor** check — a public frozen fielded dataclass, nested one class level, **inside `engine/`, a RULE A judgement-path package**:

```
POPULATION unchanged at 33      ctor EXIT=0      doors EXIT=0
sweep unchanged (534 sites, 15 violations)
--why ledger mentions it: 0  — NOT EVEN EXAMINED
runtime: Judgement.Verdict(score=object(), breached='maybe') ACCEPTED
full test suite: 1538 passed
```

**Root cause, common to both instruments and to my F-A2:** `check_judgement_path_doors.py:659` and `check_constructor_field_establishment.py:591/601/622` all enumerate **`for node in tree.body`** — top level only. Only `_admits_reach` (line 472) uses `ast.walk`.

**This supersedes my F-A2 and is broader than it.** F-A2 named RULE A's package vocabulary as the limit and needed a new package to escape. **The real limit is the AST walk, and it needs no new package, no new module and no rename — one indentation level inside an already-governed file.** The check's own note offers the reassurance *"a class that was not looked at is printed OUT under `--why` with the clause that excluded it, **or is not among the 99 examined at all**"* — the escape lives in that second disjunct, and nothing asserts the count of examined classes.

### 2.4 The exemption population — doubled, and hideable (**VERIFIED, AND WORSE THAN REPORTED**)

`admission.py:75-76` declares:

> *"**`ESTABLISHED_HERE` IS AN EXPLICIT WEAKENING AND IT IS COUNTED, NOT HIDDEN.** EIGHT parameters across FIVE callables declare it… A ninth use fails that test."*

Measured from the artefact by the project's own instrument: **16 parameters across 9 callables.** The declaration is stale by exactly a doubling.

And the counting instrument **fails the project's own rename test.** I added one door in `collectors/validation.py` using a one-word alias, `ESTABLISHED_HERE as _EH`:

```
doors check: still reports 16 exemptions,  EXIT=0     <- invisible
tests/test_judgement_path_doors.py: 22 passed        <- invisible to the door-side carrier too
```

**"COUNTED, NOT HIDDEN" is false under a one-word alias.** For a *door parameter* exemption I found no carrier that sees it. (The addendum reports pytest catching the alias; that is the *field*-exemption carrier in `test_field_establishment.py`, a different mechanism. I am narrowing the claim to what I measured, not widening it.)

So the exemption population is simultaneously: **doubled, undeclared at its true size, and concealable by aliasing** — against a limit whose own text names "exemptions that start absorbing a population" as the failure mode this project keeps re-finding.

---

## 3. WHY THE TWO CRITERION GRADES DO NOT MOVE

**CD-AC-002 — AMBER, unchanged.** The addendum traces the hostile payload to `engine/mapping.py` and it stops at `MappingKind.UNSPECIFIED`; `grep '\.payload'` finds no reference under `publication/`, `serving/` or `witness/`. Nothing here combines two dials into one number, which is what the criterion forbids. **But one prop is removed:** "every value the four Protocols RETURN exact-typed at its point of return" can no longer be cited toward this criterion, because §2.1 shows it establishes the type and not the value. And the containment is honestly an **unimplemented enum, not a guard** — the first computing `MappingKind` member puts an `inf`-bearing, schema-violating payload into the arithmetic. That is prospective, and I grade the artefact in front of me. AMBER stands.

**CD-AC-005 — AMBER, unchanged grade, weaker reasoning.** No demonstrated route runs from a foreign adapter to a forged `Agrees`; the witness path does not pass through `collect`. But in VERDICT.md I softened F-A4 by calling in-process execution "the universal limit every in-process guard on this project lives inside." **§2.2 measurably weakens that mitigation**: this codebase hands in-process execution to callers at its declared-foreign boundary. The principle is dented; the fact is not breached.

**What would flip CD-AC-005 to RED, stated so it can be tested rather than argued:** a demonstrated route from any foreign or caller-supplied input to a `WitnessPanel` value of type `Agrees` that did not pass `Agrees.__init__`. I did not find one. I did not have time to look hard, and I say so.

---

## 4. ON CD-PL-F94 — THE CORRECTION IS RIGHT, AND IN ONE RESPECT TOO GENEROUS

You asked me to say plainly if the self-correction is too generous. **In one specific respect it is, and it is generous to the wrong party — it is too hard on the Project Lead and too easy on the instrument.**

CD-PL-F94 charges the Project Lead with accepting V43's code-path change as a class closure, and with never putting to itself the sideways-move question it wrote into my brief. Both true. But the framing makes it a **reading failure**, and it was also a **steering failure by the artefact**:

`check_constructor_field_establishment.py`'s **DECLARED LIMIT 2** declares *RULE A's package list* to be the vocabulary, and `V16-new-package-undecorated-door.patch` exists to demonstrate *that* axis. Every party — Engineer, Project Lead, Product Owner, and me in VERDICT.md §3 — therefore asked "what if it is in a different **package**?" **The answer is that packages were never the limit.** §2.3 escapes with the type in `engine/`, in an existing file, one indentation level down. The declared limit named a real limit and, by naming it, hid a larger one behind it.

**So the honest charge is not "the Project Lead failed to ask a question that was available." It is "a declared limit pointed four parties at the narrower of two axes, and nobody tested the axis it did not name."** That is the same pattern as CD-D-114, CD-PL-F89, CD-D-134, CD-PL-F93 — and it is now, by my count, the **ninth** instance, three of which are inside increment 5 and one of which is in the instrument that defines the class for this gate.

I would not accept a correction that leaves the declared limit's wording standing as sound.

---

## 5. WHAT I VERIFIED AND WHAT I DID NOT — SO THIS SUPPLEMENT CAN BE GRADED TOO

**Verified independently, my own commands, pristine `/tmp` extractions:**
ESCAPE 1 (both arms + schema re-check) · ESCAPE 2 (frame-reach and global rebind) · ESCAPE 4's four door-nesting arms · the constructor check's nested-class blindness (**my extension**) · the shared `tree.body` root cause · the 8/5-vs-16/9 count · the aliased-exemption blindness (**widened**) · both refuted claims quoted verbatim from source.

**NOT verified by me — accepted as delegated measurement, flagged as such, and NOT load-bearing for any grade above:**
ESCAPE 3 (hostile sink falsifying the reading key) · the sink / ledger / validator behaviour table · the §6 end-to-end evaluate trace · the `adapter_id` double-read defect · the nested-class and container-held **field** exemption arms · the store-level carriers, which the delegated seat also could not establish.

**Standing gaps from VERDICT.md §7 that this supplement does NOT close:** T8, T9 and T10 remain unmeasured by me. Nothing here touches them.

**One thing I will not do:** grade ESCAPE 3 on the strength of ESCAPE 1 and 2 having checked out. Three verified escapes do not make a fourth true, and this project's record already contains four probes that print a verdict they did not earn (VERDICT.md §5, F-C1).

---

## 6. REVISED NEXT SAFE GATE

1. **Product Owner dispositions the RED.** My verdict is not an acceptance and neither is a RED (PBG-AUTH-003).
2. **One bounded Engineer increment, four items, each independently checkable:**
   (a) **ESCAPE 1** — snapshot the payload after validation, hand `is_empty` a copy, store the snapshot. The counterfactual arm is demonstrated and it is two lines.
   (b) **§2.3** — both instruments walk `ast.walk` rather than `tree.body`, and assert the count of classes examined.
   (c) **§2.4** — resolve `ESTABLISHED_HERE` through aliases; correct the stale 8/5 declaration to the measured figure.
   (d) **F-A1** — `@establishes()` on `Empty`, as the mechanism's own header already prescribes.
3. **Three declared limits are rewritten, not patched around:** `required-tests.yaml`'s "closed and not a limit" list; `admission.py:181-184`; `establishment.py:222-225` and `admission.py:186-189`. Each is presently wrong in a *stated* direction.
4. **A fresh Assurance seat regrades T2 and CD-AC-002/005**, because I have now attacked this surface and am no longer the freshest reader of it.

**The Project Lead promised not to argue my verdict down, and said that covers arguing it up.** It did not argue it either way; it banked the evidence unedited and asked. **I moved it up on my own reading of my own measurements, and the record should show that the thing which changed my mind was a measurement I ran myself after being handed a document I was free to dismiss.**
