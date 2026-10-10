STATUS: COMPLETE — VERDICT **RED** · T2 RED · CD-AC-002 AMBER (not closed) · CD-AC-005 AMBER (not closed)

# ASSURANCE VERDICT — WO-2R3, THE FIFTH SEAT

- **actor_id**: CD-ASR-WO2R3-02 (second carrier; the first died before banking anything — CD-D-148)
- **assigned_role**: ASSURANCE_ENGINEER
- **dispatch**: `governance/dispatch/CD-DISPATCH-WO2R3-ASSURANCE-05.yaml`
- **product authority basis**: PO-DECISIONS-0011 ruling 5
- **target SHA**: `9f7b7640f692442e22a47ecac3d4a643057729d5`
- **target tree object**: `224debf13475acdb10944bfa201a82c5d3d199d8`
- **scope**: the whole of WO-2R3, `f30e63c..9f7b764`
- **worktree**: `/srv/crash-detector-wo2r3-audit5`
- **started (UTC)**: 2026-08-22T23:14:55Z

## INDEPENDENCE DECLARATION

I am CD-ASR-WO2R3-02. I am not CD-ENG-WO2R3-01 or CD-ENG-WO2R3-02. I am none of
CD-ASR-WO2-01, CD-ASR-WO2-02, CD-ASR-WO2R2-01, CD-ASR-WO2R3-01. I did not write,
review, advise on or dispatch any part of what I am auditing. PBG-SOD-001 holds.

I inherit nothing from the dead first carrier. I have read no `/tmp` artefact
predating this session as a measurement. Every number below was produced by me in
this session, or is explicitly labelled as somebody else's and not credited.

## FINGERPRINT AT START

Recipe: `find . -path ./.git -prune -o -type f -print | LC_ALL=C sort | xargs sha256sum | sha256sum`
run in `/srv/crash-detector-wo2r3-audit5`.

```
50b356ac2de1a404b75a6fb9e478fe5d4141c4fdc6ad34ddfbfcd4a5a92ee7b9
```

Dispatch states `50b356ac2de1a404b75a6fb9e478fe5d4141c4fdc6ad34ddfbfcd4a5a92ee7b9`. **MATCH.**
`git status --porcelain` → **0 lines**. `git rev-parse HEAD` → `9f7b7640...`. `git rev-parse HEAD^{tree}` → `224debf1...`. All match the dispatch.

## BOOT VERDICT

`cd /srv/crash-detector-wo2r3-audit5 && PYTHONPATH=pbg/tools python3 -B -m pbg.cli boot`

- Verdict: **RED**, `continuity_state = CONTINUITY_REFERENCE_INVALID/RESUME_BLOCKED`.
- This is disclosure 7: the boot reads `main`'s continuity record from a detached lane.
  Disclosed, not ruled harmless. See finding section for what I make of it.
- `blueprint_identity BLUEPRINT.md@794c25097d4f1f4a`, `pid_identity PID.md@441d83166b2f3d0c`.
- `roadmap_identity None` (UNAVAILABLE: Roadmap not found at ROADMAP.md) — flagged, see findings.
- **`current_work` reads `CD-WO-002 — interrupted Engineer lane reconciled and quarantined
  (CD-D-007)` and `next_safe_action` names `CD-ASR-WO2-01` and branch `wo-2-skeleton`.**
  That is the fourth seat's stale-`ACTIVE_WORK.yaml` finding, reproduced by me independently.
  It is stale by five work orders. See findings.

**Boot verdict as ASSURANCE_ENGINEER: PROCEED.** The target reconciles byte-for-byte with
the dispatch; the RED is a known lane artefact of a PL-role boot run in a detached worktree
and does not describe the work. I record it rather than treat it as clearance.

---

# LOG OF MEASUREMENTS (appended as established)

## M1 — THE THREE INSTRUMENTS AND THE SUITE, RUN BY ME AT THE TARGET

All run in `/srv/crash-detector-wo2r3-audit5` with `PYTHONPATH=src`, exit codes captured
without a pipe (a piped exit code is the pipe's, and this record already contains one seat
misreading its own probes).

| instrument | my exit | my headline |
|---|---|---|
| `tools/register/check_judgement_path_doors.py --root .` | **1** | `CD-RT-002-DOORS-REQUIRE-THEIR-TYPES: FAIL — 1 violation(s)`; 39 files, **28 doors**, 55 assertions; SUBJECTS 28, DECORATED 27 |
| `tools/register/check_constructor_field_establishment.py --root .` | **0** | `PASS — 101 assertions, 0 violations`; 39 modules, **99 classes examined**, **33 in the class** (32 fielded, 1 vacuous) |
| `tools/sweep/delegated_judgement_sweep.py --root .` | **1** | `CD-CLASS-2-SWEEP: FAIL — 534 sites, 15 violations` |
| `python3 -m pytest -q` | — | **2 failed, 1549 passed** |

The single doors violation is `src/crash_detector/engine/evaluate.py:341 — guarded ...
UNDECORATED_JUDGEMENT_PATH_DOOR`. The two failures are
`tests/test_judgement_path_doors.py::test_the_static_check_passes_and_is_not_vacuous` and
`::test_the_collector_boundary_is_a_judgement_path_package_and_cd_bp_003_is_what_remains`.

**Every declared state in the dispatch is reproduced by me exactly.** No surprises, and I
record that as a fact about the dispatch's honesty, not as clearance for the work.

**First arithmetic note, mine:** the constructor check reports **101 assertions**; the fourth
seat measured **97** at `531c95c`, and the widened-traversal note quoted in the doors check
still quotes `PASS — 97 assertions` from the fourth seat's escape. Population is **33 at both
SHAs** and classes examined is **99 at both SHAs** — see M-T4 below, which is where that
matters.

## M2 — CD-D-146, `guarded`. MY JUDGEMENT, AND IT IS NOT EITHER OF THE TWO READINGS OFFERED

The dispatch gave me two readings and said neither is ruled. **I measured a third fact that
decides between them, and it is on nobody's list.**

### M2.1 THE RENAME TEST — THE VIOLATION DOES NOT SURVIVE ONE IDENTIFIER

Throwaway extraction of `9f7b764` at `/tmp/cd-asr5-b-t146/rename`, `git archive | tar -x`.
**One change and one change only**: the function-local binding `guarded` → `_guarded`
(`def guarded(` → `def _guarded(`, `return guarded` → `return _guarded`). Nothing else in the
tree touched — no decorator added, no test edited, no instrument edited.

| | target `9f7b764` | `+` rename only |
|---|---|---|
| doors check exit | **1** | **0** |
| doors check verdict | `FAIL — 1 violation(s)` | `PASS — 54 assertions, 0 violations` |
| subjects enumerated | 28 | 27 |
| full suite | **2 failed, 1549 passed** | **1551 passed** |
| runtime `_evaluate_dial.__name__` | `_evaluate_dial` | `_evaluate_dial` |
| runtime `__qualname__` | `_evaluate_dial` | `_evaluate_dial` |
| `inspect.signature` | `(spec, usable, now_utc, model=None)` | `(spec, usable, now_utc, model=None)` |
| `hasattr(module,'guarded')` | **False** | **False** |
| behaviour | unchanged | unchanged |

Both arms were run with **each tree's own copy of the probe**, and both printed a distinct
`tree:` provenance line (`/srv/crash-detector-wo2r3-audit5/...` vs
`/tmp/cd-asr5-b-t146/rename/...`) — CD-PL-F98 discipline, deliberately observed.

**I am reporting this AS A RENAME TEST AND NOT AS THE TREE'S STATE.** The tree's state is
exit 1, measured at M1. The dispatch forbids presenting a patched extraction's verdict as the
target's and I am not doing so.

**By this project's own standard — "for any refusal credited to a STRUCTURE: does it survive
renaming one identifier? If it depends on a NAME, it is a vocabulary guard wearing a
structural label" — the `guarded` violation FAILS the rename test.** It is decided entirely by
a name that is (a) not module-level, (b) not importable, (c) not in `__all__`, (d) overwritten
at runtime by `functools.wraps` to a *private* name, and (e) invisible everywhere except
`__code__.co_name`.

### M2.2 THE SYMMETRY ARMS — THE SAME SHAPE IS INVISIBLE ONE DIRECTORY AWAY

Identical planted shape (public-named function-local `def`, arity-open `*extra,
**extra_by_name`, no `@admits`), two throwaway extractions:

| where planted | doors check |
|---|---|
| `src/crash_detector/staleness.py` (top-level module, **not** RULE 1) | **exit 1, still 1 violation, subjects 28** — the plant is INVISIBLE |
| `src/crash_detector/serving/dial_presentation.py` (RULE 1) | **exit 1, 2 violations, subjects 29** — flagged |

### M2.3 AND THE SHAPE IS ALREADY LIVE FOUR MORE TIMES IN THIS TREE, UNFLAGGED

