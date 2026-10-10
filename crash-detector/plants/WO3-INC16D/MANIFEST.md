# WO-3 INCREMENT 16D — the contrast set for the GATE FRESHNESS STAGE

**Written and run by `CD-ENG-WO3-12`** under
`governance/dispatch/CD-DISPATCH-WO3-INC16D-GATE-FRESHNESS-ENGINEER.yaml`, authority
`governance/authority/CD-AUTH-0001-project-lead.yaml`, product authority
`governance/decisions/PO-DECISIONS-0029.md` (`Q34` ruled (a)).

**Nothing in this directory is evidence and nothing in it is assurance.** The patches exist so
that every claim this increment makes is measured **by contrast** rather than asserted from one
side. **They are never applied to the worktree**: every arm below ran in its own throwaway
`git archive <sha> | tar -x` extraction under `/tmp`, and the worktree was never mutated
(`CD-PL-F154`).

---

## *** RC IS TAKEN FROM `git apply` AND IT IS CHECKED ***

`CD-ASR-WO3-11` disclosed against itself that its first arm runner read each patch **from the
extracted tree**, where the patch did not exist at the older tip; `git apply` returned **128**,
and the instrument then ran on an **UNPATCHED** tree — measuring nothing while looking like a
result. That is `CD-ENG-F02`'s defect class, committed inside the audit of the increment that
exists to close it.

`run_arms.sh` therefore reads every patch from an **absolute path in the repository**, outside
every extraction, and **an apply rc other than 0 ABORTS THE ARM LOUDLY** rather than being run
past. The rc of every arm at both tips is in the table below, including the four that are
deliberately `rc=1`.

---

## THE ARMS

### The contract arms — `A311-F1`, and what limb (b)'s two probes could not see

| arm | what it widens |
|---|---|
| `H1` | **THE AUDITOR'S ARM H, VERBATIM IN EFFECT.** The allowlisted non-dial root property `degraded_inputs` becomes an **ARRAY of CLOSED objects** that may carry `#/$defs/detail_level`. **ONE CONTAINER DEEPER THAN THIS ROW'S OWN ARM `CC-H`**, which widens the same class to an OBJECT and is caught. |
| `H2` | The same property as an **ARRAY of OPEN objects**. The objects declare no `detail_level` at all, so a structural check that looked for the NAME would miss it — `additionalProperties` is not `false`, so any key is admissible. **CAPABLE BY OPENNESS RATHER THAN BY DECLARATION.** |
| `H3` | **TWO** containers deeper: an **ARRAY OF ARRAYS** of closed objects carrying a level. If the remedy for `A311-F1` were "a third probe shape", this is the fourth, and the census game would simply move again. |
| `H4` | **THE UNDECIDABLE ARM, AND IT IS THE ONE THAT MATTERS MOST.** `regime` is rewritten as an `allOf` composition. The live gate **still refuses** a calm-carrying object in its place, so **BOTH BEHAVIOURAL PROBES STILL PASS** and a probe-only limb (b) reports the property *affirmatively proved incapable*. **IT IS NOT PROVED — IT IS UNREAD.** |

### The source arms — do this increment's own controls fail at their own seam? (`PBG-ASSURE-017`)

| arm | what it breaks |
|---|---|
| `D1` | **THE FOURTH STAGE, REMOVED.** The one-line call is deleted from `refuse_unless_publishable`. This is `295bdbe`'s behaviour exactly. |
| `D2` | **THE NAIVE FORMULA.** The negative-age branch is removed, leaving `age > window` alone — the implementation a faithful reading of the ruling's words would have produced. |
| `D3` | **SLOT-READING INSTEAD OF THE NODE WALK.** The `_iter_nodes` quantification is replaced with reads of `equity_crash` and `monetary_debasement` — the implementation the dispatch forbids. |
| `D4` | **THE NEWEST STAMP GOVERNS**, instead of the oldest. |
| `CTRL` | **NO PATCH.** The vacuity control. An arm set with no clean arm cannot tell *"the plant did it"* from *"everything is broken"*. |

---

## THE MEASUREMENTS — `git apply` rc, instrument, LIVE GATE, and this increment's own tests

