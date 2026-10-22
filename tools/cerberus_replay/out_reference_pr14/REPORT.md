# CERBERUS WO-1.3b-II — live re-audit of PR #14 (R2D2, 2026-10-22)

**Requested by:** Trinity. **Scope:** Epic 1 only (Epic 2 consumer rules WO-2.7/2.8/2.9 not touched). **Store:** Rogue's lane — reported, not patched.

## 0. Verdict

> **RED as written (`wo/CERBERUS-WO-1.3b-II-implementation` @ `5864e47`).
> AMBER (conditional) once the three blocking changes in §3 are made.
> GREEN is not reachable from this store, and cannot be until the evidence gaps in §6 close.**

PR #14 is a faithful implementation of my eight WO-1.3b-II findings. I found no transcription error: the lock, the trend and the per-master thresholds
all behave as my harness did (§2, §4). The RED comes from three defects that the replay and the live feed exposed, and one of them traces to my own
recommendation (§3 D3, §7). On this week's live DEV feed the PR's dial goes **CALM → ALARM on 2026-10-20 with every master calm to mild**, while the
deployed build reports CALM. A dial that does that is not live-decision-grade, whatever its replay protection looks like.

Evidence grade: real code, real store, real live feed, in-sample. Four primary (≥20%) declines and ten declines ≥15% (1990–2026) in the whole base; no
out-of-sample test exists. Control-series numbers are lower bounds (§1).

## 1. What I audited, and how

| item | value |
|---|---|
| code under test | `wo/CERBERUS-WO-1.3b-II-implementation` @ `5864e47ff71f9ad5779644d28b0dc1f63214f52a` (git archive, unmodified); `main` @ `fa6fd30` is its base |
| store | `dell-debian:/srv/cerberus/wo117-data/wo117_historical.sqlite`, opened `mode=ro`. File sha256 `d6197722…aa2b`; **logical row hash `959f99b9e2382cc06b81085bd3818e416c5bfdbf6a8a0fe190bda179917b0e41` is identical to my WO-1.3b-II snapshot** (47,676 observations / 39,401 readings). Nothing on dell-debian was modified (one temp `.sqlite` copy made and deleted, `/tmp/r2_*`) |
| item 8 | as briefed: backfill not re-run; the store still holds the old window's OAS rows (108 each) |
| the pass | the PR's real `evaluator.pass_once.one_pass_for_both_dials` (the function `deploy/live-dev/evaluator_loop.py` calls), once per market day, 2,514 days, fresh history per episode |
| what is mine | only the **store view**: before the pass for day *d* a scratch raw store holds exactly the `raw_reading` rows knowable at *d* (vintage_date for `original`, else as_of+1 day, as in WO-1.3b-II). `latest_reading()` is not as-of aware, so a point-in-time store is the only honest way to drive it |
| control series (outside the store, labelled wherever used) | ^GSPC/^VIX/^VIX3M (Yahoo), T10Y3M/T10Y2Y/BAA10Y/DFII10 (FRED), SKEW (Cboe). sha256: SKEW `e9c6e84e…733a`, DFII10 `f004bf16…bc11`; others as in the WO-1.3b-II report. The control carries no hy_oas, ig_oas or copper_gold, so every ALARM/false-alarm count taken from it is a **lower bound** |
| live feed | read-only copy of the DEV raw store and state (`cd-live-data`, `cd-live-state`), 2026-10-22; sha256 `ebf580ab…0f7` / `a44d9662…9d` |
| PR's own tests | 232 passed in my environment (`test_wo13b2_implementation`, `test_resolve_official_state`, `test_engine_candidate_state`, `test_engine_masters`, `test_evaluator_pass`; `pyproject`'s `minversion` pytest-9 overridden, local pytest is 8.3.4) |

Four replay configurations (`tools/cerberus_replay/live/README.md`): **A** the real pass on the store as it is; **B** A plus S&P `history` as the live
collector stores it; **C** B plus `hy_oas` no longer REQUIRED (one flag in `deploy/indicator-scaling.json`) and acute taken over the masters that scored
(*replay-only*: shows what the engine decides were every input present); **D** C on the store as it is.

## 2. Rogue's four interpretation calls — against the live code

