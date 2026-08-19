# WO-2R variant plants — MANIFEST

**Dispatch:** `governance/dispatch/CD-DISPATCH-WO2R-ENGINEER.yaml`, increments 1 and 2.
**Written by:** `CD-ENG-WO2R-01` (ENGINEER).

**Nothing in this directory is evidence and nothing in it is assurance.** These are the
adversarial variants the implementing seat wrote against its own closure, with the refusal it
observed. A seat's own runs are IMPLEMENTATION EVIDENCE and do not become assurance by being
thorough (`PBG-SOD-001`, non-waivable). An independent seat, `CD-ASR-WO2-02`, decides.

## What this directory is FOR, and it is not what it looks like

**It is the next auditor's EXCLUSION SET.** Product Owner Ruling 4: the auditor must generate
FRESH variants, because "a guard that refuses exactly these and nothing else has been fitted to
a list". Everything written down here is, from the moment it is committed, part of the KNOWN set
and **proves nothing about the class**. Read it so you can avoid duplicating it, and then attack
the same propositions by routes that are not here. An omission in this file corrupts the next
audit, so where a route was tried and NOT refused it says so in the same words as the ones that
were.

## What is deliberately NOT here

**No wrapper, no runner, no harness, and there may not be one** (`PBG-ASSURE-001`). Every row
carries the literal command lines. Nothing in this directory is executable — the patches are
data. An auditor who verifies through a script the project wrote has verified the script.

## The procedure, once per variant

```bash
SUBJECT=$(mktemp -d /tmp/cd-variant-XXXXXX)
git -C <this repository> archive <the SHA under audit> | tar -x -C "$SUBJECT"
cd "$SUBJECT"
<the clean-arm command>                                    # expect: clean
git apply --check -p1 <repo>/variants/WO-2R/<finding>/<VID>.patch
git apply         -p1 <repo>/variants/WO-2R/<finding>/<VID>.patch
<the probe command for this row>                           # expect: the refusal in this row
rm -rf "$SUBJECT"
```

**A separate pristine extraction per variant**, so no variant contaminates another. **Never the
Engineer's worktree and never a `git worktree`.** `python3 -B` everywhere, so no `__pycache__`
is written into a tree under audit — that is mutation by EFFECT, not by label (`PBG-RT-001`).

---
---

# CD-ASR-F02 (HIGH) and CD-ASR-F03 (MEDIUM) — criterion CD-AC-001

**Directory:** `variants/WO-2R/CD-ASR-F02-F03/`

**THE CLASS these attack:** *ABSENCE YIELDING A NUMBER.* Not the name `magnitude`, not "a
property", not "a module-level constant" — any route by which a `Reading` representing absence
produces, exposes or is coerced into a numeric value, and any route by which a code path that
did not get its inputs constructs a reading that carries one.

**THE STRUCTURE they are aimed at**, so a reader can judge whether the routes below are a fair
spread over it rather than a spread over the ones that were easy:

* **layer 1, definition time** — `DECLARED_MEMBER_SURFACE` in
  `src/crash_detector/dials/reading.py`, asserted by SET EQUALITY while the module is imported;
* **layer 2, instance time** — `__slots__` on all three constructors;
* **layer 3, subclass time** — `SealedReadingType` refuses subclassing; `fold` and `is_value`
  dispatch on exact type identity;
* **layer 4, consumption time** — `fold`, `is_value` and `DialSet` re-verify the surface of the
  reading's class on every call, and `tests/test_reading.py` imports every module in the
  application package and re-verifies the three surfaces afterwards;
* **layer 5, the absence post-condition** — `refuse_a_number_without_its_inputs` in
  `src/crash_detector/engine/evaluate.py`, wrapped around the per-dial evaluator, re-deriving
  from that function's own arguments whether the dial got its required inputs;
* **layer 6, RULE F** in `tools/register/check_no_numeric_default.py`, which enumerates the ONE
  permitted provenance of a dial magnitude and reports every other, including unrecognised ones.

**COMMANDS USED BELOW**, written out once and referred to by name:

| name | command |
|---|---|
| `AST` | `python3 tools/register/check_no_numeric_default.py --root .` |
| `ARM` | `PYTHONPATH=src python3 -m pytest tests/test_reading.py tests/test_evaluate.py -q` |
| `IMPORT` | `PYTHONPATH=src python3 -c "import crash_detector.dials.reading"` |
| `EVALUATE-MISSING` | a five-line probe that builds a `ConfigSnapshot` declaring one REQUIRED source with a contribution model, registers that source, and calls `evaluate([], config, now)` so the dial's required input is absent. Written out in full at the bottom of this file. |

`AST` and `ARM` are the two DECLARED register commands for CD-AC-001, verbatim from
`required-tests.yaml`. `IMPORT` and `EVALUATE-MISSING` are probes, not register commands: the
Product Owner's word for F02 is "structurally incapable", which is a RUNTIME property, and a
static checker exiting non-zero is not proof of one.

---

