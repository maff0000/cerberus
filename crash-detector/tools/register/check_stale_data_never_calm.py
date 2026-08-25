#!/usr/bin/env python3
"""CD-RT-001-STALE-DATA-NEVER-CALM — the LIVE GATE refuses a STALE calm dial.

    python3 tools/register/check_stale_data_never_calm.py --root <subject tree>

CRITERION: `CD-AC-001` — *"Missing **or stale** input never renders as calm."* — and `PID §3.2`,
which is CONSTITUTIONAL in the same words. Authority: `PO-DECISIONS-0030` **ruling 1**:

    "Q35(a) — YES, the fourth refusal stage gets its OWN Required Test Register row, and it
     lands BEFORE 16C. This is ruling 9's principle (a constitutional guarantee is carried by a
     REGISTER-WIRED instrument, never test-only) applied to the freshness stage: the guarantee
     is proven today, but proven in tests is not proven in the register. Register-wire it — its
     own row, a negative control the gate reads, failing if stale-carrying-calm is ever
     admitted."

===========================================================================================
**WHY THIS INSTRUMENT EXISTS, IN ONE PARAGRAPH.** WO-3 increment `16D-GATE-FRESHNESS` added a
FOURTH REFUSAL STAGE to `refuse_unless_publishable` (`REFUSAL_STALE_CALM`), which compares the
root's `published_utc` against each calm-bearing node's own OLDEST stamp against the root's
declared `staleness_window_seconds`, computed purely from the document. An independent auditor
set out to break it and could not. **But nothing the register read would have noticed if it
were deleted.** MEASURED by `CD-ASR-WO3-12` (`A312-F1`), reproduced independently by
`PROJECT_LEAD_SEAT_06`, and reproduced a THIRD time by this seat before a line of this file was
written: on a tree with the entire fourth stage removed (`plants/WO3-INC16D/
D1-THE-FOURTH-STAGE-REMOVED.patch`, `git apply` rc=0 TAKEN AND CHECKED), **all thirty of the
register's `execute:` lines exit with a per-line rc list that is `diff`-IDENTICAL to the clean
tip — `TOTAL lines=30 rc0=19 nonzero=11` on both** — while the live gate ADMITS a dial stamped
`1970-01-01` carrying `calm` on BOTH surfaces. The only witness that moved was
`tests/test_envelope_freshness.py` (14 failed, 78 passed), a file **no `execute:` line named**,
against **41 distinct `tests/test_*.py` paths the register DOES name.** A memorial, not a
guard. `required-tests.yaml` line ~242 already carries a memorial about a file in this exact
position. This file is the guard.
===========================================================================================

**IT IS BEHAVIOURAL AND NOT STRUCTURAL, AND THAT IS THE WHOLE DESIGN.** It does not read the
stage's source text, does not grep for `REFUSAL_STALE_CALM`, and does not assert that any
function is called from anywhere. It builds candidate envelopes and puts them through
`crash_detector.publication.envelope_contract.refuse_unless_publishable` — **the function the
product itself calls before it writes anything** (`src/crash_detector/publication/publish.py`
lines 276-277, on both surfaces) — and records what the gate actually did. A structural read is
precisely what let this class of defect through repeatedly on this project (`CD-PL-F169`,
`CD-ASR-WO3-02` F06/F07, `CD-ASR-WO3-03`).

Register instruments on this project ARE permitted to import the application — MEASURED, five
already do: `check_exact_type_admission`, `check_engine_no_witness_reach`,
`check_no_numeric_default`, `check_judgement_path_doors` and the sibling row's
`check_missing_data_never_calm`. (`CD-RT-014`'s *"the probe must not import the application"*
rule binds `tools/probe/external_probe.py` and nothing else.)

===========================================================================================
WHAT IS ASSERTED — AND THE ADMITTING ROWS CARRY EQUAL WEIGHT
===========================================================================================

*** THE VACUITY DIRECTION IS EQUALLY A VIOLATION OF THIS ROW, AND IT IS THE HALF THIS
PROJECT'S HISTORY SAYS GETS MISSED. *** A freshness stage that refused EVERYTHING would satisfy
PID §3.2 vacuously by making the dial incapable of ever reading `calm`, and `calm` on a fresh
reading backed by real inputs is the entire reason `calm` exists (PID §4). So every refusing
row here is PAIRED with an admitting one, in the same run, on the same tree, from the same
builder:

    LIMB A — THE LIVE GATE, THROUGH THE FRONT DOOR (`refuse_unless_publishable`), on every
    surface `EnvelopeSurface` declares, at every CANONICAL DIAL SLOT the contract declares:

        calm dial stamped far in the past            ->  MUST REFUSE  [STALE_CALM]
        calm dial stamped in the FUTURE              ->  MUST REFUSE  [STALE_CALM]
        calm dial exactly ONE MICROSECOND past the
          declared window                            ->  MUST REFUSE  [STALE_CALM]
        calm dial aged EXACTLY the declared window   ->  MUST ADMIT   *** VACUITY ***
        calm dial well inside the window             ->  MUST ADMIT   *** VACUITY ***
        STALE dial rendering `elevated`              ->  MUST ADMIT   *** VACUITY ***
        STALE dial rendering `acute`                 ->  MUST ADMIT   *** VACUITY ***

    LIMB B — THE STAGE ITSELF, DRIVEN DIRECTLY, for the propositions the CLOSED CONTRACT makes
    UNREACHABLE through the front door. **THIS IS NOT A CONVENIENCE AND IT IS DECLARED LIMIT 3.**
    On the shipped contracts the ONLY node that can carry `detail_level: "calm"` is a canonical
    dial slot in its `VALUE` branch — MEASURED: `#/$defs/contribution` is closed and declares no
    `detail_level`, `degraded_inputs` is `#/$defs/source_id_list` (an array of plain strings),
    and the root declares `additionalProperties: false`. So a document that puts a calm node
    anywhere ELSE is refused at STAGE 3 as `SCHEMA_VIOLATION` and never reaches stage 4 at all.
    An instrument that only used the front door therefore **could not tell the node walk apart
    from an implementation that reads the two dial slots by name** — which is the exact
    implementation `plants/WO3-INC16D/D3-SLOT-READING-INSTEAD-OF-NODE-WALK.patch` plants, and
    the exact defect class that lost eleven consecutive audit rounds on this row. Limb B drives
    `_refuse_stale_calm` directly, exactly as `tests/test_envelope_freshness.py` already does
    and for the reason that file already states.

        a calm node at a NON-DIAL root property     ->  MUST REFUSE at ITS OWN pointer
        a calm node TWO CONTAINERS DEEP in an array ->  MUST REFUSE at ITS OWN pointer
        a calm node inside a dial's `contributions` ->  MUST REFUSE at ITS OWN pointer
        the same three positions, FRESH             ->  MUST NOT REFUSE  *** VACUITY ***
        a calm node whose OLDEST stamp is stale and
          which carries two FRESHER siblings        ->  MUST REFUSE, naming the OLDEST key
        a calm node whose stamps are ALL fresh      ->  MUST NOT REFUSE  *** VACUITY ***
        a calm node with NO stamp at all            ->  MUST REFUSE  (fail closed)
        a calm node with a `*_utc` that will not
          parse, beside a fresh stamp               ->  MUST REFUSE  (fail closed)
        a root with no usable `published_utc`       ->  MUST REFUSE  (fail closed)
        a root with no usable window (absent, zero,
          negative, boolean, string, non-finite)    ->  MUST REFUSE  (fail closed)
        a root with a usable window and a fresh
          calm node                                 ->  MUST NOT REFUSE  *** VACUITY ***

===========================================================================================
*** THE DECLARED SCOPE OF THIS GUARD — READ THIS BEFORE READING A CLEAN RUN ***
`PO-DECISIONS-0030` ruling 2. Said identically here, in
`contracts/execution/CD-RT-001-STALE-DATA-NEVER-CALM.md` and in `required-tests.yaml`
(`CD-RULE-004`, three places).
===========================================================================================

**THE GATE ENFORCES DOCUMENT-INTERNAL FRESHNESS AND NOTHING WIDER.** What it computes is
`published_utc` MINUS the calm-bearing node's oldest stamp, against the window THE SAME
DOCUMENT declares. That is a claim about the document's INTERNAL COHERENCE — *a dial cannot be
older than its declared window relative to its own declared publication instant* — and it is
not a claim about ACTUAL freshness.

**IT CANNOT CATCH A SOURCE THAT CONSISTENTLY LIES ABOUT ITS OWN STAMP.** A feed that stamps
every reading `now()` regardless of the true age of the data underneath it is internally
consistent and PASSES THIS GATE. So is a uniformly time-shifted envelope: MEASURED by
`CD-ASR-WO3-12` (`A312-F3`) at the target tip with an ordinary 600-second window,
`as_of_utc` = `published_utc` = `1970-01-01T00:00:00Z` is **ADMITTED on both surfaces**. A
replayed envelope, a stopped publisher, a stuck detector clock and a backfill run all produce
exactly that document. **Nothing in a document can prove that about itself.**

*** THAT IS NOT "OUTSIDE ENFORCEMENT" AND IT IS NOT "PERMANENTLY UNENFORCEABLE". THE PRODUCT
AUTHORITY RULED THE OPPOSITE, AND THIS PARAGRAPH IS THE RULING AND NOT THIS SEAT'S OPINION. ***
Source honesty is the SAME CLASS as the `A311-F1` forgery and it has the SAME answer, already
ruled in the THREE-TIER PERIMETER (`PO-DECISIONS-0018`/`0019`, `BLUEPRINT §17` `CD-BP-005`):

  · **PREVENTION** — what is DOCUMENT-INTERNAL is prevented AT THE GATE. That is this stage,
    and that is what this row guards.
  · **DETECTION** — a source that lies about its own freshness is caught ONE TIER OUT, by
    **WITNESS DIVERGENCE + PROVENANCE, `CD-AC-018`**, where a source's CLAIMED freshness is
    corroborated against independent witnesses and DIVERGENCE IS THE ALARM.
  · **WHEN IT IS OWED: AT WO-3**, when real sources and their witnesses land. It is not
    deferred indefinitely and it is not written off.

**AND THE HONESTY OBLIGATION THAT CREATES FOR 16C, RECORDED HERE AND DELIBERATELY NOT BUILT
HERE.** 16C's detector-side liveness marking carries the obligation that the stamps it produces
are **PROVENANCE-BACKED AND WITNESS-CORROBORATABLE**. **16C IS NOT IN THIS INCREMENT.** There
is no `feed_liveness` slot here, no dead-feed detector, and no liveness marking: this file
records the obligation and builds none of it.

**A DECLARED LIMIT THAT SAYS "WE CANNOT DO THIS" WHERE THE TRUTH IS "THIS IS DONE AT THE NEXT
TIER, AT WO-3" IS A FALSE RESIDUAL**, and four sentences on the sibling row have already been
superseded for being false in exactly that reassuring direction.

===========================================================================================
DECLARED LIMITS — THIS ROW'S OWN SEQUENCE, 1 TO 11
===========================================================================================
**DECLARED LIMIT NUMBERS ARE PER REGISTER ROW, NOT PER FILE** (the convention the sibling row
`CD-RT-001-MISSING-DATA-NEVER-CALM` states in all three of its places, whose own sequence runs
1-20). These eleven are `CD-RT-001-STALE-DATA-NEVER-CALM`'s and they are said identically in
this header, in `contracts/execution/CD-RT-001-STALE-DATA-NEVER-CALM.md` and in
`required-tests.yaml`. **Quote the row id with the number.**

  1. **IT JUDGES THE CONTRACT THE GATE ACTUALLY LOADS, WHICH IS CONFIGURABLE.**
     `envelope_contract.contracts_dir()` honours `$CD_CONTRACTS_DIR`, so the live gate can be
     pointed at a widened copy while this repository's contracts are byte-intact.
     **WHAT THIS CHECK DOES ABOUT IT:** it exits `3` unless the contracts the gate resolves are
     `<root>/contracts`, and prints their SHA-256 at every run (`CD-PL-F98`). **IT DOES NOT
     PREVENT THE ROUTE. NOT PROVED TO BE CARRIED ANYWHERE.** EXECUTABLE:
       `CD_CONTRACTS_DIR=/tmp/anything python3 tools/register/check_stale_data_never_calm.py --root .`
     -> `PRECONDITION_NOT_MET`, exit 3, never a pass and never a skip.

  2. **THE ENVELOPE ROOT SKELETON IS BUILT FROM THE CONTRACT'S OWN `required` LIST, AND THE
     DIAL FROM ITS OWN BRANCH — BUT THE VALUE VOCABULARY IS A CLOSED WRITTEN LIST.** Each
     property is filled with the FIRST of `SYNTHETIC_VALUES` that the property's OWN subschema
     accepts, decided by `jsonschema` — the same library the gate validates with — and NEVER by
     the property's NAME. A required property that none of them satisfies makes this check
     REPORT (`CD-STALE-BUILD-008`) and exit 1.

     *** ITS CLOSING SENTENCE WAS FALSE IN THE REASSURING DIRECTION. SUPERSEDED AT `16F` ON
     `A313-F1`, STATED AND NOT ERASED (`CD-RULE-004`, `PBG-CONT-003`). ***

     > **WHAT IT SAID, VERBATIM, IN ALL THREE PLACES IT WAS SAID:** *"DENY BY DEFAULT, so it is
     > not an escape; it IS a maintenance cost."*

     **THAT SENTENCE IS ABOUT THE WRONG HALF OF THE PROBLEM.** Deny-by-default governs what
     happens when a property CANNOT be built: the check reports `CD-STALE-BUILD-008` and exits
     1. **IT SAYS NOTHING WHATEVER ABOUT THE PROPERTIES THAT CAN BE BUILT AND ARE THEN DRIVEN
     AT EXACTLY ONE VALUE EACH, AND THAT IS WHERE THE ESCAPE WAS.** All 72 documents this
     instrument drove at `a9e19c3` carried THE SAME SINGLE VALUE FOR EVERY ROOT PROPERTY — ONE
     POINT in the space of documents the contract admits, while the guarantee quantifies over
     ALL of them. MEASURED by `CD-ASR-WO3-13` (`A313-F1`, HIGH), reproduced by
     `PROJECT_LEAD_SEAT_07`, and reproduced a THIRD time by `CD-ENG-WO3-14` before a line of
     `16F` was written: `W5G` (five lines, `if len(candidate.get("inputs_used") or []) > 1:
     return`) and `W5B2` (three lines, `if candidate.get("regime") == CALM_DETAIL_LEVEL:
     return`) each leave the live gate ADMITTING a 1970-stamped calm dial on BOTH surfaces
     while all 32 of this register's `execute:` lines are `diff`-identical to the clean tip.

     **WHAT IS TRUE INSTEAD, AT `16F`.** The vocabulary is still a written list and that half of
     the limit stands. What has changed is that the instrument no longer drives ONE value per
     property: the INVARIANCE PASS varies every root property, and every non-stamp property of
     the calm-bearing node, across that vocabulary, and requires the verdict not to move. The
     residual is `DECLARED LIMIT 9` — a SAMPLE of an unbounded set — and it is stated there
     rather than here. EXECUTABLE: add a required root property with
     `{"type": "string", "pattern": "^ZZZ"}` to either contract and this instrument goes RED.

  3. **LIMB B DRIVES `_refuse_stale_calm` DIRECTLY AND THEREFORE PROVES NOTHING ABOUT WHETHER
     THE GATE CALLS IT.** That is LIMB A's job and only LIMB A's. The two limbs are separable
     and each is separately defeatable: MEASURED, `D1` (the whole stage unreachable from the
     gate) costs LIMB A and costs LIMB B **nothing**, and `D3` (the slot-reading
     implementation) costs LIMB B and costs LIMB A **nothing**. **A REPORT OF THIS ROW THAT
     QUOTES ONE LIMB IS HALF A REPORT.** And limb B is NAME-COUPLED to a private symbol,
     `_refuse_stale_calm`: renaming it makes this instrument exit `3`, deliberately, because a
     check that cannot find its authentic target must fail and never wave through
     (`PBG-CI-002`). That coupling is the same trade `DECLARED LIMIT 12` of the sibling row
     prices and it is ACCEPTED for the same reason.

  4. **IT PROVES NOTHING ABOUT A `VALUE` READING THAT SHOULD NOT HAVE BEEN A `VALUE`, AND
     NOTHING ABOUT THE MISSING HALF.** A dial whose inputs were missing but which was
     constructed as `VALUE` with a fabricated score and a fresh stamp renders calm legitimately
     as far as THIS row is concerned, and this check ADMITS IT — the vacuity rows say so out
     loud, and they must. **THE CARRIERS ARE THE THREE SIBLING ENTRIES ON `CD-AC-001`:**
     `CD-RT-001-AST-NO-NUMERIC-DEFAULT` (the provenance of the magnitude),
     `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` (the runtime post-condition) and
     `CD-RT-001-MISSING-DATA-NEVER-CALM` (the MISSING half at the gate, including `RULE CC`).
     **THIS IS ONE OF FOUR GUARDS ON `CD-AC-001` AND NEVER A SOLE GUARD.**

  5. **IT DOES NOT RE-DERIVE THE ROOT PARTITION.** It drives the CANONICAL DIAL SLOTS — root
     properties spelled literally `{"$ref": "#/$defs/dial_reading"}` — and if the contract
     declares none it exits `3` rather than reporting clean. Whether some OTHER root property
     could carry a dial at all is `RULE CC`'s question and it is asserted on the SIBLING row
     (`CD-CALM-ROOT-008`), not here. **A root property this row does not drive is not a
     property this row says anything about.**

  6. **IT IS A CLAIM ABOUT DOCUMENTS THE GATE SEES.** A rendering path that never calls
     `refuse_unless_publishable` is outside this check entirely. MEASURED at this commit: the
     only callers in `src/` are `publication/publish.py` lines 276-277, on both surfaces,
     before any write. **A FUTURE SERVING LAYER THAT RENDERS A DIAL WITHOUT PUBLISHING AN
     ENVELOPE IS NOT PROVED TO BE CARRIED ANYWHERE.**

  7. **IT NEEDS `jsonschema`, BECAUSE THE GATE DOES.** If `jsonschema` is absent it exits `3`
     with the reason — never a pass and never a skip (`PBG-CI-002`).

  8. **THE DECLARED SCOPE ABOVE IS THIS ROW'S LARGEST LIMIT AND IT IS STATED IN FULL RATHER
     THAN CROSS-REFERENCED.** The gate is DOCUMENT-INTERNAL. A source that consistently lies
     about its own stamp passes it, and a uniformly time-shifted envelope passes it —
     `as_of_utc` = `published_utc` = `1970-01-01T00:00:00Z` with an ordinary 600-second window
     is ADMITTED, MEASURED, and this instrument's own `CD-STALE-SCOPE-009` assertion **DRIVES
     THAT DOCUMENT AND REQUIRES IT TO BE ADMITTED**, so the limit cannot go stale in the
     reassuring direction while the code changes underneath it. Closing that class needs a
     comparand from OUTSIDE the document, which is the DETECTION tier — `CD-AC-018`, witness
     divergence + provenance — **OWED AT WO-3**. It is enforced one tier out and it is not
     unenforceable.

  9. **THE INVARIANCE PASS VARIES ONE PROPERTY AT A TIME, AND ITS VALUE VOCABULARY IS A SAMPLE
     OF AN UNBOUNDED SET. NEW AT `16F`.** From a proved-publishable baseline it varies ONE root
     property, or ONE non-stamp property of the calm-bearing node, to ONE other value that
     property's own subschema admits, and requires the verdict FOUR-TUPLE — admitted or
     refused, reason class, pointer, key — to be unchanged. **THAT IS LINEAR RATHER THAN THE
     EXPONENTIAL CROSS-PRODUCT, AND IT CATCHES EVERY PREDICATE KEYED ON A SINGLE PROPERTY**,
     which is every weakening shape measured on this project. Where a subschema admits an
     UNBOUNDED set — every string of 1 to 128 characters, every number — **THE VOCABULARY IS A
     SAMPLE AND NOT A COVER.** What is sampled, and why each family is there: the product's own
     words (every `const` and every `enum` string HARVESTED FROM THE CONTRACT ITSELF, never
     typed in, which is the family `W5B2` keys on); array CARDINALITY at 0, 1, 2 and many (the
     family `W5G` keys on); every JSON type the subschema admits; numbers at zero, negative,
     small, large and integral; both booleans; null; and presence against absence.
     **A PREDICATE KEYED ON A STRING VALUE OUTSIDE THAT SAMPLE ESCAPES THIS PASS. MEASURED BY
     THIS SEAT AGAINST ITS OWN INSTRUMENT, AFTER FREEZING IT:** arm `N1`
     (`if candidate.get("config_snapshot_id") == "BYPASS": return`) leaves this row at `PASS`
     and admits a 1970-stamped calm dial on both surfaces. It is caught by the sibling
     STRUCTURAL row `CD-RT-001-PUBLICATION-CHOKEPOINT` (`CD-CHOKE-005`). EXECUTABLE: apply
     `plants/WO3-INC16F/N1-CONFIG-SNAPSHOT-ID-BYPASS.patch` and run both rows.

     *** ITS CLOSING SENTENCE WAS FALSE IN THE REASSURING DIRECTION. SUPERSEDED AT `16G` ON
     `CD-ASR-F14-02`, STATED AND NOT ERASED (`CD-RULE-004`, `PBG-CONT-003`). ***

     > **WHAT IT SAID, VERBATIM, IN ALL THREE PLACES IT WAS SAID:** *"It is caught by the
     > sibling STRUCTURAL row `CD-RT-001-PUBLICATION-CHOKEPOINT` (`CD-CHOKE-005`), **AND THE
     > TWO ROWS ARE A PAIR FOR EXACTLY THIS REASON.**"*
     >
     > And the sentence it rested on, said in the `16F` return
     > (`BL-20260824T223344Z-16FC`, `CD-ENG-F16F-02`): *"The class is closed by the STRUCTURAL
     > row, which catches every `return`/`continue`/`break`-shaped bypass regardless of what
     > value it is keyed on."*

     **THE FIRST HALF IS TRUE OF `N1`; THE SECOND HALF IS A CLAIM ABOUT A CLASS, AND THE CLASS
     CLAIM IS FALSE.** `N1` is caught because `N1`'s `return` is LEXICALLY INSIDE
     `_refuse_stale_calm`. **ARM `Z7` IS ALSO A `return` ON THE PUBLICATION PATH AND IT IS NOT
     CAUGHT** — it sits at the top of `_iter_nodes`, the SHARED DOCUMENT WALK the stage
     DEPENDS ON, and `CD-CHOKE-005` walks `_refuse_stale_calm` and nothing the stage calls.
     Raised as `CD-ASR-F14-02` by `CD-ASR-WO3-14`; **REPRODUCED IN THIS SEAT'S OWN SHELL AT
     `c475b8e` BEFORE THIS PARAGRAPH WAS WRITTEN** (`CD-PL-F193`): `STALE-CALM ADMISSIONS = 2`
     on both surfaces with `MUST-ADMIT ROWS REFUSED = 0`, while BOTH rows returned `PASS` —
     this row `PASS — 142088 assertions, 0 violations`, the structural row `PASS — 11
     assertions, 0 violations`. EXECUTABLE:
     `plants/WO3-INC16G/Z7-THE-SHARED-WALK-DECLINES-TO-YIELD-ONE-NODE.patch`.

     **WHAT IS TRUE INSTEAD, STATED OVER THE CLASS AND NOT OVER ONE FUNCTION.** `CD-CHOKE-005`
     catches a `return`, `continue` or `break` **LEXICALLY INSIDE `_refuse_stale_calm`**, and
     catches the stage's first executable statement ceasing to enumerate through the shared
     walk. **THAT IS A CLAIM ABOUT ONE FUNCTION'S BODY, NOT ABOUT THE PUBLICATION PATH.**
     Neither row reads the functions the stage DEPENDS ON, and the shared walk is one of them.
     **SO THE TWO ROWS ARE NOT A COVER OF THE `return`-SHAPED CLASS, AND THIS LIMIT NO LONGER
     SAYS THEY ARE.** What can be stated truthfully is that boundary and no more; **A LIMIT
     THAT ADMITS IT DOES NOT KNOW IS WORTH MORE THAN ONE THAT REASSURES**, and it was the
     reassurance that let a residual read as a closure.

     **THE SENTENCE BESIDE IT IS TRUE AND SURVIVES UNCHANGED:** *"NEITHER ROW CLOSES IT ALONE
     AND THE RETURN DOES NOT CLAIM OTHERWISE."* The disclosure was honest; the closing
     reassurance was wrong. **THE RESIDUAL CLASS IS NOT REOPENED HERE:** `PO-DECISIONS-0032`
     ruling 3 records the insider-source-weakening full guarantee (`CD-ASR-F14-01`) as OWED
     LATER-HARDENING — a code-structure invariant, a heavier mechanism than a document
     instrument — assigned to the assurance/detection tier and NOT a product blocker. **`16G`
     CORRECTS THE RECORD; IT DOES NOT CLOSE THE CLASS AND DOES NOT PRETEND TO.**

 10. **THE PAIRWISE PASS RUNS ON LIMB B ONLY, AND THREE-WAY CONJUNCTIONS ARE NOT COVERED. NEW
     AT `16F`.** One-at-a-time variation cannot see a CONJUNCTIVE predicate over two properties
     — `if regime == "acute" and len(inputs_used) == 2: return` — because neither half alone
     changes the verdict. So every unordered PAIR of `(property, value)` points drawn from two
     DIFFERENT properties is driven, over a per-property value set reduced BY FEATURE FAMILY
     (every product-vocabulary value and every array-cardinality value kept whole, one
     representative of each other family). **IT RUNS ON LIMB B ONLY** — the stage driven
     directly — because a LIMB A pairwise pass is about 230x more expensive per cell: MEASURED
     on this host, the front door costs `16.05 ms` per call because it reloads and recompiles
     the contract every time, and the stage costs `0.069 ms`. **A CONJUNCTIVE WEAKENING PLACED
     OUTSIDE THE STAGE — IN `refuse_unless_publishable` ITSELF — IS THEREFORE NOT COVERED BY
     THE PAIRWISE PASS**; it is covered by `CD-CHOKE-004` on the sibling structural row. **AND
     A THREE-WAY CONJUNCTION IS NOT COVERED BY EITHER ROW.** MEASURED at this tip: 30,575 pairs
     on the public contract and 39,142 on the private one, **stride 1 — the FULL product and
     not a sample.** Above `PAIRWISE_CELL_BUDGET` the pass takes a deterministic evenly-strided
     SUBSAMPLE and prints the stride at every run; **at the shipped contracts that branch is
     NOT REACHED and is therefore UNEXERCISED CODE IN NORMAL OPERATION**, which is stated here
     rather than left to be discovered. EXECUTABLE: arm
     `plants/WO3-INC16F/N6-CONJUNCTION-REGIME-AND-CARDINALITY.patch`.

 11. **THE PASS COSTS THIRTY TIMES WHAT THIS ROW COST BEFORE IT, AND THAT IS THE PRICE OF THE
     SPACE. NEW AT `16F`. THE `a9e19c3` ASSERTION COUNT IS CORRECTED AT `16G`.** MEASURED on
     the same host with the same command: `0.79 s` at `a9e19c3` for **97** assertions,
     `26.5 s` at this tip for 142,088. Almost all of it is LIMB A, because every front-door
     cell reloads and recompiles the contract. **THE COST IS PAID DELIBERATELY AND IT IS NOT AN
     ACCIDENT OF A LOOP NOBODY BOUNDED.** EXECUTABLE:
     `time python3 tools/register/check_stale_data_never_calm.py --root .`

     *** THE BASELINE FIGURE DID NOT REPRODUCE. SUPERSEDED AT `16G` ON `CD-ASR-F14-05`, STATED
     AND NOT ERASED (`CD-RULE-004`, `PBG-CONT-003`). ***

     > **WHAT IT SAID, VERBATIM, IN ALL THREE PLACES IT WAS SAID:** *"MEASURED on the same host
     > with the same command: `0.77 s` at `a9e19c3` for 122 assertions, `26.1 s` at this tip
     > for 142,088."*

     **`122` IS NOT WHAT THIS ROW ASSERTED AT `a9e19c3`. `97` IS.** `CD-ASR-WO3-13` and
     `CD-ASR-WO3-14` each measured `97`; **THIS SEAT DID NOT COPY THAT FIGURE, IT RAN IT**
     (`CD-PL-F193` — an inherited claim is a hypothesis until run), in a throwaway worktree so
     the lane was not disturbed, three consecutive times, and got `97` every time:

         git worktree add /tmp/inc16g/base a9e19c3
         cd /tmp/inc16g/base && python3 tools/register/check_stale_data_never_calm.py \
             --root /tmp/inc16g/base
         -> CD-RT-001-STALE-DATA-NEVER-CALM: PASS — 97 assertions, 0 violations   rc=0
            (x3, deterministic; `real 0m0.789s`)

     **THREE SEATS NOW AGREE ON `97` AND NOTHING MEASURES `122`.** The TIP figure `142,088`
     reproduces exactly and is untouched (`rc=0`, `real 0m26.486s`), so the correction is to
     the baseline half of the comparison and to nothing else; the timings are re-stated as this
     host measured them rather than carried across. **THE THIRTYFOLD CLAIM IN THE HEADLINE
     SURVIVES AND GETS LARGER, NOT SMALLER** — `142088 / 97` is about 1465x the assertion count
     at about 34x the wall clock. `122` is not recoverable from any run this seat could
     construct, and where a figure cannot be reproduced it is replaced by one that can be,
     with the command that produced it beside it.

===========================================================================================
FOR THE AUDITOR
===========================================================================================
*** THE PARAGRAPH THAT STOOD HERE ASSERTED UNIVERSALITY OVER POSITIONS AND WAS SILENT ON
DOCUMENTS. SUPERSEDED AT `16F` ON `A313-F1`, STATED AND NOT ERASED (`CD-RULE-004`,
`PBG-CONT-003`). ***

> **WHAT IT SAID, VERBATIM, IN ALL THREE PLACES IT WAS SAID:** *"Do not read a clean run of
> this check as proof that no stale reading can ever render as calm. It proves that the LIVE
> PUBLICATION GATE refuses a DOCUMENT-INTERNALLY stale calm node, on both surfaces, at every
> canonical dial slot AND at every position in the document the walk reaches, while still
> admitting everything the product must be able to publish."*

**EVERY WORD OF THAT IS TRUE OF THE ONE DOCUMENT THE INSTRUMENT BUILT, AND A READER WOULD TAKE
IT FOR A CLAIM ABOUT ALL OF THEM.** It quantified over POSITIONS — *"at every position in the
document the walk reaches"* — and said nothing at all about DOCUMENTS, while the instrument
behind it drove seventy-two documents that all carried the same single value for every root
property. This project's own words for a sentence in that shape are **"how a guard becomes a
certificate"**.

**WHAT THIS ROW PROVES AFTER `16F`, AND NO MORE.** Do not read a clean run of this check as
proof that no stale reading can ever render as calm. It proves, at every canonical dial slot on
both surfaces and at every position in the document the walk reaches, that the LIVE PUBLICATION
GATE refuses a DOCUMENT-INTERNALLY stale calm node and still admits everything the product must
be able to publish — **AND THAT THE VERDICT DOES NOT MOVE WHEN ANY OTHER ROOT PROPERTY, OR ANY
NON-STAMP PROPERTY OF THE CALM-BEARING NODE, IS VARIED TO ANY OTHER VALUE IN THE DECLARED
VOCABULARY, SINGLY ON BOTH LIMBS AND PAIRWISE ON LIMB B.** It does NOT prove that for values
outside that vocabulary (`DECLARED LIMIT 9`), for three-way conjunctions (`DECLARED LIMIT 10`),
or for a weakening that sits outside the stage altogether — that last is the SIBLING STRUCTURAL
ROW `CD-RT-001-PUBLICATION-CHOKEPOINT`, and **A REPORT THAT QUOTES ONE OF THE TWO ROWS IS HALF
A REPORT.** **The arm to weigh it against is the vacuity set**: an instrument that refused
everything would be enforcing silence rather than holding PID §3.2, **and an invariance check
that refuses everything everywhere is PERFECTLY INVARIANT**, which is why every varied point
carries the MUST-ADMIT rows too. **The arms to weigh it with are
`plants/WO3-INC16E/MANIFEST.md`'s `D1`-`D4` and `plants/WO3-INC16F/MANIFEST.md`'s `W5` and `N`
and `C` series**, each a measured tree with its `git apply` rc, its own rc and its violation
count.
"""

