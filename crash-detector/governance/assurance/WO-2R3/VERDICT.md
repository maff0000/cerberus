# ASSURANCE VERDICT — WO-2R3, THE FOURTH GATE

**Actor:** CD-ASR-WO2R3-01 · **Dispatch:** CD-DISPATCH-WO2R3-ASSURANCE (CD-D-141) · **Role:** ASSURANCE_ENGINEER

> **RECORDED VERBATIM BY THE PROJECT LEAD AND NOT EDITED.** This is the auditor's document. The
> Project Lead's reconciliation of it — including the two claims it re-measured independently and
> the findings it raises against itself — is `governance/engineering/build-log/BL-20260822T202600Z-0106.yaml`
> and is a SEPARATE record. Nothing below has been softened, shortened or rebutted in place.
> A PASS is not an acceptance and neither is an AMBER (`PBG-AUTH-003`): disposition is the Product
> Owner's.

## VERDICT: **AMBER**

**CD-AC-002 — "The two dials are never blended": AMBER. NOT closed by WO-2R3.**
**CD-AC-005 — "WITNESS UNAVAILABLE ≠ WITNESS AGREES": AMBER, weaker than CD-AC-002. NOT closed by WO-2R3.**

**Next safe gate:** Product Owner disposition of the six findings below, then a bounded increment closing F-A1 (the vacuous member), F-A2 (the floor assertion) and F-C1 (corpus probe verdicts) — each of which is small, mechanical and independently checkable. **No further scope should be added to WO-2R3.** This is not a RED: I found no mechanism defect. Every finding is about the *scope of the class* and the *integrity of the evidence*, not about whether the machinery works. It does.

---

## 0. Reconciliation, independence, boot

| | |
|---|---|
| Target SHA | `531c95c2c42df51e24d4ce9cdb1f8a0d1818f5c0` — matches dispatch |
| Tree fingerprint (start / mid / end) | `69b1fef83741d6d0ca14723a2df6ffeeb8efac3ab01195158ce65f22e2dcba5f` — **identical at all three takes**, matches dispatch |
| `git status --porcelain` | **0 lines** at start and end |
| Scope audited | `f30e63c..531c95c`, all 22 commits, increments 1–5 and the bounded completion |

**Independence (PBG-SOD-001):** I am CD-ASR-WO2R3-01, a fresh seat. I am none of CD-ASR-WO2-01/-02, CD-ASR-WO2R2-01, and not CD-ENG-WO2R3-01. I did not write, review, advise on or dispatch any part of what I audited. Nothing was mutated in the audit worktree: no commit, no `git apply`, no `git worktree add`. All variant work was done in throwaway `/tmp` extractions via `git archive`.

**Boot verdict: RED (`CONTINUITY_REFERENCE_INVALID/RESUME_BLOCKED`).** I tested the disclosure that this is a cross-branch artefact and **the disclosure holds**: `pbg boot` on `main` returns **AMBER** (`CONTINUITY_MATCH/RESUME_AMBER`) with `current_work` fully current. The lane RED is not about the work.

**But I disagree with it being fully harmless, and this is on nobody's list.** `governance/engineering/ACTIVE_WORK.yaml` was last modified at `bf8fcf9` (2026-08-19) **on both branches** — never touched during WO-2R, WO-2R2 or WO-2R3. It still reads `current_work: CD-WO-002` and `continuity_record_commit: PENDING`. `pbg boot` does not depend on it, so tooling-assisted boot is fine. But `CLAUDE.md` documents a **manual boot fallback** — "If unavailable, perform the same sequence by reading, in order: … `governance/engineering/ACTIVE_WORK.yaml` …" — and a seat taking that documented path resumes against a work order three revisions stale. The project is required to survive its tooling being unavailable; on that path, this file is a trap. **Severity LOW, but it is a continuity record that has been PENDING for four days.**

---

## 1. THE HEADLINE MANDATE — THE RUNTIME ATTACK ON THE RUNTIME CLOSURE

