# CD-DISPATCH-INC15-PUBLICATION-ENGINEER

**role source:** `pbg/roles/engineer.md` — read it; reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** `PO-DECISIONS-0024` rulings 2 (`Q27` — increment 15 proceeds) and 3 (`Q26` —
the alert-channel default) · scope `governance/engineering/WO-3-SCOPE.md` §3 **Group C**
**seat identity:** `CD-ENG-WO3-02` — **FRESH.** Never `CD-ENG-WO3-01`, never `CD-ASR-WO3-01`, never
any `CD-ENG-WO2R3-*` or `CD-ENG-COORD*`.
**issued by:** `PROJECT_LEAD_SEAT_01` · **increment:** 15 · **expected return:** `READY_FOR_ASSURANCE`

---

## 1. THE LANE, AND WHERE YOU START

```
branch    wo-3
worktree  /srv/crash-detector-wo3
tip       9b09d2a  (increment 14 — the register repair; ASSURED `PASS`, BANKED, NOT ACCEPTED)
base      be0b355  (FROZEN — READ-ONLY TO YOU. Build forward; never amend, rebase or move it.)
```

**Increment 14 made the Required Test Register compute a status for the first time in its life
(0 -> 18, all `UNDECIDABLE`).** You inherit a working instrument. **DO NOT REGRESS IT** — §7 makes
that a hard check on your return.

---

## 2. WHAT INCREMENT 15 IS

**Group C — the publication and health surface. PURE CONSTRUCTION. NO PRODUCT CONTENT.** It is
dispatched now precisely because **it does not need to know which sources exist**, and the source set
is **HELD FOR MATT** (`Q25`).

| # | Deliverable | Criterion |
|---|---|---|
| **C1** | **Publication layer** — two envelopes per cycle, **each validated against its own closed schema BEFORE writing**; `detail_level` proportionality implemented in **ONE** place | BLUEPRINT §8 |
| **C2** | **`publication.heartbeat` on every successful publish** | `CD-AC-008` |
| **C3** | **External probe, running OUTSIDE the container set** | `CD-AC-008`, `CD-AC-014` |
| **C4** | **Regime-aware staleness windows** | `CD-AC-009` |
| **C5** | **Unauthenticated health surface** | `CD-AC-014` |
| **C6** | **Alert surfacing — `Q26` IS NOW RULED, see §4** | BLUEPRINT §10 |

---

## 3. WHAT ALREADY EXISTS — **MEASURED BY THE PROJECT LEAD AT THIS BOUNDARY. SURVEY IT YOURSELF BEFORE YOU WRITE A LINE.**

**You are extending a real codebase, not starting one.** Measured on the lane:

- `src/crash_detector/publication/` — `envelope_contract.py` (with `refuse_unless_publishable`,
  `load_envelope_schema`, `EnvelopeSurface`, and a **closed** refusal vocabulary:
  `UNKNOWN_KEY`, `SCHEMA_VIOLATION`, `PRIVATE_CLASSIFIED_KEY`, `SECRET_BEARING_KEY`,
  `NON_FINITE_NUMBER`, …), `classification.py`, `dial_scalar.py`
- `src/crash_detector/staleness.py` — **596 lines**, `StalenessWindow`, `FreshnessEvidence`,
  `StalenessWindowOutOfRange`, `FreshnessNotEstablished`. **`regime` already appears in it (6
  occurrences) and in `engine/config.py`.** **SO C4 IS AN EXTENSION, NOT A GREENFIELD — FIND OUT
  EXACTLY HOW MUCH IS ALREADY THERE BEFORE YOU BUILD A SECOND MECHANISM BESIDE IT.**
- `db/migrations/0005_publication.sql` — `publication.public_envelope`, `private_envelope`,
  `witness_panel`, `review`, **and `publication.heartbeat`**
- `db/migrations/0006_private_and_alert.sql` — **`alert.event`, APPEND-ONLY**, with a **closed**
  `event_class` check constraint, `severity`, `raised_by`, and `subject_ref` bounded at 200 carrying
  **a key NAME, never the value behind it** (`PBG-SEC-002`)
- `src/crash_detector/runtime/lifecycle.py`, `serving/dial_presentation.py`,
  `serving/witness_resolver.py`, `deploy/compose.yaml` + six Dockerfiles

### *** THE MEASUREMENT THAT DEFINES C2 ***

```
grep -rn "heartbeat" src/ --include=*.py   ->  (no matches)
```

**`publication.heartbeat` IS A TABLE THAT NOTHING WRITES.** The schema landed at WO-2 and no
producer was ever built. **THIS IS THE SAME SHAPE AS THE HEADLINE INCREMENT 12 RETURNED — "THE
CONTROLS EXIST AND NOTHING RUNS THEM."** C2 is the writer. **Verify this measurement yourself; if
you find a writer I missed, say so and correct me.**

