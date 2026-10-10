# CD-ASR-WO3-01 — ASSURANCE VERDICT ON INCREMENT 14

**seat:** `CD-ASR-WO3-01` (fresh identity; **NOT** `CD-ENG-WO3-01` — `PBG-SOD-001`, non-waivable)
**target:** `9b09d2a5524743003febedabec3d461d9bc1a470` · branch `wo-3` · base `be0b355` (frozen)
**dispatch:** `governance/engineering/CD-DISPATCH-INC14-ASSURANCE.md`
**persisted by:** `PROJECT_LEAD_SEAT_01` at `BL-20260823T181502Z-0154`

> **WHY THE PROJECT LEAD IS WRITING THIS FILE AND NOT THE AUDITOR.** The Assurance dispatch
> prohibited **all** governance writes; `pbg/roles/assurance-engineer.md` requires the seat to
> persist its verdict (`PBG-CONT-007`). **The seat obeyed the dispatch, declared the conflict as its
> own limitation, and returned the verdict unpersisted.** That was the correct call — **a read-only
> seat that starts writing governance files to satisfy a continuity rule has stopped being
> read-only.** Persisting it is the Project Lead's obligation and is discharged here.
> **`CD-PL-F163` is raised against the dispatch for creating the conflict.**

---

## VERDICT: **`PASS`** — scoped

**confidence:** HIGH on the artefact · MEDIUM on one Project-Lead self-disclosure it could not reach.

**method:** its own `git archive` extractions of **both** tip and base. **The Engineer's worktree was
never read as the subject.** No project-written harness was used for any conclusion
(`PBG-ASSURE-001`). **Mutation: NONE** — all writes under its own `/tmp`; it even used
`--no-optional-locks` so as not to take an index lock.

---

## THE CONTROL THAT MAKES THE HEADLINE MEAN ANYTHING

**The seat first proved the INSTRUMENT is identical at base, tip and `main`:**

```
git rev-parse 9b09d2a:pbg be0b355:pbg main:pbg
  -> e4ee93cbd87329683678bb1403ec76c8346ded73   (all three, identical tree)
sha256sum required_tests.py (main, tip, base)
  -> 51db6180…  (x3)
```

> **THIS IS THE CHECK NOBODY ASKED FOR AND IT IS THE ONE THAT MAKES `0 -> 18` A FACT RATHER THAN A
> CLAIM: the result CANNOT be an artefact of a changed verifier.** Neither the Engineer's return nor
> the Project Lead's reconciliation established this. **The auditor did.**

---

## WHAT IT MEASURED

| Check | Result |
|---|---|
| Register validates and computes | **base 0 statuses -> tip 18.** Verbatim output captured for both. |
| Gate | **`GATE: SHUT` · `PID_ACCEPTANCE_SATISFIED: NOT DERIVED` · every row `UNDECIDABLE` · exit 2.** |
| `latest_admitted_run` | **`null` at base AND tip, parsed not read.** `evidence/` **does not exist in the tip tree** — there are no fabricated run records to admit. |
| **Duplicate-key scan** | **0 duplicates in both files**, using a `SafeLoader` subclass that traps repeated keys **before** last-wins resolution. **The `CD-PL-F158` hazard did not land.** |
| Pre-existing content | rows 16 -> 18; added `CD-AC-017`/`CD-AC-018`; removed none; **criterion-level diffs on pre-existing rows: 0**; the three changed tests differ **only** by removal of the two surplus keys. `violation` 4292/30522/12152 **IDENTICAL** at all three. `superseded_by` unchanged everywhere, so **no row was hidden from evaluation by supersession**. |
| Plant evidence | **6/6 preserved word-identical**, comment markers stripped. It did not repeat the Project Lead's `#`-as-word error. |
| Contrast 1 | apply 0 · **validation FAILED · 18 -> 0 computed** · `(not comparable)` |
| Contrast 2 | apply 0 · validation passes · 18 computed · **`MISMATCH`**, with the defect line confirmed **genuinely emitted, not composed** |
| Containment | one identity · porcelain 0 · `wo-2r3` **still `be0b355`** · `PID.md` **cmp exit 0 vs `main`** · whole-tree recursive compare: `db` `src` `tests` `contracts` `tools` `variants` `docs` `deploy` `BLUEPRINT.md` **ALL IDENTICAL**; `governance/` differs by **exactly one file**; `plants/` by **exactly one directory** |
| **No source registered** | `db/` byte-identical to base · **no `INSERT INTO raw.source_registry` anywhere** · every `SourceRecord(...)` occurrence is in `tests/`/`variants/`, both byte-identical to base. **Not one row, not a placeholder, not a fixture. `Q25` INTACT.** |
| `CD-AC-002` / `CD-AC-005` | **NEITHER MOVED.** |

### The counterfactual it ran that was not asked for

It flipped `CD-AC-017` to `NEW_REQUIREMENT` in a throwaway extraction: **gate still `SHUT`.**

> **SO THE `DERIVES` CHOICE BUYS THE ENGINEER NOTHING AT THE GATE.** That is the check that
> distinguishes "the Engineer chose the relation the instrument computes" from "the Engineer chose
> the relation that helps it." **It chose correctly and gained nothing by it.**

---

## IT GRADED THE PROJECT LEAD, AND THE PROJECT LEAD'S CORRECTIONS SURVIVED

- **`CD-PL-F160` INDEPENDENTLY CONFIRMED.** It measured the three sites at `be0b355` itself and got
  exactly `4292 / 30522 / 12152` and exactly the key list. **`CD-PL-F158` was false; `CD-PL-F160` is
  true.**
