# EXECUTION CONTRACT — `CD-CT-009-LEASE-HELD-AT-WRITE`

> **This is place 2 of the three `CD-RULE-004` requires.** Place 1 is the limit block the
> instrument prints AFTER its verdict from a `finally`, on every exit path. Place 3 is the row in
> `governance/coordination/required-tests.yaml`. **THE THREE MUST AGREE. A REGISTER ENTRY MAY NOT
> CLAIM MORE THAN ITS GUARD DELIVERS**, and two prior seats on this project were found short
> exactly here.

| | |
|---|---|
| **delivers** | PO-DECISIONS-0021 ruling 3(d) — **THE HAND HALF, AND IT LANDS HALF-CARRIED BY CONSTRUCTION** |
| **instrument** | `tools/coordination/check_lease_held.py` |
| **invocation** | `python3 -B tools/coordination/check_lease_held.py --staged` |
| **plant** | NONE, AND A PLANT WOULD BE DISHONEST HERE. See the contract §4 and the declaration below. |
| **closes its class?** | **NO.** It declares its limit — `CD-RULE-004` option 2. |
| **arms** | see section 4 |
| **last run** | see section 4 |

## 1. WHY THIS CONTROL EXISTS

Ruling 3(d) requires the lease to bind *"the driver AND the PO's own hand"*. The driver half is
`CD-CT-008` and it is real machinery. **THIS ROW IS THE HAND HALF AND IT IS NOT CARRIED.**

## 2. THE DECLARED LIMIT — VERBATIM, AND IT MUST MATCH THE OTHER TWO PLACES

> DECIDES whether every governed path in a staged set or commit range is inside the write scope of a LIVE lease held by the named identity. *** IT IS NOT INVOKED BY ANYTHING. ***

## 3. THE RESIDUE (`CD-RULE-006`)

> *** **NOT PROVED TO BE CARRIED ANYWHERE.** *** Those are the required words and they are the honest answer. `git config core.hooksPath` is `pbg/tools/hooks`; that hook's entire staged-path filter is `grep '^governance/authority/'`; `pbg/` is pinned read-only to every seat (PBG-FWK-013), so extending it would be editing the framework to make a control pass, which is a bypass and not a fix. Q11 / Q12. **THIS ROW MUST NOT BE READ AS A BINDING.**

**A residue declaration must name a layer MEASURED to hold it, or be written "NOT PROVED TO BE
CARRIED ANYWHERE". A declaration that misdirects an auditor to a layer that does not hold is
worse than no declaration, because it spends the auditor's attention somewhere the defect is not.**

## 4. WHY A PLANT HERE WOULD BE DISHONEST

A plant would show this check refusing an uncovered write and admitting a covered one, and both
arms would pass. **AND IT WOULD PROVE NOTHING THAT MATTERS**, because the proposition ruling 3(d)
asks about is not *"can this check tell the difference"* — it plainly can — but *"is a governed
write actually prevented"*. It is not. Nothing invokes this file.

**A GREEN PLANT ATTACHED TO AN UNINVOKED CHECK IS EXACTLY THE ARTEFACT THAT MAKES A GAP INVISIBLE.**
`CD-PL-F132`'s own record contains the worked example: a comment reading *"MOVED IN THE SAME
COMMIT ... FOURTH CONSECUTIVE BOUNDARY"* sitting on a line whose VALUE was stale. **THE CONFESSION
AND THE DEFECT WERE IN THE SAME LINE, AND THE CONFESSION IS WHAT MADE THE DEFECT INVISIBLE.**

So this row carries no plant, and it carries the words `CD-RULE-006` requires instead.
