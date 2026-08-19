# VARIANT MANIFEST — WO-2R2, crash-detector

**Seat:** `CD-ENG-WO2R2-01` (ENGINEER) · **Dispatch:** `CD-DISPATCH-WO2R2-ENGINEER` ·
**Authority:** `CD-AUTH-0001` · **Scope:** `PO-DECISIONS-0002` (CD-D-073).

**THIS SEAT DOES NOT CERTIFY THIS WORK** (`PBG-SOD-001`, non-waivable). Everything below is
IMPLEMENTATION EVIDENCE. It does not become assurance by being thorough, and the last two
seats' evidence was thorough.

---

## FOR THE THIRD ASSURANCE SEAT — READ THIS FIRST

You were dispatched with an exclusion set so that you can avoid routes that have already
been walked. **These four are now part of it.** From the moment you read them they prove
nothing about any class: they are a regression floor and a list of roads not to re-drive.

Two things in here are worth more to you than the three refusals:

1. **`CD-ENG-WO2R2-V05` IS NOT REFUSED.** It is an OPEN route through the product's own
   declared extension point, written and measured by the seat whose closure it defeats. No
   guard was built for it, deliberately, and the reasoning is in its row. If you are looking
   for where CD-AC-002 is still soft, start there and do not spend your budget rediscovering
   it.
2. **The static layer refused none of the first three at runtime and never will.**
   `check_no_blend` was PASS with `V01` present, PASS with `V03` present, and PASS with
   `V05` present. It reported `V04` only because that variant happens to *name* a door. Do
   not read a `check_no_blend` exit code as evidence about this class in either direction.

---

## HOW TO RE-RUN ANY ROW (extraction hygiene, `PBG-RT-001`)

Never mutate a governed worktree and never create a git worktree for a variant. One
pristine extraction per variant, discarded afterwards.

```
SHA=<the increment SHA in the row>
T=$(mktemp -d)
git -C /srv/crash-detector-wo2 archive "$SHA" | tar -x -C "$T"
cd "$T" && git apply -p1 /srv/crash-detector-wo2/variants/WO-2R2/CLASS-1/<row>.patch
# then the row's own command
```

`python3 -B` everywhere, so no `__pycache__` is written into any governed tree.

**NOTHING IN THIS DIRECTORY IS EXECUTABLE.** Every artefact is a `git apply`-able patch,
mode 0664, no symlink, no wrapper, no runner (`PBG-ASSURE-001`). Each row carries its driver
as a fenced block of DATA rather than as a file, for the same reason.

---

## THE ROWS

### CD-ENG-WO2R2-V01 — ASR2-002-A RENAMED AND ALIASED. *THE RENAME TEST, EXECUTED.*

| | |
|---|---|
| class | CLASS 1 — ADMISSION IS VALIDATION |
| patch | `CLASS-1/CD-ENG-WO2R2-V01-asr2-002-a-renamed-and-aliased.patch` |
| lands at | `src/crash_detector/publication/operator_panel.py` (inside the scanned set) |
| measured at | `1cd15b2c9bf319fa044a9043582148b19944e763` |

**PROPOSITION ATTACKED.** That the refusal recorded against `ASR2-002-A` is a property of
the CLASS and not of a set of NAMES.

**ROUTE, AND WHY IT DIFFERS FROM BOTH CORPORA.** It is `ASR2-002-A` with every identifier
changed — module, function, every local — and the door imported under an alias
(`combine_within_one_dial as fold_readings`). It exists because `CD-PL-F74` measured
`PL-R5` going from FAIL-2-violations to PASS-0-violations with **nothing changed but the
door name**, and that inference cost the second gate. `CD-D-073` makes the rename test a
delivery obligation, so it is discharged by EXECUTION here rather than asserted in prose.

**COMMAND.**

```
python3 -B tools/register/check_no_blend.py --root .
PYTHONPATH=src python3 -B -c "<the driver below>"
```

```python
from crash_detector.dials.magnitude import DialMagnitude
from crash_detector.dials.provenance import observed_for_dial
from crash_detector.publication.operator_panel import panel_figure
def mag(d, v):
    return DialMagnitude(dial_id=d, quantity=observed_for_dial(dial_id=d, quantity=v, inputs_used=('src',)))
panel_figure([mag('equity_crash', 0.9), mag('monetary_debasement', 0.1)])
```

**OBSERVED.** `check_no_blend` → **EXIT 0, PASS — 4984 assertions, 0 violations**. Runtime →
**REFUSED**, `crash_detector.dials.provenance.UndeclaredReduction: a function was offered as
a reduction. A derivation is named, never supplied ...`

