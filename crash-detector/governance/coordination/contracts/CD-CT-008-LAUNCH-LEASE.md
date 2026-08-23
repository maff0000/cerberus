# EXECUTION CONTRACT — `CD-CT-008-LAUNCH-LEASE`

> **This is place 2 of the three `CD-RULE-004` requires.** Place 1 is the limit block the
> instrument prints AFTER its verdict from a `finally`, on every exit path. Place 3 is the row in
> `governance/coordination/required-tests.yaml`. **THE THREE MUST AGREE. A REGISTER ENTRY MAY NOT
> CLAIM MORE THAN ITS GUARD DELIVERS**, and two prior seats on this project were found short
> exactly here.

| | |
|---|---|
| **delivers** | PO-DECISIONS-0021 ruling 3(d) — the driver half |
| **instrument** | `tools/coordination/lease.py` |
| **supporting** | `tools/coordination/launch.sh`, `tools/coordination/liveness.py` |
| **invocation** | `sh tools/coordination/launch.sh --lease L --seat S --task T --write-scope G -- COMMAND` |
| **plant** | `governance/coordination/plants/PLANT-COORD-04.run.sh` |
| **closes its class?** | **NO.** It declares its limit — `CD-RULE-004` option 2. |
| **arms** | 3 |
| **last run** | LIVE — 3/3 arms contrasted |

## 1. WHY THIS CONTROL EXISTS

Ruling 3(d). The lease must refuse an overlapping launch AND **admit a disjoint one, concurrently,
with the other lease still live and undisturbed. A LEASE THAT SERIALISES IS A FAILED ITEM.**

## 2. THE DECLARED LIMIT — VERBATIM, AND IT MUST MATCH THE OTHER TWO PLACES

> REFUSES task overlap, write/write overlap and write/read overlap against a LIVE lease, and launch.sh REFUSES TO exec — the non-start is PROVED by a sentinel, not inferred from an exit code. ADMITS the disjoint launch concurrently, which is an EQUAL requirement. DOES NOT DECIDE a launcher that never asks for a lease.

## 3. THE RESIDUE (`CD-RULE-006`)

> BINDING THE LAUNCHER is NOT PROVED TO BE CARRIED ANYWHERE for any launch that does not go through launch.sh. **THE OPERATOR'S WRAPPER IS NOT IN THIS REPOSITORY** and no seat and no framework in this tree can reach it.

**A residue declaration must name a layer MEASURED to hold it, or be written "NOT PROVED TO BE
CARRIED ANYWHERE". A declaration that misdirects an auditor to a layer that does not hold is
worse than no declaration, because it spends the auditor's attention somewhere the defect is not.**

## 4. HOW TO EXECUTE THE CONTRAST

1. Start a seat through `launch.sh`; attempt an overlapping launch. Non-zero, **AND the second
   seat's sentinel file must NOT exist** — the non-start is proved positively.
2. `git apply` the always-dead liveness mutation; the same overlapping launch is ADMITTED **while
   `kill -0` confirms the first session is still alive.**
3. A disjoint second launch starts, runs alongside, and `lease.py list` shows **TWO leases reading
   LIVE at the same moment.**

**A PLANT THAT PASSES BOTH ARMS IS DEAD AND IS WORSE THAN NO PLANT.** If an arm will not
contrast, the runner prints `*** DID NOT CONTRAST ***` and the plant verdict is
`NOT A CONTRAST`. It does not quietly report success.
