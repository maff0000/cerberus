# WO-3 SCOPE AND PLAN — the first real sources, with provenance

**authority:** `PO-DECISIONS-0023` rulings 5 and 6(b) · **written at:** boundary
`BL-20260823T173018Z-0151`, by `PROJECT_LEAD_SEAT_01` · **base:** `main` at `a3ca594`
**status:** A SCOPE. **NOT A DISPATCH, NOT A REGISTRATION, AND NOT A DECISION ABOUT PRODUCT CONTENT.**

---

## 0. THE STOP IS AT THE TOP OF THIS DOCUMENT, NOT THE BOTTOM

**WO-3 CANNOT BE DISPATCHED UNTIL MATT NAMES THE SOURCE SET.** That is `PO-DECISIONS-0023` ruling 6,
and it is the same boundary `BLUEPRINT` §16 has carried since v0.1.0 as `CD-D-005`:

> *"Choosing them is choosing what the dial means, and doctrine §3.6 forbids unexplained mappings —
> so this is the Product Owner's register, not my inference from the ARGUS implementation
> (`PBG-PID-003`: existing code is evidence of current implementation, not authorised intent)."*

**THIS DOCUMENT THEREFORE NAMES NO INDICATOR, NO FEED, NO VENDOR, NO CADENCE AND NO CRITICALITY.**
It specifies the **shape** of what is owed — which is construction and is this seat's — and stops at
the **content** — which is product meaning and is Matt's. §7 states exactly what must be named, in
the exact fields the code already requires, so that naming it is a filling-in and not a design task.

**A SCOPE IS NOT A REGISTRATION.** Nothing here registers a source, and no seat may read this
document as authority to register one.

---

## 1. WHAT WO-3 IS, AND WHY IT IS THE CRITICAL PATH

`BLUEPRINT` §15, verbatim:

> **WO-3** | publication layer, heartbeat, external probe, regime-aware staleness, health surface;
> **a CONSTRUCTION-PROVENANCE door at admission** (`CD-AC-017`, §17 RESISTED tier); **the publication
> boundary raising DIVERGENCE** (`CD-AC-018`, §17 DETECTED tier) | 008, 009, 014, **017**, **018** |
> Assurance PASS; public-surface change → external R2D2 review (PID §8)

`PO-DECISIONS-0023` ruling 5 states why this is not merely the next work order but **the** path:

> *"The perimeter's closure (`CD-AC-002`/`CD-AC-005`) DEPENDS on the DETECTED tier, which needs real
> registered sources with provenance and witness divergence at publication (`CD-AC-017`/`CD-AC-018`)
> — all WO-3 work. WO-3 is also what scores the dials and feeds the page (WO-4)."*

**SO ONE WORK ORDER IS SIMULTANEOUSLY THREE THINGS**, and it is worth stating them separately
because they have different audiences:

| It is | Because |
|---|---|
| **the perimeter's path to closure** | `CD-BP-005`'s `RESISTED` tier is **OWED, NOT BUILT**, and the load it was to carry has been moved to `DETECTED` — which does not exist either, because with zero registry rows **there are no witnesses to diverge from**. |
| **the dials' first honest numbers** | with zero sources every dial reads `UNKNOWN`. That is correct and it is also **not yet a detector**. |
| **Matt's "first full testing stage"** | it is the first time the thing is pointed at reality. |

### 1.1 The `RESISTED`/`DETECTED` chain, stated once so the dependency is not lost

`BLUEPRINT` §17 `CD-BP-005`, as corrected by the Product Owner at v0.4.0 and again at v0.4.2:

- **PREVENTED** — accident and casual misuse. **BUILT**, non-vacuous, proved by a refusing arm.
- **RESISTED** — deliberate in-process forgery (`F1`). **OWED, NOT BUILT.** `CD-AC-017` is the
  specified mechanism and, as first measured, **insufficient alone**: a value forged *after*
  admission defeats it at zero cost.
- **DETECTED** — the residual and the catastrophic-blast case. `CD-AC-018`, witness divergence at
  publication. **THE LOAD-BEARING DEFENCE, with admission-provenance as defence-in-depth and not as
  the primary.**

