# External Architect Review — CERBERUS Crash Detector

Do not merely confirm this system is sound. We are explicitly asking for the strongest critique you can genuinely construct, and we want disagreements surfaced, not smoothed over. Format findings as **BLOCKING / MAJOR / MINOR / OPPORTUNITY / DISAGREEMENT**, each with **Evidence / Risk / Proposed change / How to prove**.

## 1. What CERBERUS is

CERBERUS is a combined wealth-management and trading system for a family's long-term capital. It has three parts; **this review is about one** — the crash detector, a standalone, advisory-only signal producing two independent readings:

- **`equity_crash`** — how stressed equity markets look.
- **`monetary_debasement`** — how stressed currency/monetary conditions look.

**These two dials are never blended.** Deliberate: different phenomena, different causes, different correct responses.

## 2. What we're trying to achieve

A real deployment decision for a substantial sum of family capital currently sitting defensive, waiting on a trustworthy signal for when to redeploy into risk assets. The non-negotiable design principle: **missing or stale data must never render as "calm."**

**The decision rule this dial is actually meant to drive is currently undefined, and that is itself the most important open gap in this whole system** — there is no stated horizon, no reading that triggers redeployment, no reading that would pull capital back out, and no stated view on which error is worse (missing a real crash vs. sitting out a false alarm). Until that exists, no calibration target exists either. We are not asking you to invent this — it is an Owner decision pending separately — but every recommendation you make should say explicitly where it depends on that answer.

The system runs live today, ingesting real public data, with every scoring threshold disclosed as an uncalibrated placeholder. An earlier, now-retired version of a related system at this house used a different architecture (master/confirmer signals, tuned against one historical event — note the n=1 and don't treat it as proven). That precedent is mentioned for context only; it is not the answer we've already decided on, and we don't want it anchoring your review.

## 3. How it currently works

1. **Ingestion**: ~30 ratified indicators, declared public sources, fetched on a schedule, stored append-only. Missing/unreachable/stale data is recorded as such (`FEED_FAILING`/`MISSING`/`STALE`).
2. **Scoring**: each indicator scales linearly between a "calm" and "stress" band into 0–1, weighted by tier (1→3, 2→2, 3→1); the dial is the weighted mean over whatever's currently available.
3. **Note the real inconsistency, not papered over**: "never silently substituted" is true at the data layer, but the scoring layer's renormalisation over present inputs *is* an implicit substitution — each absent input is effectively treated as if it would have scored the weighted mean of the others. `MATH.md` §A.5/R-5 shows this; we want your view on whether that's acceptable and, if not, what should replace it.
4. **A handful of indicators are disclosed substitutes** where the originally-specified source doesn't exist publicly.
5. We have **not** reviewed the serving/presentation layer — out of scope for this pass, same as `MATH.md` itself states.

## 4. The actual mathematics

**The complete, exact formulas are in [`crash-detector/MATH.md`](crash-detector/MATH.md)** — read it in full; it opens with ten numbered issues (R-1 through R-10) we found ourselves and want independently verified or challenged.

Headline: both dials are a **flat weighted arithmetic mean** of independently-scaled scores. No interaction between indicators, no mechanism for one extreme signal to dominate, no time dimension (trend/momentum/persistence).

**The architectural concern, stated precisely rather than as a scale comparison**: no single input or composite group of inputs can currently dominate a reading regardless of how extreme it is — every signal is just another vote in an average. Whether that matters depends on the decision rule in §2, which is exactly why that's the open question.

## 5. Data, so you can test claims rather than take our word

On request we will provide: the raw append-only reading history per indicator (CSV), `indicator-scaling.json`, and `indicator_mapping.yaml` — so you can compute real distributions and challenge the calm/stress bands with data.

## 6. What we want from you

1. Validate or refute R-1 through R-10 with your own reasoning. Find an eleventh if one exists.
2. A concrete recommendation on weighting architecture — justified against the actual decision rule once it exists, not architecture for its own sake.
3. How to handle correlated inputs being summed as if independent (R-7).
4. What to do about saturated/clamped inputs that can't signal "worse" (R-6).
5. How coverage should honestly be represented given failing/missing feeds are currently counted as "covered" (R-10).
6. A defensible calibration methodology for the placeholder bands — including whether point-in-time data vintages matter here (i.e. are we at risk of calibrating against revised data the live system could never have seen in real time).
7. Anything else that's wrong. This informs a real capital decision; we'd rather you find the flaw than the market does.
