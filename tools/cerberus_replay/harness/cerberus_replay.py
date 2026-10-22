"""CERBERUS WO-1.3b-II replay harness (R2D2).  Point-in-time panel over the WO-1.17 store, scored
by the REAL engine code (crash_detector.engine.statistics + evaluator.resolve) at a pinned SHA.

Nothing here writes to the store.  The store is opened read-only (copy pinned by sha256).

POINT-IN-TIME RULES (stated once, applied uniformly)
  * vintage 'original'            : a row is knowable from its payload vintage_date (conservative at an
                                    archive floor: the first ALFRED vintage is later than the real release).
  * 'current_only' / 'no_revision': knowable from as_of + 1 calendar day (one-day publication lag).
  * a value is USED only if age = t - as_of <= the mapping's staleness_window_seconds (engine rule).
  * missing inputs are EXCLUDED from breadth (engine 'Degraded'), never scored as 0.
"""
from __future__ import annotations
import bisect, datetime as dt, json, math, os, sqlite3, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.dirname(HERE)
REPO = os.path.join(SCR, "repo", "crash-detector")
sys.path[:0] = [os.path.join(REPO, "src"), REPO]

import yaml
from crash_detector.dials.scores import Contribution
from crash_detector.engine import statistics as S
from evaluator import resolve as R
from evaluator.history_store import MachineStateRow

D = dt.date.fromisoformat
DB = os.path.join(SCR, "data", "wo117.sqlite")

EPISODES = [  # DECISION-RULE.md s10 named episodes; windows are the store's own contiguous windows
    ("2000-02", "1999-11-02", "2002-12-31"),
    ("2007-09", "2007-04-02", "2009-12-31"),
    ("2011", "2011-03-02", "2011-12-30"),
    ("2015-16", "2015-06-02", "2016-03-31"),
    ("Q4-2018", "2018-08-02", "2018-12-31"),
    ("Mar-2020", "2019-12-03", "2020-04-30"),
    ("2022", "2021-11-02", "2022-12-30"),
    ("Apr-2025", "2024-12-31", "2025-05-30"),
]

# ---------------------------------------------------------------- mapping / bands / weights
_MAP = yaml.safe_load(open(os.path.join(REPO, "governance/mapping/indicator_mapping.yaml")))
_SCALING = json.load(open(os.path.join(REPO, "deploy/indicator-scaling.json")))
TIER_W = {1: 3.0, 2: 2.0, 3: 1.0}
WINDOW = {m["id"]: m["staleness_window_seconds"] / 86400.0 for m in _MAP["indicators"]}
TIER = {m["id"]: m["tier"] for m in _MAP["indicators"]}
BANDS = {d: {k: v for k, v in _SCALING[d].items()} for d in ("equity_crash", "monetary_debasement")}


def score(dial, ind, x):
    b = BANDS[dial][ind]
    s = (x - b["calm"]) / (b["stress"] - b["calm"])
    return 0.0 if s < 0 else 1.0 if s > 1 else s


# ---------------------------------------------------------------- store -> series
class Series:
    """rows sorted by availability; prefix-best (max as_of) index for O(log n) point-in-time lookup."""

    def __init__(self, rows):
        rows = sorted(rows, key=lambda r: (r[1], r[0]))  # (as_of, avail, value, obs)
        self.rows = rows
        self.avail = [r[1] for r in rows]
        best, bi = [], -1
        for i, r in enumerate(rows):
            if bi < 0 or r[0] >= rows[bi][0]:
                bi = i
            best.append(bi)
        self.best = best

    def latest(self, t):
        k = bisect.bisect_right(self.avail, t)
        return self.rows[self.best[k - 1]] if k else None

    def history_closes(self, t, n):
        """the last n (as_of,value) with avail<=t, newest last, de-duplicated by as_of."""
        k = bisect.bisect_right(self.avail, t)
        seen = {}
        for r in self.rows[:k]:
            seen[r[0]] = r[2]
        ks = sorted(seen)[-n:]
        return [(d, seen[d]) for d in ks]


