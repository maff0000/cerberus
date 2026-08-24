# Execution contract — CD-RT-001-MISSING-DATA-NEVER-CALM

**CD-AC-001** · Missing or stale input never renders as calm · obligation **MANDATORY** ·
scope **CLASS** · delivered in **WO-3 increment 16B**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

**PID §3.2, constitutional, in its own words: *"Missing data must never render as calm."***
The LIVE PUBLICATION GATE — `refuse_unless_publishable`, the function
`src/crash_detector/publication/publish.py` calls on both surfaces before it writes anything —
REFUSES an envelope whose `UNKNOWN` or `DEGRADED` dial carries `detail_level: "calm"`, and
**still ADMITS** `elevated` and `acute` on those same branches and `calm` on a `VALUE` dial.

**GROWN AT `16B-FIX`, ON EVERY BRANCH OF THE UNION AND NOT ONE DOCUMENT SHAPE PER STATE.** The
proposition is now driven on **every branch of `#/$defs/dial_reading.oneOf`**, each candidate
built from **that branch's own** `required` + `properties`; and a missing-data branch carrying
**no `detail_level` key at all** or **a value outside the vocabulary** is REFUSED too. Those last
two rows are a CORRECTION: `tests/test_detail_level.py` had asserted both since before this
instrument existed and both were dropped when the property moved into the register, so the live
guard was **strictly weaker than the memorial it was built to supersede** (`CD-ASR-WO3-05` F2).

## Why this row exists at all — `PO-DECISIONS-0026` ruling 9

> "The calm-over-unknown refusal currently holds only in `tests/`, and `tests/` do not feed
> the gate — a register-wired instrument PASSES identically on a tree where the fix is fully
> reverted. That is 'the controls exist and nothing runs them' one hop sideways, and it is
> unacceptable for a CONSTITUTIONAL guarantee. 16B adds a REGISTER-WIRED negative control (one
> the gate actually reads) that FAILS if calm-over-unknown is ever admitted — the guarantee
> must be carried by a live instrument, not a memorial in tests."

MEASURED and reproduced by the Project Lead at `CD-DISPATCH-INC16B-ENGINEER` §2: on a tree
with all four `$ref`s restored to `#/$defs/detail_level`, **all fourteen register instruments
exit as they do on the clean tree**, and the only failures anywhere are nine tests in
`tests/test_detail_level.py`, a file no register `execute:` line named.

## Command

```
python3 tools/register/check_missing_data_never_calm.py --root .
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

**The RUNNING GATE, not the schema documents.** The check imports `crash_detector` from
`<root>/src`, drives `refuse_unless_publishable` with candidate envelopes, and records what
the gate actually did. It does not read the schemas as documents, does not search for the
string `absent_data_detail_level`, and does not assert that any `$ref` points anywhere.

Enumerated from the subject rather than typed in: the surfaces from `EnvelopeSurface`, the
dial slots from each contract's own properties that `$ref` `#/$defs/dial_reading`, the
detail-level vocabulary from the contract's own `#/$defs/detail_level` enum, and — **since
`16B-FIX`** — the **branch set of `#/$defs/dial_reading.oneOf`**, with each candidate dial built
from **that branch's own** `required` + `properties` and each property's value chosen from a
closed declared list by what the property's **own subschema accepts**, decided by `jsonschema`
and never by the property's name. It prints the resolved `crash_detector.__file__` and the
SHA-256 of both contracts it judged, at every run.

### The two structural assertions added at `16B-FIX`, and both DENY BY DEFAULT

* **`CD-CALM-BRANCHES-006`** — the union's branch set must be exactly one branch per declared dial
  state, with the contract's declared state set exactly the check's own closed `DECLARED_STATES`.
  **A branch nobody anticipated is a violation for being UNRECOGNISED rather than a silence** —
  the `RULE F` shape `check_no_numeric_default` already established here. Branches are recognised
  by their own `properties.state.const`, **never** by the name of the `$def` they live in, so the
  pure-rename refactor this instrument already survives keeps passing.
* **`CD-CALM-SLOTS-007`** — the driven slot set must equal the set of root properties that
  constrain a dial `state` under **any** spelling, and no root property may be undecidable.

**WHY THEY EXIST, MEASURED AND NOT ARGUED.** A fourth `oneOf` branch permitting the full
vocabulary on `UNKNOWN`, selected by a marker property and **adding no new ROOT key so
`check_schema_closed`'s allowlist never fires**, gave a tree on which the live gate ADMITTED an
`UNKNOWN` dial rendering as `calm` on both surfaces while **all thirty of the register's
`execute:` lines exited byte-identically to the clean tree** (`CD-ASR-WO3-05` F1). That tree is
arm `C6`.

### The three assertions added at `16B-CONTRACT-CLOSURE`, and they are the architectural close

* **`CD-CALM-ROOT-008` — `RULE CC`, THE ROOT PARTITION.** Every root property is EXACTLY ONE of
  (a) a canonical dial slot spelled literally `{"$ref": "#/$defs/dial_reading"}` or (b) a declared
  non-dial property on a finite written allowlist that is PROVED against the live gate to be
  incapable of carrying a `detail_level`. **ANYTHING ELSE IS A VIOLATION AND NO RECOGNISER IS
  CONSULTED.**
* **`CD-CALM-CANON-009` — THE CANONICAL PATH.** `properties.state` at depth one, `state` REQUIRED,
  every branch closed and pinned by `properties.state.const`, and every branch REQUIRING a
  `#/$defs/utc_timestamp`-typed freshness stamp.
* **`CD-CALM-FRESH-010` — THE AFFIRMATIVE VALUE CHECK.** A branch may carry `calm` **if and only
  if** it has proved present-and-fresh. **A never-before-named state cannot carry `calm`, by
  construction over a closed set.**

**WHY THEY EXIST, MEASURED AND NOT ARGUED.** `CD-CALM-SLOTS-007` compares the recogniser's output
against the driven set, so a root property the recogniser answers `False` about is in **neither**
set and is INVISIBLE. `CD-ASR-WO3-10` measured three such properties at `8398741` — a discriminator
spelled `status`, a `present: false` reading with a stale stamp, and a `state` nested one level past
the instance-walk cap — each of which left the whole thirty-line register GREEN while the live gate
ADMITTED a dead feed rendering as `calm` on both surfaces. **`PO-DECISIONS-0028` ruling 1 ruled the
architecture rather than a tenth shape.** See `DECLARED LIMIT 17` for the closure argument and, at
equal length, for its boundary.

## Why it is asserted this way

A structural read of schema keys is what let this class of defect through three times on this
project (`CD-PL-F169`, `CD-ASR-WO3-02` F06/F07, `CD-ASR-WO3-03`). A check that reads the
`$ref` TARGET NAME and never opens the target passes a tree where `calm` has been put back
inside the target's own enum; a check that asks *"is there a narrowing?"* rather than *"is
EVERY missing-data branch on EVERY surface narrowed?"* passes a tree where one branch on one
surface was reverted. **Both of those trees are contrast arms in `plants/WO3-INC16B/` and this
instrument exits non-zero on both.**

Register instruments on this project ARE permitted to import the application: four already do
(`check_exact_type_admission`, `check_engine_no_witness_reach`, `check_no_numeric_default`,
`check_judgement_path_doors`). `CD-RT-014`'s *"the probe must not import the application"*
binds `tools/probe/external_probe.py` and nothing else — an EXTERNAL probe must be external.

## *** THE ADMITTING ARMS ARE NOT DECORATION ***

The check asserts, in the same run and with equal weight, that the gate **still ADMITS**
`elevated` and `acute` on an `UNKNOWN` or `DEGRADED` dial and **`calm` on a `VALUE` dial**.

An instrument that only checked *"calm is refused"* is satisfied by a contract that refuses
everything, and — the case this project's history says gets missed — by a contract in which
**no dial can ever read `calm` at all**. `calm` on a real number backed by real inputs is the
entire reason `calm` exists (PID §4: *"calm = dial + one line"*). A guard that cannot tell
*"the forbidden thing is impossible"* from *"everything is impossible"* is not holding PID
§3.2, it is enforcing silence. Assertion `CD-CALM-VACUITY-000` checks the instrument's **own**
proposition table still contains the `VALUE`/`calm` admitting row, so the vacuity arm cannot be
quietly removed from the instrument that exists to carry it.

`CD-CALM-PAIRED-004` closes the other half: every refused candidate is diffed against the
ADMITTED candidate of the same state at the same slot on the same surface, and must differ at
**exactly one JSON pointer**, `/<slot>/detail_level`. Same document, one token moved, opposite
outcome — so the refusal is attributable to the level and to nothing else. `CD-CALM-REASON-003`
requires the refusal to be `SCHEMA_VIOLATION` located at the mutated slot, because *the right
outcome from the wrong layer* is this project's most-repeated defect (`CD-PL-F74`).

## Preconditions

