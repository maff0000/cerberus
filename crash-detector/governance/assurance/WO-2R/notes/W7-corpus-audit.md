# W7 — Corpus audit (ASSURANCE data gathering)

Target SHA: 50fc23177f790164c3fc3604ccee51663e755c70
Read-only reference: /srv/crash-detector-wo2r-audit  (NEVER executed in)
Execution sandbox: /tmp/w7/* extracted from /tmp/cd-asr-wo2r/target.tar

## (1) DENOMINATOR — SETTLED

Method (read-only, no cwd inside the audit tree):

    find /srv/crash-detector-wo2r-audit/variants -type f | wc -l                    -> 73
    find ... -name '*.patch' | wc -l                                                -> 70
    find ... -name '*.py.txt' | wc -l                                               ->  2
    find ... -type f ! -name '*.patch' ! -name '*.py.txt'                            -> 1 file:
        /srv/crash-detector-wo2r-audit/variants/WO-2R/MANIFEST.md
    find ... -type l                                                                -> none (no symlinks)
    find ... -type f -perm -u+x                                                     -> EMPTY (no executables)
    find ... -type f -printf '%m\n' | sort | uniq -c                                -> 73 x mode 664

TRUE MEASURED NUMBERS:
  - 70  *.patch
  -  2  *.py.txt   (CD-PL-F65/PL-W3-Agrees-is-unslotted.py.txt,
                    CD-PL-F65/PL-W5-a-forged-Agrees-renders-WITNESS-AGREES.py.txt)
  -  1  other      (MANIFEST.md)
  - 73  total files;  72 artefacts (patch+py.txt) + 1 manifest
  - 0 executable (no +x on any of the 73; all 0664)

VERDICT: the PROJECT LEAD's count is correct (70 + 2 = 72 artefacts, 73 files).
The ENGINEER seat's "71 re-run, 71 verdicts" does not match any file count in
the tree: neither 71 patches (70), nor 71 artefacts (72), nor 71 files (73).
The Engineer's denominator is unreconciled with the corpus on disk.

Directory breakdown (10 dirs incl. root):
  WO-2R/READER            6 patches (R01,R02,R04,R05,R06,R07 — note NO R03)
  WO-2R/CD-ENG-READER-F05 2 patches (V52,V53)
  WO-2R/CD-PL-F62         3 patches (PL-U6b, V45, V46)
  WO-2R/CD-ASR-F01       12 patches (E01,E02,PL-Q9,V07..V17)
  WO-2R/CD-PL-F65         2 .py.txt (PL-W3, PL-W5)
  WO-2R/CD-ASR-F05       14 patches (E06,V31..V44)
  WO-2R/CD-ASR-F02-F03    8 patches (E03,E04,V01..V06)
  WO-2R/CD-ASR-F04       16 patches (E05,V18..V30 incl V29a,V29b)
  WO-2R/CD-ASR-F06        7 patches (E07,E08,V47..V51)
  Sum: 6+2+3+12+2+14+8+16+7 = 70 patches + 2 py.txt = 72 artefacts. CONSISTENT.

Gaps in the V-numbering: V54+ absent; no R03. Numbering is not a reliable count proxy.

---

## (2) CD-ENG-WO2R-F27 — RE-MEASURED — **REPRODUCES EXACTLY**

Row/claim location: MANIFEST.md lines 639-652 (the boxed SUPERSEDED note above the
`BLEND-PROBE, written out in full` block) and lines 1764-1783 (the corrected probe).
The BLEND-PROBE literal source is MANIFEST.md lines 658-712.

Method:
  rm -rf /tmp/w7/f27 && mkdir -p /tmp/w7/f27
  tar -x -C /tmp/w7/f27 -f /tmp/cd-asr-wo2r/target.tar
  (verified: diff -r --brief between the audit tree's variants/ and the extraction's
   variants/ is EMPTY — the tar is the same corpus)
  cd /tmp/w7/f27 && git apply -v variants/WO-2R/CD-ASR-F01/E01-inter-procedural-fold.patch
      -> "Applied patch src/crash_detector/serving/banner.py cleanly." rc=0
  wrote blendprobe.py = MANIFEST lines 659-691 VERBATIM + the E01 arm uncommented
      (from crash_detector.serving.banner import banner_figure / report("E01", ...))
  PYTHONPATH=src python3 -B blendprobe.py

OBSERVED (exit 1, UNCAUGHT traceback — `report` is never reached):

    Traceback (most recent call last):
      File "/tmp/w7/f27/blendprobe.py", line 13, in <module>
        score=DialMagnitude(dial_id=EQUITY_DIAL_ID, quantity=0.9), contributions=()
      File "/tmp/w7/f27/src/crash_detector/dials/magnitude.py", line 377, in __init__
        _install(self, dial_id, quantity)
      File "/tmp/w7/f27/src/crash_detector/dials/magnitude.py", line 330, in _install
        raise QuantityProvenanceMissing(
    crash_detector.dials.provenance.QuantityProvenanceMissing: a bare number (0.9) was
    offered as dial 'equity_crash''s magnitude. A magnitude is built from a
    DeclaredQuantity — a number whose provenance was established at one of two declared
    doors: observed_for_dial() ... or combine_within_one_dial() ... (PID §3.1, CD-AC-002,
    CD-ASR-F01, CD-PL-F54).

CONTROL: the identical probe on a CLEAN extraction (no patch applied, /tmp/w7/f27clean)
dies with the SAME error at the SAME line. The failure is variant-INDEPENDENT: the two
fixture constructions are at MODULE level (lines 13 and 18), so the first one raises
before any variant module is imported or called. Therefore the claim "every arm dies at
scaffolding" is structurally true for ALL of E01, E02, V07, V08, V09, V10, V11 — the arm
selection is textually below the fixture and unreachable.

VERDICT F27: REPRODUCES EXACTLY, including the quoted exception text
`QuantityProvenanceMissing: a bare number (0.9) was offered as dial 'equity_crash''s
magnitude`. The MANIFEST's own warning is accurate. This is a self-declared defect, and
the correction at lines 1764-1779 is present in the same file.

---

## (3) CD-ENG-WO2R-F28 — RE-MEASURED — **REPRODUCES EXACTLY**

V11 row: MANIFEST.md lines 412-423.  Summary row: line 437.  Defect note: lines 1795, 1800-1812.

WHAT THE ROW CLAIMS (lines 420-423):
  command            : `BLEND-PROBE`, then `AST`
  construction       : "The merged object IS constructed", provenance
                       frozenset({'equity_crash','monetary_debasement'})
  refusal at THREE boundaries, all by comparing DATA:
     B1 merged.quantity_for('equity_crash')            -> CrossDialCombination
     B2 number_for_dial_slot('equity_crash', merged)   -> DialProvenanceRefused
     B3 EquityCrashScore(score=merged, ...)            -> CrossDialCombination
  AST                : exit 1, FAIL — 2 violations, RULE 3, merged.py:23 and merged.py:32

APPLY:
  cd /tmp/w7/f28 && git apply -v variants/WO-2R/CD-ASR-F01/V11-provenance-union-not-comparison.patch
  -> "Applied patch src/crash_detector/publication/merged.py cleanly." rc=0    APPLIES: YES

ARM 1 — the row's LITERAL declared command (BLEND-PROBE as written at line 658):
  exit 1, dies at blendprobe.py line 13 with
  `QuantityProvenanceMissing: a bare number (0.9) was offered as dial 'equity_crash''s magnitude`
  i.e. F27 — the scaffolding, not V11. The V11 arm is never reached.

ARM 2 — the CORRECTED BLEND-PROBE (increment-6 fix, MANIFEST lines 1769-1778):
  V11 construction: REFUSED -> builtins.TypeError:
      unsupported operand type(s) for +: 'int' and 'DeclaredQuantity'
  raised at src/crash_detector/publication/merged.py line 32, inside merged_magnitude,
  at `sum(quantities) / len(quantities)` where `quantities` are the raw private-slot
  values, which are DeclaredQuantity objects since increment 2b — not floats.

  CONSEQUENCE: the object is NEVER CONSTRUCTED, so `merged.provenance`,
  `quantity_for`, `number_for_dial_slot` and `EquityCrashScore` are ALL UNREACHABLE
  by V11's declared route. The row names three boundaries its command does not reach.
  THE CLAIM REPRODUCES EXACTLY, error text verbatim as recorded at line 1795.

ARM 3 — AST (`python3 -B tools/register/check_no_blend.py --root .`) under V11:
  exit 1, `CD-RT-002-AST-NO-BLEND: FAIL — 2 violation(s)`, assertions 4890,
  both `RULE 3: reaching past the declared magnitude release`,
  at src/crash_detector/publication/merged.py:23 and :32.
  MATCHES the row (line 423) EXACTLY.

ARM 4 — the F28 correction note's own claim, that the three boundaries still hold when
the forged magnitude is built DIRECTLY (bypassing merged_magnitude). Built the forged
magnitude by __new__ + object.__setattr__ with provenance union and a mean of two
RELEASED floats. Observed provenance frozenset({'equity_crash','monetary_debasement'}):
  B1 CrossDialCombination: "this magnitude's provenance is ['equity_crash',
     'monetary_debasement'], and the caller asked for it as 'equity_crash'"      VERBATIM
  B2 DialProvenanceRefused: "nothing may be published into the 'equity_crash' slot
     without the provenance that says it belongs there: ... which is not exactly
     one dial"                                                                    VERBATIM
  B3 CrossDialCombination: "EquityCrashScore.score was given a magnitude whose
     provenance is ['equity_crash','monetary_debasement'], and this dial is
     'equity_crash'"                                                              VERBATIM

VERDICT F28: REPRODUCES EXACTLY in both directions. The row's three named boundaries are
unreachable by its own command (the defect), AND those three boundaries genuinely still
refuse when reached by another route (the mitigation). The MANIFEST's self-declaration at
lines 1800-1812 is accurate and complete. Direction of drift is SAFE (refused earlier),
but the row as written would mislead a future auditor about WHICH layer carried it.

NOTE (mine, additional): F28's severity compounds with F27. V11's declared command is
`BLEND-PROBE, then AST`. Retyped literally, the command produces NEITHER the row's outcome
NOR F28's outcome — it produces the F27 scaffolding refusal. An auditor must apply BOTH
declared corrections (the corrected probe AND the F28 note) to observe anything about V11.

---

## (4) CORPUS SAMPLE

### 4.0 — APPLY SWEEP OVER **ALL 70** PATCHES (not a sample — the full set)

Method: for each of the 70 *.patch, a FRESH `tar -x` extraction from
/tmp/cd-asr-wo2r/target.tar into its own mktemp dir under /tmp/w7, then
`git apply --check <patch>` in that dir; dir deleted after.

RESULT: **70 / 70 apply cleanly. 0 apply failures.** (log: /tmp/w7/apply-sweep.txt)
This CONFIRMS the increment-6 claim "0 apply failures" but on a denominator of
**70 patches, not 71** (line 1762 of MANIFEST.md says "71 patches, 71 verdicts").

Note: the 2 *.py.txt are probes, not patches, so they cannot be `git apply`-ed.
70 + 2 = 72. There is no reading of the tree under which the number is 71.

### 4.1 — SAMPLE SELECTION AND DENOMINATOR

**22 of 70 patches (31%) run end-to-end** with their MANIFEST-declared command,
chosen NOT at random but by the brief's hazard criterion: variants touching the
structures increments 1-6 REWROTE, i.e. exactly where a row is most likely to
have gone stale.

  group A — DialMagnitude / DeclaredQuantity admission door (rewritten at incr 2b):
      V09, V10, V11(see §3), V12, V13, V15, V16, V17, PL-Q9        [8 + V11]
  group B — dial provenance / RULE F (check_no_numeric_default):
      E04, V06, V14                                                [3]
  group C — pending / egress closure (rewritten incr 3 + reader-F05):
      V26, V27, V29a, V53                                          [4]
  group D — container-derivation walk root (rewritten incr 4):
      V37, V43, V44                                                [3]
  group E — FreshnessEvidence / staleness window (rewritten incr 5):
      V47, V48, V49, V51                                           [4]

Deliberately INCLUDED: the rows that claim exit 0 / NOT REFUSED (V29a, V44,
V12/V13/V15/V17). A row claiming a pass is exactly as capable of going stale as
one claiming a refusal, and a stale pass row is the more dangerous of the two.

Every run: fresh `tar -x` extraction into its own mktemp dir, `git apply`,
declared command run verbatim in that dir, dir deleted. Nothing run in /srv.

### 4.2 — GROUP B, RULE F (`timeout 120 python3 -B tools/register/check_no_numeric_default.py --root .`)

| variant | applies | row claims | observed | verdict |
|---|---|---|---|---|
| E04 | YES | exit 1, `F: unrecognised magnitude provenance`, "the magnitude IS the literal `0.0`" | exit 1, FAIL 1 violation, `F: unrecognised magnitude provenance` at evaluate.py:315, text VERBATIM incl. "`QUIET_MAGNITUDE` is bound in an enclosing scope ... the magnitude IS the literal `0.0`" | **MATCH** |
| V06 | YES | exit 1, `F: unrecognised magnitude provenance`, "`float` is not a declared source ... declared sources are ['compute']" | exit 1, FAIL 1 violation, `F` at evaluate.py:317, text VERBATIM | **MATCH** |
| V14 | YES | NUMDEF exit 1, 1 violation **at `src/crash_detector/engine/evaluate.py:306`**, `rule: F` | exit 1, 1 violation, `rule: F`, **at evaluate.py:314** — RULE ID and outcome match; **LINE NUMBER DRIFT 306 -> 314** | **MATCH (line drift)** |

### 4.3 — GROUP C, EGRESS (`timeout 120 python3 -B tools/register/check_egress_no_broker.py --root .`)

| variant | applies | row claims | observed | verdict |
|---|---|---|---|---|
| V26 | YES | exit 1, 1 violation, compose.yaml:426, `CD-EGRESS-007: pending is not a list` | exit 1, FAIL 1, compose.yaml:**426**, `CD-EGRESS-007: pending is not a list`, prose VERBATIM | **MATCH** |
| V27 | YES | exit 1, 1 violation, `CD-EGRESS-007: a pending entry's key set is not the declared key set`, "unknown key(s) `host` and misses nothing" | exit 1, FAIL 1, compose.yaml:428, same rule, prose VERBATIM incl. "A HOST IS THE ONE THING A PENDING ENTRY CANNOT CARRY" | **MATCH** |
| V29a | YES | **exit 0**, `PASS — 69 assertions, 0 violations` — the DECLARED ESCAPE | exit 0, `PASS — 69 assertions, 0 violations` | **MATCH** (escape still escapes) |
| V53 | YES | exit 1, `CD-EGRESS-007: a pending entry field is not a non-empty scalar`, "`declared_in` as nothing at all" | exit 1, FAIL 1, compose.yaml:427, same rule, assertions 69, prose VERBATIM | **MATCH** |

### 4.4 — GROUP D, CONTAINER-DERIVATION WALK ROOT
(`timeout 120 python3 -B tools/register/check_engine_no_witness_reach.py --root .`)

CLEAN ARM measured at this SHA: exit 0, `PASS — 24 assertions`, 40 modules, 16 reachable
from 5 roots.  (The MANIFEST's clean arm at line 1185 records 23 at dae6503.)

| variant | applies | row claims | observed | verdict |
|---|---|---|---|---|
| V37 | YES | exit 1, root `crash_detector.runtime.engine_main`, sys.path roots `/app/src, /app`; and separately (line 1226) "V37's assertion count DROPS to 22 where the clean arm is 23" | exit 1, FAIL 1 violation, `rule: engine reaches witness code`, route `crash_detector.witness.panel <- crash_detector.runtime.engine_main`, sys.path roots `/app/src, /app`, **assertions 23 against a clean arm of 24** | **MATCH** on rule/route/root. Assertion counts are absolute-stale (22/23 recorded, 23/24 measured) but the -1 DELTA the row reasons from is preserved. |
| V43 | YES | exit 3, `CD-ENGINE-ROOT-110` | exit 3, `PRECONDITION_NOT_MET`, `CD-ENGINE-ROOT-110`, naming `/app/extra/hidden.py` | **MATCH** |
| V44 | YES | exit **0**, IT ESCAPES (declared limit boundary 6 / CD-ENG-WO2R-F17); incr-6 restates `V44 0/24` | exit 0, `PASS — 24 assertions, 0 violations` | **MATCH** — the declared escape STILL escapes |

### 4.5 — GROUP E, FRESHNESS / STALENESS WINDOW
CD-AC-005 command: `PYTHONPATH=src python3 -B -m pytest tests/test_witness_panel.py tests/test_witness_resolver.py tests/test_staleness.py -q`
V51 uses CD-AC-001's: `PYTHONPATH=src python3 -B -m pytest tests/test_reading.py tests/test_evaluate.py -q`

| variant | applies | row claims | observed | verdict |
|---|---|---|---|---|
| V47 | YES | exit 1, `24 failed, 128 passed`, `FreshnessNotEstablished` | exit 1, **24 failed, 128 passed**, `FreshnessNotEstablished` present in the failure output | **MATCH** |
| V48 | YES | exit 1, `1 failed, 152 passed`, `TypeError: staleness window must be a plain int or float ... got _NeverGreater` | exit 1, **1 failed, 152 passed**, that TypeError VERBATIM at staleness.py:306, test `test_PLANT_V48_...` | **MATCH** |
| V49 | YES | exit 1, `1 failed, 152 passed`, `TypeError: WideWindow may not subclass StalenessWindow ...`, raised at class CREATION | exit 1, **1 failed, 152 passed**, that TypeError VERBATIM raised from `__init_subclass__` at the `class WideWindow(StalenessWindow):` statement | **MATCH** |
| V51 | YES | exit 1 **on CD-AC-001's command**, `1 failed, 100 passed`, `StalenessWindowOutOfRange` | exit 1, **1 failed, 100 passed**, `StalenessWindowOutOfRange: staleness window 1e+18 seconds exceeds the ceiling of 900.0 seconds and is REFUSED, not clamped` VERBATIM, test `test_PLANT_V51_...`. CONTROL: under CD-AC-005's command V51 is exit 0 / 152 passed — which the MANIFEST states explicitly at line 1841 | **MATCH** — and the MANIFEST is honest about the command substitution |

### 4.6 — GROUP A, ADMISSION DOOR (LAUNDER-PROBE / corrected BLEND-PROBE + `check_no_blend.py`)

LAUNDER-PROBE retyped verbatim from MANIFEST lines 726-778. BLEND-PROBE retyped with the
increment-6 correction (lines 1769-1778) since the literal version cannot run (F27).

| variant | applies | row claims | observed | verdict |
|---|---|---|---|---|
| PL-Q9 | YES | probe REFUSED `QuantityProvenanceMissing: a bare number (0.5) ...`; AST exit 0 (incr-6: 0/4883) | REFUSED, message VERBATIM; AST exit 0, `PASS — 4883 assertions` | **MATCH** incl. assertion count |
| V09 | YES | probe REFUSED `KeyError: 'quantity'`; AST exit 1, 1 violation `RULE 3` at `wire_state.py:14` | REFUSED `builtins.KeyError: 'quantity'`; AST exit 1, FAIL 1, `RULE 3` at **wire_state.py:14** | **MATCH** incl. line |
| V10 | YES | probe REFUSED `TypeError: '>' not supported between instances of 'DialMagnitude' and 'DialMagnitude'`; AST exit 0 (incr-6: 0/4871) | REFUSED VERBATIM; AST exit 0, `PASS — 4871 assertions` | **MATCH** incl. count |
| V12 | YES | runtime **NOT REFUSED**, returns `EquityCrashScore(score=DialMagnitude(dial_id='equity_crash', quantity=0.5), contributions=())`; AST exit 1, **2 violations RULE 4 at banner.py:4 and :22** | NOT REFUSED, return value VERBATIM; AST exit 1, 2 violations `RULE 4`, at banner.py:4 and **:25** | **MATCH on substance; LINE MISMATCH (:22 recorded, :25 measured)** |
| V13 | YES | runtime NOT REFUSED; AST exit 1, **1 violation RULE 4 at banner.py:19** | NOT REFUSED, same return value; AST exit 1, 1 violation `RULE 4` at banner.py **:22** | **MATCH on substance; LINE MISMATCH (:19 recorded, :22 measured)** |
| V15 | YES | runtime NOT REFUSED; AST exit 1, **2 violations RULE 4 at banner.py:4 and :19** | NOT REFUSED, same return value; AST exit 1, 2 violations `RULE 4`, at banner.py:4 and **:23** | **MATCH on substance; LINE MISMATCH (:19 recorded, :23 measured)** |
| V16 | YES | leaks print `0.4` and `0.6`, both re-entries REFUSED `QuantityProvenanceMissing: a bare number (0.5) ...`; AST exit 1, 6 violations RULE 3 | f-string leak 0.4 0.6, json leak 0.4 0.6; both arms REFUSED, message VERBATIM; AST exit 1, FAIL **6 violation(s)**, all RULE 3 in wire_text.py | **MATCH** |
| V17 | YES | runtime NOT REFUSED; AST exit 1, **6 violations RULE 3 at banner.py:6, :7, :16, :17** | NOT REFUSED, same return value; AST exit 1, FAIL 6 violations RULE 3 at banner.py **:10, :11, :21, :22** | **MATCH on substance; LINE MISMATCH (all four line numbers wrong)** |

#### 4.6a — THE LINE-NUMBER MISMATCH IS NOT ROUNDING. IT IS RECORD/ARTEFACT DIVERGENCE.

The four mismatching rows all concern patches that CREATE `src/crash_detector/serving/banner.py`
from `/dev/null` (`new file mode 100644`, hunk `@@ -0,0 +1,N @@`). A whole-file creation makes
the produced file's line numbers a DETERMINISTIC property of the patch bytes — there is no
context, no offset, no fuzz. `git apply -v` confirms "Applied ... cleanly", no offset reported.

Therefore the measured line numbers are the only ones this patch can produce, and the recorded
ones are wrong FOR THE ARTEFACT AS IT NOW STANDS ON DISK. Verified by reading the patch bytes:

  V12 patch: file line 4 = `from crash_detector.dials.provenance import observed_for_dial` (row
  correct); the `observed_for_dial(` CALL is at file line 25 (patch line 31). Row says 22.

  V17 patch: file lines 10, 11, 21, 22 are respectively
    `inner = getattr(reading, "_DialMagnitude__quantity")`
    `return inner._DeclaredQuantity__value`
    `inner = getattr(carrier, "_DialMagnitude__quantity")`
    `object.__setattr__(inner, "_DeclaredQuantity__value", total / len(figures))`
  Row says 6, 7, 16, 17 — a uniform +4 / +5 shift, consistent with the patch having gained the
  `total = 0.0 / for figure in figures: total = total + figure` loop AFTER the row was written.

CONCLUSION: the CD-ASR-F01 banner.py variant patches were EDITED after their MANIFEST rows were
measured, and the rows' locations were never re-measured. Increment 6's own re-run (line 1816-
1818) records only EXIT CODES for these variants (`V12 1, V13 1, V15 1, V17 1`), so it could not
have caught this: an exit code is invariant under the edit and the line number is not.

SEVERITY (my assessment): LOW-to-MODERATE, and NOT the hazard the brief names. Every one of the
four still (a) applies, (b) reaches the boundary its row names, and (c) names the RULE ID the row
claims (RULE 4 / RULE 3). A future auditor is directed to the right layer and the right rule; only
the cited coordinate is stale. It is nevertheless a measured divergence between the record and the
artefact, in the file whose entire stated purpose is to be the next auditor's exclusion set, and
it went undetected by the increment-6 re-run.

### 4.7 — WHERE DOES "71" COME FROM? IT COMES FROM NOWHERE.

MANIFEST.md line 1762: *"71 patches, 71 verdicts, 0 apply failures."*

Measured candidates at 50fc231:
  70  *.patch files under variants/                                  (measured)
  72  artefacts (patch + py.txt)                                     (measured)
  73  files under variants/ (artefacts + MANIFEST.md)                (measured)
  73  distinct variant IDs named in the increment-6 re-run tables
      (MANIFEST lines 1785-1846), of which 3 — PL-Q4, PL-Q5, PL-Q6 —
      are explicitly PATCHLESS probes run against the clean tree
      (see line 507: "no patch; they are probes, not modules")
  70  = 73 minus those 3 patchless probes  ->  EXACTLY the patch count

So the increment-6 re-run tables do account for every one of the 70 patches, plus 3
patchless probes = 73 verdicts. The two *.py.txt probes (PL-W3, PL-W5) are verdicted
separately at lines 1632-1645, not in those tables.

**"71" is reachable by no counting rule I can construct.** The number is wrong; the WORK
behind it appears complete. This is a transcription defect in the denominator, not a gap in
coverage — but a wrong denominator in the exclusion set is precisely the thing a future
auditor uses to decide whether the set is complete.

The Engineer seat's "71 re-run, 71 verdicts" reproduces the MANIFEST's own wrong number.
The Project Lead's 70 + 2 = 72 artefacts / 73 files is CORRECT.

---

## OVERALL SAMPLE RESULT

Denominator: **22 of 70 patches (31%)** run end-to-end with their declared commands, plus
a `git apply --check` sweep over **70 of 70 (100%)**.

  applies cleanly ............................ 70 / 70   (100%, full sweep)
  declared command reaches the boundary
    the row names ............................ 22 / 22   (100%, sample)
  output names the RULE ID / exception the
    row claims (not merely non-zero exit) .... 22 / 22   (100%, sample)
  exact-text or exact-count MATCH ............ 18 / 22
  MATCH on substance, stale LINE NUMBER ......  4 / 22   (V12, V13, V15, V17)

**NO row in the sample was found claiming a route was covered when it was not.**
Every "REFUSED" row still refuses, by the named rule. Every "NOT REFUSED / ESCAPES" row
(V12, V13, V15, V17, V29a, V44) still escapes — the honest negative results are still
honest. The positive controls were not in this sample (V24, V28, V42 untested here).

The two defects the seat declared against itself — **F27 and F28 — both reproduce exactly**
and neither was overstated nor understated in the record.

## WHAT THIS AUDIT DID NOT ESTABLISH

* 48 of 70 patches were NOT run end-to-end here (apply-checked only). Absence of a
  mismatch in my 22 is not evidence of its absence in the other 48.
* The positive/false-positive controls (V24, V28, V42, V31, V45) were not re-run.
* No `.py.txt` probe (PL-W3, PL-W5) was executed.
* The V30 / R-series reader rows (exit 124 / exit 3 / recursion) were not re-measured;
  they involve deliberate non-termination and I did not spend the wall-clock on them.
* `CD-RT-003-GRANT-MATRIX-LIVE` needs a live PostgreSQL cluster; not attempted (and the
  MANIFEST declares the same at line 1853).
* I could not determine WHEN the banner.py patches were edited relative to their rows —
  only THAT the artefact and the record disagree today. Establishing the edit point needs
  git history over the variants directory, which is outside this work item's scope.

---

## INTEGRITY OF THE READ-ONLY TREE

`find /srv/crash-detector-wo2r-audit -type f -newermt '2026-08-19T21:00:00'` -> EMPTY.
Nothing in the audit tree was written, executed in, or modified. All execution took place
in per-run mktemp directories under /tmp/w7 extracted from /tmp/cd-asr-wo2r/target.tar,
each deleted after use.

Clarification on the executable check in §1: `find /srv/crash-detector-wo2r-audit -type f
-perm -u+x` over the WHOLE audit tree returns two files — `pbg/tools/hooks/pre-commit` and
`pbg/tools/hooks/install.sh` — both under the pinned framework, neither under variants/.
Scoped to `variants/` the result is EMPTY, as reported. PBG-ASSURE-001 (nothing in the
variant corpus is committed executable) HOLDS.
