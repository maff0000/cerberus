# VARIANT MANIFEST — WO-2R3, seat `CD-ENG-WO2R3-01`

**NOTHING UNDER `variants/` IS EXECUTABLE** (`PBG-ASSURE-001`). These are `git apply`-able
patches and prose. Two of them ADD a probe script to the tree they patch; the probe is data
inside a patch, it is not a runner, and nothing here runs anything.

**THIS CORPUS PROVES NOTHING ABOUT ANY CLASS** (`CD-D-047`). It is given in full so that
fitting a guard to it is worthless. It is a regression floor and the fourth Assurance seat's
EXCLUSION LIST — read it so you can avoid these routes, not so you can repeat them.

## How to run any row

```
git archive 9e1aba016f812e55c1dd59feab53fdbbcc2e871a | tar -x -C /tmp/cd-v && cd /tmp/cd-v
git apply -p1 variants/WO-2R3/<patch>
<the command in the row>
```

A **separate pristine extraction per variant**, so no variant contaminates another; run,
then discard. Never a `git worktree`, and never the Engineer's worktree. `python3 -B`
throughout so no `__pycache__` is written into a governed tree (`PBG-RT-001`).

Every patch was generated with `git diff` and never by hand (`CD-ENG-WO2R-F13`). Every one
was re-checked with `git apply --check` against a pristine extraction of
`9e1aba016f812e55c1dd59feab53fdbbcc2e871a`: **10 of 10 APPLY.**

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

## What is NOT here

The **violated arms of P1–P4 and P8** are increment 1's and are not restated. The **eleven
declared plants** under `plants/` are a different artefact with a different rule (`CD-D-033`)
and are not variants. **THREE of those eleven no longer apply, and they did not apply at
`7b00ce9` either** — the condition pre-dates increment 2, which changed nothing about it.
Named so nobody has to diff for them: `plants/CD-AC-001/CD-RT-001-ABSENCE-RENDERS-UNKNOWN.patch`,
`plants/CD-AC-001/CD-RT-001-AST-NO-NUMERIC-DEFAULT.patch`,
`plants/CD-AC-003/CD-RT-003-ENGINE-NO-WITNESS-REACH.patch`. Reported to the Project Lead; not
deleted, not silently updated, and owed at increment 4.
