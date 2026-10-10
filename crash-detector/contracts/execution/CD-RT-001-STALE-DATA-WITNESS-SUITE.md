# Execution contract — CD-RT-001-STALE-DATA-WITNESS-SUITE

**CD-AC-001** · Missing or stale input never renders as calm · obligation **MANDATORY** ·
scope **CLASS** · delivered in **WO-3 increment 16E**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

`tests/test_envelope_freshness.py` is the acceptance evidence of `PO-DECISIONS-0029` ruling 1 —
the fourth refusal stage: `published_utc` minus a calm-bearing node's oldest stamp, against the
declared window, **computed purely from the document and with no external clock.** It asserts
the stage's correctness (26 test functions parametrised to 92), its exactness (the hand-rolled
civil-date arithmetic), its FAIL-CLOSED branches, its NO-CLOCK guarantee
(`BP-AMENDMENT-0001` §D.3), the mirror between the module's stamp pattern and the contracts'
own, and — with equal weight — that a genuinely fresh calm dial is still ADMITTED.

## Why this row exists at all

**THE WITNESS EXISTED, IT BIT, AND NO REGISTER ROW NAMED IT.** MEASURED three times
independently (`A312-F1`; `PROJECT_LEAD_SEAT_06`; `CD-ENG-WO3-13`): on the tree with the entire
fourth refusal stage removed, **all thirty of the register's `execute:` lines produced a
per-line rc list `diff`-IDENTICAL to the clean tip**, while `pytest tests/test_envelope_
freshness.py` on that same tree reported **14 failed, 78 passed**. `grep -c
'test_envelope_freshness' required-tests.yaml` returned **`0`**, against **41 distinct
`tests/test_*.py` paths the register DOES name.** *The project's own established mechanism for
making a test-file guarantee live was available, and for this guarantee it was not used.*

**THIS ROW IS THE SECONDARY WITNESS AND IT IS NOT OFFERED AS THE GUARD.** The live
register-wired instrument `PO-DECISIONS-0030` ruling 1 ordered is the SIBLING row
`CD-RT-001-STALE-DATA-NEVER-CALM`, which drives `refuse_unless_publishable` itself. **A pytest
file is still a file the gate happens to name** — that sentence is `required-tests.yaml`'s own
memorial about `tests/test_detail_level.py` at line ~242, it is the record of this exact defect
class, and it must not be removed. Do not read this row as the discharge of ruling 1.

## Command

