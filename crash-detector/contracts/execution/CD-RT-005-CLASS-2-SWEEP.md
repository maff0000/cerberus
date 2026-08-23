# Execution contract — CD-RT-005-CLASS-2-SWEEP

**CD-AC-005** (and **CD-AC-002**) · every delegated judgement on the deciding paths is enumerated
and carries a written or DERIVED disposition · obligation **MANDATORY** · scope **CLASS** ·
contract created in **WO-2R3 increment 10, item 4**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every declared
test to name an execution contract that RESOLVES, and because `CD-RULE-004` requires a guard's
declared limits to be stated identically in three places. It states how this test is run and what
its exit codes mean. **It states no result.**

## Why this contract did not exist until now, which is itself the defect it closes

`CD-ENG-WO2R3-07` reported at increment 9: *"the Class-2 sweep has no `required-tests.yaml` row and
no execution contract, so 'three places' does not exist for it."* `CD-RULE-004` is a rule about
three places. **AN INSTRUMENT WITH ONLY ONE PLACE CANNOT SATISFY IT**, and this tool's declared
limits therefore lived only where a reader of the source would find them. `PO-DECISIONS-0018`
ruling 4 put `CD-D-166`'s closure inside the remedy increment as *"documentary + `tools/sweep/`"*,
and the documentary half is this file plus the register row.

## The proposition

> **EVERY SITE IN THE CLASS-2 SUBJECT SET AT WHICH AN OPERATION COULD BE EXECUTED BY AN OBJECT THE
> ENCLOSING MODULE DID NOT CONSTRUCT IS ENUMERATED, AND CARRIES A WRITTEN OR DERIVED DISPOSITION.**

**THIS TOOL IS THE ENUMERATION, NOT THE CLOSURE, AND THE DIFFERENCE IS THE WHOLE POINT.** The
closure is `crash_detector.own_terms`: values are RE-CONSTRUCTED at the door, so no method a caller
defined runs while anything is being decided. That is a runtime property of the values and it does
not depend on this file existing. What this tool does is make the SURFACE countable, and fail when
the surface changes without anyone saying so.

## How it is run

```bash
python3 -B tools/sweep/delegated_judgement_sweep.py --root .
python3 -B tools/sweep/delegated_judgement_sweep.py --root . --list
python3 -B tools/sweep/delegated_judgement_sweep.py --root . --list-undeclared
```

`--root` is the repository root of the tree under audit. The tool needs no `PYTHONPATH`, no
installed package and no wrapper: an auditor runs it from a tree they extracted themselves
(`PBG-ASSURE-001`).

## Exit codes

| code | meaning |
|---|---|
| `0` | Every tier-1 admission and every subject module carries a written or DERIVED disposition, and no disposition is declared for a site that does not exist. **READ THIS AS WHAT IT IS: a statement about the SURFACE and never about the class.** It includes sites declared as OPEN DEFECTS, which are open defects and not fixed ones. **A REGISTER FULL OF `DEFECT_OPEN` BUYS NOTHING.** A zero exit here is ARITHMETIC OVER THE DECLARATION SET, NOT EVIDENCE ABOUT THE CODE — and the tool prints that sentence itself, on the zero-exit path, so an auditor does not have to know to ask. |
| `1` | At least one violation: an undeclared tier-1 admission; an undeclared module; a STALE DECLARATION for a site that no longer exists; an unknown or malformed disposition word; a mandatory evidence field missing; a `CARRIER_ONLY` with a product caller; a `finding` that does not resolve OPEN; or a redrafted-word field that does not hold. Every violation is printed with its site key. |

**THE REGISTER IS ASSERTED BY SET EQUALITY IN BOTH DIRECTIONS.** A site with no disposition fails
this tool, and a disposition for a site that no longer exists fails it too — because a register
that only complained about additions could be satisfied by deleting the entry that does the
complaining.

## Declared limits (`CD-RULE-004`)

