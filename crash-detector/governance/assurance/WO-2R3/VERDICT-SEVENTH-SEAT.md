# VERDICT — SEVENTH ASSURANCE SEAT, WO-2R3

    actor_id            CD-ASR-WO2R3-04
    role                ASSURANCE_ENGINEER (pbg/roles/assurance-engineer.md, read in full)
    dispatch            governance/dispatch/CD-DISPATCH-WO2R3-ASSURANCE-07.yaml
    decision            CD-D-169 · PO-DECISIONS-0017 ruling 4
    target SHA          686a374e60ff8f18305fa8b665463e0e057dac2b   (branch wo-2r3, detached)
    target worktree     /srv/crash-detector-wo2r3-audit7
    session start       2026-08-23T09:11:32Z   (operator wrapper ceiling: 7200s -> ~11:11Z)

**THIS DOCUMENT IS WRITTEN INCREMENTALLY AND ON PURPOSE.** Instance 1 of this seat ran for two
hours, collected 1699 node-ids, and died at the wrapper ceiling returning NOTHING; under
PBG-CONT-007 its findings do not exist and I have re-derived everything below myself. I removed its
`.pytest_cache/` residue before I started rather than read it. A partial verdict on disk is worth
more than a complete one in a dead context.

---

## 0. BOOT DECLARATION AND TARGET IDENTITY

