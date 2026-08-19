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
register entry and both execution contracts.

> **THE SENTENCE THAT STOOD HERE WAS WRONG AND IS WITHDRAWN** (`CD-PL-F54`). It said "what closes the
> consequence is that the result is **unpublishable** — `number_for_dial_slot` takes only a
> magnitude", and told an auditor to attack the publication path rather than the type. The Project
> Lead did exactly the opposite of what that advice assumed and found the hole: it re-wrapped the
> blend as `DialMagnitude(dial_id="equity_crash", quantity=blended)`, which HAS a magnitude and HAS
> provenance of exactly one dial, and `number_for_dial_slot` **returned 0.5**. The advice sent
> attention to the layer where the defect was not, which is precisely what CD-RULE-006 now forbids.
> What closes the consequence, measured, is the RE-ENTRY: see the increment-2b section below.

---

# INCREMENT 2b — CD-PL-F54, re-opening CD-ASR-F01 (HIGH)

**Everything above increment 2b stands and was NOT reverted.** The Project Lead reproduced every
number of increment 2 exactly and refused nine of its own eleven probes against it. What it did not
close is the LAUNDERING class: `float(repr(m).split("quantity=")[1].rstrip(")"))` names no dial,
two of those add, and the sum re-wrapped as a magnitude of one dial published. The closure moved to
the **RE-ENTRY** — a bare `float` can no longer become a `DialMagnitude` — and the variants below
attack that.

**Two commands are used below.** `AST` is `python3 tools/register/check_no_blend.py --root .`.
`NUMDEF` is `python3 tools/register/check_no_numeric_default.py --root .`. `LAUNDER-PROBE` is
written out in full at the end of this file, after `BLEND-PROBE`, and is what makes the fixtures
through the declared admission door so that every attack starts from two LEGITIMATE magnitudes of
0.4 (equity) and 0.6 (monetary). A variant refused for want of a valid subject would prove nothing.

## KNOWN-SET RE-RUNS at increment 2b

Every one of the six the dispatch names as the minimum obligation, executed on a pristine
`git archive` extraction, one extraction per variant, `python3 -B` throughout.

### `PL-Q9` — `PL-Q9-flavour-free-repr-launder.patch`

| | |
|---|---|
| **finding** | CD-PL-F54 (HIGH), re-opening CD-ASR-F01 |
| **source** | The Project Lead's, verbatim, from `governance/reconciliation/WO-2R/PL-Q9-flavour-free-repr-launder.py.txt` on `main`. Committed here as a patch so it can be re-applied mechanically. |
| **proposition attacked** | No code path combines the two dials into one number. |
| **route** | `src/crash_detector/serving/banner.py` reads the figure off each reading with `float(repr(reading).split("quantity=")[1].rstrip(")"))`, sums in a loop, divides by the count, and re-wraps as `DialMagnitude(dial_id=slot, ...)` where `slot` is a PARAMETER. |
| **why it escaped at increment 2** | It removes every flavour-bearing NAME. No dial appears in any expression, no arithmetic touches a magnitude, and the type is never asked for a number. Both layers were defeated together: `AST` PASS on 3919 assertions, and at runtime it published `EquityCrashScore(score=DialMagnitude(dial_id='equity_crash', quantity=0.5))` from 0.4 and 0.6. |
| **command** | `AST`, then `LAUNDER-PROBE PLQ9` |
| **`AST` under this variant** | **exit 0**, `PASS — 4716 assertions`. **STILL CLEAN, AND THAT IS DECLARED** — boundary 6. Nothing static can recognise this module; that is why RULE 4 watches the door instead. |
| **observed refusal** | `LAUNDER-PROBE` → **REFUSED**, `crash_detector.dials.provenance.QuantityProvenanceMissing: a bare number (0.5) was offered as dial 'equity_crash''s magnitude.` |
| **also** | Carried as a declared test, `tests/test_dial_provenance.py::test_variant_pl_q9_the_flavour_free_launderer_is_refused`. |

### `PL-Q4`, `PL-Q5`, `PL-Q6` — no patch; they are probes, not modules

| | |
|---|---|
| **finding** | CD-PL-F54 (HIGH) |
| **source** | `governance/reconciliation/WO-2R/PL-Q4-Q6-launder-rewrap-publish.py.txt` on `main`. |
| **routes** | `PL-Q4` launder both through `repr`, re-wrap the mean as equity, build an `EquityCrashScore`. `PL-Q5` the same but releasing through the DECLARED door `quantity_for`. `PL-Q6` offer the re-wrapped blend to `number_for_dial_slot`. |
| **why they escaped at increment 2** | The re-wrapped blend's provenance IS exactly one dial, so every provenance comparison passed it. `PL-Q6` **returned 0.5**, which is what refuted boundary 6. |
| **command** | `LAUNDER-PROBE` (all three are in it) |
| **observed refusal** | all three **REFUSED**, `QuantityProvenanceMissing: a bare number (0.5) was offered as dial 'equity_crash''s magnitude.` `PL-Q6` never reaches the publication gate, because the magnitude it needs cannot be built. |
| **also** | All three are carried as declared tests, `test_variant_pl_q4_*`, `test_variant_pl_q5_*`, `test_variant_pl_q6_*`. |

### `E01` and `E02` — re-run unchanged

Both patches above still apply and both still raise. Re-measured at increment 2b from fixtures built
through the admission door: `E01` → `TypeError: unsupported operand type(s) for +: 'DialMagnitude'
and 'DialMagnitude'`; `E02` → `TypeError: unsupported operand type(s) for +: 'int' and
'DialMagnitude'`. This is the CD-RULE-006 re-measurement for boundaries 1, 2, 3 and 5, which hand
their residue to the type layer.

### The nine Project Lead probes that were already refused

`PL-Q1a` (repr text leak then add) is **NOT refused and never will be** — it is boundary 6 and two
floats add. `PL-Q1b`, `PL-Q2a`–`PL-Q2h` (`math.fsum`, `round`, `operator.index`, `Decimal`, `int`,
`complex`, `format`, `str`-then-`float`) are all still refused, re-run at increment 2b. `PL-Q3`
(`type.__setattr__` installing `__add__`) still succeeds and is still the declared class-mutation
residue from increment 2; `PL-Q3b` shows publication after that mutation is refused with
`MagnitudeSurfaceViolated`.

## NEW VARIANTS — devised by `CD-ENG-WO2R-01` at increment 2b, six of them

**None asks the type for a number.** Nine of those are already refused and a tenth would prove
nothing. Every one below attacks the LAUNDERING class, or the new structure's own doors.

