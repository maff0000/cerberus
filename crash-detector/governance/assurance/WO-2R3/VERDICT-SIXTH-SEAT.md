# ASSURANCE VERDICT — WO-2R3, THE SIXTH SEAT

    actor_id            CD-ASR-WO2R3-03
    role                ASSURANCE_ENGINEER
    role contract       pbg/roles/assurance-engineer.md (read in full at the target)
    dispatch            governance/dispatch/CD-DISPATCH-WO2R3-ASSURANCE-06.yaml (ISSUED)
    dispatching auth    CD-AUTH-0001, PROJECT_LEAD_SEAT_01
    product authority   governance/decisions/PO-DECISIONS-0014.md ruling 2
    target SHA          af2accbfc950961bb7f7967d34ecf16414088228   (branch wo-2r3)
    target tree object  89196dacba1680fdc048fe6f84e45081ac4e738a
    target worktree     /srv/crash-detector-wo2r3-audit6 (detached)
    scope               THE WHOLE OF WO-2R3 — f30e63c..af2accb, increments 1-7

    FINGERPRINT AT START  66a1c27dadecaa0a891f9f2a2c28f89ed3ec8729eca2719fd49680e37c5e4ecd
                          472 files fingerprinted · 0 excluded by .gitignore · porcelain 0 lines
    FINGERPRINT AT END    66a1c27dadecaa0a891f9f2a2c28f89ed3ec8729eca2719fd49680e37c5e4ecd
                          472 files fingerprinted · 0 excluded by .gitignore · porcelain 0 lines
                          HEAD af2accb… and tree object 89196da… identical at both moments.
                          **AND SEE F-06-E: THIS VALUE IS NOT AN IDENTITY. I BROKE IT.**

    INDEPENDENCE          I am none of CD-ENG-WO2R3-01/-02/-03 and none of CD-ASR-WO2-01,
                          CD-ASR-WO2-02, CD-ASR-WO2R2-01, CD-ASR-WO2R3-01, CD-ASR-WO2R3-02.
                          I did not write, review, advise on or dispatch any part of the
                          target. PBG-SOD-001 satisfied.

    METHOD                Every experiment ran in a throwaway `git archive` extraction under
                          /tmp. No commit, no edit, no `git apply` in the audit worktree. Every
                          probe ran its own tree's copy and its `tree:` line was read (CD-PL-F98).
                          **EVERY THROWAWAY RESULT IS LABELLED AS ONE IN THE SAME PARAGRAPH.**

---

# VERDICT: **RED**

    T2  (CD-BP-003, the adapter boundary that admits)     RED               (was RED)
    CD-AC-002                                              AMBER, NOT CLOSED (unchanged)
    CD-AC-005                                              AMBER, NOT CLOSED (unchanged grade,
                                                           reasoning weaker again — see §5)

**Confidence: HIGH** on all three grounds. Each was measured by me, with a control arm, in a
throwaway extraction, with provenance read every time.

**MY VERDICT IS NOT AN ACCEPTANCE (PBG-AUTH-003).** I grade; the Product Owner dispositions.

**AND THE THING I WANT READ BEFORE THE FINDINGS.** Increment 7 is the most self-critical
increment in this record. Its Engineer raised six findings against its own work; two of them
(F06, F13) caught false evidence *before it shipped*, and F13 would otherwise have headlined
"43 live bypasses" against a true answer of zero. The NETS population is real engineering:
four substantive assertions, set equality in both directions, and I broke it deliberately and
it held. **THE RED IS NOT ABOUT DILIGENCE.** It is about one criterion whose answer is false,
one measurement taken in the only state where it says "no", and one escape nobody closed.

---

## §0 BOOT VERDICT AND TARGET RECONCILIATION

`cd /srv/crash-detector-wo2r3-audit6 && PYTHONPATH=pbg/tools python3 -B -m pbg.cli boot`
→ **EXIT 2, verdict RED, `CONTINUITY_REFERENCE_INVALID/RESUME_BLOCKED`.**

Observed reconciles against the dispatch **exactly** on SHA, tree object, fingerprint, file
count, exclusion count and porcelain (table in the header block above).

**On disclosure 5 I agree the lane-boot RED is an artefact and I spent no budget on it. I
DISAGREE WITH ITS SCOPE — see F-06-C.**

**Baseline instruments, re-measured by me at the target (CD-RULE-009 — measured, not copied):**

| instrument | result | agrees with dispatch? |
|---|---|---|
| `tools/register/check_judgement_path_doors.py` | **EXIT 0** · PASS — 60 assertions, 0 violations | yes |
| `tools/sweep/delegated_judgement_sweep.py` | **EXIT 1** · FAIL — 534 sites, 15 violations | yes |
| `pytest -q` | **1580 passed** | yes |
| `hasattr(_evaluate_dial, "__wrapped__")` | **False** | yes |
| `tools/register/check_no_blend.py` | EXIT 0 · PASS — 7161 assertions | not stated |
| **`tools/register/check_no_execution_interface.py`** | **EXIT 1 · FAIL — 1 violation** | **NO — see F-06-A** |

**Every headline figure in the dispatch reproduces. One that is not in the dispatch does not.**

---

# §1 THE THREE GROUNDS OF THE RED

## GROUND 1 — THE REACHABILITY CRITERION DOES NOT MEASURE REACHABILITY (T14)

### 1.1 Why the rename pair is not a proof

`PO-DECISIONS-0012` ruling 2 corrected door membership "from NAME-PREFIX (a vocabulary) to
REACHABILITY". The increment offers a rename PAIR:

* **Arm 1** — rename the LOCAL (`guarded` → `_guarded`): verdict UNCHANGED.
* **Arm 2** — rename the DESTINATION (`_evaluate_dial` → `evaluate_dial`): verdict FLIPS.

**ARM 2 IS NOT EVIDENCE OF SOUNDNESS. IT IS THE FAILURE SIGNATURE THE OLD CLAUSE WAS
CONDEMNED FOR, MOVED ONE FRAME OUT.** The only thing that changed in arm 2 is a leading
underscore. `_reachable_public_binding` follows the local's escape routes and then, on
arrival at the destination module-level name, asks exactly one question — `_is_public(name)`.
**It never applies its own escape-route analysis to the destination. The recursion terminates
in the vocabulary test ruling 2 exists to remove.**

### 1.2 THE THIRD ARM — MEASURED

**ALL THREE ARMS BELOW ARE THROWAWAY EXTRACTIONS (`/tmp/a6-arm3{a,b,c}`) AND NONE IS THE
TARGET'S STATE. THE TARGET'S OWN STATE IS EXIT 0, PASS — 60 assertions, 0 violations.**

| arm | the ONE line appended to `engine/evaluate.py` | doors check |
|---|---|---|
| **3a** | `evaluate_dial = _evaluate_dial` — a PUBLIC module-level alias | **PASS — 60 assertions, 0 violations. UNMOVED.** |
| **3b** | `PUBLIC_EVALUATORS = {"dial": _evaluate_dial}` — a PUBLIC container | **PASS — 60 assertions, 0 violations. UNMOVED.** |
| **3c** (control, CD-D-079) | rename `_evaluate_dial` → `evaluate_dial` | **FAIL — 3 violation(s)** |

**And the reachability in 3a/3b is REAL, proved at RUNTIME, not asserted:**

```
tree: /tmp/a6-arm3a/src/crash_detector/engine/evaluate.py
route : module.evaluate_dial  — a PUBLIC module-level name
obtained: <function _evaluate_dial at 0x7f6754a5f420>
is it the NET?  __qualname__ = _evaluate_dial   closure cells = 1
undecorated evaluator reachable through it: True
is it the SAME object as module._evaluate_dial? True

tree: /tmp/a6-arm3b/src/crash_detector/engine/evaluate.py
route : module.PUBLIC_EVALUATORS["dial"] — a PUBLIC container
   (identical results)
```

**THE ASYMMETRY IS THE FINDING.** The criterion **moves** when a name gains or loses an
underscore, and **does not move** when the identical object is bound to a public module-level
name or stored in a public module-level container — both of which make it genuinely,
runtime-provably obtainable from outside the module. **A criterion that tracks the underscore
and not the binding is a vocabulary.**

Arm 3b is additionally the fourth seat's **ESCAPE 4 ARM 4 shape** (a subscript store) — the
increment's own required contrast. The clause catches it at the function-local level and is
**blind to it one level out, at the destination.**

### 1.3 Why this matters although the shipped tree is clean

At `af2accb` no such alias exists and `guarded` is correctly registered as a NET with all four
`declared_nets.py` assertions live. **THE SHIPPED TREE IS NOT DEFECTIVE HERE. THE CONTROL IS.**
`check_judgement_path_doors.py` is a **regression** instrument — its entire job is to catch a
future edit. A one-line future edit (publishing an evaluator registry; adding a public alias
for testability) makes the CD-ASR-F03 net reachable **and the control stays green**. That is
`GUARD_THE_INSTANCE_NOT_THE_CLASS`, and it is `CD-ENG-WO2R3-03-F06`'s shape for the third
time: ruling 2's own defect reintroduced inside the fix for it — one file away at F06, one
**frame** away here.