| # | call | ruling | evidence |
|---|---|---|---|
| 1 | breadth unset disables the rising-WATCH limb entirely | **CONFIRMED** | `candidate_state_for_one_reading` guards the limb with `PROVISIONAL_BREADTH_MID is not None`; with it `None`, breadth 0.9 vs 0.1 twenty rows ago, 1.0 vs 0.0, 0.489 vs 0.3 all return CALM; a 0.65 master still returns WATCH. Matches my F4 (B_mid unsupportable). Consequence to record: breadth is now display-only for the state machine |
| 2 | equity-only trend/lock | **CONFIRMED as implemented; the cost is real and should be owned.** | `pass_once.one_pass_for_dial` arms trend and lock for `EQUITY_DIAL_ID` only. Rogue's reasoning (a lock with no key halts forever) is sound. But the monetary dial keeps the back door: with the real resolver, 6 stress days then quiet gives `ALARM×10 → WATCH×5 → CALM×5` with no RECOVERY, and in the available-masters replay the monetary dial did exactly that in 2022 (`ALARM 66d → WATCH 13d → ALARM 21d → WATCH 29d → CALM 160d`). It needs an owner and a trend measure. It cannot be tested on the store: under the real pass the monetary dial is **UNKNOWN on 100% of days in all 8 episodes** (`monetisation_flag`, `gold_real_rate_cross` and `ism_manufacturing` need a stored `history` the backfilled rows do not carry) |
| 3 | "armed" semantics match my `eval_lock.py` | **CONFIRMED for every history the lock governs** | SQL `alarm_lock_armed` = "ALARM newer than the latest CALM or RECOVERY"; my harness = "an ALARM since the latest RECOVERY". Exhaustive over all 3,905 histories of ≤5 rows they differ on 490, every one a CALM row following an ALARM with no RECOVERY between. The lock makes that pattern unreachable: 120,000 resolver steps over 400 random histories, **0 violations**, 0 end-states where the two disagree, RECOVERY reached 69 times. UNKNOWN rows correctly do not clear it. The one intended difference (pre-lock history is not re-armed) is the documented design. **But see D2: the semantics are right and the UNKNOWN-exit path still lets a locked dial skip persistence** |
| 4 | the monetary dial's count can never reach k | **CONFIRMED, structurally** | of the monetary dial's 10 scaled indicators only `real_rate_10y_tips` is in `COUNT_INDICATOR_IDS`; with every monetary indicator pinned at 1.0 the real `count_for_one_dial` returns 1, K is 2. The equity dial with everything pinned returns 10. So rule 3 is an equity-only rule in effect; the monetary dial alarms only on `real_rate_master`/`currency_master` ≥ 0.85 (`fiscal_master` is ineligible). Say so in DECISION-RULE.md or make K per-dial |

Items 1–8 ledger (all eight are implemented as I specified; the exceptions are in §3):

| item | status | evidence |
|---|---|---|
| 1 vol stress 0.85→0.70 | ✓ | thresholds ride on `MasterScore`; `_DECLARED_THRESHOLDS`; replay ALARM in 8/8 episodes |
| 2 post-ALARM lock | ✓ with **D2** | §2 row 3 |
| 3 trend | ✓ | PR's `trend_confirmed_from_closes` vs my `eval_lock.trend` on the control S&P: **14,105 days, 0 disagreements** |
| 4 count v2, k=2 | ✓ as I specified — **and that specification is the defect** (D1, D3) | `COUNT_INDICATOR_IDS` = my `FAST2` exactly |
| 5 breadth unset | ✓ | §2 row 1 |
| 6 `acute_rising` deadband 0.02 | ✓ | flag true on 217/906 = 24.0% of permitted days in C (42–51% before) |
| 7 dead ratios excluded | ✓ | `breadth_rsp_spy` and `credit_stress_hyg_lqd` are not in `build_wiring().live_ids` |
| 8 OAS window to 2023-10-23 | ✓ code-complete, not run | `row_dates` yields 420 HY / 419 IG dates, contiguous from 2023-10-23, 312/311 new, nothing before FRED's floor, no gaps >5 days. **It cannot change any replay**: the extra rows land on dates where the store has no S&P, curve or VIX rows, so no dial day becomes evaluable. Its only use is a standalone 14-month calm baseline for `credit_master`. Run it when convenient; do not expect the verdict to move |

## 3. Three blocking defects

### D1. The count re-admits the curve master through the back door (regression of the curve demotion)

`curve_master.alarm_eligible=False`, but `yield_curve_10y3m` and `yield_curve_10y2y` are both in `COUNT_INDICATOR_IDS`. Both at ≥0.80 (10y3m ≤ −0.50%,
10y2y ≤ −0.40%) is count 2 = k, so rule 3 returns ALARM. Proven on the real functions: curve_master 0.80, volatility 0.10, count 2 → `State.ALARM`.

