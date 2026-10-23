"""f290583: D1 (curve pair cannot carry ALARM), D3 (count never gates), via the REAL count_for_one_dial / candidate_state_for_one_reading
/ official_state_for_dial.  Fuzz is over the real masters' thresholds (equity), random scores, random count ids."""
import sys, os, random, itertools, datetime as dt
REPO = os.path.join(os.environ["R2_SCRATCH"], "repo_pr14b", "crash-detector")
sys.path[:0] = [os.path.join(REPO, "src"), REPO]
from crash_detector.engine import statistics as S
from crash_detector.engine.statistics import State
from crash_detector.dials.scores import Contribution
from evaluator.history_store import MachineStateHistoryStore
from evaluator import resolve as R
EQ = "equity_crash"
print("PROVISIONAL_COUNT_K =", S.PROVISIONAL_COUNT_K, "| COUNT_INDICATOR_IDS =", S.COUNT_INDICATOR_IDS)
assert not any(i.startswith("yield_curve") for i in S.COUNT_INDICATOR_IDS)
M = {m.master_id: m for m in S.EQUITY_CRASH_MASTERS}
print("equity masters:", {k: (v.alarm_eligible, v.warning_threshold, v.stress_threshold) for k, v in M.items()})
def ms(scores):
    return tuple(S.MasterScore(master_id=k, dial_id=EQ, score=v, warning_threshold=M[k].warning_threshold, stress_threshold=M[k].stress_threshold,
                               exit_threshold=M[k].exit_threshold, alarm_eligible=M[k].alarm_eligible) for k, v in scores.items())
def acute_of(scores):
    m = ms(scores); top = max(m, key=lambda x: x.score)
    return S.Acute(dial_id=EQ, score=top.score, from_master_id=top.master_id, masters=m)
def contribs(d): return tuple(Contribution(source_id=k, category="x", weight=1.0, contribution=v) for k, v in sorted(d.items()))

# D1 scenario: both curves pinned at 1.0, every other input calm, via the real count
cnt = S.count_for_one_dial(contribs({"yield_curve_10y2y": 1.0, "yield_curve_10y3m": 1.0, "vix_level": 0.0}))
cand = S.candidate_state_for_one_reading(breadth=.3, acute=acute_of({"curve_master": 1.0, "volatility_master": .1, "credit_master": .1, "financial_conditions_master": .1}),
                                         count=cnt, breadth_20_rows_ago=.3, trend_confirmed=False)
print(f"D1 scenario: curves=1.0, rest calm -> count {cnt.count} {cnt.at_or_beyond} -> candidate {cand.name}")
assert cnt.count == 0 and cand is State.WATCH

# D3 scenario: TIPS + SKEW + spx_vs_200dma + vix all pinned at 1.0, all masters calm -> count high, candidate must not be ALARM
cnt = S.count_for_one_dial(contribs({k: 1.0 for k in S.COUNT_INDICATOR_IDS}))
cand = S.candidate_state_for_one_reading(breadth=.3, acute=acute_of({"curve_master": .1, "volatility_master": .1, "credit_master": .1, "financial_conditions_master": .1}),
                                         count=cnt, breadth_20_rows_ago=.3, trend_confirmed=False)
print(f"D3 scenario: all {len(S.COUNT_INDICATOR_IDS)} count ids =1.0, masters calm -> count {cnt.count} -> candidate {cand.name}")
assert cnt.count == len(S.COUNT_INDICATOR_IDS) and cand is not State.ALARM

# fuzz: candidate ALARM <=> some alarm-eligible master >= its own stress; count/breadth/trend irrelevant
rng = random.Random(20261023); n = 0; alarm = 0
for _ in range(300000):
    sc = {k: rng.choice([rng.random(), 1.0, 0.0, M[k].stress_threshold, M[k].warning_threshold]) for k in M}
    k_ids = rng.sample(S.COUNT_INDICATOR_IDS, rng.randint(0, len(S.COUNT_INDICATOR_IDS)))
    c = S.Count(at_or_beyond=tuple(sorted(k_ids)), considered=S.COUNT_INDICATOR_IDS) if True else None
    try: c = S.Count(at_or_beyond=tuple(sorted(k_ids)), considered=tuple(S.COUNT_INDICATOR_IDS))
    except Exception: c = cnt
    a = S.candidate_state_for_one_reading(breadth=rng.random(), acute=acute_of(sc), count=c, breadth_20_rows_ago=rng.choice([None, rng.random()]), trend_confirmed=rng.random() < .5)
    want = any(M[k].alarm_eligible and sc[k] >= M[k].stress_threshold for k in sc)
    assert (a is State.ALARM) == want, (sc, a)
    n += 1; alarm += want
print(f"fuzz: {n} readings, {alarm} ALARM, candidate ALARM == (eligible master >= own stress) on every one; count size 0..{len(S.COUNT_INDICATOR_IDS)} never mattered")