**THE CONSEQUENCE FOR SCOPING IS SHARP: `CD-AC-017` MUST BE BUILT *AND SHOWN TO BIND POST-ADMISSION
MUTATION*, OR IT DOES NOT DISCHARGE WHAT IT IS SCHEDULED FOR.** Building a door that admits
correctly and then letting the admitted value be mutated is the exact failure the correction was
written after. **That "and" is a WO-3 acceptance obligation, not a nice-to-have**, and §5 carries it
as its own deliverable rather than folding it into `CD-AC-017`.

---

## 2. FOUR MEASURED PRECONDITIONS. **ALL FOUR WERE MEASURED AT THIS BOUNDARY AND NONE WAS ASSUMED.**

**THESE ARE THE REASON THIS DOCUMENT IS NOT SIMPLY "DISPATCH WO-3 WHEN MATT ANSWERS."** Three of the
four were not on anybody's list before this boundary.

### P1 · **THERE IS NO `src/` ON `main` AT ALL. EVERY LINE OF THE APPLICATION LIVES ON A FROZEN LANE.**

```
git ls-tree -r --name-only HEAD -- src        ->  (empty)
git ls-tree -r --name-only be0b355 -- src     ->  39 modules
git rev-parse wo-2r3                          ->  be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5
```

`main` carries governance, `tools/` and `pbg/` — **and no product code.** The publication layer,
witness panel, source registry, staleness module, admission and establishment machinery that WO-3
must extend all exist **only at `be0b355`**, which is **FROZEN** and behind a **SHUT** WO-2 gate.

**SO WO-3 HAS NO BASE.** Its Engineer cannot branch from `main` (nothing to build on) and cannot
branch from a frozen lane without a ruling that unfreezes it or defines a successor. **THIS IS A
STRUCTURAL BLOCKER AND IT IS NOT THIS SEAT'S TO RESOLVE** — `PO-DECISIONS-0023` ruling 7 keeps the
WO-2 gate SHUT and says it *"closes when WO-3 delivers the DETECTED tier."* **THAT IS A CIRCLE ON ITS
FACE: WO-3 NEEDS A BASE, THE BASE IS BEHIND THE GATE, AND THE GATE OPENS ON WO-3'S OUTPUT.** It is
put up as `Q24` and this seat does not cut it.

**HOW THIS SEAT COULD BE WRONG, STATED PLAINLY:** the intended reading may be that the gate's
shutness governs *acceptance* and not *branching*, so a WO-3 lane may legitimately be cut from
`be0b355` while the gate stays shut. **THAT IS THE CHEAP ERROR AND IT IS PROBABLY THE RIGHT
READING.** The expensive error is a seat unfreezing a lane on its own inference, which is why the
probable reading is not acted on.

### P2 · **THE REQUIRED TEST REGISTER IS NOT A VALID INPUT, AND HAS NEVER BEEN ONE.**

Run against the register **in its own complete tree, with the very PID it was written against
present at the path it names** — so this is not an artefact of extraction:

```
git archive be0b355 | tar -x -C /tmp/wo3-lane
sha256sum /tmp/wo3-lane/PID.md -> 441d8316…   (the PID the register pins — the right one for this tree)
pbg required-tests verify --register required-tests.yaml

  VALIDATION FAILED — the register is not a valid input; no status is computed:
    ! criteria[1] (CD-AC-002).tests[3].negative_control: unknown field: planted_violation
    ! criteria[1] (CD-AC-002).tests[3].negative_control: unknown field: planted_violation_note
    ! criteria[3] (CD-AC-005).tests[2].negative_control: unknown field: planted_violation
    ! criteria[3] (CD-AC-005).tests[2].negative_control: unknown field: planted_violation_note
    ! criteria[3] (CD-AC-005).tests[3].negative_control: unknown field: planted_violation
    ! criteria[3] (CD-AC-005).tests[3].negative_control: unknown field: planted_violation_note

  GATE: SHUT
  PID_ACCEPTANCE_SATISFIED: NOT DERIVED
```