- The PR's test `test_the_curve_master_is_still_watch_only_at_0_60_and_a_curve_at_0_95_does_not_alarm` passes only because it hands the function `Count((), ())`, an empty count, and never calls `count_for_one_dial`.
- Real pass on the store (C): `2000-08-14→09-05` (11 d, vol 0.28) and `2022-11-16→12-30` (31 d, vol 0.28, NFCI 0.23) are count-only ALARM candidates on the two curves.
- Control 2006-07→2026-10 (5,055 days): 489 count-only candidate days (vol master below its stress), **424 of them (87%) involve a curve indicator**. The curve pair alone: 274 days in 8 runs, all in 2022–24; the S&P fell ≥10% within 63 days after **1%** of them (unconditional 15%). Every curve-involving combination: ≤1%.
- Effect on this control: ALARM days 18.4% → **26.3%**, false-alarm spans 0.69 → **0.94 / yr**. Permission impact here is nil (DENY 48.2% either way, because curve WATCH already denies), so what D1 changes is the **ALARM label** and **lock arming**: a curve-only ALARM arms a lock that a curve WATCH would not.

**Fix (one line, owner Rogue):** remove `yield_curve_10y3m` and `yield_curve_10y2y` from `COUNT_INDICATOR_IDS`; add a test that drives the real `count_for_one_dial`.

### D2. One quiet reading after a data outage re-opens the dial (regression of the UNKNOWN-exit floor)

With the lock armed, a RECOVERY candidate "stands whatever the previous state is" (`resolve.py`), and leaving UNKNOWN is immediate. Together: real resolver, real
history store, real lock query —

| case | result |
|---|---|
| dial ALARM (lock armed) → UNKNOWN row → first resolvable reading quiet, trend true | **official RECOVERY, counter 0, on one reading** |
| same dial with no outage | `ALARM(1) ALARM(2) ALARM(3) ALARM(4) RECOVERY` — five readings, as designed |
| dial WATCH under lock → outage → one quiet reading | official RECOVERY |
| pre-PR (`alarm_lock_armed=False`), same outage | WATCH |

RECOVERY is a permission state. This is the "one unverified number after an outage = permission" hole WO-1.3e round 3 closed for CALM, reopened for RECOVERY by the
lock. Reachable in production: `_unknown_row` does not consult the lock, the next pass does.

**Fix (owner Rogue):** in the previous-state-UNKNOWN arm, floor a RECOVERY candidate at WATCH (as CALM already is), or run it through persistence. Add the test.

### D3. A standing vote makes k=2 fire on a calm feed — and this one is mine

`real_rate_10y_tips` scores ≥0.8 once the 10-year TIPS yield is ≥2.0%: 47% of days since 2023-10-23, 59% of 2026, **2.74–2.84% this week (score 1.0)**. With TIPS
effectively always voting, k=2 reduces to "any one more fast indicator at 0.8" — SKEW ≥152 (24% of days since 2023-10-23).

Replay of the PR's real pass over the live DEV feed, 2026-10-14 → 10-21, with a 25-row CALM history so persistence counts as it would live:

```
2026-10-14 CALM cand ALARM ctr 1   masters credit .05 curve .33 vol .06 nfci .01   count 2 (cboe_skew, real_rate_10y_tips)
2026-10-15 CALM cand ALARM ctr 2   credit .08 curve .36 vol .24 nfci .00           count 2
2026-10-16 CALM cand ALARM ctr 3   credit .08 curve .38 vol .20                    count 2
2026-10-19 CALM cand ALARM ctr 4   credit .10 curve .37 vol .63                    count 2
2026-10-20 ALARM                   credit .10 curve .35 vol .45                    count 2   lock armed
2026-10-21 ALARM                   credit .10 curve .38 vol .31                    count 2
```

S&P 7,650 on 10-22 (−2.2% from its 252-day high, +5.0% over its 200-day mean); VIX 15–20. The deployed build (pre-PR) is CALM on 317 of the 337 rows in its history and WATCH on 20. In the DEV history, 161 of 337 rows
(48%) had SKEW and TIPS both ≥0.90, each of which is an ALARM candidate under the PR. Today's single pass (10-22): CALM, count 1 (TIPS only) — **one SKEW print ≥152 away from ALARM with every master calm.**

Control 2006–2026 through the PR's resolver, lock and trend (lower bound):

