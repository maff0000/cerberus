# WO-1.17 COST ESTIMATE — episode-windowed historical backfill, before any real execution

**authority:** PID.md WO-1.17 entry (2026-10-16) · **written at:** `wo/CERBERUS-WO-1.17-historical-backfill-run`,
by `ROGUE` · **base:** `main` @ `ffe85e6` · **clock:** `today = 2026-10-16`
**status:** AN ESTIMATE. **NOT AN EXECUTION, NOT AN AUTHORISATION, AND NOT A STORE.**
No backfill ran to produce this document. No store was created. Zero network requests were
issued: every number below is arithmetic over constants and evidence files already in the tree.

---

## 0. THE STOP IS AT THE TOP

Three things found while computing this estimate change what "authorise the run" means, and
two of them are not about cost at all. Read them before the numbers.

1. **80% of the bisection budget buys a restatement, not a first publication** (§7.1). For
   most (series × episode) pairs the whole window predates the series' first ALFRED vintage,
   so `AlfredVintageAdapter` returns the earliest vintage ALFRED *holds* — which is a later
   restatement — and `ingestion.backfill` labels it `VINTAGE_ORIGINAL` anyway. That label's
   own docstring says it means "the figure the source FIRST published". For those pairs it
   would not be. This is the WO-1.14 forgery class arriving through a door nobody checked.
2. **There is no date list for 23 of the 34 backfillable ingredient rows** (§3). `backfill_range`
   requires the caller to supply dates; `ingestion/backfill_dates.py` generates them only for
   `month_end`/`quarter_end`, which is 11 rows. The other 23 have no calendar source in the
   tree. This is a *prerequisite*, not a cost line.
3. **A dated backfill carries no `history` array** (§8.3), so the four COMPONENT ingredients
   whose dials need history (`fred.DFII10.history` 2600 levels, `yahoo.^GSPC` 260, `fred.WALCL`
   70, `fred.CPILFESL` 8) would be backfilled value-only. Whether R2D2's replay can run at all
   on that is a question this estimate cannot answer and does not.

**Headline cost, for the shape as specified:** 190,052 GETs over 50,459 fetches,
≈36 h sequential at a 0.5 s/GET assumption. **Tractable — not the "weeks" PID.md feared.**
**Recommended shape** (§7): 70,196 GETs / 41,779 fetches, ≈18 h sequential, ≈5 h for the
longest leg if the four source types run as separate processes against separate store files.

---

## 1. Constants, read from the tree this round (not recalled)

| Constant | Value | Read from |
|---|---|---|
| `BREADTH_LOOKBACK_ROWS` | **20** | `evaluator/resolve.py:365` |
| `PROVISIONAL_PERSISTENCE` | **5** | `evaluator/resolve.py:352` |
| `BACKFILL_PACING_SECONDS` | **0.7** | `ingestion/backfill.py:177` |
| `BACKFILL_POLICY` | `RetryPolicy(max_attempts=2, timeout_seconds=45.0, backoff_seconds=4.0)` | `ingestion/backfill.py:185` |
| `MAX_VINTAGE_PROBES` | **24** | `ingestion/adapters.py:252` |
| `STABILITY_MEASURED_FROM` | **1999-01-01** | `ingestion/vintage.py` |
| `REVISION_PRONE` | **15** pairs | `ingestion/vintage.py` |
| `REVISION_STABLE` | **6** pairs | `ingestion/vintage.py` |
| `REVISION_UNDETERMINED` | **2** pairs | `ingestion/vintage.py` |

**The WO brief says "the 15 measured revision-prone FRED series". The routed number is 17, not 15.**
`build_backfill_adapter` branches on `requires_original_vintage`, which answers from
`REVISION_STABLE` and not from `REVISION_PRONE` — deliberately, fail-safe — so the 2
`REVISION_UNDETERMINED` pairs (`BAMLC0A0CM`, `BAMLH0A0HYM2`) are bisected too. They are also
the two with the shortest vintage trail, so they are disproportionately expensive *and*
disproportionately affected by §0.1. Both are counted as bisected throughout.

Every `STABILITY_MEASURED_FROM` refusal is moot here: all eight episode windows start
1999-11-02 or later, so no date in this plan falls before the measurement's left edge.

---

## 2. The window shape, and the lead-in

**Lead-in = 40 trading days = 60 calendar days, applied before every episode start.**

Derivation, in order:

1. The engine state that needs priming is the longer of the two row-counted windows:
   `max(BREADTH_LOOKBACK_ROWS, PROVISIONAL_PERSISTENCE) = max(20, 5) = 20 rows`.
2. **A row is a day, not an hour.** WO-1.3e set `CD_EVALUATE_INTERVAL_SECONDS=86400`
   (`deploy/live-dev/compose.yaml`), which is exactly what R2D2's finding B1 corrected: at the
   old 300 s cadence, 20 rows reached back ~100 minutes. At one pass a day, 20 rows is 20
   readings of a daily instrument, which is what spec §3 rule 4 asks for.
3. **Safety margin ×2 → 40 trading days.** Not arbitrary: `_breadth_rows_ago` returns `None`
   — "cannot confirm rising" — if *either* fewer than 20 rows exist *or* the row exactly 20
   back is an `UNKNOWN` row carrying no breadth (CD-RT-001). A backfilled lead-in will contain
   `UNKNOWN` rows wherever a date was refused, came back EMPTY, or failed. ×2 means up to 20
   of the 40 lead-in rows can be unusable and rule 4's breadth limb still has a resolved row
   at index 19 on the episode's first day.
4. **Trading days → calendar days at 365.25 / 252 = 1.4494.** 252 is the conventional US
   equity trading year; the replay is driven by dates that have market data, so the engine's
   rows are trading days while a window boundary is a calendar date. `40 × 1.4494 = 57.98`
   → 58, **rounded up to 60** for a clean boundary.