Stated identically here, in the header of `tools/sweep/delegated_judgement_sweep.py`, and in the
register entry. **LIMIT 5 IS ALSO PRINTED BY THE TOOL AFTER ITS OWN VERDICT ON EVERY RUN, PASS OR
FAIL.**

**LIMIT 1 — IT IS STATIC AND INTRA-PROCEDURAL.** It reads one expression at a time and does not
know what any name is bound to at runtime. A disposition of `ESTABLISHED` is a CLAIM BY THE SEAT
THAT WROTE IT, not something this tool verified. The runtime evidence for those claims is
`tests/test_own_terms.py` and the variants under `variants/WO-2R2/CLASS-2/`, and **the claim an
auditor should attack is the disposition text, not the count.** For a site whose disposition is
wrong, **NOT PROVED TO BE CARRIED ANYWHERE** — a mis-declared disposition is invisible here by
construction.

**LIMIT 2 — IT SEES ONLY OPERATORS AND CALLS WRITTEN LITERALLY IN THE SUBJECT MODULES.** An
operation reached through `operator.lt`, `functools.reduce`, a dunder invoked by name, a
comprehension over a caller's generator, or any C-level protocol call CPython makes on this code's
behalf is not a node this tool visits.

**LIMIT 3 — ITS SUBJECT SET IS AN IMPORT CLOSURE**, so a module that reaches a judgement without
importing one of the six entry modules is outside it. Every run prints the outside modules BY NAME,
so the exclusion is disclosed rather than discovered. **NOT PROVED TO BE CARRIED ANYWHERE.**

**LIMIT 4 — A DISPOSITION IS KEYED BY THE EXPRESSION'S TEXT**, so renaming a local variable makes
the site UNDECLARED and this tool FAILS. That is the safe direction and it is deliberate. It also
means a clean run is evidence about THIS SOURCE TEXT and survives no rewriting of it.

**LIMIT 5 — `CD-D-166`, THE `gates` FIELD OF `UPSTREAM_OF_THE_PATH`. IT IS UNSOUND IN BOTH
DIRECTIONS AT ONCE: IT REFUSES WHEN NOTHING IS WRONG AND IT PASSES WHEN THE CLAIM IS FALSE.**

Closed by DECLARATION and not by repair, on `PO-DECISIONS-0018` ruling 4. **BOTH DIRECTIONS ARE
STATED WITH THEIR MEASURED NUMBERS, BECAUSE A DECLARED LIMIT THAT ONLY ADMITS THE FLATTERING HALF IS
NOT A DECLARATION.**

What the word CLAIMS: *"this site is UPSTREAM of a judgement path — what it decides is whether
judgement-path doors establish their arguments at all."* What the machine holds is only that the
named 4-tuple EXISTS in this run's measured site set and lies in a DIFFERENT module. **IT DOES NOT
CHECK THAT IT IS DOWNSTREAM, REACHABLE, OR RELATED.**

### Direction 1 — it refuses when nothing is wrong

Re-measured by `CD-ENG-WO2R3-09` at WO-2R3 increment 10, in a pristine extraction:

```bash
git archive <sha> | tar -x -C <armA>
# rename ONE local in src/crash_detector/engine/config.py:  window -> staleness_window
cd <armA> && python3 -B -m pytest -q tests/test_staleness.py tests/test_evaluate.py \
    tests/test_config_source_registry.py tests/test_envelope_contracts.py
#   -> 183 passed        THE GATING RELATION IS ENTIRELY INTACT
cd <armA> && python3 -B tools/sweep/delegated_judgement_sweep.py --root .
#   -> exit 1, FAIL — 548 sites, 53 violations
#   -> 31 x GATES_SITE_DOES_NOT_EXIST
```

**EIGHTEEN VIOLATIONS BECAME FIFTY-THREE AND NOTHING WAS BROKEN. THE REGISTER WAS.**

### Direction 2 — it passes when the claim is false

