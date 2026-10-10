---
document: BLUEPRINT — how the Crash Detector is built
product: Crash Detector — standalone market stress instrument
version: 0.4.2
status: >
  ACCEPTED. **v0.4.2 CORRECTS THE `RESISTED` TIER TO FUTURE TENSE AND MOVES THE LOAD TO DETECTION —
  PO-DECISIONS-0022 ruling 2, authored by the Product Owner and carried verbatim as the remediation
  increment's FIRST ACT, and NOTHING ELSE.** The ninth Assurance seat's `CD-ASR-WO2R3-06-F02` is
  ACCEPTED, not contested: a value forged AFTER front-door admission defeats construction-provenance
  at zero knowledge and zero package lines, so §17's PRESENT-INDICATIVE `RESISTED` row claimed a
  resistance the product does not have. The row now reads **OWED, NOT BUILT**, and the F1 route's
  load-bearing defence is the **DETECTED** tier (`CD-AC-018`) until `CD-AC-017` is BOTH built AND
  shown to bind post-admission mutation. **THE TIER IS NOT WITHDRAWN — its TENSE is corrected.**
  **CARRIAGE VERIFIED BY COMMAND IN BOTH ARMS** —
  `python3 -B tools/reconciliation/check_blueprint_carried_po_0022_verbatim.py --root .` -> EXIT 0,
  4/4 sentences resolving in BOTH files, 571 normalised characters, ARM 2a superseded fragment
  ABSENT from §17, ARM 3 the supersession measured EXACTLY ONE SENTENCE WIDE; `--counterfactual` ->
  EXIT 1, 5 failures. **AND ONE CONSEQUENCE IS DISCLOSED RATHER THAN HIDDEN, BECAUSE IT IS THE KIND
  OF THING A SEAT WOULD BE TEMPTED TO TIDY: `check_blueprint_carried_po_0019_verbatim.py` NOW EXITS
  1 AT 9/10 (1911 -> 1230 normalised characters, a drop of 681, which is EXACTLY the superseded
  sentence's measured length). IT IS NOT BROKEN AND IT WAS NOT EDITED. A sibling check going RED on
  precisely the sentence a later ruling corrected IS the evidence that the v0.4.0 text existed and
  was superseded BY THE PRODUCT OWNER AND NOT BY A SEAT.** **The Project Lead authored the version
  bump, this status paragraph, the §19 row, and the retained `**Scheduled as CD-AC-017** (§14, §15
  WO-3)` scaffolding clause — and NOTHING that is normative.**
  **v0.4.1 REPAIRS `CD-ASR-WO2R3-05-F05` — AND IT IS A REMOVAL, NOT AN ADDITION.** On
  PO-DECISIONS-0020 ruling 2 (commit abafec2, authored by Matt Scott and by NO seat), the normative
  sentence "not as a note, not as a residue paragraph, and not as a manual step" is REMOVED from §16
  and replaced by a POINTER, in the Product Owner's own words, to where that requirement now lives:
  CD-AC-017 and CD-AC-018, in the PID and the register. **THE PRODUCT OWNER REMOVED IT, NOT A SEAT —
  the prose was the PO's own, and CD-D-115 protects this file from every seat including the Project
  Lead and including the PO acting through a seat.** F05 and F03 are DISCHARGED by that act. §17's
  CD-BP-005 row is UNTOUCHED and keeps its RISK/HANDLING columns citing both criteria. **THE TWO
  CRITERIA ARE 3/4 OF THE CD-D-172 FORM AND ARE CARRIED AS 3/4, NEVER ROUNDED UP — the register row
  is a WO-3 artefact and does not exist today.** Carriage verified BY COMMAND in both arms —
  `python3 -B tools/reconciliation/check_pid_carried_po_0020_verbatim.py --root .`. **The Project
  Lead authored the version bump, this status paragraph, the §19 row, and the disclosure of the
  §16/§17 label discrepancy — and NOTHING that is normative.**
  **v0.4.0 CORRECTS THE PERIMETER TO WHAT WAS MEASURED, on PO-DECISIONS-0019 (authored by
  Matt Scott and by no seat).** §17 CD-BP-005 is restated as THREE TIERS and not two — PREVENTED
  (subclass + accident) / RESISTED (F1, via a construction-provenance door at admission, with its
  measured WeakSet obstacle OWNED in the text) / DETECTED (witness divergence at the publication
  boundary); the word "useless" is STRUCK because it was false for the F1 route the row names first;
  and the assertion "the platform does not permit preventing it" is RETRACTED because ADMISSION WAS
  NEVER TESTED. §14 and §15 gain CD-AC-017 and CD-AC-018, so the obligation is SCHEDULED with an ID
  and a work order instead of being carried as a note, a residue paragraph or a manual step. **The
  Product Owner's own sentences are carried VERBATIM and verified BY COMMAND —
  `python3 -B tools/reconciliation/check_blueprint_carried_po_0019_verbatim.py --root .`** The
  Project Lead authored the version bump, the two criterion IDs, the table scaffolding, the §14
  disclosure block marked as such, and the §19 row — enumerated at BL-20260823T124508Z-0135.
  **v0.3.0 adds NO design decision and REVERSES none — it DECLARES A PERIMETER that was
  previously implied and is false as implied.** §16 gains the FORGERY-DETECTION OBLIGATION (owed at
  WO-3, verified as a first-class criterion) and §17 gains CD-BP-005, both on PO-DECISIONS-0018
  ruling 1 (commit c72b6ea, authored by Matt Scott and by no seat), and **the Product Owner's own
  sentences are carried into both VERBATIM** because this file is protected from every seat
  including the Project Lead (CD-D-115). The version moves because §16 and §17 gained clauses, which
  is this log's own stated rule; **the Project Lead authored the version bump, the row IDs and the
  table scaffolding and NOTHING ELSE — enumerated at BL-20260823T095521Z-0131 so the delta between
  CARRIED and AUTHORED bytes is auditable by command and not by trust.**
  v0.1.0 was accepted by the Product Owner at 2e116ec
  (governance/decisions/PO-ACCEPT-BLUEPRINT-0001.md); CD-HOLD-001 released and application code
  authorised from WO-2 (CD-D-004.1 satisfied). v0.2.0 carries BP-AMENDMENT-0001, which the Product
  Owner dispositioned and ACCEPTED at governance/decisions/PO-DECISIONS-0005.md (commit b4e8eae,
  authored by Matt Scott). The amendment is IN FORCE; this document applies its §F.3 delta and
  NOTHING ELSE.
owner: PROJECT_LEAD
authority: CD-AUTH-0001
derives_from: >
  PID.md v1.1.0 · governance/decisions/PO-DECISIONS-0001.md ·
  governance/decisions/PO-DECISIONS-0004.md §2 (the engine owns the model lifecycle) ·
  governance/decisions/PO-DECISIONS-0005.md (the disposition of BP-AMENDMENT-0001) ·
  governance/decisions/PO-DECISIONS-0018.md ruling 1 (the perimeter DECLARED) ·
  governance/decisions/PO-DECISIONS-0019.md rulings 1-3 (the perimeter CORRECTED to three tiers;
  CD-AC-017 and CD-AC-018 minted) ·
  governance/decisions/PO-DECISIONS-0020.md rulings 1-2 (the two criteria placed in PID §6 BY KIND;
  F05's normative sentence removed from §16 by the Product Owner) ·
  governance/decisions/PO-DECISIONS-0022.md ruling 2 (the RESISTED tier corrected to OWED-NOT-BUILT
  and its load-bearing weight moved to the DETECTED tier)
framework: PBGv2 v2.0.0-alpha.1, pinned read-only at pbg/
last_reconciliation_sha: b4e8eae123e0f1250c80e282c274d73e93bb73ed
reconciliation_note: >
  c291f80 was the SHA whose worktree was read while authoring this document. 0047093 is the SHA at
  which the Project Lead re-read and reconciled it on resuming WO-2, finding no content drift — the
  only correction needed was that header, which still read PROPOSED and still carried the "no
  application code" hold three commits after the Product Owner released it. b4e8eae is the SHA at
  which v0.2.0 was written: the Product Owner's own commit carrying PO-DECISIONS-0005, which is the
  authority for every edit in it. Currency is computed against Git (PBG-BP-003, PBG-FWK-042), never
  read from a date.
amendment: Project Lead owns currency (PBG-BP-001). Assurance verifies, and does not author.
amendments_in_force:
  - id: BP-AMENDMENT-0001
    title: the engine owns the model lifecycle
    path: governance/blueprint/BP-AMENDMENT-0001-engine-owns-the-model-lifecycle.md
    accepted_at: governance/decisions/PO-DECISIONS-0005.md (commit b4e8eae)
    applied_to: '§1, §7, §13, §14, §16, §17, §19 — the amendment''s own §F.3 delta, confirmed by the
      Product Owner at ruling 5 as the whole of what it expected to review'
    note: 'The amendment is the design of record for §7 and is read WITH this document, not instead
      of it. Where the two differ on the model boundary, the amendment governs and this note is the
      defect (PBG-BP-001 — the Project Lead owns currency).'
---

> **NOT AUTHORITY.** The governing blueprint lives on `main`. Every governance citation in
> this lane resolves against `main` at the reconciliation boundary. This file is the
> lane's historical baseline (0.1.0), superseded on `main`.

# Crash Detector — Blueprint

The PID says **what** and **why**, and its §1 and §3 are Constitutional. This document says **how**,
and nothing in it may extend product intent (`PBG-AUTH-003`, `PBG-PID-004`). Where a question turned
out to be product content rather than construction, it is not answered here — it is raised in §16.

---

## 1. The design rule this whole build follows

Doctrine that is enforced by policy is enforced by whoever remembers it. This product's doctrine is
about failure modes that are *silent* — a stale dial reading calm, a witness absence reading as
agreement, a blended number that cancels the signal it was built to carry. A silent failure mode
cannot be governed by care.

So the rule for every component below:

> **A doctrinal property is built as a structure that makes its violation inexpressible, and is
> paired with a mutation test that proves the structure bites.**

**Five** structural instruments do nearly all the work, and they are cheap because they are chosen
once and then reused everywhere:

| Instrument | Makes impossible | Doctrine served |
|---|---|---|
| **Sum types with no default** — a reading is `Value`, `Unknown` or `Degraded`; absence has a name and no numeric fallback exists | rendering absence as a number, therefore as calm | §3.2, CD-AC-001, CD-AC-005 |
| **Database roles with no grant** — a component that must not read something has no permission to read it | a witness leaking into a score; a public surface touching the book | §3.4, §3.5, CD-AC-003, CD-AC-006 |
| **Closed schemas and egress allowlists** — the publication envelope rejects unknown keys; a container reaches only the hosts it is allowed to reach | publishing a private field; a blended headline number; an execution pathway existing at all | §3.1, §3.5, CD-AC-002, CD-AC-006, CD-AC-012 |
| **Named specs resolved by the engine** — a mapping is a name in a registry, executed by the engine over values the engine released; no argument accepts a callable or a model object | a caller's number entering a dial with the dial's own provenance stamped on it; a mapping with no source for static analysis to read | §3.1, §3.6, CD-AC-002, CD-AC-005 |
| **Establishment derived from the signature** — `admits` refuses on `type(value) is not declared` and refuses **any parameter it was not told about**, applied at the boundary so a rewrite of the body cannot remove it | a judgement-path entry point deciding on a value whose type it never established; a NEW argument arriving unguarded — it arrives refused | §3.1, §3.2, CD-AC-001, CD-AC-002, CD-AC-005 |

**The fourth and fifth rows arrive with BP-AMENDMENT-0001** and are the answer to what three gate
verdicts said in one sentence: *the value types are real closures, but the doors do not require
them.* The first three instruments were all read as properties of a **class**; the fourth removes
the door the class was reached through, and the fifth makes every remaining door on a judgement path
ask for its class. Read the amendment for the reasoning and for the measured denominator behind it.

Each of the five is verifiable from outside the running code: grants are readable from the store,
egress rules from the container config, schema closure from the schema file, the registry from the
run's config snapshot, and the decoration from the source — with a static check that enumerates the
judgement paths and fails on any public entry point that carries none. That matters, because the
Assurance seat must be able to check them without trusting the implementation (`PBG-EVID-001`).

Paired with each structure is a **planted violation** that must fail (`PBG-ASSURE-017`,
`PBG-CI-001`). A guard nobody has seen refuse anything is a rumour.

---

## 2. Container architecture

Seven containers on one Docker Compose project. Each exists because a boundary in the PID requires
it — none is a layering preference, and each justification is stated so the Product Owner can price
the cost.

| Container | Function | Exists because | Egress | Host ports |
|---|---|---|---|---|
| `cd-store` | PostgreSQL 16 — the durable record | roles and grants are the enforcement instrument (§4) | none | none |
| `cd-collectors` | fetch and persist **ingredient** observations | OWN COLLECTORS (PID §7) — all inputs ours | allowlist: ingredient sources only | none |
| `cd-witness` | fetch **witness** observations, build the witness panel, compute divergence | doctrine §3.4 — a witness that is also an ingredient corroborates nothing | allowlist: OFR, Quantical | none |
| `cd-engine` | compute both dials, build the public and private envelopes | the only writer of dial numbers | **none** | none |
| `cd-public` | serve the public market read | doctrine §3.5 — "not the same container" | none | 8710, loopback on DEV |
| `cd-private` | serve Matt's drill-down and anything book-adjacent | the other side of the same boundary | none | 8711, loopback on DEV |
| `cd-review` | run the one AI review, through its four validators | doctrine §3.3 — the only component with model-API egress, and it can write no number | allowlist: model API only | none |

Read the egress column as a statement about **CD-AC-012**: the engine, both surfaces and the store
have no route out of the network at all. There is nowhere for an execution pathway to go, and no
container's allowlist names a broker.

**Two networks.** `cd-net-private` carries the store, collectors, witness, engine, review and
`cd-private`. `cd-net-public` carries `cd-public` and nothing else that can reach the store's
private schemas. `cd-public` attaches to both but authenticates to the store as a role that can read
one table (§4). It is a boundary held in two independent places — network and grant — because either
one alone is a single point of failure for the product's most consequential criterion.

**Container-ready properties** (`PBG-RT-010`, `PBG-RT-012`, `PBG-RT-013`, baseline §12):
configuration from the environment only; base images pinned **by digest**, never by tag, with the
digest recorded in the build record; every process runs as a declared non-root UID; `SIGTERM`
handled with a bounded clean shutdown; logs to stdout/stderr (`PBG-OBS-002`); the three storage
classes separated — image = read-only code, tmpfs = ephemeral scratch, named volume = the store's
durable data. No process writes durable data into its own code directory.

**Deployment lane** (PID §8, Matt 2026-08-16): built on dell-debian = DEV → R2D2 ratifies → only
then PROD on cloud. On DEV both surfaces bind loopback; the public surface is not publicly reachable
from dell, and making it so is a PROD decision (§16, CD-D-006).

---

## 3. The public/private split, as a structural boundary

The PID calls this "not the same container, let alone the same page". Built, that means five
independent separations, of which any one failing still leaves four:

1. **Separate container** — `cd-public` and `cd-private` are different images with different code.
2. **Separate network** — the public surface's route to private schemas does not exist.
3. **Separate database role** — `cd_public` holds `SELECT` on exactly two tables:
   `publication.public_envelope` and `publication.witness_panel`. No grant on `dial`, `raw`,
   `private`, or `publication.private_envelope`. Revoking by default, granting by exception.
4. **Separate envelope schema** — the public envelope is a closed JSON Schema
   (`additionalProperties: false`) whose properties are an allowlist. A private field cannot be
   named in it, so it cannot be serialised into it.
5. **Publication refuses, rather than filters** — the engine validates the public envelope against
   the closed schema *before* writing it, and on any unknown or private-classified key it writes
   nothing and raises. Fail closed (`PBG-PORT-002`, baseline §8). A filter that strips private
   fields is the wrong shape: it succeeds quietly on input it should have rejected loudly.

**Planted violation for CD-AC-006:** insert a book-derived key into the envelope builder's input.
Expected: publication refuses, an alert is raised, and the previously published envelope stands
unchanged. Second plant: grant `cd_public` a read on `private.*` in a throwaway environment and
assert the automated public-artefact scan detects the resulting field. The scan runs against the
**served artefact**, fetched over HTTP from `cd-public`, not against the builder's output — evidence
independent of what it certifies (`PBG-EVID-001`).

---

## 4. Data store

**PostgreSQL 16, one instance, six roles.** The choice is derived, not preferred: the public/private
split and the witness separation are enforced by grants, and an embedded store with no role system
could not enforce either. SQLite would have made §3.3 and §6 policy again.

Schemas and their writers:

| Schema | Contents | Written by | Readable by |
|---|---|---|---|
| `raw` | ingredient observations, one row per fetch attempt including failures | `cd_collector` | `cd_engine` |
| `witness` | witness observations, same shape | `cd_witness` | `cd_witness` only |
| `dial` | computed dial readings and their history | `cd_engine` | `cd_engine`, `cd_private` |
| `publication` | `public_envelope`, `private_envelope`, `witness_panel`, `review`, `heartbeat` | see below | see below |
| `private` | anything book-adjacent | `cd_private` | `cd_private` |
| `alert` | append-only alert events | `cd_engine`, `cd_witness` | `cd_private`, health endpoint |

Grant matrix — the load-bearing part, and the thing Assurance reads directly out of the store:

| Role | Grants | Explicitly absent |
|---|---|---|
| `cd_collector` | `INSERT` on `raw.*`, `SELECT` on `raw.source_registry` | everything else |
| `cd_witness` | `INSERT` on `witness.*`, `publication.witness_panel`, `alert.event`; `SELECT` on `witness.*`, `publication.public_envelope` | `raw.*`, `dial.*` — **it cannot influence a score** |
| `cd_engine` | `SELECT` on `raw.*`; `INSERT` on `dial.*`, `publication.public_envelope`, `publication.private_envelope`, `publication.heartbeat`, `alert.event` | **`witness.*` — no grant at all**; `private.*` |
| `cd_public` | `SELECT` on `publication.public_envelope`, `publication.witness_panel` | everything else |
| `cd_private` | `SELECT` on `dial.*`, `publication.private_envelope`, `private.*`, `alert.event`; `INSERT` on `private.*` | `raw.*`, `witness.*` |
| `cd_review` | `SELECT` on `publication.public_envelope`; `INSERT` on `publication.review` | **no `INSERT`/`UPDATE` on any dial or envelope number** |

Note the shape of the witness row: `cd_witness` may read the *published* dial envelope, because
divergence detection needs both sides. `cd_engine` may not read `witness.*` at all. The permission
is a **one-way valve** — witnesses see the score after it is published; the score never sees the
witnesses. That single asymmetry is what makes CD-AC-003 true by construction rather than by test.

**Append-only where history is a claim.** `dial.history`, `raw.observation`, `witness.observation`
and `alert.event` carry no `UPDATE` or `DELETE` grant for any role. `first_published_utc` is set on
insert and cannot be moved afterwards, which is the whole of CD-AC-010's mechanism.

**Every timestamp is UTC, ISO-8601 with explicit `Z`** (`PBG-DATA-001`), stored as `timestamptz`.
Local time exists only in the display layer.

**Migrations** are append-only and forward-only, applied by a dedicated migration step that is not
the application's startup path (`PBG-DATA-002`, `PBG-DATA-003`). Each states its rollback or states
plainly that it has none.

---

## 5. Collectors — the OWN COLLECTORS ruling, built

PID §7 ratified own collectors because consuming a published artefact cross-site makes a failure
*silent*: a stale dial saying calm, which §3.2 forbids. The construction that honours it:

**A collector fetches and records. It never computes.** The boundary between "what we observed" and
"what we concluded" is the boundary between the `raw` schema and the `dial` schema, and between two
containers. No collector holds a grant that would let it write a conclusion.

**Every fetch attempt writes a row, including the failures.** This is the single most important
collector decision in the build. A failed fetch that writes nothing is indistinguishable from a
fetch that was never scheduled, and both are indistinguishable from a source that had nothing to
report — three states that demand different responses, collapsed into one absence (baseline §8:
*cannot determine* is not *determined to be absent*). So `raw.observation` carries an outcome:

```
outcome := OK(payload, source_as_of_utc)
         | FETCH_FAILED(class, http_status?)      # we could not ask
         | MALFORMED(schema_error_class)          # we asked, the answer did not conform
         | EMPTY(source_said_nothing)             # we asked, the source has nothing
```

The engine reads outcomes, not values, and the only outcome that can produce a dial contribution is
`OK`. The other three produce `Unknown` or `Degraded` — never zero, never the previous value, never
a default (§7).

**Validation at the boundary, once, against an explicit schema** (baseline §4). Each source has an
adapter declaring the response schema it accepts; a response that does not conform is stored as
`MALFORMED` with its error class, never coerced. External input is hostile, including a source that
has been reliable for a year.

**The source registry is data, not code.** `raw.source_registry` names each source, its adapter, its
cadence, and its **criticality**:

| Criticality | Meaning | Engine consequence |
|---|---|---|
| `REQUIRED` | the dial cannot be computed honestly without it | its absence forces `Unknown` or `Degraded` |
| `CONTRIBUTING` | improves the reading | its absence forces `Degraded` |
| `DISPOSABLE` | useful, never load-bearing | its absence changes nothing |

Quantical's undocumented `price_history` endpoint is registered `DISPOSABLE` (PID §7, explicit). A
constraint enforces that a `DISPOSABLE` source can never be named in a dial's required-input set —
so it cannot become load-bearing by an edit six months from now without that edit failing.

**Scheduling and idempotency.** Each adapter runs on its declared cadence with bounded timeouts and
bounded retries (baseline §11); an unbounded wait is an outage with extra steps. Re-fetching the
same source-period is idempotent on `(source_id, source_as_of_utc)` — a retry adds an observation
row, never a duplicate reading.

---

## 6. Witness layer — strictly side-by-side

The witness layer is a **parallel pipeline that shares no component with the score**, meeting it
only where the two are displayed next to each other:

```
ingredient sources → cd-collectors → raw.*      ─┐
                                                  ├─ (never joined) 
witnesses (OFR FSI, Quantical) → cd-witness → witness.*  ─┘

cd-engine     : raw.* → dial.* → publication.public_envelope    [no grant on witness.*]
cd-witness    : witness.* → publication.witness_panel           [reads published envelope, one-way]
cd-public     : serves envelope and panel as two separate sections of one response
```

The "side-by-side" in the PID is literal here: the public response is assembled at the **serving**
layer from two rows written by two different roles from two different pipelines. Nothing merges them
upstream, because no component holds the grants to.

**The panel's value type has no agreement default** (CD-AC-005):

```
WitnessPanel := Agrees(divergence_measure, as_of)
              | Diverges(divergence_measure, threshold, as_of)
              | Unavailable(reason, since_utc)
```

`Unavailable` is a distinct constructor, so it cannot be rendered by the same branch as `Agrees`.
And absence itself maps to `Unavailable`: if `cd-witness` writes no panel row at all, or writes one
older than its staleness window, `cd-public` renders `WITNESS UNAVAILABLE`. Both the explicit and
the implicit failure path land on the same honest state, and neither has a route to `AGREES`.

**Divergence is an alarm, never an adjustment** (CD-AC-004). The divergence module's return type is
`Alert | NoAlert`. It has no grant to write a dial and no function in its module returns a score. A
planted disagreement beyond threshold fires an `alert.event` row and sets the panel to `Diverges`;
the dial numbers in that same publication cycle are byte-identical to what they would have been with
no witness data at all — which is checkable, because they were computed by a process that could not
read the witness schema.

---

## 7. Dial engine

> **AMENDED AND IN FORCE — BP-AMENDMENT-0001, `the engine owns the model lifecycle`.**
> Accepted by the Product Owner at `governance/decisions/PO-DECISIONS-0005.md` (commit `b4e8eae`),
> implementing the ruling at `governance/decisions/PO-DECISIONS-0004.md` §2. The amendment is the
> design of record for the model boundary and for entry-point establishment; it is read **with**
> this section, and where the two differ the amendment governs. Its §C and §D are summarised below
> in the two clauses headed **models are data** and **doors require their value types**; the
> reasoning, the measured denominator of the admission class, the eight planted violations and the
> declared residue are in the amendment and are not repeated here.
>
> The superseded note this replaces recorded that a *proposed* amendment stood against §7 and that
> every clause below remained accepted until it was accepted. That is now discharged.

### 7.0 Models are data — the engine owns the model lifecycle

> **A computational mapping enters this system as a NAME resolved against a registry, never as an
> object supplied by a caller.** The engine resolves the name, the engine executes the mapping over
> values the engine released, and no argument exists through which a caller's number or a caller's
> code can reach a dial.

`ModelId`, `MappingKind` (a closed enum), `ModelSpec` (frozen data, no callable-typed field) and
`ModelRegistry` (exact-typed, **required on the `ConfigSnapshot` with no default**) replace the
`ContributionModel` protocol and its module-level dict, which are **deleted, not repaired**.
`DialSpec` carries `model_ref: ModelId | None` — a reference, not an object. Three snapshot
invariants join the constructor: every `model_ref` resolves; a resolved spec's `dial_id` equals the
dial naming it (**one model serves exactly one dial**, which is what closes the cross-dial route by
the shape of the data rather than by a guard that has to notice it); and a resolved spec's input ids
are a subset of the naming dial's declared inputs, each registered with an agreeing criticality.

**WO-2 ships `EMPTY_MODEL_REGISTRY` — zero rows**, on the same terms and for the same reason as
`EMPTY_SOURCE_REGISTRY`: with nothing registered, both dials read `Unknown`, which is the
doctrinally correct empty state and keeps CD-D-005 owed and visible in code. `MappingKind` ships
**non-empty with exactly one member, and that member computes nothing** — its executor path refuses
with a named error and never returns a magnitude (PO-DECISIONS-0005 ruling 2; see §16). It exists so
the snapshot invariants can be *demonstrated* rather than asserted, because a criterion that cannot
be demonstrated is a rumour.

**`evaluate` stays a pure function of its arguments** — and on stronger grounds than before. It is
pure because the executor is pure and takes no caller code, not because a model object was passed
in rather than looked up. That earlier reasoning was true and not load-bearing, and it is the
sentence ASR3-F02 was reasoned from.

### 7.1 Doors require their value types

> **Every public entry point on a judgement path establishes each of its arguments by EXACT TYPE at
> the door, and the establishment is derived from the signature rather than written into the body.**

Derived from the signature, because both escapes this project has suffered on this class were edits
to a *body*. The mechanism is the `admits` decorator (§1, fifth instrument): it refuses on
`type(value) is not declared` and refuses **any parameter it was not told about**, so a newly added
argument arrives refused rather than unguarded. The unit of work is the *class of doors*, and the
acceptance test is a static check that enumerates the judgement paths and fails on any public entry
point that is not decorated.

Two doors are closed differently in kind, and the amendment says so plainly rather than claiming
uniformity: the **collector boundary** keeps `Protocol`s for `adapter`, `sink`, `ledger` and
`validator` — things genuinely outside this system — and establishes **every value they return** on
arrival, while `clock` and `sleep` cease to be caller callables entirely; and `Reading.fold` is
**not** closed here, is WO-4, and carries its residue as CD-BP-004 in §17.

**Two dials, two evaluators, no aggregation stage.** There is no function anywhere that takes both
dial types and returns a number. Structurally:

```
EquityCrashScore        (frozen, no arithmetic dunders, no shared numeric base)
MonetaryDebasementScore (frozen, no arithmetic dunders, no shared numeric base)
DialSet := { equity: Reading[EquityCrashScore], monetary: Reading[MonetaryDebasementScore] }
```

`DialSet` is a container, not a combinator: it has no method returning a scalar. The public envelope
schema declares exactly these two dial objects with `additionalProperties: false`, so a third,
combined number has nowhere to be published even if someone computed one.

**Planted violation for CD-AC-002:** add `combined_stress = (equity + monetary) / 2`. It fails
**four** times, and the first refusal is structural: **there is no door through which a caller's
mapping can reach a dial at all** — no field holds an object, so the blend has nowhere to be
computed with the dial's own provenance stamped on it. Then the three that already stood: the types
reject the operator, the register's AST check flags a single expression consuming both dial types
outside the allowlisted container and serving layer, and the closed envelope schema rejects the new
key. Four independent refusals for a criterion the PID marks Constitutional, and the amendment's
§E walks the auditor's own replicated plant through each of them.

**The computation core is a pure function.**

```
evaluate(observations, config_snapshot, now_utc) -> DialSet
```

No I/O inside it. I/O happens at the edges — read observations, call `evaluate`, write the result.
This is not tidiness: it is what makes CD-AC-003's "byte-identical with witnesses unreachable" a
cheap, repeatable check rather than an environment exercise, and it makes every historical reading
reproducible from its stored inputs.

**Configuration that affects a result is snapshotted per run** (baseline §10). Every `dial.history`
row references the `config_snapshot_id` that produced it, so a reading can be explained a year later
without archaeology. Thresholds, weights and windows are configuration, external to the logic
(`PBG-SEC-001`) — never literals in the computation.

**Absence has one representation, and it is not a number** (CD-AC-001):

```
Reading[T] := Value(T, as_of_utc, inputs_used)
            | Degraded(T, as_of_utc, missing_inputs, reason)
            | Unknown(reason, since_utc, missing_inputs)
```

There is no `Optional[float]` and no zero default anywhere in the dial path. `Degraded` still
carries a value, but it is a *different constructor* — a rendering layer must decide what to do with
it, and cannot accidentally paint it as a clean reading. The register forbids, by AST check over the
dial path: `float | None` annotations, `.get(key, <numeric literal>)`, `or 0`, and bare `except`
returning a default.

**Regime-aware staleness** (CD-AC-009). The staleness window is a function, not a constant:
`window_for(regime) -> seconds`, tightening as observed volatility rises. The regime is computed
from the engine's own ingredients, carried in the envelope alongside `as_of_utc` and the window that
was applied, so every consumer judges freshness by the same declared rule. The planted check is
exactly the PID's semantics: the same observation age passes in calm and fails in stress.

**The oil transient maturation rule** (PID §9.6) is implemented correctly here rather than ported
from ARGUS with its defect. Its maturation state is explicit in the reading's `inputs_used`, because
the ~+0.20 of suppressed stress contribution is precisely what must not travel silently.

---

## 8. Publication layer

The engine builds two envelopes per cycle and validates each against its own closed schema before
writing. `cd-public` and `cd-private` **serve** — they read one row and render it. They compute no
dial value, hold no evaluation code, and have no grant that would let them.

**Drill-down proportional to risk** (PID §4) is a property of the envelope, not of a front end: the
envelope carries `detail_level` derived from the reading itself — calm emits the dial and one line;
elevated emits the contributing categories; acute emits everything ranked by contribution. The
surfaces render what they are given, so the proportionality rule lives in one place and is testable
without a browser.

**Every envelope carries its own honesty fields**, and the schema marks them `required`, so an
envelope cannot be published without them: `schema_version`, `as_of_utc`, `published_utc`, `regime`,
`staleness_window_seconds`, `inputs_used`, `degraded_inputs`, `config_snapshot_id`.

**Cadence, monitored on the publication layer** (CD-AC-008, PID §4 explicitly — monitor publication,
not only ingestion). Each successful publish writes `publication.heartbeat`. A cadence breach is an
excessive **interval between heartbeats**, not the age of a number, and it alerts within one
publication cycle. The check that detects it runs **outside the container set** — a process inside
the system reporting that the system is publishing is self-certification (`PBG-EVID-001`,
`PBG-DEPLOY-002`). The external probe reads the health endpoint and is what satisfies the PID §5
budget of independent detectability within 15 minutes.

**History is honest** (CD-AC-010). `dial.history` rows carry `first_published_utc`, immutable by
grant, and a `provenance` of `LIVE` or `BACKFILL`. The live series endpoint emits `LIVE` rows only;
backfilled points are available exclusively through a separately named, separately labelled series.
Because `provenance` is a required field on the row type, a backfilled point cannot lose its label
on the way to a chart.

**Slope is first-class** (CD-AC-011). `/series/{dial}` returns the points, the declared window, and
the slope against the S&P in machine-readable form — the PID's "the signal is in the slope, not the
level", built as a first-class field rather than left to a viewer's eye.

**Rotation-readiness ratio** (CD-AC-013) publishes as an object whose schema marks its provenance
block `required`: the named inputs and their timestamps. It cannot publish bare.

---

## 9. AI review

One review, two questions — what changed, is the plan still fit — and **zero authority over headline
numbers** (doctrine §3.3). Built:

`cd-review` reads the published public envelope and writes `publication.review`. Its role holds no
`INSERT` or `UPDATE` on any dial or envelope number, so the authority limit is a grant, not an
instruction. Its output type contains no numeric dial field, so there is nothing for a headline to
be written into.

Before admission, four validators run against the review text, each with its own planted violation
in the register (CD-AC-007): `no_headline_authorship`, `no_crash_certainty`, `no_market_is_safe`,
`no_missing_data_as_safety`. A review failing any validator is rejected and recorded as rejected —
it is not silently trimmed, because a trimmed output hides the fact that the model tried.

---

## 10. Observability, health and alerting

**Liveness and readiness are separate** (`PBG-OBS-003`, baseline §13). Liveness: the process
functions. Readiness: it can serve now — for `cd-public`, that its envelope row is present and
within its staleness window. A probe that returns 200 because HTTP is up while its dependency is
unreachable manufactures confidence, so each readiness probe tests the dependency it actually needs,
cheaply, boundedly, without side effects.

**Runtime health is externally observable** (CD-AC-014): an unauthenticated health surface exposes
liveness, `last_publication_utc`, `last_evaluation_utc`, current `regime`, and degraded state. That
is detector health, not market information and not book information, so it is public-safe. Stopping
the service is detected by the external probe inside the PID §5 budget.

**Alerts are durable rows first.** `alert.event` is append-only; cadence breach, witness divergence
and publication refusal all write there. Notification transport is deliberately not fixed in this
Blueprint — it is a Level 1 implementation choice I will settle in WO-3 against whatever channel
Matt actually reads, and the durable row means no alert is lost while that is decided.

---

## 11. Configuration, secrets and build identity

Configuration is external to application logic and read from the environment (`PBG-SEC-001`,
baseline §12). No host-specific absolute path, no config file expected at a fixed location outside
the app's own tree.

**Secrets are referenced, never reproduced** (`PBG-SEC-002`, `PBG-EVID-003` — non-waivable, and
`PBG-CONT-009`). Source-API keys and the model API key are read from the environment at point of
use, named by identifier in every record, and never logged, never in a fixture, never in evidence.
No governed record in this project will carry a secret value.

**Dependencies pinned to exact versions with a committed lockfile** (`PBG-CI-003`, baseline §6), and
deliberately few. Base images pinned by digest; a tag-only base image reference fails the register.
A clean environment builds the application from declared sources alone (`PBG-SEC-004`), with no
network-dependent build step that can drift.

---

## 12. Recovery

CD-AC-015 asks for recovery **proved from the copy**, which is a stricter thing than a backup
existing. The store's durable volume is dumped on a schedule to a separate volume; recovery is
demonstrated by restoring that dump onto a clean host and reading the proof **out of the restored
copy** — never out of the original. A backup that has never been restored is a hypothesis
(baseline §14).

Raw observations are retained in full at v1 volumes; retention is a Level 1 decision I will revisit
with real volume data rather than guess now, and the append-only grants mean revisiting it is a
policy change, not a data-loss risk.

---

## 13. The doctrine-bearing criteria, structural from the first commit

The dispatch names five. Each row states the structure, and the planted violation that proves the
structure bites. All five land in **WO-2**, before any of them has a feature to attach to.

| Criterion | The structure | The planted violation that must fail |
|---|---|---|
| **CD-AC-001** missing/stale never calm | `Reading` sum type with no numeric default; collectors record `FETCH_FAILED`/`MALFORMED`/`EMPTY` as first-class outcomes; absent or stale envelope renders `UNKNOWN` at the serving layer; AST check bans `float \| None`, `or 0`, `.get(k, 0)` in the dial path | kill a feed → dial must show `UNKNOWN`/`DEGRADED` within budget; separately, introduce a numeric default in the dial path → the AST check must refuse it |
| **CD-AC-002** dials never blended | **no door: models are named specs the engine resolves, and one spec serves exactly one dial — no argument accepts a callable or a model object** (BP-AMENDMENT-0001 §C); two unrelated frozen types with no arithmetic and no common numeric base; `DialSet` is a container with no scalar method; public envelope schema closed to a combined field | add `combined = (equity + monetary)/2` → must fail **structurally first** (there is no field to place a mapping in, and no `ModelSpec` may name two dials), then at the type level, at the AST check, and at the envelope schema |
| **CD-AC-003** witnesses side-by-side | `cd_engine` holds **no grant** on `witness.*`; separate container, separate pipeline; composition happens only at the serving layer | compute with the witness store unreachable → dials byte-identical; grant the engine a witness read → a register check on the live grant matrix must fail |
| **CD-AC-005** unavailable ≠ agrees | `WitnessPanel` sum type with `Unavailable` as a distinct constructor; absent or stale panel row maps to `UNAVAILABLE` at the serving layer; **plus the `admits` door — `resolve_panel` requires exactly `PanelRow`, so a duck row whose `state` property answers `AGREES` while its stored state is `UNAVAILABLE` is refused at the boundary** (BP-AMENDMENT-0001 §D) | kill the witness feed → panel shows `WITNESS UNAVAILABLE`; delete the panel row entirely → same result, never `AGREES`; **hand `resolve_panel` a duck row → refused by `admits`, and add an undeclared parameter to a decorated door → refused on every call** |
| **CD-AC-012** no execution pathway | no container's egress allowlist names a broker; engine and both surfaces have **no egress at all**; no order/execution interface in source; no credential of that class in the config surface; lockfile scanned against a broker-SDK denylist | add a `place_order` stub, or a broker SDK to the lockfile, or a broker host to an allowlist → each must fail the register independently |

The public/private split (CD-AC-006) deserves a note against CD-D-004, which sequences its
*enforcement evidence* at step 5. The **boundary itself is built in WO-2** — containers, networks
and grants are structural from the first commit, because retrofitting a trust boundary is how trust
boundaries end up leaky. What lands at step 5 is the planted-violation evidence and the automated
public-artefact scan. I am flagging this so the Product Owner sees that I am building the boundary
earlier than the criterion is scheduled, not reordering their sequence.

## 14. Full criterion trace

| ID | Where it lives | Delivered in |
|---|---|---|
| CD-AC-001 | §5 outcomes, §7 `Reading`, §8 serving, §7.1 `admits` on the serving door | WO-2 |
| CD-AC-002 | §7.0 model registry and one-dial binding, §7 types, envelope schema | WO-2 |
| CD-AC-003 | §4 grant matrix, §6 pipeline separation | WO-2 |
| CD-AC-004 | §6 divergence module | WO-4 |
| CD-AC-005 | §6 `WitnessPanel`, §7.1 the `admits` door on `resolve_panel` | WO-2 |
| CD-AC-006 | §3 five separations | boundary WO-2, evidence WO-5 |
| CD-AC-007 | §9 validators | WO-5 |
| CD-AC-008 | §8 heartbeat, §10 external probe | WO-3 |
| CD-AC-009 | §7 `window_for(regime)` | WO-3 |
| CD-AC-010 | §4 immutable `first_published_utc`, §8 provenance | WO-4 |
| CD-AC-011 | §8 series and slope | WO-4 |
| CD-AC-012 | §2 egress, §13 | WO-2 |
| CD-AC-013 | §8 rotation ratio | WO-6 |
| CD-AC-014 | §10 health surface | WO-3 |
| CD-AC-015 | §12 restore from the copy | WO-6 |
| CD-AC-016 | §8 envelope section | WO-6 |
| CD-AC-017 | §7.1 the `admits` doors, §17 `CD-BP-005`'s RESISTED tier — **admission on every judgement path admits only objects of provenance from a declared door (the RESISTED tier)** | WO-3 |
| CD-AC-018 | §8 publication boundary, §6 divergence, §17 `CD-BP-005`'s DETECTED tier — **the publication boundary raises DIVERGENCE between a released number and its corroborating witnesses (the DETECTED tier)** | WO-3/WO-4 |

The Required Test Register derives its population from PID §6 and is compared against it
(`PBG-RT-001`); it is created in WO-2 and every row above becomes a register entry.

> **PROJECT LEAD DISCLOSURE, not product meaning — these are the Project Lead's own bytes and they
> are enumerated as such in §19.** `CD-AC-017` and `CD-AC-018` are the Product Owner's, minted at
> PO-DECISIONS-0019 ruling 3 — *"Two new acceptance criteria are minted"* — and carried above
> verbatim. They are **not in PID §6**, and the
> sentence immediately above is therefore not yet true of them: the register row each of them owes
> **cannot be written until the Product Owner amends PID §6**. That obstacle is MEASURED, not
> asserted — `pbg/tools/pbg/required_tests.py` computes the census from the PID alone and returns
> *"NEW_REQUIREMENT is blocked pending PO amendment of the PID"*. It is recorded as an **open
> Product Authority question** at `BL-20260823T124508Z-0135` and is answered by no seat.

---

## 15. Delivery order

CD-D-004 fixed the order; the decomposition inside it is mine. Each work order is a bounded Engineer
dispatch followed by a **separate** Assurance dispatch — never the same agent (`PBG-SOD-001`,
non-waivable) — on its own branch and worktree (`PBG-GIT-003`), with a Build Log checkpoint at each
boundary.

| WO | Content | Criteria | Gate |
|---|---|---|---|
| **WO-1** | this Blueprint; pre-commit hook commissioned | — | Product Owner acceptance of the Blueprint |
| **WO-2** | repository skeleton, container set, store schema and grant matrix, dial types, collector framework and source registry, Required Test Register, the five planted violations of §13 | 001, 002, 003, 005, 012 | Assurance PASS on all five planted violations failing correctly |
| **WO-3** | publication layer, heartbeat, external probe, regime-aware staleness, health surface; **a CONSTRUCTION-PROVENANCE door at admission** (`CD-AC-017`, §17 RESISTED tier); **the publication boundary raising DIVERGENCE** (`CD-AC-018`, §17 DETECTED tier) | 008, 009, 014, **017**, **018** | Assurance PASS; public-surface change → external R2D2 review (PID §8) |
| **WO-4** | witnesses live, divergence alarm, history and slope; **`CD-AC-018` completes here as the witnesses land** | 004, 010, 011, **018** | Assurance PASS |
| **WO-5** | public/private split evidence, AI review and its four validators | 006, 007 | Assurance PASS **and** external R2D2 — doctrine-bearing controls, PID §8 |
| **WO-6** | rotation-readiness ratio, recovery proof from the copy, wave-transition monitor | 013, 015, 016 | Assurance PASS |

Nothing in WO-2 begins until the Product Owner accepts this Blueprint (CD-D-004.1).

---

## 16. What this Blueprint deliberately does not decide

Two questions turned out to be product content, not construction. Under `PBG-AUTH-003` I will not
resolve either, and under `PBG-AUTH-005`/`PBG-AUTH-006` each carries a recommendation, a default
safe action, and what continues meanwhile.

**CD-D-005 — the ingredient set: which inputs feed each dial.** The PID names the witnesses (OFR
FSI, Quantical) and rules Quantical's `price_history` disposable, but it does not enumerate the
*ingredients*. Choosing them is choosing what the dial means, and doctrine §3.6 forbids unexplained
mappings — so this is the Product Owner's register, not my inference from the ARGUS implementation
(`PBG-PID-003`: existing code is evidence of current implementation, not authorised intent).
*Recommendation:* the Product Owner issues an ingredient register per dial — source, what it stands
for, criticality — which becomes rows in `raw.source_registry`.
*Default safe action:* **WO-2 proceeds regardless.** The skeleton is structurally complete with zero
ingredient sources registered, and with none registered every dial correctly reads `UNKNOWN` — which
is the doctrinally right answer and makes CD-AC-001's first plant trivially demonstrable. The
ingredient register is needed before WO-3, not before WO-2.

**CD-D-005 NOW ALSO OWES THE MODEL REGISTRY ROWS** (BP-AMENDMENT-0001 §F.3, accepted at
PO-DECISIONS-0005). Since §7.0 makes a mapping a *named spec resolved against a registry*, the
contents of `ModelProvenance` — source, what it stands for, criticality, and the account of the
mapping that doctrine §3.6 requires — and the **members of `MappingKind`** are product meaning and
belong to the same register. The shape of both is construction and is mine; the contents are not.

**AND THE OWED LIST NOW CARRIES A MEASUREMENT THAT FALLS DUE ON THE SAME DAY** (PO-DECISIONS-0014
ruling 3, added by the Project Lead at BL-20260823T014454Z-0115 as ordered — documentary, and it
moves no product decision): **the acceptance of the first computing `MappingKind` member re-runs the
`*extra` guard measurement at the then-current head.** WO-2R3 increment 7 measured that the CD-ASR-F03
post-condition binds **none** of `_evaluate_dial`'s `*extra` / `**extra_by_name` structurally, and
that nothing passed through them can change what the evaluator returns **only because every
`MappingKind` member raises in `compute`**. That is a PRODUCT GAP holding the hole shut, not a guard —
and it expires on exactly the day this list is read. The measurement is owed *before* that member is
accepted, not after.

*Default safe action, unchanged and now stated in two places:* WO-2 ships **zero registry rows** and
every dial reads `UNKNOWN`. **`MappingKind` ships with exactly ONE member, and that member computes
nothing** (PO-DECISIONS-0005 ruling 2): its executor path refuses with a named error and never
returns a magnitude, so no weights and no mapping semantics ship. It exists only so the snapshot
invariants can be demonstrated rather than asserted. **The first COMPUTING member arrives only with
the CD-D-005 register, by amendment to this list** — a seat that adds a second member without it is
inventing product meaning (`PBG-AUTH-005`, CD-RULE-003).

**CD-D-006 — the public exposure route.** Domain, hosting and what fronts `cd-public` in PROD.
*Recommendation:* decide at R2D2 ratification, not now; the PID's lane (dev never on cloud, prod
never on dell) means it cannot be settled from DEV anyway.
*Default safe action:* both surfaces bind loopback on DEV throughout WO-2 to WO-6. Nothing is
publicly reachable until Matt says so.

**CD-D-172 — THE FORGERY-DETECTION OBLIGATION. THE PERIMETER IS DECLARED, NOT PRETENDED.**
Added at BL-20260823T095521Z-0131 on the Product Owner's own ruling, PO-DECISIONS-0018 ruling 1
(commit `c72b6ea`, authored by Matt Scott and by no seat), which ordered in terms: *"BLUEPRINT §17
gains the risk row and §16 gains the owed control."* **The sentences below are the Product Owner's
own bytes, carried verbatim and not paraphrased**, because this file is protected from every seat
including the Project Lead (`CD-D-115`) and a perimeter declaration written in a seat's words would
be a seat inventing product meaning.

Seven gates and two programmes taught one sentence, and the Product Owner wrote it down:

> *"an enumeration cannot close a property-defined class — and this class is defined by a platform
> property we do not control."*

The honest architecture is in three parts, and all three are the Product Owner's words:

> **(a)** *"The declared-route refusals STAND and are kept — they are real, they refuse the front
> door and the named routes, and they proof the product against ACCIDENT and against casual misuse.
> That is worth having and it is what they honestly are."*
>
> **(b)** *"SEALED means sealed against declared routes; NOT sealed against deliberate in-process
> forgery, which the platform does not permit preventing. A green board that says exactly that is
> honest; a green board that says more is the sixth false green."*
>
> **(c)** *"The defence against deliberate in-process forgery is DETECTION, and it already has a
> home. This is the estate's own settled doctrine arriving at its own product: prevention where
> blast radius is catastrophic (Layer 3, out-of-process, where the money gate lives — D2 untouched);
> detection everywhere else. The PID already says it: external sources are WITNESSES, never
> ingredients — DIVERGENCE IS THE ALARM. A forged magnitude that reaches publication must diverge
> from what the witnesses corroborate or be caught by the provenance chain; BLUEPRINT §17 gains the
> risk row and §16 gains the owed control: the FORGERY-DETECTION OBLIGATION, specified at WO-3 when
> real sources land, verified as a first-class criterion. The detector is ADVISORY (D1) and no money
> moves on it (D2); the perimeter now says truthfully what is prevented, what is detected, and what
> is out of scope — and the eighth seat grades against THAT, which is a gradeable claim."*

*What is therefore OWED, and it is an owed CONTROL and not an owed opinion:* **the
FORGERY-DETECTION OBLIGATION is specified at WO-3, when real sources land, and is verified as a
FIRST-CLASS CRITERION**. Its
two named mechanisms are **witness divergence** and the **provenance chain**. It cannot be specified
before WO-3 because with zero registry rows there are no witnesses to diverge from, which is the
same reason CD-D-005's register is owed there and not here.

> **`CD-ASR-WO2R3-05-F05` IS REPAIRED HERE, AT v0.4.1, BY THE ONLY HAND THAT MAY.** The normative
> sentence that closed the paragraph above — *"not as a note, not as a residue paragraph, and not as
> a manual step"* — is **REMOVED**, and it is removed on the Product Owner's own order, in the
> Product Owner's own words, carried verbatim from PO-DECISIONS-0020 ruling 2 (commit `abafec2`,
> authored by Matt Scott and by NO seat):
>
> *"**Q6 — F05 IS REPAIRED HERE, by the only hand that may.** The normative sentence "not as a note,
> not as a residue paragraph, and not as a manual step" is MY prose that landed in BLUEPRINT.md,
> which CD-D-115 protects from every seat including me-via-a-seat — so no Engineer could remove it
> and none should have tried. I remove it now, at the PO layer, and replace it with the correct
> pointer: the requirement that the forgery-detection obligation take a scheduled criterion form now
> LIVES as CD-AC-017/CD-AC-018 in the PID and the register (ruling 1), which is where a normative
> requirement belongs — not as loose prose in the Blueprint's risk section. The Blueprint §17 row
> keeps its RISK/HANDLING columns and CITES the two criteria; it no longer carries the normative
> sentence about their form. F05 is discharged; F03 (the record carrying the obligation in a
> forbidden form) is discharged by the same act, because the obligation now has the required form."*
>
> **THAT IS THE POINTER, AND IT RESOLVES:** the scheduled criterion form now lives as
> **`CD-AC-017`** (PID §6 `NEW_REQUIREMENT`, §14, §15 WO-3) and **`CD-AC-018`** (`STRENGTHENS
> CD-AC-004`, §14, §15 WO-3/WO-4) — **at 3/4 of the `CD-D-172` form and carried as 3/4, because the
> register row is a WO-3 artefact and does not exist today.** **`F05` and `F03` are DISCHARGED by
> this act and by no seat's judgement.** **ONE DISCREPANCY IS DISCLOSED RATHER THAN SILENTLY
> RESOLVED:** the ruling calls this "the Blueprint's risk section" and the dispatching brief called
> it §17, but the removed bytes occurred exactly ONCE in this file and they occurred **here, in
> §16** — so the bytes governed the target and the section label did not. §17's `CD-BP-005` row was
> read and left untouched; it already cites both criteria, which is what the ruling requires of it.

