"""The ingredient catalog: which declared feed serves which ratified indicator.

DERIVED FROM ``governance/mapping/indicator_mapping.yaml`` (Matt-ratified 2026-08-24) and
nothing else. No source here is a choice made by this module: each ``Ingredient`` is the
feed a mapping row already declares (``source.feed``), reached by the nearest public
endpoint. Where the declared source cannot be reached publicly, the indicator is listed in
:data:`NOT_TRACTABLE` with the reason, and NO substitute is wired — a substitute would be a
provenance decision, which is not this module's to make.

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
    MultplShillerAdapter,
    YahooChartAdapter,
)

__all__ = ["Ingredient", "INGREDIENTS", "NOT_TRACTABLE", "PARTIAL", "EGRESS_HOSTS", "build_adapter"]

DAY, WEEK = 86_400, 7 * 86_400
#: Polling interval, deliberately independent of publication cadence: a daily series is
#: polled every 6h so a late print is caught the same day; slower series are polled daily.
#: Re-polling is free of side effects on readings (idempotent on source period).
POLL_DAILY, POLL_SLOW = 6 * 3600, DAY


@dataclass(frozen=True)
class Ingredient:
    source_id: str
    kind: str                      # fred | cboe | yahoo | multpl
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


def _f(series, unit, serves, completes="DIRECT", *, poll=POLL_DAILY, rule="obs_date", tr=None, feed=None, stands=""):
    sid = f"fred.{series}" + (f".{tr}" if tr else "")
    return Ingredient(sid, "fred", series, unit, feed or f"FRED:{series}", tuple(serves), completes, poll, rule, tr,
                      stands_for=stands or f"FRED {series}" + (f" ({tr})" if tr else ""))


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
    Ingredient("multpl.shiller_pe", "multpl", "shiller-pe", "ratio", "multpl/Shiller", ("shiller_cape",), "COMPONENT",
               POLL_SLOW, stands_for="Shiller CAPE as published (the engine percentiles it)"),
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
    "buffett_indicator": "Declared 'Wilshire/GDP'. FRED withdrew the Wilshire 5000 series "
    "(WILL5000PRFC -> HTTP 404) and Wilshire publishes no free market-cap series. A FRED "
    "Z.1 corporate-equities/GDP ratio would be a different provenance: a Product Owner call.",
    "ism_manufacturing": "Declared feed 'ISM'. ISM PMI is licensed; FRED withdrew NAPM "
    "(HTTP 404). Needs a paid/licensed feed or an approved substitute (e.g. regional Fed "
    "surveys), which changes what the indicator means.",
    "gold_spot": "Declared 'market:XAUUSD, spot'. No keyless public spot source reachable "
    "(Yahoo XAUUSD=X -> 404; Stooq requires JS/key; FRED gold fixing withdrawn). GC=F futures "
    "is ingested for copper_gold/gold_real_rate_cross where the mapping declares futures, "
    "but futures is not spot: using it here is a provenance decision.",
    "private_credit_stress": "Declared composite of BDC NAV discount + non-accrual rate + PIK "
    "share (quarterly SEC filings) + a public-spread proxy. The composite's weighting and the "
    "per-BDC universe are undefined; filing extraction is a build in its own right.",
    "fiscal_dominance": "Declared 'derived, playbook' discriminator (deficit/GDP vs "
    "interest-cost/revenue vs benign growth). The discriminator rule is not in the mapping; "
    "the Treasury/BEA components are public but cannot be wired without that definition.",
}

EGRESS_HOSTS: dict[str, str] = {
    "fred.stlouisfed.org": "Federal Reserve Bank of St. Louis",
    "cdn-api.cboe.com": "Cboe Global Markets",
    "query1.finance.yahoo.com": "Yahoo",
    "www.multpl.com": "multpl.com",
}


def build_adapter(ing: Ingredient, clock: Callable[[], datetime]):
    common = dict(source_id=ing.source_id, as_of_rule=ing.as_of_rule, unit=ing.unit, clock=clock)
    if ing.kind == "fred":
        return FredAdapter(ing.ref, ing.transformation, **common)
    if ing.kind == "cboe":
        return CboeAdapter(ing.ref, ing.column, **common)
    if ing.kind == "yahoo":
        return YahooChartAdapter(ing.ref, ing.history, **common)
    if ing.kind == "multpl":
        return MultplShillerAdapter(**common)
    raise ValueError(f"unknown ingredient kind {ing.kind!r}")
