# PO decisions — the constitution is closed by construction; Q35: register-wire the freshness control, declare the gate/detection split
date: 2026-08-24 · authority: Product Owner (Trinity)

**THE MILESTONE, RECORDED PLAINLY:** 16D-GATE-FRESHNESS assured AMBER, and the ruled
completion test is MET FOR THE FIRST TIME ON THIS ROW. An auditor dispatched to DISBELIEVE
"closed by construction" and to BUILD the counterexample reported: "On the contract this
product ships, I could not." A dial older than its window carrying calm is REFUSED; a
never-before-named state carrying calm is REFUSED — both surfaces. After sixteen increments,
BOTH halves of CD-AC-001 ("missing OR stale never renders as calm") are now enforced BY
CONSTRUCTION — missing by the closed contract, stale by the document-internal gate stage —
verified against 3,652,059 civil dates with zero mismatches and §D.3 confirmed unreopened
three ways. The hardest thing in this build is done. The AMBER is two bounded residuals, not
a hole in the guarantee.

**1. Q35(a) — YES, the fourth refusal stage gets its OWN Required Test Register row, and it
lands BEFORE 16C.** This is ruling 9's principle (a constitutional guarantee is carried by a
REGISTER-WIRED instrument, never test-only) applied to the freshness stage: the guarantee is
proven today, but proven in tests is not proven in the register. Register-wire it — its own
row, a negative control the gate reads, failing if stale-carrying-calm is ever admitted —
and land it before 16C so the control is registered before the lane moves on. "Then register
the rows" (ruling 5) meant the INDICATOR rows; this CONTROL row comes first.

**2. Q35(b) — the gate's limit is DECLARED, and source-honesty is the DETECTION tier, NOT
"permanently outside enforcement."** The gate enforces DOCUMENT-INTERNAL freshness
(published_utc − stamp vs window). It cannot catch a source that CONSISTENTLY LIES about its
own stamp — a feed that stamps every reading `now()` regardless of true data age is
internally consistent and passes the gate. That is the SAME CLASS as the F1 forgery, and it
has the SAME answer already ruled in the three-tier perimeter (PO-DECISIONS-0018/0019): the
gate is PREVENTION of what is document-internal; a lying source is caught by DETECTION —
witness divergence + provenance (CD-AC-018), where a source's claimed freshness is
corroborated against witnesses and divergence is the alarm. So: 16C's detector-side liveness
carries the HONESTY OBLIGATION — stamps are provenance-backed and witness-corroboratable —
and the guard's DECLARED SCOPE states the split honestly: gate enforces internal freshness,
detection tier enforces source honesty. It is NOT recorded as unenforceable; it is enforced
one tier out, owed at WO-3 when real sources and their witnesses land.

**3. Dispatch — the CONTROL-ROW increment**, sequential single-seat: register-wire the
freshness refusal stage as its own Required Test Register row (ruling 1); add the guard's
declared-scope statement of the gate/detection split (ruling 2, documentary); preserve
0e80a09 (completion test met, strictly better). On GREEN, 16C RELEASES — the detector-side
liveness with the honesty obligation — THEN register the indicator rows. CD-D-181
sequential-only; be0b355 frozen.

**4. Standing:** two dials never blended; missing AND stale never render calm, BY
CONSTRUCTION, both halves, verified by a disbelieving auditor who could not break it; source
honesty owed to the detection tier at WO-3; weights provisional pending backtest; system safe.