**The Engineer's self-disclosure is TRUE and I independently confirmed it.** With V17 applied, `check_judgement_path_doors.py` and `check_constructor_field_establishment.py` both exit **0** and both print **PASS** (54 and 97 assertions). A seat verifying increment 5 by running the two register checks has verified nothing about it.

**The runtime closure is REAL.** Same probe, three trees, one measurement each:

| arm | result | refusing layer, from the failure text |
|---|---|---|
| clean `531c95c` | REFUSED | `builtins.TypeError: ConfigSnapshot.dial_specs must all be DialSpec` — raised at `engine/config.py:238` in `__post_init__` — **the BODY** |
| `+V17` | REFUSED | `crash_detector.establishment.FieldNotEstablished: ConfigSnapshot.dial_specs[0]=HostileDialSpec is not admitted; every element must be exactly DialSpec` — raised at `establishment.py:434` in `__init__` — **the CLASS BOUNDARY** |
| `+V17`, `@establishes` removed from `ConfigSnapshot` (**counterfactual arm, CD-D-079**) | ***ACCEPTED*** | none — the object escaped carrying `['HostileDialSpec','HostileDialSpec']` |

The hostile value is the one the deleted body guard's own comment names: a `DialSpec` subclass shadowing `model_ref`. **The body edit removes the body rule; the class-boundary rule catches it; remove the boundary and it escapes.** That is a three-layer contrast, not three exit codes, and it meets the CD-ENG-WO2R3-F12 standard.

**RENAME TEST — PASSES.** I renamed the field `dial_specs → spec_manifest` and the class `DialSpec → DialSpecification` consistently across `src/`. Population unchanged at 33, static exit 0, and under V17 the refusal survives verbatim: `FieldNotEstablished: ConfigSnapshot.spec_manifest[0]=Hostile is not admitted; every element must be exactly DialSpecification`. **The boundary is structural, not a vocabulary guard wearing a structural label.**

**P7 at the constructor (T1) — CONFIRMED AT RUNTIME.** Adding `operator_override: bool` to the governed type `Unavailable` faults the type: static exit 1, and at runtime **every** construction raises `UndeclaredField`, *including previously valid ones*. This is materially stronger than the static check and it is the genuine article.

**CD-D-135 — VERIFIED IN THE GIT GRAPH, not in prose.** At `4a5098d` the instrument is PRESENT and `src/crash_detector/establishment.py` is ABSENT, and the instrument reports **`FAIL — 32 violation(s)`**. The population could not be a photograph of the mechanism's diff. The claim is sound.

**My judgement on whether static evidence has been standing in for runtime evidence across six increments: PARTLY, and the seat said so before I did — but the substitution is real and it is concentrated in exactly one place.** The mechanism itself is runtime-enforced and I proved it. What is static-only is the *class definition*, and §3 below is where that costs something.

---

## 2. NAMED TARGETS T1–T11

