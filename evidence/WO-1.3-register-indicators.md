# WO-1.3 — Register indicators: independent audit and reconciliation

Audit target: `c9f6af3` (base `59a48f4`). Fresh FORGE Auditor, own worktree, tests re-run (2143 passed), mutation-tested.
**AUDIT_VERDICT: AMBER** (no RED). non_vacuity_established: yes for the main doctrine controls. Browser gate n/a (no surface).

## Judgement calls — both ruled SOUND
- **Required inputs** (equity: hy_oas, yield_curve_10y3m, yield_curve_10y2y; monetary: broad_dollar, breakeven_5y): the rationale is factually true — the monetary-only tier-1 rows (gold_real_rate_cross, fiscal_dominance) are PENDING; every live tier-1 row is equity. Removing any required input gives Unknown naming it, on that dial only.
- **`deploy/indicator-mapping.json` left empty**: the pinned tests are unmodified; wiring builds from the ratified YAML and never reads the json; no path loads the empty json into a calm dial.

## Findings and disposition
| # | Sev | Finding | Disposition |
|---|-----|---------|-------------|
| F1 | AMBER-high | 13 pending indicators are not in the dial specs, so a dial from 17 of 30 reads as a full `Value` (monetary carries ~52% of nominal weight) | **Reconciled for consumers**: `ingestion.wiring.coverage()` reports wired/nominal weight and the pending ids per dial (tested). **Carried**: registering the 13 as `WiringState.PENDING` in the registry so `pending_source_ids()` is non-empty and the dial is `Degraded` — an engine change, owed to a later WO. |
| F2 | AMBER | No plausibility gate: hy_oas=-1e9 clamps to calm, 1e308 to stress | **Carried, Owner input needed**: a declared plausible range per band. Not invented here. |
| F3 | AMBER | Non-finite guards and `RelevanceWindow.covers` boundary covered only by a site-count pin | **Reconciled**: tests for the inclusive boundary, future/NaN/inf ages, the 120-day ceiling and ceiling+1, and non-finite/bool/str/None stored values yielding no observation. |
| F4 | LOW | A non-finite payload passed straight to `evaluate` raises (fail-closed, not calm) | Accepted; the wired path filters first (tested). |
| F5 | LOW | `deploy/indicator-mapping.json` comment and `empty_config_snapshot` docstring still say the mapping "cannot be read (Q30)" | **Carried** (cosmetic; the file is pinned by tests). |
| F6 | info | Nothing in production calls `build_wiring` yet | Addressed by WO-1.4 (the GUI is the first caller). |

Tests after reconciliation: 2151 passed (Python 3.12.3 host, not the pinned 3.11; PyYAML/jsonschema only).
