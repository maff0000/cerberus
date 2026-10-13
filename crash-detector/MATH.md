# CERBERUS crash-detector — the mathematics of the two dials

**Status: DRAFT for Trinity review, then Matt, then a third-party reviewer. WO-1.11.**
**Everything in this document is PROVISIONAL. No weight, band or construction below has been backtested or calibrated. The dial figures are not probabilities and are not advice.**

| | |
|---|---|
| Source read | `crash-detector/src/crash_detector/engine/mapping.py`, `engine/derivations.py`, `engine/model.py`, `engine/evaluate.py`, `ingestion/wiring.py`, `ingestion/catalog.py`, `deploy/indicator-scaling.json`, `governance/mapping/indicator_mapping.yaml` |
| Commit | `46808bd` (WO-1.10 merge). The running GUI at `192.168.11.10:8710` reported `build: 46808bd` on `/healthz`, i.e. the code described here is the code that produced the live numbers below. |
| Live readings | `GET http://192.168.11.10:8710/api/state`, `generated_utc = 2026-10-13T08:37:58.298991Z`. Component inputs of derived indicators were read from the ingestion store (read-only). The numbers move; the worked examples in §1.5 and §2.5 are pinned to that instant. |
| Cross-check | Both worked examples were recomputed independently from `indicator-scaling.json` and the raw values. They reproduce the GUI's dial values to full double precision (equity `0.3405089786134545`, monetary `0.1402644642857143`). |
| Not covered | The serving/presentation layer (`serving/dial_presentation.py`, GUI labels) and the publication envelope. This document stops at the dial magnitude. The GUI value equals the hand computation exactly, so no further transform was observed on the GUI path. |

---

## 0. Read this first — the things a reviewer should attack

These are stated up front and again, with detail, in the dial sections. None is softened.

| Ref | Issue |
|---|---|
| **R-1** | **The dial is a flat weighted arithmetic mean of independently clamped linear scores. There is no master signal, no worst-of, no override, no interaction term, no non-linearity, and no time dimension (no trend, momentum or persistence).** One indicator at an extreme contributes at most `w_i / Σw` of the dial. The architectural gap — *no mechanism lets one extreme signal dominate* — is real and is analysed in §1.4 and §2.4. |
| **R-2** | **Every band (calm/stress) is a placeholder. No backtest or distribution study has been run for any of them.** The file itself says so (`deploy/indicator-scaling.json`, `$comment`). Where the file records how a band was chosen, it is "a round number", "a guess", or "set after one glance" at one ticker's history. |
| **R-3** | **Every weight is a tier rule (tier 1→3, 2→2, 3→1) and is a placeholder.** The tiers themselves are the ratified mapping's *provisional* tiers (`provisional_weights_pending_backtest: true`). Weights are per indicator and identical on both dials. |
| **R-4** | **Seven indicators are substitutes or new constructions, not what the ratified row declares** (`buffett_indicator`, `ism_manufacturing`, `sloos_bank_lending`, `private_credit_stress`, `constituent_breadth_200dma`, `gold_real_rate_cross`, `fiscal_dominance`), and `gold_spot` is banded as a level where its row says trend; see §3. Several are Trinity's provisional constructions, not Owner-ratified formulas. |
| **R-5** | **Missing/stale inputs are dropped and the remaining weights renormalise.** The mean runs over the inputs *present*. That is the same as assuming each absent input would have scored exactly the weighted mean of the others. It is not counted as calm and not counted as stress, but it is not neutral either. Today it matters on both dials (§1.5, §2.5). |
| **R-6** | **Saturation.** Several live readings sit beyond their stress end and clamp to 1.0 (equity: `shiller_cape`, `michigan_sentiment`, `real_rate_10y_tips`). A band that clamps carries no further information however much worse the reading gets. |
| **R-7** | **Correlated inputs are weighted as if independent.** E.g. equity carries two yield-curve spreads at ×3 each, four credit-spread measures, three volatility measures. The mean double-counts a single underlying move. |
| **R-8** | **The equity dial's two valuation inputs (`shiller_cape`, `buffett_indicator`) are both ×3 and both high today**, together 5.33 of the 15.66 weighted sum (34 %) on 13 % of the weight. They are slow-moving, in-sample, and calibrated by nothing. |
| **R-9** | **The monetary dial currently contains no gold signal at all** (`gold_spot` and `gold_real_rate_cross` are both FEED_FAILING because the LBMA feed is unreachable). A "debasement" dial that cannot see gold is reading 14 of its 21 nominal weight points. |
| **R-10** | **The `coverage` figure the GUI shows overstates what is scored** (§1.4/§2.4 explain). |

---

## A. The one equation both dials use (`mapping.py::_banded_weighted_mean`)

Each dial has its own `ModelSpec` (`banded-weighted-mean::<dial>::v0-provisional`) built by `ingestion/wiring.py::build_wiring`. A spec carries, per input *i* bound to that dial, three parameters: `calm::i`, `stress::i`, `weight::i`. The executor `compute` dispatches on the closed enum `MappingKind`; `BANDED_WEIGHTED_MEAN` is the only computing member (`UNSPECIFIED` raises and returns nothing).

For one dial *d*, let **P** be the set of inputs that are **present and fresh** (defined below). For each *i* ∈ P with reading *v_i*:

```
              v_i − calm_i
 s_i  =  ──────────────────────      then clamped:   s_i ← 0 if s_i < 0;  1 if s_i > 1
           stress_i − calm_i

 w_i  =  3 if tier_i = 1;   2 if tier_i = 2;   1 if tier_i = 3        (wiring.TIER_WEIGHT)

                 Σ_{i∈P}  w_i · s_i
 M_d  =  ─────────────────────────────          0 ≤ M_d ≤ 1
                 Σ_{i∈P}  w_i
```

Properties, each read from the code:

1. **"Polarity-aware" means only this:** polarity is encoded by the *order* of `calm` and `stress`. If `stress < calm` (e.g. `yield_curve_10y3m`: 1.5 → −1.0) then `s_i` rises as *v_i* falls. There is **no separate sign term** in the equation. A test (`tests/test_wiring.py::test_scaling_band_order_agrees_with_the_ratified_polarity_for_every_dial`, and `tests/test_wo110.py` for the WO-1.10 row) asserts that the band order agrees with the ratified polarity word on each dial.
2. **Flat.** Every term enters additively, scaled only by its own tier weight. There is no `max`, no `min`, no gating, no cross-indicator term. The magnitude is not post-processed (no smoothing, no thresholds, no bucketing) in `mapping.py` or `evaluate.py`.
3. **Two dials never blend.** One spec and one dial's payloads go in; there is no state between calls. The same indicator can appear on both dials with different bands/polarity (§1.2, §2.2), scored independently.
4. **Fail-loud, never default.** The executor raises (returns nothing) if an input has no declared band, a band with no span (`stress == calm`), a non-positive weight, a non-finite or non-numeric value, or an empty input set.
5. **Which inputs are in P** (`evaluate.py::_evaluate_dial`, `_latest_usable_ok`):
   - An observation older than its indicator's staleness window, or dated in the future, is treated as **absent**, not as a value with a caveat. Window per indicator = the mapping row's `staleness_window_seconds`, with the overrides in `ingestion/catalog.py::WINDOW_OVERRIDES` (`buffett_indicator` 120 d, `private_credit_stress` 7 d).
   - A **REQUIRED** input absent or stale ⇒ the dial is **Unknown** and no number is produced.
   - A **contributing** input absent or stale ⇒ the dial is **Degraded**: the number is computed over the present inputs and the missing ones are named.
   - Otherwise **Value**. The dial's `as_of` is the *oldest* as-of among the inputs used.
6. **Weight is not stored in `indicator-scaling.json`.** It is derived from the ratified mapping's tier at wiring time. `required` is stored there.

---

# 1. Dial: `equity_crash`

## 1.1 Top-level formula

Exactly §A with *d* = `equity_crash`, 24 bound inputs, nominal Σw = 48 (6 tier-1 ×3 = 18, 12 tier-2 ×2 = 24, 6 tier-3 ×1 = 6). **Flat weighted mean; no master or worst-of logic.**

```
 M_equity = Σ_{i∈P} w_i · clamp((v_i − calm_i)/(stress_i − calm_i), 0, 1)  /  Σ_{i∈P} w_i
```

Required inputs (dial is Unknown without them): `hy_oas`, `yield_curve_10y3m`, `yield_curve_10y2y`.

## 1.2 Every indicator wired to the dial

Bands are from `deploy/indicator-scaling.json` at commit `46808bd`. Tier is from `indicator_mapping.yaml` (`constituent_breadth_200dma` is not a ratified row; its tier and polarity are declared in WO-1.10). State is the GUI's at `2026-10-13T08:37:58.298991Z`. **All bands in this table are PROVISIONAL, UNBACKTESTED placeholders.**

| # | Indicator | Kind / feed | Tier → weight | Polarity (this dial) | calm → stress | Required? | State now (age / window, days) |
|---|---|---|---|---|---|---|---|
| 1 | `hy_oas` | DIRECT; FRED BAMLH0A0HYM2 (%) | 1 → 3 | high_is_worse | 3 → 6 | REQUIRED | LIVE (5.4 / 8) |
| 2 | `yield_curve_10y3m` | DIRECT; FRED T10Y3M (pp) | 1 → 3 | low_is_worse | 1.5 → -1 | REQUIRED | LIVE (4.4 / 8) |
| 3 | `yield_curve_10y2y` | DIRECT; FRED T10Y2Y (pp) | 1 → 3 | low_is_worse | 1 → -0.75 | REQUIRED | LIVE (4.4 / 8) |
| 4 | `ig_oas` | DIRECT; FRED BAMLC0A0CM (%) | 2 → 2 | high_is_worse | 0.9 → 2 | contributing | LIVE (5.4 / 8) |
| 5 | `jobless_claims_4w` | DIRECT; FRED IC4WSA (claims) | 2 → 2 | high_is_worse | 200,000 → 300,000 | contributing | LIVE (10.4 / 14) |
| 6 | `sahm_rule` | DIRECT; FRED SAHMREALTIME (pp) | 2 → 2 | high_is_worse | 0 → 0.5 | contributing | LIVE (13.4 / 45) |
| 7 | `michigan_sentiment` | DIRECT; FRED UMCSENT (index) | 3 → 1 | low_is_worse | 90 → 55 | contributing | LIVE (43.4 / 45) |
| 8 | `cboe_skew` | DIRECT; CBOE SKEW (index) | 2 → 2 | high_is_worse | 120 → 160 | contributing | LIVE (1.4 / 7) |
| 9 | `vix_level` | DIRECT; CBOE VIX (index) | 3 → 1 | high_is_worse | 14 → 35 | contributing | LIVE (1.4 / 7) |
| 10 | `chicago_fed_nfci` | DIRECT; FRED NFCI (index) | 2 → 2 | high_is_worse | -0.5 → 0.5 | contributing | LIVE (11.4 / 14) |
| 11 | `real_rate_10y_tips` | DIRECT; FRED DFII10 (%) | 3 → 1 | high_is_worse | 0 → 2.5 | contributing | LIVE (5.4 / 8) |
| 12 | `fed_funds_rate` | DIRECT; FRED DFF (%) | 2 → 2 | high_is_worse | 2 → 5.5 | contributing | LIVE (5.4 / 7) |
| 13 | `m2_yoy` | DIRECT; FRED M2SL, pc1 transform (% y/y) | 2 → 2 | low_is_worse | 6 → -2 | contributing | LIVE (43.4 / 45) |
| 14 | `shiller_cape` | DERIVED; multpl Shiller PE table, percentile | 1 → 3 | high_is_worse | 50 → 99 | contributing | LIVE (4.4 / 45) |
| 15 | `breadth_rsp_spy` | DERIVED; Yahoo RSP / SPY | 1 → 3 | low_is_worse | 0.29 → 0.25 | contributing | LIVE (1.4 / 7) |
| 16 | `credit_stress_hyg_lqd` | DERIVED; Yahoo HYG / LQD | 2 → 2 | low_is_worse | 0.8 → 0.7 | contributing | LIVE (1.4 / 7) |
| 17 | `copper_gold` | DERIVED; Yahoo HG=F / GC=F x1000 | 2 → 2 | low_is_worse | 2 → 1.2 | contributing | LIVE (1.4 / 7) |
| 18 | `vix_term_structure` | DERIVED; CBOE VIX / VIX3M | 2 → 2 | high_is_worse | 0.85 → 1.05 | contributing | LIVE (1.4 / 7) |
| 19 | `spx_vs_200dma` | DERIVED; Yahoo ^GSPC vs own 200d mean | 3 → 1 | low_is_worse | 5 → -10 | contributing | LIVE (1.4 / 7) |
| 20 | `buffett_indicator` | DERIVED, SUBSTITUTE; FRED NCBEILQ027S / GDP | 1 → 3 | high_is_worse | 100 → 300 | contributing | LIVE (105.4 / 120) |
| 21 | `ism_manufacturing` | DERIVED, SUBSTITUTE; 3 regional Fed surveys, z-composite | 3 → 1 | low_is_worse | 0 → -1.5 | contributing | LIVE (13.4 / 45) |
| 22 | `sloos_bank_lending` | DERIVED, SUBSTITUTE; FRED DRTSCILM + hand-entered NDFI leg | 2 → 2 | high_is_worse | 0 → 40 | contributing | MISSING (— / 120) |
| 23 | `private_credit_stress` | DERIVED, SUBSTITUTE; Yahoo BIZD (dividend-adj.) drawdown | 2 → 2 | high_is_worse | 5 → 30 | contributing | LIVE (1.4 / 7) |
| 24 | `constituent_breadth_200dma` | DERIVED, NEW (not a ratified row); Yahoo, fixed 50-name sample | 3 → 1 | low_is_worse | 70 → 30 | contributing | LIVE (1.4 / 7) |

