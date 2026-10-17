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
2. **There is no date list for 24 of the 35 backfillable ingredient rows** (§3). `backfill_range`
   requires the caller to supply dates; `ingestion/backfill_dates.py` generates them only for
   `month_end`/`quarter_end`, which is 11 rows. The other 24 have no calendar source in the
   tree. This is a *prerequisite*, not a cost line.
   **THIS PREREQUISITE IS NOW CLOSED, and this item is left standing only as the record of
   what was found.** All three date-list readers are built and committed in
   `ingestion/backfill_calendar.py` — FRED (`fa18e30`), CBOE (`613fea1`), Yahoo plain-close
   (`0f0bb2f`), with the counts corrected to DRTSCIS's 14th `obs_date` row in `9988994`. Nothing
   below reads on the assumption that it is still open; §3.1 carries the same note with the
   numbers. Whether this item is struck through or restated as RESOLVED is a later round's call,
   together with §6's arithmetic.
3. **A dated backfill carries no `history` array** (§8), so the **seven** COMPONENT ingredients
   whose dials need history (`fred.WALCL` 70, `fred.CPILFESL` 8, `fred.GACDFSA066MSFRBPHI` 1000,
   `fred.GACDISA066MSFRBNY` 1000, `fred.BACTSAMFRBDAL` 1000, `fred.DFII10.history` 2600,
   `yahoo.^GSPC` 260 — not the four originally named here; the three regional-Fed survey rows
   behind `ism_manufacturing` were missed on first count and are corrected in §8.1) would be
   backfilled value-only, across four indicators. §8.2 found this is BUILDABLE at zero extra
   GETs, not attempted in this WO's scope. §8.3 answers the "can R2D2's replay run on that"
   question §0 originally declined: necessary but not sufficient for `monetisation_flag` and
   `ism_manufacturing` (both carry an independent floor of their own, in the sources and in
   `wiring.py`), sufficient for `spx_vs_200dma`, and irrelevant on its own to
   `gold_real_rate_cross` (its other leg, `lbma.gold_fix_usd.history`, has no backfill route at
   all — §9's scope question, not §8's).

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
refuses any kind that is not `fred`. That covers **11 of the 35** backfillable ingredient rows.
The remaining **24** — 14 FRED `obs_date` rows, 3 CBOE, 7 Yahoo — have **no date source in the
tree**.

This is cheap to close and must be closed before execution, not during it:

| Source | How to get the real calendar | Cost |
|---|---|---|
| FRED `obs_date` (14 rows) | one undated `FredAdapter`-shaped GET of the full series body; read its observation dates | **14 GETs** |
| CBOE (3 rows) | the static `{index}_History.csv` already carries every date (`evidence/wo116_cboe_probe.json`: VIX 9,294 rows 1990-01-02→2026-10-14) | **3 GETs** |
| Yahoo (7 rows) | one `period1`/`period2` chart request per symbol spanning the windows; the session timestamps are the calendar | **7 GETs** |

**24 GETs total**, plus the code to extract and persist the lists. The holiday-deduction model
used for the estimate below is an *approximation standing in for those lists*; it is stated as
a model and not as a fact, and the real counts will differ by a few dates per window.

**THE THREE READERS IN THIS TABLE ARE NO LONGER A FORECAST — they are built and committed**, so
the future tense above is the tense of the estimate as written and not a statement about the
tree. `ingestion/backfill_calendar.py` holds all three: `fred_observation_dates` (`fa18e30`),
`cboe_observation_dates` (`613fea1`) and `yahoo_observation_dates` (`0f0bb2f`), the last of which
completes the 24; `9988994` carried its counts to DRTSCIS's 14th `obs_date` row. Two things the
built readers say that this table did not: the 14 FRED rows cost 14 GETs for only **13 distinct
calendars** (`fred.DFII10` and `fred.DFII10.history` are two catalog rows over one series, and
deduplicating them is the caller's business, not the reader's), and the 51 `adjclose` Yahoo rows
are refused BY NAME rather than silently absent from the count. What remains owed is not the
readers but the *persistence* of their output, and the replacement of the holiday-deduction
model below by the real lists — which is §6's round, not this one.

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

### 5.1 Route 4.1 — FRED bisected: **18 rows** (16 PRONE + 2 UNDETERMINED)

Membership is `requires_original_vintage(ing.ref, ing.transformation)` → `True`, i.e. the pair is
absent from `REVISION_STABLE`. One row per pair here; 18 rows, 18 distinct pairs.

**16 `REVISION_PRONE`:** `fred.IC4WSA`, `fred.NFCI`, `fred.DTWEXBGS`, `fred.UMCSENT`, `fred.M2SL.pc1`,
`fred.CPIAUCSL.pc1`, `fred.PCEPILFE.pc1`, `fred.DRTSCILM`, `fred.DRTSCIS`, `fred.NCBEILQ027S`, `fred.GDP`,
`fred.WALCL`, `fred.CPILFESL`, `fred.GACDFSA066MSFRBPHI`, `fred.GACDISA066MSFRBNY`, `fred.BACTSAMFRBDAL`
**+ 2 `REVISION_UNDETERMINED`:** `fred.BAMLH0A0HYM2`, `fred.BAMLC0A0CM`
**= 16 + 2 = 18.**

`fred.DRTSCIS` is the 16th, added by WO-1.19 as the small-firm leg of `sloos_bank_lending`, and it
is `REVISION_PRONE` **because it was probed and measured so, not because its sibling is**: 18 of
the 81 observations its first ALFRED vintage (2010-04-20) shares with today's differ materially,
the largest 1991-10-01 first published 5.2 and now 7.0 (`ingestion/vintage.py`, which holds the
probe's own figures and notes that `DRTSCILM`'s are different ones).

§6 needs these 18 split by the calendar each one's dates come off (§3), because eleven of them are
not daily and costing them as daily would inflate the total by an order of magnitude:

| Cadence | Count | Rows |
|---|---:|---|
| FRED business-daily | **3** | `BAMLH0A0HYM2`, `BAMLC0A0CM`, `DTWEXBGS` |
| Weekly | **3** | `WALCL` (Wed), `IC4WSA` (Sat), `NFCI` (Fri) |
| Monthly (`month_end` → day 1) | **8** | `UMCSENT`, `M2SL.pc1`, `CPIAUCSL.pc1`, `PCEPILFE.pc1`, `CPILFESL`, `GACDFSA066MSFRBPHI`, `GACDISA066MSFRBNY`, `BACTSAMFRBDAL` |
| Quarterly | **4** | `GDP`, `NCBEILQ027S` (both `quarter_end`), `DRTSCILM` and `DRTSCIS` (the two quarterly SLOOS legs, both `obs_date` rule) |

`3 + 3 + 8 + 4 = 18`. **`fred.DRTSCILM` and `fred.DRTSCIS` are the rows §3's calendar table does not
name** — their `as_of_rule` is `obs_date` (so they are two of the 14 rows with no generator, §3.1) while
their publication cadence is quarterly. They are costed on quarter starts, which is where FRED dates
them. The two legs are costed IDENTICALLY because they measure identically: `ingestion/catalog.py`
gives them the same `as_of_rule` (`obs_date`, the `_f` default — neither carries a `rule=`) and the same
`poll_seconds` (86,400), and `ingestion/release_calendar.py` records both legs' first-vintage lag at
the same measured 30–42 days from quarter start over 15 real quarters, because they print together as
one SLOOS release.

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

