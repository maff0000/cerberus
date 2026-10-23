# R2D2 — CERBERUS WO-1.3b-II, PR #14 re-audit at `f290583` (2026-10-23)

Scope: Epic 1 only. Store is Rogue's lane (read-only here). Prior audit: `../cerberus_wo13b2_pr14/REPORT.md` (head `5864e47`, RED).

## Verdict

**D1, D2, D3: all CONFIRMED FIXED, on the real engine. No regression found. Readiness: AMBER (conditional). GREEN is still not reachable from this store.**

The RED of `5864e47` is withdrawn for `f290583`. AMBER, not GREEN, for the reasons under "Why still AMBER".

## What was run

- Code under test: `git archive f290583` (unmodified). Only the store view is mine (point-in-time scratch raw store, as before).
- The same real `evaluator.pass_once.one_pass_for_both_dials`, once per market day, 2,514 days, 8 episodes, fresh history per episode, the same four configs (A strict as-is, B + live-shaped 260-close S&P history, C relaxed `hy_oas` + masters available [replay-only], D = C as-is). 10,056 passes, 0 pass errors.
- Store logical row hash `959f99b9…0b7` (identical to the previous audit). Control series byte-identical (SKEW.csv `e9c6e84e…`, DFII10.csv `f004bf16…`).
- Diff of `5864e47..f290583` read in full: `resolve.py` (D2), `statistics.py` (D1, D3), docs/yaml/tests only otherwise.
- PR test suite, full: 2,981 passed, 1 skipped (legacy ARGUS source not on this host), on a scratch copy with `minversion` relaxed (pytest 8.3.4 here, pyproject wants >= 9). The "232 passed" quoted last time was a 5-file subset and is not comparable.

## D1 — curve pair can no longer carry ALARM: FIXED

- `COUNT_INDICATOR_IDS` = 8 ids, no `yield_curve_*`.
- Real `count_for_one_dial` with both curves at 1.0, rest calm: count 0, candidate WATCH (`out/d1d3_check.out`).
- Store replay, config C 2000-02: first old ALARM 2000-08-28 was `yield_curve_10y2y + yield_curve_10y3m` only (count 2, `curve_master` .83, no eligible master at stress). New head: WATCH.

## D2 — UNKNOWN-exit floor wins over the lock: FIXED

- `unknown_exit_test` Case 1 (armed lock, ALARM -> outage -> one fully quiet reading, trend confirmed): `5864e47` gave RECOVERY, `f290583` gives **WATCH**, counter 0, equal to the unlocked pre-PR behaviour (Case 4).
- No-outage control (Case 2): unchanged, the lock still holds the dial in ALARM then walks RECOVERY.
- Case 3 (WATCH under lock after outage): WATCH.

## D3 — rule 3 removed (`PROVISIONAL_COUNT_K = None`): FIXED, near-miss dead

- Code: rule 3 sits behind `PROVISIONAL_COUNT_K is not None`; rule 2 is the only ALARM path.
- Fuzz over the real `candidate_state_for_one_reading`: 300,000 random readings (random master scores incl. exact thresholds, random count sets of size 0..8, random breadth/trend), **candidate ALARM == (an alarm-eligible master at or beyond its own stress threshold) on every one**. Count never mattered. All 8 count ids pinned at 1.0 with masters calm: count 8, candidate CALM.
- Where count goes now: only `indicator_count` / `count_at_or_beyond` into the history store and the published contract (`evaluator/contract.py`). Nothing reads it to decide a state.
- **The 2026-10-20 live-feed near-miss, replayed on the same DEV copy (10-14 .. 10-22, readings admitted to 2026-10-22T16:55Z, seeded 25-row CALM history):** `5864e47`: candidate ALARM from 10-14, official ALARM on 10-20 (credit .10, curve .35, vol .45, NFCI 0). `f290583`: **CALM on every day**. 10-19 volatility .63 gives a one-day WATCH candidate (counter 1) that does not persist. Published count is still 2 (`cboe_skew`, `real_rate_10y_tips`) on 10-14..10-21, and 1 (`real_rate_10y_tips`) on 10-22: context only.
- Only days up to the copy were replayed; I did not refresh from DEV.

## Regression check (new vs old head, same inputs)

