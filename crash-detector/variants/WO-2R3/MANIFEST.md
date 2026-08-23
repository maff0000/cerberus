# VARIANT MANIFEST — WO-2R3, seat `CD-ENG-WO2R3-01`

> **SUPERSEDED AT INCREMENT 7 BY `CD-ENG-WO2R3-03`, AND THE SUPERSEDED WORDING IS QUOTED
> RATHER THAN DELETED** (`CD-RULE-004`, `PBG-CONT-003`). It read:
>
> > *"**NOTHING UNDER `variants/` IS EXECUTABLE** (`PBG-ASSURE-001`). These are `git apply`-able
> > patches and prose. Nine of them ADD a probe script to the tree they patch; the probe is data
> > inside a patch, it is not a runner, and nothing here runs anything."*
>
> **THAT SENTENCE IS FALSE AND HAS BEEN SINCE INCREMENT 6.** `CD-PL-F97` records six executable
> probes landing under this directory with zero rows in this manifest; this increment adds two
> more. **MEASURED, NOT ASSERTED —** `ls variants/WO-2R3/*.py | wc -l` reads **8** at this commit,
> and every one is a `__main__` that imports the product and runs it. A header claiming the
> directory contains no runners, in a directory of runners, is this project's
> hand-maintained-summary defect living in the one file whose whole job is to enumerate.

**WHAT IS TRUE NOW, AND IT IS TWO CLAIMS AND NOT ONE.** (i) The `.patch` rows are `git apply`-able
patches and prose, and nothing applies them but a reader. (ii) The `P-*.py` rows **ARE EXECUTABLE
PROBES**: they are run directly against a tree with `PYTHONPATH=<tree>/src`, they import the
product, and they print a `tree:` provenance line as their first output so a reader can tell which
tree answered (`CD-PL-F98`). **NOTHING UNDER `variants/` RUNS ITSELF, AND NOTHING HERE IS WIRED
INTO A SUITE OR A REGISTER** — that much of the old sentence stands and it is the part
`PBG-ASSURE-001` is about.

**THIS CORPUS PROVES NOTHING ABOUT ANY CLASS** (`CD-D-047`). It is given in full so that
fitting a guard to it is worthless. It is a regression floor and the fourth Assurance seat's
EXCLUSION LIST — read it so you can avoid these routes, not so you can repeat them.

---

## READ THIS FIRST — YOUR FOUR NAMED FIRST TARGETS, AND WHERE EACH ONE ALREADY IS

You are the **fourth Assurance seat**. The Product Owner has already given you four first
targets and none of them is yours to choose or this seat's to drop. This section exists so you
reach them in minutes rather than by reading the tree. **Nothing below is evidence and nothing
below is a defence** — it is a map, and every claim in it is one you should try to break.

| # | Target | Set by | Where it is | Where it is SOFTEST |
|---|---|---|---|---|
| 1 | **P7** — an argument added to a decorated door arrives REFUSED, never unguarded | PO-DECISIONS-0005 ruling 1: *"the fourth Assurance seat is directed to run it first"* | `V20` (baseline) and `V23` (violated) below; mechanism at `src/crash_detector/admission.py`, `_faults` | The refusal is computed at DECORATION from `inspect.signature`. Anything that changes what `inspect.signature` reports — a `__signature__` assignment, a wrapper the mechanism did not make — is not tested here by anyone |
| 2 | **CD-BP-003** — `collect`'s four `Protocol` parameters: a door that ADMITS, not an absence of a door | PO-DECISIONS-0005 ruling 4: *"the fourth Assurance seat's first target"* | `V26` (the POSITIVE example — an object that IS admitted), `V27`, `V29`, `V30`, `V32` below; BLUEPRINT §17 | `missing_adapter_members` asks `hasattr` for **five SPELLED names** and FAILS THE RENAME TEST. It is the only refusal increment 3 relies on that does. **Source trust is NOT PROVED TO BE CARRIED ANYWHERE** |
| 3 | **THE WHOLE §D SCOPING, including the CD-D-105 closure** — a standing invitation | PO-DECISIONS-0007 ruling 2, CD-D-112 | The scope is `JUDGEMENT_PATH_PACKAGES` and the two rules in `tools/register/check_judgement_path_doors.py`; the exclusions are amendment §B.4/§H (`Lifecycle.run(tick)`, `on_shutdown`, store/migrate) | **DECLARED LIMIT 2**: RULE 1's package list is a VOCABULARY — `V16` adds a whole new package with a public undecorated door and the check exits **0**. **NOT PROVED TO BE CARRIED ANYWHERE** |
| 4 | **THE INCREMENT-5 INSTRUMENT'S OWN ENUMERATION** | PO-DECISIONS-0008 ruling 2, CD-D-119 | **IT NOW EXISTS**: `tools/register/check_constructor_field_establishment.py`, landed ALONE at `4a5098d` — one commit BEFORE the mechanism — printing `POPULATION 32` and `DECLARED TO @establishes: 0`. The PO's FLOOR is five (`ConfigSnapshot`, `DialSpec`, `ModelSpec`, `PanelRow`, `AttemptRecord`); **the measured population is 32 and the floor is 5/32 of it** | Attack clause (3) of its DEFINITION. RULE A's package list is a **VOCABULARY** (CHECK LIMIT 2) and RULE B/RULE C resolve names by a FLAT CROSS-MODULE fixpoint that this seat chose because it can only enlarge the class. The former clause (4) is a **declared HEURISTIC** and since `PO-DECISIONS-0010` ruling 1 it gates NOTHING. **THE ADJACENT SET IS GONE**: the class now reads **BODY-BORNE OR ABSENT**, the population is **33** (32 fielded + `Empty` satisfying vacuously) and `V43` is the contrast that proves the widening reached the code path rather than the header. **ATTACK THE WIDENED DEFINITION ITSELF — the Product Owner left that open to you in terms** — and note that the widening changed NOT ONE present verdict, so a green run of this check is evidence of nothing here |