**And it converges with F-06-K:** `_module_bindings` — the function this clause reasons over —
is one of the three `for node in tree.body` sites **increment 7 ADDED**. So the destination
analysis is blind twice over: it will not see a public alias, and it will not see one written
inside any `if`/`try`/`with`/`for` block at module level either.

### 1.4 WHAT THE OLD CRITERION CAUGHT THAT THE NEW ONE DOES NOT — ENUMERATED

The dispatch names this "the largest single hole in the reconciliation you are inheriting". I
enumerated it by driving the shipped instrument's **own** internals over the shipped source, so
the enumeration cannot disagree with the instrument (`/tmp/a6-attack/enumerate_old_vs_new.py`):

```
tree: /tmp/a6-base/tools/register/check_judgement_path_doors.py
FUNCTION-LOCAL CALLABLES UNDER src/: 6   (1 inside a RULE 1 judgement-path package)

OLD CAUGHT / NEW DOES NOT
  engine/evaluate.py:342  _absence_is_never_a_number.guarded
      on a RULE 1 judgement path: True   -> NETS deny-by-default APPLIES
  publication/envelope_contract.py:440  _preferred_error.sort_key
      on a RULE 1 judgement path: False  -> NETS deny-by-default DOES NOT APPLY
      reason: "...it IS passed to ['min'], which this clause does NOT treat as an escape"

NEW CATCHES / OLD DID NOT
  establishment.py:464  establishes.apply_at_the_boundary.__init__
      reason: STORED UNDER 'cls' — the fourth seat's ESCAPE 4 ARM 4 shape

SUMMARY: removed=2  added=1  invisible-to-both=0  subject-under-both=3
```

**VACUITY CHECK: THE CRITERION IS NOT VACUOUS.** It answers "reachable" for 4 of 6 and the
added row is a real catch. I record that as a measured result in the increment's favour.

**A correction I owe the record, also in the increment's favour.** Build-log 0075 says the
reclassification "changes exactly one verdict". Across the whole population the *membership
answer* changes for three — but only `guarded` is inside the check's RULE 1/RULE 2 subject
scope, so **the check's verdict does change for exactly one and 0075 is accurate as written.**
I checked it because this project has been wrong about sentences of that shape before. It is
right this time.

**What genuinely leaves with `guarded`:** `_preferred_error.sort_key` — public-named, declared
UNREACHABLE via the `PASSED_TO` weakening, and **off a judgement path, so the NETS backstop
does not cover it.** It is out of scope today only because `publication/` is not a RULE 1
package. **If `publication/` is ever added — and it is the publication path — this callable
becomes silently NET-eligible rather than a door and the `PASSED_TO` hole becomes
load-bearing.** That is on nobody's list (F-06-S).

### 1.5 THE DECLARED WEAKENING (`PASSED_TO`) — GRADED

**GRADE: ACCEPTABLE AS DECLARED ON A JUDGEMENT PATH; NOT ACCEPTABLE AS A GENERAL CRITERION.
THE DECLARATION IS ACCURATE ABOUT WHAT IT LOSES.**

The Project Lead declared it did not test whether the declaration is *accurate*. I did. The
Engineer's stated cost — *"a callee that STORES the object is now invisible"* — is true, and
its stated bound is also true: on a RULE 1 judgement path the NETS population denies by
default and such a callable fails `UNCLASSIFIED_INTERCEPTOR` unless declared. I read
`declared_nets.py` and confirmed the backstop is asserted **in both directions** with four
substantive assertions — existence, module-level resolvability, **that the body actually calls
the post-condition**, and that the post-condition is itself an `admits` door. That is real and
I say so.

**The Project Lead's own question** — *is a declared weakening inside the fix for a
defect-class the same defect-class one generation on?* — **NO for `PASSED_TO`; YES for the
clause that contains it.** `PASSED_TO`-tagged-and-not-acted-on is a hole with a name, a
measured reason, a stated cost and a backstop. **But §1.2 shows the surrounding criterion is a
vocabulary, and that is a larger finding than the weakening I was pointed at.**

---

## GROUND 2 — THE ITEM-1 STOP CONDITION WAS MET AND DID NOT FIRE

### 2.1 The condition, verbatim from `CD-DISPATCH-WO2R3-INC7-ENGINEER`

> *"If reachable without an established door, 0012 ruling 1 falls and `guarded` becomes a door
> with a redesigned CD-ASR-F03 control."* **IF YOUR MEASUREMENT LANDS THAT WAY: STOP. DO NOT
> PROCEED TO ITEM 2.**

The Engineer measured half (a) as **"NO — not within the settled threat model"** and proceeded.
Its decisive arm was a conforming hostile adapter through `collect()` (P-G), reporting
`_evaluate_dial reached: False`. The Project Lead re-ran that same probe and recorded the
result as an **attribution, not a confirmation**. **I am the third reading and the first
independent one.**

To the Engineer's credit, it refused to rule: *"'I could not construct the reach' and 'the
reach does not exist' are different sentences and only the first one is evidence."* **It was
right, and this section is the second sentence.**

### 2.2 P-G reproduced unmodified (throwaway extraction `/tmp/a6-base`)

```
tree: /tmp/a6-base/src/crash_detector/collectors/runner.py
crash_detector.engine.evaluate in sys.modules BEFORE collect(): False
  R1 sys.modules   ... IS NOT IN sys.modules at the moment collect() calls the adapter
  R2 frame walk    frames walked: 7; _evaluate_dial reached: False
crash_detector.engine.evaluate in sys.modules AFTER collect():  True
```

Exactly as disclosed. **R1 and R2 are measurements of ONE INSTANT — the instant `fetch` is
entered, the earliest moment in the adapter's life.**

### 2.3 FINDING: P-G'S CLOSING LINE IS SELF-INFLICTED

Disclosure 3 calls `... AFTER collect(): True` *"the interesting one and nobody has attacked
it"*. **It is an artefact of P-G's own Route 3**, which calls `importlib.import_module(TARGET)`
inside `fetch`. Arm A of `/tmp/a6-attack/P-K-the-adapter-that-waits.py` is P-G's structure with
Route 3 deleted and nothing else changed (**throwaway extraction**):

```
ARM A — P-G's structure with ROUTE 3 (the explicit import) DELETED.
  R1 sys.modules   crash_detector.engine.evaluate in sys.modules at fetch(): False
  crash_detector.engine.evaluate in sys.modules AFTER collect(), WITH NO ROUTE 3: False
```

**The collection path never imports the engine. P-G put it there.** The lead the record has
carried as unexamined is a measurement defect, not a signal. **This is `CD-ENG-WO2R3-F12` —
the project's most-repeated measurement defect — in the gate-deciding probe itself, and the
third instance inside increment 7 after F09 and F15.**

### 2.4 FINDING: A CONFORMING FOREIGN ADAPTER *DOES* OBTAIN AND CALL THE NET

R1 is not a property of the adapter. **It is a property of the clock.** An adapter is not a
function call; it is a **live object the host hands to foreign code**, and nothing obliges that
code to act at the instant it is entered.

`/tmp/a6-attack/P-L-the-second-cycle.py` uses **P-G's Route 1 verbatim and nothing else** —
`sys.modules.get(TARGET)` inside `fetch`. No `importlib`. No import statement. No frame walk.
**No threads.** The only difference from P-G is that the host polls **twice**, with one
ordinary evaluation between — which is a collector's entire reason to exist.
**THROWAWAY EXTRACTION:**

```
tree: /tmp/a6-base/src/crash_detector/collectors/runner.py
crash_detector.engine.evaluate in sys.modules at process start: False

>>> CYCLE 1 — this is the state P-G measured, and the only state it measured.
>>> THE HOST EVALUATES. Public API only. This is the product doing its job.
    host evaluate() -> DialSet
>>> CYCLE 2 — the next scheduled collection. NOTHING about the adapter changed.

LOG:
  cycle 1: crash_detector.engine.evaluate NOT in sys.modules — nothing reached
  cycle 2: crash_detector.engine.evaluate IS in sys.modules; _evaluate_dial obtained: True
  cycle 2: CALLED THE NET — returned Unknown
  cycle 2: UNDECORATED evaluator via __closure__: True
  cycle 2: net is und? False — the post-condition IS bypassable through this object
```

**A declared-foreign, protocol-conforming `SourceAdapter`, arriving through the door the system
advertises, OBTAINED `_evaluate_dial`, CALLED IT, and reached the UNDECORATED evaluator through
its own `__closure__` — passing no established door.**

### 2.5 Why this is inside the threat model, stated so it can be attacked back

