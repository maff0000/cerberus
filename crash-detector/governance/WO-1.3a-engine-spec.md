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
| `fiscal_master` | monetary | `monetisation_flag` (`fiscal_dominance` until the WO-1.19 rename; the id is RESERVED for the owed deficit/interest-burden measure, which is the indicator this master is named for and will take this slot when it is built) | identity |
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

## 7. The state machine's memory (Trinity, PO, 2026-10-14) — round 3 scope

Confirmed by investigation: `evaluate()` is genuinely stateless today — each call computes
fresh from current observations with no memory of a prior call. There is no existing
"previous state" or "reading history" concept anywhere in the engine. The state machine
(spec §3) needs real cross-reading memory (persistence counting, recovery tracking), so this
round has to design that storage, not just the transition logic.

**Design: a new append-only table, one row per dial per EVALUATION RUN** (not per raw
indicator observation — this is a NEW record distinct from `raw_reading`), holding at minimum:
`dial_id`, `as_of` (the evaluation's own timestamp), `state`, `persistence_counter`,
`acute_rising` (bool), and enough of the raw breadth/acute/count to re-derive persistence
checks without re-running the whole engine (store the computed values, not just the state
name — this is what "a reading is explainable a year later" already means elsewhere in this
codebase and should mean here too). Append-only, same discipline as `raw_reading`: a run's
result is a historical fact once written, never corrected in place (a bug fix produces a new,
later row with the right number, same philosophy as every observation in this product).

**Persistence, mechanically**: to check "the new state's rule has held for 3 consecutive
readings," look at the last `persistence - 1` rows plus the current one (4 rows checked, 3
transitions needed is actually "the rule held for this evaluation and the 2 before it" —
state this precisely in code, since "3 consecutive readings" is ambiguous between "3 past
rows" and "the current one plus 2 past" and the spec doesn't disambiguate; Trinity's call:
**the current evaluation plus the 2 most immediately preceding rows for this dial — 3 rows
total, all satisfying the same candidate-state's rule** — flag this interpretation plainly as
provisional/Trinity's-reading, same as the earlier persistence-reset interpretation already
flagged in the spec §3.

**RECOVERY's two conditions, checked the same way**: "every master's acute ≤ exit threshold
for `persistence` consecutive readings" reads the last 3 rows' stored acute/per-master detail;
"trend confirmed" (reference index above a flattening 200-day mean, or a higher low on the
acute statistic) is NOT yet backed by any wired indicator — `spx_vs_200dma` exists in the
mapping but as a SCALED SCORE, not as a raw "is it above/below and is the mean flattening"
boolean. **Scope cut for this round: build the state machine with a `trend_confirmed` INPUT
PARAMETER the caller supplies (not yet computed from real data)** — wiring that from
`spx_vs_200dma`'s raw series is its own follow-up, same discipline as deferring the
20-day/6-month CHANGE masters. Say so plainly in the code; do not fabricate a trend signal to
make RECOVERY "work" end-to-end this round.

**"Breadth rising over the last 20 readings" (WATCH trigger)**: the last 20 rows' stored
breadth values for this dial, strictly increasing is too strict (noisy data); Trinity's
provisional reading: **the current breadth exceeds the breadth from 20 evaluation-rows ago**
(a simple lookback comparison, not a monotonicity requirement) — flagged provisional, open to
R2D2 challenge in WO-1.3b like everything else numeric here.

**Scope for this round**: the new history table/record type, the persistence-counting
mechanism reading it, and the six-rule precedence function (spec §3) wired to real stored
history — EXCLUDING the trend-confirmation computation (parameter, not yet derived) and
EXCLUDING the output contract (§7's full YAML schema — that's the round after this one).

## 8. PO sign-off on round-3 investigation (Trinity, 2026-10-14)

Confirmed and approved, all three of Rogue's findings:

1. **A new store, own module outside `src/`, own SQLite file** — not a fourth table in
   `SqliteStore`, not a reuse of `db/migrations/0004_dial_history.sql` (that migration's
   `state` column is the EXISTING `Reading` sum type — `VALUE|DEGRADED|UNKNOWN` — a different
   concept from the new `CALM|WATCH|ALARM|RECOVERY|UNKNOWN` machine. Genuinely new table,
   genuinely new name — `machine_state`, not `state`; not named `dial_history`. If the
   Postgres side ever needs this, it is a future migration (0008+), out of this WO's scope.
2. **The real blocking decision, resolved**: a new `cd-live-evaluator` service, no egress,
   running on the collector's existing 300s cadence — read-only handle on `ingestion/store.py`'s
   raw store, write handle on the new history store. This is what "a reading" means from
   here on: one evaluator pass, not one HTTP request. The GUI continues to compute nothing new
   from this WO's work — it already reads `evaluate()` fresh per request for the EXISTING
   breadth/Value/Degraded/Unknown reading (untouched), and will read the NEW machine-state
   history the same read-only way once it exists. Folding evaluation into `collector_loop.py`
   (the only container with outbound internet) is explicitly REFUSED — it would put new
   evaluation logic in the one container that can reach the net, for no real saving.
3. **The CD-RT-001 defense** (UNKNOWN rows carry no breadth/acute/count numbers, enforced in
   the new table's own CHECK constraints, not just in the Python) — adopted, same discipline
   as `dial.history`'s own `dial_history_state_fields_coherent`.

## 9. Scope for round 4 — logic and storage only, no deployment yet

Build, in order:
1. The new history store (own module/file, append-only, idempotent schema-on-write-open,
   `machine_state` CHECK built from `State` the same way WO-1.14's `_as_sql_literals` pattern
   built `_VINTAGE_COLUMN` from `VINTAGE_LABELS` — reuse that exact technique, don't reinvent
   it) and the six-rule precedence function (pure, in `engine/statistics.py`, per Rogue's own
   recommendation — it belongs beside `State`/`MasterCombine`, not in the new store module).
2. A plain Python "evaluator pass" function: read current raw contributions + the dial's
   recent machine-state history, compute via `engine/statistics.py`'s functions, apply the
   six-rule precedence, write one new history row. Testable in isolation, no container, no
   compose, no Dockerfile — those are explicitly a LATER round (deployment), once the logic
   is proven.

## 10. PO sign-off on deployment investigation (Trinity, 2026-10-14)

Approved, all four of Rogue's findings, plus the naming correction (two compose
stacks, design vs live-dev — this WO deploys into `deploy/live-dev/compose.yaml`,
the one actually running, not the undeployed seven-service design).

1. **`network_mode: none` for `cd-live-evaluator`**, not a reused/invented
   `x-egress` declaration. Measured, kernel-enforced, and the evaluator genuinely
   needs no network (SQLite-only). Declaring a policy nothing in the live stack
   reads would be theatre; this is real.
2. **Mount `cd-live-data` rw, keep `read_only=True` at the Python/SqliteStore
   level**, matching `cd-live-gui`'s own existing precedent exactly, with the WAL
   `-shm`/`-wal` sidecar-transience finding written down as the reason, not
   implied. A genuine `:ro` mount was measured to fail intermittently against a
   WAL database whose sidecars are created/destroyed per connection — this is not
   a concession, it is the only mount that actually works against this file.
3. **A new `cd-live-state` volume**, rw, exclusive to the evaluator — neither
   existing service touches it.
4. **`--no-deps` is mandatory** on the actual `docker compose up` that deploys
   this, and **`CD_GUI_BIND=192.168.11.10` must be set explicitly** on any compose
   invocation touching this stack (the running GUI does NOT use the file's
   documented `127.0.0.1` default) — both named here so the deploy round does not
   rediscover them by recreating the collector or relocating the GUI.

**Flagged separately, not this WO's to fix**: `cd-live-gui`'s Docker-level mount
of `cd-live-data` has always been read-write; its "read-only" guarantee has only
ever existed at the Python/SQLite level (`read_only=True`), never enforced by the
container itself. Pre-existing, not introduced by WO-1.3a. Worth Helm's awareness.

## 11. Scope for the deployment round

Write the Dockerfile addition (reuse the existing `cd-live-dev` image — the
evaluator needs no new dependencies beyond what's already installed), a new
`evaluator_loop.py` mirroring `collector_loop.py`'s exact pattern (plain
`threading.Event`-based loop, `CD_EVALUATE_INTERVAL_SECONDS` default 300, SIGTERM
between passes not mid-pass), and the new `cd-live-evaluator` compose service
entry: `network_mode: none`, the two volumes as decided above, `--no-deps`
documented in the deploy instructions this round writes down for whoever actually
runs it live. Verify the per-service config-hash stability claim Rogue already
measured (adding the service must not change `cd-live-collector`'s or
`cd-live-gui`'s own hashes) as an actual check, not just a repeated assertion.

## 12. Output contract scope (Trinity, PO, 2026-10-14) — DECISION-RULE.md §7

Building the contract now, against what the state machine actually computes today. Two
real gaps, decided here rather than guessed at implementation time:

**`sizing_multiplier` — OUT OF SCOPE for this round, and NOT emitted as a plain 0.0.**
§7 says it is "non-zero only in CALM and RECOVERY" and derives from valuation inputs (CAPE,
Buffett substitute, gold extension) that no code anywhere computes. Emitting `0.0` as a
placeholder in CALM/RECOVERY would be actively misleading — it reads as "the detector
recommends sizing to zero," the opposite of the untouched-advisory truth. The contract this
round therefore carries `sizing_multiplier: null` together with a sibling
`sizing_not_computed: true`, and the schema/identity block states the `decision_rule_version`
this contract implements does not yet include real sizing. Building the valuation logic is
its own work order (WO-1.3c, not started), not a guess folded into this one.

**`coverage_bracket.dial_value_min`/`dial_value_max` — build `scored_weight_fraction` for
real this round (a known, well-understood gap, MATH.md R-10); the min/max re-score (breadth
recomputed with every missing input imputed at 0, then at 1) is a genuinely new engine
computation, not yet built anywhere.** If time in this round allows, build it; if not, it is
`null` with the same `not_computed` disclosure pattern as sizing, and gets its own follow-up
rather than blocking the rest of the contract.

**`dial` enum: `equity_crash` | `monetary_debasement` only.** No `monetary_debasement_gbp`/
`_usd` split — the GBP dial doesn't exist (tracked separately, not fabricated here).

**`identity` block, all real and buildable now:** `build_sha` from `CD_BUILD_SHA` (already
wired into the image's env); `scaling_version`/`mapping_version` as a hash of
`indicator-scaling.json`/`indicator_mapping.yaml` (same technique already used for other
content-addressed identity elsewhere in this repo — find and reuse it, don't invent a new
hashing convention); `decision_rule_version` hardcoded to `DECISION-RULE.md`'s own stated
version (currently v1, with the `sizing_not_computed`/`coverage_bracket` caveats noted
alongside it).

## 13. Scope for this round

Build the contract-assembly function: given a `MachineStateRow` (already written) plus the
identity inputs above, produce the §7 shape as a plain dict (serializing to YAML/JSON is the
caller's choice — build the dict first, matching the schema's field names exactly). This is
a pure, testable function, same discipline as everything else in this WO — no new engine
computation beyond `scored_weight_fraction` if time allows, no serving/HTTP endpoint yet
(that's a later round, once the contract shape itself is settled and tested).

## 14. PO sign-off on the output contract (Trinity, 2026-10-14)

Approved `evaluator/contract.py`, the `state_since` query, and `scored_coverage` without
reservation. Two things specifically called out as excellent beyond what was asked:

1. **`dial_value_min`/`dial_value_max` built, not deferred** — the closed-form derivation
   (`min = breadth · f`, `max = breadth · f + (1 − f)`) is a real algebraic identity of the
   re-score, needs no per-indicator detail, and closes a gap spec §12 explicitly allowed to
   be left open. Correct, and verified in this round's own test against a long-form re-score.
2. **The `inputs` gap reported, not papered over.** `master_scores` is keyed by MASTER id, not
   indicator id, and publishing it under `inputs` would mislabel it; nothing stored today
   carries per-input age. Correctly refused a plausible-but-wrong shape in the one field
   Epic 2 reads verbatim. **Ruling: `inputs: null` + `inputs_not_computed: true` stands as
   built.** Filling it for real is its own follow-up (WO-1.3d) — it needs either a new
   `MachineStateRow` column carrying the engine's `Contribution` detail, or a second read of
   the raw store's `raw_observation` ages at contract-assembly time, and that is a real
   data-shape decision, not a guess for this round to make.

**The `as_of`/"newest input" question, answered.** `DECISION-RULE.md` §7's own prose is
wrong, not the code: the engine has always dated a reading by its OLDEST input (`_oldest_as_of`,
"a reading is only as fresh as its oldest input"), which is the conservative choice and the
one every freshness/staleness decision in this product already depends on. Publishing the
newest input's timestamp instead would make a reading LOOK fresher than its stalest
contributor — the exact opposite of "missing or stale data must never render as calm."
**Ruling: publish the oldest-input `as_of`, unchanged, as built.** `DECISION-RULE.md` §7's
own comment should read "oldest" rather than "newest" — recorded here as a wording
correction owed to that document, not a behaviour question, and raised with Matt/the
architect separately rather than edited into their document unilaterally from this seat.