Episode spans are a judgement call; they are set to cover the run-up, the event, and enough
of the recovery leg to exercise DECISION-RULE's RECOVERY-both definition.

| Episode | Episode span | Window (incl. 60d lead-in) | Calendar days |
|---|---|---|---|
| 2000-02 dot-com | 2000-01-01 → 2002-12-31 | 1999-11-02 → 2002-12-31 | 1156 |
| 2007-09 GFC | 2007-06-01 → 2009-12-31 | 2007-04-02 → 2009-12-31 | 1005 |
| 2011 downgrade/euro | 2011-05-01 → 2011-12-31 | 2011-03-02 → 2011-12-31 | 305 |
| 2015-16 China/Feb low | 2015-08-01 → 2016-03-31 | 2015-06-02 → 2016-03-31 | 304 |
| Q4 2018 | 2018-10-01 → 2018-12-31 | 2018-08-02 → 2018-12-31 | 152 |
| March 2020 COVID | 2020-02-01 → 2020-04-30 | 2019-12-03 → 2020-04-30 | 150 |
| 2022 (incl. gilt) | 2022-01-01 → 2022-12-31 | 2021-11-02 → 2022-12-31 | 425 |
| April 2025 | 2025-03-01 → 2025-05-31 | 2024-12-31 → 2025-05-31 | 152 |


Total window span: 3,649 calendar days across the eight episodes (vs ~9,800 for a continuous 2000→today backfill).

---

## 3. The date list — where each calendar comes from, and the gap

`ingestion/backfill.py`'s docstring is explicit: *"`backfill_range` takes an EXPLICIT list of
observation dates. There is no cadence logic here and there must not be."* So the question is
not whether weekends are excluded — it is **who knows which dates to ask for**, per source.

**Weekends and holidays are excluded from the date LIST**, because for every source whose
calendar is a trading or business calendar the list is to be *read off a body the source
served*, and such a body simply has no row for a non-publication day. Asking for one costs a
full GET and returns EMPTY (FRED translates it to a 404 for a dated request; Cboe returns a
body with no matching row; Yahoo returns a session-less window). There is no case where
asking for a weekend buys anything.

**The four calendars are genuinely different and are not interchangeable:**

| Calendar | Who uses it | Rule | Source of the list |
|---|---|---|---|
| **FRED business days** | 9 FRED daily rows | weekdays − **federal** holidays (10/yr; 11 from 2021, Juneteenth) | ✗ no generator — must be read off a body |
| **NYSE trading days** | 3 CBOE + 7 Yahoo rows | weekdays − **exchange** holidays (9/yr; 10 from 2022, Juneteenth) | ✗ no generator — must be read off a body |
| **Weekly** | `WALCL` (Wed), `IC4WSA` (Sat), `NFCI` (Fri) | one fixed weekday per week | ✗ no generator — weekday assumed, must be confirmed |
| **Month / quarter starts** | 9 monthly + 2 quarterly rows | `day == 1`, quarters `month ∈ {1,4,7,10}` | ✓ `ingestion.backfill_dates.observation_dates` |

**FRED business days ≠ NYSE trading days, and the difference is not noise.** Good Friday is an
NYSE closure but not a federal holiday; Columbus Day and Veterans Day are federal holidays but
not NYSE closures. Treating them as one calendar would ask FRED for ~2 dates a year it has no
row for and skip ~1 a year it does. Both calendars are modelled separately throughout.

### 3.1 THE PREREQUISITE (§0.2 restated with numbers)

`observation_dates()` refuses any `as_of_rule` outside `("quarter_end", "month_end")` and
refuses any kind that is not `fred`. That covers **11 of the 34** backfillable ingredient rows.
The remaining **23** — 13 FRED `obs_date` rows, 3 CBOE, 7 Yahoo — have **no date source in the
tree**.

This is cheap to close and must be closed before execution, not during it:

| Source | How to get the real calendar | Cost |
|---|---|---|
| FRED daily/weekly (13 rows) | one undated `FredAdapter`-shaped GET of the full series body; read its observation dates | **13 GETs** |
| CBOE (3 rows) | the static `{index}_History.csv` already carries every date (`evidence/wo116_cboe_probe.json`: VIX 9,294 rows 1990-01-02→2026-10-14) | **3 GETs** |
| Yahoo (7 rows) | one `period1`/`period2` chart request per symbol spanning the windows; the session timestamps are the calendar | **7 GETs** |

**23 GETs total**, plus the code to extract and persist the lists. The holiday-deduction model
used for the estimate below is an *approximation standing in for those lists*; it is stated as
a model and not as a fact, and the real counts will differ by a few dates per window.

---

## 4. Per-date GET cost, by route

### 4.1 FRED, revision-prone/undetermined — `AlfredVintageAdapter` bisection

The docstring's `2 + ceil(log2(days))` is confirmed by reading `_acquire` directly:

```
GET 1          probe(today, absent_on_404=False)      the ceiling
GET 2          probe(observed - 1 day)                 the floor, VERIFIED not assumed
GETs 3..n      while (high - low).days > 1:            bisection to adjacent days
                   middle = low + (high - low).days // 2
```

`low` starts at `observed - 1`, `high` at `today`, so the initial span is
`S = (today - observed).days + 1`. Each step replaces the span with `span // 2` (upper branch)
or `ceil(span / 2)` (lower branch); the **worst case is the lower branch**, which is what this
estimate counts. Iterations to reach span ≤ 1 = `ceil(log2(S))`. Total = `2 + ceil(log2(S))`,
capped at `MAX_VINTAGE_PROBES = 24` (never reached here — the oldest date in the plan costs 16).

Worked example, the most expensive date in the plan — `1999-11-02`:
`S = (2026-10-16 − 1999-11-01).days = 9846`; `log2(9846) = 13.27`; `ceil = 14`; **total 16 GETs.**