`PO-DECISIONS-0012` ruling 4 puts **arbitrary code execution** outside the threat model. P-G's
Route 3 (`importlib`) is that, and **I did not use it**. **Route 1 is the route the Engineer
itself measured as the decisive IN-MODEL arm and reported as the negative the increment
proceeded on.** If reading `sys.modules` is in-model at second 0 it is in-model at second 1.
**The clock is not a security boundary.**

The one step a reader may challenge is that the host imports the engine between cycles. It does
so by calling `crash_detector.engine.evaluate` — **the product's own public entry point, from
`main`, not from the adapter.** `crash_detector/engine/__init__.py:20` imports the `evaluate`
module, so any host that evaluates has it loaded. **If a host calling its own public evaluation
API counts as "handing the net over", then the net was never unreachable in any deployment that
both collects and evaluates — which is every deployment this product has.** I state it this
plainly so the Product Owner weighs the step directly rather than taking my framing.

### 2.6 And ruling 1's own sentence is false in its load-bearing half

> *"`guarded` is a function-local binding, never importable, reachable only through doors that
> already establish."*

`never importable` was already found false of the object by the Engineer (its F01), and the
ruling survived because the object is reachable under the name `_evaluate_dial`. **The second
half — *"reachable only through doors that already establish"* — is what I have falsified, and
it is the half the ruling rests on.** My adapter passed no door.

**CONSEQUENCE, STATED AND NOT APPLIED.** By the increment's own dispatch this is the
`STOPPED_AT_ITEM_1` outcome. **I do not rule on it (PBG-AUTH-003).** Whether ruling 1 falls is
the Product Owner's, and I note the Engineer was explicitly forbidden to decide it too.

---

## GROUND 3 — ESCAPE 3 IS LIVE, UNMOVED AND UNDECLARED AT `af2accb` (T2)

The dispatch ordered "REPRODUCE IT OR REFUTE IT — DO NOT INHERIT IT." **Reproduced in full, at
`af2accb`, with control arms, in a throwaway extraction, from a harness written from the
target's source — no pre-existing probe was used as a measurement.**

Ordering confirmed by AST and runtime object identity (`inspect` is defeated here by the
`@admits` wrapper, so identity was used):

```
AST: collect defined at line 339
AST: _record(...) call sites INSIDE a `finally:` body -> [580]
AST: _reading_key(...) call sites in collect          -> [606]
IDENTITY: OK handed to sink / OK on CollectionResult  -> SAME OBJECT: True
IDENTITY: normal setattr refused by  : FrozenInstanceError
IDENTITY: object.__setattr__ bypass  : succeeds
```

```
----- CONTROL (benign sink) -----
  returned payload: {'reading': 0.25}   reading_key: ('src.h','2026-08-22T11:59:59Z')
  reading_admitted: True                ledger asked for: [('src.h','2026-08-22T11:59:59Z')]

----- ESCAPE 3 (sink does object.__setattr__ on the OK it was handed) -----
  sink saw        : [('OK', {'reading': 0.25}, '2026-08-22T11:59:59+00:00')]
  returned payload: {'reading': 999.0}
  returned as_of  : 2000-01-01T00:00:00+00:00
  reading_key     : ('src.h', '2000-01-01T00:00:00Z')
  reading_admitted: True
  ledger asked for: [('src.h', '2000-01-01T00:00:00Z')]
```

The ledger is asked for a key naming a period **no row records** and answers `admitted`. The
sink returns `None` throughout, so `_record`'s contract check is satisfied and nothing refuses.

**ARM5 reproduces:** stored payload `{'reading': 999.0, 'smuggled': 'never validated'}` fails
the schema it was judged by (`JSONSCHEMA_ADDITIONALPROPERTIES at <root>`), while the sanity arm
confirms the original `{'reading': 0.25}` **passes** the same schema — so the failure is caused
by the rewrite, not by a bad schema.

**Second half reproduces, with one correction in the project's favour:**

```
  bad schema + benign sink          -> CAUGHT by `except SchemaDeclarationInvalid`
  bad schema + value-returning sink -> NOT caught; escaped as SinkContractBreach
       __context__ of the replacement: SchemaDeclarationInvalid (still reachable: True)
  happy path + value-returning sink -> SinkContractBreach   [control: the arm is honest]
```

The original is **not annihilated** — implicit chaining preserves it on `__context__`. It is no
longer catchable **by type**, which is the handler the code's own docstring tells an operator to
write. The prior record's "replaces" is slightly stronger than the truth; the operational
consequence stands.

**THE DECLARED-LIMIT GAP IS REAL (T12):**

* DECLARED LIMIT 5 (`runner.py:486-533`) names four residues — non-exact container by
  reference, below `PAYLOAD_SNAPSHOT_MAX_DEPTH`, the `FetchedResponse` door defeated, and **the
  VALIDATOR**. The word `sink` **does not occur in it**. All three CD-RULE-004 copies
  (`runner.py`, `required-tests.yaml:1255-1285`,
  `contracts/execution/CD-RT-002-DOORS-REQUIRE-THEIR-TYPES.md:315-338`) are short the same way.
  **There are FOUR foreign protocols at that door and the residue list names one.**
* Where the sink *is* named (DECLARED LIMIT 3) the declared residue is a **non-write**. It does
  not contemplate the sink mutating what it was handed.
* The promised "sink/ledger/validator table" **does not exist anywhere in the tree.**
* **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.** Two sink-focused tests exist, both about
  raising and returning; a grep for a sink test involving mutate/rewrite/setattr/frozen/tamper
  returns **NONE**; `tests/collector_fakes.py` has `RecordingSink` and `ExplodingSink` and **no
  hostile sink exists**. `pytest tests/test_collector_runner.py tests/test_collector_admission.py`
  → **81 passed. The tree is green while the escape stands.**

**And it could not have been otherwise:**

```
commits 9f7b764..af2accb touching src/crash_detector/collectors/ : (none)
tree hash 9f7b764:src/crash_detector/collectors = 56b0459bcc9616d844fba81e30ac75545564211a
tree hash af2accb:src/crash_detector/collectors = 56b0459bcc9616d844fba81e30ac75545564211a
all of src/ changed in the range: admission.py (+75/-1), engine/evaluate.py (+42)
```

**T2 = RED. The ground of the standing RED was not removed and is still named nowhere.**

---

# §2 VERDICT ON EACH NAMED TARGET, T1-T17

| | target | verdict |
|---|---|---|
| **T1** | P7 — a new field arrives REFUSED | **PASS** — re-measured, not inherited |
| **T2** | CD-BP-003 adapter boundary | **RED** — Escape 3 reproduced (Ground 3) |
| **T3** | the §D scoping / CD-D-105 standing invitation | **ATTACKED ON MEASURED GROUNDS — first time in four gates. See F-06-J** |
| **T4** | the instruments' enumeration and traversal | **RED** — residual NOT closed; increment 7 net **+2** `tree.body` sites (F-06-K) |
| **T5** | the class-2 sweep exiting 1 | **DECLARATION ACCURATE. NOT A PARKED DEFECT. BUT THE COUNT IS STALE (F-06-I)** |
| **T6** | GRANT-MATRIX-LIVE / the bitten standard | **AMBER** — correction re-measured and HOLDS; new fact: a live Postgres exists (F-06-O) |
| **T7** | the `variants/WO-2R` routes | **AMBER** — 3 arms prove nothing (F-06-N); one route improved; two openly OPEN |
| **T8** | the eleven class-2 items | **MEASURED. I AGREE ON A AND B; I DISAGREE ON C — ALL SIX LAND (F-06-R)** |
| **T9** | CD-ENG-WO2R3-F15, the blindness window | **SWEEP RUN — it was unrun by everyone. One hard instance (F-06-F)** |
| **T10** | CD-ENG-WO2R3-F10 (`admits.door` invisible) | **STILL OPEN AND UNDISCHARGED** — confirmed at af2accb |
| **T11** | the widened class / widened traversal | **the traversal STILL does not survive intact** (T4); no new attack on the widened class |
| **T12** | the seven repairs of increment 6 | **residue still short by the SINK** — confirmed; increment 7 did not touch the file |
| **T13** | the plant set | **RED** — 12 plants, 10 evidence, **2 decoration**; `MANIFEST.md:96` false (F-06-L) |
| **T14** | **the reclassification and its weakening** | **RED — THE GREEN ROW IS NOT EARNED AS REASONED (Ground 1)** |
| **T15** | the three new instruments incl. the fingerprint | **AMBER→RED on the fingerprint — IT IS NOT INJECTIVE (F-06-E)** |
| **T16** | the vocabulary as a register contract | **A CONTRACT FOR SIX WORDS, A PLACEHOLDER FOR TWO** — measured both ways |
| **T17** | the `*extra` residue and its carrier | **A TRIPWIRE EXISTS AND THE RECORD SAYS IT DOES NOT (F-06-P)** |

