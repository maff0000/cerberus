#!/usr/bin/env python3
"""CD-RT-001-MISSING-DATA-NEVER-CALM — the LIVE GATE refuses a calm missing-data dial.

    python3 tools/register/check_missing_data_never_calm.py --root <subject tree>

CRITERION: `CD-AC-001` — *"Missing or stale input never renders as calm."* — and `PID §3.2`,
which is CONSTITUTIONAL in the same words. Authority: `PO-DECISIONS-0026` **ruling 9**:

    "The calm-over-unknown refusal currently holds only in `tests/`, and `tests/` do not feed
     the gate — a register-wired instrument PASSES identically on a tree where the fix is
     fully reverted. ... the guarantee must be carried by a live instrument, not a memorial
     in tests."

===========================================================================================
**WHY THIS INSTRUMENT EXISTS, IN ONE PARAGRAPH.** WO-3 increment 16A-FIX narrowed the
`DEGRADED` and `UNKNOWN` branches of both envelope contracts to `#/$defs/absent_data_detail_level`,
which does not contain `calm`. That closed a RED (`CD-ASR-WO3-03`) and an independent seat
proved it behaviourally. **But nothing the register reads would have noticed if it were
undone.** Reproduced by the Project Lead at increment 16B's dispatch: on a tree with all four
`$ref`s restored to `#/$defs/detail_level`, **every runnable register instrument still exits
0**, and the only failures anywhere are nine tests in `tests/test_detail_level.py` — a file no
register `execute:` line names. A memorial, not a guard. This file is the guard.
===========================================================================================

**IT IS BEHAVIOURAL AND NOT STRUCTURAL, AND THAT IS THE WHOLE DESIGN.** It does not read the
schemas as documents, does not look for the string `absent_data_detail_level`, and does not
assert that any `$ref` points anywhere. It builds candidate envelopes and puts them through
`crash_detector.publication.envelope_contract.refuse_unless_publishable` — **the function the
product itself calls before it writes anything** (`src/crash_detector/publication/publish.py`
lines 276-277) — and records what the gate actually did. A structural read of schema keys is
precisely what let this class of defect through three times on this project (`CD-PL-F169`,
`CD-ASR-WO3-02` F06/F07, `CD-ASR-WO3-03`): a check that reads the `$ref` TARGET NAME and never
opens the target passes a tree where `calm` has been put back inside the target's own enum.

Register instruments on this project ARE permitted to import the application — MEASURED, four
already do: `check_exact_type_admission`, `check_engine_no_witness_reach`,
`check_no_numeric_default`, `check_judgement_path_doors`. (`CD-RT-014`'s "the probe must not
import the application" rule binds `tools/probe/external_probe.py` and nothing else: an
EXTERNAL probe must be external. It does not bind a register check.)

===========================================================================================
WHAT IS ASSERTED — AND THE ADMITTING ROWS MATTER AS MUCH AS THE REFUSING ONES
===========================================================================================

The proposition, on **every** surface, at **every** dial slot, and — SINCE `16B-FIX` — on
**every branch of `#/$defs/dial_reading.oneOf`**, each one built from THAT BRANCH'S OWN
`required` + `properties` rather than from a document shape typed in here:

    absent-data branch · detail_level "calm"        ->  MUST REFUSE
    absent-data branch · NO detail_level KEY        ->  MUST REFUSE   *** NEW AT 16B-FIX ***
    absent-data branch · detail_level "banana"      ->  MUST REFUSE   *** NEW AT 16B-FIX ***
    absent-data branch · every other declared level ->  MUST ADMIT
    present-data branch · detail_level "calm"       ->  MUST ADMIT    *** THE VACUITY ARM ***
    present-data branch · every other declared level->  MUST ADMIT

*** THE TWO NEW REFUSING ROWS ARE A CORRECTION AND NOT A WIDENING (`FX2`, closing
`CD-ASR-WO3-05` F2). *** `tests/test_detail_level.py::_assert_missing_data_never_renders_as_calm`
has asserted `_dial_with_level(builder, None) == REFUSED` and
`_dial_with_level(builder, "banana") == REFUSED` since before this file existed, and
`CD-ASR-WO3-04`'s 30-row probe covered both. **BOTH ROWS WERE DROPPED WHEN THE PROPERTY MOVED
INTO THIS REGISTER-WIRED INSTRUMENT**, so the live guard was STRICTLY WEAKER than the memorial it
was built to supersede, while this row's own `negative_control` said in two governed artefacts
that "the instrument fails on all of these". It did not. **A replacement that quietly narrows
what it checks is how a guard becomes a certificate.** The token is `banana` and not something
cleverer on purpose: it is the memorial's own token.

*** **THE `MUST ADMIT` ROWS ARE NOT DECORATION.** An instrument that only checked "calm is
refused on an UNKNOWN dial" is satisfied by a contract that refuses everything, and — the case
this project's history says gets missed — by a contract in which NO dial can ever read `calm`
at all, on any branch. `calm` on a real number backed by real inputs is the entire reason
`calm` exists (PID §4: *"calm = dial + one line"*). A guard that cannot tell "the forbidden
thing is impossible" from "everything is impossible" is not guarding PID §3.2, it is enforcing
silence. **`CD-CALM-VACUITY-000` below asserts that this file's own expectation table still
contains the VALUE/calm admitting row**, so the vacuity arm cannot be quietly deleted from the
instrument that exists to carry it. ***

 CD-CALM-VACUITY-000  **THE INSTRUMENT'S OWN TABLE IS NOT DEGENERATE.** The table must contain
                      at least one `MUST REFUSE` row and at least one `MUST ADMIT` row whose
                      level is `calm` (the VALUE/calm row). A table of all-refusals would make
                      every arm below satisfiable by a contract that publishes nothing.

 CD-CALM-GATE-001     **THE GATE REFUSED, WHERE IT MUST REFUSE.** `refuse_unless_publishable`
                      raised `PublicationRefused` for a `calm` on an absent-data branch.

 CD-CALM-GATE-002     **THE GATE ADMITTED, WHERE IT MUST ADMIT.** It returned `None`. An
                      envelope this product must be able to publish is still publishable.

 CD-CALM-REASON-003   **AND IT REFUSED FOR THE RIGHT REASON, AT THE RIGHT PLACE.** The refusal
                      is `SCHEMA_VIOLATION` and its JSON pointer names the dial slot that was
                      mutated. *"The right outcome from the wrong layer"* is this project's
                      most-repeated defect (`CD-PL-F74`): an envelope refused because it was
                      malformed somewhere else would satisfy a weaker check while proving
                      nothing at all about `calm`.

 CD-CALM-PAIRED-004   **AND THE REFUSAL IS CAUSED BY THE LEVEL AND BY NOTHING ELSE.** For every
                      refusing row the instrument diffs the refused candidate against the
                      ADMITTED candidate of the same state at the same slot on the same
                      surface, and asserts they differ at EXACTLY ONE JSON pointer, which is
                      `/<slot>/detail_level`. Same document, one token moved, opposite outcome.
                      This is what makes CD-CALM-GATE-001 a measurement rather than a hope.

 CD-CALM-BRANCHES-006 **AND THE UNION'S BRANCH SET IS ENUMERATED AND CLOSED — DENY BY DEFAULT.**
                      *** NEW AT `16B-FIX`, AND IT IS THE ONE THAT MATTERS (`FX1`, closing
                      `CD-ASR-WO3-05` F1). *** Every branch of `#/$defs/dial_reading.oneOf` is
                      resolved and driven from its OWN `required` + `properties`; and, separately,
                      the branch SET must be exactly one branch per declared dial state, with the
                      contract's declared state set exactly this file's `DECLARED_STATES`. **A
                      branch nobody anticipated is a VIOLATION FOR BEING UNRECOGNISED rather than
                      a silence** — the `RULE F` shape `check_no_numeric_default` already
                      established on this project.
                      **WHY: MEASURED, NOT ARGUED.** The superseded implementation wrote out the
                      field list of each branch BY HAND and never looked at the union at all. A
                      FOURTH branch — the `UNKNOWN` branch copied, its `detail_level` repointed at
                      the full vocabulary, selected by a marker property, **adding no new ROOT key
                      so `check_schema_closed`'s allowlist never fires** — gave a tree on which
                      `refuse_unless_publishable` ADMITTED an `UNKNOWN` dial rendering as `calm` on
                      BOTH surfaces while **all thirty of the register's `execute:` lines exited
                      byte-identically to the clean tree.** That tree is arm `C6`.
                      A branch is recognised by its own `properties.state.const`, **never by the
                      name of the `$def` it lives in**, so the pure-rename refactor this instrument
                      already survives keeps passing.
                      *** AND SINCE `16B-FIX-3` THE BRANCH IS RESOLVED WITHOUT LOSING HALF OF IT
                      (`FX9`, closing `CD-ASR-WO3-07` F1). *** Both contracts declare JSON Schema
                      2020-12, in which a keyword SIBLING to `$ref` IS APPLIED. The resolver threw
                      those siblings away at every hop, so an `if`/`else` written on the `oneOf`
                      ENTRY — or one hop deeper — never reached the conditional guard: arms `C18`
                      and `C19`, on which the gate ADMITTED a calm `UNKNOWN` dial on both surfaces
                      while this instrument reported `PASS — 144 assertions, 0 violations`. **A
                      BRANCH COMPOSED ACROSS A `$ref` BOUNDARY IS NOW `CD-CALM-BRANCHES-006`, AT
                      EVERY HOP.** See `DECLARED LIMIT 13`.

 CD-CALM-SLOTS-007    **AND THE SLOT SET FAILS CLOSED (`FX3`, closing `CD-ASR-WO3-05` F3).** What
                      is DRIVEN is every root property spelled exactly
                      `{"$ref": "#/$defs/dial_reading"}`. What is ENUMERATED FOR COMPARISON is
                      every root property that DECLARES a dial `state`. **If those two sets
                      differ, or a root property's shape cannot be decided at all, this check
                      FAILS** — because a dial slot it cannot drive is a slot on which PID §3.2
                      is unguarded, and the superseded `DECLARED LIMIT 4` claimed the opposite.
                      Arm `C9`. *** IT FAILS CLOSED RATHER THAN WIDENING ITSELF: two dials, never
                      blended, is standing product (`PO-DECISIONS-0026`), so a third dial slot is
                      a PRODUCT decision and not this instrument's to absorb. ***
                      *** AND SINCE `16B-FIX-2` (`FX6`, closing `CD-ASR-WO3-06` F2) DECLARING THE
                      `state` IS ENOUGH TO STOP IT. *** It previously required the state's
                      `const`/`enum` to INTERSECT `DECLARED_STATES` and fell through to "not a
                      dial" otherwise, so a new quantity carrying a NEW state vocabulary was
                      SILENT: arms `C13` (`credit_stress`, `NO_DATA`) and `C14` (`feed_liveness`,
                      `["LIVE","STALE"]` — `PO-DECISIONS-0026` ruling 5's liveness quantity) both
                      had the gate ADMIT `calm` on both surfaces at `PASS — 144 assertions`.
                      An unclassifiable state vocabulary is now **UNDECIDABLE**, which is the
                      case `DECLARED LIMIT 8` says must stop the check. **This says nothing about
                      a dial that declares no property named `state`** — see this row's
                      `DECLARED LIMIT 12`.
                      *** AND SINCE `16B-FIX-3` DECLARING IT IS ENOUGH WHATEVER ITS SHAPE (`FX10`,
                      closing `CD-ASR-WO3-07` F2). *** `FX6` put the `undecidable` limb inside
                      `if isinstance(state, dict)`, so a `state` spelled as the boolean schema
                      `true` — legal in 2020-12 — was skipped and the property was classified NOT A
                      DIAL: arm `C20`, instrument `PASS — 144`, gate ADMITTING `{state: STALE,
                      detail_level: 'calm'}` on both surfaces. **A ROOT PROPERTY THAT DECLARES A
                      `state` REACHES THE UNDECIDABLE LIMB WHATEVER THE SHAPE OF THAT KEY'S
                      SUBSCHEMA.**

 CD-CALM-PRODUCER-005 **AND THE PRODUCT CANNOT EVEN FORM THE INTENT.** `DetailPolicy` refuses
                      construction with `absent_data_level="calm"` (`DetailPolicyIncoherent`),
                      admits `elevated` and `acute`, and `detail_level_for` returns the policy's
                      absent level — never `calm` — for an `Unknown` reading. The contract half
                      above is what the gate refuses to ACCEPT; this half is what the product
                      refuses to PRODUCE. Both arms, refusing and admitting.

===========================================================================================
DECLARED LIMITS — CD-RULE-004, IN THE FIRST SCREEN, AND SAID THE SAME WAY IN THE REGISTER
ENTRY (`required-tests.yaml`) AND IN THE EXECUTION CONTRACT
(`contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md`). A REGISTER ENTRY MAY NOT CLAIM
MORE THAN ITS GUARD DELIVERS.
===========================================================================================

 1  **IT JUDGES THE CONTRACT THE GATE ACTUALLY LOADS, WHICH IS CONFIGURABLE.**
    `envelope_contract.contracts_dir()` honours `$CD_CONTRACTS_DIR`, so the live gate can be
    pointed at contracts that are not the repository's while the repository's are intact.
    **THIS IS A REAL ROUTE AND IT IS THE ONE THIS INSTRUMENT'S C5 ARM DEMONSTRATES.**
    EXECUTABLE EXAMPLE:
      mkdir /tmp/widened && cp contracts/*.json /tmp/widened/
      python3 - <<'X'  # widen the UNKNOWN branch in /tmp/widened only
      import json;p='/tmp/widened/public_envelope.schema.json';d=json.load(open(p))
      d['$defs']['dial_reading_unknown']['properties']['detail_level']={'$ref':'#/$defs/detail_level'}
      json.dump(d,open(p,'w'))
      X
      CD_CONTRACTS_DIR=/tmp/widened python3 -c "..."   # the gate ADMITS a calm UNKNOWN dial
    **WHAT THIS CHECK DOES ABOUT IT:** it refuses (exit 3) unless the contracts the gate
    resolves are `<root>/contracts`, and it PRINTS the resolved paths and their SHA-256 at
    every run (`CD-PL-F98` — read the tree line every time; a contrast run against the wrong
    tree is indistinguishable from a fix that does nothing). **IT DOES NOT PREVENT THE ROUTE.**
    A deployment that sets `$CD_CONTRACTS_DIR` to a widened copy is refused by NOTHING in this
    repository, and that is **NOT PROVED TO BE CARRIED ANYWHERE.**
 2  **IT PROVES NOTHING ABOUT A `VALUE` READING THAT SHOULD NOT HAVE BEEN A `VALUE`.** The
    whole subject here is a dial that DECLARES its data absent. A dial whose inputs were
    missing but which was constructed as `VALUE` with a fabricated `score` renders `calm`
    legitimately as far as this contract is concerned, and this check admits it — row
    `VALUE/calm` above says so out loud. THE CARRIER IS THE SIBLING ENTRY: that class is
    `CD-RT-001-AST-NO-NUMERIC-DEFAULT` (provenance of the magnitude) together with
    `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` (the runtime post-condition
    `refuse_a_number_without_its_inputs`). **THIS CHECK IS ONE OF THREE GUARDS ON CD-AC-001
    AND NEVER A SOLE GUARD.**
 3  **IT SAYS NOTHING ABOUT STALENESS.** `CD-AC-001`'s words are *"missing OR STALE"*. This
    instrument drives the ABSENCE half only. Nothing here reads `staleness_window_seconds`,
    `as_of_utc` age, or any liveness/relevance quantity. The stale half is `CD-AC-009`
    (`CD-RT-009-REGIME-AWARE-STALENESS`) and, as a product model, is `PO-DECISIONS-0026`
    ruling 5, which is a LATER increment and is not evidenced here.
 4  **IT IS NOT A CENSUS OF SURFACES, AND IT DRIVES ONE EXACT SPELLING OF A DIAL SLOT.**
    *** SUPERSEDED AT `16B-FIX`, STATED AND NOT ERASED (`CD-RULE-004`, `PBG-CONT-003`). ***

      WHAT THIS LIMIT SAID, VERBATIM: *"It drives the two envelope surfaces that
      `EnvelopeSurface` declares, at the two dial slots the contracts declare, ENUMERATED FROM
      THE APPLICATION ... rather than typed in — so a third surface or a third dial added
      tomorrow is driven on the day it is added."*

      **THAT SENTENCE WAS FALSE, AND IT WAS FALSE IN ALL THREE PLACES `CD-RULE-004` REQUIRES IT
      TO BE SAID** (here, the `required-tests.yaml` comment, and the execution contract).
      MEASURED by `CD-ASR-WO3-05` (F3) and reproduced here as arm `C9`: the slot enumerator
      requires `sub.get("$ref") == "#/$defs/dial_reading"` **exactly**, so an OPTIONAL third dial
      slot spelled with any other `$ref` — which is precisely how a dial is added without
      breaking existing consumers — was invisible. The superseded instrument reported
      `PASS — 67 assertions, 0 violations` on that tree while the live gate ADMITTED `calm` on
      the new slot, on both surfaces.

      **WHAT WAS SAID INSTEAD AT `16B-FIX`, VERBATIM — AND IT IS ALSO SUPERSEDED, AT
      `16B-FIX-2`, FOR BEING FALSE IN EXACTLY THE WAY THE SENTENCE IT REPLACED WAS FALSE:**
      *"`CD-CALM-SLOTS-007` enumerates every root property that constrains a dial `state` under
      any spelling and FAILS the check if that set is not exactly the driven set, or if any root
      property's shape cannot be decided at all."*

      **THAT SENTENCE WAS ALSO FALSE, IN THE SAME THREE PLACES.** MEASURED by `CD-ASR-WO3-06`
      (F2) and reproduced here as arms `C13` and `C14`: `_dial_bearing` asked whether a root
      property's `state` `const`/`enum` INTERSECTED `DECLARED_STATES` and, where it did not,
      returned **`False` — not undecidable.** An optional root property `credit_stress` whose
      state is `{"const": "NO_DATA"}` (`C13`) **constrains a dial `state`**, its shape **is**
      decidable, it was **not** in the driven set — **and the check did not fail.** The live gate
      ADMITTED it rendering as `calm` on BOTH surfaces while this instrument reported
      `PASS — 144 assertions, 0 violations`. The identical property with the state spelled
      `["UNKNOWN","STALE"]` **was** caught. **THE ONLY DIFFERENCE BETWEEN A CAUGHT TREE AND AN
      UNCAUGHT ONE WAS WHETHER THE NEW DIAL REUSED AN OLD STATE NAME**, which is
      `GUARD_THE_INSTANCE_NOT_THE_CLASS` (`PO-DECISIONS-0026` ruling 10). `C14` is the same shape
      carrying ruling 5's LIVENESS quantity — optional root `feed_liveness`, states
      `["LIVE","STALE"]` — and `CD-AC-001`'s own words are *"missing **OR STALE** input never
      renders as calm"*.

      **WHAT IS TRUE INSTEAD, WRITTEN AFTER `FX6` WAS MEASURED AND DESCRIBING WHAT WAS MEASURED.**
      What is DRIVEN is every top-level property whose value is literally
      `{"$ref": "#/$defs/dial_reading"}`, on every surface `EnvelopeSurface` declares. A dial slot
      spelled any other way is **NOT DRIVEN**. Since `16B-FIX-2` it is **NOT SILENT PROVIDED IT
      DECLARES A `state` PROPERTY**, and that proviso is the whole of the honest claim:
      `_dial_bearing` walks a root property through a DECLARED keyword set to a DECLARED depth,
      and

        * a resolved subschema declaring a `state` whose `const`/`enum` INTERSECTS
          `DECLARED_STATES` is **dial-bearing** — driven, or `CD-CALM-SLOTS-007` fails;
        * a resolved subschema declaring a `state` whose vocabulary does **not** intersect is
          **UNDECIDABLE** — reported by `CD-CALM-SLOTS-007`'s `undecidable` limb, in the words
          *"a construct this check cannot decide about"*, because *"I cannot classify this state
          vocabulary"* is precisely the case `DECLARED LIMIT 8` says must STOP the check;
        * a `$ref` that does not resolve, a keyword outside the declared set, or a nesting deeper
          than the walk is **UNDECIDABLE** and reported the same way.

      **AND WHAT IS STILL SILENT, SAID PLAINLY RATHER THAN LEFT TO BE MEASURED BY THE NEXT
      AUDITOR: a root property that carries a dial WITHOUT DECLARING A PROPERTY NAMED `state`** —
      one that discriminates on a differently-named key — is classified `False` and says nothing.
      **THIS LIMIT NO LONGER CLAIMS "UNDER ANY SPELLING".** It claims: *declared `state`, under
      any spelling of that state's vocabulary, within a declared keyword set and depth.* See this
      row's `DECLARED LIMIT 12`.

      So a third dial that declares a `state` is **REPORTED** on the day it is added, and driven
      on the day someone spells the slot the one way this instrument drives. **REPORTED IS NOT
      DRIVEN AND THIS LIMIT STILL DOES NOT PRETEND OTHERWISE.**

      A third SURFACE genuinely is driven on the day it is added, because the surfaces come from
      `EnvelopeSurface` itself; that half of the original sentence was true and is retained.

    And a rendering path that does not go through `refuse_unless_publishable` at all is outside
    this check entirely. MEASURED at this commit: the only callers of
    `refuse_unless_publishable` in `src/` are `publication/publish.py` lines 276-277, and they
    call it on BOTH surfaces before any write. A future serving layer that renders a dial
    without publishing an envelope is **NOT PROVED TO BE CARRIED ANYWHERE** — the rendering
    layer is later WO work.
 5  **IT IMPORTS THE SUBJECT TREE AND THEREFORE INHERITS IT.** It is a runtime check because
    *"refused"* is a runtime claim and every escape on this project's record passed a static
    checker. The cost is `--root`'s honesty: it prints the resolved `crash_detector.__file__`
    it imported and the SHA-256 of both contracts it judged.
 6  **IT NEEDS `jsonschema`**, because the gate does. Unlike the stdlib-only static checks in
    this directory it cannot run in an environment where the application's own runtime
    dependencies are absent. If `jsonschema` is missing it exits 3 with the reason — never a
    pass and never a skip (`PBG-CI-002`). **SINCE `16B-FIX` IT ALSO USES `jsonschema` DIRECTLY**,
    to decide which synthetic value a branch's own property subschema accepts, so the dependency
    is now load-bearing twice over and is imported explicitly with its own exit-3 reason.
 7  **THE ENVELOPE ROOT IS STILL A DOCUMENT SHAPE WRITTEN OUT IN THIS FILE.** *** NEW AT
    `16B-FIX`, AND DECLARED BECAUSE THE FIX DOES NOT REACH IT. *** `FX1` replaced the hand-written
    DIAL shapes with shapes derived from each `oneOf` branch. `_envelope`'s ROOT skeleton —
    `schema_version`, `as_of_utc`, `regime`, `staleness_window_seconds` and the rest — is still
    typed in. **IT IS FAIL-CLOSED RATHER THAN FAIL-SILENT, WHICH IS WHY IT IS A LIMIT AND NOT A
    HOLE:** a required root property this skeleton does not carry makes EVERY candidate refused,
    so every `MUST ADMIT` row fails as `CD-CALM-GATE-002` and the check exits 1. The dial
    branches were the SILENT case — a candidate that is still valid, still admitted, and simply
    never built — and those are the ones now derived. An OPTIONAL root property that is
    dial-bearing is `CD-CALM-SLOTS-007`'s. **NOT PROVED TO BE CARRIED ANYWHERE:** an optional
    root property that is not dial-bearing and changes what a renderer does.
 8  **THE DIAL STATE VOCABULARY IS TYPED IN, DELIBERATELY, AND IT IS THE ONE AXIS THAT DOES NOT
    GROW ON ITS OWN.** *** NEW AT `16B-FIX`. *** Surfaces, dial slots, `oneOf` branches and
    detail LEVELS are all enumerated from the subject. `DECLARED_STATES` is not: a fourth dial
    STATE added to a contract makes `CD-CALM-BRANCHES-006` FAIL until someone edits this file.
    **THAT IS THE INTENDED COST AND NOT AN OVERSIGHT.** A new LEVEL is classified by a rule
    already written here in one line — it is `calm`, or it is not. A new STATE cannot be
    classified without knowing whether it MEANS the data is absent, which is product meaning and
    not an Engineer's to decide (`PBG-AUTH-005`); and the failure is asymmetric — guess "present
    data" and `calm` is silently admitted on a missing-data state, which is the constitutional
    breach itself. So it stops and says the state is unrecognised. **THE COST IS PRICED: a PID §4
    amendment adding a fourth LEVEL still passes untouched (arm `C10`, measured); a fourth STATE
    is a red instrument until a human looks.**
 9  **A BRANCH THIS CHECK CANNOT BUILD IS REPORTED, NOT DRIVEN.** *** NEW AT `16B-FIX`. *** Each
    required property of a branch is filled with the first of a CLOSED, declared list of
    synthetic values that the property's own subschema accepts, decided by `jsonschema` and never
    by the property's NAME. A property none of them satisfies — one needing a `pattern` no
    declared value matches, say — makes the check report `CD-CALM-BRANCHES-006` and exit 1. **It
    is deny-by-default, so it is not an escape; it IS a maintenance cost**, and a contract that
    adds such a property to a dial branch turns this instrument red until the declared list
    grows. Reporting is the correct failure direction: an unbuildable branch is an undriven
    branch, and an undriven branch of the published union is a shape on which PID §3.2 is
    unguarded.
 10 **A BRANCH WHOSE SHAPE IS CONDITIONAL IS REPORTED, NOT DRIVEN — DENY BY DEFAULT.** *** NEW AT
    `16B-FIX-2` (`FX5`, closing `CD-ASR-WO3-06` F1). *** This check builds **exactly one document
    per branch**, out of that branch's own `required` + `properties`. A branch that ALSO carries
    any of `CONDITIONAL_KEYWORDS` — `if`/`then`/`else`, `allOf`, `anyOf`, `oneOf`, `not`,
    `dependentSchemas`, `dependentRequired`, `unevaluatedProperties` — admits MORE shapes than
    that one document, and the shapes it never builds are exactly where a `calm` variant can
    hide. **MEASURED, arm `C11`:** `dial_reading_unknown` keeps its name, its `state.const`, its
    `required` list and `additionalProperties: false`; its `detail_level` is widened; the
    narrowing is relocated into `"if": {"required": ["render_hint"]}` with an `"else"` carrying a
    fully closed copy. A dial WITHOUT the marker is REFUSED; a dial WITH it is **ADMITTED on both
    surfaces**; and the superseded instrument reported `PASS — 144 assertions, 0 violations` while
    **exactly one** of the register's thirty `execute:` lines moved — `tests/test_detail_level.py`,
    the memorial `PO-DECISIONS-0026` ruling 9 said the guarantee must not be left in.
    **SUCH A BRANCH IS NOW `CD-CALM-BRANCHES-006`**, on `DECLARED LIMIT 9`'s own sentence: *a
    branch whose shape is conditional is a branch this check cannot say it has driven.*
    **THE COST, PRICED:** this check does **not** enumerate conditional shapes — one candidate per
    satisfiable combination of optional markers is a schema-instance generator and a design
    question this row does not price (RULED by `PROJECT_LEAD_SEAT_02`; the auditor correctly
    refused to decide it). So a **legitimate** conditional dial branch, if one is ever wanted,
    turns this instrument red until that increment prices it. **IT COSTS NOTHING TODAY:**
    MEASURED, the clean tree's six branches (three per surface) declare only
    `type`/`additionalProperties`/`required`/`properties`/`description`, and the clean run is
    unchanged at `PASS — 144 assertions, 0 violations`.

    *** ITS CLOSING SENTENCE WAS FALSE FOR A CONDITIONAL WRITTEN ONE POSITION OVER. SUPERSEDED AT
    `16B-FIX-3`, STATED AND NOT ERASED (`CD-RULE-004`, `PBG-CONT-003`). ***

      WHAT THIS LIMIT SAID, VERBATIM: *"A branch that ALSO carries any of `CONDITIONAL_KEYWORDS`
      ... **SUCH A BRANCH IS NOW `CD-CALM-BRANCHES-006`**."*

      **THAT SENTENCE WAS FALSE, AND IT WAS FALSE IN ALL THREE PLACES `CD-RULE-004` REQUIRES IT TO
      BE SAID.** MEASURED by `CD-ASR-WO3-07` (F1) and reproduced here as arms `C18` and `C19`. The
      guard tested the RESOLVED branch, and the resolver discarded every keyword sitting beside the
      `$ref` it followed. So the SAME `if`/`else` — written as a SIBLING of the `$ref` on the
      `oneOf` ENTRY (`C18`) or one hop deeper behind an innocuous entry (`C19`) instead of INSIDE
      the branch definition — never reached the guard at all. On both trees the live gate ADMITTED
      an `UNKNOWN` dial rendering as `calm` on BOTH surfaces while this instrument reported
      `PASS — 144 assertions, 0 violations` and **exactly one** of the register's thirty `execute:`
      lines moved: `tests/test_detail_level.py`, the memorial. On `C19` the instrument even printed
      the branch in its enumerated list, named and state-classified, and still reported clean.

      **WHAT IS TRUE INSTEAD, WRITTEN AFTER `FX9` WAS MEASURED.** The keyword guard below is
      UNCHANGED; **the RESOLVER was repaired**, so the branch handed to the guard is either the
      whole branch or nothing. A `$ref` chain that would have discarded an asserting keyword is
      reported instead of followed — at **every hop**, not only at the `oneOf` entry, which is what
      arm `C19` exists to bound. `C18` and `C19` are now `FAIL — 32 violation(s)` each, 20 ×
      `CD-CALM-BRANCHES-006` + 12 × `CD-CALM-PAIRED-004`, the same census `C11` produces for the
      same shape written inside the branch. The cost of that resolver change is its own limit —
      **see `DECLARED LIMIT 13`.**
 11 **THE FILLER DIAL IS THE FIRST ABSENT-DATA BRANCH THAT ACTUALLY BUILDS, AND `LIMIT 9`'S OWN
    SENTENCE WAS FALSE UNTIL IT WAS.** *** NEW AT `16B-FIX-2`, and it corrects a measurement
    `CD-ASR-WO3-06` F3 recorded against `16B-FIX` (`CD-RULE-004`, `PBG-CONT-003` — stated, not
    erased). *** `DECLARED LIMIT 9` says an unbuildable property *"makes the check report
    `CD-CALM-BRANCHES-006` and exit 1"*. **AT `16B-FIX` THAT WAS FALSE:** the filler dial was
    built from the first absent-data branch FOUND, so an unbuildable `UNKNOWN` branch exited **3**
    as `PRECONDITION_NOT_MET`, upstream of the matrix, with **no violation code at all** — the
    branch was refused-about rather than reported. Both outcomes are non-zero and both state a
    reason, so nothing escaped; **but the limit described an observable the code did not
    produce.** The filler is now the first absent-data branch that BUILDS, so the unbuildable one
    is REPORTED as `CD-CALM-BRANCHES-006` at exit 1 and `LIMIT 9` says what happens. **MEASURED,
    arm `C17`:** the `UNKNOWN` branch gains a required nested object with its own `required`
    member — `16B-FIX` gave exit 3 and no code; `16B-FIX-2` gives `FAIL — 32 violation(s)`, 20 ×
    `CD-CALM-BRANCHES-006` + 12 × `CD-CALM-PAIRED-004`. **WHAT IT COSTS:** if EVERY absent-data
    branch is unbuildable the check still exits 3, naming each branch and its obstacle — there is
    then no admissible dial to fill the other slots with and nothing to measure.
 12 **A DIAL THAT DOES NOT DECLARE A PROPERTY NAMED `state` IS STILL SILENT.** *** NEW AT
    `16B-FIX-2` (`FX6`, closing `CD-ASR-WO3-06` F2), AND IT IS THE RESIDUE OF THAT FIX RATHER
    THAN A HOLE THE FIX OPENED. *** `_dial_bearing` now stops — `None`, UNDECIDABLE, reported by
    `CD-CALM-SLOTS-007` — on a resolved subschema that DECLARES a `state` whose `const`/`enum`
    does not intersect `DECLARED_STATES`, which is what makes arms `C13` and `C14` red. **THE
    LOOSER, LOUDER FORM WAS RULED** over the tighter one (require both a `state` and a
    `detail_level`): a false positive costs one seat one look at one contract; a false negative
    costs the constitution. **WHAT IS STILL SILENT:** a root
    property carrying a dial that discriminates on a differently-NAMED key — `status`, `kind`,
    `reading_state` — is classified `False` and reported by nothing here. This check keys on the
    property NAME `state` and on nothing else, and widening that to "any discriminator" is not an
    Engineer's judgement to make (`PBG-AUTH-005`). **NOT PROVED TO BE CARRIED ANYWHERE.**
    *** THAT RESIDUE STANDS AND WAS TESTED RATHER THAN TAKEN ON TRUST: `CD-ASR-WO3-07` (F3) built
    the tree — the same dial with the key spelled `liveness` passes, spelled `state` fails, spelled
    `state` through a `$ref` fails — and judged the limit HONESTLY DRAWN. It is a condition on
    16C's dispatch and it is not closed here. ***

    *** SUPERSEDED AT `16B-FIX-3` ON TWO COUNTS, STATED AND NOT ERASED (`CD-RULE-004`,
    `PBG-CONT-003`). THE BEHAVIOUR IS UNCHANGED ON THE SECOND COUNT — WHAT IS CORRECTED IS THE
    SENTENCE. ***

      (a) **ITS POSITIVE CLAIM WAS FALSE FOR A `state` THAT IS NOT AN OBJECT.** WHAT THE HEADER
      SAID, VERBATIM: *"a resolved subschema declaring a `state` whose `const`/`enum` does not
      intersect `DECLARED_STATES` is UNDECIDABLE, and reported."* MEASURED by `CD-ASR-WO3-07` (F2)
      and reproduced as arm `C20`: `FX6` put the `undecidable = True` limb INSIDE
      `if isinstance(state, dict)`, so a `state` spelled as the boolean schema `true` — legal in
      2020-12 and maximally permissive — dropped to `None`, the limb never ran, the descent skipped
      it, and the property was classified **not a dial**. The instrument reported
      `PASS — 144 assertions, 0 violations` with the property in NEITHER list while the live gate
      ADMITTED `{state: STALE, reason: FEED_DEAD, detail_level: 'calm'}` and
      `{state: NO_DATA, ..., detail_level: 'calm'}` on BOTH surfaces. **`DECLARED LIMIT 12` DID NOT
      COVER IT** — this limit is about a differently-NAMED discriminator, and that dial's key is
      literally called `state`. **WHAT IS TRUE INSTEAD (`FX10`): DECLARING the key `state` is the
      whole trigger. A root property that declares it reaches the undecidable limb WHATEVER the
      shape of that key's subschema — object, boolean, or anything else — and the shape can only
      refine the answer to `True`, never back to `False`.**

      (b) **ITS "MEASURED" SENTENCE PRESENTED ONE SHAPE AS A CLASS.** WHAT IT SAID, VERBATIM:
      *"**MEASURED**, it does not fire on the clean tree (`PASS — 144 assertions, 0 violations`,
      byte-identical register), **nor on a legitimate optional root object that is not a dial**
      (arm `C16`, `PASS — 144`)."* **THE SECOND HALF WAS NOT A MEASUREMENT OF A CLASS.** `C16` is
      ONE benign shape — an object with no `state` anywhere — and the sentence generalised it into
      a claim about every legitimate optional root object. `CD-ASR-WO3-07` (F4) measured two
      members of that class that DO fire: **`jurisdiction.state` — A US STATE CODE — IS THE WORKED
      EXAMPLE.** A root `jurisdiction` object carrying `country` and a two-letter `state` turns
      this constitutional instrument RED (`FAIL — 2 violation(s)`, `CD-CALM-SLOTS-007`'s
      undecidable limb, `['jurisdiction']`), and so does a root `run_provenance` whose nested
      `pipeline` declares `state: {enum: [QUEUED, RUNNING, FINISHED]}` (`FAIL — 2`,
      `['run_provenance']`). **NEITHER HAS ANY BEARING ON WHETHER MISSING DATA RENDERS AS CALM.**

      **THE BEHAVIOUR IS NOT CHANGED AND THE RULING STANDS.** `PROJECT_LEAD_SEAT_02` ruled the
      LOUD form correct — a false positive costs one seat one look at one contract; a false
      negative costs the constitution — and `CD-ASR-WO3-07` recorded that it does not contest that
      ruling. **WHAT IS TRUE INSTEAD:** this check fires on **any** root property that declares a
      property named `state`, whatever that property MEANS and whatever its subschema's shape.
      MEASURED, it does not fire on the clean tree (`PASS — 144 assertions, 0 violations`) or on
      arm `C16` — **TWO SHAPES, AND THAT IS TWO MEASUREMENTS AND NOT A CLASS.** A reader who meets
      a red instrument on a US state code has met this limit working as ruled, not a defect: the
      remedy is to rename the key or to bring the contract addition to the Product Authority, and
      never to loosen the guard.

 13 **A `$ref` CARRYING AN ASSERTING SIBLING IS REPORTED, NOT FOLLOWED — DENY BY DEFAULT AT THE
    RESOLVER.** *** NEW AT `16B-FIX-3` (`FX9`, closing `CD-ASR-WO3-07` F1). *** Both contracts
    declare `"$schema": "https://json-schema.org/draft/2020-12/schema"`, and **in 2020-12 keywords
    SIBLING to `$ref` ARE APPLIED** — the one thing draft-07 did differently. `_resolve` now
    reports, at **every hop of the chain**, any key beside a `$ref` that is not one of the pure
    annotations in `REF_INERT_SIBLINGS` (`$comment`, `title`, `description`, `default`,
    `deprecated`, `readOnly`, `writeOnly`, `examples`). A branch reached through such a chain is
    `CD-CALM-BRANCHES-006`; a root property reached through one is UNDECIDABLE and
    `CD-CALM-SLOTS-007`; the union itself is `CD-CALM-BRANCHES-006`.
    **THE REMEDY CHOSEN, AND WHY, BECAUSE TWO WERE OFFERED.** The alternative was to make `_deref`
    return the target MERGED with its siblings. **A DICT MERGE IS NOT 2020-12's SEMANTICS.**
    `$ref` + siblings is a CONJUNCTION of two schema objects, and `additionalProperties`,
    `unevaluatedProperties` and `unevaluatedItems` are evaluated against the annotations of *their
    own* schema object: a target `{"properties": {"a": ...}}` conjoined with a sibling
    `{"additionalProperties": false}` admits nothing but `{}`, while the MERGED object admits
    `{"a": ...}`. **A merge can therefore admit documents neither schema admits — it can only ever
    WEAKEN this instrument, silently, which is the exact failure class F1 is.** Deny-by-default
    cannot weaken it; it can only over-report. **THE COST, PRICED:** a contract that legitimately
    narrows a `$ref` with a sibling keyword turns this instrument red until an increment prices
    composition properly. **IT COSTS NOTHING TODAY, AND THAT IS MEASURED RATHER THAN ASSUMED:** the
    public contract carries FOUR `$ref` nodes with a `description` sibling (`as_of_utc`,
    `published_utc`, `inputs_used`, `degraded_inputs`) and the private contract none, so the inert
    list is load-bearing — a resolver that denied on ANY sibling would turn the CLEAN TREE red. The
    clean run is unchanged at `PASS — 144 assertions, 0 violations`, `C10`/`C15`/`C21` are
    unchanged at `PASS — 158`, and no arm of `C1`–`C17` changed its census.
    **WHAT IS STILL NOT COVERED:** `_synthesise` still resolves a property's subschema through
    `_deref` to harvest `const`/`enum` candidates, and does NOT deny there — deliberately, because
    the candidate it picks is then validated by `jsonschema` against the **unresolved** subschema,
    which applies `$ref` siblings correctly, so the authority on that decision is the same library
    the gate validates with and not this resolver. **AND THE CLASS IS NOT BOUNDED:** `C18` and
    `C19` are two members of a class whose size nobody has measured — `CD-ASR-WO3-07` said so of
    its own finding and it is repeated here rather than quietly dropped. **NOT PROVED TO BE CARRIED
    ANYWHERE:** nothing outside this instrument reads `$ref` siblings at all.

*** NUMBERING, BECAUSE `CD-ASR-WO3-06` COULD NOT VERIFY IT AND SAID SO. *** **DECLARED LIMIT
NUMBERS ARE PER REGISTER ROW, NOT PER FILE.** These are the limits of
`CD-RT-001-MISSING-DATA-NEVER-CALM` and they run **1–13** (**1–12 until `16B-FIX-3`, which added
`13`**), said identically in this header, in
`required-tests.yaml`, and in `contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md`
(`CD-RULE-004`, three places). The SIBLING row `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` has its OWN
independent 1–12 sequence, spread across
`tools/register/check_judgement_path_doors.py` (1–4, 7–9), `src/crash_detector/admission.py`
(5–6) and `required-tests.yaml` (10–12). **BOTH ROWS LIVE IN `required-tests.yaml`, SO A BARE
"DECLARED LIMIT 12" IS AMBIGUOUS THERE AND ALWAYS WAS.** Quote the row id with the number.

EXIT: 0 clean · 1 violation, with the cell and the observed outcome · 2 usage ·
3 precondition not met. Never a skip, for any reason (`PBG-CI-002`).
"""

