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

Inputs with weekly/monthly cadence count once per new observation; persistence is counted in readings, so a monthly series cannot by itself satisfy a 3-reading rule and will only ever confirm a transition the daily inputs already made.

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
| **CALM** | No master in its warning band; breadth < B_mid; count < k; all for the persistence period | Deploy on schedule, sized by multiplier | Hold cash/gilts normally |
| **WATCH** | Breadth rising over 20 readings **and** above B_mid, **or** any master in its warning band | **Halt new tranches**; hold existing | Hedge-asset (gold) tranches permitted, sized by multiplier |
| **ALARM** | **Any one master beyond its stress threshold** (acute), **or** breadth ≥ B_high with count ≥ k | No buying. Deployed capital follows Epic 2's independent drawdown rule | Nominal cash/gilts capped (cap is an Epic 2 parameter); gold permitted |
| **RECOVERY** | Was ALARM; acute below its **exit** threshold (exit < entry) for the persistence period **and** trend confirming (reference index above a flattening 200-day mean, **or** a higher low on the acute statistic). **Both are required.** | Tranches permitted again, one at a time, subject to §8 | — |
| **UNKNOWN** | Any REQUIRED input absent/stale, or the coverage bracket (§9) spans a state boundary and cannot be resolved conservatively | **No permission** (treated as WATCH for permission purposes, never as CALM) | No permission |

Rules of precedence:

- A master beyond stress fires ALARM on its own. Calm readings elsewhere cannot outvote it.
- Breadth and count can **raise** a state; they can never **lower** one while a master is firing.
- RECOVERY requires both conditions because acute-fallen alone would have reopened the gate in Oct–Nov 2008, months before the low, and trend alone is a lagging average cross. Late by design.
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
| persistence | consecutive readings for a transition | 3 | Trinity, provisional |
| N | time floor in CALM | 6 months | provisional |
| X | averaging-down guard (Epic 2) | 10% | provisional |
| B_mid, B_high | breadth thresholds | **unset** | calibration |
| k | count threshold | **unset** | calibration |
| master set, warning/stress/exit thresholds | per master | **unset** | calibration |
| multiplier range | sizing_multiplier bounds | 0.5–1.5 | provisional |
| lookback for `acute_rising` | readings | **unset** (20 suggested) | calibration |

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
