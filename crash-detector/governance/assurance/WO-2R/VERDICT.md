# ASSURANCE VERDICT — WO-2R, crash-detector — CD-ASR-WO2-02

STATUS: IN PROGRESS (written incrementally per SD-1; a verdict that exists only in conversation is
not project state, PBG-CONT-007)

target SHA        : 50fc23177f790164c3fc3604ccee51663e755c70
target tree object: 5a952282ee6eb87079c8def7633b6aeaa1e68171
target worktree   : /srv/crash-detector-wo2r-audit (READ ONLY — nothing executed inside it)
dispatch          : governance/dispatch/CD-DISPATCH-WO2R-ASSURANCE.yaml
actor             : CD-ASR-WO2-02
independence      : DECLARED CLEAN. This seat implemented no part of the target, holds no ENGINEER
                    role on this project, is not CD-ASR-WO2-01, and inherits none of that seat's
                    conclusions.

---

## W1 — AUTHENTIC TARGET: VERIFIED

    $ cd /srv/crash-detector-wo2r-audit && git rev-parse HEAD
    50fc23177f790164c3fc3604ccee51663e755c70          == dispatched target_candidate
    $ git rev-parse HEAD^{tree}
    5a952282ee6eb87079c8def7633b6aeaa1e68171          == dispatched target_tree_object
    $ git cat-file -t 50fc231...                       commit
    $ git status --porcelain | wc -l
    0
    HEAD is DETACHED (expected for an audit worktree).

STALE-WORKTREE TRAP CLEARED: /srv/crash-detector-wo2-audit is at
66681b27ed650321f6b9e325fbc05712a754cc7d — confirmed NOT my target and not read as one.

METHOD: every execution in this audit ran in a throwaway extraction under /tmp made with
`git archive 50fc231... | tar -x` (SD-2). 364 non-.git regular files extracted, matching the
recorded fingerprint denominator. NOTHING was executed inside /srv/crash-detector-wo2r-audit.
No `git worktree add`. No commits. No repairs.

REGISTER TRANSCRIPTION CHECK (dispatch asked me to treat the register as authority): all eleven
declared `execute` strings in the dispatch table are CHARACTER-IDENTICAL to the register at the
target. NO FINDING against the dispatch table.

---

## W2 — THE ELEVEN DECLARED CONTRASTS

