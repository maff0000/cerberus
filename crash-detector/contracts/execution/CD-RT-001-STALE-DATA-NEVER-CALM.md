# Execution contract — CD-RT-001-STALE-DATA-NEVER-CALM

**CD-AC-001** · Missing or stale input never renders as calm · obligation **MANDATORY** ·
scope **CLASS** · delivered in **WO-3 increment 16E**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

**PID §3.2, constitutional, in its own words: *"Missing **or stale** data must never render as
calm."*** The LIVE PUBLICATION GATE — `refuse_unless_publishable`, the function
`src/crash_detector/publication/publish.py` calls on both surfaces before it writes anything —
REFUSES an envelope in which a node rendering `detail_level: "calm"` is older than the
`staleness_window_seconds` **the same document declares**, measured from the `published_utc`
**the same document declares**; and **still ADMITS** a genuinely fresh calm reading, a reading
aged exactly the declared window, and a stale reading rendering at its true level.

## Why this row exists at all — `PO-DECISIONS-0030` ruling 1

> "Q35(a) — YES, the fourth refusal stage gets its OWN Required Test Register row, and it lands
> BEFORE 16C. This is ruling 9's principle (a constitutional guarantee is carried by a
> REGISTER-WIRED instrument, never test-only) applied to the freshness stage: the guarantee is
> proven today, but proven in tests is not proven in the register. Register-wire it — its own
> row, a negative control the gate reads, failing if stale-carrying-calm is ever admitted — and
> land it before 16C so the control is registered before the lane moves on."

**MEASURED THREE TIMES INDEPENDENTLY** — by `CD-ASR-WO3-12` (`A312-F1`), by
`PROJECT_LEAD_SEAT_06` in its own shell, and by `CD-ENG-WO3-13` before a line of the instrument
was written. On a tree with the entire fourth refusal stage removed
(`plants/WO3-INC16D/D1-THE-FOURTH-STAGE-REMOVED.patch`, `git apply` rc=0 TAKEN AND CHECKED),
**all thirty of the register's `execute:` lines produced a per-line rc list `diff`-IDENTICAL to
the clean tip — `TOTAL lines=30 rc0=19 nonzero=11` on both** — while the live gate ADMITTED a
dial stamped `1970-01-01` carrying `calm` on BOTH surfaces. The only witness that moved was
`tests/test_envelope_freshness.py`, a file **no `execute:` line named**, against **41 distinct
`tests/test_*.py` paths the register DOES name.**

`required-tests.yaml` line ~242 already carries a memorial about `tests/test_detail_level.py`
occupying this exact position: *"A memorial nobody reads... it does not make the guarantee live,
because a pytest file is still a file the gate happens to name."* **THE MEMORIAL MUST NOT BE
REMOVED — it is the record of the defect class this row closes.**

## Command

```
python3 tools/register/check_stale_data_never_calm.py --root .
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

**THE RUNNING GATE, not the source text of the stage.** The check imports `crash_detector` from
`<root>/src`, drives `refuse_unless_publishable` with candidate envelopes, and records what the
gate actually did. It does not read the stage's source, does not grep for `REFUSAL_STALE_CALM`,
and does not assert that any function is called from anywhere. A structural read of schema keys
is what let this class of defect through three times on this project (`CD-PL-F169`,
`CD-ASR-WO3-02` F06/F07, `CD-ASR-WO3-03`).

## The two limbs, and why there are two

**LIMB A — THE FRONT DOOR.** `refuse_unless_publishable`, on every surface `EnvelopeSurface`
declares, at every CANONICAL DIAL SLOT the contract declares (a root property spelled literally
`{"$ref": "#/$defs/dial_reading"}`). Six stamp rows per slot per surface, three refusing and
three admitting, plus an all-fresh baseline that must be ADMITTED before any refusal below it
is attributable to the stamp under test.

**LIMB B — THE STAGE ITSELF, DRIVEN DIRECTLY.** On the shipped contracts the ONLY node that can
carry `detail_level: "calm"` is a canonical dial slot in its `VALUE` branch — MEASURED:
`#/$defs/contribution` is closed and declares no `detail_level`, `degraded_inputs` is
`#/$defs/source_id_list` (an array of plain strings), and the root declares
`additionalProperties: false`. A document that puts a calm node anywhere ELSE is refused at
STAGE 3 as `SCHEMA_VIOLATION` and never reaches stage 4. **An instrument that only used the
front door therefore could not tell the NODE WALK apart from an implementation that reads the
two dial slots BY NAME** — which is exactly what
`plants/WO3-INC16D/D3-SLOT-READING-INSTEAD-OF-NODE-WALK.patch` plants, and exactly the
recogniser-over-an-open-set defect class that lost eleven consecutive audit rounds on this row.
Limb B drives `_refuse_stale_calm` directly, as `tests/test_envelope_freshness.py` already does
and for the reason that file already states. **This is `DECLARED LIMIT 3` and it cuts both
ways.**

