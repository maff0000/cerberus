"""WO-1.3b-II: ``trend_confirmed`` FOR THE EQUITY DIAL - the S&P 500 above a FLATTENING 200-day mean.

Until this WO the pass supplied :data:`evaluator.pass_once.TREND_NOT_COMPUTED` (always False, spec §7's scope cut), so
spec §3 rule 5 could never fire and a dial in ALARM could only ever leave toward WATCH and then walk to CALM on two
persistence counts: R2D2's F1 back door. The post-ALARM lock (:func:`evaluator.resolve.official_state_for_dial`)
closes that door by making RECOVERY the only way out, and **a lock whose key is never cut is a dial that halts
forever** - R2D2's own harness labels that configuration "permanent lock!". So the lock and the trend ship together,
and this is the trend.

IT IS R2D2's DEFINITION, COPIED FROM HER MEASURED HARNESS (``/srv/r2d2/tools/cerberus_replay/harness/eval_lock.py``,
function ``trend``), not an approximation of the report's prose::

    ma(i)   = mean of the 200 closes ending at close i
    trend   = close(i) > ma(i)  AND  ma(i) / ma(i - 20) - 1 >= -0.0025       (and False with fewer than 220 closes)

so it needs 220 real closes ending on the latest reading's own date. The catalogue stores 260
(``ingestion/catalog.py``, ``yahoo.^GSPC``, ``history=260``).

**EVERY FAILURE IS FALSE, AND FALSE IS THE CONSERVATIVE ANSWER.** A missing series, a short history, a history that is
not strictly increasing, a last close that is not the reading's own, a reading older than the market-day window: each
is "trend not confirmed", never an exception that stops the pass and never a guess. False can only KEEP an armed dial
out of RECOVERY longer; it cannot manufacture a recovery (the same argument :data:`evaluator.pass_once.TREND_NOT_COMPUTED`
made). The cost is that a broken S&P feed holds a locked dial in WATCH - the halt-biased direction this dial is built
to err in - and the dial's other inputs go UNKNOWN long before then.

SCOPE: THE EQUITY DIAL ONLY. R2D2 measured the lock on the equity dial's S&P history; the monetary dial has no
comparable trend measure and no replay, so :func:`evaluator.pass_once.one_pass_for_dial` does not arm the lock there.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta

from ingestion.store import SqliteStore

__all__ = [
    "TREND_SOURCE_ID",
    "TREND_AVERAGE_CLOSES",
    "TREND_SLOPE_LOOKBACK_CLOSES",
    "TREND_FLATTENING_TOLERANCE",
    "TREND_MINIMUM_CLOSES",
    "TREND_MAXIMUM_AGE_DAYS",
    "trend_confirmed_from_closes",
    "equity_trend_confirmed",
]

#: The raw-store source whose stored history this reads: the same S&P 500 series ``spx_vs_200dma`` is derived from.
TREND_SOURCE_ID = "yahoo.^GSPC"

#: R2D2's 200-day simple mean.
TREND_AVERAGE_CLOSES = 200

#: How far back the mean is compared with itself: its value 20 closes ago.
TREND_SLOPE_LOOKBACK_CLOSES = 20

#: "Flattening" = the 200-day mean has not fallen by more than 0.25% over the lookback. R2D2's ``tol=-0.0025``.
TREND_FLATTENING_TOLERANCE = -0.0025

#: 200 closes ending 20 closes ago needs 220 in all (her ``i < 219`` index guard).
TREND_MINIMUM_CLOSES = TREND_AVERAGE_CLOSES + TREND_SLOPE_LOOKBACK_CLOSES

#: The newest close may be no older than this many days at ``now``: the market-day relevance window of WO-1.9 (7 days,
#: worst-case ~6-day gap plus a day's grace). An older series is a dead feed, and a dead feed confirms nothing.
TREND_MAXIMUM_AGE_DAYS = 7


def _mean(values: list) -> float:
    return math.fsum(values) / len(values)


def trend_confirmed_from_closes(closes: list) -> bool:
    """R2D2's trend test over ASCENDING closes (oldest first), most recent last. False if fewer than 220 are given.

    PURE: closes in, bool out, no store and no clock. A non-finite or non-positive close, or a bool, makes the answer
    False rather than being averaged through.
    """
    if len(closes) < TREND_MINIMUM_CLOSES:
        return False
    for close in closes[-TREND_MINIMUM_CLOSES:]:
        if type(close) is bool or type(close) not in (int, float) or not math.isfinite(close) or close <= 0.0:
            return False
    now = _mean(closes[-TREND_AVERAGE_CLOSES:])
    before = _mean(closes[-TREND_MINIMUM_CLOSES:-TREND_SLOPE_LOOKBACK_CLOSES])
    return closes[-1] > now and now / before - 1.0 >= TREND_FLATTENING_TOLERANCE


def equity_trend_confirmed(raw: SqliteStore, now_utc: datetime) -> bool:
    """``trend_confirmed`` for the equity dial, off the raw store's newest S&P reading. See the module docstring: every
    failure is False."""
    reading = raw.latest_reading(TREND_SOURCE_ID)
    if reading is None:
        return False
    payload = reading["payload"]
    if type(payload) is not dict or type(payload.get("history")) is not list:
        return False
    observed = payload.get("observation_date")
    try:
        observed_on = date.fromisoformat(observed)
    except (TypeError, ValueError):
        return False
    if observed_on < (now_utc.date() - timedelta(days=TREND_MAXIMUM_AGE_DAYS)):
        return False
    closes: list = []
    previous = ""
    for row in payload["history"]:
        if type(row) is not list or len(row) != 2 or type(row[0]) is not str or row[0] <= previous:
            return False
        previous = row[0]
        closes.append(row[1])
    if not closes or previous != observed:
        return False
    if type(payload.get("value")) not in (int, float) or not math.isclose(closes[-1], payload["value"], rel_tol=1e-9):
        return False
    return trend_confirmed_from_closes(closes)
