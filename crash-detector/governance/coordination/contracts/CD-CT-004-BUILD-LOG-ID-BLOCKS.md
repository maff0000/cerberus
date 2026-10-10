# EXECUTION CONTRACT — `CD-CT-004-BUILD-LOG-ID-BLOCKS`

> **This is place 2 of the three `CD-RULE-004` requires.** Place 1 is the limit block the
> instrument prints AFTER its verdict from a `finally`, on every exit path. Place 3 is the row in
> `governance/coordination/required-tests.yaml`. **THE THREE MUST AGREE. A REGISTER ENTRY MAY NOT
> CLAIM MORE THAN ITS GUARD DELIVERS**, and two prior seats on this project were found short
> exactly here.

| | |
|---|---|
| **delivers** | PO-DECISIONS-0021 ruling 3(b) — per-seat build-log id blocks, no shared sequence |
| **instrument** | `tools/coordination/check_build_log_blocks.py` |
| **data** | `governance/coordination/BUILD-LOG-ID-BLOCKS.yaml` |
| **invocation** | `python3 -B tools/coordination/check_build_log_blocks.py --table --entries --ref main --ref wo-2r3` |
| **plant** | NONE. **DECLARED, NOT OMITTED — see the contract §4.** |
| **closes its class?** | **NO.** It declares its limit — `CD-RULE-004` option 2. |
| **arms** | see section 4 |
| **last run** | see section 4 |

## 1. WHY THIS CONTROL EXISTS

Ruling 3(b) orders per-seat build-log id blocks and **no shared sequence**. The measurement at
`e6f9802` is that the project HAS a shared sequence and it has already collided: 15 duplicate id
numbers across `main` and `wo-2r3`, and one duplicate (`0136`) inside `main` alone.

## 2. THE DECLARED LIMIT — VERBATIM, AND IT MUST MATCH THE OTHER TWO PLACES

> DECIDES block-allocation overlap, out-of-block entries (author = git author of the ADDING commit), and duplicate id numbers. DOES NOT DECIDE cross-BRANCH collisions unless two --ref values are passed, and nothing runs the two-ref form automatically. DOES NOT RENUMBER, MOVE OR EDIT ANY ENTRY — it has no write path (PBG-CONT-003 is non-waivable).

## 3. THE RESIDUE (`CD-RULE-006`)

> AUTOMATIC INVOCATION IS NOT PROVED TO BE CARRIED ANYWHERE. Q11.

**A residue declaration must name a layer MEASURED to hold it, or be written "NOT PROVED TO BE
CARRIED ANYWHERE". A declaration that misdirects an auditor to a layer that does not hold is
worse than no declaration, because it spends the auditor's attention somewhere the defect is not.**

## 4. WHY THERE IS NO MUTATION PLANT FOR THIS ROW — DECLARED, NOT OMITTED

A mutation plant proves a control's refusal is load-bearing by removing the control and watching
the violation pass. **This instrument's refusal is already proved by real data**: run over
`main`+`wo-2r3` at `e6f9802` it exits 1 on 145 violations it did not construct, and run over its
own allocation table it exits 0. A mutation patch would add a constructed contrast to a control
that already has a measured one.

**THAT IS AN ARGUMENT, NOT A PROOF, AND IT IS RECORDED AS THE WEAKER THING.** An Assurance seat
that judges the plant owed should say so; this row would then be short of the standard and the
honest place to find that out is here rather than at a gate.

## 5. MEASURED AT `e6f9802` (this seat's dispatched baseline)

> table 0 violations; entries over main+wo-2r3: 145 violations (15 duplicate id, 40 out-of-block, 90 unallocated-author). NOT REPAIRED. DISCLOSED.

Producing command is printed by the instrument beside every count (`CD-RULE-009`).
