"""WO-1.3b-II: R2D2's calibration verdict, applied to the live decision engine.

Evidence source: fabric ``r2d2:wo:cerberus_wo13b2:verdict`` and her report
``/srv/r2d2/evidence/cerberus_wo13b2/REPORT.md`` (harness ``/srv/r2d2/tools/cerberus_replay/harness``). The items:

1. ``volatility_master`` stress 0.85 -> 0.70 (per-master thresholds threaded through the state machine).
2. The post-ALARM lock, with the S&P trend that releases it.
3. ``breadth_rsp_spy`` and ``credit_stress_hyg_lqd`` excluded from scoring (missing, never 0).
4. Count v2 (fast market-priced inputs, k = 2).
5. ``curve_master`` warning stays 0.60.
6. ``B_mid`` / ``B_high`` documented unset.
7. ``acute_rising`` deadband 0.02 (lookback unchanged).

**THE STRONGEST TEST IN THIS FILE IS THE PARITY ONE.** ``test_the_real_resolver_agrees_with_r2d2s_measured_state_machine``
walks random master-score sequences through the REAL resolver and history store and through
``_r2d2_run_machine``, a line-for-line transcription of ``candidate`` and ``run_machine`` from her
``engine_run.py`` (the harness whose output her numbers came from), and requires the SAME official state on every day.
That is what "match her harness semantics" means, measured.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from crash_detector.dials.scores import EQUITY_DIAL_ID, MONETARY_DIAL_ID
from crash_detector.engine import statistics as engine_statistics
from crash_detector.engine.statistics import (
    COUNT_INDICATOR_IDS,
    COUNT_THRESHOLD,
    EQUITY_CRASH_MASTERS,
    MONETARY_DEBASEMENT_MASTERS,
    PROVISIONAL_COUNT_K,
    PROVISIONAL_EXIT,
    PROVISIONAL_STRESS,
    PROVISIONAL_WARNING,
    VOLATILITY_MASTER_STRESS,
    Acute,
    Count,
    MasterScore,
    State,
    candidate_state_for_one_reading,
    count_for_one_dial,
    equity_crash_acute,
)
from evaluator.history_store import MachineStateHistoryStore
from evaluator.resolve import official_state_for_dial
from evaluator.trend import (
    TREND_MINIMUM_CLOSES,
    equity_trend_confirmed,
    trend_confirmed_from_closes,
)
from ingestion.store import SqliteStore
from ingestion.wiring import EXCLUDED_FROM_SCORING, build_wiring, observations_from_store

from test_engine_masters import contributions_of
from test_wiring import CALM, NOW, _derived_components, _put, _seed

ROOT = Path(__file__).resolve().parents[1]
WALK_START = datetime(2026, 1, 5, 21, 0, tzinfo=timezone.utc)


# ===================================================================================== helpers


def _vol_acute(score: float, *, dial: str = EQUITY_DIAL_ID) -> Acute:
    """ONE alarm-eligible master carrying the volatility master's REAL thresholds (warn 0.6 / stress 0.70 / exit 0.5)."""
    master = MasterScore(
        master_id="volatility_master", dial_id=dial, score=score,
        warning_threshold=PROVISIONAL_WARNING, stress_threshold=VOLATILITY_MASTER_STRESS,
        exit_threshold=PROVISIONAL_EXIT, alarm_eligible=True)
    return Acute(dial_id=dial, score=score, from_master_id="volatility_master", masters=(master,))


def _count0() -> Count:
    return Count(at_or_beyond=(), considered=("vix_level",))


def _walk(scores, trends, *, lock: bool, store: MachineStateHistoryStore):
    """Run the REAL resolver over a sequence, asking the REAL store whether the lock is armed. Returns the official states."""
    states = []
    for position, (score, trend) in enumerate(zip(scores, trends)):
        as_of = WALK_START + timedelta(days=position)
        if score is None:
            from crash_detector.engine.statistics import AcuteUnknown
            acute = AcuteUnknown(dial_id=EQUITY_DIAL_ID, unknown_master_ids=("volatility_master",),
                                 missing_component_ids=("vix_level",))
            breadth = 0.2
        else:
            acute, breadth = _vol_acute(score), 0.2
        history = store.recent(EQUITY_DIAL_ID, limit=20)
        armed = store.alarm_lock_armed(EQUITY_DIAL_ID) if lock else False
        row = official_state_for_dial(history=history, as_of=as_of, breadth=breadth, acute=acute,
                                      count=_count0(), trend_confirmed=trend, alarm_lock_armed=armed)
        store.append(row, written_utc=as_of)
        states.append(row.machine_state)
    return states