## KNOWN-SET RE-RUNS (from `governance/assurance/WO-2/ESCAPED-VARIANTS-KNOWN-SET.md`)

These two are the minimum obligation, not the proof. They were reproduced against the closure
and refused.

### E03 — `E03-unknown-numeric-property.patch`

| | |
|---|---|
| **finding** | CD-ASR-F02 (HIGH) |
| **proposition attacked** | Absence never renders as a number. |
| **route** | A plain `@property magnitude -> 0.0` in the `Unknown` class body. No dunder, no annotation, no default. Transcribed from the auditor's own entry. |
| **why it escaped at the gate** | `tests/test_reading.py` asserted only that no name from `ARITHMETIC_DUNDERS` appeared in `vars(Unknown)`. A blacklist cannot see a member nobody listed. |
| **observed refusal** | `IMPORT` → **exit 1**, `crash_detector.dials.reading.ReadingSurfaceViolated: Unknown carries undeclared member(s) ['magnitude']. The surface is declared and asserted by equality, so this is a breach whether or not the member is numeric (CD-ASR-F02).` The dial path cannot be imported at all. `ARM` → **exit 2**, both test modules ERROR during collection with the same exception. |
| **`AST` under this variant** | **exit 0**, and that is correct and declared: E03 adds no dial magnitude, so RULE F has nothing to say about it. This is the layer split doing what the declared limit says it does — the runtime layer carries F02, the static layer carries the magnitude-provenance half of F03. |

### E04 — `E04-module-level-constant.patch`

| | |
|---|---|
| **finding** | CD-ASR-F03 (MEDIUM) |
| **proposition attacked** | No route exists on the dial path by which an absent input becomes a number. |
| **route** | `QUIET_MAGNITUDE = 0.0` at module level in `evaluate.py`; the `missing_required` branch returns `Value(value=<ScoreType>(score=QUIET_MAGNITUDE, ...))`. |
| **why it escaped at the gate** | No `float \| None`, no `.get(k, 0)`, no `or 0`, no bare `except` — none of the four routes the check enumerated. The check enumerated spellings. |
| **observed refusal, static** | `AST` → **exit 1**, `FAIL — 1 violation(s)`, `F: unrecognised magnitude provenance` at the construction, naming the trail: *"`QUIET_MAGNITUDE` is bound in an enclosing scope to something that is not a declared magnitude source: the magnitude IS the literal `0.0`."* |
| **observed refusal, runtime** | `EVALUATE-MISSING` → **exit 1**, `crash_detector.dials.reading.AbsenceYieldedAValue: dial 'equity_crash' produced Value, which carries a value, but its required inputs were not all present: it declares ['src.a'], a contribution model is declared, and the usable inputs are [].` |
| **also** | `ARM` → **exit 1**, `9 failed, 80 passed`. |

---

## NEW VARIANTS — devised by `CD-ENG-WO2R-01`, six of them

Each attacks the same class by a route that is **not** in the known set. The column that matters
is *why it is a different route*, because a variant that is E03 with a different member name
would prove nothing.

### V01 — `V01-classvar-not-a-property.patch`

| | |
|---|---|
| **finding** | CD-ASR-F02 |
| **proposition attacked** | Absence's attribute surface is closed. |
| **route** | A bare class attribute in the `Unknown` body: `FALLBACK_MAGNITUDE = 0.0`. Not a descriptor, not a dataclass field, not a dunder, and not named `magnitude`. |
| **why it differs from the known set** | E03 installs a **descriptor** (a `property` object). This installs a plain value on the class, so a guard that inspected `property` objects, or that looked for the name E03 used, sees nothing. It also tests that the surface check is about DECLARATION and not about type: nothing here is callable. |
| **command** | `IMPORT` |
| **observed refusal** | **exit 1**, `ReadingSurfaceViolated: Unknown carries undeclared member(s) ['FALLBACK_MAGNITUDE']. ...` `ARM` → **exit 2** (collection errors). `AST` → exit 0, as declared. |

### V02 — `V02-getattr-catch-all.patch`

| | |
|---|---|
| **finding** | CD-ASR-F02 |
| **proposition attacked** | Absence's attribute surface is closed. |
| **route** | `def __getattr__(self, name) -> float: return 0.0` in the `Unknown` body. |
| **why it differs from the known set** | **It installs no member name at all.** E03 and V01 both add a name a surface check could in principle notice; this adds a catch-all, so `unknown.magnitude`, `unknown.level`, `unknown.anything` all yield `0.0` and no enumeration of member names could ever list them. It is the strongest of this seat's F02 variants and the one an auditor should assume was tried. `__getattr__` is not in `ARITHMETIC_DUNDERS`, so the WO-2 test would not have seen it either. |
| **command** | `IMPORT` |
| **observed refusal** | **exit 1**, `ReadingSurfaceViolated: Unknown carries undeclared member(s) ['__getattr__']. ...` — caught not because the guard understands `__getattr__` but because `__getattr__` is not in the declared set. `ARM` → **exit 2**. |

### V03 — `V03-dynamic-constructor-on-the-absence-branch.patch`