**18 + 7 + 3 + 7 = 35 rows** — the same 35 §3 counts, from the other direction: 25 FRED rows
(14 `obs_date` + 9 `month_end` + 2 `quarter_end`) + 3 CBOE + 7 Yahoo. Nothing is double-counted and
nothing backfillable is unrouted.

**The FRED sub-total moved too, and it is 25 and not 24.** Counted this round off the catalog rather
than carried forward: `len([i for i in INGREDIENTS if i.kind == "fred"]) == 25`, splitting by
`as_of_rule` into **14 `obs_date` + 9 `month_end` + 2 `quarter_end` = 25**. `DRTSCIS` is an
ADDITIONAL catalog row, not a reclassified one — no row changed its `as_of_rule` — so the only
sub-count that moves is `obs_date` (13 → 14) and the FRED total moves with it (24 → 25). The old
text's "24 FRED rows" was the arithmetic of the old catalog and added up correctly then; it does not
now, and 14 + 9 + 2 = 25 is both the route sum (18 bisected + 7 measured-stable = 25) and the
catalog count, from two independent directions.

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

Each cell is `Σ over the route's 18 rows of (that row's dates × that date's GET cost)`, grouped by
the four cadences of §5.1. `daily = 3 rows × FRED business days × mean cost`; `weekly = Σ cost over
the Wednesdays + the Saturdays + the Fridays`; `monthly = 8 × Σ cost over month starts`;
`quarterly = 4 × Σ cost over quarter starts`.

The quarterly multiplier is **4, not 3**: `fred.DRTSCIS` is the fourth quarterly bisected row (§5.1).
Its per-date cost needs no separate column because §4.1's formula —
`2 + ceil(log2((today − (observed − 1 day)).days))` — reads only the observation date and the clock;
no series identity enters `_acquire`'s span. At every quarter-start date in every window DRTSCIS
therefore costs exactly what `fred.DRTSCILM` costs, and the quarterly sub-total below is the old
three-row figure × 4/3 exactly. Daily, weekly and monthly columns are untouched.

| Episode | 3 daily | 3 weekly | 8 monthly | 4 quarterly | **4.1 cell** |
|---|---:|---:|---:|---:|---:|
| 2000-02 dot-com | 3 × 794 × 16 = 38112 | 2640+2640+2640 = 7920 | 8 × 592 = 4736 | 4 × 192 = 768 | **51536** |
| 2007-09 GFC | 3 × 690 × 15 = 31050 | 2160+2145+2145 = 6450 | 8 × 480 = 3840 | 4 × 150 = 600 | **41940** |
| 2011 downgrade/euro | 3 × 210 × 15 = 9450 | 660+660+660 = 1980 | 8 × 135 = 1080 | 4 × 45 = 180 | **12690** |
| 2015-16 China/Feb low | 3 × 209 × 14.20 = 8902 | 625+610+610 = 1845 | 8 × 127 = 1016 | 4 × 43 = 172 | **11935** |
| Q4 2018 | 3 × 104 × 14 = 4368 | 294+308+308 = 910 | 8 × 56 = 448 | 4 × 14 = 56 | **5782** |
| March 2020 COVID | 3 × 103 × 14 = 4326 | 308+294+294 = 896 | 8 × 56 = 448 | 4 × 28 = 112 | **5782** |
| 2022 (incl. gilt) | 3 × 292 × 13 = 11388 | 793+793+793 = 2379 | 8 × 169 = 1352 | 4 × 52 = 208 | **15327** |
| April 2025 | 3 × 104 × 11.94 = 3727 | 263+262+262 = 787 | 8 × 60 = 480 | 4 × 24 = 96 | **5090** |
| **Total** | **111323** | **23167** | **13400** | **2192** | **150082** |

The quarterly total moves 1644 → 2192 (= 1644 × 4/3, +548) and that +548 is the whole of the
4.1 route's change, 149534 → 150082.

### 6.4 THE 32 CELLS — GETs, 8 episodes × 4 routes

| Episode | 4.1 FRED bisected (18) | 4.2 FRED stable (7) | 4.3 CBOE (3) | 4.4 Yahoo close (7) | **Episode total** |
|---|---:|---:|---:|---:|---:|
| 2000-02 dot-com | 51536 | 4801 | 2391 | 5579 | **64307** |
| 2007-09 GFC | 41940 | 4172 | 2079 | 4851 | **53042** |
| 2011 downgrade/euro | 12690 | 1269 | 630 | 1470 | **16059** |
| 2015-16 China/Feb low | 11935 | 1263 | 630 | 1470 | **15298** |
| Q4 2018 | 5782 | 628 | 315 | 735 | **7460** |
| March 2020 COVID | 5782 | 622 | 309 | 721 | **7434** |
| 2022 (incl. gilt) | 15327 | 1765 | 879 | 2051 | **20022** |
| April 2025 | 5090 | 629 | 315 | 735 | **6769** |
| **Route total** | **150082** | **15149** | **7548** | **17612** | **190391** |

Routes 4.2–4.4 are each a plain product and can be re-derived by eye:
`4.2 = 6 × FRED business days + 1 × month starts` (e.g. 2000-02: `6 × 794 + 37 = 4801`);
`4.3 = 3 × NYSE days` (`3 × 797 = 2391`); `4.4 = 7 × NYSE days` (`7 × 797 = 5579`).

**GRAND TOTAL: 190,391 GETs** = 150,082 (4.1) + 15,149 (4.2) + 7,548 (4.3) + 17,612 (4.4).

### 6.5 THE 32 CELLS — fetches (dates asked for), the same grid

| Episode | 4.1 (18) | 4.2 (7) | 4.3 (3) | 4.4 (7) | **Episode total** |
|---|---:|---:|---:|---:|---:|
| 2000-02 dot-com | 3221 | 4801 | 2391 | 5579 | **15992** |
| 2007-09 GFC | 2796 | 4172 | 2079 | 4851 | **13898** |
| 2011 downgrade/euro | 846 | 1269 | 630 | 1470 | **4215** |
| 2015-16 China/Feb low | 841 | 1263 | 630 | 1470 | **4204** |
| Q4 2018 | 413 | 628 | 315 | 735 | **2091** |
| March 2020 COVID | 413 | 622 | 309 | 721 | **2065** |
| 2022 (incl. gilt) | 1179 | 1765 | 879 | 2051 | **5874** |
| April 2025 | 426 | 629 | 315 | 735 | **2105** |
| **Route total** | **10135** | **15149** | **7548** | **17612** | **50444** |

**GRAND TOTAL: 50,444 fetches.** Route 4.1's fetch count per episode is
`3 × FRED business days + weekly dates + 8 × month starts + 4 × quarter starts`.
Only the last term changed: DRTSCIS asks for its episode's own quarter-start dates and nothing else,
so route 4.1 gains exactly **+37 fetches** (10,098 → 10,135) — and 37 is §6.2's own Total "Qtr starts"
column, which is the cross-check that this grid and §6.2 are counting the same dates.

