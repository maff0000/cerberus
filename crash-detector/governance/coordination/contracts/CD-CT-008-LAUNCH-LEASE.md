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

> REFUSES task overlap, write/write overlap and write/read overlap against a LIVE lease, **UNDER CONCURRENCY** — the collision read and the O_EXCL take run inside ONE lease-directory critical section, because O_EXCL alone excludes on the LEASE ID exactly as it excludes on the TASK ID in `claim.py`. `launch.sh` REFUSES TO exec — the non-start is PROVED by a sentinel, not inferred from an exit code. **CARRIES THE DECLARED SCOPE TO `lease.py` WITHOUT CORRUPTING IT**: pathname expansion is disabled for the whole script (`set -f`), the scope arguments are carried in the positional parameter list rather than a string, there is no `eval`, and `lease.py` ECHOES the scope it actually RECEIVED at every acquisition. **BOUNDS BUT DOES NOT AUTHENTICATE `--pid`**: it DERIVES that the named pid is in the acquiring process's own session (`os.getsid`), which refuses `--pid 1`; a long-lived SIBLING pid in the caller's own session would still pass and that residue is NOT CLOSED. ADMITS the disjoint launch concurrently, which is an EQUAL requirement. DOES NOT DECIDE a launcher that never asks for a lease. DOES NOT DECIDE a scope entry whose prefix traverses a SYMLINK, and does not refuse a bare existing-directory literal — `claim.py` does both and `lease.py` does neither, and that asymmetry is DECLARED, not fixed at this increment.

### 2b. THE CARRIER USED TO CORRUPT ITS OWN INPUT — `CD-ASR-WO2R3-06-F05`, COMPOUNDED BY `F11`

`launch.sh` accumulated the scope arguments into a STRING and expanded it UNQUOTED, which in POSIX
`sh` performs FIELD SPLITTING **and PATHNAME EXPANSION**. **A WRITE SCOPE IS A GLOB.** Two regimes,
both wrong: a glob matching 2+ real paths became extra argv words and an argparse error printed to
the operator as `LEASE REFUSED (rc=2)`, indistinguishable from a genuine collision — **commissioning
that carrier would have refused every real launch and told the operator there was a conflict**; and
a glob matching EXACTLY ONE real path was **SILENTLY NARROWED**, so a seat typing `docs/alpha/*` got
a lease recording `docs/alpha/only.md`, a second seat acquired `docs/alpha/other.md`, and BOTH
SUCCEEDED. **SAME REQUEST, OPPOSITE VERDICTS, AND THE ONLY VARIABLE WAS WHETHER THE SCOPE PASSED
THROUGH `launch.sh`.**

**`PLANT-COORD-04` COULD NOT SEE ANY OF IT.** It exercised exactly two scope forms — a LITERAL with
no glob, and a glob matching NOTHING on disk — **THE ONLY TWO FORMS THAT CANNOT TRIGGER THE
DEFECT** — and was 3/3 LIVE over a deliverable broken for every glob matching a real path.
`PLANT-COORD-07` exists because of that, and exercises a glob matching >=2 real paths AND a glob
matching exactly 1, **with `cwd` inside the sandbox, because pathname expansion is relative to the
working directory and a plant that launches from elsewhere measures nothing.**

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
