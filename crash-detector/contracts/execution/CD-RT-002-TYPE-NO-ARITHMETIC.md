# Execution contract — CD-RT-002-TYPE-NO-ARITHMETIC

**CD-AC-002** · The two dials are never blended · obligation **MANDATORY** · scope **CLASS** ·
delivered in **WO-2**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

The two score types reject every arithmetic operator, share no numeric base, and DialSet exposes no scalar.

## Command

```
PYTHONPATH=src python3 -m pytest tests/test_scores.py tests/test_dialset.py -q
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

`tests/test_scores.py` enumerates every arithmetic, bitwise, ordering and numeric-coercion dunder rather than naming the one somebody might add. `tests/test_dialset.py` enumerates DialSet's whole public surface against an allowlist, because the property under test is an ABSENCE and an absence cannot be tested by naming what should not be there.

## Why it is asserted this way

PID §3.1 is CONSTITUTIONAL. Blending the two dials into one number destroys the only thing the product is for, and a type that refuses `+` refuses it for every future author, not just this one.

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

An arithmetic dunder added to a score type (`__add__`, or any of the arithmetic, bitwise, ordering or numeric-coercion dunders the test enumerates), a numeric base introduced under both types, or a method added to DialSet that returns a scalar.

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