Two things this grid says that the GET grid hides. **Route 4.1 asks for only 10,135 of the 50,444
dates (20.1%) and yet accounts for 150,082 of the 190,391 GETs (78.8%)** — bisection, not volume, is
what it costs, and on dates alone it is still the second-smallest route of the four, behind CBOE's
7,548: twelve of its eighteen rows are monthly or quarterly and ask for very few dates. Adding the
fourth quarterly row does not move either share by a whole point (it was 10,098/50,407 = 20.0% and
149,534/189,843 = 78.8%), because a quarterly row is the cheapest kind of row this route has.
And **route 4.4 alone is 17,612 fetches (35% of all of them)** on 7 rows, because every one of those
rows is daily.
The CBOE figure, 7,548 fetches, is the one §4.3 already costed at ≈3 GB of transfer.

### 6.6 Against §0's placeholder

§0 states **190,052 GETs over 50,459 fetches, ≈36 h sequential** — a placeholder written before
`fred.DRTSCIS` was identified as the 18th bisected row and the 4th quarterly one (§5.1). This section
now computes **190,391 GETs over 50,444 fetches** — **+339 GETs (+0.18%) and -15 fetches (-0.03%)**.

**This is the real arithmetic after the DRTSCIS correction, not the earlier reconciliation restated,
and the two counts no longer miss the placeholder in the same direction.** Before the fourth quarterly
row, the computed figures were *both* smaller than §0's (-209 GETs, -52 fetches). Now the computed GET
total is **larger** than §0's headline while the computed fetch total is still smaller, and both gaps
are narrower than they were. The residual is still rounding in the daily-date approximation rather
than a difference of method — both figures are the same four routes over the same eight windows, and
±339 GETs over 190k is far inside the few-dates-per-window error §3.1 declares for the holiday model —
so the placeholder is not *wrong*. But its direction has flipped: 190,052 is no longer a slight
over-statement of the computed GET cost, it is an under-statement of it by 339.

**§0 is not touched this round.** A reader comparing the headline at the top of this document against
this section should therefore read §0's 190,052/50,459 as the pre-DRTSCIS placeholder and the
190,391/50,444 here as the current computed total; whether to swap them is a later round's call,
recorded here rather than applied there.

The wall-clock line still reconciles, and the arithmetic behind it is worth stating because the
sentence in §0 does not: at §0's own 0.5 s/GET, 190,391 GETs is 95,196 s = **26.4 h** of GET time, and
`BACKFILL_PACING_SECONDS = 0.7` (§1) is charged **per FETCH, not per GET** — `ingestion/backfill.py:350`,
`time.sleep(pace)` "between fetches only; a skip or a refusal paces nothing" — so 50,444 fetches add
35,311 s = **9.8 h** of deliberate idling. **26.44 h + 9.81 h = 36.25 h**, which is still §0's ≈36 h.
Both components were recomputed from the new totals rather than carried over, and neither moved at
one decimal place: the DRTSCIS row adds 274 s of GET time and 26 s of pacing, taking the total from
36.17 h to 36.25 h — **+0.08 h, about five minutes**, so the ≈36 h headline holds even though the GET
count it sits beside does not. The two constants are not alternatives; the estimate needs both, and a
reader of §0 alone could reasonably have divided 190,052 by 0.5 s and got 26 h.

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
planned execution — on 11 of route 4.1's 18 rows, for 2,236 of its 10,136 fetches (33,692 GETs,
22.4% of the route, 17.7% of the whole plan).** No fix is proposed here; §7.1 confirms the gap.

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
that holds all 18 of them is referenced by `ingestion/vintage.py:196` (`EVIDENCE_FILE`) solely to
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

#### Does it fire during WO-1.17's planned run? Measured against WO-1.14's evidence — yes, on 11 rows

`evidence/wo114_alfred_probe.json` (probed 2026-10-13) measured each bisected series' earliest
ALFRED vintage. Comparing those 18 depths with §2's eight windows and §6.1's date model gives three
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
| `fred.DRTSCIS` | quarterly | **2010-04-20** | 1990-04-01 | 2000-02, 2007-09 | **22** | 0 | 15 | **10.3 y** |
| `fred.PCEPILFE.pc1` | monthly | **2000-08-01** | 1960-01-01 | 2000-02 (part) | **7** | 0 | 106 | 0.7 y |
| `fred.BAMLH0A0HYM2` | bus-daily | **2023-10-16** | 2023-10-16 | — | 0 | **2402** | 104 | — |
| `fred.BAMLC0A0CM` | bus-daily | **2023-10-16** | 2023-10-16 | — | 0 | **2402** | 104 | — |
| `fred.UMCSENT` | monthly | 1998-07-31 | 1952-11-01 | — | 0 | 0 | 113 | — |
| `fred.M2SL.pc1` | monthly | 1990-01-01 | 1960-01-01 | — | 0 | 0 | 113 | — |
| `fred.CPIAUCSL.pc1` | monthly | 1990-01-01 | 1989-05-01 | — | 0 | 0 | 113 | — |
| `fred.CPILFESL` | monthly | 1996-12-12 | 1957-01-01 | — | 0 | 0 | 113 | — |
| `fred.GDP` | quarterly | 1991-12-04 | 1959-01-01 | — | 0 | 0 | 37 | — |
| **Total — 18 rows** | | | | | **2,236** | **5,817** | **2,083** | |

The fetch total is **10,136** against §6.5's **10,135** for route 4.1 and the GET total is
**150,097** against §6.4's **150,082** — the same method (§6.1) applied per row, so the split
reconciles with the grid rather than replacing it (the +1 fetch and +15 GETs are §6.1's daily-date
rounding, unchanged in size by the new row).

`fred.DRTSCIS`'s row is `fred.DRTSCILM`'s row repeated, and that was checked rather than assumed:
same cadence, same measured archive floor (`vintage_depth.earliest = 2010-04-20` for both), same
floor-vintage span, same `as_of_rule`, and §6.3's per-date cost
`2 + ceil(log2((today − (observed − 1 day)).days))` reads only the observation date and the clock —
no series identity enters `_acquire`'s span. So the two rows contribute **identical per-episode
figures**: 37 fetches / 548 GETs each, split 22 restatement fetches (the 12 + 10 quarter starts of
2000-02 and 2007-09, costing `12 × 16 + 10 × 15 = 342` GETs) and 15 FIRST-PUB fetches across the
six later episodes, all of which begin after 2010-04-20. That **+37 / +548 / +342** is the whole of
this section's change, and the first two match §6.5's own +37 and §6.3's own +548 exactly.

**Read, in order:**

