---
document: BLUEPRINT AMENDMENT 0001 — the engine owns the model lifecycle
amendment_id: BP-AMENDMENT-0001
status: >
  IN FORCE. Dispositioned by the Product Owner at governance/decisions/PO-DECISIONS-0005.md,
  committed at b4e8eae123e0f1250c80e282c274d73e93bb73ed and authored by Matt Scott — not by any
  seat. All five §J questions are answered; the dispositions are transcribed into §J below and the
  bounded revisions ruling 6 ordered are listed in §K. WO-2R3 is authorised against this document.
target: BLUEPRINT.md §7 (rewritten), with consequential edits to §1, §13, §14, §16, §17, §19
creates: BLUEPRINT v0.2.0 — applied to BLUEPRINT.md at the boundary that marked this IN FORCE
owner: PROJECT_LEAD
authority: CD-AUTH-0001
derives_from: >
  governance/decisions/PO-DECISIONS-0004.md rulings 2, 3, 5 and 6 (the what, and the sequence) ·
  governance/decisions/PO-DECISIONS-0005.md rulings 1–6 (the disposition of this document)
revised_at: "2026-08-22T11:11:25Z"
revision_bound: >
  PO-DECISIONS-0005 ruling 6 — "revises BP-AMENDMENT-0001 per rulings 2, 3 and 5 (bounded deltas,
  no new design)". Every change made at that revision is enumerated in §K with the ruling that
  ordered it. NOTHING ELSE WAS TOUCHED, and §K says so in a form a reader can check against
  `git diff 251b2e2 -- <this file>`.
evidence_base: >
  governance/assurance/WO-2R2/ (CD-ASR-WO2R2-01, the third Assurance seat) ·
  governance/engineering/build-log/BL-20260820T022200Z-0047.yaml (the Project Lead's own
  replication) · the audited tree at f30e63cbac6782ec5d7789071ee26be0ba7fe2e5,
  tree object 01da44b51e07dfb2e71170f4f19b6db09814b981
drafted_at_sha: fb823e18f295fbf00daa68809f5142218a9567b8
drafted_at_tree: f188610dd998de46219fa82310b068f0c0c8ec61
observed_utc_at_authoring: "2026-08-20T02:45:20Z"
runtime_verified: >
  NOTHING. This document is design intent, not a runtime observation (PBG-DEPLOY-007). The
  ONE measurement in it is §B's static inventory, and its producing command is recorded
  with it (CD-PL-F78).
---

# BP-AMENDMENT-0001 — the engine owns the model lifecycle

**THIS AMENDMENT IS IN FORCE.** The Product Owner dispositioned all five §J questions at
`governance/decisions/PO-DECISIONS-0005.md` (commit `b4e8eae`): §C and §D are **ACCEPTED**, the §D
extension deliberately included; `MappingKind` ships with exactly **one refusing member**; `fold`
(A7) is **WO-4** with two conditions; the collector boundary (A6) is **IN SCOPE** for WO-2R3; and
§F.3 is confirmed as the delta, with the `admits` instrument joining BLUEPRINT §1.

The superseded proposal text read: *"This is a PROPOSAL. It is not in force and no code may be
written against it until the Product Owner accepts it."* It is recorded rather than deleted so a
reader of the diff sees the transition rather than inferring it.

**What is now authorised, and what is still not.** WO-2R3 is authorised against this document, with
a fresh Engineer seat and a fourth fresh Assurance seat after it (`PBG-SOD-001`, non-waivable).
Nothing here admits, accepts or disposes of anything: the WO-2 gate is unchanged at Assurance PASS
on all five criteria, `latest_admitted_run` stays null (CD-RULE-001), and ASR3-F08 remains a gate
blocker in its own right outside WO-2R3.

---

## A. What is ruled, and what is drafted

The Product Owner ruled the **what** at PO-DECISIONS-0004 §2, and it is transcribed here
unchanged so that no later reader has to hold two documents open:

