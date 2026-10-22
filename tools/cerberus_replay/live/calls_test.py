"""Rogue's four interpretation calls, tested against the PR's LIVE code (not his prose).  Pinned SHA 5864e47."""
import sys, os, random, itertools, datetime as dt, json, collections
REPO = os.path.join(os.environ["R2_SCRATCH"], "repo_pr14", "crash-detector")
sys.path[:0] = [os.path.join(REPO, "src"), REPO]
from crash_detector.engine import statistics as S
from crash_detector.engine.statistics import State
from crash_detector.dials.scores import Contribution
from evaluator.history_store import MachineStateHistoryStore, MachineStateRow
from evaluator import resolve as R
EQ, MO = "equity_crash", "monetary_debasement"

print("=== CALL 1: breadth unset -> rising-WATCH limb off ===")
print("B_mid, B_high:", S.PROVISIONAL_BREADTH_MID, S.PROVISIONAL_BREADTH_HIGH)
def acute(dial, scores, elig=True):
    ms = tuple(S.MasterScore(master_id=f"m{i}", dial_id=dial, score=s, warning_threshold=.6, stress_threshold=.85,
                             exit_threshold=.5, alarm_eligible=elig) for i, s in enumerate(scores))
    return S.Acute(dial_id=dial, score=max(scores), from_master_id="m0", masters=ms)
cnt0 = S.Count(at_or_beyond=(), considered=("vix_level",))
for here, back in [(0.9, 0.1), (0.5, 0.0), (0.489, 0.3), (1.0, 0.0)]:
    c = S.candidate_state_for_one_reading(breadth=here, acute=acute(EQ, [.1, .1]), count=cnt0, breadth_20_rows_ago=back, trend_confirmed=False)
    print(f"  breadth {here} vs 20-ago {back}, masters calm -> {c}")
# and an actual warning still works
print("  master 0.65 ->", S.candidate_state_for_one_reading(breadth=.2, acute=acute(EQ, [.65, .1]), count=cnt0, breadth_20_rows_ago=None, trend_confirmed=False))

print("\n=== CALL 4: monetary count can never reach k ===")
import yaml
sc = json.load(open(os.path.join(REPO, "deploy/indicator-scaling.json")))
for dial in (EQ, MO):
    ids = set(sc[dial]) - {"$comment"}
    inter = sorted(ids & set(S.COUNT_INDICATOR_IDS))
    print(f"  {dial}: scaled indicators {len(ids)}, in COUNT_INDICATOR_IDS: {inter}")
def contribs(ids, v=1.0):
    return tuple(Contribution(source_id=i, category="x", weight=1.0, contribution=v) for i in sorted(ids))
for dial in (EQ, MO):
    ids = set(sc[dial]) - {"$comment"}
    c = S.count_for_one_dial(contribs(ids, 1.0))
    print(f"  {dial}: EVERY indicator pinned at 1.0 -> count={c.count} considered={c.considered}")
print("  K =", S.PROVISIONAL_COUNT_K)

print("\n=== curve pair through the count (curve_master is alarm_eligible=False) ===")
cm = [m for m in S.EQUITY_CRASH_MASTERS if m.master_id == "curve_master"][0]
print("  curve_master alarm_eligible:", cm.alarm_eligible)
base = {i: 0.0 for i in set(sc[EQ]) - {"$comment"}}
base.update({"yield_curve_10y3m": 0.8, "yield_curve_10y2y": 0.8})
c = S.count_for_one_dial(contribs([], 0.0) + tuple(Contribution(source_id=k, category="x", weight=1.0, contribution=v) for k, v in base.items()))
print("  only both curve indicators at 0.80 -> count", c.count, c.at_or_beyond)
ac = S.Acute(dial_id=EQ, score=0.8, from_master_id="curve_master", masters=(
    S.MasterScore(master_id="curve_master", dial_id=EQ, score=0.8, warning_threshold=.6, stress_threshold=.85, exit_threshold=.5, alarm_eligible=False),
    S.MasterScore(master_id="volatility_master", dial_id=EQ, score=0.1, warning_threshold=.6, stress_threshold=.70, exit_threshold=.5, alarm_eligible=True)))
print("  candidate state with curve_master 0.80, vol 0.10, count 2 ->",
      S.candidate_state_for_one_reading(breadth=.3, acute=ac, count=c, breadth_20_rows_ago=None, trend_confirmed=False))

print("\n=== CALL 3: armed semantics -- SQL alarm_lock_armed vs the harness rule (eval_lock.py/_armed_span) ===")
def mk(state, i):
    t = dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(days=i)
    if state is State.UNKNOWN:
        return MachineStateRow(dial_id=EQ, as_of=t, machine_state=state, candidate_state=State.UNKNOWN, persistence_counter=0)
    return MachineStateRow(dial_id=EQ, as_of=t, machine_state=state, candidate_state=state, persistence_counter=0, acute_rising=False,
                           breadth=.3, acute=.3, acute_from_master_id="m", master_scores={"m": .3}, indicator_count=0, count_at_or_beyond=())