**THE FASTEST ROUTE TO EACH.** Extract a tree yourself, then:

```
# 1  P7
git apply -p1 variants/WO-2R3/V20-p7-added-parameter.patch
python3 -B tools/register/check_judgement_path_doors.py --root .        # expect exit 1
PYTHONPATH=src python3 -B -m pytest tests -q                            # expect 59 failed

# 2  CD-BP-003 — the POSITIVE example. Nothing in this tree refuses it.
git apply -p1 variants/WO-2R3/V26-conforming-hostile-adapter.patch
PYTHONPATH=src python3 -B probe_v26_conforming_hostile_adapter.py

# 3  the §D scoping
git apply -p1 variants/WO-2R3/V16-new-package-undecorated-door.patch
python3 -B tools/register/check_judgement_path_doors.py --root .        # expect exit 0 — THE GAP

# 4  the increment-5 class, and its plant in both arms
python3 -B tools/register/check_constructor_field_establishment.py --root . --why   # the enumeration
git apply -p1 variants/WO-2R3/V17-constructor-body-escape.patch
git apply -p1 variants/WO-2R3/V35-v17-companion-probe.patch
python3 -B tools/register/check_judgement_path_doors.py --root .        # STILL exit 0 — V17 removes
python3 -B tools/register/check_constructor_field_establishment.py --root .   # STILL exit 0 — a BODY,
PYTHONPATH=src python3 -B probe_v17_constructor_body_escape.py          # and NEITHER check reads
                                                                        # bodies. THE REFUSAL IS AT
                                                                        # RUNTIME: expect
                                                                        # FieldNotEstablished.
git apply -p1 variants/WO-2R3/V40-v17-violated-arm-establishes-removed.patch
PYTHONPATH=src python3 -B probe_v17_constructor_body_escape.py          # expect ESCAPED

# 5  P7 AT THE CONSTRUCTOR — the one that decides whether increment 5 is a class closure
git apply -p1 variants/WO-2R3/V39-new-field-on-a-governed-type.patch
python3 -B tools/register/check_constructor_field_establishment.py --root .   # expect exit 1
PYTHONPATH=src python3 -B probe_v39_new_field_on_a_governed_type.py     # expect UndeclaredField
PYTHONPATH=src python3 -B -m pytest tests -q                            # expect 57 failed

# 6  THE PO-DECISIONS-0010 RULING 1 WIDENING — AND IT IS THE ONE WHERE A GREEN RUN PROVES
#    NOTHING, SO DO NOT READ THE TABLE, RUN BOTH ARMS. Two SEPARATE pristine extractions;
#    the SAME single patch in each; the arms differ only in the instrument's revision.
git archive 46adf33 | tar -x -C /tmp/arm-old && cd /tmp/arm-old
git apply -p1 variants/WO-2R3/V43-fielded-judgement-path-type-with-no-establishment.patch
python3 -B tools/register/check_constructor_field_establishment.py --root .   # expect exit 0,
                                                        # "ADJACENT ... engine/verdict.py:40
                                                        # Verdict [RULE A] fields=['score']"
git archive c18aeb4 | tar -x -C /tmp/arm-new && cd /tmp/arm-new
git apply -p1 variants/WO-2R3/V43-fielded-judgement-path-type-with-no-establishment.patch
python3 -B tools/register/check_constructor_field_establishment.py --root .   # expect exit 1,
                                                        # VIOLATION naming Verdict
```

**AND THE FIFTH THING, WHICH NOBODY NAMED AND WHICH THIS SEAT IS HANDING YOU ANYWAY.**
`tools/sweep/delegated_judgement_sweep.py --root . --list` **EXITS 1** at this head — 514
sites, **11 violations**, every one of them `crash_detector.admission`, the module WO-2R3
increment 2 created and did not disposition. It has been failing since `995ec3e` and no record
said so until increment 4 (`CD-ENG-WO2R3-F15`). It is not a declared register command, so no
gate caught it. Start there if you want the shortest path to something genuinely unanswered.

**WHERE THIS SEAT WOULD ATTACK ITS OWN WORK IF IT WERE YOU**, ranked, and with no defence
offered for any of them:
1. `crash_detector.admission`'s eleven undeclared judgement sites (above). Unanswered, not declared.
2. **DECLARED LIMIT 6 route (a2)** — `V33`. The introspection surface LIES afterwards
   (`CD-ENG-WO2R3-F13`): `declared_admissions` still reports the original declaration.
3. **DECLARED LIMIT 5** — `V19`. §D.1's own rule is NOT held at the three §B.3 doors, and the
   carrier is BODY-LEVEL and says so.
4. **The rename test on `missing_adapter_members`** — five spelled names at the softest boundary.
5. **`subjects >= 24`** — a FLOOR that passes at 27 and would pass at 270. It is why CD-PL-F82
   went unnoticed for a boundary. Raising it was NOT authorised and this seat left it alone.

