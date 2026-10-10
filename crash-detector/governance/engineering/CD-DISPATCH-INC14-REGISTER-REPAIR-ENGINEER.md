# CD-DISPATCH-INC14-REGISTER-REPAIR-ENGINEER

**role source:** `pbg/roles/engineer.md` (canonical local file — read it; reading it does not grant
the role, this dispatch does: `PBG-BOOT-001`/`PBG-BOOT-002`)
**authority record:** `governance/decisions/PO-DECISIONS-0024.md` rulings 1 (`Q24`, the base) and
2 (`Q27`, increment 14 proceeds) · scope `governance/engineering/WO-3-SCOPE.md` §3 Group D
**seat identity:** `CD-ENG-WO3-01` — **A FRESH IDENTITY, never `CD-ENG-WO2R3-01`…`-09`, never
`CD-ENG-COORD-01`, never `CD-ENG-COORD-FIX-01`**
**issued by:** `PROJECT_LEAD_SEAT_01` · **increment:** 14 · **expected return:** `READY_FOR_ASSURANCE`

---

## 0. THE BASE, AND WHAT IS READ-ONLY ABOUT IT

`PO-DECISIONS-0024` ruling 1 settles `Q24`: **WO-3 branches FROM the frozen `be0b355`.** The gate's
shutness governs **ACCEPTANCE** of `CD-AC-002`/`CD-AC-005`, **not branching**. A lane frozen for
audit is an **immutable BASE**, not a prohibition on building forward.

The lane is **cut already** and you do not cut it:

```
branch    wo-3          (cut from be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5)
worktree  /srv/crash-detector-wo3
```

> **`be0b355` ITSELF IS READ-ONLY TO YOU AND SO IS `wo-2r3`.** You build forward from the base; you
> do not amend it, rebase it, force it, cherry-pick onto it, or move the `wo-2r3` ref. Verify at the
> end that `git rev-parse wo-2r3` is still `be0b355…` and **report the measurement, not the
> intention.**

---

## 1. WHAT THIS INCREMENT IS, AND WHY IT IS NOT COSMETIC

The Required Test Register (`required-tests.yaml`) **has never been a valid input.** Six schema
errors cause validation to fail, and validation failing means **NO STATUS IS COMPUTED FOR ANY
CRITERION.** The register has been carried through ten gates **returning nothing at all.**

**MEASURED BY THE PROJECT LEAD AT THIS BOUNDARY, in a pristine `git archive be0b355` extraction with
the very PID the register pins present at the path it names — so it is not an artefact of
extraction:**

```
VALIDATION FAILED — the register is not a valid input; no status is computed:
  ! criteria[1] (CD-AC-002).tests[3].negative_control: unknown field: planted_violation
  ! criteria[1] (CD-AC-002).tests[3].negative_control: unknown field: planted_violation_note
  ! criteria[3] (CD-AC-005).tests[2].negative_control: unknown field: planted_violation
  ! criteria[3] (CD-AC-005).tests[2].negative_control: unknown field: planted_violation_note
  ! criteria[3] (CD-AC-005).tests[3].negative_control: unknown field: planted_violation
  ! criteria[3] (CD-AC-005).tests[3].negative_control: unknown field: planted_violation_note

GATE: SHUT
PID_ACCEPTANCE_SATISFIED: NOT DERIVED
```

The contract allows exactly `{"violation", "evidence_ref"}` under `negative_control`
(`pbg/tools/pbg/required_tests.py:82`, `_ALLOWED_NEGATIVE_CONTROL`).

---

## 2. *** THE REPAIR IS NOT A RENAME. READ THIS TWICE. ***

**A seat that does `sed s/planted_violation/violation/` will make the validator go quiet and will
have destroyed the register's meaning.** The Project Lead inspected both forms before writing this:

- **The CONFORMING form** (e.g. `required-tests.yaml:166`, `:224`): `violation:` is **PROSE
  DESCRIBING THE CLASS OF VIOLATION** the negative control must catch — *"A dial magnitude whose
  provenance is not the declared contribution model applied to inputs that were present…"*
- **The SIX DEFECTIVE sites**: they carry **NO `violation:` PROSE AT ALL.** They carry
  `planted_violation:` — **a PATCH PATH** (`plants/CD-AC-002/CD-RT-002-EXACT-TYPE-ADMISSION.patch`)
  — and `planted_violation_note:` — prose about **that specific plant**, not about the violation
  class.

