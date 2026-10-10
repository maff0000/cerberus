# VARIANT MANIFEST — WO-2R2, crash-detector

**Seat:** `CD-ENG-WO2R2-01` (ENGINEER) · **Dispatch:** `CD-DISPATCH-WO2R2-ENGINEER` ·
**Authority:** `CD-AUTH-0001` · **Scope:** `PO-DECISIONS-0002` (CD-D-073).

**THIS SEAT DOES NOT CERTIFY THIS WORK** (`PBG-SOD-001`, non-waivable). Everything below is
IMPLEMENTATION EVIDENCE. It does not become assurance by being thorough, and the last two
seats' evidence was thorough.

---

## FOR THE THIRD ASSURANCE SEAT — READ THIS FIRST

You were dispatched with an exclusion set so that you can avoid routes that have already
been walked. **These FOURTEEN are now part of it** — four for CLASS 1 at increment 1, five for
CLASS 2 at increment 2, and five for `CD-AC-012` at increment 3. (This sentence read "these
four" when increment 1 wrote it and "these NINE" when increment 2 corrected it; it is corrected
AGAIN here rather than left to mislead, and each correction is disclosed rather than made
silently — `PBG-CONT-003`. **This is exactly the `CD-PL-F75` shape**: a declaration that
announced FOUR and then listed FIVE, because a consistency check over what a seat ADDED cannot
see what that seat made STALE. Increment 3 grepped the whole declaration rather than its own
delta, which is how this sentence and the index row above it were found.) From the moment you
read them they prove nothing about any class: they are a
regression floor and a list of roads not to re-drive.

**FOR CLASS 2, THE THREE THINGS WORTH MOST TO YOU ARE NOT THE REFUSALS:**

1. **`CD-ENG-WO2R2-V10` IS MEASURED OPEN**, at the audited base AND at the closure. A
   `tzinfo` that reports a false offset moves the instant, and CPython bounds it to under 24
   hours — which is 96x the 900-second window ceiling. A row whose stated wall clock is 22
   hours old renders `WITNESS AGREES`. It is this seat's own declared boundary 1, driven as
   an attack, and it is raised as a finding against this seat's own closure.
2. **`CD-ENG-WO2R2-V09`'s PREMISE IS REFUTED, and the row says so.** It was written to show a
   `timedelta` subclass controlling the offset subtraction. It does not, at any arm,
   including a counterfactual arm with this seat's own rebuild REMOVED. A route this seat
   predicted and could not demonstrate is recorded as such rather than quietly dropped.
3. **`CD-ENG-WO2R2-V08` IS REFUSED AT BOTH SHAs AND FOR DIFFERENT REASONS**, which is
   `CD-PL-F74` in one row: at `50fc231` it was refused by an accident of what it did not
   override, and at the closure by the descriptor read. The counterfactual arm proves which.

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
cd "$T" && git apply -p1 /srv/crash-detector-wo2/variants/WO-2R2/<CLASS-1|CLASS-2>/<row>.patch
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

# CLASS 2 — JUDGE VALUES, NEVER TYPES. Increment 2.

**THE CLASS, AS THE PRODUCT OWNER STATED IT AND AS THESE ROWS ATTACK IT:** *any judgement
this system makes that delegates its deciding operation to an object the system did not
construct.* Not "datetime subclasses". The five rows below attack it at five different
levels — the label, the mapping key, the timestamp's own fields, the offset's arithmetic,
and the timezone that reports the offset — and **two of them are not refusals**.

**INCREMENT SHA for every CLASS 2 row: the commit that lands this manifest, on branch
`wo-2-skeleton`.** The base each row is contrasted against is `50fc231`, the audited tree,
and `7ac1574`, the lane head this increment started from.

## THE CLASS 2 ROWS

### CD-ENG-WO2R2-V06 — THE PANEL STATE LABEL FORGES AGREEMENT. *No timestamp involved.*