| count composition | ALARM days | DENY | false-alarm spans / yr | declines caught |
|---|---|---|---|---|
| no count in rule 3 | 17.3% | 47.4% | 0.64 | 7/7 |
| **PR as written** (k=2, all 10 ids) | **26.3%** | 48.2% | **0.94** | 7/7 |
| k=2, curves out | 18.4% | 48.2% | 0.69 | 7/7 |
| k=2, curves + TIPS out | 17.3% | 47.4% | 0.64 | 7/7 |
| k=2 over {vix_level, vix_term, spx_vs_200dma, skew} | 17.3% | 47.4% | 0.64 | 7/7 |
| k=3, all 10 ids | 18.2% | 47.4% | 0.84 | 7/7 |

The count adds **no detection** on twenty years (every decline is caught by the volatility master with or without it) and adds false alarms. The lift I reported for count v2 in WO-1.3b-II (63% → 76% of the decline still ahead) came from eight event windows with no calm baseline (§7).

**Fix (decision for Trinity; recommendation):** take count out of rule 3 (the WO-1.3e state) until a calm baseline exists for the credit pair, or restrict `COUNT_INDICATOR_IDS` to market-priced stress with no level indicators and no curve indicators. Either removes D1 as well. I recommend the first.

## 4. What the real pass does on the real store

**Coverage map** (official equity state, share of days; `n` = market days in the window). Monetary dial: UNKNOWN on 100% of days in all eight.

| episode | n | A/B (real pass, store as is) | masters that score in C |
|---|---|---|---|
| 2000-02 | 794 | UNKNOWN 100% | curve 100%; credit, vol, NFCI 0% |
| 2007-09 | 695 | UNKNOWN 100% | curve 100%; vol 10% (VIX3M only from 2009-09); credit, NFCI 0% |
| 2011 | 212 | UNKNOWN 100% | curve 100%, vol 100%, NFCI 70% (floor 2011-05-27) |
| 2015-16 | 210 | UNKNOWN 100% | curve, vol 100%, NFCI 97% |
| Q4-2018 | 104 | UNKNOWN 100% | curve 99%, vol 99%, NFCI 96% |
| Mar-2020 | 103 | UNKNOWN 100% | curve 99%, vol 99%, NFCI 92% |
| 2022 | 293 | UNKNOWN 100% | curve, vol 100%, NFCI 97% |
| Apr-2025 | 103 | ALARM 65.0%, WATCH 30.1%, UNKNOWN 4.9%, CALM 0% | credit 99%, curve 99%, vol 99%, NFCI 95% |

Strict UNKNOWN is `hy_oas` REQUIRED and absent before 2024-12-31 — unchanged by the PR, and **item 8 cannot change it**: FRED holds no OAS before 2023-10-23. Credit_master has therefore been
observed in one episode; there it peaked at 0.54 and never reached its warning.

**Protection** (C; first ALARM after the S&P peak; share of the peak-to-trough fall still ahead):

| episode | fall | first ALARM | S&P then | ahead |
|---|---|---|---|---|
| 2000-02 | −49.1% | 2000-08-28 | −0.9% | 98% |
| 2007-09 | −56.8% | 2008-09-29 | −29.3% | 48% |
| 2011 | −19.4% | 2011-08-03 | −7.6% | 61% |
| 2015-16 | −14.1% | 2015-08-27 | −6.6% | 53% |
| Q4-2018 | −19.8% | 2018-10-25 | −7.7% | 61% |
| Mar-2020 | −33.9% | 2020-03-02 | −8.7% | 74% |
| 2022 | −25.4% | 2022-01-28 | −7.6% | 70% |
| Apr-2025 | −18.9% | 2025-01-02 (in force; counted from 02-19) | ≈0% | 100% |

Primary (≥20%) mean 73%, all eight 71% — ALARM in 8/8 episodes. My harness predicted 76%/72% for the same configuration. **Do not read Apr-2025 as skill**: its ALARM from 2025-01-02 is 34 days of D3 (SKEW + TIPS, S&P within 0.8% of its high).

**Parity with my WO-1.3b-II harness** (configured as the PR intends, same days, same trend flags): **2,509 of 2,514 days identical**. The five differences are 2024-12-31 → 2025-01-07: the real dial is UNKNOWN on 12-31, and leaving UNKNOWN is immediate (an accepted WO-1.3e call), where my harness started its history on a CALM row.