def mine(seq):  # oldest-first list of states; harness rule: an ALARM since the most recent RECOVERY
    last_rec = max([i for i, s in enumerate(seq) if s is State.RECOVERY], default=-1)
    return any(s is State.ALARM for s in seq[last_rec + 1:])
ALPH = [State.CALM, State.WATCH, State.ALARM, State.RECOVERY, State.UNKNOWN]
def real(seq):
    h = MachineStateHistoryStore(":memory:")
    for i, s in enumerate(seq):
        h.append(mk(s, i), written_utc=dt.datetime.now(dt.timezone.utc))
    r = h.alarm_lock_armed(EQ); h.close(); return r
diff = []; n = 0
for L in range(1, 6):
    for seq in itertools.product(ALPH, repeat=L):
        n += 1
        if real(seq) != mine(list(seq)):
            diff.append(seq)
print(f"  exhaustive over all histories up to length 5: {n} sequences, {len(diff)} disagree")
def has_calm_after_alarm_without_recovery(seq):
    seen_alarm = False
    for s in seq:
        if s is State.ALARM: seen_alarm = True
        elif s is State.RECOVERY: seen_alarm = False
        elif s is State.CALM and seen_alarm: return True
    return False
print("  every disagreement is a CALM row following an ALARM with no RECOVERY between:", all(has_calm_after_alarm_without_recovery(d) for d in diff))
print("  example:", [[s.name for s in d] for d in diff[:3]])

print("\n  --- is that disagreement reachable under the lock?  property test driving the REAL resolver + REAL lock query ---")
random.seed(20261022)
viol = collections.Counter(); steps = 0; reached_recovery = 0; dis_reach = 0
for trial in range(400):
    h = MachineStateHistoryStore(":memory:")
    hist_states = []
    for i in range(300):
        regime = random.random()
        # random master score path with persistence-ish autocorrelation
        base = (trial % 7) / 7.0
        sc_ = min(1.0, max(0.0, random.gauss(0.45 + 0.45 * (1 if (i // 40) % 3 == 1 else 0) * base + (0.2 if (i // 40) % 3 == 2 else 0), 0.25)))
        cnt = S.Count(at_or_beyond=("a", "b") if random.random() < 0.03 else (), considered=("a", "b", "c"))
        tr = random.random() < (0.5 if (i // 40) % 3 == 0 else 0.15)
        ac = acute(EQ, [sc_, random.random() * 0.4])
        hist = h.recent(EQ, limit=20)
        armed = h.alarm_lock_armed(EQ)
        row = R.official_state_for_dial(history=hist, as_of=dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(days=i),
                                        breadth=.3, acute=ac, count=cnt, trend_confirmed=tr, alarm_lock_armed=armed)
        steps += 1
        # I1: never an official CALM while armed
        if armed and row.machine_state is State.CALM: viol["CALM while armed"] += 1
        # I2: an official CALM never follows an ALARM without a RECOVERY between
        h.append(row, written_utc=dt.datetime.now(dt.timezone.utc))
        hist_states.append(row.machine_state)
        if row.machine_state is State.RECOVERY: reached_recovery += 1
        if real(tuple(hist_states[-5:])) != mine(hist_states[-5:]) and False: pass
    if has_calm_after_alarm_without_recovery(hist_states): viol["CALM after ALARM without RECOVERY"] += 1
    if real(tuple(hist_states)) != mine(hist_states): dis_reach += 1
    h.close()
print(f"  {steps} resolver steps over 400 random histories: violations {dict(viol)}; RECOVERY rows reached {reached_recovery}; "
      f"histories where SQL lock != harness rule at the end: {dis_reach}")

print("\n=== CALL 2: equity-only scope -- what the monetary dial can still do (lock off, trend off) ===")
h = MachineStateHistoryStore(":memory:"); seq = []
cm0 = S.Count(at_or_beyond=(), considered=("real_rate_10y_tips",))
path = [0.9] * 6 + [0.2] * 14   # real_rate_master stress then quiet
for i, s_ in enumerate(path):
    ac = S.Acute(dial_id=MO, score=s_, from_master_id="real_rate_master", masters=(
        S.MasterScore(master_id="real_rate_master", dial_id=MO, score=s_, warning_threshold=.6, stress_threshold=.85, exit_threshold=.5, alarm_eligible=True),))
    row = R.official_state_for_dial(history=h.recent(MO, limit=20), as_of=dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(days=i),
                                    breadth=.3, acute=ac, count=cm0, trend_confirmed=False, alarm_lock_armed=False)
    h.append(row, written_utc=dt.datetime.now(dt.timezone.utc)); seq.append(row.machine_state.name)
print("  monetary: 6 days stress then quiet ->", " ".join(f"{k}x{len(list(g))}" for k, g in itertools.groupby(seq)))
print("  (ALARM -> WATCH -> CALM with no RECOVERY and no trend: the back door is still open on the monetary dial)")