| | |
|---|---|
| class | CLASS 2 — JUDGE VALUES, NEVER TYPES |
| patch | `CLASS-2/CD-ENG-WO2R2-V06-panel-state-label-forges-agreement.patch` |
| proposition attacked | CD-AC-005: there is no input — missing, stale, malformed or defaulted — from which the serving layer produces AGREES |
| route | A `str` SUBCLASS supplied as `PanelRow.state`. `resolve_panel` selects the panel constructor with `row.state == _STATE_AGREES`, and `==` is the LEFT operand's to define. The row's stored state is `UNAVAILABLE` — the witness feed is DEAD — and it compares equal to `"AGREES"`. |
| why it is a DIFFERENT route from both corpora | Neither corpus attacks the DISCRIMINATOR. The WO-2 corpus attacks CD-AC-005 through window width (E07), exception handlers (E08), rendering maps, fast paths (V50) and `object.__setattr__` (PL-W5); ASR2-005-A attacks the TIMESTAMP. **This row involves no timestamp at all**: the row is fresh, the window is ordinary, and `FreshnessEvidence`'s constructor runs and succeeds honestly. It reaches the Product Owner's forbidden sentence without going anywhere near the thing F02 was about, which is the point of it — it is the same CLASS by a road with no clock on it. |
| MEASURED at `50fc231` | **OPEN.** `stored state repr: 'UNAVAILABLE' type: FeedState` → `resolved: Agrees` → `RENDERS: WITNESS AGREES`. |
| MEASURED at the closure | **REFUSED.** `stored state repr: 'UNAVAILABLE' type: str` → `Unavailable(reason='WITNESS_FEED_UNREACHABLE')` → `WITNESS UNAVAILABLE`. It does not raise; it reports the truth the row carried, which is what "fail closed, not fail silent" asks for. |
| THE REFUSING LAYER, NAMED AND SCOPED (`CD-PL-F74`) | `crash_detector.serving.witness_resolver.PanelRow.__post_init__`, at runtime, via `crash_detector.own_terms.own_str`, which returns `str.__str__(value)` — a copy of the object's own code points. **SCOPE:** every `PanelRow` constructed anywhere in the process, from any module, under any name. It is a re-construction of the VALUE, not a test of it: no property of the supplied object is consulted after the copy, so the scope does not depend on which comparisons exist downstream. |
| exception type / message | **NONE — and that is deliberate.** There is no exception. The refusal is that the forged label stops being able to answer, so the resolver reaches the branch the row's real content selects. |
| THE RENAME TEST | **SURVIVES.** `own_str` consults no identifier — not the class's name, not the module's, not the field's. Renaming `FeedState`, `feed_state` and the module changes nothing about which code points `str.__str__` copies. |

```python
# DRIVER — data, not a file under variants/ (PBG-ASSURE-001). Write it to /tmp and run it
# from the root of a pristine extraction with the patch applied.
import sys, os; sys.path.insert(0, os.path.join(os.getcwd(), "src"))
from datetime import datetime, timezone
from crash_detector.serving.feed_state import feed_state
from crash_detector.serving.witness_resolver import PanelRow, resolve_panel, render_panel
NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)
row = PanelRow(state=feed_state("UNAVAILABLE"), as_of_utc=NOW, published_utc=NOW,
               measures={"divergence_measure": 0.01})
print("stored state repr:", repr(row.state), "type:", type(row.state).__name__)
p = resolve_panel(row, now_utc=NOW, staleness_window_seconds=600.0)
print("resolved:", type(p).__name__, getattr(p, "reason", ""), "| RENDERS:", render_panel(p))
```

---

### CD-ENG-WO2R2-V07 — A MEASURE KEY ANSWERS TO A NAME IT DOES NOT HOLD.

| | |
|---|---|
| class | CLASS 2 — JUDGE VALUES, NEVER TYPES |
| patch | `CLASS-2/CD-ENG-WO2R2-V07-measure-key-answers-to-another-name.patch` |
| proposition attacked | CD-AC-005, and specifically the `PANEL_ROW_INCOHERENT` route: a row whose measurements are missing must not become agreement |
| route | A `str` SUBCLASS used as a KEY of `PanelRow.measures`, with `__hash__` returning `hash("divergence_measure")` and `__eq__` returning `True`. `_finite_measure` asks `key not in row.measures` and then indexes it, and BOTH are decided by the STORED key's `__hash__` and `__eq__`, not by ours. A row carrying only a column called `some_other_column` therefore supplies the divergence measure. |
| why it is a DIFFERENT route from both corpora | It attacks the CONTAINER rather than the value. No variant in either corpus touches a mapping key; the closest, ASR2-005-A, attacks the value's type. This is one level of indirection out — the object that decides WHICH value is read, rather than the value. `PANEL_ROW_INCOHERENT` is one of the six declared routes to Unavailable and this is a route that silently removes it. |
| MEASURED at `50fc231` | **OPEN.** `stored keys: [("'some_other_column'", 'FeedKey')]` → `resolved: Agrees` → `RENDERS: WITNESS AGREES`. A row with no divergence measure at all rendered as agreement. |
| MEASURED at the closure | **REFUSED.** `stored keys: [("'some_other_column'", 'str')]` → `Unavailable(reason='PANEL_ROW_INCOHERENT')` → `WITNESS UNAVAILABLE`. |
| THE REFUSING LAYER, NAMED AND SCOPED | `crash_detector.serving.witness_resolver.PanelRow.__post_init__`, at runtime: the `measures` mapping is rebuilt as `{own_str(key): value ...}`, so every stored key is a plain `str` hashed by CPython's own `str.__hash__`. **SCOPE:** every `PanelRow` in the process. A key that cannot be re-established as a `str` is REFUSED at construction with `TypeError: every PanelRow.measures key must be a str` rather than kept — a key this system cannot re-establish is a key whose hashing it does not control. |
| exception type / message | No exception on this arm: the forged key is neutralised and the resolver reaches the honest `PANEL_ROW_INCOHERENT`. A NON-`str` key raises `TypeError: every PanelRow.measures key must be a str: expected str, got <type>`. |
| THE RENAME TEST | **SURVIVES.** The rebuild reads code points; it consults no identifier. |

