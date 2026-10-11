# WO-1.4 + WO-1.5 — GUI, live-dev loop, derived indicators: independent audit and reconciliation

Audit target: `23c10c0` (base `de4eef1`). Fresh Auditor, own worktree, real Chromium (Playwright, 1280x900) against the GUI run from the worktree on non-production ports.
**AUDIT_VERDICT: AMBER** (no RED). non_vacuity_established: yes for derivations (8 mutations each caught). Tests: 2165 passed (host pytest 8.3.4, invoked with `-c /dev/null` because pyproject pins minversion 9.0). gitleaks: clean.

## Margin question — ruled SOUND
Equity-stress margin loosened `+0.3` to `+0.2`. Stressed inputs saturate three tier-1 rows (weight 9). Total equity weight went 26 to 39 when the 6 derived indicators were added at calm: stressed score 9/26=0.346 to 9/39=0.231. The dilution arithmetic is exactly as claimed; the `approx(_expected(...))` assertion above it is unchanged. A broken engine ignoring hy_oas scores 0.154, ignoring all three 0.0: all fail `+0.2`.

## Findings and disposition
| # | Sev | Finding | Disposition |
|---|-----|---------|-------------|
| 1 | MED | STATUS.md still said derived indicators had no computing mapping | **Reconciled**: STATUS updated |
| 2 | MED | No WO-1.4/1.5 evidence in git | **Reconciled**: this file |
| 3 | LOW | pyproject `minversion=9.0` vs host pytest 8.3.4 | Carried (host env; image pins 9.0.2) |
| 4 | LOW | Hard-coded margin brittle | **Reconciled**: margin now `0.5 * 9 / total_weight`, derived from the scaling file and tiers |
| 5 | LOW | Derived-band placeholders unverifiable offline (shiller_cape 50/99 band scores a normal CAPE high) | Carried, disclosed: placeholders, no backtest |

## Not verified by the Auditor
Real collector loop and network fetches, Docker build/compose, healthz-503 fix in a container, 60s refresh, responsive layout. Container items are verified at redeploy (WO-1.6 Step 3).