from __future__ import annotations

import hashlib
import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, resolve_root  # noqa: E402

CHECK_ID = "CD-RT-001-MISSING-DATA-NEVER-CALM"

MUST_REFUSE = "MUST REFUSE"
MUST_ADMIT = "MUST ADMIT"

#: The prohibited level. PID §3.2, verbatim: "Missing data must never render as calm."
CALM = "calm"

#: The two absent-data states. UNKNOWN declares no score at all; DEGRADED carries a value AND
#: its damage with at least one named missing input. Those are exactly the missing-data states,
#: and they are exactly the two branches 16A-FIX narrowed.
ABSENT_STATES = ("UNKNOWN", "DEGRADED")

#: The states in which the data is PRESENT, so `calm` is a legitimate rendering and MUST be
#: admitted. This is the vacuity arm's state.
PRESENT_STATES = ("VALUE",)

#: *** DENY BY DEFAULT, AND THIS IS THE STRUCTURAL HALF OF THE `F1` FIX (RULE F). *** Every dial
#: state this instrument knows how to CLASSIFY. `CD-CALM-BRANCHES-006` asserts that the contract's
#: own declared state set is exactly this, and that the union's branches cover it exactly once each
#: — so a branch nobody anticipated is a VIOLATION FOR BEING UNRECOGNISED rather than a silence.
#:
#: *** WHY THIS LIST IS TYPED IN WHILE THE LEVEL VOCABULARY IS READ FROM THE CONTRACT, WHICH IS A
#: DELIBERATE ASYMMETRY AND NOT AN OVERSIGHT. *** A new LEVEL is classified by a rule this file
#: already states in one line — it is `calm`, or it is not — so the table grows on the day the
#: vocabulary does. A new STATE cannot be classified without knowing whether it MEANS the data is
#: absent, and that is product meaning, which is not an Engineer's to decide (`PBG-AUTH-005`).
#: Guessing would be worse than stopping: guess "present" and a missing-data state silently gets
#: `calm` admitted. So the instrument stops and says the state is unrecognised. See DECLARED LIMIT 8.
DECLARED_STATES = PRESENT_STATES + ABSENT_STATES