The contract allows exactly `{"violation", "evidence_ref"}` under `negative_control`
(`pbg/tools/pbg/required_tests.py:82`). The register writes `planted_violation` /
`planted_violation_note`. **A FIELD-NAME MISMATCH, SIX TIMES.**

*** **AND THE SIX ARE NOT SPREAD ACROSS THE REGISTER. ALL SIX ARE IN `CD-AC-002` AND `CD-AC-005` —
THE EXACT TWO CRITERIA WHOSE CLOSURE THE WHOLE PERIMETER TURNS ON, AND THE TWO GRADES EVERY RECENT
RULING HAS PROTECTED.** *** This seat states what it does **not** know: whether that co-location is
causal or coincidence. **It did not investigate, because investigating it is Engineer work on a
frozen lane.** It is recorded because a coincidence in exactly those two rows is the kind of thing a
record goes quiet about.

**WHAT THIS COSTS, AND IT IS THE REAL COST:** validation failing means **NO STATUS IS COMPUTED FOR
ANY CRITERION.** The register has been carried through multiple gates as an input, and **as an input
it has been returning nothing at all.**

### P3 · **THE PID PIN IS STALE — AND THE STALENESS IS CURRENTLY INVISIBLE TO THE INSTRUMENT.**

`PO-DECISIONS-0020` disclosed the consequence in advance: *"any Required Test Register pinned to the
old hash is no longer a valid input and MUST be re-pinned before WO-3."* **MEASURED, AND THE
DISCLOSURE WAS RIGHT:**

```
register pins        sha256:441d83166b2f3d0c…
sha256sum PID.md  -> 538e30f3bf4f1803…          (and pid_identity is PID.md@538e30f3bf4f1803)
```

*** **BUT THE INSTRUMENT NEVER SAYS SO, AND THAT IS THE PART THAT IS NEW HERE.** *** Its report
prints `pid.content_hash (not comparable)` and `pid.ref (unresolved)` — **because `report.pid_ref` is
only assigned during status derivation (`required_tests.py:611-612`), which P2's schema failure
short-circuits before it is ever reached.**

**SO THE SCHEMA DEFECT MASKS THE PIN DEFECT.** Fixing P2 alone would make P3 appear as if it were
new. **IT IS NOT NEW, IT WAS HIDDEN, AND IT IS WRITTEN DOWN HERE SO THAT WHEN IT SURFACES NOBODY
RECORDS IT AS A REGRESSION.** This seat is explicit that `(unresolved)` is a **consequence** of P2
and **not a second independent defect** — the distinction matters, and overclaiming it would be the
easier and worse sentence to write.

### P4 · **THE CENSUS IS 17 AND THE REGISTER CARRIES 16.** `CD-AC-017` IS NOW `DERIVES`, NOT `NEW_REQUIREMENT`.

Measured with the instrument's **own** census function against the **current** PID — not by reading
the PID and counting by eye:

```
python3 -c "from pbg.required_tests import derive_pid_census; …"
  CENSUS SIZE: 17
  CD-AC-017 in census: True
  CD-AC-018 in census: False
```

Three consequences, and they resolve an item the record has carried as unfinished:

1. **`CD-AC-017` IS IN THE PID CENSUS**, so it enters the register with `pid_relation: DERIVES`.
   **IT IS NO LONGER `NEW_REQUIREMENT`** — that relation is coded as *"blocked pending PO amendment
   of the PID"* (`required_tests.py:708-715`), **and the amendment has happened** (PID v1.1.0,
   `PO-DECISIONS-0020` ruling 1). **THE BLOCK IS SPENT.**
2. **`CD-AC-018` IS CORRECTLY ABSENT FROM THE CENSUS** — exactly as ruling 1 ordered: *"`CD-AC-018`
   GAINS NO ROW AND THE ABSENCE IS THE RULING."* It enters as a register-only entry with
   `pid_relation: STRENGTHENS CD-AC-004`, and **`CD-AC-004` is in the census, so the `STRENGTHENS`
   trace resolves rather than dangling.**