1. **11 of 18 bisected rows have a restatement band inside WO-1.17's windows** — `DTWEXBGS`, `NFCI`,
   `IC4WSA`, `WALCL`, `GACDFSA066MSFRBPHI`, `GACDISA066MSFRBNY`, `BACTSAMFRBDAL`, `NCBEILQ027S`,
   `DRTSCILM`, `DRTSCIS`, `PCEPILFE.pc1`. **2,236 fetches / 33,692 GETs** would be stored as
   `VINTAGE_ORIGINAL` while carrying a restatement: **22.1% of route 4.1's fetches, 22.4% of its
   GETs, 17.7% of the whole plan's 190,391.** The lags are not marginal — **8.6 to 15.4 years** of
   revision between the observation and the vintage that answers for it. `DRTSCIS` is the eleventh,
   and it qualifies on its own measured record rather than by analogy to its sibling:
   `evidence/wo114_alfred_probe.json`'s DRTSCIS entry (probed 2026-10-16, added by WO-1.19's
   `--merge`) gives `vintage_depth.earliest = 2010-04-20` and
   `first_vintage_span = ["1990-04-01", "2010-04-01"]`, so the floor vintage is **attested** to
   carry every quarter-start in the band — the criterion finding 5 turns on — while `shared_span`
   back to 1990-04-01 confirms the current body reaches at least as deep, so the ceiling probe
   serves and none of its dates go EMPTY. Both the criterion's inputs are identical to
   `DRTSCILM`'s, which is what two legs of one SLOOS release printing on one vintage schedule
   should look like.
2. **The two `REVISION_UNDETERMINED` rows fail differently, and worse for coverage.** `BAMLH0A0HYM2`
   and `BAMLC0A0CM` have an ALFRED archive starting **2023-10-16** whose floor vintage holds exactly
   ONE observation (its own date), and the current body holds 784/783 — which is 2023-10-16 → the
   probe date in business days. So ALFRED's body for these two appears to begin in 2023, and the
   **ceiling** probe returns ABSENT for every date in **seven of the eight episodes**: 4,804 fetches
   → EMPTY, no reading, no mislabel. Only April 2025 is inside their archive. *This is the one
   inferential step in §7.1* — the evidence measures the current body's observation COUNT, not its
   first date — and **the verdict does not rest on it**: the 2,236-fetch restatement band is
   established from measured depths and measured floor-vintage spans alone, on rows where
   `shared_span` confirms the current body reaches at least as deep.
3. **§0's "80% of the bisection budget buys a restatement" survives as a number and needs its
   composition corrected.** Not-a-first-publication is **81.0%** of route 4.1's GETs — but that is
   **22.4% restatement + 58.6% EMPTY**, and the EMPTY majority is three rows (the two BAML plus
   `DTWEXBGS` before 2006) asking for data ALFRED does not hold at all. Re-derived against §6's
   larger route total: the restatement share rises a tenth of a point and the EMPTY share falls
   two, because the 18th row adds 342 restatement GETs and **no** EMPTY ones to a denominator that
   grew by 548. Per §6.6's convention this
   is recorded here, **not applied to §0**.
4. **The 5 clean rows are clean for one reason: their archive predates 1999-11-02**, the oldest date
   in the plan — `UMCSENT` 1998-07-31, `M2SL.pc1` and `CPIAUCSL.pc1` at or before the probe's 1990
   floor, `CPILFESL` 1996-12-12, `GDP` 1991-12-04. Still **five**, not six: the 18th row joined the
   restatement band rather than this group, so the route partitions **11 restatement + 2
   `REVISION_UNDETERMINED` + 5 clean = §5.1's 18**. Nothing about those five rows is safer by
   construction; they are on the right side of an accident of ALFRED's archive.
5. **`PCEPILFE.pc1` is the near-miss that shows the band is an over-count at its right edge**: its
   7 affected dates sit within 0.7 y of its archive floor, and a date whose real first publication
   falls after the floor is answered correctly by the bisection (which climbs past the floor vintage
   when the floor vintage does not carry it). The band criterion above already requires the floor
   vintage to be attested as carrying the date, which is why the count is 7 and not 8.

**Not claimed here.** That the restatement differs materially from first publication for these 11
rows is NOT asserted: `evidence/wo114_alfred_probe.json` measured `differing` per series at other
vintage pairs, and whether a 1999 observation's 2013 restatement moves a DECISION-RULE threshold is
a separate question from whether the row may claim it was first published. §7.1 is about the claim.

### 7.2 CBOE's missing-value convention, MEASURED rather than inherited — and unlike §7.1 it is closed, with no number to revise

**Verdict first: there is no gap here. The convention `ingestion/adapters.py` has asserted since
WO-1.16 — CBOE publishes no missing-data marker, so a non-session is an ABSENT ROW and never a
blank cell — is now attested across all three catalog bodies whole rather than across the one
month the adapter docstring cites. `CBOE_MISSING_VALUE_TOKENS = ("",)` is a guard for a body that
MIGHT one day carry a blank, not a condition ever observed. Nothing in §3.1, §4.3 or §6 changes.**

§7.2 and §7.3 are **not** §0's findings 2 and 3 — those are still unwritten, and §7's preamble
stands as the record of the round that wrote §7.1. These two come from elsewhere: they are what
this WO's CBOE and Yahoo date-list rounds turned up while building the §3.1 readers, and they are
recorded here for §6.6's reason — the finding belongs in the document whether or not it moves a
figure in it. Both of these do not, and say so below rather than leaving the question open.

**The measurement.** Building `cboe_body_dates` / `cboe_observation_dates`
(`ingestion/backfill_calendar.py:257`, `:321`) required all three CBOE history bodies to be fetched
whole, for real, on 2026-10-16 — not a fixture, not a month's excerpt. Read across every row of
every column:

| body | header | span | rows | empty cells | unreadable dates | duplicate dates | short rows |
|---|---|---|---:|---:|---:|---:|---:|
| `SKEW_History.csv` | `DATE,SKEW` | 1990-01-02 → | 9,249 | **0** | **0** | **0** | **0** |
| `VIX_History.csv` | `DATE,OPEN,HIGH,LOW,CLOSE` | 1990-01-02 → | 9,295 | **0** | **0** | **0** | **0** |
| `VIX3M_History.csv` | `DATE,OPEN,HIGH,LOW,CLOSE` | 2009-09-18 → | 4,295 | **0** | **0** | **0** | **0** |
| **Total** | | | **22,839** | **0** | **0** | **0** | **0** |

Every one of the 22,839 rows carries a figure in EVERY column. The four zero columns are the four
`ValueError`/`continue` branches `cboe_body_dates` carries (`backfill_calendar.py:300-316`), and
none of them fired on a real row.

**What this confirms, and what it adds to what was already written.** `parse_cboe_csv_for_date`'s
docstring (`ingestion/adapters.py:548-553`) already stated the rule — *"CBOE publishes no
missing-data marker: every row of every probed body carries a figure in every column and
non-sessions are simply ABSENT"* — but the evidence it names for it is
`rows_for_month_verbatim` for **2015-06**, a single month, on which it observes that the 06/06 and
06/07 weekend rows are absent. That is enough to show the absent-row mechanism; it is not enough to
show the archive never blanks a cell. The measurement above is every row of all three archives —
1990-01-02 onward for SKEW and VIX, 2009-09-18 for VIX3M, which is the whole of each — and it says
the same thing. So `backfill_calendar.py` **confirms** its sibling's assertion
on its own evidence rather than inheriting it, which is the standard §1 sets for every constant in
this document.