Units are those of the stored figure (percent, index points, claims, ratio, percentile 0–100 etc.). "State" vocabulary is the GUI's: LIVE (fresh value), MISSING (a component is absent), FEED_FAILING (the fetch is failing).

## 1.3 Formulas of the DERIVED equity indicators (`engine/derivations.py`)

The collector never computes; these are the only places a ratio, average or percentile is formed. A derivation that cannot be computed raises `DerivationUnavailable` and emits **no observation** (the dial sees an absence, never a default).

**Ratio** (`breadth_rsp_spy`, `credit_stress_hyg_lqd`, `copper_gold`, `vix_term_structure`, `buffett_indicator`)
```
 d* = newest date on which BOTH numerator N and denominator D have a reading (newest 10 readings each fetched)
 value = scale · N(d*) / D(d*)          (D(d*) must be > 0)
```
Scales: 1 for `breadth_rsp_spy` (RSP/SPY), `credit_stress_hyg_lqd` (HYG/LQD), `vix_term_structure` (VIX/VIX3M); **1000** for `copper_gold` (HG $/lb ÷ GC $/oz × 1000); **0.1** for `buffett_indicator` (NCBEILQ027S in $M ÷ GDP in $B, so 0.1·N/GDP = 100·N/(1000·GDP), i.e. percent). A ratio of different dates is refused.

**`spx_vs_200dma`** (percent vs average)
```
 value = 100 · ( C_t / mean(C_{t−199}, …, C_t) − 1 )
```
`C` = S&P 500 index (^GSPC) closes. Needs ≥ 200 stored closes, the last dated the reading's own date and equal to the reading's value; a shorter history is refused, not averaged short.

**`shiller_cape`** (percentile, in-sample)
```
 H = every monthly CAPE in multpl's table EXCEPT the entry dated the same as the latest; need |H| ≥ 360
 x = latest CAPE
 value = 100 · ( 1 + #{ h ∈ H : h ≤ x } ) / ( |H| + 1 )
```
It is where today's CAPE ranks within its own history since 1871 (ties counted at-or-below; the latest point counts itself). It is **not** the CAPE level.

**`ism_manufacturing`** (z-composite; SUBSTITUTE for ISM PMI)
```
 for each of {Philadelphia, Empire State/New York, Dallas}:   z_r(m) = ( x_r(m) − μ_r ) / σ_r
      μ_r, σ_r = mean and POPULATION std-dev of that survey's whole stored history, latest point included; need ≥ 120 months
 m* = newest month ALL three report
 value = ( z_Phil(m*) + z_NY(m*) + z_Dal(m*) ) / 3
```

**`sloos_bank_lending`** (leg mean; SUBSTITUTE)
```
 value = ( C&I_net_pct_tightening [FRED DRTSCILM] + NDFI_net_pct_tightening [hand-entered] ) / 2
```
Each leg must lie in [−100, 100]. Dated by the OLDER leg. Both legs are required; if either is absent the indicator has no value.

**`private_credit_stress`** (drawdown; MARKET-PRICE PROXY)
```
 value = 100 · ( 1 − C_t / max(C_{t−251}, …, C_t) )          C = BIZD DIVIDEND-ADJUSTED close; ≥ 0 by construction
```
Needs 252 real closes ending on the reading's date. 0 = at a 252-day high.