3. **THE REGISTER'S 16 ROWS ARE NOW SHORT BY ONE AGAINST ITS OWN CONTRACT** — and the register's own
   header is the authority against it: *"a register that quietly dropped the criteria it could not
   yet satisfy would be marking its own paper."*

**THIS CLOSES THE `3/4 OF THE CD-D-172 FORM` CARRIAGE** that `CD-AC-017` and `CD-AC-018` have been
held at since `PO-DECISIONS-0020` — *"the register row does not exist … AND NOBODY ROUNDED UP."*
**The rows are now specifiable, with the relation for each measured rather than chosen.**

---

## 3. WHAT WO-3 DELIVERS

Grouped by what they are, because they are not one kind of thing.

### Group A — **THE PRODUCT CONTENT LANDING** (blocked on Matt; §7)

| # | Deliverable | Shape |
|---|---|---|
| A1 | **The registered sources** | rows in `raw.source_registry` via `SourceRecord`/`SourceRegistry` — the module exists at `be0b355` and **registers none of it by design**. |
| A2 | **The `ModelSpec` / `ModelProvenance` rows** | `BLUEPRINT` §16: *"the contents of `ModelProvenance` — source, what it stands for, criticality, and the account of the mapping that doctrine §3.6 requires — and the members of `MappingKind` are product meaning."* |
| A3 | **`MappingKind` members** | ships today with **exactly ONE member, and that member computes nothing.** |
| A4 | **Combination models** | `PO-PRODUCT-0001` R4: a combination multiplier **IS A MODEL** — a named `MappingKind` member with a registered, provenanced `ModelSpec`. **An unexplained multiplier CANNOT COMPUTE. R4 IS ENFORCED BY CONSTRUCTION.** |

### Group B — **THE PERIMETER** (`CD-AC-017`, `CD-AC-018`) — construction, but gated on A

| # | Deliverable | Criterion | Note |
|---|---|---|---|
| B1 | Construction-provenance door at admission | `CD-AC-017` | plant: forged object of exact type that never left a declared door → **refused**; genuine article from the declared door → **admitted**. **BOTH ARMS OR IT IS VACUOUS.** |
| B2 | **`CD-AC-017` shown to bind POST-ADMISSION MUTATION** | `CD-AC-017` | **ITS OWN DELIVERABLE, DELIBERATELY NOT FOLDED INTO B1.** §17 says the door is *"insufficient alone"* precisely here. |
| B3 | Publication boundary raising DIVERGENCE | `CD-AC-018` | the `DETECTED` tier. **Carries `F1`'s load.** Completes at WO-4 as the witnesses land (§15). |
| B4 | The **FORGERY-DETECTION OBLIGATION** | §16/§17 | *"specified at WO-3, when real sources land, and verified as a first-class criterion."* **It could not be specified before WO-3 because with zero registry rows there are no witnesses to diverge from** — the same dependency as B3. |

### Group C — **THE PUBLICATION AND HEALTH SURFACE** — construction, largely independent of A

| # | Deliverable | Criterion |
|---|---|---|
| C1 | Publication layer: two envelopes/cycle, each validated against its own closed schema before writing; `detail_level` proportionality in **one** place | (§8) |
| C2 | `publication.heartbeat` on every successful publish; **a cadence breach is an excessive INTERVAL BETWEEN HEARTBEATS, not the age of a number**, alerting within one publication cycle | `CD-AC-008` |
| C3 | **External probe, running OUTSIDE the container set** — *a process inside the system reporting that the system is publishing is self-certification* (`PBG-EVID-001`, `PBG-DEPLOY-002`); satisfies the PID §5 15-minute budget | `CD-AC-008`, `CD-AC-014` |
| C4 | Regime-aware staleness windows — **the same age that passes in calm fails in stress** | `CD-AC-009` |
| C5 | Unauthenticated health surface: liveness, `last_publication_utc`, `last_evaluation_utc`, `regime`, degraded state. **Detector health, not market information — public-safe** | `CD-AC-014` |
| C6 | Alert transport — **an explicitly deferred Level 1 choice**, §10: *"settled in WO-3 against whatever channel Matt actually reads."* `alert.event` rows are durable first, **so no alert is lost while it is decided** | (§10) |