**The consequence for the guard, stated plainly.** The `continue` at `backfill_calendar.py:305` is
**unreachable on every row of every body measured**, and that is deliberate rather than an
oversight: the comment at `:249-253` and the test
`test_cboe_publishes_no_blank_cell_today_and_the_guard_is_kept_anyway`
(`tests/test_wo117_calendar.py:495`) both keep it for exactly the reason
`parse_cboe_csv_for_date` keeps its identical one — if a body one day does carry a blank, that date
must be ABSENT from the list rather than handed to the backfill as a recoverable publication date.
The guard's one-token length is a measured claim in the same breath: FRED's `.` is **not** in it
(`test_fred_s_dot_is_not_a_cboe_missing_marker_and_is_a_publication`), because importing FRED's
convention into a body that has never used it would silently drop a real session.

**Why the convention matters to the date list at all.** It is precisely *because* CBOE has no
marker that the ABSENT ROW is the only signal of a non-session, and therefore that §3's table can
record `✗ no generator — must be read off a body` for the NYSE trading calendar without
qualification. There is no cell to inspect, no token to count: the body's row set **is** the
calendar. Had the measurement found even one blank cell, §3's three CBOE rows would have needed a
rule for distinguishing "session with no print" from "no session", and the 3-GET prerequisite would
have become a 3-GET read plus a convention to settle. It did not.

**And it costs nothing, which is the point of recording it here.** The per-date cost (§4.3: 1 GET
per date per index, inherited `_BaseAdapter._acquire`, confirmed) and the calendar-build cost
(§3.1: 3 GETs, one per index) were both already costed correctly, and neither moves. §7.2 is a
confirmation of the BODY's shape, not a correction to a number — a **closed, no-revision finding**,
where §7.1 is an open one whose figures §6 had to absorb.

One sentence on the cost concern §4.3 *did* raise, so it is not read as applying here: the ≈3 GB of
transfer to extract CBOE's rows comes entirely from the cacheless per-date loop re-downloading the
whole history body on each of the route's dated fetches (§6.5 reconciles that figure to **7,548**),
and the calendar-build step is **not** subject to it — it is 3 whole-body reads done ONCE each,
one GET per row against route 4.3's 2,516 per row, which is four hundredths of one percent of the
route and vanishing next to the thing §4.3 points at §7.4 to fix.

(A reconciliation, since two different read dates of growing bodies appear in this document:
`evidence/wo116_cboe_probe.json` measured 9,294 / 9,248 / 4,294 at 2026-10-14 — the 9,294 §3.1
quotes — against 9,295 / 9,249 / 4,295 here at 2026-10-16. **Exactly +1 on each of the three**,
which is what three bodies sharing one trading calendar and gaining a row per published session
should do between two read dates, and a small cross-check that all three were read off the same
calendar. Nothing in §3.1's 3-GET figure or in §6's grid turns on which read is cited.)

### 7.3 Yahoo: the trap in the obvious deep-history request — found, measured, and avoided before it cost anything

**Verdict first: `range=max&interval=1d` — the first request any reader of this endpoint reaches
for, and a valid one by the server's own account — returns a COARSENED body with `interval=1d`
silently ignored, and a date list built from it would have been month-start or quarter-start dates
wearing the costume of a daily publication calendar. The absolute `period1`/`period2` window, which
is what `yahoo_observation_dates` actually uses, keeps `dataGranularity == "1d"` at every depth
measured. The risk was to CORRECTNESS and it is now closed; §4.4's and §6's cost model do not
change.**

**The measurement** (`evidence/wo117_yahoo_range_probe.json`, probed 2026-10-16 against
`query1.finance.yahoo.com/v8/finance/chart/`, every absolute window pinned to a fixed
`window_end = 2026-10-15` so a re-run reproduces the counts rather than drifting a bar a day). The
deep ask was settled rather than assumed because the live loop's `range=10d` / `2y` reaches nowhere
near a backfill episode in 2000, so *some* deep request had to be chosen:

| request | HTTP | `meta.range` echo | `dataGranularity` | bars | oldest date |
|---|---:|---|---|---:|---|
| `SPY?range=max&interval=1d` | 200 | `"max"` | **`"1mo"`** | 406 | 1993-02-01 |
| `SPY?range=max` (no `interval`) | 200 | `"max"` | `"1mo"` | 406 | 1993-02-01 |
| `^GSPC?range=max&interval=1d` | 200 | `"max"` | **`"3mo"`** | 169 | 1984-12-01 |
| `HG=F?range=max&interval=1d` | 200 | `"max"` | **`"1mo"`** | 269 | 2000-09-01 |
| `SPY?range=1y&interval=1d` | 200 | `"1y"` | `"1d"` | 252 | 2025-10-16 |
| `SPY?range=5y&interval=1d` | 200 | `"5y"` | `"1d"` | 1,255 | 2021-10-18 |
| `SPY?range=10y&interval=1d` | 200 | `"10y"` | `"1d"` | 2,514 | 2016-10-17 |
| `SPY?period1=…&period2=…&interval=1d` (whole listed life) | 200 | — | **`"1d"`** | **8,486** | 1993-01-29 |
| `^GSPC?period1=…&period2=…&interval=1d` (1927 → window end) | 200 | — | **`"1d"`** | **24,815** | **1927-12-30** |
| `^GSPC?period1=…&period2=…&interval=1d` (2000 → window end) | 200 | — | `"1d"` | 6,737 | 2000-01-03 |

**Read, in order:**

1. **`max` is honoured, not rejected — which is what makes it dangerous.** The server echoes
   `meta.range == "max"` and lists `"max"` in every symbol's own `meta.validRanges`. There is no
   `400`, no `chart.error`, no warning field. `interval=1d` is accepted into the URL and then
   discarded: the `range=max` rows with and without `interval` are the same 406 bars at the same
   `"1mo"`. A caller gets an ordinary `200` carrying a well-formed chart body.
2. **The coarsening is per-symbol and not announced anywhere but `dataGranularity`.** `SPY` and
   `HG=F` came back monthly; `^GSPC` came back **quarterly**. Nothing in the request distinguishes
   them, so a reader that worked by inspection on one symbol would silently change meaning on
   another.
3. **It is also SHALLOWER than the absolute window, which the obvious reading of "max" would deny.**
   `^GSPC?range=max` starts **1984-12-01**; the same symbol's absolute window reaches its real first
   bar at **1927-12-30**, 57 years deeper. Even `SPY`, where the depth is nearly right, starts
   1993-02-01 against a `meta.firstTradeDate` of 1993-01-29 — the stub of the first month, dropped
   to the month boundary. So `max` is neither the maximum depth nor the asked-for granularity.
