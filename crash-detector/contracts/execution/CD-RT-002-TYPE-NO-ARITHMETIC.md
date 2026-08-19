# Execution contract — CD-RT-002-TYPE-NO-ARITHMETIC

**CD-AC-002** · The two dials are never blended · obligation **MANDATORY** · scope **CLASS** ·
delivered in **WO-2**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

**A scalar derived from BOTH dial types is unrepresentable at runtime, and unpublishable.**

Widened at WO-2R, closing `CD-ASR-F01` (HIGH). It used to read "the two score types reject every
arithmetic operator, share no numeric base, and DialSet exposes no scalar". All three of those are
still asserted and none was relaxed; but they were not enough, because `.score` was a plain `float`
and the moment a caller held two floats the type system had left the conversation. A dial magnitude
is now a NOMINAL, PER-DIAL, NON-COERCIBLE value carrying its dial as data, cross-dial combination is
refused at the point of combination by comparing that data, and the publication boundary releases a
number into a dial slot only from a magnitude whose provenance is exactly that slot's dial.

## Command

```
PYTHONPATH=src python3 -m pytest tests/test_scores.py tests/test_dialset.py tests/test_dial_provenance.py -q
```

The command GREW by one module at WO-2R and lost nothing. `tests/test_dial_provenance.py` executes
escaped variants `E01` and `E02` in the auditor's own shape and asserts the publication-boundary
refusal; it is in the declared command because a register entry may not claim a layer it declares no
test for (`CD-RULE-004`).

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

`tests/test_scores.py` enumerates every arithmetic, bitwise, ordering and numeric-coercion dunder rather than naming the one somebody might add, and does so for the magnitude type as well as for the two score types. `tests/test_dialset.py` enumerates DialSet's whole public surface against an allowlist, because the property under test is an ABSENCE and an absence cannot be tested by naming what should not be there. `tests/test_dial_provenance.py` asserts the magnitude type's DECLARED attribute surface by set equality, attempts every binary operator, every ordering, every coercion and eight distinct aggregations (`sum`, `math.fsum`, `statistics.mean`, `statistics.median`, `functools.reduce`, `max`, `min`, `sorted`) against the two live magnitudes, attempts `json.dumps`, `copy.deepcopy` and `pickle` round trips, and executes `E01` and `E02` themselves.

**These are RUNTIME assertions and that is the point.** The Product Owner's word is "unrepresentable", which is a property of execution; a static checker exiting non-zero is not proof of one, because both blends that produced `CD-ASR-F01` passed every static checker in this repository.

## Why it is asserted this way

PID §3.1 is CONSTITUTIONAL. Blending the two dials into one number destroys the only thing the product is for, and a type that refuses `+` refuses it for every future author, not just this one — and refuses it however the two values were reached, which a check that reads expressions cannot do.

## Preconditions

* `python3` 3.11 or later with `pytest` available on the interpreter, and
  `jsonschema` for the modules that read the envelope contracts. Nothing else, and no
  install step.
* `PYTHONPATH=src` is part of the command line, not an environment the auditor is expected
  to have arranged. The package is importable from the source tree with no install.
* The working directory is the root of the subject tree the auditor extracted.

## Exit semantics

| exit | meaning |
|---|---|
| `0` | every test in the named modules passed. |
| `1` | at least one test failed — the failing assertion and its module are named in the output. |
| `2` · `3` · `4` | interrupted, internal error, or usage/collection error. None of these is a pass, and none may be read as one. |

No test in these modules may skip. A conditional skip is a hole with a comment in it, and
a suite that can skip its way to green is not evidence.

## Negative control

A scalar derived from BOTH dial types made representable or publishable, by ANY route. The class includes, and is not limited to: an arithmetic, bitwise, ordering or numeric-coercion dunder added to a score type or to the dial magnitude type, or inherited from an ancestor of either; a numeric base introduced under both types; a subclass of the magnitude type carrying a coercion; a member added to the magnitude type's declared attribute surface, by class body, decorator, class assignment or metaclass; a method added to DialSet that returns a scalar; a magnitude constructed without provenance, or with provenance that is not exactly one dial; a magnitude of one dial accepted into the other dial's score type or published into the other dial's envelope slot; a combinator that UNIONS provenance instead of comparing it; a same-dial helper that does not refuse when it is reused across dials; and a round trip through `copy`, `pickle` or JSON that strips provenance or yields a bare number.

### DECLARED LIMIT (CD-RULE-004)

Stated here, in the header of `src/crash_detector/dials/magnitude.py` (boundary A) and in the
register entry, in the same words.

**A number released through `quantity_for(<one dial id>)` is an ordinary `float`, and two of them
can be added by ordinary Python arithmetic.** MEASURED EXAMPLE, which an auditor can execute:

```python
blended = (equity.score.quantity_for(EQUITY_DIAL_ID)
           + monetary.score.quantity_for(MONETARY_DIAL_ID)) / 2.0     # -> 0.5, not refused
```

Nothing in the type system refuses that line and nothing can: they are two `float` objects. What is
refused is PUBLISHING it — `number_for_dial_slot` takes only a `DialMagnitude` whose provenance is
exactly the slot's dial, and the closed public envelope schema has no third key for the result. The
assertion is in `tests/test_dial_provenance.py::test_a_released_number_cannot_be_published_as_a_dial`,
which computes the blend, shows it equals 0.5, and shows it cannot be published as either dial.

Two further residues, stated rather than left to be found:

* `object.__setattr__(m, "provenance", ...)` rewrites a slot on any frozen object in Python. The
  direction is SAFE — a forged multi-dial provenance makes the magnitude LESS usable, not more, and
  every release path refuses it. Asserted by
  `test_a_forged_multi_dial_provenance_yields_no_number`.
* `repr(m)` contains the quantity, deliberately. Hiding a value from a developer's own debugger
  would be obfuscation, and obfuscation is not structure.

**Do not read a clean run of this arm as proof that no two numbers can ever be added in Python.**
Read it as proof that a dial magnitude cannot be combined with the other dial's magnitude, that
reducing one to a number requires naming its single dial, and that a number so obtained cannot be
published as anything but that dial.

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