- Days where the new head is MORE severe than the old: **0** in A, C, D (equity); the monetary dial is **identical on all 7,542 replayed days** (A, C, D; 2,514 each).
- Equity days that are less severe: A 40, C 799, D 884. First divergence per episode is a count-driven candidate: 2000-02 curve pair; 2007-09 `real_rate_10y_tips + vix_level` (2007-08-17); Apr-2025 `cboe_skew + real_rate_10y_tips` (2025-01-02, seven weeks before the 2025-02-19 peak). 2022-09-28 is persistence only: old count-driven ALARM candidates on 9-20/22/23 had pre-loaded the counter; the new ALARM arrives 2 days later (09-30) on the same volatility master (.87-.89).
- Of 687 old candidate-ALARM days in config C, 568 (83%) had no eligible master at stress.

## What the removal costs, and what it does not

| | `5864e47` (as written) | `f290583` |
|---|---|---|
| Apr-2025, strict store as-is: ALARM / WATCH / CALM / UNKNOWN | 65.0 / 30.1 / 0 / 4.9 % | 26.2 / 35.0 / 34.0 / 4.9 % |
| Store, config C: ALARM in n of 8 episodes | 8 | 6 (none in 2000-02, 2007-09) |
| Store, config C: mean share of fall still ahead at first ALARM, primary (>=20%) / all 8 | 73 / 71 % | 36 / 47 % |
| Control 2006-26 (lower bound): ALARM days / false alarms per yr / declines caught | 26.3% / 0.94 / 7 of 7 | 17.3% / 0.64 / 7 of 7 |
| Control: mean share of fall ahead at first ALARM | n/m | 59 % |

- **The store's drop in protection is a coverage effect, not a defect.** In 2000-02 and 2007-09 the store only lets `curve_master` (WATCH-only) score; credit, volatility and NFCI do not (config C masters map: 2000-02 vol 0%, FCI 0%; 2007-09 vol 10%, credit 0%, FCI 0%). Under a masters-only rule those two episodes cannot ALARM from this store. The 73% last time was carried in those two episodes by the count (curve votes in 2000-02; TIPS + S&P 200-day + VIX with every master calm in Sep 2008).
- The control (continuous 1990-2026 S&P, VIX, VIX3M, curve, SKEW, TIPS) drives the PR's real resolver, lock and trend, and shows the masters-only configuration catching 7 of 7 declines, e.g. 2007 first ALARM 2007-08-10, 2020 on 2020-02-28, 2022 on 2022-01-27, 2025 on 2025-03-07. This is the evidence that detection is retained when the inputs exist. It lacks `hy_oas`, `ig_oas` and `copper_gold`, so the ALARM and false-alarm figures are lower bounds.
- The lock is unchanged by this PR and its cost is as before: control DENY 47.4% (38.0% with no lock), median re-entry 190 days / +38%, 2 premature re-opens, longest deny 718 days. It is carried by `curve_master` WATCH duration (F7, Trinity's follow-up).
- Lock behaviour on the store, config C: RECOVERY reached in 2015-16 (2015-11-02) and 2022 (2022-02-08, then relapse); 2007-09 no longer reaches ALARM so no lock. Config D (store as-is, no S&P history) never releases.

## Why still AMBER (unchanged limits, and one new one)

1. **ALARM now rests on the alarm-eligible masters scoring.** Where only the curve scores (the deep history in this store), the engine cannot ALARM. That is the designed demotion, but it means the store cannot show ALARM protection in 2000-02 or 2007-09, and there is no evidence for `credit_master` beyond one episode (Apr-2025, 99% scored, first ALARM 2025-03-10).
2. In-sample; no out-of-sample test.
3. The monetary dial is UNKNOWN on every store day and its ALARM->WATCH->CALM back door (ALARM x10, WATCH x5, CALM x5) is unvalidated. Not changed by this PR.
4. The store's backfilled payloads carry no `history` (S&P, WALCL, CPILFESL, gold, Philly): trend/lock and five indicators cannot be derived from it. Rogue's lane.
5. Control results are lower bounds. GBP/gilt unobservable. Epic 2 unexamined.
6. The published `count` still reads 2 on calm days (TIPS and SKEW are standing votes). Any consumer that reads `indicator_count` as stress will mislead; it is context only and should say so where it is displayed.

## Not touched

Nothing written on dell-debian or to the store. No push.

## Reproduce

Harness: `/srv/r2d2/tools/cerberus_replay/live/` (`launch_b.sh`, `analyse_b.py`, `d1d3_check_b.py`, `unknown_exit_test_b.py`, `today_replay_b2.py`, `control_sim6.py`). Outputs: `out/`. Run digests: `out/runs_b_sha256.txt`.