## Why it is asserted this way — the admitting rows carry equal weight

*** THE VACUITY DIRECTION IS EQUALLY A VIOLATION OF THIS ROW, AND IT IS THE HALF THIS PROJECT'S
HISTORY SAYS GETS MISSED. *** A freshness stage that refused EVERYTHING would satisfy PID §3.2
vacuously by making the dial incapable of ever reading `calm`, and `calm` on a fresh reading
backed by real inputs is the entire reason `calm` exists (PID §4). Every refusing row is
therefore PAIRED with an admitting one, in the same run, on the same tree, from the same
builder, and `CD-STALE-VACUITY-000` asserts that this instrument's OWN table still contains the
fresh-calm row, the closed-interval boundary row and the stale-but-not-calm row, so the
admitting arms cannot be quietly deleted from the instrument that exists to carry them.

## Assertion codes

| code | what it asserts |
|---|---|
| `CD-STALE-VACUITY-000` | this instrument's own proposition table still declares its MUST-ADMIT rows |
| `CD-STALE-GATE-001` | what the LIVE GATE did with each candidate, refusing AND admitting |
| `CD-STALE-REASON-002` | the refusal is `STALE_CALM` **at the calm node's own pointer** — the right outcome from the RIGHT layer (`CD-PL-F74`) |
| `CD-STALE-PAIRED-003` | the refused candidate and its ADMITTED pair differ at **exactly the stamp of the slot under test** |
| `CD-STALE-NODES-004` | the stage quantifies over NODES, not over dial slots: three calm-bearing positions a slot-reader cannot see, each paired with a FRESH arm |
| `CD-STALE-OLDEST-005` | **the OLDEST stamp governs**, and the refusal names it — paired with an all-fresh arm |
| `CD-STALE-CLOSED-006` | fail closed at every branch: no stamp, an unparsable `*_utc`, no usable `published_utc`, no usable window — paired with a usable arm |
| `CD-STALE-BUILD-008` | a candidate this check could not build, or a `$ref` chain carrying an asserting sibling — **DENY BY DEFAULT**, reported and never skipped |
| `CD-STALE-SCOPE-009` | the DECLARED SCOPE below, **DRIVEN** rather than asserted: a uniformly time-shifted envelope is ADMITTED, and the day that stops being true this limit is FALSE and must be rewritten |

## Preconditions

* `<root>/src/crash_detector/__init__.py` must exist. Otherwise exit `3`: *"REFUSED" is a
  RUNTIME claim and this check will not make it against a tree it could not load.*
* `jsonschema` must import, because the gate validates with it (`DECLARED LIMIT 7`).
* `crash_detector.publication.envelope_contract._refuse_stale_calm` must import
  (`DECLARED LIMIT 3`). If it does not, exit `3` — **never a fallback to limb A alone.**
* The gate must resolve its contracts to `<root>/contracts` (`DECLARED LIMIT 1`). Otherwise
  exit `3`: this check will not report on a tree it is not looking at.
* Each contract must declare at least one canonical dial slot, a `oneOf` branch whose
  `detail_level` admits `calm`, and at least one stamp-shaped property on that branch.
  Otherwise exit `3`.

**NO PRECONDITION IS EVER A SKIP.** A precondition that cannot be met is a NON-ZERO exit with a
stated reason (`PBG-CI-002`, Standards Baseline §16).

## Exit semantics

| exit | meaning |
|---|---|
| `0` | assertions were made and all of them held: the gate refuses a document-internally stale calm node on both surfaces, and still admits everything the product must be able to publish. |
| `1` | VIOLATION. Each finding names its assertion code and says what the gate actually did. |
| `2` | USAGE — the command line was wrong. |
| `3` | PRECONDITION NOT MET, with the reason. **Never a pass and never a skip.** |

A run that made ZERO assertions also exits `3`: `exit 0` may not mean "clean" and "I looked at
nothing" indistinguishably.

## *** THE DECLARED SCOPE OF THIS GUARD — `PO-DECISIONS-0030` ruling 2 ***

