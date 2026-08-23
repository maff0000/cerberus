# EXECUTION CONTRACT — `CD-CT-006-NO-SHARED-RECORD-WRITE`

> **This is place 2 of the three `CD-RULE-004` requires.** Place 1 is the limit block the
> instrument prints AFTER its verdict from a `finally`, on every exit path. Place 3 is the row in
> `governance/coordination/required-tests.yaml`. **THE THREE MUST AGREE. A REGISTER ENTRY MAY NOT
> CLAIM MORE THAN ITS GUARD DELIVERS**, and two prior seats on this project were found short
> exactly here.

| | |
|---|---|
| **delivers** | PO-DECISIONS-0021 ruling 3(b) — no shared ACTIVE_WORK.yaml edit |
| **instrument** | `tools/coordination/check_no_shared_record_write.py` |
| **data** | `governance/coordination/ACCOUNTABLE-SEAT.yaml` |
| **invocation** | `python3 -B tools/coordination/check_no_shared_record_write.py --range A..B` |
| **plant** | NONE AS A SEPARATE RUNNER. Its PROSPECTIVE arm is exercised inside claim.py and is covered by PLANT-COORD-01's registry; its RETROSPECTIVE arm is run over real history. See the contract §4. |
| **closes its class?** | **NO.** It declares its limit — `CD-RULE-004` option 2. |
| **arms** | see section 4 |
| **last run** | see section 4 |

## 1. WHY THIS CONTROL EXISTS

Ruling 3(b): *"no shared ACTIVE_WORK.yaml edit"*. A prospective-only check is a promise a seat
makes about itself. The retrospective arm reads what actually landed and does not depend on the
seat having run anything.

## 2. THE DECLARED LIMIT — VERBATIM, AND IT MUST MATCH THE OTHER TWO PLACES

> DECIDES a NON-ACCOUNTABLE seat writing a shared record file, prospectively and retrospectively. **DOES NOT DECIDE TWO CONCURRENT SESSIONS OF THE SAME ACCOUNTABLE SEAT** — CD-RULE-002 gives one identity to a ROLE, so two live Project Leads are indistinguishable from one in `git log`.

## 3. THE RESIDUE (`CD-RULE-006`)

> TWO CONCURRENT ACCOUNTABLE SESSIONS IS **NOT PROVED TO BE CARRIED ANYWHERE**. This is VERDICT-META-ASSURANCE-01-SECOND-SEAT.md §7.2, which names it the true root cause of the day's breaches. Amending CD-RULE-002 to a per-session identity is Product Owner work.

**A residue declaration must name a layer MEASURED to hold it, or be written "NOT PROVED TO BE
CARRIED ANYWHERE". A declaration that misdirects an auditor to a layer that does not hold is
worse than no declaration, because it spends the auditor's attention somewhere the defect is not.**

## 4. WHY THERE IS NO SEPARATE RUNNER — DECLARED, NOT OMITTED

The PROSPECTIVE arm is called by `claim.py` before every take, so `PLANT-COORD-01`'s registry
exercises it on every run. The RETROSPECTIVE arm is exercised over the project's real history.
**A DEDICATED THIRD RUNNER WOULD ADD A CONSTRUCTED CONTRAST TO TWO THAT ALREADY EXIST. THAT IS AN
ARGUMENT AND NOT A PROOF, AND IT IS RECORDED AS THE WEAKER THING.**