**SO THE SIX SITES ARE MISSING A REQUIRED THING AND CARRYING TWO THINGS THE CONTRACT HAS NO HOME
FOR.** The repair is therefore three obligations at each of the six sites, and **all three or the
site is not repaired**:

1. **WRITE the `violation:` prose** — the CLASS of violation, in the register's established
   voice, at the same altitude as the conforming sites. **Derive it from the plant's own semantics
   and from the criterion's `acceptance_semantics`; do not invent a new obligation.**
2. **PRESERVE the patch path and the note. DO NOT DELETE THEM.** They are real recorded evidence of
   a measured 14-plant set. Relocate them, **byte-faithful in substance**, into a field the contract
   allows — `execution_contract` is prose and is allowed at test level (`_ALLOWED_TEST`). **A
   deletion here would destroy the record of the plant set to make an instrument go green, which is
   the exact act `PBG-FWK-013` and this project's whole record forbid.**
3. **KEEP `evidence_ref`** as it stands (`RTR-WO2-0001`).

> **IF YOU CONCLUDE THAT PRESERVING THE PLANT PATH INSIDE `execution_contract` IS THE WRONG HOME,
> SAY SO AND PROPOSE THE RIGHT ONE — DO NOT SILENTLY DROP IT AND DO NOT EDIT `pbg/` TO ADD A FIELD.**
> Widening the contract to fit the data is a bypass (`PBG-FWK-013`); `pbg/` is pinned and read-only.

---

## 3. THE DELIVERABLES

### D0 · **CARRY THE LIVE PID ONTO THE LANE — VERBATIM, AND THIS IS A CARRIAGE, NOT AN AMENDMENT**

**THE PROJECT LEAD FOUND THIS AT THIS BOUNDARY AND IT IS NOT IN THE SCOPE DOCUMENT'S GROUP D.** It
is stated here rather than left for you to hit:

`required-tests.yaml` resolves `pid.ref: PID.md` **relative to the register's own directory** — i.e.
the lane's `PID.md`, which at `be0b355` is the **OLD** PID (`441d8316…`, census 16, **no
`CD-AC-017`**). Re-pinning `content_hash` to `538e30f3…` while the lane still carries the old file
would produce a **MISMATCH**, and adding a `CD-AC-017` row against a 16-criterion census would not
resolve. **D2, D3 AND D4 ARE ALL IMPOSSIBLE WITHOUT D0.**

- Carry `PID.md` from `main` onto the lane **byte-identical**: `git checkout main -- PID.md`.
- **VERIFY BY HASH, NOT BY EYE:** `sha256sum PID.md` **must** be
  `538e30f3bf4f1803a89a11ae7b3781febba3752aeb516914e80db6ed15f9621f`.
- **YOU DO NOT EDIT `PID.md`. NOT ONE BYTE.** It is Product-Owner-authored and protected from every
  seat (`CD-D-115`). This is a verbatim carriage of an existing PO act (PID v1.1.0,
  `PO-DECISIONS-0020` ruling 1) onto a lane that predates it — the established pattern on this
  project. If the hash does not match, **STOP AND REPORT**; do not reconcile it by hand.

**Known and deliberate:** `BLUEPRINT.md` also diverges between the lane and `main` (+296/−29,
measured). **IT IS OUT OF SCOPE FOR THIS INCREMENT** — the register reads the PID and does not read
the Blueprint. **Do not carry it. Do not touch it.** It is recorded here so that when you see the
divergence you know it was seen and left deliberately.

### D1 · **The six `negative_control` sites repaired per §2** so the register **validates at all**.

### D2 · **Re-pin `pid.content_hash`** to `sha256:538e30f3…`, **after D0 and D1.**

> **EXPECT `P3` TO SURFACE AND DO NOT RECORD IT AS A REGRESSION.** The stale pin was **always**
> there; it was **invisible** because `report.pid_ref` is only assigned during status derivation
> (`required_tests.py:611-612`), which the schema failure short-circuits before reaching. **The
> schema defect MASKED the pin defect. It is one defect surfacing, not a second one appearing.**
> Update the register's own comment at that field (it currently explains the hash as "PID.md as it
> stands at the WO-2 execution base 3f038665") so the file does not carry a stale explanation of a
> fresh value.

