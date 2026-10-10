# EXECUTION CONTRACT — `CD-CT-003-LIVE-SCOPE-DISJOINT`

> **This is place 2 of the three `CD-RULE-004` requires.** Place 1 is the limit block the
> instrument prints AFTER its verdict from a `finally`, on every exit path. Place 3 is the row in
> `governance/coordination/required-tests.yaml`. **THE THREE MUST AGREE. A REGISTER ENTRY MAY NOT
> CLAIM MORE THAN ITS GUARD DELIVERS**, and two prior seats on this project were found short
> exactly here.

| | |
|---|---|
| **delivers** | PO-DECISIONS-0021 ruling 3(b) + CD-PL-F134 (write against a live reader's READ scope) |
| **instrument** | `tools/coordination/check_scope_disjoint.py` |
| **invocation** | `python3 -B tools/coordination/check_scope_disjoint.py` |
| **plant** | `governance/coordination/plants/PLANT-COORD-02.run.sh` |
| **closes its class?** | **NO.** It declares its limit — `CD-RULE-004` option 2. |
| **arms** | 4 |
| **last run** | LIVE — 4/4 arms contrasted (shares PLANT-COORD-02 with CD-CT-002) |

## 1. WHY THIS CONTROL EXISTS

`CD-PL-F134`: *"`main` ADVANCED `d0d13f8` -> `baede05` WHILE `CD-ASR-WO2R3-05` WAS LIVE ... BUT
`governance/` ON `main` IS THE SEAT'S OWN READING MATERIAL, AND IT CHANGED UNDER IT. ... THE HARM
WAS ZERO AND THE DISCIPLINE WAS STILL BROKEN. The remedy is not 'remember'."* **A write-vs-write
check would have passed that incident cleanly.** The two seats were not writing the same file.

## 2. THE DECLARED LIMIT — VERBATIM, AND IT MUST MATCH THE OTHER TWO PLACES

> DECIDES pairwise WRITE x WRITE, and WRITE x READ in BOTH directions, over EVERY pair of DISTINCT live claim records **AT ANY IDENTITY, INCLUDING TWO CLAIMS HELD BY ONE SEAT ID**. DELIBERATELY DOES NOT REFUSE READ x READ at any identity (two seats reading one file is the normal case, and refusing it would ban parallel audits — the vacuity ruling 3 rejects). DELIBERATELY DOES NOT REFUSE ONE claim record's own write scope against its OWN read scope — a SINGLE-RECORD exemption, because the pair loop never compares a record with itself. DELIBERATELY ADMITS one seat holding two or more DISJOINT live claims. DOES NOT DECIDE what a seat actually TOUCHED — it reads DECLARATIONS. DOES NOT DECIDE whether two live claim records are two SESSIONS or one, and after the F08 correction it does not need to. **IT IS NOT INVOKED BY ANYTHING (Q11).**

### 2b. WHY THIS ROW USED TO BE FALSE — `CD-ASR-WO2R3-06-F08` AND `CD-RULE-004`

Increment 12's `L1` said the instrument decides WRITE x WRITE disjointness *"over all live claims"*.
**IT DID NOT.** It decided it over CROSS-SEAT live claims and skipped the rest, in four lines that
were declared NOWHERE — not in `L1`-`L6`, not in this contract, not in `required-tests.yaml`. That
is `GUARD_THE_INSTANCE_NOT_THE_CLASS` at the exact centre of the remedy, and it is two defects and
not one: the code defect, and the FALSE CLAIM ABOUT the code.

**AND THE INSTANCE IT GUARDED EXCLUDED THE FOUNDING INCIDENT.** *"TWO PROJECT LEAD SESSIONS ALIVE
SIMULTANEOUSLY ON `main`, BOTH WITH COMMIT AUTHORITY, **BOTH COMMITTING AS
`PROJECT_LEAD_SEAT_01`**, NEITHER AWARE OF THE OTHER"* (`VERDICT-META-ASSURANCE-01-SECOND-SEAT`
§1.1). One identity. **THE INSTRUMENT BUILT TO DETECT THE INCIDENT PRINTED `CONCURRENT WORK
PROCEEDS` FOR THE INCIDENT, AND EXITED 0.** `PO-DECISIONS-0022` ruling 5: *"the control must FLAG
two live claims on one scope regardless of identity"*, and ruling 3 binds the Product Authority's
own hand with no exemption, because the incident was the Product Owner's own breach of it.

**THE TWO EXEMPTIONS THAT SURVIVED ARE NOT IDENTITY EXEMPTIONS AND NEVER WERE.** `READ x READ` is a
PAIRING exemption. A record's own write-vs-own-read is a SINGLE-RECORD exemption. Deleting the skip
indiscriminately would have taken neither with it, and `PLANT-COORD-05` arm 4 measures both still
admitting.

**A DESIGN CALL IS DECLARED HERE RATHER THAN LEFT IMPLICIT:** a seat legitimately holding two
DISJOINT claims is still ADMITTED. Refusing all same-identity multi-claim was available and was NOT
taken, because it narrows what the machinery permits. `PLANT-COORD-05` arm 3 proves the disjoint
same-identity pair still proceeds.

## 3. THE RESIDUE (`CD-RULE-006`)

> The gap between a DECLARED scope and a TOUCHED path is carried by merge_reconcile.py assertion (1) CONTAINMENT, MEASURED by PLANT-COORD-03. The gap between a LIVE ACTOR and a CLAIM is carried by launch.sh for launches that go through it, and for every other route it is NOT PROVED TO BE CARRIED ANYWHERE.

**A residue declaration must name a layer MEASURED to hold it, or be written "NOT PROVED TO BE
CARRIED ANYWHERE". A declaration that misdirects an auditor to a layer that does not hold is
worse than no declaration, because it spends the auditor's attention somewhere the defect is not.**

## 4. HOW TO EXECUTE THE CONTRAST

1. Two live claims with overlapping WRITE scopes -> non-zero, both seats and the path named.
2. Mutated algebra -> admitted.
3. Disjoint pair -> exit 0. **AND the asymmetric pair — seat A writes `ACTIVE_WORK.yaml` while
   seat B declared `governance/engineering/**` as its READ scope — MUST BE REFUSED even though the
   write-vs-write pair is disjoint.**

**A PLANT THAT PASSES BOTH ARMS IS DEAD AND IS WORSE THAN NO PLANT.** If an arm will not
contrast, the runner prints `*** DID NOT CONTRAST ***` and the plant verdict is
`NOT A CONTRAST`. It does not quietly report success.
