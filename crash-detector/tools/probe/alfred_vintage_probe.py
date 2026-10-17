#!/usr/bin/env python3
"""THE ALFRED VINTAGE PROBE — what does each FRED series' REVISION HISTORY actually look like?

    PYTHONPATH=src:. python3 tools/probe/alfred_vintage_probe.py --out evidence/<file>.json
    PYTHONPATH=src:. python3 tools/probe/alfred_vintage_probe.py --out evidence/<file>.json \
        --series DRTSCIS --merge          # amend an existing record with ONE new series

WHY THIS EXISTS (WO-1.14). DECISION-RULE.md §10 forbids filling any calibrated parameter
from "today's vintages", and requires a replay through 2000-02, 2007-09, 2011, 2015-16,
Q4 2018, March 2020, 2022 and April 2025. Backfilling a revised series from its CURRENT
history gives today's revised number for a historical date — a value the live collector
could NOT have seen then. That is lookahead bias, and which series carry it is a QUESTION
ABOUT THE SOURCE, not a judgement anybody here is entitled to make by assertion.

So this probe ASKS ALFRED, series by series, and writes down what it answered. It is the
evidence behind ``ingestion.vintage.REVISION_PRONE``; that table may be changed only by
re-running this and reading the result.

IT IS A PROBE, NOT A GATE. It opens sockets to a third party, so its verdict is not
reproducible offline and can never be a register check (CD-PL-F48). It writes a JSON
record; a human reads it and edits a declaration.

WHAT IT MEASURES, AND THE THREE SEPARATE FACTS IT KEEPS APART
------------------------------------------------------------
1. ``vintage_depth`` — the EARLIEST vintage date ALFRED will serve for the series, found by
   bisection on HTTP status (200 vs 404). This is the real floor on point-in-time backfill
   and it VARIES PER SERIES; it is not one number for the whole source.
2. ``revision`` — the earliest available vintage compared with today's, over every
   observation date the two share. ``differing`` counts observations whose value CHANGED
   after first publication. A series with zero differing observations over a long shared
   span is NOT revision-prone, whatever anyone guessed.
3. ``trail`` — the value of ONE fixed observation read at several successive vintages. This
   catches the case the pairwise comparison can miss: a figure revised and then revised
   BACK, which looks unrevised if you only read the two ends.

Each is reported as a number this file obtained, next to the request that obtained it.
Nothing is inferred and nothing is averaged across series.

AMENDING AN EXISTING RECORD (``--merge``, WO-1.19). A round that adds ONE FRED pair to the
catalog has to measure that pair, not re-measure the other 23: rewriting 23 recorded
measurements and their dates to learn one thing is how an evidence file loses the ability to
say WHEN each of its numbers was obtained. ``--merge`` therefore probes the series asked for
and folds them into the document already at ``--out``, leaving its header's ``probed_utc``
alone, stamping the amended records with their own, and listing the amendment in
``amendments``. See :func:`merge` for the two conditions that keep that honest.

TRANSFORMATIONS ARE PROBED AS WIRED. ``M2SL``, ``CPIAUCSL`` and ``PCEPILFE`` are collected
through FRED's own ``pc1`` (percent change from a year ago), so the quantity whose revisions
matter is the YoY figure, not the index. The probe asks for exactly what the catalog asks
for, because a YoY figure revises when EITHER of its two index levels revises and is
therefore more revision-prone than the index — reporting the index would understate it.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from typing import Union

HOST = "alfred.stlouisfed.org"
#: ALFRED's keyless graph CSV. The SAME public, credential-free door as fredgraph.csv (see
#: ingestion.adapters.FredAdapter) with one extra query parameter, ``vintage_date``. No API
#: key is involved anywhere in this file; api.stlouisfed.org is never contacted.
BASE = f"https://{HOST}/graph/alfredgraph.csv"
#: Bisection floor. Nothing in DECISION-RULE.md §10 asks for a replay before 2000, and
#: ALFRED's own vintage record does not begin before this for any series we collect.
FLOOR = date(1990, 1, 1)
#: The replay window §10 cares about: the earliest episode it names is 2000-02. This is
#: REPORTED AS A SLICE of the comparison, never used to bound it — see :func:`revision` for
#: what bounding the request did instead.
COMPARE_FROM = "1999-01-01"
#: Courtesy gap between requests to a public endpoint nobody is charging us for.
PACE = 0.7
#: A difference below this is reprinting noise (a decimal place moved), not a revision.
#: Reported SEPARATELY from the exact count so the two are never conflated.
MATERIAL = 0.005


def _get(url: str, timeout: float = 30.0, *, head: bool = False) -> Union[str, int]:
    """The body, or — for ``head`` — the HTTP status as an int. ``404`` is an ANSWER here."""
    request = urllib.request.Request(url, method="HEAD" if head else "GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status if head else response.read(8_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as failure:
        if head:
            return failure.code
        raise


def _url(series: str, transformation: Union[str, None], vintage: Union[str, None],
         start: Union[str, None] = None, end: Union[str, None] = None) -> str:
    parts = [f"id={series}"]
    if transformation:
        parts.append(f"transformation={transformation}")
    if vintage:
        parts.append(f"vintage_date={vintage}")
    if start:
        parts.append(f"cosd={start}")
    if end:
        parts.append(f"coed={end}")
    return BASE + "?" + "&".join(parts)


def _column(series: str, transformation: Union[str, None]) -> str:
    return series + (f"_{transformation.upper()}" if transformation else "")


def _observations(body: str, series: str, transformation: Union[str, None]) -> tuple[dict, str]:
    """``{observation_date: value}`` plus the vintage suffix the SERVER put in the header.

    The returned suffix is checked by the caller against the vintage it ASKED for. ALFRED
    labels its value column ``<ID>[_<TRANSFORM>]_<YYYYMMDD>``, so the response states which
    vintage it is; a body that answered a different one is not read as the one requested.
    """
    lines = body.strip().splitlines()
    header = lines[0].split(",") if lines else []
    if len(header) != 2 or header[0] != "observation_date":
        raise ValueError("unexpected header")
    prefix = _column(series, transformation) + "_"
    if not header[1].startswith(prefix):
        raise ValueError(f"header names {header[1]!r}, not a vintage of {prefix}")
    out = {}
    for line in lines[1:]:
        cells = line.split(",")
        if len(cells) == 2 and cells[1] not in ("", "."):
            out[cells[0]] = float(cells[1])
    return out, header[1][len(prefix):]


def vintage_depth(series: str, transformation: Union[str, None], today: date) -> dict:
    """The earliest vintage ALFRED serves, by bisection on status. ``None`` if it serves none."""
    if _get(_url(series, transformation, today.isoformat()), head=True) != 200:
        return {"earliest": None, "probes": 1, "note": "no vintage served, not even today's"}
    low, high, probes = FLOOR, today, 1
    if _get(_url(series, transformation, low.isoformat()), head=True) == 200:
        return {"earliest": low.isoformat(), "probes": 2, "note": "at or before the 1990 probe floor"}
    probes += 1
    # Invariant: low is refused (404), high is served (200). Narrow to adjacent days.
    while (high - low).days > 1:
        middle = low + timedelta(days=(high - low).days // 2)
        time.sleep(PACE)
        probes += 1
        if _get(_url(series, transformation, middle.isoformat()), head=True) == 200:
            high = middle
        else:
            low = middle
    return {"earliest": high.isoformat(), "probes": probes, "note": ""}


def _compare(first: dict, current: dict, dates: list) -> dict:
    """First-published vs today over exactly ``dates``, and nothing inferred beyond them."""
    changed = [(d, first[d], current[d]) for d in dates if abs(first[d] - current[d]) > 1e-9]
    material = [row for row in changed if abs(row[1] - row[2]) > MATERIAL]
    biggest = max(changed, key=lambda row: abs(row[1] - row[2]), default=None)
    return {
        "shared_observations": len(dates),
        "shared_span": [dates[0], dates[-1]] if dates else None,
        "differing": len(changed),
        "differing_materially": len(material),
        "largest_change": ({"observation": biggest[0], "first_published": biggest[1],
                            "today": biggest[2], "delta": round(biggest[2] - biggest[1], 6)}
                           if biggest else None),
    }


def revision(series: str, transformation: Union[str, None], earliest: str) -> dict:
    """Earliest available vintage vs today's, over every observation date they share.

    BOTH bodies are fetched WHOLE and the shared window is intersected HERE. It is NOT asked
    for with ``cosd``/``coed``, because ALFRED does not REFUSE an out-of-range window — it
    CLAMPS it. Verified 2026-10-13: ``id=M2SL&transformation=pc1&vintage_date=1990-01-01``
    with ``cosd=1999-01-01`` answers with that vintage's whole 1960-1989 history, the window
    silently dropped, while the same ``cosd`` on the CURRENT vintage is applied and trims it
    to 1999 onward. Asking each side for the same window therefore compared 1960-1989
    against 1999-2026 and found nothing in common: ``shared=0``, a probe that could not
    answer, printed in the same shape as "this series is never revised". An intersection
    taken from two whole bodies cannot fail that way for any series.

    The §10 replay window is still reported, as a SLICE of the result (``replay_window``),
    so what the calibration actually replays is visible without being able to empty the
    comparison. A series whose earliest vintage predates that window — M2SL, CPIAUCSL,
    UMCSENT — is judged on the span the two vintages genuinely share, which is the only
    span about which ALFRED can be asked anything at all.
    """
    first_body = _get(_url(series, transformation, earliest))
    time.sleep(PACE)
    current_body = _get(_url(series, transformation, None))
    first, served = _observations(first_body, series, transformation)
    current, _ = _observations(current_body, series, transformation)
    if served != earliest.replace("-", ""):
        return {"error": f"asked vintage {earliest}, server answered {served}"}
    shared = sorted(set(first) & set(current))
    in_window = [d for d in shared if d >= COMPARE_FROM]
    return {
        "first_vintage": earliest,
        **_compare(first, current, shared),
        "replay_window": {
            "from": COMPARE_FROM,
            **_compare(first, current, in_window),
            "note": "" if in_window else
                    "the first vintage holds no observation inside the replay window; the "
                    "verdict rests on the whole shared span above, which is the only span "
                    "these two vintages share",
        },
        "first_vintage_observations": len(first),
        "current_vintage_observations": len(current),
        "first_vintage_span": [min(first), max(first)] if first else None,
    }


def trail(series: str, transformation: Union[str, None], target: str, earliest: str,
          today: date) -> dict:
    """ONE observation read at successive vintages: the revision history of a single figure.

    The figure trailed is the latest observation the series ACTUALLY HAS on or before
    ``target``, not ``target`` itself. A weekly series is dated on its own day of the week
    — IC4WSA on a Saturday, WALCL on a Wednesday, NFCI on a Friday — so a hardcoded Monday
    is absent from every vintage of it, and the trail would read ``None`` five times and
    report a figure that is never revised because it never existed. One windowed read of the
    current vintage establishes which date to ask for; the vintages are then asked for that.
    """
    window = (date.fromisoformat(target) - timedelta(days=130)).isoformat()
    present, _ = _observations(
        _get(_url(series, transformation, None, window, target)), series, transformation)
    if not present:
        return {"observation": None, "readings": [], "distinct_values": 0, "values_seen": 0,
                "note": f"the current vintage has no observation in the 130 days to {target}"}
    observation = max(present)
    start = date.fromisoformat(observation)
    floor = date.fromisoformat(earliest)
    readings = []
    for when in (start + timedelta(days=offset) for offset in (10, 45, 120, 400, 1000)):
        if when > today or when < floor:
            continue
        time.sleep(PACE)
        body = _get(_url(series, transformation, when.isoformat(), observation, observation))
        rows, served = _observations(body, series, transformation)
        readings.append({"vintage": when.isoformat(), "served": served,
                         "value": rows.get(observation)})
    readings.append({"vintage": "current", "served": "current",
                     "value": present.get(observation)})
    seen = [r["value"] for r in readings if r["value"] is not None]
    return {"observation": observation, "asked_on_or_before": target, "readings": readings,
            "distinct_values": len(set(seen)), "values_seen": len(seen), "note": ""}


def probe_one(series: str, transformation: Union[str, None], today: date,
              trail_observation: Union[str, None]) -> dict:
    record: dict = {"series": series, "transformation": transformation,
                    "column": _column(series, transformation)}
    try:
        record["vintage_depth"] = vintage_depth(series, transformation, today)
        earliest = record["vintage_depth"]["earliest"]
        if earliest is None:
            return record
        time.sleep(PACE)
        record["revision"] = revision(series, transformation, earliest)
        if trail_observation:
            record["trail"] = trail(series, transformation, trail_observation, earliest, today)
    except (urllib.error.URLError, ValueError, OSError) as failure:
        record["error"] = f"{type(failure).__name__}: {failure}"
    return record


def fred_series_from_catalog() -> list[tuple[str, Union[str, None]]]:
    """Every distinct (series, transformation) the ingredient catalog actually collects.

    Read from the catalog rather than retyped so the probe cannot cover a different set from
    the one the system fetches.
    """
    from ingestion.catalog import INGREDIENTS

    seen, out = set(), []
    for ingredient in INGREDIENTS:
        if ingredient.kind != "fred":
            continue
        key = (ingredient.ref, ingredient.transformation)
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def merge(document: dict, records: list, today: date,
          order: list[tuple[str, Union[str, None]]]) -> dict:
    """Fold freshly probed ``records`` into an EXISTING probe document, in catalog order.

    WHY THIS EXISTS (WO-1.19). ``evidence/wo114_alfred_probe.json`` is the evidence behind
    ``ingestion.vintage``'s three sets, and WO-1.19 added exactly ONE new FRED pair to the
    catalog — ``DRTSCIS``, the small-firm leg of the same SLOOS question ``DRTSCILM`` asks of
    large ones. Re-probing all 24 pairs to measure one of them would overwrite 23 recorded
    measurements, and their dates, for nothing. What lands instead is an AMENDMENT: the same
    probe against the same endpoint, run for the new series alone, written into the file
    beside the others carrying its own probe date.

    Two conditions keep that honest rather than merely convenient.

    * THE HEADER IS NOT RESTAMPED. ``probed_utc`` stays the date the series already in the
      file were measured; each amended record carries a ``probed_utc`` of its own, and every
      amendment is listed under ``amendments``. So no reader can mistake one date for the
      other, which is precisely what a blanket restamp would make them do.
    * THE MEASUREMENT PARAMETERS MUST AGREE EXACTLY. Merging into a file measured with a
      different ``material_threshold``, ``compare_from`` or ``endpoint`` would file two
      incomparable measurements under one header, and ``ingestion.vintage.classify`` reads
      the whole list through one rule. A mismatch is refused, not reconciled.

    A record for a pair already present is REPLACED rather than duplicated: re-probing a
    series is a correction to the file, and ``tests/test_vintage_declaration.py`` fails on a
    pair recorded twice.
    """
    for key, measured in (("endpoint", BASE), ("compare_from", COMPARE_FROM),
                          ("material_threshold", MATERIAL)):
        if document.get(key) != measured:
            raise SystemExit(f"refusing to merge: the file was measured with {key}="
                             f"{document.get(key)!r}, this probe measures {measured!r}")
    stamped = [{**record, "probed_utc": today.isoformat()} for record in records]
    fresh = {(record["series"], record["transformation"]) for record in stamped}
    kept = [record for record in document["series"]
            if (record["series"], record["transformation"]) not in fresh]
    position = {pair: index for index, pair in enumerate(order)}
    # Stable sort on catalog position: the kept records are already in that order, so this
    # places each new one where the catalog puts it rather than at the end.
    document["series"] = sorted(
        kept + stamped,
        key=lambda record: position.get((record["series"], record["transformation"]), len(order)))
    document.setdefault("amendments", []).append({
        "probed_utc": today.isoformat(),
        "series": sorted(series for series, _ in fresh),
        "note": "probed by this script with --merge; the header's probed_utc is the date the "
                "series already in the file were measured and is deliberately not restamped",
    })
    return document


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="where to write the JSON record")
    parser.add_argument("--series", nargs="*", default=[], help="limit to these series ids")
    parser.add_argument("--trail-observation", default="2024-07-01",
                        help="the trail reads the series' latest observation on or before this date")
    parser.add_argument("--no-trail", action="store_true")
    parser.add_argument("--merge", action="store_true",
                        help="amend the document already at --out instead of replacing it")
    args = parser.parse_args(argv)

    today = date.today()
    order = fred_series_from_catalog()
    wanted = order
    if args.series:
        unknown = sorted(set(args.series) - {series for series, _ in order})
        if unknown:
            raise SystemExit(f"--series names what the catalog does not collect: {unknown}")
        wanted = [(s, t) for s, t in order if s in set(args.series)]
    records = []
    for index, (series, transformation) in enumerate(wanted, 1):
        print(f"[{index}/{len(wanted)}] {series}{'/' + transformation if transformation else ''}",
              flush=True)
        record = probe_one(series, transformation, today,
                           None if args.no_trail else args.trail_observation)
        records.append(record)
        depth = record.get("vintage_depth", {}).get("earliest")
        rev = record.get("revision", {})
        print(f"    earliest vintage {depth}  shared={rev.get('shared_observations')} "
              f"differing={rev.get('differing')} material={rev.get('differing_materially')} "
              f"distinct_in_trail={record.get('trail', {}).get('distinct_values')}", flush=True)
        time.sleep(PACE)
    if args.merge:
        with open(args.out, encoding="utf-8") as handle:
            document = merge(json.load(handle), records, today, order)
    else:
        document = {"probed_utc": today.isoformat(), "endpoint": BASE,
                    "credential": "none (keyless)", "compare_from": COMPARE_FROM,
                    "material_threshold": MATERIAL, "series": records}
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"-- {len(records)} series {'merged into' if args.merge else 'written to'} "
          f"{args.out}, which now records {len(document['series'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
