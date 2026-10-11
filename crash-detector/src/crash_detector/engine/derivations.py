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
    "derive",
]

#: A percentile over fewer points than this is a truncated or broken page, not a history.
MINIMUM_PERCENTILE_HISTORY = 360


class DerivationKind(Enum):
    RATIO = "ratio"
    PERCENT_VS_AVERAGE = "percent_vs_average"
    PERCENTILE = "percentile"


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
    return _percentile(spec, inputs)
