# Execution contract — CD-RT-002-AST-NO-BLEND

**CD-AC-002** · The two dials are never blended · obligation **MANDATORY** · scope **INSTANCE** ·
delivered in **WO-2**

> **THE SCOPE OF THIS TEST WAS CORRECTED FROM `CLASS` TO `INSTANCE` AT WO-2R**, closing
> `CD-ASR-F01` (HIGH). It is a **LOCATOR**, not the closure, and it carries a DECLARED LIMIT below.
> Claiming CLASS while enumerating what a static intra-procedural checker can see is the defect
> that produced the finding. The CLASS closure is claimed by `CD-RT-002-TYPE-NO-ARITHMETIC`, which
> delivers it at runtime.

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

No single expression **that this check can see** consumes both dial types outside the allowlisted
container and serving layer, and no expression anywhere in the application source reaches past the
declared magnitude release into the private slot where a dial magnitude holds its number.

That is deliberately narrower than "the two dials are never blended". The criterion is wider than
this check, and the difference is written out in the DECLARED LIMIT below.

## Command

```
python3 tools/register/check_no_blend.py --root .
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

Every Python module in the application tree, walked as an AST. The allowlist is declared in the check and printed on every run, so a reader can see exactly where blending is permitted and why. FOUR rules run: RULE 1 arithmetic across the two dials, with no allowlist; RULE 2 co-occurrence in one expression, with a six-path allowlist; RULE 3, added at WO-2R and carrying no allowlist beyond the module that declares the slot, which reports any expression naming `_DialMagnitude__quantity` by attribute or as a string handed to `getattr`, and any call of the pickle protocol that returns that slot as state (`__getstate__`, `__reduce__`, `__reduce_ex__`); and RULE 4, added closing `CD-PL-F54`, which **denies by default over a declared registry of admission sites** — no module on the scanned path may name `observed_for_dial`, `derived_within_one_dial` or `DeclaredQuantity`, by call, attribute, import, annotation, default or a string handed to `getattr`, unless it is one of the four modules listed in `DECLARED_ADMISSION_SITES` with the reason it is there. RULE 4 is the rule that answers `PL-Q9`, and it recognises nothing about a blend: it watches the one door a laundering module cannot avoid, so an unlisted module is a violation because it is not a place anybody declared that numbers enter. An IMPORT counts, unlike everywhere else in this check. The reflection half was added closing `CD-ENG-WO2R-F06`, a finding the implementing seat raised against its own increment-2 work. RULE 3 distinguishes a dunder name held as DATA from a dunder name REACHED, so `ARITHMETIC_DUNDERS` and `TOLERATED_INTERPRETER_MACHINERY` — both legitimate tables of dunder names — are untouched.

The check REFUSES (exit `3`) if `src/crash_detector/dials/magnitude.py` or `src/crash_detector/dials/provenance.py` is absent from the subject tree. Those two modules are the type-level and re-entry closures this check is only a locator over, and reporting a clean scan of a tree that has lost either would be the worst kind of pass. Without `provenance.py` RULE 4 would also have no vocabulary to deny by default over.

## Why it is asserted this way

It **locates** a blend in the source, with a file and a line, in the one place a reviewer can act on it cheaply, and it catches the three-statement spelling that no runtime layer would see until the branch executed.

It used to be described as the instrument that catches "somebody unwrapping both to floats first". **That description was refuted by execution** and is not repeated: two working blends did exactly that and this check exited 0 on both (`CD-ASR-F01`, escaped variants `E01` and `E02`). Unwrapping is now stopped at the type — what a caller unwraps to is a `DialMagnitude`, not a `float`.

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

## DECLARED LIMIT — what this check does NOT catch, and which layer does

Required by `CD-RULE-004` and by the WO-2R dispatch, drawn in the pattern of
`CD-RT-012-NO-EXECUTION-INTERFACE`, whose declaration an independent auditor examined and judged
**honestly drawn, and drawn conservatively**. That auditor's caveat is why this section exists:
*"CD-AC-002's AST guard has comparable limitations (intra-procedural, static) and NO comparable
written declaration, which is why CD-ASR-F01 is reported at HIGH."*

The same list, in the same words, is in the header of `tools/register/check_no_blend.py` and in the
comment above this test's entry in `required-tests.yaml`.

**THIS CHECK IS A STATIC READ OF SOURCE TEXT AT ONE COMMIT, AND ITS FLAVOUR PROPAGATION IS
INTRA-PROCEDURAL.** Both limitations are permanent. They are not defects to be repaired in a later
work order; they are what a static intra-procedural checker *is*.

1. **INTER-PROCEDURAL FLOW.** A value carried into a function is not followed; a parameter
   annotated `float` carries no dial flavour whatever the caller passed. MEASURED EXAMPLE, which
   exits `0` here — this is escaped variant `E01` verbatim:
   ```python
   def _fold(left: float, right: float) -> float:
       return (left + right) / 2.0
   def banner_figure(dials):
       return _fold(dials.equity.value.score, dials.monetary.value.score)
   ```
   THE TYPE LAYER CARRIES THIS: executed, `_fold` raises
   `TypeError: unsupported operand type(s) for +: 'DialMagnitude' and 'DialMagnitude'`.

2. **DYNAMIC ATTRIBUTE ACCESS ERASES FLAVOUR ENTIRELY.** MEASURED EXAMPLE, which exits `0` here —
   this is escaped variant `E02` verbatim, and it is the stronger of the two because it needs no
   allowlisted path:
   ```python
   _SLOTS = ("equity", "monetary")
   magnitudes = [getattr(dials, slot).value.score for slot in _SLOTS]
   return sum(magnitudes) / len(magnitudes)
   ```
   No dial marker appears in any expression, so nothing is ever flavoured and no rule can fire.
   THE TYPE LAYER CARRIES THIS: executed, `sum` raises
   `TypeError: unsupported operand type(s) for +: 'int' and 'DialMagnitude'`.

3. **THE RULE 2 ALLOWLIST IS A REAL HOLE IN RULE 2, BY DESIGN.** Six paths may consume both dials
   in one expression, and `E01` was planted in one of them (`src/crash_detector/serving`). RULE 1
   has no allowlist and applies there in full, but RULE 1 only sees arithmetic it can attribute to
   both dials **in one scope**. MEASURED EXAMPLE: any inter-procedural fold placed under
   `src/crash_detector/serving/` is invisible to both rules.

4. **THE SCANNED SET.** Only `src/crash_detector/` and `deploy/entrypoints/` are read. `tests/` is
   deliberately excluded — the tests for CD-AC-002 must write `operator.add(equity, monetary)` in
   order to assert that it raises. MEASURED EXAMPLE: a blend placed in `tests/` or `db/` exits `0`
   here. It cannot reach a shipped image (all six application Dockerfiles COPY exactly `src/` and
   `deploy/entrypoints/`), but this check does not see it.

5. **IT READS SOURCE, NOT BEHAVIOUR.** A blend assembled at runtime — from configuration, from a
   plugin, from `eval`, or from a module written at import time — is outside a static check
   entirely. MEASURED EXAMPLE: `exec(open(cfg).read())` is one expression naming no dial. THE TYPE
   LAYER CARRIES THIS, because the refusal is a property of the objects rather than of the text.

6. **A NUMBER ALREADY RELEASED IS AN ORDINARY FLOAT, AND THE EXITS ARE MANY.**
   `quantity_for(<dial id>)` yields a bare `float` to a caller that names its one dial — and so,
   without the caller naming anything, do `repr`, `str`, `format`, an f-string, `%`-formatting,
   `pprint`, a log line, `json.dumps` over `__getstate__`, the bytes of a `pickle` and `getattr` on
   the private slot. Two such floats can be added. MEASURED EXAMPLE, which RULE 1 **does** catch
   when spelled with the dial ids and does **not** catch when the ids are reached dynamically:
   ```python
   e = dials.equity.value.score.quantity_for(EQUITY_DIAL_ID)
   m = dials.monetary.value.score.quantity_for(MONETARY_DIAL_ID)
   blended = (e + m) / 2.0
   ```
   **THIS BOUNDARY PREVIOUSLY READ "THE PUBLICATION BOUNDARY CARRIES THIS". THAT WAS MEASURED FALSE
   AND IS WITHDRAWN** (`CD-PL-F54`; CD-RULE-006 exists because of it). The Project Lead re-wrapped
   the blend as `DialMagnitude(dial_id="equity_crash", quantity=blended)`, whose provenance IS
   exactly the slot's dial, and `number_for_dial_slot("equity_crash", <that>)` **returned 0.5**.
   Two declarations each assumed the other was covering the route.

   **THE RE-ENTRY CARRIES THIS, AND HERE IS THE EVIDENCE** (CD-RULE-006). Executed on a pristine
   extraction, from two legitimately constructed magnitudes of 0.4 and 0.6, every one of `PL-Q4`,
   `PL-Q5`, `PL-Q6`, `PL-Q9`, `V16a` (f-string, no `repr` anywhere) and `V16b` (JSON round trip of
   `__getstate__`, no `repr` anywhere) raises
   `QuantityProvenanceMissing: a bare number (0.5) was offered as dial 'equity_crash''s magnitude.`
   What is NOT claimed is that the addition is refused: it is not, `PL-Q1a` still returns 1.0, and
   that is the honest state. The claim is that the sum cannot become a magnitude again. Stated
   identically in `src/crash_detector/dials/magnitude.py` (boundary A),
   `src/crash_detector/dials/provenance.py`, the register entry and
   `CD-RT-002-TYPE-NO-ARITHMETIC.md`.