@pytest.fixture
def store(tmp_path):
    with MachineStateHistoryStore(str(tmp_path / "machine-state.sqlite")) as s:
        yield s


# ========================================= R2D2's state machine, transcribed (the parity oracle)


def _r2d2_candidate(score, trend, *, warn=0.6, stress=0.70, exit_=0.5):
    """``engine_run.candidate`` with one eligible master 'vol', b_mid = b_high = 9 (breadth gates off), no count."""
    if score is None:
        return "UNKNOWN"
    if score >= stress:
        return "ALARM"
    if score >= warn:
        return "WATCH"
    if score <= exit_ and trend:
        return "RECOVERY"
    return "CALM"


def _r2d2_armed_span(hist):
    for i, h in enumerate(hist):
        if h["state"] == "RECOVERY":
            return i
    return len(hist)


def _r2d2_run_machine(scores, trends, *, lock: bool, persistence=5):
    """``engine_run.run_machine`` (engine_run.py @ 2026-10-22), single window, only what a one-master walk exercises."""
    out, hist = [], []
    for score, trend in zip(scores, trends):
        cand = _r2d2_candidate(score, trend)
        prev = hist[0] if hist else None
        armed = lock and any(h["state"] == "ALARM" for h in hist[: _r2d2_armed_span(hist)])
        # DELIBERATE DEVIATION FROM HER HARNESS (R2D2 PR #14 live re-audit, D2): the lock does not override the
        # UNKNOWN-exit floor, so a previous UNKNOWN row makes `armed` irrelevant to the RECOVERY gate.
        armed_for_gate = armed and not (prev is not None and prev["state"] == "UNKNOWN")
        if cand == "RECOVERY" and not armed_for_gate and (prev is None or prev["state"] != "ALARM"):
            cand = "CALM"
        if lock and armed and cand == "CALM":
            cand = "WATCH"
        if prev is not None and cand == "CALM" and prev["state"] in ("ALARM", "UNKNOWN"):
            cand = "WATCH"
        if cand == "UNKNOWN":
            off, ctr = "UNKNOWN", 0
        elif prev is None:
            off, ctr = cand, 0
        elif prev["state"] == "RECOVERY" and cand == "ALARM":
            off, ctr = "ALARM", 0
        elif prev["state"] == "UNKNOWN":
            off, ctr = cand, 0
        elif cand == prev["state"]:
            off, ctr = cand, 0
        else:
            acc = prev["counter"] if prev["cand"] == cand else 0
            ctr = acc + 1
            if ctr >= persistence:
                off, ctr = cand, 0
            else:
                off = prev["state"]
        hist.insert(0, dict(state=off, cand=cand, counter=ctr))
        out.append(off)
    return out


def _random_sequence(seed: int, length: int = 400):
    """Master-score regimes with calm stretches, spikes, slow decays, outages (None) and trend flips - the shapes a
    decline and its aftermath have - so every branch of the machine is walked many times."""
    rng = random.Random(seed)
    scores, trends = [], []
    level, trend = 0.3, False
    while len(scores) < length:
        regime = rng.choice(["calm", "spike", "decay", "outage", "choppy"])
        run = rng.randint(3, 25)
        for _ in range(run):
            if regime == "calm":
                level = rng.uniform(0.05, 0.5)
            elif regime == "spike":
                level = rng.uniform(0.6, 0.95)
            elif regime == "decay":
                level = max(0.0, level - rng.uniform(0.0, 0.08))
            elif regime == "choppy":
                level = min(1.0, max(0.0, level + rng.uniform(-0.2, 0.2)))
            if rng.random() < 0.05:
                trend = not trend
            scores.append(None if regime == "outage" else round(level, 4))
            trends.append(trend)
    return scores[:length], trends[:length]


