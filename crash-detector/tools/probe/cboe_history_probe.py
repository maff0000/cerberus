#!/usr/bin/env python3
"""THE CBOE HISTORY PROBE — is there ANY date window on ``*_History.csv``, or only the whole past?

    PYTHONPATH=src:. python3 tools/probe/cboe_history_probe.py --out evidence/<file>.json

WHY THIS EXISTS (WO-1.16). ``ingestion.adapters.CboeAdapter._url`` asks for
``https://cdn-api.cboe.com/api/global/us_indices/daily_prices/{index}_History.csv`` with NO
date parameter of any kind, and ``parse_cboe_csv`` then reads the LAST row of whatever came
back — "latest row" by POSITION, exactly the read WO-1.15 found unsafe in ``parse_fred_csv``.
Two separate questions follow and they have different answers, so this file asks them
separately:

    Q1  Is there a windowing mechanism at all? A query parameter that narrows the body, the
        way ``cosd``/``coed`` narrows ``fredgraph.csv`` and ``period1``/``period2`` narrows
        Yahoo's chart? Or is this one static artefact, the whole history, every time?

    Q2  Whatever the answer to Q1, is "the last row" already unsafe for a HISTORICAL read?
        That question does not wait on Q1: if the body is the whole history and the parser
        reads its last row, then a per-date backfill built on today's parser would answer any
        date you like with today's close. Measured, not asserted — the probe finds the target
        date's REAL row inside the body and puts it next to what ``parse_cboe_csv`` actually
        returns for the same body.

WHY Q1 CANNOT BE ANSWERED BY READING THE URL. An endpoint that IGNORES an unknown parameter
and an endpoint that HONOURS it are indistinguishable from the caller's side until the two
bodies are compared — and "it 200s" is not evidence of either. So every candidate parameter
here is scored by comparing its body's SHA-256 against the bare URL's, and the set includes
two controls: ``cosd``/``coed`` (FRED's parameter names, meaningless here) and a deliberately
nonsense parameter. If those two controls come back byte-identical to the bare URL, then an
identical body for a plausible-looking parameter means IGNORED and nothing else — which is the
inference that would otherwise have to be guessed. Public write-ups of this file (the
``datasets/finance-vix`` pipeline, read 2026-10-15) fetch it with no parameters at all and
filter client-side, which is a hint about what exists and not a measurement of it.

IT IS A PROBE, NOT A GATE, AND IT WRITES NO ADAPTER CODE. It opens sockets to a third party,
so its verdict is not reproducible offline and can never be a register check (CD-PL-F48). It
records what the server said; a human reads that and decides what the adapter does. This round
deliberately changes nothing under ``ingestion/``.

SCOPE. The three in-scope CBOE ingredients from ``ingestion/catalog.py`` — ``cboe.VIX`` and
``cboe.VIX3M`` (``column="CLOSE"``) and ``cboe.SKEW`` (``column="SKEW"``) — all of which are
indices with no dividends to adjust for, so none of the ``adjclose`` problem ``PID.md``'s
WO-1.16 correction (2026-10-15) describes applies to any of them. ``VIX`` carries the full
question set; the other two are asked the shape questions only, because what differs between
them is the COLUMN the catalog names and the span the server holds, and both of those have to
be seen rather than assumed for an exact-date read to be possible across all three.

BODIES ARE MEASURED, NOT DUMPED, and the distinction is deliberate. This file is ~470 KB of
CSV and three copies of it would make the evidence unreadable. So each response is recorded as
its literal header line, its exact row count, its span, its first and last
:data:`HEAD_TAIL` rows verbatim, its byte count and its SHA-256 — plus, for the baseline, a
VERBATIM excerpt of every row in the target month, which is the part a per-date read would
have to find and is therefore the part worth keeping in full.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from typing import Union

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
# ``src`` AND the repo root, in pyproject's own order (``pythonpath = ["src", "."]``): the
# supported import route is PYTHONPATH=src:., and this file is runnable without it.
sys.path[:0] = [os.path.join(_ROOT, "src"), _ROOT]

try:  # read-only: the probe asks the REAL parser what it makes of the body it was handed
    from ingestion.adapters import parse_cboe_csv
except ImportError:  # pragma: no cover - the measurements below still stand alone
    parse_cboe_csv = None  # type: ignore[assignment]

HOST = "cdn-api.cboe.com"
#: The EXACT door ``ingestion.adapters.CboeAdapter`` uses: same host, same path shape, no
#: credential (this file takes none and none exists here).
BASE = f"https://{HOST}/api/global/us_indices/daily_prices/"
#: Courtesy gap between requests to a public CDN nobody is charging us for. Each GET here is
#: ~470 KB, so the pace is wider than the other probes'.
PACE = 1.5
#: Rows kept verbatim at each end of every recorded body.
HEAD_TAIL = 4
#: The 5+-years-back date the windowing attempts name, and whose month is kept verbatim out of
#: the baseline body. A date inside every index's span, well clear of both ends.
TARGET = "2015-06-15"

#: Candidate date-window parameters, each as the query string to append to the bare URL.
#: ``_control`` cases are the ones whose answer licenses the inference about all the others:
#: if a parameter the endpoint cannot possibly understand returns the identical body, then an
#: identical body means IGNORED rather than HONOURED-and-coincidentally-whole.
CANDIDATE_PARAMS = [
    {"name": "dt", "query": f"dt={TARGET}",
     "why": "a single-date parameter, the shape a CDN file server is likeliest to accept"},
    {"name": "date", "query": f"date={TARGET}",
     "why": "the same idea under the most obvious spelling"},
    {"name": "startDate_endDate", "query": f"startDate={TARGET}&endDate={TARGET}",
     "why": "Cboe's own web tooling uses camelCase date bounds elsewhere on the site"},
    {"name": "start_end", "query": f"start={TARGET}&end={TARGET}",
     "why": "the terse spelling of the same bounds"},
    {"name": "from_to", "query": f"from={TARGET}&to={TARGET}",
     "why": "the third common spelling of the same bounds"},
    {"name": "start_date_end_date", "query": f"start_date={TARGET}&end_date={TARGET}",
     "why": "the snake_case spelling of the same bounds"},
    {"name": "control_fred_param_names", "query": f"cosd={TARGET}&coed={TARGET}", "control": True,
     "why": "CONTROL: FRED's parameter names, which this endpoint has no reason to know. An "
            "identical body here is what makes 'identical body' mean IGNORED above"},
    {"name": "control_nonsense_param", "query": "cerberus_probe_not_a_real_param=1", "control": True,
     "why": "CONTROL: a parameter that certainly does not exist. Separates 'unknown parameters "
            "are ignored' from 'unknown parameters are refused'"},
]

#: Headers worth recording verbatim from the baseline response: whether the CDN advertises
#: byte ranges, how it caches, and what it claims the artefact's identity and age are. Not a
#: date window, but the question "does anything in the response hint at one" is answered by
#: looking rather than by assuming it does not.
HEADERS_OF_INTEREST = ("Content-Type", "Content-Length", "Content-Encoding", "ETag",
                       "Last-Modified", "Cache-Control", "Age", "Accept-Ranges", "Vary",
                       "Access-Control-Allow-Origin", "Server", "X-Cache", "Link")


def _url(index: str, query: Union[str, None] = None) -> str:
    """The request, built the way ``CboeAdapter._url`` builds it plus the parameter under test."""
    url = f"{BASE}{index}_History.csv"
    return f"{url}?{query}" if query else url


def _fetch(url: str, timeout: float = 60.0) -> dict:
    """status, headers and the literal body. An HTTP error is an ANSWER, not a failure.

    A 400/403/404 here is one of the outcomes the probe is looking for — "the CDN refuses this
    parameter" — so it is recorded with its body rather than raised. Only a transport failure,
    which is an absence of an answer, is reported as an error.
    """
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            headers = response.headers
            return {"http_status": response.status,
                    "headers": {k: headers.get(k) for k in HEADERS_OF_INTEREST if headers.get(k)},
                    "body": response.read(64_000_000).decode("utf-8", "replace")}
    except urllib.error.HTTPError as failure:
        headers = failure.headers
        return {"http_status": failure.code,
                "http_error": True,
                "headers": ({k: headers.get(k) for k in HEADERS_OF_INTEREST if headers.get(k)}
                            if headers else {}),
                "body": failure.read(400_000).decode("utf-8", "replace")}


def _rows(body: str) -> tuple:
    """``(header_line, [line, ...])`` split the way ``parse_cboe_csv`` splits it."""
    lines = body.strip().splitlines()
    return (lines[0] if lines else ""), [line for line in lines[1:] if line.strip()]


def _iso(cell: str) -> Union[str, None]:
    """``MM/DD/YYYY`` → ISO, by ``parse_cboe_csv``'s own rule; ``None`` if it does not parse."""
    try:
        return datetime.strptime(cell, "%m/%d/%Y").date().isoformat()
    except ValueError:
        return None