* `python3` 3.11 or later.
* **`jsonschema` must be importable.** *This is a departure from the stdlib-only checks in
  this directory and it is stated rather than left to be discovered.* This check drives the
  live gate and the live gate validates with `jsonschema`; a behavioural check cannot be more
  stdlib-only than the behaviour it drives. If it is missing, the check exits `3` with the
  reason — never a pass and never a skip.
* `<root>/src/crash_detector/__init__.py` must exist. *"REFUSED"* is a runtime claim and the
  check will not make it against a tree it could not load.
* **`$CD_CONTRACTS_DIR` must be unset, or set to `<root>/contracts`.** The gate honours that
  variable, so it can be pointed at contracts that are not the subject's. The check resolves
  what the gate would load and exits `3` if it is not the subject's own — it will not report
  on a tree it is not looking at.
* The subject tree extracted by the auditor, with the working directory set to its root.
  `--root .` is not a default and is not optional.

## Exit semantics

| exit | meaning |
|---|---|
| `0` | CLEAN — assertions were made and all of them held. A run that made ZERO assertions refuses instead, so `0` can never mean "I looked at nothing". |
| `1` | VIOLATION — at least one finding, each printed with the cell (`surface/slot/state/level`) and the observed outcome. |
| `2` | USAGE — the command line was wrong. |
| `3` | PRECONDITION NOT MET — the check could not do its job, with the reason on stderr. |

Anything other than `0` is a failure. **The check never skips, for any reason**
(`PBG-CI-002`): a precondition it cannot meet is a non-zero exit with a stated reason,
never a pass.

## Declared limits — `CD-RULE-004`

Said the same way here, in the header of `tools/register/check_missing_data_never_calm.py`,
and in the comment above the entry in `required-tests.yaml`. **A register entry may not claim
more than its guard delivers.**

1. **IT JUDGES THE CONTRACT THE GATE ACTUALLY LOADS, WHICH IS CONFIGURABLE.**
   `$CD_CONTRACTS_DIR` can point the live gate at a widened copy while the repository's
   contracts are byte-intact. **This is a real, executable route and it is arm `C5` of
   `plants/WO3-INC16B/MANIFEST.md`, where the gate is MEASURED admitting a calm `UNKNOWN` dial
   with both repository schemas untouched.** The check refuses (exit `3`) when it is pointed
   that way, and prints the resolved contract paths and their SHA-256 at every run
   (`CD-PL-F98`). **IT DOES NOT PREVENT THE ROUTE.** A deployment that sets the variable to a
   widened copy is refused by nothing in this repository: **NOT PROVED TO BE CARRIED ANYWHERE.**
2. **IT PROVES NOTHING ABOUT A `VALUE` READING THAT SHOULD NOT HAVE BEEN A `VALUE`.** A dial
   whose inputs were missing but which was constructed as `VALUE` with a fabricated `score`
   renders `calm` legitimately as far as this contract is concerned, and this check ADMITS it —
   the `VALUE`/`calm` row says so out loud. **THE CARRIERS ARE THE SIBLING ENTRIES:**
   `CD-RT-001-AST-NO-NUMERIC-DEFAULT` (the provenance of the magnitude) and
   `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` (the runtime post-condition
   `refuse_a_number_without_its_inputs`). **This check is ONE OF THREE guards on `CD-AC-001`
   and never a sole guard.**
3. **IT SAYS NOTHING ABOUT STALENESS.** `CD-AC-001`'s words are *"missing OR STALE"*. This
   instrument drives the ABSENCE half only. Nothing in it reads `staleness_window_seconds`,
   the age of `as_of_utc`, or any liveness/relevance quantity. The stale half is `CD-AC-009`
   (`CD-RT-009-REGIME-AWARE-STALENESS`) and, as a product model, `PO-DECISIONS-0026` ruling 5,
   which is a LATER increment and is not evidenced here.
4. **IT IS NOT A CENSUS OF RENDERING PATHS, AND IT DRIVES ONE EXACT SPELLING OF A DIAL SLOT.**
   *** SUPERSEDED AT `16B-FIX`, STATED AND NOT ERASED (`CD-RULE-004`, `PBG-CONT-003`). ***

   > **WHAT THIS LIMIT SAID, VERBATIM:** *"It drives every surface `EnvelopeSurface` declares at
   > every dial slot the contracts declare, so a third surface or a third dial is driven on the
   > day it is added."*

   **THAT SENTENCE WAS FALSE**, and identically false in all three places `CD-RULE-004` requires
   this limit to be said. MEASURED by `CD-ASR-WO3-05` (F3) and reproduced as arm `C9` of
   `plants/WO3-INC16B/MANIFEST.md`: the slot enumerator requires
   `sub.get("$ref") == "#/$defs/dial_reading"` **exactly**, so an **OPTIONAL** third dial slot
   spelled with any other `$ref` — which is exactly how a dial is added without breaking existing
   consumers — was invisible. The superseded instrument reported `PASS — 67 assertions, 0
   violations` on that tree while the live gate ADMITTED `calm` on the new slot on **both**
   surfaces. The exposure was narrow, and honestly so: `check_schema_closed` catches that tree via
   its root-properties allowlist, and a *required* third slot in any spelling was already caught
   by this instrument. **That is not the point. A limit that promises what the code does not do is
   the defect, whatever else happens to cover it.**

   > **WHAT WAS SAID INSTEAD AT `16B-FIX`, VERBATIM — AND IT IS ALSO SUPERSEDED, AT `16B-FIX-2`,
   > FOR BEING FALSE IN EXACTLY THE WAY THE SENTENCE IT REPLACED WAS FALSE:**
   > *"`CD-CALM-SLOTS-007` enumerates every root property that constrains a dial `state` under
   > **any** spelling and **FAILS the check** if that set is not exactly the driven set, or if any
   > root property's shape cannot be decided at all."*

   **THAT SENTENCE WAS ALSO FALSE, IN THE SAME THREE PLACES.** MEASURED by `CD-ASR-WO3-06` (F2)
   and reproduced as arms `C13` and `C14`: `_dial_bearing` asked whether a root property's `state`
   `const`/`enum` **intersected** `DECLARED_STATES`, and where it did not it returned **`False` —
   not undecidable.** An **optional** root property `credit_stress` whose state is
   `{"const": "NO_DATA"}` (`C13`) **constrains a dial `state`**, its shape **is** decidable, it was
   **not** in the driven set — **and the check did not fail.** The live gate ADMITTED it rendering
   as `calm` on **both** surfaces while the instrument reported `PASS — 144 assertions, 0
   violations`. The identical property with the state spelled `["UNKNOWN","STALE"]` **was** caught.
   *** **THE ONLY DIFFERENCE BETWEEN A CAUGHT TREE AND AN UNCAUGHT ONE WAS WHETHER THE NEW DIAL
   REUSED AN OLD STATE NAME**, which is `GUARD_THE_INSTANCE_NOT_THE_CLASS` (`PO-DECISIONS-0026`
   ruling 10). *** `C14` is the same shape carrying ruling 5's **liveness** quantity — optional
   root `feed_liveness`, states `["LIVE","STALE"]` — and `CD-AC-001`'s own words are *"missing **or
   stale** input never renders as calm"*.

   **WHAT IS TRUE INSTEAD — WRITTEN AFTER `FX6` WAS MEASURED, AND DESCRIBING WHAT WAS MEASURED.**
   What is **DRIVEN** is every top-level property whose value is literally
   `{"$ref": "#/$defs/dial_reading"}`, on every surface `EnvelopeSurface` declares. A dial slot
   spelled any other way is **NOT DRIVEN**. Since `16B-FIX-2` it is **NOT SILENT PROVIDED IT
   DECLARES A PROPERTY NAMED `state`**, and that proviso is the whole of the honest claim.
   `_dial_bearing` walks a root property through a **declared** keyword set to a **declared**
   depth, and:

   * a resolved subschema declaring a `state` whose `const`/`enum` **intersects**
     `DECLARED_STATES` is **dial-bearing** — driven, or `CD-CALM-SLOTS-007` fails;
   * a resolved subschema declaring a `state` whose vocabulary does **not** intersect is
     **UNDECIDABLE**, reported by `CD-CALM-SLOTS-007`'s `undecidable` limb, because *"I cannot
     classify this state vocabulary"* is precisely the case `DECLARED LIMIT 8` says must **stop**
     the check;
   * a `$ref` that does not resolve, a keyword outside the declared set, or a nesting deeper than
     the walk is **UNDECIDABLE** and reported the same way.

   **AND WHAT IS STILL SILENT, SAID PLAINLY RATHER THAN LEFT FOR THE NEXT AUDITOR TO MEASURE:** a
   root property carrying a dial that **does not declare a property named `state`** — one that
   discriminates on a differently-named key — is classified `False` and says nothing. **THIS LIMIT
   NO LONGER CLAIMS "UNDER ANY SPELLING".** It claims: *declared `state`, under any spelling of
   that state's vocabulary, within a declared keyword set and depth.* See this row's `DECLARED
   LIMIT 12`.

   **REPORTED IS NOT DRIVEN, and this limit still does not pretend otherwise.** A third *surface*
   genuinely is driven on the day it is added, because the surfaces come from `EnvelopeSurface`
   itself; that half of the original sentence was true and stands.

   *** THIS IS NOT AND MUST NOT BE READ AS SUPPORT FOR A THIRD DIAL. *** `PO-DECISIONS-0026`
   standing is **two dials, never blended**. `CD-CALM-SLOTS-007` fails closed precisely so that a
   third dial slot stays a **product** decision rather than something an instrument absorbs.

   And a path that does not go through `refuse_unless_publishable` is outside this check entirely.
   MEASURED at this commit: the only callers in `src/` are `publication/publish.py:276-277`, on
   both surfaces, before any write. A future serving layer that renders a dial without publishing
   an envelope is **NOT PROVED TO BE CARRIED ANYWHERE** — the rendering layer is later WO work.