@pytest.mark.parametrize("lock", [True, False])
@pytest.mark.parametrize("seed", range(40))
def test_the_real_resolver_agrees_with_r2d2s_measured_state_machine(tmp_path, seed, lock):
    scores, trends = _random_sequence(seed)
    with MachineStateHistoryStore(str(tmp_path / "walk.sqlite")) as real_store:
        real = [state.name for state in _walk(scores, trends, lock=lock, store=real_store)]
    assert real == _r2d2_run_machine(scores, trends, lock=lock)


def test_the_parity_sequences_actually_exercise_the_lock(tmp_path):
    """A parity test over sequences that never arm the lock proves nothing: show the walks reach RECOVERY, hold WATCH,
    and differ between locked and unlocked."""
    reached_recovery = held_watch = differ = 0
    for seed in range(40):
        scores, trends = _random_sequence(seed)
        locked = _r2d2_run_machine(scores, trends, lock=True)
        unlocked = _r2d2_run_machine(scores, trends, lock=False)
        reached_recovery += "RECOVERY" in locked
        differ += locked != unlocked
        held_watch += any(b == "CALM" and a == "WATCH" for a, b in zip(locked, unlocked))
    assert reached_recovery >= 10 and differ >= 20 and held_watch >= 20


# ====================================================================== item 2: the lock itself


def _regime(n_alarm=1, n_calm=30):
    return [0.9] * n_alarm + [0.3] * n_calm


def test_without_the_lock_alarm_walks_through_watch_to_calm_on_two_persistence_counts(store):
    """THE BACK DOOR, reproduced: the deployed behaviour R2D2 measured (F1). No trend ever confirms in this walk."""
    scores = _regime()
    states = _walk(scores, [False] * len(scores), lock=False, store=store)
    assert states[0] is State.ALARM
    assert State.WATCH in states and states[-1] is State.CALM


def test_with_the_lock_alarm_cannot_reach_calm_without_recovery(store):
    """The same walk with the lock armed: the dial holds WATCH for ever while the trend does not confirm."""
    scores = _regime(n_calm=200)
    states = _walk(scores, [False] * len(scores), lock=True, store=store)
    assert states[0] is State.ALARM and State.CALM not in states
    assert states[-1] is State.WATCH


def test_the_lock_releases_through_recovery_and_then_calm_is_reachable(store):
    """ALARM -> WATCH -> (masters under exit AND the trend confirms, five readings) RECOVERY -> CALM."""
    scores = [0.9] + [0.3] * 40
    trends = [False] * 20 + [True] * 21
    states = _walk(scores, trends, lock=True, store=store)
    assert State.RECOVERY in states
    assert states.index(State.RECOVERY) > states.index(State.WATCH)
    assert states[-1] is State.CALM
    assert not store.alarm_lock_armed(EQUITY_DIAL_ID)


def test_a_relapse_out_of_recovery_is_immediate_and_rearms_the_lock(store):
    """The second-leg rule composes with the lock: ALARM re-fires out of RECOVERY with no persistence wait, and CALM is
    again unreachable until another RECOVERY."""
    scores = [0.9] + [0.3] * 14 + [0.9] + [0.3] * 40
    trends = [False] * 10 + [True] * 5 + [False] * 46
    states = _walk(scores, trends, lock=True, store=store)
    assert states[14] is State.RECOVERY            # five trend-confirmed readings after the quiet began
    assert states[15] is State.ALARM               # second-leg rule: immediately
    assert store.alarm_lock_armed(EQUITY_DIAL_ID)
    assert State.CALM not in states[15:]           # the trend never confirms again, so the dial holds


def test_an_unknown_outage_in_the_middle_of_a_halt_does_not_lift_the_lock(store):
    scores = [0.9] + [0.3] * 6 + [None] * 4 + [0.3] * 40
    states = _walk(scores, [False] * len(scores), lock=True, store=store)
    assert State.UNKNOWN in states and State.CALM not in states
    assert store.alarm_lock_armed(EQUITY_DIAL_ID)