### T1 — **PASS**
Four governed types, each in its own throwaway tree, provenance printed. Adding one field to
`Empty`, `DialSet` or `Contribution` gives `establishment_faults` 1 and **REFUSES every
ordinary construction** with `crash_detector.establishment.UndeclaredField: … is a FAULTED type
and every construction of it is refused`. Counterfactual on the base tree:
`Empty(confidence=object())` → CPython's `TypeError`, i.e. before the field exists the refusal
is the interpreter's; **the mechanism is what changes when the field lands.** V39 → check exit
1 `FIELD_NOT_DECLARED_TO_ESTABLISHES`; **V39+V41 violated arm → faults 0, "the new field
arrived UNGUARDED"**. The contrast is real.

### T5 — declaration accurate, but the *count* is not
Sweep EXIT 1, 534 sites, 15 violations, matching the bisect. The declaration is not parking a
defect. **But see F-06-I: the governance vocabulary says "the eleven" and the instrument has
printed 15 at every run since `66d1d6a`.** The fifth seat's *"DECLARING IS NOT READING"* is
right and I would add a second clause: **NAMING IS NOT COUNTING.**

### T8 — my own reading of the eleven
* **Category A — I AGREE, and I add the negative nobody had.** Reproduced with a two-arm
  contrast: control refuses `UndeclaredParameter: f0 is a FAULTED door and every call to it is
  refused`; after one assignment `f1.__qualname__ = "Faked.f1"`, `admission_faults == ()` and
  the body runs with an unestablished first argument. **IS IT REACHABLE FROM `collect()`?
  NO, AND I BUILT THE CHAIN THAT SHOWS WHY.** The site has exactly one call site
  (`_signature_parameters`), itself called only from `admits.apply_at_the_boundary` — a
  **decoration-time** site, never consulted on a call. Instrumented `collect()` runs hit it
  **0 times**. Pushed to the end: a hostile adapter installing a Category-A door over
  `runner.seconds_since` produces **an outcome identical to installing a bare `lambda`**
  (arm 2 ≡ arm 3). **Category A buys a runtime attacker nothing.** *That is a negative result
  and it is the answer to a question three gates have carried unanswered.*
  **BUT ITS SOURCE-LEVEL REACH IS WORSE THAN THE RECORD STATES:** the same door written in
  `staleness.py` (not a RULE 1 package) is **invisible to all four instruments** — doors PASS
  60/0 exit 0, sweep 534/15 exit 1, constructor exit 0, suite 1580 passed — **byte-identical
  output to the pristine tree.**
* **Category B — I AGREE, by my own AST enumeration and not by inheriting the assertion.**
  Every `.py` under `src/`, `tools/`, `tests/` walked for `ImportFrom` (incl. `asname`), `Call`
  by `Name` and `Attribute`, bare references, and **string literals** equal to the names or to
  `__admits__`/`__admission_faults__` (the `getattr` route). **Callers under `src/`: NONE.**
  The ten `declared_admissions` hits in the sweep are a local identifier of the tool, not the
  function — checked, not assumed. I would sharpen the wording: these three are a **documented
  reviewer-facing surface that lies by construction**, not an unused function.
* **Category C — I DISAGREE WITH THE FIFTH SEAT. ALL SIX LAND, AND I VERIFIED IT MYSELF.**
  See F-06-R. The narrow claim ("no caller-controlled route") is correct; **it is the wrong
  test**, and `OUT_OF_BOUND ×6` records the weaker half of the fact.
* **THE ELEVEN/FOUR SPLIT — NOT A DIFFERENT KIND.** See F-06-I. The four are the same shape,
  in the closure for the identical reason, with word-for-word identical violation text. And
  **establishment site 3 (`getattr(self, name, _ABSENT)`) is arguably worse than Category A**:
  it runs on **every construction of every governed type** and `getattr` on a subclass executes
  a property — caller code — at the moment establishment is claimed. Measured: a
  `Lying(PanelRow)` whose `state` property is honest on its first read only is **CONSTRUCTED,
  the boundary raises nothing**, and every later reader gets `'AGREES'`. Honest bound, also
  measured: `resolve_panel` then refuses it at the `@admits` door — **so the establishment
  boundary's claim is carried by a different mechanism, only where a door happens to stand.**
* **`declared_dispositions.py` contains NOT ONE of the eleven** — verified independently by me,
  and the blob is **byte-identical** at `9f7b764` and `af2accb` (`9f71b7cc…`), untouched since
  increment 1. **The separation held.**

### T16 — measured in both directions, all arms in a throwaway extraction
| injection | result |
|---|---|
| a bogus disposition word | **CAUGHT** — `UNKNOWN_DISPOSITION`, 15 → 16 violations |
| `CARRIER_ONLY` for `ensure_utc` (which IS called under `src/`) | **CAUGHT** — `CARRIER_ONLY_HAS_A_PRODUCT_CALLER` |
| control: `CARRIER_ONLY` for a name nothing calls | **ACCEPTED**, 15 unchanged — the check discriminates, it is not vacuous |
| `DEFECT_OPEN` with prose where the evidence mapping belongs | **CAUGHT** — `DISPOSITION_EVIDENCE_MISSING` |
| **`DEFECT_OPEN` well-formed with `finding: "CD-TOTALLY-MADE-UP-999"`** | **ACCEPTED**, 15 unchanged |
| **an original word substantively false (`ESTABLISHED` for `OUT_OF_BOUND`)** | **ACCEPTED**, 15 unchanged |

**ANSWER TO THE QUESTION AS ASKED: IT IS A CONTRACT FOR SIX WORDS AND A PLACEHOLDER FOR TWO.**
The five original words plus `CARRIER_ONLY` are enforced — and `CARRIER_ONLY` is enforced on
its *truth*, which is the only word in the vocabulary that is. `DEFECT_OPEN.finding` resolves
against nothing and a fictional id passes. `UPSTREAM_OF_THE_PATH`'s two fields are prose. **The
vocabulary cannot express its eleventh item today, and the Product Owner has already ruled
that the word is rejected as drafted — so the shipped contract at `af2accb` contains a word its
Product Authority has since rejected.** That is not the Engineer's fault (the rejection is
later than the increment and the printed table marks all three `PO RATIFICATION PENDING`); it
is the state of the tree I am grading.

### T17 — **and the record is wrong in the pessimistic direction**
See F-06-P. The Engineer's *"There is no carrier for that day"* is **false**.
`tests/test_engine_model_registry.py:830::test_p8_the_enum_ships_exactly_one_member_and_it_is_the_refusing_one`
asserts `list(MappingKind) == [MappingKind.UNSPECIFIED]` and its docstring says in terms it is
*"the tripwire that makes such an addition visible instead of quiet."* **The day arrives
loudly.** What does not exist is the **link**: the tripwire fires and says "a second member is
a PRODUCT decision"; it does **not** say "re-run the `*extra` guard measurement". And the
BLUEPRINT §16 entry ordered by ruling 3 **is on `main`, not at my target.**
**IS A DOCUMENTARY ENTRY ON AN OWED LIST A CARRIER? NO — but this project has a real tripwire
it did not know it had, and joining the two is one sentence in an existing failure message.**

---

# §3 FINDINGS ON NOBODY'S LIST

## **F-06-A — HIGH. A GOVERNED REGISTER REGRESSED FROM EXIT 0 TO EXIT 1 INSIDE INCREMENT 7, AND MY OWN DISPATCH'S CLAUSE (i) SAYS IT DID NOT.**

My dispatch states, carrying `PO-DECISIONS-0009` ruling 1: *"a governed instrument in this tree
EXITS NON-ZERO BY DECLARED STATE … At the fifth gate there were TWO such instruments. **THERE
IS NOW ONE**."* **THERE ARE TWO. MEASURED BY ME, AND BISECTED:**

```
at 9f7b764 : CD-RT-012-NO-EXECUTION-INTERFACE: PASS — 53663 assertions, 0 violations   EXIT 0
at af2accb : CD-RT-012-NO-EXECUTION-INTERFACE: FAIL — 1 violation(s)                    EXIT 1
   VIOLATION  tests/test_tree_fingerprint.py:61
       rule: execution interface declared in prose (docstring or string literal)
```

The violating file is **created by increment 7 item 6** — the CD-PL-F100 fingerprint fix. It is
an **L3 prose false positive**: the test's docstring contains *"the dispatch ORDERS the auditor
to do"* and L3 reads `orders` in the active voice.

**WHY THIS IS HIGH AND NOT LOW.** The product has no execution interface and I am not claiming
one. What is high is this: **`CD-RT-012-NO-EXECUTION-INTERFACE` is the register that carries
CD-AC-012 — "no execution pathway exists" — in a trading-adjacent product, and it has been RED
at the tip of the lane through an Engineer return, a Project Lead reconciliation by
measurement, a Product Owner disposition and an Assurance dispatch, and not one of them
reports it.** The increment's own commit message and my dispatch both record "suite 1580
passed"; I reproduce that exactly. **The suite is not the register.** Of 13 declared register
commands on the clean tree at `af2accb`: 11 exit 0, one exits 3 (GRANT-MATRIX-LIVE, no store),
**one exits 1.** This is precisely the clause-(ii) mirror the dispatch taught me — *an exit 1
is not a failure either* — except **nobody read it in either direction.**