5. **IT IMPORTS THE SUBJECT TREE AND THEREFORE INHERITS IT.** It is a runtime check because
   *"refused"* is a runtime claim and every escape on this project's record passed a static
   checker. The cost is `--root`'s honesty, which is why the resolved package path and both
   contract digests are printed on every run.
6. **IT NEEDS `jsonschema`.** See Preconditions. It cannot run where the application's own
   runtime dependencies are absent, and it exits `3` rather than passing when they are. **Since
   `16B-FIX` it also uses `jsonschema` directly**, to decide which declared synthetic value a
   branch's own property subschema accepts, so the dependency is load-bearing twice over.
7. **THE ENVELOPE ROOT IS STILL A DOCUMENT SHAPE WRITTEN OUT IN THE CHECK.** *** NEW AT
   `16B-FIX`. *** `FX1` replaced the hand-written DIAL shapes with shapes derived from each
   `oneOf` branch; `_envelope`'s ROOT skeleton is still typed in. **It is FAIL-CLOSED rather than
   fail-silent, which is why it is a limit and not a hole:** a required root property the
   skeleton does not carry makes every candidate refused, so every `MUST ADMIT` row fails as
   `CD-CALM-GATE-002` and the check exits `1`. The dial branches were the SILENT case — a
   candidate still valid, still admitted, and simply never built — and those are the ones now
   derived.
8. **THE DIAL STATE VOCABULARY IS TYPED IN, DELIBERATELY.** *** NEW AT `16B-FIX`. *** Surfaces,
   dial slots, `oneOf` branches and detail LEVELS are all enumerated from the subject.
   `DECLARED_STATES` is not: a fourth dial **state** added to a contract makes
   `CD-CALM-BRANCHES-006` FAIL until someone edits the check. **THAT IS THE INTENDED COST.** A new
   LEVEL is classified by a rule already written in one line — it is `calm`, or it is not. A new
   STATE cannot be classified without knowing whether it MEANS the data is absent, which is
   product meaning (`PBG-AUTH-005`), and the failure is asymmetric: guess "present data" and
   `calm` is silently admitted on a missing-data state, which is the constitutional breach itself.
   **The cost is priced: a PID §4 amendment adding a fourth LEVEL still passes untouched — arm
   `C10`, measured — while a fourth STATE is a red instrument until a human looks.**
9. **A BRANCH THE CHECK CANNOT BUILD IS REPORTED, NOT DRIVEN.** *** NEW AT `16B-FIX`. *** Each
   required property of a branch is filled with the first of a closed, declared list of synthetic
   values that the property's own subschema accepts, decided by `jsonschema` and never by the
   property's NAME. A property none of them satisfies makes the check report
   `CD-CALM-BRANCHES-006` and exit `1`. Deny-by-default, so it is not an escape; it **is** a
   maintenance cost, and reporting is the correct failure direction.
10. **A BRANCH WHOSE SHAPE IS CONDITIONAL IS REPORTED, NOT DRIVEN — DENY BY DEFAULT.** *** NEW AT
    `16B-FIX-2` (`FX5`, closing `CD-ASR-WO3-06` F1). *** This check builds **exactly one document
    per branch**, out of that branch's own `required` + `properties`. A branch that **also**
    carries any of `if`/`then`/`else`, `allOf`, `anyOf`, `oneOf`, `not`, `dependentSchemas`,
    `dependentRequired` or `unevaluatedProperties` admits **more** shapes than that one document,
    and the shapes it never builds are exactly where a `calm` variant hides. **MEASURED, arm
    `C11`:** `dial_reading_unknown` keeps its name, its `state.const`, its `required` list and
    `additionalProperties: false`; its `detail_level` is widened; the narrowing is relocated into
    `"if": {"required": ["render_hint"]}` with an `"else"` carrying a fully closed copy. A dial
    **without** the marker is REFUSED; a dial **with** it is ADMITTED on both surfaces; and the
    superseded instrument reported `PASS — 144 assertions, 0 violations` while **exactly one** of
    the register's thirty `execute:` lines moved — `tests/test_detail_level.py`, the memorial
    `PO-DECISIONS-0026` ruling 9 said the guarantee must not be left in. Such a branch is now
    `CD-CALM-BRANCHES-006`, on `DECLARED LIMIT 9`'s own sentence: *a branch whose shape is
    conditional is a branch this check cannot say it has driven.* **THE COST IS PRICED:** this
    check does **not** enumerate conditional shapes — one candidate per satisfiable combination of
    optional markers is a schema-instance generator and a design question this row does not price
    (RULED by `PROJECT_LEAD_SEAT_02`; the auditor correctly refused to decide it) — so a
    **legitimate** conditional dial branch would turn this instrument red until that increment
    prices it. **IT COSTS NOTHING TODAY:** measured, the clean tree's six branches declare only
    `type`/`additionalProperties`/`required`/`properties`/`description`, and the clean run is
    unchanged at `PASS — 144 assertions, 0 violations`.

    *** ITS CLOSING SENTENCE WAS FALSE FOR A CONDITIONAL WRITTEN ONE POSITION OVER. SUPERSEDED AT
    `16B-FIX-3`, STATED AND NOT ERASED (`CD-RULE-004`, `PBG-CONT-003`). ***

    **WHAT THIS LIMIT SAID, VERBATIM:** *"A branch that **also** carries any of `if`/`then`/`else`
    ... admits **more** shapes than that one document ... Such a branch is now
    `CD-CALM-BRANCHES-006`."*

    **THAT SENTENCE WAS FALSE, identically in all three places `CD-RULE-004` requires it to be
    said.** MEASURED by `CD-ASR-WO3-07` (F1) and reproduced as arms `C18` and `C19`. Both contracts
    declare JSON Schema 2020-12, in which a keyword **sibling** to `$ref` **is applied**; the
    resolver replaced a node carrying `$ref` with the `$ref`'s target and discarded that node's
    siblings **at every hop**. So the same `if`/`else` — written as a sibling of the `$ref` on the
    `oneOf` **entry** (`C18`), or one hop deeper behind an innocuous entry (`C19`), rather than
    **inside** the branch definition — never reached the guard. On both trees the live gate
    **ADMITTED** an `UNKNOWN` dial rendering as `calm` on **both** surfaces while the instrument
    reported `PASS — 144 assertions, 0 violations`, and **exactly one** of the register's thirty
    `execute:` lines moved: LINE 2, `tests/test_detail_level.py`, the memorial. **LINE 3 — this
    row's own register-wired instrument — did not move.** On `C19` the instrument even printed the
    branch in its enumerated list, named and state-classified, and still reported clean.

    **WHAT IS TRUE INSTEAD, written after `FX9` was measured.** The conditional-keyword guard is
    **unchanged**; **the resolver was repaired**, so the branch handed to that guard is either the
    whole branch or nothing, and the answer no longer depends on **where** the conditional was
    written. `C18` and `C19` are `FAIL — 32 violation(s)` each, 20 × `CD-CALM-BRANCHES-006` + 12 ×
    `CD-CALM-PAIRED-004` — the same census `C11` gives for the same shape written inside the branch
    — and LINE 3 now moves on both. The cost of that resolver change is **`DECLARED LIMIT 13`**.
11. **THE FILLER DIAL IS THE FIRST ABSENT-DATA BRANCH THAT ACTUALLY BUILDS, AND `LIMIT 9`'S OWN
    SENTENCE WAS FALSE UNTIL IT WAS.** *** NEW AT `16B-FIX-2`; it corrects a measurement
    `CD-ASR-WO3-06` F3 recorded against `16B-FIX` (`CD-RULE-004`, `PBG-CONT-003` — stated, not
    erased). *** `DECLARED LIMIT 9` says an unbuildable property *"makes the check report
    `CD-CALM-BRANCHES-006` and exit `1`"*. **AT `16B-FIX` THAT WAS FALSE:** the filler dial was
    built from the first absent-data branch **found**, so an unbuildable `UNKNOWN` branch exited
    **3** as `PRECONDITION_NOT_MET`, upstream of the matrix, **with no violation code at all**.
    Both outcomes are non-zero and both state a reason, so nothing escaped; **but the limit
    described an observable the code did not produce.** The filler is now the first absent-data
    branch that **builds**, so the unbuildable one is REPORTED at exit `1` and `LIMIT 9` says what
    happens. **MEASURED, arm `C17`:** the `UNKNOWN` branch gains a required nested object with its
    own `required` member — `16B-FIX` gave exit 3 and no code; `16B-FIX-2` gives
    `FAIL — 32 violation(s)`, 20 × `CD-CALM-BRANCHES-006` + 12 × `CD-CALM-PAIRED-004`. **WHAT IT
    COSTS:** if **every** absent-data branch is unbuildable the check still exits `3`, naming each
    branch and its obstacle — there is then no admissible dial to fill the other slots with and
    nothing to measure.
