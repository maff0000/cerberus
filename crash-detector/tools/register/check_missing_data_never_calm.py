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

 CD-CALM-ROOT-008     **AND THE ROOT IS A CLOSED PARTITION OVER A FINITE SET, NOT AN OPEN SPACE
                      WITH A RECOGNISER IN IT — `RULE CC`.** *** NEW AT `16B-CONTRACT-CLOSURE`
                      (`CC-1`), AND IT IS THE ARCHITECTURAL CLOSE `PO-DECISIONS-0028` RULING 1
                      ORDERED. *** Every property of an envelope contract's root `properties` is
                      **EXACTLY ONE** of **(a)** a CANONICAL DIAL SLOT, spelled literally
                      `{"$ref": "#/$defs/dial_reading"}`, that one key and no sibling keyword; or
                      **(b)** a DECLARED NON-DIAL PROPERTY, whose name is on the finite written
                      allowlist :data:`NON_DIAL_ROOT_PROPERTIES` **and** which is AFFIRMATIVELY
                      PROVED, by driving the LIVE GATE with a calm-carrying object in its place,
                      to be incapable of carrying a `detail_level`. **ANYTHING ELSE IS A
                      VIOLATION. NO RECOGNISER IS CONSULTED. THERE IS NO THIRD CASE AND NO
                      SILENCE.**
                      **WHY THIS CLOSES WHAT `CD-CALM-SLOTS-007` COULD NOT.** That check compares
                      `dial_bearing` (the recogniser's output) against `found` (literal `$ref`
                      slots), so **a root property the recogniser answers `False` about is in
                      NEITHER SET, the comparison is satisfied, and the slot is INVISIBLE.** That
                      is the hole `CD-ASR-WO3-10` proved unclosable by any list: `A310-F2` (the
                      discriminator spelled `status`), `A310-F3` (`present: false` with a stale
                      stamp) and `A310-F1` (a nest past the depth cap) are all root properties the
                      recogniser cannot see. **THEY ARE NOT CLOSED BY `RULE CC` — THEY ARE
                      UNREACHABLE**, because none of them is limb (a) or limb (b).
                      **THE TWO PREMISES OF EXHAUSTIVENESS ARE ASSERTED AND NOT ASSUMED:** the
                      root declares `additionalProperties: false`, so a document cannot introduce
                      a root key the contract does not declare; and the root declares no keyword
                      outside :data:`_ROOT_STRUCTURAL_KEYWORDS`, so nothing else at the root can
                      introduce or constrain a property this enumeration does not see. **AN
                      UNASSERTED PREMISE IS EXACTLY HOW `DECLARED LIMIT 4` CAME TO CLAIM "UNDER
                      ANY SPELLING" THREE TIMES RUNNING.** See `DECLARED LIMIT 17`.
                      *** AND SINCE `16D-GATE-FRESHNESS` LIMB (b) IS STRUCTURAL AS WELL AS
                      BEHAVIOURAL (closing `CD-ASR-WO3-11`'s `A311-F1`). *** Limb (b)'s
                      affirmative proof was a SAMPLE OF TWO PROBE SHAPES, and a third shape
                      defeated it: arm `H` widened the allowlisted root property
                      `degraded_inputs` to an **ARRAY of closed objects** carrying
                      `#/$defs/detail_level` — ONE CONTAINER DEEPER than this row's own arm
                      `CC-H` — on which both probes are still refused, this instrument still
                      reported `PASS — 243`, the whole thirty-line register was unmoved, and the
                      LIVE GATE ADMITTED the list of DEGRADED inputs rendering as CALM at a root
                      position on BOTH surfaces. **THE REMEDY IS NOT A THIRD PROBE** — that moves
                      the census game to the probe alphabet. Each allowlisted name is now also put
                      to :func:`_can_carry_detail_level`, a DECISION PROCEDURE over the property's
                      OWN CLOSED SUBSCHEMA: capable, or UNDECIDABLE, are BOTH violations. **THE
                      PROBES ARE RETAINED AS THE PAIRED BEHAVIOURAL CONTROL** — structure says
                      what the contract ADMITS, the probes say what the gate DOES, and a
                      disagreement between them is itself a finding. See `DECLARED LIMIT 18`,
                      which states this half's own residue at equal length.

 CD-CALM-CANON-009    **AND THE DISCRIMINATOR IS AT ONE CANONICAL PATH, MANDATED BY THE CONTRACT
                      AND ASSERTED HERE.** *** NEW AT `16B-CONTRACT-CLOSURE` (`CC-2`). *** Inside
                      `#/$defs/dial_reading` the canonical path is `properties.state`, at depth
                      ONE, pinned per branch at `properties.state.const`. Both contracts now
                      declare `"required": ["state"]` on the union and carry a normative `RULE CC`
                      clause in their `description`. This asserts, per surface, counted: the union
                      is `additionalProperties: false`, declares `properties.state` and REQUIRES
                      `state`; **every** branch is `additionalProperties: false`, REQUIRES `state`,
                      and declares `properties.state.const` as a STRING; and **every** branch
                      REQUIRES at least one property typed `#/$defs/utc_timestamp` — the freshness
                      stamp, asserted by TYPE and never by NAME, because `VALUE`/`DEGRADED` require
                      `as_of_utc` while `UNKNOWN` requires `since_utc`. **A BRANCH THAT REQUIRES NO
                      TIMESTAMP CANNOT PROVE FRESHNESS AND IS A VIOLATION**, and the ABSENCE of the
                      canonical path is its OWN named violation rather than folded into
                      `CD-CALM-BRANCHES-006`, which reports a recognition failure and would read as
                      the wrong sentence.
                      *** A `description` IS NOT AN ENFORCEMENT POINT AND THIS CONTRACT ALREADY
                      CARRIES A SUPERSEDED NOTE SAYING SO IN ITS OWN WORDS *** —
                      `absent_data_detail_level`'s description records 16A, where the guarantee was
                      *"asserted only in PROSE"* while the gate admitted a calm `UNKNOWN` dial on
                      both surfaces. **THE PROSE STATES THE MANDATE; THIS ROW AND THE NEXT ENFORCE
                      IT.**

 CD-CALM-FRESH-010    **AND `calm` IS UNREPRESENTABLE ON ANY BRANCH THAT HAS NOT AFFIRMATIVELY
                      PROVED PRESENT-AND-FRESH.** *** NEW AT `16B-CONTRACT-CLOSURE` (`CC-3`), AND
                      IT IS `PO-DECISIONS-0027` RULING 5 MADE ACHIEVABLE, WHICH IS WHAT
                      `PO-DECISIONS-0028` RULING 2 ORDERED. *** A branch may reference the
                      calm-bearing `#/$defs/detail_level` **IF AND ONLY IF** its
                      `properties.state.const` is a member of :data:`PRESENT_STATES` **and** it
                      requires a freshness stamp. **EVERY OTHER BRANCH MUST reference a vocabulary
                      from which `calm` is ABSENT.**
                      **THAT IS THE AFFIRMATIVE FORM, AND IT IS WHY THIS IS NOT A DENYLIST.** It
                      does not ask *"is this state on my list of bad ones?"* — the question nine
                      audits defeated by naming a state nobody had listed. It asks *"has this
                      branch PROVED present-and-fresh?"*, and a branch that has not gets a
                      vocabulary in which `calm` cannot be written. **A never-before-named state
                      must arrive as a NEW BRANCH; a new branch's state is NOT in `PRESENT_STATES`;
                      therefore it CANNOT CARRY `calm` — BY CONSTRUCTION, OVER A CLOSED SET, AND
                      NOT BY RECOGNITION OVER AN OPEN ONE.** The vocabulary is judged by its VALUES
                      and never by the name of the `$def` it comes from (`CD-PL-F169`,
                      `CD-ASR-WO3-02` F06/F07: a check that reads the `$ref` target NAME passes a
                      tree where `calm` was put back inside the target's own enum).
                      **THE VACUITY DIRECTION IS ASSERTED TOO AND CARRIES EQUAL WEIGHT:** a branch
                      that HAS proved present-and-fresh and CANNOT carry `calm` is also a
                      violation, because PID §4 makes `calm` the base case and a contract that
                      cannot express it is enforcing silence rather than holding PID §3.2.

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

      (c) *** SUPERSEDED AGAIN AT `16B-FIX-4` — (a)'s OWN REPLACEMENT SENTENCE WAS FALSE IN THE
      SAME WAY AS THE ONE IT REPLACED, AND `CD-ASR-WO3-08` (F3) MEASURED IT. *** The word doing
      the damage was **ANY**. `FX10` corrected the SHAPE axis and then re-committed the identical
      over-generalisation on the DECLARATION-KEYWORD axis: a `state` declared under
      `patternProperties`, introduced by `dependentSchemas`, reached by `$dynamicRef`, or reached
      past thirty-two `$ref` hops was classified **not a dial** and was SILENT — four root
      properties that DECLARE a property named `state` and on which the check did not fire.
      **WHAT IS TRUE AT `16B-FIX-4` (`FX12`), AND IT IS TWO SENTENCES BECAUSE IT IS TWO LIMBS:**
      this check fires on any root property that declares a property named `state` under
      `properties`, `required` or `dependentRequired` — the keywords whose property NAMES it
      reads — whatever that property MEANS and whatever its subschema's shape; **AND** it fires on
      any root property, dial or not, whose shape it cannot fully read (`DECLARED LIMIT 14`). The
      four spellings above now reach the second limb, and so does a fifth nobody in the chain had
      named (arm `C27`) — not because they are listed, but because they are not readable.

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
    `{"a": ...}`. **A merge can therefore admit documents THE NODE AS WRITTEN REFUSES — it can
    only ever WEAKEN this instrument, silently, which is the exact failure class F1 is.**
    Deny-by-default cannot weaken it; it can only over-report. **THE COST, PRICED:** a contract that legitimately
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

    *** SUPERSEDED AT `16B-FIX-4` ON ONE SENTENCE, STATED AND NOT ERASED (`CD-RULE-004`,
    `PBG-CONT-003`) — `FX14`, `CD-ASR-WO3-08` F4. THE RULING AND THE BEHAVIOUR ARE UNCHANGED. ***
    WHAT THIS LIMIT SAID, VERBATIM, IN ALL THREE PLACES: *"A merge can therefore admit documents
    NEITHER schema admits."* **THAT IS FALSE, AND NOT MERELY UNMEASURED.** MEASURED BY THIS SEAT
    (`CD-ENG-WO3-09`) WITH THE GATE'S OWN LIBRARY, `jsonschema 4.10.3`,
    `Draft202012Validator`, over SIX sibling keyword sets x NINE documents x BOTH merge directions
    = 108 combinations: `MERGE ADMITS WHAT THE NODE AS WRITTEN REFUSES -> 11 hits`;
    `MERGE ADMITS WHAT NEITHER SCHEMA OBJECT ADMITS -> 0 hits`. AND IT IS NOT A SEARCH GAP: under
    `{**target, **sibling}` every SIBLING key survives into the merged object, so
    `sibling(D) = False` forces `merged(D) = False`, and symmetrically for the other direction —
    **a document the merge admits is ALWAYS admitted by at least one of the two, so the clause
    describes an empty set.** `CD-ASR-WO3-08` measured 10 hits over its own set and 0 for the
    false clause; this is an independent re-measurement, not a relay, and the two agree.
    **WHAT IS TRUE INSTEAD, AND IT CARRIES THE WHOLE CONCLUSION: a merge can admit documents THE
    NODE AS WRITTEN REFUSES.** The node as written is a CONJUNCTION; the merge is not; the merge
    is therefore `>=` the conjunction and can only WEAKEN this instrument. That is strictly
    weaker to prove, it is what was measured, and the decision to deny rather than merge rests on
    it entirely. **THE FALSE CLAUSE BOUGHT NOTHING.** *** THIS IS THE THIRD SENTENCE ON THIS ROW
    TO BE SUPERSEDED FOR OVERSTATING IN THE SAME DIRECTION AS THE SENTENCE IT REPLACED (`DECLARED
    LIMIT 10`, then `12`(a), now `13`). THE PATTERN IS RECORDED BECAUSE IT IS THE PATTERN AND NOT
    THE INSTANCE THAT IS THE DEFECT: on this row, a replacement sentence has three times been
    written to the widest claim its author believed rather than to the narrowest claim their
    evidence carried. `DECLARED LIMIT 14` IS WRITTEN TO WHAT WAS MEASURED AND ITS COST COLUMN IS
    A MEASUREMENT AND NOT AN ESTIMATE. ***

 14 **A ROOT PROPERTY THIS CHECK CANNOT FULLY READ IS UNDECIDABLE, NOT "NOT A DIAL" — THE DEFAULT
    IS INVERTED AT THE RECOGNISER.** *** NEW AT `16B-FIX-4` (`FX12`, closing `CD-ASR-WO3-08` F1
    AS A CLASS, and F2 and F5 with it). *** **WHAT "CANNOT FULLY READ" MEANS HERE, PRECISELY, AND
    IT IS A PROPERTY OF THE NODE AND NOT OF A LIST OF ATTACKS.** :func:`_dial_bearing` may return
    `False` about a node only when EVERY KEYWORD THE NODE ACTUALLY DECLARES, at every node the
    walk visited, is in :data:`_READABLE_KEYWORDS`, which is the union of exactly three declared,
    closed sets and nothing else:

      * :data:`_SUBSCHEMA_KEYWORDS` minus :data:`_NAME_BEARING_APPLICATORS` — keywords carrying
        subschemas that the walk DESCENDS INTO, so it has looked underneath every one of them;
      * :data:`_NAME_DECLARING_KEYWORDS` (`properties`, `required`, `dependentRequired`) —
        keywords whose keys or entries are LITERAL property names, which this check reads;
      * :data:`_INERT_KEYWORDS` — the remaining 2020-12 keywords that carry no subschema and name
        no property, enumerated from the specification's own vocabularies.

    **EVERYTHING ELSE IS UNREADABLE AND MAKES THE NODE UNDECIDABLE.** That includes
    `patternProperties`, `propertyNames` and `dependentSchemas` (descended into, so a dial under
    one can still come back `True`, but their KEYS are names this check does not evaluate — a
    regex, a constraint, a trigger property), `$id`, `$dynamicRef`, `$dynamicAnchor`,
    `$recursiveRef`, any keyword of a private vocabulary, any keyword of a draft not yet written,
    and any misspelling of a keyword that does exist. :func:`_resolve` reaching
    :data:`REF_CHAIN_CAP` is the same answer for the same reason.

    *** WHY DENY-BY-DEFAULT AND NOT A LIST, AND THIS IS THE WHOLE POINT OF THE INCREMENT. *** The
    superseded walk asked a list of keywords IT HAD THOUGHT OF whether they were present, so a
    keyword it had not thought of was invisible and the node fell through to `False`. **THAT IS
    WHY THIS RECOGNISER WAS ESCAPED FOUR TIMES BY FOUR SPELLINGS OF ONE IDEA** — `A306` a new
    state vocabulary, `A307` a boolean `state`, `A308` `patternProperties` / `dependentSchemas` /
    `$dynamicRef` / a chain past the cap — **and why each fix closed the spelling it was shown and
    the next auditor found another** (`PO-DECISIONS-0026` ruling 10,
    `GUARD_THE_INSTANCE_NOT_THE_CLASS`). Asking the NODE instead of the list means the deny class
    is the COMPLEMENT of a finite written set, which no future spelling can leave.
    **THE FALSIFIER WAS BUILT AND RUN RATHER THAN ARGUED:** arm `C27` is a fifth spelling none of
    the four audits used — `propertyDependencies`, an applicator proposed for the draft AFTER
    2020-12 — which appears ZERO times in this file (`grep -c propertyDependencies` -> `0`) and
    which was a live escape on the superseded instrument (`PASS — 144 assertions, 0 violations`
    with the gate ADMITTING `{state: STALE, reason: FEED_DEAD, detail_level: 'calm'}` on BOTH
    surfaces) and is `FAIL — 2` `CD-CALM-SLOTS-007` here. Three more never-named spellings behave
    identically: a private `x-` vendor keyword, an invented `slotShape`, and **`propertys` — a
    ONE-LETTER TYPO of `properties`, which is the likeliest real-world author error of all and
    was silent before this fix.**

    **THE COST, MEASURED AND NOT ESTIMATED — THE FALSE-POSITIVE TAIL IS REAL AND IT IS PRICED.**
    EIGHT benign root properties, none of them a dial, none declaring a `state` subschema, each
    added to both contracts on its own pristine extraction: SIX turn this instrument RED that were
    green before — a `patternProperties` metrics bag, a `propertyNames`-constrained map, a benign
    `dependentSchemas` pair, a subschema carrying its own `$id`, **a property carrying a custom
    `x-` annotation**, and an object whose `required` names `state` without giving it a subschema.
    TWO benign controls stay green — a plain closed object and an array of strings — so the tail
    is a tail and not a blanket. **THE CLEAN TREE IS UNAFFECTED AND THAT IS THE MEASUREMENT THAT
    MATTERED MOST:** `PASS — 144 assertions, 0 violations`, exit 0, and the instrument's FULL
    output on the clean tree is byte-identical before and after this fix but for the absolute path
    string. `C1`–`C21` are unchanged, every one. **THE RULED DIRECTION IS THE ONE TAKEN:** a false
    positive costs one seat one look at one contract; a false negative costs the constitution.
    **THE REMEDY WHEN THE TAIL BITES IS NEVER TO LOOSEN THE GUARD:** a keyword that is genuinely
    inert here belongs in :data:`_INERT_KEYWORDS` with the reason written down, and a keyword that
    carries a subschema belongs in :data:`_SUBSCHEMA_KEYWORDS` so the walk descends it. Both are
    edits a reader can audit; neither is a silent `False`.

    **WHAT THIS DOES NOT CLOSE, SAID PLAINLY.** It does not close `DECLARED LIMIT 12`'s residue —
    a dial that discriminates on a differently-NAMED key is still `False` and still silent, and
    that limit is judged honestly drawn and stands as a condition on 16C's dispatch. **AND A ROOT
    PROPERTY THAT DECLARES NOTHING AT ALL — `{"type": "object"}` — IS STILL `False`**: every
    keyword it declares is readable, so it is read, and there is no `state` in it. That is not the
    class this fix bounds, and it is named here rather than left for the next audit to find.
    **NOT PROVED TO BE CARRIED ANYWHERE:** nothing outside this instrument reads
    :data:`_READABLE_KEYWORDS`.

    *** SUPERSEDED AT `16B-FIX-5` ON ITS COST COLUMN, STATED AND NOT ERASED (`CD-RULE-004`,
    `PBG-CONT-003`) — `FX17`, `CD-ASR-WO3-09` F5. THE RULING AND THE BEHAVIOUR ARE UNCHANGED. ***
    **WHAT THE COST COLUMN SAID, IN ALL THREE PLACES:** *"EIGHT benign root properties ... SIX turn
    this instrument RED ... TWO benign controls stay green."* **THAT IS A SAMPLE DESCRIBED AS A
    MEASUREMENT.** The auditor found a SEVENTH red shape in about a minute — a `contentSchema`
    carrying a `state` — and it is named by nothing in the list of six. **AND THE SENTENCE DIRECTLY
    ABOVE IT PROMISED THE OPPOSITE:** `DECLARED LIMIT 13`'s supersession ends *"DECLARED LIMIT 14
    IS WRITTEN TO WHAT WAS MEASURED AND ITS COST COLUMN IS A MEASUREMENT AND NOT AN ESTIMATE"*, and
    the cost column then enumerated six INSTANCES of a CLASS, in a file whose entire thesis is
    GUARD THE CLASS AND NOT THE INSTANCE. **THAT IS THE SAME ERROR THE CODE HAD JUST FIXED, WRITTEN
    IN PROSE**, and it is the fourth sentence on this row superseded for overstating in the same
    direction as the sentence it replaced (`10`, then `12`(a), then `13`, now `14`'s cost column).

    *** THE TAIL IS A CLASS, AND THIS IS THE CLASS. *** A root property is UNDECIDABLE — and
    therefore `CD-CALM-SLOTS-007`, whether or not it is a dial — **exactly when, at some node the
    walk visits, at least one of these three holds**:

      (a) **AN UNREADABLE KEYWORD.** The node declares a keyword outside
          :data:`_READABLE_KEYWORDS`: every 2020-12 keyword that list omits, every keyword of a
          draft not yet written, every private or vendor keyword, and every misspelling of every
          keyword. **AN INFINITE SET BY CONSTRUCTION, WHICH IS THE POINT.**
      (b) **A `state` IT CANNOT CLASSIFY.** The node NAMES a property called `state` — in any
          position :func:`_declared_names` reads — and does not give it a `const`/`enum` that
          intersects :data:`DECLARED_STATES`.
      (c) **A WALK THAT DID NOT COMPLETE.** A `$ref` that does not resolve, a chain past
          :data:`REF_CHAIN_CAP`, an ASSERTING sibling of a `$ref`, or nesting past the depth cap.

    **THOSE THREE ARE THE ONLY LIMBS IN THE FUNCTION THAT SET `undecidable` OR RETURN `None`, SO
    THE TAIL HAS NO OTHER MEMBERS.** That is a property of the code, checkable by reading it. The
    shapes below are EXAMPLES OF THAT CLASS AND ARE EXPLICITLY NON-EXHAUSTIVE.

    **THE EXAMPLES, RE-MEASURED AT `16B-FIX-5` OVER TWENTY-ONE PROBES PUT DIRECTLY TO
    :func:`_dial_bearing`, NONE OF THEM A DIAL.** **ELEVEN RED:** a `patternProperties` metrics bag
    · a `propertyNames`-constrained map · a benign `dependentSchemas` pair · a subschema carrying
    its own `$id` · an ordinary `x-` vendor annotation · an object whose `required` names `state`
    without a subschema · a `contentSchema` carrying a `state` (the auditor's seventh) · **and the
    FOUR the alphabet correction adds — an `enum` of objects naming `state` (an ordinary workflow
    status, not a dial), an object `const` naming `state`, an `enum` member with a `state` nested
    two levels inside it, and a `dependentRequired` KEY named `state`.** **TEN GREEN:** a scalar
    string `enum` · a scalar `const` · a numeric `enum` · a plain closed object · an `enum` of
    objects naming NO `state` · an object `const` naming NO `state` · a `default` annotation
    carrying a whole dead-feed reading · an `examples` annotation carrying one · arm `C16`'s benign
    optional root object. The twenty-first probe is the real dial slot spelling and comes back
    `True`, which is the arm that stops this probe set being one-sided.

    *** HOW FAR THE ALPHABET CORRECTION MOVED THE TAIL, IN NUMBERS, BECAUSE THE DISPATCH ASKED. ***
    Over that same twenty-one-probe set: `dd40407` -> **7 red / 13 green**; `16B-FIX-5` -> **11 red
    / 9 green**. **THE FOUR THAT MOVED ARE EXACTLY LIMB (b)'s NEW MEMBERS AND NOTHING ELSE MOVED.**
    Every probe that does not NAME a property called `state` is unchanged — including both
    annotation probes, which is the MEASURED form of the claim that `default` and `examples` assert
    nothing. **THE CLEAN TREE DID NOT MOVE** (`PASS — 144 assertions, 0 violations`, exit 0), **NOR
    DID ANY OF `C1`–`C28`**, and neither envelope contract carries an object-valued or
    array-valued `enum`/`const` anywhere, which is why.

    **THE RULED DIRECTION IS THE ONE TAKEN, AND THE REMEDY WHEN THE TAIL BITES IS NEVER TO LOOSEN
    THE GUARD:** a false positive costs one seat one look at one contract; a false negative costs
    the constitution. A keyword genuinely inert here belongs in :data:`_INERT_KEYWORDS` with the
    reason written down; a keyword that carries a subschema belongs in
    :data:`_SUBSCHEMA_KEYWORDS`; a property that means something other than a dial state and is
    called `state` is renamed, or the addition goes to the Product Authority. All three are edits a
    reader can audit. None is a silent `False`.

 15 **THE ALPHABET — WHERE A PROPERTY NAME MAY BE WRITTEN, AND HOW DEEP THIS CHECK LOOKS FOR ONE.**
    *** NEW AT `16B-FIX-5` (`FX15`, closing `CD-ASR-WO3-09` F1 — THE ONLY THING FOUND WRONG WITH
    `FX12`). *** `DECLARED LIMIT 14`'s inversion is a TRUE universal quantification and its
    falsifier passed — **but over KEYWORD NAMES only.** It never asked what a READABLE keyword's
    VALUE asserts; `enum` and `const` take INSTANCE VALUES; an object instance value NAMES
    PROPERTIES. So `{"enum": [<a LIVE reading>, <a STALE reading whose detail_level is "calm">]}`
    was fully read, named no `state` as far as the walk could see, and came back a clean `False` —
    NOT A DIAL — with this instrument reporting `PASS — 144 assertions, 0 violations` while the
    live gate ADMITTED a dead feed rendering as `calm` on BOTH surfaces. **THE QUANTIFIER WAS
    RIGHT; THE ALPHABET WAS WRONG.**

    **WHAT IS READ NOW, AND THE LIST IS AGAINST THE SPECIFICATION AND NOT AGAINST THE ATTACKS.** A
    property name can appear in a 2020-12 schema in exactly these positions: `properties` keys ·
    `required` members · `dependentRequired` KEYS **and** values · the property names inside `enum`
    members and inside a `const` value · `patternProperties` keys, `propertyNames` and
    `dependentSchemas` keys (**NOT read — they are in :data:`_NAME_BEARING_APPLICATORS`, so the
    node is UNDECIDABLE before the question is asked**) · `default` and `examples` (**NOT read, and
    deliberately: they are ANNOTATIONS, they assert nothing, and a `state` named inside one
    constrains no document and can admit none. `enum` and `const` ASSERT. That is the whole
    distinction and it is the auditor's**).

    *** `enum` AND `const` STAY IN :data:`_INERT_KEYWORDS`, AND THAT IS A PROHIBITION AND NOT A
    PREFERENCE. *** They carry no SUBSCHEMA, so there is nothing under them to descend into, and
    the auditor MEASURED that making them UNREADABLE turns every ordinary
    `{"type": "string", "enum": [...]}` root property UNDECIDABLE and explodes the tail. **The
    VALUE is read; the KEYWORD stays inert.**

    **DECISION 1 — DEPTH, DECLARED AND PRICED.** An `enum` member is arbitrary JSON and may nest.
    This walk collects names **at every depth of the value, through objects and arrays alike**,
    capped at :data:`INSTANCE_WALK_CAP`. The alternative — the top-level keys of each member only —
    would have closed the shape the auditor wrote and left `{"enum": [{"reading": {"state": ...}}]}`
    open, **which is this row's entire history**. **THE PRICE IS A WIDER FALSE-POSITIVE CLASS:** any
    node whose `enum` or `const` value contains, ANYWHERE inside it, an object with a key called
    `state`. It is `DECLARED LIMIT 14`'s limb (b), it is measured there, and it moved the tail by
    exactly four probes out of twenty-one.

    *** ITS CAP SENTENCE WAS FALSE, AND IT WAS FALSE IN THE ONE DIRECTION THAT MATTERS.
    SUPERSEDED AT `16B-CONTRACT-CLOSURE` (`CC-4`, closing `CD-ASR-WO3-10` `A310-F1`), STATED AND
    NOT ERASED (`CD-RULE-004`, `PBG-CONT-003`). ***

      WHAT THIS LIMIT SAID, VERBATIM, UNDER THE HEADING **"REACHING THE CAP IS NOT A SILENT
      SUCCESS"**: *"the walk returns `INSTANCE_TOO_DEEP`, a sentinel no contract can declare as a
      property name, so it enters the declared set, can never equal `state`, and can never make
      the node `True`."*

      **EVERY CLAUSE OF THAT SENTENCE IS TRUE AND THE HEADING IT SITS UNDER WAS FALSE.** The
      sentence is about `True`; the heading is about SILENCE; and the answer that makes a heading
      about silence true is `None`. The sentinel had **ZERO EXECUTABLE CONSUMERS** — `declared`'s
      only reader was `"state" in declared`, which a sentinel can never satisfy — so reaching the
      cap set nothing, and the node returned **a clean `False`, which this file's own docstring
      calls THE ONLY SILENT ANSWER IT HAS.** `_dial_bearing`'s own depth cap returns `None`; this
      one copied the NUMBER and not the FAIL-CLOSED HANDLING, and its docstring claimed *"reaching
      it is handled the same way"*. **MEASURED BY `CD-ASR-WO3-10`, RE-MEASURED BY THE PROJECT LEAD,
      AND RE-MEASURED INDEPENDENTLY BY THIS SEAT BEFORE CHANGING A LINE — ONE INTEGER APART:** a
      `state` nested inside an `enum` member at depth 24 -> `None`; at depth 25 -> `False`.

      **WHAT IS TRUE INSTEAD (`CC-4`), AND IT IS ONE LINE OF CODE AND ONE MEASUREMENT.**
      :func:`_dial_bearing` now tests for :data:`INSTANCE_TOO_DEEP` in the declared set and sets
      `undecidable = True` on it, which is `DECLARED LIMIT 14` limb (c) — **a walk that did not
      complete** — reached by the position it was always meant to reach. **REACHING THE CAP IS NOW
      UNDECIDABLE AND REPORTED, WHICH IS WHAT THE HEADING ALWAYS CLAIMED.** MEASURED AT THIS
      COMMIT: depths 1, 5, 20, 22, 23 and 24 -> `None`, **UNCHANGED**; depths 25, 26, 30 and 40 ->
      `None`, **MOVED FROM `False`**. The clean tree is unmoved at `PASS — 144 assertions, 0
      violations` for this item alone, because neither contract nests an `enum`/`const` value at
      all. **THE COST IS ONE MORE MEMBER OF THE FALSE-POSITIVE TAIL** — a node whose `enum` or
      `const` value nests deeper than twenty-four levels is now UNDECIDABLE whatever is in it —
      and it is the ruled direction. **`CC-1`'s Rule CC makes a nest this deep UNREACHABLE at the
      root, so this fix guards a position that is now closed by construction; it is made anyway,
      because a cap that fails open is a defect whether or not anything reaches it, and because
      `DECLARED LIMIT 14`'s limb (c) is a claim about this function that was not true until now.**

    **DECISION 2 — `const`, SAID EXPLICITLY RATHER THAN LEFT TO BE INFERRED.** **A `const` THAT IS
    NOT AN OBJECT OR AN ARRAY NAMES NOTHING.** `{"const": "equity_crash"}` and
    `{"type": "string", "enum": ["a", "b"]}` contribute the EMPTY SET and are still answered
    `False` — measured, and it is why the tail did not explode. Only the KEYS of object instance
    values are collected, so `{"enum": ["state", "detail_level"]}` — an ordinary string enum whose
    members happen to be those words — names nothing either.

    **AND ONE POSITION NOBODY ATTACKED, FIXED ANYWAY: the KEYS of `dependentRequired`.** A key
    there NAMES a property as literally as a member of its value list does —
    `{"dependentRequired": {"state": ["reason"]}}` says *if `state` is present then `reason` must
    be* — and the superseded code read the values and not the keys, so that node answered a clean
    `False` while admitting `{"state": "STALE", "detail_level": "calm"}`. **MEASURED AS A LIVE
    ESCAPE AT `dd40407` AND CLOSED HERE** (arm `C34`, `PASS — 144` before, `FAIL — 2` after, with
    the live gate ADMITTING the calm-carrying document on both surfaces at `dd40407`). **The point
    of an alphabet correction is to be COMPLETE, not to close the shape it was shown.**

    **WHY WIDENING THE ALPHABET IS SAFE WITHOUT RE-AUDITING EVERYTHING DOWNSTREAM.** The only
    consumer of :func:`_declared_names` is the test `"state" in declared`, and the limb that test
    guards sets `undecidable = True`. **MORE NAMES CAN THEREFORE ONLY EVER PRODUCE MORE UNDECIDABLE
    AND NEVER MORE `False`** — the widening is monotone in the safe direction.

    **WHAT THIS DOES NOT CLOSE, SAID PLAINLY.** It reads the NAME `state`. A dial that discriminates
    on a DIFFERENTLY-NAMED key is `DECLARED LIMIT 12`'s residue: still `False`, still silent, and
    still a stated condition on 16C's dispatch. **NOT PROVED TO BE CARRIED ANYWHERE:** nothing
    outside this instrument reads :func:`_declared_names`.

 16 **THE TWO RECOGNISERS AGREE ABOUT "READABLE" BY CONSTRUCTION, AND A BRANCH THIS CHECK CANNOT
    FULLY READ HAS NO IDENTIFIED STATE.** *** NEW AT `16B-FIX-5` (`FX16`, closing `CD-ASR-WO3-09`
    F2). *** `FX12` was applied at the ROOT-PROPERTY recogniser only. :func:`_branch_states` read
    `resolved["properties"]["state"]["const"]` and nothing else — no readability test, no
    undecidable outcome — so a branch that resolved to a perfectly good `state.const` **while also
    carrying a keyword this check cannot read** was returned as an identified, accepted branch and
    the walk went on as though it had looked at all of it. MEASURED by the auditor on `dd40407`:
    `{"properties": {"state": {"const": "UNKNOWN"}, ...}, "patternProperties": {"^x_": {}},
    "additionalProperties": false}` -> `_branch_states` ACCEPTED it as `UNKNOWN` with no violation,
    while `_dial_bearing` on the same node answered `True`.

    **HOW THEY ARE PROVED TO AGREE, AND IT IS NOT A COMMENT ASSERTING THAT THEY DO.** Both call
    :func:`_unreadable_keywords`, and the phrase ``not in _READABLE_KEYWORDS`` has **exactly
    one EXECUTABLE occurrence in this file, inside that function** (`grep -n` returns five hits;
    the other four are this sentence and its restatements). There is nothing left for the two to drift from,
    and the claim is greppable rather than argued.

    **THE COST, MEASURED.** A branch carrying ANY unreadable keyword now has `state is None`, is
    reported as `CD-CALM-BRANCHES-006` **with the keyword named**, and is NOT DRIVEN — the same
    treatment a branch whose `state` cannot be read has always had. On the clean tree the three
    branches declare only `type`/`additionalProperties`/`required`/`properties`/`description`, so
    it costs nothing today: `PASS — 144`, and `C6`/`C11`/`C12`/`C17`/`C18`/`C19` — every arm that
    touches a branch — produce output byte-identical to `dd40407`.

    **WHAT THIS DOES NOT CLOSE, SAID PLAINLY.** The two recognisers now agree about READABILITY;
    they are still not one mechanism. :func:`_dial_from_branch`'s
    :data:`CONDITIONAL_KEYWORDS` and `ref_siblings` guards remain SEPARATE and are still needed,
    because `if`/`then`/`else`/`allOf`/`anyOf`/`not` are all perfectly READABLE and are refused for
    a different reason — the branch admits more documents than the one this check builds. **Two
    guards, two reasons, one shared notion of "readable"** — and nobody has proved the CONDITIONAL
    set complete. **AND THE BRANCH SIDE IS ONLY EXERCISED FOR THE `oneOf` UNDER
    `#/$defs/dial_reading`:** a union spelled any other way is `DECLARED LIMIT 9`'s territory, not
    this one's.

 17 **WHAT `RULE CC` CLOSES, AND — SAID FIRST AND NOT LAST — WHAT IT DOES NOT.** *** NEW AT
    `16B-CONTRACT-CLOSURE` (`CC-1`/`CC-2`/`CC-3`). *** `PO-DECISIONS-0028` ruling 1 replaced a
    RECOGNISER at the root with a CLOSED PARTITION over a FINITE SET. **THE CLOSURE ARGUMENT, AND
    IT IS WRITTEN TO BE CHECKED RATHER THAN BELIEVED** — every step is a line of code an auditor
    can read, and the answer sites are enumerated:

      1. **THE ROOT KEY SET IS FINITE AND ENUMERABLE.** `CD-CALM-ROOT-008` iterates
         `schema["properties"]`, a JSON object with finitely many keys.
      2. **NOTHING OUTSIDE THAT ENUMERATION CAN REACH A PUBLISHED DOCUMENT.** Asserted, per
         surface, not assumed: the root declares `additionalProperties: false`, **and** the root
         declares no keyword outside :data:`_ROOT_STRUCTURAL_KEYWORDS`. Without the second
         assertion a root `patternProperties`, `allOf` or `if` could admit a key `properties`
         never names.
      3. **EACH ENUMERATED KEY IS DECIDED BY EQUALITY, NEVER BY A WALK.** :func:`_root_limb`
         is two comparisons: dict equality against a two-token literal, and membership of a
         frozenset of strings. **NEITHER CAN RETURN "I COULD NOT TELL".**
      4. **THEREFORE EVERY ROOT PROPERTY IS limb (a), limb (b), OR A VIOLATION.** There is no
         fourth outcome, because the function has three `return` statements and the third is
         `None`, which the caller reports.
      5. **limb (b) IS NOT TAKEN ON TRUST.** Each allowlisted name, on each surface, is driven
         through the LIVE GATE with a calm-carrying object in its place and MUST be REFUSED, with
         an ADMITTING control per surface so the section cannot pass vacuously.
      6. **limb (a) POINTS AT ONE DEFINITION, AND THAT DEFINITION IS CLOSED.**
         `CD-CALM-CANON-009` asserts the union and every branch are `additionalProperties: false`,
         require `state`, pin `properties.state.const` as a string, and require a freshness stamp;
         `CD-CALM-BRANCHES-006` asserts the branch set is exactly one branch per declared state
         and that the declared state set is exactly :data:`DECLARED_STATES`.
      7. **SO THE BRANCH ALPHABET IS CLOSED, AND OVER A CLOSED ALPHABET THE VALUE CHECK IS
         SUFFICIENT** — `PO-DECISIONS-0028` ruling 1's own words. `CD-CALM-FRESH-010` then makes
         `calm` unrepresentable on every branch that has not proved present-and-fresh.

    **THE CONCLUSION THAT FOLLOWS, AND ONLY THIS ONE:** *a contract edit cannot open a
    calm-over-unknown hole at the ROOT of either envelope without this instrument going RED*,
    because the hole must arrive as a root property, and every root property is limb (a), limb
    (b), or a violation.

    *** NOW THE BOUNDARY, AND IT IS NAMED RATHER THAN LEFT FOR THE NEXT AUDITOR. *** **THE
    ARGUMENT ABOVE IS ABOUT THE TWO ENVELOPE CONTRACTS THIS INSTRUMENT LOADS, AND NOTHING ELSE.**

      (a) **IT IS NOT A CLAIM ABOUT DOCUMENTS THE GATE NEVER SEES.** A rendering path that does
          not call `refuse_unless_publishable` is outside this check entirely — `DECLARED LIMIT
          4`'s closing paragraph, unchanged and still true.
      (b) **IT IS NOT A CLAIM ABOUT A CONTRACT THIS INSTRUMENT IS NOT LOOKING AT.**
          `$CD_CONTRACTS_DIR` can point the live gate at a widened copy; this check REFUSES TO
          RUN when it resolves anywhere but `<root>/contracts`, and it does not PREVENT the route
          (`DECLARED LIMIT 1`, unchanged, **NOT PROVED TO BE CARRIED ANYWHERE**).
      (c) **IT IS A CLAIM ABOUT THE ROOT, NOT ABOUT EVERY POSITION IN THE DOCUMENT.** `RULE CC`
          partitions ROOT properties. Depth inside a canonical dial is covered by
          `CD-CALM-CANON-009`/`-FRESH-010`/`-BRANCHES-006` over the union; depth inside a limb (b)
          property is covered by the LIVE GATE probe and by NOTHING STRUCTURAL. **A limb (b)
          property that is narrow enough to refuse a calm-carrying object today, and is widened
          tomorrow, is caught by the probe — but only for the two shapes in
          :data:`CALM_BEARING_PROBES`.** That is two shapes and it is not a class, and this
          sentence is written that way ON PURPOSE: four sentences on this row have already been
          superseded for describing a sample as a measurement (`DECLARED LIMIT 10`, `12`(a), `13`,
          `14`'s cost column).
      (d) **THE FRESHNESS ASSERTION KEYS ON THE DEFINITION OBJECT `#/$defs/utc_timestamp`, BY
          IDENTITY.** A branch whose stamp is typed by an INLINE copy of the same pattern is
          REPORTED, not accepted — fail-closed — and RENAMING that `$def` turns this instrument
          RED. The remedy is to price the rename, never to loosen the assertion.
      (e) **`DECLARED LIMIT 12`'s RESIDUE IS NOT CLOSED AT THE RECOGNISER AND IS NOT CLAIMED TO
          BE.** :func:`_dial_bearing` still answers `False` about a dial that discriminates on a
          differently-named key. **WHAT CHANGED IS THAT THE GUARANTEE NO LONGER RESTS ON IT:**
          such a dial cannot reach a published envelope as a ROOT property without failing `RULE
          CC`. It is retained as a SECOND instrument (`PO-DECISIONS-0028` ruling 3 — `8398741` is
          preserved and nothing is reverted), and a second instrument's residue is a weaker thing
          than a sole guard's.
      (f) **`PRESENT_STATES` IS TYPED IN, LIKE `DECLARED_STATES`, AND FOR THE SAME REASON.**
          Whether a NEW state means the data is PRESENT is product meaning (`PBG-AUTH-005`). A new
          state therefore makes this instrument RED until a human rules — which is the intended
          cost, and is the mechanism by which `CC-3` refuses `calm` to a never-before-named state
          rather than a list of bad names.
      (g) **NOTHING OUTSIDE THIS INSTRUMENT READS `RULE CC`.** The contracts now STATE the mandate
          in their `description`s, and a `description` refuses nothing. **NOT PROVED TO BE CARRIED
          ANYWHERE.**

      *** LIMB (c) ABOVE IS SUPERSEDED IN ITS SECOND HALF AT `16D-GATE-FRESHNESS`, STATED AND NOT
      ERASED. *** It read *"depth inside a limb (b) property is covered by the LIVE GATE probe and
      by NOTHING STRUCTURAL ... that is two shapes and it is not a class"*, and it was RIGHT — the
      sentence was written that way on purpose and `CD-ASR-WO3-11` then exploited exactly the gap
      it named (`A311-F1`, arm `H`). **THE SENTENCE IS NOW FALSE IN ITS SECOND HALF ONLY:** depth
      inside a limb (b) property IS covered structurally, by :func:`_can_carry_detail_level`, over
      the property's own closed subschema, through objects and arrays at every depth, with capable
      and UNDECIDABLE both violations — and the two probes are RETAINED as the paired behavioural
      control. **THE FIRST HALF STANDS UNCHANGED:** `RULE CC` is still a claim about the ROOT.
      `DECLARED LIMIT 18` states what the structural half itself does NOT cover.

 18 **LIMB (b)'s PROOF WAS A SAMPLE OF TWO AND IS NOW STRUCTURAL — AND THE STRUCTURAL HALF HAS ITS
    OWN RESIDUE.** *** NEW AT `16D-GATE-FRESHNESS`, CLOSING `CD-ASR-WO3-11`'s `A311-F1`. ***
    `_can_carry_detail_level` decides, over each allowlisted root property's OWN CLOSED SUBSCHEMA,
    whether ANY conforming instance could carry a `detail_level` at any depth through any
    container. `True` and `None` are BOTH violations. **WHAT IT DOES NOT COVER:**
      (a) its decidable keyword set is deliberately much narrower than :data:`_READABLE_KEYWORDS`
          — `allOf`/`anyOf`/`oneOf`/`not`/`if`/`then`/`else`/`contains`/`patternProperties`/
          `propertyNames`/`dependentSchemas`/`unevaluatedProperties` on an allowlisted root
          property make it **UNDECIDABLE and this instrument RED**. That is the ruled direction and
          it is a REAL COST: a legitimate future widening written with a composition keyword turns
          this row red until a human looks at it;
      (b) it OVER-REPORTS in two known places, both toward RED — a node with NO `type` is CAPABLE
          (correctly: `{"minLength": 1}` admits `{"detail_level": "calm"}`), and a shape closed
          only by `unevaluatedProperties: false` reads as CAPABLE because that keyword is not in
          the decidable set;
      (c) it is a claim about the SUBSCHEMA and never about the gate — `DECLARED LIMIT 1` is
          untouched;
      (d) it says nothing about limb (a), which is decided by dict equality and never put through
          this procedure.

 19 **THE GATE'S FRESHNESS FLOOR IS ONLY AS HONEST AS THE WINDOW THE DOCUMENT DECLARES. NAMED AND
    NOT CLOSED.** *** NEW AT `16D-GATE-FRESHNESS` (`CD-PL-F206`). *** The fourth refusal stage in
    `envelope_contract` compares against the `staleness_window_seconds` THE DOCUMENT ITSELF
    DECLARES, so a detector that stamps an absurdly large window re-opens the hole from the other
    side. **A DOCUMENT-INTERNAL COMPARISON CANNOT BOUND ITS OWN COMPARAND.** The per-indicator
    floors exist and are ratified in `governance/mapping/indicator_mapping.yaml` (30 indicators,
    345600..10368000 seconds) but **THE ENVELOPE HAS NO INDICATOR DIMENSION — IT HAS TWO DIALS**,
    and collapsing 30 windows onto a dial is PRODUCT MEANING (`PBG-AUTH-005`). **STRICTLY BETTER
    THAN THE PRIOR STATE EITHER WAY: BEFORE `16D` THERE WAS NO COMPARISON AT ALL.**

 20 **WHAT THE FOURTH STAGE ITSELF DOES NOT PROVE.** *** NEW AT `16D-GATE-FRESHNESS`. *** It is
    asserted by `tests/test_envelope_freshness.py` and NOT by this instrument.
      (a) a calm-bearing node's stamps are detected BY VALUE and the OLDEST governs, which cannot
          be defeated by renaming a stamp — but a node carrying an unrelated string that happens
          to be a valid UTC instant has that string counted. Oldest-governs makes every such case
          MORE conservative except where a node has NO real stamp and a decoy fresh one;
      (b) a `:60` leap second parses as no instant and FAILS CLOSED. No producer here can emit one;
      (c) it guards `calm` and only `calm` — a stale `elevated` or `acute` reading is ADMITTED,
          which is the criterion's own scope;
      (d) it says nothing about whether the `published_utc` a document carries is the instant that
          document was really published. Nothing in a document can prove that about itself.

*** NUMBERING, BECAUSE `CD-ASR-WO3-06` COULD NOT VERIFY IT AND SAID SO. *** **DECLARED LIMIT
NUMBERS ARE PER REGISTER ROW, NOT PER FILE.** These are the limits of
`CD-RT-001-MISSING-DATA-NEVER-CALM` and they run **1–20** (**1–12 until `16B-FIX-3`, which added
`13`; `14` added at `16B-FIX-4`; `15` and `16` added at `16B-FIX-5`; `17` added at
`16B-CONTRACT-CLOSURE`; `18`, `19` and `20` added at `16D-GATE-FRESHNESS`**), said identically in
this
header, in
`required-tests.yaml`, and in `contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md`
(`CD-RULE-004`, three places). The SIBLING row `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` has its OWN
independent 1–12 sequence, spread across
`tools/register/check_judgement_path_doors.py` (1–4, 7–9), `src/crash_detector/admission.py`
(5–6) and `required-tests.yaml` (10–12). **BOTH ROWS LIVE IN `required-tests.yaml`, SO A BARE
"DECLARED LIMIT 12" IS AMBIGUOUS THERE AND ALWAYS WAS.** Quote the row id with the number.

*** AND `18`, `19` AND `20` ARE SAID IN TWO OF THE THREE PLACES `CD-RULE-004` REQUIRES, NOT
THREE. DISCLOSED HERE RATHER THAN LEFT TO BE DISCOVERED. *** They are in this header and in
`contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md`. They are NOT in
`required-tests.yaml`, because `required-tests.yaml` is **OUTSIDE `CD-ENG-WO3-12`'s WRITABLE
SCOPE** under `CD-DISPATCH-WO3-INC16D-GATE-FRESHNESS-ENGINEER`. A necessary change outside a
writable scope is an ESCALATION and not an initiative, so it is raised as a finding
(`CD-ENG-F16D-02`) and left for the Project Lead rather than taken. **THE REGISTER ENTRY
THEREFORE UNDERSTATES THIS ROW'S LIMITS BY THREE UNTIL THAT IS CLOSED**, which is the safe
direction for a register entry to be wrong in — it claims LESS than the guard delivers, never
more — but it is a real gap in `CD-RULE-004` compliance and it is stated as one.

EXIT: 0 clean · 1 violation, with the cell and the observed outcome · 2 usage ·
3 precondition not met. Never a skip, for any reason (`PBG-CI-002`).
"""

from __future__ import annotations

import copy
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
    **A merge can therefore admit documents THE NODE AS WRITTEN REFUSES — it can only ever WEAKEN
    this instrument, silently, which is the exact failure class F1 is.** Reporting cannot weaken
    it: it can only over-report, and an over-report costs one seat one look at one contract.
    (**SUPERSEDED SENTENCE, `16B-FIX-4`, `FX14`:** this read *"admit documents neither schema
    admits"*, which is FALSE and provably impossible. See `DECLARED LIMIT 13`'s supersession.)
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

#: *** EVERY REMAINING JSON SCHEMA 2020-12 KEYWORD THAT CARRIES NO SUBSCHEMA. *** Enumerated from
#: the specification's own vocabularies — Core, Applicator, Validation, Format-Annotation, Content
#: and Meta-Data — and DELIBERATELY EXHAUSTIVE, because this is the list that decides when the
#: recogniser is allowed to say `False`. Four Core keywords are ABSENT ON PURPOSE and are therefore
#: UNREADABLE: `$id` (it moves the base URI a relative `$ref` resolves against, and
#: :func:`_resolve` always resolves against the document root), `$dynamicRef`, `$dynamicAnchor` and
#: `$recursiveRef`/`$recursiveAnchor` (references this resolver does not follow — `CD-ASR-WO3-08`
#: F1 arm `DYN`, arm `C24`).
#:
#: *** THE DOCSTRING'S SECOND HALF USED TO READ "AND NAMES NO PROPERTY" AND IT WAS FALSE OF TWO
#: MEMBERS. CORRECTED AT `16B-FIX-5` (`FX15`, closing `CD-ASR-WO3-09` F1). *** `enum` and `const`
#: carry INSTANCE VALUES, and an instance value that is an object NAMES PROPERTIES — including
#: `state` and `detail_level`. **THEY ARE STILL LISTED HERE AND THAT IS DELIBERATE**: they carry no
#: SUBSCHEMA, so there is nothing under them for :func:`_dial_bearing` to descend into, and making
#: them UNREADABLE would turn every ordinary `{"type": "string", "enum": [...]}` root property
#: UNDECIDABLE — the auditor MEASURED that and priced it as an explosion of the false-positive
#: tail. **THE ALPHABET IS CORRECTED WHERE THE DEFECT IS, IN :func:`_declared_names`, WHICH NOW
#: READS THEIR VALUES.** `default` and `examples` also take arbitrary instance values and are NOT
#: read there, and the distinction is the one the auditor drew: they are ANNOTATIONS in the
#: Meta-Data vocabulary and ASSERT NOTHING, so a `state` named inside one constrains no document
#: and cannot admit one; `enum` and `const` ASSERT.
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

#: How deep :func:`_instance_declared_names` walks an `enum` member or a `const` value. An instance
#: value is arbitrary JSON and may nest without limit; this is the same cap :func:`_dial_bearing`
#: puts on its own descent, for the same reason, and reaching it is handled the same way — see the
#: comment at the cap itself.
INSTANCE_WALK_CAP = 24

#: The sentinel :func:`_instance_declared_names` returns when it hits its cap. Not a property name
#: any contract can declare, so it can never be mistaken for one.
INSTANCE_TOO_DEEP = "<<instance value nested deeper than this check walks>>"


#: *** RULE CC, LIMB (a) — THE CANONICAL DIAL SLOT, AS A LITERAL. *** A root property is in limb
#: (a) when its subschema is EXACTLY this mapping: that one key, that one value, **and no sibling
#: keyword**. The test is DICT EQUALITY, not `sub.get("$ref") == ...`, and the difference is the
#: whole of `DECLARED LIMIT 13`: in 2020-12 a keyword sibling to `$ref` APPLIES, so
#: `{"$ref": "#/$defs/dial_reading", "unevaluatedProperties": {...}}` is a DIFFERENT schema from
#: this one and must not be admitted to limb (a) on the strength of sharing its `$ref`.
CANONICAL_DIAL_SLOT = {"$ref": "#/$defs/dial_reading"}

#: *** RULE CC, LIMB (b) — THE FINITE WRITTEN ALLOWLIST OF NON-DIAL ROOT PROPERTIES. ***
#: *** NEW AT `16B-CONTRACT-CLOSURE` (`CC-1`), AND IT IS THE ARCHITECTURAL CLOSE ORDERED BY
#: `PO-DECISIONS-0028` RULING 1. ***
#:
#: **IT IS DERIVED, NOT INVENTED.** It is exactly the union, over both surfaces, of the root
#: properties the contracts declare TODAY that are not canonical dial slots — enumerated from the
#: two contracts at this commit and written down here so that the set is CLOSED and a reader can
#: audit it in one screen. `classification` is PRIVATE-only; the other eight are on both surfaces.
#:
#: *** ADDING A NAME HERE IS A PRODUCT ACT AND NOT AN ENGINEER'S (`PBG-AUTH-005`). *** If a
#: contract grows a root property that is neither a canonical dial slot nor already on this list,
#: this instrument goes **RED AND STAYS RED** until a human rules on it. That is the intended cost
#: and it is the same asymmetry `DECLARED LIMIT 8` prices for a new dial STATE: whether a new root
#: property can carry a rendering decision is product meaning, and guessing "it cannot" is how
#: `calm` gets admitted over an absence in silence.
#:
#: **A WRITTEN ALLOWLIST OF NAMES IS A DENYLIST WEARING AN ALLOWLIST'S CLOTHES IF NOTHING PROVES
#: THE NAMED PROPERTIES ARE REALLY NOT DIALS**, so membership here is NOT sufficient: every name
#: on this list is put to the LIVE GATE, on every surface, with a calm-carrying object in its
#: place, and must be REFUSED. See the `CD-CALM-ROOT-008` limb-(b) section in :func:`main`.
NON_DIAL_ROOT_PROPERTIES = frozenset({
    "schema_version",
    "classification",
    "as_of_utc",
    "published_utc",
    "regime",
    "staleness_window_seconds",
    "inputs_used",
    "degraded_inputs",
    "config_snapshot_id",
})

#: *** THE KEYWORDS THE ROOT MAY DECLARE FOR RULE CC's ENUMERATION TO BE EXHAUSTIVE. ***
#: Rule CC enumerates `schema["properties"]` and asserts every member is limb (a) or limb (b).
#: **THAT ENUMERATION IS ONLY EXHAUSTIVE IF NOTHING ELSE AT THE ROOT CAN INTRODUCE OR CONSTRAIN A
#: ROOT PROPERTY**, so the root node itself is closed here, by the same deny-by-default rule and
#: for the same reason. A root carrying `patternProperties`, `allOf`, `if`/`then`/`else`,
#: `$dynamicRef`, `dependentSchemas`, `unevaluatedProperties` or any keyword nobody has written
#: yet can admit a root key `properties` never names, and Rule CC would then be a partition of a
#: SUBSET while claiming to be a partition of the whole. **ANYTHING OUTSIDE THIS SET AT THE ROOT
#: IS A VIOLATION**, which is the loud, ruled direction. This is deliberately NOT
#: :data:`_READABLE_KEYWORDS`: that set is what the RECOGNISER may descend, and it is far wider
#: than what a closed envelope root has any business declaring.
#:
#: `$id` is admitted and the reason is MEASURED rather than assumed: it moves the base URI a
#: RELATIVE `$ref` resolves against, both contracts declare it as a non-dereferenceable `urn:`,
#: and every `$ref` in both contracts is a local `#/` fragment that :func:`_resolve` resolves
#: against the document root regardless. It constrains no property and names none.
_ROOT_STRUCTURAL_KEYWORDS = frozenset({
    "$schema", "$id", "$defs", "$comment", "$anchor", "$vocabulary",
    "title", "description",
    "type", "additionalProperties", "required", "properties",
})

#: *** LIMB (b)'s AFFIRMATIVE PROOF, AND IT IS A VALUE CHECK — `PO-DECISIONS-0028` RULING 1's OWN
#: WORDS, *"within that closed shape the value check is sufficient."* *** Each of these is put in
#: the place of an allowlisted non-dial root property, in an otherwise ADMITTED envelope, and the
#: live gate MUST REFUSE it. A root property that ADMITS a calm-carrying object **is not a
#: non-dial property, whatever the allowlist says.** Two variants, because one of them is the flat
#: shape and the other is the nested shape this row's entire history is made of.
CALM_BEARING_PROBES = (
    ("flat", {DETAIL_LEVEL: CALM}),
    ("nested", {"reading": {"state": "SPINDRIFT", DETAIL_LEVEL: CALM}}),
)


def _root_limb(name: str, subschema):
    """Which limb of **RULE CC** this root property is in: ``"a"``, ``"b"``, or ``None``.

    *** THIS FUNCTION IS THE ARCHITECTURAL CLOSE, AND WHAT MATTERS ABOUT IT IS WHAT IT DOES NOT
    DO: IT DOES NOT RECOGNISE ANYTHING. *** :func:`_dial_bearing` asks an open-space question —
    *"is there, somewhere under this node, a property called `state`?"* — over a space with no
    boundary, and its `False` means only *"nothing I could read named one"*. Nine audits attacked
    that question and the tenth proved it unanswerable: a `status` spelling, an `{"enum": [...]}`
    dial, a nest past the depth cap and a `present: false` reading are all nodes it answers
    `False` about, and `CD-CALM-SLOTS-007` compared `dial_bearing` against `found` — **so a root
    property in NEITHER set satisfied the comparison and was INVISIBLE.** That is the hole,
    exactly.

    **THIS ASKS THE CLOSED QUESTION INSTEAD: of every root property there is, is this one of the
    two things a root property is ALLOWED to be?**

      ``"a"``   a CANONICAL DIAL SLOT — its subschema is EXACTLY
                :data:`CANONICAL_DIAL_SLOT`, decidable by dict equality against a two-token
                literal;
      ``"b"``   a DECLARED NON-DIAL PROPERTY — its NAME is a member of
                :data:`NON_DIAL_ROOT_PROPERTIES`, decidable by string equality, **and** it is
                separately proved by the LIVE GATE to be incapable of carrying a `detail_level`;
      ``None``  **A VIOLATION. THERE IS NO THIRD CASE AND THERE IS NO SILENCE.**

    **WHY THE PARTITION IS EXHAUSTIVE, WHICH IS THE CLAIM THE WHOLE INCREMENT RESTS ON.** The
    root's `properties` object has a FINITE, ENUMERABLE key set; both limbs are decided by
    EQUALITY rather than by a walk; the root carries `additionalProperties: false` (asserted, not
    assumed — see `CD-CALM-ROOT-008` in :func:`main`); and the root declares no keyword outside
    :data:`_ROOT_STRUCTURAL_KEYWORDS` (also asserted), so nothing else at the root can introduce a
    property this enumeration does not see. **THE ALPHABET IS CLOSED, SO "EVERYTHING ELSE" IS A SET
    THIS INSTRUMENT CAN NAME WITHOUT HAVING TO RECOGNISE ANYTHING.**

    **`A310-F2` AND `A310-F3` ARE NOT CLOSED BY THIS — THEY ARE UNREACHABLE.** A root property
    spelled `{"enum": [...]}`, or one whose discriminator is called `status`, or one nested
    twenty-five deep, or one carrying `present: false`, is a root property that is neither limb
    (a) nor limb (b). It does not need to be RECOGNISED as a dial to be refused; it is refused for
    not being one of the two permitted shapes, and the recogniser is never consulted.

    *** THE RECOGNISER IS NOT DELETED AND IS NOT LOAD-BEARING. *** :func:`_dial_bearing` and
    `CD-CALM-SLOTS-007` are KEPT, unchanged in behaviour but for `CC-4`, as a SECOND INSTRUMENT
    over the same root properties (`PO-DECISIONS-0028` ruling 3: `8398741` is preserved, nothing
    is reverted). What changed is that the GUARANTEE no longer rests on them.
    """
    if subschema == CANONICAL_DIAL_SLOT:
        return "a"
    if name in NON_DIAL_ROOT_PROPERTIES:
        return "b"
    return None


def _unreadable_keywords(node) -> list:
    """Every keyword of ``node`` this check CANNOT READ. Empty means it read the whole node.

    *** THIS FUNCTION IS THE WHOLE OF `FX16` AND IT EXISTS TO BE THE *ONLY* DEFINITION
    (`16B-FIX-5`, closing `CD-ASR-WO3-09` F2). *** Before it there were two recognisers in this
    file and only ONE of them had the `FX12` inversion: :func:`_dial_bearing` asked whether it
    could read every keyword of the node, and :func:`_branch_states` asked nothing at all — it read
    `properties.state.const` and accepted a branch that also carried `patternProperties`, a
    `$dynamicRef`, or a keyword from a draft nobody has written, **silently**. MEASURED by the
    auditor on the target tree: the node
    `{"properties":{"state":{"const":"UNKNOWN"},...},"patternProperties":{"^x_":{}},
    "additionalProperties":false}` came back from :func:`_branch_states` as an accepted `UNKNOWN`
    branch with no violation, while :func:`_dial_bearing` on the same node answered `True`.

    **TWO RECOGNISERS THAT DISAGREE ABOUT WHAT "READABLE" MEANS ARE ONE EDIT FROM A HOLE**, and a
    comment asserting they agree would not be a proof. This is the proof, and it is mechanical:
    the phrase ``not in _READABLE_KEYWORDS`` has EXACTLY ONE EXECUTABLE OCCURRENCE in this
    file, on the `return` below, and both recognisers reach it by calling this function. They cannot drift, because there is nothing left
    to drift from.
    """
    if not isinstance(node, dict):
        return []
    return sorted(key for key in node if key not in _READABLE_KEYWORDS)


def _instance_declared_names(value, depth: int = 0) -> set:
    """Every property name an INSTANCE VALUE names, **AT ANY DEPTH**.

    *** NEW AT `16B-FIX-5` (`FX15`), AND IT IS THE ALPHABET CORRECTION `PO-DECISIONS-0027`
    RULING 6 CALLS "THE LAST STRUCTURAL STEP". *** `FX12`'s inversion is a TRUE universal
    quantification — but over KEYWORD NAMES, and never over what a readable keyword's VALUE
    asserts. `enum` and `const` take instance values, an object instance value NAMES PROPERTIES,
    and so a root property spelled

        {"enum": [ {"state": "LIVE", ...}, {"state": "STALE", "detail_level": "calm"} ]}

    is a dial in every product sense — it declares the states, it declares `detail_level`, it is
    exactly as tight as the `oneOf` spelling — and the superseded recogniser read the keyword name
    `enum`, found it readable, never looked inside, found no `properties`/`required`/
    `dependentRequired` naming `state`, and returned a clean `False`: **NOT A DIAL**. MEASURED
    end-to-end by `CD-ASR-WO3-09` on the honest 16C tree: instrument `PASS — 144 assertions, 0
    violations` with the live gate ADMITTING a DEAD FEED rendering as `calm` on BOTH surfaces.

    **THE DEPTH DECISION IS DECLARED AND PRICED (`DECLARED LIMIT 15`).** An `enum` member is
    arbitrary JSON and may nest — ``{"enum": [{"reading": {"state": ...}}]}`` names `state` one
    level down, and ``{"enum": [[{"state": ...}]]}`` names it inside an array. This walk collects
    names at EVERY depth of the value, through objects and arrays alike, because the top-level-only
    reading would be a sixth spelling patch: it would close the shape the auditor wrote and leave
    the shape one nesting deeper open, which is this row's entire history. The price is a WIDER
    false-positive class — any node whose `enum` or `const` value contains, anywhere inside it, an
    object with a key called `state` is now UNDECIDABLE — and it is the ruled direction: **a false
    positive costs one seat one look at one contract; a false negative costs the constitution.**
    MEASURED: neither envelope contract carries an object-valued or array-valued `enum`/`const`
    anywhere, so this costs the clean tree nothing.

    **A `const` THAT IS NOT AN OBJECT NAMES NOTHING, AND THAT IS SAID HERE RATHER THAN LEFT TO BE
    INFERRED.** ``{"const": "equity_crash"}`` and ``{"type": "string", "enum": ["a", "b"]}`` return
    the EMPTY SET from this function and are therefore still answered `False` by
    :func:`_dial_bearing`. Scalar `enum`/`const` are genuinely inert and stay green: that is the
    whole reason `enum` and `const` remain in :data:`_INERT_KEYWORDS` instead of being made
    unreadable, which the auditor measured would explode the tail.

    **AND THE STRING ``"state"`` APPEARING AS A VALUE IS NOT A DECLARATION.** Only the KEYS of
    object instance values are collected, so ``{"enum": ["state", "detail_level"]}`` — a perfectly
    ordinary string enum — names nothing.
    """
    if depth > INSTANCE_WALK_CAP:
        # An instance value nested deeper than this walk goes. It is not silently discarded: the
        # sentinel below is a name no JSON Schema property can have and no contract can declare,
        # so it enters `declared`, cannot equal `state`, and cannot make the node `True` — but a
        # caller asking "did you read all of it?" gets an honest NO. See DECLARED LIMIT 15.
        return {INSTANCE_TOO_DEEP}
    names: set = set()
    if isinstance(value, dict):
        names |= {key for key in value if isinstance(key, str)}
        for member in value.values():
            names |= _instance_declared_names(member, depth + 1)
    elif isinstance(value, list):
        for member in value:
            names |= _instance_declared_names(member, depth + 1)
    return names


def _declared_names(resolved: dict) -> set:
    """*** EVERY PROPERTY NAME THIS NODE NAMES, OVER EVERY NAMING POSITION 2020-12 HAS. ***

    This is the ALPHABET the `FX12` inversion quantifies over, and until `16B-FIX-5` it was three
    keywords wide. It is now the complete list, and the completeness claim is made against the
    specification rather than against a list of attacks — **a property name can appear in a 2020-12
    schema in exactly these positions**:

    ==========================  ================================================================
    position                    handled
    ==========================  ================================================================
    `properties` keys           READ HERE
    `required` members          READ HERE
    `dependentRequired` values  READ HERE
    `dependentRequired` keys    *** READ HERE, NEW AT `16B-FIX-5` (`FX15`). *** A key of
                                `dependentRequired` NAMES a property just as literally as a member
                                of its value list does — ``{"dependentRequired": {"state":
                                ["reason"]}}`` says "if `state` is present then `reason` must be",
                                which names `state` and constrains a document that carries one.
                                The superseded code read the VALUES and not the KEYS, so that node
                                answered a clean `False`. **NOBODY ATTACKED THIS AND IT IS FIXED
                                ANYWAY**, because the point of an alphabet correction is to be
                                complete rather than to close the shape it was shown.
    `enum` object members       *** READ HERE, NEW AT `16B-FIX-5` (`FX15`) — `CD-ASR-WO3-09` F1.
                                *** See :func:`_instance_declared_names`.
    `const` object value        *** READ HERE, NEW AT `16B-FIX-5` (`FX15`) — `CD-ASR-WO3-09` F1.
    `patternProperties` keys    NOT READ — regular expressions. In
                                :data:`_NAME_BEARING_APPLICATORS`, therefore UNREADABLE, therefore
                                the node is UNDECIDABLE before this function is consulted.
    `propertyNames`             NOT READ — constrains names it never lists. Same treatment.
    `dependentSchemas` keys     NOT READ — selects a whole schema by another property's presence.
                                Same treatment.
    `default` / `examples`      NOT READ, AND DELIBERATELY. Annotations: they assert nothing, so a
                                `state` named inside one constrains no document and can admit
                                none. `enum`/`const` ASSERT, which is the whole distinction.
    ==========================  ================================================================

    **ADDING A NAME HERE CAN ONLY EVER MAKE THE ANSWER STRICTER, NEVER LOOSER**, and that is the
    reason this function is safe to widen without re-auditing everything downstream: its only
    consumer is the test ``"state" in declared`` in :func:`_dial_bearing`, and the limb that test
    guards sets ``undecidable = True``. More names means more UNDECIDABLE and never more `False`.
    """
    declared: set = set()
    properties = resolved.get("properties")
    if isinstance(properties, dict):
        declared |= {key for key in properties if isinstance(key, str)}
    required = resolved.get("required")
    if isinstance(required, list):
        declared |= {name for name in required if isinstance(name, str)}
    dependent_required = resolved.get("dependentRequired")
    if isinstance(dependent_required, dict):
        declared |= {key for key in dependent_required if isinstance(key, str)}
        for names in dependent_required.values():
            if isinstance(names, list):
                declared |= {name for name in names if isinstance(name, str)}
    # *** THE VALUE OF A READABLE KEYWORD, WHICH IS THE ALPHABET THE INVERSION WAS MISSING. ***
    if isinstance(resolved.get("enum"), list):
        for member in resolved["enum"]:
            declared |= _instance_declared_names(member)
    if "const" in resolved:
        declared |= _instance_declared_names(resolved["const"])
    return declared


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
    # *** ONE DEFINITION OF "CANNOT READ", SHARED WITH `_branch_states`. NEW AT `16B-FIX-5`
    # (`FX16`, closing `CD-ASR-WO3-09` F2). *** The predicate used to be written out here and
    # nowhere else, so the branch recogniser two hundred lines below had no inversion at all.
    unreadable = _unreadable_keywords(resolved)
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
    # *** AND WIDENED AGAIN AT `16B-FIX-5` (`FX15`), WHICH IS THE ALPHABET CORRECTION AND THE ONLY
    # THING `CD-ASR-WO3-09` FOUND WRONG WITH THE INVERSION. *** `FX12` quantified over KEYWORD
    # NAMES and never over what a READABLE keyword's VALUE asserts, so `{"enum": [<a LIVE
    # reading>, <a STALE reading whose detail_level is "calm">]}` was read, found to contain no
    # unreadable keyword, found to name no `state` in `properties`/`required`/`dependentRequired`,
    # and answered a clean `False` — NOT A DIAL — while the live gate ADMITTED a dead feed
    # rendering as `calm` on both surfaces. **THE QUANTIFIER WAS RIGHT AND THE ALPHABET WAS
    # WRONG.** :func:`_declared_names` is now the whole alphabet and it is enumerated against the
    # specification's naming positions rather than against the four shapes that escaped.
    declared = _declared_names(resolved)

    # *** THE INSTANCE-WALK CAP NOW FAILS CLOSED. NEW AT `16B-CONTRACT-CLOSURE` (`CC-4`, closing
    # `CD-ASR-WO3-10` `A310-F1`, ruled a separate bounded fix by `PO-DECISIONS-0028` ruling 4). ***
    # `FX15` gave :func:`_instance_declared_names` a depth cap and, at that cap, returned the
    # sentinel :data:`INSTANCE_TOO_DEEP` — **which had ZERO EXECUTABLE CONSUMERS.** It entered
    # `declared`, `declared`'s only reader was the `"state" in declared` test on the next line, a
    # sentinel can never equal `state`, so the node fell through to `return None if undecidable
    # else False` with `undecidable` still False and answered **a clean `False`: the only SILENT
    # answer this instrument has.** `DECLARED LIMIT 15`'s own heading said *"REACHING THE CAP IS
    # NOT A SILENT SUCCESS"* and the code did the opposite of what the heading claimed.
    # **MEASURED, ONE INTEGER APART, at `8398741` and re-measured by this seat before the fix:**
    # a `{"state": ..., "detail_level": "calm"}` object nested inside an `enum` member at depth
    # 1/5/20/22/23/24 -> `None` (UNDECIDABLE, reported); at 25/26/30/40 -> **`False`**.
    # **THE CAP MUST BE HANDLED THE WAY :func:`_dial_bearing`'s OWN CAP AT LINE ~1515 IS HANDLED:
    # a walk that did not complete is `DECLARED LIMIT 14` limb (c), UNDECIDABLE, never `False`.**
    # It is fixed here rather than inside :func:`_instance_declared_names` because that function
    # returns a NAME SET and has no `None` to return; the sentinel is its honest report that it
    # stopped early, and this is the consumer that was missing. **Rule CC (`CC-1`) makes a nest
    # this deep unreachable at the root anyway — the cap is fixed REGARDLESS, because a cap that
    # fails open is a defect whether or not anything currently reaches it.**
    if INSTANCE_TOO_DEEP in declared:
        undecidable = True

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


#: *** THE JSON TYPES THERE ARE. *** A `type` token outside this set is one this file has never
#: heard of, which makes the node UNDECIDABLE rather than benign — the same inversion `FX12`
#: applies to keywords, applied to type tokens.
_JSON_TYPES = frozenset({
    "object", "array", "string", "number", "integer", "boolean", "null",
})

#: *** THE KEYWORDS :func:`_can_carry_detail_level` CAN COMPLETELY ACCOUNT FOR, AND IT IS
#: DELIBERATELY MUCH NARROWER THAN :data:`_READABLE_KEYWORDS`. ***
#:
#: That set is what the DIAL RECOGNISER may descend; this one is what a decision procedure about
#: **what instances a subschema ADMITS** can settle. The two questions are not the same and must
#: not share a set. `allOf`/`anyOf`/`oneOf`/`not`/`if`/`then`/`else` are all perfectly readable to
#: a walk that is only looking for a declared name; to a walk that must decide *"can any conforming
#: instance carry a `detail_level` anywhere?"* they are composition, and composition is where a
#: naive walk quietly answers about a schema nobody wrote. **THEY ARE THEREFORE UNDECIDABLE HERE
#: AND THE INSTRUMENT GOES RED ON THEM.** MEASURED: no allowlisted non-dial root property in
#: either contract declares one today, so the strictness costs the clean tree nothing — and if one
#: ever does, a human looks at it, which is the whole intent.
_DETAIL_CARRIER_DECIDABLE_KEYWORDS = frozenset({
    # Core / annotation — assert nothing about the instance
    "$schema", "$vocabulary", "$comment", "$anchor", "$defs", "$ref",
    "title", "description", "default", "deprecated", "readOnly", "writeOnly", "examples",
    # Validation assertions this procedure accounts for by CONSTRUCTION
    "type", "enum", "const",
    "multipleOf", "maximum", "exclusiveMaximum", "minimum", "exclusiveMinimum",
    "maxLength", "minLength", "pattern",
    "maxItems", "minItems", "uniqueItems", "maxProperties", "minProperties",
    "format", "contentEncoding", "contentMediaType",
    # The shape keywords it reads DIRECTLY
    "required", "properties", "additionalProperties", "items", "prefixItems",
})

#: How deep the structural walk descends. Reaching it is UNDECIDABLE and never a clean `False` —
#: the same treatment `CC-4` gave :func:`_instance_declared_names`' cap, for the same reason.
DETAIL_CARRIER_DEPTH_CAP = 24


def _can_carry_detail_level(schema: dict, node, depth: int = 0, seen=None):
    """Can ANY instance conforming to this subschema carry a ``detail_level``, at any depth?

    ``True`` / ``False`` / ``None`` = **UNDECIDABLE, AND THE INSTRUMENT GOES RED ON IT.**

    *** THIS IS `CD-ASR-WO3-11`'s `A311-F1`, AND IT IS THE REMEDY THE AUDITOR PRESCRIBED RATHER
    THAN THE ONE THAT WOULD HAVE BEEN CHEAPER. ***

    Rule CC limb (b) claims each allowlisted root property is *"AFFIRMATIVELY PROVED incapable of
    carrying a `detail_level`"*. Until now the whole of that proof was a **SAMPLE OF TWO PROBE
    SHAPES** — :data:`CALM_BEARING_PROBES`, one flat and one nested — driven through the live gate.
    **A SAMPLE OF TWO IS NOT A PROOF OF A UNIVERSAL, AND A THIRD SHAPE DEFEATED IT.** The auditor's
    arm `H` widened the allowlisted root property `degraded_inputs` to an ARRAY OF CLOSED OBJECTS
    carrying `#/$defs/detail_level`. **BOTH PROBES ARE STILL REFUSED ON THAT TREE** — the flat
    object and the nested object are neither of them an array — so this instrument went on
    reporting `PASS — 243`, the whole thirty-line register was identical in every rc, and the LIVE
    GATE ADMITTED `"degraded_inputs": [{"source_id": "SRC-A", "detail_level": "calm"}]` on BOTH
    SURFACES: the list of inputs that are DEGRADED, rendering as CALM, at a root position. The
    increment's own arm `CC-H` widens the same property to an OBJECT and is caught (`FAIL — 4`).
    **ONE CONTAINER DEEPER AND THE PROOF EVAPORATED.**

    *** THE REMEDY IS NOT A THIRD PROBE, AND THE AUDITOR SAID SO IN TERMS: *** a third shape
    *"moves the census game to the probe alphabet and earns an eleventh"*. Enumerating shapes is
    RECOGNITION OVER AN OPEN SET and it is what has lost eleven consecutive audits on this row.
    **THIS ASKS THE CLOSED QUESTION OF THE SUBSCHEMA INSTEAD** — not *"is this one of the shapes I
    know how to build?"* but *"of everything this subschema admits, is there anything that could
    carry a rendering decision?"* — and it is decided from the subschema's OWN CLOSED TEXT.

    **THE PROBES ARE RETAINED, AND THAT IS ALSO THE AUDITOR'S PRESCRIPTION**: a structural value
    check *"with the probes retained as the paired behavioural control"*. Structure and behaviour
    answer different questions — this one says what the contract ADMITS, the probes say what the
    GATE DOES — and a disagreement between them is itself a finding.

    ---- THE PROCEDURE, AND WHY EACH LIMB IS A COMPLETE ANSWER --------------------------------

    ``const``            the instance is pinned to exactly one value; walk that value's own
                         property names. A COMPLETE decision, because nothing else the node
                         declares can widen it.
    ``enum``             the instance is one of a finite list; the same walk, over every member.
    ``object`` admitted  ``additionalProperties`` anything but ``false`` -> **CAPABLE**, because an
                         arbitrary key is admissible and ``detail_level`` is an arbitrary key.
                         Closed, and ``detail_level`` declared or required -> **CAPABLE**. Closed
                         otherwise -> descend into every declared property.
    ``array`` admitted   ``items`` absent or ``true`` -> **CAPABLE**, because an arbitrary item is
                         admissible and an arbitrary item can be an object with any key. ***THIS
                         IS THE LIMB ARM `H` WALKS THROUGH.*** Otherwise descend into ``items``
                         and ``prefixItems``.
    scalars only         ``string``/``number``/``integer``/``boolean``/``null`` and nothing else
                         -> **NOT CAPABLE**, and this is the only route to ``False``. A scalar has
                         no properties, at any depth, under any spelling.
    anything else        **UNDECIDABLE.** A keyword outside
                         :data:`_DETAIL_CARRIER_DECIDABLE_KEYWORDS`, a `$ref` chain that dropped
                         an asserting sibling or would not resolve, a `type` token this file has
                         never heard of, a walk that hit its depth cap, a cycle.

    **A NODE WITH NO `type` AT ALL IS CAPABLE, AND THAT IS NOT AN OVER-REPORT — IT IS THE
    SPECIFICATION.** ``{"minLength": 1}`` admits ``{"detail_level": "calm"}``: ``minLength``
    applies to strings and asserts nothing about an object. A procedure that read that as "a
    string, therefore safe" would be reading the author's intention rather than the schema.
    """
    if depth > DETAIL_CARRIER_DEPTH_CAP:
        return None
    seen = set() if seen is None else seen

    resolved, dropped = _resolve(schema, node)
    if resolved is None or dropped:
        # Unresolvable, or composed across a `$ref` boundary so the object just resolved is not
        # the schema the gate enforces. UNDECIDABLE, never False (`DECLARED LIMIT 13`).
        return None
    if id(resolved) in seen:
        return None  # a cycle. This walk did not complete, so it has no answer to give.
    seen = seen | {id(resolved)}

    if sorted(key for key in resolved if key not in _DETAIL_CARRIER_DECIDABLE_KEYWORDS):
        return None

    # ---- `const` and `enum` pin the instance, so they DECIDE it outright -------------------- #
    if "const" in resolved:
        names = _instance_declared_names(resolved["const"])
        return None if INSTANCE_TOO_DEEP in names else DETAIL_LEVEL in names
    if "enum" in resolved:
        members = resolved["enum"]
        if not isinstance(members, list):
            return None
        for member in members:
            names = _instance_declared_names(member)
            if INSTANCE_TOO_DEEP in names:
                return None
            if DETAIL_LEVEL in names:
                return True
        return False

    # ---- what TYPES does this node admit? ---------------------------------------------------- #
    declared_type = resolved.get("type")
    if declared_type is None:
        types = set(_JSON_TYPES)          # constrains no type: everything is admissible
    elif isinstance(declared_type, str):
        types = {declared_type}
    elif isinstance(declared_type, list) and all(
        isinstance(token, str) for token in declared_type
    ):
        types = set(declared_type)
    else:
        return None
    if not types <= _JSON_TYPES:
        return None

    undecidable = False

    if "object" in types:
        properties = resolved.get("properties")
        if properties is not None and not isinstance(properties, dict):
            return None
        if resolved.get("additionalProperties", True) is not False:
            # *** THE OPEN OBJECT. *** Any key not named by `properties` is admissible, and
            # `detail_level` is such a key. This is the deny-by-default direction: a shape is
            # capable unless its own text CLOSES it.
            return True
        if isinstance(properties, dict) and DETAIL_LEVEL in properties:
            return True
        required = resolved.get("required")
        if required is not None and not isinstance(required, list):
            return None
        if isinstance(required, list) and DETAIL_LEVEL in required:
            return True
        for child in (properties or {}).values():
            verdict = _can_carry_detail_level(schema, child, depth + 1, seen)
            if verdict is True:
                return True
            if verdict is None:
                undecidable = True

    if "array" in types:
        prefix = resolved.get("prefixItems")
        if prefix is not None:
            if not isinstance(prefix, list):
                return None
            if "items" not in resolved:
                # Positions past the prefix are unconstrained, so an arbitrary object may sit
                # there. CAPABLE without needing to read the prefix at all.
                return True
            for entry in prefix:
                verdict = _can_carry_detail_level(schema, entry, depth + 1, seen)
                if verdict is True:
                    return True
                if verdict is None:
                    undecidable = True
        items = resolved.get("items", True)
        if items is True:
            return True                    # *** ARM H's LIMB. An arbitrary item is an object. ***
        if items is not False:
            if not isinstance(items, dict):
                return None
            verdict = _can_carry_detail_level(schema, items, depth + 1, seen)
            if verdict is True:
                return True
            if verdict is None:
                undecidable = True

    # Everything reachable was read and none of it could hold a property. `False` here is a claim
    # about a shape that WAS READ, never about one that was not recognised.
    return None if undecidable else False


#: The `$def` that types a FRESHNESS STAMP. Both contracts declare it and both use it for every
#: timestamp they carry. **`CC-2` KEYS ON THIS DEFINITION OBJECT AND NOT ON A PROPERTY NAME**, and
#: that is the point: MEASURED at this commit, `VALUE` and `DEGRADED` require `as_of_utc` while
#: `UNKNOWN` requires `since_utc`, so a fixed property name would have been a fifth spelling patch
#: waiting to happen. **RENAMING THIS `$def` TURNS THIS INSTRUMENT RED**, which is fail-closed and
#: is `DECLARED LIMIT 17`'s stated cost — the remedy is to price the rename, never to loosen this.
UTC_TIMESTAMP_DEF = "utc_timestamp"


def _required_timestamp_properties(schema: dict, branch: dict):
    """This branch's REQUIRED properties that are typed as a freshness stamp.

    Returns the list of names, which is EMPTY when the branch requires no timestamp at all — and
    **a branch that requires no timestamp CANNOT PROVE FRESHNESS**, which is `CC-2`'s violation and
    `CC-3`'s premise.

    A property counts only when it is (1) in the branch's own ``required`` list — a stamp the
    branch merely PERMITS proves nothing, because the document that omits it is still admitted —
    and (2) its subschema resolves, through a chain that discarded no assertion, to the very
    ``#/$defs/utc_timestamp`` object this contract declares. The comparison is by OBJECT IDENTITY
    against that definition, so a property typed by an inline copy of the same pattern does NOT
    count. **THAT IS DELIBERATE AND IT IS THE FAIL-CLOSED DIRECTION:** this check would otherwise
    have to decide whether an arbitrary string pattern is "a timestamp", which is exactly the
    open-space recognition question `PO-DECISIONS-0028` ruling 1 removed from the load-bearing
    position. An inline copy is REPORTED, never silently accepted.
    """
    stamp = (schema.get("$defs") or {}).get(UTC_TIMESTAMP_DEF)
    if not isinstance(stamp, dict):
        return None
    properties = branch.get("properties") or {}
    names = []
    for name in (branch.get("required") or []):
        if not isinstance(name, str):
            continue
        subschema = properties.get(name)
        if not isinstance(subschema, dict):
            continue
        resolved, dropped = _resolve(schema, subschema)
        if dropped:
            continue
        if resolved is stamp:
            names.append(name)
    return names


def _calm_admissible(schema: dict, branch: dict):
    """Does this branch's ``detail_level`` admit ``calm``? ``True`` / ``False`` / ``None``.

    ``None`` means this check could not read the branch's level vocabulary at all, and every
    caller treats that as a VIOLATION rather than as an answer. **THE QUESTION IS ASKED OF THE
    VOCABULARY'S VALUES AND NOT OF THE `$def`'s NAME**, which is the same lesson `CD-PL-F169` and
    `CD-ASR-WO3-02`/`-03` each cost this project a RED to learn: a check that reads the `$ref`
    TARGET NAME and never opens the target passes a tree where `calm` has been put back inside the
    target's own enum. `PO-DECISIONS-0028` ruling 1 calls this "the value check", and it is
    sufficient here precisely BECAUSE `CC-1` and `CC-2` have closed the shape it ranges over.
    """
    subschema = (branch.get("properties") or {}).get(DETAIL_LEVEL)
    if not isinstance(subschema, dict):
        return None
    resolved, dropped = _resolve(schema, subschema)
    if dropped or not isinstance(resolved, dict):
        return None
    values = resolved.get("enum")
    if not isinstance(values, list):
        return None
    return CALM in values


def _branch_states(schema: dict, dial_union: dict):
    """The union's branches as ``(label, resolved_branch, state_const, ref_siblings)``.

    The branch SET is what the superseded instrument never enumerated. It wrote out one document
    shape per state by hand, so the union could grow a branch and nothing anywhere would move.

    *** THE FOURTH ELEMENT IS NEW AT `16B-FIX-3` (`FX9`, closing `CD-ASR-WO3-07` F1). *** It is
    every ASSERTING keyword the `$ref` chain from the `oneOf` ENTRY to the branch definition — and
    from the branch to its `state` subschema — discarded on the way. **IT IS COLLECTED AT EVERY
    HOP AND NOT ONLY AT THE ENTRY**, because auditor arm `A2` wrote the conditional one `$ref`
    deeper, behind an innocuous entry, and got the identical escape.

    *** AND SINCE `16B-FIX-5` THIS RECOGNISER HAS THE SAME INVERSION AS THE OTHER ONE (`FX16`,
    closing `CD-ASR-WO3-09` F2). *** `FX12` was applied at the ROOT-PROPERTY recogniser only. This
    function read `resolved["properties"]["state"]["const"]` **and nothing else** — no readability
    test, no :data:`_READABLE_KEYWORDS`, no undecidable outcome — so a branch that resolved to a
    perfectly good `state.const` **while also carrying a keyword this check cannot read** was
    returned as an identified, accepted branch, and the walk went on as though it had looked at the
    whole of it. MEASURED by the auditor on the target tree:

        {"properties": {"state": {"const": "UNKNOWN"}, ...},
         "patternProperties": {"^x_": {}}, "additionalProperties": false}
        _branch_states -> [('oneOf[0]', 'UNKNOWN', [])]     ACCEPTED, no violation
        _dial_bearing  -> True

    **TWO RECOGNISERS IN ONE FILE DISAGREEING ABOUT WHAT "READABLE" MEANS IS ONE EDIT FROM A HOLE.**
    They now agree BY CONSTRUCTION and not by assertion: both ask :func:`_unreadable_keywords`,
    which holds the only EXECUTABLE occurrence of ``not in _READABLE_KEYWORDS`` in this file. **A
    BRANCH THIS CHECK CANNOT FULLY READ HAS NO IDENTIFIED STATE** — ``state`` comes back ``None``,
    which every caller already treats as UNRECOGNISED, and the caller reports
    `CD-CALM-BRANCHES-006` **naming the keyword** rather than the generic sentence. It is the same
    answer :func:`_dial_bearing` gives about the same node, and it is reached through the same
    predicate.
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
        if isinstance(resolved, dict) and not _unreadable_keywords(resolved):
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
    limb_b_by_surface = {}
    for surface, schema in schemas.items():
        properties = schema.get("properties") or {}

        # ---- CD-CALM-ROOT-008 — *** RULE CC: THE ROOT PARTITION. THIS IS THE ARCHITECTURAL
        # CLOSE, AND IT RUNS BEFORE THE RECOGNISER BECAUSE IT DOES NOT USE ONE. *** ----------- #
        # `PO-DECISIONS-0028` ruling 1. Every root property is EXACTLY ONE of (a) a canonical
        # dial slot or (b) a declared non-dial property; anything else is a VIOLATION. See
        # :func:`_root_limb` for why the partition is exhaustive and `DECLARED LIMIT 17` for what
        # it does and does not cover.
        #
        # *** THE TWO PREMISES OF EXHAUSTIVENESS ARE ASSERTED HERE AND NOT ASSUMED. *** Rule CC
        # enumerates `schema["properties"]` and calls that "every root property there is". That
        # sentence is true only if (1) the root refuses undeclared keys and (2) nothing else at
        # the root can introduce or constrain a property. An unasserted premise is exactly how
        # `DECLARED LIMIT 4` came to claim "under any spelling" three times in a row.
        root_unreadable = sorted(key for key in schema
                                 if key not in _ROOT_STRUCTURAL_KEYWORDS)
        check.asserted(2)
        if root_unreadable:
            check.violation(
                here, 0, "CD-CALM-ROOT-008",
                f"{surface.value}: the contract ROOT declares {root_unreadable!r}, which is "
                f"outside this check's declared, closed set of root keywords "
                f"{sorted(_ROOT_STRUCTURAL_KEYWORDS)!r}. *** RULE CC ENUMERATES `properties` AND "
                "CALLS THAT EVERY ROOT PROPERTY THERE IS. A keyword like `patternProperties`, "
                "`allOf`, `if`, `dependentSchemas`, `unevaluatedProperties`, `$dynamicRef` — or "
                "one from a draft nobody has written — can admit or constrain a root key "
                "`properties` never names, and the partition would then be a partition of a "
                "SUBSET while claiming to be a partition of the whole. *** DENY BY DEFAULT: a "
                "root keyword this check has not priced makes RULE CC's exhaustiveness "
                "UNPROVED, and an unproved closure is reported, never assumed. See DECLARED "
                "LIMIT 17.",
            )
        if schema.get("additionalProperties") is not False:
            check.violation(
                here, 0, "CD-CALM-ROOT-008",
                f"{surface.value}: the contract ROOT does not declare "
                "'additionalProperties: false' (it declares "
                f"{schema.get('additionalProperties')!r}). *** RULE CC's SECOND PREMISE IS THAT A "
                "DOCUMENT CANNOT INTRODUCE A ROOT KEY THE CONTRACT DOES NOT DECLARE. *** Without "
                "that, a published envelope can carry a root property no partition ever "
                "examined, and every assertion below is about a document shape that is not the "
                "only one the gate admits.",
            )

        limbs = {}
        for name, sub in sorted(properties.items()):
            limbs[name] = _root_limb(name, sub)
            check.asserted()
            if limbs[name] is None:
                check.violation(
                    here, 0, "CD-CALM-ROOT-008",
                    f"{surface.value}: root property {name!r} is NEITHER limb of RULE CC. *** IT "
                    "IS NOT A CANONICAL DIAL SLOT *** — a canonical dial slot is spelled EXACTLY "
                    f"{CANONICAL_DIAL_SLOT!r}, that one key and no sibling keyword, and this one "
                    f"is spelled {sub!r}. *** AND ITS NAME IS NOT ON THIS CHECK'S FINITE, WRITTEN "
                    f"ALLOWLIST OF NON-DIAL ROOT PROPERTIES *** "
                    f"{sorted(NON_DIAL_ROOT_PROPERTIES)!r}. "
                    "*** THERE IS NO THIRD CASE AND NO RECOGNISER IS CONSULTED. *** This is NOT "
                    "a report that the property looks like a dial; it is a report that it is not "
                    "one of the two things a root property is ALLOWED to be. A dial spelled "
                    "'{\"enum\": [...]}', one whose discriminator is called `status`, one nested "
                    "past this check's depth cap and one carrying 'present: false' are all "
                    "refused HERE, by this one sentence, without any of them being recognised — "
                    "which is precisely what nine audits proved a recogniser cannot do "
                    "(CD-ASR-WO3-10, A310-F1/F2/F3; PO-DECISIONS-0028 ruling 1). "
                    "*** THE REMEDY IS NEVER TO ADD THE NAME TO THE ALLOWLIST TO GET A GREEN. *** "
                    "This instrument goes RED AND STAYS RED until a HUMAN rules on it: a third "
                    "dial slot is a PRODUCT decision (two dials, never blended, is standing "
                    "product — PO-DECISIONS-0026), and whether a new non-dial root property can "
                    "carry a rendering decision is product meaning and not an Engineer's to "
                    "guess (PBG-AUTH-005).",
                )

        canonical = sorted(name for name, limb in limbs.items() if limb == "a")
        limb_b_by_surface[surface] = sorted(
            name for name, limb in limbs.items() if limb == "b")
        check.note(f"{surface.value} RULE CC limb (a) CANONICAL DIAL SLOTS: {canonical}")
        check.note(f"{surface.value} RULE CC limb (b) DECLARED NON-DIAL ROOT PROPERTIES "
                   f"(each proved against the LIVE GATE below): {limb_b_by_surface[surface]}")

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

        # *** RULE CC's LIMB (a) AND THE DRIVEN SET MUST BE THE SAME SET. *** `found` admits a
        # `$ref` with siblings and limb (a) does not, so limb (a) is a SUBSET of `found` by
        # construction; asserting the equality is what makes "the matrix drives exactly the
        # properties RULE CC calls dial slots" a MEASUREMENT rather than a reading of the code.
        check.asserted()
        if set(canonical) != set(found):
            check.violation(
                here, 0, "CD-CALM-ROOT-008",
                f"{surface.value}: RULE CC limb (a) is {canonical!r} but the set this check "
                f"actually DRIVES through the gate is {sorted(found)!r}. Those must be the same "
                "set: a slot RULE CC calls canonical but the matrix never drives is a slot on "
                "which PID §3.2 is asserted and not measured, and a slot the matrix drives that "
                "RULE CC does not call canonical is a `$ref` carrying a sibling keyword, which "
                "in 2020-12 APPLIES and makes it a different schema (DECLARED LIMIT 13).",
            )
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
        # *** WHICH KEYWORD, NEW AT `16B-FIX-5` (`FX16`). *** `_branch_states` now withholds a
        # state from a branch carrying a keyword it cannot read, so this violation has a SECOND
        # cause and a report that named only the first would be false about the new one. The
        # predicate is the SAME FUNCTION the recogniser used — it is not re-derived here.
        illegible = {label: _unreadable_keywords(resolved)
                     for label, resolved, state, _ in branches
                     if state is None and _unreadable_keywords(resolved)}
        if unreadable:
            check.violation(
                here, 0, "CD-CALM-BRANCHES-006",
                f"{surface.value}: branches {unreadable!r} of '#/$defs/dial_reading.oneOf' do "
                "not resolve to a schema object declaring 'properties.state.const' as a string, "
                "*** OR DECLARE A KEYWORD THIS CHECK CANNOT READ (NEW AT 16B-FIX-5, FX16): "
                f"{illegible!r} ***. DENY BY DEFAULT: a branch this check cannot IDENTIFY is a "
                "branch it cannot DRIVE, and an undriven branch of the published union is a shape "
                "on which PID §3.2 is unguarded. Unrecognised is a VIOLATION, never a silence. "
                "*** AND THE TWO RECOGNISERS IN THIS FILE NOW AGREE ABOUT WHAT 'READABLE' MEANS "
                "BY CONSTRUCTION: `_dial_bearing` and `_branch_states` both ask "
                "`_unreadable_keywords`, which holds the ONLY EXECUTABLE occurrence of "
                "`not in _READABLE_KEYWORDS` in the file. Before this increment the branch "
                "recogniser had NO inversion at all and accepted "
                "`{'properties': {'state': {'const': 'UNKNOWN'}}, 'patternProperties': "
                "{...}}` silently (CD-ASR-WO3-09 F2). *** See DECLARED LIMIT 14.",
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

        # ---- CD-CALM-CANON-009 — *** CC-2: THE CANONICAL PATH, ENFORCED. *** ------------ #
        # `PO-DECISIONS-0028` ruling 1: the discriminator lives at `properties.state`, at depth
        # ONE of `#/$defs/dial_reading`, pinned per branch at `properties.state.const`. The
        # contracts now MANDATE it (`required: ["state"]` plus a normative description clause);
        # this asserts it, because *** A `description` IS NOT AN ENFORCEMENT POINT AND THIS
        # CONTRACT ALREADY CARRIES A SUPERSEDED NOTE SAYING SO IN ITS OWN WORDS *** —
        # `absent_data_detail_level`'s description records 16A, where the guarantee was "asserted
        # only in PROSE" while the gate admitted a calm UNKNOWN dial on both surfaces.
        check.asserted(3)
        if dial_union.get("additionalProperties") is not False:
            check.violation(
                here, 0, "CD-CALM-CANON-009",
                f"{surface.value}: '#/$defs/dial_reading' does not declare "
                f"'additionalProperties: false' (it declares "
                f"{dial_union.get('additionalProperties')!r}). The canonical dial shape is a "
                "CLOSED object: without this a dial can carry a key no branch declares, and the "
                "shape CC-3's value check ranges over is no longer closed.",
            )
        union_properties = dial_union.get("properties")
        if not (isinstance(union_properties, dict)
                and isinstance(union_properties.get("state"), dict)):
            check.violation(
                here, 0, "CD-CALM-CANON-009",
                f"{surface.value}: '#/$defs/dial_reading' does not declare 'properties.state' as "
                "a subschema. *** THE CANONICAL PATH FOR THE DISCRIMINATOR IS "
                "`properties.state`, AT DEPTH ONE, AND NOWHERE ELSE (PO-DECISIONS-0028 ruling "
                "1). *** A dial that carries its discriminator anywhere else is refused at "
                "contract validation, and a contract that stops declaring the canonical path has "
                "removed the thing every check below reads.",
            )
        if "state" not in [name for name in (dial_union.get("required") or [])
                           if isinstance(name, str)]:
            check.violation(
                here, 0, "CD-CALM-CANON-009",
                f"{surface.value}: '#/$defs/dial_reading' does not REQUIRE 'state' (its required "
                f"list is {dial_union.get('required')!r}). *** THIS IS THE MANDATE "
                "PO-DECISIONS-0028 RULING 1 ORDERS INTO THE ENVELOPE CONTRACT ITSELF: 'every dial "
                "carries a well-formed `state` at a CANONICAL PATH ... with present + freshness "
                "semantics REQUIRED by the schema'. *** Left to be IMPLIED by the branches, it is "
                "an accident of the current branch set; stated as an assertion, it is a property "
                "of the contract that survives an edit to any one branch.",
            )

        for label, resolved, _state, branch_dropped in branches:
            check.asserted(4)
            if resolved is None or branch_dropped:
                check.violation(
                    here, 0, "CD-CALM-CANON-009",
                    f"{surface.value}: branch {label!r} could not be read as a schema object "
                    "this check can judge (it does not resolve, or its `$ref` chain discarded an "
                    "asserting sibling — DECLARED LIMIT 13). *** THE CANONICAL PATH IS UNPROVED "
                    "ON THIS BRANCH, AND UNPROVED IS A VIOLATION AND NEVER A SILENCE. ***",
                )
                continue
            if resolved.get("additionalProperties") is not False:
                check.violation(
                    here, 0, "CD-CALM-CANON-009",
                    f"{surface.value}: branch {label!r} does not declare "
                    f"'additionalProperties: false' (it declares "
                    f"{resolved.get('additionalProperties')!r}). An open branch admits keys no "
                    "branch declares — including a second discriminator beside the canonical "
                    "one — so the alphabet CC-3 quantifies over is not closed.",
                )
            if "state" not in [name for name in (resolved.get("required") or [])
                               if isinstance(name, str)]:
                check.violation(
                    here, 0, "CD-CALM-CANON-009",
                    f"{surface.value}: branch {label!r} does not REQUIRE 'state' (its required "
                    f"list is {resolved.get('required')!r}). A branch that permits its "
                    "discriminator to be absent admits a document with no state at all, and a "
                    "document with no state has proved nothing about present-or-fresh.",
                )
            branch_state = None
            branch_properties = resolved.get("properties")
            if isinstance(branch_properties, dict):
                state_sub = branch_properties.get("state")
                state_resolved, state_dropped = (
                    _resolve(schema, state_sub) if isinstance(state_sub, dict) else (None, []))
                if isinstance(state_resolved, dict) and not state_dropped and isinstance(
                        state_resolved.get("const"), str):
                    branch_state = state_resolved["const"]
            if branch_state is None:
                check.violation(
                    here, 0, "CD-CALM-CANON-009",
                    f"{surface.value}: branch {label!r} does not declare "
                    "'properties.state.const' as a STRING. *** THIS IS ITS OWN NAMED VIOLATION "
                    "AND IS DELIBERATELY NOT FOLDED INTO CD-CALM-BRANCHES-006: *** that code "
                    "reports a branch whose STATE could not be identified, which reads as a "
                    "recognition failure. This one reports that the branch DEPARTS FROM THE "
                    "CANONICAL SHAPE THE CONTRACT MANDATES — a `const` is what pins one branch to "
                    "one state, and an `enum`, a `$ref` to a vocabulary, or no `state` subschema "
                    "at all makes the branch set something other than a partition of the state "
                    "alphabet. CC-3's value check is only sufficient over a closed alphabet.",
                )
            stamps = _required_timestamp_properties(schema, resolved)
            if stamps is None:
                check.violation(
                    here, 0, "CD-CALM-CANON-009",
                    f"{surface.value}: the contract declares no '#/$defs/{UTC_TIMESTAMP_DEF}' "
                    "definition, so this check cannot tell which of a branch's required "
                    "properties is a FRESHNESS STAMP. The freshness half of "
                    "'present and fresh' is unmeasurable on this contract.",
                )
            elif not stamps:
                check.violation(
                    here, 0, "CD-CALM-CANON-009",
                    f"{surface.value}: branch {label!r} (state {branch_state!r}) REQUIRES NO "
                    f"PROPERTY TYPED '#/$defs/{UTC_TIMESTAMP_DEF}'. *** A BRANCH THAT REQUIRES NO "
                    "FRESHNESS STAMP CANNOT PROVE FRESHNESS, AND CD-AC-001's OWN WORDS ARE "
                    "'missing OR STALE input never renders as calm'. *** The stamp is asserted by "
                    "TYPE and not by NAME on purpose — MEASURED, VALUE and DEGRADED require "
                    "`as_of_utc` while UNKNOWN requires `since_utc`, so a fixed name would have "
                    "been a fifth spelling patch. A stamp the branch merely PERMITS does not "
                    "count: the document that omits it is still admitted.",
                )

            # ---- CD-CALM-FRESH-010 — *** CC-3: THE AFFIRMATIVE VALUE CHECK OVER THE NOW-CLOSED
            # ALPHABET. THIS IS PO-DECISIONS-0027 RULING 5, MADE ACHIEVABLE. *** ----------- #
            # *** A branch may reference the calm-bearing `#/$defs/detail_level` IF AND ONLY IF
            # its `properties.state.const` is a member of PRESENT_STATES **and** it requires a
            # freshness stamp. EVERY OTHER BRANCH MUST reference a vocabulary from which `calm`
            # is ABSENT. ***
            #
            # **THAT IS THE AFFIRMATIVE FORM AND IT IS WHY THIS IS NOT A DENYLIST.** It does not
            # ask "is this state on my list of bad ones?" — the question nine audits defeated by
            # naming a state nobody had listed. It asks "has this branch PROVED PRESENT AND
            # FRESH?", and a branch that has not gets a vocabulary in which `calm` is
            # UNREPRESENTABLE. A never-before-named state must arrive as a NEW BRANCH; a new
            # branch's state is NOT in PRESENT_STATES; therefore it CANNOT CARRY `calm` — **BY
            # CONSTRUCTION, OVER A CLOSED SET, AND NOT BY RECOGNITION OVER AN OPEN ONE.**
            check.asserted()
            calm_ok = _calm_admissible(schema, resolved)
            proved = branch_state in PRESENT_STATES and bool(stamps)
            if calm_ok is None:
                check.violation(
                    here, 0, "CD-CALM-FRESH-010",
                    f"{surface.value}: branch {label!r} (state {branch_state!r}) declares a "
                    f"{DETAIL_LEVEL!r} this check cannot read as a closed vocabulary — it is "
                    "missing, it does not resolve, its `$ref` chain discarded an asserting "
                    "sibling, or it declares no `enum`. *** DENY BY DEFAULT: a branch whose level "
                    "vocabulary cannot be read is a branch on which 'calm is unrepresentable' is "
                    "UNPROVED, and unproved is a violation. *** The vocabulary is judged by its "
                    "VALUES and never by the name of the `$def` it comes from — a check that "
                    "reads the `$ref` target NAME passes a tree where `calm` was put back inside "
                    "the target's own enum, which is CD-PL-F169 and CD-ASR-WO3-02 F06/F07.",
                )
            elif calm_ok and not proved:
                why = []
                if branch_state not in PRESENT_STATES:
                    why.append(
                        f"its state {branch_state!r} is NOT in this check's declared "
                        f"PRESENT_STATES {sorted(PRESENT_STATES)!r}, so nothing about this branch "
                        "asserts the data is PRESENT"
                    )
                if not stamps:
                    why.append(
                        f"it REQUIRES no property typed '#/$defs/{UTC_TIMESTAMP_DEF}', so nothing "
                        "about this branch asserts the data is FRESH"
                    )
                check.violation(
                    here, 0, "CD-CALM-FRESH-010",
                    f"{surface.value}: branch {label!r} MAY CARRY {CALM!r} AND HAS NOT PROVED "
                    "PRESENT-AND-FRESH — " + "; and ".join(why) + ". *** THIS IS "
                    "PO-DECISIONS-0027 RULING 5's COMPLETION CONDITION, FAILING: 'a dial that "
                    "cannot prove present-and-fresh is REFUSED BY CONSTRUCTION; a dial in a "
                    "NEVER-BEFORE-NAMED STATE, carrying calm, is REFUSED.' *** The remedy is to "
                    f"point this branch's {DETAIL_LEVEL!r} at a vocabulary WITHOUT {CALM!r} "
                    "(#/$defs/absent_data_detail_level is the one this contract declares for "
                    "exactly that), never to add the state to PRESENT_STATES. **WHETHER A NEW "
                    "STATE MEANS THE DATA IS PRESENT IS PRODUCT MEANING AND NOT AN ENGINEER'S TO "
                    "DECIDE (PBG-AUTH-005)** — and the failure is asymmetric: guess 'present' and "
                    "`calm` is admitted over an absence, which is PID §3.2 broken in silence.",
                )
            elif proved and not calm_ok:
                check.violation(
                    here, 0, "CD-CALM-FRESH-010",
                    f"{surface.value}: branch {label!r} (state {branch_state!r}) HAS proved "
                    f"present-and-fresh — its state is in PRESENT_STATES and it requires the "
                    f"freshness stamp(s) {stamps!r} — but its {DETAIL_LEVEL!r} vocabulary does "
                    f"NOT contain {CALM!r}. *** THIS IS THE VACUITY DIRECTION AND IT CARRIES "
                    "EQUAL WEIGHT. *** PID §4 makes `calm` the base case — 'calm = dial + one "
                    "line' — so a contract in which a real reading backed by real inputs and a "
                    "real timestamp CANNOT render as calm is not holding PID §3.2, it is "
                    "enforcing silence, and every refusing arm in this instrument would be "
                    "satisfied vacuously by it. Same argument as CD-CALM-VACUITY-000, made "
                    "structurally instead of behaviourally.",
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

    # ---- CD-CALM-ROOT-008 — *** RULE CC LIMB (b)'s AFFIRMATIVE PROOF, DRIVEN THROUGH THE
    # LIVE GATE. THIS IS WHAT STOPS THE ALLOWLIST BEING A DENYLIST IN AN ALLOWLIST'S CLOTHES. ***
    # ------------------------------------------------------------------------------------- #
    # `PO-DECISIONS-0028` ruling 1, verbatim: *"within that closed shape the value check is
    # sufficient."* A written list of names proves nothing on its own — somebody has to show that
    # the named properties really cannot carry a rendering decision. So for EACH allowlisted
    # non-dial root property, on EACH surface, this replaces that property's value with a
    # calm-carrying object in an otherwise ADMITTED envelope and REQUIRES the gate to REFUSE.
    #
    # *** A ROOT PROPERTY THAT ADMITS A CALM-CARRYING OBJECT IS NOT A NON-DIAL PROPERTY, WHATEVER
    # THE ALLOWLIST SAYS. *** It is finite and it is counted: the allowlist x 2 surfaces x
    # :data:`CALM_BEARING_PROBES`, plus one ADMITTING control per surface.
    #
    # **THE CONTROL IS NOT DECORATION AND IS NOT OPTIONAL.** If the unmutated baseline envelope
    # were itself refused, every refusal below would be a refusal of the baseline and this whole
    # section would be vacuous — an instrument that fails on everything is a brick, not a guard.
    # It is the same argument `CD-CALM-VACUITY-000` makes about the proposition table.
    for surface in EnvelopeSurface:
        schema = schemas[surface]
        slots = slots_by_surface[surface]
        baseline = _envelope(
            surface.value, slots, slots[0], dict(fillers[surface]), fillers[surface])
        baseline["schema_version"] = ENVELOPE_SCHEMA_VERSION

        check.asserted()
        try:
            refuse_unless_publishable(copy.deepcopy(baseline), surface=surface)
        except Exception as exc:
            check.violation(
                here, 0, "CD-CALM-ROOT-008",
                f"{surface.value}: *** THE LIMB (b) BASELINE ENVELOPE IS ITSELF REFUSED *** "
                f"({type(exc).__name__}: {str(exc).splitlines()[0][:160]}), so every refusal in "
                "this section would be a refusal of the BASELINE and not of the calm-carrying "
                "object put into it. RULE CC limb (b) is UNPROVED on this surface. A check whose "
                "control does not admit cannot tell 'the forbidden thing is impossible' from "
                "'everything is impossible'.",
            )
            continue
        check.note(f"{surface.value} RULE CC limb (b) CONTROL: the unmutated baseline envelope "
                   "is ADMITTED, so the refusals below are attributable to the probe")

        # ---- *** limb (b)'s STRUCTURAL half. NEW AT `16D-GATE-FRESHNESS`, CLOSING
        # `CD-ASR-WO3-11` `A311-F1` FAIL-CLOSED. *** ------------------------------------------ #
        # The probes below are a SAMPLE OF TWO SHAPES and the auditor defeated them with a third
        # — an ARRAY of closed objects carrying `#/$defs/detail_level`, ONE CONTAINER DEEPER than
        # this increment's own arm `CC-H`, on which BOTH probes are still refused and the live gate
        # ADMITTED calm at a root position on both surfaces. **THE REMEDY IS NOT A THIRD PROBE**
        # (that moves the census game to the probe alphabet); it is a DECISION PROCEDURE over the
        # property's OWN CLOSED SUBSCHEMA, and it is :func:`_can_carry_detail_level`.
        # **THE PROBES ARE RETAINED AS THE PAIRED BEHAVIOURAL CONTROL**, which is the auditor's own
        # prescription: this limb says what the CONTRACT ADMITS, the probes say what the GATE DOES,
        # and a disagreement between them is itself a finding.
        declared_root_properties = schema.get("properties")
        if not isinstance(declared_root_properties, dict):
            declared_root_properties = {}
        for name in limb_b_by_surface[surface]:
            check.asserted()
            capable = _can_carry_detail_level(
                schema, declared_root_properties.get(name))
            if capable is True:
                check.violation(
                    here, 0, "CD-CALM-ROOT-008",
                    f"{surface.value}: *** RULE CC LIMB (b) CLAIMS THE ROOT PROPERTY {name!r} IS "
                    "AFFIRMATIVELY PROVED INCAPABLE OF CARRYING A `detail_level`, AND ITS OWN "
                    "SUBSCHEMA ADMITS AN INSTANCE THAT CARRIES ONE. *** The claim is false as "
                    "written, whatever the behavioural probes below report — they are a SAMPLE OF "
                    "TWO SHAPES and `CD-ASR-WO3-11`'s arm H defeated exactly that sample with a "
                    "third. **THE REMEDY IS NEVER TO REMOVE THIS ASSERTION, THE NAME OR A PROBE "
                    "TO GET A GREEN:** narrow the property's subschema until it cannot carry a "
                    "rendering decision, or take the widening to the Product Authority "
                    "(PBG-AUTH-005). A root property that CAN carry a rendering decision is a "
                    "dial slot nobody declared.",
                )
            elif capable is None:
                check.violation(
                    here, 0, "CD-CALM-ROOT-008",
                    f"{surface.value}: RULE CC LIMB (b) IS UNDECIDABLE FOR THE ROOT PROPERTY "
                    f"{name!r} — its subschema declares a keyword, a `$ref` chain, a `type` token "
                    "or a nesting this decision procedure CANNOT COMPLETELY ACCOUNT FOR, so "
                    "whether a conforming instance could carry a `detail_level` is UNKNOWN. "
                    "**'I COULD NOT TELL' AND 'IT CANNOT CARRY ONE' ARE DIFFERENT ANSWERS AND "
                    "ONLY ONE OF THEM IS SAFE** (PO-DECISIONS-0026 ruling 10). This check does "
                    "not pass on the first: a false positive costs one seat one look at one "
                    "contract; a false negative costs the constitution.",
                )
            else:
                check.note(
                    f"{surface.value}/<root>/{name}: limb (b) STRUCTURAL — the property's own "
                    "closed subschema admits no instance carrying a `detail_level`, at any "
                    "depth, through any container")

        for name in limb_b_by_surface[surface]:
            for variant, probe in CALM_BEARING_PROBES:
                candidate = copy.deepcopy(baseline)
                candidate[name] = copy.deepcopy(probe)
                label = f"{surface.value}/<root>/{name}/calm-bearing-{variant}"
                check.asserted()
                try:
                    returned = refuse_unless_publishable(candidate, surface=surface)
                except PublicationRefused as refused:
                    check.note(f"{label}: REFUSED [{refused.reason_class}] at "
                               f"{refused.pointer or '<root>'}")
                except Exception as other:
                    check.violation(
                        here, 0, "CD-CALM-ROOT-008",
                        f"{label}: the gate raised {type(other).__name__}: "
                        f"{str(other).splitlines()[0][:160]}. That is neither an admission nor a "
                        "declared refusal, and a check cannot read a crash as a refusal "
                        "(CD-PL-F74).",
                    )
                else:
                    check.violation(
                        here, 0, "CD-CALM-ROOT-008",
                        f"{label}: *** THE LIVE GATE ADMITTED A CALM-CARRYING OBJECT AT THE ROOT "
                        f"PROPERTY {name!r}, WHICH RULE CC's LIMB (b) DECLARES IS NOT A DIAL. *** "
                        f"The document put {probe!r} in its place and "
                        f"refuse_unless_publishable returned {returned!r}. **A ROOT PROPERTY THAT "
                        "ADMITS A CALM-CARRYING OBJECT IS NOT A NON-DIAL PROPERTY, WHATEVER THIS "
                        "CHECK'S ALLOWLIST SAYS** — the allowlist is a claim about the contract "
                        "and the contract has stopped making it true. Either the contract widened "
                        f"{name!r} until it can carry a rendering decision, or the name was never "
                        "safe to allowlist. *** THE REMEDY IS NEVER TO REMOVE THE PROBE OR THE "
                        "NAME TO GET A GREEN: *** narrow the property back, or take the change to "
                        "the Product Authority (PBG-AUTH-005). PO-DECISIONS-0028 ruling 1: "
                        "'within that closed shape the value check is sufficient' — this IS that "
                        "value check, and it has just failed.",
                    )

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
    check.note(
        "AND THE STALENESS HALF NOW EXISTS, ELSEWHERE, AND IS STILL NOT ASSERTED HERE: WO-3 "
        "increment 16D added a FOURTH REFUSAL STAGE to refuse_unless_publishable "
        "(REFUSAL_STALE_CALM), which compares published_utc against each calm-bearing node's "
        "own oldest stamp against the root's declared staleness_window_seconds, computed purely "
        "from the document (PO-DECISIONS-0029 ruling 1). THIS INSTRUMENT DOES NOT ASSERT IT and "
        "the sentence above is unchanged and still true of THIS ROW. The freshness stage's own "
        "acceptance evidence is tests/test_envelope_freshness.py. A guard that is asserted "
        "somewhere else is not a guard this row may take credit for."
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