**ADDED AT INCREMENT 5, AND THESE ARE THE ONES THIS SEAT WOULD HIT FIRST NOW:**
6. ~~**THE ADJACENT SET** (`CD-ENG-WO2R3-F17`). A frozen public judgement-path type with NO
   `__post_init__` is OUTSIDE the class the Product Owner ruled — its establishment is ABSENT, not
   body-borne — so the increment-5 check names it and does not fail. Write one and see.
   **NOT PROVED TO BE CARRIED ANYWHERE.**~~
   **SUPERSEDED, AND THE STRIKETHROUGH IS THE POINT — THIS SEAT DID NOT DELETE ITS OWN DECLARED
   HOLE, IT WAS RULED SHUT OVER ITS HEAD.** `CD-ENG-WO2R3-F17` went up because widening a ruled
   class is a scope decision and not a seat's to take; the Product Owner ruled the class
   **BODY-BORNE OR ABSENT** at `PO-DECISIONS-0010` ruling 1. **WRITE ONE AND SEE STILL APPLIES —
   `V43` IS "ONE", WRITTEN, AND IT NOW EXITS 1.** What remains is residue (i) of the check's
   DECLARED LIMIT 1: a ZERO-FIELD member still satisfies vacuously and carries no boundary of any
   kind. **AND THE ATTACK THIS SEAT WOULD MAKE ON ITS OWN WIDENING:** it altered NO verdict on the
   real tree, so nothing but `V43` distinguishes it from a reworded docstring — run both arms
   yourself rather than reading the table, and then attack the widened definition itself, which the
   Product Owner explicitly left open to you.
7. **CROSS-FIELD INVARIANTS** (`CD-ENG-WO2R3-F18`, `V36`). §C.5's invariants 2 and 3 and
   `ConfigSnapshot`'s one-spec-per-dial cannot be derived from a declared field list and REMAIN
   BODY-BORNE. V36 deletes one and the snapshot is **ACCEPTED**.
8. **A `@dataclass` SUBCLASS** (`CD-ENG-WO2R3-F19`, `V38`). It REGENERATES `__init__` and overrides
   the wrapped one, so **not one** field is established — inherited or added. This seat wrote the
   limit claiming the opposite and the measurement refuted it.
9. **THE CLOSURE CELL** (`V37` ARM 4). The registry rewrite is NOT a route (ARM 3, measured, still
   refused); the `compiled` dict in `__init__.__closure__` IS. `V33`'s move one level down.
10. **THE ORDERING COST.** The boundary establishes AFTER the generated `__init__`, so while a
   `__post_init__` CANONICALISES (`own_str`, `ensure_utc`, `dict(...)`, `tuple(...)`) the boundary
   is invisible for that field and the BODY is what refuses. `V42` exists because of it. Anyone
   reading an exit code alone will credit the wrong layer — `CD-ENG-WO2R3-F12`, again.

---

## How to run any row

```
git archive <SHA> | tar -x -C /tmp/cd-v && cd /tmp/cd-v
git apply -p1 variants/WO-2R3/<patch>
<the command in the row>
```

`<SHA>` is `9e1aba016f812e55c1dd59feab53fdbbcc2e871a` for **V16–V25** (WO-2R3 increment 2),
the increment-3 lane head for **V26–V32**, and `a622687ba6a3d3ab4b9f889fc412b3ce3c123226` (the
increment-4 head) for **V33–V34**. Every row states which SHA its numbers were
measured at, because a number measured at one SHA and quoted at another is the thing
CD-RULE-009 exists to stop. **THE V16–V19 ROWS CARRIED `38 assertions` UNTIL INCREMENT 4 AND
NOW CARRY THE RE-MEASURED `54`** — the same defect class as `CD-PL-F82`, found in this file,
corrected by RE-RUNNING each variant rather than by copying 54 from elsewhere.

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
| **V16** | `V16-new-package-undecorated-door.patch` | DECLARED LIMIT 2 of the static check: RULE 1's package list is a VOCABULARY. Adds `src/crash_detector/judging/decide.py`, public, undecorated, unannotated. | check exit **0**, `PASS — 54 assertions, 0 violations` (re-measured at increment 4 on a pristine extraction; this row read **38**, which was the increment-2 figure). **THE LIMIT IS REAL.** | `python3 -B tools/register/check_judgement_path_doors.py --root .` |
| **V17** | `V17-constructor-body-escape.patch` | DECLARED LIMIT 1: constructors are not subjects. Deletes the `type(spec) is not DialSpec` loop from `ConfigSnapshot.__post_init__`. | check exit **0**, `PASS — 54 assertions` (re-measured at increment 4; this row read **38**); whole suite **1519 passed** with it applied. **THE LIMIT IS REAL.** | `python3 -B tools/register/check_judgement_path_doors.py --root .` |
| **V18** | `V18-counterfeit-admits.patch` | DECLARED LIMIT 4: `admits` is recognised by its NAME in the source. A do-nothing `admits` in `own_terms.py`, imported by `serving/witness_resolver.py`. | check exit **0**, `PASS — 54 assertions` (re-measured at increment 4; this row read **38**); the duck row RENDERS `WITNESS AGREES`; **and the runtime catches it: 3 failed, 1516 passed**. The named carrier, measured. | `python3 -B tools/register/check_judgement_path_doors.py --root .` then `PYTHONPATH=src python3 -B -m pytest tests -q` |
| **V19** | `V19-b3-door-body-rewrite.patch` | DECLARED LIMIT 5 of `admission.py`: the six `ESTABLISHED_HERE` uses on §B.3's doors are a LIMIT, not a closure. Deletes the exact-type refusal from `derived_within_one_dial`'s body, decorator untouched. | check exit **0**, `PASS — 54 assertions` (re-measured at increment 4; this row read **38**); whole suite **1 failed, 1518 passed**. §D.1's rule is NOT held at that door and the patch shows why. | `python3 -B tools/register/check_judgement_path_doors.py --root .` |
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