12. **A DIAL THAT DOES NOT DECLARE A PROPERTY NAMED `state` IS STILL SILENT.** *** NEW AT
    `16B-FIX-2` (`FX6`, closing `CD-ASR-WO3-06` F2), AND IT IS THE RESIDUE OF THAT FIX RATHER THAN
    A HOLE THE FIX OPENED. *** `_dial_bearing` now stops — `None`, UNDECIDABLE, reported by
    `CD-CALM-SLOTS-007` — on a resolved subschema that **declares** a `state` whose `const`/`enum`
    does not intersect `DECLARED_STATES`, which is what makes arms `C13` and `C14` red. **THE
    LOOSER, LOUDER FORM WAS RULED** over the tighter one (require a `state` **and** a
    `detail_level`): a false positive costs one seat one look at one contract; a false negative
    costs the constitution. **WHAT IS
    STILL SILENT:** a root property carrying a dial that discriminates on a differently-**named**
    key — `status`, `kind`, `reading_state` — is classified `False` and reported by nothing here.
    This check keys on the property name `state` and on nothing else, and widening that to "any
    discriminator" is not an Engineer's judgement to make (`PBG-AUTH-005`). **NOT PROVED TO BE
    CARRIED ANYWHERE.** *** That residue STANDS and it was TESTED rather than taken on trust:
    `CD-ASR-WO3-07` (F3) built the tree — the same dial with the key spelled `liveness` PASSES,
    spelled `state` FAILS, spelled `state` through a `$ref` FAILS — and judged the limit HONESTLY
    DRAWN. It is a condition on 16C's dispatch and it is not closed here. ***

    *** SUPERSEDED AT `16B-FIX-3` ON TWO COUNTS, STATED AND NOT ERASED (`CD-RULE-004`,
    `PBG-CONT-003`). THE BEHAVIOUR IS UNCHANGED ON THE SECOND COUNT — WHAT IS CORRECTED IS THE
    SENTENCE. ***

    **(a) ITS POSITIVE CLAIM WAS FALSE FOR A `state` THAT IS NOT AN OBJECT.** WHAT IT SAID,
    VERBATIM: *"a resolved subschema that **declares** a `state` whose `const`/`enum` does not
    intersect `DECLARED_STATES`"* is UNDECIDABLE and reported. MEASURED by `CD-ASR-WO3-07` (F2) and
    reproduced as arm `C20`: `FX6` put the `undecidable` limb **inside** `if isinstance(state,
    dict)`, so a `state` spelled as the **boolean schema `true`** — legal in 2020-12 and maximally
    permissive — dropped to `None`, the limb never ran, the descent skipped it, and the property was
    classified **not a dial**. Instrument `PASS — 144 assertions, 0 violations` with the property in
    **neither** list, while the live gate **ADMITTED** `{state: STALE, reason: FEED_DEAD,
    detail_level: 'calm'}` **and** `{state: NO_DATA, ..., detail_level: 'calm'}` on **both**
    surfaces. **`DECLARED LIMIT 12` DID NOT COVER IT** — this limit is about a differently-**named**
    discriminator and that dial's key is literally called `state`. **WHAT IS TRUE INSTEAD (`FX10`):
    declaring the key `state` is the whole trigger.** A root property that declares it reaches the
    undecidable limb **whatever the shape of that key's subschema** — object, boolean, or anything
    else — and the shape can only refine the answer to `True`, never back to `False`. `C20` is
    `FAIL — 2 violation(s)`, `CD-CALM-SLOTS-007`, one per surface.

    **(b) ITS "MEASURED" SENTENCE PRESENTED ONE SHAPE AS A CLASS.** WHAT IT SAID, VERBATIM:
    *"**MEASURED**, it does not fire on the clean tree (`PASS — 144 assertions, 0 violations`, and
    the whole 30-line register byte-identical) **nor on a legitimate optional root object that is
    not a dial** (arm `C16`, `PASS — 144`)."* **The second half was not a measurement of a class.**
    `C16` is ONE benign shape — an object with no `state` anywhere — generalised into a claim about
    every legitimate optional root object. `CD-ASR-WO3-07` (F4) measured two members of that class
    that **do** fire. *** **THE WORKED EXAMPLE IS `jurisdiction.state` — A US STATE CODE.** *** A
    root `jurisdiction` object carrying `country` and a two-letter `state` turns this constitutional
    instrument **RED** (`FAIL — 2 violation(s)`, `CD-CALM-SLOTS-007`'s undecidable limb,
    `['jurisdiction']`), and so does a root `run_provenance` whose nested `pipeline` declares
    `state: {enum: [QUEUED, RUNNING, FINISHED]}` (`FAIL — 2`, `['run_provenance']`). **Neither has
    any bearing on whether missing data renders as calm.**

    **THE BEHAVIOUR IS NOT CHANGED AND THE RULING STANDS.** `PROJECT_LEAD_SEAT_02` ruled the LOUD
    form correct — a false positive costs one seat one look at one contract; a false negative costs
    the constitution — and `CD-ASR-WO3-07` recorded that it does not contest that ruling. **WHAT IS
    TRUE INSTEAD:** this check fires on **any** root property that declares a property named
    `state`, whatever that property means and whatever its subschema's shape. MEASURED, it does not
    fire on the clean tree (`PASS — 144 assertions, 0 violations`) or on arm `C16` — **two shapes,
    and that is two measurements and not a class.** A reader who meets a red instrument on a US
    state code has met this limit working as ruled, not a defect: the remedy is to rename the key,
    or to bring the contract addition to the Product Authority, and never to loosen the guard.

    **(c) SUPERSEDED AGAIN AT `16B-FIX-4` — (a)'s OWN REPLACEMENT SENTENCE WAS FALSE IN THE SAME
    WAY AS THE ONE IT REPLACED, AND `CD-ASR-WO3-08` (F3) MEASURED IT.** The word doing the damage
    was **ANY**. `FX10` corrected the SHAPE axis and then re-committed the identical
    over-generalisation on the **declaration-keyword** axis: a `state` declared under
    `patternProperties`, introduced by `dependentSchemas`, reached by `$dynamicRef`, or reached
    past thirty-two `$ref` hops was classified **not a dial** and was **silent** — four root
    properties that DECLARE a property named `state` and on which the check did not fire.
    **WHAT IS TRUE AT `16B-FIX-4` (`FX12`), AND IT IS TWO SENTENCES BECAUSE IT IS TWO LIMBS:** this
    check fires on any root property that declares a property named `state` under `properties`,
    `required` or `dependentRequired` — the keywords whose property **names** it reads — whatever
    that property means and whatever its subschema's shape; **and** it fires on any root property,
    dial or not, whose shape it **cannot fully read** (`DECLARED LIMIT 14`). The four spellings
    above now reach the second limb, and so does a fifth nobody in the chain had named (arm `C27`)
    — not because they are listed, but because they are not readable.
