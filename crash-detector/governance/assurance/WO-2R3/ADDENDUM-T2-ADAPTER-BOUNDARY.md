# ADDENDUM TO THE WO-2R3 ASSURANCE RECORD — T2, THE ADAPTER BOUNDARY (CD-BP-003)

**Provenance:** a measurement DELEGATED BY CD-ASR-WO2R3-01 under CD-DISPATCH-WO2R3-ASSURANCE, against
target `531c95c`, all work in throwaway `/tmp` extractions.

> ## READ THIS BEFORE THE EVIDENCE. IT DECIDES WHAT THIS DOCUMENT IS AND IS NOT.
>
> **THIS MEASUREMENT RETURNED *AFTER* THE ASSURANCE SEAT CLOSED ITS VERDICT.** The seat's own
> `VERDICT.md` §2 (T2) and §7.2 say, in terms: *"A deeper adapter attack was delegated and had not
> returned when I closed the verdict — stated as a measured limit, not a silent omission"*, and
> *"did not trace a hostile `payload` to a published envelope or a dial score. The Product Owner's
> 'spend your first hour here' is only partly discharged."* **THIS IS THAT MEASUREMENT, ARRIVING
> LATE.**
>
> **IT IS THEREFORE UNGRADED BY ANY COMPETENT PARTY AT THE MOMENT OF WRITING:**
> - **The Assurance seat has NOT graded it.** Its verdict was closed before this landed. Nothing in
>   `VERDICT.md` takes account of anything below, and `VERDICT.md` IS NOT EDITED to pretend otherwise
>   (`PBG-CONT-003` — corrections supersede, never edit).
> - **The Project Lead has NOT graded it and MAY NOT.** `PBG-AUTH-006`: the Project Lead writes
>   neither the fix nor the assurance. The Project Lead banked this document to stop the evidence
>   dying in a conversation (`PBG-CONT-007`) and did nothing else to it. **NOT ONE WORD OF THE
>   EVIDENCE BELOW HAS BEEN EDITED, SHORTENED, RANKED OR REBUTTED.**
>
> **WHY IT IS BANKED SEPARATELY RATHER THAN FOLDED IN.** Folding late evidence into a closed verdict
> would make the record say the auditor weighed something it never saw. The verdict stands as
> written; this stands beside it; the Product Owner reads both and decides what follows.
>
> **AND ITS DIRECTION IS NOT NEUTRAL.** Every item below, if it survives grading, makes the gate
> HARDER and not easier. It cannot be read as a softening of the AMBER.

---

## What the measurement returned, verbatim

Everything below ran against `531c95c2` extracted to `/tmp`. Nothing outside `/tmp` was touched.
Baseline suite on the unmodified tree: **1538 passed**, so every reported failure is attributable.

### 1. What the door actually checks

**`missing_adapter_members`** (`src/crash_detector/collectors/adapter.py:185-207`) checks **names via
`hasattr`** for all five members, plus **`callable()`** for `fetch`/`is_empty` only. It checks no
signature and no type. Measured:

| candidate | result |
|---|---|
| `source_id=3, adapter_id=None, response_schema="not a mapping"` + two callables | `()` — **conformant** |
| `fetch = 7` | `('fetch',)` |
| `class Anything: def __getattr__(self, n): return lambda *a, **k: None` | `()` — **conformant** |
| `__getattr__` returning `7` | `('fetch', 'is_empty')` |

**RENAME TEST**: fails, as declared. It is worse than the declaration says in one direction — an
object with `__getattr__` conforms *for any member set whatsoever*, so the vocabulary is not even
five names, it is "answers to attribute access". **COUNTERFACTUAL ARM** on the callable clause: with
`_ADAPTER_CALLABLES` removed, `fetch = 7` reports `()`. The clause is doing real work.

There is **no structural check at all** for `sink`, `ledger` or `validator` — no
`missing_sink_members` exists (`attempt.__all__` and `validation.__all__` confirm).

### 2. ESCAPE 1 — the stored payload is not the validated payload (`runner.py:670 / 709 / 728`)

`_attempt` reads `response.payload` four times:

```
L670  validator.validate(response.payload, adapter.response_schema)   <- validated HERE
L699  isinstance(response.payload, AbcMapping)
L709  empty = adapter.is_empty(response.payload)     <- ADAPTER CODE RUNS, HOLDING THE PAYLOAD
L728  return OK(payload=response.payload, ...)       <- stored HERE
```

