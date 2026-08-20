# ASSURANCE VERDICT — WO-2R2, crash-detector — CD-ASR-WO2R2-01 (THIRD Assurance seat)

```
target            f30e63cbac6782ec5d7789071ee26be0ba7fe2e5   (branch wo-2-skeleton)
target tree       01da44b51e07dfb2e71170f4f19b6db09814b981
worktree          /srv/crash-detector-wo2r2-audit  (detached, porcelain 0, 392 files)
dispatch          governance/dispatch/CD-DISPATCH-WO2R2-ASSURANCE.yaml  (CD-AUTH-0001)
actor             CD-ASR-WO2R2-01
independence      DECLARED CLEAN — not CD-ASR-WO2-01, not CD-ASR-WO2-02, never an Engineer
                  on this project, no commit on wo-2-skeleton (verified by enumerating every
                  author on the branch). No INDEPENDENCE_CONFLICT.
method            Every execution ran in a throwaway `git archive | tar -x` extraction under
                  /tmp (SD-2), a separate one per arm. NOTHING was executed inside the audit
                  worktree. `python3 -B` everywhere. No `git worktree add`. No repairs.
```

---

## PER-CRITERION VERDICTS — the gate is per criterion; the overall verdict is the worst

| criterion | verdict | confidence | basis |
|---|---|---|---|
| **CD-AC-001** Missing or stale input never renders as calm | **RED** | MEDIUM-HIGH | ASR3-F05 |
| **CD-AC-002** The two dials are never blended | **RED** | HIGH | ASR3-F02; scoping defeated |
| **CD-AC-003** Witnesses are side-by-side, never ingredients | **PASS (scoped)** | HIGH | live contrast closed by me |
| **CD-AC-005** WITNESS UNAVAILABLE is not WITNESS AGREES | **RED** | HIGH | ASR3-F04 |
| **CD-AC-012** No execution pathway exists | **RED** | HIGH | ASR3-F08 |

```
OVERALL   RED        THE WO-2 GATE IS NOT MET, for the third time, on grounds
                     different from both previous gates.
```

**A PASS is not an acceptance and neither is this RED (PBG-AUTH-003).** Disposition is the
Product Owner's. I supply evidence and a verdict.

---

## THE HEADLINE: three of the four RED findings need NO SOURCE EDIT AT ALL