def test_leaving_unknown_with_the_lock_armed_still_reports_watch_for_that_reading_even_on_a_recovery_candidate(store):
    """D2 regression: the lock must not override the UNKNOWN-exit floor."""
    scores = [0.9, 0.3, 0.3, None, 0.3, 0.3]
    trends = [False, True, True, True, True, True]
    states = _walk(scores, trends, lock=True, store=store)
    assert states[3] is State.UNKNOWN
    assert store.alarm_lock_armed(EQUITY_DIAL_ID)
    assert states[4] is State.WATCH  # first reading out of UNKNOWN: candidate is RECOVERY, floor wins
    # The same reading directly through the resolver, armed, previous UNKNOWN.
    history = store.recent(EQUITY_DIAL_ID, limit=20)
    assert history[0].machine_state is State.WATCH
    from test_resolve_official_state import _row
    unknown_prev = _row(State.UNKNOWN, dial_id=EQUITY_DIAL_ID, as_of=WALK_START + timedelta(days=50))
    row = official_state_for_dial(history=[unknown_prev], as_of=WALK_START + timedelta(days=51), breadth=0.2,
                                  acute=_vol_acute(0.3), count=_count0(), trend_confirmed=True, alarm_lock_armed=True)
    assert row.candidate_state is State.WATCH and row.machine_state is State.WATCH


# --------------------------------------------------------------- the store's armed question


def _append_states(store, sequence, dial=EQUITY_DIAL_ID):
    from test_resolve_official_state import _row
    for position, state in enumerate(sequence):
        store.append(_row(state, dial_id=dial, as_of=WALK_START + timedelta(days=position)),
                     written_utc=WALK_START + timedelta(days=position))


@pytest.mark.parametrize("sequence,armed", [
    ((), False),
    ((State.CALM,), False),
    ((State.WATCH, State.CALM), False),
    ((State.ALARM,), True),
    ((State.ALARM, State.WATCH), True),
    ((State.ALARM, State.WATCH, State.UNKNOWN), True),
    ((State.ALARM, State.WATCH, State.RECOVERY), False),
    ((State.ALARM, State.RECOVERY, State.ALARM), True),
    ((State.ALARM, State.RECOVERY, State.WATCH), False),
    # A history that PREDATES the lock: an ALARM that resolved through the old back door to CALM is settled, not re-armed.
    ((State.ALARM, State.WATCH, State.CALM), False),
    ((State.ALARM, State.WATCH, State.CALM, State.WATCH), False),
    ((State.ALARM, State.WATCH, State.CALM, State.ALARM), True),
])
def test_the_store_arms_the_lock_when_the_latest_alarm_is_newer_than_any_calm_or_recovery(store, sequence, armed):
    _append_states(store, sequence)
    assert store.alarm_lock_armed(EQUITY_DIAL_ID) is armed


def test_the_lock_is_per_dial(store):
    _append_states(store, (State.ALARM,), dial=MONETARY_DIAL_ID)
    assert store.alarm_lock_armed(MONETARY_DIAL_ID) is True
    assert store.alarm_lock_armed(EQUITY_DIAL_ID) is False


def test_the_armed_flag_has_no_default_so_a_forgetful_caller_cannot_run_without_the_lock():
    with pytest.raises(TypeError, match="alarm_lock_armed"):
        official_state_for_dial(history=(), as_of=WALK_START, breadth=0.2, acute=_vol_acute(0.3),
                                count=_count0(), trend_confirmed=False)


# ================================================================ the trend that releases the lock


def _r2d2_trend(closes):
    """``eval_lock.trend`` transcribed: numpy-free, indexes exactly as hers (cumsum 200-day mean, 20-row slope, tol -0.0025)."""
    i = len(closes) - 1
    if i < 219:
        return False
    ma = lambda k: sum(closes[k - 199:k + 1]) / 200
    return closes[i] > ma(i) and ma(i) / ma(i - 20) - 1 >= -0.0025


