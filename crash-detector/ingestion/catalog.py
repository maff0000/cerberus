"""The ingredient catalog: which declared feed serves which ratified indicator.

DERIVED FROM ``governance/mapping/indicator_mapping.yaml`` (Matt-ratified 2026-08-24) and
nothing else. No source here is a choice made by this module: each ``Ingredient`` is the
feed a mapping row already declares (``source.feed``), reached by the nearest public
endpoint. Where the declared source cannot be reached publicly, the indicator is listed in
:data:`NOT_TRACTABLE` with the reason, and NO substitute is wired — a substitute would be a
provenance decision, which is not this module's to make. WO-1.6 is the recorded exception: the
two indicators wired from something other than their declared feed are listed, with the
authority each rests on, in :data:`SUBSTITUTED_FEEDS`, and nowhere else.

``serves`` names the mapping rows an ingredient feeds. ``completes`` says whether that
single ingredient is the indicator's whole scored quantity (``DIRECT``) or one input to a
derivation the ENGINE owns (``COMPONENT``). The ingestion layer never performs the
derivation (collector-never-computes, BLUEPRINT §5).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Union

from crash_detector.engine.derivations import BREADTH_MINIMUM_RESOLVED, BREADTH_SAMPLE
from ingestion.adapters import (
    CboeAdapter,
    FredAdapter,
    HERMES_PEER,
    HermesCandleAdapter,
    LbmaGoldAdapter,
    MultplShillerAdapter,
    YahooChartAdapter,
)

__all__ = ["Ingredient", "INGREDIENTS", "NOT_TRACTABLE", "PARTIAL", "SUBSTITUTED_FEEDS", "WINDOW_OVERRIDES",
           "window_seconds", "EGRESS_HOSTS", "NON_HTTP_PEERS", "build_adapter", "MANUAL_SLOOS_NDFI", "QUORUM",
           "PROVISIONAL_CONSTRUCTIONS"]

DAY, WEEK = 86_400, 7 * 86_400

#: The manual SLOOS NDFI leg's source id (a constant so ``ingestion.manual`` and the tests name the same thing).
MANUAL_SLOOS_NDFI = "manual.sloos_ndfi"
#: Polling interval, deliberately independent of publication cadence: a daily series is
#: polled every 6h so a late print is caught the same day; slower series are polled daily.
#: Re-polling is free of side effects on readings (idempotent on source period).
POLL_DAILY, POLL_SLOW = 6 * 3600, DAY


@dataclass(frozen=True)
class Ingredient:
    source_id: str
    kind: str                      # fred | cboe | yahoo | multpl | lbma | hermes | manual
    ref: str                       # series id / index / symbol
    unit: str
    declared_feed: str             # the mapping row's ``source.feed`` this implements
    serves: tuple[str, ...]        # indicator ids
    completes: str                 # DIRECT | COMPONENT
    poll_seconds: int
    as_of_rule: str = "obs_date"   # obs_date | month_end
    transformation: Union[str, None] = None
    column: str = ""
    history: int = 0
    stands_for: str = ""


def _f(series, unit, serves, completes="DIRECT", *, poll=POLL_DAILY, rule="obs_date", tr=None, feed=None, stands="",
       history=0):
    sid = f"fred.{series}" + (f".{tr}" if tr else "")
    return Ingredient(sid, "fred", series, unit, feed or f"FRED:{series}", tuple(serves), completes, poll, rule, tr,
                      history=history, stands_for=stands or f"FRED {series}" + (f" ({tr})" if tr else ""))


INGREDIENTS: tuple[Ingredient, ...] = (
    # ---- FRED, daily -------------------------------------------------------------------
    _f("BAMLH0A0HYM2", "percent", ["hy_oas"]),
    _f("BAMLC0A0CM", "percent", ["ig_oas"]),
    _f("T10Y3M", "percent", ["yield_curve_10y3m"]),
    _f("T10Y2Y", "percent", ["yield_curve_10y2y"]),
    _f("DFII10", "percent", ["real_rate_10y_tips"], feed="FRED:DFII10"),
    _f("T5YIE", "percent", ["breakeven_5y"]),
    _f("DFF", "percent", ["fed_funds_rate"]),
    # ---- FRED, weekly ------------------------------------------------------------------
    _f("IC4WSA", "claims", ["jobless_claims_4w"], poll=POLL_SLOW),
    _f("NFCI", "index", ["chicago_fed_nfci"], poll=POLL_SLOW),
    _f("DTWEXBGS", "index", ["broad_dollar"], poll=POLL_SLOW),
    # ---- FRED, monthly -----------------------------------------------------------------
    _f("SAHMREALTIME", "percentage_points", ["sahm_rule"], poll=POLL_SLOW, rule="month_end"),
    _f("UMCSENT", "index", ["michigan_sentiment"], poll=POLL_SLOW, rule="month_end"),
    # YoY rows: FRED's own server-side ``pc1`` (percent change from a year ago).
    _f("M2SL", "percent_yoy", ["m2_yoy"], poll=POLL_SLOW, rule="month_end", tr="pc1"),
    _f("CPIAUCSL", "percent_yoy", ["cpi_yoy"], poll=POLL_SLOW, rule="month_end", tr="pc1"),
    _f("PCEPILFE", "percent_yoy", ["core_pce_yoy"], poll=POLL_SLOW, rule="month_end", tr="pc1"),
    # ---- FRED, quarterly (SLOOS, auto C&I leg only — see PARTIAL) -----------------------
    _f("DRTSCILM", "net_percent_tightening", ["sloos_bank_lending"], "COMPONENT", poll=POLL_SLOW),
    # ---- WO-1.19: the SMALL-FIRM half of the SAME SLOOS question, replacing the hand-entered NDFI leg -----
    _f("DRTSCIS", "net_percent_tightening", ["sloos_bank_lending"], "COMPONENT", poll=POLL_SLOW),
    # ---- WO-1.6: substitute / ported-rule inputs (see SUBSTITUTED_FEEDS) ---------------------
    # buffett_indicator: Z.1 corporate equities (market value, $ millions) over nominal GDP ($ billions).
    # Both are quarterly and FRED dates them at the quarter START; they are aged from the quarter END
    # (the ``quarter_end`` as-of rule), the period they describe, as ``month_end`` does for monthly series.
    _f("NCBEILQ027S", "usd_millions", ["buffett_indicator"], "COMPONENT", poll=POLL_SLOW, rule="quarter_end",
       feed="FRED:NCBEILQ027S", stands="FRED NCBEILQ027S (Z.1 nonfinancial corporate equities, market value, $M)"),
    _f("GDP", "usd_billions", ["buffett_indicator"], "COMPONENT", poll=POLL_SLOW, rule="quarter_end", feed="FRED:GDP",
       stands="FRED GDP (nominal GDP, $B, annual rate)"),
    # monetisation_flag (the ratified row called fiscal_dominance until the WO-1.19 rename): the legacy
    # discriminator's two inputs, as RAW LEVEL HISTORY. The engine takes the
    # 12-month change of WALCL and the 3-month annualised change of core CPI; the collector computes neither.
    # WALCL is weekly (history 70 rows spans the 53 weeks the year-on-year needs, with slack); CPILFESL is
    # monthly (history 8 rows: the latest, and the one 3 months before it, with slack for a missing month).
    _f("WALCL", "usd_millions", ["monetisation_flag"], "COMPONENT", poll=POLL_SLOW, history=70, feed="FRED:WALCL",
       stands="FRED WALCL (Fed total assets, $M) with its last 70 weekly levels"),
    _f("CPILFESL", "index", ["monetisation_flag"], "COMPONENT", poll=POLL_SLOW, rule="month_end", history=8,
       feed="FRED:CPILFESL", stands="FRED CPILFESL (core CPI index) with its last 8 monthly levels"),
    # ---- WO-1.12: gold_spot = HERMES' published XAU/USD H4 candle close ------------------------
    # This IMPLEMENTS the ratified row's own feed (`market:XAUUSD`, provenance `spot`) and is therefore NOT a
    # substitute: HERMES publishes live OANDA XAU/USD, which is spot gold, not a futures contract and not a fix.
    # It REPLACES the LBMA gold-fix endpoint, which answers HTTP 403 to this host and delivered no reading at all
    # from WO-1.6 to WO-1.12. A NEW source id, not a reuse of `lbma.gold_fix_usd`: the store keeps the first
    # payload admitted per source period and the failed id's observation history is left untouched.
    # H4 is the timeframe asked for because it FITS the row's daily cadence: M1/M5/M15/H1 are far more granular
    # than a daily indicator can use, and HERMES' D1 timeframe is not active. See parse_hermes_candle for the
    # disclosed consequence — the figure is the FIRST H4 close of each UTC day, not an intraday tick.
    Ingredient("hermes.xau_usd.h4_close", "hermes", "XAU_USD:H4", "usd_per_oz",
               "market:XAUUSD (HERMES published H4 candle close, instrument XAU_USD, live OANDA spot)",
               ("gold_spot",), "DIRECT", POLL_DAILY,
               stands_for="XAU/USD spot in USD per troy ounce: the close of the first H4 candle HERMES publishes "
                          "each UTC day (live OANDA prices; HERMES is a DEV/STAGING engineering candidate, see "
                          "ingestion.adapters.HERMES_PEER)"),
    # ---- WO-1.7: gold_real_rate_cross (see SUBSTITUTED_FEEDS) -----------------------------------
    # Two RAW daily histories the ENGINE correlates. NEW source ids on purpose: the store keeps the first payload
    # admitted per source period, and ``fred.DFII10`` (history-less, serves real_rate_10y_tips) must not change.
    # ~2600 rows is ~10 years of trading days (the schema's cap is MAX_HISTORY). Gold is the LBMA fix and NOT the
    # COMEX futures close: if LBMA refuses this host (it does, HTTP 403) this indicator FAILS with it.
    Ingredient("fred.DFII10.history", "fred", "DFII10", "percent", "FRED:DFII10", ("gold_real_rate_cross",), "COMPONENT",
               POLL_DAILY, history=2600, stands_for="FRED DFII10 (10y TIPS real yield) with its last 2600 daily levels"),
    Ingredient("lbma.gold_fix_usd.history", "lbma", "gold_pm+gold_am", "usd_per_oz", "market:XAUUSD (LBMA PM fix, AM fallback)",
               ("gold_real_rate_cross",), "COMPONENT", POLL_DAILY, history=2600,
               stands_for="LBMA daily gold fix (USD/oz, PM else AM) with its last 2600 dated fixes"),
    # ---- WO-1.7: ism_manufacturing substitute = regional Fed surveys (see SUBSTITUTED_FEEDS) ------------
    # FRED ids VERIFIED to return data 2026-10-12. Monthly diffusion indices, seasonally adjusted, dated the 1st.
    _f("GACDFSA066MSFRBPHI", "diffusion_index", ["ism_manufacturing"], "COMPONENT", poll=POLL_SLOW, rule="month_end",
       history=1000, feed="FRED:GACDFSA066MSFRBPHI",
       stands="Philadelphia Fed Manufacturing Business Outlook, current general activity (FRED GACDFSA066MSFRBPHI)"),
    _f("GACDISA066MSFRBNY", "diffusion_index", ["ism_manufacturing"], "COMPONENT", poll=POLL_SLOW, rule="month_end",
       history=1000, feed="FRED:GACDISA066MSFRBNY",
       stands="Empire State Manufacturing Survey, general business conditions (FRED GACDISA066MSFRBNY)"),
    _f("BACTSAMFRBDAL", "diffusion_index", ["ism_manufacturing"], "COMPONENT", poll=POLL_SLOW, rule="month_end",
       history=1000, feed="FRED:BACTSAMFRBDAL",
       stands="Dallas Fed Texas Manufacturing Outlook, general business activity (FRED BACTSAMFRBDAL)"),
    # ---- WO-1.7: sloos_bank_lending MANUAL leg. No feed exists; ``ingestion.manual`` records a hand-entered value ---
    Ingredient(MANUAL_SLOOS_NDFI, "manual", "sloos_table2_q14", "net_percent_tightening",
               "manual:Fed SLOOS Table 2 Q14 (avg of 5 sub-categories), hand-entered", ("sloos_bank_lending",),
               "COMPONENT", 0, as_of_rule="obs_date",
               stands_for="Fed SLOOS Table 2 Q14 NDFI net tightening, average of the 5 sub-categories, hand-entered quarterly"),
    # ---- CBOE public history CSVs ------------------------------------------------------
    Ingredient("cboe.SKEW", "cboe", "SKEW", "index", "CBOE:SKEW", ("cboe_skew",), "DIRECT", POLL_DAILY,
               column="SKEW", stands_for="CBOE SKEW index close"),
    Ingredient("cboe.VIX", "cboe", "VIX", "index", "CBOE:VIX", ("vix_level", "vix_term_structure"), "DIRECT", POLL_DAILY,
               column="CLOSE", stands_for="CBOE VIX close"),
    Ingredient("cboe.VIX3M", "cboe", "VIX3M", "index", "CBOE:VIX3M", ("vix_term_structure",), "COMPONENT",
               POLL_DAILY, column="CLOSE", stands_for="CBOE VIX3M close (denominator of VIX/VIX3M)"),
    # ---- Yahoo public chart (ETF / index / futures closes) -----------------------------
    Ingredient("yahoo.HYG", "yahoo", "HYG", "usd", "market:HYG,LQD", ("credit_stress_hyg_lqd",), "COMPONENT", POLL_DAILY,
               stands_for="HYG close (numerator of HYG/LQD)"),
    Ingredient("yahoo.LQD", "yahoo", "LQD", "usd", "market:HYG,LQD", ("credit_stress_hyg_lqd",), "COMPONENT", POLL_DAILY,
               stands_for="LQD close (denominator of HYG/LQD)"),
    Ingredient("yahoo.RSP", "yahoo", "RSP", "usd", "market:RSP,SPY", ("breadth_rsp_spy",), "COMPONENT", POLL_DAILY,
               stands_for="RSP close (equal-weight S&P)"),
    Ingredient("yahoo.SPY", "yahoo", "SPY", "usd", "market:RSP,SPY", ("breadth_rsp_spy",), "COMPONENT", POLL_DAILY,
               stands_for="SPY close (cap-weight S&P)"),
    Ingredient("yahoo.^GSPC", "yahoo", "^GSPC", "index", "market:SPX", ("spx_vs_200dma",), "COMPONENT", POLL_DAILY,
               history=260, stands_for="S&P 500 close + last 260 closes for the 200-day average"),
    Ingredient("yahoo.HG=F", "yahoo", "HG=F", "usd_per_lb", "market:HG,GC", ("copper_gold",), "COMPONENT", POLL_DAILY,
               stands_for="COMEX copper front-month close"),
    Ingredient("yahoo.GC=F", "yahoo", "GC=F", "usd_per_oz", "market:HG,GC", ("copper_gold",),
               "COMPONENT", POLL_DAILY, stands_for="COMEX gold front-month close"),
    # ---- WO-1.8: private_credit_stress v1 = BIZD market-price proxy (see SUBSTITUTED_FEEDS) ----------------------
    # ``column="adjclose"`` asks Yahoo for the DIVIDEND-ADJUSTED close: BIZD distributes most of its return, and a
    # printed-price drawdown would count every ex-dividend drop as stress (verified 2026-10-12: 19.7% printed vs 9.5%
    # adjusted below the 252-day high). history=520 is the whole ``range=2y`` page (~500 bars) the adapter requests.
    Ingredient("yahoo.BIZD.adj", "yahoo", "BIZD", "usd", "market:BIZD (VanEck BDC Income ETF), dividend-adjusted close",
               ("private_credit_stress",), "COMPONENT", POLL_DAILY, column="adjclose", history=520,
               stands_for="BIZD dividend-adjusted close + last 520 adjusted closes for the 252-day trailing high"),
    # ---- WO-1.10: constituent_breadth_200dma = % of a DEFINED 50-name large-cap sample above its own 200-day mean -------
    # One COMPONENT per name, dividend-adjusted close like the legacy tell (yfinance auto_adjust=True). history=210 keeps
    # the 200 closes the mean needs plus a small margin for bars Yahoo nulls; the ENGINE counts and fails loud (<30 of 50).
    *(Ingredient(f"yahoo.{name}.adj", "yahoo", name, "usd", f"market:{name}, dividend-adjusted close (breadth sample)",
                 ("constituent_breadth_200dma",), "COMPONENT", POLL_DAILY, column="adjclose", history=210,
                 stands_for=f"{name} dividend-adjusted close + last 210 adjusted closes for its 200-day mean")
      for name in BREADTH_SAMPLE),
    # ---- multpl (declared: multpl/Shiller) ---------------------------------------------
    # A NEW source id (was ``multpl.shiller_pe``, latest figure only): the payload now carries the
    # whole published monthly table for the engine's percentile, and the store keeps the first
    # payload admitted per source period, so reusing the id would have kept the history-less
    # reading in place until multpl's date rolled over. The old id's readings are left untouched.
    Ingredient("multpl.shiller_pe_table", "multpl", "shiller-pe", "ratio", "multpl/Shiller", ("shiller_cape",),
               "COMPONENT", POLL_SLOW, history=2400,
               stands_for="Shiller CAPE as published, with multpl's full monthly table (the engine percentiles it)"),
)

#: Indicators that are only half-fed with no way to complete them. EMPTY since WO-1.7: sloos_bank_lending's manual
#: NDFI leg is now a first-class ingredient (``MANUAL_SLOOS_NDFI``, entered with ``python -m ingestion.manual``). The
#: indicator reads MISSING until a value is entered and STALE again 120 days after the survey it describes, so it can
#: never read complete on one leg.
PARTIAL: dict[str, str] = {}

#: Indicators whose DECLARED source cannot be reached with public/free data, or whose
#: definition needs a decision this module has no authority to make. No substitute is wired.
NOT_TRACTABLE: dict[str, str] = {}

#: Derived indicators that tolerate some absent components: indicator id -> the fewest components that must be healthy.
#: Every other derived indicator needs ALL of its components. The floor is the engine's own (``BREADTH_MINIMUM_RESOLVED``).
QUORUM: dict[str, int] = {"constituent_breadth_200dma": BREADTH_MINIMUM_RESOLVED}

#: Indicators the ratified mapping never declared, built in a later WO as a DEFINED, uncalibrated construction. Each
#: reason travels with the indicator onto the GUI so a number is never read as more than it is.
PROVISIONAL_CONSTRUCTIONS: dict[str, str] = {
    "constituent_breadth_200dma": "WO-1.10 addition, not a ratified row: the percent of a FIXED 50-name large-cap SAMPLE "
    "(ported from the legacy ARGUS equity_tells BREADTH_SAMPLE) whose latest dividend-adjusted close is above its own "
    "200-day mean. It is a defined sample, NOT the S&P 500 and not an index constituent list. It needs at least "
    f"{BREADTH_MINIMUM_RESOLVED} of the 50 names to resolve and otherwise shows no number. Its band is a placeholder (no "
    "backtest) and its weight is the lowest tier (x1). breadth_rsp_spy is a different, indirect signal and is unchanged.",
}

#: Indicators WIRED (WO-1.6) from a feed or rule that is NOT the one the ratified mapping row declares.
#: A substitute is a provenance decision; each is recorded here with whose authority it rests on, and
#: ``tests/test_ingestion.py`` allows a catalog/mapping feed mismatch for exactly these and no others.
SUBSTITUTED_FEEDS: dict[str, str] = {
    "sloos_bank_lending": "Declared as the SLOOS C&I leg PLUS the NDFI leg; the row does not say how to combine them. Wired as the PLAIN MEAN of the automatic C&I leg (FRED DRTSCILM) and the HAND-ENTERED NDFI leg (python3 -m ingestion.manual): an engineering choice awaiting Owner acceptance. The figure is dated by the OLDER leg; it is MISSING until an NDFI value is entered and STALE 120 days after a survey quarter start, so expect a short STALE gap each quarter until the next print is hand-entered.",
    "ism_manufacturing": "Declared 'ISM' (licensed; FRED withdrew NAPM). Wired as an EQUAL-WEIGHTED COMPOSITE OF Z-SCORED "
    "REGIONAL FED MANUFACTURING SURVEYS: Philadelphia (FRED GACDFSA066MSFRBPHI), Empire State/New York "
    "(GACDISA066MSFRBNY) and Dallas (BACTSAMFRBDAL), each z-scored against its own full published history and the three "
    "averaged. A DIFFERENT QUANTITY with different provenance from ISM PMI (regional, three districts, a z-score and not "
    "a 0-100 PMI): the row's 'below 93' arm does not apply. Richmond and Kansas City were asked for but are NOT on FRED "
    "(every plausible id returned 404 on 2026-10-12), so they are absent, not approximated. Substitute chosen by Trinity "
    "(provisional, not Owner-ratified, easily revisable).",
    "gold_real_rate_cross": "The ratified row says 'Gold vs 10y TIPS divergence, normalised 0-100' and defines neither. "
    "Wired as TRINITY'S PROVISIONAL, UNCALIBRATED, NOT-OWNER-RATIFIED construction (WO-1.7; Matt may choose a different "
    "one and nothing here is locked in): the 60-trading-day rolling Pearson correlation between daily gold changes "
    "(simple return of the LBMA fix) and daily changes in the 10y TIPS real yield (FRED DFII10, in percentage points), "
    "normally negative; the figure is the percentile (0-100) of the latest correlation within the ~10 years of "
    "correlations the collector holds, so a flip toward positive reads high. RELATIVE, NOT ABSOLUTE: the figure ranks the latest correlation against the series' own history and never checks the correlation LEVEL, so even a stationary all-negative regime reads uniformly 0-100 and the dial will show stress roughly 10% of the time with no sign flip (Auditor 2026-10-12). A sustained POSITIVE-correlation regime reads mid-range, not high, for the same reason, and the rolling windows overlap so the percentile is not a probability. Changes are taken between consecutive shared dates whatever the gap (a holiday makes a multi-day change). GOLD IS THE LBMA FIX, NOT THE ROW'S "
    "'market:GC' FUTURES: if LBMA is unreachable (it is, HTTP 403 from the build host) this indicator is FEED_FAILING "
    "with it and shows no value; no futures substitution is made.",
    "buffett_indicator": "Declared 'Wilshire/GDP, percentiled'; Wilshire is unavailable (FRED withdrew WILL5000PRFC). "
    "Wired as the Z.1 ratio FRED NCBEILQ027S / (GDP*1000), in percent, banded as that ratio (the row's "
    "'percentiled' step is NOT applied). Substitute accepted by Matt per the Trinity dispatch of WO-1.6; the legacy "
    "engine proved it live (Trinity 2026-07-07, ~218%). Its staleness window is overridden (see WINDOW_OVERRIDES).",
    "private_credit_stress": "The ratified row declares a COMPOSITE of BDC NAV discount + non-accrual rate + PIK share "
    "(quarterly SEC filings) with public spreads as a fast proxy. Those three metrics live in free-text filing narrative, "
    "not structured XBRL tags (confirmed against ARCC's EDGAR data), so they are NOT extracted. v1 is a MARKET-PRICE "
    "PROXY: the percent drawdown of BIZD (VanEck BDC Income ETF), on its DIVIDEND-ADJUSTED close, below its trailing "
    "252-trading-day high. It measures how the market is pricing listed private-credit risk, NOT the underlying loan "
    "quality; it is a different quantity from the declared composite, and it moves with equity beta and liquidity as well "
    "as credit. v2 (BDC NAV-discount leg, manual cadence) and v3 (non-accrual/PIK by filing-text extraction or a paid "
    "vendor) remain OPEN and are not attempted. Substitute directed by Trinity (provisional, not Owner-ratified). Its "
    "staleness window is overridden to 7 days (see WINDOW_OVERRIDES).",
    "monetisation_flag": "Declared 'Treasury/BEA deficit + interest-cost: deficit/GDP vs interest-cost/revenue, "
    "discriminated vs benign growth'. Wired instead as the legacy ARGUS crash-engine discriminator (fred_tells.py, "
    "R2D2-locked bands): Fed balance-sheet (WALCL) growth >= 10% over 12 months AND core CPI (CPILFESL) >= 4% "
    "annualised over 3 months, as a conjunction. This is a DIFFERENT quantity from the ratified row's wording "
    "(monetisation vs deficit/interest burden). Ported on the Trinity dispatch of WO-1.6. OWNER CONFIRMATION "
    "RECEIVED (Matt, 2026-10-16) and it did NOT confirm a deficit measure: the Owner's ruling is that the wired "
    "monetisation conjunction stands, and that the row is RENAMED (WO-1.19, fiscal_dominance -> monetisation_flag) "
    "so its name stops claiming the deficit/interest-burden quantity it never computed. THIS ENTRY STAYS because "
    "the row's ratified `source` and `calculation` lines are deliberately left as ratified and still declare that "
    "other quantity, so the declared-vs-wired gap is real and belongs on the dial. The deficit/interest-cost "
    "measure is OWED as a SEPARATE indicator holding the reserved id `fiscal_dominance`; it belongs in the "
    "`fiscal_master` slot of the acute statistic (DECISION-RULE.md, governance/WO-1.3a-engine-spec.md) and is not "
    "built here. The bands are still the legacy engine's and still uncalibrated by this project.",
}

#: Per-indicator staleness windows that REPLACE the ratified row's ``staleness_window_seconds``, with the reason.
#: A window shorter than the data's own release rhythm would mark a healthy feed permanently STALE.
WINDOW_OVERRIDES: dict[str, tuple[int, str]] = {
    "buffett_indicator": (
        120 * DAY,
        "the ratified row says 45 days (it assumed a monthly Wilshire series; this ratio is QUARTERLY). The Z.1 "
        "release for a quarter lands about 70 days after the quarter ends and the next one about 91 days later, so a "
        "healthy ratio is 70 to ~165 days old when aged from the quarter END. 120 days is the WIDEST relevance window "
        "the engine will admit (crash_detector.staleness.RELEVANCE_WINDOW_CEILING_SECONDS, the Owner's own figure for "
        "quarterly series), so the ratio reads STALE for roughly the last 45 days before each release. That is stated, "
        "not hidden; widening it means raising a staleness ceiling, which is an Owner decision with external review.",
    ),
    "private_credit_stress": (
        7 * DAY,
        "the ratified row's 120 days assumed QUARTERLY filings (NAV / non-accrual / PIK). v1 is a DAILY ETF price; under a "
        "120-day window a dead feed would keep a months-old drawdown reading as current, which is the opposite of the "
        "row's own 'absence reads Unknown never calm'. 7 days is the market-day daily window the mapping declares for "
        "every ETF/index/futures row (WO-1.9: worst-case holiday-weekend gap just under 6 days plus a day of grace; "
        "it was 4 days before WO-1.9), and is inside the engine's 120-day relevance ceiling. Revert this "
        "override when a quarterly v2/v3 leg is added.",
    ),
}


def window_seconds(indicator_id: str, ratified_seconds: float) -> float:
    """The staleness window to apply: the ratified one unless a recorded override replaces it."""
    override = WINDOW_OVERRIDES.get(indicator_id)
    return float(override[0]) if override else float(ratified_seconds)


#: The HTTP hostnames the LIVE collector's adapters resolve to, and ONLY those: this dict is
#: mirrored host-for-host by ``deploy/egress-destinations.yaml`` and by ``cd-collectors``'
#: ``x-egress.hosts``, and ``tests/test_ingestion.py`` asserts it equals the hostnames of
#: ``build_adapter(i)._url()`` over :data:`INGREDIENTS` by EQUALITY. A host reached by
#: something that is NOT the live collector therefore does not belong here, however real the
#: egress: WO-1.14's backfill-only ALFRED host is declared in
#: ``ingestion.backfill_adapters.BACKFILL_EGRESS_HOSTS``, with the reason, and the non-HTTP
#: HERMES peer in :data:`NON_HTTP_PEERS`.
EGRESS_HOSTS: dict[str, str] = {
    "fred.stlouisfed.org": "Federal Reserve Bank of St. Louis",
    "cdn-api.cboe.com": "Cboe Global Markets",
    "query1.finance.yahoo.com": "Yahoo",
    "www.multpl.com": "multpl.com",
    "prices.lbma.org.uk": "LBMA (London Bullion Market Association)",
}


#: NON-HTTP peers an ingredient reaches (WO-1.12). SEPARATE from :data:`EGRESS_HOSTS` because that dict is the
#: set of HTTP hostnames the adapters' ``_url`` methods resolve to, mirrored by ``deploy/egress-destinations.yaml``.
#:
#: WHY THIS IS NOT IN THAT REGISTRY, STATED RATHER THAN QUIETLY OMITTED. The destination registry admits a `host`
#: only in one POSITIVE PERMITTED SHAPE — a DNS hostname of two or more labels — and it refuses an address literal
#: BY DESIGN (see that file's header: CD-ASR-F04 was an auditor slipping `198.51.100.24` past a name-matching
#: check, and the repair was to make an address undeclarable rather than to recognise one more spelling). The
#: HERMES publication peer IS an address literal on the LAN; there is no hostname for it. So it cannot be
#: registered there without reopening exactly the hole that file exists to close, which is a change to a
#: finding-closing control and not this WO's to make.
#:
#: WHAT THAT LEAVES OWED, NAMED HERE SO IT IS NOT INVISIBLE: the designed six-service stack
#: (``deploy/compose.yaml``) is UNCHANGED by WO-1.12 and its ``cd-collectors`` allowlist still names only the five
#: public data hosts. The live DEV stack (``deploy/live-dev/``) is the one that reads HERMES, and it was already
#: outside the designed egress lane by its own header ("the design's egress lane is still OWED"). A declaration
#: shape that can express a LAN peer, so that the WO-3 egress lane inherits this read rather than discovering it,
#: is owed and is a Product Owner / architecture decision (it touches Q31, Redis, which BLUEPRINT §2 still does
#: not declare as a service — and nothing here adds one: this project is a read-only CONSUMER of another system's).
NON_HTTP_PEERS: dict[str, str] = {
    f"{HERMES_PEER[0]}:{HERMES_PEER[1]}/db{HERMES_PEER[2]}":
        "HERMES candle publication (read-only GET of hermes:candles:XAU_USD:H4:latest:v1 for gold_spot; "
        "never written to, and no other hermes:* key is read)",
}


def build_adapter(ing: Ingredient, clock: Callable[[], datetime]):
    """The LIVE collector's adapter for ``ing`` — one bounded GET for the latest observation.

    This is the constructor ``ingestion.run`` calls on every pass, and the only one it can
    call: there is no argument here that selects a point-in-time adapter, because the vintage
    search is a different question under a budget this loop does not have. WO-1.14's
    backfill-path constructor is ``ingestion.backfill_adapters.build_backfill_adapter``,
    which imports this module and is never imported BY it (that module's docstring states
    why the dependency runs only that way, and ``tests/test_wo114.py`` holds it).
    """
    common = dict(source_id=ing.source_id, as_of_rule=ing.as_of_rule, unit=ing.unit, clock=clock)
    if ing.kind == "fred":
        return FredAdapter(ing.ref, ing.transformation, ing.history, **common)
    if ing.kind == "cboe":
        return CboeAdapter(ing.ref, ing.column, **common)
    if ing.kind == "yahoo":
        return YahooChartAdapter(ing.ref, ing.history, field=ing.column or "close", **common)
    if ing.kind == "multpl":
        return MultplShillerAdapter(history=ing.history, **common)
    if ing.kind == "lbma":
        return LbmaGoldAdapter(history=ing.history, **common)
    if ing.kind == "hermes":
        instrument, timeframe = ing.ref.split(":")
        return HermesCandleAdapter(instrument, timeframe, **common)
    if ing.kind == "manual":
        raise ValueError(f"{ing.source_id} is hand-entered (ingestion.manual); it has no adapter to poll")
    raise ValueError(f"unknown ingredient kind {ing.kind!r}")
