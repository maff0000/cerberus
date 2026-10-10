# Execution contract — CD-RT-006-PUBLIC-SURFACE-NO-PRIVATE-DATA

**CD-AC-006** · The public surface carries zero private data · obligation **MANDATORY** · scope **CLASS** ·
delivered in **WO-5**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

Publication REFUSES on a private or book-derived key — it does not filter — and an automated scan of the published artefact finds no private field.

## Command

```
python3 tools/register/check_public_artefact_no_private_field.py --root .
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

The published artefact and the publication path. BLUEPRINT §13 records that the BOUNDARY is built in WO-2 — containers, networks, grants, the closed envelope schema and the refusal path in `tests/test_publication_refusal.py` — while CD-D-004 sequences this criterion's EVIDENCE at WO-5.

## Why it is asserted this way

Retrofitting a trust boundary is how trust boundaries end up leaky, which is why the boundary is early. The WO-2 boundary work is NOT offered here as a substitute for the WO-5 evidence: a boundary that exists and a boundary that has been attacked are different claims.

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

A private or book-derived key reaching the published artefact — by being added to the public schema, by publication filtering it out instead of refusing, or by a private field renamed to look public. To be planted in WO-5.

Detection is a **contrast**, and the validator computes it as one: the same declared command
must exit `0` on the clean subject and non-zero on the subject with the violation planted.
A clean arm that fails cannot be told apart from a broken harness, and a broken harness
detects nothing — the validator returns `UNDECIDABLE`, never `PASS`.

The negative control for this test is declared as run record **`RTR-WO5-0001`**.
That record does not exist yet and will be produced by the work order
that owes this criterion. The validator therefore computes `UNDECIDABLE` here, and that is
the honest answer at this baseline rather than a defect to be dressed up.

## What this contract does not claim

It does not claim the test passes. It does not claim the criterion is satisfied. It does not
admit any evidence: `latest_admitted_run` is null in the register and this seat cannot fill
it in, because an implementation may not certify itself (`PBG-SOD-001`, non-waivable).
