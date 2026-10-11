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

from ingestion.adapters import (
    CboeAdapter,
    FredAdapter,
    LbmaGoldAdapter,
    MultplShillerAdapter,
    YahooChartAdapter,
)

__all__ = ["Ingredient", "INGREDIENTS", "NOT_TRACTABLE", "PARTIAL", "SUBSTITUTED_FEEDS", "WINDOW_OVERRIDES",
           "window_seconds", "EGRESS_HOSTS", "build_adapter"]

DAY, WEEK = 86_400, 7 * 86_400
#: Polling interval, deliberately independent of publication cadence: a daily series is
#: polled every 6h so a late print is caught the same day; slower series are polled daily.
#: Re-polling is free of side effects on readings (idempotent on source period).
POLL_DAILY, POLL_SLOW = 6 * 3600, DAY


@dataclass(frozen=True)
class Ingredient:
    source_id: str
    kind: str                      # fred | cboe | yahoo | multpl | lbma
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
    _f("DFII10", "percent", ["real_rate_10y_tips", "gold_real_rate_cross"], feed="FRED:DFII10"),
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
    # ---- WO-1.6: substitute / ported-rule inputs (see SUBSTITUTED_FEEDS) ---------------------
    # buffett_indicator: Z.1 corporate equities (market value, $ millions) over nominal GDP ($ billions).
    # Both are quarterly and FRED dates them at the quarter START; they are aged from the quarter END
    # (the ``quarter_end`` as-of rule), the period they describe, as ``month_end`` does for monthly series.
    _f("NCBEILQ027S", "usd_millions", ["buffett_indicator"], "COMPONENT", poll=POLL_SLOW, rule="quarter_end",
       feed="FRED:NCBEILQ027S", stands="FRED NCBEILQ027S (Z.1 nonfinancial corporate equities, market value, $M)"),
    _f("GDP", "usd_billions", ["buffett_indicator"], "COMPONENT", poll=POLL_SLOW, rule="quarter_end", feed="FRED:GDP",
       stands="FRED GDP (nominal GDP, $B, annual rate)"),
    # fiscal_dominance: the legacy discriminator's two inputs, as RAW LEVEL HISTORY. The engine takes the
    # 12-month change of WALCL and the 3-month annualised change of core CPI; the collector computes neither.
    # WALCL is weekly (history 70 rows spans the 53 weeks the year-on-year needs, with slack); CPILFESL is
    # monthly (history 8 rows: the latest, and the one 3 months before it, with slack for a missing month).
    _f("WALCL", "usd_millions", ["fiscal_dominance"], "COMPONENT", poll=POLL_SLOW, history=70, feed="FRED:WALCL",
       stands="FRED WALCL (Fed total assets, $M) with its last 70 weekly levels"),
    _f("CPILFESL", "index", ["fiscal_dominance"], "COMPONENT", poll=POLL_SLOW, rule="month_end", history=8,
       feed="FRED:CPILFESL", stands="FRED CPILFESL (core CPI index) with its last 8 monthly levels"),
    # ---- LBMA (gold_spot) ---------------------------------------------------------------
    Ingredient("lbma.gold_fix_usd", "lbma", "gold_pm+gold_am", "usd_per_oz", "market:XAUUSD (LBMA PM fix, AM fallback)",
               ("gold_spot",), "DIRECT", POLL_DAILY,
               stands_for="LBMA daily gold fix in USD per troy ounce: the PM fix, else that date's AM fix"),
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
    Ingredient("yahoo.GC=F", "yahoo", "GC=F", "usd_per_oz", "market:HG,GC", ("copper_gold", "gold_real_rate_cross"),
               "COMPONENT", POLL_DAILY, stands_for="COMEX gold front-month close"),
    # ---- multpl (declared: multpl/Shiller) ---------------------------------------------
    # A NEW source id (was ``multpl.shiller_pe``, latest figure only): the payload now carries the
    # whole published monthly table for the engine's percentile, and the store keeps the first
    # payload admitted per source period, so reusing the id would have kept the history-less
    # reading in place until multpl's date rolled over. The old id's readings are left untouched.
    Ingredient("multpl.shiller_pe_table", "multpl", "shiller-pe", "ratio", "multpl/Shiller", ("shiller_cape",),
               "COMPONENT", POLL_SLOW, history=2400,
               stands_for="Shiller CAPE as published, with multpl's full monthly table (the engine percentiles it)"),
)