I enumerated every public function-local `def` in `src/crash_detector` myself by AST:

```
admission.py:714    admits.apply_at_the_boundary          <- NOT FLAGGED
admission.py:720    apply_at_the_boundary.door            <- NOT FLAGGED  (*args, **kwargs)
engine/evaluate.py:341  _absence_is_never_a_number.guarded    <- THE ONE VIOLATION
establishment.py:451    establishes.apply_at_the_boundary  <- NOT FLAGGED
publication/envelope_contract.py:440  _preferred_error.sort_key  <- NOT FLAGGED
```

**`door` is the single most load-bearing callable in the admission mechanism** — every value
that passes through every `@admits` door in this system passes through it — it is
PUBLIC-NAMED, it is **ARITY-OPEN `(*args, **kwargs)`**, it carries no `@admits`, and it is not
flagged for one reason only: `admission.py` is not under `engine/serving/collectors`.

### M2.4 MY JUDGEMENT ON CD-D-146

**On "is `guarded` a real door": NO, not as the check means it, and reading TWO is right —
but for a reason stronger than the one offered.** The offered reading TWO was that the public
clause is a name heuristic that does not transfer to function scope. My rename test *proves*
that, rather than arguing it. The check's verdict at this site is a pure function of one
unreachable local identifier, and the arms above show the same shape passing untouched one
module away.

**On "is the arity-open tension real": YES, AND IT IS WORSE THAN THE DISPATCH STATES — IT IS
NOT A TENSION, IT IS A CONTRADICTION THE INSTRUMENT ITSELF ALREADY RULES ON.**
`check_judgement_path_doors.py` carries an `OPEN_CHANNEL` violation rule, verbatim: *"A
variadic parameter is the general case of a parameter the declaration was not told about…
**The runtime refuses every call to such a door**."* So decorating `guarded` with `@admits`
does not fix the violation — **it converts `UNDECORATED_JUDGEMENT_PATH_DOOR` into
`OPEN_CHANNEL` and, by the instrument's own words, makes every call to `_evaluate_dial` raise
at runtime.** There is **no shape that establishes AND stays arity-open** under this
instrument's rules; the instrument has already decided that, and the only reason nobody hit it
is that the door was invisible until the traversal widened. Answering the dispatch's question
directly: the tension is real, it is not resolvable inside the current rule set, and the
Engineer's three "routes to green" list was therefore **incomplete** — there is a fourth
(`@admits` + accept the arity break) and it is worse than the three it named.

