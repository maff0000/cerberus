#!/usr/bin/env python3
"""THE PROOF RUN, NO-REVISION-MECHANISM BRANCH — ``ingestion.backfill`` against the REAL
network and a REAL store, for BOTH of WO-1.16's sources and for the row it must refuse.

    PYTHONPATH=src:. python3 tools/probe/wo116_backfill_proof.py \
        --db /tmp/wo116_backfill_proof.sqlite \
        --out evidence/wo116_backfill_proof.json

WHY THIS EXISTS EVEN THOUGH ``tests/test_wo114_backfill.py`` IS GREEN. The same reason
``tools/probe/wo115_backfill_proof.py`` exists for the stable branch and
``tools/probe/wo114_backfill_proof.py`` for the vintage one: those tests substitute the WIRE
and nothing else — real driver, real adapter construction, real parser, real store, a
callable where the socket should be. Their fakes were built FROM measurements of the live
endpoints (``tools/probe/cboe_history_probe.py`` and
``tools/probe/yahoo_period_window_probe.py``, both 2026-10-15), so they are evidence — but
once-removed evidence, and a transport fake answers what it was told to answer. It cannot
answer the question an operator about to backfill decades of VIX closes actually has: does
``backfill_range`` recover the RIGHT historical value when it reaches ``cdn-api.cboe.com``
and ``query1.finance.yahoo.com`` for real, today? This runs it for real and writes down what
came back.

IT IS A PROBE, NOT A GATE. It opens sockets to two third parties, so it is not reproducible
offline and is not a register check (CD-PL-F48). It writes a JSON record a human reads.

THREE LEGS, AND THE THIRD IS NOT AN AFTERTHOUGHT
    1. **CBOE** — ``cboe.VIX`` at a named past date, through ``backfill_range``.
    2. **YAHOO** — ``yahoo.SPY`` at a DIFFERENT named past date, through ``backfill_range``.
    3. **THE ``adjclose`` REFUSAL** — ``yahoo.BIZD.adj``, the real ``private_credit_stress``
       catalog row, through the same entry point. It reaches no network and is recorded here
       anyway, because an evidence file that showed only the two sources this WO OPENED
       would not show the row it deliberately left CLOSED, and the closure is half of what
       WO-1.16 decided (PID.md scope correction). ``tests/test_wo114_backfill.py`` already
       proves the label-dispatch refusal fires first through this entry point; this is not
       re-discovering that, it is confirming the REAL catalog row behaves the same way
       outside a test harness, and recording the exact message an operator would see.

THE CROSS-CHECK IS WHAT MAKES THIS A PROOF AND NOT PLUMBING
    A run that only reported what the driver stored would prove the driver can write a row.
    So each stored value is checked against the SAME value obtained a SECOND way that does
    not go through the dated path at all. The two legs cross-check differently because the
    two sources differ in what a "second way" can even be:

    * **CBOE has no second request to make**, which is measured rather than conceded:
      ``cdn-api.cboe.com`` honours NO date-windowing parameter — eight spellings plus two
      negative controls each returned a body BYTE-IDENTICAL to the bare URL's
      (``evidence/wo116_cboe_probe.json``). There is exactly one body. So the independent leg
      is one plain GET of that bare ``VIX_History.csv`` URL, built HERE from
      :data:`CBOE_HISTORY`, read off BY HAND in this file (:func:`read_cboe_by_hand`) —
      outside :class:`~ingestion.adapters.CboeAdapter` and outside
      :func:`~ingestion.adapters.parse_cboe_csv_for_date`. What is independent is the READING,
      not the request: the ``MM/DD/YYYY`` conversion is done here by splitting on ``/``
      rather than by ``strptime``, so the two legs share the hostname and nothing else. That
      is the strongest available second opinion on this source and the honest description of
      it is "the same body, read by different code".

    * **YAHOO has a structurally different request available**, and it is used.
      ``YahooChartAdapter``'s dated mode asks an ABSOLUTE window — ``period1``/``period2``
      bounding one UTC day, no ``range=`` at all. The independent leg asks a RELATIVE range
      — ``range=10y&interval=1d``, which is the shape the LIVE collector uses — and picks the
      bar for the date by hand (:func:`read_yahoo_by_hand`). Two different query shapes, two
      different response sizes (one bar against ~2,500), one answer. If a one-day absolute
      window and a ten-year relative range disagree about 2018-11-15, something is wrong that
      no amount of agreement with itself would have surfaced.

    If a leg's stored value and its independent value disagree, that is a REAL DEFECT this
    file exists to surface, and the run says ``DISAGREEMENT`` and exits non-zero. It is not
    something to tune until it agrees.

    ``differs_from_series_latest_value`` is the second leg's other use, and it matters MORE
    here than it did on the FRED branches. The dangerous failure on this branch is a parser
    reading the body BY POSITION — the last row — and on BOTH of these sources every dated
    request is answered by a body whose last row is the current session (CBOE always, because
    the body cannot be windowed; Yahoo whenever a window is ignored or malformed). So a
    position read would answer a 2015 backfill with this week's close, every time. Each full
    body's last row is recorded, and a stored historical value that differs from it
    demonstrably was not read off the end.

WHAT IS READ BACK, AND FROM WHERE
    The ``backfill`` section is the driver's own ``BackfillResult``. The ``stored`` section is
    read back OUT OF THE STORE on a read-only handle, so what is reported is what the database
    holds and not what the driver believed it wrote.

    The ``wire`` section is the request line ``http.client`` actually put on the socket for
    EVERY GET this run issued — backfill legs and cross-check legs alike — recorded by an
    OBSERVER that delegates to the real method (:func:`install_wire_log`). It is what makes
    "the request was genuinely issued, genuinely to that host, and genuinely shaped that way"
    a measurement rather than a claim: a ``period1=...&period2=...`` in the recorded target
    came from this run's socket, not from a cache and not from a default. For the Yahoo leg
    the record carries one further fact the driver's result cannot — that the dated request
    contained NO ``range=``, which is the ``range``-wins finding of
    ``evidence/wo116_yahoo_window_probe.json`` (``q6_range_and_period_together``) being
    honoured on the real path rather than only in a test.

THE CLAIM, STATED AT ITS REAL WIDTH. Both admitted readings are labelled
:data:`~ingestion.vintage.VINTAGE_NO_REVISION_MECHANISM`, and that label is narrower than
either FRED label: neither source exposes a vintage trail, and neither has a stability
MEASUREMENT behind it the way ``fred.DFF`` does. What is proven here is that
**``backfill_range`` recovers the correct historical value for a named past date from each
live endpoint** — the right session, matched by exact date, not the latest row wearing a past
key. It is NOT a proof that either value is point-in-time-original; nothing on this branch
claims that, and ``ingestion.vintage`` is where the ruling that an unrevised source need not
produce one lives.

THERE IS NO DATE FLOOR ON THIS BRANCH, and its absence is why the third leg is here. The
stable branch refuses any date before ``STABILITY_MEASURED_FROM`` because it leans on a
measurement with a left edge; ``VINTAGE_NO_REVISION_MECHANISM`` leans on "this source has no
revision mechanism at all", which has no left edge to refuse at (``ingestion.backfill``). So
the thing this branch must refuse is not a DATE, it is a COLUMN — and the third leg is that
refusal, exercised on the real catalog row.

WHAT IT DOES NOT DO. It does not pick the database for you: ``--db`` is required and the
caller owns where a real write lands — a throwaway file, for this run, since these rows are a
proof and not the DEV store's data. It computes no dates: the two defaults are real sessions
of their respective sources, deliberately YEARS back and deliberately DIFFERENT from each
other, and a caller may name others.
"""