### V12 — `V12-admission-door-false-declaration.patch` — **NOT REFUSED AT RUNTIME**

| | |
|---|---|
| **finding** | CD-PL-F54 (HIGH) |
| **proposition attacked** | No code path combines the two dials into one number. |
| **route** | `PL-Q9` **plus one line**: the mean is passed through `observed_for_dial(dial_id=slot, quantity=mean, inputs_used=("operator-banner",))` before being wrapped. This is the exact follow-up the re-entry closure's declared residue predicts, written by this seat against its own structure rather than waited for. |
| **why it is a DIFFERENT route from the known set** | Nothing in the known set names an admission door, because before this increment there was none. It attacks the base case of the closure, not a laundering exit. |
| **command** | `AST`, then `LAUNDER-PROBE V12` |
| **`AST` under this variant** | **exit 1**, 2 violations, both `RULE 4: a provenance door outside the declared admission sites` — `src/crash_detector/serving/banner.py:4` (the import) and `:22` (the call). |
| **`NUMDEF` under this variant** | exit 0. It is not on the dial path Rule F reasons about. |
| **observed at runtime** | ***NOT REFUSED.*** Returns `EquityCrashScore(score=DialMagnitude(dial_id='equity_crash', quantity=0.5), contributions=())` from 0.4 and 0.6. **THIS IS THE DECLARED LIMIT, BOUNDARY 7, AND IT IS NOT CLAIMED TO BE CARRIED ANYWHERE AT RUNTIME.** Only RULE 4 catches it, and RULE 4 is static. |

### V13 — `V13-admission-door-via-importlib-getattr.patch` — **NOT REFUSED AT RUNTIME**

| | |
|---|---|
| **finding** | CD-PL-F54 (HIGH) |
| **proposition attacked** | The same, and additionally: can RULE 4 be walked around by never writing the door's name in an import? |
| **route** | `importlib.import_module("crash_detector.dials.provenance")` at module level, then `admit = getattr(_M, "observed_for_dial")` inside the function. No `from … import` of the name at all. |
| **why it is a DIFFERENT route** | It tests RULE 4's own reach rather than the closure's, by the same manoeuvre `E02` used against RULE 1 — replace a name with a string. |
| **command** | `AST`, then `LAUNDER-PROBE V13` |
| **`AST` under this variant** | **exit 1**, 1 violation, `RULE 4` at `src/crash_detector/serving/banner.py:19` — the string constant handed to `getattr`. RULE 4 judges constants as well as names, so the manoeuvre that beat RULE 1 does not beat this one. |
| **observed at runtime** | ***NOT REFUSED***, same as V12 and for the same declared reason. |

### V15 — `V15-declared-quantity-constructed-directly.patch` — **NOT REFUSED AT RUNTIME**

| | |
|---|---|
| **finding** | CD-PL-F54 (HIGH) |
| **proposition attacked** | Are the two declared doors the ONLY way to establish a provenance? |
| **route** | Bypass both doors and construct the carrier itself: `DeclaredQuantity(dials=frozenset({slot}), value=total / len(figures))`. |
| **why it is a DIFFERENT route** | It attacks the type rather than the door — the shape a reader who has understood the closure would reach for first. |
| **command** | `AST`, then `LAUNDER-PROBE V15` |
| **`AST` under this variant** | **exit 1**, 2 violations, `RULE 4` at `banner.py:4` and `:19`. The TYPE NAME is in the guarded vocabulary precisely so that constructing one is not a way around the doors. |
| **observed at runtime** | ***NOT REFUSED***. Boundary 7. Declared, not claimed closed. |

### V14 — `V14-admission-door-as-a-numeric-default.patch` — **REFUSED, TWICE, BY TWO CRITERIA**

| | |
|---|---|
| **finding** | CD-PL-F54, and it guards CD-ASR-F03 against being reopened by this increment |
| **proposition attacked** | Did widening Rule F to trace THROUGH the admission door quietly make the door a DECLARED provenance, so that `observed_for_dial(quantity=0.0)` on an absence branch became legal? |
| **route** | The `missing_required` branch of `_evaluate_dial` returns a `Value` whose magnitude is `observed_for_dial(dial_id=spec.dial_id, quantity=0.0, inputs_used=("baseline",))`. |
| **why it is a DIFFERENT route** | It attacks the SEAM between this increment and increment 1 — the place a closure most often reopens something it was not looking at. This seat wrote it because it made the change, not because anybody asked. |
| **command** | `NUMDEF`, then `PYTHONPATH=src python3 -m pytest tests/test_evaluate.py -q` |
| **observed refusal, static** | `NUMDEF` **exit 1**, 1 violation at `src/crash_detector/engine/evaluate.py:306`, `rule: F: unrecognised magnitude provenance` — the literal `0.0` is reported as the literal it is. The door is a PASS-THROUGH and did not become a terminus. |
| **observed refusal, runtime** | **9 failed, 26 passed.** The increment-1 post-condition `refuse_a_number_without_its_inputs` raises `AbsenceYieldedAValue`. |
| **`AST` under this variant** | exit 0, and correctly: `evaluate.py` IS a declared admission site, so RULE 4 does not fire there. Being on that list exempts it from RULE 4 and from nothing else, which is exactly what these two refusals demonstrate. |

### V16 — `V16-text-and-json-launder-without-repr.patch` — **REFUSED**

| | |
|---|---|
| **finding** | CD-PL-F54 (HIGH) |
| **proposition attacked** | **Is this closure a `repr` fix or a class closure?** |
| **route** | `src/crash_detector/publication/wire_text.py` launders with **no `repr` anywhere**: `from_text` uses an f-string over the private declared quantity and parses the number back out; `from_json` does a JSON round trip of the pickle state. `combined_for` sums whichever it is given and re-wraps. |
| **why it is a DIFFERENT route** | Every laundering variant so far — the auditor's, the Project Lead's and this seat's — has gone through `repr`. If the closure were a `repr` fix, this would walk straight past it. |
| **command** | `AST`, then `LAUNDER-PROBE V16` |
| **`AST` under this variant** | **exit 1**, 6 violations, `RULE 3` — the module names both private slots. That is a second, independent refusal and was not the point of the variant. |
| **observed refusal** | Both arms leak the numbers successfully (`0.4` and `0.6` printed by the probe, so the EXIT genuinely worked and nothing was hidden), and both re-entries are **REFUSED**: `QuantityProvenanceMissing: a bare number (0.5) was offered as dial 'equity_crash''s magnitude.` **This is the evidence that the closure is at the re-entry and not at `repr`.** |
| **also** | Carried as a declared test, `tests/test_dial_provenance.py::test_laundering_that_never_touches_repr_is_refused_too`. |