---

## 4. `Q26` IS RULED — THE ALERT CHANNEL HAS A DEFAULT, AND IT IS NOT A HARD STOP

`PO-DECISIONS-0024` ruling 3, verbatim in substance:

> The detector is advisory (D1): **alerts surface on the publication surface (the page) and a
> machine-readable state endpoint, with NO external push channel until Matt names one.**

**SO:**

1. **`alert.event` ROWS ARE WRITTEN FIRST AND DURABLY.** *"Durable rows first, so no alert is lost
   while the channel is decided."* **The row is the alert. Everything else is a view of it.**
2. **Alerts surface on the publication surface AND on a machine-readable state endpoint.**
3. *** **YOU BUILD NO EXTERNAL PUSH. NO EMAIL, NO WEBHOOK, NO DISCORD, NO SLACK, NO SMS, NO
   OUTBOUND HTTP TO ANY THIRD PARTY.** *** Not behind a feature flag, not disabled-by-default, not
   "ready to enable". **Matt names the channel or there is no channel.** The ruling says it is *"a
   one-line addition when he says so"* — **build so that it is one line, and do not write the line.**
4. **Egress is already constrained on this lane** (`deploy/egress-destinations.yaml`,
   `CD-RT-012-EGRESS-NO-BROKER`). **DO NOT WIDEN IT.** If your work appears to need a new egress
   destination, **STOP AND REPORT** — that is a finding, not a config change.

---

## 5. THE DELIVERABLES, WITH THE PARTS THAT ARE EASY TO GET WRONG NAMED

### C1 — the publication layer

- **Two envelopes per cycle, each validated against ITS OWN closed schema BEFORE the write.**
  Validation after the write, or one schema shared by both surfaces, is not this.
- **`detail_level` proportionality lives in EXACTLY ONE PLACE.** The scope says *"in **one**
  place"* deliberately. **Two call sites that each decide how much detail to emit is the defect.**
- **The public envelope carries ZERO private data** (`CD-AC-006`). The existing refusal vocabulary
  already has `PRIVATE_CLASSIFIED_KEY` and `SECRET_BEARING_KEY` — **use the existing door, do not
  build a second one beside it.**

### C2 — heartbeat and cadence

- **A heartbeat row on EVERY successful publish.**
- *** **A CADENCE BREACH IS AN EXCESSIVE *INTERVAL BETWEEN HEARTBEATS*. IT IS NOT THE AGE OF A
  NUMBER.** *** These come apart exactly when it matters: **a detector republishing a stale number
  on time has a healthy cadence and stale data; a detector publishing fresh data late has fresh data
  and a broken cadence.** **C2 measures the FIRST. C4 measures the SECOND. If your implementation
  cannot distinguish them, it has not built C2.**
- **Alerting within one publication cycle.**

### C3 — the external probe

> *"A process inside the system reporting that the system is publishing is **SELF-CERTIFICATION**"*
> (`PBG-EVID-001`, `PBG-DEPLOY-002`).

- **IT RUNS OUTSIDE THE CONTAINER SET.** Not another service in `compose.yaml` that happens to be
  separate. **Outside.** If the whole container set is down, **the probe must still be able to say
  so** — a probe that dies with the thing it watches has reported nothing.
- It must satisfy the **PID §5 15-minute budget**. Read PID §5 and satisfy what it actually says.
- **It observes the PUBLIC surface only**, as an outside party would. **No database credential, no
  private envelope, no internal API.**

### C4 — regime-aware staleness

> *"The same age that passes in calm fails in stress."*

- Extend what `staleness.py` already has. **Survey first.**
- **The windows are a REGIME-DEPENDENT POLICY, not a per-indicator product choice** — **you are NOT
  naming sources, indicators or per-indicator windows** (that is `Q25`, held; and
  `PO-PRODUCT-0001` R2's per-indicator windows are increment 16's).

### C5 — the health surface

- **Unauthenticated**, carrying: liveness, `last_publication_utc`, `last_evaluation_utc`, `regime`,
  degraded state.
- *** **DETECTOR HEALTH, NOT MARKET INFORMATION. IT MUST BE PUBLIC-SAFE.** *** **A health endpoint
  that leaks a dial value, a witness reading, a source name or a private-envelope key is a
  `CD-AC-006` breach wearing an ops hat** — and it is a genuinely easy mistake, because "degraded"
  is tempting to explain with the number that degraded. **Explain it with a CLASS, never a VALUE.**
- The machine-readable state endpoint of `Q26` is naturally adjacent to this. **Keep the SAFETY
  PROPERTY identical on both.**

---