`cd /srv/crash-detector-wo2r3-audit7 && PYTHONPATH=pbg/tools python3 -B -m pbg.cli boot`

    Verdict          RED — CONTINUITY_REFERENCE_INVALID / RESUME_BLOCKED
    observed_sha     686a374e60ff8f18305fa8b665463e0e057dac2b
    PID              PID.md@441d83166b2f3d0c
    BLUEPRINT        BLUEPRINT.md@6b33d5266bd1b73b   (the LANE's v0.1.0 historical baseline)
    roadmap          UNAVAILABLE

This is disclosure 3 of the dispatch and I agree it is not about the work: a detached audit
worktree reads `main`'s continuity record and cannot resolve it. **I do, however, record that this
means EVERY assurance seat on this project has booted RED and the reading has become furniture.**
An instrument whose alarm is unconditionally true for a whole class of legitimate invocation is not
raising an alarm; it is emitting a constant. That is a live PBG limitation, not a finding against
the target, and I return it as `CONTROL_NOT_VERIFIABLE` for the continuity control in this context.

### Fingerprint, taken by me, at the start

    cd /srv/crash-detector-wo2r3-audit7 && python3 -B tools/audit/tree_fingerprint.py --root .
    files fingerprinted: 509
    EXCLUDED by .gitignore: 5   <-- (the .pytest_cache residue, before I removed it)
    FINGERPRINT: 319e401fc2591dc48b611d101d5330bdb3dbb3bb9824b7bb1c39a11e5b10fc6a
    git status --porcelain | wc -l  ->  0

**BYTE-IDENTICAL to the dispatch's `target_tree_fingerprint`.** I did not inherit the Project
Lead's number; I took it and then compared.

**A small positive finding while I am here (T15).** The PL measured `EXCLUDED by .gitignore: 0`;
I measured 5, because instance 1 had left a `.pytest_cache/`. **The FINGERPRINT is identical
across those two readings.** That is a real, unplanned differential test of the instrument's
exclusion logic — two runs, different ignored-file populations, same hash — and it is stronger
evidence for `tools/audit/tree_fingerprint.py` than anything in its own test file, because neither
party constructed it. It is the CD-PL-F100 fix behaving correctly under an accident.

(Sections below are appended as measured. See section 99 for what I did not reach.)

---

# 1. THE HEADLINE. T18 AND T19 TOGETHER.

## VERDICT ON T18 (IS THE SEALING GREEN EARNED?) — **RED. IT IS NOT EARNED.**
## VERDICT ON T19 (THE ROUTE SET) — **RED. I FOUND A SIXTH ROUTE. AND A SEVENTH, AND AN EIGHTH.**

The dispatch asked for one thing above all others: *"FIND A SIXTH ROUTE. IT IS THE SINGLE MOST
VALUABLE THING YOU COULD RETURN."* and named the settled sentence to disbelieve as **"THE CLASS OF
99 IS SEALED"**.

**THE SENTENCE IS FALSE AT `686a374`, AND IT IS FALSE BY THE INSTRUMENT'S OWN DEFINITION OF ITS OWN
PROPERTY, MEASURED THE INSTRUMENT'S OWN WAY.**

### R6 — `cls.__new__(cls)` then `object.__setattr__(subject, <slot>, FORGED)`

**40 of the 51 classes `check_sealed_against_forged_establishment.py` certifies `SEALED` are
constructible with forged state, of exactly the right type, having executed ZERO lines of package
code.** Measured with `sys.settrace`, package-line counted, value read back — the instrument's own
three disciplines, re-implemented by me and not copied.

Hand-run, fully explicit, at the target (`/tmp/asr7/demo.py`, a throwaway probe; the TREE IS
UNMODIFIED):

    CLASS crash_detector.staleness.StalenessWindow
      __slots__ in vars(cls): True   __dictoffset__: 0
      has __setstate__: False        frozen dataclass: True
      R1 __dict__.update    -> REFUSED AttributeError: 'StalenessWindow' object has no attribute '__dict__'
      R6 object.__setattr__ -> type is exactly StalenessWindow: True
         read back 'seconds' = '__CD_ASR_FORGED__'
         PACKAGE LINES EXECUTED: 0  (none)
         repr of the forged object: StalenessWindow(seconds='__CD_ASR_FORGED__')

*** **THAT IS `StalenessWindow`.** *** It is the class this whole increment is celebrated for. It
is the class in `CD-PL-F119` and `CD-PL-F120`, the one whose forging proved that
`"__slots__" in vars(cls) and not cls.__dictoffset__` was unsound and that two independent readings
had shared a blind spot. **THE INCREMENT CLOSED THE `__setstate__` ROUTE ON IT AND IT STILL FORGES,
BY A SHORTER ROUTE, AND THE NEW INSTRUMENT SCORES IT `SEALED`.**

`OK` (`observations.py`) forges identically — `payload` set to an arbitrary object, zero package
lines. That is the class on the judgement path in Escape 3.

### R7 — the slot `member_descriptor`'s own `__set__`

Same 40 classes. Independent of `object.__setattr__`, in case anyone proposes to guard that name.
`vars(cls)['seconds'].__set__(subject, FORGED)`. Zero package lines. Listed separately because a
remedy that stops R6 and not R7 would be `GUARD_THE_INSTANCE_NOT_THE_CLASS` a fifth time.

### WHY THE INSTRUMENT CANNOT SEE THIS — AND IT IS NOT A GAP, IT IS THE SHAPE OF THE CRITERION

All five declared routes write state by exactly two mechanisms:

* R1, R2, R3 — `subject.__dict__.update(...)`. **`__slots__` closes this.**
* R4, R5 — `subject.__setstate__(...)`. **Deleting the stdlib `__setstate__` closes this.**

Increment 9 did both, to 36 classes, and the board went green. **BUT `__slots__` DOES NOT MAKE AN
ATTRIBUTE UNWRITABLE. IT REPLACES A `__dict__` ENTRY WITH A C-LEVEL DESCRIPTOR THAT IS STILL
WRITABLE, AND `object.__setattr__` WRITES IT.** Note the direction of the evidence: CPython's own
`dataclasses._dataclass_setstate` — the function R5 exists to exercise — *is implemented as a loop
of `object.__setattr__`*. **R5 IS R6 WITH A WRAPPER ROUND IT. THE INSTRUMENT FOUND THE WRAPPER AND
REMOVED THE WRAPPER, AND THE MECHANISM UNDERNEATH IT WAS NEVER THE WRAPPER'S TO CARRY.**

45 of the 47 seal-available classes have no `__setstate__` at all, so R4 and R5 cannot even fire
against them; they are scored SEALED on five refusals of which two are `AttributeError: __setstate__`.
**A REFUSAL BECAUSE THE ROUTE'S ENTRY POINT DOES NOT EXIST IS NOT THE PROPERTY HOLDING.** That is
precisely the `CD-ENG-WO2R3-F12` standard the instrument's own R5 docstring invokes against R4 —
*"A ROUTE THAT FAILS FOR THE WRONG REASON SCORES A CLASS CLOSED"* — **failing a second time, one
level down, inside the fix for the first time.**

### SO: IS THE EXCLUSION CLAUSE A PROPERTY OR A LIST WEARING A MEASUREMENT?

The dispatch asked. **My answer: the exclusion clause is a genuine measured property and it is not
my finding. It is sound and I could not break it.** I re-ran `_seal_availability` against all 99
independently and reproduced 43 `BaseException` / 5 `enum.Enum`. **The defect is not in the
exclusion. The defect is in what "SEALED" is taken to mean for everything the exclusion lets
through.** The instrument answers a narrower question than its own stated property, and prints the
stated property.

*** **THE RENAME TEST PROVES A CRITERION IS NOT A VOCABULARY. THE BASE/TIP CONTRAST PROVES IT IS
NOT VACUOUS. THE PROJECT LEAD ASKED THE RIGHT QUESTION — NEITHER PROVES IT IS RIGHT — AND THIS IS
THE ANSWER: IT IS NOT RIGHT. IT IS A SOUND, NON-VACUOUS, RENAME-STABLE MEASUREMENT OF THE WRONG
PROPERTY.** ***

---

# 2. AND THE ONE THAT IS ON NOBODY'S LIST: **CD-ASR-F01 IS REOPENED AT `686a374`.**

## FINDING **CD-ASR-WO2R3-04-F01** — SEVERITY **HIGH**. A LIVE CONTROL BYPASS.

While reconciling a four-class gap between my population count and the instrument's, I found that
four classes are scored `SEALED` **while carrying `__dictoffset__ == 264`** — a full live instance
`__dict__`:

    dials/magnitude.py:305          SealedMagnitudeType      __dictoffset__ == 264
    dials/provenance.py:319         SealedQuantityType       __dictoffset__ == 264
    dials/reading.py:212            SealedReadingType        __dictoffset__ == 264
    serving/dial_presentation.py:218 SealedPresentationType  __dictoffset__ == 264

They are scored SEALED because **`if not forging:` is evaluated BEFORE `_seal_availability` is ever
consulted** (`check_sealed_against_forged_establishment.py`, the measurement loop). They do not
forge only because `cls.__new__(cls)` raises `TypeError: __new__() missing 3 required positional
arguments` — **an ARITY refusal, not a sealing refusal.** Wrong reason again.

Pulling that thread produced a live bypass of a different control entirely.

`SealedMagnitudeType.__new__` refuses subclassing of `DialMagnitude`. Its own docstring states the
stakes: *"Subclassing is refused rather than policed because a subclass carrying `__float__` would
be accepted everywhere a magnitude is accepted while passing every check aimed at the declared
class."* That is the `CD-ASR-F01` route from two dials to one number.

**THE COUNTERFACTUAL ARM (CD-D-079), BOTH ARMS RUN, `/tmp/asr7/f01.py`, THROWAWAY PROBE, TREE
UNMODIFIED:**

    ARM 1 — THE DECLARED ROUTE, which is the guard's own target:
      class Evil(DialMagnitude): ...
      -> REFUSED MagnitudeSurfaceViolated: "Evil may not subclass DialMagnitude: a dial
         magnitude is a CLOSED type..."                          THE GUARD FIRES.

    ARM 2 — MY ROUTE 8b: type.__new__ with the metaclass as the FIRST argument:
      type.__new__(SealedMagnitudeType, 'Evil2', (DialMagnitude,),
                   {'__slots__': (), '__float__': lambda self: 999.0})
      -> CREATED <class 'Evil2'>          package lines executed: 0
         issubclass(Evil2, DialMagnitude)     True
         instance built,                   package lines: 0
         float(inst)                        999.0
         isinstance(inst, DialMagnitude)      True

*** **A DIAL MAGNITUDE THAT COERCES TO A NUMBER, BUILT WITH ZERO LINES OF PACKAGE CODE, PASSING
`isinstance`. THAT IS CD-ASR-F01, WHICH THIS PROJECT BELIEVES IT CLOSED.** ***

`type.__new__(metaclass, ...)` does not call `metaclass.__new__`. The guard is written in
`SealedMagnitudeType.__new__` and is therefore only on the path that the `class` statement takes.
**It guards the syntax, not the type.** By inspection the same shape holds for `SealedReadingType`,
`SealedQuantityType` and `SealedPresentationType`; I executed it against `SealedMagnitudeType` and
report the other three as *structurally identical, not individually executed* — an honest limit.

* **RENAME TEST:** not applicable — this is a defect in a guard, not a criterion keyed on text.
* **VACUITY:** the guard is NOT vacuous. Arm 1 proves it refuses. It refuses the reported case.
* **SOUNDNESS:** it is unsound in the permissive direction. `GUARD_THE_INSTANCE_NOT_THE_CLASS`:
  it stops the `class` statement and not the class of routes that make a class.


---

# 3. T2 / ESCAPE 3 — **REFUTED IN ITS MEASURED FORM AT `686a374`.** AND THE DISPATCH IS WRONG ABOUT IT.

The dispatch's T2 entry reads: *"**ESCAPE 3 IS LIVE, UNMOVED AND UNDECLARED AT YOUR TARGET** —
increment 9 changed nothing under `collectors/`."*

**THE SECOND HALF IS TRUE AND THE FIRST HALF IS FALSE, AND THE SECOND HALF IS WHY THE FIRST HALF
WAS NOT CHECKED.** Increment 9 changed nothing substantive under `collectors/` — I confirm it,
`git diff --stat 753efe4..686a374 -- src/crash_detector/collectors/` is 4 files / 72 insertions and
all 72 are `__slots__` lines. **BUT ESCAPE 3 WAS CLOSED BY INCREMENT 8, AT COMMIT `6eecb85`,
WHICH IS BEFORE THE TARGET AND AFTER THE SIXTH SEAT'S `af2accb`.** The sixth seat's finding was
carried forward into my brief as a live standing item by reasoning about increment 9's diff alone.
**THAT IS A T22 DEFECT IN THE DISPATCH ITSELF: THE POPULATION EXAMINED (increment 9's diff) DID NOT
CONTAIN THE ANSWER, AND A VERDICT WAS STATED ANYWAY.** It is the exact shape of `CD-PL-F121`.

I did not inherit it and I did not inherit its refutation either. **BOTH ARMS RUN, MY OWN HOSTILE
SINKS, WRITTEN FROM THE TARGET'S SOURCE** (`/tmp/asr7/escape3.py`, throwaway; the tree is
unmodified; imports only, `python3 -B` so no `__pycache__` is written):

    ----- CONTROL — benign sink, flat payload -----
      sink was handed  : {'reading': 0.25}
      RETURNED payload : {'reading': 0.25}
      reading_key      : ('src.h', '2026-08-22T11:59:59Z')      reading_admitted: True

    ----- ESCAPE 3 — TOP-LEVEL REWRITE (the measured escape) -----
      sink was handed  : {'reading': 999.0, 'smuggled': 'never validated'}   <- the sink DID rewrite it
      RETURNED payload : {'reading': 0.25}                                   <- THE RUNNER IS UNMOVED
      RETURNED as_of   : 2026-08-22 11:59:59+00:00                           <- UNMOVED
      reading_key      : ('src.h', '2026-08-22T11:59:59Z')                   <- THE HONEST KEY
      reading_admitted : True     ledger asked for: [('src.h','2026-08-22T11:59:59Z')]

**THE ESCAPE IS CLOSED.** The sink's `object.__setattr__` lands — the "sink was handed" line proves
the arm is honest and not a dud — and it reaches nothing. `kept = _the_runners_own_copy(outcome)` is
taken before `_record`, re-established through the outcome's own constructor, and every subsequent
read is of `kept`. **The fix is well made, it is derived rather than spelled (`typing.get_args`,
`dataclasses.fields`, `is_exactly`), and its residue is declared in its own docstring rather than
left to be found.** I grade the fix itself **GREEN** and say so plainly; it is the best-constructed
thing I examined at this target.

**THE DECLARED RESIDUE REPRODUCES, EXACTLY AS DECLARED:**

    ----- CONTROL — benign sink, NESTED payload -----
      RETURNED payload : {'reading': 0.25, 'nested': {'reading': 0.25}}
    ----- RESIDUE — NESTED INTERIOR REWRITE -----
      sink was handed  : {'reading': 0.25, 'nested': {'reading': inf}}
      RETURNED payload : {'reading': 0.25, 'nested': {'reading': inf}}       <- THE RUNNER CARRIES IT

`OK.__post_init__` takes `dict(self.payload)`, a SHALLOW copy. **This is DECLARED, it is CARRIED by
`tests/test_collector_mutating_sink.py`, and it is NOT claimed closed. I grade the declaration
HONEST and the residue LIVE.** A stored payload carrying `inf` where the validated one carried
`0.25` is Escape 1's class surviving inside Escape 3's fix.

---

# 4. *** THE FINDING THAT DECIDES THIS GATE. THE TREE CONTRADICTS ITSELF AT ONE SHA. ***

## FINDING **CD-ASR-WO2R3-04-F02** — SEVERITY **HIGH**.

I did not have to leave the target to find the sixth route. **IT IS WRITTEN DOWN IN THIS
REPOSITORY, IN A DOCSTRING, AS A KNOWN LIVE ATTACK THE PRODUCT HAD TO DEFEND AGAINST OPERATIONALLY
— AND THE INSTRUMENT WRITTEN EIGHT HOURS AGO DOES NOT HAVE IT IN ITS ROUTE SET.**

`src/crash_detector/collectors/runner.py`, `_the_runners_own_copy`, at the target:

> *"The `OK` handed to the sink and the `OK` the runner went on to report were **THE SAME
> OBJECT**: normal `setattr` is refused (`FrozenInstanceError`) and **`object.__setattr__`
> succeeds**, so a sink doing::*
>
>     object.__setattr__(attempt.observation.outcome, "payload", {"reading": 999.0})
>
> *changed `CollectionResult.final_outcome` and made `_reading_key` ask the ledger for a key naming
> a period NO ROW RECORDS."*

`tools/register/check_sealed_against_forged_establishment.py`, at the same SHA, same run:

> `SEALED   observations.py:... OK — no declared route reached an object of exactly this type
> carrying forged state with zero package lines. __dictoffset__ == 0.`

*** **ONE SHA. TWO GOVERNED ARTEFACTS. `runner.py` SAYS `object.__setattr__` ON AN `OK` SUCCEEDS
AND BUILDS A WHOLE DEFENSIVE COPY BECAUSE OF IT. THE SEALING REGISTER CERTIFIES THAT SAME CLASS
SEALED AGAINST FORGED ESTABLISHMENT. THEY CANNOT BOTH BE TRUE, AND THE ONE THAT IS TRUE IS THE ONE
WITH THE EXECUTING COUNTER-MEASURE ROUND IT.** ***

This is not a clever attack I imported. **THE PROJECT ALREADY KNEW THE ROUTE. IT KNEW IT WELL
ENOUGH TO SPEND AN INCREMENT DEFENDING AGAINST IT.** The route set was assembled by asking *"what
routes do I know of?"* and it did not include the one route this codebase had most recently been
burned by. Adding `object.__setattr__` to `ROUTES` is a four-line change that would have turned the
`PASS` into roughly **40 violations** on the run it was added.

**AND THIS IS THE ANSWER TO THE QUESTION THE DISPATCH ASKED ABOUT ITSELF.** Header item 2 says the
lesson is *"agreement between two independent readings was treated as evidence when both readings
shared a blind spot"* and instructs me to *"assume that is still true somewhere in this record and
that nobody has found it yet."* **IT IS STILL TRUE, IT IS IN THE SAME PROPERTY, AND THE THIRD
READING SHARES THE BLIND SPOT WITH THE FIRST TWO.** The first two could not see `__setstate__`. The
third can see `__setstate__` and cannot see `object.__setattr__`. **THE METHOD DID NOT CHANGE: ALL
THREE ENUMERATE ROUTES FROM MEMORY AND NONE DERIVES THE SET FROM THE ATTRIBUTE MODEL.** The
instrument's own DECLARED LIMIT 2 — *"THE ROUTE SET IS DECLARED, NOT PROVED COMPLETE"* — is
scrupulously honest and it is not a mitigation, because the register's exit code does not carry the
limit and the reconciliation reads the exit code.


### AND IT IS SHARPER THAN THAT. THE ROUTE IS NAMED IN THE SEALING RATIONALE ITSELF.

`src/crash_detector/observations.py`, lines 126-131, the comment justifying how `FetchFailed` was
sealed by this increment:

> *"THAT DECORATOR ALSO INSTALLS `dataclasses._dataclass_setstate` — A STDLIB FUNCTION THAT WRITES
> EVERY KEY IT IS GIVEN **THROUGH `object.__setattr__`** WITH NO VALIDATION AND NO PACKAGE CODE —
> which re-opens by the `__setstate__` sibling exactly the route..."*

*** **THE WORDS `object.__setattr__`, "NO VALIDATION" AND "NO PACKAGE CODE" APPEAR TOGETHER, IN THE
INCREMENT'S OWN JUSTIFICATION FOR ITS OWN SEAL, DESCRIBING THE MECHANISM THAT DEFEATS THAT SEAL —
AND THEY ARE READ AS A PROPERTY OF `__setstate__` RATHER THAN AS A ROUTE.** *** The Engineer wrote
the correct sentence and drew the narrower conclusion from it. This is `GUARD_THE_INSTANCE_NOT_THE_CLASS`
in its purest observed form on this project: the instance is `__setstate__`, the class is
`object.__setattr__`, and the class was named in writing at the moment the instance was closed.

### THE PLANT CONTRAST — RE-RUN BY ME, AND IT IS EVIDENCE FOR THE WRONG PROPOSITION

Throwaway extraction `/tmp/asr7_plants` (`git archive 686a374 | tar -x`), the tree untouched:

    CLEAN ARM     rc=0   PASS — 99 assertions, 0 violations
    git apply     rc=0
    VIOLATED ARM  rc=1   FAIL — 1 violation(s)      rule: OPEN TO FORGED STATE
    SIBLING check_constructor_field_establishment on the SAME violated arm:
                  rc=0   PASS — 101 assertions, 0 violations

**EVERY NUMBER THE PROJECT LEAD PUBLISHED FOR THIS CONTRAST REPRODUCES, AND THE WIDENING IS REAL** —
the sibling really is blind to what the new instrument catches. It applies, it contrasts, and it
fails at the layer its proposition names, so it CLEARS the `CD-ENG-WO2R3-F12` standard. **AND IT IS
STILL EVIDENCE FOR THE WRONG PROPOSITION.** The plant removes `__slots__` from one class and the
instrument notices. That establishes *"this instrument detects the absence of `__slots__`."* It
does not establish *"`__slots__` seals."* R6 shows it does not. **A PERFECT CONTRAST AROUND AN
UNSOUND CRITERION IS STILL AN UNSOUND CRITERION, AND THIS IS THE CLEANEST EXAMPLE OF THE PROJECT
LEAD'S OWN QUESTION THAT THE RECORD WILL EVER GET.**

---

# 5. T20 — WHAT A FORGED EXCEPTION OR ENUM MEMBER COSTS THIS PRODUCT. **THE ASSESSMENT NOBODY HAS MADE.**

## GRADE: **RED FOR THE EXCEPTIONS. AMBER FOR THE ENUMS. THE COST IS REAL, IT IS ONE HOP, AND IT IS AT A NAMED LINE.**

I re-derived the population independently: **43 exceptions, 5 enums** — reproduces the instrument's
split exactly. Of the 43, **5 carry structured state through their own `__init__`**:
`AdapterFetchError`, `SchemaRejection`, `SchemaDeclarationInvalid`, `PublicationRefused`,
`MigrationApplyFailed`. The other 38 are markers and their forging costs nothing I can find.

### THE EXCEPTION COST IS AT `src/crash_detector/collectors/runner.py:868`, AND IT IS ONE LINE

    return FetchFailed(error_class=exc.error_class, http_status=exc.http_status)

**AN EXCEPTION'S ATTRIBUTES ARE LIFTED DIRECTLY ONTO A GOVERNED OUTCOME OBJECT.** `AdapterFetchError`
is one of the 43 UNSEALABLE classes — it carries a `__dict__` imposed by `BaseException`, so R1/R2/R3
forge it with zero package code, and the instrument correctly prints **"NOT SAFE — UNSEALABLE. NOT
PROVED TO BE CARRIED ANYWHERE."** It is right to. **HERE IS WHAT IT COSTS:** a hostile or merely
broken adapter raises a forged `AdapterFetchError`, and `error_class` and `http_status` land on a
`FetchFailed` that the rest of the system treats as established. `FetchFailed.__post_init__` checks
that `error_class` is non-empty and that `http_status` is an `int` or absent — **it does NOT check
that `error_class` is a member of the declared `ERROR_*` vocabulary**, so an arbitrary string
becomes a governed outcome's error classification.

**THIS IS THE ADAPTER BOUNDARY ADMITTING AGAIN — CD-BP-003 — BY A ROUTE THAT IS NOT ESCAPE 3 AND IS
ON NOBODY'S LIST.** The residue the sealing instrument declares as "NOT PROVED TO BE CARRIED
ANYWHERE" **IS carried, one hop, to a governed field.** I did not build the end-to-end arm — see
section 99 — so I grade this **REPRODUCED AS A PATH BY READING, NOT EXECUTED END TO END**, and I
name that limit rather than let it read as a demonstration.

### THE ENUM COST IS CONCENTRATED IN ONE MEMBER SET AND THE PRODUCT DEFENDS ITSELF WELL IN THE OTHER

The five: `DelayKind`(1), `SameDialReduction`(4), `MappingKind`(1), `EnvelopeSurface`(2),
`Criticality`(3).

* **`Criticality` — DEFENDED, AND IT SHOULD BE CREDITED.** `source_registry.py:281-312` compares
  with **`is`**, four times: `record.criticality is Criticality.DISPOSABLE`. Identity comparison
  makes a forged member match NOTHING, so it fails into the conservative branch. **THAT IS THE
  CORRECT DEFENCE AGAINST A FORGED ENUM MEMBER AND THIS CODEBASE ALREADY USES IT.** A forged
  `Criticality` costs approximately nothing.
* **`EnvelopeSurface` — THIS IS THE EXPENSIVE ONE.** `publication/envelope_contract.py:186`:

        def schema_path_for(surface):
            if not isinstance(surface, EnvelopeSurface):
                raise TypeError("surface must be an EnvelopeSurface member")
            return contracts_dir() / surface.schema_filename

  **THE GUARD IS `isinstance`, NOT MEMBERSHIP.** `isinstance` is satisfied by any object of the
  enum type, including one built by `EnvelopeSurface.__new__(EnvelopeSurface)` — which is not in
  `_member_map_` and is not a member. `surface.schema_filename` is then read off it **and
  CONCATENATED INTO A FILESYSTEM PATH**. A forged surface selects an arbitrary contract file: the
  PUBLIC schema applied to PRIVATE data, which is `CD-RT-006-PUBLIC-SURFACE-NO-PRIVATE-DATA`
  directly, and a path component the caller chose. The same `isinstance`-not-membership shape is at
  line 244. **`is` is used for `Criticality` and `isinstance` is used for `EnvelopeSurface`, in the
  same tree, and the one that gets the weaker test is the one that separates public from private.**
  I did not execute this arm either — same limit, same honesty.

### AND THE SECOND HALF OF T20, WHICH IS MECHANICAL AND WHICH I CONFIRM

**`CD-PL-F122` IS CORRECT AND I REPRODUCE IT.** `required-tests.yaml` at the target carries
**25 `test_id` rows**, enumerated. `delegated_judgement_sweep` appears in that file exactly **once**,
at line 1000, **inside the prose of a different row**. It has no `test_id`, no `execution_contract`,
no plant. **THE ONE GUARD THE LAST THREE GATES HAVE ARGUED ABOUT IS THE ONE GUARD CD-RULE-004 HAS
NEVER APPLIED TO.**

**AND HERE IS THE PART THE PROJECT LEAD DID NOT SAY, WHICH I ADD:**
`CD-RT-002-SEALED-AGAINST-FORGED-ESTABLISHMENT` **DOES** have a full row — `test_id`,
`execution_contract`, `planted_violation` — added by the increment that wrote it, eight hours ago.
*** **THE INCREMENT GAVE ITS OWN BRAND-NEW INSTRUMENT ALL THREE PLACES IN AN AFTERNOON, WHILE THE
SWEEP THAT HAS BEEN RED AND ARGUED OVER FOR THREE GATES STILL HAS NONE.** *** The rule is not
unenforceable and it is not expensive. It was applied where someone was looking and not where
nobody was.

---

# 6. T22 — THE PROJECT LEAD'S OWN TABLES. **POPULATIONS FIRST, VERDICTS SECOND.**

I was told to distrust this seat's derived tables specifically and to check every population is
non-empty before reading its verdict. I did. **THE RESULT IS BETTER THAN THE WARNING PREDICTED,
WITH ONE EXCEPTION THAT IS NOT A PARSE DEFECT BUT IS WORSE.**

| PL table | population re-derived by me | verdict |
|---|---|---|
| 99-class sealing population | **99**, by my own live `vars()` descent, written from scratch | **CONFIRMED, NON-EMPTY** |
| 43 exceptions / 5 enums excluded | **43 / 5** | **CONFIRMED, NON-EMPTY** |
| 13 plants · all apply · ZERO DEAD | **13 found, 13 `git apply --check` rc=0, 0 dead** | **CONFIRMED, NON-EMPTY** |
| sealing plant contrast rc 0 / 0 / 1 | reproduced exactly, plus sibling rc=0 | **CONFIRMED** |
| suite 3 failed / 1696 passed | **3 failed / 1696 passed**, same three node-ids | **CONFIRMED, NO FOURTH FAILURE** |
| Class-2 sweep byte-identical at base and tip | not re-taken — see section 99 | **NOT REACHED** |
| **T2 / "Escape 3 is LIVE, UNMOVED at your target"** | **the population examined was increment 9's diff; the answer was in increment 8's** | *** **REFUTED** *** |

**THE ONE THAT FAILS IS NOT A PARSE DEFECT.** `CD-PL-F121` is about extractions that matched
nothing or everything and printed confident rows. **THIS IS THE OPPOSITE FAILURE AND IT IS MORE
DANGEROUS: A CORRECT MEASUREMENT OVER A POPULATION THAT COULD NOT CONTAIN THE ANSWER, REPORTED AS
AN ANSWER.** `git diff 753efe4..686a374 -- collectors/` is a true statement, correctly taken, and
"Escape 3 is live" does not follow from it. **THE FIVE `CD-PL-F121` INSTANCES WERE ALL CAUGHT
BECAUSE A NUMBER LOOKED WRONG. THIS ONE HAS NO WRONG-LOOKING NUMBER, WHICH IS WHY IT SURVIVED INTO
A DISPATCH AND WOULD HAVE SURVIVED MY VERDICT IF I HAD INHERITED IT AS INSTRUCTED NOT TO.**

**I therefore CONFIRM the Project Lead's arithmetic wherever I could reach it and I RAISE against
its scoping.** The four parse defects have made this seat careful about how it counts. **They have
not made it careful about whether the thing it counted was the thing in question.** That is the
next `CD-PL-F` and I recommend it be opened as one.


---

# 7. THE VERDICT

## **RED.**

    target        686a374e60ff8f18305fa8b665463e0e057dac2b   branch wo-2r3
    fingerprint   319e401fc2591dc48b611d101d5330bdb3dbb3bb9824b7bb1c39a11e5b10fc6a
                  RE-TAKEN AT THE END OF THIS AUDIT AND IDENTICAL TO THE START.
                  509 files both times. `git status --porcelain` ZERO LINES both times.
                  THE TREE I AUDITED IS THE TREE I WAS SENT TO AND I DID NOT CHANGE IT.
    confidence    HIGH on the sealing finding (executed, counted, read back, hand-verified
                  on named classes, and corroborated by the target's own docstrings).
                  HIGH on Escape 3 refuted (both arms run, control arm honest).
                  MEDIUM on the T20 costs (paths established by reading, NOT executed
                  end to end — stated as a limit, not smuggled as a demonstration).

**THE GROUND OF THE RED IS ONE SENTENCE:** `PASS — 99 assertions, 0 violations` certifies a
property that does not hold of 40 of the 51 classes it certifies, by a route the same repository
documents in two places as live, and the register's exit code carries none of that.

**A RED IS NOT A FAILURE OF THE INCREMENT AND I WANT THAT ON THE RECORD IN MY OWN WORDS.**
Increment 9 is the best-evidenced work I read here. It found its own false green (`F06`). Its
scaffolding broke its own check and it said so (`F14`). It refused twice to keep a dead register
key alive so a control would pass, and returned `SCOPE_INSUFFICIENT` instead — **that refusal is
the single most valuable behaviour in this record and it should not be graded as an incomplete
item.** The `_the_runners_own_copy` fix is excellent and its residues are declared honestly. **THE
DEFECT I FOUND IS NOT SLOPPINESS. IT IS THAT THE ROUTE SET WAS ENUMERATED FROM MEMORY BY EVERY
PARTY WHO EVER TOUCHED IT, INCLUDING ME UNTIL I STOPPED GUESSING AND ASKED HOW CPYTHON WRITES AN
ATTRIBUTE.**

## PER-CRITERION GRADES

| criterion | prior | **MY GRADE** | what would move it |
|---|---|---|---|
| **CD-AC-002** | AMBER, not closed | **AMBER — NOT CLOSED. UNMOVED.** | Escape 3 closing is real progress and I credit it. But the adapter boundary still admits by the `runner.py:868` exception-attribute lift, the validator is uncovered by the snapshot by declaration, and the nested residue reproduces. **Closing needs the validator route and an `error_class` vocabulary check.** |
| **CD-AC-005** | AMBER, not closed | *** **RED. MOVED DOWN.** *** | This is the criterion the sealing claim was supposed to serve. The instrument certifies a property that fails on 40 of 51 classes. **An AMBER here would be a PASS I am not sure of; I am sure of this one.** Moving to AMBER needs `object.__setattr__` and the descriptor `__set__` in the route set, the run re-taken, and whatever it then says accepted as the real starting point. |
| **T2 (CD-BP-003)** | RED at the 4th, 5th, 6th gates | **RED. SAME LETTER, DIFFERENT GROUND — AND THE GROUND MATTERS.** | The standing ground (Escape 3) is **GONE — I refute it.** I am not leaving T2 RED by inheritance; **I am re-grounding it** on `runner.py:868`, on the declared nested residue reproduced, and on the uncovered validator. **If I had only checked the old ground I would have moved T2 to AMBER and been wrong.** |

**MY VERDICT IS NOT AN ACCEPTANCE** (PBG-AUTH-003). I grade; the Product Owner dispositions.

## EVERY NAMED TARGET, INCLUDING THE ONES I DID NOT REACH

| T | grade | basis |
|---|---|---|
| **T18** sealing claim | **RED — THE GREEN IS NOT EARNED** | §1. 40/51 forge. Criterion sound, non-vacuous, rename-stable, and measuring the wrong property. |
| **T19** route set | **RED — SIXTH, SEVENTH AND EIGHTH ROUTES FOUND** | §1, §2. R6 `object.__setattr__`; R7 descriptor `__set__`; R8 `type.__new__(metaclass,...)`. |
| **T20** forged exception/enum | **RED / AMBER** | §5. Cost located at `runner.py:868` and `envelope_contract.py:186`. Sweep has no row — confirmed. |
| **T22** PL tables | **AMBER — arithmetic confirmed, one scoping refutation** | §6. |
| **T2** adapter boundary | **RED, re-grounded** | §3, §5. |
| **T13** plant set | **CONFIRMED — 13, all apply, ZERO DEAD, re-derived not inherited** | §5. Applicability axis only; per-plant contrast re-run for ONE plant. |
| **T15** fingerprint instrument | **PASS, with an unplanned differential test in its favour** | §0. |
| **T5** sweep exit 1 | **DECLARED AND HONEST — not a defect to fix, a record owed** | Suite reproduces the three declared failures and no fourth. |
| **T21** two new instruments | **PARTIAL** — sealing instrument graded in full (§1); the citation instrument on `main` NOT graded | §99. |
| **T3** §D scoping invitation | **NOT SPENT** — I spent my time on T18/T19 instead, and I say so plainly | §99. |
| **T6** grant-matrix inheritance | **NOT REACHED** | §99. |
| **T8** the fifty derivation rows | **NOT REACHED** | §99. |
| **T9** blindness-window sweep | **NOT REACHED — STILL UNRUN THROUGH FOUR GATES** | §99. |
| **T14** increment 7 reclassification | **NOT REGRADED** | §99. |
| **T17** `*extra` residue | **NOT REACHED** | §99. |

## FINDINGS RAISED BY THIS SEAT

| id | sev | finding |
|---|---|---|
| **CD-ASR-WO2R3-04-F01** | **HIGH** | `CD-ASR-F01` reopened: `type.__new__(SealedMagnitudeType, ...)` bypasses the sealed-type metaclass guard, zero package lines, producing a `DialMagnitude` subclass with `__float__`. Both arms run. |
| **CD-ASR-WO2R3-04-F02** | **HIGH** | The tree contradicts itself at one SHA: `runner.py` documents `object.__setattr__` on an `OK` as a live attack it defends against; the sealing register certifies that same class SEALED. |
| **CD-ASR-WO2R3-04-F03** | **HIGH** | R6/R7: 40 of 51 classes certified SEALED are forgeable with zero package code. |
| **CD-ASR-WO2R3-04-F04** | **MEDIUM** | `SEALED` is assigned before `_seal_availability` is consulted, so four classes with `__dictoffset__ == 264` are labelled SEALED on an ARITY refusal. Wrong-reason refusal, the `CD-ENG-WO2R3-F12` standard failing inside the instrument that cites it. |
| **CD-ASR-WO2R3-04-F05** | **MEDIUM** | The dispatch's T2 entry states a verdict over a population that could not contain the answer. Not a parse defect — a scoping defect, and it has no wrong-looking number to catch it. |
| **CD-ASR-WO2R3-04-F06** | **MEDIUM** | `envelope_contract.schema_path_for` guards with `isinstance`, not membership, and reads `schema_filename` into a path. `Criticality` gets `is` in the same tree; the public/private separator gets the weaker test. |
| **CD-ASR-WO2R3-04-F07** | **LOW** | `FetchFailed.__post_init__` does not check `error_class` against the declared `ERROR_*` vocabulary. |

## CONTINUATION IMPLICATION — STATED SEPARATELY FROM THE FINDING

**WHAT IS TRUE:** the sealing claim is not established, and `CD-ASR-F01` has a live bypass.

**WHAT IS SAFE:** *** **NOTHING I FOUND MAKES THIS TREE UNSAFE TO LEAVE EXACTLY WHERE IT IS.** ***
Every route I executed requires an attacker already running arbitrary Python in this process. That
is not a mitigation of the finding — the whole architecture of `@establishes`/`admits` is a defence
against in-process foreign code, so "the attacker is in-process" is the threat model, not an excuse
— but it does mean **there is no emergency, nothing needs reverting, and increment 9 should NOT be
backed out.** Increment 9 made the tree strictly better: it closed R1-R5 on 36 classes and those
routes are really closed. **IT IS THE CLAIM THAT OVERREACHED, NOT THE CODE THAT REGRESSED.**

**THE WO-2 GATE STAYS SHUT.** CD-AC-005 goes down, not up.

## NEXT SAFE GATE

1. **DO NOT FIX THIS BY ADDING TWO ROUTES TO `ROUTES`.** That is `GUARD_THE_INSTANCE_NOT_THE_CLASS`
   a sixth time and this project has now been bitten by it in the same property three readings
   running. **DERIVE THE ROUTE SET FROM THE ATTRIBUTE MODEL** — every way CPython writes an
   instance attribute — **or declare in the register's own exit-code-bearing summary that the set
   is enumerated and the PASS is therefore conditional.** Either is honest. The current shape is
   honest in DECLARED LIMIT 2 and not honest in the exit code, and the reconciliation reads the
   exit code.
2. **ADD `object.__setattr__` AND THE DESCRIPTOR `__set__` AND RE-RUN, BEFORE ANY REMEDY IS
   DESIGNED**, so the real starting number is on the record. I predict ~40 violations. **IF IT IS
   NOT ~40, ONE OF US IS WRONG AND THAT IS WORTH KNOWING.**
3. **`CD-ASR-WO2R3-04-F01` IS THE MOST URGENT ITEM** — it is a bypass of a guard the project
   believes closed, in the CD-ASR-F01 class. A separate Engineer (not me — `PBG-SOD-004`).
4. **RUN THE T9 BLINDNESS-WINDOW SWEEP.** Four gates have now called it mechanical and
   high-value and not run it, including me. **THAT IS ITSELF A FINDING ABOUT THIS PROGRAMME'S
   PRIORITISATION AND I INCLUDE MYSELF IN IT.**
5. Sweep the record backward for `CD-PL-F124`'s class, per the dispatch's own general question.
6. The three stale keys, the plant-drift carrier and ITEM 3's closure, per PO-DECISIONS-0017.

---

# 8. *** SUPERSEDING CORRECTION, BY THIS SEAT, AGAINST SECTION 5 AND SECTION 7 OF THIS DOCUMENT ***

**I WROTE SECTION 5 FROM READING. THEN I EXECUTED IT. TWO OF MY OWN FINDINGS ARE REFUTED BY THE
PRODUCT AND I AM CORRECTING THEM RATHER THAN EDITING THEM AWAY** (the project's own rule —
corrections supersede, never edit — applied to an auditor's own draft, which is where it is
hardest and therefore where it counts).

Section 5 graded T20's exception route **RED** and named `runner.py:868` as a live cost, flagged
honestly as *"reproduced as a path by reading, NOT executed end to end."* **I THEN BUILT THE ARM.
THE PRODUCT REFUSED IT.**

    ARM — a forged AdapterFetchError (__new__ + __dict__.update, ZERO package lines),
          error_class = {'not': 'a string'}, raised by the adapter:

    crash_detector.establishment.FieldNotEstablished:
      FetchFailed.error_class=dict is not admitted; this door requires exactly str.
      Exact type and never isinstance...

*** **THE `@establishes` DOOR CATCHES IT. THE CONSTRUCTOR-FIELD-ESTABLISHMENT MECHANISM — WHICH IS
WHAT CD-AC-005 IS ABOUT — DOES EXACTLY WHAT IT CLAIMS, AT THE EXACT LINE I EXPECTED IT TO FAIL.** ***
And with a *string* `error_class` the forgery gains nothing either: `error_class` is free-form by
design, so a forged exception produces the same `FetchFailed` an honest adapter could produce by
calling the constructor. **THE FORGERY BUYS THE ATTACKER NOTHING AT THIS SITE.**

The `EnvelopeSurface` route (my `F06`) is refuted too:

    A: EnvelopeSurface.__new__(EnvelopeSurface) -> REFUSED TypeError: missing 'value'
    B: object.__new__(EnvelopeSurface)          -> built, 0 package lines, isinstance=True
       object.__setattr__(obj,"schema_filename",...) -> AttributeError: property has no setter
       schema_path_for(forged)  -> REFUSED AttributeError: no attribute '_value_'

**`schema_filename` IS A DERIVED PROPERTY, NOT A STORED ATTRIBUTE, SO THERE IS NOTHING TO FORGE.**
That is the correct design and I did not credit it when I was reading instead of running.

## CORRECTED GRADES

| item | section 5/7 said | **CORRECTED** |
|---|---|---|
| **T20 exceptions** | RED | **AMBER — the 43 are unsealable and the instrument is right to say so, but the residue is CONTAINED at the receiving doors by exact-type establishment. I could not carry a forged exception into a governed field.** |
| **T20 enums** | AMBER | **PASS — `Criticality` uses `is`, `EnvelopeSurface` uses derived properties. Both are the correct defence. This is the strongest thing I found in this tree.** |
| `CD-ASR-WO2R3-04-F06` | MEDIUM | **WITHDRAWN — refuted by execution.** |
| `CD-ASR-WO2R3-04-F07` | LOW | **STANDS, downgraded to INFORMATIONAL.** `error_class` really is unvalidated against the `ERROR_*` vocabulary, but no forgery is needed to exploit that and no boundary claims otherwise. |

**THIS IS THE `runtime claims need runtime proof` STANDARD BITING THE AUDITOR, AND IT SHOULD BE READ
THAT WAY.** I produced two plausible findings by reading source and reasoning about it — the exact
method the sealing instrument's own docstring forbids — and both were wrong. **THE PROJECT'S OWN
EVIDENCE STANDARD CAUGHT MY ERROR, WHICH IS THE BEST AVAILABLE EVIDENCE THAT THE STANDARD IS WORTH
THE COST (`CONTROL_BURDEN`).**

## AND T2 IS RE-GROUNDED A SECOND TIME — THIS TIME ON AN EXECUTED ARM

Removing `runner.py:868` removed one of my three T2 grounds. **SO I BUILT THE ARM FOR ANOTHER ONE
RATHER THAN LEAVE T2 RED ON A GROUND I HAD NOT RUN.** DECLARED LIMIT 5 says *"THE VALIDATOR IS NOT
COVERED AT ALL... A validator that mutates the payload while judging it defeats this closure
completely"* and, of that residue, *"NOT PROVED TO BE CARRIED ANYWHERE."*

**BOTH ARMS RUN** (`/tmp/asr7/validator.py`, throwaway; tree unmodified):

    ----- CONTROL — benign validator -----
       validator was handed : [{'reading': 0.25}]
       outcome              : OK
       STORED payload       : {'reading': 0.25}

    ----- MUTATING VALIDATOR -----
       validator was handed : [{'reading': 0.25}]      <- it judged the HONEST value, and passed it
       outcome              : OK
       STORED payload       : {'reading': 999.0, 'smuggled': 'never validated'}

*** **THE STORED PAYLOAD IS NOT THE VALIDATED PAYLOAD. IT CARRIES A KEY THE SCHEMA FORBIDS
(`additionalProperties: false`) AND A VALUE NOTHING EVER JUDGED, AND THE OUTCOME IS `OK`.** *** The
control arm proves the arm is honest and not a dud. **This is Escape 1's proposition, live at
`686a374`, through the validator rather than the adapter.**

It is **DECLARED** — DECLARED LIMIT 5 names it precisely and honestly, and I grade that declaration
**EXEMPLARY**; it told me exactly where to attack. **IT IS ALSO UNCARRIED BY THE SEAT'S OWN
ADMISSION, AND `pytest -q` IS GREEN ON THIS ROUTE.** The fifth seat's sentence is the right one and
it applies here: **DECLARING IS NOT READING.** A declared route with no carrier drifts the moment
somebody edits `_payload_snapshot`, and nothing on the board will say so.

**T2 REMAINS RED. THE GROUND IS NOW THE VALIDATOR, EXECUTED BY ME, WITH A CONTROL ARM — NOT ESCAPE
3, WHICH I REFUTE, AND NOT `runner.py:868`, WHICH I WITHDRAW.** `CD-AC-002` also remains **AMBER**
rather than moving up, on the same arm plus the nested-interior residue of §3.

**AND `CD-AC-002` GAINS A NEW GROUND I DID NOT HAVE WHEN I GRADED IT:** `CD-ASR-WO2R3-04-F01`
produces a `DialMagnitude` subclass carrying `__float__`, which is the proposition of
`plants/CD-AC-002/CD-RT-002-TYPE-NO-ARITHMETIC.patch`. **A MAGNITUDE THAT COERCES TO A NUMBER IS A
CD-AC-002 DEFECT, NOT ONLY A CD-AC-005 ONE.** I leave CD-AC-002 at AMBER rather than moving it to
RED only because the route needs in-process arbitrary code, which is the same standing I gave
everything else here — **but if the Product Owner reads F01 as a CD-AC-002 breach rather than a
CD-AC-005 one, I would not argue.**

---

# 9. T9 — THE BLINDNESS WINDOW. **RUN. AFTER FOUR GATES CARRIED IT AS "MECHANICAL AND UNRUN".**

The fifth seat called this *"the highest-value thing left on this tree, and it is mechanical"*. It
was carried unrun through the fifth, sixth and (in my §7 table, written before I did this) my own
gate. **IT IS MECHANICAL. IT TOOK ONE PASS. HERE IT IS.**

**METHOD:** over every `*.py` under `src/` and `tools/`, extract every reference of the form
`tests/<file>.py[::<name>]` appearing in a declared limit or CARRIER claim, and resolve each
against the file system and against `pytest --collect-only`.

**POPULATION, PRINTED BEFORE THE VERDICT (CD-PL-F121):**

    61 distinct (test file, test name) references, from 32 source files
    CONTROL: pytest --collect-only -> 983 distinct test names, 1699 node ids.  NON-EMPTY: True
    RESOLVES: 52    FILE MISSING: 1    NAME NOT COLLECTED: 8

**AND I APPLIED THE `CD-PL-F121` TEST TO MY OWN TABLE BEFORE PUBLISHING IT, WHICH REMOVED 4 OF MY
9 CANDIDATES.** Four "missing" names are **artefacts of my own regex meeting Python string
concatenation** — the citation continues in the next literal (`..._no_longer_"` + `"resolves..."`).
A fifth, `test_field_establishment.py::_import_the_whole_product`, is a helper and not a test node,
correctly cited. **THOSE FIVE ARE NOT FINDINGS AND I RECORD THEM AS MY OWN NEAR-MISS.** This is
the fourth-seat/`F121` failure mode arriving on schedule in the auditor's own work, caught by
running the check the dispatch told me to run on everybody else.

## WHAT SURVIVES THE TEST — **FOUR REAL STALE CARRIER CITATIONS**

### FINDING `CD-ASR-WO2R3-04-F08` — MEDIUM. Three carriers named, none of the three names exists.

`src/crash_detector/collectors/runner.py`, lines 327, 338, 351 — each a **complete single-line
string literal**, so not a wrap; I checked:

| cited as CARRIER MEASURED | actually collected as |
|---|---|
| `test_collector_admission.py::test_a_sink_that_answers_with_a_value_is_refused` | `test_a6_7_a_sink_that_answers_with_a_value_is_refused` |
| `test_collector_admission.py::test_a_ledger_verdict_that_is_not_a_bool_is_refused` | `test_a6_5_a_ledger_verdict_that_is_not_a_bool_is_refused` |
| `test_collector_admission.py::test_a_validator_that_returns_a_repaired_payload_is_a_breach` | `test_a6_6_a_validator_that_returns_a_repaired_payload_is_a_breach` |

**THE `a6_N_` PREFIX IS MISSING FROM ALL THREE.** The tests DO exist and the properties ARE
carried, so this is **not** a false carrier claim in substance. **IT IS EXACTLY T9'S QUESTION
ANSWERED: THE SITE IS NAMED, THE NAME DOES NOT RESOLVE, AND NOTHING IN THIS TREE WOULD EVER SAY
SO.** These three sit in the `ESTABLISHED_HERE(...)` block for `sink`, `ledger` and `validator` —
**the three foreign protocols at the adapter boundary, which is T2.** A reader following the
citation to check the boundary's carrier finds nothing and must guess.

### FINDING `CD-ASR-WO2R3-04-F09` — MEDIUM. A carrier declared **MEASURED** against a file that does not exist.

    tools/register/check_constructor_field_establishment.py:218
      "...**CARRIER MEASURED AND IT IS BODY-LEVEL:** ``tests/test_engine_config.py``"
    src/crash_detector/establishment.py:167
      "``tests/test_engine_config.py`` and ``tests/test_engine_model_registry.py`` measure..."

**`tests/test_engine_config.py` DOES NOT EXIST AT THIS SHA.** `ls tests/ | grep engine` returns
`test_engine_model_registry.py` and nothing else. The words **"CARRIER MEASURED"** are attached to
it in a **governed register instrument**. This is the `CD-PL-F124` shape — a field asserted as
resolved that does not resolve — **in a carrier citation instead of a SHA, and in the tree rather
than in `governance/`.** The general question the dispatch raises about SHAs applies here verbatim:
**nothing checks that a carrier citation names a real test.**

## T9 VERDICT: **AMBER, AND THE WINDOW IS NARROWER THAN FEARED.**

**52 of 61 resolve.** The blindness window is real but it is not a chasm, and I would rather say
that than inflate it. **The four that fail are all in the same shape — a name transcribed rather
than resolved — which is `CD-PL-F36` ("resolve, never transcribe") applying to carrier citations,
where nobody has ever applied it.** The check is ~40 lines and I have just written and run it;
**it belongs in `tools/` as a governed instrument, and I say that as a finding and not as a fix,
because implementing it is not mine** (`PBG-SOD-001`, `PBG-SOD-004`).

**AND THE ANSWER TO THE DISPATCH'S GENERAL QUESTION, WHICH IS NOW EVIDENCED TWICE:** *"WHEN A RULE
IS ADOPTED, IS THE RECORD EVER SWEPT BACKWARD FOR THE INSTANCES THAT MOTIVATED IT?"* **NO.**
`CD-PL-F124` found it for SHAs in `governance/`. **I HAVE NOW FOUND THE SAME ANSWER, INDEPENDENTLY,
FOR CARRIER CITATIONS IN `src/` AND `tools/`.** Two populations, same rule, same result. **THAT IS
NOT A COINCIDENCE AND IT SHOULD BE TREATED AS A PROGRAMME-LEVEL FINDING RATHER THAN TWO ITEM-LEVEL
ONES.**

---

# 10. T21 — THE TWO NEW GOVERNING INSTRUMENTS, GRADED AS ARTEFACTS

## `tools/register/check_sealed_against_forged_establishment.py` — **RED AS A CONTROL, EXCELLENT AS A CRAFT OBJECT.**

I want both halves on the record because grading it only on my finding would be unfair and would
teach the wrong lesson. **What it does well is unusual and should be copied:** it measures by
EXECUTING and tracing rather than by reading source; it reads the forged value BACK rather than
assuming a write took; it diffs two independent derivations and treats disagreement as a violation
rather than a reconciliation; it prints its arithmetic *because a predecessor's table closed at 90
of 99*; and its exclusion clause is a genuine run-time measurement, which I attacked and could not
break. **Its `R5` docstring is the best piece of technical writing in this repository.**

**AND IT IS STILL RED**, because a control is graded on whether its green means what it says, and
this one's does not (§1, §4). **THE TWO GRADES ARE NOT IN TENSION: THE CARE WENT INTO THE
MEASUREMENT AND NOT INTO THE ENUMERATION, AND THE ENUMERATION IS WHERE THE PROPERTY LIVED.**

## `tools/reconciliation/check_lane_governance_citations.py` (on `main`) — **AMBER. HONEST, REPRODUCIBLE, AND ITS DECLARED LIMIT 3 IS NOT ENOUGH.**

Re-run by me on `main`, reproducing its declared state exactly:

    DISTINCT citations 133  (PATH 23, IDENTIFIER 110)   TOTAL OCCURRENCES 2204
    files citing at least once: 235      RESOLVED against main@a7a8670: 130
    UNRESOLVED: 2   — both in tools/register/check_dockerignore.py (lines 78, 146)
    CD-LANE-CITATIONS: FAIL — 133 citations, 2 unresolved     EXIT=1

**POPULATION NON-EMPTY AND LARGE (T22 test applied).** It exits 1 truthfully. Its "WHAT 'RESOLVES'
DELIBERATELY DOES NOT MEAN" section — *existence, not agreement* — is exactly the disclosure this
project keeps asking for, made before anyone had to demand it.

**ON THE SELF-VOUCHING SHAPE** (the Project Lead wrote an instrument measuring the Project Lead's
own boundary, disclosed and not defended): **the mitigation is not independence, it is
REPRODUCIBILITY, and it holds.** I re-ran it and got its numbers. `PBG-EVID-001` is about evidence
that cannot be checked by anyone but its author; this can be, and I did. **I do not uphold the
self-vouching concern as a defect. I record that it is answered by reproducibility and would NOT be
answered by the disclosure alone.**

### **"A REGISTER WOULD BE THE STRONGER CONTROL AND IT DOES NOT EXIST; THIS IS THE WEAKER ONE, NAMED." IS NAMING IT ENOUGH?**

*** **NO — AND I CAN NOW ANSWER THAT WITH EVIDENCE INSTEAD OF PRINCIPLE.** *** §9 found **four live
unresolvable citations** in a population this instrument does not cover: carrier citations naming
test nodes in `src/` and `tools/`. Three name tests missing an `a6_N_` prefix; one asserts
**"CARRIER MEASURED"** against `tests/test_engine_config.py`, **which does not exist.** A register of
resolvable identifiers — or simply resolving the name instead of transcribing it — closes all four.

**NAMING A LIMIT IS HONEST AND IT IS NOT A CONTROL. THE INSTANCES BEHIND THE NAMED LIMIT WERE THERE
THE WHOLE TIME, AND IT TOOK ONE 40-LINE SWEEP TO FIND THEM.** That is the fifth seat's *"DECLARING
IS NOT READING"*, upheld, with a measured population behind it for the first time.

---

# 99. WHAT I DID NOT REACH, AND WHY. MEASURED LIMITS, NOT A SILENT NARROWING.

**I chose depth on T18/T19 over breadth, deliberately, because the dispatch said the sixth route was
the single most valuable thing I could return. That choice cost the items below and I am naming the
cost rather than letting the table's blank cells do it quietly.**

* **T3 — the §D scoping / CD-D-105 invitation. NOT SPENT.** The fifth seat did not spend it and said
  so; the sixth spent it and got an entire increment. **I did not spend it either.** It remains the
  highest-value unspent thing on this tree after the route-set repair.
* **T6 — the grant-matrix `exit 3` correction, inherited by three seats and re-measured by none.**
  **NOW FOUR SEATS. I DID NOT RE-MEASURE IT EITHER, AND THAT IS THE POINT OF THE TARGET.** A
  correction inherited without re-measurement four times running is a claim, and I have added my
  name to the list of people who passed it on.
* **T8 — `operand_origin` and the 50 derivation rows.** Not attacked. The `OWN_CONSTRUCTION` rows
  remain the answer that would end the enquiry, as `CD-ENG-WO2R3-04-F07` asked.
* **T14 — increment 7's reclassification and its `PASSED_TO` weakening.** Not regraded; the sixth
  seat's grading stands unchallenged by me, which is not the same as confirmed by me.
* **T17 — the `*extra` residue.** Not reached.
* **The Class-2 sweep's byte-identical `md5sum` at base and tip.** I ran the sweep only via the
  suite's three declared failures; I did not take the `md5sum` at both SHAs. **The PL's claim of
  `049c7ff8a5a3f7b5b6e0ee804b285865` at both is UNCONFIRMED BY ME.**
* **The four "attributed, not confirmed" claims from increment 8.** Still not re-run at `686a374`
  by anyone, including me.
* **The 48 excluded classes were not individually re-probed by me either** — I re-derived the
  exclusion CLAUSE and the 43/5 split, not 48 separate verdicts. Same limit the Project Lead
  declared; I did not remove it.
* **The other three sealed metaclasses** (`SealedReadingType`, `SealedQuantityType`,
  `SealedPresentationType`) are **structurally identical to the one I broke and NOT individually
  executed.** Treat `F01` as proved for `SealedMagnitudeType` and as strongly indicated for the
  other three.
* **`ctypes` and `__class__` reassignment** — two of the four routes the Engineer named as measured
  by nobody. **STILL MEASURED BY NOBODY.** I found R6/R7/R8 without needing them, so they remain
  open and may yield more. `__reduce__`/`__reduce_ex__` I did not re-take beyond the PL's pass.
* **`pbg boot` reads RED in this worktree** and I have returned `CONTROL_NOT_VERIFIABLE` for the
  continuity control in an audit worktree rather than treating the reading as either a finding or a
  harmless constant (§0).

## THE ONE I MOST WANT SOMEBODY TO CHECK BEHIND ME

**My claim that 40 of 51 forge rests on my own probe** (`/tmp/asr7/route6.py`), and per `CD-PL-F98`
and `CD-PL-F121` **you should not take my table on trust any more than I took theirs.** The
hand-verified, fully-explicit demonstration on `StalenessWindow`, `OK` and `Value` in §1 is the
part I would defend to the last; **the exact number 40 is a derived table from a seat you have no
reason to trust yet, and the honest statement is "at least three, hand-checked, and my instrument
says forty."** The cheapest possible independent check is four lines added to `ROUTES` in the
existing instrument and one re-run — **and I deliberately did NOT make that change, because
implementing it is not mine** (`PBG-SOD-001`, `PBG-SOD-004`). **I wanted to. That want is recorded
here instead, as the dispatch instructs.**

---

## CLOSING IDENTITY CHECK

    RE-TAKEN AFTER ALL WORK, BEFORE WRITING THIS LINE:
      cd /srv/crash-detector-wo2r3-audit7 && python3 -B tools/audit/tree_fingerprint.py --root .
      files fingerprinted: 509
      FINGERPRINT: 319e401fc2591dc48b611d101d5330bdb3dbb3bb9824b7bb1c39a11e5b10fc6a
      git rev-parse HEAD      -> 686a374e60ff8f18305fa8b665463e0e057dac2b
      git status --porcelain  -> 0 lines

**IDENTICAL TO THE OPENING READING. THE TARGET DID NOT MOVE AND I DID NOT MOVE IT.** Every variant
was run in `/tmp/asr7*` throwaway directories from `git archive`, every throwaway result is labelled
as one in the same paragraph as the result, no `git worktree add` was used, nothing under
`/srv/crash-detector-wo2r3-audit7` was edited, no commit was made on any branch, and nothing under
`pbg/` was touched.

    — CD-ASR-WO2R3-04, seventh Assurance seat, WO-2R3.
      VERDICT: RED.  CD-AC-002 AMBER (not closed) · CD-AC-005 RED (moved down) · T2 RED (re-grounded twice).
      A PASS IS NOT AN ACCEPTANCE AND NEITHER IS THIS (PBG-AUTH-003).

---

# 11. PROVENANCE OF MY OWN EVIDENCE CHAIN — MEASURED AFTER A HAZARD NOTICE, NOT ASSERTED

Late in this audit the Project Lead sent a **hazard notice** (explicitly not direction, and it
touched no target, method or grade): `/tmp/asr7` is a **shared** path that instance 1 of this seat
also used before it was killed, so it holds artefacts from two contexts interleaved. **This belongs
in the record because it is a `CD-PL-F98` exposure in the auditor's own evidence chain**, and
because I would rather publish the measurement than the reassurance.

**I DID NOT RELY ON MEMORY. I MEASURED IT.**

    INSTANCE 1 RESIDUE (11 files, mtimes 09:50:08 - 09:58:59):
      r6_probe.py r6_probe2.py r6_probe3.py r6_demo.py fieldless.py
      ac005.py ac005b.py ac005c.py independent.py t20c.py sweep_tip.txt
    MY OWN ARTEFACTS (12 files, mtimes 10:20:08 - 10:32:35):
      route6.py recon.py demo.py instr_sealed.txt meta.py f01.py
      escape3.py t20.py t20exec.py t20b.py validator.py t9.py
    My launch boundary: 10:17. EVERY FILE I RELIED ON POSTDATES IT. NO OVERLAP.

**THE SHADOWING RISK, CHECKED RATHER THAN DISMISSED.** Python places a script's own directory at
`sys.path[0]`, so a stale `/tmp/asr7/<name>.py` matching any module I import would silently shadow
it. My full import set across all eleven probes is:

    collections · collector_fakes · copyreg · crash_detector.* · dataclasses · datetime · enum
    importlib · importlib.util · inspect · pathlib · re · subprocess · sys

**INTERSECTION WITH THE ELEVEN STALE BASENAMES: EMPTY.** No stale module could have been imported.
I opened none of the eleven, used no glob, and `cat`-ed no captured output; `instr_sealed.txt` is
mine, written 10:21:40 from `/tmp/asr7_seal_why.log` which I generated at 10:21:35.

## *** AND THERE IS A ONE-CHARACTER NEAR-MISS THAT I AM RECORDING AS A FINDING AGAINST MYSELF ***

### `CD-ASR-WO2R3-04-F10` — INFORMATIONAL, AND IT IS THE MOST INSTRUCTIVE THING IN THIS SECTION.

    INSTANCE 1:  /tmp/asr7-plants    (HYPHEN)   created 09:55:15
    MINE:        /tmp/asr7_plants    (UNDERSCORE) created 10:26:29

**ONE CHARACTER.** I ran my entire T13 plant re-derivation and the sealing plant contrast — clean
arm rc=0, apply rc=0, violated arm rc=1 — inside `/tmp/asr7_plants`. **HAD I TYPED A HYPHEN, I
WOULD HAVE RUN THAT CONTRAST INSIDE A DIRECTORY A DEAD INSTANCE HAD ALREADY MUTATED, POSSIBLY WITH
A PLANT ALREADY APPLIED, AND I WOULD HAVE REPORTED THE RESULT AS THE TARGET'S STATE.** That is
precisely what this dispatch's `and_one_specific_to_THIS_gate` clause forbids in so many words, and
I would have had no way to notice: a `git archive` extraction and a mutated one look identical to
`ls`, and my probe printed no `tree:` line for the extraction itself. **`CD-PL-F98`'s remedy —
"RUN EACH TREE'S OWN COPY OF A PROBE, AND READ ITS `tree:` LINE EVERY TIME" — IS WRITTEN IN MY
BRIEF AND I DID NOT FULLY DISCHARGE IT FOR THE EXTRACTION DIRECTORY.** I discharged it for the
audit worktree (fingerprint at both ends) and not for `/tmp`.

**I re-verified after the fact** that `/tmp/asr7_plants` was created by my own `git archive 686a374`
at 10:26:29 and that its clean arm read `PASS — 99 assertions, 0 violations` — the tip's own value —
before I applied anything, which is the control that retrospectively establishes it was pristine.
**SO THE RESULT STANDS. THE METHOD DOES NOT, AND THE DIFFERENCE IS THE WHOLE POINT OF THIS
PROJECT.**

**THE GENERALISABLE FINDING, WHICH IS NOT ABOUT ME:** *** **NOTHING ON THIS PROJECT CHECKS THE
PROVENANCE OF A THROWAWAY EXTRACTION.** *** Every seat is told to work in `/tmp`, every seat picks
its own path, paths collide across concurrent and resurrected seats (`CD-FWK-004` — PBGv2 cannot
represent concurrent seats), and **the only thing that caught it here was a human-directed
`ls -la` on mtimes.** A contrast run in a poisoned extraction produces a confident table and a
green or red exit code with nothing anywhere to contradict it. **It is the dead-plant problem
(header item 4) with the tree as the plant, and it is one line to fix: print the extraction's
fingerprint before the first arm.** I recommend it be added to whatever carrier answers
`PO-DECISIONS-0017` ruling 1.

---

## SCOPE OF WRITES BY THIS SEAT — STATED SO NOTHING IS MISATTRIBUTED

**THE ONLY FILE I CREATED UNDER `/srv/crash-detector` IS THIS ONE.** I made no commit on any
branch, ran no `git add`, and edited nothing else. Verified at close:

    git status --porcelain (on main), non-noise lines:
      ?? governance/assurance/WO-2R3/VERDICT-SEVENTH-SEAT.md      <- MINE
       M governance/engineering/ACTIVE_WORK.yaml                  <- NOT MINE
      ?? governance/engineering/build-log/BL-20260823T093449Z-0129.yaml  <- NOT MINE

The latter two appeared on `main` while I was working and are the Project Lead's own boundary
record. **I NAME THEM BECAUSE A READER DIFFING `main` AFTER THIS AUDIT WOULD OTHERWISE HAVE TO
GUESS WHICH OF THE THREE WERE THE AUDITOR'S**, and an auditor who leaves that ambiguous has
weakened its own independence claim for no reason. `main`'s untracked count moved 45 -> 48 across
this session; **one of the three is mine** (`CD-PL-F101` continues to be re-counted rather than
tidied, correctly).

**THE TARGET ITSELF — `/srv/crash-detector-wo2r3-audit7` — IS AT `686a374`, `git status --porcelain`
ZERO LINES, FINGERPRINT `319e401f...b10fc6a`, UNCHANGED FROM THE MOMENT I BOOTED.**
