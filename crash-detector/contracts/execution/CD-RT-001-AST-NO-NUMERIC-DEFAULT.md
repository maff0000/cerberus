# Execution contract — CD-RT-001-AST-NO-NUMERIC-DEFAULT

**CD-AC-001** · Missing or stale input never renders as calm · obligation **MANDATORY** · scope **CLASS** ·
delivered in **WO-2**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

No route exists on the dial path by which an absent input becomes a number.

## Command

```
python3 tools/register/check_no_numeric_default.py --root .
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

The declared dial path under `src/crash_detector/`, read as an abstract syntax tree rather than as text. The check prints, on every clean run, the annotations it found OUTSIDE the dial path as notes — visible, not hidden, and not failed on, because the ban is a BLUEPRINT §7 property of the dial path and widening it to the whole tree would be a Blueprint change.

## Why it is asserted this way

A dial that reads `0.0` because a source did not answer is the exact failure PID §3.2 forbids. The type system carries the guarantee; this check exists because a type can be bypassed by an annotation, a `.get` default or an `except` that returns a literal.

**Those four routes were a list of spellings, and CD-ASR-F03 is the finding that says so.** An independent auditor put the numeric default in a module-level constant and returned `Value(value=<ScoreType>(score=QUIET_MAGNITUDE, ...))` from the missing-inputs branch; none of the four enumerated routes was present and the check exited 0. The check now carries **RULE F**, which inverts the question. Instead of enumerating the ways a number can arrive, it enumerates the **one way a dial magnitude is permitted to arrive** — from the declared contribution model applied to inputs that were present — and reports **every other provenance, including provenances nobody has thought of**. Rule F **denies by default**: an unrecognised shape is a violation, never a silence.

## DECLARED LIMIT — what this check does not catch, and which layer does

Required by `CD-RULE-004`, drawn in the pattern of `CD-RT-012-NO-EXECUTION-INTERFACE`. The same list appears in the header of `tools/register/check_no_numeric_default.py` (the longest of the three, carrying each measured example in full) and in the comment above this test's entry in `required-tests.yaml`. The three are kept consistent with each other.

**This check is a static read of source text at one commit, and CD-AC-001's proposition is a RUNTIME property.** Where a boundary below says *the runtime layer carries this*, that layer is the sealed and slotted `Reading` types in `src/crash_detector/dials/reading.py` together with the absence post-condition `refuse_a_number_without_its_inputs` in `src/crash_detector/engine/evaluate.py`, and it is evidenced by the sibling test **`CD-RT-001-ABSENCE-RENDERS-UNKNOWN`**, not by this one.

| # | boundary | example an auditor can execute | who carries it |
|---|---|---|---|
| 1 | A construction this check cannot see as a construction. Rule F recognises a value-bearing reading by the terminal name of its callee (`Value`, `Degraded`), resolved through the module's import aliases. | `maker = getattr(sys.modules["crash_detector.dials.reading"], "Value")` then `return maker(value=score, as_of_utc=now_utc, inputs_used=("carried",))` on the missing-inputs branch — **exit 0 here** | the runtime layer: the post-condition reads the returned object's TYPE and never the expression, so this raises `AbsenceYieldedAValue` when the branch executes |
| 2 | Tracing beyond one scope chain. A magnitude computed inside a helper is **reported** rather than followed. | `score = _blend(payloads)` → `F: unrecognised magnitude provenance` | this check, deny-by-default. A legitimate future helper must be declared in `DECLARED_MAGNITUDE_SOURCES`, deliberately and visibly |
| 3 | Anything outside the two declared tiers. | the same plant placed in `src/crash_detector/publication/summary.py` — **exit 0 here** | nothing, at WO-2. The declared set REFUSES if a declared path is missing, so it cannot be narrowed by deleting a module, but it does not grow on its own |
| 4 | Class A (nullable-number annotations) outside the dial path. | `observations.py:99` and `witness_resolver.py:168` are printed as NOTES on every clean run | BLUEPRINT §7/§13 scope the ban to the dial path; widening it is a Blueprint change, not this check's initiative (CD-ENG-F26) |
| 5 | A magnitude legitimately computed but WRONG. Rule F asks where a number came from, never whether it is right. | a contribution model returning `0.0` for a dial whose inputs were all present passes every rule here | nothing yet. `scores.py` deliberately imposes no range, because the scale of a dial is what the dial MEANS (CD-D-005, owed by the Product Owner) |
| 6 | Runtime, configuration and data. A zero arriving from a config file, an environment variable or a database row is not in the source text at all. | set a fallback magnitude in configuration rather than in source | the runtime layer: the post-condition never asks where the number came from, so a configured zero raises exactly as a literal zero does |
| 7 | **A consumer that ANSWERS an absence with a number.** Boundaries 1, 2, 3, 5 and 6 are every one of them about a value-bearing reading being CONSTRUCTED; **none reserved the CONSUMPTION route, and that enumeration was measured INCOMPLETE** (`CD-ASR-WO2R-F03`). `fold` guarantees a caller cannot FORGET `Unknown`; it never guaranteed a caller cannot ANSWER `Unknown` with a number. | `ASR2-001-A` verbatim in the adjacent tier: `def surface_scalar(reading): return fold(reading, on_value=lambda s: s.value, on_degraded=lambda s: s.value, on_unknown=lambda s: 0.0)` — **exit 0 here** (measured, 377 assertions at `50fc231` and 443 at WO-2R2 increment 1c) | **IN PART, and measured.** `src/crash_detector/serving/dial_presentation.py` carries the PRESENTATION half: `Shown` admits only a `DialMagnitude` of its own dial by exact type, so that `0.0` cannot be presented as a dial (`DialPresentationRefused`, measured on a pristine extraction with the variant present), and `present_dial` performs the elimination itself so no surface writes its own `on_unknown`. Evidenced by `CD-RT-001-ABSENCE-RENDERS-UNKNOWN`, whose declared command grew by `tests/test_dial_presentation.py`. **NOT CARRIED, and NOT PROVED TO BE CARRIED ANYWHERE:** a module that computes a number for an absence and renders it ITSELF without coming through the presentation type. The rendering LAYER is WO-3; there is nothing in WO-2 to refuse it, and `surface_scalar` still returns `0.0`. `fold` was deliberately not given a guard — banning a numeric return is a ban on a spelling, and would forbid a legitimate numeric answer ABOUT an absence such as a count of missing inputs. |

**Do not read a clean run of this check as proof that no route from absence to a number exists.** A variant landing beyond a boundary above is a finding against **this declaration** — *was the limit honestly drawn?* — rather than an automatic RED against the guard. The pair to weigh is this check together with `CD-RT-001-ABSENCE-RENDERS-UNKNOWN`.

## Preconditions

* `python3` 3.11 or later. **Stdlib only** — no install step, no network, no
  virtualenv. A check that needs a package installed is a check the auditor cannot run.
* The subject tree extracted by the auditor, with the working directory set to its root.
  `--root .` is not a default and is not optional: it is there so that the check is always
  pointed at a tree explicitly, and never at whatever directory it happens to sit in.

## Exit semantics

| exit | meaning |
|---|---|
| `0` | CLEAN — assertions were made and all of them held. A run that made ZERO assertions refuses instead, so `0` can never mean "I looked at nothing". |
| `1` | VIOLATION — at least one finding, each printed with its file, its line and why it is one. |
| `2` | USAGE — the command line was wrong. |
| `3` | PRECONDITION NOT MET — the check could not do its job, with the reason on stderr. |

Anything other than `0` is a failure. **The check never skips, for any reason**
(`PBG-CI-002`): a precondition it cannot meet is a non-zero exit with a stated reason,
never a pass.

## Negative control

A dial magnitude whose provenance is not the declared contribution model applied to inputs that were present. The class is **wider** than the four spellings this check enumerated at the WO-2 gate — a `float | None` or `Optional[float]` annotation, a `.get(key, <numeric literal>)`, an `or 0`, a bare `except` returning a number — because CD-ASR-F03 escaped all four with a module-level constant. Rule F reports any `Value` or `Degraded` construction on the scanned path whose magnitude traces to a literal, a module-level constant, a parameter, a configuration attribute, a lookup, a previous reading, an unrecognised helper call, or anything else it cannot name as declared. A plant therefore does not need to use a route the check anticipated, which is the point.

Subject to the DECLARED LIMIT above.

Detection is a **contrast**, and the validator computes it as one: the same declared command
must exit `0` on the clean subject and non-zero on the subject with the violation planted.
A clean arm that fails cannot be told apart from a broken harness, and a broken harness
detects nothing — the validator returns `UNDECIDABLE`, never `PASS`.

The negative control for this test is declared as run record **`RTR-WO2-0001`**.
That record does not exist yet. It is the run the **independent Assurance
seat** will produce — a distinct actor from the one that wrote this test. Until it exists
the validator computes `UNDECIDABLE` for this test and the gate stays shut, which is
correct: this seat may declare which run must evidence its guard, and may not supply it.

## What this contract does not claim

It does not claim the test passes. It does not claim the criterion is satisfied. It does not
admit any evidence: `latest_admitted_run` is null in the register and this seat cannot fill
it in, because an implementation may not certify itself (`PBG-SOD-001`, non-waivable).