13. **A `$ref` CARRYING AN ASSERTING SIBLING IS REPORTED, NOT FOLLOWED — DENY BY DEFAULT AT THE
    RESOLVER.** *** NEW AT `16B-FIX-3` (`FX9`, closing `CD-ASR-WO3-07` F1). *** Both contracts
    declare `"$schema": "https://json-schema.org/draft/2020-12/schema"`, and **in 2020-12 keywords
    sibling to `$ref` ARE APPLIED** — the one thing draft-07 did differently. `_resolve` now
    reports, **at every hop of the chain**, any key beside a `$ref` that is not one of the pure
    annotations in `REF_INERT_SIBLINGS` (`$comment`, `title`, `description`, `default`,
    `deprecated`, `readOnly`, `writeOnly`, `examples`). A branch reached through such a chain is
    `CD-CALM-BRANCHES-006`; a root property reached through one is UNDECIDABLE and
    `CD-CALM-SLOTS-007`; the union itself is `CD-CALM-BRANCHES-006`.

    **THE REMEDY CHOSEN, AND WHY, BECAUSE TWO WERE OFFERED.** The alternative was to return the
    target **merged** with its siblings. **A dict merge is not 2020-12's semantics.** `$ref` +
    siblings is a **conjunction** of two schema objects, and `additionalProperties`,
    `unevaluatedProperties` and `unevaluatedItems` are evaluated against the annotations of **their
    own** schema object: a target `{"properties": {"a": ...}}` conjoined with a sibling
    `{"additionalProperties": false}` admits nothing but `{}`, while the **merged** object admits
    `{"a": ...}`. **A merge can therefore admit documents THE NODE AS WRITTEN REFUSES — it can only
    ever WEAKEN this instrument, silently, which is the exact failure class F1 is.**
    Deny-by-default cannot weaken it; it can only over-report.

    **THE COST, PRICED:** a contract that legitimately narrows a `$ref` with a sibling keyword turns
    this instrument red until an increment prices composition properly. **IT COSTS NOTHING TODAY,
    AND THAT IS MEASURED RATHER THAN ASSUMED:** the public contract carries **four** `$ref` nodes
    with a `description` sibling (`as_of_utc`, `published_utc`, `inputs_used`, `degraded_inputs`)
    and the private contract none, so the inert list is load-bearing — a resolver that denied on
    **any** sibling would turn the **clean tree** red. The clean run is unchanged at `PASS — 144
    assertions, 0 violations`, `C10`/`C15`/`C21` are unchanged at `PASS — 158`, and no arm of
    `C1`–`C17` changed its census.

    **WHAT IS STILL NOT COVERED:** `_synthesise` still resolves a property's subschema to harvest
    `const`/`enum` candidates and does **not** deny there — deliberately, because the candidate it
    picks is validated by `jsonschema` against the **unresolved** subschema, which applies `$ref`
    siblings correctly, so the authority on that decision is the same library the gate validates
    with and not this resolver. **And the class is not bounded:** `C18` and `C19` are two members of
    a class whose size nobody has measured — `CD-ASR-WO3-07` said so of its own finding and it is
    repeated here rather than quietly dropped. **NOT PROVED TO BE CARRIED ANYWHERE:** nothing
    outside this instrument reads `$ref` siblings at all.

    **SUPERSEDED AT `16B-FIX-4` ON ONE SENTENCE, STATED AND NOT ERASED (`CD-RULE-004`,
    `PBG-CONT-003`) — `FX14`, `CD-ASR-WO3-08` F4. THE RULING AND THE BEHAVIOUR ARE UNCHANGED.**
    WHAT THIS LIMIT SAID, VERBATIM, IN ALL THREE PLACES: *"A merge can therefore admit documents
    **neither** schema admits."* **That is false, and not merely unmeasured.** MEASURED BY THIS
    SEAT (`CD-ENG-WO3-09`) with the gate's own library, `jsonschema 4.10.3`,
    `Draft202012Validator`, over **six** sibling keyword sets × **nine** documents × **both** merge
    directions = 108 combinations: `MERGE ADMITS WHAT THE NODE AS WRITTEN REFUSES -> 11 hits`;
    `MERGE ADMITS WHAT NEITHER SCHEMA OBJECT ADMITS -> 0 hits`. And it is not a search gap: under
    `{**target, **sibling}` every sibling key survives into the merged object, so
    `sibling(D) = False` forces `merged(D) = False`, and symmetrically for the other direction —
    **a document the merge admits is always admitted by at least one of the two, so the clause
    describes an empty set.** `CD-ASR-WO3-08` measured 10 hits over its own set and 0 for the false
    clause; this is an independent re-measurement, not a relay, and the two agree.
    **WHAT IS TRUE INSTEAD, AND IT CARRIES THE WHOLE CONCLUSION: a merge can admit documents THE
    NODE AS WRITTEN REFUSES.** The node as written is a conjunction; the merge is not; the merge is
    therefore `>=` the conjunction and can only WEAKEN this instrument. That is strictly weaker to
    prove, it is what was measured, and the decision to deny rather than merge rests on it
    entirely. **The false clause bought nothing.** *** **THIS IS THE THIRD SENTENCE ON THIS ROW TO
    BE SUPERSEDED FOR OVERSTATING IN THE SAME DIRECTION AS THE SENTENCE IT REPLACED** (`DECLARED
    LIMIT 10`, then `12`(a), now `13`). The pattern is recorded because it is the pattern and not
    the instance that is the defect: on this row a replacement sentence has three times been
    written to the widest claim its author believed rather than to the narrowest claim their
    evidence carried. `DECLARED LIMIT 14` is written to what was measured and its cost column is a
    measurement and not an estimate. ***
