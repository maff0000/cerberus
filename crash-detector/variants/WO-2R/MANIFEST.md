# WO-2R variant plants — MANIFEST

**Dispatch:** `governance/dispatch/CD-DISPATCH-WO2R-ENGINEER.yaml`, increment 1.
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

## Increments 2 to 6 are not represented here

This file covers **increment 1 only** (CD-ASR-F02 and CD-ASR-F03). Variants for CD-ASR-F01,
F04, F05 and F06 are owed by the later increments of the same dispatch and their absence here is
not a claim about them.