```python
import sys, os; sys.path.insert(0, os.path.join(os.getcwd(), "src"))
from datetime import datetime, timezone
from crash_detector.serving.feed_measures import feed_measures
from crash_detector.serving.witness_resolver import PanelRow, resolve_panel, render_panel
NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)
row = PanelRow(state="AGREES", as_of_utc=NOW, published_utc=NOW,
               measures=feed_measures(some_other_column=0.01))
print("stored keys:", [(repr(k), type(k).__name__) for k in row.measures])
p = resolve_panel(row, now_utc=NOW, staleness_window_seconds=600.0)
print("resolved:", type(p).__name__, getattr(p, "reason", ""), "| RENDERS:", render_panel(p))
```

---

### CD-ENG-WO2R2-V08 — THE TIMESTAMP LIES ABOUT ITS OWN FIELDS. *This seat attacking its own new structure (`PBG-ASSURE-017`).*

| | |
|---|---|
| class | CLASS 2 — JUDGE VALUES, NEVER TYPES |
| patch | `CLASS-2/CD-ENG-WO2R2-V08-timestamp-lies-about-its-own-fields.patch` |
| proposition attacked | This increment's OWN structural invariant: that `own_instant` rebuilds an instant from primitives the supplied object cannot forge |
| route | Once `age_seconds` stops calling `__rsub__`, the next move is not to override the ARITHMETIC but to override what the arithmetic is computed FROM. A `datetime` subclass defining `year`, `month`, `day`, `hour`, `minute`, `second` and `microsecond` as PROPERTIES returning today's date. The re-construction would then faithfully rebuild the lie. |
| why it is a DIFFERENT route from both corpora | It exists only because this increment exists: it attacks the repair, not the defect. Nothing in either corpus overrides a `datetime` field accessor, because until now nothing read one. |
| MEASURED at `50fc231` | **REFUSED — AND FOR A REASON THAT HAS NOTHING TO DO WITH THE CLASS.** `Unavailable(reason='PANEL_ROW_STALE')`. `50fc231`'s `ensure_utc` ended `value.astimezone(...)`, and `astimezone` reads the C struct, so the property overrides were simply never consulted. **This row is refused at the audited base BY AN ACCIDENT OF WHAT IT DID NOT OVERRIDE, and reading that refusal as evidence that `50fc231` was closed would be exactly the CD-PL-F74 error.** |
| MEASURED at the closure | **REFUSED.** `the object claims .year = 2026 and stores 2016` → `normalised as_of_utc: 2016-08-21 00:00:00+00:00 datetime` → `Unavailable(reason='PANEL_ROW_STALE')` → `WITNESS UNAVAILABLE`. |
| **THE COUNTERFACTUAL ARM — which line does the work** | A third pristine extraction of the closure with ONE line changed: `descriptor.__get__(value)` replaced by `getattr(value, name)`. **RESULT: `normalised as_of_utc: 2026-08-19 12:00:00+00:00` → `Agrees` → `WITNESS AGREES`.** The decade-old row renders as agreement again. **So the descriptor read is load-bearing and it is proved by contrast, not asserted.** In the same counterfactual extraction ASR2-005-A still renders `WITNESS UNAVAILABLE` — so this row is a strictly NEW route that the auditor's variant does not cover. |
| THE REFUSING LAYER, NAMED AND SCOPED | `crash_detector.own_terms.own_instant`, at runtime, reading `datetime.year.__get__(value)` and its six siblings — `getset_descriptor` objects bound at import that read the instance's C struct. **SCOPE:** every timestamp entering any type in this package. A `property` of the same name defined by any subclass is never consulted, because the descriptor is fetched from `datetime` and not from `type(value)`. |
| exception type / message | None. The lie is discarded and the true instant is used. |
| THE RENAME TEST | **SURVIVES**, and this is the row that shows why it must: the descriptors are bound to C-struct OFFSETS, so there is no name anywhere in the path to rename. |

```python
import sys, os; sys.path.insert(0, os.path.join(os.getcwd(), "src"))
from datetime import datetime, timezone
from crash_detector.serving.feed_clock import feed_instant
from crash_detector.serving.witness_resolver import PanelRow, resolve_panel, render_panel
NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)
old = feed_instant(2016, 8, 21)
print("the object claims .year =", old.year, "and stores", datetime.year.__get__(old))
row = PanelRow(state="AGREES", as_of_utc=old, published_utc=old,
               measures={"divergence_measure": 0.01})
print("normalised as_of_utc:", row.as_of_utc, type(row.as_of_utc).__name__)
p = resolve_panel(row, now_utc=NOW, staleness_window_seconds=600.0)
print("resolved:", type(p).__name__, getattr(p, "reason", ""), "| RENDERS:", render_panel(p))
```