from __future__ import annotations

import argparse
import hashlib
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
from ingestion.vintage import VINTAGE_NO_REVISION_MECHANISM, has_no_revision_mechanism

#: The whole static CBOE history body, for the independent leg. The SAME URL
#: :meth:`~ingestion.adapters.CboeAdapter._url` builds — because there is no other one to
#: build (``evidence/wo116_cboe_probe.json``: no windowing parameter is honoured) — written
#: out here so the second leg shares no line of code with the first.
CBOE_HISTORY = "https://cdn-api.cboe.com/api/global/us_indices/daily_prices/{index}_History.csv"

#: The Yahoo chart endpoint, for the independent leg, asked the RELATIVE way. ``range=`` is
#: the shape ``YahooChartAdapter`` uses when ``observation_date`` is ``None`` — i.e. the live
#: collector's shape — and is structurally unlike the absolute ``period1``/``period2`` window
#: the dated path builds. Built here, not borrowed.
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

#: Yahoo answers ``429`` to urllib's default agent and ``200`` to an identified browser-style
#: one (``ingestion.adapters.YahooChartAdapter._headers``). Spelled differently here on
#: purpose: this leg must not be able to pass or fail because of a string it shares with the
#: code under test, and a User-Agent is a transport courtesy, not a parse.
CROSS_CHECK_AGENT = "Mozilla/5.0 (compatible; cerberus-wo116-crosscheck/1.0)"

