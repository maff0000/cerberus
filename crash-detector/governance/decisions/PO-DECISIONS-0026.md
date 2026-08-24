# PO decisions — the mapping content supplied as repo data; Redis not mandated; liveness ≠ relevance
date: 2026-08-24 · authority: Product Owner (Trinity)

Increment 16A confirmed by measurement (scaffolding sound, no row registered, correct). Its
split from 16B paid for itself: three blockers found with no content in hand and no pressure
to widen a ratified constant. All three are the Product Authority's. Answered.

**1. Q30 — the mapping CONTENT is supplied as a REPO DATA FILE, not a fabric key.** My
error: I named the mapping by a Trinity-host fabric key the build environment cannot read.
The content is now `governance/mapping/indicator_mapping.yaml` (PO-authored, carried into
the repo verbatim) — the ~24 indicators with dial binding, tier weight (PROVISIONAL),
polarity, cadence, per-indicator staleness window, source feed + provenance, and
calculation. The engine registers FROM THIS FILE — no seat invents product meaning. This is
the models-are-data / portability architecture working exactly as designed: the mapping
travels with the container as data.

**2. Q31 — REDIS IS NOT MANDATED; the architecture wording is corrected.** The design has no
Redis, and I will not force one where the app does not use it. The portability constraint is
corrected to: **the movable persistent store(s) the app ACTUALLY uses** — Postgres (movable
named volume, schema+seed in-repo, connection via env) is required; Redis is included ONLY
if and when the design uses it. "Movable SQL/Redis" was my over-specification; the invariant
is *movable persistence + cut-and-paste dev→prod*, whatever stores that means for this app.
(`…:architecture_portability:v1` updated.)

**3. Q32 — LIVENESS AND RELEVANCE ARE TWO QUANTITIES; the single 900s ceiling is wrong.** The
Engineer was right to refuse widening a ratified constant. The fix is structural, not a
bigger number:
- **RELEVANCE / staleness window is PER-INDICATOR data** — how old that indicator's data may
  be for ITS cadence (daily ~4d, weekly ~14d, monthly ~45d, quarterly ~120d). It lives in
  the mapping file (ruling 1). There is NO global ceiling below the slowest legitimate
  cadence. A quarterly lending survey is not a dead feed at sixteen minutes.
- **LIVENESS / publish-freshness budget is SEPARATE** — the ~900s number from PID §5 is the
  freshness budget for the DETECTOR'S OWN compute-and-publish loop and its assurance latency,
  NOT a cap on how old a legitimately-slow indicator's underlying data may be. It keeps that
  meaning and applies to the detector's own heartbeat, not to indicator data age.
- **PID §5 prose is corrected (PO-authored, carried verbatim)** to name the two quantities
  distinctly. `STALENESS_WINDOW_CEILING_SECONDS` is retired as a global relevance cap;
  relevance is per-indicator data; the 900s becomes the named publish/assurance-liveness
  budget. This is CD-RULE-004 applied to a constant: one symbol was carrying two meanings.

