# The five planted violations — MANIFEST

**Deliverable B3 of `governance/dispatch/CD-DISPATCH-WO2-ENGINEER.yaml`.**
Written by `CD-ENG-WO2-01`. Nothing in this directory is evidence, and nothing in it is
assurance.

> **WO-2R INCREMENT 1 — what `CD-ENG-WO2R-01` changed here, and why.** Closing CD-ASR-F02 and
> CD-ASR-F03 changed the structure of `src/crash_detector/dials/reading.py` and
> `src/crash_detector/engine/evaluate.py`, so **two plants stopped applying** and were
> regenerated against the new structure, violating the same propositions by the same routes:
> `CD-AC-001/CD-RT-001-ABSENCE-RENDERS-UNKNOWN.patch` and
> `CD-AC-003/CD-RT-003-ENGINE-NO-WITNESS-REACH.patch`. A **third** row —
> `CD-AC-001/CD-RT-001-AST-NO-NUMERIC-DEFAULT` — still applies unchanged but its failure
> signature grew from two violations to three. All eleven patches apply cleanly at the WO-2R
> increment-1 SHA. **No plant was deleted and none was weakened** (CD-D-033). Every row that
> changed says so in its own text, and one changed collateral observation is disclosed as a
> finding against this seat's own work (CD-ENG-WO2R-F01, in the
> `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` row).
>
> **WO-2R INCREMENT 2 — what `CD-ENG-WO2R-01` changed here, and why.** Closing CD-ASR-F01
> changed `src/crash_detector/dials/scores.py`: a dial magnitude is no longer a bare `float`
> but a per-dial `DialMagnitude` carrying its provenance as data. **One plant stopped
> applying** and was regenerated against the new structure, violating the SAME proposition by
> the SAME route: `CD-AC-002/CD-RT-002-TYPE-NO-ARITHMETIC.patch`. Its declared command also
> grew by one module (`tests/test_dial_provenance.py`) and its failure signature grew from
> `6 failed, 90 passed` to `6 failed, 197 passed` — the same six named failures. The other
> ten patches apply cleanly and contrast unchanged at the WO-2R increment-2 SHA. **No plant
> was deleted and none was weakened** (CD-D-033). CD-AC-002's three-test independence was
> re-measured under all three of its plants and is intact; the measurement is recorded in the
> `CD-RT-002-TYPE-NO-ARITHMETIC` row. **`CD-RT-003-GRANT-MATRIX-LIVE` applies cleanly but its
> CONTRAST was NOT re-run at this increment**: it needs a live PostgreSQL and increment 2
> touched nothing it reads, so the throwaway-container authorisation (RT-A) does not extend
> to it here. That is disclosed rather than implied.
>
> It is a set of *negative controls* an INDEPENDENT seat applies and runs for
itself (`PBG-SOD-001`, non-waivable — this seat may not certify its own work).

---

## What is here

One directory per PID §6 criterion delivered in WO-2, and inside it **one `git apply`-able
patch per required test** from `required-tests.yaml`. Eleven tests, eleven patches.

```
plants/
  MANIFEST.md                 <- this file: test_id, patch, proposition, failure signature
  CD-AC-001/                  missing or stale input never renders as calm      (2 plants)
  CD-AC-002/                  the two dials are never blended                   (3 plants)
  CD-AC-003/                  witnesses are side-by-side, never ingredients     (2 plants)
  CD-AC-005/                  WITNESS UNAVAILABLE is not WITNESS AGREES         (1 plant)
  CD-AC-012/                  no execution pathway exists                       (3 plants)
```

## What is deliberately NOT here

**There is no wrapper script, no make target, no pytest harness and no runner of any kind,
and there may not be one** (`PBG-ASSURE-001`). An auditor who verifies a planted violation
through a script the project wrote has verified the script. The patches and this manifest
are the deliverable; APPLYING them and running the arms is the Assurance seat's work, done
with its own hands, on a tree it extracted itself.

That is also why every row below carries the **literal command lines**. They are not
described, they are written out, so that reproducing a result requires no interpretation of
anything this seat says.

---

## How an auditor uses this — the exact procedure

Do this once per plant. Never in the Engineer's worktree; never in a `git worktree`.

```bash
# 1. Extract a THROWAWAY COPY of the subject tree, yourself, from the object database.
SUBJECT=$(mktemp -d /tmp/cd-plant-XXXXXX)
git -C <this repository> archive <the SHA under audit> | tar -x -C "$SUBJECT"

# 2. Establish the CLEAN ARM first. The declared command must exit 0 (or, for the two
#    pytest arms, report all tests passed) on the unmodified tree. A plant that fails a
#    check which was already failing evidences nothing.
cd "$SUBJECT" && <the declared command for this test>   # expect: clean

# 3. Apply the plant.
git apply --stat --check "<repo>/plants/<CRITERION>/<TEST_ID>.patch"   # verify it applies
git apply             "<repo>/plants/<CRITERION>/<TEST_ID>.patch"

#    The patches are plain unified diffs against the delivered tree. `$SUBJECT` need not be
#    a git repository for `git apply` to work; it reads the diff, not the index.

# 4. Run the SAME declared command again. It must now fail with the signature below.
cd "$SUBJECT" && <the declared command for this test>   # expect: the signature in this file
echo "exit=$?"

# 5. Destroy the copy.
rm -rf "$SUBJECT"
```

`<the declared command for this test>` is quoted verbatim in each row below and is the same
string as `criteria[].tests[].execute` in `required-tests.yaml`. Where the two ever differ,
`required-tests.yaml` is the register and this file is wrong.

## Reading a result

* **Register checks** (`tools/register/check_*.py`) exit `0` clean, `1` violation, `2`
  usage, `3` precondition not met. A plant must produce **`1`**. A `3` means the check could
  not reach its subject — that is not a demonstrated violation and must not be recorded as
  one.
