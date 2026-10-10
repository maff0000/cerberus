# WO-3 INCREMENT 14 — THE CONTRAST PATCHES FOR THE REGISTER REPAIR

**Written by `CD-ENG-WO3-01`** under `governance/engineering/CD-DISPATCH-INC14-REGISTER-REPAIR-ENGINEER.md` §4.
**Nothing in this directory is evidence, and nothing in it is assurance.** The patches exist so that
the claim *"the register now validates and computes"* is measured by CONTRAST rather than asserted
from one side.

These patches do **not** touch product code. They mutate `required-tests.yaml` only. They are
**never applied to the worktree** — each arm below was run in its own throwaway `git archive`
extraction under `/tmp`, and the worktree was never mutated.

---

## THE ARMS, AS MEASURED AT TIP `7b7fafe1a67d2aca7c03c7c4ee9c262cbbe13687`

Each arm from **its own pristine `git archive 7b7fafe | tar -x` extraction**. `git apply`'s **own
exit code** is recorded as its own column, because *a patch that does not apply produces a
"violated" arm that is the clean tree* — this project's established form.

| Arm | Tree | `git apply` exit | validation | criteria with a COMPUTED STATUS | `pid.content_hash` |
|---|---|---|---|---|---|
| **CLEAN** | tip, unpatched | n/a (no patch) | **PASSES** | **18** | `MATCHES` |
| **CONTRAST 1** | tip + `CONTRAST-1-REINTRODUCE-ONE-PLANTED-VIOLATION.patch` | **0** | **FAILED** | **0** | `(not comparable)` |
| **CONTRAST 2** | tip + `CONTRAST-2-REVERT-PID-PIN-TO-STALE.patch` | **0** | **PASSES** | **18** | `MISMATCH` |

### *** THE VERIFIER'S EXIT CODE IS `2` IN ALL THREE ARMS AND THEREFORE DISCRIMINATES NOTHING HERE ***

**A table of exit codes alone would have been VACUOUS on this measurement**, and would have looked
exactly like a passing contrast. The gate is `SHUT` in every arm — correctly, because
`latest_admitted_run` is `null` in every arm and no seat may change that (`PBG-SOD-001`). The
DISCRIMINATING measurements are therefore stated as their own columns above:

* whether `VALIDATION FAILED` appears at all, and
* **how many criteria RECEIVED a computed status** — the number this increment exists to move off zero.

This is written down because the established three-column form was designed around checks whose
exit codes DO differ between arms, and it does not transfer to this instrument unexamined.

---

## `CONTRAST-1-REINTRODUCE-ONE-PLANTED-VIOLATION.patch`

**ONE LINE.** It un-comments a single preserved `planted_violation:` line at the `CD-AC-002`
`CD-RT-002-EXACT-TYPE-ADMISSION` site, making it a live key again under `negative_control`.

**WHAT IT PROVES:** the repair is LOAD-BEARING and not cosmetic. **ONE** unknown field collapses the
register from **18 criteria with a computed status to 0** — the whole document becomes an invalid
input and derivation is short-circuited before it starts. Verbatim, from the arm:

```
VALIDATION FAILED — the register is not a valid input; no status is computed:
  ! criteria[1] (CD-AC-002).tests[3].negative_control: unknown field: planted_violation
```

It also demonstrates the MASKING that `P3` described: with the schema broken, `pid.ref` reads
`(unresolved)` and `pid.content_hash` reads `(not comparable)` — **the instrument cannot reach the
pin comparison at all.**

## `CONTRAST-2-REVERT-PID-PIN-TO-STALE.patch`

**ONE LINE.** It reverts `pid.content_hash` to the stale `441d8316…`.

**WHAT IT PROVES:** the instrument **NOW REPORTS A MISMATCH IT WAS PREVIOUSLY UNABLE TO REACH.**
Before this increment the same defect was invisible; here it is named:

```
  pid.content_hash      MISMATCH

DEFECTS:
  ! pid.content_hash does not match the referenced PID — the register's population was derived from a different document than the one now governing
```

**Note the pairing with CONTRAST 1**, which is the point of running both: the stale pin is
*undetectable* while the schema is broken and *detected* once it is repaired. That is the masking
relationship measured from both sides rather than argued from one.

---

## WHAT THESE PATCHES DO NOT PROVE

* **NOTHING ABOUT ANY GRADE.** `CD-AC-002` is AMBER and not closed; `CD-AC-005` is RED. These arms
  measure an INSTRUMENT, not the criteria it reads. That the register was blind is not evidence any
  grade was wrong.
* **NOTHING ABOUT THE GATE.** The gate is SHUT in all three arms and this increment does not open
  it. `latest_admitted_run` is `null` and untouched.
* **NOTHING ABOUT `CD-AC-017` OR `CD-AC-018`.** Both rows are declared and NOT YET EVIDENCED; their
  mechanisms are owed by increments 17 and 18, and their execution contracts do not exist.