4. **What a date list off that body would have been.** 406 month-start dates for `SPY`, 169
   quarter-start dates for `^GSPC` — handed to `backfill_range` as the symbol's publication
   calendar. Every one of them is a date the symbol did **not** necessarily print on, and the
   ~8,000 and ~24,600 dates it *did* print on would never be mentioned. That is the exact failure
   `ingestion/backfill_calendar.py`'s module docstring and §3 are written against: not a refusal,
   not an EMPTY, but **a hole nothing downstream ever reports**, arriving as a `200` nobody would
   think to question. It is the one shape a date-list reader cannot be allowed to produce, because
   every check after it is a check on dates it was handed.
5. **The window is clean at every depth that matters, and the ceiling has room.** The deepest ask
   any of the 7 plain-close rows can make — `^GSPC` across 1927-12-30..2026-10-15 — came back as
   **24,815 daily bars at `dataGranularity == "1d"` in ONE response of ≈2.65 MB**, which is 66% of
   `MAX_BODY_BYTES` (4,000,000). So no chunked walk, no seam to get wrong, and a body that exceeded
   the ceiling would raise `BODY_TOO_LARGE` in `http_get` and FAIL the calendar read rather than
   return a truncated list — the correct direction for this module. The coarsening is specific to
   `max`: `1y`, `5y` and `10y` all held `"1d"`.

**What this says about §3.1's own prediction, stated honestly.** §3.1's table named the right
mechanism from the start — *"one `period1`/`period2` chart request per symbol spanning the
windows; the session timestamps are the calendar"* — and `yahoo_observation_dates`
(`backfill_calendar.py:461`), built on `yahoo_chart_url` (`adapters.py:591`), is that request
unchanged. But §3.1 chose it for a plain reason (the windows are known, so ask for them) and **not
because this trap was foreseen**; nothing in §3.1 or §4.4 as written anticipates that the obvious
alternative returns a coarsened 200. The prediction was correct and its reasoning was lucky. This
round is where the alternative was actually probed, where the trap was found, and where the
mechanism was independently re-confirmed as the safe one — which is worth recording precisely
because a later reader reaching for `range=max` as an "obvious simplification" of a 7-GET read
would be undoing a decision that now has evidence behind it rather than a preference.

**And it costs nothing.** `yahoo_observation_dates`'s production cost is **1 GET per row — 7 GETs
for the whole calendar build**, exactly what §3.1 costed, and the per-date route cost (§4.4: 1 GET
per date per symbol) is untouched. The 7 GETs are one per row against route 4.4's 2,516 per row,
the same four-hundredths-of-a-percent §7.2 arrives at for CBOE and for the same reason — both
routes are NYSE-days × rows, so a one-GET-per-row prerequisite is the same fraction of either. What
was real and is now closed is a risk to the CORRECTNESS of a date list a future reader might build
the obvious way, not a risk to any number in §6.

**Not claimed here.** That the four symbols not probed (`SPY`, `^GSPC` and `HG=F` were; the
remaining 4 of the 7 plain-close rows were not) coarsen identically is **not** asserted — three
instruments of three different kinds, an ETF, an index and a futures contract, all coarsened, which
is why the behaviour is read as the endpoint's rather than any symbol's. The avoidance does not
depend on it either way: `yahoo_observation_dates` never issues a `range` request for any of the 7,
so a symbol that honoured `max` properly would change nothing about what the reader does.

## 8. §0 finding 3: a dated backfill carries no `history` array — **7 rows, not 4** — and the fix is smaller than the finding

**Verdict first, in three parts.**

**(a) The gap is REAL and STRUCTURAL.** Every dated parser in `ingestion/adapters.py` can return
at most the ONE named observation; none of them has a code path that could construct a `history`
key, and `ing.history` is *passed* to the dated adapters and then discarded by the parser they
dispatch to. It is not a missed parameter.

**(b) §0's COUNT WAS WRONG and is corrected here. The population is SEVEN catalog rows, not four**
— §0 named `fred.DFII10.history`, `yahoo.^GSPC`, `fred.WALCL` and `fred.CPILFESL` and missed the
three regional-Fed surveys behind `ism_manufacturing` entirely. **FOUR INDICATORS** are affected,
which is probably where the four came from.

**(c) The fix is buildable, and this was found while writing this section rather than known in
advance.** §0 said whether a replay can run on a value-only store "is a question this estimate
cannot answer and does not". Part of it can now be answered: carrying `history` for all seven rows
is **not new infrastructure**. It is *widen the window the dated fetch already asks for, and keep
the trailing N rows instead of only the keyed one* — two functions this WO already built and
proved, at **zero extra GETs on all seven rows**. What it is NOT is sufficient: on two of the four
indicators a SECOND, INDEPENDENT floor stops the replay anyway, and one of those cannot be moved by
any backfill at all (§8.3). **Nothing here is authorised, and no figure in §6 changes.**

### 8.1 The gap, stated precisely, and the population counted

**The seven rows.** Counted this round the way §5 counts: `history > 0` over
`ingestion.catalog.INGREDIENTS`, intersected with §5's 35-row backfillable population by asking the
routing predicates themselves (`requires_original_vintage`, `has_no_revision_mechanism`) rather than
by reading §5's lists back.

| row | route | `history` | `completes` | `serves` | what the derivation needs the window FOR |
|---|---|---:|---|---|---|
| `fred.WALCL` | 4.1 bisected | **70** | COMPONENT | `monetisation_flag` | a RATE OF CHANGE, not a level: the latest level against the last level on or before 365 days earlier (`FISCAL_BALANCE_SHEET_LOOKBACK_DAYS`, `derivations.py:77`) |
| `fred.CPILFESL` | 4.1 bisected | **8** | COMPONENT | `monetisation_flag` | the level dated **exactly** 3 calendar months before the latest one, month-start (`FISCAL_CORE_CPI_MONTHS`, `:78`); a missing month is refused, never bridged |
| `fred.GACDFSA066MSFRBPHI` | 4.1 bisected | **1000** | COMPONENT | `ism_manufacturing` | its OWN full published history, to z-score the latest point against (mean and population σ over every stored row) |
| `fred.GACDISA066MSFRBNY` | 4.1 bisected | **1000** | COMPONENT | `ism_manufacturing` | same, independently per survey |
| `fred.BACTSAMFRBDAL` | 4.1 bisected | **1000** | COMPONENT | `ism_manufacturing` | same, independently per survey |
| `fred.DFII10.history` | 4.2 measured-stable | **2600** | COMPONENT | `gold_real_rate_cross` | ~2600 daily LEVELS: a 60-change rolling Pearson correlation, percentiled within every earlier rolling correlation the history yields |
| `yahoo.^GSPC` | 4.4 Yahoo plain-close | **260** | COMPONENT | `spx_vs_200dma` | 200 trailing closes ENDING at the reading's own date, to average |

**7 rows across 3 of the 4 routes; route 4.3 (CBOE) has none.** Out of scope and deliberately not
counted, by §4.4/§5.4 and whatever §9 formalises: the **51** `yahoo`/`adjclose` rows (history 520 /
210), `lbma.gold_fix_usd.history` (2600) and `multpl.shiller_pe_table` (2400). **7 + 53 = 60**, the
whole of `history > 0` in the catalog, so the in-scope and out-of-scope halves account for it.