@pytest.mark.parametrize("seed", range(60))
def test_the_trend_is_r2d2s_definition_over_random_walks(seed):
    rng = random.Random(seed)
    price, closes = 100.0, []
    drift = rng.uniform(-0.003, 0.003)
    for _ in range(rng.randint(200, 400)):
        price *= 1.0 + drift + rng.gauss(0, 0.01)
        closes.append(price)
    assert trend_confirmed_from_closes(closes) == _r2d2_trend(closes)


def test_the_trend_needs_220_closes_and_a_close_above_a_flattening_mean():
    rising = [100.0 + i * 0.1 for i in range(TREND_MINIMUM_CLOSES)]
    assert trend_confirmed_from_closes(rising) is True
    assert trend_confirmed_from_closes(rising[1:]) is False  # 219 closes: no trend is claimed on a short history
    below_the_mean = rising[:-1] + [50.0]
    assert trend_confirmed_from_closes(below_the_mean) is False
    # close above its mean but the mean itself fell 9% over the lookback: not flattening
    falling_mean = [200.0] * 20 + [100.0] * 199 + [101.0]
    assert trend_confirmed_from_closes(falling_mean) is False
    for bad in (float("nan"), -1.0, 0.0, True):
        assert trend_confirmed_from_closes(rising[:-1] + [bad]) is False


def _gspc_payload(closes, *, last_date="2026-10-10", value=None):
    end = datetime.fromisoformat(last_date).date()
    dates = [(end - timedelta(days=len(closes) - 1 - i)).isoformat() for i in range(len(closes))]
    return {"unit": "index", "observation_date": last_date,
            "value": closes[-1] if value is None else value, "history": [[d, c] for d, c in zip(dates, closes)]}


def _raw_with_gspc(tmp_path, payload, as_of="2026-10-10T00:00:00Z"):
    path = str(tmp_path / "raw.sqlite")
    with SqliteStore(path) as writer:
        if payload is not None:
            _put(writer, "yahoo.^GSPC", payload, as_of)
    return SqliteStore(path, read_only=True)


def test_the_live_trend_reads_the_stored_sp500_history_and_every_failure_is_false(tmp_path):
    rising = [100.0 + i * 0.1 for i in range(260)]
    now = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)

    with _raw_with_gspc(tmp_path, _gspc_payload(rising)) as raw:
        assert equity_trend_confirmed(raw, now) is True
        assert equity_trend_confirmed(raw, now + timedelta(days=30)) is False  # a dead feed confirms nothing

    cases = {
        "missing": None,
        "short": _gspc_payload(rising[:200]),
        "last date is not the reading's own": _gspc_payload(rising, value=rising[-1]) | {"observation_date": "2026-10-09"},
        "value is not the last close": _gspc_payload(rising, value=rising[-1] + 5.0),
        "no history": {"unit": "index", "observation_date": "2026-10-10", "value": 1.0},
        "history not strictly increasing": _gspc_payload(rising) | {
            "history": _gspc_payload(rising)["history"][:100] + _gspc_payload(rising)["history"][99:]},
    }
    for name, payload in cases.items():
        sub = tmp_path / name.replace(" ", "_").replace("'", "")
        sub.mkdir()
        with _raw_with_gspc(sub, payload) as raw:
            assert equity_trend_confirmed(raw, now) is False, name


# ===================================================== item 1 and 5: per-master thresholds, curve unchanged


def test_only_the_volatility_master_has_a_threshold_of_its_own():
    tables = {m.master_id: m for table in (EQUITY_CRASH_MASTERS, MONETARY_DEBASEMENT_MASTERS) for m in table}
    for master_id, master in tables.items():
        expected_stress = VOLATILITY_MASTER_STRESS if master_id == "volatility_master" else PROVISIONAL_STRESS
        assert (master.warning_threshold, master.stress_threshold, master.exit_threshold) == (
            PROVISIONAL_WARNING, expected_stress, PROVISIONAL_EXIT), master_id
    assert VOLATILITY_MASTER_STRESS == 0.70
    # leave warning/exit/persistence unchanged (item 1) and the curve warning at 0.60 (item 5)
    assert tables["curve_master"].warning_threshold == 0.60 and tables["curve_master"].alarm_eligible is False
    assert PROVISIONAL_WARNING == 0.60 and PROVISIONAL_EXIT == 0.50 and PROVISIONAL_STRESS == 0.85