**`constituent_breadth_200dma`** (new, WO-1.10)
```
 sample S = 50 hand-chosen large caps (AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, BRK-B, JPM, V, UNH, XOM, JNJ, WMT, MA, PG, HD, AVGO,
            CVX, LLY, ABBV, KO, PEP, MRK, COST, ADBE, CRM, BAC, MCD, CSCO, ACN, TMO, ABT, LIN, DHR, NKE, DIS, VZ, TXN, WFC, PM, INTC,
            CMCSA, AMD, IBM, QCOM, CAT, GE, HON, UNP) — fixed, never refreshed
 a name RESOLVES iff it has ≥ 200 stored (dividend-adjusted) closes ending on its reading date; all names are measured on the newest close date any has
     (a name whose latest close is older is unresolved, not carried forward)
 a resolved name is ABOVE iff C_t > mean(last 200 closes)
 value = 100 · #ABOVE / #resolved ;   if #resolved < 30 the indicator has NO value
```
This is a count over a fixed list, not the S&P 500.

## 1.4 Provisional, uncalibrated and structurally weak elements — equity

Stated plainly, not softened.

1. **All 24 bands are unbacktested placeholders** (R-2). The file's own descriptions: derived bands are "round-number guesses placed within roughly ±20 % of the figure's level on 2026-10-09"; `buffett_indicator` 100/300 are "round numbers"; `private_credit_stress` 5/30 were "set after ONE glance at BIZD's own adjusted 10-year drawdown distribution"; `constituent_breadth_200dma` 70/30: 70 is "the ~70 % the legacy tell read live on 2026-07-07", 30 "a round number". The direct-feed bands (e.g. `hy_oas` 3→6, `vix_level` 14→35, `cboe_skew` 120→160) carry no documented derivation either.
2. **Weights are tier rules, not estimates** (R-3).
3. **Substitutions / new constructions on this dial** (R-4):
   - `buffett_indicator` — ratified row is "Wilshire/GDP, percentiled". Wilshire is unavailable. Wired as the Z.1 ratio NCBEILQ027S/(GDP·1000) **in percent, and the "percentiled" step is NOT applied**. Quarterly; its window is 120 days (the engine's ceiling) against a 70–165 day natural age, so **it reads STALE for roughly the last 45 days before each release** (catalog note). Its as-of is the quarter end.
   - `ism_manufacturing` — ISM PMI is licensed; wired as a z-composite of three *regional* Fed surveys. Different quantity; the row's "below 93" arm does not apply. The three surveys are z-scored over **different history lengths** (Philadelphia 701 months, Empire State 303, Dallas 268 at the time of reading), so "0" means a different historical average for each. In-sample; Trinity's provisional choice.
   - `sloos_bank_lending` — plain mean of a FRED leg and a hand-entered leg; the combining rule is an engineering choice "awaiting Owner acceptance". **Currently MISSING (no NDFI entry).**
   - `private_credit_stress` — ratified row is a BDC NAV-discount + non-accrual + PIK composite. Wired as BIZD's drawdown, a price proxy that "moves with equity beta and liquidity as well as credit". It is therefore partly **an equity-drawdown measure inside an equity-crash dial**.
   - `constituent_breadth_200dma` — **not a substitute: a new indicator** with no ratified row, a defined 50-name sample, lowest tier. It overlaps conceptually with `breadth_rsp_spy`; both are scored.
   - `spx_vs_200dma` — the row's ">15 % above = overextended" arm is non-monotone and **is not scored** (one-direction band only); a market 15 % above its mean scores the same 0.0 as one 5 % above.
   - `shiller_cape` — scored on its own-history *percentile* (R-6), not on the CAPE level.
4. **Saturated and zeroed inputs today** (R-6). Clamped at 1.0: `shiller_cape` (×3), `michigan_sentiment` (×1), `real_rate_10y_tips` (×1) — 5 of the 15.66 weighted sum. Scoring 0.0 (at or beyond the calm end): `ig_oas`, `jobless_claims_4w`, `sahm_rule`, `vix_term_structure` (×2 each), `spx_vs_200dma`, `ism_manufacturing` (×1 each) — 10 of the 46 weight carrying zero.
5. **Correlated inputs weighted independently** (R-7). `yield_curve_10y3m` and `yield_curve_10y2y` (×3 each, both REQUIRED); `hy_oas`, `ig_oas`, `credit_stress_hyg_lqd`, `private_credit_stress` (credit, 3+2+2+2); `vix_level`, `vix_term_structure`, `cboe_skew` (volatility); `shiller_cape`, `buffett_indicator` (valuation). The model has no notion of overlap.
6. **Same reading, opposite stress on the two dials.** `real_rate_10y_tips` = 2.87 scores 1.0 (stress) here and 0.0 on the monetary dial. `m2_yoy` and `fed_funds_rate` also run opposite ways on the two dials. This is by ratified design (the bindings carry different polarity) but a reviewer should know the same number is "bad" on one dial and "fine" on the other.
7. **Required-input rule differs from its documentation.** The `$comment` in `indicator-scaling.json` says `required` is set "only on the dial's highest-tier wired indicators". In fact `shiller_cape`, `buffett_indicator` and `breadth_rsp_spy` are tier 1 and **not** required, while the three required ones are the rates/credit tier-1 indicators. (See D-2.)
8. **ARCHITECTURAL GAP — no override for one extreme signal (R-1).** The dial can never be dominated by a single input. Illustration, current inputs: if the three REQUIRED tier-1 indicators (`hy_oas`, `yield_curve_10y3m`, `yield_curve_10y2y`) all went to full stress (s = 1), the numerator would rise by 3·(1−0.05)+3·(1−0.204)+3·(1−0.32) = 7.278, giving (15.663413+7.278)/46 = **0.4987** — a dial still below one half after the credit market and the curve have both fully signalled. There is no worst-of, no breach flag and no escalation path. Conversely, a 0.34 reading is compatible with a single input already at maximum stress.
9. **Absence is renormalised, not zero-filled (R-5).** With `sloos_bank_lending` (×2) MISSING the dial is 15.663413/46 = 0.3405. Had sloos been present and at 0 the dial would be 15.663413/48 = 0.3263; at 1, 17.663413/48 = 0.3680. Separately, `buffett_indicator` (as-of 2026-06-30, window 120 d) ages out on or about 2026-10-28; until the next Z.1 release the dial would read (15.663413−2.325697)/(46−3) = **0.3102** purely because an input went stale.
10. **Coverage is overstated (R-10).** The GUI's `coverage.fraction` is 1.0 and `pending` is empty for this dial, although `sloos_bank_lending` is MISSING. The figure (`wiring.coverage`) counts every *wired* indicator as covered, whether or not it currently has a value.
11. **Dial freshness.** The dial's as-of (`2026-06-30`) is the oldest used input (`buffett_indicator`). The status is **Degraded**, not Value, while `sloos_bank_lending` is missing. (The GUI's `inputs_used` list is empty for a Degraded reading, which is a display property, not a computation one.)