**All seven are `completes == "COMPONENT"`**, which is what §0's wording claimed and is confirmed
here, and **all seven have `transformation is None`**. That second fact closes a question §8.2 would
otherwise have to answer: the three transformed FRED rows (`M2SL.pc1`, `CPIAUCSL.pc1`,
`PCEPILFE.pc1`) all carry `history=0` and `completes == "DIRECT"`, so a `pc1` series' base period
never enters this list and the fix below does not have to generalise across a server-side
transformation. It is **not** asserted that it would.

**The derivations, read rather than taken from the GUI's "why" text.** `ingestion/wiring.py:92-99`
binds the roles and `src/crash_detector/engine/derivations.py` computes them. Four corrections to
how this is usually described, each from the code:

* **`monetisation_flag` and `fiscal_dominance` are ONE indicator, not two.** The row was renamed in
  WO-1.19; `DerivationKind.FISCAL_CONJUNCTION`'s *value* deliberately did not move, because it
  reaches the store as the indicator's `adapter_id` (`derivations.py:169-173`). The catalog's
  `serves` for both rows says `monetisation_flag` and nothing else.
* **The two `monetisation_flag` legs need DIFFERENT things from their windows.** WALCL's leg is a
  365-day reach-back and takes whatever level sits on or before the cutoff (`derivations.py:313-317`);
  CPILFESL's leg demands a level at an **exact** month-start key 3 months back and refuses if that
  month is absent (`:324-329`). A slice that merely reaches far enough satisfies the first and can
  still fail the second.
* **`ism_manufacturing` z-scores each survey against its own full stored history**, not against a
  shared window, and each survey independently needs `MINIMUM_SURVEY_HISTORY = 120` monthly points
  (`derivations.py:86`, `:393-412`). The live GUI's "why" text says the same thing; it is confirmed
  here against `_z_composite` rather than trusted.
* **`spx_vs_200dma` requires the history to END at the reading's own date** and the reading's value
  to BE that last close (`derivations.py:264-271`) — three refusals, not one. A trailing window
  anchored anywhere else is rejected even if it is 200 rows long.

**The structural proof, with lines.** `ingestion/backfill_adapters.py` already says it in its own
docstring — *"`ing.history` is not carried by a dated fetch — a one-day window has no history in
it"* (`:79`) and *"`ing.history` is passed for the same reason the FRED branch passes it and with
the same effect: a dated read is one bar, so there is no history in it to carry"* (`:221`) — and the
code around `build_backfill_adapter` confirms it is structural rather than an omission:

1. **The parameter arrives.** `backfill_adapters.py:208` passes `ing.history` to `FredAdapter`;
   `:222` passes it to `YahooChartAdapter`. Nothing withholds it.
2. **The dated branch then dispatches to a parser that has no such parameter.**
   `adapters.py:1147-1148` — `parse_fred_csv(body, column, unit, self._history)` when
   `observation_date is None`, and `parse_fred_csv_for_date(body, column, unit, observation_date)`
   when it is set. The second function's signature takes no `history` at all. `adapters.py:1577-1578`
   is the identical pair for Yahoo; `:1441` is CBOE's dated parser, which has no history rows anyway.
3. **Neither dated parser can construct the key.** `parse_fred_csv_for_date` returns one of
   `{"unit"}`, `{"unit", "observation_date", "value"}` or `{"malformed": …}` and nothing else
   (`adapters.py:440-456`); `parse_alfred_csv` returns the same three plus `vintage_date`
   (`:377-394`). The only four places in the file that build a `history` array are
   `adapters.py:228`, `:698`, `:811` and `:869` — `parse_fred_csv`, `parse_yahoo_chart`,
   `parse_multpl_table` and `parse_lbma_gold`, every one of them an UNDATED latest-row parser.
4. **And both dated parsers say so in their own docstrings**, with the reason: *"NO `history`. A
   windowed request asks for one day, so there is no history in the body to carry, and a payload
   that mixed one day's window with a history read out of some other body would be two different
   questions under one key"* (`adapters.py:436-439`), naming `fred.DFII10.history` explicitly.

**So the gap is this.** A store built by this WO's execution would hold a real, correctly-dated,
point-in-time VALUE for each of these seven rows at every recovered date — and the ENGINE could not
turn any of them into a number. `_history_of` raises `DerivationUnavailable("… stored reading
carries no raw history")` (`derivations.py:239-241`) before any arithmetic happens, so
`monetisation_flag`, `ism_manufacturing`, `gold_real_rate_cross` and `spx_vs_200dma` would each read
as having **no usable input** at every backfilled historical date, while the raw observation sits in
the store beside them. That is an absence, not a wrong number — `derive` emits no observation and
the dial sees nothing (CD-AC-001) — which is the right failure direction and still a replay that
cannot exercise four of its indicators.

### 8.2 Is this unsolvable, or just not attempted here? — BUILDABLE, and the obvious version of the fix is wrong on five of the seven rows

**The shape of the fix, stated once: keep the VALUES as well as the dates, and slice to the N
trailing rows at or before date D.** Both halves already exist in this WO's own code.

**The values are already in hand and thrown away.** `ingestion/backfill_calendar.py:178` is
`if cells[1] in MISSING_VALUE_TOKENS: continue` — `cells[1]` *is* the FRED value column, read only
to test it for `.` and then dropped; `:445` is `if close is None:` doing exactly the same to Yahoo's
close. Neither reader would fetch a byte more to keep them. And the array-building half is not new
either: `parse_fred_csv` (`adapters.py:218-229`) already walks the body in reverse, stops at
`max(history, 1)` rows and emits `[[date, value], …]` oldest-first — the exact shape `_history_of`
validates. The extension is to anchor that walk at a **keyed** row instead of at the body's last
row.

**But the obvious source for those values is the WRONG one for five of the seven rows, and that is
the real finding of this subsection.** The tempting version is: `fred_observation_dates` already
issues ONE **undated** whole-body GET per FRED row (`backfill_calendar.py:238` →
`fred_graph_url(ing.ref, ing.transformation)`, undated on purpose, for the reason the docstring
gives), and that body carries every historical value, not just every date. True — and for
`fred.WALCL`, `fred.CPILFESL` and the three surveys those values are **TODAY'S RESTATED FIGURES**.
Hanging a today-restated history behind an original-vintage point value would put two different
vintages under one key: §0.1 and the WO-1.14 forgery class arriving through a third door. So for
route 4.1 the undated body is **refused as the source**, and the right one is the vintage body
itself:

| route | rows | where the trailing window comes from | extra GETs |
|---|---:|---|---:|
| **4.1** bisected | 5 | `AlfredVintageAdapter._url_for` already pins `cosd=D&coed=D` (`adapters.py:1293`). Widen `cosd` to D − N observations. The history then comes from **the same vintage body the value came from** — the point-in-time-correct history, which the undated body could not give. | **0** |
| **4.2** measured-stable | 1 (`fred.DFII10.history`) | `fred_graph_url` already takes `observation_date` and emits `cosd=D&coed=D` (`adapters.py:274-276`); widen `cosd`. The undated whole-body read is ALSO legitimate here, and only here, because `REVISION_STABLE` membership *is* the measured claim that today's body carries the figure a collector would have seen. | **0** |
| **4.4** Yahoo plain-close | 1 (`yahoo.^GSPC`) | `yahoo_chart_url(symbol, start=…, end=…)` (`adapters.py:591`) — the absolute `period1`/`period2` window §7.3 measured to **24,815 daily bars at `dataGranularity == "1d"` back to 1927-12-30 in one 2.65 MB response**. A window ending at D and spanning 260 trading days back is a trivial case of a request already proved at 95× that depth. | **0** |