## The rows added at INCREMENT 4 — the two routes through DECLARED LIMIT 6 that the record named but never wrote down

Measured at the increment-4 head, `a622687ba6a3d3ab4b9f889fc412b3ce3c123226`, each in a separate
pristine extraction, run and discarded. **NEITHER IS A GUARD AND NEITHER PROVOKED A CODE
CHANGE.** They exist because DECLARED LIMIT 6's *wording* covered them and its *named example*
did not, three times running (`CD-PL-F80`, `CD-PL-F83`, ruled `CD-D-111` / `CD-D-121`).

| id | patch | PROPOSITION violated | expected failure signature | command |
|---|---|---|---|---|
| **V33** | `V33-closure-declaration-rewrite.patch` | **MINE. DECLARED LIMIT 6, ROUTE (a2).** Not "reach the wrapped function" — **rewrite the door's own LIVE DECLARATION**, so the DECORATED door stops refusing at its own front entrance. `resolve_panel.__closure__[0]` IS the `compiled` dict the door consults on every call. | CONTROL: `REFUSED: NotAdmitted: resolve_panel: row=DuckRow is not admitted; this door requires exactly PanelRow or None`. ARM, the SAME front-door call: **`ESCAPED -> Agrees; RENDERS: WITNESS AGREES`**. AFTERWARDS: `is_admitting_door` **True**, `declared_admissions` still `['now_utc','row','staleness_window_seconds']`, `__admission_faults__` still `()` — **the introspection surface does not show it** (`CD-ENG-WO2R3-F13`). | `PYTHONPATH=src python3 -B probe_v33_closure_declaration_rewrite.py` |
| **V34** | `V34-establishing-function-rebound.patch` | **THE PROJECT LEAD'S ROUTE (`CD-PL-F83`), REPLICATED BY THIS SEAT AND NOT RELAYED. DECLARED LIMIT 6, ROUTE (c).** Rebind the ESTABLISHING FUNCTION in the module that calls it. It attacks the establishment layer, not the door. | CONTROL: `AttemptRecord.requested_utc recorded: ['2026-08-22T12:00:00.000010+00:00', ...]`. ARM after `crash_detector.collectors.runner.ensure_utc = lambda value: <1999-01-01Z>`: `['1999-01-01T00:00:00.000007+00:00', ...]`. **THE DOOR IS SATISFIED IN BOTH ARMS** — `started_utc` is an exact `datetime` either way. | `PYTHONPATH=src python3 -B probe_v34_establishing_function_rebound.py` |

## The increment-4 rows, and why each is a DIFFERENT ROUTE

**V33 is a different route from V24 arm 3, and the difference is the whole reason it exists.**
V24 arm 3 reaches into `__closure__` and calls **a different callable** — the undecorated
function. The door is untouched; a second caller in the same process still meets a working
door. **V33 reaches into the same place and mutates state the door SHARES**, so after it runs
*every* caller in the process is unguarded, including code that never went near a closure and
callers written years later. Same reach, different blast radius. It is in no corpus: WO-2's
`E01`–`E10`, WO-2R's six, WO-2R2's `V01`–`V15`, the three auditors' sets and the Project
Lead's `PL-*` probes contain nothing that attacks a decorator's *live declaration*, because
until WO-2R3 increment 2 there was no such declaration to attack.

*Measured side-note, recorded so nobody mistakes a break for a closure:* **`.clear()` on that
dict does NOT open the door.** The mechanism reads `compiled[name]` for every parameter the
signature names, so an emptied dict raises `KeyError` and the door merely **BREAKS**. It has to
be **REWRITTEN**. A seat that tries the obvious thing, sees a refusal and concludes the reach
is closed will be wrong.

**V34 is not this seat's discovery and the row says so.** The Project Lead found it on a driver
that is in no corpus and raised it as `CD-PL-F83`; this seat wrote its own driver and
**replicated it rather than transcribing the result**, because a limit's declaration citing a
measurement nobody in the citing seat ever ran is the exact defect `CD-RULE-009` exists to
stop. It is a different KIND of route from everything above it: every other variant in every
corpus attacks **what crosses a door**. This one leaves the door perfectly satisfied and
attacks **what the module does with the value afterwards** — specifically, the IDENTITY of the
function that established it, which `admits` does not and cannot establish.

**IT DOES NOT DEFEAT §D.3 PART 1 AND THIS SEAT IS NOT CLAIMING IT DOES.** Part 1's claim is
about what a **CALLER** of `collect` can supply. `clock` and `sleep` are not parameters and the
interpreter refuses to pass them; V34 needs the ability to execute code inside the package,
which is the universal limit every in-process guard on this project lives inside.

## APPLY CHECK, RE-RUN AT INCREMENT 4

Against a pristine extraction of `a622687ba6a3d3ab4b9f889fc412b3ce3c123226`, command
`for p in variants/WO-2R3/*.patch; do git apply --check -p1 "$p"; done`:
**19 of 19 APPLY** (V16–V25, V26–V32, V33–V34).

**THE PRIOR CORPORA, MEASURED AT THE SAME HEAD, BECAUSE "NO REGRESSION" IS A CLAIM ABOUT
PATCHES THAT CAN STILL BE APPLIED:** `variants/WO-2R2/` **14 of 14 apply**.
`variants/WO-2R/` **67 of 70 apply**, and **THREE DO NOT** — raised as `CD-ENG-WO2R3-F16`
(LOW) rather than left for the auditor to trip over:

```
variants/WO-2R/CD-ASR-F02-F03/E04-module-level-constant.patch
variants/WO-2R/CD-ASR-F02-F03/V03-dynamic-constructor-on-the-absence-branch.patch
variants/WO-2R/CD-ASR-F02-F03/V06-magnitude-from-configuration-not-a-literal.patch
```

BISECTED, one pristine extraction per SHA: **all three apply at `f30e63c` and none applies at
`7b00ce9`** — they stopped at **WO-2R3 increment 1**, not at increment 4, and all three patch
the region of `_evaluate_dial`'s absence branch that §C rewrote. **CONSEQUENCE, STATED:** the
regression floor over the WO-2R corpus is measurable at 67 of 70 at this head, and no seat
should read "the exclusion set does not regress" as covering those three. They were NOT updated
here: `CD-D-033`'s conservation rule is about the ELEVEN DECLARED PLANTS under `plants/`, and
extending it to the auditors' variant corpus is a scope decision for the Project Lead and not
this seat's to take.

## What is NOT here

The **violated arms of P1–P4 and P8** are increment 1's and are not restated. The **eleven
declared plants** under `plants/` are a different artefact with a different rule (`CD-D-033`)
and are not variants.

**THE THREE PLANTS THIS SECTION USED TO NAME AS NOT APPLYING NOW APPLY AND NOW CONTRAST**, and
what this section said about them at increment 3 is superseded rather than deleted. It read:
*"THREE of those eleven no longer apply … Reported to the Project Lead; not deleted, not
silently updated, and owed at increment 4."* That debt is discharged at increment 4:
`CD-RT-001-ABSENCE-RENDERS-UNKNOWN`, `CD-RT-001-AST-NO-NUMERIC-DEFAULT` and
`CD-RT-003-ENGINE-NO-WITNESS-REACH` were regenerated against the new structure, violating the
same propositions. **ALL ELEVEN APPLY AND TEN OF ELEVEN CONTRAST** at the lane head, each
measured in one pristine extraction per arm under the command `required-tests.yaml` declares.
The eleventh, `CD-RT-003-GRANT-MATRIX-LIVE`, exits **3 PRECONDITION_NOT_MET on BOTH arms** for
want of a live PostgreSQL — **that is not a contrast and it is not counted as one**. The full
account, including what it would take to measure it properly, is in `plants/MANIFEST.md`.

**ONE OF THE THREE WAS FAILING FOR THE WRONG REASON AND THAT IS THE MOST USEFUL THING ON THIS
PAGE FOR YOU.** A literal regeneration of `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` put a bare
`float` in a score slot, which since WO-2R increment 2 raises **`ScoreOutOfRange` — a CD-AC-002
refusal** — before the CD-AC-001 absence post-condition is ever reached. The declared command
still exits 1, so an exit code alone would have recorded a contrast under the wrong criterion
(`CD-ENG-WO2R3-F12`). **AN EXIT CODE IS NOT A REFUSING LAYER.** Apply that test to every row on
this page, including the ones this seat wrote.


## The rows added at INCREMENT 5 — the CONSTRUCTORS, and the class the Product Owner re-based onto

Measured at tree `3ae0205a5e692a69ad5724c8f8973375eecfa3ca`, **which is the tree of commit
`66d1d6a`**, each in a SEPARATE PRISTINE EXTRACTION (`git archive <tree> | tar -x -C <tmpdir>`), run
and discarded. Every patch was generated with `git diff` and never by hand (`CD-ENG-WO2R-F13`).

**V35, V40 and V41 are ARMS, NOT ROUTES**, and are labelled as such: they add a probe or remove the
mechanism so that another row has a contrast. **V36, V37, V38, V39 and V42 are MINE.**

