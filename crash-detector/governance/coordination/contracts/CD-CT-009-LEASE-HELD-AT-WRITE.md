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
| **plant** | `governance/coordination/plants/PLANT-COORD-08.run.sh` — **THE `--range` HALF ONLY.** A plant over the CARRIAGE would still be dishonest: see §4. |
| **closes its class?** | **NO.** It declares its limit — `CD-RULE-004` option 2. |
| **arms** | see section 4 |
| **last run** | see section 4 |

## 1. WHY THIS CONTROL EXISTS

Ruling 3(d) requires the lease to bind *"the driver AND the PO's own hand"*. The driver half is
`CD-CT-008` and it is real machinery. **THIS ROW IS THE HAND HALF AND IT IS NOT CARRIED.**

## 2. THE DECLARED LIMIT — VERBATIM, AND IT MUST MATCH THE OTHER TWO PLACES

> DECIDES (`--staged`) whether every governed path in the STAGED set is inside the write scope of a lease held by the named identity and LIVE NOW. DECIDES (`--range`) whether every governed path of EVERY COMMIT in the range was inside the write scope of a lease held by that identity **AND LIVE AT THE TIME OF THAT COMMIT** — the lease's recorded interval (`acquired_utc` .. `released_utc`/`reaped_utc`) against that commit's committer timestamp, with BOTH EDGES STRICT. `--range` DOES NOT consult pid liveness, deliberately. **DOES NOT DECIDE WHETHER EITHER TIMESTAMP IS TRUE — BOTH ARE SELF-REPORTED.** REFUSES TO ANSWER rather than answering wrongly: an unreadable `acquired_utc` makes a lease cover NOTHING, and an unparseable commit timestamp aborts with `PRECONDITION_NOT_MET`. *** IT IS NOT INVOKED BY ANYTHING. ***

### 2b. THE MODE THE GRADED PARTY COULD FLIP — `CD-ASR-WO2R3-06-F09`

**THIS CONTRACT IS NAMED `LEASE-HELD-AT-WRITE` AND `--range` DID NOT MEASURE TIME-OF-WRITE AT ALL.**
It asked whether a lease is live at THIS INSTANT, which a lease acquired one second ago satisfies —
so the ninth Assurance seat took the same commits, the same history, nothing rewritten, and turned
**RED TO GREEN IN ONE COMMAND** as the party being graded. Two separable causes: `--range` grading
history against leases live now, and `lease.py --pid` being unauthenticated with `--pid 1` naming
`init`, which is always alive and made the lease IMMORTAL.

**AND THE OLD MODE WAS ALSO WRONG IN THE OTHER DIRECTION**: it required the WRITER'S PROCESS to
still be running, and the seat that made a historical write is normally dead by the time anyone
audits it.

**BOTH INTERVAL EDGES ARE STRICT, AND THAT IS MEASURED, NOT STYLISTIC.** `CD-RULE-005` mandates one
timestamp source, `date -u +%FT%TZ`, which is SECOND-GRANULAR — so a lease acquired in the same
second as a commit cannot be distinguished from one acquired retroactively. With an inclusive edge
the retro-flip **still captured 1 of 11 governed writes**. The ambiguous instant is decided AGAINST
the party being graded, and **THE COST IS DECLARED: an honest launch that commits inside the same
second as its own lease acquisition is REFUSED.**

**WHAT IS NOT CLOSED, AND IS RETURNED RATHER THAN PRETENDED:** full `--pid` authentication is
`CONTROL_NOT_SATISFIABLE` — a pid cannot be authenticated from userspace on this platform, so
`lease.py` DERIVES a session bound instead (`CD-RULE-003`, never a denylist) and every lease record
carries `pid_authenticated: false` in its own bytes. And neither timestamp withstands a party
willing to forge one. **NOT PROVED TO BE CARRIED ANYWHERE.**

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
