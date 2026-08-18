---
document: PID — Product Intent Definition
product: Crash Detector — standalone market stress instrument
version: 1.0
status: RATIFIED by Matt 2026-08-19 — all PO recommendations accepted; issues dealt with as we go
owner: Product Owner (Trinity)
authority: Matt — final
project-root: /srv/crash-detector on dell-debian (DEV) — per Matt's topology ruling 2026-08-19
framework: PBGv2, instantiated as a pinned release at /srv/crash-detector/pbg/
profile: PBG-OPERATED (G1–G6 + G8 runtime health, G9 for its own state)
authority-class: ADVISORY ONLY — ratified by Matt 2026-08-18
amendment: PO only; sections marked CONSTITUTIONAL by Matt only
---

# Crash Detector — Product Intent Definition

## 1. Purpose — CONSTITUTIONAL

**Tell Matt, early and honestly, when the conditions for an equity crash or a monetary
debasement are building — so that a decision made in calm can be executed mechanically under
stress.**

Standalone. Extracted from ARGUS into its own container, because a warning system must not fail
for reasons that have nothing to do with the market — the ARGUS-coupled instrument died twice on
ARGUS internals.

**Authority: ADVISORY ONLY.** It detects, scores, explains, alerts, and publishes
machine-readable state. It never executes, never places or alters anything, and its output is
**evidence and input, never authority**. Any downstream system that acts on it is Class E and
must cross the Layer 3 gate on its own account.

## 2. Users and outcomes

Matt (primary) · Trinity (strategy and posture) · Trader/Solo (execution context) · the public
(market read only).

Outcomes: a dial Matt trusts enough to act on without re-deriving it; pre-committed triggers
that fire mechanically; a public market read carrying no private information whatsoever.

## 3. Non-negotiable doctrine — CONSTITUTIONAL

1. **Two dials, never blended.** Equity crash and monetary/debasement fail in opposite
   directions; averaging cancels the signal.
2. **Missing data must never render as calm.** Absence of signal is not absence of risk.
3. **The AI review has zero authority over headline numbers.** Two questions only: what changed,
   is the plan still fit.
4. **External sources are witnesses, never ingredients.** A witness that is also an ingredient
   cannot corroborate anything. Divergence is the alarm.
5. **Hard public/private split.** Market read outward; anything touching the book stays private.
   Not the same container, let alone the same page.
6. **No unexplained mappings.** We do not copy a score-to-probability curve we cannot account for.

Prohibited behaviour: rendering stale or missing data as calm · publishing anything derived from
the book · letting an AI author or adjust a headline number · blending a witness into the score ·
presenting a backfilled series as a track record.

## 4. Scope, v1

- Equity crash dial; monetary/debasement dial (USD + GBP first-class; EUR optional).
- Drill-down proportional to risk: calm = dial + one line; elevated = the categories carrying
  the score; acute = everything, ranked by contribution.
- Each dial paired with its own history against the S&P — **the signal is in the slope, not the
  level**.
- Regime-aware staleness: windows tighten when vol spikes; alert on **cadence breach**, not age;
  monitor the **publication layer**, not only ingestion.
- External witnesses side-by-side: OFR FSI + Quantical composite.
- Gold/equity **rotation-readiness ratio** (new — serves the committed wealth strategy: measure
  the rotation, not the crash).
- AI wave-1 → wave-2 transition monitor (new).
- One AI review, two questions, with validators: `no_headline_authorship`, `no_crash_certainty`,
  `no_market_is_safe`, `no_missing_data_as_safety`.

**Non-goals:** portfolio execution · tax/domicile advice · replacing the two-floor advisory
(that product *consumes* this one). The floors re-base question (old D5) is **transferred to the
advisory product**, not silently dropped — the detector's public read never touches the book.

## 5. Consequence model and assurance latency budget

| Property | Value |
|---|---|
| Class | C — detection & alerting, advisory |
| Blast radius of a false "done" | a missed regime signal, or a false alarm informing a human decision; **no direct action** |
| Kernel required | No (Layer 2 guardrail when it graduates; gates nothing) |
| Layer 3 gate required | No — nothing irreversible; the freeze does not touch this project |
| **Assurance latency budget** *(proposed, Matt to ratify)* | pipeline/publication failure independently detectable ≤ **15 minutes**; a cadence breach alerts within **one publication cycle**; a candidate defect is caught at the register gate before promotion |

## 6. Acceptance criteria

Stable IDs; the project's Required Test Register derives its population from THIS section and is
compared. Every criterion MANDATORY unless marked. Semantics are the proposition to satisfy —
most are not "exit 0".

