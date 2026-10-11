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

A live run on 2026-10-11 fetched **27 of 27 sources OK**. Of the 30 ratified indicators:

| State | n | Indicators |
|---|---|---|
| **LIVE** (the source's own number, inside its staleness window) | 17 | hy_oas, ig_oas, yield_curve_10y3m, yield_curve_10y2y, real_rate_10y_tips, breakeven_5y, fed_funds_rate, jobless_claims_4w, chicago_fed_nfci, broad_dollar, sahm_rule, michigan_sentiment, m2_yoy, cpi_yoy, core_pce_yoy, vix_level, cboe_skew |
| **DERIVED** (every input fetched; the *engine* must derive the number, and has no computing mapping yet, so there is no number of its own) | 7 | credit_stress_hyg_lqd, breadth_rsp_spy, vix_term_structure, spx_vs_200dma, copper_gold, gold_real_rate_cross, shiller_cape |
| **PARTIAL** | 1 | sloos_bank_lending: the automatic C&I leg (FRED DRTSCILM) is live; the manual NDFI leg (SLOOS Table 2 Q14) has no feed, so it must not read complete |
| **NOT_TRACTABLE** (no substitute wired; a substitute is a provenance decision) | 5 | buffett_indicator (Wilshire/GDP: FRED withdrew WILL5000PRFC, no free market-cap series), ism_manufacturing (licensed; FRED withdrew NAPM), gold_spot (no keyless public spot source; GC=F is futures, not spot), private_credit_stress (composite weighting and BDC universe undefined), fiscal_dominance (discriminator rule not in the mapping) |

So **17 produce a real number now, 7 have all raw inputs but need the engine to derive, 1 is half-fed, 5 are blocked.** "Tractable" is 25 of 30 counting inputs, 17 of 30 counting finished numbers.

Caveats, stated plainly:
- Yahoo is unofficial, unlicensed and rate-limited, and it is the only source for 5 of the 7 DERIVED indicators (credit_stress_hyg_lqd, breadth_rsp_spy, spx_vs_200dma, copper_gold; gold_real_rate_cross in part). Its failures are recorded, never defaulted.
- multpl is scraped HTML; a layout change is recorded MALFORMED.
- FRED monthly series are dated at the first of the month; the as-of used is month-end (capped at today) so they are neither permanently stale nor future-dated.
- Two zeros are genuine source values (SAHMREALTIME 2026-09 = 0.00; DRTSCILM 2026-07 = 0.0), checked against the raw FRED CSV.
- `ingestion/report.py` imports PyYAML, which the host has but `requirements.txt` does not declare (tests already depend on it too). Declaring it is owed; the lock was not touched here.
- None of the five NOT_TRACTABLE gaps is closable by engineering alone: each needs a licensed feed, a substitute the Product Owner approves, or a missing definition.

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