#: *** DELIBERATELY UNMISTAKABLE, AND NOT AN INGREDIENT. *** `Q25` holds the ingredient set with
#: the Product Authority and `CD-PL-F154` is what happens when a fixture escapes. The VALUE
#: branch requires `inputs_used` with `minItems: 1`, so this string exists only to satisfy that
#: cardinality inside this process. Nothing in this file constructs a `SourceRecord`, imports
#: `crash_detector.source_registry`, or emits a statement naming `raw.source_registry`. A grep
#: for this token lands here and nowhere near a registry.
SYNTHETIC_INPUT_ID = "SYNTHETIC-REGISTER-CHECK-NOT-A-SOURCE"

SYNTHETIC_CONFIG_SNAPSHOT_ID = "SYNTHETIC-REGISTER-CHECK-NOT-A-CONFIG"

AS_OF_UTC = "2026-08-23T12:00:00Z"
PUBLISHED_UTC = "2026-08-23T12:00:05Z"

#: The same instant as :data:`AS_OF_UTC`, PARSED FROM IT rather than written out a second time,
#: so the wire string a dial document carries and the ``datetime`` the producer arm's reading
#: carries cannot drift apart.
NOW = datetime.strptime(AS_OF_UTC, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

#: SYNTHETIC AND MEANINGLESS AS A NUMBER. The dial has no ratified scale (`Q25` holds it). It is
#: below any plausible calm boundary ON PURPOSE: an implementation that read the magnitude and
#: ignored the state would call this DEGRADED reading `calm`, which is the exact prohibited
#: rendering. Nothing here declares a threshold or a scale.
SYNTHETIC_SCORE = 0.01


#: *** THE LEVEL KEY IS OMITTED ENTIRELY. *** Not a level, and deliberately not a string: this is
#: the FIELD-ABSENT row (`FX2`, closing `CD-ASR-WO3-05` F2). `tests/test_detail_level.py` has
#: asserted `_dial_with_level(builder, None) == REFUSED` since before this instrument existed, and
#: that row was dropped when the property moved into the register. A dial that carries NO
#: `detail_level` at all leaves the renderer to decide, which is the second decision site the whole
#: module exists to prevent.
LEVEL_ABSENT = "<<the detail_level key is not present>>"

#: The OFF-VOCABULARY row (`FX2`). It is `banana` and not something cleverer ON PURPOSE: that is the
#: exact token `tests/test_detail_level.py::_assert_missing_data_never_renders_as_calm` has always
#: used, and this instrument must not be weaker than the memorial it supersedes. If a contract ever
#: declares it as a real level this check REFUSES to run (exit 3) rather than asserting a row that
#: has quietly become false.
OFF_VOCABULARY_LEVEL = "banana"

#: The property that carries the level, on every branch of the union.
DETAIL_LEVEL = "detail_level"

#: A generic non-empty bounded string, for any required property whose schema wants one. It is
#: unmistakable for the same reason `SYNTHETIC_INPUT_ID` is: a grep for it lands here.
SYNTHETIC_TEXT = "SYNTHETIC-REGISTER-CHECK-NOT-A-VALUE"

#: *** THE DECLARED VALUE VOCABULARY, AND IT IS A CLOSED LIST ON PURPOSE (RULE F). *** A candidate
#: dial is built from the branch's OWN `required` + `properties`, and each property's value is the
#: FIRST of these that the property's own subschema ACCEPTS — decided by `jsonschema`, the same
#: library the gate validates with, and never by the property's NAME. A required property that none
#: of these satisfies is reported as UNRECOGNISED (`CD-CALM-BRANCHES-006`) rather than skipped, so a
#: branch this instrument cannot build is a VIOLATION and not a silence.
#: Order matters and is the only thing that is tuned: the plain string precedes the timestamp so a
#: free-text property gets text and a `pattern`-constrained one gets the timestamp.
SYNTHETIC_VALUES = (
    SYNTHETIC_TEXT,             # a bounded, non-empty, unpatterned string
    AS_OF_UTC,                  # a UTC timestamp string
    SYNTHETIC_SCORE,            # a number
    [SYNTHETIC_INPUT_ID],       # a non-empty array of id-shaped strings
    [],                         # an empty array
    {},                         # an empty object
    True,                       # a boolean
    None,                       # null
)


def _fragment(schema: dict, subschema: dict) -> dict:
    """``subschema`` as a standalone document, so its local ``#/$defs/...`` refs still resolve."""
    fragment = dict(subschema)
    fragment.setdefault("$schema", schema.get("$schema")
                        or "https://json-schema.org/draft/2020-12/schema")
    fragment.setdefault("$defs", schema.get("$defs") or {})
    return fragment


#: *** THE ONLY KEYS THAT MAY SIT BESIDE A `$ref` WITHOUT CHANGING WHAT THE NODE ADMITS. NEW AT
#: `16B-FIX-3` (`FX9`, closing `CD-ASR-WO3-07` F1). *** Both envelope contracts declare
#: `"$schema": "https://json-schema.org/draft/2020-12/schema"`, and **in 2020-12 keywords SIBLING to
#: `$ref` ARE APPLIED** — that is the one thing draft-07 did differently and the whole of F1. Every
#: key listed here is a pure ANNOTATION in that specification (Core `$comment`, and the Basic
#: Meta-Data vocabulary `title`/`description`/`default`/`deprecated`/`readOnly`/`writeOnly`/
#: `examples`): it produces an annotation and asserts NOTHING, so discarding it cannot change which
#: documents the node admits. **ANY OTHER KEY BESIDE A `$ref` IS AN ASSERTION THIS RESOLVER WOULD
#: THROW AWAY**, and :func:`_resolve` reports it instead. `description` is not decoration in this
#: list — MEASURED at this commit, the public contract carries FOUR `$ref` nodes with a
#: `description` sibling (`as_of_utc`, `published_utc`, `inputs_used`, `degraded_inputs`), so a
#: resolver that denied on ANY sibling would turn the CLEAN TREE red.
REF_INERT_SIBLINGS = frozenset({
    "$ref", "$comment", "title", "description",
    "default", "deprecated", "readOnly", "writeOnly", "examples",
})

#: How many `$ref` hops :func:`_resolve` will follow before it gives up. **REACHING IT IS
#: UNDECIDABLE AND NOT A RESULT** — see the comment at the cap itself (`FX12`).
REF_CHAIN_CAP = 32


def _resolve(schema: dict, node, depth: int = 0):
    """Follow a chain of LOCAL ``#/...`` refs, and **SAY WHAT THE CHAIN DISCARDED**.

    Returns ``(resolved, dropped)``. ``resolved`` is the mapping the chain names, or ``None`` if it
    is unresolvable — every caller treats ``None`` as UNRECOGNISED rather than as "nothing to see".
    ``dropped`` is a list of ``(hop, ref, [asserting sibling keys])``, one entry per hop of the
    chain whose node carried a key outside :data:`REF_INERT_SIBLINGS` beside its `$ref`.

    *** THIS IS THE FIX FOR `CD-ASR-WO3-07` F1 AND IT IS A RESOLVER FIX, NOT A GUARD FIX. *** The
    superseded `_deref` replaced a node carrying `$ref` with the `$ref`'s TARGET and threw the
    node's siblings away **at every hop, silently**. In JSON Schema 2020-12 those siblings ARE
    applied, so the resolved object this check inspected was NOT the schema the gate enforced. An
    `if`/`else` written as a sibling of the `$ref` on a `oneOf` ENTRY — instead of inside the branch
    definition — therefore never reached `FX5`'s conditional-keyword guard: the instrument reported
    `PASS — 144 assertions, 0 violations` while the live gate ADMITTED an `UNKNOWN` dial rendering
    as `calm` on BOTH surfaces (auditor arm `A1`), and putting the same conditional ONE `$ref`
    DEEPER behind an innocuous entry gave the identical result (`A2`). **A GUARD THAT LOOKED ONLY AT
    THE `oneOf` ENTRY WOULD STILL BE BLIND, WHICH IS WHY THE REPAIR IS HERE**: this walk reports
    every hop, so the caller's answer does not depend on WHERE the sibling was written.

    **WHY DENY-BY-DEFAULT AND NOT A MERGE — THE CHOICE IS DECLARED (`DECLARED LIMIT 13`).** The
    alternative was to return the target MERGED with its siblings. A dict merge is **not** 2020-12's
    semantics: `$ref` + siblings is a CONJUNCTION of two schema objects, and `additionalProperties`,
    `unevaluatedProperties` and `unevaluatedItems` are evaluated against the annotations of *their
    own* schema object. Target `{"properties": {"a": ...}}` conjoined with sibling
    `{"additionalProperties": false}` admits NOTHING but `{}`; the MERGED object admits `{"a": ...}`.
    **A merge can therefore admit documents neither schema admits — it can only ever WEAKEN this
    instrument, silently, which is the exact failure class F1 is.** Reporting cannot weaken it: it
    can only over-report, and an over-report costs one seat one look at one contract.
    """
    dropped: list = []
    while isinstance(node, dict) and "$ref" in node:
        # *** THE CAP RETURNS `None`, NEVER THE NODE IT DID NOT RESOLVE. NEW AT `16B-FIX-4`
        # (`FX12`, closing `CD-ASR-WO3-08` F5 and one member of F1). *** The superseded loop
        # carried `depth < 32` in the `while` condition, so a chain longer than the cap fell out
        # of the loop still holding a node with its `$ref` ON it and handed that back as
        # `resolved` — with `dropped == []`, i.e. as though the walk had succeeded and discarded
        # nothing. MEASURED by `CD-ASR-WO3-08` (arm `R33`) and reproduced here as arm `C25`:
        # `_resolve(...)` -> `resolved = {"$ref": "#/$defs/hop32"} | dropped = []` and
        # `_dial_bearing(...) -> False`, on a tree whose live gate ADMITTED a STALE dial rendering
        # as `calm` on both surfaces. **A RESOLVER THAT SAYS "RESOLVED" ABOUT A NODE IT DID NOT
        # RESOLVE IS THE SAME LIE AS A RECOGNISER THAT SAYS "NOT A DIAL" ABOUT A SHAPE IT COULD
        # NOT READ**, and this row now refuses both. `None` is what every caller already treats as
        # UNRECOGNISED, so the cap is now UNDECIDABLE rather than a clean false answer.
        if depth >= REF_CHAIN_CAP:
            return None, dropped
        ref = node["$ref"]
        asserting = sorted(key for key in node if key not in REF_INERT_SIBLINGS)
        if asserting:
            dropped.append((depth, ref if isinstance(ref, str) else repr(ref), asserting))
        if not isinstance(ref, str) or not ref.startswith("#/"):
            return None, dropped
        cursor = schema
        for token in ref[2:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            if not isinstance(cursor, dict) or token not in cursor:
                return None, dropped
            cursor = cursor[token]
        node, depth = cursor, depth + 1
    return (node if isinstance(node, dict) else None), dropped


def _dropped_sentence(dropped) -> str:
    """How a discarded-sibling set is named in a violation. One sentence, every hop."""
    return " ; ".join(
        f"hop {hop} ({ref}) also declares {keys!r}" for hop, ref, keys in dropped
    )


def _deref(schema: dict, node, depth: int = 0):
    """The resolved node only, for the callers that have no siblings to lose.

    **EVERY CALLER THAT COULD BE MISLED BY A DISCARDED SIBLING USES** :func:`_resolve` **INSTEAD.**
    This wrapper exists so the two cannot drift: there is ONE walk, and one place that decides what
    a `$ref` chain names.
    """
    return _resolve(schema, node, depth)[0]


def _synthesise(schema: dict, subschema, validator):
    """A value the property's OWN subschema accepts, or ``None`` if this check cannot build one.

    Returns ``(value, True)`` on success and ``(None, False)`` on failure, so a legitimate
    ``None``/``null`` value is not confused with an unbuildable property.
    """
    if not isinstance(subschema, dict):
        return None, False
    resolved = _deref(schema, subschema)
    candidates: list = []
    if isinstance(resolved, dict):
        if "const" in resolved:
            candidates.append(resolved["const"])
        if isinstance(resolved.get("enum"), list):
            candidates.extend(resolved["enum"])
    candidates.extend(SYNTHETIC_VALUES)
    try:
        checker = validator(_fragment(schema, subschema))
    except Exception:  # pragma: no cover - a subschema jsonschema cannot even compile
        return None, False
    for candidate in candidates:
        try:
            if checker.is_valid(candidate):
                return candidate, True
        except Exception:  # pragma: no cover - a candidate the validator chokes on
            continue
    return None, False


#: *** THE KEYWORDS THAT MAKE A BRANCH'S ADMISSIBLE SHAPE CONDITIONAL. NEW AT `16B-FIX-2` (`FX5`,
#: closing `CD-ASR-WO3-06` F1). *** :func:`_dial_from_branch` builds ONE document per branch, out of
#: that branch's ``required`` + ``properties``. If the branch also carries any of these, the set of
#: documents it admits is LARGER than the one document built from ``required`` — the branch has
#: variants this check never constructs, and one of them can be the variant that renders `calm`.
#: MEASURED, arm `C11`: `dial_reading_unknown` keeps its name, its `state.const`, its `required`
#: list and `additionalProperties: false`; its `detail_level` is widened; the narrowing is relocated
#: into ``"if": {"required": ["render_hint"]}`` with an ``"else"`` carrying a fully closed copy. A
#: dial WITHOUT the marker is still refused; a dial WITH it is ADMITTED on both surfaces; and the
#: superseded instrument built only the marker-less shape and reported `PASS — 144 assertions, 0
#: violations`.
#:
#: **DENY BY DEFAULT, AND NOT AN ENUMERATION.** This check does not attempt to build one candidate
#: per satisfiable combination of optional markers — that is a schema-instance-generator's job and a
#: design question this row does not price. A branch carrying any of these keywords is returned as
#: UNBUILDABLE and reported as `CD-CALM-BRANCHES-006`, on the same sentence `DECLARED LIMIT 9`
#: already writes for a property this check cannot synthesise: **a branch whose shape is conditional
#: is a branch this check cannot say it has driven.** The clean tree's three branches declare only
#: `type` / `additionalProperties` / `required` / `properties` / `description`, so this costs
#: nothing today. See DECLARED LIMIT 10 (of THIS row; see the NUMBERING note).
CONDITIONAL_KEYWORDS = (
    "if", "then", "else", "allOf", "anyOf", "oneOf", "not",
    "dependentSchemas", "dependentRequired", "unevaluatedProperties",
)


def _dial_from_branch(schema: dict, branch: dict, level, validator, ref_siblings=()):
    """One dial reading built from **THIS BRANCH'S OWN** ``required`` + ``properties``.

    *** THIS IS THE FIX FOR `CD-ASR-WO3-05` F1 AND IT IS THE WHOLE POINT OF `16B-FIX`. *** The
    superseded implementation wrote out the field list of each branch BY HAND, one hard-coded
    document shape per state, so a fourth `oneOf` branch — one the author never wrote — was a
    branch the instrument could not drive, and a tree on which the live gate ADMITTED an `UNKNOWN`
    dial rendering as `calm` left every one of the register's thirty `execute:` lines byte-identical
    to the clean tree. Nothing here is written by hand any more: the field list comes from the
    branch, the values come from each property's own subschema, and `detail_level` — the one token
    under test — is the only thing this function decides.

    *** AND SINCE `16B-FIX-2` IT REFUSES TO PRETEND THE ONE DOCUMENT IS THE WHOLE BRANCH (`FX5`,
    closing `CD-ASR-WO3-06` F1). *** A branch carrying any of :data:`CONDITIONAL_KEYWORDS` admits
    MORE shapes than the one made of `required` + `properties`, so this function returns it as
    UNBUILDABLE and the caller reports `CD-CALM-BRANCHES-006`. **A branch whose shape is conditional
    is a branch this check cannot say it has driven.**

    *** AND SINCE `16B-FIX-3` THAT SENTENCE IS TRUE WHEREVER THE CONDITIONAL IS WRITTEN (`FX9`,
    closing `CD-ASR-WO3-07` F1). *** ``ref_siblings`` is what :func:`_resolve` discarded on the way
    to this branch — every hop of the `$ref` chain that carried an ASSERTING keyword beside its
    `$ref`. In 2020-12 those keywords apply, so a branch that has any is a branch whose admissible
    set is larger than the resolved object shows, and it is UNBUILDABLE for the same reason a
    conditional one is. **THE GUARD BELOW WAS NEVER THE DEFECT: the RESOLVER WAS**, and the fix is
    upstream of here so it does not depend on WHERE the conditional was written (auditor arm `A2`
    put it one hop deeper and the entry-only fix would still have been blind).

    Returns ``(document, None)`` or ``(None, <a sentence naming why it could not be built>)``. The
    obstacle is a SENTENCE and not a bare property name because there are now three ways to fail and
    a violation that named a property for a conditional branch would be false.
    """
    if ref_siblings:
        return None, (
            "the branch is COMPOSED ACROSS A `$ref` BOUNDARY: " + _dropped_sentence(ref_siblings)
            + ". Both contracts declare JSON Schema 2020-12, in which keywords SIBLING to `$ref` "
            "ARE APPLIED, so the object this check resolved is NOT the schema the gate enforces "
            "and every keyword above was silently discarded before any guard saw it. *** MEASURED "
            "(auditor arms A1 and A2): the SAME `if`/`else` this check reports as "
            "CD-CALM-BRANCHES-006 when it is written INSIDE the branch definition was written as a "
            "SIBLING of the `$ref` instead — on the `oneOf` ENTRY in A1 and one hop DEEPER in A2 — "
            "and this instrument reported PASS while the live gate ADMITTED an UNKNOWN dial "
            "rendering as `calm` on BOTH surfaces. *** DENY BY DEFAULT: a branch whose shape is "
            "composed across a `$ref` boundary is a branch this check cannot say it has driven. "
            "See THIS ROW'S DECLARED LIMIT 13"
        )

    conditional = [keyword for keyword in CONDITIONAL_KEYWORDS if keyword in branch]
    if conditional:
        return None, (
            f"the branch declares the conditional keyword(s) {conditional!r}, so the documents it "
            "admits are NOT the single document made of its `required` + `properties`. *** A "
            "BRANCH WHOSE SHAPE IS CONDITIONAL IS A BRANCH THIS CHECK CANNOT SAY IT HAS DRIVEN: "
            "the variant selected by a marker property is one this check never constructs, and on "
            "the tree that measured this (arm C11) that variant is the one the live gate ADMITTED "
            "rendering as `calm` while this instrument reported PASS. *** See THIS ROW'S "
            "DECLARED LIMIT 10"
        )

    required = [name for name in (branch.get("required") or []) if isinstance(name, str)]
    properties = branch.get("properties") or {}
    names = list(required)
    if DETAIL_LEVEL not in names and DETAIL_LEVEL in properties:
        # The branch declares the level but does not REQUIRE it — auditor tree E2. Drive it
        # anyway, or every row below would silently become the field-absent row.
        names.append(DETAIL_LEVEL)
    if DETAIL_LEVEL not in names:
        return None, (
            f"the branch declares no {DETAIL_LEVEL!r} property at all, so there is no token under "
            "test to move and no candidate to build"
        )

    document: dict = {}
    for name in names:
        if name == DETAIL_LEVEL:
            if level is not LEVEL_ABSENT:
                document[name] = level
            continue
        value, built = _synthesise(schema, properties.get(name), validator)
        if not built:
            return None, (
                f"required property {name!r} has a subschema none of this check's declared "
                "synthetic values satisfies. See DECLARED LIMIT 9"
            )
        document[name] = value
    return document, None


def _envelope(surface_value: str, slots: tuple, slot: str, dial: dict, filler: dict) -> dict:
    """A conforming envelope with ONE slot moved to ``dial`` and nothing else.

    Every other slot carries ``filler`` — one admissible absent-data dial, itself derived from the
    contract — so the ONLY thing that varies across the whole matrix is the one dial under test.
    That is what makes `CD-CALM-PAIRED-004`'s one-pointer diff possible.

    THE ENVELOPE ROOT IS STILL WRITTEN OUT HERE, AND THAT IS DECLARED LIMIT 7. It is FAIL-CLOSED
    rather than fail-silent: a required root property this skeleton does not carry makes every
    candidate refused, so every `MUST ADMIT` row fails as `CD-CALM-GATE-002`. The dial BRANCHES were
    the silent case, and they are the ones now derived.
    """
    envelope = {
        "schema_version": None,  # filled by the caller from the application's own constant
        "as_of_utc": AS_OF_UTC,
        "published_utc": PUBLISHED_UTC,
        "regime": "CALM",
        "staleness_window_seconds": 600.0,
        "inputs_used": [],
        "degraded_inputs": [],
        "config_snapshot_id": SYNTHETIC_CONFIG_SNAPSHOT_ID,
    }
    for name in slots:
        envelope[name] = dict(filler)
    if surface_value == "private":
        envelope["classification"] = "PRIVATE"
    envelope[slot] = dial
    return envelope


def _pointers(node, pointer: str = "") -> dict:
    """Every LEAF of a JSON document, keyed by RFC 6901 pointer. Used only for the diff."""
    out: dict = {}
    if isinstance(node, dict):
        for key, value in node.items():
            token = str(key).replace("~", "~0").replace("/", "~1")
            out.update(_pointers(value, f"{pointer}/{token}"))
    elif isinstance(node, list):
        if not node:
            out[pointer] = "[]"
        for index, value in enumerate(node):
            out.update(_pointers(value, f"{pointer}/{index}"))
    else:
        out[pointer] = node
    return out


def _differing_pointers(left: dict, right: dict) -> list:
    a, b = _pointers(left), _pointers(right)
    return sorted(set(a) ^ set(b)) + sorted(k for k in set(a) & set(b) if a[k] != b[k])


def _expectations(levels: tuple, absent_data: bool) -> tuple:
    """The proposition table for ONE branch: ``(level, expectation)``.

    `levels` is read from the contract's own `#/$defs/detail_level` enum rather than typed in,
    so a fourth level added to the vocabulary is driven on the day it is added instead of being
    silently unexercised. The RULE is what is written here and it is written once:

      * an ABSENT-DATA branch carrying `calm` MUST BE REFUSED;
      * everything else in the vocabulary MUST BE ADMITTED, including `calm` on a present-data
        branch — that is the vacuity arm and it carries equal weight;
      * and, NEW AT `16B-FIX` (`FX2`, closing `CD-ASR-WO3-05` F2), an absent-data branch carrying
        NO `detail_level` key at all, or one OUTSIDE the vocabulary, MUST ALSO BE REFUSED. Both
        rows were asserted by `tests/test_detail_level.py` before this instrument existed and both
        were dropped when the property moved into the register; the superseded instrument was
        therefore STRICTLY WEAKER than the memorial it was built to replace, while this row's own
        `negative_control` said in two governed artefacts that it "fails on all of these".
    """
    rows = [(level, MUST_REFUSE if (absent_data and level == CALM) else MUST_ADMIT)
            for level in levels]
    if absent_data:
        rows.append((LEVEL_ABSENT, MUST_REFUSE))
        rows.append((OFF_VOCABULARY_LEVEL, MUST_REFUSE))
    return tuple(rows)


def _label_for(level) -> str:
    """How a row's level is named in a cell label and in a violation."""
    if level is LEVEL_ABSENT:
        return "<no detail_level key>"
    return str(level)


#: The keywords a subschema can hide another subschema behind — the set :func:`_dial_bearing`
#: DESCENDS INTO. `$defs` is deliberately ABSENT and the reason is unchanged: descending into the
#: definition pot from a single property would make every property reach every definition, and a
#: definition that is actually in force is reached by the `$ref` :func:`_resolve` follows.
#:
#: *** `dependentSchemas` ADDED AT `16B-FIX-4` (`FX13`, closing `CD-ASR-WO3-08` F2). *** It was
#: named as an applicator in :data:`CONDITIONAL_KEYWORDS` — this module's own statement that it
#: widens what a schema admits — and omitted here, in the same file, two hundred lines away.
#: **`_SUBSCHEMA_KEYWORDS` WAS THE CONSTANT THAT WAS WRONG**: `CONDITIONAL_KEYWORDS` correctly
#: names every keyword that makes a BRANCH admit more than `required` + `properties` describes,
#: and `dependentSchemas` belongs in it; this list must contain every keyword that can carry a
#: subschema, and `dependentSchemas` was missing from it. (The two lists are NOT meant to be
#: equal — `dependentRequired` is legitimately in the first and not here because it carries no
#: subschema, and `properties`/`items` are legitimately here and not there because they do not by
#: themselves widen a branch. `dependentSchemas` was the ONE genuine disagreement.)
_SUBSCHEMA_KEYWORDS = (
    "allOf", "anyOf", "oneOf", "not", "if", "then", "else",
    "items", "prefixItems", "contains", "additionalItems", "additionalProperties",
    "properties", "patternProperties", "propertyNames", "dependentSchemas",
    "contentSchema", "unevaluatedItems", "unevaluatedProperties",
)

#: The keywords whose KEYS ARE PROPERTY NAMES THIS RECOGNISER READS LITERALLY. This is the whole
#: of what "it declares a property called `state`" is decided from, and it is READ rather than
#: pattern-matched: a name in any of these is a name this check has seen.
_NAME_DECLARING_KEYWORDS = ("properties", "required", "dependentRequired")

#: *** DESCENDED INTO, BUT NEVER A CLEAN `False`. *** These carry subschemas — so the walk goes
#: into them and a dial underneath one can still come back `True` — but their KEYS are property
#: names this recogniser does NOT evaluate: `patternProperties` keys are regular expressions,
#: `propertyNames` constrains names it never lists, and `dependentSchemas` keys select a whole
#: schema by the presence of another property. A node declaring one of these can therefore be
#: declaring a property named `state` in a way :data:`_NAME_DECLARING_KEYWORDS` cannot see, so it
#: is UNDECIDABLE. (`CD-ASR-WO3-08` F1 arms `P1` and `D2`; arms `C22` and `C23`.)
_NAME_BEARING_APPLICATORS = frozenset({
    "patternProperties", "propertyNames", "dependentSchemas",
})

#: *** EVERY REMAINING JSON SCHEMA 2020-12 KEYWORD THAT CARRIES NO SUBSCHEMA AND NAMES NO
#: PROPERTY. *** Enumerated from the specification's own vocabularies — Core, Applicator,
#: Validation, Format-Annotation, Content and Meta-Data — and DELIBERATELY EXHAUSTIVE, because
#: this is the list that decides when the recogniser is allowed to say `False`. Four Core
#: keywords are ABSENT ON PURPOSE and are therefore UNREADABLE: `$id` (it moves the base URI a
#: relative `$ref` resolves against, and :func:`_resolve` always resolves against the document
#: root), `$dynamicRef`, `$dynamicAnchor` and `$recursiveRef`/`$recursiveAnchor` (references this
#: resolver does not follow — `CD-ASR-WO3-08` F1 arm `DYN`, arm `C24`).
_INERT_KEYWORDS = frozenset({
    # Core, and inert HERE
    "$schema", "$vocabulary", "$comment", "$anchor", "$defs",
    # Validation — assertions about a value, carrying no subschema
    "type", "enum", "const", "multipleOf", "maximum", "exclusiveMaximum", "minimum",
    "exclusiveMinimum", "maxLength", "minLength", "pattern", "maxItems", "minItems",
    "uniqueItems", "maxContains", "minContains", "maxProperties", "minProperties",
    # Format and Content
    "format", "contentEncoding", "contentMediaType",
    # Meta-Data — pure annotation
    "title", "description", "default", "deprecated", "readOnly", "writeOnly", "examples",
})

#: *** THE INVERSION, AND IT IS THE WHOLE OF `FX12`. *** The recogniser may answer `False` — "this
#: is NOT a dial" — only about a node EVERY KEYWORD OF WHICH IS IN THIS SET: either one it
#: descends into (so it has looked underneath), or one it knows carries nothing to look under, or
#: one whose property names it reads. **A KEYWORD THAT IS NOT IN THIS SET IS ONE THIS CHECK
#: CANNOT READ, AND A NODE IT CANNOT FULLY READ IS UNDECIDABLE.** That is a property of what the
#: node actually declares, not of a list of attacks: the four escapes of `A306`/`A307`/`A308` and
#: every spelling nobody has thought of yet fail the SAME test, which is that this file has never
#: heard of the keyword.
_READABLE_KEYWORDS = (
    (frozenset(_SUBSCHEMA_KEYWORDS) - _NAME_BEARING_APPLICATORS)
    | frozenset(_NAME_DECLARING_KEYWORDS)
    | _INERT_KEYWORDS
)


def _dial_bearing(schema: dict, node, depth: int = 0, seen=None):
    """Does this subschema DECLARE a dial ``state``? ``True`` / ``False`` / ``None`` = undecidable.

    *** THIS IS THE FIX FOR `CD-ASR-WO3-05` F3 AND IT IS WHY `DECLARED LIMIT 4` CAN NOW BE STATED
    TRUTHFULLY. *** The slot enumerator drives every root property spelled EXACTLY
    ``{"$ref": "#/$defs/dial_reading"}`` — that is what it has always done, and the superseded limit
    claimed more. This function is the fail-closed half: it recognises a dial-bearing root property
    under any spelling of the `$ref` chain, so a dial slot this instrument does NOT drive is a
    VIOLATION rather than an invisible one. Auditor tree `E1` — an OPTIONAL third slot
    `credit_stress` referencing a permissive union — passed the superseded instrument at
    `67 assertions, 0 violations` while the live gate ADMITTED `calm` on it, on both surfaces.

    *** AND SINCE `16B-FIX-2` THE VOCABULARY IS NOT PART OF THE RECOGNITION (`FX6`, closing
    `CD-ASR-WO3-06` F2). *** Returning ``False`` for a declared `state` this check cannot classify
    made this a PATTERN RECOGNISER WEARING DENY-BY-DEFAULT'S CLOTHES, and the pattern was
    `DECLARED_STATES`. THE THREE OUTCOMES ARE NOW:

      ``True``   the resolved subschema declares a `state` whose `const`/`enum` INTERSECTS
                 `DECLARED_STATES` — a dial this check can classify;
      ``None``   it declares a `state` this check CANNOT classify, or hides a subschema behind a
                 keyword outside the declared set, or nests deeper than the walk, or carries a
                 `$ref` that does not resolve — **UNDECIDABLE, and reported**;
      ``False``  nothing anywhere under it declares a property named `state`, **AND EVERY KEYWORD
                 IT DECLARES, AT EVERY NODE THE WALK VISITED, IS ONE THIS CHECK CAN READ.**

    **THE THIRD LINE IS THE RESIDUE AND IT IS DECLARED, NOT HIDDEN** — this row's `DECLARED
    LIMIT 12`. The looser form (declaring a `state` is enough) was RULED over the tighter one
    (require a `state` AND a `detail_level`): a false positive costs one seat one look at one
    contract; a false negative costs the constitution.

    *** AND SINCE `16B-FIX-3` THE FIRST OF THOSE THREE LINES IS TRUE OF A `state` OF **ANY** SHAPE
    (`FX10`, closing `CD-ASR-WO3-07` F2), AND A CHAIN THAT DISCARDED AN ASSERTION IS UNDECIDABLE
    (`FX9`, closing F1). *** `FX6` put the `undecidable = True` limb inside
    `if isinstance(state, dict)`, so a `state` spelled as the boolean schema `true` — legal in
    2020-12 — was skipped and the property was classified **not a dial**: instrument
    `PASS — 144 assertions, 0 violations` with the gate ADMITTING `{state: STALE, detail_level:
    'calm'}` on both surfaces (auditor arm `D1`, arm `C20`). **DECLARING the key is now the whole
    trigger; the key's SHAPE can only refine the answer to ``True`` and never back to ``False``.**

    *** AND SINCE `16B-FIX-4` THE DEFAULT IS INVERTED AT THIS RECOGNISER TOO, WHICH IS THE ONLY
    THING THAT BOUNDS THE CLASS (`FX12`, closing `CD-ASR-WO3-08` F1). *** `FX6` and `FX10` each
    made the trigger independent of one more thing — the state VOCABULARY, then the state key's
    SHAPE — and each left it wholly dependent on the KEYWORD the key is declared under, which was
    read as `properties` and nothing else. **FOUR AUDITS ESCAPED THIS FUNCTION WITH FOUR
    SPELLINGS OF ONE IDEA AND EACH FIX CLOSED THE SPELLING IT WAS SHOWN.** What is different here
    is the QUESTION: this walk no longer asks a list of keywords whether they are present, it
    asks the NODE whether every keyword it declares is one this check can read
    (:data:`_READABLE_KEYWORDS`), and a node it cannot fully read is UNDECIDABLE. `False` is now
    a claim about a shape that was READ, not a shape that was not recognised.

    *** IT DOES NOT ADD A THIRD DIAL SLOT TO ANYTHING. *** `PO-DECISIONS-0026` standing is TWO
    DIALS, NEVER BLENDED. This makes the enumerator honest about what it drives; it drives nothing
    new on the clean tree, where the two sets are equal and the undecidable set is empty.
    """
    if depth > 24:
        return None
    seen = set() if seen is None else seen
    resolved, dropped = _resolve(schema, node)
    if resolved is None:
        return None
    if dropped:
        # *** THE RESOLVER DISCARDED AN ASSERTION. NEW AT `16B-FIX-3` (`FX9`, closing
        # `CD-ASR-WO3-07` F1). *** In 2020-12 a keyword sibling to `$ref` APPLIES, so the object
        # just resolved is not the schema the gate enforces and any answer derived from it would be
        # about a schema nobody wrote. UNDECIDABLE, never False. See DECLARED LIMIT 13.
        return None
    if id(resolved) in seen:
        return False
    seen = seen | {id(resolved)}

    undecidable = False

    # *** THE INVERSION. NEW AT `16B-FIX-4` (`FX12`, closing `CD-ASR-WO3-08` F1 AS A CLASS). ***
    # THE SUPERSEDED WALK ASKED, OF A LIST OF KEYWORDS IT HAD THOUGHT OF, "is this one present?"
    # — so any keyword it had NOT thought of was invisible and the node fell through to `False`.
    # That is how this recogniser was escaped FOUR TIMES BY FOUR SPELLINGS OF ONE IDEA
    # (`A306` a new state vocabulary, `A307` a boolean `state`, `A308` `patternProperties` /
    # `dependentSchemas` / `$dynamicRef` / a chain past the resolver's cap), each fix closing the
    # spelling it was shown. **THIS ASKS THE OPPOSITE QUESTION, OF THE NODE AND NOT OF A LIST:
    # for every keyword ACTUALLY PRESENT here, can this check read it?** A keyword outside
    # `_READABLE_KEYWORDS` — a 2020-12 keyword nobody wired up, a keyword from a draft not yet
    # written, a custom vocabulary, an applicator this walk does not descend — makes the node
    # UNDECIDABLE. **"I could not read this" and "this is not a dial" are different answers and
    # only one of them is safe** (`PO-DECISIONS-0026` ruling 10, GUARD_THE_INSTANCE_NOT_THE_CLASS).
    # THE COST IS PRICED AND IT IS THE RULED DIRECTION: a false positive costs one seat one look
    # at one contract; a false negative costs the constitution. See DECLARED LIMIT 14.
    unreadable = sorted(key for key in resolved if key not in _READABLE_KEYWORDS)
    if unreadable:
        undecidable = True

    properties = resolved.get("properties")
    # *** THE TRIGGER IS THE PRESENCE OF THE DECLARED KEY, NOT ITS SHAPE. NEW AT `16B-FIX-3`
    # (`FX10`, closing `CD-ASR-WO3-07` F2). *** The superseded code read
    # `state = _deref(...) if isinstance(state, dict) else None` and put the whole `undecidable`
    # limb inside `if isinstance(state, dict)`, so a `state` spelled as the BOOLEAN SCHEMA `true`
    # — legal in 2020-12 and maximally permissive — dropped to None, the limb never ran, the
    # `_SUBSCHEMA_KEYWORDS` descent skipped it too, and the property was classified NOT A DIAL.
    # MEASURED, auditor arm `D1` and arm `C20`: instrument `PASS — 144 assertions, 0 violations`,
    # the property in NEITHER the classifiable nor the undecidable list, and the live gate ADMITTING
    # `{state: STALE, detail_level: 'calm'}` on BOTH surfaces. DECLARED LIMIT 12 did not cover it —
    # that limit is about a differently-NAMED discriminator and D1's dial declares a property
    # literally called `state`. **A ROOT PROPERTY THAT DECLARES A `state` REACHES THE UNDECIDABLE
    # LIMB WHATEVER THE SHAPE OF THAT KEY'S SUBSCHEMA**; the shape can only ever REFINE the answer
    # to `True`, never back to `False`.
    # *** WIDENED AT `16B-FIX-4` (`FX12`). *** `properties` is no longer the only keyword whose
    # property NAMES this check reads: `required: ["state"]` and `dependentRequired` name a
    # property just as literally, and a node that names `state` in either of them without giving
    # it a subschema is a node that requires a `state` it constrains not at all. Reading them is
    # a COMPLETE read of those keywords, which is why they are in `_READABLE_KEYWORDS`; the
    # keywords whose names this check CANNOT read are handled by the inversion above.
    declared = set()
    if isinstance(properties, dict):
        declared |= {key for key in properties if isinstance(key, str)}
    required = resolved.get("required")
    if isinstance(required, list):
        declared |= {name for name in required if isinstance(name, str)}
    dependent_required = resolved.get("dependentRequired")
    if isinstance(dependent_required, dict):
        for names in dependent_required.values():
            if isinstance(names, list):
                declared |= {name for name in names if isinstance(name, str)}

    if "state" in declared:
        subschema = properties.get("state") if isinstance(properties, dict) else None
        state, state_dropped = (
            _resolve(schema, subschema) if isinstance(subschema, dict) else (None, [])
        )
        if state_dropped:
            state = None  # composed across a `$ref` boundary — its const/enum cannot be trusted
        if isinstance(state, dict):
            if state.get("const") in DECLARED_STATES:
                return True
            values = state.get("enum")
            if isinstance(values, list) and set(values) & set(DECLARED_STATES):
                return True
        # *** DECLARING A `state` IS ENOUGH TO STOP THE CHECK. NEW AT `16B-FIX-2` (`FX6`, closing
        # `CD-ASR-WO3-06` F2). *** The superseded code fell through to False here, so a root
        # property that is a dial in every respect the product cares about, but whose state
        # vocabulary is NEW, was classified NOT-A-DIAL and was SILENT. MEASURED: arm `C13`
        # (`credit_stress`, state const `NO_DATA`) and arm `C14` (`feed_liveness`, states
        # `["LIVE","STALE"]` — PO-DECISIONS-0026 ruling 5's liveness quantity written the obvious
        # way) both had the live gate ADMIT a missing/stale dial rendering as `calm` on BOTH
        # surfaces while this instrument reported `PASS — 144 assertions, 0 violations`; the same
        # property with the state spelled `["UNKNOWN","STALE"]` was caught. The only difference
        # between a caught tree and an uncaught one was whether the new dial reused an OLD STATE
        # NAME, which is GUARD_THE_INSTANCE_NOT_THE_CLASS (PO-DECISIONS-0026 ruling 10).
        # "I cannot classify this state vocabulary" is exactly the case DECLARED LIMIT 8 says must
        # STOP the check, so it is UNDECIDABLE and never False. The LOOSER form is deliberate and
        # RULED: a false positive costs one seat one look at one contract; a false negative costs
        # the constitution. See DECLARED LIMIT 12 (of THIS row; see the NUMBERING note).
        undecidable = True


    for keyword in _SUBSCHEMA_KEYWORDS:
        if keyword not in resolved:
            continue
        child = resolved[keyword]
        children = (list(child.values()) if isinstance(child, dict) and keyword in
                    ("properties", "patternProperties", "dependentSchemas")
                    else child if isinstance(child, list) else [child])
        for entry in children:
            if not isinstance(entry, (dict, list)):
                continue
            verdict = _dial_bearing(schema, entry, depth + 1, seen)
            if verdict is True:
                return True
            if verdict is None:
                undecidable = True
    return None if undecidable else False


def _branch_states(schema: dict, dial_union: dict):
    """The union's branches as ``(label, resolved_branch, state_const, ref_siblings)``.

    The branch SET is what the superseded instrument never enumerated. It wrote out one document
    shape per state by hand, so the union could grow a branch and nothing anywhere would move.

    *** THE FOURTH ELEMENT IS NEW AT `16B-FIX-3` (`FX9`, closing `CD-ASR-WO3-07` F1). *** It is
    every ASSERTING keyword the `$ref` chain from the `oneOf` ENTRY to the branch definition — and
    from the branch to its `state` subschema — discarded on the way. **IT IS COLLECTED AT EVERY
    HOP AND NOT ONLY AT THE ENTRY**, because auditor arm `A2` wrote the conditional one `$ref`
    deeper, behind an innocuous entry, and got the identical escape.
    """
    branches = dial_union.get("oneOf")
    if not isinstance(branches, list) or not branches:
        return None
    out = []
    for index, entry in enumerate(branches):
        label = entry.get("$ref") if isinstance(entry, dict) and isinstance(
            entry.get("$ref"), str) else f"oneOf[{index}]"
        resolved, dropped = _resolve(schema, entry) if isinstance(entry, dict) else (None, [])
        state = None
        if isinstance(resolved, dict):
            declared = resolved.get("properties", {}).get("state") if isinstance(
                resolved.get("properties"), dict) else None
            declared, declared_dropped = (
                _resolve(schema, declared) if isinstance(declared, dict) else (None, []))
            dropped = list(dropped) + list(declared_dropped)
            if isinstance(declared, dict) and isinstance(declared.get("const"), str):
                state = declared["const"]
        out.append((label, resolved, state, dropped))
    return out


def main(argv=None) -> int:
    args = parse_root(CHECK_ID, __doc__.splitlines()[0])
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code
    check = Check(CHECK_ID, root)

    src = root / "src"
    if not (src / "crash_detector" / "__init__.py").is_file():
        return check.refuse(
            f"{src}/crash_detector/__init__.py does not exist, so there is no gate to drive. "
            "'REFUSED' is a RUNTIME claim and this check will not make it against a tree it "
            "could not load."
        )

    sys.path.insert(0, str(src))
    for name in [
        m for m in sys.modules if m == "crash_detector" or m.startswith("crash_detector.")
    ]:
        del sys.modules[name]

    try:
        import crash_detector  # noqa: F401
        from crash_detector.dials.dialset import DIAL_IDS
        from crash_detector.dials.reading import Unknown
        from crash_detector.publication.detail_level import (
            DetailPolicy,
            DetailPolicyIncoherent,
            detail_level_for,
        )
        from crash_detector.publication.envelope_contract import (
            ENVELOPE_SCHEMA_VERSION,
            EnvelopeSurface,
            PublicationRefused,
            REFUSAL_SCHEMA_VIOLATION,
            contracts_dir,
            load_envelope_schema,
            refuse_unless_publishable,
            schema_path_for,
        )
    except Exception as exc:  # pragma: no cover - a tree that will not import
        return check.refuse(
            f"the subject tree at {src} did not import: {type(exc).__name__}: {exc}. If this "
            "is a missing `jsonschema`, that is DECLARED LIMIT 6: this check drives the live "
            "gate and the live gate validates with jsonschema."
        )

    try:
        import jsonschema  # noqa: F401
        from jsonschema.validators import validator_for
    except Exception as exc:  # pragma: no cover - DECLARED LIMIT 6
        return check.refuse(
            f"`jsonschema` did not import ({type(exc).__name__}: {exc}). DECLARED LIMIT 6: this "
            "check drives the live gate, the live gate validates with jsonschema, and a "
            "behavioural check cannot be more stdlib-only than the behaviour it drives."
        )

    package_dir = pathlib.Path(crash_detector.__file__).resolve().parent
    # CD-PL-F98 — READ THE TREE LINE EVERY TIME. A contrast run against the wrong tree is
    # indistinguishable from a fix that does nothing.
    check.note(f"imported crash_detector from: {package_dir / '__init__.py'}")
    check.note(f"python: {sys.version.split()[0]}")
    check.note(f"ENVELOPE_SCHEMA_VERSION as the application declares it: {ENVELOPE_SCHEMA_VERSION}")

    # ---- DECLARED LIMIT 1, ENFORCED AS A PRECONDITION -------------------------------- #
    # The gate reads $CD_CONTRACTS_DIR. If it resolves anywhere but the subject tree, this
    # check would be judging documents that are not the subject's, and its clean exit would be
    # a statement about somebody else's files. Non-zero with the reason; never a pass.
    resolved = contracts_dir().resolve()
    if resolved != (root / "contracts").resolve():
        return check.refuse(
            f"the live gate resolves its contracts to {resolved}, which is NOT "
            f"{(root / 'contracts').resolve()}. $CD_CONTRACTS_DIR is set, or the package was "
            "imported from outside --root. This check judges the contract the gate ACTUALLY "
            "LOADS, so it will not report on a tree it is not looking at (DECLARED LIMIT 1)."
        )

    schemas = {}
    for surface in EnvelopeSurface:
        path = schema_path_for(surface)
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            return check.refuse(f"cannot read {path}: {type(exc).__name__}: {exc}")
        check.note(f"judging {surface.value} contract {path} sha256:{digest}")
        try:
            schemas[surface] = load_envelope_schema(surface)
        except Exception as exc:
            return check.refuse(
                f"the {surface.value} contract is not loadable by the gate: "
                f"{type(exc).__name__}: {exc}. The candidate would never be judged, so this "
                "check has nothing to measure."
            )

    here = pathlib.Path(__file__)

    # ---- THE SUBJECT SET, ENUMERATED FROM THE APPLICATION AND THE CONTRACT ------------ #
    # Dial slots are the top-level properties that $ref the dial_reading union, read from the
    # contract itself. Typing them in would mean a third dial added tomorrow is never driven.
    #
    # *** AND THE FAIL-CLOSED HALF, NEW AT 16B-FIX (FX3, closing CD-ASR-WO3-05 F3). *** What is
    # DRIVEN is every property spelled EXACTLY {"$ref": "#/$defs/dial_reading"}. What is
    # ENUMERATED FOR COMPARISON is every root property that DECLARES a dial `state` (and, since
    # 16B-FIX-2 / FX6, one whose state VOCABULARY this check cannot classify is UNDECIDABLE and
    # reported, never False). If those two sets differ, there is a dial-bearing slot it cannot
    # drive, and that is a VIOLATION rather than a silence. Auditor tree E1 — an OPTIONAL third
    # slot spelled with a different $ref — passed the superseded instrument while the gate
    # ADMITTED `calm` on it, on both surfaces.
    slots_by_surface = {}
    for surface, schema in schemas.items():
        properties = schema.get("properties") or {}
        found = tuple(
            sorted(
                name
                for name, sub in properties.items()
                if isinstance(sub, dict) and sub.get("$ref") == "#/$defs/dial_reading"
            )
        )
        slots_by_surface[surface] = found
        check.note(f"{surface.value} dial slots DRIVEN (literal $ref to #/$defs/dial_reading): "
                   f"{list(found)}")
        if not found:
            return check.refuse(
                f"the {surface.value} contract declares no property referencing "
                "'#/$defs/dial_reading'. There is no dial to drive, so a clean exit would "
                "mean 'I looked at nothing'."
            )

        dial_bearing, undecidable = [], []
        for name, sub in sorted(properties.items()):
            verdict = _dial_bearing(schema, sub)
            if verdict is True:
                dial_bearing.append(name)
            elif verdict is None:
                undecidable.append(name)
        check.note(f"{surface.value} root properties that DECLARE a dial state this check can "
                   f"classify: {dial_bearing}")
        if undecidable:
            check.note(f"{surface.value} root properties this check CANNOT decide about "
                       f"(UNDECIDABLE, reported below): {undecidable}")

        check.asserted(2)
        if set(dial_bearing) != set(found):
            check.violation(
                here, 0, "CD-CALM-SLOTS-007",
                f"{surface.value}: the contract declares dial-bearing root properties "
                f"{sorted(set(dial_bearing) - set(found))!r} that are NOT spelled "
                "'{\"$ref\": \"#/$defs/dial_reading\"}' and are therefore NOT DRIVEN by this "
                "instrument, "
                f"and/or drives {sorted(set(found) - set(dial_bearing))!r} that no longer "
                "constrains a dial state. *** A DIAL SLOT THIS CHECK CANNOT DRIVE IS A SLOT ON "
                "WHICH PID §3.2 IS UNGUARDED, and the superseded DECLARED LIMIT 4 claimed the "
                "opposite. *** This assertion FAILS CLOSED rather than the enumerator widening "
                "itself: two dials, never blended, is standing product (PO-DECISIONS-0026), so "
                "a third dial slot is a PRODUCT decision and not this instrument's to absorb.",
            )
        if undecidable:
            check.violation(
                here, 0, "CD-CALM-SLOTS-007",
                f"{surface.value}: root properties {undecidable!r} use a construct this check "
                "cannot decide about — *** A `state` VOCABULARY OUTSIDE THIS CHECK'S DECLARED, "
                f"CLOSED SET {sorted(DECLARED_STATES)!r} (NEW AT 16B-FIX-2, FX6) ***, a $ref it "
                "could not resolve OR one whose chain is longer than this check follows, "
                "*** ANY KEYWORD THE NODE DECLARES THAT THIS CHECK CANNOT READ (NEW AT 16B-FIX-4, "
                "FX12) ***, or a nesting deeper than "
                "it walks. DENY BY DEFAULT (RULE F): an undecidable root property is reported as "
                "UNRECOGNISED, because 'I could not tell whether that is a dial' must never read "
                "the same as 'it is not'. Whether a NEW state MEANS the data is absent or stale "
                "is product meaning and not an Engineer's to guess (PBG-AUTH-005): guess "
                "'present' and `calm` is silently admitted on it, which is CD-AC-001's own words "
                "— 'missing OR STALE input never renders as calm' — broken in silence. See "
                "DECLARED LIMIT 8 and this row's DECLARED LIMIT 12.",
            )

    vocabulary = tuple((schemas[EnvelopeSurface.PUBLIC].get("$defs") or {})
                       .get("detail_level", {}).get("enum") or ())
    if not vocabulary:
        return check.refuse(
            "the public contract declares no '#/$defs/detail_level' enum, so this check "
            "cannot enumerate the vocabulary it must drive."
        )
    check.note(f"detail_level vocabulary enumerated from the contract: {list(vocabulary)}")
    if OFF_VOCABULARY_LEVEL in vocabulary:
        return check.refuse(
            f"the contract now declares {OFF_VOCABULARY_LEVEL!r} as a real detail_level, so this "
            "check's OFF-VOCABULARY row is no longer off-vocabulary and would assert something "
            "that has quietly become false. Non-zero with the reason, never a pass (PBG-CI-002)."
        )

    absent_table = _expectations(vocabulary, absent_data=True)
    present_table = _expectations(vocabulary, absent_data=False)

    # ---- CD-CALM-VACUITY-000 — THE TABLE ITSELF IS NOT DEGENERATE -------------------- #
    check.asserted(3)
    if not any(expectation == MUST_REFUSE for _, expectation in absent_table):
        check.violation(
            here, 0, "CD-CALM-VACUITY-000",
            "this check's own proposition table contains no MUST REFUSE row. It would then "
            "assert nothing about PID §3.2 at all.",
        )
    if not any(
        level == CALM and expectation == MUST_ADMIT for level, expectation in present_table
    ):
        check.violation(
            here, 0, "CD-CALM-VACUITY-000",
            "*** THIS CHECK'S OWN VACUITY ARM IS GONE. *** The table no longer requires that a "
            "VALUE dial carrying 'calm' is ADMITTED, so every remaining arm would be satisfied "
            "by a contract in which no dial can ever read calm on any branch. That is not PID "
            "§3.2 held, it is silence enforced, and it is the failure mode this instrument was "
            "written to be incapable of.",
        )
    if not (
        any(level is LEVEL_ABSENT and expectation == MUST_REFUSE
            for level, expectation in absent_table)
        and any(level == OFF_VOCABULARY_LEVEL and expectation == MUST_REFUSE
                for level, expectation in absent_table)
    ):
        check.violation(
            here, 0, "CD-CALM-VACUITY-000",
            "*** THIS CHECK'S FIELD-ABSENT AND OFF-VOCABULARY ROWS ARE GONE. *** Those two rows "
            "are what stop this instrument being STRICTLY WEAKER than the memorial it "
            "superseded: tests/test_detail_level.py has asserted both since before this file "
            "existed, and both were dropped when the property moved into the register "
            "(CD-ASR-WO3-05 F2). Losing them again is how a guard becomes a certificate.",
        )

    # ---- CD-CALM-BRANCHES-006 — THE UNION'S BRANCH SET, ENUMERATED AND CLOSED --------- #
    # *** THE STRUCTURAL HALF OF THE F1 FIX, AND IT DENIES BY DEFAULT (RULE F, the shape
    # check_no_numeric_default already established here). *** The superseded instrument never
    # looked at #/$defs/dial_reading.oneOf at all: it wrote one document shape per state by
    # hand, so a FOURTH branch — permitting the full vocabulary on UNKNOWN, selected by a marker
    # property, adding NO root key so check_schema_closed's allowlist never fires — left the
    # gate ADMITTING a calm UNKNOWN dial on both surfaces with all thirty of the register's
    # `execute:` lines byte-identical to the clean tree (CD-ASR-WO3-05 F1, tree E3).
    #
    # A branch is recognised by its own `properties.state.const` — NEVER by the name of the
    # $def it lives in — so the pure-rename refactor this instrument already survives keeps
    # passing. What is closed is the SHAPE of the branch set: exactly one branch per declared
    # state, no duplicates, no extras, and every declared state one this check can classify.
    branches_by_surface = {}
    for surface, schema in schemas.items():
        dial_union, union_dropped = _resolve(
            schema, (schema.get("$defs") or {}).get("dial_reading"))
        if dial_union is None:
            return check.refuse(
                f"the {surface.value} contract's '#/$defs/dial_reading' does not resolve to a "
                "schema object, so there is no union to enumerate and no branch to drive."
            )
        branches = _branch_states(schema, dial_union)
        if branches is None:
            return check.refuse(
                f"the {surface.value} contract's '#/$defs/dial_reading' declares no non-empty "
                "'oneOf'. This check drives EVERY branch of the union; with no union declared "
                "it has nothing to enumerate and a clean exit would mean 'I looked at nothing'."
            )
        branches_by_surface[surface] = branches
        check.note(f"{surface.value} dial_reading.oneOf branches enumerated: "
                   + repr([(label, state) for label, _, state, _ in branches]))
        composed = [(label, dropped) for label, _, _, dropped in branches if dropped]
        if composed:
            check.note(f"{surface.value} dial_reading.oneOf branches COMPOSED ACROSS A `$ref` "
                       f"BOUNDARY (reported below): {[label for label, _ in composed]!r}")

        declared = dial_union.get("properties", {}).get("state") if isinstance(
            dial_union.get("properties"), dict) else None
        declared, declared_dropped = (
            _resolve(schema, declared) if isinstance(declared, dict) else (None, []))
        contract_states = (tuple(declared.get("enum") or ())
                           if isinstance(declared, dict) and not declared_dropped else ())

        check.asserted(4)
        # *** THE UNION ITSELF, AND ITS OWN `state`, RESOLVED WITHOUT LOSING AN ASSERTION. NEW AT
        # `16B-FIX-3` (`FX9`). *** No new `check.asserted` here on purpose: this rides the four
        # branch-set assertions already counted, so the clean tree's assertion total is unchanged.
        if union_dropped or declared_dropped:
            check.violation(
                here, 0, "CD-CALM-BRANCHES-006",
                f"{surface.value}: '#/$defs/dial_reading' is COMPOSED ACROSS A `$ref` BOUNDARY — "
                + _dropped_sentence(list(union_dropped) + list(declared_dropped))
                + ". In JSON Schema 2020-12, which both contracts declare, those keywords APPLY, "
                "so the union this check enumerated is not the union the gate enforces and its "
                "branch set cannot be called closed. DENY BY DEFAULT. See DECLARED LIMIT 13.",
            )
        unreadable = [label for label, resolved, state, _ in branches
                      if resolved is None or state is None]
        if unreadable:
            check.violation(
                here, 0, "CD-CALM-BRANCHES-006",
                f"{surface.value}: branches {unreadable!r} of '#/$defs/dial_reading.oneOf' do "
                "not resolve to a schema object declaring 'properties.state.const' as a string. "
                "DENY BY DEFAULT: a branch this check cannot IDENTIFY is a branch it cannot "
                "DRIVE, and an undriven branch of the published union is a shape on which PID "
                "§3.2 is unguarded. Unrecognised is a VIOLATION, never a silence.",
            )
        states = [state for _, _, state, _ in branches if state is not None]
        duplicated = sorted({s for s in states if states.count(s) > 1})
        if duplicated:
            check.violation(
                here, 0, "CD-CALM-BRANCHES-006",
                f"{surface.value}: '#/$defs/dial_reading.oneOf' declares MORE THAN ONE branch "
                f"for the dial state(s) {duplicated!r}. *** A SECOND BRANCH FOR A STATE THAT "
                "ALREADY HAS ONE IS THE E3 SHAPE: it can widen what that state may carry while "
                "the original branch, and every structural check that reads it, stays exactly "
                "as it was. *** One branch per state, or this check cannot say which document "
                "shape the state actually permits.",
            )
        if contract_states and set(states) != set(contract_states):
            check.violation(
                here, 0, "CD-CALM-BRANCHES-006",
                f"{surface.value}: the union's branch states {sorted(set(states))!r} are not "
                f"the states '#/$defs/dial_reading.properties.state' declares, "
                f"{sorted(set(contract_states))!r}. A declared state with no branch is "
                "unconstrained; a branch for an undeclared state is a shape nobody declared.",
            )
        if set(contract_states or states) != set(DECLARED_STATES):
            check.violation(
                here, 0, "CD-CALM-BRANCHES-006",
                f"{surface.value}: the contract declares dial states "
                f"{sorted(set(contract_states or states))!r}, which is not this check's "
                f"declared, closed set {sorted(DECLARED_STATES)!r}. *** DENY BY DEFAULT: a "
                "state nobody anticipated is a VIOLATION FOR BEING UNRECOGNISED. *** Whether a "
                "new state MEANS the data is absent is product meaning and not an Engineer's to "
                "guess (PBG-AUTH-005) — and guessing 'present' would silently admit `calm` on "
                "it. See DECLARED LIMIT 8: this is the one axis on which this instrument does "
                "NOT grow on the day the contract does, deliberately.",
            )

    # ---- THE FILLER DIAL, ITSELF DERIVED FROM THE CONTRACT ---------------------------- #
    # Every slot other than the one under test carries an admissible absent-data dial, so the
    # ONLY thing that varies across the whole matrix is the one dial under test.
    admissible = tuple(level for level in vocabulary if level != CALM)
    if not admissible:
        return check.refuse(
            "the contract's detail_level vocabulary contains nothing but 'calm', so there is no "
            "admissible level for a missing-data dial and this check would be vacuous."
        )
    fillers = {}
    for surface, schema in schemas.items():
        validator = validator_for(schema)
        # *** THE FILLER IS THE FIRST ABSENT-DATA BRANCH THAT ACTUALLY BUILDS, NEW AT `16B-FIX-2`
        # AND IT IS PART OF `FX5`. *** The superseded code took the first absent-data branch it
        # FOUND and refused (exit 3) if that one branch was unbuildable, which would have turned
        # every conditional-UNKNOWN tree into a PRECONDITION_NOT_MET with no violation code — the
        # branch would have been unreported rather than reported, and `CD-CALM-BRANCHES-006` is
        # where the auditor's prescription says it belongs. Trying the other absent-data branch
        # first costs nothing on the clean tree (UNKNOWN builds, and is still chosen), and it is
        # also what makes `DECLARED LIMIT 9`'s sentence "makes the check report
        # CD-CALM-BRANCHES-006 and exit 1" true — `CD-ASR-WO3-06` F3 measured it exiting 3
        # instead. See DECLARED LIMIT 11 (of THIS row; see the NUMBERING note).
        filler, obstacle, refusals = None, None, []
        for wanted in ABSENT_STATES:
            for label, resolved, state, ref_siblings in branches_by_surface[surface]:
                if state != wanted or resolved is None:
                    continue
                built, obstacle = _dial_from_branch(
                    schema, resolved, admissible[0], validator, ref_siblings)
                if built is not None:
                    filler = built
                    check.note(f"{surface.value} filler dial taken from branch {label} ({state})")
                    break
                refusals.append(f"{label} ({state}): {obstacle}")
            if filler is not None:
                break
        if filler is None:
            if refusals:
                return check.refuse(
                    f"the {surface.value} contract declares absent-data branches this check "
                    "cannot build a candidate for, so it cannot form a conforming envelope at "
                    "all and has nothing to measure: " + " | ".join(refusals)
                )
            return check.refuse(
                f"the {surface.value} contract's dial union declares no branch for any of the "
                f"absent-data states {list(ABSENT_STATES)}, so there is nothing for this check "
                "to assert about PID §3.2 on that surface."
            )
        fillers[surface] = filler
        check.note(f"{surface.value} filler dial derived from the contract: {filler!r}")

    # ---- THE MATRIX ------------------------------------------------------------------- #
    admitted_reference: dict = {}
    candidates_built: dict = {}
    cells = 0

    for surface in EnvelopeSurface:
        schema = schemas[surface]
        validator = validator_for(schema)
        slots = slots_by_surface[surface]
        for slot in slots:
            for branch_index, (branch_label, branch, state, ref_siblings) in enumerate(
                branches_by_surface[surface]
            ):
                if branch is None or state is None:
                    continue  # already reported as CD-CALM-BRANCHES-006, and not silently
                absent_data = state in ABSENT_STATES
                if not absent_data and state not in PRESENT_STATES:
                    continue  # unrecognised state, already reported; never assumed benign
                table = absent_table if absent_data else present_table
                for level, expectation in table:
                    dial, obstacle = _dial_from_branch(
                        schema, branch, level, validator, ref_siblings)
                    label = (f"{surface.value}/{slot}/{state}[{branch_label}]/"
                             f"{_label_for(level)}")
                    if dial is None:
                        check.asserted()
                        check.violation(
                            here, 0, "CD-CALM-BRANCHES-006",
                            f"{label}: this check could not build a candidate for this branch — "
                            f"{obstacle}. DENY BY DEFAULT: a branch that cannot be built cannot "
                            "be driven, and an undriven branch is reported as UNRECOGNISED "
                            "rather than passed over (RULE F).",
                        )
                        continue
                    candidate = _envelope(surface.value, slots, slot, dial, fillers[surface])
                    candidate["schema_version"] = ENVELOPE_SCHEMA_VERSION
                    candidates_built[(surface, slot, branch_index, _label_for(level))] = candidate
                    cells += 1

                    check.asserted()
                    try:
                        returned = refuse_unless_publishable(candidate, surface=surface)
                    except PublicationRefused as refused:
                        if expectation is MUST_ADMIT:
                            check.violation(
                                here, 0, "CD-CALM-GATE-002",
                                f"{label}: {expectation} — but the gate REFUSED it "
                                f"[{refused.reason_class}] at {refused.pointer or '<root>'}. "
                                + (
                                    "*** A VALUE dial backed by real inputs can no longer render "
                                    "as calm. PID §4 makes calm the base case — 'calm = dial + one "
                                    "line' — and a contract that cannot express it is not holding "
                                    "PID §3.2, it is enforcing silence. ***"
                                    if not absent_data and level == CALM
                                    else "This is a state the product must be able to publish. A "
                                    "guard that refuses it has not closed a hole, it has closed "
                                    "the product."
                                ),
                            )
                            continue
                        # It refused, as it must. Now: for the right reason, at the right place?
                        check.asserted(2)
                        if refused.reason_class != REFUSAL_SCHEMA_VIOLATION:
                            check.violation(
                                here, 0, "CD-CALM-REASON-003",
                                f"{label}: refused, but as {refused.reason_class} and not as "
                                f"{REFUSAL_SCHEMA_VIOLATION}. The right outcome from the wrong "
                                "layer is this project's most-repeated defect (CD-PL-F74): a "
                                "candidate refused for an unrelated malformation proves nothing "
                                "about calm.",
                            )
                        if refused.pointer != f"/{slot}":
                            check.violation(
                                here, 0, "CD-CALM-REASON-003",
                                f"{label}: refused at pointer {refused.pointer or '<root>'!r}, "
                                f"which does not name the mutated dial slot '/{slot}'. The "
                                "refusal is not located at the thing under test.",
                            )
                        check.note(
                            f"{label}: REFUSED [{refused.reason_class}] at "
                            f"{refused.pointer or '<root>'}"
                        )
                    except Exception as other:
                        check.violation(
                            here, 0, "CD-CALM-REASON-003",
                            f"{label}: the gate raised {type(other).__name__}: "
                            f"{str(other).splitlines()[0][:160]}. That is neither an admission nor "
                            "a declared refusal. A refusal that arrives as a crash is not a "
                            "refusal, and a check cannot read it as one.",
                        )
                    else:
                        if expectation is MUST_REFUSE:
                            if level is LEVEL_ABSENT:
                                what = (
                                    f"*** THE LIVE GATE ADMITTED A {state} DIAL CARRYING NO "
                                    "detail_level AT ALL. *** A missing-data dial with no level "
                                    "leaves the RENDERER to choose one, which is the second "
                                    "decision site the whole detail_level module exists to "
                                    "prevent, and `calm` is among the choices. "
                                    "tests/test_detail_level.py has asserted this refusal since "
                                    "before this instrument existed; this row exists because "
                                    "the instrument that superseded that memorial dropped it "
                                    "(CD-ASR-WO3-05 F2)."
                                )
                            elif level == OFF_VOCABULARY_LEVEL:
                                what = (
                                    f"*** THE LIVE GATE ADMITTED A {state} DIAL CARRYING "
                                    f"{level!r}, WHICH IS NOT A detail_level AT ALL. *** A "
                                    "branch that accepts an arbitrary string accepts `calm` the "
                                    "moment the enum in front of it is loosened, and a renderer "
                                    "meeting a level it does not know will fall back to one it "
                                    "does. tests/test_detail_level.py has asserted this refusal "
                                    "with this same token since before this instrument existed."
                                )
                            else:
                                what = (
                                    f"*** THE LIVE GATE ADMITTED A {state} DIAL RENDERING AS "
                                    "CALM. *** PID §3.2 is constitutional and its words are "
                                    "'Missing data must never render as calm'. With zero "
                                    "registered sources every dial reads UNKNOWN, so this is "
                                    "not an edge case — it is the only state this product can "
                                    "currently publish."
                                )
                            check.violation(
                                here, 0, "CD-CALM-GATE-001",
                                f"{label}: {what} refuse_unless_publishable returned "
                                f"{returned!r} and nothing stopped the write.",
                            )
                            continue
                        admitted_reference[(surface, slot, branch_index)] = candidate
                        check.note(f"{label}: ADMITTED")

    # ---- CD-CALM-PAIRED-004 — ONE TOKEN MOVED, OPPOSITE OUTCOME ---------------------- #
    # The refusal must be caused by the LEVEL. Diff each refused candidate against an ADMITTED
    # candidate of the SAME BRANCH at the SAME slot on the SAME surface and require exactly one
    # differing pointer, which must be the detail_level of that dial.
    #
    # *** THE FIELD-ABSENT ROW NEEDS NO EXCEPTION AND IS NOT GIVEN ONE, AND THAT IS MEASURED
    # RATHER THAN ASSUMED. *** `_differing_pointers` is a SYMMETRIC DIFFERENCE of the two
    # documents' pointer SETS followed by a value comparison of the common ones, so a candidate
    # that OMITS `/<slot>/detail_level` differs from its admitted pair at exactly that one
    # pointer — by the pointer's PRESENCE rather than by its value. The sentence "same document,
    # one token moved, opposite outcome" stays literally true; what moved is the token's
    # existence. STATED, because the auditor's prescription and this increment's dispatch both
    # expected a stated exception to be necessary here and MEASUREMENT SAYS IT IS NOT.
    for surface in EnvelopeSurface:
        for slot in slots_by_surface[surface]:
            for branch_index, (branch_label, branch, state, ref_siblings) in enumerate(
                branches_by_surface[surface]
            ):
                if branch is None or state is None:
                    continue
                absent_data = state in ABSENT_STATES
                if not absent_data and state not in PRESENT_STATES:
                    continue
                for level, expectation in (absent_table if absent_data else present_table):
                    if expectation is not MUST_REFUSE:
                        continue
                    reference = admitted_reference.get((surface, slot, branch_index))
                    label = (f"{surface.value}/{slot}/{state}[{branch_label}]/"
                             f"{_label_for(level)}")
                    check.asserted()
                    if reference is None:
                        check.violation(
                            here, 0, "CD-CALM-PAIRED-004",
                            f"{label}: NO ADMITTED CANDIDATE of the same branch exists to pair "
                            "the refusal against, so the refusal cannot be attributed to the "
                            f"level rather than to the {state} shape itself. If every {state} "
                            "dial is refused whatever it carries, this arm is vacuous — which "
                            "is exactly what this assertion exists to detect.",
                        )
                        continue
                    refused_candidate = candidates_built.get(
                        (surface, slot, branch_index, _label_for(level))
                    )
                    if refused_candidate is None:
                        check.violation(
                            here, 0, "CD-CALM-PAIRED-004",
                            f"{label}: the refused candidate was never built, so there is "
                            "nothing to pair. Already reported as CD-CALM-BRANCHES-006; "
                            "recorded here too rather than passed over.",
                        )
                        continue
                    differing = _differing_pointers(refused_candidate, reference)
                    if differing != [f"/{slot}/{DETAIL_LEVEL}"]:
                        check.violation(
                            here, 0, "CD-CALM-PAIRED-004",
                            f"{label}: the refused candidate and its admitted pair differ at "
                            f"{differing!r}, not at exactly ['/{slot}/{DETAIL_LEVEL}']. The two "
                            "documents must be identical apart from the one token under test, "
                            "or the opposite outcomes cannot be attributed to it.",
                        )
                    else:
                        check.note(
                            f"{label}: PAIRED against "
                            f"{reference[slot].get(DETAIL_LEVEL)!r} — sole difference "
                            f"/{slot}/{DETAIL_LEVEL}"
                            + (" (present in the admitted pair, ABSENT in the refused "
                               "candidate)" if level is LEVEL_ABSENT else "")
                        )

    # ---- CD-CALM-PRODUCER-005 — THE PRODUCT CANNOT FORM THE INTENT EITHER ------------ #
    # The contract half above is what the gate refuses to ACCEPT. This is what the product
    # refuses to PRODUCE. Both arms, refusing and admitting, because a constructor that refused
    # every policy would be vacuous in the same way a contract that refuses everything is.
    check.asserted()
    try:
        policy = DetailPolicy(elevated_at=0.4, acute_at=0.8, absent_data_level=CALM)
    except DetailPolicyIncoherent as refused:
        check.note(f"PRODUCER: DetailPolicy(absent_data_level='calm') REFUSED "
                   f"{type(refused).__name__}")
    except Exception as other:
        check.violation(
            here, 0, "CD-CALM-PRODUCER-005",
            f"DetailPolicy(absent_data_level='calm') raised {type(other).__name__} and not "
            "the declared DetailPolicyIncoherent (CD-PL-F74).",
        )
    else:
        check.violation(
            here, 0, "CD-CALM-PRODUCER-005",
            "DetailPolicy(absent_data_level='calm') was CONSTRUCTED. The product can now form "
            f"a policy that renders missing data as calm; it returned {policy!r}.",
        )

    absent_levels = tuple(level for level in vocabulary if level != CALM)
    if not absent_levels:
        return check.refuse(
            "the vocabulary contains no level other than 'calm', so the admitting arm of "
            "CD-CALM-PRODUCER-005 cannot be driven and this check would be vacuous."
        )
    for level in absent_levels:
        check.asserted(2)
        try:
            policy = DetailPolicy(elevated_at=0.4, acute_at=0.8, absent_data_level=level)
        except Exception as exc:
            check.violation(
                here, 0, "CD-CALM-PRODUCER-005",
                f"DetailPolicy(absent_data_level={level!r}) was REFUSED "
                f"({type(exc).__name__}: {str(exc).splitlines()[0][:120]}). A constructor that "
                "refuses every policy is vacuous, and the product would have no level left to "
                "render an absence with.",
            )
            continue
        try:
            produced = detail_level_for(
                Unknown(reason="NO_SOURCE_REGISTERED", since_utc=NOW, missing_inputs=()),
                dial_slot=DIAL_IDS[0],
                policy=policy,
            )
        except Exception as exc:
            check.violation(
                here, 0, "CD-CALM-PRODUCER-005",
                f"detail_level_for(Unknown, policy.absent_data_level={level!r}) raised "
                f"{type(exc).__name__}: {str(exc).splitlines()[0][:160]}.",
            )
            continue
        if produced == CALM or produced != level:
            check.violation(
                here, 0, "CD-CALM-PRODUCER-005",
                f"detail_level_for(Unknown) returned {produced!r} for a policy whose "
                f"absent_data_level is {level!r}. The level an absence renders with must be "
                "the policy's absent level and must never be 'calm'.",
            )
        else:
            check.note(f"PRODUCER: detail_level_for(Unknown) -> {produced!r} (policy {level!r})")

    check.note(
        "DECLARED LIMIT, PRINTED AT EVERY RUN: this check drives the ABSENCE half of CD-AC-001 "
        "only. It says nothing about staleness, nothing about a fabricated VALUE that should "
        "have been an absence, and it does not prevent $CD_CONTRACTS_DIR being pointed at a "
        "widened copy of the contracts — it refuses to run when it is. It is ONE OF THREE "
        "guards on CD-AC-001 and never a sole guard."
    )

    return check.done(
        f"{cells} gate cells ({len(list(EnvelopeSurface))} surfaces x dial slots x "
        f"dial_reading.oneOf branches x {len(absent_table)} absent-data / "
        f"{len(present_table)} present-data level rows) driven in-process through "
        f"refuse_unless_publishable against {package_dir}, plus the union's branch set, the "
        "dial-bearing root-property set and the producer arms"
    )


if __name__ == "__main__":
    raise SystemExit(main())
