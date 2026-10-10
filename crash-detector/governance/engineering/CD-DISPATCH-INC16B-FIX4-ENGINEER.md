# CD-DISPATCH-INC16B-FIX4-ENGINEER

**role source:** `pbg/roles/engineer.md` — reading it does not grant the role (`PBG-BOOT-001`),
**this dispatch does**.
**authority record:** `CD-ASR-WO3-08`'s `AMBER` at `3174753` (`BL-20260824T134814Z-A308.yaml`,
branch `asr-wo3-08-verdict`), findings **F1** and **F2** · F1 reproduced by the Project Lead ·
`PO-DECISIONS-0026` rulings 9 and 10
**seat identity:** `CD-ENG-WO3-09` — **FRESH.** **Never `CD-ENG-WO3-08` (which built what you are
repairing)**, **never `CD-ASR-WO3-08` (which found F1 — `PBG-SOD-004`)**, never
`CD-ENG-WO3-01`…`-07`, never `CD-ASR-WO3-01`…`-07`.
**issued by:** `PROJECT_LEAD_SEAT_02` · **increment:** 16B-FIX-4 · **expected return:**
`READY_FOR_ASSURANCE`

---

## 0. STOP PATCHING SPELLINGS. THIS ONE IS A CLASS FIX AND THE PROJECT LEAD HAS RULED IT.

**Read the count before you read anything else.** `_dial_bearing`'s root-property recogniser has now
been escaped **four times**, each time by a different *spelling* of the same idea:

```
A306  a NEW STATE VOCABULARY        (state const/enum not intersecting DECLARED_STATES)
A307  state as a BOOLEAN SCHEMA     (the undecidable limb sat inside isinstance(state, dict))
A308  patternProperties · dependentSchemas · $dynamicRef · a chain past _resolve's depth cap
```

*** **EACH FIX CLOSED THE SPELLING IT WAS SHOWN AND THE NEXT AUDITOR FOUND ANOTHER. THAT IS THE
CENSUS GAME `PO-DECISIONS-0026` RULING 10 FORBIDS IN TERMS, AND THIS DISPATCH WILL NOT PLAY A FIFTH
ROUND OF IT.** ***

**PROJECT LEAD RULING — INVERT THE DEFAULT AT THE ROOT-PROPERTY RECOGNISER, EXACTLY AS IT WAS
ALREADY INVERTED AT THE BRANCH RECOGNISER AND AT THE RESOLVER.** The medicine that has held
everywhere it was applied is the same medicine, and it has not been applied here.

---

## 1. THE LANE

```
branch    wo-3
worktree  /srv/crash-detector-wo3
tip       4d797e6  (16B-FIX-3 — assured AMBER at 3174753, banked, NOT accepted; content tip 3c44843)
base      be0b355  (FROZEN — READ-ONLY)
verdict   3174753 on branch asr-wo3-08-verdict — BL-20260824T134814Z-A308.yaml — READ IT IN FULL
```

**WRITABLE SCOPE:** `tools/register/check_missing_data_never_calm.py` ·
`contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md` · `required-tests.yaml` (`CD-AC-001`
block only) · `plants/WO3-INC16B/**` (**adding** arms; C1–C21 untouched) ·
`governance/engineering/build-log/**` for your own return.

**PROTECTED — ZERO PATHS, PROVED BY COMMAND:** `pbg/**` · `BLUEPRINT.md` · `PID.md` ·
`governance/decisions/**` · `governance/mapping/**` · **both envelope schemas** · `src/**` ·
`tests/**` · `deploy/**` · `db/**` · `tools/**` except your one file · `evidence/**` · `be0b355`.

---

## 2. FX12 — THE CLASS FIX: A ROOT PROPERTY YOU CANNOT FULLY READ IS UNDECIDABLE, NOT "NOT A DIAL"

`_dial_bearing` decides *"is this root property a dial?"* by looking at `resolved.get("properties")`
**and only that**. Anything that declares its `state` some other legal way is classified **not a
dial** and is **silent**.