Harness: auditor-authored `/tmp/cd-asr-wo2r/arm.sh`. No Engineer-supplied wrapper was used
(PBG-ASSURE-001). Plants applied by me with `git apply`. Every arm is a FRESH extraction.
Full per-arm command / exit / output: /srv/crash-detector-wo2r-evidence/arms/*.txt

DENOMINATOR: 11 declared tests, 22 arms attempted, 22 arms ran (0 apply failures).

| test_id | baseline exit | violated exit | contrast | rule ID asserted (F13) |
|---|---|---|---|---|
| CD-RT-001-AST-NO-NUMERIC-DEFAULT | 0 | 1 | YES | rules A, C, **F** (unrecognised magnitude provenance) |
| CD-RT-001-ABSENCE-RENDERS-UNKNOWN | 0 | 1 | YES | 18 named absence/staleness tests fail |
| CD-RT-002-TYPE-NO-ARITHMETIC | 0 | 1 | YES | arithmetic dunders on score type + ancestor |
| CD-RT-002-AST-NO-BLEND | 0 | 1 | YES | RULE 1 (cross-dial arithmetic), RULE 2 (one expression, both dials) |
| CD-RT-002-SCHEMA-CLOSED | 0 | 1 | YES | rules 3, 4, 5 (undeclared root key `combined_stress`) |
| CD-RT-003-ENGINE-NO-WITNESS-REACH | 0 | 1 | YES | engine reaches witness code, with the route printed |
| **CD-RT-003-GRANT-MATRIX-LIVE** | **3** | **3** | **NO — BOTH ARMS FAIL** | PRECONDITION_NOT_MET both sides |
| CD-RT-005-PANEL-UNAVAILABLE-NEVER-AGREES | 0 | 1 | YES | 12 named resolver/staleness tests fail |
| CD-RT-012-NO-EXECUTION-INTERFACE | 0 | 1 | YES | signature-shape, definition-verb AND prose layers all fired |
| CD-RT-012-LOCKFILE-DENYLIST | 0 | 1 | YES | broker SDK in dependency manifest (`ib-insync`) |
| CD-RT-012-EGRESS-NO-BROKER | 0 | 1 | YES | CD-EGRESS-004 unregistered destination |

### F18 — exit 3 vs exit 1 distinguished
CD-RT-003-GRANT-MATRIX-LIVE returns exit **3 PRECONDITION_NOT_MET** on BOTH arms with no live
store. That is NOT a refusal of the plant. Per the gate (REQUIRED-TEST-REGISTER-CONTRACT-v1
check 2) a violated arm that fails while the clean arm also fails is **UNDECIDABLE, never PASS**.
Closing this is SD-3 work (see W5 section below).

### F16 — assertion counts recorded, no shrink
| arm | baseline | violated | total conserved? |
|---|---|---|---|
| CD-RT-001-ABSENCE-RENDERS-UNKNOWN | 100 passed | 18 failed / 82 passed | 100 == 100 YES |
| CD-RT-002-TYPE-NO-ARITHMETIC | 306 passed | 2 failed / 304 passed | 306 == 306 YES |
| CD-RT-005-PANEL-UNAVAILABLE-NEVER-AGREES | 152 passed | 12 failed / 140 passed | 152 == 152 YES |

Static-check self-reported assertion counts on the violated arms: no-numeric-default 380,
no-blend 4872, schema-closed 244, engine-no-witness-reach 26, no-execution-interface 38891,
lockfile-denylist 17, egress-no-broker 71. No arm silently degraded to a skip.

---

(sections W3, W4, W5, W6, W7, W8, W9 and the per-criterion verdicts follow as they are produced)

---

## SD-3 / W5 — THE GRANT MATRIX, LIVE. THE STANDING RISK CD-RT-002 IS **CLOSED**.

This is the structure the dispatch says nobody on this project has ever verified live, and the
contrast nobody has ever run. I ran it.

STORE: throwaway container `cd-asr-wo2r-store`, image pinned BY DIGEST
`postgres@sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685`
(postgres:16-alpine), volume `cd-asr-wo2r-pgdata`, published 127.0.0.1 on an ephemeral port,
superuser password generated at run time with `secrets.token_urlsafe(24)` and never written into
any record. PostgreSQL 16.15. No container or volume without the `cd-asr-wo2r-` prefix was
touched, inspected, started or stopped.

    baseline arm  db cd_asr_probe (7 subject-tree migrations)  EXIT 0   PASS — 138 assertions, 0 violations
    violated arm  db cd_asr_v003  (8 migrations, plant applied) EXIT 1   FAIL — 9 violations, 138 assertions

CONTRAST ESTABLISHED. F16: assertion count 138 on BOTH arms — no shrink, no skipped arm.
F18: this is a real exit-1 violation, NOT the exit-3 PRECONDITION_NOT_MET that both arms returned
without a store. The two are distinguished on the evidence, not assumed.
F13: the rule IDs are asserted, not merely the exit code. The plant is caught on SIX INDEPENDENT
ROUTES — `CD-GM-001 route=schema-privilege USAGE`, `route=table-privilege` (x2),
`route=column-privilege`, and — decisively — `route=live refusal`, where the check opened a real
session as cd_engine and PostgreSQL itself executed `SELECT 1 FROM witness.observation LIMIT 1`.
Plus `CD-GM-002` and the WHOLE-MATRIX comparison. That is a guard reading the catalogue by
several independent means rather than one.

evidence: arms/B-003-GRANT-LIVE.out, arms/V-003-GRANT-LIVE.out

### My own catalogue queries — evidence independent of the check (PBG-EVID-001)
I did not take the check's word. I queried the live catalogue directly with `psql`:

  * `cd_engine` on schema `witness`: **16/16 probes false** — USAGE, CREATE, and
    SELECT/INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER on both `witness.observation` and
    `witness.reading`. NO privilege of any kind. CONFIRMED.
  * `pg_authid` for all six cd_* roles: rolsuper=f, rolbypassrls=f, rolcreaterole=f, rolcreatedb=f,
    **rolpassword IS NULL** (no password on any role), **rolinherit=f**. CONFIRMED.
  * `pg_auth_members`: ZERO memberships among the six cd_* roles (the only rows are PostgreSQL's
    own pg_monitor built-ins). No role inherits another's privileges. CONFIRMED.
  * every UPDATE/DELETE/TRUNCATE grant in the database to a non-owner: **NONE** on any project
    table. (The single row returned is PostgreSQL's built-in `PUBLIC` UPDATE on
    `pg_catalog.pg_settings`, which ships with the server and is not this project's grant.)
    The append-only posture holds in the live catalogue. CONFIRMED.
  * schema ACLs: `witness` is `{cd_asr_super=UC, cd_witness=U}` — cd_witness alone. CONFIRMED.
  * `pg_default_acl`: exactly one entry — schema `private`, relations, `cd_private=ar`
    (INSERT+SELECT). No default privilege grants UPDATE or DELETE on any FUTURE object, and none
    exists for schema `witness`. CONFIRMED.

W5 grant-matrix element: **PASS**, on my own queries against a live catalogue I built myself from
the subject tree's migrations. DENOMINATOR: 6 roles, 8 schemas, 16 direct privilege probes on the
witness schema, plus 4 whole-catalogue sweeps.

---

# W3 — FRESH ADVERSARIAL VARIANTS. THIS IS THE DISPATCH.

All variants below were devised by CD-ASR-WO2-02 by reading the structures, not the exclusion set.
Each is recorded as DATA under /srv/crash-detector-wo2r-evidence/variants/ (`.py.txt` / `.patch.txt`
suffixes, no +x bit). Every arm ran in a fresh `/tmp` extraction of 50fc231.

## FINDING CD-ASR-WO2R-F01 — **HIGH** — CD-AC-002. THE CLASS IS NOT CLOSED.
### `combine_within_one_dial` is an unguarded proxy through the derivation door.

variant: `variants/ASR2-002-A-derivation-door-launders-a-blend.py.txt`
authentic target: 50fc23177f790164c3fc3604ccee51663e755c70, file added at
`src/crash_detector/publication/composite.py` (INSIDE the scanned set — the check counted 41 files
with it present, 40 without).

**THE PROPOSITION VIOLATED.** `src/crash_detector/dials/magnitude.py` boundary A states the claim
increment 2b was accepted on, in terms:

>  "What IS claimed, and is measured: **the sum cannot come back.** ... Read it as claiming that
>   **no number so obtained can ever be a dial magnitude again.**"

**THAT CLAIM IS FALSE AT THIS SHA.** The sum comes back.

**THE ROUTE.** `check_no_blend.py` RULE 4 denies by default over `ADMISSION_VOCABULARY =
{observed_for_dial, derived_within_one_dial, DeclaredQuantity}`. **`combine_within_one_dial` is not
in that set** — and it is PUBLIC API, re-exported in `crash_detector/dials/__init__.py` `__all__`
(line 67). It computes the dial set from the magnitudes it was given (so the LABEL is evidence,
exactly as documented) but it then passes the caller's arbitrary `using` callable's RETURN VALUE
**straight into `derived_within_one_dial`, which validates nothing at all**:

    return DialMagnitude(dial_id=dial_id,
                         quantity=derived_within_one_dial(dials=dials, value=using(numbers)))

`using` is a closure. It can close over the OTHER dial's released number. The door checks the label
and never looks at the value.

    def console_figure(readings):
        held = tuple(readings)
        numbers = [reading.quantity_for(sole_dial_of(reading)) for reading in held]
        carried = sum(numbers) / len(numbers)
        return combine_within_one_dial([held[0]], using=lambda _released: carried)

No dial name appears in any expression (`sole_dial_of` supplies it at runtime). No admission-door
name appears. No private slot is touched. No `repr`, no f-string, no JSON, no `getattr`, no
`importlib` — none of the laundering routes CD-PL-F54 closed.

**MEASURED — all four declared static/behavioural layers exit 0 WITH THE VARIANT PRESENT:**

    CD-RT-002-AST-NO-BLEND        EXIT 0   PASS — 4873 assertions, 0 violations   (clean: 4855)
    CD-RT-002-SCHEMA-CLOSED       EXIT 0   PASS — 242 assertions, 0 violations
    CD-RT-002-TYPE-NO-ARITHMETIC  EXIT 0   306 passed
    CD-RT-001-AST-NO-NUMERIC-DEF  EXIT 0   PASS — 377 assertions, 0 violations
    WHOLE SUITE  PYTHONPATH=src python3 -m pytest tests -q   EXIT 0   1325 passed

F16: the assertion count ROSE from 4855 to 4873 — the check DID scan the new module and had
nothing to say about it. This is not a skipped arm; it is a clean pass over a live blend.

**THEN EXECUTED:**

    equity  magnitude: DialMagnitude(dial_id='equity_crash', quantity=0.9)
    monetary magnitude: DialMagnitude(dial_id='monetary_debasement', quantity=0.1)
    RESULT TYPE : DialMagnitude
    RESULT      : DialMagnitude(dial_id='equity_crash', quantity=0.5)
    provenance  : ['equity_crash']
    IS IT A GENUINE DialMagnitude?  True
    DID THE BLEND RE-ENTER?         True

**AND IT PUBLISHES.** The blended magnitude is accepted by the score type and by the publication
gate — the two layers CD-PL-F54 was closed to protect:

    score type accepts the blended magnitude : *** NOT REFUSED *** ->
        EquityCrashScore(score=DialMagnitude(dial_id='equity_crash', quantity=0.5), contributions=())
    PUBLICATION GATE number_for_dial_slot    : *** NOT REFUSED *** -> 0.5

Equity 0.9 and monetary 0.1 are published as an equity reading of **0.5**. That is the exact
product failure PID §3.1 calls constitutional — averaging cancels the signal — reached through a
magnitude carrying a single, honest-looking, *computed* provenance.

**WHY THIS IS NOT IN THE EXCLUSION SET, STATED PRECISELY.** I did independently rediscover the
neighbourhood, and the dispatch asks me to say so. `PL-R2` ("derived_within_one_dial re-admits the
blend") called that door DIRECTLY and was recorded `*** NOT REFUSED ***`, then dispositioned
"INSIDE THE DECLARED LIMIT, boundary 7". `PL-R5` — described in BL-20260819T115400Z-0025 as
"THE DECISIVE ONE ... what an engineer who reads the new code and wants a blend anyway would
actually write" — was CAUGHT, with two RULE 4 violations, and CD-D-040 accepted increment 2b on
exactly that basis: *"by structure at the re-entry PLUS a deny-by-default static layer at the doors"*.

**MY VARIANT DEFEATS THE STATIC LAYER THAT MADE PL-R2 ACCEPTABLE.** Boundary 7 says "RULE 4 is the
only layer over it" and then enumerates its own residues exhaustively: (i) an edit to
`DECLARED_ADMISSION_SITES`, (ii) a module outside the scanned set (boundary 4), (iii) a dynamically
assembled door name (boundary 5). **My route is none of the three.** The module is inside the
scanned set, edits no registry, and assembles no name. It walks through a door RULE 4 guards by
using a public function RULE 4 does not know is a door. A registry that denies by default over a
vocabulary is only as closed as its vocabulary, and this vocabulary has a public proxy missing
from it.

**SEVERITY HIGH** because: the runtime residue that boundary 7 declares was accepted *on the
strength of the static carrier*, and the static carrier does not hold for this route. Under
CD-RULE-006 a boundary asserting a carrier that does not carry it is the CD-PL-F54/CD-PL-F59
defect. This is that defect, one function across.

**NOT REPAIRED BY ME (PBG-SOD-004).** For the record only, and not as a design: the shape of the
question is whether `combine_within_one_dial` belongs in `ADMISSION_VOCABULARY`, and whether a
derivation door can validate a value it did not compute. Both are the Engineer's to answer.

## FINDING CD-ASR-WO2R-F02 — **HIGH** — CD-AC-005. THE FOURTH CONSTRUCTOR ROUTE EXISTS.
### `ensure_utc` admits a `datetime` SUBCLASS by `isinstance`; a decade-old row renders WITNESS AGREES.

variant: `variants/ASR2-005-A-datetime-subclass-lies-about-age.py.txt`
(added at `src/crash_detector/serving/panel_feed.py`)

**THE PROPOSITION VIOLATED.** CD-AC-005: WITNESS UNAVAILABLE is not WITNESS AGREES; there is no
input — missing, stale, malformed or defaulted — from which the serving layer produces AGREES.

**WHY THIS IS THE EXACT GAP THE BOUNDARY INVITED.** `src/crash_detector/staleness.py` boundary 3
says, of the `object.__setattr__` residue:

>  "it is not a route from ordinary input, and **every route measured that goes through a
>   CONSTRUCTOR is refused. THREE MEASURED, and three is the denominator, not a proof that a
>   fourth does not exist**"

**THIS IS THE FOURTH.** It uses no `object.__setattr__`, no reflection and no post-construction
write. It goes through `PanelRow.__post_init__`, `resolve_panel`, `StalenessWindow.__post_init__`
and `FreshnessEvidence.__post_init__` — every constructor on the path — and reaches `Agrees`.

**THE ROUTE, AND WHY IT IS THIS PROJECT'S OWN DOCTRINE APPLIED ONE OPERAND ACROSS.**
`StalenessWindow` refuses a `float` subclass in terms, on exact type, with the reason spelled out:

>  "a subclass of a number is not a number: it may redefine what comparison means, and a window
>   whose comparisons it controls is not a window at all."

The age comparison has **TWO operands**. That doctrine was applied to the window and **never to the
timestamp**. `ensure_utc()` admits any `datetime` by `isinstance` (`time_utc.py:44`), and
`age_seconds()` computes the age by SUBTRACTING two datetimes. A `datetime` subclass controls that
subtraction:

    class FeedInstant(datetime):
        def __rsub__(self, other):  return timedelta(0)
        def astimezone(self, tz=None):  return self

`PanelRow.__post_init__` normalises through `ensure_utc`, which returns `value.astimezone(...)` —
and the subclass survives the normalisation (measured: `after PanelRow normalisation, as_of_utc
type: FeedInstant`).

**MEASURED — a row dated 2016-08-21 read at 2026-08-19 with a 600 s window:**

    row as_of_utc is a FeedInstant = 2016-08-21 00:00:00+00:00
    resolved  : Agrees
    state     : AGREES
    RENDERS   : WITNESS AGREES

    CONTROL - the same decade-old instant as a PLAIN datetime:
    resolved  : Unavailable | RENDERS: WITNESS UNAVAILABLE

That control is the contrast: identical data, identical window, identical call — the ONLY variable
is the concrete type of the timestamp.

**AND EVERY DECLARED GUARD IS GREEN WITH IT PRESENT:**

    CD-RT-005-PANEL-UNAVAILABLE-NEVER-AGREES   EXIT 0   152 passed   (clean also 152 — F16: no shrink)
    WHOLE SUITE  pytest tests -q                EXIT 0   1325 passed
    check_no_numeric_default / check_no_blend / check_engine_no_witness_reach /
    check_no_execution_interface                all EXIT 0

**NOT IN THE EXCLUSION SET.** No variant under `variants/` and no PL probe under
`governance/reconciliation/WO-2R/` defines a `datetime` subclass; the corpus attacks this criterion
via window width (E07), exception handlers (E08), rendering maps, and `object.__setattr__`
(PL-W5). The subclass route is untouched.

**WHY SEVERITY IS HIGH AND NOT A CURIOSITY.** `datetime` subclasses are ordinary in this problem
domain — `pandas.Timestamp` IS a `datetime` subclass, as are `freezegun`'s and several time
libraries' types. A collector or adapter handing the resolver such an object is not an attack, it
is Tuesday. The guard's own reasoning already identifies subclass-controlled comparison as the
hazard; it simply guards one of the two operands. The `Agrees` produced here is internally
coherent — it carries genuine `FreshnessEvidence` whose constructor ran and computed an age of
zero — so no downstream re-validation can distinguish it.

**A RELATED WEAKNESS OBSERVED WHILE HERE, reported not as a separate finding but as the same
class:** `witness_resolver._finite_measure` admits a measurement with
`isinstance(observed, float)`, which also accepts a `float` subclass — the very type
`StalenessWindow` refuses by exact type four modules away. The two modules disagree about whether a
subclass of a number is a number.

**NOT REPAIRED BY ME (PBG-SOD-004).**

## FINDING CD-ASR-WO2R-F03 — **MEDIUM** — CD-AC-001. ABSENCE RENDERS AS CALM ON THE SCANNED PATH.
### `fold`'s `on_unknown` branch may return a number, and nothing at this SHA refuses it.

variant: `variants/ASR2-001-A-fold-unknown-branch-returns-calm.py.txt`
(added at `src/crash_detector/serving/dial_surface.py` — the ADJACENT tier, which IS in the
check's declared scanned set; the check counted it)

**MEASURED:**

    CD-RT-001-AST-NO-NUMERIC-DEFAULT   EXIT 0   PASS — 377 assertions, 0 violations
    CD-RT-001-ABSENCE-RENDERS-UNKNOWN  EXIT 0   100 passed          (clean also 100 — no shrink)
    WHOLE SUITE                        EXIT 0   1325 passed

    reading        : Unknown | reason: REQUIRED_INPUT_MISSING | missing: ('vix', 'move')
    SURFACE SHOWS  : 0.0
    ABSENCE RENDERED AS A NUMBER? True

A dial that did not get its inputs shows `0.0` — calm — which is the exact failure PID §3.2
forbids.

**IT USES NONE OF THE ENUMERATED SPELLINGS** and none of the exclusion set's routes: no
`float | None` (rule A), no `or 0.0` (rule C), no `.get(key, 0)`, no bare `except`, no module-level
numeric constant (E04), no numeric member on `Unknown` (E03), no dynamic constructor (boundary 1).
It does not CONSTRUCT a value-bearing reading at all — which is why Rule F, whose whole subject is
the provenance of a constructed magnitude, has nothing to look at.

**IT GOES THROUGH `fold`** — the exhaustive, no-default-branch, surface-re-verifying consumer the
design points every caller at. `fold`'s guarantee is that a caller **cannot FORGET** `Unknown`.
It is not a guarantee that a caller cannot **ANSWER** `Unknown` with a number, and the criterion
is about the second.

**I CHECKED ALL SIX DECLARED BOUNDARIES BEFORE CALLING THIS A FINDING.** Boundaries 1, 2, 3, 5 and
6 of `check_no_numeric_default.py` are all about a value-bearing reading being CONSTRUCTED
(dynamically, in a helper, outside the scanned set, wrongly computed, or from configuration).
Boundary 4 is the class-A scoping note. **None of the six covers a consumer folding `Unknown` to a
number, and the plant is inside the declared scanned set, not outside it.** The header names its
carrier explicitly — "THE RUNTIME LAYER CARRIES THIS: the sealed, slotted, subclass-closed
`Reading` types and the absence post-condition in `evaluate.py`" — and that carrier does not carry
this route: `refuse_a_number_without_its_inputs` guards the evaluation, not the surface, and the
sealed types are intact here (nothing was mutated).

**SEVERITY MEDIUM, honestly qualified.** The rendering/publication layer is WO-3, so a consumer
like this is not yet part of the product; and one can argue CD-AC-001's runtime layer is asked to
guard construction, not consumption. What makes it a finding rather than an observation is that
the criterion's words are about RENDERING ("Missing or stale input never renders as calm"), the
plant sits on a path this check declares it scans, and no declared limit reserves this route.

---

# W7 — THE EXCLUSION SET AUDITED AS A HAZARD IN ITS OWN RIGHT

## THE DENOMINATOR IS SETTLED. Neither "71" is right; the Project Lead's count is.

Measured at the target by `find` over `variants/`:

    70   *.patch
     2   *.py.txt              (the CD-PL-F65 probe records)
     1   MANIFEST.md
    ---
    73   files    =    72 variant artefacts + the index
     0   executable — `find variants/ -perm -u+x` is EMPTY; all 73 are mode 0664, no symlinks.
                     PBG-ASSURE-001 satisfied, VERIFIED INDEPENDENTLY.

Per-directory sums reconcile exactly: 6+2+3+12+2+14+8+16+7 = 70.

**WHERE "71" CAME FROM — settled, and it is a transcription defect, not missing work.** The
increment-6 re-run tables (MANIFEST.md lines 1785-1846) name **73 distinct variant IDs**, of which
**3** (PL-Q4/Q5/Q6) are expressly PATCHLESS probes. 73 − 3 = **70**, exactly the patch count. The
Engineer seat's "71 re-run, 71 verdicts" reproduces a wrong number from MANIFEST.md line 1762.
THE WORK WAS DONE; THE COUNT WAS MIS-STATED. This closes the item the dispatch handed over as
unreconciled.

## CD-ENG-WO2R-F27 — **REPRODUCES EXACTLY**, and is worse than recorded in one respect
Ran the MANIFEST's BLEND-PROBE verbatim on a throwaway extraction with E01 applied. Exit 1 with an
UNCAUGHT traceback — `report()` is never reached:

    crash_detector.dials.provenance.QuantityProvenanceMissing: a bare number (0.9) was offered
    as dial 'equity_crash''s magnitude.

Control: identical failure on a clean extraction with no patch. Both fixtures are module-level and
the arm selection is textually below them, so **all seven arms are unreachable**, not merely the
one measured. CONFIRMED, and the seat's own severity (MEDIUM) is right.

## CD-ENG-WO2R-F28 — **REPRODUCES EXACTLY**, in both directions
V11 applies cleanly; under the corrected probe it dies at
`TypeError: unsupported operand type(s) for +: 'int' and 'DeclaredQuantity'` in `merged_magnitude`.
The object is never constructed, so all three boundaries the row names are unreachable by V11's own
route. The mitigation checks out too: forging the magnitude directly reproduces all three refusals
word for word, and the AST arm matches the row exactly (exit 1, 2 violations, RULE 3).
**ADDITION TO F28 THIS AUDIT FOUND:** V11's *literal* declared command is "BLEND-PROBE, then AST".
Retyped literally it produces neither the row's outcome nor F28's — it produces F27's scaffolding
refusal. An auditor must apply BOTH declared corrections to observe anything about V11 at all.

## THE SAMPLE — DENOMINATOR STATED
`git apply --check`: **70 of 70 (100%) apply cleanly, 0 failures.**
Run end-to-end with their declared commands: **22 of 70 (31%)**, chosen by the dispatch's hazard
criterion (structures increments 1-6 rewrote), deliberately including rows claiming a PASS.

    applies                                        70/70
    reaches the boundary its row names             22/22
    names the RULE ID the row claims (F13)         22/22
    exact match on every recorded detail           18/22
    substance match, stale line number              4/22

**NO ROW IN THE SAMPLE CLAIMED A ROUTE WAS COVERED WHEN IT WAS NOT.** Every "REFUSED" row still
refuses by the named rule; every honest-negative row (V12/V13/V15/V17/V29a/V44) still escapes, so
the corpus is not lying about its coverage. **This is the single most reassuring result in the
audit** and it is recorded as such.

## FINDING CD-ASR-WO2R-F04 — **LOW** — four corpus rows carry stale line numbers
V12 (RULE 4 recorded @ banner.py:4,:22 — actually :4,:25), V13 (:19 → :22), V15 (:4,:19 → :4,:23),
V17 (RULE 3 @ :6,:7,:16,:17 → :10,:11,:21,:22). All four are patches that CREATE `banner.py` from
`/dev/null`, so the line numbers are a deterministic property of the patch bytes — verified against
the bytes, with `git apply -v` clean and no offset. **The patches were edited after their rows were
measured** (a uniform +3/+4 shift) and the rows were never re-measured. Increment 6's re-run
recorded only EXIT CODES for these four, which are invariant under the edit, so it structurally
could not have caught this.
NOT the hazard the dispatch names — the rows still send an auditor to the right layer with the
right rule ID; only the coordinate is stale. LOW.

## WHAT W7 DID NOT REACH, stated rather than footnoted
48 of 70 were apply-checked only, not run — absence of mismatch in my 22 is not evidence about the
other 48. Positive controls V24/V28/V42/V31/V45 not re-run. Neither `.py.txt` probe executed. The
V30/R-series non-termination rows not re-measured. And I could not determine WHEN the banner.py
patches were edited relative to their rows — only that artefact and record disagree today.

Raw evidence: `/srv/crash-detector-wo2r-evidence/notes/W7-corpus-audit.md`

## CD-AC-003 — TWO FRESH ATTACKS, BOTH REFUSED. THE GUARD IS PROVED TO BITE THE CLASS.

The dispatch asks me to say so when a guard catches the class, because a guard proved to bite is
worth recording as proved. This one is.

**ASR2-003-B — the compose `command:` override.** I started `cd-engine` on a DIFFERENT entrypoint
(`deploy/entrypoints/cd_engine_console.py`, which imports `crash_detector.witness.panel`) by adding
a compose `command:` — not by touching the Dockerfile's ENTRYPOINT the derivation reads.

    EXIT 1  VIOLATION src/crash_detector/witness/panel.py
            rule: engine reaches witness code
            Route (nearest first): crash_detector.witness.panel <- cd_engine_console

CAUGHT, and caught for the RIGHT reason (F13) — the route names my override's module. The
derivation genuinely composes `entrypoint + command` rather than reading ENTRYPOINT alone.

*F18 note, recorded because it is exactly the trap the method note warns about:* my FIRST attempt
wrote the command as a JSON flow sequence and returned **exit 3 CD-ENGINE-ROOT-101
PRECONDITION_NOT_MET** ("non-empty flow collections are not supported by this reader"). That is a
READER REFUSAL, not a catch. Had I recorded "non-zero, therefore caught" I would have credited the
guard with a refusal it had not made. I rewrote it in block form and obtained the real exit-1
violation above.

**ASR2-003-C — rename the guard's subject out from under it.** I renamed the whole
`src/crash_detector/witness/` package to `corroborators/` and rewrote every reference, to test
whether the guard identifies witness modules by the literal name `witness` and would pass
vacuously once its subject vanished.

    with the rename, no engine import : EXIT 0, PASS 24, note: "2 witness module(s) exist and were
                                        the subject of the assertion: crash_detector.corroborators,
                                        crash_detector.corroborators.panel"
    with the rename AND an engine import: EXIT 1, VIOLATION on crash_detector.corroborators.panel

**IT TRACKED THE RENAME.** The witness module set is derived from the container topology, not from
the string "witness", and the guard reports its subject count on every run so a vacuous pass would
be visible. This is a genuine class closure and the best-engineered guard I attacked.

### Observation (LOW, not a finding) — ASR2-003-A
Copying the panel's TYPES into the engine package under a non-witness name
(`src/crash_detector/engine/corroboration_panel.py`, imported by `evaluate.py`) exits 0, PASS 25.
I am NOT recording this as a defect: the check's boundary 3 says in terms that "IMPORTING WITNESS
TYPES IS NOT READING WITNESS DATA", and the DATA half is carried by the grant matrix, **which I
measured live myself** — `cd_engine` holds zero privilege of any kind on schema `witness` across
16 direct probes, and PostgreSQL refuses it in a real session. The carrier here is measured, not
asserted. That is a limit honestly drawn with a carrier that actually carries.

## CD-AC-012 — THREE FRESH ATTACKS. ONE ESCAPE THAT MATTERS.

### FINDING CD-ASR-WO2R-F05 — **MEDIUM** — a REAL broker SDK escapes the denylist while the
### register declares that test `scope: CLASS`.
variant: `variants/ASR2-012-B-real-broker-sdk-not-on-denylist.txt`

    tastytrade-sdk==1.2.0  in requirements.txt AND requirements.lock
    CD-RT-012-LOCKFILE-DENYLIST   EXIT 0   PASS — 17 assertions, 0 violations

tastytrade is a **real, currently-operating US brokerage** and this is its real order-entry SDK.
It is not a fictional name: it is absent from the 61-name denylist and carries none of the
execution tokens (`broker`, `order`, `trade`, `trading`, `execution`, `oms`, `ems`, `fix`,
`exchange`). Note that `trade` is a token and `tastytrade` contains it — the check normalises and
matches tokens as words, not substrings, so the brand name defeats it.

CONTROLS, run in the same batch so the result is not one lucky name:
  * `meridian-fix-connect==0.4.1` -> **EXIT 1, CAUGHT** on the `fix` token. The token rule genuinely
    generalises, exactly as the header claims.
  * `lattice-client==2.0.0` -> exit 0, escaped (but this one is a fictional name, so it proves less).

**WHY THIS IS A FINDING AND NOT MERELY THE DECLARED FLOOR.** The check says in its header that the
denylist "is explicitly a FLOOR and not an oracle", and that is honest. But (a) it is **not written
in the CD-RULE-004 numbered-boundary form** — there is no DECLARED LIMIT section, no numbered
boundaries, no executable example and **no named carrier** for what the floor does not reach, unlike
its two sibling CD-AC-012 checks which both have one; and (b) `required-tests.yaml` declares this
test **`scope: CLASS`**. A reader relying on the register is told this guard closes the class. It
does not: it closes a 61-name list plus a token rule, and a real broker SDK walks through.
**This is NQ-4 made concrete** — see the NQ answers below.

MITIGATION, measured not assumed: a dependency is permission to import, not a pathway. The pathway
needs somewhere to go, and I measured the egress layer denying by default with an **EMPTY**
admissible set (0 registered destinations). So the product harm is contained; the register's
description of the guard is what is wrong.

### Observation (LOW) — ASR2-012-C, the split order ticket
`variants/ASR2-012-C-order-ticket-split-across-two-types.py.txt` splits an order ticket across two
frozen dataclasses (`Leg{ref,size}` and `Target{endpoint,account}`) so that no single field set is
an order-entry signature, then joins them in `forward(leg, target, direction, limit)`.
`CD-RT-012-NO-EXECUTION-INTERFACE` exits 0 (PASS, 38883 assertions vs 38847 clean — it scanned the
module and had nothing to say). L2 reads FIELD SETS, and a set that has been split is not a set.
Reported LOW rather than as a finding: this is close kin to declared boundary 1 (deliberate
euphemism), which the FIRST auditor already judged honestly drawn and "genuinely unbounded and
always will be", and the harm is again carried by the measured-empty egress registry. But I record
that **none of the six declared boundaries names structural splitting** — they name euphemism,
`work_order` suppression, L3's suppression list, motion-chain length, non-Python/SQL files, and
runtime. Splitting is a seventh shape.

### ASR2-012-A — the `_yamlmin` reader turned on the egress check. REFUSED. (NQ-2, see below.)

---

# W4 — THE REGISTER ITSELF

    $ PYTHONPATH=pbg/tools python3 -B -m pbg.cli required-tests verify --register required-tests.yaml
    EXIT 2
      pid.ref               PID.md
      pid.content_hash      MATCHES
      latest_admitted_run   (null)
      all 16 criteria       UNDECIDABLE
      MANDATORY NOT PASS (15) — no waiver exists; only PO disposition can move these

INDEPENDENTLY CONFIRMED: the criteria population is all SIXTEEN, CD-AC-001..016, derived from
PID §6 — the validator derives the census from the PID text itself and did not object.
`pid.content_hash` MATCHES the PID at the target. `latest_admitted_run` is **null**. I parsed the
register with a YAML loader and confirmed **NO status-like key appears anywhere**: the top-level
keys are exactly `register_version`, `pid`, `latest_admitted_run`, `criteria`. **THE GATE IS SHUT,
which is the correct and honest answer at WO-2 and is NOT a defect of this candidate.**

## THE ELEVEN UNDELIVERED-CRITERIA COMMANDS — NOW MEASURED AT 50fc231, NOT ARGUED
This was on the NOT_INDEPENDENTLY_VERIFIED list because the Project Lead measured them at the BASE
and reasoned that no logic changed. I re-ran all eleven at the final SHA. **DENOMINATOR: 11 of 11.**

    9 pytest commands  -> EXIT 4   "ERROR: file or directory not found: tests/test_<x>.py"
    2 check commands   -> EXIT 2   "can't open file '.../check_<x>.py': [Errno 2] No such file..."

**EVERY ONE terminates NON-ZERO naming an ABSENT SUBJECT. NONE passes vacuously.** The argument
was correct; it is now a measurement. Evidence: `arms/W4-undelivered-eleven.txt`.

# W9 — THE RUN RECORD, AND THE CD-RULE-001 TEST

Written to `required-tests/runs/RTR-WO2R-0001.json`: 22 results (11 NEGATIVE_CONTROL with both
arms, 11 ACCEPTANCE). Every `command` string was read PROGRAMMATICALLY OUT OF THE REGISTER and is
character-identical to its declared `execute`, verified by equality assertion. Every exit code is
what I actually observed. Nothing was adjusted; no arm is recorded that I did not run.

**I DID NOT ADMIT IT** — admission is a separate act under CD-RULE-001 and is not mine
(PBG-AUTH-003).

## THE FRAMEWORK HOLDS. NO FINDING AGAINST IT.
The dispatch asks whether my record could make a criterion I hold not-PASS compute PASS — and says
that if it could, it is a HIGH finding against the framework. I tested it, including adversarially:

    A) record placed as written (RTR-WO2R-0001)     -> all criteria UNDECIDABLE. Not PASS.
    B) DIAGNOSTIC: the SAME exit codes renamed to
       RTR-WO2-0001, the id the register's
       negative_control.evidence_ref actually cites  -> all criteria NOT_EVALUATED. STILL NOT PASS.

Arm B is the important one: **passing exit codes alone cannot compute PASS**, because
`latest_admitted_run` is null and admission is a separate act by a separate party. The register
grades nothing and computes everything. CD-RULE-001 is structurally enforced, not merely asserted.

**ONE OBSERVATION (LOW), not a defect:** the register's `negative_control.evidence_ref` for all
eleven WO-2 tests cites `RTR-WO2-0001`, while this dispatch instructed me to write
`RTR-WO2R-0001`. Whoever admits evidence will have to reconcile those two identifiers. I have NOT
changed either — renaming a register field to make my own record resolve is exactly the act
PBG-FWK-013 and PBG-ASSURE-012 forbid.

---

# TARGET INTEGRITY ON RETURN

    $ find . -path ./.git -prune -o -type f -print | wc -l   ->  364   (== recorded denominator)
    $ find . -name __pycache__ -o -name .pytest_cache | wc -l ->    0
    $ git status --porcelain | wc -l                          ->    0
    $ git rev-parse HEAD  -> 50fc23177f790164c3fc3604ccee51663e755c70

I recomputed the per-file sha256 manifest and **diffed it against the Project Lead's
`/tmp/cd-asr-wo2r-tree.sha256sums` line by line: IDENTICAL CONTENT. Not one of the 364 files
changed.** The PL manifest still reproduces its recorded fingerprint
`50ae34d657126709c0e44b3a57c58c8308d25c1cb845aa70b30e86338a2d729d` exactly.

**METHOD NOTE FOR THE NEXT AUDITOR (LOW, and it nearly caught me):** my first recomputation
produced a DIFFERENT manifest hash, and F13 says a surprising result is the one to investigate.
The cause was not mutation — `LC_ALL=C sort` over `sha256sum` output sorts by the WHOLE LINE
(hash first), whereas the recorded manifest is sorted by PATH. The fingerprint method as written
in the dispatch does not state its sort key, so a future auditor will see a "mismatch" that is not
one. Recommend the method state `sort -k2`.

---

# W6 — THE DECLARED LIMITS

**SCOPE MEASURED: 43 numbered boundaries across 11 delivered register entries** — not "roughly
nine". Per guard: numeric_default 6 · no_blend **7** · engine_no_witness_reach 6 ·
no_execution_interface 6 · egress_no_broker **10** (1-8, 8b, 9) · absence_renders_unknown 1 ·
type_no_arithmetic 1 · panel_unavailable 4 · schema_closed 1 · grant_matrix_live **0** ·
lockfile_denylist **0**. Full table: `notes/W6-declared-limits.md`.

## (b) UNMEASURED CARRIERS — the CD-RULE-006 question

### FINDING CD-ASR-WO2R-F06 — **the one boundary that fails CD-RULE-006 in form — AND I HAVE NOW MEASURED IT, SO IT IS DISCHARGED**
`check_engine_no_witness_reach` boundary 3 hands the DATA half of CD-AC-003 to
`CD-RT-003-GRANT-MATRIX-LIVE` with the **unqualified** word CARRIED: *"which PROVES `cd_engine`
holds no privilege of any kind on schema `witness` by any of seven routes, IN A REAL POSTGRESQL
SESSION. CARRIED."* Every other carrier sentence in the corpus is qualified
(`CARRIED, MEASURED` / `PARTIALLY CARRIED, MEASURED` / `NOT PROVED TO BE CARRIED ANYWHERE`).
This one is not — and it was the one with **no measurement anywhere in the record**
(`BL-20260819T193519Z-0049.yaml:151`: *"CD-RT-003-GRANT-MATRIX-LIVE's CONTRAST was again NOT
re-run for want of a live store"*).

**THIS AUDIT DISCHARGES IT.** I built the store, ran both arms, and measured the carrier
CARRYING: clean PASS 138/0, plant FAIL with 9 violations across 6 independent routes including a
live PostgreSQL session refusal. **The boundary's claim is TRUE. Its FORM was defective — it
asserted a measurement that had never been taken.** That distinction matters: the seat was right,
and was right without evidence, which under CD-RULE-006 is the CD-PL-F54/F59 shape. Recorded as a
FORM finding now DISCHARGED ON THE FACTS by this audit.

### FINDING CD-ASR-WO2R-F07 — **MEDIUM** — a carrier that was MEASURED NOT TO CARRY
`contracts/public_envelope.schema.json:5` — the text the register points to as canonical for
SCHEMA-CLOSED's limit — names as its carrier *"the register's AST no-blend check flags a single
expression consuming both dial types."* **That check's scope was demoted CLASS -> INSTANCE at
WO-2R precisely because it cannot close this class** (confirmed: `required-tests.yaml` declares
`CD-RT-002-AST-NO-BLEND` `scope: INSTANCE`), and E01/E02 both exit 0 on it. The schema text is
pre-CD-ASR-F01 and was never re-measured. Meanwhile the register entry names a DIFFERENT carrier
(`publication.dial_scalar` / the re-entry), the check header names a THIRD (two pytest modules),
and the execution contract names NONE. **Four texts, three carrier sets, one of them demonstrably
demoted.**

### CD-ASR-WO2R-F08 — **LOW-MEDIUM** — mis-scoped carrier
All three NO-EXECUTION-INTERFACE texts offer as structural carrier *"cd-engine, cd-public,
cd-private and cd-store have no egress at all."* But the residue (euphemism, non-.py/.sql) lives
anywhere in five roots including `cd-collectors`, `cd-witness` and `cd-review`, which declare
`policy: ALLOWLIST`, not NONE. What actually reaches them is `internal: true` on both networks —
which IS measured, but that sentence appears only in the EGRESS guard's boundary 1 and never in
this guard's declaration.

## (c) THREE PLACES — SUBSTANCE DISAGREEMENTS. The dispatch was right to distrust the token matrix.

### FINDING CD-ASR-WO2R-F09 — **MEDIUM** — the register ASSERTS a WITHDRAWN, defect-causing text
The exact CD-PL-F71 shape, and the dispatch's assumption that F71 was not the only instance is
CONFIRMED.
  * register, boundary (5), asserted as current: *"Only the ENGINE service's process is a WALK
    ROOT; the other five are RESOLVED..."*
  * check header: *"AMENDED AT CD-D-055 CLOSING CD-PL-F62 ... **It used to read** 'ONLY THE ENGINE
    SERVICE'S PROCESS IS DERIVED AS A ROOT...'"*
  * execution contract: *"**This boundary used to read** 'only the engine SERVICE's process is a
    walk root ... the other five are resolved'"*

Two places quote it as SUPERSEDED; the register asserts it as CURRENT. It is a SCOPE disagreement
— service-name versus image-identity — and it is **the exact narrowness that let PL-U6b escape**.
Mitigating: the error makes the guard look NARROWER than it is, so it creates no false assurance.

### FINDING CD-ASR-WO2R-F10 — **MEDIUM** — the CD-RULE-006 discharge sentence says the OPPOSITE thing, 2-of-3
  * check header: *"EVERY 'CARRIES THIS' ABOVE HAS BEEN RE-MEASURED **AT THIS COMMIT**, not
    inherited from the increment that wrote it."*
  * register AND contract: *"EVERY 'CARRIES THIS' ABOVE WAS RE-MEASURED **AT THE COMMIT THAT WROTE
    IT**, not inherited."*

"At the commit that wrote it" **IS** the inherited measurement CD-RULE-006 forbids, and the
trailing "not inherited" contradicts its own subject. The MAJORITY reading is the weaker one.
Because of this the carriers were re-measured directly rather than taken on the attestation: the
no_blend b1/b2 type layer (both `TypeError` messages verbatim), b6 re-entry
(`QuantityProvenanceMissing`), and numeric_default b1's runtime post-condition
(`AbsenceYieldedAValue`) — **all hold**.

### FINDING CD-ASR-WO2R-F11 — **MEDIUM** — a declared reader defect is declared for ONE guard and ABSENT from the two that share the reader
Egress boundary 9 (CD-D-062, the silent flattening) says in terms: *"the reader is shared with
`check_base_image_digest_pin.py` and `check_engine_no_witness_reach.py`, and this seat did NOT
sweep their subjects."* Grepping `flatten|CD-D-062|inline key|READER-F05` over the engine check,
its contract, its register entry and the digest-pin check returns **zero hits in all four**. The
engine check's subject is `deploy/compose.yaml`, which contains sequences of mappings, so the
defect can fire there. **A reader of those three places is not told the guard has a known reader
defect.** See NQ-2 for what I measured about it.

### CD-ASR-WO2R-F12 — **LOW** — the boundary COUNT contradicts itself in the load-bearing field
Register comment: *"in NINE numbered boundaries (1..8, 8b and 9)"*. The `negative_control` twenty
lines below: *"in EIGHT boundaries"* — then enumerates **ten**. `check_egress_no_broker.py:1275`
prints *"the EIGHT boundaries"* on every clean run (reproduced). Header and contract enumerate
**ten**. Three different counts of the same list, in the field that carries the obligation.

### CD-ASR-WO2R-F13 — **LOW** — dangling executable example, and a second CD-PL-F71 instance
The egress contract cites *"(variant `V-F04-04`)"*; `grep -rn V-F04-04` over the whole tree returns
**exactly that one line**. The real variant is `V21-innocent-host-broker-operator.patch`. Substance
true, citation unusable.
AND: the lockfile check's header calls the denylist *"a FLOOR and not an oracle ... rather than
letting a reader assume completeness"* (**a limit**), while the register and contract say *"a floor
and not an oracle, **so the class includes** an SDK nobody has heard of ... must fail as surely as
a named one"* (**a class-widening claim**). Same sentence, opposite work. My F05 measured which one
is true: it is the limit.

Minor, recorded not itemised: numeric_default contract cites `witness_resolver.py:168`, actual is
`:170`; no_execution_interface's guard-file exclusion is in the header and contract but absent from
the register; no_blend boundaries 3 and 5 drop the carrier from the numbered item.

## (a) EXECUTABLE EXAMPLES — re-run at 50fc231, reproduce EXACTLY
numeric_default b1 (AST exit 0, runtime `AbsenceYieldedAValue` verbatim) · b3 (exit 0 in
`publication/`, exit 1 in `dials/`) · no_exec_iface b3 (`must` -> 0, same sentence without `must`
-> 1) · egress b9 PL-X10a (`{'top': [{'key': None, 'sub': '1'}]}`) · egress b1 topology
(`test_both_networks_are_internal`, 1 passed). **Declared-uncarried residues confirmed REAL:**
no_blend b7 — `observed_for_dial(..., inputs_used=("fabricated",))` re-admits a blend and
`number_for_dial_slot` **publishes 0.5**; egress b5 — `extra_hosts: ["api.ibkr.com:198.51.100.24"]`
on cd-collectors is invisible to all four register guards AND the whole 83-test container suite.
Both are honestly declared and both are real.

---

# W8 — THE EIGHT NAMED QUESTIONS

**NQ-1 (is a STATIC-ONLY guard on the admission door sufficient for CD-AC-002?)**
**NO. MEASURED, NOT REASONED — and this is the answer CD-ASR-WO2R-F01 gives.** The Project Lead's
argument was that the residue is any registry's and that the layer denies by default rather than
recognising. That argument is sound *about the vocabulary it guards*. What it does not survive is
a PUBLIC FUNCTION THAT IS NOT IN THE VOCABULARY AND WALKS THROUGH THE DOOR FOR YOU.
`combine_within_one_dial` is exported in `crash_detector.dials.__all__`, is absent from
`ADMISSION_VOCABULARY`, and passes an arbitrary caller callable's return value unvalidated into
`derived_within_one_dial`. A static deny-by-default registry is only as closed as its vocabulary,
and a runtime check was not what was needed — a complete vocabulary was. **The gate was not the
Project Lead's to give, and on the measurement it should not have been given.**

**NQ-2 (the YAML reader's silent flattening — find the FOURTH route to a FALSE CLEAN)**
**I FOUND A FOURTH DIVERGENCE AND IT IS NOT A FALSE CLEAN. The guard refused it.**
I differentially parsed `_yamlmin.parse_block_yaml` against PyYAML and found a divergence the three
recorded probes do not cover: **`_yamlmin` splits a block-sequence scalar on ANY `:`, without
requiring the space that real YAML requires.**

    - api.ibkr.com:443      PyYAML / docker compose : ['api.ibkr.com:443']   (a STRING)
                            _yamlmin / the CHECK    : [{'api.ibkr.com': '443'}]  (a MAPPING)
    - https://api.ibkr.com  PyYAML                  : ['https://api.ibkr.com']
                            _yamlmin                : [{'https': '//api.ibkr.com'}]
    - api.ibkr.com          (control)               : identical in both. No divergence.

So a host written with a port or a scheme is a STRING to Docker and a MAPPING to the guard. I then
weaponised it — `hosts: [- api.ibkr.com:443]` on `cd-collectors`:

    CD-RT-012-EGRESS-NO-BROKER   EXIT 1
    VIOLATION deploy/compose.yaml:426
      rule: CD-EGRESS-004: an allowlist entry is not a scalar
      what: service `cd-collectors` declares an allowlist entry of type LocDict. An entry is the
            `host` of a registered destination, compared character for character; anything that is
            not a scalar cannot be that, and cannot be registered.

**DENY BY DEFAULT HELD.** The guard did not need to understand the divergence; it refused a
non-scalar because a non-scalar cannot be a registered host. **This is the strongest evidence in
the audit that deny-by-default is the right shape** — it refused an attack devised specifically
against its reader, for a reason that had nothing to do with the attack.
**WHAT I DID NOT ESTABLISH:** whether the same divergence produces a false clean in
`check_engine_no_witness_reach` or `check_base_image_digest_pin`, which share the reader and were
never swept (see F11). I probed the engine check obliquely — my compose `command:` in flow form
returned **exit 3 CD-ENGINE-ROOT-101, a loud refusal**, which is evidence that the engine check
also fails closed on what its reader cannot read. That is one probe, not a sweep. **The fourth
false-clean route was not found. I do not claim it does not exist.**

**NQ-3 (the reader refuses to convert RecursionError — limit or hole?)** **A LIMIT, and I agree
with CD-D-061.** A recursion depth exception is a property of the interpreter's stack, not of the
document, and converting it would have been the verdict change the reader dispatch forbade. It
fails LOUD and it fails CLOSED — which is the only property that matters for a guard. NOT a hole.

**NQ-4 (three tests declare `scope: CLASS` with no declared limit in the register)** **YES, IT
MISDESCRIBES THE GUARD, in the OVER-CLAIMING direction, on all three.** The three are exactly
`CD-RT-012-LOCKFILE-DENYLIST`, `CD-RT-003-GRANT-MATRIX-LIVE` and `CD-RT-002-SCHEMA-CLOSED` — and
note both of the two guards with **ZERO numbered boundaries** are in that set.
  * LOCKFILE-DENYLIST: **I MEASURED THE RESIDUE — see F05.** `tastytrade-sdk`, a real broker SDK,
    exits 0. So does `quietbridge`. `ib-insync` exits 1. The guard catches 61 named distributions
    plus an execution-token rule; a neutral-named broker SDK is neither, and **no place-text names
    a carrier for it.** The check prints its disclosure on every run; the register does not carry it.
  * GRANT-MATRIX-LIVE: the register hides that this command needs a LIVE PostgreSQL and five env
    vars (measured: exit 3 without them), a role that is "in practice the cluster superuser", and
    that **it APPLIES the subject tree's migrations to that database** — it is the only MUTATING
    command in the register. Its `execute:` line is visually indistinguishable from the eight
    offline static checks. A reader running the register top to bottom would be surprised.
  * SCHEMA-CLOSED: misdescribes by delegation — one sentence pointing at a schema description whose
    named carriers differ from the register's own and include a check demoted to INSTANCE for not
    carrying it (F07).

**NQ-5 (the eleven undelivered commands exit by interpreter convention, not exit 3)**
**CONFIRMED AT 50fc231 (9x exit 4, 2x exit 2) AND IT DOES MILDLY MISLEAD — but not dangerously.**
A reader who has learned this project's exit-3 = PRECONDITION_NOT_MET convention will read exit 4
and exit 2 as *defects of the harness* rather than *absence of the subject*. Every one names its
absent subject in its output, so the honest answer is one line away. LOW, and the existing
disposition (owed at WO-3) is right.

**NQ-6 (boundary 9 holds only because nothing in either contract may be None)**
**NO — the condition it names is NOT the only one that breaks it.** The reader's divergence is not
confined to null-valued nested keys. My NQ-2 measurement shows the SAME boundary is reached by a
plain scalar containing a colon, with no `None` and no nested block anywhere: `- api.ibkr.com:443`
becomes a mapping. So the boundary's stated precondition ("one optional field reopens it") is
narrower than the real precondition, which is closer to "any value whose text the reader tokenises
differently from YAML". The boundary understates itself. MEDIUM as a documentation defect;
the guard still refuses, so it is not an exposure.

**NQ-7 (the seat's F20-F24 and the PL's F53..F73)** **NOT RE-OPENED and NOT INHERITED.** I read
none of them as settled input to my own measurements: every conclusion in this verdict rests on an
arm I ran at 50fc231. Where my results touch theirs I have said so explicitly and by ID — CD-PL-F54
and PL-R2/PL-R5 under F01, CD-PL-F62/CD-D-055 under F09, CD-PL-F65/CD-D-058 under F02,
CD-PL-F71 under F09/F13, CD-PL-F66's denominator rule throughout, CD-PL-F73's V53 correction
(confirmed: 70 patches, so V53 is real and the "through V52" record was wrong by one).

**NQ-8 (an 892-line check rewrite at increment 4 added ZERO pytest tests — a real exposure?)**
**YES, A REAL BUT BOUNDED EXPOSURE, and my own work is the evidence.** The derivation is proved by
execution against fifteen durable variants and that IS stronger than a unit test — but W7 measured
the failure mode directly: **four corpus rows now carry stale line numbers because the artefacts
were edited after the rows were measured, and increment 6's re-run recorded only EXIT CODES, which
are invariant under the edit, so it structurally could not notice** (F04). That is exactly the
"silent regression only the check itself would witness" shape, occurring in miniature, in the
regression apparatus itself. The exposure is real. It is bounded because the derivation is
re-executed on every run and its 6 notes print the derived root set, the container set and the
shipped-file count on every clean run — a regression that shrank the graph would change those
printed numbers. **RECOMMENDATION (not a repair): assert the printed derivation summary, not just
the exit code.**

---

# THE VERDICT

    target        50fc23177f790164c3fc3604ccee51663e755c70   (verified: HEAD, tree object,
                                                              364 files, git status clean)
    OVERALL       RED
    confidence    HIGH on the two RED/HIGH findings — each is a positive demonstration by
                  execution with a control arm, re-run, and reproduced. MEDIUM on the
                  documentary findings. The negatives (what I could NOT break) carry only the
                  confidence of the routes I actually tried, and I state those denominators below.

    THE WO-2 GATE IS **NOT MET**, for the second time, on different grounds from the first.

## PER-CRITERION

**CD-AC-001 — Missing or stale input never renders as calm — AMBER. CLASS NOT FULLY CLOSED.**
Both declared tests CONTRAST correctly (0 -> 1; 100 assertions conserved; rule A, C and F all
named). The AST guard's Rule F is a genuine deny-by-default over provenance and it bit every
construction route I tried. **But `ASR2-001-A` renders an `Unknown` reading as `0.0` on the
DECLARED SCANNED PATH, through `fold`, using none of the enumerated spellings, and it is outside
all six declared boundaries — which are all about CONSTRUCTION, not CONSUMPTION** (F03, MEDIUM).
The guard closes the class of *numeric defaults being constructed*. It does not close the class of
*absence being answered with a number*. Evidence: `arms/`, `variants/ASR2-001-A-*.py.txt`.

**CD-AC-002 — The two dials are never blended — RED. THE CLASS IS NOT CLOSED.**
All three declared tests CONTRAST correctly. **And a live blend of equity 0.9 and monetary 0.1
publishes as an equity reading of 0.5, with `check_no_blend` PASS at 4873 assertions,
`check_schema_closed` PASS, `test_scores`/`test_dialset`/`test_dial_provenance` 306 passed, and the
whole 1325-test suite green** (F01, HIGH). The route is PUBLIC API — `combine_within_one_dial`,
exported in `__all__`, absent from `ADMISSION_VOCABULARY`, feeding an unvalidated value into
`derived_within_one_dial`. `src/crash_detector/dials/magnitude.py` boundary A states without
qualification: *"the sum cannot come back ... no number so obtained can ever be a dial magnitude
again."* **THAT IS THE CLAIM UNDER AUDIT AND IT IS FALSE.**
**WHY RED AND NOT AMBER, stated so it can be argued with:** boundary 7 enumerates its residues
EXHAUSTIVELY — a registry edit, a module outside the scanned set, a dynamically assembled name —
and my route is none of the three. This is not a declared gap; it is a positive claim refuted by
execution, and CD-D-040 accepted increment 2b on precisely the static carrier that fails here.
Contrast CD-AC-005, where the boundary HEDGED and I therefore graded AMBER. The distinction is
whether the deliverable claimed what it could not do.

**CD-AC-003 — Witnesses are side-by-side, never ingredients — PASS (scoped). CLASS CLOSED.**
**This is the strongest work in the deliverable and I could not break it.**
`CD-RT-003-ENGINE-NO-WITNESS-REACH` contrasts 0 -> 1. **`CD-RT-003-GRANT-MATRIX-LIVE` CONTRASTS
FOR THE FIRST TIME IN THIS PROJECT'S HISTORY: 0 -> 1, 138 assertions on both arms, 9 violations
across 6 independent catalogue routes including a live PostgreSQL session refusal.** The standing
risk CD-RT-002 is CLOSED (CD-D-020 discharged).
Two fresh attacks REFUSED: the compose `command:` override (caught, route named) and a full rename
of the witness package to `corroborators/` (tracked — the guard derives its subject from topology,
not from the string "witness", and prints its subject count so a vacuous pass is visible).
I verified the grant matrix MYSELF against the live catalogue, independent of the check: cd_engine
16/16 privilege probes false on schema witness; no role has SUPERUSER, BYPASSRLS, CREATEROLE, a
password or inheritance; zero memberships among the six roles; **no UPDATE/DELETE/TRUNCATE grant to
any project role anywhere**; one default ACL, INSERT+SELECT only.
SCOPE OF THIS PASS: the register's DESCRIPTION of this guard asserts a superseded, narrower
boundary text (F09, MEDIUM), and boundary 3's carrier sentence was unqualified and unmeasured until
this audit measured it (F06). Both are documentation defects on a sound guard, and both err toward
under-claiming, so neither creates false assurance.

**CD-AC-005 — WITNESS UNAVAILABLE is not WITNESS AGREES — AMBER. CLASS NOT CLOSED.**
The declared test CONTRASTS correctly (152 assertions conserved, 12 named failures). The
`FreshnessEvidence` design is genuinely good: the age comparison IS the act of constructing the
evidence, so a route that skips the comparison does not exist. There is no third comparison site —
I checked every `age_seconds`/`StalenessWindow`/`covers` use in the tree; both sites admit through
`StalenessWindow` and nothing else, exactly as claimed.
**But `ASR2-005-A` makes a decade-old row render `WITNESS AGREES`, through EVERY CONSTRUCTOR on the
path and with no `object.__setattr__` anywhere** (F02, HIGH). `StalenessWindow` refuses a `float`
subclass on exact type because "a subclass of a number is not a number: it may redefine what
comparison means" — and the SAME doctrine was never applied to the comparison's OTHER operand.
`ensure_utc` admits any `datetime` by `isinstance`. A `datetime` subclass controls the subtraction.
Control arm: the identical instant as a plain `datetime` correctly renders `WITNESS UNAVAILABLE`.
**AMBER and not RED because boundary 3 HEDGED HONESTLY**: "THREE MEASURED, and three is the
denominator, not a proof that a fourth does not exist." It named its own uncertainty and I found
the fourth. That is a declared limit doing its job, and it is why the grade differs from CD-AC-002.

**CD-AC-012 — No execution pathway exists — AMBER. CLASS NOT CLOSED ON THE DEPENDENCY SURFACE.**
All three declared tests CONTRAST correctly. The egress guard is the best deny-by-default artefact
here: it refused my `_yamlmin` reader attack for a reason unrelated to the attack (NQ-2), and the
execution-interface check's L2 caught a neutrally-named ticket on field shape alone.
**But `tastytrade-sdk` — a REAL, currently-operating brokerage's real order-entry SDK — exits 0 on
`CD-RT-012-LOCKFILE-DENYLIST`, which the register declares `scope: CLASS` and for which NO
place-text names a carrier** (F05, MEDIUM). Controls: `meridian-fix-connect` caught on the `fix`
token, so the token rule does generalise; `lattice-client` also escaped.
Also observed: an order ticket SPLIT across two types defeats L2's field-set rule and is named by
none of the six boundaries (LOW).
MITIGATION, measured not assumed: a dependency is permission to import, and the pathway needs
somewhere to go — the egress registry is EMPTY (0 registered destinations) and both networks are
`internal: true`. The product harm is contained; the register's description of the guard is not.

    CD-AC-001  AMBER  — class not fully closed (F03)
    CD-AC-002  RED    — class NOT closed; a documented claim refuted by execution (F01)
    CD-AC-003  PASS   — class closed; the live contrast finally exists
    CD-AC-005  AMBER  — class not closed, but the limit was honestly declared (F02)
    CD-AC-012  AMBER  — class not closed on the dependency surface (F05)
    ------------------------------------------------------------------------------
    OVERALL    RED     (the worst of them, as the dispatch specifies)

## WHAT WAS NOT EXAMINED, AND WHY
Stated here and not in a footnote (PBG-ASSURE-012).
* **48 of 70 corpus variants were apply-checked only, not executed.** Absence of mismatch in my 22
  is not evidence about the other 48.
* **The fourth `_yamlmin` FALSE-CLEAN route was NOT found.** I found a fourth DIVERGENCE and the
  guard refused it. I did not sweep `check_engine_no_witness_reach` or `check_base_image_digest_pin`
  for the reader defect; one oblique probe of the engine check failed loud. **This remains open and
  is the single most valuable thing a next audit could take.**
* **43 boundaries were assessed on (a)(b)(c); I re-ran executable examples for 9 of them.** The
  other 34 rest on textual comparison plus the W6 agent's reading.
* **No image was built, no container ran the application, no non-root or signal-handling proof was
  taken** — FORBIDDEN in WO-2 by PBG-RT-010 and correctly recorded as OWED. Judging them absent is
  right; judging them a defect of WO-2 would not be.
* **Out-of-scope items were not re-litigated:** CD-ASR-F07, CD-ENG-F39/F41, CD-PL-F43,
  CD-ASR-N01/N02, CD-ERR-001, CD-OB-004, CD-ENG-WO2R-F29/F30 and the CD-ENG-READER-F05/F08 FIX.
* **I did not verify the store under load, concurrency, or with RLS**, only the grant matrix.
* **My CD-AC-002 finding was demonstrated with a source edit.** Like every plant in this gate, it
  requires committing code. I do not claim a route from configuration or data alone.

## CONTROL BYPASSES AND FRAMEWORK LIMITATIONS OBSERVED
* **NO framework bypass found, and I tested for one.** `pbg required-tests verify` refuses to
  compute PASS from exit codes alone even when the run record is renamed to the id the register
  cites: `latest_admitted_run` is null and admission is a separate act. CD-RULE-001 is structurally
  enforced. This is the control that saved the first gate and it still holds.
* **The register grades nothing** — no status-like key exists anywhere in it. Confirmed by parse.
* **The variant corpus carries ZERO executable files** (all 73 mode 0664, no symlinks), so
  PBG-ASSURE-001 is satisfied in fact and not only by policy. Verified independently.
* **LIMITATION, not a bypass:** the tree-fingerprint method in the dispatch does not state its sort
  key, and `LC_ALL=C sort` over `sha256sum` output does not reproduce the recorded value even on an
  untouched tree. Recommend `sort -k2`.

## CONTINUATION IMPLICATION — stated separately from the findings
**What is true and what is safe to do next are different calculations.**
Nothing here is unsafe to LEAVE AS IT IS. There is no running deployment, no published envelope, no
egress destination registered, no image built, and the publication layer is WO-3. **The two HIGH
findings are latent structural defects, not live incidents.** Leaving 50fc231 in the repository
harms nobody.
What is NOT safe is **promoting this as the WO-2 baseline that WO-3 builds the publication layer
on**. CD-AC-002's route ends at `number_for_dial_slot` returning a blend, and WO-3's envelope
builder is the code that will call it. The defect is cheapest to close now, before there is a
builder to re-audit. Same for CD-AC-005: WO-3 delivers `window_for(regime)`, which will sit on top
of `FreshnessEvidence`.
**A PASS IS NOT AN ACCEPTANCE AND NEITHER IS THIS RED (PBG-AUTH-003).** I supply evidence and a
verdict. Disposition is the Product Owner's.

## NEXT SAFE GATE (PBG-ASSURE-004)
**A bounded WO-2R2 ENGINEER dispatch, scoped to CD-ASR-WO2R-F01 and F02 ONLY, returning to a THIRD
Assurance seat that is neither me nor CD-ASR-WO2-01.**
Its minimum proof obligation should be: every variant in the exclusion set, PLUS `ASR2-002-A` and
`ASR2-005-A` executed and shown REFUSED, PLUS at least two further fresh variants per finding by a
route in neither corpus. **It must NOT be scoped as "add `combine_within_one_dial` to
`ADMISSION_VOCABULARY`"** — that is the instance game, and it is the exact error the first gate
caught. The class question is: *can any public function reach a door the registry guards?* and,
for F02, *which other operands of which other comparisons admit subclasses by `isinstance`?*
The documentary findings (F05, F07, F09, F10, F11, F12, F13) are correction work, not logic work,
and should NOT be folded into the same dispatch — they belong with the CD-PL-F43 / CD-ASR-N01 /
CD-ENG-WO2R-F29 bundle already owed at WO-3.
**Do not re-run this gate until F01 and F02 are closed.** A third attempt that has not addressed
them would fail on the same evidence.

---
CD-ASR-WO2-02 · target 50fc23177f790164c3fc3604ccee51663e755c70 · read-only · nothing repaired ·
no acceptance granted · run record written, NOT admitted.

---
## APPENDIX — FINAL TARGET INTEGRITY, MEASURED ON RETURN

    HEAD    50fc23177f790164c3fc3604ccee51663e755c70
    status  0 lines
    files   364 non-.git regular files
    caches  0 __pycache__ / .pytest_cache

    $ awk '{print $1}' <PL manifest> | sort  vs  awk '{print $1}' <my manifest> | sort
    -> NO DIFFERENCE. ALL 364 FILE HASHES IDENTICAL. THE TREE IS UNMUTATED.

**THE MANIFEST FILES THEMSELVES DIFFER ONLY IN LINE ORDER, AND THIS IS A METHOD DEFECT IN THE
FINGERPRINT, NOT A MUTATION.** I could not reproduce
`50ae34d657126709c0e44b3a57c58c8308d25c1cb845aa70b30e86338a2d729d` by any sort I tried
(`LC_ALL=C sort`, `sort -k2`), because the recorded manifest orders `./.dockerignore`, `./PID.md`
and `./README.md` ahead of `./contracts/...` — an ordering that is NOT `LC_ALL=C`. The dispatch
describes the method as "the LC_ALL=C-sorted `sha256sum` manifest", and that description does not
reproduce the recorded value on a tree I have proved is unchanged.
**RECOMMENDATION (LOW): the CD-D-022 device should record the exact command, not a prose
description of it.** As written it will report a mutation that has not occurred, which is the worst
failure mode an integrity device can have — the next auditor would be accused of exactly what this
one was warned about.

SD-3 teardown verified: `docker ps -a --filter name=cd-asr-wo2r-` and
`docker volume ls --filter name=cd-asr-wo2r-` are BOTH EMPTY. 26 other containers on this host
were left untouched. Generated credential destroyed; its value appears in no artefact.
All 6 evidence variant artefacts are mode 0664 — `find -perm -u+x` over the evidence tree returns 0.

BOTH HIGH FINDINGS WERE RE-RUN FROM CLEAN EXTRACTIONS AS THE LAST ACT OF THIS AUDIT (F13) AND BOTH
REPRODUCED IDENTICALLY.