## 6. PLANTS — CONTRAST FORM. **BOTH ARMS OR IT IS VACUOUS.**

**Every guard you build gets a plant that PROVES IT REFUSES, and an arm that PROVES IT ADMITS THE
GENUINE ARTICLE.** A guard that refuses everything satisfies its invariant vacuously — this project
has made that mistake and named it.

At minimum:

| Plant | Refusing arm | Admitting arm |
|---|---|---|
| Envelope validated **before** write | an envelope violating its closed schema is **refused and NOT written** | a conforming envelope **is written** |
| Public surface carries no private data | a private-classified key in the public envelope is **refused** | a legitimate public envelope **passes** |
| Cadence breach | an excessive **interval between heartbeats** raises within one cycle | normal cadence raises **nothing** |
| **Cadence ≠ age** | a **fresh number published LATE** breaches cadence | a **stale number republished ON TIME** does **NOT** breach cadence *(it is C4's business)* |
| Regime-aware staleness | an age that **passes in calm FAILS in stress** | the same age **passes in calm** |
| Health surface public-safe | an attempt to place a dial value / witness reading / source name on the health surface is **refused** | liveness, timestamps, regime and degraded **class** **pass** |
| **No external push** | **there is no code path that reaches a third party** — prove it structurally, in the shape of `CD-RT-012-EGRESS-NO-BROKER` | — |

**Follow the established evidence form:** each arm from **its own pristine `git archive | tar -x`
extraction**, `git apply`'s **own exit code** recorded as its own column.

> **AND HEED INCREMENT 14'S LESSON (`CD-ENG-WO3-01`'s `F04`, upheld):** **if a column does not
> discriminate on your instrument, SAY SO AND SUBSTITUTE ONE THAT DOES.** Performing the ritual form
> while it measures nothing is the failure mode, not the fix. **Declare any substitution.**

---

## 7. THE REGISTER — A NARROW PERMISSION AND A HARD CHECK

`CD-AC-008`, `CD-AC-009` and `CD-AC-014` **already have rows**. As you make their tests real, you may
update **those three rows' `execute` / `execution_contract` / `negative_control` fields ONLY**.

**HARD CONSTRAINTS:**

1. **RE-RUN THE VERIFIER BEFORE YOU RETURN AND REPORT WHAT IT COMPUTES.** It must **still validate**
   and **still compute 18 statuses**. **A validation failure is a REGRESSION OF INCREMENT 14 and is a
   returnable blocker.**
2. **DO NOT TOUCH `latest_admitted_run`.** It stays `null`. **You do not admit your own evidence**
   (`PBG-SOD-001`, non-waivable).
3. **DO NOT ADD, REMOVE OR RENUMBER ROWS.** 18 in, 18 out.
4. **DO NOT TOUCH `CD-AC-002` OR `CD-AC-005` ROWS AT ALL.**
5. **THE REGISTER GRADES NOTHING.** The validator refuses any register that grades itself. **The
   statuses will stay `UNDECIDABLE` and THAT IS CORRECT** — run records are an Assurance seat's to
   produce. **DO NOT CHASE A GREEN. DO NOT OPEN THE GATE.**
6. **BEWARE `execution_contract`: IT IS A RESOLVABLE FILE PATH, NOT PROSE.** A non-resolving path
   silently forces `UNDECIDABLE` and **skips negative-control evaluation entirely**
   (`required_tests.py:659-663`). **This exact error was prescribed in increment 14's dispatch and
   refused by its Engineer — do not reintroduce it.** If you point a row at a contract file,
   **create the file**.

---

## 8. WRITABLE SCOPE — EXACT

**WRITABLE:** `src/crash_detector/` (publication, staleness, serving, runtime, and a new health/probe
module as needed) · `tests/` · `db/migrations/` (**forward-only, new numbered files; NEVER edit a
landed migration** — `PBG-DATA-002`) · `deploy/` (**compose/Dockerfiles for the probe ONLY; NOT
`egress-destinations.yaml`**) · `contracts/` (envelope schemas and any execution contract you
reference) · `plants/` · `required-tests.yaml` (**narrowly, per §7**) ·
`governance/engineering/build-log/` (your own entries) · `/tmp` scratch

**NOT WRITABLE, each for a reason:**
- **`pbg/`** — pinned, read-only, non-waivable. Editing it to make a control pass is a bypass, not a
  fix (`PBG-FWK-013`).
- **`be0b355` / the `wo-2r3` ref** — the frozen base.
- **`PID.md`, `BLUEPRINT.md`, `governance/decisions/`** — PO-authored, protected from every seat
  including the Project Lead (`CD-D-115`).