*Default safe action meanwhile:* **unchanged, and it is already load-bearing.** The detector is
ADVISORY (`D1`) and no money moves on it (`D2`), so the blast radius of a forged magnitude at WO-2
is a wrong number on an advisory board and not a transaction. The declared-route refusals continue
to do the accident-proofing they honestly do.

Level 1 choices I have taken rather than escalated, listed so they are visible and reversible:
Python for the application; PostgreSQL for the store (derived in §4); seven containers as justified
in §2; alert transport deferred to WO-3 (§10); raw retention revisited on real volume (§12).

---

## 17. Risks carried into WO-2

| ID | Risk | Severity | Handling |
|---|---|---|---|
| CD-FWK-001 | seat attestations unusable in a vendored layout | AMBER | dispositioned CD-D-002 — `PBG-SOD-001` evidenced by named `actor_id` on every seat; Engineer and Assurance dispatches carry distinct actor identities |
| CD-FWK-002 | `PBG-CONT-003` and `PBG-SOD-001` verifiers `NOT_YET_RUN` | AMBER | both clear during WO-2 — the first Engineer/Assurance pair evidences separation, the accumulating Build Log evidences append-only |
| CD-FWK-003 | `pbg log` / `pbg resume` vacuous GREEN at the wrong root | AMBER | carried to the PBGv2 backlog by the PO; continuity on this project is verified through `pbg boot` only |
| CD-BP-001 | the AST-based register checks (§7, §13) are the one novel instrument here and could be brittle or evadable | LOW | they are never the sole guard — every criterion in §13 has at least two independent refusals, and the AST check is the cheapest, not the strongest, of them |
| CD-BP-002 | **the executor is now the single highest-value target in the product** — after BP-AMENDMENT-0001 it is the only place a dial number is computed. The concentration is deliberate (one place with source beats seven doors without) but it is a risk, not a win, and a `MEAN` that is not a mean is a defect this architecture does not prevent — it makes it *have source* | MEDIUM | stated in the amendment's §E residue rather than glossed; the mapping has source, so static analysis and review reach it, and every member of `MappingKind` is added deliberately and visibly with CD-D-005 provenance behind it |
| CD-BP-003 | **the collector's adapter boundary admits by protocol and is the softest remaining surface.** `adapter`, `sink`, `ledger` and `validator` are genuinely foreign, so exact-typing them is not available; the closure is that every value they RETURN is established on arrival. That is a door that admits, not an absence of a door — weaker in kind than §7.0's | MEDIUM | declared as a limit rather than hidden (amendment §D.3); **named by the Product Owner as the fourth Assurance seat's first target** (PO-DECISIONS-0005 ruling 4) |
| CD-BP-004 | **a consumer's `fold` with an `on_unknown` returning `0.0` renders absence as a number**, with the `Reading` sum type wholly intact — CD-AC-001's failure mode reached outside the governed boundary | MEDIUM | ruled WO-4, not WO-2R3 (PO-DECISIONS-0005 ruling 3), because the envelope schema and not `fold` is the structural refusal for what actually publishes. Carried here **and** named in WO-4's scope on day one, on the Product Owner's condition that a residue this amendment made visible does not become invisible by being deferred |
| CD-BP-005 | **DELIBERATE IN-PROCESS CONSTRUCTION OF A FORGED OBJECT CANNOT BE PREVENTED.** An actor already executing inside the process can construct an object of a governed exact type with a forged value, executing ZERO package lines — `cls.__new__(cls)` + `object.__setattr__`, and `type.__new__(<metaclass>, ...)` for the type itself. `object.__setattr__` and `type.__new__` are CPython working as documented. Seven gate verdicts, forty measured forgeries at `686a374` and a HIGH live control bypass (`CD-ASR-WO2R3-04-F01`) established it; appending a refused route to the census produced a false green five times. **CORRECTED AT v0.4.0 BY THE PRODUCT OWNER (PO-DECISIONS-0019 ruling 2), whose own bytes state the correction:** *"the platform does not permit preventing it" is RETRACTED, and the reason is that ADMISSION WAS NEVER TESTED.* *Construction cannot be prevented — measured three times, that stands. But admission is a different predicate, and a construction-provenance discriminator at admission is available and measured.* *The corrected text rests on that measurement, not on an assertion.* | **HIGH, ACCEPTED AND DECLARED** | **the perimeter is DECLARED, not pretended** (PO-DECISIONS-0018 ruling 1, quoted verbatim in §16), **and at v0.4.0 it is CORRECTED to what was MEASURED — PO-DECISIONS-0019 ruling 1, the Product Owner's own bytes carried verbatim: *"The perimeter is restated as THREE TIERS, because two was the error"*.** **PREVENTED (accident + casual misuse):** *the declared-route refusals and the front door, exact-type admission — non-vacuous, proved by a refusing arm. Stops the forged SUBCLASS (F2) and every accident. Says exactly that and no more.* **RESISTED (deliberate in-process forgery, F1) — OWED, NOT BUILT.** A construction-provenance discriminator at admission is the specified mechanism (CD-AC-017), and it is **not yet built and, as first measured, insufficient alone**: a value forged AFTER admission defeats it at zero cost. Until CD-AC-017 is built AND shown to bind post-admission mutation, the F1 route is carried by the **DETECTED** tier (CD-AC-018, witness divergence at publication) as the load-bearing defence, with admission-provenance as defence-in-depth, not the primary. Verified at WO-3 when real sources land. **Scheduled as `CD-AC-017`** (§14, §15 WO-3). **DETECTED (the residual, and the catastrophic-blast case):** *witness divergence + provenance, at the publication boundary — the backstop for what admission-time resistance does not hold, and the only defence where blast radius forbids relying on any in-process control (Layer 3 territory, D2 untouched).* **Scheduled as `CD-AC-018`** (§14, §15 WO-3/WO-4). **Blast-radius basis: the detector is ADVISORY (`D1`) and no money moves on it (`D2`).** **Every instrument reporting SEALED must carry this limit in its own exit text; a verdict that claims more is the defect** (PO-DECISIONS-0018 ruling 1b) |