- **`CD-PL-F161` CONFIRMED** by reading the pinned source (`required_tests.py:659-663`).
- **`CD-PL-F162` CONFIRMED:** census 17, register 18, base 16.
- **`PBG-CONT-003` HONOURED — MEASURED, NOT ASSUMED:** `git log --follow --numstat` on
  `BL-...-0152.yaml` -> **ONE commit only, `4ba110f`, 188 insertions / 0 deletions, no subsequent
  commits, clean working tree.** **`CD-PL-F158` stands on the record unedited and wrong, exactly as
  claimed. No rewrite occurred.**
- **The Engineer's `F03` residual is honestly carried, not closed** — and it **probed the substance**
  by writing the two missing contract stubs into a throwaway tree: statuses unchanged, gate still
  `SHUT`. **F03's substance holds.**

---

## ITS FINDINGS — THREE, ALL `LOW`, ALL AGAINST THE RECORD'S PRECISION, NONE AGAINST THE ARTEFACT

**`CD-ASR-WO3-01-F01` (LOW)** — *"it masks nothing today"* is very slightly too strong **and the
attributed cause is not the printed one.** `BL-...-0153` says the 18 are `UNDECIDABLE` *"for the
`latest_admitted_run` reason anyway"*. **Measured: the printed cause for `CD-AC-001`-`016` is
`negative_control.evidence_ref … does not resolve`, and for `017`/`018` it is `execution_contract …
does not resolve`.** The contract miss `continue`s, so it **does** suppress one diagnostic line per
row. **The status is identical either way — it proved that by probe — so the consequence is nil, but
"masks nothing" masks a message.** **ADOPTED.**

**`CD-ASR-WO3-01-F02` (LOW) — THE SHARPEST FINDING IN THE RETURN.** There are **THREE** defective
test sites producing **SIX** schema errors. `CD-PL-F158` and dispatch §2 both say *"the six defective
sites"* and order *"three obligations at each of the six sites"*. **`CD-PL-F160` quotes that phrase
and answers with "all three defective tests" — correcting the count BY USAGE without ever raising it
as the second error in `F158`.** *** **ON A PROJECT WHOSE RULE IS THAT CORRECTIONS SUPERSEDE RATHER
THAN REWRITE, A SUPERSEDING ROW MUST NAME *BOTH* ERRORS IT CORRECTS, NOT ONE — OTHERWISE THE
CORRECTION IS ITSELF A QUIET EDIT.** *** **A cold reader of the still-standing dispatch would count
six sites.** **ADOPTED IN FULL — carried as `CD-PL-F164`.**

**`CD-ASR-WO3-01-F03` (LOW, framework, NOT this lane)** — `NEW_REQUIREMENT` on a criterion that **is**
in the census **double-reports it**: `required_tests.py:675` emits a report for the census member,
then `:708` emits a second for the register-only branch; `CD-AC-017` appeared **twice** and the
mandatory count read 18 for 17 criteria. **A PINNED-FRAMEWORK WART. It argues FOR the `DERIVES`
choice. It belongs in the PBG defect queue as a separate bounded dispatch and MUST NOT be folded
into lane work (`PBG-FWK-013`).**

---

## WHAT IT DECLARED UNVERIFIED RATHER THAN ASSUMED

1. **The Project Lead's self-disclosed retracted first run** of the preservation check (*"reported 3
   LOST and was wrong"*). **No artefact of it exists.** It confirmed the *corrected* result
   independently. *** **"THE DISCLOSURE IS CREDIBLE AND UNREFUTED, BUT IT IS NOT VERIFIABLE — IT
   RESTS ON THE SEAT'S OWN HONESTY. THAT IS THE CORRECT PLACE FOR IT TO REST; I RECORD THAT IT IS
   NOT EVIDENCE."** *** **THE PROJECT LEAD ADOPTS THAT SENTENCE WITHOUT SOFTENING IT.**
2. **`CD-PL-F160`'s account of *how* the error was made** (the `sed` window landing inside a block
   scalar) is *"a plausible reconstruction I cannot confirm."* Its **conclusion** was measured.
3. **The `PBG-CONT-007` conflict** described at the top of this file.

---

## SCOPE QUALIFICATION IT VOLUNTEERED

*"Nothing else changed"* is **true** of the register's pre-existing content, `pbg/`, `src/`, `tests/`,
`contracts/`, `db/`, `tools/`, `variants/`, `docs/`, `deploy/`, `BLUEPRINT.md`,
`governance/decisions/`, the `wo-2r3` ref and the source set. **It is NOT literally true of the
tree**, which also gained `PID.md` (a carriage, cmp exit 0 — not an edit), `plants/WO3-INC14/`, and
one Engineer build-log entry. **All are dispatched deliverables within writable scope.** It stated
this *"so the claim is not read wider than it was measured."*

**NOT EXAMINED:** the substance of any `violation` prose or `acceptance_semantics`; whether
`CD-AC-017`/`018` are the right criteria (reserved to the PO); any runtime, service or database;
increments 15-18.

---

## NEXT SAFE GATE (the seat's own words)

> **Project Lead reconciles and persists this verdict at a boundary naming `9b09d2a`, then dispatches
> increment 15 (publication layer) per `PO-DECISIONS-0024` ruling 2.**

**Carried forward, unclosed:** increment 14 stays **BANKED AND NOT ACCEPTED — acceptance is Matt's
alone** · the two execution contracts owed at increments **17/18**, and **per its probe they become
the SOLE remaining cause on those rows the moment run records land** · **`Q28`** for the PO —
**`PID.md` is PO-authored and no seat may tidy it** · **`Q25` REMAINS HELD FOR MATT; no seat
inherits the source set** · the framework double-report as a separate bounded PBG dispatch.