Because the clock is `today`, cost falls with recency — this is per episode, not a constant:

| Episode | oldest date in window | GETs/date | newest date | GETs/date |
|---|---|---:|---|---:|
| 2000-02 | 1999-11-02 | 16 | 2002-12-31 | 16 |
| 2007-09 | 2007-04-02 | 15 | 2009-12-31 | 15 |
| 2011 | 2011-03-02 | 15 | 2011-12-31 | 15 |
| 2015-16 | 2015-06-02 | 15 | 2016-03-31 | 14 |
| Q4 2018 | 2018-08-02 | 14 | 2018-12-31 | 14 |
| March 2020 | 2019-12-03 | 14 | 2020-04-30 | 14 |
| 2022 | 2021-11-02 | 13 | 2022-12-31 | 13 |
| April 2025 | 2024-12-31 | 12 | 2025-05-31 | 11 |

### 4.2 FRED, measured-stable — 1 GET

`FredAdapter` in dated mode: one windowed request (`cosd`/`coed` on the observation date),
matched by exact date (`parse_fred_csv_for_date`). **1 GET per date per ingredient row.**

### 4.3 CBOE — 1 GET per date per index, and the body is re-downloaded every time

**Confirmed, not assumed.** `CboeAdapter` declares no `_acquire` override, so it inherits
`_BaseAdapter._acquire` — `self._parse(self._getter(self._url(), ...))`, exactly one GET — and
`_url()` is *unchanged* by `observation_date` because `cdn-api.cboe.com` honours no windowing
parameter (`evidence/wo116_cboe_probe.json`: eight parameter spellings plus two negative
controls, all byte-identical, same SHA-256). Only the parse changes.

There is **no cache**: `backfill_range` constructs a fresh adapter per date via
`build_backfill_adapter(ing, observation_date, clock)`. So each date re-downloads the entire
history file — 9,294 rows ≈ 0.4 MB for VIX. At 7,557 CBOE fetches that is **≈3 GB of transfer
to extract 7,557 rows.** The arithmetic below counts it as 1 GET/date as specified; §7.4
records it as the cheapest available code-side saving.

### 4.4 Yahoo plain-close — 1 GET per date per symbol

`YahooChartAdapter` dated mode: one `period1`/`period2` request for the named session.
**1 GET per date per symbol.** `adjclose` rows raise at construction and are out of scope (§9).


---

## 5. Series counts, per route, by name

Read this round out of `ingestion/vintage.py` (the three frozen sets) and `ingestion/catalog.py`
(`INGREDIENTS`), by importing both and asking the routing predicates — not recalled. **The unit of
cost is a CATALOG ROW, not a (series, transformation) pair**, because `backfill_range` is called per
ingredient and `build_backfill_adapter(ing, ...)` takes an `Ingredient`. That distinction changes one
route's count: see 5.2.

### 5.1 Route 4.1 — FRED bisected: **17 rows** (15 PRONE + 2 UNDETERMINED)

Membership is `requires_original_vintage(ing.ref, ing.transformation)` → `True`, i.e. the pair is
absent from `REVISION_STABLE`. One row per pair here; 17 rows, 17 distinct pairs.

**15 `REVISION_PRONE`:** `fred.IC4WSA`, `fred.NFCI`, `fred.DTWEXBGS`, `fred.UMCSENT`, `fred.M2SL.pc1`,
`fred.CPIAUCSL.pc1`, `fred.PCEPILFE.pc1`, `fred.DRTSCILM`, `fred.NCBEILQ027S`, `fred.GDP`, `fred.WALCL`,
`fred.CPILFESL`, `fred.GACDFSA066MSFRBPHI`, `fred.GACDISA066MSFRBNY`, `fred.BACTSAMFRBDAL`
**+ 2 `REVISION_UNDETERMINED`:** `fred.BAMLH0A0HYM2`, `fred.BAMLC0A0CM`
**= 15 + 2 = 17.**

§6 needs these 17 split by the calendar each one's dates come off (§3), because eleven of them are
not daily and costing them as daily would inflate the total by an order of magnitude:

| Cadence | Count | Rows |
|---|---:|---|
| FRED business-daily | **3** | `BAMLH0A0HYM2`, `BAMLC0A0CM`, `DTWEXBGS` |
| Weekly | **3** | `WALCL` (Wed), `IC4WSA` (Sat), `NFCI` (Fri) |
| Monthly (`month_end` → day 1) | **8** | `UMCSENT`, `M2SL.pc1`, `CPIAUCSL.pc1`, `PCEPILFE.pc1`, `CPILFESL`, `GACDFSA066MSFRBPHI`, `GACDISA066MSFRBNY`, `BACTSAMFRBDAL` |
| Quarterly | **3** | `GDP`, `NCBEILQ027S` (both `quarter_end`), `DRTSCILM` (quarterly SLOOS, `obs_date` rule) |

`3 + 3 + 8 + 3 = 17`. **`fred.DRTSCILM` is the row §3's calendar table does not name** — its
`as_of_rule` is `obs_date` (so it is one of the 13 rows with no generator, §3.1) while its publication
cadence is quarterly. It is costed on quarter starts, which is where FRED dates it.

### 5.2 Route 4.2 — FRED measured-stable: **7 rows** for 6 pairs

`REVISION_STABLE` holds **6 pairs**: `(DFF, None)`, `(DFII10, None)`, `(SAHMREALTIME, None)`,
`(T10Y2Y, None)`, `(T10Y3M, None)`, `(T5YIE, None)`. The catalog spends **7 rows** on them, because
`DFII10` appears twice: `fred.DFII10` (history 0, serves `real_rate_10y_tips`) and
`fred.DFII10.history` (history 2600, serves `gold_real_rate_cross`) — two source ids, two store
rows, two independent `backfill_range` calls at the same series. **6 pairs → 7 rows: `fred.DFF`,**
**`fred.DFII10`, `fred.DFII10.history`, `fred.SAHMREALTIME`, `fred.T10Y2Y`, `fred.T10Y3M`, `fred.T5YIE` = 7.**

