import sys, os, datetime as dt
REPO = os.path.join(os.environ["R2_SCRATCH"], "repo_pr14b", "crash-detector")
sys.path[:0] = [os.path.join(REPO, "src"), REPO]
from crash_detector.engine import statistics as S
from crash_detector.engine.statistics import State
from evaluator.history_store import MachineStateHistoryStore, MachineStateRow
from evaluator import resolve as R
EQ = "equity_crash"
T0 = dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc)
def num_row(state, i, cand=None, ctr=0):
    return MachineStateRow(dial_id=EQ, as_of=T0 + dt.timedelta(days=i), machine_state=state, candidate_state=cand or state, persistence_counter=ctr,
                           acute_rising=False, breadth=.3, acute=.3, acute_from_master_id="m", master_scores={"m": .3}, indicator_count=0, count_at_or_beyond=())
def unk(i): return MachineStateRow(dial_id=EQ, as_of=T0 + dt.timedelta(days=i), machine_state=State.UNKNOWN, candidate_state=State.UNKNOWN, persistence_counter=0)
def calm_acute():
    ms = (S.MasterScore(master_id="volatility_master", dial_id=EQ, score=.1, warning_threshold=.6, stress_threshold=.70, exit_threshold=.5, alarm_eligible=True),
          S.MasterScore(master_id="curve_master", dial_id=EQ, score=.1, warning_threshold=.6, stress_threshold=.85, exit_threshold=.5, alarm_eligible=False))
    return S.Acute(dial_id=EQ, score=.1, from_master_id="volatility_master", masters=ms)
cnt0 = S.Count(at_or_beyond=(), considered=("vix_level",))
def step(h, i, trend):
    armed = h.alarm_lock_armed(EQ)
    row = R.official_state_for_dial(history=h.recent(EQ, limit=20), as_of=T0 + dt.timedelta(days=i), breadth=.3, acute=calm_acute(), count=cnt0,
                                    trend_confirmed=trend, alarm_lock_armed=armed)
    h.append(row, written_utc=dt.datetime.now(dt.timezone.utc)); return armed, row

print("Case 1: dial in ALARM (lock armed) -> data outage (UNKNOWN rows) -> FIRST resolvable reading is fully quiet and trend is confirmed")
h = MachineStateHistoryStore(":memory:")
for i, s in enumerate([State.WATCH, State.ALARM, State.ALARM]): h.append(num_row(s, i), written_utc=dt.datetime.now(dt.timezone.utc))
h.append(unk(3), written_utc=dt.datetime.now(dt.timezone.utc))
armed, row = step(h, 4, True)
print(f"   armed={armed}; first reading after outage -> official {row.machine_state.name}, candidate {row.candidate_state.name}, counter {row.persistence_counter}")
print("   (RECOVERY needs 5 consecutive RECOVERY candidates when it comes from ALARM/WATCH; here it took ONE reading)")

print("Case 2: same, but WITHOUT an outage (control): dial ALARM, quiet + trend, 5 readings needed")
h = MachineStateHistoryStore(":memory:")
for i, s in enumerate([State.WATCH, State.ALARM, State.ALARM]): h.append(num_row(s, i), written_utc=dt.datetime.now(dt.timezone.utc))
seq = []
for i in range(3, 10):
    armed, row = step(h, i, True); seq.append(f"{row.machine_state.name}({row.persistence_counter})")
print("   ", " ".join(seq))

print("Case 3: dial WATCH under lock (ALARM weeks ago) -> outage -> one quiet reading")
h = MachineStateHistoryStore(":memory:")
for i, s in enumerate([State.ALARM, State.WATCH, State.WATCH, State.WATCH]): h.append(num_row(s, i), written_utc=dt.datetime.now(dt.timezone.utc))
h.append(unk(4), written_utc=dt.datetime.now(dt.timezone.utc))
armed, row = step(h, 5, True)
print(f"   armed={armed}; first reading after outage -> official {row.machine_state.name}")
print("Case 4: pre-PR behaviour for the same outage (lock not armed) for contrast")
h = MachineStateHistoryStore(":memory:")
for i, s in enumerate([State.WATCH, State.ALARM, State.ALARM]): h.append(num_row(s, i), written_utc=dt.datetime.now(dt.timezone.utc))
h.append(unk(3), written_utc=dt.datetime.now(dt.timezone.utc))
row = R.official_state_for_dial(history=h.recent(EQ, limit=20), as_of=T0 + dt.timedelta(days=4), breadth=.3, acute=calm_acute(), count=cnt0, trend_confirmed=True, alarm_lock_armed=False)
print(f"   alarm_lock_armed=False -> official {row.machine_state.name}")
