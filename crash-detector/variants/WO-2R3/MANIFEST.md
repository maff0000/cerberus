# VARIANT MANIFEST — WO-2R3, seat `CD-ENG-WO2R3-01`

**NOTHING UNDER `variants/` IS EXECUTABLE** (`PBG-ASSURE-001`). These are `git apply`-able
patches and prose. Nine of them ADD a probe script to the tree they patch; the probe is data
inside a patch, it is not a runner, and nothing here runs anything.

**THIS CORPUS PROVES NOTHING ABOUT ANY CLASS** (`CD-D-047`). It is given in full so that
fitting a guard to it is worthless. It is a regression floor and the fourth Assurance seat's
EXCLUSION LIST — read it so you can avoid these routes, not so you can repeat them.

## How to run any row

```
git archive <SHA> | tar -x -C /tmp/cd-v && cd /tmp/cd-v
git apply -p1 variants/WO-2R3/<patch>
<the command in the row>
```

`<SHA>` is `9e1aba016f812e55c1dd59feab53fdbbcc2e871a` for **V16–V25** (WO-2R3 increment 2) and
the increment-3 lane head for **V26–V32**. Every row states which SHA its numbers were
measured at, because a number measured at one SHA and quoted at another is the thing
CD-RULE-009 exists to stop.

A **separate pristine extraction per variant**, so no variant contaminates another; run,
then discard. Never a `git worktree`, and never the Engineer's worktree. `python3 -B`
throughout so no `__pycache__` is written into a governed tree (`PBG-RT-001`).

Every patch was generated with `git diff` and never by hand (`CD-ENG-WO2R-F13`).

**APPLY CHECK, RE-RUN AT WO-2R3 INCREMENT 3** against a pristine extraction of
`78a2cc9c265071d07b45ff328977438b32eebb03` (the increment-3 code commit), command
`for p in variants/WO-2R3/*.patch; do git apply --check -p1 "$p"; done`:
**V16–V25: 10 of 10 APPLY. V26–V32: 7 of 7 APPLY.** `git apply --check` is a static
applicability test and nothing more — it is not evidence that any variant still escapes, and
the escape column below is measured by RUNNING each one.

**THE ASSERTION COUNTS QUOTED FOR V16–V19 MOVED AND ARE RE-MEASURED HERE.** The static check
reported 38 assertions at increment 2 and reports **54** at increment 3, because `collectors`
joined its RULE 1. The rows below carry the increment-3 numbers; the increment-2 numbers are
not deleted from the record, they are superseded (`PBG-CONT-003`).

## The rows

