# PID — CERBERUS
Combined LGT Wealth Management + US-Equities Day Trading + Crash Detector

**Status:** AUTHORISED — Owner green-lit 2026-09-19 (chat record), subject to the corrections in this revision (project renamed, PLUTUS scope corrected). WO-1.1 may now be dispatched.
**Author:** Trinity (Strategic Partner / Product Owner for this PID)
**Date:** 2026-09-19 (authorised same day)
**Governance:** FORGE delivery-control framework (PID → PL → Engineer/Auditor loop, `/srv/forge`), per Matt's explicit 2026-09-19 instruction, **superseding PBGv2** (retired 2026-08-29, see §12). This document's shape follows the PBG-1.0.0 `pid.md` template for continuity of format only — the delivery mechanism it authorises is FORGE, not classic PBG WO/epic tooling.

---

## 1. PROJECT SUMMARY

**Name:** CERBERUS — confirmed. Three heads, one guard: the crash detector (early warning), LGT wealth (long-term guardianship), and equities day trading (active guardianship) — one system watching the whole capital picture. Chosen at Owner's request for a name distinct from PLUTUS, which is a separate, actively-developed project for a different purpose with its own path to production.

**One-line purpose:** One coherent, governed system that (a) tells Matt when to move money between defensive and growth positions for LGT long-term wealth, (b) runs a real, risk-gated US-equities day-trading capability that doesn't exist today, and (c) gives both of those a working crash/regime signal to act on — built by adopting proven open-source components instead of re-deriving everything by hand.

**Strategic reason:** Eighteen-plus months of build effort across Argus, PBGv2 and the crash detector has produced excellent design and partial infrastructure, but — verified as of 2026-09-19 — **no working crash signal, a static £356,931 book with £850k sitting undeployed, and zero existing US-equities day-trading capability of any kind.** (Note: PLUTUS, a separate FX/metals scalping project, exists but is being built for a different purpose on its own production timeline — out of scope here, not a substitute for the equities capability this PID delivers.) The gap isn't ideas; it's a working, integrated system. This PID's job is to close that gap fast by reusing what the market has already built where it's genuinely good, and reserving custom build effort for the small number of things nothing off-the-shelf does honestly (validated backtesting discipline, risk gating, the crash dial logic itself).

**Desired outcome:** A live, containerised, FORGE-delivered system on dell-debian (DEV) promoting to IONOS (PROD) that (1) gives Matt a trustworthy crash/regime dial feeding the £850k re-entry decision, (2) runs a structured, multi-source LGT research/committee process on a monthly cadence, and (3) runs a real, backtested, risk-gated US-equities day-trading loop on IBKR paper, with a defined (not yet exercised) path to live.

**Definition of success:** Crash detector live on real data, its output driving a documented re-entry rule Matt has actually used at least once. LGT committee cycle running monthly with reconciled (not divergent) numbers against Argus/CO. Equities day-trading strategy backtested, risk-gated, and proven on IBKR paper over a defined soak period. Everything containerised, reboot-safe, and owned by a named persona — nothing left as an unmonitored zombie service, which is exactly the failure mode the legacy crash engine is in right now.

**Definition of failure:** Another design-complete, never-deployed artefact. A second silent zombie service nobody notices for a month. An LLM-generated buy/sell signal acted on without a backtested, risk-gated foundation underneath it. £850k still sitting idle six months from now because the signal it's waiting on was quietly retired again.

---

## 2. OWNER INTENT

**Why it exists:** Matt's own framing, 2026-09-19: *"We have thrown a lot of time and effort at this and have not really progressed to where we need to get to... we need to start taking short cuts... our work is not wasted, we just need to make sense of what we are doing."* This PID is that sense-making, converted into a deliverable shape.

