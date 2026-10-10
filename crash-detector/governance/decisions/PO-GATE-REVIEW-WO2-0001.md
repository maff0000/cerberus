# PRODUCT OWNER GATE REVIEW — WO-2, crash-detector

**Record type:** PRODUCT_AUTHORITY_DISPOSITION
**Transcribed by:** PROJECT_LEAD_SEAT_01 (the actor, not the grantor)
**Received:** 2026-08-19, at the WO-2 gate, HEAD `f041c6f`, lane `wo-2-skeleton` at `66681b2`
**Gate state at review:** NOT MET — Assurance CD-ASR-WO2-01 returned AMBER; four of five criteria
not PASS (`governance/assurance/WO-2/BL-ASR-WO2-01.yaml`)

This file transcribes a Product Authority disposition. The Project Lead does not resolve Product
Authority decisions (`PBG-AUTH-003`); it records them and executes them. Where the ruling leaves an
implementation choice open, that choice is named below as belonging to the Project Lead, and where
it does not, that is said too.

---

## RULING 1 — the refusal to admit the run record stands

The Project Lead's refusal to admit `RTR-WO2-0001` while four criteria stood not-PASS (CD-D-023) is
**correct and is commended**. `CD-FWK-005` is **harvested to the framework backlog as IMP-015
(HIGH)**.

**PROJECT RULE, effective immediately, to be recorded in project governance:**

1. No run record is admitted at any gate without the **paired assurance verdict attached**.
2. A criterion the **Assurance seat holds not-PASS cannot compute PASS**, regardless of what runs
   are admitted.

The Project Lead enforces this **procedurally** until the framework carries it natively.

→ Recorded as `CD-RULE-001` in `governance/rules/PROJECT-RULES.md`.

## RULING 2 — REWORK DISPATCH WO-2R: close the CLASS, not the instances

The auditor's theme on F01–F04 is `GUARD_THE_INSTANCE_NOT_THE_CLASS`. Ten of its twenty-four
variants escaped. WO-2R is ordered.

For **each** finding the rework must **state IN THE COMMIT what CLASS is being closed and by what
STRUCTURE**, then prove that closure against:

* the auditor's **escaped variants**, and
* **at least two new variants of the Engineer's own**.

Per finding, as ruled:

| Finding | Sev | Criterion | Ruling |
|---|---|---|---|
| **F01** | HIGH | CD-AC-002 | A working blend defeats all three layers. The closure must make **any scalar derived from both dial types unrepresentable/unpublishable as a class** — not ban known spellings. |
| **F02** | HIGH | CD-AC-001 | `Unknown.magnitude -> 0.0` defeats both guards. **Absence must be structurally incapable of yielding a numeric attribute.** Consider closing the Reading types against attribute addition **entirely** — the frozen-or-slotted invariant from the framework's own kernel lesson. |
| **F03** | MED | CD-AC-001 | Numeric default via a module-level constant — **same class as F02's; close together.** |
| **F04** | MED | CD-AC-012 | IP-literal egress passes the allowlist. The check must resolve what an entry **REACHES**, not what it is **spelled** as. **Must be closed BEFORE any WO-3 egress lane inherits it.** |
| **F05** | MED | CD-AC-003 | The code-graph guard's walk root must derive from the **CONTAINER'S OWN entrypoint set**, not a hard-coded path. |
| **F06** | MED | CD-AC-005 | Staleness windows get a **hard upper bound**. A decade-old row must be **structurally incapable** of rendering `WITNESS AGREES`. |

## RULING 3 — identity re-authoring, same gate

**Every commit on the unmerged lane is re-authored under the correct seat identities before merge.**
The ambient identity currently attributes agent work to a human. Prove with a **git log author
audit**. Enforce **per-seat identity on future commits procedurally**.

→ Recorded as `CD-RULE-002` in `governance/rules/PROJECT-RULES.md`.

## RULING 4 — re-issue Assurance when rework is complete

The auditor **must generate FRESH variants**. Its escaped ten are now the Engineer's known set and
**prove nothing about the class**. Same separation, same **distinct actor_ids**.

## THE GATE

Unchanged: **Assurance PASS on all five.** Deliberate **STOP at the gate either way.** Commit at
every boundary. Small durable steps.

---

## What this disposition does NOT rule, and is therefore still owed

Recorded so no seat reads silence as permission (`PBG-AUTH-005`):

* **CD-ASR-F07** (LOW, CD-AC-005 — an exception handler resolving to agreement, undetected but not
  shown exploitable) is **not named** in Ruling 2. The Project Lead's reading: F07 is the same class
  as F06 on the same criterion, and the structure that closes F06 as a class — agreement requiring
  positive freshness evidence at construction — closes F07 as a consequence rather than as extra
  scope. WO-2R is instructed to **report** whether its F06 structure closes F07, and **not** to
  broaden scope if it does not. F07 otherwise remains owed at WO-3.
* **CD-ASR-N02** (LOW, the live grant-matrix check declares no clean-cluster precondition) is not
  named. Owed at WO-3; the Assurance re-dispatch is told about it so it does not rediscover it as a
  cluster-contamination surprise.
* **CD-D-005** (the ingredient set) and **CD-D-006** consequences, **CD-ENG-F39**, **CD-ENG-F41**,
  **CD-PL-F43**, **CD-ERR-001** — all previously ruled owed at WO-3 and untouched by this review.
* **The staleness ceiling VALUE** (F06) is a product quantity. The Project Lead will not invent one
  (`PBG-AUTH-005`). WO-2R is instructed to **derive** the ceiling from already-recorded product
  intent, and if no such intent exists, to **fail closed and raise it** rather than choose a number.
  See `CD-RULE-003`.