### D3 · **Add the `CD-AC-017` row** — `pid_relation: DERIVES`.

`CD-AC-017` **IS** in the live PID census (**measured by the Project Lead with the instrument's own
`derive_pid_census`, census size 17, `CD-AC-017 in census: True`**). It is therefore **`DERIVES`, NOT
`NEW_REQUIREMENT`** — the `NEW_REQUIREMENT` block ("blocked pending PO amendment of the PID",
`required_tests.py:708-715`) is **SPENT, because the amendment happened.**

### D4 · **Add the `CD-AC-018` register-only row** — `pid_relation: STRENGTHENS CD-AC-004`.

`CD-AC-018` is **correctly ABSENT** from the census — *"`CD-AC-018` GAINS NO ROW AND THE ABSENCE IS
THE RULING"* (`PO-DECISIONS-0020` ruling 1). **`CD-AC-004` IS in the census (measured), so the
`STRENGTHENS` trace resolves rather than dangling.**

**D3 and D4 take the register from 16 rows to 17 and CLOSE the `3/4 of the CD-D-172 form` carriage.**

> **BOTH ROWS DECLARE OBLIGATIONS THAT ARE NOT YET BUILT, AND THAT IS THE POINT.** `CD-AC-017`'s
> mechanism is increment 17; `CD-AC-018`'s is increment 18. Write the test rows that **will**
> evidence them with an execution contract stating plainly which increment owes them and that they
> are **NOT YET EVIDENCED**. The register's own header is the authority: *"a register that quietly
> dropped the criteria it could not yet satisfy would be marking its own paper."* **DO NOT write a
> row whose test you then make pass.**

### D5 · **Re-run the verifier and record WHAT IT COMPUTES — not what you assert.**

Run it from a **pristine extraction of your own tip**, not from your working tree:

```
git archive <your-tip> | tar -x -C /tmp/inc14-verify
cd /tmp/inc14-verify
PYTHONPATH=/srv/crash-detector/pbg/tools python3 -B -m pbg.cli required-tests verify --register required-tests.yaml
```

> *** **THE GATE WILL ALMOST CERTAINLY STILL READ `SHUT`, AND THAT IS A CORRECT OUTCOME OF THIS
> INCREMENT — NOT A FAILURE OF IT.** *** `latest_admitted_run` is `null` and **you cannot change
> that**: the Engineer does not admit its own evidence (`PBG-SOD-001`, non-waivable). The win here is
> that the register **COMPUTES A STATUS AT ALL** for the first time in its life. **DO NOT chase a
> green. DO NOT touch `latest_admitted_run`. A seat that made this gate open would be forging the
> thing the whole project exists to refuse.**

### D6 · **DIAGNOSE THE CO-LOCATION — the question the scope reported but deliberately did not answer**

**All six errors are in `CD-AC-002` and `CD-AC-005` — the exact two criteria the perimeter turns on
and the two grades every recent ruling has protected.** The scope recorded this and did **not**
investigate, because investigating was Engineer work on a frozen lane. **You are the Engineer and
the lane is no longer a blocker. Investigate it.**

Use `git log -L` / `git log -S 'planted_violation' -- required-tests.yaml` to find **which commit and
which increment introduced the defective form**, and report **causal or coincidence** with the
evidence. **If you cannot tell, say you cannot tell.** A confident answer here that is wrong is worse
than "I measured this much and it does not settle it."

---

## 4. PLANTS — CONTRAST FORM, AND BOTH ARMS OR IT IS VACUOUS

Your repair claims *"the register now validates and computes."* **PROVE IT THE WAY THIS PROJECT
PROVES THINGS: two arms, the tree the only variable, exit codes recorded as their own column, each
arm run from its own pristine `git archive` extraction.**

| Arm | Tree | Expected |
|---|---|---|
| **CLEAN** | your repaired tip | validation **passes**, statuses **computed**, 17 criteria reported |
| **CONTRAST** | your tip **+ a patch reintroducing ONE `planted_violation` field** | validation **FAILS**, **no status computed** |

**A one-armed measurement here would reproduce the exact vacuity this project has corrected four
times.** Record `git apply`'s **own exit code** as a third column (`CD-ENG-WO2R3-09`'s established
form). Add a **second** contrast if you can: a tip with the PID pin reverted to `441d8316…`, proving
the instrument **now reports the mismatch** it was previously unable to reach.