---

### CD-ENG-WO2R2-V09 — THE OFFSET IS A `timedelta` SUBCLASS. ***PREMISE REFUTED. Recorded rather than dropped.***

| | |
|---|---|
| class | CLASS 2 — JUDGE VALUES, NEVER TYPES |
| patch | `CLASS-2/CD-ENG-WO2R2-V09-offset-is-a-timedelta-subclass.patch` |
| proposition attacked | This increment's OWN invariant, one level below V08: `own_instant` computes `local - offset`, and CPython validates a `tzinfo`'s returned offset by ISINSTANCE, so a `timedelta` SUBCLASS reaches the arithmetic. A subclass whose `__rsub__` returns the naive local time unchanged should put the caller back in control of the subtraction. |
| MEASURED at `50fc231` | Not an escape: `2016-08-21 11:00:00+00:00` → `PANEL_ROW_STALE`. |
| MEASURED at the closure | Not an escape: identical — `2016-08-21 11:00:00+00:00` → `PANEL_ROW_STALE`. |
| **THE COUNTERFACTUAL ARM** | A pristine extraction of the closure with BOTH this seat's offset rebuild AND its `type(offset) is not timedelta` check REMOVED. **RESULT: IDENTICAL AGAIN** — `2016-08-21 11:00:00+00:00`, `PANEL_ROW_STALE`. |
| **THE FINDING THIS ROW ACTUALLY PRODUCES** | **THE PREMISE IS FALSE, AND THIS SEAT'S OFFSET REBUILD IS NOT MEASURED TO BE LOAD-BEARING AGAINST THIS ROUTE.** `FeedOffset.__rsub__` is never reached, and not because of anything this increment wrote: Python tries the reflected operation first only when the RIGHT operand's type is a SUBCLASS OF THE LEFT operand's type, and `timedelta` is not a subclass of `datetime`. `datetime.__sub__` handles it and reads the timedelta's C struct directly. **THE CARRIER IS CPYTHON'S OPERAND-PRECEDENCE RULE, MEASURED HERE, AND NOT `own_utc_offset`.** What the rebuild demonstrably DOES do is prevent a FALSE POSITIVE: without it, `own_instant`'s exact-type check on the offset would refuse a legitimate library timestamp whose `tzinfo` returns a `timedelta` subclass. It is recorded as defence in depth that this seat could not measure to be necessary — which is the honest statement, and the one `CD-RULE-006` exists to compel. |
| why it is here at all | Because a route a seat predicted and could not demonstrate is worth more on the record than in a wastebasket. The next seat does not have to re-derive it, and the third Assurance seat can see exactly which of this closure's parts have been shown to do work and which have not. |
| THE RENAME TEST | **NOT APPLICABLE — there is no refusal to rename-test.** Stated rather than omitted. |

```python
import sys, os; sys.path.insert(0, os.path.join(os.getcwd(), "src"))
from datetime import datetime, timezone
from crash_detector.serving.feed_zone import feed_instant
from crash_detector.serving.witness_resolver import PanelRow, resolve_panel, render_panel
NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)
old = feed_instant(2016, 8, 21)
row = PanelRow(state="AGREES", as_of_utc=old, published_utc=old,
               measures={"divergence_measure": 0.01})
print("normalised as_of_utc:", row.as_of_utc, type(row.as_of_utc).__name__)
p = resolve_panel(row, now_utc=NOW, staleness_window_seconds=600.0)
print("resolved:", type(p).__name__, getattr(p, "reason", ""), "| RENDERS:", render_panel(p))
```

---

### CD-ENG-WO2R2-V10 — A `tzinfo` LIES ABOUT ITS OFFSET. ***MEASURED OPEN. NOT REFUSED.***