**THE GATE ENFORCES DOCUMENT-INTERNAL FRESHNESS AND NOTHING WIDER.** What it computes is
`published_utc` MINUS the calm-bearing node's oldest stamp, against the window THE SAME DOCUMENT
declares. That is a claim about the document's INTERNAL COHERENCE — *a dial cannot be older than
its declared window relative to its own declared publication instant* — and it is **not** a claim
about ACTUAL freshness.

**IT CANNOT CATCH A SOURCE THAT CONSISTENTLY LIES ABOUT ITS OWN STAMP.** A feed that stamps
every reading with the current instant regardless of the true age of the data underneath it is
internally consistent and PASSES THIS GATE. So is a uniformly time-shifted envelope: MEASURED by
`CD-ASR-WO3-12` (`A312-F3`) at `0e80a09` with an ordinary 600-second window, `as_of_utc` =
`published_utc` = `1970-01-01T00:00:00Z` is **ADMITTED on both surfaces**. A replayed envelope, a
stopped publisher, a stuck detector clock and a backfill run all produce exactly that document.
**Nothing in a document can prove that about itself.** `CD-STALE-SCOPE-009` DRIVES that document
at every run and REQUIRES it to be admitted, so this paragraph cannot go stale in the reassuring
direction while the code changes underneath it.

*** THAT IS NOT RECORDED AS "OUTSIDE ENFORCEMENT" AND IT IS NOT "PERMANENTLY UNENFORCEABLE".
THE PRODUCT AUTHORITY RULED THE OPPOSITE. *** Source honesty is the SAME CLASS as the `A311-F1`
forgery and it has the SAME answer, already ruled in the THREE-TIER PERIMETER
(`PO-DECISIONS-0018`/`0019`, `BLUEPRINT §17` `CD-BP-005`):

* **PREVENTION** — what is DOCUMENT-INTERNAL is prevented AT THE GATE. That is this stage, and
  that is what this row guards.
* **DETECTION** — a source that lies about its own freshness is caught **ONE TIER OUT**, by
  **WITNESS DIVERGENCE + PROVENANCE, `CD-AC-018`**, where a source's CLAIMED freshness is
  corroborated against independent witnesses and **DIVERGENCE IS THE ALARM**.
* **WHEN IT IS OWED: AT WO-3**, when real sources and their witnesses land. It is not deferred
  indefinitely and it is not written off.

**THE HONESTY OBLIGATION THIS CREATES FOR 16C, RECORDED HERE AND DELIBERATELY NOT BUILT HERE.**
16C's detector-side liveness marking carries the obligation that the stamps it produces are
**PROVENANCE-BACKED AND WITNESS-CORROBORATABLE**. **16C IS NOT IN THIS INCREMENT:** no
`feed_liveness` slot, no dead-feed detector, no liveness marking. This row records the
obligation and builds none of it.

**A DECLARED LIMIT THAT SAYS "WE CANNOT DO THIS" WHERE THE TRUTH IS "THIS IS DONE AT THE NEXT
TIER, AT WO-3" IS A FALSE RESIDUAL**, and four sentences on the sibling row
`CD-RT-001-MISSING-DATA-NEVER-CALM` have already been superseded for being false in exactly that
reassuring direction.

## Declared limits — this row's own sequence, 1 to 11

**DECLARED LIMIT NUMBERS ARE PER REGISTER ROW, NOT PER FILE.** These eleven are
`CD-RT-001-STALE-DATA-NEVER-CALM`'s and they are said identically here, in the header of
`tools/register/check_stale_data_never_calm.py` and in `required-tests.yaml` (`CD-RULE-004`,
three places). The sibling row `CD-RT-001-MISSING-DATA-NEVER-CALM` has its own independent 1–20
sequence and `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` its own 1–12. **Three rows now carry a
`DECLARED LIMIT 3`; quote the row id with the number.**

1. **IT JUDGES THE CONTRACT THE GATE ACTUALLY LOADS, WHICH IS CONFIGURABLE.**
   `envelope_contract.contracts_dir()` honours `$CD_CONTRACTS_DIR`, so the live gate can be
   pointed at a widened copy while this repository's contracts are byte-intact. **WHAT THIS
   CHECK DOES ABOUT IT:** it exits `3` unless the contracts the gate resolves are
   `<root>/contracts`, and prints their SHA-256 at every run (`CD-PL-F98`). **IT DOES NOT
   PREVENT THE ROUTE. NOT PROVED TO BE CARRIED ANYWHERE.** EXECUTABLE:
   `CD_CONTRACTS_DIR=/tmp/anything python3 tools/register/check_stale_data_never_calm.py --root .`
   -> `PRECONDITION_NOT_MET`, exit 3.