| id | patch | PROPOSITION violated | expected signature | command |
|---|---|---|---|---|
| **V20** | `V20-p7-added-parameter.patch` | **P7.** A new parameter added to a decorated door without being declared to `admits` is REFUSED ON EVERY CALL. This is the AUTHORITATIVE P7 arm: `tolerate_stale: bool = False` added to the REAL `resolve_panel`. | check exit **1**, `PARAMETER_NOT_DECLARED_TO_ADMITS`; suite **57 failed** (from 1482 passed); an ordinary call that does not pass the argument raises `UndeclaredParameter: resolve_panel is a FAULTED door and every call to it is refused` | `python3 -B tools/register/check_judgement_path_doors.py --root .` and `PYTHONPATH=src python3 -B -m pytest tests -q` |
| **V23** | `V23-p7-violated.patch` | **P7 VIOLATED ARM.** The same added parameter with the `@admits` decorator removed. | both calls ADMITTED; `Agrees`; `RENDERS: WITNESS AGREES`; the new argument arrived UNGUARDED | `PYTHONPATH=src python3 -B <the P7 probe>` |
| **V21** | `V21-p5-violated.patch` | **P5 VIOLATED ARM.** `evaluate` requires exactly `ConfigSnapshot` (A2). Decorator removed. | `ASR3-F05`'s duck ConfigSnapshot ADMITTED; its own `covers()` called once, on an age of **315 360 000 s**, against a declared window of 600 s | `PYTHONPATH=src python3 -B <the P5 probe>` |
| **V22** | `V22-p6-violated.patch` | **P6 VIOLATED ARM.** `resolve_panel` requires exactly `PanelRow` or `None` (A4). Decorator removed. | `ASR3-F04`'s row -> `Agrees`; `RENDERS: WITNESS AGREES` with the stored state `UNAVAILABLE` | `PYTHONPATH=src python3 -B <the P6 probe>` |
| **V16** | `V16-new-package-undecorated-door.patch` | DECLARED LIMIT 2 of the static check: RULE 1's package list is a VOCABULARY. Adds `src/crash_detector/judging/decide.py`, public, undecorated, unannotated. | check exit **0**, `PASS — 38 assertions, 0 violations`. **THE LIMIT IS REAL.** | `python3 -B tools/register/check_judgement_path_doors.py --root .` |
| **V17** | `V17-constructor-body-escape.patch` | DECLARED LIMIT 1: constructors are not subjects. Deletes the `type(spec) is not DialSpec` loop from `ConfigSnapshot.__post_init__`. | check exit **0**, `PASS — 38 assertions`. **THE LIMIT IS REAL.** | `python3 -B tools/register/check_judgement_path_doors.py --root .` |
| **V18** | `V18-counterfeit-admits.patch` | DECLARED LIMIT 4: `admits` is recognised by its NAME in the source. A do-nothing `admits` in `own_terms.py`, imported by `serving/witness_resolver.py`. | check exit **0**, `PASS — 38 assertions`; the duck row RENDERS `WITNESS AGREES`; **and the runtime catches it: 3 FAILED**. The named carrier, measured. | `python3 -B tools/register/check_judgement_path_doors.py --root .` then `PYTHONPATH=src python3 -B -m pytest tests -q` |
| **V19** | `V19-b3-door-body-rewrite.patch` | DECLARED LIMIT 5 of `admission.py`: the six `ESTABLISHED_HERE` uses on §B.3's doors are a LIMIT, not a closure. Deletes the exact-type refusal from `derived_within_one_dial`'s body, decorator untouched. | check exit **0**, `PASS — 38 assertions`. §D.1's rule is NOT held at that door and the patch shows why. | `python3 -B tools/register/check_judgement_path_doors.py --root .` |
| **V24** | `V24-wrapped-attribute-bypass.patch` | **MINE.** A door must not publish a way round itself. Adds a probe that calls the undecorated function through `functools.wraps`'s `__wrapped__`, and through `__closure__`. | ARM 1 (front door) REFUSED `NotAdmitted`; ARM 2 (`__wrapped__`) **REFUSED — `AttributeError: 'function' object has no attribute '__wrapped__'`**; ARM 3 (`__closure__`) **ESCAPED -> `Agrees`; RENDERS `WITNESS AGREES`** | `PYTHONPATH=src python3 -B probe_v24_wrapped_bypass.py` |
| **V25** | `V25-admitted-then-rewritten.patch` | **MINE.** Satisfy an exact-type door HONESTLY, then rewrite the admitted value past `frozen` and use it. Swaps a real `ConfigSnapshot`'s `model_registry` for a caller object whose `get()` IS the resolution. | REFUSED at both arms: `NotAdmitted: establish_model_for_dial: model_registry=CallerRegistry is not admitted; this door requires exactly ModelRegistry` | `PYTHONPATH=src python3 -B probe_v25_admitted_then_rewritten.py` |

## The two that are MINE, and why each is a DIFFERENT ROUTE

