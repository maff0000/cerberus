"""The derived indicators' computation (CERBERUS WO-1.5): the ENGINE derives, the collector never does.

BLUEPRINT §5 (collector-never-computes) puts every ratio, average and percentile on this side
of the raw/dial boundary. The ingestion layer stores what a source SAID (a close, a date, and
for two sources a raw history of closes); this module turns those stored readings into the one
number a ratified indicator row declares, and it is the only place that does.

SIX CALCULATIONS, EACH THE ROW'S DECLARED ONE (``governance/mapping/indicator_mapping.yaml``):

``RATIO``              ``breadth_rsp_spy`` (RSP / SPY), ``credit_stress_hyg_lqd`` (HYG / LQD),
                       ``copper_gold`` (HG / GC, scaled x1000 so the figure is readable),
                       ``vix_term_structure`` (VIX / VIX3M).
``PERCENT_VS_AVERAGE`` ``spx_vs_200dma``: percent the latest S&P 500 close sits above (+) or
                       below (-) the simple average of its last 200 closes.
``PERCENTILE``         ``shiller_cape``: where the latest CAPE sits in its own published
                       monthly history, 0-100.
``RATIO``  (WO-1.6)    ``buffett_indicator``: Z.1 corporate equities ($M) over nominal GDP ($B),
                       in percent: ``NCBEILQ027S / (GDP * 1000) * 100``, i.e. a RATIO with scale 0.1.
``FISCAL_CONJUNCTION`` ``fiscal_dominance`` (WO-1.6): the legacy ARGUS discriminator. Fed balance-sheet
                       (WALCL) growth over 12 months >= 10% AND core CPI annualised over 3 months >= 4%.
                       Both legs or nothing: balance-sheet growth alone never fires. 1.0 = fired, 0.0 = not.

NOTHING IS FILLED IN. A derivation that cannot be computed RAISES :class:`DerivationUnavailable`
carrying a plain reason and no number; the caller emits NO observation and the dial sees an
absence, never a default (CD-AC-001). Specifically:

* a ratio is taken only between two closes of THE SAME SOURCE DATE (the newest date both
  components have): a ratio of Thursday's numerator to Wednesday's denominator is not a
  measurement of anything;
* a 200-day average is taken only over 200 REAL stored closes whose last date is the reading's
  own date. A shorter history is refused with the count it holds, not averaged short;
* a percentile is taken only over a history of at least ``MINIMUM_PERCENTILE_HISTORY`` points,
  a guard against a truncated page, not a calibration.

Every figure here is a measurement of stored data. The bands that turn it into a stress score
are a different thing and live, labelled PROVISIONAL, in ``deploy/indicator-scaling.json``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

from crash_detector.admission import admits
from crash_detector.establishment import each_of, establishes

__all__ = [
    "DERIVATIONS",
    "Derivation",
    "DerivationKind",
    "DerivationUnavailable",
    "Derived",
    "MINIMUM_PERCENTILE_HISTORY",
    "FISCAL_BALANCE_SHEET_GROWTH_FIRE",
    "FISCAL_CORE_CPI_ANNUALISED_FIRE_PERCENT",
    "CORRELATION_WINDOW",
    "DRAWDOWN_WINDOW",
    "MINIMUM_SURVEY_HISTORY",
    "derive",
]

#: A percentile over fewer points than this is a truncated or broken page, not a history.
MINIMUM_PERCENTILE_HISTORY = 360

#: The fiscal-dominance discriminator's two fire bands. NOT chosen here: they are the legacy ARGUS
#: crash-engine's, which records them as R2D2-LOCKED (migration 072, ``fred_tells.py``): Fed total assets
#: growth >= 10% over 12 months AND core CPI >= 4.0% annualised over the latest 3 months.
FISCAL_BALANCE_SHEET_GROWTH_FIRE = 0.10
FISCAL_CORE_CPI_ANNUALISED_FIRE_PERCENT = 4.0
#: The legacy look-back for the balance-sheet leg: the latest level against the last level on or before
#: this many days earlier (365 = 12 months).
FISCAL_BALANCE_SHEET_LOOKBACK_DAYS = 365
FISCAL_CORE_CPI_MONTHS = 3

#: WO-1.7 ``gold_real_rate_cross``: rolling-correlation window in aligned trading-day changes. TRINITY'S PROVISIONAL
#: CHOICE, not Owner-ratified and not calibrated; changing it is a one-line edit in ``DERIVATIONS``.
CORRELATION_WINDOW = 60

#: WO-1.7 ``ism_manufacturing``: a survey's z-score needs at least this many monthly points (10 years); a shorter page
#: is a truncated fetch, not a distribution.
MINIMUM_SURVEY_HISTORY = 120


#: WO-1.8 ``private_credit_stress`` v1: the trailing-high look-back, in trading days (~1 year, the usual drawdown
#: convention). TRINITY'S PROVISIONAL CHOICE, not Owner-ratified and not calibrated.
DRAWDOWN_WINDOW = 252


class DerivationKind(Enum):
    RATIO = "ratio"
    PERCENT_VS_AVERAGE = "percent_vs_average"
    PERCENTILE = "percentile"
    FISCAL_CONJUNCTION = "fiscal_conjunction"
    CORRELATION_PERCENTILE = "correlation_percentile"
    Z_COMPOSITE = "z_composite"
    LEG_MEAN = "leg_mean"
    DRAWDOWN = "drawdown"


class DerivationUnavailable(Exception):
    """The indicator cannot be computed from what is stored. Carries a reason and NO number."""


@establishes(
    kind=DerivationKind,
    roles=each_of(str, within=(tuple,)),
    unit=str,
    scale=float,
    window=int,
)
@dataclass(frozen=True)
class Derivation:
    # SEALED against forged state (PO-DECISIONS-0016 ruling 2); slots forbid field defaults, so none are declared.
    __slots__ = ("kind", "roles", "unit", "scale", "window")

    kind: DerivationKind
    #: input role names, in the order the caller supplies them
    roles: tuple
    unit: str
    scale: float
    window: int


@establishes(
    value=float,
    observation_date=str,
    unit=str,
)
@dataclass(frozen=True)
class Derived:
    __slots__ = ("value", "observation_date", "unit")

    value: float
    observation_date: str
    unit: str


DERIVATIONS = {
    "breadth_rsp_spy": Derivation(DerivationKind.RATIO, ("numerator", "denominator"), "ratio", 1.0, 0),
    "credit_stress_hyg_lqd": Derivation(DerivationKind.RATIO, ("numerator", "denominator"), "ratio", 1.0, 0),
    "copper_gold": Derivation(DerivationKind.RATIO, ("numerator", "denominator"), "ratio_x1000", 1000.0, 0),
    "vix_term_structure": Derivation(DerivationKind.RATIO, ("numerator", "denominator"), "ratio", 1.0, 0),
    "spx_vs_200dma": Derivation(DerivationKind.PERCENT_VS_AVERAGE, ("series",), "percent_vs_200dma", 1.0, 200),
    "shiller_cape": Derivation(DerivationKind.PERCENTILE, ("series",), "percentile", 1.0, 0),
    # NCBEILQ027S is in $ millions and GDP in $ billions: (NCB / (GDP * 1000)) * 100 == NCB / GDP * 0.1.
    "buffett_indicator": Derivation(DerivationKind.RATIO, ("numerator", "denominator"), "percent_of_gdp", 0.1, 0),
    "fiscal_dominance": Derivation(
        DerivationKind.FISCAL_CONJUNCTION, ("balance_sheet", "core_price_index"), "fired_flag", 1.0, 0
    ),
    # WO-1.7 (all three provisional, see ingestion.catalog.SUBSTITUTED_FEEDS and STATUS.md):
    "gold_real_rate_cross": Derivation(
        DerivationKind.CORRELATION_PERCENTILE, ("gold", "real_rate"), "percentile_of_rolling_corr", 1.0, CORRELATION_WINDOW
    ),
    "ism_manufacturing": Derivation(
        DerivationKind.Z_COMPOSITE, ("philadelphia", "new_york", "dallas"), "regional_survey_z_composite", 1.0, 0
    ),
    "sloos_bank_lending": Derivation(
        DerivationKind.LEG_MEAN, ("commercial_industrial", "ndfi"), "net_percent_tightening", 1.0, 0
    ),
    # WO-1.8: a MARKET-PRICE PROXY for the ratified composite (BDC NAV discount + non-accrual + PIK), see SUBSTITUTED_FEEDS.
    "private_credit_stress": Derivation(
        DerivationKind.DRAWDOWN, ("series",), "percent_below_trailing_high", 1.0, DRAWDOWN_WINDOW
    ),
}


def _number(owner: str, value: object) -> float:
    if type(value) is bool or type(value) not in (int, float):
        raise DerivationUnavailable(f"{owner} is not a plain number")
    number = float(value)
    if not math.isfinite(number):
        raise DerivationUnavailable(f"{owner} is not finite")
    return number


def _dated_value(owner: str, payload: object) -> tuple:
    if type(payload) is not dict:
        raise DerivationUnavailable(f"{owner}: stored payload is not an object")
    date_text = payload.get("observation_date")
    if type(date_text) is not str:
        raise DerivationUnavailable(f"{owner}: stored reading carries no observation_date")
    return date_text, _number(f"{owner} value", payload.get("value"))


def _ratio(spec: Derivation, inputs: dict) -> Derived:
    top = {}
    bottom = {}
    for owner, readings, into in (("numerator", inputs["numerator"], top), ("denominator", inputs["denominator"], bottom)):
        for payload in readings:
            date_text, value = _dated_value(owner, payload)
            if date_text not in into:
                into[date_text] = value
    common = sorted(set(top) & set(bottom), reverse=True)
    if not common:
        raise DerivationUnavailable(
            "no source date has both a numerator and a denominator reading "
            f"(numerator dates {sorted(top, reverse=True)[:3]}, denominator dates {sorted(bottom, reverse=True)[:3]})"
        )
    date_text = common[0]
    if bottom[date_text] <= 0.0:
        raise DerivationUnavailable("denominator is not positive")
    value = top[date_text] / bottom[date_text] * spec.scale
    if not math.isfinite(value):
        raise DerivationUnavailable("ratio is not finite")
    return Derived(value=value, observation_date=date_text, unit=spec.unit)


def _history_of(owner: str, payload: object) -> list:
    if type(payload) is not dict or type(payload.get("history")) is not list:
        raise DerivationUnavailable(f"{owner}: stored reading carries no raw history")
    rows = []
    previous = ""
    for row in payload["history"]:
        if type(row) is not list or len(row) != 2 or type(row[0]) is not str:
            raise DerivationUnavailable(f"{owner}: history row is not a [date, number] pair")
        if row[0] <= previous:
            raise DerivationUnavailable(f"{owner}: history is not strictly increasing by date")
        previous = row[0]
        rows.append((row[0], _number(f"{owner} history value", row[1])))
    return rows


def _percent_vs_average(spec: Derivation, inputs: dict) -> Derived:
    latest = inputs["series"][0]
    date_text, value = _dated_value("series", latest)
    rows = _history_of("series", latest)
    if len(rows) < spec.window:
        raise DerivationUnavailable(
            f"the stored history holds {len(rows)} closes; a {spec.window}-day average needs {spec.window}. "
            "No shorter average is substituted."
        )
    if rows[-1][0] != date_text:
        raise DerivationUnavailable(
            f"the history ends {rows[-1][0]} but the reading is dated {date_text}; they must be the same close"
        )
    if not math.isclose(rows[-1][1], value, rel_tol=1e-9):
        raise DerivationUnavailable("the reading's value is not the last close of its own history")
    window = [close for _, close in rows[-spec.window:]]
    average = sum(window) / len(window)
    if average <= 0.0:
        raise DerivationUnavailable("the average is not positive")
    return Derived(value=(rows[-1][1] / average - 1.0) * 100.0, observation_date=date_text, unit=spec.unit)


def _percentile(spec: Derivation, inputs: dict) -> Derived:
    latest = inputs["series"][0]
    date_text, value = _dated_value("series", latest)
    rows = [close for day, close in _history_of("series", latest) if day != date_text]
    if len(rows) < MINIMUM_PERCENTILE_HISTORY:
        raise DerivationUnavailable(
            f"the stored history holds {len(rows)} points; a percentile needs at least {MINIMUM_PERCENTILE_HISTORY}"
        )
    at_or_below = 1 + sum(1 for close in rows if close <= value)
    return Derived(value=100.0 * at_or_below / (len(rows) + 1), observation_date=date_text, unit=spec.unit)


def _dated_rows(owner: str, payload: object) -> list:
    """The payload's raw ``[date, number]`` history as ascending ``(date, number)`` pairs, dates validated."""
    rows = _history_of(owner, payload)
    for day, _ in rows:
        try:
            date.fromisoformat(day)
        except ValueError:
            raise DerivationUnavailable(f"{owner}: history date {day!r} is not an ISO date") from None
    return rows