| | |
|---|---|
| **finding** | CD-ASR-F03 |
| **proposition attacked** | A code path that did not get its inputs cannot construct a reading that carries a number. |
| **route** | On the `missing_required` branch, obtain the constructor through the module object — `maker = getattr(sys.modules["crash_detector.dials.reading"], "Value")` — and build the reading with a magnitude from a helper that contains no numeric literal (`float(len(()))`). |
| **why it differs from the known set** | E04 names `Value` directly and puts the number in a module constant. This variant makes **the construction itself invisible to static analysis** and puts the number **behind a call**, so there is no numeric constant to resolve and no recognisable constructor name. It is written deliberately at **boundary 1 of `CD-RT-001-AST-NO-NUMERIC-DEFAULT`'s declared limit**, to test whether that limit was honestly drawn and whether the layer said to carry it actually does. |
| **commands** | `AST`, then `EVALUATE-MISSING` |
| **observed outcome, static** | `AST` → **exit 0**, `PASS — 244 assertions, 0 violations`. **NOT REFUSED by the static layer, exactly as boundary 1 declares.** |
| **observed refusal, runtime** | `EVALUATE-MISSING` → **exit 1**, `AbsenceYieldedAValue: dial 'equity_crash' produced Value, which carries a value, but its required inputs were not all present ...`. The post-condition inspects the returned object's TYPE and never reads the expression that produced it, so how the constructor was obtained is irrelevant to it. `ARM` → **exit 1**, `9 failed, 80 passed`. |
| **why this row matters most** | It is the variant that proves the declared limit is a real division of labour rather than an excuse, and it replaces a property the `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` plant used to demonstrate and no longer does (see `plants/MANIFEST.md`, CD-ENG-WO2R-F01). |

### V04 — `V04-post-import-class-mutation.patch`

| | |
|---|---|
| **finding** | CD-ASR-F02 |
| **proposition attacked** | Absence is structurally incapable of yielding a numeric attribute. |
| **route** | A new module `src/crash_detector/serving/panel_scale.py` which, at import, runs `type.__setattr__(Unknown, "magnitude", property(lambda self: 0.0))`. |
| **why it differs from the known set** | E03 edits the class **body**. This mutates the class **object after import**, from a different module, through the one call that walks past a metaclass's `__setattr__`. CPython offers no way to refuse it, so it is the route this seat expects an auditor to find and it is written down here rather than left to be found. |
| **commands** | `ARM`, then a probe that imports the module and tries `unknown.magnitude`, `fold`, `is_value` and `DialSet` |
| **observed outcome — PARTIALLY REFUSED, AND THIS IS THE DECLARED LIMIT** | The mutation **succeeds**: `Unknown(...).magnitude` is `0.0` for code that reads it directly. Every consumer boundary refuses it: `fold` → `ReadingSurfaceViolated`, `is_value` → `ReadingSurfaceViolated`, `DialSet(...)` → `ReadingSurfaceViolated`, each naming `Unknown carries undeclared member(s) ['magnitude']`. |
| **observed refusal by a DECLARED arm** | `ARM` → **exit 1**, `1 failed, 89 passed`, `FAILED tests/test_reading.py::test_no_application_module_leaves_a_reading_surface_breached`. That test imports every module in the application package and then re-verifies all three surfaces, so it is an assertion about the OUTCOME and not about `type.__setattr__` — a module that breaches a surface is caught however it did it. |
| **what is still open, stated plainly** | A mutation performed by code that is **not in this package** — an operator's script, a plugin, a debugger, an interactive session — is outside any test over this tree. What is closed is that no in-tree module can leave a surface breached, and that a reading of a mutated class is refused wherever it would be used. Do not read a clean `ARM` as proof that a numeric attribute is unattainable by a process that rewrites class objects at runtime. |

### V05 — `V05-decorator-installs-the-member.patch`

| | |
|---|---|
| **finding** | CD-ASR-F02 |
| **proposition attacked** | Absence's attribute surface is closed. |
| **route** | A decorator applied above `@dataclass` — `@_with_neutral_measure` — whose body calls `setattr(cls, "magnitude", property(...))` and returns the class. |
| **why it differs from the known set** | The member appears in **no class body**, so a reader of the class definition sees three fields and a `__post_init__`. It is also the route most likely to arrive innocently, as a shared "give every reading type a uniform surface" helper, and it exercises the ordering question directly: a decorator runs BEFORE the module-bottom seal, so the closure has to catch it by verifying the surface rather than by refusing the assignment. |
| **command** | `IMPORT` |
| **observed refusal** | **exit 1**, `ReadingSurfaceViolated: Unknown carries undeclared member(s) ['magnitude']. ...` raised from `seal_reading_type` at import. `ARM` → **exit 2**. |

### V06 — `V06-magnitude-from-configuration-not-a-literal.patch`

