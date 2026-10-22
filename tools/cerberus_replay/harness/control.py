"""CONTROL SERIES (NOT the WO-1.17 store): continuous, unrevised public series fetched 2026-10-22 (sha256 pinned in the
report).  Used ONLY for the market-priced masters (vol, curve) and S&P event labels, to give the false-alarm base rate
and a longer event list that the store's 8 event windows cannot.  Labelled as such wherever it is used."""
import csv, datetime as dt, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
CTL = os.path.join(os.path.dirname(HERE), "control")
D = dt.date.fromisoformat


def yahoo(name):
    j = json.load(open(os.path.join(CTL, name + ".json")))["chart"]["result"][0]
    ts = j["timestamp"]
    cl = j["indicators"]["quote"][0]["close"]
    out = {}
    for t, c in zip(ts, cl):
        if c is None:
            continue
        out[dt.datetime.fromtimestamp(t + j["meta"].get("gmtoffset", 0), dt.timezone.utc).date()] = float(c)
    return out


def fred(name):
    out = {}
    for r in csv.reader(open(os.path.join(CTL, name + ".csv"))):
        if r[0] == "observation_date" or r[1] in ("", "."):
            continue
        out[D(r[0])] = float(r[1])
    return out


def load():
    return dict(spx=yahoo("gspc"), vix=yahoo("vix"), vix3m=yahoo("vix3m"),
                t10y3m=fred("T10Y3M"), t10y2y=fred("T10Y2Y"))
