# CERBERUS crash-detector — Decision Rule

**Status:** OWNER-CONFIRMED (Matt, 2026-10-13). Numeric thresholds marked *provisional* are placeholders pending the historical replay; the rule's **shape** is fixed.
**Scope:** Epic 1 (crash detector). Everything that *consumes* the output — tranching, regime map, historical analogues, position-level stops — is Epic 2 (WO-2.7/2.8/2.9) and is referenced here only to fix the boundary.
**Depends on:** `MATH.md` (current scoring), the three-statistic redesign (breadth / acute / count — not yet built, see WO-1.3a), point-in-time data discipline, historical backfill.

---

## 1. What CERBERUS decides, and what it does not

CERBERUS is a **macro permission layer**. Per dial it emits a **state** saying whether deployment into the dial's asset class is permitted, paused, or should be reduced, plus a **sizing multiplier**. It never picks instruments, prices or days; that work is done downstream before any purchase. The question it answers is *"is the macro environment one in which buying is allowed right now,"* not *"is this the bottom."*

The two dials remain separate outputs. No blending, no combined score. The consumer sees both states and resolves them under its own rules.

## 2. Objective and ranked failure modes

Sit out crashes; deploy into cheapness over an extended timeline.

| Rank | Failure | Character |
|---|---|---|
| 1 — worst | **Step-down crash**: deploying tranche after tranche into a market that keeps falling | Capital loss, fast, compounds with each tranche |
| 2 | **Opportunity risk**: sitting in cash through a long calm market because permission never comes | Bounded, slow |

The two are not symmetric. The rule makes #1 structurally impossible at the macro layer and caps #2 with a time floor.

## 3. Asymmetric loss — stated once

**Missing a real crash is worse than a false alarm.** The family is already defensive: a false alarm costs months of opportunity; a missed crash costs capital and triggers the step-down scenario.

Therefore: **the halt/exit threshold is hair-trigger; the re-entry threshold is demanding.** Hysteresis in the state machine is how this asymmetry is encoded, and the tranche design in Epic 2 bounds the false-alarm cost further.

## 4. Horizon and reading cadence

The dials are **regime instruments at a 3–12 month horizon**. Readings are computed daily but the *decision* is weekly. A state transition requires **3 consecutive daily readings** beyond the threshold (*provisional*; chosen to kill single-day noise without missing a fast week such as September 2022 — revise after replay). A single day's spike never changes state.

Inputs with weekly/monthly cadence count once per new observation; persistence is counted in readings, so a monthly series cannot by itself satisfy a 5-reading rule and will only ever confirm a transition the daily inputs already made.

## 5. Base currency and calibration targets

**Base currency: GBP.** The GBP monetary dial drives the family's cash/gilts-vs-gold decision. The existing USD monetary dial is retained alongside it because gold and global risk price in dollars; it informs, it does not drive.

Calibration targets (the event each dial is scored against in replay):

| Dial | Event definition |
|---|---|
| `equity_crash` | **Primary:** S&P 500 drawdown ≥ 20% within the next 6 months. **Secondary:** ≥ 15% within 3 months. S&P 500 is the reference because global crashes are US-led and it is the only index with calibration-grade depth; it does not imply the family buys only US equities. |
| `monetary_debasement_gbp` | **12-month real return on GBP cash ≤ −3%** (CPI exceeding Bank Rate by ≥ 3pp over the window) **or gold in GBP ≥ +15% over 12 months**. |
| `monetary_debasement_usd` | Same shape in USD terms; informational, not a decision driver. |

The GBP dial does not yet exist; its inputs and sources are a separate work item (BoE/ONS source verification pending). Until it exists the GBP decision cannot be calibrated, and the rule below applies to it in shape only.

## 6. States

Five states per dial. `UNKNOWN` is a state, not an absence.