| id | patch | PROPOSITION violated | observed | command |
|---|---|---|---|---|
| **V35** | `V35-v17-companion-probe.patch` | **AN ARM, NOT A ROUTE.** Adds `probe_v17_constructor_body_escape.py` and nothing else. V17 DELETES a guard; it does not walk through the hole. This walks through it. | — (it is the probe the two V17 rows below run) | `PYTHONPATH=src python3 -B probe_v17_constructor_body_escape.py` |
| **V17 + V35** | `V17-constructor-body-escape.patch` then `V35` | **V17's OWN PROPOSITION, BASELINE ARM.** `ConfigSnapshot.dial_specs` establishes its elements in `__post_init__`; delete that loop and a duck `DialSpec` should reach the snapshot. | **REFUSED.** `crash_detector.establishment.FieldNotEstablished: ConfigSnapshot.dial_specs[0]=DuckDialSpec is not admitted; every element must be exactly DialSpec.` **THE LAYER, FROM THE FAILURE TEXT: the CLASS BOUNDARY** — not `engine.config`'s body, which V17 deleted, and not a door. **AND: with V17 applied BOTH static checks still exit 0** (doors `PASS — 54 assertions`; constructors `PASS — 96 assertions`), because V17 removes a BODY and neither check reads bodies. | `PYTHONPATH=src python3 -B probe_v17_constructor_body_escape.py` |
| **V17 + V35 + V40** | `V40-v17-violated-arm-establishes-removed.patch` | **V17's VIOLATED ARM.** The same, with `@establishes(...)` removed from `ConfigSnapshot`. | **ESCAPED.** `ConfigSnapshot CONSTRUCTED with duck dial_specs`; `stored element types: ['DuckDialSpec','DuckDialSpec']`; `spec_for('equity_crash') -> DuckDialSpec` | `PYTHONPATH=src python3 -B probe_v17_constructor_body_escape.py` |
| **V39** | `V39-new-field-on-a-governed-type.patch` | **MINE. P7 AT THE CONSTRUCTOR, BASELINE ARM.** `tolerate_stale: bool = False` added to the REAL `PanelRow` and NOT declared to `@establishes`. | check exit **1**, `FIELD_NOT_DECLARED_TO_ESTABLISHES`; an ORDINARY construction that never mentions the field raises `establishment.UndeclaredField: PanelRow is a FAULTED type and every construction of it is refused`; suite **57 failed, 1480 passed** (from 1537 passed) | `python3 -B tools/register/check_constructor_field_establishment.py --root .` · `PYTHONPATH=src python3 -B probe_v39_new_field_on_a_governed_type.py` · `PYTHONPATH=src python3 -B -m pytest tests -q` |
| **V39 + V41** | `V41-v39-violated-arm-establishes-removed.patch` | **P7 AT THE CONSTRUCTOR, VIOLATED ARM.** The same added field with `@establishes` removed from `PanelRow`. | **`declaration faults on PanelRow: 0`**; `ADMITTED -> the new field arrived UNGUARDED` | `PYTHONPATH=src python3 -B probe_v39_new_field_on_a_governed_type.py` |
| **V42** | `V42-panelrow-canonicalisation-body-deleted.patch` | **MINE. THE SAME MOVE AS V17 ON A DIFFERENT TYPE, A DIFFERENT FIELD AND A DIFFERENT ESTABLISHING FUNCTION.** Deletes `own_str(self.state)` from `PanelRow.__post_init__` and offers a `str` SUBCLASS whose `__eq__` answers `True`. It exists because a closure that answered only V17 would be the instance game with a decorator on it. | **BASELINE: REFUSED.** `establishment.FieldNotEstablished: PanelRow.state=DuckStr is not admitted; this door requires exactly str.` | `PYTHONPATH=src python3 -B probe_v42_canonicalisation_deleted.py` |
| **V42 + V41** | as above | **V42's VIOLATED ARM.** | **ESCAPED.** `stored state type: DuckStr`; `stored state value: 'UNAVAILABLE'`; **`row.state == 'AGREES' answers: True`** — `ASR3-F04`'s sentence, reached through a constructor. **NOT OVERCLAIMED: `resolve_panel` still returned `Unavailable`** in this arm, so the escape reaches the VALUE TYPE and the resolver's own re-establishment still held. | `PYTHONPATH=src python3 -B probe_v42_canonicalisation_deleted.py` |
| **V36** | `V36-cross-field-invariant-body-rewrite.patch` | **MINE. MECHANISM DECLARED LIMIT 1's EXECUTABLE EXAMPLE, AND IT IS A POSITIVE ONE — AN OBJECT THAT IS ACCEPTED.** Deletes §C.5's "exactly one spec per dial" check and builds a snapshot with TWO equity specs and NO monetary spec. | **ACCEPTED.** `element types: ['DialSpec','DialSpec'] (all exactly DialSpec)`; `dial_ids: ['equity_crash','equity_crash']`. The boundary is fully satisfied and the object is wrong. **A CROSS-FIELD INVARIANT CANNOT BE DERIVED FROM A DECLARED FIELD LIST.** | `PYTHONPATH=src python3 -B probe_v36_cross_field_invariant.py` |
| **V37** | `V37-establishes-registry-rewrite.patch` | **MINE. MECHANISM DECLARED LIMIT 3.** The interpreter reach at this boundary, four arms, on `ScoreComputation` — chosen because its body establishes NO element type of `contributions`, so **only the boundary can refuse** and the measurement cannot be credited to the wrong layer. | ARM 1 front door **REFUSED**; ARM 2 `__init__.__wrapped__` **REFUSED** (`AttributeError`, deleted); ARM 3 rewrite `_DECLARATIONS` **STILL REFUSED** — the registry is a REPORT, not the live declaration, so it makes the introspection surface LIE in the SAFE direction (`CD-ENG-WO2R3-F13` INVERTED); **ARM 4 rewrite the `compiled` dict in `__init__.__closure__` -> ESCAPED**, a bare `object` stored in `contributions`. **ARM 3 WAS WRITTEN EXPECTING AN ESCAPE AND MEASURED A REFUSAL, and the limit was corrected to the measurement.** | `PYTHONPATH=src python3 -B probe_v37_establishes_registry_rewrite.py` |
| **V43 — OLD ARM, at `46adf33`** | `V43-fielded-judgement-path-type-with-no-establishment.patch` | **MINE, AND IT IS THE ONLY PROOF THE `PO-DECISIONS-0010` RULING 1 WIDENING HAS.** It is CHECK LIMIT 1's own executable example landed as a patch, verbatim: a `@dataclass(frozen=True)` `class Verdict: score: float` under `src/crash_detector/engine/`, with no `__post_init__`, no `__init__` and no `@establishes`. **A SINGLE NEW FILE — no guard removed, nothing reached into. It simply declares a type.** | **EXIT 0**, `PASS — 96 assertions, 0 violations`, and `  ADJACENT (not required, and this is a real hole): engine/verdict.py:40 Verdict [RULE A] fields=['score']`. **ADJACENT SET 2.** THE HOLE, MEASURED FROM THE OLD SIDE AND NOT ASSERTED FROM THE NEW ONE | `git archive 46adf33 \| tar -x -C /tmp/arm-old`, `git apply -p1 <this patch>`, `python3 -B tools/register/check_constructor_field_establishment.py --root .` |
| **V43 — NEW ARM, at `c18aeb4`** | the same single patch, unchanged | **THE SAME PATCH ON THE WIDENED INSTRUMENT.** The arms differ ONLY in which revision of the instrument reads the identical file. | **EXIT 1**, `FAIL — 1 violation(s)`: `VIOLATION src/crash_detector/engine/verdict.py:40 — Verdict is a PUBLIC FROZEN type ON A JUDGEMENT PATH declaring 1 field(s) ['score'], and it carries no @establishes(...). Its establishment is ABSENT ...`. **POPULATION 34, FIELDED 33, DECLARED TO @establishes 32.** The type is IN, and it is NAMED | same, from `git archive c18aeb4` |
| **V38** | `V38-subclass-adds-an-unestablished-field.patch` | **MINE. MECHANISM DECLARED LIMIT 4.** No guard removed, no privileged code, nothing reached into — it simply DECLARES A NEW TYPE. | (a) a `@dataclass` subclass **REGENERATES `__init__`** and overrides the wrapped one, so **NOT ONE field is established**: `ScoreComputationPlus(magnitude=0.5, contributions=(object(),))` **ACCEPTED**; (b) the added field accepted a `lambda`; (c) a PLAIN, non-dataclass subclass DOES inherit the wrapped `__init__` and is **REFUSED**; (d) the DECLARED CARRIER, MEASURED: `resolve_panel` refuses a `PanelRow` subclass with `admission.NotAdmitted: row=PanelRowPlus is not admitted; this door requires exactly PanelRow or None` | `PYTHONPATH=src python3 -B probe_v38_subclass_adds_a_field.py` |