**C6 IS A SECOND, SMALLER PRODUCT QUESTION AND IT IS NOT THE SAME AS THE SOURCE SET.** It is `Q26`.

### Group D — **THE REGISTER REPAIR** (P2/P3/P4) — a precondition, not a WO-3 feature

| # | Deliverable |
|---|---|
| D1 | Repair the six `negative_control` field-name errors so the register **validates at all**. |
| D2 | Re-pin `pid.content_hash` to `538e30f3…`, **after** D1, and expect P3 to surface — **it is not a regression.** |
| D3 | Add the `CD-AC-017` row, `pid_relation: DERIVES`. |
| D4 | Add the `CD-AC-018` register-only row, `pid_relation: STRENGTHENS CD-AC-004`. |
| D5 | Re-run the verifier and record **what it computes**, not what a seat asserts. |

**D IS NOT OPTIONAL AND IT IS NOT COSMETIC: UNTIL THE REGISTER VALIDATES, NO CRITERION HAS A
COMPUTED STATUS, AND WO-3'S GATE HAS NOTHING TO READ.**

---

## 4. THE PROPOSED INCREMENT ORDER, AND THE REASON FOR IT

**SEQUENTIAL SINGLE-SEAT (`CD-D-181`). NO PARALLEL SEAT. ONE INCREMENT AT A TIME, EACH ITS OWN
ENGINEER DISPATCH, EACH FOLLOWED BY A SEPARATE ASSURANCE SEAT (`PBG-SOD-001`, non-waivable).**

| Inc | Content | Blocked on | Why here |
|---|---|---|---|
| **14** | **Group D** — the register repair | `Q24` (base) only | **IT IS THE ONLY GROUP BLOCKED ON NOTHING PRODUCT-SHAPED, AND EVERY LATER GATE READS ITS OUTPUT.** Doing it first means WO-3's gates have an instrument that computes. Doing it last means every gate before it was read off a register that returns nothing. |
| **15** | **Group C** (C1–C5) — publication, heartbeat, external probe, staleness, health | `Q24` | Construction that **does not need to know which sources exist**. It can proceed while Matt decides, which is the whole reason for separating it. |
| **16** | **Group A** — the sources, models, mappings, combinations | **`Q25` — MATT** | **THE HINGE. NOTHING BELOW IT CAN START.** |
| **17** | **Group B** (B1, B2) — `CD-AC-017` and post-admission binding | inc 16 | needs a real declared door with real traffic through it. |
| **18** | **Group B** (B3, B4) — `CD-AC-018` divergence + the forgery-detection obligation | inc 16, 17 | **needs registered sources to have witnesses to diverge from.** |
| — | C6 alert transport | `Q26` | folds into whichever increment is live when it is answered. |

**INCREMENTS 14 AND 15 ARE THE HONEST ANSWER TO "WHAT CAN PROCEED WHILE MATT DECIDES."** They are
offered as *available*, **NOT DISPATCHED** — `PO-DECISIONS-0023` ruling 6 sends this seat to a stop,
and a seat that dispatched an increment on its way to a stop would be choosing to keep moving.

---

## 5. WHAT MUST NOT HAPPEN IN WO-3

1. **NO SOURCE IS REGISTERED BEFORE MATT NAMES THE SET.** Not one row, not as a placeholder, **and
   not as a test fixture** — `CD-PL-F154` is what happens when a fixture escapes.
2. **NO `MappingKind` MEMBER IS ACCEPTED WITHOUT THE OWED MEASUREMENT.** `BLUEPRINT` §16:
   **acceptance of the first computing member RE-RUNS the `*extra` guard measurement at the
   then-current head.** WO-2R3 inc 7 measured that nothing structurally binds `_evaluate_dial`'s
   `*extra`/`**extra_by_name`, and that it is safe **only because every `MappingKind` member raises
   in `compute`.** *** **THAT IS A PRODUCT GAP HOLDING A HOLE SHUT, NOT A GUARD — AND IT EXPIRES ON
   THE EXACT DAY INCREMENT 16 LANDS. THE MEASUREMENT IS OWED *BEFORE* THE MEMBER IS ACCEPTED, NOT
   AFTER.** ***