- **`deploy/egress-destinations.yaml`** — see §4.4.
- **`governance/engineering/ACTIVE_WORK.yaml`** — the Project Lead's.
- **`src/crash_detector/source_registry.py` as a place to REGISTER anything** — see §9.1.

---

## 9. WHAT MUST NOT HAPPEN

1. *** **NO SOURCE IS REGISTERED. NOT ONE ROW, NOT A PLACEHOLDER, AND NOT A TEST FIXTURE.** *** The
   source set is **HELD FOR MATT** (`Q25`, `PO-DECISIONS-0024` ruling 4). **`CD-PL-F154` is what
   happens when a fixture escapes.** If you need something to publish in a test, use an obviously
   synthetic in-test double that **cannot** be mistaken for a registered source and **never reaches
   `raw.source_registry`**.
2. **DO NOT READ THE INDICATOR LIST OFF THE ARGUS `/playbook` PAGE.** The shape is inheritable; the
   list is not (`PBG-PID-003`).
3. **NO `MappingKind` MEMBER IS ACCEPTED.** It ships with **one member that computes nothing**, and
   **that product gap is currently holding a hole shut**: nothing structurally binds
   `_evaluate_dial`'s `*extra`/`**extra_by_name`, and it is safe **only because every member raises
   in `compute`**. **THAT EXPIRES THE DAY INCREMENT 16 LANDS, AND THE OWED MEASUREMENT IS BEFORE
   ACCEPTANCE, NOT AFTER. DO NOT SPEND IT HERE.**
4. **NO BLENDING OF THE TWO DIALS, EVER** (`CD-AC-002`).
5. **NO ROUTE FROM `Unavailable` TO `Agrees`** (`CD-AC-005`). Absence maps to `Unavailable` on
   **both** the explicit and implicit failure paths. **A publication layer is exactly where an
   absent witness gets quietly rendered as agreement.**
6. **DIVERGENCE IS AN ALARM, NEVER AN ADJUSTMENT** (`CD-AC-004`).
7. **NO BACKFILLED POINT PRESENTED AS LIVE TRACK RECORD** (`CD-AC-010`).
8. **`CD-AC-017` AND `CD-AC-018` ARE NOT YOURS.** They are increments 17 and 18 and they need
   registered sources first. **Do not build the admission door or the divergence detector here**, and
   **do not write their execution contracts** — those are booked to 17/18 deliberately.
9. **DO NOT REACH FOR THE COORDINATION DISCIPLINE.** It is **PARKED** and decoupled to the framework
   track. **No WO-3 increment may quietly fix a coordination residual** — that un-parks it by the
   back door.
10. **NO PARALLEL SEAT** (`CD-D-181`). You are one seat, sequential.
11. **YOU DO NOT APPROVE YOUR OWN WORK.** A separate Assurance seat follows (`PBG-SOD-001`).

---

## 10. IDENTITY

```
GIT_AUTHOR_NAME=CD-ENG-WO3-02 GIT_AUTHOR_EMAIL=cd-eng-wo3-02@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ENG-WO3-02 GIT_COMMITTER_EMAIL=cd-eng-wo3-02@seats.crash-detector.invalid \
git commit -m "[CD-ENG-WO3-02] …"
```

(`git -c user.name=` **does not work in this environment.**) **ONE IDENTITY FROM `9b09d2a` TO YOUR
TIP** (`CD-RULE-002`). Verify: `git log --format='%an' 9b09d2a..HEAD | sort -u` -> **exactly one.**

---

## 11. RETURN

`READY_FOR_ASSURANCE`, with:

- **tip SHA** and `git status --porcelain` (**must be empty**)
- **the verifier's verbatim output** from a pristine extraction of your tip — **18 computed, still
  validating** (§7.1)
- **the plant table**, every guard, both arms, with any column substitution **declared**
- **how you ran the external probe and how you demonstrated it is genuinely OUTSIDE the container
  set** — this is the claim most easily asserted and least easily proved, so **prove it**
- **the cadence-vs-age demonstration** (§5 C2) — the two cases that come apart
- **`git rev-parse wo-2r3`** and confirmation `pbg/` is untouched
- **evidence that NO source was registered**
- **every finding you raise against your own work — and against THIS DISPATCH.** Increment 14's
  Engineer found **two HIGH errors in its own dispatch** and was right both times. **THAT IS THE
  NORM HERE, NOT AN AFFRONT.** If something in this document is wrong, **say so with the
  measurement.**

**IF YOU CANNOT DO SOMETHING, RETURN AND SAY SO. DO NOT IMPROVISE AROUND IT AND DO NOT WIDEN YOUR
OWN SCOPE.** If Group C proves larger than one increment, **build C1-C2 properly and return with a
measured account of what remains** — **a truthful partial is worth more than a hurried whole**, and
the Product Authority is holding at the end of this increment anyway.