---

## 18. Reconciliation record

| Item | Value |
|---|---|
| Reconciled against SHA | `c291f80057119dcbe610e365350159414547b65a` |
| Reconciled against | PID.md v1.0.1 · PO-DECISIONS-0001.md · pinned PBGv2 v2.0.0-alpha.1 |
| Observed UTC at authoring | 2026-08-18T17:58:26Z |
| Runtime verified | **nothing** — no application runtime exists yet. Every statement in this document is design intent, not a runtime observation (`PBG-DEPLOY-007`) |
| Authored by | PROJECT_LEAD under CD-AUTH-0001 |
| Verified by | **not yet** — Assurance verification is a separate artefact from this document (`PBG-BP-001`, `PBG-BP-004`) |

Currency is computed by comparing `last_reconciliation_sha` to HEAD (`PBG-BP-003`), never read from
a written date.

## 19. Amendment log

| Version | Date (UTC) | By | Change |
|---|---|---|---|
| 0.4.2 | 2026-08-23 | **Product Owner (the corrected tier text); Project Lead (the version bump, the status paragraph, this row, the retained scheduling clause)** | **THE `RESISTED` TIER IS CORRECTED TO FUTURE TENSE AND ITS LOAD MOVES TO DETECTION — PO-DECISIONS-0022 ruling 2, applied and NOTHING ELSE.** The ninth Assurance seat's `CD-ASR-WO2R3-06-F02` is **ACCEPTED AND NOT CONTESTED**, and the Product Owner's own words state why: *"provenance-at-construction cannot stop post-admission mutation, so the tier as written claims a resistance it does not have. §17's present-indicative RESISTED row is WRONG where §16 already concedes it is a specification."* The v0.4.0 row — *a CONSTRUCTION-PROVENANCE door ... defeatable only by locating and mutating a module-private structure* — is REPLACED by the PO-authored **OWED, NOT BUILT** text, in which `CD-AC-017` is the **specified** mechanism, is **not yet built and, as first measured, insufficient alone**, and the F1 route is carried by the **DETECTED** tier (`CD-AC-018`, witness divergence at publication) **as the load-bearing defence, with admission-provenance as defence-in-depth, not the primary**. **THE TIER IS NOT WITHDRAWN — the mechanism is still owed and real; its TENSE is corrected to match the truth.** **CARRIAGE VERIFIED BY COMMAND AND NOT BY ASSERTION** — `python3 -B tools/reconciliation/check_blueprint_carried_po_0022_verbatim.py --root .` -> EXIT 0, ARM 1 4/4 sentences in BOTH files (571 normalised chars), ARM 2a the superseded fragment ABSENT from §17, ARM 3 the supersession measured **EXACTLY ONE SENTENCE WIDE** against the 0019 check's own table; `--counterfactual` -> EXIT 1, 5 failures. **THREE THINGS THIS VERSION DOES NOT DO, DISCLOSED RATHER THAN HIDDEN. (1) `check_blueprint_carried_po_0019_verbatim.py` NOW EXITS 1 AT 9/10 — 1911 -> 1230 normalised characters, a drop of 681, EXACTLY the superseded sentence's measured length. IT WAS NOT EDITED AND MUST NOT BE: a sibling check going RED on precisely the sentence a later ruling corrected IS the standing evidence that the v0.4.0 text existed and was superseded by the Product Owner and not by a seat.** **(2) It does not build `CD-AC-017` and does not move it — the criterion stays 3/4 of the `CD-D-172` form, the register row still does not exist, and nothing here rounds it up.** **(3) It does not touch `CD-AC-002` or `CD-AC-005`, whose standing remains AMBER and RED respectively (PO-DECISIONS-0022 ruling 6), and it does not touch the `wo-2r3` lane, frozen at `be0b355` behind a SHUT gate.** |
| 0.4.1 | 2026-08-23 | **Product Owner (the removal); Project Lead (the version bump, this row, the disclosure)** | **`CD-ASR-WO2R3-05-F05` REPAIRED — AND THE REPAIR IS A REMOVAL.** PO-DECISIONS-0020 ruling 2 (commit `abafec2`, authored by Matt Scott and by NO seat) removes from §16 the normative sentence *"not as a note, not as a residue paragraph, and not as a manual step"*, on the Product Owner's own stated reason: *"is MY prose that landed in BLUEPRINT.md, which CD-D-115 protects from every seat including me-via-a-seat — so no Engineer could remove it and none should have tried."* In its place stands a POINTER, quoted verbatim from the ruling, to where the requirement now lives: **`CD-AC-017`** (PID §6, entered as `NEW_REQUIREMENT` by the PO's amendment of the PID to v1.1.0) and **`CD-AC-018`** (`STRENGTHENS CD-AC-004`, homed in the register's `pid_relation` at WO-3). **`F03` IS DISCHARGED BY THE SAME ACT** — the obligation now has the required form rather than the three forms `CD-D-172` forbids. **§17 `CD-BP-005` IS UNTOUCHED**: read, and left exactly as v0.4.0 wrote it, keeping its RISK/HANDLING columns citing both criteria, which is what the ruling requires of it. **WHAT THIS VERSION DOES NOT DO, DISCLOSED RATHER THAN HIDDEN: it does not reach 4/4 of the `CD-D-172` form for either criterion. The register row does not exist — `required-tests.yaml` lives on the `wo-2r3` lane at `be0b355`, the lane is frozen at a SHUT gate, and the row is reachable at WO-3. Both criteria are carried as 3/4 in every place this boundary writes them, on the Product Owner's explicit instruction: *"Until the register rows exist they are 3/4 and MUST be carried as such, never rounded up."*** **AND ONE DISCREPANCY IS DISCLOSED RATHER THAN SILENTLY RESOLVED:** the ruling locates the sentence in *"the Blueprint's risk section"* and the dispatching brief said §17, but the named bytes occurred exactly ONCE in this file and occurred in **§16**. The bytes governed the target; the section label did not. **CARRIAGE VERIFIED BY COMMAND AND NOT BY ASSERTION** — `python3 -B tools/reconciliation/check_pid_carried_po_0020_verbatim.py --root .`, with a counterfactual arm proving the check can fail. |
| 0.4.0 | 2026-08-23 | Project Lead, **carrying the Product Owner's own bytes** | **THE PERIMETER IS CORRECTED TO WHAT WAS MEASURED — PO-DECISIONS-0019 rulings 1, 2 and 3 (authored by Matt Scott and by no seat), applied and NOTHING ELSE.** The eighth Assurance seat's `RED` was upheld in full, **including `F02` and `F05`, both of which were aimed at bytes this seat authored in this protected file**, and this row records the correction rather than the defence. **§17 `CD-BP-005` is restated as THREE TIERS and not two**: PREVENTED (the forged SUBCLASS `F2` and every accident — *"Says exactly that and no more"*); **RESISTED** (`F1`, via *a CONSTRUCTION-PROVENANCE door — "did this object leave a declared door?"*, whose defeat is measured, hence resisted and not prevented, **with the measured `WeakSet`/`__slots__` obstacle OWNED IN THE TEXT rather than glossed**); DETECTED (witness divergence + provenance at the publication boundary). **The word "useless" is STRUCK** — `F02` proved it false for the very route the risk column names first. **The assertion "AND THE PLATFORM DOES NOT PERMIT PREVENTING IT" is RETRACTED**, on the Product Owner's own reason: *"ADMISSION WAS NEVER TESTED"* — construction cannot be prevented and that stands, but admission is a different predicate. **§14 and §15 gain `CD-AC-017` (admission by declared-door provenance, RESISTED tier, WO-3) and `CD-AC-018` (publication divergence, DETECTED tier, WO-3/WO-4)**, which answers `F03`: the obligation now has an ID, a §14 trace row and a §15 work order, and is no longer carried in the three forms `CD-D-172` forbids. **THE CARRIAGE IS VERIFIED BY COMMAND AND NOT BY ASSERTION** — `python3 -B tools/reconciliation/check_blueprint_carried_po_0019_verbatim.py --root .`, with the counterfactual arm proving the check can fail. **This file is protected from every seat including the Project Lead (`CD-D-115`); the authority for the carriage is the ruling's own instruction that the corrections *"are mine to author ... and are authored here for verbatim carriage"*. THE PROJECT LEAD'S OWN AUTHORED BYTES ARE EXACTLY: the version bump and status block, the two criterion IDs and their §14/§15 table scaffolding, the §14 disclosure blockquote (marked PROJECT LEAD DISCLOSURE precisely because `F05` found this seat writing unattributed normative prose here), and this row — enumerated at `BL-20260823T124508Z-0135`.** **TWO THINGS THIS VERSION DOES NOT DO, both disclosed rather than hidden: it does not write the register rows `CD-AC-017`/`CD-AC-018` owe, because PID §6 does not contain them and the register's population is derived from PID §6 alone (MEASURED — `NEW_REQUIREMENT is blocked pending PO amendment of the PID`); and it does not repair `F05`'s existing §16 sentence, because only the Product Owner may. Both are open Product Authority questions.** |
| 0.1.0 | 2026-08-18 | Project Lead | initial Blueprint, proposed for Product Owner acceptance under WO-1 |
| 0.1.0 | 2026-08-19 | Project Lead | **status only** — PROPOSED → ACCEPTED, recording the Product Owner's acceptance at 2e116ec and releasing the "no application code" hold this header was still asserting. No clause of the design changed, so the version does not move. |
| 0.3.0 | 2026-08-23 | Project Lead, **carrying the Product Owner's own bytes** | **THE PERIMETER IS DECLARED, NOT PRETENDED — PO-DECISIONS-0018 ruling 1 (commit `c72b6ea`, authored by Matt Scott and by no seat), applied and NOTHING ELSE.** §16 gains **CD-D-172, the FORGERY-DETECTION OBLIGATION**: deliberate in-process forgery cannot be prevented on this platform, so the defence is DETECTION — witness divergence and the provenance chain — **specified at WO-3 when real sources land and verified as a FIRST-CLASS CRITERION**, with the ruling's three parts (a)/(b)/(c) quoted verbatim. §17 gains **CD-BP-005**, HIGH, ACCEPTED AND DECLARED, stating in one row what is PREVENTED, what is DETECTED and what is OUT OF SCOPE, on the blast-radius basis that the detector is ADVISORY (`D1`) and no money moves on it (`D2`). **No design decision changed and none was reversed; a claim that was false as implied is now stated truthfully.** The version moves because §16 and §17 gained clauses. **This file is protected from every seat including the Project Lead (`CD-D-115`); the ruling's parenthetical — *"PO-authored text carried verbatim where protected"* — is the authority for the carriage, and the Project Lead's OWN authored bytes are exactly the version bump, the two IDs, the table scaffolding and this row, enumerated at `BL-20260823T095521Z-0131`.** Graded by the eighth Assurance seat against the declared perimeter. |
| 0.2.0 | 2026-08-22 | Project Lead | **BP-AMENDMENT-0001 — the engine owns the model lifecycle — IN FORCE.** Accepted by the Product Owner at governance/decisions/PO-DECISIONS-0005.md (commit b4e8eae). Applies the amendment's §F.3 delta and nothing else: §1 gains the fourth and fifth structural instruments (named specs resolved by the engine; establishment derived from the signature); §7 is rewritten with §7.0 *models are data* and §7.1 *doors require their value types*, and the "model injected into a DialSpec keeps evaluate pure" reasoning is retired as true-but-not-load-bearing; §13 and §14 carry CD-AC-002's fourth and first-structural refusal and CD-AC-005's `admits` door; §16 records that CD-D-005 now also owes model registry rows and that `MappingKind` ships one refusing member; §17 gains CD-BP-002, CD-BP-003 and CD-BP-004. **The version moves because clauses changed** — three gate verdicts said the value types are real closures but the doors do not require them, and this is the design that answers that sentence. |