2. **THE SKELETON IS DERIVED FROM THE CONTRACT BUT THE VALUE VOCABULARY IS A CLOSED WRITTEN
   LIST.** The root is built from the contract's own `required` list and the dial from the
   calm-bearing branch's own `required` + `properties`; each property is filled with the FIRST
   of `SYNTHETIC_VALUES` that the property's OWN subschema accepts, decided by `jsonschema` —
   the same library the gate validates with — and NEVER by the property's NAME. A required
   property none of them satisfies makes this check REPORT (`CD-STALE-BUILD-008`) and exit 1.

   *** ITS CLOSING SENTENCE WAS FALSE IN THE REASSURING DIRECTION. SUPERSEDED AT `16F` ON
   `A313-F1`, STATED AND NOT ERASED (`CD-RULE-004`, `PBG-CONT-003`). ***

   > **WHAT IT SAID, VERBATIM, IN ALL THREE PLACES IT WAS SAID:** *"DENY BY DEFAULT, so it is
   > not an escape; it IS a maintenance cost."*

   **THAT SENTENCE IS ABOUT THE WRONG HALF OF THE PROBLEM.** Deny-by-default governs what
   happens when a property CANNOT be built: the check reports `CD-STALE-BUILD-008` and exits 1.
   **IT SAYS NOTHING WHATEVER ABOUT THE PROPERTIES THAT CAN BE BUILT AND ARE THEN DRIVEN AT
   EXACTLY ONE VALUE EACH, AND THAT IS WHERE THE ESCAPE WAS.** All 72 documents this instrument
   drove at `a9e19c3` carried THE SAME SINGLE VALUE FOR EVERY ROOT PROPERTY — ONE POINT in the
   space of documents the contract admits, while the guarantee quantifies over ALL of them.
   MEASURED by `CD-ASR-WO3-13` (`A313-F1`, HIGH), reproduced by `PROJECT_LEAD_SEAT_07`, and
   reproduced a THIRD time by `CD-ENG-WO3-14` before a line of `16F` was written: `W5G` (five
   lines, `if len(candidate.get("inputs_used") or []) > 1: return`) and `W5B2` (three lines,
   `if candidate.get("regime") == CALM_DETAIL_LEVEL: return`) each leave the live gate ADMITTING
   a 1970-stamped calm dial on BOTH surfaces while all 32 of this register's `execute:` lines
   are `diff`-identical to the clean tip.

   **WHAT IS TRUE INSTEAD, AT `16F`.** The vocabulary is still a written list and that half of
   the limit stands. What has changed is that the instrument no longer drives ONE value per
   property: the INVARIANCE PASS varies every root property, and every non-stamp property of the
   calm-bearing node, across that vocabulary, and requires the verdict not to move. The residual
   is `DECLARED LIMIT 9` — a SAMPLE of an unbounded set — and it is stated there rather than
   here. EXECUTABLE: add a required root property typed `{"type": "string", "pattern": "^ZZZ"}`
   to either contract and this instrument goes RED.

3. **LIMB B DRIVES `_refuse_stale_calm` DIRECTLY AND THEREFORE PROVES NOTHING ABOUT WHETHER THE
   GATE CALLS IT.** That is LIMB A's job and only LIMB A's. The two limbs are separately
   defeatable and **MEASURED TO BE**: arm `D1` (the whole stage unreachable from the gate) costs
   LIMB A twelve violations and costs LIMB B **nothing**; arm `D3` (the slot-reading
   implementation) costs LIMB B twelve and costs LIMB A **nothing**. **A REPORT OF THIS ROW THAT
   QUOTES ONE LIMB IS HALF A REPORT.** And limb B is NAME-COUPLED to a private symbol,
   `_refuse_stale_calm`: renaming it makes this instrument exit `3`, deliberately, because a
   check that cannot reach its authentic target must fail and never wave through (`PBG-CI-002`).
   That coupling is the same trade the sibling row's `DECLARED LIMIT 12` prices and it is
   ACCEPTED for the same reason: a false positive costs one seat one look; a false negative
   costs the constitution. EXECUTABLE: rename `_refuse_stale_calm` in
   `src/crash_detector/publication/envelope_contract.py` and run the command — exit `3` with the
   reason, never `0`.

