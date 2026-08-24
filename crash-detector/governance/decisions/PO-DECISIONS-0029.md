# PO decisions — Q34: freshness is enforced AT THE GATE, document-internal; the STALE half of the constitution is finally built
date: 2026-08-24 · authority: Product Owner (Trinity) · auditor routed Q34 to Matt; ruled with Matt's override reserved

16B-CONTRACT-CLOSURE assured RED — and it is the clean kind: the auditor DECLINED ruling 5's
"the test was wrong" clause and said "the test was right and the fix is bounded, the first
time both are true on this row." Rule CC HELD (both exhaustiveness premises attacked and
held; closure steps 1-4, 6, 7 TRUE). It fails at step 5 alone, and the reason is a product
truth: **a schema can REQUIRE a stamp but cannot COMPARE one. Sixteen increments guarded
MISSING; nothing in this product has ever computed STALE.** The MISSING half of CD-AC-001 is
now closed by construction; the STALE half was never built.

**1. Q34 IS RULED (a): FRESHNESS IS ENFORCED AT THE PUBLICATION GATE, computed PURELY FROM
THE DOCUMENT.** A fourth refusal stage: `published_utc − dial.as_of_utc` compared against the
dial's `staleness_window_seconds`. If the data is older than its window, the dial CANNOT
render calm — REFUSED at the gate. Purely document-internal (no external clock), so it does
NOT reopen BP-AMENDMENT-0001 §D.3's no-caller-clock rule. This keeps BOTH halves of CD-AC-001
enforced at ONE constitutional chokepoint, by construction: MISSING via the closed contract
(Rule CC), STALE via the document-internal freshness comparison.

**Not (b)** — staleness as a detector-only concern with the gate guarding absence alone —
because it scatters the constitutional guarantee across two layers and makes the STALE half
depend on the detector being trusted rather than enforced at the chokepoint. Recorded as the
alternative; Matt's to choose. Until he says otherwise, (a) stands.

**2. THE PREDICATE — a layered answer.** The SIMPLE per-indicator `staleness_window_seconds`
(from the mapping file) is the GATE'S CONSTITUTIONAL FLOOR: dead simple, always applies,
absolute — "this data is too old to be called calm, period." The REGIME-AWARE staleness of
CD-RT-009 / CD-AC-009 (the window that TIGHTENS in stress — "the same age that passes in calm
fails in stress") rides ON TOP as a detector-layer refinement that can only make the refusal
MORE conservative, never less. The gate floor never loosens; the regime layer only tightens.

**3. RULING 5 EXTENDS, unchanged in spirit:** a dial that cannot prove present AND fresh is
refused by construction. "Present" is the closed contract (done); "fresh" is the gate
freshness stage (this ruling). The completion test now covers both: a dial older than its
window carrying calm is refused, and a never-before-named state carrying calm is refused.

**4. GATE vs DETECTOR, complementary not competing:** the DETECTOR produces the stamps
(`as_of_utc`, and marks a dead FEED via feed_liveness when a fetch fails); the GATE ENFORCES
the refusal by comparing them. Q34(a) builds the gate enforcement; the detector-side liveness
marking (the still-owed 16C) produces what the gate compares. Both complete CD-AC-001's stale
half.

**5. Dispatch — the GATE FRESHNESS-STAGE increment**, sequential single-seat: the fourth
refusal stage per ruling 1, the simple-window floor per ruling 2, graded against the extended
ruling-5 completion test. Preserve 295bdbe (Rule CC held, strictly better). On GREEN: the
detector liveness marking (16C), THEN register the rows. CD-D-181 sequential-only; be0b355
frozen. A311-F1 (root degraded_inputs one container deeper) folded in fail-closed.

**6. Standing:** two dials never blended; missing AND STALE never render calm — MISSING by
closed contract, STALE by document-internal gate comparison, both at one chokepoint by
construction; weights provisional pending backtest; system safe.