### V17 — `V17-second-private-slot-overwritten-in-place.patch` — **NOT REFUSED AT RUNTIME. A FINDING AGAINST THIS SEAT'S OWN WORK.**

| | |
|---|---|
| **finding** | `CD-ENG-WO2R-F11`, raised by this seat against its own closure |
| **proposition attacked** | Does the re-entry closure cover a number that is never RE-ENTERED because it is written in place? |
| **route** | Read both figures off `_DeclaredQuantity__value`, then `object.__setattr__(inner, "_DeclaredQuantity__value", mean)` on the quantity one live magnitude already holds, and return that magnitude. **Nothing is ever constructed**, so no constructor is ever reached. |
| **why it is a DIFFERENT route** | Every other variant here goes IN through a constructor. This one changes a number that is already inside, which is the one shape a re-entry closure structurally cannot see. |
| **command** | `AST`, then `LAUNDER-PROBE V17` |
| **`AST` under this variant** | **exit 1**, 6 violations, `RULE 3` at `banner.py:6, :7, :16, :17`. |
| **observed at runtime** | ***NOT REFUSED.*** The magnitude then reads `0.5`. **NO RUNTIME LAYER CARRIES THIS AND NONE IS CLAIMED TO** (CD-RULE-006). It is `object.__setattr__`, which walks past `__setattr__` on every frozen object in Python and which no Python-level structure can prevent. Declared as boundary B in `src/crash_detector/dials/magnitude.py` and in `provenance.py`, where the previous text said this residue's direction was SAFE — **that was true of forging the PROVENANCE and is not true of forging the VALUE**, and this seat corrected it rather than leaving the claim standing. |
| **what changed because of it** | RULE 3's guarded set was extended from one private name to two (`_DeclaredQuantity__value`, `__value`), with each declaring module exempt only for the slot it declares. **HONEST NOTE: this seat did NOT find a route to the second slot that avoids naming the first**, so at the commit before the extension this variant already produced 4 RULE 3 violations. The extension is therefore PROPHYLACTIC — closing a name the closure created — rather than the repair of a measured escape, and it is recorded that way. |

## Summary of what was refused by what — increment 2b

| variant | route class | `AST` locator | runtime |
|---|---|---|---|
| E01 | inter-procedural fold | exit 0 — declared limit, boundary 1 | **REFUSED** `TypeError` on `+` |
| E02 | `getattr` over string slots | exit 0 — declared limit, boundary 2 | **REFUSED** `TypeError` on `+` |
| PL-Q4 | repr launder, re-wrap, publish | n/a (probe) | **REFUSED** `QuantityProvenanceMissing` |
| PL-Q5 | `quantity_for` launder, re-wrap | n/a (probe) | **REFUSED** `QuantityProvenanceMissing` |
| PL-Q6 | publication gate on the re-wrap | n/a (probe) | **REFUSED** `QuantityProvenanceMissing` |
| PL-Q9 | flavour-free module | exit 0 — declared limit, boundary 6 | **REFUSED** `QuantityProvenanceMissing` |
| V12 | admission door, false declaration | **exit 1, RULE 4 ×2** | ***NOT REFUSED*** — boundary 7 |
| V13 | admission door via `importlib`+`getattr` | **exit 1, RULE 4** | ***NOT REFUSED*** — boundary 7 |
| V15 | `DeclaredQuantity` built directly | **exit 1, RULE 4 ×2** | ***NOT REFUSED*** — boundary 7 |
| V14 | door as a numeric default on absence | **`NUMDEF` exit 1, Rule F** | **REFUSED** `AbsenceYieldedAValue`, 9 tests |
| V16 | f-string and JSON, **no `repr`** | **exit 1, RULE 3 ×6** | **REFUSED** `QuantityProvenanceMissing` ×2 |
| V17 | in-place slot rewrite | **exit 1, RULE 3 ×6** | ***NOT REFUSED*** — `CD-ENG-WO2R-F11` |

**Four honest observations about that table.** First, **three variants are NOT refused at runtime and
all three are inside a written boundary** — V12, V13 and V15 at boundary 7, which says in terms that
the admission door is a declaration and that no runtime layer carries it. Second, **V17 was not
inside a boundary until this seat wrote one**: the previous text claimed the `object.__setattr__`
residue was safe, and that was true of the provenance direction and false of the value direction.
Third, **the static and runtime arms now split the work rather than duplicating it**: where one is
silent the other bites, and the four rows where both bite are not the same four. Fourth, and it has
not stopped being true since the last increment: **no row here proves the class is closed.** Twelve
routes refused or bounded is twelve routes. The next auditor's job is the thirteenth, and the
strongest place to look is boundary 7.

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

## `LAUNDER-PROBE`, written out in full

Not executable and not a runner (`PBG-ASSURE-001`). Retype it into a file in the root of an
extracted subject tree and run `python3 -B <file>.py <VARIANT>`. It builds its fixtures through the
DECLARED admission door, so every attack starts from two LEGITIMATE magnitudes and a refusal is a
refusal of the ATTACK rather than of the scaffolding.

