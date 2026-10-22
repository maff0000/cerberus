"""Decision-grade metrics.  The product's job is PERMISSION (tranches only in CALM/RECOVERY), so the primary
measure is 'permission denied' (WATCH|ALARM|UNKNOWN), with ALARM-only reported alongside for continuity with WO-1.3b."""
from __future__ import annotations
import collections
import cerberus_replay as C

DENY = ("WATCH", "ALARM", "UNKNOWN")


def label_days(panel, lab):
    """pos = >=20% fall within 126d OR >=15% within 63d (observed); neg = both horizons fully observed & neither hit;
    cen = censored by the window edge."""
    out = {}
    for d, v in lab.items():
        (mp, fp), (ms, fs) = v["p"], v["s"]
        if mp <= -0.20 or ms <= -0.15:
            out[d] = "pos"
        elif fp and fs:
            out[d] = "neg"
        else:
            out[d] = "cen"
    return out


def day_table(states, labels, panel, episodes=None):
    """counts per episode and total of (label x permission)."""
    t = collections.defaultdict(collections.Counter)
    for d, s in states.items():
        L = labels.get(d)
        if L is None:
            continue
        ep = panel.win[d]
        st = s["state"] if isinstance(s, dict) else s
        for key in (ep, "ALL"):
            t[key][(L, st)] += 1
    return t


def summarise(t, key="ALL", deny=DENY):
    c = t[key]
    pos = sum(v for (L, s), v in c.items() if L == "pos")
    neg = sum(v for (L, s), v in c.items() if L == "neg")
    pos_den = sum(v for (L, s), v in c.items() if L == "pos" and s in deny)
    neg_den = sum(v for (L, s), v in c.items() if L == "neg" and s in deny)
    alarm_pos = sum(v for (L, s), v in c.items() if L == "pos" and s == "ALARM")
    alarm_neg = sum(v for (L, s), v in c.items() if L == "neg" and s == "ALARM")
    return dict(pos=pos, neg=neg,
                recall_deny=pos_den / pos if pos else float("nan"),
                fpr_deny=neg_den / neg if neg else float("nan"),
                prec_deny=pos_den / (pos_den + neg_den) if pos_den + neg_den else float("nan"),
                recall_alarm=alarm_pos / pos if pos else float("nan"),
                fpr_alarm=alarm_neg / neg if neg else float("nan"),
                prec_alarm=alarm_pos / (alarm_pos + alarm_neg) if alarm_pos + alarm_neg else float("nan"))


def first_crossing(panel, ep, level):
    """first date in episode where S&P is `level` (e.g. -0.10) below its running in-window peak."""
    dd = C.drawdown_path(panel)
    for d in panel.days:
        if panel.win[d] == ep and dd[d] <= level:
            return d
    return None


def lead_table(panel, states, deny_states=("ALARM",), level=-0.10):
    """per episode: first day (>= window start) the state enters deny_states AND stays for >=5 days,
    versus the day the S&P first closes `level` below its peak.  lead>0 = signalled BEFORE the damage."""
    out = {}
    for name, a, b in C.EPISODES:
        ds = [d for d in panel.days if panel.win[d] == name]
        cross = first_crossing(panel, name, level)
        first = None
        for i, d in enumerate(ds):
            if states[d]["state"] in deny_states:
                first = d
                break
        out[name] = (first, cross, (cross - first).days if first and cross else None)
    return out