4. **IT PROVES NOTHING ABOUT A `VALUE` READING THAT SHOULD NOT HAVE BEEN A `VALUE`, AND NOTHING
   ABOUT THE MISSING HALF.** A dial whose inputs were missing but which was constructed as
   `VALUE` with a fabricated score and a fresh stamp renders calm legitimately as far as THIS
   row is concerned, and this check ADMITS IT — the vacuity rows say so out loud, and they must,
   or the check would be the vacuous kind. **THE CARRIERS ARE THE THREE SIBLING ENTRIES ON
   `CD-AC-001`:** `CD-RT-001-AST-NO-NUMERIC-DEFAULT` (the provenance of the magnitude),
   `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` (the runtime post-condition) and
   `CD-RT-001-MISSING-DATA-NEVER-CALM` (the MISSING half at the gate, including `RULE CC`).
   **THIS IS ONE OF FOUR GUARDS ON `CD-AC-001` AND NEVER A SOLE GUARD.** MEASURED: arms
   `H1`–`H4`, which widen a non-dial root property to admit a calm-bearing object, leave this
   row at `PASS — 97` and are caught by the sibling row at `FAIL — 2`.

5. **IT DOES NOT RE-DERIVE THE ROOT PARTITION.** It drives the CANONICAL DIAL SLOTS — root
   properties spelled literally `{"$ref": "#/$defs/dial_reading"}` — and if a contract declares
   none it exits `3` rather than reporting clean. Whether some OTHER root property could carry a
   dial at all is `RULE CC`'s question and it is asserted on the SIBLING row
   (`CD-CALM-ROOT-008`), not here. **A root property this row does not drive is not a property
   this row says anything about.**

6. **IT IS A CLAIM ABOUT DOCUMENTS THE GATE SEES.** A rendering path that never calls
   `refuse_unless_publishable` is outside this check entirely. MEASURED at this commit: the only
   callers in `src/` are `publication/publish.py` lines 276-277, on both surfaces, before any
   write. **A FUTURE SERVING LAYER THAT RENDERS A DIAL WITHOUT PUBLISHING AN ENVELOPE IS NOT
   PROVED TO BE CARRIED ANYWHERE.**

7. **IT NEEDS `jsonschema`, BECAUSE THE GATE DOES.** If `jsonschema` is absent it exits `3` with
   the reason — never a pass and never a skip (`PBG-CI-002`).

8. **THE DECLARED SCOPE ABOVE IS THIS ROW'S LARGEST LIMIT.** It is stated in full rather than
   cross-referenced, and `CD-STALE-SCOPE-009` drives it at every run. Closing that class needs a
   comparand from OUTSIDE the document, which is the DETECTION tier — `CD-AC-018`, witness
   divergence + provenance — **OWED AT WO-3**. It is enforced one tier out and it is **not**
   unenforceable.