By cadence: **6 FRED business-daily** (`DFF`, `DFII10`, `DFII10.history`, `T10Y2Y`, `T10Y3M`, `T5YIE`)
**+ 1 monthly** (`SAHMREALTIME`, `month_end`) **= 7**.

### 5.3 Route 4.3 — CBOE: **3 rows**

`kind == "cboe"` in `INGREDIENTS`, all three on the NYSE calendar:
`cboe.SKEW` (column `SKEW`), `cboe.VIX` (`CLOSE`), `cboe.VIX3M` (`CLOSE`) **= 3**.

### 5.4 Route 4.4 — Yahoo plain-close: **7 rows**

`kind == "yahoo"` AND `has_no_revision_mechanism("yahoo", ing.column)` → `True`, which is the
`NO_REVISION_MECHANISM_COLUMNS["yahoo"] = {"", "close"}` tier. All seven leave `column` at its
default `""`, which `build_adapter` resolves with `field=ing.column or "close"`:
`yahoo.HYG`, `yahoo.LQD`, `yahoo.RSP`, `yahoo.SPY`, `yahoo.^GSPC`, `yahoo.HG=F`, `yahoo.GC=F` **= 7**.

The other **51** `yahoo` rows ask for `column="adjclose"` (`yahoo.BIZD.adj` plus the 50-name
`constituent_breadth_200dma` sample) and are not in any route here (§4.4; the exclusion itself is §9's).

### 5.5 The four routes sum to §3's backfillable population

**17 + 7 + 3 + 7 = 34 rows** — the same 34 §3 counts, from the other direction: 24 FRED rows
(13 `obs_date` + 9 `month_end` + 2 `quarter_end`) + 3 CBOE + 7 Yahoo. Nothing is double-counted and
nothing backfillable is unrouted.

---

## 6. The grand total, as a visible sum

### 6.1 The method, stated once and applied to all eight episodes

1. **Daily date counts are approximated from calendar days** by §3's holiday-deduction model, with
   **one factor per calendar, used everywhere**:
   * **FRED business days: ×0.6869** — `365.25 × 5/7 = 260.89` weekdays, minus 10 federal holidays
     = `250.89`; `250.89 / 365.25 = 0.6869`.
   * **NYSE trading days: ×0.6897** — `260.89` minus 9 exchange holidays = `251.89`;
     `251.89 / 365.25 = 0.6897` (and `251.89 ≈ 252`, which is §2's conventional trading year, so the
     two models agree).
   * Juneteenth (11th federal holiday from 2021, 10th NYSE closure from 2022) would lower both
     factors by 0.0027 for the 2022 and April 2025 windows only — **under 2 dates per window**, which
     is inside the error §3.1 already declares for this model. It is **not** applied, so that the
     factors stay one-per-calendar rather than one-per-episode.
2. **Weekly, monthly and quarterly date counts are EXACT, not approximated** — they are generated,
   not estimated: Wednesdays / Saturdays / Fridays in the window for the three weekly rows, `day == 1`
   for monthly, `day == 1 and month ∈ {1,4,7,10}` for quarterly, which is `observation_dates()`'s own rule.
3. **Per-date GET cost.** Routes 4.2/4.3/4.4 are flat 1 (§4.2–4.4). Route 4.1 is
   `2 + ceil(log2((today − (observed − 1 day)).days))` evaluated per date (§4.1), `today = 2026-10-16`:
   exactly, on each generated weekly/monthly/quarterly date; and as the **mean over the window's
   weekdays** for the three business-daily rows, whose individual dates the approximation does not
   name. That mean reproduces §4.1's per-episode table exactly — it is a single integer for six of
   the eight episodes, and blends two only where §4.1's own oldest/newest columns differ
   (2015-16: 15→14, mean 14.20; April 2025: 12→11, mean 11.94).
4. **A fetch is a date asked for, for one row** — one per date per row in every route, including 4.1,
   where a single fetch costs up to 16 GETs inside one `_acquire`.

### 6.2 Dates per episode, per calendar

| Episode | Window | Cal. days | FRED bus. (×0.6869) | NYSE (×0.6897) | Weekly (Wed/Sat/Fri) | Month starts | Qtr starts | 4.1 GETs/date |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2000-02 dot-com | 1999-11-02 → 2002-12-31 | 1156 | **794** | **797** | 165/165/165 | **37** | **12** | 16 |
| 2007-09 GFC | 2007-04-02 → 2009-12-31 | 1005 | **690** | **693** | 144/143/143 | **32** | **10** | 15 |
| 2011 downgrade/euro | 2011-03-02 → 2011-12-31 | 305 | **210** | **210** | 44/44/44 | **9** | **3** | 15 |
| 2015-16 China/Feb low | 2015-06-02 → 2016-03-31 | 304 | **209** | **210** | 44/43/43 | **9** | **3** | 14.20 |
| Q4 2018 | 2018-08-02 → 2018-12-31 | 152 | **104** | **105** | 21/22/22 | **4** | **1** | 14 |
| March 2020 COVID | 2019-12-03 → 2020-04-30 | 150 | **103** | **103** | 22/21/21 | **4** | **2** | 14 |
| 2022 (incl. gilt) | 2021-11-02 → 2022-12-31 | 425 | **292** | **293** | 61/61/61 | **13** | **4** | 13 |
| April 2025 | 2024-12-31 → 2025-05-31 | 152 | **104** | **105** | 22/22/22 | **5** | **2** | 11.94 |
| **Total** | | **3649** | **2506** | **2516** | 523/521/521 | **113** | **37** | |

### 6.3 Route 4.1 cell arithmetic — it is 79% of the bill, so it is shown in full

Each cell is `Σ over the route's 17 rows of (that row's dates × that date's GET cost)`, grouped by
the four cadences of §5.1. `daily = 3 rows × FRED business days × mean cost`; `weekly = Σ cost over
the Wednesdays + the Saturdays + the Fridays`; `monthly = 8 × Σ cost over month starts`;
`quarterly = 3 × Σ cost over quarter starts`.

| Episode | 3 daily | 3 weekly | 8 monthly | 3 quarterly | **4.1 cell** |
|---|---:|---:|---:|---:|---:|
| 2000-02 dot-com | 3 × 794 × 16 = 38112 | 2640+2640+2640 = 7920 | 8 × 592 = 4736 | 3 × 192 = 576 | **51344** |
| 2007-09 GFC | 3 × 690 × 15 = 31050 | 2160+2145+2145 = 6450 | 8 × 480 = 3840 | 3 × 150 = 450 | **41790** |
| 2011 downgrade/euro | 3 × 210 × 15 = 9450 | 660+660+660 = 1980 | 8 × 135 = 1080 | 3 × 45 = 135 | **12645** |
| 2015-16 China/Feb low | 3 × 209 × 14.20 = 8902 | 625+610+610 = 1845 | 8 × 127 = 1016 | 3 × 43 = 129 | **11892** |
| Q4 2018 | 3 × 104 × 14 = 4368 | 294+308+308 = 910 | 8 × 56 = 448 | 3 × 14 = 42 | **5768** |
| March 2020 COVID | 3 × 103 × 14 = 4326 | 308+294+294 = 896 | 8 × 56 = 448 | 3 × 28 = 84 | **5754** |
| 2022 (incl. gilt) | 3 × 292 × 13 = 11388 | 793+793+793 = 2379 | 8 × 169 = 1352 | 3 × 52 = 156 | **15275** |
| April 2025 | 3 × 104 × 11.94 = 3727 | 263+262+262 = 787 | 8 × 60 = 480 | 3 × 24 = 72 | **5066** |
| **Total** | **111323** | **23167** | **13400** | **1644** | **149534** |

### 6.4 THE 32 CELLS — GETs, 8 episodes × 4 routes

| Episode | 4.1 FRED bisected (17) | 4.2 FRED stable (7) | 4.3 CBOE (3) | 4.4 Yahoo close (7) | **Episode total** |
|---|---:|---:|---:|---:|---:|
| 2000-02 dot-com | 51344 | 4801 | 2391 | 5579 | **64115** |
| 2007-09 GFC | 41790 | 4172 | 2079 | 4851 | **52892** |
| 2011 downgrade/euro | 12645 | 1269 | 630 | 1470 | **16014** |
| 2015-16 China/Feb low | 11892 | 1263 | 630 | 1470 | **15255** |
| Q4 2018 | 5768 | 628 | 315 | 735 | **7446** |
| March 2020 COVID | 5754 | 622 | 309 | 721 | **7406** |
| 2022 (incl. gilt) | 15275 | 1765 | 879 | 2051 | **19970** |
| April 2025 | 5066 | 629 | 315 | 735 | **6745** |
| **Route total** | **149534** | **15149** | **7548** | **17612** | **189843** |

Routes 4.2–4.4 are each a plain product and can be re-derived by eye:
`4.2 = 6 × FRED business days + 1 × month starts` (e.g. 2000-02: `6 × 794 + 37 = 4801`);
`4.3 = 3 × NYSE days` (`3 × 797 = 2391`); `4.4 = 7 × NYSE days` (`7 × 797 = 5579`).

**GRAND TOTAL: 189,843 GETs** = 149,534 (4.1) + 15,149 (4.2) + 7,548 (4.3) + 17,612 (4.4).

### 6.5 THE 32 CELLS — fetches (dates asked for), the same grid

| Episode | 4.1 (17) | 4.2 (7) | 4.3 (3) | 4.4 (7) | **Episode total** |
|---|---:|---:|---:|---:|---:|
| 2000-02 dot-com | 3209 | 4801 | 2391 | 5579 | **15980** |
| 2007-09 GFC | 2786 | 4172 | 2079 | 4851 | **13888** |
| 2011 downgrade/euro | 843 | 1269 | 630 | 1470 | **4212** |
| 2015-16 China/Feb low | 838 | 1263 | 630 | 1470 | **4201** |
| Q4 2018 | 412 | 628 | 315 | 735 | **2090** |
| March 2020 COVID | 411 | 622 | 309 | 721 | **2063** |
| 2022 (incl. gilt) | 1175 | 1765 | 879 | 2051 | **5870** |
| April 2025 | 424 | 629 | 315 | 735 | **2103** |
| **Route total** | **10098** | **15149** | **7548** | **17612** | **50407** |

**GRAND TOTAL: 50,407 fetches.** Route 4.1's fetch count per episode is
`3 × FRED business days + weekly dates + 8 × month starts + 3 × quarter starts`.

Two things this grid says that the GET grid hides. **Route 4.1 asks for only 10,098 of the 50,407
dates (20%) and yet accounts for 149,534 of the 189,843 GETs (79%)** — bisection, not volume, is what
it costs, and on dates alone it is the second-smallest route of the four, behind CBOE's 7,548: eleven
of its seventeen rows are monthly or quarterly and ask for very few dates. And **route 4.4 alone is
17,612 fetches (35% of all of them)** on 7 rows, because every one of those rows is daily.
The CBOE figure, 7,548 fetches, is the one §4.3 already costed at ≈3 GB of transfer.

### 6.6 Against §0's placeholder

§0 states **190,052 GETs over 50,459 fetches, ≈36 h sequential**. This section computes
**189,843 GETs over 50,407 fetches** — **-209 GETs (-0.11%) and -52 fetches (-0.10%)**. They agree, and the
residual is rounding in the daily-date approximation, not a difference of method: both are the same
four routes over the same eight windows, and the gap is far inside the few-dates-per-window error
§3.1 declares for the holiday model. **So the placeholder is not wrong, and §0 is not touched this
round** — whether to swap 190,052/50,459 for the figures above is a later round's call, recorded here
rather than applied there.

The wall-clock line reconciles too, and the arithmetic behind it is worth stating because the sentence
in §0 does not: at §0's own 0.5 s/GET, 189,843 GETs is 26.4 h of GET time, and
`BACKFILL_PACING_SECONDS = 0.7` (§1) is charged **per FETCH, not per GET** — `ingestion/backfill.py:350`,
`time.sleep(pace)` "between fetches only; a skip or a refusal paces nothing" — so 50,407 fetches add
9.8 h of deliberate idling. **26.4 h + 9.8 h = 36.2 h**, which is §0's ≈36 h. The two constants are
not alternatives; the estimate needs both, and a reader of §0 alone could reasonably have divided
190,052 by 0.5 s and got 26 h.

**None of the above is an authorisation, and no part of it has been executed.** Zero network requests
were issued to produce it: every figure is arithmetic over the frozen sets in `ingestion/vintage.py`,
the rows of `ingestion.catalog.INGREDIENTS`, the cost model read off `_acquire` in §4.1, and the
eight windows of §2.


---

## 7. The shape, examined — one finding per subsection

§0's three findings are traced here, one per subsection, each against the code and the evidence
rather than against the brief. **This round writes §7.1 only** (§0 finding 1). The lever analysis
and the recommended shape §0 points at — "70,196 GETs / 41,779 fetches, ≈18 h" — are **not derived
below and remain a placeholder**, recorded here the way §6.6 recorded its own: not applied to §0,
not this round's work.

### 7.1 §0 finding 1 is REAL. The floor check catches the opposite error, and ALFRED's per-series archive floor is invisible to it

**Verdict first: the gap is real, it is not closed by the `vintage_floor` check or by anything
else in `ingestion/`, and on the evidence already in the tree it WOULD fire during WO-1.17's
planned execution — on 10 of route 4.1's 17 rows, for 2,214 of its 10,099 fetches (33,350 GETs,
22% of the route, 17.6% of the whole plan).** No fix is proposed here; §7.1 confirms the gap.