## 1.5 Worked example — live readings at `2026-10-13T08:37:58.298991Z`

Raw values are the GUI's `value` fields (full double precision used; table shows rounded). `s` is the clamped score; `w·s` is rounded to 6 d.p. so column sums differ from the full-precision sum by < 1e-5.

| Indicator | Raw value *v* | calm → stress | (v−calm)/(stress−calm) | clamped *s* | w | w·s |
|---|---|---|---|---|---|---|
| `hy_oas` | 3.15 | 3 → 6 | 0.050000 | 0.050000 | 3 | 0.150000 |
| `yield_curve_10y3m` | 0.99 | 1.5 → -1 | 0.204000 | 0.204000 | 3 | 0.612000 |
| `yield_curve_10y2y` | 0.44 | 1 → -0.75 | 0.320000 | 0.320000 | 3 | 0.960000 |
| `ig_oas` | 0.82 | 0.9 → 2 | -0.072727 | 0.000000 ◀ clamped | 2 | 0.000000 |
| `jobless_claims_4w` | 198,000 | 200,000 → 300,000 | -0.020000 | 0.000000 ◀ clamped | 2 | 0.000000 |
| `sahm_rule` | 0 | 0 → 0.5 | 0.000000 | 0.000000 | 2 | 0.000000 |
| `michigan_sentiment` | 51.7 | 90 → 55 | 1.094286 | 1.000000 ◀ clamped | 1 | 1.000000 |
| `cboe_skew` | 155.06 | 120 → 160 | 0.876500 | 0.876500 | 2 | 1.753000 |
| `vix_level` | 15.21 | 14 → 35 | 0.057619 | 0.057619 | 1 | 0.057619 |
| `chicago_fed_nfci` | -0.494 | -0.5 → 0.5 | 0.006000 | 0.006000 | 2 | 0.012000 |
| `real_rate_10y_tips` | 2.87 | 0 → 2.5 | 1.148000 | 1.000000 ◀ clamped | 1 | 1.000000 |
| `fed_funds_rate` | 3.88 | 2 → 5.5 | 0.537143 | 0.537143 | 2 | 1.074286 |
| `m2_yoy` | 5.65891 | 6 → -2 | 0.042636 | 0.042636 | 2 | 0.085273 |
| `shiller_cape` | 99.1439 | 50 → 99 | 1.002937 | 1.000000 ◀ clamped | 3 | 3.000000 |
| `breadth_rsp_spy` | 0.273988 | 0.29 → 0.25 | 0.400302 | 0.400302 | 3 | 1.200905 |
| `credit_stress_hyg_lqd` | 0.753461 | 0.8 → 0.7 | 0.465393 | 0.465393 | 2 | 0.930786 |
| `copper_gold` | 1.59846 | 2 → 1.2 | 0.501927 | 0.501927 | 2 | 1.003854 |
| `vix_term_structure` | 0.848299 | 0.85 → 1.05 | -0.008505 | 0.000000 ◀ clamped | 2 | 0.000000 |
| `spx_vs_200dma` | 7.61013 | 5 → -10 | -0.174009 | 0.000000 ◀ clamped | 1 | 0.000000 |
| `buffett_indicator` | 255.046 | 100 → 300 | 0.775232 | 0.775232 | 3 | 2.325697 |
| `ism_manufacturing` | 0.694895 | 0 → -1.5 | -0.463263 | 0.000000 ◀ clamped | 1 | 0.000000 |
| `sloos_bank_lending` | **none — MISSING** | 0 → 40 | EXCLUDED | EXCLUDED | (2, not in Σw) | — |
| `private_credit_stress` | 9.34993 | 5 → 30 | 0.173997 | 0.173997 | 2 | 0.347994 |
| `constituent_breadth_200dma` | 64 | 70 → 30 | 0.150000 | 0.150000 | 1 | 0.150000 |
| **Σ** | | | | | **46** | **15.663413** |

```
 M_equity = Σ w·s / Σ w = 15.663413 / 46 = 0.340509        (GUI: 0.3405089786134545)      status: DEGRADED (sloos_bank_lending missing)
```

Raw components of the derived inputs (read from the ingestion store, same instant):

| Indicator | Components | Computation |
|---|---|---|
| `shiller_cape` | latest CAPE 41.87 (2026-10-09); \|H\| = 1868 earlier months (first 1871-02, 10.92); 1852 of them ≤ 41.87 | 100·(1+1852)/(1868+1) = 99.1439 |
| `buffett_indicator` | NCBEILQ027S = 83,050,847 ($M); GDP = 32,563.03 ($B); both dated 2026-04-01 | 0.1·83,050,847/32,563.03 = 255.0464 |
| `breadth_rsp_spy` | RSP 213.19 / SPY 778.10 (2026-10-12) | 0.273988 |
| `credit_stress_hyg_lqd` | HYG 77.29 / LQD 102.58 | 0.753461 |
| `copper_gold` | HG 6.6985 $/lb; GC 4,190.60 $/oz | 6.6985/4190.60·1000 = 1.598458 |
| `vix_term_structure` | VIX 15.21 / VIX3M 17.93 | 0.848299 |
| `spx_vs_200dma` | ^GSPC 7,807.24; mean of last 200 closes 7,255.116 | 100·(7807.24/7255.116 − 1) = 7.6101 |
| `private_credit_stress` | BIZD adj. close 12.100; 252-day high 13.348 | 100·(1 − 12.100/13.348) = 9.3499 |
| `constituent_breadth_200dma` | 50/50 names resolved; 32 above own 200d mean | 100·32/50 = 64.0 |
| `ism_manufacturing` | z: Philadelphia +1.5430 (37.8), Empire State +0.0772 (7.6), Dallas +0.4645 (9.8); month 2026-09 | (1.5430+0.0772+0.4645)/3 = 0.6949 |
| `sloos_bank_lending` | DRTSCILM = 0.0 (2026-07-01); NDFI leg: no entry | **no value** |