from __future__ import annotations

import copy
import hashlib
import math
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, resolve_root  # noqa: E402

CHECK_ID = "CD-RT-001-STALE-DATA-NEVER-CALM"

MUST_REFUSE = "MUST REFUSE"
MUST_ADMIT = "MUST ADMIT"

#: The level the criterion names. PID §3.2, verbatim: "Missing OR STALE data must never render
#: as calm." Judged by VALUE against the contract's own vocabulary, never by the name of the
#: `$def` it comes from (`CD-PL-F169`, `CD-ASR-WO3-02` F06/F07).
CALM = "calm"

#: The canonical dial slot spelling. A root property whose value is LITERALLY this mapping.
CANONICAL_DIAL_REF = {"$ref": "#/$defs/dial_reading"}

#: The document's declared publication instant. Every stamp below is expressed relative to it,
#: and NOTHING here reads a clock — neither this file nor the stage it drives (the stage's own
#: no-clock guarantee is `BP-AMENDMENT-0001` §D.3 and is asserted by
#: `tests/test_envelope_freshness.py`, not here).
PUBLISHED = "2026-08-24T18:00:00Z"

#: The declared window, in seconds, and the stamps that sit exactly on and just past its edge.
WINDOW_SECONDS = 600.0
STAMP_FRESH = "2026-08-24T17:59:30Z"            # 30s old — well inside
STAMP_ON_THE_EDGE = "2026-08-24T17:50:00Z"      # exactly 600s old — the CLOSED interval
STAMP_ONE_MICROSECOND_PAST = "2026-08-24T17:49:59.999999Z"   # 600.000001s old
STAMP_ANCIENT = "1970-01-01T00:00:00Z"          # fifty-six years old
STAMP_FUTURE = "2099-01-01T00:00:00Z"           # stamped AFTER publication: incoherent
STAMP_SECOND_FRESH = "2026-08-24T17:59:45Z"
STAMP_THIRD_FRESH = "2026-08-24T17:59:50Z"

