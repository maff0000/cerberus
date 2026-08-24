# Execution contract — CD-RT-001-MISSING-DATA-NEVER-CALM

**CD-AC-001** · Missing or stale input never renders as calm · obligation **MANDATORY** ·
scope **CLASS** · delivered in **WO-3 increment 16B**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

**PID §3.2, constitutional, in its own words: *"Missing data must never render as calm."***
The LIVE PUBLICATION GATE — `refuse_unless_publishable`, the function
`src/crash_detector/publication/publish.py` calls on both surfaces before it writes anything —
REFUSES an envelope whose `UNKNOWN` or `DEGRADED` dial carries `detail_level: "calm"`, and
**still ADMITS** `elevated` and `acute` on those same branches and `calm` on a `VALUE` dial.

## Why this row exists at all — `PO-DECISIONS-0026` ruling 9

> "The calm-over-unknown refusal currently holds only in `tests/`, and `tests/` do not feed
> the gate — a register-wired instrument PASSES identically on a tree where the fix is fully
> reverted. That is 'the controls exist and nothing runs them' one hop sideways, and it is
> unacceptable for a CONSTITUTIONAL guarantee. 16B adds a REGISTER-WIRED negative control (one
> the gate actually reads) that FAILS if calm-over-unknown is ever admitted — the guarantee
> must be carried by a live instrument, not a memorial in tests."

MEASURED and reproduced by the Project Lead at `CD-DISPATCH-INC16B-ENGINEER` §2: on a tree
with all four `$ref`s restored to `#/$defs/detail_level`, **all fourteen register instruments
exit as they do on the clean tree**, and the only failures anywhere are nine tests in
`tests/test_detail_level.py`, a file no register `execute:` line named.

## Command

```
python3 tools/register/check_missing_data_never_calm.py --root .
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

**The RUNNING GATE, not the schema documents.** The check imports `crash_detector` from
`<root>/src`, drives `refuse_unless_publishable` with candidate envelopes, and records what
the gate actually did. It does not read the schemas as documents, does not search for the
string `absent_data_detail_level`, and does not assert that any `$ref` points anywhere.

Enumerated from the subject rather than typed in: the surfaces from `EnvelopeSurface`, the
dial slots from each contract's own properties that `$ref` `#/$defs/dial_reading`, and the
detail-level vocabulary from the contract's own `#/$defs/detail_level` enum. It prints the
resolved `crash_detector.__file__` and the SHA-256 of both contracts it judged, at every run.

## Why it is asserted this way

A structural read of schema keys is what let this class of defect through three times on this
project (`CD-PL-F169`, `CD-ASR-WO3-02` F06/F07, `CD-ASR-WO3-03`). A check that reads the
`$ref` TARGET NAME and never opens the target passes a tree where `calm` has been put back
inside the target's own enum; a check that asks *"is there a narrowing?"* rather than *"is
EVERY missing-data branch on EVERY surface narrowed?"* passes a tree where one branch on one
surface was reverted. **Both of those trees are contrast arms in `plants/WO3-INC16B/` and this
instrument exits non-zero on both.**

Register instruments on this project ARE permitted to import the application: four already do
(`check_exact_type_admission`, `check_engine_no_witness_reach`, `check_no_numeric_default`,
`check_judgement_path_doors`). `CD-RT-014`'s *"the probe must not import the application"*
binds `tools/probe/external_probe.py` and nothing else — an EXTERNAL probe must be external.

## *** THE ADMITTING ARMS ARE NOT DECORATION ***

The check asserts, in the same run and with equal weight, that the gate **still ADMITS**
`elevated` and `acute` on an `UNKNOWN` or `DEGRADED` dial and **`calm` on a `VALUE` dial**.

