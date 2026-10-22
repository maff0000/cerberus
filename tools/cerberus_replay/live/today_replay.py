"""Replay the PR's real pass over the LAST WEEK of the live DEV feed (copy, read-only source): for each calendar day, the store holds
only readings ADMITTED by the end of that day; one pass per day at 21:00Z; fresh scratch history."""
import sys, os, json, sqlite3, datetime as dt, tempfile
SP = os.environ["R2_SCRATCH"]; REPO = os.path.join(SP, "repo_pr14", "crash-detector")
sys.path[:0] = [os.path.join(REPO, "src"), REPO]
from evaluator.pass_once import one_pass_for_both_dials
from evaluator.history_store import MachineStateHistoryStore
from ingestion.store import SqliteStore
src = sqlite3.connect(f"file:{SP}/livecopy/r2_live_ingestion_copy.sqlite?mode=ro", uri=True)
rows = src.execute("select source_id, source_as_of_utc, payload, admitted_utc, vintage from raw_reading order by admitted_utc").fetchall()
print("live copy readings:", len(rows), "admitted", rows[0][3], "->", rows[-1][3])
wd = tempfile.mkdtemp(dir=SP); raw = os.path.join(wd, "r.sqlite"); SqliteStore(raw).close()
w = sqlite3.connect(raw, isolation_level=None)
w.execute("INSERT INTO raw_observation (source_id,adapter_id,collector_run_id,attempt_number,requested_utc,observed_utc,outcome) VALUES ('r','r','r',1,'x','x','OK')")
h = MachineStateHistoryStore(os.path.join(wd, "h.sqlite"))
from evaluator.history_store import MachineStateRow
from crash_detector.engine.statistics import State
for k in range(25):   # a deployed dial has a history: 25 CALM rows before the first replayed day (so persistence counts as live would)
    h.append(MachineStateRow(dial_id="equity_crash", as_of=dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc) + dt.timedelta(days=k), machine_state=State.CALM, candidate_state=State.CALM, persistence_counter=0,
             acute_rising=False, breadth=.33, acute=.3, acute_from_master_id="curve_master", master_scores={"curve_master": .3}, indicator_count=0, count_at_or_beyond=()), written_utc=dt.datetime.now(dt.timezone.utc))
i = 0
for day in range(14, 22):
    d = dt.date(2026, 10, day)
    if d.weekday() >= 5: continue
    cut = dt.datetime(2026, 10, day, 23, 59, 59, tzinfo=dt.timezone.utc).isoformat().replace("+00:00", "Z")
    while i < len(rows) and rows[i][3] <= cut:
        sid, asof, payload, adm, vint = rows[i]
        w.execute("INSERT OR IGNORE INTO raw_reading (source_id,source_as_of_utc,payload,observation_id,admitted_utc,vintage) VALUES (?,?,?,1,?,?)", (sid, asof, payload, adm, vint)); i += 1
    now = dt.datetime(2026, 10, day, 21, 0, tzinfo=dt.timezone.utc)
    res = one_pass_for_both_dials(raw_store_path=raw, history=h, now_utc=now)
    e = res["equity_crash"]
    print(d, e.machine_state.name, "cand", e.candidate_state.name, "ctr", e.persistence_counter, "| masters", e.master_scores and {k[:6]: round(v, 2) for k, v in e.master_scores.items()}, "| count", e.indicator_count, e.count_at_or_beyond, "| armed", h.alarm_lock_armed("equity_crash"))
