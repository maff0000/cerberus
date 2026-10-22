# CERBERUS WO-1.3b-II — replay re-run against the WO-1.17 historical store

**Persona:** R2D2 · **Date:** 2026-10-22 · **Lane:** Epic 1 calibration only (Epic 2 consumer rules untouched; the store was not patched)
**Engine under test:** `dell-debian:/srv/cerberus-worktrees/wo-1.17` @ `dfd127e` (branch `wo/CERBERUS-WO-1.17-historical-backfill-run`, audited by SHA, not by merge)
**Store:** `wo117_historical.sqlite`, online-backup snapshot, sha256 `8087a455e1cd4131dc78fc5ea466036a4335d89c6d465c3cee110af1c344e3e3`
**Harness:** `/srv/r2d2/tools/cerberus_replay/` (committed; `results.json` sha256 `a7f5fe22…d1f4`, reproduced byte-identically)

---

## 1. Verdict

| Configuration | Verdict |
|---|---|
| **The dial as deployed @ `dfd127e`** | **RED — not live-decision-grade** |
| **The dial with §5's changes 1–3 applied** | **AMBER (conditional)** — a measured, halt-biased ALARM core, with named holes that stay open (credit, financial-conditions, breadth, count, GBP) |
| GREEN | Not reachable from this store: it needs a credit history before 2023-10 and a GBP dial, neither of which exists |

Bar, unchanged from WO-1.3b: **RED** = a blocking defect, or a decision-driving parameter that is unmeasured. **AMBER** = the decision core is measured and stable under leave-one-episode-out, and every open hole is disclosed and non-blocking for a conservative (halt-biased) use. **GREEN** = AMBER plus an out-of-sample test and no required-input hole across the named episodes.

**What the numbers say, in six lines**

1. **Late.** As deployed, ALARM arrives with **19%** of the four ≥20% declines still ahead (32% across all eight episodes). It never fires in 2000-02, 2007-09 or 2022. Permission to deploy stays on for the first ~80% of a primary decline.
2. **Threshold fix.** `volatility_master` stress 0.85 → **0.70** lifts that to **63%** (primary) / 60% (all eight), 8 of 8 episodes signalled. On 1990-2026 continuous data it catches 10 of 10 declines ≥15% against 7 of 10 at 0.85. It costs 0.52 false-alarm spans/yr (3.9% of days) against 0.22/yr (1.3%).
3. **Back door.** `ALARM → WATCH → CALM` needs only two persistence counts and no trend test, so RECOVERY's "both conditions" gate is bypassed. In the control history there are **9 premature re-opens** in four declines; **8 of the 9 had ≥10% still to fall** (mean further fall −27.6%). Rank-1 failure mode, structurally open.
4. **No lead.** Breadth, `acute` and count are coincident or lagging. Breadth at the S&P peak ≈ breadth at −10% ≈ the unconditional level, and its maximum anywhere in the store is 0.489. **`B_high` = 0.55 was never reached in 2,514 days**, so rule 3 is dead. Breadth cannot be calibrated here, only shown to carry no lead.
5. **Two broken inputs.** `breadth_rsp_spy` (tier 1, ×3) scores exactly 0.00 on every one of 1,713 days. `credit_stress_hyg_lqd` drifts from ≈1.0 (2007) to ≈0.65-0.75 (2016+) on price-ratio decay and has nothing to do with stress.
6. **The ICE cap has not lifted** (§4).

---

## 2. Method (so it can be challenged)

* **Real engine, not a re-implementation.** `engine.statistics` (masters, count) and `evaluator.resolve.official_state_for_dial` are imported at `dfd127e`. My parameterised state machine is proven identical to the real resolver: **0 mismatches over 2,507 days**, re-checked after every harness edit.
* **Point-in-time rules.**
  * Rows with vintage `original` are knowable from their `vintage_date`.
  * `current_only` and `no_revision_mechanism` rows are knowable from `as_of` + 1 day.
  * A value is used only inside the mapping's `staleness_window_seconds`.
  * Missing inputs are excluded from breadth (engine "Degraded"), never scored 0.
  * One reading = one trading day (the post-WO-1.3e daily cadence). History resets at each window edge because the store has no data between windows.
* **Store audit (spot, not exhaustive).**
  * 0 of 2,202 `original`-vintage rows have `vintage_date` < `observation_date` (no look-ahead).
  * The vintages are genuinely original: 201/201 NFCI rows and 37/37 GDP rows differ from today's FRED values (GDP up to 4.75%).
  * Against independent continuous series, S&P matches on 2,514/2,514 dates and T10Y3M/T10Y2Y on 2,497/2,497, all exact. VIX3M matches to ≤0.067%. VIX differs on two half-days (2008-11-28, 2009-11-27, 1%).