---

## 5. WRITABLE SCOPE — EXACT

**Repository:** `/srv/crash-detector` · **branch:** `wo-3` · **worktree:** `/srv/crash-detector-wo3`

**WRITABLE:**
- `required-tests.yaml`
- `PID.md` — **ONLY** as the verbatim `git checkout main -- PID.md` carriage of D0. No edits.
- `plants/` — new contrast patches for §4
- `governance/engineering/build-log/` — **your own entries only**
- a scratch dir under `/tmp` for extractions

**NOT WRITABLE — and each has a reason, not just a prohibition:**
- **`pbg/`** — pinned, read-only, non-waivable. Editing it to make a control pass is a bypass, not a
  fix (`PBG-FWK-013`).
- **`be0b355` / the `wo-2r3` ref** — the frozen base. Read-only per `PO-DECISIONS-0024` ruling 1.
- **`BLUEPRINT.md`, `PID.md` (as an edit), `governance/decisions/`** — Product-Owner-authored,
  protected from every seat including the Project Lead (`CD-D-115`).
- **`src/`, `tests/`** — **this increment changes NO product code.** If you believe it must, that is
  a finding to report, not a change to make.
- **`governance/engineering/ACTIVE_WORK.yaml`** — the Project Lead's file.

---

## 6. WHAT MUST NOT HAPPEN

1. **DO NOT MOVE `CD-AC-002` OR `CD-AC-005`.** `CD-AC-002` is **AMBER and NOT CLOSED**; `CD-AC-005`
   is **RED**. **You are repairing the INSTRUMENT THAT READS THEM, not the grades.** That the
   instrument was blind is **not** evidence the grades were wrong.
2. **DO NOT REGISTER A SOURCE.** Not one row, not a placeholder, **not a test fixture**
   (`CD-PL-F154` is what happens when a fixture escapes). The source set is **HELD FOR MATT**
   (`Q25`, `PO-DECISIONS-0024` ruling 4).
3. **DO NOT READ THE INDICATOR LIST OFF THE ARGUS `/playbook` PAGE.** The shape is inheritable; the
   list is not (`PBG-PID-003`).
4. **DO NOT OPEN THE GATE** (see D5).
5. **DO NOT DELETE THE PLANT EVIDENCE** (see §2).
6. **DO NOT REACH FOR THE COORDINATION DISCIPLINE.** It is **PARKED** and decoupled to the framework
   track. No WO-3 increment may quietly fix a coordination residual — that un-parks it by the back
   door (`WO-3-SCOPE` §5.8).
7. **NO PARALLEL SEAT** (`CD-D-181`). You are one seat, sequential.
8. **YOU DO NOT APPROVE YOUR OWN WORK.** A separate Assurance seat follows you (`PBG-SOD-001`,
   non-waivable).

---

## 7. IDENTITY AND COMMITS

Commit as your own seat identity. `git -c user.name=` **does not work in this environment** — use
the environment variables:

```
GIT_AUTHOR_NAME=CD-ENG-WO3-01 GIT_AUTHOR_EMAIL=cd-eng-wo3-01@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ENG-WO3-01 GIT_COMMITTER_EMAIL=cd-eng-wo3-01@seats.crash-detector.invalid \
git commit -m "[CD-ENG-WO3-01] …"
```

**ONE IDENTITY ON THIS LANE, START TO FINISH** (`CD-RULE-002`). Verify before you return:
`git log --format='%an' be0b355..HEAD | sort -u` → **exactly one name.**

---

## 8. RETURN

Return `READY_FOR_ASSURANCE` with:

- your **tip SHA**, and `git status --porcelain` (**must be empty**)
- the verifier's **verbatim output** at that tip, from a pristine extraction — **what it computed**
- the **plant table**, both arms, three columns, per §4
- **`sha256sum PID.md`** and **`git rev-parse wo-2r3`** as measurements
- your **D6 finding** — causal or coincidence, with the evidence, or an honest "does not settle it"
- **every finding you raise against your own work**, which on this project is expected and is the
  norm rather than a failing

**IF YOU CANNOT DO SOMETHING IN THIS DISPATCH, RETURN AND SAY SO. DO NOT IMPROVISE AROUND IT, AND DO
NOT WIDEN YOUR OWN SCOPE TO REACH IT.**