14. **A ROOT PROPERTY THIS CHECK CANNOT FULLY READ IS UNDECIDABLE, NOT "NOT A DIAL" — THE DEFAULT
    IS INVERTED AT THE RECOGNISER.** *** NEW AT `16B-FIX-4` (`FX12`, closing `CD-ASR-WO3-08` F1 as
    a **class**, and F2 and F5 with it). ***

    **WHAT "CANNOT FULLY READ" MEANS, PRECISELY, AND IT IS A PROPERTY OF THE NODE AND NOT OF A LIST
    OF ATTACKS.** `_dial_bearing` may return `False` about a node only when **every keyword the
    node actually declares**, at every node the walk visited, is in `_READABLE_KEYWORDS` — the
    union of exactly three declared, closed sets and nothing else:

    * `_SUBSCHEMA_KEYWORDS` minus `_NAME_BEARING_APPLICATORS` — keywords carrying subschemas that
      the walk **descends into**, so it has looked underneath every one of them;
    * `_NAME_DECLARING_KEYWORDS` (`properties`, `required`, `dependentRequired`) — keywords whose
      keys or entries are **literal property names**, which this check reads;
    * `_INERT_KEYWORDS` — the remaining 2020-12 keywords that carry no subschema and name no
      property, enumerated from the specification's own vocabularies.

    **Everything else is unreadable and makes the node UNDECIDABLE.** That includes
    `patternProperties`, `propertyNames` and `dependentSchemas` (descended into, so a dial under one
    can still come back `True`, but their **keys** are names this check does not evaluate — a regex,
    a constraint, a trigger property), `$id`, `$dynamicRef`, `$dynamicAnchor`, `$recursiveRef`, any
    keyword of a private vocabulary, any keyword of a draft not yet written, and any misspelling of
    a keyword that does exist. `_resolve` reaching `REF_CHAIN_CAP` is the same answer for the same
    reason.

    *** **WHY DENY-BY-DEFAULT AND NOT A LIST, AND THIS IS THE WHOLE POINT OF THE INCREMENT.** ***
    The superseded walk asked a list of keywords **it had thought of** whether they were present, so
    a keyword it had not thought of was invisible and the node fell through to `False`. **That is
    why this recogniser was escaped four times by four spellings of one idea** — `A306` a new state
    vocabulary, `A307` a boolean `state`, `A308` `patternProperties` / `dependentSchemas` /
    `$dynamicRef` / a chain past the cap — **and why each fix closed the spelling it was shown and
    the next auditor found another** (`PO-DECISIONS-0026` ruling 10,
    `GUARD_THE_INSTANCE_NOT_THE_CLASS`). Asking the **node** instead of the list means the deny
    class is the **complement** of a finite written set, which no future spelling can leave.

    **THE FALSIFIER WAS BUILT AND RUN RATHER THAN ARGUED.** Arm `C27` is a fifth spelling none of
    the four audits used — `propertyDependencies`, an applicator proposed for the draft **after**
    2020-12 — which appears **zero** times in the instrument (`grep -c propertyDependencies` → `0`)
    and which was a live escape on the superseded instrument (`PASS — 144 assertions, 0 violations`
    with the gate **ADMITTING** `{state: STALE, reason: FEED_DEAD, detail_level: 'calm'}` on **both**
    surfaces) and is `FAIL — 2` `CD-CALM-SLOTS-007` here. Three more never-named spellings behave
    identically: a private `x-` vendor keyword, an invented `slotShape`, and **`propertys` — a
    one-letter typo of `properties`, the likeliest real-world author error of all, and silent before
    this fix.**

    **THE COST, MEASURED AND NOT ESTIMATED — THE FALSE-POSITIVE TAIL IS REAL AND IT IS PRICED.**
    Eight benign root properties, none of them a dial, none declaring a `state` subschema, each
    added to both contracts on its own pristine extraction: **six** turn this instrument red that
    were green before — a `patternProperties` metrics bag, a `propertyNames`-constrained map, a
    benign `dependentSchemas` pair, a subschema carrying its own `$id`, **a property carrying a
    custom `x-` annotation**, and an object whose `required` names `state` without giving it a
    subschema. **Two** benign controls stay green — a plain closed object and an array of strings —
    so the tail is a tail and not a blanket. **The clean tree is unaffected, and that is the
    measurement that mattered most:** `PASS — 144 assertions, 0 violations`, exit 0, and the
    instrument's **full output** on the clean tree is byte-identical before and after this fix but
    for the absolute path string. `C1`–`C21` are unchanged, every one. **The ruled direction is the
    one taken:** a false positive costs one seat one look at one contract; a false negative costs
    the constitution. **The remedy when the tail bites is never to loosen the guard:** a keyword
    genuinely inert here belongs in `_INERT_KEYWORDS` with the reason written down, and a keyword
    that carries a subschema belongs in `_SUBSCHEMA_KEYWORDS` so the walk descends it. Both are
    edits a reader can audit; neither is a silent `False`.

    **WHAT THIS DOES NOT CLOSE, SAID PLAINLY.** It does not close `DECLARED LIMIT 12`'s residue — a
    dial that discriminates on a differently-**named** key is still `False` and still silent, and
    that limit is judged honestly drawn and stands as a condition on 16C's dispatch. **And a root
    property that declares nothing at all — `{"type": "object"}` — is still `False`:** every keyword
    it declares is readable, so it is read, and there is no `state` in it. That is not the class
    this fix bounds, and it is named here rather than left for the next audit to find. **NOT PROVED
    TO BE CARRIED ANYWHERE:** nothing outside this instrument reads `_READABLE_KEYWORDS`.

    *** SUPERSEDED AT `16B-FIX-5` ON ITS COST COLUMN, STATED AND NOT ERASED (`CD-RULE-004`,
    `PBG-CONT-003`) — `FX17`, `CD-ASR-WO3-09` F5. THE RULING AND THE BEHAVIOUR ARE UNCHANGED. ***
    **What the cost column said, in all three places:** *"Eight benign root properties ... six turn
    this instrument red ... two benign controls stay green."* **That is a SAMPLE described as a
    MEASUREMENT.** The auditor found a **seventh** red shape in about a minute — a `contentSchema`
    carrying a `state` — named by nothing in the list of six. **And the sentence directly above it
    promised the opposite:** `DECLARED LIMIT 13`'s supersession ends *"DECLARED LIMIT 14 is written
    to what was measured and its cost column is a measurement and not an estimate"*, and the cost
    column then enumerated six **instances** of a **class**, in a file whose entire thesis is
    *guard the class and not the instance*. **That is the same error the code had just fixed,
    written in prose**, and it is the fourth sentence on this row superseded for overstating in the
    same direction as the sentence it replaced (`10`, then `12`(a), then `13`, now `14`'s cost
    column).

    *** THE TAIL IS A CLASS, AND THIS IS THE CLASS. *** A root property is UNDECIDABLE — and
    therefore `CD-CALM-SLOTS-007`, whether or not it is a dial — **exactly when, at some node the
    walk visits, at least one of these three holds:**

    - **(a) an unreadable keyword.** The node declares a keyword outside `_READABLE_KEYWORDS`:
      every 2020-12 keyword that list omits, every keyword of a draft not yet written, every
      private or vendor keyword, and every misspelling of every keyword. **An infinite set by
      construction, which is the point.**
    - **(b) a `state` it cannot classify.** The node **names** a property called `state` — in any
      position `_declared_names` reads — and does not give it a `const`/`enum` that intersects
      `DECLARED_STATES`.
    - **(c) a walk that did not complete.** A `$ref` that does not resolve, a chain past
      `REF_CHAIN_CAP`, an asserting sibling of a `$ref`, or nesting past the depth cap.

    **Those three are the only limbs in the function that set `undecidable` or return `None`, so
    the tail has no other members.** That is a property of the code, checkable by reading it. The
    shapes below are **examples of that class and are explicitly non-exhaustive.**

    **THE EXAMPLES, RE-MEASURED AT `16B-FIX-5` over twenty-one probes put directly to
    `_dial_bearing`, none of them a dial.** **Eleven red:** a `patternProperties` metrics bag · a
    `propertyNames`-constrained map · a benign `dependentSchemas` pair · a subschema carrying its
    own `$id` · an ordinary `x-` vendor annotation · an object whose `required` names `state`
    without a subschema · a `contentSchema` carrying a `state` (the auditor's seventh) · **and the
    four the alphabet correction adds — an `enum` of objects naming `state` (an ordinary workflow
    status, not a dial), an object `const` naming `state`, an `enum` member with a `state` nested
    two levels inside it, and a `dependentRequired` KEY named `state`.** **Ten green:** a scalar
    string `enum` · a scalar `const` · a numeric `enum` · a plain closed object · an `enum` of
    objects naming NO `state` · an object `const` naming NO `state` · a `default` annotation
    carrying a whole dead-feed reading · an `examples` annotation carrying one · arm `C16`'s benign
    optional root object. The twenty-first probe is the real dial slot spelling and comes back
    `True`, which is the arm that stops this probe set being one-sided.

    *** HOW FAR THE ALPHABET CORRECTION MOVED THE TAIL, IN NUMBERS. *** Over that same
    twenty-one-probe set: `dd40407` → **7 red / 13 green**; `16B-FIX-5` → **11 red / 9 green**.
    **The four that moved are exactly limb (b)'s new members and nothing else moved.** Every probe
    that does not **name** a property called `state` is unchanged — including both annotation
    probes, which is the measured form of the claim that `default` and `examples` assert nothing.
    **The clean tree did not move** (`PASS — 144 assertions, 0 violations`, exit 0), **nor did any
    of `C1`–`C28`**, and neither envelope contract carries an object-valued or array-valued
    `enum`/`const` anywhere, which is why.

    **The ruled direction is the one taken, and the remedy when the tail bites is never to loosen
    the guard:** a false positive costs one seat one look at one contract; a false negative costs
    the constitution. A keyword genuinely inert here belongs in `_INERT_KEYWORDS` with the reason
    written down; a keyword that carries a subschema belongs in `_SUBSCHEMA_KEYWORDS`; a property
    that means something other than a dial state and is called `state` is renamed, or the addition
    goes to the Product Authority. All three are edits a reader can audit. None is a silent `False`.

15. **THE ALPHABET — WHERE A PROPERTY NAME MAY BE WRITTEN, AND HOW DEEP THIS CHECK LOOKS FOR ONE.**
    *** NEW AT `16B-FIX-5` (`FX15`, closing `CD-ASR-WO3-09` F1 — the only thing found wrong with
    `FX12`). *** `DECLARED LIMIT 14`'s inversion is a **true** universal quantification and its
    falsifier passed — **but over KEYWORD NAMES only.** It never asked what a readable keyword's
    **value** asserts; `enum` and `const` take **instance values**; an object instance value
    **names properties**. So `{"enum": [<a LIVE reading>, <a STALE reading whose detail_level is
    "calm">]}` was fully read, named no `state` as far as the walk could see, and came back a clean
    `False` — **not a dial** — with this instrument reporting `PASS — 144 assertions, 0 violations`
    while the live gate **ADMITTED** a dead feed rendering as `calm` on **both** surfaces. **The
    quantifier was right; the alphabet was wrong.**

    **WHAT IS READ NOW, AND THE LIST IS AGAINST THE SPECIFICATION AND NOT AGAINST THE ATTACKS.** A
    property name can appear in a 2020-12 schema in exactly these positions: `properties` keys ·
    `required` members · `dependentRequired` **keys** and values · the property names inside `enum`
    members and inside a `const` value · `patternProperties` keys, `propertyNames` and
    `dependentSchemas` keys (**not read** — they are in `_NAME_BEARING_APPLICATORS`, so the node is
    UNDECIDABLE before the question is asked) · `default` and `examples` (**not read, and
    deliberately**: they are annotations, they assert nothing, and a `state` named inside one
    constrains no document and can admit none. `enum` and `const` **assert**. That is the whole
    distinction and it is the auditor's).

    *** `enum` AND `const` STAY IN `_INERT_KEYWORDS`, AND THAT IS A PROHIBITION AND NOT A
    PREFERENCE. *** They carry no **subschema**, so there is nothing under them to descend into,
    and the auditor **measured** that making them unreadable turns every ordinary
    `{"type": "string", "enum": [...]}` root property UNDECIDABLE and explodes the tail. **The
    value is read; the keyword stays inert.**

    **DECISION 1 — DEPTH, DECLARED AND PRICED.** An `enum` member is arbitrary JSON and may nest.
    This walk collects names **at every depth of the value, through objects and arrays alike**,
    capped at `INSTANCE_WALK_CAP`. The alternative — the top-level keys of each member only — would
    have closed the shape the auditor wrote and left `{"enum": [{"reading": {"state": ...}}]}`
    open, **which is this row's entire history**. **The price is a wider false-positive class:** any
    node whose `enum` or `const` value contains, anywhere inside it, an object with a key called
    `state`. It is `DECLARED LIMIT 14`'s limb (b), it is measured there, and it moved the tail by
    exactly four probes out of twenty-one. **Reaching the cap is not a silent success:** the walk
    returns `INSTANCE_TOO_DEEP`, a sentinel no contract can declare as a property name, so it enters
    the declared set, can never equal `state`, and can never make the node `True`.

    **DECISION 2 — `const`, SAID EXPLICITLY RATHER THAN LEFT TO BE INFERRED.** **A `const` that is
    not an object or an array names nothing.** `{"const": "equity_crash"}` and
    `{"type": "string", "enum": ["a", "b"]}` contribute the **empty set** and are still answered
    `False` — measured, and it is why the tail did not explode. Only the **keys** of object instance
    values are collected, so `{"enum": ["state", "detail_level"]}` — an ordinary string enum whose
    members happen to be those words — names nothing either.

    **AND ONE POSITION NOBODY ATTACKED, FIXED ANYWAY: the KEYS of `dependentRequired`.** A key there
    names a property as literally as a member of its value list does —
    `{"dependentRequired": {"state": ["reason"]}}` says *if `state` is present then `reason` must
    be* — and the superseded code read the values and not the keys, so that node answered a clean
    `False` while admitting `{"state": "STALE", "detail_level": "calm"}`. **Measured as a live
    escape at `dd40407` and closed here** (arm `C34`: `PASS — 144` before, `FAIL — 2` after, with
    the live gate ADMITTING the calm-carrying document on both surfaces at `dd40407`). **The point
    of an alphabet correction is to be complete, not to close the shape it was shown.**

    **WHY WIDENING THE ALPHABET IS SAFE WITHOUT RE-AUDITING EVERYTHING DOWNSTREAM.** The only
    consumer of `_declared_names` is the test `"state" in declared`, and the limb that test guards
    sets `undecidable = True`. **More names can therefore only ever produce more UNDECIDABLE and
    never more `False`** — the widening is monotone in the safe direction.

    **WHAT THIS DOES NOT CLOSE, SAID PLAINLY.** It reads the **name** `state`. A dial that
    discriminates on a differently-**named** key is `DECLARED LIMIT 12`'s residue: still `False`,
    still silent, and still a stated condition on 16C's dispatch. **NOT PROVED TO BE CARRIED
    ANYWHERE:** nothing outside this instrument reads `_declared_names`.

16. **THE TWO RECOGNISERS AGREE ABOUT "READABLE" BY CONSTRUCTION, AND A BRANCH THIS CHECK CANNOT
    FULLY READ HAS NO IDENTIFIED STATE.** *** NEW AT `16B-FIX-5` (`FX16`, closing `CD-ASR-WO3-09`
    F2). *** `FX12` was applied at the **root-property** recogniser only. `_branch_states` read
    `resolved["properties"]["state"]["const"]` and nothing else — no readability test, no
    undecidable outcome — so a branch that resolved to a perfectly good `state.const` **while also
    carrying a keyword this check cannot read** was returned as an identified, accepted branch and
    the walk went on as though it had looked at all of it. Measured by the auditor on `dd40407`:
    `{"properties": {"state": {"const": "UNKNOWN"}, ...}, "patternProperties": {"^x_": {}},
    "additionalProperties": false}` → `_branch_states` **accepted** it as `UNKNOWN` with no
    violation, while `_dial_bearing` on the same node answered `True`.

    **HOW THEY ARE PROVED TO AGREE, AND IT IS NOT A COMMENT ASSERTING THAT THEY DO.** Both call
    `_unreadable_keywords`, and the phrase `not in _READABLE_KEYWORDS` has **exactly one
    EXECUTABLE occurrence in the file, inside that function** — `grep -n` returns five hits and the
    other four are this sentence and its three restatements, which a reader can see at a glance.
    There is nothing left for the two recognisers to drift from, and the claim is **greppable**
    rather than argued.

    **THE COST, MEASURED.** A branch carrying **any** unreadable keyword now has `state is None`,
    is reported as `CD-CALM-BRANCHES-006` **with the keyword named**, and is **not driven** — the
    same treatment a branch whose `state` cannot be read has always had. On the clean tree the
    three branches declare only `type`/`additionalProperties`/`required`/`properties`/`description`,
    so it costs nothing today: `PASS — 144`, and `C6`/`C11`/`C12`/`C17`/`C18`/`C19` — every arm that
    touches a branch — produce output byte-identical to `dd40407`.

    **WHAT THIS DOES NOT CLOSE, SAID PLAINLY.** The two recognisers now agree about **readability**;
    they are still not one mechanism. `_dial_from_branch`'s `CONDITIONAL_KEYWORDS` and
    `ref_siblings` guards remain separate and are still needed, because `if`/`then`/`else`/`allOf`/
    `anyOf`/`not` are all perfectly **readable** and are refused for a different reason — the branch
    admits more documents than the one this check builds. **Two guards, two reasons, one shared
    notion of "readable"** — and nobody has proved the conditional set complete. **And the branch
    side is only exercised for the `oneOf` under `#/$defs/dial_reading`:** a union spelled any other
    way is `DECLARED LIMIT 9`'s territory, not this one's.

17. **WHAT `RULE CC` CLOSES, AND — SAID FIRST AND NOT LAST — WHAT IT DOES NOT.** *** NEW AT
    `16B-CONTRACT-CLOSURE` (`CC-1`/`CC-2`/`CC-3`), under `PO-DECISIONS-0028` ruling 1, which
    replaced a RECOGNISER at the root with a CLOSED PARTITION over a FINITE SET. *** Three
    assertion codes are new and together they are the architectural close.

    * **`CD-CALM-ROOT-008` — `RULE CC`.** Every property of an envelope contract's root
      `properties` is **EXACTLY ONE** of **(a)** a CANONICAL DIAL SLOT spelled literally
      `{"$ref": "#/$defs/dial_reading"}`, that one key and no sibling keyword; or **(b)** a
      DECLARED NON-DIAL PROPERTY whose name is on the finite written allowlist
      `NON_DIAL_ROOT_PROPERTIES` **and** which is AFFIRMATIVELY PROVED, by driving the LIVE GATE
      with a calm-carrying object in its place, incapable of carrying a `detail_level`.
      **ANYTHING ELSE IS A VIOLATION. NO RECOGNISER IS CONSULTED, AND THERE IS NO THIRD CASE AND
      NO SILENCE.** `CD-CALM-SLOTS-007` compares `dial_bearing` against `found`, so **a root
      property the recogniser answers `False` about is in NEITHER SET, the comparison is
      satisfied, and the slot is INVISIBLE** — the hole `CD-ASR-WO3-10` proved unclosable by any
      list (`A310-F1` a nest past the depth cap, `A310-F2` the discriminator spelled `status`,
      `A310-F3` `present: false` with a stale stamp). **THOSE ARE NOT CLOSED BY `RULE CC` — THEY
      ARE UNREACHABLE**, because none of them is limb (a) or limb (b). Both premises of
      exhaustiveness are **ASSERTED and not assumed**: the root declares
      `additionalProperties: false`, and the root declares no keyword outside
      `_ROOT_STRUCTURAL_KEYWORDS`. Adding a name to the allowlist is a **PRODUCT act**
      (`PBG-AUTH-005`): the instrument goes RED and STAYS RED until a human rules on it.
    * **`CD-CALM-CANON-009` — THE CANONICAL PATH, MANDATED IN THE CONTRACT AND ASSERTED HERE.**
      Inside `#/$defs/dial_reading` the discriminator is at `properties.state`, at depth ONE,
      pinned per branch at `properties.state.const`. Both contracts now declare
      `"required": ["state"]` on the union and carry a normative `RULE CC` clause in their
      `description`. Asserted per surface, counted: the union is `additionalProperties: false`,
      declares `properties.state` and REQUIRES `state`; **every** branch is
      `additionalProperties: false`, REQUIRES `state`, and declares `properties.state.const` as a
      STRING; and **every** branch REQUIRES at least one property typed `#/$defs/utc_timestamp` —
      the freshness stamp, asserted by TYPE and never by NAME, because `VALUE`/`DEGRADED` require
      `as_of_utc` while `UNKNOWN` requires `since_utc`. **A BRANCH THAT REQUIRES NO TIMESTAMP
      CANNOT PROVE FRESHNESS AND IS A VIOLATION.** The ABSENCE of the canonical path is its **own**
      named violation and is deliberately NOT folded into `CD-CALM-BRANCHES-006`, which reports a
      recognition failure and would read as the wrong sentence. **A `description` IS NOT AN
      ENFORCEMENT POINT** — `absent_data_detail_level`'s own description records 16A, where the
      guarantee was *"asserted only in PROSE"* while the gate admitted a calm `UNKNOWN` dial on
      both surfaces. The prose states the mandate; these codes enforce it.
    * **`CD-CALM-FRESH-010` — THE AFFIRMATIVE VALUE CHECK OVER THE NOW-CLOSED ALPHABET**, which is
      `PO-DECISIONS-0027` ruling 5 **MADE ACHIEVABLE** (`PO-DECISIONS-0028` ruling 2). A branch may
      reference the calm-bearing `#/$defs/detail_level` **IF AND ONLY IF** its
      `properties.state.const` is in `PRESENT_STATES` **and** it requires a freshness stamp;
      **every other branch MUST reference a vocabulary from which `calm` is ABSENT.** That is the
      affirmative form: it does not ask *"is this state on my list of bad ones?"* — the question
      nine audits defeated by naming a state nobody had listed — it asks *"has this branch PROVED
      present-and-fresh?"*. **A never-before-named state must arrive as a NEW BRANCH; a new
      branch's state is NOT in `PRESENT_STATES`; therefore it CANNOT CARRY `calm` — BY
      CONSTRUCTION, OVER A CLOSED SET, AND NOT BY RECOGNITION OVER AN OPEN ONE.** The vocabulary is
      judged by its VALUES and never by the name of the `$def` it comes from (`CD-PL-F169`,
      `CD-ASR-WO3-02` F06/F07). **The VACUITY direction is asserted too and carries equal weight:**
      a branch that HAS proved present-and-fresh and CANNOT carry `calm` is also a violation,
      because PID §4 makes `calm` the base case and a contract that cannot express it is enforcing
      silence.

    **THE CONCLUSION THAT FOLLOWS, AND ONLY THIS ONE:** *a contract edit cannot open a
    calm-over-unknown hole at the ROOT of either envelope without this instrument going RED*,
    because the hole must arrive as a root property and every root property is limb (a), limb (b)
    or a violation.

    *** NOW THE BOUNDARY, NAMED RATHER THAN LEFT FOR THE NEXT AUDITOR. THE ARGUMENT IS ABOUT THE
    TWO ENVELOPE CONTRACTS THIS INSTRUMENT LOADS AND NOTHING ELSE. ***
    **(a)** It is not a claim about documents the gate never sees — `DECLARED LIMIT 4`'s closing
    paragraph, unchanged.
    **(b)** It is not a claim about a contract this instrument is not looking at —
    `$CD_CONTRACTS_DIR` is `DECLARED LIMIT 1`; the check REFUSES TO RUN when it resolves elsewhere
    and does **not** prevent the route. **NOT PROVED TO BE CARRIED ANYWHERE.**
    **(c)** It is a claim about the **ROOT**, not about every position in the document. Depth
    inside a limb (b) property is covered by the LIVE GATE probe and by **nothing structural**, and
    only for the **two** shapes in `CALM_BEARING_PROBES`. **THAT IS TWO SHAPES AND IT IS NOT A
    CLASS**, and it is written that way on purpose: four sentences on this row have already been
    superseded for describing a sample as a measurement (`DECLARED LIMIT 10`, `12`(a), `13`, and
    `14`'s cost column).
    **(d)** The freshness assertion keys on the definition object `#/$defs/utc_timestamp` **by
    identity**: a stamp typed by an inline copy of the same pattern is REPORTED, not accepted, and
    **renaming that `$def` turns this instrument RED**. The remedy is to price the rename, never to
    loosen the assertion.
    **(e)** `DECLARED LIMIT 12`'s residue is **not** closed at the recogniser and is not claimed to
    be — `_dial_bearing` still answers `False` about a dial discriminating on a differently-named
    key. **WHAT CHANGED IS THAT THE GUARANTEE NO LONGER RESTS ON IT:** such a dial cannot reach a
    published envelope as a ROOT property without failing `RULE CC`. The recogniser is RETAINED as
    a **SECOND instrument** (`PO-DECISIONS-0028` ruling 3 — `8398741` is preserved, nothing
    reverted), and a second instrument's residue is a weaker thing than a sole guard's.
    **(f)** `PRESENT_STATES` is typed in, like `DECLARED_STATES` and for the same reason: whether a
    NEW state means the data is PRESENT is product meaning (`PBG-AUTH-005`), so a new state makes
    this instrument RED until a human rules — which is the mechanism by which `CC-3` refuses `calm`
    to a never-before-named state rather than a list of bad names.
    **(g)** **NOTHING OUTSIDE THIS INSTRUMENT READS `RULE CC`.** The contracts now STATE the mandate
    in their `description`s, and a `description` refuses nothing. **NOT PROVED TO BE CARRIED
    ANYWHERE.**

    *** AND ONE MORE, WHICH IS `CC-4` AND IS SEPARATE (`PO-DECISIONS-0028` ruling 4). ***
    `DECLARED LIMIT 15`'s heading said **"REACHING THE CAP IS NOT A SILENT SUCCESS"** and the code
    did the opposite. `_instance_declared_names` returned the sentinel `INSTANCE_TOO_DEEP` at its
    depth cap and **the sentinel had ZERO EXECUTABLE CONSUMERS**, so reaching the cap produced a
    clean `False` — the only silent answer this instrument has. **MEASURED, ONE INTEGER APART, at
    `8398741`:** a `state` nested inside an `enum` member at depth 24 -> `None`; at depth 25 ->
    `False`. `_dial_bearing` now sets `undecidable = True` on that sentinel, which is `DECLARED
    LIMIT 14` limb (c). **MEASURED AFTER:** depths 1/5/20/22/23/24 -> `None`, **UNCHANGED**; depths
    25/26/30/40 -> `None`, **MOVED from `False`**. `RULE CC` makes a nest this deep unreachable at
    the root anyway; **the cap is fixed regardless, because a cap that fails open is a defect
    whether or not anything reaches it.**

### Numbering — because `CD-ASR-WO3-06` could not verify it and said so

**DECLARED LIMIT NUMBERS ARE PER REGISTER ROW, NOT PER FILE.** The seventeen above (**twelve until
`16B-FIX-3`, which added `13`; `14` added at `16B-FIX-4`; `15` and `16` added at `16B-FIX-5`; `17`
added at `16B-CONTRACT-CLOSURE`**) are
`CD-RT-001-MISSING-DATA-NEVER-CALM`'s, and they are said identically here, in the header of
`tools/register/check_missing_data_never_calm.py`, and in `required-tests.yaml` (`CD-RULE-004`,
three places). The **sibling** row `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` has its **own** independent
1–12 sequence, spread across `tools/register/check_judgement_path_doors.py` (1–4, 7–9),
`src/crash_detector/admission.py` (5–6) and `required-tests.yaml` (10–12). **Both rows live in
`required-tests.yaml`, so a bare "DECLARED LIMIT 12" is ambiguous there and always was — quote the
row id with the number.**

## Negative control

An envelope carrying `detail_level: "calm"` on a dial in the `UNKNOWN` or `DEGRADED` state
ADMITTED by `refuse_unless_publishable` on either surface — by ANY route. The class includes,
and is not limited to: either `$ref` on either contract's `dial_reading_degraded` or
`dial_reading_unknown` branch restored to `#/$defs/detail_level` (**including only ONE branch
on ONE surface**); `"calm"` added back into the `#/$defs/absent_data_detail_level` enum so the
`$ref` target keeps its name and loses its meaning; the branch `detail_level` requirement
dropped so the parent `dial_reading`'s full-vocabulary property is what applies; **a FOURTH
branch appended to `#/$defs/dial_reading.oneOf` that permits the full vocabulary on a
missing-data state (arm `C6`)**; **a missing-data branch that accepts a level outside the
declared vocabulary (arm `C8`)**; **an optional additional dial slot spelled with any `$ref`
other than `#/$defs/dial_reading` (arm `C9`)**; or any change to `refuse_unless_publishable`
that stops the closed schema being applied.

### *** THE SENTENCE THAT FOLLOWED THIS LIST WAS FALSE. SUPERSEDED AT `16B-FIX`, NOT ERASED. ***

> **WHAT IT SAID, VERBATIM:** *"The instrument fails on all of these."*

**IT DID NOT.** `CD-ASR-WO3-05` (F2) measured the named member *"the branch `detail_level`
requirement dropped so the parent `dial_reading`'s full-vocabulary property is what applies"* on
a tree where `detail_level` was removed from `required` on `dial_reading_unknown` and
`dial_reading_degraded` on **both** contracts: the instrument reported
`PASS — 67 assertions, 0 violations` while the live gate **ADMITTED an `UNKNOWN` dial carrying no
`detail_level` at all, on both surfaces.** A governed artefact stated something measurably false,
and this project supersedes rather than deletes.

**WHAT IS TRUE INSTEAD, AND IT IS TRUE BY MEASUREMENT AND NOT BY ASSERTION.** The instrument now
carries a **field-absent** row and an **off-vocabulary** row for every missing-data branch, on
every slot, on both surfaces, and it FAILS on that tree — arm `C7`, `FAIL — 8 violation(s)`, all
`CD-CALM-GATE-001`. Each member of the class above is a measured arm of
`plants/WO3-INC16B/MANIFEST.md` with its violation count and the assertion that caught it, run
from its own pristine extraction. **A member of this class that is not a measured arm is a claim,
and this row no longer makes one.**

**AND — with equal weight — the VACUOUS DIRECTION IS ALSO A VIOLATION OF THIS ROW:**
`#/$defs/dial_reading_value.detail_level` narrowed so that **no** dial can ever read `calm`,
or any change that makes `elevated` or `acute` stop being admitted on a missing-data branch.
A tree on which nothing can be published is not a tree on which PID §3.2 holds, and this row
does not report it as one.

Detection is a **contrast**, and the validator computes it as one: the same declared command
must exit `0` on the clean subject and non-zero on the subject with the violation planted.
A clean arm that fails cannot be told apart from a broken harness, and a broken harness
detects nothing — the validator returns `UNDECIDABLE`, never `PASS`.

The negative control for this test is declared as run record **`RTR-WO3-0001`**.
That record does not exist yet. It is the run the **independent Assurance
seat** will produce — a distinct actor from the one that wrote this test. Until it exists
the validator computes `UNDECIDABLE` for this test and the gate stays shut, which is
correct: this seat may declare which run must evidence its guard, and may not supply it.

## What this contract does not claim

It does not claim the test passes. It does not claim the criterion is satisfied. It does not
admit any evidence: `latest_admitted_run` is null in the register and this seat cannot fill
it in, because an implementation may not certify itself (`PBG-SOD-001`, non-waivable).
