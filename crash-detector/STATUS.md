# Crash Detector — Recovery Status

**Read this first.** This is the cold-start orientation for `crash-detector/`: what the thing is, what was actually built, exactly where the build stopped, and what it would take to finish and deploy it. It was written at import time (CERBERUS WO-1.2, 2026-10-10) from the archived records themselves, not from memory, and it corrects at least one claim made about the build before the import (see §3).

Everything under `crash-detector/` is the recovered repository (history preserved, see §8), **modified only by an email/identity scrub** (see `RECOVERY-ERRATA.md`). This file, `ARCHIVE-COMMIT-MAP.txt` and `RECOVERY-ERRATA.md` are the only additions.

---

## 1. What it is

An **advisory-only** market-stress instrument. It tells the Owner, early and honestly, when the conditions for an **equity crash** or a **monetary debasement** are building, so that a decision made in calm can be executed mechanically under stress. It detects, scores, explains, alerts and publishes machine-readable state. It never executes anything; its output is evidence and input, never authority.

It was built as a **standalone container set** because its ARGUS-coupled predecessor died twice on ARGUS internals. In CERBERUS it is **Epic 1** and replaces that legacy engine (retired in WO-1.1).

The authoritative documents (read in this order):

| File | What it is |
|---|---|
| `crash-detector/PID.md` (v1.1.1) | Product Intent. §1 purpose and §3 doctrine are **CONSTITUTIONAL** (Owner only). §6 holds the 17 acceptance criteria `CD-AC-001..017`. |
| `crash-detector/BLUEPRINT.md` | How it is built: containers, store, collectors, dial engine, publication, risks (§17), delivery order (§15). |
| `crash-detector/governance/mapping/indicator_mapping.yaml` | The Owner-ratified indicator mapping (30 rows). Data the engine registers. |
| `crash-detector/governance/decisions/PO-DECISIONS-*.md` | 32 numbered Product Owner rulings; the real decision history. |

> Note on naming: `crash-detector/PID.md` is the **crash detector's own** PID. The CERBERUS-level `PID.md` at the repo root governs the whole programme; Epic 1 there is this component. They do not conflict, but the root one wins on scope.

## 2. The design in one page

**Two dials, never blended.** Equity-crash and monetary/debasement stress fail in opposite directions; averaging them cancels the signal. No code path may combine them (`CD-AC-002`, enforced structurally and by a planted violation).

**Doctrine (PID §3, constitutional):**
1. Two dials, never blended.
2. **Missing or stale data must never render as calm.** Absence of signal is not absence of risk.
3. The AI review has **zero authority** over headline numbers (two questions only: what changed, is the plan still fit).
4. External sources are **witnesses, never ingredients** (OFR FSI and a Quantical composite, shown side by side; divergence is the alarm).
5. **Hard public/private split**: the market read goes outward; anything touching the book stays private, in a different container.
6. **No unexplained mappings**: no score-to-probability curve we cannot account for.

**Indicators.** The ratified mapping file has **30 rows**: 19 equity-only, 7 monetary-only, 4 scored into *both* dials, each with its own polarity. (The CERBERUS README/PID say "~24"; the file says 30. The discrepancy is unresolved and is for the Owner/Architect to settle.) Tiers carry provisional weights ×3/×2/×1. **Weights are provisional pending backtest.** Each indicator has its own relevance window (a quarterly survey is not "dead" at 16 minutes), which is a *different* quantity from the 15-minute publication-liveness budget.

**Container set** (`deploy/`): `cd-collectors`, `cd-engine`, `cd-witness`, `cd-review`, `cd-private`, `cd-public`, plus a store (`cd-store`, Postgres) on two networks (private / public). Authority class C, advisory; DEV on the Linux build host first, an independent assurance party ratifies, only then PROD on cloud.

## 3. Where the build actually stopped

**Correction to the pre-import brief.** CERBERUS's README and the WO-1.2 dispatch describe the build as having "reached WO-2R increment 2b". The archived records show it went **considerably further**: past WO-2, WO-2R, WO-2R2 and WO-2R3, and into **WO-3 increment 16G**. The WO-2R-2b description matches an early point in the rework, not the end.

### Timeline (from `governance/assurance/` and `governance/engineering/build-log/`)

