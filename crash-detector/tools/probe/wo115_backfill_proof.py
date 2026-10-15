#!/usr/bin/env python3
"""THE PROOF RUN, STABLE BRANCH — ``ingestion.backfill`` against the REAL network and a REAL store.

    PYTHONPATH=src:. python3 tools/probe/wo115_backfill_proof.py \
        --db /tmp/wo115_backfill_proof.sqlite --source fred.DFF \
        --out evidence/wo115_backfill_proof.json

WHY THIS EXISTS EVEN THOUGH ``tests/test_wo114_backfill.py`` IS GREEN. Those tests substitute
the WIRE and nothing else — real driver, real adapter construction, real parser, real store,
a callable where the socket should be. Their fake (``_Fred``) was built FROM a measurement of
the live endpoint (``tools/probe/fred_graph_window_probe.py``, 2026-10-15), so it is evidence
— but once-removed evidence, and a transport fake answers what it was told to answer. It
cannot answer the one question an operator about to backfill 25 years of history actually has:
does ``backfill_range`` recover the RIGHT historical value when it reaches
``fred.stlouisfed.org`` for real, today? This runs it for real and writes down what came back,
the same standing and for the same reason as ``tools/probe/wo114_backfill_proof.py`` — which
proved the VINTAGE branch this way. This is the STABLE branch's equivalent.

IT IS A PROBE, NOT A GATE. It opens sockets to a third party, so it is not reproducible
offline and is not a register check (CD-PL-F48). It writes a JSON record a human reads.

THE CROSS-CHECK IS WHAT MAKES IT A PROOF AND NOT PLUMBING
    A run that only reported what the driver stored would prove the driver can write a row.
    So every stored value is checked against the SAME value obtained a SECOND way that does
    not go through the new per-date path at all: ONE extra GET of the UNWINDOWED body — the
    whole series, 26,000-odd rows, the URL shape ``FredAdapter`` builds when
    ``observation_date`` is ``None`` — read off BY HAND in this file (:func:`read_by_hand`),
    outside the adapter and outside :func:`~ingestion.adapters.parse_fred_csv_for_date`. The
    two legs share the hostname and nothing else.

    If the windowed per-date fetch and the manual read of the full body disagree for the same
    date, that is a REAL DEFECT this file exists to surface, and the run says
    ``DISAGREEMENT`` and exits non-zero. It is not something to tune until it agrees.

    ``differs_from_series_latest_value`` is the second leg's other use. The dangerous failure
    on this branch is a parser reading the body BY POSITION — the last row — which answers a
    1999 backfill with this morning's rate. The full body's last row is recorded, so a stored
    historical value that differs from it demonstrably was not read off the end. For a date
    near today the two can legitimately coincide, and the field then proves nothing; it is
    reported per date rather than claimed for the range.

WHAT IS READ BACK, AND FROM WHERE
    The ``backfill`` section is the driver's own ``BackfillResult``. The ``stored`` section is
    read back OUT OF THE STORE on a read-only handle, so what is reported is what the
    database holds and not what the driver believed it wrote.

    The ``wire`` section is the request line ``http.client`` actually put on the socket for
    every GET the driver issued — host, method, target, status — recorded by an OBSERVER that
    delegates to the real method (:func:`install_wire_log`). It is what makes "the request was
    genuinely windowed, and was genuinely issued" a measurement rather than a claim: a
    ``cosd=D&coed=D`` in the recorded target came from this run's socket, not from a cache and
    not from a default.

THE NARROWER CLAIM — SAY IT PLAINLY. DFF is MEASURED STABLE from
:data:`~ingestion.vintage.STABILITY_MEASURED_FROM` (zero differences in 2,369 shared
observations from 1999 on: ``ingestion.vintage``), so there is NO "first published vs current"
gap to display the way ``wo114_backfill_proof.py``'s ``revision`` section displays GDP's. That
is not a weakness of this proof, it is the branch's premise: a measured-stable pair is
current-value-by-design and its reading is labelled ``current_only`` for exactly that reason.
So what is proven here is that **the WINDOW MECHANISM recovers the correct historical value
for a named past date** — the right period, matched by exact date, not today's row wearing a
past key. It is NOT a proof that the value is point-in-time-original. Nothing on this branch
claims that, and ``ingestion.vintage`` is where the ruling that it need not lives.

A DATE BEFORE THE MEASUREMENT'S LEFT EDGE IS INCLUDED ON PURPOSE. The default dates end at
1985-01-02, which ``backfill_range`` must REFUSE UNFETCHED. The full body has a value for it;
the record shows that value and shows that nothing was stored, which is the fail-closed floor
working on the real path instead of only in a test.

WHAT IT DOES NOT DO. It does not pick the database for you: ``--db`` is required and the
caller owns where a real write lands — a throwaway file, for this run, since these rows are a
proof and not the DEV store's data. It computes no dates: ``ingestion.backfill_dates`` states
the dating convention for the two cadences that ARE a formula and REFUSES a daily series'
publication calendar, correctly, so the dates are given explicitly and are DFF observations
per the server's own baseline body (``evidence/wo115_fred_window_probe.json``).
"""

