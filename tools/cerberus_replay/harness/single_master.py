"""Calibrate ONE market-priced master on the continuous control history, through the same state machine
(persistence, hysteresis, ALARM->WATCH exit) the engine uses.  Returns span-level and event-level results."""
import datetime as dt
import collections
import control as K
import engine_run as E
import cerberus_replay as C

X = None


def data():
    global X
    if X is None:
        X = K.load()
    return X


def zigzag_declines(days, px, th=0.15):
    piv, mode, hi, lo = [], None, days[0], days[0]
    for d in days:
        if px[d] > px[hi]:
            hi = d
        if px[d] < px[lo]:
            lo = d
        if mode in (None, "up") and px[d] / px[hi] - 1 <= -th:
            piv.append(("H", hi)); mode = "down"; lo = d
        elif mode == "down" and px[d] / px[lo] - 1 >= th:
            piv.append(("L", lo)); mode = "up"; hi = d
    out = []
    for a, b in zip(piv, piv[1:]):
        if a[0] == "H" and b[0] == "L":
            out.append((a[1], b[1]))
    return out


def clusters(declines, gap_days=200):
    """merge swings whose gap is < gap_days into ONE episode (independent-event unit)."""
    cl = []
    for p, t in declines:
        if cl and (p - cl[-1][1]).days < gap_days:
            cl[-1] = (cl[-1][0], t)
        else:
            cl.append((p, t))
    return cl


def score_series(kind, start=dt.date(1990, 1, 2)):
    x = data()
    days = [d for d in sorted(x["spx"]) if d >= start and d in x["vix"]]
    s = {}
    for d in days:
        if kind == "vol":
            a = C.score("equity_crash", "vix_level", x["vix"][d])
            if d in x["vix3m"] and x["vix3m"][d] > 0:
                a = max(a, C.score("equity_crash", "vix_term_structure", x["vix"][d] / x["vix3m"][d]))
            s[d] = a
        elif kind == "vol_level_only":
            s[d] = C.score("equity_crash", "vix_level", x["vix"][d])
    return days, s


def curve_series(start=dt.date(1990, 1, 2)):
    x = data()
    days = [d for d in sorted(x["spx"]) if d >= start and d in x["t10y3m"] and d in x["t10y2y"]]
    return days, {d: max(C.score("equity_crash", "yield_curve_10y3m", x["t10y3m"][d]),
                         C.score("equity_crash", "yield_curve_10y2y", x["t10y2y"][d])) for d in days}


def run(days, s, master, warn, stress, exit_, eligible=True, persistence=5):
    rows = {d: dict(w="all", breadth=None, masters={master: s[d]}, unknown=(), snap={}) for d in days}
    p = E.Params(warn={master: warn}, stress={master: stress}, exit={master: exit_},
                 eligible={master: eligible}, persistence=persistence, b_mid=9, b_high=9)
    return E.run_machine(rows, days, p)


def spans(states, days, which):
    out, cur = [], None
    for d in days:
        inside = states[d]["state"] in which
        if inside and cur is None:
            cur = [d, d]
        elif inside:
            cur[1] = d
        elif cur is not None:
            out.append(tuple(cur)); cur = None
    if cur is not None:
        out.append(tuple(cur))
    return out