Same increment, second extraction, **ZERO lines under `src/` touched**. **BOTH ARMS WERE MEASURED AT `625e3c8`, WHERE THE ROW COUNT WAS 43.** Item 5 of the same increment then re-pointed five rows away from `UPSTREAM_OF_THE_PATH`, so the live count is lower — and the instrument DERIVES AND PRINTS the live count at every run. **THAT DIVERGENCE IS THIS VERY LIMIT'S DIRECTION 1 HAPPENING TO ITS OWN EVIDENCE, AND IT IS LEFT VISIBLE RATHER THAN TIDIED AWAY.**

```bash
git archive <sha> | tar -x -C <armB>
# repoint ALL 43 `gates` values in tools/sweep/declared_dispositions.py at
#   ('crash_detector.time_utc','parse_utc','ISINSTANCE','isinstance(text, str)')
diff -rq <armB>/src/ <control>/src/
#   -> IDENTICAL: no product source touched
cd <armB> && python3 -B tools/sweep/delegated_judgement_sweep.py --root .
#   -> exit 1, FAIL — 548 sites, 18 violations    BIT-FOR-BIT THE CONTROL'S VERDICT
#   -> 0 x GATES_SITE_*
```

**ALL 43 GATING CLAIMS WERE FALSE AND THIS INSTRUMENT SAID NOTHING.**

### Why this is a declared limit and not a fix

Direction 1 is not repairable while a site key's fourth element is SOURCE TEXT —
`CD-ENG-WO2R3-07`'s **F17**: *"`gates` cannot be made structural by adding a clause, because it is a
site key whose fourth element is SOURCE TEXT — so any criterion keyed on it fails the rename test by
construction"* — and coarsening the key would weaken the both-directions set equality the whole
register rests on. Direction 2 needs an inter-procedural, cross-module dataflow fact —
*does a mis-decision at this site reach that door's operand* — which **LIMIT 1** says this tool does
not have.

**AND A CANDIDATE CLAUSE WAS MEASURED AND REJECTED BY A NUMBER, RECORDED HERE RATHER THAN QUIETLY
DROPPED.** The obvious strengthening for direction 2 is to require the `gates` module to
transitively import the DECLARING module, from the import graph the tool already builds. It holds
for all 43 real rows, and it **does** refuse direction 2's arm — `reach(crash_detector.time_utc)` is
exactly two modules and `crash_detector.admission` is not one of them. **IT WAS STILL REJECTED**: of
the 19 subject modules, **TEN other than `crash_detector.admission` transitively import it, and
THIRTEEN other than `crash_detector.establishment` transitively import that**, so the same falsehood
repointed at any real site in any of them satisfies the clause while being exactly as false. **A
GUARD THAT STOPS THE REPORTED CASE AND NOT ITS CLASS HAS NOT BEEN TESTED** (`PBG-ASSURE-017`), and
shipping it would let a reader believe `gates` is verified when it would be satisfiable by a string
swap. Those counts are **DERIVED AND PRINTED AT EVERY RUN** so the rejection is not taken on trust.

### What `gates` is worth, stated plainly

**IT IS A POINTER THAT ROTS LOUDLY.** It guarantees the named site existed in the tree at the moment
the register was last green, and **nothing else**. The gating RELATION is a **CLAIM BY THE SEAT THAT
WROTE THE ROW**, carried in that row's `note` field, and **THAT PROSE is what an auditor should
attack — not this field.** **NOT PROVED TO BE CARRIED ANYWHERE** (`CD-RULE-006`): no layer of this
project verifies the gating relation, and none is claimed to.

**THE VACUITY GUARD ON THIS LIMIT IS DIRECTION 1 ITSELF.** The field CAN refuse — 31 times — so its
silence in direction 2 is not the silence of a clause that never runs.

## The negative control

The tool's own **STALE DECLARATION** and **UNDECLARED** arms are the standing negative control and
they are not hypothetical: at the SHA this contract was written the tool exits **1**. Direction 1
above is additionally a live falsification arm that can be re-run in one command against any
extraction. **RUN THEM; DO NOT QUOTE THEM** (`CD-PL-F133`).