def _equity_reading(**overrides):
    base = {"hy_oas": 0.2, "yield_curve_10y3m": 0.2, "yield_curve_10y2y": 0.2, "vix_level": 0.2,
            "vix_term_structure": 0.2, "chicago_fed_nfci": 0.2}
    return contributions_of(base | overrides)


def test_a_vix_at_0_75_is_alarm_through_the_real_masters_table_and_watch_for_every_other_master():
    vol = equity_crash_acute(_equity_reading(vix_level=0.75))
    assert candidate_state_for_one_reading(0.2, vol, count_for_one_dial(_equity_reading(vix_level=0.75)),
                                           None, False) is State.ALARM
    # the same 0.75 on the credit master (stress 0.85, unchanged) is a WATCH and no more
    credit = equity_crash_acute(_equity_reading(hy_oas=0.75))
    assert candidate_state_for_one_reading(0.2, credit, count_for_one_dial(_equity_reading(hy_oas=0.75)),
                                           None, False) is State.WATCH
    # the volatility master still WATCHes at 0.60 (warning unchanged) and is calm under it
    at_warning = equity_crash_acute(_equity_reading(vix_level=0.60))
    assert candidate_state_for_one_reading(0.2, at_warning, Count(at_or_beyond=(), considered=()),
                                           None, False) is State.WATCH
    below = equity_crash_acute(_equity_reading(vix_level=0.59))
    assert candidate_state_for_one_reading(0.2, below, Count(at_or_beyond=(), considered=()),
                                           None, False) is State.CALM


def test_the_curve_master_is_still_watch_only_at_0_60_and_a_curve_at_0_95_does_not_alarm():
    reading = _equity_reading(yield_curve_10y3m=0.60)
    assert candidate_state_for_one_reading(0.2, equity_crash_acute(reading), Count((), ()), None, False) is State.WATCH
    reading = _equity_reading(yield_curve_10y3m=0.95)
    assert candidate_state_for_one_reading(0.2, equity_crash_acute(reading), Count((), ()), None, False) is State.WATCH


# ================================================================================ item 4: count v2


R2D2_FAST2 = {"yield_curve_10y3m", "yield_curve_10y2y", "hy_oas", "ig_oas", "copper_gold", "cboe_skew", "vix_level",
              "vix_term_structure", "spx_vs_200dma", "real_rate_10y_tips"}  # eval_count.FAST2, verbatim


def test_count_set_is_r2d2s_fast_set_minus_the_curve_pair_at_0_8_and_excludes_the_two_defective_ratios():
    assert set(COUNT_INDICATOR_IDS) == R2D2_FAST2 - {"yield_curve_10y3m", "yield_curve_10y2y"}
    assert not set(COUNT_INDICATOR_IDS) & set(EXCLUDED_FROM_SCORING)
    assert COUNT_THRESHOLD == 0.8
    assert PROVISIONAL_COUNT_K is None  # D3: rule 3 removed, provisionally


def test_count_v2_ignores_the_slow_indicators_that_saturated_v1_and_counts_threshold_inclusively():
    saturated_slow = {"michigan_sentiment": 1.0, "real_rate_10y_tips": 1.0, "shiller_cape": 1.0,
                      "chicago_fed_nfci": 1.0, "buffett_indicator": 1.0, "sloos_bank_lending": 1.0}
    count = count_for_one_dial(contributions_of(saturated_slow | {"vix_level": 0.8, "hy_oas": 0.79}))
    assert count.at_or_beyond == ("real_rate_10y_tips", "vix_level")
    assert "michigan_sentiment" not in count.considered and "chicago_fed_nfci" not in count.considered
    assert count.considered == ("hy_oas", "real_rate_10y_tips", "vix_level")


