# PO decisions — the source set is named; the WO-3 hold is RELEASED; registration begins on the portable container
date: 2026-08-24 · authority: Product Owner (Trinity), source set ratified by Matt

**1. Q25 IS ANSWERED — the source set is named and ratified.** Matt named the indicator set
(2026-08-24) and accepted the dial mapping. It is `trinity:pbgv2:crash_detector:indicator_dial_mapping:v1`:
~24 indicators across two dials — the delivered playbook 20 (`trinity:playbook:as_built:v1.0`)
plus the Quantical-reference additions and private credit stress — each with dial binding,
tier weight (×3/×2/×1) and polarity. The Matt hold is RELEASED.

**2. ARCHITECTURE IS BINDING (`…:architecture_portability:v1`).** Independent Docker
container; SQL + Redis in movable named volumes; all config via env; cut-and-paste dev
(dell) → prod (cloud). The mapping lives as REGISTRY DATA, portable by construction. Every
WO-3 increment is written to this constraint and the deploy audit verifies cut-and-paste
reproducibility before go-live.

**3. WEIGHTS ARE PROVISIONAL — BACKTESTED, NOT ASSERTED.** The tier weights are starting
values. They are calibrated by backtest against historical crash + debasement episodes
(R2D2 / Apollo / Athena, sentinel days, backtest-first rule) "until the balance is right"
(Matt). No weight is trusted on assertion. Backtest calibration is its own increment after
the sources register and score.

**4. SLOOS IS SOURCE-IDENTIFIED, not unknown-for-lack-of-a-source.** The ARGUS playbook
already sourced it: FRED DRTSCILM (C&I, auto) + manual NDFI quarterly (Fed SLOOS Table 2
Q14). It registers from those; until registered in this container it shows PENDING, never a
false green.

**5. Q28 + Q29 carried as the first act of increment 16:** correct the PID prose
NEW_REQUIREMENT → DERIVES for CD-AC-017 (the register already records DERIVES; PO-authored
one-line prose fix, carried verbatim); detail_level attaches PER-DIAL.

**6. DISPATCH — INCREMENT 16, sequential single-seat, bounded.** Register the indicator
sources per the mapping into the portable container: each with provenance (CD-D-005),
declared staleness window, and its dial binding + provisional weight as registry data. Start
with the automatable feeds (FRED / market series); SLOOS as DRTSCILM-auto + NDFI-manual;
private credit stress with a WIDE staleness window (its latency is the point — absence reads
Unknown, never calm). Stop at a reviewable boundary; do not attempt all ~24 in one increment.
Then the DETECTED tier (CD-AC-018 witness divergence) and CD-AC-017 provenance-admission
follow as their own increments; then backtest calibration. CD-D-181 sequential-only stands.

**7. Standing:** two dials never blended; missing data never renders calm; lane branches from
frozen be0b355; system safe to leave running.