## **F-06-B — HIGH. THE AUDIT TARGET DOES NOT CONTAIN ITS OWN GOVERNING AUTHORITY.**

```
LANE (af2accb) BLUEPRINT.md : version 0.1.0   blob 9c65d98…
   CD-BP-003 : 0 hits   CD-BP-002 : 0 hits   BP-AMENDMENT-0001 : 0 hits
   governance/blueprint/ : DOES NOT EXIST     find -iname "*AMENDMENT*" : nothing
MAIN BLUEPRINT.md           : version 0.2.0   blob dc25c77…
   CD-BP-003 : 2   CD-BP-002 : 2   BP-AMENDMENT-0001 : 11
   governance/blueprint/BP-AMENDMENT-0001-engine-owns-the-model-lifecycle.md : EXISTS

is main's BLUEPRINT commit an ancestor of af2accb? : NO — the lane never received it

CITED AT af2accb (excluding BLUEPRINT.md and governance/):
   BP-AMENDMENT-0001 : 96 times across 34 files
   CD-BP-003         : 86 times across 23 files
```

Those 23 files include **shipped product source** (`admission.py`, `establishment.py`,
`collectors/runner.py`, `collectors/adapter.py`, `collectors/validation.py`) and **the doors
instrument whose green row is this audit's subject**, whose DECLARED LIMIT 3 reads *"CD-BP-003,
THE PROTOCOL BOUNDARY THAT ADMITS … BP-AMENDMENT-0001 §D.3 part 2 … BLUEPRINT §17's softest
remaining surface."* **None of those exist at the SHA the instrument runs at.**

The only lane-local text stating what CD-BP-003 *is* sits in `contracts/execution/*.md`, which
the implementing seats wrote. **At the audit target, the authority for the most-cited design
constraint in the product is vouched for by the implementation** —
`SELF_REFERENCE_AND_SELF_VOUCHING` and `EVIDENCE_NOT_INDEPENDENT` (PBG-EVID-001).

**This is also a direct hit on my own dispatch**, which ordered me to read "the Blueprint
(v0.2.0, IN FORCE, with BP-AMENDMENT-0001 applied)" and reconcile. **Recorded and observed
state disagree**, which `CLAUDE.md` names a stop condition — *"reconcile and report; never
silently correct"*. **I report.** I note the mitigation fairly: main/lane governance splitting
is deliberate elsewhere (CD-D-132 splits the build-log blocks). But `BLUEPRINT.md` is not
absent from the lane — it is present **at a stale version**, which is worse, because a reader
following `CLAUDE.md`'s documented manual boot path reads it and concludes CD-BP-003 does not
exist.

## **F-06-C — MEDIUM. `ACTIVE_WORK.yaml` IS STALE ON *BOTH* DOCUMENTED READ PATHS, NOT ONE.**

Disclosure 5 confines this to *"the DOCUMENTED MANUAL BOOT PATH"*. **The `pbg.cli boot` run
printed it too:** `current_work: CD-WO-002`, `next_actor: ENGINEER`, `next_safe_action` naming
`CD-ASR-WO2-01` and branch `wo-2-skeleton`. The file at the target reads
`updated_utc: '2026-08-19T02:54:00Z'` — **four days and five work orders stale.** The CLI does
not compute a fresher answer; it reads and prints the same stale file. **The record's own
continuity file misrepresents the project on BOTH of its read paths.**

## **F-06-D — HIGH. THE CENTRAL ADMISSION GUARD IS IMPLEMENTED WITH THE OPERATOR ITS OWN DOCTRINE FORBIDS.**

`admission.py` states its doctrine three times:
* `:33` — *"A VALUE OF THE WRONG EXACT TYPE — `type(value) is not declared`, never `isinstance`"*
* `:510` — `_Exactly`: *"`type(value)` must BE one of these types. Never `isinstance`."*

and implements it at **`:525` as `if type(value) in self.types:`**.

`in` over a tuple is `==`, not `is`, and `==` is delegable to a metaclass. **VERIFIED BY ME
(throwaway extraction):**

```
class Anything(type):
    def __eq__(cls, other): return True
    def __hash__(cls): return hash("anything")
class Wildcard(metaclass=Anything): pass

--- CONTROL (CD-D-079): @admits(value=float) ---
   faults: ()
   control(Victim) -> REFUSED NotAdmitted: value=Victim is not admitted; requires exactly float
   control(str)    -> REFUSED NotAdmitted
   control(float)  -> ('BODY RAN', 3.14)

--- @admits(value=Wildcard) — SAME decorator spelling ---
   faults: ()                       is_admitting_door: True
   hostile(Victim) -> BODY RAN with Victim
   hostile(str)    -> BODY RAN with str
   hostile(float)  -> BODY RAN with float
   what the door REPORTS it requires: {'value': 'Wildcard'}
```

**A door that admits everything, reports no fault, and tells its own introspection surface that
it requires `Wildcard`.** This project has spent six gates on *guards defeated by a name*.
**This one is defeated by an operator.** The same idiom appears at `admission.py:556` and `:565`
(`_EachOf`), and — outside the mechanism, where the consequence is smaller — at
`dials/dialset.py:70,86`, `engine/evaluate.py:316`, `serving/dial_presentation.py:518`.

**Reach, stated honestly:** the declaration is source-written, so this is not a caller route,
and the fifth seat's *"no caller-controlled route"* for Category C is **correct**. But the
threat this project actually designs against is the plausible edit, which is what `plants/`
exists for — and a developer choosing a type with a custom metaclass for innocent reasons
silently loses the guard while `admission_faults()` returns `()`. **There is no plant and no
test for it:** `tests/test_admission.py` contains one `__eq__` (on an instance, not a
metaclass) and no metaclass-based hostile declaration anywhere.
**Fix is one line: `any(type(value) is t for t in self.types)`.**

## **F-06-E — HIGH. THE FINGERPRINT INSTRUMENT IS NOT INJECTIVE. I PRODUCED A COLLISION.**

This is the instrument my dispatch uses to state my target's identity — *"IF IT IS WRONG, THE
FIRST LINE OF YOUR VERDICT IS WRONG."* **REPRODUCED BY ME, in two throwaway git repos, using
the target's own copy of the instrument:**

```
Tree A: two honest files  a.py = "FIRST = 1\n" , b.py = "SECOND = 2\n"
Tree B: ONE file whose PATH is  'a.py\n<sha256 of b.py>  ./b.py' , content "FIRST = 1\n"
        is "SECOND = 2" the content of any file in tree B? : NO

A (2 honest files) : FINGERPRINT: c688e3d5733697cabf07415792cc2dd246876607ecd15b4e832b558ca7410904
B (1 forged path)  : FINGERPRINT: c688e3d5733697cabf07415792cc2dd246876607ecd15b4e832b558ca7410904
```

Not a sha256 collision — an **unescaped-delimiter preimage injection**. Line 147 builds
`digest + b"  ./" + name + b"\n"` with no escaping and no length prefix. **A recorded
fingerprint does not determine a tree.**

Three further undeclared blindnesses, each material to using this value as identity:
* **its self-vouching claim is false.** The header claims byte-for-byte equivalence with
  `… | xargs -0 sha256sum | sha256sum`. GNU `sha256sum` escapes newlines and backslashes; this
  does not. On tree B: instrument `c688e3d5…` vs shell recipe **different**. The carrier
  `test_it_reproduces_the_historic_shell_recipe_byte_for_byte` asserts it only against a
  fixture with no metacharacters, **so it passes while the claim is false** — the exact
  vacuous-green shape the header itself warns about.
* **its sole declared mitigation switches itself off on the real subject tree.** The header
  justifies accepting the `.gitignore` weakness because *"IT PRINTS EVERY PATH IT EXCLUDED"* —
  but `:220` reads `if excluded and (arguments.show_excluded or len(excluded) <= 40)`. After
  the dispatch's own ordered `pytest` run the real tree has >100 ignored paths, so the list is
  suppressed and a file planted under any `__pycache__/` is invisible **both** to the digest
  and to the report.
* **becoming a symlink is invisible.** Content is read *through* the link (`read_bytes()`), no
  `lstat`. Replacing `src/crash_detector/__init__.py` with a symlink to a file outside the tree
  leaves the fingerprint unmoved while `git status` shows ` T`. Only the *retarget* direction
  is declared.

