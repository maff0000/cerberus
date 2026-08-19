# The five planted violations — MANIFEST

**Deliverable B3 of `governance/dispatch/CD-DISPATCH-WO2-ENGINEER.yaml`.**
Written by `CD-ENG-WO2-01`. Nothing in this directory is evidence, and nothing in it is
assurance. It is a set of *negative controls* an INDEPENDENT seat applies and runs for
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

**Expected failure signature.** Exit **1**, `FAIL — 2 violation(s)`:

```
VIOLATION  src/crash_detector/engine/config.py:84
    rule: A: nullable-number annotation
    what: `last_known_magnitude` is annotated as a number that may be None (float | None). ...
VIOLATION  src/crash_detector/engine/evaluate.py:166
    rule: C: `or <number>`
    what: `spec.last_known_magnitude or 0.0` substitutes a number when the left side is falsey. ...
```

Two notes about class A on the ADJACENT path (`observations.py:99`,
`witness_resolver.py:168`) are printed on the clean arm as well and are **not** violations.
They must appear in both arms; if they appear only under the plant, something else changed.

**Collateral observed by this seat** (`PYTHONPATH=src python3 -m pytest tests/test_reading.py
tests/test_evaluate.py -q` → 9 failed, 40 passed). The behaviour changed as well as the
shape, so the sibling arm fails too. Disclosed, not trimmed: the two arms are meant to
overlap here.

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

**This plant is invisible to the sibling AST arm, and that is the point.** `score=0.0` is a
plain keyword argument carrying a numeric literal — it is none of the five routes
`check_no_numeric_default.py` bans, and that check stays at exit **0** with the plant
applied (observed by this seat). The two CD-AC-001 tests are therefore not two spellings of
one instrument: one reads the SHAPE of the dial path, the other reads what it DOES, and
this violation is only visible to the second.

**Expected failure signature.** pytest exits **1**, `3 failed, 46 passed`:

```
FAILED tests/test_evaluate.py::test_with_no_sources_declared_both_dials_read_unknown
FAILED tests/test_evaluate.py::test_the_empty_state_is_unknown_even_when_observations_happen_to_be_present
FAILED tests/test_evaluate.py::test_evaluate_does_not_consult_the_clock
```

with `AttributeError: 'Value' object has no attribute 'since_utc'` — the assertion reaching
for the reason on a reading that should have been `Unknown` and is now a number.

**Collateral observed by this seat.** `python3 tools/register/check_no_numeric_default.py
--root .` remains exit **0**. See above; that is a result, not a gap.

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
| **command** | `PYTHONPATH=src python3 -m pytest tests/test_scores.py tests/test_dialset.py -q` |

**Proposition violated.** *The two score types reject every arithmetic operator and share
no numeric base.* The patch gives `EquityCrashScore` an `__add__` (with `__radd__ = __add__`
so `sum()` works from its zero start) and a `__truediv__`, told as "so a rolling window can
be averaged".

**Why this is the proposition and not a token.** The added `__add__` is duck-typed on
`other.score`, so it does not merely *exist* — **it actually blends the two dials**. This
seat ran it:

```
>>> e = EquityCrashScore(score=0.8, contributions=())
>>> m = MonetaryDebasementScore(score=0.2, contributions=())
>>> e + m
EquityCrashScore(score=1.0, contributions=())
>>> (e + m) / 2
EquityCrashScore(score=0.5, contributions=())
```

An equity dial at 0.8 and a monetary dial at 0.2 become one number reading 0.5 — the signal
cancelled, exactly as PID §3.1 says it will be. Note also that the author only ever wrote
methods on the *equity* type and never mentioned the monetary one; the blend arrives
without either type naming the other, which is why the test asserts the absence of the
whole `ARITHMETIC_DUNDERS` family rather than watching for `equity + monetary` to raise.

**Expected failure signature.** pytest exits **1**, `6 failed, 90 passed`:

```
FAILED tests/test_scores.py::test_neither_score_type_defines_any_arithmetic_or_coercion_dunder
FAILED tests/test_scores.py::test_no_ancestor_of_either_score_type_defines_one_either
FAILED tests/test_scores.py::test_every_binary_operator_between_the_two_dials_is_a_type_error[add]
FAILED tests/test_scores.py::test_no_score_can_be_combined_with_a_bare_number_either[add]
FAILED tests/test_scores.py::test_no_score_can_be_combined_with_a_bare_number_either[truediv]
FAILED tests/test_scores.py::test_a_score_cannot_be_summed_which_is_how_a_blend_usually_arrives
```

**Sibling arms under this plant, observed by this seat:** `check_no_blend.py` exit **0**,
`check_schema_closed.py` exit **0**. The type layer is the only one that sees it — nothing
in the source yet writes the blend, and nothing publishes it, so a project relying on the
AST scan alone would have shipped a blendable dial type.

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

**Collateral observed by this seat, and it is the most interesting result here.**
`PYTHONPATH=src python3 -m pytest tests/test_reading.py tests/test_evaluate.py -q` → **1
failed, 48 passed**, and the one failure is
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
