"""R2D2 WO-1.3b-II live re-audit: drive the PR's REAL pass (evaluator.pass_once.one_pass_for_both_dials) over a
point-in-time rebuild of the WO-1.17 store, one pass per market day, one fresh history per episode window.

The code under test is unmodified (git archive of the pinned SHA).  What is mine is only the store view: before the pass
for day d, a scratch raw store holds exactly the raw_reading rows knowable at d (same availability rule as the
WO-1.3b-II harness: 'original' vintage -> payload vintage_date, else as_of + 1 day).  The pinned WO-1.17 store is opened
mode=ro and never written.
"""
from __future__ import annotations
import bisect, datetime as dt, json, os, sqlite3, sys, tempfile, time
SP = os.environ["R2_SCRATCH"]
REPO = os.environ.get("CERBERUS_REPO", os.path.join(SP, "repo_pr14", "crash-detector"))
STORE = os.environ.get("CERBERUS_STORE", os.path.join(SP, "data", "wo117.sqlite"))
sys.path[:0] = [os.path.join(REPO, "src"), REPO]

from crash_detector.dials.dialset import DIAL_IDS
from evaluator.history_store import MachineStateHistoryStore
from evaluator.pass_once import one_pass_for_both_dials
from evaluator.trend import equity_trend_confirmed
from ingestion.store import SqliteStore

D = dt.date.fromisoformat
HIST_MODE = os.environ.get("R2_HIST", "none")      # none = store as-is ; control = live-shaped S&P history (260 closes) from the control series
ACUTE_MODE = os.environ.get("R2_ACUTE", "strict")  # strict = the real pass ; available = real pass with acute over the masters that scored
EPISODES = [
    ("2000-02", "1999-11-02", "2002-12-31"), ("2007-09", "2007-04-02", "2009-12-31"),
    ("2011", "2011-03-02", "2011-12-30"), ("2015-16", "2015-06-02", "2016-03-31"),
    ("Q4-2018", "2018-08-02", "2018-12-31"), ("Mar-2020", "2019-12-03", "2020-04-30"),
    ("2022", "2021-11-02", "2022-12-30"), ("Apr-2025", "2024-12-31", "2025-05-30"),
]


def load_rows():
    c = sqlite3.connect(f"file:{STORE}?mode=ro", uri=True)
    out = []
    for sid, asof, payload, adm, vint in c.execute(
            "select source_id,source_as_of_utc,payload,admitted_utc,vintage from raw_reading"):
        p = json.loads(payload)
        a = D(asof[:10])
        av = D(p["vintage_date"]) if vint == "original" else a + dt.timedelta(days=1)
        out.append((av, sid, asof, payload, adm, vint))
    out.sort(key=lambda r: (r[0], r[1], r[2]))
    return out


def spx_days():
    c = sqlite3.connect(f"file:{STORE}?mode=ro", uri=True)
    return sorted({D(r[0][:10]) for r in c.execute("select source_as_of_utc from raw_reading where source_id='yahoo.^GSPC'")})


_CTL = None


def control_closes():
    """date -> close from the CONTROL ^GSPC series (outside the store; equals the store on all 2,514 store days)."""
    global _CTL
    if _CTL is None:
        sys.path.insert(0, os.path.join(SP, "harness"))
        import control as K
        _CTL = K.yahoo("gspc")
    return _CTL


def with_history(sid, asof, payload):
    """The S&P payload as the LIVE collector stores it: + history = last 260 closes ending on the reading's own date."""
    if HIST_MODE != "control" or sid != "yahoo.^GSPC":
        return payload
    p = json.loads(payload)
    ctl = control_closes()
    a = D(asof[:10])
    ds = sorted(d for d in ctl if d <= a)[-260:]
    hist = [[d.isoformat(), ctl[d]] for d in ds]
    if not hist or hist[-1][0] != p["observation_date"]:
        return payload
    hist[-1][1] = p["value"]                                   # the reading's own value is the last close, exactly
    p["history"] = hist
    return json.dumps(p)