def test_two_fast_indicators_at_their_band_no_longer_alarm_on_count_alone():
    """D3 regression: this reading fired ALARM on count alone under k=2. Rule 3 is removed, so it must not."""
    two = _equity_reading(vix_level=0.8, hy_oas=0.8)
    count = count_for_one_dial(two)
    assert count.count >= 2  # the count is still computed and published
    # Masters held quiet (the two readings also drive volatility_master; this isolates the COUNT rule).
    assert candidate_state_for_one_reading(0.2, _vol_acute(0.3), count, None, False) is State.CALM


def test_a_huge_count_alone_cannot_alarm_a_dial_whose_masters_are_calm():
    big = Count(at_or_beyond=tuple(sorted(COUNT_INDICATOR_IDS)), considered=tuple(sorted(COUNT_INDICATOR_IDS)))
    assert big.count == len(COUNT_INDICATOR_IDS)
    assert candidate_state_for_one_reading(0.2, _vol_acute(0.3), big, None, False) is State.CALM


def test_rule_2_still_alarms_so_alarm_is_not_lost():
    assert candidate_state_for_one_reading(0.2, _vol_acute(0.70), _count0(), None, False) is State.ALARM


def test_a_watch_only_masters_components_are_not_countable_so_cannot_push_count_past_any_k():
    """D1 regression: curve_master is alarm_eligible=False; its components must not be in the count at all."""
    watch_only = {m.master_id: m for m in EQUITY_CRASH_MASTERS}
    assert watch_only["curve_master"].alarm_eligible is False
    curve = {"yield_curve_10y3m", "yield_curve_10y2y"}
    assert not curve & set(COUNT_INDICATOR_IDS)
    count = count_for_one_dial(contributions_of({"yield_curve_10y3m": 1.0, "yield_curve_10y2y": 1.0, "vix_level": 0.9}))
    assert count.count == 1 and not curve & set(count.considered) and not curve & set(count.at_or_beyond)
    for master in EQUITY_CRASH_MASTERS + MONETARY_DEBASEMENT_MASTERS:
        if not master.alarm_eligible:
            assert not set(master.component_ids) & set(COUNT_INDICATOR_IDS), master.master_id


def test_the_monetary_dials_count_can_never_reach_k():
    """Disclosed: of the monetary dial's indicators only real_rate_10y_tips is in R2D2's measured set."""
    reading = contributions_of({"monetisation_flag": 1.0, "real_rate_10y_tips": 1.0, "broad_dollar": 1.0})
    assert count_for_one_dial(reading).count == 1


# ========================================================== item 6: B_mid / B_high unset and documented


def test_b_mid_and_b_high_are_unset_not_fabricated():
    assert engine_statistics.PROVISIONAL_BREADTH_MID is None and engine_statistics.PROVISIONAL_BREADTH_HIGH is None


def test_decision_rule_section_10_documents_the_unset_thresholds_and_the_mapping_says_so():
    text = (ROOT / "DECISION-RULE.md").read_text(encoding="utf-8")
    section_10 = text[text.index("## 10. Provisional parameters"):text.index("## 11.")]
    mid = next(line for line in section_10.splitlines() if line.startswith("| B_mid"))
    high = next(line for line in section_10.splitlines() if line.startswith("| B_high"))
    assert "unset" in mid and "never a gating threshold" in mid
    assert "unset" in high and "rule 3 is dead" in high
    assert "r2d2:wo:cerberus_wo13b2:verdict" in text  # the evidence source is cited
    mapping = (ROOT / "governance" / "mapping" / "indicator_mapping.yaml").read_text(encoding="utf-8")
    assert "B_mid and B_high are NOT mapping parameters and are UNSET" in mapping
    assert "r2d2:wo:cerberus_wo13b2:verdict" in mapping


# ============================================================ item 3: the two broken inputs are missing


def test_the_two_broken_inputs_are_pending_by_name_with_their_reason_and_are_in_neither_dials_model():
    wiring = build_wiring()
    assert set(EXCLUDED_FROM_SCORING) == {"breadth_rsp_spy", "credit_stress_hyg_lqd"}
    for indicator in EXCLUDED_FROM_SCORING:
        assert indicator in wiring.pending and indicator not in wiring.live_ids
        assert wiring.pending[indicator].startswith("EXCLUDED (WO-1.3b-II)")
        for dial in ("equity_crash", "monetary_debasement"):
            spec = wiring.snapshot.spec_for(dial)
            assert indicator not in spec.required_input_ids + spec.contributing_input_ids