from __future__ import annotations

import argparse
import http.client
import json
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from typing import Union

from ingestion.backfill import backfill_range
from ingestion.backfill_adapters import build_backfill_adapter
from ingestion.catalog import INGREDIENTS
from ingestion.store import SqliteStore
from ingestion.vintage import STABILITY_MEASURED_FROM, requires_original_vintage

#: The series' whole body, for the independent leg. Same shape as an unwindowed
#: ``FredAdapter`` request — no ``cosd``/``coed`` — built here so the second leg shares no
#: code with the first.
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"

#: Dates spanning different eras of one series, ascending. Each is an observation DFF really
#: has (it carries every calendar day from 1954-07-01: ``evidence/wo115_fred_window_probe.json``,
#: ``baseline_no_window``), and the last is before :data:`STABILITY_MEASURED_FROM` so the
#: refusal is exercised on the real path too.
DEFAULT_DATES = ("1985-01-02", "1999-01-01", "2005-06-15", "2026-09-15")

#: The unwindowed DFF body is ~424 KB. This is room for it without being unbounded.
MAX_BODY_BYTES = 16_000_000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# --- the wire observer ---------------------------------------------------------------- #

_WIRE_REQUEST = http.client.HTTPConnection.request
_WIRE_GETRESPONSE = http.client.HTTPConnection.getresponse


def install_wire_log() -> list:
    """Record what ``http.client`` puts on the socket, then DELEGATE to the real method.

    AN OBSERVER, NOT A SUBSTITUTE, and the distinction is the whole reason this is allowed
    in a proof whose point is that nothing is faked: both wrappers call the original and
    return exactly what it returned. No URL is rewritten, no body is supplied, no status is
    invented. What is gained is the one fact the driver's own result cannot carry — the
    literal request target that went out, which is how ``cosd=D&coed=D`` is shown to have
    been SENT rather than merely built.

    It is patched on ``HTTPConnection`` rather than on ``HTTPSConnection`` because the
    latter inherits both methods, so one patch covers plain and TLS alike.
    ``getresponse`` attributes its status to the most recent request, which is correct for
    the strictly sequential one-GET-at-a-time traffic this driver issues and would not be
    for a pooled or concurrent client.
    """
    wire: list = []

    def request(self, method, url, *args, **kwargs):  # noqa: ANN001 - mirrors http.client
        wire.append({
            "scheme": "https" if isinstance(self, http.client.HTTPSConnection) else "http",
            "host": self.host,
            "port": self.port,
            "method": method,
            "request_target": url,
            "requested_utc": _now(),
        })
        return _WIRE_REQUEST(self, method, url, *args, **kwargs)

    def getresponse(self):
        response = _WIRE_GETRESPONSE(self)
        if wire:
            wire[-1].update({
                "http_status": response.status,
                "content_type": response.headers.get("Content-Type"),
                "content_length": response.headers.get("Content-Length"),
                "answered_utc": _now(),
            })
        return response

    http.client.HTTPConnection.request = request
    http.client.HTTPConnection.getresponse = getresponse
    return wire