def degraded_pass(dial_id, *, raw_store_path, history, now_utc):
    """REPLAY-ONLY variant of evaluator.pass_once.one_pass_for_dial: identical, except the acute statistic is the max over the
    masters that SCORED (what the real pass would do if every input existed for the masters that can be computed).  Never a
    live behaviour; labelled wherever used."""
    from datetime import datetime, timezone
    from crash_detector.dials.dialset import EQUITY_DIAL_ID
    from crash_detector.engine.evaluate import evaluate
    from crash_detector.engine import statistics as S
    from crash_detector.serving.dial_presentation import NotShown, present_dial
    from evaluator import pass_once as P
    from evaluator.resolve import BREADTH_LOOKBACK_ROWS, official_state_for_dial
    from ingestion.wiring import build_wiring, observations_from_store
    dial_field, _ = P._PER_DIAL[dial_id]
    wiring = build_wiring()
    with P._raw_reader(raw_store_path) as raw:
        observations = observations_from_store(raw, wiring, now_utc)
        trend = equity_trend_confirmed(raw, now_utc) if dial_id == EQUITY_DIAL_ID else P.TREND_NOT_COMPUTED
    reading = getattr(evaluate(observations, wiring.snapshot, now_utc), dial_field)
    shown = present_dial(dial_id, reading)
    if type(shown) is NotShown:
        row = P._unknown_row(dial_id, now_utc)
        history.append(row, written_utc=datetime.now(timezone.utc))
        return row
    breadth = shown.magnitude.quantity_for(dial_id)
    contribs = P._contributions_of(dial_id, reading)
    ms = (S.equity_crash_masters if dial_id == EQUITY_DIAL_ID else S.monetary_debasement_masters)(contribs)
    scored = tuple(m for m in ms if type(m) is S.MasterScore)
    if scored:
        top = scored[0]
        for m in scored[1:]:
            if m.score > top.score:
                top = m
        acute = S.Acute(dial_id=dial_id, score=top.score, from_master_id=top.master_id, masters=scored)
    else:
        acute = (S.equity_crash_acute if dial_id == EQUITY_DIAL_ID else S.monetary_debasement_acute)(contribs)
    count = S.count_for_one_dial(contribs)
    rows = history.recent(dial_id, limit=BREADTH_LOOKBACK_ROWS)
    lock = history.alarm_lock_armed(dial_id) if dial_id == EQUITY_DIAL_ID else False
    row = official_state_for_dial(history=rows, as_of=reading.as_of_utc, breadth=breadth, acute=acute, count=count,
                                  trend_confirmed=trend, alarm_lock_armed=lock)
    history.append(row, written_utc=datetime.now(timezone.utc))
    return row


def run_window(name, a, b, rows, days, out_path):
    wd = tempfile.mkdtemp(prefix=f"r2live_{name}_", dir=os.environ.get("R2_TMP", SP))
    raw_path, hist_path = os.path.join(wd, "raw.sqlite"), os.path.join(wd, "hist.sqlite")
    SqliteStore(raw_path).close()
    w = sqlite3.connect(raw_path, isolation_level=None)
    w.execute("INSERT INTO raw_observation (source_id,adapter_id,collector_run_id,attempt_number,requested_utc,observed_utc,outcome)"
              " VALUES ('replay','replay','replay',1,'2000-01-01T00:00:00Z','2000-01-01T00:00:00Z','OK')")
    hist = MachineStateHistoryStore(hist_path)
    avs = [r[0] for r in rows]
    i = 0
    wdays = [d for d in days if D(a) <= d <= D(b)]
    f = open(out_path, "w")
    for d in wdays:
        j = bisect.bisect_right(avs, d)
        if j > i:
            w.execute("BEGIN")
            for av, sid, asof, payload, adm, vint in rows[i:j]:
                payload = with_history(sid, asof, payload)
                w.execute("INSERT OR IGNORE INTO raw_reading (source_id,source_as_of_utc,payload,observation_id,admitted_utc,vintage)"
                          " VALUES (?,?,?,1,?,?)", (sid, asof, payload, adm, vint))
            w.execute("COMMIT")
            i = j
        now = dt.datetime(d.year, d.month, d.day, 0, 0, tzinfo=dt.timezone.utc)
        with SqliteStore(raw_path, read_only=True) as rs:
            tr = equity_trend_confirmed(rs, now)
        armed_before = hist.alarm_lock_armed("equity_crash")
        try:
            if ACUTE_MODE == "available":
                res = {dial: degraded_pass(dial, raw_store_path=raw_path, history=hist, now_utc=now) for dial in DIAL_IDS}
            else:
                res = one_pass_for_both_dials(raw_store_path=raw_path, history=hist, now_utc=now)
            err = None
        except Exception as e:  # recorded, never swallowed silently
            res, err = {}, f"{type(e).__name__}: {e}"
        rec = dict(date=d.isoformat(), window=name, trend=tr, armed_before=armed_before, err=err)
        for dial, row in res.items():
            rec[dial] = dict(state=row.machine_state.value, cand=row.candidate_state.value if row.candidate_state else None,
                             ctr=row.persistence_counter, breadth=row.breadth, acute=row.acute, from_master=row.acute_from_master_id,
                             masters=row.master_scores, count=row.indicator_count, at_or_beyond=row.count_at_or_beyond,
                             rising=row.acute_rising)
        f.write(json.dumps(rec) + "\n")
    f.close()
    return len(wdays)


if __name__ == "__main__":
    which = sys.argv[1:]
    rows, days = load_rows(), spx_days()
    outdir = os.environ.get("R2_OUT", os.path.join(SP, "live", "out"))
    os.makedirs(outdir, exist_ok=True)
    for name, a, b in EPISODES:
        if which and name not in which:
            continue
        t = time.time()
        n = run_window(name, a, b, rows, days, os.path.join(outdir, f"{name}.jsonl"))
        print(name, n, "days", f"{time.time()-t:.0f}s", flush=True)