def test_stored_readings_of_the_excluded_inputs_feed_neither_breadth_nor_count_nor_any_master(tmp_path):
    """The feeds are still COLLECTED (the data stays for the re-spec). Seed the RSP/SPY and HYG/LQD components at values
    that would score 1.0 and show they change nothing: not an observation, not a contribution, not a count."""
    wiring = build_wiring()
    path = str(tmp_path / "raw.sqlite")
    with SqliteStore(path) as writer:
        _seed(writer, wiring, CALM)
        day = "2026-10-10"
        for indicator, figure in (("breadth_rsp_spy", 0.20), ("credit_stress_hyg_lqd", 0.50)):
            parts = wiring.derived_for.get(indicator)
            assert parts is None  # not wired, so the test builds the components from the catalog directly
        from ingestion.catalog import INGREDIENTS
        for source_id, value in (("yahoo.RSP", 20.0), ("yahoo.SPY", 100.0), ("yahoo.HYG", 50.0), ("yahoo.LQD", 100.0)):
            ing = next(i for i in INGREDIENTS if i.source_id == source_id)
            _put(writer, source_id, {"unit": ing.unit, "observation_date": day, "value": value}, day + "T00:00:00Z")
    with SqliteStore(path, read_only=True) as raw:
        ids = {o.source_id for o in observations_from_store(raw, wiring, NOW)}
    assert not ids & set(EXCLUDED_FROM_SCORING)
    # and what is left is the same set that is live, with nothing of the excluded pair in it
    assert ids <= wiring.live_ids


# --- item 8: HY/IG OAS request window widened to the FRED floor ------------------------- #
def _oas_serves(column, dates):
    body = "\n".join([f"observation_date,{column}"] + [f"{d},1.5" for d in dates]) + "\n"

    def getter(url, timeout_seconds, headers=None):
        return body

    return getter


def test_oas_rows_take_dates_from_the_fred_floor_not_just_the_apr_2025_window():
    from tools.backfill.wo117_run import EPISODES, OAS_FRED_FLOOR, row_dates
    from ingestion.catalog import INGREDIENTS

    assert OAS_FRED_FLOOR == "2023-10-23"
    ing = next(i for i in INGREDIENTS if i.source_id == "fred.BAMLH0A0HYM2")
    published = ["2023-10-20", "2023-10-23", "2024-06-03", "2024-12-30", "2024-12-31", "2025-03-03"]
    dates, _ = row_dates(ing, EPISODES, getter=_oas_serves("BAMLH0A0HYM2", published))
    assert dates == ("2023-10-23", "2024-06-03", "2024-12-30", "2024-12-31", "2025-03-03")


def test_ig_oas_is_widened_too_and_other_rows_are_not():
    from tools.backfill.wo117_run import EPISODES, row_dates
    from ingestion.catalog import INGREDIENTS

    published = ["2023-10-23", "2024-06-03", "2025-03-03"]
    ig = next(i for i in INGREDIENTS if i.source_id == "fred.BAMLC0A0CM")
    assert row_dates(ig, EPISODES, getter=_oas_serves("BAMLC0A0CM", published))[0] == tuple(published)
    dff = next(i for i in INGREDIENTS if i.source_id == "fred.DFF")
    assert row_dates(dff, EPISODES, getter=_oas_serves("DFF", published))[0] == ("2025-03-03",)


def test_oas_widening_needs_the_apr_2025_episode_selected():
    from tools.backfill.wo117_run import EPISODES, row_dates
    from ingestion.catalog import INGREDIENTS

    ing = next(i for i in INGREDIENTS if i.source_id == "fred.BAMLH0A0HYM2")
    others = tuple(e for e in EPISODES if e.key != "apr-2025")
    assert row_dates(ing, others, getter=_oas_serves("BAMLH0A0HYM2", ["2023-10-23", "2024-06-03"]))[0] == ()
