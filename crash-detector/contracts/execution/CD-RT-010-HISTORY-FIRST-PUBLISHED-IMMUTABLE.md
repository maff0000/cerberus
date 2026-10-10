# Execution contract — CD-RT-010-HISTORY-FIRST-PUBLISHED-IMMUTABLE

**CD-AC-010** · History is honest · obligation **MANDATORY** · scope **CLASS** ·
delivered in **WO-4**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

`first_published_utc` is set on insert and cannot be moved, and no backfilled point is presented as a live track record.

## Command

```
python3 tools/register/check_first_published_immutable.py --root .
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

The history tables and the provenance surface. The column, the immutability and the absence of UPDATE and DELETE grants are STRUCTURAL from WO-2 (BLUEPRINT §4) and were proved against a live catalogue in WO-2 increment 3; the criterion's own evidence is sequenced at WO-4.

## Why it is asserted this way

This is one of the four properties carried as CD-OB-004 — proved live, with no standing guard. The obligation is recorded rather than quietly satisfied by citing the WO-2 run, because a property with evidence and no guard is a property that stops being true the moment somebody edits a migration.

## Preconditions

* **NONE THAT CAN BE MET AT THIS BASELINE.** The subject named by the
  command does not exist in the tree yet. Running the command here terminates non-zero
  because there is nothing to collect — which is the register saying, in the only way a
  command line can, that this criterion is NOT YET EVIDENCED.

## Exit semantics

| exit | meaning |
|---|---|
| non-zero, at this baseline | the subject does not exist yet. **This is NOT a FAIL of the criterion** and must not be recorded as one. It is the absence of evidence, and the validator computes `NOT_EVALUATED` or `UNDECIDABLE` accordingly. |
| `0`, once the owing work order has delivered | every test in the named module passed against a real subject. |
| `1`, once the owing work order has delivered | the criterion's proposition is violated. |

Nothing about this row may be read as a claim about the product today. The register
declares an obligation; it does not report a result, and it has no field in which one
could be written.

## Negative control

A route by which `first_published_utc` can move, or a backfilled point served as live — an UPDATE grant appearing on a history table, the trigger or constraint removed, or the publication path writing a backfill without marking it. To be planted in WO-4. This is also one of the four properties carried as CD-OB-004, proved live in WO-2 increment 3 with no standing guard: the guard is owed, and this row is where it will attach.

Detection is a **contrast**, and the validator computes it as one: the same declared command
must exit `0` on the clean subject and non-zero on the subject with the violation planted.
A clean arm that fails cannot be told apart from a broken harness, and a broken harness
detects nothing — the validator returns `UNDECIDABLE`, never `PASS`.

The negative control for this test is declared as run record **`RTR-WO4-0001`**.
That record does not exist yet and will be produced by the work order
that owes this criterion. The validator therefore computes `UNDECIDABLE` here, and that is
the honest answer at this baseline rather than a defect to be dressed up.

## What this contract does not claim

It does not claim the test passes. It does not claim the criterion is satisfied. It does not
admit any evidence: `latest_admitted_run` is null in the register and this seat cannot fill
it in, because an implementation may not certify itself (`PBG-SOD-001`, non-waivable).