```python
import sys
sys.path.insert(0, "src")
from crash_detector.dials.magnitude import DialMagnitude
from crash_detector.dials.provenance import observed_for_dial

EQ = DialMagnitude(dial_id="equity_crash",
                   quantity=observed_for_dial(dial_id="equity_crash", quantity=0.4,
                                              inputs_used=("feed.a",)))
MO = DialMagnitude(dial_id="monetary_debasement",
                   quantity=observed_for_dial(dial_id="monetary_debasement", quantity=0.6,
                                              inputs_used=("feed.b",)))


def report(label, fn):
    try:
        answer = fn()
    except BaseException:
        exc_type, exc, _ = sys.exc_info()
        print(f"{label}: REFUSED -> {exc_type.__module__}.{exc_type.__name__}: {exc}")
        return
    print(f"{label}: *** NOT REFUSED *** returned {answer!r}")


def leak(m):
    return float(repr(m).split("quantity=")[1].rstrip(")"))


which = sys.argv[1]

# PL-Q4 / PL-Q5 / PL-Q6 need no patch; they run against the clean tree.
if which == "PLQ456":
    from crash_detector.dials import scores as S
    from crash_detector.publication import dial_scalar as P
    b1 = (leak(EQ) + leak(MO)) / 2
    report("PL-Q4", lambda: S.EquityCrashScore(
        score=DialMagnitude(dial_id="equity_crash", quantity=b1), contributions=()))
    b2 = (EQ.quantity_for("equity_crash") + MO.quantity_for("monetary_debasement")) / 2
    report("PL-Q5", lambda: S.EquityCrashScore(
        score=DialMagnitude(dial_id="equity_crash", quantity=b2), contributions=()))
    report("PL-Q6", lambda: P.number_for_dial_slot(
        "equity_crash", DialMagnitude(dial_id="equity_crash", quantity=b1)))

# PLQ9 / V12 / V13 / V15 / V17 each replace src/crash_detector/serving/banner.py
elif which in ("PLQ9", "V12", "V13", "V15", "V17"):
    from crash_detector.serving.banner import aggregate
    report(which, lambda: aggregate([EQ, MO], "equity_crash"))

elif which == "V16":
    from crash_detector.publication.wire_text import combined_for, from_text, from_json
    print("  f-string leak:", from_text(EQ), from_text(MO))
    print("  json leak:", from_json(EQ), from_json(MO))
    report("V16a-fstring", lambda: combined_for([EQ, MO], "equity_crash", using=from_text))
    report("V16b-json", lambda: combined_for([EQ, MO], "equity_crash", using=from_json))
```

`E01` and `E02` use `BLEND-PROBE` above, unchanged, and `V14` uses no probe at all — its two arms
are `NUMDEF` and `pytest tests/test_evaluate.py`.

---

## Increments 3 to 6 are not represented here

This file covers **increment 1** (CD-ASR-F02 and CD-ASR-F03), **increment 2** (CD-ASR-F01) and
**increment 2b** (CD-PL-F54, re-opening CD-ASR-F01).
Variants for CD-ASR-F04, F05 and F06 are owed by the later increments of the same dispatch and their
absence here is not a claim about them.

---
---

# CD-ASR-F04 (MEDIUM) — criterion CD-AC-012 — WO-2R increment 3

**Directory:** `variants/WO-2R/CD-ASR-F04/`

**THE CLASS these attack:** *AN EGRESS ALLOWLIST ENTRY THAT REACHES A BROKER* — closed as the
class *AN EGRESS ALLOWLIST ENTRY NOBODY DECLARED.* Not "an entry whose name matches a broker
vocabulary", and emphatically not "an entry that is an IP literal". The auditor put
`198.51.100.24` where `api.ibkr.com` had been and the check went green, because it recognised
brokers **by name** and an address has no name to recognise.

**THE STRUCTURE they are aimed at.** Deny by default over `deploy/egress-destinations.yaml`, a
new in-tree registry read as data by `tools/register/check_egress_no_broker.py`:

* **layer 1, `CD-EGRESS-004`** — an allowlist entry is admissible only if it is, character for
  character, the `host` of a destination registered in that file whose `services` list names
  that service. **No recognition is performed on an entry that is not**, so there is no pattern
  to write around;
* **layer 2, `CD-EGRESS-002`** — the broker concept vocabulary and the known-operator denylist
  **survive**, applied to every registered `host` and `operator`, to every allowlist entry as
  written, and to every `pending` entry. Neither layer is sole;
* **layer 3, `CD-EGRESS-005`** — closed key sets on `x-egress`, on a destination and on the
  registry document, asserted by **equality** with a declared member set;
* **layer 4, `CD-EGRESS-006`** — a **positive** hostname shape, uniqueness, an operator, a
  purpose, a `declared_in` clause, and services that exist and declare `ALLOWLIST`;
* **layer 5, the precondition** — an absent or unparseable registry is `exit 3`, never a pass.

**WHY THE ROUTES BELOW ARE AIMED AT THE FIX AND NOT AT THE OLD DEFECT.** Writing more address
spellings would prove nothing: layer 1 refuses every one of them for the same reason and without
looking. The interesting question is what a deny-by-default registry **still lets through**, so
six of the seven attack the registry, the key set, the service scoping or the file's own
existence, and the seventh is the positive control that proves the closure does not forbid the
product.

**Clean-arm command for every row below:**
`python3 tools/register/check_egress_no_broker.py --root .` → **exit 0**, `PASS — 53 assertions,
0 violations` at lane `4933376`.

### E05 — `E05-broker-by-ip-literal.patch`

| | |
|---|---|
| **finding** | CD-ASR-F04 (MEDIUM) — the whole of the CD-AC-012 AMBER |
| **proposition attacked** | A broker host added to any container's egress allowlist is a violation. |
| **route** | `198.51.100.24` into `cd-collectors`' `x-egress.hosts` **in place of a hostname**, with an innocent comment. Transcribed from the auditor's own entry. |
| **why it escaped at the gate** | The check judged a host by tokenising its **domain labels** against an execution vocabulary and its **registrable domain** against a known-operator denylist. An address has neither. **Reproduced by this seat before repairing anything**: applied to an extraction of `cc961bf`, `exit 0`, `PASS — 44 assertions, 0 violations`. |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |
| **observed refusal** | **exit 1**, `FAIL — 1 violation(s)`. `deploy/compose.yaml:380` · rule `CD-EGRESS-004: an allowlist entry is not a registered destination` · *"service `cd-collectors` may reach `198.51.100.24`, which is not registered in deploy/egress-destinations.yaml. THIS IS A VIOLATION BY DEFAULT: nothing was recognised about `198.51.100.24` and nothing needed to be. … The admissible set at this commit is EMPTY."* |
| **the point** | The refusal names the entry **without having recognised anything about it**. Layer 2 never runs on it. That is the difference between closing the class and catching the instance. |

### V18 — `V18-registered-for-another-service.patch`

| | |
|---|---|
| **finding** | CD-ASR-F04 — a variant of this seat's own, against its own structure |
| **proposition attacked** | Is a registry entry a grant to **named services**, or a global permit? |
| **route** | `panel.example.org` registered properly — six fields, well-formed host, innocent operator `Example Panel Data Ltd`, `declared_in` cited — **for `cd-witness`**, and then named in **`cd-collectors`**' allowlist. |
| **why it is a DIFFERENT route from anything on the known set** | The known set contains one CD-AC-012 egress route and it is a **spelling** attack. This one has no spelling problem at all: it satisfies the registry schema completely, passes the positive hostname shape, passes the vocabulary and passes the denylist. It attacks the **scope** of a grant, which did not exist as a concept before this increment. |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |
| **observed refusal** | **exit 1**, `FAIL — 1 violation(s)`. `deploy/compose.yaml:380` · rule `CD-EGRESS-004: a destination is registered, but not for this service` · *"…which IS registered in deploy/egress-destinations.yaml — but for cd-witness, not for `cd-collectors`. A registry entry is a grant to named services, not a global permit."* |