`is_empty` is the foreign object's own code and it is handed a live reference to the payload, between
validation and storage. Nothing re-validates. Two independent mechanisms, both with the **shipped
default `JsonSchemaValidator`** and the **strictest declarable schema** (`type: object`,
`additionalProperties: false`, `required`, `minimum/maximum`):

```
none     -> ('OK', {'reading': 0.25})                              # control
mutate   -> ('OK', {'reading': 99.0, 'extra': 'not in schema'})    # payload["k"]=... inside is_empty
rebind   -> ('OK', {'totally': 'different'})                       # object.__setattr__(response,'payload',...)
```

Full hostile run, reproduced on a pristine extraction:

```
outcome         : OK
STORED payload  : {'reading': inf, 'not_in_schema': '\x00\x00\x00', 'type': <module 'builtins'>}
row outcome     : OK {'reading': inf, ...}      # the append-only observation row carries it too
Does the STORED payload conform to the DECLARED schema?
   NO -> ValidationError: Additional properties are not allowed ('not_in_schema', 'type' were unexpected)
```

A **live Python module object** is in a governed `OK.payload` and in the recorded row.

**This refutes a written claim.** `required-tests.yaml:1200` and `collect`'s DECLARED LIMIT 1 both say
the hostile adapter is bounded by *"a payload that passes the declared schema"*, and
`required-tests.yaml:1201` says *"every value the four Protocols RETURN exact-typed at its point of
return"*. The **type** is established (`OK.payload` is exactly `dict`, `observations.py:73-92`). The
**value** is not the one that passed validation, and no test in the tree asserts that it is
(`grep is_empty tests/` covers only non-bool returns and exceptions).

**RENAME TEST**: not applicable — the escape names no identifier of this system.

**COUNTERFACTUAL ARM**: `_attempt` rebuilt with one structural change — snapshot `dict(response.payload)`
immediately after validation, hand `is_empty` a separate copy, store the snapshot. Both arms then
refuse:

```
WITHOUT the shared reference, mutate -> ('OK', {'reading': 0.25})
WITHOUT the shared reference, rebind -> ('OK', {'reading': 0.25})
```

So the structure being credited ("validation once, at the boundary") is demonstrably *not* doing the
work in the shipped code, and a two-line change makes it do it.

### 3. ESCAPE 2 — the four Protocol parameters are an in-process code-execution channel

`admission.py:186-189` and `establishment.py:222-225` both excuse the closure/rebinding reaches with
*"Every route requires the ability to execute code inside this package"*. `admission.py:181-184`
states of the rebinding route specifically: **"It is NOT a caller route: it needs the ability to
execute code inside the package."**

`collect` calls `adapter.fetch`, `adapter.response_schema`, `adapter.is_empty`, `sink.record`,
`ledger.admit_if_absent`, `validator.validate` — six re-entry points *interleaved with the runner's
own establishment sequence*. A caller who can pass an object therefore has exactly that ability.
Demonstrated from caller code only:

```
outcome                : OK
STORED payload         : {'reading': -999.0, 'leaked': 'never validated'}
recorded requested_utc : 1999-01-01T00:00:00+00:00
recorded observed_utc  : 1999-01-01T00:00:00+00:00
reading_key            : ('src.rebind', '1999-01-01T00:00:00Z')
```

The adapter's `fetch` rebound `runner.FetchedResponse` to a look-alike whose `payload` is a
**property** — defeating the `type(response) is not FetchedResponse` check at `runner.py:663`, which
the contract lists under *"WHAT IS CLOSED AT THAT DOOR AND IS NOT A LIMIT"* — and rebound `ensure_utc`
in `attempt`/`observations`, which is V34's move reached by a caller.

And with **zero imports of `crash_detector` inside the hostile object**, reaching the runner's own
globals through the calling frame:

```
   reached module: crash_detector.collectors.runner
   outcome: OK payload: {'anything': 'at all'}
```

> The delegated measurement ranked this second only to Escape 1: **the distinction the project relies
> on twice — "a caller supplies a value" vs "code executes inside the package" — does not exist at
> this door.**

### 4. Hostile sink, ledger, validator