3. **NO BLENDING, EVER** (`CD-AC-002`). Real numbers are when the temptation arrives.
4. **NO ROUTE FROM `Unavailable` TO `Agrees`** (`CD-AC-005`). `WITNESS UNAVAILABLE ≠ WITNESS AGREES`,
   and **absence must map to `Unavailable`** — both the explicit and implicit failure paths.
5. **DIVERGENCE IS AN ALARM, NEVER AN ADJUSTMENT** (`CD-AC-004`). In a divergence cycle the dial
   numbers are **byte-identical** to what they would have been with no witness data — checkable,
   because the computing process holds no grant on the witness schema.
6. **NO BACKFILLED POINT PRESENTED AS LIVE TRACK RECORD** (`CD-AC-010`, `PO-PRODUCT-0001` R2).
7. **`CD-AC-017` IS NOT DONE WHEN THE DOOR REFUSES A FORGERY.** It is done when the door refuses a
   forgery **and** the admitted value cannot be mutated afterwards (B2). **A one-armed plant here
   would reproduce the exact vacuity §17 was corrected for.**
8. **NO PARALLEL SEAT** (`CD-D-181`); **the coordination discipline stays parked** — no WO-3
   increment may reach for it, and **no coordination residual may be quietly fixed inside a WO-3
   increment**, which would un-park it by the back door.

---

## 6. WHAT THIS SCOPE DOES *NOT* MOVE

**`CD-AC-002` AMBER AND NOT CLOSED. `CD-AC-005` RED. NEITHER TOUCHED, AND THE DISPATCH FORBADE
TOUCHING THEM.** The WO-2 gate stays **SHUT**. `wo-2r3` stays **FROZEN at `be0b355`** — **verified at
this boundary and not assumed.** No finding is closed. No grade is moved. No seat is dispatched.

---

## 7. WHAT MATT MUST NAME — THE EXACT FIELDS, SO THAT NAMING IT IS FILLING IN AND NOT DESIGNING

Every field below **already exists in code at `be0b355`** or is already required by
`PO-PRODUCT-0001`. **NOTHING HERE IS A NEW ASK; IT IS THE EXISTING ASK MADE FIELD-BY-FIELD.**

### 7.1 Per source (one row each)

| Field | Meaning | Note |
|---|---|---|
| `source_id` | stable identifier | |
| what it stands for | the plain-language account | **doctrine §3.6 forbids unexplained mappings — this is not documentation, it is the admission ticket.** |
| adapter | how it is fetched | |
| cadence | how often | |
| **`criticality`** | `REQUIRED` \| `CONTRIBUTING` \| `DISPOSABLE` | **THIS IS A STATEMENT ABOUT ENGINE BEHAVIOUR, NOT A LABEL:** `REQUIRED` absent → `Unknown`; `CONTRIBUTING` absent → `Degraded`; `DISPOSABLE` absent → nothing changes. **The registry refuses any incoherent combination (`CriticalityContractViolated`), so a criticality chosen loosely will be REFUSED, not silently accepted.** |
| which dial(s) it feeds | `equity` and/or `monetary` | **NEVER BOTH BLENDED** (`CD-AC-002`). |
| weight / contribution | its contribution to the score | `PO-PRODUCT-0001` R3: **contribution is first-class; level alone is not enough.** |
| relevant window | days / weeks-months / quarters | `PO-PRODUCT-0001` R2 — **per indicator, not global.** |

### 7.2 Per model / mapping

`ModelSpec` name · `ModelProvenance` (source, what it stands for, criticality) · **the account of the
mapping doctrine §3.6 requires** · the `MappingKind` member it uses.

### 7.3 Per combination (`PO-PRODUCT-0001` R4)

