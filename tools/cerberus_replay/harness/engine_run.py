"""Engine layer: per-day statistics from the REAL engine, plus a parameterised state machine whose
default-parameter output is proven byte-identical to the REAL evaluator.resolve.official_state_for_dial."""
from __future__ import annotations
import datetime as dt
from dataclasses import dataclass, field
import cerberus_replay as C
S, R = C.S, C.R


def build_rows(panel, dial="equity_crash"):
    masters_fn = S.equity_crash_masters if dial == "equity_crash" else S.monetary_debasement_masters
    acute_fn = S.equity_crash_acute if dial == "equity_crash" else S.monetary_debasement_acute
    rows = {}
    for d in panel.days:
        snap = panel.snapshot(dial, d)
        if not snap:
            rows[d] = dict(w=panel.win[d], snap={}, breadth=None, masters={}, unknown=(), acute_real=None, cnt=None)
            continue
        contribs = C.contributions(dial, snap)
        ms = masters_fn(contribs)
        scored = {m.master_id: m.score for m in ms if type(m) is S.MasterScore}
        unknown = tuple(m.master_id for m in ms if type(m) is S.MasterUnknown)
        rows[d] = dict(
            w=panel.win[d], snap=snap, breadth=C.breadth_of(dial, snap), masters=scored, unknown=unknown,
            acute_real=acute_fn(contribs),            # live-strict acute (AcuteUnknown if any master unknown)
            cnt=S.count_for_one_dial(contribs),
            wcov=sum(C.TIER_W[C.TIER[i]] for i in snap) / C.nominal_weight(dial),
        )
    return rows


# ------------------------------------------------------------------ parameterised machine
ELIGIBLE_DEFAULT = {"credit_master": True, "curve_master": False, "volatility_master": True,
                    "financial_conditions_master": True}


@dataclass
class Params:
    warn: dict = field(default_factory=lambda: {})      # per master; default PROVISIONAL_WARNING
    stress: dict = field(default_factory=lambda: {})
    exit: dict = field(default_factory=lambda: {})
    eligible: dict = field(default_factory=lambda: dict(ELIGIBLE_DEFAULT))
    b_mid: float = S.PROVISIONAL_BREADTH_MID
    b_high: float = S.PROVISIONAL_BREADTH_HIGH
    k: int | None = None            # None = count NOT in rule 3 (as deployed since WO-1.3e)
    count_fn: object = None         # callable(row)->int when k is set
    lookback: int = R.BREADTH_LOOKBACK_ROWS
    deadband: float = S.PROVISIONAL_BREADTH_RISE_DEADBAND
    persistence: int = R.PROVISIONAL_PERSISTENCE
    strict_unknown: bool = False    # True = live behaviour (any master unknown -> UNKNOWN)
    trend: dict | None = None       # date -> bool ; None = hard False (as deployed)
    lock: bool = False              # EXPERIMENT (not deployed): after an official ALARM, CALM is unreachable until RECOVERY


def candidate(row, p, breadth_back, trend):
    ms = row["masters"]
    if p.strict_unknown and row["unknown"]:
        return "UNKNOWN"
    if not ms and row["breadth"] is None:
        return "UNKNOWN"
    if not ms:                       # no master at all -> cannot judge acute
        return "UNKNOWN"
    st = lambda m: p.stress.get(m, S.PROVISIONAL_STRESS)
    wn = lambda m: p.warn.get(m, S.PROVISIONAL_WARNING)
    ex = lambda m: p.exit.get(m, S.PROVISIONAL_EXIT)
    if any(p.eligible.get(m, True) and v >= st(m) for m, v in ms.items()):
        return "ALARM"
    b = row["breadth"]
    if b is not None and b >= p.b_high and (p.k is None or p.count_fn(row) >= p.k):
        return "ALARM"
    rising = (breadth_back is not None and b is not None and b > breadth_back + p.deadband and b >= p.b_mid)
    if any(v >= wn(m) for m, v in ms.items()) or rising:
        return "WATCH"
    if all(v <= ex(m) for m, v in ms.items()) and trend:
        return "RECOVERY"
    return "CALM"


def _armed_span(hist):
    """rows back to (and including) the most recent official RECOVERY; the lock holds while an ALARM sits inside."""
    for i, h in enumerate(hist):
        if h["state"] == "RECOVERY":
            return i
    return len(hist)


def run_machine(rows, days, p: Params):
    """walk days in order; history resets at each window boundary (the store has no data between)."""
    out = {}
    hist = []                     # most-recent-first: dicts(state,cand,counter,breadth,acute)
    cur = None
    for d in days:
        r = rows[d]
        if r["w"] != cur:
            cur, hist = r["w"], []
        back = hist[p.lookback - 1]["breadth"] if len(hist) >= p.lookback else None
        tr = bool(p.trend.get(d, False)) if p.trend else False
        cand = candidate(r, p, back, tr)
        prev = hist[0] if hist else None
        armed = p.lock and any(h["state"] == "ALARM" for h in hist[: _armed_span(hist)])
        if cand == "RECOVERY" and not armed and (prev is None or prev["state"] != "ALARM"):
            cand = "CALM"
        if p.lock and armed and cand == "CALM":
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
            if ctr >= p.persistence:
                off, ctr = cand, 0
            else:
                off = prev["state"]
        acute = max(r["masters"].values()) if r["masters"] else None
        hist.insert(0, dict(state=off, cand=cand, counter=ctr, breadth=r["breadth"], acute=acute))
        out[d] = dict(state=off, cand=cand, counter=ctr, breadth=r["breadth"], acute=acute)
    return out


# ------------------------------------------------------------------ parity vs the REAL resolver
def real_machine(rows, days, panel, dial="equity_crash"):
    """thread the REAL official_state_for_dial; returns {date: state-name}. Live-strict semantics."""
    out, hist, cur = {}, [], None
    for d in days:
        r = rows[d]
        if r["w"] != cur:
            cur, hist = r["w"], []
        if r["breadth"] is None:
            continue
        acute = r["acute_real"]
        row = R.official_state_for_dial(
            history=tuple(hist[:S and 25]), as_of=dt.datetime.combine(d, dt.time(21)),
            breadth=float(r["breadth"]), acute=acute, count=r["cnt"], trend_confirmed=False)
        hist.insert(0, row)
        out[d] = row.machine_state.value if hasattr(row.machine_state, "value") else str(row.machine_state)
    return out