9. **THE INVARIANCE PASS VARIES ONE PROPERTY AT A TIME, AND ITS VALUE VOCABULARY IS A SAMPLE OF
   AN UNBOUNDED SET. NEW AT `16F`.** From a proved-publishable baseline it varies ONE root
   property, or ONE non-stamp property of the calm-bearing node, to ONE other value that
   property's own subschema admits, and requires the verdict FOUR-TUPLE — admitted or refused,
   reason class, pointer, key — to be unchanged. **THAT IS LINEAR RATHER THAN THE EXPONENTIAL
   CROSS-PRODUCT, AND IT CATCHES EVERY PREDICATE KEYED ON A SINGLE PROPERTY**, which is every
   weakening shape measured on this project. Where a subschema admits an UNBOUNDED set — every
   string of 1 to 128 characters, every number — **THE VOCABULARY IS A SAMPLE AND NOT A COVER.**
   What is sampled, and why each family is there: the product's own words (every `const` and
   every `enum` string HARVESTED FROM THE CONTRACT ITSELF, never typed in, which is the family
   `W5B2` keys on); array CARDINALITY at 0, 1, 2 and many (the family `W5G` keys on); every JSON
   type the subschema admits; numbers at zero, negative, small, large and integral; both
   booleans; null; and presence against absence. **A PREDICATE KEYED ON A STRING VALUE OUTSIDE
   THAT SAMPLE ESCAPES THIS PASS. MEASURED BY THIS SEAT AGAINST ITS OWN INSTRUMENT, AFTER
   FREEZING IT:** arm `N1` (`if candidate.get("config_snapshot_id") == "BYPASS": return`) leaves
   this row at `PASS` and admits a 1970-stamped calm dial on both surfaces. It is caught by the
   sibling STRUCTURAL row `CD-RT-001-PUBLICATION-CHOKEPOINT` (`CD-CHOKE-005`). EXECUTABLE: apply
   `plants/WO3-INC16F/N1-CONFIG-SNAPSHOT-ID-BYPASS.patch` and run both rows.

   *** ITS CLOSING SENTENCE WAS FALSE IN THE REASSURING DIRECTION. SUPERSEDED AT `16G` ON
   `CD-ASR-F14-02`, STATED AND NOT ERASED (`CD-RULE-004`, `PBG-CONT-003`). ***

   > **WHAT IT SAID, VERBATIM, IN ALL THREE PLACES IT WAS SAID:** *"It is caught by the sibling
   > STRUCTURAL row `CD-RT-001-PUBLICATION-CHOKEPOINT` (`CD-CHOKE-005`), **AND THE TWO ROWS ARE
   > A PAIR FOR EXACTLY THIS REASON.**"*
   >
   > And the sentence it rested on, said in the `16F` return (`BL-20260824T223344Z-16FC`,
   > `CD-ENG-F16F-02`): *"The class is closed by the STRUCTURAL row, which catches every
   > `return`/`continue`/`break`-shaped bypass regardless of what value it is keyed on."*

   **THE FIRST HALF IS TRUE OF `N1`; THE SECOND HALF IS A CLAIM ABOUT A CLASS, AND THE CLASS
   CLAIM IS FALSE.** `N1` is caught because `N1`'s `return` is LEXICALLY INSIDE
   `_refuse_stale_calm`. **ARM `Z7` IS ALSO A `return` ON THE PUBLICATION PATH AND IT IS NOT
   CAUGHT** — it sits at the top of `_iter_nodes`, the SHARED DOCUMENT WALK the stage DEPENDS
   ON, and `CD-CHOKE-005` walks `_refuse_stale_calm` and nothing the stage calls. Raised as
   `CD-ASR-F14-02` by `CD-ASR-WO3-14`; **REPRODUCED IN THIS SEAT'S OWN SHELL AT `c475b8e`
   BEFORE THIS PARAGRAPH WAS WRITTEN** (`CD-PL-F193`): `STALE-CALM ADMISSIONS = 2` on both
   surfaces with `MUST-ADMIT ROWS REFUSED = 0`, while BOTH rows returned `PASS` — this row
   `PASS — 142088 assertions, 0 violations`, the structural row `PASS — 11 assertions, 0
   violations`. EXECUTABLE:
   `plants/WO3-INC16G/Z7-THE-SHARED-WALK-DECLINES-TO-YIELD-ONE-NODE.patch`.

   **WHAT IS TRUE INSTEAD, STATED OVER THE CLASS AND NOT OVER ONE FUNCTION.** `CD-CHOKE-005`
   catches a `return`, `continue` or `break` **LEXICALLY INSIDE `_refuse_stale_calm`**, and
   catches the stage's first executable statement ceasing to enumerate through the shared walk.
   **THAT IS A CLAIM ABOUT ONE FUNCTION'S BODY, NOT ABOUT THE PUBLICATION PATH.** Neither row
   reads the functions the stage DEPENDS ON, and the shared walk is one of them. **SO THE TWO
   ROWS ARE NOT A COVER OF THE `return`-SHAPED CLASS, AND THIS LIMIT NO LONGER SAYS THEY ARE.**
   What can be stated truthfully is that boundary and no more; **A LIMIT THAT ADMITS IT DOES
   NOT KNOW IS WORTH MORE THAN ONE THAT REASSURES**, and it was the reassurance that let a
   residual read as a closure.

   **THE SENTENCE BESIDE IT IS TRUE AND SURVIVES UNCHANGED:** *"NEITHER ROW CLOSES IT ALONE AND
   THE RETURN DOES NOT CLAIM OTHERWISE."* The disclosure was honest; the closing reassurance
   was wrong. **THE RESIDUAL CLASS IS NOT REOPENED HERE:** `PO-DECISIONS-0032` ruling 3 records
   the insider-source-weakening full guarantee (`CD-ASR-F14-01`) as OWED LATER-HARDENING — a
   code-structure invariant, a heavier mechanism than a document instrument — assigned to the
   assurance/detection tier and NOT a product blocker. **`16G` CORRECTS THE RECORD; IT DOES NOT
   CLOSE THE CLASS AND DOES NOT PRETEND TO.**