Run twice: once at `295bdbe` (the 16B-CONTRACT-CLOSURE tip this increment starts from) and once
at `f9819fe` (this increment's item-3 tip). **AN ARM THAT IS RED AT THE NEW TIP PROVES NOTHING
UNLESS IT WAS GREEN AT THE OLD ONE**, which is why every contract arm is run at both.

### At `295bdbe` — BEFORE

| arm | apply rc | instrument | LIVE GATE, both surfaces |
|---|---|---|---|
| `CTRL` | — | `PASS — 243` exit 0 | 1970+calm **ADMITTED ×2** · 2099+calm **ADMITTED ×2** · fresh+calm ADMITTED ×2 · UNKNOWN/SPINDRIFT+calm REFUSED ×2 |
| `H1` | **0** | **`PASS — 243` exit 0 — UNMOVED** | **`degraded_inputs: [{source_id, detail_level: calm}]` ADMITTED ×2.** `A311-F1` REPRODUCED IN THIS SEAT'S OWN SHELL. |
| `H2` | **0** | **`PASS — 243` exit 0 — UNMOVED** | the same document **ADMITTED ×2** |
| `H3` | **0** | **`PASS — 243` exit 0 — UNMOVED** | `[[{source_id, detail_level: calm}]]` **ADMITTED ×2** |
| `H4` | **0** | **`PASS — 243` exit 0 — UNMOVED** | everything REFUSED. **A LATENT UNPROVED CLAIM, NOT A LIVE ESCAPE — stated as such and not dressed up.** |
| `D1`–`D4` | **1** | ARM ABORTED | ARM ABORTED |

**`D1`–`D4` DO NOT APPLY AT `295bdbe` AND THAT IS CORRECT, NOT A FAILURE.** They mutate a stage
that does not exist at that tip. The rc is `1`, it was taken from `git apply`, it was checked, and
the runner refused to run anything after it. **Nothing at `295bdbe` was measured for those four
arms and nothing is claimed about them there.**

### At `f9819fe` — AFTER

| arm | apply rc | instrument | LIVE GATE, both surfaces | `test_envelope_freshness.py` |
|---|---|---|---|---|
| `CTRL` | — | `PASS — 260` exit 0 | 1970+calm **REFUSED[`STALE_CALM`]@`/equity_crash` ×2** · 2099+calm **REFUSED ×2** · **fresh+calm ADMITTED ×2** · UNKNOWN/SPINDRIFT+calm REFUSED[`SCHEMA_VIOLATION`] ×2 **UNMOVED** | **92 passed** |
| `H1` | 0 | **`FAIL — 2 violation(s)` exit 1** — limb (b) CAPABLE, one per surface | arm-H document **REFUSED[`STALE_CALM`]@`/degraded_inputs/0` ×2** | 92 passed |
| `H2` | 0 | **`FAIL — 2` exit 1** | **REFUSED[`STALE_CALM`]@`/degraded_inputs/0` ×2** | 92 passed |
| `H3` | 0 | **`FAIL — 2` exit 1** | **REFUSED[`STALE_CALM`]@`/degraded_inputs/0/0` ×2** — note the pointer: the walk went through TWO containers | 92 passed |
| `H4` | 0 | **`FAIL — 2` exit 1** — limb (b) **UNDECIDABLE** for `regime` | everything REFUSED (unchanged) | 92 passed |
| `D1` | 0 | `PASS — 260` exit 0 | **1970+calm ADMITTED ×2 · 2099+calm ADMITTED ×2** — `295bdbe`'s behaviour, restored exactly | **14 failed**, 78 passed |
| `D2` | 0 | `PASS — 260` exit 0 | 1970 REFUSED ×2 · **2099 ADMITTED ×2** | **2 failed**, 90 passed |
| `D3` | 0 | `PASS — 260` exit 0 | the dial rows still flip; the NODE rows do not | **40 failed**, 52 passed |
| `D4` | 0 | `PASS — 260` exit 0 | the dial rows still flip | **2 failed**, 90 passed |

---

## WHAT THE TABLE SAYS, AND IT IS NOT ALL FLATTERING

**1. `A311-F1` IS CLOSED TWICE OVER, AND THE TWO CLOSURES ARE INDEPENDENT.** At the instrument,
by a decision procedure over the property's own closed subschema (`H1`/`H2`/`H3` go `PASS — 243`
-> `FAIL — 2`). At the gate, by construction, because a node claiming `calm` with no stamp cannot
prove freshness — **`REFUSED[STALE_CALM]` on a tree whose contract was widened to admit it.**
Neither closure needed a third probe shape.

**2. `H4` IS THE ARM THAT JUSTIFIES THE WHOLE STRUCTURAL LIMB.** Its live gate is IDENTICAL at
both tips: everything refused, both probes pass, the freshness stage has nothing to say because
nothing conforming carries `calm` there. A probe-only limb (b) would report `regime`
*affirmatively proved incapable of carrying a `detail_level`* on a subschema **it never read**.
The structural limb reports UNDECIDABLE and the instrument goes RED. **"I could not tell" and "it
cannot carry one" are different answers and only one of them is safe.**

**3. THE INSTRUMENT DOES NOT NOTICE `D1` AND THAT IS CORRECT AND IS DECLARED.** Removing the
entire freshness stage leaves `CD-RT-001-MISSING-DATA-NEVER-CALM` at `PASS — 260, 0 violations`,
because **THIS ROW DOES NOT ASSERT THE FRESHNESS STAGE AND MAY NOT TAKE CREDIT FOR IT**
(`DECLARED LIMIT 3` as amended, `DECLARED LIMIT 20`). What notices `D1` is
`tests/test_envelope_freshness.py`, which loses 14 assertions, and the live gate, which returns
to admitting a fifty-six-year-old reading as calm. **THE STAGE IS GUARDED BY A TEST FILE AND BY
NO REGISTER ROW. That is a real gap and it is raised as `CD-ENG-F16D-03`, not hidden here.**

**4. `D2` MOVES EXACTLY ONE ROW, WHICH IS WHAT MAKES IT WORTH HAVING.** Removing the negative-age
branch leaves 1970 refused and 2099 **ADMITTED** — half of the Product Owner's own named plant,
surviving an implementation that looks faithful to the ruling's words. Two assertions catch it.

**5. `D3` AND `D4` ARE THE DESIGN CONSTRAINTS, MEASURED.** Slot-reading loses 40 assertions;
newest-stamp-governs loses 2. Neither is caught by the instrument or by the dial rows of the live
gate — **the node-quantified predicate and the oldest-governs rule are load-bearing and are
guarded only by this increment's own tests.**

## HOW TO RE-RUN IT

```bash
plants/WO3-INC16D/run_arms.sh 295bdbe BEFORE
plants/WO3-INC16D/run_arms.sh <tip>   AFTER
plants/WO3-INC16D/run_register.sh /srv/crash-detector-wo3   # all 30 register lines, rc per line
python3 -B plants/WO3-INC16D/probe_16d.py                   # the graded rows on the worktree
```