| arm | result |
|---|---|
| sink returns a value | `SinkContractBreach: ObservationSink.record returned str; …` — **refused** |
| sink writes nothing, returns `None` | `rows_recorded=1` — **admitted**, as declared |
| ledger returns `"already claimed"` | `LedgerContractBreach: … returned str; exactly True or exactly False is the contract` — **refused** |
| ledger always `True` | admitted, as declared limit 3 |
| **sink mutates the outcome after `record`** | **ESCAPE 3, below** |
| validator returns `None`, validates nothing | genuinely malformed payload becomes `OK {'reading': 'not a number', 'junk': [1,2]}` |
| validator returns a repaired payload | `Malformed VALIDATOR_CONTRACT_BREACH` — **refused** |
| validator raises `SchemaDeclarationInvalid` | propagates; row written as `MALFORMED / SCHEMA_DECLARATION_INVALID` — a hostile validator makes the system **blame itself** for the source |
| `validator=object()` | `Malformed VALIDATOR_FAILED_AttributeError` — **our wiring defect recorded as the SOURCE misbehaving** |
| `sink=object()` / `ledger=object()` | bare `AttributeError`, not a named contract breach |

**ESCAPE 3 — a hostile sink makes the reading key claim a period no row records.** `_record` runs in
the `finally` at `runner.py:491`; `_reading_key(source_id, final_outcome)` runs afterwards at
`runner.py:517` **off the same object**. A sink that `object.__setattr__`s the outcome it was just
handed:

```
what the sink SAW at record time : ('OK', {'reading': 0.25}, 2026-08-22 11:59:59+00:00)
what collect RETURNED afterwards : {'reading': 999.0}  2000-01-01T00:00:00+00:00
reading_key                      : ('src.h', '2000-01-01T00:00:00Z')
```

The `UNIQUE (source_id, source_as_of_utc)` constraint that declared limit 3 names as the carrier is
asked about a key that corresponds to **no recorded observation**. Also: a sink that returns a value
inside the `finally` **replaces** a propagating `SchemaDeclarationInvalid` with `SinkContractBreach`,
silently losing the "our declared schema is unusable" signal.

**COUNTERFACTUAL ARM** on the ledger: restore `bool(ledger.admit_if_absent(key))` and the truthy-string
ledger is admitted (`reading_admitted=True`). The exact-`bool` check is doing the work, and
`class B(bool)` raises `TypeError: type 'bool' is not an acceptable base type` — it cannot be evaded.
**RENAME TEST**: the refusal is `type(verdict) is not bool`, naming no identifier of the supplied
object — it survives. Same for `verdict is not None` on the validator (counterfactual: discarding the
return re-opens the arm to `OK`).

### 5. ESCAPE 4 — the ESTABLISHED_HERE count, and the population that is not closed

**Counts.** `admission.py:75-76` says *"EIGHT parameters across FIVE callables"* and *"A ninth use
fails that test."* Measured at runtime and by the register check: **16 parameters across 9
callables.** The prose declaring the limit is stale by exactly the increment that added CD-BP-003's
four plus the collector doors' four. This is the project's own stated fear — *"exemptions that start
absorbing a population"* — with the declaration not having moved.

**A fourth field exemption (literal spelling), added to `AttemptRecord.adapter_id`:**
- `check_constructor_field_establishment.py` → prints `ESTABLISHED_HERE field exemptions: 4`, **PASS,
  exit 0** (as documented — it reports, it does not adjudicate)
- `test_the_established_here_field_exemptions_are_exactly_this_set` → **FAILED, exit 1**,
  `Extra items in the left set: (AttemptRecord, 'adapter_id')`

So the claim holds **for that shape**. It does not hold for these:

**(a) ALIAS.** `from crash_detector.establishment import ESTABLISHED_HERE as _EH` then `_EH("…")`, in
`collectors/validation.py` (a module the check definitely scans):
- static check → **still reports 16, exit 0** — the counting instrument **fails the rename test**
- pytest → caught

**(b) NESTED CLASS** — `class Outer: class Inner: @admits(anything=ESTABLISHED_HERE("…"))`, spelled
**literally**, in `collectors/validation.py`:
- static check → **still 16, exit 0**
- `test_the_established_here_exemptions_are_exactly_this_set` → **passes it over**

**(c) CONTAINER-HELD** — a door built by a factory and bound in a module-level `dict`, spelled
literally: **both instruments miss it.**

Two of three new exemptions are invisible to **both named carriers**, with no rename involved.
*"A fourth use is a test failure and not a quiet widening"* is false for a door on a nested class or
held in a container.