**REPRODUCED BY THE PROJECT LEAD, `patternProperties` spelling, on its own plant:**

```
instrument                  PASS — 144 assertions, 0 violations
live gate, PUBLIC           *** ADMITTED — a DEAD FEED rendering as CALM ***
live gate, PRIVATE          *** ADMITTED ***
```

**And the auditor's arm `FINAL` is the one that decides the programme: 16C landed HONESTLY —
closed, `required`, allowlist paid, `_envelope` skeleton edited — gives a GREEN instrument and an
ADMITTED `calm`.** Its control, with `state` under `properties`, is `FAIL — 2`. **So the only thing
standing between 16C and a published dead-feed-as-calm is which keyword the author reaches for.**

**BUILD — and the shape is ruled, not optional:** `_dial_bearing` must return **UNDECIDABLE** for
any root property whose shape it **cannot fully read with its declared keyword set** — not `False`.
*"I could not decide what this property is"* and *"this property is not a dial"* are different
answers and only one of them is safe. Concretely, at minimum: an object schema declaring
`patternProperties`, `dependentSchemas`, `$dynamicRef`, or **any applicator the recogniser does not
itself descend**, is UNDECIDABLE; and **`_resolve` hitting its depth cap must be UNDECIDABLE, never
a clean `resolved` with `dropped == []`** — the auditor measured that cap returning an unresolved
`$ref` node as though it had resolved it, which is a silent lie in the resolver's own contract.

*** **THE TEST OF WHETHER YOU HAVE DONE THIS RIGHT IS NOT THAT THE FOUR NAMED SPELLINGS GO RED. IT
IS THAT A SPELLING NOBODY IN THIS CHAIN HAS THOUGHT OF GOES RED TOO, BECAUSE IT IS UNRECOGNISED
RATHER THAN BECAUSE IT IS ON A LIST. Build the arm that proves that — invent a fifth spelling none
of the four audits used, and show it fails.** ***

**Expect a false-positive tail and price it honestly** (`CD-RULE-004`). The Project Lead's standing
ruling holds: **a false positive costs one seat one look at one contract; a false negative costs the
constitution.** **If the inversion turns the CLEAN TREE red, STOP and say so** — that measurement
would change the ruling.

---

## 3. FX13 — F2: AN INTERNAL INCONSISTENCY THE FILE DOCUMENTS AGAINST ITSELF

The auditor found the file **documents the missing fail-closed limb** and names `dependentSchemas`
as an applicator in `CONDITIONAL_KEYWORDS` **while omitting it from `_SUBSCHEMA_KEYWORDS`.** **A
module that knows the answer in one constant and not in the other is one edit from the bug it just
described.** Reconcile the two, and say in the record which was wrong.

---

## 4. FX14 — THE FX9 SENTENCE IS ONE CLAUSE TOO WIDE

Your predecessor's justification for deny-by-default was **graded CORRECT by the auditor and the
Project Lead's ordered remedy was graded WRONG — that stands and is on the record.** But the
sentence carrying it claims a merge *"can admit documents NEITHER schema admits"*, and the auditor
measured **0 hits and showed it is provably impossible** (every keyword that wins a collision
survives into the merge). **The true claim is that a merge can admit documents the node as written
REFUSES — which is enough, and which was measured 10 times over six keyword sets in both merge
directions.**

**Correct it by supersession in all three `CD-RULE-004` places.** *** **THIS IS THE THIRD
REPLACEMENT SENTENCE ON THIS ROW TO BE FALSE IN THE SAME WAY AS THE SENTENCE IT REPLACED. WRITE THIS
ONE LAST, AFTER FX12 IS MEASURED, AND MAKE IT DESCRIBE WHAT YOU MEASURED — NOT WHAT YOU INTENDED,
AND NOT WHAT WOULD SOUND STRONGER.** ***

---

## 5. YOUR CONTRAST SET

Under `plants/WO3-INC16B/`, **C1–C21 untouched**, MANIFEST form with **`git apply`'s own exit code
as its own column**, every arm from its own pristine extraction (`CD-PL-F154`):