* **pytest arms** must go from all-passed to at least one FAILED. The named tests are given
  in each row; a plant that fails *different* tests than those named is a finding worth
  raising, not a pass.

---

## The single constraint these plants were built to

**Each plant violates the PROPOSITION, not the string the checker greps for.** Where a
guard's own documentation names the escape a plant author actually uses — a blend spelled
over three statements, a witness import reached transitively through a relative import, a
broker host with no execution word in its name — the plant takes THAT route rather than the
obvious one, so that a guard which caught only the literal instance would pass and be
caught doing it.

Each row therefore states the proposition first and the mechanism second. If a future edit
makes a guard catch the patch but stop catching the class, the patch is no longer doing its
job and should be rewritten rather than kept green.

## On collateral

Several plants fail more than the test they are filed under, because the criteria are
defended at more than one layer on purpose. Every collateral failure this seat OBSERVED is
disclosed in its row. Collateral is disclosed rather than trimmed away: a plant edited until
it fails exactly one instrument would be a plant shaped to the instruments rather than to
the product.

---
---

# CD-AC-001 — Missing or stale input never renders as calm

> PID §6 plant: kill a feed, and the affected dial shows UNKNOWN or DEGRADED within the
> assurance latency budget, NEVER a calm reading. PID doctrine §3.2 is constitutional.
>
> The criterion has two halves and both are required: **absence must have a name in the
> type system**, and **no route may exist by which absence becomes a number**. Two tests,
> and the two plants below demonstrate that neither test is redundant — each plant is
> caught by its own arm and *not* by the other.

| | |
|---|---|
| **test_id** | `CD-RT-001-AST-NO-NUMERIC-DEFAULT` |
| **patch** | `plants/CD-AC-001/CD-RT-001-AST-NO-NUMERIC-DEFAULT.patch` |
| **command** | `python3 tools/register/check_no_numeric_default.py --root .` |

**Proposition violated.** *No route exists on the dial path by which absence becomes a
number.* The patch opens two of them at once, and they are two of the five distinct ROUTES
the check enumerates rather than two spellings of one:

* **class A** — `DialSpec.last_known_magnitude: Union[float, None]`. A nullable number on
  the dial path is a type whose absence case is a value slot; every consumer must remember
  to branch, and the one that forgets renders absence as a number. The dial path uses a sum
  type precisely so that absence has a *constructor* and no value field.
* **class C** — `spec.last_known_magnitude or 0.0` inside `_evaluate_dial`.