def load_store(path=DB):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    ser = defaultdict(list)
    for sid, asof, payload, vint in c.execute(
            "select source_id,source_as_of_utc,payload,vintage from raw_reading"):
        p = json.loads(payload)
        a = D(asof[:10])
        if vint == "original":
            av = D(p["vintage_date"])
        else:
            av = a + dt.timedelta(days=1)
        ser[sid].append((a, av, float(p["value"]), D(p["observation_date"])))
    return {k: Series(v) for k, v in ser.items()}


# ---------------------------------------------------------------- indicator derivation (PIT)
DIRECT = {  # indicator -> store source
    "hy_oas": "fred.BAMLH0A0HYM2", "ig_oas": "fred.BAMLC0A0CM",
    "yield_curve_10y3m": "fred.T10Y3M", "yield_curve_10y2y": "fred.T10Y2Y",
    "real_rate_10y_tips": "fred.DFII10", "jobless_claims_4w": "fred.IC4WSA",
    "sahm_rule": "fred.SAHMREALTIME", "michigan_sentiment": "fred.UMCSENT",
    "cboe_skew": "cboe.SKEW", "vix_level": "cboe.VIX", "chicago_fed_nfci": "fred.NFCI",
    "fed_funds_rate": "fred.DFF", "m2_yoy": "fred.M2SL.pc1", "cpi_yoy": "fred.CPIAUCSL.pc1",
    "core_pce_yoy": "fred.PCEPILFE.pc1", "breakeven_5y": "fred.T5YIE",
    "broad_dollar": "fred.DTWEXBGS", "gold_spot": "yahoo.GC=F",
}
RATIOS = {  # indicator -> (num, den, scale)  (same-as_of-date requirement, as engine _ratio)
    "breadth_rsp_spy": ("yahoo.RSP", "yahoo.SPY", 1.0),
    "credit_stress_hyg_lqd": ("yahoo.HYG", "yahoo.LQD", 1.0),
    "copper_gold": ("yahoo.HG=F", "yahoo.GC=F", 1000.0),
    "vix_term_structure": ("cboe.VIX", "cboe.VIX3M", 1.0),
}
# rows that exist in the live catalogue but CANNOT be replayed from this store (stated, not hidden)
NOT_REPLAYABLE = {
    "shiller_cape": "multpl series not in store", "private_credit_stress": "BIZD not in store",
    "constituent_breadth_200dma": "50-name sample not in store", "ism_manufacturing": "z-history too short in windows",
    "gold_real_rate_cross": "needs ~10y rolling-corr history; windows too short",
}


