# PO decisions — Q33: close the CONTRACT so the affirmative guarantee is achievable; my completion test did its job
date: 2026-08-24 · authority: Product Owner (Trinity) · the auditor routed Q33 to Matt; ruled with Matt's override reserved

16B-FIX-5 assured RED, and the RED is the resolution, not a setback. The auditor did NOT
return a tenth shape — it proved (as ruling 5 licensed it to) that **a RECOGNISER cannot
satisfy an AFFIRMATIVE requirement**. The instrument's `False` means "nothing here names a
property `state`"; the constitution's `REFUSED` means "this dial cannot prove present +
fresh." Every escape — a `status` spelling, a 25-deep nest past the cap, `present: false`
with a stale stamp the recogniser never reads — lives in that gap, and no list entry closes
a category error. **My ruling-5 completion test was RIGHT to exist: it falsified the
instrument's architecture, which is precisely what a completion test is for. I own that the
recogniser could not meet it — that is the finding, not a failure of the test.**

**1. Q33 IS RULED (a): CLOSE THE CONTRACT.** The envelope contract MANDATES that every dial
carries a well-formed `state` at a CANONICAL PATH (fixed location, not arbitrarily nested),
with present + freshness semantics REQUIRED by the schema. Then: malformed, missing,
mis-spelled, over-nested, or `present:false`-stale is REFUSED AT CONTRACT VALIDATION —
deny-by-default at the schema boundary, which the gate already runs — and within that closed
shape the value check is sufficient. This is the same principle that has carried this whole
build: close the contract, deny by default at the boundary, and the check inside a closed
space is enough. It makes ruling 5's completion test ACHIEVABLE, because the contract
guarantees the alphabet the check ranges over. Bounded, not a from-scratch re-pricing.

**Not (b)** — inverting the default for all root properties and re-pricing the tail from
scratch — works but pays far more for the same guarantee. Recorded as the alternative; Matt's
to choose if he prefers the heavier, more general form. Until he says otherwise, (a) stands.

**2. RULING 5 STANDS, reframed.** The completion condition — a dial that cannot prove
present+fresh is refused BY CONSTRUCTION — is unchanged and correct. What changes is HOW it
is achieved: not by a recogniser searching an open space, but by a CLOSED CONTRACT that makes
the space finite and the proof mandatory. The completion test now grades the closed-contract
instrument and is achievable.

**3. Preserve `8398741`** — strictly better than `dd40407`, nothing reverted. FX16 (the item
the FIX-5 seat added beyond the ruling) passed clean and is kept.

**4. A310-F1 (the depth-cap FX15 that copied the number but not the fail-closed handling —
25-deep answers a silent `False`) is a SEPARATE BOUNDED FIX**, fail-closed, folded into the
contract-closure increment (a closed contract with a canonical path makes deep nesting
unreachable anyway, but the cap must still fail closed, not open).

**5. Dispatch — the CONTRACT-CLOSURE increment**, sequential single-seat: mandate the
canonical `state` shape in the envelope contract (deny-by-default at validation), fold in
A310-F1 fail-closed, graded against ruling 5's completion test over the now-closed contract.
On GREEN: 16C releases → liveness detector → register the rows. CD-D-181 sequential-only;
`be0b355` frozen. No sixth spelling patch — this is the architectural close.

**6. CD-PL-F203/F204 noted** — the PL again propagated a claim without measuring (twice this
session, once inside a dispatch warning about exactly that). Self-caught, already the standing
IMP-040 pattern; the "hypothesis until run" rule the PL adopted is the remedy.

**7. Standing:** two dials never blended; missing AND stale never render calm — now by a
CLOSED CONTRACT, the architectural form the four rounds were converging toward; weights
provisional pending backtest; system safe, stopped or running.