7. **THE ADMISSION DOOR IS A DECLARATION, AND RULE 4 GUARDS IT BY REGISTRY, NOT BY TRUTH.**
   `observed_for_dial` is the base case of the re-entry closure and it believes what it is told:
   something has to be the first number or the product cannot exist, and a base case that had to
   prove itself would need a base case of its own. A module that calls it with a blend and a
   fabricated `inputs_used` obtains a magnitude. MEASURED EXAMPLE — `V12`, which is `PL-Q9` with the
   door added: this check **FAILS** on it with two RULE 4 violations (the import and the call) while
   its RUNTIME is **not** refused and publishes 0.5.
   **NOT PROVED TO BE CARRIED ANYWHERE AT RUNTIME.** RULE 4 is the only layer over it and RULE 4 is
   static, so this residue inherits every limitation in this list. Its own residues are an edit to
   `DECLARED_ADMISSION_SITES` itself — a deliberate act with a written reason, and the first thing a
   reviewer should look at — a module outside the scanned set (boundary 4), and a dynamically
   assembled door name (boundary 5). `V13`, which reaches the door through `importlib` and `getattr`
   with a whole string, **is** caught.

**EVERY "CARRIES THIS" ABOVE WAS RE-MEASURED AT THE COMMIT THAT WROTE IT**, not inherited
(CD-RULE-006). Boundaries 1, 2, 3 and 5 hand their residue to the type layer, and `E01` and `E02`
both raise `TypeError` when executed on a pristine extraction. Boundary 6 hands its residue to the
re-entry and carries six executed refusals. Boundary 7 hands its residue to nobody at runtime and
says so.