| Date (2026) | Event |
|---|---|
| 08-18 | PID v1.0 ratified by the Owner. First commit. |
| 08-19 | **WO-2 gate: Assurance returns AMBER** (`CD-ASR-WO2-01`); four of five criteria not PASS. Product Owner gate review (`PO-GATE-REVIEW-WO2-0001`) **reopens** the gate: refusal to admit the run record is commended; a project rule is set (an Assurance not-PASS cannot be computed to PASS); rework **WO-2R** ordered to "close the CLASS, not the instances" (blend, absence-yields-a-number, IP-literal egress, hard staleness bound…); commit identities to be re-authored per seat. The pre-rework state is preserved under the archive tag `wo-2-pre-identity-rework`. |
| 08-19 to 08-20 | **WO-2R → RED**, then **WO-2R2 → RED** ("the WO-2 gate is not met, for the third time"). Each verdict is in `governance/assurance/WO-2R*/`. |
| 08-20 to 08-23 | **WO-2R3**: several independent Assurance seats, mostly RED (fifth, sixth, seventh), ending **AMBER at the tenth seat**. Product Owner ruled the perimeter into **three tiers** — PREVENTED / RESISTED / DETECTED — after the eighth seat proved the earlier two-tier claim false (BLUEPRINT v0.4.0, risk `CD-BP-005`). This produced new criterion `CD-AC-017` (PID v1.1.0) and the `CD-AC-018` relation. |
| 08-23 to 08-25 | **WO-3** (publication layer, heartbeat, staleness, health surface, construction-provenance admission). Increment 14 **PASS (scoped)**; increment 15 **AMBER (scoped)**; increments 16A–16F were audited seat by seat. |
| 08-24 | Increment **16F** (control-row strength) graded **RED** at `7ac11c9` after nine rounds (`BL-…-A314`): "the product is sound and the completion condition is not met". |
| 08-25 | `PO-DECISIONS-0032` — **Q41 disposed** (Owner: accept-and-release). The 16F guard is accepted with a **declared** scope; the residual "an in-process insider deliberately weakening the publication code" is explicitly *not gate-preventable* and is assigned to assurance/detection, **not a product blocker**. Four bounded increments authorised. |
| 08-25 (last record) | **Increment 16G** ("true-regardless" fixes) returned `READY_FOR_ASSURANCE` (original SHAs content `0cf8411`, entry tip `90c3dc3`; see commit map). Banked as an *input*, **not accepted**. A fresh Assurance seat (not the one that raised the findings — `PBG-SOD-001`) was to grade it; dispatch `CD-D-187` was issued. **No verdict on 16G exists in the archive.** Build log tail: `BL-20260825T063803Z-0190`. |
| 08-29 | The governing framework (PBGv2) is retired; the repo is orphaned in an archive with no remote. |

**So the honest position is:** WO-1 and WO-2 (with rework) are done to the extent an adversarial assurance process would let them be; WO-3 is **mid-flight at increment 16G, awaiting its independent grading**; WO-4, WO-5 and WO-6 have **not started**.

## 4. What is real vs. what is scaffolded

Measured at import: **2,099 tests pass** (`PYTHONPATH=src python3 -m pytest tests`, CPython 3.11, run on a clean `git archive` of the merged tree). After WO-1.2b (2026-10-11): **2,129 pass** (`python3 -m pytest`, 30 new in `tests/test_ingestion.py`). Roughly 17k lines in 45 modules under `src/crash_detector/`.

### Implemented and tested
- **Dial types** (`dials/`): `Reading` sum type where absence (`Unknown`) is structurally incapable of yielding a number; scores; provenance. The two dials cannot be combined into one scalar.
- **Admission** (`admission.py`, `establishment.py`): exact-type admission "doors" and construction-provenance admission (`CD-AC-017`).
- **Collector framework** (`collectors/`): runner, validation, delay, adapter *boundary* and attempt records. See "scaffolded" below: there are no real source adapters.
- **Source registry & config** (`source_registry.py`, `engine/config.py`): sources as data, with pending sources shown as PENDING, never as a false green.
- **Engine** (`engine/`): the model is *data*; the engine owns the model lifecycle (BP-AMENDMENT-0001); evaluation and mapping.
- **Staleness** (`staleness.py`, `regime.py`): regime-aware windows that tighten in high vol; hard upper bound.
- **Publication layer** (`publication/`): envelope contracts (public/private JSON schemas in `contracts/`), classification, `refuse_unless_publishable`, cadence-breach detection, alerting, detail-level (calm/elevated/acute).
- **Witness panel** (`witness/`, `serving/witness_resolver.py`): `WITNESS UNAVAILABLE` ≠ `WITNESS AGREES`.
- **Health surface & runtime lifecycle** (`health.py`, `runtime/`).
- **Store** (`store/`, `db/`): migrations 0001–0007 and a grant matrix (role separation).
- **Assurance machinery**: Required Test Register (`required-tests.yaml`), planted-violation suites (`plants/`), variant suites (`variants/`), probes and sweeps (`tools/`). These are unusually extensive; the project was built *to be audited*.

