# CD-ASR-WO2R2-01 — CD-AC-002 and the PO scoping ruling

target: f30e63cbac6782ec5d7789071ee26be0ba7fe2e5 · evidence: arms/ASR3-002-*.out

## THE INVITATION, AND WHAT I DID WITH IT

PO-DECISIONS-0003 ruling 1 scopes CD-AC-002 at WO-2 on this factual basis:

> "a WO-2 candidate registers no model, no source, deploys nothing and has no publication
>  layer — the injected-model route is not in WO-2's population. The criterion at WO-2's
>  gate covers **every route that needs no injected model**."

Ruling 4 invites me to attack it; CD-D-076 makes success a suspension trigger.

I attacked the **premise**, not the conclusion. The premise has four limbs. Three are true
of the SHIPPED DEFAULT CONFIGURATION and none of them is true of WO-2's POPULATION.

---

## FINDING ASR3-F02 — **HIGH** — CD-AC-002. THE INJECTED-MODEL ROUTE IS IN WO-2'S REAL
## POPULATION, AND IT PUBLISHES A BLEND WITH **NO SOURCE EDIT OF ANY KIND**.

probe: `probes/ASR3-002-A-injected-model-blend-no-source-edit.py.txt`
arm:   `arms/ASR3-002-A.out`

### What I built
A WO-2 candidate assembled **entirely from delivered public API** at f30e63c. No file in
`src/` patched. No private slot touched. No `object.__setattr__`. No subclass of any
project type. **No patch applied to the tree at all** — I proved the extraction
byte-identical to the target after the run (`src/` + `tools/` sha256 tree hash
`b12f5d3ab7e2db69c2f174a5c54d957c150d02010a66d1aa539c133b449ee2c9`, equal to the audit
worktree's).

One ordinary `ContributionModel` — a class with a `model_id` and a `compute`, satisfying
the Protocol exactly, performing **no I/O, reading no clock and reading no environment**,
so it does not breach the documented purity contract — injected into **both** `DialSpec`s.

### MEASURED

```
ONE model object in BOTH specs: True
TRUE equity level (input) : 0.9
TRUE monetary level(input): 0.1

equity   : Value(EquityCrashScore(score=DialMagnitude(dial_id='equity_crash',
                                                      quantity=0.9)), inputs_used=('equity_feed',))
monetary : Value(MonetaryDebasementScore(score=DialMagnitude(dial_id='monetary_debasement',
                                                      quantity=0.5)), inputs_used=('monetary_feed',))

number_for_dial_slot('equity_crash')        -> 0.9   [NOT REFUSED]
number_for_dial_slot('monetary_debasement') -> 0.5   [NOT REFUSED]
```

The monetary dial's true level is **0.1**. It publishes **0.5** — the mean of both dials —
through the declared CD-AC-002 publication gate. Every field of the admission claim is
true (`dial_id='monetary_debasement'`, `inputs_used=('monetary_feed',)`) except the number.
This is the exact product failure PID §3.1 calls constitutional.

### WHY THE ADMISSION DOOR CANNOT SEE IT
`engine/evaluate.py:371` is the ONE declared admission site, and the citation it makes is
**true**: `used_ids` really is the set of sources that dial got. The blend does not enter
through a false claim; it enters through a **true claim about a number computed elsewhere**.
`observed_for_dial` never validates `quantity` (`provenance.py:731-811` — it validates
`dial_id`, validates `inputs_used`, refuses `dial_id in inputs_used`, and passes `quantity`
straight to `_new_quantity`). Nothing downstream can distinguish this magnitude from an
honest one, because in every respect except the number it *is* an honest one.

### WHY THE STATIC APPARATUS IS BLIND BY CONSTRUCTION
The route changes **no scanned file**. `check_no_blend` and every sibling check are static
reads of source text. There is nothing for them to read. This is not a gap in the
vocabulary (CD-ASR-WO2R-F01's shape) — it is a route with **no source text at all**.

### THIS IS STRONGER THAN CD-ENG-WO2R2-F03 / PL-Z4 IN ONE RESPECT THAT MATTERS
Both prior demonstrations, and every plant in this gate, require **committing code**.
CD-ASR-WO2-02 stated in terms: *"My CD-AC-002 finding was demonstrated with a source edit.
Like every plant in this gate, it requires committing code. I do not claim a route from
configuration or data alone."* **I claim exactly that, and I measured it.** The blend is
reachable from configuration and data against an unmodified tree.

---

## FINDING ASR3-F03 — **MEDIUM** — a blend publishes with **NO INJECTED MODEL**, which is
## inside the scope the PO ruling expressly did NOT exempt.

probe/arm: `arms/ASR3-002-B.out`

The ruling exempts only "the injected-model route" and states the criterion at WO-2's gate
"covers every route that needs no injected model". This route uses no model:

```
observed_for_dial(dial_id='monetary_debasement',
                  quantity=0.5,                       # a blend
                  inputs_used=('gold_feed','cpi_feed'))
  -> DeclaredQuantity(dials=['monetary_debasement'], value=0.5)   ACCEPTED
number_for_dial_slot('monetary_debasement', DialMagnitude(...))  -> 0.5   [NOT REFUSED]
```

`observed_for_dial` is **public API**, re-exported in `crash_detector.dials.__all__`.

**HONEST QUALIFICATION, stated because it changes the grade.** This is the DECLARED
residue: `check_no_blend` RULE 4 constrains *where in the scanned set* the door may be
called, and the module docstring says openly that the door "believes what it is told".
CD-ENG-WO2R2-01 declared it (*"THE EXTERNAL ADMISSION BASE CASE IS NOT CLOSED"*), and
CD-ASR-WO2-02 already confirmed it real. I am **confirming a declared residue, not
defeating a claim** — which is why this is MEDIUM and ASR3-F02 is HIGH. It matters here
only because it sits inside the scope the ruling did not carve out.

---

## MY EXPLICIT STATEMENT ON THE CD-AC-002 SCOPING (required by the dispatch)

### The premise, limb by limb, measured

| ruling's limb | true of the shipped default? | true of WO-2's POPULATION? |
|---|---|---|
| "registers no model" | YES — `CONTRIBUTION_MODELS = {}` | **IRRELEVANT.** Injection never consults that registry. `DialSpec.contribution_model` is a plain field. Registration is not the injection route. |
| "registers no source" | YES — `EMPTY_SOURCE_REGISTRY` | **NO.** `SourceRegistry` is delivered public API; `ConfigSnapshot` accepts any instance. |
| "deploys nothing" | YES | agreed, and not load-bearing for this route — no deployment is needed. |
| "has no publication layer" | the envelope BUILDER/server: YES | **NO as to the gate.** `publication/dial_scalar.py::number_for_dial_slot` IS delivered at WO-2, IS the declared CD-AC-002 gate, and IS what returned 0.5 above. |

### The decisive evidence: **WO-2's own deliverable exercises the route**

```
tests/ defining ContributionModel implementations : 3
tests/ injecting a contribution_model            : 6 sites
tests/ registering SourceRecords                 : 6 sites
```
(`tests/test_evaluate.py`, `tests/test_config_source_registry.py`, `tests/test_source_registry.py`)

A route that WO-2's own accepted test suite exercises six times is in WO-2's population.
The ruling's premise describes the **shipped configuration**; it was applied as though it
described the **delivered code**. Those are different sets, and the criterion is about the
second.

### The dilemma, measured rather than argued (`arms/ASR3-002-C.out`)

Under the shipped configuration:

```
shipped registry is_empty : True     models per dial: [None, None]
equity   : Unknown -> NO_REQUIRED_INPUTS_DECLARED
monetary : Unknown -> NO_REQUIRED_INPUTS_DECLARED
Does EITHER dial carry a number? -> False
```

**Under the shipped configuration there are no dial numbers at all.** So read strictly,
the ruling's population makes CD-AC-002 **vacuous** at WO-2 — "the two dials are never
blended" is satisfied by there being nothing to blend. That reading cannot be the intended
one: the project spent increments 1 and 2b building type closures on the derivation door,
maintains three declared CD-AC-002 contrast tests, and plants violations against them. All
of that work presupposes a population in which dial numbers exist.

**So the scoping faces a dilemma with no third branch:**
- read it as *the shipped config* → CD-AC-002 is vacuous at WO-2 and the gate certifies nothing;
- read it as *what the delivered code admits* → the injected-model route is in population,
  and **ASR3-F02 exercises it**.

### VERDICT ON THE SCOPING

**I DO NOT ACCEPT THE PO'S WO-2 SCOPING OF CD-AC-002, AND ON THE EVIDENCE ABOVE I REGARD
IT AS DEFEATED.** I exercised an injected-model route inside a WO-2 candidate's real
population — using only delivered public API, against a tree I proved unmodified, in a
configuration shape WO-2's own test suite uses six times.

Stated in terms, because CD-D-076 makes this a gate condition and not a footnote:
**CD-D-076's trigger condition is met on my measurement, and OPTION (C) SUSPENSION
APPLIES on its own terms** — Blueprint §7 returns for architectural review and
implementation stops.

**WHAT I AM NOT SAYING.** I am not saying the Engineer seats did poor work; increments 1
and 2 are the strongest closures I examined and I could not break the derivation door
(below). I am not saying the PO reasoned dishonestly — the ruling handed me the knife
precisely so this could happen, and the failure is in a factual premise about
*registration* that does not describe the *injection* mechanism. **Disposition is the
Product Owner's and this is not an acceptance or a refusal of one (PBG-AUTH-003).**

---

## WHAT I COULD NOT BREAK — recorded because a guard proved to bite is worth recording

**The derivation door is genuinely closed at the type.** `derived_within_one_dial`
(`provenance.py:814`) takes only `DeclaredQuantity` refused by **exact type identity** and
a `reduction` refused by exact type against `SameDialReduction`. The number is computed by
`SAME_DIAL_REDUCTIONS` inside the door over values it released itself. `combine_within_one_dial`
now passes established quantities and a named reduction — **there is no argument on that
path through which a caller's float or callable can arrive.** CD-ASR-WO2R-F01's route is
closed, and closed at the class rather than at the name. I attempted it and it is refused.

`number_for_dial_slot` correctly refuses a bare float, a wrong-dial magnitude and a
non-`DialMagnitude`, by exact type plus a data comparison of provenance. It did its job on
every input I gave it. **It cannot help here** — ASR3-F02 hands it a magnitude whose
provenance is genuinely and exactly `monetary_debasement`. The gate compares provenance,
and the provenance is true. The number is the lie, and no provenance check can see it.