**The rule, as the code states it.** `AlfredVintageAdapter`'s docstring: *"the EARLIEST vintage
date, within `[observation_date, today]`, at which ALFRED serves a non-empty value for this
observation date"*, followed by the claim that makes it a point-in-time fact — *"that is the first
vintage that could have published the figure, so its value is the figure as first published"*.
The first sentence is a search specification. The second is a **premise about the archive**, and
it is the premise that fails.

**The three measurement points, read off `ingestion/adapters.py:1077-1136` (opened this round, not recalled).**

1. **`adapters.py:1105` — the ceiling.** `high, found = today, probe(today, absent_on_404=False)`.
   Today's vintage. A 404 here is a real failure, not an ABSENT (the carve-out is stated at
   `adapters.py:1098`: `absent_on_404` is `False` only at this one call). If today's body carries
   no row for the observation date → `_ABSENT` → `adapters.py:1109` returns `{"unit": ...}`, EMPTY:
   "no vintage ever published this". If it does carry one → `_SERVED`, and the search continues.
2. **`adapters.py:1113-1114` — the floor.** `low = observed - timedelta(days=1)`; `beneath = probe(low)`,
   this time with `absent_on_404=True`.
3. **`adapters.py:1125-1134` — the bisection**, on the invariant the two probes establish: `low`
   ABSENT, `high` SERVED, halve to adjacent days, return the payload last seen SERVED.