#: Deliberately unmistakable, for the same reason the sibling row's are: a grep for one of these
#: lands HERE and nowhere near a source registry. **NOTHING IN THIS FILE REGISTERS A SOURCE**
#: (`Q25`, `CD-PL-F154`): nothing constructs a `SourceRecord`, imports
#: `crash_detector.source_registry`, or names `raw.source_registry`.
SYNTHETIC_INPUT_ID = "SYNTHETIC-STALE-REGISTER-CHECK-NOT-A-SOURCE"
SYNTHETIC_TEXT = "SYNTHETIC-STALE-REGISTER-CHECK-NOT-A-VALUE"

#: Synthetic and meaningless as a number. The dial has no ratified scale (`Q25` holds it).
SYNTHETIC_SCORE = 0.01

#: *** THE DECLARED VALUE VOCABULARY, A CLOSED LIST ON PURPOSE (RULE F), AND THE SAME DEVICE
#: `check_missing_data_never_calm.SYNTHETIC_VALUES` uses. *** Every property of the root and of
#: the calm-bearing branch is filled with the FIRST of these that the property's OWN subschema
#: ACCEPTS — decided by `jsonschema` and never by the property's NAME. A required property none
#: of them satisfies is REPORTED (`CD-STALE-BUILD-008`), never skipped. Order is the only thing
#: tuned: the plain string precedes the timestamp so a free-text property gets text and a
#: `pattern`-constrained one gets the timestamp.
SYNTHETIC_VALUES = (
    SYNTHETIC_TEXT,             # a bounded, non-empty, unpatterned string
    STAMP_FRESH,                # a UTC timestamp string
    SYNTHETIC_SCORE,            # a number
    [SYNTHETIC_INPUT_ID],       # a non-empty array of id-shaped strings
    [],                         # an empty array
    {},                         # an empty object
    True,                       # a boolean
    None,                       # null
)

#: A string that is shaped like nothing and parses as no instant. Used to prove a property that
#: ANNOUNCES itself as a stamp by name and does not read as one is a REFUSAL and never a skip.
NOT_A_STAMP = "SYNTHETIC-STALE-REGISTER-CHECK-NOT-AN-INSTANT"

#: Windows that are not windows. Each MUST make a calm-bearing node refuse, because an
#: unbounded, absent, reversed or type-confused window is no window. `True` is in the list on
#: purpose: it is an `int` in Python and would otherwise read as a one-second window nobody
#: declared, arrived at by a type confusion.
UNUSABLE_WINDOWS = (
    ("ABSENT", None),
    ("ZERO", 0),
    ("NEGATIVE", -1.0),
    ("BOOLEAN-TRUE", True),
    ("STRING", "600"),
    ("NOT-FINITE", float("inf")),
    ("NOT-A-NUMBER", float("nan")),
)

#: Values of `published_utc` from which no age can be computed. Each MUST refuse every
#: calm-bearing node in the document rather than be assumed fresh.
UNUSABLE_PUBLISHED = (
    ("ABSENT", None),
    ("UNPARSABLE", NOT_A_STAMP),
    ("SHAPE-VALID-NON-INSTANT", "2026-13-45T99:99:99Z"),
)

#: Only these keys may sit beside a `$ref` without changing what the node admits — every one is
#: a pure ANNOTATION in 2020-12. Carried from the sibling row's resolver, where the reasoning is
#: written in full (`DECLARED LIMIT 13`): in 2020-12 keywords SIBLING to `$ref` ARE APPLIED, so
#: a resolver that discards them silently is judging a schema the gate does not enforce.
REF_INERT_SIBLINGS = frozenset({
    "$ref", "$comment", "title", "description",
    "default", "deprecated", "readOnly", "writeOnly", "examples",
})

#: How many `$ref` hops :func:`_resolve` follows before giving up. Reaching it returns `None`,
#: which every caller treats as UNRECOGNISED — never as "nothing to see".
REF_CHAIN_CAP = 32


# ============================================================================================ #
# *** WO-3 INCREMENT 16F — THE VARIATION VOCABULARY. THE HALF THAT DECIDES WHETHER THE
# INVARIANCE PASS WORKS. *** `PO-DECISIONS-0031` ruling 1(i); `A313-F1`.
#
# An invariance check is only as wide as the values it varies across, and the vocabulary that
# was here before 16F WOULD NOT HAVE CAUGHT `W5G`: its only arrays are length 0 and length 1
# and that predicate needs length 2. Every family below is here for a named reason and the
# reason is the FEATURE A WEAKENING PREDICATE CAN KEY ON, never "it seemed like a good value".
#
#   · PRODUCT VOCABULARY — every string the CONTRACT ITSELF pins as a `const` or lists in an
#     `enum`, harvested from the loaded schema and NEVER typed in. On the shipped contracts that
#     is `1.1.0`, `PRIVATE`, `VALUE`, `DEGRADED`, `UNKNOWN`, `calm`, `elevated`, `acute`.
#     **`W5B2` IS EXACTLY THIS FAMILY:** `regime` is `{"type": "string", "minLength": 1}` on
#     both contracts — deliberately not an enumeration — so `"calm"` is an ORDINARY admissible
#     value of an ordinary root property, and a predicate keyed on it is invisible to any
#     instrument that only ever drives one string there. Harvesting rather than naming is what
#     makes a vocabulary a future contract edit adds covered the day it lands.
#   · ARRAY CARDINALITY at 0, 1, 2 and MANY. **`W5G` IS EXACTLY THIS FAMILY.**
#   · EVERY JSON TYPE — string, number, boolean, null, array, object — because a predicate can
#     key on a type as easily as on a value.
#   · NUMBERS at zero, negative, small, large and integral, because `if score > 0` and
#     `if not score` are different predicates and the second is satisfied by zero.
#   · BOTH BOOLEANS, because `if flag` and `if flag is False` are different predicates.
#   · STRINGS at empty, synthetic, long, and stamp-shaped.
#
# Where a subschema admits an UNBOUNDED set (every string of 1..128 characters, every number)
# this samples it. **THAT IS `DECLARED LIMIT 9` AND IT IS STATED THERE IN THOSE TERMS.**
# ============================================================================================ #

#: Distinct id-shaped strings, for building arrays at each cardinality. `uniqueItems` is
#: declared on `#/$defs/source_id_list`, so a two-element array of the SAME id is one element
#: as far as the contract is concerned and would not probe cardinality at all.
VARIATION_IDS = tuple(
    f"{SYNTHETIC_INPUT_ID}-{index}" for index in range(1, 6)
)

#: A string exactly at the longest `maxLength` either contract declares for a root property.
VARIATION_LONG_STRING = "Z" * 128

#: The families above, as `(family, label, value)`. FAMILY is carried because the PAIRWISE pass
#: (`DECLARED LIMIT 10`) reduces to a bounded number of values per property and must reduce by
#: FEATURE rather than by list position — dropping every array cardinality but one would drop
#: exactly the feature `W5G` keys on.
VARIATION_FAMILIES = (
    ("STRING", "STRING-EMPTY", ""),
    ("STRING", "STRING-SYNTHETIC", SYNTHETIC_TEXT),
    ("STRING", "STRING-128-CHARACTERS", VARIATION_LONG_STRING),
    ("STAMP", "STRING-STAMP-FRESH", STAMP_FRESH),
    ("STAMP", "STRING-STAMP-ANCIENT", STAMP_ANCIENT),
    ("STAMP", "STRING-STAMP-FUTURE", STAMP_FUTURE),
    ("NUMBER", "NUMBER-ZERO", 0),
    ("NUMBER", "NUMBER-NEGATIVE", -1.5),
    ("NUMBER", "NUMBER-SMALL", 1e-09),
    ("NUMBER", "NUMBER-LARGE", 1e12),
    ("NUMBER", "NUMBER-INTEGER-ONE", 1),
    ("BOOLEAN", "BOOLEAN-TRUE", True),
    ("BOOLEAN", "BOOLEAN-FALSE", False),
    ("NULL", "NULL", None),
    ("ARRAY-CARDINALITY", "ARRAY-CARDINALITY-0", []),
    ("ARRAY-CARDINALITY", "ARRAY-CARDINALITY-1", list(VARIATION_IDS[:1])),
    ("ARRAY-CARDINALITY", "ARRAY-CARDINALITY-2", list(VARIATION_IDS[:2])),
    ("ARRAY-CARDINALITY", "ARRAY-CARDINALITY-MANY", list(VARIATION_IDS)),
    ("OBJECT", "OBJECT-EMPTY", {}),
    ("OBJECT", "OBJECT-NESTED", {"a": {"b": ["c"]}}),
)

#: The two ROOT properties the criterion names, and the ONLY two the verdict may read from the
#: root. They are named here because the INVARIANT is stated in terms of them — this is the
#: boundary of the independence being asserted, not a recogniser over a set that could grow.
ROOT_PUBLISHED_KEY = "published_utc"
ROOT_WINDOW_KEY = "staleness_window_seconds"

#: A sentinel meaning DELETE THIS PROPERTY. `None` is an ordinary admissible JSON value and a
#: variation pass that used it for absence could not tell "null" from "not there".
_ABSENT = object()

#: How many distinct findings PER RULE the invariance pass prints in full. The rest are counted
#: and the count is printed. The varied space is thousands of cells wide and a stage that has
#: stopped working fails most of them; the exit code is non-zero either way.
VIOLATION_REPORT_CAP = 12

#: The floor on the varied space. **AN INVARIANCE CHECK THAT VARIES NOTHING IS PERFECTLY
#: INVARIANT**, so `CD-STALE-INVARIANT-012` refuses a run that drove fewer points than this.
#: MEASURED at `a9e19c3` + 16F: the pass drives far more than this on both contracts; the floor
#: exists to catch a vocabulary narrowed back to the one-value-per-property shape of `A313-F1`.
MINIMUM_INVARIANCE_POINTS = 200

#: The cell budget for the LIMB B PAIRWISE pass. `DECLARED LIMIT 10`. Beyond it the pass takes
#: a DETERMINISTIC evenly-strided subsample and SAYS SO at every run, rather than pretending to
#: run a product it does not run.
PAIRWISE_CELL_BUDGET = 90000

#: How many values per property the PAIRWISE pass carries. `DECLARED LIMIT 10`. Every
#: `PRODUCT-VOCABULARY` and every `ARRAY-CARDINALITY` value is kept whatever this is; the cap
#: applies to the remaining families, one per family. The ONE-AT-A-TIME pass is NOT capped.
PAIRWISE_FAMILY_CAP = 1

#: Extra property names planted on a calm-bearing node by the LIMB B invariance pass, to probe
#: a predicate keyed on a property the contract has never heard of. **NONE OF THEM ENDS IN
#: `_utc`**: a property that ANNOUNCES itself as a stamp and does not parse is a REFUSAL by
#: design (the stage's own fail-closed branch), which would be a verdict change caused by one of
#: the criterion's OWN inputs rather than by an independent property.
VARIATION_EXTRA_NODE_KEYS = ("synthetic_16f_extra", "synthetic_16f_flag")