**REFUSING LAYER AND ITS SCOPE.** `crash_detector.dials.provenance.derived_within_one_dial`,
at runtime, by `type(reduction) is not SameDialReduction`. **Scope:** every call to the
derivation door in the process, from any module, inside or outside any scanned set, reached
by any name or under any alias. It is an exact-type comparison of the object the door was
handed; it reads no source, no registry and no module path.

**RENAME TEST.** **SURVIVES — and this row IS the measurement.** The refusal is byte-identical
to the one `ASR2-002-A` produces with its original names.

---

### CD-ENG-WO2R2-V03 — REWRITE THE REDUCTION TABLE THE DOOR TRUSTS

| | |
|---|---|
| class | CLASS 1 — ADMISSION IS VALIDATION |
| patch | `CLASS-1/CD-ENG-WO2R2-V03-rewrite-the-reduction-table-the-door-trusts.patch` |
| lands at | `src/crash_detector/publication/console_total.py` (inside the scanned set) |
| measured at | `1cd15b2c9bf319fa044a9043582148b19944e763` |

**PROPOSITION ATTACKED.** That a door which computes the number ITSELF is safer than one
that accepts a number — i.e. the whole of increment 1a's structural claim.

**ROUTE, AND WHY IT DIFFERS FROM BOTH CORPORA.** It is not a laundering route at all, and
the structure it attacks did not exist before this increment. Every variant in both corpora
tries to get a number PAST a door. This one **accepts the refusal** and then installs the
attacker's callable INTO the table of reductions the door executes:
`SAME_DIAL_REDUCTIONS[SameDialReduction.MEAN] = lambda _values: conveyed`. Had it worked,
every refusal in the closure would still have fired correctly and would then have run the
attacker's code with the door's own blessing — the number would have been computed "by the
module", from quantities the module established, and no provenance comparison anywhere would
have had anything to complain about. Written by this seat against its own seam
(`PBG-ASSURE-017`).

**COMMAND.** As V01, importing `console_total` from
`crash_detector.publication.console_total`.

**OBSERVED.** `check_no_blend` → **EXIT 0, PASS — 4989 assertions, 0 violations**. Runtime →
**REFUSED**, `TypeError: 'mappingproxy' object does not support item assignment`.

**REFUSING LAYER AND ITS SCOPE.** The **CPython interpreter**, on a `types.MappingProxyType`.
**Scope:** every attempt to write to that mapping, by any module, by any spelling of the
assignment. Its own residue is declared: the underlying dict is consumed by the proxy at
module level and never bound to a name, so it cannot be reached by NAME — but
`gc.get_referents(SAME_DIAL_REDUCTIONS)` returns it, and no Python-level structure can
prevent that. **That residue is NOT claimed to be carried anywhere at runtime**, and it is
the same fact already declared for `object.__setattr__` in this package's headers.

**RENAME TEST.** **SURVIVES.** The refusal is raised by the interpreter on the object's own
type; no identifier in the attacking module participates in it.

---

### CD-ENG-WO2R2-V04 — DUCK-TYPE THE PROVENANCE CARRIER

| | |
|---|---|
| class | CLASS 1 — ADMISSION IS VALIDATION (and the CLASS 2 doctrine on this operand) |
| patch | `CLASS-1/CD-ENG-WO2R2-V04-duck-typed-provenance-carrier.patch` |
| lands at | `src/crash_detector/publication/carried_figure.py` (inside the scanned set) |
| measured at | `1cd15b2c9bf319fa044a9043582148b19944e763` |

**PROPOSITION ATTACKED.** That "a value carrying an established provenance" is decided by
what a value IS and not by what it can DO.

**ROUTE, AND WHY IT DIFFERS FROM BOTH CORPORA.** Both corpora duck-type OUTCOMES and
READINGS — `test_an_outcome_that_merely_looks_like_ok_is_not_accepted_as_one` exists because
of one such finding, and `ASR2-005-A` duck-types a timestamp. **Nothing in either corpus
duck-types the provenance carrier**, because until this increment the derivation door took a
bare `float` and there was no carrier to imitate. The imitation is faithful: `dials` is a
real `frozenset` naming one real dial and `value_for` honours the same set-equality contract
the genuine article honours. A second arm does the same with a `float` SUBCLASS, which is
the CLASS 2 doctrine — "a subclass of a number is not a number" — applied to this operand
before an auditor has to apply it for us.

**COMMAND.** As V01, importing `carried_figure` and `carried_number` from
`crash_detector.publication.carried_figure`.