## The increment-5 rows that are MINE, and why each is a DIFFERENT ROUTE

**Every corpus before this increment attacks a CALLABLE.** WO-2's `E01`–`E10`, WO-2R's six,
WO-2R2's `V01`–`V15`, the three auditors' sets and the Project Lead's `PL-*` probes all enter through
a parameter, a door, a decorator's attribute surface or the gap between admission and use. `V16`–`V34`
are the same: they are about doors. **A CONSTRUCTOR IS A DIFFERENT SUBJECT**, and it is a different
subject because the Product Owner ruled it one — *"`__post_init__` IS A BODY"* — after this seat
raised `CD-ENG-WO2R3-F05` against its own increment-2 work.

**V39 is the row that decides whether this is a class closure or thirty-two type checks.** It is P7
one level down. P7 asks *does a NEW ARGUMENT on a door arrive refused?*; V39 asks *does a NEW FIELD on
a governed type arrive refused?* Both arms are measured and the answer is yes at the baseline and no
with the decorator removed. Nothing in any corpus adds a field to a value type, because until this
increment there was no per-type declaration for a new field to fail to be in.

**V42 exists because V17 alone would not have proved a class.** V17 attacks ONE type through ONE
field with ONE establishing function. V42 makes the identical move — delete a body-borne
establishment — on `PanelRow.state`, whose establishing function is `own_str` and not a `type(...) is
not` comparison, and whose escape is `ASR3-F04`'s published sentence rather than a duck spec. Same
boundary, different type, different field, different function, same refusal.

**V36 is a different KIND of artefact and is labelled as one**, in the shape `V26` set at increment 3:
it removes a guard and demonstrates that the new mechanism DOES NOT COVER what it removed. A limit
stated only in prose is a limit an auditor has to take on trust.

**V37 is a different route from V33, and the difference is which dict is live.** V33 rewrites the
`compiled` dict a DOOR consults. V37 first rewrites the module REGISTRY — and MEASURES A REFUSAL,
because at this boundary the registry is not what is consulted — and only then reaches the closure
cell. The negative half is the more useful half: it tells the next seat that the obvious handle is
not the handle.

**V38 is the only route in any corpus that removes nothing, reaches into nothing and executes no
privileged code.** It writes `class X(GovernedType)`. That is all.

## APPLY CHECK, RE-RUN AT INCREMENT 5

Against a pristine extraction of tree `3ae0205a5e692a69ad5724c8f8973375eecfa3ca` (commit `66d1d6a`),
command `for p in variants/WO-2R3/*.patch; do git apply --check -p1 "$p"; done`:
**27 of 27 APPLY** (V16–V42).

**THE PRIOR CORPORA, MEASURED AT THE SAME TREE:** `variants/WO-2R2/` **14 of 14 apply**.
`variants/WO-2R/` **66 of 70 apply, DOWN FROM 67 OF 70 AT INCREMENT 4, AND THE FOURTH ONE IS THIS
SEAT'S DOING:**

```
variants/WO-2R/CD-ASR-F02-F03/E04-module-level-constant.patch                    (pre-existing)
variants/WO-2R/CD-ASR-F02-F03/V03-dynamic-constructor-on-the-absence-branch.patch (pre-existing)
variants/WO-2R/CD-ASR-F02-F03/V06-magnitude-from-configuration-not-a-literal.patch (pre-existing)
variants/WO-2R/CD-ASR-F02-F03/V05-decorator-installs-the-member.patch            <- NEW AT INCREMENT 5
```