def _fiscal_conjunction(spec: Derivation, inputs: dict) -> Derived:
    """The legacy discriminator, ported: fired only if BOTH legs are over their band.

    Balance-sheet leg: latest WALCL level against the last level on or before 365 days earlier.
    Core-CPI leg: ``(latest / level 3 months earlier) ** 4 - 1``, in percent. The level 3 months earlier
    must BE the level dated exactly 3 calendar months before the latest one: a missing month (FRED has
    had unpublished months) is refused, not bridged by taking whichever level is four rows back.
    The reading is dated by the OLDER of the two legs' latest dates, so it is never fresher than its
    stalest input.
    """
    walcl = _dated_rows("balance_sheet", inputs["balance_sheet"][0])
    core = _dated_rows("core_price_index", inputs["core_price_index"][0])
    if not walcl or not core:
        raise DerivationUnavailable("a leg of the fiscal discriminator carries no history")
    last_day, last_level = walcl[-1]
    cutoff = (date.fromisoformat(last_day) - timedelta(days=FISCAL_BALANCE_SHEET_LOOKBACK_DAYS)).isoformat()
    prior = [level for day, level in walcl if day <= cutoff]
    if not prior:
        raise DerivationUnavailable(
            f"the balance-sheet history ({walcl[0][0]}..{last_day}) does not reach back {FISCAL_BALANCE_SHEET_LOOKBACK_DAYS} days"
        )
    if prior[-1] <= 0.0:
        raise DerivationUnavailable("the prior balance-sheet level is not positive")
    growth = (last_level - prior[-1]) / prior[-1]

    core_day, core_level = core[-1]
    latest = date.fromisoformat(core_day)
    month_index = latest.year * 12 + latest.month - 1 - FISCAL_CORE_CPI_MONTHS
    earlier_day = date(month_index // 12, month_index % 12 + 1, 1).isoformat()
    earlier = [level for day, level in core if day == earlier_day]
    if not earlier:
        raise DerivationUnavailable(
            f"core price index has no level dated {earlier_day}, {FISCAL_CORE_CPI_MONTHS} months before {core_day}"
        )
    if earlier[0] <= 0.0 or core_level <= 0.0 or latest.day != 1:
        raise DerivationUnavailable("core price index levels must be positive and month-start dated")
    annualised = ((core_level / earlier[0]) ** (12 // FISCAL_CORE_CPI_MONTHS) - 1.0) * 100.0
    if not (math.isfinite(growth) and math.isfinite(annualised)):
        raise DerivationUnavailable("a leg of the fiscal discriminator is not finite")
    fired = growth >= FISCAL_BALANCE_SHEET_GROWTH_FIRE and annualised >= FISCAL_CORE_CPI_ANNUALISED_FIRE_PERCENT
    return Derived(value=1.0 if fired else 0.0, observation_date=min(last_day, core_day), unit=spec.unit)


def _pearson(owner: str, xs: list, ys: list) -> float:
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    syy = sum((y - mean_y) ** 2 for y in ys)
    if sxx <= 0.0 or syy <= 0.0:
        raise DerivationUnavailable(f"{owner}: a window has zero variance, so its correlation is undefined")
    r = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)
    return max(-1.0, min(1.0, r))


def _correlation_percentile(spec: Derivation, inputs: dict) -> Derived:
    """``gold_real_rate_cross`` (TRINITY'S PROVISIONAL CONSTRUCTION; not Owner-ratified; uncalibrated).

    Align the two daily histories on the dates BOTH have. Between consecutive shared dates take gold's simple return
    and the real yield's change in percentage points. The rolling Pearson correlation of the last ``window`` such pairs
    is normally negative (gold rises as real yields fall); the figure is the percentile, 0-100, of the LATEST rolling
    correlation within every rolling correlation the stored history yields, so a flip toward positive reads high.
    CAVEAT: this is relative to the series' own history, not an absolute test (the correlation level is never checked), so
    ~10% of the time it reads stress with no sign flip. Provisional by design.
    Changes are between consecutive SHARED dates whatever the gap (a holiday makes a multi-day change). A zero-variance
    window in the old history is skipped; the latest window being flat is refused.
    Refused, never shortened, when there are too few correlations to percentile.
    """
    gold = dict(_dated_rows("gold", inputs["gold"][0]))
    real = dict(_dated_rows("real_rate", inputs["real_rate"][0]))
    if any(level <= 0.0 for level in gold.values()):
        raise DerivationUnavailable("gold: a non-positive price cannot be turned into a return")
    shared = sorted(set(gold) & set(real))
    if len(shared) < spec.window + 1:
        raise DerivationUnavailable(f"only {len(shared)} shared dates; a {spec.window}-change correlation needs {spec.window + 1}")
    gold_change = [gold[b] / gold[a] - 1.0 for a, b in zip(shared, shared[1:])]
    real_change = [real[b] - real[a] for a, b in zip(shared, shared[1:])]
    # A degenerate (zero-variance) window has no defined correlation. One in the old history is skipped (it carries no
    # information) rather than disabling the indicator for a decade; the LATEST window being degenerate is refused.
    correlations = []
    for i in range(spec.window, len(gold_change) + 1):
        try:
            correlations.append(_pearson("gold_real_rate_cross", gold_change[i - spec.window:i], real_change[i - spec.window:i]))
        except DerivationUnavailable:
            if i == len(gold_change):
                raise
    latest, earlier = correlations[-1], correlations[:-1]
    if len(earlier) < MINIMUM_PERCENTILE_HISTORY:
        raise DerivationUnavailable(
            f"the stored history yields {len(earlier)} earlier correlations; a percentile needs at least {MINIMUM_PERCENTILE_HISTORY}"
        )
    at_or_below = 1 + sum(1 for c in earlier if c <= latest)
    return Derived(value=100.0 * at_or_below / (len(earlier) + 1), observation_date=shared[-1], unit=spec.unit)


def _z_composite(spec: Derivation, inputs: dict) -> Derived:
    """``ism_manufacturing`` substitute: the equal-weighted mean of each regional survey's z-score.

    Each survey is z-scored against its OWN full stored history (population standard deviation, the latest point
    included). The composite is taken at the newest month ALL regions share; a region that has not yet reported that
    month holds the composite at the previous shared month rather than being dropped (a two-region mean is a different
    quantity). In-sample and uncalibrated.
    """
    zscores = []
    for role in spec.roles:
        rows = _dated_rows(role, inputs[role][0])
        if len(rows) < MINIMUM_SURVEY_HISTORY:
            raise DerivationUnavailable(f"{role}: {len(rows)} monthly points; a z-score needs at least {MINIMUM_SURVEY_HISTORY}")
        values = [v for _, v in rows]
        mean = sum(values) / len(values)
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
        if std <= 0.0:
            raise DerivationUnavailable(f"{role}: the history has zero variance")
        zscores.append({day: (v - mean) / std for day, v in rows})
    shared = set(zscores[0])
    for z in zscores[1:]:
        shared &= set(z)
    if not shared:
        raise DerivationUnavailable("no month is reported by every regional survey")
    day = max(shared)
    return Derived(value=sum(z[day] for z in zscores) / len(zscores), observation_date=day, unit=spec.unit)


def _leg_mean(spec: Derivation, inputs: dict) -> Derived:
    """``sloos_bank_lending``: the plain mean of the automatic C&I leg and the hand-entered NDFI leg.

    Both legs are required; a missing one is DerivationUnavailable and never filled. The figure is dated by the OLDER
    leg, so it ages out when either leg does. The mean is an engineering choice (the row says '+', not how to combine).
    """
    values, days = [], []
    for role in spec.roles:
        day, value = _dated_value(role, inputs[role][0])
        if not -100.0 <= value <= 100.0:
            raise DerivationUnavailable(f"{role}: {value} is not a net percentage in [-100, 100]")
        values.append(value)
        days.append(day)
    return Derived(value=sum(values) / len(values), observation_date=min(days), unit=spec.unit)


def _drawdown(spec: Derivation, inputs: dict) -> Derived:
    """``private_credit_stress`` v1 (TRINITY'S PROVISIONAL CONSTRUCTION; a market-price proxy; uncalibrated).

    The percent the latest close sits BELOW the highest close of the last ``window`` closes (the latest included), so
    the figure is never negative: 0 = at a new high, 25 = 25% below it. Higher = more stress, matching the row's
    ``high_is_worse``. The history must hold ``window`` real closes ending on the reading's own date and value; a
    shorter history is refused with its count, not measured over a shorter (easier-to-be-near-the-high) window.
    """
    latest = inputs["series"][0]
    date_text, value = _dated_value("series", latest)
    rows = _dated_rows("series", latest)
    if len(rows) < spec.window:
        raise DerivationUnavailable(
            f"the stored history holds {len(rows)} closes; a {spec.window}-day trailing high needs {spec.window}. "
            "No shorter window is substituted."
        )
    if rows[-1][0] != date_text:
        raise DerivationUnavailable(
            f"the history ends {rows[-1][0]} but the reading is dated {date_text}; they must be the same close"
        )
    if not math.isclose(rows[-1][1], value, rel_tol=1e-9):
        raise DerivationUnavailable("the reading's value is not the last close of its own history")
    closes = [close for _, close in rows[-spec.window:]]
    if any(close <= 0.0 for close in closes):
        raise DerivationUnavailable("a non-positive close cannot be drawn down from")
    return Derived(value=(1.0 - closes[-1] / max(closes)) * 100.0, observation_date=date_text, unit=spec.unit)


@admits(indicator_id=str, inputs=dict)
def derive(indicator_id: str, inputs: dict) -> Derived:
    """Compute one derived indicator from its stored component readings.

    ``inputs`` maps each of the derivation's role names to that component's stored payloads,
    NEWEST FIRST (at least one). Raises :class:`DerivationUnavailable` when the figure cannot
    be computed; there is no return path that carries a number for an absence.
    """
    spec = DERIVATIONS.get(indicator_id)
    if spec is None:
        raise ValueError(f"{indicator_id!r} is not a derived indicator")
    if set(inputs) != set(spec.roles):
        raise ValueError(f"{indicator_id!r} takes inputs {sorted(spec.roles)}, got {sorted(inputs)}")
    for role, readings in inputs.items():
        if type(readings) is not list or not readings:
            raise DerivationUnavailable(f"no stored reading for {role}")
    if spec.kind is DerivationKind.RATIO:
        return _ratio(spec, inputs)
    if spec.kind is DerivationKind.PERCENT_VS_AVERAGE:
        return _percent_vs_average(spec, inputs)
    if spec.kind is DerivationKind.FISCAL_CONJUNCTION:
        return _fiscal_conjunction(spec, inputs)
    if spec.kind is DerivationKind.CORRELATION_PERCENTILE:
        return _correlation_percentile(spec, inputs)
    if spec.kind is DerivationKind.Z_COMPOSITE:
        return _z_composite(spec, inputs)
    if spec.kind is DerivationKind.LEG_MEAN:
        return _leg_mean(spec, inputs)
    if spec.kind is DerivationKind.DRAWDOWN:
        return _drawdown(spec, inputs)
    return _percentile(spec, inputs)