| | |
|---|---|
| **finding** | CD-ASR-F03 |
| **proposition attacked** | No route exists on the dial path by which an absent input becomes a number. |
| **route** | `CARRIED_MAGNITUDE = float(os.environ.get("CD_DIAL_CARRIED_MAGNITUDE", "0"))` at module level; the `missing_required` branch returns `Degraded(value=<ScoreType>(score=CARRIED_MAGNITUDE, ...))`. |
| **why it differs from the known set** | **There is no numeric literal anywhere in the patch.** The default is the STRING `"0"`, so class B (a numeric second argument to a lookup) does not fire, and the module-level name is bound to a `Call` rather than to a number, so the existing module-constant resolution does not see it either. E04's number was a literal in a constant; this number arrives from the environment. It also returns `Degraded` rather than `Value`, which is the more plausible edit — `Degraded` is *supposed* to carry a value — and therefore the one most likely to survive review. |
| **observed refusal, static** | `AST` → **exit 1**, `F: unrecognised magnitude provenance` — *"`CARRIED_MAGNITUDE` is bound in an enclosing scope to something that is not a declared magnitude source: the magnitude comes from `float(os.environ.get('CD_DIAL_CARRIED_MAGNITUDE', '0'))`, and `float` is not a declared source of a dial magnitude. The declared sources are ['compute']."* |
| **observed refusal, runtime** | `EVALUATE-MISSING` → **exit 1**, `AbsenceYieldedAValue: dial 'equity_crash' produced Degraded, which carries a value, but its required inputs were not all present ...`. `ARM` → **exit 1**, `9 failed, 80 passed`. |

---

## Summary of what was refused by what

| variant | route class | static `AST` | declared `ARM` | runtime probe |
|---|---|---|---|---|
| E03 | member in the class body | exit 0 (declared: not its class) | **exit 2**, collection error | `IMPORT` **exit 1** |
| E04 | module-level numeric constant | **exit 1**, rule F | **exit 1** | `EVALUATE-MISSING` **exit 1** |
| V01 | bare classvar | exit 0 (declared) | **exit 2** | `IMPORT` **exit 1** |
| V02 | `__getattr__` catch-all | exit 0 (declared) | **exit 2** | `IMPORT` **exit 1** |
| V03 | dynamic constructor | **exit 0 — declared limit, boundary 1** | **exit 1** | `EVALUATE-MISSING` **exit 1** |
| V04 | post-import class mutation | exit 0 (declared) | **exit 1**, package sweep | consumer boundaries refuse; **direct read is not refused** |
| V05 | decorator | exit 0 (declared) | **exit 2** | `IMPORT` **exit 1** |
| V06 | magnitude from configuration | **exit 1**, rule F | **exit 1** | `EVALUATE-MISSING` **exit 1** |

**Two honest observations about that table.** First, the static arm is silent on five of eight,
and that is the layer split working as declared, not a gap discovered afterwards — CD-AC-001 is
a runtime proposition and the runtime arm is what carries it. Second, **V04 is the only row
whose refusal is partial**, and it is partial in exactly the way `reading.py`'s header, the
register entry and the execution contract all say it is.

---

## `EVALUATE-MISSING`, written out in full

The probe below is data, not a runner: it is printed here so an auditor can retype it, and it is
NOT committed as an executable file (`PBG-ASSURE-001`). It reaches the `missing_required`
branch, which the WO-2 empty-registry state does not — with no source registered, a dial takes
the *no required inputs* branch instead, and a probe that used `empty_config_snapshot` would
report a clean `Unknown` while the planted branch was never executed. This seat made that
mistake first and records it so the next reader does not.

```python
from datetime import datetime, timezone

from crash_detector.dials.dialset import EQUITY_DIAL_ID, MONETARY_DIAL_ID
from crash_detector.engine.config import ConfigSnapshot, DialSpec
from crash_detector.engine.evaluate import evaluate
from crash_detector.source_registry import Criticality, SourceRecord, SourceRegistry

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)


class Model:
    model_id = "probe.model.v0"

    def compute(self, payloads):
        raise AssertionError("must not be reached: the input is missing")


registry = SourceRegistry(sources=(
    SourceRecord(source_id="src.a", adapter_id="probe.adapter.v0", cadence_seconds=60,
                 criticality=Criticality.REQUIRED, stands_for="PROBE source"),
))
config = ConfigSnapshot(
    config_snapshot_id="cfg-probe",
    dial_specs=(
        DialSpec(dial_id=EQUITY_DIAL_ID, required_input_ids=("src.a",),
                 contributing_input_ids=(), contribution_model=Model()),
        DialSpec(dial_id=MONETARY_DIAL_ID, required_input_ids=(),
                 contributing_input_ids=(), contribution_model=None),
    ),
    staleness_window_seconds=900.0,
    source_registry=registry,
)
result = evaluate([], config, NOW)      # src.a never answered
print("NOT REFUSED — equity reads:", result.equity)
```

Run it as `PYTHONPATH=src python3 -B <file>.py` from the root of the extracted subject tree,
writing the file into the extraction and discarding it with the extraction.

---

---
---

# CD-ASR-F01 (HIGH) — criterion CD-AC-002