A reviewer can verify by hand: the three REQUIRED rows give 0.150000 + 0.612000 + 0.960000; add the rest of the w·s column; divide by Σw.

---

# 2. Dial: `monetary_debasement`

## 2.1 Top-level formula

Exactly §A with *d* = `monetary_debasement`: 10 bound inputs scored (plus `copper_gold`, which is live on the equity dial but **HELD** here), nominal Σw = 21, of which 19 are wired. **Flat weighted mean; no master or worst-of logic.**

```
 M_monetary = Σ_{i∈P} w_i · clamp((v_i − calm_i)/(stress_i − calm_i), 0, 1)  /  Σ_{i∈P} w_i
```

Required inputs (dial is Unknown without them): `broad_dollar`, `breakeven_5y`. Both are **tier 2**; the two tier-1 inputs (`gold_real_rate_cross`, `fiscal_dominance`) are only contributing (D-2).

## 2.2 Every indicator wired to the dial

**All bands are PROVISIONAL, UNBACKTESTED placeholders.**

| # | Indicator | Kind / feed | Tier → weight | Polarity (this dial) | calm → stress | Required? | State now (age / window, days) |
|---|---|---|---|---|---|---|---|
| 1 | `broad_dollar` | DIRECT; FRED DTWEXBGS (index) | 2 → 2 | low_is_worse | 125 → 105 | REQUIRED | LIVE (11.4 / 14) |
| 2 | `breakeven_5y` | DIRECT; FRED T5YIE (%) | 2 → 2 | high_is_worse | 2 → 3.5 | REQUIRED | LIVE (4.4 / 8) |
| 3 | `cpi_yoy` | DIRECT; FRED CPIAUCSL, pc1 (% y/y) | 3 → 1 | high_is_worse | 2 → 6 | contributing | LIVE (43.4 / 45) |
| 4 | `core_pce_yoy` | DIRECT; FRED PCEPILFE, pc1 (% y/y) | 3 → 1 | high_is_worse | 2 → 5 | contributing | LIVE (43.4 / 45) |
| 5 | `real_rate_10y_tips` | DIRECT; FRED DFII10 (%) | 3 → 1 | high_is_better | 2 → -1 | contributing | LIVE (5.4 / 8) |
| 6 | `fed_funds_rate` | DIRECT; FRED DFF (%) | 2 → 2 | low_is_worse | 4 → 0 | contributing | LIVE (5.4 / 7) |
| 7 | `m2_yoy` | DIRECT; FRED M2SL, pc1 transform (% y/y) | 2 → 2 | high_is_worse | 4 → 12 | contributing | LIVE (43.4 / 45) |
| 8 | `gold_spot` | DIRECT; LBMA gold fix USD/oz | 2 → 2 | high_is_worse | 2,000 → 5,000 | contributing | FEED_FAILING (— / 7) |
| 9 | `fiscal_dominance` | DERIVED, SUBSTITUTE; FRED WALCL + CPILFESL, 0/1 flag | 1 → 3 | high_is_worse | 0 → 1 | contributing | LIVE (73.4 / 120) |
| 10 | `gold_real_rate_cross` | DERIVED, SUBSTITUTE; LBMA gold fix vs FRED DFII10 | 1 → 3 | high_is_worse | 25 → 90 | contributing | FEED_FAILING (— / 14) |

**HELD binding (`wiring.HELD_BINDINGS`) — not scored on this dial:** `copper_gold` (tier 2, ×2). The ratified row declares polarity `low_is_better` on this dial while its own comment says falling copper/gold = gold strength = debasement. Those cannot both be right and which is intended is the Owner's call. No monetary band is declared, deliberately. It is unresolved.

## 2.3 Formulas of the DERIVED monetary indicators

**`fiscal_dominance`** (conjunction flag; SUBSTITUTE — the legacy ARGUS discriminator)
```
 g  = ( WALCL_t − WALCL_ref ) / WALCL_ref         WALCL_ref = last WALCL level dated ≤ (date of latest) − 365 days
 π  = ( ( CPILFESL_t / CPILFESL_{t−3 months} )^4 − 1 ) · 100        the level dated exactly 3 calendar months earlier must exist
 value = 1.0 if ( g ≥ 0.10  AND  π ≥ 4.0 ) else 0.0
```
Both legs or nothing; balance-sheet growth alone never fires. Dated by the OLDER leg. The output is a **0/1 flag** and `calm 0 / stress 1` makes the band the identity, so this indicator contributes either 0 or its full weight (×3) to the numerator.