| State | Trigger shape (symbols set by calibration) | Equity dial permits | Monetary dial permits |
|---|---|---|---|
| **CALM** | No master in its warning band; count < k; all for the persistence period. **After an ALARM, CALM is reachable only through RECOVERY (post-ALARM lock, below).** | Deploy on schedule, sized by multiplier | Hold cash/gilts normally |
| **WATCH** | Any master in its warning band. *(The breadth-rising-above-B_mid limb is OFF: B_mid is unset, §10.)* | **Halt new tranches**; hold existing | Hedge-asset (gold) tranches permitted, sized by multiplier |
| **ALARM** | **Any one alarm-eligible master beyond its stress threshold** (acute) — **and nothing else**. *(The count rule is REMOVED, provisionally, until count is recalibrated: k is unset, §10, R2D2 PR #14 live re-audit D3. The breadth ≥ B_high rule is dead: B_high is unset, §10.)* | No buying. Deployed capital follows Epic 2's independent drawdown rule | Nominal cash/gilts capped (cap is an Epic 2 parameter); gold permitted |
| **RECOVERY** | Was ALARM; acute below its **exit** threshold (exit < entry) for the persistence period **and** trend confirming (reference index above a flattening 200-day mean, **or** a higher low on the acute statistic). **Both are required.** | Tranches permitted again, one at a time, subject to §8 | — |
| **UNKNOWN** | Any REQUIRED input absent/stale, or the coverage bracket (§9) spans a state boundary and cannot be resolved conservatively | **No permission** (treated as WATCH for permission purposes, never as CALM) | No permission |

Rules of precedence:

- A master beyond stress fires ALARM on its own. Calm readings elsewhere cannot outvote it.
- Breadth and count can **raise** a state; they can never **lower** one while a master is firing.
- RECOVERY requires both conditions because acute-fallen alone would have reopened the gate in Oct–Nov 2008, months before the low, and trend alone is a lagging average cross. Late by design.
- **Post-ALARM lock (WO-1.3b-II; closes R2D2's F1, the re-entry back door):** once ALARM has fired, the dial may not reach CALM except through RECOVERY. ALARM → WATCH → CALM used to need only two persistence counts and no trend test, so RECOVERY's "both conditions" were walked around: in the control history there were 9 premature re-opens in four declines, 8 of which still had ≥ 10% to fall (mean further fall −27.6%). Armed means "the dial's most recent ALARM row is newer than its most recent CALM or RECOVERY row"; while armed a CALM candidate is held at WATCH and a RECOVERY candidate stands whatever the previous state was. UNKNOWN rows do not clear it. **The lock does not override the UNKNOWN-exit floor** (R2D2 PR #14 live re-audit, D2): a dial whose last official state is UNKNOWN reports WATCH for its first reading out, lock armed or not, even when that reading's candidate is RECOVERY. The measured cost, stated plainly: denial rises from 16.2% to 24.0% of days and median re-entry moves from 58 to 119 days after the trough (+17% → +21% off the low). Applies to the equity dial, whose trend measure is the S&P 500 above a flattening 200-day mean (§6 RECOVERY); the monetary dial has no such measure and is not locked.
- **Second-leg rule:** if ALARM re-fires after RECOVERY, the state returns to ALARM and the recovery clock restarts from zero. "It is even cheaper now" is not a macro-layer input.

Candidate masters (composites, not single tickers; final set and thresholds from calibration — *provisional*):
equity — credit (HY OAS level + 20-day change), curve 6-month change, volatility regime (VIX level + VIX/VIX3M), funding stress / external financial-stress index;
monetary — fiscal-dominance flag (moved out of the blended mean), real-rate direction, currency trend.

> **Naming note (Trinity, 2026-10-13):** "breadth" above names the equity dial's composite statistic in this new three-statistic design. The codebase already has a specific indicator called `constituent_breadth_200dma` (Matt's own S&P-500-breadth proposal, WO-1.10). These are not the same thing, and the overlap is confusing — worth a cleaner name for the composite statistic (e.g. `weighted_mean`) when the three-statistic engine is actually built (WO-1.3a), so a reader doesn't conflate the two.

## 7. The output contract — the one thing this document must get right

Epic 2 reads **only** this. It never reads CERBERUS internals.

```yaml
schema_version: decision-rule/v1
dial: equity_crash | monetary_debasement_gbp | monetary_debasement_usd
as_of: <UTC timestamp of the newest input used>        # per-input ages are in `inputs`
state: CALM | WATCH | ALARM | RECOVERY | UNKNOWN
state_since: <UTC timestamp>
persistence_counter: <int>                               # readings toward the next transition, 0 if none pending
sizing_multiplier: <float >= 0>                          # 0 in WATCH / ALARM / UNKNOWN; valuation-scaled in CALM / RECOVERY
acute_rising: <bool>                                     # acute statistic higher than N readings ago
statistics:
  breadth: <float 0..1>                                  # the current weighted mean
  acute: <float 0..1>                                    # max over calibrated masters
  count: <int>                                           # inputs at/beyond their stress end
coverage_bracket:
  scored_weight_fraction: <float 0..1>                   # scored weight / nominal weight
  dial_value_min: <float>                                # dial's statistic if every missing input scored 0
  dial_value_max: <float>                                # dial's statistic if every missing input scored 1
inputs:                                                  # one entry per wired indicator: id, state, age_seconds, score or null
identity:
  build_sha: <git sha>
  scaling_version: <hash of indicator-scaling.json>
  mapping_version: <hash of indicator_mapping.yaml>
  decision_rule_version: <this file's version>
```

Semantics the consumer may rely on:

- `state` is **fail-closed**: a reading the detector cannot stand behind is `UNKNOWN`, never `CALM`.
- `sizing_multiplier` is non-zero only in `CALM` and `RECOVERY`. Its magnitude comes from valuation inputs (CAPE, Buffett-indicator substitute, gold extension vs 200-day mean) and is capped in a provisional range of 0.5–1.5. Valuation **scales size; it never withholds permission.**
- `acute_rising` is published so Epic 2 can enforce "no tranche while acute is rising" without recomputing anything.
- `coverage_bracket` is the honest coverage figure. If `[dial_value_min, dial_value_max]` straddles a state boundary, the state resolves to the **worse** of the two; if it straddles two boundaries, `UNKNOWN`.
- Equity and monetary outputs are independent documents. CERBERUS does not resolve conflicts between them.

> **Rename note (Trinity, 2026-10-13):** this schema's `coverage_bracket` fields were originally drafted as `breadth_min`/`breadth_max`. Renamed to `dial_value_min`/`dial_value_max` before merge — "breadth" already names both the equity composite statistic above and a specific existing indicator (`constituent_breadth_200dma`); a third meaning on the same word in the one contract Epic 2 reads verbatim was a real ambiguity risk, not a style preference. Trinity owns this schema from here per the architect's handoff; everything else in this document is Owner-level and untouched.

## 8. Anti-step-down rules — who owns which

| Rule | Owner |
|---|---|
| Tranches permitted only in CALM or RECOVERY | CERBERUS (via `state`) |
| Second-leg restart on ALARM re-fire | CERBERUS (§6) |
| No tranche while acute is rising | CERBERUS publishes `acute_rising`; Epic 2 enforces |
| Minimum spacing between tranches (*provisional* 4–6 weeks) | Epic 2 |
| No averaging down at the macro layer: next tranche waits for a higher low if the previous is more than **X = 10%** underwater (*provisional*) | Epic 2 |
| Independent drawdown rule on deployed capital, functioning when CERBERUS is blind | Epic 2 |

**Accepted cost, stated plainly:** this rule misses the exact bottom every time, by design. The family buys the recovery, typically 10–20% off the low, in exchange for never buying a falling knife.

## 9. Anti-opportunity-risk rules

| Rule | Owner |
|---|---|
| **Time floor:** if CALM persists for **N = 6 months** (*provisional*) with no WATCH, deployment proceeds on schedule. "Expensive but calm" does not block. | CERBERUS (state does not change); Epic 2 (schedule) |
| Valuation scales `sizing_multiplier`, never permission | CERBERUS |
| Gold tranches additionally require gold-in-GBP not extended vs its 200-day mean and real yields not rising | CERBERUS (feeds the monetary `sizing_multiplier`) |

## 10. Provisional parameters — single table

| Symbol | Meaning | Value today | Set by |
|---|---|---|---|
| persistence | consecutive readings for a transition | 5 | R2D2, WO-1.3b ruling 2026-10-15 (was 3, Trinity provisional) — still provisional |
| N | time floor in CALM | 6 months | provisional |
| X | averaging-down guard (Epic 2) | 10% | provisional |
| B_mid | breadth at which breadth alone (when rising) says WATCH | **unset — published context only, never a gating threshold** | R2D2, WO-1.3b-II: no value is supportable. Breadth carries no lead (day-level AUC vs forward fall 0.40, below 0.5; breadth at the S&P peak ≈ its unconditional level), and removing the limb changes WATCH days by −0.8 point with no change in protection. The live 24-indicator composition (CAPE, Buffett, private credit, constituent breadth) has not accrued, so the replayed store cannot set it either. Assigning a value is a calibration decision for when it has. |
| B_high | breadth at which breadth alone says ALARM | **unset — rule 3 is dead at the current store composition** | R2D2, WO-1.3b-II: maximum breadth anywhere in the 2,514-day store is 0.489; the old placeholder 0.55 was reached on 0.00% of days. Unreachable, not "high". Do not fabricate a value. |
| k | count threshold | **unset — rule 3 (count) REMOVED, provisionally** | R2D2 PR #14 live re-audit (D3) WITHDREW her count v2 / k = 2 recommendation: it added no measured detection over the masters alone and came within one bad day of a live false ALARM off `real_rate_10y_tips` alone. ALARM fires via rule 2 only until count is properly recalibrated. **Provisional removal, not permanent**: restoring it is assigning k (an integer). The count is still computed and published as context. Its indicator set (`copper_gold`, `cboe_skew`, `hy_oas`, `ig_oas`, `real_rate_10y_tips`, `spx_vs_200dma`, `vix_level`, `vix_term_structure`; threshold score ≥ 0.8) no longer includes `yield_curve_10y2y`/`yield_curve_10y3m` (D1): `curve_master` is WATCH-only, and its components may not vote ALARM through the count. |
| master set, warning/stress/exit thresholds | per master | warning 0.60 / stress 0.85 / exit 0.50 for every master **except `volatility_master`: stress 0.70** | R2D2, WO-1.3b-II: 0.70 catches 10 of 10 declines ≥ 15% on 1990–2026 (7 of 10 at 0.85), leave-one-episode-out stable, at 0.52 false-alarm spans a year against 0.22. `curve_master` warning stays 0.60 (R2D2's tentative 0.80 is rejected: it halves decline coverage for a span reduction that does not fix the structural issue, F7). `credit_master` and `financial_conditions_master`: **no change, unvalidated** — one replayable episode and never reached warning. All other values remain provisional. |
| multiplier range | sizing_multiplier bounds | 0.5–1.5 | provisional |
| lookback for `acute_rising` | readings | 20 (unchanged) with a **0.02 deadband** (`acute > previous + 0.02`) | R2D2, WO-1.3b-II: no skill at 5/10/20/40, so the lookback stays; the deadband matches breadth's. Epic 2 note: "no tranche while acute is rising" blocks about 44% of permitted days at lookback 20 with no measured risk reduction. |

Nothing in the "unset" rows may be filled from today's vintages. Calibration requires point-in-time data and the historical backfill first, and must be replayed through at minimum: 2000–02, 2007–09, 2011, 2015–16, Q4 2018, March 2020, 2022 (incl. September gilt crisis), April 2025. With roughly six real crash events in the usable history, constrained prior-driven parameters are preferred over anything fitted.

## 11. Explicitly outside this document

- Instrument selection, price levels, order timing within a permitted window.
- Tranche size schedule, spacing, the drawdown stop, regime map, historical-analogue matching (Epic 2 — WO-2.7/2.8/2.9).
- Any blending of dials or any combined "risk score".
- Execution of any kind. CERBERUS is advisory.

---

*Change log*
- v1 2026-10-13: initial, Owner-confirmed (base currency, event definitions, RECOVERY-both). Provisional numerics per Trinity.
- v1.0.1 2026-10-13: Trinity — renamed `coverage_bracket.breadth_min/breadth_max` → `dial_value_min/dial_value_max` (naming-collision fix, see §7 note); added §6 naming note on "breadth" overload; no Owner-level content changed.
- v1.0.3 2026-10-22: WO-1.3b-II — implements R2D2's calibration findings (fabric `r2d2:wo:cerberus_wo13b2:verdict`; report `/srv/r2d2/evidence/cerberus_wo13b2/REPORT.md`): `volatility_master` stress 0.85 → 0.70; post-ALARM lock; `breadth_rsp_spy` and `credit_stress_hyg_lqd` excluded from scoring; count v2 with k = 2 (§6 rule 3 is now the count rule); B_mid / B_high documented unset and unreachable (§10); `acute_rising` deadband 0.02. `curve_master` warning unchanged at 0.60. §6 trigger shapes edited to match; no Owner-level content otherwise changed.
- v1.0.4 2026-10-23: WO-1.3b-II follow-up — R2D2's PR #14 live re-audit (D1-D3), confirmed against the code: (D1) the two yield-curve indicators leave the count set; (D2) the post-ALARM lock no longer overrides the UNKNOWN-exit floor; (D3) the count rule (rule 3) is removed provisionally, k unset — ALARM fires via rule 2 only until count is recalibrated.
- v1.0.2 2026-10-15: persistence changed 3 → 5 (R2D2's WO-1.3b audit ruling, replacing Trinity's original provisional guess with an evidence-backed one — ~3.6 transitions/year at 5 vs ~5.9 at 3, over a daily-reading cadence). Still marked provisional; R2D2's own finding B1 is that the deployed evaluator had been running every 300 seconds instead of daily, so the original "3" was never actually being measured in the unit this document states — fixed in the deployment (WO-1.3e), not in this document.
