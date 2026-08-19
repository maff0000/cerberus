# Execution contract — CD-RT-012-NO-EXECUTION-INTERFACE

**CD-AC-012** · No execution pathway exists · obligation **MANDATORY** · scope **CLASS** ·
delivered in **WO-2**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

The application source and the store schema contain no broker, order or execution interface — in any spelling, in any signature, and in any prose that describes one.

## Command

```
python3 tools/register/check_no_execution_interface.py --root .
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

Every Python module and every SQL migration under `src/`, `db/`, `deploy/`, `tests/` and `tools/`, in THREE independent layers: L1 identifier composition, L2 signature shape (the field set of every callable and class, judged WITHOUT its name), and L3 prose (docstrings, comments, string literals, SQL comments). The register's own guard files are excluded, with the exclusion printed on every run: a guard must name what it forbids in order to forbid it, and its vocabulary is data rather than an interface.

## Why it is asserted this way

PID §6 says advisory-only is STRUCTURAL, not policy. A policy is a sentence somebody can change in an afternoon.

L2 and L3 exist because L1 alone was not enough and was PROVED not to be. The Project Lead's independent probe planted `submit_instruction(symbol, qty, side)` and it passed — identically with and without a docstring reading "Route an order to the broker for execution" (CD-PL-F32). The class gap, not the instance, was that one question was being asked of every construct. An auditor planting its own variant should attack all three layers, and should assume a fourth gap exists: three of ten checks in this register were shown to pass a real violation on their first cut.

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

Any order-entry path in the application source or the store schema. The class is wider than a `place_order` stub and the guard is built for the wider class after CD-PL-F32: a callable or class whose FIELD SET is an order ticket (an instrument with a quantity and a side, a price or order type, or a venue) under a neutral name; a transmission verb applied to a tradeable noun in any spelling; a broker SDK import; an execution endpoint literal; an execution identifier in a SQL migration; or PROSE — a docstring or comment saying in plain English that the code routes orders to a broker.

Detection is a **contrast**, and the validator computes it as one: the same declared command
must exit `0` on the clean subject and non-zero on the subject with the violation planted.
A clean arm that fails cannot be told apart from a broken harness, and a broken harness
detects nothing — the validator returns `UNDECIDABLE`, never `PASS`.

The negative control for this test is declared as run record **`RTR-WO2-0001`**.
That record does not exist yet. It is the run the **independent Assurance
seat** will produce — a distinct actor from the one that wrote this test. Until it exists
the validator computes `UNDECIDABLE` for this test and the gate stays shut, which is
correct: this seat may declare which run must evidence its guard, and may not supply it.

## Declared limit

Required by **CD-D-014**, bounded by **CD-D-015**. Stated identically in the header of
`tools/register/check_no_execution_interface.py` and in the comment above this test's entry
in `required-tests.yaml`; the check's header is the longest of the three and carries the
measured example behind each item. This is a statement of scope, not an apology — an auditor
must be able to see the boundary here rather than discover it.

This check does **not** catch:

1. **Deliberate euphemism.** A static reader of natural language has no terminating
   condition against an author choosing words to avoid it. Two rounds of independent probing
   each found a fresh escape of exactly this kind — CD-PL-F32, CD-PL-F35, and the residual
   CD-PL-F38 — all since closed. That each round found *another* is the evidence for this
   limit, and CD-D-015 ends the chase rather than pretending a third round would be the last.
2. **Code named to hide behind the `work_order` sequence-sense suppression.** L1 suppresses
   the token `order` when it follows one of the thirty-one modifiers in
   `ORDER_SEQUENCE_MODIFIERS`, so the guard does not fail on this project's own daily
   vocabulary. A pathway named `work_order_router` to sit inside that suppression escapes L1.
   It escapes the *check* only if it is also shaped to avoid an order ticket, because L2
   reads no names at all.
3. **Any sentence L3 suppresses — and the list is wide.** 46 negation words and 25
   hypothetical words, including `must`, `free`, `advisory`, `absence`, `zero`, `say`,
   `check` and `were`. Measured: `"The engine must send each instruction to the broker"` is
   not read by L3 at all, on `must` alone. The trade was taken because this project's charter
   says repeatedly that it places no orders, and a check whose output is mostly its own
   charter is a check nobody reads.
4. **A motion chain longer than eight words** between a verb of motion and its destination
   noun. CD-PL-F38 widened this from four; CD-D-015 permits no further widening.
5. **Anything that is not `.py` or `.sql` under the five scanned roots.** No YAML, JSON,
   TOML, shell, Markdown, notebook, template, CI job, compiled artefact, vendored dependency
   or container image is read.
6. **Runtime.** This is a static read of source text at one commit.

**What carries the rest.** CD-BP-001, risk-accepted by the Product Owner at Blueprint
acceptance, records that the AST register checks are never a sole guard. CD-AC-012 is
defended by this check, by `CD-RT-012-LOCKFILE-DENYLIST` — which no euphemism in our own
source can evade, because the SDK is named by its publisher and not by us — by
`CD-RT-012-EGRESS-NO-BROKER`, and structurally by the network posture of BLUEPRINT §2 and
§13: cd-engine, cd-public, cd-private and cd-store have no egress at all, so a perfectly
euphemised pathway inside the engine still has nowhere to send an order.

**How to read a clean run.** As evidence about names, shapes and documented intent at one
commit — not as proof of the proposition. For the proposition itself, weigh the egress
posture first: of the four, it is the only one that constrains what the software *can do*
rather than what it says. A CD-AC-012 variant planted beyond this boundary is a finding
against **this declaration** — was the limit honestly drawn? — and not an automatic RED
against the guard (CD-D-014).

## What this contract does not claim

It does not claim the test passes. It does not claim the criterion is satisfied. It does not
admit any evidence: `latest_admitted_run` is null in the register and this seat cannot fill
it in, because an implementation may not certify itself (`PBG-SOD-001`, non-waivable).