def _shape(body: str, column: Union[str, None], keep_month: Union[str, None] = None) -> dict:
    """What the body IS, measured. Nothing here interprets; it records.

    ``date_format_parse_cboe_csv_can_read`` and ``column_catalog_names_present`` are the two
    structural preconditions an exact-date read would need, asked of the real body rather than
    carried over from the parser's docstring. ``strictly_ascending_by_date`` is asked because
    ``parse_cboe_csv`` reads the LAST row and calls it the latest: that is only true of a body
    sorted oldest-first, which is an assumption until it is measured.
    """
    header, rows = _rows(body)
    cells = header.split(",") if header else []
    out: dict = {
        "body_bytes": len(body),
        "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "header_line": header,
        "header_cells": cells,
        "row_count": len(rows),
        "rows_head": rows[:HEAD_TAIL],
        "rows_tail": rows[-HEAD_TAIL:],
    }
    if column is not None:
        out["column_catalog_names"] = column
        out["column_catalog_names_present"] = column in cells
    first_dates = [_iso(line.split(",")[0]) for line in rows[:HEAD_TAIL]]
    last_dates = [_iso(line.split(",")[0]) for line in rows[-HEAD_TAIL:]]
    out["date_format_parse_cboe_csv_can_read"] = all(d is not None for d in first_dates + last_dates)
    dates = [_iso(line.split(",")[0]) for line in rows]
    readable = [d for d in dates if d is not None]
    out["unreadable_date_cells"] = len(dates) - len(readable)
    out["span"] = [readable[0], readable[-1]] if readable else None
    out["strictly_ascending_by_date"] = all(a < b for a, b in zip(readable, readable[1:]))
    if keep_month and readable:
        # The rows a per-date read would have to FIND, kept verbatim: this is the one part of a
        # 470 KB body that is worth storing in full, because it is the part the fix depends on.
        wanted = [line for line, iso in zip(rows, dates) if iso and iso.startswith(keep_month)]
        out["rows_for_month_verbatim"] = {"month": keep_month, "rows": wanted}
    return out