### V19 — `V19-posture-through-an-unread-key.patch`

| | |
|---|---|
| **finding** | CD-ASR-F04 — a variant of this seat's own |
| **proposition attacked** | Can a destination be declared through a field the guard does not read? |
| **route** | `hosts: []` left untouched and honest; a sibling `hosts_extra:` added to the same `x-egress` block carrying `198.51.100.24`. |
| **why it is a DIFFERENT route** | It is **not an allowlist entry**, so layer 1 never sees it — `CD-EGRESS-004` iterates `hosts` and `hosts` is empty. Nothing on the known set attacks the reader's own field vocabulary. This is `CD-EGRESS-003`'s argument ("a check that skips a service it does not recognise is bypassed by adding a service") applied one level down to **keys**, and it is the route that would otherwise have let the WO-3 lane inherit a declaration with a second, unread allowlist in it. |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |
| **observed refusal** | **exit 1**, `FAIL — 1 violation(s)`. `deploy/compose.yaml:379` · rule `CD-EGRESS-005: x-egress declares an unknown key` · *"…the contract admits exactly enforced_by, hosts, pending, policy. An unknown key is a violation and not an extension."* |

### V20 — `V20-register-the-address-itself.patch`

| | |
|---|---|
| **finding** | CD-ASR-F04 — **the attack on this seat's own fix**, and the most important row here |
| **proposition attacked** | Does deny-by-default merely move the hole one file up? |
| **route** | Register `198.51.100.24` as a destination — `id`, `operator: Example Market Data Ltd`, a plausible `purpose`, a `declared_in` clause, `services: [cd-collectors]` — and then name it in `cd-collectors`' allowlist. |
| **why it is a DIFFERENT route** | E05 attacks the allowlist. This attacks the **registry**, which is where E05's repair put the trust. It passes layer 1 completely: the destination IS declared, for the right service. And **layer 2 cannot judge it at all** — an address has no registrable domain for the denylist to read and no labels for the vocabulary to tokenise, which is the whole of why E05 worked in the first place. |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |
| **observed refusal** | **exit 1**, `FAIL — 2 violation(s)`. `deploy/egress-destinations.yaml:133` · rule `CD-EGRESS-006: a destination host is not a declarable hostname` · *"…its final label `24` is not an alphabetic top-level domain of at least two characters. … This clause is not an address detector: it never asks what the value IS, only whether it is the one admissible shape."* And `deploy/compose.yaml:380` · `CD-EGRESS-004`, because a malformed entry registers nothing, so the registry **fails closed** rather than widening the admissible set. |
| **the point** | The positive hostname shape is what stops the registry becoming the hole the allowlist used to be, and the reason it is a hostname is stated rather than assumed: the only offline evidence of what a destination reaches is its registrable domain, so a destination layer 2 cannot judge must not be declarable. |

### V21 — `V21-innocent-host-broker-operator.patch`

| | |
|---|---|
| **finding** | CD-ASR-F04 — a variant of this seat's own |
| **proposition attacked** | Can a broker be admitted by registering a hostname that carries no execution word? |
| **route** | `gateway.example.net` — no concept token, on no denylist, perfectly shaped — registered for `cd-collectors` with `operator: Interactive Brokers`, and named in the allowlist. |
| **why it is a DIFFERENT route** | It passes layer 1 in full and passes the **host half** of layer 2. Nothing on the known set attacks the attribution fields; E05 attacks the host string only. This row is the measured evidence for **boundary 3** of the declared limit — the claim that `purpose` prose is unjudged but the `operator` field is judged, and that this carries the archetypal case. |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |
| **observed refusal** | **exit 1**, `FAIL — 1 violation(s)`. `deploy/egress-destinations.yaml:134` · rule `CD-EGRESS-002: a REGISTERED destination is a broker` · *"…declares operator `Interactive Brokers`, and its name carries the execution concept(s) brokers. … Registering it does not make it admissible: deny-by-default decides what nobody declared, and this layer decides what somebody declared and should not have."* |

### V22 — `V22-registered-for-a-no-egress-service.patch`

| | |
|---|---|
| **finding** | CD-ASR-F04 — a variant of this seat's own |
| **proposition attacked** | Is a registry entry harmless while no allowlist names it? |
| **route** | `data.example.org` registered for **`cd-engine`**, with **no allowlist entry anywhere**. `cd-engine`'s `hosts` stays `[]`, so `CD-EGRESS-001` is satisfied and `CD-EGRESS-004` has nothing to iterate. |
| **why it is a DIFFERENT route** | Every other row here writes something into a `hosts` list. This one writes nothing into any allowlist at all, and is invisible to every rule that reads one. The declaration that BLUEPRINT §13's no-egress container may reach a host is exactly the kind of inherited defect the Product Owner ordered closed *before* the WO-3 lane reads it. |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |
| **observed refusal** | **exit 1**, `FAIL — 1 violation(s)`. `deploy/egress-destinations.yaml:138` · rule `CD-EGRESS-006: a destination is registered for a no-egress service` · *"…names service `cd-engine`, which declares policy 'NONE'. … a destination registered for one of them is a declaration that contradicts the criterion even before any allowlist names it."* |

### V23 — `V23-delete-the-registry.patch`

| | |
|---|---|
| **finding** | CD-ASR-F04 — a variant of this seat's own |
| **proposition attacked** | What does a deny-by-default guard do when the thing it denies against is gone? |
| **route** | Delete `deploy/egress-destinations.yaml` outright. The cheapest attack on any registry structure, and the one a hurried author actually makes. |
| **why it is a DIFFERENT route** | It attacks the **precondition** rather than the content. Nothing on the known set attacks a guard's dependency. Had the check read a missing registry as "nothing is registered, therefore nothing is wrong", the entire closure would be one `rm` away. |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |
| **observed refusal** | **exit 3**, `CD-RT-012-EGRESS-NO-BROKER: PRECONDITION_NOT_MET` · *"deploy/egress-destinations.yaml does not exist in this subject tree. … An absent registry must not read as an empty one: an empty registry is a decision somebody wrote down, and an absent one is a file somebody removed."* Non-zero with a stated reason, never a pass and never a skip (`PBG-CI-002`). |