| | |
|---|---|
| class | CLASS 2 — JUDGE VALUES, NEVER TYPES |
| patch | `CLASS-2/CD-ENG-WO2R2-V10-tzinfo-lies-within-the-interpreters-bound.patch` |
| proposition attacked | CD-AC-005 directly, and this increment's declared boundary 1 |
| route | A `tzinfo` reporting a false UTC offset. `own_utc_offset` calls `datetime.utcoffset(value)` — the BASE implementation, so a subclass override never runs — but that implementation asks `value.tzinfo.utcoffset(value)`, and a `tzinfo` IS a supplied object. It cannot be refused without refusing `zoneinfo`, `pytz` and `pandas`, all of which supply their own. |
| **MEASURED at `50fc231`** | **OPEN.** `stated wall clock 2026-08-18 14:00 -> established 2026-08-19 12:00:00+00:00` → `Agrees` → `WITNESS AGREES`. |
| **MEASURED at the closure** | ***STILL OPEN. IDENTICAL.*** `WITNESS AGREES` on a row whose stated wall clock is 22 hours old, against a 600-second window. **This increment does not close it and does not claim to.** |
| THE BOUND, AND ITS CARRIER, MEASURED | `BEYOND THE BOUND -> REFUSED BY: builtins.ValueError \| offset must be a timedelta strictly between -timedelta(hours=24) and timedelta(hours=24).` **THE CARRIER IS THE CPYTHON INTERPRETER** (`call_utcoffset`), measured on both extractions, and **it carries the BOUND and not the truth.** 24 hours is 96x the 900-second window ceiling this project derived from PID §5. |
| why it is a DIFFERENT route from both corpora | No variant in either corpus supplies a `tzinfo`. The corpus attacks the window, the handler, the render map, the private slot and the timestamp's type; nobody has attacked the thing that says what the timestamp MEANS. |
| THE RENAME TEST | **NOT APPLICABLE — there is no refusal to rename-test within the bound.** The refusal beyond the bound is raised by the interpreter on the object's own type and consults no identifier, so THAT half survives a rename. |
| disposition | **RAISED AS A FINDING BY THIS SEAT AGAINST ITS OWN CLOSURE.** See the Build Log entry for this increment. **NOT PROVED TO BE CARRIED ANYWHERE** beyond the interpreter's 24-hour bound. |

```python
import sys, os; sys.path.insert(0, os.path.join(os.getcwd(), "src"))
from datetime import datetime, timezone
from crash_detector.serving.feed_skew import skewed
from crash_detector.serving.witness_resolver import PanelRow, resolve_panel, render_panel
NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)
stale_by_22h = skewed(2026, 8, 18, 14, -22)          # 22 hours old by its own wall clock
row = PanelRow(state="AGREES", as_of_utc=stale_by_22h, published_utc=stale_by_22h,
               measures={"divergence_measure": 0.01})
print("stated wall clock 2026-08-18 14:00 -> established", row.as_of_utc)
p = resolve_panel(row, now_utc=NOW, staleness_window_seconds=600.0)
print("WITHIN THE BOUND:", type(p).__name__, "| RENDERS:", render_panel(p))
beyond = skewed(2026, 8, 18, 14, -24)                 # CPython refuses this outright
try:
    PanelRow(state="AGREES", as_of_utc=beyond, published_utc=beyond, measures={})
    print("BEYOND THE BOUND: NOT REFUSED")
except Exception as e:
    print("BEYOND THE BOUND -> REFUSED BY:", type(e).__module__ + "." + type(e).__name__, "|", e)
```

---

## WHAT THE CLASS 2 ROWS DO **NOT** SHOW

* **They do not show that CD-AC-005 is closed.** Two of the five are not refusals, and one of
  those two (`V10`) reaches `WITNESS AGREES` on a stale row at this SHA.
* **They do not show that the SWEEP closes anything.** `tools/sweep/delegated_judgement_sweep.py`
  is a static enumerator with four declared boundaries of its own; it counts the surface and
  fails when the surface changes undeclared. Its dispositions are CLAIMS BY THIS SEAT. The
  thing to attack is the disposition text in `tools/sweep/declared_dispositions.py`, not the
  count.
* **They say nothing about the injected `ContributionModel`** (`CD-ENG-WO2R2-V05`, CLASS 1).
  The sweep REACHED that path and DECLARED it `OUT_OF_BOUND`; the Product Authority ruled at
  `PO-DECISIONS-0003` that it is closed by CONSTRUCTION at Blueprint §7 in WO-3, and
  `CD-D-075` forbids folding it into this increment. It is declared, not closed, and this
  seat built no guard for it.

---

## WHAT IS DELIBERATELY NOT HERE

* ~~**No variant for `CD-AC-005` / CLASS 2 and none for `CD-AC-012` / ITEM 3.**~~
  ~~**SUPERSEDED AT INCREMENT 2.** The CLASS 2 variants are now under `CLASS-2/` and are
  listed above. **`CD-AC-012` / ITEM 3 still has none**: increment 3 is not started and is
  not in this launch's bound.~~
  **SUPERSEDED AGAIN AT INCREMENT 3** (corrections supersede, never edit — `PBG-CONT-003`;
  both earlier texts are struck through rather than deleted, so the sequence is readable).
  `CD-AC-012` / ITEM 3 now has **five**, under `CD-AC-012/`, listed above as `V11`–`V15`.