**Directory:** `variants/WO-2R/CD-ASR-F01/`
**Subject SHA these were run against:** the increment-2 head of the WO-2R lane. Every row below was
executed on a **separate pristine `git archive` extraction** of it, `python3 -B` throughout.

**THE CLASS these attack:** *A SCALAR DERIVED FROM BOTH DIAL TYPES.* Not "an expression naming both
markers" and not "a call whose arguments are both dials" — **any** value, however computed, however
many function calls away, however the attribute was reached, whose provenance includes both the
equity dial and the monetary dial.

**THE STRUCTURE they are aimed at**, so a reader can judge whether the routes are a fair spread over
it rather than a spread over the ones that were easy:

* **layer 1, the type** — `DialMagnitude` in `src/crash_detector/dials/magnitude.py`. Nominal,
  per-dial, non-coercible; defines none of `ARITHMETIC_DUNDERS`; provenance is a `frozenset` that is
  always exactly one dial because the only constructor takes a single `dial_id`;
* **layer 2, the point of combination** — `combine_within_one_dial`, which compares carried
  provenance and refuses anything but a single dial;
* **layer 3, the release** — `DialMagnitude.quantity_for(<dial id>)`, the only declared member that
  yields a bare `float`, refusing a mismatch by set equality;
* **layer 4, the consumer boundaries** — `EquityCrashScore` / `MonetaryDebasementScore` each refuse a
  magnitude that is not their own dial's;
* **layer 5, the publication gate** — `number_for_dial_slot` in
  `src/crash_detector/publication/dial_scalar.py`, which releases into a dial slot only from a
  magnitude whose provenance is exactly that slot's dial;
* **layer 6, the closed public envelope schema**, which has no third key for a combined figure;
* **layer 7, the AST LOCATOR** — `tools/register/check_no_blend.py`, RULES 1, 2 and 3. **It is a
  locator, not a closure, and it carries a declared limit.** Several rows below record `exit 0` from
  it, and that is the declared limit doing what it says, not a gap found afterwards.

**COMMANDS USED BELOW**, written out once and referred to by name:

| name | command |
|---|---|
| `AST` | `python3 tools/register/check_no_blend.py --root .` |
| `ARM` | `PYTHONPATH=src python3 -m pytest tests/test_scores.py tests/test_dialset.py tests/test_dial_provenance.py -q` |
| `BLEND-PROBE` | a probe that builds a `DialSet` with equity `0.9` and monetary `0.1` and calls the variant, printing either the value returned or the exception type and message. Written out in full at the bottom of this section. |

`AST` and `ARM` are two of the three DECLARED register commands for CD-AC-002, verbatim from
`required-tests.yaml`. `BLEND-PROBE` is a probe, not a register command: the Product Owner's word for
F01 is "unrepresentable", which is a RUNTIME property, and **a static checker exiting non-zero is not
proof of one** — both known-set variants passed every static checker in this repository at the WO-2
gate.

---

## KNOWN-SET RE-RUNS (from `governance/assurance/WO-2/ESCAPED-VARIANTS-KNOWN-SET.md`)

These two are the minimum obligation, not the proof. Both were reproduced in the auditor's own shape
and **refused by execution, with the traceback observed** — a checker exit alone is not sufficient
for either.

### E01 — `E01-inter-procedural-fold.patch`

| | |
|---|---|
| **finding** | CD-ASR-F01 (HIGH) |
| **proposition attacked** | No code path combines the two dials into one number. |
| **route** | `src/crash_detector/serving/banner.py` defines `_fold(left: float, right: float) -> float: return (left + right) / 2.0` and `banner_figure(dials): return _fold(dials.equity.value.score, dials.monetary.value.score)`. Transcribed from the auditor's own entry. |
| **why it escaped at the gate** | The call expression holds both dial markers but contains **no arithmetic**, so RULE 1 did not fire. The arithmetic sits one call away inside `_fold`, whose parameters are annotated `float` and carry no dial flavour. RULE 2 would have caught the co-occurrence, but `src/crash_detector/serving` **is allowlisted for RULE 2 by design**. |
| **command** | `BLEND-PROBE`, then `AST` |
| **observed refusal** | `BLEND-PROBE` → **REFUSED**, `TypeError: unsupported operand type(s) for +: 'DialMagnitude' and 'DialMagnitude'`, raised by the interpreter inside `_fold`. |
| **`AST` under this variant** | **exit 0**, `PASS — 3908 assertions`. **That is correct and DECLARED** — boundary 1 of the check's declared limit says inter-procedural flow is not followed and names this variant as its measured example. The layer that carries it is the type, and it did. |
| **also** | The route is carried as a declared test, `tests/test_dial_provenance.py::test_variant_e01_inter_procedural_fold_raises_when_executed`, so a regression fails `ARM` and not only this patch. |

### E02 — `E02-getattr-over-string-slots.patch`