def _target_row(body: str, target: str, column: Union[str, None]) -> dict:
    """The body's own row for ``target``, found by EXACT date match — the per-date read, by hand.

    This is the measurement Q2 turns on. It is deliberately NOT done with ``parse_cboe_csv``:
    the point is to have an independent reading of the target date to put NEXT TO what that
    parser returns for the same body, so "the last row is not the target date's row" is a
    comparison in the record rather than a claim in prose.
    """
    header, rows = _rows(body)
    cells = header.split(",") if header else []
    index = cells.index(column) if column in cells else None
    for line in rows:
        parts = line.split(",")
        if _iso(parts[0]) == target:
            return {"found": True, "row_verbatim": line,
                    "value_in_catalog_column": parts[index] if index is not None
                                               and index < len(parts) else None}
    return {"found": False, "row_verbatim": None, "value_in_catalog_column": None}


def probe_one(index: str, column: str, full: bool) -> dict:
    """Every case for one index, in order, each pacing itself."""
    record: dict = {"index": index, "catalog_column": column,
                    "adapter_url_today": _url(index), "cases": []}

    def add(name: str, question: str, asks: str, query: Union[str, None],
            keep_month: Union[str, None] = None) -> dict:
        url = _url(index, query)
        case: dict = {"case": name, "question": question, "asks": asks,
                      "query_appended": query, "url": url}
        try:
            answer = _fetch(url)
        except (urllib.error.URLError, OSError) as failure:
            case["transport_error"] = f"{type(failure).__name__}: {failure}"
        else:
            case["http_status"] = answer["http_status"]
            case["response_headers"] = answer["headers"]
            if answer.get("http_error"):
                case["http_error"] = True
            case["observed"] = _shape(answer["body"], column, keep_month)
            case["_body"] = answer["body"]  # stripped before the record is written
        record["cases"].append(case)
        observed = case.get("observed", {})
        print(f"    {case['case']:<30} status={case.get('http_status')} "
              f"rows={observed.get('row_count')} span={observed.get('span')} "
              f"bytes={observed.get('body_bytes')} sha={str(observed.get('sha256'))[:12]}",
              flush=True)
        time.sleep(PACE)
        return case

    baseline = add("baseline_bare_url_as_adapter_builds_it", "Q1",
                   "the URL CboeAdapter._url builds TODAY, unchanged: how big is the whole "
                   "history, how far back does it go, and is it ordered oldest-first the way "
                   "parse_cboe_csv's read-the-last-row assumes",
                   None, keep_month=TARGET[:7])
    baseline_body = baseline.get("_body")
    baseline_sha = baseline.get("observed", {}).get("sha256")

    if full and baseline_body is not None:
        for candidate in CANDIDATE_PARAMS:
            case = add(f"q1_param_{candidate['name']}", "Q1", candidate["why"],
                       candidate["query"])
            case["is_control"] = bool(candidate.get("control"))
            observed = case.get("observed", {})
            # The whole point of the comparison, recorded as a measurement rather than left
            # for a reader to do by eye across two 470 KB bodies.
            case["identical_to_baseline_body"] = (
                observed.get("sha256") == baseline_sha if baseline_sha else None)
            case["row_count_delta_vs_baseline"] = (
                None if observed.get("row_count") is None
                else observed["row_count"] - baseline["observed"]["row_count"])

    if baseline_body is not None:
        hand_read = _target_row(baseline_body, TARGET, column)
        parser_says = (parse_cboe_csv(baseline_body, column, "index")
                       if parse_cboe_csv is not None else None)
        record["q2_last_row_safety"] = {
            "asks": ("if the body is always the whole history and parse_cboe_csv reads its LAST "
                     "row, what would a per-date backfill of " + TARGET + " get? The hand read "
                     "finds that date's real row by exact match; the parser is handed the same "
                     "body. If the two disagree, 'last row' is unsafe for a historical read in "
                     "exactly the way parse_fred_csv's was (WO-1.15)"),
            "target_date": TARGET,
            "hand_read_by_exact_date_match": hand_read,
            "parse_cboe_csv_on_the_same_body": parser_says,
            "parser_observation_date": (parser_says or {}).get("observation_date"),
            "parser_answers_the_target_date": (
                (parser_says or {}).get("observation_date") == TARGET),
            "body_span": record["cases"][0]["observed"]["span"],
        }
    return record