**WHAT I STILL ASSERT ABOUT MY OWN TARGET, AND WHY IT SURVIVES THIS.** My start and end
fingerprints are identical, `git status --porcelain` was 0 lines at both moments, **and HEAD
and the tree OBJECT (`89196da…`) — which are git identities and are injective — are identical
at both moments.** The fingerprint is a sound *change detector* against accident, which is what
I used it for. **It is not an identity, and the dispatch uses it as one.** F-06-E is properly
the meta-assurance pass's, and I raise it here because it is on my named target list (T15).

## **F-06-F — HIGH. A CARRIER NAMED "MEASURED" IN ALL THREE CD-RULE-004 PLACES DOES NOT EXIST, AND THE INVARIANT IT NAMES IS DEAD WITH THE SUITE GREEN.** *(This is T9's class, run.)*

```
$ git ls-tree -r --name-only af2accb -- tests/ | grep -c test_engine_config.py
0
```

Yet it is named as **"CARRIER MEASURED AND IT IS BODY-LEVEL"** at
`tools/register/check_constructor_field_establishment.py:218`, at
`src/crash_detector/establishment.py:167`, at `required-tests.yaml:1841` and `:1951`, and at
`contracts/execution/CD-RT-002-CONSTRUCTORS-ESTABLISH-FROM-THE-DECLARED-FIELD-LIST.md:223`.

**And the surviving named carrier does not fire either.** AST-shape-preserving kill (throwaway
tree) — the invariant is rewritten to a tautology so node counts and every site-counting sweep
are unmoved and only the semantics die:

```
-        if sorted(declared) != sorted(DIAL_IDS):
+        if sorted(declared) != sorted(declared):

$ PYTHONPATH=src python3 -B -m pytest -q tests/
1580 passed          <-- IDENTICAL TO BASELINE. GREEN.

MUTATED : ConfigSnapshot ACCEPTED with declared dial_ids ['equity_crash','equity_crash'];
          MONETARY DIAL HAS NO SPEC AT ALL: True; every field exactly typed: True
PRISTINE: ValueError: ConfigSnapshot must carry exactly one spec per dial
```

**That is V36's exact claimed shape reproduced at `af2accb` with the entire suite green.**
Four more named carriers are node IDs that do not resolve (`pytest` answers `no tests ran`);
all four exist under drifted names, so the property is carried but **the name in the limit is
not the name of the carrier**, and a reader verifying the limit cannot tell that from an absent
carrier. **The T9 class is LIVE: 1 hard instance, 4 unresolvable IDs, 1 under-named three-site
closure.** It is not systemic rot — three sibling claims in the same paragraph pair are
properly carried, which is exactly what makes the one hole hard to see.

## **F-06-G / F-06-H** — Grounds 1 and 2 above.

## **F-06-I — MEDIUM. "THE ELEVEN" IS A STALE COUNT, AND A PRODUCT OWNER RULING NOW CARRIES IT.**

`crash_detector.establishment` **did not exist** when `CD-ENG-WO2R3-F15` was raised: the file is
created at `66d1d6a` (increment 5), and the sweep reads `514 sites, 11 violations` at `995ec3e`
and `04cdd34`, then `534 sites, 15 violations` from `46adf33`. **The finding enumerated the
entire violation set of its day, which was eleven. Increment 5 created a second mechanism
module of the same shape, the sweep correctly went 11 → 15, and the name never moved.**

The four have been carried ever since as a **remainder the naming produced**, not as a category
anyone derived. There is no property the eleven have that the four lack: same closure rule,
same violation text word-for-word, same kind of module.

**This is the defect `admission.py` DECLARED LIMIT 1 and `CD-PL-F91` were both written about** —
*"A COUNT READ FROM A SIBLING'S RUN IS A MEASUREMENT; A COUNT COPIED HERE IS A TRANSCRIPTION"*
(CD-RULE-009) — reproduced **in the governance vocabulary itself**, and now inside
`PO-DECISIONS-0014` ruling 2, which makes "the eleven" my named targets. **The instrument has
printed the true number at every run for eight build-log entries.**

**RECOMMENDATION: retire the phrase. Fourteen sites and two modules need a disposition.**
Whether they are ruled in one dispatch or several is Product Authority sequencing; the *number*
is not a scope question, it is what the tool measures.

## **F-06-J — HIGH. T3 ATTACKED ON MEASURED GROUNDS: THE §D CLOSURE'S CLASS IS 22 OF 99, AND THE REMEDY IS ALREADY IN THE TREE.**

