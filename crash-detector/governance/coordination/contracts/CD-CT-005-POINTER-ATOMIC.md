# EXECUTION CONTRACT — `CD-CT-005-POINTER-ATOMIC`

> **This is place 2 of the three `CD-RULE-004` requires.** Place 1 is the limit block the
> instrument prints AFTER its verdict from a `finally`, on every exit path. Place 3 is the row in
> `governance/coordination/required-tests.yaml`. **THE THREE MUST AGREE. A REGISTER ENTRY MAY NOT
> CLAIM MORE THAN ITS GUARD DELIVERS**, and two prior seats on this project were found short
> exactly here.

| | |
|---|---|
| **delivers** | CD-PL-F132's real fix — the pointer moves in the same commit as the entry it names |
| **instrument** | `tools/coordination/check_build_log_pointer_atomic.py` |
| **invocation** | `python3 -B tools/coordination/check_build_log_pointer_atomic.py --rev <sha>` |
| **plant** | NONE AS A MUTATION PLANT. **ITS CONTRAST IS THE BACKWARD SWEEP ITSELF — see the contract §4.** |
| **closes its class?** | **NO.** It declares its limit — `CD-RULE-004` option 2. |
| **arms** | see section 4 |
| **last run** | see section 4 |

## 1. WHY THIS CONTROL EXISTS

`CD-PL-F111` -> `CD-PL-F112` -> `CD-PL-F132` is ONE discipline that lived only in a seat's
attention, was declared structurally fixed, held eight boundaries and failed at the ninth. Five
consecutive commits booted `RESUME_BLOCKED` and **a cold agent could not start this project from
its own tip.** `PO-DECISIONS-0021` ruling 4, adopting the meta-auditor's phrase: ***A PREDICTION
IS NOT A CARRIER.***

## 2. THE DECLARED LIMIT — VERBATIM, AND IT MUST MATCH THE OTHER TWO PLACES

> DECIDES POINTER_NOT_MOVED, POINTER_DANGLING and POINTER_STALE. DOES NOT DECIDE whether the entry the pointer names is the RIGHT one; DOES NOT DECIDE the other two continuity pointer fields; DOES NOT DECIDE SCHEMA validity — `5f09627`, one of the five RESUME_BLOCKED commits, is NOT caught by this instrument and that is stated rather than hidden.

## 3. THE RESIDUE (`CD-RULE-006`)

> AUTOMATIC INVOCATION IS NOT PROVED TO BE CARRIED ANYWHERE. The detector that would catch this (`pbg`'s continuity.active_work_currency()) EXISTS and the gate that runs on every commit EXISTS, both inside `pbg/`, AND THEY ARE NOT CONNECTED. No seat may connect them (PBG-FWK-013). Q11.

**A residue declaration must name a layer MEASURED to hold it, or be written "NOT PROVED TO BE
CARRIED ANYWHERE". A declaration that misdirects an auditor to a layer that does not hold is
worse than no declaration, because it spends the auditor's attention somewhere the defect is not.**

## 4. WHY THE CONTRAST IS THE HISTORY AND NOT A PATCH — AND THE ONE IT MISSES

The backward sweep over 208 commits at `main` and 204 at `e6f9802` contains BOTH conforming and
violating commits, so the instrument is shown to DISTINGUISH them on data nobody constructed.
That is a stronger contrast than a mutation patch, not a weaker one.

**AND IT MISSES ONE OF THE FIVE COMMITS THE RECORD NAMES.** `5f09627` booted `RESUME_BLOCKED` and
this instrument does NOT flag it, because its failure was a SCHEMA violation
(`continuity_record_commit: PENDING_CD_RULE_007_FOLLOW_UP` against a `^([0-9a-f]{7,40}|PENDING)$`
rule — `CD-PL-F148`), which this instrument declares it does not decide. **FOUR OF FIVE IS WHAT IS
CLAIMED. `pbg boot` is the layer that catches the fifth, and that hand-off is MEASURED — the boot
verdict at `5f09627` is in the record — not asserted.**

**A FIRST DRAFT OF THIS INSTRUMENT CHECKED ONLY `POINTER_NOT_MOVED` AND `POINTER_DANGLING` AND
MISSED THREE OF THE FIVE.** It would have shipped a green-looking near-miss. `POINTER_STALE` was
added because the backward run over real history disagreed with the record, and that disagreement
was the finding.

## 5. MEASURED AT `e6f9802` (this seat's dispatched baseline)

> 93 applications, 9 violating commits, failing positions [30, 76, 85, 90, 91, 92]. The record's four positions 76/85/90/91 reproduced exactly; two more found.

Producing command is printed by the instrument beside every count (`CD-RULE-009`).