| | |
|---|---|
| **finding** | CD-ASR-F01 (HIGH) |
| **proposition attacked** | No code path combines the two dials into one number. |
| **route** | `src/crash_detector/publication/summary.py` defines `_SLOTS = ("equity", "monetary")` and `magnitudes = [getattr(dials, slot).value.score for slot in _SLOTS]; return sum(magnitudes) / len(magnitudes)`. |
| **why it escaped at the gate** | **No dial marker appears in any expression.** The slot names are plain strings and the check's marker set holds only `equity_crash` and `monetary_debasement`, so nothing is ever flavoured and no rule fires. Stronger than E01 because it needs no allowlisted path. |
| **command** | `BLEND-PROBE`, then `AST` |
| **observed refusal** | `BLEND-PROBE` → **REFUSED**, `TypeError: unsupported operand type(s) for +: 'int' and 'DialMagnitude'` — `sum` starts from `0` and the very first addition fails. |
| **`AST` under this variant** | **exit 0**, `PASS — 3908 assertions`, and that is boundary 2 of the declared limit, which names this variant as its measured example. |
| **also** | Carried as `tests/test_dial_provenance.py::test_variant_e02_getattr_over_string_slots_raises_when_executed`. |

---

## NEW VARIANTS — devised by `CD-ENG-WO2R-01`, five of them

Each attacks the same class by a route that is **not** in the known set and **not** among this
seat's own six increment-1 variants (V01–V06, which are all CD-AC-001 routes against the Reading
types). The column that matters is *why it is a different route*, because a variant that is E02 with
a different slot name would prove nothing.

### V07 — `V07-reflection-over-declared-fields.patch`

| | |
|---|---|
| **finding** | CD-ASR-F01 |
| **proposition attacked** | Any scalar derived from both dials is unrepresentable. |
| **route** | `src/crash_detector/publication/overview.py`: `readings = [getattr(dials, field.name) for field in dataclasses.fields(dials)]`, then `statistics.mean([r.value.score for r in readings])`. |
| **why it differs from the known set** | E02 at least had the STRINGS `"equity"` and `"monetary"` in the source. **This has no dial name anywhere at all, in any form** — the slots are discovered from the container's own declared fields at runtime, so a check that grew its marker set to include every dial spelling would still see nothing. It also uses `statistics.mean` rather than `sum`, which matters: `statistics` does not use `+` at all, it reaches for `__float__` and `as_integer_ratio` through `_exact_ratio`, so this tests a completely different coercion path from E02's. |
| **command** | `BLEND-PROBE`, then `AST` |
| **observed refusal** | `BLEND-PROBE` → **REFUSED**, `TypeError: can't convert type 'DialMagnitude' to numerator/denominator` — raised by `statistics`, not by an operator. |
| **`AST` under this variant** | **exit 0**, `PASS — 3909 assertions`, boundary 2 of the declared limit. |

### V08 — `V08-json-round-trip-then-average.patch`

| | |
|---|---|
| **finding** | CD-ASR-F01 |
| **proposition attacked** | Any scalar derived from both dials is unrepresentable. |
| **route** | `src/crash_detector/publication/wire.py`: `dials_as_json(dials)` serialises every declared dial magnitude into one JSON document; `average_from_json(document)` averages `json.loads(document).values()`. The two functions are in the same module but the second **never sees a dial or a magnitude** — it sees a document of numbers. |
| **why it differs from the known set** | Neither known-set variant tries to LEAVE the type system rather than defeat it. This one does no arithmetic on magnitudes at all: it converts them to a transport format first, and does the arithmetic on the far side of a serialisation boundary where no type survives. It is the shape that arrives when a banner is built by a front end rather than by the engine, and it is the one this seat expected to be hardest. |
| **command** | `BLEND-PROBE`, then `AST` |
| **observed refusal** | `BLEND-PROBE` → **REFUSED at the serialisation boundary**, `TypeError: Object of type DialMagnitude is not JSON serializable`. The document is never produced, so `average_from_json` is never reached. |
| **`AST` under this variant** | **exit 0**, `PASS — 3921 assertions`, boundary 2 of the declared limit. |
| **note** | This is the same refusal the closed envelope contract already relies on: `refuse_unless_publishable` rejects a non-JSON value anywhere in a candidate, so a magnitude cannot be published un-gated either. |

### V09 — `V09-pickle-state-strips-provenance.patch` — **THIS ONE FOUND A DEFECT**