The `__new__` + `__dict__.update` route **is declared** (`establishment.py:234`, *"TOO NARROW —
MEASURED AT ZERO … NOT CLOSED, NOT CLAIMED, AND NOT PROVED TO BE CARRIED ANYWHERE"*), and I do
not report it as a discovery. **WHAT IS NOT IN THE RECORD IS THE POPULATION.** The declaration
is written about `Agrees`. Nobody has ever counted. I did, over the live package:

```
GOVERNED CLASSES INTERROGATED: 99
  SEALED against __new__ + __dict__.update : 13
  OPEN to it (exact type, forged state)    : 77
```

**All four types the CD-D-105 closure was scoped to are OPEN** — `ConfigSnapshot`, `DialSpec`,
`ModelSpec`, `PanelRow` — as are `DialSet`, `EquityCrashScore`, `MonetaryDebasementScore`, `OK`,
`ObservationRecord`, `Empty`, and **all three witness verdicts** `Agrees`, `Diverges`,
`Unavailable`. The 13 sealed include `DialMagnitude`, `Value`, `Degraded`, `Unknown`,
`FreshnessEvidence`, `StalenessWindow`, `Shown`, `NotShown`.

**The mechanism is `__slots__`** — `DialMagnitude.__slots__ == ('provenance','__quantity')`,
`Agrees.__slots__` absent. **THE REMEDY EXISTS IN THIS TREE, IS APPLIED TO 13 TYPES, AND WAS
NEVER ASKED OF THE OTHER 77.** CD-D-105 ruled *"§D REACHES CONSTRUCTORS … applied at the
boundary so a body edit cannot remove it."* **A body edit cannot. A caller declining to use the
boundary can, for 77 of 99 governed types, and that question was never in the closure's
scope.** That is this project's signature pattern — a control scoped narrower than the class it
names — **with the count measured for the first time.**

## **F-06-K — MEDIUM. INCREMENT 7 CLOSED ONE `tree.body` RESIDUAL AND ADDED THREE. (T4)**

```
LIVE at af2accb:
  check_constructor_field_establishment.py:580  _module_level_names   <- the prior finding, UNTOUCHED
  check_judgement_path_doors.py:573             _module_bindings      <- NEW at increment 7
  check_judgement_path_doors.py:1257            main (NET resolution) <- NEW at increment 7
  check_judgement_path_doors.py:1295            main (NET fetch)      <- NEW at increment 7
```
`git diff 9f7b764 af2accb` confirms `+    for node in tree.body:` is **added**.
`git log f0cee9c..af2accb -- tools/register/check_constructor_field_establishment.py` is
**EMPTY** — increment 7 never touched the constructor check, so the "line 533" closure was in
the **doors** check. **Net traversal residual across the two governing instruments: +2.**

DECLARED LIMIT 5's *"THE RESIDUAL REACH LIMITS ARE EXACTLY TWO"* is **merely less wrong**:
accurate on the class-enumeration axis, false on the **name** axis, and **the file states the
exact mechanism at :283 and leaves it live 297 lines later at :580**. The escape still works
(throwaway): wrapping `FetchOutcome = Union[...]` in `if True:` drops `FetchFailed`, `Malformed`
and `Empty` from the governed class — population 33 → 30, assertions 101 → 91, **EXIT 0 both
times** — and **converts a real FAIL into a PASS**: with `@establishes` stripped from
`FetchFailed`, control = `FAIL — 1 violation, EXIT 1`; with `if True:` = `PASS — 91 assertions,
EXIT 0`. Reproduced for `if`/`try`/`with`/`for`/`while`. **Uncarried anywhere.**
And **`_module_bindings` being new is the convergence with Ground 1**: the function the
reachability clause reasons over cannot see a module-level binding written inside any block.

## **F-06-L — MEDIUM. THE PLANT SET (T13): 12 PLANTS, 10 EVIDENCE, 2 DECORATION — AND NOBODY HAD MEASURED IT SINCE `531c95c`.**

All 12 apply. Ten fail **at the layer their proposition names** with the refusal read from the
failure text — that is real, and I record it. **Two are not contrasts:**
* `CD-RT-003-GRANT-MATRIX-LIVE` — **exit 3 PRECONDITION on BOTH arms.** Identical output clean
  and violated. **Not a contrast; decoration.**
* `CD-RT-012-NO-EXECUTION-INTERFACE` — **the clean arm already fails** (F-06-A). No contrast.

`plants/MANIFEST.md:96` — *"Eleven tests, eleven patches"* — is **FALSE**, and the same file
contradicts itself at `:1209` (*"A TWELFTH PLANT"*) and `:1214`. Nine `eleven` occurrences
survive. **This is the fifth seat's next-safe-gate item (e), which increment 7 did not take.**
Also: **`CD-RT-002-DOORS-REQUIRE-THEIR-TYPES` has no plant at all** — the register whose green
row is this audit's subject is covered only by an Engineer variant, not by a negative control.

## **F-06-M — LOW/MEDIUM. THE CORPUS INDEX IS BLIND TO AN ENTIRE TREE AND ASSERTS THE OPPOSITE OF WHAT IS ON DISK.** *(disclosure 6)*

The WO-2R3 manifest itself is now **complete** — I read the directory, not the manifest: 40
files, 11 executable probes, **every file has at least one row, zero gaps**, and the six probes
that had **0 rows at `9f7b764` have 1 row each at `af2accb`**. Increment 7 genuinely closed
CD-PL-F97 for that directory. **But one level up:**
* `variants/MANIFEST.md` — the corpus index — contains **zero** occurrences of `WO-2R3`. Its
  index table has two rows. **An entire tree of 40 artefacts and 11 executable probes is
  invisible to the file that exists specifically because a dispatch pointed at a corpus index
  that did not exist.**
* Its closing sentence reads *"**NOTHING ANYWHERE UNDER `variants/` IS EXECUTABLE** — patches
  and prose only, mode 0664, no symlinks, no wrapper, no runner (`PBG-ASSURE-001`)."*
  `variants/WO-2R3/` holds 9 `.py` and 2 `.sh` files the WO-2R3 manifest **tells you to run**;
  `P-H…sh` opens `#!/usr/bin/env bash` and drives ten arms. **The index asserts the opposite of
  what is on disk.**
* `variants/WO-2R/`: **25 of 70 patches are never named by filename** anywhere in its manifest
  — the whole of `CD-ASR-F05/`, `CD-ASR-F06/` and `CD-PL-F62/`. Rename any of them and the
  manifest still "covers" them.

## **F-06-N — MEDIUM. THREE `variants/WO-2R` ARMS FAIL FOR THE WRONG REASON, AND EXIT CODES SCORE THEM CLOSED. (T7)**

**Four** patches now need `patch --fuzz=5`, not one — the dispatch names V05; **E04, V03 and
V06 are in the same state and nobody has said so.** And `--fuzz=5` mis-lands three of them:
* **V03** — `+import sys` lands at line 59, **inside the module docstring** (which ends at 76).
  The runtime arm dies `NameError: name 'sys' is not defined`. **NO LAYER REFUSED. The route
  never executes.**
* **V06** — same, `+import os`. Static arm valid (`RULE F`); **runtime arm worthless.**
* **V05** — `@_with_neutral_measure` lands above **`Degraded`**, not `Unknown`. Right layer,
  **wrong class**; V05's proposition is about *absence*, which is `Unknown`. **Not
  re-established for its own proposition.**

**Anyone re-running `variants/WO-2R/` with `--fuzz` and reading exit codes scores all three
CLOSED.** That is the `CD-ENG-WO2R3-F12` standard failing in the corpus itself.
Also measured: **V15 has CHANGED — the manifest records it NOT REFUSED at `253c38b`; at
`af2accb` it is REFUSED** (`QuantityProvenanceMissing`). And **E04, V11, V48 name runtime
carriers their commands no longer reach** — the refusals moved (safe direction, earlier layer),
but the rows are stale. Openly OPEN and correctly declared: V12, V13, V17, V29a, V44, E08.

## **F-06-O — MEDIUM. THE "NO LIVE STORE" PREMISE CARRIED SINCE INCREMENT 2 IS FALSE. (T6)**

The inherited correction **holds and I re-measured it**: the five `CD_CHECK_STORE_*` variables
are unset here; the check refuses at `check_grant_matrix_live.py:727-735`, **before** the
`import psycopg2` at `:738`; `EXIT=3`. And two new measurements strengthen it:
* **`psycopg2` IS importable** (2.9.11), so exit 3 is definitively not "no driver".
* **Exit 3 is ambiguous by construction.** With all five set to a dud target the check still
  exits 3, with a different reason. `check.refuse()` returns 3 for env-unset, driver-missing,
  store-unreachable and migration-failure alike. **The exit code can never distinguish them;
  only the text can.**

**And the new fact:** that dud-target run returned `FATAL: password authentication failed for
user "nobody"` — **not** `connection refused`. **There is a live PostgreSQL listening on
127.0.0.1:5432 on this host.** The plant has been recorded as un-runnable *"for want of a live
store"* at every increment since 2. **That premise is now false; what is missing is
credentials.** No credentials were guessed. This is a different sentence from the one the
record carries, and someone should be told it.

## **F-06-P — LOW, AND IT CORRECTS THE RECORD IN THE PROJECT'S FAVOUR. (T17)**

The Engineer's *"it expires the day a computing mapping lands. There is no carrier for that
day"* — adopted into `PO-DECISIONS-0014` ruling 3 — **is false.**
`tests/test_engine_model_registry.py:830` asserts `list(MappingKind) == [MappingKind.UNSPECIFIED]`
and its own docstring calls it *"the tripwire that makes such an addition visible instead of
quiet."* **The day arrives loudly and the suite goes red.** What is missing is not a carrier,
it is the **link** — the failure message says "a second member is a PRODUCT decision"; it does
not say "re-run the `*extra` guard measurement". **A declared limit wrong in the pessimistic
direction is still wrong** (the increment's own F17 makes this point), and the remedy is one
sentence in an existing failure message rather than a new control.

## **F-06-Q — LOW, FLAGGED AND NOT CHASED.** During Category-A plant work an intermediate tree
carried a `SyntaxError` in `staleness.py` and `check_judgement_path_doors.py` still reported
`PASS — 60 assertions` with no count change and no warning. **A check that silently skips a
file it cannot parse exits 0 over a subject it never read.** I did not confirm the mechanism
and I am not asserting it — **it is worth a bounded look and I would not want it lost.**

## **F-06-R — HIGH. CATEGORY C: ALL SIX LAND. I DISAGREE WITH THE FIFTH SEAT AND WITH THE DRAFT DISPOSITIONS.**

The lever is F-06-D. A metaclass defining `__eq__` satisfies `isinstance(X, type)` at the six
Category C sites **and then compares equal to every type** at `_Exactly.refusal`. **C4 verified
by me personally** (output in F-06-D); the other five measured on the same lever:
`_EstablishedHere.__call__` accepts a `str` subclass whose `strip` lies, so **an unexplained
exemption gets through — the one thing that guard exists to stop**; `_compile(_Admission)`
accepts a subclass whose `refusal` returns `None` **and whose `describe()` reports `"exactly
PanelRow"`**; `_compile(tuple)` accepts a `tuple` subclass whose `__iter__` yields something
other than what `repr` and `len` show; `_type_tuple` and `each_of` follow.

**The fifth seat's narrow claim is CORRECT — these are consumed at decoration from a
source-written declaration and I found no caller route either.** But **"no caller-controlled
route" is the wrong test**, because the module's own doctrine is that a *subclass* must never
be trusted, and **the declaration vocabulary is admitted by `isinstance` at all six sites while
the value vocabulary is not.** The mechanism applies its doctrine to values and violates it one
level up, at the layer that decides what "established" means. **`OUT_OF_BOUND ×6` records the
weaker half of the fact, and `OUT_OF_BOUND` is a scope claim no instrument can falsify.**

## **F-06-S — LOW, LATENT.** `_preferred_error.sort_key` (`publication/envelope_contract.py:440`)
is the second callable the reclassification removed from the door population. It is
public-named, declared UNREACHABLE via the `PASSED_TO` weakening, and **off a RULE 1 judgement
path, so the NETS backstop does not cover it.** Harmless today only because `publication/` is
not a judgement-path package. **The day `publication/` is added — and it is the publication
path — this callable becomes silently NET-eligible rather than a door.**

---

# §4 WHAT I COULD NOT ESTABLISH — MEASURED LIMITS, NOT SILENT OMISSIONS

1. **`CD-RT-003-GRANT-MATRIX-LIVE`'s actual verdict.** The check refuses at the env gate before
   touching a database. A live PostgreSQL exists on this host (F-06-O) but I have no
   credentials and **did not guess any.** The plant's contrast remains unmeasured — now for
   want of credentials, not for want of a store.
2. **Whether V03, V05 and V06's routes are actually closed at `af2accb`.** Their patches no
   longer apply cleanly and `--fuzz=5` mis-lands them (F-06-N). Re-cutting them against the
   `af2accb` structure is Engineer work and outside a read-only audit.
3. **Whether the C1-C6 hostile declaration forms are reachable through
   `crash_detector.establishment.establishes(...)` from a caller.** `establishes` routes through
   the same `_compile`, so the six sites are in play one level down, but `@establishes(...)` is
   likewise source-written. **I did not find a caller route and I did not exhaustively rule one
   out.**
4. **Whether Category A has ever been exercised in this tree's history.** I measured the
   property at `af2accb`. I did not bisect.
5. **The mechanism behind F-06-Q** (possible silent skip of an unparseable file).
6. **The meta-assurance questions raised by F-06-B and F-06-E** are properly the authorised
   meta-assurance pass's; I measured them because they are on my target list, not because I
   discharged them.
7. **I did not attack the CD-D-105 closure's *substance*** — whether §D should reach
   constructors at all. F-06-J attacks its **scope**, which is what the invitation offered.
8. **I make no claim that my finding list is complete.** Disclosure 9 says the "control scoped
   narrower than the class it names" pattern was counted at nine where four were recorded, and
   *"should not have implied the count was bounded"*. **F-06-J is the first time anyone has
   measured one of these classes rather than counted instances, and it came out at 77.
   ASSUME THERE ARE MORE.**

---

# §5 THE REGRADES, AND WHAT WOULD MOVE EACH

### T2 — **RED** (unchanged)
Escape 3 reproduced in full at `af2accb`, undeclared, uncarried, in a file increment 7 did not
touch. **→ AMBER** requires the sink route closed (snapshot the outcome before `_record`, or
derive the reading key from the recorded row) **or** declared with item A's specificity, **and**
a carrier that fails when a sink mutates its argument. **→ PASS** requires conformance-and-return
closure over `sink`/`ledger`/`validator` equal to `adapter`'s, with counterfactual arms.

### CD-AC-002 — **AMBER, NOT CLOSED** (unchanged)
*"The two dials are never blended."* `check_no_blend.py` → **EXIT 0, PASS — 7161 assertions**,
and the blend plant is genuine evidence (clean 0/7161 → violated FAIL 2, `RULE 1: arithmetic
across the two dials`, `RULE 2: one expression consumes both dials`). **That machinery works.**
It stays AMBER because the two dial score types `EquityCrashScore` and `MonetaryDebasementScore`
are in F-06-J's open 77 — an object of the exact score type carrying forged state can be made
with **zero package code**, and no blend rule reads a type that was never constructed through
its boundary. **→ moved** requires the declared member floor turned from a `check.note` into a
`check.violation`, and the two score types sealed the way `DialMagnitude` already is.

### CD-AC-005 — **AMBER, NOT CLOSED. Grade unchanged; reasoning weaker again, and this is the third gate running that has had to say so.**
*"`WITNESS UNAVAILABLE` ≠ `WITNESS AGREES`."* Measured by me, with the counterfactual arm at the
right layer:

```
CONTROL (ordinary path, correct field names):
  Agrees(divergence_measure=0.0, as_of_utc='NOT A TIMESTAMP', freshness='NOT EVIDENCE')
    -> REFUSED at layer: TypeError — "expected datetime, got str"

ESCAPE (__new__ + __dict__.update, same field names, no package code):
  type(s) is exactly Agrees : True      __post_init__ ran? : NO
  divergence_measure : 'NOT A FLOAT'   as_of_utc : 'NOT A TIMESTAMP'   freshness : 'NOT EVIDENCE'
  ==> AgreementWithoutFreshnessEvidence never fired.
```

**And the new part: it is not just `Agrees`. `Diverges` and `Unavailable` are equally open, and
`DialMagnitude` — one module away — is SEALED.** So the very distinction CD-AC-005 names is
between three types none of which is sealed, in a codebase that seals thirteen others.
**→ RED** if the Product Owner takes the fourth seat's stated test.
**→ PASS** requires `Agrees`, `Diverges` and `Unavailable` sealed against `__new__`/`__dict__`
construction the way `DialMagnitude` already is — **which is `__slots__`, already in this tree,
already applied to 13 types.** I record that the remedy is cheap because "expensive" has been
doing quiet work in this item's history.

---

# §6 CONTINUATION IMPLICATION, AND THE NEXT SAFE GATE

**CONTINUATION IMPLICATION, STATED SEPARATELY FROM THE FINDINGS as the role contract requires.**
Nothing here makes the tree unsafe to *hold*. Nothing found is exploitable by a remote party;
every route needs either in-process code or a source edit. **The WO-2 gate should stay SHUT and
nothing should merge or promote** — but the lane is safe to leave exactly where it is, and
`af2accb` is a sound base for the next increment. **The urgency is in the CONTROLS, not the
product.** Three governing instruments currently answer questions they are not asking:
the doors check's reachability clause (Ground 1), the constructor check's DECLARED LIMIT 5
(F-06-K), and `CD-RT-012-NO-EXECUTION-INTERFACE`, which is simply red (F-06-A).

**NEXT SAFE GATE — Product Owner disposition of this verdict FIRST.** Nothing below is
authorised by me (PBG-AUTH-003). In the order I would take them:

1. **RULE ON GROUND 2 BEFORE ANY CODE MOVES.** The item-1 STOP condition was met. Whether
   `PO-DECISIONS-0012` ruling 1 falls is Product Authority's alone, and **the answer decides
   whether the doors instrument is repaired or redesigned.** Repairing the criterion before that
   ruling would be a seat applying a consequence reserved to the Product Owner — the exact move
   the increment-7 dispatch forbade its Engineer.
2. **F-06-A: `CD-RT-012-NO-EXECUTION-INTERFACE` is RED at the tip.** Independent of everything
   else. It needs a decision (fix the L3 false positive, or declare it) and it needs whoever
   reconciles boundaries to run **the register set**, not only the suite and the two named
   instruments. **This is the cheapest and most urgent item on the list.**
3. **F-06-D: one line in `admission.py:525`** — `type(value) in self.types` →
   `any(type(value) is t for t in self.types)`, with a metaclass plant as its carrier. It
   unblocks the honest disposition of Category C.
4. **F-06-B: reconcile the lane's `BLUEPRINT.md`.** The tree cites an authority it does not
   contain, 182 times. This is a governance act, not an engineering one.
5. **THEN the eleven — as fifteen (F-06-I)**, in the ratified vocabulary, with the minimal
   findings register so `DEFECT_OPEN.finding` resolves against something (T16 measured that it
   currently resolves against nothing), and with Category C dispositioned on F-06-R rather than
   as `OUT_OF_BOUND`.
6. **Ground 3 / Escape 3** — the fifth seat's item (a), still untaken after two gates. Snapshot
   the outcome before `_record`, or derive the reading key from the recorded row; carrier: a
   test that a mutating sink cannot change `CollectionResult.final_outcome` or `reading_key`.
7. **F-06-K**: `_module_level_names` and the three new `tree.body` sites to `ast.walk`;
   DECLARED LIMIT 5 corrected to its measured count with a carrier that fails.
8. **F-06-J**: a ruling on whether §D's closure extends to the construction *path*. If yes,
   `__slots__` on the witness verdicts and the score types first.
9. **F-06-L / F-06-M**: `plants/MANIFEST.md:96`, the corpus index's WO-2R3 blindness and its
   false "nothing is executable" sentence. Documentary, cheap, and three of them are the fifth
   seat's item (e) which is now two gates old.
10. **The authorised META-ASSURANCE pass** now has F-06-E (the fingerprint is not injective),
    F-06-B, F-06-C and F-06-F waiting for it.

**AND ONE THING I WANT ON THE RECORD ABOUT THE SEQUENCING (clause iii).**
`PO-DECISIONS-0014` ruling 2 inverted the order so that I would see the raw record, on the
fifth seat's argument, against that seat's own convenience. **The Project Lead's stated risk in
CD-D-158 was that "the auditor grades a register that is not there." IT DID NOT BITE, AND I
SHOULD SAY SO PLAINLY BECAUSE THE PROJECT LEAD WAS OVERRULED AND IS ENTITLED TO THE ANSWER.**
Grading an absent register cost me nothing, because **the register was never the target — the
ELEVEN were**, and they exist in the sweep's output whether or not anyone has written a
disposition for them. What I would have lost, had the dispositions been written first, is
F-06-R: I would have read `OUT_OF_BOUND ×6` and spent my Category C budget checking a stated
reason instead of attacking the sites. **The inversion was right, the fifth seat's general rule
is right, and the evidence for it is that the map drawn by the author would have pointed me
away from the largest thing I found in that section.**

---

    CD-ASR-WO2R3-03 · ASSURANCE_ENGINEER
    target af2accbfc950961bb7f7967d34ecf16414088228 · tree 89196dacba1680fdc048fe6f84e45081ac4e738a
    fingerprint 66a1c27dadecaa0a891f9f2a2c28f89ed3ec8729eca2719fd49680e37c5e4ecd
      — taken at start and re-taken at end, identical; porcelain 0 lines at both moments
      — and see F-06-E: I broke this instrument's injectivity, so HEAD and the tree object,
        which are git identities, are what I actually rest my target claim on.
    VERDICT RED · T2 RED · CD-AC-002 AMBER NOT CLOSED · CD-AC-005 AMBER NOT CLOSED
    NOT AN ACCEPTANCE (PBG-AUTH-003). The Product Owner dispositions.
