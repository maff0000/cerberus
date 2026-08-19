# PL-R6 — INDEPENDENT REPLICATION OF CD-ASR-WO2R-F01 AND F02

**Actor:** PROJECT_LEAD_SEAT_01 (ninth seat) · **Authority:** CD-AUTH-0001 · **Date:** 2026-08-19
**Target:** `50fc23177f790164c3fc3604ccee51663e755c70`
**Owed by:** ACTIVE_WORK.yaml `next_safe_action` at 8a14749 — *"THE NEXT PROJECT LEAD SEAT'S FIRST
ACT, BEFORE ANY DISPATCH: INDEPENDENTLY REPLICATE ASR2-F01 AND ASR2-F02 on its own pristine
`git archive` extractions of 50fc231."*

**VERDICT: BOTH FINDINGS REPLICATE EXACTLY. THE AUDITOR IS CONFIRMED ON BOTH HIGH FINDINGS.**
**AND A THIRD THING WAS FOUND — CD-PL-F74, a method finding about RECONCILIATION ITSELF.**

---

## 0. TARGET INTEGRITY — established before anything was measured

Three independent `git archive 50fc231 | tar -x` extractions, each into a throwaway directory
OUTSIDE every governed worktree. No clone, no checkout, no worktree — `git archive` cannot carry a
dirty tree, which is why it is the extraction this project uses at a gate.

    files extracted                              364
    sha256 over the sorted per-file digests      50ae34d657126709c0e44b3a57c58c8308d25c1cb845aa70b30e86338a2d729d

**That fingerprint MATCHES the one CD-ASR-WO2-02 recorded (`50ae34d6…`), computed independently by
this seat with no sight of the auditor's command.** 364 files both times. The auditor and this seat
measured the same tree. Target integrity is not taken on trust here; it is the precondition that
makes every number below comparable at all.

---

## 1. CD-ASR-WO2R-F01 — **REPLICATES EXACTLY. CONFIRMED.**

Variant under test: the auditor's `variants/ASR2-002-A-derivation-door-launders-a-blend.py.txt`,
replanted at `src/crash_detector/publication/composite.py`. The variant is the artefact whose claim
is being replicated, so it is used verbatim. **The driver is this seat's own**
(`PL-R6-F01-driver.py.txt`), written from the source at 50fc231 — the inputs are built through the
legitimate admission door `observed_for_dial`, and the publication attempt and every assertion are
this seat's.

### The structure, read before it was run