**V24 — the decorator's own attribute surface.** No variant in WO-2's `E01`..`E10`, WO-2R's
six, WO-2R2's `V01`..`V15`, the three auditors' sets or the Project Lead's `PL-*` probes
attacks a decorator's attribute surface, for a simple reason: **until WO-2R3 increment 2
there was no decorator on a judgement-path door to attack.** The route arrived with the
mechanism. MEASURED BEFORE THE FIX, against this seat's own work:
`resolve_panel.__wrapped__(duck_row, now_utc=..., staleness_window_seconds=600.0)` returned
`Agrees` and rendered `WITNESS AGREES` — `ASR3-F04` published with every door decorated.
`__wrapped__` is now deleted in `admits` itself, so the closure applies to every door the
mechanism has ever made and will make. **THE `__closure__` HALF IS NOT CLOSED**, is asserted
OPEN by `tests/test_admission.py::test_a_door_publishes_no_way_round_itself`, and is
DECLARED LIMIT 6. It is true of every decorator in Python, including this codebase's own
`_absence_is_never_a_number`, and CPython offers no way to prevent it.

**V25 — the interval between admission and use.** WO-2R2's `V05` and `V10` and the `PL-*`
probes rewrite fields to defeat a BODY check on the same object. V25 does the opposite: it
satisfies an EXACT-TYPE DOOR honestly first — the value genuinely IS a `ConfigSnapshot` and
genuinely passed every §C.5 invariant at construction — and then attacks the gap between
being admitted and being used. That route did not exist before there was a door to satisfy.
**REFUSED**, and the layer that refuses it is not the `evaluate` door: it is
`establish_model_for_dial`, which increment 1 made the ONE resolution door and which
increment 2 decorated, so the registry is re-established at the moment it resolves rather
than at the moment the snapshot was built. That is why `ConfigSnapshot.model_for` calling
the same function as `ConfigSnapshot.__post_init__` is load-bearing and not tidiness.


## The rows added at INCREMENT 3 — A6, the collector boundary (§D.3, both parts)

Measured at `78a2cc9c265071d07b45ff328977438b32eebb03` unless a row says otherwise. Every one
was RUN in a separate pristine extraction and discarded; the output quoted is the output
observed.

| id | patch | PROPOSITION violated | observed | command |
|---|---|---|---|---|
| **V26** | `V26-conforming-hostile-adapter.patch` | **CD-BP-003, IN THE POSITIVE DIRECTION — the declared limit's executable example. NO GUARD IS REMOVED.** An adapter supplying all five protocol members, returning an exact `FetchedResponse` whose payload conforms to the schema it declared itself. | **ADMITTED.** `missing protocol members: ()`; `ADMITTED: OK`; `payload recorded: {'reading': 0.0}`; `source_id recorded: src.does.not.exist`; `rows written: 1`; `reading admitted: True` | `PYTHONPATH=src python3 -B probe_v26_conforming_hostile_adapter.py` |
| **V27** | `V27-lying-ledger.patch` | **A6-5 VIOLATED ARM.** The `bool()` coercion on the ledger verdict, restored. A ledger answering a truthy STRING. | **ESCAPED.** Two collections of ONE source period both report `reading_admitted: True`. One period, two readings. | `PYTHONPATH=src python3 -B probe_v27_lying_ledger.py` |
| **V28** | `V28-policy-subclass-isinstance.patch` | **A6-1 VIOLATED ARM.** `isinstance(policy, RetryPolicy)` restored in the body in place of exact type at the door. | **ESCAPED.** `MAX_ATTEMPTS_CEILING: 5`; `policy.max_attempts as asked: 5000`; the probe halted the runner at **201 attempts**. | `PYTHONPATH=src python3 -B probe_v28_policy_subclass.py` |
| **V29** | `V29-fetched-response-subclass.patch` | **A6-4 VIOLATED ARM.** `isinstance(response, FetchedResponse)` restored at the point of return from `fetch`. | **ESCAPED.** `outcome: OK`; `payload STORED: {'reading': 999.0}` — the validator saw `{'reading': 1.5}`. `payload asks made: 4`. | `PYTHONPATH=src python3 -B probe_v29_fetched_response_subclass.py` |
| **V30** | `V30-validator-return-discarded.patch` | **A6-6 VIOLATED ARM.** The validation verdict discarded again, so "conforming" means only "did not raise". | **ESCAPED.** A NON-conforming payload recorded as `OK`: `payload stored: {'reading': 'not a number'}`; `reading admitted: True`. | `PYTHONPATH=src python3 -B probe_v30_validator_return_discarded.py` |
| **V31** | `V31-caller-supplied-sleep-restored.patch` | **§D.3 PART 1's COUNTERFACTUAL (CD-D-079).** Part 1 is a DELETION, so its counterfactual is not "remove a guard" — it is **put the parameter back**. `sleep` is a parameter again, admitted by `callable()`. | **ESCAPED.** `policy.backoff_seconds: 5.0`; `worst_case_seconds: 25.0`; `backoffs the policy asked: [5.0, 5.0, 5.0, 5.0]`; **`seconds actually waited: 0.0004`**. | `PYTHONPATH=src python3 -B probe_v31_caller_supplied_sleep.py` |
| **V32** | `V32-arrival-establishment-removed.patch` | **A6-7, A6-8 AND A6-9 VIOLATED ARMS, in one patch and labelled as three.** The sink-return check, the whole-protocol conformance check and the `own_str` rebuild of the adapter's identity, all removed. | **ESCAPED, all three.** ARM 1: a sink that writes nothing and returns a string is ADMITTED, `rows_recorded = 1`. ARM 2: an adapter missing `is_empty` is recorded `Malformed EMPTINESS_UNDECIDABLE_AttributeError` — OUR wiring defect blamed on the source. ARM 3: `source_id` stored as the SUBCLASS and `result.source_id == 'anything at all'` is **True**. | `PYTHONPATH=src python3 -B probe_v32_arrival_establishment_removed.py` |

