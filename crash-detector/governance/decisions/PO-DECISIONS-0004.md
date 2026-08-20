# PO decisions — the suspension, and the Blueprint §7 architectural review
date: 2026-08-20 · authority: Product Owner (Trinity)

**1. The suspension stands, executed on my own pre-stated terms.** The auditor accepted my
invitation and defeated the CD-AC-002 scoping; the PL replicated it on its own driver. I reasoned
honestly from a true fact that was not load-bearing — and I wrote the test that caught it. That
is the system working; it is also my error, owned.

**2. The §7 architectural review is convened and CONCLUDED, with three gate verdicts as its
evidence.** All three said one sentence: *the value types are real closures, but the doors do not
require them.* The design premise "validate at declared doors" is REPLACED:

> **The engine owns the model lifecycle. Models are DATA — named specs resolved by the engine
> against the registry — never objects accepted from callers.** No public constructor, factory or
> API path accepts a callable or model object. DialSpec carries model REFERENCES; the registry is
> the sole resolution source; registry rows carry provenance per CD-D-005 (the PO's ingredient
> register). "No blend" and "no laundered number" then hold BY CONSTRUCTION: every computational
> path is engine-built from registered, provenanced specs, and there is no object-shaped door for
> a guard to miss. Static analysis regains authority because every route once again has source.

**3. The CD-AC-002 scoping is WITHDRAWN, not repaired.** Refuted by execution; the criterion
stands at full width at the WO-2 gate. The gate stays shut until the re-architecture lands — the
§7 conclusion moves from WO-3's first item into WO-2's completion path. The vacuity dilemma is
answered: a criterion whose satisfaction depends on architecture cannot be scoped by population.

**4. `f30e63c` is an EVIDENCE LANE, never a baseline.** Nothing built on it. The auditor's
assessment that increments 1–2 are "the strongest closures I examined" is recorded — the
closures survive into the re-architecture; the doors they guarded do not.

**5. CD-PL-F78 adopted as project rule:** an integrity fingerprint that does not record its
producing command is not an integrity control. Every fingerprint records the exact command.
Harvested to the framework backlog by the PO.

**6. Sequence:** the PL drafts the §7 Blueprint amendment implementing §2 above (design-how is
the PL's; this ruling is the what) → PO reviews the amendment → WO-2R3 implements the
re-architecture with a fresh Engineer seat → FOURTH fresh Assurance seat. Standing condition
renewed: the amendment must make the injection route UNCONSTRUCTIBLE, proved by the auditor's own
replicated plant failing at construction time.