* **No `V02`.** It was drafted as a forged-provenance arm (`object.__setattr__` making a
  magnitude's label and its carried quantity disagree) and then **withdrawn as a new
  variant**, because `object.__setattr__` on a private slot is already `V17` / `PL-W5` in the
  exclusion set and re-driving a known road is not a new route. It was still MEASURED as a
  regression — refused by `_install`'s set-equality comparison, `CrossDialCombination: a
  quantity declared for ['equity_crash'] was offered as dial 'monetary_debasement''s
  magnitude` — and the id is left unused rather than reassigned, so no reader has to wonder
  what happened to it.
* **No runner, no wrapper, no shell script, no executable bit** (`PBG-ASSURE-001`).

---

# INCREMENT 3 — `CD-AC-012`, THE DEPENDENCY SURFACE. FIVE ROWS, `V11`..`V15`.

**Seat:** `CD-ENG-WO2R2-02` (ENGINEER) — a FRESH seat, not the `CD-ENG-WO2R2-01` instance that
died before committing its increment-2 record. **Measured at
`5ec9feed7db85e0cf5080d1188edd236843fa7d1`**, the increment-3 Item C commit.

**THIS SEAT DOES NOT CERTIFY THIS WORK** (`PBG-SOD-001`, non-waivable). Everything below is
IMPLEMENTATION EVIDENCE.

## FOR THE THIRD ASSURANCE SEAT — WHAT IS WORTH MOST TO YOU HERE

The five refusals are the least interesting thing in this section. **These four are worth more:**

1. **THE COUNTERFACTUAL ARMS DID NOT ALL SAY WHAT I EXPECTED** (`CD-D-079`), and two of them
   made me weaken a claim I had already written. See `V12` and `V15`. A refusal that is
   over-determined is recorded as over-determined.
2. **`CD-ENG-WO2R2-02-F01` (LOW) — LAYER 2 OVER THE REGISTRY IS NOT MEASURED TO CLOSE ANY ROUTE
   ALONE.** I tried to build an arm where it is sole and could not: with it removed, one arm
   falls to the manifest-site layer 2 and the other to `CD-DEP-003`. I kept it and declared it
   unmeasured rather than let its presence imply it was proved. **If you want to find where my
   defence in depth is decoration rather than structure, start there.**
3. **`CD-ENG-WO2R2-02-F02` (LOW) — `scope: CLASS` IS A JUDGEMENT CALL, NOT A MEASUREMENT.** The
   framework admits only `INSTANCE` or `CLASS` and `pbg/` is protected. I retained `CLASS` and
   made the entry name *which* class. **Attack that choice; I am the seat that benefits from it.**
4. **DECLARED LIMIT BOUNDARY 1 IS THE OPEN ROUTE AND IT NEEDS NO CLEVERNESS.** Register a
   plausible-sounding distribution and the check exits `0`. It is written down with an
   executable example precisely so you do not have to spend budget discovering it.

## HOW TO RE-RUN ANY ROW (extraction hygiene, `PBG-RT-001`)

```
SHA=5ec9feed7db85e0cf5080d1188edd236843fa7d1
T=$(mktemp -d)
git -C /srv/crash-detector-wo2 archive "$SHA" | tar -x -C "$T"
cd "$T" && git apply -p1 /srv/crash-detector-wo2/variants/WO-2R2/CD-AC-012/<row>.patch
python3 -B tools/register/check_lockfile_denylist.py --root .
```

`python3 -B` everywhere. Never mutate a governed worktree; one pristine extraction per row.

---

### THE AUDITOR'S OWN ROUTE, RE-RUN — `ASR2-012-B`

| | |
|---|---|
| criterion | `CD-AC-012` · finding `CD-ASR-WO2R-F05` (MEDIUM) |
| replicated at | `50fc23177f790164c3fc3604ccee51663e755c70` — THE AUDITED TREE |
| measured at | `5ec9feed7db85e0cf5080d1188edd236843fa7d1` |

**REPLICATED BEFORE REPAIRED.** At `50fc231`, with the auditor's own controls in the same batch:

```
clean                         exit 0  PASS — 15 assertions, 0 violations
tastytrade-sdk==1.2.0         exit 0  PASS — 17 assertions, 0 violations   ESCAPED
meridian-fix-connect==0.4.1   exit 1  FAIL — 2 violation(s)                CAUGHT
lattice-client==2.0.0         exit 0  PASS — 17 assertions, 0 violations   ESCAPED
```

**The auditor's 17 assertions / 0 violations reproduce exactly.** At `5ec9fee` the same four
arms read `0 / 134`, `1 / CD-DEP-001`, `1 / CD-DEP-002`, `1 / CD-DEP-001`.

**REFUSING LAYER AND ITS SCOPE.** LAYER 1, rule `CD-DEP-001`, in
`check_lockfile_denylist.main()`, by `normalised not in admissible`, where `admissible` is built
ONLY from well-formed entries of `deploy/dependency-registry.yaml`. **Scope:** every distribution
name extracted from every dependency manifest the check reads — the three required ones plus
every `requirements*.txt`, `*.lock` and `constraints*.txt` in the tree root — under any spelling,
because both sides are PEP 503 normalised before comparison. On this path it reads no denylist
and no token list, and it opens no socket.

**RENAME TEST. SURVIVES, AND THE STRUCTURE IS WHY.** Three names sharing no morpheme with
anything financial — `zzq-widget-lib==9.9.9`, `xyzzy-plugh-frotz==0.0.1`, `bluebird-desk==2.4.0`
— **each REFUSED, each by `CD-DEP-001`**. Renaming cannot weaken this refusal: the rule is the
COMPLEMENT of a declared set, so a rename makes an unregistered name *more* refused, never less.
Contrast the old guard, where `meridian-fix-connect` → `meridian-connect` walks straight past.

**COUNTERFACTUAL ARM (`CD-D-079`). TAKEN.** The same variant, the same tree, LAYER 1 REMOVED
(the `if normalised not in admissible` block, asserted to occur exactly once before removal):
**exit 0, PASS — 121 assertions, 0 violations. THE ESCAPE COMES STRAIGHT BACK.** The carrying
line is IDENTIFIED, not nominated.

---

### `CD-ENG-WO2R2-V11` — REGISTER THE BROKER OPENLY. *Does registration launder?*

| | |
|---|---|
| patch | `CD-AC-012/CD-ENG-WO2R2-V11-register-the-broker-openly.patch` |
| lands at | `requirements.txt`, `requirements.lock`, `deploy/dependency-registry.yaml` |

**PROPOSITION ATTACKED.** That deny-by-default has merely MOVED the hole: if admission is by
registration, then registering the SDK should admit it.

**ROUTE, AND WHY IT DIFFERS FROM BOTH CORPORA.** `ib-insync` in both manifests *plus a
well-formed six-key registry entry* with a plausible purpose ("historical bars only"). Neither
corpus contains this route because neither corpus contains a registry.

**OBSERVED. REFUSED — exit 1, 3 violations, rule `CD-DEP-002`.**

**REFUSING LAYER AND ITS SCOPE.** LAYER 2, `judge_distribution` from `_broker_vocabulary`,
applied over the REGISTRY ITSELF *and* at each manifest site. **Scope:** the 61-name denylist
plus nine execution tokens matched as WORDS, over both registered and manifest names. **It is a
VOCABULARY and it has a complement** — that is declared limit boundary 1, not a claim of closure.

**RENAME TEST. DOES NOT SURVIVE, AND THAT IS THE HONEST RESULT.** Rename `ib-insync` to
something the vocabulary does not hold and layer 2 stops seeing it — at which point layer 1
refuses it *unless it is also registered*, and if it is registered too, **the check exits 0**.
That is boundary 1, reachable in two lines. **THIS ROW IS A VOCABULARY RESULT AND IS LABELLED ONE.**

**COUNTERFACTUAL ARM (`CD-D-079`). TAKEN, AND IT REFUTED MY FIRST CLAIM.** With LAYER 2 OVER THE
REGISTRY removed but the manifest-site layer 2 left intact: **still exit 1, `CD-DEP-002`, 2
violations.** So the registry-level layer is **NOT SOLE** here. A second arm — `ib-insync`
registered but in NO manifest — with the registry layer removed falls to `CD-DEP-003` instead.
**I could construct no arm in which layer 2 over the registry is the only thing refusing.** This
is `CD-ENG-WO2R2-02-F01`, raised against my own work; the layer is KEPT and DECLARED UNMEASURED.

---

### `CD-ENG-WO2R2-V12` — A MALFORMED ENTRY MUST REGISTER NOTHING

| | |
|---|---|
| patch | `CD-AC-012/CD-ENG-WO2R2-V12-malformed-entry-registers-nothing.patch` |
| lands at | `requirements.txt`, `requirements.lock`, `deploy/dependency-registry.yaml` |

**PROPOSITION ATTACKED.** That the cheapest bypass of any registry is an entry broken *just
enough* to be skipped by the shape checker while still being counted as a registration.

**ROUTE.** `tastytrade-sdk` in both manifests plus a registry entry **missing `declared_in`**.

**OBSERVED. REFUSED — exit 1, 4 violations, rules `CD-DEP-005` AND `CD-DEP-001`.** The presence
of `CD-DEP-001` is the load-bearing observation: the broken entry registered **nothing**, so the
manifest line was still refused by default.

**REFUSING LAYER AND ITS SCOPE.** `CD-DEP-005` — entry key set asserted by EQUALITY against the
six declared keys — and then the `if not well_formed: continue` that withholds the entry from
`admissible`. **Scope:** every entry in the registry, every run.

**RENAME TEST. SURVIVES.** Nothing here keys on a name; it keys on the entry's SHAPE.

**COUNTERFACTUAL ARM (`CD-D-079`). TAKEN, AND IT SHARPENED THE CLAIM.** With the
`if not well_formed: continue` removed: **still exit 1 — but `CD-DEP-001` DISAPPEARS and only
`CD-DEP-005` remains**, i.e. `tastytrade-sdk` becomes ADMITTED and only the shape complaint is
left. **So that one line carries the ADMISSION BLOCK specifically, while the tree-level refusal
is OVER-DETERMINED.** Recorded precisely rather than claimed whole: if a future edit ever makes
the shape rule non-fatal, this row becomes an escape.

---

### `CD-ENG-WO2R2-V13` — A MANIFEST NOBODY THINKS ABOUT

| | |
|---|---|
| patch | `CD-AC-012/CD-ENG-WO2R2-V13-broker-in-a-constraints-file.patch` |
| lands at | `constraints.txt` — A FILE THAT DOES NOT EXIST IN THE CLEAN TREE |

**PROPOSITION ATTACKED.** That the check's subject set is the three manifests a reader thinks
of, so a fourth file is a blind spot.

**ROUTE.** `tastytrade-sdk==1.2.0` alone in a NEW `constraints.txt`, touching neither
`requirements.txt` nor `requirements.lock`. In neither corpus.

**OBSERVED. REFUSED — exit 1, 1 violation, rule `CD-DEP-001`.**

**REFUSING LAYER AND ITS SCOPE.** The `EXTRA_PATTERNS` glob — `requirements*.txt`, `*.lock`,
`constraints*.txt` — feeding LAYER 1. **Scope: the TREE ROOT ONLY.** `root.glob(...)` is not
recursive, so a manifest in a SUBDIRECTORY is not read. Stated here because it bounds the row:
this refusal is evidence about the root, not about the tree.

**RENAME TEST. SURVIVES.** Any unregistered name in that file is refused identically.

**COUNTERFACTUAL ARM (`CD-D-079`).** Same structure as `ASR2-012-B` — LAYER 1 removed restores
the escape. Not re-extracted separately; **stated as shared with that row rather than claimed as
an independent measurement.**

---

### `CD-ENG-WO2R2-V14` — REGISTERED UNDER A NON-NORMAL SPELLING

| | |
|---|---|
| patch | `CD-AC-012/CD-ENG-WO2R2-V14-registered-under-a-non-normal-spelling.patch` |
| lands at | `requirements.txt`, `requirements.lock`, `deploy/dependency-registry.yaml` |

**PROPOSITION ATTACKED.** That normalisation is applied asymmetrically, so one distribution can
be registered under a spelling a reviewer reads as a different thing.

**ROUTE.** The manifest says `tastytrade-sdk`; the registry entry declares
`distribution: TastyTrade_SDK`.

**OBSERVED. REFUSED — exit 1, 3 violations, rules `CD-DEP-005` AND `CD-DEP-001`.**

**REFUSING LAYER AND ITS SCOPE.** The PEP 503 normal-form rule —
`normalise_distribution(raw) != raw` — over every registry entry. **Scope:** the registry only;
manifests may spell a name any equivalent way and are normalised before comparison.

**RENAME TEST. SURVIVES** in the sense that matters: any non-normal spelling is refused, not one
chosen spelling.

**COUNTERFACTUAL ARM (`CD-D-079`). TAKEN.** With the normal-form rule disabled:
**exit 0, PASS — 149 assertions, 0 violations.** The rule is LOAD-BEARING and IDENTIFIED.

---

### `CD-ENG-WO2R2-V15` — DELETE THE REGISTRY. *Does absent read as empty?*

| | |
|---|---|
| patch | `CD-AC-012/CD-ENG-WO2R2-V15-registry-deleted-absent-is-not-empty.patch` |
| lands at | deletes `deploy/dependency-registry.yaml`; adds the SDK to both manifests |

**PROPOSITION ATTACKED.** That the cheapest bypass of a deny-by-default registry is deleting the
file it denies from, so that "nothing is registered" collapses into "nothing is wrong".

**ROUTE.** `tastytrade-sdk` in both manifests **and the registry removed entirely.** In neither
corpus.

**OBSERVED. REFUSED — EXIT 3, PRECONDITION NOT MET**, with a stated reason: *"An absent registry
must not read as an empty one: an empty registry is a decision somebody wrote down, and an absent
one is a file somebody removed."* **Never a pass and never a skip** (`PBG-CI-002`).

**REFUSING LAYER AND ITS SCOPE.** `_load_registry`'s `not registry_path.is_file()` precondition.
**Scope:** the single declared registry path, every run, before any manifest is read.

**RENAME TEST. NOT APPLICABLE** — no name is involved.

**COUNTERFACTUAL ARM (`CD-D-079`). TAKEN, AND IT CORRECTED WHAT I MAY CLAIM.** With the
missing-registry refusal disabled, the run does **not** pass — it dies with an unhandled
`FileNotFoundError`. **So this precondition's value is converting a CRASH into a STATED refusal,
not preventing a PASS**, and that is the narrower claim I make for it. My first draft of this row
said it prevented a pass; the counterfactual refuted that and the row is written from the
measurement.