**OBSERVED.** Runtime, both arms → **REFUSED**,
`crash_detector.dials.provenance.QuantityProvenanceMissing: a CarriedFigure was offered for
derivation ...` and `... a CarriedNumber was offered for derivation ...`.

`check_no_blend` → **FAIL, 3 violations** — but read that correctly: it reports this variant
only because the variant happens to NAME `derived_within_one_dial`, which is RULE 4's
vocabulary. That is a coincidence of spelling, not a class result, and it is **not** what
refuses the variant.

**REFUSING LAYER AND ITS SCOPE.** `crash_detector.dials.provenance.derived_within_one_dial`,
at runtime, by `type(offered) is not DeclaredQuantity`. **Scope:** every value offered for
derivation, in the process, from anywhere, however faithfully it imitates the interface.

**RENAME TEST.** **SURVIVES** for the runtime refusal — exact-type identity does not consult
a name. **DOES NOT SURVIVE** for the `check_no_blend` FAIL: rename `derived_within_one_dial`
at both ends and RULE 4 goes silent while the runtime refusal is unchanged. Labelled a
VOCABULARY result, and it is the clearest side-by-side demonstration in this manifest of why
the two must never be confused.

---

### CD-ENG-WO2R2-V05 — A STATEFUL `ContributionModel` SHARED BY BOTH `DialSpec`s

> ## *** NOT REFUSED. THIS ROUTE IS OPEN. ***
> Recorded by the seat that wrote the closure it defeats. **No guard was built for it, and
> that is a decision, not an oversight** — see WHY NO GUARD below.

| | |
|---|---|
| class | CLASS 1 — ADMISSION IS VALIDATION (the external base case) |
| patch | `CLASS-1/CD-ENG-WO2R2-V05-stateful-model-shared-by-both-dials.patch` |
| lands at | `src/crash_detector/engine/carrying_model.py` (inside the scanned set, on the DIAL PATH) |
| measured at | `1cd15b2c9bf319fa044a9043582148b19944e763` |

**PROPOSITION ATTACKED.** CD-AC-002 itself: "the two dials are never blended". And, one
level down, the sentence this package has carried since `CD-PL-F54` — that `observed_for_dial`
"believes what it is told" but that a caller wanting a blend admitted must write an explicit
false statement in source.

**ROUTE, AND WHY IT DIFFERS FROM BOTH CORPORA.** Every variant in both corpora attacks the
dial types from OUTSIDE the product's declared flow — a helper, a publication module, a
serving module, a reflection route, a subclassed timestamp, a re-wrapped `repr`. **This one
attacks from INSIDE it, at the product's own declared extension point.**
`DialSpec.contribution_model` is injected, and `evaluate` calls
`spec.contribution_model.compute(payloads)` once per dial with THAT DIAL'S payloads only —
a separation that is real and that this variant does not break. It breaks the *other*
assumption: that the model is pure. `ContributionModel`'s own docstring says
*"Contract: **pure**. No I/O, no clock, no configuration read from the environment"*, and
nothing enforces it. One model object given to BOTH dial specs sees both dials' figures one
at a time and returns the mean as the second dial's magnitude.

**WHAT IT DOES NOT DO, WHICH IS WHY IT MATTERS.** It launders nothing. It names no admission
door outside a declared site. It touches no private slot, defines no dunder, performs no
arithmetic on a magnitude, and never holds both dials in one expression. Its
`observed_for_dial` claim is made from `evaluate.py` — the ONE declared product admission
site — and **every field of that claim is true**: the dial is right, and the cited inputs
were genuinely present and genuinely used. The only thing wrong is the number, and the
number is the one thing a base case cannot check.

**COMMAND.**

```
python3 -B tools/register/check_no_blend.py --root .
python3 -B tools/register/check_no_numeric_default.py --root .
PYTHONPATH=src python3 -B -m pytest tests -q -p no:cacheprovider
PYTHONPATH=src python3 -B -c "<the driver below>"
```