> **The engine owns the model lifecycle. Models are DATA — named specs resolved by the
> engine against the registry — never objects accepted from callers.** No public
> constructor, factory or API path accepts a callable or model object. DialSpec carries
> model REFERENCES; the registry is the sole resolution source; registry rows carry
> provenance per CD-D-005 (the PO's ingredient register). "No blend" and "no laundered
> number" then hold BY CONSTRUCTION: every computational path is engine-built from
> registered, provenanced specs, and there is no object-shaped door for a guard to miss.
> Static analysis regains authority because every route once again has source.

Everything below §A is the **how**, and it is the Project Lead's under `PBG-BP-001`. Where
a question in it turned out to be product content rather than construction it is not
answered — it is raised in §G, and §J is the list the Product Owner is asked to rule on.

**One correction to the framing before the design starts, and it is not cosmetic.** The
ruling's phrase *"there is no object-shaped door for a guard to miss"* is the whole point,
and it is worth saying why the previous three gates failed in the exact words the third
auditor used, because the amendment is answerable to that sentence:

> the value types re-establish their fields correctly and the closures are genuine — **but
> the ENTRY POINTS do not require the value types.** … The guard is on the class; the door
> does not ask for the class.
> — CD-ASR-WO2R2-01, *the single most important structural observation*

So this amendment has two halves and both are load-bearing:

1. **§C — the model boundary stops being a door at all.** No object arrives, so nothing
   has to be admitted. This is the ruling.
2. **§D — every remaining door on a judgement path requires its value type.** Doors that
   remain must ask for the class. This is the consequence, and without it §C closes one
   door out of a measured class of them.

---

## B. THE DENOMINATOR QUESTION, MEASURED

The auditor left one question explicitly open and told the Project Lead not to answer it by
enumeration:

> The class question is: *which public entry points accept a value whose type they never
> establish, and decide something with it?* The three I found (`resolve_panel(row)`,
> `evaluate(config_snapshot)`, `DialSpec.contribution_model`) are a denominator of three,
> not a proof that a fourth does not exist — and the sweep cannot answer it, because its
> closure excludes consumers. **It must NOT be scoped as "add
> `type(row) is not PanelRow` to `resolve_panel`"** — that is the instance game, and it is
> the error the first gate caught.

### B.1 The instrument, and what it is worth

`governance/blueprint/instruments/entry_point_inventory.py`, run as:

```
python3 -B governance/blueprint/instruments/entry_point_inventory.py \
    /srv/crash-detector-wo2r2-audit/src/crash_detector
```

against `/srv/crash-detector-wo2r2-audit` at `f30e63c`, tree `01da44b51e07dfb2e71170f4f19b6db09814b981`.
Output preserved at `governance/blueprint/instruments/entry-point-inventory-f30e63c.out`.
Instrument `sha256 14a03f0658813dcc4cff338b3cdb252d11024986558736e318f8dea4e1d21ce1`;
output `sha256 feba5f581e245d5c7c6026a38477b8053dd42d3b42e859082d8ad8e811131689`. Both
fingerprints record the command that produced them, per PO-DECISIONS-0004 ruling 5.

**Result: 44 public callables in `src/` have at least one parameter whose type they do not
establish.** The instrument's own docstring states its error in both directions and says
what it is worth: a floor on where to look, not a defect count. It reads syntax, it does
not know what a judgement path is, and it does not read annotations — because for a
`Protocol` parameter an annotation is not establishment, which is the whole of ASR3-F02.

**The classification below is the Project Lead's reading of those 44 and is not a
measurement.** It is offered as reasoning the Product Owner and the fourth Assurance seat
can check line by line against the file, not as a result.

### B.2 Class A — the ADMISSION CLASS: an unestablished value that decides a dial number or a witness state

| # | Entry point | What arrives unestablished | What it decides | Found by |
|---|---|---|---|---|
| **A1** | `DialSpec.contribution_model` (`engine/config.py:86`) | any object with a `compute` attribute — `ContributionModel` is a `Protocol`, so the annotation asserts nothing | **the dial's number** | ASR3-F02 |
| **A2** | `evaluate(config_snapshot=…)` (`engine/evaluate.py:109`) | any object answering `window()`, `spec_for()` | the window, both specs — therefore both dials | ASR3-F05 |
| **A3** | `evaluate(observations=…)` (`engine/evaluate.py:109`) | any sequence of objects answering `.outcome` | which observations are usable | **PL, this amendment** |
| **A4** | `resolve_panel(row=…)` (`serving/witness_resolver.py:140`) | any object answering `.state`, `.as_of_utc`, `.measures` | **`WITNESS AGREES`** | ASR3-F04 |
| **A5** | `present_dial(reading)` (`serving/dial_presentation.py:440`) | `reading` is **unannotated**; any object | `Shown` vs `NotShown` | **PL, this amendment** |
| **A6** | `collect(adapter, sink, ledger, clock, sleep, validator)` (`collectors/runner.py:195`) | four `Protocol`s and two bare `callable()`-checked callables | **every observation the dial path later consumes** | **PL, this amendment** |
| **A7** | `Reading.fold(on_value, on_degraded, on_unknown)` (`dials/reading.py:438`) | three caller callables | what absence renders as — an `on_unknown` returning `0.0` is CD-AC-001's failure mode with the sum type intact | **PL, this amendment** |

**The denominator is at least seven, not three, and A6 is the largest of them.** `collect`
takes six caller-supplied objects plus a `policy`, and `policy` is the only one admitted at
all — by `isinstance(policy, RetryPolicy)`, which is not even this project's own exact-type
standard, so a `RetryPolicy` subclass shadowing `max_attempts` with a property is admitted.
`clock` and `sleep` are checked with `callable()`, which establishes that they can be
called and nothing else; and `adapter`, `sink`, `ledger` and `validator` are `Protocol`s.
Everything the dial path later evaluates was written by objects the collector never
established. That route was outside the third audit's stated scope (`WHAT I DID NOT
EXAMINE`), and it is in scope here.

**A5 is worse than it looks and is stated plainly against this Project Lead's own prior
approval:** `present_dial(dial_id: str, reading)` carries no annotation on `reading` at
all, on the serving path, for CD-AC-001. It passed three gates.

### B.3 Class B — doors already closed, and they are the template

These are not defects. They are listed because §C is their generalisation, and because the
auditor called increments 1–2 *"the strongest closures I examined"*:

| Door | How it is closed |
|---|---|
| `number_for_dial_slot(slot, magnitude)` | exact type, plus provenance compared as **data**; refuses a bare `float` first of all |
| `derived_within_one_dial(quantities, reduction)` | **takes no number and no dial set** — only `DeclaredQuantity` values this module released |
| `combine_within_one_dial(magnitudes, using)` | **`using` is a NAMED REDUCTION, not a callable** — a member of the closed `SameDialReduction` enum, executed by `provenance` over numbers `provenance` released |
| `ConfigSnapshot.dial_specs`, `.source_registry` | `type(x) is not DialSpec` / `is not SourceRegistry` — exact, with the subclass-property reasoning written out |
| `StalenessWindow` | one admission door; the raw float is a record of what was configured, not a thing that may be applied |

**`combine_within_one_dial` is the precedent this entire amendment rests on.** Its history
is exactly the history the model boundary is now living through, one increment earlier:

> Until this commit `using` received a tuple of released `float` values and returned one,
> and this function passed that return value straight into the derivation door. It computed
> the dial set honestly and it validated the VALUE not at all, which made this the public,
> re-exported proxy through which `ASR2-002-A` published an equity 0.5 out of an equity 0.9
> and a monetary 0.1 with every declared static layer green.

The repair was not a stronger check on the callable. It was **deleting the callable
argument** and replacing it with a name from a closed set, executed by the module that owns
the numbers. `ASR3-F02` is the identical defect one level up: the model *is* the `using`
closure, wearing a `Protocol` instead of a `lambda`, arriving through `DialSpec` instead of
through a keyword argument. §C applies the closure that already worked to the boundary that
has not had it yet. **The pattern is not new to this project and it is not the Project
Lead's invention — it is this codebase's own strongest existing closure, generalised.**

### B.4 Class C — unestablished, but not on a judgement path

`store/migrate.py` (`connection`), `store/migrations.py` (`directory`, `migrations`),
`runtime/lifecycle.py` (`tick`, `callback`, `event`, `seconds`), the private helpers, and
the `Protocol` method stubs the instrument counts because it parses their signatures. These
decide no dial number and no witness state. **They are listed so the residue is visible and
so nobody later reads "44" as "7".** `Lifecycle.run(tick)` and `on_shutdown(callback)` take
caller callables and are the nearest of these to a judgement path; §H places them
explicitly out of WO-2R3's scope, and that is a scoping decision the fourth Assurance seat
is invited to attack.

---

## C. THE REPLACEMENT DESIGN — models are data

### C.1 The rule, replacing BLUEPRINT §7's "validate at declared doors"

> **A computational mapping enters this system as a NAME resolved against a registry, never
> as an object supplied by a caller.** The engine resolves the name, the engine executes
> the mapping over values the engine released, and no argument exists through which a
> caller's number or a caller's code can reach a dial.

The difference from what stands today is not the strength of a check. It is that **there is
nothing to check**, because there is no parameter through which the thing could arrive.

### C.2 What replaces `ContributionModel`

`engine/model.py`'s `ContributionModel` `Protocol` and the `CONTRIBUTION_MODELS: Mapping[str, ContributionModel]`
dict are **deleted, not repaired**. In their place, three data types and one executor:

```
ModelId          := a name. Established on its own terms (own_str), like every other id.

MappingKind      := a CLOSED enum, members added HERE, deliberately and visibly.
                    It is the SameDialReduction pattern at the model boundary:
                    an enum with members is closed against subclassing by the
                    interpreter, and members cannot be added after class creation.
                    SHIPS NON-EMPTY WITH EXACTLY ONE MEMBER, AND THAT MEMBER
                    COMPUTES NOTHING (PO-DECISIONS-0005 ruling 2) — see C.2.1.

ModelSpec        := frozen data, no callables, no methods that compute:
                      model_id        : ModelId
                      dial_id         : one of DIAL_IDS          <- BINDS THE MODEL TO ONE DIAL
                      required_input_ids   : tuple[SourceId, ...]
                      contributing_input_ids : tuple[SourceId, ...]
                      mapping         : MappingKind              <- A NAME, NOT A FUNCTION
                      parameters      : tuple[DeclaredParameter, ...]  <- numbers, from config
                      provenance      : ModelProvenance          <- CD-D-005, see C.6

ModelRegistry    := frozen mapping ModelId -> ModelSpec, exact-typed like SourceRegistry,
                    REQUIRED on the ConfigSnapshot with NO DEFAULT.
```

`DialSpec` then carries **a reference and not an object**:

```
DialSpec := dial_id
            required_input_ids
            contributing_input_ids
            model_ref : ModelId | None        <- WAS: contribution_model: ContributionModel | None
```

`evaluate` no longer calls anything a caller supplied. It calls one engine-owned function:

```
engine.mapping.compute(spec: ModelSpec, payloads) -> ScoreComputation
```

which dispatches on `spec.mapping` — a member of a closed enum — over payload values the
engine released, and returns a magnitude the engine then stamps with the dial's provenance
at the existing single admission site. `ScoreComputation` survives unchanged: the
contributions are still required, because BLUEPRINT §7's "explicable a year later without
archaeology" is untouched by this amendment.

### C.2.1 `MappingKind` ships with ONE member, and that member refuses

**Ruled by the Product Owner at PO-DECISIONS-0005 ruling 2**, against the Project Lead's §J.2
question and against the PO's own first lean, which the full read refuted:

> `MappingKind` ships NON-EMPTY, with exactly ONE member, and the member computes nothing. … P3 and
> P4 must construct a `ModelSpec` to plant against `ConfigSnapshot` invariants 2 and 3, and over an
> empty enum they die at `ModelSpec` construction for a reason that is not under test. A criterion
> that cannot be demonstrated is a rumour — §F.1's own doctrine, applied to §F.1.

The ruling fixes the *property* and leaves the *name* to the Project Lead ("its name is construction
and the Project Lead's"). The construction, then, and it is deliberately dull:

```
class MappingKind(Enum):
    UNSPECIFIED = "unspecified"      # the one member. It names the ABSENCE of a declared mapping.
                                     # It is not a mapping, it is not a default, and it is not a
                                     # placeholder for one that is coming — the first COMPUTING
                                     # member arrives only with the CD-D-005 register.

# in the executor, engine/mapping.py:
#   the UNSPECIFIED branch RAISES UnspecifiedMapping AND RETURNS NOTHING.
#   there is no `else`, no fallthrough, and no numeric return anywhere on that path.
class UnspecifiedMapping(Exception): ...   # a NAMED error, per the ruling
```

Three properties the WO-2R3 Engineer must hold, and they are the whole of what ruling 2 buys:

1. **`ModelSpec` is constructible.** P3 and P4 can be planted, so `ConfigSnapshot` invariants 2 and
   3 are demonstrable rather than rumoured. That is the ruling's entire reason.
2. **Zero product meaning ships.** No weights, no mapping semantics, nothing that says what a dial
   means. CD-D-005 stays owed in full and stays visible in code, exactly as `EMPTY_SOURCE_REGISTRY`
   and `EMPTY_MODEL_REGISTRY` already make it visible (§G.3, and CD-HOLD-004 is untouched).
3. **The executor path refuses with a named error and never returns a magnitude.** `UNSPECIFIED`
   reaching the executor is a *refusal*, not a zero, not a `None` and not a `Unknown` reading
   manufactured inside the executor — CD-AC-001's failure mode is exactly a number standing in for
   an absence, and an executor that answered `0.0` here would reintroduce it at the one place this
   amendment concentrates all computation.

Under `EMPTY_MODEL_REGISTRY` the executor is unreachable in the shipped configuration anyway: no
model is registered, so no `model_ref` resolves, so no `ModelSpec` reaches `engine.mapping.compute`
at all. The refusal is demonstrated by a plant (P8, §F.1) rather than by a shipped route.

**The first computing member arrives only with the CD-D-005 register, by amendment to §16's owed
list** (ruling 2, verbatim). A seat adding a second member to this enum without that register is
inventing product meaning (`PBG-AUTH-005`, CD-RULE-003).

### C.3 The four refusals the plant now meets, and where each one bites

`spec.contribution_model.compute(payloads)` — the line at `engine/evaluate.py:348` through
which ASR3-F02 published a laundered number — **does not exist after this amendment**.
There is no attribute on `DialSpec` holding an object, so there is no expression that could
be written there.

### C.4 One model may serve exactly one dial

`ModelSpec.dial_id` is not decoration and it is the specific structural answer to ASR3-F02's
mechanism. The plant was **one stateful object placed in BOTH `DialSpec`s**: it saw the
equity dial's payloads on the first call and the monetary dial's on the second, blended
them in its own memory, and returned a number that every downstream layer then stamped with
honest single-dial provenance. Every field of the claim was true except the number.

After this amendment:

* a registry row declares the one dial it serves. Resolving it for the other dial is
  refused **at snapshot construction**, before an evaluation runs;
* the executor is handed **one dial's** `ModelSpec` and **one dial's** payloads, and holds
  no state between dials or between runs — it is a function of its arguments, and the
  arguments cannot span two dials;
* there is no object to place in both specs, because there is no object.

**The cross-dial route is closed by the shape of the data, not by a guard that has to
notice it.** That is the ruling's "by construction", made specific.

### C.5 The registry is part of the snapshot, and WO-2 ships it EMPTY

`ModelRegistry` joins `SourceRegistry` on `ConfigSnapshot`, on the same terms and for the
same stated reason: it is configuration that affects a result, so it belongs in the
run-level snapshot (Standards Baseline §10), and it is **required with no default**,
because *a registry nobody chose is not evidence of anything*.

Three invariants join the constructor with it, and the first two mirror the source registry
exactly:

1. every `model_ref` a dial names **must resolve** in the registry;
2. a resolved `ModelSpec`'s `dial_id` **must equal** the dial naming it;
3. a resolved `ModelSpec`'s input ids **must be a subset of** the naming `DialSpec`'s
   declared inputs, and every one of them must be registered in the `SourceRegistry` with
   an agreeing criticality. A model may not read an input its dial did not declare — which
   is the same evasion invariant 1 of the source registry closes, one level up.

**WO-2R3 ships `EMPTY_MODEL_REGISTRY` — zero rows.** With no model registered, no dial may
name one; with no source registered, no dial may declare an input; both dials read
`Unknown`, which remains the doctrinally correct empty state and keeps CD-D-005 owed and
visible in code exactly as `EMPTY_SOURCE_REGISTRY` does today.

### C.6 The vacuity dilemma, answered

The auditor measured a dilemma with no third branch and the Product Owner ruled on it
(PO-DECISIONS-0004 ruling 3): *a criterion whose satisfaction depends on architecture
cannot be scoped by population*. Under the shipped config both dials read `Unknown` and no
dial number exists at all, so "no blend" was satisfied by there being nothing to blend.

This amendment answers it in the only way that survives an empty configuration:
**CD-AC-002's closure after this amendment is a property of the TYPES AND THE RESOLUTION
PATH, which exist and are testable with zero rows registered.** The demonstrations in §F.1
all run against `EMPTY_MODEL_REGISTRY` — they show the plant failing at *construction* and
at *resolution*, neither of which needs a number to exist. A criterion that can be
demonstrated on an empty configuration is not vacuous on an empty configuration.

`ModelProvenance` is where CD-D-005 attaches: source, what it stands for, criticality, and
the account of the mapping that doctrine §3.6 requires ("no unexplained mappings"). Its
**shape** is construction and is the Project Lead's. Its **contents** are the Product
Owner's register and are not invented here (`PBG-AUTH-005`).

---

## D. THE DOORS THAT REMAIN MUST REQUIRE THEIR VALUE TYPES

§C removes the model door. It does not remove A2–A7. The ruling's guarantee — *"there is no
object-shaped door for a guard to miss"* — is only true of the system if the remaining
doors are closed too, and the auditor's instruction was that the class must be closed as a
class and not finding by finding.

### D.1 The rule

> **Every public entry point on a judgement path establishes each of its arguments by EXACT
> TYPE at the door, and the establishment is derived from the signature rather than written
> into the body.**

Derived from the signature, because the two escapes this project has already suffered were
both edits to a body: CD-ASR-F03 (an edit to `_evaluate_dial`'s body) and the fourth
argument that `_absence_is_never_a_number` is deliberately written with `*extra` to
survive. The existing post-condition decorator is the precedent and the mechanism:

```
@admits(row=PanelRow, now_utc=datetime, staleness_window_seconds=float)
def resolve_panel(row, *, now_utc, staleness_window_seconds): ...
```

`admits` refuses on `type(value) is not declared`, refuses **any parameter it was not told
about** (so a new argument arrives unguarded never — it arrives refused), and is applied at
the boundary so a rewrite of the body cannot remove it.

**This is deliberately NOT "add `type(row) is not PanelRow` to `resolve_panel`".** That is
the instance game the first gate caught and the auditor named it as the thing WO-2R3 must
not be scoped to. The unit of work is *the class of doors*, the mechanism is *derived from
the signature*, and the acceptance test is a static check that enumerates the judgement
paths and fails on any public entry point that is not decorated — not a list of three fixes.

### D.2 The doors, and what each must require

| # | Door | Requires |
|---|---|---|
| A2 | `evaluate(config_snapshot)` | exactly `ConfigSnapshot` |
| A3 | `evaluate(observations)` | every element exactly `ObservationRecord` — the *record*, not only the outcome, which is already exact-typed one level in |
| A4 | `resolve_panel(row)` | exactly `PanelRow`, or `None` |
| A5 | `present_dial(reading)` | exactly one of the sealed `Reading` members |
| A6 | `collect(adapter, sink, ledger, validator, clock, sleep)` | see D.3 — this one is not a type check |
| A7 | `Reading.fold(...)` | see D.4 — this one is not a type check either |

### D.3 A6 — the collector's protocols

`adapter`, `sink`, `ledger` and `validator` are boundaries to things outside this system (a
market data source, the store), so exact-typing them against a concrete class is not
available and would be wrong. The closure is different in kind and has two parts:

1. **`clock` and `sleep` stop being caller callables.** They are the same defect as `using`
   and the same repair: `clock` becomes an engine-owned instant already established by
   `ensure_utc` and passed as a *value*; `sleep` becomes a named member of a closed
   `DelayKind`. A caller supplies neither.
2. **`adapter`, `sink`, `ledger` and `validator` keep their `Protocol`s, and the values
   they RETURN are established at the point of return** — `missing_adapter_members` already
   exists and is the right shape, and every `FetchedResponse`, every `ObservationRecord`
   and every validation verdict crossing back in is exact-typed on arrival. The system
   cannot establish what an adapter *is*; it can and must establish everything the adapter
   *hands it*.

**Stated as a limit rather than hidden:** part 2 is a weaker guarantee than §C's. It is a
door that admits, not an absence of a door. It is the right one here because the thing on
the other side is genuinely foreign, and the fourth Assurance seat should attack it first.

### D.4 A7 — `fold`

`fold` exists so that a rendering layer must decide what to do with each `Reading`
constructor — that is CD-AC-001 working. Its three callables are the caller's own rendering
code and are not a laundering route into a dial: the values they receive are already
established and their return value never re-enters the dial path.

**It is listed anyway, and not closed, and that is a judgement this amendment makes
visible rather than quietly.** A `fold` whose `on_unknown` returns `0.0` renders absence as
a number in a *consumer*, with the sum type wholly intact — which is CD-AC-001's failure
mode reached in a place this architecture has decided not to govern. The Project Lead's
reading is that governing a consumer's rendering is WO-4 (§8 publication) and not WO-2R3,
because the envelope schema — not `fold` — is the structural refusal for what actually
publishes.

**RULED: `fold` (A7) IS WO-4** (PO-DECISIONS-0005 ruling 3). The Project Lead's reading is accepted
in terms — *"its callables receive already-established values and their returns never re-enter the
dial path; the envelope schema — not `fold` — is the structural refusal for what actually
publishes"* — and it is accepted **with two conditions, so §D.4's honesty is not lost between here
and WO-4**:

* **(a)** the residue is added to BLUEPRINT §17 as a **named risk** alongside CD-BP-002 and
  CD-BP-003. It is **CD-BP-004** and it is carried in §F.3's §17 row below;
* **(b)** **WO-4's scope names it on day one.** It is recorded as an owed item in
  `governance/engineering/ACTIVE_WORK.yaml`'s `remaining_items` at the boundary that put this
  amendment in force, so a WO-4 dispatch cannot be drafted without meeting it.

> *"A residue this amendment made visible does not get to become invisible again by being
> deferred."* — PO-DECISIONS-0005 ruling 3

The deferral is therefore a **scheduling** decision and not a disposal of the residue: A7 is out of
WO-2R3's scope (§H) and simultaneously on WO-4's face and in §17. Both are true at once, and the
fourth Assurance seat may treat the pair as a single checkable claim.

---

## E. HOW THE AUDITOR'S REPLICATED PLANT FAILS AT CONSTRUCTION TIME

PO-DECISIONS-0004 ruling 6 renews the standing condition in terms:

> the amendment must make the injection route UNCONSTRUCTIBLE, proved by the auditor's own
> replicated plant failing at construction time.

The plant, exactly as CD-ASR-WO2R2-01 wrote it and the Project Lead replicated it
(BL-…-0047): one ordinary `ContributionModel` — no I/O, no clock, no environment, breaching
no documented contract — placed in **both** `DialSpec`s, with equity 0.9 and monetary 0.1 as
true inputs, publishing **monetary 0.5** through `number_for_dial_slot`, the one declared
publication gate, not refused.

Walked against the amended design, in the order the interpreter reaches each line:

| Step in the plant | Under the amendment | Where it dies |
|---|---|---|
| 1. define a class with a `compute` method | still legal Python — this amendment does not try to stop anyone writing a class | — |
| 2. `DialSpec(dial_id="equity", …, contribution_model=plant)` | **`TypeError`: `DialSpec` has no field `contribution_model`.** The field is deleted; the only model field is `model_ref: ModelId`, and a `ModelId` is a name established by `own_str`. An object is not a name. | **CONSTRUCTION of the first `DialSpec`** |
| 3. suppose the plant is instead registered as a `ModelSpec` | `ModelSpec` is frozen data with **no callable-typed field**. There is nowhere to put the object. `mapping` is a `MappingKind` enum member; `enum` membership is closed by the interpreter, and a value that is not a member is refused. | **CONSTRUCTION of `ModelSpec`** |
| 4. suppose a `MappingKind` member exists and the plant names it in both dials | **`ModelSpec.dial_id` binds the row to ONE dial.** Naming an equity-bound model from the monetary `DialSpec` is refused by `ConfigSnapshot` invariant 2. | **CONSTRUCTION of `ConfigSnapshot`** |
| 5. suppose two rows, one per dial, both naming the same `MappingKind` | Legal — and it blends nothing. The executor is a function of one dial's spec and one dial's payloads, holds no state, and **has no reference to the other dial's payloads to close over**. Two rows naming `MEAN` compute two independent means. | **NOT REACHED — there is nothing to blend with** |
| 6. suppose the model reads an input its dial did not declare | Refused by `ConfigSnapshot` invariant 3 before any evaluation runs. | **CONSTRUCTION of `ConfigSnapshot`** |
| 7. the WO-2R3 shipped configuration | `EMPTY_MODEL_REGISTRY`. Step 2 is unreachable because no `model_ref` resolves at all. | **RESOLUTION, with zero rows** |

**Four independent refusals, three of them at construction and one at resolution, and every
one of them demonstrable against an empty registry.** Steps 2–4 and 6 are the ones the
standing condition names; step 5 is the one that matters most for CD-AC-002, because it is
where the previous architecture's honest-looking path was.

**What this amendment does NOT claim.** It does not claim the plant is the last plant. The
first three gates each fell to a route the previous gate's closure did not describe, and
the honest statement of this design's residue is:

* the executor's `MappingKind` members are code, and code can be wrong. A `MEAN` that is
  not a mean is a defect this architecture does not prevent — it makes it *have source*,
  which is the ruling's "static analysis regains authority" and is a strictly weaker claim
  than "cannot happen";
* D.3's adapter boundary admits foreign objects by protocol and is the softest surface left;
* **the executor is now the only place a dial number is computed, which makes it the single
  highest-value target in the product.** That concentration is deliberate — one place with
  source beats seven doors without — but it should be stated as a risk and not as a win,
  and §F.3 carries it into BLUEPRINT §17.

---

## F. WHAT CHANGES IN THE BLUEPRINT, AND WHAT IS PROVED

### F.1 Planted violations — each must fail, each with a baseline/violated contrast

Per BLUEPRINT §1, a structure without a planted violation that fails is a rumour. Seven,
and every one runs against `EMPTY_MODEL_REGISTRY` and a zero-source configuration:

| id | plant | must fail at |
|---|---|---|
| P1 | the auditor's ASR3-F02 model object into `DialSpec` | `DialSpec` construction |
| P2 | a callable into any `ModelSpec` field | `ModelSpec` construction |
| P3 | an equity-bound `ModelSpec` named by the monetary `DialSpec` | `ConfigSnapshot` construction |
| P4 | a `ModelSpec` reading an undeclared input | `ConfigSnapshot` construction |
| P5 | a duck `ConfigSnapshot` into `evaluate` (ASR3-F05) | the `admits` door |
| P6 | a duck row whose `state` property answers `AGREES` while its stored state is `UNAVAILABLE` (ASR3-F04) | the `admits` door |
| P7 | a new parameter added to a decorated door without being declared to `admits` | the `admits` door, on every call |
| P8 | a `ModelSpec` whose `mapping` is `MappingKind.UNSPECIFIED`, resolved and executed | the executor, with `UnspecifiedMapping` — **and no magnitude returned** |

**P7 is the one that makes this a class closure rather than seven fixes**, and it is the
test the fourth Assurance seat should run first.

**P8 IS ADDED BY THE REVISION AND IS DISCLOSED AS AN ADDITION, NOT PRESENTED AS ORIGINAL.** It is
the demonstration that PO-DECISIONS-0005 ruling 2 requires and does not itself name: the one
`MappingKind` member ships *because* a criterion that cannot be demonstrated is a rumour, and a
refusing member nobody has watched refuse is that same rumour one level down. **P1–P7 are unchanged
in number, in content and in numbering** — P8 is appended, so every reference to "P1–P7" written
before this revision, including PO-DECISIONS-0005 ruling 6's own, continues to resolve to exactly
the plants it named. The baseline arm is the executor refusing; the violated arm is the refusal
branch replaced by any numeric return, which must then publish a magnitude — the contrast form the
third seat used, and the one §F.1 requires of all the others.

Each plant is recorded with a BASELINE (the guard present: refuses) and a VIOLATED (the
guard removed: passes) arm, in the contrast form the third seat used, because a guard
nobody has seen refuse anything is a rumour and a guard nobody has seen *fail to refuse* is
an untested one.

### F.2 A fourth AND A FIFTH structural instrument in BLUEPRINT §1

The §1 table gains **two** rows, because both of these are instruments that do the work everywhere
rather than §7 local rules:

| Instrument | Makes impossible | Doctrine served |
|---|---|---|
| **Named specs resolved by the engine** — a mapping is a name in a registry, executed by the engine over values the engine released; no argument accepts a callable or a model object | a caller's number entering a dial with the dial's own provenance stamped on it; a mapping with no source for static analysis to read | §3.1, §3.6, CD-AC-002, CD-AC-005 |
| **Establishment derived from the signature** — `admits` refuses on `type(value) is not declared` and refuses **any parameter it was not told about**, applied at the boundary so a rewrite of the body cannot remove it | a judgement-path entry point deciding on a value whose type it never established; a NEW argument arriving unguarded — it arrives refused | §3.1, §3.2, CD-AC-001, CD-AC-002, CD-AC-005 |

**The second row is added by the revision, on the Product Owner's ruling 5**, which put the question
and refused to accept silence on it:

> The `admits` mechanism of §D.1 is itself an instrument that does the work everywhere rather than a
> §7 local rule — the same criterion §F.2 applied to named-spec resolution. Either BLUEPRINT §1
> gains a second instrument row for it, or the amendment states why it is properly §7-local; silence
> is the only unacceptable resolution.

**The Project Lead takes the first branch, and states why rather than merely choosing.** §7-local
would be the honest answer if `admits` were a rule *about dials*. It is not. Its subject is *every
public entry point on a judgement path*, and three of the six doors §D.2 lists — `resolve_panel`
(§6, the witness layer), `present_dial` (the serving path) and `collect` (§5, the collector runner)
— are not in §7 at all. A rule that governs §5, §6 and §7 and is written down in §7 is a rule the
next §5 author does not read; that is the same "guard is on the class, the door does not ask for the
class" shape one storey up, in the documentation instead of the code. It also meets §1's own test
for an instrument, which is not "is it important" but *"is it verifiable from outside the running
code"* (`PBG-EVID-001`): the decoration is readable in the source and the acceptance test is a
static enumeration of judgement paths that fails on any undecorated public entry point — checkable
by an auditor who trusts nothing in the implementation.

### F.3 Consequential edits, listed so the PO reviews the whole delta

**CONFIRMED BY THE PRODUCT OWNER AT PO-DECISIONS-0005 RULING 5, with one addition — the `admits`
instrument row — which is folded into the §1 row below. "With those, §F.3 is the whole of what I
expect to review."** The table is therefore the complete delta to BLUEPRINT.md, and the boundary
that marked this amendment IN FORCE applied exactly it and nothing else, creating **v0.2.0**.

| § | Edit |
|---|---|
| §1 | the fourth **and fifth** instrument rows above — named specs resolved by the engine, and establishment derived from the signature (`admits`), per ruling 5 |
| §7 | rewritten per §C and §D. "The model is injected into a `DialSpec` rather than looked up inside `evaluate`, which is what keeps `evaluate` a pure function of its arguments" is **DELETED** — it is the sentence the defect was reasoned from, and it was true and not load-bearing. `evaluate` stays pure because the executor is pure and takes no caller code, which is a stronger purity than the one that argument bought |
| §13, §14 | CD-AC-002's trace changes from three refusals (type / AST / schema) to **four, the first structural**: no door, plus the three that already stand. CD-AC-005 gains the `admits` door |
| §16 | CD-D-005 now also owes **model registry rows** — `ModelProvenance` contents and `MappingKind` members are product meaning. The default safe action is unchanged: WO-2 ships zero rows and every dial reads `Unknown`. **PLUS, per ruling 5: the single-refusing-member statement of ruling 2** — `MappingKind` ships one member, it computes nothing, its executor path refuses with a named error, and **the first computing member arrives only with the CD-D-005 register, by amendment to §16's own owed list** |
| §17 | **three** new risks: **CD-BP-002** — the executor is the single highest-value target in the product (§E residue); **CD-BP-003** — D.3's adapter boundary admits by protocol and is the softest remaining surface; **CD-BP-004**, per ruling 3 — a consumer's `fold` with an `on_unknown` returning `0.0` renders absence as a number outside the governed boundary, CD-AC-001's failure mode reached where this architecture has chosen not to govern; deferred to WO-4, named here so the deferral is visible |
| §19 | v0.2.0 amendment-log row |

---

## G. WHAT THIS AMENDMENT DELIBERATELY DOES NOT DECIDE

Under `PBG-AUTH-003` and `PBG-AUTH-005`, three things in the design above are product
content and are **not** answered here:

1. **The members of `MappingKind`.** Which mappings exist is *what a dial means*.
   `SameDialReduction`'s precedent is followed exactly: **no weighted mapping is shipped,
   and that is a refusal rather than an omission** — weights are the relative worth of one
   observation against another and CD-D-005 is owed. **ANSWERED at PO-DECISIONS-0005 ruling 2 and
   no longer open: exactly one member, computing nothing, refusing at the executor with a named
   error (§C.2.1).** The construction — the member's name and the error's name — is the Project
   Lead's and is written out in §C.2.1. What remains the Product Owner's is unchanged and is the
   whole of the product meaning: **the first COMPUTING member, which arrives only with the CD-D-005
   register.**
2. **The contents of `ModelProvenance`.** Shape here, contents in the PO's register.
3. **Whether a model may exist at all before CD-D-005 is issued.** The Project Lead's
   default safe action is: no — zero rows, both dials `Unknown` — and that is unchanged
   from what ships today.

---

## H. SCOPE BOUNDARY FOR WO-2R3 — AS AMENDED BY PO-DECISIONS-0005 RULING 4

**In scope** — the entry-point admission class as a class: §C (the model boundary) and §D
(A2–A6), with §F.1's plants — **P1–P7 as originally written, plus P8 for ruling 2's refusing
member** — and the static check that enumerates the judgement paths.

**A6 — THE COLLECTOR BOUNDARY — IS IN SCOPE, RULED** (ruling 4). The Project Lead put the question
in §J.4 and recommended nothing; the Product Owner ruled it IN, with the cost stated rather than
discovered:

> Excluding the largest member of the measured class re-opens the instance game this amendment
> exists to end, and it leaves every observation the dial path consumes written by objects the
> system never established — "by construction" true of the judgement half of the system and false
> of its input half. §D.3 is accepted as written, both parts … The material enlargement of WO-2R3
> is a cost accepted here and paid with the Project Lead's increment discipline, not with a scope
> cut.

Two consequences bind the WO-2R3 dispatch and are not the seat's to reinterpret. **First, §D.3 is
accepted AS WRITTEN, both parts**: `clock` and `sleep` cease to be caller callables (the `using`
repair applied again — an engine-owned instant already established by `ensure_utc`, and a named
member of a closed `DelayKind`); `adapter`, `sink`, `ledger` and `validator` keep their `Protocol`s
with **every value they RETURN established on arrival**. **Second, the softest surface is stated
plainly as an admitting door** (CD-BP-003) and is **the fourth Assurance seat's first target** —
which, with P7, gives that seat two named first targets and no discretion about whether to look.

**"Paid with the Project Lead's increment discipline, not with a scope cut"** is a delivery
instruction to this seat, not a compliment: WO-2R3 is dispatched in committed increments, each
landing whole, because seven runtime terminations on this project have shown that an increment that
is not committed did not happen (`PBG-CONT-007`).

**Explicitly NOT folded in**, per the auditor's own separation:

* **ASR3-F08** — the CD-AC-012 extraction gap (a real broker SDK escaping deny-by-default on
  requirement *spelling*). Parser work with its own denominator question. It is a gate
  blocker in its own right: the auditor's instruction is that the gate must not be re-run
  until F02, F04, F05 **and F08** are closed;
* **ASR3-F01, F06, F07, F09** — documentary and method corrections;
* **A7 (`fold`)** — §D.4. **OUT, RULED: it is WO-4** (ruling 3), and out **with two conditions
  that are now discharged obligations and not intentions**: the residue is BLUEPRINT §17's
  CD-BP-004, and WO-4's scope names it on day one via `remaining_items`;
* **Class C (`Lifecycle`)** — §B.4; out of scope on the Project Lead's reading, which the Product
  Owner did not disturb. `Lifecycle.run(tick)` and `on_shutdown(callback)` remain the nearest of
  Class C to a judgement path, and the fourth Assurance seat is still invited to attack that
  scoping.

**Sequence, unchanged from PO-DECISIONS-0004 ruling 6 and re-stated at PO-DECISIONS-0005 ruling 6:**
PO reviews this amendment (**DONE** — PO-DECISIONS-0005, `b4e8eae`) → WO-2R3 implements with a
**fresh** Engineer seat → **fourth fresh** Assurance seat. The Engineer and the Assurance Engineer
are never the same agent (`PBG-SOD-001`, non-waivable).

**The standing condition is unchanged and is renewed a third time** (ruling 6): the auditor's
replicated plant fails at construction, demonstrated in §F.1's baseline/violated contrast form,
P1–P7, **all over `EMPTY_MODEL_REGISTRY`**.

**ASR3-F08 remains a gate blocker in its own right, outside WO-2R3** (ruling 6, and §H stands): the
WO-2 gate is not re-run until F02, F04, F05 **and F08** are closed. The Project Lead **proposes the
F08 parser work order once WO-2R3's Engineer is running, not before** — that timing is the Product
Owner's instruction, not this seat's scheduling preference.

---

## I. WHAT THIS AMENDMENT COSTS, STATED BEFORE IT IS ASKED FOR

* `engine/model.py` is deleted and rewritten. `engine/config.py`, `engine/evaluate.py`,
  `serving/witness_resolver.py`, `serving/dial_presentation.py` and `collectors/runner.py`
  change at their signatures.
* **The `f30e63c` closures in `dials/`, `own_terms.py`, `staleness.py`,
  `source_registry.py` and `publication/` carry forward substantially unchanged** — they
  are the auditor's "strongest closures examined" and they are what §C is built out of, not
  what it replaces. The doors they guarded do not carry forward.
* WO-2R3 is a re-architecture of the dial path's *boundaries*, not of its computation.
  There is no computation to re-architect: zero sources, zero models, both dials `Unknown`.
* `f30e63c` remains an **evidence lane, never a baseline** (PO-DECISIONS-0004 ruling 4).
  Nothing is built on it and nothing is merged from it.

---

## J. WHAT WAS ASKED OF THE PRODUCT OWNER — AND WHAT WAS RULED

The Project Lead recommended **no answer to any of the five**. All five are now dispositioned at
`governance/decisions/PO-DECISIONS-0005.md` (commit `b4e8eae`, authored by Matt Scott). The
questions are kept verbatim so that the ruling reads against what was actually asked.

**J.1 — Accept, amend or reject §C and §D** as the design implementing PO-DECISIONS-0004 §2. §D in
particular goes beyond the literal words of the ruling, and that extension is the Product Owner's to
accept or cut.

> **RULED (ruling 1): §C AND §D ARE ACCEPTED, the §D extension included, deliberately.** *"'By
> construction' is a claim about the SYSTEM; a system with one closed boundary and six open doors
> from a measured class is the instance game played at system scale."* The estate's standing lesson
> from five kernel assurance rounds applies at full force: **a remedy found in a defect is assessed
> as a general invariant before the defect is closed.** §D.1's rule is the class closure; **P7 is
> its test, and the fourth Assurance seat is directed to run it first**, exactly as §F.1 proposes.

**J.2 — `MappingKind`'s initial members** — minimum non-empty set, or empty (§G.1)?

> **RULED (ruling 2): NON-EMPTY, EXACTLY ONE MEMBER, AND THE MEMBER COMPUTES NOTHING.** The PO's
> first lean was empty — the stronger statement — and *"the full read refuted it"*: P3 and P4 must
> construct a `ModelSpec`, and over an empty enum they die at `ModelSpec` construction for a reason
> that is not under test. **A criterion that cannot be demonstrated is a rumour — §F.1's own
> doctrine, applied to §F.1.** Executor path refuses with a named error and never returns a
> magnitude; zero product meaning ships; the first computing member arrives only with CD-D-005.
> **Transcribed into the design at §C.2.1; the name is the Project Lead's construction.**

**J.3 — Is `fold` (A7) in WO-2R3's scope or is it WO-4?** The Project Lead's reading is WO-4; §D.4
states the residue that reading leaves.

> **RULED (ruling 3): `fold` IS WO-4, on the Project Lead's own reasoning, WITH TWO CONDITIONS** —
> the residue becomes BLUEPRINT §17's **CD-BP-004**, and **WO-4's scope names it on day one**.
> *"A residue this amendment made visible does not get to become invisible again by being
> deferred."* **Transcribed at §D.4 and §H; both conditions discharged at this boundary.**

**J.4 — Is the collector boundary (A6) in WO-2R3's scope?** Including it enlarges WO-2R3 materially;
excluding it leaves every observation the dial path consumes written by objects the system never
established.

> **RULED (ruling 4): A6 IS IN SCOPE.** *"Excluding the largest member of the measured class
> re-opens the instance game this amendment exists to end."* §D.3 accepted **as written, both
> parts**; the admitting door is stated plainly as CD-BP-003 and is **the fourth Assurance seat's
> first target**; **the enlargement is paid with increment discipline, not with a scope cut.**
> **Transcribed at §H.**

**J.5 — Confirm the §F.3 consequential edits** are the whole delta, or name what is missing.

> **RULED (ruling 5): CONFIRMED, WITH ONE ADDITION.** The `admits` mechanism is itself an instrument
> — *"either BLUEPRINT §1 gains a second instrument row for it, or the amendment states why it is
> properly §7-local; silence is the only unacceptable resolution."* **The Project Lead takes the
> first branch and states its reasoning anyway** (§F.2): `admits` governs §5, §6 and §7 doors alike,
> so writing it down in §7 alone is the "guard is on the class, the door does not ask for the class"
> shape moved into the documentation. §16's edit additionally carries ruling 2's
> single-refusing-member statement. *"With those, §F.3 is the whole of what I expect to review."*

**The superseded closing paragraph of this section, retained rather than deleted:** *"**STOP.** No
Engineer is dispatched and no application code is written until this is dispositioned. A PASS would
not have been an acceptance and this proposal is not a decision (`PBG-AUTH-003`)."* It was honoured:
the thirteenth Project Lead seat drafted and stopped, and the next thing that moved was the Product
Owner's own commit.

---

## K. THE REVISION LOG — WHAT CHANGED WHEN THIS WAS MARKED IN FORCE, AND UNDER WHICH RULING

PO-DECISIONS-0005 ruling 6 bounds this revision in terms: *"revises BP-AMENDMENT-0001 per rulings 2,
3 and 5 (bounded deltas, no new design)"*. The complete list, checkable against
`git diff 251b2e2 -- governance/blueprint/BP-AMENDMENT-0001-engine-owns-the-model-lifecycle.md`:

| # | Where | Change | Ordered by |
|---|---|---|---|
| K1 | frontmatter | `status` PROPOSED → **IN FORCE**, naming the disposition record and its commit; `would_create` → `creates`; `derives_from` gains PO-DECISIONS-0005; `revised_at` and `revision_bound` added | ruling 6 |
| K2 | document head | the PROPOSAL banner replaced by the IN FORCE statement, with the superseded sentence quoted rather than deleted | ruling 6 |
| K3 | §C.2 code block | `MappingKind` annotated: ships non-empty, one member, computes nothing | ruling 2 |
| K4 | **§C.2.1 (new)** | the one member written out — `UNSPECIFIED`, the named error `UnspecifiedMapping`, and the three properties the Engineer must hold. **The member's NAME and the error's NAME are the Project Lead's construction, which ruling 2 assigns here in terms** | ruling 2 |
| K5 | §D.4 | the Project Lead's WO-4 reading replaced by the RULING, with conditions (a) CD-BP-004 in §17 and (b) WO-4 names it on day one | ruling 3 |
| K6 | §F.1 | **P8 appended** — the executor refusal demonstrated in contrast form. P1–P7 unchanged and un-renumbered, and the addition disclosed as an addition | ruling 2 (consequential) |
| K7 | §F.2 | a **fifth** instrument row for `admits`, plus the stated reasoning for why it is not §7-local | ruling 5 |
| K8 | §F.3 | header records the confirmation; §1 row covers both instrument rows; §16 row carries the single-refusing-member statement; §17 row carries **CD-BP-004** | rulings 2, 3, 5 |
| K9 | §G.1 | `MappingKind` members marked ANSWERED; what remains the PO's is narrowed to the first COMPUTING member | ruling 2 |
| K10 | §H | A6 **IN SCOPE** with the ruling quoted; A7 out as WO-4 with its two conditions; the standing condition and ASR3-F08's separate gate-blocking status restated | rulings 3, 4, 6 |
| K11 | §J | rewritten from five open questions to five transcribed dispositions, questions kept verbatim | ruling 6 |
| K12 | §K | this table | ruling 6 |

**WHAT WAS NOT CHANGED, and it is the larger half of the list.** §A, §B (the measured denominator,
all three classes and the 44-callable inventory), §C.1, §C.3–§C.6, §D.1–§D.3, §E (the plant walked
through the amended design, all seven steps and the residue), §F.1's P1–P7, §G.2, §G.3 and §I are
**untouched**. No design was added, no design was removed, and no measurement was restated. Three of
the twelve rows above are pure status; the rest transcribe a ruling into the place the ruling names.

**One thing this revision deliberately did NOT do.** It did not soften §E's residue paragraph, which
still says in terms that this amendment *does not claim the plant is the last plant*, that a
`MEAN` that is not a mean is a defect this architecture does not prevent, and that concentrating all
computation in one executor *"should be stated as a risk and not as a win"*. An amendment reads
differently once it is in force, and that paragraph is the one most likely to be quietly improved.
It was left alone on purpose.