### Scaffolded or not built
- **Real data collection: PARTIAL (WO-1.2b), outside the application tree.** `src/crash_detector` still opens no sockets (a test asserts it). The network-bearing adapters live in `crash-detector/ingestion/` and drive the core's own `collect()`. 25 of 30 indicators have a wired public feed; 5 do not (see §4a). Nothing is scheduled: ingestion runs only when invoked, and writes to a SQLite DEV store, not the Postgres `cd-store`.
- **Indicator rows are not yet registered in the engine**, so **the dials have never produced a real number.** (Raw readings now exist in the ingestion store; nothing consumes them yet.) That was the next step after 16G ("register the indicator rows from the mapping… first real numbers", PO-DECISIONS-0032 §4). Also owed first: detector-side `feed_liveness` marking from a real dead-feed detector.
- **Weights are provisional**; no backtest has been run. Nothing is calibrated.
- **Containers are written, not built.** The six Dockerfiles, `compose.yaml` and entrypoints exist and are checked for portability (no host-specific addresses), but each entrypoint is a 20-line shim and the images were explicitly never built (`CONTAINER_BUILD_NOT_YET_AUTHORISED`).
- **No public page / presentation layer** (WO-4). `serving/dial_presentation.py` exists; the actual page does not.
- **AI review** (`cd-review`, four validators) — WO-5, not implemented.
- **Rotation-readiness ratio, wave-transition monitor, recovery-from-backup proof** (`CD-AC-013/015/016`) — WO-6, not implemented.
- **Witness live feeds and divergence history/slope** (`CD-AC-004`, `010`, `011`) — WO-4.
- **No deployment of any kind.** Never run against live data, never on PROD.

### 4a. Ingestion state (WO-1.2b, verified live 2026-10-11)

`ingestion/` fetches and records. It computes nothing: no ratio, spread, percentile or score (collector-never-computes, BLUEPRINT §5). Sources are exactly the feeds the Owner-ratified mapping declares, reached by the nearest keyless public endpoint: FRED `fredgraph.csv`, Cboe daily-history CSVs, Yahoo chart, multpl Shiller table. Egress is the four hosts in `deploy/egress-destinations.yaml`, for `cd-collectors` only.

A live run on 2026-10-11 fetched **27 of 27 sources OK**. (As of WO-1.6 a live run fetches 31 of 32 OK; the one failure is `lbma.gold_fix_usd`, HTTP 403, see the addendum below.) Of the 30 ratified indicators:

| State | n | Indicators |
|---|---|---|
| **LIVE** (the source's own number, inside its staleness window) | 17 | hy_oas, ig_oas, yield_curve_10y3m, yield_curve_10y2y, real_rate_10y_tips, breakeven_5y, fed_funds_rate, jobless_claims_4w, chicago_fed_nfci, broad_dollar, sahm_rule, michigan_sentiment, m2_yoy, cpi_yoy, core_pce_yoy, vix_level, cboe_skew |
| **DERIVED** (every input fetched; the *engine* must derive the number, and has no computing mapping yet, so there is no number of its own) | 7 | credit_stress_hyg_lqd, breadth_rsp_spy, vix_term_structure, spx_vs_200dma, copper_gold, gold_real_rate_cross, shiller_cape |
| **PARTIAL** | 1 | sloos_bank_lending: the automatic C&I leg (FRED DRTSCILM) is live; the manual NDFI leg (SLOOS Table 2 Q14) has no feed, so it must not read complete |
| **NOT_TRACTABLE** (no substitute wired; a substitute is a provenance decision) | 5 | buffett_indicator (Wilshire/GDP: FRED withdrew WILL5000PRFC, no free market-cap series), ism_manufacturing (licensed; FRED withdrew NAPM), gold_spot (no keyless public spot source; GC=F is futures, not spot), private_credit_stress (composite weighting and BDC universe undefined), fiscal_dominance (discriminator rule not in the mapping) |

> **WO-1.6 addendum (2026-10-11, supersedes the NOT_TRACTABLE row above for three indicators).**  `buffett_indicator` (FRED NCBEILQ027S / GDP, 255.05 % on 2026-10-11) and `fiscal_dominance` (FRED WALCL + core CPI conjunction) are now **LIVE as disclosed SUBSTITUTE feeds**; the fiscal_dominance substitute still awaits Owner acceptance. `gold_spot` is **wired to the LBMA fix but FEED_FAILING**: prices.lbma.org.uk answers HTTP 403 (Cloudflare) from the build host for every User-Agent tried, so it delivers no reading and degrades the monetary dial honestly until an accessible source exists. `copper_gold` monetary binding is HELD (polarity contradiction in the mapping); `gold_real_rate_cross` is BLOCKED (divergence undefined).

> **WO-1.7 addendum (2026-10-12, supersedes the BLOCKED / NOT_TRACTABLE / PARTIAL rows above for three indicators).** All three are wired as **PROVISIONAL, uncalibrated, not-Owner-ratified** constructions (see `SUBSTITUTED_FEEDS`). `gold_real_rate_cross` = percentile of the latest 60-day gold-return vs DFII10-change Pearson correlation within its own ~10y history; it is **relative, not absolute** (stationary all-negative regimes still read 0-100, ~10% false-stress rate), and because gold is the LBMA fix it is **FEED_FAILING (HTTP 403) and dark in production**, with no futures fallback. `ism_manufacturing` is a **substitute**: z-composite of three regional Fed surveys, not a PMI (band calm 0 / stress -1.5, provisional). `sloos_bank_lending` = plain **mean of the C&I leg (DRTSCILM) and the hand-entered NDFI leg**, dated by the older leg; MISSING ("AWAITING MANUAL ENTRY") until a value is entered via `ingestion/manual.py` (preview by default, `--confirm` to record, append-only, duplicate dates refused), STALE after 120 days. The mean-of-legs choice is a Trinity decision awaiting Owner acceptance. Live counts moved with this WO (test_gui 26/4 -> 29/1); `private_credit_stress` remains unwired until WO-1.8.

> **WO-1.9 addendum (2026-10-12): daily staleness windows recalibrated.** Symptom: the equity_crash dial read NO READING because `hy_oas` (REQUIRED) was 4.5 days old (FRED's last print 2026-10-08; Fri 10-09 not yet published, Mon 10-12 a federal holiday) against a 4-day (345,600 s) window. **Cause:** 4 days cannot survive an ordinary weekend with a publish lag. Age is measured from the observation date at 00:00 UTC (`as_of_for`, rule `obs_date`).
>
> **Realistic worst case, worked out, not guessed.** *FRED business-day series (1-business-day publish lag):* last print Thu (00:00 UTC), Fri holiday, Sat, Sun, Mon holiday, next observation Tue, published Wed; the newest available print is up to **6 d 23 h 59 m** old just before it lands. Even a plain Friday print with a Monday holiday is 4.5 d by Monday noon and ~5 d by Tuesday. *Market-day series (ETF / index / futures, dated the trading day itself):* same stretch, but Tuesday's close is available Tuesday evening, so the worst case is **5 d 23 h 59 m**. `tests/test_wo19.py::_worst_gap_seconds` computes both over a two-year calendar rather than asserting them.
>
> **New windows.** FRED business-day rows (`hy_oas`, `ig_oas`, `yield_curve_10y3m`, `yield_curve_10y2y`, `real_rate_10y_tips`, `breakeven_5y`): **8 days (691,200 s)** = 7-day worst case + 1 day grace (one missed or late FRED publication / poll). Market-day rows (`credit_stress_hyg_lqd`, `breadth_rsp_spy`, `cboe_skew`, `vix_term_structure`, `vix_level`, `spx_vs_200dma`, `copper_gold`, `gold_spot`, and the `private_credit_stress` override): **7 days (604,800 s)** = ~6-day worst case + 1 day grace. `fed_funds_rate` (DFF prints every calendar day) already had 7 days and is unchanged. Still tighter than every weekly row (14 d) and far below the monthly ones, so a dead feed is still caught within a week. **Not changed:** the required/contributing classification (equity required = `hy_oas`, `yield_curve_10y2y`, `yield_curve_10y3m`; monetary = `breakeven_5y`, `broad_dollar`); that one stale required input can still blank a whole dial is a separate design question, flagged for Owner discussion and pinned by a test so it cannot change quietly.
>
> Also folded in (uncommitted Auditor-dispatch residue from WO-1.7, reviewed): stricter ISO date validation and a 1990 floor in `ingestion/manual.py`, `allow_abbrev=False` (so `--conf` cannot silently mean `--confirm`), unreadable-DB refusals instead of tracebacks, a preview that refuses a date `--confirm` would refuse (corrected: a not-yet-created store is valid for a preview), degenerate old correlation windows skipped in `gold_real_rate_cross`, `sloos_bank_lending` added to `SUBSTITUTED_FEEDS`, with tests.

> **WO-1.12 addendum (2026-10-13, supersedes the FEED_FAILING state of `gold_spot` in the WO-1.6 and WO-1.7 addenda above).** `gold_spot` moves **FEED_FAILING → LIVE (pending redeploy — not yet built/deployed)**. The LBMA gold-fix endpoint, which answered **HTTP 403** to this host and delivered no reading at all from WO-1.6 to WO-1.12, is replaced by **HERMES' published XAU/USD H4 candle close** (new source id `hermes.xau_usd.h4_close`, instrument `XAU_USD`, timeframe `H4`).
>
> **THIS IS A SOURCE CHANGE, NOT A FEED SUBSTITUTION.** The ratified feed is still `market:XAUUSD` with provenance `spot`, and HERMES publishes live OANDA XAU/USD, which **is** spot gold — not a futures contract and not a fix. So `gold_spot` is not added to `SUBSTITUTED_FEEDS`.
>
> **DISCLOSED MATURITY CAVEAT, stated rather than smoothed over.** HERMES is a **separate system in another seat's domain** and its publishing service is labelled **`NON_PROMOTED_ENGINEERING_CANDIDATE` with `ENVIRONMENT=DEV` and `RUN_ENV=STAGING`** — it is **NOT a promoted production service**. Its **price data is nevertheless real**: it runs `OANDA_ENVIRONMENT=live`, so these are live OANDA quotes and not a demo feed. Matt accepted that maturity caveat explicitly ("good enough, will be maintained").
>
> **DISCLOSED COARSENING.** The figure is the close of the **FIRST H4 candle HERMES publishes each UTC day** — a defined, reproducible once-a-day reference in the same spirit as the LBMA daily fix it replaces, **NOT an intraday tick**. H4 is used because it fits the row's daily cadence: M1/M5/M15/H1 are far more granular than a daily indicator can use, and HERMES' D1 timeframe is not active. An absent key is the publisher saying it has nothing (its own TTL is 4 h), which reads MISSING downstream and never calm.
>
> **TRANSPORT AND WHAT THAT LEAVES OWED.** A read-only Redis `GET` of one key (`hermes:candles:XAU_USD:H4:latest:v1`) on a **LAN peer**, so it is declared in `ingestion.catalog.NON_HTTP_PEERS` and **not** in `deploy/egress-destinations.yaml` — that registry admits only DNS hostnames of two or more labels and refuses an address literal by design (CD-ASR-F04), and the HERMES peer has no hostname; the reason is recorded at the declaration. **This project runs no Redis and registers no service**: it is a read-only *consumer* of another system's publication, BLUEPRINT §2 still declares no Redis service and **Q31 remains open**. The designed six-service stack (`deploy/compose.yaml`) is unchanged and its `cd-collectors` allowlist still names only the five public data hosts; a declaration shape that can express a LAN peer is **owed** and is a Product Owner / architecture decision.
>
> **NOW BUILT AND DEPLOYED, AND VERIFIED LIVE (2026-10-13T10:44Z).** `gold_spot` reads **LIVE at 4186.57 `usd_per_oz`**, as-of `2026-10-13T00:00:00Z`, age 0.45 d — the close of HERMES' `2026-10-13T06:00:00Z` H4 candle (`freshness_state: FRESH`, `status: OK`, `source: oanda`, derived H4-from-H1 with `source_coverage: 1.0`). Indicator counts moved **LIVE 28 → 29, FEED_FAILING 2 → 1**. `monetary_debasement` moved **0.14026446 → 0.21383849**, and `gold_spot` left its `missing_inputs` (which now holds `gold_real_rate_cross` alone). `equity_crash` is **unchanged at 0.34050898**, as expected: `gold_spot` serves `monetary_debasement` only. Both dials remain **DEGRADED** — this closes one missing input, not the dials.
>
> **HOW IT WAS INSTALLED, AND THE PRE-EXISTING LOCKFILE GAP THAT IS NOT FIXED HERE.** `requirements.lock` is the *designed* install path (PBG-CI-003, hash-verified) but **it is not what `deploy/live-dev/Dockerfile` actually installs from**: that image has always carried an ad hoc `RUN pip install --no-cache-dir PyYAML==6.0.2 jsonschema==4.10.3`, bypassing the lock. **`redis==5.0.1` was added to that same ad hoc line and therefore joins PyYAML and jsonschema in that gap** — explicitly pinned, but **not hash-verified and not from the lock**. This is a **pre-existing inconsistency that WO-1.12 neither introduces nor repairs**; redis is still absent from `requirements.lock`, so a container built from the lock still would not have it. Fixing the lock pipeline is **out of this WO's scope and remains owed**.
>
> **CORRECTION TO THE `async-timeout` CLAIM ABOVE.** Earlier WO-1.12 notes said the lock entry needs digests for redis **and** `async-timeout`. That is true **of the DEV host** (CPython 3.11.2) but **not of this container**: the live-dev base image is **CPython 3.12.14** (`python@sha256:2f17fc04…`, `python:3.12.14-slim-trixie`), and redis 5.0.1 declares `async-timeout >=4.0.2 ; python_full_version <= "3.11.2"`, so the marker is **false** in the image. `async-timeout` was therefore **deliberately not installed**, and its absence was verified in the built image. The container is not the host.
>
> **BOTH SERVICES NEEDED IT, NOT JUST THE COLLECTOR.** `ingestion/adapters.py` imports `redis` at module scope and `gui/state.py` → `ingestion.catalog` → `ingestion.adapters`, so **the GUI would fail to import without redis too**. One image serves both services, so both were rebuilt and recreated together; had only the collector been changed, the GUI would have broken.
>
> **`gold_real_rate_cross` IS NOT FIXED BY THIS AND STAYS FEED_FAILING.** It is a *separate* ingredient, `lbma.gold_fix_usd.history`, still pointing at the same 403ing LBMA endpoint, and it needs ~2600 **dated daily gold levels** (the percentile needs at least `MINIMUM_PERCENTILE_HISTORY` = 360 earlier correlations over a 60-day window, so ≥421 shared dates). HERMES publishes only the **single newest closed candle** under a 4 h TTL and no history at all, so it cannot supply that: `engine/derivations.py` needs **no change** (the derivation takes `gold`/`real_rate` dated histories by role and is source-agnostic), but a new accumulating-history gold feed is owed and is **larger than this WO**. **The monetary dial therefore still carries no `gold_real_rate_cross` signal**, and MATH.md R-9 is only half-closed by WO-1.12.
>
> **STALE COUNTS, FLAGGED NOT CORRECTED.** §4a carries no WO-1.10 or WO-1.11 addendum, so the counts in the table and in the paragraph below it predate `constituent_breadth_200dma` and `private_credit_stress`. This addendum changes `gold_spot` only and does **not** reconcile them.

So **17 have a raw source value that needs no further input (the dial scaling is WO-1.3), 7 have all raw inputs but need the engine to derive, 1 is half-fed, 5 are blocked.** *(Counts as of WO-1.2b/1.3; after the WO-1.6 addendum, `buffett_indicator` and `fiscal_dominance` are LIVE substitutes, `gold_spot` is wired but FEED_FAILING, so 2 of the 5 blocked are now live and the remaining blocked set is `ism_manufacturing`, `private_credit_stress` and `gold_spot`'s feed.)* "Tractable" is 25 of 30 counting inputs, 17 of 30 counting finished numbers.

Caveats, stated plainly:
- Yahoo is unofficial, unlicensed and rate-limited, and it is the only source for 5 of the 7 DERIVED indicators (credit_stress_hyg_lqd, breadth_rsp_spy, spx_vs_200dma, copper_gold; gold_real_rate_cross in part). Its failures are recorded, never defaulted.
- multpl is scraped HTML; a layout change is recorded MALFORMED.
- FRED monthly series are dated at the first of the month; the as-of used is month-end (capped at today) so they are neither permanently stale nor future-dated.
- Two zeros are genuine source values (SAHMREALTIME 2026-09 = 0.00; DRTSCILM 2026-07 = 0.0), checked against the raw FRED CSV.
- `ingestion/report.py` imports PyYAML; declared in `requirements.txt` at the host version (6.0) in the WO-1.2b Auditor reconciliation. The hash lock is not regenerated here.
- **`requirements.lock` is not what the deployed DEV image installs from.** `deploy/live-dev/Dockerfile` pip-installs its pins ad hoc (`PyYAML==6.0.2 jsonschema==4.10.3 redis==5.0.1`), bypassing the hash-verified lock path (PBG-CI-003). Pinned but not hash-verified. Pre-existing, widened by `redis` in WO-1.12, and **not fixed** — see the WO-1.12 addendum above.
- Auditor reconciliation (AMBER): a feed whose latest attempt failed now reports FEED_FAILING instead of LIVE; Yahoo bars dated today are dropped (a partial intraday bar can no longer be locked in as the close). Point-in-time/revision handling (a first print is never replaced) remains a noted WO-1.3+ concern.
- (Superseded in part by the WO-1.6 addendum: three of these five were wired.) None of the five NOT_TRACTABLE gaps is closable by engineering alone: each needs a licensed feed, a substitute the Product Owner approves, or a missing definition.

**Superseded in part by WO-1.5 (2026-10-11):** the engine now derives 6 of the 7 DERIVED indicators (`engine/derivations.py`: credit_stress_hyg_lqd, breadth_rsp_spy, vix_term_structure, spx_vs_200dma, copper_gold, shiller_cape). Live wired = 17 direct + 6 derived = 23 of 30. `gold_real_rate_cross` stays BLOCKED on definition. copper_gold is derived and stored, but its monetary binding is HELD on a polarity conflict (no band, not scored). Scaling bands for the derived six are provisional placeholders: no backtest, no distribution study. The "no computing mapping yet" wording in the table above is the WO-1.2b state.

Run: `PYTHONPATH=src:. python3 -m ingestion.run --db <file> [--force]`, then `python3 -m ingestion.report --db <file>`.

### Declared limits (not defects to be "fixed" casually)
- Deliberate in-process forgery by an insider cannot be *prevented* in Python (`CD-BP-005`); it is carried by the **DETECTED** tier (witness divergence at publication). The Owner accepted this explicitly (PO-DECISIONS-0018/0019/0032). Any text claiming more is the defect.
- The collector adapter boundary admits by protocol and is the softest surface (`CD-BP-003`).
- A consumer `fold` returning `0.0` on unknown renders absence as a number (`CD-BP-004`); ruled to WO-4.

## 5. What is needed to finish and deploy

In the order the Product Owner sequenced it (PO-DECISIONS-0032 §6):

1. **Independent Assurance verdict on increment 16G** (a fresh seat; the previous seat is barred by `PBG-SOD-001`). Outstanding since 2026-08-25.
2. **16C**: detector-side `feed_liveness` marking → register the 30 indicator rows from the mapping. First real dial numbers.
3. **Carry the PID §5 three-quantity correction** (relevance / liveness / publish) as a Product Owner record-act.
4. **WO-3 continues**: wire real sources (adapters for each mapped feed, under the admission perimeter).
5. **WO-4**: the public page; witnesses live; divergence alarm; history and slope; complete `CD-AC-018`.
6. **WO-5**: AI review with the four validators; public/private split evidence. **External party-independent review required** (doctrine-bearing controls, PID §8).
7. **WO-6**: rotation-readiness ratio, recovery-from-copy proof, wave-transition monitor.
8. **Backtest** to calibrate weights.
9. Build the images, deploy to DEV, independent ratification, then PROD. First production release, any change to the public publication surface, and any doctrine-bearing control change all need external review.

### Decisions CERBERUS must make before step 1 can even start
- **Governance framework.** The build was run under PBGv2 (a pinned `pbg/` snapshot, role seats, `PBG-*` rules). PBGv2 is retired. CERBERUS runs under FORGE. The `pbg/` tree, `CLAUDE.md`, the `governance/` records and the register tooling are vendored history; `pbg/PROVENANCE.json` still says `suitable_for_adoption: false` (see `docs/FRAMEWORK-ADOPTION-DISPOSITION.md`). Someone must decide whether to keep the register/plant discipline under FORGE or translate it. Do not run `pbg boot` and expect it to be authoritative.
- **Python version.** Pins target CPython 3.11 and the original host interpreter. The tests pass here on 3.11.2.
- **The `~24` vs `30` indicator discrepancy** (§2).
- **Ownership of Assurance.** The project depended on a pool of independent audit seats; CERBERUS WO flow uses R2D2 for that. Confirm.

## 6. How to run what exists

```bash
cd crash-detector
python3 -m pytest -q                            # 2,129 tests, ~70 s, no network, no install step
```

There is intentionally no install step (see `crash-detector/README.md`). Do not read a green test run as "the detector works": it means the *machinery that refuses to render absence as calm* is intact. Raw data can now be ingested (§4a) but no dial consumes it yet.

## 7. Map of this directory

| Path | Contents |
|---|---|
| `src/crash_detector/` | The implementation (45 modules). |
| `tests/` | 56 test modules, 2,099 tests. |
| `db/`, `contracts/`, `deploy/` | Store migrations, envelope schemas, containers/compose. |
| `plants/`, `variants/`, `tools/` | Planted-violation, variant and probe instruments for assurance. |
| `required-tests.yaml` | The Required Test Register: obligations, no results. |
| `governance/decisions/` | `PO-DECISIONS-0001..0032`: the Owner/PO rulings. **Best narrative of why things are the way they are.** |
| `governance/assurance/` | Every independent Assurance verdict (WO-2, 2R, 2R2, 2R3, meta-assurance, WO-3). |
| `governance/dispatch/`, `governance/engineering/` | Dispatch briefs, Active-work, and 236 append-only build-log entries (`BL-*.yaml`, one per session boundary). |
| `governance/mapping/` | The ratified indicator mapping. |
| `governance/rules/PROJECT-RULES.md` | `CD-RULE-*` project rules. |
| `pbg/` | Vendored PBGv2 snapshot. **Retired framework; read-only history.** |
| `ARCHIVE-COMMIT-MAP.txt` | Original SHA → imported SHA (see §8). |

Heads-up on volume: `governance/engineering/ACTIVE_WORK.yaml` is ~700 KB and the build log is dense and shouted in places. Start with the PO decisions and the verdicts, not the log.

## 8. History, provenance and the SHA caveat

- Source: the retired PBGv2 crash-detector repository, archived on the DEV host (2026-08-29). 586 commits across 19 branches and one tag, 2026-08-18 to 2026-08-25. (The earlier "342 commits" figure is only the archive's `main` branch, which carries governance records but **no source code**; the code lives on the unmerged `wo-3` branch.)
- All 586 commits are reachable from this branch. Paths were rewritten into `crash-detector/` with `git filter-repo --to-subdirectory-filter`, so `git log --follow crash-detector/PID.md` shows the real past back to 2026-08-18.
- **Imported commit SHAs differ from the originals** (the path rewrite changes them). Build-log entries, verdicts and commit messages quote **original** SHAs. Translate with `ARCHIVE-COMMIT-MAP.txt` (`old new`, one pair per line).
- Merge structure: archive `main` and `wo-3` (merge-base `bf8fcf9` original) are merged cleanly; twelve single-commit Assurance verdict branches `asr-wo3-03..14` are folded in by an octopus merge; the 24 commits that exist only under tag `wo-2-pre-identity-rework` are recorded with a tree-neutral (`-s ours`) merge.
- Not imported: the PBGv2 framework's own repository (a separate project), and an un-versioned copy of the WO-2 tree (`crash-detector-wo2`, superseded by the WO-2 branch). A backup path named in the CERBERUS PID (`/mnt/backup/crash-detector.git`) did not exist when this was checked.
- Security: the full imported history was scanned with `gitleaks` (all refs) with no findings. Owner email addresses were subsequently scrubbed from history; see `RECOVERY-ERRATA.md`. See `evidence/WO-1.2-crash-detector-recovery.md`.