### V24 — `V24-a-legitimate-destination-must-pass.patch` — **THE POSITIVE CONTROL. THIS ONE MUST PASS.**

| | |
|---|---|
| **finding** | CD-ASR-F04 — the false-positive obligation |
| **proposition attacked** | Does the closure forbid the product? A closure that does is not a closure. |
| **route** | `data.example.org`, operator `Example Data Ltd`, a real purpose, a `declared_in` clause, registered for `cd-collectors` — and named in `cd-collectors`' own allowlist. Exactly what a legitimate WO-3 ingredient source will look like once `CD-D-005` lands. |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |
| **observed** | **exit 0**, `PASS — 67 assertions, 0 violations`. **NOT a refusal, and that is the result being reported.** |
| **and it demonstrates the derivation** | The assertion count moves from **53** to **67** with the registry entry, because the guard's subject is **the artefact** and not a constant. Change the registry and the subject follows; there is no permitted host named anywhere in the script and there cannot be one. That is the `proof_standard`'s structural requirement, measured rather than argued. |
| **honest note** | Under V24 **two tests in `tests/test_egress_destination_registry.py` fail by design** — `test_wo2_registers_no_destination_at_all` and `test_no_service_names_any_host_in_its_allowlist` — because WO-2's declared state is an empty registry and both tests say so in their own docstrings. The **declared command** for this test id is the register check, and it exits 0. Disclosed rather than smoothed over. |

## Summary of what was refused by what — increment 3

| variant | route class | layer that refused it | exit |
|---|---|---|---|
| E05 | broker by IP literal in an allowlist | `CD-EGRESS-004` deny by default | **1** |
| V18 | registered, wrong service | `CD-EGRESS-004` service scoping | **1** |
| V19 | posture through an unread key | `CD-EGRESS-005` closed key set | **1** |
| V20 | register the address itself | `CD-EGRESS-006` positive host shape (+ `004`) | **1** |
| V21 | innocent host, broker operator | `CD-EGRESS-002` layer 2 on `operator` | **1** |
| V22 | registered for a no-egress service | `CD-EGRESS-006` service policy | **1** |
| V23 | delete the registry | precondition, fail closed | **3** |
| V24 | a legitimate destination | **none — it PASSES, by design** | **0** |

**Four honest observations about that table.** First, **no two rows are refused by the same
clause**, which is the spread this directory is supposed to show and is the opposite of a guard
fitted to a list. Second, **every row was written against the fix, not against the finding** —
the only spelling attack here is E05 itself, because a second spelling would be refused by the
same clause without adding a fact. Third, **layer 2 refused exactly one row** (V21) and that is
the honest measure of its worth: it is a floor, and the declared limit says so. Fourth, and it
is the row that should be read hardest, **nothing here proves a registered hostname reaches what
its operator claims** — that is boundary 2 of the declared limit and it reads **NOT PROVED TO BE
CARRIED ANYWHERE**, because detecting it needs the network and the network is prohibited. The
next auditor's strongest ground is a *lie in the registry*, and no variant in this directory
closes it.

## The one route this seat looked for and did NOT close

`extra_hosts:` on a service maps a name to an address in the container's `/etc/hosts`. It is
outside this check's subject and is declared as **boundary 5**, reading **NOT PROVED TO BE
CARRIED ANYWHERE**. It is raised against this seat's own work as `CD-ENG-WO2R-F12` and owed at
WO-3 with the egress lane. It is written here, in the exclusion set, rather than left for the
auditor to discover, because a route the implementing seat knows about and does not disclose is
worth less than one it never thought of.

---

# CD-PL-F59 (MEDIUM) — criterion CD-AC-012 — WO-2R increment **3b**

**Directory:** `variants/WO-2R/CD-ASR-F04/` (same finding, re-opened).
**Subject SHA these were generated against and run on:** the increment-3b lane head.
**Every patch below was generated with `git diff`, never by hand** (`CD-ENG-WO2R-F13`: a
hand-written hunk with a wrong line count is silently truncated by `git apply`, and six
variants once failed FOR THE WRONG REASON because of it). **Every row asserts the expected
RULE ID, not merely a non-zero exit**, for the same reason.

## What CD-PL-F59 is

Increment 3 closed the `hosts` allowlist under deny-by-default and it held against everything
— E05, V18..V24, and three fresh Project Lead probes. It left the **adjacent `pending` field**
carrying only layer 2, which is the layer `CD-ASR-F04` had already proved insufficient. The
Project Lead measured the consequence on pristine extractions of `b60d153`:

| probe | `pending` carries | result at `b60d153` |
|---|---|---|
| `PL-S3b` | `api.ibkr.com` | **REFUSED**, exit 1, `CD-EGRESS-002` |
| `PL-S3a` | `198.51.100.24` | **PASS**, exit 0, 53 assertions |
| `PL-S3c` | the same address on a `host:` key in a pending mapping | **PASS**, exit 0 |

That is `CD-ASR-F04` reproduced verbatim one field across. Under `CD-RULE-004` a guard closes
its class **or** declares its limit, and for `pending` increment 3 did **neither** — none of
its six boundaries mentioned the field — while boundary 4 asserted a compensating layer 1 that
did not exist for it (`CD-RULE-006`).

## The remedy chosen, and why

**Option (i): CLOSE.** Not option (ii). But *not* by mirroring `CD-EGRESS-004`'s registry onto
`pending`, which would be incoherent: a pending entry exists **because the host is unknown**,
so requiring it to name a registered destination is either unsatisfiable or forces an
engineering seat to invent the hostname this project deliberately recorded as owed
(`CD-RULE-003`, `PBG-AUTH-005`).

`CD-EGRESS-007` closes it from the field's own meaning instead. A pending entry is the record
of an **absence**: what authorises the future endpoint (`declared_in`) and why the host is not
written (`blocked_by`). **A host is precisely the thing it declares the absence of**, so the
key set is closed *by equality* and there is no field in a pending entry that can hold a
destination at all. `host:`, `endpoint:`, `url:`, `address:`, `target:` and every key nobody
has thought of fail the **same** clause, **without the value being examined**.

**Boundary 4 is corrected either way, as the dispatch required.** It is not softened; it is
made field-specific, each field naming its own layer-1 rule and the variant that measured it.

## Rows

### V25 — `V25-pending-through-a-yaml-alias.patch`