#: DRTSCILM is only the automatic leg of sloos_bank_lending; the NDFI leg is a manual
#: transcription from the Fed's SLOOS Table 2 and has no feed. The indicator therefore stays
#: ``registration_pending`` in the mapping and must not read as complete.
PARTIAL: dict[str, str] = {
    "sloos_bank_lending": "auto C&I leg (FRED:DRTSCILM) is live; the manual NDFI leg "
    "(Fed SLOOS Table 2 Q14, avg of 5 sub-categories) has no machine-readable feed.",
}

#: Indicators whose DECLARED source cannot be reached with public/free data, or whose
#: definition needs a decision this module has no authority to make. No substitute is wired.
NOT_TRACTABLE: dict[str, str] = {
    "ism_manufacturing": "Declared feed 'ISM'. ISM PMI is licensed; FRED withdrew NAPM "
    "(HTTP 404). Needs a paid/licensed feed or an approved substitute (e.g. regional Fed "
    "surveys), which changes what the indicator means.",
    "private_credit_stress": "Declared composite of BDC NAV discount + non-accrual rate + PIK "
    "share (quarterly SEC filings) + a public-spread proxy. The composite's weighting and the "
    "per-BDC universe are undefined; filing extraction is a build in its own right.",
}

#: Indicators WIRED (WO-1.6) from a feed or rule that is NOT the one the ratified mapping row declares.
#: A substitute is a provenance decision; each is recorded here with whose authority it rests on, and
#: ``tests/test_ingestion.py`` allows a catalog/mapping feed mismatch for exactly these and no others.
SUBSTITUTED_FEEDS: dict[str, str] = {
    "buffett_indicator": "Declared 'Wilshire/GDP, percentiled'; Wilshire is unavailable (FRED withdrew WILL5000PRFC). "
    "Wired as the Z.1 ratio FRED NCBEILQ027S / (GDP*1000), in percent, banded as that ratio (the row's "
    "'percentiled' step is NOT applied). Substitute accepted by Matt per the Trinity dispatch of WO-1.6; the legacy "
    "engine proved it live (Trinity 2026-07-07, ~218%). Its staleness window is overridden (see WINDOW_OVERRIDES).",
    "fiscal_dominance": "Declared 'Treasury/BEA deficit + interest-cost: deficit/GDP vs interest-cost/revenue, "
    "discriminated vs benign growth'. Wired instead as the legacy ARGUS crash-engine discriminator (fred_tells.py, "
    "R2D2-locked bands): Fed balance-sheet (WALCL) growth >= 10% over 12 months AND core CPI (CPILFESL) >= 4% "
    "annualised over 3 months, as a conjunction. This is a DIFFERENT quantity from the ratified row's wording "
    "(monetisation vs deficit/interest burden). Ported on the Trinity dispatch of WO-1.6; OWNER CONFIRMATION that it "
    "may stand for this row is OUTSTANDING.",
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
}


def window_seconds(indicator_id: str, ratified_seconds: float) -> float:
    """The staleness window to apply: the ratified one unless a recorded override replaces it."""
    override = WINDOW_OVERRIDES.get(indicator_id)
    return float(override[0]) if override else float(ratified_seconds)


EGRESS_HOSTS: dict[str, str] = {
    "fred.stlouisfed.org": "Federal Reserve Bank of St. Louis",
    "cdn-api.cboe.com": "Cboe Global Markets",
    "query1.finance.yahoo.com": "Yahoo",
    "www.multpl.com": "multpl.com",
    "prices.lbma.org.uk": "LBMA (London Bullion Market Association)",
}


def build_adapter(ing: Ingredient, clock: Callable[[], datetime]):
    common = dict(source_id=ing.source_id, as_of_rule=ing.as_of_rule, unit=ing.unit, clock=clock)
    if ing.kind == "fred":
        return FredAdapter(ing.ref, ing.transformation, ing.history, **common)
    if ing.kind == "cboe":
        return CboeAdapter(ing.ref, ing.column, **common)
    if ing.kind == "yahoo":
        return YahooChartAdapter(ing.ref, ing.history, **common)
    if ing.kind == "multpl":
        return MultplShillerAdapter(history=ing.history, **common)
    if ing.kind == "lbma":
        return LbmaGoldAdapter(**common)
    raise ValueError(f"unknown ingredient kind {ing.kind!r}")