An instrument that only checked *"calm is refused"* is satisfied by a contract that refuses
everything, and — the case this project's history says gets missed — by a contract in which
**no dial can ever read `calm` at all**. `calm` on a real number backed by real inputs is the
entire reason `calm` exists (PID §4: *"calm = dial + one line"*). A guard that cannot tell
*"the forbidden thing is impossible"* from *"everything is impossible"* is not holding PID
§3.2, it is enforcing silence. Assertion `CD-CALM-VACUITY-000` checks the instrument's **own**
proposition table still contains the `VALUE`/`calm` admitting row, so the vacuity arm cannot be
quietly removed from the instrument that exists to carry it.

`CD-CALM-PAIRED-004` closes the other half: every refused candidate is diffed against the
ADMITTED candidate of the same state at the same slot on the same surface, and must differ at
**exactly one JSON pointer**, `/<slot>/detail_level`. Same document, one token moved, opposite
outcome — so the refusal is attributable to the level and to nothing else. `CD-CALM-REASON-003`
requires the refusal to be `SCHEMA_VIOLATION` located at the mutated slot, because *the right
outcome from the wrong layer* is this project's most-repeated defect (`CD-PL-F74`).

## Preconditions

* `python3` 3.11 or later.
* **`jsonschema` must be importable.** *This is a departure from the stdlib-only checks in
  this directory and it is stated rather than left to be discovered.* This check drives the
  live gate and the live gate validates with `jsonschema`; a behavioural check cannot be more
  stdlib-only than the behaviour it drives. If it is missing, the check exits `3` with the
  reason — never a pass and never a skip.
* `<root>/src/crash_detector/__init__.py` must exist. *"REFUSED"* is a runtime claim and the
  check will not make it against a tree it could not load.
* **`$CD_CONTRACTS_DIR` must be unset, or set to `<root>/contracts`.** The gate honours that
  variable, so it can be pointed at contracts that are not the subject's. The check resolves
  what the gate would load and exits `3` if it is not the subject's own — it will not report
  on a tree it is not looking at.
* The subject tree extracted by the auditor, with the working directory set to its root.
  `--root .` is not a default and is not optional.

## Exit semantics

| exit | meaning |
|---|---|
| `0` | CLEAN — assertions were made and all of them held. A run that made ZERO assertions refuses instead, so `0` can never mean "I looked at nothing". |
| `1` | VIOLATION — at least one finding, each printed with the cell (`surface/slot/state/level`) and the observed outcome. |
| `2` | USAGE — the command line was wrong. |
| `3` | PRECONDITION NOT MET — the check could not do its job, with the reason on stderr. |

Anything other than `0` is a failure. **The check never skips, for any reason**
(`PBG-CI-002`): a precondition it cannot meet is a non-zero exit with a stated reason,
never a pass.

## Declared limits — `CD-RULE-004`

Said the same way here, in the header of `tools/register/check_missing_data_never_calm.py`,
and in the comment above the entry in `required-tests.yaml`. **A register entry may not claim
more than its guard delivers.**

1. **IT JUDGES THE CONTRACT THE GATE ACTUALLY LOADS, WHICH IS CONFIGURABLE.**
   `$CD_CONTRACTS_DIR` can point the live gate at a widened copy while the repository's
   contracts are byte-intact. **This is a real, executable route and it is arm `C5` of
   `plants/WO3-INC16B/MANIFEST.md`, where the gate is MEASURED admitting a calm `UNKNOWN` dial
   with both repository schemas untouched.** The check refuses (exit `3`) when it is pointed
   that way, and prints the resolved contract paths and their SHA-256 at every run
   (`CD-PL-F98`). **IT DOES NOT PREVENT THE ROUTE.** A deployment that sets the variable to a
   widened copy is refused by nothing in this repository: **NOT PROVED TO BE CARRIED ANYWHERE.**
