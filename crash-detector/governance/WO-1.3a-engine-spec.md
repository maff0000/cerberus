# WO-1.3a engine spec (Trinity, PO) — translating DECISION-RULE.md into concrete formulas

This exists because DECISION-RULE.md §6/§10 deliberately leaves masters, thresholds and the
breadth/acute/count split as prose + "unset — calibration". Someone has to turn that into a
first, provisional, implementable design before any code gets written. That's a PO decision,
not an engineering one, so it's done here rather than left for whoever implements it to guess.

## 1. breadth, acute, count — what each one actually is

**`breadth`** is the EXISTING flat weighted-mean composite (`mapping.py`'s
`_banded_weighted_mean`, documented in `MATH.md`) over ALL ratified indicators for the dial,
UNCHANGED. It is not renamed and its calculation does not change in WO-1.3a. It is read out of
the existing per-dial evaluation exactly as it is today.

**`acute`** is a NEW, PARALLEL computation: `max` over a small, named set of **masters**. A
master is a named composite with its own provisional warning/stress/exit thresholds. The SAME
underlying indicator may feed both `breadth` (as one of many weighted inputs) and a master (as
a standalone signal) — that is not double-counting, it is the whole point: breadth captures the
average, a master captures whether any ONE extreme signal exists regardless of the average
(DECISION-RULE.md §6: "a master beyond stress fires ALARM on its own; no amount of calm
elsewhere can outvote it").

**`count`** is the number of CONTRIBUTING indicators (same set `breadth` is computed over)
whose scaled score is at/beyond `COUNT_THRESHOLD = 0.9` (provisional — meaning "essentially at
its stress band"). This is a plain count, not a derivation on any one indicator.

## 2. Masters v1 — level-only, provisional, each a `max` of its named components

Deliberately the simplest defensible version: every master below is the `max` of one or more
EXISTING indicators' already-scaled (0–1) scores — no new derivation kind, no new data source.
A richer version using explicit N-day/N-month CHANGE components (the way DECISION-RULE.md's own
prose describes "HY OAS level + 20-day change", "curve 6-month change") is a stated, deliberate
follow-up (WO-1.3a-ii or folded into WO-1.3b's calibration pass) — not attempted here, because
it needs a new `DerivationKind` and this round should prove the state machine works before that.

| Master | Dial | Components (indicator ids) | Combine |
|---|---|---|---|
| `credit_master` | equity | `hy_oas` | identity (one component) |
| `curve_master` | equity | `yield_curve_10y3m`, `yield_curve_10y2y` | max |
| `volatility_master` | equity | `vix_level`, `vix_term_structure` | max |
| `financial_conditions_master` | equity | `chicago_fed_nfci` | identity |
| `fiscal_master` | monetary | `fiscal_dominance` | identity |
| `real_rate_master` | monetary | `real_rate_10y_tips` (monetary polarity) | identity |
| `currency_master` | monetary | `broad_dollar` | identity |

`acute_equity = max(credit_master, curve_master, volatility_master, financial_conditions_master)`
`acute_monetary = max(fiscal_master, real_rate_master, currency_master)`

Each master's **warning/stress/exit thresholds** are provisional and, for v1, DERIVED from the
component indicator's own existing calm/stress band in `indicator-scaling.json` rather than
invented fresh: `warning = 0.6`, `stress = 0.85`, `exit = 0.5` (exit < entry — hysteresis,
per DECISION-RULE.md §6) on the already-0–1-scaled component score. These three numbers are
placeholders pending WO-1.3b's calibration, same disclosure as every other provisional number
in this repo — state this plainly in the code and in STATUS.md, do not present them as tuned.

A master with a missing/stale required component reads as that component already does
(MISSING/FEED_FAILING) and the master itself becomes `UNKNOWN` for this reading — it must NOT
read as 0 (calm). Propagates into state resolution per §3 below.

## 3. The five-state machine — exact precedence, matching DECISION-RULE.md §6

Per dial, per reading:

1. If ANY required master is `UNKNOWN` (a component missing/stale) → dial state is
   `UNKNOWN`. Stop; no other rule overrides this.
2. Else if ANY master's `acute` ≥ its `stress` threshold → `ALARM`. (Masters override breadth
   and count; breadth/count can never pull the state below what a firing master dictates.)
3. Else if `breadth ≥ B_high` AND `count ≥ k` → `ALARM`.
4. Else if (ANY master's `acute` ≥ its `warning` threshold) OR (`breadth` rising over the last
   20 readings AND `breadth ≥ B_mid`) → `WATCH`.
5. Else if the dial's PREVIOUS state was `ALARM` AND (every master's `acute` ≤ its `exit`
   threshold for `persistence` consecutive readings) AND (trend-confirmed: reference index
   above a flattening 200-day mean, OR a higher low on the acute statistic) → `RECOVERY`.
   **Both conditions required** (DECISION-RULE.md §6 — late by design).
6. Else → `CALM`.

**Second-leg rule**: if the dial's state was `RECOVERY` and rule 2 or 3 above fires again, the
new state is `ALARM` and the persistence/recovery clock resets to zero (DECISION-RULE.md §6).

**Persistence**: a state TRANSITION (not a reading) requires `persistence = 3` (provisional,
`DECISION-RULE.md` §10) consecutive readings satisfying the new state's own rule above. A
single reading reaching the threshold moves `persistence_counter` by one; it does not change
`state` until the counter reaches 3. Reverting mid-count resets the counter to zero — this is
NOT specified explicitly in DECISION-RULE.md and is Trinity's provisional interpretation,
flagged for R2D2 to confirm or challenge in WO-1.3b, not presented as settled doctrine.

`B_mid`, `B_high`, `k`, and each master's exact thresholds are ALL provisional (§10's own
"unset — calibration" rows) — v1 placeholder values: `B_mid = 0.35`, `B_high = 0.55`, `k = 3`.
State this as plainly provisional everywhere it appears in code/docs.