| # | Arm | Must |
|---|---|---|
| **C22** | `state` via `patternProperties` (auditor `F1`, PL-reproduced) | **FAIL** |
| **C23** | `state` via `dependentSchemas` | **FAIL** |
| **C24** | `state` via `$dynamicRef` | **FAIL** |
| **C25** | a `$ref` chain past `_resolve`'s depth cap | **FAIL** |
| **C26** | **auditor arm `FINAL` — 16C landed HONESTLY.** *This is the one that releases 16C* | **FAIL** |
| **C27** | **a FIFTH spelling none of the four audits used — your own invention** | **FAIL** |
| **C28** | *(CONTROL — MUST STILL PASS)* the symmetric fourth level (C10/C15/C21) | **PASS** |

**RE-RUN C1–C21 UNCHANGED.** `C10`/`C21` at `PASS — 158`, `C14` at `FAIL — 2`, `C18`/`C19` at
`FAIL — 32`, `C20` at `FAIL — 2`.

---

## 6. NOT IN THIS INCREMENT

**Do not implement 16C** and make **no schema edit of any kind**. Out: `CD-PL-F180` / the
contract-bytes route and **exit 3** (settled by four auditors) · `DECLARED LIMIT 12`'s
differently-named discriminator (**judged honestly drawn; a condition on 16C's dispatch**) ·
`REF_INERT_SIBLINGS` (**the auditor proved it a provably empty attack class — all eight annotations
pass and none is in `Draft202012Validator.VALIDATORS`; do not touch it**) · `STALENESS_WINDOW_CEILING_SECONDS`
(16C) · no-blend, host-coupling, version (16D) · registering any indicator row (16E) · `pbg/`.

---

## 7. YOUR RETURN

**BOOT FIRST**; the inherited `RED` (blob `ce0803c3`, eight seats) is the frozen base's —
**diagnose, do not repair.**

1. **C22–C27 each FAILING** with violation codes — **C26 and C27 called out explicitly.**
2. **C28 PASSING**; **C1–C21 re-run and unchanged.**
3. Clean tree exit **0**, assertion count, and **any false-positive tail measured and priced.**
4. `pytest tests/ -q` — no regression from **2007**; `test_detail_level.py` still **52**.
5. Register `MATCHES` · **18** · `GATE: SHUT` · `latest_admitted_run (null)`.
6. **What "cannot fully read" means in your implementation, stated precisely** — and why it is
   deny-by-default rather than a list.
7. FX13 reconciled, saying which constant was wrong. FX14 superseded in all three places, **written
   last**.
8. Scope proof by command; **ONE identity**, `git log --format='%an' 4d797e6..HEAD | sort -u`.
9. **Your declared limits**, including any new one. 10. **Your findings against this dispatch.**

**Commit identity — `git -c user.name=` DOES NOT WORK on this host:**
```
GIT_AUTHOR_NAME=CD-ENG-WO3-09 GIT_AUTHOR_EMAIL=cd-eng-wo3-09@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ENG-WO3-09 GIT_COMMITTER_EMAIL=cd-eng-wo3-09@seats.crash-detector.invalid \
git commit -m "..."
```

**COMMIT AT EVERY BOUNDARY** (`PBG-CONT-007`). **YOU DO NOT CERTIFY YOUR OWN WORK.**

**STOP AND RETURN if:** the inversion turns the clean tree or any existing arm red · you cannot make
`C27` fail without a list · **or you find any statement in this dispatch to be false.** *** **NINE
CONSECUTIVE DISPATCHES ON THIS LANE HAVE CONTAINED A FALSE STATEMENT A SEAT CAUGHT, AND THE LAST ONE
AIMED ITS PRIMARY ATTACK AT A PROVABLY EMPTY CLASS. ASSUME THIS ONE DOES TOO. If the falsehood does
not touch what you must build, continue and say so — `CD-PL-F192` is precedent.** ***