**Every combination/multiplier DECLARED, NAMED and EXPLAINED** — *"never an implicit interaction
inside a formula."* Each **is a model**: a named `MappingKind` member with a registered, provenanced
`ModelSpec`. **AN UNEXPLAINED MULTIPLIER CANNOT COMPUTE.**

### 7.4 The alignment `PO-DECISIONS-0023` ruling 6 requires

The set must align with the **ratified page spec** (`PO-PRODUCT-0001`): the indicator table, RAG
status, per-indicator modals carrying **chart + calculation + dial-binding**, and combinations as
registered models. **Its lineage is the ARGUS `/playbook` page — 20 indicators, 10 categories, 8
combination mirror signals — which *"proved the shape; the detector does it with provenance and
refusals."*** **THAT LINEAGE IS EVIDENCE OF A SHAPE THAT WORKED. IT IS NOT AUTHORISED INTENT AND NO
SEAT MAY READ THE INDICATOR LIST OFF IT** (`PBG-PID-003`, and `BLUEPRINT` §16 says so by name).

---

## 8. QUESTIONS FOR THE PRODUCT AUTHORITY. **THIS SEAT ANSWERS NONE OF THEM.**

**`Q24` — WHAT IS WO-3'S BASE?** `main` has **no `src/`** (measured); the only application tree is
`be0b355`, frozen behind a gate ruling 7 keeps SHUT until WO-3 delivers. **Does a WO-3 lane cut from
`be0b355` while the gate stays shut, or does something else move first?** This seat's reading is that
the gate governs *acceptance*, not *branching* — **and it did not act on that reading, because
unfreezing a lane on an inference is exactly the class of act this project has spent ten gates
learning not to do.**

**`Q25` — THE SOURCE SET. THE HINGE, AND IT IS MATT'S.** §7 is the field list. **Nothing in Group A,
B or increments 16-18 can begin.**

**`Q26` — THE ALERT CHANNEL** (§10, an explicitly deferred Level 1 choice): *"whatever channel Matt
actually reads."* **Durable `alert.event` rows mean nothing is lost while it is open, so it does not
block — but it does not answer itself either.**

**`Q27` — DO INCREMENTS 14 AND 15 PROCEED WHILE `Q25` IS OPEN?** Group D (register repair) and
Group C (publication/health) need no source names. **They are offered as available and are NOT
dispatched.** Ruling 6 sent this seat to a stop, **and a seat that dispatched on its way to a stop
would have decided this question by moving.**

---

## 9. DECLARED LIMITS OF THIS SCOPE

1. **NO PRODUCT CONTENT IS CHOSEN HERE.** No indicator, feed, vendor, cadence, criticality, weight,
   window, model or combination. **That is the point of the document, not a gap in it.**
2. **THE INCREMENT ORDER IN §4 IS A PROPOSAL.** `PBG-AUTH-003` — a Project Lead scopes; it does not
   ratify its own plan.
3. **P2/P3/P4 WERE MEASURED AT `be0b355` AND AGAINST `PID.md@538e30f3`, AT THIS BOUNDARY.** They are
   true of those artefacts at those SHAs and **were not re-derived from any other tree.**
4. **NO WO-3 CODE WAS READ FOR CORRECTNESS.** Modules were enumerated (`git ls-tree`) and
   `source_registry.py`'s contract read. **THIS IS A SCOPE, NOT A REVIEW, AND IT MAKES NO CLAIM
   ABOUT WHETHER WHAT EXISTS AT `be0b355` IS RIGHT.**
5. **THE `CD-AC-002`/`CD-AC-005` CO-LOCATION OF ALL SIX P2 ERRORS IS REPORTED, NOT DIAGNOSED.** This
   seat does not know whether it is causal or coincidence and **did not investigate, because that is
   Engineer work on a frozen lane.**
6. **`PBG-EVID-001`/`PBG-DEPLOY-002` ARE CITED FROM `BLUEPRINT` §8's OWN TEXT, NOT RE-READ FROM THE
   FRAMEWORK AT THIS BOUNDARY.** The obligation they carry is the Blueprint's statement of them.
