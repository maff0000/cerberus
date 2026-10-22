import sys, os, json, sqlite3, datetime as dt, tempfile
SP = os.environ["R2_SCRATCH"]; REPO = os.path.join(SP, "repo_pr14", "crash-detector")
sys.path[:0] = [os.path.join(REPO, "src"), REPO]
from evaluator.pass_once import one_pass_for_both_dials
from evaluator.history_store import MachineStateHistoryStore
from evaluator.trend import equity_trend_confirmed
from ingestion.store import SqliteStore
raw = os.path.join(SP, "livecopy", "r2_live_ingestion_copy.sqlite")
now = dt.datetime.now(dt.timezone.utc)
h = MachineStateHistoryStore(os.path.join(tempfile.mkdtemp(dir=SP), "h.sqlite"))
with SqliteStore(raw, read_only=True) as rs:
    print("trend_confirmed (PR) on today's live feed:", equity_trend_confirmed(rs, now))
rows = one_pass_for_both_dials(raw_store_path=raw, history=h, now_utc=now)
for dial, r in rows.items():
    print(dial, r.machine_state.name, "cand", r.candidate_state.name, "breadth", r.breadth and round(r.breadth, 3), "acute", r.acute and round(r.acute, 3), r.acute_from_master_id,
          "masters", r.master_scores and {k: round(v, 2) for k, v in r.master_scores.items()}, "count", r.indicator_count, r.count_at_or_beyond)
print("\nlive DEPLOYED evaluator (build a56bfc2, pre-PR) last rows:")
c = sqlite3.connect(f"file:{os.path.join(SP,'livecopy','r2_live_state_copy.sqlite')}?mode=ro", uri=True)
cols = [r[1] for r in c.execute("pragma table_info(machine_state_history)")]
for dial in ("equity_crash", "monetary_debasement"):
    for r in c.execute("select as_of_utc, machine_state, candidate_state, breadth, acute, acute_from_master_id, indicator_count, count_at_or_beyond from machine_state_history where dial_id=? order by 1 desc limit 4", (dial,)):
        print("  ", dial, r)