**The lock in replay.** On the store as it is (D) the lock never releases in any episode (0 RECOVERY days): the stored S&P readings carry no `history`, so `equity_trend_confirmed` is False on every day and `spx_vs_200dma` cannot be derived. With live-shaped S&P history (C) RECOVERY is reached in 3 of 8 episodes (2007-09 on 2009-08-19; 2015-16 on 2015-11-02; 2022 on 2022-02-08, ten days, then relapse). The live collector does store 260 closes (`yahoo.^GSPC`: 260, trend True on today's feed), so production can release the lock; **the backfilled store cannot be used to validate it**.

## 5. The cost side of the lock (Trinity's F1 decision, now quantified end to end)

Control 2006–2026, PR resolver (lower bound on denial):

| | DENY share | premature re-opens | re-entry after the low (median) | longest continuous deny |
|---|---|---|---|---|
| no lock, vol 0.70 | 38.0% | 5 (mean further fall −31%) | 73 d, +18% off the low | 629 d |
| lock + trend | 47.4% | 2 (−38%) | **190 d, +38%** | 718 d |
| PR as written | 48.2% | 2 (−38%) | 190 d, +38% | **943 d** (2022-02-22 → 2025-12-04) |

RECOVERY requires every master ≤ its exit, `curve_master` included, so a chronically inverted curve holds the lock (and the F7 curve-WATCH duration is still undecided, with no threshold that fixes it). The lock does what it was designed to do: premature re-opens fall from 5 to 2. It costs roughly 2.6× the delay to re-entry.

## 6. What this audit does not establish

- **Out-of-sample performance.** Everything is in-sample; four primary declines.
- **`credit_master`**: one episode (Apr-2025), never at warning. Its bands are untested.
- **The monetary dial**: unreplayable on the store (100% UNKNOWN under the real pass). Its lock-less back door (§2 row 2) is shown on the resolver and on an available-masters replay only.
- **Trend/lock on backfilled data**: needs S&P history the store does not carry. I supplied it from the control series (equal to the store's S&P on all 2,514 days) and said so.
- **Control results** exclude hy_oas, ig_oas and copper_gold; denial and false-alarm counts are lower bounds.
- **GBP dial and the Sept-2022 gilt event**: still unobservable (no GBP/gilt/BoE rows). Epic 2 not examined.

## 7. Correction to my own WO-1.3b-II report

I recommended count v2 with k=2 over `FAST2` as "provisional" and measured it only on the store's eight event windows, which have no calm baseline for SKEW, TIPS or the curves. A recommendation that adds a standing vote to rule 3 needs a calm baseline first; I had one for the vol and curve masters and did not extend it to the count. On the 20-year control the count catches nothing the volatility master does not, and on this week's live feed it raises ALARM. I withdraw the count v2 k=2 recommendation as specified. Rogue implemented it exactly; the fault is in the specification.

## 8. Decisions and asks

**Trinity**
1. Accept the three blocking changes (D1, D2, D3-recommendation), or choose the D3 alternative. I will re-audit the fixed code against the same four configurations and the live-week replay; the fixes are small.
2. F7 — curve WATCH duration: still open, and it now drives lock duration.
3. Monetary dial back door: name an owner and a trend measure, or record it as a known open defect.
4. Item 8 may run whenever convenient. It does not affect this verdict.

**Rogue (via Trinity)** — store and code, not patched by me
1. D1 and D2 fixes and tests above.
2. The backfilled readings carry no `history` for `yahoo.^GSPC`, `fred.WALCL`, `fred.CPILFESL`, gold or the Philadelphia series, so `spx_vs_200dma`, the trend, `monetisation_flag`, `gold_real_rate_cross` and `ism_manufacturing` cannot be derived from the store. Whether a point-in-time history reconstruction is in scope for the backfill is yours to decide; without it, trend/lock/monetary can only be validated through a labelled control series.
3. `pyproject.toml` requires pytest ≥ 9.0; the environment I tested in has 8.3.4. Not a defect, a reproduction note.

## 9. Reproduction

`/srv/r2d2/tools/cerberus_replay/live/` (branch `wo/CERBERUS-WO-1.3b-II-pr14-live-audit`, local, not pushed): `fetch_pr14_inputs.sh`, `launch.sh`, `analyse.py`, `calls_test.py`, `unknown_exit_test.py`, `control_sim*.py`, `combos.py`, `parity.py`, `misc_checks.py`, `today.py`, `today_replay.py`. Outputs: `evidence/cerberus_wo13b2_pr14/out/*.out`, per-day states `out/runs_summary.json`.