**DO NOT READ A CLEAN RUN OF THIS CHECK AS PROOF THAT NO CODE PATH COMBINES THE TWO DIALS.** It was
clean for both blends that produced `CD-ASR-F01`. The pair to weigh is this check together with
`CD-RT-002-TYPE-NO-ARITHMETIC`, which is where the runtime property is evidenced.

**FOR THE AUDITOR.** A CD-AC-002 variant landing beyond a boundary above is a finding against
**this declaration** — was the limit honestly drawn? — and not an automatic RED against the guard.
A variant that reaches the violation by a route a boundary above says is covered by the type layer
or by the re-entry, and is nevertheless **not refused when EXECUTED**, is a defect in the closure
and should be reported as one. Boundary 7 makes no such claim and a variant landing there is
landing inside a declared limit, not outside one.

## Negative control

A single expression consuming both dial types outside the allowlisted container and serving layer — the canonical form being `combined = (equity + monetary) / 2`, and what this check reaches being any arithmetic, comparison or aggregation over the two together **within one scope**, including the three-statement spelling that its intra-procedural flavour propagation follows. RULE 3 additionally reports any expression naming `_DialMagnitude__quantity`, by attribute or as a string handed to `getattr`, and any call of `__getstate__`, `__reduce__` or `__reduce_ex__`. RULE 4 additionally reports any naming of `observed_for_dial`, `derived_within_one_dial` or `DeclaredQuantity` outside the four declared admission sites, an import included.

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