**What `vintage_floor` catches.** `adapters.py:1118-1122` fires on exactly one state: the floor
probe came back `_SERVED` — *a vintage dated the day before the observation date already carried a
figure for that observation date*. That is a source publishing a period before the period ended: a
projection, a nowcast, a forecast series. The refusal is correct and the reasoning in the comment
is correct — if something served earlier than the window's left edge, the earliest-serving vintage
is outside the window and the answer would not be the earliest. **The error it catches is "served
too EARLY".**

**What it does not catch, traced for the case §0 worries about.** Take a series whose ALFRED
vintage archive begins at `floor_v` (e.g. `fred.NCBEILQ027S`, `floor_v = 2013-06-06`) and an
observation date `D` long before it (e.g. `D = 1999-12-01`, inside episode 2000-02's window):

* **Ceiling, `probe(today)` → `_SERVED`.** Today's body of a FRED series carries its whole
  back-history, restated: the archive began in 2013, the *series* did not. Measured, not assumed —
  `evidence/wo114_alfred_probe.json` records `NCBEILQ027S` `shared_span = ["1945-10-01", "2013-01-01"]`,
  i.e. the current body and the 2013 floor vintage share observations back to 1945. So the search
  proceeds.
* **Floor, `probe(1999-11-30)` → `_ABSENT`, and it is the 404 branch that makes it so.** Below
  `floor_v`, ALFRED does not serve a clamped body — it answers **404**. That is precisely what
  WO-1.14's probe measured: `tools/probe/alfred_vintage_probe.py:128-139`'s `vintage_depth` finds
  `earliest` by bisecting **on HTTP status, 200 vs 404**, so every "earliest" in the evidence file
  is the attested boundary of a uniform 404 region beneath it. `probe`'s `absent_on_404=True`
  (`adapters.py:1098`) turns that 404 into `{"unit": self._unit}` — a well-formed EMPTY — and
  `_vintage_state` reads it as `_ABSENT`.
* **Therefore `state == _SERVED` at `adapters.py:1118` is FALSE and `vintage_floor` does not fire.**
  The check's trigger condition is genuinely not met: *nothing was served before the observation
  date*, which is the one thing the check looks for. It is not that the check is wrong — it is
  answering a different question.
* **The bisection then runs normally and converges on `floor_v` itself.** Every vintage in
  `[D, floor_v)` 404s → ABSENT; `floor_v` and everything above it serves `D` (measured: the floor
  vintage's own span starts 1945-10-01, so it carries `D`). The "monotone in between" assumption
  the docstring declares holds exactly here. The returned payload is well-formed, carries
  `vintage_date = 2013-06-06`, and satisfies the stated rule **literally**: it IS the earliest
  vintage in `[D, today]` that serves a value. It is also a figure as restated **13.4 years after
  the observation**, through every benchmark revision in between.
* **And the label is applied without ever looking at it.** `ingestion/backfill.py:304-307` takes
  `vintage = VINTAGE_ORIGINAL if requires_original_vintage(ing.ref, ing.transformation)` as **ONE
  decision for the whole range, before the first fetch**; `requires_original_vintage`
  (`ingestion/vintage.py:363`) takes a series and a transformation and **no date**. So the row is
  stored claiming the warrant `VINTAGE_ORIGINAL` declares in its own comment — *"a vintage was READ.
  The warrant is the server's own vintage-dated answer"* — for a number the source first published
  in 1999 and this vintage merely re-states. §0 calls that the WO-1.14 forgery class arriving
  through a door nobody checked; the trace agrees.

**The alternative server behaviour does not close it either.** If ALFRED had *clamped* an
out-of-range `vintage_date` instead of 404ing (it clamps out-of-range `cosd`/`coed` — measured
2026-10-13, `parse_alfred_csv`'s docstring), the floor probe would return a body whose header names
a vintage we did not ask for, and `adapters.py:293` would make it `{"malformed": "vintage"}` →
`_UNREADABLE` → the fetch refused as MALFORMED at `adapters.py:1116-1117`. Still not
`vintage_floor`, and still no first-publication claim — but a refusal rather than a forgery. The
measured behaviour is the 404 branch, which is the one that answers.

**Nothing else in the tree catches it.** `grep -rn "vintage_depth\|earliest" ingestion/` returns
only docstring prose — **no runtime code reads a per-series archive floor**, and the evidence file
that holds all 17 of them is referenced by `ingestion/vintage.py:196` (`EVIDENCE_FILE`) solely to
source the `REVISION_PRONE`/`REVISION_STABLE` membership. `STABILITY_MEASURED_FROM = 1999-01-01`
gates the OTHER branch (`VINTAGE_CURRENT_ONLY`) and is one global date, not a per-series depth, so
§1's "every `STABILITY_MEASURED_FROM` refusal is moot here" stays true and buys nothing on this
branch. `build_backfill_adapter` (`ingestion/backfill_adapters.py:199-209`) routes on the same
dateless predicate.

**The gap, stated exactly.** *The implementation is faithful to its rule; the rule's premise is
never tested.* The bisection's floor is the OBSERVATION date, which bounds the answer from below
and is what makes "could not have known" impossible — but nothing bounds the answer from ABOVE, so
the rule cannot distinguish (a) *the first vintage published after the figure was published* from
(b) *the first vintage ALFRED happens to keep*. Both present identically to a bisection that reads
only SERVED/ABSENT at the observation date: a uniform 404 region beneath, a serving region above.
The distinguishing evidence exists — "does any vintage of this series exist on date V" is a
different question from "does vintage V carry observation D", and the two answers diverge exactly
in case (b) — but no probe in `_acquire` asks the first question. Designing that is a later round's;
§7.1 stops at confirming the gap.

**One thing already right, worth recording:** the served vintage is not lost. `VINTAGE_RESPONSE_SCHEMA`
(`adapters.py:134-143`) makes `vintage_date` **required alongside** `value`, and the payload is
stored whole, so every affected row will carry the 2013-06-06-style vintage inside its payload JSON
next to the `original` label. The contradiction is recorded on the row; it is simply not acted on.

#### Does it fire during WO-1.17's planned run? Measured against WO-1.14's evidence — yes, on 10 rows

`evidence/wo114_alfred_probe.json` (probed 2026-10-13) measured each bisected series' earliest
ALFRED vintage. Comparing those 17 depths with §2's eight windows and §6.1's date model gives three
outcomes per date, and all three are decided by measured facts:

* **FIRST-PUB** — `observation_date ≥ floor_v`: the earliest serving vintage is a real publication
  event. The rule's premise holds; nothing to fix.
* **RESTATEMENT** (the §0 finding) — `floor_obs ≤ observation_date < floor_v` *and* the floor
  vintage's own span covers the date (so it is attested to serve it): bisection returns `floor_v`,
  stored as `VINTAGE_ORIGINAL`. **A false first-publication claim.**
* **EMPTY** — `observation_date < floor_obs`, the earliest observation ALFRED's body holds at all:
  the ceiling probe comes back ABSENT and `adapters.py:1109` returns EMPTY. Honest, and `backfill.py`
  records the date as `failed`/EMPTY — but it is a date the backfill does not have.

| row | cadence | earliest ALFRED vintage | that vintage's earliest obs | episodes with a restatement band | RESTATEMENT fetches | EMPTY fetches | FIRST-PUB fetches | worst obs→vintage lag |
|---|---|---|---|---|---:|---:|---:|---:|
| `fred.DTWEXBGS` | bus-daily | **2019-02-04** | 2006-01-02 | 2007-09, 2011, 2015-16, Q4 2018 | **1213** | 794 | 499 | **11.8 y** |
| `fred.NFCI` | weekly (Fri) | **2011-05-25** | 1973-01-05 | 2000-02, 2007-09, 2011 | **320** | 0 | 201 | **11.6 y** |
| `fred.IC4WSA` | weekly (Sat) | **2009-05-28** | 1967-01-28 | 2000-02, 2007-09 | **277** | 0 | 244 | **9.6 y** |
| `fred.WALCL` | weekly (Wed) | **2011-07-07** | 2002-12-18 | 2000-02, 2007-09, 2011 | **165** | 163 | 195 | **8.6 y** |
| `fred.GACDFSA066MSFRBPHI` | monthly | **2015-04-16** | 1968-05-01 | 2000-02, 2007-09, 2011 | **78** | 0 | 35 | **15.4 y** |
| `fred.GACDISA066MSFRBNY` | monthly | **2014-03-17** | 2001-07-01 | 2000-02, 2007-09, 2011 | **59** | 19 | 35 | **12.7 y** |
| `fred.BACTSAMFRBDAL` | monthly | **2016-01-25** | 2004-06-01 | 2007-09, 2011, 2015-16 | **48** | 37 | 28 | **8.7 y** |
| `fred.NCBEILQ027S` | quarterly | **2013-06-06** | 1945-10-01 | 2000-02, 2007-09, 2011 | **25** | 0 | 12 | **13.4 y** |
| `fred.DRTSCILM` | quarterly | **2010-04-20** | 1990-04-01 | 2000-02, 2007-09 | **22** | 0 | 15 | **10.3 y** |
| `fred.PCEPILFE.pc1` | monthly | **2000-08-01** | 1960-01-01 | 2000-02 (part) | **7** | 0 | 106 | 0.7 y |
| `fred.BAMLH0A0HYM2` | bus-daily | **2023-10-16** | 2023-10-16 | — | 0 | **2402** | 104 | — |
| `fred.BAMLC0A0CM` | bus-daily | **2023-10-16** | 2023-10-16 | — | 0 | **2402** | 104 | — |
| `fred.UMCSENT` | monthly | 1998-07-31 | 1952-11-01 | — | 0 | 0 | 113 | — |
| `fred.M2SL.pc1` | monthly | 1990-01-01 | 1960-01-01 | — | 0 | 0 | 113 | — |
| `fred.CPIAUCSL.pc1` | monthly | 1990-01-01 | 1989-05-01 | — | 0 | 0 | 113 | — |
| `fred.CPILFESL` | monthly | 1996-12-12 | 1957-01-01 | — | 0 | 0 | 113 | — |
| `fred.GDP` | quarterly | 1991-12-04 | 1959-01-01 | — | 0 | 0 | 37 | — |
| **Total — 17 rows** | | | | | **2,214** | **5,817** | **2,068** | |

The fetch total is **10,099** against §6.5's **10,098** for route 4.1 and the GET total is
**149,549** against §6.4's **149,534** — the same method (§6.1) applied per row, so the split
reconciles with the grid rather than replacing it.

**Read, in order:**

1. **10 of 17 bisected rows have a restatement band inside WO-1.17's windows** — `DTWEXBGS`, `NFCI`,
   `IC4WSA`, `WALCL`, `GACDFSA066MSFRBPHI`, `GACDISA066MSFRBNY`, `BACTSAMFRBDAL`, `NCBEILQ027S`,
   `DRTSCILM`, `PCEPILFE.pc1`. **2,214 fetches / 33,350 GETs** would be stored as `VINTAGE_ORIGINAL`
   while carrying a restatement: **22% of route 4.1's fetches, 22.3% of its GETs, 17.6% of the whole
   plan's 189,843.** The lags are not marginal — **8.6 to 15.4 years** of revision between the
   observation and the vintage that answers for it.
2. **The two `REVISION_UNDETERMINED` rows fail differently, and worse for coverage.** `BAMLH0A0HYM2`
   and `BAMLC0A0CM` have an ALFRED archive starting **2023-10-16** whose floor vintage holds exactly
   ONE observation (its own date), and the current body holds 784/783 — which is 2023-10-16 → the
   probe date in business days. So ALFRED's body for these two appears to begin in 2023, and the
   **ceiling** probe returns ABSENT for every date in **seven of the eight episodes**: 4,804 fetches
   → EMPTY, no reading, no mislabel. Only April 2025 is inside their archive. *This is the one
   inferential step in §7.1* — the evidence measures the current body's observation COUNT, not its
   first date — and **the verdict does not rest on it**: the 2,214-fetch restatement band is
   established from measured depths and measured floor-vintage spans alone, on rows where
   `shared_span` confirms the current body reaches at least as deep.
3. **§0's "80% of the bisection budget buys a restatement" survives as a number and needs its
   composition corrected.** Not-a-first-publication is **81.1%** of route 4.1's GETs — but that is
   **22.3% restatement + 58.8% EMPTY**, and the EMPTY majority is three rows (the two BAML plus
   `DTWEXBGS` before 2006) asking for data ALFRED does not hold at all. Per §6.6's convention this
   is recorded here, **not applied to §0**.
4. **The 5 clean rows are clean for one reason: their archive predates 1999-11-02**, the oldest date
   in the plan — `UMCSENT` 1998-07-31, `M2SL.pc1` and `CPIAUCSL.pc1` at or before the probe's 1990
   floor, `CPILFESL` 1996-12-12, `GDP` 1991-12-04. Nothing about those five rows is safer by
   construction; they are on the right side of an accident of ALFRED's archive.
5. **`PCEPILFE.pc1` is the near-miss that shows the band is an over-count at its right edge**: its
   7 affected dates sit within 0.7 y of its archive floor, and a date whose real first publication
   falls after the floor is answered correctly by the bisection (which climbs past the floor vintage
   when the floor vintage does not carry it). The band criterion above already requires the floor
   vintage to be attested as carrying the date, which is why the count is 7 and not 8.

**Not claimed here.** That the restatement differs materially from first publication for these 10
rows is NOT asserted: `evidence/wo114_alfred_probe.json` measured `differing` per series at other
vintage pairs, and whether a 1999 observation's 2013 restatement moves a DECISION-RULE threshold is
a separate question from whether the row may claim it was first published. §7.1 is about the claim.