**What must NOT drift:**
- The two goals stay distinct. LGT wealth management and day trading are "very different beasts" (Matt's words) with different cadence, different risk tolerance, different instruments. No workstream may blur them to look efficient.
- No ungrounded LLM verdict ever touches real capital directly. Every adopted research/analysis tool (OpenBB, Fincept, TradingAgents, AI Hedge Fund) is a documented *input*, reconciled against our own data, never a standalone trigger.
- No second source of truth left unreconciled against Argus/CO. This program already has one live incident in that exact class (`helm_defect_board_is_stale`) — do not create a second.
- Nothing ships as a design document that never runs. The crash detector already failed this once under PBGv2.

**Acceptable trade-offs:** Speed over originality — adopt a proven open-source component even if it's not a perfect fit, provided it's reconciled and risk-gated. Narrower MVP scope over another multi-month foundation phase.

**Unacceptable trade-offs:** Skipping backtested validation to hit a date. Letting a paid-API research tool's number silently override Argus's board without a diff step. Going live on real equities capital before a defined paper soak period completes.

---

## 3. SCOPE

**In scope:**
- Crash Detector rebuild: retire the legacy ARGUS-coupled engine, stand up the standalone container on FORGE (recovering the already-Matt-signed design), MVP on dell-debian DEV, promote to IONOS PROD.
- LGT wealth tooling: OpenBB (data layer), Fincept Terminal (Matt's research console), TradingAgents (due-diligence tool), AI Hedge Fund (monthly committee + backtest pre-screen), integrated into Trinity's existing portfolio-review process.
- US-equities day trading: net-new build on a backtest-proven engine (backtrader), with a governed risk-gate layer, targeting IBKR paper first.
- A shared risk-management/position-sizing capability (Kelly/fractional-Kelly + liquidity/correlation/concentration/drawdown gates) — no credible open-source candidate exists; this is built once and used by both the day-trading epic and, where relevant, LGT sizing decisions.

**Out of scope / non-goals:**
- **PLUTUS is entirely out of scope.** Confirmed by Matt 2026-09-19: it is a separate, actively-developed project built for a different purpose, with its own path to production later. CERBERUS does not assess it, revive it, retire it, or reference its build status — it is mentioned in this PID only as the existing precedent for the ARGUS-boundary isolation discipline (§10), nothing more.
- Replacing the Argus CO valuation stack. New data sources supplement and cross-check it; they don't replace the Beneish/valuation/fiscal-calendar logic already built.
- Fixing NEO's ground-truth gap (`decisions_scored: 0`, no R2D2 audit ever run) or the live Helios DB-access defect. Real, open, but NEO's own lane — cross-referenced here, not re-scoped in.
- Going live with real capital on the equities day-trading loop. This PID delivers to a proven paper stage; going live is a future, separately Owner-authorised decision.

**Assumptions:**
- FORGE (`/srv/forge`) governs all epics in this PID, not just the crash detector — confirmed by Owner green light 2026-09-19.
- "IONOS server" for crash-detector PROD means `prod-web-1` (194.164.122.84, Helm-owned) — the only known Helm-owned IONOS host in the record. Accepted; Helm confirms the exact host technically as part of WO-1.4 before promotion, not a pre-condition to starting Epic 1.
- backtrader (cloudQuant fork)'s live-trading layer includes a working IBKR adapter. Reviewed as a backtest+live engine; the specific IBKR broker integration in this fork has not been hands-on verified. First action item, not an assumption to build on blind.

**Known unknowns:**
- Whether the crash detector's provisional indicator weights survive real backtesting, or need rework.
- Real cost of running Fincept/TradingAgents/AI Hedge Fund's per-token agent calls at the cadence this PID proposes — needs a budget set before regular use, not after.
- Whether NEO's mandate should extend to equities day-trading observation, or whether that needs a new/adjacent role. Left open for the PO breakdown, not decided here.

---

## 4. ROLE MODEL (RACI)

| Role | Specialist | Notes |
|---|---|---|
| Product Owner (this PID) | **Trinity** | Holds intent, sequencing, reconciliation discipline, Owner liaison |
| Delivery Lead / FORGE PL | **Rogue** | **Corrected 2026-10-10 — was wrongly assigned to Helm in the original draft.** Argus-adjacent, dell-debian infrastructure is Rogue's standing lane, not Helm's (CLAUDE.md domain table: "Trinity delegates Argus infrastructure work to Rogue, NOT Helm"). Runs the PID→PL→Engineer/Auditor loop under FORGE; dispatched by Trinity under this authorised PID — escalates only irreversible/large-blast/real-money actions, for a second pair of eyes, not permission. |
| ARGUS/dell-debian infra boundary custodian | **Rogue** (same seat as above) | Owns the legacy engine retirement's ARGUS-side blast radius; owns keeping the crash detector and any future equities engine OUT of the ARGUS app boundary, same discipline as the PLUTUS wall |
| Infra escalation only | **Helm** | Not the Delivery Lead for this PID. Available if Rogue needs infra escalation outside the Argus boundary (e.g. IONOS prod host confirmation per §3), not for routine CERBERUS dispatch. |
| Backtest & strategy validation | **R2D2** | Independently validates crash-dial weights and any equities strategy before either touches paper/live capital — this is the gate that was missing from every LLM-driven repo reviewed |
| Live/paper execution authority | **Trader** | Owns the IBKR paper (and any future live) account the equities epic targets; owns session-level go/no-go |
| Observation (day trading) | **NEO** | Existing mandate — observation/scoring/never-executes; extension to equities day-trading is an open design question (§3), not assumed |
| Final authority | **Matt** | All Owner Review Points in §6; real-capital decisions non-delegable |

No hats doubled beyond the existing standing model. Rogue and Helm's ARGUS-boundary discipline is the same one already governing PLUTUS's isolation — extend it, don't re-litigate it.

---

## 5. DELEGATED AUTHORITY

Once this PID is Owner-authorised, the Delivery Lead (Rogue, dispatched by Trinity) decides autonomously within:
- **Objective:** deliver the Epics in §11 to the acceptance criteria each carries.
- **App boundary:** each epic's own container/repo; never inside the ARGUS app boundary (crash detector and equities engine are both standalone, ARGUS-adjacent-not-ARGUS, same wall as PLUTUS).
- **Security:** no secrets in git (public-repo doctrine already proven on Bagman applies here), no live broker/API keys in any third-party desktop tool (Fincept), no conversational order placement outside a sealed sandbox.
- **Approved architecture:** FORGE PID→PL→Engineer/Auditor loop; containerised dev-then-prod per Matt's instruction.
- **Runtime authority:** dell-debian DEV without further sign-off per change; IONOS PROD promotion requires the Owner Review Point in §6.
- **Cost/risk:** paid API usage (Financial Datasets, FRED beyond free tier, agent-token spend) capped at **£80/month combined across all adopted tools**, set by Trinity under this delegated authority following the 2026-09-19 cost discussion; reviewed at Epic 2 kickoff and adjustable there; anything larger escalates. **This is a burst/ceiling cap, not an expected bill** — per the revised §10 LLM-routing rule, routine/occasional CERBERUS reasoning defaults to Matt's spare Claude Max headroom (don't pay twice for capacity already sitting idle); metered spend is expected mainly from AI Hedge Fund's backtest sweeps and any genuinely high-volume scheduled job, the two cases where an unmonitored burst could actually compete with the team's delivery capacity.

**Escalate for a second pair of eyes (not permission):** retiring the legacy crash engine (irreversible-ish, touches live ARGUS-adjacent infra), any step that touches real trading capital, any step that would delete rather than archive the existing `/srv/ARCHIVE/pbgv2-retired-20260829/` crash-detector artifacts.

---

## 6. OWNER REVIEW POINTS (exception triggers)

All naming/framework/host/budget questions raised at draft stage were resolved by Owner green light 2026-09-19 (§16). Live, ongoing exception triggers for delivery:

- Any equities day-trading step that moves from IBKR paper toward real capital.
- Any LGT allocation decision the crash detector's dial output actually recommends acting on (the dial informs; Matt decides).
- Deletion (not archival) of any legacy artefact.
- Anything that would touch, reference, or fold in PLUTUS — it is fully out of scope; if any WO finds itself needing PLUTUS for any reason, stop and return to Matt rather than assume.
- Paid API/agent spend exceeding the £150/month delegated cap (§5).

---

## 7. GOVERNANCE

Complies with **FORGE** (`/srv/forge`): PID → PL (Rogue, driving session) → Engineer subagents (bounded, no git authority) → reconciliation/tests → independent fresh-dispatch Auditor → bounded repair loop → GitHub delivery candidate → Matt's final scrutiny. Durable truth = git; Fabric/Redis is messaging only, never durable state — matches the `bagman:knowledge:forge_doctrine` model already proven end-to-end on Bagman CD-1 through CD-5.

**Project-specific addition:** the FORGE `pl-startup-gate` (PID.md + git repo + GitHub remote, all three, before any Engineer dispatch) applies per epic-repo, not once for the whole PID — each of the three build epics (§11) gets its own repo, its own gate pass, before work starts. No epic quietly shares another's git history.

**Hard supersession note:** PBGv2 is retired (2026-08-29, `/srv/ARCHIVE/pbgv2-retired-20260829/`). This PID does not resume it, extend it, or reference it as a live framework. Where PBGv2-era design artefacts are genuinely reusable (the crash-detector design itself, Matt-signed), they are salvaged as content, not as process.

---

## 8. DOCUMENTATION SKELETON

- Repo: one new GitHub repo per build epic (crash-detector, cerberus-wealth-tooling or similar, cerberus-equities-daytrading), name/owner/visibility set by Matt at repo-creation time — FORGE's own doctrine bars the PL from inventing this.
- Worktrees: `/srv/openclaw/worktrees/epic/<EPIC-ID>` and `/srv/openclaw/worktrees/wo/<WO-ID>` per the existing CLAUDE.md branch hierarchy, layered under each epic's own repo.
- Governance: this PID.md at `/srv/cerberus/PID.md` (or the repo root once created); FORGE docs at `/srv/forge/docs/` for the process itself.
- Backlog / logs: Fabric `project:cerberus:*` namespace (§14).
- Blueprint: crash detector's existing Matt-signed design content stays where it is (`trinity:pbgv2:crash_detector:*` — the "pbgv2" in the key name is now historical, not a live dependency); a `project:cerberus:crash_detector:index` pointer is added rather than migrating the data.
- Evidence: per-epic, in-repo, FORGE evidence-doctrine style (proven on Bagman: `memory/generated/<EPIC>-EVIDENCE-<date>.md`).
- Fabric namespace: `project:cerberus:*` (see §14).

---

## 9. DELIVERY MODEL

**Epic → Story/WO**, each WO run through the full FORGE PL→Engineer→Auditor loop, one Owner approval per bounded change (Lean-PBG-style proportionality already proven right for ARGUS — see [[shared_rule_argus_lean_pbg]] — carried forward here rather than re-litigated), hard gates reserved for destructive/irreversible/cross-project/real-capital actions per §5.

**Definition of Done** (per WO): implemented, independently Auditor-reviewed (fresh dispatch, zero inherited context), live CI green (not just local), evidence committed in-repo, and — for anything touching a live service — **live, tested, and signed off**, not merged-and-assumed-deployed. This project inherits [[shared_rule_done_live_tested_signed_off]] and [[shared_rule_merged_is_not_deployed]] directly: the crash detector's entire failure mode to date has been exactly "correct design, never actually live."

---

## 10. TECHNICAL + ISOLATION BOUNDARIES

**Canonical build location, pinned 2026-10-10:** `dell-debian:/srv/cerberus` (`ssh root@192.168.11.10`) — cloned from `https://github.com/maff0000/cerberus` (GitHub is the source of truth; this is just where the live checkout lives). Confirmed empty before cloning — this is a fresh location, not a move of existing work. Note this deliberately departs from the house `/srv-dev/<name>` convention other dell-debian projects use (ARGCAT, ARGUS) — Owner's explicit choice, not an oversight. The original authoring copy at `trinity:/srv/cerberus` is historical only going forward; all further work happens against the dell-debian checkout.


- **Crash Detector:** standalone container, own DB schema, own service surface, dell-debian DEV → IONOS PROD. Integrates with ARGUS/HERMES data **only via governed, read-only contracts** — never embedded in the ARGUS runtime again. This is the specific lesson from why it "died twice on ARGUS internals."
- **US-Equities Day Trading:** new, standalone project. Same wall PLUTUS already taught us to build: never smuggled into the ARGUS app boundary, own repo, own runtime, own credentials. Consumes Argus/OpenBB data via contract, never direct DB access.
- **LGT Wealth Tooling:** OpenBB/Fincept/TradingAgents/AI-Hedge-Fund integrations sit alongside Trinity's own review process, write to `project:cerberus:wealth:*`, and are explicitly reconciled against Argus/CO before any number is presented to Matt as decision-grade.
- **Shared risk-management library:** built once, versioned, consumed by the equities epic as a hard gate and available (not mandatory) to LGT sizing decisions.
- **Secrets:** no secrets in any git repo (Bagman's proven three-layer config model + gitleaks scanning applies); Fincept never gets a live broker key; Alpaca-style conversational order placement stays out entirely (rejected in repo review, §11 references only).
- **Data integrity:** every ingested data source (yfinance via OpenBB, Financial Datasets via AI Hedge Fund) is treated as unofficial/rate-limited until proven otherwise — fail-loud on staleness, never silent-stale (the exact class of bug already open on the board-is-stale defect).
- **LLM routing (Owner ruling, 2026-09-19, revised same day — Matt is on Claude Max with real spare headroom day-to-day, rate-limited only once, during the PBGv2 incident; the rule is usage-based, not a blanket ban on using that headroom):**
  - **Default: use the spare Claude Max capacity** for CERBERUS's low/occasional-volume reasoning work — Fincept-equivalent DCF/screening, TradingAgents-equivalent on-demand due-diligence, AI Hedge Fund's monthly committee cycle — driven as ordinary Trinity/persona sessions rather than paying per-token for equivalent quality the plan already covers. Same principle already established for attended vs unattended work ([[trinity_feedback_run_helm_autonomously]]): a bounded, Trinity-supervised session against a low-volume task is attendance, not a drain.
  - **The dial is volume/burst risk, not the tool.** Anything that could spike into hundreds-to-thousands of calls in a short window — AI Hedge Fund's historical backtest sweeps above all, and any Epic 0 cron/scheduled job running unattended at real frequency — routes to metered Sonnet 5 API or the local `trinity:llm` gateway instead, specifically because an unmonitored burst is what actually caused the one real limit-hit on record (PBGv2). Routine/bulk formatting-type work defaults to the free local gateway regardless of volume.
  - **Circuit breaker:** if any team dispatch (Helm/R2D2/Bagman/Trader/dev work) is ever observed rate-limited or delayed because of CERBERUS activity, that's the signal to shift the specific workload causing it off Max sessions — not a reason to preemptively wall everything off.
  - Metered API stays the fallback for whichever of TradingAgents/AI Hedge Fund can't be reasonably run as a Trinity-driven session (their own internal multi-agent loop, not equivalent manual synthesis) — Fincept confirmed to support custom/Ollama endpoints too, if that turns out cheaper than either.
  - **Friday-night scheduling for burst workloads (Owner idea, 2026-09-19):** Claude Max's weekly token allowance resets Saturday — any leftover weekly headroom otherwise expires unused. Burst-risk jobs (AI Hedge Fund backtest sweeps chiefly) are scheduled Friday evening, ahead of the reset, authenticated via the Max OAuth profile by default (SDK credential order: `ANTHROPIC_API_KEY` unset → falls through to the `ant auth login` profile) rather than an API key from the start. A wrapper catches the *specific* usage-limit error (not any failure) and swaps to the metered Sonnet 5 key only for the overflow past what Max headroom covers, so the run finishes rather than stalling. Also clear of any trading activity ([[shared_weekend_no_trading_context]]) and reuses Epic 0's digest harness to post a completion/failure summary — a Friday-night job failing silently over the weekend is the exact zombie-service pattern already in §12.
  - **NOT YET VERIFIED — first action, not an assumption:** `ant` CLI is not installed on this host; there is no confirmed active Max-linked OAuth profile to fall back to, and it is not confirmed that Fincept/TradingAgents/AI Hedge Fund all use the standard Anthropic SDK (vs. raw HTTP with only API-key support) — the OAuth fallback only works through the SDK's credential resolution. Verify both before building the Friday-night wrapper.

---

## 11. INITIAL WORKSTREAMS

### EPIC 0 — Foundations & Shared Data/Risk Layer
- WO-0.1: OpenBB Python SDK (not the MCP) scripted on a cron — FRED macro daily, fundamentals on filing, EOD equity/ETF scans post-close — writing to `project:cerberus:data:*` and cross-feeding Epic 1's crash-detector indicators.
- WO-0.2: Risk-management/position-sizing library — Kelly/fractional-Kelly sizing + liquidity/correlation/concentration/drawdown gate engine. Built fresh (confirmed no credible open-source candidate exists after two search passes). Consumed by Epic 3 as a hard pre-trade gate.
- WO-0.3: Reusable "scheduled digest" automation harness (cron → fetch → LLM synthesis → push-to-Telegram/Discord), pattern borrowed from daily_stock_analysis's automation design (not its decision logic) — used by Epic 1 (dial-change alerts) and Epic 2 (monthly committee digest). Synthesis step runs through the local `trinity:llm` gateway (routine work), not metered API.
- WO-0.4a: Verify the Max-OAuth-fallback mechanism — confirm `ant` CLI + an active Max-linked profile can be set up on the delivery host, and confirm which of Fincept/TradingAgents/AI Hedge Fund use the standard Anthropic SDK (required for automatic credential fallback) vs. raw HTTP (would need a bespoke wrapper). First action before WO-0.4b.
- WO-0.4b: Build the Friday-night burst scheduler — cron-fires burst-risk jobs (AI Hedge Fund backtests) Friday evening ahead of the Saturday Max reset, Max-OAuth by default, falls over to metered Sonnet 5 only on an actual usage-limit error, posts a completion/failure summary via Epic 0's digest harness (WO-0.3).
- WO-0.4c: Attempt a Financial Datasets replacement — adapter pointing AI Hedge Fund's data layer at Argus/CO (which already has point-in-time-disciplined fundamentals) + OpenBB, instead of the ~$20/month third-party subscription. One-time engineering spike; keep the subscription as fallback only if the adapter can't cover what the backtest actually needs. Avoids both the recurring cost and introducing a second unreconciled data source.

### EPIC 1 — Crash Detector Rebuild (Matt's stated priority — blocks the £850k re-entry decision)
- WO-1.1: Retire and archive the legacy ARGUS-coupled crash engine (`argus-crash-deploy-advisory`, `argus-monetary-regime-alert`, `argus-monetary-regime-producer`, `argus-monetary-tell-{boe,fred,gold}`) — stop the services, disable/remove the timers currently firing hourly/daily into failure, archive don't delete. Dispatch: Rogue.
- WO-1.2: Stand up the standalone containerised crash detector on dell-debian DEV via FORGE, recovering the Matt-signed design and existing build increments from `/srv/ARCHIVE/pbgv2-retired-20260829/crash-detector{,-wo2r3}` and `/mnt/backup/crash-detector.git` — salvage, do not re-derive.
- WO-1.2b: Real data ingestion for the 30 ratified indicators — survey which are tractable on free/public sources (FRED, OpenBB, public APIs) vs blocked, build real fetch-on-cadence ingestion feeding the existing fail-safe core (missing/stale stays missing, never calm). Narrowly Epic 1 data need; does NOT revive paused Epic 0/Epic 3. Branch `wo/CERBERUS-WO-1.2b-indicator-data-ingestion`, no self-merge. Dispatch: Rogue (via Trinity, 2026-10-11).
- **WO-1.3 SUPERSEDED 2026-10-13 (`DECISION-RULE.md`, Owner-confirmed) — split in two, below.** The original framing ("validate the provisional weight mapping") assumed the current flat `BANDED_WEIGHTED_MEAN` engine stays; it does not — `DECISION-RULE.md` replaces it with a masters/breadth/acute/count state machine. Validating today's tier weights would validate an architecture already being replaced.
- **WO-1.3a (new):** build the three-statistic engine against `DECISION-RULE.md` §6 — breadth/acute/count composites, the master set, the five-state machine (including `UNKNOWN` fail-closed and conservative bracket resolution), and the §7 output contract. Sequenced after historical backfill and point-in-time/vintage discipline exist (already sequenced first; this is new build work, not calibration, and calibrating masters against today's vintages would be exactly the lookahead backfill is meant to avoid).
- **WO-1.3b (new):** R2D2 validates the masters and state thresholds (§6/§10's "unset" rows) via historical replay across the episode list in `DECISION-RULE.md` §10, once WO-1.3a exists and backfill is real. This is the actual audit gate — nothing here is trustworthy before R2D2 clears it.
- **WO-1.14 (new 2026-10-13):** Historical backfill + point-in-time/vintage discipline — prerequisite for WO-1.3a/1.3b and the architect's "prove it on episodes" replay (`DECISION-RULE.md` §10: 2000-02, 2007-09, 2011, 2015-16, Q4 2018, March 2020, 2022, April 2025). Scope narrowed from the architect's general flag to the two real mechanisms, not every series: (1) **ALFRED vintages, not plain FRED**, for the genuinely revision-prone series — initial claims (`IC4WSA`), consumer sentiment (`UMCSENT`), `NFCI`, `M2SL`, `CPIAUCSL`, `PCEPILFE` — verify this list against ALFRED's own revision history rather than assuming; everything else FRED-sourced (yield/spread/rate levels: `BAMLH0A0HYM2`, `BAMLC0A0CM`, `T10Y3M`, `T10Y2Y`, `DFII10`, `DFF`, `T5YIE`, `DTWEXBGS`, `DRTSCILM`) is a realized market/survey value, not revised, and backfills safely from plain FRED. (2) **Yahoo unadjusted close, not dividend-adjusted**, for `private_credit_stress` and `constituent_breadth_200dma` — adjusted closes are rewritten retroactively on every distribution. Store schema gains a `vintage` tag (`original` | `current_only`) per backfilled row; anything that can't get a genuine point-in-time vintage is tagged `current_only` and **excluded from WO-1.3b calibration**, not silently used. Disclosed, not fixed, here: `multpl.com`'s CAPE/Buffett-substitute figures are themselves derived from GDP/earnings data that gets revised upstream — multpl.com publishes no vintages, so this is a known, carried limitation, not solved by this WO. `gold_spot`'s HERMES source has no multi-year history at all (35-day retention) — backfill for gold needs a separate historical source, out of this WO's scope, tracked separately.
- WO-1.4: MVP acceptance on DEV, then promote to IONOS PROD (host TBC — assumed `prod-web-1`, confirm with Helm).
- WO-1.5: Define the actual re-entry decision rule — what dial reading triggers what LGT allocation conversation — so Epic 2's £850k question has a concrete trigger, not another open-ended wait.

**Delivered so far (2026-10-11 → 2026-10-13, actual sequence — diverges from the WO-1.1–1.5 sketch above as real gaps were found during the recovery; this block is the honest record, not a rewrite of the original plan):**
- WO-1.2 (`dbd7641`): standalone container recovered on FORGE — 586 commits of genuine build history salvaged from the PBGv2 archive, not re-derived.
- WO-1.2b (`1a0def5`): real data ingestion wired for the ratified indicators (fail-safe: missing/stale never renders calm).
- WO-1.3 (`de4eef1`): indicators registered in the engine.
- WO-1.5 (`4b58c6c`): derived indicators + GUI, deployed as a Docker container on dell-debian.
- WO-1.6 (`8d0ee45`): legacy-source reuse from the old ARGUS crash-engine code; `gold_spot`'s LBMA 403 first disclosed.
- WO-1.7 (`2fa6aec`): remaining-pending indicators (`gold_real_rate_cross` attempt, `ism_manufacturing`, SLOOS manual-entry leg).
- WO-1.8 (`2312e0f`): `private_credit_stress` (BIZD proxy).
- WO-1.9 (`83d7057`): staleness-window recalibration (fixed the equity_crash "NO READING" bug — window too tight for routine holiday gaps).
- WO-1.10 (`46808bd`): `constituent_breadth_200dma` — new S&P-breadth indicator, Matt's own proposal.
- WO-1.11 (`393e0ba`): `MATH.md` — full, independently-verified dial mathematics, written for third-party (external architect) review.
- WO-1.12 (`d377b69`, [PR #1](https://github.com/maff0000/cerberus/pull/1)): `gold_spot` re-sourced from HERMES's live XAU_USD feed, replacing the dead LBMA endpoint. First WO delivered through an actual reviewed GitHub PR.

**Still open from the original sketch, not started:** WO-1.3 (backtest/R2D2 validation of the provisional weight mapping — real priority now that the external architect review is in motion), WO-1.4 (IONOS PROD promotion), WO-1.5 (the re-entry decision rule — now superseded in substance by the state-machine `DECISION-RULE.md` being drafted with the external architect; this PID line will be struck when that lands).

**Process change, standing from 2026-10-13 (Matt):** every WO from here opens a real GitHub PR with a full description — what changed, why, verified evidence, disclosed-not-fixed items — before merge. WO-1.2 through WO-1.11 were merged directly with no PR trail; that gap is not being retroactively rewritten, only closed going forward.

### EPIC 2 — LGT Wealth Management System
- WO-2.1: OpenBB fundamentals/macro feed into Trinity's portfolio review (via Epic 0).
- WO-2.2: Fincept Terminal set up as Matt's personal interactive research console — screening, DCF, geopolitics desk. Token budget cap set before regular use.
- WO-2.3: TradingAgents wired as an on-demand due-diligence tool for significant entry/add decisions — deliberate, per-decision use, never scheduled.
- WO-2.4: AI Hedge Fund committee cycle run monthly (matching its own default rebalance cadence) against LGT candidate/held names, backtest feature used to pre-screen strategy ideas before anything goes to R2D2.
- WO-2.5: Reconciliation process — any number from Fincept/TradingAgents/AI-Hedge-Fund that would influence a real decision must be diffed against Argus/CO before use; formalise this as a checklist, not a hope.
- WO-2.6: Execute the £850k re-entry decision once Epic 1's WO-1.5 trigger fires and Matt actually rules on it.
- **WO-2.7 (new 2026-10-13 — scope boundary, Matt confirmed):** Tranche/deployment mechanics — minimum spacing between tranches, the anti-step-down rules (no tranche while the acute statistic is rising, no averaging-down beyond the X% guard, second-leg rule restarting the recovery clock), and the independent position drawdown/stop rule that must keep working when CERBERUS is blind. Consumes CERBERUS's output contract only (`state`, `sizing_multiplier`, `acute_rising`, `coverage_bracket`, `as_of` — `DECISION-RULE.md`); never reaches into the crash-detector's own internals.
- **WO-2.8 (new 2026-10-13 — scope boundary, Matt confirmed):** Regime map — historical market-regime classification keyed off CERBERUS's dial/state history, built and owned as a consumer-side analysis tool, not part of the crash detector itself.
- **WO-2.9 (new 2026-10-13 — scope boundary, Matt confirmed):** Historical analogues / "prove it on episodes" backtest across 2000-02 through the present, validating the decision rule's behaviour against real historical crashes and recoveries — a consumer-side validation exercise (R2D2-owned per the usual backtest-validation lane), not an Epic 1 deliverable.

### EPIC 3 — US-Equities Day-Trading System (net-new, shortcut-first)
- WO-3.1: Verify backtrader (cloudQuant fork)'s IBKR live-broker adapter — first action, before committing further build to this engine as the backbone.
- WO-3.2: Adopt backtrader/backtesting.py as the backtest + execution engine, under R2D2 validation, against our own strategy ideas (fast-iterate in backtesting.py, validate for real in backtrader).
- WO-3.3: Wire Epic 0's risk-gate library in front of every order — hard-refuse on any failed gate, no override path that bypasses it silently.
- WO-3.4: Symbol/instrument identity discipline from day one: `(symbol, exchange, currency)` triple or `conId`, fail-loud on ambiguity — carrying forward the Boeing/BAE lesson from the still-HELD IBKR-symbol-resolution defect so it isn't repeated in new code.
- WO-3.5: (Optional, explicitly downstream-only) LLM-assisted signal layer inspired by TradingAgents/AI-Hedge-Fund's analyst/debate architecture — never the trigger itself, always sitting behind R2D2-validated logic.
- WO-3.6: Paper-trade proof on IBKR paper account, minimum soak period (TBD by PO/Delivery Lead at breakdown), before any live-capital conversation opens as a separate future PID.

### PLUTUS — boundary note, not an epic
PLUTUS is a separate, actively-developed project for a different purpose, on its own path to production. No PLUTUS work of any kind — assessment, revival, integration, or otherwise — happens under CERBERUS. It appears in this PID only as the existing precedent for the ARGUS-boundary isolation discipline applied to Epic 1 and Epic 3 (§10).

---

## 12. RISK REGISTER

| Risk | Class | Mitigation |
|---|---|---|
| Repeat the crash detector's own failure mode: design-complete, never live | Delivery | Definition of Done requires live+tested+signed-off per WO (§9), not merged-and-assumed |
| Ungrounded LLM verdict (daily_stock_analysis-style, or misused TradingAgents/AI-Hedge-Fund output) acted on directly | Correctness/capital | Every research-tool output is a documented input, reconciled, never a standalone trigger (§2, §11 WO-2.5) |
| Second unreconciled source of truth vs Argus/CO (same class as `helm_defect_board_is_stale`) | Correctness | Mandatory reconciliation checklist before any external number is decision-grade |
| Symbol/instrument identity collision in new equities code (Boeing/BAE class) | Correctness/capital | `(symbol, exchange, currency)` or conId discipline from day one, fail-loud on ambiguity |
| Backtest survivorship/lookahead bias (AI Hedge Fund equity curve, any adopted backtester) | Correctness | R2D2 independent validation mandatory before any backtest result informs real capital |
| Silent zombie service (the legacy crash engine is currently in exactly this state) | Ops | Every new service gets an owning persona and an active, verified-working health check — not a watchdog watching nothing |
| Per-token cost creep across Fincept/TradingAgents/AI-Hedge-Fund | Cost | £80/month delegated cap (§5), reviewed at Epic 2 kickoff |
| CERBERUS research work silently drawing on Matt's shared Claude Code Max capacity instead of metered API, crowding out the team's delivery work (Helm/R2D2/Bagman/Trader/dev) | Ops/Cost | Explicit LLM-routing rule (§10): bulk/routine work on the local gateway, quality-critical work on metered Sonnet 5, Max-plan sessions never used as a substitute backend |
| Data source reliability (yfinance unofficial API, Financial Datasets pedigree unverified) | Data integrity | Fail-loud on staleness, never silent-stale; verify Financial Datasets' point-in-time correctness before trusting any backtest built on it |
| AGPL-3.0 (OpenBB, Fincept) | Legal | Fine for internal use; flag before any external distribution |
| Scope creep into PLUTUS (adjacent FX/day-trading domain, easy to conflate with Epic 3) | Delivery | Explicit boundary note (§11); any WO that finds itself needing PLUTUS stops and returns to Matt (§6) |

---

## 13. ESCALATION RULES

Exception triggers = §6 verbatim. In addition: any Auditor RED finding that the PL cannot resolve in the bounded repair loop escalates to Trinity before a second repair attempt (per FORGE doctrine — repeated repair loops without escalation is drift, not diligence).

---

## 14. FABRIC REQUIREMENTS

- `project:cerberus:*` — new project namespace, indexed at `project:cerberus:index`.
- `project:cerberus:crash_detector:index` — pointer to the existing `trinity:pbgv2:crash_detector:*` content (no data migration).
- `project:cerberus:data:*` — Epic 0 data-layer outputs.
- `project:cerberus:wealth:*` — Epic 2 committee/reconciliation outputs.
- `project:cerberus:daytrading:*` — Epic 3 strategy/risk-gate state.
- Existing review record, already written this session and to be read before any epic kickoff: `trinity:repo_review:index:v1`, `trinity:repo_review:SYNTHESIS:v1`, `trinity:pid_prep:state_of_truth:v1`.
- `bagman:knowledge:forge_doctrine` — read this before any FORGE PL dispatch; it's the condensed, already-proven operating doctrine, don't re-derive from `/srv/forge`'s docs each session.

---

## 15. FIRST 3 ACTIONS for the Delivery Lead after authorisation

1. **WO-1.1 first, before anything else builds**: retire and archive the legacy ARGUS-coupled crash engine — it's actively failing into nothing right now and consuming resources. Dispatch Rogue.
2. Run FORGE's `pl-startup-gate` against a newly created crash-detector repo (name/owner/visibility from Matt) and recover the salvageable design/build content from the PBGv2 archive — do not re-derive the design from scratch.
3. Verify backtrader (cloudQuant fork)'s IBKR broker adapter actually works against our governed IBKR paper account before Epic 3 commits further build to it as the backbone.

---

## 16. AUTHORISATION BLOCK

**Owner decisions — resolved 2026-09-19 (chat record):**
- [x] Approve PID as a whole — **APPROVED** ("the rest is green light")
- [x] Project name — **CERBERUS**, replacing provisional ATLAS, specifically to avoid collision with PLUTUS
- [x] FORGE governs all three epics, not just the crash detector — **CONFIRMED**
- [x] PLUTUS — **RESOLVED**: separate active project, different purpose, own production timeline. Fully out of scope, no CERBERUS action of any kind.
- [x] IONOS PROD host — accepted as `prod-web-1`, Helm to confirm technically at WO-1.4, not a pre-condition
- [x] Budget ceiling — delegated to Trinity per §5 (£150/month), not an Owner-set figure

**Owner:** Matt — approved 2026-09-19, this conversation.
**Team sign-off:** not collected as a pre-condition (Lean-PBG proportionality, [[shared_rule_argus_lean_pbg]], applied here rather than a bureaucratic pre-signature ritual) — each specialist signs on effectively by taking their first dispatch (Rogue on WO-1.1 as Delivery Lead, R2D2 on WO-1.3, Trader on WO-3.1 onward).

**Update 2026-10-10:** Matt confirmed CERBERUS's crash detector rebuild (Epic 1) explicitly replaces the legacy ARGUS-coupled engine — not a parallel option, the successor. Repo created: `https://github.com/maff0000/cerberus` (public, deliberately — so ChatGPT/Architect can view and assist the build directly). RACI corrected above (Rogue, not Helm, as Delivery Lead/FORGE PL). Rogue dispatched same day to run the FORGE PL loop.

**Update 2026-10-13:** Scope-boundary decision, Matt confirmed directly: deployment mechanics (tranching/spacing/anti-step-down rules, the independent drawdown/stop rule), the regime map, and historical-analogue backtesting are CERBERUS output **consumers**, not part of Epic 1 (the crash detector itself). They move to Epic 2 as WO-2.7/2.8/2.9 rather than being folded into Epic 1's scope. The boundary is CERBERUS's own output contract (`state`, `sizing_multiplier`, `acute_rising`, `coverage_bracket`, `as_of` — see the crash detector's forthcoming `DECISION-RULE.md`): anything on the far side of that contract is Epic 2's to build, never Epic 1's.

**AUTHORISED. WO-1.1 (retire the legacy crash engine) may be dispatched now.**