| ID | Criterion | Acceptance semantics — satisfied when |
|---|---|---|
| **CD-AC-001** | Missing or stale input never renders as calm | plant: kill a feed → the affected dial shows `UNKNOWN`/`DEGRADED` within budget, **never** a calm reading |
| **CD-AC-002** | The two dials are never blended | no code path combines them into one number; a planted blend fails the register |
| **CD-AC-003** | Witnesses are side-by-side, never ingredients | score computed with witnesses unreachable is byte-identical; witness feeds removed → dials unchanged, witness panel shows `WITNESS UNAVAILABLE` |
| **CD-AC-004** | Witness divergence raises the alarm | plant: force witness disagreement beyond threshold → divergence alert fires |
| **CD-AC-005** | `WITNESS UNAVAILABLE` ≠ `WITNESS AGREES` | plant: kill witness feed → panel degrades to UNAVAILABLE, never to agreement |
| **CD-AC-006** | The public surface carries zero private data | plant: private/book-derived key present in the publication path → publication **refuses**; automated scan of the public artefact finds no private field |
| **CD-AC-007** | AI review cannot author a headline | `no_headline_authorship` validator: plant an AI-written headline mutation → refused; the four validators each fail their planted violation |
| **CD-AC-008** | Cadence breach alerting on the publication layer | plant: halt publication while ingestion continues → alert within one cycle |
| **CD-AC-009** | Regime-aware staleness windows | in a planted high-vol regime, the staleness window tightens; the same age that passes in calm fails in stress |
| **CD-AC-010** | History is honest | no backfilled point presented as live track record; series carries first-published timestamps |
| **CD-AC-011** | Slope is first-class | each dial exposes its history and slope against the S&P in machine-readable form |
| **CD-AC-012** | No execution pathway exists | a test asserts the codebase contains no broker/order/execution interface; advisory-only is structural, not policy |
| **CD-AC-013** | Rotation-readiness ratio published with provenance | ratio present, inputs named, timestamps carried |
| **CD-AC-014** | Runtime health externally observable | liveness, freshness, last-evaluation, degraded state independently readable; stopping the service is detected inside the budget |
| **CD-AC-015** | Recovery proved from the copy | detector state restored from backup on a clean host; proof read from the copy |
| **CD-AC-016** *(advisory)* | Wave-transition monitor operative | wave-1→wave-2 indicator publishes with declared inputs |

## 7. Data architecture — decision D1, for ratification

**PO recommendation: OWN COLLECTORS.** Standing recommendation since 2026-08-08, sharpened
2026-08-16: consuming a published artefact cross-site makes a public production service's
failure mode *silent* — a stale dial saying calm, which doctrine §3.2 forbids. All inputs and
computation ours; witnesses read-only external. Known-fragile: Quantical's undocumented
`price_history` endpoint — treat as disposable, never load-bearing.

## 8. Delivery and assurance policy

- **Topology (Matt, 2026-08-19):** independent Docker container; project root
  `/srv/crash-detector` on dell-debian; PBGv2 instantiated as a **pinned release** at
  `/srv/crash-detector/pbg/`; PL engaged from that root. The framework is never modified in situ.
- **Standing deployment lane (Matt, 2026-08-16):** built on dell = DEV → **R2D2 ratifies** →
  only then PROD on cloud. Dev never on cloud; prod never on dell.
- **Assurance policy (declared here, PO-owned):** internal loop (Engineer → Auditor → PL) every
  candidate; **external, party-independent (R2D2)** at: first production release · any change to
  the public publication surface · any change to doctrine-bearing controls (CD-AC-001..007).
  Matt dispatches; the PO raises the need.
- Old D7 (team comms path) stays off this critical path — Matt dispatches directly.
- Standing rulings preserved: against adopting Quantical/MacroMicro backfilled series; against
  blend-and-check double use; against copying unexplained mappings.

## 9. Ratification record — signed by Matt 2026-08-19

1. §1 purpose and §3 doctrine — the CONSTITUTIONAL sections (his pen, unchanged from the held
   draft he shaped).
2. **D1: own collectors** — the one real architecture decision.
3. **D6 resolved as doctrine:** witnesses strictly side-by-side, no influence on drill-down —
   CD-AC-003 makes it structural. *(Was open; this PID closes it consistent with doctrine §4.)*
4. The assurance latency budget in §5.
5. The acceptance criteria in §6 as the register population.
6. Old D3 (oil transient rule that never matures) — **folded into scope**: the standalone
   rebuild implements the maturation rule correctly rather than porting the defect. Its ~+0.20
   suppressed stress contribution is the reason it cannot be carried silently.