| | |
|---|---|
| **finding** | CD-ASR-F01, and it produced **CD-ENG-WO2R-F06** against this seat's own work |
| **proposition attacked** | Any scalar derived from both dials is unrepresentable. |
| **route** | `src/crash_detector/publication/wire_state.py`: `states_of(dials)` returns `copy.deepcopy(<magnitude>).__getstate__()` for every declared field; `average_of_states(states)` averages `state["quantity"]`. |
| **why it differs from the known set** | It attacks the **pickle/copy protocol** rather than any arithmetic, comparison or aggregation. Nothing in the known set touches reflection. It also does not need the magnitude type to cooperate at all: `__getstate__` is a protocol every Python object answers. |
| **OBSERVED AT `a8a2781` (increment 2, step 1) — NOT REFUSED** | **`average_of_states(states_of(DIALS))` returned `0.5`** from equity 0.9 and monetary 0.1, and `AST` exited 0. **This was a real hole in this seat's own closure and it is recorded here in the same words as the rows that were refused.** `__getstate__` had been added so `deepcopy` and `pickle` would not raise on a slotted type, and it returned `{"dial_id": ..., "quantity": ...}` — which handed out the number without naming a dial and without naming the private slot, so the release check never ran and RULE 3 had nothing to see. |
| **REPAIRED at `cec82c0` (increment 2, step 4)** | The state is now keyed by the private slot names, and `__setstate__` re-validates through the same path the constructor uses. RULE 3 gained the reflection reach. |
| **command** | `BLEND-PROBE`, then `AST` |
| **observed refusal, after the repair** | `BLEND-PROBE` → **REFUSED**, `KeyError: 'quantity'` — the state carries no such key, and the key it does carry is the one RULE 3 watches. |
| **`AST` under this variant, after the repair** | **exit 1**, `FAIL — 1 violation`, `RULE 3: reaching past the declared magnitude release` at `src/crash_detector/publication/wire_state.py:14`, naming `__getstate__`. |
| **why this row matters most** | It is the only row where the closure lost, and the loss is recorded with the SHA at which it lost. An auditor should assume this route was tried, should not re-use it, and should read the repair sceptically: what is closed is that the state cannot be read without naming the slot, and that a revived magnitude is validated exactly as a constructed one. What is NOT closed — and is declared as boundary C of the module's limit — is that reflection reaches the payload at runtime, as it does in every Python object. |

### V10 — `V10-selection-not-arithmetic.patch`

| | |
|---|---|
| **finding** | CD-ASR-F01 |
| **proposition attacked** | Any scalar derived from both dials is unrepresentable. |
| **route** | `src/crash_detector/publication/worse.py`: `max([<magnitude> for each declared field])` — "whichever dial reads highest", for a single-figure banner. |
| **why it differs from the known set** | **There is no arithmetic anywhere in it, and the figure it returns is one dial's own magnitude, unaltered.** Every other variant in this file and in the known set computes a new number. This one only CHOOSES, and it is a fair attack on the class precisely because the chosen figure is still *derived from both dials*: the choice is the blend. A closure built only against arithmetic would let it through, and a reviewer would find it hard to object to on the face of it. |
| **command** | `BLEND-PROBE`, then `AST` |
| **observed refusal** | `BLEND-PROBE` → **REFUSED**, `TypeError: '>' not supported between instances of 'DialMagnitude' and 'DialMagnitude'` — the ordering dunders are absent for exactly this reason: comparing the two dials presumes a shared scale, which is the premise CD-AC-002 denies. |
| **`AST` under this variant** | **exit 0**, `PASS — 3907 assertions`, boundary 2 of the declared limit. |

### V11 — `V11-provenance-union-not-comparison.patch`

| | |
|---|---|
| **finding** | CD-ASR-F01 |
| **proposition attacked** | Provenance is compared at the point of combination, and the publication boundary refuses any scalar whose provenance is not exactly one dial. |
| **route** | `src/crash_detector/publication/merged.py` builds a magnitude by `DialMagnitude.__new__` plus `object.__setattr__`, setting `provenance` to the **UNION** of the two dials' provenance and the payload to their mean, told as "provenance is preserved rather than discarded". |
| **why it differs from the known set** | It does not try to defeat the provenance check — it tries to **satisfy** it by making the merged figure honest about where it came from, which is the argument a thoughtful engineer would actually make. It attacks the invariant rather than the arithmetic, and it is the only variant here that produces an object that exists. |
| **command** | `BLEND-PROBE`, then `AST` |
| **observed outcome, construction** | The merged object IS constructed — `__new__` and `object.__setattr__` walk past the constructor, as they do for any frozen object in Python (boundary B of the declared limit). Its provenance is `frozenset({'equity_crash', 'monetary_debasement'})`. |
| **observed refusal, three boundaries, all by comparing DATA** | `quantity_for('equity_crash')` → `CrossDialCombination: this magnitude's provenance is ['equity_crash', 'monetary_debasement'], and the caller asked for it as 'equity_crash'`. `number_for_dial_slot('equity_crash', merged)` → `DialProvenanceRefused: nothing may be published into the 'equity_crash' slot without the provenance that says it belongs there: ... which is not exactly one dial`. `EquityCrashScore(score=merged, ...)` → `CrossDialCombination: ... this dial is 'equity_crash'`. **The forged provenance made the object LESS usable, not more, which is the direction boundary B declares.** |
| **`AST` under this variant** | **exit 1**, `FAIL — 2 violations`, both `RULE 3: reaching past the declared magnitude release`, at `merged.py:23` and `merged.py:32`. |

---

## Summary of what was refused by what