**Why this is the proposition and not a token.** The semantics are the exact failure PID
§3.2 forbids: a required input that did not answer no longer forces `Unknown`. It produces
`Degraded` carrying **the previous magnitude, or zero** — a stale dial that reads calm. The
patch tells the plausible story that gets this written in real life ("a feed that drops for
one cycle should not blank the surface"), which is why it is worth catching by class: the
author is not being clever, they are being helpful.

**Expected failure signature.** Exit **1**, `FAIL — 3 violation(s)`:

```
VIOLATION  src/crash_detector/engine/config.py:84
    rule: A: nullable-number annotation
    what: `last_known_magnitude` is annotated as a number that may be None (float | None). ...
VIOLATION  src/crash_detector/engine/evaluate.py:<line>
    rule: C: `or <number>`
    what: `spec.last_known_magnitude or 0.0` substitutes a number when the left side is falsey. ...
VIOLATION  src/crash_detector/engine/evaluate.py:<line>
    rule: F: unrecognised magnitude provenance
    what: `Degraded(value=DIAL_SCORE_TYPES[spec.dial_id](score=carried, contributions=()), ...)`
          constructs a reading that CARRIES A VALUE ... but `carried` is bound in this scope to
          something that is not a declared magnitude source: the magnitude comes from
          `spec.last_known_magnitude or 0.0` ...
```

**UPDATED IN WO-2R (`CD-ENG-WO2R-01`).** The patch itself is unchanged and still applies. What
changed is the signature: it was `FAIL — 2 violation(s)` at the WO-2 gate, and it is now
**three**, because `check_no_numeric_default.py` gained **RULE F** closing CD-ASR-F03. The
third violation is the one worth reading — it does not depend on the `or 0.0` idiom at all. It
fires because a `Degraded` is constructed carrying a magnitude whose provenance is not the
declared contribution model, so the SAME plant written without `or` (say, with a plain
`spec.last_known_magnitude`) would still be caught. Rules A and C catch the spelling; rule F
catches the class. Line numbers moved with the module and are given as `<line>` rather than
transcribed, because a transcribed line number is a maintenance trap; the rule names are the
signature.

Two notes about class A on the ADJACENT path (`observations.py:99`,
`witness_resolver.py:168`) are printed on the clean arm as well and are **not** violations.
They must appear in both arms; if they appear only under the plant, something else changed.

**Collateral observed by this seat** (`PYTHONPATH=src python3 -m pytest tests/test_reading.py
tests/test_evaluate.py -q` → 9 failed, 40 passed at the WO-2 gate). The behaviour changed as
well as the shape, so the sibling arm fails too. Disclosed, not trimmed: the two arms are meant
to overlap here. **WO-2R re-measurement is owed to the auditor, not asserted here**: the
sibling suite gained 40 tests in WO-2R, so the failure count will differ from 9 and the seat
that re-runs it should record what it observes rather than expect this number.

---

| | |
|---|---|
| **test_id** | `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` |
| **patch** | `plants/CD-AC-001/CD-RT-001-ABSENCE-RENDERS-UNKNOWN.patch` |
| **command** | `PYTHONPATH=src python3 -m pytest tests/test_reading.py tests/test_evaluate.py -q` |

**Proposition violated.** *With an empty source registry both dials read `Unknown`; absence
never renders as a value.* The patch makes `evaluate()` return
`Value(EquityCrashScore(score=0.0))` for a dial that declares no required inputs — the WO-2
shipped state, in which **no ingredient source is registered at all**.

**Why this is the proposition and not a token.** This is the failure the whole product
exists to prevent, in its most likely real form. Nobody plants it maliciously; somebody
writes it because a surface has nothing to render and "0 until the sources land" reads like
a placeholder rather than a claim. It is a claim. The dial says *calm* on a day when the
detector has no data whatsoever, and `evaluate`'s own docstring already refuses it in
words: "Zero satisfied requirements is not 'all requirements satisfied'."

**REWRITTEN IN WO-2R (`CD-ENG-WO2R-01`), same proposition, same route, new context.** The
WO-2 patch no longer applied: `_evaluate_dial` gained the CD-ASR-F03 post-condition decorator
and a longer docstring, so the hunk context moved. The patch was regenerated against the WO-2R
structure and makes the identical semantic change — a dial declaring no required inputs returns
`Value(EquityCrashScore(score=0.0), inputs_used=("baseline",))`. Nothing about what it violates
has changed. *A plant that no longer applies is not a plant* (CD-D-033), and deleting one is
prohibited.

**Expected failure signature.** pytest exits **1**. At the WO-2 gate this was `3 failed, 46
passed` with `AttributeError: 'Value' object has no attribute 'since_utc'`. In WO-2R it is
**`17 failed, 72 passed`**, and the reason is worth reading rather than the count:

```
crash_detector.dials.reading.AbsenceYieldedAValue: dial 'monetary_debasement' produced Value,
which carries a value, but its required inputs were not all present: it declares [], NO
contribution model is declared, and the usable inputs are []. A reading that carries a value is
a claim that its inputs were present; a dial that did not get them must be Unknown, whatever the
number is and wherever it came from (PID §3.2, CD-AC-001, CD-ASR-F03).
```

The post-condition raises inside `evaluate()`, so every test in the file that evaluates
anything now fails rather than only the three that inspected the reading. That is a stronger
contrast and a worse-looking number; both are honest. The signature to check is the exception
type, not the count.

**Collateral, RE-MEASURED IN WO-2R, and it CHANGED — disclosed as a finding against this
seat's own work (CD-ENG-WO2R-F01).** At the WO-2 gate
`python3 tools/register/check_no_numeric_default.py --root .` stayed at exit **0** under this
plant, and the manifest reasoned from that: the two CD-AC-001 tests were "not two spellings of
one instrument", because only the behavioural arm saw this violation. **That is no longer
true.** Rule F now catches this plant too (exit **1**, `FAIL — 1 violation(s)`, `F:
unrecognised magnitude provenance` — `score=0.0` is a literal, and a literal is not a declared
magnitude source). The plant is still a valid negative control for its own arm, but it no
longer *demonstrates* the independence of the two arms.

The route that still separates them is **boundary 1 of `CD-RT-001-AST-NO-NUMERIC-DEFAULT`'s
declared limit** — a constructor obtained dynamically, which rule F cannot see as a
construction and which the runtime post-condition refuses anyway. It is written out as variant
**`V03`** in `variants/WO-2R/CD-ASR-F02-F03/`, with its command and its observed refusal, so
the property this row used to evidence is evidenced somewhere it can be executed.

---
---

# CD-AC-002 — The two dials are never blended

> PID §3.1 is CONSTITUTIONAL: "Two dials, never blended. Equity crash and
> monetary/debasement fail in opposite directions; averaging cancels the signal."
>
> Enforced at **three independent layers**, because one layer is a preference and three are
> a structure: the TYPES refuse arithmetic, an AST scan refuses the expression, and the
> closed envelope schema refuses the document. A blend that slips past any one layer must
> still fail the other two — so there is one plant per layer, and each was checked against
> the other two arms.

| | |
|---|---|
| **test_id** | `CD-RT-002-TYPE-NO-ARITHMETIC` |
| **patch** | `plants/CD-AC-002/CD-RT-002-TYPE-NO-ARITHMETIC.patch` |
| **command** | `PYTHONPATH=src python3 -m pytest tests/test_scores.py tests/test_dialset.py tests/test_dial_provenance.py -q` |

> **REGENERATED AT WO-2R INCREMENT 2 by `CD-ENG-WO2R-01`, and the command GREW by one
> module.** Closing CD-ASR-F01 changed `src/crash_detector/dials/scores.py` — `score` is no
> longer a bare `float` but a per-dial `DialMagnitude` — so the previous patch stopped
> applying. It was regenerated to violate **the same proposition by the same route**: an
> arithmetic dunder on a score type that actually blends the two dials. **Nothing was
> deleted and nothing was weakened** (CD-D-033). The declared command grew by
> `tests/test_dial_provenance.py` because the register entry now names a publication-boundary
> layer and may not claim a layer it declares no test for.

**Proposition violated.** *A scalar derived from BOTH dial types is unrepresentable — the
score types and the dial magnitude type reject every arithmetic operator and share no
numeric base.* The patch gives `EquityCrashScore` an `__add__` (with `__radd__ = __add__` so
`sum()` works from its zero start) and a `__truediv__`, told as "so a rolling window can be
averaged".

**Why this is the proposition and not a token.** The added `__add__` reads the other
operand's magnitude through **whatever dial that magnitude says it came from** —
`other.score.quantity_for(sorted(other.score.provenance)[0])` — so it does not merely
*exist*: **it actually blends the two dials, and it does so while walking around the
provenance check rather than through it.** This seat ran it on a pristine extraction:

```
>>> e = EquityCrashScore(score=DialMagnitude(dial_id=EQUITY_DIAL_ID, quantity=0.9), contributions=())
>>> m = MonetaryDebasementScore(score=DialMagnitude(dial_id=MONETARY_DIAL_ID, quantity=0.1), contributions=())
>>> ((e + m) / 2.0).score
DialMagnitude(dial_id='equity_crash', quantity=0.5)
```

An equity dial at 0.9 and a monetary dial at 0.1 become one number reading 0.5, **wearing
equity's provenance**, so it would pass the publication gate as an equity reading — the
signal cancelled and the provenance falsified, exactly as PID §3.1 says it will be. Note
also that the author only ever wrote methods on the *equity* type and never mentioned the
monetary one; the blend arrives without either type naming the other, which is why the test
asserts the absence of the whole `ARITHMETIC_DUNDERS` family rather than watching for
`equity + monetary` to raise.

**Expected failure signature.** pytest exits **1**, `6 failed, 197 passed`:

```
FAILED tests/test_scores.py::test_neither_score_type_defines_any_arithmetic_or_coercion_dunder
FAILED tests/test_scores.py::test_no_ancestor_of_either_score_type_defines_one_either
FAILED tests/test_scores.py::test_every_binary_operator_between_the_two_dials_is_a_type_error[add]
FAILED tests/test_scores.py::test_no_score_can_be_combined_with_a_bare_number_either[add]
FAILED tests/test_scores.py::test_no_score_can_be_combined_with_a_bare_number_either[truediv]
FAILED tests/test_scores.py::test_a_score_cannot_be_summed_which_is_how_a_blend_usually_arrives
```

**Sibling arms under this plant, observed by this seat on the regenerated patch:**
`check_no_blend.py` exit **0** (3128 assertions), `check_schema_closed.py` exit **0**. The
type layer is still the only one that sees it — nothing in the source yet writes the blend,
and nothing publishes it, so a project relying on the AST scan alone would have shipped a
blendable dial type.

**THREE-TEST INDEPENDENCE, RE-MEASURED AT WO-2R INCREMENT 2 AND STILL INTACT.** CD-AC-002
has three declared tests and this plant fires exactly one of them. Both CD-AC-001 arms also
stay clean under it (`check_no_numeric_default.py` exit 0 at 302 assertions;
`pytest tests/test_reading.py tests/test_evaluate.py` 90 passed), so strengthening the type
layer did NOT make two declared tests fire on the same plant — the hazard the previous
increment raised against its own work. Each of CD-AC-002's three plants still fires its own
arm and only its own arm.

---

| | |
|---|---|
| **test_id** | `CD-RT-002-AST-NO-BLEND` |
| **patch** | `plants/CD-AC-002/CD-RT-002-AST-NO-BLEND.patch` |
| **command** | `python3 tools/register/check_no_blend.py --root .` |

**Proposition violated.** *No single expression consumes both dial types outside the
allowlisted container and serving layer, and no expression anywhere combines them
arithmetically.* The patch adds a new module `src/crash_detector/publication/headline.py`
whose `headline_figure(dials)` returns the mean of the two dial magnitudes — the "one number
for the banner" that PID §3.1 exists to forbid.

**Why this is the proposition and not a token.** It is written in the spelling
`check_no_blend.py`'s own docstring names as the ESCAPE, not the one it names as the
obvious plant:

```python
    first = dials.equity.value.score
    second = dials.monetary.value.score
    return (first + second) / 2.0
```

By the time the addition happens, **no dial marker is left in the expression**. The local
names are `first` and `second` — deliberately neutral, carrying no `equity`, `monetary` or
`debasement` token — so the check can only catch this through intra-procedural flavour
propagation. A guard that inspected single expressions, or that pattern-matched on dial
names, reports the tree clean while the blend sits in it. It also reaches for the two
`.score` floats and so never asks the type system anything, which is why the type layer
does not see it either.

**Expected failure signature.** Exit **1**, `FAIL — 2 violation(s)`, both at
`src/crash_detector/publication/headline.py:23`:

```
    rule: RULE 1: arithmetic across the two dials
    what: `first + second` combines an equity-flavoured value with a monetary-flavoured value. ...
    rule: RULE 2: one expression consumes both dials
    what: `(first + second) / 2.0` consumes BOTH dial types in a single expression, ...
```

Both rules must fire. RULE 1 alone would mean the propagation worked; RULE 2 alone would
mean it did not and only the co-occurrence sweep caught the return value.

**Sibling arms under this plant, observed by this seat:** the type arm passes (96 passed),
`check_schema_closed.py` exit **0**, and so do `check_no_execution_interface.py` and
`check_no_numeric_default.py`. This plant is seen by exactly one instrument.

---

| | |
|---|---|
| **test_id** | `CD-RT-002-SCHEMA-CLOSED` |
| **patch** | `plants/CD-AC-002/CD-RT-002-SCHEMA-CLOSED.patch` |
| **command** | `python3 tools/register/check_schema_closed.py --root .` |

**Proposition violated.** *The public envelope schema is closed and its properties are an
allowlist; there is no place in it for a third, combined number.* The patch adds a
`combined_stress` property of `"type": "number"` to the public envelope contract, and adds
it to `required` — i.e. the contract change is made *properly*, the way an engineer who
believed in it would make it, not left half-written.

**Why this is the proposition and not a token.** The plant does not open the schema
(`additionalProperties` stays `false` at every level) and does not touch
`patternProperties` or `unevaluatedProperties`. It concedes the point the honest way: a
declared, required, documented top-level number that is neither dial. That is what makes it
a fair test — the guard has to hold the ALLOWLIST as an exact set rather than merely hunt
for escape hatches, and it has to notice that the document now carries a second scalar
number whatever the key is called.

**Expected failure signature.** Exit **1**, `FAIL — 3 violation(s)` in
`contracts/public_envelope.schema.json` — three *independent* propositions, not one finding
reported three times:

```
    rule: 3: the root properties are not the declared allowlist
    what: ... UNDECLARED KEYS PRESENT: combined_stress. ...
    rule: 4: required does not match the allowlist
    what: required=[... 'combined_stress' ...] but the allowlist is [...]. ...
    rule: 5: a third top-level number
    what: ... scalar-numeric root properties ['combined_stress', 'staleness_window_seconds']; ...
```

Proposition 5 is the one that matters most: it holds even if a future edit widened the
allowlist in proposition 3, because a blended headline has to be a number somewhere and
that rule counts the numbers whatever they are called.

**Collateral observed by this seat.** `PYTHONPATH=src python3 -m pytest
tests/test_envelope_contracts.py tests/test_publication_refusal.py -q` → 17 failed, 237
passed, including
`test_the_same_blend_is_refused_by_every_construction_route[dict_round_trip]` and
`[json_reparse]`. Those are the WO-2 boundary tests for CD-AC-006, and they see the same
change from the other side. The type arm and the AST arm both stay clean.

---
---

# CD-AC-003 — Witnesses are side-by-side, never ingredients

> PID §6: the score computed with witnesses unreachable is BYTE-IDENTICAL. PID doctrine
> §3.4: "a witness that is also an ingredient cannot corroborate anything."
>
> Held in **two independent places**, and the two are different KINDS of fact: the code
> graph, and the database catalogue. A GRANT that was written and a GRANT that is held are
> not the same thing, and where they disagree the catalogue wins. One plant each.

| | |
|---|---|
| **test_id** | `CD-RT-003-ENGINE-NO-WITNESS-REACH` |
| **patch** | `plants/CD-AC-003/CD-RT-003-ENGINE-NO-WITNESS-REACH.patch` |
| **command** | `python3 tools/register/check_engine_no_witness_reach.py --root .` |

**Proposition violated.** *Nothing reachable from `src/crash_detector/engine/` reaches
witness code.* The patch adds `src/crash_detector/corroboration.py` — a small shared helper
sitting beside `observations.py` — which relatively-imports `.witness.panel`, and has
`evaluate()` consult it: a dial whose panel says the independent view has diverged now
returns `Unknown(WITNESSES_DIVERGED)` instead of its computed reading.

**Why this is the proposition and not a token.** This is PID §3.4 broken in substance, not
in form. The witness stops being a witness and becomes an input: the dial's value now
depends on it, so when the two agree the agreement is circular and corroborates nothing.
And the story is the seductive one — "surely we should not publish a number the independent
sources contradict" — which is exactly why the separation is structural rather than left to
judgement.

**It takes three routes a grep would not find, all at once:**

* **transitive.** The reach is two hops: engine → `crash_detector.corroboration` → witness.
  `grep -rn '^\s*\(from\|import\).*witness' src/crash_detector/engine/` returns **nothing**
  with the plant applied. This seat ran that grep. A one-level check reports clean.
* **relative.** The helper writes `from .witness.panel import ...`, never the dotted
  absolute path, so a search for `crash_detector.witness` finds nothing either.
* **placement.** The import in `evaluate.py` is FUNCTION-LOCAL. That is not cosmetic —
  see the collateral note below, where it defeats a runtime test.

**Expected failure signature.** Exit **1**, `FAIL — 1 violation(s)`, and the route trail is
the part to read:

```
VIOLATION  src/crash_detector/witness/panel.py
    rule: engine reaches witness code
    what: witness module `crash_detector.witness.panel` is REACHABLE from the engine package.
          Route (nearest first): crash_detector.witness.panel <- crash_detector.corroboration
          <- crash_detector.engine.evaluate. ...
```

A trail of length 2 is the pass condition for this plant. A trail showing a direct
`engine → witness` edge would mean the plant had been simplified into the instance the
check's own docstring says a grep would find.

**REGENERATED IN WO-2R (`CD-ENG-WO2R-01`), same proposition, same three routes, new context.**
The WO-2 patch no longer applied: it patches `evaluate.py`'s import block and `_evaluate_dial`'s
signature, both of which moved when the CD-ASR-F03 post-condition landed. The patch was
regenerated and makes the identical semantic change — a new `src/crash_detector/corroboration.py`
relatively importing `.witness.panel`, consulted through a function-local import in
`evaluate.py`. The transitive, relative and function-local properties are all preserved and were
re-verified: the violation trail is still of length 2 and
`test_importing_the_engine_does_not_pull_in_the_witness_package` still PASSES under it.

**Collateral observed by this seat, and it is the most interesting result here.**
`PYTHONPATH=src python3 -m pytest tests/test_reading.py tests/test_evaluate.py -q` → **1
failed, 88 passed** in WO-2R (**1 failed, 48 passed** at the WO-2 gate; the suite grew), and the
one failure is
`test_evaluate_has_the_blueprint_signature` (the added parameter), *not* the witness test.
**`test_evaluate.py::test_importing_the_engine_does_not_pull_in_the_witness_package`
PASSES with this plant applied** — because the import is function-local, so importing the
engine genuinely does not pull the witness package into `sys.modules`. The runtime test is
not wrong; it is measuring a different thing. Only the static import-graph walk sees this
reach, which is the argument for CD-AC-003 having a structural guard at all.
`check_no_numeric_default.py`, `check_no_blend.py` and `check_no_execution_interface.py`
all stay at exit **0**.

---

| | |
|---|---|
| **test_id** | `CD-RT-003-GRANT-MATRIX-LIVE` |
| **patch** | `plants/CD-AC-003/CD-RT-003-GRANT-MATRIX-LIVE.patch` |
| **command** | `python3 tools/register/check_grant_matrix_live.py --root .` |
| **also needs** | a reachable PostgreSQL, named in the environment: `CD_CHECK_STORE_HOST`, `CD_CHECK_STORE_PORT`, `CD_CHECK_STORE_NAME`, `CD_CHECK_STORE_USER`, `CD_CHECK_STORE_PASSWORD`. **By name only** — no value appears in this file, in the patch, or anywhere governed. |

**Proposition violated.** *`cd_engine` holds no privilege of any kind on schema `witness`.*
The patch adds one forward migration, `db/migrations/0008_engine_reads_witness_panel.sql`,
granting `USAGE ON SCHEMA witness` and `SELECT` on two witness tables to `cd_engine`. It is
written the way such a migration really arrives: modest, reasoned, SELECT-only, explicitly
leaving migration 7's append-only posture alone.

**Why this is the proposition and not a token — and why it is the plant this check was
built for.** The grant is added in a **later migration**, so:

* `db/grant_matrix.json` is left untouched and still says `cd_engine` reaches only
  `alert, dial, publication, raw`;
* `tests/test_grant_matrix_declaration.py` — which parses the migration *named*
  `grant_matrix`, i.e. 0007 — **still passes**. This seat ran it: green.

So the text comparison between the SQL and the declaration is blind to it by construction.
The store nevertheless holds the grant. That is precisely the gap this check exists to
close: "a GRANT that was written and a GRANT that is held are different facts, and where
they disagree the catalogue wins."

**Expected failure signature.** Exit **1**, `FAIL — 9 violation(s)` — **five** of them
CD-GM-001 along independent routes, so a check that only queried one table would still
fail, plus CD-GM-002 and both whole-matrix comparisons:

```
CD-GM-001 route=schema-privilege USAGE           has_schema_privilege('cd_engine','witness','USAGE') -> True
CD-GM-001 route=table-privilege SELECT ON witness.observation
CD-GM-001 route=table-privilege SELECT ON witness.reading
CD-GM-001 route=column-privilege                 information_schema.column_privileges -> [19 rows]
CD-GM-001 route=live refusal: cd_engine `SELECT 1 FROM witness.observation LIMIT 1`
          THE STATEMENT SUCCEEDED — cd_engine reached schema witness in a real session
CD-GM-001 route=live refusal: cd_engine `SELECT 1 FROM witness.reading LIMIT 1`
CD-GM-002 route=schema witness is cd_witness's alone
WHOLE-MATRIX route=schema USAGE, live vs db/grant_matrix.json
WHOLE-MATRIX route=table privileges, live vs db/grant_matrix.json
```

The two `live refusal` lines are the ones to weigh: they are not catalogue queries at all.
The check opens a session as `cd_engine` and asks PostgreSQL itself to refuse. Under the
plant, PostgreSQL does not refuse.

**Note the migration count in the header.** The clean arm reports `built from 7 subject-tree
migrations`; the plant arm reports `8`, and names `0008_engine_reads_witness_panel.sql` in
its applied list. If the plant arm still says 7, the patch did not apply.

**Verified by this seat under RT-A**, with the result recorded in the increment 6b Build Log
entry: clean arm `PASS — 138 assertions, 0 violations`; plant arm `FAIL — 9 violation(s)`,
against PostgreSQL 16.15 in one throwaway loopback-bound container, destroyed before the
seat returned. **That run is implementation evidence and is NOT assurance** — the Assurance
seat builds its own store and reads the catalogue itself (`PBG-SOD-001`, `PBG-ASSURE-001`).

**Collateral observed by this seat.** `tests/test_store_migrations.py::test_the_delivered_set_loads`
and `tests/test_store_schema_sql.py::test_the_migration_set_loads_and_is_not_empty` fail —
both assert the delivered migration set, which now has an eighth member.
`tests/test_grant_matrix_declaration.py` passes, as explained above, and
`check_no_execution_interface.py` stays at exit **0** over the added SQL.

**If the store is unreachable, the check exits 3, not 0.** With none of the five environment
variables set it prints `PRECONDITION_NOT_MET` and exits **3**. That is the correct answer
and it is *not* a demonstrated violation: an auditor who records exit 3 as "the plant
failed the check" has recorded nothing. Bring a store.

---
---

# CD-AC-005 — WITNESS UNAVAILABLE is not WITNESS AGREES

> PID §6: kill the witness feed, and the panel degrades to UNAVAILABLE, NEVER to agreement.
> BLUEPRINT §13 adds the harder half: **delete the panel row entirely and the result is the
> same**, and a row older than its staleness window is an absence too.
>
> "There must be no input whatever — missing, stale, malformed or defaulted — from which the
> serving layer produces AGREES."

| | |
|---|---|
| **test_id** | `CD-RT-005-PANEL-UNAVAILABLE-NEVER-AGREES` |
| **patch** | `plants/CD-AC-005/CD-RT-005-PANEL-UNAVAILABLE-NEVER-AGREES.patch` |
| **command** | `PYTHONPATH=src python3 -m pytest tests/test_witness_panel.py tests/test_witness_resolver.py -q` |

**Proposition violated.** *No absence resolves to agreement.* The patch attacks **both**
halves of the proposition, because the criterion names both and a plant that took only one
would leave the other unevidenced:

* **the explicit absence** — `row is None` now returns
  `Agrees(divergence_measure=NO_MEASURED_DIVERGENCE)`, on the reasoning that "cd-witness has
  raised nothing, so there is no disagreement on record";
* **the silent one** — the `PANEL_ROW_STALE` branch is **deleted**, so a row older than its
  window falls through to ordinary state handling and keeps saying whatever it last said.

**Why this is the proposition and not a token.** Neither edit is exotic and neither looks
wrong in review. The first is the "no news is good news" default, which is the single most
common way a monitoring surface learns to lie. The second is what happens the week the
staleness window is judged too tight and somebody removes the branch that keeps returning
UNAVAILABLE, rather than widening the window where it is configured. Both produce the same
outcome and it is the one PID §3.4 names: a panel that reads AGREES most confidently at the
exact moment the witness pipeline is broken, manufacturing corroboration out of silence.

Note what the patch does **not** do. It does not touch `WitnessPanel`, so `Unavailable` is
still a distinct constructor with no measurement on it, `UNAVAILABLE_REASONS` is unchanged,
`render_panel` still raises on a foreign member, and all of `tests/test_witness_panel.py`
passes. The type layer is intact and the product still lies — which is the argument for the
resolver being tested as behaviour and not inferred from the shape of its return type.

**Expected failure signature.** pytest exits **1**, `6 failed, 59 passed`, all in
`tests/test_witness_resolver.py`:

```
FAILED test_an_absent_panel_row_resolves_to_unavailable
FAILED test_a_stale_panel_row_resolves_to_unavailable
FAILED test_a_stale_row_that_said_agrees_does_not_keep_agreeing
FAILED test_freshness_is_judged_on_the_data_not_on_when_we_wrote_the_row
FAILED test_no_absent_stale_future_or_malformed_input_ever_resolves_to_agrees
FAILED test_the_absent_row_case_is_included_in_the_sweep_separately
```

with `_resolve(None)` returning `Agrees(divergence_measure=0.0, ...)`.

Three of those six are worth reading as a set:
`test_no_absent_stale_future_or_malformed_input_ever_resolves_to_agrees` is the sweep over
the whole class of bad inputs, `test_the_absent_row_case_is_included_in_the_sweep_separately`
is the guard that the sweep did not quietly drop the `None` case, and
`test_a_stale_row_that_said_agrees_does_not_keep_agreeing` is the half a plant author is
most likely to forget. If the sweep fails but the separate absent-row test passes, the
sweep is not covering what its name claims.

**Collateral observed by this seat: none.** All five source-scanning register checks stay at
exit **0** — `check_no_numeric_default.py` included, even though a `0.0` now reaches a panel
value on the serving path. This violation is visible to exactly one instrument, and CD-AC-005
has exactly one declared test.

---
---

# CD-AC-012 — No execution pathway exists

> PID §6: a test asserts the codebase contains no broker, order or execution interface —
> **advisory-only is STRUCTURAL, not policy**. That distinction is the whole criterion. A
> policy saying "we do not trade" is a sentence somebody can change in an afternoon; a
> codebase with no order interface in it, no broker SDK in its lockfile and no container
> that may reach a broker is a different kind of promise.
>
> Three independent tests, because the pathway can be opened **in source**, **in a
> dependency**, or **in the network posture**, and closing two of the three closes nothing.
> Each plant below opens exactly one of them, and each was run against the other two.

**Read this before judging the first plant.** `CD-RT-012-NO-EXECUTION-INTERFACE` carries a
**DECLARED LIMIT**, written out in the header of
`tools/register/check_no_execution_interface.py`, in its `required-tests.yaml` entry and in
its execution contract (CD-D-014, bounded by CD-D-015). It states in six numbered boundaries
what the check does **not** catch — deliberate euphemism among them. Per CD-D-014, a
CD-AC-012 variant an auditor plants that lands beyond that boundary is a finding **against
the declaration** — *was the limit honestly drawn?* — and not an automatic RED against the
guard. This seat did not plant beyond the boundary and does not claim the boundary is
narrow; it claims only that the boundary is written down.

| | |
|---|---|
| **test_id** | `CD-RT-012-NO-EXECUTION-INTERFACE` |
| **patch** | `plants/CD-AC-012/CD-RT-012-NO-EXECUTION-INTERFACE.patch` |
| **command** | `python3 tools/register/check_no_execution_interface.py --root .` |

**Proposition violated.** *The application source contains no order-entry path.* The patch
adds `src/crash_detector/backtest/paper_book.py` — a paper book "so a published reading can
be scored against what it implied", with the adapter left as a stub and a comment saying
nothing reaches a live venue in WO-2.

**Why this is the proposition and not a token.** The story is the one that actually opens
this door in an advisory product: nobody sets out to build an execution pathway, they build
a backtest harness, and the harness needs a shape for an intention. The shape is an order
ticket, and once the type and the entry point exist the remaining distance to a live venue
is the adapter nobody has written yet. PID §2's answer is that the shape itself is the
thing forbidden.

The patch deliberately contains **three different kinds of subject** so that no single layer
carries the result:

* `place_order(symbol, quantity, side, limit_price, venue)` — the named instance, which L1
  catches on `place` applied to `order`;
* `record(instrument, size, direction, destination)` — **the same order ticket under a name
  with no execution word in it**. L1 has nothing to say about `record`. It is caught by L2,
  which reads the field set and never reads the name at all;
* `class Ticket` — a frozen dataclass carrying the same five fields, caught by L2 as a
  *class* data model rather than as a callable signature.

**Expected failure signature.** Exit **1**, `FAIL — 6 violation(s)` in
`src/crash_detector/backtest/paper_book.py`, spread across all three layers:

```
:16  execution interface (signature shape)   class `Ticket` takes an ORDER TICKET: destination=`venue`,
                                             instrument=`symbol`, price=`limit_price`, quantity=`quantity`, side=`side`
:26  execution interface (signature shape)   function `place_order` takes an ORDER TICKET: (same five)
:26  execution interface (definition)        `place_order` applies the transmission verb `place`
                                             to the tradeable noun `order`
:31  execution interface (signature shape)   function `record` takes an ORDER TICKET: destination=`destination`,
                                             instrument=`instrument`, quantity=`size`, side=`direction`
:12  execution interface declared in prose   "place_order"
:27  execution interface declared in prose   "Write one intention into the paper book and hand it
                                             to the venue adapter" — trade-lifecycle act `book` with `venue`
```

**The line to check is `:31`.** If the run reports the `place_order` violations but not
`record`, the guard has caught the instance and lost the class: L2 is the layer that makes
renaming useless, and `record` is the only subject in the patch that tests it in isolation.

**Sibling arms under this plant, observed by this seat:** `check_lockfile_denylist.py` exit
**0** and `check_egress_no_broker.py` exit **0**. An order-entry path can exist in the source
of a project whose dependencies and network posture are both spotless.

---

| | |
|---|---|
| **test_id** | `CD-RT-012-LOCKFILE-DENYLIST` |
| **patch** | `plants/CD-AC-012/CD-RT-012-LOCKFILE-DENYLIST.patch` |
| **command** | `python3 tools/register/check_lockfile_denylist.py --root .` |

**Proposition violated.** *No broker, exchange or order-routing SDK appears in any
dependency manifest.* The patch adds `ib-insync==0.9.86` to `[project].dependencies` in
`pyproject.toml` and to `requirements.txt`, with the comment "Market data for the equity
dial's price inputs ... only the historical-bars call is used".

**Why this is the proposition and not a token.** `ib_insync` is a full Interactive Brokers
client. The comment is true and irrelevant: the distribution being present makes order entry
one `import` away and needs no further dependency review to become real, because the review
already happened and it said yes. That is the whole argument for scanning the manifest
rather than the code — the code that uses it does not have to exist yet.

**The name carries no execution word.** `ib-insync` tokenises to `{ib, insync}`; neither is
`broker`, `order`, `trade`, `execution`, `oms`, `ems`, `fix` or `exchange`. The token rule —
the rule that generalises to an SDK nobody has heard of — does **not** fire here. This plant
is caught only by the named denylist, which is why the check carries both rules and says in
its own output that the denylist is a **floor and not an oracle**.

**Why the plant is in `pyproject.toml` and `requirements.txt` and NOT in
`requirements.lock`.** A lockfile entry needs a `--hash=sha256:...` line, and this seat will
not write a digest it did not compute over bytes it fetched. Inventing one would be
recording a false observation in a governed artefact, which is worse than the narrower
plant. The two manifests it does touch are where a human adds a dependency; the lock is
generated from them. The lock ARM of this check is therefore **not exercised by this plant**,
and that is stated rather than left to be discovered.

**Expected failure signature.** Exit **1**, `FAIL — 2 violation(s)`:

```
VIOLATION  pyproject.toml:36      rule: broker SDK in a dependency manifest
    what: `ib-insync` is a known broker, exchange or order-routing SDK. ... Declared in [project].dependencies.
VIOLATION  requirements.txt:20    rule: broker SDK in a dependency manifest
    what: `ib-insync` is a known broker, exchange or order-routing SDK. ... Declared in requirements.txt.
```

Both must appear. One alone means only one manifest was read.

**Sibling arms under this plant, observed by this seat:** `check_no_execution_interface.py`
exit **0** and `check_egress_no_broker.py` exit **0**. Nothing in the source imports it yet —
which is exactly the state this check exists to refuse.

---

| | |
|---|---|
| **test_id** | `CD-RT-012-EGRESS-NO-BROKER` |
| **patch** | `plants/CD-AC-012/CD-RT-012-EGRESS-NO-BROKER.patch` |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |

**Proposition violated.** *No container's egress allowlist names a broker.* The patch puts
`api.ibkr.com` into `cd-collectors`' `x-egress.hosts`, commented "Market data for the equity
dial's price inputs. Read-only historical bars."

**Why this is the proposition and not a token.** The host chosen is the one the check's own
docstring names as *"the single most likely real-world instance"*: `ibkr.com` contains **no
execution concept word at all**. Tokenised, its labels are `{api, ibkr, com}` — not
`broker`, not `order`, not `trade`, not `exchange`. The concept-vocabulary rule does not fire
on it. Only the registrable-domain denylist does. A guard built from a word list alone
reports this tree clean while the collectors hold standing permission to talk to a brokerage.

And the intent behind the entry is genuinely innocent, which is the point: a broker really is
a market-data vendor, the request really would be read-only historical bars, and the
allowlist entry is nevertheless a route from this system to a venue that accepts
instructions. CD-EGRESS-002's own wording insists the question is *what kind of thing lives
there*, not what the request happens to be for today.

**Expected failure signature.** Exit **1**, `FAIL — 1 violation(s)`:

```
VIOLATION  deploy/compose.yaml:324
    rule: CD-EGRESS-002: an allowlist names a broker
    what: service `cd-collectors` may reach `api.ibkr.com`, and ibkr.com is a known broker,
          exchange or order-routing operator. It carries no concept word at all, which is
          precisely why a vocabulary rule alone would let it through. ...
```

The phrase *"It carries no concept word at all"* in the check's own output is the
confirmation that rule 2 fired and rule 1 did not — i.e. that the denylist did the work. A
run that reports the violation with a `carries the execution concept(s) ...` reason has
matched something else and the plant should be re-read.

**Not attacked by this plant, and named so the gap is visible:** the *other* half of
CD-EGRESS-002's proposition — any egress at all granted to `cd-engine`, `cd-public`,
`cd-private` or `cd-store`, the four services BLUEPRINT §13 gives none. That half is asserted
by CD-EGRESS-001 (policy `NONE`, empty `hosts`, and attachment only to `internal: true`
networks) and is exercised on the clean arm, not by a plant here. One test, one plant; an
auditor wanting the second half covered should say so as a finding about coverage rather
than read this row as claiming it.

**Collateral observed by this seat.**
`PYTHONPATH=src python3 -m pytest tests/test_deploy_container_set.py -q` →
`test_no_allowlist_anywhere_names_a_host` fails, 82 passed. That test is the WO-2 boundary
assertion that the allowlists are *empty*, which is a stronger and narrower claim than "name
no broker"; it sees the same change from the other side.
`check_no_execution_interface.py`, `check_lockfile_denylist.py` and
`check_base_image_digest_pin.py` all stay at exit **0**.
