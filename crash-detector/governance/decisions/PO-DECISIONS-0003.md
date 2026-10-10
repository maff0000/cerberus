# PO decisions — CD-AC-002: what closes it, and when
date: 2026-08-19 · authority: Product Owner (Trinity)

**The engineer's restraint is endorsed**: refusing to order a guard that looks like a closure —
"an identity check is defeated by two instances sharing a class attribute, a purity probe by
memoisation" — is the lesson of two gates, applied before it cost a third.

**RULING: (B) and (A) together, bound so neither can drift.**

1. **CD-AC-002 is ruled at WO-2 scope on a measured basis** (which layer refused what, per
   CD-PL-F74): a WO-2 candidate registers no model, no source, deploys nothing and has no
   publication layer — the injected-model route is not in WO-2's population. The criterion at
   WO-2's gate covers every route that needs no injected model. **The full-width criterion is
   NOT narrowed, superseded or softened** — it remains MANDATORY and travels to WO-3.
2. **Blueprint §7 RETURNS FOR ARCHITECTURAL REVIEW as the mandatory FIRST item of WO-3**, before
   any collector or model wiring: the engine owns the model lifecycle, so a shared mutable
   object cannot be injected — closure by construction, not another guard. This converts my
   CD-D-073 standing condition: the carrier/admission class has now shown open a third time
   (caught upstream of the gate, which is the loop working); the architectural review is no
   longer contingent — only its timing was mine to set.
3. **Model integrity attaches to CD-D-005** (the ingredient register, owed by the PO) — a model
   is an ingredient with provenance, and the PO's register will say what the number should be
   traceable to. The engineer was right that admission alone cannot know it.
4. **The scoping itself is attack surface.** The third Assurance seat is EXPLICITLY invited to
   attack this ruling's basis: if it can exercise an injected-model route inside a WO-2
   candidate's real population, the ruling falls and (C) suspension applies. A PO scoping a
   criterion at the moment of failure is the acceptance-semantics trap; the only honest defence
   is handing the auditor the knife.

**Proceed**: complete held increments 2 and 3; then the THIRD fresh Assurance seat, fresh
variants, with this decision record in its brief. Gate: PASS on all five as ruled here, no
waiver, latest_admitted_run null until the paired verdict rule is satisfied.