| variant | route class | `AST` locator | runtime refusal |
|---|---|---|---|
| E01 | inter-procedural fold, allowlisted path | exit 0 — **declared limit, boundary 1** | `TypeError` on `+`, `DialMagnitude` and `DialMagnitude` |
| E02 | `getattr` over string slots | exit 0 — **declared limit, boundary 2** | `TypeError` on `+`, `int` and `DialMagnitude` |
| V07 | reflection over declared fields, `statistics.mean` | exit 0 — declared limit, boundary 2 | `TypeError`, can't convert to numerator/denominator |
| V08 | JSON round trip, arithmetic downstream | exit 0 — declared limit, boundary 2 | `TypeError`, not JSON serializable |
| V09 | pickle/copy state | **exit 1, RULE 3** | `KeyError: 'quantity'` — **AND SEE THE ROW: NOT REFUSED at `a8a2781`** |
| V10 | selection, not arithmetic | exit 0 — declared limit, boundary 2 | `TypeError`, `'>' not supported` |
| V11 | provenance union rather than comparison | **exit 1, RULE 3 ×2** | `CrossDialCombination` at three separate boundaries |

**Three honest observations about that table.** First, **the static arm is silent on five of seven**,
and that is the layer split working exactly as the declared limit says it does — CD-AC-002's
"unrepresentable" half is a runtime proposition and the type carries it. Second, **V09 found a real
defect in this seat's own closure**, and both observations are recorded, with the SHA at which the
closure lost. Third, **no row here proves the class is closed.** Seven routes refused is seven routes
refused. The next auditor's job is the eighth.

## What this seat did NOT manage to refuse, stated plainly

A number **already released** through `quantity_for(<one dial id>)` is an ordinary `float`, and two
of them can be added by ordinary Python arithmetic. No variant here attacks that, because there is
nothing to attack: it is boundary A of the declared limit in
`src/crash_detector/dials/magnitude.py`, it is boundary 6 of the AST check's, and it is stated in the
register entry and both execution contracts. What closes the consequence is that the result is
**unpublishable** — `number_for_dial_slot` takes only a magnitude, and the closed envelope schema has
no third key. An auditor who wants to attack this should attack the PUBLICATION path, not the type.

---

## `BLEND-PROBE`, written out in full

The probe below is **data, not a runner**: it is printed here so an auditor can retype it, and it is
NOT committed as an executable file (`PBG-ASSURE-001`). Write it into the extraction, run it, and
discard it with the extraction.

```python
import sys
from datetime import datetime, timezone

from crash_detector.dials.dialset import DialSet, EQUITY_DIAL_ID, MONETARY_DIAL_ID
from crash_detector.dials.magnitude import DialMagnitude
from crash_detector.dials.reading import Value
from crash_detector.dials.scores import EquityCrashScore, MonetaryDebasementScore

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)
DIALS = DialSet(
    equity=Value(
        value=EquityCrashScore(
            score=DialMagnitude(dial_id=EQUITY_DIAL_ID, quantity=0.9), contributions=()
        ),
        as_of_utc=NOW, inputs_used=("src.a",),
    ),
    monetary=Value(
        value=MonetaryDebasementScore(
            score=DialMagnitude(dial_id=MONETARY_DIAL_ID, quantity=0.1), contributions=()
        ),
        as_of_utc=NOW, inputs_used=("src.a",),
    ),
)


def report(label, fn):
    try:
        answer = fn()
    except BaseException:
        exc_type, exc, _ = sys.exc_info()
        print(f"{label}: REFUSED -> {exc_type.__module__}.{exc_type.__name__}: {exc}")
        return
    print(f"{label}: *** NOT REFUSED *** returned {answer!r}")


# then, per variant, one of:
#   from crash_detector.serving.banner import banner_figure
#   report("E01", lambda: banner_figure(DIALS))
#   from crash_detector.publication.summary import summary_figure
#   report("E02", lambda: summary_figure(DIALS))
#   from crash_detector.publication.overview import overview_figure
#   report("V07", lambda: overview_figure(DIALS))
#   from crash_detector.publication.wire import dials_as_json
#   report("V08", lambda: dials_as_json(DIALS))
#   from crash_detector.publication.wire_state import states_of, average_of_states
#   report("V09", lambda: average_of_states(states_of(DIALS)))
#   from crash_detector.publication.worse import worse_dial_magnitude
#   report("V10", lambda: worse_dial_magnitude(DIALS))
#   from crash_detector.publication.merged import merged_magnitude
#   from crash_detector.publication.dial_scalar import number_for_dial_slot
#   merged = merged_magnitude(DIALS)
#   report("V11 release", lambda: merged.quantity_for(EQUITY_DIAL_ID))
#   report("V11 publish", lambda: number_for_dial_slot(EQUITY_DIAL_ID, merged))
```

Run it as `PYTHONPATH=src python3 -B <file>.py` from the root of the extracted subject tree.

---

## Increments 3 to 6 are not represented here

This file covers **increment 1** (CD-ASR-F02 and CD-ASR-F03) and **increment 2** (CD-ASR-F01).
Variants for CD-ASR-F04, F05 and F06 are owed by the later increments of the same dispatch and their
absence here is not a claim about them.