| | |
|---|---|
| **finding** | CD-PL-F59 — a variant of this seat's own |
| **proposition attacked** | Can `pending` be supplied through an indirection the reader does not expand, so the field reads as absent and the whole arm is skipped? |
| **route** | `pending: &smuggled` on `cd-store` carrying a bare `198.51.100.24`, aliased into `cd-collectors` as `pending: *smuggled`. |
| **why it is a DIFFERENT route from anything known** | It attacks the **precondition layer**, not the value layer. `PL-S2` aliased **`hosts`** — a name that *was* in the refusal filter's five-name enumeration — and correctly exited 3. `pending` was **not** in that enumeration, for the same reason it was in none of the boundaries, so the aliased field was read as a non-list and every assertion over it vanished. Nothing in PL-S3a/b/c or V18..V24 attacks an indirection. |
| **measured OPEN at `b60d153`** | **exit 0**, `PASS — 53 assertions, 0 violations`. Both the anchor site and the alias site were invisible. |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |
| **observed refusal** | **exit 3**, `PRECONDITION_NOT_MET` · *"a posture field is supplied through an unresolved YAML alias and this reader does not expand aliases: cd-collectors/x-egress/pending -> \*smuggled (line 427). Read literally the field would appear ABSENT, which is how a posture hides behind an indirection."* |
| **the point** | The fix is not "add `pending` to the list". The five-name list **was itself the enumeration defect** — a field added to the contract tomorrow would be aliasable and unrefused, exactly as `pending` was. The filter now covers the whole `x-egress` subtree at any depth. Strictly wider: nothing previously refused is now admitted, and `PL-S2` still exits 3. |

### V26 — `V26-pending-as-a-mapping-not-a-list.patch`

| | |
|---|---|
| **finding** | CD-PL-F59 — a variant of this seat's own |
| **proposition attacked** | Is the **container** of the field guarded, or only its contents? |
| **route** | `pending:` written as a **mapping** — `host: 198.51.100.24` alongside `declared_in:` and `blocked_by:` — rather than as a list. |
| **why it is a DIFFERENT route** | Every known-set row and all of `PL-S3a/b/c` keep `pending` a **list** and attack what is *in* it. This attacks its type. The guard reached the field through `isinstance(pending, list)` and nothing else, so any other type made the entire arm disappear. |
| **measured OPEN at `b60d153`** | **exit 0**, `PASS — 52 assertions, 0 violations`. **Read that number.** The count *dropped* from 53 to 52 — the guard did less work and still said PASS. A silently shrinking assertion count is the only trace a skipped arm leaves, and nobody was watching it. |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |
| **observed refusal** | **exit 1**, `FAIL — 1 violation(s)`. `deploy/compose.yaml:426` · rule `CD-EGRESS-007: pending is not a list` · *"service `cd-collectors` declares `pending` as a mapping; the contract admits a LIST and nothing else. An absent or differently typed `pending` is not an empty one — it is the whole field disappearing from this guard's reach."* |

### V27 — `V27-a-destination-beneath-an-admissible-key.patch`

| | |
|---|---|
| **finding** | CD-PL-F59 — a variant of this seat's own |
| **proposition attacked** | Once the key set is closed, can a destination hide in the **value position** beneath a key that *is* admissible? |
| **route** | `declared_in:` opening a nested mapping carrying `host: 198.51.100.24`. |
| **why it is a DIFFERENT route** | `PL-S3c` puts `host:` as a **sibling** key of the entry. This puts it **inside an admissible key's value**, where a key-set rule has no reason to look. |
| **measured OPEN at `b60d153`** | **exit 0**, `PASS — 53 assertions, 0 violations`. |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |
| **observed refusal** | **exit 1**, `FAIL — 1 violation(s)`. `deploy/compose.yaml` · rule `CD-EGRESS-007: a pending entry's key set is not the declared key set` · *"pending entry #0 declares unknown key(s) `host` and misses nothing. … A HOST IS THE ONE THING A PENDING ENTRY CANNOT CARRY."* |
| **honest note — it is refused by a clause other than the one it was aimed at** | The stdlib subset reader **flattens** a nested mapping: `{'declared_in': None, 'host': '198.51.100.24', 'blocked_by': …}`. So at the reader level V27 collapses into `PL-S3c`'s shape and the key-set clause catches it, rather than the non-empty-scalar clause it was written for. The refusal is correct and the rule id is asserted, but **the route is narrower than it looks** and an auditor should not read it as evidence that value-position attacks are covered in general. Raised against this seat's own work as `CD-ENG-WO2R-F15`. |

### V28 — `V28-a-legitimate-pending-entry-must-pass.patch` — **POSITIVE CONTROL. THIS ONE MUST PASS.**

| | |
|---|---|
| **finding** | CD-PL-F59 — the false-positive obligation, and the subject-derivation proof for `pending` |
| **proposition attacked** | Does the closure forbid the product? Does the guard's subject follow the artefact for `pending`, or only for `hosts`? |
| **route** | An **eighth** service, `cd-atlas`, policy ALLOWLIST, empty `hosts`, and a well-formed `pending` entry declaring exactly `declared_in` and `blocked_by`. |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |
| **observed** | **exit 0**, `PASS — 79 assertions, 0 violations`. **NOT a refusal, and that is the result being reported.** |
| **and it demonstrates the derivation** | `scanned:` moves **7 → 8 services** and assertions move **69 → 79**. The pending arm's subject is the artefact, not a constant: there is no service name and no permitted shape instance written anywhere in the script. |
| **and the real entries still pass** | The three genuine `pending` entries in this project — `cd-collectors`, `cd-witness`, `cd-review`, each recording an endpoint BLUEPRINT §2 owes and the decision that blocks it — pass unchanged. The closed key set **is the shape they already had**, formalised; no new shape was imposed on the product. |

### V29a — `V29a-an-address-in-pending-prose-ESCAPES.patch` — **THIS ONE IS NOT REFUSED**

| | |
|---|---|
| **finding** | CD-PL-F59 — **the declared residue**, boundary 7's executable example |
| **proposition attacked** | Does `CD-EGRESS-007` close everything, or only the entry's *fields*? |
| **route** | `blocked_by: "CD-D-005; the source will be 198.51.100.24 once ruled"` — the key set is exactly right, both values are non-empty scalars, and the address rides in the prose. |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |
| **observed** | **exit 0**, `PASS — 69 assertions, 0 violations`. **NOT REFUSED. It escapes, and it is written here in the same words as the rows that do not.** |
| **why it is not closed** | Closing it would mean recognising which text tokens look like network endpoints — the spelling recognition that `CD-ASR-F04` and `CD-PL-F59` **both are**. It is boundary 3 (`purpose` prose) drawn again for the same reason. |
| **which layer carries it** | For an **address literal in prose: NOT PROVED TO BE CARRIED ANYWHERE** (`CD-RULE-006`). The argument that a pending entry now has no host-bearing field, so an address in prose is a *mention* and not a *declaration*, is recorded in the boundary **as an argument and explicitly not as a layer** — because `CD-RULE-006` admits only layers that were run. |