| | target | verdict |
|---|---|---|
| **T1** | P7 — new field arrives refused | **PASS.** Runtime-confirmed above. `UndeclaredField` on every construction of the faulted type. Static and runtime agree. |
| **T2** | CD-BP-003, the adapter boundary | **AMBER — the softest surface is still soft, and the record says so.** Independently confirmed: a *conforming hostile adapter* (V26) is **ADMITTED** — `missing protocol members: ()`, payload recorded, row written. **Nothing in this tree refuses it.** `FetchedResponse.payload` remains `NOT PROVED TO BE CARRIED ANYWHERE` and I found no guard over it. I verified the containment claim: a **fourth** `ESTABLISHED_HERE` is reported by the check (`exemptions: 4`) but the check still **exits 0**; the carrier is `tests/test_field_establishment.py::test_the_established_here_field_exemptions_are_exactly_this_set`, which **FAILS**. So "a fourth use is a test failure, not a quiet widening" is TRUE, correctly attributed to the test and not the check. A deeper adapter attack was delegated and had not returned when I closed the verdict — **stated as a measured limit, not a silent omission.** |
| **T3** | §D scoping incl. CD-D-105 | **CHALLENGED — see §3.** Constructors are now genuinely subjects; that half of CD-D-105 is discharged. The scoping defect is not in *what* is a subject but in *what is reached*. |
| **T4** | the instrument's own enumeration | **AMBER.** The definition, not the count, is where it fails — §3. I asked the question the header invites ("what is it still measuring a vocabulary of?") and the answer is: **`JUDGEMENT_PATH_PACKAGES = ("engine","serving","collectors")` reaches only 14 of 33 members. The other 19 enter by name-resolution.** |
| **T5** | Class-2 sweep exiting 1 | **DECLARATION ACCURATE, NOT A PARKED DEFECT — with one correction.** I measured `534 sites, 15 violations` at the target and confirmed it is **unmoved** by my plants. But the WO-2R3 variant MANIFEST still records **514 / 11**; the four increment-5 additions in `crash_detector.establishment` are real and undispositioned. The declaration is honest; a manifest copy of it is stale. |
| **T6** | GRANT-MATRIX-LIVE | **BITTEN. And the standing premise was FALSE.** See §4 — this is a significant correction to the record. |
| **T7** | the three `variants/WO-2R` routes | **CLOSED — but NOT by increment 5's machinery, and one of the four "pre-existing" failures is not pre-existing.** All four fail `git apply` on context drift only and port cleanly. `V03`, `E04`, `V06` are genuinely closed at the CD-AC-001 layer by `refuse_a_number_without_its_inputs` (a WO-2R-era post-condition), *not* by `establishment.py` — with V03/E04/V06 applied the constructor check exits **0**, population unchanged at 33. `V05` is closed by `ReadingSurfaceViolated` at import. **`V05` is NOT pre-existing — it was broken by increment 5's own `@establishes` insertion (CD-ENG-WO2R3-F20). Calling all four "pre-existing" understates by one what increment 5 broke.** |
| **T8** | the eleven Class-2 dispositions | **NOT ESTABLISHED — delegated measurement did not return.** I confirmed the 11+4=15 decomposition and that the four new ones are all in `crash_detector.establishment`. I did **not** independently assess each of the eleven for substance. **Stated plainly rather than glossed.** On the *sequencing* invitation, see §6. |
| **T9** | F15 and the blindness window | **NOT ESTABLISHED — delegated measurement did not return.** I did, however, find the window's shape independently and from a different direction: §3's finding is precisely a thing that survived multiple reconciliations because *every instrument was green and nobody asserted the population*. |
| **T10** | CD-ENG-WO2R3-F10 | **NOT ESTABLISHED — delegated measurement did not return.** Adjacent evidence: the corpus re-run shows `CD-RT-002-TYPE-NO-ARITHMETIC`'s blend now dies inside the plant itself (`QuantityProvenanceMissing` at `magnitude.py:389`), which is the F10 shape still live. |
| **T11** | the widened class as an attackable claim | **ATTACKED, AND IT DOES NOT SURVIVE INTACT — §3.** |

---

## 3. THE FINDING OF THIS AUDIT — THE WIDENING MOVED THE ONE AXIS THAT WAS ALREADY SAFEST

This is my attack on T11, on CD-ENG-WO2R3-F24 **as the Engineer framed it**, and it is the fifth instance of the pattern the dispatch told me to assume was present.

Membership is `(1) public ∧ (2) frozen dataclass ∧ (3) reached by RULE A|B|C`. PO-DECISIONS-0010 ruling 1 deleted clause **(4)**, the locus gate. The Engineer says the error direction is toward a **larger** class. **That is true of the axis the ruling moved and irrelevant to the three it did not** — and the reach is where the narrowness lives.

**F-A1 — The vacuous member is runtime-unguarded, and the widening's entire measurable effect at this SHA was to add it.**
Measured across the lane, the population goes `32` at `46adf33` → `33` at `c18aeb4` (the widening). The one member added is `Empty`. I then did what the dispatch asks:

- Add a field to **`Empty`**: static **exit 1, VIOLATION** (the instrument's claim "add one field and it becomes REQUIRED on the same run" is TRUE) — but at runtime `Empty(confidence=object())` is ***ACCEPTED***, `is_establishing_type(Empty) → False`. **Nothing refuses it.**
- Add a field to a **decorated** member (`Unavailable`): runtime `UndeclaredField` on every construction.
- Apply `@establishes()` to `Empty` — **exactly as `establishment.py`'s own docstring prescribes** ("`@establishes()` with no declarations is a meaningful and deliberate statement, not a no-op … adding one later refuses every construction") — then add the field: runtime **`UndeclaredField`**.

So the ruling's phrase **"FAILS ON ARRIVAL"** — which in this module's own vocabulary means *raises on every construction* — is a **static check line only** for the one member the widening added. **The fix is one decorator, already designed, already documented in the mechanism's own header, and it was not applied.**

**F-A2 — A fielded public frozen judgement-path type with no establishment passes EVERYTHING if it is placed outside the reach.** The dispatch asks this literally. The answer is **yes**. I created `src/crash_detector/judging/decide.py` containing a public frozen dataclass named **`Verdict`** — the same name V43 uses — with `score: float, breached: bool` and no establishment:

```
ctor  EXIT=0     POPULATION unchanged at 33
doors EXIT=0
sweep unchanged (534 sites, 15 violations)
full test suite: 1538 passed
runtime: Verdict(score=object(), breached='maybe') ACCEPTED
```

**V43 — the ONLY evidence for the widened class — is therefore an artefact of WHERE the type was put, not of WHAT it is.** The identical class in `engine/verdict.py` is caught; in `judging/decide.py` it is invisible. The check is *honest* about this — the ledger prints `OUT … clause (3): RULE A — no; RULE B — no; RULE C — no` under `--why` — but honesty about a limit is not closure of a class.

The same holds one step earlier at clause (2): a public **non-dataclass** state holder in `engine/` with judgement fields and no method passes both checks, the sweep and all 1538 tests. (If it has a public method the doors check catches it as `UNDECORATED_JUDGEMENT_PATH_DOOR` — so the two instruments *do* compose for callables. The residue is pure data.)

**F-A3 — The class can lose CD-AC-002's central types silently, and the Product Owner's declared floor is never asserted.** Applying **V21** — which removes *one* `@admits` decorator from `evaluate` — I measured:

```
POPULATION: 33 → 30     assertions: 97 → 88
CD-RT-002-CONSTRUCTORS-...: PASS — 88 assertions, 0 violations     ctor EXIT=0
members lost: DialSet, EquityCrashScore, MonetaryDebasementScore
```

**Those are the two dials and their container — CD-AC-002's entire subject — leaving the class while the instrument reports PASS.** RULE B derives the constructor class from the doors' declarations, so changing a door silently narrows what the sibling instrument asserts over.

I checked the floor: `"THE FLOOR THE PRODUCT OWNER NAMED … is ConfigSnapshot, DialSpec, ModelSpec, PanelRow, AttemptRecord — FIVE"` is a `check.note(...)`. **It is printed and never asserted** — there is no `check.violation` guarding it. All five floor members happen to be RULE A, so they are safe *by accident of location*, not by assertion.

**In fairness — and this materially softens F-A3:** `tests/test_field_establishment.py::test_the_static_enumeration_and_the_runtime_population_are_the_same_class` **DOES catch it**, naming `DialSet`, `EquityCrashScore`, `MonetaryDebasementScore` exactly. The carrier exists and is measured. **But note what that test can and cannot do:** it diffs the static population against the `@establishes` decorator registry. It catches *a decorated type falling out*. It cannot see a type that was never decorated and never reached — which is why F-A2's `Verdict` passes it 19/19. **The composed guarantee is "the 32 types that are decorated stay in the class" — a census of the present, which is precisely what PO-DECISIONS-0010 ruling 1 said it was widening the class to escape.**

**F-A4 — `establishment.py`'s DECLARED LIMIT 3 is stated narrower than the class it names.** It says: *"Every route requires the ability to execute code inside this package, which is the universal limit every in-process guard on this project lives inside."* **That is false.** `Agrees.__new__(Agrees)` followed by `__dict__.update(...)` requires no package code at all:

```
Agrees(divergence_measure=0.0, as_of_utc=now, freshness=None)
  -> REFUSED: AgreementWithoutFreshnessEvidence         # the constructor closure works
smuggled = Agrees.__new__(Agrees); smuggled.__dict__.update(freshness=None, ...)
render_panel(smuggled) -> 'WITNESS AGREES'              # CD-AC-005's prohibited outcome
render_panel(FakeAgrees())
  -> REFUSED: NotAdmitted: ... requires exactly Agrees or Diverges or Unavailable
```

The exact-type door admits the smuggled object because `type(x) is Agrees`. **The door's guarantee is class-identity, not boundary-passage**, and this project's doctrine repeatedly treats them as the same thing.

**The route itself is known** — `variants/WO-2R/MANIFEST.md:418-421` records it as "boundary B of the declared limit". What is new is (a) that it lands directly on CD-AC-005's prohibited outcome, and (b) **the asymmetry**: the *dials* layer defends against exactly this and the *establishment* layer does not.

```
DialMagnitude.__new__(DialMagnitude).__setstate__({"provenance": "not-a-set"})
  -> REFUSED: CrossDialCombination: ... A pickle is untrusted input like any other
Agrees: hasattr(Agrees, "__setstate__") -> False
```

**The technique exists in this codebase, is applied by an earlier work order to the dial provenance types, and was not applied to any of increment 5's 32 governed types — while the new module's declared limit asserts the route requires something it does not require.** That is the pattern again, in the load-bearing limit of the increment being graded.

**Attempted and NOT reproduced (reported so the record is not one-sided):** `frozen_by_name[node.name] = node` is a last-wins assignment, so I tried shadowing `EquityCrashScore`/`MonetaryDebasementScore` from a later-sorted module to shrink RULE C's walk. **It did not work** — reach is redundant and `Contribution` stayed IN (population 33→35, exit 0). I also tested the docstring claim that `_module_level_names` "can only enlarge the class, never shrink it": it uses `setdefault(...).update(...)`, it **unions**, and **the claim is TRUE.**

---

## 4. T6 — GRANT-MATRIX-LIVE IS BITTEN, AND THE STANDING PREMISE WAS FALSE

**Full contrast established against a real PostgreSQL 16.14 catalogue: exit 0 clean → exit 1 planted, with the manifest's 9-violation signature reproduced line-for-line, the instrument unmodified (SHA-256 verified byte-identical to `git cat-file 531c95c:tools/register/check_grant_matrix_live.py`).**

**The premise was wrong: exit 3 never meant "database unreachable."** The refusal fires at `check_grant_matrix_live.py:727-735`, *before* psycopg2 is imported and *before* any connection is attempted:

```
CD-RT-003-GRANT-MATRIX-LIVE: PRECONDITION_NOT_MET
    the connection target is not set: CD_CHECK_STORE_HOST, CD_CHECK_STORE_PORT,
    CD_CHECK_STORE_NAME, CD_CHECK_STORE_USER, CD_CHECK_STORE_PASSWORD.
```

`psycopg2` is installed here. **The five documented environment variables were simply never exported.** Every recorded "exit 3 on both arms" across increments 2, 2b, 3, 4 and 5 was the check behaving correctly against an unsupplied configuration — not a limit of the instrument, the plant or the host.

All nine expected violations fired, including the two behavioural probes that are not catalogue queries (`route=live refusal: cd_engine 'SELECT 1 FROM witness.observation LIMIT 1' — THE STATEMENT SUCCEEDED`). The check **discriminates**: `INSERT` was still refused by PostgreSQL and produced no violation, because the plant granted `SELECT` only. And the manifest's central claim is confirmed — under the plant `tests/test_grant_matrix_declaration.py` **still passes (30 passed)**, so the SQL-text comparison is blind to a grant added in a later migration while the live catalogue catches it.

**This is a finding against the record, not against the work.** A plant guarding the only criterion currently passing sat unbitten for five increments and three auditors behind an unset environment variable, and was repeatedly recorded as producing no contrast. **An "unbiteable" instrument that was biteable all along is the same defect class this project keeps finding: a limit stated wider than the thing that actually limits it.** Version note stated rather than glossed: the record cites PostgreSQL 16.15; I measured 16.14, identical signature.

---

## 5. EVIDENCE INTEGRITY — WHAT I FOUND IN THE CORPUS ITSELF

**F-C1 — Four probes print an unconditional verdict string (SERIOUS, and on nobody's list).** Run against the **unpatched** tree, `probe_v29`, `probe_v30`, `probe_v39` and `probe_v42` still print `ESCAPED …` / `ADMITTED -> the new field arrived UNGUARDED` even though nothing escaped. `probe_v42` clean prints `stored state type: str`, `row.state == 'AGREES' answers: False` — and then an escape verdict. **A reader taking the headline line as the result records an escape in an arm that had none.** This is the F12 defect inverted: not two arms failing for different reasons, but one arm *announcing* a result it did not produce. It undermines the corpus as evidence wherever a summary quoted a probe's verdict line rather than its data lines.

**F-C2 — V42 vs V42+V41: the exit code is INVERTED against safety.** Baseline arm exits **0** and *refuses at runtime* (`FieldNotEstablished: PanelRow.state=DuckStr … requires exactly str`). Violated arm exits **1** and *escapes* (`row.state == 'AGREES' answers: True`). **Anyone crediting the exit code credits it exactly backwards.** This is CD-PL-F90's defect class, live, in a place the record has not named.

**F-C3 — Three manifest rows have no executable artefact.** V21, V22, V23 write their command as the literal placeholders `<the P5 probe>` / `<the P6 probe>` / `<the P7 probe>`. No such file exists in the tree. Their quoted results are not reproducible from the corpus alone.

**F-C4 — Stale manifest rows.** V32's row says "ESCAPED, all three"; **ARM 3 is now CLOSED** (`FieldNotEstablished: CollectionResult.source_id=AnswersToAnything … requires exactly str`) — measured at increment 3 and never re-run. V17's suite row says `1519 passed`; it is now `1 failed, 1537 passed`. Constructor assertions are **97**, not the **96** the increment-5 rows quote. Sweep is **534/15**, not **514/11**. Four patches (V16–V19) carry stray empty-file hunks that silently create an empty `src/crash_detector/judging/` package.

**On the eleven plants (independently re-contrasted at their named layers): 11/11 apply, 10/11 contrast, 9/11 fail unambiguously at the layer their proposition names.** Two exceptions:
- **`CD-RT-005-PANEL-UNAVAILABLE-NEVER-AGREES` — PARTIAL.** Only **2 of 12** failures are resolver-return assertions (the named layer). **10 of 12** are `FreshnessNotEstablished` from `staleness.py:570`. The manifest row asserts the stale half "keeps saying whatever it last said" — **that is false at this SHA; it raises.** The criterion is still defended (that layer is named under CD-AC-005 in `required-tests.yaml`), but the row's prose no longer evidences what it says.
- **`CD-RT-002-TYPE-NO-ARITHMETIC` — narrowed, and four tests are green for the wrong reason.** The plant's `__add__` now dies inside itself with `QuantityProvenanceMissing` at `magnitude.py:389`. Four tests asserting the operation raises `TypeError` **pass under the plant — because the plant raises, not because the guard refused.**

**Corpus apply counts, independently measured:** WO-2R3 **28/28**, WO-2R2 **14/14**, WO-2R **66/70** = **108/112**. This confirms the Engineer's headline figure independently.

---

## 6. THE STANDING INVITATIONS

**On the dispositions-after-sequencing (CD-D-127/CD-D-130): the sequencing is CORRECT, and I say so having been the party disadvantaged by it.** I was asked to judge eleven items whose dispositions do not exist, and that genuinely cost me — T8 is one of my weakest sections. But the alternative is worse in a specific, demonstrable way: **this audit's single most valuable result (T6) came from disbelieving a disposition the record had already settled.** Had the eleven arrived pre-dispositioned, the pull toward grading the disposition rather than the item would have been exactly the failure mode the fourth seat exists to avoid. Keep the sequencing.

**On the §D scoping and CD-D-105 (T3):** the ruling that constructors are subjects is sound and is now discharged in code. My challenge is not to that ruling but to §3's reach.

**On CD-PL-F93 and the four-deep pattern:** the disclosure was accurate and useful. I looked for the fifth instance as instructed and **found three** — F-A1 (the ruling's own "fails on arrival" is static-only for the member the ruling added), F-A3 (the PO's declared floor is printed, never asserted), F-A4 (a declared limit asserting a precondition the route does not need). **The pattern is not four deep. It is at least seven, and all three new ones are inside increment 5.**

---

## 7. WHAT I COULD NOT ESTABLISH

Said plainly, as required:

1. **T8, T9, T10** — delegated measurement had not returned when I closed the verdict. I hold no independent assessment of the eleven Class-2 items' substance, of the F15 blindness window's mechanism, or of CD-ENG-WO2R3-F10's current status. **These are gaps in my verdict, not in the record.**
2. **T2 in depth** — I confirmed the conforming-hostile-adapter admission and the `ESTABLISHED_HERE` containment claim, but did not trace a hostile `payload` to a published envelope or a dial score. The Product Owner's "spend your first hour here" is only partly discharged.
3. **Whether the eleven plants are collectively *sufficient*** for their criteria — I measured whether each fails where its proposition says, not whether the set is complete.
4. **`check_lockfile_denylist.py`'s deny-by-default layer is exercised by no plant** — a `continue` at lines 606-637 skips Layer 1 after a Layer 2 hit. Correct design, but the layer the check advertises as "NEITHER LAYER IS SOLE" has no plant behind it.
5. I did not attempt to defeat the `@admits` doors themselves beyond the corpus.

---

## 8. GRADING

**CD-AC-002 — AMBER. WO-2R3 does not close it.**
The structural defences are real and I verified several: the absent door (no `contribution_model` attribute exists to name), the closed envelope schema, the AST blend scan, and the constructor refusals. The register text is honest — it names what each layer does *not* do, having been burned once when an auditor blended past all three declared layers. **What blocks a PASS:** the criterion's subject types (`DialSet`, `EquityCrashScore`, `MonetaryDebasementScore`) are in neither the PO's declared floor nor RULE A; they leave the measured class when a door changes, with the instrument reporting PASS (F-A3); the type-layer plant is green for the wrong reason; and a fielded judgement type with no establishment passes everything if placed outside the reach (F-A2).

**CD-AC-005 — AMBER, and weaker than CD-AC-002.**
`Agrees` genuinely requires `FreshnessEvidence` and the constructor refuses `None` — a real, runtime-verified closure, and the staleness ceiling is derived rather than chosen. **What blocks a PASS:** the criterion's own words are *"There must be no input whatever — missing, stale, malformed or defaulted — from which the serving layer produces AGREES"*, and I produced one (F-A4) that renders `WITNESS AGREES`; the plant meets F12 only partially, with 10 of 12 failures at a layer its manifest row does not name and the row's stated mechanism falsified; and the same reach defect applies to `Agrees`/`Diverges`/`Unavailable`, none of which are RULE A.

**Neither grade is a criticism of the mechanism.** `establishes` is a genuine closure, it is derived from the declaration, it survives the rename test, it has a working counterfactual arm, and it was built and measured before the mechanism existed. **The gap between what it closes and what the acceptance criteria claim is a gap in the definition of the class, and that is the Product Owner's to rule on — which is why the widening question came here and not to me first.**

**A last word on the seat's own limits.** The Project Lead asked for a route nobody had written down rather than a confirmation. I believe F-A1, F-A2, F-A3 and the T6 correction are that. But three of my eleven targets are unmeasured, and I would rather the Product Owner disposition an AMBER with four holes I have named than a PASS with four holes I have not.

---

**Verdict summary for the record:** SHA `531c95c2c42df51e24d4ce9cdb1f8a0d1818f5c0`, tree fingerprint `69b1fef83741d6d0ca14723a2df6ffeeb8efac3ab01195158ce65f22e2dcba5f` unchanged start to end, porcelain zero, target unmutated. **AMBER.** CD-AC-002 AMBER, CD-AC-005 AMBER. This verdict is **not an acceptance** (PBG-AUTH-003) — the Product Owner dispositions.