#: Extra ROOT property names planted by the LIMB B invariance pass, for the same reason.
VARIATION_EXTRA_ROOT_KEYS = ("synthetic_16f_root_extra",)

#: *** MIRRORED FROM `crash_detector.publication.envelope_contract.UTC_STAMP_PATTERN`, CHARACTER
#: FOR CHARACTER, AND ASSERTED AGAINST IT AT EVERY RUN. *** The invariance pass uses it for ONE
#: purpose: to decide which pool values would become one of a calm-bearing node's OWN STAMPS if
#: they were written onto it, so that those values are varied at the ROOT and not at the NODE.
#: **IF THE TWO EVER DIVERGE THIS CHECK EXITS 3** rather than quietly varying across a value
#: that is a verdict input — a check that cannot reach its authentic target fails, never waves
#: through (`PBG-CI-002`). The application's own pattern is PUBLIC (it is in that module's
#: `__all__`), so this is a mirror of an exported constant and not a second private coupling.
_STAMP_SHAPE_PATTERN = (
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?Z$"
)
_STAMP_SHAPE_RE = re.compile(_STAMP_SHAPE_PATTERN)


# ------------------------------------------------------------------------------------------ #
# Schema plumbing. Small, deliberate duplicates of the sibling row's helpers: every check in
# `tools/register/` is a STANDALONE script (see `_support.__doc__`), and an auditor extracting a
# tree runs this file on its own.
# ------------------------------------------------------------------------------------------ #

def _fragment(schema: dict, subschema: dict) -> dict:
    """``subschema`` as a standalone document, so its local ``#/$defs/...`` refs still resolve."""
    fragment = dict(subschema)
    fragment.setdefault("$schema", schema.get("$schema")
                        or "https://json-schema.org/draft/2020-12/schema")
    fragment.setdefault("$defs", schema.get("$defs") or {})
    return fragment


def _resolve(schema: dict, node, depth: int = 0):
    """Follow a chain of LOCAL ``#/...`` refs. Returns ``(resolved, dropped)``.

    ``dropped`` names every hop that carried an ASSERTING key beside its ``$ref``, so a caller
    can refuse rather than silently judge a node the chain rewrote.
    """
    dropped: list = []
    while isinstance(node, dict) and "$ref" in node:
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


def _deref(schema: dict, node, depth: int = 0):
    """The resolved node only, for callers with no siblings to lose."""
    return _resolve(schema, node, depth)[0]


def _accepts(schema: dict, subschema, validator, value) -> bool:
    """Does ``subschema`` accept ``value``? Decided by `jsonschema`, never by a property NAME."""
    if not isinstance(subschema, dict):
        return False
    try:
        return bool(validator(_fragment(schema, subschema)).is_valid(value))
    except Exception:  # pragma: no cover - a subschema jsonschema cannot compile
        return False