```python
from datetime import datetime, timedelta, timezone
from crash_detector.dials.dialset import EQUITY_DIAL_ID, MONETARY_DIAL_ID
from crash_detector.engine.carrying_model import CarryingModel
from crash_detector.engine.config import ConfigSnapshot, DialSpec
from crash_detector.engine.evaluate import evaluate
from crash_detector.observations import OK, ObservationRecord
from crash_detector.publication.dial_scalar import number_for_dial_slot
from crash_detector.source_registry import Criticality, SourceRecord, SourceRegistry

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)
model = CarryingModel()                     # ONE object, given to BOTH specs
config = ConfigSnapshot(
    config_snapshot_id="cfg-v05",
    dial_specs=(
        DialSpec(dial_id=EQUITY_DIAL_ID, required_input_ids=("src.e",),
                 contributing_input_ids=(), contribution_model=model),
        DialSpec(dial_id=MONETARY_DIAL_ID, required_input_ids=("src.m",),
                 contributing_input_ids=(), contribution_model=model),
    ),
    staleness_window_seconds=600.0,
    source_registry=SourceRegistry((
        SourceRecord(source_id="src.e", adapter_id="a.e", cadence_seconds=60,
                     criticality=Criticality.REQUIRED, stands_for="e"),
        SourceRecord(source_id="src.m", adapter_id="a.m", cadence_seconds=60,
                     criticality=Criticality.REQUIRED, stands_for="m"),
    )),
)
def ok(sid, figure):
    return ObservationRecord(source_id=sid, observed_utc=NOW,
        outcome=OK(payload={"figure": figure}, source_as_of_utc=NOW - timedelta(seconds=5)))

dials = evaluate([ok("src.e", 0.9), ok("src.m", 0.1)], config, NOW)
print(number_for_dial_slot(MONETARY_DIAL_ID, dials.monetary.value.score))
```

**OBSERVED — EVERY DECLARED LAYER GREEN WITH IT PRESENT.**

```
CD-RT-002-AST-NO-BLEND            EXIT 0   PASS — 5002 assertions, 0 violations
CD-RT-001-AST-NO-NUMERIC-DEFAULT  EXIT 0   PASS —  397 assertions, 0 violations
WHOLE SUITE                       EXIT 0   1333 passed

the model saw        : [0.9, 0.1]
equity   reading     : Value | DialMagnitude(dial_id='equity_crash', quantity=0.9)
monetary reading     : Value | DialMagnitude(dial_id='monetary_debasement', quantity=0.5)
monetary inputs_used : ('src.m',)
PUBLICATION GATE     : *** NOT REFUSED *** -> 0.5
IS IT THE BLEND?     : True
```

Equity 0.9 and monetary 0.1 are published as a **monetary reading of 0.5**.

**REFUSING LAYER AND ITS SCOPE.** **NONE. NOT PROVED TO BE CARRIED ANYWHERE**
(`CD-RULE-006`). Measured, not reasoned: no runtime layer refused it and no static layer
reported it.

**RENAME TEST.** Not applicable — there is no refusal to rename-test. Stated rather than
omitted, so that the absence is visible on the row's face.

**WHY NO GUARD WAS BUILT, AND WHY THAT IS THE HONEST ANSWER.**

* An identity check refusing one model OBJECT shared between two `DialSpec`s is a
  one-line change and would refuse exactly this file. It is defeated by two instances of the
  same class sharing a class attribute. That is the instance game for the third time on this
  project, and both the auditor and the Product Owner named it in writing.
* A purity probe — call `compute` twice and compare — catches this file and is defeated by a
  model that memoises on its payloads. It is a heuristic, it doubles the cost of every
  evaluation, and it would be a fourth clever guard over a hole it does not close.
* Deciding whether a caller-supplied model is pure is **not decidable at this altitude.**

**Closing it is an architectural change, not a guard:** the system would have to compute dial
magnitudes from source payloads itself rather than delegating to a caller-supplied model.
That is `BLUEPRINT §7` / `CD-D-005` territory, it is owed to the Product Owner, and it is
raised to the Project Lead as such. `PO-DECISIONS-0002` states that escalating a structural
impossibility is worth more than another guard; this row is that escalation, with the
measurement attached.

---

## WHAT IS DELIBERATELY NOT HERE

* **No variant for `CD-AC-005` / CLASS 2 and none for `CD-AC-012` / ITEM 3.** This launch is
  bounded to increment 1. Increments 2 and 3 are re-dispatched after the Project Lead
  reconciles this one, and their variants land beside these under the same tree.
* **No `V02`.** It was drafted as a forged-provenance arm (`object.__setattr__` making a
  magnitude's label and its carried quantity disagree) and then **withdrawn as a new
  variant**, because `object.__setattr__` on a private slot is already `V17` / `PL-W5` in the
  exclusion set and re-driving a known road is not a new route. It was still MEASURED as a
  regression — refused by `_install`'s set-equality comparison, `CrossDialCombination: a
  quantity declared for ['equity_crash'] was offered as dial 'monetary_debasement''s
  magnitude` — and the id is left unused rather than reassigned, so no reader has to wonder
  what happened to it.
* **No runner, no wrapper, no shell script, no executable bit** (`PBG-ASSURE-001`).
