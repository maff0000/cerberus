# EXECUTION CONTRACT — `CD-CT-001-WORK-CLAIM-ATOMIC`

> **This is place 2 of the three `CD-RULE-004` requires.** Place 1 is the limit block the
> instrument prints AFTER its verdict from a `finally`, on every exit path. Place 3 is the row in
> `governance/coordination/required-tests.yaml`. **THE THREE MUST AGREE. A REGISTER ENTRY MAY NOT
> CLAIM MORE THAN ITS GUARD DELIVERS**, and two prior seats on this project were found short
> exactly here.

| | |
|---|---|
| **delivers** | PO-DECISIONS-0021 ruling 3(a) — two seats can never take the same work |
| **instrument** | `tools/coordination/claim.py` |
| **supporting** | `tools/coordination/registry.py`, `tools/coordination/liveness.py` |
| **invocation** | `python3 -B tools/coordination/claim.py claim --task T --seat S --write-scope G` |
| **plant** | `governance/coordination/plants/PLANT-COORD-01.run.sh` |
| **closes its class?** | **NO.** It declares its limit — `CD-RULE-004` option 2. |
| **arms** | 3 |
| **last run** | LIVE — 3/3 arms contrasted |

## 1. WHY THIS CONTROL EXISTS

`PO-DECISIONS-0021` ruling 2 names the cause of the day this increment answers: *"I dispatched
PO-DECISIONS-0020 (wo2r3n) while PO-DECISIONS-0019 (wo2r3m) was still alive, BOTH pointed at the
WO-2R3 lane and the same increment stream. **The record survived only because git's index lock
serialised the writes.**"* A record that survives by an accident of `.git/index.lock` has no
control on it at all. This row is the control.

## 2. THE DECLARED LIMIT — VERBATIM, AND IT MUST MATCH THE OTHER TWO PLACES

> DECIDES mutual exclusion on a TASK ID by O_EXCL create, MEASURED atomic at 6400 concurrent attempts / 200 rounds / 0 double-takes on this filesystem. DOES NOT DECIDE whether two DIFFERENT task ids name the same work; DOES NOT DECIDE work done with no claim at all; DOES NOT DECIDE a claim file edited by hand; REFUSES rather than proceeds on a network filesystem.

## 3. THE RESIDUE (`CD-RULE-006`)

> TASK-ID SYNONYMY is NOT PROVED TO BE CARRIED ANYWHERE. The scope-overlap refusal is a PARTIAL carrier and that partiality is measured (PLANT-COORD-02 arm 1), not assumed.

**A residue declaration must name a layer MEASURED to hold it, or be written "NOT PROVED TO BE
CARRIED ANYWHERE". A declaration that misdirects an auditor to a layer that does not hold is
worse than no declaration, because it spends the auditor's attention somewhere the defect is not.**

## 4. HOW TO EXECUTE THE CONTRAST

1. Take a claim, then try to take it again as a different seat. The second must exit non-zero and
   NAME the holder, its PID and its claim time.
2. `git apply` the mutation patch and repeat: BOTH takes now succeed and the registry retains ONE
   file. Read it back — the surviving `seat_actor_id` is one seat, and the other believes it holds
   the task.
3. Revert, then take two claims on DIFFERENT tasks concurrently. **BOTH MUST SUCCEED AND BOTH MUST
   BE LIVE AT ONCE.** If this arm refuses, the item has banned concurrency and FAILED.

**A PLANT THAT PASSES BOTH ARMS IS DEAD AND IS WORSE THAN NO PLANT.** If an arm will not
contrast, the runner prints `*** DID NOT CONTRAST ***` and the plant verdict is
`NOT A CONTRAST`. It does not quietly report success.