```
PYTHONPATH=src python3 -m pytest tests/test_envelope_freshness.py -q
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

`tests/test_envelope_freshness.py` and, through it,
`src/crash_detector/publication/envelope_contract.py`'s fourth refusal stage — reached through
`refuse_unless_publishable` wherever the closed contracts make that possible, and driven
directly at `_refuse_stale_calm` where they do not, which each such test states in its own
docstring.

## Why it is asserted this way

A schema can REQUIRE a stamp but it cannot COMPARE one. Nothing in this product had ever
computed an age before increment 16D, and the assertions that a comparison is EXACT — the
civil-date arithmetic, the microsecond boundary, the leap-year rules, the closed interval, the
future stamp failing closed — are arithmetic propositions that belong in a test module and not
in a gate instrument.

## Preconditions

* `pytest` and `jsonschema` must be importable, and `<root>/src` must hold the package.
* **Zero skipped, zero xfailed, zero deselected, zero errored.** A test that can skip is not
  evidence (`pbg/roles/engineer.md`). MEASURED at the clean tip: `92 passed`, and
  `grep -iE 'skipped|xfailed|xpassed|deselected|error'` over the output returns nothing.

## Exit semantics

| exit | meaning |
|---|---|
| `0` | every test in the named module passed against a real subject. |
| `1` | at least one assertion about the freshness stage failed. |
| non-zero for any other reason | collection failed, the module is absent, or a dependency is missing. **That is never a pass.** |

## Negative control

**The same class as the sibling row's** — a stale calm reading admitted, the comparison
weakened, or the arithmetic made inexact — **and every named member is a MEASURED ARM, run from
its own pristine `git archive` extraction with `git apply`'s rc taken and checked** (see
`plants/WO3-INC16E/MANIFEST.md`):

| member | arm | measured |
|---|---|---|
| the fourth refusal stage removed from `refuse_unless_publishable` | `D1` | **14 failed, 78 passed**, exit `1` |
| the naive `age > window` — the negative-age branch removed | `D2` | **2 failed, 90 passed**, exit `1` |
| the stage reading the dial slots BY NAME instead of walking nodes | `D3` | **40 failed, 52 passed**, exit `1` |
| the NEWEST stamp governing instead of the oldest | `D4` | **2 failed, 90 passed**, exit `1` |
| clean control, no patch | `CTRL` | **92 passed**, exit `0` |

**DECLARED LIMIT — `CD-RT-001-STALE-DATA-WITNESS-SUITE`'s own sequence, which is 1 to 2.**

1. **IT IS A pytest FILE AND THEREFORE NAME-COUPLED TO ITS OWN PATH.** Deleting or renaming
   `tests/test_envelope_freshness.py` makes this row non-zero, which is the correct direction;
   but a test file the register names is only as live as the register line that names it, and
   this row is what makes it live at all. **The LIVE guard is the sibling row.**
2. **ONE OF ITS ASSERTIONS GUARDS THE INSTANCE AND NOT THE CLASS, AND IT IS NAMED RATHER THAN
   LEFT TO BE FOUND.** `test_A311_F1_arm_H_is_REFUSED_even_on_a_contract_widened_to_admit_it`
   drives a FIXED module-level constant, `ARM_H_DOCUMENT_FRAGMENT = [{"source_id": "SRC-A",
   "detail_level": DETAIL_CALM}]`. It proves that ONE fragment is refused; **it does not
   quantify over what the widened subschema admits**, and `CD-ASR-WO3-12` (`A312-F2`) built a
   fragment the same widened schema admits — `[{"source_id": "2026-08-24T18:00:00Z",
   "detail_level": "calm"}]` — which is **ADMITTED on both surfaces**, because stamps are
   detected BY VALUE and a node with NO real stamp and ONE decoy proves itself fresh against the
   decoy. **THAT IS NOT A LIVE ESCAPE ON THE SHIPPED CONTRACT** — `degraded_inputs` is
   `#/$defs/source_id_list`, an array of plain strings, so no `calm` can appear there at all —
   and both contract JSONs are byte-unchanged. **RECORDING IT IS IN SCOPE HERE; FIXING IT IS
   NOT:** requiring a calm-bearing node's stamp to be a DECLARED stamp narrows what the product
   admits, which is PRODUCT SCOPE (`PBG-AUTH-005`), and it is with the Product Authority as
   `Q36`. This limit is also the sibling row's `DECLARED LIMIT 3` in miniature: an assertion is
   only as general as the alphabet it quantifies over.

Detection is a **contrast**, and the validator computes it as one: the same declared command
must exit `0` on the clean subject and non-zero on the subject with the violation planted.
A clean arm that fails cannot be told apart from a broken harness, and a broken harness
detects nothing — the validator returns `UNDECIDABLE`, never `PASS`.

The negative control for this test is declared as run record **`RTR-WO3-0001`**. That record
does not exist yet. It is the run the **independent Assurance seat** will produce — a distinct
actor from the one that wrote this test. Until it exists the validator computes `UNDECIDABLE`
for this test and the gate stays shut.

## What this contract does not claim

It does not claim the test passes. It does not claim the criterion is satisfied. It does not
admit any evidence: `latest_admitted_run` is null in the register and this seat cannot fill
it in, because an implementation may not certify itself (`PBG-SOD-001`, non-waivable).
