# CD-DISPATCH-INC14-ASSURANCE

**role source:** `pbg/roles/assurance-engineer.md` · **seat identity:** `CD-ASR-WO3-01` — **FRESH,
AND NEVER `CD-ENG-WO3-01`.** The Engineer and the Assurance Engineer are never the same agent
(`PBG-SOD-001`, **non-waivable**).
**authority record:** `PO-DECISIONS-0024` ruling 2 · boundary `BL-20260823T180244Z-0153`
**issued by:** `PROJECT_LEAD_SEAT_01` · **expected return:** `PASS` / `AMBER` / `RED` **with the next
safe gate.**

---

## 1. THE TARGET — EXACT

| | |
|---|---|
| **subject SHA** | `9b09d2a5524743003febedabec3d461d9bc1a470` |
| **branch / worktree** | `wo-3` · `/srv/crash-detector-wo3` |
| **base** | `be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5` (**FROZEN — read-only to you too**) |
| **the claim under audit** | *"The Required Test Register now VALIDATES and COMPUTES A STATUS for all 18 criteria, where before it computed none — and NOTHING ELSE CHANGED."* |
| **runtime** | `PYTHONPATH=/srv/crash-detector/pbg/tools python3 -B -m pbg.cli required-tests verify --register required-tests.yaml` |

**EXTRACT THE SUBJECT YOURSELF: `git archive 9b09d2a \| tar -x -C <your own tmpdir>`.** Do not audit
the Engineer's working tree and **do not verify through any harness this project wrote** — verifying
through the project's own harness is verifying the harness (`PBG-ASSURE-001`).

---

## 2. MUTATION IS PROHIBITED

**You write nothing** except explicitly safe diagnostic artefacts under your own `/tmp` scratch
directory. **No commits. No branch moves. No edits to the lane, to `main`, to `pbg/`, or to any
governance file.** If you believe something must change, **that is a finding, not an act.**

---

## 3. WHAT TO GRADE

1. **Does the register validate, and does it compute 18 statuses?** Run it. Record verbatim.
2. **Is the gate honestly SHUT?** It must read `GATE: SHUT` / `PID_ACCEPTANCE_SATISFIED: NOT
   DERIVED`, and every status `UNDECIDABLE`. **`UNDECIDABLE` IS NOT A PASS. If the gate reads
   anything else, that is a RED and the most serious possible finding on this project.**
3. **`latest_admitted_run` MUST still be `null`.** The Engineer must not have admitted its own
   evidence (`PBG-SOD-001`).
4. **Was any pre-existing register content altered?** Compare the base and tip registers
   **semantically** (parse both; do not eyeball a diff — a last-wins duplicate YAML key is invisible
   in a diff and is the exact hazard here). `violation` prose, `evidence_ref`, `execution_contract`
   on every pre-existing test.
5. **Was the plant evidence preserved?** All six `planted_violation` / `planted_violation_note`
   values from `be0b355`. **Strip comment markers before comparing** — the Project Lead's first run
   of this check reported a false loss by counting `#` as words, and that error is recorded at
   `BL-...-0153` so you do not repeat it.
6. **Are the contrast arms non-vacuous?** Re-apply both patches under `plants/WO3-INC14/` in your
   own extractions. **CONTRAST 1 must collapse 18 statuses to 0. CONTRAST 2 must produce
   `MISMATCH`.** A plant that does not discriminate is not evidence.
7. **Containment:** one identity, porcelain empty, `pbg/` / `src/` / `tests/` / `BLUEPRINT.md` /
   `governance/decisions/` untouched, `wo-2r3` still at `be0b355`, `PID.md` byte-identical to
   `main`'s.
8. **NO SOURCE REGISTERED — not one row, not a placeholder, NOT A FIXTURE** (`Q25` is held for
   Matt). Check `raw.source_registry` and the register for smuggled content.
9. **`CD-AC-002` still AMBER-and-not-closed, `CD-AC-005` still RED.** Neither may have moved.

---

## 4. GRADE THE PROJECT LEAD TOO, NOT ONLY THE ENGINEER

`BL-20260823T180244Z-0153` records that **two of the Project Lead's own dispatch prescriptions were
wrong** (`CD-PL-F160`, `CD-PL-F161`) and that `CD-PL-F158` stands unedited and false, superseded
rather than rewritten. **AUDIT THAT HANDLING.**

- **Is `CD-PL-F160`'s correction itself correct?** Measure the three sites at `be0b355` yourself.
- **Was `PBG-CONT-003` honoured — superseded, never edited?** Check that `BL-...-0152` was not
  altered after the fact: `git log -p --follow` the file, or diff it against its committed form.
- **Is the Engineer's `F03` residual (the two unresolvable execution contracts) honestly carried
  rather than quietly closed?**

**IF THE PROJECT LEAD'S RECORD OVERSTATES WHAT WAS MEASURED, SAY SO. THAT IS THE FINDING THIS
PROJECT VALUES MOST, AND ITS RECORD SHOWS SEATS HAVE FOUND IT BEFORE.**

---

## 5. RETURN

`PASS` / `AMBER` / `RED`, **with the next safe gate named**, and with:

- every command you ran and **what it actually printed**
- your findings, each with severity and the measurement behind it
- **anything you could NOT verify, stated as unverified rather than assumed**

**Do not grade on the Project Lead's summary or the Engineer's return. Grade on what you run.**