**4. THE 16A ASSURANCE RED (D2) IS UPHELD AND FIXED FIRST — it is constitutional.** The
publish gate ADMITS an Unknown dial carrying `detail_level: "calm"` on both surfaces, and
with zero sources every dial is Unknown, so calm-over-unknown is the ONLY state the product
can currently publish — a direct breach of PID §3.2 ("missing data must never render as
calm"). The auditor proved the fix (calm REFUSED on both surfaces, all 43 tests still pass).
This is fixed BEFORE any row registers — the first state this product ever publishes must
not be the one the constitution forbids. Increment 16B's FIRST act is the D2 fix
(the guard refuses calm on an Unknown dial), with the auditor's plant as its contrast.

**5. Q32 REFINED by the auditor and made stronger — THREE quantities on the row, not two.**
The store schema already separates liveness from relevance, but NO CODE READS the liveness
half, so the staleness window is currently the system's ONLY dead-feed detector — and my
"retire the ceiling" would have silently deleted it. Corrected ruling: the row carries THREE
distinct quantities, each read by code: (a) RELEVANCE — how old the data may be for its
cadence (per-indicator, the mapping file); (b) LIVENESS / fetch-freshness — is the FEED dead
(did we fail to fetch within its expected cadence + grace)? — a real field a real dead-feed
detector reads; (c) PUBLISH BUDGET — freshness of the detector's own compute+publish loop
(the ~900s PID §5 number). The staleness ceiling is NOT removed until the liveness detector
(b) exists and reads its field — never delete a control to widen a window. PID §5 prose
corrected to name all three.

**6. D3 HOST-COUPLING GAPS closed (they bite the portability constraint directly).** Two
leaks reproduced: a dell path hidden in an env DEFAULT passes with 0 violations, and a real
dell hostname as `CD_STORE_HOST` passes with 0 violations. Cut-and-paste dev→prod REQUIRES
that no host-specific default survives — a dell default baked into the image breaks the moment
it lands on the cloud host. The host-coupling check must refuse a dell path/host wherever it
appears, DEFAULTS INCLUDED. Folded into 16B.

**7. Dispatch — increment 16B**, sequential single-seat, in order: (i) the D2 constitutional
fix (ruling 4); (ii) the three-quantity liveness/relevance/publish model (ruling 5) with the
dead-feed detector actually reading its field; (iii) the D3 host-coupling closure (ruling 6);
(iv) THEN register the indicators FROM the mapping file (ruling 1) into the portable Postgres
store (ruling 2), honouring per-indicator relevance windows. SLOOS registers PENDING; private
credit gets its ~120d relevance window. Bounded — stop at a reviewable boundary. Fresh
Assurance seat follows (PBG-SOD-001). CD-D-181 sequential-only stands.

**8. Q33 — the version string must DISCRIMINATE; I make the decision the seat wasn't scoped
to make.** `schema_version 1.1.0` now names two different contracts (one URN → two
documents), so the version has lost its discriminating power. Ruling: bump the envelope /
affected contract version so ONE version string identifies exactly ONE contract shape.
Folded into 16B; the "decision nobody was allowed to make" is now made, by the seat that may.

**9. THE CONSTITUTIONAL FIX MUST BE REGISTER-WIRED, not test-only (CD-RT-002 finding).** The
calm-over-unknown refusal currently holds only in `tests/`, and `tests/` do not feed the
gate — a register-wired instrument PASSES identically on a tree where the fix is fully
reverted. That is "the controls exist and nothing runs them" one hop sideways, and it is
unacceptable for a CONSTITUTIONAL guarantee. 16B adds a REGISTER-WIRED negative control (one
the gate actually reads) that FAILS if calm-over-unknown is ever admitted — the guarantee
must be carried by a live instrument, not a memorial in tests.

**10. THE NO-BLEND GUARD IS CLOSED STRUCTURALLY, not by extending a blacklist.** The
corrected CD-AC-002 guard still admits 8 of 14 blend shapes (including `*readings` varargs
that slip its own blacklist word). Do NOT play whack-a-mole with shapes — that is the census
game this estate has paid for repeatedly. Close it by CONSTRUCTION: a judgement function
receives exactly ONE dial's data, enforced structurally, so no blend shape can arrive
regardless of spelling. 16B; contrast plant is the `*readings` shape the current guard misses.

**11. CD-PL-F179 accepted, on the record honestly:** the "CD-AC-002 AMBER / CD-AC-005 RED"
grades have been carried from assurance history, not computed — the register reports all 18
UNDECIDABLE. That is correct and disclosed: the register computes only what a run admits, and
no run is admitted yet. The grades are auditor verdicts, and the record now says so rather
than implying a register instrument that has not run.

**12. PID §5 prose correction (the three-quantity naming) is a separate PO record-act**,
carried at the next boundary once I have §5's exact bytes to author the verbatim replacement.
The CODE change (ruling 5's three quantities) is 16B and does not wait on the prose.

**13. Standing:** two dials never blended (now closed structurally, not declared); missing
data never renders calm (now register-wired, not test-only); weights provisional pending
backtest; lane branches from frozen be0b355; system safe to leave running OR stopped.
