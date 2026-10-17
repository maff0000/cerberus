#!/usr/bin/env python3
"""THE RELEASE-LAG PROBE — on what DATE did each quarterly observation first exist?

    PYTHONPATH=src:. python3 tools/probe/release_lag_probe.py --out evidence/<file>.json

WHY THIS EXISTS (WO-1.19 item 5). The two quarterly rows whose relevance windows do not fit
their cadence - ``sloos_bank_lending`` (DRTSCILM + DRTSCIS) and ``buffett_indicator``
(NCBEILQ027S + GDP) - can only be given a release-calendar relevance rule if the RELEASE
CALENDAR is a measured fact. The figures quoted in ``ingestion.catalog.WINDOW_OVERRIDES``
today are derivations from knowledge of the publication schedules, stated as such ("NO
RELEASE CALENDAR WAS FETCHED FOR ANY FIGURE BELOW"), and a relevance rule built on an
unverified lag would read the dial STALE or LIVE on an assumption.

This probe does not ask a release calendar. It asks ALFRED the only question that is
operative for THIS engine: on what date did the observation the collector stores first
become available in the series the collector reads? A published calendar says when a report
was issued; the first vintage containing the observation says when our feed could have seen
it, which is the quantity a relevance window is measured against.

WHAT IT MEASURES. For each (series, observation date) pair, the EARLIEST vintage date whose
body contains that observation with a value, found by bisection on presence within a
horizon of :data:`HORIZON_DAYS` after the observation date. The lag is reported twice -
from the observation date (the quarter START, which is where FRED dates a quarterly figure)
and from the quarter END (the instant ``ingestion.adapters.as_of_for``'s ``quarter_end``
rule ages a reading from) - because the two rows under WO-1.19 item 5 declare DIFFERENT
as-of rules and a single lag number would be read against the wrong anchor for one of them.

WHOLE BODIES, NEVER A cosd/coed WINDOW. ``tools/probe/alfred_vintage_probe.py`` recorded
(2026-10-13) that ALFRED CLAMPS an out-of-range observation window instead of refusing it,
which silently answers a different question from the one asked. Presence of an observation
is exactly the kind of question that bug would corrupt - an absent observation and a
clamped-away observation look identical - so every request here is for the whole vintage
body and the observation is looked for in it. The quarterly series probed here are a few
hundred rows, so this costs bytes and buys the answer being about what was asked.

IT IS A PROBE, NOT A GATE. It opens sockets to a third party; its verdict is not
reproducible offline and can never be a register check (CD-PL-F48). It writes a JSON
record; a human reads it and decides what the engine does.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from typing import Union

HOST = "alfred.stlouisfed.org"
#: ALFRED's keyless graph CSV - the same public door ``tools/probe/alfred_vintage_probe.py``
#: uses, declared for the backfill path in ``ingestion.backfill_adapters.BACKFILL_EGRESS_HOSTS``.
#: No API key is involved anywhere in this file; api.stlouisfed.org is never contacted.
BASE = f"https://{HOST}/graph/alfredgraph.csv"
#: How far after an observation date the probe will look for the vintage that first carried
#: it. Wide enough for a Z.1 release (~70 days after the quarter ends, i.e. ~161 after the
#: quarter starts) with room for a release that slips, and bounded so that an observation
#: which was NEVER published is reported as unpublished rather than hunted for forever.
HORIZON_DAYS = 400
#: Courtesy gap between requests to a public endpoint nobody is charging us for. The figure
#: ``ingestion.backfill.BACKFILL_PACING_SECONDS`` already uses against the same host.
PACE = 0.7

#: The series probed, and the indicator each one's cadence governs. Both legs of each row are
#: probed separately and NEITHER is taken as a proxy for the other: a derived row's state is
#: the WORST of its legs (``ingestion.report.indicator_states``), so the binding cadence is
#: the SLOWEST leg's and that is a measurement, not an assumption about which leg is slower.
SERIES = (
    ("DRTSCILM", "sloos_bank_lending"),
    ("DRTSCIS", "sloos_bank_lending"),
    ("NCBEILQ027S", "buffett_indicator"),
    ("GDP", "buffett_indicator"),
)

#: The observation dates asked about: quarter STARTS, which is where FRED dates a quarterly
#: observation (``ingestion.backfill_dates``, verified against the live DEV store 2026-10-13).
#: Several years, so a per-quarter difference in release lag shows up as one rather than
#: being averaged away by a single sample.
FIRST_QUARTER = "2023-01-01"


def _get(url: str, timeout: float = 30.0) -> str:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(8_000_000).decode("utf-8", "replace")


def _url(series: str, vintage: Union[str, None]) -> str:
    parts = [f"id={series}"]
    if vintage:
        parts.append(f"vintage_date={vintage}")
    return BASE + "?" + "&".join(parts)


def _observations(body: str, series: str) -> tuple[dict, str]:
    """``{observation_date: value}`` plus the vintage suffix the SERVER put in the header.

    The suffix is checked by the caller against the vintage ASKED for: ALFRED labels its
    value column ``<ID>_<YYYYMMDD>``, so a body that answered a different vintage is not
    read as the one requested.
    """
    lines = body.strip().splitlines()
    header = lines[0].split(",") if lines else []
    if len(header) != 2 or header[0] != "observation_date":
        raise ValueError("unexpected header")
    if not header[1].startswith(series + "_"):
        raise ValueError(f"header names {header[1]!r}, not a vintage of {series}")
    out = {}
    for line in lines[1:]:
        cells = line.split(",")
        if len(cells) == 2 and cells[1] not in ("", "."):
            out[cells[0]] = float(cells[1])
    return out, header[1][len(series) + 1:]


def _has(series: str, observation: str, vintage: date, probes: list) -> bool:
    """Did the vintage served on ``vintage`` carry ``observation`` with a value?"""
    time.sleep(PACE)
    body = _get(_url(series, vintage.isoformat()))
    values, served = _observations(body, series)
    if served != vintage.isoformat().replace("-", ""):
        # ALFRED serves the nearest vintage it has when asked for a date it does not hold
        # (a weekend, a holiday). That is an ANSWER about a different date, so the date the
        # server states is the one recorded, and the bisection is told about the real one.
        probes.append({"asked": vintage.isoformat(), "served": served,
                       "carries": observation in values})
        return observation in values
    probes.append({"asked": vintage.isoformat(), "served": served, "carries": observation in values})
    return observation in values


def first_vintage_carrying(series: str, observation: str) -> dict:
    """The earliest vintage date whose body carries ``observation``, by bisection on presence.

    Returns the date, the number of GETs it cost, and the bracket it was narrowed to, so a
    reader can see the answer is a measured pair of adjacent days and not a single probe.
    """
    obs = date.fromisoformat(observation)
    low, high = obs, obs + timedelta(days=HORIZON_DAYS)
    probes: list = []
    if not _has(series, observation, high, probes):
        return {"observation": observation, "first_vintage": None, "probes": len(probes),
                "note": f"not carried by any vintage within {HORIZON_DAYS} days - unpublished, "
                        "or published later than this probe looks"}
    if _has(series, observation, low, probes):
        return {"observation": observation, "first_vintage": low.isoformat(), "probes": len(probes),
                "note": "already carried by the vintage served ON the observation date - the "
                        "release lag is zero or the observation date is not a period start"}
    # Invariant: low does not carry it, high does. Narrow to adjacent days.
    while (high - low).days > 1:
        middle = low + timedelta(days=(high - low).days // 2)
        if _has(series, observation, middle, probes):
            high = middle
        else:
            low = middle
    return {"observation": observation, "first_vintage": high.isoformat(),
            "last_vintage_without": low.isoformat(), "probes": len(probes), "note": ""}


def _quarter_starts(first: str, today: date) -> list:
    out, year, month = [], int(first[:4]), int(first[5:7])
    while True:
        day = date(year, month, 1)
        if day > today:
            return out
        out.append(day.isoformat())
        month += 3
        if month > 12:
            year, month = year + 1, month - 12


def _quarter_end(quarter_start: str) -> date:
    start = date.fromisoformat(quarter_start)
    month = start.month + 3
    year = start.year + (1 if month > 12 else 0)
    return date(year, month - 12 if month > 12 else month, 1) - timedelta(days=1)


def probe(series: str, indicator: str, today: date) -> dict:
    """Every quarter start from :data:`FIRST_QUARTER`, with the lag from both anchors."""
    releases = []
    for observation in _quarter_starts(FIRST_QUARTER, today):
        found = first_vintage_carrying(series, observation)
        if found.get("first_vintage"):
            published = date.fromisoformat(found["first_vintage"])
            found["lag_days_from_quarter_start"] = (published - date.fromisoformat(observation)).days
            found["lag_days_from_quarter_end"] = (published - _quarter_end(observation)).days
        releases.append(found)
    measured = [r for r in releases if r.get("first_vintage")]
    return {
        "series": series,
        "governs": indicator,
        "probed_utc": datetime.now(timezone.utc).date().isoformat(),
        "releases": releases,
        "lag_days_from_quarter_start": {
            "min": min((r["lag_days_from_quarter_start"] for r in measured), default=None),
            "max": max((r["lag_days_from_quarter_start"] for r in measured), default=None),
            "measured_quarters": len(measured),
        },
        "lag_days_from_quarter_end": {
            "min": min((r["lag_days_from_quarter_end"] for r in measured), default=None),
            "max": max((r["lag_days_from_quarter_end"] for r in measured), default=None),
        },
        "unpublished_quarters": [r["observation"] for r in releases if not r.get("first_vintage")],
    }


def main(argv: Union[list, None] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, help="JSON record to write")
    parser.add_argument("--series", action="append", default=None,
                        help="probe only this series (repeatable); default is all four legs")
    args = parser.parse_args(argv)

    today = datetime.now(timezone.utc).date()
    wanted = [(s, i) for s, i in SERIES if args.series is None or s in args.series]
    record = {
        "credential": "none (keyless)",
        "endpoint": BASE,
        "horizon_days": HORIZON_DAYS,
        "first_quarter": FIRST_QUARTER,
        "probed_utc": today.isoformat(),
        "asks": "the earliest ALFRED vintage carrying each quarterly observation - i.e. the "
                "date our own feed could first have seen it",
        "series": [],
    }
    for series, indicator in wanted:
        print(f"-- {series} ({indicator})", file=sys.stderr, flush=True)
        try:
            record["series"].append(probe(series, indicator, today))
        except (urllib.error.URLError, ValueError) as failure:
            record["series"].append({"series": series, "governs": indicator,
                                     "error": f"{type(failure).__name__}: {failure}"})
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