## 4. Scope for WO-1.3a's first implementation round

Build ONLY: the `State` enum (`CALM/WATCH/ALARM/RECOVERY/UNKNOWN`), the master definitions
table above as data (not yet wired to live indicator readings), and the breadth/acute/count
pure-function computation signatures — given a dial's already-scored indicator readings
(whatever `_evaluate_dial` or similar already produces today), compute breadth (reuse
existing), acute (new, per masters table), count (new). NO state-machine wiring yet, NO
persistence counting yet, NO output contract yet — those are later rounds, same discipline as
WO-1.14.

## 5. Addendum (Trinity, 2026-10-14) — architecture sign-off, after Rogue's round-1 investigation

**Approved: a parallel module (`engine/statistics.py` or `engine/masters.py`), not a new
`MappingKind` member.** `MappingKind`/`ScoreComputation` are sealed around "one magnitude per
dial" for a real incident's sake (ASR3-F02); a three-statistic member would either need
multiple `ModelSpec` rows per dial (structurally forbidden) or widen the sealed type. The
precedent is `derivations.py`'s own `DerivationKind` — a second closed enum added without
touching `MappingKind` when a genuinely new kind of computation was needed. Same shape here.
`mapping.py` is untouched; `breadth` stays byte-identical to today's `_banded_weighted_mean`.

**Approved: two separate per-dial master tables, no `check_no_blend.py` allowlist entry.**
`real_rate_10y_tips` scores 1.0 on equity and 0.0 on monetary from the same underlying value
(opposite polarity, both dials) — a shared "scaled score for indicator X" helper would be
exactly the cross-dial function that rule exists to catch. Keep the two tables separate and
stay out of the allowlist; that fixes the actual hazard rather than suppressing the lint.

**Flagged, not fixed, carried into WO-1.3b:** `count` (≥0.9 scaled) right now equals `k` only
because three indicators (`michigan_sentiment`, `real_rate_10y_tips`, `shiller_cape`) are
CLAMPED at exactly 1.0 on their provisional bands — saturated, not necessarily genuinely
acute (same root cause as `MATH.md` R-6). `count` as specified measures band-narrowness as
much as market stress. R2D2's WO-1.3b calibration pass should consider counting unclamped
distance-to-stress rather than clamped scaled score — recorded here as an open question for
that pass, not decided in this document.

## 6. Scope for round 2

Build the `State` enum, `MasterCombine` closed enum (`IDENTITY`, `MAX`) with its own
executor-branch set-equality assertion (mirroring `mapping.py`'s own pattern), the two
separate per-dial masters tables as frozen data, and the pure acute/count functions — each
taking one dial's `Contribution` tuple (already produced by `_banded_weighted_mean`, no new
scaling). Re-establish `mapping.py`'s three structural properties (no code, no state, cannot
span two dials) in the new module explicitly, since they are not inherited. NO state-machine
wiring yet (rules 1-6 of §3 above), no persistence counting, no output contract — those stay
later rounds.