**`gold_real_rate_cross`** (correlation percentile; SUBSTITUTE, Trinity's provisional construction)
```
 shared dates T = dates on which both LBMA gold fix and FRED DFII10 have a value
 for consecutive shared dates (a,b):   r_gold = G_b/G_a − 1 ;   Δy = y_b − y_a   (y in percentage points)   (holiday gaps give multi-day changes)
 ρ_k = Pearson correlation of the 60 most recent (r_gold, Δy) pairs ending at pair k   (window = 60, Trinity's choice)
 latest = ρ_last ;  E = all earlier ρ_k (windows with zero variance skipped; a flat LATEST window is refused);  need |E| ≥ 360
 value = 100 · ( 1 + #{ e ∈ E : e ≤ latest } ) / ( |E| + 1 )
```
This ranks the latest correlation against its own history. It **never tests the correlation's level or sign** and the 60-day windows overlap, so by construction it reads high ≈10 % of the time with no regime change, and a sustained positive-correlation regime reads mid-range. The catalog says so explicitly. **Currently no value** (see §2.4).

(`gold_spot` is DIRECT: the LBMA fix in USD/oz, banded as a **level**, not a trend; the ratified row says "absolute gold trend".)

## 2.4 Provisional, uncalibrated and structurally weak elements — monetary

1. **All 10 bands are unbacktested placeholders** (R-2). `gold_spot` 2000→5000 is "the most arbitrary band in this file" by the file's own words (it brackets one futures close of 4216 seen on 2026-10-09). `gold_real_rate_cross` 25→90 are "guesses". `fiscal_dominance` 0→1 is the identity, not a calibration. `broad_dollar` 125→105, `breakeven_5y` 2.0→3.5, `cpi_yoy` 2→6, `core_pce_yoy` 2→5, `real_rate_10y_tips` 2→−1, `fed_funds_rate` 4→0, `m2_yoy` 4→12 have no documented derivation.
2. **Weights are tier rules** (R-3), identical to the equity dial's weights for the same indicator.
3. **Substitutions on this dial** (R-4): `gold_real_rate_cross` (Trinity's construction above; the ratified row defines neither "divergence" nor "0–100"); `fiscal_dominance` (ratified row is "Treasury/BEA deficit + interest-cost: deficit/GDP vs interest-cost/revenue, discriminated vs benign growth"; wired instead as the Fed-balance-sheet/core-CPI conjunction — a different quantity, *Owner confirmation outstanding*); `gold_spot` (LBMA fix instead of the row's `market:GC` futures; level, not trend).
4. **The dial contains no gold signal today (R-9).** `gold_spot` and `gold_real_rate_cross` are FEED_FAILING (LBMA unreachable from the build host: HTTP 403; no futures substitution is made). They carry 2+3 = 5 of the 21 nominal weight points. The dial is a mean over 14.
5. **A binary ×3 input.** `fiscal_dominance` is 0 today because neither leg fires (g = 2.44 % vs 10 %; π = 1.97 % vs 4.0 %). If it fired, with everything else unchanged, the dial would move from 1.9637/14 = 0.1403 to (1.9637025+3)/14 = **0.3546** — a +0.214 step from one flag. It is also dated 2026-08-01 (73 d old, window 120 d).
6. **Required-input rule differs from its documentation** (D-2): the two REQUIRED inputs are tier 2; the tier-1 inputs are contributing.
7. **Absence is renormalised** (R-5): see §2.5; the weighted sum is divided by 14, not 21.
8. **Coverage is overstated** (R-10). The GUI reports `coverage.fraction = 0.905` (19/21), pending `copper_gold` only, because `wiring.coverage` counts `gold_spot` and `gold_real_rate_cross` as wired although neither currently has a value. By *scored* weight the dial reads 14/21 = 0.667.
9. **Level-based inputs vs rate-of-change inputs.** `cpi_yoy`, `core_pce_yoy`, `m2_yoy` are y/y percentages (already changes); `broad_dollar` and `gold_spot` are levels with fixed bands that will drift out of relevance as the series trend (no re-centring exists).
10. **No override (R-1).** As with equity, no single input, including a fully fired `fiscal_dominance` plus extreme gold, can dominate. Illustration, current inputs: both REQUIRED inputs (`broad_dollar`, `breakeven_5y`) and `fiscal_dominance` at full stress would add 2·(1−0.18076) + 2·(1−0.226667) + 3 = 6.185147 to the numerator, giving (1.9637025 + 6.185147)/14 = **0.5821**.
11. **Dial freshness.** As-of `2026-08-01` is the oldest used input (`fiscal_dominance`). Status is **Degraded** while the two gold inputs are failing.

## 2.5 Worked example — live readings at `2026-10-13T08:37:58.298991Z`

| Indicator | Raw value *v* | calm → stress | (v−calm)/(stress−calm) | clamped *s* | w | w·s |
|---|---|---|---|---|---|---|
| `broad_dollar` | 121.385 | 125 → 105 | 0.180760 | 0.180760 | 2 | 0.361520 |
| `breakeven_5y` | 2.34 | 2 → 3.5 | 0.226667 | 0.226667 | 2 | 0.453333 |
| `cpi_yoy` | 3.35302 | 2 → 6 | 0.338255 | 0.338255 | 1 | 0.338255 |
| `core_pce_yoy` | 3.0076 | 2 → 5 | 0.335867 | 0.335867 | 1 | 0.335867 |
| `real_rate_10y_tips` | 2.87 | 2 → -1 | -0.290000 | 0.000000 ◀ clamped | 1 | 0.000000 |
| `fed_funds_rate` | 3.88 | 4 → 0 | 0.030000 | 0.030000 | 2 | 0.060000 |
| `m2_yoy` | 5.65891 | 4 → 12 | 0.207364 | 0.207364 | 2 | 0.414727 |
| `gold_spot` | **none — FEED_FAILING** | 2,000 → 5,000 | EXCLUDED | EXCLUDED | (2, not in Σw) | — |
| `fiscal_dominance` | 0 | 0 → 1 | 0.000000 | 0.000000 | 3 | 0.000000 |
| `gold_real_rate_cross` | **none — FEED_FAILING** | 25 → 90 | EXCLUDED | EXCLUDED | (3, not in Σw) | — |
| **Σ** | | | | | **14** | **1.963703** |

```
 M_monetary = Σ w·s / Σ w = 1.963703 / 14 = 0.140264        (GUI: 0.1402644642857143)      status: DEGRADED (gold_spot, gold_real_rate_cross missing)
```

Raw components of the derived input:

| Indicator | Components | Computation |
|---|---|---|
| `fiscal_dominance` | WALCL latest 6,747,560 (2026-10-07) vs 6,587,119 (2025-10-01, last level ≤ 365 d earlier); core CPI level 337.765 (2026-08-01) vs 336.121 (2026-05-01) | g = 2.436 % (< 10 %); π = ((337.765/336.121)^4 − 1)·100 = 1.971 % (< 4.0 %) ⇒ **0.0** |
| `gold_real_rate_cross`, `gold_spot` | LBMA fetch failing | **no value** |

Note the hand arithmetic: the largest single contribution is `breakeven_5y` (0.4533), then `m2_yoy` (0.4147), and the REQUIRED `broad_dollar` and `breakeven_5y` together supply 0.8149 of the 1.9637 numerator.

---

# 3. Index of every provisional / substituted element

| Indicator | Dial(s) | What it is instead of / beyond the ratified row | Band basis | Status |
|---|---|---|---|---|
| `buffett_indicator` | equity | Z.1 equities/GDP in percent; "percentiled" step not applied (Wilshire unavailable) | round numbers 100/300 | substitute, accepted by Matt per Trinity dispatch WO-1.6 |
| `ism_manufacturing` | equity | z-composite of 3 regional Fed surveys instead of ISM PMI | round numbers 0/−1.5 | substitute, Trinity-provisional, not Owner-ratified |
| `sloos_bank_lending` | equity | mean of FRED C&I leg + hand-entered NDFI leg | 0/40 from the row's own "40 % preceded every recession since 1990" | substitute, awaiting Owner acceptance; **MISSING now** |
| `private_credit_stress` | equity | BIZD price drawdown instead of NAV/non-accrual/PIK composite | 5/30 after one glance at one ticker | substitute, Trinity-directed, not Owner-ratified |
| `constituent_breadth_200dma` | equity | NEW; % of fixed 50 names above 200d mean | 70/30 (70 = legacy reading, 30 = round) | new construction; not a ratified row |
| `shiller_cape`, `spx_vs_200dma`, `copper_gold`, `breadth_rsp_spy`, `credit_stress_hyg_lqd`, `vix_term_structure` | equity (`copper_gold` also monetary, HELD there) | WO-1.5 derivations of the ratified rows; bands are "least-grounded numbers in the file"; `spx_vs_200dma`'s ">15 % above" arm unscored | guesses ≈ ±20 % of the 2026-10-09 level | ratified definition, uncalibrated bands |
| `gold_real_rate_cross` | monetary | Trinity's rolling-correlation-percentile construction | 25/90 guesses | substitute, not Owner-ratified; **FEED_FAILING now** |
| `fiscal_dominance` | monetary | legacy ARGUS Fed-balance-sheet/core-CPI conjunction | 0/1 identity | substitute; Owner confirmation outstanding |
| `gold_spot` | monetary | LBMA fix level, not "absolute gold trend" | 2000/5000, "most arbitrary" | **FEED_FAILING now** |
| `copper_gold` (monetary binding) | monetary | — | none | **HELD**: ratified polarity word and row comment disagree |

All direct-feed indicators (FRED rates/spreads/macro, CBOE) are the ratified rows' own quantities, but their calm/stress bands are equally unbacktested.

---

# 4. Where this document differs from the dispatch brief, and from the code's own comments

The code wins; these are the corrections.

| Ref | Brief or comment said | The code does |
|---|---|---|
| **D-1** | "polarity-aware" top-level equation | There is no polarity term. Polarity is the *order* of `calm` and `stress` in each band; `s = clamp((v−calm)/(stress−calm))`. |
| **D-2** | `indicator-scaling.json` `$comment`: `required` is set "only on the dial's highest-tier wired indicators" | False on both dials. Equity required = `hy_oas`, `yield_curve_10y3m`, `yield_curve_10y2y` (tier 1), but tier-1 `shiller_cape`, `buffett_indicator`, `breadth_rsp_spy` are contributing. Monetary required = `broad_dollar`, `breakeven_5y` (**tier 2**), while tier-1 `gold_real_rate_cross` and `fiscal_dominance` are contributing. |
| **D-3** | State vocabulary LIVE/DERIVED/FEED_FAILING/MISSING/HELD/BLOCKED | The GUI emits only LIVE, MISSING and FEED_FAILING per indicator. "Derived" is a *kind*, not a state (derived indicators show LIVE). HELD is per *binding* (`copper_gold` on the monetary dial). No indicator is BLOCKED: all 31 rows are wired and `DERIVATION_BLOCKED` is empty. |
| **D-4** | Substitution list: `buffett_indicator`, `ism_manufacturing`, `private_credit_stress`, `gold_real_rate_cross`, `constituent_breadth_200dma` | Also substituted: **`sloos_bank_lending`** and **`fiscal_dominance`**, and `gold_spot` is a level where the row says trend. And `constituent_breadth_200dma` is a new indicator, not a replacement. |
| **D-5** | "confirmed in Trinity's audit this week" (flat mean, no master) | Confirmed independently here from `mapping.py` and `evaluate.py`; the audit itself was not consulted. |
| **D-6** | Weight (tier → 3/2/1) as part of each dial's band table | Weight is per indicator and **identical on both dials**; it is not in `indicator-scaling.json` and is derived at wiring time from the ratified mapping's tier. |
| **D-7** | (implicit) both dials give a reading | **Neither dial is a clean `Value` today**: both are `DEGRADED`. |

---

# 5. Reproducing the figures

1. `curl http://192.168.11.10:8710/api/state` gives each indicator's `value`, `state`, age and window, and each dial's value.
2. For each dial read `deploy/indicator-scaling.json` (bands, `required`) and `governance/mapping/indicator_mapping.yaml` (tier → weight 3/2/1).
3. Apply §A. Drop any indicator with no value (state MISSING/FEED_FAILING), and any indicator on this dial that is HELD.
4. The result equals the dial value on the GUI to double precision. Float summation in the code is in sorted `source_id` order; a different order can differ in the last digit.