* **Truth.** Real S&P 500 drawdowns (the store's own `^GSPC` closes). Primary = ≥20% within 126 trading days; secondary = ≥15% within 63. Days whose forward horizon runs past a window edge are *censored*, not counted negative.
* **Control series.** The store is event-window sampled (§4, S1), so it has no calm baseline. For the two market-priced masters only (vol, curve) and for event lists I used **continuous, unrevised public series, fetched 2026-10-22, outside the store**: Yahoo `^GSPC`/`^VIX`/`^VIX3M` and FRED `T10Y3M`/`T10Y2Y` (+`BAA10Y`, descriptive only). They are labelled "control" wherever used. sha256 values are in `fabric r2d2:backtest:latest`.
* **The sample is small.** There are 4 primary (≥20%) declines in 1990-2026 and 10 declines ≥15% (clustered). The store's 8 episodes are a subset of the control's 10, so the numbers below are **in-sample, rule-selected and leave-one-out-stable. They are not out-of-sample.** The Decision Rule's own preference for constrained, prior-driven parameters over fitted ones is followed, and each value comes from a pre-stated rule.

---

## 3. Coverage map (what the replay can and cannot see)

Percent of trading days in each episode with a fresh point-in-time value. Floors from the brief were *not* re-derived; they show up here as the blanks.

| indicator (tier) | 2000-02 | 2007-09 | 2011 | 2015-16 | Q4-18 | Mar-20 | 2022 | Apr-25 |
|---|---|---|---|---|---|---|---|---|
| **hy_oas (1, req)** | — | — | — | — | — | — | — | 100 |
| yield_curve_10y3m / 10y2y (1, req) | 100 | 100 | 99 | 99 | 97 | 97 | 99 | 97 |
| ig_oas (2) | — | — | — | — | — | — | — | 100 |
| jobless_claims_4w (2) | — | 21 | 97 | 96 | 94 | 91 | 98 | 94 |
| sahm_rule / michigan (2/3) | 95 | 94 | 80 | 79 | 60 | 60 | 86 | 80 |
| cboe_skew (2) / vix_level (3) | 99 | 100 | 99 | 99 | 97 | 97 | 99 | 97 |
| chicago_fed_nfci (2) | — | — | 69 | 97 | 94 | 94 | 97 | 94 |
| real_rate_10y_tips (3) | — | 100 | 99 | 99 | 97 | 97 | 99 | 97 |
| fed_funds_rate (2) | 100 | 100 | 99 | 99 | 97 | 97 | 99 | 97 |
| m2_yoy (2) | 93 | 92 | 76 | 76 | 51 | 51 | 58 | 51 |
| breadth_rsp_spy (1) | — | 100 | 99 | 99 | 97 | 97 | 99 | 97 |
| credit_stress_hyg_lqd (2) | — | 99 | 99 | 99 | 97 | 97 | 99 | 97 |
| copper_gold (2) | 74 | 100 | 99 | 99 | 97 | 97 | 99 | 97 |
| vix_term_structure (2) | — | **10** | 99 | 99 | 97 | 97 | 99 | 97 |
| spx_vs_200dma (3) | 75 | 71 | **6** | **4** | **—** | **—** | 32 | **—** |
| buffett_indicator (1) | — | — | — | 36 | — | — | 48 | — |
| sloos_bank_lending (2) | — | — | 80 | 79 | 31 | 60 | 79 | 80 |
| shiller_cape (1), private_credit (2), constituent_breadth (3), ism (3) | not replayable from the store | | | | | | | |
| **scored-weight fraction (mean)** | **37%** | 52% | 61% | 64% | 57% | 57% | 66% | 70% |

**Equity masters, % of days scorable** (the live `acute` needs all four):

| master | 2000-02 | 2007-09 | 2011 | 2015-16 | Q4-18 | Mar-20 | 2022 | Apr-25 |
|---|---|---|---|---|---|---|---|---|
| credit | — | — | — | — | — | — | — | 100 |
| curve | 100 | 100 | 100 | 100 | 99 | 99 | 100 | 99 |
| volatility | — | **10** | 100 | 100 | 99 | 99 | 100 | 99 |
| financial_conditions | — | — | 70 | 97 | 96 | 92 | 97 | 95 |
| **all four** | — | — | — | — | — | — | — | **95** |

Consequences:
* The dial as deployed returns **UNKNOWN on 96.1% of store days and on 100% of days in seven of the eight episodes** (only Apr-2025 resolves). That is fail-closed behaving correctly on a store whose credit leg does not exist before 2024-12. It is not a live defect, but it means the as-deployed dial cannot be validated against any episode before 2025.
* `volatility_master` needs both `vix_level` and `vix_term_structure`; VIX3M starts 2006-07 (store: 2009-09), so the master is UNKNOWN through 2000-02 and most of the GFC. VIX3M is present live, so this matters only for replay. For calibration I let the master use VIX alone where VIX3M does not exist ("calibration mode", never used for the as-deployed verdict).
* Lookback indicators are blind at window starts because the store holds ~100-300 days per window. `spx_vs_200dma` is 0% in Q4-2018, Mar-2020 and Apr-2025. `monetisation_flag` (365-day WALCL) is 0% before 2015.
* **Monetary dial (USD):** the live `acute` resolves on 62% of 2022 and 13% of Apr-2025, and nowhere else (`broad_dollar` floors 2019-02). The USD monetary dial is effectively unreplayable, and **GBP is untestable: the store contains no GBP, gilt, BoE or SONIA row.**

---

## 4. Disposition of the WO-1.3b `cannot_validate` list

| Item | Status now | Evidence |
|---|---|---|
| **credit_master pre-2023-10** | **NOT resolved, and not a different limit: the same ICE cap.** | FRED's earliest `BAMLH0A0HYM2` observation, fetched today, is **2023-10-23** (exactly 3 years back), and the same for `BAMLC0A0CM`. The store's 108 OAS rows are the 108 *asked-for* dates (2024-12-31 → 2025-05-31) and all 108 came back OK with zero failures. "Complete" means complete over a request set that never reached the earlier episodes. The cap is rolling, so the floor advances a day per day. |
| **NFCI vintages** | Resolved as bounded | First store row 2011-05-27. Vintages are real (201/201 differ from current). The GFC and 2000-02 stay blind. |
| **B_mid / B_high / count / whole-dial breadth** | Now measurable, with a negative result | §5 and §6. |
| **RECOVERY trend** | Measured | A computed `trend_confirmed` makes RECOVERY reachable in **1 of 10** declines, and the real problem is the back door (§6, F5). |
| **GBP dial** | Structurally capped | No GBP series exists in the store. |
| **Sept-2022 gilt crisis** | Equity side only | Under the §5 settings, 2022-09-15 → 10-14: CALM on 11 of 22 days (ALARM only from 2022-09-30, after the gilt shock of 09-23/28), S&P 3901 → 3577. The GBP-side crisis is unobservable. |

A non-ICE credit series does exist: FRED `BAA10Y` (Moody's Baa − 10y, daily from 1986-01-02, continuous, sha256 `3980ed95…`). It moves with every decline (e.g. 1.59 → 2.40 at −10% → 5.40 at the GFC trough). That is descriptive only. It is a candidate for a pre-2023 credit-master history, and licence/provenance is Rogue's/Trinity's call.

---

## 5. Parameters — measured values

Evidence grades: **M** = measured on the control with leave-one-out. **S** = store, in-sample. **U** = unmeasurable here.

| Parameter | Provisional / deployed | Measured | Recommended | Grade |
|---|---|---|---|---|
| **persistence** | 5 | Control, stress 0.70: P=3 → 10/10 declines caught, 8 before −10% DD, 1.01 false-alarm spans/yr. **P=5 → 10/10, 5, 0.52/yr.** P=10 → 7/10, 2, 0.14/yr. | **5 (confirm)** | M |
| **vol_master stress** | 0.85 | Stress 0.85: 7/10 caught (3 before −10% DD), ALARM 7.2% of days, 0.22 FA spans/yr, 124 FA days. **Stress 0.70: 10/10 (5 before), ALARM 12.3%, 0.52/yr, 365 FA days (3.9%).** 0.50-0.70 all catch 10/10; 0.75 drops 1990. Pre-stated rule "highest stress catching every decline": LOO gives 0.70 in 9 of 10 drops and 0.75 when 1990 is dropped. | **0.70** | M |
| vol_master warning / exit | 0.60 / 0.50 | No evidence to move 0.60. **Exit has zero effect on any state today** (exit is read only by RECOVERY, which is unreachable). | keep | M |
| **curve_master warning** (WATCH-only) | 0.60 | Warn 0.6: denies 14.3% of days since 1990 and had a WATCH in the prior 18 months for 5/10 declines. 23% of its WATCH days sit outside any decline window, and the longest single span is **887 days (2022-07 → 2024-12)**. Warn 0.8: 6.7% of days, 2/10 declines, but the longest span is still 724 days. No threshold removes the multi-year inversion span. | 0.80, **low confidence**. The structural issue is for Trinity (§6, F7). | M |
| **financial_conditions_master** | 0.60 / 0.85 / 0.50 | Highest score reached in any of the six replayable episodes is **0.57** (Mar-2020). It never reached warning, and the GFC is outside NFCI's PIT range. | **no change; inert and unvalidated** | U |
| **credit_master** | 0.60 / 0.85 / 0.50 | One replayable episode (Apr-2025): HY OAS peaked 4.61% → score **0.54**, below warning. Nothing else exists. | **no change; unvalidated** | U |
| **B_high** | 0.55 (unset in the rule) | Max breadth 0.489 over 2,514 days. **Reached 0.00% of days.** Rule 3 cannot fire. | **leave unset; treat rule 3 as dead** until the live composition has accrued | S |
| **B_mid** | 0.35 | Reached on 20.0% of days. Removing the breadth-rising limb changes WATCH days by −0.8 pt (22.5% → 21.7%) with no change in protection. Day-level AUC of breadth vs forward fall = **0.40** (below 0.5, so it peaks late). Live composition also carries CAPE and Buffett (structurally ≈1.0), which the replay cannot model, so the live floor is higher than any replayed number. | **no value supportable**; keep as published context | S/U |
| **k / count** | 3 (count v1) | Count v1 is saturated by clamped inputs (AUC 0.54). **Count v2** (fast, daily market-priced inputs only, excluding the two defective ratios, T = 0.8): the maximum count ever observed is 3 of 6-10. k=3, 4, 5 never change the result. **k=2 adds +3.8 pt ALARM days and lifts "share of decline ahead" 63% → 76% on the primary events.** | **count v2, k=2, provisional**, only after the two ratio inputs are fixed | S |
| **acute_rising lookback** | 20 (suggested) | L = 5/10/20/40: the flag is true on 51/51/44/42% of otherwise-permitted days. P(fwd ≤ −20%) rising vs flat is .33-.39 vs .39-.43: **no skill, slightly inverted.** | **keep 20**, add a deadband like breadth's 0.02. **Epic 2 cost: "no tranche while acute is rising" blocks ~44% of permitted days at L=20 with no measured risk reduction.** | S |

### The headline comparison (store, 2,514 days, 8 episodes)

| | Deployed, live-strict | Deployed, masters available | **Recommended (vol 0.70, curve warn 0.80)** | + count v2 k=2 |
|---|---|---|---|---|
| UNKNOWN / ALARM / WATCH / CALM, % of days | 96.1 / 0.8 / 1.6 / 1.6 | 0.3 / 6.6 / 23.2 / 69.9 | 0.3 / 26.0 / 12.2 / 61.5 | 0.3 / 29.8 / 10.3 / 59.6 |
| Share of primary (≥20%) decline still ahead at first ALARM | 0% | **19%** | **63%** | 76% |
| Same, all 8 episodes | 6% | 32% | 60% | 72% |
| Episodes with an ALARM | 1/8 | 5/8 | **8/8** | 8/8 |
| P(≥20% fall in next 126d \| tranches permitted) vs denied | n/a | 0.35 vs 0.10 | 0.32 vs 0.22 | 0.32 vs 0.23 |

**Read the last row honestly.** At the day level the dial does not separate dangerous days from safe ones. It is a *coincident halt that avoids the later part of a decline*, not a predictor, and permitted days are *not* safer than denied ones in this sample. ALARM on the store is 26% of days only because the store is crash-selected; the continuous-history base rate is 12.3% of days at stress 0.70.

Per-episode first ALARM under the recommended setting (date, S&P drawdown then, share of the peak-to-trough decline still ahead):
2000-02: 2001-03-23, −25.4%, 48% · 2007-09: 2008-09-22, −22.9%, 60% · 2011: 2011-08-03, −7.6%, 61% · 2015-16: 2015-08-27, −6.6%, 53% · Q4-18: 2018-10-25, −7.7%, 61% · Mar-20: 2020-03-02, −8.7%, 74% · 2022: 2022-01-28, −7.6%, 70% · Apr-25: 2025-03-10, −8.6%, 54%.
The two slowest are the grinding bears (2000-02, GFC), where VIX does not stay elevated.

---

## 6. Findings that are not parameters

| # | Finding | Evidence | Owner |
|---|---|---|---|
| **F1** | **Re-entry back door.** The deployed ALARM exit goes ALARM → WATCH → CALM. CALM does not require `trend_confirmed` or RECOVERY, so rule 5's "both conditions" never gates re-entry. | 9 premature re-opens in 2000-02 (2), 2007-09 (2), 2022 (4) and 2025 (1); 8 of 9 had ≥10% still to fall, mean −27.6%. A candidate lock (after ALARM, CALM unreachable until RECOVERY; trend = S&P above a flattening 200-day mean) cuts that to 3 re-opens. The cost: median re-entry 119 days / +21% off the low vs 58 days / +17%, and denial rises from 16.2% to 24.0% of days. | Trinity (design) |
| **F2** | **`breadth_rsp_spy` is dead.** Tier 1 (weight ×3), band 0.29 → 0.25, observed ratio 0.294-0.389 on 1,713 days. It scores 0.00 every day and only dilutes the breadth denominator. An absolute ETF price ratio is not stationary. | `out_reference/saturation.md` | Trinity / Rogue |
| **F3** | **`credit_stress_hyg_lqd` is drift-contaminated.** The ratio runs 1.017 → 0.599, median 0.976 (2007) → 0.65-0.69 (2019-2022). The HYG first print is 104.35 on 2007-04-11, consistent with *unadjusted* closes. 28% of days are ≥0.9 purely from decay. It saturates count v1. | same | Trinity / Rogue |
| **F4** | **Count v1 measures band narrowness, not stress**, as the WO-1.3a addendum feared. A count over fast inputs rarely exceeds 3. | §5 | Trinity |
| **F5** | **Exit thresholds are inert** until RECOVERY is reachable. The hysteresis in `candidate_state_for_one_reading` is carried by persistence alone. | exit 0.3-0.6 → identical states | Trinity |
| **F6** | **RECOVERY reached in 1 of 10 declines** with a computed trend: 2020-08-06, 136 days after the trough, S&P +50% off the low, and re-ALARM on 2020-09-10. | `eval_lock.py` | Trinity |
| **F7** | **Curve WATCH can deny permission for ~2.4 years** (2022-07-15 → 2024-12). Demotion to WATCH-only removed its ALARM but WATCH still halts tranches. No threshold fixes it, so it needs a structural answer (sizing input, or a cap on how long curve alone may hold WATCH). | `eval_curve.py` | Trinity |
| **S1** | **The store is event-window sampled, not continuous.** It is 8 windows and 2,514 market days, with nothing in 2003-06, 2010, 2012-14, 2017, most of 2019, or 2023-24. 71% of fully-observed store days face a ≥10% fall within 126 days. Precision and false-positive rates from the store alone are selection-biased, which is why the control was needed. | coverage map | Rogue, FYI |
| **S2** | **OAS request set stops at 2024-12-31**, but FRED still serves 2023-10-23 → 2024-12-30 (calm period plus the Aug-2024 vol event). Unrequested, not a backfill fault. The rolling cap means the Apr-2025 window leaves FRED's reach around 2028-04. | FRED fetch 2026-10-22 | Rogue |
| **S3** | **Lookback indicators are blind at window starts.** | coverage map | Rogue, FYI |
| **S4** | 9 store VIX dates fall on US market holidays and are absent from the independent VIX series (immaterial). | parity check | FYI |

Reported, not patched: the store is Rogue's lane, and none of S1-S4 is a defect in the backfill.

---

## 7. What it would take to reach GREEN

1. Adopt §5's `volatility_master` stress 0.70 (the pre-stated rule, LOO-stable).
2. Decide F1 (the post-ALARM lock or an equivalent). This is a design change, so it is Trinity's and Matt's call. I have measured both sides.
3. Fix or exclude `breadth_rsp_spy` and `credit_stress_hyg_lqd` (returns-based, or dividend-adjusted) before anything uses breadth or count.
4. Give `credit_master` a pre-2023 history from a non-ICE source (`BAA10Y` is a candidate), then calibrate it. Today it has one episode and never reached warning in it.
5. Let the live store accrue the full 24-indicator composition (CAPE, Buffett, private credit, constituent breadth) before any breadth threshold is set.
6. Build a GBP dial. It cannot be validated without GBP series.
7. Re-run this harness on any change to the backfill or the engine. An independent test of the 0.70 value needs a decline that has not yet happened.

## 8. Reproduce

```
/srv/r2d2/tools/cerberus_replay/fetch_inputs.sh && cd /srv/r2d2/tools/cerberus_replay/harness && python3 -I final_run.py
```
Reference outputs are in `/srv/r2d2/tools/cerberus_replay/out_reference/` (coverage map, indicator reach, saturation, `results.json`).