`src/crash_detector/dials/magnitude.py:620-622`:

    return DialMagnitude(
        dial_id=dial_id,
        quantity=derived_within_one_dial(dials=dials, value=using(numbers)),

`derived_within_one_dial` (`provenance.py:543`) is four lines and its body is
`return DeclaredQuantity(dials=dials, value=value)`. **It validates the dial set it was handed and
does not look at the value at all.** The comment directly above the call site says so in terms —
*"`using` may return any float it likes and cannot influence which dial the result is declared
for"* — which is true and is exactly the gap: it cannot influence the LABEL, and it does not need
to. It supplies the VALUE.

`combine_within_one_dial` is public API and is absent from
`check_no_blend.py`'s `ADMISSION_VOCABULARY`. Confirmed at 50fc231.

### MEASURED — every declared layer green WITH the variant present

    CD-RT-002-AST-NO-BLEND        EXIT 0   PASS — 4873 assertions, 0 violations
    CD-RT-002-SCHEMA-CLOSED       EXIT 0   PASS —  242 assertions, 0 violations
    CD-RT-001-AST-NO-NUMERIC-DEF  EXIT 0   PASS —  377 assertions, 0 violations
    CD-RT-002-TYPE-NO-ARITHMETIC  EXIT 0   306 passed
    WHOLE SUITE   PYTHONPATH=src python3 -m pytest tests -q     EXIT 0   1325 passed

    CLEAN ARM (no variant), same command, separate extraction:
    CD-RT-002-AST-NO-BLEND        EXIT 0   PASS — 4855 assertions, 0 violations

**F16 CONTRAST: 4855 → 4873. The count ROSE by 18. The check DID scan the new module and had
nothing to say about it.** This is not a skipped arm or a shrunk denominator; it is a clean pass
over a live blend. Every one of these five numbers is IDENTICAL to the auditor's.

### THEN EXECUTED

    equity   magnitude: DialMagnitude(dial_id='equity_crash', quantity=0.9)
    monetary magnitude: DialMagnitude(dial_id='monetary_debasement', quantity=0.1)

    RESULT TYPE : DialMagnitude
    RESULT      : DialMagnitude(dial_id='equity_crash', quantity=0.5)
    provenance  : ['equity_crash']
    EXACT DialMagnitude (type identity, not isinstance)? True
    released quantity_for('equity_crash') : 0.5

    score type       : *** NOT REFUSED *** -> EquityCrashScore(score=DialMagnitude(...quantity=0.5), contributions=())
    publication gate : *** NOT REFUSED *** -> 0.5

**Equity 0.9 and monetary 0.1 publish as an equity reading of 0.5.** That is the failure PID §3.1
calls constitutional — averaging cancels the signal.

### The proposition that is false

`magnitude.py:117-122`, boundary A, quoted verbatim from the target:

>  "What IS claimed, and is measured: **the sum cannot come back.** … Read it as claiming that no
>   number so obtained can ever be a dial magnitude again."

**Measured FALSE at this SHA.** The claim is unqualified, and CD-RULE-006 forbids a boundary that
asserts a carrier that does not carry. The auditor's reading is correct and the severity is
correct.

---

## 2. CD-ASR-WO2R-F02 — **REPLICATES EXACTLY. CONFIRMED.**

Variant: the auditor's `variants/ASR2-005-A-datetime-subclass-lies-about-age.py.txt`, replanted at
`src/crash_detector/serving/panel_feed.py`. Driver this seat's own
(`PL-R6-F02-driver.py.txt`) — **and it carries a CONTROL ARM the auditor also ran, because a
one-armed measurement here proves nothing.**

### The structure

`time_utc.py:37` — `if not isinstance(value, datetime)` — admits any subclass.
`time_utc.py:50` — `return value.astimezone(timezone.utc)` — and the subclass overrides
`astimezone` to return `self`, so **the subclass survives the normalisation**.
`time_utc.py:106` — `age_seconds` is `(ensure_utc(now) - ensure_utc(as_of)).total_seconds()`, and
for a subclass on the right Python tries the reflected `__rsub__` FIRST.

### MEASURED — a row dated 2016-08-21 read at 2026-08-19 with a 600 s window

    --- ATTACK  — as_of_utc is a FeedInstant (datetime SUBCLASS)
       type after PanelRow normalisation : FeedInstant   (survived: True)
       resolved                          : Agrees
       RENDERS                           : WITNESS AGREES

    --- CONTROL — the SAME decade-old instant as a PLAIN datetime
       type after PanelRow normalisation : datetime
       resolved                          : Unavailable
       RENDERS                           : WITNESS UNAVAILABLE

**Identical data, identical window, identical call. The only variable is the concrete type of the
timestamp.** No `object.__setattr__`, no reflection, no post-construction write anywhere in the
driver. The value reaches `Agrees` through `PanelRow.__post_init__`, `resolve_panel`,
`StalenessWindow.__post_init__` and `FreshnessEvidence.__post_init__` — every constructor on the
path ran.

### Every declared guard green with it present

    CD-RT-005-PANEL-UNAVAILABLE-NEVER-AGREES   EXIT 0   152 passed
    WHOLE SUITE  pytest tests -q                EXIT 0   1325 passed
    check_no_numeric_default                    EXIT 0   PASS —   377 assertions
    check_no_blend                              EXIT 0   PASS —  4873 assertions
    check_engine_no_witness_reach               EXIT 0   PASS —    24 assertions
    check_no_execution_interface                EXIT 0   PASS — 38881 assertions

### The proposition, and the boundary that invited exactly this

`staleness.py` boundary 3, verbatim:

>  "every route measured that goes through a CONSTRUCTOR is refused. **THREE MEASURED, and three is
>   the denominator, not a proof that a fourth does not exist**"

**This is the fourth.** The boundary was drawn honestly — it declined to claim what it had not
measured, and that honesty is why F02 is AMBER on CD-AC-005 rather than RED. The guard applied its
own doctrine ("a subclass of a number is not a number: it may redefine what comparison means") to
one operand of the comparison and never to the other.

### The severity claim, MEASURED rather than accepted

The auditor argues HIGH partly on `pandas.Timestamp` being a `datetime` subclass. **Checked by
execution on this host:**

    pandas 2.1.4 — issubclass(pandas.Timestamp, datetime.datetime) -> True

**And a qualification this seat adds in the auditor's favour and against its own convenience:**
`grep -rn pandas src/ tests/ tools/` at 50fc231 returns NOTHING. This project does not depend on
pandas today. That makes the route *latent* rather than *live* — which lowers the probability but
not the severity, because CD-AC-005 is a claim about *any* input, WO-3 is where sources get
registered (CD-D-005, zero registered today), and a collector handing the resolver a
`pandas.Timestamp` is, as the auditor put it, not an attack but a Tuesday. **HIGH is upheld.**

---

## 3. CD-PL-F74 (HIGH, METHOD) — **WHY CD-D-040 ACCEPTED MORE THAN IT MEASURED**

The `next_safe_action` at 8a14749 anticipated this precisely: *"ASR2-F01 CONTRADICTS CD-D-040, an
acceptance this project already made … If PL-R5 was read as proving more than it did, that is a
method finding about RECONCILIATION ITSELF and it must not be lost inside the repair."*

**It was. It is. And here it is, measured rather than argued.**

### First: PL-R5's refusal reproduces exactly

`PL-R5-launder-through-the-declared-door.py.txt` replanted at
`src/crash_detector/publication/banner.py` on a pristine extraction:

    CD-RT-002-AST-NO-BLEND: FAIL — 2 violation(s)      (banner.py:3 and banner.py:21, both RULE 4)

As recorded. CD-D-040 accepted increment 2b on this, *"by structure at the re-entry PLUS a
deny-by-default static layer at the doors"*.

### Then: what RULE 4's own violation text CLAIMS

Quoted verbatim from the check's output at 50fc231:

>  "a module that launders two dials into one figure need name no dial and perform no arithmetic on
>   a magnitude … **but it cannot avoid coming here.**"

### The one-variable experiment

`PL-R6-banner-door-swapped.py.txt` is **PL-R5 with exactly one thing changed: the door.** Same
intent, same mean, same loop, same publication into a slot. `observed_for_dial` →
`combine_within_one_dial`.

    PL-R5  (door: observed_for_dial)        CD-RT-002-AST-NO-BLEND: FAIL — 2 violations  (4887 assertions)
    PL-R6  (door: combine_within_one_dial)  CD-RT-002-AST-NO-BLEND: PASS — 0 violations  (4882 assertions)

    PL-R6 banner result : EquityCrashScore(score=DialMagnitude(dial_id='equity_crash', quantity=0.5), ...)
    publication gate    : 0.5

**"It cannot avoid coming here" is FALSE, and one identifier is the whole difference.**

### The ruling, and it is about method, not about this guard

**PL-R5 WAS NEVER EVIDENCE THAT THE CLASS WAS CLOSED. It was evidence that PL-R5 named a door that
was in the vocabulary.** A deny-by-default registry is only as closed as its vocabulary, and this
vocabulary had a public proxy missing from it. The refusal was real; the *inference drawn from the
refusal* was wider than the refusal supported, and CD-D-040 recorded that wider inference as an
acceptance.

This is the **CD-ENG-WO2R-F13 pattern — a probe refused for the wrong reason — and it is the SIXTH
recurrence on this project, but the FIRST aimed at an ACCEPTANCE rather than at a probe.** The five
prior instances cost a re-run. This one cost a GATE: increment 2b was accepted, the work order ran
on, and an auditor found the same class open one function across, two gates later.

**THE STANDING METHOD CORRECTION, offered to the Product Authority and NOT self-adopted, because a
rule that binds future seats is not this seat's to make:** when a probe is REFUSED, the record must
state *which layer refused it and what that layer's stated scope is*, before any acceptance cites
it. A refusal by a registry is evidence about the registry's vocabulary — never about the class.
The question CD-D-040 never asked is the one that would have found this in one line: **"what is in
the vocabulary, and what is a door that is not in it?"**

---

## 4. WHAT THIS REPLICATION DOES NOT REACH — stated, not footnoted

* The three AMBER criteria (CD-AC-001, CD-AC-005, CD-AC-012) were **not** re-measured here. This
  seat replicated the two HIGH findings it was told to replicate, plus the CD-D-040 question. The
  AMBERs stand as the auditor left them.
* F03 through F13 were **not** independently replicated. Not doubted — not reached.
* Nothing here re-opens W1/W5/W7. The auditor's target-integrity and grant-matrix work is confirmed
  only to the extent that the target fingerprint matched.
* **No repair was designed and none is proposed.** `PBG-SOD-004`. The shape of the fix is the
  Engineer's to answer, and the scoping is the Product Authority's.

---

## 5. CONSEQUENCE FOR THE GATE

**NONE OF THIS CHANGES THE VERDICT. It confirms it.** CD-ASR-WO2-02's RED on CD-AC-002 stands,
independently reproduced. The WO-2 gate is NOT MET. Nothing is admitted; `latest_admitted_run`
remains null (CD-RULE-001, non-relaxable, and not sought).

CD-D-073 stands: **the Project Lead does not dispatch WO-2R2.** A second consecutive failure of a
rework the Product Owner personally ordered and scoped is that authority's question. CD-PL-F74
makes the case for stopping *stronger*, not weaker — because it shows the failure is not only in
the code but in how this project has been reading its own acceptances, and re-scoping that on the
PL's own authority is the exact error it names.