**Why zero extra GETs on all three routes, which is the load-bearing claim.** Nothing above adds a
request; each one *widens a window on a request already being issued*. On route 4.1 the bisection's
GET count is `2 + ceil(log2(days))` and is a function of the observation date and the clock only —
no series identity and no window width enters `_acquire` (`adapters.py:1303-1370`) — and widening
cannot disturb the search, because `parse_alfred_csv` decides `_SERVED` vs `_ABSENT` by **exact-date
match** and is explicitly written to be immune to a body carrying a span nobody asked for
(`:373-376`). The bodies grow: a survey's whole vintage body is ~700 rows, ~14 KB, against
`MAX_BODY_BYTES` of 4,000,000. (A cheaper-bytes variant — widen only the FINAL confirmed probe —
costs **+1 GET per date** instead; it is noted so the choice is visible, not recommended.) So the
only new cost is **CPU-side slicing, not network**, and §6's 70,196/190,052 GET figures stand
unchanged either way.

**Does it generalise cleanly across the seven?** Checked rather than assumed, and it does — with one
honest qualifier and one inherited problem:

* **All seven have `transformation is None`** (§8.1), so no `pc1` base period, no server-side
  transform to re-derive. The fix is **not** claimed to generalise to "any FRED row"; it is claimed
  for these seven, and the rows that would complicate it are measurably not among them.
* **One qualifier:** `CPILFESL`'s leg needs an **exact** month-start key 3 months back, so the
  slice must be taken over OBSERVATION dates and not over "the last 8 rows of whatever came back".
  With `history=8` monthly rows ending at D the required row is the fourth from the end — present
  by construction, and only by construction.
* **One inherited problem, declared:** a trailing window sliced out of an ALFRED vintage is
  point-in-time correct **exactly to the extent that vintage is a genuine first publication**. Where
  §7.1's restatement band applies, the history would be a restatement history behind a restatement
  value. §8's fix neither worsens nor repairs §7.1 — it inherits it unchanged, which is the honest
  position and not a defence.

**So: a real, buildable path, found while writing this section.** It was not reached in advance and
§0 item 3 did not forecast it; §0 forecast only the gap.

### 8.3 What it means — the fix is NECESSARY and on two indicators NOT SUFFICIENT

The fix would make four indicators *computable in principle*. Whether each can actually produce a
number at a backfilled date is a different question, and it is decided by floors that live in the
SOURCES and in `wiring.py`, not in the backfill. Measured against §2's eight episode windows, using
`evidence/wo114_alfred_probe.json`'s per-series observation spans (probed 2026-10-13/16, the same
file §7.1 reads):

| indicator | rows | the binding floor, and where it comes from | episodes it could compute in |
|---|---|---|---:|
| `spx_vs_200dma` | `yahoo.^GSPC` | none. 200 trailing closes ending at D; §7.3 measured daily bars to 1927-12-30, and the plan's oldest date is 1999-11-02. | **8 of 8** |
| `monetisation_flag` | `WALCL`, `CPILFESL` | **WALCL's own first observation is 2002-12-18**, and its leg must reach 365 days further back → **earliest computable D ≈ 2003-12-18**. CPILFESL reaches 1957-01-01 and is one of §7.1's five clean rows (113 FIRST-PUB, 0 restatement, 0 EMPTY). | **7 of 8** (2000-02 dot-com out) |
| `ism_manufacturing` | the 3 surveys | **`MINIMUM_SURVEY_HISTORY = 120` per survey against `BACTSAMFRBDAL`'s first observation 2004-06-01 → the composite is floored at 2014-05-01.** (PHI 1968-05-01 → 1978-04-01; NY 2001-07-01 → 2011-06-01; Dallas binds.) Independently, §7.1 already refuses or empties all three surveys' VALUES across the first three episodes. | **5 of 8** (2015-16 onward) |
| `gold_real_rate_cross` | `fred.DFII10.history` | **not a history problem at all.** Its *gold* leg is `lbma.gold_fix_usd.history` (`wiring.py:98`), `kind == "lbma"`, and `VINTAGE_BACKFILLABLE_KINDS = ("fred", "cboe", "yahoo")` (`backfill_adapters.py:176`) — `build_backfill_adapter` **raises** on it. One of two legs cannot be backfilled at any date by any route in this plan. | **0 of 8** |

**Read, in order:**

1. **Carrying `history` is necessary for all four and sufficient for only two.** `spx_vs_200dma`
   becomes fully available; `monetisation_flag` becomes available wherever WALCL itself exists.
2. **`ism_manufacturing`'s floor is in the publisher and no mechanism moves it.** The Dallas survey
   did not exist before 2004-06-01 and a 120-point z-score distribution cannot be assembled from
   observations that were never published. The three earliest episodes — dot-com, GFC, 2011, the
   three a crash replay most wants — are impossible for this indicator on two independent grounds,
   and the history gap is the lesser of them.
3. **Fixing `fred.DFII10.history` buys `gold_real_rate_cross` NOTHING on its own**, and this is the
   one place §8's fix is not merely insufficient but irrelevant: the indicator needs 421 shared
   dates across two legs (`CORRELATION_WINDOW` 60 + `MINIMUM_PERCENTILE_HISTORY` 360 + 1) and one
   leg has no backfill route. Whether `lbma` should become backfillable is §9's scope question, not
   §8's.
4. **No number in this document moves.** No GET-count change, because the reads that would serve the
   history are the SAME undated/dated reads already costed — §3.1's 24 FRED + 3 CBOE + 7 Yahoo
   calendar GETs and §6's per-date grid are untouched. The only new cost is CPU-side slicing.

**The recommendation, plainly.** A `history`-carrying backfill for these seven rows is **not a
separate, harder problem requiring new infrastructure** — it is a small extension of functions this
WO already built and proved, at no network cost, and the correctness trap in it (route 4.1's history
must come from the vintage body, never from the undated one) is now identified rather than left for
whoever builds it to discover. It was **not attempted in this WO's scope and is not estimated
here**. Whether to build it is a scope decision for whoever picks up the real backfill execution
next, together with §9's exclusions — **this estimate does not authorise it**, and §0's three
findings remain the things to read before authorising anything.

**Not claimed here.** That a replay with `history` carried would produce *correct* indicator
readings: §7.1's restatement band is inherited unchanged (§8.2), and nothing here measures whether a
recovered figure moves a DECISION-RULE threshold. That the fix generalises beyond these seven rows —
the three transformed FRED rows and the 53 out-of-scope `history > 0` rows are untested by it. And
that the per-episode column above is a schedule: it is an arithmetic floor on what could compute,
not a prediction that it would.