## The increment-3 rows that are MINE, and why each is a DIFFERENT ROUTE

**Every route in every prior corpus enters through the JUDGEMENT half of the system** — a
model object into a `DialSpec`, a duck row into `resolve_panel`, a duck snapshot into
`evaluate`, a decorator's attribute surface, the gap between admission and use. The third
audit's own `WHAT I DID NOT EXAMINE` names the collector path, and A6 was found by the
Project Lead in the amendment, not by an auditor.

**V29 and V27 enter through what the INPUT half HANDS BACK**, which is a different half of
the system and a different kind of route: not "what did the caller pass in" but "what did the
foreign object answer when this system asked". V29 is `ASR3-F04`'s property trick relocated
to a `FetchedResponse` returned by `fetch`; V27 is the same shape reached through `bool()`
coercion rather than through a property, and it defeats IDEMPOTENCY rather than a dial
reading. Neither appears in `E01`..`E10`, in WO-2R's six, in WO-2R2's `V01`..`V15`, or in the
Project Lead's `PL-*` probes.

**V26 is a different kind of artefact from all of them and is labelled as one.** It removes
no guard and demonstrates no escape from a closure: it demonstrates the DECLARED LIMIT, by
showing an object that IS ADMITTED and saying what is not proved about it. A limit stated only
in prose is a limit an auditor has to take on trust.

## What is NOT here

The **violated arms of P1–P4 and P8** are increment 1's and are not restated. The **eleven
declared plants** under `plants/` are a different artefact with a different rule (`CD-D-033`)
and are not variants. **THREE of those eleven no longer apply, and they did not apply at
`7b00ce9` either** — the condition pre-dates increment 2, which changed nothing about it.
Named so nobody has to diff for them: `plants/CD-AC-001/CD-RT-001-ABSENCE-RENDERS-UNKNOWN.patch`,
`plants/CD-AC-001/CD-RT-001-AST-NO-NUMERIC-DEFAULT.patch`,
`plants/CD-AC-003/CD-RT-003-ENGINE-NO-WITNESS-REACH.patch`. Reported to the Project Lead; not
deleted, not silently updated, and owed at increment 4.