### V29b — `V29b-a-broker-name-in-pending-prose.patch` — the measured half of boundary 7's hand-off

| | |
|---|---|
| **finding** | CD-PL-F59 — the "PARTIALLY CARRIED, MEASURED" half of boundary 7 |
| **proposition attacked** | Is the prose residue *total*, or does layer 2 still reach into it? |
| **route** | The identical sentence as V29a with `api.ibkr.com` in place of the address. |
| **command** | `python3 tools/register/check_egress_no_broker.py --root .` |
| **observed refusal** | **exit 1**, `FAIL — 1 violation(s)` · rule `CD-EGRESS-002: a pending entry names a broker host` · *"…names `api.ibkr.com`, and ibkr.com is a known broker, exchange or order-routing operator. It carries no concept word at all, which is precisely why a vocabulary rule alone would let it through."* |
| **the point** | V29a and V29b are the **same sentence** differing only in the endpoint, and one is refused and one is not. That pair is the measurement boundary 7 rests on, and it is the reason the boundary says *partially* carried rather than carried. |

### V30 — `V30-a-document-shape-that-never-returns.patch` — **THIS ONE RETURNS NO VERDICT AT ALL**

| | |
|---|---|
| **finding** | `CD-ENG-WO2R-F14` — boundary 8's executable example. Raised against this seat's own work and **escalated, not fixed**. |
| **proposition attacked** | What does the guard do on a document it cannot parse — refuse, or never answer? |
| **route** | `declared_in:` opening a nested **block sequence** in `cd-collectors`' `pending`. Minimal reproducer, independent of this check: the three lines `top:` / `  - key:` / `      - nested`. |
| **command** | `timeout 30 python3 tools/register/check_egress_no_broker.py --root .` |
| **observed** | **exit 124** — **the check DOES NOT TERMINATE** and is killed by the timeout. `tools/register/_yamlmin.py` enters an infinite loop on a block sequence opened by the **first** key of a block-sequence item. 124 is not one of the four declared exit codes. |
| **is it a false clean?** | **No.** The check never reports PASS. But non-termination is not a *stated refusal* either, and a gate that hangs is a gate somebody eventually disables. **NOT PROVED TO BE CARRIED ANYWHERE.** |
| **pre-existing, and why it was not fixed here** | It reproduces identically at `ee8be6b`, the WO-2R dispatch base, before any of this seat's work. The reader is shared with `tools/register/check_base_image_digest_pin.py`, so repairing it changes the behaviour of a guard this dispatch does not cover, and this dispatch is bounded to `CD-PL-F59`. Widening scope silently is prohibited; it is escalated instead. |

## The Project Lead's probes, re-run at increment 3b

Given to this seat rather than withheld (`CD-D-047`). **From the moment they were committed
they prove nothing about the class** and they are part of the exclusion set. They are recorded
here with their observed outcome so the next auditor can avoid them.

| probe | route | at `b60d153` | at increment 3b |
|---|---|---|---|
| `PL-S1` | an EIGHTH service with a broker allowlist | exit 1, `CD-EGRESS-004` + `CD-EGRESS-002`, `scanned:` 7→8 | **exit 1**, same two rules, `scanned:` 7→8, assertions 77 |
| `PL-S2` | a YAML anchor aliased into `hosts` | exit 3 | **exit 3**, `PRECONDITION_NOT_MET` |
| `PL-S3a` | `198.51.100.24` as a bare `pending` entry | **exit 0, PASS 53 — ESCAPED** | **exit 1**, `CD-EGRESS-007: a pending entry is not a declaration of an omission` |
| `PL-S3b` | `api.ibkr.com` in the same slot | exit 1, `CD-EGRESS-002` | **exit 1**, and now by **BOTH** layers: `CD-EGRESS-007` **and** `CD-EGRESS-002` |
| `PL-S3c` | the address on a `host:` key in a pending mapping | **exit 0, PASS 53 — ESCAPED** | **exit 1**, `CD-EGRESS-007: a pending entry's key set is not the declared key set` |
| `PL-S4` | a duplicate `hosts:` key | exit 1, `CD-EGRESS-004` | **exit 1**, `CD-EGRESS-004` on the last-wins value |

## Summary of what was refused by what — increment 3b

| variant | route class | layer that refused it | exit |
|---|---|---|---|
| V25 | `pending` through a YAML alias | precondition, x-egress subtree | **3** |
| V26 | `pending` as a mapping, not a list | `CD-EGRESS-007` container type | **1** |
| V27 | a destination beneath an admissible key | `CD-EGRESS-007` closed key set | **1** |
| V28 | a legitimate pending entry | **none — it PASSES, by design** | **0** |
| V29a | an address in pending **prose** | **none — IT ESCAPES. Boundary 7.** | **0** |
| V29b | a broker **name** in pending prose | `CD-EGRESS-002` layer 2 | **1** |
| V30 | a document shape the reader loops on | **none — NO VERDICT AT ALL. Boundary 8.** | **124** |

**Three honest observations.** First, **two of the seven rows are not refused and one of those
returns no verdict at all**, and both are written up in the same detail as the refusals,
because a variant this seat tried and did not close is worth more to the next auditor than one
it did. Second, **V27 is refused by a clause other than the one it was aimed at**, because the
reader flattens nesting — disclosed as `CD-ENG-WO2R-F15` rather than presented as a cleaner
result than it is. Third, **`PL-S3b` is now refused by both layers where it used to be refused
by one**, which is the property `hosts` gained at increment 3 and is the only real test of
whether the two layers over `pending` are independent.

## Correction to the increment-3 record: V24's numbers moved

`V24`'s row above records **`PASS — 67 assertions`** and the derivation **53 → 67**. Those were
correct at `b60d153` and are **no longer the numbers you will observe**: `CD-EGRESS-007` adds
assertions over `pending` on every service, so at increment 3b the clean arm is **69** and V24
is **`PASS — 83 assertions`**. The row is not rewritten — the derivation it demonstrates is
unchanged and the observation stands as made at its own SHA — and this note supersedes its two
numbers rather than editing them (`PBG-CONT-003`).