**BISECTED, one pristine extraction per SHA:** `V05` APPLIES at `4ac159e` and does NOT apply at this
tree. **CAUSE, NAMED:** V05 inserts `@_with_neutral_measure` immediately above
`@dataclass(frozen=True)` / `class Unknown`, and increment 5 inserts `@establishes(...)` between
them, so the hunk's trailing context no longer matches. **ITS PROPOSITION IS UNTOUCHED AND STILL
REACHABLE** — a decorator installing a numeric member on a sealed Reading constructor — and only the
insertion point moved. **NOT UPDATED HERE, and that is a scope call and not laziness:** `CD-D-033`'s
conservation rule is about the ELEVEN DECLARED PLANTS under `plants/`, and the increment-4 boundary
ruled in terms (`CD-ENG-WO2R3-F16`) that extending it to the auditors' corpus is the Project Lead's
decision and not this seat's. **RAISED AS `CD-ENG-WO2R3-F20` (LOW).**

---

## THE EXECUTABLE PROBE ROWS — WRITTEN DOWN FOR THE FIRST TIME (`CD-PL-F97`)

**THIS SECTION EXISTS BECAUSE IT DID NOT.** Six probes landed at increment 6 with zero rows here.
Every row states what the probe ASKS, not what it concludes — a manifest that carries conclusions
is a summary, and a summary is the thing this project keeps finding wrong.

| probe | asks | run it |
|---|---|---|
| `P-A-escape1-stored-is-not-validated.py` | is the stored payload the validated payload? | `PYTHONPATH=src python3 -B variants/WO-2R3/P-A-escape1-stored-is-not-validated.py` |
| `P-B-how-deep-can-a-type-hide.py` | how deep can a `ClassDef` nest before the constructor check stops seeing it? | `PYTHONPATH=src python3 -B variants/WO-2R3/P-B-how-deep-can-a-type-hide.py` |
| `P-C-an-aliased-exemption.py` | does an aliased `ESTABLISHED_HERE` still count as a use? | `PYTHONPATH=src python3 -B variants/WO-2R3/P-C-an-aliased-exemption.py` |
| `P-D-empty-is-runtime-unguarded.py` | is `Empty` establishing at runtime? | `PYTHONPATH=src python3 -B variants/WO-2R3/P-D-empty-is-runtime-unguarded.py` |
| `P-E1-what-is-closed-at-that-door.py` | what is actually closed at the CD-BP-003 door? | `PYTHONPATH=src python3 -B variants/WO-2R3/P-E1-what-is-closed-at-that-door.py` |
| `P-E23-what-the-in-package-execution-sentence-gets-wrong.py` | how many lines of package code does the route the sentence calls a precondition actually need? | `PYTHONPATH=src python3 -B variants/WO-2R3/P-E23-what-the-in-package-execution-sentence-gets-wrong.py` |
| **`P-F-can-anything-reach-the-net-without-a-door.py`** | **NEW AT INCREMENT 7.** Both halves of `PO-DECISIONS-0012` ruling 4, separately: can anything in-process reach `_evaluate_dial` without passing an established door, and does the net's post-condition bind everything its open arity admits? **18 arms, each a live call.** | `PYTHONPATH=src python3 -B variants/WO-2R3/P-F-can-anything-reach-the-net-without-a-door.py` |
| **`P-G-can-a-foreign-adapter-reach-the-net.py`** | **NEW AT INCREMENT 7.** The same question asked of the DECLARED-FOREIGN actor rather than of a REPL: can a conforming hostile adapter, arriving through `collect()`, obtain and call the net? The fifth seat wrote *"I did not demonstrate a route to it from `collect`"*; this is that demonstration attempted. | `PYTHONPATH=src python3 -B variants/WO-2R3/P-G-can-a-foreign-adapter-reach-the-net.py` |

| **`P-H-the-reachability-criterion-under-attack.sh`** | **NEW AT INCREMENT 7.** The item-2 reachability criterion under its own two REQUIRED contrasts: does it survive the rename that killed the clause it replaced, and does it still catch the fourth Assurance seat's ESCAPE 4 ARM 4 — including with a PRIVATE-named local, which a name-prefix clause cannot see at all? Ten arms, **each running its own tree's own copy of the instrument and printing its SHA** (CD-PL-F98). | `bash variants/WO-2R3/P-H-the-reachability-criterion-under-attack.sh` |

| **`P-I-the-wrapped-attack-set-re-run.sh`** | **NEW AT INCREMENT 7.** PO-DECISIONS-0013 ruling 2's *"the historic WO-2R `__wrapped__` attack set is re-run at the new head"*, before and after, nine routes READ FROM THE DIRECTORY and not from this manifest (CD-PL-F97): V24 plus every patch in `variants/WO-2R/CD-ASR-F02-F03/`, the corpus the fifth seat's M10 named as depending on the guard this increment changed. | `bash variants/WO-2R3/P-I-the-wrapped-attack-set-re-run.sh` |

| **`P-J-the-admits-door-arity.py`** | **NEW AT INCREMENT 7.** `admits`'s own arity-open `door(*args, **kwargs)`, asked the question PO-DECISIONS-0012 ruling 1 asked of `guarded`: is there anything a caller can pass that reaches the entry point WITHOUT passing through the binding-and-refusal loop? Ten live arms, including the two that BOUND the answer (J0/J, the `__qualname__` route — measured, NOT repaired: T8 Category A is not this increment's). | `PYTHONPATH=src python3 -B variants/WO-2R3/P-J-the-admits-door-arity.py` |

**NEITHER NEW PROBE IS A CARRIER.** Both exit 0 whatever they measure, by design: they are
INSTRUMENTS THAT REPORT, and this project's `CD-RULE-006` says a check reports and a carrier fails.
The carriers for increment 7's propositions are in `tests/`, and where a proposition has no carrier
that is said in the return rather than left to be found.