#: The in-scope CBOE ingredients. ``full`` marks the one carrying the parameter hunt; the other
#: two are asked the shape questions, because the column the catalog names and the span the
#: server holds differ per index and both must be seen for a per-date read to be possible.
INDICES = [
    {"index": "VIX", "column": "CLOSE", "full": True},
    {"index": "VIX3M", "column": "CLOSE", "full": False},
    {"index": "SKEW", "column": "SKEW", "full": False},
]


def _strip_bodies(record: dict) -> dict:
    """Drop the carried full bodies: they are MEASURED in ``observed``, never dumped."""
    for case in record.get("cases", []):
        case.pop("_body", None)
    return record


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="where to write the JSON record")
    parser.add_argument("--only", nargs="*", default=None,
                        help="restrict to these indices (default: all three in INDICES)")
    args = parser.parse_args(argv)

    wanted = [i for i in INDICES if args.only is None or i["index"] in args.only]
    records = []
    for position, spec in enumerate(wanted, 1):
        print(f"[{position}/{len(wanted)}] {spec['index']}"
              f"{' (full question set)' if spec['full'] else ' (shape only)'}", flush=True)
        records.append(_strip_bodies(probe_one(spec["index"], spec["column"], spec["full"])))

    document = {
        "probed_utc": date.today().isoformat(),
        "endpoint": BASE,
        "credential": "none (this endpoint takes none)",
        "user_agent": "python-urllib default (CboeAdapter sends no custom agent either)",
        "parser_imported": parse_cboe_csv is not None,
        "target_date": TARGET,
        "bodies_note": ("each body is ~470 KB; recorded as header line, exact row count, span, "
                        "first/last rows verbatim, byte count and SHA-256, plus the target "
                        "month's rows verbatim out of the baseline"),
        "why": ("WO-1.16: whether cdn-api.cboe.com's *_History.csv supports ANY date-windowing "
                "parameter (Q1) and, independently of that, whether parse_cboe_csv's "
                "read-the-last-row already carries the same risk parse_fred_csv's did — a "
                "historical date answered with today's close (Q2)"),
        "indices": records,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"-- {len(records)} indices written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