def remove_wire_log() -> None:
    """Put ``http.client`` back exactly as it was."""
    http.client.HTTPConnection.request = _WIRE_REQUEST
    http.client.HTTPConnection.getresponse = _WIRE_GETRESPONSE


def wire_url(record: dict) -> str:
    """The absolute URL a recorded request line stands for."""
    return f"{record['scheme']}://{record['host']}{record['request_target']}"


# --- the independent leg -------------------------------------------------------------- #


def full_body(series: str, timeout: float = 60.0) -> tuple:
    """ONE GET of the UNWINDOWED body. Plain ``urllib``, no adapter, no ``http_get``.

    Deliberately not ``ingestion.adapters.http_get`` either: the value of this leg is that
    it shares no line of code with the thing under test. The URL has the same SHAPE an
    unwindowed ``FredAdapter`` request has, and is built here from :data:`FRED_CSV`.
    """
    url = f"{FRED_CSV}?id={series}"
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(MAX_BODY_BYTES).decode("utf-8", "replace")
    return url, body


def read_by_hand(body: str, column: str) -> dict:
    """Split a ``fredgraph.csv`` body into its rows HERE, in this file, by hand.

    Not :func:`~ingestion.adapters.parse_fred_csv_for_date` and not
    :func:`~ingestion.adapters.parse_fred_csv`: a cross-check routed through the parser under
    test would check that the parser agrees with itself. The body being read is a different
    body too — the whole series rather than a one-day window — so the shape it reports
    (``row_count``, ``span``, ``last_row``) is itself evidence about which request answered.
    """
    lines = body.strip().splitlines()
    header = lines[0] if lines else ""
    rows = [line.split(",") for line in lines[1:] if line.strip()]
    return {
        "header_line": header,
        "header_is_expected": header == f"observation_date,{column}",
        "row_count": len(rows),
        "span": [rows[0][0], rows[-1][0]] if rows else None,
        "last_row": ",".join(rows[-1]) if rows else None,
        "by_date": {cells[0]: cells[1] for cells in rows if len(cells) == 2},
    }


def _number(raw: Union[str, None]) -> Union[float, None]:
    """A finite float, or ``None`` for FRED's ``.``/blank and for anything unreadable."""
    if raw is None or raw in ("", "."):
        return None
    try:
        return float(raw)
    except ValueError:
        return None


# --- the store, read back ------------------------------------------------------------- #


def stored_rows(db_path: str, source_id: str) -> list:
    """What the DATABASE holds for this source, vintage label included. Read-only handle."""
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = db.execute(
            "SELECT source_as_of_utc, payload, vintage, admitted_utc FROM raw_reading "
            "WHERE source_id=? ORDER BY source_as_of_utc", (source_id,)).fetchall()
    finally:
        db.close()
    return [{"source_as_of_utc": as_of, "payload": json.loads(payload), "vintage": vintage,
             "admitted_utc": admitted} for as_of, payload, vintage, admitted in rows]