class Panel:
    def __init__(self, store=None):
        self.st = store or load_store()
        spx = self.st["yahoo.^GSPC"]
        seen = {}
        for r in spx.rows:
            seen[r[0]] = r[2]
        self.days = sorted(seen)
        self.spx = seen
        self.win = {}
        for name, a, b in EPISODES:
            for d in self.days:
                if D(a) <= d <= D(b):
                    self.win[d] = name

    def _age_ok(self, ind, t, asof):
        return (t - asof).days <= WINDOW[ind] + 1e-9

    def value(self, ind, t):
        if ind in DIRECT:
            s = self.st.get(DIRECT[ind])
            r = s.latest(t) if s else None
            if r and self._age_ok(ind, t, r[0]):
                return r[2]
            return None
        if ind in RATIOS:
            n, d_, sc = RATIOS[ind]
            sn, sd = self.st.get(n), self.st.get(d_)
            if not sn or not sd:
                return None
            # latest common as_of among points knowable at t
            kn = sn.history_closes(t, 8)
            kd = {a: v for a, v in sd.history_closes(t, 8)}
            for a, v in reversed(kn):
                if a in kd and kd[a] > 0:
                    return v / kd[a] * sc if self._age_ok(ind, t, a) else None
            return None
        if ind == "spx_vs_200dma":
            h = self.st["yahoo.^GSPC"].history_closes(t, 200)
            if len(h) < 200 or (t - h[0][0]).days > 330:  # contiguous-ish 200 closes only
                return None
            if not self._age_ok(ind, t, h[-1][0]):
                return None
            avg = sum(v for _, v in h) / 200.0
            return (h[-1][1] / avg - 1.0) * 100.0
        if ind == "buffett_indicator":
            a, b = self.st.get("fred.NCBEILQ027S"), self.st.get("fred.GDP")
            ra, rb = (a.latest(t) if a else None), (b.latest(t) if b else None)
            if ra and rb and self._age_ok(ind, t, min(ra[0], rb[0])):
                return ra[2] / (rb[2] * 1000.0) * 100.0
            return None
        if ind == "sloos_bank_lending":
            a, b = self.st.get("fred.DRTSCILM"), self.st.get("fred.DRTSCIS")
            ra, rb = (a.latest(t) if a else None), (b.latest(t) if b else None)
            if ra and rb and self._age_ok(ind, t, min(ra[0], rb[0])):
                return (ra[2] + rb[2]) / 2.0
            return None
        if ind == "monetisation_flag":
            w, c = self.st.get("fred.WALCL"), self.st.get("fred.CPILFESL")
            if not w or not c:
                return None
            wl = w.history_closes(t, 400)
            cl = dict(c.history_closes(t, 24))
            if not wl or not cl:
                return None
            last_d, last_v = wl[-1]
            prior = [v for d, v in wl if d <= last_d - dt.timedelta(days=365)]
            if not prior:
                return None
            cd = max(cl)
            mi = cd.year * 12 + cd.month - 1 - 3
            ed = dt.date(mi // 12, mi % 12 + 1, 1)
            # store as_of for monthly is month END; match by (year,month)
            ec = [v for d, v in cl.items() if (d.year, d.month) == (ed.year, ed.month)]
            if not ec or not self._age_ok(ind, t, min(last_d, cd)):
                return None
            growth = (last_v - prior[-1]) / prior[-1]
            ann = ((cl[cd] / ec[0]) ** 4 - 1.0) * 100.0
            return 1.0 if (growth >= 0.10 and ann >= 4.0) else 0.0
        return None

    def indicators(self, dial):
        return list(BANDS[dial])

    def snapshot(self, dial, t):
        """{ind: (value, score)} for every indicator replayable and fresh at t."""
        out = {}
        for ind in BANDS[dial]:
            if ind in NOT_REPLAYABLE:
                continue
            v = self.value(ind, t)
            if v is not None and math.isfinite(v):
                out[ind] = (v, score(dial, ind, v))
        return out


def breadth_of(dial, snap):
    tw = sw = 0.0
    for ind, (_, s) in snap.items():
        w = TIER_W[TIER[ind]]
        tw += w
        sw += w * s
    return (sw / tw) if tw else None


def nominal_weight(dial):
    return sum(TIER_W[TIER[i]] for i in BANDS[dial])


def contributions(dial, snap):
    return tuple(Contribution(source_id=i, category="banded_indicator",
                              weight=TIER_W[TIER[i]], contribution=s) for i, (_, s) in snap.items())


# ---------------------------------------------------------------- S&P truth labels
def forward_labels(panel, h_primary=126, thr_primary=-0.20, h_secondary=63, thr_secondary=-0.15):
    """per day: (min fwd return over h days, observed horizon fully inside the window?)"""
    days = panel.days
    lab = {}
    idx = {d: i for i, d in enumerate(days)}
    for d in days:
        w = panel.win.get(d)
        i = idx[d]
        p0 = panel.spx[d]
        out = {}
        for key, h in (("p", h_primary), ("s", h_secondary)):
            fut = []
            for j in range(i + 1, min(i + 1 + h, len(days))):
                if panel.win.get(days[j]) != w:
                    break
                fut.append(panel.spx[days[j]] / p0 - 1.0)
            full = (len(fut) == h)
            out[key] = (min(fut) if fut else 0.0, full)
        lab[d] = out
    return lab


def drawdown_path(panel):
    """peak-to-date drawdown within each window (running max inside window)."""
    dd = {}
    cur_w, pk = None, 0.0
    for d in panel.days:
        w = panel.win.get(d)
        if w != cur_w:
            cur_w, pk = w, 0.0
        pk = max(pk, panel.spx[d])
        dd[d] = panel.spx[d] / pk - 1.0
    return dd
