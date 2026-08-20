---
document: BLUEPRINT — how the Crash Detector is built
product: Crash Detector — standalone market stress instrument
version: 0.1.0
status: ACCEPTED — Product Owner accepted v0.1.0 at 2e116ec (governance/decisions/PO-ACCEPT-BLUEPRINT-0001.md).
  CD-HOLD-001 released; application code is authorised from WO-2 (CD-D-004.1 satisfied).
owner: PROJECT_LEAD
authority: CD-AUTH-0001
derives_from: PID.md v1.0.1 · governance/decisions/PO-DECISIONS-0001.md
framework: PBGv2 v2.0.0-alpha.1, pinned read-only at pbg/
last_reconciliation_sha: 0047093287f4282cad63c993ab87416bdb5a54ea
reconciliation_note: >
  c291f80 was the SHA whose worktree was read while authoring this document. 0047093 is the SHA at
  which the Project Lead re-read and reconciled it on resuming WO-2, finding no content drift — the
  only correction needed was this header, which still read PROPOSED and still carried the "no
  application code" hold three commits after the Product Owner released it. Content is unchanged at
  v0.1.0. Currency is computed against Git (PBG-BP-003, PBG-FWK-042), never read from a date.
amendment: Project Lead owns currency (PBG-BP-001). Assurance verifies, and does not author.
---

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

Three structural instruments do nearly all the work, and they are cheap because they are chosen once
and then reused everywhere:

| Instrument | Makes impossible | Doctrine served |
|---|---|---|
| **Sum types with no default** — a reading is `Value`, `Unknown` or `Degraded`; absence has a name and no numeric fallback exists | rendering absence as a number, therefore as calm | §3.2, CD-AC-001, CD-AC-005 |
| **Database roles with no grant** — a component that must not read something has no permission to read it | a witness leaking into a score; a public surface touching the book | §3.4, §3.5, CD-AC-003, CD-AC-006 |
| **Closed schemas and egress allowlists** — the publication envelope rejects unknown keys; a container reaches only the hosts it is allowed to reach | publishing a private field; a blended headline number; an execution pathway existing at all | §3.1, §3.5, CD-AC-002, CD-AC-006, CD-AC-012 |

Each of the three is verifiable from outside the running code: grants are readable from the store,
egress rules from the container config, schema closure from the schema file. That matters, because
the Assurance seat must be able to check them without trusting the implementation
(`PBG-EVID-001`).

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

> **A PROPOSED AMENDMENT STANDS AGAINST THIS SECTION AND IS NOT YET IN FORCE.**
> `governance/blueprint/BP-AMENDMENT-0001-engine-owns-the-model-lifecycle.md` would rewrite §7
> per the Product Owner's ruling at `governance/decisions/PO-DECISIONS-0004.md` §2 — *the engine
> owns the model lifecycle; models are named specs resolved against a registry, never objects
> accepted from callers.* It awaits Product Owner acceptance. **Every clause below remains the
> accepted design until it is accepted**, and this note changes none of them. In particular the
> sentence "The model is injected into a `DialSpec` rather than looked up inside `evaluate`"
> (`engine/model.py`, and the reasoning behind it) is what CD-ASR-WO2R2-01's finding ASR3-F02
> defeated at the third gate; it is recorded here so no reader takes §7 as unchallenged.

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

**Planted violation for CD-AC-002:** add `combined_stress = (equity + monetary) / 2`. It fails three
times — the types reject the operator, the register's AST check flags a single expression consuming
both dial types outside the allowlisted container and serving layer, and the closed envelope schema
rejects the new key. Three independent refusals for a criterion the PID marks Constitutional.

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
| **CD-AC-002** dials never blended | two unrelated frozen types with no arithmetic and no common numeric base; `DialSet` is a container with no scalar method; public envelope schema closed to a combined field | add `combined = (equity + monetary)/2` → must fail at the type level, at the AST check, and at the envelope schema |
| **CD-AC-003** witnesses side-by-side | `cd_engine` holds **no grant** on `witness.*`; separate container, separate pipeline; composition happens only at the serving layer | compute with the witness store unreachable → dials byte-identical; grant the engine a witness read → a register check on the live grant matrix must fail |
| **CD-AC-005** unavailable ≠ agrees | `WitnessPanel` sum type with `Unavailable` as a distinct constructor; absent or stale panel row maps to `UNAVAILABLE` at the serving layer | kill the witness feed → panel shows `WITNESS UNAVAILABLE`; delete the panel row entirely → same result, never `AGREES` |
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
| CD-AC-001 | §5 outcomes, §7 `Reading`, §8 serving | WO-2 |
| CD-AC-002 | §7 types, envelope schema | WO-2 |
| CD-AC-003 | §4 grant matrix, §6 pipeline separation | WO-2 |
| CD-AC-004 | §6 divergence module | WO-4 |
| CD-AC-005 | §6 `WitnessPanel` | WO-2 |
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

The Required Test Register derives its population from PID §6 and is compared against it
(`PBG-RT-001`); it is created in WO-2 and every row above becomes a register entry.

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
| **WO-3** | publication layer, heartbeat, external probe, regime-aware staleness, health surface | 008, 009, 014 | Assurance PASS; public-surface change → external R2D2 review (PID §8) |
| **WO-4** | witnesses live, divergence alarm, history and slope | 004, 010, 011 | Assurance PASS |
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

**CD-D-006 — the public exposure route.** Domain, hosting and what fronts `cd-public` in PROD.
*Recommendation:* decide at R2D2 ratification, not now; the PID's lane (dev never on cloud, prod
never on dell) means it cannot be settled from DEV anyway.
*Default safe action:* both surfaces bind loopback on DEV throughout WO-2 to WO-6. Nothing is
publicly reachable until Matt says so.

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
| 0.1.0 | 2026-08-18 | Project Lead | initial Blueprint, proposed for Product Owner acceptance under WO-1 |
| 0.1.0 | 2026-08-19 | Project Lead | **status only** — PROPOSED → ACCEPTED, recording the Product Owner's acceptance at 2e116ec and releasing the "no application code" hold this header was still asserting. No clause of the design changed, so the version does not move. |