**On "was shipping the lane RED the right call, or a defect parked behind a story":
THE DECISION TO SHIP RED WAS RIGHT. THE STORY ATTACHED TO IT IS WRONG, AND THAT IS THE
FINDING.** Right, because every route to green available to the Engineer was a bypass
(`PBG-FWK-013`'s shape), it named all three and took none, and it offered no recommendation —
that is the seat behaving correctly under an unresolvable brief. Wrong, because the RED is
being carried as *"the widened walk found a pre-existing violation in protected product
code"*, and **what it actually found is that the instrument's public-clause and package-clause
are vocabulary tests that its own widened traversal has now outrun.** The tree is not
carrying a defect at `evaluate.py:341`; **the instrument is carrying two**, and one of them
(the RULE 1 package vocabulary, which hides `door`) is the *ninth-instance pattern the fourth
seat counted, now at instance ten, inside the fix for instance nine.**

**Consequence for CD-D-146, stated so the Product Owner can rule on it rather than argue it:
a ruling that `guarded` is a real door obliges the same ruling on `admits.door`, and the
instrument cannot see `admits.door`. A ruling that it is not obliges a narrowing of the public
clause at function scope. Either ruling requires an instrument change. THE ONE OPTION THAT IS
NOT AVAILABLE IS RULING THE VIOLATION SOUND AND LEAVING THE INSTRUMENT ALONE.**

## M3 — **THE ROUTE NOBODY HAS WRITTEN DOWN.** `__wrapped__` IS LIVE ON THE CD-ASR-F03 GUARD

This is on no auditor's list, in no dispatch, in no manifest, in no build log, and in no
variant patch. It is the thing the dispatch asked for.

### M3.1 THE FACT

`crash_detector.admission` deletes `__wrapped__` from every `@admits` door
(`admission.py:766`), with a doctrine block, a DECLARED LIMIT, the V24 patch
(`variants/WO-2R3/V24-wrapped-attribute-bypass.patch`) as its evidence — *"`resolve_panel.__wrapped__(duck_row, ...)`
returned Agrees and rendered WITNESS AGREES"* — and a test carrier at
`tests/test_admission.py:334`.

`crash_detector.establishment` deletes `__wrapped__` from every `@establishes` `__init__`
(`establishment.py:506`), with the same doctrine and carriers at
`tests/test_field_establishment.py:215-216`.

**`crash_detector.engine.evaluate._absence_is_never_a_number` — the CD-ASR-F03 post-condition
wrapper, the one guard in this tree that exists *because* of an escape — DOES NOT.** Measured
by me at the target:

```
tree: /srv/crash-detector-wo2r3-audit5/src/crash_detector/engine/evaluate.py
has __wrapped__ on the CD-ASR-F03 post-condition wrapper? True
  __wrapped__ -> <function _evaluate_dial ...> _evaluate_dial
```

### M3.2 THE TWO-ARM DEMONSTRATION, AT THE LAYER THE PROPOSITION NAMES

Throwaway extraction `/tmp/cd-asr5-b-wrapped` of `9f7b764`. One body rewrite — CD-ASR-F03's
own shape, the `missing_required` branch made to return a `Value` claiming the inputs it did
not get. **Nothing else changed; the wrapper is intact and applied.**

```
tree: /tmp/cd-asr5-b-wrapped/src/crash_detector/engine/evaluate.py
THROUGH the CD-ASR-F03 wrapper : REFUSED -> crash_detector.dials.reading.AbsenceYieldedAValue:
                                 dial 'equity_crash' produced Value, which carries a value,
                                 but its required inputs were not all present
THROUGH __wrapped__            : *** ACCEPTED *** -> Value carrying a value;
                                 inputs_used=('src.a',)      <- inputs that were NEVER PRESENT
```

**Method note against myself, recorded because this project's F12 standard demands it.** My
FIRST attempt at this contrast produced *both arms refusing*, with
`CrossDialCombination: refusing to admit a number for dial 'equity_crash' with no inputs` —
a **different layer** (`observed_for_dial`) refusing for a **different reason**. Had I stopped
there I would have recorded "no bypass" — a false negative from two arms that looked alike in
a summary table. I read the failure text, saw it named the wrong layer, and rebuilt the arm so
the rewritten branch *claims* its required inputs. Only then did the arms separate. **This is
CD-ENG-WO2R3-F12 biting me in this audit, and I am recording it rather than only its
conclusion.**

### M3.3 COUNTERFACTUAL ARM (CD-D-079) AND RENAME TEST

**Counterfactual:** add `delattr(guarded, "__wrapped__")` — literally what `admits` and
`establishes` already do — and the route does not exist:
`AttributeError: 'function' object has no attribute '__wrapped__'`. **The route is closed by
the two lines the project has already written twice.**

**Rename test:** the refusal that DOES hold (`AbsenceYieldedAValue`) is derived from
`type(reading) not in READINGS_THAT_CARRY_A_VALUE` — type identity, naming no identifier of
the caller. **It survives renaming.** The refusal is structural; the *bypass around it* is
what is unguarded.

### M3.4 AND THE CARRIER FOR THE GUARD IS THE BYPASS ITSELF

`tests/test_evaluate.py:692`, verbatim:

```python
assert hasattr(evaluate_module._evaluate_dial, "__wrapped__"), (
    "the per-dial evaluator must be wrapped in refuse_a_number_without_its_inputs; "
    "without it, any rewritten branch may return a number (CD-ASR-F03)")
```

**The only shipped assertion that the CD-ASR-F03 guard is applied is the presence of the
attribute that removes it.** Fixing the defect fails that test. The test and the defect are
the same line. That is not a coincidence to be smiled at — it is why three parties looked at
this wrapper across WO-2R, WO-2R2 and WO-2R3 and saw a guard.

### M3.5 SCOPE AND SEVERITY, STATED HONESTLY

- **Pre-existing, not introduced by WO-2R3.** `git log -S` puts `_absence_is_never_a_number`
  at `defd76c` (WO-2R increment 1) and `006b922`; it is present at the WO-2R3 base `f30e63c`.
  I am not charging it to this increment. I am charging it to the tree WO-2R3 asks to be
  graded, which is what my scope is.
- **Not exploitable through a foreign adapter or a network caller at this SHA.**
  `_evaluate_dial` is a private module-level name. The route requires in-process code that can
  import `crash_detector.engine.evaluate` — which, per the fourth seat's ESCAPE 2 and my M6
  below, is a lower bar at this codebase's declared-foreign boundary than its own declarations
  claim, but it is still a bar. **I did not demonstrate a route to it from `collect`.**
- **It is the ELEVENTH instance of "a control scoped narrower than the class it names"** —
  the fourth seat counted nine, the Project Lead had recorded four and said the count was not
  bounded. M2.3 is the tenth and this is the eleventh. **I do not claim eleven is the count
  either.**

## M4 — ESCAPE 3 AND THE SINK / LEDGER / VALIDATOR TABLE, GRADED ON MY OWN MEASUREMENT

Ordered by PO-DECISIONS-0011 ruling 5. Both were **delegated measurement, never verified by
any auditor**. I wrote my own harness from `collectors/runner.py` at the target; I did not
run and did not read any pre-existing probe as a measurement. `tree:` provenance printed on
every run and read every time (CD-PL-F98).

### M4.1 ESCAPE 3 — **CONFIRMED, UNMOVED BY THE REMEDIATION INCREMENT, AND WORSE THAN THE ADDENDUM STATES**

A conforming adapter; a sink that `object.__setattr__`s the outcome it was just handed.

```
tree: /srv/crash-detector-wo2r3-audit5/src/crash_detector/collectors/runner.py
CONTROL  outcome=OK payload={'reading': 0.25} rows=1
         key=('src.h','2026-08-22T11:59:59Z') admitted=True
ESCAPE 3 what the sink SAW at record time : [('OK', {'reading': 0.25}, 2026-08-22 11:59:59+00:00)]
         what collect RETURNED afterwards : {'reading': 999.0}  2000-01-01 00:00:00+00:00
         key handed to the ledger         : ('src.h', '2000-01-01T00:00:00Z')
         reading_admitted                 : True
```

**GRADE: ESCAPE 3 IS REAL. VERIFIED INDEPENDENTLY AT `9f7b764`.** `_record` runs in the
`finally`; `_reading_key(source_id, final_outcome)` runs afterwards off the same object; the
`UNIQUE (source_id, source_as_of_utc)` constraint that DECLARED LIMIT 3 names as the carrier
is asked about a key that corresponds to **no recorded observation**, and answers `admitted`.

**AND THE PART THE ADDENDUM DID NOT REACH:** the sink does not merely falsify the *key*. It
replaces `OK.payload` wholesale — see M4.3 ARM5 — so the value returned to the caller in
`CollectionResult.final_outcome` is a payload **the validator never saw and which fails the
schema it was judged by**. That is ESCAPE 1's outcome arriving through a different protocol,
**after** the remediation increment's item A fix, which does not reach it.

**Second half, also confirmed:** a value-returning sink inside the `finally` **replaces** a
propagating `SchemaDeclarationInvalid` with `SinkContractBreach`:

```
[SchemaDeclarationInvalid + value-returning sink] RAISED ...SinkContractBreach: ...returned str
```

The "our own declared schema is unusable" signal is lost and the failure is re-attributed to
the sink. Confirmed by me.

### M4.2 THE SINK / LEDGER / VALIDATOR BEHAVIOUR TABLE — **CONFIRMED ROW FOR ROW, INCLUDING REASON CODES**

Every row below is my own run at `9f7b764`.

| arm | my result | agrees with the addendum? |
|---|---|---|
| sink returns a value | `SinkContractBreach: ObservationSink.record returned str` | **YES** |
| sink writes nothing, returns `None` | `rows_recorded=1`, admitted | **YES** (as declared) |
| ledger returns `"already claimed"` | `LedgerContractBreach: ... returned str; exactly True or exactly False is the contract` | **YES** |
| ledger always `True` | admitted | **YES** (declared limit 3) |
| validator returns `None`, validates nothing | `OK {'reading': 'not a number', 'junk': [1,2]}` | **YES**, byte-identical |
| validator returns a repaired payload | `Malformed`, `schema_error_class='VALIDATOR_CONTRACT_BREACH'` | **YES** |
| validator raises `SchemaDeclarationInvalid` | propagates; row written `Malformed` | **YES** |
| `validator=object()` | `Malformed`, `schema_error_class='VALIDATOR_FAILED_AttributeError'` | **YES** — our wiring defect recorded as the SOURCE misbehaving |
| `sink=object()` | bare `builtins.AttributeError: 'object' object has no attribute 'record'` | **YES** |
| `ledger=object()` | bare `builtins.AttributeError: ... 'admit_if_absent'` | **YES** |

**GRADE: THE TABLE IS ACCURATE. It is the first auditor verification it has had and it
survives it intact.** I looked for a row that was wrong and did not find one.

**RENAME TEST + COUNTERFACTUAL ARM for the refusals I credit** (required by the dispatch):

| refusal credited | counterfactual (CD-D-079) | rename test |
|---|---|---|
| ledger exact-`bool` (`type(verdict) is not bool`) | restore `bool(ledger.admit_if_absent(key))` → truthy `str` **ADMITTED, `admitted=True`**. The exact-type check is doing the work. | **SURVIVES.** Refusal names no identifier of the supplied object. `int 1` → refused; an object with `__bool__` → refused. `class B(bool)` → `TypeError: type 'bool' is not an acceptable base type` — **unevadable by Python itself**. |
| sink `verdict is not None` | discard `sink.record`'s return → the value-returning sink is **ADMITTED**. Doing real work. | **SURVIVES** — type/identity, no name. |
| adapter conformance (`missing_adapter_members`) | (fourth seat's, re-confirmed) `_ADAPTER_CALLABLES` removed → `fetch = 7` reports `()`. | **FAILS, AS DECLARED.** It is a name check and says so. |

**And the asymmetry stands, unmoved:** there is `missing_adapter_members`, and there is **no
`missing_sink_members`, no `missing_ledger_members`, no `missing_validator_members`.** Three
of the four declared-foreign protocols at CD-BP-003 get a bare `AttributeError` from inside
the run — our wiring defect, recorded against the source.

### M4.3 ITEM A's CLOSURE **AND ITS RESIDUES**, TESTED — AND THE RESIDUE LIST IS SHORT BY ONE

DECLARED LIMIT 5 in `collect` names its residues. I tested the closure and every declared
residue, and then looked for one it does not name.

| arm | stored payload | conforms to the schema it was judged by? | declared? |
|---|---|---|---|
| **ARM0** `is_empty` rewrites a TOP-LEVEL key | `{'reading': 0.25}` | **CONFORMS** | **CLOSURE HOLDS** |
| **ARM1** `is_empty` rewrites a nested **exact `dict`** | `{'reading':0.25,'nested':{'reading':0.25}}` | **CONFORMS** | **CLOSURE HOLDS** |
| **ARM2** nested **`dict` SUBCLASS** | `{'reading':0.25,'nested':{'reading': inf}}` | **NO** → `SchemaRejection` | declared OPEN — **TRUE** |
| **ARM3** below `PAYLOAD_SNAPSHOT_MAX_DEPTH` (measured = **32**) | innermost `reading` = `inf` | **NO** | declared OPEN — **TRUE** |
| **ARM4** the **VALIDATOR** mutates while judging | `{'reading': inf}` | **NO** → `SchemaRejection` | declared "NOT COVERED AT ALL" — **TRUE** |
| **ARM5** the **SINK** rewrites `OK.payload` after `_record` | `{'reading': 999.0, 'smuggled': 'never validated'}` | **NO** → `SchemaRejection` | **NOT DECLARED ANYWHERE** |

**FINDING — ITEM A'S RESIDUE IS UNDERSTATED BY EXACTLY ONE PROTOCOL.** DECLARED LIMIT 5
enumerates three residues and names the validator explicitly as uncovered. **It does not name
the sink**, and the sink reaches the same outcome — an unvalidated, schema-violating value on
a governed `OK.payload` — by a strictly later route that the snapshot cannot reach by
construction, since the snapshot is taken before the row is written and the sink is handed the
stored object.

This is the pattern the dispatch told me was this project's most-found defect — *"an
understated residue… a fix that closed less than it says is worse than no fix, because the
declaration is what a reader stops reading at"* — **inside the remediation increment that was
dispatched to fix an understated residue.**

**BOTH HALVES OF THE T2 ESCAPE-1 CLAIM ARE TESTED AND BOTH ARE TRUE**: closed for the top
level and for exactly-`dict` nesting (ARM0, ARM1); still open for a `dict` subclass nested
inside (ARM2) and for anything below the depth cap of 32 (ARM3). **The Engineer's claim about
its own fix is accurate in both directions.** I looked for it to be overstated and it is not.

## M5 — T13, THE TWELFTH PLANT: **EVIDENCE, NOT DECORATION.** BITTEN BY ME, WITH THE AXIS CONTRAST

`plants/CD-AC-005/CD-RT-002-CONSTRUCTORS-ESTABLISH-FROM-THE-DECLARED-FIELD-LIST.patch`,
held to the F12 standard AND the new BITTEN standard (PO-DECISIONS-0011 ruling 4).

**Instrument SHA-verified byte-identical before anything else** — throwaway extraction's copy
vs `git cat-file -p 9f7b764:tools/register/check_constructor_field_establishment.py`:
`48679d2bc5b2ac8ceef427023e553d37f64e65716bbbe6c90ac1d80636479382` on both. **The instrument
that failed is the instrument that ships**, and it is unchanged by the patch (re-hashed after
apply: same digest).

```
CLEAN arm established FIRST : exit 0 · PASS — 101 assertions, 0 violations
git apply --check           : OK        git apply : APPLIED FOR REAL
VIOLATED arm                : exit 1
  VIOLATION src/crash_detector/engine/config.py:392
    rule: FIELD_ESTABLISHMENT_NOT_DERIVED_FROM_THE_DECLARED_FIELD_LIST
    what: Judgement.Verdict is a PUBLIC FROZEN type ON A JUDGEMENT PATH declaring 2 field(s)
          ['score','breached'], and it carries no @establishes(...)
```

**RUNTIME ARM (runtime claims need runtime proof), mine:**
`Judgement.Verdict(score=<object>, breached='maybe')` → **CONSTRUCTED AND ACCEPTED**;
`is_establishing_type(Judgement.Verdict) = False`. The plant is a real unguarded type, not a
static-only artefact.

### M5.1 THE AXIS CONTRAST — I ASKED WHICH AXIS THE **NEW** EVIDENCE VARIES

PO-DECISIONS-0011 ruling 2 is the Product Owner's finding against itself for accepting
contrast evidence *"without asking which axis it varied"*, harvested with *"a rule that binds
seats binds their Product Owner"*, and the dispatch names it an open invitation. **So I asked
it of the new evidence.** Same patch, same file, same type — **each SHA run with ITS OWN copy
of the instrument** (CD-PL-F98):

| | instrument sha256 | clean | + the SAME plant | runtime |
|---|---|---|---|---|
| `531c95c` | `173a3255…9be759` | exit 0, `PASS — 97 assertions` | **exit 0, `PASS — 97 assertions, 0 violations`** | `Judgement.Verdict(...)` **ACCEPTED** |
| `9f7b764` | `48679d2b…479382` | exit 0, `PASS — 101 assertions` | **exit 1, `FAIL — 1 violation`, NAMED in the ledger** | `Judgement.Verdict(...)` **ACCEPTED** |

**THE ONLY VARIABLE BETWEEN THE TWO VIOLATED ARMS IS THE INSTRUMENT'S TRAVERSAL.** The file,
the patch, the type, the package, the name and the runtime behaviour are identical and
measured identical. **The axis varied is exactly the axis the proposition names.** Item B's
widening is proved, by me, against the standard the Product Owner wrote against itself.

**T13 VERDICT: PASS. The twelfth plant is evidence.** I went looking for it to be decoration
and it is not. This is the strongest single piece of work in the remediation increment and I
record it as plainly as I record the defects.

## M6 — **T8: THE ELEVEN CLASS-2 SWEEP ITEMS, MEASURED FOR SUBSTANCE. THE FIRST TIME ANY SEAT HAS.**

CD-D-130 holds eleven dispositions unwritten waiting on this. I did not hurry it.

**Decomposition confirmed by my own run at `9f7b764`:** 15 violations = 13 `UNDECLARED
ADMISSION` + 2 `UNDECLARED MODULE`. Ten admission sites + one module in
`crash_detector.admission` = **the eleven**. Three admission sites + one module in
`crash_detector.establishment` = **the four**. 11 + 4 = 15. Unmoved by the remediation
increment, exactly as declared.

I read each of the ten sites in the source and tested the ones where substance was possible.
**They are NOT one category. They are three, and the record has never said so.**

### CATEGORY A — ONE REAL DEFECT, AND IT FALSIFIES A SHIPPED SENTENCE

**Item: `crash_detector.admission::_is_defined_in_a_class_body DUCK: getattr(entry_point, '__qualname__', '')`**

`_is_defined_in_a_class_body`'s own docstring, verbatim from the source at the target:

> *"It is a property of where the ``def`` was written and **it is not something a caller can
> influence**."*

**THAT SENTENCE IS FALSE AND I FALSIFIED IT BY MEASUREMENT.** `__qualname__` is an ordinary
writable attribute on a function object. One assignment, no class, no import:

```
tree: /srv/crash-detector-wo2r3-audit5/src/crash_detector/admission.py

def free_function(cls, other): ...
  _is_defined_in_a_class_body(free_function)      = False
  _signature_parameters -> ['cls','other']  skipped: []

free_function.__qualname__ = "Faked.free_function"          # ONE STRING ASSIGNMENT
  _is_defined_in_a_class_body(free_function)      = True
  _signature_parameters -> ['other']        SKIPPED: ['cls']

door = admits(other=int)(free_function)
  admission_faults(door) = ()                     <- NO FAULT REPORTED
  door(<a live object>, 3) -> BODY RAN            <- FIRST ARGUMENT ARRIVED
                                                     UNESTABLISHED AND UNDECLARED
```

**COUNTERFACTUAL ARM (CD-D-079), same code without the one assignment:**

```
UndeclaredParameter: free_function2 is a FAULTED door and every call to it is refused.
parameter 'cls' is in the signature of free_function2 and was NOT declared to admits().
```

**One writable attribute converts a FAULTED, always-refusing door into a silently-passing
one that reports no fault.** The skip is gated on the parameter being named in
`_RECEIVER_NAMES` (`self`/`cls`), so the reach is bounded — and the docstring itself records
that `assert_closed_presentation_surface(cls)` on the serving path is a real module-level
function with a parameter named `cls`. **The bound is one identifier wide, not zero.**

**RENAME TEST:** the refusal that normally holds names the parameter, not a structure — it is
*defeated* by a name (`__qualname__`) and *triggered* by a name (`cls`). **It is a vocabulary
guard on both sides.**

**Reachability, stated honestly:** setting `__qualname__` requires in-process code that can
reach the function object before decoration — the same bar as the routes `admission.py`'s own
DECLARED LIMIT 6 lists. It is not a route from a foreign adapter. **It is a real defect of
bounded reach, and it is the one of the ten that has substance.**

### CATEGORY B — THREE SITES WHOSE CONSEQUENCE IS TEST CREDIBILITY, NOT PRODUCT JUDGEMENT

`admission_faults`, `declared_admissions`, `is_admitting_door` — the introspection trio.
**Measured:** each believes any object that carries the attribute.

```
is_admitting_door(Liar())    = True
declared_admissions(Liar())  = {'x': 'whatever'}
admission_faults(Liar())     = ()
```

**And measured: they are called from NO module under `src/`, and not by the sweep.** Their
only callers are `tests/test_admission.py`, `tests/test_judgement_path_doors.py` and
`tests/test_collector_runner.py`. So the consequence of a lie here is that **a test believes a
claim an object makes about itself** — which is already CD-ENG-WO2R3-F13's subject, arrived at
from the other side. Their honest disposition is neither `OUT_OF_BOUND` nor `ESTABLISHED`; it
is *"reached only by carriers, and a carrier that asks an object about itself is a carrier
that can be told anything."* **No existing disposition word says that.**

### CATEGORY C — SIX SITES THAT CONSUME A DECLARATION AUTHORED IN SOURCE AT DECORATION TIME

`_EstablishedHere.__call__ isinstance(because, str)`; `_compile` ×3 (`_Admission`, `tuple`,
`type`); `_type_tuple isinstance(value, type)`; `each_of isinstance(within, tuple)`. Every one
consumes a value a developer wrote inside `@admits(...)` in the artefact. They are the
`OUT_OF_BOUND`/`OWN` shape and I found no route to them that a caller controls.

### AND THE UNDECLARED MODULE — **THE "SHOULD NEVER HAVE ENTERED THE CLOSURE" ANSWER IS WRONG, AND I CAN PROVE IT**

The most available disposition for `crash_detector.admission` is *"it is the mechanism, not a
judgement path; it entered the closure only because judgement modules import it."* **Category
A refutes that.** A tier-1 admission inside `admission` decides **whether a judgement-path
door establishes its arguments at all**. That is not adjacent to the deciding path; it is
upstream of every point on it. **`crash_detector.admission` belongs in the closure, and the
sweep denying by default was right, and the reason it was right is stronger than any record
has yet stated.**

### T8 VERDICT

**MEASURED. The eleven are not eleven of a kind.** One is a real defect that falsifies a
shipped sentence (`_is_defined_in_a_class_body`); three are carrier-credibility items with no
existing disposition word that fits; six are legitimate `OUT_OF_BOUND`/`OWN`; the module entry
is correct and must not be dispositioned away. **The declaration is NOT being used to park a
real defect — but it has been holding one, unread, for four increments, and nobody had looked
at the ten items one at a time until now.**

**On the CD-D-127/CD-D-130 sequencing invitation — I DISAGREE WITH THE FOURTH SEAT, and I am
the first seat with standing to, because I actually measured T8.** The fourth seat argued to
keep the sequencing on the ground that its best result came from disbelieving a settled
disposition. That argument is about *dispositions already written*. **It says nothing about
the cost of leaving eleven items with NO disposition through four increments and five
auditors — which is what actually happened, and the cost was that Category A sat unexamined
in the admission mechanism the whole time.** The right rule is not "disposition after audit";
it is **"a deny-by-default instrument's output is READ ITEM BY ITEM at the boundary that
creates it, and the disposition is written after audit."** Reading is not dispositioning.
Nobody read.

## M7 — **T9: THE BLINDNESS WINDOW. ANSWERED, AND THE ANSWER IS M3.**

The question the Product Owner escalated F15 into: *"WHAT ELSE COULD SURVIVE TWO
RECONCILIATIONS? Answer that and you have the class, not the instance."*

**MY ANSWER, MEASURED, AND IT IS WORSE THAN TWO RECONCILIATIONS.** `src/crash_detector/admission.py`
DECLARED LIMIT 6, verbatim from the source at the target, which I read myself:

> **(a) THE `__closure__` REACH** … *"CPython offers no way to prevent it, so it is a property
> of the language and not of this design, and **it is true of this codebase's own
> `_absence_is_never_a_number`, which has passed three gates**."*
>
> **(b) THE `__wrapped__` ATTRIBUTE — THIS HALF IS CLOSED HERE**, *and the closure is measured
> (`tests/test_admission.py::test_a_door_publishes_no_way_round_itself`)…*

**PARAGRAPH (a) NAMES `_absence_is_never_a_number` BY NAME. PARAGRAPH (b), FORTY LINES LATER,
CLOSES `__wrapped__` — "HERE", MEANING FOR `admits` ONLY. THE MODULE NAMED IN (a) IS NOT
CLOSED, AND NOWHERE DOES THE RECORD SAY IT IS NOT.** `establishment.py:506` then closed the
same half a third time, for `@establishes`. **Two closures, one explicit naming of the third
site, and the third site left open** — which is the M3 finding, live at my target and
demonstrated at runtime with a counterfactual.

**SO THE CLASS IS NOT "AN INSTRUMENT OUTSIDE THE REGISTER GLOB."** That is F15's instance and
CD-PL-F86's generalisation, and it is true but narrow. **The class is: A DECLARATION THAT
NAMES A SIBLING SITE AND THEN CLOSES ITSELF.** The reader's eye takes the naming as coverage.
Six increments, four auditors, three Project Lead reconciliations and a Product Owner all read
paragraph (a) — it is *quoted in the increment-6 dispatch material* — and nobody asked whether
(b) covered what (a) named.

**That is a mechanically detectable class**, which is what makes it worth having: *for every
declared limit that names a site outside its own module, is that site's carrier measured or
merely named?* I did not have budget to run that sweep across the tree. **I state it as the
class and as an unrun measurement, not as a finding I have discharged.**

**T9 VERDICT: MEASURED AND ANSWERED.** The window's mechanism is a naming-taken-for-coverage
defect, and I found a live instance of it, at runtime, with a counterfactual. F15 itself is
not closed and I do not close it.

## M8 — **T10: CD-ENG-WO2R3-F10, STILL OPEN. MEASURED, AND ITEM C MOVED IT WITHOUT DISCHARGING IT.**

F10: *"the `ESTABLISHED_HERE` exemption set DOUBLED, 8 → 16 … REVIEWER ATTENTION IS THE WHOLE
CONTROL … a set of sixteen is materially harder for a reviewer to hold than a set of eight."*
Its proposed remedy: *"a second CATEGORY on the declaration — establishment door versus
declared limit — so the two kinds are counted separately at every run rather than by a reader
reading reasons. The check already partitions the two groups for `collectors/` only."*

**MEASURED BY ME AT `9f7b764`:**

- `ESTABLISHED_HERE uses: **16**` — **unchanged from `531c95c`, which I also ran.** The set has
  not shrunk and it has not been categorised globally.
- The partition is **still `collectors/` only**: `"(also under collectors/, and NOT CD-BP-003:
  4 ESTABLISHMENT DOOR parameter(s)…)"`. The remaining eight uses in `dials/` and `engine/`
  are listed with no category. **F10's proposed remedy is NOT implemented.**
- What item C DID add, and it is real: aliases now resolve, and a new line prints
  `MODULES BINDING A NON-LITERAL SPELLING OF ESTABLISHED_HERE: 0`.

**MY CONTRAST FOR ITEM C, each SHA with ITS OWN instrument** (`@admits` literal,
`ESTABLISHED_HERE as _EH`, planted in `collectors/validation.py`):

| | `ESTABLISHED_HERE uses` | non-literal spellings | `tests/test_judgement_path_doors.py` |
|---|---|---|---|
| `531c95c` + aliased door | **16 — INVISIBLE**, exit 0 | (line absent) | **22 passed — blind** |
| `9f7b764` + aliased door | **17 — SEEN**, exit 1 | **1** | **5 failed, 19 passed — caught** |

**ITEM C IS PROVED. The fourth seat's §2.4 aliasing route is CLOSED, and the correction the
dispatch disclosed to me (that `test_admission.py` also caught it) is beside the point: the
door-side carrier now catches it too, which is what §2.4 said no carrier did.**

**T10 VERDICT: F10 REMAINS OPEN AND UNDISCHARGED, and it is now MEASURED rather than
asserted.** The set is 16, the categorisation is partial, reviewer attention is still the whole
control for eight of the sixteen. Item C reduced the *concealability* of the set and did
nothing to its *size* or its *legibility*, which is what F10 is about. **Nobody has claimed
otherwise — I checked — and I record that the record is honest here.**

## M9 — **T4 / T11 / ITEM B: THE TRAVERSAL WAS WIDENED FOR CLASSES AND NOT FOR NAMES. "EXACTLY TWO" IS FALSE.**

`check_constructor_field_establishment.py` DECLARED LIMIT 5, verbatim:

> **THE RESIDUAL REACH LIMITS ARE EXACTLY TWO. MEASURED, NOT LISTED FROM IMAGINATION.**
> (i) a class with no `ClassDef` node · (ii) a module outside `src/crash_detector/`

**THERE IS A THIRD AND I MEASURED IT.** `_classes()` was rewritten to `ast.walk` (line 397).
**`_module_level_names()` at line 580 still reads `for node in tree.body`** — twelve lines
away, the identical idiom, in the same file, in the increment dispatched to eliminate it. And
RULES B and C reach types *through names*: the check's own DEFINITION says so —
*"RULES B AND C RESOLVE MODULE-LEVEL NAMES TO A FIXPOINT, because both reach types through a
name — `one_of(*READING_CONSTRUCTORS)` spells no constructor and `outcome: 'FetchOutcome'`
spells no outcome."*

**THE ESCAPE, MEASURED. One `if True:` around ONE module-level assignment in
`observations.py`** — `FetchOutcome = Union[OK, FetchFailed, Malformed, Empty]`:

```
tree: /tmp/cd-asr5-b-t4/src/crash_detector/observations.py

BASELINE   99 class(es) examined; 33 in the class (32 fielded, 1 vacuous); 101 assertions; EXIT 0
+ if True:  99 class(es) examined; 30 in the class (30 fielded, 0 vacuous);  91 assertions; EXIT 0
                                                              CD-RT-002-...: PASS — 0 violations
package still imports; FetchOutcome resolves identically at runtime
```

**`FetchFailed`, `Malformed` AND `Empty` LEAVE THE CLASS AND THE INSTRUMENT REPORTS PASS.**
Confirmed from the `--why` ledger in the escaped arm:

```
OUT  observations.py:101 FetchFailed — clause (3): RULE A — no; RULE B — no; RULE C — no.
OUT  observations.py:124 Malformed   — clause (3): RULE A — no; RULE B — no; RULE C — no.
OUT  observations.py:171 Empty       — clause (3): RULE A — no; RULE B — no; RULE C — no.
```

All three are still `@establishes`-decorated and `is_establishing_type` is `True` for all of
them at runtime. **The types did not become unguarded; the INSTRUMENT stopped asserting over
them, silently, at exit 0.** That is F-A3's shape by a route nobody has named, and `Empty` is
the very member PO-DECISIONS-0010 ruling 1 widened the class to include and item D was
dispatched to decorate.

**AND THE COUNT ASSERTION DOES NOT REACH IT.** Item B2's headline reassurance — *"THE COUNT IS
ASSERTED, NOT PRINTED"* — reads, in the escaped arm: `the adjudication path finds 99; …finds
99. IN THE INDEPENDENT READING AND NEVER ADJUDICATED: 0. ADJUDICATED BUT NOT INDEPENDENTLY
FOUND: 0.` **Both derivations assert the EXAMINED set. Neither asserts MEMBERSHIP.** The
assertion is sound and it is orthogonal to this escape.

### M9.1 AND I CHECKED FOR A CARRIER, AND THERE IS ONE — WHICH RESIZES MY OWN FINDING

I ran the full suite in the escaped arm rather than stopping at the green instrument:

```
FAILED tests/test_field_establishment.py::test_the_static_enumeration_and_the_runtime_population_are_the_same_class
FAILED tests/test_field_establishment.py::test_the_vacuously_satisfying_members_are_exactly_this_set
4 failed, 1547 passed          (2 of the 4 are the baseline guarded failures)
```

**THE ROUTE IS CARRIED.** I am recording that against my own finding, in the same breath as the
finding, because a seat that reports the green instrument and not the red suite is doing the
thing this whole project exists to stop. **The finding therefore is NOT "three types leave the
class uncarried." It is:**

1. **DECLARED LIMIT 5's "EXACTLY TWO … MEASURED, NOT LISTED FROM IMAGINATION" IS FALSE.**
   There is a third residual reach limit, it is one `sed` from the fix that was applied, and
   the increment's own probe found this exact `if True:` shape *for classes* and did not carry
   it across to names. **A declaration that says "exactly two" is a stronger claim than one
   that says "two known", and it was wrong in the stated direction — which is this project's
   most-found defect, at instance twelve, inside the fix for instance nine.**
2. **The declared register command exits 0 and says PASS while the class shrinks by three.**
   A reader running the instrument the register names sees green. The carrier is a test the
   limit does not mention, because the limit does not mention the limit.
3. **`_module_level_names`'s own docstring says the flat namespace "can only enlarge the class,
   never shrink it, which is the safe direction."** That is true of what it finds and says
   nothing about what it cannot see — and a reader takes it for both.

### M9.2 WHAT IS RIGHT ABOUT T4, SAID AS PLAINLY AS WHAT IS WRONG

**The two derivations ARE genuinely independent, and I checked rather than accepted it.**
`_ClassCounter` re-reads each file's bytes from disk, re-parses them, and descends by
`ast.NodeVisitor` dispatch with its own qualname stack — sharing no parse, no list and no
object with `_classes`'s `ast.walk`. **They are not two readings of one list wearing different
names.** And the instrument declares precisely what they do NOT give independence from — the
`ast` module and the file set — with *"Two derivations of one input are two derivations, not
two inputs."* **That is exactly right and it is better than the ruling asked for.**

**F-A2 WAS SUPERSEDED, NOT QUIETLY DROPPED.** DECLARED LIMIT 5 quotes the fourth seat's escape
in full, names it as the supersession, and records the population/exit/assertion figures it
produced. Checked, as the dispatch instructed.

## M10 — T7: THE THREE (FOUR) `variants/WO-2R` ROUTES, RE-TESTED AT `9f7b764`. **NOBODY HAD.**

The Project Lead declared these unverified at my target. One pristine `/tmp` extraction per arm.

| patch | apply at `9f7b764` | result | ctor | doors |
|---|---|---|---|---|
| `V03-dynamic-constructor-on-the-absence-branch` | `-C1` (context drift) | **CLOSED** — `test_evaluate.py` 11 failed / 34 passed; full suite 13 failed, 1538 passed | **0** | 1 (baseline) |
| `E04-module-level-constant` | `-C1` | **CLOSED** — identical signature | **0** | 1 |
| `V06-magnitude-from-configuration-not-a-literal` | `-C1` | **CLOSED** — identical signature | **0** | 1 |
| `V05-decorator-installs-the-member` | `git apply` and `-C1` BOTH FAIL; ports with `patch --fuzz=5` (fuzz 3) | **CLOSED** — `ReadingSurfaceViolated: Degraded carries undeclared member(s) ['magnitude']` at import | — | — |

**All four remain closed at my target. `ctor EXIT=0` in all three applying arms confirms the
fourth seat's finding independently: they are NOT closed by increment 5's machinery.**

**AND A CONVERGENCE THAT IS MINE:** the layer that closes V03, E04 and V06 is
`refuse_a_number_without_its_inputs` — **the guard whose `__wrapped__` bypass I demonstrated
live at M3.** Three of this project's four historic CD-ASR-F03-class routes are held shut by a
post-condition a caller can step around with one documented attribute. **That is the single
most load-bearing consequence of M3 and neither finding is legible without the other.**

## M11 — T12: THE SEVEN REPAIRS, EACH AS AN ATTACKABLE CLAIM

| item | claim | my verdict |
|---|---|---|
| **A** — stored payload is the validated payload | closed for top level and exactly-`dict`; open for `dict` subclass, below depth 32, and the validator | **PROVED IN BOTH DIRECTIONS** (M4.3 ARM0–ARM4). **RESIDUE UNDERSTATED BY ONE PROTOCOL** — the SINK (ARM5) is in no residue and reaches the same outcome. |
| **B** — both instruments walk the whole AST | doors 27→28 subjects; ctor catches the nested plant | **PROVED** for doors (found `guarded`) and for ctor (T13 axis contrast, M5.1). **BUT NOT APPLIED TO `_module_level_names`** (M9), and at the target the ctor's examined count is **99 at both SHAs** — `src/` contains **zero** nested `ClassDef`s, so the ctor widening changes nothing about the shipped tree and is proved only by plants. Correct, prophylactic, and **not stated**. |
| **B2** — count asserted against a second independent derivation | genuinely independent | **PROVED** (M9.2). Asserts the examined set, not membership. |
| **C** — `ESTABLISHED_HERE` resolved through aliases; 8/5 → 16/9 | the aliasing route is closed | **PROVED** by my two-SHA contrast (M8): 16-invisible/22-passed at `531c95c` → 17-seen/5-failed at `9f7b764`. |
| **D** — `@establishes()` on `Empty` | `Empty` becomes establishing; P7 holds for it | **PROVED**: `is_establishing_type(Empty)` **False → True**; add one field and every construction — *including previously valid `Empty()`* — raises `UndeclaredField` at `9f7b764`, while both are **ACCEPTED** at `531c95c`. |
| **E1** — the `required-tests.yaml` "closed and not a limit" sentence | rewritten to measured reach | **CORRECT.** The superseded wording is quoted, not deleted; the correction is in the right direction. |
| **E2/E3** — `admission.py` / `establishment.py` "it needs the ability to execute code inside the package" | measured at ZERO LINES; it IS a caller route | **CORRECT, AND I RE-MEASURED THE MECHANISM MYSELF AT `9f7b764`**: a hostile adapter importing nothing from `crash_detector` reached `crash_detector.collectors.runner`'s module globals through its own call frame, with `FetchedResponse` rebindable — `outcome=OK`, `admitted=True`. **The new wording is right and the old wording was wrong in both directions.** |

**SIX OF SEVEN PROVED. Item A is proved as to its closure and understated as to its residue.**
Two implementers and a reconciler agreeing is worth less than one auditor disagreeing — so I
went looking for disagreement, and on six of seven I did not find it. **That is a result and I
record it as one.**

---

# THE VERDICT

## FINGERPRINT RE-TAKEN AT THE END — AND IT MOVED. HERE IS WHY, AND IT IS MINE.

```
SHA         9f7b7640f692442e22a47ecac3d4a643057729d5     unchanged
TREE        224debf13475acdb10944bfa201a82c5d3d199d8     unchanged
PORCELAIN   0 lines                                      unchanged
git diff HEAD --stat                                     0 lines
untracked non-ignored files                              0

FINGERPRINT (dispatch recipe, verbatim)          24d66d0ef56634d973011e8793d208e92fc560ecf85473ca969786318a333c9c
FINGERPRINT at my start / dispatch value         50b356ac2de1a404b75a6fb9e478fe5d4141c4fdc6ad34ddfbfcd4a5a92ee7b9
FINGERPRINT excluding ./.pytest_cache            50b356ac2de1a404b75a6fb9e478fe5d4141c4fdc6ad34ddfbfcd4a5a92ee7b9   <- EXACT MATCH
```

**THE GOVERNED TREE DID NOT MOVE. THE DELTA IS A `.pytest_cache/` DIRECTORY THAT I CREATED**
by running the project's own suite in the audit worktree (`stat`: 2026-08-23 00:16). It is
`.gitignore`d, which is why `git status --porcelain` reads 0 and why nothing warned me. **I
have not deleted it** — removing evidence of my own contamination to make a control read clean
is the exact move I am here to catch in others. The Project Lead should note it exists.

**AND THAT IS A FINDING AGAINST THE CONTROL, NOT ONLY AGAINST ME.** The dispatch says of this
recipe: *"If it moved, something mutated under you and your verdict is about a tree that no
longer exists."* **It moved, and nothing mutated.** The recipe walks every file except `.git`,
so it cannot distinguish a source edit from a bytecode or pytest cache — and it will now fire
for **any** seat that runs the test suite in the worktree it was told to audit. A control that
raises a maximum-severity alarm when an auditor does the thing the dispatch orders it to do is
a control that trains auditors to dismiss it. **The fix is one `-path ./.pytest_cache -prune`,
or comparing `git rev-parse HEAD^{tree}` plus `git status --porcelain --ignored`.**

## OVERALL: **RED**

**And a RED here is not a criticism of the remediation increment.** I attacked all seven of its
repairs and six are proved, one of them (T13/item B) by a contrast cleaner than anything else
in this record. The Engineer named three routes to green on CD-D-146 and took none of them.
**The RED is about the tree WO-2R3 asks to be graded, and about three declarations in it that
are wrong in a stated direction.**

### THE FOUR GROUNDS, EACH REPRODUCED BY ME AT `9f7b764` WITH A COUNTERFACTUAL

1. **ESCAPE 3 IS LIVE, UNMOVED, AND UNDECLARED — AND IT SATISFIES EVERY CLAUSE OF THE SENTENCE
   THE FOURTH SEAT'S RED RESTED ON.** That sentence was: *"ESCAPE 1 … is a correctness defect
   in the shipped ingestion path, it has a two-line counterfactual fix, and I reproduced it
   myself."* ESCAPE 3 is a correctness defect in the shipped ingestion path (a declared-foreign
   sink puts an unvalidated, schema-violating value on a governed `OK.payload` and hands the
   ledger a reading key naming a period no row records, `admitted=True`); it has a bounded fix;
   and I reproduced it myself. **The ground of the RED was not removed. It moved one protocol
   to the left, and unlike ESCAPE 1's residues it is named nowhere.**
2. **`__wrapped__` IS LIVE ON THE CD-ASR-F03 GUARD** (M3), closed in both sibling mechanisms,
   named by `admission.py` DECLARED LIMIT 6(a) and left open by 6(b), asserted-as-required by a
   shipped test, and holding shut three of the four historic WO-2R escape routes (M10).
3. **A SHIPPED SENTENCE IS FALSE IN THE ADMISSION MECHANISM** (M6 Cat A):
   *"it is not something a caller can influence"* — one attribute assignment turns a FAULTED
   door into a silently-passing one reporting no fault.
4. **"THE RESIDUAL REACH LIMITS ARE EXACTLY TWO" IS FALSE** (M9): there is a third, one `sed`
   from the fix that was applied, and the declared register command exits 0 while three
   governed types leave the class. It is carried by a test, and I say so.

### NEXT SAFE GATE

**Product Owner disposition of this verdict and of CD-D-146. Then ONE bounded Engineer
increment, six items, each independently checkable, none requiring a design decision:**

- **(a)** ESCAPE 3 — snapshot the outcome before `_record`, or derive the reading key from the
  recorded row rather than from the live object. Carrier: a test that a sink mutating its
  argument cannot change `CollectionResult.final_outcome` or `reading_key`.
- **(b)** `delattr(guarded, "__wrapped__")` in `_absence_is_never_a_number`, as `admits` and
  `establishes` already do — **and `tests/test_evaluate.py:692` must be rewritten first**,
  because it currently asserts the bypass is present. Replace it with a behavioural assertion.
- **(c)** `_module_level_names` to `ast.walk`; DECLARED LIMIT 5 corrected from "EXACTLY TWO"
  to its measured count; item A's residue list to name the SINK.
- **(d)** `_is_defined_in_a_class_body`'s docstring corrected, and the skip made not to depend
  on a writable attribute (compare the code object, or require the receiver name AND a bound
  `__self__`).
- **(e)** `plants/MANIFEST.md:96` — "Eleven tests, eleven patches" is now false *because of this
  increment*; and CD-D-139's line 1148-1149 still stands, as ruled.
- **(f)** the fingerprint recipe in every dispatch that carries it (see above).

**CD-D-146 requires a RULING BEFORE (b) can be scoped**, because whichever way it goes the
instrument changes. **Nothing above is authorised by me. I grade; the Product Owner
dispositions (PBG-AUTH-003).**

## PER-CRITERION GRADES

### **T2 — CD-BP-003, THE ADAPTER BOUNDARY: RED. UNMOVED — BUT FOR A DIFFERENT ESCAPE.**

I came to this expecting to move it up, and the evidence turned.

**What moved UP, and I say it first:** ESCAPE 1 is genuinely closed at the layer it named. I
tested both halves of the claim and **both are true** — closed for the top level and for
exactly-`dict` nesting, still open for a nested `dict` subclass and below depth 32 — and the
declaration is accurate in both directions. ESCAPE 2's sentence is corrected honestly, in the
right direction, with the superseded wording quoted, and I re-measured the mechanism myself.
Item C closes the aliasing route. **Everything the increment was dispatched to do at this
boundary, it did.**

**What holds it at RED:** the surface still admits, through a declared-foreign protocol at the
same door, an unvalidated schema-violating value onto a governed type, and falsifies the
uniqueness key the declared limit names as its carrier — `admitted=True`, nothing refuses it,
and no declaration anywhere mentions it. Three of the four declared-foreign protocols still
have no conformance check at all (`sink=object()` → bare `AttributeError`), while the fourth
has `missing_adapter_members`.

**WHAT WOULD MOVE T2 TO AMBER, stated so it can be tested rather than argued:** the sink route
closed or declared with the same specificity item A declares its three, and the reading key
derived from a recorded row rather than a live object. **What would move it to PASS:** a
conformance-and-return closure over `sink`, `ledger` and `validator` equal to the one `adapter`
has, with counterfactual arms.

### **CD-AC-002 — "The two dials are never blended": AMBER. NOT CLOSED. UNCHANGED.**

I looked for a route from anything I found to a blend and did not find one. My M3 bypass runs
on the dial path but its consequence is CD-AC-001/CD-ASR-F03's subject — a value without its
inputs — not a combination of two dials. My M9 route drops `FetchFailed`/`Malformed`/`Empty`
from the measured class, not the dial types. The fourth seat's blockers all stand and I
re-confirmed none of them was quietly repaired.

**WHAT WOULD MOVE IT:** the criterion's subject types (`DialSet`, `EquityCrashScore`,
`MonetaryDebasementScore`) asserted into the class by a rule that does not depend on a door's
declaration — the Product Owner's declared floor turned from a `check.note` into a
`check.violation`. That is one line and nobody has written it.

### **CD-AC-005 — "WITNESS UNAVAILABLE ≠ WITNESS AGREES": AMBER. NOT CLOSED. UNCHANGED GRADE, REASONING WEAKER AGAIN.**

The fourth seat set an explicit RED test: *"a demonstrated route from any foreign or
caller-supplied input to a `WitnessPanel` value of type `Agrees` that did not pass
`Agrees.__init__`."* **I DID NOT MEET IT AND I DID NOT HAVE BUDGET TO HUNT IT. I say that as
plainly as that seat did.** The witness path does not pass through `collect` and I did not
disprove that.

**But the mitigation the AMBER leans on is dented in a third place.** F-A4's route was excused
as needing in-process execution; ESCAPE 2 showed that bar is handed to callers at the
declared-foreign door (re-measured by me); **and M3 now shows the CD-ASR-F03 guard itself is
stepped around in-process by one documented attribute with no closure-cell archaeology at all.**
Each of the three is separately survivable. The principle that "in-process execution is a high
bar on this project" has now been measured false three times by three parties, and it is the
load-bearing premise of this criterion's AMBER rather than its RED.

**WHAT WOULD MOVE IT TO RED:** the fourth seat's test, met. **What would move it to PASS:**
`Agrees` sealed against `__new__`/`__dict__` construction the way `DialMagnitude` already is —
the technique exists in this codebase, in this codebase's own dials layer, and was not applied.

## VERDICT ON EACH NAMED TARGET T1–T13

| | target | verdict |
|---|---|---|
| **T1** | P7 — a new field arrives REFUSED | **PASS**, re-tested against the NEW tree as instructed. Item D changed which types establish, so I re-tested at the member it added: at `9f7b764` adding one field to `Empty` raises `UndeclaredField` on **every** construction including previously-valid `Empty()`; at `531c95c` both are **ACCEPTED**. The property now covers the member the widening added. |
| **T2** | CD-BP-003 | **RED — unmoved, for a different escape.** See above. |
| **T3** | §D scoping incl. CD-D-105 (CD-D-112) | **NOT INDEPENDENTLY ATTACKED.** Reached only through T4/T11, where my finding is about the instrument's reach and not about what §D scopes as a subject. **Stated as a gap, not glossed.** |
| **T4** | the instruments' enumeration AND traversal | **AMBER, with a new finding.** The two derivations are genuinely independent and honestly limited (M9.2); F-A2 was superseded and not dropped (checked). **But "EXACTLY TWO residual reach limits" is false** (M9), and the assertion covers the examined set and not membership. |
| **T5** | the Class-2 sweep exiting 1 | **DECLARATION ACCURATE. NOT CONCEALMENT — BUT NOT HARMLESS EITHER.** I measured `534 sites, 15 violations` and the 11+4 decomposition myself; the bisect matches. **The declaration is not being used to park a defect. It has, however, been holding one unread for four increments** — see T8 Category A. Declaring is not reading. |
| **T6** | GRANT-MATRIX-LIVE / the BITTEN standard | **STANDARD APPLIED, AND THE ONE NEW PLANT IS BITTEN (T13).** I did **not** re-bite GRANT-MATRIX-LIVE — the dispatch says in terms *"YOUR JOB HERE IS NOT TO RE-BITE IT"* — so that is an instructed limit, not a measured one. **On "which other 'cannot be demonstrated' claims are an unset variable": I have one answer and it is T8 Category A.** Eleven items were carried as "cannot be dispositioned yet" for four increments and one of them was a live defect the whole time. Same shape as the unset variable: a true procedural reason for not looking, mistaken for a reason there was nothing to see. |
| **T7** | the three (four) `variants/WO-2R` routes | **CLOSED AT `9f7b764`, RE-TESTED BY ME — NOBODY HAD.** See M10, including `V05`, which no longer applies with `git apply` at all and needs `patch --fuzz`. |
| **T8** | the eleven Class-2 dispositions AS SUCH | **MEASURED. Three categories, not one.** One real defect falsifying a shipped sentence; three carrier-credibility items no disposition word fits; six legitimate `OUT_OF_BOUND`/`OWN`; and the module entry is CORRECT and must not be dispositioned away. See M6. **I disagree with the fourth seat on the sequencing and say why.** |
| **T9** | F15 — the blindness window | **MEASURED AND ANSWERED.** The class is *a declaration that names a sibling site and then closes itself*; the live instance is M3, found at runtime with a counterfactual. See M7. F15 itself is not closed and I do not close it. |
| **T10** | CD-ENG-WO2R3-F10 | **STILL OPEN AND UNDISCHARGED — now measured rather than asserted.** 16 uses at both SHAs; partition still `collectors/`-only; F10's proposed remedy not implemented. Item C reduced concealability and not size. See M8. |
| **T11** | the widened class AND the widened traversal | **THE WIDENED TRAVERSAL DOES NOT SURVIVE INTACT** (M9): it was widened for classes and not for names, and the "exactly two" declaration is false. **On the widened CLASS itself I found no new attack** beyond the fourth seat's and I say so rather than manufacture one. |
| **T12** | the seven repairs | **SIX OF SEVEN PROVED. Item A proved as to closure, understated as to residue.** See M11. |
| **T13** | the twelfth plant | **PASS — EVIDENCE, NOT DECORATION.** Bitten by me to the ruling-4 standard, with the axis contrast run at both SHAs using each SHA's own instrument. See M5. |

## THINGS I FOUND THAT ARE ON NOBODY'S LIST — **THE POINT OF THE SEAT**

1. **`__wrapped__` is live on the CD-ASR-F03 post-condition wrapper** (M3) — closed twice
   elsewhere, the third site named in the record and not closed, its only carrier being the
   attribute itself, and it holds shut three of four historic WO-2R routes (M10). **Severity:
   the highest thing in this verdict.**
2. **`admits`'s own `door(*args, **kwargs)` is `guarded`'s shape, more load-bearing, and
   unflagged** (M2.3), together with three further live instances — invisible purely because
   `admission.py` is not under `engine/serving/collectors`.
3. **The `OPEN_CHANNEL` rule makes the arity-open tension unresolvable inside the current rule
   set** (M2.4), so the Engineer's three-routes-to-green list was incomplete: there is a fourth
   and it is worse.
4. **The `guarded` violation fails the project's own rename test** (M2.1) — one unreachable
   local identifier decides it, and the runtime name is already private.
5. **Item A's residue is short by one protocol — the SINK** (M4.3 ARM5).
6. **`_is_defined_in_a_class_body`'s shipped docstring is falsified by one attribute
   assignment** (M6 Cat A), inside one of the eleven items the project has been blocked on.
7. **`_module_level_names` is a third, undeclared reach limit against a declaration that says
   "EXACTLY TWO"** (M9) — carried by a test, uncarried by the instrument, and one `sed` from
   the fix that was applied.
8. **`plants/MANIFEST.md:96` — "Eleven tests, eleven patches" — was made stale BY THIS
   INCREMENT.** Disclosure 8 asked whether the old stale line survived: it did (1148-1149, as
   CD-D-139 ruled), and the increment's edit was **append-only at line 1203**, so it never
   opened either line. **But by appending "Eleven becomes twelve" it created a SIXTH stale copy
   in the same file** — a count going stale in the act of declaring a count.
9. **The dispatch's own fingerprint recipe raises a maximum-severity false alarm** when the
   auditor runs the suite it was told to run (above).
10. **CD-PL-F97 confirmed by my own count**: six executable probes under `variants/WO-2R3/`,
    **zero** manifest rows each. Disclosed, unremedied, and I confirm the disclosure is exact.
11. **The stale `ACTIVE_WORK.yaml` on the documented manual boot path, reproduced
    independently**: my `pbg boot` in the audit worktree printed `current_work: CD-WO-002` and a
    `next_safe_action` naming `CD-ASR-WO2-01` and branch `wo-2-skeleton`. The fourth seat found
    this; I confirm it is unmoved five work orders later, and it is the record's own
    continuity file.

## WHAT I COULD NOT ESTABLISH — SAID PLAINLY

1. **T3** — I did not independently attack the §D scoping or the CD-D-105 closure.
2. **CD-AC-005's stated RED test** — not met, and not hunted. I ran out of budget before the
   witness path, having spent it on T8/T9/T10, which had never been measured at all.
3. **GRANT-MATRIX-LIVE not re-bitten by me** — by instruction, not by inability. I did not
   verify the environment variables were still unset, so the fourth seat's correction is
   *inherited* by me, not re-measured.
4. **The eleven plants at `9f7b764`** — the Project Lead declared these unmeasured at my
   target and **they are still unmeasured.** I bit the twelfth only. `plants/` health at my
   SHA rests on the fourth seat's `531c95c` figures and nothing else.
5. **The WO-2R3 variant corpus was not re-run by me**, and item B's nine-placement probe and
   item E1's probe were not run by me. **The Engineer's module-level `if True:` claim is
   therefore not verified by me — but I hit the identical shape from the opposite side (name
   resolution rather than class enumeration) without having run its probe, which corroborates
   it independently and is stronger than having re-run it.**
6. **The T9 class as a sweep** — *for every declared limit that names a site outside its own
   module, is that site's carrier measured or merely named?* I state it as the class and as an
   **unrun measurement**, not as a discharged finding. It is the highest-value thing left on
   this tree and it is mechanical.
7. **Whether M6 Category A is reachable from `collect`** — I did not build that chain.
8. **I did not exhaust the `__closure__` reach**, the `_compile` declaration sites under a
   hostile `tuple`/`type` subclass, or the store-level carriers.
9. **This list is not claimed complete.** `admission.py` says of its own limit block:
   *"anyone reading this should assume there is a fourth and should look for it rather than
   check this list."* That applies to mine.

## DECLARATIONS

- **Read-only honoured.** No commit, no `git apply`, no `git worktree add` in the audit tree.
  Every variant ran in a throwaway `/tmp` extraction from `git archive` and was discarded.
  Nothing under `pbg/` was touched. Every probe was run with **each tree's own copy** and its
  `tree:` provenance line read (CD-PL-F98). **My one mutation of the audit directory is the
  `.pytest_cache/` disclosed above, and I have not removed it.**
- **I did not make the doors check green and report it as the tree's state.** M2.1 is labelled
  a rename test on a throwaway in the same paragraph as the result.
- **PBG-AUTH-003: THIS IS NOT AN ACCEPTANCE.** I grade; the Product Owner dispositions.
- **PBG-SOD-001: I am CD-ASR-WO2R3-02**, a fresh seat, none of the two Engineers and none of
  the four prior auditors, and I inherited nothing from the dead first carrier of this seat.
- **Nothing in this document is a number I did not produce in this session**, except where it
  is explicitly attributed to another seat and explicitly not credited.

**Verdict for the record:** SHA `9f7b7640f692442e22a47ecac3d4a643057729d5`, tree
`224debf13475acdb10944bfa201a82c5d3d199d8`, porcelain **0** at start and end, governed-tree
fingerprint `50b356ac2de1a404b75a6fb9e478fe5d4141c4fdc6ad34ddfbfcd4a5a92ee7b9` **unchanged**
start to end. **RED.** T2 **RED**. CD-AC-002 **AMBER, NOT CLOSED**. CD-AC-005 **AMBER, NOT
CLOSED**. CD-D-146: `guarded` is **not** a door as the check means it, the arity tension is
**real and unresolvable inside the current rules**, and **shipping the lane RED was the right
call attached to the wrong story**.
