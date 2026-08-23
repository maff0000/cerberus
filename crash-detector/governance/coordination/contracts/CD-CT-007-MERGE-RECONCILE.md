# EXECUTION CONTRACT — `CD-CT-007-MERGE-RECONCILE`

> **This is place 2 of the three `CD-RULE-004` requires.** Place 1 is the limit block the
> instrument prints AFTER its verdict from a `finally`, on every exit path. Place 3 is the row in
> `governance/coordination/required-tests.yaml`. **THE THREE MUST AGREE. A REGISTER ENTRY MAY NOT
> CLAIM MORE THAN ITS GUARD DELIVERS**, and two prior seats on this project were found short
> exactly here.

| | |
|---|---|
| **delivers** | PO-DECISIONS-0021 ruling 3(c) — the merge step asserts no two seats touched the same artefact |
| **instrument** | `tools/coordination/merge_reconcile.py` |
| **invocation** | `python3 -B tools/coordination/merge_reconcile.py --base <sha> --claim T [--claim T] --emit` |
| **plant** | `governance/coordination/plants/PLANT-COORD-03.run.sh` |
| **closes its class?** | **NO.** It declares its limit — `CD-RULE-004` option 2. |
| **arms** | 3 |
| **last run** | LIVE — 3/3 arms contrasted |

## 1. WHY THIS CONTROL EXISTS

Ruling 3(c) requires a merge step that *"asserts no two seats touched the same artefact"*.
`CD-D-174` puts increment 12 on its own branch precisely so that this instrument gets its first
real test on its own increment — and records in advance that **if the Engineer's own merge
instrument refuses its own merge, that is a RESULT and not an embarrassment.**

## 2. THE DECLARED LIMIT — VERBATIM, AND IT MUST MATCH THE OTHER TWO PLACES

> MEASURES PATHS, NOT BYTES. OVER-REFUSES two seats editing disjoint REGIONS of one file. DOES NOT CATCH the same bytes written THROUGH an undeclared path — a symlink, a generated file, a .gitignore'd artefact. DOES NOT PERFORM THE MERGE AND CANNOT PREVENT ONE.

## 3. THE RESIDUE (`CD-RULE-006`)

> BYTE-LEVEL and OUT-OF-INDEX collision is NOT PROVED TO BE CARRIED ANYWHERE. The over-refusal on same-path edits is the only thing standing where that control would be, and it is blunt by design.

**A residue declaration must name a layer MEASURED to hold it, or be written "NOT PROVED TO BE
CARRIED ANYWHERE". A declaration that misdirects an auditor to a layer that does not hold is
worse than no declaration, because it spends the auditor's attention somewhere the defect is not.**

## 4. HOW TO EXECUTE THE CONTRAST

1. Two seat branches that both touched one file -> non-zero, naming the artefact and both seats.
2. `git apply` the mutation dropping the intersection assertion -> the merge is ADMITTED, then
   PERFORM the merge and show WHICH seat's work was lost.
3. Two branches with disjoint touched-path sets -> exit 0, then PERFORM the merge and verify BOTH
   seats' changes are present in the result. **VERIFY THE RESULT, NOT THE EXIT CODE.**

**A PLANT THAT PASSES BOTH ARMS IS DEAD AND IS WORSE THAN NO PLANT.** If an arm will not
contrast, the runner prints `*** DID NOT CONTRAST ***` and the plant verdict is
`NOT A CONTRAST`. It does not quietly report success.