2. **IT PROVES NOTHING ABOUT A `VALUE` READING THAT SHOULD NOT HAVE BEEN A `VALUE`.** A dial
   whose inputs were missing but which was constructed as `VALUE` with a fabricated `score`
   renders `calm` legitimately as far as this contract is concerned, and this check ADMITS it —
   the `VALUE`/`calm` row says so out loud. **THE CARRIERS ARE THE SIBLING ENTRIES:**
   `CD-RT-001-AST-NO-NUMERIC-DEFAULT` (the provenance of the magnitude) and
   `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` (the runtime post-condition
   `refuse_a_number_without_its_inputs`). **This check is ONE OF THREE guards on `CD-AC-001`
   and never a sole guard.**
3. **IT SAYS NOTHING ABOUT STALENESS.** `CD-AC-001`'s words are *"missing OR STALE"*. This
   instrument drives the ABSENCE half only. Nothing in it reads `staleness_window_seconds`,
   the age of `as_of_utc`, or any liveness/relevance quantity. The stale half is `CD-AC-009`
   (`CD-RT-009-REGIME-AWARE-STALENESS`) and, as a product model, `PO-DECISIONS-0026` ruling 5,
   which is a LATER increment and is not evidenced here.
4. **IT IS NOT A CENSUS OF RENDERING PATHS.** It drives every surface `EnvelopeSurface`
   declares at every dial slot the contracts declare, so a third surface or a third dial is
   driven on the day it is added. But a path that does not go through
   `refuse_unless_publishable` is outside it. MEASURED at this commit: the only callers in
   `src/` are `publication/publish.py:276-277`, on both surfaces, before any write. A future
   serving layer that renders a dial without publishing an envelope is **NOT PROVED TO BE
   CARRIED ANYWHERE** — the rendering layer is later WO work.
5. **IT IMPORTS THE SUBJECT TREE AND THEREFORE INHERITS IT.** It is a runtime check because
   *"refused"* is a runtime claim and every escape on this project's record passed a static
   checker. The cost is `--root`'s honesty, which is why the resolved package path and both
   contract digests are printed on every run.
6. **IT NEEDS `jsonschema`.** See Preconditions. It cannot run where the application's own
   runtime dependencies are absent, and it exits `3` rather than passing when they are.

## Negative control

An envelope carrying `detail_level: "calm"` on a dial in the `UNKNOWN` or `DEGRADED` state
ADMITTED by `refuse_unless_publishable` on either surface — by ANY route. The class includes,
and is not limited to: either `$ref` on either contract's `dial_reading_degraded` or
`dial_reading_unknown` branch restored to `#/$defs/detail_level` (**including only ONE branch
on ONE surface**); `"calm"` added back into the `#/$defs/absent_data_detail_level` enum so the
`$ref` target keeps its name and loses its meaning; the branch `detail_level` requirement
dropped so the parent `dial_reading`'s full-vocabulary property is what applies; or any
change to `refuse_unless_publishable` that stops the closed schema being applied.

**AND — with equal weight — the VACUOUS DIRECTION IS ALSO A VIOLATION OF THIS ROW:**
`#/$defs/dial_reading_value.detail_level` narrowed so that **no** dial can ever read `calm`,
or any change that makes `elevated` or `acute` stop being admitted on a missing-data branch.
A tree on which nothing can be published is not a tree on which PID §3.2 holds, and this row
does not report it as one.

Detection is a **contrast**, and the validator computes it as one: the same declared command
must exit `0` on the clean subject and non-zero on the subject with the violation planted.
A clean arm that fails cannot be told apart from a broken harness, and a broken harness
detects nothing — the validator returns `UNDECIDABLE`, never `PASS`.

The negative control for this test is declared as run record **`RTR-WO3-0001`**.
That record does not exist yet. It is the run the **independent Assurance
seat** will produce — a distinct actor from the one that wrote this test. Until it exists
the validator computes `UNDECIDABLE` for this test and the gate stays shut, which is
correct: this seat may declare which run must evidence its guard, and may not supply it.

## What this contract does not claim

It does not claim the test passes. It does not claim the criterion is satisfied. It does not
admit any evidence: `latest_admitted_run` is null in the register and this seat cannot fill
it in, because an implementation may not certify itself (`PBG-SOD-001`, non-waivable).