#: A real CBOE session, years back. VIX carries 06/15/2015 in its history body; the date is
#: named rather than derived because no cadence formula knows an index's trading calendar
#: (``ingestion.backfill_dates`` refuses exactly that, correctly).
DEFAULT_CBOE_DATE = "2015-06-15"

#: A real SPY session, years back and DIFFERENT from the CBOE one — the two legs prove two
#: endpoints and there is nothing to be gained by coupling their dates. It must also lie
#: inside :data:`DEFAULT_YAHOO_RANGE` for the cross-check to be able to see it, which the
#: run checks rather than assumes (``independent_range_covers_date``).
DEFAULT_YAHOO_DATE = "2018-11-15"

#: The relative range the independent Yahoo leg asks for. Wide enough to comfortably contain
#: :data:`DEFAULT_YAHOO_DATE` with years to spare, so the cross-check is not itself balanced
#: on a boundary.
DEFAULT_YAHOO_RANGE = "10y"

#: The real ``private_credit_stress`` row — ``column="adjclose"`` — and a date that is a
#: perfectly ordinary trading session, so nothing about the date can be what the refusal is
#: about.
DEFAULT_ADJCLOSE_SOURCE = "yahoo.BIZD.adj"
DEFAULT_ADJCLOSE_DATE = "2018-11-15"

#: The unwindowed VIX body is ~460 KB and ten years of SPY bars ~250 KB. Room for both
#: without being unbounded.
MAX_BODY_BYTES = 16_000_000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _clock() -> datetime:
    return datetime.now(timezone.utc)


# --- the wire observer ---------------------------------------------------------------- #

_WIRE_REQUEST = http.client.HTTPConnection.request
_WIRE_GETRESPONSE = http.client.HTTPConnection.getresponse