def ingredient(source_id: str):
    for ing in INGREDIENTS:
        if ing.source_id == source_id:
            return ing
    raise SystemExit(f"no such ingredient: {source_id}")


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description="WO-1.15 real backfill proof run (stable branch)")
    parser.add_argument("--db", required=True, help="the SQLite store to write into (throwaway)")
    parser.add_argument("--source", default="fred.DFF", help="ingredient source_id")
    parser.add_argument("--dates", nargs="+", default=list(DEFAULT_DATES),
                        help="observation dates to backfill, as the SOURCE dates them")
    parser.add_argument("--out", required=True, help="where to write the JSON record")
    parser.add_argument("--pace", type=float, default=None, help="override courtesy pacing")
    args = parser.parse_args(argv)

    ing = ingredient(args.source)
    original = requires_original_vintage(ing.ref, ing.transformation)
    if original:
        raise SystemExit(
            f"{ing.source_id} routes to the VINTAGE branch (requires_original_vintage is True); "
            f"this file proves the STABLE one. tools/probe/wo114_backfill_proof.py is the other")
    dates = list(args.dates)
    column = ing.ref + (f"_{ing.transformation.upper()}" if ing.transformation else "")
    print(f"-- {ing.source_id}: {len(dates)} dates {dates[0]}..{dates[-1]}", flush=True)
    print(f"-- point-in-time required: {original}  (stability measured from "
          f"{STABILITY_MEASURED_FROM})", flush=True)
    # The adapter the driver WILL build for a date, recorded rather than assumed. Constructing
    # one fetches nothing; this is the routing decision made visible in the evidence.
    probe_adapter = build_backfill_adapter(ing, dates[-1], lambda: datetime.now(timezone.utc))
    print(f"-- adapter: {type(probe_adapter).__name__} ({probe_adapter.adapter_id})", flush=True)

    started = _now()
    kwargs = {} if args.pace is None else {"pace": args.pace}
    wire = install_wire_log()
    try:
        with SqliteStore(args.db) as store:
            result = backfill_range(ing, dates, store, lambda: datetime.now(timezone.utc), **kwargs)
    finally:
        remove_wire_log()
    finished = _now()
    print(f"-- {result.counts}", flush=True)
    for record in wire:
        print(f"   SENT {record['method']} {wire_url(record)} -> {record.get('http_status')}",
              flush=True)

    rows = stored_rows(args.db, ing.source_id)
    stored_by_date = {row["payload"].get("observation_date"): row for row in rows}

    cross_url, body = full_body(ing.ref)
    whole = read_by_hand(body, column)
    print(f"-- cross-check: {cross_url} -> {whole['row_count']} rows {whole['span']}", flush=True)
    latest_value = _number(whole["last_row"].split(",")[1]) if whole["last_row"] else None

    bucket_of = {}
    for date_text in result.admitted:
        bucket_of[date_text] = ("admitted", None)
    for date_text in result.skipped:
        bucket_of[date_text] = ("skipped", None)
    for date_text, why in result.refused:
        bucket_of[date_text] = ("refused", why)
    for date_text, why in result.failed:
        bucket_of[date_text] = ("failed", why)

    table = []
    for date_text in dates:
        bucket, why = bucket_of.get(date_text, ("UNACCOUNTED", None))
        row = stored_by_date.get(date_text)
        stored_value = row["payload"].get("value") if row else None
        independent_raw = whole["by_date"].get(date_text)
        independent_value = _number(independent_raw)
        sent = [r for r in wire if f"cosd={date_text}&coed={date_text}" in r["request_target"]]
        entry = {
            "observation_date": date_text,
            "bucket": bucket,
            "class": why,
            "stored_value": stored_value,
            "stored_source_as_of_utc": row["source_as_of_utc"] if row else None,
            "vintage_label": row["vintage"] if row else None,
            "independent_value": independent_value,
            "independent_raw_cell": independent_raw,
            "independent_source": "unwindowed full body, read by hand in this file",
            "windowed_request_url": wire_url(sent[0]) if sent else None,
            "windowed_request_sent": bool(sent),
            "windowed_http_status": sent[0].get("http_status") if sent else None,
            # 37 bytes of CSV against the unwindowed body's 424 KB is the window being
            # HONOURED, measured off the response rather than inferred from the request.
            "windowed_response_content_length": sent[0].get("content_length") if sent else None,
        }
        if bucket == "admitted" and stored_value is not None and independent_value is not None:
            entry["agree"] = stored_value == independent_value
            entry["differs_from_series_latest_value"] = (
                None if latest_value is None else stored_value != latest_value)
        elif bucket == "refused":
            entry["agree"] = None
            entry["agree_note"] = (
                f"refused UNFETCHED: before {STABILITY_MEASURED_FROM}, where the stability "
                f"measurement says nothing. Nothing was stored. The full body does carry "
                f"{independent_raw!r} for this date — storing THAT under this date is exactly "
                f"the forgery the floor refuses, so the absence above is the proof")
        else:
            entry["agree"] = None
            entry["agree_note"] = (
                f"no value to cross-check: bucket {bucket}"
                + (f" ({why})" if why else "")
                + ("; the full body has no row for this date either"
                   if independent_raw is None else
                   f"; the full body carries {independent_raw!r} for it"))
        table.append(entry)
        print(f"   {date_text}  {bucket:<9} stored={stored_value}  "
              f"independent={independent_value}  agree={entry['agree']}", flush=True)

    disagreed = [e for e in table if e["agree"] is False]
    proven = [e for e in table if e["agree"] is True]
    unproven = [e for e in table if e["agree"] is None and e["bucket"] != "refused"]
    unwindowed = [e for e in table if e["bucket"] == "admitted" and not e["windowed_request_sent"]]
    if disagreed:
        verdict, code = "DISAGREEMENT", 1
    elif unproven:
        verdict, code = "INCOMPLETE", 1
    elif unwindowed:
        verdict, code = "WINDOW_UNPROVEN", 1
    elif not proven:
        verdict, code = "NOTHING_PROVEN", 1
    else:
        verdict, code = "PROVEN", 0

    document = {
        "ran_utc": started,
        "finished_utc": finished,
        "database": args.db,
        "source_id": ing.source_id,
        "series": ing.ref,
        "transformation": ing.transformation,
        "as_of_rule": ing.as_of_rule,
        "value_column_expected": column,
        "requires_original_vintage": original,
        "stability_measured_from": STABILITY_MEASURED_FROM,
        "adapter_class": type(probe_adapter).__name__,
        "adapter_id": probe_adapter.adapter_id,
        "requested_dates": dates,
        "proves": ("that the cosd/coed WINDOW mechanism recovers the correct historical value "
                   "for a named past date against the live endpoint — the right period, matched "
                   "by exact date. NOT that the value is point-in-time-original: DFF is measured "
                   "stable, so a stable pair is current-value-by-design and its reading is "
                   "labelled current_only (ingestion.vintage)"),
        "backfill": {
            "vintage": result.vintage,
            "admitted": list(result.admitted),
            "skipped": list(result.skipped),
            "refused": [list(pair) for pair in result.refused],
            "failed": [list(pair) for pair in result.failed],
            "fetches": result.fetches,
            "counts": result.counts,
        },
        "wire": [dict(record, url=wire_url(record)) for record in wire],
        "stored": rows,
        "cross_check": {
            "url": cross_url,
            "how": ("one extra GET of the UNWINDOWED body, read off by hand in this file, "
                    "outside the adapter and outside parse_fred_csv_for_date"),
            "header_line": whole["header_line"],
            "header_is_expected": whole["header_is_expected"],
            "row_count": whole["row_count"],
            "span": whole["span"],
            "last_row": whole["last_row"],
            "series_latest_value": latest_value,
            "values_for_requested_dates": {
                date_text: whole["by_date"].get(date_text) for date_text in dates},
        },
        "comparison": table,
        "verdict": verdict,
        "agreed": len(proven),
        "disagreed": len(disagreed),
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"-- {verdict}: {len(proven)} agreed, {len(disagreed)} disagreed; written to {args.out}",
          flush=True)
    if code:
        print("-- STOP: this is a reportable result, not something to retune", flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