Every plant in this gate, and both previous auditors' HIGH findings, required committing
code. CD-ASR-WO2-02 stated in terms: *"I do not claim a route from configuration or data
alone."* **ASR3-F02, ASR3-F04 and ASR3-F05 are all reached from delivered public API against
a tree I proved byte-identical to the target** (`src/` + `tools/` sha256
`b12f5d3ab7e2db69c2f174a5c54d957c150d02010a66d1aa539c133b449ee2c9`, equal to the audit
worktree's). ASR3-F08 needs only a one-line manifest edit.

This matters for grading: the entire static apparatus — `check_no_blend`, the sweep, every
AST guard — is a read of source text. **A route with no source text is invisible to all of
it by construction, not by oversight.**

---

## MY EXPLICIT STATEMENT ON THE CD-AC-002 SCOPING (dispatch requires this in terms)

**I DO NOT ACCEPT THE PO'S WO-2 SCOPING OF CD-AC-002. ON MY MEASUREMENT IT IS DEFEATED,
CD-D-076'S TRIGGER CONDITION IS MET, AND OPTION (C) SUSPENSION APPLIES ON ITS OWN TERMS.**

The ruling's premise is that "a WO-2 candidate registers no model, no source, deploys
nothing and has no publication layer". Measured, limb by limb:

* **"registers no model" is true but not load-bearing.** `CONTRIBUTION_MODELS` is empty —
  and **injection never consults it**. `DialSpec.contribution_model` is a plain field.
  Registration is not the injection route, so the emptiness of the registry says nothing
  about the reachability of the route.
* **"registers no source" is true of the shipped default only.** `SourceRegistry` is
  delivered public API and `ConfigSnapshot` accepts any instance.
* **"has no publication layer" is false as to the gate.** `publication/dial_scalar.py::
  number_for_dial_slot` — which the module itself calls *"THE ONE PLACE a dial magnitude
  becomes a number that may be published"* — ships in WO-2 and is what returned the blend.

**The decisive evidence is WO-2's own deliverable**: its accepted test suite defines **3**
`ContributionModel` implementations, injects a model at **6** sites and registers sources at
**6** sites. A route the deliverable's own tests exercise six times is in its population.

**And the scoping faces a dilemma with no third branch, measured not argued** — under the
shipped configuration both dials read `Unknown` and **no dial number exists at all**
(`arms/ASR3-002-C.out`). So:

* read the population as *the shipped config* → **CD-AC-002 is vacuous at WO-2** and the
  gate certifies nothing;
* read it as *what the delivered code admits* → **the injected-model route is in
  population and ASR3-F02 exercises it.**

The project does not behave as though the first reading were true: it built type closures on
the derivation door, maintains three CD-AC-002 contrast tests and plants violations against
them. All of that presupposes a population in which numbers exist.

**What I am NOT saying.** The Engineer seats did strong work — increments 1 and 2 are the
best closures I examined and I could not break the derivation door. The PO did not reason
dishonestly; it handed me the knife precisely so this could happen. The failure is in a
factual premise about *registration* that does not describe the *injection* mechanism.

---

## FINDINGS

| id | sev | criterion | one line |
|---|---|---|---|
| **ASR3-F02** | HIGH | CD-AC-002 | One stateful model in both `DialSpec`s → monetary dial publishes 0.5 against a true 0.1. **No source edit.** |
| **ASR3-F04** | HIGH | CD-AC-005 | `WITNESS AGREES` from a row whose stored state is `UNAVAILABLE`. `resolve_panel` never admits its row. |
| **ASR3-F05** | HIGH | CD-AC-001/005 | `evaluate()` never admits its `ConfigSnapshot`; a 10-year-old observation renders as `0.9`. |
| **ASR3-F08** | HIGH | CD-AC-012 | A real broker SDK escapes deny-by-default on requirement **spelling** (`-e git+…`), exit 0. |
| **ASR3-F03** | MED | CD-AC-002 | A blend publishes with **no injected model** via the public admission door (declared residue, confirmed). |
| **ASR3-F06** | MED | CD-AC-005 | `witness_resolver` declared `ESTABLISHED` on a sentence I measured false. |
| **ASR3-F07** | MED | method | The sweep's import closure excludes every **consumer** by construction — including the CD-AC-002 gate. 262 undeclared sites. |
| **ASR3-F09** | MED | CD-AC-012 | Three-place CD-RULE-004 disagreement on `scope`, inside the repair for a CD-RULE-004 defect. |
| **ASR3-F01** | LOW | process | The dispatch's tree fingerprint is not reproducible from its stated definition — a self-vouching artefact. |

Full evidence and reproduction: `01-CD-AC-002-AND-THE-SCOPING.md`,
`02-CD-AC-005-AND-001.md`, `03-CD-AC-012-AND-UV6.md`, `arms/`, `probes/`.

### The single most important structural observation

**Every one of ASR3-F02, F04 and F05 is the same defect at three different doors:** the
value types re-establish their fields correctly and the closures are genuine — I confirmed
`PanelRow`, `Contribution`, `DialSpec`, `SourceRecord`, `StalenessWindow` and
`FreshnessEvidence` all really do re-establish — **but the ENTRY POINTS do not require the
value types.** The codebase enforces exact type at 20 sites, including
`type(spec) is not DialSpec` and `type(source) is not SourceRecord`. It is absent at
precisely the two public entry points of the two judgement paths — `resolve_panel(row=…)`
and `evaluate(config_snapshot=…)` — and at the model boundary. **The guard is on the class;
the door does not ask for the class.** That is `GUARD_THE_INSTANCE_NOT_THE_CLASS` inverted,
and it is the third variation of the shape that lost the first two gates.

---

## PER-CRITERION REASONING

**CD-AC-001 — RED.** Both declared tests CONTRAST correctly (0 → 1; the AST guard names
rule A). But ASR3-F05 makes a **ten-year-old observation render as `0.9`** with no source
edit, defeating the `StalenessWindow` ceiling closure (CD-ASR-F06) entirely by supplying a
non-`ConfigSnapshot`. The previously declared consumption residue is also still open — I
measured `fold(Unknown, on_unknown=lambda r: 0.0)` → `0.0`.
*Alternative reading, stated so the PO can weigh it:* one may argue `evaluate`'s argument is
a composition-root responsibility, which would make this **AMBER**. I grade RED because the
project itself reasons explicitly about "consumer boundaries" and enforces exact type at
them everywhere else, and because no declared boundary reserves this route.

**CD-AC-002 — RED.** See the scoping section. A blend publishes from configuration and data
alone. The closure that *was* built (the derivation door) is excellent and I could not break
it — the criterion fails elsewhere.

**CD-AC-003 — PASS (scoped). The strongest work in the deliverable, and I could not break
it.** `CD-RT-003-ENGINE-NO-WITNESS-REACH` contrasts 0 → 1. **I closed the eleventh contrast
myself at the target SHA** — the arm neither Engineer seat nor the Project Lead could take
(UV-3): a throwaway digest-pinned PostgreSQL 16.15, baseline **exit 0, PASS 138 assertions,
0 violations**; planted **exit 1, 9 violations** including a whole-matrix contradiction.
I then verified the catalogue **independently of the check** (PBG-EVID-001): `cd_engine`
**16/16 privilege probes false** on schema `witness`; all six project roles have no
superuser, no BYPASSRLS, no CREATEROLE, no inheritance and **no password**; **zero**
memberships among them; **zero** UPDATE/DELETE/TRUNCATE grants to any project role anywhere;
and PostgreSQL itself refused a real session: `ERROR: permission denied for schema witness`.
*SCOPE OF THIS PASS:* I did not re-run the compose `command:` override or the package-rename
test (CD-ASR-WO2-02 did, and I did not inherit those conclusions — I simply did not reach
them); I did not test the store under load, concurrency or RLS; I swept only the grant
matrix. Within that scope the class is closed and the carrier is measured, not asserted.

**CD-AC-005 — RED, and the grade has moved from the previous audit's AMBER for a stated
reason.** CD-ASR-WO2-02 graded AMBER *because boundary 3 hedged honestly* — "three is the
denominator, not a proof that a fourth does not exist". **That hedge is gone.** Increment 2
replaced it with a stated denominator (402 sites, "asserted BY SET EQUALITY IN BOTH
DIRECTIONS") and increment 3 replaced the wide invariant with an exhaustive positive claim:
*"WHAT STILL EXECUTES, AND IT IS EXACTLY ONE THING: `tzinfo.utcoffset`."* ASR3-F04 shows a
second thing executes and decides the outcome. **A positive exhaustive claim refuted by
execution is the RED shape by this project's own established distinction** (the one
CD-ASR-WO2-02 used to separate CD-AC-002/RED from CD-AC-005/AMBER). The narrowing that
increment 3 made to repair CD-PL-F76 is *still* wider than the closure.

**CD-AC-012 — RED.** All three declared tests CONTRAST 0 → 1, and deny-by-default is the
right shape — it caught `futu-api` by CD-DEP-001 without recognising anything about it.
But the register's stated class ("any distribution named in any dependency manifest … is
refused BY DEFAULT") is refuted by **three independent one-line, manifest-only edits**, one
of which installs a NASDAQ-listed broker-dealer's real order-entry SDK — confirmed by pip's
own parser as a genuine editable requirement. No boundary names the parser; boundary 3
bounds the *file set*, not the *extraction*. Declared boundary 1 (a registered SDK with a
plausible purpose) I re-executed at **exit 0, 149 assertions** — and **that shape on its own
IS compatible with a scoped PASS**, since closing it needs an offline oracle that does not
exist. It is not what fails this criterion; ASR3-F08 is.

---

## UV-6 — `scope: CLASS`, SETTLED (assigned to me because the beneficiary made the call)

**I OVERRULE the retention, on evidence.** The seat's reasoning is honest and correct as far
as it goes — the framework offers only `{INSTANCE, CLASS}`, `pbg/` is protected, and
`INSTANCE` would be a *different* falsehood. But `scope` claims what a clean run **proves**,
and the class as written in the entry is refuted by execution at this SHA. **The defect is
not the value in the field: it is that neither available value is true and the entry does
not say so where the gate reads it** — while the check's own runtime note prints
"SCOPE IS DECLARED_SURFACE, NOT CLASS" into every PASS artefact, contradicting the register
row that PASS is evidence for. Remedies are the Engineer's to choose (PBG-SOD-004).

---

## THE PROJECT-LEAD ITEMS I WAS ASKED TO SETTLE

* **UV-1 — PARTIALLY DISCHARGED.** `git apply --check`: **84/84 clean** (reproduces the PL's
  measurement). I then ran the **whole suite under each of the 14 WO-2R2 variants** — never
  done by any PL seat. Clean baseline passes; the four CD-AC-012 variants fail exactly the
  `test_dependency_registry.py` assertions they are designed to trip; the other ten pass.
  **No anomalous pass/fail pattern.** *Not discharged:* the other 70 corpus patches were
  apply-checked only, as before.
* **UV-2 — DISCHARGED. The regenerated plant is honest, and I checked it personally.**
  Added lines and removed lines are **byte-identical** across the regeneration
  (sha256 `8379f1cd226a60583076f0af0ce3c059ff0673b4f3e6d5eb1441c7e13dfa3629` on both
  `d47a0a0` and `7edb84e`). Only blob hashes, hunk offsets and context lines moved — exactly
  what regeneration against shifted code must change. It contrasts 0 → 1 naming rule A.
  **No finding.**
* **UV-3 — DISCHARGED.** All eleven plants apply clean; **10/11 contrast on the declared
  commands**, and I closed the eleventh live (above). **11/11 now contrast.**
* **UV-4 — REACHED.** All three AMBER criteria re-measured; F03 replicated and exceeded.
* **UV-5 — NOT REACHED.** I did not re-measure the `own_utc_offset` defence-in-depth claim
  (CD-ENG-WO2R2-F05). Stated, not footnoted.
* **UV-6 — SETTLED** above.

---

## WHAT I DID NOT EXAMINE, AND WHY (PBG-ASSURE-012 — stated here, not footnoted)

* **70 of the 84 corpus patches were apply-checked only, not executed.** My 14 tell you
  nothing about the other 70.
* **UV-5 not re-measured** (above).
* **CD-AC-003's compose-override and package-rename arms not re-run by me.** CD-ASR-WO2-02
  ran them; I did not inherit the conclusions, I simply did not reach them. My CD-AC-003
  PASS rests only on arms I ran.
* **The store was not tested under load, concurrency or RLS** — grant matrix only.
* **I did not sweep `check_engine_no_witness_reach` or `check_base_image_digest_pin` for the
  `_yamlmin` reader defect.** CD-ASR-WO2-02 named this "the single most valuable thing a
  next audit could take". **I did not take it. It remains open** — I prioritised the five
  gate criteria and the scoping attack, and I am naming the omission rather than implying
  coverage.
* **Tier-2 dispositions were sampled, not exhaustively verified** — 369 occurrences declared
  at module granularity; I verified the two module claims I could refute and sampled others.
* **No image was built, no container ran the application, no non-root or signal-handling
  proof taken** — FORBIDDEN in WO-2 by PBG-RT-010 and correctly recorded as OWED. **Judging
  them absent is right; judging them a defect of WO-2 would not be**, and I do not.
* **Out-of-scope WO-3..WO-6 items were not litigated.**

## CONTROL BYPASSES AND FRAMEWORK LIMITATIONS OBSERVED

* **NO framework bypass found.** `pbg required-tests verify` computes `GATE: SHUT`,
  `PID_ACCEPTANCE_SATISFIED: NOT DERIVED`, all sixteen criteria not-PASS, with
  `latest_admitted_run: null`. **CD-RULE-001 is structurally enforced, not asserted.** I did
  not touch it and did not admit anything.
* **A real control bypass in the product:** ASR3-F08 — pip installs a dependency the guard
  cannot see, with the assertion count unmoved.
* **A method limitation:** ASR3-F07 — the sweep's forward-edge import closure excludes every
  consumer of a judged value by construction, so its 402-site denominator reads as a whole
  when it is 60.5% of the package's 664 sites.
* **A process limitation:** ASR3-F01 — the tree fingerprint is unfalsifiable in both
  directions. **CD-ASR-WO2-02 raised exactly this and recommended recording the exact
  command; it was not acted on.** I raise it a second time.
* **The variant corpus carries ZERO executable files**; my evidence tree likewise
  (`find -perm -u+x` → 0). PBG-ASSURE-001 satisfied in fact.

## CONTINUATION IMPLICATION — stated separately from the findings

**What is true and what is safe to do next are different calculations.**

**Nothing here is unsafe to LEAVE AS IT IS.** There is no running deployment, no published
envelope, **0 registered egress destinations**, both networks `internal: true`, no image
built, an empty source registry and an empty model registry. Both dials read `Unknown` in
the shipped configuration. **These are latent structural defects, not live incidents.**
Leaving f30e63c in the repository harms nobody.

**What is NOT safe is promoting f30e63c as the WO-2 baseline WO-3 builds on.** WO-3 delivers
the publication layer, the collectors and the model wiring — precisely the code that will
call `number_for_dial_slot`, supply `ConfigSnapshot`s to `evaluate`, hand rows to
`resolve_panel`, and register the first real dependency and the first egress destination.
Every finding above is cheapest to close before that caller exists, and each one gets
harder and more expensive the moment it does.

**On CD-D-076 specifically:** the suspension trigger is met on my evidence. Whether to
invoke Option (C) is the Product Owner's alone. I note only that the architectural review
of Blueprint §7 was *already* ruled the mandatory first item of WO-3, and the substance of
my CD-AC-002 finding is exactly what that review is for — the engine owning the model
lifecycle so a shared mutable object cannot be injected. **The remedy the PO already chose
is the right one; my finding is that it cannot wait behind a scoping that does not hold.**

## NEXT SAFE GATE (PBG-ASSURE-004)

**A Product Owner disposition on CD-D-076 FIRST — before any further Engineer dispatch.**
The scoping that CD-AC-002 reached this gate on has fallen, so the next Engineer brief
cannot be written until the PO rules whether Option (C) applies. Only the PO can make that
call (PBG-AUTH-003), and an Engineer dispatched before it would be building against an
unsettled premise.

Then, and only then, **a bounded WO-2R3 ENGINEER dispatch scoped to the ENTRY-POINT
ADMISSION CLASS** — not to the three findings individually. The class question is:
*which public entry points accept a value whose type they never establish, and decide
something with it?* The three I found (`resolve_panel(row)`, `evaluate(config_snapshot)`,
`DialSpec.contribution_model`) are a denominator of three, not a proof that a fourth does
not exist — and the sweep cannot answer it, because its closure excludes consumers.
**It must NOT be scoped as "add `type(row) is not PanelRow` to `resolve_panel`"** — that is
the instance game, and it is the error the first gate caught.

Separately and NOT folded in: the CD-AC-012 extraction gap (ASR3-F08) is parser work with
its own denominator question; the documentary findings (ASR3-F01, F06, F07, F09) are
correction work.

**Do not re-run this gate until ASR3-F02, F04, F05 and F08 are closed.** A fourth attempt
that has not addressed them would fail on the same evidence.

---

## TARGET INTEGRITY ON RETURN

```
HEAD               f30e63cbac6782ec5d7789071ee26be0ba7fe2e5   == dispatched target
tree object        01da44b51e07dfb2e71170f4f19b6db09814b981   == at boot
git status         0 lines          untracked  0
tracked files      392                          __pycache__ / .pytest_cache  0
```

**THE AUDITED TREE IS BYTE-IDENTICAL TO THE SHA I WAS DISPATCHED AGAINST.** Nothing was
executed inside it; every arm ran in a /tmp extraction.

I cannot confirm the dispatch's `target_tree_fingerprint` because it is not reproducible
from its stated definition (ASR3-F01). **In its place I record two fingerprints WITH their
construction, so the next party can reproduce them:**

```
git rev-parse HEAD^{tree}
  -> 01da44b51e07dfb2e71170f4f19b6db09814b981

find . -path ./.git -prune -o -type f -printf '%P\n' | sort | xargs -d'\n' sha256sum | sha256sum
  -> 41ca051870725246f205c3b2ca98234f6a0073ff6c3f8ed4c3b387091962dad0
```

**SD-3 teardown verified:** containers matching `cd-asr-wo2r2-` → **0**; volumes → **0**;
**36 other containers on this host untouched** (`arms/SD-3-teardown.txt`). Image pinned by
digest `postgres@sha256:cf78e766…`. Credential generated at runtime, destroyed, and its
value appears in no artefact.

---

CD-ASR-WO2R2-01 · target f30e63cbac6782ec5d7789071ee26be0ba7fe2e5 · read-only · nothing
repaired (PBG-SOD-004) · no acceptance granted (PBG-AUTH-003) · `latest_admitted_run`
untouched and still null (CD-RULE-001) · nothing under `pbg/` modified.