def _synthesise(schema: dict, subschema, validator):
    """A value the property's OWN subschema accepts.

    Returns ``(value, True)`` on success and ``(None, False)`` on failure, so a legitimate
    ``null`` is never confused with an unbuildable property.
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
    except Exception:  # pragma: no cover
        return None, False
    for candidate in candidates:
        try:
            if checker.is_valid(candidate):
                return candidate, True
        except Exception:  # pragma: no cover
            continue
    return None, False


def _canonical_dial_slots(schema: dict) -> list:
    """Root properties spelled LITERALLY ``{"$ref": "#/$defs/dial_reading"}``. Sorted."""
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return []
    return sorted(
        name for name, sub in properties.items()
        if isinstance(sub, dict) and sub == CANONICAL_DIAL_REF
    )


def _calm_bearing_branch(schema: dict, validator):
    """The ``#/$defs/dial_reading.oneOf`` branch whose ``detail_level`` ADMITS ``calm``.

    Returns ``(label, branch, dropped)`` or ``(None, None, dropped)``. The branch is identified
    by WHAT ITS OWN SUBSCHEMA ACCEPTS and never by the name of the ``$def`` it lives in — a
    structural read of `$ref` target names is what let this class through three times here.
    """
    union, dropped = _resolve(schema, (schema.get("$defs") or {}).get("dial_reading"))
    if not isinstance(union, dict):
        return None, None, dropped
    branches = union.get("oneOf")
    if not isinstance(branches, list):
        return None, None, dropped
    for index, entry in enumerate(branches):
        resolved, entry_dropped = _resolve(schema, entry)
        dropped = dropped + entry_dropped
        if not isinstance(resolved, dict):
            continue
        properties = resolved.get("properties")
        if not isinstance(properties, dict):
            continue
        if _accepts(schema, properties.get("detail_level"), validator, CALM):
            state = properties.get("state")
            label = (state.get("const") if isinstance(state, dict) else None) or f"[{index}]"
            return str(label), resolved, dropped
    return None, None, dropped


def _stamp_properties(schema: dict, branch: dict, validator) -> list:
    """Properties of ``branch`` that are STAMP-SHAPED, decided behaviourally.

    A property is stamp-shaped when its own subschema ACCEPTS a UTC instant string and REJECTS
    a string that is not one. **NEVER BY NAME:** the contracts spell the stamp ``as_of_utc`` on
    two branches and ``since_utc`` on a third, so a fixed property name would already be wrong,
    and a contract that spells it a fourth way tomorrow would make a name-reading instrument
    silently stop finding stamps — which is *admitting*, not refusing.
    """
    properties = branch.get("properties")
    if not isinstance(properties, dict):
        return []
    return sorted(
        name for name, sub in properties.items()
        if _accepts(schema, sub, validator, STAMP_FRESH)
        and not _accepts(schema, sub, validator, NOT_A_STAMP)
    )


def _pointer_tokens(node, pointer: str = ""):
    """``(node, pointer)`` for every node in a document, root first. RFC 6901 escaping."""
    yield node, pointer
    if isinstance(node, dict):
        for key, value in node.items():
            token = str(key).replace("~", "~0").replace("/", "~1")
            yield from _pointer_tokens(value, f"{pointer}/{token}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _pointer_tokens(value, f"{pointer}/{index}")


def _differing_pointers(left, right) -> list:
    """Every JSON pointer at which two documents differ — by value OR by presence."""
    left_map = {pointer: node for node, pointer in _pointer_tokens(left)
                if not isinstance(node, (dict, list))}
    right_map = {pointer: node for node, pointer in _pointer_tokens(right)
                 if not isinstance(node, (dict, list))}
    differing = set(left_map) ^ set(right_map)
    for pointer in set(left_map) & set(right_map):
        if left_map[pointer] != right_map[pointer]:
            differing.add(pointer)
    return sorted(differing)


# ------------------------------------------------------------------------------------------ #
# WO-3 INCREMENT 16F — the invariance pass's own plumbing.
# ------------------------------------------------------------------------------------------ #

def _product_vocabulary(schema: dict) -> tuple:
    """Every STRING the contract itself pins as a ``const`` or lists in an ``enum``.

    **HARVESTED FROM THE LOADED CONTRACT AND NEVER TYPED IN.** A contract edit that adds a
    regime name, a state or a detail level is varied across the day it lands rather than the
    day somebody remembers to add it to a list in this file — which is the difference between
    an instrument that probes the SPACE and one that probes the points its author thought of.
    """
    found = set()

    def walk(node) -> None:
        if isinstance(node, dict):
            if isinstance(node.get("const"), str):
                found.add(node["const"])
            if isinstance(node.get("enum"), list):
                for value in node["enum"]:
                    if isinstance(value, str):
                        found.add(value)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)
    return tuple(sorted(found))


def _variation_pool(schema: dict) -> tuple:
    """``(family, label, value)`` for the whole declared vocabulary, contract words first."""
    pool = [
        ("PRODUCT-VOCABULARY", f"PRODUCT-VOCABULARY:{word}", word)
        for word in _product_vocabulary(schema)
    ]
    pool.extend(VARIATION_FAMILIES)
    return tuple(pool)


def _same_value(left, right) -> bool:
    """Equality that does not confuse ``True`` with ``1`` or ``0`` with ``False``."""
    if isinstance(left, bool) != isinstance(right, bool):
        return False
    try:
        return bool(left == right)
    except Exception:  # pragma: no cover
        return False


def _instance_of(schema: dict, subschema, validator, stamp: str, tag: str):
    """One instance of ``subschema``, built from its OWN ``required`` list. ``None`` on failure.

    This is what gives a property whose subschema admits no scalar — a dial slot, an array of
    closed objects — a set of ALTERNATIVE ADMISSIBLE VALUES to be varied across. Without it
    those properties would silently contribute nothing to the space and the instrument would be
    invariant over them by never having driven them.
    """
    resolved = _deref(schema, subschema)
    if not isinstance(resolved, dict):
        return None
    built = {}
    for name in resolved.get("required") or []:
        value, ok = _synthesise(schema, (resolved.get("properties") or {}).get(name), validator)
        if not ok:
            return None
        built[str(name)] = copy.deepcopy(value)
    if not built:
        return None
    for name, sub in (resolved.get("properties") or {}).items():
        if name in built and _accepts(schema, sub, validator, STAMP_FRESH) \
                and not _accepts(schema, sub, validator, NOT_A_STAMP):
            built[str(name)] = stamp
    for name, sub in (resolved.get("properties") or {}).items():
        if name in built and isinstance(built[name], str) and tag \
                and _accepts(schema, sub, validator, tag):
            built[str(name)] = tag
            break
    return built


def _structural_variants(schema: dict, subschema, validator) -> list:
    """``(label, value)`` alternatives built FROM THE SUBSCHEMA rather than from the flat pool.

    Two shapes, both of which exist on the shipped contracts:

      · a ``oneOf`` union (``#/$defs/dial_reading``) — ONE INSTANCE PER BRANCH, each with a
        FRESH stamp, so a weakening keyed on *the OTHER dial's state* is inside the space;
      · an array of objects (``#/$defs/contribution_list``) — the SAME CARDINALITY LADDER the
        flat pool applies to arrays of strings, at 1 and 2 elements, so cardinality coverage is
        real for object arrays and not only for id arrays.
    """
    resolved = _deref(schema, subschema)
    if not isinstance(resolved, dict):
        return []
    variants: list = []
    branches = resolved.get("oneOf")
    if isinstance(branches, list):
        for index, entry in enumerate(branches):
            branch = _deref(schema, entry)
            if not isinstance(branch, dict):
                continue
            instance = _instance_of(schema, branch, validator, STAMP_FRESH, "")
            if instance is None:
                continue
            state = (branch.get("properties") or {}).get("state")
            label = (state.get("const") if isinstance(state, dict) else None) or f"[{index}]"
            variants.append((f"BRANCH-INSTANCE:{label}", instance))
    if resolved.get("type") == "array" and isinstance(resolved.get("items"), dict):
        first = _instance_of(schema, resolved["items"], validator, STAMP_FRESH, "")
        second = _instance_of(schema, resolved["items"], validator, STAMP_SECOND_FRESH,
                              VARIATION_IDS[1])
        if first is not None:
            variants.append(("ARRAY-OF-OBJECTS-CARDINALITY-1", [first]))
            if second is not None and second != first:
                variants.append(("ARRAY-OF-OBJECTS-CARDINALITY-2", [first, second]))
    return variants


def _admissible_variants(schema, subschema, validator, baseline, pool, exclude_stamp_like=False):
    """Every ``(family, label, value)`` the subschema ACCEPTS that is not the baseline value.

    ``exclude_stamp_like`` drops any value that reads as a UTC instant. It is set when the
    property being varied belongs to the CALM-BEARING NODE: a string that parses as an instant
    BECOMES ONE OF THAT NODE'S OWN STAMPS, and the node's own stamps are one of the three
    things the verdict is ALLOWED to depend on. Dropping them is not a gap in the space — it is
    the boundary of the invariant, and those values are driven at the ROOT instead.
    """
    out = []
    for family, label, value in pool:
        if _same_value(value, baseline):
            continue
        if exclude_stamp_like and isinstance(value, str) and _STAMP_SHAPE_RE.match(value):
            continue
        if not _accepts(schema, subschema, validator, value):
            continue
        out.append((family, label, value))
    for label, value in _structural_variants(schema, subschema, validator):
        if _same_value(value, baseline):
            continue
        if _accepts(schema, subschema, validator, value):
            out.append(("STRUCTURAL", label, value))
    return out


def _pairwise_reduction(variants: list) -> list:
    """The bounded per-property value set the PAIRWISE pass carries. ``DECLARED LIMIT 10``.

    Every ``PRODUCT-VOCABULARY`` value and every ``ARRAY-CARDINALITY`` value is KEPT — those are
    the two families the two measured fifth weakenings key on, and reducing them away would
    reduce away the point of the pass. Every other family contributes
    :data:`PAIRWISE_FAMILY_CAP` representatives.
    """
    kept: list = []
    seen: dict = {}
    for family, label, value in variants:
        if family in ("PRODUCT-VOCABULARY", "ARRAY-CARDINALITY", "STRUCTURAL"):
            kept.append((family, label, value))
            continue
        seen[family] = seen.get(family, 0) + 1
        if seen[family] <= PAIRWISE_FAMILY_CAP:
            kept.append((family, label, value))
    return kept


def _signature(outcome) -> tuple:
    """A comparable verdict. Never a boolean: WHICH refusal, at WHICH pointer, is load-bearing."""
    if outcome is None:
        return ("ADMITTED", None, None, None)
    reason = getattr(outcome, "reason_class", None)
    if reason is not None:
        return ("REFUSED", reason, getattr(outcome, "pointer", None),
                getattr(outcome, "key", None))
    return ("ERROR", type(outcome).__name__, None, None)


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
        from crash_detector.publication.envelope_contract import (
            ENVELOPE_SCHEMA_VERSION,
            EnvelopeSurface,
            PublicationRefused,
            REFUSAL_STALE_CALM,
            UTC_STAMP_PATTERN,
            contracts_dir,
            load_envelope_schema,
            refuse_unless_publishable,
            schema_path_for,
        )
    except Exception as exc:
        return check.refuse(
            f"the subject tree at {src} did not import: {type(exc).__name__}: {exc}. If this "
            "is a missing `jsonschema`, that is DECLARED LIMIT 7: this check drives the live "
            "gate and the live gate validates with jsonschema."
        )

    # ---- THE STAGE ITSELF, FOR LIMB B — DECLARED LIMIT 3 ----------------------------- #
    # A check that cannot find its authentic target FAILS. It does not fall back to limb A and
    # report clean on half the propositions (`PBG-CI-002`, `PBG-EVID-002`).
    try:
        from crash_detector.publication.envelope_contract import _refuse_stale_calm
    except Exception as exc:
        return check.refuse(
            f"`crash_detector.publication.envelope_contract._refuse_stale_calm` did not import "
            f"({type(exc).__name__}: {exc}). LIMB B drives the fourth refusal stage directly, "
            "because the CLOSED contracts make every calm-bearing position except a canonical "
            "dial slot unreachable through the front door, and an instrument that only used "
            "the front door could not tell the NODE WALK apart from an implementation that "
            "reads the two dial slots BY NAME. This is DECLARED LIMIT 3's name coupling, and "
            "it fails loudly rather than quietly measuring less."
        )

    try:
        import jsonschema  # noqa: F401
        from jsonschema.validators import validator_for
    except Exception as exc:
        return check.refuse(
            f"`jsonschema` did not import ({type(exc).__name__}: {exc}). DECLARED LIMIT 7: this "
            "check drives the live gate, the live gate validates with jsonschema, and a "
            "behavioural check cannot be more stdlib-only than the behaviour it drives."
        )

    package_dir = pathlib.Path(crash_detector.__file__).resolve().parent
    # CD-PL-F98 — READ THE TREE LINE EVERY TIME. A contrast run against the wrong tree is
    # indistinguishable from a fix that does nothing.
    check.note(f"imported crash_detector from: {package_dir / '__init__.py'}")
    check.note(f"python: {sys.version.split()[0]}")
    check.note(f"ENVELOPE_SCHEMA_VERSION as the application declares it: {ENVELOPE_SCHEMA_VERSION}")
    check.note(f"the refusal token this row requires: {REFUSAL_STALE_CALM!r}")

    # ---- THE STAMP-SHAPE MIRROR, ENFORCED AS A PRECONDITION (16F) -------------------- #
    # The invariance pass uses this pattern to keep values that would become a calm-bearing
    # node's OWN stamp out of the set of properties it varies AT THE NODE. If the mirror has
    # drifted from the application's exported constant, that reasoning is void.
    if UTC_STAMP_PATTERN != _STAMP_SHAPE_PATTERN:
        return check.refuse(
            "this check mirrors `UTC_STAMP_PATTERN` from the application so the invariance "
            "pass can tell which values would BECOME one of a calm-bearing node's own stamps. "
            f"The application now declares {UTC_STAMP_PATTERN!r} and this file mirrors "
            f"{_STAMP_SHAPE_PATTERN!r}. They have drifted, so the boundary of the invariant "
            "this row asserts is no longer the boundary it computes. Exiting 3 rather than "
            "measuring a space whose edge has moved (PBG-CI-002)."
        )

    # ---- DECLARED LIMIT 1, ENFORCED AS A PRECONDITION -------------------------------- #
    resolved_contracts = contracts_dir().resolve()
    if resolved_contracts != (root / "contracts").resolve():
        return check.refuse(
            f"the live gate resolves its contracts to {resolved_contracts}, which is NOT "
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

    # ---- CD-STALE-VACUITY-000 — THE ADMITTING ROWS CANNOT BE QUIETLY DELETED --------- #
    # The sibling row learned this the expensive way: an instrument that only checked "the bad
    # thing is refused" is satisfied by a tree on which NOTHING can be published. This assertion
    # is about THIS FILE'S OWN TABLE, so the vacuity arms cannot be removed from the instrument
    # that exists to carry them.
    check.asserted()
    gate_table = (
        ("ANCIENT", STAMP_ANCIENT, CALM, MUST_REFUSE),
        ("FUTURE", STAMP_FUTURE, CALM, MUST_REFUSE),
        ("ONE-MICROSECOND-PAST-THE-WINDOW", STAMP_ONE_MICROSECOND_PAST, CALM, MUST_REFUSE),
        ("EXACTLY-THE-WINDOW", STAMP_ON_THE_EDGE, CALM, MUST_ADMIT),
        ("WELL-INSIDE-THE-WINDOW", STAMP_FRESH, CALM, MUST_ADMIT),
        ("ANCIENT-BUT-NOT-CALM", STAMP_ANCIENT, None, MUST_ADMIT),
    )
    admitting = [row for row in gate_table if row[3] is MUST_ADMIT]
    refusing = [row for row in gate_table if row[3] is MUST_REFUSE]
    missing_directions = []
    if not any(row[2] == CALM for row in admitting):
        missing_directions.append("a FRESH CALM dial that must still be ADMITTED")
    if not any(row[1] == STAMP_ON_THE_EDGE for row in admitting):
        missing_directions.append("the CLOSED-INTERVAL boundary row (age EXACTLY the window)")
    if not any(row[2] is None for row in admitting):
        missing_directions.append("a STALE NON-CALM dial that must still be ADMITTED")
    if not refusing:
        missing_directions.append("any refusing row at all")
    if missing_directions:
        check.violation(
            here, 0, "CD-STALE-VACUITY-000",
            "this instrument's OWN proposition table has lost "
            f"{missing_directions!r}. A row that refuses everything is not a row on which "
            "CD-AC-001 holds — it is a row on which the product can no longer publish a calm "
            "reading at all, and PID §4 makes calm the base case. The admitting arms carry "
            "equal weight and may not be deleted from the instrument that exists to carry them.",
        )
    else:
        check.note(
            f"VACUITY GUARD: the table declares {len(refusing)} MUST-REFUSE and "
            f"{len(admitting)} MUST-ADMIT rows, including the fresh-calm row, the "
            "closed-interval boundary row and the stale-but-not-calm row."
        )

    # ---- THE SUBJECT SET, ENUMERATED FROM THE APPLICATION AND THE CONTRACTS ---------- #
    slots_by_surface = {}
    branch_by_surface = {}
    stamps_by_surface = {}
    for surface in EnvelopeSurface:
        schema = schemas[surface]
        validator = validator_for(schema)
        slots = _canonical_dial_slots(schema)
        if not slots:
            return check.refuse(
                f"the {surface.value} contract declares NO canonical dial slot "
                f"({CANONICAL_DIAL_REF!r}) at its root, so there is no calm-bearing dial to "
                "age and this check would be measuring nothing. DECLARED LIMIT 5."
            )
        label, branch, dropped = _calm_bearing_branch(schema, validator)
        if branch is None:
            return check.refuse(
                f"no branch of the {surface.value} contract's #/$defs/dial_reading.oneOf has a "
                "detail_level that admits 'calm', so no document this contract accepts can "
                "carry a calm dial and this check cannot drive its own subject. That is either "
                "a contract in which calm is unrepresentable — which is the VACUOUS direction "
                "and a defect in itself (PID §4 makes calm the base case) — or a union this "
                "check cannot read."
            )
        if dropped:
            check.asserted()
            check.violation(
                here, 0, "CD-STALE-BUILD-008",
                f"{surface.value}: a $ref on the way to the calm-bearing branch carries an "
                f"ASSERTING sibling ({dropped!r}). In JSON Schema 2020-12 a keyword beside a "
                "$ref IS APPLIED, so the branch this check would drive is NOT the branch the "
                "gate enforces. Reported rather than resolved: a resolver that discards "
                "siblings can only ever WEAKEN this instrument, silently.",
            )
        stamps = _stamp_properties(schema, branch, validator)
        if not stamps:
            return check.refuse(
                f"the {surface.value} contract's calm-bearing branch {label!r} declares NO "
                "stamp-shaped property (one whose own subschema accepts a UTC instant and "
                "rejects a non-instant), so a calm dial on this contract cannot date its own "
                "data and there is nothing for this check to age. A branch that requires no "
                "timestamp cannot prove freshness — the sibling row asserts that structurally "
                "as CD-CALM-CANON-009; this row refuses to measure without one."
            )
        slots_by_surface[surface] = slots
        branch_by_surface[surface] = (label, branch)
        stamps_by_surface[surface] = stamps
        check.note(
            f"{surface.value}: dial slots {slots!r} · calm-bearing branch {label!r} · "
            f"stamp-shaped properties {stamps!r} (decided by what each subschema ACCEPTS, "
            "never by name)"
        )

    # ---- THE BUILDERS ---------------------------------------------------------------- #
    def build_dial(surface, level, stamp):
        """One dial from the calm-bearing branch's OWN required + properties."""
        schema = schemas[surface]
        validator = validator_for(schema)
        _label, branch = branch_by_surface[surface]
        properties = branch.get("properties") or {}
        required = branch.get("required") or []
        dial = {}
        unbuildable = []
        for name in required:
            sub = properties.get(name)
            value, built = _synthesise(schema, sub, validator)
            if not built:
                unbuildable.append(name)
                continue
            dial[str(name)] = copy.deepcopy(value)
        for name in stamps_by_surface[surface]:
            if name in dial:
                dial[name] = stamp
        if level is not None:
            dial["detail_level"] = level
        return dial, unbuildable

    def build_root(surface, dials, window=WINDOW_SECONDS, published=PUBLISHED):
        """The envelope root from the contract's OWN required list."""
        schema = schemas[surface]
        validator = validator_for(schema)
        properties = schema.get("properties") or {}
        required = schema.get("required") or []
        document = {}
        unbuildable = []
        for name in required:
            if name in dials:
                document[str(name)] = copy.deepcopy(dials[name])
                continue
            value, built = _synthesise(schema, properties.get(name), validator)
            if not built:
                unbuildable.append(name)
                continue
            document[str(name)] = copy.deepcopy(value)
        if published is None:
            document.pop("published_utc", None)
        else:
            document["published_utc"] = published
        if window is None:
            document.pop("staleness_window_seconds", None)
        else:
            document["staleness_window_seconds"] = window
        return document, unbuildable

    def verdict(surface, document):
        """What the LIVE GATE did. Never a boolean: the reason class is load-bearing."""
        try:
            refuse_unless_publishable(copy.deepcopy(document), surface=surface)
        except PublicationRefused as exc:
            return exc
        except Exception as other:
            return other
        return None

    # ================================================================================== #
    # LIMB A — THE LIVE GATE, THROUGH THE FRONT DOOR.
    # This is the limb `D1` (the whole stage unreachable from the gate) and `D2` (the naive
    # `age > window`) are measured against.
    # ================================================================================== #
    cells = 0
    for surface in EnvelopeSurface:
        slots = slots_by_surface[surface]
        branch_label, _branch = branch_by_surface[surface]
        stamps = stamps_by_surface[surface]

        fresh_dial, unbuildable = build_dial(surface, CALM, STAMP_FRESH)
        if unbuildable:
            check.asserted()
            check.violation(
                here, 0, "CD-STALE-BUILD-008",
                f"{surface.value}/{branch_label}: this check could not build a value for the "
                f"required propert(ies) {unbuildable!r} out of its declared closed vocabulary, "
                "so the calm-bearing dial was never constructed and NOTHING below measured it. "
                "DENY BY DEFAULT (DECLARED LIMIT 2): reported and non-zero, never skipped.",
            )
            continue

        for slot_under_test in slots:
            dials = {slot: copy.deepcopy(fresh_dial) for slot in slots}
            baseline, root_unbuildable = build_root(surface, dials)
            if root_unbuildable:
                check.asserted()
                check.violation(
                    here, 0, "CD-STALE-BUILD-008",
                    f"{surface.value}: this check could not build a value for the required "
                    f"root propert(ies) {root_unbuildable!r}, so no candidate envelope was "
                    "constructed. DENY BY DEFAULT (DECLARED LIMIT 2).",
                )
                continue

            # The baseline must be publishable, or every refusal below is attributable to the
            # skeleton rather than to the stamp under test. FAIL CLOSED, LOUDLY.
            check.asserted()
            cells += 1
            baseline_outcome = verdict(surface, baseline)
            if baseline_outcome is not None:
                check.violation(
                    here, 0, "CD-STALE-GATE-001",
                    f"{surface.value}/{slot_under_test}/BASELINE-FRESH-CALM: the gate REFUSED "
                    f"the all-fresh calm baseline ({baseline_outcome!r}). *** THIS IS THE "
                    "VACUOUS DIRECTION AND IT IS EQUALLY A VIOLATION OF THIS ROW. *** A tree "
                    "on which the product cannot publish a genuinely fresh calm reading is not "
                    "a tree on which CD-AC-001 holds; it is a tree that has stopped being able "
                    "to say anything. It also means every refusal this run reports is "
                    "attributable to the document skeleton and not to the stamp under test.",
                )
                continue
            check.note(f"{surface.value}/{slot_under_test}/BASELINE-FRESH-CALM: ADMITTED")

            for row_label, stamp, level, expectation in gate_table:
                candidate = copy.deepcopy(baseline)
                mutated, unbuildable_row = build_dial(
                    surface, CALM if level is None else level, stamp
                )
                if unbuildable_row:
                    check.asserted()
                    check.violation(
                        here, 0, "CD-STALE-BUILD-008",
                        f"{surface.value}/{slot_under_test}/{row_label}: unbuildable "
                        f"{unbuildable_row!r} (DECLARED LIMIT 2).",
                    )
                    continue
                if level is None:
                    # The stale-but-not-calm vacuity row: pick a declared level that is NOT
                    # calm, out of the branch's own detail_level subschema, never typed in.
                    schema = schemas[surface]
                    validator = validator_for(schema)
                    _lab, branch = branch_by_surface[surface]
                    sub = (branch.get("properties") or {}).get("detail_level")
                    resolved = _deref(schema, sub)
                    vocabulary = []
                    if isinstance(resolved, dict) and isinstance(resolved.get("enum"), list):
                        vocabulary = [v for v in resolved["enum"] if v != CALM]
                    if not vocabulary:
                        check.asserted()
                        check.violation(
                            here, 0, "CD-STALE-VACUITY-000",
                            f"{surface.value}/{slot_under_test}: the calm-bearing branch's "
                            "detail_level vocabulary contains NOTHING BUT 'calm', so this row "
                            "cannot drive a stale reading that renders at its TRUE level. A "
                            "contract in which the only thing a present dial can say is 'calm' "
                            "leaves the product no way to report a stale reading honestly.",
                        )
                        continue
                    mutated["detail_level"] = vocabulary[0]
                candidate[slot_under_test] = mutated

                label = f"{surface.value}/{slot_under_test}/{row_label}"
                check.asserted()
                cells += 1
                outcome = verdict(surface, candidate)

                if expectation is MUST_ADMIT:
                    if outcome is None:
                        check.note(f"{label}: ADMITTED")
                        continue
                    what = (
                        "*** THE VACUOUS DIRECTION, AND IT IS EQUALLY A VIOLATION OF THIS "
                        "ROW. *** "
                    )
                    if row_label == "EXACTLY-THE-WINDOW":
                        what += (
                            "A reading aged EXACTLY the declared window is INSIDE it: the "
                            "predicate is a CLOSED interval, and a stage that refuses the "
                            "boundary is refusing a reading the declared rule admits. "
                        )
                    elif level is None:
                        what += (
                            "The stage guards `calm` and ONLY `calm` — that is the criterion's "
                            "own scope, 'never renders as CALM'. A stale reading rendering at "
                            "its TRUE level is the product working correctly, and refusing it "
                            "removes the product's only honest way to report a stale dial. "
                        )
                    else:
                        what += (
                            "A genuinely fresh calm reading must still publish. PID §4 makes "
                            "calm the base case, and an instrument satisfied by a contract "
                            "that refuses everything guards nothing. "
                        )
                    check.violation(
                        here, 0, "CD-STALE-GATE-001",
                        f"{label}: {what}The gate REFUSED it: {outcome!r}.",
                    )
                    continue

                # MUST REFUSE.
                if outcome is None:
                    if row_label == "FUTURE":
                        what = (
                            "*** THE LIVE GATE ADMITTED A CALM DIAL STAMPED AFTER THE ENVELOPE "
                            "WAS PUBLISHED. *** Data from the future is INCOHERENT rather than "
                            "fresh, and a NEGATIVE AGE IS NOT A SMALL AGE. This is exactly "
                            "what the obvious `age > window` formula leaves open, and it is "
                            "arm D2 of plants/WO3-INC16E/."
                        )
                    elif row_label == "ONE-MICROSECOND-PAST-THE-WINDOW":
                        what = (
                            "*** THE LIVE GATE ADMITTED A CALM DIAL ONE MICROSECOND PAST THE "
                            "WINDOW THE DOCUMENT ITSELF DECLARES. *** The boundary is decided "
                            "in integer microseconds precisely so it is not a float one ULP "
                            "the wrong side of the edge."
                        )
                    else:
                        what = (
                            "*** THE LIVE GATE ADMITTED A STALE DIAL RENDERING AS CALM. *** "
                            "PID §3.2 is constitutional and its words are 'Missing OR STALE "
                            "data must never render as calm'. The reading is older than the "
                            "staleness window THE DOCUMENT ITSELF DECLARES, and the repair is "
                            "to render it at its true level — never to widen the window."
                        )
                    check.violation(
                        here, 0, "CD-STALE-GATE-001",
                        f"{label}: {what} refuse_unless_publishable returned None and nothing "
                        "stopped the write.",
                    )
                    continue

                # ---- CD-STALE-REASON-002 — THE RIGHT OUTCOME FROM THE RIGHT LAYER ---- #
                # `CD-PL-F74` is this project's most-repeated defect: the right outcome
                # arriving from the wrong layer. A candidate refused as SCHEMA_VIOLATION
                # proves the skeleton is wrong, not that the freshness stage works.
                check.asserted()
                if not isinstance(outcome, PublicationRefused):
                    check.violation(
                        here, 0, "CD-STALE-REASON-002",
                        f"{label}: the gate raised {type(outcome).__name__} and not the "
                        f"declared PublicationRefused: {outcome!r}. An unexpected exception is "
                        "not a refusal (CD-PL-F74).",
                    )
                    continue
                expected_pointer = f"/{slot_under_test}"
                if (outcome.reason_class != REFUSAL_STALE_CALM
                        or outcome.pointer != expected_pointer):
                    check.violation(
                        here, 0, "CD-STALE-REASON-002",
                        f"{label}: REFUSED with reason_class {outcome.reason_class!r} at "
                        f"{outcome.pointer!r}, and this row requires {REFUSAL_STALE_CALM!r} at "
                        f"{expected_pointer!r}. A refusal from ANOTHER layer — a schema "
                        "violation caused by this check's own skeleton, for instance — would "
                        "otherwise be counted as the freshness stage working, which is the "
                        "right outcome from the wrong layer (CD-PL-F74).",
                    )
                    continue
                check.note(
                    f"{label}: REFUSED [{outcome.reason_class}] at {outcome.pointer} "
                    f"key {outcome.key!r}"
                )

                # ---- CD-STALE-PAIRED-003 — ONE TOKEN MOVED, OPPOSITE OUTCOME --------- #
                # The refusal must be caused by the STAMP. The refused candidate and the
                # ADMITTED baseline must be the same document apart from the stamp(s) of the
                # slot under test.
                #
                # *** THE GUARD BELOW WAS WRITTEN INVERTED IN THIS FILE'S FIRST DRAFT AND THIS
                # WHOLE LIMB WAS DEAD. RAISED BY THIS SEAT AGAINST ITS OWN WORK AS
                # `CD-ENG-F16E-01` AND CAUGHT ON THE FIRST RUN, because the run printed not one
                # `PAIRED` note. It read `if level is not None: continue`, and every MUST-REFUSE
                # row carries `level = CALM`, so it skipped every one of them; the only row with
                # `level is None` is the stale-but-not-calm VACUITY row, which is `MUST_ADMIT`
                # and has already `continue`d above. **A DEAD ASSERTION DETECTS NOTHING WHILE
                # LOOKING LIKE COVERAGE**, in a file whose entire subject is a guarantee nobody
                # ran. Fixed, and RECORDED rather than quietly corrected.
                if level is None:
                    continue
                check.asserted()
                differing = _differing_pointers(candidate, baseline)
                expected = sorted(f"/{slot_under_test}/{key}" for key in stamps)
                if differing != expected:
                    check.violation(
                        here, 0, "CD-STALE-PAIRED-003",
                        f"{label}: the refused candidate and its ADMITTED pair differ at "
                        f"{differing!r}, not at exactly {expected!r}. The two documents must "
                        "be identical apart from the stamp under test, or the opposite "
                        "outcomes cannot be attributed to it.",
                    )
                else:
                    check.note(f"{label}: PAIRED — sole difference {expected!r}")

    # ================================================================================== #
    # LIMB B — THE STAGE ITSELF. DECLARED LIMIT 3.
    # This is the limb `D3` (the forbidden slot-read) and `D4` (newest-governs) are measured
    # against, and it is where the FAIL-CLOSED branches live.
    # ================================================================================== #
    def stage_outcome(surface, document):
        try:
            _refuse_stale_calm(copy.deepcopy(document), surface)
        except PublicationRefused as exc:
            return exc
        except Exception as other:
            return other
        return None

    NON_DIAL_ROOT = "synthetic_16e_probe"

    for surface in EnvelopeSurface:
        slots = slots_by_surface[surface]
        stamps = stamps_by_surface[surface]
        fresh_dial, unbuildable = build_dial(surface, CALM, STAMP_FRESH)
        if unbuildable:
            continue
        dials = {slot: copy.deepcopy(fresh_dial) for slot in slots}
        base_document, root_unbuildable = build_root(surface, dials)
        if root_unbuildable:
            continue

        # ---- CD-STALE-NODES-004 — IT QUANTIFIES OVER NODES, NOT OVER DIAL SLOTS ------ #
        # Every position here is one a slot-reading implementation cannot see. The paired
        # FRESH arm is what stops this becoming "refuse anything that is not a dial".
        first_slot = slots[0]
        positions = [
            (
                "NON-DIAL-ROOT-PROPERTY",
                lambda doc, node: doc.__setitem__(NON_DIAL_ROOT, node),
                f"/{NON_DIAL_ROOT}",
            ),
            (
                "TWO-CONTAINERS-DEEP-IN-AN-ARRAY",
                lambda doc, node: doc.__setitem__(NON_DIAL_ROOT, [[node]]),
                f"/{NON_DIAL_ROOT}/0/0",
            ),
            (
                "INSIDE-A-DIAL-S-OWN-ARRAY",
                lambda doc, node: doc[first_slot].__setitem__("contributions", [node]),
                f"/{first_slot}/contributions/0",
            ),
        ]
        for position_label, place, expected_pointer in positions:
            for arm_label, stamp, expectation in (
                ("STALE", STAMP_ANCIENT, MUST_REFUSE),
                ("FRESH", STAMP_FRESH, MUST_ADMIT),
            ):
                document = copy.deepcopy(base_document)
                place(document, {"detail_level": CALM, "planted_utc": stamp})
                label = f"{surface.value}/LIMB-B/{position_label}/{arm_label}"
                check.asserted()
                outcome = stage_outcome(surface, document)
                if expectation is MUST_ADMIT:
                    if outcome is None:
                        check.note(f"{label}: NOT REFUSED (correct — the node is fresh)")
                    else:
                        check.violation(
                            here, 0, "CD-STALE-NODES-004",
                            f"{label}: *** THE VACUOUS DIRECTION. *** A calm node at "
                            f"{expected_pointer} carrying a FRESH stamp was REFUSED "
                            f"({outcome!r}). The stage must refuse the STALE calm node and "
                            "nothing else; a stage that refuses a fresh one wherever it sits "
                            "is refusing position rather than age.",
                        )
                    continue
                if outcome is None:
                    check.violation(
                        here, 0, "CD-STALE-NODES-004",
                        f"{label}: *** A CALM-BEARING NODE AT {expected_pointer} CARRYING A "
                        "FIFTY-SIX-YEAR-OLD STAMP WAS NOT REFUSED. *** The stage must "
                        "quantify over NODES and never over the dial slots that happen to "
                        "exist today: 'does this node claim calm, and can it prove it earned "
                        "it?' — not 'is this one of the dials I know about?'. An "
                        "implementation that reads `candidate[\"equity_crash\"]` is silent on "
                        "the third slot a contract edit adds tomorrow, and that recogniser-"
                        "over-an-open-set is the defect class that lost eleven consecutive "
                        "audit rounds on this row. This is arm D3 of plants/WO3-INC16E/.",
                    )
                    continue
                if not isinstance(outcome, PublicationRefused):
                    check.violation(
                        here, 0, "CD-STALE-NODES-004",
                        f"{label}: the stage raised {type(outcome).__name__} and not "
                        f"PublicationRefused: {outcome!r} (CD-PL-F74).",
                    )
                    continue
                if (outcome.reason_class != REFUSAL_STALE_CALM
                        or outcome.pointer != expected_pointer):
                    check.violation(
                        here, 0, "CD-STALE-NODES-004",
                        f"{label}: REFUSED [{outcome.reason_class}] at {outcome.pointer!r}, "
                        f"and this row requires {REFUSAL_STALE_CALM!r} at "
                        f"{expected_pointer!r}. The refusal must name the node that could not "
                        "prove its freshness, or a reader cannot act on it.",
                    )
                    continue
                check.note(f"{label}: REFUSED [{outcome.reason_class}] at {outcome.pointer}")

        # ---- CD-STALE-OLDEST-005 — THE OLDEST STAMP GOVERNS -------------------------- #
        # Value-detection of stamps is only safe in the direction that matters BECAUSE the
        # oldest governs: adding a fresh-looking string to a node can never rescue it.
        oldest_arms = (
            (
                "STALE-BESIDE-TWO-FRESHER-SIBLINGS",
                {"detail_level": CALM, "a_planted_utc": STAMP_ANCIENT,
                 "b_planted_utc": STAMP_SECOND_FRESH, "c_planted_utc": STAMP_THIRD_FRESH},
                MUST_REFUSE, "a_planted_utc",
            ),
            (
                "ALL-THREE-STAMPS-FRESH",
                {"detail_level": CALM, "a_planted_utc": STAMP_FRESH,
                 "b_planted_utc": STAMP_SECOND_FRESH, "c_planted_utc": STAMP_THIRD_FRESH},
                MUST_ADMIT, None,
            ),
        )
        for arm_label, node, expectation, oldest_key in oldest_arms:
            document = copy.deepcopy(base_document)
            document[NON_DIAL_ROOT] = copy.deepcopy(node)
            label = f"{surface.value}/LIMB-B/OLDEST-GOVERNS/{arm_label}"
            check.asserted()
            outcome = stage_outcome(surface, document)
            if expectation is MUST_ADMIT:
                if outcome is None:
                    check.note(f"{label}: NOT REFUSED (correct — every stamp is fresh)")
                else:
                    check.violation(
                        here, 0, "CD-STALE-OLDEST-005",
                        f"{label}: *** THE VACUOUS DIRECTION. *** A calm node whose stamps are "
                        f"ALL fresh was REFUSED ({outcome!r}). 'The oldest governs' must not "
                        "degenerate into 'more than one stamp is suspicious'.",
                    )
                continue
            if not isinstance(outcome, PublicationRefused):
                check.violation(
                    here, 0, "CD-STALE-OLDEST-005",
                    f"{label}: *** A CALM NODE WHOSE OLDEST STAMP IS FIFTY-SIX YEARS OLD WAS "
                    f"NOT REFUSED ({outcome!r}). *** Two fresher siblings rescued it, so the "
                    "NEWEST stamp is governing. A node is only as fresh as its OLDEST readable "
                    "stamp — the envelope's own declared doctrine, 'as fresh as its oldest "
                    "input, never as fresh as the last time we asked'. If the newest governs, "
                    "adding one fresh-looking string to a stale node launders it, and stamps "
                    "are detected BY VALUE. This is arm D4 of plants/WO3-INC16E/.",
                )
                continue
            if outcome.key != oldest_key:
                check.violation(
                    here, 0, "CD-STALE-OLDEST-005",
                    f"{label}: REFUSED, but the refusal names key {outcome.key!r} and the "
                    f"OLDEST stamp on that node is {oldest_key!r}. The refusal must name the "
                    "stamp that governed, or the reader cannot tell WHICH stamp made the node "
                    "stale — and a refusal that names a fresher stamp is the newest-governs "
                    "bug reporting itself as the oldest-governs rule.",
                )
                continue
            check.note(
                f"{label}: REFUSED [{outcome.reason_class}] at {outcome.pointer} naming the "
                f"OLDEST key {outcome.key!r}"
            )

        # ---- CD-STALE-CLOSED-006 — FAIL CLOSED AT EVERY BRANCH ----------------------- #
        # "Where a check cannot reach its authentic target it must fail, never wave through"
        # (Standards Baseline §16, PBG-CI-002). There is no "cannot tell, so allow" branch in
        # this stage, and this assertion is what stops one being added.
        closed_arms = [
            ("NO-STAMP-AT-ALL", {"detail_level": CALM}, WINDOW_SECONDS, PUBLISHED),
            (
                "A-PROPERTY-THAT-ANNOUNCES-ITSELF-AS-A-STAMP-AND-DOES-NOT-PARSE",
                {"detail_level": CALM, "planted_utc": STAMP_FRESH, "broken_utc": NOT_A_STAMP},
                WINDOW_SECONDS, PUBLISHED,
            ),
        ]
        for window_label, window_value in UNUSABLE_WINDOWS:
            closed_arms.append((
                f"WINDOW-{window_label}",
                {"detail_level": CALM, "planted_utc": STAMP_FRESH},
                window_value, PUBLISHED,
            ))
        for published_label, published_value in UNUSABLE_PUBLISHED:
            closed_arms.append((
                f"PUBLISHED-{published_label}",
                {"detail_level": CALM, "planted_utc": STAMP_FRESH},
                WINDOW_SECONDS, published_value,
            ))
        for arm_label, node, window_value, published_value in closed_arms:
            document, unbuildable_root = build_root(
                surface, dials, window=window_value, published=published_value
            )
            if unbuildable_root:
                continue
            if isinstance(window_value, float) and math.isnan(window_value):
                document["staleness_window_seconds"] = window_value
            document[NON_DIAL_ROOT] = copy.deepcopy(node)
            label = f"{surface.value}/LIMB-B/FAIL-CLOSED/{arm_label}"
            check.asserted()
            outcome = stage_outcome(surface, document)
            if isinstance(outcome, PublicationRefused) \
                    and outcome.reason_class == REFUSAL_STALE_CALM:
                check.note(
                    f"{label}: REFUSED [{outcome.reason_class}] at {outcome.pointer} "
                    f"key {outcome.key!r}"
                )
                continue
            check.violation(
                here, 0, "CD-STALE-CLOSED-006",
                f"{label}: this arm removes the stage's ability to compute an age and the "
                f"stage did NOT refuse — it returned {outcome!r}. A node whose age CANNOT be "
                "computed has not proved it is fresh, and an unprovable freshness claim is "
                "REFUSED rather than assumed. There is no 'cannot tell, so allow' branch in "
                "this stage and this assertion exists so one cannot be added quietly "
                "(PBG-CI-002, Standards Baseline §16).",
            )

        # ---- CD-STALE-CLOSED-006, THE PAIRED NON-VACUITY ----------------------------- #
        document, unbuildable_root = build_root(surface, dials)
        if not unbuildable_root:
            document[NON_DIAL_ROOT] = {"detail_level": CALM, "planted_utc": STAMP_FRESH}
            label = f"{surface.value}/LIMB-B/FAIL-CLOSED/USABLE-WINDOW-AND-FRESH-NODE"
            check.asserted()
            outcome = stage_outcome(surface, document)
            if outcome is None:
                check.note(f"{label}: NOT REFUSED (correct — the arms above are not vacuous)")
            else:
                check.violation(
                    here, 0, "CD-STALE-CLOSED-006",
                    f"{label}: *** THE VACUOUS DIRECTION. *** With a real, finite, positive "
                    "window, a readable published_utc and a FRESH stamp, the stage still "
                    f"refused ({outcome!r}). Every fail-closed arm above is then satisfied by "
                    "a stage that refuses unconditionally, which detects nothing.",
                )

        # ---- CD-STALE-SCOPE-009 — THE DECLARED SCOPE, DRIVEN RATHER THAN ASSERTED ---- #
        # DECLARED LIMIT 8. The gate proves INTERNAL COHERENCE and never ACTUAL freshness, and
        # this row states that as its declared scope. A limit stated in prose goes stale in the
        # reassuring direction; this one is MEASURED at every run, so the day the product
        # closes the class this assertion goes RED and somebody must come and rewrite the
        # limit rather than discover it is obsolete.
        shifted_dial, unbuildable_shift = build_dial(surface, CALM, STAMP_ANCIENT)
        if not unbuildable_shift:
            shifted_dials = {slot: copy.deepcopy(shifted_dial) for slot in slots}
            shifted, unbuildable_root = build_root(
                surface, shifted_dials, window=WINDOW_SECONDS, published=STAMP_ANCIENT
            )
            if not unbuildable_root:
                shifted["as_of_utc"] = STAMP_ANCIENT
                label = f"{surface.value}/DECLARED-SCOPE/UNIFORMLY-TIME-SHIFTED-ENVELOPE"
                check.asserted()
                outcome = verdict(surface, shifted)
                if outcome is None:
                    check.note(
                        f"{label}: ADMITTED — and that is the DECLARED SCOPE of this guard, "
                        "measured rather than asserted. The gate enforces DOCUMENT-INTERNAL "
                        "freshness (published_utc minus the node's oldest stamp against the "
                        "declared window) and CANNOT catch a source that consistently LIES "
                        "about its own stamp. SOURCE HONESTY IS THE DETECTION TIER — witness "
                        "divergence + provenance, CD-AC-018 — ENFORCED ONE TIER OUT AND OWED "
                        "AT WO-3 (PO-DECISIONS-0030 ruling 2). It is NOT unenforceable."
                    )
                else:
                    check.violation(
                        here, 0, "CD-STALE-SCOPE-009",
                        f"{label}: this row's DECLARED SCOPE says a uniformly time-shifted "
                        "envelope — every stamp AND published_utc moved together — is ADMITTED, "
                        "because a document-internal comparison cannot see it. The gate "
                        f"REFUSED it instead ({outcome!r}). Either the product has closed that "
                        "class, in which case DECLARED LIMIT 8 is now FALSE and must be "
                        "rewritten in all three CD-RULE-004 places rather than left to go "
                        "stale in the reassuring direction; or something else refused this "
                        "document and the limit is being proved by the wrong layer (CD-PL-F74).",
                    )

    # ================================================================================== #
    # *** WO-3 INCREMENT 16F — THE INVARIANCE PASS. THE INSTRUMENT PROBES THE SPACE. ***
    # `PO-DECISIONS-0031` ruling 1(i), answering `A313-F1` (HIGH).
    #
    # THE PROPOSITION, AND IT IS AN INDEPENDENCE RATHER THAN A LIST OF SHAPES:
    #
    #     THE GATE'S STALE-CALM VERDICT DEPENDS ON EXACTLY THREE THINGS — THE CALM-BEARING
    #     NODE'S OWN STAMPS, THE ROOT'S `published_utc`, AND THE ROOT'S
    #     `staleness_window_seconds` — AND ON NOTHING ELSE. VARY ANY OTHER PROPERTY OF THE
    #     DOCUMENT TO ANY OTHER VALUE, AND THE VERDICT MUST NOT CHANGE.
    #
    # A weakening keyed on ANY other property is a DEPENDENCE on a property the criterion says
    # nothing about, and a dependence is what an invariance check detects. That is why this is
    # complete BY CONSTRUCTION over the vocabulary it varies rather than by enumeration: the
    # four `D` arms, `W5A`, `W5B2`, `W5G` and shapes nobody has named are all the same shape to
    # it. **IT IS NOT A FIFTH ARM.**
    #
    # THE VERDICT IS COMPARED AS A FOUR-TUPLE — (admitted/refused, reason class, pointer, key) —
    # and never as a boolean, so a weakening that keeps the refusal but moves it to another
    # layer or another pointer is a CHANGE (`CD-PL-F74`).
    #
    # *** AND THE VACUITY DIRECTION IS EQUALLY A VIOLATION, WHICH IS HARDER HERE THAN ANYWHERE
    # ELSE IN THIS FILE: AN INSTRUMENT THAT REFUSES EVERYTHING EVERYWHERE IS PERFECTLY
    # INVARIANT. *** So the row set driven at EVERY point in the varied space carries the
    # MUST-ADMIT rows as well as the MUST-REFUSE ones — a genuinely fresh calm dial, a dial
    # aged EXACTLY the window, and a stale dial rendering at its true level — and the
    # reference point itself is checked against its EXPECTATION before anything is compared
    # against it, so the pass cannot be invariance around the wrong point.
    # ================================================================================== #

    invariant_rows = (
        ("ANCIENT", STAMP_ANCIENT, CALM, MUST_REFUSE),
        ("FUTURE", STAMP_FUTURE, CALM, MUST_REFUSE),
        ("WELL-INSIDE-THE-WINDOW", STAMP_FRESH, CALM, MUST_ADMIT),
        ("EXACTLY-THE-WINDOW", STAMP_ON_THE_EDGE, CALM, MUST_ADMIT),
        ("ANCIENT-BUT-NOT-CALM", STAMP_ANCIENT, None, MUST_ADMIT),
    )

    non_calm_level = {}
    for surface in EnvelopeSurface:
        _lab, branch = branch_by_surface[surface]
        resolved = _deref(schemas[surface], (branch.get("properties") or {}).get("detail_level"))
        vocabulary = []
        if isinstance(resolved, dict) and isinstance(resolved.get("enum"), list):
            vocabulary = [value for value in resolved["enum"] if value != CALM]
        non_calm_level[surface] = vocabulary[0] if vocabulary else None

    def invariant_dial(surface, stamp, level):
        dial, unbuildable_dial = build_dial(surface, CALM if level is None else level, stamp)
        if unbuildable_dial:
            return None
        if level is None:
            if non_calm_level[surface] is None:
                return None
            dial["detail_level"] = non_calm_level[surface]
        return dial

    reported = {}

    def report(rule: str, message: str) -> None:
        """Record a violation, but never print ten thousand of them.

        The varied space is thousands of cells wide and a stage that has stopped working fails
        most of them. `VIOLATION_REPORT_CAP` distinct findings per rule are printed in full and
        the rest are COUNTED — the count is printed as a note and the exit code is non-zero
        either way, so nothing is hidden and the output stays readable.
        """
        reported[rule] = reported.get(rule, 0) + 1
        if reported[rule] <= VIOLATION_REPORT_CAP:
            check.violation(here, 0, rule, message)

    invariance_points = 0
    invariance_cells = 0
    invariance_skipped = 0
    coverage_lines = []

    # ---------------------------------------------------------------------------------- #
    # LIMB A — THE LIVE GATE, THROUGH THE FRONT DOOR, OVER THE SPACE OF DOCUMENTS THE
    # CONTRACT ADMITS. One-at-a-time variation from a proved-publishable baseline.
    # ---------------------------------------------------------------------------------- #
    for surface in EnvelopeSurface:
        schema = schemas[surface]
        validator = validator_for(schema)
        document_validator = validator(schema)
        pool = _variation_pool(schema)
        root_properties = schema.get("properties") or {}
        slots = slots_by_surface[surface]
        check.note(
            f"{surface.value}: INVARIANCE VOCABULARY — product words harvested from the "
            f"contract itself: {_product_vocabulary(schema)!r}"
        )

        fresh_dial, unbuildable = build_dial(surface, CALM, STAMP_FRESH)
        if unbuildable:
            check.asserted()
            report(
                "CD-STALE-INVARIANT-010",
                f"{surface.value}: the calm-bearing dial could not be built, so the invariance "
                f"pass drove NOTHING on this surface ({unbuildable!r}). DENY BY DEFAULT.",
            )
            continue

        for slot_under_test in slots:
            dials = {slot: copy.deepcopy(fresh_dial) for slot in slots}
            reference_root, root_unbuildable = build_root(surface, dials)
            if root_unbuildable:
                check.asserted()
                report(
                    "CD-STALE-INVARIANT-010",
                    f"{surface.value}: the envelope root could not be built "
                    f"({root_unbuildable!r}), so the invariance pass drove NOTHING.",
                )
                continue

            # -- THE REFERENCE POINT, AND IT IS CHECKED AGAINST ITS EXPECTATION FIRST ---- #
            row_documents = {}
            reference = {}
            usable = True
            for row_label, stamp, level, expectation in invariant_rows:
                dial = invariant_dial(surface, stamp, level)
                if dial is None:
                    usable = False
                    break
                document = copy.deepcopy(reference_root)
                document[slot_under_test] = dial
                row_documents[row_label] = document
                check.asserted()
                signature = _signature(verdict(surface, document))
                reference[row_label] = signature
                label = f"{surface.value}/{slot_under_test}/{row_label}"
                if expectation is MUST_ADMIT and signature[0] != "ADMITTED":
                    usable = False
                    report(
                        "CD-STALE-INVARIANT-010",
                        f"{label}: *** THE VACUOUS DIRECTION AT THE REFERENCE POINT. *** the "
                        f"unvaried document this pass varies FROM was not ADMITTED "
                        f"({signature!r}). Every comparison below would then be invariance "
                        "around a point the product cannot publish, which is a tree that has "
                        "stopped being able to say anything (PID §4).",
                    )
                elif expectation is MUST_REFUSE and signature != (
                    "REFUSED", REFUSAL_STALE_CALM, f"/{slot_under_test}",
                    signature[3],
                ):
                    usable = False
                    report(
                        "CD-STALE-INVARIANT-010",
                        f"{label}: the unvaried reference document was not REFUSED "
                        f"[{REFUSAL_STALE_CALM}] at /{slot_under_test} — it produced "
                        f"{signature!r}. The invariance comparison below would be anchored on "
                        "a verdict that is already wrong, and a refusal from ANOTHER layer "
                        "would then be held invariant and counted as the stage working "
                        "(CD-PL-F74).",
                    )
            if not usable:
                continue

            # -- THE SPACE: EVERY ROOT PROPERTY, ENUMERATED FROM THE CONTRACT ITSELF ----- #
            for name in sorted(root_properties):
                if name in (ROOT_PUBLISHED_KEY, ROOT_WINDOW_KEY):
                    coverage_lines.append(
                        f"{surface.value}/LIMB-A/{name}: NOT VARIED — it is one of the three "
                        "VERDICT INPUTS the invariant is stated in terms of."
                    )
                    continue
                if name == slot_under_test:
                    coverage_lines.append(
                        f"{surface.value}/LIMB-A/{name}: NOT VARIED at this position — it is "
                        "the slot under test and its own stamps are a VERDICT INPUT."
                    )
                    continue
                variants = _admissible_variants(
                    schema, root_properties[name], validator,
                    reference_root.get(name), pool,
                )
                coverage_lines.append(
                    f"{surface.value}/LIMB-A/{name}: {len(variants)} alternative admissible "
                    f"value(s) driven — {[label for _f, label, _v in variants]!r}"
                )
                for _family, value_label, value in variants:
                    invariance_points += 1
                    for row_label, _stamp, _level, _expectation in invariant_rows:
                        candidate = copy.deepcopy(row_documents[row_label])
                        candidate[name] = copy.deepcopy(value)
                        if not document_validator.is_valid(candidate):
                            # The property's OWN subschema accepts this value but the whole
                            # document does not. Driving it would measure the SCHEMA stage and
                            # attribute the result to the freshness stage (CD-PL-F74). Counted,
                            # never silently dropped.
                            invariance_skipped += 1
                            continue
                        check.asserted()
                        invariance_cells += 1
                        signature = _signature(verdict(surface, candidate))
                        if signature != reference[row_label]:
                            report(
                                "CD-STALE-INVARIANT-010",
                                f"{surface.value}/{slot_under_test}/{row_label} with root "
                                f"property {name!r} varied to {value_label} — *** THE GATE'S "
                                "STALE-CALM VERDICT CHANGED ON A PROPERTY THE CRITERION SAYS "
                                f"NOTHING ABOUT. *** unvaried: {reference[row_label]!r}; "
                                f"varied: {signature!r}. The verdict may depend on the "
                                "calm-bearing node's own stamps, on the root's "
                                f"{ROOT_PUBLISHED_KEY!r} and on the root's {ROOT_WINDOW_KEY!r}, "
                                "and on NOTHING ELSE. A dependence on anything else is either "
                                "a weakening (some documents now escape the stage) or an "
                                "over-refusal (some documents the product must publish now "
                                "cannot be) — and BOTH are violations of this row.",
                            )

            # -- AND THE CALM-BEARING NODE'S OWN NON-STAMP PROPERTIES ------------------- #
            # `W5A` keys on a ROOT property; a shape keyed on the node's own `score`,
            # `inputs_used` or `contributions` is the same defect ONE LEVEL DOWN, and the
            # invariant's "everything else" contains it.
            _branch_label, calm_branch = branch_by_surface[surface]
            node_properties = calm_branch.get("properties") or {}
            for name in sorted(node_properties):
                if name in stamps_by_surface[surface]:
                    coverage_lines.append(
                        f"{surface.value}/LIMB-A/NODE/{name}: NOT VARIED — a STAMP-SHAPED "
                        "property of the calm-bearing node is a VERDICT INPUT."
                    )
                    continue
                if name == "detail_level":
                    coverage_lines.append(
                        f"{surface.value}/LIMB-A/NODE/detail_level: NOT VARIED — it is what "
                        "makes the node a SUBJECT of the criterion at all, not an independent "
                        "property of it. It IS varied, as the level, by the row set."
                    )
                    continue
                variants = _admissible_variants(
                    schema, node_properties[name], validator,
                    fresh_dial.get(name), pool, exclude_stamp_like=True,
                )
                coverage_lines.append(
                    f"{surface.value}/LIMB-A/NODE/{name}: {len(variants)} alternative "
                    f"admissible value(s) driven — "
                    f"{[label for _f, label, _v in variants]!r}"
                )
                for _family, value_label, value in variants:
                    invariance_points += 1
                    for row_label, _stamp, _level, _expectation in invariant_rows:
                        candidate = copy.deepcopy(row_documents[row_label])
                        node = candidate.get(slot_under_test)
                        if not isinstance(node, dict) or name not in node:
                            invariance_skipped += 1
                            continue
                        node[name] = copy.deepcopy(value)
                        if not document_validator.is_valid(candidate):
                            invariance_skipped += 1
                            continue
                        check.asserted()
                        invariance_cells += 1
                        signature = _signature(verdict(surface, candidate))
                        if signature != reference[row_label]:
                            report(
                                "CD-STALE-INVARIANT-010",
                                f"{surface.value}/{slot_under_test}/{row_label} with the "
                                f"CALM-BEARING NODE'S OWN property {name!r} varied to "
                                f"{value_label} — *** THE VERDICT CHANGED ON A PROPERTY OF THE "
                                "NODE THAT IS NOT ONE OF ITS STAMPS. *** unvaried: "
                                f"{reference[row_label]!r}; varied: {signature!r}. Freshness "
                                "is proved from the node's STAMPS and from the root's two "
                                "comparands; a stage that also reads the node's score, its "
                                "inputs or its contributions is deciding freshness from "
                                "something that is not a time.",
                            )

    # ---------------------------------------------------------------------------------- #
    # LIMB B — THE STAGE ITSELF, OVER A WIDER SPACE THAN THE CONTRACT ADMITS, AND THE ONLY
    # PLACE THE PAIRWISE PASS RUNS. `DECLARED LIMIT 10` states why.
    # ---------------------------------------------------------------------------------- #
    def planted_node(stamp):
        """A calm-bearing node with NON-STAMP properties of its own to vary."""
        return {
            "detail_level": CALM,
            "planted_utc": stamp,
            "state": "VALUE",
            "score": SYNTHETIC_SCORE,
            "inputs_used": [SYNTHETIC_INPUT_ID],
            "contributions": [],
        }

    NON_STAMP_NODE_KEYS = ("state", "score", "inputs_used", "contributions")

    for surface in EnvelopeSurface:
        schema = schemas[surface]
        pool = _variation_pool(schema)
        slots = slots_by_surface[surface]
        fresh_dial, unbuildable = build_dial(surface, CALM, STAMP_FRESH)
        if unbuildable:
            continue
        dials = {slot: copy.deepcopy(fresh_dial) for slot in slots}
        base_document, root_unbuildable = build_root(surface, dials)
        if root_unbuildable:
            continue

        arms = (
            ("STALE", STAMP_ANCIENT, MUST_REFUSE),
            ("FRESH", STAMP_FRESH, MUST_ADMIT),
        )

        def limb_b_document(stamp, root_changes=(), node_changes=()):
            document = dict(base_document)
            node = planted_node(stamp)
            for key, value in node_changes:
                if value is _ABSENT:
                    node.pop(key, None)
                else:
                    node[key] = value
            document[NON_DIAL_ROOT] = node
            for key, value in root_changes:
                if value is _ABSENT:
                    document.pop(key, None)
                else:
                    document[key] = value
            return document

        # The invariance pass drives the stage ~140,000 times, so it composes a FRESH root
        # mapping and a FRESH node mapping per cell and does NOT deep-copy the whole document
        # (which costs more than the stage call). The stage's own contract says the candidate
        # is never mutated; **that is ASSERTED rather than trusted** by
        # `CD-STALE-INVARIANT-013` below, which compares the base document against a snapshot
        # taken before the pass.
        untouched_snapshot = copy.deepcopy(base_document)

        def stage_signature(surface_, document):
            try:
                _refuse_stale_calm(document, surface_)
            except PublicationRefused as exc:
                return _signature(exc)
            except Exception as other:  # noqa: BLE001
                return _signature(other)
            return _signature(None)

        reference_b = {}
        usable = True
        for arm_label, stamp, expectation in arms:
            check.asserted()
            signature = stage_signature(surface, limb_b_document(stamp))
            reference_b[arm_label] = signature
            if expectation is MUST_ADMIT and signature[0] != "ADMITTED":
                usable = False
                report(
                    "CD-STALE-INVARIANT-011",
                    f"{surface.value}/LIMB-B/{arm_label}: *** THE VACUOUS DIRECTION AT THE "
                    f"REFERENCE POINT. *** the FRESH planted calm node was REFUSED "
                    f"({signature!r}), so every invariance comparison below would be anchored "
                    "on a stage that refuses what it must admit.",
                )
            if expectation is MUST_REFUSE and (
                signature[0] != "REFUSED" or signature[1] != REFUSAL_STALE_CALM
                or signature[2] != f"/{NON_DIAL_ROOT}"
            ):
                usable = False
                report(
                    "CD-STALE-INVARIANT-011",
                    f"{surface.value}/LIMB-B/{arm_label}: the unvaried reference was "
                    f"{signature!r} and this row requires REFUSED [{REFUSAL_STALE_CALM}] at "
                    f"/{NON_DIAL_ROOT}.",
                )
        if not usable:
            continue

        # -- THE POINTS: root properties AND the planted node's own non-stamp properties -- #
        points = []
        for name in sorted(base_document):
            if name in (ROOT_PUBLISHED_KEY, ROOT_WINDOW_KEY):
                coverage_lines.append(
                    f"{surface.value}/LIMB-B/{name}: NOT VARIED — VERDICT INPUT."
                )
                continue
            values = [("ABSENCE", "ABSENT", _ABSENT)]
            values.extend(
                (family, label, value) for family, label, value in pool
                if not _same_value(value, base_document.get(name))
            )
            points.append(("ROOT", name, values))
        for name in VARIATION_EXTRA_ROOT_KEYS:
            points.append((
                "ROOT", name,
                [(family, label, value) for family, label, value in pool],
            ))
        node_reference = planted_node(STAMP_FRESH)
        for name in NON_STAMP_NODE_KEYS + VARIATION_EXTRA_NODE_KEYS:
            values = []
            if name in node_reference:
                values.append(("ABSENCE", "ABSENT", _ABSENT))
            for family, label, value in pool:
                if isinstance(value, str) and _STAMP_SHAPE_RE.match(value):
                    continue
                if _same_value(value, node_reference.get(name)):
                    continue
                values.append((family, label, value))
            points.append(("NODE", name, values))
        for scope, name, values in points:
            coverage_lines.append(
                f"{surface.value}/LIMB-B/{scope}/{name}: {len(values)} value(s) driven"
            )

        # -- ONE AT A TIME ---------------------------------------------------------------- #
        for scope, name, values in points:
            for _family, value_label, value in values:
                invariance_points += 1
                for arm_label, stamp, _expectation in arms:
                    change = ((name, value),)
                    document = limb_b_document(
                        stamp,
                        root_changes=change if scope == "ROOT" else (),
                        node_changes=change if scope == "NODE" else (),
                    )
                    check.asserted()
                    invariance_cells += 1
                    signature = stage_signature(surface, document)
                    if signature != reference_b[arm_label]:
                        report(
                            "CD-STALE-INVARIANT-011",
                            f"{surface.value}/LIMB-B/{arm_label} with {scope} property "
                            f"{name!r} varied to {value_label} — *** THE STAGE'S VERDICT "
                            "CHANGED ON A PROPERTY THE CRITERION SAYS NOTHING ABOUT. *** "
                            f"unvaried: {reference_b[arm_label]!r}; varied: {signature!r}. "
                            "LIMB B drives the stage DIRECTLY, so this space is wider than "
                            "the one the closed contract admits — which is the point: a "
                            "weakening does not have to be reachable through the front door "
                            "on today's contract to be a weakening.",
                        )

        # -- PAIRWISE, FOR THE CONJUNCTIVE PREDICATE. `DECLARED LIMIT 10`. ---------------- #
        # ONE-AT-A-TIME variation catches every predicate keyed on a SINGLE property, which is
        # every shape measured on this project so far. It does NOT catch a CONJUNCTION over
        # two properties: `if regime == "calm" and len(inputs_used) > 1: return` is invisible
        # to it, because neither half alone changes the verdict. This pass drives ORDERED
        # PAIRS from DIFFERENT properties over a REDUCED per-property value set, and it runs
        # on LIMB B only because a LIMB A pairwise pass is ~2000x more expensive per cell
        # (MEASURED: the front door reloads and recompiles the contract on every call).
        reduced = [
            (scope, name, _pairwise_reduction(values))
            for scope, name, values in points
        ]
        total_pairs = 0
        for index, (scope_a, name_a, values_a) in enumerate(reduced):
            for scope_b, name_b, values_b in reduced[index + 1:]:
                total_pairs += len(values_a) * len(values_b)
        stride = 1
        if total_pairs * len(arms) > PAIRWISE_CELL_BUDGET:
            stride = (total_pairs * len(arms) // PAIRWISE_CELL_BUDGET) + 1
        check.note(
            f"{surface.value}/LIMB-B/PAIRWISE: {total_pairs} property-value pairs over "
            f"{len(reduced)} properties, stride {stride} (budget "
            f"{PAIRWISE_CELL_BUDGET} cells — DECLARED LIMIT 10)"
        )
        counter = 0
        for index, (scope_a, name_a, values_a) in enumerate(reduced):
            for scope_b, name_b, values_b in reduced[index + 1:]:
                for _fa, label_a, value_a in values_a:
                    for _fb, label_b, value_b in values_b:
                        counter += 1
                        if counter % stride:
                            continue
                        root_changes = []
                        node_changes = []
                        (root_changes if scope_a == "ROOT" else node_changes).append(
                            (name_a, value_a))
                        (root_changes if scope_b == "ROOT" else node_changes).append(
                            (name_b, value_b))
                        for arm_label, stamp, _expectation in arms:
                            document = limb_b_document(
                                stamp,
                                root_changes=tuple(root_changes),
                                node_changes=tuple(node_changes),
                            )
                            check.asserted()
                            invariance_cells += 1
                            signature = stage_signature(surface, document)
                            if signature != reference_b[arm_label]:
                                report(
                                    "CD-STALE-INVARIANT-011",
                                    f"{surface.value}/LIMB-B/{arm_label} with "
                                    f"{scope_a}/{name_a}={label_a} AND "
                                    f"{scope_b}/{name_b}={label_b} — *** THE STAGE'S VERDICT "
                                    "CHANGED ON A CONJUNCTION OF TWO PROPERTIES THE CRITERION "
                                    f"SAYS NOTHING ABOUT. *** unvaried: "
                                    f"{reference_b[arm_label]!r}; varied: {signature!r}.",
                                )

        # -- CD-STALE-INVARIANT-013 — THE STAGE MAY NOT MUTATE WHAT IT JUDGES ---------- #
        # The pass above traded a deep copy per cell for a fresh root and a fresh node. That
        # trade is only sound if the stage leaves the candidate alone, and
        # `refuse_unless_publishable`'s own docstring says it does — *"``candidate`` is never
        # mutated, never copied-and-repaired, and never partially accepted."* **A SENTENCE IS
        # NOT AN ENFORCEMENT POINT**, so it is MEASURED here rather than believed.
        check.asserted()
        if base_document != untouched_snapshot:
            differing = _differing_pointers(base_document, untouched_snapshot)
            check.violation(
                here, 0, "CD-STALE-INVARIANT-013",
                f"{surface.value}: the fourth refusal stage MUTATED the document it was given "
                f"— the base document differs from its pre-pass snapshot at {differing!r}. "
                "The publication gate's own contract says the candidate is never mutated, and "
                "a judging step that edits what it judges means the document that was JUDGED "
                "and the document that would be WRITTEN are not the same document. It also "
                "invalidates this pass's fresh-root/fresh-node composition, so every "
                "invariance cell above must be re-read as unsound.",
            )
        else:
            check.note(
                f"{surface.value}: the stage did not mutate the document it judged, measured "
                "against a snapshot taken before the invariance pass (CD-STALE-INVARIANT-013)."
            )

    # -- CD-STALE-INVARIANT-012 — THE PASS ITSELF MAY NOT GO VACUOUS -------------------- #
    # An invariance check that drove NO varied point is perfectly invariant and detects
    # nothing. So is one whose vocabulary has been narrowed until no property has an
    # alternative value. This assertion is about THIS PASS'S OWN COVERAGE.
    check.asserted()
    if invariance_points < MINIMUM_INVARIANCE_POINTS or invariance_cells == 0:
        check.violation(
            here, 0, "CD-STALE-INVARIANT-012",
            f"the invariance pass drove {invariance_points} varied point(s) and "
            f"{invariance_cells} cell(s), and this row requires at least "
            f"{MINIMUM_INVARIANCE_POINTS} points. *** AN INVARIANCE CHECK THAT VARIES NOTHING "
            "IS PERFECTLY INVARIANT AND DETECTS NOTHING. *** Either the value vocabulary has "
            "been narrowed until no property has an alternative admissible value — which is "
            "how `A313-F1` happened in the first place, one value per property — or the "
            "contract has stopped admitting more than one document. Both are failures of this "
            "row and neither may report clean.",
        )
    for line in coverage_lines:
        check.note(f"COVERAGE {line}")
    check.note(
        f"INVARIANCE PASS: {invariance_points} varied points, {invariance_cells} cells driven, "
        f"{invariance_skipped} variant(s) not driven because the WHOLE document was not "
        "contract-admissible in combination (counted, never silently dropped)."
    )
    for rule, count in sorted(reported.items()):
        if count > VIOLATION_REPORT_CAP:
            check.note(
                f"{rule}: {count} violations found, {VIOLATION_REPORT_CAP} printed in full "
                f"and {count - VIOLATION_REPORT_CAP} counted only (report cap)."
            )

    check.note(
        "DECLARED LIMIT, PRINTED AT EVERY RUN: this check drives the STALE half of CD-AC-001 "
        "only. It says nothing about MISSING data — that is the sibling row "
        "CD-RT-001-MISSING-DATA-NEVER-CALM and its RULE CC — nothing about a fabricated VALUE "
        "reading that should have been an absence, and it does not prevent $CD_CONTRACTS_DIR "
        "being pointed at a widened copy of the contracts: it refuses to run when it is. It is "
        "ONE OF FOUR guards on CD-AC-001 and never a sole guard."
    )
    check.note(
        "AND THE DECLARED SCOPE, PRINTED AT EVERY RUN (PO-DECISIONS-0030 ruling 2): the gate "
        "enforces DOCUMENT-INTERNAL freshness — published_utc minus a calm-bearing node's "
        "oldest stamp, against the window the same document declares. IT CANNOT CATCH A SOURCE "
        "THAT CONSISTENTLY LIES ABOUT ITS OWN STAMP: a feed that stamps every reading with the "
        "current instant regardless of the true age of the data is internally consistent and "
        "PASSES. THAT IS NOT RECORDED AS UNENFORCEABLE. It is the same class as the A311-F1 "
        "forgery and it has the same answer in the three-tier perimeter (PO-DECISIONS-0018/"
        "0019, BLUEPRINT §17 CD-BP-005): the gate is PREVENTION of what is document-internal; "
        "a lying source is caught by DETECTION — witness divergence + provenance, CD-AC-018 — "
        "ENFORCED ONE TIER OUT AND OWED AT WO-3, when real sources and their witnesses land. "
        "16C's detector-side liveness marking carries the resulting HONESTY OBLIGATION: stamps "
        "are PROVENANCE-BACKED and WITNESS-CORROBORATABLE. 16C IS NOT BUILT HERE."
    )

    return check.done(
        f"{cells} gate cells driven in-process through refuse_unless_publishable against "
        f"{package_dir} ({len(list(EnvelopeSurface))} surfaces x canonical dial slots x "
        f"{len(gate_table)} stamp rows), plus the fourth refusal stage driven directly at "
        "three calm-bearing positions the closed contract makes unreachable through the front "
        "door, the oldest-governs arms, the fail-closed arms and the declared-scope arm"
    )


if __name__ == "__main__":
    raise SystemExit(main())