10. **THE PAIRWISE PASS RUNS ON LIMB B ONLY, AND THREE-WAY CONJUNCTIONS ARE NOT COVERED. NEW AT
    `16F`.** One-at-a-time variation cannot see a CONJUNCTIVE predicate over two properties —
    `if regime == "acute" and len(inputs_used) == 2: return` — because neither half alone
    changes the verdict. So every unordered PAIR of `(property, value)` points drawn from two
    DIFFERENT properties is driven, over a per-property value set reduced BY FEATURE FAMILY
    (every product-vocabulary value and every array-cardinality value kept whole, one
    representative of each other family). **IT RUNS ON LIMB B ONLY** — the stage driven directly
    — because a LIMB A pairwise pass is about 230x more expensive per cell: MEASURED on this
    host, the front door costs `16.05 ms` per call because it reloads and recompiles the
    contract every time, and the stage costs `0.069 ms`. **A CONJUNCTIVE WEAKENING PLACED
    OUTSIDE THE STAGE — IN `refuse_unless_publishable` ITSELF — IS THEREFORE NOT COVERED BY THE
    PAIRWISE PASS**; it is covered by `CD-CHOKE-004` on the sibling structural row. **AND A
    THREE-WAY CONJUNCTION IS NOT COVERED BY EITHER ROW.** MEASURED at this tip: 30,575 pairs on
    the public contract and 39,142 on the private one, **stride 1 — the FULL product and not a
    sample.** Above `PAIRWISE_CELL_BUDGET` the pass takes a deterministic evenly-strided
    SUBSAMPLE and prints the stride at every run; **at the shipped contracts that branch is NOT
    REACHED and is therefore UNEXERCISED CODE IN NORMAL OPERATION**, which is stated here rather
    than left to be discovered. EXECUTABLE: arm
    `plants/WO3-INC16F/N6-CONJUNCTION-REGIME-AND-CARDINALITY.patch`.

11. **THE PASS COSTS THIRTY TIMES WHAT THIS ROW COST BEFORE IT, AND THAT IS THE PRICE OF THE
    SPACE. NEW AT `16F`. THE `a9e19c3` ASSERTION COUNT IS CORRECTED AT `16G`.** MEASURED on the
    same host with the same command: `0.79 s` at `a9e19c3` for **97** assertions, `26.5 s` at
    this tip for 142,088. Almost all of it is LIMB A, because every front-door cell reloads and
    recompiles the contract. **THE COST IS PAID DELIBERATELY AND IT IS NOT AN ACCIDENT OF A
    LOOP NOBODY BOUNDED.** EXECUTABLE:
    `time python3 tools/register/check_stale_data_never_calm.py --root .`

    *** THE BASELINE FIGURE DID NOT REPRODUCE. SUPERSEDED AT `16G` ON `CD-ASR-F14-05`, STATED
    AND NOT ERASED (`CD-RULE-004`, `PBG-CONT-003`). ***

    > **WHAT IT SAID, VERBATIM, IN ALL THREE PLACES IT WAS SAID:** *"MEASURED on the same host
    > with the same command: `0.77 s` at `a9e19c3` for 122 assertions, `26.1 s` at this tip for
    > 142,088."*

    **`122` IS NOT WHAT THIS ROW ASSERTED AT `a9e19c3`. `97` IS.** `CD-ASR-WO3-13` and
    `CD-ASR-WO3-14` each measured `97`; **THIS SEAT DID NOT COPY THAT FIGURE, IT RAN IT**
    (`CD-PL-F193` — an inherited claim is a hypothesis until run), in a throwaway worktree so
    the lane was not disturbed, three consecutive times, and got `97` every time:

    ```
    git worktree add /tmp/inc16g/base a9e19c3
    cd /tmp/inc16g/base && python3 tools/register/check_stale_data_never_calm.py \
        --root /tmp/inc16g/base
    -> CD-RT-001-STALE-DATA-NEVER-CALM: PASS — 97 assertions, 0 violations   rc=0
       (x3, deterministic; `real 0m0.789s`)
    ```

    **THREE SEATS NOW AGREE ON `97` AND NOTHING MEASURES `122`.** The TIP figure `142,088`
    reproduces exactly and is untouched (`rc=0`, `real 0m26.486s`), so the correction is to the
    baseline half of the comparison and to nothing else; the timings are re-stated as this host
    measured them rather than carried across. **THE THIRTYFOLD CLAIM IN THE HEADLINE SURVIVES
    AND GETS LARGER, NOT SMALLER** — `142088 / 97` is about 1465x the assertion count at about
    34x the wall clock. `122` is not recoverable from any run this seat could construct, and
    where a figure cannot be reproduced it is replaced by one that can be, with the command
    that produced it beside it.

## For the auditor

*** THE PARAGRAPH THAT STOOD HERE ASSERTED UNIVERSALITY OVER POSITIONS AND WAS SILENT ON
DOCUMENTS. SUPERSEDED AT `16F` ON `A313-F1`, STATED AND NOT ERASED (`CD-RULE-004`,
`PBG-CONT-003`). ***

