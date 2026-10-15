#!/usr/bin/env python3
"""THE PLAIN-FRED WINDOW PROBE — does ``fredgraph.csv``'s ``cosd``/``coed`` CLAMP, REFUSE, or get IGNORED?

    python3 tools/probe/fred_graph_window_probe.py --out evidence/<file>.json

WHY THIS EXISTS (WO-1.15). ``ingestion/backfill.py`` records the declared limit in its own
docstring: ``FredAdapter`` asks for the series' WHOLE current body and
``parse_fred_csv`` reads its LATEST observation, so for the six pairs
``ingestion.vintage.REVISION_STABLE`` measured stable, a backfill of a date years back gets
a perfectly good reading of the WRONG period. ``backfill_range`` gates on that and reports
``FAILED_DATE_NOT_ANSWERED`` rather than storing it, so nothing wrong is stored today — but
those six series cannot be backfilled for history at all. The fix the docstring names is
per-date selection out of that body: a ``cosd``/``coed`` window on the FRED request.

THE THING THAT MUST NOT BE ASSUMED. That window is the same technique
``ingestion.adapters.AlfredVintageAdapter._url_for`` already uses — but it was measured
against ``alfred.stlouisfed.org`` (``tools/probe/alfred_vintage_probe.py``,
``evidence/wo114_alfred_probe.json``, 2026-10-13), and what it measured there is that ALFRED
does **not refuse** an out-of-range window, it silently **CLAMPS** it. That is why
``parse_alfred_csv`` matches the observation by EXACT DATE and never reads "the only row".
Whether plain ``fred.stlouisfed.org/graph/fredgraph.csv`` behaves the same way — clamps,
refuses, returns an empty body, or ignores the window and hands back the whole series — has
never been measured. Guessing it is exactly how a backfill forges a historical reading out
of today's value, which is the one thing WO-1.14's vintage work exists to stop. So this
file ASKS, and writes down the answer.

IT IS A PROBE, NOT A GATE, AND IT WRITES NO ADAPTER CODE. It opens sockets to a third party,
so its verdict is not reproducible offline and can never be a register check (CD-PL-F48).
It records what the server said; a human reads that and decides what the adapter does. This
round deliberately changes nothing under ``ingestion/``.

WHAT IT ASKS, PER SERIES
------------------------
``baseline`` — the UNWINDOWED request, exactly the URL ``FredAdapter._url`` builds today.
Establishes the series' real span, so every "impossible" date below is DERIVED from what the
server says the series holds rather than typed in from memory.

``Q1`` — a one-day window and a multi-day window on a date 5+ years back. Does the body hold
only that date's row, more rows, the whole series, or an error? The multi-day case is asked
as well as the single-day one because a single row proves the window was applied only if a
wider window demonstrably returns wider; one row could otherwise be a series that happens to
have one row anywhere you look.

``Q2`` — a window wholly BEFORE the series' first observation, and a window SPANNING that
first observation from outside it. The pair separates the three candidate behaviours that
look alike from one side: clamp-to-start answers the spanning case with the real start,
empty answers it with no rows, and a refusal answers neither.

``Q3`` — ``coed`` before ``cosd``. A malformed window's failure/clamp shape, so it is known
rather than guessed when a caller computes a window wrong.

``Q4`` — the header line of every one of the above, recorded literally, against the
``observation_date,<column>`` that ``parse_fred_csv`` already requires. ALFRED's header
carries a ``_<YYYYMMDD>`` vintage suffix and ``parse_alfred_csv`` reads the served vintage
back out of it; whether a window changes plain FRED's header at all is a separate question
and is asked as one.

``EXTRA`` — a window on a date INSIDE the series' span that the series does not have (a
weekend or holiday for a business-daily series), DERIVED from the multi-day body above
rather than assumed, and then the same window widened to cover the whole gap. Not one of the
four questions, but it is the case that decides whether a future ``parse_fred_csv`` may trust
"the only row in the window": if a gap date answers with a neighbouring row instead of
nothing, "the only row" is a forgery waiting to happen and exact-date matching is mandatory.
The widened version asks whether whatever the single day answered is the endpoint's general
shape for "this window matches no observation" or a one-off. Two more GETs on the same
read-only door.

BODIES ARE RECORDED VERBATIM where they fit under :data:`VERBATIM_CAP`, which is every
windowed case. The unwindowed baseline is tens of thousands of rows, so it is recorded as its
literal header, first and last lines, and an exact row count, with ``truncated`` set — the
one place this file stores a measurement of a body rather than the body.
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

HOST = "fred.stlouisfed.org"
#: FRED's keyless graph CSV — the EXACT door ``ingestion.adapters.FredAdapter`` uses, same
#: host, same path, no API key. ``api.stlouisfed.org`` is never contacted and no credential
#: exists anywhere in this file.
BASE = f"https://{HOST}/graph/fredgraph.csv"
#: Courtesy gap between requests to a public endpoint nobody is charging us for.
PACE = 0.7
#: Bodies at or under this are stored verbatim; longer ones are stored as head/tail plus an
#: exact row count, flagged ``truncated``.
VERBATIM_CAP = 20_000
#: Lines kept at each end of a truncated body.
HEAD_TAIL = 4
#: How far before a series' first observation the "impossible" window is placed. Ten years is
#: not a boundary-adjacent off-by-one; it is unambiguously outside.
IMPOSSIBLE_YEARS = 10


def _url(series: str, transformation: Union[str, None],
         start: Union[str, None] = None, end: Union[str, None] = None) -> str:
    """The request, built the way ``FredAdapter._url`` builds it plus the window under test."""
    parts = [f"id={series}"]
    if transformation:
        parts.append(f"transformation={transformation}")
    if start is not None:
        parts.append(f"cosd={start}")
    if end is not None:
        parts.append(f"coed={end}")
    return BASE + "?" + "&".join(parts)


def _fetch(url: str, timeout: float = 30.0) -> dict:
    """status, content type and the literal body. An HTTP error is an ANSWER, not a failure.

    A 400/404 here is one of the outcomes the probe is looking for — "FRED refuses this
    window" — so it is recorded with its body rather than raised. Only a transport failure,
    which is an absence of an answer, is reported as an error.
    """
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"http_status": response.status,
                    "content_type": response.headers.get("Content-Type"),
                    "body": response.read(16_000_000).decode("utf-8", "replace")}
    except urllib.error.HTTPError as failure:
        return {"http_status": failure.code,
                "content_type": failure.headers.get("Content-Type") if failure.headers else None,
                "http_error": True,
                "body": failure.read(200_000).decode("utf-8", "replace")}


def _shape(body: str) -> dict:
    """What the body IS, measured: its literal header, its rows, its span.

    Nothing here interprets. ``observation_dates`` is the first cell of every non-blank line
    after the header, in the order the server sent them, so a body that came back out of
    order or clamped to a span nobody asked for says so in the record itself.
    """
    lines = body.splitlines()
    header = lines[0] if lines else ""
    rows = [line for line in lines[1:] if line.strip()]
    dates = [line.split(",")[0] for line in rows]
    out: dict = {
        "header_line": header,
        "header_cells": header.split(",") if header else [],
        "row_count": len(rows),
        "first_row": rows[0] if rows else None,
        "last_row": rows[-1] if rows else None,
        "span": [dates[0], dates[-1]] if dates else None,
        "body_bytes": len(body),
    }
    if len(body) <= VERBATIM_CAP:
        out["body_verbatim"] = body
        out["observation_dates"] = dates
        out["truncated"] = False
    else:
        out["body_head_lines"] = lines[:HEAD_TAIL + 1]
        out["body_tail_lines"] = lines[-HEAD_TAIL:]
        out["truncated"] = True
    # An error page states its own error in its title. Kept because the alternative is a
    # record saying only "28935 bytes of something" about the one case that refused.
    titles = [line.strip() for line in lines if "<title" in line.lower()]
    if titles:
        out["html_title_lines"] = titles[:3]
    return out


def _case(name: str, question: str, asks: str, series: str,
          transformation: Union[str, None], start: Union[str, None],
          end: Union[str, None]) -> dict:
    """One request, one record. ``asks`` states in words what this case is trying to tell apart."""
    url = _url(series, transformation, start, end)
    record: dict = {"case": name, "question": question, "asks": asks,
                    "cosd": start, "coed": end, "url": url}
    try:
        answer = _fetch(url)
    except (urllib.error.URLError, OSError) as failure:
        record["transport_error"] = f"{type(failure).__name__}: {failure}"
        return record
    record.update({k: v for k, v in answer.items() if k != "body"})
    record["observed"] = _shape(answer["body"])
    return record


def _column(series: str, transformation: Union[str, None]) -> str:
    """The value-column header ``parse_fred_csv`` demands, built by its own rule."""
    return series + (f"_{transformation.upper()}" if transformation else "")


def _gap_run(window_case: dict, start: str, end: str) -> Union[tuple, None]:
    """The first RUN of consecutive calendar dates inside ``[start, end]`` with no row.

    Derived from the multi-day body this run actually received, never assumed: a business-daily
    series skips weekends and holidays, a 7-day series skips nothing, and which one a given id
    is is not this file's to declare. The run's two ends are returned, not just its first day,
    so a window can be placed WHOLLY inside the gap as well as on one day of it — the two ask
    different things and the second is the general "window matches no observation" case.
    """
    observed = window_case.get("observed", {})
    if "observation_dates" not in observed:
        return None  # the body was truncated or absent: no derivation is available
    present = set(observed["observation_dates"])
    cursor, stop = date.fromisoformat(start), date.fromisoformat(end)
    while cursor <= stop and cursor.isoformat() in present:
        cursor += timedelta(days=1)
    if cursor > stop:
        return None
    first = cursor
    while cursor + timedelta(days=1) <= stop and (cursor + timedelta(days=1)).isoformat() not in present:
        cursor += timedelta(days=1)
    return first.isoformat(), cursor.isoformat()


def probe_one(series: str, transformation: Union[str, None], target: str,
              range_days: int) -> dict:
    """Every case for one series, in order, each pacing itself."""
    record: dict = {"series": series, "transformation": transformation,
                    "column_parse_fred_csv_expects": _column(series, transformation),
                    "cases": []}

    def add(*args) -> dict:
        case = _case(*args)
        record["cases"].append(case)
        print(f"    {case['case']:<28} status={case.get('http_status')} "
              f"rows={case.get('observed', {}).get('row_count')} "
              f"span={case.get('observed', {}).get('span')} "
              f"header={case.get('observed', {}).get('header_line')!r}", flush=True)
        time.sleep(PACE)
        return case

    baseline = add("baseline_no_window", "baseline",
                   "the URL FredAdapter builds today; establishes the series' REAL span so "
                   "the impossible dates below are derived rather than typed",
                   series, transformation, None, None)
    if baseline.get("observed", {}).get("span") is None:
        record["note"] = "the unwindowed request returned no rows; nothing below is derivable"
        return record
    series_start, series_end = baseline["observed"]["span"]
    record["series_span_per_server"] = [series_start, series_end]

    window_end = (date.fromisoformat(target) + timedelta(days=range_days - 1)).isoformat()
    add("q1_window_one_day", "Q1",
        "a one-day window 5+ years back: only that date's row, more rows, the whole series, "
        "or an error?",
        series, transformation, target, target)
    multi = add("q1_window_multi_day", "Q1",
                f"the same window widened to {range_days} days: proves the window is APPLIED "
                "rather than a series that returns one row whatever you ask",
                series, transformation, target, window_end)

    # Days, not ``replace(year=...)``: a series whose first observation is a 29 February has
    # no such date ten years earlier and the replace would raise rather than probe.
    impossible = (date.fromisoformat(series_start)
                  - timedelta(days=round(IMPOSSIBLE_YEARS * 365.25))).isoformat()
    record["impossible_window_derivation"] = (
        f"series_start {series_start} per the baseline body, minus {IMPOSSIBLE_YEARS} years "
        f"= {impossible}")
    add("q2_window_before_series_start", "Q2",
        "a window WHOLLY before the series' first observation: clamp, empty, error, or the "
        "whole series?",
        series, transformation, impossible, impossible)
    add("q2_window_spanning_series_start", "Q2",
        "a window opening 10 years before the first observation and closing just after it: "
        "clamp-to-start answers with the real start, empty answers with no rows, a refusal "
        "answers with neither — the three cannot be told apart from the case above alone",
        series, transformation, impossible,
        (date.fromisoformat(series_start) + timedelta(days=5)).isoformat())

    add("q3_window_reversed", "Q3",
        "coed BEFORE cosd: the failure/clamp shape of a malformed window, measured rather "
        "than guessed",
        series, transformation, target,
        (date.fromisoformat(target) - timedelta(days=5)).isoformat())

    run = _gap_run(multi, target, window_end)
    if run is None and "observation_dates" in multi.get("observed", {}):
        record["gap_date_note"] = (
            f"every calendar day in {target}..{window_end} came back with a row, so this "
            "series has no gap to probe in that span")
    elif run is None:
        record["gap_date_note"] = (
            "the multi-day body carried no readable date list, so no gap date could be derived")
    else:
        gap_first, gap_last = run
        record["gap_date_derivation"] = (
            f"{gap_first}..{gap_last} is inside the series' span but absent from the "
            f"{range_days}-day body above")
        add("extra_window_on_gap_date", "EXTRA",
            "a one-day window on a date the series does NOT have: nothing, or a NEIGHBOURING "
            "row? This is what decides whether 'the only row in the window' is safe to trust "
            "or whether exact-date matching is mandatory",
            series, transformation, gap_first, gap_first)
        if gap_last != gap_first:
            add("extra_window_wholly_inside_gap", "EXTRA",
                "the same question generalised: a MULTI-day window that matches no "
                "observation at all. Confirms whether the single-day answer above is the "
                "endpoint's shape for an empty window or a one-off",
                series, transformation, gap_first, gap_last)
    return record


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="where to write the JSON record")
    parser.add_argument("--series", nargs="*",
                        default=["DFF", "T5YIE"],
                        help="series ids to probe; the default is one long-history and one "
                             "short-history pair out of ingestion.vintage.REVISION_STABLE")
    parser.add_argument("--target", default="2015-06-15",
                        help="the 5+-years-back date the Q1 window is placed on")
    parser.add_argument("--range-days", type=int, default=9,
                        help="width of the Q1 multi-day window, in calendar days")
    args = parser.parse_args(argv)

    records = []
    for index, series in enumerate(args.series, 1):
        print(f"[{index}/{len(args.series)}] {series}", flush=True)
        records.append(probe_one(series, None, args.target, args.range_days))

    document = {
        "probed_utc": date.today().isoformat(),
        "endpoint": BASE,
        "credential": "none (keyless)",
        "target_date": args.target,
        "range_days": args.range_days,
        "why": ("WO-1.15: whether plain fredgraph.csv CLAMPS an out-of-range cosd/coed window "
                "the way alfredgraph.csv was measured to (evidence/wo114_alfred_probe.json, "
                "2026-10-13), refuses it, ignores it, or answers empty"),
        "series": records,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"-- {len(records)} series written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