def install_wire_log() -> list:
    """Record what ``http.client`` puts on the socket, then DELEGATE to the real method.

    AN OBSERVER, NOT A SUBSTITUTE, and the distinction is the whole reason this is allowed
    in a proof whose point is that nothing is faked: both wrappers call the original and
    return exactly what it returned. No URL is rewritten, no body is supplied, no status is
    invented. What is gained is the one fact the driver's own result cannot carry — the
    literal request target that went out, which is how ``period1=...&period2=...`` is shown
    to have been SENT rather than merely built, and how the ABSENCE of ``range=`` from that
    same target is shown to be a property of the request rather than of the source.

    It is patched on ``HTTPConnection`` rather than on ``HTTPSConnection`` because the
    latter inherits both methods, so one patch covers plain and TLS alike. ``getresponse``
    attributes its status to the most recent request, which is correct for the strictly
    sequential one-GET-at-a-time traffic this file issues and would not be for a pooled or
    concurrent client.

    UNLIKE ``wo115_backfill_proof.py``, THIS ONE STAYS INSTALLED FOR THE CROSS-CHECKS TOO.
    There, the independent leg's URL was known because this file built it. That is still
    true here, and it is no longer the whole story: the Yahoo cross-check's claim is that it
    is a STRUCTURALLY DIFFERENT REQUEST, and a claim about request shape deserves the same
    socket-level evidence on both sides of the comparison rather than evidence on one side
    and a string literal on the other.
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


# --- the independent legs ------------------------------------------------------------- #


def plain_get(url: str, headers: Union[dict, None] = None, timeout: float = 60.0) -> str:
    """One GET with plain ``urllib``. Deliberately NOT ``ingestion.adapters.http_get``.

    The value of an independent leg is that it shares no line of code with the thing under
    test, and ``http_get`` is under test: it is what every adapter fetches through. So the
    transport here is the stdlib's, called directly, with this file's own headers.
    """
    request = urllib.request.Request(url, method="GET", headers=headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(MAX_BODY_BYTES).decode("utf-8", "replace")


def read_cboe_by_hand(body: str, column: str) -> dict:
    """Split a CBOE ``*_History.csv`` body into its rows HERE, in this file, by hand.

    Not :func:`~ingestion.adapters.parse_cboe_csv_for_date` and not
    :func:`~ingestion.adapters.parse_cboe_csv`: a cross-check routed through the parser under
    test would check that the parser agrees with itself.

    THE DATE CONVERSION IS DONE BY SPLITTING ON ``/``, NOT BY ``strptime``, and that is the
    one place this function could have quietly become the same code as the parser. CBOE dates
    the rows ``MM/DD/YYYY`` and the ISO key has to come from somewhere; the parser reaches
    for ``datetime.strptime`` and so would anyone writing this a second time. Doing it with a
    split means a defect in how one of them reorders the three fields cannot be present in
    both. ``row_count``, ``span`` and ``last_row`` are reported because the SHAPE of the body
    that answered is itself evidence about which request answered.
    """
    lines = body.strip().splitlines()
    header = lines[0].split(",") if lines else []
    by_date: dict = {}
    rows = 0
    first_iso = last_iso = last_row = None
    index = header.index(column) if column in header else None
    for line in lines[1:]:
        cells = line.split(",")
        if len(cells) != len(header) or index is None:
            continue
        parts = cells[0].split("/")
        if len(parts) != 3:
            continue
        month, day, year = parts
        iso = f"{year}-{month}-{day}"
        rows += 1
        first_iso = first_iso or iso
        last_iso, last_row = iso, line
        by_date[iso] = cells[index]
    return {
        "header_line": lines[0] if lines else "",
        "header_has_column": column in header,
        "row_count": rows,
        "span": [first_iso, last_iso] if rows else None,
        "last_row": last_row,
        # The latest session's figure in the asked-for column, taken off the same hand-read
        # rows rather than re-split out of ``last_row`` by the caller. It is what a POSITION
        # read of this body would have returned for ANY date, which is the point of
        # recording it (see ``differs_from_series_latest_value``).
        "last_row_value": by_date[last_iso] if last_iso else None,
        "by_date": by_date,
    }


def read_yahoo_by_hand(body: str) -> dict:
    """Walk a Yahoo v8 chart envelope HERE, in this file, by hand.

    Not :func:`~ingestion.adapters.parse_yahoo_chart_for_date` and not
    :func:`~ingestion.adapters.parse_yahoo_chart`, for the reason above. The body being read
    is a DIFFERENT body too — a ten-year relative range rather than a one-day absolute
    window — so ``bar_count`` and ``span`` are evidence about which request answered.

    The epoch-second to UTC-date step is the same arithmetic the parser does, and cannot
    honestly be anything else: a ``1d`` bar is stamped at the session OPEN and the UTC date of
    that stamp IS the session's date (``evidence/wo116_yahoo_window_probe.json``). What is
    independent here is the request, the envelope walk and the selection — not the definition
    of what a timestamp means, which is the source's and not ours to vary.
    """
    envelope = json.loads(body)
    result = envelope["chart"]["result"][0]
    stamps = result.get("timestamp") or []
    closes = result["indicators"]["quote"][0].get("close") or []
    by_date: dict = {}
    for stamp, close in zip(stamps, closes):
        if close is None:
            continue
        by_date[datetime.fromtimestamp(stamp, tz=timezone.utc).date().isoformat()] = close
    dates = sorted(by_date)
    return {
        "bar_count": len(stamps),
        "priced_bar_count": len(by_date),
        "span": [dates[0], dates[-1]] if dates else None,
        "last_bar_date": dates[-1] if dates else None,
        "last_bar_close": by_date[dates[-1]] if dates else None,
        "meta_symbol": result.get("meta", {}).get("symbol"),
        "meta_currency": result.get("meta", {}).get("currency"),
        "by_date": by_date,
    }


def _number(raw) -> Union[float, None]:
    """A finite float, or ``None`` for a blank cell and for anything unreadable."""
    if raw is None or raw == "":
        return None
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None


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


def buckets_of(result) -> dict:
    """``BackfillResult`` turned inside out: date -> (bucket, class)."""
    out = {}
    for date_text in result.admitted:
        out[date_text] = ("admitted", None)
    for date_text in result.skipped:
        out[date_text] = ("skipped", None)
    for date_text, why in result.refused:
        out[date_text] = ("refused", why)
    for date_text, why in result.failed:
        out[date_text] = ("failed", why)
    return out


def backfill_section(result) -> dict:
    return {
        "vintage": result.vintage,
        "admitted": list(result.admitted),
        "skipped": list(result.skipped),
        "refused": [list(pair) for pair in result.refused],
        "failed": [list(pair) for pair in result.failed],
        "fetches": result.fetches,
        "counts": result.counts,
    }


# --- leg 1: CBOE ---------------------------------------------------------------------- #


def run_cboe(source_id: str, date_text: str, db_path: str, store: SqliteStore,
             wire: list) -> dict:
    """``backfill_range`` for one real CBOE session, cross-checked against the bare body."""
    ing = ingredient(source_id)
    print(f"-- CBOE  {ing.source_id} @ {date_text}  (column {ing.column})", flush=True)
    adapter = build_backfill_adapter(ing, date_text, _clock)
    print(f"   adapter: {type(adapter).__name__} ({adapter.adapter_id})", flush=True)

    before = len(wire)
    result = backfill_range(ing, [date_text], store, _clock)
    sent = wire[before:]
    print(f"   {result.counts}", flush=True)
    for record in sent:
        print(f"   SENT {record['method']} {wire_url(record)} -> {record.get('http_status')}",
              flush=True)

    rows = stored_rows(db_path, ing.source_id)
    stored = {row["payload"].get("observation_date"): row for row in rows}.get(date_text)
    stored_value = stored["payload"].get("value") if stored else None

    cross_url = CBOE_HISTORY.format(index=ing.ref)
    before_cross = len(wire)
    body = plain_get(cross_url)
    cross_wire = wire[before_cross:]
    whole = read_cboe_by_hand(body, ing.column)
    print(f"   cross-check: {cross_url} -> {whole['row_count']} rows {whole['span']}", flush=True)
    independent_raw = whole["by_date"].get(date_text)
    independent_value = _number(independent_raw)
    latest_value = _number(whole["last_row_value"])

    bucket, why = buckets_of(result).get(date_text, ("UNACCOUNTED", None))
    entry = {
        "leg": "cboe",
        "source_id": ing.source_id,
        "kind": ing.kind,
        "ref": ing.ref,
        "column": ing.column,
        "unit": ing.unit,
        "as_of_rule": ing.as_of_rule,
        "observation_date": date_text,
        "adapter_class": type(adapter).__name__,
        "adapter_id": adapter.adapter_id,
        "expected_vintage_label": VINTAGE_NO_REVISION_MECHANISM,
        "has_no_revision_mechanism": has_no_revision_mechanism(ing.kind, ing.column),
        "bucket": bucket,
        "class": why,
        "stored_value": stored_value,
        "stored_source_as_of_utc": stored["source_as_of_utc"] if stored else None,
        "vintage_label": stored["vintage"] if stored else None,
        "independent_value": independent_value,
        "independent_raw_cell": independent_raw,
        "independent_how": ("one plain GET of the bare VIX_History.csv URL, rows split and "
                            "MM/DD/YYYY converted BY HAND in this file, outside CboeAdapter "
                            "and outside parse_cboe_csv_for_date"),
        "independent_url": cross_url,
        "independent_http_status": cross_wire[0].get("http_status") if cross_wire else None,
        "independent_content_length": (cross_wire[0].get("content_length")
                                       if cross_wire else None),
        "independent_body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "independent_row_count": whole["row_count"],
        "independent_span": whole["span"],
        "independent_last_row": whole["last_row"],
        "series_latest_value": latest_value,
        "backfill_request_url": wire_url(sent[0]) if sent else None,
        "backfill_request_sent": bool(sent),
        "backfill_http_status": sent[0].get("http_status") if sent else None,
        "backfill_response_content_length": sent[0].get("content_length") if sent else None,
        # MEASURED, not asserted: the dated CBOE request carries no window parameter, because
        # the source honours none (evidence/wo116_cboe_probe.json). The two legs therefore
        # fetched the SAME URL, which is why the independence lives entirely in the reading.
        "backfill_and_cross_check_same_url": bool(sent) and wire_url(sent[0]) == cross_url,
        "backfill": backfill_section(result),
        "stored_rows": rows,
    }
    if bucket == "admitted" and stored_value is not None and independent_value is not None:
        entry["agree"] = stored_value == independent_value
        entry["differs_from_series_latest_value"] = (
            None if latest_value is None else stored_value != latest_value)
    else:
        entry["agree"] = None
        entry["agree_note"] = (
            f"no stored value to cross-check: bucket {bucket}" + (f" ({why})" if why else "")
            + ("; the full body has no row for this date either" if independent_raw is None
               else f"; the full body carries {independent_raw!r} for it"))
    print(f"   {date_text}  {bucket:<9} stored={stored_value}  "
          f"independent={independent_value}  agree={entry['agree']}", flush=True)
    return entry


# --- leg 2: YAHOO --------------------------------------------------------------------- #


def run_yahoo(source_id: str, date_text: str, wide_range: str, db_path: str,
              store: SqliteStore, wire: list) -> dict:
    """``backfill_range`` for one real SPY session, cross-checked a structurally other way."""
    ing = ingredient(source_id)
    field = ing.column or "close"
    print(f"-- YAHOO {ing.source_id} @ {date_text}  (field {field})", flush=True)
    adapter = build_backfill_adapter(ing, date_text, _clock)
    print(f"   adapter: {type(adapter).__name__} ({adapter.adapter_id})", flush=True)

    before = len(wire)
    result = backfill_range(ing, [date_text], store, _clock)
    sent = wire[before:]
    print(f"   {result.counts}", flush=True)
    for record in sent:
        print(f"   SENT {record['method']} {wire_url(record)} -> {record.get('http_status')}",
              flush=True)

    rows = stored_rows(db_path, ing.source_id)
    stored = {row["payload"].get("observation_date"): row for row in rows}.get(date_text)
    stored_value = stored["payload"].get("value") if stored else None

    symbol = ing.ref.replace("^", "%5E").replace("=", "%3D")
    cross_url = (f"{YAHOO_CHART.format(symbol=symbol)}"
                 f"?range={wide_range}&interval=1d")
    before_cross = len(wire)
    body = plain_get(cross_url, headers={"User-Agent": CROSS_CHECK_AGENT})
    cross_wire = wire[before_cross:]
    whole = read_yahoo_by_hand(body)
    print(f"   cross-check: {cross_url} -> {whole['bar_count']} bars {whole['span']}", flush=True)
    independent_value = _number(whole["by_date"].get(date_text))
    latest_value = _number(whole["last_bar_close"])

    dated_target = sent[0]["request_target"] if sent else ""
    bucket, why = buckets_of(result).get(date_text, ("UNACCOUNTED", None))
    entry = {
        "leg": "yahoo",
        "source_id": ing.source_id,
        "kind": ing.kind,
        "column": ing.column,
        "field_resolved": field,
        "ref": ing.ref,
        "unit": ing.unit,
        "as_of_rule": ing.as_of_rule,
        "observation_date": date_text,
        "adapter_class": type(adapter).__name__,
        "adapter_id": adapter.adapter_id,
        "expected_vintage_label": VINTAGE_NO_REVISION_MECHANISM,
        "has_no_revision_mechanism": has_no_revision_mechanism(ing.kind, ing.column),
        "bucket": bucket,
        "class": why,
        "stored_value": stored_value,
        "stored_source_as_of_utc": stored["source_as_of_utc"] if stored else None,
        "vintage_label": stored["vintage"] if stored else None,
        "independent_value": independent_value,
        "independent_how": (f"one plain GET asking a RELATIVE range={wide_range} — the live "
                            f"collector's request shape, not the dated path's absolute "
                            f"period1/period2 window — with the bar for this date picked BY "
                            f"HAND in this file, outside YahooChartAdapter and outside "
                            f"parse_yahoo_chart_for_date"),
        "independent_url": cross_url,
        "independent_http_status": cross_wire[0].get("http_status") if cross_wire else None,
        "independent_content_length": (cross_wire[0].get("content_length")
                                       if cross_wire else None),
        "independent_body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "independent_bar_count": whole["bar_count"],
        "independent_priced_bar_count": whole["priced_bar_count"],
        "independent_span": whole["span"],
        "independent_meta_symbol": whole["meta_symbol"],
        "independent_range_covers_date": bool(
            whole["span"] and whole["span"][0] <= date_text <= whole["span"][1]),
        "series_latest_bar_date": whole["last_bar_date"],
        "series_latest_value": latest_value,
        "backfill_request_url": wire_url(sent[0]) if sent else None,
        "backfill_request_sent": bool(sent),
        "backfill_http_status": sent[0].get("http_status") if sent else None,
        "backfill_response_content_length": sent[0].get("content_length") if sent else None,
        # The three facts that make "structurally different request" a measurement. The
        # dated leg asked an ABSOLUTE window and carried no range=; the cross-check asked a
        # RELATIVE range and carried no period window. Both read off this run's sockets.
        "backfill_request_is_absolute_window": (
            "period1=" in dated_target and "period2=" in dated_target),
        "backfill_request_carries_no_range": bool(sent) and "range=" not in dated_target,
        "cross_check_request_is_relative_range": (
            "range=" in cross_url and "period1=" not in cross_url),
        "backfill_and_cross_check_same_url": bool(sent) and wire_url(sent[0]) == cross_url,
        "backfill": backfill_section(result),
        "stored_rows": rows,
    }
    if bucket == "admitted" and stored_value is not None and independent_value is not None:
        entry["agree"] = stored_value == independent_value
        entry["differs_from_series_latest_value"] = (
            None if latest_value is None else stored_value != latest_value)
    else:
        entry["agree"] = None
        entry["agree_note"] = (
            f"no stored value to cross-check: bucket {bucket}" + (f" ({why})" if why else "")
            + ("; the ten-year body has no priced bar for this date either"
               if whole["by_date"].get(date_text) is None else
               f"; the ten-year body carries {whole['by_date'][date_text]!r} for it"))
    print(f"   {date_text}  {bucket:<9} stored={stored_value}  "
          f"independent={independent_value}  agree={entry['agree']}", flush=True)
    return entry


# --- leg 3: the adjclose refusal ------------------------------------------------------ #

#: The sentence ``ingestion.backfill`` raises when no vintage label can be derived. Matched
#: as a SUBSTRING of the real exception's message, so this leg reports WHICH of WO-1.16's two
#: independent refusals fired and not merely that something did.
LABEL_DISPATCH_MARKER = "no vintage label is derived for it"

#: The sentence ``YahooChartAdapter.__init__`` raises for a dated ``adjclose`` fetch. The
#: SECOND door. It is recorded here — constructed directly, which fetches nothing — because
#: an evidence file that showed only the refusal that happened to fire first would not show
#: that the closure survives someone removing it.
ADAPTER_MARKER = "adjclose has no"


def run_adjclose(source_id: str, date_text: str, store: SqliteStore, wire: list) -> dict:
    """The real ``private_credit_stress`` row through ``backfill_range``. No network.

    ``tests/test_wo114_backfill.py`` already proves the label-dispatch refusal fires FIRST
    through this entry point, so nothing is being discovered here. What is being recorded is
    that the REAL catalog row — not a fixture shaped like it — behaves the same way outside a
    test harness, and the exact message an operator would read.

    ``wire`` is passed so the record can state that NOTHING WAS FETCHED as a measurement
    rather than as a description of the code path: the refusal is a ``raise`` in the label
    dispatch, before the first date is touched, so a socket write during this leg would mean
    the refusal was not where this file says it is.
    """
    ing = ingredient(source_id)
    print(f"-- ADJCLOSE {ing.source_id} @ {date_text}  (column {ing.column!r})", flush=True)
    before = len(wire)

    raised_type = raised_message = None
    try:
        backfill_range(ing, [date_text], store, _clock)
    except Exception as failure:  # the thing under test is THAT it raises, and with what
        raised_type, raised_message = type(failure).__name__, str(failure)

    # The second, independent door, constructed directly. Building an adapter fetches
    # nothing; this is the other refusal made visible rather than inferred.
    adapter_type = adapter_message = None
    try:
        build_backfill_adapter(ing, date_text, _clock)
    except Exception as failure:
        adapter_type, adapter_message = type(failure).__name__, str(failure)

    fetched = wire[before:]
    which = ("label_dispatch" if raised_message and LABEL_DISPATCH_MARKER in raised_message
             else "adapter_construction" if raised_message and ADAPTER_MARKER in raised_message
             else None if raised_message is None else "unrecognised")
    entry = {
        "leg": "adjclose_refusal",
        "source_id": ing.source_id,
        "kind": ing.kind,
        "column": ing.column,
        "ref": ing.ref,
        "serves": list(ing.serves),
        "observation_date": date_text,
        "raised": raised_type is not None,
        "raised_type": raised_type,
        "raised_message": raised_message,
        "refusal_door": which,
        "refusal_is_label_dispatch": which == "label_dispatch",
        "has_no_revision_mechanism": has_no_revision_mechanism(ing.kind, ing.column),
        # Both doors, so the record shows the closure is held twice over.
        "second_door_build_backfill_adapter_raised": adapter_type is not None,
        "second_door_raised_type": adapter_type,
        "second_door_raised_message": adapter_message,
        "requests_issued_during_leg": len(fetched),
        "no_network_reached": not fetched,
        "proves": ("that the REAL private_credit_stress catalog row is refused by "
                   "backfill_range itself — at the label dispatch, before any date is "
                   "touched and before any URL exists — and that YahooChartAdapter refuses "
                   "the same row independently at construction"),
    }
    print(f"   raised {raised_type}: {raised_message}", flush=True)
    print(f"   door={which}  fetched={len(fetched)}  "
          f"second door: {adapter_type}", flush=True)
    return entry


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        description="WO-1.16 real backfill proof run (CBOE + Yahoo, and the adjclose refusal)")
    parser.add_argument("--db", required=True, help="the SQLite store to write into (throwaway)")
    parser.add_argument("--out", required=True, help="where to write the JSON record")
    parser.add_argument("--cboe-source", default="cboe.VIX")
    parser.add_argument("--cboe-date", default=DEFAULT_CBOE_DATE)
    parser.add_argument("--yahoo-source", default="yahoo.SPY")
    parser.add_argument("--yahoo-date", default=DEFAULT_YAHOO_DATE)
    parser.add_argument("--yahoo-range", default=DEFAULT_YAHOO_RANGE,
                        help="the RELATIVE range the independent Yahoo leg asks for")
    parser.add_argument("--adjclose-source", default=DEFAULT_ADJCLOSE_SOURCE)
    parser.add_argument("--adjclose-date", default=DEFAULT_ADJCLOSE_DATE)
    args = parser.parse_args(argv)

    started = _now()
    wire = install_wire_log()
    try:
        with SqliteStore(args.db) as store:
            cboe = run_cboe(args.cboe_source, args.cboe_date, args.db, store, wire)
            yahoo = run_yahoo(args.yahoo_source, args.yahoo_date, args.yahoo_range,
                              args.db, store, wire)
            adjclose = run_adjclose(args.adjclose_source, args.adjclose_date, store, wire)
    finally:
        remove_wire_log()
    finished = _now()

    legs = [cboe, yahoo]
    disagreed = [leg for leg in legs if leg["agree"] is False]
    proven = [leg for leg in legs if leg["agree"] is True]
    unproven = [leg for leg in legs if leg["agree"] is None]
    unsent = [leg for leg in legs if leg["bucket"] == "admitted"
              and not leg["backfill_request_sent"]]
    mislabelled = [leg for leg in legs
                   if leg["bucket"] == "admitted"
                   and leg["vintage_label"] != VINTAGE_NO_REVISION_MECHANISM]
    if disagreed:
        verdict, code = "DISAGREEMENT", 1
    elif unproven:
        verdict, code = "INCOMPLETE", 1
    elif unsent:
        verdict, code = "REQUEST_UNPROVEN", 1
    elif mislabelled:
        verdict, code = "LABEL_UNPROVEN", 1
    elif not adjclose["refusal_is_label_dispatch"]:
        verdict, code = "REFUSAL_UNPROVEN", 1
    elif len(proven) != len(legs):
        verdict, code = "NOTHING_PROVEN", 1
    else:
        verdict, code = "PROVEN", 0

    document = {
        "ran_utc": started,
        "finished_utc": finished,
        "database": args.db,
        "work_order": "CERBERUS-WO-1.16",
        "precedent": ["tools/probe/wo114_backfill_proof.py",
                      "tools/probe/wo115_backfill_proof.py"],
        "endpoints": {
            "cboe": "cdn-api.cboe.com",
            "yahoo": "query1.finance.yahoo.com",
        },
        "credential": "none — both endpoints are keyless public HTTP",
        "proves": ("that backfill_range recovers the CORRECT historical value for a named "
                   "past date from BOTH live endpoints — the right session, matched by exact "
                   "date, not the latest row wearing a past key — and that the real "
                   "private_credit_stress row (yahoo.BIZD.adj) is refused through the same "
                   "entry point. NOT that either value is point-in-time-original: neither "
                   "source exposes a vintage trail, which is what the "
                   f"{VINTAGE_NO_REVISION_MECHANISM} label says and the narrower claim it "
                   "carries (ingestion.vintage)"),
        "vintage_label_expected": VINTAGE_NO_REVISION_MECHANISM,
        "cboe": cboe,
        "yahoo": yahoo,
        "adjclose_refusal": adjclose,
        "wire": [dict(record, url=wire_url(record)) for record in wire],
        "verdict": verdict,
        "agreed": len(proven),
        "disagreed": len(disagreed),
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"-- {verdict}: {len(proven)}/{len(legs)} agreed, {len(disagreed)} disagreed; "
          f"adjclose door={adjclose['refusal_door']}; written to {args.out}", flush=True)
    if code:
        print("-- STOP: this is a reportable result, not something to retune", flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