**And it is worse for undecorated doors.** In `collectors/runner.py` itself:

| where the public door is defined | `check_judgement_path_doors.py` |
|---|---|
| module-level `def` | **FAIL — 1 violation, exit 1** |
| method of a top-level class | **FAIL — 1 violation, exit 1** |
| method of a class nested one level (`Outer.Inner`) | **PASS — 0 violations, exit 0** |
| function-local `def` returned by a factory, bound in a module dict | **PASS — 0 violations, exit 0** |

That is V16's shape one nesting level down, in the CD-BP-003 module, against the instrument that
`admission.py:66-67` names as *"the acceptance test … which enumerates the judgement paths FROM THE
ARTEFACT and fails on any public entry point that is not decorated."*

### 6. Where a hostile payload actually gets — traced, not assumed

`OK.payload` → `evaluate.py:420` `payloads = {…}` → `mapping.py:_payloads_the_engine_released` →
`compute`. Driven end to end with a config whose equity dial requires the hostile source:

```
evaluate RAISED UnspecifiedMapping: model 'm.equity.v1' … declares MappingKind.UNSPECIFIED
payload reached _payloads_the_engine_released?
  [{'src.self': {'nan': nan, 'inf': inf, 'obj': <a live object in a governed payload>}}]
```

So: the hostile payload **reaches `engine/mapping.py` intact** — NaN, inf and a live object survive
`_payloads_the_engine_released`'s `dict(payload)` shallow copy — and stops there because `MappingKind`
has exactly one member and it raises. It reaches **no dial score, no published envelope, no witness
panel** (`grep '\.payload'` finds no reference under `publication/`, `serving/`, `witness/`).

**The containment is the empty mapping enum, not any guard on payload.** The counterfactual is the
product roadmap: the first computing `MappingKind` member lands the payload in the arithmetic, and per
Escape 1 that payload is not bounded by the declared schema either. Note also the adapter fully
controls `source_as_of_utc` — year-2126 and stale-stamped-now both produce `OK` with matching reading
keys; the freshness carrier named in declared limit 2 protects against a dishonest *caller clock*, not
a dishonest *adapter*, since freshness is computed from the adapter's own number.

### 7. Refusals that do hold, with counterfactuals

- `own_str` on `source_id`/`adapter_id` (`runner.py:546-580`): a `str` subclass with lying
  `__eq__`/`__hash__` is rebuilt to exact `str`. Non-`str` → `AdapterContractBreach`. Solid.
- `type(response) is not FetchedResponse` (`runner.py:663`): a plain subclass → `Malformed
  ADAPTER_CONTRACT_BREACH`; a duck response → same. Holds **unless the module global is rebound**
  (Escape 2).
- `type(empty) is not bool` (`runner.py:717`): `"yes"` and `0` both → `Malformed
  ADAPTER_CONTRACT_BREACH`. Unsubclassable, so unevadable.
- Payload not a JSON object → `PAYLOAD_NOT_A_JSON_OBJECT`.
- Missing member → `AdapterContractBreach`, before any row is owed.

**One small defect found here**: `adapter_id` is read **twice** — once by `missing_adapter_members`'
`hasattr`, once by `_established_adapter_identity`'s `getattr`. With a property-backed adapter, the
value **established and stored is the second read** (`'a.READ2'`), not the one the conformance check
observed. The adapter's code runs inside the runner's own conformance check.

### 8. What the delegated measurement could NOT establish

- Whether the store-level carriers actually hold. `CD-RT-GRANT-MATRIX-LIVE` and
  `tests/test_store_schema_sql.py` are named as the carriers for the sink and ledger residues; they
  were not run against a live Postgres here, so declared limit 3's carrier is unverified by this
  measurement. Escape 3 is *in-process* and shows the key handed to that constraint can be false
  regardless.
- Whether the schema self-certification (adapter supplies both payload and the schema it is judged
  by) is intended. It is structurally circular — an empty `response_schema` admits anything, and
  NaN/inf/`10**400`/live objects land in a governed payload with no mutation trick at all — but no
  statement claiming otherwise was found, so it is recorded as an observation, not a refutation.
- `__closure__` rewriting from inside an adapter method (V33/V37's move) was not exhausted. Escape 2
  establishes the *precondition* is available to a caller; two consequences were demonstrated and the
  measurement stopped there. **"Assume there are more."**
