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

## Declared limits — this row's own sequence, 1 to 8

**DECLARED LIMIT NUMBERS ARE PER REGISTER ROW, NOT PER FILE.** These eight are
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
   **DENY BY DEFAULT, so it is not an escape; it IS a maintenance cost.** EXECUTABLE: add a
   required root property typed `{"type": "string", "pattern": "^ZZZ"}` to either contract and
   this instrument goes RED.

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