> **WHAT IT SAID, VERBATIM, IN ALL THREE PLACES IT WAS SAID:** *"Do not read a clean run of this
> check as proof that no stale reading can ever render as calm. It proves that the LIVE
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
ROW `CD-RT-001-PUBLICATION-CHOKEPOINT`, and **A REPORT THAT QUOTES ONE OF THE TWO ROWS IS HALF A
REPORT.** **The arm to weigh it against is the vacuity set**: an instrument that refused
everything would be enforcing silence rather than holding PID §3.2, **and an invariance check
that refuses everything everywhere is PERFECTLY INVARIANT**, which is why every varied point
carries the MUST-ADMIT rows too. **The arms to weigh it with are
`plants/WO3-INC16E/MANIFEST.md`'s `D1`-`D4` and `plants/WO3-INC16F/MANIFEST.md`'s `W5` and `N`
and `C` series**, each a measured tree with its `git apply` rc, its own rc and its violation
count.

## Negative control

**A node rendering `detail_level: "calm"` whose oldest readable stamp is further from the
document's declared `published_utc` than the document's declared `staleness_window_seconds`,
ADMITTED by `refuse_unless_publishable` on either surface, by ANY route.** The class includes,
and is not limited to — **AND EVERY NAMED MEMBER BELOW IS A MEASURED ARM WITH ITS rc AND ITS
VIOLATION COUNT, NOT A CLAIM:**

| member | arm | measured |
|---|---|---|
| the fourth refusal stage removed from `refuse_unless_publishable` | `D1` | `FAIL — 12 violation(s)`, exit `1`, all `CD-STALE-GATE-001` |
| the naive `age > window` — the negative-age branch removed, so a FUTURE stamp is admitted | `D2` | `FAIL — 4 violation(s)`, exit `1`, all `CD-STALE-GATE-001` |
| the stage reading the dial slots BY NAME instead of walking nodes | `D3` | `FAIL — 12 violation(s)`, exit `1` — 6x `CD-STALE-NODES-004`, 4x `CD-STALE-CLOSED-006`, 2x `CD-STALE-OLDEST-005` |
| the NEWEST stamp governing instead of the oldest | `D4` | `FAIL — 2 violation(s)`, exit `1`, both `CD-STALE-OLDEST-005` |

Each arm is run from **its own pristine `git archive <sha> \| tar -x` extraction**, with the
patch read from an ABSOLUTE path outside every extraction and `git apply`'s rc **taken and
checked** — `CD-ASR-WO3-11` disclosed against itself that its runner read patches from inside
the extraction, got rc=128, and then measured an UNPATCHED tree while looking like a result.
See `plants/WO3-INC16E/MANIFEST.md`.

**A member of this class that is not a measured arm is a claim, and this row does not make
one.** The sentence *"the instrument fails on all of these"* stood on the sibling row and was
FALSE; it is superseded there and readable beside its correction, and it is not repeated here.

*** AND THE VACUOUS DIRECTION IS EQUALLY A VIOLATION OF THIS ROW, WHICH IS THE HALF THIS
PROJECT'S HISTORY SAYS GETS MISSED: *** a genuinely fresh calm dial that stops being ADMITTED; a
reading aged EXACTLY the declared window that stops being ADMITTED (the predicate is a CLOSED
interval); a stale `elevated` or `acute` reading that stops being ADMITTED (the stage guards
`calm` and only `calm` — the criterion's own scope); a calm node whose stamps are all fresh that
starts being refused. **A tree on which nothing can be published is not a tree on which PID §3.2
holds, and this row does not report it as one.** MEASURED at the clean tip: fresh-calm ADMITTED
on both surfaces, `1970` + `elevated` ADMITTED on both surfaces.

Detection is a **contrast**, and the validator computes it as one: the same declared command
must exit `0` on the clean subject and non-zero on the subject with the violation planted.
A clean arm that fails cannot be told apart from a broken harness, and a broken harness
detects nothing — the validator returns `UNDECIDABLE`, never `PASS`.

The negative control for this test is declared as run record **`RTR-WO3-0001`**. That record
does not exist yet. It is the run the **independent Assurance seat** will produce — a distinct
actor from the one that wrote this test. Until it exists the validator computes `UNDECIDABLE`
for this test and the gate stays shut, which is correct: this seat may declare which run must
evidence its guard, and may not supply it.

## What this contract does not claim

It does not claim the test passes. It does not claim the criterion is satisfied. It does not
admit any evidence: `latest_admitted_run` is null in the register and this seat cannot fill
it in, because an implementation may not certify itself (`PBG-SOD-001`, non-waivable).
