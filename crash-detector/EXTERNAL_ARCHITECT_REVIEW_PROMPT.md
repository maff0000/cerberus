# External Architect Review — CERBERUS Crash Detector

You are being asked to independently review the mathematical and architectural soundness of a market early-warning system, and to tell us plainly what's wrong with it. This is not a request for reassurance — it's a request for the strongest critique you can genuinely construct, backed by the actual numbers.

## 1. What CERBERUS is

CERBERUS is a combined wealth-management and trading system being built for a family's long-term capital. It has three parts; **this review is about one of them** — the crash detector.

The crash detector is a standalone, advisory-only signal system. It produces two independent readings ("dials"):

- **`equity_crash`** — how stressed equity markets look right now.
- **`monetary_debasement`** — how stressed currency/monetary conditions look right now.

**These two dials are never blended into a single number.** That's a deliberate, load-bearing design decision, not an oversight — equity stress and monetary debasement are different phenomena with different causes and different correct responses, and compressing them into one score would hide which one is actually firing.

## 2. What we're trying to achieve

The family currently holds a large defensive position (gilts/cash) built up specifically *because* there was no trustworthy signal telling them when conditions warranted redeploying into risk assets. A separate, substantial sum (low seven figures) is sitting in cash waiting on exactly this signal. The explicit, non-negotiable design principle underneath everything:

> **Missing or stale data must never render as "calm."** A sensor that goes blind must say so loudly, not quietly default to "all clear."

The system was originally built in mid-2026 under a different governance framework, got orphaned when that framework was retired, and was recovered this week (342→586 commits of real history salvaged, not rebuilt from scratch) under a new delivery process. It now runs live, ingesting real public data (FRED, LBMA, Yahoo/stooq, multpl.com, and several others), with a working GUI showing real-time dial state. It is explicitly **not yet calibrated** — every scoring threshold in it today is a placeholder, disclosed as such.

## 3. How it currently works

1. **Ingestion**: ~30 ratified indicators, each with a declared public data source, fetched on a schedule, stored append-only. Missing/unreachable/stale data is recorded honestly as such (`FEED_FAILING`, `MISSING`, `STALE`), never silently substituted.
2. **Scoring**: each indicator's raw value is linearly scaled between a "calm" and "stress" band into a 0–1 score, weighted by an importance tier (1→weight 3, 2→weight 2, 3→weight 1), and the dial's final reading is the weighted average of every indicator currently available for that dial.
3. **A handful of indicators are substitutes or new constructions** where the originally-specified data source didn't exist publicly (disclosed explicitly in the code and in the document below) — e.g. a Buffett-indicator proxy built from a different FRED series than originally specified, a private-credit-stress proxy built from a liquid ETF's price action rather than the originally-envisioned (and confirmed unextractable) filing-level composite.
4. **Presentation**: a live GUI shows both dials' current value, which inputs are live/missing/failing, and why.

## 4. The actual mathematics — do not take our word for it

**The complete, exact formulas — every band, every weight, every derived calculation, pulled directly from the running code, not approximated — are in [`crash-detector/MATH.md`](crash-detector/MATH.md) in this repository.** Read that document in full; it is the authoritative source, and it opens with ten numbered issues (R-1 through R-10) that we have already found ourselves and want you to independently verify or challenge, not just accept.

The headline of the current method, so you have it before opening that file: both dials are computed as a **flat weighted arithmetic mean** of independently-scaled indicator scores. There is no interaction between indicators, no mechanism for one extreme signal to dominate regardless of what others say, and no time dimension (trend/momentum/persistence) — a dial reads whatever the blended snapshot says *right now*.

## 5. Why we built it this way, and why we think that's not good enough yet

The flat-mean approach was chosen for v1 because it's simple, transparent, fast to build, and easy to audit by hand — every number in a reading can be traced to a specific input and a specific weight. That transparency was the right priority for getting something real and honest running quickly rather than spending months designing a sophisticated model with nothing live.

**But we already know it has a real weakness, demonstrated with live numbers in `MATH.md`**: if every required, highest-importance equity input were pushed to its absolute worst reading right now, the dial would still only read **0.4987** — not even halfway to maximum. A system meant to warn of a crash that can't reach "high alarm" even when its most important inputs are screaming is not doing its job.

We know what a better architecture can look like, because an earlier, now-retired version of a related system at this house used one: a two-path model with **standalone-capable master signals** (any one of which could independently fire a full alarm) and **confirmer-only signals** (which could raise or lower confidence but could never, by themselves, calm down an alarm a master had already raised) — tuned against a real historical event (the 2022 UK gilt crisis). That system is not reusable as-is, but its design principle — *some signals should be allowed to dominate, and calm signals should never be allowed to outvote a genuine extreme* — is exactly what's missing here.

## 6. What we actually want from you

Read `MATH.md` in full. Then, specifically:

1. **Validate or refute R-1 through R-10** in that document with your own reasoning, not just agreement. If you find an eleventh problem we missed, say so.
2. **Give a concrete recommendation on the weighting architecture** — flat weighted mean vs. a master/worst-of model vs. something else entirely (e.g., a proper statistical approach that handles correlated inputs without double-counting, which R-7 flags as currently unaddressed). We want a defensible design, not just "more sophisticated."
3. **Address the correlated-inputs problem (R-7) directly** — several of the wired indicators are not statistically independent (e.g. two yield-curve spreads, four credit-spread measures) and are currently being summed as if they were. Tell us how you'd fix this.
4. **Tell us what you'd do about saturation (R-6)** — several live indicators are already clamped at maximum score and can't signal "worse" even if conditions deteriorate further.
5. **Comment on the misleading coverage metric (R-10)** — the GUI currently reports 100% equity-dial coverage and 90.5% monetary-dial coverage, but the *actually scored* weight on the monetary dial right now is only 66.7%, because failing/missing feeds are being counted as "covered." This needs fixing and we want your view on the right way to represent partial coverage honestly.
6. **Tell us how you'd approach calibrating the placeholder bands** — every calm/stress threshold in the system today is an uncalibrated guess. What's the right backtesting methodology before any of these numbers should be trusted for a real capital decision?
7. **Be direct about anything else that's wrong.** This system will inform a real, large, irreversible capital decision. We would much rather you find the flaw now than have it found by the market later.
